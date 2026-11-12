# Pre-model CPU contract and source plan

`cpu_execution_contract.prepare(manifest_bytes, artifact_root, definition,
tokenizer_definition, expected_inventory_id, tokenizer_runtime, cpu_runtime, *,
worker_policy=None)` performs scalar admission, verifies the actual model-space files, and
reads the pinned CPU profile metadata and selected code. It starts no tokenizer session,
CPU worker, model, or framework. It returns a frozen `PlannedContract` containing
`record_bytes`, `fingerprint`, `intended_execution_fingerprint`, and `space_id`.
Runtime roots, package directories, and their protected ancestry must be trusted.

`cpu_embedding_plan.build(original_store, bundle_metadata_bytes, bundle_members, chunk_ids,
manifest_bytes, artifact_root, embedding_definition, tokenizer_definition,
expected_inventory_id, runtime, cpu_runtime, *, purpose="prepare", representation_policy=None,
batch_policy=None, worker_policy=None)` independently admits source and contract inputs. It
returns frozen `plan_bytes`, `spec`, `texts`, `predicted_record`, `execution_fingerprint`, and
`intended_execution_fingerprint`. The source-derived plan is unchanged except for its execution
dependency, which binds the complete predicted contract. Its journal job identity can therefore
be claimed before model startup. The legacy source-plan API remains unchanged.

The canonical ASCII schema-2 record has exactly `schema`, `contract`, `space`, `definition`,
`worker`, `normalization`, `native`, `bridge`, and `hardware_qualification`. The worker fields
are `space`, `definition`, `profile`, `code`, and `policy`. Native fields are
`artifact_sha256`, `backend`, `role`, `revision`, `preprocessing`, `policy`, and `worker_sha256`;
the native policy records all fixed ID-session limits. The bridge maps exactly
`isolated_cpu_embedding.py`, `cpu_execution_contract.py`, `embedding_tokenizer.py`, and
`embedding_vectors.py` to SHA-256 digests. Hardware qualification is `unknown`. The record is
bounded to 16384 bytes and its hash uses the `isolated-cpu-embedding-execution-v2` domain.
Schema 2 deliberately changes execution identity from v1; legacy space, definition, and intended
CPU FP32 fingerprints remain unchanged.

A predicted record is not an observed handshake, current authorization, package-file attestation,
ABI or hardware qualification, nor evidence of neural behavior. The profile identifies selected
pinned package metadata under a trusted runtime. Frozen return objects are forgeable and do not
prove admission. A later controller must compare the actual observed record and fingerprint with
the prediction before forwarding content and before completing output, and must independently
recheck fresh source and current rights at the consumer boundary. This plan grants no inference or
GPU permission. Real runtime compatibility, model behavior, precision, hardware, licenses, ICA,
and MVP qualification remain open; the broader 007 objective remains partial.
