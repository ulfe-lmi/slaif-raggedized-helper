# Raw retrieval representation

`build(store, metadata_json_bytes, members, chunk_id, definition, runtime, policy=None)` revalidates the entire bundle against the trusted original store on every call, selects the chunk and joins the source title, nonempty headings and original text with two line feeds. It returns a frozen representation with scope, source, identity, exact text and native count. Scope records provenance; it does not authorize access. `Policy(max_tokens=...)` may lower the default 1024 token limit. Refusals raise `RepresentationError` without input details.

The count covers the final string, with special tokens and without truncation or padding. It does not qualify an encoder, checkpoint or hardware. The caller supplies trusted tokenizer configuration. No generated annotations are supported. A single build validates the bundle and starts a worker; build_many shares these across its selected rows.

The fixed preflight limits are 100,000 Unicode code points and 200,000 bytes for the ASCII-escaped session request. Policy size fields require exact integers; version and separator are fixed. Tokenizer identity metadata is bounded before bundle validation and hashing. A large source that would exceed the session wire cap may already be refused by native chunk construction, so a controlled representation-layer test covers that preflight independently.

`build_many(store, metadata_json_bytes, members, chunk_ids, definition, runtime,
policy=None, batch_policy=None)` returns an ordered tuple. The batch policy permits
up to 128 distinct IDs, one million rendered codepoints and four million escaped
request bytes; callers can lower these limits. Individual limits remain in force.
The source is validated once and a single native session counts each final text.
Failure rejects the entire batch. These are cooperative cost bounds, not a
throughput guarantee. Native token counting does not run an encoder.
