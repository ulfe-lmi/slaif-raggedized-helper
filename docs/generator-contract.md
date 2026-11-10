# Generator transport/gateway/native contract (003 slice)

This document describes the ACTUAL behavior of `model_clients/transport.py`,
`model_clients/gateway.py` and `model_clients/direct.py` as implemented and
tested in objective 003 (branch
`oap/003-generator-adapters-and-cache-probes`, PR 5; the 003-b
transport/gateway slice, the 003-c protocol-validation repair, the
003-d structural validation closure and the 003-e private native
`/completion` adapter). It is a
contract excerpt, not the full architecture. The qualification probes and
live-target evidence of objective 003 are NOT RUN here and remain pending
for separately finalized continuations of objective 003; nothing in this
file claims them.

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

Capability gates (default deny, A13): optional controls are usable only
when the configured route explicitly advertises the capability —
streaming, vision (route AND declared model), `text.format` structured
output and `prompt_cache_key`. The gates honor BOTH the actual input
shape and the explicit minimum requirement: a constructor-validated
request may carry `JSON_MODE` or `PROMPT_CACHING` in
`required_capabilities` while sending no `response_format` or
`prompt_cache_key` at all (003-h). An unqualified requirement refuses
locally with zero HTTP — a model capability declaration alone is not
route support; a qualified requirement alone does not invent an output
format or cache key (the pinned minimal envelope is sent unchanged).

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

## Native direct `/completion` adapter (003-e)

`model_clients/direct.py` (`DirectNativeGenerator`) speaks the pinned
**non-OAI-compatible** native dialect of `ggml-org/llama.cpp` server
reference commit `3b4d6ab3f79651935fba1dd93732f29022a7f5f5`
(`tools/server/README.md` plus the pinned `server-task.cpp` /
`server-context.cpp` / `server-common.cpp` excerpts). The reference
revision is a dialect reference, **not** the unknown deployed build; this
slice pins implementation semantics without live claims. The adapter
reuses the 003-b bounded transport (same deadline, privacy, redirect,
retry and cleanup behavior) with the pinned native endpoint resolution
(`/apply-template`, `/completion` at the configured server base path;
any reverse-proxy prefix preserved; no other native path resolvable —
no arbitrary-destination/path proxy).

### Materialization policy (refusal before any network work)

The client materializes only when ALL of the following hold, rechecked at
call time (a refusal performs zero requests):

- `direct_generation.mode == "offline_diagnostic"` with the explicit
  `private_trusted` policy declaration;
- a private/loopback `destination.base_url` (config-validated: private IP
  / localhost only, no credentials, no query/fragment);
- the declared `model` identity (the operator-declared model/alias of the
  private build; absent = unknown, never guessed);
- a `template_qualification` record matching the declared `chat_template`
  identity (see below);
- the explicit finite operator `max_output_tokens` and
  `deadline_seconds` (a `None` limit is not permission for an uncapped
  caller allowance; config validation enforces this for the materialized
  mode and the client rechecks it).

Purpose/shape gates (architecture A22, SECURITY S03): ONLY the
`annotation` purpose is supported — `answer` is refused (this adapter is
never an answer fallback after a gateway failure/denial), and every
visual/image request (purpose, `images` or the `VISION` capability) is
refused locally before dispatch until a qualified native image
serializer exists. Streaming control is refused (non-stream slice).
Prompt caching (`prompt_cache_key` / `PROMPT_CACHING`) requires the
tested `cache_prompt` capability; the application-level key never appears
on the native wire (the documented native cache identity is the rendered
prompt prefix, plus the slot). Requested JSON/schema controls are default
deny and require the tested `json_grammar_tested` capability, refusing
locally with zero dispatch while unqualified. The gate honors BOTH the
actual input shape (`response_format` `json_object`/`json_schema`) and
the explicit minimum requirement (`JSON_MODE` in
`required_capabilities`): a constructor-validated request may require
the capability while sending no format field at all, and a model
capability declaration alone cannot prove serving-build support. A
qualified `JSON_MODE` requirement alone does not invent an output
format. The output budget uses REFUSAL semantics
consistent with the gateway: `request.max_output_tokens` above the
operator limit refuses before dispatch; the accepted request's value is
exactly the effective `n_predict` (no silent clamp).

### Template rendering: server-rendered, no local rendering

