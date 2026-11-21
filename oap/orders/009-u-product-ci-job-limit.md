# OAP Work Order — 009-u

Status: FINAL
Identifier: 009-u
PR mode: AMEND_EXISTING_PR
Branch: oap/009-evaluation-baseline
Base commit: e97d29fb63a9dbc07dacc36f0feb13008251c92b
PR number: 11
Expected active: 009-t
Provenance: H activated MVP development, A ARCH23/A24 complete test and evidence gates, E exact GitHub 20-minute job timeout during integration, I Root exact terminal review of run 44717676140
Architecture SHA256: 4b41905396a3838269fd6cf372614cd23cb2c3b6a37be09f29ed752803c0983a
Governance SHA256: 24cec23235e3defc5f55bab4690298191d5a233d35dd9bf20b0afb4b3925f922

## Objective

Run one changed CI job-limit comparison on the same private PR. Change
the finite Product job-level timeout from 20 to 30 minutes. All
existing integration and unit test execution and downstream checks
stay required. The bounded headroom targets the proven CI platform
cancellation after successful units. Its effect on this run must be
observed before the policy capture transfer can advance.

## Dependencies and current state

Unique open non-draft PR 11, main
`5a7b41cc512cf883b5b2cb92d87554b4d24e685b`, prior exact round/report
`e97d29fb63a9dbc07dacc36f0feb13008251c92b` and already consumed
009-t response. Root terminal review
`audit/009-t-check/Root-terminal-review.json` SHA256
`1b5fafccf0f70a649a7373c6df589a0f67366132271d4a85c14683e77e8fe131`.
Copy `workorders/009-u-ci-job-limit-prior-resolution.json`, SHA256
`1443a9c4b7ce676a03a1bcd39a106f1addeb31ae9c42bffe01ae53e0acb07f1c`,
unchanged to `oap/reviews/` with the same basename in the transcript.

Run `44717676140` attempt 1 ended CANCELLED. Both Product unit steps
passed all 3,015 units (A 1,421, B 1,594), including the four added
policy modules with the expected 47/124/18/95 file counts. Python 3.14
completed separate integration and all 24 steps. All three OAP jobs
passed. Python 3.12 started at 10:15:30 UTC, completed the unit step
at 10:17:35, and its integration log reached 90% at 10:32:54 before
cancellation at 10:35:42. Check-run 136225094911 explicitly reports
the maximum execution time of 20m0s. The integration step was
cancelled and five later steps were skipped. The exact integration
wall-time variance and active test at cancellation remain unproven.

## Allowed paths and scope

Canonical CODING pane %30. Transcript only `oap/active` (`009-u` + LF),
the exact order under `oap/orders/`, and the one exact prior resolution
under `oap/reviews/`. One sole-parent implementation with only
`.github/workflows/oap.yml`, `STATUS.md`, `docs/CI.md` and
`docs/evaluation.md`. The only workflow byte change is the 20 to 30
integer replacement at product-tests `timeout-minutes`.

Workflow preimage 14,235 bytes, SHA256
`b919535561a88706d815f79d481aa3480837eb1de75d36b0c89ab7b0d99a6118`.
Workflow target 14,235 bytes, SHA256
`54e66869d9a2a02e95202ed3eaecba199a2494ca6f6c5742554e722cf14367c6`.

## Non-goals

Preserve both matrices, existing permissions, action pins, setup,
runner isolation, all unit and integration commands and fixtures,
output and 180 s unit-process budget, local runtime and prior reports.
No selector/skip/xfail, unit or integration partition change, retries,
parallelism change, new step, dependencies, privileges, deployment,
untested fallback or waiver. Keep the capture transfer and any product
modification for a later exact order.

## Acceptance criteria

1. Freshly reconcile canonical branch/base, exact prior report and
   owned regular response, adopted terminal evidence, current PR/main,
   order bytes and exact prior-resolution hash. Stop on unexpected
   working changes, GitHub drift or workflow preimage mismatch.
2. Check the full workflow preimage and target by exact size and SHA256.
   Verify that the single intended integer changes in the Product job
   only. The three OAP jobs keep 10 minutes and all action, setup and
   step bytes remain exact. Check changed file and path scope before
   commit and at the actual candidate implementation head.
3. Keep all original hosted requirements. In both Product legs require
   3,015 actual units (1,421 and 1,594), the same independent integration
   command and complete successful later steps. Keep three OAP checks.
   Report exact pending status before remote CI. Root assesses the
   new exact report-head terminal run and remaining uncertainty.
4. Commit the ordered transcript unchanged, implementation on its
   sole parent, then one immutable report-only SELF child. No advance
   to another objective, merge, release or qualification on local proof.

## Verification and negative evidence

Use bounded static byte/diff verification then fresh normal hosted CI
at the exact report head. No local suite, setup installation or
additional runtime observation needed for this exact workflow change.
Preserve the previous cancellation annotation and progress evidence.
If the new hosted job ends early or fails, retain actual output and
stop for review. A second timeout or partial run cannot close the gate.

## Documentation

Update the existing Product job-limit line in `docs/CI.md` to the
30-minute bound. In STATUS and the cumulative evaluation notes identify
the prior run, the verified timeout, actual counts, reason for the
bounded comparison and pending result. Keep the representative baseline
NOT_RUN and objective 009 PARTIAL. Preserve earlier history and its
previous job limits as historical facts.

## Runtime and protected resources

Private hosted synthetic CI only, no credentials, protected inputs,
model data, corpora, GPU, external services or deployment. Use the
pre-existing helpers and assigned canonical pane. No direct FIFO
read/write, extra reader, activation replay or unchanged CI rerun.

## Deferred human adjudication

- Decision: NONE

## Publication and report

Same PR 11, one ordinary fast-forward push of the existing branch.
Report `oap/reports/009-u-product-ci-job-limit.md` in its own SELF
child. After the remote verification, use the single owned
`send-response.sh --identifier 009-u --timeout 10` and quiesce.
Root owns subsequent CI terminal review.
