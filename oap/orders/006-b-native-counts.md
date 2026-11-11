# OAP Work Order — 006-b

Status: FINAL
Identifier: 006-b
PR mode: AMEND_EXISTING_PR
Branch: oap/006-native-extraction-and-chunking
Base commit: 6b087d3a58d1f96faf130f086556706fec297de1
PR number: 8
Expected active: 006-a
Provenance: H activated architecture MVP and parallel mandate; A original006 and architecture8.1–8.3/9.3–9.4/20.2; I independently accepted native bridgeB and native setupB; E canonical extraction still lacks observed native chunks
Architecture SHA256: 4b41905396a3838269fd6cf372614cd23cb2c3b6a37be09f29ed752803c0983a
Governance SHA256: ceec4a34ae426a83d107edd7a96253ad6bdd3acbb3f362875cd05b6786d094f9

## Objective

Integrate the reviewed fixed native tokenizer session and structural chunk adapter with
canonical extraction, prove observed independent input/count bindings and exact original
mappings, and make real native tests mandatory on both product CI versions. Continue PR8;
this slice does not close006. Durable derived bundles/loaders and the private installed chunk
command remain a separate required same-PR workset before whole006 acceptance.

## Dependencies and current state

006-a accepted as extraction slice only. Exact report 6b087d3a58d1f96faf130f086556706fec297de1, sole implementation
parent e57820e13993860f86d026531dd0ef6d223f0f60, reportSHA
873dcb31bb9971eb84c5b0bf419616c01de4870dbb113964aea4d2e131a6a6ca.
Root review oap/reviews/006-a-review.json SHA9ae5bbc3979b8b5b269437845fa365b1c1a474a4cf40c64533062506d8e214ef, copied unchanged into the
working tree for this round-start commit. Root51 actual extraction tests PASS with real worker;
collection614unit+383integration; implementationCI43053529368 and reportCI43055664954
all five required jobs SUCCESS. Unique PR8 OPEN, branch/base/head confirmed, zero review
threads/auto-merge. Correct PDF-D source retained; no whole006 or real qualification claim.
Canonical006-a bounded operational goal was cleared once after response completion; actual
quiet prompt without Pursuing footer verified. Start/retain exactly one external next-control
waiter under strategy; no coding post-response readers. No Git reset/clean/stash/switch.

Accepted local candidates (immutable reports/orders/histories retained):
- Native bridgeB: 1a9e6387f4ba2134894f81c6827c78d78d462843, implementation
  40d7d867629c43e42aaf06ac56d9c58a509af6e1, reportSHA
  486e4a4d71f2a6798ac9edaa023ec35b4a233e6d5ec926ea8009fda5769fb453.
  Root parallel/native-chunk-bridge-b/review.json: full original source plus corrected
  declaration pre-admission guard, Root14tests and unchanged negative witness PASS;
  opposite peerA covers unchanged features, no B peer claimed. Includes corrected chunkC,
  nativeB and accepted session d558c97d8d610bec3bbf4979062855feab5923d1.
- Native setupB: 181fab4ad0db31acf50c74e48bdff9f1b3ea2c22, implementation
  00e973a79e60bf36b2dc396b872200ece1c8fe24, reportSHA
  7fd6b8c297e0ccc87886bccf07c4625bdc83f457fd6c2c916cac12a6b4ff00a4.
  Root parallel/native-test-setup-b/review.json: corrected bounded probe pipe/cleanup,
  five actual new child tests, unchanged2MB output witness and fresh private engine capsule
  with actual worker tests PASS. Earlier peerA38tests each parent; no B peer claimed.
Read the exact accepted reviews and relevant API contracts; do not load whole books/history.

## Allowed paths and scope

Commit exact strategic review/order/active bytes unchanged as round-start on current branch.
Perform TWO authorized LOCAL --no-ff merges in order: native bridgeB, then native setupB.
Forecast against actual parents using merge-tree, verify parents/tree after each and preserve
histories. Preliminary first forecast at reporthead+bridgeB: df9ca714c0e871fc41a36e5e7753db89bc5b731d; recompute locally.
Conflicts/unexpected accepted source changes require evidence reconciliation, never reset,
clean, stash or provenance-erasing cherry-pick. No GitHub/default-main merge by coding.

Allowed new edits: ONE meaningful combined native extraction/count/chunk integration test;
.github/workflows/oap.yml for mandatory pinned native engine-only test setup; docs/ingestion.md
and detailed native protocol; README/STATUS/TESTING/UNCERTAINTIES plus affected context/manifest
measurements. Only causal demonstrated native composition defects may change relevant native/
chunk modules or test setup. Preserve all accepted005/006 extraction and004 routes/regressions.
No008/ranking/vector/JSONL/bundle candidates in this slice. No lock/app dependency/allowlist,
architecture/law/helper/prompt/client/profile/auth changes.

## Non-goals

