# OAP Coding Report — 009-b

Identifier: 009-b
Result: PARTIAL
Repository: ulfe-lmi/slaif-raggedized-helper
PR number: 11
Branch: oap/009-evaluation-baseline
Base branch: main
Round base commit: 21a3cbd12b8164ec21ba3b6a0b78104d0663c8e1
PR main base: 5a7b41cc512cf883b5b2cb92d87554b4d24e685b
Transcript commit: 3961a085f752e89732070cfd024d5521701fd098
Implementation head SHA: e1af83d90d8d2a39f479db68682399e15c4d9987
Report publication commit: SELF

## Work and scope

Order 009-b (FINAL, AMEND_EXISTING_PR) on PR 11 head 21a3cbd: portable
dataclasses.replace rejection expectation.
Transcript 3961a085 (sole parent
21a3cbd): 6 paths — unchanged FINAL order,
active 009-b+LF (6 B), three exact Root records (4,683 B), exact
1,085 B index
(SHA-256 0105880d…) at oap/reviews/009-b-root-records.json.
Implementation e1af83d9 (sole parent transcript): 3 paths —
tests/unit/test_text_evaluation_dataset.py (ONLY line 46:
`pytest.raises(TypeError)` → `pytest.raises((TypeError, ValueError))`
immediately around dataclasses.replace(result,
qualification="QUALIFIED"); old SHA-256 901707ff…, fixed b00aa74f…),
docs/ci-dataclass-replace-portability.md (new), STATUS.md. The
implementation amended once pre-SELF (same message/paths) per Root
review, one-implementation topology preserved; this report commit
changes only this report. No
merge/cherry-pick/reset/clean/stash/rebase; no product/dep/workflow/
config/law/profile/cap/skip/xfail change. Actual sequence deviation
(from the order's no-force-push/one-new-report-head-push wording):
implementation pushed as c2e0344, then per the Root pre-SELF
precision review amended and force-with-lease pushed as e1af83d9
before this report; reported as deviation, not compliance.

## Acceptance evidence

1. Reconciled: unique open PR 11 (head 21a3cbd, base main 5a7b41cc,
   no auto-merge, not draft); 009-a report-head CI 43395492425:
   Product 3.12 unit FAILED at test_oracle_and_frozen_private_records
   (CPython 3.12.16 ValueError for the init=False field qualification
   vs TypeError-only expectation); later required steps SKIPPED;
   three OAP + Product 3.14 unit SUCCESS; preserved, not accepted,
   no old-run retry. Transcript byte-verified (size+SHA-256); record
   sources verified at the supervision audit paths; base test file
   SHA-256 901707ff… exact.
2. Unit-only: exactly one differing line (46); normalizing the tuple
   back to TypeError makes the module AST exactly equal base 21a3cbd;
   one tuple occurrence; the call still refuses replacement; all
   other cases/fixtures/assertions/imports/frozen-record/oracle
   assertions retained; production/oracle bytes
   (923d34d2…/70f6a73d…) unchanged before/after.
3. ONE focused pytest process (Python 3.14.4; pinned
   /tmp/slaif-pinned-query-setup-20261113/venv/bin/python →
   /usr/bin/python3.14 52e0a13e…; pytest 8.4.2) ran the ENTIRE fixed
   dataset unit module: `python -m pytest tests/unit/
   test_text_evaluation_dataset.py --disable-plugin-autoload
   --tb=short -o cache_dir=<scratch>/pytest-cache --basetemp=
   <scratch>/pytest-basetemp` in fresh 0700 scratch
   /tmp/slaif-009b-dataclass-portability-20261113, closed env
   (PATH/HOME/LANG/PYTHONPATH src+tests-unit, private TMPDIR, five
   thread vars=1, bytecode+plugin autoload disabled, builtin cache
   enabled), default assertion rewriting (no --assert=plain),
   inherited rlimits CPU 10 s/AS 1 GiB/FSIZE 16 MiB + CPU 0
   affinity. Result: 19 passed in 0.44 s, exit 0; cache nodeids
   1,614 B; GNU time 0.70 s user / 0.06 s system / 0.77 s wall; max
   RSS 62,724 KiB.
4. ONE focused Ruff 0.17.4 (4ef33997…) on the changed unit file only
   (same closed env; rlimits CPU 5 s/AS 512 MiB/FSIZE 16 MiB, CPU 0): All checks passed, exit 0.
5. Guard limits (recorded, not backfilled): 60 s/30 s wall were
   launcher-level SIGALRM backstops only, not descendant wall-cap
   proof; observed walls are samples. pytest-preflight.json `at`
   (09:00Z) is not the actual creation time (mtime 09:08:05, run
   09:08:28). No standalone Ruff preflight exists; the shared
   launcher records Ruff argv/caps and the postflight identifies
   closed env/source/tool hashes. Root pre-SELF review (SHA-256
   9dc54831…) accepts the focused unit + Ruff as LIMITED evidence
   with these deviations; no extra runtime/retry.
6. Docs: new CI note records the 3.12 ValueError vs old
   expectation, the one-line two-type fix, unchanged
   rejection/production, exact local conditions/results/guard limits
   and Root review; STATUS.md slice corrected to 009-b (009-a
   historical PARTIAL); whole 009 not accepted.
7. The final report-head push triggers the full unchanged five-job
   CI (all steps, unit+integration 3.12/3.14, three OAP).
   Missing/pending/skipped/cancelled/failed is not green; Root
   reviews the exact head and all required checks before
   acceptance/next suffix. Pre-report implementation-head CI
   43401446840 (e1af83d9) observed five jobs SUCCESS, including the
   previously failing Product 3.12; it does not replace the final
   report-head CI. Pre-amend CI 43399277429 (c2e0344) cancelled by
   the amend — recorded, not retried.

## Mock/live distinction

Local evidence: one synthetic owned unit module + one lint pass
(Python 3.14.4 only) — no local 3.12 run, no cross-version claim.
The remote matrix at the new report head is the evidence boundary,
PENDING; no CI pass claimed. No live route/model/GPU/corpus/key/
network access; live authorization NONE.

## DHA and boundaries

Decision: NONE (no CRITICAL append). Preserved: the failed 009-a CI
run/log and all prior immutable reports, all unaffected assertions
and files, scratch logs with the inaccurate preflight timestamp (no
backfill), Qwen3.8-27b/A100 Q8/xhigh profile and auth, unrelated
panes/worktrees/source originals. No merge/auto-merge/tag/release/
deploy; no nested agents, FIFO reread or duplicate reader; no
model/profile change.

## Limitations and remaining work

The two-type clause is a portability allowance for the CPython
stdlib rejection-class variation on this one call, not behavior
proof; other retained assertions still require refusal. Whole
009 PARTIAL: stage-set loss/meaningfulness/source binder and real
rights/human held-out/model/hardware/visual/license/ICA/MVP gates
remain open (replan audit/009-b-ci-correction-replan.json); the
prior 15-file 009-b DRAFT stays deferred/inert; no 010 activation.
New actual-source proofs require a proper child-lifetime guard.
