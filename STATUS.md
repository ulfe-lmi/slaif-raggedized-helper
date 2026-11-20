# Project status

## Current state (2026-11-20)

- Current (2026-11-20): active objective 009, current slice 009-w
 - Current (2026-11-20): active objective 009, current slice 009-x
  - Current (2026-11-20): active objective 009, current slice 009-y
   - Current (2026-11-20): active objective 009, current slice 009-z
    - Current (2026-11-20): active objective 009, current slice 009-aa
  (AMEND existing PR 11, branch oap/009-evaluation-baseline,
  transcript-first). Objective 008 software is MERGED to main as PR #10
  (server-guarded expected-head merge 5a7b41cc, parents 1a8fddf8 +
  29447168, merge tree equal to 2944; implementation-head CI run
  43388401267 all five jobs / all 78 steps SUCCESS); objective 007 is
  complete and merged as PR #9 (merge commit 1a8fddf8); the 007-a..007-v
  and 008-a..008-g entries below are historical round records retained
  for traceability, their at-time PARTIAL/no-merge wordings and
  report limits preserved. Slice 009-a was the first 009 software wave:
  byte-exact 32-file transfer (322,735 B: six production modules, six
  unit suites, twenty docs/parallel contracts) of the reviewed
  structural text-evaluation dataset admission, supplied graded-rank
  metrics and original-source/span support primitives, plus
  docs/evaluation.md, docs/benchmarks/raw-baseline.md and STATUS
  current-state corrections. Its report-head CI (run 43395492425 on
  21a3cbd) failed ONLY the Product 3.12 unit step:
  test_oracle_and_frozen_private_records expected TypeError from
  dataclasses.replace(result, qualification="QUALIFIED") but CPython
  3.12.16 raises ValueError for an init=False field (Product 3.14 and
  all three OAP jobs succeeded; the production guard refused the
  replacement on both versions). Slice 009-b is the ordered correction:
  the one pytest.raises clause immediately around that call now accepts
  (TypeError, ValueError); every other byte, test, fixture, assertion,
  import and production blob is unchanged
  (docs/ci-dataclass-replace-portability.md). Slice 009-c is the
  source-backed stage-evaluation wave: byte-exact 22-file transfer
  (395,115 B: three production modules — 127,064 B — three unit suites —
  110,520 B — five integration suites — 78,437 B, one of them the exact
  existing raw-hybrid fixture modification — and eleven docs/parallel
  contract/proof documents — 79,094 B) from the reviewed source SELF e6b229b1 (implementation
  748d08b4) per oap/reviews/009-c-components.json (SHA-256
  6fbeb96c23…): 21 NEW + one MODIFY with exact preimage — the raw text
  stage support, declared stage geometry and source-bound stage loss
  components completing the nine private module API families (the nine
  callable private evaluation primitives), with the actual synthetic
  source-backed composition proofs (raw bridge
  V3 eight-attempt pass; stage-loss v2 eight ordered cases — two
  positive / six expected refusals, six native session wrappers reaped,
  no close overages; 51 controlled source-binder unit cases and 45
  geometry unit cases attributed to their exact sources; v1 preflight
  failure retained with the separately approved v2). The independent
  COMPLETE software-coverage audit 2624 (Root adjudicated;
  oap/reviews/009-c-software-coverage-adjudication.json) confirms the
  remaining ABSENT production software: a callable cohort pipeline
  joining frozen split selection, per-case producer traces/source
  binding, source Recall@20/60/multi-source/stage-loss aggregation and
  total/defined/undefined/refused denominators with private report
  provenance (an operator loop is not harness software; separately
  ordered same-009 continuation). Slice 009-d is the
  declared-cohort-metrics wave: byte-exact 5-file transfer
  (89,811 B: one production module — 32,800 B — one unit suite —
  22,772 B — three docs/parallel contract/oracle/API documents —
  34,239 B) from the reviewed source SELF b33da381 (implementation
  b15adaf) per oap/reviews/009-d-components.json (SHA-256
  665c7118…): five NEW blobs verified absent at the round base b87e264d,
  copied by immutable Git object and re-verified by blob ID/size/SHA-256
  — the pure declared-cohort aggregation (exact normalized rationals,
  six prefix summaries and seven transition summaries over 1–256
  supplied cases, source-macro vs pooled denominators distinguished,
  explicit OR/no-Gold undefined reasons, content-free whole-call
  refusal, chunk MRR/nDCG UNAVAILABLE without an explicit chunk
  relevance mapping) completing the ten private module API families.
  Attributed local proof (oap/reviews/009-d-local-admission.json): ONE
  approved current Ruff format/check and 33 complete unit tests PASS
  under Python 3.14 (CPU 15 s/AS 1 GiB/wall 90 s/FSIZE 32 MiB/CPU 0,
  plain assertions/cache enabled) at source 743a8949…/unit
  5a60130f…; GNU 1.81 s wall waited-process observation only; the
  earlier 19/22 passes predate corrected semantics/metering; the final
  API-only amendment did not rerun tests (source/test identical). At
  009-d time the callable SOURCE-RUNNING cohort pipeline, joined
  private split report and actual cohort composition proof were ABSENT
  (separately scoped source-runner lane at immutable b33da381 after
  normal quiet per oap/reviews/009-d-replan.json — the lane whose
  reviewed output is the 009-e transfer below). Slice 009-e is the
  source-cohort-runner wave: byte-exact 9-file transfer (167,455 B: one
  production module — 43,767 B — one unit suite — 31,638 B — one
  integration suite — 27,711 B — five docs/parallel contract/proof
  documents — 64,339 B) from the reviewed source SELFs 91f31182 (runner
  lane; implementation 3c92a59d) and 5ffef4c1 (proof lane;
  implementation 60b17137 over preparation 657fbf57) per
  oap/reviews/009-e-components.json (SHA-256 b73448cf…c55c8e6): five
  runner blobs and four proof blobs, all nine NEW and verified absent at
  the round base 598d6dc6, copied by immutable Git object and
  re-verified by blob ID/size/SHA-256 (the 117 shared production files
  plus pyproject/uv.lock/workflow byte-identical at both source SELFs
  and the canonical base; no lower adaptation). It implements the
  source-running cohort pipeline source_cohort_runner.run_cohort —
  full canonical dataset admission before selection (1–256-case and
  512-Gold software bounds), declared split/subset selection
  (FULL_ADMITTED_SPLIT/DECLARED_SUBSET, no omitted or failed cases),
  per-case effective-authority intersection before the traced producer
  with original authority at the source-bound binder, the borrowed
  old-generation snapshot pin, full dataset and all Gold bundles for
  every binder, one pure aggregate only after complete success, the
  joined private split report with stable private linkable identities,
  and whole-cohort refusal with
  intended/attempted/completed/refused/pending prefixes and no
  surviving-subset report — the eleventh private module API family,
  closing the coverage-2624 harness gap as software. The canonical
  round was static transfer plus documentation (no local source run)
  and corrected the three 009-d documentation precision findings in the
  current docs (lexical 4→5→6→7 removal edges; OR
  AMBIGUOUS_ALTERNATIVE_SOURCE_UNIVERSE versus the no-Gold
  NO_GOLD_REQUIREMENTS/NO_GOLD_SOURCES reasons; the pure 13-tuple /
  declared-field-insertion-order identity encoding versus generic
  sorted-key JSON, distinct from the runner wrapper encoding).
  Attributed source-lane evidence, not rerun: 54 controlled units and
  the focused Ruff check PASS at the corrected runner source
  96e69714…/unit 4d01ca5c…; ONE actual synthetic composition proof
  against the exact driver/source/oracle (full 5-case dataset, four
  selected cases, 6 selected/7 full Gold occurrences, three bundles for
  every binder; four outer attempts; seven producer / six binder / one
  aggregate direct calls; no surviving subset; success pins
  5/producer 4/binder 4/aggregate 1; missing query zero delegates;
  changed space 4/3/2/0 with PRODUCER 4/3/2/1/1; closed pin zero
  delegates with PREFLIGHT 4/0/0/0/4); one generator observed exit 0
  and six captured session wrappers deliberately closed/reaped 143 —
  not six zero exits nor whole-tree containment; observed pytest
  59.29 s, launcher 62.39849 s, SELF 2.707422 plus waited CHILDREN
  58.910207 CPU s, sampled scratch 286,066 B/74 entries (observations,
  not aggregate hard bounds); the first inventory and first collection
  guard failures were retained with the separately corrected checks
  passing; Root independently ran ten controlled cleanup cases once
  (PASS; coding author did not rerun). Slice 009-f is the
  graded-evaluation-program wave: byte-exact 17-file transfer (230,430 B:
  two production modules — 79,975 B, one of them the exact minimal
  shared-loop replacement of source_cohort_runner.py — three test suites
  — 73,822 B — and twelve docs/parallel contract/proof documents —
  76,633 B) from the reviewed source SELFs f4d9dbb2 (existing graded
  interop proof; implementation 1dcf7c3e), 45bcb729 (graded evaluation
  core; implementation 7df7e79c over f4d9dbb2) and e3bf5b84c (genuine
  program proof; implementation 5d79e3d6 over 45bcb729) per
  oap/reviews/009-f-components.json (SHA-256 1ff91482…cd6b): sixteen NEW
  plus one MODIFY verified against its exact preimage b69589c3, copied
  by immutable Git object and re-verified by blob ID/size/SHA-256; no
  lower adaptation (120 of 122 shared production/config/workflow paths
  byte-exact, the two intentional deltas only). It implements the
  private callable graded evaluation program
  evaluation_program.run_evaluation — all-case plan/judgment/cutoff/
  grade-budget admission before any pin/source/producer, per-case
  grade-owned pin bracketing one genuine explicit judged-ID source
  binding under effective authority, one additional catalog load, the
  exact source-only report preserved, exactly three supplied metric
  aggregates (one per dense/lexical/fusion variant, zero direct score
  queries) only after all cases succeed, the private graded report
  embedding the source identity payload once, thirteen fixed failure
  phases and whole-call refusal with no surviving subset — the twelfth
  private module API family; the runner's public source-only behavior is
  unchanged and regressed against the three pre-implementation legacy
  identity goldens. Attributed source-lane evidence, not rerun: 98
  controlled units (54 unchanged old runner + 44 new) with the three
  legacy identity goldens and the full-256 moderate synthetic check; ONE
  actual two-query synthetic lower graded interop process (two producer
  / three stage binder / five judged-ID grounding / six direct score /
  three aggregate, four real refusals; one generator exit 0, six
  wrappers reaped 143); ONE actual whole-module genuine graded program
  proof v3 (full 5-case/7-Gold/3-bundle universe, h1/h4 selection;
  direct totals owner 19 / producer 6 / binder 6 / source aggregate 2 /
  pre-catalog 2 / grade binder 4 / rank aggregate 3 / direct score 0;
  exact legacy source-only output equivalence; bool preflight 0, later
  ineligible b:0 GRADE_BIND 2/2/1/1/0, closed pin CATALOG 2/0/0/0/2; six
  real captured wrappers closed/reaped 143; zero generators via one
  cached data-only fixture; observer SELF+waited CHILDREN CPU delta
  64.584229 s, pytest SELF peak 94,252 KiB = 92.04296875 MiB, children
  max RSS 72,036 KiB — distinct scopes, not additive); the initial broad
  read/lane-isolation FAIL (fresh semantic 341,392 B > 262,144 B
  allowance by 79,248 B) is retained, not a pass. Whole 009 remains
  PARTIAL: the source-running cohort harness and joined private split
  report are now implemented software (009-e) and the private graded
  evaluation program over the shared source loop (009-f) — each backed
  by tiny synthetic composition proofs only — weaker substitutes for the
  required representative real baseline; no real-model retrieval quality, human held-out data,
  corpus rights/current principal-policy authority or qualified
  encoder, and no real baseline (raw baseline NOT RUN); the 1–256-case
  / 512-Gold runner admission and the 512-row catalog diagnostic bound
  (≤ 512 rows / 256 cases / 512 global Gold occurrences in the joined
  components; 512 cases / 16 MiB at standalone admission) and the
  synthetic three-revision fixtures are software bounds, not 20k
  qualification. Hardware/visual/license/ICA/full-MVP gates retained;
  historical 009-a/b/c/d at-time evidence and the 008 accepted state
  preserved; no 010 activation; no merge. Public serving, current
  principal/current policy, evidence delivery and real qualification
  remain absent/open. Slice 009-g is the bounded test-origin context
  repair (same 009 continuation, AMEND PR 11 at round base 4e2d073a,
  the 009-f report head whose hosted CI FAILED): run 43921457809 —
  product 3.12 job 133489544939 and 3.14 job 133489545017 each
  2445 PASS / 4 FAIL in the full default tests/unit session, the
  four failures being exactly the four origin entry nodes of
  tests/unit/test_evaluation_program.py (every per-module local
  origin predicate passed, then the helper's misplaced final global
  assertion failed summing session-loaded product/test source-file
  EXTENTS, 2,923,383 B, against the focused 2 MiB readset ceiling —
  stat extents are not actual bytes read or RSS); three OAP jobs
  SUCCESS; integration/downstream product steps SKIPPED, not green;
  one orphan bwrap per failed product leg reported at cleanup
  (origin/state/ownership UNPROVEN, no causal attribution, no worker
  fix). Root causal review and D0 scope decision retained at
  oap/reviews/009-g-ci-finding.json and oap/reviews/
  009-g-scope-decision.json. The repair removes only the misplaced
  global sum from the broad default suite and keeps the strict
  global local-origin invariant (real local __file__ resolving under
  assigned root/src for every loaded slaif_raggedized_helper
  package/module and under root/tests/unit for every loaded test_
  module; foreign/missing/non-file/resolved-escape origins still
  fail at the same four entry points) plus new bounded
  synthetic-metadata regressions (legitimate focused and broader
  local metadata pass — including local test extents above the old
  2 MiB sum — while foreign package/test origin, missing
  __file__/non-file and resolved path escape fail); no cap raise,
  no skip/xfail/filter, no collection change, no
  sys.path/sys.modules manipulation, no fake package modules, no
  product helper/API/module added. Source implementation unchanged:
  evaluation_program.py 84aceffc… and source_cohort_runner.py
  d9f1b0e8… byte-exact; the focused 98-unit source proof evidence
  stays tied to those old exact bytes (no rerun, no retrospective
  cap change); the new regressions and the new-head full hosted CI
  are new evidence. Only tests/unit/test_evaluation_program.py,
  docs/evaluation.md and STATUS.md changed; static local
  verification only (Git/read/hash/AST/JSON), no local runtime.
  Real baseline NOT RUN; current policy/qualified encoder/data/
  rights/CLI/plan/publisher/native-OS/20k/hardware/visual/security/
  license/merged-ICA/MVP/release gates preserved; 009-f 17
  components = 16 NEW + one MODIFY (actual NEW groups 5+6+5,
  per-source total groups 5+7+5, Root clarification); no 010
  activation; no merge.
  Slice 009-h is the bounded stat-fixture constructor correction
  (same 009 continuation, AMEND PR 11 at round base 857355ab, the
  009-g report head whose hosted CI FAILED, run 43931502904: three
  OAP jobs SUCCESS, product 3.12 job 133524822329 FAILED in the new
  broad-session regression's fake_stat — os.stat_result(*values)
  expands ten fields into ten arguments, TypeError, then pytest
  INTERNALERROR re-entering the scoped Path.stat monkeypatch with no
  complete summary — product 3.14 job 133524822987 one F then exit
  137 with cause UNPROVEN, not equated with the 3.12 defect or OOM;
  78 required steps 64/2/12; integration SKIPPED, not green). The
  correction is the exact one-character fixture substitution
  os.stat_result(values): test 24,446 B 085f0cea… to 24,445 B
  59f093b4…, all 50 default nodes (44+6) and every other byte
  preserved; program 84aceffc… and runner d9f1b0e8…
  byte-exact unchanged. NEW Root-owned independent bounded
  verification (Root proposal 52f4fe9c… / result 0fb613bb… /
  log beb63602…, 11,326 B): one authorized direct pytest child
  under the frozen caps (CPU 20 s / AS 1 GiB / wall 120 s / core 0 /
  file 16 MiB / affinity 0 / five threads 1, private fresh 0700 /tmp)
  passed 104/104 (54 runner + 50 program, all six new provenance
  regressions and four origin entry points), no skip/xfail/xpass,
  all 79 frozen input identities rechecked unchanged post-run;
  waited-children CPU 7.725588 s user / 0.094994 s system,
  parent-observed wall 7.952863 s, waited-children high-water 87,292
  KiB absolute. The coder's static-preflight product-check launcher
  was NOT RUN (preserved as reference); the static AST inventory was
  generated without product imports; Root owned the actual 104-unit
  process; the Root stdlib
  value witness (expanded ten fields TYPE_ERROR, single-sequence
  st_size 3,145,728) is not product/CI acceptance. Old 98 focused
  units stayed tied to old test bytes 593a3be6… (program/runner
  the same exact bytes across 009-f/g/h); regression intent is not a
  pass. Only tests/unit/test_evaluation_program.py, docs/evaluation.md
  and STATUS.md changed; no coding-side local check/import/collect/
  lint/setup. New-head full complete hosted product/integration
  3.12/3.14 plus all three OAP jobs PENDING at publication; real
  baseline NOT RUN; current policy/qualified encoder/data/rights/
  CLI/plan/publisher/native-OS/20k/hardware/visual/security/
  license/merged-ICA/MVP/release gates preserved; no 010 activation;
  no merge.
  Slice 009-i is the bounded unit-exit diagnostic (same 009
  continuation, AMEND PR 11 at round base 7117201, the 009-h
  report head whose hosted CI FAILED, run 43949914814: four jobs
  SUCCESS - three OAP legs plus product 3.14 job 133589341005
  with full unit/integration progress at 100%, retained
  multithreaded-fork DeprecationWarning not a failed gate or
  full OS certificate - one FAILURE: product 3.12 job
  133589340533 unit step exit 137 after 90% progress plus 52
  dots, no failed-node traceback or completed summary, six
  downstream steps SKIPPED; 78 required steps 71/1/6; precise
  cause UNPROVEN - no OOM/sender/culprit-node/
  constructor-recurrence claim). The change is diagnostic-only:
  the Product test suite step alone changes from quiet
  uv run pytest tests/unit -q to /usr/bin/time -v uv run pytest
  tests/unit -o addopts= -vv after an executable /usr/bin/time
  check (workflow 14,095 B a26bda03... to 14,169 B
  556fa14d..., every other workflow byte unchanged):
  reporting-only - no selector, filter, skip, xfail or
  splitting; full suite/node set/order, both matrix legs, the
  20-minute product job limit and all downstream
  integration/OAP/governance/help/doctor gates unchanged; GNU
  time adds one external parent and reports command
  resources/termination - an observation boundary, not process
  ancestry proof, measured allocation, additive/delta high-water,
  live-tree/cgroup accounting or OOM proof; a last printed node
  is localization, not cause. Root's 009-h independent 104/104
  focused units remain prior bounded evidence, not a full-suite
  replacement or localization. No product fix/capacity change/
  workflow weakening/test change; no coding-side local product
  execution (static Git/hash/text verification only; exact
  three-path diff/hashes through the Root regular-file gate).
  New-head full complete hosted CI PENDING at publication; no
  current or future green certificate, cause claim, baseline or
  whole-MVP acceptance; real baseline NOT RUN; current
  policy/qualified encoder/data/rights/CLI/plan/publisher/
  native-OS/20k/hardware/visual/security/license/merged-ICA/MVP/
  release gates preserved; no 010 activation; no merge.
  Slice 009-j is the bounded unit-diagnostics deadline (same 009
  continuation, AMEND PR 11 at round base a7ad70b, the 009-i
  report head whose hosted CI CANCELLED, run 43962945486: three
  OAP jobs SUCCESS; product 3.12 job 133634863960 and product
  3.14 job 133634863970 CANCELLED by the unchanged 20-minute
  job limit, both check-runs annotated "exceeded the maximum
  execution time of 20m0s"; raw terminal API 76 steps - 60
  completed SUCCESS, 2 unit steps labelled in_progress, 14
  downstream pending - with the two Complete job steps absent:
  inconsistency preserved, never promoted; precise blocked
  node/underlying cause UNPROVEN - connector logs 404
  BlobNotFound, gh --log 0 bytes not execution/success evidence;
  earlier 009-h exit-137 cause also UNPROVEN). The change is
  diagnostic-only: the Product test suite step alone becomes
  PYTHONUNBUFFERED=1 /usr/bin/time -v /usr/bin/timeout
  --signal=TERM --kill-after=10s 180s uv run pytest tests/unit
  -o addopts= -vv -o faulthandler_timeout=60 behind executable
  /usr/bin/time and /usr/bin/timeout checks (workflow 14,169 B
  556fa14d... to 14,317 B fc1ba2cd..., every other workflow
  byte unchanged): a disclosed LOWERED 180-second unit-command
  deadline - TERM on expiry, KILL after 10 s if necessary, any
  timeout/nonzero exit fails the step and never succeeds;
  builtin faulthandler_timeout=60 requests a stack dump only
  (no cancellation/cause proof/OS containment); unbuffered
  output reduces lost progress only; missing tools fail loudly,
  no install; no selector/filter/skip/xfail/split/pipeline/
  background/status-mask/continue-on-error/retry; full
  suite/node set/order, both matrix legs, the 20-minute product
  job limit and all downstream
  integration/OAP/governance/help/doctor gates unchanged;
  external time/timeout change ancestry/observation boundaries
  only (no live-tree accounting, descendant reap, escaped-child
  containment, exact allocation or OOM cause); a printed
  stack/last node is localization only and a >180 s command may be
  a legitimate slow case to preserve and replan from evidence -
  never cap-raise or suite-filter authority. Program 84aceffc/
  runner d9f1/unit 59f093b4 bytes unchanged. Root's 009-h
  104/104 focused units remain separate prior bounded evidence,
  not a full-CI substitution. No product fix/capacity change/
  workflow weakening/test change; no coding-side local product
  execution (static Git/hash/text verification only; exact
  three-path diff/hashes through the Root regular-file gate).
  GitHub-hosted new-head full complete CI PENDING at
  publication and is the first actual invocation of the revised
  command; no current or future green certificate, cause claim,
  baseline or whole-MVP acceptance; real baseline NOT RUN;
  current policy/qualified encoder/data/rights/CLI/plan/
  publisher/native-OS/20k/hardware/visual/security/license/
  merged-ICA/MVP/release gates preserved; no 010 activation;
  no merge.
  Slice 009-k is the owned unit-diagnostics supervisor (same 009
  continuation, AMEND PR 11 at round base cc51b9a, the 009-j report
  head whose hosted CI CANCELLED - run 43978029330: 3 OAP SUCCESS;
  both product jobs CANCELLED; cause UNPROVEN, hypothesis only).
  Diagnostic-only: the Product test suite step alone becomes
  PYTHONUNBUFFERED=1 /usr/bin/time -v python3
  oap/bin/ci_unit_diagnostics.py (workflow fc1ba2cd... to 29a44dd6...;
  other bytes unchanged). The private stdlib supervisor (no
  product/operator API, no new dependency) spawns the fixed uv run
  pytest tests/unit -o addopts= -vv -o faulthandler_timeout=60 as
  argv (no shell) with PYTHONUNBUFFERED=1, stdin DEVNULL,
  stdout/stderr to an exclusive 0600 log in a private 0700
  RUNNER_TEMP dir (raw bytes retained; PRESERVED, never deleted; no
  PIPE/runner output). Parent forwards finite 64 KiB reads: 4 MiB
  cap, 4,096-byte labeled escaped segments, finite wall/byte
  backpressure on job stdout (refusal = honest OBSERVER_FAILURE,
  offset recorded); 180 s child deadline; every post-launch exit runs
  bounded owned teardown first: identity-verified group TERM, 10 s
  grace, bounded KILL sweep (labeled, not claimed; no host scan), ONE
  shared 5 s post-KILL budget, single bounded reap; recycled PID/PGID
  never signalled; exit codes preserved exactly (0/7/5; named CLD
  decoding; signalled child separate field); private 0600 status
  record holds full result; nonzero 124-132 statuses; uncertainty
  stays nonzero; only complete zero + proven teardown returns 0.
  Limits: no host guarantee for a persistently blocking channel, no
  proof of the old cause, no universal descendant containment, no
  live-tree guarantee. Full unit set/order, both matrix legs,
  20-minute job limit, all downstream gates unchanged; no
  selector/filter/skip/xfail/split. New default-discovered unittest:
  v1 14-case proposal NEVER_RUN; v4 census (pre-execution): 19
  methods, 13 returned/owned stdlib children + 1 failed Popen
  constructor/exec attempt (test 7; conservatively budgeted 14
  creation attempts; no invented PID), 0 grandchildren, max 1
  concurrent. V4 static: t11 honest-bounded cap contract + near-cap
  oracle; t13 real private abort-record truthfulness (primary
  unmasked, no external-signal claim); t18 post-teardown-only
  real-child sink refusal (honest 126); t19 prelaunch private
  record, zero Popen; final-summary record run_status +
  summary_status (126 intended, never falsely OK).
  009-K_CHECK_EVIDENCE (finite, true): Root-owned actual check (not
  a coding-owned run): 19/19 PASS, 0 fail/err/skip, 14 constructor
  attempts = 13 returned/owned children + 1 failed constructor/exec
  attempt, 0 grandchild, max 1 concurrent, all reaped in supervised
  teardown, no Root rescue, 20/20 post/current hashes matched; local
  Python 3.14.4 stdlib only, wall 14.745 s, waited-child CPU 0.244 s,
  RSS high-water 79,548 KiB (not aggregate); exact source
  3e15bf1c2e3707de12365ffb6ec73fd24b180c9e7ea023b0817d853c04ab3681 /
  test e4f348a12defe4b4996ef553c33c544c297acf17b4f1a0c7cca5363804c6ab65;
  full log 2,948 B sha256
  1ca4be4ec4e367a67a633120ed6f7d17e958a3ddf4e7efa2c9673f2ca87c7279
  preserved. Amended per-process limits only (CPU 20 / AS 512 MiB /
  FSIZE 32 MiB / NOFILE 256 / CORE 0 / affinity 0 / alarm 90; rescue
  5 s limit, none used): not an aggregate/OS-blocking/external-
  SIGKILL/adoption/escaped-descendant theorem; no production rlimit.
  On refusal forwarded_bytes = queued/attempted display bytes, not
  guaranteed delivered; exact raw log distinct from bounded display
  + summary phase. V3 17-case attempt 16 PASS/1 FAIL t11 (log
  b60807561943df885b95d60bc46659886a0032cec9e923156080207502cfc8cd
  preserved): old per-case values unobserved, old cause not proven;
  the new deterministic near-cap oracle + honest-bounded contract is
  what passes; no invented old result. Peer frozen-V2 K20-K22
  findings differentially resolved by Root current bytes + actual V5
  regressions (peer did not review V5; not a merged ICA). Hosted CI:
  head cc51b9a CI 43978029330 CANCELLED (20m0s, cause UNPROVEN,
  output-ownership hypothesis only); fresh head CI
  PENDING/NOT_YET_RUN; product command/matrix/order/downstream
  gates/job cap unchanged; no local full-product or existing OAP
  suite claim. Representative baseline NOT_RUN; plan
  wire/publisher/principal/policy/real-CPU encoder/held-out data +
  rights/operator/runtime/hardware/visual/security/license/merged-
  ICA/full-MVP/release gates OPEN; no 010/merge/deploy claim.
  pyproject already excludes oap/bin + tests/oap from product Ruff
  scope; no new lint task or exclude change; fresh head normal CI
  must pass all product lint/OAP checks/matrices. No green
  certificate, cause claim, baseline or whole-MVP acceptance; gates
  preserved; no 010, no merge.
  Slice 009-l is the bounded pytest case-ID metadata repair (same 009
  continuation, AMEND PR 11 at round base 3f8b4eb0, the 009-k report
  head whose hosted CI run 44017736685 FAILED: 3 OAP SUCCESS; both
  product jobs FAILURE - 2455 collected per run, verbose auto-derived
  parameter IDs serialized large scalar fixtures (first 65,537 B
  header) into node names, supervisor raw 16,843,391 B crossed 16 MiB,
  OVERSIZE 128 after 5.62/5.97 s; current observed failure, old
  20-minute/exit-137 causes remain UNPROVEN). Metadata-only: the
  exact fifteen named parametrize calls gain one explicit bounded
  literal ids= tuple of short lowercase ASCII labels (90 total; 1..48
  chars, unique per call, content-free); every fixture
  value/expression, body, name, argument, count and order preserved -
  static AST differential removing exactly the new ids keywords
  yields the exact preimage AST for all fifteen files. Display-only
  impact (verbose node IDs no longer embed large scalar payloads);
  2455-case set/order/matrices/supervisor/workflow bytes and all
  limits unchanged; no src/, no limit increase, no filters/skips/
  xfails. Verification: hash/Git/diff/text/AST-shape checks plus
  three actual Ruff invocations disclosed as an order deviation
  (1: proper 15-file run, repo pyproject config, ruff 0.17.4, exit
  0, "All checks passed!"; 2: supplemental /tmp preimage run under
  ruff default config, no evidentiary value claimed; 3: tests/unit/
  directory run, repo config, exit 0; no further runs made); no
  local product/native/test/collection execution claimed; fresh
  head CI PENDING as the actual whole-unit run; representative
  baseline
  NOT_RUN; current principal/policy/encoder/data+rights/CLI/parser/
  publisher/raw-ceiling/hardware/visual/security/license/merged-ICA/
  MVP/release gates preserved; no 010, no merge; DHA NONE.
  Slice 009-m is the exact reviewed private-component blob transfer (same 009
  continuation, AMEND PR 11 at round base 494a1908, the 009-l report
  head whose fresh hosted CI run 44022614755 SUCCESS, all five jobs/78
  steps/five status contexts, both 3.12/3.14 unit legs 2455 passed).
  The EXACT 16 Root-indexed blobs (7b4f4ec0, 11,722 B; 14
  implementation + 2 byte-identical archival reports) were copied from
  source Git objects only (parser ceef2888/82923f0; publisher
  70bf21fc/6196ef2; preparation bases e3bf5b84/45bcb729 are NOT
  canonical ancestors - no branch merge/cherry-pick or
  preparation-history import): two source modules, two unit modules
  (186 parser + 88 publisher cases) and ten contract/API/order docs;
  the two archival reports under oap/provenance/009-m/ keep their
  original SELF resolving the original report heads 82923f0/6196ef2,
  never a later copy commit (source-graph mapping explicit in the Root
  ledger and archives). All 16 destinations verified NEW at 494a,
  byte-exact after copy (sha256 + size + blob OID); core
  evaluation_program.py / source_cohort_runner.py / pyproject.toml
  hashes unchanged vs index. One authorized static .venv/bin/ruff
  check of the four new Python files: exit 0, "All checks passed!"
  (static lint only; no local test/import/collection/product
  execution). Fresh report-head full CI is the first canonical
  combined run and must collect the expected 2729 unit cases = 2455
  current + 186 parser + 88 publisher (expectation only; a mismatch is
  a stop, not a silent adjustment), every new case actually run, not
  skipped; the inherited scoped source evidence (284 parser PASS =
  186 + 44 + 54, 88 publisher PASS) is historical on the exact source,
  not a fresh combined claim. Parser admission stays a private 8 MiB
  closed wire to real Plan objects, not current auth/grades truth;
  publisher private unnamed-stage/no-replace/durability/cleanup
  contracts remain exact with no new target or hardware qualification
  from import; pure policy primitives remain separately INERT design
  work. The source workload illustration is 20k CHUNKS, not 20k
  documents; the raw 4096-row ceiling stays open. Existing local
  real-resource evidence is neither erased as globally unproven nor
  universalized. The prior 3f8b4eb run 44017736685 OVERSIZE128 failure
  is preserved (auto parameter IDs/oversized step output);
  only the older 20-minute/exit-137 underlying causes remain UNPROVEN.
  no-auth/no-current-policy/no-real-producer/no-model-qualification
  labels, full baseline NOT_RUN and rights/privacy/visual/security/
  license/hardware/merged-ICA/MVP/release gates preserved; whole 009
  PARTIAL, no deployment readiness implied, no 010, no merge; DHA NONE.

  Slice 009-n is the diagnostic-to-publication continuation (same 009
  continuation, AMEND PR 11 at round base 0b131157, the 009-m report
  head whose run 44028728886 completed FAILURE with only the two
  Product unit steps (3.14/3.12) failed and all OAP jobs SUCCESS; the
  earlier five unit failures UNTRACED and the native exit causes (139
  on 3.14, 137 on 3.12) UNPROVEN; the 009-l report/CI evidence at
  494a1908 run 44022614755 SUCCESS preserved). Bounded local
  diagnostics (private audit only): with the original configuration
  the comparison observed 40 OS threads and nearly exhausted virtual
  address space (RuntimeError at the 8th partially-started publisher
  thread); only OPENBLAS_NUM_THREADS=1 in the test subprocess changed
  collection to one OS thread and made the same case pass; publisher
  88/88, and after the fixture correction 89/89 with the fixture
  owning partially-started threads (abort barrier/signal, bounded
  joins, re-raise of the exact original exception) - local comparison
  and selected tests, not actual CI, no native pool owner or CI cause
  claimed.
  Changed semantics: specio parse_spec_json runs the quote-aware
  64-container parity_io depth check before json.loads (native
  RecursionError fallback kept); the manifest read loop bounded to
  captured size plus one with immediate excess refusal (O(captured
  size), reaching the existing global limit only at that size); one
  Ruff exit 0 on the two refined files and one bounded selection
  19 passed, no skips (observer n=19 sel=0); publisher bytes keep
  their accepted 89-case evidence. Two new default cases (publisher
  partial-start cleanup; one at-limit spec parsing) make the full
  default count EXPECTED 2731 = 2729 + 2 (expectation only, awaiting
  actual CI; no narrower CI selection). Baseline NOT_RUN; protected
  authority/hardware/right/license/MVP and release gates open; whole
  009 PARTIAL; no merge; DHA NONE.

  Slice 009-o is the Product CI thread-budget continuation (same 009
  continuation, AMEND PR 11 at round base 21341795, the 009-n report
  head whose run 44656541114 completed FAILURE: both Product legs
  (Python 3.12 and 3.14) collected 2731, passed 2730, and failed the
  16-slot publisher test with RuntimeError (can't start new thread)
  inside the fixture's Thread.start; the cleanup regression, the
  reader cases and the four other previously failing publisher cases
  passed, the three OAP jobs succeeded, mandatory downstream steps
  were skipped, and the earlier fatal exits 139/137 did not recur; the
  hosted OS thread-refusal cause remains unproven). The single scoped
  change adds the two-line step env OPENBLAS_NUM_THREADS='1' to the
  unique Product test suite step (both Python matrix legs) of the
  unchanged .github/workflows/oap.yml, reproducing the bounded local
  comparison in which only that setting changed collection from 40 OS
  threads to one, VmSize from 1,838,972 to 241,244 KiB, and made the
  same publisher case pass (publisher-only selection 88/88) - a local
  comparison, not proof of the hosted cause. No product or test
  edits, no fixture weakening, no job/deadline/limit or other thread
  setting change; the 16 real concurrent publication reservations and
  all test assertions are preserved; the supervisor bytes are
  unchanged and its run_child call inherits the step env through
  Popen without override. Fresh full Product matrix plus all OAP
  checks at the new report head decide the outcome (pending at report
  authoring); baseline NOT_RUN; protected authority/hardware/right/
  license/MVP and release gates open; whole 009 PARTIAL; no merge;
  DHA NONE.

  Slice 009-p is the publisher concurrency-case isolation (same 009
  continuation, AMEND PR 11 at round base e9f24bae, the 009-o report
  head whose run 44662270802 completed FAILURE: both Product legs
  (Python 3.12 and 3.14) with the observed OPENBLAS_NUM_THREADS=1
  step env again collected 2731, passed 2730 and failed the same
  16-slot publisher test with RuntimeError (can't start new thread)
  inside the fixture's Thread.start; the three OAP jobs succeeded and
  the mandatory downstream steps were skipped; the hosted cause
  remains unproven). Scoped changes: the two experiment env lines are
  removed from .github/workflows/oap.yml, restoring the whole
  workflow byte-for-byte to the pre-experiment 21341795 preimage
  (SHA256 29a44dd6, original suite selection and downstream steps);
  and the one 16-slot testcase now launches one fresh sys.executable
  -c process (parent 20s bound, zero exit, one fixed success marker
  only after all child assertions) whose fixed inline child
  self-binds CPU 5s / AS 512 MiB / CORE 0 / FSIZE 16 MiB before any
  import, runpy-loads the exact resolved physical test path, checks
  the existing origin assertions and calls the unchanged shared
  fixture under a real pytest.MonkeyPatch with a genuine-reservation
  observer (16 distinct real reservations, baseline registry
  restoration, refused 17th publication before open, real worker
  termination); no pytest recursion, no preexec_fn; the shared
  fixture, the two-thread partial-startup regression and the default
  collection (2731 expectation) stay unchanged. Local actual
  results: the first bounded publisher-module run failed only the
  isolated child at real Thread.start under its own 512 MiB cap
  (88/89); Root's controlled diagnosis (same instrumented program;
  caps inside-only and exec+inside both failing at the same point;
  the single MALLOC_ARENA_MAX=1 child env passing all 16 real
  reservations) authorized that one child-only env line, and the one
  bounded changed-byte re-run under the same exact envelope passed
  89/89. Fresh full Product matrix plus all OAP checks at the new
  report head decide the hosted outcome (pending at report
  authoring); the hosted limiting resource and hosted benefit remain
  unproven. Baseline NOT_RUN; protected authority/hardware/right/
  license/MVP and release gates open; whole 009 PARTIAL; no merge;
  DHA NONE.

  Slice 009-q is the combined CI process-resource comparison (same
  009 continuation, AMEND PR 11 at round base 3522d263, the 009-p
  report head whose run 44667676605 completed FAILURE: Python 3.12
  Product collected 2731 with all 24 steps succeeded (2731 unit
  passes; the separate integration step and all other required
  steps succeeded); Python 3.14 collected 2731 and emitted 2532
  pass marks before child exit 137 without a final summary, last
  unfinished forwarded node
  test_controlled_two_partition_full_stages_exceed_return_cap with
  its six subsequent steps skipped; both versions passed the
  corrected 16-slot publisher case; the three OAP jobs succeeded;
  neither the exit status nor that last forwarded node establishes
  the cause). The 009-o Product-step OPENBLAS_NUM_THREADS=1 trial
  alone left the publisher thread-start failure on both versions
  while each job completed the other 2730 cases, including that 3.14
  last forwarded node, and a separate local controlled probe reduced
  collection from 40 native OS threads to one. The scoped change
  restores the exact two-line env stanza OPENBLAS_NUM_THREADS='1'
  under the unique Product test suite step (both Python matrix legs)
  of .github/workflows/oap.yml, making the whole workflow byte-for-
  byte equal to the e9f24bae postimage (SHA256 b9195355) while
  retaining the successful 009-p isolated-child allocator setting,
  every test and required check, suite selection, downstream steps
  and all limits - a bounded combined comparison without attributing
  the hosted exit to OpenBLAS. Both full hosted Product matrices are
  required again. Fresh full Product matrix plus all OAP checks at
  the new report head decide the hosted outcome (pending at report
  authoring); baseline NOT_RUN; protected authority/hardware/right/
  license/MVP and release gates open; whole 009 PARTIAL; no merge;
  DHA NONE.

  Slice 009-r is the direct unit launch and bounded cgroup evidence
  (same 009 continuation, AMEND PR 11 at round base 416009c9, the
  009-q report head whose run 44672714984 completed TERMINAL_
  FAILURE: both Product legs with the confirmed
  OPENBLAS_NUM_THREADS=1 step env collected 2731, both passed the
  named isolated 16-slot publisher case, Python 3.12 forwarded 2532
  pass marks and Python 3.14 forwarded 2505, both direct supervised
  uv processes exited positive 137 with no signal field, no
  supervisor termination reason and no display refusal, different
  last unfinished source-stage nodes with no final summary, both
  around 63 s including existing cleanup, six downstream required
  steps skipped per leg, three OAP jobs succeeded; no causal claim
  about a source test, OOM, scheduler or host process). Scoped
  changes: main of oap/bin/ci_unit_diagnostics.py now supervises
  the repo's own installed pytest console (<root>/.venv/bin/pytest,
  absolute fixed path, unchanged trailing suite args, exact repo
  cwd) directly - the uv wrapper is no longer invoked - with a
  fail-closed prelaunch projection (fixed installed console, same-
  local-venv shebang, real local venv and bin) and the reviewed
  local launch projection as child env (inherited env plus repo
  .venv VIRTUAL_ENV and its bin as the first PATH entry; no new uv
  operation, shell, argv override or fallback); run_child keeps
  every resource execution/ownership behavior and the exact old
  child signal/exit and nonzero/failure behavior. NEW stdlib-only
  oap/bin/ci_unit_resources.py adds the bounded optional own-cgroup
  observation: one snapshot immediately before launch and one after
  the owned teardown (exactly one unified /proc/self/cgroup row,
  validated canonical components, EOF-driven bounded read of the
  fixed local event files under trusted /sys/fs/cgroup - procfs
  pseudofiles report zero stat size but return data - no path
  scan, symlink traversal or path output), reporting only
  nonnegative deltas of memory.events.local max/oom/oom_kill and
  pids.events.local max for the same cgroup device/inode with
  monotone counters, plus the inherited prelaunch RLIMIT_CPU
  soft/hard as bounded decimal/unlimited/unavailable; missing,
  malformed, oversize, unstable or counter-reset observations
  report unavailable, kernel-documented untracked event keys
  (low/high/oom_group_kill/sock_throttled) are parsed and ignored,
  and the fixed-length fragment is wired only into the
  supervisor's existing bounded final summary (observer
  availability or a delta never determines child status,
  acceptance, or which member failed). New bounded synthetic OAP
  checks: positive exit 137 and real direct SIGKILL produce
  distinct owned wait results (exact normal exit 137 vs separate
  child-signal field, no 128 addition) with no signal to any
  process outside the owned group, plus the direct projected
  argv/env and clean prelaunch refusal for a missing or
  non-local console; the new pure bounded parser and
  stable/missing/malformed/reset resource tests use owned
  synthetic fixtures only (no real cgroup mutation or privilege).
  The workflow, all product and pytest files, the current package
  environment and prior logs/reports are unchanged (protected
  workflow SHA256 b9195355 verified; unit and integration remain
  separate CI steps). One bounded local stdlib run of the two
  changed test modules (explicit selection, CPU 60 s / AS 1 GiB /
  wall 120 s then KILL 5 s): first run 30 tests with 1 failure and
  2 errors (exit 1) - an actual read/parser boundary: the stat-
  sized read could not observe the zero-size /proc/self/cgroup
  pseudofile, and the strict key set rejected complete normal
  kernel event files carrying documented untracked keys - fixed in
  the same authorized correction (EOF-driven strict cap-plus-one
  read; bounded ASCII key/value grammar that ignores untracked
  valid keys and refuses malformed values without raising), and
  the one changed-byte re-run under the same cap passed 31 tests
  (exit 0); ruff shows no new findings (one pre-existing F401 in
  the base test module, outside the product lint scope); no local
  full product run or CI rerun. The full hosted comparison under
  unchanged test and timeout/cleanup policy is the exact report
  head's fresh CI (pending at report authoring), which Root
  reviews for exact fresh CI and any actual resource signals; no
  unsupported cause claim even on matching counters. Baseline
  NOT_RUN; whole 009 PARTIAL; actual credential/current policy and
  MVP gates open; no merge; DHA NONE.

  Slice 009-s is the bounded unit process partition (same 009
  continuation, AMEND PR 11 at round base dfe301c7, the 009-r
  report head whose run 44688983707 completed TERMINAL_FAILURE per
  the Root terminal review: the Python 3.12 direct supervised pytest
  was SIGKILLed before the normal group teardown, supervisor exit
  131, 2731 collected and 2391 forwarded pass marks, no final
  pytest summary, wall 63.56 s including cleanup, six downstream
  required steps skipped; Python 3.14 completed all 2731 units, the
  separate integration step and all 24 job steps (supervisor wall
  78.58 s including cleanup); both legs showed unlimited inherited
  RLIMIT_CPU and zero selected own-cgroup deltas; the three OAP
  jobs were green; signal origin unproven, including on any green
  result). Scoped changes: main of
  oap/bin/ci_unit_diagnostics.py now supervises TWO bounded
  sequential direct pytest-console processes (group A then group B;
  same fixed installed console, exact repo cwd, unchanged inherited
  environment projection and same trailing suite args after the
  path selectors - only the ordered path selectors differ) under
  ONE aggregate monotonic 180 s observation/dispatch budget: A
  receives the full remaining budget and display/raw-log byte
  ceilings, B receives the exact remaining aggregate budget
  (monotonic, including A's run and owned cleanup) and the remaining
  aggregate ceilings via the existing run_child arguments; the
  remaining time is recomputed immediately before each dispatch
  (after the optional per-child pre-snapshot) and the dispatch is
  vetoed on exhaustion - no child ever receives a stale deadline;
  no dispatch after the first nonzero/unproven child, after an
  exhausted budget, or after a final display refusal; an
  unavailable second dispatch is an explicit nonzero 130, never a
  synthetic second result; the exact first nonzero and the original
  child wait distinctions are preserved; bounded 10 s/5 s owned
  group cleanup per launched child; per-child status-neutral
  own-cgroup/RLIMIT observation; each bounded per-process summary
  carries a bounded group label (unit_group=A/B) and the actual
  child deadline; run_child, the owned process cleanup and the
  observer primitives are unchanged, as is the direct-console
  admission. NEW stdlib-only oap/bin/ci_unit_partition.py: bounded
  one-level inventory under a finite pre-materialization entry
  ceiling (1024), exact regular path admission of the two default
  patterns (test_*.py, *_test.py); the generated __pycache__ is not
  a test entry; ordinary non-test files and hidden entries are not
  test entries; unsupported nonhidden nested layouts, symlinked
  scope entries, non-regular entries, an absent cut file or an empty
  group are refused, never silently omitted; group B begins at
  test_owned_gpu_worker.py. Actual group sizes at the exact base:
  62 files / 1421 nodes (A, ending test_native_tokenizers.py) and
  56 files / 1310 nodes (B). Bounded three-way collect-only
  equivalence under the original caps (CPU 60 s / AS 1 GiB / wall
  120 s KILL 5 s per observation; the one-thread Product setting
  OPENBLAS_NUM_THREADS=1 plus PYTHONDONTWRITEBYTECODE=1, fresh
  private /tmp basetemp, no cacheprovider, local locked venv): all
  three observations exit 0, the concatenated ordered A+B nodes are
  byte-equal to the full ordered 2731-node list and byte-equal to
  Root's full ordered collection from the exact dfe301c (canonical
  SHA256 60da7304…; groups 9bec4a3d… / 5001c6f3… matching Root's
  expected projections), with no duplicate, omission, extra or
  failed collection. One bounded local stdlib run of the two
  changed test modules (explicit selection; CPU 60 s / AS 1 GiB /
  wall 120 s then KILL 5 s): first run 39 tests with 2 failures
  (exit 1; assertion outcomes in the new 009-s cases - the default
  10 s teardown grace instead of the module's short synthetic
  bounds, and a same-deadline body-identity algebra error) fixed in
  the same authorized changed-byte correction; the one re-run under
  the same exact cap passed 41 tests (exit 0, wall 32.90 s).
  Collected setup/deviation disclosure: the first full-directory
  collect-only observation under the caps WITHOUT the one-thread
  setting failed silently (exit 1, no output - setup failure); two
  out-of-scope diagnostic probes (AS 1.5 GiB segfault exit 139; AS
  2/3 GiB and one uncapped /usr/bin/time -v run) were stopped on
  Root's order, preserved and never used as proof; the ordered
  batch then ran under Root's exact one-thread setting. ruff shows
  no new findings (product lint scope untouched; OAP is governance-
  owned compact style outside product lint); compileall clean;
  git diff --check exit 0. The workflow, all product and pytest
  files, the current package environment and prior logs/reports are
  unchanged (protected workflow SHA256 b9195355 verified; unit and
  integration remain separate CI steps). The fresh full hosted
  comparison (both Product legs plus all OAP jobs) at the exact
  report head is pending at report authoring; Root owns the fresh
  CI and honest terminal assessment; a required failure remains a
  failure even if one partition or job passed; no attribution of
  the 3.12 signal sender even on a green result. Baseline NOT_RUN;
  whole 009 PARTIAL; protected authority/hardware/right/license/MVP
  and release gates open; no merge; DHA NONE.
  Slice 009-t is the pure policy component transfer (same 009
  continuation, AMEND PR 11 at round base d731dea7, the 009-s
  report-only head whose run 44711903559 attempt 1 passed all five
  jobs and all steps: both Product legs passed the ordered 2,731
  units - 1,421 in group A and 1,310 in group B - plus the
  independent full integration; the earlier SIGKILL cause remains
  unproven). Four reviewed parallel-lane component scopes are
  transferred byte-exact from their indexed implementation commits
  (16 payload paths: four product modules, four unit modules, four
  component docs, four original lane orders), keeping their reviewed
  unit contracts and immutable provenance: (1) supplied-policy -
  the typed supplied-policy declaration, domain-separated framed
  identity and supplied-credential matching via hmac.compare_digest
  (labelled SUPPLIED_POLICY_MATCH_ONLY: supplied declaration plus
  admitted-credential evidence only, never current application
  authorization or current-policy verification), 124 units; (2)
  supplied-policy-wire - the canonical wire reader, 95 units; (3)
  policy-selection-record - the selected-view record, 47 units; (4)
  supplied-membership-eligibility - the pinned-membership
  eligibility primitive, 18 units. The four original lane
  report-only SELF commits' archival reports are copied byte-exact
  (historical SELF markers preserved) to oap/provenance/009-t/;
  no lane commit, PR or report is amended, imported or
  cherry-picked. The three inherited dependency blobs
  (provenance_records, raw_snapshot_membership, qualification/
  parity_io) were verified byte-identical at the round base and are
  reused unchanged. The transferred primitives admit explicit
  caller-supplied policy data for later operator composition; the
  slice contains no protected policy service, no live credentials,
  no model dispatch and no representative held-out qualification.
  Actual local proof at the exact implementation head under the
  ordered caps (CPU 60 s / AS 1 GiB / wall 120 s KILL 5 s,
  PYTHONDONTWRITEBYTECODE=1, OPENBLAS_NUM_THREADS=1, one-thread
  affinity for the ruff worker pool, fresh private basetemp, no
  cacheprovider): one targeted ruff check over the eight copied
  Python files clean (exit 0); one bounded pytest invocation of
  all four new default unit modules 284 passed (124 typed, 95
  wire, 47 selection, 18 eligibility; exit 0); one bounded origin
  check confirmed every imported product module resolves to the
  canonical repository src/ with the exact indexed blob hashes.
  Expected (not yet measured) at the new report head: group A
  1,421, group B 1,594, total 3,015, plus the separate integration
  and all unchanged required jobs/steps. The fresh full hosted
  comparison at the exact new report head is pending at report
  authoring; Root owns the fresh CI and terminal review. Baseline
  NOT_RUN; whole 009 PARTIAL; protected authority/hardware/right/
  license/MVP and release gates open; no merge; DHA NONE.
  Slice 009-u is the one changed CI job-limit comparison (same 009
  continuation, AMEND PR 11 at round base e97d29fb, the 009-t
  report-only head). The exact prior round run 44717676140 attempt 1
  ended CANCELLED: both Product unit steps passed all 3,015 units
  (1,421 in group A, 1,594 in group B), including the four added
  policy modules with the expected 47/124/18/95 file counts; Python
  3.14 completed the separate integration and all 24 steps; all
  three OAP jobs passed; Python 3.12 started at 10:15:30 UTC,
  completed the unit step at 10:17:35, and its integration log
  reached 90% at 10:32:54 before cancellation at 10:35:42 -
  check-run 136225094911 explicitly reports the maximum execution
  time of 20m0s, the integration step was cancelled and five later
  steps were skipped; the exact integration wall-time variance and
  the active test at cancellation remain unproven. The only
  workflow byte change is the product-tests job-level
  timeout-minutes integer 20 to 30 (verified preimage b9195355,
  14,235 B, to target 54e66869, 14,235 B, single line-70 change;
  the three OAP jobs keep 10 minutes and all action, setup and step
  bytes remain exact). The bounded headroom targets the proven CI
  platform cancellation after successful units; its effect must be
  observed before the policy capture transfer can advance. The
  fresh full hosted comparison at the exact report head is PENDING
  at report authoring (exact pending status before remote CI);
  Root owns the fresh CI terminal review of the new exact
  report-head run and the remaining uncertainty. A second timeout
  or partial run cannot close the gate. Baseline NOT_RUN; whole 009
  PARTIAL; protected authority/hardware/right/license/MVP and
  release gates open; no merge; DHA NONE.
  Slice 009-v is the byte-exact four-payload transfer of the
  reviewed private policy selection reread and selected wire-byte
  capture scope (same 009 continuation, AMEND PR 11 at round base
  851a1e29, the 009-u report-only head whose run 44724323631
  attempt 1 passed all five jobs and all steps: both Product legs
  passed 3,015 units (1,421 group A, 1,594 group B) plus a
  separate 951-case integration run, both within the former
  20-minute limit; the 30-minute bound remains current and prior
  wall-time variance remains unproven). Per
  oap/reviews/009-v-capture-transfer-index.json, from the exact
  lane implementation 6e8922c6 on base b0bd2821: the
  private_policy_capture source module (14,974 B), the new focus
  suite (37,256 B) and the original lane order (5,807 B), plus the
  original lane report-only SELF archival report (10,890 B) from
  its report-only commit ff876ee7 - all four verified mode 100644
  / size / SHA-256 / Git blob OID at the exact source commits, at
  the receiving working-tree paths before commit and again at the
  implementation head, with the historical SELF markers preserved
  at oap/provenance/009-v/PAR-009-PRIVATE-POLICY-CAPTURE-A.json.
  The two inherited dependency blobs (policy_selection,
  private_report_publication) are byte-identical at the round base
  and reused unchanged. The selected identity is
  current-policy.json with its digest-named opaque wire-byte
  payload, read through a protected request from one explicit
  trusted operator-owned root; the bounded owner is one private
  offline evaluation invocation (ARCH 13.3-13.4/A23/A24) with
  reader-owned fixed six-cell descriptor slots, deadline and
  refusal proofs, no writer, no actual current-auth invocation and
  no protected-runtime use. Actual local proof at the
  implementation head under the ordered CPU60s/AS1GiB/wall120s
  KILL5 bounds: one targeted ruff check on the two new Python
  files (exit 0), one bounded pytest invocation of the new focus
  suite plus the inherited selection suite (118 = 71 new + 47
  inherited, exit 0, exactly 118 progress dots; the configured
  double -q suppresses the final summary line, preserved as raw
  output) and one bounded canonical-origin check (all three
  imported modules resolve to the canonical src with exact indexed
  hashes). The fresh full hosted CI at the exact report head is
  PENDING with Root owning it and the terminal review; expected
  until measured A 1,421, B 1,665, total 3,086. Baseline NOT_RUN;
  whole 009 PARTIAL; protected authority/hardware/right/license/
  MVP and release gates open; no merge; DHA NONE.
  Slice 009-w is the byte-exact three-component transfer of the
  reviewed declaration-side preflight scopes (same 009 continuation,
  AMEND PR 11 at round base 0f24c91c, the 009-v report-only head
  whose adopted hosted run 44731327493 attempt 1 passed all five
  jobs and all steps: both Product legs 3,086 units (1,421 group A,
  1,665 group B) plus a separate 951-case integration run). Per
  oap/reviews/009-w-declaration-transfer-index.json, three changed
  product preimages, three new unit suites, three original lane
  orders and three original lane report-only SELF archival reports
  (12 indexed paths, all verified mode 100644 / size / SHA-256 /
  Git blob OID at the exact source commits, at the receiving
  working-tree paths before commit and again at the implementation
  head): the shared binder declaration-only admission
  (source_bound_stage_loss.py 91,797 B, 8 new unit cases, from
  cacc5b36 on base 416009c9), the private query-free cohort
  declaration envelope with shared ordered source selection
  (source_cohort_runner.py 49,662 B, 21 new unit cases, from
  ab832488 on the exact accepted binder implementation cacc5b36)
  and the private grade declaration envelope (evaluation_program.py
  34,416 B, 19 new unit cases, from d052c3c9 on base dfe301c7).
  The existing query-dependent admission and grade behaviors,
  order, metering and report identity remain governed by their
  inherited tests (the legacy binder payload gate keeps its
  original position before any reserve, the legacy cohort entry
  keeps its query comparison and full vector binder check before
  the dataset, and the legacy grade budget bound keeps its
  original first point); the query-independent pieces add
  declaration-only synthetic admission with no actual encoder,
  pin/catalog, publisher, delivery, current-policy authentication,
  fixture replacement or CI change. The three original lane orders
  (5,013/5,144/4,586 B) and the three original SELF archival
  reports are preserved with their historical SELF markers
  unchanged, archived at oap/provenance/009-w/. Actual local proof
  at the implementation head under the ordered CPU60s/AS1GiB/
  wall120s KILL5 bounds: one targeted ruff check on the six
  changed Python files (exit 0), one combined focused pytest of
  the three new unit suites plus the eight exact inherited
  selectors (58 = 48 new + 10 inherited parameterized nodes, exit
  0) and one bounded canonical-origin check (all imported product
  modules resolve to the canonical src with exact indexed hashes).
  The fresh full hosted CI at the exact report head is PENDING
  with Root owning it and the terminal review; expected until
  measured A 1,440, B 1,694, total 3,134 plus the unchanged
  complete integration and every downstream step. The open
  governed operator, the real representative baseline, source
  rights and model gates remain open. Baseline NOT_RUN; whole 009
  PARTIAL; protected authority/hardware/right/license/MVP and
  release gates open; no merge; DHA NONE.
  Slice 009-x is the one private policy payload install entry (same
  009 continuation, AMEND PR 11 at round base ed48ca58, the 009-w
  report-only head whose adopted hosted run 44737907992 attempt 1
  passed all five jobs and all steps: both Product legs 3,134 units
  (1,440 group A, 1,694 group B) plus a separate 951-case
  integration run).  The entry takes the exact wire bytes, the
  trusted private directory and one bounded monotonic deadline; it
  rejects invalid inputs before any protected namespace work, admits
  the entire candidate through the production admit_policy_bytes
  with the established wire envelope, and installs the admitted
  bytes at their SHA-256 digest name (<64 lowercase hex>.bin) in
  bounded chunks.  The visible publisher now exposes the complete
  admitted-content transaction (fixed slot pool, directory-inode
  lock, no-follow walk, unnamed O_TMPFILE stage, immutable mode,
  one no-overwrite link, byte+inode verification, both fsync
  boundaries, conservative state and the existing retry_cleanup)
  exactly once, and both trusted entries go through it; the legacy
  report publication code, ordering and outputs and the original
  capture helpers are exact.  Every ordinary initial, deadline or
  slot failure normalizes to the entry's fixed content-free refusal
  with the truthful installation and cleanup state, BaseException
  identity is preserved, the shared publisher error is wrapped to
  the entry's fixed error, and the shared transaction outcomes map
  explicitly to the entry's own new-installation and existing
  distinction.  The receipt reports installation state, cleanup
  state, exact byte length and wire digest; it confers no selection
  authority, and the existing selector's bytes and linked inode
  remain unchanged.  One new 62-case synthetic unit suite covers
  the zero-namespace refusals, the early post-decode and post-hash
  deadline cuts, the pool and refusal wrapping, the new and raced
  existing outcome types, the truthful late durable return and the
  counted real I/O operation order.  Actual local proof at the
  implementation head under the ordered CPU60s/AS1GiB/wall120s
  KILL5 bounds: one targeted ruff check on the three changed Python
  files (exit 0), one combined focused pytest of the new suite plus
  the two exact inherited publisher and capture suites (222 = 62
  new + 160 inherited nodes, exit 0) and one bounded
  canonical-origin check (every imported product module resolves to
  the canonical src, every unchanged input at its prior-resolution
  hash).  The fresh full hosted CI at the exact report head is
  PENDING with Root owning it and the terminal review; expected
  until measured A 1,440, B 1,694 plus the 62 new unit nodes,
  integration 951 and every downstream step.  The open governed
  operator, the real representative baseline, source rights and
  model gates remain open.  Baseline NOT_RUN; whole 009 PARTIAL;
  protected authority/hardware/right/license/MVP and release gates
  open; no merge; DHA NONE.
  Slice 009-y is the test-only procfs exit-observation correction
  (same 009 continuation, AMEND PR 11 at round base 53937d7e, the
  009-x report-only head).  The required hosted check of the adopted
  prior resolution failed at exactly the 009-x run 44760385202
  attempt 1: the Product Python 3.14 job (136371029375) unit step
  failed at the inherited
  tests/unit/test_real_cpu_toy_probe.py::test_timeout_kills_owned_descendant
  and its six downstream steps were skipped; the Python 3.12 full leg
  (3,196 ordered units), all 62 new payload cases on both Products and
  all three OAP jobs passed.  The inherited timeout test observes the
  owned descendant's exit only through a missing procfs stat path or a
  zombie state.  Linux can instead return ESRCH while reading an
  already-opened stat record after the task disappears (Root
  independently reproduced the kernel sequence: ESRCH on the held
  record read, ENOENT on the absent record open); the observed CI
  failure was that second form at the stat poll after the expected
  parent timeout, escaping as ProcessLookupError.  The correction is
  scoped to that one test: the stat poll now accepts FileNotFoundError
  at open and ProcessLookupError at read as the two observations of
  record disappearance, and the existing pidfd-bound cleanup accepts a
  missing stat record after successful pidfd acquisition; the parent
  timeout, observation deadline, zombie check, UNREAPED assertion,
  same-handle signal path, PID/start-time check, still-live failure
  path and descriptor close are preserved, and every other I/O and
  malformed-evidence failure behavior is unchanged.  No product
  source, workflow, test inventory, budget or other test changed.
  Actual local proof at the implementation bytes under the ordered
  CPU60s/AS1GiB/wall120s KILL5 bounds with OPENBLAS_NUM_THREADS=1,
  PYTHONDONTWRITEBYTECODE=1, fresh private 0700 scratch and no
  cacheprovider: the whole inherited module once (28/28 cases, exit
  0), the existing strategic witness diagnostic once with the changed
  test (actual Linux forms ESRCH-held/ENOENT-absent; controlled ENOENT
  and ESRCH at the owned stat poll accepted, controlled EACCES still
  escaping), and one targeted ruff check on the changed module (exit
  0).  The fresh full hosted CI at the exact report head (both
  Product legs, each expected A 1,440 and B 1,756 units, the separate
  951-case integration and the same three OAP jobs) is PENDING at
  report authoring, with Root owning the fresh CI and terminal review;
  it is distinct from the local proof above.  Baseline NOT_RUN; whole
  009 PARTIAL; protected authority/hardware/right/license/MVP and
  release gates open; no merge; DHA NONE.
  Slice 009-z is the byte-exact canonical transfer of the two
  independently reviewed isolated development lanes (same 009
  continuation, AMEND PR 11 at round base 0b337ec, the accepted
  009-y report-only head; required run 44768398812 attempt 1 passed
  all five jobs and every step).  The frozen Root transfer index
  (17,348 B, SHA-256
  d6a249fbd1162cbdc831b3961ebc49602fc93fa9db24a0afe513ede56f39124f)
  and prior resolution (1,968 B, SHA-256
  9fabdabc8cdfff363ae796f059ab57d60550b536ff8a6fd5782b2ad420b46eb5)
  are preserved byte-exact under oap/reviews/.  Lane 1,
  current-view-request (PAR-009-CURRENT-VIEW-REQUEST-A; implementation
  4b798897 on effective base c9332238, preparation tree 01c91d3d with
  exact parents 6e8922c6 + 89946522): the new private current-view
  request entry private_policy_request.py (14,885 B) composes the
  accepted reader capture, the pure wire admission and the genuine
  supplied-credential match under one trusted operator-owned reader,
  one absolute creator-process deadline and one nonblocking recheck
  span, plus the 45-case test_private_policy_request.py (42,773 B)
  and the original verbatim lane order (5,675 B); the original
  immutable lane SELF report (publication 037e238a, 27,304 B) is
  preserved at
  oap/provenance/009-z/PAR-009-CURRENT-VIEW-REQUEST-A.json.  Lane 2,
  encoder-runtime-identity (PAR-009-ENCODER-RUNTIME-IDENTITY-A;
  implementation 7ac6994c on effective base 416009c9): the extended
  query_embedding.py (10,872 B, replacing the 7,907 B preimage) adds
  one explicit guarded entry that, under the existing encoder lock,
  compares the live admitted session and worker record with the exact
  expected four-field encoder identity tuple before invoking the
  existing session encode, keeping every original unguarded
  signature, check, identity, failure and cleanup behavior, plus the
  extended 51-case test_query_embedding.py (24,884 B, replacing the
  8,731 B preimage with the original 17 nodes an exact ordered
  prefix and 34 added) and the original verbatim lane order (5,006
  B); the original immutable lane SELF report (publication 84b0a6f3,
  13,264 B) is preserved at
  oap/provenance/009-z/PAR-009-ENCODER-RUNTIME-IDENTITY-A.json.
  All eight transfer objects were verified at the exact source
  commits and at the receiving tree for mode 100644, size, SHA-256
  and blob OID; all indexed receiving preimages were verified
  byte-exact at the round base, including the unchanged reader, both
  workers, the wire/selection/provenance sources and the 009-x
  measured bridge bytes, with the current publisher's full SHA-256
  and its exact 22,985-byte original capture prefix unchanged through
  009-x and 009-y.  Actual local proof at the implementation bytes
  under the ordered CPU60s/AS1GiB/wall120s KILL5 bounds with
  OPENBLAS_NUM_THREADS=1, PYTHONDONTWRITEBYTECODE=1, fresh private
  0700 scratch and no cacheprovider: one bounded combined focus of
  the five ordered modules (45 + 51 + 71 + 95 + 62 = 324 cases, exit
  0 in 7.77 s, including the exact passing installed-payload
  interoperability suite against the current reader), one four-file
  Ruff check (exit 0) and one bounded import-origin check (both
  transferred product modules resolve to the canonical repository
  src with the exact indexed hashes).  The transferred bytes and
  eligible declarations remain separate from real runtime or
  authority qualification: the request entry exercises real request
  and authentication checks under synthetic installed policy only,
  and the guarded encoder exercises the actual resident wrapper and
  session boundary with synthetic controlled delegates only.
  Expected at the report head: group A 1,440 unchanged, group B
  1,835 (all 79 new default nodes in B, the 17 inherited encoder
  nodes retaining their order), 3,275 total units, the separate
  951-case integration and the same three OAP jobs; the fresh full
  hosted CI at the exact report head is PENDING at report authoring,
  with Root owning the fresh CI and terminal review; it is distinct
  from the local proof above.  Baseline NOT_RUN; whole 009 PARTIAL;
  protected authority/hardware/right/license/MVP and release gates
  open; no merge; DHA NONE.
  Slice 009-aa is the byte-exact canonical transfer of the two
  independently reviewed isolated development lanes (same 009
  continuation, AMEND PR 11 at round base ca8e9c8a, the accepted
  009-z report-only head whose required hosted run 44775148168
  attempt 1 passed all five jobs and every step, both Products at
  3,275 ordered units and the separate 951-case integration).  The
  frozen Root transfer index (16,828 B, SHA-256
  9bd1da70a5cf37a91b90d6c11f4f16dc8c791eb91ab46736c686b2a58ddd35e4)
  and prior resolution (1,724 B, SHA-256
  dbc5d5006a6073aa0473218ccdcf56f33a4a2def442b4e5ffbed20fa1d8c3d8b)
  are preserved byte-exact under oap/reviews/.  Lane 1,
  joint-evaluation-declaration
  (PAR-009-JOINT-EVALUATION-DECLARATION-A; implementation 0a816ab0 on
  effective base ed48ca58): the new private joint declaration
  preparation entry private_evaluation_preflight.py (7,140 B) binds
  the exact evaluation plan wire admission, the genuine source cohort
  declaration admission and the actual grade declaration preparation
  over the exact same admitted dataset and ordered selected values
  under one existing bounded deadline created at entry, plus the
  42-case test_private_evaluation_preflight.py (37,427 B) and the
  original verbatim lane order (5,825 B); the original immutable lane
  SELF report (publication cfb7ef41, 18,640 B) is preserved at
  oap/provenance/009-aa/PAR-009-JOINT-EVALUATION-DECLARATION-A.json.
  Lane 2, current-policy-pin-eligibility
  (PAR-009-CURRENT-POLICY-PIN-ELIGIBILITY-A; implementation 57d463a5
  on the ordered preparation head 9e6283fe with tree 0279879f and
  exact parents 4b798897 + 7f6190ad): the new private current-policy
  partition eligibility entry
  private_policy_pin_eligibility.py (19,591 B) composes the exact
  admitted current selected-policy request with the already admitted
  in-memory capture of one exact borrowed operator-owned PinOwner
  under one absolute cooperative deadline, with the genuine recheck
  before and after scope computation and the real
  unavailable-partitions rules over the retained current policy, and
  the retained selected policy re-admitted in memory as one bounded
  coherent isolated snapshot through the genuine closed
  supplied-policy admission before any of its rules are used, plus
  the 53-case test_private_policy_pin_eligibility.py (70,832 B) and
  the original verbatim lane order (6,376 B); the original immutable
  lane SELF report (publication dc28c0d2, 35,496 B) is preserved at
  oap/provenance/009-aa/PAR-009-CURRENT-POLICY-PIN-ELIGIBILITY-A.json.
  All eight transfer objects were verified at the exact source
  commits and at the receiving tree for mode 100644, size, SHA-256
  and blob OID; all 27 indexed receiving preimages were verified
  byte-exact at the round base, including the actually inherited
  current-view files (private_policy_request.py and
  test_private_policy_request.py), the pin ownership sources
  (raw_snapshot_pin.py and the raw_snapshot_* readers), and the
  genuine policy admission code (supplied_policy.py,
  policy_selection.py, private_policy_capture.py,
  supplied_policy_wire.py).  Actual local proof at the implementation
  bytes under the ordered CPU60s/AS1GiB/wall120s KILL5 bounds with
  OPENBLAS_NUM_THREADS=1, PYTHONDONTWRITEBYTECODE=1, fresh private
  0700 scratch and no cacheprovider: one bounded focus of the nine
  ordered entries (42 + 21 + 19 + 1 + 1 + 53 + 18 + 45 + 8 = 208
  cases, exit 0 in 2.65 s, all 95 new cases in the two transferred
  suites), one four-file Ruff check on one process-local core
  (exit 0) and one bounded import-origin check (both transferred
  product modules resolve to the canonical repository src with the
  exact indexed SHA-256s).  The transferred bytes and eligible
  declarations remain separate from real runtime or authority
  qualification: the joint entry exercises the genuine wire, cohort
  and grade admission paths and bounded deadline behavior over
  synthetic declared datasets only, and the pin entry exercises the
  real request rechecks and unavailable-partitions rules over an
  in-memory borrowed capture with synthetic controlled delegates
  only; the accepted artifacts do not connect evaluation execution
  to either entry, and the existing public entry points are
  preserved.  Expected at the report head: group A 1,440 unchanged,
  group B 1,930 (all 95 new default nodes in B), 3,370 total units
  each Product, the separate 951-case integration and all five
  required jobs (the two Product legs and the three OAP legs) with
  every existing step; the fresh full hosted CI at the exact report
  head is PENDING at report authoring, with Root owning the fresh CI
  and terminal review; it is distinct from the local proof above.
  Baseline NOT_RUN; whole 009 PARTIAL; the remaining real operator,
  current writer, request execution, rights, baseline and hardware
  gates stay open; no merge; DHA NONE.
