"""Private trusted OFFLINE native llama.cpp ``/completion`` adapter (OAP 003-e).

Wire dialect (pinned reference, NOT the unknown deployed build):
``ggml-org/llama.cpp`` commit ``3b4d6ab3f79651935fba1dd93732f29022a7f5f5``,
``tools/server/README.md`` and the pinned ``server-task.cpp`` /
``server-context.cpp`` / ``server-common.cpp`` excerpts:

- ``POST /apply-template``: ``{"messages": [...]}`` (the same message shape
  as ``/v1/chat/completions``) is rendered by the SERVER's loaded chat
  template (model-metadata default with Jinja enabled, or an
  operator-declared template); the response is ``{"prompt": str}``. No
  inference is performed; the client performs no local template rendering
  and never guesses special tokens.
- ``POST /completion`` (non-OAI-compatible native form): one bounded
  ``prompt`` string, explicit ``n_predict``, ``stream: false`` and only the
  supported optional controls — ``temperature``/``top_p`` (caller-set),
  documented ``json_schema`` grammar (``{}`` = any JSON for the
  ``json_object`` semantic), ``cache_prompt: true`` only when the
  ``cache_prompt`` capability was tested on the build, and singular
  ``id_slot`` only when the slot capability was tested (invented
  ``slot_ids`` never appear).

Purpose/shape policy (architecture A13/A22, SECURITY S03): materialized
only under the explicit ``offline_diagnostic`` policy with the
``private_trusted`` declaration and a private/loopback destination, and
only for the ``annotation`` purpose. ``answer`` purpose and every
visual/image request are refused locally before any network work (no
qualified native image serializer exists yet; unknown vision/native
features remain explicit refusal). This adapter is never an answer
fallback after a gateway failure/denial.

Optional-control admission (default deny): the requested JSON/schema
controls are admitted only when the serving build's
``json_grammar_tested`` capability was actually tested. Both the ACTUAL
INPUT SHAPE (``response_format`` ``json_object``/``json_schema``) and the
EXPLICIT MINIMUM REQUIREMENT (``required_capabilities`` containing
``JSON_MODE``) are honored independently: a constructor-validated
request may require ``JSON_MODE`` while sending no format field at all.
A documented field is not tested grammar support, a model capability
declaration alone cannot prove serving-build support, and template
qualification alone does not prove it: an unqualified JSON requirement
or request is refused locally BEFORE ``/apply-template`` or
``/completion`` (zero dispatch), while qualified controls preserve the
pinned request semantics (``{}`` is any JSON in the native reference —
not a stronger object-shape guarantee). A qualified ``JSON_MODE``
requirement alone does not invent an output format: with no format
selected the pinned minimal envelope is sent unchanged.

Outcome mapping (fail-closed, pinned dialect): only ``stop: true`` +
``truncated: false`` + ``stop_type: "eos"`` + usable nonempty ``content``
produces TERMINAL. ``stop_type: "limit"`` (n_predict reached),
``truncated: true`` (context exceeded), ``stop_type: "none"`` (still
generating), ``stop != true`` and a missing/invalid terminal reason never
become TERMINAL. Because this adapter sends no ``stop`` strings, a
``stop_type: "word"`` terminal is an unqualified state and fails. Invalid
encoding/JSON/fields or an explicit server error produce a safe typed
failure; provider bodies, messages and exception text are never echoed.

Metric mapping (pinned source; fields that are unknown on an old build
stay null, never invented):

- ``usage.input_tokens``      <- top-level ``tokens_evaluated``
  (``slot.task->n_tokens()``: the task's total prompt tokens);
- ``usage.prefill_tokens``    <- ``timings.prompt_n``
  (``n_prompt_processed``: prompt tokens actually evaluated for this
  request — not substituted with the total/submitted count);
- ``usage.cache_hit_tokens``  <- ``timings.cache_n`` (``n_prompt_cached``:
  prompt tokens reused from the KV cache);
- ``usage.output_tokens``     <- ``timings.predicted_n`` (``n_gen``);
- top-level ``tokens_cached`` is the SLOT's resulting ``prompt.n_tokens()``
  (prompt + generated), NOT the cache hits of this request: it is never
  substituted for ``timings.cache_n``. Counters are validated as finite
  nonnegative numbers without accepting bool/NaN/infinity. Under the
  supported dialect the task's total prompt tokens equal newly processed
  plus cached (``tokens_evaluated == prompt_n + cache_n``); a
  contradictory reported breakdown (e.g. 100 input with 90 new + 90
  cached) cannot prove evaluated work or caching, so the evaluated/cache
  breakdown is withheld (null) while the directly reported task total
  keeps its own provenance.

``timings`` maps only from the dialect's own reported fields with correct
quantities and units (ms -> s); caller wall time stays separate and is
never mixed in:

- ``ttft_seconds`` is NEVER set by this adapter: the pinned native
  dialect reports no first-token measurement, and the prompt-processing
  duration is a lower bound, not an observed first-token time. TTFT
  stays unavailable (null) unless a supported backend actually reports
  or measures it.
- ``prefill_seconds`` <- ``timings.prompt_ms``/1000 (the reported PROMPT
  PROCESSING duration — not TTFT);
- ``decode_seconds`` <- ``timings.predicted_ms``/1000 (the reported
  token-generation duration);
- ``total_seconds`` <- the two phase durations summed IN SECONDS
  (``prompt_ms``/1000 + ``predicted_ms``/1000) ONLY when both model
  phases were reported: an explicitly model-scoped derived model-work
  total, never caller elapsed time. The safe input conversion happens
  first (each phase is individually validated finite nonnegative
  milliseconds), and the derived sum is then computed in seconds with a
  finite check: individually finite extreme phases (for example both
  ``1e308`` ms) convert to finite seconds (``1e305`` each) and the
  derived total stays finite (``2e305`` s) instead of overflowing the
  millisecond sum; if a derived total were ever unrepresentable it is
  explicitly withheld (null) while the individually valid phase values
  are retained. No ``OverflowError``/``ValidationError`` or nonfinite
  total may escape ``generate()``; there is no arbitrary physical-time
  cutoff and no whole-function exception blanket.

A measured reported ``0ms`` is a known zero (0.0), never null; a missing
or invalid field stays unavailable and must not discard the other
reported phase. Numeric conversion checks reject bool/NaN/Inf and
unrepresentable values safely (a reported ``prompt_ms`` of 10**400 is
unavailable data, not an ``OverflowError`` out of ``generate()``); the
handling is narrow at the input conversion boundary, not a
whole-function exception blanket.
"""

