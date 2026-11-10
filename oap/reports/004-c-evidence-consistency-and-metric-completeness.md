# OAP Coding Report — 004-c

Identifier: 004-c
Result: COMPLETE
Repository: ulfe-lmi/slaif-raggedized-helper
PR number: 6
Branch: oap/004-qualification-harness
Base branch: main
Implementation head SHA: b35e82026343725d441708d57a9d5863373d8508
Report publication commit: SELF

## Work and scope

Executed oap/orders/004-c-evidence-consistency-and-metric-completeness.md
(Status FINAL, Decision: NONE, live target authorization: NONE, PR mode
AMEND_EXISTING_PR, base commit 2bc320ff9e66c874f07da061218f2ff52e3420a9)
as the bounded correction on the existing numeric 004/PR 6, closing the
four independently reproduced findings from the final 004-b review on
the verified 004-b head a769265cb888271a9daf67dbe333025b4e423a6d
(whose immutable COMPLETE report-only SELF 693ef7a2cc49ca35ea7fd86939ccc2a104dbb22d
is preserved, not strategic acceptance). Round start reconciled against
GitHub: unique PR 6 OPEN, original branch, main base
2bc320ff9e66c874f07da061218f2ff52e3420a9, remote head 693ef7a. The
worktree carried exactly the strategic round-start bytes: oap/active
004-b -> 004-c (exactly `004-c\n`), the new
oap/orders/004-c-evidence-consistency-and-metric-completeness.md, the
final 004-b review oap/reviews/004-b-review.json (SHA-256
81f1fa1b4e8566bb5b7ab6a18ea0bef66f81f576dbaaa86516e6984b8c2f5fc4), and
the root-authored startup-governance restoration (oap/prompts/coding-
startup.txt the exact previously qualified 582-byte ordinary prompt
SHA-256 41afe88aa473905c6496b8179aa3e2b87a04a8b0c88662b3214481634d3f8464,
docs/AGENT-ROLE-SETUP.md SHA-256 7078a1e9fc39b9b07b5eb67d4614d82e98a1e9c66ff81ad1d80740172600bbf3,
docs/OAP-RUNBOOK.md SHA-256 9d5be6bf85112560d9600e37155b68755724c532cdb13e246986871ed1267b2d,
manifest activation SHA-256 2521c128a784c6c1064374a03595c328fc9e62873486e99b0fc0ef76db043007
re-verified byte-identical before commit). The sole control OK was
consumed by the sole external wrapper and was never reread or replayed
and no waiter was created. All strategic files were committed byte-for-
byte unchanged inside the single implementation commit
b35e82026343725d441708d57a9d5863373d8508 (18 files, +1168/-140) on
branch oap/004-qualification-harness from verified remote head 693ef7a.
No reset/clean/stash/force-push was used.

The four ordered corrections from oap/reviews/004-b-review.json:

- F01 cross-field evidence bindings (qualification/contracts.py):
  `validate_trial_evidence` now drives the analysis pure-recomputation
  from the ACTUAL transport-boundary call ledger
  (`transport_boundary.calls_by_kind`), never the analysis's own copy —
  an analysis call count that conflicts with the ledger is refused,
  while adapter cycles can differ legitimately and never replace
  actual transport attempts. The envelope additionally binds: the
  envelope backend equals the declared backend; every KNOWN per-sample
  backend fingerprint equals the observed per-trial backend binding
  (an absent binding stays null, never guessed); the evidence class and
  target type form the consistent provenance pair (MOCK iff
  synthetic-owned-fixture, CONFIGURED_UNVERIFIED iff unverified); the
  output-reservation total/per-sample equal the same declared
  `max_output_tokens_total`/`per_sample_output_tokens` budget, with the
  per-sample share the floor even share over the DECLARED scheduled
  sample count (`workload.samples`, never the shorter recorded prefix
  after an early stop); and the cache/input consistency counts equal
  the shared pure derivation
  `derive_cache_input_consistency_counts` from the actually recorded
  raw usage (new module-level helper; `runner.py`'s
  `_cache_input_consistency` now delegates to it — an unreported cache
  counter is uncounted, a known cache with unknown input is
  uncheckable, cache > input is contradictory, a known 0 is a fact; raw
  contradictory counters remain valid sample facts, the label lives in
  the accounting section). These checks prove INTERNAL consistency
  only — never that declared metadata is true, that a fingerprint
  proves deployed hardware/model identity, or that imported JSON was
  executed here.
