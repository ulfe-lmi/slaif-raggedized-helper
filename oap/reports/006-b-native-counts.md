# OAP Coding Report — 006-b

Identifier: 006-b
Result: COMPLETE
Repository: ulfe-lmi/slaif-raggedized-helper
PR number: 8
Branch: oap/006-native-extraction-and-chunking
Base branch: main
Base commit: 6b087d3a58d1f96faf130f086556706fec297de1
Implementation head SHA: c2d589c23dab73b6f34bb75ee588db179b1efbb7
Report publication commit: SELF

## Work and scope

Order oap/orders/006-b-native-counts.md (Status FINAL, Decision NONE) on
the accepted 006-a extraction slice (PR 8 head 6b087d3; main 4977186).
Round-start reconciliation: PR 8 OPEN, head
6b087d3a58d1f96faf130f086556706fec297de1, base main, no auto-merge, zero
review threads; origin/main == 4977186d3ddbd2259f78590b29c0364fe26eb1fb.
Commits pushed before this report:

- d30898f7817d2e5890de886d255c8bcf94cf479b (round start): strategic
  bytes byte-for-byte unchanged — active "006-b\n", order 006-b
  (SHA256 dfdd9bc9993bfcfe3f1677ba95020226d4e9a47bd72cf6f4aa65f10ca021c22a)
  and oap/reviews/006-a-review.json (SHA256
  9ae5bbc3979b8b5b269437845fa365b1c1a474a4cf40c64533062506d8e214ef)
  copied unchanged into the tree.
- b86f42e951eefe38f5d31132a6a04f5ed98ffe30: local --no-ff merge of the
  accepted native bridge B candidate tip
  1a9e6387f4ba2134894f81c6827c78d78d462843 (implementation
  40d7d867629c43e42aaf06ac56d9c58a509af6e1, report SHA
  486e4a4d71f2a6798ac9edaa023ec35b4a233e6d5ec926ea8009fda5769fb453).
  The order's preliminary first forecast (df9ca714c0e871fc41a36e5e7753db89bc5b731d,
  report-head-relative) was recomputed locally against the actual
  round-start parent: clean, and forecast tree
  ccd6838da50193d9d964c23bf95c33f6e7e6c622 equals the actual merged tree.
- 15153ade9dc8830f70792918377e3c52ae1f201f: local --no-ff merge of the
  accepted native setup B candidate tip
  181fab4ad0db31acf50c74e48bdff9f1b3ea2c22 (implementation
  00e973a79e60bf36b2dc396b872200ece1c8fe24, report SHA
  7fd6b8c297e0ccc87886bccf07c4625bdc83f457fd6c2c916cac12a6b4ff00a4).
  Forecast clean against the actual parent; forecast tree
  8f37114ea3b7b19c628d8a73049c8cba0ae6ffa3 equals the actual merged
  tree. Candidate order/report/implementation histories preserved; no
  reset/clean/stash/provenance-erasing cherry-pick.
- c2d589c23dab73b6f34bb75ee588db179b1efbb7: implementation — ONE new
  combined native extraction/count/chunk integration test, mandatory
  native CI provisioning on both product legs, docs/ingestion.md
  observed-count/chunk protocol, README/STATUS/UNCERTAINTIES/TESTING
  (T14) and governance measurements (routine context 46521 -> 48413/
  50000; MANIFEST re-hashed for TESTING.md and CONTEXT-BUDGET.md). No
  candidate code change was required: the two accepted tips passed the
  combined journey as-is.

Allowed paths only: one new integration test,
.github/workflows/oap.yml (solely the mandatory pinned native engine-
only test setup), docs/ingestion.md and the detailed native protocol,
README/STATUS/TESTING/UNCERTAINTIES and the affected context/manifest
measurements. No dependency/lock/runtime-model graph or
architecture/law/helper/prompt/client/profile/auth change; every other
MANIFEST-listed file is byte-identical (check_state verify_governance
passes; docs/benchmarks/qualification-testing.md byte-identical).

## Acceptance evidence

1. Actual owned OriginalStore -> native line/structure and real PDF
   extraction -> Registry -> fixed owned Session/native_chunking.build
   -> exact chunks, neighbors and three observed receipts per chunk:
   tests/integration/test_native_extraction_counts.py composes the
   actually merged components in ONE owned store: two logical documents
   sharing bytes with distinct corpus/labels/rights/version over one
   verified 0600 blob, a 700-word budget document and a mixed PDF;
   literal line/structural blocks tile the decoded original (Unicode,
   CRLF, astral, combining); the mixed native/raster PDF stays
   partial_visual_needed with no invented visual coverage; all extraction
   dependencies bind into the Registry; native_chunking.build returns
   exact chunks, each carrying three frozen TokenCount records and three
   matching receipts (OBSERVED_LOCAL_NATIVE_TOKENIZATION provenance)
   binding the exact full body / heading+body / query-pair inputs,
   observed artifact SHA, backend tokenizers 0.21.4, declared
   revision/preprocessing, role, mode/serialization and input digests;
   exact original spans/separators, heading paths, warnings with their
   procedures, repeated original table headers, conditional
   word-boundary overlap (observed body count at most 64 tokens —
   exactly two whole 60-word sentences observed), tail coverage,
   same-byte distinct IDs and cross-source binding denial; deterministic
   rebuild, reciprocal neighbors re-bound through the Registry, and
   changed definition/query/policy/revision change the chunk IDs.
