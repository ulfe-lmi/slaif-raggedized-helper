# OAP Coding Report — 003-a

Identifier: 003-a
Result: PARTIAL
Repository: ulfe-lmi/slaif-raggedized-helper
PR number: 5
Branch: oap/003-generator-adapters-and-cache-probes
Base branch: main
Implementation head SHA: f34b9906c7757913104a4ccc9899ee59879d00d4
Report publication commit: SELF

## Work and scope

Executed oap/orders/003-a-generator-adapters-and-cache-probes.md (Status FINAL,
active 003-a) on branch oap/003-generator-adapters-and-cache-probes from
verified origin/main 93b43177f4dcd0b28ef2c5ed33a049f83217f152 (order Base
commit). One objective PR (#5), created via gh.

Per the strategic D0 replan (audit/003-execution-replan.md) this round ended
with a truthful PARTIAL checkpoint instead of a further broad rewrite. One
implementation commit f34b9906c7757913104a4ccc9899ee59879d00d4
(9 files, +1783/-5) changed:

- pyproject.toml, uv.lock: httpx 0.28.1 runtime dependency only (locked
  lightweight environment otherwise unchanged; no ML stack).
- src/slaif_raggedized_helper/config.py: RouteCapabilities +
  RouteConfig.capabilities (default-deny), GeneratorConfig.api_key_ref/
  max_retries, DirectCapabilities, DirectDestination (private/loopback-only
  validation), DirectTemplateQualification (aware recorded_at, pinned
  method), DirectGenerationConfig (disabled|offline_diagnostic, explicit
  private_trusted policy, PINNED_LLAMA_CHAT_TEMPLATES registry, slot_id
  gated on slot_tested, unconditional online refusal retained).
- src/slaif_raggedized_helper/schema.py: Capability.PROMPT_CACHING;
  GeneratorRequest gains bounded instructions/temperature/top_p/
  response_format/json_schema/prompt_cache_key with cross-field validators;
  GeneratorResult.attempts; MAX_INSTRUCTIONS/MAX_JSON_SCHEMA_BYTES.
- src/slaif_raggedized_helper/model_clients/transport.py (new): bounded
  single-purpose HTTP transport (total-deadline post_json, bounded SSE
  parser with line/event/aggregate byte bounds, no redirects,
  trust_env=False, safe error classes that never echo provider bodies).
- src/slaif_raggedized_helper/model_clients/gateway.py (new): gateway
  Responses adapter (pinned contract f2df0e82), capability-gated envelope
  with store=false default, pre-dispatch local refusals, allowlisted
  terminal/refusal classification, bounded retry loop with explicit attempt
  evidence, gateway_backend_fingerprint (declared identity; runtime
  identity explicitly unverified).
- oap/active, oap/orders/003-a-generator-adapters-and-cache-probes.md,
  oap/reviews/002-resolution.json: committed byte-identical to the
  strategic state (activation bytes preserved; order immutable).

Mechanical repairs applied this round (no semantic change): removed unused
imports, wrapped four over-length lines, added the missing
TransportConfigError import in gateway.py (restores intended safe
route-not-configured behavior; previously a latent NameError), removed a
duplicate Literal import in schema.py.

## Acceptance evidence

1. Gateway adapter route/envelope/capability/URL safety: implemented in
   gateway.py + transport.py (URL validation, no redirects, no body echo,
   pre-dispatch refusals, native cache_prompt/id_slot never present on the
   gateway wire). Evidence: code + unit suite; exact-envelope integration
   assertions NOT yet run (no tests/integration this round) — gap.
2. Output-text parsing and SSE terminal handling: implemented in code;
   the late-body total-deadline path is runtime-proven (see Verification),
   but the SSE delimiter handling carries a known defect and
   split/coalesced/CRLF/UTF-8-split frame proofs are NOT earned — gap
   (defect 1 below).
3. Direct adapter: NOT implemented. Only config/contract models exist
   (destination, policy, template registry, qualification record). The
   native /completion adapter, qualified chatml prompt formatting, stop/
   stop_type/truncated terminal classification, timings metric mapping,
   direct_backend_fingerprint and pre-dispatch purpose refusals remain for
   003-c or later suffixes — gap.
4. Deadlines/bounded retries/ambiguity: post_json total deadline is
   runtime-proven; connect-level retry loop with attempt evidence exists;
   expired-deadline pre-dispatch refusal verified in the control script.
   Known defects: post-dispatch timeout classification and raw-httpx
   escape in post_json (defect 2), terminal queue-signal dropping under a
   full data queue (defect 3) — not fixed this round.
5. Qualification probes: NOT implemented (no probe module, no explicit
   CLI opt-in subcommand) — gap, later suffixes.
6. Controlled local HTTP integration tests: NOT implemented this round
   (tests/integration absent; CI wiring absent). The synthetic loopback
   reproductions below are runtime evidence only and do not satisfy the
   criterion's test-suite requirement — gap.

## Verification

All commands run locally at implementation head f34b9906c7757913104a4ccc9899ee59879d00d4
before this report push; all evidence is synthetic loopback — live model
authorization is NONE and no real trial ran.

- `uv run pytest tests/unit -q` -> 80 passed (existing public
  config/contract suite stays green).
- `python -m unittest discover -s tests/oap` -> 41 tests OK.
- `python oap/bin/check_state.py --repo-root .` -> exit 0; state ACTIVE,
  active 003-a, order found, activation_matches_current_governance=true,
  critical={}.
- `uv run ruff check src tests/unit` -> clean (after the mechanical
  repairs above).
- `python -m compileall -q oap tests` -> OK.
- `uv run raggedized --help` -> OK; `raggedized doctor --config
  config/examples/example-config.json` -> exit 1 with honest issues
  (status issues / config valid / readiness not_ready, MODEL_UNQUALIFIED
  present).
- /tmp/raggedized003-deadline-repro.py -> TransportTimeoutError, elapsed
  0.2019s for a 0.2s TOTAL budget (server sends headers, then a body byte,
  then stalls): the blocked late read refuses inside the shared budget.
- /tmp/raggedized003-control.py -> ALL CONTROLS OK: valid slow body inside
  budget succeeds; valid slow SSE inside budget yields 3 frames (frame
  content corrupted per defect 1); expired deadline refuses pre-dispatch
  as retryable; redirect refused.
- PR #5 implementation-head CI: run 42742664437 on head
  f34b9906c7757913104a4ccc9899ee59879d00d4 -> success, 5/5 jobs (OAP
  tests 3.12/3.13/3.14, Product tests 3.12/3.14).

Known failed or unrun checks recorded honestly:

1. SSE delimiter defect (transport.py SSEStream): during an earlier
   multi-level escape repair the CRLF-strip literal was corrupted; the file
   bytes are a backslash followed by a carriage return inside the string,
   which resolves to the empty string. `line.endswith("")` is therefore
   always true and strips the final character of every parsed line.
   Runtime evidence: the control SSE stream delivers 3 frames but the first
   event name is `response.create` instead of `response.created`, and data
   fields lose their last character. LF splitting itself dispatches frames;
   CRLF handling, coalesced frames and UTF-8-split sequences are NOT proven
   on the current bytes.
2. Post-dispatch timeout classification (per
   audit/003-async-timeout-classification.md, reproduced against this
   code): the dispatched state is set only after response headers.
   Consequences: (a) post_json with the httpx read timeout firing on an
   accepted request escapes as a raw unmapped httpx.ReadTimeout;
   (b) post_json total-deadline expiry after the request was accepted is
   classified retryable=True; (c) both open_stream header-wait cases are
   classified retryable=True. Only positively pre-dispatch
   ConnectError/ConnectTimeout may authorize automatic retry; accepted
   request/no header must be ambiguous (unknown_completion, no retry).
3. Terminal queue-signal dropping: `_put` suppresses queue.Full, so when
   the 32-slot data queue is full, terminal eof/error/closed signals can be
   silently discarded; a slow consumer can lose actual completion/failure
   or leave an orphaned worker.
4. Unrun (no implementation): all direct-adapter contract checks, all
   probe checks, all tests/integration checks (exact envelopes, multi-item,
   malformed/partial/refusal/error/SSE terminals, canary non-disclosure,
   bounded retries, cancel cleanup).

## Documentation impact

No user-facing documentation changed in this checkpoint:
docs/generator-contract.md is new-to-003 and README/TESTING/STATUS/
UNCERTAINTIES updates are deferred to the continuation where the wire
contract stabilizes. config/schema/app-config.schema.json and
model-manifest.schema.json were NOT regenerated although pydantic model
definitions changed (they predate this commit and lack the new fields);
regeneration is deferred to the same continuation to avoid exporting a
transitional schema twice.

## DHA and boundaries

Order DHA: Decision NONE; no CRITICAL entry; no disposition evidence
appended. No merge performed; no next objective chosen; no model/profile/
setting change; no re-signal of the consumed control; no second waiter
started. Strategic activation bytes preserved (oap/active committed
unchanged). Live model authorization NONE retained: no inference, no
downloads, no GPU use, no real gateway traffic.

## Limitations and remaining work

PARTIAL by explicit strategic replan; full 003 acceptance remains
unresolved and this checkpoint is not a merge candidate.

- Defects 1-3 above (SSE delimiters; post-dispatch timeout classification
  including the raw-httpx escape in post_json; terminal signal dropping
  under a full queue) are known, reproduced-or-audited failures of the
  current transport and are the planned focus of 003-b with the concrete
  reproductions and audit findings.
- Direct /completion adapter, qualification probe module and explicit CLI
  opt-in are unimplemented (003-c or later suffixes).
- tests/integration is absent and not wired into CI; criterion 6 is
  unearned.
- config/schema JSON exports are stale relative to the committed pydantic
  models.
- This report does not claim gateway/Responses compatibility beyond the
  pinned-contract parsing implemented here; fixture-level success was not
  used to infer broader compatibility.
- No claim is made about this report commit's future push/CI; the
  post-publication receipt verifies it separately.