`POST /apply-template` sends exactly `{"messages": [...]}` (no inference,
no other keys): the trusted `instructions` become the single leading
`system` message and each ordered `TextItem` (untrusted reference data)
becomes its own `user` message, preserving item boundaries and order. The
server renders with its loaded template (model-metadata default with
Jinja enabled on the pinned reference, or an operator-declared template)
and returns `{"prompt": str}`. The client performs NO local template
rendering, never guesses special tokens, and enforces no arbitrary local
name allowlist: the declared `chat_template` identity is `None` (the
model-metadata default) or a plain token (pinned built-in or operator
Jinja template); unknown templates are refused by the SERVER itself and
that 400 maps to the safe typed failure `template application refused
(HTTP 400)`. The config `PINNED_LLAMA_BUILTIN_CHAT_TEMPLATES` tuple is the
actual built-in reference list copied from the pinned upstream source
(including `mistral-v1/v3/v7`, `phi3`, `phi4`; the previously pinned false
five-name set is corrected), documented for operator convenience, not a
client-side allowlist. Template qualification is established solely by the
qualification record (server rendering against the tested build, or
pinned-upstream verification) — never by magic substring/delimiter
scanning of rendered text. The config-time rule that the declared template
IDENTITY token must not embed the gateway-dialect closing tag the old
hand-written formatter invented as a turn delimiter (repository history,
not a pinned native primary-source fact) is an identity-token constraint
on the configured name only. Literal technical content containing that
sequence (constructed in the regression fixture as
`chr(60)+"/tool_call"+chr(62)`), and Markdown fence data, pass through the
rendered prompt to `/completion` byte-for-byte unchanged (no blanket
rejection, no stripping); both remain preserved data, not delimiters.

### `/completion` envelope and supported controls

Exactly these keys (nothing else): `prompt` (the rendered prompt string),
explicit `n_predict`, `stream: false`, optional caller-set
`temperature`/`top_p`, the documented `json_schema` grammar control
(the caller's exact schema for `json_schema`, and `{}` — the pinned
reference's any-JSON form — for the `json_object` semantic; `{}` is any
JSON, NOT a stronger object-shape guarantee), `cache_prompt: true` ONLY
when the `cache_prompt` capability was tested on the build, and singular
`id_slot` ONLY when the slot capability was tested (configured slot;
invented `slot_ids` and any untested control cannot appear). The JSON/
schema controls are default deny: a requested `json_object`/`json_schema`
control (inferred from the actual input shape) or an explicit `JSON_MODE`
minimum requirement (which a valid request may carry with no format
field at all) is admitted only when the build's `json_grammar_tested`
capability was actually tested — a documented field is not tested grammar
support, a model declaration alone does not prove serving-build support,
and template qualification alone does not prove it — so an unqualified
request is refused locally before `/apply-template` or `/completion`
(zero dispatch). A qualified capability requirement without a selected
format sends the pinned minimal envelope unchanged (no invented
`json_schema`). Unsupported requested behavior is refused locally before
the envelope is built — never silently ignored.

### Outcome mapping (fail-closed, pinned dialect)

Only `stop: true` + `truncated: false` + `stop_type: "eos"` + usable
nonempty `content` produces TERMINAL. Everything else is a non-success:
`stop_type: "limit"` (n_predict reached), `truncated: true` (context
exceeded), `stop_type: "none"` (still generating) and `stop != true` map
to INCOMPLETE; a missing/invalid terminal reason (null/non-string/unknown
`stop_type`), a non-string `content`, an explicit server `error` object,
and an UNQUALIFIED `stop_type: "word"` terminal (this adapter sends no
stop strings) map to FAILED. Invalid UTF-8/JSON (including the
interpreter integer digit-limit rejection of oversized JSON integers,
which the native parse guards with the same narrow
`ValueError`/`RecursionError` boundary as the gateway non-stream parse)
and HTTP 4xx/5xx produce safe typed failures. Provider bodies, messages
and exception text are never echoed (canary-tested).

### Metric mapping (pinned source; unknowns stay null)