2. Budgets, special tokens and legacy behavior: default 512 BGE body
   target / 768 soft maximum / 1024 representation maximum enforced;
   native complete pair 1280 with explicit 64 query reserve (the
   architecture example) while caller-supplied smaller values remain
   strict (observed native pair count 708 > legacy 512, smaller-policy
   refusal asserted); independent artifacts, repeated and empty pair
   inputs, both tokenizers' special-token pair shapes (6,7)/(4,5)/(3,4)
   on two independent artifacts; wrong count/identity/mutation/resource
   refused; no silently discarded tail. The legacy chunking.build
   callback fixture keeps pair 512 with SUPPLIED_UNVERIFIED provenance
   (supplied counts are assertions; mismatch refused). Counts are bound
   by independent session re-counts, never hand-derived word counts
   (the toy tokenizers emit extra tokens for words containing '.').
3. Mandatory native tests on BOTH product CI legs:
   .github/workflows/oap.yml adds the "Provision new private
   hash-verified native tokenizer test backend" step to the Python 3.12
   and 3.14 product jobs: the same verified /usr/bin/prlimit +
   /usr/bin/bwrap unshare set (plus /usr/bin/timeout), the same trusted
   standalone CPython 3.12 worker runtime and a NEW private pinned
   SHA-256-verified engine-only tokenizers 0.21.4 capsule via the
   corrected setup B helper; literal GITHUB_ENV
   SLAIF_NATIVE_TEST_ROOT/PYTHON/PACKAGES entries bound after the step
   (helper output never sourced or eval'd; helper failure retained
   through tee+pipefail). Missing or incompatible native/PDF backend or
   isolation FAILS — locally verified as explicit fixture errors with
   zero skips. Runner-only, read-only permissions and action pins
   unchanged; no native distribution added to the app graph/lock/
   allowlist; the engine-only --no-deps capsule is not license
   clearance.
4. Combined native pipeline, full affected native/session/bridge/
   chunk/extraction/source/provenance regressions, unit and
   integration separately, and lint/OAP/governance/installed-source
   routes all green at the implementation head before this report (see
   Verification): 661 unit / 414 integration collected and run, both
   exit 0; OAP scaffold 41 OK; check_state exit 0 (48413/50000);
   ruff/compileall clean; installed `raggedized --help` exit 0 and
   `doctor` exit 1 with MODEL_UNQUALIFIED (the honest unqualified
   example, as asserted in CI). Actual CI run 43065337340: all five
   required jobs SUCCESS. No causally demonstrated native composition
   defect existed, so no candidate module changed.
5. Documentation: docs/ingestion.md documents the observed-count/chunk
   protocol, budgets, observed versus supplied provenance, trusted
   filesystem/runtime/cooperative-deadline limits, required DEV setup
   and an actual usability limit section; TESTING.md T14; README/
   STATUS/UNCERTAINTIES updated with the honest limits and remaining
   work. No observed tokenizer receipt proves inference preprocessing
   parity, model quality, CPU serving, GPU memory, or
   license/019/ICA/MVP. Durable derived bundles/loaders and the private
   installed chunk command are explicitly retained as remaining 006
   work; this slice does not advance to 007.

## Actual usability limit (honest, reproduced)

A trusted mid-round strategic notice (QUAL-006-BUNDLE-SIZES-A report
S/parallel/bundle-capacity/report.json, independent root
/tmp/bundle_capacity_measure.py rerun) recorded that the accepted
session's 1024-call budget refuses the 7876-byte procedure source (403
blocks) and the 9269-byte table source (243 blocks) at attempted session
call 1025 before any chunk/neighbor/receipt output, while the 938-byte
Unicode source (765 calls, 1 chunk) and the 148-byte manual (150 calls,
3 chunks) complete. The affected broad criteria are therefore bounded:
the budgets are enforced with a total honest refusal, but
representative-scale usability is limited to documents small enough to
fit within 1024 session calls until the commissioned isolated
PAR-006-NATIVE-EFFICIENCY-A correction lands. The new test
test_native_session_call_budget_refuses_before_output reproduces the
refusal with the exact observed call count (1025; 202810 B input /
191163 B output) and asserts no partial output. No representative
large-document PASS is claimed from the bounded test fixtures, and no
full-006 or representative-large-document acceptance is claimed from
this slice. No optimization was duplicated and no unreviewed candidate
was integrated in this tree.

## Verification

Commands (implementation head c2d589c, devhost Ubuntu 26.04, uv 0.12.5,
local worker runtime CPython 3.12.15, parent pytest 3.14):

- git fetch origin; rev-parse origin/main == 4977186d3ddbd2259f78590b29c0364fe26eb1fb;
  gh pr view 8: OPEN, head 6b087d3, base main, no auto-merge, zero review
  threads.
