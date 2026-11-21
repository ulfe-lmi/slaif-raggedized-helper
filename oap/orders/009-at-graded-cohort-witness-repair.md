# OAP Work Order — 009-at

Status: FINAL
Identifier: 009-at
PR mode: AMEND_EXISTING_PR
Branch: oap/009-evaluation-baseline
PR number: 11
Expected active: 009-as
Base commit: 915c516c3ad83ab8657b1cc67a98f8ca94d32dc5
Provenance: H activated MVP, A ARCH 13.3–13.4 and 23.4–23.5, E two exact native fixture faults in run 44905965875, I independent exact log and source comparison
Architecture SHA256: 4b41905396a3838269fd6cf372614cd23cb2c3b6a37be09f29ed752803c0983a
Governance SHA256: 24cec23235e3defc5f55bab4690298191d5a233d35dd9bf20b0afb4b3925f922

## Objective

Repair the two native grade witness faults from 009-as and execute the
stable, unavailable-scope and final selected-generation witnesses on the
exact canonical report head. Whole 009 PARTIAL, baseline NOT_RUN, DHA NONE.

## Dependencies and current state

PR 11 remains open and rooted at main
`5a7b41cc512cf883b5b2cb92d87554b4d24e685b`. At the sole exact prior
report, run 44905965875 attempt 1 had three green OAP jobs and both
Product jobs passed ordered 1,440 + 1,998 units. Each integration step
ran an observed 1,003 tests with 1,001 passes and two failures.

Read the Root terminal review
`audit/009-as-check/Root-terminal-review.json` (SHA256
`cbc767fb51f4589f778b4044936a9be02b6f1274575f387baa0a4e73a4ef2b49`).
Only the stable local work check and the unavailable-declaration
wire fixture failed.

Copy `workorders/009-at-prior-resolution.json` byte-exact to
`oap/reviews/009-at-prior-resolution.json`. SHA256
`87b440421e762219715060323635b2d514287999a8575ffcbf99e4d87a1c01ae`.
Use the historical ordered source/grade inputs where required. The
preserved 009-as report SHA256 is
`ce83fc56a78e36c435b7280fda68b16e76914e84e08bd754e19a36c796dbfeb8`.

## Allowed paths and scope

The first transcript contains the exact order, active with LF, and the
exact prior-resolution JSON. The single implementation commit may
change only `tests/integration/test_current_graded_cohort_composition.py`
from original SHA256
`6f77e679e1c5d71496c255fa0f7e3fbcc44328bba62a56f8c0aa308c54583758`.
Limit changes to necessary imports and the existing stable and
unavailable-declaration tests. Preserve the final-generation test verbatim,
all three test names, prior stage fixture and every product/other file.
One immutable report-only child.

## Non-goals

No stage, grade or publication product change, workflow change, widened
scope, synthetic fixture relaxation, new hosted node, native local run,
writer/CLI, qualified encoder, representative baseline, merge or release.

## Acceptance criteria

1. Keep the stable h1/h4 a/c replacement declaration with the actual
   same raw pin and withheld b. The actual grade and embedded source
   digests already returned. In the native stable check use named
   `runner.Budget(*runner._MAX_BUDGET).local_work` and
   `.local_payload` for the source counters. Ordinals 10 and 11 are
   geometry and aggregate call limits. Use named grade budget fields
   for the corresponding grade counters. Preserve all existing stable
   assertions and reconcile their exact real source definitions. In
   the existing legacy parity phase use the actual dense/lexical/fusion
   rankings to check the reported grade-3 gain and cutoff results for
   h1 and the undefined h4 empty-gold case. Match the query results
   by exact query ID. This is an assertion within the same stable node.
2. In the original h1/h2 denial, pass the intended singleton h1
   judgment as `(("h1", ((_c, 3),)), ("h2", ()))` to the existing
   plan-wire helper. Prove the real helper encodes that pair structure
   in a bounded pure check if useful. The genuine product must now
   reach the complete all-case admission and refuse with PREFLIGHT /
   2 / 0 / 0 / 0 / 2 and zero new protected work. Retain the exact
   original dataset and three Gold IDs, selected authority, live
   owner and all zero-work counters.
3. Preserve the actual final-generation witness verbatim. Both
   failed runs already passed it, with actual 75 directories and 21
   full pins, fresh genuine same-wire mutation after the final full
   pin, exact FINAL_PIN / 2 / 2 / 2 / 0 / 0 and no usable mint.
4. Verify sole-parent transcript, test-only implementation, report-only
   child, preserved exact product and fixture bytes and all three
   names. Run the established 361 focused units, collect-only exact
   three native nodes, scoped one-core Ruff and two fresh physical
   imports. At the exact remote report require all five green jobs and
   every step, ordered 1,440 + 1,998 units and 1,003 integrations in
   each Product job. No unchanged rerun of the failing head.

## Verification and negative evidence

Use the existing boxed venv and physical source, separate pytest
basetemps under private 0700 `/dev/shm`, `OPENBLAS_NUM_THREADS=1`,
`PYTHONDONTWRITEBYTECODE=1`, CPU60, AS1GiB, wall120 and KILL5.
Use pytest `-o addopts= -p no:cacheprovider` and one allowed Ruff CPU
with Rayon one thread. Report raw commands, exits, digests and scope.
Local proof remains units, collection and lint. Native pending exact CI.

## Documentation

Report the two fixture errors and exact correction. Retain the original
report and existing product documentation without edits.

## Runtime and protected resources

Only configured bounded synthetic local and hosted tests. Preserve
human-selected runtime and identity settings. No protected data,
credentials, hardware, external service, deployment, tag or release work.

## Deferred human adjudication

- Decision: NONE

## Publication and report

Push the exact transcript, test-only implementation and report-only
child to PR 11 once. Verify the immutable remote report before the
single owned response wrapper. Report CI pending and retain the exact
failed prior result.
