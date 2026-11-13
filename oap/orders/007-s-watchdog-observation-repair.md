# OAP Work Order — 007-s

Status: FINAL
Identifier: 007-s
PR mode: AMEND_EXISTING_PR
Branch: oap/007-embedding-pipeline
Base commit: c1bcba4666d184689e6d8cdf47e42ceea3667db9
PR number: 9
Expected active: 007-r
Provenance: H active full-MVP delegated development; A ARCH8/11/13 isolation/recovery and exact report protocol; E actual CI43311410951 watchdog procstat ESRCH race and published R strict-metadata refusal; I reviewed local watchdog87be/SELF8b096, oppositef1bc and Root failed-format recovery V3/oppositeae70
Architecture SHA256: 4b41905396a3838269fd6cf372614cd23cb2c3b6a37be09f29ed752803c0983a
Governance SHA256: 24cec23235e3defc5f55bab4690298191d5a233d35dd9bf20b0afb4b3925f922

## Objective

Repair the watchdog TEST's interpretation of an owned process disappearing during a /proc read. Preserve worker identity/ownership, paused-parent expiry, actual timeouts and cleanup. Publish a normally strict-valid new S report. This is a bounded same007 test-harness continuation, not a production watchdog change or acceptance of malformed R. DHA NONE.

## Dependencies and current state

Current unique OPEN/nonDraft PR9 branch/main, auto-mergeOFF, main11badc7782bed326995d400f5532b63399b91fbd. Exact RSELF c1bcba4666d184689e6d8cdf47e42ceea3667db9 soleparent270d4156c4bf813a12e58c32cdd638ddb1ca35d0; report7426B SHA cf716a628f7e51373845bc8151e5907e5684b490135c5675c1cf4afc7f68ddf6. Rsource/transcripts/eightgatewaycomponents82739B+STATUS reviewed; CURRENT RCI43315535020 all5jobs/all78actualstepsSUCCESS, no reviewthreads. Nevertheless Rreport's Implementation head SHA field has a parenthetical; canonical verifier REFUSED Full literal Git object ID required. Rootaudit/007-r-review.json REJECTED_REPORT_FORMAT_WHOLE007_PARTIAL and timing recorded; coding terminal regular receipt8843B, goal/task complete. No normal R OK was sent or consumed; do NOT fabricate one, amend R report or replay any old FIFO.

Root alone owns the EXACT one-time operational failed-format transition, independently reviewed V3 source19102B SHA47bc852c3d63b6f6f9c00441adeb5f3167dee1e58d9ce12052ea022fe0422f93. It preserves R history/strict parser, independently verifies all prior graph/CI invariants and publishes ONLY exact S order/active atomically after frozen approval/current-state gates; no FIFO IO. Original R sole waiting response reader3861339 was retired via pidfd only after exact identity/terminal evidence. Root actual intent/result regular files in .oap-state certify only publication, not acceptance. CODING MUST NOT execute/recreate/relax this Root-only procedure. New S normal control/strict report/response helpers apply unchanged. Whole007/MVP stillPARTIAL.

## Allowed paths and scope

FIRST ONE transcript commit, soleparent roundbasec1bc, copies exact FINAL order to oap/orders/007-s-watchdog-observation-repair.md and exact active007-s+LF, all18 frozen Root records from audit/007-s-root-records.json (69274 source bytes) unchanged to indexed oap/reviews targets, plus exact index to oap/reviews/007-s-root-records.json. Index4895B SHA4a7cbbf57386dafc00b0c2e192f7214aa1047ad6f077ee33a6afa689e2bad4a1. Verify every source/target/size/hash, no Root-byte edits. Archival helper source target is TEXT ONLY; never execute it. Root records need identity/copy checks; use relevant concise Root review as context, no repeated full semantic reading of archived operational source/history for coding this test. Preserve task-local readset and honest source/range measurements.

Then ONE implementation selectively copies EXACT TWO files11871B indexed audit/007-s-watchdog-components.json from immutable SELF8b0961736389c0bcd00827e2a48fb31439c99494 / impl87be2e8f8558e648790af33201de26536f9f633e. Existing replacement ONLY tests/integration/test_cpu_embedding_worker_composition.py11031B SHA79b98fb99f30751604b5a31640ab5d31a6dce4e7ebb34ed299a348fee9390c97; NEW docs/parallel/watchdog-proc-disappearance-test.md840B SHA3562e4da37e776d8024c58dffdcb8dd905f1b71dd1183f0d368b3d21f8c99d7b. No parallel order/report or whole-branch merge/cherrypick. Additional ONLY concise STATUS.md current-S/scoped-evidence paragraph. Total implementation THREE paths. All production source including gateway f8a686590e0b91f0f367327733cb7c0b02131ed2fa650de6695e5a9e717ea5bd, worker/profiles/locks/architecture/CRITICAL/TESTING/governance/deps/CI remain byteexact.

## Non-goals

No production/model/gateway behavior, timeout increase, worker ownership relaxation, source/rights/hardware/quality qualification, capture/repair integration, numeric008 advance or mainmerge. No Rreport rewrite, duplicate Rreport, lenient parser, manual OK, old-reader recreation, root recovery implementation or changed model/profile/auth. TESTING.md17448B/b84fd5c63384bd3a3778599d19f87cf916f567a82e3a64865b4279f6ae6eea8f and governance/routine readset49999/50000B preserved; no law refresh.

## Acceptance criteria

