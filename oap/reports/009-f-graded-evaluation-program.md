# OAP Coding Report — 009-f

Identifier: 009-f
Result: PARTIAL
Repository: ulfe-lmi/slaif-raggedized-helper
PR number: 11
Branch: oap/009-evaluation-baseline
Base branch: main
Round base commit: 9ba33cd7939634f31ebba25fe8c8b638ade51d81
PR main base: 5a7b41cc512cf883b5b2cb92d87554b4d24e685b
Transcript commit: 756ab32e2ead372547dddd96adb4d04872999704
Source SELF (graded proof): f4d9dbb2427c88d6d286475e25b378c7fcf57f0d
Source SELF (core): 45bcb729025e2015e306bc883bdbf008a05f31ec
Source SELF (program proof): e3bf5b84c04f5dbd2256a37a5a30be491b8f06a6
Component index SHA256: 1ff91482e22fa0a7ac931da2f65c469c463fa572ebc9b8dad27022456b95cd6b
Root index SHA256: 57a170a233c7ff047bdbb2bf6c3f9f01e864bdf5b2b21c5d27288d04804cde2c
Implementation head SHA: 926bba696e0eda3677166671fd1fd56acfe725aa
Report publication commit: SELF

## Work and scope

Order 009-f (FINAL, AMEND_EXISTING_PR) on PR 11 at round base 9ba33cd (009-e report head; hosted CI 43455291739 all five jobs / all 78 steps SUCCESS): static byte-exact transfer of SEVENTEEN reviewed component blobs (230,430 B) plus three current docs; PARTIAL whole 009. Transcript 756ab32e (sole parent 9ba33cd): 11 paths — unchanged FINAL order, active 009-f+LF (6 B), eight exact Root records (22,831 B incl. components index) and the exact 2,590 B Root index. Implementation 926bba69 (sole parent 756ab32e): exactly 20 paths — 16 NEW blobs (five graded-proof, seven core, five program-proof) and the exact source_cohort_runner.py shared-loop replacement (preimage b69589c3), copied by immutable source Git object per oap/reviews/009-f-components.json, plus only docs/evaluation.md, docs/benchmarks/raw-baseline.md and STATUS.md. This report commit changes only this report; one final report-head push follows; no reset/clean/stash/rebase/force-push, no cherry-pick/merge of parallel history.

## Acceptance evidence

