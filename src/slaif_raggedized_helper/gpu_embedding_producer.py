"""One-batch durable GPU producer; composition under development."""

import hashlib
import json
import os
import re
import secrets
import sys
import time

from . import embedding_batch_store as batch


class ProducerRefused(ValueError):
    """Content-free refusal, optionally retaining a pending cleanup owner."""

    def __init__(self, *, owner=None):
        super().__init__("GPU producer refused")
        self.owner = owner
        self.pending = owner is not None


def _wire(value):
    return json.dumps(
        value, sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(",", ":")
    ).encode("utf-8")


def _now(previous):
    value = time.time_ns() // 1_000_000
    if type(value) is not int or value < previous or value > 2**63 - 1:
        raise ValueError
    return value


def _authorize(provider, data, boundary, epoch=None):
    value = provider(data, boundary)
    if type(value) is not str or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise ValueError
    if epoch is not None and value != epoch:
        raise ValueError
    return value


def _metadata(plan, encoded):
    return _wire(
        {
            "schema": 1,
            "kind": "embedding-batch-v1",
            "dependencies": plan["dependencies"],
            "rows": plan["rows"],
            "codec_policy_fingerprint": plan["codec_policy_fingerprint"],
            "vector_container_sha256": encoded.container_sha256,
            "vector_payload_sha256": encoded.payload_sha256,
        }
    )


def _reuse_metadata(store, ref, plan):
    if type(ref) is not str or re.fullmatch(r"sha256:[0-9a-f]{64}", ref) is None:
        raise ValueError
    snapshot = store.load(ref[7:])
    data = _wire(json.loads(snapshot.manifest)["metadata"])
    obj = batch._metadata(data)
    if any(obj[k] != plan[k] for k in ("dependencies", "rows", "codec_policy_fingerprint")):
        raise ValueError
    return data


def _output(metadata, identifier):
    if type(identifier) is not str or re.fullmatch(r"[0-9a-f]{64}", identifier) is None:
        raise ValueError
    return {
        "ref": "sha256:" + identifier,
        "fingerprint": "sha256:" + hashlib.sha256(metadata).hexdigest(),
        "availability": "verified",
    }


# Exact exception-object association avoids stale ID lookup and remains available
# even if the original interruption refuses attribute assignment. Entries are
# removed when the associated owner is fully drained.
_retained_cleanup = []
_retained_associations = []


def _attach_owner(error, owner):
    if not any(item is owner for item in _retained_cleanup):
        _retained_cleanup.append(owner)
    if not any(exc is error and item is owner for exc, item in _retained_associations):
        _retained_associations.append((error, owner))
    try:
        matches = [item for exc, item in _retained_associations if exc is error]
        error.cleanup_owner = owner if len(matches) == 1 else None
    except BaseException:
        pass


def pending_cleanup(error):
    """Return the exact owner only when this exception has a unique association."""
    matches = [owner for exc, owner in _retained_associations if exc is error]
    return matches[0] if len(matches) == 1 else None


def _owner_for(error):
    try:
        return getattr(error, "cleanup_owner", None) or getattr(error, "owner", None)
    except BaseException:
        return None


def _prefer(original, later):
    """Preserve the first interrupt, but prefer it over an ordinary error."""
    if original is None or (isinstance(original, Exception) and not isinstance(later, Exception)):
        return later
    return original


