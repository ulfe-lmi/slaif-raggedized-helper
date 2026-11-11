# OAP Coding Report — 005-b

Identifier: 005-b
Result: COMPLETE
Repository: ulfe-lmi/slaif-raggedized-helper
PR number: 7
Branch: oap/005-artifact-schema-and-source-scopes
Base branch: main
Base commit: bd8e454b23b09bb25967b2c496ace9c0719a96a0
Implementation head SHA: 617bc725cdc34519ab9d080e5da185065ffd4d91
Report publication commit: SELF

## Work and scope

Executed oap/orders/005-b-canonical-provenance-and-jobs.md (Status FINAL,
PR mode AMEND_EXISTING_PR, Decision: NONE, live authorization: NONE).
GitHub reconciled first: unique OPEN PR 7 (head
oap/005-artifact-schema-and-source-scopes, base main), remote head equal to
the prior 005-a report head bb7fd82a811fd63c63c4dd40e66ff45a706c1a16,
origin/main bd8e454b23b09bb25967b2c496ace9c0719a96a0 unchanged, no
auto-merge, zero review threads, local worktree containing exactly the
three expected round-start changes. The exact order, the accepted root
005-a review oap/reviews/005-a-review.json (SHA-256
2dd04434984cc3a92e31144a10a3d04c177b25b6894b2b362ba65341ede62c5e, matching
the order) and oap/active (exactly `005-b` + LF) were committed
byte-for-byte unchanged first:

- 44f63bd3ce140f2f4e0b9a1607fabebe505823f9 — strategic 005-b round-start
  bytes byte-for-byte unchanged
- 44f97a7bcbf93b367871f8bce38aa4099a8eda5d — the FIRST authorized LOCAL
  --no-ff merge of exactly
  3f2ec5768cc07c86c2f0ab663a4e4af23ecac406 (branch
  oap/parallel-005-provenance; implementation
  4c0b3519ebf242edac9462bf24ee5fccd87ce7b5, candidate report
  b84b4a6959a066561c012f5b5467255414775cf5dc0869a3607f1aaa3b965bcf in
  candidate history) preserving candidate order/report/implementation
  histories (no cherry-pick). Forecast against the actual round-start
  parent with `git merge-tree --write-tree`: clean, automatic tree
  f0009f29c7b84f56f93b4d68328a3b04a64a1d2a; the merged commit's tree
  equals that forecast exactly. Eight additive files
  (provenance_records.py, unit/integration tests, docs/parallel/
  provenance-records-api.md, PAR-005-PROVENANCE-A/B orders and reports),
  +1260/-0, no shared-code change.
- 930d1250d1561df79b48e2ccbdab226a91fb04f7 — the SECOND authorized LOCAL
  --no-ff merge of exactly
  798d92524dfcf4b24bc312712d21453f159b204a (branch
  oap/parallel-005-job-records; implementation
  7b6959ab65e517dd88edb4ce4569c14a813ba451, candidate report
  a13c1e275bf0fc566aa9f631c1991c40b1369aedda6f065159305784701abde7 in
  candidate history). Forecast clean: automatic tree
  6b5f8f0d4907e028f8f9aefc3a204c3167050e2f; merged tree equals the
  forecast exactly. Eight additive files (job_records.py, unit/
  integration tests, docs/parallel/job-records-api.md, PAR-005-JOBS-A/B
  orders and reports), +895/-0, no shared-code change.
  These local integrations are NOT GitHub PR/default-main merges.
