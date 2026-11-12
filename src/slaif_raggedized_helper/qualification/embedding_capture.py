"""Bounded observed-path capture; evidence does not establish qualification."""

import hashlib
import math
import re

from slaif_raggedized_helper import query_embedding


class CaptureRefused(ValueError):
    """Content-free refusal of an invalid capture request."""


def _id(value):
    if type(value) is not str or not re.fullmatch(r"[A-Za-z0-9._:-]{1,128}", value):
        raise ValueError
    return value


def _admit(chunk_ids, queries, deadline_ms, k, cosine_tolerance, score_tolerance):
    """Freeze and preflight bounded trial inputs before any producer dispatch."""
    try:
        if type(chunk_ids) not in (tuple, list) or not 1 <= len(chunk_ids) <= 8:
            raise ValueError
        ids = tuple(_id(item) for item in chunk_ids)
        if len(set(ids)) != len(ids):
            raise ValueError
        if type(queries) is not tuple or not 1 <= len(queries) <= 8:
            raise ValueError
        if type(deadline_ms) is not int or not 1 <= deadline_ms <= 180000:
            raise ValueError
        if type(k) is not int or not 1 <= k <= 2048:
            raise ValueError
        for value in (cosine_tolerance, score_tolerance):
            if type(value) not in (int, float) or not math.isfinite(value):
                raise ValueError
        if not 0 <= cosine_tolerance <= 2 or score_tolerance < 0:
            raise ValueError
        result = []
        for item in queries:
            if type(item) is not tuple or len(item) != 3:
                raise ValueError
            ident, text, gold = item
            _id(ident)
            query_embedding._query(text)
            if type(gold) is not tuple or len(gold) > len(ids):
                raise ValueError
            for entry in gold:
                _id(entry)
            if len(set(gold)) != len(gold) or not set(gold) <= set(ids):
                raise ValueError
            result.append((ident, text, gold, hashlib.sha256(text.encode("utf-8")).hexdigest()))
        if len({item[0] for item in result}) != len(result):
            raise ValueError
        return ids, tuple(result)
    except (ValueError, TypeError, UnicodeError, OverflowError):
        raise CaptureRefused("capture refused") from None


def _wire(value):
    import json

    return json.dumps(
        value, sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(",", ":")
    ).encode("utf-8")


class _Epoch:
    """Forward real boundaries while enforcing one epoch and elapsed budget."""

    def __init__(self, provider, deadline_ms):
        import time

        if not callable(provider) or type(deadline_ms) is not int or not 1 <= deadline_ms <= 180000:
            raise CaptureRefused("capture refused")
        self._provider = provider
        self._end = time.monotonic() + deadline_ms / 1000
        self._epoch = None
        self.guard = None

    def check(self):
        import time

        if time.monotonic() >= self._end:
            raise CaptureRefused("capture refused")

    def __call__(self, plan_bytes, boundary):
        self.check()
        try:
            epoch = self._provider(plan_bytes, boundary)
        except Exception:
            raise CaptureRefused("capture refused") from None
        self.check()
        if self.guard is not None:
            self.guard()
        if type(epoch) is not str or re.fullmatch(r"[0-9a-f]{64}", epoch) is None:
            raise CaptureRefused("capture refused")
        if self._epoch is None:
            self._epoch = epoch
        elif epoch != self._epoch:
            raise CaptureRefused("capture refused")
        return epoch


def _compare_plans(cpu, gpu):
    """Compare independently built source bindings, excluding execution identity."""
    import json

    try:
        left, right = json.loads(cpu.plan_bytes), json.loads(gpu.plan_bytes)
        if left["rows"] != right["rows"] or cpu.texts != gpu.texts:
            raise ValueError
        left_deps, right_deps = dict(left["dependencies"]), dict(right["dependencies"])
        del left_deps["execution_fingerprint"]
        del right_deps["execution_fingerprint"]
        if left_deps != right_deps:
            raise ValueError
        left["dependencies"], right["dependencies"] = left_deps, right_deps
        if left != right:
            raise ValueError
        return left
    except (AttributeError, KeyError, TypeError, ValueError):
        raise CaptureRefused("capture refused") from None


