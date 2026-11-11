# Raw retrieval representation

`build(store, metadata_json_bytes, members, chunk_id, definition, runtime, policy=None)` revalidates the entire bundle against the trusted original store on every call, selects the chunk and joins the source title, nonempty headings and original text with two line feeds. It returns a frozen representation with scope, source, identity, exact text and native count. Scope records provenance; it does not authorize access. `Policy(max_tokens=...)` may lower the default 1024 token limit. Refusals raise `RepresentationError` without input details.

The count covers the final string, with special tokens and without truncation or padding. It does not qualify an encoder, checkpoint or hardware. The caller supplies trusted tokenizer configuration. No generated annotations are supported. Session reuse and batching are future work; each build incurs bundle validation and worker startup.
