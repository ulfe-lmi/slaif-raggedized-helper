# OAP Coding Report — 008-c

Identifier: 008-c
Result: PARTIAL
Repository: ulfe-lmi/slaif-raggedized-helper
PR number: 10
Branch: oap/008-raw-hybrid-snapshots
Base branch: main
Round base commit: d9ef6b4ce54fe32486baff70ce318bf4c08f1804
Transcript commit: f72405f779d1f1b6e13951a6742d909f0fc6073d
Implementation head SHA: c66dfe4917862ba24d3acf9a739cbb0a62367203
Report publication commit: SELF

## Work and scope

Order 008-c (FINAL, DHA NONE, AMEND_EXISTING_PR) amended PR 10 on exact
branch/base d9ef6b4c. Transcript f72405f7 (sole parent d9ef6b4c):
unchanged FINAL order, active 008-c+LF, NINE exact Root records
(37,297 B) + exact index (3,040 B 3afb969e…4dc27) per
oap/reviews/008-c-root-records.json — 12 paths, all bytes verified, no
Root bytes edited.
Implementation c66dfe49 (sole parent transcript): exactly 25 NEW blobs
(200,027 B) by Git-object read from reviewed local assembly SELF 4e428b17
per oap/reviews/008-c-publication-reader-components.json (441c130f…1355)
— five production raw_snapshot_* modules (publication, selection,
catalog, pin, file_builder), five unit and five integration suites, ten
docs/parallel contracts — plus ONLY docs/retrieval.md and STATUS.md
current 008-c paragraphs (no-caller wording corrected to no
CLI/application entrypoint; 008-b AST 11-vs-13 and terminal-008-b-CI
updates in current provenance; immutable reports preserved).
27 paths; 39 round paths excluding / 40 including this report; no
branch switch/cherry-pick; no local product tests; no merge.

## Acceptance evidence

1. Same unique PR 10/branch/base d9ef6b4c: report ← c66dfe49 ←
f72405f7 ← d9ef6b4c; round diff = 39 paths (12 + 25 + 2), none
unexpected; order/active bytes unchanged in both commits; no
reset/stash/clean/rebase/force-push/report amendment; main 1a8fddf8 and
other branches preserved.
2. Five-layer behavior preserved: FileBuilder fresh
membership/payload/manifest/file binding with declared query context;
publisher private immutable candidate, no-replace rename, fsync,
publication_may_exist uncertainty; selection exact expected-pointer
CAS with generation and selection_may_have_changed uncertainty;
catalog bounded fresh source/row/vector/term correspondence; pin held
data identity, target lock, creator-only cleanup, FD no-retry. DATA
validation/cooperation are not current auth, retention, unlink, ABA,
power-loss, hard-preemption or model-readiness proof; no cap raise or
silent truncation from 4,096/128/96 MiB (catalog 32 MiB non-vector)
toward 20k (NOTQUALIFIED).
3. Static exact-bytes / API fit / measured LF read set only: 25/25
SHA-256/byte equality (source SELF, worktree, commit tree); 15/15 AST
parse; 78/78 local import edges resolved (FileBuilder carries all
publication/selection test imports in this slice). No local
product/unit/integration/collection/app-import/native/store/scorer/
model/setup/diagnostic process ran; existing authorized directory-first
provider initialization retained; no path override or fake package; no
unexpected mismatch or failure.
4. docs/retrieval.md and STATUS.md describe the actual five APIs,
trust, error uncertainty, borrowed stores, private DATA versus rights
and lifetime, and the future query/scoring/operator interfaces; dated
historical evidence distinct from current CI (008-b terminal
43362986520 at d9ef6b4c; 008-c pending); 25 = 5 prod + 5 unit + 5
integration + 10 docs, 200,027 B exact; 008-b AST 11-vs-13
clarification preserved, old report unrewritten; README unchanged.
5. No CI workflow, skip, deselection, package, timeout or
continue-on-error change; one final-head push triggers the unchanged
normal five-job matrix (full unit + integration on Python 3.12/3.14
plus the three OAP jobs). Missing/skipped/cancelled/pending are not
green; at publication the 008-c report-head CI is PENDING; Root owns
post-response CI observation.
6. This report: immutable, under the 8,192 B hard limit, bare 40-char
implementation head + SELF, parser headers, Result PARTIAL whole 008,
exact counts, zero local tests, history limits, actual CI status, DHA
NONE; one final head push, strict remote verify, one original normal
response; no self-acceptance/merge/MVP claim.

## Verification

Commands/results: 25/25 SHA-256/byte equality (source 4e428b17,
worktree, commit c66dfe49; 200,027 B); 9 records 37,297 B + index
3,040 B 3afb969e… verified; ancestry/diff-tree 12+27 paths (39 round),
none unexpected; ast.parse 15/15; import read-set 78/78; gh pr view 10 — OPEN, main, branch
exact, MERGEABLE, no auto-merge; remote main 1a8fddf8 unchanged. This
report cannot certify its own future push or CI: at c66dfe49 the
report-head CI is PENDING; the 008-b head CI 43362986520 (5 jobs /
78 steps SUCCESS; both Product 3.12/3.14, 1,836 unit + 838
integration) is terminal for that head only.

## Documentation impact

docs/retrieval.md: 008-c provenance/API/evidence/trust/
remaining-scope paragraphs plus the two current-wording updates
(immutable reports preserved). STATUS.md: 008-b evidence update and
current 008-c entry. Ten new docs/parallel contracts byte-exact. No
routine context changed.

## DHA and boundaries

Decision: NONE; no CRITICAL entry. Preserved: unrelated files,
worktrees, Qwen/gateway services, GPU allocations, profiles, auth.
No merge performed; PR 10 remains open for Root observation.

## Limitations and remaining work

Zero local product tests this round: static Git/hash/AST/diff/
ancestry checks only. Historical local proof only: 008-a 49-unit/
source-row with the preserved 48-pass/1-fixture-import failure; 008-b
one bounded 7-row synthetic journey satisfying only the named
source-composition gate (details in the immutable 008-b report); 008-c
Root separate bounded fault proofs support
component admission; FileBuilder historical peer pre-run provenance
UNPROVEN, never backfilled; pin peer old-author RAYON-missing/
reconstructed-stdout limits retained separate from the Root fully
bounded FD-reuse proof. Not qualified: full corpus, physical atomicity,
current-policy behavior, neural/FP16 quality, 20k capacity
(NOTQUALIFIED), rights/license clearance, ICA, held-out quality, full
MVP. Remaining same-PR waves: completion-locator/construction
wrapper, dense/BM25/RRF/hybrid, query/operator/current-policy,
scoring, whole-008 criteria review. Report-head CI pending at
publication; Root owns post-response CI observation.