def _load_result(store, result, planned, *, gpu):
    """Reload a producer output against the independently prepared declaration."""
    import json

    from slaif_raggedized_helper import (
        cpu_embedding_producer,
        cpu_execution_contract,
        embedding_batch_store,
        gpu_embedding_producer,
        isolated_gpu_embedding,
        schema,
    )

    try:
        expected_type = gpu_embedding_producer.Result if gpu else cpu_embedding_producer.Result
        if type(result) is not expected_type or type(result.reused) is not bool:
            raise ValueError
        if (
            type(result.output_ref) is not str
            or re.fullmatch(r"sha256:[0-9a-f]{64}", result.output_ref) is None
            or result.job_id != planned.spec.job_id
            or result.execution_record != planned.predicted_record
            or result.execution_fingerprint != planned.execution_fingerprint
        ):
            raise ValueError
        if gpu:
            if (
                result.native_runtime_record != planned.native_runtime_record
                or isolated_gpu_embedding.validate_record(
                    result.execution_record, result.native_runtime_record
                )
                != isolated_gpu_embedding._digest(result.execution_record)
                or hashlib.sha256(result.execution_record).hexdigest()
                != result.execution_fingerprint
            ):
                raise ValueError
        else:
            record = cpu_execution_contract._validate(result.execution_record)
            if schema.fingerprint({"kind": "isolated-cpu-embedding-execution-v2", **record}) != (
                result.execution_fingerprint
            ):
                raise ValueError
        metadata = embedding_batch_store._metadata(result.metadata)
        plan = json.loads(planned.plan_bytes)
        if any(
            metadata[key] != plan[key]
            for key in ("dependencies", "rows", "codec_policy_fingerprint")
        ):
            raise ValueError
        loaded = embedding_batch_store.load(store, result.output_ref[7:], result.metadata)
        return loaded, metadata
    except Exception:
        raise CaptureRefused("capture refused") from None


def _query_result(value, definition, space, expected_execution):
    """Validate an actual returned query embedding without retaining its payload in evidence."""
    import struct

    from slaif_raggedized_helper import cpu_execution_contract, schema

    try:
        if type(value) is not query_embedding.QueryEmbedding:
            raise ValueError
        if (
            type(value.payload) is not bytes
            or len(value.payload) != 4096
            or hashlib.sha256(value.payload).hexdigest() != value.payload_sha256
            or value.space_id != space
            or value.definition_fingerprint != definition.fingerprint()
            or value.query_policy_id != query_embedding.POLICY_ID
            or value.intended_execution_fingerprint != expected_execution
        ):
            raise ValueError
        vector = struct.unpack("<1024f", value.payload)
        if any(not math.isfinite(item) for item in vector) or abs(math.hypot(*vector) - 1) > 0.0001:
            raise ValueError
        record = cpu_execution_contract._validate(value.execution_record)
        if (
            record["space"] != space
            or record["definition"] != definition.fingerprint()
            or value.execution_fingerprint
            != schema.fingerprint({"kind": "isolated-cpu-embedding-execution-v2", **record})
        ):
            raise ValueError
        return vector
    except Exception:
        raise CaptureRefused("capture refused") from None


def _query_identity(bundle_id, chunk_ids, query):
    """Build the content-free identity sent to the authorization provider."""
    return _wire(
        {
            "purpose": "evaluate",
            "bundle_id": bundle_id,
            "chunk_ids": list(chunk_ids),
            "query_id": query[0],
            "query_sha256": query[3],
        }
    )


def _source_snapshot(originals, derived, bundle_id, epoch):
    """Freshly load and bind the actual original-backed ingestion bundle."""
    from slaif_raggedized_helper import ingestion_store

    epoch.check()
    try:
        bundle = ingestion_store.load(originals, derived, bundle_id)
        epoch.check()
        if type(bundle.metadata_json) is not bytes or type(bundle.members) is not tuple:
            raise ValueError
        # Keep the complete immutable source bytes for later equality checks. They are
        # never included in capture evidence or exception messages.
        snapshot = (bundle.metadata_json, bundle.members)
        return snapshot
    except Exception:
        raise CaptureRefused("capture refused") from None


def _unchanged_source(originals, derived, bundle_id, snapshot, epoch):
    if _source_snapshot(originals, derived, bundle_id, epoch) != snapshot:
        raise CaptureRefused("capture refused")


