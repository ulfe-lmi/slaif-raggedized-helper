# OAP Work Order — 006-a

Status: FINAL
Identifier: 006-a
PR mode: CREATE_NEW_PR
Branch: oap/006-native-extraction-and-chunking
Base commit: 4977186d3ddbd2259f78590b29c0364fe26eb1fb
PR number: NEW
Expected active: 005-b
Provenance: H activated architecture MVP and parallel work; A original006 and architecture7.1–7.4/9.1–9.4/22.1–22.2; I independently accepted local extraction/PDF/required-test-setup components
Architecture SHA256: 4b41905396a3838269fd6cf372614cd23cb2c3b6a37be09f29ed752803c0983a
Governance SHA256: ead5815a0c2ab551f6343b7c71736486ab482cfe4c810b12aeb3363c639ee59b

## Objective

Begin canonical006 with complete native extraction software on the accepted005 record/store
foundation: integrate exact reviewed line, structured Markdown subset and corrected isolated
PDF adapters, prove original coverage and refusal behavior in the combined tree, and make
required PDF tests reproducible and mandatory on actual CI. This first slice does not close
006. Same-PR continuation must integrate reviewed structural chunking/native tokenizer
sessions and prove actual bounded composition before whole006 acceptance. Original006
criteria all remain; no silent weakening or numerical jump.

## Dependencies and current state

005 is complete and MERGED as PR7 at main4977186d3ddbd2259f78590b29c0364fe26eb1fb, accepted report45a50db3478152fdb4056c1bcb3a990580d60373, implementation617bc725cdc34519ab9d080e5da185065ffd4d91, reportSHA091b4bdce4ea426b697b559b50aa68343094812c9bd1fb23ed5a180dba3b2d2c.
Final Root review oap/reviews/005-b-review.json SHA1aae55206bd1d8c786037bb7db5022a48d5bbcecb2bc008fb5824f8014b73219; terminal resolution oap/reviews/005-resolution.json SHA3ffbac86344d2ee47422cda69c4659716d8eeace7d7a53fcc2b9147fa1fba754. ImplementationCI43042968211/reportCI43044055137/mainCI43044818307 ALL5SUCCESS, last main job15:09:06Z. Exact expected-head protected merge15:05:18Z, default main/parents/tree independently verified. No unresolved objective PR. Routine44046/50000bytes; source/role/helper/startup laws unchanged.

Current coding branch is the terminal005 branch. The only intended untracked files are the exact two Root review/resolution files above. Commit these plus new order/active unchanged on new006 branch from the verified main. No reset/clean/stash or prior signal replay. Existing sole next-control waiter1725810 is retained; current005 operational goal achieved and cleared once. No duplicate reader. All actual target/model/GPU/private corpus authorization remains NONE; public tokenizer tooling scope applies only in specifically ordered parallel/006 continuations.

Exact locally accepted candidate tips, with immutable original orders/reports retained:
- PDF-D plus reproducible test setup: be40286eeafe810071961789aa7d80d2fac847d5;
  setup implementation33d77b6841bc22448095c791fdd9e8b9a37fa3ed,
  reportSHA d086031bb45cc975cb92792121032990fda2f11ff4fc2a15253a2d3fbcd7465e.
  Root parallel/pdf-test-setup/review.json; corrected PDF-D tip
  eb80a7bc84fbf74f46882030a3ce277852e18bf2 and Root review there. Exact
  corrected parser and worker blobs01d18381895ad539051e9fe6f98119c31623f3f1
  and652fcf664cb6de017a9ed4d13353b0a365031be0 respectively.
- Literal line extraction: e84469f78b82fc5cd41110289bfa7446793ca034;
  Root parallel/text-extraction/review.json.
- Structural text: 7a0caf1a3c51427de33fa7140ec01bc24ca81d13;
  Root parallel/structured-text/review.json.
Each Root review has an opposite-context peer artifact. Structural text's old PDF-A ancestor
is not accepted PDF code; canonical integration must retain corrected D and test setup.

## Allowed paths and scope

After exact branch/round-start setup, THREE authorized LOCAL --no-ff merges only, in the
listed order: PDF-test-setup, literal line, structured text. Forecast against actual parents
using merge-tree, inspect parents/tree after each and retain immutable candidate histories.
Any conflict or unexpected accepted source/PDF change requires concrete reconciliation,
never reset/clean/stash/cherry-pick away provenance. No GitHub/default-main merge by coding.
No006 tokenizer/chunk/native-session or008 branch belongs in this first slice.

Allowed new edits: one meaningful combined extraction integration test and any demonstrated
scoped extraction composition defect; docs/ingestion.md or native extraction protocol;
README/STATUS/UNCERTAINTIES/TESTING and affected context/manifest measurements;
.github/workflows/oap.yml solely for required reproducible native PDF development tests;
tests/support backend setup and its exact hash requirements only if actual CI qualification
shows a necessary correction. Preserve all accepted005 records/source/CLI,004 qualification
and older regression assertions. No dependency/lock/runtime-model graph or architecture/law/
helper/prompt rewrite. Source metadata processing approval remains distinct from auth/rights.

## Non-goals

No tokenizer/chunk/session/008 integration in this first006 slice, contextualization, embeddings,
snapshot/retrieval/API/GPU/vision work, real sources or legal exceptions. No unrelated refactor,
client/profile/auth changes, new public interface, release/tag/deploy or GitHub/default-main merge.