- F02 metric completeness (qualification/contracts.py): the quartile
  block (`_QuartileBlock`, renamed validator
  `_check_quartile_completeness`) enforces `n==0` iff ALL quartiles
  null and `n>0` requiring EVERY quartile present, finite, non-negative
  and ordered `min <= p50 <= p95 <= max`; partial quartile sets with a
  positive count, bool/nonfinite/negative values and malformed ordering
  are refused. Full result validation still recomputes the
  deterministic nearest-rank summaries from the recorded eligible
  samples, preserving known-zero counts, missingness, failure exclusion
  and the warmup/measured separation.
- F03 decoded-Unicode admission (qualification/spec.py): a workload
  parent or suffix that decodes to an unpaired surrogate code point
  (U+D800..U+DFFF, e.g. from a JSON `\uD800` escape) is refused at spec
  admission with a fixed safe reason BEFORE fingerprinting or request
  construction — typed exit 2, always zero HTTP, no input echo, no
  traceback. Valid Unicode — including escaped astral surrogate pairs
  and non-Latin (Slovenian) text — is admitted unchanged; the refusal
  performs no replacement, no truncation, no global encoding change and
  no fingerprint-version change.
- F04 serializer/spent-ledger boundary (cli.py): the `qualification
  run` serialization boundary now enforces the canonical FULL strict
  result contract (`validate_trial_evidence`: strict shape plus the
  analysis pure-recomputation against the actual ledger) instead of a
  basic `TrialEvidence.model_validate`. A post-work rejection is an
  honest exit 3: the fixed safe structured error
  (`_post_work_contract_error`) is written to stdout AND stderr,
  carrying the ACTUAL valid spent-attempt ledger (the
  `TransportBoundarySection` re-validated against the strict ledger
  contract); when the ledger itself is missing or malformed its
  availability is marked honestly (`ledger_availability:
  unavailable` with a fixed note) — the attempted-call count is never
  assumed zero and formatting never crashes — and the invalid record is
  never exported as a valid result, inviting no blind replay. The
  ordinary valid complete document (full ledger on stdout), the
  genuine late-write export failure behavior and all exit-code
  distinctions are preserved.

## Acceptance evidence

Criterion 1 (result validator binds actual call facts): the
recomputation input is `transport_boundary.calls_by_kind`. Unit tests
`TestCrossFieldBindings::test_analysis_call_count_conflicts_with_actual_ledger_refused`
(both drift directions) and the retained
/tmp/raggedized004-evidence-binding-review.py prove it on ACTUAL owned
HTTP evidence: `analysis_call_count_conflicts_with_transport` is
refused while `unaltered_evidence_positive` is admitted and
`actual_owned_http_positive` exits 0 complete with exactly one POST.
Criterion 2 (backend/fingerprint bindings): the witness cases
`envelope_backend_conflicts_with_declared_backend`,
`sample_backend_fp_conflicts_with_observed_binding` are refused; the
unit test `test_null_sample_backend_fp_stays_allowed` preserves the
actual null/unavailable semantics. Criterion 3 (reservation metadata):
`output_reservation_conflicts_with_budget` is refused by the witness;
unit tests `test_output_reservation_conflicts_with_budget_refused` and
`test_per_sample_must_be_even_share_of_declared_count` (a share
computed from the shorter recorded prefix is refused; the declared-
count share with the incomplete prefix is admitted) cover it; the
actual positive keeps `total=32, per_sample=16` consistent with the
declared 2-sample budget. Criterion 4 (provenance pairs + cache
derivation): `target_type_conflicts_with_unverified_evidence_class` is
refused; both valid pairs are unit-tested
(`test_configured_unverified_pair_is_the_other_valid_pair`);
`cache_consistency_claim_without_reported_cache` is refused;
`TestCacheDerivation` and `test_cache_consistency_counts_derived_from_recorded_usage`
cover unreported/known-zero/uncheckable/contradictory/consistent over
recorded raw usage. Criterion 5 (metric DTOs): the witness case
`stage_positive_count_partial_missing_quartile` (previously admitted)
is now refused; `TestQuartileCompleteness` covers partial quartiles
per field, malformed ordering, nonfinite/negative values,
bool-as-count, n=0-with-present-quartile, with the n=2 full and n=0
all-null positives preserved; full result validation still recomputes
deterministic summaries (unchanged `stage-analysis` witness:
hand-computed checks PASS, warmup separation, failure exclusion,
known-zero/missing distinct, empty metrics null). Criterion 6
(meaningful tests, preserved behavior, CI/lint/governance): 39 new
unit tests (314 unit total = 615 product with the unchanged 301
integration; 41 OAP scaffold; zero tests removed); the unaltered
actual owned-HTTP positive and every retained single-field
contradiction, unknown/zero/contradictory usage control, incomplete-
prefix/reservation case, malformed partial quartile and existing strict
/shaped input refusal are unit-tested; the actual valid gateway/
direct/HTTP/retry/deadian/operator-cancel/export behavior is
preserved by the unchanged integration suite and the retained
`runner-http`/`cli-spec-input`/`stage-analysis` witnesses; a genuine
post-work validation/export error retains the actual spent ledger and
cannot become a zero-dispatch usage refusal (witness below). Final-
head CI, product, OAP and lint evidence in Verification. Criterion 7
(Unicode admission): the retained matched-fingerprint witnesses
(/tmp/raggedized004-unicode-matched-fingerprint-review.py,
/tmp/raggedized004-unicode-privacy-review.py) now show the lone-high-
surrogate parent and lone-low-surrogate first suffix refused at PLAN
and RUN with typed exit 2 (`SPEC_INVALID`), zero POSTs, no traceback,
and the owned source canary ABSENT from stderr (the pre-fix run
leaked it with a raw Pydantic `string_unicode` ValidationError and
exit 1); the valid Unicode controls (emoji, escaped astral pairs,
Slovenian text) exit 0 unchanged with matched fingerprints; unit tests
`TestSpecUnicodeAdmission` cover both refusal fields, the fixed safe
message with no input echo (via `safe_validation_errors`), the matched
fingerprint fixtures and the no-replacement/no-truncation property.
Criterion 8 (canonical full validator + spent ledger): the retained
/tmp/raggedized004-cli-validation-boundary-review.py (owned real 2-POST
work) now shows `actual_work_then_none` exit 0 complete with the full
spent ledger on stdout; `actual_work_then_version` exit 3 with the
ACTUAL ledger preserved on stdout (pre-fix: exit 3 with stdout EMPTY
and the ledger lost) and `EVIDENCE_CONTRACT_VIOLATION` on stderr;
`actual_work_then_analysis_p50` (within-range forged p50) exit 3 with
the ledger and `forged_analysis_exported: false` (pre-fix: exit 0 with
the altered analysis exported). The ledger-availability supplement
(/tmp/raggedized004-cli-ledger-availability-review.py) covers
ledger-none/missing/bad/unknown/negative/bool attempts: each exits 3
with the fixed safe error, `ledger_availability: unavailable`, no raw
exception, no false zero-call claim and no forged export. Criterion 9
(documentation): the enforced cross-field invariants, the
metadata reservation-versus-spending semantics, the known/unknown
fields, the malformed-evidence refusal and the remaining
qualification/prerequisite status are documented (see
Documentation impact); no overclaim of consistency remains — the
internal-consistency-only limitation is explicit.

