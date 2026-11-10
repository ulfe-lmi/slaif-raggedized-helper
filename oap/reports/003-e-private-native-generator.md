# OAP Coding Report — 003-e

Identifier: 003-e
Result: COMPLETE
Repository: ulfe-lmi/slaif-raggedized-helper
PR number: 5
Branch: oap/003-generator-adapters-and-cache-probes
Base branch: main
Implementation head SHA: ef1251597bace2a8b8155845de2d8d8c219c5b63
Report publication commit: SELF

## Work and scope

Executed oap/orders/003-e-private-native-generator.md (Status FINAL,
active 003-e, PR mode AMEND_EXISTING_PR) on the existing unique 003
objective PR #5, branch oap/003-generator-adapters-and-cache-probes
from verified base main 93b43177f4dcd0b28ef2c5ed33a049f83217f152. At
round start the remote head af87bcc16dfb252d71f8f909c0a770c5058de853
was the published 003-d report SELF (sole parent implementation
8e96b0cd50d186ef11e159906d376117488a90ac, report-only diff; PR #5
OPEN/MERGEABLE; worktree tracked-clean except the untracked strategic
003-d review). Exactly one implementation commit was pushed before
this report:

- ef1251597bace2a8b8155845de2d8d8c219c5b63 (implementation head): the
  narrow JSON-decoder ValueError boundary plus the private offline
  native generator, the exact 003-e order/active bytes, the unchanged
  pre-published 003-d strategic review (oap/reviews/003-d-review.json)
  and the affected governance-manifest refresh (the TESTING.md pin).

