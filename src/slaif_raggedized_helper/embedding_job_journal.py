"""Owned, bounded atomic journal for declared embedding batches."""

import functools
from dataclasses import dataclass
import hashlib
import json
import os
import re
import secrets
import stat
import sys
import time

from . import derived_store, embedding_batch_store as batch, embedding_job_ownership as ownership
from . import job_records as records
from .schema import fingerprint


class JournalError(ValueError):
    """Journal operation refused without exposing input data."""


@dataclass(frozen=True, slots=True)
class OutputRepairResult:
    output: records.OutputRef
    revision: str
    old_attempt_id: str
    old_owner_id: str
    repair_owner_id: str
    epoch: str
    observation_ms: int
    materialization: str = "REPAIRED_VALID_OUTPUT"
    execution_origin: str = "SUPPLIED_UNVERIFIED"
    accounting: str = "UNKNOWN"
    physical_drain: str = "UNKNOWN"
    qualification: str = "NOT_QUALIFIED"


def _observation_ms(previous_ms):
    observed = time.time_ns() // 1000000
    if observed < previous_ms:
        raise ValueError
    return observed


def _private(fn):
    @functools.wraps(fn)
    def wrapped(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception as exc:
            error = JournalError("journal refused")
            if getattr(exc, "cleanup_owner", None) is not None:
                error.cleanup_owner = exc.cleanup_owner
            raise error from None

    return wrapped


def _json(value):
    return json.dumps(
        value, sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(",", ":")
    ).encode("utf-8")


def _parse(data, limit):
    if type(data) is not bytes or not 1 <= len(data) <= limit:
        raise ValueError

    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError
            result[key] = value
        return result

    def reject(_):
        raise ValueError

    obj = json.loads(
        data.decode("utf-8"),
        object_pairs_hook=unique,
        parse_float=reject,
        parse_constant=reject,
        parse_int=lambda s: int(s) if len(s) <= 20 else reject(s),
    )
    stack = [(obj, 1)]
    nodes = 0
    while stack:
        item, depth = stack.pop()
        nodes += 1
        if nodes > 20000 or depth > 32:
            raise ValueError
        if type(item) is dict:
            stack.extend((v, depth + 1) for v in item.values())
        elif type(item) is list:
            stack.extend((v, depth + 1) for v in item)
        elif item is not None and type(item) not in (str, int, bool):
            raise ValueError
    return obj


def _plan(data):
    obj = _parse(data, 131072)
    if (
        type(obj) is not dict
        or set(obj) != {"format", "purpose", "dependencies", "rows", "codec_policy_fingerprint"}
        or obj["format"] != "embedding-job-plan-v1"
        or obj["purpose"] not in ("prepare", "evaluate")
    ):
        raise ValueError
    # Reuse the accepted batch admission contract; the fabricated vector fields never
    # enter the plan or its identity and are used exclusively for structural validation.
    metadata = {
        "schema": 1,
        "kind": "embedding-batch-v1",
        "dependencies": obj["dependencies"],
        "rows": obj["rows"],
        "codec_policy_fingerprint": obj["codec_policy_fingerprint"],
        "vector_container_sha256": "0" * 64,
        "vector_payload_sha256": "0" * 64,
    }
    batch._metadata(_json(metadata))
    if len(_json(obj)) > 131072:
        raise ValueError
    return obj


def make_spec(plan_bytes):
    """Validate a data-only plan and derive its immutable embedding job identity."""
    try:
        plan = _plan(plan_bytes)
        dep = plan["dependencies"]
        spec = {
            "version": 1,
            "kind": "embedding",
            "purpose": plan["purpose"],
            "inputs": [
                {
                    "kind": "artifact",
                    "ref": "sha256:" + row["representation_id"],
                    "fingerprint": fingerprint({"kind": "embedding-job-row-v1", "row": row}),
                }
                for row in plan["rows"]
            ],
            "configuration": {
                "model": "sha256:" + dep["inventory_id"],
                "encoder": "sha256:" + dep["space_id"],
                "runtime": "sha256:" + dep["execution_fingerprint"],
                "policy": fingerprint(
                    {
                        "kind": "embedding-job-policy-v1",
                        "dependencies": dep,
                        "codec_policy_fingerprint": plan["codec_policy_fingerprint"],
                    }
                ),
                "prompt": fingerprint(
                    {"kind": "embedding-job-prompt-policy-v1", "mode": "no-generator-prompt"}
                ),
            },
        }
        return records.admit(records.JobSpec, spec)
    except Exception:
        raise JournalError("journal refused") from None


def _checked_file(st, mode, kind):
    if st.st_uid != os.geteuid() or stat.S_IMODE(st.st_mode) != mode or not kind(st.st_mode):
        raise ValueError


class Journal:
    def __init__(self, root):
        self.root = root

    def own(self, plan_bytes):
        try:
            plan = _plan(plan_bytes)
            spec = make_spec(_json(plan))
            return _Owned(self.root, plan, spec)
        except Exception:
            raise JournalError("journal refused") from None


class _Owned:
    def __init__(self, root, plan, spec):
        self.root, self.plan, self.spec = root, plan, spec
        self.lease = None
        self.rootfd = self.dirfd = None
        self.pid = os.getpid()
        self.active = False
        self.name = spec.job_id[7:]
        self.cleanup_attempts = []
        self.pending_owners = []
        self.pending = False
        self._cleanup_started = False

    @_private
    def __enter__(self):
        try:
            self.lease = ownership.claim(self.root, self.spec.job_id)
            flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
            self.rootfd = os.open(self.root, flags)
            root_st = os.fstat(self.rootfd)
            _checked_file(root_st, 0o700, stat.S_ISDIR)
            lease_root = os.fstat(self.lease._rootfd)
            if (root_st.st_dev, root_st.st_ino) != (lease_root.st_dev, lease_root.st_ino):
                raise ValueError
            try:
                os.mkdir("embedding_job_journals", 0o700, dir_fd=self.rootfd)
            except FileExistsError:
                pass
            self.dirfd = os.open("embedding_job_journals", flags, dir_fd=self.rootfd)
            st = os.fstat(self.dirfd)
            _checked_file(st, 0o700, stat.S_ISDIR)
            self.dir_identity = (st.st_dev, st.st_ino)
            self.active = True
            self._assert()
            os.fsync(self.rootfd)
            try:
                self._read()
            except FileNotFoundError:
                initial = {
                    "version": 1,
                    "format": "embedding-job-journal-v1",
                    "plan": self.plan,
                    "spec": self.spec.model_dump(mode="json"),
                    "events": [
                        {
                            "state": {
                                "version": 1,
                                "job_id": self.spec.job_id,
                                "status": "PENDING",
                                "attempt_id": None,
                                "owner_id": None,
                                "updated_ms": time.time_ns() // 1000000,
                                "output": None,
                            },
                            "attempt": None,
                        }
                    ],
                }
                self._commit(initial, None)
            return self
        except BaseException as exc:
            nested = getattr(exc, "cleanup_owner", None)
            if nested is not None:
                if nested is not self:
                    self.pending_owners.append(nested)
                self.pending = True
            try:
                self._close()
            except BaseException as cleanup:
                exc.add_note("journal cleanup failed")
                if isinstance(exc, Exception) and not isinstance(cleanup, Exception):
                    self._attach(cleanup)
                    raise cleanup from None
            self._attach(exc)
            raise

    def _attach(self, error):
        if self.pending:
            error.cleanup_owner = self

    def __exit__(self, typ, exc, tb):
        try:
            self._close()
        except BaseException as failure:
            if exc is not None:
                exc.add_note("journal cleanup failed")
                self._attach(exc)
                if isinstance(exc, Exception) and not isinstance(failure, Exception):
                    self._attach(failure)
                    raise failure from None
            elif isinstance(failure, Exception):
                error = JournalError("journal refused")
                self._attach(error)
                raise error from None
            else:
                self._attach(failure)
                raise

    def _close(self):
        self.active = False
        if self._cleanup_started:
            if self.pending:
                error = JournalError("journal cleanup pending or unknown")
                self._attach(error)
                raise error
            return
        self._cleanup_started = True
        failures = []
        if self.lease is not None:
            try:
                self.lease.close()
            except BaseException as exc:
                failures.append(exc)
                self.cleanup_attempts.append(("lease", "unknown"))
                nested = getattr(exc, "cleanup_owner", None)
                if nested is not None:
                    self.pending_owners.append(nested)
            else:
                self.cleanup_attempts.append(("lease", "done"))
                self.lease = None
        for name in ("dirfd", "rootfd"):
            fd = getattr(self, name)
            if fd is None:
                continue
            # A failed close has an unknown outcome. Never retry the number: it
            # may already identify a different open description of the same inode.
            try:
                os.close(fd)
            except BaseException as exc:
                failures.append(exc)
                self.cleanup_attempts.append((name, fd, "unknown"))
            else:
                self.cleanup_attempts.append((name, fd, "done"))
            finally:
                setattr(self, name, None)
        if failures:
            self.pending = True
            failure = next((e for e in failures if not isinstance(e, Exception)), failures[0])
            self._attach(failure)
            raise failure
        if self.pending:
            error = JournalError("journal cleanup pending or unknown")
            self._attach(error)
            raise error

    def _close_file(self, fd, label):
        try:
            os.close(fd)
        except BaseException as exc:
            self.cleanup_attempts.append((label, fd, "unknown"))
            self.pending = True
            self._attach(exc)
            raise
        else:
            self.cleanup_attempts.append((label, fd, "done"))

    def _finish_cleanup(self, original, failures):
        if not failures:
            return
        failure = next((e for e in failures if not isinstance(e, Exception)), failures[0])
        if original is not None:
            original.add_note("journal cleanup failed")
            self._attach(original)
            if not isinstance(original, Exception) or isinstance(failure, Exception):
                return
        self._attach(failure)
        raise failure from None

    def _assert(self):
        if not self.active or self.pending or os.getpid() != self.pid:
            raise JournalError("journal refused")
        self.lease.assert_owned()
        _checked_file(os.fstat(self.rootfd), 0o700, stat.S_ISDIR)
        _checked_file(os.fstat(self.dirfd), 0o700, stat.S_ISDIR)
        st = os.stat("embedding_job_journals", dir_fd=self.rootfd, follow_symlinks=False)
        _checked_file(st, 0o700, stat.S_ISDIR)
        if (st.st_dev, st.st_ino) != self.dir_identity:
            raise JournalError("journal refused")

    @property
    @_private
    def owner_id(self):
        self._assert()
        return self.lease.owner_id

    def _validate(self, raw):
        obj = _parse(raw, 524288)
        if (
            type(obj) is not dict
            or set(obj) != {"version", "format", "plan", "spec", "events"}
            or type(obj["version"]) is not int
            or obj["version"] != 1
            or obj["format"] != "embedding-job-journal-v1"
            or _json(obj) != raw
            or _plan(_json(obj["plan"])) != self.plan
            or records.admit(records.JobSpec, obj["spec"]) != self.spec
            or obj["spec"] != self.spec.model_dump(mode="json")
        ):
            raise ValueError
        events = obj["events"]
        if type(events) is not list or not 1 <= len(events) <= 64:
            raise ValueError
        previous = None
        attempts = set()
        for event in events:
            if type(event) is not dict or set(event) != {"state", "attempt"}:
                raise ValueError
            state = records.admit(records.JobState, event["state"])
            records.serialize(state)
            attempt = (
                None
                if event["attempt"] is None
                else records.admit(records.Attempt, event["attempt"])
            )
            if attempt is not None:
                records.serialize(attempt)
            if state.job_id != self.spec.job_id:
                raise ValueError
            if state.status == "COMPLETE" and (
                state.output is None or state.output.availability != "verified"
            ):
                raise ValueError
            if previous is None:
                if state.status != "PENDING" or state.attempt_id is not None or attempt is not None:
                    raise ValueError
            else:
                records.transition(previous, state, attempt)
                if state.status == "CLAIMED":
                    if state.attempt_id in attempts:
                        raise ValueError
                    attempts.add(state.attempt_id)
            if len(attempts) > 16:
                raise ValueError
            previous = state
        return obj

    @_private
    def read(self):
        return self._read()

    def _read(self):
        """Return (validated envelope, SHA-256 revision); historical labels are not fresh proof."""
        self._assert()
        fd = os.open(
            self.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK, dir_fd=self.dirfd
        )
        try:
            st = os.fstat(fd)
            _checked_file(st, 0o600, stat.S_ISREG)
            if st.st_nlink != 1 or st.st_size > 524288:
                raise ValueError
            raw = bytearray()
            while len(raw) <= 524288:
                chunk = os.read(fd, min(65536, 524289 - len(raw)))
                if not chunk:
                    break
                raw.extend(chunk)
            raw = bytes(raw)
            self._assert()
            entry = os.stat(self.name, dir_fd=self.dirfd, follow_symlinks=False)
            if (entry.st_dev, entry.st_ino) != (st.st_dev, st.st_ino):
                raise ValueError
            obj = self._validate(raw)
            return obj, hashlib.sha256(raw).hexdigest()
        finally:
            original = sys.exception()
            failures = []
            try:
                self._close_file(fd, "read")
            except BaseException as exc:
                failures.append(exc)
            self._finish_cleanup(original, failures)

    def _commit(self, envelope, expected):
        raw = _json(envelope)
        self._validate(raw)
        name = ".stage-" + secrets.token_hex(24)
        fd = None
        stage_identity = None
        try:
            self._assert()
            fd = os.open(
                name,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC,
                0o600,
                dir_fd=self.dirfd,
            )
            stage_st = os.fstat(fd)
            stage_identity = (stage_st.st_dev, stage_st.st_ino)
            view = memoryview(raw)
            while view:
                n = os.write(fd, view)
                if n <= 0:
                    raise OSError("short write")
                view = view[n:]
            os.fsync(fd)
            closing, fd = fd, None
            self._close_file(closing, "stage")
            self._assert()
            stage_st = os.stat(name, dir_fd=self.dirfd, follow_symlinks=False)
            if (stage_st.st_dev, stage_st.st_ino) != stage_identity:
                raise ValueError
            try:
                _, revision = self._read()
            except FileNotFoundError:
                revision = None
            if revision != expected:
                raise JournalError("stale journal revision")
            os.replace(name, self.name, src_dir_fd=self.dirfd, dst_dir_fd=self.dirfd)
            os.fsync(self.dirfd)
            return self.read()
        finally:
            original = sys.exception()
            failures = []
            if fd is not None:
                try:
                    self._close_file(fd, "stage")
                except BaseException as exc:
                    failures.append(exc)
            try:
                st = os.stat(name, dir_fd=self.dirfd, follow_symlinks=False)
                if stage_identity is not None and (st.st_dev, st.st_ino) == stage_identity:
                    os.unlink(name, dir_fd=self.dirfd)
            except FileNotFoundError:
                pass
            except BaseException as exc:
                self.cleanup_attempts.append(("stage-unlink", "unknown"))
                self.pending = True
                failures.append(exc)
            self._finish_cleanup(original, failures)

    def _output(self, store, metadata_bytes, container_id):
        if type(store) is not derived_store.Store:
            raise ValueError
        metadata = batch._metadata(metadata_bytes)
        for key in ("dependencies", "rows", "codec_policy_fingerprint"):
            if metadata[key] != self.plan[key]:
                raise ValueError
        batch.load(store, container_id, metadata_bytes)
        return records.admit(
            records.OutputRef,
            {
                "ref": "sha256:" + container_id,
                "fingerprint": "sha256:" + hashlib.sha256(metadata_bytes).hexdigest(),
                "availability": "verified",
            },
        )

    @_private
    def verified_output(self, store, expected_metadata_bytes):
        envelope, _ = self.read()
        state = records.admit(records.JobState, envelope["events"][-1]["state"])
        if state.status != "COMPLETE" or state.output is None:
            raise JournalError("journal refused")
        output = self._output(store, expected_metadata_bytes, state.output.ref[7:])
        if output != state.output:
            raise JournalError("journal refused")
        return output

    @_private
    def repair_running_output(
        self, metadata_bytes, container_id, expected_revision, expected_state_bytes,
        *, store, validate_current, deadline_ms=5000,
    ):
        """Repair stale RUNNING materialization using an explicitly supplied output."""
        start = time.monotonic_ns()
        if (type(metadata_bytes) is not bytes or not 1 <= len(metadata_bytes) <= 131072
                or type(container_id) is not str
                or re.fullmatch(r"[0-9a-f]{64}", container_id) is None
                or type(expected_revision) is not str
                or re.fullmatch(r"[0-9a-f]{64}", expected_revision) is None
                or type(expected_state_bytes) is not bytes
                or not 1 <= len(expected_state_bytes) <= records.MAX_BYTES
                or type(deadline_ms) is not int or not 1 <= deadline_ms <= 120000
                or not callable(validate_current)):
            raise ValueError
        expected = records.admit(records.JobState, expected_state_bytes)
        if records.serialize(expected) != expected_state_bytes:
            raise ValueError
        plan_bytes = _json(self.plan)
        def deadline():
            if time.monotonic_ns() - start >= deadline_ms * 1000000:
                raise ValueError
        def current():
            deadline()
            envelope, revision = self._read()
            state = records.admit(records.JobState, envelope["events"][-1]["state"])
            if (revision != expected_revision or records.serialize(state) != expected_state_bytes
                    or state.status != "RUNNING" or state.job_id != self.spec.job_id
                    or not state.attempt_id or not state.owner_id or state.output is not None
                    or state.owner_id == self.owner_id):
                raise ValueError
            return envelope, state
        def epoch(stage):
            deadline()
            value = validate_current(plan_bytes, stage)
            deadline()
            if type(value) is not str or re.fullmatch(r"[0-9a-f]{64}", value) is None:
                raise ValueError
            return value
        envelope, state = current()
        repair_owner = self.owner_id
        first_epoch = epoch("before_repair_validation")
        output = self._output(store, metadata_bytes, container_id)
        second_epoch = epoch("before_repair_commit")
        if first_epoch != second_epoch:
            raise ValueError
        envelope, state = current()
        if self._output(store, metadata_bytes, container_id) != output:
            raise ValueError
        claimed = [event["state"] for event in envelope["events"]
                   if event["state"]["status"] == "CLAIMED"
                   and event["state"]["attempt_id"] == state.attempt_id]
        if len(claimed) != 1:
            raise ValueError
        observed = _observation_ms(state.updated_ms)
        terminal = records.admit(records.JobState, {
            "version": 1, "job_id": state.job_id, "status": "COMPLETE",
            "attempt_id": state.attempt_id, "owner_id": None, "updated_ms": observed,
            "output": output.model_dump(mode="json"),
        })
        attempt = records.admit(records.Attempt, {
            "version": 1, "job_id": state.job_id, "attempt_id": state.attempt_id,
            "request_id": None, "outcome": "COMPLETE", "started_ms": claimed[0]["updated_ms"],
            "ended_ms": observed, "input_tokens": None, "output_tokens": None,
            "diagnostic_code": "RECOVERED_VALID_OUTPUT", "output": output.model_dump(mode="json"),
        })
        records.transition(state, terminal, attempt)
        envelope["events"].append({"state": json.loads(records.serialize(terminal)),
                                   "attempt": json.loads(records.serialize(attempt))})
        deadline()
        self._assert()
        committed, revision = self._commit(envelope, expected_revision)
        deadline()
        if records.admit(records.JobState, committed["events"][-1]["state"]) != terminal:
            raise ValueError
        verified = self.verified_output(store, metadata_bytes)
        deadline()
        if verified != output:
            raise ValueError
        return OutputRepairResult(output, revision, state.attempt_id, state.owner_id,
                                  repair_owner, first_epoch, observed)

    @_private
    def append(
        self, state_bytes, attempt_bytes, expected_revision, *, store=None, metadata_bytes=None
    ):
        """CAS an admitted transition; COMPLETE requires fresh typed store validation."""
        if (
            type(state_bytes) is not bytes
            or (attempt_bytes is not None and type(attempt_bytes) is not bytes)
            or type(expected_revision) is not str
            or re.fullmatch(r"[0-9a-f]{64}", expected_revision) is None
        ):
            raise ValueError
        envelope, revision = self.read()
        if revision != expected_revision:
            raise JournalError("stale journal revision")
        state = records.admit(records.JobState, state_bytes)
        attempt = None if attempt_bytes is None else records.admit(records.Attempt, attempt_bytes)
        previous = records.admit(records.JobState, envelope["events"][-1]["state"])
        records.transition(previous, state, attempt)
        if state.status in ("CLAIMED", "RUNNING") and state.owner_id != self.owner_id:
            raise JournalError("journal refused")
        if state.status == "COMPLETE":
            if (
                state.output is None
                or self._output(store, metadata_bytes, state.output.ref[7:]) != state.output
            ):
                raise JournalError("journal refused")
        envelope["events"].append(
            {
                "state": json.loads(records.serialize(state)),
                "attempt": None if attempt is None else json.loads(records.serialize(attempt)),
            }
        )
        return self._commit(envelope, expected_revision)