## Verification

Local, on the implementation commit (Python 3.14.4 venv; synthetic and
offline only, owned disposable 127.0.0.1 fixtures, zero network/keys/
GPU/model access):

- `ruff check .` — clean.
- `pytest tests/unit` — 314 passed (275 at 004-b + 39 new 004-c unit
  tests; zero removed); `pytest tests/integration` — 301 passed
  (unchanged 004-a/b positives, including the installed-CLI owned-
  loopback composition, transport/budget/retry/native-template/
  UNKNOWN-outcome, credential and export cases); `pytest tests/oap` —
  41 passed (governance scaffold, including verify_governance over the
  refreshed manifest).
- Retained root witnesses re-run with output inspected (not only
  exit 0): evidence-binding (six single-field contradictions refused,
  unaltered admitted, actual owned-HTTP positive exit 0, one POST);
  evidence-contract (partial quartile refused; all strict/shape and
  known-zero/unknown positives preserved); stage-analysis (hand-
  computed checks PASS, warmup/measured separation, failure exclusion,
  known-zero/missing distinct, empty-metric nulls); cli-spec-input
  (invalid UTF-8/JSON/oversize-integer/FIFO typed exit 2, bounded
  return, no traceback); unicode-matched-fingerprint and
  unicode-privacy (lone high/low surrogates: plan+run typed exit 2,
  zero HTTP, no traceback, canary absent; valid Unicode exit 0);
  cli-validation-boundary (none: exit 0 full ledger; version: exit 3
  ledger preserved; forged p50: exit 3 not exported); runner-http
  (shared allowance, retry consumption, deadline, accepted-then-
  closed unknown, preflight zero-HTTP positives preserved). The
  earlier /tmp/raggedized004-unicode-spec-review.py badcases had a
  mismatched fingerprint and proved fingerprint refusal only, as the
  order notes; the matched-fingerprint and privacy supplements are the
  operative Unicode witnesses.
- `python3 oap/bin/check_state.py --repo-root .` — exit 0: state
  ACTIVE, active 004-c, order resolved, report absent pre-publication,
  governance verified (manifest file hashes in sync after the
  authorized refresh; activation-vs-current-governance reported
  informational only).
