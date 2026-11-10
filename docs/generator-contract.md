# Generator transport/gateway contract (003-b bounded slice)

This document describes the ACTUAL behavior of `model_clients/transport.py` and
`model_clients/gateway.py` as implemented and tested in objective 003-b
(branch `oap/003-generator-adapters-and-cache-probes`, PR 5). It is a contract
excerpt, not the full architecture. The native direct `/completion` adapter and
the qualification probes of objective 003 are NOT RUN here and remain pending
(later 003-c continuation); nothing in this file claims them.

## Pinned wire dialect

The gateway adapter speaks the bounded `POST /v1/responses` contract of the
pinned gateway revision `f2df0e82df8766740d9ac169ea56ffd7a3cb1f1e`
(`ulfe-lmi/slaif-api-gateway`).

Request envelope (exactly these keys, nothing else): `model`, `input`
(message with `input_text` parts and bounded `input_image` parts only when a
trusted resolver materialized authorized images), optional `instructions`,
`max_output_tokens`, optional `temperature`/`top_p`, `store: false`,
optional bounded `text.format` structured output, optional `prompt_cache_key`
(only with the prompt-caching capability), `stream: true` only when the route
advertises Responses streaming. Native llama fields (`cache_prompt`,
`id_slot`, `slot_ids`) cannot appear: the envelope is built from an allowlist
and the integration tests assert their absence on recorded wire bytes.

Base URL contract: `route.base_url` is the gateway root (any reverse-proxy
prefix preserved) or that root ending in `/v1`. The final request path is
always exactly one `/v1/responses` suffix, resolved to an ABSOLUTE URL, so
httpx base-URL path joining is never relied on (the historical
`/v1/v1/responses` duplication bug). Any other base path is refused at
construction time.

Response/SSE dialect (streaming): the pinned gateway emits **data-only** SSE
frames — `data: {json}\n\n` with no `event:` lines. The event discriminator
is the JSON `type` field (`response.created`, `response.output_item.added`,
`response.output_text.delta`, `response.output_text.done`,
`response.output_item.done`, `response.completed`, `response.failed`,
`response.incomplete`, `error`, ...). If an explicit SSE event name IS
present it must agree with the JSON `type`; disagreement fails the stream
closed. `output_index` is an **event-envelope** field on `output_item`
events (required, must equal the observed position). The final
`response.completed` `output` items are authoritative in **array order and do
NOT carry `output_index`** (an index that is genuinely present must not
contradict the position). A trailing `data: [DONE]` is tolerated but never
substitutes for a terminal event.

Terminal item validation (fail-closed): final `message` items must be
`completed` (assistant `output_text` parts, 1..N, or a `refusal` item whose
reason is allowlisted to `content_filter`/`unknown`, otherwise a fixed safe
`refusal` reason) — `in_progress`/`incomplete`/`failed` and unknown part
types are structural errors. `reasoning` items are supported non-text items:
they never contribute answer text, but a non-`completed` terminal status is a
contradictory state and fails the response (never silently skipped).
`function_call` items are an **unsupported action** for this adapter (the
envelope never declares tools) and refuse the whole response, including when
valid text is also present. Duplicate/foreign/out-of-order item IDs,
delta/cumulative mismatches, completed output that disagrees with the
observed stream, and duplicate terminals all fail.

Outcome mapping: only a validated `completed` terminal with usable output
produces `TERMINAL`. `REFUSAL`/`INCOMPLETE`/`FAILED` terminals, EOF without
terminal success, and completed responses without usable text never produce
a success. Provider error bodies are never echoed: only safe status classes
and fixed/allowlisted reasons appear in results; canary bytes in provider
codes, messages, refusal fields or auth exceptions are asserted absent.

## Deadline, cancellation, retry and outcome semantics

- One total absolute deadline (min of request and configured budgets) spans
  connect, write, headers, every body read and every retry. Both normal and
  streaming calls refuse before dispatch if the deadline is already expired;
  a body that drips or stalls late in the budget cannot overrun it.
- Only positively pre-dispatch connect failures (connect timeout / connect
  failure) are retryable, within the finite configured retry policy, and
  retries share the original budget; a budget-consumed pre-dispatch failure
  is refused before any re-dispatch.
- Once a send was attempted, any network failure or timeout leaves
  completion **UNKNOWN_COMPLETION** (non-retryable) — including a server
  that accepted and read the POST then closed without headers, in both the
  httpx-timeout and total-deadline forms, normal and streaming. The
  integration tests assert the server recorded exactly one accepted request
  and that no duplicate attempt followed.
- The streaming worker rechecks the absolute deadline and cancellation at
  its dispatch boundary: an exhausted budget or an already-cancelled
  request never dispatches a late POST (regression: controlled 60ms
  worker-start delay against a 25ms budget refuses pre-dispatch and the
  cancelled worker never reaches the server). Valid slow calls inside the
  budget still succeed.
- The bounded (32-slot) data queue is cancellation-aware: terminal/error/EOF
  signals are never dropped when full; queue saturation is proven by
  observing exact full capacity before consumption. Closing a consumer
  cancels only its owned request and stops its worker; no orphaned threads.

## Safe configuration, secrets, proxy and redirect behavior

- `http`/`https` destinations only; embedded credentials (userinfo),
  query/fragment strings are refused at config/transport construction.
- The API key exists only in the `Authorization` header; it is asserted
  absent from recorded wire bodies.
- Redirects are never followed (a 3xx response is a safe refusal, the
  `Location` is never contacted); ambient HTTP proxy environment is never
  inherited (`trust_env=False`) — asserted with a proxy sink that must stay
  empty; no cookie jar, no cross-call connection reuse.
- Response bodies are byte-bounded (2 MiB default), SSE events 256 KiB and
  streams 16 MiB by default; oversize lines/events/streams, invalid UTF-8
  and truncated frames fail with safe fixed messages.

## Declared backend identity

`gateway_backend_fingerprint` hashes the adapter kind, dialect, pinned
contract commit, declared model, the **credential-free configured endpoint
identity** (normalized `base_url`: scheme, host, port and API segment — not
just the hostname), timeout and capability snapshot, plus the explicit
`runtime_identity: "unverified"` marker. Request IDs and answer text do not
change it; endpoint port/scheme/model changes do. The deployed runtime/GGUF
identity remains explicitly unverified in this slice.

## Exact test commands (offline, synthetic)

```sh
uv sync --locked
uv run pytest tests/integration -q     # transport + gateway loopback suites
uv run pytest tests/unit -q            # foundation regressions
python3 -m unittest discover -s tests/oap -v
python3 oap/bin/check_state.py --repo-root .
uv run ruff check src tests/unit tests/integration
```

The product CI job (`.github/workflows/oap.yml`, Python 3.12/3.14) runs the
integration suite from a clean locked install alongside unit tests and
lint (see docs/CI.md).

## Supported/proven vs NOT RUN / pending (003-c)

Proven in this slice (synthetic loopback + pinned-dialect fixtures): wire
path resolution, envelope allowlist, deadline/retry/UNKNOWN semantics, SSE
byte-level parsing, bounded backpressure and cancellation, pinned
completed/refusal/error dialects, canary safety, identity stability.

NOT RUN / pending: the native direct `/completion` adapter and its
cache/slot behavior, live gateway/model traffic, qualification probes, and
hardware evidence. The whole of objective 003 remains unresolved until that
scope is proved; this slice is not acceptance or readiness for objective
003, and the certifi (MPL-2.0) dependency gate recorded in
THIRD_PARTY_NOTICES remains an open human question.
