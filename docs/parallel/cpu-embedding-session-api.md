# Owned CPU embedding session

`CPUEmbeddingSession(manifest_bytes, artifact_root, definition, tokenizer_definition,
expected_inventory_id, runtime, *, parent=None)` is an owned context manager. Actual
staging, admission and native worker startup precede loading a single resident CPU/FP32 backend. The tokenizer
is rebound to the staged `tokenizer.json`; the backend independently admits that tree.
`embed(texts)` returns fresh lists of normalized vectors. `encode(texts)` returns frozen
`EncodedBatch` containing the normalized payload, native receipts, admitted space ID,
definition and CPU/FP32 execution fingerprints, and normalization policy ID. These
execution and policy identities do not alter the embedding space fingerprint.

Inputs are lists or tuples of 1–128 exact strings, bounded to 100,000 characters and
200,000 encoded wire bytes each and 1 million characters and 4 million wire bytes per
batch. Identity text is used unchanged. All input preflight and native receipts are
validated before one ordered backend forward. A nonblocking guard rejects concurrent or
reentrant operations. Failures close the owned resources; close is idempotent when idle.
A native worker is renewed before a batch when its call, input byte, or remaining lifetime
budget cannot accommodate the batch with two seconds per row and five seconds startup
margin. Renewal reuses the staged tokenizer without reloading the model. It never retries
a failed forward. The native worker retains its 300 second, 1024 call and 32 MB limits.

The caller must establish rights and current ACL before invoking this API. Staging assumes
trusted ancestry and filesystem; runtime and installed tokenizer packages remain trusted.
The neural backend runs in process: no kernel neural-worker isolation, physical RAM release,
actual model execution, latency or residency qualification is established. Protected
artifact ancestry, trusted runtime, current authorization, actual model and CPU/GPU parity,
license, quality and hardware qualification remain separate gates.
