# OAP Work Order — 009-y

Status: FINAL
Identifier: 009-y
PR mode: AMEND_EXISTING_PR
Branch: oap/009-evaluation-baseline
Base commit: 53937d7eac0805905a0b6c5ca6e973ea989f8032
PR number: 11
Expected active: 009-x
Provenance: H activated MVP, A protected runtime and evidence obligations, E exact 009-x required Python 3.14 failure in the inherited owned-descendant test
Architecture SHA256: 4b41905396a3838269fd6cf372614cd23cb2c3b6a37be09f29ed752803c0983a
Governance SHA256: 24cec23235e3defc5f55bab4690298191d5a233d35dd9bf20b0afb4b3925f922

## Objective

Correct the Linux procfs exit observation in the existing owned-descendant
timeout test so it recognizes a task disappearing after a successful
stat-file open. Preserve the tested timeout and process custody behavior.

## Dependencies and current state

Unique open non-draft PR 11 against main
`5a7b41cc512cf883b5b2cb92d87554b4d24e685b`. Run 44760385202 attempt 1
completed at the exact 009-x report head. Python 3.12 passed 3,196 ordered
unit and 951 integration cases. Python 3.14 matched the expected ordered
unit inventory with one inherited failure in job 136371029375 and six
downstream skips. All 62 new payload cases passed on both Products, and
all three OAP jobs succeeded. The required gate remains failed.

Verify `workorders/009-y-prior-resolution.json` SHA-256
`61fc5048a5e2df6f26b8c775e9bd999985a3d97034e6229001aee6744256d15c`
and its exact indexed inputs, consumed report, diagnostic and terminal
review. Root's terminal review SHA-256 is
`5130c9ad75bbbf90e182393020600680faaf59847092386021cf1b5ddb8bd2b6`.
The accepted isolated candidates stay outside this continuation.

## Allowed paths and scope

Canonical CODING pane %30. Commit three byte-exact Root transcript paths
first: `oap/active` with `009-y` and LF, the exact order at
`oap/orders/009-y-proc-exit-observation.md`, and the prior resolution at
`oap/reviews/009-y-prior-resolution.json`.

The implementation may change only the existing
`test_timeout_kills_owned_descendant` in
`tests/unit/test_real_cpu_toy_probe.py` and minimal evidence notes in
`STATUS.md` and `docs/evaluation.md`.

## Non-goals

Product behavior, workflow, test inventory, resource or timeout budgets,
test runner, process signals, PID/start-time binding and other tests
remain byte-exact wherever outside the two procfs observation cuts.
No transfer, baseline measurement, merge, release or deploy.

## Acceptance criteria

1. At the actual owned procfs stat poll, accept `FileNotFoundError` at
   open and `ProcessLookupError` at read as the two observations of
   record disappearance. The hosted failure was the second condition
   after the actual expected parent timeout. In the existing pidfd-bound
   cleanup, also accept a missing stat record after successful pidfd
   acquisition. Keep the exception handling scoped to the existing
   process observations and cleanup. Other I/O and malformed evidence
   retain their failure behavior.
2. Preserve the existing assertion of actual parent timeout, the
   observation deadline and zombie check, `probe.UNREAPED` assertion,
   same-handle signal path, and exact PID/start-time check before any
   conditional cleanup signal. Preserve the still-live failure path,
   descriptor close and all existing test nodes.
3. Run the entire inherited test module once, expected 28 cases. The
   existing strategic diagnostic must demonstrate the two actual Linux
   read forms and the changed test's acceptance of controlled ENOENT and
   ESRCH at the owned stat poll, while EACCES still escapes. Use one
   targeted Ruff check on the changed test module. Record raw results and
   exact physical test and product import origins. Present synthetic
   injected observations distinctly from real timeout and kernel evidence.
4. Require fresh exact-report-head hosted Product Python 3.12 and 3.14,
   each with unchanged ordered A 1,440 and B 1,756 unit cases, separate
   951-case integration, and the same three OAP jobs. Every existing
   step must succeed. Root owns this terminal review.

## Verification and negative evidence

The indexed `audit/009-x-check/proc-exit-race-witness.py` is a small
temporary diagnostic. Run it through the existing canonical Python from
the canonical repository with its own private scratch path. The indexed
Root legacy witness already records ENOENT accepted, ESRCH propagated and
EACCES propagated by the base test. Do not repeat or modify the old test.
Run the changed-input diagnostic once with the same independent
normalization expectations. Preserve any actual first fault and report
it. Use the exact branch, source and prior receipt identities in the
report.

## Documentation

Record the observed inherited procfs exit race and actual correction in
STATUS and the evaluation notes. Attribute the failed required check to
the exact 009-x run, distinguish the new pending hosted gate from local
proof, and preserve prior results. Representative baseline NOT_RUN,
whole 009 PARTIAL.

## Runtime and protected resources

Use the pre-existing canonical `.venv`, exact canonical `src`, fresh
mode-0700 scratch directly beneath sticky `/tmp`, private pytest basetemp,
`-o addopts= -p no:cacheprovider`, `OPENBLAS_NUM_THREADS=1`,
`PYTHONDONTWRITEBYTECODE=1` and `timeout -k 5 120 prlimit --cpu=60
--as=1073741824` for each authorized proof. Targeted Ruff may use one
allowed process-local core within the same limits. Use owned synthetic
child processes only. No package installs, additional uncapped or
repeated proofs, protected resources, live model, GPU, credentials or
data. The regular GitHub publication and hosted CI below are authorized.

## Deferred human adjudication

- Decision: NONE

## Publication and report

Use the existing control and response components. Publish exactly one
`oap/reports/009-y-proc-exit-observation.md` report-only SELF child of the
implementation. Include actual bounded proof and exits, source and
workflow identities, exact prior failure and any setup deviations. One
regular push to the same PR and one
`send-response.sh --identifier 009-y --timeout 10`. Quiesce afterwards.
Root reviews exact fresh remote head and required CI. DHA NONE.
