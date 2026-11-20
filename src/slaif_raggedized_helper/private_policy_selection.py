"""Private selection of an installed policy payload; storage is not selection.

Operator-side current-policy view update (ARCH 13.3-13.4, provenance E/I):
select already-installed genuinely admitted wire bytes as the current
policy under one existing cooperating root lock.  The existing payload
installer, publisher, capture reader and selection parser stay
byte-exact; this module owns only the selection transaction.  One
trusted entry takes the exact wire bytes, the trusted private
directory and one bounded monotonic admission deadline; it rejects
invalid inputs before any protected namespace work, admits the entire
candidate through the production ``admit_policy_bytes`` with the
established wire envelope, and derives the canonical digest name from
the SHA-256 of the exact bytes in bounded chunks.  The input supplies
no explicit name, record, digest, generation, parsed DTO, callback or
selector.

The transaction reuses the publisher's shared process-wide slot pool,
the no-follow namespace walk, the directory-inode writer lock, the
namespace identity checks and the held-fd verification, held in one
bounded transaction and one lock hold: it reads and parses the exact
canonical current record (absent, malformed or exhausted records
refuse), allocates the observed generation plus one (same-wire
reselection and A-B-A always allocate a new generation), verifies the
installed digest-named payload against the exact admitted bytes
through the held-fd path including its file flush, requires a verified
root-directory flush before the new selector becomes visible, stages
the new canonical record in the single reserved per-root name
``.current-policy.stage`` through an exclusive no-follow create, seals
it, verifies the sealed name with the exact canonical bytes and the
held staging identity, rechecks the namespace and the prior selection
by its full stable signature, and publishes it with one fd-relative
``os.replace``.  A preexisting reserved entry of any identity or type
refuses before creating or changing any namespace entry and is never
removed by this module; the only removal this module performs is the
pre-attempt unlink of the still-proven-owned staging inode,
identity-verified under the same held lock; an interrupted unlink is
never retried, and its state is established by one fresh bounded
observation or stays unresolved.  After the replace attempt, the
linked new selector is checked with exact bytes and staging identity,
the directory is flushed, and the same namespace and selected record
are confirmed by the final readback.  No success after the one
deadline.  The old selected name is preserved on every failure before
the replace attempt, and no automatic selector restoration exists
after it.  A fault in the stage observation never bypasses the
pending latch, the descriptor cleanup or the guard release, and the
first non-Exception interruption keeps its identity when stage and
cleanup faults collide.

Fixed content-free refusals separate the selection state (selection
before possible effect, possible effect, verified durable) from the
descriptor cleanup state and the observed absent/present/unresolved
reserved stage.  An attempted replace may act and then raise; a later
flush, readback, deadline or cleanup fault never proves rollback and
never conflates an absence proof with a selector outcome.  The
publisher's descriptor cleanup closes only definitely-owned
descriptors and never unlinks names; it is not claimed to.  Actual
first non-Exception interruption identity, bounded creator-process
descriptor custody and truthful incomplete custody are preserved.
All use is synthetic and operator-owned; no actual current
authorization invocation happens here.
"""

from dataclasses import dataclass
from enum import Enum
import errno
import hashlib
import json
import os
import stat
import sys
import time

from .policy_selection import (
    _KIND,
    _MAX_GENERATION,
    _MAX_RECORD_BYTES,
    parse_policy_selection,
)
from .private_policy_capture import _root_path_ok
from .private_report_publication import (
    _CHUNK,
    _CREATOR,
    _Conflict,
    _Failure,
    _READ_FLAGS,
    _cleanup,
    _deadline,
    _file_ok,
    _file_signature,
    _lock,
    _namespace,
    _release,
    _reserve,
    _tick,
    _verify,
    _walk,
    Cleanup,
    Publication,
    PublicationError,
)
from .supplied_policy_wire import (
    _MAX_WIRE_BYTES,
    _MIN_WIRE_BYTES,
    admit_policy_bytes,
)

