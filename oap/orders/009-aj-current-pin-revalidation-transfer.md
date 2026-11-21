# OAP Work Order — 009-aj

Status: FINAL
Identifier: 009-aj
PR mode: AMEND_EXISTING_PR
Branch: oap/009-evaluation-baseline
Base commit: 0ea63e91cf563ca1751bb373010d56ea8d884745
PR number: 11
Expected active: 009-ai
Provenance: H activated MVP, A ARCH 13.3–13.4, E actual full stage and grade pin reload starts lack selected-policy checks, I exact stage source peer and local case pin review
Architecture SHA256: 4b41905396a3838269fd6cf372614cd23cb2c3b6a37be09f29ed752803c0983a
Governance SHA256: 24cec23235e3defc5f55bab4690298191d5a233d35dd9bf20b0afb4b3925f922

## Objective

Receive the exact reviewed private case-bound current pin revalidation
and its four hosted synthetic witnesses. Preserve the legacy full pin
revalidation API and results. Whole 009 remains PARTIAL. Baseline NOT_RUN.

## Dependencies and current state

The exact receiving report head passed run 44847591776 attempt 1.
All five jobs and required steps passed. Both Products passed the
ordered 1,440 + 1,998 unit inventory and 975 integrations.
PR 11 uniquely targets main `5a7b41cc512cf883b5b2cb92d87554b4d24e685b`.

Required exact inputs under
`/home/janezp/codex-supervision/slaif-raggedized-helper`.

- `workorders/009-aj-current-pin-revalidation-transfer-index.json`
  SHA-256 `1ea03961188029203505a8af89d692118123a4aa70bc0b8560a75ca562532456`.
- `workorders/009-aj-prior-resolution.json`
  SHA-256 `13cdfe383200b6e8ce60d681dd8fad0c0fd72d4172bc8376352b9d311f955397`.
- `audit/009-current-pin-revalidation-local-resolution.json`
  SHA-256 `c657e8dbecff83662b16d4a2ea7fc8685030f9f741d41bc8196600c9bc718302`.
- `audit/009-ai-check/Root-terminal-review.json`
  SHA-256 `d6032e96b1b49bb846bb7a2d3f3388afbf07c629379519bfafee97dc56445673`.

Exact local implementation `63936e7c2b9e3098bf039d57b3a8359ad326c746`
is sole child of `78ffe7473c8ab517c339c96c038c3f0e9c041d8c`.
Its report-only SELF `cb1373b50a097c7915f6438008f4e42d4cb55e43`
has report SHA-256
`06ef5866da8cf1bdd098c7fc39cd001c7a82b8340f3b482d69c0e057f1c50716`.
All 25 pinned source preimages match at this receiving head.
The independent bounded candidate checks passed. Receiving checks
and execution of the four hosted fixtures remain pending.

## Allowed paths and scope

Canonical CODING pane %30. Commit four exact transcript objects first.
Write `oap/active` as 009-aj with LF. Commit the order under
`oap/orders/` and the two indexed JSONs under `oap/reviews/`
by basename, preserving bytes.

Implementation exactly five files. Transfer three indexed candidate
blobs byte-for-byte, without importing candidate history/order/report.

- `src/slaif_raggedized_helper/raw_snapshot_pin.py`
- `src/slaif_raggedized_helper/private_policy_pin_eligibility.py`
- `tests/integration/test_current_pin_revalidation_composition.py`
- `STATUS.md` and `docs/evaluation.md` for concise scope and evidence.

## Non-goals

Stage and grade caller wiring, stage direct catalog, cohort/program
authority, report provenance, actual publication and delivery are
deferred. Preserve legacy callers, workflow and existing suites.

## Acceptance criteria

1. Verify exact open PR/head, clean activation delta, indexed preimages,
   exact candidate/report and absent destinations. Commit the four
   exact transcript bytes before a five-file transfer implementation.
2. Preserve real `PinOwner.check` behavior. Reuse its shared held
   reload, post-association and exact pin equality body. Freeze bounded
   dataset bytes and case identity and derive selected authority from
   the genuine immutable full principal grant and that exact dataset
   case. Pure complete membership and scope validation precedes any
   directory or source load. Under one borrowed real owner guard and
   one clipped end, check actual association, observe genuine live
   selected policy before the real full directory reload, and again
   after validated association and equality. Compare the final detached
   authority and actual deadline, preserve truthful interruption/cleanup
   and restore prior owner end. The trusted full validation can read
   pinned sources outside effective case scope.
3. Preserve four exact hosted fixtures. Stable h2 matches legacy
   semantics and witnesses one real full directory and two selected
   observations. Unavailable selected h2 refuses before I/O, while
   narrower h1 retains b and trusted integrity genuinely verifies it.
   A real selected-generation denial after the initial association
   prevents all new directory and source reads. A real selected denial
   after one complete reload returns no usable guarded pin. Keep exact
   physical/revision and interruption identities.
4. Fresh exact report-head CI passes all five jobs and all required
   steps. Each Product passes ordered 1,440 + 1,998 units and exactly
   979 integrations (975 + four). No missing or skipped evidence.

## Verification and negative evidence

Use pre-existing canonical venv and physical canonical src. Run one
bounded inherited focus of 106 tests (`test_raw_snapshot_pin.py` 8,
`test_private_policy_pin_eligibility.py` 53,
`test_private_policy_request.py` 45), one bounded collection of the four
hosted nodes, scoped three-file Ruff with one Rayon thread and taskset
to the first allowed core, and physical product import-origin probe.
Use fresh mode-0700 scratch directly in sticky /dev/shm, separate
TMPDIR, pytest basetemp and raw logs outside basetemp. Apply
`-o addopts= -p no:cacheprovider`,
`OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1` and
`timeout -k 5 120 prlimit --cpu=60 --as=1073741824`. Preserve exact
raw streams and exit statuses. No native local execution, setup,
installation or unchanged retries.

## Documentation

Describe the transferred private boundary, actual current selected
checks versus trusted full-directory integrity, local proof and pending
exact hosted gates. Record remaining stage, cohort, grade, publication,
delivery, source rights and baseline qualification without exclusivity
or release claims.

## Runtime and protected resources

Only bounded synthetic software proofs and established PR CI.
No live credentials, sensitive real data, hardware runs, protected
services, release, deployment or merge. DHA NONE.

## Deferred human adjudication

- Decision: NONE

## Publication and report

Commit exact transcript, one scoped implementation and one immutable
report-only SELF child. Include exact source and proof identities and
remaining gates. Publish once to existing PR 11 and respond once through
the owned helper after verifying remote publication. Root checks exact
hosted proof before accepting.
