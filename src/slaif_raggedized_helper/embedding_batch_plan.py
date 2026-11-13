"""Fresh source-bound declarations for intended CPU embedding batches."""

from dataclasses import asdict, dataclass
import hashlib
import json
import os
from pathlib import Path
import re

from . import embedding_batch_store, embedding_job_journal, embedding_space, embedding_vectors
from . import ingestion_bundle, native_tokenizers, retrieval_representation, schema
from .source_admission import OriginalStore


class PlanError(ValueError):
    """A content-free refusal of the entire plan."""


@dataclass(frozen=True)
class Prepared:
    plan_bytes: bytes
    spec: object
    texts: tuple[str, ...]


def _hex(value):
    return type(value) is str and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def _unprefix(value):
    if type(value) is not str or not value.startswith("sha256:") or not _hex(value[7:]):
        raise ValueError
    return value[7:]


def _path(value):
    if type(value) not in (str, type(Path())):
        raise ValueError
    if type(value) is type(Path()):
        parts = value._raw_paths
        if (
            type(parts) is not list
            or len(parts) > 4096
            or any(type(part) is not str or len(part) > 4096 for part in parts)
            or sum(map(len, parts)) > 4096
        ):
            raise ValueError
    value = os.fspath(value)
    if (
        len(value) > 4096
        or not value.startswith("/")
        or value == "/"
        or os.path.normpath(value) != value
        or len(value.encode("utf-8")) > 4096
    ):
        raise ValueError
    return value


def _preflight(
    store, metadata, members, ids, manifest, root, d, t, expected, runtime, purpose, policy, bp
):
    if (
        type(store) is not OriginalStore
        or type(metadata) is not bytes
        or not 1 <= len(metadata) <= ingestion_bundle.METADATA_BYTES
        or type(members) is not tuple
        or len(members) != 5
        or type(ids) not in (list, tuple)
        or not 1 <= len(ids) <= 128
        or type(manifest) is not bytes
        or not 1 <= len(manifest) <= 262144
        or type(purpose) is not str
        or purpose not in ("prepare", "evaluate")
        or type(policy) is not retrieval_representation.Policy
        or type(bp) is not retrieval_representation.BatchPolicy
    ):
        raise ValueError
    total = len(metadata)
    for index, item in enumerate(members):
        if (
            type(item) is not tuple
            or len(item) != 2
            or type(item[0]) is not str
            or item[0] != ingestion_bundle.NAMES[index]
            or type(item[1]) is not bytes
            or len(item[1]) > ingestion_bundle.CAPS[index]
        ):
            raise ValueError
        total += len(item[1])
    if total > ingestion_bundle.TOTAL_BYTES:
        raise ValueError
    if (
        type(bp.version) is not str
        or bp.version != "raw-batch-v1"
        or any(
            type(v) is not int or not 1 <= v <= limit
            for v, limit in (
                (bp.max_items, 128),
                (bp.max_total_codepoints, 1000000),
                (bp.max_total_request_bytes, 4000000),
            )
        )
        or len(ids) > bp.max_items
        or any(
            type(x) is not str
            or not 1 <= len(x) <= 71
            or len(x.encode("utf-8")) > 71
            or any(ord(c) < 32 or 127 <= ord(c) <= 159 for c in x)
            for x in ids
        )
        or len(set(ids)) != len(ids)
        or type(policy.max_tokens) is not int
        or not 1 <= policy.max_tokens <= 1024
        or type(policy.version) is not str
        or policy.version != "raw-v1"
        or type(policy.separator) is not str
        or policy.separator != "\n\n"
        or type(policy.max_codepoints) is not int
        or policy.max_codepoints != 100000
        or type(policy.max_request_bytes) is not int
        or policy.max_request_bytes != 200000
    ):
        raise ValueError
    root_path = _path(root)
    if (
        type(d) is not schema.EmbeddingDefinition
        or type(t) is not native_tokenizers.Definition
        or type(runtime) is not native_tokenizers.Runtime
        or not _hex(expected)
        or type(d.model_name) is not str
        or d.model_name != "BAAI/bge-m3"
        or type(d.checkpoint_revision) is not str
        or re.fullmatch(r"[0-9a-f]{40}", d.checkpoint_revision) is None
        or not _hex(d.checkpoint_sha256)
        or type(d.tokenizer_revision) is not str
        or d.tokenizer_revision != d.checkpoint_revision
        or type(d.pooling) is not str
        or d.pooling != "cls"
        or d.normalize is not True
        or d.query_prefix is not None
        or type(d.dimensions) is not int
        or d.dimensions != 1024
        or type(t.artifact) is not type(Path())
        or _path(t.artifact) != root_path + "/tokenizer.json"
        or not _hex(t.sha256)
        or type(t.backend_version) is not str
        or t.backend_version != "0.21.4"
        or type(t.role) is not str
        or t.role != "bge_representation"
        or type(t.model_revision) is not str
        or t.model_revision != d.checkpoint_revision
        or type(t.preprocessing) is not str
        or t.preprocessing != "identity"
        or type(runtime.root) is not type(Path())
        or type(runtime.packages) is not type(Path())
        or type(runtime.python) is not str
        or re.fullmatch(r"python3\.(12|14)", runtime.python) is None
    ):
        raise ValueError
    _path(runtime.root)
    _path(runtime.packages)


