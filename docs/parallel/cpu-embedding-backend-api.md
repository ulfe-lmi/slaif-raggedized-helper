# CPU CLS backend

`CPUEmbeddingBackend(manifest_bytes, artifact_root, definition, tokenizer_definition,
expected_inventory_id)` admits the local space, verifies the inventory and closed tree, then
loads one fixed XLMRobertaModel. `forward_cls(sequences)` accepts 1–128 ordered integer token
sequences of 2–1024 IDs and returns immutable raw FP32 CLS rows of 1024 floats. It pads using
the verified config. `close()` is idempotent; a failed forward closes the instance. These rows
are not normalized embeddings. The later encoder service must perform native tokenizer
preflight, normalization and storage validation.

The caller owns a protected absolute artifact tree for the backend's lifetime. It must contain
exactly the inventory files and necessary directories, without symlinks or concurrent mutation.
The fixed weight name is `model.safetensors` or schema 2 `pytorch_model.bin`. Admission and
expected inventory identity establish neither operator approval, model provenance nor license.
The backend does not copy, stage or download artifacts.

The source now selects the cpu-v2 lock: CPython 3.12, torch 2.14.0+cpu,
transformers 5.22.2, framework tokenizers 0.23.1, safetensors 0.8.0,
huggingface-hub 1.31.0 and numpy 2.5.4, with all 38 locked distribution
metadata versions required. The independent native tokenizer engine remains 0.21.4;
the framework tokenizer dependency is not used for native receipts.

This is a source and fake-protocol cutover, not qualification of those packages.
Actual class loading, a newly owned toy model, BGE, ABI, security, license, numerical
parity and independent coverage audit remain future gates. Canonical integration and
CI must provision both the legacy fixture for legacy helpers and the v2 fixture.
The declared change preserves the semantic space, definition and intended CPU FP32
identity, while the complete execution and source fingerprints change. Tests use
trusted fake framework modules in the real worker protocol; local-only flags alone
are not operating-system network or credential isolation. Real package startup,
checkpoint security, CPU capacity, quality, memory and latency remain unqualified.
