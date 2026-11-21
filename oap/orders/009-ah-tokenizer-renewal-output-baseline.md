# OAP Work Order — 009-ah

Status: FINAL
Identifier: 009-ah
PR mode: AMEND_EXISTING_PR
Branch: oap/009-evaluation-baseline
Base commit: 1fa6bc87dcb5dbdddc9fd317c1e9b662b5fd7c59
PR number: 11
Expected active: 009-ag
Provenance: H activated MVP, A ARCH 13.3–13.4, E identical T1 failure on both Products in exact hosted run 44834284664 attempt 1, I independently checked pending and terminal report evidence
Architecture SHA256: 4b41905396a3838269fd6cf372614cd23cb2c3b6a37be09f29ed752803c0983a
Governance SHA256: 24cec23235e3defc5f55bab4690298191d5a233d35dd9bf20b0afb4b3925f922

## Objective

Correct the guarded tokenizer T1 renewal witness to separate actual
startup bytes from query output. Preserve the real current-policy
cut and every independent protected-byte and cleanup assertion.

## Dependencies and current state

Exact open PR 11 targets main
`5a7b41cc512cf883b5b2cb92d87554b4d24e685b`. The prior immutable
009-ag report has reconciled owned response. Hosted run 44834284664
attempt 1 at that exact head passed three OAP jobs and both ordered unit
inventories (1,440 + 1,998 each). Both Product integrations have
969 passes and the same T1 failure. Required steps following that
failure are skipped. The upper transfer remains unaccepted.

Read these exact strategic files under
`/home/janezp/codex-supervision/slaif-raggedized-helper`.

- `workorders/009-ah-tokenizer-renewal-output-baseline-index.json`
  SHA-256 `2ca353c87c7c35d67643c4c3661e0ed5331a70a2460f1d59ec477d40bc43df7f`.
- `workorders/009-ah-prior-resolution.json`
  SHA-256 `b3df41743871a4e7e1881c9cfbc19dc40024ee966926a001d00bb153373603b0`.
- `audit/009-ag-check/Root-terminal-review.json`
  SHA-256 `986ce2c515d9be20350fbf4b61c41a9c3edf1f9696e49b3e1dbe955cf298c833`.

The existing real tokenizer child emits its startup ready frame and
the actual constructor consumes it with `TokenIDSession._read`.
That method increments `_output` on all actual reads, before any query.
T1 reaches the changed selection, refuses and confirms child reaping
before failing on the incorrect zero-total assertion at line 564.
The observed startup total was 19 on both hosts. Read the existing
test T1, constructor and `_read`, and worker readiness emission.

## Allowed paths and scope

Canonical CODING pane %30. First commit the four exact transcript
objects. Use `oap/active` with 009-ah plus LF, this exact order under
`oap/orders/`, and the two exact strategic JSONs under `oap/reviews/`
by basename (index and prior resolution).

Implementation changes exactly these three paths.

- `tests/integration/test_guarded_encoder_transport_composition.py`
  exclusively in `test_t1_selected_change_after_renewal_before_text_bytes`.
- `STATUS.md` and `docs/evaluation.md` with brief cumulative notes.

## Non-goals

Preserve all product source, other test code and IDs, workflow,
dependencies, runtime setup, immutable reports, branches and policy.
No hardcoded expected startup byte count, counter reset, reduced
observations, test skip, loosened predicate or unchanged CI retry.

## Acceptance criteria

1. Reconcile exact current PR head, clean worktree, owned response and
   the frozen 17 source objects. Commit exact transcript bytes before
   implementation. Preserve all out-of-scope paths.
2. At the real `_renew` return, capture the renewed tokenizer's actual
   startup output counter in the existing renewed child/pipe record.
   Assert that the captured value is positive and the later refused
   T1 output equals that same snapshot. Keep the exact untouched
   assertions for the real renewed child and pipe identity, selected
   observation, expected booked counters, zero kernel writes to
   either tokenizer or CPU stdin, zero receipt and forward, admission
   latch and fresh re-admission, and real closure/custody.
3. Run the one ordered bounded collection and one ordered Ruff check.
   Report actual output and no local native result. Preserve both raw
   failing CI jobs. The test method name and all five hosted collection
   nodes stay unchanged.
4. Require fresh exact report-head hosted proof, both Product jobs at
   ordered 1,440 plus 1,998 units and exactly 970 passing integrations.
   All five jobs and every required step must pass. The report may state
   hosted outcomes are pending at authoring.

## Verification and negative evidence

One scoped collect-only of the unchanged five new integration nodes and
one one-core Ruff check on the changed test file under the existing
physical canonical venv and src. Use a private mode-0700 scratch at
sticky `/tmp`, separate pytest basetemp and raw logs outside it. Every
process uses `timeout -k 5 120 prlimit --cpu=60 --as=1073741824`,
`OPENBLAS_NUM_THREADS=1`, `PYTHONDONTWRITEBYTECODE=1`; pytest uses
`-o addopts= -p no:cacheprovider` and Ruff uses one allowed core.
Record exact commands, real exits and raw identities. No setup,
install, discovery or local execution of native fixtures. Report
which assertions the original failed run prevented from completing.

## Documentation

Record the exact earlier red head and run, the startup/output-delta
correction, the unchanged protected observations and the hosted proof
status. Whole 009 remains PARTIAL. Representative baseline NOT_RUN.

## Runtime and protected resources

Only bounded offline local software validation and already configured
private CI. No live model, data, credentials, protected runtime,
hardware, license decision, public interface, release, deployment or
merge. DHA NONE.

## Deferred human adjudication

- Decision: NONE

## Publication and report

One exact transcript, one scoped implementation and a separate
report-only SELF child on PR 11. Preserve the earlier immutable
report. Verify remote publication and respond once using the owned
helper once remote identity is established. The response acknowledges
publication and lets Root independently assess hosted results.