Slice A — narrow gateway decoder boundary (the order's prerequisite):
- gateway.py _parse_non_stream now catches (ValueError, RecursionError)
  at that single json.loads call: json.JSONDecodeError is a ValueError
  subtype, and the interpreter integer-digit limit
  (sys.get_int_max_str_digits; 4300 on the observed interpreters)
  rejects an oversized JSON integer with a bare ValueError. The guard
  is scoped to that parse call only; no whole-generation catch-all.
  The native parser (direct.py) guards the same expected decoder
  classes (test_oversized_integer_in_native_response_is_safe).
- Two actual-HTTP regressions in
  tests/integration/test_gateway_generator.py:
  test_non_stream_excessive_integer_digits_safe_refusal (in-process
  5000-digit usage integer; branch on the observed interpreter limit:
  safe FAILED refusal, or validated TERMINAL when the interpreter
  accepts the digits) and
  test_non_stream_decoder_digit_limit_controlled_subprocess (isolated
  subprocess pinned to the supported 640-digit limit, the CPython
  minimum; the production/global interpreter limit is never changed in
  the main test process).

Slice B — private offline native generator:
- direct.py (new, 615 lines): DirectNativeGenerator on the proven
  003-b transport — zero-network preflight (explicit offline_diagnostic
  mode, private/loopback destination, private_trusted policy, declared
  model, template qualification record, explicit finite operator
  max_output_tokens and deadline_seconds); the /apply-template
  envelope (trusted instructions in the system role, ordered TextItems
  as user data); the bounded /completion envelope (rendered prompt,
  explicit n_predict, stream:false, supported temperature/top_p,
  json_object -> {} any-JSON grammar, json_schema -> the caller's
  exact schema, cache_prompt only with the tested capability,
  singular id_slot only with the tested capability); one total
  deadline (the smaller of caller/config) spanning template +
  generation + retries and never reset per attempt, with the
  pre-inference recheck after template work; finite retry only for
  positive pre-dispatch failures; unknown completion non-retryable;
  cancellation/cleanup of owned I/O; and fail-closed native
  terminal/metric parsing (no raw provider bytes).
- transport.py: NATIVE_PINNED_PATHS (/apply-template, /completion)
  plus resolve_native_endpoint_url (origin + configured base_path +
  pinned path, 003-b prefix semantics preserved) and
  GatewayTransport(endpoint_contract=...) defaulting to the unchanged
  003-b contract. URL, deadline, privacy, retry and cleanup behavior
  are preserved; the unchanged 33 transport regressions remain green.
- config.py: the falsely pinned five-name built-in registry corrected
  to PINNED_LLAMA_BUILTIN_CHAT_TEMPLATES (the 49 names of the pinned
  reference commit 3b4d6ab3f79651935fba1dd93732f29022a7f5f5; a
  documented reference list, not a client-side allowlist);
  chat_template None = the model-metadata default template; the
  identity-token rule (plain non-empty token; no path; no whitespace;
  the dialect closing-marker sequence is not a legal IDENTITY);
  DirectTemplateQualification (template str|None, build_id, method,
  recorded_at) with the declared-match check; the offline_diagnostic
  opt-in requires destination + private_trusted + model +
  qualification + explicit finite limits.
- model_clients/__init__.py exports DirectNativeGenerator and
  GatewayGenerator; config/schema/app-config.schema.json regenerated
  (deterministic, byte-stable).

Strategic clarification (audit/003-e-template-instruction-clarification
.md, strategic home): the criterion-2 closing-marker rule corrects the
old hand-written formatter that invented the token as the system/user
turn delimiter; it is not a ban on literal technical/source content.
The implementation follows: the client never substring-scans,
rejects, strips, rewrites or truncates a server-rendered prompt; the
forbidden-sequence rule applies to the declared template IDENTITY
token only (config time); and the focused owned-HTTP positive case
test_literal_marker_content_reaches_completion_unchanged carries a
literal closing-marker example (documented in
docs/generator-contract.md as `&lt;/tool_call&gt;`) inside untrusted
TextItem reference data and proves the exact server-rendered
qualified prompt reaches /completion byte-for-byte unchanged (the
sequence appears exactly once, inside the user-data segment).

Changed files (20, 2847 insertions / 73 deletions):
src/slaif_raggedized_helper/model_clients/direct.py (new),
src/slaif_raggedized_helper/model_clients/gateway.py,
src/slaif_raggedized_helper/model_clients/transport.py,
src/slaif_raggedized_helper/model_clients/__init__.py,
src/slaif_raggedized_helper/config.py,
config/schema/app-config.schema.json, docs/generator-contract.md,
README.md, TESTING.md, docs/CI.md, STATUS.md,
tests/integration/conftest.py,
tests/integration/test_gateway_generator.py,
tests/integration/test_native_direct.py (new),
tests/unit/test_config.py, tests/unit/test_native_mapping.py (new),
oap/active (exact 003-d -> 003-e bytes),
oap/orders/003-e-private-native-generator.md (new, exact bytes),
oap/reviews/003-d-review.json (new, unchanged pre-published review),
oap/governance/MANIFEST.json (TESTING.md pin refreshed for the
in-scope T06 doc change; the manifest is not self-pinned; the 003-b
and 003-c rounds used the same pattern — the next order pins the new
manifest identity). No other files touched; no model/provider/profile
change, no role-law change, no new PR, no merge, no numeric advance.

## Acceptance evidence

1. Explicit materialization (criterion 1): config-time opt-in
   validation (offline_diagnostic requires destination +
   private_trusted + declared model + matching qualification +
   explicit finite max_output_tokens and deadline_seconds; online
   direct generation refused) and the zero-network preflight in
   direct.py. Actual-HTTP proofs (owned loopback, zero recorded
   requests asserted): test_disabled_mode_refuses_with_zero_network,
   test_answer_purpose_refused_before_any_network,
   test_visual_image_requests_refused_before_dispatch,
   test_disabled_policy_destination_never_materializes,
   test_operator_limit_missing_refuses_before_dispatch. Destinations
   and secret refs are operator-controlled config; callers cannot
   supply arbitrary URL/file/model/process endpoints; no ambient proxy
   or redirect (fixed origin + base_path + pinned paths only).
2. Real template rendering (criterion 2): the client renders no
   templates locally; test_apply_template_wire_is_exact_messages_contract
   proves the exact messages contract (system = trusted instructions,
   ordered TextItems = user data) and that /apply-template performs no
   inference (exactly one request per path);
   test_ordered_items_keep_boundaries_and_roles proves the ordered
   boundaries in the rendered prompt;
   test_template_refusal_is_safe_and_stops_before_completion proves
   the server 400 maps to a safe typed failure with no /completion
   dispatch; malformed/missing/error prompt responses are refused
   (test_apply_template_malformed_prompt_refused,
   test_apply_template_missing_prompt_refused,
   test_apply_template_error_object_refused). The registry correction
   is the 49-name PINNED_LLAMA_BUILTIN_CHAT_TEMPLATES (unit-tested
   against the pinned reference list); chat_template None = the
   model-metadata default; the identity-token rules are unit-tested
   (plain token; no path; no whitespace; the closing-marker sequence
   refused as an IDENTITY while the same sequence as message content
   passes). Per the strategic clarification no blanket substring
   rejection exists anywhere in the client;
   test_literal_marker_content_reaches_completion_unchanged is the
   focused owned-HTTP positive literal-marker case.
3. Envelope and controls (criterion 3):
   test_completion_envelope_exact_minimal proves exactly
   {prompt, n_predict, stream:false} and nothing else;
   test_completion_envelope_supported_sampling_and_json_controls and
   test_completion_envelope_json_object_maps_to_any_json_grammar prove
   the supported sampling and the json_object -> {} / json_schema ->
   exact-schema mapping; test_cache_prompt_only_with_tested_capability
   and test_id_slot_sent_when_tested prove the capability gates
   (test_untested_slot_id_is_config_error: an untested slot identity
   is a config error, never an invented slot_ids control);
   test_unsupported_controls_refused_before_any_dispatch and
   test_visual_image_requests_refused_before_dispatch prove local
   refusal with zero inference dispatch for unsupported requested
   behavior and every visual/image request.
4. Deadline/budget (criterion 4): one total deadline (the smaller of
   caller/config) spans template + generation + retries and is never
   reset: test_expired_deadline_refuses_before_re_dispatch_after_
   template_work proves refusal before inference after template work
   with zero /completion dispatch; test_retry_on_pre_dispatch_failure
   _shares_one_budget and test_pre_dispatch_timeout_is_retryable_
   within_budget prove finite retry only for positive pre-dispatch
   failures under one budget; test_budget_exhausted_refuses_before_
   first_dispatch proves the budget is finite;
   test_output_budget_refused_before_dispatch and
   test_output_budget_equal_to_operator_limit_is_accepted prove the
   explicit refuse (never clamp) semantics when the requested
   max_output_tokens exceeds the operator limit, equality accepted;
   missing operator limits refuse before any dispatch (zero network)
   via test_operator_limit_missing_refuses_before_dispatch. All owned
   I/O is cancelled/closed on every path (the transport's preserved
   cleanup; the 33 unchanged transport regressions stay green).
5. Stop semantics (criterion 5): test_non_successful_terminals_never_
   become_terminal (parameterized: stop=true with stop_type=limit,
   truncated=true, stop_type=none, stop != true, missing/invalid
   terminal reason, unqualified stop-word completion, empty content)
   and test_eos_with_usable_content_is_terminal (stop=true,
   truncated=false, stop_type=eos, non-empty string content ->
   TERMINAL) prove the fail-closed matrix;
   test_server_error_object_is_safe_refusal,
   test_http_error_statuses_are_safe and
   test_malformed_completion_bodies_are_safe prove safe typed
   failures with no raw provider bytes (canary assertions);
   test_identity_stable_and_distinct_from_response_text and
   test_identity_changes_with_declared_identity prove the stable
   declared identity distinct from response text/ID, with missing
   runtime/artifact fields staying unknown.
6. Metrics (criterion 6): test_synthetic_metric_case_preserves_
   distinct_facts proves the synthetic 100-submitted (10 new / 90
   cached) + 12-generated case with tokens_cached=112 preserving the
   distinct facts (input_tokens <- tokens_evaluated; prefill_tokens <-
   timings.prompt_n; cache_hit_tokens <- timings.cache_n;
   output_tokens <- timings.predicted_n; the top-level tokens_cached
   is the slot's resulting prompt length and is never substituted for
   timings.cache_n); test_malformed_or_unsafe_counters_stay_null
   (bool/NaN/inf/malformed counters cannot prove evaluated work),
   test_missing_metric_fields_stay_null (unknown old-build fields
   stay null), test_zero_millisecond_timings_are_null_not_zero
   (positive-only contract) and
   test_model_timings_are_model_reported_not_caller_wall (ttft/total
   from prompt_ms/predicted_ms; caller wall time separate).
7. Controlled HTTP and all-green (criterion 7): 71 new owned-loopback
   native integration cases (tests/integration/test_native_direct.py)
   plus 37 native mapping unit cases
   (tests/unit/test_native_mapping.py) and 10 additional config unit
   cases (tests/unit/test_config.py: 37 -> 47); 2 new gateway
   regressions (suite 123 -> 125). All prior suites remain green: 33
   transport, all gateway/foundation unit, OAP, lint, governance and
   CI — see Verification.

Test-count record per the order: the pre-003-e baseline is 236
product tests (156 integration: 123 gateway + 33 transport; 80 unit)
plus the separate 41 OAP. Actual collection at the implementation
head: 229 integration (125 gateway + 33 transport + 71 native) + 127
unit (47 config + 37 native mapping + 15 cli-doctor + 14 contracts +
11 model-lock + 3 import-hygiene) = 356 product tests, plus the
separate 41 OAP unittest suite. The old erroneous 003-c 136/95/41
figures are not copied.

## Verification

Exact commands at the implementation head (all local, synthetic,
offline; no live model, download, credentials, GPU or corpus):

- uv sync --locked — clean locked environment, exit 0.
- uv run pytest tests/unit -q — 127 passed, exit 0.
- uv run pytest tests/integration -q — 229 passed, exit 0 (125
  gateway + 33 transport + 71 native).
- python3 -m unittest discover -s tests/oap — Ran 41 tests, OK.
- python3 oap/bin/check_state.py --repo-root . — state ACTIVE, active
  003-e, exit 0; activation_matches_current_governance=false is the
  expected post-refresh state for the in-scope manifest pin update
  (the source_note records that an authorized candidate governance
  change may differ from activation; the immutable order bytes are
  not rewritten).
- uv run ruff check src tests/unit tests/integration — All checks
  passed.
- python -m compileall -q oap tests — clean.
- uv run raggedized --help — console entry works offline.
- uv run raggedized doctor --config config/examples/example-config.json
  — exit 1 with the honest issues MODEL_UNQUALIFIED + SECRET_ABSENT
  (status issues, config valid, readiness not_ready), as CI expects.
- Schema regeneration is deterministic: a second
  json.dumps(model_json_schema(), indent=2, sort_keys=True) + LF write
  is byte-identical to the committed schema file.

CI (GitHub Actions, .github/workflows/oap.yml, clean locked checkout):
- Implementation head ef1251597bace2a8b8155845de2d8d8c219c5b63: run
  42774495647, all 5 jobs SUCCESS (Product tests Python 3.12 and 3.14;
  OAP tests Python 3.12, 3.13, 3.14), completed 2026-11-10T07:21:46Z.
- Round-start heads remain green in history:
  8e96b0cd50d186ef11e159906d376117488a90ac run 42764635506 and
  af87bcc16dfb252d71f8f909c0a770c5058de853 run 42765057169, all 5
  SUCCESS each (the 003-d implementation and report heads).

Mock/live distinction: every network fact above is owned 127.0.0.1
loopback fixtures with synthetic qualifications and canaries, plus
pinned-dialect fixtures and GitHub CI from a clean checkout. No live
model/route request, no real upstream key, no gateway access, no GPU
or service control was performed (order live authorization: NONE).

This report cannot certify its own future push or checks on the
report-publication head; the CI facts recorded above are for the
implementation head only, and the post-publication state is recorded
by the separate receipt/strategic review.

## Documentation impact

docs/generator-contract.md: the new native section documents the
supported exact wire dialect (the /apply-template messages contract;
the exact /completion key set), the safe config/templates/
capabilities (49-name reference registry, the identity-token rule
including the closing-marker identity restriction, the qualification
record), the explicit offline-only boundary (private trusted
destination, operator-controlled explicit finite limits, refuse-not-
clamp semantics), the stable declared-vs-verified identity, the
truthful stop matrix and the metric/timings mapping (including the
tokens_cached=112 distinction), and the literal-marker-as-data rule
(the rendered prompt is never substring-scanned, rejected or
stripped; the sequence is documented as `&lt;/tool_call&gt;`).
README.md, TESTING.md (T06 native suite entry), docs/CI.md (the
integration step now includes the native suite) and STATUS.md (the
003-e round record; native qualification still open) updated to match.
config/schema/app-config.schema.json regenerated. No command,
performance, license clearance or readiness is claimed beyond what
was executed; the certifi license gate is preserved.

## DHA and boundaries

The order declares Decision: NONE; no critical append was performed or
needed; CRITICAL.md untouched. Preserved: the 003-b transport behavior
(endpoint-contract default unchanged; 33 regressions green), the 003-d
structural oracles and their suite, all prior immutable reports/
orders/reviews, the exact strategic 003-e order/active bytes
(committed unchanged), the unchanged pre-published 003-d strategic
review, model/provider/profile, private state, deadline/cancellation
behavior and original sources. No merge, auto-merge, tag, release or
deploy; PR #5 remains the single 003 objective PR (amended); no next
work selected; no numeric advance; no competing control reader started
(the sole external wrapper consumed the signal before this round).

## Limitations and remaining work

- The live native target is NOT RUN: no live model/route/service
  authorization exists (order: NONE); all native evidence is synthetic
  owned-loopback HTTP plus pinned-dialect fixtures. The pinned
  reference (ggml-org/llama.cpp tools/server, commit
  3b4d6ab3f79651935fba1dd93732f29022a7f5f5) is a dialect reference,
  not the unknown deployed build; native qualification remains open
  until an actually qualified target is probed.
- The 003-b/003-c-era JSON decoder ValueError gap is closed at the
  non-stream parse call with the narrow guard; the stream path's
  numeric decoding is not widened (out of scope per the order).
- The existing certifi (MPL-2.0) license-policy gate remains explicit
  and unresolved; no distribution audit is claimed from code tests.
- Whole 003 (probes/CLI/documentation closure) remains open for
  explicit remaining scope; a reported COMPLETE describes execution,
  not acceptance or release readiness. Strategic review and any
  continuation/acceptance/merge decisions are separate.