## Acceptance criteria

1. Actual owned source manifest -> OriginalStore -> native line/structure/PDF adapters ->
   provenance.Registry, complete approved revision/scope binding, exact original Unicode
   codepoint coverage, native/visual-needed status, original geometry/reading order and honest
   partial outcomes. Preserve headings, paragraphs, procedures/warnings, code fences and
   table headers/units as supported by the documented bounded subset. Never claim full
   CommonMark, OCR, rasterization or semantic reconstruction from the implemented subset.
2. PDF remains fixed trusted isolated worker: bounded verified original read before parser,
   actual configured runtime/packages read-only, no network/home/GPU/credentials, bounded
   CPU/memory/pipe/time and owned-child cleanup. Nested forms retain native text/actual
   character boxes without duplication; images and vector content, including mixed pages,
   explicitly require visual work and cannot report complete-looking native extraction.
   Count/coverage correlations reject objects0 with claimed blocks or forged geometry.
3. Add combined tests with shared-byte distinct rights/ACL/version, metadata revision,
   native literal and structural coverage, source immutability and malformed/oversized/
   wrong-hash/unsupported input refusal. Retain corrected actual nested-form/mixed-raster/
   vector-page and every existing parser/source regression. Separate source byte integrity
   pass from parse limit and cooperative parent-filesystem limits honestly; no timeout claim
   unsupported by actual worker boundary.
4. Required PDF tests fail missing/incompatible backend or isolation instead of skipping.
   On both product CI Python3.12/3.14, explicitly provision a NEW private pinned hash-verified
   PDF backend via the reviewed helper and bind an actual standalone worker3.12 runtime
   using PDF_TEST_RUNTIME/PDF_TEST_PACKAGES. Install/verify bwrap/prlimit only on disposable
   GitHub-hosted test runners. Qualify actual namespaces/worker setup and run the full
   unchanged required tests; no fallback unsandboxed parsing, continue-on-error, exclusions,
   success with skipped checks or weaker fixture assertions. Preserve read-only contents,
   immutable action pins, no secrets/self-hosted/deploy/release/public-service side effects.
   If host isolation fails, retain precise evidence and correct safe setup; do not silently
   count missing capability as pass.
5. Whole combined unit and integration run separately, OAP/lint/governance/installed source/
   qualification routes pass on actual implementation head and all required actual CI checks
   succeed before immutable report. Record real process exits, not grep pipelines, and use
   collection-only for test counts. Keep routine governance<=50000bytes and preserve detailed
   historical qualification-testing.md verbatim. Detailed ingestion contracts live outside
   routine projections. No model-token measurement or quality claim without evidence.

## Verification and negative evidence

Use actual required source/structure/PDF and combined extraction fixtures, including malformed
inputs, unsupported formats, corruption/hash/metadata/ACL boundaries, wrong/count/geometry
responses, nested forms, text plus raster/vector pages, finite worker limits and cleanup. Test
real isolated backend on parent3.12/3.14 and configured worker3.12, not mocks replacing native
parsing. Preserve all older source/record/qualification regressions. Capture actual exits and CI;
missing/skipped/pending/cancelled is not success. Unit/integration run separately; collection-only
for counts. Explicit configured backend and namespace prerequisites fail visibly if absent.

## Documentation

Publish exact supported format/structural subset, source-to-block coverage/anchors/native versus
visual-needed/partial semantics, parser resource and trusted-runtime/filesystem limits, required
local/CI setup and exact DEV-only pins. Clearly separate remaining006 chunk/tokenizer integration
and all physical/model/domain/license/ICA gates. Summarize in routine<=50000bytes, update manifest/
context measurements together, preserve detailed qualification history verbatim and source/role/
helper/startup files unchanged. Do not advertise an unimplemented command or qualified model.

## Runtime and protected resources

Real target/model/GPU/corpus authority NONE. Synthetic owned CPU inputs and isolated ordinary
DEV backend setup/CI are authorized. PDF packages are exact development dependencies only;
cffi MIT-0, other transitive/native/platform/model license questions remain release and
redistribution gates. No application graph or allowlist expansion, no legal exception,
weights/model inference/credentials/service/profile changes, unrelated source or real data.
Preserve canonical coding Qwen3.8-27B/A100Q8/xhigh and existing gateway/Qwen profiles.

The remaining same-PR006 continuation integrates independently accepted corrected C structural
chunks and exact native/session counting, preserves512/768/1024 body/representation and complete
independent pair budgets/conditional64 overlap, warnings/procedures, exact table references/
neighbors and no-tail-loss mapping. Public tokenizer observed-case software evidence remains
separate from deployed inference/model/serving/019/domain/license/ICA qualification. Full text
and visual MVP, renderer/vision016 and source-serving/auth014 remain open.

## Deferred human adjudication

- Decision: NONE

## Publication and report

Create exactly one006 PR after accepted005 resolution; commit exact Root review/resolution/
order/active bytes unchanged. Perform only the THREE ordered local merges and scoped changes.
Publish immutable report-only SELF commit with sole actual implementation parent, exact tests/
CI/scope/omissions and NO whole006/MVP claim. Verify remote bytes/head/topology, respond once
through the qualified sole wrapper, complete bounded goal and idle. No next work, post-response
poll/readers, GitHub/default-main merge or release. Strategy independently accepts current head,
orders necessary same-PR continuation and owns any qualifying protected development merge.
