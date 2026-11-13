# OAP Work Order — 008-d

Status: FINAL
Identifier: 008-d
PR mode: AMEND_EXISTING_PR
Branch: oap/008-raw-hybrid-snapshots
Base commit: 322c7fe0f54e3ce53fa4550c914cd73f51525126
PR number: 10
Expected active: 008-c
Provenance: H activated full MVP mandate; E actual 008-c CI 43368073059 job 131697112168 ProcessLookupError ESRCH in existing descendant observer; A reliable bounded cleanup evidence; I Root exact 008-c source/report/failed-CI reconciliation
Architecture SHA256: 4b41905396a3838269fd6cf372614cd23cb2c3b6a37be09f29ed752803c0983a
Governance SHA256: 24cec23235e3defc5f55bab4690298191d5a233d35dd9bf20b0afb4b3925f922

## Objective

Repair the narrowly observed test-only process-disappearance race. Actual Python 3.14 CI on report head 322c7fe0 failed tests/unit/test_cpu_worker_backend_setup.py::test_timeout_kills_owned_descendant: _descendant_gone reads /proc/PID/stat and catches only FileNotFoundError, while the runner raised ProcessLookupError with errno ESRCH. Preserve the real descendant timeout assertion and prove the observer handles absence without accepting a live process or hiding unrelated errors. No product cleanup behavior changes.

## Dependencies and current state

Same objective 008 and PR10, no numeric advance or merge. Exact report SELF322c7fe0, implementationc66dfe49, transcriptf72405f7 and normal response04:51:59.102399 are independently reconciled. All25 new source blobs/15Python AST, nine Root records and prior tracked bytes were verified. Current CI is NOT green: Product3.14 failed its unit step and skipped dependent integration/governance/console steps; Product3.12 was still running at the recorded observation, three OAP jobs succeeded. No hosted rerun is authorized to hide the failure. Root failed-CI reconciliation and timing resolve only continuation routing, not development acceptance. Old report/raw failure remain immutable. Old inert scoring-008d draft/index were never activated; scoring transfer is deferred to a later suffix after this repair.

## Allowed paths and scope

FIRST one transcript commit with sole parent 322c7fe0: unchanged this order and active008-dLF, plus THREE unchanged Root records and their unchanged index from /home/janezp/codex-supervision/slaif-raggedized-helper/audit/008-d-root-records-FINAL.json. Copy each source->target and copy the index to oap/reviews/008-d-root-records.json. Index1178B SHA25624ba99d3f9a933d14aef8748bc72567031f5078e0a71ac6383c681a9e48d341f, three records5272B. Six transcript paths total: three records, index, order and active. Root owns those bytes; verify exact index/source hashes before commit.

THEN one implementation changes ONLY tests/unit/test_cpu_worker_backend_setup.py, new docs/ci-proc-observation.md and STATUS.md. Keep all product modules, tests/support setup code, other tests, CI, dependencies, profiles, architecture, law, prior reports and source books unchanged. In the existing _descendant_gone helper, accept only the two absence classes FileNotFoundError and ProcessLookupError. Keep the direct stat read, zombie observation and live-state refusal. No broad except OSError/Exception, existence precheck race, permission-error suppression, retry, sleep increase, deadline/cap change, skip or fixture rewrite.

Add deterministic tests named test_descendant_absence_errors (two errno-bearing ENOENT/ESRCH parameter cases, one read each) and test_descendant_observation_rejects_live_and_unexpected_errors (live S false, zombie Z true, PermissionError/EPERM and OSError/EIO propagate, one read each). Keep existing test_descendant_disappearance_boundary and test_timeout_kills_owned_descendant unchanged. A forged assertion that merely avoids the failing branch is not a regression test.

## Non-goals

No scoring source transfer, new application feature, production helper fix, process recovery rewrite, CI retry/skip/deselection/timeout change, new dependency/setup/install, service/GPU/credential/corpus/model action, public route, deploy/release/tag or human-owner behavior. This fixes evidence observation, not a claim of universal process cleanup or kernel behavior.

## Acceptance criteria