- Implementation-head CI (push b35e82026343725d441708d57a9d5863373d8508
  to origin/oap/004-qualification-harness, 693ef7a..b35e820): CI run
  42853699111 all five jobs SUCCESS (OAP tests 3.12/3.13/3.14; Product
  tests 3.12/3.14), observed after push before this report was written.
- Mock/live distinction: every executed path above is synthetic/offline
  or owned disposable loopback fixtures; live target authorization is
  NONE; ALL real qualification trials remain NOT_RUN; no live
  target/model/GPU/corpus work was performed.
- No claim is made about this report's future push/CI; a separate
  post-publication receipt verifies it.

## Documentation impact

- docs/benchmarks/qualification-protocol.md: the evidence-contract
  section is now 004-b/004-c with the actual enforced bindings (actual-
  ledger-driven recomputation; envelope/declared/sample backend and
  fingerprint bindings; provenance pairs; declared-budget reservation
  and floor even share over the declared sample count; pure cache/
  input derivation), the quartile-completeness contract, the decoded-
  Unicode admission bullet in the bounded spec file input section, the
  canonical-FULL serialization boundary with the spent-ledger
  semantics, the explicit internal-consistency-only limitation, the
  004-c replan paragraph and the refreshed Tests section.
- TESTING.md T08: the 004-c coverage (Unicode admission, cross-field
  bindings, quartile completeness, serialization-boundary ledger) and
  the 004-b/004-c live-authorization NONE statement.
- STATUS.md: current-state line and the 004-c history block with the
  four corrections, preserved positives and the startup-governance
  restoration record.
- docs/UNCERTAINTIES.md: the 004-c observation (U01-U09 unchanged in
  kind with the internal-consistency-only bound; U05 strengthened in
  bound; U10 stays OPEN with the failed goal-first qualification kept
  as RECORDED FAILED history).
- README.md: the PR #6 summary now names the 004-b/004-c corrections
  (cross-field bindings, quartile-complete metrics, decoded-Unicode
  admission, canonical-full serialization with the spent ledger).
- oap/governance/CONTEXT-BUDGET.md + oap/governance/MANIFEST.json:
  routine governance refreshed from the final actual files (TESTING.md
  9607 -> 11018 UTF-8 bytes; total 42158 -> 43569, ceiling 50000;
  manifest file hashes updated for TESTING.md and CONTEXT-BUDGET.md;
  the restored prompt entry preserved). Exact model tokens and client
  injection remain UNMEASURED.
- The root-authored startup docs (docs/AGENT-ROLE-SETUP.md,
  docs/OAP-RUNBOOK.md) and prompt (oap/prompts/coding-startup.txt) are
  committed byte-unchanged as ordered; the failed goal-first
  qualification is never relabeled passed, and real restored
  wrapper/role/order/post-start-goal qualification is strategy's on
  this handoff, never inferred from file hash.

## DHA and boundaries

Decision: NONE — no CRITICAL append was ordered or made; the register
is unchanged (critical state empty per check_state). No merge was
performed, no auto-merge enabled, no release/tag/deploy, no next-work
selection, no model/provider/profile change, no nested/helper agents,
no new consumer or waiter. Preserved: the immutable 004-a/004-b
reports and orders, the final 004-b review (byte-unchanged), the three
root-authored startup-governance bytes (SHA-256 verified before commit),
agent homes, private FIFOs, source originals and unrelated worktrees.
No live target/model/GPU/corpus work (live authorization NONE); no
secrets, real corpus/prompts, private URLs or credentials in any commit
or this report.

## Limitations and remaining work

- These corrections prove INTERNAL consistency of evidence documents;
  they do not turn imported/operator-supplied labels or consistent
  metadata into trusted local execution or qualification evidence, do
  not prove deployed hardware/model identity from fingerprints, and do
  not authorize or imply any unapproved probe.
- No live qualification: real gateway/GPU/model/corpus inputs remain
  absent (authorization NONE); ALL real trials remain NOT_RUN;
  019/ICA/MVP gate actual A1/hardware/quality feasibility.
- Resource telemetry, vector/rank parity and full named gate
  composition remain required in later proof-sized 004 continuations
  (strategic activation required) before any whole-004 acceptance;
  this correction alone is not whole-004 acceptance, and no
  merge/005 authority is claimed. LICENSE-01 (certifi MPL-2.0
  exception) remains open.
- The 004-a /goal-first startup qualification remains RECORDED FAILED
  history; the restored ordinary startup is operationally qualified by
  strategy on this actual handoff, never from hash; U10 stays OPEN.
- Exact model token counts and client injection overhead remain
  UNMEASURED.