- 617bc725cdc34519ab9d080e5da185065ffd4d91 — implementation head (this
  round's new work only).

Changed behavior/paths at the implementation head:

- tests/integration/test_canonical_records_journey.py — new; ONE actual
  combined store-to-record journey (two tests) composing the real 005-a
  OriginalStore with provenance_records and job_records.
- docs/data-model.md — new; focused canonical 005 record protocol
  (identities, code-point reconstruction, origins, labels/rights,
  neighbors, job/attempt DTO-versus-execution boundary, remaining 005
  scope).
- README.md, STATUS.md, docs/UNCERTAINTIES.md — summaries of the 005-b
  continuation on the open 005 PR.
- TESTING.md — new T12 entry for the combined journey.
- oap/governance/CONTEXT-BUDGET.md and MANIFEST.json — measured
  routine read set 42370 -> 44046 UTF-8 bytes (ceiling 50,000); TESTING.md
  and CONTEXT-BUDGET.md manifest hashes re-verified; model tokens stay
  UNMEASURED.
- No candidate source change was required: both accepted tips passed the
  combined journey as-is (no concrete record/scope defect demonstrated).
- No new dependency, no source/role/helper/prompt/architecture rewrite,
  no 006/PDF/tokenizer/chunk-algorithm/008 material, no GitHub PR or
  default-main merge.

## Acceptance evidence

1. Versioned bounded records roundtrip through safe JSON/JSONL-shaped
   admission: candidate unit suite test_provenance_records.py (13 tests)
   admits Chunk/Neighbors through admit_record from mappings and UTF-8
   bytes, roundtrips byte-identically, and rejects duplicate keys, lone
   surrogates, oversized/nested payloads and unknown kinds with the
   input-free "invalid record"; catalog binds logical document/revision,
   corpus, declared version (null stays null), canonical sorted labels,
   processing approval and separate redistribution rights, and refuses
   forged revision/blob/label identities. Distinct traceable identities
   are asserted in the journey: source revision fingerprints,
   extraction_id(definition) and policy_id(definition) differ per
   definition; no extractor execution is invented (definition strings are
   declarations; configuration digests in the job spec are explicit
   not-applicable fixture values).
2. Reconstruction uses start-inclusive/end-exclusive Unicode code-point
   offsets into exact unmodified block text: the journey reconstructs
   astral (U+1F600), combining mark (U+0301), CRLF and non-ASCII spans
   across multi-fragment chunks with explicit separators
   ("\n", "…", "\r\n") including a repeated original table-header block
   reference; asserted chunk texts equal the exact concatenations and
   text_sha256 (UTF-8) matches. Negatives in the journey and the merged
   candidate suite: boolean offsets (start=True), negative, out-of-range
   (end=15>14) and empty (start==end) spans, conflicting copied text,
   unknown block, wrong block text/hash, wrong dependency definition and
   tampered chunk hash are all refused; unknown block/revision and wrong
   dependency/checksum at the registry are refused; no normalization is
   applied (asserted literals contain the combining mark and CRLF).
   Empty-fragment handling is explicitly rejected by the candidate DTOs
   (min_length=1 on copied_text/separator text).
3. Origins stay distinct: Block.origin is native or visual_transcription
   (the latter requires page_ref + uncertainty; finite ordered geometry
   optional, never manufactured); Derived origin is context or
   interpretation (interpretation additionally requires page reference
   and uncertainty); the journey uses only supplied synthetic native
   records and a context derived record; no real extraction was performed
   (asserted in docs/data-model.md and the T12 note).
4. Labels are explicit canonical sorted sets with all-label semantics:
   the journey asserts scopes[0].labels == () (public classification)
   vs scopes[1].labels == ("confidential","internal"), distinct
   redistribution rights (allowed vs prohibited) over ONE shared blob;
   blocks/chunks inherit the whole revision classification (bind_chunk
   returns the Scope); bind_derived unions target/support labels and
   rejects support crossing the document boundary (t-b1) and the
   revision boundary (h-a2, same document/corpus/labels, different
   revision); reader_allows denies missing one required label, denies
   absent grants, narrows with Restrictions, and fails closed on the
   unknown (null) declared version even with corpus and all labels;
   processing and redistribution rights remain separate fields.
5. Deterministic job identities and immutable attempts: the journey
   builds JobSpec from real store revision fingerprints (shared blob
   under distinct revisions; job ID changes across documents, across
   input order, and roundtrips through serialize/admit); transitions
   PENDING -> CLAIMED -> RUNNING -> COMPLETE with a matching immutable
   Attempt (known-zero input_tokens, null output_tokens) and an
   asserted-only "verified" OutputRef; terminal without attempt is
   refused; UNKNOWN_COMPLETION preserves attempt/request correlation and
   has no retry path (PENDING and RETRYABLE_FAILED targets both refused);
   RETRYABLE_FAILED -> PENDING retains the prior attempt ID and a
   re-claim with the same ID is refused while a fresh ID is accepted.
   The merged candidate suite additionally covers the full transition
   matrix, owner consistency, output-only-assertion semantics
   (missing/unverified/verified), pending cancellation without
   fabricated attempts, strict UTF-8 byte admission and non-ASCII safe
   refusal.
6. One actual combined journey beyond separate constructors:
   tests/integration/test_canonical_records_journey.py runs the real
   store (two documents, shared bytes, distinct corpus/labels/rights,
   declared version "1" vs unknown, metadata-corrected third revision),
   verifies ONE blob file and exact byte load via read_original for all
   three revisions, builds the synthetic registry, performs the chunk/
   neighbor/derived/reader decisions above, and the job/attempt
   roundtrip/transition chain with real revision fingerprints. The prior
   005-a regressions (descriptor/path race, read bounds, atomic
   publication/retry, corruption refusal) remain in-tree and pass
   unchanged (tests/unit/test_source_admission.py,
   tests/integration/test_source_admission_composition.py,
   test_source_module_cli.py, test_source_installed_cli.py). The journey
   is assertions over supplied extraction/counts, not executed parsers,
   tokenizers or cache validation; unknown-version behavior stays
   fail-closed (no access widened).

Original 005 criteria reconciliation: the software record-validation and
pure scope/transition scope is complete on PR 7; whole-005 acceptance is
not delegated to this round and remains strategy review before any
protected merge (extraction 006, contextualization 010, embedding 007,
snapshots 008, serving/auth 014, revocation 017 are later ordered work).

## Verification

Local (implementation head 617bc725cdc34519ab9d080e5da185065ffd4d91):

- `uv run pytest tests/integration/test_canonical_records_journey.py -q`
  -> 2 passed (new combined journey).
- Focused combined set (both candidate unit suites, both candidate
  composition suites, the new journey, all four 005-a source unit/
  integration suites) -> 52 passed.
- `uv run pytest tests/unit -q` -> 588 passed (562 baseline + 13
  provenance + 13 job unit), exit 0, no F/E in progress output.
- `uv run pytest tests/integration -q` -> 354 passed (350 baseline + 1 + 1
  candidate compositions + 2 journey), exit 0, no F/E in progress output.
- Counts via collect-only (per order, not repeated full suites): 588 unit,
  354 integration; `python3 -m unittest discover -s tests/oap -v` -> Ran
  41 tests, OK.
- `uv run ruff check src tests/unit tests/integration` -> All checks
  passed; `python3 -m compileall -q oap tests` -> clean.
- `python3 oap/bin/check_state.py --repo-root .` -> exit 0, declared
  context 44046/50000, exact model tokens UNMEASURED, critical {}.
- CI (already observed at implementation head): run 43042968211, all five
  jobs SUCCESS (OAP tests Python 3.12/3.13/3.14; Product tests Python
  3.12/3.14 including lint, compileall, tests/unit, tests/integration,
  OAP checks, governance check, console help and doctor example). This
  report's own push/CI is NOT certified here; a separate post-
  publication receipt and strategic review record report-head facts.

Mock/live distinction: all fixtures are owned, synthetic and offline; no
network, keys, GPU, model downloads, real corpus, credentials, live
inference or extraction occurred. Live target/model/GPU/corpus
authorization: NONE. No secret, private path or source text was written
to Git or this report.

## Documentation impact

Added docs/data-model.md (focused canonical 005 record protocol: exact
source/extraction/policy/chunk/job identities, Unicode code-point and
separator reconstruction, native/transcription/interpretation origins,
complete-label scope/rights and same-source support, unknown-version
fail-closed, reciprocal neighbors, job/attempt DTO versus execution/cache
claims, remaining 005 boundaries). Candidate docs/parallel/
provenance-records-api.md and job-records-api.md arrived byte-identical
via the ordered merges. Updated README/STATUS/UNCERTAINTIES summaries,
TESTING T12, and the measured governance entries (routine 44046/50000;
MANIFEST hashes for TESTING.md and CONTEXT-BUDGET.md; model tokens
UNMEASURED). The existing qualification-testing detail remains verbatim
and linked; no checks were weakened.

## DHA and boundaries

Order declaration: Decision: NONE; no critical append was ordered or
performed; no consequential candidate is reported. Preserved: all
004/005-a code, tests, candidate order/report/implementation identities,
the thin installed source/parity routes, private config, unrelated
worktrees (candidate worktrees left untouched at their accepted tips) and
all strategic/parallel material. No merge performed: PR 7 remains OPEN
with no auto-merge; main bd8e454 unchanged; no tag/release/deploy; no
006 or next-work activation; no model/profile change (human-selected
Qwen3.8-27B/A100 preserved).

## Limitations and remaining work

- DTO COMPLETE/verified OutputRef is an assertion, not artifact, cache or
  exactly-once execution proof; claim ownership, output-first
  publication, bounded retry execution and reconciliation remain 010.
- Supplied extraction text and token counts are synthetic assertions; no
  extraction, tokenization, model, GPU, license or corpus qualification
  was run (all NOT RUN).
- No record persistence/CLI for provenance or jobs exists yet; the
  journey exercises in-memory composition over the real store.
- This report cannot certify its own future push/checks; strategy owns
  report-head CI, the independent whole-005 review, protected qualifying
  merge, main CI and resolution.
- No scope deviations, no failed or skipped required checks at the
  implementation head.
