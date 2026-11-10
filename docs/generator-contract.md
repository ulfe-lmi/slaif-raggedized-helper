# Generator transport/gateway contract (003 slice)

This document describes the ACTUAL behavior of `model_clients/transport.py` and
`model_clients/gateway.py` as implemented and tested in objective 003
(branch `oap/003-generator-adapters-and-cache-probes`, PR 5; the 003-b
transport/gateway slice, the 003-c protocol-validation repair and the
003-d structural validation closure). It is a
contract excerpt, not the full architecture. The native direct `/completion`
adapter and the qualification probes of objective 003 are NOT RUN here and
remain pending for separately finalized continuations of objective 003;
nothing in this file claims them.

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
events (required, must equal the observed position); on `output_text.delta`,
`output_text.done` and `content_part.*` events a supplied `output_index` must
likewise equal the item's observed position, and a supplied `content_index`
must name a part already added to the item (the implicit part is 0 when the
field is absent). All event coordinates pass one shared decoder where key
**absence and present-null are distinct**: an absent optional coordinate
keeps the implicit form, a present `null` (or any non-integer)
`output_index`/`content_index` is malformed and fails the stream, and
`content_index` has no meaning at the `output_item.done` boundary, where it
is malformed whenever present. A message may carry **multiple bounded
`output_text` parts**; explicit parts are numbered `0,1,2,...` in the order
they are `content_part.added` (a gap, rename or out-of-order coordinate is
refused), each part's cumulative text is reconciled independently against
its own deltas, and at the item's done boundary the explicit part
coordinates are bound to their actual ordered final part positions (an
observed part cannot disappear because the final concatenated text happens
to match), so the answer text preserves the final array part order
(parts concatenated in order). Each part's own events are validated when
present (part added with text, part done before text done, part text
disagreeing with the deltas all fail), and the `output_item.done` boundary
is the item's terminal transition: an explicitly declared part that never
receives its own `output_text.done`/`content_part.done` before the item's
done is closed by that parent done and remains valid provided the
part-to-final-position binding (part count and per-part text) holds at the
item boundary; the full `added -> deltas -> text done -> part done`
sequence per part is the pinned gateway shape, not a client-side
requirement. A non-string `output_item.added` `item.type` (object/array
included) is a structural error at the added boundary (guarded before set
membership, never a raw exception). The final `response.completed` `output` items
are authoritative in **array order and do NOT carry `output_index`** (an
index that is genuinely present must not contradict the position). A
trailing `data: [DONE]` is tolerated but never substitutes for a terminal
event.

Terminal and event validation (fail-closed): terminal events
(`response.completed`/`response.failed`/`response.incomplete`) must carry a
valid nonempty response ID consistent with the observed events; a missing or
malformed terminal ID fails closed instead of being ignored. Item type/identity is **frozen from `output_item.added` through
`output_item.done` and the final `output` array**: only `message` and
`reasoning` items enter the stream lifecycle (an added `function_call` or
any other type is an unsupported action, refused at the added boundary), a
reasoning item cannot become a message with the same ID (or vice versa) at
the done or final boundary, and text events belong to supported message
parts only. A `message`
`output_item.done` must carry a terminal status (`completed` or `refusal`): a
nonterminal status followed by a completed final message is contradictory,
never success; a `reasoning` `output_item.done` must be `completed` (a
nonterminal done status is contradictory even when the final output later
shows it completed). Item completion is **latched**: a duplicate
`output_item.done`, or any delta/text-done/content-part event after the
item's done, is refused. A `delta` must be a string and a cumulative `text` a string;
an array delta followed by empty done/item data and an authoritative terminal
text is a malformed stream, never a salvaged successful answer, and a later
valid final payload cannot erase an observed protocol error. A non-string
final `message.status` (e.g. `{}` or `[]`) is guarded before set membership:
a structural error, never a `TypeError`. Event JSON with excessive nesting
(beyond the interpreter recursion limit inside the transport byte bounds)
fails as a malformed event payload. Final `message` items must be
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
observed stream, duplicate terminals, duplicate/late part lifecycle events
(part added with text, part done before text done, part text disagreeing
with the deltas, delta after part done, unknown content part), and part
events targeting unknown or non-message items all fail.

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
- Response bodies are byte-bounded by default to 2,000,000 bytes (decimal,
  `DEFAULT_MAX_RESPONSE_BYTES`), SSE events to exactly 262,144 bytes (256
  KiB) and streams to 16,000,000 bytes (decimal,
  `DEFAULT_MAX_STREAM_BYTES`); oversize lines/events/streams, invalid
  UTF-8 and truncated frames fail with safe fixed messages. The response
  and stream defaults are the decimal literals 2,000,000 and 16,000,000,
  not 2/16 MiB.

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

## Supported/proven vs NOT RUN / pending

Proven in this slice (synthetic loopback + pinned-dialect fixtures): wire
path resolution, envelope allowlist, deadline/retry/UNKNOWN semantics, SSE
byte-level parsing, bounded backpressure and cancellation, pinned
completed/refusal/error dialects, malformed type/ID/coordinate/status
refusals with canary-safe fixed reasons, valid single-part, multi-part
(exact per-part text) and multi-message streams, part lifecycle
violations, excessive-JSON-nesting refusals, the deterministic zero-dispatch
deadline boundary, canary safety, identity stability; 003-d: supplied-null
versus absent coordinate handling, bounded sequential content-part
numbering and part-to-final-position binding (gap/rename/disappeared-part
refusals), item type/identity freeze at added/done/final, latched item
completion (duplicate/late events refused), per-type terminal done status
(reasoning nonterminal done refused; completed reasoning plus message
streams valid with message text only), non-string/unhashable added
item types refused at the added boundary, the documented
item-done-closes-open-parts part lifecycle, and actual-HTTP regressions
for all six strategic structural variants plus the incremental
review observations.

NOT RUN / pending: the native direct `/completion` adapter and its
cache/slot behavior, live gateway/model traffic, qualification probes, and
hardware evidence. The whole of objective 003 remains unresolved until that
scope is proved; this slice is not acceptance or readiness for objective
003, and the certifi (MPL-2.0) dependency gate recorded in
THIRD_PARTY_NOTICES remains an open human question.
