# OAP Coding Report — 004-a

Identifier: 004-a
Result: COMPLETE
Repository: ulfe-lmi/slaif-raggedized-helper
PR number: 6
Branch: oap/004-qualification-harness
Base branch: main
Implementation head SHA: 17085c03f2ebabc5744fe1a19358e71ff4a6aedd
Report publication commit: SELF

## Work and scope

Executed oap/orders/004-a-trial-runner-and-gateway-direct-composition.md
(Status FINAL, Decision: NONE, live target authorization: NONE, active
004-a, PR mode CREATE_NEW_PR) as the first proof-sized slice of
objective 004 under the explicit D0 replan (authorized real
gateway/GPU/model/corpus inputs remain absent; actual
A1/hardware/quality feasibility remains UNPROVEN and is mandatory at
019/ICA/MVP). Round start reconciled against GitHub: remote main
2bc320ff9e66c874f07da061218f2ff52e3420a9 (PR #5 merged 2026-11-10; the
order base commit), no open PRs, no remote
oap/004-qualification-harness branch, and the worktree on the 003
accepted tree carried exactly the strategic round-start bytes: new
oap/orders/004-a-trial-runner-and-gateway-direct-composition.md,
oap/active 003-j -> 004-a (exactly `004-a\n`), and the untracked
strategic reviews oap/reviews/003-j-review.json (SHA-256
6fb27044b3f6476bae8fd080544f0afc50ca4df2a7d1241fcc82f63451ed1c3f) and
oap/reviews/003-resolution.json (SHA-256
00548c41f27923bbf5981f8e6903eba3309df3277f98dc8defe63ddf2673fe88).
All strategic files were committed byte-for-byte unchanged inside the
single implementation commit
17085c03f2ebabc5744fe1a19358e71ff4a6aedd (24 files, +4128/-38) on the
new branch oap/004-qualification-harness from verified main 2bc320f;
the order file itself, oap/active and both 003 reviews are part of
that commit unchanged. No reset/clean/stash/force-push was used.

Changed behavior/paths:

- NEW `src/slaif_raggedized_helper/qualification/` — the finite
  qualification trial runner: `spec.py` (strict bounded frozen
  TrialSpec/TrialBudgets: repeated-parent + annotation + concurrency 1
  only; declared code/backend/model/profile/purpose identities and
  exact workload/seed fingerprints verified pre-dispatch;
  unimplemented context/pair/batch/precision/seed_variation/
  concurrency_policy controls refuse with named 004-b prerequisites;
  bool-as-number, nonfinite/negative/out-of-bounds and unknown
  settings refused), `runner.py` (preflight_issues, offline
  zero-I/O plan_trial, and run_trial which actually invokes the
  current GatewayGenerator/DirectNativeGenerator application adapters
  through the REAL transport under ONE absolute trial deadline and ONE
  shared dispatch admission allowance spanning all warmups,
  repetitions, retries, template and model calls — the reused 003
  shared-budget seam `probes.BudgetedTransport`, enforced at the
  transport dispatch boundary including failed connects, with exact
  sample-start minimums of 1 gateway / 2 direct calls so no sample is
  half-dispatched; safe fingerprint-only per-trial/per-phase
  observations, reported-only usage with unknown staying null,
  contradictory cache/input accounting as raw facts only, no
  prompt/response/credential/private-URL leakage), `analysis.py`
  (pure deterministic nearest-rank min/p50/p95/max over
  terminal-outcome samples only, per warmup/measured group;
  zero-sample all-null; no qualifying pass from synthetic or
  configured-unverified evidence), `gates.py` (the machine-readable
  projection of every architecture section 23.2 ID) and
  `synthetic.py` (the owned deterministic loopback fixture for the
  explicit `--synthetic` route; configured secrets never read).
- MODIFIED `src/slaif_raggedized_helper/cli.py` — explicit
  `raggedized qualification gates|plan|run` subcommands (gates/plan
  offline with zero model/HTTP/telemetry I/O; run explicit opt-in;
  exit 0 complete execution status / 1 not-run-incomplete / 2
  pre-dispatch refusal with zero dispatches / 3 honest post-work
  evidence export failure with the full safe document and spent-
  attempt ledger on stdout). Existing probe/doctor/help behavior
  preserved.
