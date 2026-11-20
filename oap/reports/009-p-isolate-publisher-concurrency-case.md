# OAP Coding Report — 009-p

Identifier: 009-p
Result: PARTIAL
Repository: ulfe-lmi/slaif-raggedized-helper
PR number: 11
Branch: oap/009-evaluation-baseline
Base branch: main
Round base commit: e9f24bae9ce47c1ceb3f51e9eff10e91574c7242
Transcript commit: 885b2dcc201530081e43085c00e31d4fe7a2c495
Implementation head SHA: 4ef4dbb9f441219736c03f9291d80509f98fd4c3
Report publication commit: SELF
Order SHA256: d91b8f8f6b065686c6061faea8f08e812565d63c83678b005d2821bc85e2f9b0
Amendment SHA256: c7fa12df23c185804366c0b179989421f518c45ce6990ee17fa5ce302544c337
Prior resolution SHA256: e0438d4305eaf1340afd34038503a8df0fbb967c7fed9858bdad2b3d762c6ade
Publication authorization: FINAL order 009-p-isolate-publisher-concurrency-case.md (d91b8f8f…) at round base e9f24bae plus FINAL strategic amendment 009-p-child-arena-amendment.md (c7fa12df…, separate provenance alongside the original order hash): standard non-force push to the existing branch subject to its named checks; Root prior resolution NOT_ACCEPTED_CURRENT_REQUIRED_CI_FAILURE_CONTINUE_SAME009_WITH_PUBLISHER_CASE_ISOLATION

## Scope

009-p (FINAL) at round base e9f24bae (the 009-o report head): isolate
the existing 16-slot publisher test in one fresh bounded process while
preserving its default collection, all real concurrency, the existing
seventeenth-publication refusal before open and verified cleanup, and
restore the pre-experiment workflow bytes. The only functional changes
are the one 16-slot testcase (plus its two module constants), the
two-line workflow env removal, and current docs. No production or other
test-source edits, no retries/skip/xfail, no weaker assertions, no
supervisor/dependency/deadline/CI job change, no native model or real
publisher storage work; the shared fixture, the two-thread
partial-startup regression and the 2731 default-collection expectation
stay unchanged; no merge.

## Change

Transcript 885b2dc (sole parent e9f24bae): the exact three-path Root
transcript (order d91b8f8f…, active 009-p+LF, prior resolution
e0438d43…), byte-verified against the strategic home.
Implementation 4ef4dbb (sole parent 885b2dc): exactly 4 paths.
- tests/unit/test_private_report_publication.py: preimage SHA256
  ce179d92…, postimage 1b8cb255…. Only the one default-collected
  testcase test_sixteen_slots_refuse_seventeenth_without_open changes
  (plus the _SIXTEEN_SLOT_MARKER constant and the one fixed inline
  _SIXTEEN_SLOT_CHILD program): it launches one fresh
  `sys.executable -c` process with the exact resolved physical test
  path as the sole argument; the child self-binds CPU 5s, AS 512 MiB,
  CORE 0 and FSIZE 16 MiB before any test or product import,
  runpy-loads the exact given test, checks the existing origin
  assertions, and calls the unchanged shared fixture under a real
  pytest.MonkeyPatch context with a genuine-reservation observer -
  16 distinct real reservations, baseline registry restoration, the
  refused 17th publication before open and real worker termination
  all stay fixture assertions inside the child; the parent (using the
  existing _child_environment thread settings, explicit child
  PYTHONPATH at the canonical src for that exact test path, cwd the
  checkout) bounds the child to 20 seconds and requires zero exit
  plus the one fixed success marker emitted only after those
  assertions (timeout/nonzero/missing marker fails); no pytest
  recursion, no preexec_fn. Per the FINAL amendment c7fa12df…, the
  one authorized child-only line environment["MALLOC_ARENA_MAX"] = "1"
  sits after the child PYTHONPATH and before the launch; the shared
  _child_environment helper and every other subprocess are untouched.
  _sixteen_slot_fixture and
  test_partial_startup_preserves_failure_and_terminates_workers are
  byte-identical (AST source segments vs e9f24bae); the test-function
  set and default collection are unchanged.
