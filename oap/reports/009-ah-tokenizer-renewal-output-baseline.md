# OAP Coding Report — 009-ah

Identifier: 009-ah
Result: COMPLETE
Repository: ulfe-lmi/slaif-raggedized-helper
PR number: 11
Branch: oap/009-evaluation-baseline
Base branch: main
Implementation head SHA: 8db5c12e83c6d8d72d681c9740bf7ff226933634
Report publication commit: SELF

## Work and scope

Order `oap/orders/009-ah-tokenizer-renewal-output-baseline.md`
(FINAL; AMEND_EXISTING_PR 11; Decision: NONE; order file 5,894 B,
SHA-256 `67312079f767ece92039f95d0b644a3461cc8d8fca8b879e9ceac41a47cf7070`,
byte-identical to the strategic workorders copy) at round base
`1fa6bc87dcb5dbdddc9fd317c1e9b662b5fd7c59` (the accepted 009-ag
report-only head). At round start the unique open non-draft PR 11
targets main `5a7b41cc512cf883b5b2cb92d87554b4d24e685b` (exact
against the remote) with head ref
`oap/009-evaluation-baseline` at exactly `1fa6bc87...` and no auto
merge; the prior exact required hosted run 44834284664 attempt 1 at
that head (started 2026-11-20T23:06:25Z, conclusion failure) passed
the three OAP jobs (Python 3.12/3.13/3.14) and both ordered unit
inventories (1,440 + 1,998 each) and failed both Product jobs at the
exact one node
`test_t1_selected_change_after_renewal_before_text_bytes` with
`assert 19 == 0` (`19 = <TokenIDSession object>._output`) on both
Python legs (jobs 136626640661 and 136626640665, failing step
"Integration test suite (owned loopback HTTP/SSE)", every later
required step skipped). The exact owned response of the prior round
was already reconciled by Root
(Root-consumed-response-reconciliation.json, SHA-256
`308ac9579009d43b097b88f3171fb2ae297c9d9aab67701a50efcb6b92756793`).

Objective: correct the guarded tokenizer T1 renewal witness to
separate actual startup bytes from query output, preserving the real
current-policy cut and every independent protected-byte and cleanup
assertion. Bounded synthetic software evidence; whole 009 remains
PARTIAL.

History published in this round (one normal push to the same PR
branch, no force push, no merge, one PR):

1. `e1723e502f4fe255a7c61b38e7849bd459754541` (parent: round base
   `1fa6bc87`) — exact Root transcript, four paths: `oap/active`
   (`009-ah` + LF, 7 B, SHA-256
   `710745f470eaa1caf12f173d1530540463e35de53941d3159972431d6860f4ae`),
   `oap/orders/009-ah-tokenizer-renewal-output-baseline.md` (5,894 B,
   SHA-256
   `67312079f767ece92039f95d0b644a3461cc8d8fca8b879e9ceac41a47cf7070`)
   and the two indexed JSON control files copied byte-exact by
   basename: `oap/reviews/009-ah-tokenizer-renewal-output-baseline-index.json`
   (4,946 B, SHA-256
   `2ca353c87c7c35d67643c4c3661e0ed5331a70a2460f1d59ec477d40bc43df7f`)
   and `oap/reviews/009-ah-prior-resolution.json` (888 B, SHA-256
   `b3df41743871a4e7e1881c9cfbc19dc40024ee966926a001d00bb153373603b0`),
   each re-verified at its ordered SHA-256 after copy.
2. `8db5c12e83c6d8d72d681c9740bf7ff226933634` (parent: 1; tree
   `6eddc9f9d75fb3f513605e65864668e3ba90bd73`) — implementation,
   exactly the three ordered paths:
   `tests/integration/test_guarded_encoder_transport_composition.py`
   (40,499 B, SHA-256
   `12161c5a7204edd7f87491e076d4d59c10c58c15a61b2c2999bf088e6d95afbe`,
   blob `7f2a4ef9bcdbd6e5f7f4d3213958bdfb55c5a456`) exclusively in
   `test_t1_selected_change_after_renewal_before_text_bytes`, plus
   `STATUS.md` (193,347 B, SHA-256
   `5491a107ad82cb6027bc33ef4c1af3a389a29953d005076b93b5c253a08455f3`,
   blob `4c893e10e994fcaf662b0f128a8d1f05bc02047b`) and
   `docs/evaluation.md` (192,318 B, SHA-256
   `e556944e3ae9feab8c80216a986e9d13ea745d04dadb9d0604bd8477484d8101`,
   blob `8be293f77a1bdfde5df41cc65fe5d978a9577c6b`) with brief
   cumulative notes. Everything else — the product source, all other
   test code and IDs, the workflow, dependencies, runtime setup, the
   immutable reports, branches and policy — stays byte-exact.