- NEW `docs/benchmarks/qualification-gates.json` — the committed
  canonical rendering of the gate projection (bound to the code by a
  unit test): all 14 section 23.2 IDs (GATEWAY-01/02/03, DIRECT-01,
  V100-MEM-01/02, RERANK-01, EMBED-01/02, ONLINE-01/02, OPS-01/02,
  LICENSE-01), all real trials NOT_RUN, live target authorization
  NONE, only GATEWAY-01/GATEWAY-03/DIRECT-01 executable in this
  slice.
- NEW `docs/benchmarks/qualification-protocol.md` — exact CLI
  commands, spec field table, budget admission/accounting semantics,
  nearest-rank quantile definition, declared/observed/
  supplied-unverified/MOCK evidence classes, finite runner behavior,
  unsupported workload settings, and the 004 replan with remaining
  prerequisites.
- NEW tests: `tests/unit/test_qualification.py` (67 tests) and
  `tests/integration/test_qualification_composition.py` (23 tests,
  installed-CLI subprocess + owned 127.0.0.1 loopback servers).
- The one ordered operational correction: `oap/prompts/
  coding-startup.txt` replaced with the exact bytes of
  /home/janezp/codex-supervision/slaif-raggedized-helper/drafts/
  coding-startup-bounded-goal.txt (SHA-256
  6d2323bb832e5f78e4cd86d6951c04c0b3975dc80730c473fc7834820965a98e,
  verified byte-identical in the worktree and measured in the
  manifest), with docs/AGENT-ROLE-SETUP.md, docs/OAP-RUNBOOK.md and
  the oap/governance/MANIFEST.json measurements for that file and
  TESTING.md updated in the same commit. The new /goal-first
  startup is NOT operationally validated by file hash alone; strategy
  qualifies it during the same-objective 004-b fresh control handoff.
  No helper/global client/model/profile/auth change accompanies it.
- Updated docs: README.md, STATUS.md, TESTING.md (new T08),
  docs/CI.md, docs/UNCERTAINTIES.md.

No new runtime dependency (uv.lock/pyproject unchanged); no live
model requests; no telemetry or GPU probing; no merge, no auto-merge,
no tag/deploy; no 004-b or any next work authored, chosen or started.

## Acceptance evidence

Criterion 1 (strict finite spec/sample/result models, refuse before
dispatch): `qualification/spec.py` is bounded/frozen/extra-forbid with
explicit finite bounds on every field; `trial_workload_fingerprint`
recomputes the exact declared workload and mismatches refuse (never
re-bind). Proof: tests/unit/test_qualification.py::TestTrialSpec
Strictness (unknown field, unsupported-control named-prerequisite
refusals, workload/purpose/concurrency, bool-as-number at every
numeric field, nonfinite/invalid deadline, out-of-bounds values,
fingerprint format/mismatch, frozen spec, per-sample reservation) and
::TestPreflight (code_version, workload fingerprint, unknown profile,
missing route, declared model, output allowance, unmaterialized
direct, template build mismatch); installed-CLI zero-dispatch proofs:
tests/integration/test_qualification_composition.py::
test_trial_preflight_model_mismatch_zero_dispatch,
::test_trial_preflight_fingerprint_mismatch_zero_dispatch,
::test_trial_missing_route_gives_exact_not_run,
::test_trial_direct_mode_refused_when_gateway_only,
::test_trial_invalid_spec_refused_zero_dispatch.

