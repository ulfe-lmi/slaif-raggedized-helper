# OAP Coding Report — 008-a

Identifier: 008-a
Result: PARTIAL
Repository: ulfe-lmi/slaif-raggedized-helper
PR number: 10
Branch: oap/008-raw-hybrid-snapshots
Base branch: main
Round base commit: 1a8fddf8c1448ad9e76b6b8194984877c4c21a95
PR main base: 1a8fddf8c1448ad9e76b6b8194984877c4c21a95
Transcript commit: f9806f314b3db45353a2b12500ee99f37db97385
Implementation head SHA: a4887071a7921668c43eca9265623539627e7cbb
Report publication commit: SELF

## Work and scope

Order 008-a (FINAL, DHA NONE, CREATE_NEW_PR) ran transcript-first from exact
verified main 1a8fddf8 (PR #9 accepted merge). Transcript f9806f3 (sole parent
1a8fddf8): unchanged FINAL order (11,500 B), active 008-a+LF, NINE exact Root
records (52,370 B) per oap/reviews/008-a-root-records.json plus the exact
index (2,203 B 7a1ea7d6…); all bytes verified, no Root bytes edited.
Implementation a488707 (sole parent transcript): exactly 25 NEW blobs
(142,322 B) transferred by Git-object read from reviewed local assembly SELF
96822ff4 (implementation 3eac764) per
oap/reviews/008-a-foundation-components.json (e11bfb74…0633) — five
production modules (technical_analyzer, raw_snapshot_membership,
raw_snapshot_source_rows, raw_snapshot_dense, raw_snapshot_lexical), twenty
test files, ten docs/parallel contracts — plus ONLY new docs/retrieval.md and
concise README/STATUS paragraphs. No branch switch/cherry-pick/merge of the
candidate; no local product tests; no merge.

## Acceptance evidence

1. One new 008 branch/PR 10 on exact accepted main: report ← a488707 ←
f9806f3 ← 1a8fddf8; diff vs main = 40 paths (12 transcript + 25 transfer +
3 docs), none unexpected; 25 implementation-tree blobs and 9 records
re-verified byte-exact; no reset/stash/clean/rebase/force-push/report
amendment; 007 reports/records unchanged.
2. Foundation source retains strict token preservation, canonical codecs,
normalized finite read-only FP32 storage, whole-batch membership and bounded
4,096-row/128-group limits; 20k capacity NOTQUALIFIED; no supplied DTO/hash
becomes neural origin, current principal or readiness proof.
3. Static-only verification: full byte/JSON/AST/diff checks and current
transitive call sites against main (all relative imports, attributes and
RowMap/Row fields resolve in unchanged canonical modules); all five modules
and all 25 assembly files exact per index. Prior exact-source 49-unit and
source-row journey plus current unchanged normal CI supply behavior/negative
evidence. No local product/unit/integration/native/store execution, no app
imports/env dumps; no new dependencies (stdlib plus already-locked NumPy).
4. Unchanged hosted CI: the one report-head push triggers full unit and
integration suites in BOTH Product 3.12/3.14 plus 3 OAP jobs; no
skips/deselection/overrides/fake modules; CI PENDING at publication; Root
independently reviews terminal final-head checks.
5. docs/retrieval.md maps actual callable foundation APIs versus absent
writer/reader/query/current-policy/quality interfaces, byte-transfer
provenance, inherited test-only fixture exception (explicit importlib load of
the real existing structured-text fixture; no sys.path/sys.modules override),
historical versus current evidence, trust DATA boundaries and remaining 008
waves (correspondence/directory, publication/catalog/pinning,
dense/BM25/RRF, query/current-policy integration, final review).
6. Report within 8,192 B with bare literal 40-hex implementation ID and SELF;
one final-head push; strict remote verification and ONE original response
belong to the separate post-publication receipt, not this report.

## Verification

Mock/live: zero local product processes this round; no new mock/live
evidence. Historical exact-source evidence (49-unit plus source-row
synthetic native journey; preserved original 48-pass/1-fixture-import
failure) is an input, never current proof. Current report-head CI:
PENDING/UNOBSERVED at publication; future checks are not attested here.

## Documentation impact

ONLY new docs/retrieval.md and concise README/STATUS paragraphs. No
TESTING/ARCHITECTURE/CRITICAL/law/governance/CI/pyproject/uv.lock/profile
edit; canonical manifest/row-map/corpus-program/representation modules,
rights distinction and original-source evidence obligations unchanged; new
direct/transitive dependencies NONE; 018 license/SBOM/release qualification
remains open.

## DHA and boundaries

Order Decision: NONE; no CRIT append; no candidate. Preserved: human
Qwen3.8-27b/A100Q8 profile/auth, parallel raw-foundation worktree (read-only
object access), prior immutable orders/reports/records. No merge performed —
PR 10 remains OPEN, auto-merge off; no tag/deploy/release, no FIFO
read/replay, no new reader, no next suffix, no nested agents.

## Limitations and remaining work

Whole-008 acceptance open: current report-head CI terminal state, Root
review and later strategically activated same-PR continuations
(publication/reader/query/authorization contract). Historical row/file-
builder peer-provenance limitations stay open until scoped current evidence.
EMBED01/02, FP16, current rights, controller/hardware/quality/license/ICA/
fulltext+visual MVP gates remain NOT RUN/UNPROVEN; no complete-008/MVP/
service claim.
