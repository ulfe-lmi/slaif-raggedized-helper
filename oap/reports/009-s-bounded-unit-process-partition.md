# OAP Coding Report — 009-s

Identifier: 009-s
Result: COMPLETE
Repository: ulfe-lmi/slaif-raggedized-helper
PR number: 11
Branch: oap/009-evaluation-baseline
Base branch: main
Implementation head SHA: 432485720720ae6676764409feeafa5eab3bf25b
Report publication commit: SELF

## Work and scope

Executed the exact FINAL order 009-s (bounded unit process partition),
AMEND existing PR 11 at round base dfe301c7c5796dc6de2bf8309f885dfc3b1cd2af
(the immutable 009-r report head whose run 44688983707 completed
TERMINAL_FAILURE per the Root terminal review
audit/009-r-check/Root-terminal-review.json, SHA256
3d3b5e0ddd1883dbad32de53dc80ada31519baef49f2e23ffabc0541d9e3b994,
verified byte-exact), with remote main
5a7b41cc512cf883b5b2cb92d87554b4d24e685b and PR 11 OPEN at that head,
MERGEABLE, no auto-merge.

Transcript commit be30982b2220f29f79c0843d32329ac1eab2bd6e (sole parent
dfe301c) carries exactly three bytes: oap/active = "009-s" + LF, the
order file (SHA256 8f0063ff3c090f84b41b61f45d06f62396db6eff98e0b5adf49028ffee149536)
and the copied prior resolution (SHA256
3a2c54bd9ed78c46ded2b70966ea92274c89af836ba56d20bc40e3d33af36501).

Implementation commit 432485720720ae6676764409feeafa5eab3bf25b (sole
parent be30982b) changes only the ordered scope:

* oap/bin/ci_unit_diagnostics.py (diagnostics file SHA256
  1b5ab7c13f77766501b1ecfc0264b798577b8f583c1300a232597c3df7a8db7b):
  main now supervises TWO bounded sequential direct pytest-console
  processes (group A then group B) under ONE aggregate monotonic 180 s
  observation/dispatch budget; NEW supervise_ordered_groups,
  group_launch_argv; _summary/_summary_phase gain the bounded group
  label (unit_group=A/B) and the actual child deadline. run_child, the
  owned process-cleanup functions and the observer primitives are
  byte-identical to the base (verified by full-block comparison).
* NEW oap/bin/ci_unit_partition.py (SHA256
  e1030e106035583ea3b1e712714f9d99bfb2d5434223abf04cad63a07c307e7b):
  stdlib-only bounded one-level flat tests/unit partition.
* tests/oap/test_ci_unit_diagnostics.py: 21 -> 29 methods (new 22-29);
  tests/oap/test_ci_unit_partition.py: NEW, 12 methods.
* STATUS.md: current slice 009-r -> 009-s plus the dense 009-s note.
* docs/evaluation.md: new "The 009-s bounded unit process partition"
  section.

Nothing else changed: the protected workflow
SHA256 b919535561a88706d815f79d481aa3480837eb1de75d36b0c89ab7b0d99a6118
is byte-unchanged base -> implementation; ARCHITECTURE.md
4b41905396a3838269fd6cf372614cd23cb2c3b6a37be09f29ed752803c0983a and
oap/governance/MANIFEST.json 24cec23235e3defc5f55bab4690298191d5a233d35dd9bf20b0afb4b3925f922
match the order; pyproject/lock, src, tests/unit, tests/integration,
the prior 009-r report (file SHA256
f9438463c6c542c3d59f1c5fbb59224d1da9f18cecfc938445b29c01baf24a68) and
all prior logs/reports are unchanged.

## Acceptance evidence

1. Canonical checkout/branch/base, exact prior report, terminal
   evidence, three transcript bytes; one same-PR normal push.
   Local branch oap/009-evaluation-baseline at implementation head
   43248572 with first-parent chain dfe301c -> be30982b -> 43248572,
   clean tree, remote branch and PR 11 head verified at dfe301c
   (round base) before push, base main, MERGEABLE, auto-merge absent.
   The exact prior 009-r report bytes, the Root terminal review bytes
   and the three transcript bytes are SHA256-verified above. The single
   ordinary non-force push of the existing branch is performed by this
   publication step (this report cannot certify its own push; the
   separate post-publication execution receipt records the remote
   verification).

