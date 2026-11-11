# Structured text bundle value API

`ingestion_bundle.validate(store, metadata_json_bytes, members)` accepts an actual trusted
`OriginalStore`, immutable metadata bytes and a tuple of five `(name, bytes)` pairs ordered
`blocks`, `coverage`, `chunks`, `neighbors`, `receipts`. It returns a frozen `Validated` value
with reverified source, scope, dependency, blocks, coverage, policy, chunks, neighbors, receipts,
canonical metadata and canonical members. It refuses the whole input with an input-free
`BundleError`; it does not publish, invoke tokenizers, or execute a document-supplied path.
Canonical output can be revalidated. Metadata fields and member formats follow
[native bundle v1](native-bundle-value-contract.md). Structured text and PDF source records are supported.

Admission limits metadata to 256 KiB, each JSONL stream to 16 MiB, each JSONL record to 1 MiB,
coverage to 2 MiB, receipts to 8,000,000 bytes, aggregate to 96 MiB, blocks and chunks to
4,096 each, and fragments to 1,048,576. Existing leaf schema, node, work and 30-second limits
also apply; the outer validator checks a cooperative 30-second deadline through final success.
The deadline cannot interrupt a blocked filesystem operation.

For structured text, the validator re-extracts the verified source. It binds each chunk to its exact source fragments,
requires contiguous first exposure in original order, checks heading stacks and the complete
neighbor chain, and validates native receipt consistency. It retains explicit separators.
Source rights and labels are not authentication or serving authorization. Counts and hashes
are mechanical consistency checks, not proof that a tokenizer ran: a coordinated false count
and matching receipt can remain consistent. Query-only reserve and overlap-token observations
are not present in the exported receipts and are trusted producer invariants.

This value layer does not provide the descriptor store, fresh loader, or installed operator CLI.
Full 006 requires verified durable publication/load, the installed private operator CLI and
current CI. Objective 019, model, domain, licensing, hardware, independent audit and broader
MVP gates remain open.

PDF source records are also supported through fixed `pdf_extraction` dispatch. Returned
`coverage` is a text codepoint-coverage tuple (empty for PDF); `pages` is a PDF page/status
tuple (empty for text). `adapter`, `status`, and `coverage_kind` come from the validated
source header. PDF fragment offsets index extracted block text codepoints, not PDF bytes.
PDF records preserve heuristic and partial-visual status; loading does not re-extract PDF or
attest completeness or visual fidelity. An all-visual source with no native blocks cannot
form a native bundle. The later operator must represent that partial/no-native-chunks outcome.
This support retains the source producer and pinned storage trust boundary described in
[bundle PDF records](bundle-pdf-records-api.md). Descriptor Store, fresh verified loader,
private CLI, 019, model, license, independent audit and full MVP gates remain open.

PDF policy v4 binds the literal classifier; kind is part of the shared block fingerprint v2. Legacy v3 PDF records require explicit re-extraction, not an in-place upgrade. Stored validation rederives kinds without running a PDF parser or tokenizer; the trusted producer assumption and current authorization, visual, license, 019 and independent audit gates remain. The literal grammar is not a general PDF layout solution.