- Historical 007 record (active objective at the time: 007,
  then-current slice 007-r; the 007-a reviewed
  normalized FP32 NPY subset codec plus reproducible NumPy 2.5.4 pin,
  extended by the 007-b source-bound raw retrieval representation/batch
  and published BGE-M3 checkpoint inventory/encoder-space software,
  the 007-c composed CPU-session software: owned staging, exact native
  token IDs, bounded preflight before one ordered CPU CLS forward and
  fixed FP32 normalization under trusted neural fakes, the 007-d
  durable source-plan substrate: fresh source-bound intended CPU/FP32
  batch plans, typed validated batch store, per-job ownership leases
  and the atomic job journal with output-before-COMPLETE, and the
  007-e CPU reference path: pre-model schema-2 execution contract and
  job claim before model startup, observed-execution comparison before
  any content is forwarded, one-attempt producer with an explicit
  trusted authorization provider, output-before-COMPLETE and verified
  zero-model-start reuse, the resident CPU worker under the actual
  bounded OS isolation protocol, and the portable synthetic
  six-real/22-metadata CPU test fixture provisioned in CI; the 007-f
  continuation adds the two exact root-reviewed cleanup/ownership
  composition candidates and the cooperative per-device kernel lease:
  finite owned-descriptor close attempts across failures with original
  non-Exception interruptions preserved (a new cleanup interrupt
  outranks ordinary errors), no blind re-close of a reused descriptor
  number, sticky UNKNOWN cleanup owners retained through the sanitized
  journal and producer, the producer's pending native/model resource and
  journal lease held until drain, the isolated context-exit under the
  same interrupt priority, and the device lease key binding only the
  versioned host + physical UUID under the trusted common local root
  (cooperative: no physical exclusivity, no granted runtime authority);
  the 007-g selective integration adds the CPUv2 lock selection (Torch
  2.14.0+cpu / Transformers 5.22.2 / framework tokenizers 0.23.1; 38
  locked metadata distributions) with the legacy profile/helper/fixture
  and native 0.21.4 capsule intact, the required portable synthetic CPUv2
  CI fixture (six exact wheels plus 32 DATA-ONLY metadata distributions)
  before lint on both matrix legs, and the corrected raw GPU backend
  source finite and inert (device UUID byte guard, process-owned
  DeviceLease assertion, no autocast, ordered finite CPU FP32 raw CLS
  output, sticky close and original non-Exception identity); the actual
  BGE/checkpoint/hardware remain UNRUN/UNQUALIFIED; the 007-g-era
  full-38 PARTIAL claim is superseded as current status by separately
  scoped Root actual development evidence (frozen full-CLI acquisition
  of all 38 wheels complete: 22.254 s, 252554535 payload bytes, 38
  hash-verified wheels, 38 metadata and dependency graph, all four
  commands exit 0, no unresolved owned children, sampled disk
  2085087847 B under 2 GiB address space / 120 s CPU / 600 s wall,
  sampling not quota; separate actual CPU class import of Torch
  2.14.0+cpu plus Transformers 5.22.2 XLMRobertaModel succeeded:
  14.73 s, 352816 KiB RSS, standalone CPython 3.12 namespace,
  synthetic /dev, no home, offline, separate 4 GiB / 30 s CPU /
  120 s wall — a class import is not BGE weight loading, model
  construction, forward execution, latency, parity, hardware, security
  or license qualification; prior partial receipts remain HISTORY);
  the 007-h selective integration adds the SIX root-reviewed
  setup/test/API files (original byte-identical transfer 70,906
  bytes per historical oap/reviews/007-h-components.json; Root
  CI-portability amendment 007-h-1 changed ONLY the installer unit
  file — 23,095 → 28,320 bytes, current SHA-256
  6038a3b1766f52911f9d15b800d6fe515630b32f03cec52bca39b30ed56d1482 —
  and the other five files, including the production helper
  226a527650083ec3324fcb783354ca47eb8b30884f0db0d3e4df6c044e6ede0c,
  remain byte-exact, current six-file sum 76,131 bytes per
  oap/reviews/007-h-components-after-portability.json; fixed CPUv2
  runtime installer developer
  qualification tooling: 38-wheel pinned official graph, offline
  no-index/no-deps hash-required install, MALLOC_ARENA_MAX=1, atomic
  receipts — never run in CI, not a deployment or runtime grant;
  portable synthetic GPU worker fixture helper: six exact wheels plus
  51 DATA-ONLY metadata distributions from the fixed GPU lock; unit
  suites and API docs) and the required GPU fixture CI step after the
  CPUv2 fixture and before lint on both matrix legs with literal
  GITHUB_ENV bindings; the 007-i selective integration adds the FIFTEEN
  root-reviewed resident-query/CPU-asset files (oap/reviews/
  007-i-components.json, 170,026 bytes, no branch ancestry, no
  source adaptation): the private resident CPU query encoder
  (bounded raw Unicode/UTF-8 admission with no prefix/
  truncation, independent native 0.21.4 tokenizer IDs, one
  actually owned CPU worker reused across queries with
  load-once, immutable normalized FP32 result with observed
  complete execution provenance, content-free refusal before
  exposure), the shared native/CPU/session diagnostic-priority
  fixes (selected original non-Exception interruption preserved
  when cleanup or diagnostic annotation fails; a new cleanup
  interruption outranks ordinary errors; notes/owner attributes
  are best effort, never resource ownership) and the packaged
  CPU profile lock assets (the actual offline wheel bundles
  byte-identical CPU v2/legacy CPU/GPU locks under
  _worker_profiles; installed-layout selection refuses
  missing/corrupt/symlinked or whole-bundle-missing assets even
  with a matching ambient project/lock under bounded dist-info
  downgrade guards; source-checkout support retained; pyproject
  adds only the three reviewed force-include lock mappings,
  dependencies and all CPU/GPU/native locks unchanged); finite
  model-free software under trusted neural fakes and the actual
  offline wheel, actual BGE UNRUN/UNQUALIFIED, GPU child/plan/
  parent resources still parallel/unintegrated; the 007-j selective
  integration adds the FOURTEEN root-reviewed GPU child/protocol,
  prepared-launch and packaged-resource files (oap/reviews/
  007-j-components.json, 136,921 bytes, no branch ancestry, no
  source adaptation, single exact source commit 5445c03): the GPU
  worker protocol (child-owned device lease before backend load,
  fixed closed bounded wire/version/config/startup vocabulary,
  exact token-ID requests and raw FP32 rows, content-free refusals,
  immutable ready bindings, no fake serialized PID-bound lease,
  original non-Exception interruption priority retained), the
  corrected raw GPU backend finite and inert under trusted fakes,
  the prepared launch (actual pinned Python/package/config/device
  inputs with retained FDs, exact closed copied capsule, fixed
  argv/clearenv/private namespaces, trusted fixed entry,
  fork-creating-PID check before any close/cleanup, bounded
  startup) and the packaged GPU profile lock assets (bundled
  unchanged GPU lock first; fail-closed missing/corrupt/symlinked/
  whole-bundle-missing refusal under actual installed normal/src-
  named prefixes even with a matching ambient project/lock;
  bounded dist-info guards; the /app/src/pkg layout is a data
  mapping, not authorization); finite model-free software under
  fake/null namespaces and the actual offline wheel, no real GPU/
  driver/Tensor/model/framework executed, actual BGE
  UNRUN/UNQUALIFIED, the actual owned GPU parent + new lock +
  worker identity still parallel/unintegrated pending affected
  reviews; the 007-k selective integration adds the EIGHT
  root-reviewed immutable raw snapshot core/row-map
  declaration codec/test/API/design files (oap/reviews/
  007-k8-snapshot-components.json, 47,707 bytes, byte-exact
  from exact source commits b7a2b52/09fe0d5): a closed
  bounded canonical ASCII schema-1 core codec with derived
  noncircular snapshot ID and an 8-header/17-row row-map
  codec with canonical partition subsets and fresh-bytes
  bind; pure declared-format data only, no
  payload/source/vector/rights/normalization/publication/
  retention proof and no activation; the 007-l selective
  integration adds the TWENTY-THREE root-reviewed immutable
  owned-GPU parent/identity and native runtime-identity
  files (oap/reviews/
  007-l-parent-native-components.json, 250,571 bytes,
  byte-exact from exact source commits 9ac0eabd/d7701a53):
  the owned GPU embedding worker parent (retained
  creating-process lock, lock-close race, raw worker
  identity, single initialization refused before any live
  owner/process/FD/lock/registry mutation, original Popen
  pre-return capture), the raw GPU worker-identity
  predictor/validator (selected-file canonical bytes with
  domain-separated fingerprint; a record is data, never
  authorization) and the native runtime-identity leaf plus
  TokenIDSession acquisition corrections (owned Popen
  retained before fallible initialization, independent
  strong pending owner, fork refusal, creator/once/closed/
  context/error precedence, bounded no-follow artifact
  identity); the held parent K13 hold is remediated at the
  frozen software + fresh peer (hold history preserved, no
  human DHA waiver); two authorized
  test-only portability exceptions (Root addenda 1/2/3)
  replace the frozen FILE unit's 32 MiB+1 fixture-file
  creation with an exact device/inode fstat size boundary
  under the inherited CI FSIZE cap, and the CPU-session
  composition's public-class Popen replacement spy with a
  real Popen.__init__ spy (the integrated exact-class
  guard refuses a replaced public class); all other 22
  files and all production guards/limits remain
  byte-exact; finite model-free
  software under the
  actual offline fixture, fake/null namespaces, synthetic
  copied entries and the actual native 0.21.4 tokenizer
  worker on synthetic strings, actual BGE UNRUN/
  UNQUALIFIED, GPU text bridge/producer/controller/durable
  GPU execution still unimplemented;   the 007-m selective integration adds the TEN
  root-reviewed immutable GPU text-bridge and
  source-bound GPU plan files (oap/reviews/
  007-m-bridge-plan-components.json, 95,773 bytes,
  byte-exact from exact source commits a9a5ef0/d100689):
  the isolated GPU embedding bridge (borrows the
  actual owned GPU parent/PreparedLaunch/reservation,
  owns only its own native TokenIDSession, native IDs
  never supplied, bounded preflight before any native
  text exposure, receipt-field validation, forward/encode
  reach the captured actual class implementations,
  creator/closed/busy/fork rules, pre-return ownership
  retention, cleanup priority, raw CLS then normalized
  FP32) and the source-bound GPU plan (freshly derives
  complete selected rows, source scope, independent
  native counts and canonical order/hash/space/
  definition/inventory/policy before job creation,
  predicts the selected GPU batch execution before
  execution, replaces only the legacy CPU intended
  execution dependency with the complete predicted GPU
  execution, refuses forged/detached/stale records and
  source changes); the two preserved 007-l test-only
  exceptions remain byte-exact (c2b483b7/15,779 B,
  275e10d3/5,179 B); finite model-free software under
  synthetic fixtures with the actual native 0.21.4
  tokenizer worker on synthetic strings and the approved
  copied GPU fake/null fixture, actual BGE UNRUN/
  UNQUALIFIED, GPU producer/controller/durable GPU
  execution still unimplemented;   the 007-n selective
  integration adds the TWENTY-ONE root-reviewed
  immutable corpus-pipeline files (oap/reviews/
  007-n-corpus-pipeline-components.json, 335,687 bytes,
  byte-exact from exact source commits b0ca5a6/880dedf/
  6f5b311/bac11be; two deliberate existing production
  replacements, nineteen new paths): the owned launch
  preparation/handoff in gpu_worker_launch.py, the
  one-batch GPU embedding producer, the whole-source
  formatting support in retrieval_representation.py
  with the source embedding program (every selected
  original-backed container freshly revalidated,
  stable ordered source-local batches, no silent
  >128-row truncation or whole-corpus row ceiling) and
  the selected-source corpus executor (one
  operation-wide epoch, stops on failure before
  uncertain later work, journal-gated reuse,
  fresh-creator resume after a clean between-batch
  stop); exact contracts under docs/parallel/
  (gpu-launch-preparation-owner, gpu-embedding-
  producer, corpus-embedding-program, corpus-
  embedding-executor API/design docs); the two
  preserved 007-l test-only exceptions remain
  byte-exact (c2b483b7/15,779 B, 275e10d3/5,179 B);
  finite model-free software under synthetic fixtures
  with the actual native 0.21.4 tokenizer worker on
  synthetic strings and the approved copied GPU
  fake/null fixture, actual BGE UNRUN/UNQUALIFIED,
  mode controller/current-principal policy/inference
  CLI/snapshot integration/physical qualification
  still unimplemented;
  the 007-r selective integration adds the EIGHT
  root-reviewed gateway role/precedence files (oap/
  reviews/007-r-component-index.json, 82,739 bytes, byte-exact
  from exact source commit 77b4e8c; ONE existing production
  replacement gateway.py with +28/-0 lines versus Q, seven new
  paths absent at base): exact assistant-role admission at the
  collector and the stream item-added/done boundaries with the
  fixed input-free error invalid message role (the hostile role
  value is never echoed), and latched structural-error
  precedence across all five stream exception exits so a latched
  role failure finishes through the existing stream finisher
  instead of being salvaged by later timeout/protocol/refused/
  generic handling, while normal assistant output, reasoning,
  valid refusal, multiple items, cleanup/drain, finite retry and
  honest UNKNOWN_COMPLETION stay intact; actual scoped local
  proof: 15 unit + 19 new integration cases (separate processes)
  plus 3 named regressions all passed once under
  CPU30/AS1GiB/wall120, with the timeout-guard causal control and
  controlled late-close faults labelled controlled; finite
  model-free software under owned synthetic loopback fixtures,
  actual BGE UNRUN/UNQUALIFIED, live gateway qualification
  unchanged;

open on the 007 PR, branch
  oap/007-embedding-pipeline from main 11badc7; whole-007 remains
  PARTIAL — the CPU reference path (CPUv2 lock selected) plus the 007-f
  cleanup/lease composition, the 007-j GPU child/protocol/launch/
  assets software, the 007-k pure snapshot declaration
  codecs, the 007-l owned GPU parent/identity and native
  runtime-identity software, the 007-m isolated GPU text
  bridge and source-bound GPU plan software, the 007-n
  launch-preparation/producer/program/executor software
  and the inert raw GPU backend source are software
  under trusted neural fakes only (no real GPU, driver,
  Tensor or model was run); the actual BGE model has
  never been run, the legacy optional CPU pins are NOT security
  qualified, the archived prior OWNED random CPU toy was historically
  run (toy evidence), the ACTUAL BGE checkpoint/model has NOT been
  executed or qualified, the current 38-dependency and class-level
  interoperability differs from real BGE forward and both differ from
  the controlled neural fakes, and there is still no actual-model CPU query execution,
  resumable owned GPU batches or qualification contracts), live
  PR/CI/merge state is
  queried on GitHub, not asserted here. Objective 006 is complete and merged to
  main as PR #8 (merge commit 11badc7; final slice 006-e bounded native
  PDF structural correction, terminal resolution
  oap/reviews/006-resolution.json). Objective 005 is complete: both slices (005-a canonical
  source integration, 005-b canonical provenance and job records)
  were root-reviewed and merged to main as PR #7 (merge commit
  4977186; final review oap/reviews/005-b-review.json, terminal
  resolution oap/reviews/005-resolution.json). Objective 004
  likewise merged as PR #6 (merge commit bd8e454). All real
  qualification trials remain NOT_RUN; the development merges are
  not qualification.