2. Two nonempty disjoint deterministic ordered groups from the current
   flat tests/unit layout and exact pytest default file naming, with
   tests/unit/test_owned_gpu_worker.py beginning group B. The cut is
   the order's fixed cut (near 29.8 s in successful 3.14 and roughly
   39 s in the failed 3.12's forwarded postcollection observations;
   both observations from the order/terminal review, no re-derivation).
   Measured at the exact base with the committed helper on the actual
   layout (which includes a real tests/unit/__pycache__ directory left
   by the immediately preceding compileall step): group A = 62 files /
   1421 nodes (ending test_native_tokenizers.py), group B = 56 files /
   1310 nodes (beginning test_owned_gpu_worker.py) - exactly the order's
   62/56 tracked-file expectation. The inventory is bounded one-level:
   scandir under a finite pre-materialization entry ceiling (1024; an
   oversized scope is refused with the "too-many-entries" token before
   any unbounded listing/sort - os.listdir-then-sort is not used);
   admission is exact regular-path only via lstat for BOTH default
   patterns (test_*.py, *_test.py); the generated __pycache__ is
   explicitly admitted as a non-test entry (never followed), other
   hidden entries and ordinary non-test files are not test entries;
   refusal fails closed with bounded reason tokens for a symlinked
   scope, any symlinked scope entry, any nonhidden nested directory,
   any nonhidden non-regular entry, an entry that vanishes under the
   inventory, a missing/non-directory scope, the absent cut file, or an
   empty derived group - never a silent omission. No argv override, no
   file/site cleanup. Negative layout cases are exercised by actual
   owned synthetic filesystem trees in the partition test module.

3. Exact ordered equivalence under the inherited locked environment
   (local venv: python 3.14.4, pytest 8.4.2) via bounded collect-only
   observations, full directory first, then the two actual launch path
   groups (selectors derived from the committed helper). Each
   observation ran under CPU 60 s / AS 1 GiB (prlimit
   --cpu=60 --as=1073741824) / wall 120 s KILL 5 s (timeout -k 5 120)
   in a fresh private 0700 /tmp scratch, with the Root one-thread
   Product setting OPENBLAS_NUM_THREADS=1 plus
   PYTHONDONTWRITEBYTECODE=1, fresh private --basetemp per observation
   and -p no:cacheprovider. Actual results of the final batch: exits
   0/0/0 (walls 2.24 s / 3.07 s / 2.86 s), full = 2731 unique nodes,
   A = 1421, B = 1310; canonical SHA256 of the ordered node lists
   (newline-joined + trailing newline): full
   60da730445d66ef81c1d20cbb367f2dc1203469a28e6309ca86461bd8d764834,
   A 9bec4a3d52e1b7d23f59921efbe2fd421d7b6e78a0c6188d1168fc2ed4a8c069,
   B 5001c6f38cc6eec55abf53936347cb4a223f69e03396cadc4d6d3a9d27a30570.
   Concatenated ordered A+B is byte-equal to the full ordered node
   list (no duplicate, omission, extra or failed collection; both
   groups nonempty). All three canonical hashes and counts match
   Root's independent capped baseline collected from the exact
   unchanged dfe301c paths (audit/009-s-check/Root-base-collect-only/
   Root-full-ordered-collection.json: 2731/118 files, exit 0) and
   Root's independent capped group review
   (audit/009-s-check/Root-capped-actual-group-collection/
   root-summary.json: 62/1421 and 56/1310, exact_ordered_matches_
   original true, unique true); the final batch's full/A/B node lists are also
   byte-equal to Root's archived stdout node lists. No prior-round
   count was asserted without this matching. Original outputs are
   preserved privately on the host (0700 scratch and the supervision
   audit directory); no test body was executed. The hosted positive
   gate on each Product leg (both pytest success summaries, observed
   combined complete unit census, every later required step) is
   evaluated by the fresh full CI at the report head, which Root owns.

