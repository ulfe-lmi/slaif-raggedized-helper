# OAP Coding Report — 009-r

Identifier: 009-r
Result: PARTIAL
Repository: ulfe-lmi/slaif-raggedized-helper
PR number: 11
Branch: oap/009-evaluation-baseline
Base branch: main
Round base commit: 416009c94a6759c9a42e9c19dab688c0f54d9650
Transcript commit: 886fb781d0ca2ab7515c622f1100bd9a51c707e4
Implementation head SHA: dff27d4bf0c54796c4f1450f9c0320b44a083664
Report publication commit: SELF
Order SHA256: bbf066f88bcd9026d63d3a0cf861d1f3f5c4d8e8544ed9edc549074b7757d4c0
Active bytes: 009-r + LF (SHA256 fbd5469e481526d5f7cebe8bf6e22bc9f069e512f0fd88cd7407ebc251883557)
Prior resolution SHA256: 17943b522180dc6dc3a6b8cf76d05076b8346a4e8ff9823051deca9d83fbb31c
Publication authorization: FINAL order 009-r-direct-unit-launch-and-cgroup-evidence.md (bbf066f8…) at round base 416009c9 (architecture 4b419053… and governance 24cec232… verified); Root prior resolution decision NOT_ACCEPTED_REQUIRED_PRODUCT_CI_FAILURE_CONTINUE_SAME009_WITH_BOUNDED_DIAGNOSTIC_LAUNCH; standard non-force push to the existing branch subject to its named checks

## Scope

009-r (FINAL) at round base 416009c9 (the 009-q report head):
expose the actual wait status of the unit-test process and bounded
numeric evidence of resource events in the hosted supervisor's own
cgroup, and run the complete hosted comparison under unchanged test
and timeout/cleanup policy. The uv wrapper is replaced by the direct
repo pytest console in main only; run_child, supervisor teardown and
output framing keep their behavior; one bounded optional own-cgroup/
RLIMIT_CPU observation is wired only into the existing bounded
final summary. Allowed paths only (supervisor, new small stdlib
resource module, the two focused tests/oap modules, STATUS.md,
docs/evaluation.md); no workflow, source or pytest file change, no
package environment change, no prior log/report rewrite, no merge,
no next objective, no deploy/credentials/live data/hardware work.

## Change

Transcript 886fb78 (sole parent 416009c9): the exact three-path Root
transcript (order bbf066f8…, active 009-r+LF, prior resolution
17943b52… copied unchanged from the strategic workorders),
byte-verified.
Implementation dff27d4 (sole parent 886fb78): exactly 6 allowed
paths.
- oap/bin/ci_unit_diagnostics.py: preimage 3e15bf1c… postimage
  1cf1368d… (main only; run_child/teardown/forwarding unchanged).
  main now supervises the fixed installed console
  `<root>/.venv/bin/pytest` (absolute fixed path) with the
  unchanged trailing suite args (`tests/unit -o addopts= -vv -o
  faulthandler_timeout=60`) and exact repo cwd; the uv wrapper is
  no longer invoked (no new uv operation, shell, argv override or
  fallback). Fail-closed prelaunch projection
  direct_launch_projection: fixed installed console (real regular
  executable file), same-local-venv shebang interpreter, real local
  venv (pyvenv.cfg) and real bin directory; any absence returns
  EXIT_PREREQUISITE before any child exists. Child env is the
  inherited env plus repo .venv VIRTUAL_ENV and its bin as the
  first PATH entry (the reviewed local launch projection). Bounded
  optional own-cgroup observation: one snapshot immediately before
  launch and one after the owned teardown, plus the inherited
  prelaunch RLIMIT_CPU soft/hard; only a fixed-length numeric
  fragment is appended to the existing bounded final summary;
  observer availability or a delta never determines child status,
  acceptance, or which member failed; the exact old child
  signal/exit and nonzero/failure behavior is preserved.
- oap/bin/ci_unit_resources.py (NEW, stdlib-only): 240845f6…
  Exactly one unified /proc/self/cgroup row; validated canonical
  components (bounded count/length, no dots/empty segments,
  conservative ASCII); lstat-verified component chain under the
  trusted fixed mount /sys/fs/cgroup (no path scan, no symlink
  traversal, no caller-selected input, no path output); EOF-driven
  read under a strict cap-plus-one because procfs/cgroupfs
  pseudofiles report a stat size that does not describe the
  generated text (/proc/self/cgroup reports zero while returning
  data); only the cgroup directory (st_dev, st_ino) identity plus
  bounded nonnegative counters; only nonnegative deltas of
  memory.events.local max/oom/oom_kill and pids.events.local max
  for the same identity with monotone counters; missing,
  malformed, oversize, unstable or counter-reset report
  unavailable; kernel-documented untracked event keys
  (low/high/oom_group_kill/sock_throttled) parsed and ignored
  under the bounded ASCII key/value grammar; malformed values
  (including non-ASCII numeric text) refuse the whole file without
  raising; RLIMIT_CPU as bounded decimal/unlimited/unavailable.
