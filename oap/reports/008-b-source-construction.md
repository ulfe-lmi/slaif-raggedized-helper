# OAP Coding Report — 008-b

Identifier: 008-b
Result: PARTIAL
Repository: ulfe-lmi/slaif-raggedized-helper
PR number: 10
Branch: oap/008-raw-hybrid-snapshots
Base branch: main
Round base commit: 0ef370696ea4a28e7153977df8c623e27fdad1e7
Transcript commit: ffdab9bf5d15f96a37a14e6ddf996708d4b09ccc
Implementation head SHA: e046203c3ae5158d00a28401dede483ac1f76d39
Report publication commit: SELF

## Work and scope

Order 008-b (FINAL, DHA NONE, AMEND_EXISTING_PR) amended PR 10 on exact
branch/base 0ef37069. Transcript ffdab9bf (sole parent 0ef37069):
unchanged FINAL order, active 008-b+LF, EIGHT exact Root records
(33,928 B) per oap/reviews/008-b-root-records.json (index 2,687 B
498551a8…) — 11 paths, all bytes verified, no Root bytes edited.
Implementation e046203c (sole parent transcript): exactly 21 NEW blobs
(145,034 B) by Git-object read from reviewed local assembly SELF 2da3d0df
(implementation 009044a) per oap/reviews/008-b-construction-components.json
(bb292ea9…ddf9) — four production modules (raw_snapshot_row_builder,
raw_snapshot_files, raw_snapshot_program_coverage, raw_snapshot_directory),
four unit and five integration suites, eight docs/parallel contracts — plus
ONLY docs/retrieval.md and STATUS.md (008-a count corrected to 25 = 5
production + 5 unit + 5 integration + 10 docs per Root reconciliation
oap/reviews/008-a-scoped-prefix-resolution.json; immutable 008-a report
unchanged; current 008-b API/evidence/limits paragraphs). 23 paths; no
branch switch/cherry-pick/merge; no local product tests; no merge.

## Acceptance evidence

1. Same unique PR 10/branch/base 0ef37069: report ← e046203c ← ffdab9bf
← 0ef37069; diff vs base = 34 paths (11 transcript + 21 transfer + 2 docs),
none unexpected; 21 commit-tree blobs and 8 records re-verified byte-exact;
order/active bytes unchanged in both commits; no reset/stash/clean/rebase/
force-push/report amendment; main 1a8fddf8 and other branches preserved.
2. Correspondence preserved: selected-batch row-map DATA, file-set
correspondence DATA, selected-program coverage DATA (4,096 rows / 128
batches / 128 sources) and private directory DATA reader, all with fresh
source-backed validation; 4,096-row/128-group limits are finite policies;
SUPPLIED_UNVERIFIED / NOT_QUALIFIED / COMPLETE_SELECTED_PROGRAM describe
the selected data cut only — no neural origin, current principal, rights,
precision or readiness attestation; existing source filters/withdrawal and
borrowed-store behavior unchanged; no new auth claim.
3. Static verification only: 21/21 index SHA-256/byte equality at source
SELF, worktree and commit tree; AST parse of all 11 new Python files; 41/41
local import edges resolve against the current canonical tree; no
sys.path/PYTHONPATH additions by coding. The two integration donors carry
the Root-approved existing-provider-import-only initialization (final
prepared blobs authoritative; no further import or path adaptation). No
local product/unit/integration/collection/native/store process ran; current
unchanged hosted CI supplies canonical behavior.
4. docs/retrieval.md and STATUS.md corrected to the actual 008-a count
(immutable report preserved with Root attribution) and describe the new
21 = 4 production + 4 unit + 5 integration + 8 docs, 145,034 B, the four
construction APIs, and the absent writer/publisher/FileBuilder/query/
operator/current-policy/serving; README and all earlier product/tests,
CI/pyproject/uv.lock, law/routine-context files byte-identical.
5. No CI workflow, skip, deselection, package, timeout or
continue-on-error change; one report-head push triggers the unchanged
normal five-job matrix (full unit + integration on Python 3.12 and 3.14
plus the three OAP jobs).

## Verification

Commands/results: Git-object read + SHA-256/byte comparison of all 21
index entries (source 2da3d0df, worktree, commit e046203c) — 21/21 exact,
145,034 B total; ancestry/diff-tree path checks — 11 + 23 paths, none
unexpected; python3 ast.parse over the 11 new Python files — all parse;
AST import read-set — 41/41 resolved; gh pr view 10 — OPEN, main, head
oap/008-raw-hybrid-snapshots, MERGEABLE, no auto-merge; remote main
1a8fddf8 unchanged. This report cannot certify its own future push or CI:
at implementation head e046203c the report-head CI is PENDING. The prior
0ef37069 CI 43358779227 (5 jobs / 78 steps SUCCESS; both normal Product
3.12/3.14 with 1805 unit + 815 integration) is historical for this head.

## Documentation impact

docs/retrieval.md: 008-a count corrected per Root reconciliation (report
preserved), 008-b provenance/API/evidence/trust/remaining-scope paragraphs.
STATUS.md: 008-a count corrected and current 008-b entry. Eight new
docs/parallel contracts transferred byte-exact. No routine context changed.

## DHA and boundaries

Decision: NONE; no CRITICAL entry. Preserved: all unrelated files,
worktrees, Qwen/gateway services, GPU allocations, profiles and auth.
No merge performed; PR 10 remains open for Root observation.

## Limitations and remaining work

Zero local product tests: historical local proof only (008-a 49-unit/
source-row with the preserved 48-pass/1-fixture-import failure; 008-b one
bounded 7-row/1-batch/1-partition/1-group synthetic journey — 2 native
processes, 0 generators, 29 bundle loads, 4.90 s wall — satisfying only
the named source-composition gate; historical correspondence receipt
thread-field gap and Root-authorized corrected 20-unit pass preserved;
leaf row-builder peer pre-run provenance UNPROVEN, never backfilled).
Not qualified: full corpus, physical atomicity, current-policy behavior,
neural/FP16 quality, 20k capacity (NOTQUALIFIED), rights/license
clearance, ICA, held-out quality, full MVP. Remaining same-PR waves:
FileBuilder/publication/selection/pinning, dense/BM25/RRF/hybrid,
query/operator/current-policy, scoring, whole-008 criteria review.
Report-head CI pending at publication; Root owns post-response CI
observation.
