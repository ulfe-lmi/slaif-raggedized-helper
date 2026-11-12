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

The isolated candidate worker profile is CPython 3.12, torch 2.10.0+cpu, transformers 4.51.3,
tokenizers 0.21.4, safetensors 0.5.3, huggingface-hub 0.30.2 and numpy 2.2.6. Runtime checks
require those exact versions; this is not a resolved transitive hash lock. Keep this worker
separate from application dependencies. Local-only flags are not network or credential isolation:
the future owned worker must enforce both at the operating-system boundary. Real package and
model startup, checkpoint security, CPU execution, tokenizer parity, quality, memory and latency
remain unqualified. Trusted fake tests establish the software contract only; no actual model
or weight execution was performed.