1. Exact same PR10/branch/322c7fe0 base; transcript first with only enumerated Root bytes, active/order; one three-path implementation; sole-parent report-only SELF. No unrelated tracked changes or report rewrites/reset/clean/stash/rebase/force push.
2. Exactly the narrow observer exception fix plus deterministic errno/read-count/live/zombie/unexpected-error tests. Existing owned parent/descendant timeout test remains intact. Product setup.run and cleanup implementations unchanged; a process that remains running still fails.
3. ONE focused local pytest process as below, all five expected cases pass with retained exact preflight/argv/env/current test/support/runtime identity, private guard/raw outputs/GNU time/exit. No full unit module or unrelated tests: other module tests require explicit capsule fixtures and are covered by unchanged hosted CI. Failure stops before retry or expanded diagnostics.
4. New doc and STATUS explain actual old314 failure, observer-only fix, exact local evidence and current final-head CI status. Do not mark 008-c retrospectively green. No whole008/MVP/model/scale/rights/license qualification or closed ICA claim.
5. One final report-head push; unchanged normal hosted matrix must run every required job/step and complete full unit/integration BOTH3.12/3.14. Pending/skipped/cancelled/failed are not green. Root observes after the one normal response; coding finishes bounded goal and idles. No future-CI claim or self acceptance/merge.

## Verification and negative evidence

Use existing /tmp/slaif-scoring-test-assembly-setup-v2-20261113/venv/bin/python, pinned in preflight. No install or environment change. The focused test file imports only stdlib, pytest and its actual tests/support/prepare_cpu_worker_test_backend.py via its current-checkout path; it does not import the application. Existing editable application origin in that venv belongs to another isolated worktree and MUST NOT be used or represented as current application execution. Verify test/support code origins are this canonical checkout. No PYTHONPATH/path override/fake module.

Exactly ONE pytest process: -m pytest -q -p no:cacheprovider followed by these four node IDs in tests/unit/test_cpu_worker_backend_setup.py: test_descendant_disappearance_boundary, test_descendant_absence_errors, test_descendant_observation_rejects_live_and_unexpected_errors, test_timeout_kills_owned_descendant. Expected five cases (two absence parameter cases). CPU10 seconds, AS1GiB, hard wall30 via timeout --signal=KILL, CPU affinity0; OMP_NUM_THREADS/OPENBLAS_NUM_THREADS/MKL_NUM_THREADS/RAYON_NUM_THREADS/NUMEXPR_NUM_THREADS exactly1; no PYTHONPATH/VIRTUAL_ENV, disable bytecode, fresh owned0700 /tmp/slaif-008d-proc-observer-proof-20261113 TMPDIR. Closed benign environment, no inherited secret dump. New metadata setup/install/native/model invocation is not authorized.

The sole existing owned-descendant test runs the known literal stdlib parent+child sleep code, timeout0.7 and observation budget2; only those two owned Python children are permitted. No other selected test may launch a process. Preserve literal test code and limits. Preflight exact driver/source test/support script/config/tools/interpreter/pytest and selected runtime identity, argv/env/caps BEFORE exclusive durable attempt guard; retain split stdout/stderr/GNU time/exit, fsync records/directory, propagate nonzero. No aggregate resource or guaranteed arbitrary-descendant cleanup claim. Stop/preserve/regular blocker on any failure; no retry, leftover-process guess or unrelated PID kill. Optional static checks CPU5/AS256MiB/wall30/five vars1/no bytecode.

## Documentation

Only the new narrow CI observation note and current STATUS update. Keep source/data snapshots and current retrieval docs unchanged. Explain that ESRCH is an absence observation here, not authority to suppress arbitrary OS errors. Preserve all original CI artifacts and current readiness gates. No new routine context.

## Runtime and protected resources

Live authorization NONE. One finite owned local process proof above and existing disposable hosted CI only. No model download, package setup, GPU/service/private corpus/credential activity or public exposure. Preserve human Qwen3.8-27B/A100Q8/xhigh/profile/auth, other panes and branches. Coding owns implementation/Git and cannot merge or choose next scope. Sole wrappers own control/response; no manual FIFO read/replay or duplicate readers.

## Deferred human adjudication

- Decision: NONE

## Publication and report

Before activation Root reconciles actual quiet goal-complete coding pane, exact clean322c7fe0, unique PR10/main/head, current failure/source/timing, runtime and unchanged automation; publish order then active under lock/read back and start one original helper pair. One immutable concise report target6000B hard8192B, implementation literal40 SHA and SELF, PARTIAL whole008, exact scope/cases/caps/raw witness identities, preserved old failure and honest current CI. Prior all35/40/count or source-transfer reports remain unchanged. Root must independently review current final head and all required jobs/steps before any further development gate. Strongest objection: broad absence handling could mask a live-process bug; deterministic live/error regressions plus the preserved real timeout test and full current CI are mandatory. No merge/deploy authority is delegated to coding.
