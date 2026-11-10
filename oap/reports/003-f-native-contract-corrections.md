# OAP Coding Report — 003-f

Identifier: 003-f
Result: COMPLETE
Repository: ulfe-lmi/slaif-raggedized-helper
PR number: 5
Branch: oap/003-generator-adapters-and-cache-probes
Base branch: main
Implementation head SHA: db7443fd64b3207a208348ea178c1600e6ff90f4
Report publication commit: SELF

## Work and scope

Executed oap/orders/003-f-native-contract-corrections.md (Status FINAL,
active 003-f, PR mode AMEND_EXISTING_PR) on the existing unique 003
objective PR #5, branch oap/003-generator-adapters-and-cache-probes from
verified base main 93b43177f4dcd0b28ef2c5ed33a049f83217f152. At round
start the remote head 893081f1e93b1c6282e685de91bb4684fa9bb1e7 was the
published 003-e report SELF (sole parent implementation
ef1251597bace2a8b8155845de2d8d8c219c5b63, report-only diff; PR #5
OPEN/MERGEABLE; worktree tracked-clean except the untracked strategic
003-e review). Exactly one implementation commit was pushed before this
report:

- db7443fd64b3207a208348ea178c1600e6ff90f4 (implementation head): the
  native metric-quantity/zero/overflow/counter corrections, the
  default-deny native JSON/schema control admission, the focused
  semantic extensions, the affected docs, the refreshed governance
  measurements/hashes, plus the exact 003-f order/active bytes and the
  unchanged pre-published 003-e strategic review
  (oap/reviews/003-e-review.json).

Metric quantities (criterion 1), in
src/slaif_raggedized_helper/model_clients/direct.py and
src/slaif_raggedized_helper/schema.py:
- ``timings.prefill_seconds`` <- ``timings.prompt_ms``/1000 (the
  reported PROMPT PROCESSING duration — a lower bound, never labelled a
  first-token measurement); ``timings.decode_seconds`` <-
  ``timings.predicted_ms``/1000; each carried individually with explicit
  units and provenance. ``ttft_seconds`` is never set by this adapter:
  the pinned native dialect (reference 3b4d6ab3f79651935fba1dd93732f29022a7f5f5,
  server_slot_stats::to_json) reports no first-token measurement, so
  TTFT stays unavailable unless a supported backend actually reports or
  measures it.
- ``timings.total_seconds`` is retained only as an explicitly
  model-scoped derived model-work total (sum of the two reported
  model-phase durations, present only when both were reported); it is
  never presented as caller wall time, and caller elapsed time is
  neither mixed in nor invented from native phases.

Known zeros and safe numerics (criterion 2): a measured reported 0ms is
a known zero (0.0), never null (focused NonNegativeFiniteFloat
contract extension in _constraints.py with bool rejection); a missing
or invalid field stays unavailable and no longer discards the other
reported phase (prompt_ms=0 with predicted_ms=60 now yields
prefill 0.0, decode 0.06, model total 0.06). The numeric
conversion/arithmetic boundary in _finite_nonneg_number now rejects
bool/NaN/Inf and unrepresentable input safely: a reported prompt_ms of
10**400 (valid JSON within the byte/digit bounds) maps to unavailable
data instead of a raw float() OverflowError escaping generate(); the
guard is narrow at the input conversion boundary, not a
whole-function exception blanket.

Default-deny optional JSON/schema controls (criterion 3):
src/slaif_raggedized_helper/config.py adds
DirectCapabilities.json_grammar_tested (default False). The native
preflight in direct.py infers the requested control from the ACTUAL
INPUT SHAPE (response_format json_object/json_schema — not only from
caller-required capability declarations) and refuses before
/apply-template or /completion (zero dispatch) unless the capability
was tested on the build; template qualification alone does not prove
grammar support. Qualified controls preserve the pinned request
semantics: json_object maps to the reference's any-JSON grammar form {}
(not a stronger object-shape guarantee) and json_schema sends the
caller's exact schema. All existing cache/slot/vision/stream/purpose/
operator-budget gates and the declared backend identity are preserved.