- 007-s (watchdog observation repair; same PR 9, transcript-first):
  bounded TEST-harness continuation of 007 — the watchdog test now
  interprets an owned process disappearing during a /proc read; no
  production watchdog, timeout or ownership change. Byte-exact
  TWO-file copy from the root-reviewed candidate SELF 8b09617
  (implementation 87be2e8, per oap/reviews/007-s-watchdog-components.json,
  11,871 B): _proc_read returns None only for ENOENT/ESRCH read errors,
  every other OSError propagates; the children/cmdline/exe/stat consumers
  keep successful-content parsing and worker identity and treat only
  absent owned reads as disappearance; the new deterministic
  default-collected node exercises both disappearance codes, a live value
  and EACCES/EPERM/EIO; the paused-parent worker ownership, 5-second
  watchdog, 8-second pending window and final cleanup assertions are
  unchanged. Scoped local evidence: ONE cached python3.14 process ran
  exactly the two named nodes once (disappearance/errors plus paused-parent
  watchdog), 2 passed in 5.88 s under CPU30/AS1GiB/wall120 (wall 6.49 s,
  user 1.21 s, sys 0.24 s, max RSS 140,672 kB), PYTHONPATH unset, five
  thread caps 1, private 0700 basetemp, borrowed CPUv2 fixture roots
  byte-preserved. R distinction preserved: the R report was REJECTED for
  report format (parenthetical implementation head SHA; Root records under
  oap/reviews/007-s-prior-*) while current R CI 43315535020 is all 5 jobs /
  78 steps green — no R report rewrite, no fabricated normal R OK, no
  replayed FIFO. Whole-007 and actual BGE remain UNRUN/UNQUALIFIED; no 008
  advance, no merge.

