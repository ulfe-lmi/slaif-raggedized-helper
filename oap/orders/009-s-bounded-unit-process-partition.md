# OAP Work Order — 009-s

Status: FINAL
Identifier: 009-s
PR mode: AMEND_EXISTING_PR
Branch: oap/009-evaluation-baseline
Base commit: dfe301c7c5796dc6de2bf8309f885dfc3b1cd2af
PR number: 11
Expected active: 009-r
Provenance: H activated MVP development, A ARCH23/A24 honest coverage evidence, E CI44688983707 real SIGKILL, I exact Root terminal review
Architecture SHA256: 4b41905396a3838269fd6cf372614cd23cb2c3b6a37be09f29ed752803c0983a
Governance SHA256: 24cec23235e3defc5f55bab4690298191d5a233d35dd9bf20b0afb4b3925f922

## Objective

Run a changed hosted comparison using two bounded sequential direct
pytest processes covering the exact complete default unit collection.
Measure whether the full check can complete under that execution
mode. Preserve the same job, required unit step, downstream checks,
test bodies, installation, process resource settings and honest
terminal evidence. A green comparison can qualify this CI execution
mode. Signal origin remains unproven, including on a green result.

## Dependencies and current state

Open unique PR 11, exact report-only base dfe301c, main 5a7b41cc.
Original canonical wrapper timed out before publication. Root
independently verified the remote immutable report. No replay.
Read Root terminal review audit/009-r-check/Root-terminal-review.json
SHA256 3d3b5e0ddd1883dbad32de53dc80ada31519baef49f2e23ffabc0541d9e3b994.
Copy workorders/009-s-prior-resolution.json SHA256
3a2c54bd9ed78c46ded2b70966ea92274c89af836ba56d20bc40e3d33af36501
unchanged in the transcript. Avoid rereading bulk hosted logs.

Run 44688983707 terminal FAILURE. Python 3.12 collected 2731,
forwarded 2391 pass marks and directly observed pytest SIGKILL before
normal group teardown. Supervisor exit 131, cleanup PROVEN,
terminated_by=none, wall 63.56s including cleanup. No final pytest
summary. The last forwarded line is a pass, with cause unproven.
Six subsequent steps skipped. Python 3.14 completed all 2731 unit
tests, separate integration and all 24 job steps. Its supervisor
elapsed 78.58s including cleanup. Both show unlimited inherited
RLIMIT_CPU and zero selected own-cgroup deltas. All three OAP jobs
passed. The evidence supports a changed execution comparison and no
attribution to a specific test, timer or cgroup event.

## Allowed paths and scope

Canonical CODING pane %30 only. Three exact Root transcript paths
oap/active, this order and oap/reviews/009-s-prior-resolution.json.
Transcript sole parent dfe301c.

Implementation scope oap/bin/ci_unit_diagnostics.py, existing
tests/oap/test_ci_unit_diagnostics.py and small focused companion
oap/bin/ci_unit_partition.py and tests/oap/test_ci_unit_partition.py
if needed, STATUS.md and docs/evaluation.md. Keep run_child,
owned process cleanup and observer primitives unchanged. No edits
to .github/workflows/oap.yml, pyproject, lock/environment, src,
tests/unit, tests/integration, prior logs or reports.

## Non-goals

No subset, retry after an execution failure, requirement weakening,
runner privilege, alternate test route or artifact publication.
No process scans, new host probes, diagnosis claims beyond actual
result, merge, next numeric objective, release or deployment.

## Acceptance criteria

1. Verify actual canonical checkout, branch/base, exact prior report,
   terminal evidence and three transcript bytes. One same-PR normal
   push, no force or checkout change.