from __future__ import annotations

import json
import math
import time
from collections.abc import Callable

from ..config import DirectGenerationConfig
from ..schema import (
    Capability,
    CompletionOutcome,
    GeneratorPurpose,
    GeneratorRequest,
    GeneratorResult,
    ModelIdentity,
    TimingMetrics,
    UsageMetrics,
    fingerprint,
)
from .transport import (
    GatewayTransport,
    TransportConfigError,
    TransportConnectError,
    TransportError,
    TransportRefusedError,
    TransportTimeoutError,
    TransportTruncatedError,
)

NATIVE_REFERENCE_COMMIT = "3b4d6ab3f79651935fba1dd93732f29022a7f5f5"
NATIVE_REFERENCE_SOURCE = "ggml-org/llama.cpp:tools/server/README.md"
APPLY_TEMPLATE_PATH = "/apply-template"
COMPLETION_PATH = "/completion"
_MAX_ERROR_TEXT = 200

# stop_type vocabulary of the pinned reference (server-task.cpp
# stop_type_to_str). "none" means generating, not stopped.
_STOP_EOS = "eos"
_STOP_WORD = "word"
_STOP_LIMIT = "limit"
_STOP_NONE = "none"


def _safe_error(message: str) -> str:
    return message[:_MAX_ERROR_TEXT]