1. Reconciled: unique open non-draft PR 11 (head 9ba33cd, base main 5a7b41cc); local at exact base with only the two published activation paths dirty; both frozen indexes hash-verified; three-commit ancestry verified. Exactly 32 round paths (31 excluding this report): 11 + 20. All eight Root records verified by size + SHA-256 and parse as JSON; all 17 blobs verified against immutable source Git objects (blob ID + size + SHA-256) and at implementation head; 16 NEW absent at base, MODIFY preimage exact. Copied Python (5) AST-parsed, JSON (6) parsed without importing or executing product.
2. Docs describe the TWELVE private module families and evaluation_program.run_evaluation with the exact source contract/API/binding: all-case plan/judgment/cutoff/grade-budget admission before source work, per-case grade-owned pin bracketing the judged-ID binding under effective authority (original at the source binder), one extra catalog load, full source universe, exact graded applicability (both exact declared policies, chunk-ID unit, 13 GradeBudget ceilings, 13 failure phases) and the three variant aggregates only after all cases succeed (zero direct score queries). Legacy source-only identity bytes preserved (three pre-implementation legacy goldens); no surviving-subset report; no policy from caller fields, no model qualification from supplied diagnostic vectors.
3. docs/evaluation.md source-cohort Budget corrected 22→20 fields (precision repair, verified against both old and new runner dataclasses); source versus graded budgets, private identities, explicit relevance mapping and grade eligibility distinguished; exact undefined partitions kept.
4. Three source-lane evidence families attributed separately, not rerun. Core: 98 controlled units (54 existing + 44 new), three controlled legacy goldens, full-256 moderate synthetic check — controlled delegates/pure metrics, not source/model execution. Existing graded proof: ONE actual two-query synthetic process — 2 producer / 3 stage binder / 5 judged-ID grounding / 6 direct score / 3 aggregate, four real refusals; one generator exit 0, six wrappers reaped 143. Genuine program proof: exactly one whole-module v3 test node — full 5-case/7-Gold/3-bundle universe, h1/h4; direct totals owner 19 / producer 6 / binder 6 / source aggregate 2 / pre-catalog 2 / grade binder 4 / rank aggregate 3 / direct score 0; exact legacy source-only output equivalence; bool preflight 0, later ineligible b:0 GRADE_BIND 2/2/1/1/0, closed pin CATALOG 2/0/0/0/2; six real wrappers closed/reaped 143; ZERO generators via one cached data-only fixture.
5. Retained failures and distinct-scope resources preserved in the docs: SELF+waited CHILDREN CPU delta 64.584229 s, observer wall 65.29573054192588 s, launcher child wall 65.777162 s, launcher waited-child CPU 65.039091 s; pytest SELF peak 94,252 KiB = 92.04296875 MiB, children max RSS 72,036 KiB (high waters, non-additive, not deltas/AS); per-process CPU 120/AS 2 GiB/wall 240/FSIZE 16 MiB not aggregate guarantees; initial broad read/lane-isolation FAIL (semantic 341,392 B > 262,144 B by 79,248 B) retained, later semantic total INCOMPLETE_NOT_CERTIFIED; V1/v2 launchers not actual runs.
6. Original 009 obligations explicit: raw representative baseline NOT RUN (approved human held-out data/rights/current principal-policy authority/qualified real encoder and real operator composition missing); private publisher and named plan/evaluate CLI unfinished; remaining 009 gates open; no plaintext/vector/credentials/private corpus/path/trace/hit content in Git or this report.
7. The single report-head push triggers the full unchanged hosted CI (Python 3.12/3.14 product/integration + three OAP jobs); at publication the new run is PENDING — no result certified, no old-run reuse; missing/skipped/pending/cancelled/failed is not green; Root independently reviews the exact new source/report/head/CI/threads before acceptance; the CI-312 orphan bwrap observation remains unresolved qualification, not a causal fix or veto.

## Verification

Static Git/read/hash/AST/JSON identity checks only (git fetch/rev-parse/cat-file/hash-object/diff/show, sha256sum, ast.parse, json.load, gh pr view). No local format/lint/test/collect/setup/native/store/scorer/model execution, no new environment/download, no runtime/GPU/credential/service/private-corpus access. Measured semantic readset ~205 KB (compact read set, exact order, both indexes, replan + public evidence, the transferred contract/API/binding/composition docs, evaluation_program.py excerpts, runner diff, three current docs, 009-e report, generated verification) — within the finite 512 KiB allowance. Default-collected proof tests retained without skip/xfail/filter changes (static mark scan: none).

## Documentation impact

docs/evaluation.md: twelfth family section (exact run_evaluation contract/API/binding, shared-loop semantics), provenance section, 20-field Budget repair, suite census 11→12, deadline list, final 009 status. docs/benchmarks/raw-baseline.md: 009-f provenance/state, NOT RUN unchanged. STATUS.md: current slice 009-f, round record, whole-009 state. No other docs.

## DHA and boundaries

Decision: NONE (no CRITICAL append; register untouched). Preserved: immutable prior reports/reviews, retained failure evidence, source worktrees (topology evidence only, not merged history), gateway/services, human Qwen3.8-27b/A100 Q8/xhigh model/profile/auth, other panes/worktrees. No merge/auto-merge/tag/release/deploy; PR 11 remains open; no nested agents; no FIFO reread/replay; no second consumer; no model/profile change.

## Limitations and remaining work

PARTIAL whole 009: tiny synthetic proofs are weaker than the required representative real baseline; the new head has no current CI until the pushed run completes. A qualified real baseline, the private publisher, the named plan/evaluate CLI and current-policy verification remain separate required work; no 009 closure or next numeric objective from this transfer. This report cannot certify its own push or future checks.
