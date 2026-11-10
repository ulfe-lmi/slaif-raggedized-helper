# OAP Coding Report — 003-h

Identifier: 003-h
Result: COMPLETE
Repository: ulfe-lmi/slaif-raggedized-helper
PR number: 5
Branch: oap/003-generator-adapters-and-cache-probes
Base branch: main
Implementation head SHA: e91e737592deccbbb4dfdcd6ab411a21aae0a776
Report publication commit: SELF

## Work and scope

Executed oap/orders/003-h-bounded-probes-and-objective-closure.md (Status
FINAL, active 003-h, PR mode AMEND_EXISTING_PR) on the existing unique 003
objective PR #5, branch oap/003-generator-adapters-and-cache-probes from
verified base main 93b43177f4dcd0b28ef2c5ed33a049f83217f152. At round start
the remote head 883f1cb0587d242a9c675f94e7a5891833342f79 was the published
003-g report SELF (sole implementation parent
29fb8b9686fc0be9f920e7c05fbe72dd86e5f2d3; PR #5 OPEN/MERGEABLE;
implementation CI 42785261938 and final CI 42785852083 all 5 SUCCESS), and
the worktree carried exactly the strategic round-start bytes: modified
oap/active (003-g -> 003-h), new
oap/orders/003-h-bounded-probes-and-objective-closure.md and new
oap/reviews/003-g-review.json. Exactly one implementation commit was
pushed before this report:

- e91e737592deccbbb4dfdcd6ab411a21aae0a776 (implementation head, 16 files,
  +2575/-30): the bounded repeated-parent qualification probe module and
  CLI, its unit and installed-CLI owned-loopback composition suites, the
  documented gateway minimum-capability admission repair, the
  docs/README/TESTING/STATUS/UNCERTAINTIES updates and the refreshed
  governance measurements, plus the exact strategic 003-h activation bytes
  and the unchanged pre-published 003-g review (oap/reviews/003-g-review.
  json committed byte-for-byte as found in the worktree).

Changed behavior:

1. Gateway minimum-capability admission repair (003-a criterion 1;
   strategic audit 003-gateway-capability-admission-review): in
   src/slaif_raggedized_helper/model_clients/gateway.py (GatewayGenerator.
   _preflight, +11 lines) the explicit minimum requirements are now
   honored independently of the actual format/cache-key fields. A
   constructor-validated request may REQUIRE JSON_MODE or PROMPT_CACHING
   while sending no response_format or prompt_cache_key at all; an
   unqualified requirement refuses locally before dispatch (zero HTTP) —
   "structured output refused: route does not advertise json_mode" /
   "prompt caching refused: route does not advertise prompt_caching" —
   because a model capability declaration alone is not route support. A
   qualified requirement alone does not invent an output format or cache
   key (the pinned minimal envelope is sent unchanged). The actual
   format/cache-key gates, the streaming/vision gates and the wire/parser
   are unchanged (no broader redesign).