def build(
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
    *,
    purpose="prepare",
    representation_policy=None,
    batch_policy=None,
):
    """Revalidate source and artifacts and return an immutable, unexecuted plan."""
    try:
        policy = (
            retrieval_representation.Policy()
            if representation_policy is None
            else representation_policy
        )
        bp = retrieval_representation.BatchPolicy() if batch_policy is None else batch_policy
        _preflight(
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
        space = embedding_space.admit(
            manifest_bytes,
            artifact_root,
            embedding_definition,
            tokenizer_definition,
            expected_inventory_id,
        )
        reps = retrieval_representation.build_many(
            original_store,
            bundle_metadata_bytes,
            bundle_members,
            chunk_ids,
            tokenizer_definition,
            runtime,
            policy,
            bp,
        )
        if (
            type(space) is not embedding_space.AdmittedSpace
            or type(reps) is not tuple
            or len(reps) != len(chunk_ids)
            or space.inventory_id != expected_inventory_id
            or space.tokenizer_sha256 != tokenizer_definition.sha256
            or space.preprocessing != tokenizer_definition.preprocessing
            or space.definition_fingerprint != embedding_definition.fingerprint()
        ):
            raise ValueError
        rows = []
        texts = []
        for index, rep in enumerate(reps):
            if (
                type(rep) is not retrieval_representation.Representation
                or rep.chunk_id != chunk_ids[index]
                or rep.variant != "raw"
                or rep.policy != policy
                or type(rep.text) is not str
                or rep.rendered_sha256 != hashlib.sha256(rep.text.encode("utf-8")).hexdigest()
            ):
                raise ValueError
            count = rep.count
            input_hash = hashlib.sha256(
                json.dumps([rep.text, None], ensure_ascii=True, separators=(",", ":")).encode(
                    "utf-8"
                )
            ).hexdigest()
            if (
                type(count) is not native_tokenizers.Count
                or type(count.count) is not int
                or not 2 <= count.count <= policy.max_tokens
                or count.artifact_sha256 != space.tokenizer_sha256
                or count.backend_version != tokenizer_definition.backend_version
                or count.role != tokenizer_definition.role
                or count.model_revision != embedding_definition.checkpoint_revision
                or count.preprocessing != space.preprocessing
                or count.input_sha256 != input_hash
                or count.mode != "single"
                or count.serialization != "utf8-json-v1;no-truncation;no-padding;special-tokens"
            ):
                raise ValueError
            rows.append(
                dict(
                    chunk_id=rep.chunk_id,
                    revision_id=rep.revision_id,
                    extraction_id=rep.extraction_id,
                    representation_id=rep.representation_id,
                    rendered_sha256=rep.rendered_sha256,
                    source_scope_sha256=_unprefix(
                        schema.fingerprint(
                            {
                                "kind": "embedding-source-scope-v1",
                                "scope": rep.scope.model_dump(mode="json"),
                            }
                        )
                    ),
                    input_sha256=count.input_sha256,
                    token_count=count.count,
                )
            )
            texts.append(rep.text)
        dependencies = dict(
            space_id=space.space_id,
            inventory_id=space.inventory_id,
            definition_fingerprint=_unprefix(space.definition_fingerprint),
            execution_fingerprint=_unprefix(
                schema.EmbeddingExecution(
                    definition=embedding_definition, device="cpu", dtype="fp32"
                ).fingerprint()
            ),
            tokenizer_sha256=space.tokenizer_sha256,
            normalization_policy_id=embedding_vectors.POLICY_ID,
            representation_policy_fingerprint=_unprefix(
                schema.fingerprint(
                    {
                        "kind": "embedding-representation-policy-v1",
                        "policy": asdict(policy),
                        "batch_policy": asdict(bp),
                    }
                )
            ),
        )
        plan = dict(
            format="embedding-job-plan-v1",
            purpose=purpose,
            dependencies=dependencies,
            rows=rows,
            codec_policy_fingerprint=embedding_batch_store.POLICY.fingerprint(),
        )
        data = json.dumps(
            plan, sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(",", ":")
        ).encode("utf-8")
        if len(data) > 131072:
            raise ValueError
        return Prepared(data, embedding_job_journal.make_spec(data), tuple(texts))
    except Exception:
        raise PlanError("embedding batch plan refused") from None
