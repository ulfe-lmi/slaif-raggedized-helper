# Local native chunk counts

`native_chunking.build(registry, blocks, body, representation, pair, runtime, query,
policy=None)` accepts a validated provenance Registry and the complete ordered tuple of
blocks for one extraction. The three explicit `native_tokenizers.Definition` values must
have roles `bge_body`, `bge_representation` and `reranker_pair`, respectively. A fixed
owned Session verifies actual artifact bytes and counts exact already-preprocessed
strings, then closes on success or failure. Two artifacts at most are permitted; the
same file may serve both BGE roles. No source-selected executable or tokenizer is used.
The caller declares revision and preprocessing; this does not verify inference parity.

The returned frozen `Result` contains chunks, reciprocal neighbors and three frozen
receipts per chunk. Each count has `OBSERVED_LOCAL_NATIVE_TOKENIZATION` provenance and
a SHA-256 fingerprint of versioned definition fields: observed artifact hash, backend
version, declared revision and preprocessing, role, mode and serialization. The adapter
checks the entire `Count` against the exact input before binding it. Body input is chunk
text, representation is the concatenated heading path followed by body, and pair input
is query followed by the complete representation. The worker uses special tokens, no
truncation and no padding. Input digest is SHA-256 of UTF-8 JSON `[text,pair]` with
`ensure_ascii=True` and compact separators (single mode uses null for pair).
`receipts_json()` returns version 1 bounded JSON containing chunk ID, definition
fingerprint and complete Count, including digest and declarations, without source or
query text. Store receipts with the chunks if persistence is needed; this API itself
does not persist records. Rebinding verifies Registry contracts and changes IDs and
neighbors deterministically when observed provenance, policy or query changes. Legacy
callback chunks remain `SUPPLIED_UNVERIFIED`.

Default chunk policy is target 512, soft maximum 768, heading representation maximum
1024, full independent pair maximum 1280 and explicit query reserve 64. The pair
maximum 1280 follows the architecture example; it is not the legacy seam's 512
fixture default. Caller-supplied smaller values remain strict. The entire pair and
query-with-empty-passage are measured, so reserve is not a substitute for pair counting.
The inherited builder has a five-second build budget, 4096 blocks/chunks, one million
source characters, 20,000 calls and 20 million work characters; Session limits are
stricter where applicable: startup five seconds, request two seconds, lifetime 20
seconds, 8192 calls, 16 MB input, 4 MB output, 200000 bytes and 100000 characters per
request, 4096 bytes per response and 200000 tokens per count. Each build memoizes only exact role and full input pairs after the first native
response is validated. The cache belongs to that build and Session, never crosses
sources or builds, and retains the first observation. Cache hits still consume the
chunker callback, work-character and deadline budgets; native requests consume the
Session request and byte budgets. The cache is bounded by those Session limits. Receipt output is capped at 8 MB after
serialization of produced results; this is not a general memory admission guarantee for
arbitrary caller-forged Result or Receipt objects. Exceeding a limit refuses without
returning a partial result. Errors contain no source text. Filesystem reads and runtime/packages are trusted local inputs, and
caller concurrency must be bounded externally.

These are observed local tokenizer counts, not model, serving latency, hardware or
inference qualification. Full 006, 012 preprocessing/inference alignment, 019 held-out
evaluation, native and transitive license audit, independent architecture review (ICA),
rights and deployment gates remain open. Public tokenizer tooling and the standalone
development backend are not transitive or license approval.

Representative synthetic procedure and table fixtures complete under these limits, but
larger documents can still refuse: a 157,312-byte many-paragraph fixture reached the
five-second builder budget in a local run. This is not a general capacity guarantee;
CPU speed, tokenizer behavior and source structure affect admission. No MVP claim,
model/domain qualification or inference parity follows from these software counts.
