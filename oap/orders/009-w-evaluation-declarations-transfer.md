# OAP Work Order — 009-w

Status: FINAL
Identifier: 009-w
PR mode: AMEND_EXISTING_PR
Branch: oap/009-evaluation-baseline
Base commit: 0f24c91c1c04931ffbc3a82d896ce08afc816d05
PR number: 11
Expected active: 009-v
Provenance: H activated MVP, A ARCH13/A23/A24, E current graded runner needs real vectors before full query-independent declaration admission, I reviewed exact binder/cohort/grade slices and 009-v hosted gate
Architecture SHA256: 4b41905396a3838269fd6cf372614cd23cb2c3b6a37be09f29ed752803c0983a
Governance SHA256: 24cec23235e3defc5f55bab4690298191d5a233d35dd9bf20b0afb4b3925f922

## Objective

Transfer the exact accepted private declaration-side binder, source
cohort and grade preflight changes. Keep the existing query-dependent
admission and grade behaviors, order, metering and report identity. The
query-independent pieces support later bounded orchestration before
actual encoding.

## Dependencies and current state

Unique open, non-draft PR 11 on main
`5a7b41cc512cf883b5b2cb92d87554b4d24e685b`. Exact 009-v report-only
head at the base above. Run 44731327493 attempt 1 passed all five
jobs and steps. Both Products ran 3,086 ordered units (1,421 A and
1,665 B) and separate 951-case integration. Root terminal review
`audit/009-v-check/Root-terminal-review.json`, SHA256
`fd1c6a5cd0492b052d1492973479523c0b0efdb1d9133f7054d1e336062eb905`.

- `workorders/009-w-declaration-transfer-index.json` SHA256
  `34c34d715a24e8eef47a03d6d220aa718bb6c38157ca82d7185046db7103a5f2`
  freezes original candidate dependencies, three required canonical
  preimages, three order and test sets, and original report identity
  and archival destinations.
- `workorders/009-w-prior-resolution.json` SHA256
  `6c8cced1117f498ca3c9deb177c44758518f03870d79192631b1ae03d6ba4bb0`
  binds the already consumed 009-v regular response and exact terminal
  review. Do not replay the prior signal or invoke an old reader.

## Allowed paths and scope

Canonical CODING pane %30. Four exact Root transcript paths are
`oap/active` with `009-w` + LF, the unchanged order under `oap/orders/`,
and the two exact JSON files above under `oap/reviews/` by basename.
The implementation changes only the three existing product preimages
and adds the three indexed test files, three exact lane orders, and
three original SELF reports in `oap/provenance/009-w/`. In addition,
add cumulative `STATUS.md` and `docs/evaluation.md` notes. The report
is its own sole-parent SELF child.

## Non-goals

No current policy, actual encoder, pin/catalog, publisher or delivery
composition, legal/rights claim, fixture replacement, CI change,
dependency installation, full local suite, merge, new PR or release.
The existing source and grade runtime signatures, public paths and
negative outcomes remain governed by their tests. Keep these exact
accepted bytes. No branch history merge or cherry-pick.

## Acceptance criteria

1. Reconcile the exact canonical branch/base, PR/main, actual
   worktree activation changes, prior report and consumed regular
   response, adopted hosted review and both strategic source hashes.
   Require all three existing source preimages and six absent
   additive payload paths plus three absent archive destinations.
2. Verify each original candidate's exact parents, Root resolution,
   consumed receipt and immutable report-only child. The cohort
   candidate depends on the exact binder implementation. Copy and
   verify receiving mode, full size, SHA256 and blob OID for all 12
   indexed paths, without changing the historical original SELF
   markers. Verify physical receiving paths, exact committed scope
   and the original old-path behavior witnesses. Stop on drift.
3. Run the six-file targeted Ruff check and one combined focused
   pytest from the canonical locked environment, with physical
   package origin verified. Include the three indexed new unit files
   and the exact existing test selectors below. Expect 58 focused
   tests, including 48 new and 10 inherited parameterized nodes.
   Preserve all actual exits/setup outcomes. A concrete failure is
   retained for Root, with no changes to the accepted transfer bytes.
4. Required fresh full hosted result on each Product is A 1,440,
   B 1,694, total 3,134, plus unchanged complete integration and every
   downstream step. Expect all OAP jobs. These figures are projections
   until exact report-head checks complete. Keep the representative
   baseline NOT_RUN and whole 009 PARTIAL.

## Verification and negative evidence

New focus files are `test_source_bound_stage_loss_preflight.py`,
`test_source_cohort_declaration_preflight.py`, and
`test_evaluation_grade_preflight.py` under `tests/unit/`. Use these
existing exact cases from the same directory.

- `test_source_bound_stage_loss.py::test_input_preflight_rejects_bad_types_and_nonfinite_payload`
- `test_source_cohort_runner.py::test_success_and_private_report`
- `test_source_cohort_runner.py::test_admission_failure_has_no_progress_and_no_source`
- `test_source_cohort_runner.py::test_precharge_refuses_before_dataset_and_source`
- `test_source_cohort_runner.py::test_bad_query_vector_and_extra_fields_refuse`
- `test_evaluation_program.py::test_budget_refusal_before_pin`
- `test_evaluation_program.py::test_local_and_output_preflight_refuse_before_pin`
- `test_evaluation_program.py::test_two_cases_empty_and_unretrieved_positive`

Use canonical `.venv` and a fresh 0700 disposable directory under
`/tmp`, private pytest basetemp, disabled cacheprovider, scoped
`OPENBLAS_NUM_THREADS=1`, `PYTHONDONTWRITEBYTECODE=1`, and
`timeout -k 5 120 prlimit --cpu=60 --as=1073741824` for each proof.
One core Ruff process affinity is permitted under the same cap. A
bounded origin check under those limits is permitted. Reset `addopts`
for the focused command to preserve a pytest summary. Preserve real
commands, output, exits and bounds. No full local execution or
unchanged retry. Use only indexed evidence for already run proofs.

## Documentation

Add brief cumulative STATUS and evaluation notes covering exact copies,
old and new synthetic behavior, prior 009-v hosted run, retained original
identities, actual focus and fresh CI pending. Describe the open
governed operator, real baseline, source rights and model gates.

## Runtime and protected resources

No real dataset, corpus, credentials, protected sources or model/GPU
access. Synthetic files, owned bounded verification and existing private
GitHub CI only. Use established one-signal components. No direct FIFO
access, relay, manual reader or changed runtime profile.

## Deferred human adjudication

- Decision: NONE

## Publication and report

Same PR 11, one ordinary push verified against current report head.
Publish `oap/reports/009-w-evaluation-declarations-transfer.md` as
one immutable report-only SELF child. Report full ordered scope,
matching preimages/dependencies, actual local proof and precise
pending hosted result. Use the existing owned helper
`send-response.sh --identifier 009-w --timeout 10` once, then quiesce.
