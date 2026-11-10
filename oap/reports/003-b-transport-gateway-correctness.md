# OAP Coding Report — 003-b

Identifier: 003-b
Result: COMPLETE
Repository: ulfe-lmi/slaif-raggedized-helper
PR number: 5
Branch: oap/003-generator-adapters-and-cache-probes
Base branch: main
Implementation head SHA: 51dc499a5b08f67901cdfb87436f9026a96c5c48
Report publication commit: SELF

## Work and scope

Executed oap/orders/003-b-transport-gateway-correctness.md (Status FINAL,
active 003-b, PR mode AMEND_EXISTING_PR) on the existing unique 003
objective PR #5, branch oap/003-generator-adapters-and-cache-probes from
verified base main 93b43177f4dcd0b28ef2c5ed33a049f83217f152. One
implementation commit 51dc499a5b08f67901cdfb87436f9026a96c5c48 (19 files,
+700/-126) changed:

- src/slaif_raggedized_helper/model_clients/transport.py: absolute endpoint
  resolution (root or .../v1 base -> exactly one /v1/responses; the
  /v1/v1/responses httpx base-URL joining bug is gone), one total deadline
  spanning connect/write/headers/body/retry for post_json (async
  cancellation scope) and the streaming worker (bounded deadline queue
  reads + task cancellation + join), dispatch-boundary deadline/cancellation
  rechecks (an exhausted budget or already-cancelled request never
  dispatches a late POST; the start() remaining<=0 race refuses instead of
  converting exhausted time into an unbounded wait), connect timeout bounded
  by remaining budget, pre-dispatch-only retry classification with a
  dispatched flag (accepted-POST-then-close / delayed headers are
  non-retryable ambiguity), bounded 32-slot cancellation-aware queue whose
  terminal signals are never dropped, SSE parser on LF/CR chr() constants
  (literal wire bytes: LF/CRLF, split multibyte UTF-8, coalesced frames,
  multiline data/comments, partial trailing frames, line/event/aggregate
  bounds, invalid UTF-8 refusal).
- src/slaif_raggedized_helper/model_clients/gateway.py: the exact pinned
  f2df0e82 dialect — data-only SSE frames with the JSON "type"
  discriminator (an explicit SSE event name, when present, must agree;
  disagreement fails closed), required envelope output_index on
  output_item events, final output items authoritative in array order
  WITHOUT output_index; completed/refusal message statuses, validated
  non-text terminal states (an in-progress/incomplete/failed reasoning item
  in a final completed response is contradictory, never silently skipped),
  explicit unsupported function_call refusal (the envelope never declares
  tools; valid text alongside is not salvaged), allowlisted refusal reasons
  no longer shadowed by the generic fallback, canary-safe fixed/allowlisted
  error reasons; pre-dispatch gates for route AND declared-model vision,
  bounded (4 MiB) image material bytes and the configured output reserve;
  backend fingerprint over the credential-free configured endpoint identity
  (scheme/host/port/API segment, not just hostname).
- src/slaif_raggedized_helper/config.py: RouteConfig base-path validation
  (root or .../v1 only) supporting the same contract.
- tests/integration/ (new): conftest.py (owned loopback RecordingServer
  fixture recording exact path/headers/body, synthetic canary key, literal
  SSE frame builders), test_generator_transport.py (criteria 1-4),
  test_gateway_generator.py (criteria 5-7, full-generator level).
- .github/workflows/oap.yml: product job now runs the integration suite
  from the clean locked install and lints tests/integration.