- 007-t (parity capture integration; same PR 9, transcript-first):
  bounded SOFTWARE continuation of 007 — byte-exact FIVE-file copy of
  the root-reviewed finite1-8 same-source CPU/GPU/query execution DATA
  capture primitive and its analyzer adapter (source implementation
  773aacf, per oap/reviews/007-t-capture-components.json, 69,098 B)
  after the exact eleven frozen Root records plus index transcript
  (110,669 source bytes). Capture evidence stays
  OBSERVED_LOCAL_SOFTWARE_PATHS_UNQUALIFIED / NOT_QUALIFIED: verified
  reuse versus new forward execution is distinguished, and no neural,
  FP16, hardware or current-rights qualification is claimed. Scoped
  local evidence: ONE source-only python3.14 process collected and
  passed 38/38 unit cases; ONE separate cached synthetic process ran
  the two named boundary nodes — the bad-GPU-root refusal BEFORE CPU
  entry passed, but the epoch-revocation node FAILED with
  gpu_embedding_producer.ProducerRefused raised from the _build_plans
  catch-all before any CPU producer entry (expected
  cpu_embedding_producer.ProducerRefused at the CPU before_encode
  authorization); the raw failure is preserved and further actual
  processes were stopped per order pending Root's revised decision.
  The full combined driver remains gated on the current report CI
  (both Product jobs). Whole-007 and actual BGE remain
  UNRUN/UNQUALIFIED; no 008 advance, no merge.