- tests/oap/test_ci_unit_diagnostics.py: preimage e4f348a1…
  postimage cf7bbf18… Two new bounded synthetic OAP cases:
  (20) positive exit 137 and real direct self-issued SIGKILL give
  DISTINCT owned wait results (exact normal exit 137,
  child_signal None, status OK, exit 137 preserved, reconciled
  Popen returncode 137; versus child_exit None,
  child_signal SIGKILL, status CHILD_SIGNALED, exit 131, returncode
  -9 - never a 128-addition), and the SIGKILL child's SIGTERM
  marker handler is never written, proving the identity-verified
  owned group sweep signalled no live process outside the child's
  own self-kill (an unowned process is never signalled); (21) the
  exact direct projected argv/env over an owned synthetic repo
  tree (fixed console + unchanged trailing args; inherited env
  plus local VIRTUAL_ENV and PATH head) and the clean prelaunch
  refusal (None) for a missing, non-executable, external-shebang,
  no-shebang, non-ASCII-shebang, interpreter-less, pyvenv.cfg-less
  or symlinked-venv console. All 19 original cases unchanged;
  census updated (21 methods, 15 owned children, 16 creation
  attempts).
- tests/oap/test_ci_unit_resources.py (NEW): 1414a45f… 10 focused
  pure cases on owned synthetic fixtures (no real cgroup mutation
  or privilege): unified-row parsing, component validation,
  bounded event grammar (complete normal kernel files with
  untracked valid keys; malformed/non-ASCII/oversize/duplicate
  refusals without raising), oversize read-seam refusal, symlink
  event-file refusal, stable positive snapshots (nested and root
  cgroup), unavailable boundaries (no unified row, multiple
  unified rows, traversal, no exact mount mapping, symlink chain,
  missing/malformed files), render deltas/reset/identity/
  path-free output, real-process RLIMIT_CPU grammar, bounded
  fragment length, and the read-only zero-size procfs pseudofile
  real-read case.
- STATUS.md: preimage eddbcb42… postimage f6aa5b8a… Current-state
  lead advanced 009-q -> 009-r; one current 009-r slice note; the
  ordered 009-q parenthetical clarified in the current docs
  (Python 3.12: 2731 unit passes; the separate integration step
  and all other required steps succeeded).
- docs/evaluation.md: preimage ce1b3c24… postimage be973cc3… New
  009-r section near the preserved 009-q section recording the
  009-q terminal evidence, the new direct launch and limited
  counters, the unchanged tests/CI gate and unit-vs-integration
  as separate steps, the local first-run defect and its same-
  correction fix; the same ordered 009-q parenthetical
  clarification.

Protected/unchanged: .github/workflows/oap.yml SHA256
b9195355… byte-verified unchanged (unit and integration remain
separate steps); all src/, tests/unit/, tests/integration/ and
other OAP bytes unchanged; prior logs/reports preserved (the
immutable 009-q report keeps its original wording).

## Verification (bounded local; exact command results and hashes
private in the strategic audit/009-r-check directory, never in Git)

- Preflight: local HEAD/branch = origin/oap/009-evaluation-
  baseline = 416009c9 (= order base); origin/main 5a7b41cc; local
  tracked base clean except the exact activation bytes (order
  bbf066f8…, active 009-r+LF); PR 11 unique OPEN (head 416009c9,
  base main, MERGEABLE, no auto-merge); prior resolution 17943b52…
  and Root audit/009-q-ci-terminal/Root-terminal-review.json
  dccf70a0… plus Root-console-launch-projection.json 7a633f58…
  match the order; supervisor preimage 3e15bf1c… and protected
  workflow b9195355… match.