def _journal_identity(path):
    """Admit an existing private root and return stable directory identity."""
    import os
    import stat

    try:
        value = os.lstat(path)
        if (
            not stat.S_ISDIR(value.st_mode)
            or value.st_uid != os.geteuid()
            or stat.S_IMODE(value.st_mode) != 0o700
        ):
            raise ValueError
        return (
            value.st_dev,
            value.st_ino,
            value.st_uid,
            stat.S_IMODE(value.st_mode),
            stat.S_IFMT(value.st_mode),
        )
    except Exception:
        raise CaptureRefused("capture refused") from None


def _journal_paths(cpu_root, gpu_root):
    """Require distinct canonical private journal paths before any model work."""
    import os

    from slaif_raggedized_helper import isolated_cpu_embedding

    try:
        cpu = isolated_cpu_embedding._path(cpu_root)
        gpu = isolated_cpu_embedding._path(gpu_root)
        if cpu == "/" or gpu == "/" or cpu == gpu:
            raise ValueError
        # Resolve existing ancestors as well as the eventual leaf to catch aliases.
        if os.path.realpath(cpu) != cpu or os.path.realpath(gpu) != gpu:
            raise ValueError
        if os.path.commonpath((cpu, gpu)) in (cpu, gpu):
            raise ValueError
        _journal_identity(cpu)
        _journal_identity(gpu)
        return cpu, gpu
    except Exception:
        raise CaptureRefused("capture refused") from None


def _build_plans(
    source_args,
    cpu_runtime,
    launch_inputs,
    reservation,
    epoch,
    *,
    representation_policy,
    batch_policy,
    cpu_worker_policy,
):
    """Build independent real plans and drain only the launch resources acquired here."""
    from slaif_raggedized_helper import (
        cpu_embedding_plan,
        gpu_embedding_plan,
        gpu_embedding_producer,
        gpu_worker_launch,
    )

    kwargs = dict(
        purpose="evaluate", representation_policy=representation_policy, batch_policy=batch_policy
    )
    epoch.check()
    cpu = cpu_embedding_plan.build(
        *source_args, cpu_runtime, worker_policy=cpu_worker_policy, **kwargs
    )
    epoch.check()
    launch_snapshot = gpu_embedding_producer._launch_snapshot(launch_inputs, reservation)
    capture = gpu_worker_launch.PreparationOwner()
    prepared = None
    selected = None
    try:
        prepared = gpu_embedding_producer._prepare(
            launch_inputs,
            reservation,
            launch_snapshot,
            source_args[4],
            source_args[5],
            source_args[6],
            source_args[7],
            source_args[8],
            capture,
        )
        epoch.check()
        gpu = gpu_embedding_plan.build(*source_args, prepared, **kwargs)
        epoch.check()
        _compare_plans(cpu, gpu)
    except BaseException as error:
        selected = error
    owner = gpu_embedding_producer._CleanupOwner(
        None, None, None, preparation=prepared, capture=capture
    )
    if selected is not None:
        nested = gpu_embedding_producer._owner_for(selected)
        if nested is not None and nested is not prepared and nested is not capture:
            owner.uncertainty.append(nested)
    try:
        owner.close()
    except BaseException as error:
        selected = gpu_embedding_producer._prefer(selected, error)
    pending = owner.preparation is not None or owner.capture is not None or owner.uncertainty
    if selected is not None or pending:
        if selected is not None and not isinstance(selected, Exception):
            if pending:
                gpu_embedding_producer._attach_owner(selected, owner)
            raise selected from None
        refusal = gpu_embedding_producer.ProducerRefused(owner=owner if pending else None)
        if pending:
            gpu_embedding_producer._attach_owner(refusal, owner)
        raise refusal from None
    return cpu, gpu, launch_snapshot


