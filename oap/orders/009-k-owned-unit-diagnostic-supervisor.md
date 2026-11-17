# OAP Work Order — 009-k

Status: FINAL
Identifier: 009-k
PR mode: AMEND_EXISTING_PR
Branch: oap/009-evaluation-baseline
Base commit: cc51b9a9a3eb478b3812bb3295459172bc5882b7
PR number: 11
Expected active: 009-j
Provenance: H standing full-MVP development; E 009i and009j annotated20m product-job cancellation with no usable logs despite009j180s/10s wrapper; I Root exact report/normal/CI/jobs/steps/annotations/log/remote review; A honest complete verification and owned execution
Architecture SHA256: 4b41905396a3838269fd6cf372614cd23cb2c3b6a37be09f29ed752803c0983a
Governance SHA256: 24cec23235e3defc5f55bab4690298191d5a233d35dd9bf20b0afb4b3925f922

## Objective

Make whole-unit CI diagnostics observable through an owned standalone stdlib supervisor, without giving test children the GitHub runner output pipe. Keep full suite, order, matrices and every downstream gate. This is same numeric009/PR11, not a speculative product repair, test reduction or acceptance. Root resolved009j CANCELLED_NOT_ACCEPTED in audit/009-j-resolution.json. Runtime cause remains UNPROVEN; an inherited output writer is only a hypothesis. Diagnose it rather than asserting it happened.

## Dependencies and current state

Exact report-only SELFcc51b9a soleparent implementationa0575b2 soleparent transcript10a2e03; report5986Bf964a57a independently reviewed and normal23:18:04.368659Z. Run43978029330/run133/attempt1 completed CANCELLED23:42:50Z. All3 OAP jobsSUCCESS; product3.12job133686949905 and3.14job133686950403 CANCELLED, both annotated exceeded20m0s. Terminal metadata has76steps:60success/2unitsteps stillin_progress/14downstreampending; two usual Completejob steps absent. Both connector productlogs404BlobNotFound; one gh312 fallback returned0+0bytes, not successful execution evidence. Earlier009i and009h137 causes unproven; Root104 focused units from009h are separate, not fullCI substitution. No oldrunretry/cancel. Root raw evidence audit/009-j-ci-terminal remains outside Git.

Canonical tree CLEAN/currentheadcc51, exact branch/main5a7 and uniqueopenPR11, zero reviews/threads atterminal review, noautomerge. Oldresponsewrapper4042801 absent; %30 verifiedquiescent/oldgoalachieved during this continuation preflight with humanQwen preserved. Reconcile actual state before acting. Do not reset/clean/stash/switch/create worktrees. Independent parser/publisher lanes retain their own orders; no transfer from them here.

## Allowed paths and scope

Exactly FIVE implementation paths:
1. NEW oap/bin/ci_unit_diagnostics.py — private CI execution utility, no product/operator API.
2. NEW tests/oap/test_ci_unit_diagnostics.py — default-discovered meaningful unittest cases for the utility.
3. .github/workflows/oap.yml — change ONLY unique Product test suite run block to invoke the utility through the selected matrix Python. All other bytes unchanged.
4. docs/evaluation.md — concise current009k evidence/limitations.
5. STATUS.md — concise matching status.

Workflow preimage14317B SHA256fc1ba2cd062ae5d314dc480bb2f2270834a7c22b9a2937fa9afc4b430101655d. No changes to existing test code, product source, lower helpers, dependencies/actions/setup/job caps/permissions/triggers/matrices, integration/OAP/governance/help/doctor gates, docs history or law. New default OAP utility tests extend existing discovery; never filter or replace old tests. No new installed dependency or action. No artifact upload/network/model/corpus invocation. Keep historical source/status claims accurate; no actual full-suite PASS until fresh-head evidence.

First transcript commit FOUR paths: unchanged final order oap/orders/009-k-owned-unit-diagnostic-supervisor.md; oap/active009-k+oneLF; exact Root resolution oap/reviews/009-k-prior-resolution.json; exact Root index oap/reviews/009-k-root-records.json copied from audit/009-k-root-records-FINAL.json. Index binds the sole3866B prior-resolution SHA256b3437f032249fc76cfd339703a45b9a8321a58d6cac309c62edafd7ad4f8e95c. Do not reconstruct Root prose. One5path implementation soleparent transcript, then immutable report-only SELF soleparent implementation: TEN round paths. No intermediate push or report rewrite.

