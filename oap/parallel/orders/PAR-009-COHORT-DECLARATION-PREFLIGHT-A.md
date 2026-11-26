# OAP parallel work order — PAR-009-COHORT-DECLARATION-PREFLIGHT-A

Status: FINAL — isolated local development candidate.
Lane: cohort-declaration-preflight. Pane: %32.
Base: cacc5b362574638e09862a0d82e14e53bd1abef1.
Branch: oap/parallel-009-cohort-declaration-preflight.
Transport: isolated worktree, no remote push or PR.
Architecture SHA256: 4b41905396a3838269fd6cf372614cd23cb2c3b6a37be09f29ed752803c0983a
Governance SHA256: 24cec23235e3defc5f55bab4690298191d5a233d35dd9bf20b0afb4b3925f922
DHA: NONE.
Source inputs SHA256: bdaf1331de6dc9e63ac54c2178b0d16abff968de03b69b0ca94704d32f5c25cf.

Provenance H activated MVP, A ARCH13/A23/A24, E current source cohort
requires encoded Query payloads before dataset and authority admission,
I verified read-only encoder-preflight report at 416009c with SHA256
62d4552aab04327049f0dfaeb9d930f51a7625229ab63b42be6c9c246367eab6
and Root-review-62d4552a.json.

## Objective

Add a private bounded pre-encode admission for the real full source
cohort declaration using the exact accepted private binder declaration
primitive. Preserve the old source runner's existing input order,
metering, error behavior and report identity. This is the source-side
prerequisite for later shared graded admission and private operator
composition, without adding the operator, encoder or policy checks.

## Candidate implementation

Isolated local source on the accepted exact binder implementation
base above, with original SELF report 63e36735376e72e64abf239ba4d77d518c72731f
and Root dependency resolution SHA256 77d25a57fc3403bc34f7b5267ea3c3d562aec65ec8f978ca58a14c69a630937f. Modify only
src/slaif_raggedized_helper/source_cohort_runner.py, a new focused
test tests/unit/test_source_cohort_declaration_preflight.py, and
the exact ordered parallel order copy. Keep binder and grade code,
existing tests, public exports and package/workflow bytes exact.
No general runtime configuration, source/catalog/storage I/O,
protected policy, actual encoding or authorization.

## Acceptance

1. Use existing source._input_admission boundaries as the reference.
   Reuse shared private pieces for exact input envelope, known
   config/cohort ID grammar and ordered bounded dataset and
   scope/selection. The old flow must retain the initial combined
   shape checks, fixed failure prefix reservation, config-first
   checks, per-Query nominal/identity check and true vector gate
   interleaved before dataset parsing, plus every existing meter and
   time checkpoint. Preserve exact nominal type/length guards and
   all concurrent callers' data ownership and state. No fake Query
   or old helper shortcut that omits malformed actual vector payloads.
2. The new private path accepts the genuine declared cohort and a
   bounded ordered tuple of encoder-identifier tuples, one per
   declared case in the same order, with no actual Query or payload.
   Reuse the accepted binder's query-free declaration primitive at
   each case. Validate all original declarative root/dataset envelope,
   Gold IDs, deadlines, case ID grammar/order, explicit config/budget,
   case selection and supplied scope intersection before a result.
   Check exact declared inputs before potentially large traversal.
   Result may reuse the exact admitted dataset, selected tuple,
   selection and meter convention. No new DTO or claim about actual
   encoder fingerprint equality, grade plan, real pin/catalog,
   current-policy authentication, durable grants or source rights.
3. Nonvacuous proof uses synthetic exact physical source origins.
   Valid private declaration admits complete selected subset or split
   as appropriate and yields ordered all-case scope evidence with no
   vector, pin, catalog or producer. Reject malformed later case
   declaration before source, malformed dataset/selection/scope and
   budget shortfall. Distinguish full-shape and later authority
   refusals using delegated validator and actual meter witnesses.
   Demonstrate old-path interleaving of dataset fault and real legacy
   vector fault, identical valid selected evidence and original
   metering/report identity. Public sanitized failure strings alone
   do not prove first-error ordering.
4. Run a bounded targeted Ruff and one selected pytest invocation,
   candidate import origin checked relative to the physical new test.
   Include the new tests and existing test_success_and_private_report,
   test_admission_failure_has_no_progress_and_no_source,
   test_precharge_refuses_before_dataset_and_source and
   test_bad_query_vector_and_extra_fields_refuse from
   tests/unit/test_source_cohort_runner.py. Existing locked venv,
   fresh private scratch, CPU60s AS1GiB wall120s + KILL5. Preserve
   actual logs, command and exits. One changed-byte retry only for
   concrete failed assertion. No full unit/integration execution.
5. Sole-parent exact implementation checkpoint. Request owned
   implementation review and await FIX/REPORT. After consumed REPORT,
   one unchanged report-only SELF child and owned response. No new
   reader outside the protocol, no canonical or another lane's
   transport, remote push, integration or acceptance.