- Actual 009-q terminal outcome (run 44672714984 at 416009c9):
  both Product legs with the confirmed OPENBLAS_NUM_THREADS=1 step
  env collected 2731; both passed the named isolated 16-slot
  publisher case; Python 3.12 (job 136077193909) forwarded 2532
  pass marks, Python 3.14 (job 136077193256) forwarded 2505; both
  direct supervised uv processes exited positive 137 with no
  signal field, no supervisor termination reason and no display
  refusal; different last unfinished source-stage nodes
  (test_controlled_two_partition_full_stages_exceed_return_cap on
  3.12, test_controlled_flat_denominator_and_rank_21 on 3.14), no
  final summary; both elapsed around 63 s including existing
  cleanup (63.12/63.22 s; gnu time max RSS 217552/229352 KiB);
  six downstream required steps skipped per leg; three OAP jobs
  succeeded. No causal claim about a source test, OOM, scheduler
  or host process.
- Bounded local stdlib run (explicit test module selection:
  tests.oap.test_ci_unit_diagnostics +
  tests.oap.test_ci_unit_resources; CPU 60 s / AS 1 GiB / wall
  120 s then KILL 5 s via prlimit + timeout -k 5 120): FIRST run
  30 tests, 1 failure and 2 errors, actual exit 1 (log
  f0794cbb…) - an actual read/parser boundary in the new module:
  the stat-sized read could not observe the real zero-size
  /proc/self/cgroup pseudofile (it reports st_size 0 while
  returning data), and the strict key set rejected complete
  normal kernel event files carrying documented untracked keys.
  Fixed in the same already-authorized correction (EOF-driven
  strict cap-plus-one read keeping the file/identity checks;
  bounded ASCII key/value grammar that ignores untracked valid
  keys and refuses malformed values without throwing). ONE
  changed-byte re-run under the same exact cap: 31 tests OK,
  actual exit 0 (log 3370a76e…; wall 17.0 s, user 4.26 s, max RSS
  67780 KiB - inside CPU 60 s / AS 1 GiB / wall 120 s). The
  original first-run proof log is preserved.
- Lint/syntax: ruff on the four changed Python files reports no
  NEW findings - the single F401 (unused `import time`) in
  tests/oap/test_ci_unit_diagnostics.py is pre-existing at base
  (identical single finding on the base file) and outside the
  product lint scope (OAP scaffold excluded in pyproject);
  python3 -m compileall -q oap tests exit 0; git diff --check
  exit 0 on both commit ranges.
- Real-route read-only smoke (canonical host, never in Git):
  /proc/self/cgroup reports st_size 0; the fixed snapshot read it
  to EOF and returned the real own-cgroup identity (30,
  1102570) with all four tracked counters (0) and
  rlimit_cpu=unlimited:unlimited; fragment
  `rlimit_cpu=unlimited:unlimited cgroup=mem_max+0:oom+0:
  oom_kill+0:pids_max+0`; the actual kernel memory.events.local
  (low/high/max/oom/oom_kill/oom_group_kill/sock_throttled) is
  parsed with untracked keys ignored.
- Static: implementation diff exactly the six allowed paths with
  the transcript as sole parent; transcript diff exactly its
  three paths with sole parent 416009c9; workflow byte-unchanged;
  no product/test/fixture/job/deadline/limit/selection bytes
  changed.
- Local product run / CI rerun: NOT RUN (ordered: no local full
  product run or CI rerun; the hosted full proof remains the
  exact report head).
- Mock/live distinction: all test evidence is synthetic/offline
  (owned fixtures, stdlib children, no keys/network/GPU/model
  download/live inference); the only real reads are the
  read-only RLIMIT_CPU and zero-size /proc/self/cgroup pseudofile
  in the named test and smoke; the fresh hosted run at the new
  head is the actual CI evidence and is PENDING at report
  authoring - pending is pending, and no green/cause/baseline
  claim follows from this report.

## Acceptance evidence

1. Actual clean base, previous report/receipt/CI and exact
   transcript verified (local HEAD = branch = origin branch =
   416009c9 = order base; origin/main 5a7b41cc; PR 11 unique
   OPEN, no force, no branch checkout change; prior resolution
   17943b52…, terminal review dccf70a0…, launch projection
   7a633f58… all match the order); transcript committed with
   exactly its three paths as the sole child of 416009c9.
2. At main only, the repo .venv/bin/pytest console is supervised
   directly with unchanged trailing args, absolute fixed
   executable path and exact repo cwd; the fixed installed console
   is required before launch and fails closed (EXIT_PREREQUISITE,
   no child) if missing; the child env reproduces the reviewed
   local launch projection (same inherited env, repo .venv
   VIRTUAL_ENV, its bin as first PATH entry) with no new uv
   operation, shell, argv override or fallback; run_child
   receives this explicit argv/environment and keeps all resource
   execution/ownership behavior; the bounded synthetic OAP check
   proves positive exit 137 and real direct SIGKILL have distinct
   wait results and that no unowned process is signalled (SIGTERM
   marker never written; identity-verified group sweep only).
