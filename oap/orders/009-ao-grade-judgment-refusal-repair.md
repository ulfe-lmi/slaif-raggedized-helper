# OAP Work Order — 009-ao

Status: FINAL
Identifier: 009-ao
PR mode: AMEND_EXISTING_PR
Branch: oap/009-evaluation-baseline
Base commit: dc09ae4f90ffab086aadf24ca39de9b9f2b29384
PR number: 11
Expected active: 009-an
Provenance: E exact required 009-an native CI assertion and independent
source review, A A32 A33 A37, H activated MVP
Architecture SHA256: 4b41905396a3838269fd6cf372614cd23cb2c3b6a37be09f29ed752803c0983a
Governance SHA256: 24cec23235e3defc5f55bab4690298191d5a233d35dd9bf20b0afb4b3925f922

## Objective

Repair the one failing grade-judgment hosted witness expectation. Use the
existing PR. Its previous report head is a failed gate, not an accepted
scope. This suffix changes only the erroneous test expectation. Whole 009
PARTIAL, representative baseline NOT_RUN, DHA NONE.

## Dependencies and current state

Hosted CI run 44877969312 attempt 1 at exact 009-an report dc09ae4f.
Both Product jobs failed the same assertion after each passed ordered
1,440 + 1,998 unit tests. All three standalone OAP jobs passed. Skipped
Product steps are unqualified. The previous suffix remains failed.

Exact inputs under `/home/janezp/codex-supervision/slaif-raggedized-helper`:

- `workorders/009-ao-grade-judgment-refusal-repair-index.json` SHA-256 `149d921ef154b3d5a990b2cc8470fb43f7d2eb7b0c11f581c6264bc5072ea507`.
- `workorders/009-ao-prior-resolution.json` SHA-256 `852a91f22bbb1872c4713dd9bfd59f72e99efc0575ab9e824207c889e1ed60f0`.
- `audit/009-an-check/Root-terminal-review.json` SHA-256 `75a25a1c29f873f9590456532316bf0d0fd24921b5d15b1bb4c8042b5ec21aa8`.
- `audit/009-an-check/Root-hosted-refusal-failure-review.json` SHA-256 `7a0bd26ab01947e626437f29645ead127a25fb0f46a5ca7a4b4e84b3dd78bc64`.

Both workorders JSONs are to be copied byte-for-byte to `oap/reviews/`
by basename in the first transcript. The index's only allowed
implementation object is the test named below, with exact expected
postimage SHA-256 `8aca72099afff0e7c4712e9a9d4d88d9098b6c90a924c43c83439079352c7bf1`.
The regular `audit/009-ao-check/check-refusal-repair.py` verifies exact
preimages, expected edit, and optionally implementation/report topology.

In tests/integration/test_current_grade_judgment_dispatch_composition.py,
test_judgment_dispatch_pure_refusals_zero_new_reads subcase (g) tests one
prepared case with two plan judgments. The actual paired admission calls
_prepare_plan and _plan_admission before returning. The order/length gate
raises before admitted=True. The existing content-free EvaluationError
therefore correctly has progress=None. The witness incorrectly expects an
admitted PREFLIGHT prefix in this one subcase.

## Allowed paths and scope

Change only the expected value for subcase (g) from plan_level to None
and correct the immediately preceding comment to say the mismatch is
rejected before admission. Match the exact after bytes of the final
receiving index. Keep the same genuine malformed-plan inputs, no-reads
counters, exact status/message, caught-context check, admission latch and
custody checks. Keep (a)–(f), the other two hosted nodes, product code,
workflow, dependencies and product docs unchanged. The order, active
pointer, two indexed control records and immutable report are the governed
transcript.

## Non-goals

No production or deployed activity. Do not reconsider the product refusal
or add admitted progress to a malformed plan. The unrelated encoder candidate
awaits its own later receiving scope.

## Acceptance criteria

1. Verify exact open non-draft PR and failed 009-an report head, current main,
   final order inputs and clean state except activation. Commit order/active
   plus both exact control JSONs under oap/reviews/ transcript-first.
2. Exactly one implementation file, exact subcase and comment change from
   the locked preimage to the exact postimage. The old accepted product
   behavior and actual enforcement remain intact. Preserve the content-free
   error and no new delegated reads and prove admitted progress stays distinct.
3. Existing venv and physical canonical source. 92 focused existing units
   (evaluation program 50, joint preflight 42), three exact hosted collect-only,
   one-file scoped Ruff on one permitted CPU and one Rayon thread, exact
   source and test hashes. Fresh 0700 /dev/shm with CPU60/AS1GiB/wall120/KILL5,
   bounded single-thread environment, no dependencies installed or native
   test execution locally.
4. One immutable report-only SELF child. Push transcript, implementation
   and report together to current existing PR, verify remote publication,
   signal the owned response once. No separate implementation-only push,
   unchanged rerun or waiting for CI before publishing report. Hosted proof
   remains pending in report.
5. Fresh exact report-head gate must pass all five required jobs and
   every required step, both Products at ordered 1,440 + 1,998 units and
   exactly 994 integrations. Prior failure remains recorded.

## Verification and negative evidence

Verify no delegated source reads or latch activity for malformed joint
declaration, exact content-free error, and custody preserved. Test locally
with OPENBLAS_NUM_THREADS=1, PYTHONDONTWRITEBYTECODE=1, separate TMPDIR
and pytest basetemp, -o addopts= -p no:cacheprovider, and the exact unit
focus, collect-only and scoped Ruff in the acceptance criteria. Do not
claim locally executed hosted witnesses.

## Documentation

Record the test expectation and prior-hosted-failure rationale in the
immutable report. Product documentation has no new behavior to describe.

## Runtime and protected resources

Existing venv and bounded synthetic setup only; no new dependencies,
live model, corpus, credentials, service, hardware, deploy or release.
No merge. Preserve unrelated state.

## Deferred human adjudication

- Decision: NONE

## Publication and report

Report exact implementation SHA and SELF, focused commands, raw streams
and outcomes, hosted gate pending, and DHA NONE. Publish the one full
sequence to the existing PR and verify before the single owned OK.
Continue remaining encoder and full grade after the exact repair gate.
