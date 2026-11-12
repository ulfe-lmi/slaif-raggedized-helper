# OAP Work Order — 007-f

Status: FINAL
Identifier: 007-f
PR mode: AMEND_EXISTING_PR
Branch: oap/007-embedding-pipeline
Base commit: 52ae2918c09ea939ba7c8694cd6e65e735c1d918
PR number: 9
Expected active: 007-e
Provenance: H activated full-MVP/parallel mandate; A8.4/11.2/19/22/23; I independent producer peerB CHANGES_REQUIRED and exact Root component reviews; E demonstrated acquisition/journal/producer/isolated cleanup/interrupt/foreign-FD faults, plus missing per-device substrate
Architecture SHA256: 4b41905396a3838269fd6cf372614cd23cb2c3b6a37be09f29ed752803c0983a
Governance SHA256: f279dbc7e4bbc0240bd8b85eef1f3877fb2ad9f5b72488dff46c196847f637c1

## Objective
Integrate TWO exact already-reviewed candidates fixing actual ownership/cleanup composition and providing the cooperative per-device kernel lease substrate. Preserve whole007 PARTIAL: no mainmerge, numeric008, actual model/GPU operation, runtime/profile cutover, release or deploy. This is exact integration, not reimplementation or whole-pipeline ICA.

## Dependencies and current state
007-e exact impl2bf4d3916c07bfd8e2ae99612885e364788c9e3f and SELFreport52ae2918c09ea939ba7c8694cd6e65e735c1d918, reportSHA b3d7f0a6efc0eec4c208637b4267ab2785bee21c1b73f9d5c5f42f9d0fbacfe7/7431B, independently reconciled in audit/007-e-review.json. BOTH implementationCI43143641055 and reportCI43144877086 are independently ALL5/ALL74SUCCESS. UniqueOPENPR9/main11badc7782bed326995d400f5532b63399b91fbd, no draft/auto/unresolvedthreads, clean currenthead and consumedresponse. Never reread that FIFO. Routine49936/50000; tokensUNMEASURED; law unchanged.

Exact merge order: FIRST cleanup-composition report985806afe7c985d8a511261f9384cd1bfebce2f0 (impl4a929261f9ee6104df5002587d45cd043607a719, SELFreportSHA4d835027c13747084a711ea109c31f28bff42c85337a4ec4ea3a902a42e34f63), which includes exactGPUlease report692fa53bb62aa2c0b0b61454378a7986c4b3c025; THEN isolated-exit report52252484baf733c98e42963ce759c0b5db27b006 (impl48aafeefdb65b1fbcd340f3fb32ddda811c42117, SELFreportSHAefaae34670b6d4e69af8fa4fb7d191ea972c66d54653f92a271ef05095d8b8bd). All local Root reviews final. Index audit/007-f-components.json SHA199fd1a248023448cfd9027182590aebe3ea96e71a1fc306e4c8750bd0b84d24 enumerates17exact source/test/API files,195649B; all already reviewed. Root exact pair-tree f92f8da765cb3262794e39534c628c2d9fa1cab9 independently105unit+39standalone+10originalwitnessesPASS, notcurrenthead/ICA. Read APIs/index/relevant owned-test setup and actual diff identities; do NOT load all195KB/history/sourcebooks by default. Measure task/transitive reads.

## Allowed paths and scope
First commit exact Root order/active plus FOURTEEN immutable Rootrecords from audit/007-f-root-records.json and that index itself ->oap/reviews/007-f-root-records.json. Source records live STRATEGIC root, targets repository. No private runtime/STATE/FIFOs/permits/weights. Then TWO --no-ff merges in exact order above, preserving actual parents and clean merge-tree at each actual NEW transcript/intermediateparent. Final17productblobs/hash mustmatch index; preserve all parallel orders/addendum/SELFreports/history unchanged. No alternate source transplant/conflict resolution/rebase/cherry-pick/force/reset/clean/stash. Any conflict preserves state and reports exact evidence.

Imported17 source/test/API bytes are IMMUTABLE. Only subsequent small CURRENT docs README.md, STATUS.md, TESTING.md, docs/embedding.md, docs/UNCERTAINTIES.md; oap/governance/CONTEXT-BUDGET.md/MANIFEST.json only measured doc-hash updates ifneeded. T16 compress within existing footprint/50000 aggregate; no law/sourcebook/projection edits or refresh. No CI/workflow/dependency/profile/helper/worker/backend/source adaptations. New local CPUv2/GPUprofile/rawbackend lanes remain OUTSIDE this task.

## Non-goals
No defaultbranch merge/numeric008; no actual ML/framework/Tensor/model/checkpoint/GPU/physical probe/service/credential/private corpus/SSH operation, weights/permits/secrets inGit, current-policy implementation, retry/reclaim/mode-controller/exclusiveGPUbulk/search/API feature. No deployment/tag/release/auto-merge. A cooperative kernel key does not prove physical exclusivity or grant runtime authority.