Counter evidence (criterion 4): _parse_native_usage now enforces the
supported-dialect consistency relation (tokens_evaluated == prompt_n +
cache_n, per the pinned reference bookkeeping n_prompt_cached = n_past
and n_prompt_processed increments): a contradictory reported breakdown
(e.g. 100 input with 90 new + 90 cached) invalidates the evaluated/
cache breakdown (prefill_tokens/cache_hit_tokens withheld as null)
while the directly reported task total keeps its own provenance; raw
contradictory values are not carried in the result. Missing/zero/raw
field provenance is preserved (reported zero stays a value; missing
stays null; top-level tokens_cached is still never substituted for
cache hits; nothing is inferred from the submitted count).

Docs/governance: docs/generator-contract.md documents the actual metric
units/measurement boundaries, the unknowns, the chosen invalid-counter
handling and the default-deny native-control qualification, and removes
the misleading delimiter-identity facts (template qualification is
never magic substring/delimiter scanning; the identity-token rule
constrains the configured template name only; the literal
chr(60)+"/tool_call"+chr(62) tool-call close and the three-backtick
Markdown fence example are both preserved data). TESTING.md T06, the
generated config/schema/app-config.schema.json and the affected
governance measurements were refreshed together (below).

Changed files (13 modified + 2 added = 15, 704 insertions / 103
deletions):
src/slaif_raggedized_helper/model_clients/direct.py,
src/slaif_raggedized_helper/schema.py,
src/slaif_raggedized_helper/_constraints.py,
src/slaif_raggedized_helper/config.py,
config/schema/app-config.schema.json, docs/generator-contract.md,
TESTING.md, tests/integration/test_native_direct.py,
tests/unit/test_native_mapping.py, tests/unit/test_config.py,
oap/governance/CONTEXT-BUDGET.md, oap/governance/MANIFEST.json,
oap/active (exact 003-e -> 003-f bytes),
oap/orders/003-f-native-contract-corrections.md (new, exact bytes),
oap/reviews/003-e-review.json (new, unchanged pre-published review).
No other files touched; no model/provider/profile change, no role-law
change, no new PR, no merge, no numeric advance.

## Acceptance evidence

1. Actual metric quantities preserved: the pinned reference's
   server_slot_stats::to_json (prompt_ms = t_prompt_ms(), predicted_ms
   = t_gen_ms(), no first-token field) is the mapping source.
   test_synthetic_metric_case_preserves_distinct_facts (loopback HTTP)
   and its unit twin assert prefill_seconds 0.25 / decode_seconds 1.3 /
   total_seconds 1.55 with ttft_seconds None for the
   prompt_ms=250/predicted_ms=1300 case; the unit mapping tests prove
   ttft is never populated from any reported field, the model-scoped
   total requires both reported phases, and caller wall time never
   appears in result timings (test_model_timings_are_model_reported_
   not_caller_wall).
2. Known zeros and safe numerics: test_reported_zero_millisecond_
   prefill_is_a_known_zero (loopback: prompt_ms=0, predicted_ms=60 ->
   prefill_seconds 0.0, decode_seconds 0.06, total_seconds 0.06, usage
   intact) and the unit twin (both-zero and single-phase cases);
   test_overflow_reported_time_is_safe_over_http and the unit twin
   (prompt_ms=10**400 -> generate() returns a safe TERMINAL result,
   prefill unavailable, decode 0.06 preserved, no exception). Bool/
   NaN/Inf/negative/string counters and times remain rejected
   (extended parametrizations).
