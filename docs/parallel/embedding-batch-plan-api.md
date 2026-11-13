# Fresh source-bound embedding batch plan

`embedding_batch_plan.build(original_store, bundle_metadata_bytes, bundle_members, chunk_ids,
manifest_bytes, artifact_root, embedding_definition, tokenizer_definition, expected_inventory_id,
runtime, *, purpose='prepare', representation_policy=None, batch_policy=None)` produces frozen
`Prepared(plan_bytes, spec, texts)`. `texts` is an ordered tuple of raw rendered source strings;
`spec` is revalidated by `embedding_job_journal.make_spec`. A fresh call admits the model inventory
from bytes and validates the original-backed bundle before counting all selected representations in
one native session. It does not run a model or publish vectors. Failures raise content-free
`PlanError` and return no partial plan. Inputs and policies are bounded and revalidated, including
mutated frozen instances; ordered chunk IDs must be unique and number 1–128.

The plan is sorted, compact UTF-8 JSON with `ensure_ascii=False` and no NaN, capped at 131072 bytes.
Dependencies use admitted space and inventory IDs and tokenizer hash, the normalization policy ID,
and the accepted codec policy fingerprint. Definition, intended CPU/FP32 execution, and full
representation/batch policy fingerprints use `schema.fingerprint`; the required `sha256:` prefix is
strictly checked and stripped for the plan's 64-character lowercase hexadecimal fields. Each row
binds the returned chunk, revision, extraction and representation IDs, rendered text SHA-256, native
input SHA-256 and count, plus the full actual scope's `embedding-source-scope-v1` schema fingerprint
with the same prefix conversion. The policy fingerprint hashes the full dataclass dictionaries under
`embedding-representation-policy-v1`. Journal specification identities include the no-generator-prompt
policy. CPU/FP32 is an intended execution identity, not proof that execution happened or that another
device is equivalent.

Artifact verification reads model weights only as bytes. The runtime and packages must be trusted
and approved; neither artifact admission nor source receipts establish a license or current access
rights. A `Prepared` value is forgeable and is not fresh authorization or source proof for a later
consumer; revalidate at the relevant boundary. This API provides no automatic retry, neural output,
vector storage, deployment, milestone acceptance, or independent audit claim.
