# OAP Work Order — 009-r

Status: FINAL
Identifier: 009-r
PR mode: AMEND_EXISTING_PR
Branch: oap/009-evaluation-baseline
Base commit: 416009c94a6759c9a42e9c19dab688c0f54d9650
PR number: 11
Expected active: 009-q
Provenance: H activated MVP development; A ARCH23/A24 honest evidence; E CI44672714984 wrapper exit 137; I exact source and terminal review
Architecture SHA256: 4b41905396a3838269fd6cf372614cd23cb2c3b6a37be09f29ed752803c0983a
Governance SHA256: 24cec23235e3defc5f55bab4690298191d5a233d35dd9bf20b0afb4b3925f922

## Objective

Expose the actual wait status of the unit-test process and bounded
numeric evidence of resource events in the hosted supervisor's own
cgroup. Run the complete hosted comparison under unchanged test and
timeout/cleanup policy.

## Dependencies and current state

Open PR 11, exact report-only base 416009c9 and main 5a7b41cc. Previous
round disposition is the exact Root file
`workorders/009-r-prior-resolution.json` SHA256 17943b522180dc6dc3a6b8cf76d05076b8346a4e8ff9823051deca9d83fbb31c.
Read compact audit/009-q-ci-terminal/Root-terminal-review.json SHA256
dccf70a08213a18519321b4f05cb8da6239b08866be2412e12ef07416c8003e8
and its Root-console-launch-projection.json. Avoid rereading bulk CI.

44672714984 terminal failure. Both Product legs received
OPENBLAS_NUM_THREADS=1, collected 2731 and passed the named isolated
16-slot case. Python 3.12 forwarded 2532 pass marks, Python 3.14 2505.
Different last unfinished source-stage lines, no final summary.
The direct supervised uv process exited positive 137 with no signal
field, no supervisor termination reason and no display refusal.
Both elapsed around 63s including existing cleanup. No causal claim
about a source test, OOM, scheduler or host process. Six downstream
required steps skipped in each Product leg. Three OAP jobs succeeded.

## Allowed paths and scope

Canonical CODING pane %30. Exact three-path independent transcript
with Root order, active LF and prior resolution copied unchanged to
`oap/reviews/009-r-prior-resolution.json`, sole parent 416009c9.

Implementation may touch only oap/bin/ci_unit_diagnostics.py, a small
stdlib-only oap/bin/ci_unit_resources.py, the existing tests/oap/
test_ci_unit_diagnostics.py and focused tests/oap/test_ci_unit_resources.py,
STATUS.md and docs/evaluation.md. Do not change the workflow, source
or pytest files, current package environment, prior logs or reports.
No refactor of run_child, supervisor teardown or output framing.

## Non-goals

No pytest selection changes, resource-cap workaround, ENV/PID dumps,
broader host access or alternate unverified code paths. No replacement
worker, retry of unchanged failed bytes, merge, next objective, deploy,
credentials, live product/source data or hardware work.

## Acceptance criteria

1. Verify actual clean base, previous report/receipt/CI and exact
   transcript. Preserve one same-PR, no force, no branch checkout change.
2. At main only, supervise repo .venv/bin/pytest console entry directly,
   with unchanged trailing args, absolute fixed executable path and
   exact repo cwd; require the fixed installed console before launch
   and fail closed if missing. Existing locked CI setup precedes this.
   Reproduce locally verified launch projection: same inherited env,
   repo .venv VIRTUAL_ENV and its bin as the first PATH entry. No new
   uv operation, shell, argv override or fallback. Existing run_child
   receives this explicit argv and environment and keeps all resource
   execution/ownership behavior. Have a bounded synthetic OAP check
   that positive exit 137 and real direct SIGKILL have distinct
   wait results; never signal an unowned process.
3. Add small optional own-cgroup numeric snapshots immediately before
   the launch and after owned teardown. Bounded read of /proc/self/cgroup
   and fixed local event files under trusted /sys/fs/cgroup using
   exactly one unified row and validated absolute canonical components,
   with no path scan, symlink traversal chosen by caller or path output.
   Exact mount mapping not available means unavailable. Compare the
   same cgroup device/inode and monotone bounded counter values. Report
   only nonnegative deltas for memory.events.local max/oom/oom_kill
   and pids.events.local max. Missing, malformed, oversize, unstable or
   counter-reset reports unavailable for the affected observation.
   Also record inherited prelaunch RLIMIT_CPU soft/hard as bounded
   decimal/unlimited/unavailable. No raw files or unrelated metadata.
   Wire observation only into the fixed bounded final summary output
   already owned by the supervisor. Observer availability or a delta
   never determines child status, acceptance, or which member failed.
   Preserve exact old child signal/exit and nonzero/failure behavior.
4. Cover pure bounded parsers and stable/missing/malformed/reset
   behavior with owned synthetic fixtures, no real cgroup mutation or
   privilege. Verify direct projected argv/env and clean refusal for
   missing console. Use existing stdlib narrow supervisor unittest
   selection plus new resource tests. The original supervisor runtime
   limits, owned process tests and summary tests still pass. Record
   exact counts/exits and lint/syntax evidence; no local full product
   run or CI rerun. Hosted full proof remains exact report head.
5. Verify implementation paths/sole parent, original protected workflow
   and tests' unchanged hashes, local proof and docs. Publish one
   immutable report-only SELF child after fresh branch reconciliation
   and one normal push. Verify report bytes then respond once through
   existing helper. Root reviews exact fresh CI and any actual resource
   signals. No unsupported cause claim even on matching counters.

## Verification and negative evidence

Use existing standard Python in canonical repo. Private audit output
under audit/009-r-check and private owned test scratch. One targeted
stdlib run using explicit test module selection under CPU 60s, AS1GiB,
wall120s with KILL5, using actual exit and full finite log. If a real
code/test assertion defect needs correction, one changed-byte rerun
under the same cap is authorized. Separate environment/setup failure.
No arbitrary dependency, system-tool install or extra host probing.
Keep cgroup-local scope limitations and true status on output refusal.

## Documentation

Current 009-r STATUS/evaluation notes explain 009-q terminal evidence,
the new direct launch and limited counters, unchanged tests/CI gate,
and unit vs integration as separate steps. If editing the specific
009-q parenthetical, clarify 2731 unit tests and successful additional
integration step. Preserve historical reports. Baseline NOT_RUN;
whole 009 PARTIAL. Actual credential/current policy and MVP gates open.

## Runtime and protected resources

Offline synthetic standard-library checks and private hosted fixture CI.
Existing client/profile and authorization. No GPU/model/credentials,
corpus, user files, protected services, current real policy, deploy or
release. No reread of prior FIFOs.

## Deferred human adjudication

- Decision: NONE

## Publication and report

Same PR 11. `oap/reports/009-r-direct-unit-launch-and-cgroup-evidence.md`.
Scope PARTIAL for whole 009, exact order and parent hashes, bounded local
evidence, actual hosted CI pending at report authoring. Quiesce after
the normal response. Independent policy lanes continue under own orders.