- .github/workflows/oap.yml: preimage SHA256 b9195355…; exactly the
  two 009-o lines (`env:` / `OPENBLAS_NUM_THREADS: '1'` under the
  unique Product test suite step) removed; postimage 29a44dd6… equals
  the 21341795 preimage byte-for-byte, restoring original suite
  selection and all downstream steps.
- STATUS.md: preimage SHA256 45dcdafc…; current-state lead advanced
  009-o -> 009-p plus one short factual 009-p continuation paragraph.
- docs/evaluation.md: preimage SHA256 fa1d8d5a…; new 009-p section
  near the preserved 009-o section; no 009-o report or section
  rewritten.
Supervisor oap/bin/ci_unit_diagnostics.py byte-verified unchanged at
3e15bf1c….

## Verification (bounded; all private logs/hashes in the strategic audit/009-p-check dir, never in Git)

- Preflight: HEAD/branch = origin/oap/009-evaluation-baseline =
  e9f24bae (= order base); origin/main 5a7b41cc; local clean tracked
  base except the exact active/order bytes; PR 11 unique OPEN, head
  e9f24bae, base main, not draft, no auto-merge; active exactly
  009-p+LF; prior resolution digest e0438d43… and Root
  audit/009-o-ci-terminal/Root-terminal-review.json 9003c156… (plus
  the six preserved probe artifact digests) match the order; test and
  workflow preimages ce179d92…/b9195355… match; default module
  collection 89 at preimage.