def _nonneg_int(value: object) -> int | None:
    """Strict nonnegative integer: bool, NaN/Inf floats and negatives fail."""
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        return None
    return value


def _finite_nonneg_number(value: object) -> float | None:
    """Finite nonnegative number (int or float, no bool/NaN/Inf).

    Unrepresentable numeric input (for example a reported ``prompt_ms``
    of 10**400, whose ``float()`` conversion overflows) is UNAVAILABLE
    data: the conversion check at this input boundary returns None
    instead of letting the provider value raise out of ``generate()``.
    """
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    try:
        number = float(value)
    except (OverflowError, ValueError):
        return None
    if not math.isfinite(number) or number < 0:
        return None
    return number


def direct_backend_fingerprint(direct: DirectGenerationConfig) -> str:
    """Stable declared native backend identity (A13 provenance).

    Identifies the adapter dialect, pinned reference, declared model,
    credential-free configured endpoint identity, declared template
    identity + build evidence and the explicit operator limits/capability
    snapshot. Changing the request ID or response text must not change it;
    a declared model/template/endpoint/limit/capability change must. The
    deployed runtime/GGUF identity is explicitly unverified in this slice
    and recorded as such.
    """
    qual = direct.template_qualification
    return fingerprint(
        {
            "kind": "direct-native",
            "dialect": "llama-server-native",
            "reference_commit": NATIVE_REFERENCE_COMMIT,
            "model": direct.model,
            "endpoint": str(direct.destination.base_url).rstrip("/")
            if direct.destination is not None else None,
            "chat_template": direct.chat_template,
            "template_build_id": qual.build_id if qual is not None else None,
            "template_method": qual.method if qual is not None else None,
            "deadline_seconds": direct.deadline_seconds,
            "max_output_tokens": direct.max_output_tokens,
            "slot_id": direct.slot_id,
            "capabilities": dict(sorted(direct.capabilities.model_dump().items())),
            "runtime_identity": "unverified",
        }
    )


def _terminal_result(
    request: GeneratorRequest,
    outcome: CompletionOutcome,
    *,
    backend_fingerprint: str | None = None,
    text: str | None = None,
    usage: UsageMetrics | None = None,
    timings: TimingMetrics | None = None,
    error: str | None = None,
    attempts: int | None = None,
) -> GeneratorResult:
    return GeneratorResult(
        request_id=request.request_id,
        outcome=outcome,
        text=text,
        usage=usage,
        timings=timings,
        fingerprint=backend_fingerprint,
        error=_safe_error(error) if error else None,
        attempts=attempts,
    )


def build_apply_template_envelope(request: GeneratorRequest) -> dict:
    """Serialize the exact bounded ``/apply-template`` body.

    The body contains only the constructed ``messages`` array (no
    inference, no other keys). Trusted instruction/reference separation:
    ``request.instructions`` (trusted) is the single leading ``system``
    message; each ordered ``TextItem`` (reference material, untrusted
    data) becomes its own ``user`` message, preserving item boundaries and
    order. The server renders the prompt with its qualified loaded
    template; the client never invents token strings locally.
    """
    messages: list[dict] = []
    if request.instructions:
        messages.append({"role": "system", "content": request.instructions})
    messages.extend(
        {"role": "user", "content": item.text} for item in request.items
    )
    return {"messages": messages}


