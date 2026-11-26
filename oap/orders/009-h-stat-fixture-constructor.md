# OAP Work Order — 009-h

Status: FINAL
Identifier: 009-h
PR mode: AMEND_EXISTING_PR
Branch: oap/009-evaluation-baseline
Base commit: 857355abbcfc4f5e322377f2bbee1388bafafc56
PR number: 11
Expected active: 009-g
Provenance: H standing full-MVP development; E current CI43931502904 failed; I Root exact diff/log/stdlib value review; A meaningful provenance regressions and complete unfiltered verification
Architecture SHA256: 4b41905396a3838269fd6cf372614cd23cb2c3b6a37be09f29ed752803c0983a
Governance SHA256: 24cec23235e3defc5f55bab4690298191d5a233d35dd9bf20b0afb4b3925f922

## Objective

Correct the confirmed constructor error in the new broad-session origin-metadata regression, preserve all provenance checks and test nodes, and verify the focused unit suites before another report-head CI. Same numeric009 and PR11, not acceptance or feature work. Root reviewed the original normal response at18:49:39.126355Z, remote current head857355ab/main5a7b41cc, exact six-path transcript a60a04d7, three-path implementation9b3622ce and report-only SELF857355ab. Report8180B SHA256aefda76ced8adec5da6b57c5575388a0e16887f7ce041266b7cd700227fb27d0 remains immutable. Root resolution audit/009-g-resolution.json records FAILED, not accepted; checkpoint/009-g-implementation-aecf3ac remains preserved. Reconcile live state again before activation/work.

## Dependencies and current state

CI run43931502904 has three successful OAP jobs, two failed product jobs, 78 required steps:64 success/2failure/12skipped. Product3.12 job133524822329 fails in fake_stat at line96: os.stat_result(*values) expands ten fields into ten arguments, raising TypeError; pytest error rendering then hits the same monkeypatch and INTERNALERROR. Product3.14 job133524822987 shows one F and later exit137 without completed traceback/summary: its precise cause is UNPROVEN. Do not claim OOM, identical traceback or successful full unit count. Integration/downstream skipped is not green. Retain both failed decoded logs; do not retry old runs. Root's isolated standard-library synthetic value witness confirms expanded-ten-fields TYPE_ERROR and single-sequence st_size3145728; it is neither a product test nor CI acceptance.

## Allowed paths and scope

Only THREE implementation paths: tests/unit/test_evaluation_program.py, docs/evaluation.md, STATUS.md. Test preimage24446B SHA256085f0cea1a05a26cbdced09ec8b0b7e4c9980f6995bbd80f2c306d2635cc1598. Make ONLY the unique byte substitution `return os.stat_result(*values)` to `return os.stat_result(values)`. Expected resulting test24445B SHA25659f093b45a471e04ac21ad555643c6899cac3d972c47e1aea4756904525b39b0. All50 default-collected nodes (44original+6new) and every other byte of this test remain unchanged. Preserve test-scoped restoration, distinct real local file witness, strict global origin checks, negative cases and no global source-size sum. No format rewriting, added tests, skip/xfail/filter, sys.path/sys.modules product/test patching or fake packages.

The two current docs add a concise attributed009h record:009g failure, confirmed3.12 constructor defect,3.14 exit137 cause unproven, actual NEW bounded verification result only after it runs, and new report-head full CI pending at publication. Clarify old98focused units used old test593a3be6 while program/runner remain same; never rewrite historical reports or treat regression intent as a pass. Keep real baseline NOT_RUN and all operator/currentpolicy/encoder/data/rights/plan/publisher/nativeOS/20k/hardware/visual/security/license/mergedICA/MVP/release gates open. No inferred bwrap owner/liveness or worker fix.

Program SHA25684aceffc09ec7e53fcf96913ad0cb409616b31223d71915e60fbd750300b9b90 and runner SHA256d9f1b0e8f748be9c5b32b6e6d45e8228ace43b397517a41e6187638d4c296faf remain exact, as does every other existing path outside the three allowed implementation paths and explicit transcript/report paths. No config/dependency/workflow/law/provider/model/profile/auth/service changes, no new worktree/branch/PR, no reset/clean/stash/switch, no merge/release/deploy.

First commit the FIVE transcript paths, sole parent exact base857355ab: unchanged FINAL order at oap/orders/009-h-stat-fixture-constructor.md, active009-h plus LF, TWO exact Root records per audit/009-h-root-records-FINAL.json copied to its named targets, and exact index at oap/reviews/009-h-root-records.json. Index749B SHA2566981d295c0a26c390f107aac2ccd9571b188d55133fe87ad27848e8bfebff40c; two records3143B. Verify source size/hash and exact target bytes; index metadata supplied by Root, not invented. No raw CI logs, private host paths/process maps or other lane artifacts in Git. One implementation commit sole parent transcript, then one immutable report-only SELF sole parent implementation: NINE round paths total. No intermediate push/amend published history or report rewrite. Unpublished checkpoint refs may preserve review iterations.

## Non-goals

No feature, algorithm, worker, policy, parser, publisher, workflow, dependency or runtime configuration change; no source proof, native/model/fixture journey, real corpus/credential use or hardware qualification. Local execution awaits the separate exact Root decision below. No old CI retry or weakening of the full unchanged suite.

## Verification and negative evidence

