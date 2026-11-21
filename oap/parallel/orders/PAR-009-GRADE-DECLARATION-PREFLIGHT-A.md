# OAP parallel work order — PAR-009-GRADE-DECLARATION-PREFLIGHT-A

Status: FINAL — isolated local development candidate.
Lane: grade-declaration-preflight. Pane: %33.
Base: dfe301c7c5796dc6de2bf8309f885dfc3b1cd2af.
Branch: oap/parallel-009-grade-declaration-preflight.
Transport: isolated worktree, no remote push or PR.
Architecture SHA256: 4b41905396a3838269fd6cf372614cd23cb2c3b6a37be09f29ed752803c0983a
Governance SHA256: 24cec23235e3defc5f55bab4690298191d5a233d35dd9bf20b0afb4b3925f922
DHA: NONE.
Source inputs SHA256: 0e822c11df217c10c593eb1ea20c3f4852bc95c052d40155334a8a37db84c280.

Provenance H activated MVP, A ARCH13/A23/A24, E existing graded
admission couples plan envelope and query identity inside _prepare,
I exact AUDIT-009-ENCODER-PREFLIGHT-SEAM-A report at 416009c,
SHA256 62d4552aab04327049f0dfaeb9d930f51a7625229ab63b42be6c9c246367eab6,
and strategic note Root-review-62d4552a.json.

## Objective

Extract only query-independent graded plan and conservative envelope
admission from evaluation_program._prepare into one private reusable
unit. This complements the binder-declaration slice without overlapping
its write paths. Keep the legacy _prepare entry and actual post-encoding
validation/accounting unchanged.

## Candidate scope

Only src/slaif_raggedized_helper/evaluation_program.py, an explicit
new focused pytest file tests/unit/test_evaluation_grade_preflight.py,
and the exact ordered OAP order copy, one sole-parent local checkpoint
on the exact base above. No changes to existing source-cohort runner,
stage-loss binder, product public API/exports, existing tests, config,
dependencies, fixtures or workflow. No encoding, storage, protected
data, actual operator/query flow, credentials, model or network.

## Acceptance

1. Extract the existing block at 299–322 into one private helper
   accepting the existing admitted dataset/selected cases, _State
   and cooperative clock. Use existing _plan_admission and exact
   nominal GradeBudget, caps, phase, calculations and reservations.
   Original state.meter is established at the current point and
   remains observable on the same partial-refusal boundary. Return
   only the prep values already consumed by the old remainder
   (entries, conservative work and payload) with native private
   representations. No duplicated plan validators, new meter or
   transferred ownership. This declaration helper has no query,
   payload, expected identity, pin, catalog or dispatch arguments.
2. Legacy _prepare calls the shared helper at the original point.
   Keep its argument list, _expected_queries timing, fixed charge
   at 324, canonical plan hash/query-record construction, state
   mutations at 359–363, and final residual check at 364–368 in
   their original relative order. Pre-encoding declaration admission
   guarantees bounded shape and conservative envelope only. The
   final residual meter condition is tested again after actual
   query identity work on the old path. Snapshot/catalog IDs are
   declaration shapes until actual probe/capture comparison.
3. Test a private preparation with actual bounded synthetic declared
   data, selected cases, plan and budget. Show early rejection for
   bad plan and envelope shortfall, no query/identity or source
   invocation, unchanged post-preparation expected/reserve state,
   and actual metered declarations. Using test-local delegating
   witnesses, compare the legacy _prepare valid identity/meter
   to exact preimage expectations, and verify first-error placement
   and the after-identity residual check. Avoid comparing only the
   public content-free failure string. Maintain physical assigned
   worktree import proof.
4. One bounded Ruff and one selected pytest invocation in existing
   canonical locked venv against candidate source. Use the new
   tests and existing focused tests
   test_budget_refusal_before_pin,
   test_local_and_output_preflight_refuse_before_pin and
   test_two_cases_empty_and_unretrieved_positive from
   tests/unit/test_evaluation_program.py. Private fresh scratch,
   CPU60s AS1GiB wall120s + KILL5 with actual outputs/exits. Preserve
   all attempts under unique names. One changed-byte correction
   for actual assertions under same caps. No full unit or integration.
5. Clean exact implementation-only checkpoint before requesting review.
   Report as one immutable report-only SELF child only after consumed
   REPORT. Reconcile clean topology and normal response with the
   lane-owned helper. No canonical or other lane FIFO, remote push,
   acceptance, merge or qualification claim.