## Implementation

The real tokenizer child emits its startup ready frame and the real
constructor consumes it with `TokenIDSession._read`, which increments
`_output` on all actual reads, before any query (observed startup
total 19 on both hosted legs). The earlier witness therefore failed
at the refused T1 on the incorrect zero-total assertion: the startup
frame was already counted.

The correction, confined to that one node: at the real `_renew`
return the renewed tokenizer's actual startup output counter is
captured in the existing renewed child/pipe record (the `renewals`
tuple gains the snapshot as its retained fifth element) under the
name `tokenizer_startup_output`; the witness asserts the captured
value is positive and that the later refused T1 output equals that
same snapshot, i.e. the refusal added no further bytes. No hardcoded
expected startup byte count, no counter reset, no reduced
observations, no test skip, no loosened predicate, no unchanged CI
retry. The exact untouched assertions are preserved: the real
renewed child and pipe identity (new pid against the renewed-away
child, old child reaped, retained live fd and pipe identity), the
selected observation (`reads == [1]`), the expected booked counters
(`_calls == 1`, `_input` the exact 60-byte framed hello wire), zero
kernel writes to either tokenizer or CPU stdin pipe identity, zero
receipt and forward (`worker._calls == 0`, unchanged worker
`startup_input`/`startup_output`), the admission latch
(`_invalid is True`, recheck refused on a further same-wire
rotation) and fresh re-admission (generation 3, same policy id), and
the real closure/custody (encoder `refused`, session `closed`,
tokenizer/worker/stage `None`). The method name and all five hosted
collection nodes stay unchanged.

Disclosed pre-proof human correction: the first draft of this edit
named the renewed-tokenizer snapshot `startup_output`, and its
destructuring in the test body overwrote the existing outer-scope CPU
worker `startup_output` used by the independent worker assertion.
Root corrected the exact naming before proof: `tokenizer_startup_output`
is used for the renewed-tokenizer capture, the tuple capture/
destructuring and both new tokenizer assertions; `startup_output`
is preserved for the independent worker assertion. The ordered
proofs were run once, on the final corrected bytes.

## Acceptance evidence

1. Reconciled before implementation: exact current PR head
   `1fa6bc87dcb5dbdddc9fd317c1e9b662b5fd7c59` against the remote
   (`git ls-remote`), main `5a7b41cc512cf883b5b2cb92d87554b4d24e685b`
   exact, PR 11 open/non-draft/auto-merge null, worktree clean except
   the ordered transcript state (the `oap/active` swap and the new
   order file), and all 17 frozen source objects verified at round
   base by blob, bytes, mode and SHA-256 against the index
   (including the prior `oap/active` = `009-ag` + LF). The exact
   owned response of the prior round is reconciled per the Root
   reconciliation record above. The four exact transcript bytes were
   committed first (commit 1) before any implementation.
2. The renewed tokenizer's actual startup output counter is captured
   at the real `_renew` return in the existing renewed child/pipe
   record as `tokenizer_startup_output`; the witness asserts the
   captured value is positive
   (`assert tokenizer_startup_output > 0`) and the later refused T1
   output equals that same snapshot
   (`assert new_tokenizer._output == tokenizer_startup_output`). All
   untouched assertions listed under Implementation are preserved
   byte-for-byte, including the independent worker
   `startup_output` assertions now provably unshadowed.
3. The one ordered bounded collect-only and one ordered one-core
   Ruff check ran once each under the canonical physical venv and
   src (see Verification): both exit 0; actual output recorded; no
   local native result. The test method name and all five hosted
   collection nodes are unchanged (collect-only lists exactly the
   five). The two raw failing CI jobs (136626640661,
   136626640665 of run 44834284664 attempt 1) are preserved on the
   remote and cited here; nothing was re-run locally to mask them.
4. Fresh exact report-head hosted proof is required and PENDING at
   authoring: all five jobs and every required step, both Product
   jobs at ordered 1,440 + 1,998 units and exactly 970 passing
   integrations (969 prior + 1 corrected) each.

## Verification

Environment: canonical physical venv (Python 3.14.4, pytest 8.4.2,
ruff 0.17.4) and `src` under the existing repository checkout;
private mode-0700 scratch `/tmp/oap-009ah-proof.I3JqYf` at sticky
`/tmp`; separate private pytest basetemp
`/tmp/oap-009ah-proof.I3JqYf/pytest-basetemp`; raw logs and
commands.txt outside the basetemp, all preserved. No setup,
install, discovery or local execution of native fixtures; no keys,
network, GPU or model download.

