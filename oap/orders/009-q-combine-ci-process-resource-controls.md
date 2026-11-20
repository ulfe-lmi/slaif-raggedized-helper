# OAP Work Order — 009-q

Status: FINAL
Identifier: 009-q
PR mode: AMEND_EXISTING_PR
Branch: oap/009-evaluation-baseline
Base commit: 3522d263991e35b25b65f2621a289a05ad4231be
PR number: 11
Expected active: 009-p
Provenance: H activated MVP development; A ARCH23/A24 honest proof; E CI44667676605 Product 3.14 exit 137 after publisher pass; I exact terminal and local process-state reviews
Architecture SHA256: 4b41905396a3838269fd6cf372614cd23cb2c3b6a37be09f29ed752803c0983a
Governance SHA256: 24cec23235e3defc5f55bab4690298191d5a233d35dd9bf20b0afb4b3925f922

## Objective

Run a fresh full hosted comparison that combines the now-passing
isolated publisher case with the previously exercised OpenBLAS control
on the Product unit step. Retain every test and required check.

## Dependencies and current state

PR 11 remains open at exact 3522d263 against main
5a7b41cc512cf883b5b2cb92d87554b4d24e685b. Its report-only child graph and
single original response receipt have been verified. Read the existing
order, the prior resolution `workorders/009-q-prior-resolution.json`
SHA256 abeaa64b4dea622bcc9a2c7d7562b3747a43f0bb088fd8ac5c429e90a3f15151
and `audit/009-p-ci-terminal/Root-terminal-review.json` SHA256
35c86e4791b38d27d558bb2e5dfbd0215630e6761a41530fdd563248ed5db371.

009-p hosted 44667676605 terminally failed. Python 3.12 Product had 2731
unit passes and all 24 steps succeeded, including integration. Python
3.14 collected 2731 and emitted 2532 pass marks before child exit 137
without a final summary. Last unfinished forwarded node was
test_controlled_two_partition_full_stages_exceed_return_cap. Its six
subsequent steps were skipped. Both Python versions passed the corrected
16-slot publisher case. The three OAP jobs all succeeded. Neither the
exit status nor that last forwarded node establishes the cause.

The 009-o Product-step OPENBLAS_NUM_THREADS=1 trial alone left the
publisher thread-start failure on both versions, while each job
completed 2730 other cases, including the 3.14 last forwarded node
above. It also reduced collection to one native OS thread from 40 in a
separate local controlled probe. We now keep the successful 009-p
isolated-child allocator setting and add the earlier exact Product-step
control for a changed comparison. This evidence justifies a bounded
resource control without attributing the hosted exit to OpenBLAS. Both
hosted full matrices are required again.

## Allowed paths and scope

CODING pane %30 in canonical checkout. Transcript commit sole parent
3522d263 containing the exact Root order and active bytes plus exact
`oap/reviews/009-q-prior-resolution.json` from strategic workorders.

Implementation touches only `.github/workflows/oap.yml`, `STATUS.md`
and `docs/evaluation.md`. Restore the exact two-line environment
stanza from 009-o after the unique Product test suite name, preserving
LF/indentation and all other bytes:

      - name: Product test suite
        env:
          OPENBLAS_NUM_THREADS: '1'
        run: |

Workflow preimage equals 21341795 SHA256
29a44dd6f5d36d6035478c469d8b3c666fed8c25fe6c2b36ae2ac4e57c887bc4.
Postimage must equal the whole workflow from e9f24bae SHA256
b919535561a88706d815f79d481aa3480837eb1de75d36b0c89ab7b0d99a6118.
Verify unchanged isolated publisher test SHA256
1b8cb255ba2b31fe1cb2c197fd6c72d5123dee9c400108d1d2a2b7812e9ad55d
and supervisor SHA256
3e15bf1c2e3707de12365ffb6ec73fd24b180c9e7ea023b0817d853c04ab3681.

## Non-goals

No test/product or supervisor changes, workflow change outside that unit
step, coverage alteration, resource limit increase, unchanged retry,
other PR, merge, or real service/data/model/hardware operation.

## Acceptance criteria

1. Verify exact local and remote identity, clean base except activation
   files, previous receipt and resolution. Commit the exact three paths
   of the transcript as its own sole-child commit.
2. Verify the two workflow lines and exact historical postimage, and
   unchanged publisher test, resource controls, commands, matrices,
   selection and downstream steps. Static Git/hash/diff checks suffice
   for this env-only comparison. Git diff --check on all scoped commits.
3. Document actual 009-p outcomes and the limited reason for the
   combined comparison. Commit exactly the three scoped implementation
   paths as the transcript's sole child. Report active exact authorized
   bytes and actual fresh CI pending at report authoring.
4. Publish one immutable report-only SELF commit as the implementation's
   sole child, through one ordinary push to the existing branch after
   current remote reconcilation. Verify remote report bytes and topology
   before one canonical response. Scope whole 009 PARTIAL. Keep fresh
   CI ownership with Root and protect every gate.
5. Acceptance after publication requires both complete Product matrices
   and all three required OAP jobs succeed at exact report head. A new
   red result requires cause evidence and bounded hosted diagnostics,
   independent of the exact last forwarded node. No automatic retry.

## Verification and negative evidence

No local product run needed for this exact static byte replacement.
Keep exact command results and hashes private under audit/009-q-check.
Expected full default count stays 2731 until observed. Prior whole suite
failed on 3.14 despite passing the repaired named case. A mid-run stage
name, wall measurement, exit code or allocator choice alone does not
qualify a cause, workload or deployment. Any failing/skipped check
leaves the merge gate open.

## Documentation

Update current lead to 009-q and concise current paragraphs in STATUS.md
and docs/evaluation.md. In the existing 009-p evaluation section, clarify
that the 520260 KiB observation and first 73748 KiB increments belong
to the separate instrumented baseline trials. The first publisher-module
failure itself established the traceback and 88/89. Preserve numeric
evidence, historical immutable reports and all other material.
Report baseline NOT_RUN, current policy/operator and MVP gates open.

## Runtime and protected resources

Existing client/profile, existing helper state, canonical pure software
and hosted fixture CI only. No state mutation outside the scoped round.
No credential, real model/data, corpus rights, hardware, services,
release or deploy. Detached independent lanes remain authorized only on
their own exact scopes.

## Deferred human adjudication

- Decision: NONE

## Publication and report

`oap/reports/009-q-combine-ci-process-resource-controls.md`, same PR 11
and exact gate evidence. Use actual order SHA, prior-resolution SHA,
SELF and exact implementation ancestry. Quiesce after response.
