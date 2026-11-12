# OAP Work Order — 007-n

Status: FINAL
Identifier: 007-n
PR mode: AMEND_EXISTING_PR
Branch: oap/007-embedding-pipeline
Base commit: e9ee12568fdfbfd9f122ceb3ed0d15690b4dbbfa
PR number: 9
Expected active: 007-m
Provenance: H full-MVP/parallel/CI mandate; A ARCH8.4/11.2/19 and A08/A12/A16/A27; I four Root/opposite-peer reviewed component sources; E canonical selected-source GPU pipeline and clean-stop/fresh-creator resume remain absent after M
Architecture SHA256: 4b41905396a3838269fd6cf372614cd23cb2c3b6a37be09f29ed752803c0983a
Governance SHA256: d4edcae75ef40e0c7cc697435fb2ec4b5b01802b40809e87cb1ad486bec221e5

## Objective

Integrate ONLY21 frozen files335687bytes in audit/007-n-corpus-pipeline-components.json SHA256 7d28fbb58e4cfaf888ddc0cb60f066297f76c66e31766f040c39f1823e78d752. Sources: launch-owner b0ca5a68f8e55667ada5dd7523903b5585cbe0af (5), GPU producer880dedf33e7b9eb1da497bf88acb6bb626a7fce3 (5), source program6f5b31123d080376b6b0c09a803bd67033694484 (6), executorbac11bee72fa809157b77e21be8bcf8ef17529a9 (5). Use exact source blobs, no implementation adaptation. TWO deliberate existing production replacements: gpu_worker_launch.py adds reviewed owned preparation/handoff, retrieval_representation.py adds reviewed whole-source formatting support. Other19paths are new. Preserve every other preexisting code/test/API/design file.

The pipeline validates complete selected original-backed bundles, stable source-local batching, known-parent launch preparation and owned per-batch producer, native/execution/result records, typed normalized FP32 output and actual journal COMPLETE reuse. Executor preserves operation-wide epoch/configuration, stops before uncertain later work and supports fresh-creator resume after a clean stop BETWEEN batches. Unknown/failed/claimed/running attempts do not become retryable by decree. Borrowed reservations/stores remain borrowed. Whole007 remainsPARTIAL; no operational mode controller, current-principal policy, inference CLI or physical qualification is supplied.

## Dependencies and current state

M is resolved PARTIAL in audit/007-m-review.json, with timing ledger event recorded before this continuation. Exact M transcript3cd39ce, implementationc74407f10ebaf429b233a6d9f6da67a0f367e5e4 and SELF report e9ee12568fdfbfd9f122ceb3ed0d15690b4dbbfa (8064B) passed strict original remote verification. Current report run43262182860 ALL5 requiredjobs/ALL78 actualstepsSUCCESS; sole normalresponse verified17:05:04Z. PR9 uniqueOPEN/non-draft/auto-mergeoff, no unresolvedthreads/change requests; main11badc7782bed326995d400f5532b63399b91fbd unchanged. Root has independently reviewed source/docs/controls/localchecks/SELF/remote and recorded report ancillary timing/setup errors as limitations rather than accepting those claims. No main merge or whole007 acceptance.
Root current-M-plus-N source forecast audit/007-n-current-M-source-forecast.json independently verifies all83 shared production modules equal the reviewed executor source. Two canonical-only K declaration modules remain. This forecast establishes source correspondence, not current canonical execution or CI. Root frozen component records include independent peer findings, actual controls, repaired failures and original approved heavy-proof boundaries.

Exact Root records: audit/007-n-root-records.json SHA256 64e22fd4c5b655e4bcc45cafd690e08d2ecb14758be99b1efd5474718cf11ebb. FIRST copy all 29 source/target/hash/byte entries unchanged plus this index to oap/reviews/007-n-root-records.json and the component index to oap/reviews/007-n-corpus-pipeline-components.json. All actual bytes are available on the shared filesystem. Historical pending-at-first-review records remain followed by final admissions/peer decisions; do not rewrite history or coding reports.

## Allowed paths and scope

FIRST sole-parent transcript commit on exact M SELF: final order unchanged at oap/orders/007-n-corpus-pipeline-integration.md, active007-n plus LF, all named Root records and both indices. THEN ONE sole-parent implementation commit: exactly21 indexed paths plus named concise current docs/accounting. THEN immutable sole-parent SELF report-only commit. No merge/cherry-pick/rebase/reset/clean/stash/switch, parallel orders/reports/helpers/private permits/state/FIFOs or source adaptation. Unindexed conflict returns to Root.