- 007-u (output-repair integration; same PR 9, transcript-first):
  bounded SOFTWARE continuation of 007 — byte-exact FIVE-file copy
  of the root-reviewed explicit locator-only stale-RUNNING output
  repair (source implementation e368730, source report SELF 3fd1d9e,
  per oap/reviews/007-u-components.json, 65,717 B) after the exact
  sixteen frozen Root inputs plus index transcript (57,100 source
  bytes): ONE existing journal replacement (embedding_job_journal.py
  25,497 B — adds the dataclass import, OutputRepairResult,
  _observation_ms and repair_running_output; all existing journal
  definitions preserved) plus FOUR NEW paths (unit + integration
  tests, API/design docs) and this STATUS paragraph — SIX
  implementation paths total. repair_running_output repairs only an
  exact canonical old RUNNING state/revision owned by a distinct old
  owner under a new live exclusive lease, with full frozen plan/output
  validation, equal fresh provider epochs at both named stages and
  revision CAS; it retains the attempt/history/original start,
  refuses observed wall-clock rollback, rereads the verified output
  after commit instead of blindly repeating the repair, and its
  cooperative deadline covers callbacks, commit return and final
  verification without preempting nested operations. COMPLETE with
  RECOVERED_VALID_OUTPUT proves materialization only: execution origin
  SUPPLIED_UNVERIFIED, accounting/physical drain UNKNOWN,
  qualification NOT_QUALIFIED; no discovery, no terminal
  UNKNOWN/FAILED/CANCELLED reopening, no guessed retry, no actual
  policy provider, no model execution; borrowed store/handle remain
  caller-owned. Scoped local evidence: ONE source-only python3.14
  process passed 11/11 unit cases (order forecast 11; wall 0.76 s,
  max RSS 66,440 kB); ONE separate cached synthetic process passed
  the two named nodes — test_positive plus both postcommit-deadline
  phases — 3/3 (order forecast 3; wall 1.09 s, max RSS 67,764 kB);
  both under CPU30/AS1GiB/wall120, PYTHONPATH unset, no bytecode,
  five thread caps 1, fresh 0700 basetemps, raw stdout/stderr/
  resource/exit records preserved; the selected nodes require no
  SLAIF_* fixture environment. The full unchanged repair and T
  capture/reuse drivers remain gated on the current report CI (both
  Product jobs). Whole-007 and actual BGE remain UNRUN/UNQUALIFIED;
  no 008 advance, no merge.
- 007-v (evidence correction + software boundary replan; same PR 9,
  transcript-first): documentation/evidence-only continuation of 007 — no
  product patch, no local product tests. After the exact thirteen frozen
  Root records plus index transcript (39,726 source bytes), byte-exact
  TWO-file copy of the Root-owned FINAL documents (16,538 B, per
  oap/reviews/007-v-document-components.json):
  docs/benchmarks/007-u-local-evidence-correction.md (6,400 B) supersedes
  the U report's local-evidence interpretation only — the published U
  wording undercounts unit-target invocations, the first unexpected
  failure should have stopped further actual processes pending Root
  decision, same-target diagnostics still count, and failed/successful
  outcomes, known/unknown caps, overwritten first-P1 evidence, discarded
  loop outputs and the inferred (unproven) cause are recorded without any
  capped-everywhere claim or fabricated total/date/stdout/proof; the
  immutable U report, retained attempt records and source stay unchanged.
  docs/embedding-software-boundary.md (10,138 B) maps all four original 007
  acceptance criteria to exact callable modules per the independent
  exact-e92 source assessment while EMBED-01/02, FP16 parity,
  current-rights and physical-drain gates remain NOT RUN/UNPROVEN and
  008/010/011/014/015/017/018/019/020/021 obligations stay separately
  owned. U CI 43342353043 is historical for V; whole-007 and actual BGE
  remain UNRUN/UNQUALIFIED; no 008 advance, no merge.
- 008-a (raw snapshot foundation; NEW PR, branch
  oap/008-raw-hybrid-snapshots, transcript-first, same main base
  1a8fddf8 as accepted PR9): first bounded slice of objective 008 —
  byte-exact 25-file transfer (142,322 B) of the Root- and
  peer-reviewed local assembly per
  oap/reviews/008-a-foundation-components.json (five production
  modules: technical_analyzer, raw_snapshot_membership,
  raw_snapshot_source_rows, raw_snapshot_dense,
  raw_snapshot_lexical; ten test files — five unit and five
  integration suites; the documented 008-a count wording is
  corrected here per Root reconciliation
  oap/reviews/008-a-scoped-prefix-resolution.json while the
  immutable 008-a report is retained unchanged; ten docs/parallel
  contracts) plus nine exact Root records and the exact index in
  the transcript commit. Strict token preservation, whole-batch
  membership, original-backed source rows, normalized finite read-only
  FP32 dense storage and canonical lexical payloads with 4,096-row/128-
  group bounded limits; 20k capacity remains NOTQUALIFIED. No
  writer/reader/query/current-policy/quality interface, no CLI/
  publisher wiring, existing canonical modules unchanged, no local
  product tests, no new dependencies; historical exact-source
  49-unit/source-row proof and current report-head CI (pending) are
  the evidence boundary; whole 008 remained PARTIAL at 008-a, no
  merge.
