# Canonical 005 record protocol — identities, reconstruction, scopes and jobs

Objective 005 SOFTWARE slice (005-a source admission/store, 005-b provenance and job
records). This page states the exact record identities and boundaries implemented so far;
the component contracts remain in `docs/parallel/source-admission-api.md`,
`docs/parallel/source-cli-api.md`, `docs/parallel/provenance-records-api.md` and
`docs/parallel/job-records-api.md`. Nothing here performs extraction, tokenization,
embedding, authorization, retrieval or worker execution.

## Exact identities

| Identity | Definition | Produced by |
|---|---|---|
| original blob | SHA-256 over the exact admitted bytes | `OriginalStore.admit` |
| source revision | `fingerprint({version:1, kind:"source-revision", source})` over the validated `Source` metadata | `source_admission._identity`; metadata-sensitive: any metadata change yields a new revision over the same blob |
| extraction | `extraction_id(definition)` = `fingerprint({version:1, kind:"extraction", definition})` | declared caller definition; NOT execution evidence |
| chunk policy | `policy_id(definition)` = `fingerprint({version:1, kind:"chunk-policy", definition})` | declared caller definition |
| chunk | `chunk_id(chunk)` = `fingerprint({version:1, kind:"chunk", record})` over every chunk field except the ID, including fragments, text, hashes, counts | construct with a temporary ID, then replace with this value before binding |
| job | `job_id` = `fingerprint({domain:"job-spec", **spec})` over kind, purpose, ordered inputs and configuration digests | `JobSpec.job_id`; mapping key order irrelevant, input order meaningful |
| attempt | caller-supplied opaque `attempt_id`; `request_id` is correlation, not identity | never derived from the schema |

The shared `schema.fingerprint` scheme is versioned canonical JSON with ASCII escaping and
the `slaif-fingerprint-v1` prefix; it is never Python `hash()`. Source revision, extraction
dependency and chunk policy are distinct traceable identities; a block and chunk bind to a
dependency, not to an extractor execution, and no extractor execution is invented before one
occurs. Duplicate bytes retain distinct source/document/rights identities across revisions.

## Unicode code-point reconstruction

`SourceFragment` spans are start-inclusive/end-exclusive Unicode CODE-POINT offsets into the
exact unmodified extracted block text. Ordered typed `SourceFragment` entries and explicit
`Separator` entries concatenate to the exact claimed chunk text; `Chunk.text` and
`Chunk.text_sha256` (SHA-256 over UTF-8) must both match, and `bind_chunk` re-checks every
copied span against the block. Repeated references to the same original table-header block
keep the original block identity. No normalization occurs; astral characters, combining
marks, non-ASCII letters and CRLF/LF sequences round-trip. Bytes, graphemes, PDF
coordinates and tokenizer positions are never reinterpreted as offsets. Empty source
fragments and empty separators are rejected; unknown blocks, conflicting copied text,
boolean/out-of-range offsets and wrong hashes or dependencies fail closed with input-free
errors.

## Origins: native, transcription, interpretation

`Block.origin` is `native` or `visual_transcription`; the latter must carry the original
`page_ref` and explicit `uncertainty` (crop and finite ordered geometry are optional and
never manufactured from a model description). `Derived` records with origin `context` or
`interpretation` are separate artifacts, never original blocks; interpretation additionally
requires a page reference and uncertainty. This slice validates supplied SYNTHETIC
extraction records; it does not perform real extraction.

## Labels, rights and same-source support

`Source.access_labels` is an explicit canonical sorted set with ALL-label semantics: every
required label must be held by the principal, missing labels are invalid, and the empty set
is the public source CLASSIFICATION (not anonymous API access). Blocks and chunks inherit
the whole approved source-revision classification; `Scope` records separate
`processing_approved` metadata from `redistribution_rights`. `bind_derived` returns the
target classification with labels unioned across all support blocks, and rejects any support
crossing the target document, revision, corpus or access boundary — unioning labels is never
permission to construct a mixed public/private parent, and shared bytes never merge
source/document/rights identities. `reader_allows` is a pure effective-scope intersection
with explicit operator `Grants` (corpora, versions, all labels) and optional narrowing
`Restrictions`; absent grants, empty version grants, missing labels and UNKNOWN (null)
declared versions all deny. Authentication, policy epochs, revocation and retrieval
admission remain later implementation.

## Neighbors

`Neighbors` relations are explicitly supplied; null means unknown, not a document end.
`bind_neighbors` requires compatible revision/extraction/policy, rejects unknown,
self, duplicate and conflicting reciprocal references (when both sides are supplied they
must agree), and never infers adjacency. Neighbor changes do not alter chunk IDs.

## Jobs and attempts versus execution

`JobSpec` binds complete declared inputs (kind, revision/artifact digest, fingerprint) and
configuration digests (policy, model, prompt, encoder, runtime `null` = explicitly
unqualified). Mutable job progress is a chain of immutable `JobState` values through the
pure `transition` function with the bounded status set of architecture §8.4; immutable
`Attempt` records carry their own identities, safe status/request correlation, bounded
counts (known zero stays zero, unavailable is null) and optional `OutputRef`. A `COMPLETE`
state with an `OutputRef` is a caller assertion — `verified` availability still requires
independent current artifact and dependency validation; no cache hit, exactly-once
inference, claim ownership, retry execution or output-first publication follows from these
DTOs (objective 010). `UNKNOWN_COMPLETION` preserves correlation and has no automatic retry
path; `RETRYABLE_FAILED` → PENDING retains the prior attempt ID and the next claim must use
a different one.

## Remaining 005 scope and boundaries

The original 005 criteria are reconciled in the 005-b report and strategic review: this
slice implements record validation and pure scope/transition behavior over the real
005-a store, with the combined journey in `tests/integration/test_canonical_records_journey.py`.
Extraction (006), contextualization (010), embedding (007), snapshots (008), serving and
auth (014), revision/revocation (017) remain later ordered work; real model, hardware,
license and corpus qualification remains NOT RUN.