__all__ = [
    "PolicySelectError",
    "PolicySelectOutcome",
    "PolicySelectReceipt",
    "Stage",
    "select_installed_policy",
]

_SELECTION_NAME = "current-policy.json"
_STAGE_NAME = ".current-policy.stage"
_CLEANUP_NOTE = "private policy selection cleanup pending"


class Stage(Enum):
    """Reported reserved staging-name state: observed ABSENT or
    PRESENT, or UNRESOLVED when the name was not observed or the
    observation was uncertain."""

    ABSENT = "ABSENT"
    PRESENT = "PRESENT"
    UNRESOLVED = "UNRESOLVED"


class PolicySelectOutcome(Enum):
    SELECTED = "SELECTED"


@dataclass(frozen=True, repr=False, slots=True)
class PolicySelectReceipt:
    outcome: PolicySelectOutcome
    selection: Publication
    cleanup: Cleanup
    generation: int
    wire_digest: str
    selection_bytes: bytes


class PolicySelectError(Exception):
    """Fixed content-free refusal with the truthful three states."""

    __slots__ = ("_selection", "_cleanup", "_stage")

    def __init__(self, selection, cleanup, stage):
        super().__init__("private policy selection refused")
        self._selection = selection
        self._cleanup = cleanup
        self._stage = stage

    @property
    def selection(self):
        return self._selection

    @property
    def cleanup(self):
        return self._cleanup

    @property
    def stage(self):
        return self._stage


def _refuse():
    # Nothing was observed: the reserved name is reported unresolved.
    raise PolicySelectError(
        Publication.NOT_PUBLISHED, Cleanup.CLEAN, Stage.UNRESOLVED
    ) from None


def _selection_error(selection, cleanup, stage):
    return PolicySelectError(selection, cleanup, stage)


