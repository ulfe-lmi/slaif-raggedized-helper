# Local BGE-M3 artifact admission

`verify_artifacts(manifest_bytes, artifact_root, *, timeout=30)` accepts UTF-8 JSON bytes
and a caller-selected trusted local directory, and returns a frozen `VerifiedInventory`, or
raises `ArtifactRefused` with an input-free message. The root must be selected by the caller,
not by a document. The deadline is cooperative: it is checked between reads and other steps;
filesystem calls themselves may block and are not hard real-time operations.

Schema 1 is exactly `{ "schema": 1, "model_name": "BAAI/bge-m3", "model_revision":
"<40 lowercase hex>", "files": [...] }`. Each descriptor has exactly `role`, `path`,
`sha256` (64 lowercase hex) and integer `size` (bytes). Required role/path pairs are:

| Role | Path |
| --- | --- |
| config | config.json |
| tokenizer | tokenizer.json |
| tokenizer_config | tokenizer_config.json |
| special_tokens_map | special_tokens_map.json |
| modules | modules.json |
| pooling | 1_Pooling/config.json |
| sentence_bert_config | sentence_bert_config.json |
| sentence_transformers_config | config_sentence_transformers.json |

At least one `weights` descriptor is required; it may occur multiple times with distinct
relative `.safetensors` paths. No names, sizes, or hashes of actual weights are assumed.
Paths are unique, relative, slash-separated and contain no empty, dot, dot-dot, NUL, colon,
or backslash components. Manifests are at most 256 KiB and 32 descriptors, each file at most
4 GiB and total at most 8 GiB. Small JSON files are at most 64 KiB; tokenizer bytes are at
most 32 MiB and are hashed without parsing. Streaming reads are at most 64 KiB.

Root path components and files are opened without following symlinks. The root and objects
inside it must be owned by the effective user or root and not group/world writable; files must
be regular. Descriptor sizes and hashes are verified, metadata checked before and after reads,
and paths reopened to detect replacement. Concurrent filesystem operations cannot be made
atomic across an entire tree: a sufficiently privileged adversary or changes after the final
check remain outside this point-in-time proof. Protect the tree throughout use.

Small JSON rejects duplicate keys, nonfinite values and `auto_map` anywhere. The verifier
requires XLM-RoBERTa/1024, the built-in Transformer, Pooling and Normalize sequence and paths,
CLS pooling with every other declared pooling mode false, and 8192 token configuration with
lowercasing disabled. Unsupported custom model or tokenizer classes are refused. Package
version metadata is recorded through the verified file hash, never used to select dependencies.
No code or weights are loaded. The canonical inventory ID hashes the revision and sorted file
map, including verified sizes and digests; semantic configuration is bound by its file digests.
It is independent of the local root and does not change the legacy embedding fingerprint.

A manifest is an operator's expected inventory, not evidence of publisher origin: compare it
with independently trusted expected digests and provenance. The returned dataclass alone can
be forged; invoke the verifier on the bytes and files at the relevant trust boundary. This is
not license clearance, encoder construction, authorization, device qualification or inference.