- Hosted run 44662270802 at e9f24bae (preserved evidence): both
  Product legs (3.12 job 136043083964, 3.14 job 136043084117) with
  the observed OPENBLAS_NUM_THREADS=1 step env again collected 2731,
  passed 2730, failed the same 16-slot publisher test (RuntimeError
  "can't start new thread" at the fixture's real Thread.start); the
  cleanup regression and the 96-descriptor bound passed; the three
  OAP jobs succeeded; mandatory downstream steps were skipped; the
  earlier fatal exits 139/137 did not recur; the hosted limiting
  resource and hosted benefit remain unproven.
- First bounded local publisher-module run (existing venv Python
  3.14.4; CPU 60s / AS 2 GiB / TERM 120s then KILL 5s via
  `timeout --kill-after=5s 120s` + `/usr/bin/prlimit --cpu=60
  --as=2147483648` + `/usr/bin/time -v`; fresh private direct /tmp
  0700 basetemp; canonical src; -q -p no:cacheprovider --tb=short):
  88/89 - the sole failure was the isolated child at real
  Thread.start under its own 512 MiB cap (test failure preserved as
  evidence, log pytest-publisher.full.log SHA256 14361d81…); all
  other 88 cases passed, no setup/cap/resource failure.
- Root controlled diagnosis (audit/009-p-check records c4ab370e… and
  104a6c8d…): the same instrumented program 5be9d257… failed at the
  same point with caps inside-only and exec+inside (failures reached
  520260 KiB VmSize with 11 threads, initial increments 73748 KiB);
  the single MALLOC_ARENA_MAX=1 child env passed all 16 real
  reservations, the refusal/no-open assertion and clean restoration
  (+8212 KiB per sampled start, 168096 KiB with 16 threads before the
  final start; glibc 2.43).
- After the one authorized child-only line (ruff exit 0 on the
  changed file; fixture/regression re-verified byte-identical): one
  bounded changed-byte re-run under the same exact envelope with a
  fresh private basetemp passed 89/89 (89 collected, 89 pass marks,
  zero failures/errors, exit status 0; wall 2.26s, maxrss 71,392
  KiB) - the actual 89-case outcome, proving the named local command
  only.
- Static checks: git diff --check exit 0 on the transcript and
  implementation ranges; implementation diff exactly the four scoped
  paths with the transcript as its sole parent; ruff (focused,
  changed test file) exit 0; workflow postimage equals the 21341795
  preimage byte-for-byte (diff against that blob empty).
- Mock/live distinction: synthetic owned fixtures and offline
  subprocesses only; no network, keys, GPU, model download or live
  inference; the fresh hosted run at the new head is the actual CI
  evidence and is PENDING at report authoring - pending is pending,
  and no green/cause/baseline claim follows from this report.

## Acceptance evidence

1. Clean exact base verified apart from the activation files (order
   d91b8f8f…, active 009-p+LF, prior resolution e0438d43…); unique
   remote PR 11 (OPEN, head e9f24bae, base main) and branch state;
   bound sources (terminal review 9003c156…, probe artifacts) match
   the order; transcript committed with exactly its three paths, sole
   parent e9f24bae.
2. The default-collected test name, the original _sixteen_slot_fixture
   and the partial-startup regression are byte-identical; the one
   16-slot testcase launches the fresh bounded process with the exact
   resolved physical test path, the existing _child_environment thread
   settings, explicit child PYTHONPATH at the canonical src and cwd
   the checkout, no pytest recursion, no preexec_fn; the child sets
   CPU 5s / AS 512 MiB / CORE 0 / FSIZE 16 MiB before any test or
   product import, runpy-loads the exact given test, checks the
   existing origin assertions, and calls the same fixture with a
   genuine-reservation observer (16 distinct real reservations,
   baseline registry restoration, refused 17th call before open, real
   worker termination); the parent requires zero exit and the one
   fixed success marker after those assertions, with
   timeout/nonzero/missing-marker failure.
3. The env removal restores the entire workflow bytes (diff against
   the 21341795 blob empty, SHA256 29a44dd6…), including original
   suite selection and downstream steps; focused Ruff exit 0, git
   diff --check exit 0 on both commit ranges, and one scoped
   publisher-module run under the existing venv (CPU 60s, AS 2 GiB,
   TERM 120s then KILL 5s, fresh private direct /tmp basetemp,
   canonical src) with explicit synthetic basetemp path, preserved
   output and actual exit: first run 88/89 (test failure preserved
   and reviewed via the amendment), one authorized child-only line,
   changed-byte re-run 89/89; the test failure stayed distinct from
   any setup/cap/resource failure.
4. Three distinct commit layers verified: transcript 885b2dc (sole
   parent e9f24bae), implementation 4ef4dbb (sole parent 885b2dc,
   exactly four scoped paths), and this report as one immutable
   report-only sole child of the implementation; the remote
   base/branch/PR were reconciled before the one standard non-force
   push, and the remote PR head, report bytes, report-only diff and
   first-parent identity are re-verified by the canonical report
   verifier before the one canonical response. The DEFAULT collection
   expectation remains 2731 as an expectation before actual CI.
5. Fresh full Product matrix (both legs) plus all OAP checks/steps at
   the exact report head: PENDING at report authoring; any failure
   goes to Root for bounded next diagnosis, never auto-retry.

## Documentation impact

STATUS.md: current-state lead advanced to 009-p with one short
current continuation note (hosted run 44662270802 with both legs'
2731/2730/1 counts and the observed OpenBLAS step result, the restored
workflow preimage, the test isolation with genuine unchanged
obligations, the local 88/89 -> 89/89 actual results and fresh CI
pending). docs/evaluation.md: new 009-p section near the preserved
009-o section recording the same exact facts plus the controlled
arena diagnosis and its bounds. The original 009-n/009-o reports and
sections are not rewritten; no unrelated docs change.

## DHA and boundaries

DHA NONE; no CRITICAL change. Preserved: Qwen profile/auth,
credentials, models, services and hardware untouched; no
dependency/environment installation; no supervisor or other
test-source edit; no candidate-branch or worktree action (no
merge/cherry-pick/reset/force/tag/deploy/duplicate PR); no new FIFO
reader or replay (the sole external wrapper ownership and prior
receipts are preserved); all private logs and hashes retained in the
strategic audit/009-p-check directory, away from Git. No merge; PR 11
remains open and unmerged.

## Limitations and remaining work

Whole 009 PARTIAL; no deployment readiness implied. The fresh
report-head CI is PENDING at report authoring (no green/cause/
baseline/whole-MVP certificate follows). Successful isolation is
proven only for the named local command; the hosted limiting resource
and hosted benefit remain unproven - a fresh hosted failure (different
resource or ordering constraint) stays possible and the full suite
remains required. Baseline NOT_RUN; no narrower CI selection;
no-auth/no-current-policy/no-real-producer/no-model-qualification
labels hold; protected authority/hardware/right/license/MVP and
release gates remain OPEN. Strategy owns the fresh full
check/acceptance review. No 010, no merge; DHA NONE.