def build_completion_envelope(
    request: GeneratorRequest,
    *,
    prompt: str,
    n_predict: int,
    cache_prompt: bool,
    id_slot: int | None,
) -> dict:
    """Serialize the exact bounded native ``/completion`` body.

    Only supported pinned-dialect controls appear: the rendered ``prompt``
    string, explicit ``n_predict``, ``stream: false``, caller-set
    ``temperature``/``top_p``, the documented ``json_schema`` grammar
    control (``{}`` is the pinned reference's any-JSON form, mapping the
    ``json_object`` semantic — not a stronger object-shape guarantee —;
    the caller's exact schema otherwise), ``cache_prompt: true`` only
    when the capability was tested, and singular ``id_slot`` only when
    the slot capability was tested. JSON/schema requests reach this
    builder only when the build's ``json_grammar_tested`` capability was
    checked by the preflight (default deny); unsupported requested
    behavior is refused by the caller before the envelope is built —
    never silently ignored here.
    """
    envelope: dict = {
        "prompt": prompt,
        "n_predict": n_predict,
        "stream": False,
    }
    if request.temperature is not None:
        envelope["temperature"] = request.temperature
    if request.top_p is not None:
        envelope["top_p"] = request.top_p
    if request.response_format == "json_object":
        envelope["json_schema"] = {}
    elif request.response_format == "json_schema":
        assert request.json_schema is not None
        envelope["json_schema"] = request.json_schema
    if cache_prompt:
        envelope["cache_prompt"] = True
    if id_slot is not None:
        envelope["id_slot"] = id_slot
    return envelope


def _parse_json_bytes(body: bytes) -> tuple[dict | None, str | None]:
    """Bounded JSON decode with the expected decoder failure class.

    ``ValueError`` covers ``json.JSONDecodeError`` AND the interpreter
    integer digit limit (``sys.get_int_max_str_digits``; 4300 on the
    observed interpreters) rejecting oversized JSON integers with a plain
    ``ValueError``; ``RecursionError`` covers excessive nesting inside the
    transport byte bounds. The guard is scoped to this parse call only.
    """
    try:
        text = body.decode("utf-8")
    except UnicodeDecodeError:
        return None, "native response is not valid UTF-8"
    try:
        doc = json.loads(text)
    except (ValueError, RecursionError):
        return None, "native response is not valid JSON"
    if not isinstance(doc, dict):
        return None, "malformed native response (expected object)"
    return doc, None


def _parse_native_usage(doc: dict) -> UsageMetrics | None:
    """Map only the pinned dialect's actual reported fields (see module doc).

    A measured zero is legitimate; missing fields stay null; a bool/NaN/
    infinity counter is invalid (stays null) and cannot prove evaluated
    work. Top-level ``tokens_cached`` is deliberately ignored for
    ``cache_hit_tokens`` (it is the slot's resulting prompt token count).

    Dialect consistency: the pinned reference books the task's total
    prompt tokens as newly processed plus cached
    (``tokens_evaluated == prompt_n + cache_n``). When all three reported
    fields are present but contradict that relation (e.g. 100 input with
    90 new + 90 cached), the reported breakdown cannot be cache or
    evaluated-work proof: ``prefill_tokens``/``cache_hit_tokens`` are
    withheld (null). The directly reported task total keeps its own
    provenance; the raw contradictory values are not carried anywhere in
    the result (they are diagnostic server output, not qualified
    metrics).
    """
    input_tokens = _nonneg_int(doc.get("tokens_evaluated"))
    prompt_n = None
    cache_n = None
    predicted_n = None
    timings = doc.get("timings")
    if isinstance(timings, dict):
        prompt_n = _nonneg_int(timings.get("prompt_n"))
        cache_n = _nonneg_int(timings.get("cache_n"))
        predicted_n = _nonneg_int(timings.get("predicted_n"))
    if (input_tokens is not None and prompt_n is not None
            and cache_n is not None
            and prompt_n + cache_n != input_tokens):
        prompt_n = None
        cache_n = None
    if (input_tokens is None and predicted_n is None
            and prompt_n is None and cache_n is None):
        return None
    return UsageMetrics(
        input_tokens=input_tokens,
        output_tokens=predicted_n,
        prefill_tokens=prompt_n,
        cache_hit_tokens=cache_n,
    )