BOTH L exceptions stay exact: tests/unit/test_embedding_native_identity.py SHA256c2b483b77c84f304ead4a6ae5c2ef27e5194c1df6ccd6adbb62992a7904a8df6 and tests/integration/test_cpu_embedding_session_composition.py SHA256275e10d333555f6e02f3261449e6f9becf99e659a352ee9d4464e4837a843fd0. Preserve canonicalK declarations and allM10. Earlier prototype tests must not overwrite these fixes.

Allowed current docs README.md, STATUS.md, TESTING.md, docs/embedding.md, docs/UNCERTAINTIES.md. oap/governance/CONTEXT-BUDGET.md and MANIFEST.json only for measured current-document accounting/hash updates. Preserve TESTING T1–T15 byte-for-byte; update/compress T16 within aggregate sixfile coding-readset50000B. Current aggregate49999B, TESTING17448B; those are distinct measurements. Rewrite current summaries concisely/link exact APIs instead of adding another history paragraph. No source originals/ARCH/law/projections/CRITICAL/CI/workflows/pins/dependencies/helper/profile changes.

## Non-goals

No current-principal permission/controller, serving, inference CLI, physical BGE/FP16/GPU/hardware qualification, snapshot/parity integration, numeric008, main merge, release or deployment. No changes outside exact indexed source and named current docs/accounting. No test skip or raised runtime policy.

## Acceptance criteria

1. Verify exact transcript/source/index/hash/size/base/sole-parent topology and preserved paths. Report metadata uses bare literal40hex actual Git facts, Identifier007-n, ResultPARTIAL, publicationSELF and <=8192UTF8bytes. Record current changed paths/counts, not guessed source invariance.
2. Source program validates ALL selected original-backed rows, stable ordered source-local batches, no silent >128-row truncation or whole-corpus ceiling128. Fresh complete source/configuration correspondence, wire/count row fit and canonical program before model/job. Source DATA is not current rights, qualified runtime or readiness.
3. Producer uses actual captured preparation/native bridge/journal/typed store; original epoch checks at boundaries and actual full observed records/digests/reuse. Pending cleanup retains actual owners/lease, hostile non-Exception identity survives, borrowed state is not released. Executor stops on failure, checks operation-wide epoch/config/deadline, retains lightweight completions and a common record pair. No fabricated exactly-once guarantee.
4. Run ALL four new unit modules: test_gpu_launch_preparation_owner.py, test_gpu_embedding_producer.py, test_corpus_embedding_program.py, test_corpus_embedding_executor.py. Static parametrization predicts51cases; record actual collection/results without rerunning passes just to print summaries. Each invocation CPU30/AS1GiB/wall120/fiveThreads1. Run these13 actual cases each in its OWN capped process:
   - tests/integration/test_gpu_launch_preparation_owner_composition.py::test_owner_handoff_preserves_existing_arguments
   - tests/integration/test_corpus_embedding_program_composition.py::test_actual_selected_sources
   - tests/integration/test_corpus_embedding_program_composition.py::test_over_128_actual_chunks
   - tests/integration/test_corpus_embedding_program_composition.py::test_actual_remaining_char_preflight_matches_base
   - tests/integration/test_corpus_embedding_program_composition.py::test_actual_byte_budget_refuses_before_next_source_load
   - tests/integration/test_gpu_embedding_producer_composition.py::test_before_model_authorization_refusal_is_pre_journal
   - tests/integration/test_corpus_embedding_executor_composition.py::test_actual_whole_program_rowfit_refuses_before_dispatch
   - tests/integration/test_corpus_embedding_executor_composition.py::test_actual_changed_source_refuses_before_producer
   - tests/integration/test_corpus_embedding_executor_composition.py::test_actual_changed_launch_after_validation_refuses_before_producer
   - tests/integration/test_corpus_embedding_executor_composition.py::test_actual_provider_refusal_stops_before_later_batch
   - tests/integration/test_corpus_embedding_executor_composition.py::test_actual_terminal_journal_stops_corpus[FAILED]
   - tests/integration/test_corpus_embedding_executor_composition.py::test_actual_terminal_journal_stops_corpus[UNKNOWN_COMPLETION]
   - tests/integration/test_corpus_embedding_executor_composition.py::test_actual_hostile_interrupt_retains_producer_cleanup
   Ruff product scope, syntax/diff, OAP41/check_state, offlinehelp/doctor and measured governance required. Do not rerun unchanged L112/M17/expensive producer sweeps absent a new concern. Preserve every failed log; no skip/xfail/cap increase or count-only repeats.