- config/schema/*.json: regenerated from the current models (003-a fields
  were missing).
- docs/generator-contract.md (new), docs/CI.md, TESTING.md (T06),
  README.md, STATUS.md: actual behavior, test commands, proven vs
  NOT-RUN/pending state.
- THIRD_PARTY_NOTICES: locked httpx 0.28.1 / httpcore 1.0.9 / anyio 4.16.0 /
  h11 0.16.0 / idna 3.20 / certifi 2026.10.23 rows plus the certifi MPL-2.0
  dependency gate (unapproved under the current whitelist; pending human
  question; not a platform waiver or license-audit pass).
- oap/active, oap/orders/003-b-transport-gateway-correctness.md,
  oap/reviews/003-a-review.json committed unchanged (exact strategic
  bytes); oap/governance/MANIFEST.json hash updated for TESTING.md only.

Native direct /completion adapter and qualification probes were NOT
implemented or rewritten here (003-c continuation); no partial owned files
were deleted.

## Acceptance evidence

1. Total deadline spans dispatch/connect/write/headers/body/retry; expired
   budgets refuse before dispatch; late drips cannot overrun; valid slow
   calls succeed; I/O owned/cancelled/closed; bounded worker/queue.
   Proof: post_json asyncio.wait_for cancellation scope; worker
   deadline-bounded queue reads, _cancel_worker (task.cancel + join),
   start() pre-check plus post-start remaining<=0 refusal, dispatch-
   boundary rechecks in both exchanges, connect bounded by remaining
   budget. Tests: test_expired_deadline_refused_before_dispatch (absolute,
   both paths, zero dispatch), test_late_body_drip_cannot_overrun_total_
   budget (kept regression of /tmp/raggedized003-deadline-repro.py; probe
   re-run passed: 0.203s against a 0.2s budget), test_valid_slow_call_
   inside_budget_succeeds, test_stream_total_deadline_mid_body_unknown_
   with_partial_text, test_stream_valid_slow_inside_budget_succeeds,
   test_stream_slow_headers_within_budget_starts, test_stream_startup_
   deadline_race_no_late_dispatch (controlled 60ms worker-start delay vs
   25ms budget: pre-dispatch refusal, zero requests recorded, cancelled
   worker never dispatches), test_budget_exhausted_retry_refused_before_
   dispatch and test_already_expired_deadline_refused_before_any_dispatch
   (normal and streaming; zero/one attempts, zero post-expiry dispatches).
2. Only positively pre-dispatch connect failures retry; accepted-POST with
   delayed/absent headers is UNKNOWN_COMPLETION, non-retryable, both
   timeout forms, both paths; no raw exceptions; server-side acceptance
   recorded and no duplicate attempt. Proof: _classify_send_error /
   _map_httpx with the dispatched flag; GatewayGenerator maps
   dispatched TransportError to UNKNOWN_COMPLETION on both result
   boundaries. Tests: test_accepted_header_delay_httpx_read_timeout_not_
   retryable, test_accepted_header_delay_total_deadline_not_retryable,
   test_stream_accepted_header_delay_httpx_timeout_not_retryable,
   test_stream_accepted_header_delay_total_deadline_not_retryable,
   test_stream_close_after_send_is_safe_non_retryable, test_full_
   generator_post_send_close_unknown_no_retry, test_full_generator_stream_
   post_send_close_unknown_no_retry, test_full_generator_header_delay_
   unknown_no_retry (attempts == 1, exact /v1/responses path, safe error
   text), test_pre_connect_retry_policy_is_finite (attempts == 3).
   Independent probe /tmp/probe-003b-closesend.py: outcome
   unknown_completion, attempts 1, path /v1/responses.
3. SSE parser exactness on literal wire bytes. Proof: LF/CR via chr()
   constants; tests use literal byte fixtures built independently of
   serializer code: test_sse_lf_crlf_and_coalesced_frames, test_sse_
   multiline_data_comments_and_inert_fields, test_sse_multibyte_utf8_
   split_across_chunks (real 2/4-byte sequences split mid-sequence),
   test_sse_partial_trailing_frame_is_not_emitted, test_sse_partial_
   trailing_line_is_not_emitted, test_sse_clean_eof_without_trailing_is_
   complete, test_sse_malformed_utf8_refused_safely, line/event/aggregate
   byte-bound refusals.
4. Finite cancellation-aware backpressure; terminal signals never dropped;
   early close stops the owned worker; no orphans. Proof: _put_signal /
   _put_bounded (cancel-aware blocking puts), close() -> task cancel +
   join. Tests: test_stream_queue_saturation_delivers_all_frames_and_eof
   (queue observed at exact full capacity 32 before any consumption; all
   200 frames delivered), test_stream_error_after_full_queue_is_delivered
   (exact full observation; RST after saturation still delivers the
   terminal failure), test_stream_early_close_stops_worker_no_orphans,
   test_stream_happy_path_frames_clean_eof_worker_stops.
5. Pinned bounded envelope only; native fields impossible; images require
   route AND declared-model capability plus trusted bounded resolver even
   when required_capabilities omits VISION; unsupported controls refuse
   pre-dispatch; no redirects/proxy-env switches/body echo/secret leak;
   stable declared identity. Proof: allowlist-built envelope, preflight
   gates (route+model vision, 4 MiB material bound, output reserve).
   Tests: test_stream_full_dialect_terminal_with_exact_envelope (native
   fields and canary key asserted absent from recorded wire bytes),
   test_root_base_hits_same_endpoint, test_image_requires_vision_and_
   resolver_even_if_omitted, test_image_requires_declared_model_vision,
   test_image_resolver_unsafe_or_failing_material_refused (unsafe,
   oversize, raising, missing resolver), test_image_with_safe_resolver_
   dispatches, test_max_output_tokens_over_reserve_refused_before_
   dispatch, test_unsupported_controls_refused_before_dispatch (stream/
   json_object/json_schema/prompt_cache), test_redirect_refused_at_
   gateway, test_proxy_environment_is_not_inherited, test_4xx_with_canary
   _body_is_safe_refusal (+ streaming), test_backend_identity_stable_
   across_requests_and_responses (request ID/answer stable; endpoint
   port/scheme and model changes alter identity).
6. Ordered multi-item parsing; duplicate/foreign/malformed IDs,
   contradictory terminal/item states, invalid encodings and unexpected/
   unsupported output refused; refusals/failed/incomplete/missing EOF
   never success; completed without usable text is failure; exact pinned
   dialect; safe allowlisted error reasons; canaries never leak. Proof:
   _collect_output + _GatewayAccumulator. Tests: test_pinned_completed_
   fixture_is_terminal (exact pinned e2e completed shape, final item
   without output_index, vllm-style usage), test_data_only_frames_are_the
   _supported_dialect (no event: lines on the wire), test_final_item_
   without_output_index_accepted, test_explicit_event_name_disagreement_
   refused, test_explicit_event_name_agreement_is_accepted, test_non_
   stream_multiple_message_items_in_order, test_duplicate_output_item_id_
   refused, test_out_of_order_output_index_refused, test_reasoning_
   completed_is_supported_non_text, test_reasoning_non_completed_mixed_
   refused (in_progress/incomplete/failed/missing status all fail),
   test_function_call_unsupported_action_not_salvaged (completed and
   in_progress; valid text present), test_function_call_only_is_
   explicitly_unsupported, test_stream_in_progress_reasoning_mixed_refused
   (stream boundary), test_completed_without_usable_text_is_failure,
   test_stream_delta_cumulative_mismatch_refused, test_stream_delta_for_
   unknown_item_refused, test_stream_duplicate_terminal_refused,
   test_stream_completed_output_mismatch_refused, test_stream_eof_
   without_terminal_is_incomplete_not_success, test_stream_eof_without_
   events_is_unknown_completion, test_non_stream_refusal_with_allowlisted
   _reason (error == "refusal: content_filter"), test_stream_refusal_with
   _allowlisted_reason, test_unknown_refusal_reason_is_fixed_safe,
   test_failed_status_canary_not_leaked, test_stream_error_event_canary_
   not_leaked (canary bytes asserted absent from results).
7. Real controlled HTTP/SSE tests run from a clean locked install in
   product CI alongside foundation/OAP regressions and product lint;
   supported/proven vs NOT-RUN documented. Proof: the product job step
   "Integration test suite (owned loopback HTTP/SSE)" and extended lint
   run in CI (below); docs/generator-contract.md documents the exact
   contract, test commands and the 003-c pending remainder.

## Verification

Local (implementation head 51dc499, worktree clean before report commit):

    uv run --locked pytest tests/integration -q   # 87 passed (5 consecutive runs)
    uv run --locked pytest tests/unit -q          # 80 passed
    python3 -m unittest discover -s tests/oap     # Ran 41 tests ... OK
    python3 oap/bin/check_state.py --repo-root .  # rc=0, state ACTIVE (003-b)
    uv run ruff check src tests/unit tests/integration  # All checks passed
    python -m compileall -q oap tests             # clean
    uv run python /tmp/raggedized003-deadline-repro.py
        # elapsed 0.203s vs 0.2s budget (known regression preserved)
    uv run python /tmp/probe-003b-closesend.py
        # unknown_completion, attempts 1, path /v1/responses

GitHub CI at implementation head 51dc499 (run 42754483667), all pass:
OAP tests Python 3.12/3.13/3.14; Product tests Python 3.12/3.14 (the
product job now includes the integration suite). All loopback tests use
owned 127.0.0.1 servers, unique synthetic canary keys, synthetic
dialect fixtures pinned to the reviewed gateway commit; no external
network, product services, real keys, GPU, live models or downloads were
touched. This report cannot certify its own future push/checks; a
separate post-publication receipt and strategic review record those facts.

## Documentation impact

docs/generator-contract.md (new) is the actual transport/gateway contract
and cancellation/deadline/outcome semantics doc; docs/CI.md and TESTING.md
(T06) record the new CI step, local parity commands and loopback/synthetic
character; README.md and STATUS.md carry actual-behavior links (003 slice
open on PR #5, not merged, native/probe remainder pending). Schema exports
regenerated to match the models. No behavioral documentation was left
stale.

## DHA and boundaries

Order declares Decision: NONE; no CRITICAL append was performed or
required. No merge performed, no auto-merge, no tag/deploy/release, no
model/provider/profile change, no next-work selection. Protected
resources untouched: no live services, GPU work, real keys, production
data or other projects/panes/FIFOs were modified; the sole control
wrapper's consumed OK was not re-read; no duplicate reader was started.

## Limitations and remaining work

- Objective 003 as a whole remains UNRESOLVED: the native direct
  /completion adapter (cache_prompt/id_slot on tested private builds) and
  the qualification probes are NOT RUN and remain pending for the later
  same-PR 003-c continuation; this round neither waives nor satisfies
  them.
- certifi 2026.10.23 (MPL-2.0) is an unresolved dependency gate under the
  current MIT/BSD/Apache allowlist: recorded in THIRD_PARTY_NOTICES with
  the locked metadata; the policy question is pending human exception;
  not a platform waiver and not a license-audit pass; final 003/018
  license gates must resolve it before any distribution.
- All evidence in this report is synthetic loopback + pinned-dialect
  fixtures: it proves the bounded transport/gateway behavior, not live
  gateway/model, hardware or whole-objective readiness.
- Result COMPLETE describes execution of the bounded 003-b slice only; it
  is not acceptance, release readiness or merge approval.