def _parse_native_timings(timings: object) -> TimingMetrics | None:
    """Model-phase timings from the dialect's own reported ms fields.

    Quantities (correct, explicit, per field — see module doc):

    - ``prefill_seconds``: reported prompt-processing duration; a
      measured reported 0ms is a known zero (0.0), never null;
    - ``decode_seconds``: reported token-generation duration, same
      zero/missing semantics (a withheld phase never discards the other
      reported phase);
    - ``total_seconds``: derived model-work total, explicitly model
      scoped (never caller wall time), present only when BOTH model
      phases were validly reported;
    - ``ttft_seconds``: never set here — the pinned dialect reports no
      first-token measurement, so TTFT stays unavailable.

    Caller wall time is never mixed in; absent/invalid/unrepresentable
    fields stay null.

    The derived total is computed in SECONDS from the two individually
    validated phase conversions (equivalent to dividing each phase by
    1000 before summing, so the millisecond sum never overflows first)
    and re-checked for finiteness: an unrepresentable derived total is
    withheld (null) while the individually valid phase values are
    retained — never a raw OverflowError/ValidationError out of
    generate(), never an invented cutoff.
    """
    if not isinstance(timings, dict):
        return None
    prompt_ms = _finite_nonneg_number(timings.get("prompt_ms"))
    predicted_ms = _finite_nonneg_number(timings.get("predicted_ms"))
    prefill = prompt_ms / 1000.0 if prompt_ms is not None else None
    decode = predicted_ms / 1000.0 if predicted_ms is not None else None
    total = None
    if prefill is not None and decode is not None:
        total = prefill + decode
        if not math.isfinite(total):
            # Defensively withhold an unrepresentable derived total;
            # the individually valid phases are retained.
            total = None
    if prefill is None and decode is None and total is None:
        return None
    return TimingMetrics(prefill_seconds=prefill, decode_seconds=decode,
                         total_seconds=total)


def _parse_apply_template(body: bytes) -> tuple[str | None, str | None]:
    """Validate the ``/apply-template`` response; return the rendered prompt.

    The server's explicit error form (an ``error`` object) and a missing,
    empty or non-string ``prompt`` are safe typed failures; no provider
    message text is ever echoed.
    """
    doc, error = _parse_json_bytes(body)
    if error is not None:
        return None, error
    if isinstance(doc.get("error"), dict):
        return None, "template application failed at the native server"
    prompt = doc.get("prompt")
    if not isinstance(prompt, str) or not prompt:
        return None, "apply-template response has no usable prompt"
    return prompt, None