class _CleanupOwner:
    """Retain actual resource owners and the lease until both cleanup paths finish."""

    def __init__(self, session, worker, lease, uncertainty=(), preparation=None, capture=None):
        self.creator = os.getpid()
        self.session = session
        self.worker = worker
        self.preparation = preparation
        self.capture = capture
        self.lease = lease
        self.uncertainty = list(uncertainty)

    def close(self):
        from . import gpu_embedding_worker, gpu_worker_launch, isolated_gpu_embedding

        if self.creator != os.getpid():
            raise ProducerRefused(owner=self)
        error = None
        if self.session is not None:
            try:
                isolated_gpu_embedding.GPUTextEmbeddingSession.close(self.session)
                self.session = None
            except BaseException as caught:
                error = _prefer(error, caught)
        if self.worker is not None:
            try:
                gpu_embedding_worker.GPUEmbeddingWorker.close(self.worker)
                self.worker = None
                self.preparation = None  # parent consumed it
            except BaseException as caught:
                error = _prefer(error, caught)
        # A capture may reveal the actual successful handoff after interrupted return.
        # A live/pending parent remains the sole owner allowed to drain that handoff.
        if self.worker is None and self.capture is not None and self.preparation is None:
            try:
                if type(self.capture) is not gpu_worker_launch.PreparationOwner:
                    raise ValueError
                self.preparation = gpu_worker_launch.PreparationOwner.prepared.__get__(
                    self.capture, gpu_worker_launch.PreparationOwner
                )
            except BaseException as caught:
                error = _prefer(error, caught)
                # Do not close capture or journal when handoff state is unknown.
                if error is not None:
                    raise error
        if self.worker is None and self.preparation is not None:
            try:
                preparation = self.preparation
                gpu_worker_launch.PreparedLaunch.close(preparation)
                self.preparation = None
                _retained_cleanup[:] = [
                    item for item in _retained_cleanup if item is not preparation
                ]
            except BaseException as caught:
                error = _prefer(error, caught)
        if self.worker is None and self.preparation is None and self.capture is not None:
            try:
                gpu_worker_launch.PreparationOwner.close(self.capture)
                self.capture = None
            except BaseException as caught:
                error = _prefer(error, caught)
        if (
            self.session is None
            and self.worker is None
            and self.preparation is None
            and self.capture is None
            and not self.uncertainty
            and self.lease is not None
        ):
            try:
                self.lease.__exit__(None, None, None)
                self.lease = None
            except BaseException as caught:
                # Journal close already performed its finite descriptor cleanup.
                # Preserve its actual owner; never repeat an uncertain close.
                self.uncertainty.append(self.lease)
                self.lease = None
                error = _prefer(error, caught)
        if error is not None:
            raise error
        if self.uncertainty:
            raise ProducerRefused(owner=self)
        _retained_cleanup[:] = [item for item in _retained_cleanup if item is not self]
        _retained_associations[:] = [item for item in _retained_associations if item[1] is not self]


def _vector(vectors, row_count):
    """Bind normalized rows to the exact payload before typed encoding."""
    import numpy as np

    from . import embedding_vectors, vector_codec

    if (
        type(vectors) is not embedding_vectors.NormalizedVectors
        or vectors.policy_id != embedding_vectors.POLICY_ID
        or type(vectors.rows) is not tuple
        or len(vectors.rows) != row_count
        or any(
            type(row) is not tuple
            or len(row) != 1024
            or any(type(value) is not float for value in row)
            for row in vectors.rows
        )
        or type(vectors.payload) is not bytes
        or len(vectors.payload) != row_count * 4096
        or hashlib.sha256(vectors.payload).hexdigest() != vectors.sha256
    ):
        raise ValueError
    matrix = np.asarray(vectors.rows, dtype="<f4", order="C")
    if matrix.tobytes() != vectors.payload:
        raise ValueError
    return vector_codec.encode(matrix, batch.POLICY)


def _observe(session, prepared, definition):
    """Read the registered bridge plan under its actual retained owner lock."""
    from . import isolated_gpu_embedding as bridge

    cls = bridge.GPUTextEmbeddingSession
    if type(session) is not cls:
        raise ValueError
    owner = cls._acquire(session)
    lock = owner[2]
    try:
        cls._check(session)
        actual = owner[4][3]
        if (
            type(actual) is not bridge.PlannedContract
            or actual.execution_record != prepared.predicted_record
            or actual.native_runtime_record != prepared.native_runtime_record
            or actual.space_id != prepared.space_id
            or actual.definition_fingerprint != definition.fingerprint()
            or actual.intended_execution_fingerprint != prepared.intended_execution_fingerprint
            or bridge.validate_record(actual.execution_record, actual.native_runtime_record)
            != actual.execution_fingerprint
            or hashlib.sha256(actual.execution_record).hexdigest() != prepared.execution_fingerprint
        ):
            raise ValueError
        return actual
    finally:
        lock.release()