3. Default-deny JSON/schema admission: test_unsupported_controls_
   refused_before_any_dispatch now includes json-object-unqualified and
   json-schema-unqualified (FAILED, safe fixed reason "native JSON
   control refused: json_schema grammar support is not tested on this
   build (default deny)", zero recorded requests);
   test_qualified_json_controls_preserve_request_semantics (parameter-
   ized json-object-qualified/json-schema-qualified) proves the
   qualified build dispatches exactly once per path and sends
   json_schema {} / the caller's exact schema with the pinned key set;
   test_native_json_grammar_capability_is_default_deny (unit) pins the
   config default; the fingerprint sensitivity test covers the new
   capability.
4. Counter evidence: test_contradictory_reported_counters_are_withheld
   (loopback: 100 input with 90 new + 90 cached -> input_tokens 100
   kept, prefill_tokens/cache_hit_tokens null, output_tokens 12) and
   the unit twin (consistent 10+90=100 not withheld; missing breakdown
   field disables the check, nothing inferred) plus the preserved
   distinct-facts regressions (top-level tokens_cached=112 never
   substitutes for cache hits).
5. Real controlled-HTTP coverage and preserved regressions: the five
   vector experiments (baseline 100/10/90/12 with 30/60ms; zero
   prefill 0/60ms; huge reported time 10**400; unqualified json_object;
   contradictory counters) are asserted over real owned-loopback paths
   and recorded request bytes; the exact unchanged qualified prompt
   (literal tool-call close constructed as chr(60)+"/tool_call"+chr(62)
   AND the three-backtick Markdown fence data) is asserted
   byte-for-byte in test_literal_marker_content_reaches_completion_
   unchanged. The independent /tmp/raggedized003-native-review.py
   (five experiments, ten actual owned-loopback POSTs at the
   implementation head) was re-run: all five observations now conform
   (no timing alias, no zero loss, no OverflowError, zero-dispatch
   refusal, withheld contradiction). All prior gateway/transport/
   native/product/OAP/lint/governance regressions remain green
   (125 gateway, 33 transport, 78 native, 132 unit, 41 OAP, ruff clean,
   all 5 CI jobs SUCCESS — see Verification).

Test-count record per the order: the baseline before F is 356 product
tests (229 integration: 125 gateway + 33 transport + 71 native; 127
unit) plus the separate 41 OAP. Actual collection at the
implementation head: 236 integration (125 gateway + 33 transport + 78
native) + 132 unit (48 config + 41 native mapping + 15 cli-doctor + 14
contracts + 11 model-lock + 3 import-hygiene) = 368 product tests, plus
the separate 41 OAP unittest suite.

## Verification

Exact commands at the implementation head (all local, synthetic,
offline; no live model, download, credentials, GPU or corpus):

- uv sync --locked — clean locked environment, exit 0.
- uv run pytest tests/unit -q — 132 passed, exit 0.
- uv run pytest tests/integration -q — 236 passed, exit 0 (125
  gateway + 33 transport + 78 native).
- python3 -m unittest discover -s tests/oap — Ran 41 tests, OK.
- python3 oap/bin/check_state.py --repo-root . — state ACTIVE, active
  003-f, exit 0; activation_matches_current_governance=false is the
  expected post-refresh state for the in-scope manifest pin update
  (the source_note records that an authorized candidate governance
  change may differ from activation; the immutable order bytes are
  not rewritten).
- uv run ruff check src tests/unit tests/integration — All checks
  passed.
- python3 -m compileall -q oap tests — clean.
- Schema regeneration is deterministic: a second
  json.dumps(model_json_schema(), indent=2, sort_keys=True) + LF write
  is byte-identical to the committed schema file (the only committed
  delta versus the 003-e schema is the new json_grammar_tested
  property).

CI (GitHub Actions, .github/workflows/oap.yml, clean locked checkout):
- Implementation head db7443fd64b3207a208348ea178c1600e6ff90f4: run
  42781488186, all 5 jobs SUCCESS (Product tests Python 3.12 and 3.14;
  OAP tests Python 3.12, 3.13, 3.14), conclusion success, observed
  2026-11-10.
- Round-start head remains green in history:
  893081f1e93b1c6282e685de91bb4684fa9bb1e7 run 42775398612, all 5
  SUCCESS (the 003-e report head).

Mock/live distinction: every network fact above is owned 127.0.0.1
loopback fixtures with synthetic qualifications and canaries, plus
pinned-dialect fixtures and GitHub CI from a clean checkout. No live
model/route request, no real upstream key, no gateway access, no GPU or
service control was performed (order live authorization: NONE).

This report cannot certify its own future push or checks on the
report-publication head; the CI facts recorded above are for the
implementation head only, and the post-publication state is recorded
by the separate receipt/strategic review.

## Documentation impact

docs/generator-contract.md: the native sections now state the actual
metric units/measurement boundaries (prefill vs decode vs model-scoped
total; TTFT unavailable in the pinned dialect), the known-zero
semantics, the safe overflow handling, the chosen contradictory-counter
withholding rule, the default-deny native JSON/schema qualification
(documented field is not tested grammar support; {} is any JSON, not an
object-shape guarantee) and the corrected template-identity facts
(qualification is never magic substring/delimiter scanning; the
identity-token rule and the literal chr(60)+"/tool_call"+chr(62) plus
Markdown-fence data preservation are stated as data preservation).
TESTING.md T06 lists the 003-f native semantics.
config/schema/app-config.schema.json regenerated (deterministic,
byte-stable). Governance: CONTEXT-BUDGET.md table refreshed to the
actual final bytes (TESTING.md 3296; declared routine read set 35847
UTF-8 bytes, ceiling 50000) and MANIFEST.json pins for TESTING.md and
CONTEXT-BUDGET.md updated together; DISTILLATION-MAP.md carries no
measurements and is unchanged; historical order pins were not altered.
No command, performance, license clearance or readiness is claimed
beyond what was executed; the certifi license gate is preserved.

Registry accuracy (per the order, from the actual primary-source
comparison): the pinned reference registry
PINNED_LLAMA_BUILTIN_CHAT_TEMPLATES holds 54 entries (verified by count
against the pinned README built-in list, matching the strategic
independent comparison); the 003-e report's "49" was a report
inaccuracy — the code registry already carried the 54-entry list and is
unchanged by this round.

## DHA and boundaries

The order declares Decision: NONE; no critical append was performed or
needed; CRITICAL.md untouched. Preserved: the 003-b transport behavior
and its 33 regressions, all gateway suite regressions (125), the 003-d
structural oracles and their suite, all prior immutable reports/orders/
reviews, the exact strategic 003-f order/active bytes (committed
unchanged), the unchanged pre-published 003-e strategic review,
model/provider/profile, private state, deadline/cancellation behavior
and original sources. No merge, auto-merge, tag, release or deploy; PR
#5 remains the single 003 objective PR (amended); no next work
selected; no numeric advance; no competing control reader started (the
sole external wrapper consumed the signal before this round).

## Limitations and remaining work

- The live native target is NOT RUN: no live model/route/service
  authorization exists (order: NONE); all native evidence is synthetic
  owned-loopback HTTP plus pinned-dialect fixtures. The pinned
  reference (ggml-org/llama.cpp tools/server, commit
  3b4d6ab3f79651935fba1dd93732f29022a7f5f5) is a dialect reference, not
  the unknown deployed build; the json_grammar_tested capability
  remains default deny until an actually tested serving build
  qualifies it.
- Bounded qualification probes (and any probe runner) remain required
  in a later finalized suffix; no probe, benchmark or live claim is
  made here.
- The existing certifi (MPL-2.0) license-policy gate remains explicit
  and unresolved; no distribution audit is claimed from code tests.
- Whole 003 (probes/CLI/documentation closure) remains open for
  explicit remaining scope; a reported COMPLETE describes execution,
  not acceptance or release readiness. Strategic review and any
  continuation/acceptance/merge decisions are separate.