def _parse_completion(body: bytes, request: GeneratorRequest,
                      backend_fingerprint: str) -> GeneratorResult:
    """Fail-closed outcome mapping for one non-stream native final response."""
    doc, error = _parse_json_bytes(body)
    if error is not None:
        return _terminal_result(request, CompletionOutcome.FAILED,
                                backend_fingerprint=backend_fingerprint,
                                error=error)
    usage = _parse_native_usage(doc)
    timings = _parse_native_timings(doc.get("timings"))
    if isinstance(doc.get("error"), dict):
        return _terminal_result(request, CompletionOutcome.FAILED,
                                backend_fingerprint=backend_fingerprint,
                                error="native completion failed at the server",
                                usage=usage, timings=timings)
    # stop must be true: the pinned final non-OAI serialization always
    # carries stop=true; anything else is not a stopped terminal.
    if doc.get("stop") is not True:
        return _terminal_result(request, CompletionOutcome.INCOMPLETE,
                                backend_fingerprint=backend_fingerprint,
                                error="native completion not stopped (stop != true)",
                                usage=usage, timings=timings)
    if doc.get("truncated") is not False:
        return _terminal_result(request, CompletionOutcome.INCOMPLETE,
                                backend_fingerprint=backend_fingerprint,
                                error="context truncated during generation",
                                usage=usage, timings=timings)
    stop_type = doc.get("stop_type")
    if not isinstance(stop_type, str):
        return _terminal_result(request, CompletionOutcome.FAILED,
                                backend_fingerprint=backend_fingerprint,
                                error="missing or invalid terminal reason",
                                usage=usage, timings=timings)
    if stop_type == _STOP_NONE:
        return _terminal_result(request, CompletionOutcome.INCOMPLETE,
                                backend_fingerprint=backend_fingerprint,
                                error="still generating at terminal response",
                                usage=usage, timings=timings)
    if stop_type == _STOP_LIMIT:
        return _terminal_result(request, CompletionOutcome.INCOMPLETE,
                                backend_fingerprint=backend_fingerprint,
                                error="stopped at the n_predict token limit",
                                usage=usage, timings=timings)
    if stop_type == _STOP_WORD:
        # This adapter sends no stop strings: a stop-word terminal has no
        # qualification and cannot become a success.
        return _terminal_result(request, CompletionOutcome.FAILED,
                                backend_fingerprint=backend_fingerprint,
                                error="unqualified stop-word terminal",
                                usage=usage, timings=timings)
    if stop_type != _STOP_EOS:
        return _terminal_result(request, CompletionOutcome.FAILED,
                                backend_fingerprint=backend_fingerprint,
                                error="missing or invalid terminal reason",
                                usage=usage, timings=timings)
    content = doc.get("content")
    if not isinstance(content, str):
        return _terminal_result(request, CompletionOutcome.FAILED,
                                backend_fingerprint=backend_fingerprint,
                                error="malformed native content",
                                usage=usage, timings=timings)
    if not content:
        return _terminal_result(request, CompletionOutcome.INCOMPLETE,
                                backend_fingerprint=backend_fingerprint,
                                error="completion stopped (eos) without usable content",
                                usage=usage, timings=timings)
    return _terminal_result(request, CompletionOutcome.TERMINAL,
                            backend_fingerprint=backend_fingerprint,
                            text=content, usage=usage, timings=timings)