Criterion 2 (real gateway/direct composition; one absolute deadline +
one shared allowance at the real transport boundary, never reset per
probe; deadline/cancellation stops new work, closes/joins owned
in-flight work, never kills upstream): `run_trial` builds the REAL
GatewayGenerator/DirectNativeGenerator over the real GatewayTransport
wrapped by the reused 003 `probes.BudgetedTransport` (deadline
recheck + allowance reservation before every `post_json`, including
failed connects; ambiguous post-dispatch work spent, never replayed).
Proof: tests/integration/test_qualification_composition.py::
test_gateway_trial_happy_path_shared_allowance (exact /v1/responses
count across warmups+repetitions),
::test_gateway_trial_dispatch_allowance_shared_across_warmups_reps,
::test_gateway_trial_retries_consume_shared_allowance (failed
connects consume the SHARED allowance; sample 1 never starts),
::test_gateway_trial_deadline_exhausted_mid_trial_no_replay (one
in-flight exchange closed at the deadline, unknown completion, zero
re-dispatch, honest elapsed bound),
::test_gateway_trial_accepted_then_closed_unknown_not_replayed
(accepted-then-closed stays unknown, no replay),
::test_direct_trial_happy_path_template_work_counts (native
template+completion wire order; template work counts),
::test_direct_trial_budget3_native_boundary (template calls count:
budget 3 -> exactly one complete native sample, stop with
remaining=1, no half-dispatched sample) and
::test_direct_trial_budget4_native_boundary_full (budget 4 -> exactly
two native samples, remaining=0).

