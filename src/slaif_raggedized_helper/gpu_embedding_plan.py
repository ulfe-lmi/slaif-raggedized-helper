"""Fresh source-bound GPU execution declarations; does not start a GPU worker."""

from dataclasses import asdict, dataclass
import hashlib
import json

from . import embedding_batch_plan as source
from . import embedding_job_journal, embedding_vectors, gpu_worker_launch
from . import gpu_worker_protocol as wire, isolated_gpu_embedding as bridge
from . import retrieval_representation, schema


class PlanError(ValueError):
    """Content-free refusal of the entire plan."""


@dataclass(frozen=True)
class Prepared:
    plan_bytes: bytes
    spec: object
    texts: tuple[str, ...]
    predicted_record: bytes
    native_runtime_record: bytes
    execution_fingerprint: str
    intended_execution_fingerprint: str
    space_id: str


def _prediction(prepared, runtime):
    prediction = bridge.predict(prepared, runtime)
    if type(prediction) is not bridge.PlannedContract:
        raise ValueError
    record = wire.parse(prediction.execution_record)
    if (
        bridge.validate_record(prediction.execution_record, prediction.native_runtime_record)
        != prediction.execution_fingerprint
        or record["space_id"] != prediction.space_id
        or record["definition_fingerprint"] != prediction.definition_fingerprint
        or record["intended_execution_fingerprint"] != prediction.intended_execution_fingerprint
    ):
        raise ValueError
    return prediction, record


def _bind(start, record, prediction, manifest, definition, tokenizer, inventory):
    token = start["tokenizer"]
    native = record["native"]
    expected_token = dict(
        sha256=tokenizer.sha256,
        backend_version=tokenizer.backend_version,
        role=tokenizer.role,
        model_revision=tokenizer.model_revision,
        preprocessing=tokenizer.preprocessing,
    )
    if (
        start["manifest"].encode("utf-8") != manifest
        or start["definition"] != definition.model_dump(mode="json")
        or start["inventory"] != inventory
        or start["space"] != prediction.space_id
        or token != expected_token
        or native["artifact_sha256"] != tokenizer.sha256
        or any(
            native[k] != expected_token[k]
            for k in ("backend_version", "role", "model_revision", "preprocessing")
        )
        or prediction.definition_fingerprint != definition.fingerprint()
        or prediction.intended_execution_fingerprint
        != schema.EmbeddingExecution(
            definition=definition, device="gpu", dtype="fp16"
        ).fingerprint()
    ):
        raise ValueError


def _bind_source(dep, prediction, record, legacy, expected_inventory_id, policy, bp):
    if (
        dep["execution_fingerprint"] != legacy
        or dep["space_id"] != prediction.space_id
        or dep["inventory_id"] != expected_inventory_id
        or dep["definition_fingerprint"] != source._unprefix(prediction.definition_fingerprint)
        or dep["tokenizer_sha256"] != record["native"]["artifact_sha256"]
        or dep["normalization_policy_id"] != embedding_vectors.POLICY_ID
        or dep["normalization_policy_id"] != record["normalization_policy_id"]
        or dep["representation_policy_fingerprint"]
        != source._unprefix(
            schema.fingerprint(
                {
                    "kind": "embedding-representation-policy-v1",
                    "policy": asdict(policy),
                    "batch_policy": asdict(bp),
                }
            )
        )
    ):
        raise ValueError


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
    prepared_launch,
    *,
    purpose="prepare",
    representation_policy=None,
    batch_policy=None,
):
    """Independently count admitted source and bind it to a borrowed prediction."""
    try:
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
        if type(prepared_launch) is not gpu_worker_launch.PreparedLaunch:
            raise ValueError
        prediction, record = _prediction(prepared_launch, runtime)
        startup = prepared_launch.startup
        start = wire.parse(startup)
        _bind(
            start,
            record,
            prediction,
            manifest_bytes,
            embedding_definition,
            tokenizer_definition,
            expected_inventory_id,
        )
        wire_policy = wire.Policy(**start["policy"])
        if len(chunk_ids) > wire_policy.max_rows:
            raise ValueError
        base = source.build(
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
            purpose=purpose,
            representation_policy=policy,
            batch_policy=bp,
        )
        obj = json.loads(base.plan_bytes)
        dep = obj["dependencies"]
        legacy = source._unprefix(
            schema.EmbeddingExecution(
                definition=embedding_definition, device="cpu", dtype="fp32"
            ).fingerprint()
        )
        _bind_source(dep, prediction, record, legacy, expected_inventory_id, policy, bp)
        sizes = [
            len(
                json.dumps(
                    {"text": t, "nonce": "0" * 32}, ensure_ascii=True, separators=(",", ":")
                ).encode()
            )
            + 1
            for t in base.texts
        ]
        if (
            any(len(t) > 100000 for t in base.texts)
            or sum(map(len, base.texts)) > 1000000
            or any(n > 200000 for n in sizes)
            or sum(sizes) > 4000000
            or any(not 2 <= row["token_count"] <= 1024 for row in obj["rows"])
        ):
            raise ValueError
        again, _ = _prediction(prepared_launch, runtime)
        if again != prediction or prepared_launch.startup != startup:
            raise ValueError
        execution = hashlib.sha256(prediction.execution_record).hexdigest()
        dep["execution_fingerprint"] = execution
        data = json.dumps(
            obj, sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(",", ":")
        ).encode("utf-8")
        if len(data) > 131072:
            raise ValueError
        return Prepared(
            data,
            embedding_job_journal.make_spec(data),
            base.texts,
            prediction.execution_record,
            prediction.native_runtime_record,
            execution,
            prediction.intended_execution_fingerprint,
            prediction.space_id,
        )
    except Exception:
        raise PlanError("GPU embedding plan refused") from None