- 008-b (source construction; same PR 10/branch, transcript-first):
  second bounded slice of objective 008 — byte-exact 21-file
  transfer (145,034 B) of the Root- and peer-reviewed local assembly
  per oap/reviews/008-b-construction-components.json (four production
  modules: raw_snapshot_row_builder, raw_snapshot_files,
  raw_snapshot_program_coverage, raw_snapshot_directory; four unit
  and five integration suites; eight docs/parallel contracts) plus
  eight exact Root records and the exact index in the transcript
  commit, and correction of the 008-a foundation count in current
  docs/retrieval.md and STATUS (25 = 5 production + 5 unit + 5
  integration + 10 docs; immutable 008-a report unchanged).
  Selected-batch row-map DATA builder, snapshot file-set
  correspondence DATA, selected-program row-coverage DATA and
  private snapshot directory DATA reader, all with 4,096-row/128-
  group finite limits, borrowed stores and cooperative deadlines;
  20k capacity remains NOTQUALIFIED. No
  writer/publisher/FileBuilder/query/current-policy/quality
  interface, no CLI wiring, existing canonical modules unchanged,
  no local product tests, no new dependencies; one historical
  bounded 7-row synthetic journey and the report-head CI now
  recorded terminal at d9ef6b4 (run 43362986520: all five jobs /
  all 78 steps SUCCESS, full normal 1,836 unit + 838 integration
  on both Product 3.12/3.14 legs per
  oap/reviews/008-b-ci-terminal.json) are the evidence boundary
  for that head; the immutable 008-b report's 11-new-Python AST
  wording is a documented count limitation — the slice
  transferred 13 — per Root clarification
  oap/reviews/008-b-scoped-prefix-resolution.json (report
  preserved unchanged); whole 008 remained PARTIAL at 008-b, no
  merge.
- 008-c (publication reader; same PR 10/branch, transcript-first):
  third bounded slice of objective 008 — byte-exact 25-file
  transfer (200,027 B) of the Root- and peer-reviewed local
  assembly per
  oap/reviews/008-c-publication-reader-components.json (five
  production modules: raw_snapshot_publication,
  raw_snapshot_selection, raw_snapshot_catalog,
  raw_snapshot_pin, raw_snapshot_file_builder; ten test files —
  five unit and five integration suites; ten docs/parallel
  contracts) plus nine exact Root records (37,297 B) and the
  exact index in the transcript commit. Immutable private
  publication with no-replace rename/fsync and explicit
  publication_may_exist rename uncertainty, exact
  expected-pointer selection with generation CAS and
  selection_may_have_changed replace uncertainty, source-backed
  bounded catalog (32 MiB non-vector), creator-owned lifetime
  pin without removal, and FileBuilder constructing plus
  independently validating unqualified DATA from the borrowed
  stores — 4,096-row/128-group/96 MiB finite limits preserved,
  20k capacity remains NOTQUALIFIED, no cap raise or silent
  truncation; the blanket no-caller wording is corrected to no
  CLI/application entrypoint because interlibrary callers now
  exist. No query/scoring/operator/current-policy/public-route
  integration, no CLI, existing canonical modules unchanged, no
  local product tests, no new dependencies; zero local tests
  this round and current final-head CI (pending) are the
  evidence boundary; whole 008 remains PARTIAL, no merge.

- 008-d (CI process observation; same PR 10/branch,
  transcript-first): test-only repair of the narrowly observed
  actual 3.14 CI failure at the 008-c report head 322c7fe0 (run
  43368073059, job 131697112168) — the preserved
  test_timeout_kills_owned_descendant post-kill observer
  _descendant_gone caught only FileNotFoundError while the
  runner raised ProcessLookupError/ESRCH; the observer now
  accepts exactly the two absence classes (ENOENT, ESRCH) and
  keeps the direct stat read, zombie observation and
  live-state refusal (no broad except, existence precheck,
  retry, sleep increase, deadline/cap change, skip or fixture
  rewrite), with two new deterministic regressions
  (parameterized errno-bearing ENOENT/ESRCH absence cases, and
  live S false / zombie Z true / PermissionError-EPERM and
  OSError-EIO propagate, one read each) and the unchanged real
  timeout test; no product module, setup.run/cleanup, other
  test, CI, dependency, profile, architecture, law, prior
  report or source-book change; one bounded local pytest
  process (four node IDs, five cases passed, exit 0, 1.18 s
  elapsed under CPU 10 s / AS 1 GiB / wall 30 s / affinity 0 /
  five thread vars 1 / closed env, pinned Python 3.14.4 +
  pytest 8.4.2; private fsync'd preflight/argv/env/caps guard,
  split stdout/stderr, GNU time and exit records) plus
  optional static AST/compile checks; new
  docs/ci-proc-observation.md explains the actual old-3.14
  failure, the observer-only fix, the exact local evidence and
  the current final-head CI status; the old failed 3.14
  artifacts are preserved unchanged (not marked green
  retrospectively); current final-head CI (pending) is the
  evidence boundary; whole 008 remains PARTIAL, no merge.
  Current correction per the Root 008-d evidence replan: the
  private harness directory reset, check-cat guard and uncapped
  metadata/fsync/pytest-version probes do not establish one-shot
  provenance, so LOCAL-008D-ONE-SHOT-ATTESTATION remains UNPROVEN
  permanently and the harness is never rerun or reused; that round
  moved 9 paths excluding its own report and 10 including it
  (immutable report preserved); the old 3.14 failure stays
  preserved, not green.

- 008-e (raw scoring transfer; same PR 10/branch,
  transcript-first): byte-exact 37-file transfer (451,715 B) of the
  Root-reviewed donor SELF b289e8d9 per
  oap/reviews/008-e-scoring-components.json — four production
  modules (raw_dense_search, raw_lexical_search, raw_rank_fusion,
  raw_hybrid_search), seven unit and seven integration suites,
  seventeen docs/parallel contracts, and two dependency metadata
  files (only bm25s 0.2.14 + SciPy 1.18.1 added; no old package
  version removed or changed; no lock regeneration) — with exactly
  one narrow test-fixture portability adaptation ordered by the Root
  D0 addendum oap/reviews/008-e-portability-addendum.md:
  tests/integration/test_raw_hybrid_trace_composition.py calls the
  inherited test_native_tokenizers.make_native once before its
  subprocess guard, verifies the two pinned artifact hashes and
  drops the hard-coded private witness cache, while all other 36
  indexed files stay byte-exact. Transcript commit carries the
  unchanged FINAL order, active 008-e+LF, nine exact Root records
  (29,999 B), the exact index and the unchanged addendum (13
  paths); three current docs updated (retrieval 008-e scoring
  section, this STATUS entry, ci-proc-observation corrections and
  portability note). Static Git/hash/AST/metadata checks only: no
  local product, unit, integration, collection, import, setup,
  model, store or scorer process; the full unchanged hosted CI
  supplies new-head behavior (pending). Authorized partitions,
  normalized 1024-D CPU vectors, pinned Lucene BM25/technical
  analyzer, deterministic caps and RRF 60 with no raw-score
  addition, fail-closed source/catalog/ACL binding and supplied
  (unverified, not attested) trace origins are preserved; the
  completion-locator/construction and query joins, the
  application/serving constructor, pinned-query entrypoint,
  current-service and current-principal/policy gates remained absent
  at 008-e; 008-f then transferred the completion-locator/construction
  and pinned-query joins as private modules (the application/serving
  constructor and current-service/current-principal/policy gates
  remain absent). Whole 008 remains PARTIAL, no merge.

- 008-f (construction/pinned-query join transfer + lint repair; same PR
  10/branch, transcript-first): byte-exact 19-file transfer (129,802 B)
  of the Root-reviewed prepared SELF 1224dae (implementation 78d2598)
  per oap/reviews/008-f-joins-components.json — three production
  modules (raw_snapshot_completion_locator, raw_snapshot_construction,
  raw_snapshot_query), three unit and three integration suites
  (including the new normal-CI controlled-encoder query case and the
  new construction-composition case), ten docs/parallel
  contracts/provenance — eighteen NEW paths plus the existing trace
  integration file changed ONLY in its one overlong (101-char, E501)
  docstring line, the format-only repair of the 008-e report-head lint
  failure. The transcript commit carries the unchanged FINAL order,
  active 008-f+LF, eleven exact Root records (38,427 B) and the exact
  index (14 paths); the implementation commit carries the 19 blobs
  plus only docs/retrieval.md and STATUS.md (21 paths). Static
  Git/hash/AST/metadata checks only: no local product, unit,
  integration, collection, import, setup, model, store or scorer
  process; no donor-branch merge, cherry-pick, reset, clean, stash,
  switch, rebase or force push; the donor's unrelated 009 code and
  obsolete fixture were not copied. Preserved 008-e record:
  report-head CI run 43377547440 at head 50a85ac failed both Product
  jobs (3.12 job 131727449278, 3.14 job 131727448752) at the lint step
  on that one docstring line with all later product steps SKIPPED (not
  pass); three OAP jobs succeeded; the failure, raw log and immutable
  008-e report are preserved unchanged, not accepted or retried. The
  transferred joins keep supplied/unverified execution origin,
  NOT_QUALIFIED results, borrowed stores, cooperative deadlines,
  fail-closed source/ACL/policy binding and the before-encode
  unavailable-partition refusal; the private real Toy proof driver and
  009 extras remain excluded. The full unchanged hosted CI at the new
  report head (all five jobs, unit + integration on 3.12/3.14) is the
  evidence boundary and remains pending. Whole 008 remains PARTIAL, no
  merge.

- 008-g (bounded pytest parameter IDs; same PR 10/branch,
  transcript-first): test-metadata-only repair of
  tests/unit/test_raw_snapshot_completion_locator.py — the
  test_bad_program_refused parametrize gained six stable unique short
  IDs (empty, malformed-json, trailing-newline, mutable-bytes,
  bytes-subclass, oversized-program); all six payload expressions are
  byte-identical (including b"x" * 16777217), case cardinality is
  unchanged (6), and the module AST equals the base after removing the
  one ids keyword. The transcript commit carries the unchanged FINAL
  order (d3f220b3…), active 008-g+LF, three exact Root records
  (3,722 B) and the exact index (1,100 B, SHA-256 a2eb1596…; 6 paths);
  the implementation commit carries the test file plus only
  docs/ci-parameter-ids.md (new), docs/retrieval.md and STATUS.md
  (4 paths). Bounded local evidence under owned disposable children
  (CPU 10 s / AS 1 GiB / wall 60 s / affinity 0 / five thread vars = 1 /
  closed env / bytecode + third-party plugin autoload disabled, built-in
  cache provider enabled / deliberately lowered 1 MiB child file-size
  limit / fresh 0700 scratches): one pre-edit collect-only (51 collected,
  max node-ID 16,777,295 chars — the serialized oversized payload; no
  cache/nodeids write under collect-only in pytest 8.4.2, no error), one
  post-edit full module run (51 passed in 0.42 s, exit 0, session finish
  and cache write succeeded; cache/v/cache/nodeids 4,601 B, max node-ID
  95 chars), static AST/hash checks and one ruff 0.17.4 (SHA-256
  4ef33997…) pass on the changed file. Honest attempt history: FOUR
  attempted pytest processes (A usage-fail before collection, A2 old
  collect, B pre-correction full run, F the D0-permitted final run);
  A2 and B preceded the Root correction records and are preserved
  without replay; no further runtime is authorized or performed.
  Preserved 008-f record: report-head CI run 43383127224 at head
  5509c6ba failed both Product jobs (3.12 job 131745302976, 3.14 job
  131745303383) in the pytest session-finish cache/nodeids write
  (OSError errno 27) after unit progress 100%, with no failed assertion
  in the logs and all later product steps SKIPPED (not pass); three OAP
  jobs succeeded; the failure, raw logs and immutable 008-f report are
  preserved unchanged, not accepted or retried. The exact original CI
  file-size limit value was NOT measured (an inherited RLIMIT_FSIZE
  remains an unverified inference); no cap was raised or changed. All
  local evidence is synthetic owned-test-infrastructure proof, not a
  CI-ceiling measurement and not model evidence; see
  docs/ci-parameter-ids.md. No merge, no cherry-pick/reset/clean/stash/
  switch/rebase/force push. The full unchanged hosted CI at the new
  report head (all five jobs, all steps, unit + integration on
  3.12/3.14) is the evidence boundary and remains pending. Whole 008
  remains PARTIAL, no merge.

- 009-a (evaluation foundations first software wave; NEW PR, branch
  oap/009-evaluation-baseline at exact base 5a7b41cc, transcript-first):
  byte-exact 32-file transfer (322,735 B) of the Root-reviewed donor
  SELF 8c351a95 (implementations c91a5c2b / 70d3b61f) per
  oap/reviews/009-a-components.json (SHA-256 f3f65b1b…) — six
  production modules (text_evaluation_dataset, supplied_rank_metrics,
  text_evaluation_gold_binding, declared_span_support,
  source_bound_ranking, source_bound_text_support), six unit suites and
  twenty docs/parallel API/design/oracle contracts; all 32 paths NEW at
  the actual base and the 27 shared lower 008 paths byte-identical, so
  no API adaptation or branch transfer. The transcript commit carries
  the unchanged FINAL order, active 009-a+LF, the eight exact Root
  records (26,410 B) and the exact 2,628 B index (11 paths); the
  implementation commit carries the 32 blobs plus only
  docs/evaluation.md (new), docs/benchmarks/raw-baseline.md (new) and
  this STATUS.md (35 paths). Static Git/hash/size/JSON/AST checks only:
  all 32 donor blobs verified by size + SHA-256 + Git-object identity
  before copy, all 32 absent at base, all 12 Python files parse after
  copy; no local product, unit, integration, collection, import, setup,
  model, store or scorer process, no source fixup/format/deps/workflow
  change. The six APIs are private evaluation contracts (three pure,
  three borrowing the original/derived stores): declared (unverified)
  dataset admission with STRUCTURAL_ONLY splits, supplied graded-rank
  mathematics (graded MRR/nDCG/Recall, explicit
  UNDEFINED_EMPTY_POSITIVE_GOLD), bind-time original gold revalidation
  (not atomic, not current rights), declared span geometry, supplied-rank
  source binding (SUPPLIED_SCOPE_CHECKS_ONLY, NOT_ATTESTED) and the
  operator-only composed text-support diagnostic (NOT_CHECKED gold
  eligibility, SEQUENTIAL_OBSERVATIONS_NOT_ATOMIC). No metrics from
  requirement grades, no actual source/hybrid join and no real baseline
  execution in this wave: the raw baseline stays NOT RUN and the
  human-heldout/corpus-rights/current-auth/qualified-encoder gates remain
  open (docs/benchmarks/raw-baseline.md). The full unchanged five-job
  CI at the new report head is the evidence boundary and remains
  pending. Whole 009 remains PARTIAL; no merge; no 010 activation.

- 009-b (dataclasses.replace portability correction; AMEND PR 11, same
  branch oap/009-evaluation-baseline, transcript-first): the transcript
  commit carries the unchanged FINAL order, active 009-b+LF, the three
  exact Root records (4,683 B: 009-a source/report review, 009-a
  CI-failure reconciliation, 009-b CI-correction replan) and the exact
  1,085 B index at oap/reviews/009-b-root-records.json (SHA-256
  0105880d…) — six transcript paths on sole parent 21a3cbd (the 009-a
  report head). The implementation commit changes ONLY three paths:
  tests/unit/test_text_evaluation_dataset.py (old SHA-256 901707ff…;
  the single line 46 `pytest.raises(TypeError)` becomes
  `pytest.raises((TypeError, ValueError))` immediately around
  dataclasses.replace(result, qualification="QUALIFIED"); module AST
  equals base 21a3cbd after normalizing the tuple back to TypeError),
  docs/ci-dataclass-replace-portability.md (new) and this STATUS.md.
  Bounded local evidence (Python 3.14.4 only, pinned venv): ONE full
  dataset unit module pytest run 19 passed / exit 0 (fresh private
  cache nodeids 1,614 B; max RSS 62,724 KiB; closed env; default
  assertion rewriting, no --assert=plain; inherited rlimits CPU
  10 s / AS 1 GiB / FSIZE 16 MiB + CPU 0 affinity; the 60 s wall was a
  launcher-level backstop, not a descendant wall proof) and ONE Ruff
  0.17.4 changed-file check All checks passed. Root pre-SELF precision
  review accepts these as LIMITED evidence with preserved procedural
  deviations (no backfill, no extra runtime/retry); the 009-a head CI
  failure (run 43395492425) and all earlier reports/runs are preserved
  unchanged; the full unchanged five-job CI at the new report head is
  the evidence boundary and remains PENDING. Whole 009 remains
  PARTIAL; no merge; no 010 activation.

- 009-c (source-backed stage evaluation v2; AMEND PR 11, same branch
  oap/009-evaluation-baseline, transcript-first): the transcript commit
  ac408fe0 carries the unchanged FINAL order, active 009-c+LF, the
  eleven exact Root records (52,832 B, including the source component
  index at oap/reviews/009-c-components.json) and the exact 3,512 B
  index (SHA-256 659d3856…) — fourteen transcript paths on sole parent
  aba42a52 (the 009-b report head). The implementation commit changes
  exactly 25 paths: the 22 indexed byte-exact blobs (395,115 B from
  source SELF e6b229b1; 21 NEW verified absent at base, one MODIFY
  against exact preimage d4cdcb97…) plus docs/evaluation.md,
  docs/benchmarks/raw-baseline.md and this STATUS.md. Static
  Git/read/hash/AST/JSON identity verification only: every blob verified
  by size + SHA-256 + Git-object identity before and after copy, changed
  Python parses, structured copied inputs parse, canonical portable
  dataset unit b00aa74f… preserved; no local lint, collect, product,
  unit, integration, native, model, scorer or store run, no setup or
  download. Prior local evidence attribution preserved (51/45 unit
  cases, raw bridge V3 eight-attempt, stage-loss v2 eight ordered cases
  two-positive/six-refusal/six-workers-reaped, v1 preflight failure with
  separately approved v2; GNU values are waited-process observations,
  not aggregate tree bounds or encoder performance). Coverage 2624:
  cohort harness/source aggregation/complete denominators/private
  split-report integration ABSENT — documented, separately ordered
  same-009 work. The full unchanged five-job CI at the new report head
  is the evidence boundary and remains PENDING. Whole 009 remains
  PARTIAL; no merge; no 010 activation.