Criterion 3 (safe raw observations; warmups separate from measured;
first/repeated order separate from cold/warm physical state; native
template time is not TTFT; reported cached tokens are not
evaluated-prefill; no leakage): `_sample_record` carries ordinal,
phase, first_repetition, `physical_state: unknown`, input/output
fingerprints only, per-sample declared backend fingerprint,
reported-only usage/timings; `_cache_input_consistency` preserves
contradictory cache/input counters as raw facts only. Proof: the
direct happy-path test asserts `ttft_seconds is None`,
`prefill_seconds == 0.02` (the dialect's reported prompt phase),
warmups/measured separation in the analysis;
tests/integration/test_qualification_composition.py::
test_trial_contradictory_cache_counters_are_raw_facts_only and
::test_trial_missing_usage_stays_null;
::test_provider_error_canary_never_reaches_evidence (provider error
body stays out of evidence); unit analysis tests assert failed/
unknown/refusal/incomplete/invalid observations never enter latency.

Criterion 4 (reproducible latency analysis; failed/incomplete/
unknown/zero-sample cannot produce a qualifying pass; complete/
exit-0 is execution status, not success): `analyze_trial` is a pure
deterministic function; nearest-rank quantiles (rank = ceil(p/100*n),
1-based, clamped) over finite non-negative caller-wall terminal
samples only; zero-sample groups n=0 all-null; `qualifying_pass` is
always impossible in this slice with the exact reason
(no_terminal_samples / evidence_not_qualified). Proof:
tests/unit/test_qualification.py::TestAnalysis (quantile convention,
zero-sample nulls, failed/unknown exclusion, warmup/measured
separation, purity/determinism); installed-CLI proofs:
::test_gateway_trial_accepted_then_closed_unknown_not_replayed
(exit 0 with status complete containing an unknown_completion
sample — execution status, not success or qualification) while
::test_gateway_trial_retries_consume_shared_allowance and the
deadline/budget-boundary tests show exit 1/incomplete with the
exact stop_reason.

Criterion 5 (installed CLI zero-I/O planning/help; explicit opt-in
execution; deterministic explicit synthetic route; configured URL
never synthetic; existing behavior preserved; honest post-work
export error): import/`--help`/`doctor`/`qualification
gates`/`qualification plan` perform zero model/HTTP/telemetry I/O.
Proof: tests/integration/test_qualification_composition.py::
test_plan_and_gates_are_zero_io_on_closed_port (port closed, zero
I/O), ::test_plan_rejection_is_honest_and_offline; the `--synthetic`
route starts the owned fixture and labels evidence MOCK /
`synthetic-owned-fixture` (configured secrets never read; constant
fixture endpoint identity for cross-run determinism):
::test_synthetic_trial_deterministic_mock_route and
::test_synthetic_direct_trial_deterministic_mock_route (timing-
stripped evidence byte-identical across two runs);
::test_configured_loopback_url_never_synthetic (a configured
loopback URL stays `target_type: unverified` /
`evidence_class: CONFIGURED_UNVERIFIED`);
::test_trial_invalid_output_dir_refused_before_dispatch and
::test_trial_late_output_write_failure_is_honest_post_work_stage
(exit 3 after actual dispatches, full safe evidence + spent-attempt
ledger on stdout).

Criterion 6 (machine-readable prerequisite projection covering all
section 23.2 IDs; only text/repeated-parent entrypoints executable;
real trials NOT_RUN; no positive claim): `qualification/gates.py`
covers exactly the 14 order-listed IDs with per-gate experiment,
executable flag, NOT_RUN status and named pending prerequisites;
committed `docs/benchmarks/qualification-gates.json` is the canonical
rendering. Proof: tests/unit/test_qualification.py::TestGates
(all IDs present, executable set exactly {GATEWAY-01, GATEWAY-03,
DIRECT-01}, LICENSE-01 names the open certifi question, deterministic
bytes, committed document == canonical bytes).

Criterion 7 (meaningful owned-HTTP gateway/direct composition +
installed-CLI tests; 003/OAP/lint/governance regressions preserved;
exact bounded-goal prompt and docs/manifest updated): the 23-test
installed-CLI composition suite (listed under criteria 1-5) runs the
INSTALLED `raggedized` CLI in subprocesses against owned loopback
servers with unique synthetic canaries, observing real total calls
across warmups/repetitions (both dialects), the budget-3/budget-4
native boundaries, one shared allowance, retries at the real
transport boundary, deadline/cancellation, preflight zero-dispatch,
metric ambiguity and deterministic summaries. Regressions: full
product suites green (238 unit = 171 prior + 67 new; 294
integration = 271 prior + 23 new), OAP scaffold 41 tests OK, ruff
clean, `oap/bin/check_state.py` exit 0 (active 004-a;
activation_matches_current_governance is informationally False
because the ordered manifest measurement change legitimately
postdates the activation, as check_state's own source_note
describes), and CI at the implementation head green (below). The
bounded-goal prompt replacement and its docs/manifest measurements
are committed as ordered; its operational qualification remains
explicitly pending strategy's 004-b handoff.

## Verification

Local commands at the implementation worktree (before commit), all
run from /home/janezp/codex-work/slaif-raggedized-helper:

- `uv run ruff check src tests/unit tests/integration` -> All checks
  passed! (exit 0)
- `uv run pytest tests/unit` -> 238 passed (171 baseline + 67 new)
- `uv run pytest tests/integration` -> 294 passed in ~163 s (271
  baseline + 23 new)
- `python3 -m unittest discover -s tests/oap` -> Ran 41 tests, OK
- `python3 oap/bin/check_state.py --repo-root .` -> exit 0, state
  ACTIVE, active 004-a, order path present, no report yet
- CLI smoke: `uv run raggedized --help` exit 0; `raggedized
  qualification gates` renders the 14-ID projection with real_trials
  NOT_RUN; `plan`/`run` exercised through the installed-CLI
  integration suite above (including closed-port zero-I/O and the
  deterministic synthetic route across two runs).

CI already observed at the implementation head (run 42829357444,
headSha 17085c03f2ebabc5744fe1a19358e71ff4a6aedd, conclusion
success, workflow CI): OAP tests (Python 3.12) pass, OAP tests
(Python 3.13) pass, OAP tests (Python 3.14) pass, Product tests
(Python 3.12) pass, Product tests (Python 3.14) pass. PR #6 head
17085c0, base main, MERGEABLE, no auto-merge configured; no other
required checks exist on the live policy at that head. This report
does NOT claim anything about the future push/CI of the report
commit itself; the separate post-publication receipt and strategic
review record those facts.

Mock/live distinction: everything above is synthetic/offline —
owned 127.0.0.1 loopback servers, unique synthetic canary keys, no
external network, no product services, no real keys, no GPU, no model
downloads. Live target authorization: NONE; no live model/hardware
trial was executed and none could be (no approved URL/model/
secretref/GPU/corpus). Mock success is not real qualification; all
real qualification gates and LICENSE-01 remain open and NOT RUN.

## Documentation impact

- NEW docs/benchmarks/qualification-protocol.md: the exact supported
  CLI commands, spec field table, budget admission/accounting
  semantics (one absolute deadline, one shared allowance, per-sample
  output reservation, ambiguous-work accounting), the nearest-rank
  quantile definition, the wall-time boundary (caller wall time is
  not model work; native template time is not TTFT; missing prefill
  stays null), the evidence classes (declared/observed/
  supplied-unverified/MOCK), finite runner behavior and unsupported
  workload settings, unknown physical cache state, the 004 replan and
  remaining 004-b/019/ICA prerequisites.
- NEW docs/benchmarks/qualification-gates.json: machine-readable
  section 23.2 prerequisite projection (all real trials NOT_RUN;
  no positive claim).
- TESTING.md: new T08 entry describing the 004-a test suite exactly.
- README.md: 004-a slice and `qualification` command documented;
  quickstart and public CLI surface updated.
- STATUS.md: current state moved to 004-a/PR #6; full 004-a history
  entry; 003 recorded as accepted/merged (PR #5, 2bc320f).
- docs/CI.md: product job now covers the 003-h/i/j probe and 004-a
  trial composition suites; NOT RUN / pending language kept honest.
- docs/UNCERTAINTIES.md: 004-a observation (U01/U02 stay open:
  runtime/GGUF/tokenizer identities unverified/unavailable and
  target provenance unverified; U03/U04/U05/U08 unchanged; U10 open
  for the startup-prompt operational qualification).
- docs/AGENT-ROLE-SETUP.md and docs/OAP-RUNBOOK.md: the ordered
  /goal-first bounded-goal startup correction, with the explicit
  caveat that it is NOT operationally validated by file hash alone
  (strategy qualifies it during the 004-b fresh control handoff; no
  self-triggering).
- oap/governance/MANIFEST.json: measurements updated for
  oap/prompts/coding-startup.txt and TESTING.md (the only
  manifest-tracked files changed this round); all other manifest
  entries untouched and verified by check_state.
- No earlier report/order/review bytes were edited; immutable
  historical claims unchanged.

## DHA and boundaries

Decision: NONE (as ordered); no APPEND CRIT-* was ordered and no
candidate critical entry was appended. No D1/D2 action taken.
Preserved resources: Qwen3.8-27B/A100 Q8/xhigh model/profile
settings, existing services, agent homes, real credentials and FIFOs
untouched; no live model requests, downloads, service/process/GPU
changes, GPU/telemetry probing or network exposure beyond owned
loopback and GitHub CI/publication; the consumed control/response
FIFOs were never read; no second waiter started. No merge performed
and no auto-merge requested; whole-004 acceptance, 004-b activation
and 005 selection remain strategy alone. Unrelated worktree state
preserved; the strategic 003 reviews, the 004 order and oap/active
are committed byte-for-byte as found (hashes re-verified in the
worktree before commit: 003-j-review.json 6fb27044..., 003-
resolution.json 00548c41..., oap/active exactly `004-a\n`).

## Limitations and remaining work

- The 004-a slice is instrumentation + prerequisite projection only:
  004-b (strategic activation required) adds resource telemetry,
  parity analysis and full named gate composition; 019/ICA/MVP gate
  actual A1/hardware/quality feasibility. No whole-004 acceptance,
  merge or readiness claim is made or implied.
- Live target authorization: NONE — no approved actual URL/model/
  secretref/GPU ownership/corpus reply has arrived; ALL real trials
  persist NOT_RUN, and no positive topology, cache, speedup, quality,
  VRAM, license or readiness claim follows from this software or from
  any synthetic/configured-unverified evidence.
- LICENSE-01 remains open: the certifi (MPL-2.0) policy exception has
  not been granted (018 owns the full dependency/model/renderer
  inventory).
- The /goal-first bounded-goal startup prompt is a committed file
  correction only; it is NOT operationally validated by file hash
  alone — strategy qualifies it during the same-objective 004-b fresh
  control handoff, before final 004 acceptance. No self-triggering
  was performed.
- Unavailable physical identities (deployed runtime/GGUF, tokenizer,
  GPU state) remain unverified/unavailable on this host by design;
  physical cold/warm cache state stays unknown without cache
  reset/isolation evidence; the trial sends no cache-key/slot
  control (no assumed slot reuse).
- No failures, skips or blocked tests at the implementation head;
  the only deviation from the handoff state was a corrupted SHA-256
  digest in the new UNCERTAINTIES 004-a entry (a 60-char truncation
  of the prompt file digest), corrected to the exact 64-hex digest
  before the implementation commit. No scope deviations otherwise;
  the implementation stayed within the ordered allowed paths with no
  new runtime dependency.
