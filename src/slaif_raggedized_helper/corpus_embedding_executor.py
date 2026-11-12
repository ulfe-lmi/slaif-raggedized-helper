"""Complete execution of a freshly validated selected-source program."""

from dataclasses import asdict, dataclass
import hashlib
import json
import re
import time

from . import corpus_embedding_program as program
from . import derived_store, embedding_batch_plan
from . import gpu_embedding_producer as producer
from . import ingestion_store, native_tokenizers, retrieval_representation as rr, schema
from .source_admission import OriginalStore


class ExecutorRefused(ValueError):
    """Content-free refusal of an incomplete corpus operation."""


@dataclass(frozen=True)
class BatchCompletion:
    batch_index: int
    job_id: str
    output_ref: str
    metadata_sha256: str
    reused: bool


@dataclass(frozen=True)
class CorpusResult:
    source_program_id: str
    row_count: int
    completions: tuple[BatchCompletion, ...]
    execution_record: bytes
    native_runtime_record: bytes
    execution_fingerprint: str


class _Epoch:
    def __init__(self, provider):
        self.provider = provider
        self.value = None

    def __call__(self, plan, boundary):
        current = self.provider(plan, boundary)
        if type(current) is not str or re.fullmatch("[0-9a-f]{64}", current) is None:
            raise ExecutorRefused("corpus execution refused")
        if self.value is not None and current != self.value:
            raise ExecutorRefused("corpus execution refused")
        self.value = current
        return current


def _snapshot(definition, token, runtime, inputs, reservation):
    if (
        type(definition) is not schema.EmbeddingDefinition
        or type(token) is not native_tokenizers.Definition
        or type(runtime) is not native_tokenizers.Runtime
    ):
        raise ExecutorRefused("corpus execution refused")
    return (
        definition.model_dump_json(),
        asdict(token),
        asdict(runtime),
        producer._launch_snapshot(inputs, reservation),
    )


def _check(end):
    if time.monotonic() >= end:
        raise ExecutorRefused("corpus execution refused")


def _source_matches(value, source):
    chunks = sorted(value.chunks, key=lambda chunk: chunk.chunk_id)
    scope = schema.fingerprint(
        {"kind": "embedding-source-scope-v1", "scope": value.scope.model_dump(mode="json")}
    )[7:]
    return (
        hashlib.sha256(value.metadata_json).hexdigest() == source["bundle_metadata_sha256"]
        and value.revision.revision_id == source["revision_id"]
        and len(chunks) == source["row_count"]
        and all(c.extraction_id == source["extraction_id"] for c in chunks)
        and scope == source["source_scope_sha256"]
    )