## Non-goals

No unknown-node fix, OOM assertion, skipped test, selector, test split/order change, broader unit runtime/job cap, setup/download, product/gateway/GPU/real encoder/data/credentials/service action, oldCI retry, merge/deploy/release, numeric010 or fullMVP claim. No source patch by Root to bypass coding review. Current publisher tracking repair and parser candidate remain separate and unintegrated.

## Acceptance criteria

1. Utility uses only stdlib and the already-required /usr/bin/time. Fixed production command preserves exactly uv run pytest tests/unit -o addopts= -vv -o faulthandler_timeout=60 with PYTHONUNBUFFERED=1. No shell command construction or public arbitrary-command CLI. Testable private execution function may accept explicit short synthetic commands/bounds for its own tests; production defaults cannot be changed by caller environment/CLI. Preserve the existing required fixture environment and matrix selection; never dump environment/credentials.
2. Create one private0700 owned temp child under existing RUNNER_TEMP and an exclusive0600 regular diagnostic log. Missing/unsafe prerequisite fails loudly, no install/fallback or destructive external cleanup. Test subprocess stdin=DEVNULL, stdout/stderr=owned regular file, close_fds=True, start_new_session=True. No PIPE or inherited runner output stream in the child. Parent alone forwards finite regular-file reads with bounded chunks/total4MiB; neutralize child workflow-control prefixes when forwarding (e.g. fixed per-line label), preserve raw bytes in private log and indicate any decode/truncation limit. Observed output above16MiB is failure plus owned cleanup, not a hard write-rate/host-disk certificate. No whole-file read into memory, output-EOF wait or unbounded line accumulation. Log paths/IDs need not be public output.
3. Parent monotonic deadline180s; send TERM to its owned initial group, KILL after10s; no increased child runtime. Observe direct-child termination without reaping/reusing its numeric identity until required group cleanup: waitidWNOWAIT or equivalent proven ownership-safe ordering. Teardown in finally handles normal/nonzero, deadline and observer failure, then direct reap. Bound post-KILL observation/reap attempt to5s; unresolved termination/cleanup is explicit nonzero CLEANUP_UNPROVEN, never clean success. No claim signals can bound uninterruptible kernel calls. Do not kill/reap unrelated processes, scan host PIDs, adopt descendants, use ctypes/native bridge or claim initial group covers escaped sessions. Child/group limits and waited resource observations are not aggregate-host/live-tree guarantees. A child inheriting a regular log cannot keep the runner output pipe open, but this is not proof of the old failure's cause or universal descendant containment.
4. Preserve actual child nonzero status (including pytest5) and fail on timeout/observer/log/cleanup refusal; no continue-on-error, success masking, retry or surviving-subset report. Only complete zero command with successful required supervisor teardown may return0. Emit finite own status/deadline/cleanup/resource summary even when test output is unavailable. Keep /usr/bin/time -v stream for process observations, not OOM/aggregate accounting. Avoid Popen.poll/wait reaping followed by unsafe group signal; direct owned PID remains protected until all group-signal decisions finish. Handle failing construction/launch before PID exists without inventing ownership.
5. Default unittest file must exercise actual stdlib owned children: normal0 and real regular-file stdout/stderr+stdinEOF; nonzero7 and pytest-style5 preservation; deadline termination; observer/read failure cleanup; retained extra output-handle case showing no waiting for pipeEOF (honest model, no fabricated reproduction of CI fault). Also negative launch/prerequisite/size/bound/state cases as meaningful. Tests must own/reap all their direct children; no orphan experiment, actual OOM, real signals to unrelated processes or live service. No skip/xfail/fake modules/selector-based passing set. Specify exact counts, command/process census and limits BEFORE execution. No required broad existing harness rerun locally.
6. BEFORE ANY local format/lint/import/collect/unit/probe invocation: prepare regular audit/009-k-check/review-request.json with full5path diff/hashes and exact finite verification proposal (source/test/helper/interpreter/env/readset/origins/temp/resource/lifetime/case/process census). Root first independently reviews actual code and selects an exact bounded local verification; no inherited runtime permission. Proposed one new-file unittest process CPU20/AS512MiB/wall60/FSIZE16MiB/CORE0/privateTMP/thread1, at most12 short stdlib ownchildren total/max2concurrent with individual bounded waits/teardown. These are ceilings for a proposal, not authority. Do not run product fullsuite locally. Preserve firstfailure and stop, no retry or capraise. Static Python AST parsing without evaluation, Git/hash/text comparisons are permitted.
7. After separately reviewed checks, update only own current docs evidence, obtain Root exact5path precommit approval, finish implementation/report and push only reporthead. Use original canonical respond helper ONCE. Root independently reviews report-only ancestry/uniquePR/currenthead/allrequired freshCI jobs+steps+logs/reviews. Missing/cancelled/skipped/pending/failed/blocked is not green; three OAP successes cannot substitute for product matrices. No merge here.