1. TWO copied files byteexact. _proc_read catches OSError only to return None for errnoENOENT/ESRCH; every other error propagates. Children/cmdline/exe/stat consumers retain successful-content parsing/worker identity and only treat absent owned /proc reads as disappearance. No arbitrary exception swallow or unknown PID ownership. Default-collected deterministic new node exercises both disappearance codes/live value/EACCES/EPERM/EIO. Existing ownership/nonempty descendants+workerPIDs/SIGSTOPparent/5-second watchdog/8-second pending window/finalcleanup assertions unchanged.
2. ONE exact local process runs TWO named nodes from the same integration module: test_proc_read_disappearance_and_errors and test_watchdog_expires_while_owned_parent_paused. Cached .venv/bin/python3.14 only; unset PYTHONPATH (module's established src/tests-unit imports), SLAIF_CPU_V2_TEST_ROOT=/tmp/raggedized-root-cpython312-portability and SLAIF_CPU_V2_TEST_PACKAGES=/tmp/raggedized-root-cpu-v2-portable-485fc687/packages; allfive threadvars1/no bytecode/private0700 directtmp+basetemp. CPU30/AS1073741824/wall120 EACH parent process; native child existing limits/5s watchdog unchanged, not aggregate hardCPU cap. Exact source/command/env/setup/hashreadset/preplan and stdout/stderr/exit/resource records before/after. This exact one owned synthetic-OS case plus cheap node is preauthorized by this order; no new separate budget permission needed. No model imports/inference/downloads/extra fixtures/network. Preserve unexpected failure/stop further actual tests/notify Root before a revised plan; no blind retry, capraise, skips or timeout/CI weakening. No broad predecessor/parity/native test replay. Current normal fullCI still required separately.
3. Focused Ruff/AST/diff on changed test and exact three-path/gateway/profiles/TESTING/manifest preservation checks. Report actual collected counts, failures and current sources; TWO is a forecast, not a count to invent. Strongest counterargument: finite synthetic OS positive plus injected errors doesn't reproduce arbitrary GitHub races or qualify production watchdog/neural/hardware/currentrights.
4. Before report COMMIT, validate its actual bytes through imported oaplib.metadata and oaplib.commit_id(R,metadata['Implementation head SHA']); require this metadata value equals current40hex implementation HEAD with NO commentary, and Report publication commit exactly SELF. All commit-ID header fields must be bare40hex; parent/explanation belongs only in BODY. Assert <=8192B, metadata identity/branch/PR/result, no duplicate fields, soleparent/reportonly plan. Do not rely on a hand-written parser or only post-push checks. Preserve local invalid draft/correct before publication if rejected; no published report rewrite.
5. Commit one immutable S report, soleparent implementation/report-only. Push ONLY the final REPORT HEAD once (including prior local transcript/implementation) to existing branch/PR9; do not push or wait on intermediate heads. Then use ORIGINAL unmodified strict verify_report/normalrespond helpers on S. CURRENT S REPORT all5requiredjobs and EVERYactualstepSUCCESS required, no skip/pending/cancelled acceptance or auto-merge/bypass. Terminalred: preserve exacthead/run/job/failedstep/logs/postpublication receipt, notify Root and ONE original normal report-ready response explicitlyNOTacceptance, no unrelatedpatch. Wait<=60seconds; do not keep background shell loop for 60 iterations after terminal state. AFTER ONE response complete boundedgoal andidle immediately; no redundant postresponse audits. Unexpected published-format error: preserveimmutable report, regular blocker toRoot, no manualFIFOOK or edits.

## Verification and negative evidence

Actual failure43311410951 Product3.12 integration step17 /procstat ProcessLookupError outside Rscope, latercurrentR78stepsgreen; classified intermittent observation/test harness race, not broad reliability proof. Local candidate Rootsource/oppositef1bc reviewed all preserved assertions; original v1 proof plan never invoked, v2 exact original-cap ONEactualOSproofPASS6.19wall1.02user.11system/RSS55864KiB. Root independent deterministic node PASS.74wall. Author cheap raw output not retained, report attributes transcript and Root independently retained proof honestly. New canonical two-node process/current S CI required; old proof not claimed new execution.

## Documentation

ONLY concise STATUS current-S paragraph plus exact copied API doc, preserving Rfailedformat/currentgreenCI distinction and whole007/BGEUNRUN/UNQUALIFIED gates. Root archival recovery records and report carry protocol/history, no TESTING law-budget edits or oldreport changes. No human-owner/referral/contact behavior added.

## Runtime and protected resources

Preserve human Qwen3.8-27b/A100Q8/xhigh/provider/profile/auth and existing authorized roots. No otherpanes/nestedagents, reset/stash/clean/switch/rebase/cherrypick/forcepush, newinstalls/large downloads/credentials/SSH/gateway/model/GPU/service/realdata/publicexposure. Syntheticowned OS only named above. OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 RAYON_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1. Scoped fixtures borrowed and preserved; all model/PDF/currentrights/heldout/latency/license/hardware/fullICA gates remain open. Reference gateway repo untouched. Root alone controls operational recovery, source/order/active bytes, developmentacceptance and futuremerge; coding only normal S work/protocol. No FIFO rereads/replays/duplicate readers.

## Deferred human adjudication

- Decision: NONE

## Publication and report

Exact18records/order/active/index transcript first; exact TWO candidate files+STATUS implementation; precommit actualmetadata bare40 validation; immutable soleparent SELF/report-only; one push of finalhead; original strict remote verification; CURRENT allCI/ONE originalresponse; goalcompleteidle. Root records independent review/timing before nextsuffix. Capture now prospective T and explicitrepair U remain inert (historical S/Tdraft aliases retained); full007 sourcecoverage/replan/ICA required before numericadvance or mainmerge. No release/tag/deploy authority.