def run(
    originals,
    derived,
    program_bytes,
    manifest_bytes,
    artifact_root,
    embedding_definition,
    tokenizer_definition,
    expected_inventory_id,
    runtime,
    launch_inputs,
    reservation,
    journal_root,
    authorization_provider,
    *,
    deadline_ms,
    purpose="prepare",
):
    """Execute all batches or raise; all stores and the reservation remain borrowed.

    Permission must already be established before calling. The trusted provider is
    invoked at every producer boundary and must return one operation-wide epoch.
    Deadline checks are cooperative and do not preempt native I/O or workers.
    """
    if (
        type(program_bytes) is not bytes
        or not 1 <= len(program_bytes) <= 16777216
        or type(manifest_bytes) is not bytes
        or not 1 <= len(manifest_bytes) <= 262144
        or type(deadline_ms) is not int
        or not 1 <= deadline_ms <= 86400000
        or type(purpose) is not str
        or purpose not in ("prepare", "evaluate")
        or not callable(authorization_provider)
        or type(originals) is not OriginalStore
        or type(derived) is not derived_store.Store
        or type(expected_inventory_id) is not str
        or re.fullmatch("[0-9a-f]{64}", expected_inventory_id) is None
    ):
        raise ExecutorRefused("corpus execution refused")
    try:
        embedding_batch_plan._path(artifact_root)
        embedding_batch_plan._path(journal_root)
    except (TypeError, ValueError):
        raise ExecutorRefused("corpus execution refused") from None
    end = time.monotonic() + deadline_ms / 1000
    snapshot = _snapshot(
        embedding_definition, tokenizer_definition, runtime, launch_inputs, reservation
    )
    _check(end)
    validated = program.validate(originals, derived, program_bytes)
    _check(end)
    _, doc = program._parse(program_bytes)
    policy = rr.Policy(**doc["representation_policy"])
    batch_policy = rr.BatchPolicy(**doc["batch_policy"])
    if any(
        len(batch.chunk_ids) > launch_inputs.wire_policy.max_rows for batch in validated.batches
    ):
        raise ExecutorRefused("corpus execution refused")
    authorize = _Epoch(authorization_provider)

    completions = []
    used = 2
    common = None
    dependencies = None
    for selection, batch_doc in zip(validated.batches, doc["batches"], strict=True):
        _check(end)
        if (
            _snapshot(
                embedding_definition, tokenizer_definition, runtime, launch_inputs, reservation
            )
            != snapshot
        ):
            raise ExecutorRefused("corpus execution refused")
        source = doc["sources"][batch_doc["source_index"]]
        value = ingestion_store.load(originals, derived, selection.bundle_id)
        _check(end)
        source_rows = doc["rows"][
            source["first_ordinal"] : source["first_ordinal"] + source["row_count"]
        ]
        if not _source_matches(value, source) or [
            c.chunk_id for c in sorted(value.chunks, key=lambda c: c.chunk_id)
        ] != [row["chunk_id"] for row in source_rows]:
            raise ExecutorRefused("corpus execution refused")
        if (
            _snapshot(
                embedding_definition, tokenizer_definition, runtime, launch_inputs, reservation
            )
            != snapshot
        ):
            raise ExecutorRefused("corpus execution refused")
        _check(end)
        result = producer.produce(
            originals,
            value.metadata_json,
            value.members,
            selection.chunk_ids,
            manifest_bytes,
            artifact_root,
            embedding_definition,
            tokenizer_definition,
            expected_inventory_id,
            runtime,
            launch_inputs,
            reservation,
            derived,
            journal_root,
            authorize,
            purpose=purpose,
            representation_policy=policy,
            batch_policy=batch_policy,
        )
        _check(end)
        if (
            _snapshot(
                embedding_definition, tokenizer_definition, runtime, launch_inputs, reservation
            )
            != snapshot
        ):
            raise ExecutorRefused("corpus execution refused")
        metadata = json.loads(result.metadata)
        rows = doc["rows"][
            selection.first_ordinal : selection.first_ordinal + len(selection.chunk_ids)
        ]
        actual = metadata["rows"]
        if len(actual) != len(rows) or any(
            a["chunk_id"] != b["chunk_id"]
            or a["rendered_sha256"] != b["rendered_sha256"]
            or a["revision_id"] != source["revision_id"]
            or a["extraction_id"] != source["extraction_id"]
            or a["source_scope_sha256"] != source["source_scope_sha256"]
            for a, b in zip(actual, rows, strict=True)
        ):
            raise ExecutorRefused("corpus execution refused")
        records = (
            result.execution_record,
            result.native_runtime_record,
            result.execution_fingerprint,
        )
        if common is None:
            common, dependencies = records, metadata["dependencies"]
        elif records != common or metadata["dependencies"] != dependencies:
            raise ExecutorRefused("corpus execution refused")
        completion = BatchCompletion(
            selection.batch_index,
            result.job_id,
            result.output_ref,
            hashlib.sha256(result.metadata).hexdigest(),
            result.reused,
        )
        size = len(json.dumps(asdict(completion), sort_keys=True, separators=(",", ":")).encode())
        used += size + bool(completions)
        if used > 32 * 1024 * 1024:
            raise ExecutorRefused("corpus execution refused")
        completions.append(completion)
        del value, result, metadata, actual, rows
    _check(end)
    if program.validate(originals, derived, program_bytes).program_bytes != program_bytes:
        raise ExecutorRefused("corpus execution refused")
    _check(end)
    if (
        _snapshot(embedding_definition, tokenizer_definition, runtime, launch_inputs, reservation)
        != snapshot
    ):
        raise ExecutorRefused("corpus execution refused")
    _check(end)
    return CorpusResult(
        validated.source_program_id, validated.row_count, tuple(completions), *common
    )