4. main supervises group A then group B as separate direct
   invocations of the installed venv pytest console: same exact repo
   cwd, unchanged inherited environment projection (inherited env +
   local VIRTUAL_ENV + .venv/bin first on PATH), same trailing suite
   options after the path selectors - only the ordered path selectors
   differ (group_launch_argv). ONE aggregate monotonic 180 s
   observation/dispatch budget covers both children: A receives the
   full remaining budget and the full 4 MiB display / 16 MiB raw-log
   ceilings; B receives the EXACT remaining aggregate budget
   (monotonic, including A's run and its owned cleanup) and the
   remaining aggregate ceilings via the existing run_child arguments.
   The remaining time is RECOMPUTED immediately before each dispatch,
   AFTER the optional per-child pre-snapshot (which itself spends
   aggregate budget), and the dispatch is vetoed on exhaustion - no
   child ever receives a stale deadline (the exact clock-advance
   proof, no real child, is in Verification). No new dispatch after
   the first nonzero or unproven child, after an exhausted budget, or
   after a final display refusal; an unavailable later dispatch is the
   explicit nonzero 130 (EXIT_LAUNCH_FAILURE) with the bounded stderr
   token "dispatch unavailable: aggregate-budget-exhausted", never a
   synthetic second result. The exact first nonzero exit and the
   original child wait/exit/signal distinctions (124/125/126/127/128/
   129/131/132 vocabulary) are preserved; bounded 10 s kill grace and
   5 s post-KILL owned group cleanup run per launched child; the
   original per-line and per-operation output safety is retained. Each
   bounded per-process summary carries the bounded group label
   (unit_group=A/B; unlabeled output is byte-identical to 009-r) and
   the deadline that child actually received. Per-child own-cgroup
   snapshots and inherited RLIMIT_CPU observation remain status-neutral
   (availability or any delta never changes the computed status or
   exit). The 009-r direct-console admission (direct_launch_projection)
   is unchanged, and run_child plus the owned process-cleanup functions
   are byte-identical to the base.

5. Bounded synthetic OAP tests: the diagnostics module now has 29
   methods (pre-execution census: 20 owned children total, 21
   conservatively budgeted Popen creation attempts incl. test 7's
   failed constructor, 0 grandchildren, short synthetic bounds,
   per-case wall bound, no skip/xfail/selector) - the retained
   existing wait/cleanup/backpressure/interrupt/record tests 1-21 plus
   new 22-29: exact argv/env sameness across both launch groups,
   sequenced two-real-child success with exact remaining-budget
   algebra (0.05 ms bound) and ceiling carryover with hook order, no
   second dispatch after a nonzero first child (exact 7 preserved),
   after an owned-child SIGKILL (131), on an exhausted aggregate
   budget (fake run; 130 + token; zero dispatched), and after a final
   display refusal (126); the process-free label format case; and the
   stale-deadline probe (test 29) exercising the exact clock advance
   WITHOUT a real child (pre-snapshot spends the remaining budget;
   run stub never called; 130 + token; no synthetic result). The
   partition module has 12 methods (0 children): positive
   both-patterns/disjoint/complete/deterministic/absolute cases and
   actual owned-layout refusals (empty scope, missing cut file,
   cut-first -> empty group, nonhidden nested directory, symlinked
   test and non-test entries, symlinked scope, FIFO, missing/file
   scope, hidden and ordinary non-test entries, entry ceiling).
   Local proof is tied to the exact implementation head (files
   SHA256-verified before and during the proofs). One report-only
   SELF child commit follows the exact implementation on the
   transcript; the remote report is verified before the sole normal
   response. Root owns the fresh CI terminal assessment; a required
   failure remains a failure even if one partition or job passed; the
   3.12 signal origin stays unproven, including on a green result.

## Verification

All local proofs used the locked local venv, private 0700 scratch,
and the original caps (CPU 60 s / AS 1 GiB / wall 120 s KILL 5 s per
observation): timeout -k 5 120 prlimit --cpu=60 --as=1073741824.

* Dispatch-guard stale-deadline proof (synthetic; production child
  launch stubbed with a recording seam; simulated monotonic clock; the
  optional per-child pre-snapshot advances the clock from 0 to 181
  against the production 180 s aggregate budget - the exact clock
  advance of the Root provisional probe
  audit/009-s-check/Root-provisional-dispatch-guard-probe.json, which
  had recorded one dispatch at clock 181 with stale deadline 180 on
  the provisional source). Run on the final immutable implementation
  (digests 1b5ab7c1.../e1030e10...): zero dispatches (the recording
  stub was never called), zero dispatched, zero results, unavailable
  = "aggregate-budget-exhausted", exit 130, no display refusal, no
  real child launched. Evidence preserved at
  audit/009-s-check/Coding-corrected-dispatch-proof-final.json. Root's
  independent corrected proof on the same digests
  (audit/009-s-check/Root-corrected-provisional-dispatch-proof.json:
  no_launch_after_exhausting_pre_observation true, exit 130) and the
  same-scene in-suite case (test 29, real monotonic clock) agree.
* Targeted stdlib OAP suite (explicit selection of the two changed
  test modules; -o addopts= -o faulthandler_timeout=60
  -p no:cacheprovider; PYTHONDONTWRITEBYTECODE=1; private scratch
  TMPDIR). First run (recorded by the prior session; console output
  not preserved on disk): 39 tests collected, 2 failures, exit 1,
  wall 68.43 s - assertion outcomes in the new 009-s cases (a default
  10 s teardown grace used instead of the module's short synthetic
  bounds, and a same-deadline body-identity algebra error). One
  changed-byte correction inside the same authorized allowance (short
  synthetic bounds; same-deadline body comparison; the stale-deadline
  probe case added per the Root proof-recovery guidance) and one
  affected bounded re-run under the same exact cap (recorded): 41
  passed, exit 0, wall 32.90 s. Final verification re-run at the
  implementation head (this session; output preserved at
  audit/009-s-check/targeted-suite-final.log): 41 passed, exit 0,
  wall 32.22 s, empty stderr. Root's independent exact stdlib proof on
  the same head (audit/009-s-check/Root-exact-stdlib-proof/, unittest
  -v, exit 0): 41 tests OK in 31.633 s (wall 31.74 s).
* Bounded ordered three-way collect-only batch (selectors from the
  committed helper; -o addopts= -o faulthandler_timeout=60
  -p no:cacheprovider --basetemp <fresh private per observation>
  --collect-only -q; OPENBLAS_NUM_THREADS=1
  PYTHONDONTWRITEBYTECODE=1; fresh private 0700 /tmp scratch): full
  then A then B, exits 0/0/0, walls 2.24/3.07/2.86 s, counts 2731 =
  1421 + 1310, all unique; concatenated ordered A+B byte-equal to the
  full list; canonical SHA256s and Root-baseline match as in
  acceptance evidence 3. Preserved at
  audit/009-s-check/Coding-capped-ordered-three-way-final/ (summary,
  exact outputs, selectors). A prior-session ordered batch (exits
  0/0/0, same counts and canonical hashes, archived by Root at
  audit/009-s-check/Root-capped-actual-group-collection/) used the
  default /tmp pytest basetemp rather than a fresh private one;
  collect-only consumes no tmp_path fixture, so no test-side effect,
  and it is superseded by the fresh-basetemp batch above (deviation
  disclosed, not used as acceptance on its own).
* Static validation at the implementation head: ruff 0.17.4
  (--line-length 100 --select E,F,W) on all four changed OAP files:
  all checks passed; python -m compileall clean; git diff --check
  dfe301c..43248572 clean; run_child and the cleanup primitives
  byte-identical to the base (full-block comparison); workflow,
  ARCHITECTURE.md, MANIFEST, prior report and terminal review
  SHA256s as in Work and scope.

Mock/synthetic vs live: the dispatch-guard proof and tests 22-29 (and
all 12 partition cases) are bounded synthetic models - stubbed launch
seams, simulated or short synthetic clocks, owned synthetic 0700
filesystem trees, 0 or 20 short stdlib children - NOT real kernel/OOM/
signal qualification and NOT the hosted route. The three-way
collect-only batch is a real (locked venv, collect-only, no test
body) observation of the actual layout. No full local unit or
integration execution, no host scans, no further broader diagnostics,
no live model requests/downloads. The fresh full hosted comparison at
the report head is pending at authoring; Root owns the fresh CI and
the honest terminal assessment; no claim is made about this report's
own future push or the report-head checks (the separate
post-publication execution receipt records the observed push and
remote verification only).

## Documentation impact

STATUS.md: current slice 009-r -> 009-s with the dense 009-s note
(terminal 009-r evidence, scoped two-process change, measured group
sizes 62/1421 and 56/1310, collection equality, disclosed setup and
deviation history, pending hosted comparison). docs/evaluation.md:
new "The 009-s bounded unit process partition (same 009
continuation)" section recording the real 009-r outcomes, the limits
of the numeric evidence, the reason for the two-process comparison,
the actual group counts, the exact collection equality, the no-
attribution boundary and the NOT_RUN/PARTIAL state. Source-fixture
and external-qualification status remain truthful (no new live
qualification performed).

