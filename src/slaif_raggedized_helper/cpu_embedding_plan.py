"""Fresh source plans bound to a predicted, pre-model CPU execution contract."""

from dataclasses import dataclass
import json

from . import cpu_embedding_worker, cpu_execution_contract, embedding_batch_plan
from . import embedding_job_journal, isolated_cpu_embedding, retrieval_representation, schema


class PlanError(ValueError):
    """A content-free refusal of the entire CPU plan."""


@dataclass(frozen=True)
class Prepared:
    plan_bytes: bytes
    spec: object
    texts: tuple[str, ...]
    predicted_record: bytes
    execution_fingerprint: str
    intended_execution_fingerprint: str


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
    cpu_runtime,
    *,
    purpose="prepare",
    representation_policy=None,
    batch_policy=None,
    worker_policy=None,
):
    """Revalidate both inputs and bind the complete predicted contract before model startup."""
    try:
        policy = cpu_embedding_worker.Policy() if worker_policy is None else worker_policy
        values = isolated_cpu_embedding._cpu_values(policy)
        bp = retrieval_representation.BatchPolicy() if batch_policy is None else batch_policy
        rp = (
            retrieval_representation.Policy()
            if representation_policy is None
            else representation_policy
        )
        # This admission precedes both filesystem access and native token counting.
        embedding_batch_plan._preflight(
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
            rp,
            bp,
        )
        if len(chunk_ids) > values[0]:
            raise ValueError
        contract = cpu_execution_contract.prepare(
            manifest_bytes,
            artifact_root,
            embedding_definition,
            tokenizer_definition,
            expected_inventory_id,
            runtime,
            cpu_runtime,
            worker_policy=policy,
        )
        if type(contract) is not cpu_execution_contract.PlannedContract:
            raise ValueError
        record = cpu_execution_contract._validate(contract.record_bytes)
        if (
            contract.fingerprint
            != schema.fingerprint({"kind": "isolated-cpu-embedding-execution-v2", **record})
            or record["space"] != contract.space_id
            or record["definition"] != embedding_definition.fingerprint()
            or record["native"]["artifact_sha256"] != tokenizer_definition.sha256
            or record["native"]["revision"] != tokenizer_definition.model_revision
        ):
            raise ValueError
        source = embedding_batch_plan.build(
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
            representation_policy=rp,
            batch_policy=bp,
        )
        plan = json.loads(source.plan_bytes)
        deps = plan["dependencies"]
        if (
            deps["space_id"] != contract.space_id
            or deps["inventory_id"] != expected_inventory_id
            or deps["definition_fingerprint"]
            != embedding_batch_plan._unprefix(embedding_definition.fingerprint())
            or deps["tokenizer_sha256"] != tokenizer_definition.sha256
            or deps["execution_fingerprint"]
            != embedding_batch_plan._unprefix(contract.intended_execution_fingerprint)
        ):
            raise ValueError
        deps["execution_fingerprint"] = embedding_batch_plan._unprefix(contract.fingerprint)
        data = json.dumps(
            plan, sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(",", ":")
        ).encode("utf-8")
        return Prepared(
            data,
            embedding_job_journal.make_spec(data),
            source.texts,
            contract.record_bytes,
            contract.fingerprint,
            contract.intended_execution_fingerprint,
        )
    except Exception:
        raise PlanError("CPU embedding plan refused") from None