3. Bounded optional own-cgroup snapshots immediately before
   launch and after the owned teardown: exactly one unified row,
   validated absolute canonical components, fixed local event
   files under trusted /sys/fs/cgroup, no path scan/symlink
   traversal/path output, unavailable on missing exact mount
   mapping; same device/inode identity compared; only nonnegative
   deltas of the four named counters; missing/malformed/oversize/
   unstable/counter-reset report unavailable; inherited
   prelaunch RLIMIT_CPU soft/hard recorded as bounded
   decimal/unlimited/unavailable; no raw files or unrelated
   metadata; wired only into the fixed bounded final summary;
   observer availability or a delta never determines child
   status, acceptance, or which member failed; exact old child
   signal/exit and nonzero/failure behavior preserved (all
   original supervisor runtime-limit, owned-process and summary
   tests pass in the suite run).
4. Pure bounded parsers and stable/missing/malformed/reset
   behavior covered with owned synthetic fixtures (no real
   cgroup mutation or privilege); direct projected argv/env and
   clean refusal for missing console verified; existing stdlib
   narrow supervisor unittest selection plus new resource tests;
   exact counts/exits recorded (first run 30 tests
   failures=1/errors=2 exit 1; changed-byte re-run 31 tests OK
   exit 0 under CPU 60 s / AS 1 GiB / wall 120 s KILL 5) plus
   lint/syntax evidence; no local full product run or CI rerun.
5. Implementation paths/sole parent verified (six allowed paths,
   sole parent 886fb78); protected workflow hash b9195355… and
   all product/pytest files byte-unchanged; local proof and docs
   complete; this ONE immutable report-only SELF child is
   published after fresh branch reconciliation through one
   ordinary non-force push, with remote report bytes, report-only
   diff and first-parent chain verified before the one canonical
   response. Scope: whole 009 PARTIAL for this order; fresh
   hosted CI ownership stays with Root.

## Documentation impact

STATUS.md: current-state lead advanced to 009-r with one current
009-r slice note (009-q terminal evidence per version, the
direct console launch and fail-closed projection, the bounded
own-cgroup/RLIMIT_CPU observation and its unavailable semantics,
unchanged workflow/tests/CI gate with unit vs integration as
separate steps, the first-run read/parser boundary and its same-
correction fix, both runs' exact results, fresh CI pending), plus
the ordered 009-q parenthetical clarification (2731 unit passes;
the separate integration step and all other required steps
succeeded). docs/evaluation.md: new 009-r section near the
preserved 009-q section with the same exact facts, plus the same
ordered clarification. Historical immutable reports (including
the 009-q report's own wording) preserved; no unrelated docs
change.

## DHA and boundaries

DHA NONE (order Decision: NONE); no CRITICAL change. Preserved:
Qwen profile/auth, credentials, models, services and hardware
untouched; no dependency/environment installation; no workflow,
source or pytest file edit; no candidate-branch or worktree
action (no merge/cherry-pick/reset/force/tag/deploy/duplicate
PR); no new FIFO reader or replay (the sole external wrapper
ownership and prior receipts are preserved; the expired response
wrapper is handled exactly once at publication per the recovery
instruction, bounded with its --timeout 10 option, never
replayed); all private command results and hashes retained in the
strategic audit/009-r-check directory, away from Git. No merge;
PR 11 remains open and unmerged.

## Limitations and remaining work

Whole 009 PARTIAL; no deployment readiness implied. The fresh
report-head CI is PENDING at report authoring (no green/cause/
baseline/whole-MVP certificate follows; this report cannot
certify its future push or checks; a separate post-publication
receipt and the strategic review record those facts). The hosted
terminator of the 3.14/3.12 direct uv exit 137 remains unproven
and a new red result stays possible - the new direct launch
exposes the actual pytest wait status and the bounded own-cgroup
counters give Root numeric resource evidence, but no unsupported
cause claim follows even on matching counters; any failure goes
to Root for cause evidence and bounded hosted diagnostics, never
auto-retry. Baseline NOT_RUN; the full default count stays 2731
as an expectation until observed; no narrower CI selection;
no-auth/no-current-policy/no-real-producer/no-model-qualification
labels hold; protected authority/hardware/right/license/MVP and
release gates remain OPEN; actual credential/current policy and
MVP gates open. Strategy owns the fresh full check/acceptance
review. No 010, no merge; DHA NONE.