def _validate_encoded(session, prepared, plan, definition, encoded):
    """Check the actual session result against source rows and both record identities."""
    from . import embedding_tokenizer, isolated_gpu_embedding as bridge

    cls = bridge.GPUTextEmbeddingSession
    if (
        type(encoded) is not bridge.EncodedBatch
        or encoded.execution_record != prepared.predicted_record
        or encoded.native_runtime_record != prepared.native_runtime_record
        or encoded.execution_fingerprint
        != bridge.validate_record(prepared.predicted_record, prepared.native_runtime_record)
        or encoded.space_id != prepared.space_id
        or encoded.space_id != plan["dependencies"]["space_id"]
        or encoded.definition_fingerprint != definition.fingerprint()
        or encoded.intended_execution_fingerprint != prepared.intended_execution_fingerprint
        or plan["dependencies"]["execution_fingerprint"] != prepared.execution_fingerprint
        or type(encoded.receipts) is not tuple
        or len(encoded.receipts) != len(plan["rows"])
        or len(prepared.texts) != len(plan["rows"])
    ):
        raise ValueError
    owner = cls._acquire(session)
    lock = owner[2]
    try:
        cls._check(session)
        nonces = set()
        for receipt, row, text in zip(encoded.receipts, plan["rows"], prepared.texts, strict=True):
            if (
                type(receipt) is not embedding_tokenizer.TokenIDReceipt
                or receipt.input_sha256 != row["input_sha256"]
                or receipt.count != row["token_count"]
                or receipt.nonce in nonces
            ):
                raise ValueError
            cls._receipt(session, receipt, text)
            if receipt.nonce not in owner[8]:
                raise ValueError
            nonces.add(receipt.nonce)
    finally:
        lock.release()
    return _vector(encoded.vectors, len(plan["rows"]))


class _Attempt:
    """Append one actual owned journal attempt with revision checks."""

    def __init__(self, handle, prepared, store, revision, started, attempt_id):
        self.handle = handle
        self.prepared = prepared
        self.store = store
        self.revision = revision
        self.started = started
        self.attempt_id = attempt_id

    def append(self, status, timestamp, output=None, metadata=None):
        if status not in (
            "CLAIMED",
            "RUNNING",
            "COMPLETE",
            "CANCELLED",
            "FAILED",
            "UNKNOWN_COMPLETION",
        ):
            raise ValueError
        terminal = status not in ("CLAIMED", "RUNNING")
        job_id = self.prepared.spec.job_id
        state = _wire(
            dict(
                version=1,
                job_id=job_id,
                status=status,
                attempt_id=self.attempt_id,
                owner_id=None if terminal else self.handle.owner_id,
                updated_ms=timestamp,
                output=output,
            )
        )
        attempt = None
        if terminal:
            attempt = _wire(
                dict(
                    version=1,
                    job_id=job_id,
                    attempt_id=self.attempt_id,
                    request_id=None,
                    outcome=status,
                    started_ms=self.started,
                    ended_ms=timestamp,
                    input_tokens=None,
                    output_tokens=None,
                    diagnostic_code=None,
                    output=output,
                )
            )
        kwargs = {"store": self.store, "metadata_bytes": metadata} if status == "COMPLETE" else {}
        _, self.revision = self.handle.append(state, attempt, self.revision, **kwargs)

    def reconcile(self, dispatch_attempted):
        """Reread after errors; never overwrite an already committed terminal state."""
        envelope, self.revision = self.handle.read()
        current = envelope["events"][-1]["state"]
        status = current["status"]
        if status in ("CLAIMED", "RUNNING"):
            if (
                current["attempt_id"] != self.attempt_id
                or current["owner_id"] != self.handle.owner_id
            ):
                raise ValueError
            final = (
                "CANCELLED"
                if status == "CLAIMED"
                else "UNKNOWN_COMPLETION"
                if dispatch_attempted
                else "FAILED"
            )
            self.append(final, _now(current["updated_ms"]))
            return final
        return status


from dataclasses import asdict, dataclass  # noqa: E402


@dataclass(frozen=True)
class LaunchInputs:
    """Trusted internal fixed launch inputs, not caller authorization."""

    source_root: str
    staging_root: str
    runtime_root: str
    packages_root: str
    lease_root: str
    device: object
    drivers: tuple
    resource: object
    wire_policy: object


def _launch_snapshot(inputs, reservation):
    from . import gpu_worker_launch as launch, gpu_worker_protocol as wire

    if type(inputs) is not LaunchInputs:
        raise ValueError
    for path in (
        inputs.source_root,
        inputs.staging_root,
        inputs.runtime_root,
        inputs.packages_root,
        inputs.lease_root,
    ):
        if (
            type(path) is not str
            or not path.startswith("/")
            or path == "/"
            or os.path.normpath(path) != path
            or len(path.encode()) > 4096
        ):
            raise ValueError
    if (
        type(inputs.device) is not launch.DevicePlan
        or type(inputs.resource) is not launch.ResourcePolicy
        or type(inputs.wire_policy) is not wire.Policy
    ):
        raise ValueError
    launch.DevicePlan(inputs.device.host_id, inputs.device.device_uuid, inputs.device.nodes)
    launch._driver_list(inputs.drivers)
    launch.ResourcePolicy(**asdict(inputs.resource))
    wire.Policy(**asdict(inputs.wire_policy))
    launch._reservation(reservation, inputs.device)
    return _wire(asdict(inputs))