Exact commands (as recorded in
`/tmp/oap-009ah-proof.I3JqYf/commands.txt`, SHA-256
`8cdaf7aaaf98e00fca8da3b67322aeb544acc1e42ccada451e75ffdfeded007f`):

1. `env OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src timeout -k 5 120 prlimit --cpu=60 --as=1073741824 .venv/bin/python -m pytest tests/integration/test_guarded_encoder_transport_composition.py --collect-only -q -o addopts= -p no:cacheprovider --basetemp=/tmp/oap-009ah-proof.I3JqYf/pytest-basetemp`
   — real exit 0; raw output (SHA-256
   `38d5baef20f3d85967c58f9db8a27d53b10bcd6bd5ad391536bdc6c41cc64514`):
   the five unchanged hosted nodes listed in order
   (test_matched_new_positive_planned_actual_and_legacy,
   test_t1_selected_change_after_renewal_before_text_bytes,
   test_t2_selected_change_after_receipt_before_forward_payload,
   test_old_expected_binding_refuses_before_protected_payloads,
   test_late_observation_and_interruption_custody), then
   `5 tests collected in 0.35s`.
2. `env OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 timeout -k 5 120 prlimit --cpu=60 --as=1073741824 taskset -c 0 .venv/bin/ruff check tests/integration/test_guarded_encoder_transport_composition.py`
   — real exit 0; raw output (SHA-256
   `82b3e6a6c090a57601d22943bd23fca9218d1031dbe5a7b754092f9a156b4f18`):
   `All checks passed!`.

Mock/live distinction: the five hosted nodes are hosted-only
compositions over real child processes and real pipes with the
trusted synthetic model delegate; collect-only and lint prove
structure only, not behavior. The local proof establishes no hosted
outcome.

Assertions the original failing run (44834284664 attempt 1)
prevented from completing: everything after the failed
`assert new_tokenizer._output == 0` in that node —
`new_tokenizer._child is None` (real cleanup reaped the renewed
child), the zero-write filters over the old and renewed tokenizer
stdin pipe identities and the worker pipe identity,
`worker._calls == 0`, `worker._input == startup_input`,
`worker._output == startup_output`, the admission latch
(`admission._invalid is True`, generation-3 rotation,
`admission.recheck(...) is False`), the fresh re-admission
(`fresh.selection.generation == 3`, `fresh.policy_id ==
admission.policy_id`), and the closure/custody block (`encoder._state
== "refused"`, `cleanup_owner is session`, `session._state ==
"closed"`, `session._tokenizer is None and session._worker is None`,
`session._stage is None`). Those now run after the corrected
snapshot assertions in hosted CI.

No claim is made about this report's future push/CI; the separate
post-publication receipt records the remote facts observed after
push, and Root independently assesses the hosted results.

## Documentation impact

`STATUS.md`: current-slice line for 009-ah plus a brief cumulative
note (round base, exact prior run and single-node failure with
`assert 19 == 0`, transcript byte identities, the startup/output
delta correction, preserved protected observations, local proof,
expected hosted proof, baseline NOT_RUN / whole 009 PARTIAL / no
merge / DHA NONE). `docs/evaluation.md`: new section "The 009-ah
tokenizer renewal output baseline (same 009 continuation)"
recording the exact earlier red head and run, the
startup/output-delta correction, the unchanged protected
observations and the hosted proof status. No other documentation
changed; no implemented commands, measured performance, license
clearance or readiness are claimed.

## DHA and boundaries

Decision: NONE (no D1 candidate reported; no ordered append; the
CRITICAL register was not loaded). Preserved: all product source,
other test code and IDs, workflow, dependencies, runtime setup,
immutable prior reports and reviews, branches, policy, unrelated
worktrees and the strategy-side state. No live model, data,
credentials, protected runtime, hardware, license decision, public
interface, release, deployment or merge performed or requested.

## Limitations and remaining work

The fresh exact report-head hosted CI is PENDING at authoring; this
report cannot certify its future push or checks. Until it is
measured, the corrected T1 node's post-correction assertions and the
970-passing integration expectation are not hosted-proven. The
assertions the failed run left incomplete (listed in
Verification) complete for the first time in that fresh CI. No
scope deviation beyond the disclosed pre-proof naming correction.
Real source rights, subsequent ranking, grading, publisher,
authenticated delivery, governed full evaluation and the
representative baseline remain open; baseline NOT_RUN; whole 009
PARTIAL; no merge.