- git merge-tree --write-tree (per merge, against the actual parent):
  clean forecasts ccd6838d / 8f37114e; actual merged trees equal;
  parents verified after each merge (b86f42e: d30898f+1a9e638;
  15153ad: b86f42e+181fab4).
- uv run ruff check src tests/unit tests/integration: "All checks
  passed!"; python3 -m compileall -q oap tests: clean.
- With provisioned dev backends (PDF_TEST_* and SLAIF_NATIVE_TEST_* as
  in TESTING.md T14): uv run pytest tests/unit -q exit 0 (661,
  collection-only count; includes the new native suites); uv run pytest
  tests/integration -q exit 0 (414, real isolated native worker and
  real PDF worker).
- Without the native/PDF backend environment: the required native/PDF
  suites fail explicitly (fixture ERROR/FAILED, zero skips, suite exit
  1) — fail-not-skip verified.
- python3 -m unittest discover -s tests/oap: "Ran 41 tests in 8.481s"
  OK.
- python3 oap/bin/check_state.py --repo-root .: exit 0 (state ACTIVE
  006-b; declared 48413/50000; critical {};
  activation_matches_current_governance false after this round's
  authorized measurement update — expected, 006-a precedent; the
  immutable order bytes are not rewritten).
- uv run raggedized --help exit 0; uv run raggedized doctor
  --config config/examples/example-config.json exit 1 with
  MODEL_UNQUALIFIED (honest unqualified example).
- Actual CI run 43065337340 on implementation head
  c2d589c23dab73b6f34bb75ee588db179b1efbb7 (Actions API: status
  completed, conclusion success, 2026-11-11T17:13:43Z): all five
  required jobs SUCCESS — OAP tests 3.12/3.13/3.14 (130678672640/
  130678671545/130678671460) and Product tests 3.12/3.14
  (130678671063/130678671618); the product legs executed the full
  required suites on the actually provisioned native and PDF backends.

Mock/live distinction: all inputs are synthetic owned fixtures. The
native count route is REAL local tokenization: the actual tokenizers
0.21.4 worker executes under real bwrap/prlimit/timeout isolation on the
devhost and both CI legs (a real worker route, not a mock replacing
tokenization), but the artifacts are locally generated toy tokenizers —
no deployed-model equivalence or inference preprocessing claim. The
PDF route is real native parsing by the merged 006-a worker.
Gateway/qualification routes are unchanged synthetic loopback suites.
Live target/model/GPU/private corpus authorization: NONE. No model
download, no network beyond the pinned wheel fetch inside the reviewed
helpers, no real corpus, no GPU. The CI evidence above was already
observed at the implementation head; this report makes no claim about
its own future push or CI — a separate post-publication receipt and
strategic review record those facts.

## Documentation impact

docs/ingestion.md: observed-count/chunk protocol (roles, exact inputs,
receipts, budgets, observed versus supplied provenance), the actual
usability limit, required local/CI native setup and the remaining-work
list. TESTING.md T14 added (historical T01-T13 unchanged). README
extended with the 006-b slice and the honest limits; STATUS current
state moved to slice 006-b with a historical entry; UNCERTAINTIES
"2026-11-11, order 006-b" observation block (U06 narrowed in software
only, observed call-budget limit, U07 unchanged — the engine-only DEV
capsule is not license clearance). CONTEXT-BUDGET.md 48413/50000 and
MANIFEST.json re-hashed (TESTING.md 6f3f3d19..., CONTEXT-BUDGET.md
1ed4f764...); docs/benchmarks/qualification-testing.md byte-identical;
exact model-token measurement remains UNMEASURED.

## DHA and boundaries

Decision: NONE; no critical append ordered or made; CRITICAL.md
untouched (critical {}). Preserved resources: every MANIFEST-listed
source/role/helper/prompt/startup/governance-law file byte-identical;
candidate order/report/implementation histories retained without
reset/clean/stash/cherry-pick; no secrets or private data in Git. No
merge performed: PR 8 remains OPEN, no auto-merge, no
tag/release/deploy, no GitHub/default-main merge by coding.

## Limitations and remaining work

- This slice does NOT close 006. The ordered same-PR continuations
  remain: (a) the commissioned isolated PAR-006-NATIVE-EFFICIENCY-A
  correction for the observed 1024-call session usability limit, and
  (b) the durable derived bundle/loader plus the private installed chunk
  command — all required before whole-006 acceptance.
- Representative-scale documents (the 7876-byte procedure and 9269-byte
  table sources) are refused today at attempted session call 1025 with
  no partial output (see Actual usability limit); no large-document PASS
  is claimed from the bounded fixtures.
- The DEV native capsule is engine-only --no-deps (pinned hash-verified
  tokenizers 0.21.4): not an upstream complete-app dependency, a
  lock/allowlist entry or a license clearance; cffi MIT-0 and the other
  transitive/native/platform/model license questions remain
  release/redistribution gates.
- Whole-006 acceptance, contextualization, embeddings, snapshots,
  retrieval, API, GPU/vision, ICA and all real qualification remain open
  / NOT RUN; this report certifies execution of 006-b only, not
  acceptance or release readiness.