- Product implementation: IN PROGRESS — foundation (objective 002-a,
  merged), the complete 003 gateway/transport/native/probe slice
  (merged as PR #5) plus the 004-a finite qualification trial runner
  with the 004-b strict bounded trial spec/sample/result evidence
  contracts with the 004-c cross-field consistency bindings and
  quartile-complete stage summaries, bounded safe spec file input with
  decoded-Unicode admission and available-stage summaries, actual
  gateway/direct repeated-parent composition and the machine-readable
  section 23.2 gate projection, plus the 004-d bounded read-only local
  resource telemetry (explicit opt-in `resource diagnose` own-process
  CPU/RSS diagnostic and `qualification run --resources` wrapper with
  the plain v1 trial evidence intact; at most one bounded nvidia-smi
  metadata query; no remote/worker/model-process measurement), open on
  PR #6, see history, with the 004-e corrections of its resource
  lifecycle (shared-deadline startup admission, every-exit-path
  observer stop), honest aggregate byte accounting at the pipe and
  sample boundaries, late-export spent-ledger handling and strict
  versioned collector/code-source binding. Hardware/model
  qualification: NOT RUN. ICA:
  NOT RUN.
- The coding client is active on objective 009 (PR 11, branch
  oap/009-evaluation-baseline; PR number 11 assigned by GitHub at
  009-a publication), not idle; the 008-era wording is historical.
- Current main is the 008 merge commit 5a7b41cc (PR #10, parents
  1a8fddf8 + 29447168, merge tree equal to 2944); the 009 branch (new
  PR) builds from it. Historical: while 008 was in flight, current main
  was the 007 merge commit 1a8fddf8 (PR #9) and the 008 branch built
  from it; while 007 was in flight, current main was the 006 merge
  commit 11badc7 (PR #8) and the 007 branch built from it.
- The 2026-11-10 human MVP activation re-enabled the strategic runtime
  for the current MVP; the executed program is docs/MVP-EXECUTION-PLAN.md
  (strategic, copied unchanged).
- GitHub branch/PR state must be queried live; no current SHA or active
  objective is asserted in durable constitutions beyond the recorded
  merge commits below.

## Historical events (chronological)

Bootstrap/materialization: VALIDATED LOCALLY, 2026-11-01; 39 helper tests
passed. See docs/bootstrap/BOOTSTRAP-RECEIPT.md for exact scope, evidence
and limitations. Product implementation was absent at that time; no
product order/control signal, commit, push or PR was created during the
bootstrap.

000-a (OAP scaffold publication + CI): merged as PR #1 (merge commit
08b21db). CI covers the OAP scaffold only (docs/CI.md); product/hardware
evidence remains absent.

Architecture revision 2.0 publication: merged as PR #2 (merge commit
976381e). Main CI 42721733037 successful for Python 3.12/3.13/3.14 per the
activated order's verified dependencies.

001-a (environment/contract inventory): merged as PR #3 (merge commit
3178650). Published docs/environment-inventory.md (CPU-only development
host facts; gateway repository contract pinned to
f2df0e82df8766740d9ac169ea56ffd7a3cb1f1e; reported long-context capability
kept separate from unmeasured target configurations; unknown deployed
facts and exact prerequisites), persisted docs/MVP-EXECUTION-PLAN.md
unchanged, and committed the 000 strategic resolution unchanged. No live
service was changed.

002-a (foundation and qualification harness): merged as PR #4 (merge
commit 93b4317, the current main), branched from main 3178650. Added the
installable src package (slaif_raggedized_helper: strict config, typed
generator/embedding/reranker contracts, model lock/qualification schemas,
offline `raggedized doctor`), locked lightweight environment (uv.lock;
pydantic runtime; pytest/ruff dev), focused product tests (tests/unit)
plus an OAP fixture source-copy boundary fix, a separate product CI job,
docs/foundation.md, JSON schemas and THIRD_PARTY_NOTICES. Foundation code
and mocked contract composition only: product runtime qualification
remains NOT RUN/UNKNOWN; no model, GPU, live route or service change.

003 slice (generator adapters + transport/gateway correctness; open on
PR #5, branch oap/003-generator-adapters-and-cache-probes from main
93b4317):
- 003-a PARTIAL checkpoint: the gateway `POST /v1/responses` adapter and
  bounded HTTP/SSE transport (one total deadline, pre-dispatch-only retry,
  UNKNOWN_COMPLETION ambiguity semantics, bounded queue backpressure and
  cancellation) plus real loopback HTTP/SSE integration tests
  (tests/integration) wired into the product CI job; actual behavior and
  contract: docs/generator-contract.md. Round report:
  oap/reports/003-a-generator-adapters-and-cache-probes.md.
- 003-b bounded transport/gateway repair: published round report
  oap/reports/003-b-transport-gateway-correctness.md; strategic review
  CONTINUE/NOT_ACCEPTED at the 003-b report candidate (actual malformed
  wire successes/raw exception and valid multipart rejection contradicted
  criterion 6).
- 003-c: gateway protocol validation repair of the
  remaining structural gaps (malformed type/ID/coordinate/status
  handling, valid multipart streams, deterministic zero-dispatch deadline
  boundary, scoped docs); round report
  oap/reports/003-c-gateway-protocol-validation.md; strategic review
  CONTINUE/NOT_ACCEPTED at the 003-c report candidate (six supplied-null /
  part-coordinate / item-type / done-latch / reasoning-status variants
  still produced TERMINAL).
- 003-d: structural validation closure of the shared coordinate and
  item-lifecycle invariants behind those six variants (supplied-null vs
  absent coordinates, bounded sequential content-part numbering bound to
  final part positions, item type/identity freeze added through done/
  final, latched item completion, per-type terminal done status),
  actual-HTTP regressions, scoped docs.
- 003-e: the private trusted OFFLINE native llama.cpp
  `/completion` adapter (model_clients/direct.py): explicit
  offline_diagnostic materialization policy (private/loopback destination,
  private_trusted, declared model identity, template qualification,
  explicit finite operator limits), annotation-only purpose with visual/
  image and answer refusals before any network work, server-rendered
  templates through the pinned `/apply-template` contract (no local
  rendering, no local name allowlist; corrected pinned reference
  template registry), exact bounded `/completion` envelopes with
  tested-only cache_prompt/id_slot, one total deadline spanning template
  work + generation + retries (pre-inference expiry refuses), finite
  pre-dispatch-only retry, the fail-closed stop-terminal matrix (stop=true
  is stopped, not successful; only eos with usable content succeeds),
  metric mapping from the pinned dialect's actual reported fields
  (tokens_cached is the slot prompt total, never a cache-hit
  substitute), actual-HTTP loopback regressions, the narrow
  JSON-integer-digit-limit ValueError guard at the gateway non-stream
  parse with actual-HTTP regressions (in-process and a controlled-limit
  isolated subprocess), regenerated JSON schema and scoped docs. The 003
  probe tooling then remained pending (delivered in 003-h); live
  qualification is out of 003 software scope (003-a Runtime: live
  authorization NONE) and stays with the 004/019/full-MVP gates.
- 003-f/g: native metric-quantity and default-deny JSON/schema
  corrections, then the native boundary closure (safe finite phase-total
  arithmetic; explicit required-JSON_MODE capability admission) with
  actual-HTTP regressions; round reports
  oap/reports/003-f-native-contract-corrections.md and
  oap/reports/003-g-native-boundary-closure.md.
- 003-h: the bounded explicit generator qualification
  probe (`src/slaif_raggedized_helper/probes.py` + `raggedized probe`
  CLI): explicit opt-in repeated-parent experiment with one overall
  experiment deadline, finite call/attempt and total output-token
  budgets enforced at the real transport boundary (call allowance
  reserved before every transport invocation; ambiguous dispatched
  work spent and never replayed; retries/template work cannot bypass
  the budget), safe structured evidence (declared unverified
  identities, opaque endpoint digest, fingerprinted inputs,
  digest-only output checks, reported-metric-only cache conclusions),
  installed-CLI subprocess composition over owned loopback HTTP, the
  documented gateway minimum-capability admission repair (explicit
  required JSON_MODE/PROMPT_CACHING honored independently of the
  format/cache-key fields; unqualified minimums refuse at zero HTTP;
  qualified minimum-only and ordinary TEXT positive controls retained),
  and docs/README/TESTING/STATUS updates. Live qualification,
  caching-effectiveness and hardware evidence remain NOT RUN.
- 003-i (current round): probe evidence and credential boundary
  corrections over the same probe/CLI, scoped to the demonstrated
  gaps: bounded, non-blocking, regular-file-only single-line
  credential resolution with fixed typed missing/invalid outcomes
  (no raw UnicodeDecodeError; owned FIFO refused without a blocking
  open and no killed child) and file references recorded in evidence
  as opaque digests (no private path, no value); label-independent
  same/different output evidence with phase-identity fingerprints kept
  separate and the documented namespaced expected-digest format;
  reported-vs-validated cache counters (supported accounting relation
  checked before any qualification conclusion; contradictory
  counters are raw facts only and unqualified; the pinned gateway
  dialect's reported cached_tokens corrected as distinct from its
  absent evaluated-prefill metrics); exported declared backend
  fingerprint per request and in identities with `target_type:
  unverified` replacing the unsupported hard-coded fixture/live
  classification; knowably invalid `--output` destinations refused
  before dispatch (exit 2, zero HTTP) and post-work write failures
  returning the honest exit-3 export-stage error with the full
  spent-attempt evidence on stdout. Unit and installed-CLI owned-
  loopback regressions for every corrected case plus the retained
  003-h positive controls; docs/README/TESTING/STATUS updates. Live
  qualification, caching-effectiveness and hardware evidence remain
  NOT RUN.
- 003-j (current round): credential-value admission aligned to the
  ACTUAL locked HTTPX 0.28.1 string-header serializer: the transport
  passes the `Authorization` header as a Python str whose serializer
  encodes as ASCII with no encoding override, so the admitted domain
  is exactly 0x20-0x7E. The previously missed 0x80-0xFF Latin-1 range
  (e.g. U+00E9, valid UTF-8 file/env bytes decoding to an
  unserializable str) is now refused pre-dispatch for env AND file
  references with the fixed typed `CREDENTIAL_INVALID` /
  `value_not_ascii` outcome (exit 2, zero HTTP, no raw
  `UnicodeEncodeError`, no key or path echo), replacing the 003-i
  `value_not_latin1` reason; ASCII positives, C0/DEL control refusal,
  bounded regular-file/FIFO/UTF-8/size handling and the opaque
  credential-path digest are retained. Unit and installed-CLI
  owned-loopback regressions cover file and env U+00E9 plus an
  outside-Latin-1 value and ASCII positives; the proved 003-i
  output-stage fixes (owned-0400 / invalid-directory pre-dispatch
  refusal; genuinely late post-work export failure with exit 3, full
  safe JSON on stdout, exact spent-attempt accounting and a safe
  post-work stderr stage) and the exception-safe Python 3.12/3.14
  destination probes are preserved. Documentation corrected to the
  actual scope: 003 software acceptance is adapters/probe tooling +
  synthetic HTTP (003-a Runtime: live authorization NONE), with
  live-target evidence a separate 004/019/full-MVP gate; the 8192
  credential-file size cap (bounded lookahead, not an exact read
  claim), the real probe module path and the post-work export stage
  described accurately. Live qualification, caching-effectiveness and
  hardware evidence remain NOT RUN.
- Objective 003 scope fidelity (order 003-a Runtime: live
  authorization NONE — "accept callable adapters/probe tooling and
  synthetic HTTP evidence only"): the 003 software acceptance is the
  adapters and bounded probe tooling qualified by synthetic
  owned-loopback HTTP; live-target evidence is NOT a 003 closure
  prerequisite — it belongs to the separate 004/019/full-MVP
  qualification gates, which remain OPEN and NOT RUN. Objective 003
  was accepted and merged as PR #5 (merge commit 2bc320f,
  2026-11-10); the strategic 003-j review and resolution records were
  committed unchanged with 004-a.
- 004-a (trial runner and gateway/direct composition; open on PR #6,
  branch oap/004-qualification-harness from main 2bc320f): the first
  proof-sized slice of objective 004 under the explicit D0 replan
  (authorized real gateway/GPU/model/corpus inputs remain absent;
  004 establishes usable instrumentation and exact prerequisites;
  actual A1/hardware/quality feasibility remains UNPROVEN, mandatory
  at 019/ICA/MVP). Delivered executable software, not a JSON approval
  wrapper: strict finite trial spec/sample/result contracts
  (slaif_raggedized_helper/qualification/spec.py: bounded, frozen,
  extra-forbid; declared workload/seed fingerprints verified
  pre-dispatch; unimplemented context/pair/batch/precision/seed
  controls refuse with named prerequisites); a finite trial runner
  (qualification/runner.py) that actually invokes the current
  gateway/direct application adapters through the REAL transport with
  ONE absolute trial deadline and ONE shared dispatch admission
  allowance spanning all warmups, repetitions, retries, template and
  model calls (enforced at the real transport dispatch boundary, the
  reused 003 shared-budget seam; native template work consumes the
  allowance; exact sample-start minimums), safe per-trial/per-phase
  observations (fingerprints only, declared-vs-observed identities
  with unavailable physical identities explicit, physical cold/warm
  state unknown, reported-only usage, contradictory cache/input
  accounting as raw facts only); reproducible nearest-rank latency
  analysis (qualification/analysis.py: deterministic pure function,
  terminal samples only, zero-sample nulls, no qualifying pass from
  synthetic/configured-unverified evidence); the deterministic
  explicit synthetic route (--synthetic: owned loopback fixture,
  real adapters, evidence labeled MOCK / synthetic-owned-fixture,
  configured secrets never read; a configured URL is never
  classified synthetic by a boolean); CLI `raggedized
  qualification gates|plan|run` (help/import/plan/gates zero
  model/HTTP/telemetry I/O; run is explicit opt-in; exit codes 0/1/2/3
  with the honest post-work export stage); the machine-readable
  prerequisite projection of every architecture section 23.2 ID
  (qualification/gates.py + docs/benchmarks/qualification-gates.json:
  all real trials NOT_RUN, live target authorization NONE, only text
  repeated-parent runner entrypoints executable in this slice);
  installed-CLI owned-loopback composition tests (gateway + direct,
  budget boundaries, deadline/cancellation, unknown-no-replay,
  preflight zero-dispatch, metric ambiguity, deterministic synthetic
  route, zero-I/O plan/gates) and unit contracts; docs/benchmarks/
  qualification-protocol.md plus README/TESTING (T08)/STATUS/CI/
  UNCERTAINTIES updates. The one ordered operational correction:
  oap/prompts/coding-startup.txt replaced with the exact
  /goal-first bounded-goal bytes (SHA-256
  6d2323bb832e5f78e4cd86d6951c04c0b3975dc80730c473fc7834820965a98e)
  with docs/AGENT-ROLE-SETUP.md, docs/OAP-RUNBOOK.md and the
  governance manifest measurement updated; the new startup is NOT
  operationally validated by file hash alone (strategy qualifies it
  during the same-objective 004-b fresh control handoff). The
  strategic 003-j review/resolution files and the unchanged 004
  order/active are committed with this round. Live target/model/GPU/
  corpus work: NONE; all real qualification gates and LICENSE-01
  remain open (certifi MPL-2.0 exception not granted); 004-b/005+
  selection remains strategy alone.
