"""One-attempt CPU reference composition with explicit current authorization."""

from dataclasses import dataclass
import hashlib
import json
import re
import secrets
import sys
import time

import numpy as np

from . import cpu_embedding_plan as plan
from . import derived_store, embedding_batch_store as batch, embedding_job_journal as journal
from . import embedding_tokenizer, embedding_vectors, isolated_cpu_embedding as isolated
from . import vector_codec


class ProducerRefused(ValueError):
    """Content-free refusal; owner retains resources when cleanup is pending."""

    def __init__(self, *, owner=None):
        super().__init__("CPU producer refused")
        self.owner = owner
        self.pending = owner is not None


@dataclass(frozen=True)
class Result:
    job_id: str
    output_ref: str
    metadata: bytes
    batch: batch.ValidatedBatch
    execution_record: bytes
    execution_fingerprint: str
    reused: bool


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


def _metadata(p, encoded):
    return _wire(
        {
            "schema": 1,
            "kind": "embedding-batch-v1",
            "dependencies": p["dependencies"],
            "rows": p["rows"],
            "codec_policy_fingerprint": p["codec_policy_fingerprint"],
            "vector_container_sha256": encoded.container_sha256,
            "vector_payload_sha256": encoded.payload_sha256,
        }
    )


def _reuse_metadata(store, ref, p):
    snapshot = store.load(ref[7:])
    manifest = json.loads(snapshot.manifest)
    data = _wire(manifest["metadata"])
    obj = batch._metadata(data)
    if any(obj[k] != p[k] for k in ("dependencies", "rows", "codec_policy_fingerprint")):
        raise ValueError
    return data