def _prepare(inputs, reservation, snapshot, manifest, root, definition, token, inventory, capture):
    from . import gpu_worker_launch as launch

    if _launch_snapshot(inputs, reservation) != snapshot:
        raise ValueError
    result = launch.prepare(
        source_root=inputs.source_root,
        staging_root=inputs.staging_root,
        runtime_root=inputs.runtime_root,
        packages_root=inputs.packages_root,
        lease_root=inputs.lease_root,
        device=inputs.device,
        drivers=inputs.drivers,
        resource=inputs.resource,
        wire_policy=inputs.wire_policy,
        reservation=reservation,
        artifact_root=str(root),
        manifest=manifest,
        definition=definition,
        tokenizer=token,
        inventory_id=inventory,
        preparation_owner=capture,
    )
    if _launch_snapshot(inputs, reservation) != snapshot:
        raise ValueError
    return result


@dataclass(frozen=True)
class Result:
    job_id: str
    output_ref: str
    metadata: bytes
    batch: batch.ValidatedBatch
    execution_record: bytes
    native_runtime_record: bytes
    execution_fingerprint: str
    reused: bool


def produce(
    original_store,
    bundle_metadata_bytes,
    bundle_members,
    chunk_ids,
    manifest_bytes,
    artifact_root,
    embedding_definition,
    tokenizer_definition,
    expected_inventory_id,
    runtime,
    launch_inputs,
    reservation,
    store,
    journal_root,
    authorization_provider,
    *,
    purpose="prepare",
    representation_policy=None,
    batch_policy=None,
):
    """Produce one batch or verify a complete batch with current authorization."""
    from . import derived_store, embedding_batch_plan as source, embedding_job_journal as journal
    from . import gpu_embedding_plan as plan, gpu_embedding_worker as parent
    from . import gpu_worker_launch as launch
    from . import isolated_cpu_embedding, isolated_gpu_embedding as bridge
    from . import retrieval_representation

    if type(store) is not derived_store.Store or not callable(authorization_provider):
        raise ProducerRefused()
    handle = prep = capture = session = worker = attempt = None
    entered = dispatch = False
    owner = None
    try:
        if type(chunk_ids) not in (list, tuple) or not 1 <= len(chunk_ids) <= 128:
            raise ValueError
        if isolated_cpu_embedding._path(journal_root) == "/":
            raise ValueError
        policy = (
            retrieval_representation.Policy()
            if representation_policy is None
            else representation_policy
        )
        bp = retrieval_representation.BatchPolicy() if batch_policy is None else batch_policy
        source._preflight(
            original_store,
            bundle_metadata_bytes,
            bundle_members,
            chunk_ids,
            manifest_bytes,
            artifact_root,
            embedding_definition,
            tokenizer_definition,
            expected_inventory_id,
            runtime,
            purpose,
            policy,
            bp,
        )
        snapshot = _launch_snapshot(launch_inputs, reservation)
        source_args = (
            original_store,
            bundle_metadata_bytes,
            bundle_members,
            chunk_ids,
            manifest_bytes,
            artifact_root,
            embedding_definition,
            tokenizer_definition,
            expected_inventory_id,
            runtime,
        )
        kwargs = dict(
            purpose=purpose, representation_policy=representation_policy, batch_policy=batch_policy
        )

        def prepare(actual_capture):
            return _prepare(
                launch_inputs,
                reservation,
                snapshot,
                manifest_bytes,
                artifact_root,
                embedding_definition,
                tokenizer_definition,
                expected_inventory_id,
                actual_capture,
            )

        def rebuild(candidate):
            if _launch_snapshot(launch_inputs, reservation) != snapshot:
                raise ValueError
            return plan.build(*source_args, candidate, **kwargs)

        capture = launch.PreparationOwner()
        prep = prepare(capture)
        planned = rebuild(prep)
        obj = json.loads(planned.plan_bytes)
        epoch = _authorize(authorization_provider, planned.plan_bytes, "before_model")
        handle = journal.Journal(journal_root).own(planned.plan_bytes)
        handle.__enter__()
        entered = True
        envelope, revision = handle.read()
        current = envelope["events"][-1]["state"]
        if current["status"] == "COMPLETE":
            fresh = rebuild(prep)
            if fresh != planned:
                raise ValueError
            metadata = _reuse_metadata(store, current["output"]["ref"], obj)
            verified = handle.verified_output(store, metadata)
            loaded = batch.load(store, verified.ref[7:], metadata)
            _authorize(authorization_provider, fresh.plan_bytes, "before_reuse", epoch)
            prep.close()
            prep = None
            capture.close()
            capture = None
            result = Result(
                planned.spec.job_id,
                verified.ref,
                metadata,
                loaded,
                planned.predicted_record,
                planned.native_runtime_record,
                planned.execution_fingerprint,
                True,
            )
        else:
            if current["status"] != "PENDING":
                raise ValueError
            started = _now(current["updated_ms"])
            attempt = _Attempt(handle, planned, store, revision, started, secrets.token_hex(24))
            attempt.append("CLAIMED", started)
            attempt.append("RUNNING", _now(started))
            worker = parent.GPUEmbeddingWorker.__new__(parent.GPUEmbeddingWorker)
            parent.GPUEmbeddingWorker.__init__(worker, prep)
            session = bridge.GPUTextEmbeddingSession.__new__(bridge.GPUTextEmbeddingSession)
            bridge.GPUTextEmbeddingSession.__init__(session, worker, runtime)
            _observe(session, planned, embedding_definition)
            fresh = rebuild(prep)
            if fresh != planned:
                raise ValueError
            _authorize(authorization_provider, fresh.plan_bytes, "before_encode", epoch)
            dispatch = True
            encoded = bridge.GPUTextEmbeddingSession.encode(session, fresh.texts)
            vector = _validate_encoded(session, planned, obj, embedding_definition, encoded)
            drain = _CleanupOwner(session, worker, None, preparation=prep, capture=capture)
            try:
                drain.close()
            finally:
                session, worker, prep, capture = (
                    drain.session,
                    drain.worker,
                    drain.preparation,
                    drain.capture,
                )
            capture = launch.PreparationOwner()
            prep = prepare(capture)
            fresh = rebuild(prep)
            if fresh != planned:
                raise ValueError
            _authorize(authorization_provider, fresh.plan_bytes, "before_publish", epoch)
            metadata = _metadata(obj, vector)
            identifier = batch.publish(store, metadata, vector.container)
            batch.load(store, identifier, metadata)
            fresh = rebuild(prep)
            if fresh != planned:
                raise ValueError
            _authorize(authorization_provider, fresh.plan_bytes, "before_complete", epoch)
            prep.close()
            prep = None
            capture.close()
            capture = None
            output = _output(metadata, identifier)
            last = handle.read()[0]["events"][-1]["state"]["updated_ms"]
            attempt.append("COMPLETE", _now(last), output, metadata)
            verified = handle.verified_output(store, metadata)
            loaded = batch.load(store, identifier, metadata)
            result = Result(
                planned.spec.job_id,
                verified.ref,
                metadata,
                loaded,
                planned.predicted_record,
                planned.native_runtime_record,
                planned.execution_fingerprint,
                False,
            )
        return result
    except BaseException as error:
        selected = error
        uncertain = []
        nested = _owner_for(error)
        if nested is not None and all(
            nested is not known for known in (prep, capture, worker, session, handle)
        ):
            uncertain.append(nested)
        if not entered and handle is not None:
            if getattr(handle, "pending", False):
                uncertain.append(handle)
            handle = None
        if attempt is not None:
            try:
                attempt.reconcile(dispatch)
            except BaseException as reconciliation:
                selected = _prefer(selected, reconciliation)
                uncertain.append(getattr(reconciliation, "cleanup_owner", reconciliation))
        if worker is not None and id(worker) not in parent._records:
            worker = None  # constructor acquired no registered worker resources
        owner = _CleanupOwner(session, worker, handle, uncertain, preparation=prep, capture=capture)
        try:
            owner.close()
        except BaseException as cleanup:
            selected = _prefer(selected, cleanup)
        if (
            owner.session is None
            and owner.worker is None
            and owner.preparation is None
            and owner.capture is None
            and owner.lease is None
            and not owner.uncertainty
        ):
            owner = None
        handle = None
        if not isinstance(selected, Exception):
            if owner is not None:
                _attach_owner(selected, owner)
            raise selected from None
        refusal = ProducerRefused(owner=owner)
        if owner is not None:
            _attach_owner(refusal, owner)
        raise refusal from None
    finally:
        if handle is not None:
            active = sys.exception()
            try:
                handle.__exit__(None, None, None)
            except BaseException as cleanup:
                owner = _CleanupOwner(None, None, None, [handle])
                if active is not None and not isinstance(active, Exception):
                    _attach_owner(active, owner)
                elif not isinstance(cleanup, Exception):
                    _attach_owner(cleanup, owner)
                    raise cleanup from None
                else:
                    refusal = ProducerRefused(owner=owner)
                    _attach_owner(refusal, owner)
                    raise refusal from None