def _produce_pair(
    source_args,
    cpu_runtime,
    launch_inputs,
    reservation,
    derived,
    cpu_journal,
    gpu_journal,
    epoch,
    cpu_plan,
    gpu_plan,
    recheck,
    *,
    representation_policy,
    batch_policy,
    cpu_worker_policy,
):
    """Invoke each actual producer once and reload each result from its store."""
    from slaif_raggedized_helper import cpu_embedding_producer, gpu_embedding_producer

    kwargs = dict(
        purpose="evaluate", representation_policy=representation_policy, batch_policy=batch_policy
    )
    recheck()
    cpu = cpu_embedding_producer.produce(
        *source_args,
        cpu_runtime,
        derived,
        cpu_journal,
        epoch,
        worker_policy=cpu_worker_policy,
        **kwargs,
    )
    epoch.check()
    recheck()
    cpu_batch, cpu_metadata = _load_result(derived, cpu, cpu_plan, gpu=False)
    epoch.check()
    recheck()
    gpu = gpu_embedding_producer.produce(
        *source_args, launch_inputs, reservation, derived, gpu_journal, epoch, **kwargs
    )
    epoch.check()
    recheck()
    gpu_batch, gpu_metadata = _load_result(derived, gpu, gpu_plan, gpu=True)
    epoch.check()
    recheck()
    return cpu, cpu_batch, cpu_metadata, gpu, gpu_batch, gpu_metadata


def _analyze(
    definition, queries, vectors, rows, cpu_batch, gpu_batch, k, cosine_tolerance, score_tolerance
):
    """Analyze only vectors returned by the verified stores and actual query encoder."""
    from slaif_raggedized_helper import schema
    from slaif_raggedized_helper.qualification import embedding_parity

    if len(queries) != len(vectors):
        raise CaptureRefused("capture refused")
    query_rows = [
        {
            "id": query[0],
            "input_digest": query[3],
            "representation_digest": query_embedding.POLICY_ID,
            "vector": list(vector),
            "relevant_ids": list(query[2]),
        }
        for query, vector in zip(queries, vectors, strict=True)
    ]

    def corpus(batch):
        matrix = batch.matrix.tolist()
        if len(matrix) != len(rows):
            raise CaptureRefused("capture refused")
        return [
            {
                "id": row["chunk_id"],
                "input_digest": row["input_sha256"],
                "representation_digest": row["representation_id"],
                "vector": vector,
            }
            for row, vector in zip(rows, matrix, strict=True)
        ]

    return embedding_parity.analyze(
        {
            "version": 1,
            "reference": schema.EmbeddingExecution(
                definition=definition, device="cpu", dtype="fp32"
            ),
            "candidate": schema.EmbeddingExecution(
                definition=definition, device="gpu", dtype="fp16"
            ),
            "queries": query_rows,
            "reference_corpus": corpus(cpu_batch),
            "candidate_corpus": corpus(gpu_batch),
            "k": k,
            "cosine_tolerance": cosine_tolerance,
            "score_tolerance": score_tolerance,
        }
    )


def _configuration(
    manifest,
    artifact_root,
    definition,
    tokenizer,
    inventory,
    tokenizer_runtime,
    cpu_runtime,
    launch_inputs,
    reservation,
    representation_policy,
    batch_policy,
    cpu_worker_policy,
    encoder,
):
    """Read immutable configuration values and verify the borrowed query owner."""
    from dataclasses import asdict

    from slaif_raggedized_helper import (
        cpu_embedding_worker,
        gpu_embedding_producer,
        isolated_cpu_embedding,
        retrieval_representation,
    )

    try:
        if (
            type(manifest) is not bytes
            or type(inventory) is not str
            or type(encoder) is not query_embedding.ResidentQueryEncoder
            or encoder._state != "open"
        ):
            raise ValueError
        session = encoder._session
        if type(session) is not isolated_cpu_embedding.IsolatedCPUEmbeddingSession:
            raise ValueError
        query_embedding.ResidentQueryEncoder._check(encoder)
        if (
            session._state != "open"
            or session._args[0] != manifest
            or isolated_cpu_embedding._path(session._args[1])
            != isolated_cpu_embedding._path(artifact_root)
            or isolated_cpu_embedding._definition_values(session.definition)
            != isolated_cpu_embedding._definition_values(definition)
            or isolated_cpu_embedding._token_values(
                session._args[3], definition.checkpoint_revision
            )
            != isolated_cpu_embedding._token_values(tokenizer, definition.checkpoint_revision)
            or session._args[4] != inventory
        ):
            raise ValueError
        policy = cpu_embedding_worker.Policy() if cpu_worker_policy is None else cpu_worker_policy
        rp = (
            retrieval_representation.Policy()
            if representation_policy is None
            else representation_policy
        )
        bp = retrieval_representation.BatchPolicy() if batch_policy is None else batch_policy
        return (
            manifest,
            isolated_cpu_embedding._path(artifact_root),
            isolated_cpu_embedding._definition_values(definition),
            isolated_cpu_embedding._token_values(tokenizer, definition.checkpoint_revision),
            inventory,
            isolated_cpu_embedding._runtime_values(tokenizer_runtime),
            isolated_cpu_embedding._runtime_values(cpu_runtime),
            gpu_embedding_producer._launch_snapshot(launch_inputs, reservation),
            _wire(asdict(rp)),
            _wire(asdict(bp)),
            isolated_cpu_embedding._cpu_values(policy),
            encoder,
            session,
            session.execution_record,
            session.execution_fingerprint,
        )
    except Exception:
        raise CaptureRefused("capture refused") from None