- 004-b (evidence-contract correction of the verified 004-a head;
  amends the same open PR #6, branch oap/004-qualification-harness):
  the four ordered corrections from the final 004-a review
  (oap/reviews/004-a-review.json committed byte-unchanged, SHA-256
  02ab0d2288191469c5c480b11777d71b509b3963b8110e0f9afeb5f7a6db0611):
  (F01) bounded safe trial-spec file input (qualification/specio.py:
  non-blocking open with fstat of the actually opened descriptor —
  directories/FIFOs/sockets/devices, including a path resolving
  through a symlink to a special file — refused without blocking;
  65536-byte bound; strict UTF-8; typed JSON decoder/integer/depth
  refusals; fixed safe messages with no input or private-path echo;
  no process-global decoder-limit change); (F02) explicit strict
  bounded sample/result evidence contracts (qualification/contracts.
  py: frozen extra=forbid DTOs with strict int/float/bool; envelope
  invariants — requests are the exact leading prefix of the declared
  workload, remaining+attempted == budgets.max_dispatches,
  status/stop_reason consistency, not_run implies zero dispatches —
  and the analysis section must equal the pure recomputation from the
  recorded samples; used at the construction, analysis and
  serialization boundaries, a violating executed document is an
  honest post-work exit-3 evidence_contract_violation, and the spent
  ledger is preserved); (F03) reproducible available-stage
  n/min/p50/p95/max summaries per warmup/measured group
  (caller_wall/prefill/decode/model_total/ttft with known-zero,
  missing and invalid-observation bookkeeping and per-stage
  provenance; gateway prefill/TTFT stay n=0 all-null, unavailable not
  zero); (F04) documentation corrections to the actual implementation
  (14 section 23.2 IDs, sample-start minimums are an admission guard
  only, context measurements refreshed from the final actual files:
  routine governance 42158 bytes, ceiling 50000; exact model tokens
  and client injection remain UNMEASURED). The 004-b fresh-handoff
  /goal-first startup qualification is RECORDED FAILED by strategy
  (upstream payload refusal before any implementation; the stalled
  goal was cleared and the sole control OK was consumed, never
  replayed); the previously qualified ordinary startup is restored
  and the bounded native goal sequence is set by strategy after this
  ordinary startup — it is NOT claimed passed, and U10 stays OPEN.
  All 004-a transport/budget/retry/native-template/UNKNOWN/
  credential/export positives preserved. No live target/model/GPU/
  corpus work (live authorization NONE); all real qualification
  gates and LICENSE-01 remain open; resource telemetry, vector/rank
  parity and full named gate composition remain required in later
  proof-sized 004 continuations; no merge; 004 continuations and 005
  selection remain strategy alone.

- 004-c (evidence-consistency and metric-completeness correction of
  the verified 004-b head; amends the same open PR #6, branch
  oap/004-qualification-harness): the four ordered corrections from
  the final 004-b review (oap/reviews/004-b-review.json committed
  byte-unchanged, SHA-256
  81f1fa1b4e8566bb5b7ab6a18ea0bef66f81f576dbaaa86516e6984b8c2f5fc4):
  (F01) cross-field evidence bindings (qualification/contracts.py:
  the analysis pure-recomputation is driven by the ACTUAL
  transport-boundary call ledger — an analysis call count that
  conflicts with the ledger is refused; the envelope backend equals
  the declared backend; every KNOWN per-sample backend fingerprint
  equals the observed per-trial backend binding, an absent binding
  stays null; the evidence class and target type form the consistent
  provenance pair; the output reservation total/per-sample equal the
  declared budget with the per-sample share the floor even share over
  the DECLARED scheduled sample count; the cache/input consistency
  counts equal the shared pure derivation from the actually recorded
  raw usage — every single-field contradiction refused, the unaltered
  actual owned-HTTP result admitted); (F02) metric completeness
  (n=0 iff all-null quartiles; n>0 requires EVERY quartile present,
  finite, non-negative and ordered min <= p50 <= p95 <= max; partial
  quartile sets refused; the full result validation still
  recomputes the deterministic summaries); (F03) decoded-Unicode
  admission (qualification/spec.py: a workload string that decodes to
  an unpaired surrogate code point is refused at spec admission with
  a fixed safe reason BEFORE fingerprinting or request construction —
  typed exit 2, zero HTTP, no input echo; valid Unicode including
  escaped astral pairs and Slovenian text admitted unchanged; no
  replacement/truncation/global-encoding/fingerprint-version
  change); (F04) serializer/spent-ledger boundary (cli.py: the
  canonical FULL strict result contract — strict shape plus the
  analysis pure-recomputation — is enforced at serialization; a
  post-work rejection is an honest exit 3 with the fixed safe
  structured error carrying the ACTUAL valid spent-attempt ledger on
  stdout, honest ledger availability when the ledger itself cannot
  validate — never assumed zero, never a crash — and the invalid
  record is never exported as a valid result). These checks prove
  INTERNAL consistency only — never that declared metadata is true,
  that a fingerprint proves deployed identity, or that imported JSON
  was executed here. The root-authored startup-governance restoration
  (oap/prompts/coding-startup.txt the exact previously qualified
  582-byte ordinary prompt, docs/AGENT-ROLE-SETUP.md and
  docs/OAP-RUNBOOK.md) is committed byte-unchanged; the 004-a
  /goal-first qualification remains RECORDED FAILED history, never
  relabeled passed; U10 stays OPEN and real restored
  wrapper/role/order/post-start-goal qualification is strategy's,
  performed on this actual handoff, never inferred from hash.
  Documentation (protocol/TESTING/STATUS/UNCERTAINTIES/README) and
  context measurements refreshed to the actual implementation. All
  004-a/004-b transport/budget/retry/native-template/UNKNOWN/
  credential/export/file-input/Unicode/ledger positives preserved.
  No live target/model/GPU/corpus work (live authorization NONE);
  all real qualification gates and LICENSE-01 remain open; resource
  telemetry, vector/rank parity and full named gate composition
  remain required in later proof-sized 004 continuations; no merge;
  004 continuations and 005 selection remain strategy alone.
- 004-e (resource lifecycle and budget correction of the verified
  004-d head; amends the same open PR #6, branch
  oap/004-qualification-harness): the five ordered corrections from
  the final 004-d review (oap/reviews/004-d-review.json committed
  byte-unchanged, SHA-256
  5a8d4dff6a259dc689cf056071091960501ba1ae321a0b3285b611230bf19e10):
  (F01) the startup nvidia-smi metadata query is clipped to the
  remaining trial AND observer duration and admission is rechecked
  after the query and before every sample — an already-passed
  deadline queries nothing and samples nothing, and no late first
  sample is admitted past expiry (the 0.08 s deadline case that
  previously admitted a ~0.276 s late query/sample); (F02) pipe
  reads enforce the remaining declared allowance plus a bounded
  one-byte lookahead and report the ACTUAL observed bytes (a cap-128
  overflow reports the observed 129 instead of requesting 4096 and
  claiming cap+1), and aggregate collection calls/bytes/time are
  enforced before work across the whole observer lifetime —
  bytes_read is actual observed bytes (never the read cap) with the
  cap reserved per admitted sample, so a finite workload terminates
  with a valid honest partial record at resource_exhausted instead
  of an over-limit invalid document; (F03) the runner stops and
  finitely joins the owned observer on EVERY execution exit path,
  including in-process KeyboardInterrupt with a surviving caller
  (no detached sampler, no continued samples, original exception
  preserved); (F04) late --output failures use the canonical inner
  trial ledger (wrapper-aware): after real work the error reports
  the actual known call count with a replay warning, a
  missing/invalid ledger stays an explicit unknown, and only genuine
  pre-dispatch refusals keep the true zero-dispatch claim; (F05)
  resource schema versions refuse booleans and wrong numeric types,
  and the collector record binds the bounded collector identity,
  code source and actual executing package version with the Git
  source revision explicitly unavailable (no attestation/signing, no
  Git subprocess on import or default commands). The published
  004-d report is immutable; its over-claimed pipe bound, aggregate
  admission, cancellation and collector/code metadata statements are
  superseded by this correction. The retained independent 004-d
  witnesses now demonstrate the corrected behaviors; the plain trial
  v1 contract, the 004-a/b/c positives and the D0 bounded allowance
  are preserved. No live target/model/GPU/corpus work (live
  authorization NONE); all real qualification gates, vector/rank
  parity and the full named gate composition, 019/ICA/MVP and
  LICENSE-01 remain open; no merge; 004 continuations and 005
  selection remain strategy alone.
- 005-a (canonical source integration, first 005 slice; new 005 PR,
  branch oap/005-artifact-schema-and-source-scopes from main bd8e454,
  the PR #6 merge): ONE authorized local --no-ff merge of the
  root-reviewed local candidate branch oap/parallel-005-source-cli tip
  32a2b84d099f2641123d2569b01afe533064ac61 (including the
  source-admission-b tip
  0837191198b2b1712445d5ba6ca268d358637866) preserving candidate
  order/report/implementation histories, plus the thin installed
  `raggedized source` prefix delegation to the existing source_cli.main,
  focused installed-CLI source tests and documentation/governance
  reconciliation. Adds source_admission.py (strict versioned manifest,
  descriptor-bounded approved-root reads, digest-named immutable blobs,
  metadata-sensitive immutable revisions, atomic same-filesystem
  publication) and source_cli.py (bounded import/inspect operator tool);
  the installed route proves shared-byte blob dedup with distinct
  rights/ACL/corpus metadata, metadata-revision immutability, verified
  reuse and safe input-free failures on owned disposable fixtures.
  Strategic 005-a round-start bytes committed byte-for-byte unchanged.
  Block/span/chunk, derived-scope and job/attempt records remain REQUIRED
  same-PR continuations before whole-005 acceptance; no 006 activation or
  partial 005 merge; all real qualification, provenance, license and MVP
  gates remain open (NOT RUN).
- 005-b (canonical provenance and job records; same PR 7 branch):
  TWO authorized local --no-ff merges of the root-reviewed candidate
  tips, provenance first (oap/parallel-005-provenance tip
  3f2ec5768cc07c86c2f0ab663a4e4af23ecac406) then jobs
  (oap/parallel-005-job-records tip
  798d92524dfcf4b24bc312712d21453f159b204a), each forecast clean with
  git merge-tree against the actual parent (purely additive trees, no
  shared-code change), preserving candidate order/report/implementation
  histories. Adds provenance_records.py (admit_record/catalog/Registry
  bind_chunk/bind_neighbors/bind_derived/reader_allows over strict
  versioned Scope/Dependency/Block/SourceFragment/Separator/Chunk/
  Neighbors/Derived/Grants/Restrictions DTOs) and job_records.py
  (admit/serialize/transition over JobSpec/Configuration/InputRef/
  JobState/Attempt/OutputRef), the ONE combined
  tests/integration/test_canonical_records_journey.py store-to-record
  journey (shared-byte two-document store with distinct
  rights/labels/corpus, metadata revision, code-point multi-span
  chunks with explicit separators and repeated table-header
  references, reciprocal neighbors, same-source derived support with
  label union and cross-boundary rejection, unknown-version
  fail-closed reader intersection, job/attempt roundtrip and bounded
  transitions) and docs/data-model.md record protocol. NOT a GitHub
  PR/default-main merge. Extraction, contextualization, embedding,
  snapshots, serving/auth and worker execution remain later ordered
  scope (006/010/007/008/014/017); DTO COMPLETE is not artifact, cache
  or execution proof; all real qualification remains NOT RUN.
- 006-a (native extraction first slice; new 006 PR 8 branch
  oap/006-native-extraction-and-chunking from main 4977186): THREE
  ordered local --no-ff merge steps of the root-reviewed candidate
  tips, PDF-test-setup first (oap/parallel-006-pdf-test-setup tip
  be40286eeafe810071961789aa7d80d2fac847d5, carrying corrected PDF-D
  tip eb80a7bc84fbf74f46882030a3ce277852e18bf2 with the accepted
  parser/worker blobs plus the reproducible development PDF test
  setup), literal line second (oap/parallel-006-text-extraction tip
  e84469f78b82fc5cd41110289bfa7446793ca034, a strict ancestor of the
  first merged tip so its full history is retained and the step
  creates no new commits), structured text third
  (oap/parallel-006-structured-text tip
  7a0caf1a3c51427de33fa7140ec01bc24ca81d13); the two real merges were
  forecast clean with git merge-tree and the merged trees equal the
  forecasts. Adds text_extraction.py, structured_text.py,
  pdf_extraction.py and the fixed pdf_worker.py, the ONE combined
  tests/integration/test_extraction_combined.py journey (shared-byte
  documents with distinct corpus/labels/rights/version, metadata
  revision over one verified blob, exact code-point line/structural
  coverage, mixed native/visual PDF pages binding into the
  provenance Registry, and malformed/oversized/wrong-hash/
  unsupported refusal), the required reproducible PDF development
  tests (missing/incompatible backend or isolation fails instead of
  skipping) wired into both product CI legs via a new private
  pinned hash-verified backend and standalone CPython 3.12 worker
  runtime with runner-only bwrap/prlimit install and namespace
  verification, and docs/ingestion.md supported-subset protocol. NOT
  a GitHub PR/default-main merge. This first slice does not close
  006: structural chunking, native tokenizer sessions and bounded
  composition remain the ordered same-PR continuation;
  contextualization, embedding, snapshot/retrieval, GPU/vision, real
  corpus, model and license/ICA qualification all remain open; all
  real qualification remains NOT RUN.
- 006-b (observed native counts and chunks; same PR 8 branch):
  TWO authorized local --no-ff merges of the root-reviewed candidate
  tips, native bridge B first (oap/parallel-006-native-chunk-bridge-b
  tip 1a9e6387f4ba2134894f81c6827c78d78d462843, implementation
  40d7d867629c43e42aaf06ac56d9c58a509af6e1) then native test setup B
  (oap/parallel-006-native-test-setup-b tip
  181fab4ad0db31acf50c74e48bdff9f1b3ea2c22, implementation
  00e973a79e60bf36b2dc396b872200ece1c8fe24), each forecast clean with
  git merge-tree against the actual parents and the merged trees equal
  to the recomputed forecasts, preserving candidate
  order/report/implementation histories; the strategic 006-b
  round-start bytes (order, active, 006-a root review) were committed
  byte-for-byte unchanged. Adds ONE combined
  tests/integration/test_native_extraction_counts.py journey
  (manifest -> OriginalStore -> line/structure/PDF extraction ->
  Registry -> native_chunking.build with three observed
  counts/receipts per chunk, exact digests/identities, Unicode/table/
  warning/tail/overlap coverage, reciprocal neighbors, deterministic
  rebuild, same-byte distinct IDs and cross-source denial,
  partial_visual_needed, native pair against legacy supplied-512, and
  independent session re-counts) and makes the native tests mandatory
  on both product CI legs via a NEW private pinned hash-verified
  engine-only tokenizers 0.21.4 capsule (DEV only; literal
  SLAIF_NATIVE_TEST_* GITHUB_ENV bindings, helper output never
  sourced). Observed limit: the 1024-call session budget refuses the
  7876-byte procedure source (403 blocks) and the 9269-byte table
  source (243 blocks) at attempted call 1025 before any output, while
  the 938-byte Unicode (765 calls) and 148-byte manual (150 calls)
  complete; the refusal is total and honest, a precise observed bound
  rather than a capacity proof, and no representative large-document
  PASS is claimed from the bounded fixtures. The commissioned isolated
  PAR-006-NATIVE-EFFICIENCY-A correction plus the durable derived
  bundle/loader and the private installed chunk command remain
  required same-PR 006 work before whole-006 acceptance. NOT a GitHub
  PR/default-main merge; contextualization, embedding,
  snapshot/retrieval, GPU/vision, real corpus and model/license/ICA
  qualification all remain open; all real qualification remains
  NOT RUN.
- 006-c (durable record integration; same PR 8 branch): THREE
  authorized local --no-ff merges of the root-reviewed candidate
  tips in the exact ordered index, native query fix A first
  (oap/parallel-006-native-query-fix tip
  0761f6de94cc388ccfd71042986f13d0fa90db4f, implementation
  4f73a38d6b2cc574c91c6320c34dbfb2a4611a84, carrying the accepted
  PAR-006-NATIVE-EFFICIENCY-A/SCALE-C and query correction),
  structured text bundle source A second
  (oap/parallel-006-bundle-source-text tip
  1b05f3647ac3ca83593bc1f1ca2e869ebad4826f, implementation
  026abc91de4bbfc0265a9d1dca4a3f9e9b92fa80, carrying the accepted
  JSONL A / receipt C lanes), derived member store C third
  (oap/parallel-006-derived-member-store-c tip
  f2a2cedc80286cb114ee87db83e674d901fccd74, implementation
  2451dcd081b62b3202fc96ce949a0e4b343bf741), each forecast clean
  with git merge-tree against the actual parents and the merged
  trees equal to the recomputed forecasts, preserving candidate
  order/report/implementation histories; the strategic 006-c
  round-start bytes (order, active, 006-b root review and the
  006-c component index) were committed byte-for-byte unchanged,
  and all accepted source module blobs plus the corrected
  unchanged PDF parser/worker blobs match the root component
  index. The combined counts journey is updated to the current
  bounds: session hard caps 16,384 calls / 32 MB input / 4 MB
  output, 15,000 ms native default builder deadline (legacy
  explicit default 5,000 ms, maximum 15,000 ms), per-build reuse
  with duplicate-free deterministic session call streams, and
  policy definition v2 binding the exact UTF-8 SHA-256 query
  digest (10,000-character query bound kept; equal-count distinct
  queries keep distinct policy IDs; native v1 identity and receipt
  fingerprints unchanged); the stale 1025-attempt negative is
  replaced by actual 7876-byte procedure (403 blocks, 81 chunks,
  1,305 session calls) and 9269-byte table (243 blocks, 25 chunks,
  1,657 session calls) positive journeys at the current caps, a
  standalone Session hard-quota negative (seeded at 16,384 calls;
  next count refuses; owned child reaped), and a tightened full
  interval-union/no-gap block coverage helper. The SAME combined
  test gains the component storage composition: actual structured
  text records -> bundle_source_records.validate +
  bundle_native_records.validate -> opaque immutable
  derived_store container publication (idempotent) -> close ->
  FRESH store in a NEW owned process revalidating against the
  actual OriginalStore, both validators, Registry chunk/neighbor
  re-binding, scope, full coverage union, tail, roles and
  deterministic IDs; corrupted-member and altered-original
  refusals asserted. This foundation slice does NOT implement or
  claim the full typed ingestion bundle loader, PDF semantic value
  composition or the private installed chunk CLI; those remain
  required following 006 work. No numeric 007 or whole-006 merge
  from this slice. NOT a GitHub PR/default-main merge;
  contextualization, embedding, snapshot/retrieval, GPU/vision,
  real corpus and model/license/ICA qualification all remain
  open; all real qualification remains NOT RUN.
- 006-d (final native operator; same PR 8 branch): TWO authorized
  local --no-ff merges of the root-reviewed candidate tips in the
  exact ordered index, derived member store D first
  (oap/parallel-006-derived-member-store-d tip
  b2d274cdf5b652df2fc874c422bd2dd04fa5f058, implementation
  80f0f9d408f26a319d36b71f738f3db76b0a2a49) and final operator C
  second (oap/parallel-006-operator-chunk-cli-c tip
  b3ac81b6eb4d9435272a9535f2987a7742d62d8b, implementation
  2012393e768a0db8c7d3f183287f94a04c6f3f97), each forecast clean with
  git merge-tree against the actual parents, the merged trees equal to
  the recomputed forecasts (first merge head 18d1d6c08ed62bedfb31f9be3087e134e621e956,
  parents 334ef7d9cf2ede5347c5d93986c0ba8ad9e07000 +
  b2d274cdf5b652df2fc874c422bd2dd04fa5f058, tree
  bec0606afd3f53fabd4df74db8472e8249397f9c; second merge head
  065f25a62fadf29020d517bfd750e4c34d845bf4, parents
  18d1d6c08ed62bedfb31f9be3087e134e621e956 +
  b3ac81b6eb4d9435272a9535f2987a7742d62d8b, tree
  c12577b5dcb04478e2a98b96615f365f081dadab), preserving candidate
  order/report/implementation histories; the strategic 006-d
  round-start bytes (order, active, 006-c root review and the 006-d
  component index) were committed byte-for-byte unchanged, and all
  sixteen accepted source blobs plus the unchanged corrected PDF
  parser/worker match the root component index (independently verified
  by the root merge-topology review). Store D fixes the concurrent
  member read: a changed read attempt is discarded and the file is
  reopened and rechecked at most four fresh times within the existing
  deadline; only stable bytes reach the size/hash checks; the original
  root race witness now passes unchanged and the closed-FD, deadline
  and corruption witnesses pass. Operator C adds the complete typed
  text/PDF semantic bundle (ingestion_bundle.validate), the durable
  publisher and verified fresh loader (ingestion_store.publish/load),
  the operator profile (ingestion_profile) and the installed private
  `raggedized chunk` / `chunk inspect` routes (bounded JSON overview,
  exit 0/1/2, `no_native_chunks` + `source_status` partial visual
  truth, known `published_bundle_id` on later failure, idempotent
  canonical retries, cooperative 180-second budget). The root
  reproduced on the merged source a reduced-policy PDF table
  header-relationship loss: a 23-all-text PDF table under a VALID
  reduced policy (target 12 / soft 20 / representation 80 / pair 100 /
  reserve 8) yields eight chunks in which only the first retains the
  actual column header while every source code point, anchor and the
  tail are preserved; this is a header-relationship loss, not dropped
  text, with no default-512 failure claim. The bounded D0 causal
  repair (architecture 9.2/9.3) is isolated in PAR-006-PDF-STRUCTURE-A
  with NO app patch in this round, so whole-006 native coverage stays
  PARTIAL until that reviewed fix integrates in a later 006
  continuation. Focused local checks: 84 derived-store tests passed;
  25 installed CLI/service tests passed under the actual private CPU
  tokenizer and isolated PDF backends; the six combined
  extraction/count integration composition suites (49 cases) passed
  with no skip or fallback. No numeric 007, no whole-006 merge from
  this slice. NOT a GitHub PR/default-main merge; contextualization,
  embedding, snapshot/retrieval, GPU/vision, real corpus and
  model/license/ICA qualification all remain open; all real
  qualification remains NOT RUN.

- 006-e (bounded native PDF structural correction; same PR 8 branch):
  ONE authorized local --no-ff merge of the root-reviewed PDF structure
  correction tip (oap/parallel-006-native-pdf-bridge-c tip
  275335a068e9f62723d344288240b6571f9d4f8e, implementation
  b39317a838f7d6d7500be4efb84a586af5b45205; the tip ancestry already
  includes the reviewed classifier A/B, bridge B and Store D, not
  merged again), forecast clean with git merge-tree against the actual
  round-start parent b2b4f100dea96ba2bf0326d59f51f14730c30261, merged
  tree equal to the forecast 3c2edff8e678fdb6311a6f38656c17ea567f2703
  (merge head 6582845378a57995039ba278d3cf02d024ddcf38, parents
  b2b4f100dea96ba2bf0326d59f51f14730c30261 +
  275335a068e9f62723d344288240b6571f9d4f8e); the strategic 006-e
  round-start bytes (order, active, 006-d root review, 006-e component
  index) were committed byte-for-byte unchanged, and all seventeen
  index source blobs (two changed PDF modules plus new
  pdf_structure.py, unchanged worker 652fcf6) match the root component
  index. The classifier v3 / policy v4 / kind-bound block v2 correction
  repairs the three root-reproduced structural failures (default
  303-block table second header absent; fitting warning body 14 <=
  soft 20 > target 12 separated; closing rule/blank losing the last
  row) on the actual post-merge owned fixtures, every row chunk now
  retaining the original header fragments with full source coverage,
  tail, units and anchors preserved; the unchanged Root terminator and
  admission witnesses and the independent peer boundary witness pass
  on the merged source. NOT a GitHub PR/default-main merge; whole-006
  acceptance, 019 and all real qualification remain open and NOT RUN.