## Acceptance criteria
1. Exact ordered candidate ancestry/clean actual-parent merge trees and17indexedblobs after merge/tests/currenthead; original ROOT/order/active/14records plusindex remain byte-identical. All other code/deps/history untouched except prescribed transcript/docs.
2. Job acquisition/entry/close attempts every owned descriptor finitely across failures, preserves original non-Exception interruption, otherwise newcleanupinterrupt outranks ordinaryerror; stickyUNKNOWN/actualcleanupowner reaches sanitized journal and producer errors even beforeclaimreturns. No blind reclose of a reused number, including SAMEinode open description; no false clean idempotence or auto-reclaim. Temporary journal/read cleanup and independent safe attempts remain honest.
3. Producer retains actual pending native/model resource and journal lease until drain; no lost owner or cleanupinterrupt relabeled ordinary refusal. Existing current-provider callback/plan/receipt/output-before-COMPLETE/freshreuse/ambiguousCOMPLETE semantics preserved; it is NOT actual current rights store. Isolated context-exit follows same interruptpriority. These finite fixes are not guaranteed kernel reaping, restart recovery or fullICA.
4. Device lease key binds ONLY versioned host+physicalUUID under actual trusted common localroot; different jobs contend, own process/fork/metadata guards and pending uncertainty are honest. Caller must verify real assigneddevice/occupancy/currentrights and drain futureworkers before release. Differentroots/noncooperators/restarts are not coordinated; no actualGPU lifecycle implementation claimed.
5. Preserve semantic/native0.21.4/legacyCPUintent identities. Selected source hashes/complete execution fingerprints naturallychange; prediction/observed handshake/sourcejob matching stillworks, no hardcoded oldvalue. Legacy CPU2.10/4.51 profile remains UNQUALIFIED and unchanged; no new CPU/GPU profilecutover or neuralpermit.
6. Correct CURRENT docs security-severity wording: docs/embedding.md incorrectly says high/medium on BOTH pins. Actual GitHubTorchScript advisory is LOW; Transformers list includes4HIGH plusmedium/low. Cite exact committed Rootobservation, no unqualified vulnerability-absence/legal/security claim. Report peerB as independent original CHANGES_REQUIRED evidence plus Rootlocalremediation, not a completed new ICA or human adjudication.

## Verification and negative evidence
Actual focused6unit files: embedding_job_ownership, gpu_device_lease, embedding_job_journal, cpu_embedding_producer, isolated_cpu_embedding, cpu_embedding_plan; actualcounts govern (Root105 atcomposedtree). SIX SEPARATE standalone integrations same names plus _composition (Root39); parent/source/unit/int PYTHONPATH exactly qualified per necessary transitivefixture, don't confuse collection or combinedfiles with standaloneproof. No actual framework/CUDA import; fakeprovider and real ownedfiles/native/kernelprocess protocols only.

Inspect then run TEN original Rootscripts at current canonical with unchanged17 source hashes before/after: /tmp/raggedized-root-isolated-exit-priority.py, producer-secondary-interrupt.py, journal-cleanup-boundaries.py, producer-lease-interrupt.py, native-close-ownership.py, native-interrupt-priority.py, gpu-lease-registry.py, job-ownership-boundaries.py, job-enter-failure.py, job-interrupted-close.py (all subsequent names share /tmp/raggedized-root- prefix). All originally causal failures nowmustpass; no weakening witnesses or sourcepatching to forcepass. Existing multithreaded-fork warning remains no genericfork-safety proof. Full unit/integration, productlint/compile/diff, OAP41/check_state/budget/source-copies, consolehelp/doctorhonest, exact current GitHuballrequiredjobs/steps. Use uv run or explicitly prependproject.venv/bin to PATH for installedCLI tests; direct interpreter alone didnotprovideconsolelookup inE. Failures are evidence: diagnose selectedlogs/cache/setup, no skips/futureCI claim/repeatentiresuite merelytoidentifyfailednames.

## Runtime and protected resources
Existing cached parent/app NumPy2.5.4, threads1, focused<=1GiBAS/30CPU/120wall AFTERuvstartup; fullsuites approvedDEV bounds. Standalone3.12root /home/janezp/.local/share/uv/python/cpython-3.12.15-linux-x86_64-gnu, native /tmp/raggedized-root-native-setup-b-6cd8bebe0a/packages with SLAIF_NATIVE_TEST_PYTHON=python3.12; OLD CPUfake /tmp/raggedized-root-cpu-synthetic-56cdd5b2898d3d17/packages via SLAIF_CPU_WORKER_TEST_ROOT/PACKAGES. PDF_TEST_RUNTIME same3.12root, PDF_TEST_PACKAGES=/tmp/raggedized-root-pdf-setup-20ca62cd48/lib/python3.12/site-packages. Set named variables explicitly; no newlocalpackages/metadata/runtime changes or actual neuralcalls. Existing CI sixlightfixture step stays byte-identical. No oldtoypermit transfer or humanmodel/profile/auth/pane changes.

## Documentation
CurrentF exactintegratedbehavior/limits and17identity proof, explicit originalpeer finding/remediation, accurate profiles/advisoryseverity, cooperativevsphysicalownership/currentrights, unknowncleanup/refusal/finiteprocess limitations and unchanged fullMVP gates. No history/report rewrites/queue percentages/fullclosure/humanowner referralbehavior. Unknown actualmodels/security/license/hardware/parity/current-policy/visual/heldout/ICA remainOPEN.

## Deferred human adjudication

- Decision: NONE

## Publication and report
Root owns exact source/review/CI acceptance/nextorders; coding boundedimplementation/Git only. Commit/push samePR9 implementation literalSHA then soleparent immutable report-only SELFreport<=7500B, actualcommands/counts/limits/docs/ROOTrecord identities and observedCI status only; whole007PARTIAL. Verify currentremote report thenONE send-response.sh --identifier007-f, finishgoal/idle. FIRST/SOLE existingorderedhelpers authorized; no duplicate/read/replay of consumedFIFOs, no newaudits/nextobjective/merge. Ordinarylaw/order/source tools before ONE optionalRootboundedgoal. All D0 work has standing mandate, no recurring humanpermission needed. No release/deploy authority.