2. Use the current tests/unit flat layout and exact pytest default
   file naming. Derive two nonempty disjoint deterministic ordered
   groups, with tests/unit/test_owned_gpu_worker.py beginning group
   B. The current exact base has 62 and 56 tracked files in the two
   groups. The cut is near 29.8s in successful 3.14 and roughly
   39s in failed 3.12's forwarded postcollection observations.
   Measure actual group sizes and timings. Use bounded one-level
   inventory and exact regular path admission. Admit both default
   patterns test_*.py and *_test.py. Ordinary non-test files and
   generated __pycache__ are not test entries. Refuse unsupported
   non-hidden nested layouts or symlinked test/scope entries instead
   of silently omitting tests. No argv override or file/site cleanup.
3. Demonstrate exact ordered equivalence under the inherited locked
   environment with three bounded collect-only observations, full
   directory then the two actual launch path groups. Concatenated
   unique node IDs must equal the full ordered node list, with both
   groups nonempty and no duplicate, omission, extra or failed
   collection. Record counts, canonical lists' SHA256 and true
   exits, and preserve original output privately. Hosted positive
   gate on each Product leg requires both pytest success summaries,
   observed combined complete unit census and every later required
   step. No total counts asserted from prior round without matching.
4. At main only supervise groups A then B as separate direct
   invocations of the installed venv pytest console, same exact cwd,
   unchanged inherited environment projection and same trailing
   options after the path selectors. No new dispatch after an
   unproven or nonzero first child, exhausted budget or final
   display refusal. Preserve exact first nonzero and original
   child wait distinctions. Use one aggregate monotonic 180s
   observation/dispatch budget, with remaining time passed via the
   existing run_child private deadline argument, including elapsed
   first-group cleanup before admission of B. Preserve bounded
   10s and 5s owned group cleanup per launched child. Use remaining
   aggregate original display and raw-log byte ceilings on B via
   existing run_child arguments. Retain original per-line and
   per-operation output safety. A bounded group label ties each
   existing summary to its own process. Keep per-child own cgroup
   snapshots and inherited RLIMIT observational and status-neutral.
   An unavailable second dispatch is explicit nonzero, never a
   synthetic second result. Keep the current direct console
   admission unchanged.
5. Bounded synthetic OAP tests exercise ordered membership, empty/
   unsupported layout and sameness of argv/env, sequenced success,
   no next launch after signal/nonzero/budget or display refusal
   and exact remaining budget. Use existing supervisor wait and
   cleanup tests. Tie local proof and immutable report to exact
   implementation head. Publish one report-only SELF child and
   verify actual remote report before the sole normal response.
   Root owns fresh CI terminal assessment. A required failure
   remains a failure even if one partition or job passed.

## Verification and negative evidence

Use the existing canonical locked .venv and standard Python.
One targeted stdlib OAP suite run plus one three-way collection-only
batch, each under private scratch, CPU60s AS1GiB wall120s KILL5.
No full local unit or integration execution. Preserve every actual
exit, stdout/stderr, hash and cap. One changed-byte correction on
a real failure may rerun only affected bounded proof under the same
cap. No unchanged CI retry. Static validation, changed paths,
original workflow/test/environment hashes and suite visibility in
report. Group 3.14 prior successes are evidence for that prior head.

## Documentation

STATUS and docs/evaluation record the real 009-r outcomes, limits of
numeric evidence, reason for the two-process comparison, both actual
group counts and exact collection equality or refusal. Keep source
fixture and external-qualification status truthful. Baseline NOT_RUN,
whole 009 PARTIAL. No claim of knowing the 3.12 signal sender.

## Runtime and protected resources

Offline synthetic standard library and collect-only checks, normal
private CI. No services, user files, corpora, protected policy,
credentials, model binary or GPU invocation. No prior FIFO read or
response replay. No external writable targets beyond the preexisting
branch authorized for this same round's ordinary push.

## Deferred human adjudication

- Decision: NONE

## Publication and report

Same PR 11. oap/reports/009-s-bounded-unit-process-partition.md.
Immutable report-only SELF commit after exact implementation on the
transcript, one ordinary push of the existing branch. Fresh full
CI pending at publication, no development acceptance or release.
Quiesce after the owned response.