def _render_record(generation, wire_bytes, wire_sha256):
    # The exact canonical record: sorted keys, compact separators,
    # ASCII; the caller passes it through the real parser.
    return json.dumps(
        {
            "generation": generation,
            "kind": _KIND,
            "schema": 1,
            "wire_bytes": wire_bytes,
            "wire_sha256": wire_sha256,
        },
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("ascii")


def _read_current(slot, end):
    # Bounded no-follow read of the current canonical record under the
    # held lock.  Returns (parsed record, observed full stable
    # signature) or None when the entry is absent at the bounded
    # observation; a non-regular, conflicting or noncanonical current
    # entry is a pre-attempt conflict.
    _tick(end)
    try:
        os.stat(_SELECTION_NAME, dir_fd=slot.root, follow_symlinks=False)
    except FileNotFoundError:
        return None
    try:
        fd = slot.opened(_SELECTION_NAME, _READ_FLAGS, parent=slot.root)
    except FileNotFoundError:
        return None
    except OSError as exc:
        if exc.errno in (errno.ELOOP, errno.ENXIO, errno.EACCES, errno.EPERM):
            raise _Conflict() from None
        raise
    try:
        _tick(end)
        before = os.fstat(fd)
        _tick(end)
        if (
            not _file_ok(before, before.st_size, 1)
            or not 1 <= before.st_size <= _MAX_RECORD_BYTES
        ):
            raise _Conflict()
        data = bytearray()
        while len(data) < before.st_size:
            _tick(end)
            chunk = os.read(fd, min(_CHUNK, before.st_size - len(data)))
            _tick(end)
            if not chunk:
                raise _Conflict()
            data.extend(chunk)
        _tick(end)
        if os.read(fd, 1):
            raise _Conflict()
        _tick(end)
        after = os.fstat(fd)
        _tick(end)
        entry = os.stat(_SELECTION_NAME, dir_fd=slot.root, follow_symlinks=False)
        _tick(end)
        if _file_signature(before) != _file_signature(after) or _file_signature(
            after
        ) != _file_signature(entry):
            raise _Conflict()
        raw = bytes(data)
        signature = _file_signature(before)
    finally:
        active = sys.exc_info()[1]
        try:
            slot.close(fd)
        except BaseException as close_error:
            if active is None or (
                isinstance(active, Exception) and not isinstance(close_error, Exception)
            ):
                raise
    try:
        return parse_policy_selection(raw), signature
    except Exception:
        raise _Conflict() from None


def _stage_absent(slot, end):
    # The single reserved per-root staging name: a preexisting entry of
    # any identity or type refuses before creating or changing any
    # namespace entry, with no unlink and no re-create, across
    # processes and restarts.
    _tick(end)
    try:
        os.stat(_STAGE_NAME, dir_fd=slot.root, follow_symlinks=False)
    except FileNotFoundError:
        return
    raise _Conflict()


def _open_stage(slot, record, end):
    # Exclusive no-follow create, tracked before acquisition, actual
    # 0600 owned regular file with one link on the root's device,
    # bounded writes, seal to 0400, flush, and exact record bytes with
    # the bounded staging identity rechecked.
    _tick(end)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC
    fd = slot.opened(_STAGE_NAME, flags, 0o600, parent=slot.root)
    _tick(end)
    st = os.fstat(fd)
    _tick(end)
    # Tracked before verification: a fault below still leaves the held
    # descriptor provably owned for pre-attempt resolution.
    slot.stage = fd
    slot.stage_identity = (st.st_dev, st.st_ino)
    if (
        not stat.S_ISREG(st.st_mode)
        or st.st_uid != os.geteuid()
        or stat.S_IMODE(st.st_mode) != 0o600
        or st.st_nlink != 1
        or st.st_dev != os.fstat(slot.root).st_dev
    ):
        raise _Failure()
    view = memoryview(record)
    offset = 0
    while offset < len(record):
        _tick(end)
        count = os.write(fd, view[offset : min(offset + _CHUNK, len(record))])
        _tick(end)
        if count <= 0:
            raise _Failure()
        offset += count
    os.fchmod(fd, 0o400)
    _tick(end)
    os.fsync(fd)
    _tick(end)
    st = os.fstat(fd)
    _tick(end)
    if not _file_ok(st, len(record), 1) or (st.st_dev, st.st_ino) != slot.stage_identity:
        raise _Failure()


def _prior_unchanged(slot, end, prior_signature):
    # Recheck the linked prior selection before the one fd-relative
    # replace: the full stable signature, metadata only, no second
    # full read.
    _tick(end)
    st = os.stat(_SELECTION_NAME, dir_fd=slot.root, follow_symlinks=False)
    if _file_signature(st) != prior_signature:
        raise _Conflict()


def _observe_stage(slot):
    # Bounded no-follow observation of the reserved name; an uncertain
    # observation stays unresolved even if an earlier state looked
    # known.
    try:
        os.stat(_STAGE_NAME, dir_fd=slot.root, follow_symlinks=False)
    except FileNotFoundError:
        return Stage.ABSENT
    except OSError:
        return Stage.UNRESOLVED
    return Stage.PRESENT


def _resolve_stage(slot):
    # Pre-attempt resolution: unlink only the still-proven-owned
    # staging inode, identity-verified under the same held lock, with
    # one unlink that is never retried after an interruption; an
    # interrupted unlink establishes the state with one fresh bounded
    # observation or stays unresolved; the post-unlink observation is
    # bounded.
    proven = False
    if slot.stage is not None and slot.stage_identity is not None:
        try:
            st = os.fstat(slot.stage)
            proven = (
                (st.st_dev, st.st_ino) == slot.stage_identity
                and stat.S_ISREG(st.st_mode)
                and st.st_uid == os.geteuid()
                and st.st_nlink == 1
            )
        except OSError:
            proven = False
    if proven:
        try:
            entry = os.stat(_STAGE_NAME, dir_fd=slot.root, follow_symlinks=False)
        except FileNotFoundError:
            return Stage.ABSENT
        except OSError:
            return Stage.UNRESOLVED
        if (entry.st_dev, entry.st_ino) == slot.stage_identity and entry.st_nlink == 1:
            try:
                os.unlink(_STAGE_NAME, dir_fd=slot.root)
            except OSError:
                # An interrupted unlink may have acted: never retried;
                # establish the state with one fresh bounded
                # observation, or stay unresolved when no safe
                # observation is available.
                return _observe_stage(slot)
            try:
                os.stat(_STAGE_NAME, dir_fd=slot.root, follow_symlinks=False)
            except FileNotFoundError:
                return Stage.ABSENT
            except OSError:
                return Stage.UNRESOLVED
            return Stage.PRESENT
    return _observe_stage(slot)


def _transact_select(parts, final, wire_bytes, wire_digest, end):
    # One bounded transaction and one lock hold: pool reservation,
    # no-follow namespace walk, directory-inode writer lock, namespace
    # stability, the current-record read and generation allocation,
    # the held-fd payload verification with its file flush, the
    # verified root-directory flush before the new selector becomes
    # visible, the single reserved staging entry, one fd-relative
    # replace, the post-replace check, the directory flush and the
    # namespace and selected-record confirmation.  The conservative
    # state, the cleanup/retirement and guard policy and the
    # ordinary-failure normalization mirror the shared publisher
    # transaction; the payload installer and the shared _transact are
    # never called, so no second directory lock exists here.
    try:
        slot = _reserve()
    except PublicationError as exc:
        raise _selection_error(
            exc.publication, exc.cleanup, Stage.UNRESOLVED
        ) from None
    # Known only after a bounded observation under the associated
    # locked root; an unobserved or uncertain state stays unresolved.
    stage_state = Stage.UNRESOLVED
    attempted = False
    root_verified = False
    failure = None
    stage_fault = None
    try:
        slot.root = _walk(slot, parts, end)
        _lock(slot, end)
        _namespace(slot, parts, end)
        # The first namespace recheck verifies the association of the
        # locked root with the requested path; a successful flock by
        # itself does not.
        root_verified = True
        observed = _read_current(slot, end)
        if observed is None:
            # Absent current record: no selector exists and nothing
            # was touched; generation-1 initialization is separate.
            raise _Failure()
        current, prior_signature = observed
        generation = current.generation + 1
        if generation > _MAX_GENERATION:
            # Exhausted generation space: refuse, selector intact.
            raise _Failure()
        record = _render_record(generation, len(wire_bytes), wire_digest)
        parse_policy_selection(record)
        # Verify the already installed digest-named payload against
        # the exact admitted bytes through the held-fd path,
        # including the verified file flush; absent or conflicting
        # payloads refuse with the old selector intact.
        if not _verify(slot, final, wire_bytes, end):
            raise _Failure()
        # Verified root-directory flush before the new selector
        # becomes visible; required even for admissible existing
        # bytes that do not carry a prior installer receipt.
        os.fsync(slot.root)
        _tick(end)
        _stage_absent(slot, end)
        _open_stage(slot, record, end)
        # Verify the staged name itself before the attempt: exact
        # canonical bytes and the held staging identity, not just the
        # later selector readback.
        if not _verify(
            slot, _STAGE_NAME, record, end, expected_identity=slot.stage_identity
        ):
            raise _Failure()
        # Final namespace and prior-selection rechecks after the
        # complete staged-name verify, immediately before the one
        # replace: a prior-selection change observed after that read
        # is still caught.  The prior selector keeps its one full read
        # from the initial read under the lock and no second lock.
        try:
            _namespace(slot, parts, end)
        except BaseException:
            # The locked root is no longer verified as the requested
            # path: no reported stage state may claim that root.
            root_verified = False
            raise
        _prior_unchanged(slot, end, prior_signature)
        _tick(end)
        slot.state = Publication.POSSIBLY_PUBLISHED
        attempted = True
        os.replace(_STAGE_NAME, _SELECTION_NAME, src_dir_fd=slot.root, dst_dir_fd=slot.root)
        _tick(end)
        if not _verify(
            slot, _SELECTION_NAME, record, end, expected_identity=slot.stage_identity
        ):
            raise _Failure()
        _tick(end)
        os.fsync(slot.root)
        _tick(end)
        try:
            _namespace(slot, parts, end)
        except BaseException:
            # The locked root is no longer verified as the requested
            # path: no reported stage state may claim that root.
            root_verified = False
            raise
        # Final readback: byte-equal with the staging identity
        # signature after the verified directory flush and the
        # namespace recheck; only this proves durable.
        if not _verify(
            slot, _SELECTION_NAME, record, end, expected_identity=slot.stage_identity
        ):
            raise _Failure()
        slot.state = Publication.DURABLE
        stage_state = Stage.ABSENT
        _tick(end)
    except BaseException as exc:
        failure = exc
        # CONFLICT is assigned only to pre-attempt namespace
        # conflicts: an unresolved post-attempt state keeps
        # POSSIBLY_PUBLISHED and is never downgraded.
        if isinstance(exc, _Conflict) and slot.state is not Publication.POSSIBLY_PUBLISHED:
            slot.state = Publication.CONFLICT
        try:
            if attempted:
                # Post-attempt: bounded observation of the reserved
                # name without automatic unlink; an absence proof
                # never proves a selector outcome.  Reported only
                # while the held root's association with the
                # requested path is still verified.
                if root_verified:
                    stage_state = _observe_stage(slot)
            elif slot.stage is not None:
                # Pre-attempt custody of the positively owned staging
                # inode in the previously associated held root:
                # identity-verified resolution and the one
                # never-retried unlink run regardless of any later
                # association loss; the result is reported only while
                # the association is still verified, otherwise the
                # requested root's reserved name was not observed.
                resolved = _resolve_stage(slot)
                stage_state = resolved if root_verified else Stage.UNRESOLVED
            elif root_verified:
                # Pre-attempt under the associated locked root:
                # observe.  A fault before the verified association
                # keeps the unresolved state.
                stage_state = _observe_stage(slot)
        except BaseException as stage_exc:
            # A stage observation fault is a later secondary fault:
            # it never bypasses the pending latch, the descriptor
            # cleanup or the guard release below, and the stage stays
            # unresolved.
            stage_fault = stage_exc
            stage_state = Stage.UNRESOLVED
    # Recovery-visible pending before risky cleanup work: an
    # interruption outside the per-fd close try must never leave a
    # non-clean slot invisible to retry_cleanup.
    slot.pending = True
    state = slot.state
    clean = False
    cleanup_interrupt = None
    boundary_error = None
    guard_error = None
    try:
        clean, cleanup_interrupt = _cleanup(slot, end)
        if clean:
            _release(slot)
    except BaseException as exc:
        boundary_error = exc
    try:
        slot.guard.release()
    except BaseException as exc:
        guard_error = exc
    # One coherent cleanup/retirement/guard policy: the latched
    # primary and the first caught non-Exception interruption outrank
    # later ordinary faults; the stage observation fault is a later
    # secondary fault that keeps the first non-Exception identity
    # when stage and cleanup faults collide; ordinary faults never
    # escape raw but degrade the conservative count; an ambiguous
    # guard release is never retried blindly and no descriptor work
    # follows the ownership transfer.
    first_fault = boundary_error if boundary_error is not None else guard_error
    if failure is not None and not isinstance(failure, Exception):
        # The first non-Exception interruption outranks later faults;
        # chain from the nearest later fault, the stage observation
        # fault preceding the cleanup and guard faults.
        context = stage_fault if stage_fault is not None else first_fault
        if context is not None:
            raise failure from context
        if not clean:
            try:
                failure.add_note(_CLEANUP_NOTE)
            except BaseException:
                pass
        raise failure
    if (
        boundary_error is not None
        and not isinstance(boundary_error, Exception)
        and cleanup_interrupt is None
        and (stage_fault is None or isinstance(stage_fault, Exception))
        and (failure is None or isinstance(failure, Exception))
    ):
        earlier = stage_fault if stage_fault is not None else failure
        if earlier is None:
            raise boundary_error
        raise boundary_error from earlier
    if (
        guard_error is not None
        and not isinstance(guard_error, Exception)
        and cleanup_interrupt is None
        and (stage_fault is None or isinstance(stage_fault, Exception))
        and (failure is None or isinstance(failure, Exception))
    ):
        raise guard_error
    if stage_fault is not None and not isinstance(stage_fault, Exception):
        if failure is not None:
            raise stage_fault from failure
        if first_fault is not None:
            # A later cleanup or guard interruption follows the stage
            # interruption: keep both identities by context.
            stage_fault.__context__ = first_fault
        raise stage_fault
    if first_fault is not None:
        clean = False
    if cleanup_interrupt is not None and (failure is None or isinstance(failure, Exception)):
        failure = cleanup_interrupt
    if failure is not None and not isinstance(failure, Exception):
        if not clean:
            try:
                failure.add_note(_CLEANUP_NOTE)
            except BaseException:
                pass
        raise failure
    if failure is not None or not clean:
        raise _selection_error(
            state, Cleanup.CLEAN if clean else Cleanup.PENDING, stage_state
        ) from None
    return generation, record


def select_installed_policy(wire_bytes, *, directory, deadline_ms=30000):
    """Select exact admitted wire bytes as the current policy.

    Takes the exact wire bytes, the trusted private directory and one
    bounded monotonic admission deadline.  The entire candidate is
    admitted by the production ``admit_policy_bytes`` with the
    established wire envelope before any protected namespace work;
    the canonical digest and record are derived from the exact bytes.
    Returns a receipt reporting the verified durable selection: the
    allocated generation, the wire digest and the exact canonical
    record bytes; a fixed content-free refusal reports the selection,
    descriptor-cleanup and reserved-stage states and nothing else.
    """
    # Invalid inputs are rejected before any protected namespace work.
    if type(deadline_ms) is not int or not 1 <= deadline_ms <= 30000:
        _refuse()
    end = _deadline(deadline_ms)
    if os.getpid() != _CREATOR:
        # Shared pool custody is process-bound; the truthful state is
        # the publisher's own for an unowned pool.
        raise PolicySelectError(
            Publication.NOT_PUBLISHED, Cleanup.PENDING, Stage.UNRESOLVED
        ) from None
    if (
        type(wire_bytes) is not bytes
        or not _MIN_WIRE_BYTES <= len(wire_bytes) <= _MAX_WIRE_BYTES
    ):
        _refuse()
    if not _root_path_ok(directory):
        _refuse()
    try:
        _tick(end)
        # Production admission of the entire candidate, established
        # wire envelope; structural and domain admission stays in the
        # typed wire decoder.
        admit_policy_bytes(wire_bytes)
        _tick(end)
        # Derive the canonical digest of the exact bytes in bounded
        # chunks.
        digest = hashlib.sha256()
        view = memoryview(wire_bytes)
        for offset in range(0, len(wire_bytes), _CHUNK):
            _tick(end)
            digest.update(view[offset : offset + _CHUNK])
        _tick(end)
    except Exception:
        # Ordinary admission, deadline or hashing failure before any
        # protected namespace work: nothing was reserved or touched,
        # so the truthful state is not-published, clean and stage-
        # absent.  Non-Exception interruptions keep their identity.
        _refuse()
    wire_digest = digest.hexdigest()
    final = wire_digest + ".bin"
    parts = directory[1:].split("/")
    generation, record = _transact_select(parts, final, wire_bytes, wire_digest, end)
    # Final checkpoint before the receipt can return: no successful
    # result after a cooperative expiry.  The transaction returns only
    # after verified durability, so the truthful late state is
    # durable, clean and stage-absent.
    if time.monotonic() >= end:
        raise PolicySelectError(Publication.DURABLE, Cleanup.CLEAN, Stage.ABSENT) from None
    return PolicySelectReceipt(
        PolicySelectOutcome.SELECTED,
        Publication.DURABLE,
        Cleanup.CLEAN,
        generation,
        wire_digest,
        record,
    )