## Verification and negative evidence

Static exact scope/byte remainder, real helper lifecycle and privacy review, finite default utility tests under separately approved controls, actual fresh-head fullCI. Source of operational patterns: Root-owned supervision parallel/private-report-publication/Root_correction_product_check_launcher.py9184B SHAb74c381a34395fe864ffa79b4337cf7a504c1ab5fe5c2d2050c01684c497e885, especially owned group teardown before reap and observational accounting. This is an input pattern, not universal qualification or an instruction to copy product-specific arguments. Its prior normal/nonzero/timeout/observer-error qualification is separate evidence; current utility changes need meaningful own tests. Read only relevant lifetime blocks, not surrounding publisher source/history.

Any mismatch, missing tool, cleanup uncertainty or helper refusal: retain exact evidence and regular blocker, no reset or silent retry. Actual failure or timeout is evidence to investigate, not permission to narrow suite. Logs/model outputs do not establish rights, current-policy or baseline attestation.

## Documentation

Keep current paragraphs/report concise. Preserve prior cancellations, 009h104focused evidence, unit180s/10s child deadline,20minute enclosingjob cap, baselineNOT_RUN and parser/publisher/currentprincipal/policy/encoder/data/rights/operator/runtime/hardware/visual/security/license/mergedICA/MVP/release gates. Illustrative source workload is ~20k CHUNKS, not a human20k-document requirement; existing raw4096row software ceiling remains separately open. No retrospective source/physical/RSS/aggregate cap claim.

Semantic allowance256KiB INCLUDING repeats/helper/own verification. Use compact relevant source ranges and measured estimates/unknowns, not whole source books/large docs/history/worktrees. No tokens-to-bytes certificate. If insufficient, preserve remaining subset for Root. Root owns order/records, coding owns implementation/Git.

## Runtime and protected resources

STATIC initially. Separate exact local verification decision mandatory; no product/native/model/fixture/setup execution by implication. Fresh-head ordinary fullCI is the first fullunit invocation of the reviewed utility. Preserve20minute job cap, full unit set/order and all downstream gates. Preserve humanQwen3.8-27B/A100Q8/xhigh/profile/auth, current canonical checkout and other panes. Qualified fresh-context startup via original control waiter; then Root-set bounded goal for this order only. Helpers own sole FIFO readers; no read/replay/newconsumer or nested agents. No release/deploy authority.

## Deferred human adjudication

- Decision: NONE

## Publication and report

Whole009 PARTIAL. Report target3000–4500B, soft6000/hard8192. Exact implementation/SELF/PR/helper/test/source/contract hashes; commands/cases/resources/failures; oldcauseunknown; true cleanup/read/OS limits; freshCI PENDING; DHA NONE and open gates. One report-head push, then ONCE python3 oap/bin/oap.py respond --repo-root /home/janezp/codex-work/slaif-raggedized-helper --runtime /home/janezp/codex-supervision/slaif-raggedized-helper/runtime.json --role CODING --identifier 009-k. Existing response-send receipt means reconcile, not replay. Helper writes its own receipt; no custom postpush loop. Remain quiescent afterward.

Strongest counterargument: a new supervisor adds process/lifetime complexity and changes test ancestry; a plain log redirection might suffice. Repeated job cancellation with unavailable output after both verbose diagnostics and a narrowed external timeout justifies one bounded observable owned parent with meaningful failure tests. It is not a causal fix or qualification, and incomplete teardown must fail rather than make CI green. No limit increase or test weakening is selected.