5. Historical exact executor5rows/2batches stop/freshcreatorresume/allCOMPLETEreuse proof passed observed102.715SELF+CHILDRENCPU104.983wall, not aggregate hard cap. Historical producer freshbatch used explicit outerCPU60; ordinary cases remain30. No new standalone local heavy rerun is authorized. Current full required CI must normally collect and pass ALL integration tests, including unchanged producer freshbatch and executor complete-resume drivers and their existing narrow fresh-child phase limits. Do not omit tests or treat historical proof as fresh currentCI. Any separate local heavy run requires new exact source/driver/plan/Root budget decision first. Existing20min product jobs remain; actual timeout/failure requires investigation, not waiver.
6. Current docs/report distinguish integrated synthetic software, real native tokenizer and DATA-only fake CPU/GPU distributions from actualBGE UNRUN/UNQUALIFIED. No model origin/current processing grant/rights/READY/hardware/FP16/scale/license/security/quality/visual/ICA claim from records/hash/DTO/epoch. Preserve actual38/class-import/license observations, archived CPU toy history and unknown old host-failure cause. Snapshot/parity/operator leaves remain future scope.
7. Local checks then truthful sole-parent SELF publication, without waiting for intermediate implementationCI. CURRENT REPORT head must pass ALL5 requiredjobs and EVERY actual requiredstep (currently78) before ONE normalresponse/Rootacceptance. Missing/skipped/pending/cancelled/blocked/failure is not green. No workflow/protection/cap bypass. Report at publication states then-currentCI truth; later facts are separate records. Each wait call<=60sec, with regular observations. No6min polling batch. Original verify-report against actualremote before response; no metadata adapter/oldreport rewrite.

## Verification and negative evidence

Review exact actual base/source/index/records/SELF/current report CI. Keep original hostile-interruption, unknown-journal, changed-epoch/source/config, before-model refusal and stop/resume controls attributable. Metadata/source identity is distinct from actual model origin, current authorization and hardware qualification. Preserve all original failure logs and ordered setup corrections. Do not rewrite immutable reports or turn historical proof into current CI.

## Documentation

Only named concise current documentation and measured TESTING/T16/accounting. Full transitive task readset hashes, whole-file bytes and actual read ranges are required; hashing a file does not show full reading. Keep original source books, architecture and law unchanged. Explain two deliberate production replacements and all remaining qualification gates.

## Runtime and protected resources

Cached app3.14; PYTHONPATHsrc:tests/unit:tests/integration, PYTHONDONTWRITEBYTECODE1 and OMP/OPENBLAS/MKL/RAYON/NUMEXPR_NUM_THREADS1. Each ordinary pytestCPU30/AS1073741824/wall120. Unique0700 basetemp ancestor created before source fixtures; insecure ancestor caused M setup refusals. Exact native root/home/janezp/.local/share/uv/python/cpython-3.12.15-linux-x86_64-gnu, SLAIF_NATIVE_TEST_PYTHON=python3.12, SLAIF_NATIVE_TEST_PACKAGES=/tmp/raggedized-root-native-setup-b-6cd8bebe0a/packages. GPUfake SLAIF_GPU_TEST_ROOT=/tmp/raggedized-root-cpython312-portability and SLAIF_GPU_TEST_PACKAGES=/tmp/raggedized-root-gpu-fixture-c0e14e2c/packages. CPUv2fake SLAIF_CPU_V2_TEST_ROOT=same copied root and SLAIF_CPU_V2_TEST_PACKAGES=/tmp/raggedized-root-cpu-v2-portable-485fc687/packages. Native root variable SLAIF_NATIVE_TEST_ROOT. Ruff wall120/thread1 allocator exception stays separate from test caps.

No install/download/network/framework/Tensor/model/GPU/driver/service/credential/privatecorpus/SSH/sharedfixturewrites. Preserve human Qwen/A100Q8/xhigh/profile/auth. No otherpanes/nestedagents/runtimepermits/mode transitions. No snapshot/parity integration, inference CLI, numeric008, mainmerge/auto-merge/release/tag/deploy. Strongest counterargument:21files335687B, two existing production extensions and costly default CI tests increase review/dependency/runtime cost. Mitigate exact coherent83shared-module forecast, independent component evidence,13 finite current ordinarycases and currentfullCI. Split if an actual source/dependency concern appears; never relax an invariant to meet the queue.

## Deferred human adjudication

- Decision: NONE

## Publication and report

Existing PR9 only, original helper and ONE control/response. Read shared final order/active/records first. Exact measured transitive readset and full-vs-selected scopes, source/test/API/design hashes/bytes, actual commands/env/rawstdout/exit/failures and limits. Original strict metadata/remote SELF verifier, current report all5/everyrequiredstep success, ONE normalresponse, finish bounded007-n goal and idle. Root owns review, further suffixes and development merge. Whole007/MVP staysPARTIAL. No FIFO reread/replay, second consumer or self-chosen roadmap.