2. Bounded repeated-parent qualification probe (003-a criterion 5): new
   src/slaif_raggedized_helper/probes.py (680 lines) plus the
   `raggedized probe` CLI subcommand in src/slaif_raggedized_helper/cli.py
   (lazy import keeps import/--help/doctor lightweight and network-free).
   Explicit opt-in only: import, --help, doctor, readiness and default
   tests never dispatch a probe; only the probe subcommand with explicit
   finite budgets and an actually configured gateway/direct mode does, and
   neither mode falls back to the other after a denial. The experiment
   uses one constant bounded synthetic parent and two explicit
   deterministic child suffixes; phases are labeled first-call/
   second-call with cold_state unknown (no cache reset/isolation was
   authorized). ONE overall experiment deadline spans both paired
   requests, native template work and every adapter retry (a per-call
   allowance never resets it). The dispatch allowance is reserved BEFORE
   every transport invocation (model dispatch, template work, failed
   connects); conservatively counted ambiguous dispatched work is spent
   and never replayed; retries and template requests cannot bypass the
   budget. The output-token allowance is bounded across the pair (>= 2;
   each request receives the deterministic even half total//2).
   BudgetedTransport wraps the REAL transport and records model dispatch
   vs template work, known vs ambiguous vs pre-dispatch failures.
   Credentials resolve only through the configured safe operator
   reference (secrets env/file kind); the value never appears on the
   command line, in reports, errors or logs, and an absent reference
   refuses before dispatch (exit 2). The safe evidence document carries
   declared-unverified identities, an opaque endpoint digest (never a
   URL), char counts + sha256 fingerprints (never raw material),
   digest-only expected-output checks, and cache conclusions driven
   solely by reported evaluated metrics (no_cache_control /
   metrics_unavailable / no_cache_hit_reported / cache_hit_reported /
   not_run); it is live: false and model_quality: not_assessed. Exit
   codes: 0 complete / 1 explicit not-run-incomplete with published
   evidence / 2 usage-config error with zero dispatch.

## Acceptance evidence

003-h criteria, with concrete code/test proof (paths under tests/):

1. Explicit opt-in, actually configured mode, safe credentials,
   minimum-capability admission: unit/test_probes.py
   test_cli_probe_requires_explicit_opt_in_and_budgets,
   test_cli_probe_invalid_config_refuses_with_exit_2,
   test_gateway_mode_not_configured_refuses_before_any_transport,
   test_direct_mode_not_materialized_refuses_with_the_specific_gap,
   test_gateway_credential_reference_absent_refuses_before_dispatch;
   integration/test_probe_composition.py test_doctor_help_and_missing_
   optin_never_dispatch (import/--help/doctor observed against a live
   loopback recorder: zero requests) plus the three import-hygiene unit
   regressions; test_direct_mode_refused_when_gateway_only_config
   (no cross-mode fallback; direct stays offline-only under the native
   round's trusted/template gates). Gateway minimums:
   integration/test_gateway_generator.py test_unsupported_controls_
   refused_before_dispatch gained the two unqualified zero-HTTP cases
   (required JSON_MODE-only and PROMPT_CACHING-only against a default-
   false route: FAILED, "refused", zero requests) and the qualified
   minimum-only positive controls test_required_json_mode_qualified_
   dispatches_without_invented_format / test_required_prompt_caching_
   qualified_dispatches_without_invented_key (exactly one POST each; no
   text.format / no prompt_cache_key invented); the ordinary
   TEXT/no-format envelope regression is retained.
2. Finite budgets validated before dispatch; one deadline; reservation
   before every transport invocation; ambiguous work spent, never
   replayed; pair-bounded output: unit test_budgets_refuse_nonfinite_or_
   nonpositive, test_budgets_split_the_pair_evenly_and_never_exceed_the_
   total, test_gateway_output_reserve_refusal_stops_with_no_transport_
   calls, test_direct_operator_limit_refusal_stops_with_no_transport_
   calls, test_direct_dispatch_allowance_exhausted_mid_pair,
   test_gateway_retry_budget_is_consumed_at_the_boundary, test_retry_
   that_exhausts_the_total_budget_never_dispatches_beyond, test_deadline_
   exhausted_between_phases_stops_without_dispatch, test_boundary_refuses_
   when_deadline_passes_mid_experiment, test_boundary_reserves_before_
   every_call_including_failed_connects, test_unknown_completion_counts_
   spent_and_never_replays; through the real transport boundary with the
   installed CLI (owned loopback): test_gateway_probe_dispatch_allowance_
   exhausted_across_pair, test_gateway_probe_deadline_exhausted_during_
   first_call, test_gateway_probe_unknown_completion_is_never_replayed,
   test_direct_probe_budget_exhaustion_with_retry_at_closed_port,
   test_direct_probe_ambiguous_completion_spent_not_replayed,
   test_invalid_config_refuses_before_dispatch. Insufficient budget
   yields explicit not-run/incomplete evidence (status + stop_reason,
   exit 1) with no extra generation. GeneratorResult.attempts is NOT
   used as an authoritative dispatch count: counts come from the
   BudgetedTransport boundary (transport_boundary block in the evidence).
3. Repeated-parent construction and identities: unit test_cache_evidence_
   no_control_by_default, test_gateway_qualified_cache_control_sends_key_
   but_stays_unqualified (key sent; conclusion stays unqualified without
   reported metrics), test_native_cache_metrics_reported_param,
   test_expected_output_check_match_mismatch_not_provided; integration
   test_gateway_probe_happy_path_with_credential_reference and
   test_direct_probe_happy_path_exact_order_and_envelopes (exact request
   count/order/control payloads; constant parent + deterministic suffixes
   recorded as char counts + fingerprints; first-call/second-call labels,
   cold_state unknown; no cache isolation asserted).
4. Safe structured evidence: unit test_evidence_carries_no_url_secret_
   prompt_or_response_text (no endpoint URL, credential value, raw
   prompt/response text or provider error enters the document),
   test_native_cache_metrics_reported_param (missing/invalid measured
   values -> unqualified conclusion, never a synthetic zero or claimed
   cache success), test_expected_output_check_match_mismatch_not_
   provided (digest-only equality); integration test_gateway_probe_
   missing_metrics_stay_null (the gateway dialect never reports
   prefill -> null + metrics_unavailable) and
   test_provider_error_canary_never_reaches_evidence.
5. Output correctness explicitly limited: the evidence is live: false
   and model_quality: not_assessed; terminal validity is recorded per
   request separately from semantic quality; expected-output checks are
   operator-supplied sha256 digest equality only (equal answers do not
   establish truth; speed does not establish caching; a mock does not
   qualify actual behavior); arbitrary response text never enters the
   evidence (fingerprints/digests only); all real trials remain NOT RUN
   (order live authorization: NONE).
6. Installed-CLI composition and regressions: tests/integration/
   test_probe_composition.py (15 tests) exercises the INSTALLED
   `raggedized` CLI in subprocesses with the real gateway and native
   adapters against owned 127.0.0.1 loopback servers — exact request
   count/order/control payloads, budget exhaustion across the pair and
   retries, no implicit dispatch, missing metrics, mismatched outputs,
   unknown-completion no-replay, safe canaries, invalid config before
   dispatch. All prior regressions, lint, governance and the CI matrix
   pass (see Verification).
7. Original 003-a criteria 1-6 and final b/c/d/e/f/g contract review
   (concise evidence table; actual references, not counts alone):

   | 003-a criterion | Status at e91e737 | Evidence |
   |---|---|---|
   | 1 Gateway adapter: configured route/model + secret reference, bounded serialization, explicit capability gating incl. explicit minimums, no native cache_prompt/id_slot leak, safe errors | met; 003-h closes the demonstrated minimum-admission defect | 129 gateway loopback tests; test_unsupported_controls_refused_before_dispatch (+2 zero-HTTP cases); the two qualified minimum-only positive controls; preflight-only change, no wire/parser redesign |
   | 2 Terminal/SSE parsing: supported text items in order; refusal/incomplete/failed/duplicate/EOF-never-COMPLETE; split-coalesced frames, UTF-8, bounds, cancellation cleanup | met (003-b/c/d); unchanged by 003-h | 129 gateway tests (SSE vectors, terminal handling) green at e91e737 |
   | 3 Direct adapter: explicit offline/diagnostic policy, private trusted destination, online purpose refused before network work, tested cache/slot controls | met (003-e/f/g); 003-h exercises the real native adapter via the probe | test_direct_probe_happy_path_exact_order_and_envelopes; test_direct_probe_qualified_cache_control_reaches_the_wire; 83 native tests + online-refusal regressions green |
   | 4 Finite deadlines, bounded sizes, no auth/schema/permission retries, pre-dispatch vs ambiguous distinction, no costly unknown-completion replay | met (003-b/c/d/g); 003-h enforces it across the whole experiment at the real transport boundary | test_deadline_exhausted_between_phases_stops_without_dispatch; test_boundary_reserves_before_every_call_including_failed_connects; test_unknown_completion_counts_spent_and_never_replays; the deadline/budget/no-replay integration tests above |
   | 5 Qualification command: explicit opt-in, finite request/time/token budgets and model/runtime identity, safe GATEWAY/DIRECT evidence; repeated-parent first-call/second-call with reported-metric-only cache conclusions; no probe on import/doctor/help/readiness/default tests | met (003-h; the remaining 003-a software gap) | src/slaif_raggedized_helper/probes.py + `raggedized probe`; criteria 1-5 test references above; test_doctor_help_and_missing_optin_never_dispatch |
   | 6 Controlled local HTTP integration: exact envelopes, canaries, refusals, no redirects, bounded retries, cleanup; public config/contracts compatible; CI passes; real trials unrun | met; 003-h adds 15 installed-CLI composition tests | test_probe_composition.py (15); 419 product tests green; 41 OAP; CI run 42795740359 all 5 jobs SUCCESS |

   The final b/c/d/e/f/g contracts are unchanged at e91e737 and remain
   proven by their retained green regressions (129 gateway + 33 transport
   + 83 native integration, 159 unit) and their immutable round reports
   (oap/reports/003-b…003-g); no contract field changed and no schema
   file changed in the implementation commit.

## Verification

Exact commands at the implementation head
e91e737592deccbbb4dfdcd6ab411a21aae0a776 (all local, synthetic, offline;
no live model, download, credentials, GPU or corpus):

- uv sync --locked — exit 0.
- uv run pytest tests/unit -q — 159 passed, exit 0 (15 cli-doctor + 48
  config + 14 contracts + 3 import-hygiene + 11 model-lock + 44 native-
  mapping + 24 probes).
- uv run pytest tests/integration -q — 260 passed, exit 0 (129 gateway +
  33 transport + 83 native + 15 probe composition).
- python3 -m unittest discover -s tests/oap — Ran 41 tests, OK.
- uv run ruff check src tests/unit tests/integration — All checks passed.
- python3 oap/bin/check_state.py --repo-root . — state ACTIVE, active
  003-h, exit 0; activation_matches_current_governance=false is the
  expected post-refresh state for the in-scope manifest pin update (the
  immutable order bytes were not rewritten).

Test-count record per the order: baseline 376 product (241 integration:
125 gateway + 33 transport + 83 native; 135 unit) plus separate 41 OAP.
Actual at the implementation head: 419 product (260 integration: 129
gateway + 33 transport + 83 native + 15 probe composition; 159 unit) =
+43 (+4 gateway admission, +15 probe composition, +24 probe unit), plus
the separate 41-test OAP suite unchanged.

CI (GitHub Actions, clean locked checkout):
- Implementation head e91e737592deccbbb4dfdcd6ab411a21aae0a776: run
  42795740359 (headSha e91e737…, status completed, conclusion success,
  created 2026-11-10T10:02:32Z), all 5 jobs SUCCESS — Product tests
  Python 3.12 and 3.14; OAP tests Python 3.12, 3.13, 3.14.
- Round-start heads remain green in history (cited as historical only):
  883f1cb0587d242a9c675f94e7a5891833342f79 run 42785852083 and
  29fb8b9686fc0be9f920e7c05fbe72dd86e5f2d3 run 42785261938, each all 5
  SUCCESS.

Mock/live distinction: every network fact above is owned 127.0.0.1
loopback fixtures with synthetic qualifications and canaries, plus
pinned-dialect fixtures and GitHub CI from a clean checkout. No live
model/route request, no real upstream key, no gateway access, no GPU or
service control was performed (order live authorization: NONE).

This report cannot certify its own future push or checks on the
report-publication head; the CI facts recorded above are for the
implementation head only, and the post-publication state is recorded by
the separate receipt/strategic review.

## Documentation impact

- docs/generator-contract.md: the capability-gate section now states that
  the default-deny gates honor BOTH the actual input shape and the
  explicit minimum requirement (JSON_MODE/PROMPT_CACHING in
  required_capabilities, which a valid request may carry with no
  format/key field), that an unqualified minimum refuses at zero HTTP
  and that a qualified minimum alone does not invent a format or key; a
  new "Bounded qualification probe (003-h)" section documents the exact
  public CLI contract (arguments, one-deadline and reserve-before-
  invocation budget semantics, exit codes, safe credential reference,
  safe evidence document with opaque endpoint digest, fingerprints,
  digest-only checks and reported-metric-only cache conclusions,
  first-call/second-call with cold state unknown), with Proven /
  NOT-RUN updated.
- README.md: the CLI overview lists `raggedized probe` (explicit opt-in,
  exit codes 0/1/2; import/help/doctor never dispatch) and points to
  docs/foundation.md and docs/generator-contract.md.
- TESTING.md: new T07 (bounded probe composition) with the exact command
  and its synthetic/offline boundaries.
- STATUS.md: 003-h round entry (probe/CLI composition, gateway minimum-
  admission repair, live/hardware NOT RUN retained) and active objective
  003-h on PR #5.
- docs/UNCERTAINTIES.md: 003-h observation — U05 (gateway/direct prefix
  reuse) remains OPEN: no live prefix-reuse, cache-hit or speedup
  observation exists and the probe's cache conclusion is driven solely by
  reported evaluated metrics of the second phase, staying unqualified
  whenever they are absent (the gateway dialect never reports
  prefill/cache metrics); U01 narrowed further (the gateway explicit-
  minimum capability admission is enforced and regression-tested over
  real loopback HTTP; wire-level admission at the pinned contract
  revision, not live compatibility proof); U02-U4 and U06-U11 unchanged;
  the certifi (MPL-2.0) policy gate remains an open human question.
- Governance: oap/governance/CONTEXT-BUDGET.md table refreshed to the
  actual final bytes (TESTING.md 4934; declared routine project
  governance 37485 UTF-8 bytes, ceiling 50000) together with the
  oap/governance/MANIFEST.json pins for TESTING.md and CONTEXT-BUDGET.
  md (all other pins unchanged; check_state verifies every manifest
  hash). No dependency, schema, command, performance, license clearance
  or readiness is claimed beyond what was executed; the config/schema
  JSON exports are unchanged (no contract field changed).

## DHA and boundaries

The order declares Decision: NONE; no critical append was performed or
needed; CRITICAL.md untouched. Preserved: all prior gateway/transport/
native behavior and their regressions (129 + 33 + 83), the accepted
003-e/f/g metric meanings and oracles, the original native vectors and
positive controls, all prior immutable reports/orders/reviews, the exact
strategic 003-h order/active bytes (committed unchanged), the unchanged
pre-published 003-g review (oap/reviews/003-g-review.json committed
byte-for-byte), model/provider/profile, private state, deadline/
cancellation behavior and original sources. No merge, auto-merge, tag,
release or deploy; PR #5 remains the single 003 objective PR (amended);
no next work selected; no numeric advance; no competing control reader
started (the sole external wrapper consumed the notification before
fresh startup); exactly one response OK is signaled after this report's
verified publication.

## Limitations and remaining work

- Live qualification is NOT RUN: no live model/route/service
  authorization exists (order: NONE); all probe evidence is synthetic
  owned-loopback HTTP plus pinned-dialect fixtures. No cache-hit,
  speedup or prefix-reuse observation exists (U05 OPEN); the probe's
  cache conclusion is driven solely by reported evaluated metrics and
  stays unqualified whenever they are absent (the gateway dialect never
  reports prefill/cache metrics).
- The pinned native reference (ggml-org/llama.cpp tools/server, commit
  3b4d6ab3f79651935fba1dd93732f29022a7f5f5) is a dialect reference, not
  the unknown deployed build; json_grammar_tested remains default deny
  until an actually tested serving build qualifies it.
- Whole-003 acceptance (including live-target evidence and the protected
  expected-head development merge) is a separate strategic decision:
  this COMPLETE describes execution of the ordered 003-h scope, not
  acceptance or release readiness.
- The existing certifi (MPL-2.0) license-policy gate remains explicit
  and unresolved; no distribution audit is claimed from code tests.
