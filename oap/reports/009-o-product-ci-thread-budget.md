# OAP Coding Report — 009-o

Identifier: 009-o
Result: PARTIAL
Repository: ulfe-lmi/slaif-raggedized-helper
PR number: 11
Branch: oap/009-evaluation-baseline
Base branch: main
Round base commit: 21341795babef15de2913fd50c4f66d20abca2b1
Transcript commit: eec22406d67b192a0aa286a79cb0d0e46e0d8790
Implementation head SHA: 1f8d84a4c6f11170c642751a4b96f438e70077bf
Report publication commit: SELF
Order SHA256: 07422430c288a9b6e1fbe70800899ecfd0a5854fefb609dea841356cc1fe0101
Prior resolution SHA256: 6f2c280ec82161b51f4b1d6d535252568da95cbfbe5c9e35c28a17e24d07ca49
Publication authorization: FINAL order 009-o-product-ci-thread-budget.md (07422430…) at round base 21341795: standard non-force push to the existing branch subject to its named checks; Root prior resolution NOT_ACCEPTED_CURRENT_REQUIRED_CI_FAILURE_CONTINUE_SAME009_WITH_BOUNDED_CI_ENVIRONMENT_CORRECTION

## Scope

009-o (FINAL) at round base 21341795 (the 009-n report head): the bounded
Product CI thread-budget correction on the same numeric objective and PR.
The only functional change is the two-line step env
OPENBLAS_NUM_THREADS='1' on the unique Product test suite step (covering
both Python 3.12/3.14 matrix legs) of .github/workflows/oap.yml, plus
current docs. No product or test edits, no fixture weakening, no test
selection, no job/deadline/limit or other thread setting, no
dependency/setup, governance/DHA, trigger/credential/deploy change; the
16 real concurrent publication reservations and all test assertions are
preserved; no merge.

## Change

Transcript eec22406 (sole parent 21341795): the exact three-path Root
transcript (order, active 009-o+LF, prior resolution), byte-verified.
Implementation 1f8d84a4 (sole parent eec22406): exactly 3 paths.
- .github/workflows/oap.yml: preimage SHA256 29a44dd6…; the two lines
  `env:` and `OPENBLAS_NUM_THREADS: '1'` (retaining indentation and LF)
  inserted after the unique `- name: Product test suite` and before its
  `run:` key - the only workflow diff (postimage b9195355…); removing
  exactly those two lines restores the preimage byte-for-byte; the
  added env lines occur exactly once, under Product test suite only.
- STATUS.md: preimage SHA256 76ad8496…; current-state lead advanced to
  current slice 009-o plus one short factual 009-o continuation
  paragraph (009-n head and run, 2731/2730/1 per Product leg, the local
  comparison and its limit, the Product step setting, the pending
  outcome, gates preserved).
- docs/evaluation.md: preimage SHA256 3d36b870…; new 009-o section near
  the preserved 009-n section with the same exact facts; no 009-n
  report or section rewritten.
Supervisor oap/bin/ci_unit_diagnostics.py byte-verified unchanged at
3e15bf1c…; its main() run_child call passes no environment= override,
so run_child builds env from os.environ and the Popen child inherits the
step env (verified at the literal call site).

## Verification (bounded; all private logs/hashes in the strategic audit/009-o-check dir, never in Git)

- Preflight: HEAD/branch = origin/oap/009-evaluation-baseline =
  21341795 (= order base); origin/main 5a7b41cc; local clean tracked
  base except the exact active/order bytes; PR 11 unique OPEN, head
  21341795, base main, MERGEABLE, not draft, no auto-merge; active
  exactly 009-o+LF (fd6740ce…); prior resolution digest 6f2c280e… and
  the two named Root audit records (536460eb… / 4ee4f838…) match the
  order under the strategic home.
- Hosted run 44656541114 at 21341795 (preserved evidence): both Product
  legs collected 2731, passed 2730, failed the 16-slot publisher test
  (RuntimeError "can't start new thread" inside the fixture's
  Thread.start); the cleanup regression, the reader cases and the four
  other previously failing publisher cases passed; the three OAP jobs
  succeeded; mandatory downstream steps in the two Product jobs were
  skipped; the earlier fatal exits 139/137 did not recur; the hosted OS
  thread-refusal cause is unproven.