class DirectNativeGenerator:
    """Private trusted OFFLINE native generator (annotation purpose only).

    Materializes only under the explicit ``offline_diagnostic`` policy
    (``private_trusted`` + private/loopback destination + declared model
    identity + template qualification + explicit finite operator limits);
    every gate is rechecked at call time, before any network work. The
    total deadline (min of caller and operator budgets) spans template
    rendering, generation, reads and every retry and is never reset per
    attempt; only positively pre-dispatch connect failures may use the
    finite configured retry budget. Unknown completion is non-retryable.
    """

    def __init__(
        self,
        config: DirectGenerationConfig,
        *,
        transport: GatewayTransport | None = None,
        clock: Callable[[], float] | None = None,
    ) -> None:
        self._config = config
        self._transport = transport
        # Generator-local monotonic clock: the real monotonic clock by
        # default; an injected deterministic clock makes deadline boundary
        # tests exact without patching the global time module.
        self._clock = clock if clock is not None else time.monotonic

    @property
    def identity(self) -> ModelIdentity | None:
        """Declared identity of the configured native destination.

        None while the offline opt-in is not fully materialized (no route,
        mode or model identity); the deployed runtime/GGUF identity stays
        explicitly unknown and is never asserted here.
        """
        direct = self._config
        if (direct.mode != "offline_diagnostic"
                or direct.model is None or direct.destination is None):
            return None
        return ModelIdentity(name=direct.model, adapter="native-completion")

    def _transport_instance(self) -> GatewayTransport:
        if self._transport is not None:
            return self._transport
        direct = self._config
        if direct.destination is None:
            raise TransportConfigError("native destination not configured")
        if direct.deadline_seconds is None:
            raise TransportConfigError("native operator deadline not configured")
        # The per-operation transport timeout is the total operator budget:
        # a finite secondary bound that the absolute deadline dominates.
        return GatewayTransport(
            direct.destination.base_url,
            timeout_seconds=direct.deadline_seconds,
            endpoint_contract="native",
        )

    def _preflight(self, request: GeneratorRequest) -> str | None:
        """Local refusal gates; zero network work on any refusal."""
        direct = self._config
        if direct.mode != "offline_diagnostic":
            return "native generation refused: direct mode is disabled"
        if direct.trusted_policy != "private_trusted":
            return "native generation refused: private_trusted policy not declared"
        if direct.destination is None:
            return "native generation refused: no private destination configured"
        if direct.model is None:
            return "native generation refused: declared model identity missing"
        if direct.template_qualification is None:
            return "native generation refused: template qualification record missing"
        if direct.max_output_tokens is None or direct.deadline_seconds is None:
            return "native generation refused: explicit finite operator limits missing"
        # Never an answer fallback (A22): only the annotation purpose.
        if request.purpose is not GeneratorPurpose.ANNOTATION:
            return ("native generation refused: only the annotation purpose is "
                    "supported (never an answer fallback)")
        # No qualified native image serializer exists yet: every visual /
        # image request refuses locally before dispatch, even when the
        # caller omits the capability from required_capabilities.
        if request.images or Capability.VISION in request.required_capabilities:
            return ("native generation refused: visual/image input has no "
                    "qualified native serializer")
        if Capability.STREAMING in request.required_capabilities:
            return ("native generation refused: streaming control is not "
                    "supported by the non-stream native slice")
        if (request.prompt_cache_key is not None
                or Capability.PROMPT_CACHING in request.required_capabilities):
            if not direct.capabilities.cache_prompt_tested:
                return ("prompt caching refused: native cache_prompt "
                        "capability not tested on this build")
        # Optional JSON/schema control admission (default deny): honored
        # BOTH from the actual input shape (a json_object/json_schema
        # response_format) and from the explicit minimum requirement
        # (JSON_MODE in required_capabilities, which a valid request may
        # carry without any format field). Template qualification and a
        # model capability declaration alone do not prove serving-build
        # grammar support; refuse BEFORE /apply-template or /completion
        # (zero dispatch) unless the serving build's JSON grammar
        # capability was actually tested.
        json_shape = request.response_format in ("json_object", "json_schema")
        json_required = Capability.JSON_MODE in request.required_capabilities
        if json_shape or json_required:
            if not direct.capabilities.json_grammar_tested:
                return ("native JSON control refused: json_schema grammar "
                        "support is not tested on this build (default deny)")
        # Output budget: REFUSAL semantics (consistent with the gateway
        # output reserve). The caller allowance must fit the explicit
        # finite operator limit; it is never silently clamped, and the
        # effective n_predict is exactly the (now bounded) caller value.
        if request.max_output_tokens > direct.max_output_tokens:
            return ("output budget refused: max_output_tokens exceeds the "
                    "configured native operator limit")
        return None

    def generate(self, request: GeneratorRequest) -> GeneratorResult:
        """Run one bounded native generation; expected failures are safe results."""
        direct = self._config
        backend_fingerprint = direct_backend_fingerprint(direct)
        refused = self._preflight(request)
        if refused is not None:
            return _terminal_result(request, CompletionOutcome.FAILED,
                                    backend_fingerprint=backend_fingerprint,
                                    error=refused)
        try:
            transport = self._transport_instance()
        except TransportConfigError as exc:
            return _terminal_result(request, CompletionOutcome.FAILED,
                                    backend_fingerprint=backend_fingerprint,
                                    error=str(exc))
        # One total absolute deadline spans template work, generation,
        # reads and every retry (min of caller and operator budgets).
        deadline = self._clock() + min(request.deadline_seconds,
                                       direct.deadline_seconds)
        template_body = json.dumps(
            build_apply_template_envelope(request),
            sort_keys=True, separators=(",", ":"), ensure_ascii=True,
        ).encode("utf-8")
        cache_prompt = (request.prompt_cache_key is not None
                        or Capability.PROMPT_CACHING in request.required_capabilities)
        id_slot = (direct.slot_id
                   if direct.slot_id is not None and direct.capabilities.slot_tested
                   else None)
        max_attempts = 1 + direct.max_retries
        attempts = 0
        while True:
            # Budget check before every dispatch, including retries.
            if self._clock() >= deadline:
                return _terminal_result(request, CompletionOutcome.FAILED,
                                        backend_fingerprint=backend_fingerprint,
                                        error="deadline exhausted before dispatch",
                                        attempts=attempts)
            attempts += 1
            try:
                status, body = transport.post_json(
                    APPLY_TEMPLATE_PATH, template_body, deadline=deadline)
                if status >= 400:
                    return _terminal_result(
                        request, CompletionOutcome.FAILED,
                        backend_fingerprint=backend_fingerprint,
                        error=f"template application refused (HTTP {status})",
                        attempts=attempts)
                prompt, error = _parse_apply_template(body)
                if error is not None:
                    return _terminal_result(request, CompletionOutcome.FAILED,
                                            backend_fingerprint=backend_fingerprint,
                                            error=error, attempts=attempts)
                # The budget spans template work AND generation: an
                # expiry after template rendering, before inference,
                # refuses the /completion dispatch (the deadline is never
                # reset per attempt).
                if self._clock() >= deadline:
                    return _terminal_result(request, CompletionOutcome.FAILED,
                                            backend_fingerprint=backend_fingerprint,
                                            error="deadline exhausted before dispatch",
                                            attempts=attempts)
                envelope = build_completion_envelope(
                    request, prompt=prompt,
                    n_predict=request.max_output_tokens,
                    cache_prompt=cache_prompt, id_slot=id_slot)
                completion_body = json.dumps(
                    envelope, sort_keys=True, separators=(",", ":"),
                    ensure_ascii=True).encode("utf-8")
                status, body = transport.post_json(
                    COMPLETION_PATH, completion_body, deadline=deadline)
                if status >= 400:
                    return _terminal_result(
                        request, CompletionOutcome.FAILED,
                        backend_fingerprint=backend_fingerprint,
                        error=f"native completion refused (HTTP {status})",
                        attempts=attempts)
                result = _parse_completion(body, request, backend_fingerprint)
                return result.model_copy(update={"attempts": attempts})
            except TransportConnectError as exc:
                # Positively pre-dispatch: the finite retry policy decides.
                if attempts < max_attempts:
                    continue
                return _terminal_result(request, CompletionOutcome.FAILED,
                                        backend_fingerprint=backend_fingerprint,
                                        error=str(exc), attempts=attempts)
            except TransportTimeoutError as exc:
                if exc.retryable and attempts < max_attempts:
                    continue
                if exc.retryable:
                    return _terminal_result(request, CompletionOutcome.FAILED,
                                            backend_fingerprint=backend_fingerprint,
                                            error=str(exc), attempts=attempts)
                return _terminal_result(request, CompletionOutcome.UNKNOWN_COMPLETION,
                                        backend_fingerprint=backend_fingerprint,
                                        error=str(exc), attempts=attempts)
            except TransportRefusedError as exc:
                return _terminal_result(request, CompletionOutcome.FAILED,
                                        backend_fingerprint=backend_fingerprint,
                                        error=str(exc), attempts=attempts)
            except TransportTruncatedError as exc:
                return _terminal_result(request, CompletionOutcome.FAILED,
                                        backend_fingerprint=backend_fingerprint,
                                        error=str(exc), attempts=attempts)
            except TransportError as exc:
                # Post-dispatch network failure leaves completion unknown
                # (V2-03); only a positively pre-dispatch failure is a safe
                # definite failure.
                outcome = (CompletionOutcome.UNKNOWN_COMPLETION
                           if exc.dispatched else CompletionOutcome.FAILED)
                return _terminal_result(request, outcome,
                                        backend_fingerprint=backend_fingerprint,
                                        error=str(exc), attempts=attempts)
