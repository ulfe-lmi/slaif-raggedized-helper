# OAP Coding Report — 008-e

Identifier: 008-e
Result: PARTIAL
Repository: ulfe-lmi/slaif-raggedized-helper
PR number: 10
Branch: oap/008-raw-hybrid-snapshots
Base branch: main
Round base commit: c3e36dae37966958cf30d8f6bb5df221a26f0d14
Transcript commit: 5911cbdd3651a4998406821bf5fe1093bf13a1ed
Implementation head SHA: 291321f170592e90fdad9918e4d8176e608583b0
Report publication commit: SELF

## Work and scope

Order 008-e (FINAL, DHA NONE, AMEND_EXISTING_PR) plus the exact Root
D0 portability addendum amended PR 10 at exact branch/base
c3e36dae. Transcript 5911cbdd (sole parent c3e36dae): unchanged
FINAL order, active 008-e+LF, NINE exact Root records (29,999 B) +
exact index (3,081 B 5a99e1c4…035d5) and the unchanged
addendum (4,181 B c39388bc…87690) — 13 paths, all hashes/sizes
verified before commit, no Root bytes edited. Implementation 291321f1 (sole
parent transcript): exactly 40 paths — the 37 indexed blobs
from donor SELF b289e8d9 (index 44e5bcd2…069b; 451,715 B; 35 new +
2 metadata: 4 production, 7 unit, 7 integration, 17 docs,
pyproject.toml + uv.lock) — with the single addendum-ordered
adaptation in
tests/integration/test_raw_hybrid_trace_composition.py (final
11,420 B 3759df10…acb7057; donor 11,951 B): trace_owned calls the
inherited test_native_tokenizers.make_native(tmp_path) exactly once
before the subprocess.Popen guard installs, retains and verifies
the two pinned artifact hashes, drops the hard-coded private
witness cache, manual paths, redundant runtime/definition
recreation and now-unused os import, and keeps monkeypatching
make_native to the same owned paths/runtime/definition so the
inherited builder regenerates nothing; both tests and all scorer/
native/source/policy/count assertions, caps and causal controls
byte-unchanged — plus ONLY docs/retrieval.md, STATUS.md and
docs/ci-proc-observation.md. The other 36 indexed files are
byte-identical to the donor. 54 unique round paths including this
report / 53 excluding; no other old test/product/config/law/
profile/report/workflow change; no merge.

## Acceptance evidence

1. Exact PR 10/branch/base; report ← 291321f1 ← 5911cbdd ←
c3e36dae. Round diff vs base: 13 transcript + 40 implementation =
53 (+ own report = 54), none unexpected; order/active bytes
unchanged, byte-identical to worktree; no reset/stash/clean/
rebase/force-push/old-report rewrite. All 37 sizes/hashes equal
the final Root index and prepared Git objects (verified at copy);
only the three current docs add further changes; the adapted test
is the single authorized deviation.
2. Behavior preserved by exact bytes of the four reviewed modules:
scope filtering before candidates/index/scoring, normalized 1024-D
CPU vectors, pinned Lucene BM25/technical analyzer, deterministic
per-partition/global caps, RRF 60 without raw-score addition,
fail-closed source/catalog/map/model/deletion/ACL binding; trace
defaults (trace=False, nested None) and fixed markers
(SUPPLIED_UNVERIFIED, NOT_QUALIFIED, SUPPLIED_SCOPE_CHECKS_ONLY,
NOT_ATTESTED) are supplied metadata, not authentication or neural
provenance. Pinned-hash premise: witness a.json/b.json
(1432b17a…ee32 / 36583090…66153) match exactly and CI provisions
the same hash-verified tokenizers 0.21.4 capsule via the
unchanged prepare_native_test_backend.py.
3. Dependencies change only to the indexed pyproject/lock bytes:
bm25s==0.2.14 + scipy==1.18.1 added (lock diff additions-only; no
old package record removed or changed; no lock regeneration). No
setup, network or license exception; Audit/SBOM/model/runtime/
heldout/20k/security/ICA gates remain open.
4. Static Git/hash/AST/metadata only: 18/18 new Python files
parse; production imports stdlib + numpy/bm25s/scipy. NO local
product/unit/integration/collection/pytest/interpreter/package
probe, setup, model, native, store or scorer process, no
environment dump. Unchanged hosted CI alone supplies new-head
behavior; no skip/deselection/cap/timeout/workflow change.
5. Current retrieval/STATUS describe the four private APIs, trace
fields/defaults, declared query-execution binding, supplied
authority limits and remaining constructor/pinned-query/current-
service gates. The CI note separates the five-case inner-capped
success from the reset/check-cat/uncapped-metadata harness limits,
forbids that harness's reuse, scopes old kill-dispatch wording as
inference, states 9 paths excluding / 10 including the old 008-d
report, records c3e3 terminal CI (run 43370945412, all 5 jobs /
78 steps, 1,864 unit + 894 integration both legs); immutable old
reports and the failed 3.14 CI stay preserved; nothing implies
one-shot attestation was repaired or old 3.14 CI passed.
6. This one report-head push triggers the unchanged normal 5-job
matrix / all steps / full unit+integration on BOTH 3.12/3.14;
missing/pending/skipped/cancelled/failed are not green. Root
observes after the one normal response; coding then idles. No
future-pass claim, no self-acceptance, no next scope, no merge.

## Verification

Static only: 13 transcript paths and 37 blobs
re-hash verified against the exact Root indexes before each
commit; adapted-test diff vs donor limited to the addendum lines;
18/18 AST parse; dependency diffs additions-only. No local
runtime evidence exists this round. This report cannot certify
its own
future push or CI: at publication the 008-e report-head CI is
PENDING; the old 322c 3.14 failure (run 43368073059) and all
private records remain preserved. Root will independently compare
the adapted test to the donor and review all new-head checks.

## Documentation impact

docs/retrieval.md: title + new 008-e scoring-layer section (four
private APIs, trace defaults/markers, query-execution binding,
supplied authority, remaining gates) + remaining-scope/
dependency corrections. STATUS.md: 008-d current correction
(harness limits, one-shot UNPROVEN, 9/10 path count, old 3.14
failure preserved) + new 008-e entry. docs/ci-proc-
observation.md: kill-dispatch inference scope, harness-limits/
attestation section, 008-e portability section, c3e3 terminal +
008-e pending CI. No other doc, source, law or report changed.

## DHA and boundaries

Decision: NONE; no CRITICAL entry. Preserved: unrelated files and
worktrees, human Qwen3.8-27B/A100Q8 profile/auth, other panes,
branches, prior immutable orders/reports/records, private witness
cache (historical evidence only). No service/GPU/credential/
corpus/model action, no public exposure, live authorization NONE.
No merge performed; PR 10 open for Root observation; no
tag/deploy/release; no FIFO reread/replay, no duplicate consumer,
no nested agents.

## Limitations and remaining work

Whole 008 remains PARTIAL: construction/query join and the
original 008 criteria review are outstanding; no public
authentication, serving or model qualification is implied. The
adapted fixture has not been executed locally or on CI yet; the
pinned-hash premise rests on the exactly matching witness
artifacts plus the unchanged hash-pinned CI capsule, to be
confirmed by Root's new-head CI observation. No local tests,
imports, collection or runtime ran this round; no measured
performance, license clearance or readiness claimed.