This order authorizes the exact source fix and STATIC preparation of ONE finite focused-unit proposal. It DOES NOT yet authorize any local product invocation, lint/format/test/import/collection/setup/native/model execution. Before implementation commit or report, stop at a regular-file review request under strategic audit/009-h-check/ with exact proposed source/test/doc hashes, source readset, installed environment identities and a frozen actual parent launcher. Notify Root; await separate exact regular-file Root decision. No FIFO for this checkpoint, no new consumer. Do not mistake this staging gate for human permission or stop independent static work.

Prepare ONE unit process, same two full unit files tests/unit/test_source_cohort_runner.py and tests/unit/test_evaluation_program.py, expected54+50=104PASS, no skip/xfail/xpass/filter. Use existing /tmp/slaif-pinned-query-setup-20261113/venv only; no setup/download/environment mutation. Proposed command: its bin/python -m pytest -v --assert=plain -o addopts= -p no:cacheprovider with the two explicit files. No formatter, no local Ruff needed for this one-character change. Proposed limits:CPU20seconds/address-space1GiB/wall120seconds/core0/file16MiB/CPUaffinity0/threadvariables1. These are proposed ceilings, not invocation authority; Root reviews actual environment/launcher/readset before decision. One attempt, no retry/cap increase after failure.

The old parallel/evaluation-core/check-proposal.json and check_launcher.py are REFERENCE ONLY, not current permission and contain obsolete moved worktree paths. Do not execute them. Freeze current executable resolution/hash, pyvenv.cfg, installed pytest/required dependencies, executable .pth targets and sitecustomize/apport hooks where exposed; preserve human settings. Explicit canonical src and tests/unit search paths must take precedence over the old editable .pth worktree and all actual loaded product/test origins must satisfy the unchanged test origin invariant. Avoid claiming a normal pytest startup is stdlib-only or its whole OS/native/package closure measured. Provide static measured transitive local source inventory, repeats/estimates/unknowns, not a fabricated exact dynamic-read certificate. The old2MiB stat proxy is not restored into the default suite.

Freeze a closed environment with private fresh0700 direct /tmp HOME/TMPDIR/cache, plugin autoload and bytecode disabled, deterministic hash seed and thread variables1. Launcher must validate exact source/environment/proposal identities, exclusively create one attempt receipt/log/result, start only the owned unit child, enforce wall timeout and directly reap it, retain complete combined stdout/stderr/resource/return receipts on failure and stop. No shell timeout child chains, broad scans or signalling nonchildren; no silent cleanup failure or numeric FD retry. No source/native/model/fixture/generator subprocess or GPU/service/network access in this focused check. Failure or unexpected imported source needs regular blocker and explicit replan; no hidden retry. Successful focused units cannot replace full CI or qualify the source proof/runtime/baseline.

## Acceptance criteria

1. Exact previous normal/current PR/base/order/source/report identities and unchanged five-path transcript; three-path implementation and report-only graph, no unrelated dirty adoption.
2. Exact one-character test correction and expected hash, all50program/54runner nodes preserved, no production/code/algorithm change or weakening.
3. Root independently reviews frozen proposal/source/environment/launcher and records a separate exact bounded decision BEFORE one local unit process. Preserve every attempt, result and uncertainty. Root must review result/post-run identities before coding commits the implementation or publishes report. No report/checkpoint publication to bypass this gate.
4. Current docs distinguish009g failed evidence, old exact-source evidence and NEW local/currentCI evidence, no future result or qualification claims.
5. After Root local-result review, coding completes immutable implementation/report graph and one report-head push, then actual normal response. New unchanged FULL hosted product/integration3.12/3.14 plus all three OAP jobs must succeed at current head for development acceptance. Missing/skipped/pending/cancelled/failed is not green. No workflow edit, test filtering or old-run retry. Root owns new-head source/report/CI/review-thread evaluation and continuation.

## Documentation

Semantic coding allowance256KiB including repeated/helper/own verification source reads; measured compact transitive inventory plus explicit estimates/unknowns. Do not reload whole books/history or certify source closure from token conversion. Reading the old focused proposal does not import its allowance. Local unit runtime readset/accounting is separate and frozen in its proposal. Root authors scope/decisions; coding owns implementation/Git. Only the two named current docs receive the precise evidence record described above.

## Runtime and protected resources

Static source/preflight preparation only until separate exact Root unit decision. No other local execution or protected service/data/model/hardware access. Preserve original signals/readers; next sole control/response wrappers only after verified completed009g handles and live pane/current roots. Native fresh-context startup must preserve human model/profile/auth; ordinary role/order first, then one bounded goal, never goal-first or nested agents. No extra worktree or client restart.

## Deferred human adjudication

- Decision: NONE

## Publication and report

Result PARTIAL whole009; report soft6000B/hard8192B, exact implementation/SELF/PR/source/verification/read ledger, preserved failure and all open gates, no future CI certificate. After strict remote verification invoke actual helper ONCE: python3 oap/bin/oap.py respond --repo-root /home/janezp/codex-work/slaif-raggedized-helper --runtime /home/janezp/codex-supervision/slaif-raggedized-helper/runtime.json --role CODING --identifier 009-h . Chat OK is not response delivery. Existing response-send receipt means reconcile without replay; never read a FIFO or start another reader. Preserve human Qwen model/profile/auth and other panes/worktrees. Remain idle after actual normal response. No numeric010 advance, acceptance, merge or release authority.

Strongest counterargument: another tiny fixture repair could consume a full CI cycle without establishing the regression. Exact static source review plus a separately frozen focused104-unit execution before publication catches the concrete constructor error while preserving the required full suite as the broader evidence boundary. Python3.14 exit137 stays unproven until new evidence; it is not silently declared fixed.