## DHA and boundaries

Ordered Decision: NONE; no candidate, append or register change.
Preserved resources: private 0700 scratch trees (suite, three-way
batch, dispatch probe) and their preserved outputs, the prior-session
preserved attempts (including the setup failure and the stopped
probes, all on the host /tmp and the supervision audit directory),
Root's baseline/group/stdlib evidence, and all unrelated worktrees,
shared services and host state untouched. No merge, no auto-merge,
no tag, no release, no deployment, no force push; exactly one
ordinary push of the existing branch at publication; no new waiter or
consumer started; no model/provider/profile change.

## Limitations and remaining work

* Disclosed setup failures (setup outcomes, distinct from assertion
  outcomes): (a) an early mktemp mode-flag failure during scratch
  preparation (no test impact; recorded by the prior session, output
  not preserved); (b) the first full-directory capped collect-only
  WITHOUT the one-thread setting failed silently: exit 1, output
  ending at "collecting ..." with nothing after (preserved on the
  host, 354 B) - the unthreaded numpy/BLAS import demand exceeds the
  1 GiB AS cap; it is an environment setup failure, not a collection
  or assertion failure. The ordered batch was then run under the
  exact one-thread Product setting.
* Stopped out-of-scope probes (authorization deviation, disclosed;
  never used as acceptance; attempts preserved on the host per Root's
  order): a full-directory collect-only at AS 1.5 GiB (partial output
  ending "115 tests collected in 0.37s" plus OpenBLAS thread-creation
  errors on stderr; terminated abnormally, exit 139 as recorded by
  the prior session), full-directory collect-only at AS 2 GiB and
  3 GiB (each exit 0, complete 2731-node lists), and one uncapped
  /usr/bin/time -v full-directory collect-only (exit 0, wall 2.46 s,
  maximum RSS 177276 KiB). These violated the ordered 1 GiB
  cap/one-thread scope, were stopped on Root's explicit order
  (audit/009-s-check/Root-collection-cap-recovery.json), and remain
  excluded from acceptance.
* Prior-session ordered three-way batch used the default /tmp pytest
  basetemp (deviation; no test-side effect; superseded by the fresh
  private-basetemp batch, which is the acceptance batch).
* The fresh full hosted comparison (both Product legs plus all OAP
  jobs) at the exact report head is PENDING at publication; Root
  owns the fresh CI and any actual resource signals. A required
  failure remains a failure even if one partition or job passed; no
  attribution of the 3.12 signal sender is made, even on a green
  result.
* Baseline NOT_RUN; whole 009 PARTIAL; protected
  authority/hardware/right/license/MVP and release gates open;
  DHA NONE; no merge performed.