class _CleanupOwner:
    def __init__(self, session, lease):
        self.session, self.lease = session, lease

    def close(self):
        if self.session is not None:
            self.session.close()
            self.session = None
        if self.lease is not None:
            self.lease.__exit__(None, None, None)
            self.lease = None


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
    cpu_runtime,
    store,
    journal_root,
    authorization_provider,
    *,
    purpose="prepare",
    representation_policy=None,
    batch_policy=None,
    worker_policy=None,
):
    """Produce or freshly verify one immutable batch under an owned journal lease."""
    if type(store) is not derived_store.Store or not callable(authorization_provider):
        raise ProducerRefused()
    kwargs = dict(
        purpose=purpose,
        representation_policy=representation_policy,
        batch_policy=batch_policy,
        worker_policy=worker_policy,
    )
    args = (
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
        cpu_runtime,
    )
    handle = None
    session = None
    entered = False
    dispatch = False
    started = None
    attempt_id = None
    try:
        if type(chunk_ids) not in (list, tuple) or not 1 <= len(chunk_ids) <= 128:
            raise ValueError
        if isolated._path(journal_root) == "/":
            raise ValueError
        prepared = plan.build(*args, **kwargs)
        p = json.loads(prepared.plan_bytes)
        epoch = _authorize(authorization_provider, prepared.plan_bytes, "before_model")
        handle = journal.Journal(journal_root).own(prepared.plan_bytes)
        handle.__enter__()
        envelope, revision = handle.read()
        current = envelope["events"][-1]["state"]
        if current["status"] == "COMPLETE":
            fresh = plan.build(*args, **kwargs)
            if fresh != prepared:
                raise ValueError
            output = current["output"]
            metadata = _reuse_metadata(store, output["ref"], p)
            verified = handle.verified_output(store, metadata)
            loaded = batch.load(store, output["ref"][7:], metadata)
            _authorize(authorization_provider, fresh.plan_bytes, "before_reuse", epoch)
            return Result(
                prepared.spec.job_id,
                verified.ref,
                metadata,
                loaded,
                prepared.predicted_record,
                prepared.execution_fingerprint,
                True,
            )
        if current["status"] != "PENDING":
            raise ValueError
        attempt_id = secrets.token_hex(24)
        started = _now(current["updated_ms"])

        def append(status, timestamp, output=None):
            nonlocal revision
            state = dict(
                version=1,
                job_id=prepared.spec.job_id,
                status=status,
                attempt_id=attempt_id,
                owner_id=handle.owner_id if status in ("CLAIMED", "RUNNING") else None,
                updated_ms=timestamp,
                output=output,
            )
            attempt = None
            if status not in ("CLAIMED", "RUNNING"):
                attempt = _wire(
                    dict(
                        version=1,
                        job_id=prepared.spec.job_id,
                        attempt_id=attempt_id,
                        request_id=None,
                        outcome=status,
                        started_ms=started,
                        ended_ms=timestamp,
                        input_tokens=None,
                        output_tokens=None,
                        diagnostic_code=None,
                        output=output,
                    )
                )
            _, revision = handle.append(
                _wire(state),
                attempt,
                revision,
                **({"store": store, "metadata_bytes": metadata} if status == "COMPLETE" else {}),
            )

        append("CLAIMED", started)
        append("RUNNING", _now(started))
        session = isolated.IsolatedCPUEmbeddingSession(
            manifest_bytes,
            artifact_root,
            embedding_definition,
            tokenizer_definition,
            expected_inventory_id,
            runtime,
            cpu_runtime,
            worker_policy=worker_policy,
        )
        session.__enter__()
        entered = True
        if (
            session.execution_record != prepared.predicted_record
            or session.execution_fingerprint != prepared.execution_fingerprint
        ):
            raise ValueError
        fresh = plan.build(*args, **kwargs)
        if fresh != prepared:
            raise ValueError
        _authorize(authorization_provider, fresh.plan_bytes, "before_encode", epoch)
        dispatch = True
        encoded = session.encode(fresh.texts)
        if (
            type(encoded) is not isolated.EncodedBatch
            or encoded.execution_record != prepared.predicted_record
            or encoded.execution_fingerprint != prepared.execution_fingerprint
            or session.execution_record != prepared.predicted_record
            or session.execution_fingerprint != prepared.execution_fingerprint
            or encoded.intended_execution_fingerprint != prepared.intended_execution_fingerprint
            or encoded.space_id != p["dependencies"]["space_id"]
            or encoded.definition_fingerprint != embedding_definition.fingerprint()
            or type(encoded.receipts) is not tuple
            or len(encoded.receipts) != len(p["rows"])
            or type(encoded.vectors) is not embedding_vectors.NormalizedVectors
            or encoded.vectors.policy_id != embedding_vectors.POLICY_ID
        ):
            raise ValueError
        for receipt, row, text in zip(encoded.receipts, p["rows"], fresh.texts, strict=True):
            if (
                type(receipt) is not embedding_tokenizer.TokenIDReceipt
                or receipt.input_sha256 != row["input_sha256"]
                or receipt.count != row["token_count"]
            ):
                raise ValueError
            session._receipt(receipt, text)
        if (
            type(encoded.vectors.rows) is not tuple
            or len(encoded.vectors.rows) != len(p["rows"])
            or any(
                type(row) is not tuple
                or len(row) != 1024
                or any(type(value) is not float for value in row)
                for row in encoded.vectors.rows
            )
            or type(encoded.vectors.payload) is not bytes
            or len(encoded.vectors.payload) != len(p["rows"]) * 4096
            or len({receipt.nonce for receipt in encoded.receipts}) != len(encoded.receipts)
            or hashlib.sha256(encoded.vectors.payload).hexdigest() != encoded.vectors.sha256
        ):
            raise ValueError
        matrix = np.asarray(encoded.vectors.rows, dtype="<f4", order="C")
        if matrix.tobytes() != encoded.vectors.payload:
            raise ValueError
        vector = vector_codec.encode(matrix, batch.POLICY)
        session.close()
        session = None
        entered = False
        fresh = plan.build(*args, **kwargs)
        if fresh != prepared:
            raise ValueError
        _authorize(authorization_provider, fresh.plan_bytes, "before_publish", epoch)
        metadata = _metadata(p, vector)
        identifier = batch.publish(store, metadata, vector.container)
        batch.load(store, identifier, metadata)
        fresh = plan.build(*args, **kwargs)
        if fresh != prepared:
            raise ValueError
        _authorize(authorization_provider, fresh.plan_bytes, "before_complete", epoch)
        output = dict(
            ref="sha256:" + identifier,
            fingerprint="sha256:" + hashlib.sha256(metadata).hexdigest(),
            availability="verified",
        )
        previous = handle.read()[0]["events"][-1]["state"]["updated_ms"]
        append("COMPLETE", _now(previous), output)
        verified = handle.verified_output(store, metadata)
        loaded = batch.load(store, identifier, metadata)
        return Result(
            prepared.spec.job_id,
            verified.ref,
            metadata,
            loaded,
            prepared.predicted_record,
            prepared.execution_fingerprint,
            False,
        )
    except BaseException as error:
        uncertain = False
        if handle is not None and started is not None:
            try:
                envelope, revision = handle.read()
                state = envelope["events"][-1]["state"]
                if state["status"] in ("CLAIMED", "RUNNING"):
                    status = (
                        "CANCELLED"
                        if state["status"] == "CLAIMED"
                        else "UNKNOWN_COMPLETION"
                        if dispatch
                        else "FAILED"
                    )
                    append(status, _now(state["updated_ms"]))
            except BaseException:
                uncertain = True
                error.add_note("journal outcome uncertain")
        pending = getattr(error, "cleanup_owner", None) or getattr(error, "owner", None)
        if session is not None and entered and pending is None:
            try:
                session.close()
                session = None
            except BaseException:
                pending = session
        if pending is not None:
            owner = _CleanupOwner(pending, handle)
            handle = None
            if not isinstance(error, Exception):
                error.cleanup_owner = owner
                raise
            refusal = ProducerRefused(owner=owner)
            if uncertain:
                refusal.add_note("journal outcome uncertain")
            raise refusal from None
        if not isinstance(error, Exception):
            raise
        refusal = ProducerRefused()
        if uncertain:
            refusal.add_note("journal outcome uncertain")
        raise refusal from None
    finally:
        if handle is not None:
            active_error = sys.exception()
            try:
                handle.__exit__(None, None, None)
            except BaseException as cleanup_error:
                owner = _CleanupOwner(None, handle)
                if active_error is None:
                    if not isinstance(cleanup_error, Exception):
                        cleanup_error.cleanup_owner = owner
                        raise
                    raise ProducerRefused(owner=owner) from None
                active_error.add_note("journal cleanup pending")
                active_error.cleanup_owner = owner
                if isinstance(active_error, ProducerRefused):
                    active_error.owner = owner
                    active_error.pending = True
