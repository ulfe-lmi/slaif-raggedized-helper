# Operator ingestion profile

`parse_profile(bytes)` and `load_profile(operator_path)` return a frozen `Profile` or raise the
fixed input-free `ProfileError`. The path is explicitly selected by an operator, never by a
source document. Loading admits one non-symlink regular file through a nonblocking descriptor,
checks its identity and timestamps before and after reading, and closes it. Parsing performs no
filesystem access. Both operations have a cooperative five-second deadline; a blocked filesystem
call cannot be forcibly interrupted by this deadline.

The exact JSON object has `schema_version` (integer 1), `native_runtime` (exact keys `root`,
`packages`, `python`), `bge`, `reranker`, `pdf_runtime`, and `chunk_policy`. Runtime python is
`python3.12` or `python3.14`. Each tokenizer record has exactly `artifact`, `sha256` (64 lowercase
hex characters), `backend_version` (`0.21.4`), `model_revision`, and `preprocessing` (each 1–256
valid Unicode characters). Paths are absolute, 1–4096 valid Unicode characters, without NUL.
`pdf_runtime` is null or an object with exactly `runtime_dir` and `packages_dir` paths.
`chunk_policy` must explicitly contain every field of the actual `chunking.Policy`; that class
validates all values and caps. No defaults are inserted. JSON is UTF-8, at most 65536 bytes,
without duplicate keys or nonfinite numbers, at most depth 16 and 10000 nodes.

The BGE record creates separate fixed `bge_body` and `bge_representation` definitions; the
reranker record creates `reranker_pair`. The returned policy object must be used as the same
object in the later producer and metadata. Paths and declarations do not establish artifact
existence, hashes, backend or model equivalence, preprocessing, serving, or licensing. Actual
hash and count validation remains a later producer step. CLI, preparation, Store, PDF integration,
current CI, 019, model and domain qualification, license, ICA, and full MVP remain open.

A toy example can be constructed by supplying arbitrary owned absolute paths and explicitly
serializing every field from `dataclasses.asdict(chunking.Policy())`; those toy paths are not
configured runtime or model recommendations.

For example, this is an owned toy declaration, not an installed model or runtime:

```json
{
  "schema_version": 1,
  "native_runtime": {"root": "/toy/runtime", "packages": "/toy/packages", "python": "python3.12"},
  "bge": {"artifact": "/toy/bge", "sha256": "0000000000000000000000000000000000000000000000000000000000000000", "backend_version": "0.21.4", "model_revision": "toy", "preprocessing": "toy"},
  "reranker": {"artifact": "/toy/reranker", "sha256": "0000000000000000000000000000000000000000000000000000000000000000", "backend_version": "0.21.4", "model_revision": "toy", "preprocessing": "toy"},
  "pdf_runtime": null,
  "chunk_policy": {"target": 512, "soft_max": 768, "representation_max": 1024, "pair_max": 1280, "query_reserve": 64, "max_blocks": 4096, "max_chars": 1000000, "max_chunks": 4096, "max_calls": 20000, "max_work_chars": 20000000, "deadline_ms": 15000}
}
```