No durable bundle/filesystem/CLI integration yet, contextualization, embedding, snapshots,
retrieval, API, GPU/vision, real source/model inference, legal exceptions, deployment/release,
unrelated refactor or Github/main merge. No qualified serving latency/memory/quality claim.

## Acceptance criteria

1. Actual approved owned OriginalStore -> native line/structure and real PDF extraction ->
   Registry -> fixed owned Session/native_chunking.build -> exact chunks, neighbors and three
   observed receipts per chunk. Preserve exact Unicode fragments/separators, headings,
   warnings/procedures, table headers/units, tail coverage, revision/rights/labels and original
   bytes. Same-byte distinct rights/version retains distinct IDs and cross-source denial.
   PDF mixed/raster/vector status remains partial_visual_needed; never invent visual coverage.
2. Preserve default512 BGE body target/768 soft maximum/1024 full representation, conditional
   up-to64 overlap, native complete pair1280/reserve64 and both independent tokenizers' special
   tokens. Legacy callback fixture pair512 remains supplied/unverified. Actual native roles bind
   exact full body/heading+body/query-pair inputs, artifactSHA, declared revision/preprocessing,
   backend, role, mode/serialization and input digests. Test independent artifacts, repeated and
   empty pair inputs, budgets, deterministic IDs/reciprocal neighbors, wrong count/identity/
   mutation/resource refusal and no silently discarded tail. Use locally generated toy tokenizer
   artifacts for mandatory tests; no deployed-model equivalence claim.
3. Required native tests run on BOTH product CI Python3.12/3.14 using actual standalone worker
   CPython3.12 and a NEW private pinned hash-verified engine-only tokenizers0.21.4 capsule via
   corrected setupB helper. Existing bwrap/prlimit/timeout and real namespaces/mounts required.
   Set literal known SLAIF_NATIVE_TEST_ROOT, SLAIF_NATIVE_TEST_PYTHON=python3.12 and
   SLAIF_NATIVE_TEST_PACKAGES entries in GITHUB_ENV; never source/eval helper output and retain
   helper failure through pipelines. Missing/incompatible native/PDF backend/isolation FAILS,
   never skips/fallbacks/weakened assertions. Preserve runner-only/read-only/no-secret/action
   pins. No native distributions added to app graph/lock/allowlist or legal clearance inferred.
4. Run combined native pipeline, full affected native/session/bridge/chunk/extraction/source/
   provenance regressions, unit and integration separately, lint/OAP/governance/installed-source
   routes. All required exact implementation-head CI jobs SUCCESS before immutable report.
   Record actual exits and collect-only counts. Keep routine governance<=50000UTF8bytes:
   consolidate routine test summaries if necessary, retain detailed qualification-testing.md
   byte-identical and full contracts outside routine files. Update context/manifest together;
   exact model-token measurement remains UNMEASURED.
5. Document API, budgets, observed native provenance versus supplied callbacks and trusted
   filesystem/runtime/cooperative deadline limits. No observed tokenizer receipt proves actual
   inference preprocessing parity, model quality, CPU serving, GPU memory, license/019/ICA or
   MVP. Explicitly retain durable bundle/loader/private chunk CLI as remaining006 work before
   whole006 merge; do not advance to007 from completion of this slice.

## Verification and negative evidence

Use owned synthetic multilingual/technical command/version/negation/procedure/table fixtures,
source span reconstruction, conditional overlap and no-tail-loss with independent actual toy
native tokenizers and real PDF worker. Retain all corrected source/hash/count/geometry/nested
form/mixed visual and native declaration/output/deadline/cleanup regressions. Distinguish
special-token pair shapes from simplistic word counts, source byte integrity from parser limits
and observed native counts from model qualification. No missing/skipped/pending check is green.

## Documentation

Update ingestion/native protocol and succinct routine projection with actual commands/setup,
limits/uncertainty and remaining durable/operator gates. Preserve source originals/law and
historical qualification details. Existing detailed component docs can remain detailed outside
routine reads. Reflect actual CI and provenance, never future results in a report.

## Runtime and protected resources

Real target/model/GPU/services/credentials/private corpus authority: NONE. Ordinary disposable
CPU/DEV CI and bounded owned synthetic inputs are authorized. Public tokenizer assets may be
used only for supplemental CPU counts within the existing exact allowance in strategic
 audit/006-public-tokenizer-provisioning-scope.json; no weights/forward inference/GPU or required
network assets in tests. Engine-only --no-deps capsule is not upstream complete app dependency
or license clearance. Preserve canonical Qwen3.8-27B/A100Q8/xhigh and all human client settings.

## Deferred human adjudication

- Decision: NONE

## Publication and report

Amend existing PR8 only. Commit Root review/order/active unchanged, preserve exact local merge
histories and report identities, publish tested implementation, observe all required actual CI,
then immutable report-only SELF commit with sole implementation parent. Verify remote bytes/
head/topology and respond ONCE through qualified helper; finish bounded operational goal and
idle. No post-response audits/polls/readers/next work. Strategy owns exact-head review,
continuation and any later guarded development merge; no release/tag/deploy.