- Local reproduction of the ordered comparison (private audit only, not
  actual CI): 2 GiB address-space cap, ordinary unit collection -
  original publisher case: 40 OS threads, VmSize 1,838,972 KiB; only
  OPENBLAS_NUM_THREADS=1: one OS thread, VmSize 241,244 KiB, same case
  passed; publisher-only selection with the same setting: 88/88
  passed.
- Static checks: env lines exactly once under Product test suite;
  removal restores the workflow preimage byte-for-byte; supervisor byte
  hash unchanged; git diff --check exit 0 on the transcript and
  implementation commits; implementation diff exactly the three scoped
  paths with sole parent the transcript.
- No locally executing product tests this round (ordered env-only
  comparison; the tests are already required at the new head). Fresh
  full Product matrix (both legs, all steps) plus all OAP checks/steps
  at the new report head: PENDING at report authoring - awaiting fresh
  required checks; pending is pending, and no green/cause/baseline
  claim follows from this report.

## Acceptance evidence

1. Local clean tracked base except the exact active/order bytes
   verified; current unique remote PR (11) and branch head (21341795),
   active ID 009-o and prior resolution digest 6f2c280e… verified;
   transcript committed with exactly its three paths, sole parent
   21341795.
2. The additional env lines occur exactly once, under Product test
   suite only, and removing them restores the whole workflow
   byte-for-byte; the supervisor byte hash is unchanged (3e15bf1c…);
   the main run_child env inheritance through Popen without explicit
   override was verified at the literal call; git diff --check exit 0
   on both commits.
3. Short factual 009-o paragraphs added per Documentation (STATUS lead
   and paragraph; docs/evaluation.md 009-o section near the preserved
   009-n section); the implementation diff is exactly the three scoped
   paths with the transcript as its sole parent.
4. This report is one immutable report-only sole child of the
   implementation; the exact branch/PR and remote head are reconciled
   before the one ordinary (non-force) push, after which the remote
   head, report bytes, report-only diff and first-parent identity are
   re-verified by the canonical report verifier, and the one canonical
   CODING response is sent only after that remote proof. Scope result
   PARTIAL for 009; CI is reported as awaiting fresh required checks at
   report-authoring time; historical run evidence and commit
   identities are preserved.
5. Strategic gate after publication: actual fresh full Product matrix
   (both legs) and all OAP checks/steps green at the exact report head;
   if still pending, uncertainty is reported; missing or skipped checks
   block merge; any CI failure goes to Root for bounded next diagnosis,
   never auto-retry.

## Documentation impact

STATUS.md: current-state lead advanced to 009-o with one short current
continuation note. docs/evaluation.md: new 009-o section near the
preserved 009-n section recording the exact 009-n head (21341795), CI
run 44656541114, 2731 collected / 2730 passed / 1 failed per Product
leg, the reproduced local comparison and its limit, the Product step
setting, and the pending actual outcome on the new head. The original
009-n report and section are not rewritten; no unrelated docs change.

## DHA and boundaries

DHA NONE; no CRITICAL change. Preserved: Qwen profile/auth,
credentials, models, services and hardware untouched; no
dependency/environment installation; no product/test/fixture edit; no
candidate-branch or worktree action (no merge/cherry-pick/reset/
force/tag/deploy/duplicate PR); no FIFO replay or new reader; all
private logs and hashes retained in the strategic audit/009-o-check
directory, away from Git. No merge; PR 11 remains open and unmerged.

## Limitations and remaining work

Whole 009 PARTIAL; no deployment readiness implied. The fresh
report-head CI is PENDING at report authoring (no green/cause/
baseline/whole-MVP certificate follows). The hosted thread-refusal
cause is unproven and a fresh hosted failure (different resource or
ordering constraint) remains possible - confirm with the hosted actual
result. Baseline NOT_RUN; no narrower CI selection. no-auth/
no-current-policy/no-real-producer/no-model-qualification labels hold;
protected authority/hardware/right/license/MVP and release gates remain
OPEN. Strategy owns the fresh full check/acceptance review. No 010, no
merge; DHA NONE.