Mapped only from the dialect's actual reported fields:
`usage.input_tokens` <- top-level `tokens_evaluated`
(`slot.task->n_tokens()`, the task's total prompt tokens);
`usage.prefill_tokens` <- `timings.prompt_n` (`n_prompt_processed`,
prompt tokens actually evaluated for this request — never substituted
with the total/submitted count); `usage.cache_hit_tokens` <-
`timings.cache_n` (`n_prompt_cached`); `usage.output_tokens` <-
`timings.predicted_n` (`n_gen`). Top-level `tokens_cached` is the SLOT's
resulting `prompt.n_tokens()` (prompt + generated) — NOT the cache hits
of this request — and is never substituted for `timings.cache_n`; the
synthetic 100-submitted (10 new / 90 cached) + 12-generated case with
`tokens_cached` reporting 112 preserves all four facts distinctly
(unit- and loopback-tested). Counters are validated as finite
nonnegative numbers without accepting bool/NaN/infinity. Dialect
consistency: under the supported dialect the task's total prompt tokens
equal newly processed plus cached (`tokens_evaluated == prompt_n +
cache_n`); a contradictory reported breakdown (e.g. 100 input with 90
new + 90 cached) cannot prove evaluated work or caching, so
`usage.prefill_tokens`/`usage.cache_hit_tokens` are withheld (null)
while the directly reported task total keeps its own provenance; the raw
contradictory values are not carried in the result. Model timings map
only from `timings.prompt_ms`/`timings.predicted_ms` (ms -> s) with
correct quantities: `timings.prefill_seconds` <- `prompt_ms/1000` (the
reported PROMPT PROCESSING duration — not TTFT) and
`timings.decode_seconds` <- `predicted_ms/1000` (the reported
token-generation duration); `timings.total_seconds` <- the two phase
durations summed IN SECONDS (`prompt_ms`/1000 + `predicted_ms`/1000) only
when both model phases were reported — an explicitly model-scoped derived
model-work total, never caller elapsed time. Safe arithmetic follows safe
input conversion: each phase is first individually validated as a finite
nonnegative millisecond value, then the derived sum is computed in
seconds with a finite check, so individually finite extreme phases (both
`1e308` ms -> `1e305` s each) yield a finite derived total (`2e305` s)
instead of an overflowing millisecond sum, and an unrepresentable derived
total would be explicitly withheld (null) while the individually valid
phases are retained (no `OverflowError`/`ValidationError` out of
`generate()`, no arbitrary physical-time cutoff). A measured reported 0ms
is a known zero (0.0), never null, and a withheld phase never discards
the other reported phase. `ttft_seconds` is NEVER set by this adapter: the pinned native
dialect reports no first-token measurement, and a lower bound is not an
observed first-token time — TTFT stays unavailable unless a supported
backend actually reports or measures it. Numeric conversion/arithmetic
checks reject bool/NaN/Inf and unrepresentable values safely (a reported
`prompt_ms` of 10**400 is unavailable data, not an `OverflowError` out
of `generate()`), narrowly at the input conversion boundary. Caller wall
time never mixes in; undocumented/old-build fields stay null. The
declared identity
(`direct_backend_fingerprint`) hashes adapter kind, dialect, reference
commit, declared model, credential-free endpoint identity, declared
template identity + build evidence, operator limits and the capability
snapshot, plus `runtime_identity: "unverified"`; request IDs and response
text never change it.

## Bounded qualification probe (003-h)

`model_clients/probes.py` + the `raggedized probe` CLI subcommand run the
bounded repeated-parent qualification experiment. The probe is an
EXPLICIT opt-in: import, `--help`, `doctor`, readiness and default tests
never dispatch a probe; only the probe subcommand with explicit finite
budgets and an actually configured mode does. Neither mode may fall back
to the other after a denial (the gateway path and the private
offline-diagnostic direct path are independent).

### Public CLI contract

```
raggedized probe --config PATH --mode {gateway,direct}
    --deadline-seconds S --max-dispatches N --max-output-tokens-total T
    [--expected-output-a sha256:<64hex>] [--expected-output-b sha256:<64hex>]
    [--output PATH]
```

- `--config`: the strict deployment configuration. `--mode gateway`
  requires `generator.route`; `--mode direct` requires a fully
  materialized `direct_generation` offline-diagnostic policy (private
  destination + `private_trusted` + declared model + template
  qualification + explicit finite operator limits).
- `--deadline-seconds`: ONE overall wall-time budget spanning the whole
  experiment — both paired requests, native template work and every
  adapter retry. A per-call allowance never resets it; the transport
  boundary rechecks it before every invocation.
- `--max-dispatches`: the total call/attempt allowance. One allowance is
  reserved BEFORE every transport invocation (model dispatch, template
  work, failed connects). Ambiguous dispatched work is conservatively
  counted as spent and never replayed; retries and template requests
  cannot bypass it.
- `--max-output-tokens-total`: the total output-token allowance across
  the pair (>= 2). Each request receives the deterministic even half
  (`total // 2`), so the pair's summed allowance never exceeds the total.
- `--expected-output-a/b`: operator-supplied `sha256:` digests for an
  available EXACT expected-output check (digest equality only; an equal
  digest does not establish truth).
- `--output`: write the evidence document to a file (default stdout).
- Credentials resolve ONLY through the configured safe operator
  reference (`generator.api_key_ref` -> `secrets`, env or file kind).
  The command line, reports, errors and logs never carry the value; an
  absent reference refuses before dispatch (exit 2).

Exit codes: `0` complete (both paired requests resolved), `1` explicit
not-run/incomplete with published evidence (finite budget or adapter
preflight stop), `2` usage/config error (invalid budgets, mode not
configured, invalid config, absent credential reference) — always zero
dispatches.

Safe synthetic example (owned loopback gateway fixture, synthetic env
credential reference):

```sh
raggedized probe --config probe-config.json --mode gateway \
    --deadline-seconds 30 --max-dispatches 8 --max-output-tokens-total 32 \
    --output probe-evidence.json
```

### Experiment semantics (repeated parent)

- One constant bounded synthetic parent plus explicit deterministic
  child suffixes form two phases (annotation purpose, plain text).
  Phases are labeled `first-call` / `second-call`; `cold_state` is
  `unknown` because no cache reset/isolation control is authorized or
  verified — the probe never calls the first call physically cold, never
  performs a reset, and never asserts cache isolation from a client key
  alone.
- Exact identities are recorded: dialect with pinned commit, declared
  (unverified) model, an opaque endpoint DIGEST (never the URL), template
  identity/build/method and capability snapshots (direct), slot control
  state, and the cache-control kind with a fingerprinted parent-derived
  key.
- Native cache/slot controls are used only where qualified
  (`cache_prompt_tested` / `slot_tested`); the gateway sends
  `prompt_cache_key` only on a route that advertises prompt caching.
- Input material enters evidence only as fingerprints and lengths, never
  raw text; arbitrary response text never enters evidence — only a
  response-text digest, the terminal outcome, the available exact
  expected-output check result, and the adapter's safe reason.
- Output correctness is explicitly limited: terminal validity and
  available exact expected-output checks are recorded separately from
  semantic model quality (`model_quality: not_assessed`). Equal answers
  do not establish truth and speed does not establish caching.

### Evidence and budget accounting

The safe structured document (`probe: repeated-parent, version: 1`)
carries: budgets + measured probe-level elapsed time; identities;
experiment fingerprints/lengths/phase labels; per-phase records
(outcome, safe error, `adapter_reported_cycles` — the adapter's own
cycle count, NOT an authoritative dispatch count —, response-text digest,
expected-output check, reported usage/timings with missing values null,
probe-level wall time); the transport-boundary accounting
(`attempted_calls`, `calls_by_kind` separating model dispatches from
non-inference template work, `responses_received`,
`ambiguous_dispatches`, `pre_dispatch_failures`,
`remaining_dispatches`); and the cache evidence. The cache conclusion is
driven ONLY by reported evaluated metrics of the second phase
(`cache_hit_tokens` measured zero -> `no_cache_hit_reported`, > 0 ->
`cache_hit_reported`, absent/invalid -> `metrics_unavailable`, no
qualified control -> `no_cache_control`, second phase not run ->
`not_run`); submitted input tokens or faster wall time cannot substitute
for evaluated work, and the gateway's absent prefill metrics stay
unavailable. No endpoint URL, authorization header, secret reference
value, configured instructions, rendered prompt, source item, image
material, raw response text or provider error body ever appears.

The probe proves executable bounded tooling and synthetic HTTP
composition; real target/hardware/cache/quality qualification remains
NOT RUN (order 003-h live authorization: NONE).


## Exact test commands (offline, synthetic)

```sh
uv sync --locked
uv run pytest tests/integration -q     # transport + gateway + native + probe composition loopback suites
uv run pytest tests/unit -q            # foundation + native mapping + probe budget regressions
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

Proven for the 003-e native slice (synthetic loopback + pinned-dialect
fixtures): materialization/purpose/shape refusals with zero dispatch,
exact `/apply-template` message serialization (trusted system / ordered
user data), literal-marker content forwarded unchanged to `/completion`
(no substring scanning), exact minimal and controlled `/completion`
envelopes (json_schema grammar forms, tested-only cache_prompt/id_slot,
invented controls impossible), refusal-vs-clamp output budget, one total
deadline spanning template work + generation + retries (pre-inference
expiry refuses the dispatch), finite pre-dispatch-only retry, unknown
completion non-retryable, the full stop-terminal matrix
(limit/truncated/still-generating/not-stopped/empty-content never
TERMINAL; unqualified stop-word and invalid reasons FAILED), the synthetic
distinct-facts metric case (100/10/90/12 with tokens_cached 112),
bool/NaN/infinity and malformed-counter refusal, canary safety and
declared-identity stability.

Proven for the 003-f native corrections (synthetic loopback +
pinned-dialect fixtures; five controlled-HTTP vector experiments):
correct metric quantities with provenance (reported prefill/decode ms
carried as `prefill_seconds`/`decode_seconds` with the model-scoped
phase total, TTFT unavailable rather than prefill-aliased), a measured
reported 0ms preserved as a known zero without discarding the other
phase, safe unrepresentable/overflow numeric handling (10**400
`prompt_ms` -> unavailable, no exception out of `generate()`),
default-deny admission of the requested JSON/schema controls (zero
dispatch for unqualified `json_object`/`json_schema`, inferred from the
actual input shape) with qualified positive controls preserving the
pinned `{}` any-JSON and exact-schema semantics, and contradiction
withholding of a contradictory reported evaluated/cache breakdown
(100 input with 90 new + 90 cached).

Proven for the 003-g native boundary closure (synthetic loopback +
pinned-dialect fixtures; the independent eight-vector owned-HTTP
observations): safe finite phase-total arithmetic over real loopback
(both reported phases `1e308` ms — individually finite, converting to
finite `1e305` s — with the derived total computed in seconds as a finite
`2e305` s, no `OverflowError`/`ValidationError` out of `generate()`, TTFT
still unavailable, the both-phases-zero known-zero positive control
retained) and explicit required `JSON_MODE` capability admission (zero-
dispatch typed refusal for the constructor-validated required-
capability-only request on an untested build — a model declaration alone
never proves serving-build support; qualified positive control dispatching
once per path without inventing an output format; ordinary
TEXT/no-format success preserved; the five original native vectors and
their oracles unchanged).

Proven for the 003-h bounded probe closure (installed-CLI subprocess
composition over real loopback HTTP, synthetic fixtures only): explicit
opt-in with finite overall deadline, call/attempt and total output-token
budgets; the single experiment deadline spanning both paired requests,
template work and retries (per-call allowances never reset it); call
allowance reserved before every transport invocation with ambiguous
dispatched work spent and never replayed and finite retries unable to
bypass the budget; exact request counts/order/control payloads on the
wire (stable parent-derived cache key, tested-only native
cache_prompt); preflight refusals and invalid config/credential
absences at zero dispatch; missing metrics null (no synthetic zero);
digest-only expected-output match/mismatch; unknown-completion
no-replay; no implicit dispatch on import/help/doctor/missing opt-in;
and safe structured evidence carrying no endpoint URL, credential, raw
prompt or response text or provider error. Also proven this round: the
gateway explicit-minimum capability admission (zero-HTTP refusal of
required JSON_MODE/PROMPT_CACHING on an unqualified route, qualified
minimum-only positive controls without invented format/key, ordinary
TEXT preserved).

NOT RUN / pending: live-target qualification evidence (the pinned
reference is not the unknown deployed build), direct caching
effectiveness on a real build, live gateway/model traffic and hardware
evidence — the probe tooling is executable and its synthetic HTTP
composition is proved, but every real trial remains NOT RUN. The whole
of objective 003 remains unresolved until that scope is proved; this
slice is not acceptance or readiness for objective 003, and the
certifi (MPL-2.0) dependency gate recorded in THIRD_PARTY_NOTICES
remains an open human question.
