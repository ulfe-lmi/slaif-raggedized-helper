# Embedding space admission

`admit` verifies the caller-selected manifest and protected local artifact tree, compares the operator-configured expected inventory ID, and binds the sole verified checkpoint weight and tokenizer to the supplied definitions. Version 1 supports BGE-M3 CLS, L2 normalization, 1024 dimensions and identity query preprocessing only; multiple weight shards are unsupported. The caller must supply an absolute, lexically normal root and its exact `tokenizer.json` path; alternate paths and aliases are unsupported. The verifier requires protected files and rejects symlinks.

The resulting identity excludes paths and execution device or dtype. The expected ID is configuration, not approval, a license, or publisher attestation. This verifies synthetic or supplied files, not a loaded model. A future loader must repeat admission at its actual trust boundary and consume only verified files; this API does not ensure framework file selection or prevent changes after verification. It does not establish provenance, licensing, current authorization, hardware qualification, or model behavior.

Composition checks exercise real local file verification, configuration identity, private-path
refusal and the shared cooperative deadline. They do not load weights or run a model; the
deadline is cooperative and cannot preempt an individual blocking filesystem operation.

Schema 1 retains its safetensors compatibility behavior. Schema 2 admits `safetensors` at `model.safetensors` or `pytorch-state-dict` at `pytorch_model.bin`; admission hashes raw bytes and never loads them. The admitted result exposes the verified schema and format. A future loader needs a separately reviewed safe loading policy.
