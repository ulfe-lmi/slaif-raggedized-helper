# OAP Work Order — 009-aw

Status: FINAL
Identifier: 009-aw
PR mode: AMEND_EXISTING_PR
Branch: oap/009-evaluation-baseline
PR number: 11
Expected active: 009-av
Base commit: 13563000b2e44f01f455ca880744017c0e6433da
Provenance: H activated MVP, A ARCH 13.3–13.4 and 20.2, E exact dual-Product native fixture failure, I real Entry/Row source and pure reproduction
Architecture SHA256: 4b41905396a3838269fd6cf372614cd23cb2c3b6a37be09f29ed752803c0983a
Governance SHA256: 24cec23235e3defc5f55bab4690298191d5a233d35dd9bf20b0afb4b3925f922

## Objective

Repair the shared guarded publisher witness setup to use actual held row
membership and actual selected-policy withholding. Whole 009 PARTIAL,
representative baseline NOT_RUN, DHA NONE.

## Dependencies and current state

Exact 009-av, PR 11, report 13563000b2e44f01f455ca880744017c0e6433da.
GitHub run 44923276160 attempt 1 passed all three OAP jobs and both
ordered Product unit sets (1,440 + 1,998). Each Product completed 1,006
integration nodes with 1,003 passes and the same three failed publisher
nodes. They all stopped at shared fixture line 253, before real grade
or publication, on Entry.batch_container_id. The genuine membership
Entry does not have that field. The genuine row map Row does, but the
membership-to-row association is via Entry.ordinals.

Root terminal review audit/009-av-check/Root-terminal-review.json SHA256
1a8f5ab40c5ee9263c245f394fb07bda2d217651ce0dd15dcff9e74feb4137c9. Preserve the rejected report and all exact logs.
Copy workorders/009-aw-prior-resolution.json (SHA256 3fb75d31bd261426e039c6aedd550a62120725ba0fbf67b921f0e1004f88b24f) to
oap/reviews/009-aw-prior-resolution.json byte-exact in the transcript.

The actual fixture preimage is blob 164f215113a36044f8e418d656fe38fa5b9c105c
with SHA256 688da09889b8edd76939a3107d2e4dc6c711710a82dcde592a7ad00093e842da.
The independent pure example reproduced the exact error using real
raw_snapshot_membership.Entry and raw_snapshot_rows.Row. Its actual log
is audit/009-aw-check/Root-exact-prior-negative.log SHA256
07ffd619c00d8d45daf7f4a9fb557b11fe2b86ebafac34363b165fc8fc71eb78. The exact receiving main remains
5a7b41cc512cf883b5b2cb92d87554b4d24e685b.

## Allowed paths and scope

Transcript only the order, oap/active with one LF and the exact prior
resolution. Implementation only
tests/integration/test_current_graded_report_publication_composition.py.
Add the same single supplied_policy_eligibility import spelling already
used by test_current_graded_cohort_composition.py. Change only the
held_rows block in _fixture before ctx.pointer_generation and insert
the selected unavailable assertion between full_grants and wire in that
fixture. All three test bodies, all other fixture bytes, docs, product,
workflow, other tests and dependencies stay exact. One report-only child.

## Non-goals

Production edits, test additions or removals, CLI, local native execution,
live data, hardware qualification, merge, deployment and release are
outside this order.

## Acceptance criteria

1. Keep the b ID extracted from actual bundle IDs and omitted by the
   actual projected declaration. Preserve held_rows as the common
   test-local assignment at the start of the comparison. Read the
   actual owner.value.data.row_map.rows and prove member_b.ordinals
   is nonempty. For each declared ordinal prove exact ordinal,
   bundle ID, revision ID, extraction ID and partition ID against
   the actual held row. Avoid any unused or invented Entry field.
2. After the real current admission and captured policy snapshot,
   call the existing supplied_policy_eligibility.unavailable_partitions
   on that actual policy_snapshot and held.data.membership. Assert the
   actual b partition is unavailable. Preserve the real b pin and
   projected a/c h1/h4 grade, native producer/publisher calls, all
   teardown and actual I/O assertions. Use the single import line
   from the canonical grade witness, including its noqa.
3. Exercise the exact patched row-proof block on the actual Entry
   and Row types with the ordered pure checker, using the physical
   source on PYTHONPATH. Validate one positive and five negative
   bindings. Keep fault reproduction evidence at the failed base.
4. Prove the exact transcript, test-only implementation scope and
   report-only child with check-exact-repair.py. Pass 388 existing
   focused units (89 publisher, 62 policy payload, 68 selection,
   71 capture, 45 request, 53 pin eligibility), exact three hosted
   node collection only, scoped Ruff, both fresh physical import
   orders and the pure checker. On the new exact report head require
   all five jobs and all required steps, 1,440 + 1,998 units in their
   existing order and exactly 1,006 integrations in each Product.

## Verification and negative evidence

Run python3 -B audit/009-aw-check/check-pure-membership.py PHYSICAL_WITNESS_FILE
from the strategic home or by absolute path. Checker SHA256 c5b5434c4c9f54e9ef131fe2e7d8ed4caebea3f196ca76a86c224375fffaef3a.
It extracts the exact comparison between held_rows and the assignment to
ctx.pointer_generation. Use physical source and the existing boxed venv,
private 0700 /dev/shm TMPDIR, separate pytest basetemps, CPU60, AS1GiB,
wall120, KILL5. OPENBLAS_NUM_THREADS=1, PYTHONDONTWRITEBYTECODE=1,
RAYON_NUM_THREADS=1, one allowed Ruff core, pytest -o addopts= -p no:cacheprovider.
Exact topology checker audit/009-aw-check/check-exact-repair.py
SHA256 80c156e62f1fa0a75b817024db4d80fb68b86f9b2ab3fcd1ee2c5eb26e94158a. It accepts REPOSITORY STRATEGIC_HOME IMPLEMENTATION
[--report REPORT]. Record actual exits, origins and log digests.

## Documentation

Record the native fixture failure and exact proof in the immutable report.
Preserve existing documentation and previous reports. Treat all new
native publication outcomes as pending hosted proof.

## Runtime and protected resources

Existing bounded synthetic fixtures only. Preserve current runtime settings.
No dependency setup, credential, live data, model, service or hardware action.

## Deferred human adjudication

- Decision: NONE

## Publication and report

Amend the existing PR 11 with the three exact commits together once. Verify
remote report and SELF ancestry, then answer through the sole wrapper once.
No replay or report revision.