def _encode_queries(
    encoder, queries, bundle_id, chunk_ids, definition, space, intended_execution, epoch, recheck
):
    """Authorize and call the actual borrowed encoder for each admitted query."""
    vectors, observations = [], []
    execution = None
    for query in queries:
        recheck()
        identity = _query_identity(bundle_id, chunk_ids, query)
        epoch(identity, "before_query")
        result = query_embedding.ResidentQueryEncoder.encode_query(encoder, query[1])
        epoch.check()
        recheck()
        vector = _query_result(result, definition, space, intended_execution)
        current = (
            result.execution_record,
            result.execution_fingerprint,
            result.intended_execution_fingerprint,
        )
        if execution is None:
            execution = current
        elif execution != current:
            raise CaptureRefused("capture refused")
        epoch(identity, "after_query")
        recheck()
        vectors.append(vector)
        observations.append(
            {
                "query_id": query[0],
                "query_sha256": query[3],
                "relevant_ids": list(query[2]),
                "payload_sha256": result.payload_sha256,
            }
        )
    return tuple(vectors), observations, execution


from dataclasses import dataclass  # noqa: E402


@dataclass(frozen=True)
class Capture:
    capture_bytes: bytes
    capture_sha256: str
    analyzer_result: dict


def capture(
    originals,
    derived,
    bundle_id,
    chunk_ids,
    manifest_bytes,
    artifact_root,
    embedding_definition,
    tokenizer_definition,
    expected_inventory_id,
    tokenizer_runtime,
    cpu_runtime,
    launch_inputs,
    reservation,
    cpu_journal_root,
    gpu_journal_root,
    query_encoder,
    queries,
    authorization_provider,
    *,
    deadline_ms,
    k,
    cosine_tolerance,
    score_tolerance,
    representation_policy=None,
    batch_policy=None,
    cpu_worker_policy=None,
):
    """Capture unqualified evidence from actual local producer and query paths."""
    import json

    from slaif_raggedized_helper import schema

    epoch = _Epoch(authorization_provider, deadline_ms)
    ids, admitted_queries = _admit(
        chunk_ids, queries, deadline_ms, k, cosine_tolerance, score_tolerance
    )
    epoch.check()
    cpu_journal, gpu_journal = _journal_paths(cpu_journal_root, gpu_journal_root)
    journal_identity = (_journal_identity(cpu_journal), _journal_identity(gpu_journal))
    if (
        type(embedding_definition) is not schema.EmbeddingDefinition
        or embedding_definition.dimensions != 1024
    ):
        raise CaptureRefused("capture refused")
    config_args = (
        manifest_bytes,
        artifact_root,
        embedding_definition,
        tokenizer_definition,
        expected_inventory_id,
        tokenizer_runtime,
        cpu_runtime,
        launch_inputs,
        reservation,
        representation_policy,
        batch_policy,
        cpu_worker_policy,
        query_encoder,
    )
    config = _configuration(*config_args)
    snapshot = _source_snapshot(originals, derived, bundle_id, epoch)
    source_args = (
        originals,
        snapshot[0],
        snapshot[1],
        ids,
        manifest_bytes,
        artifact_root,
        embedding_definition,
        tokenizer_definition,
        expected_inventory_id,
        tokenizer_runtime,
    )

    def recheck():
        epoch.check()
        if (
            _journal_paths(cpu_journal, gpu_journal) != (cpu_journal, gpu_journal)
            or (_journal_identity(cpu_journal), _journal_identity(gpu_journal)) != journal_identity
        ):
            raise CaptureRefused("capture refused")
        if _configuration(*config_args) != config:
            raise CaptureRefused("capture refused")
        if _admit(chunk_ids, queries, deadline_ms, k, cosine_tolerance, score_tolerance) != (
            ids,
            admitted_queries,
        ):
            raise CaptureRefused("capture refused")
        _unchanged_source(originals, derived, bundle_id, snapshot, epoch)
        epoch.check()

    recheck()
    epoch.guard = recheck
    cpu_plan, gpu_plan, _ = _build_plans(
        source_args,
        cpu_runtime,
        launch_inputs,
        reservation,
        epoch,
        representation_policy=representation_policy,
        batch_policy=batch_policy,
        cpu_worker_policy=cpu_worker_policy,
    )
    recheck()
    cpu, cpu_batch, cpu_meta, gpu, gpu_batch, gpu_meta = _produce_pair(
        source_args,
        cpu_runtime,
        launch_inputs,
        reservation,
        derived,
        cpu_journal,
        gpu_journal,
        epoch,
        cpu_plan,
        gpu_plan,
        recheck,
        representation_policy=representation_policy,
        batch_policy=batch_policy,
        cpu_worker_policy=cpu_worker_policy,
    )
    if cpu_meta["rows"] != gpu_meta["rows"]:
        raise CaptureRefused("capture refused")
    space = cpu_meta["dependencies"]["space_id"]
    intended = schema.EmbeddingExecution(
        definition=embedding_definition, device="cpu", dtype="fp32"
    ).fingerprint()
    vectors, observed_queries, query_execution = _encode_queries(
        query_encoder,
        admitted_queries,
        bundle_id,
        ids,
        embedding_definition,
        space,
        intended,
        epoch,
        recheck,
    )
    result = _analyze(
        embedding_definition,
        admitted_queries,
        vectors,
        cpu_meta["rows"],
        cpu_batch,
        gpu_batch,
        k,
        cosine_tolerance,
        score_tolerance,
    )
    recheck()

    def producer_evidence(producer, metadata):
        return {
            "job_id": producer.job_id,
            "output_ref": producer.output_ref,
            "reused": producer.reused,
            "metadata": metadata,
            "metadata_sha256": hashlib.sha256(producer.metadata).hexdigest(),
            "execution_record": json.loads(producer.execution_record),
            "execution_fingerprint": producer.execution_fingerprint,
        }

    cpu_evidence = producer_evidence(cpu, cpu_meta)
    gpu_evidence = producer_evidence(gpu, gpu_meta)
    gpu_evidence["native_runtime_record"] = json.loads(gpu.native_runtime_record)
    evidence = {
        "version": 1,
        "origin": "OBSERVED_LOCAL_SOFTWARE_PATHS_UNQUALIFIED",
        "qualification": "NOT_QUALIFIED",
        "purpose": "evaluate",
        "bundle_id": bundle_id,
        "chunk_ids": list(ids),
        "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "definition": embedding_definition.model_dump(mode="json"),
        "space_id": space,
        "cpu": cpu_evidence,
        "gpu": gpu_evidence,
        "queries": observed_queries,
        "query_execution_record": json.loads(query_execution[0]),
        "query_execution_fingerprint": query_execution[1],
        "query_intended_execution_fingerprint": query_execution[2],
        "k": k,
        "cosine_tolerance": cosine_tolerance,
        "score_tolerance": score_tolerance,
        "analyzer_result": result,
    }
    data = _wire(evidence)
    if len(data) > 1048576:
        raise CaptureRefused("capture refused")
    recheck()
    epoch(
        _wire(
            {
                "purpose": "evaluate",
                "bundle_id": bundle_id,
                "chunk_ids": list(ids),
                "capture_sha256": hashlib.sha256(data).hexdigest(),
            }
        ),
        "before_return",
    )
    recheck()
    return Capture(data, hashlib.sha256(data).hexdigest(), result)
