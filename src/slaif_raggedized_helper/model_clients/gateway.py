"""Gateway ``/v1/responses`` adapter behind the 002 ``GeneratorClient`` contract.

The wire dialect is the bounded Responses contract of the pinned gateway
revision ``f2df0e82df8766740d9ac169ea56ffd7a3cb1f1e``
(``ulfe-lmi/slaif-api-gateway``, ``docs/responses-compatibility.md``):
``model``, text/item-array ``input``, optional ``instructions``,
``max_output_tokens``, ``temperature``, ``top_p``, ``store`` (the gateway
injects ``store=false`` when omitted; this adapter sends it explicitly),
``stream`` only when the route advertises streaming, bounded ``text.format``
structured output, and (behind explicit capability) ``prompt_cache_key``.
Native llama fields (``cache_prompt``/``id_slot``/``slot_ids``) never appear
on the gateway wire.

Outcome mapping (architecture A13/V2-03/V2-06): only a validated
``response.completed`` / ``status: completed`` produces TERMINAL. Refusals,
incomplete and failed terminals, duplicate/malformed or out-of-order item
IDs, and EOF without terminal success never appear as COMPLETE. Provider
error bodies are never echoed; only safe status classes and bounded
provider codes are reported.

Structural invariants of the streaming dialect (fail-closed): supplied
envelope coordinates are validated by one shared decoder where key absence
and present-null are distinct (absent optional coordinates keep the
implicit forms; present-null or non-integer coordinates are malformed);
item type/identity is frozen from ``output_item.added`` through
``output_item.done`` and the final ``output`` array; explicit content-part
coordinates are bounded, sequential and bound to the actual ordered final
part positions; item completion is latched (duplicate or contradictory
post-done events are refused); and every supported item type has a
validated terminal done status (message: ``completed``/``refusal``;
reasoning: ``completed``). No internal reasoning becomes answer text.
"""

from __future__ import annotations

import json
import re
import time
from collections.abc import Callable
from typing import Protocol, runtime_checkable

from ..config import GeneratorConfig
from ..schema import (
    Capability,
    CompletionOutcome,
    GeneratorRequest,
    GeneratorResult,
    ImageRef,
    ModelIdentity,
    UsageMetrics,
    fingerprint,
)
from .transport import (
    GatewayTransport,
    SSEFrame,
    TransportConfigError,
    TransportConnectError,
    TransportError,
    TransportProtocolError,
    TransportRefusedError,
    TransportTimeoutError,
    TransportTruncatedError,
)

GATEWAY_CONTRACT_COMMIT = "f2df0e82df8766740d9ac169ea56ffd7a3cb1f1e"
GATEWAY_CONTRACT_SOURCE = "ulfe-lmi/slaif-api-gateway:docs/responses-compatibility.md"
RESPONSES_PATH = "/v1/responses"
_MAX_ERROR_TEXT = 200

# Provider-controlled strings are exfiltration channels: only fixed protocol
# vocabulary from the pinned dialect is ever echoed; anything else becomes a
# fixed safe reason. No provider codes, messages or body bytes are reported.
_REFUSAL_REASONS = frozenset({"content_filter", "unknown"})
_INCOMPLETE_REASONS = frozenset({"max_output_tokens", "content_filter"})
_SAFE_IMAGE_PREFIXES = ("data:image/png;base64,", "data:image/jpeg;base64,",
                        "data:image/webp;base64,", "data:image/gif;base64,")
_SAFE_IMAGE_URL_RE = re.compile(r"https://[a-z0-9._:-]+(/.*)?\Z", re.IGNORECASE)

# Event families of the bounded Responses SSE dialect at the pinned contract
# commit. Anything else is delivered but never treated as a terminal.
_KNOWN_EVENTS = frozenset(
    {
        "response.created",
        "response.in_progress",
        "response.output_item.added",
        "response.content_part.added",
        "response.output_text.delta",
        "response.output_text.done",
        "response.content_part.done",
        "response.output_item.done",
        "response.completed",
        "response.failed",
        "response.incomplete",
        "error",
    }
)


@runtime_checkable
class ImageResolver(Protocol):
    """Explicitly trusted bounded resolver for authorized ``ImageRef`` IDs.

    Callers never pass raw URLs/files: the resolver is trusted operator code
    that maps an authorized ``(image_id, source_revision)`` pair to bounded
    image material (data URL or credential-free https URL).
    """

    def resolve(self, image_ref: ImageRef) -> str:  # pragma: no cover - protocol
        ...


def _safe_error(message: str) -> str:
    return message[:_MAX_ERROR_TEXT]


def _allowlisted(value: object, allowed: frozenset[str]) -> str | None:
    return value if isinstance(value, str) and value in allowed else None


def _nonneg_int(value: object) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        return None
    return value


def _is_finite_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and value >= 0.0


def _parse_usage(usage: object) -> UsageMetrics | None:
    """Map provider usage to null-preserving metrics; missing stays None."""
    if not isinstance(usage, dict):
        return None
    input_tokens = _nonneg_int(usage.get("input_tokens"))
    output_tokens = _nonneg_int(usage.get("output_tokens"))
    cached_tokens = None
    details = usage.get("input_tokens_details")
    if isinstance(details, dict):
        cached_tokens = _nonneg_int(details.get("cached_tokens"))
    if input_tokens is None and output_tokens is None and cached_tokens is None:
        return None
    return UsageMetrics(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        prefill_tokens=None,  # the gateway dialect does not report prefill counts
        cache_hit_tokens=cached_tokens,
    )


# Pinned dialect (f2df0e82, app/slaif_gateway/providers/streaming.py
# validators): final output items are array-ordered and do NOT carry
# output_index (that coordinate is an SSE event-envelope field); message
# items are completed assistant text whose content parts are output_text;
# reasoning/function_call items carry no answer text; any other item or
# part type, or a contradictory item status, is a structural error.
_MESSAGE_STATUSES = frozenset({"completed", "refusal"})
# Item types with a supported stream lifecycle in this bounded adapter:
# message items carry the answer text; reasoning items are supported
# non-text items. Any other added type (function_call included) is an
# unsupported action, refused at the stream boundary.
_SUPPORTED_ITEM_TYPES = frozenset({"message", "reasoning"})
# Bounded image material size (data URL or URL string) before JSON
# serialization; the resolver protocol alone does not bound bytes.
_MAX_IMAGE_MATERIAL_BYTES = 4 * 1024 * 1024


def _validate_message_parts(
    content: object, status: str
) -> tuple[list[str], str | None, str | None]:
    """Strict message-content part rules shared by the final ``output``
    array and the ``output_item.done`` boundary (one consistent private
    validation path, V2-06/A14).

    Returns ``(part_texts, refusal_reason, structural_error)`` in array
    order, preserving per-part positions. ``output_text`` parts must carry
    string text; a ``refusal`` part is meaningful only on a ``refusal``
    item and its reason is allowlisted; any other part type, shape or
    missing text is a structural error, never silently skipped to salvage
    success.
    """
    if not isinstance(content, list):
        return [], None, "message item without content parts"
    part_texts: list[str] = []
    refusal: str | None = None
    for part in content:
        if not isinstance(part, dict):
            return [], None, "malformed content part"
        part_type = part.get("type")
        if part_type == "output_text":
            text = part.get("text")
            if not isinstance(text, str):
                return [], None, "malformed output_text part"
            part_texts.append(text)
        elif part_type == "refusal" and status == "refusal":
            reason = _allowlisted(part.get("refusal"), _REFUSAL_REASONS)
            if reason is not None and refusal is None:
                refusal = reason
        else:
            return [], None, "unsupported content part type"
    return part_texts, refusal, None


def _valid_message_role(item: dict) -> bool:
    role = item.get("role")
    return isinstance(role, str) and role == "assistant"


def _collect_output(output: object) -> tuple[list[str], str | None, str | None]:
    """Collect ordered output-text and refusals from a Responses ``output``.

    Returns ``(message_texts, refusal_reason, structural_error)``. Final
    items are authoritative in array order; a ``message`` item must be
    ``completed`` (or a refusal item) and may only contain ``output_text``
    parts. Text in any other field, part or item type is never accepted;
    malformed, unknown or contradictory items are structural errors, never
    skipped to salvage success. A completed response without usable output
    text is an error.
    """
    if not isinstance(output, list) or not output:
        return [], None, "malformed output (expected non-empty item list)"
    seen_ids: set[str] = set()
    refusal: str | None = None
    texts: list[str] = []
    for position, item in enumerate(output):
        if not isinstance(item, dict):
            return [], None, "malformed output item (expected object)"
        item_id = item.get("id")
        if not isinstance(item_id, str) or not item_id:
            return [], None, "output item missing ID"
        if item_id in seen_ids:
            return [], None, "duplicate output item ID"
        seen_ids.add(item_id)
        # Array order is authoritative for final items; an index that is
        # genuinely present must not contradict the position. A present
        # null (or non-integer) final index is malformed, distinct from
        # absence.
        if "output_index" in item:
            supplied_index = item.get("output_index")
            if _nonneg_int(supplied_index) is None:
                return [], None, "malformed output item index"
            if supplied_index != position:
                return [], None, "out-of-order output item"
        item_type = item.get("type")
        status = item.get("status")
        if item_type == "message":
            if not _valid_message_role(item):
                return [], None, "invalid message role"
            # Guard the type before set membership: a hostile provider may
            # send status {} or []; that is a structural error, never a
            # TypeError and never a salvaged success.
            if not isinstance(status, str) or status not in _MESSAGE_STATUSES:
                return [], None, "contradictory terminal message item status"
            part_texts, part_refusal, structural = _validate_message_parts(
                item.get("content"), status)
            if structural:
                return [], None, structural
            if status == "refusal" and refusal is None:
                # An allowlisted reason from the part wins; the generic
                # fallback must never shadow it.
                refusal = part_refusal or "refusal"
            if any(part_texts) and status == "refusal":
                return [], None, "contradictory refusal item with output text"
            if status == "completed" and not any(part_texts):
                return [], None, "message item without usable output_text content"
            if any(part_texts):
                texts.append("".join(part_texts))
        elif item_type == "reasoning":
            # Supported non-text item: it never contributes answer text, but
            # its terminal state is validated like any other item. A
            # reasoning item whose status is not a completed string inside
            # the final output of a completed response is a contradictory
            # state, never silently skipped.
            if not isinstance(status, str) or status != "completed":
                return [], None, "contradictory terminal reasoning item status"
        elif item_type == "function_call":
            # Explicit unsupported-action handling: this bounded adapter
            # never declares tools in the wire envelope, so a model
            # function_call is an unsupported action. The whole response is
            # refused instead of salvaging text around the action.
            return [], None, "unsupported function_call output item"
        else:
            return [], None, "unsupported output item type"
    if texts and refusal is not None:
        return [], None, "contradictory terminal (refusal with output text)"
    if not texts and refusal is None:
        return [], None, "no usable output text in completed response"
    return texts, refusal, None


def gateway_backend_fingerprint(route: object) -> str:
    """Stable declared backend identity (A13 provenance).

    Identifies the adapter dialect, pinned contract, declared model, route
    endpoint and capability snapshot. Changing the request ID or response
    text must not change it; a declared model revision or route/endpoint/
    capability change must. The credential-free configured endpoint
    identity (scheme, host, port, API segment) distinguishes deployments
    that a bare hostname would collapse. The deployed runtime/GGUF identity
    is explicitly unverified in this slice and recorded as such.
    """
    return fingerprint(
        {
            "kind": "gateway",
            "dialect": "v1-responses",
            "contract_commit": GATEWAY_CONTRACT_COMMIT,
            "model": route.model,  # type: ignore[attr-defined]
            "endpoint": str(route.base_url).rstrip("/"),  # type: ignore[attr-defined]
            "timeout_seconds": route.timeout_seconds,  # type: ignore[attr-defined]
            "capabilities": dict(sorted(route.capabilities.model_dump().items())),  # type: ignore[attr-defined]
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
    error: str | None = None,
    attempts: int | None = None,
) -> GeneratorResult:
    return GeneratorResult(
        request_id=request.request_id,
        outcome=outcome,
        text=text,
        usage=usage,
        timings=None,
        fingerprint=backend_fingerprint,
        error=_safe_error(error) if error else None,
        attempts=attempts,
    )


def build_responses_envelope(
    request: GeneratorRequest,
    route: object,
    *,
    stream: bool,
    image_materials: list[str] | None = None,
) -> dict:
    """Serialize the exact bounded Responses create envelope.

    The body contains only the constructed allowlist keys; native direct
    fields (``cache_prompt``/``id_slot``/``slot_ids``) are impossible here by
    construction. ``image_materials`` must align 1:1 with
    ``request.images`` in order.
    """
    parts: list[dict] = [{"type": "input_text", "text": item.text} for item in request.items]
    if request.images:
        materials = image_materials or []
        if len(materials) != len(request.images):
            raise ValueError("image material count mismatch")
        for material in materials:
            parts.append({"type": "input_image", "image_url": material})
    envelope: dict = {
        "model": route.model,  # type: ignore[attr-defined]
        "input": [{"type": "message", "role": "user", "content": parts}],
        "max_output_tokens": request.max_output_tokens,
        "store": False,
    }
    if request.instructions:
        envelope["instructions"] = request.instructions
    if request.temperature is not None:
        envelope["temperature"] = request.temperature
    if request.top_p is not None:
        envelope["top_p"] = request.top_p
    if request.response_format == "json_object":
        envelope["text"] = {"format": {"type": "json_object"}}
    elif request.response_format == "json_schema":
        assert request.json_schema is not None
        envelope["text"] = {"format": {"type": "json_schema", "name": "output",
                                       "schema": request.json_schema}}
    if request.prompt_cache_key:
        envelope["prompt_cache_key"] = request.prompt_cache_key
    if stream:
        envelope["stream"] = True
    return envelope


class _StreamState:
    """Frame-by-frame accumulator with fail-closed structural validation.

    Text is buffered per output item AND per content part (part 0 is the
    implicit default when an event carries no ``content_index``), so a
    message with several bounded ``output_text`` parts reconciles each
    part's cumulative text independently instead of one buffer per item
    confusing a later part's cumulative text with the prior parts.
    """

    def __init__(self) -> None:
        self.response_id: str | None = None
        self.public_events = 0
        self.terminal: tuple[str, dict] | None = None  # (kind, payload.response)
        self.terminal_reason: str | None = None
        self.error: str | None = None
        self.saw_done = False
        self.item_ids: set[str] = set()
        self.item_order: list[str] = []
        self.item_types: dict[str, object] = {}
        self.item_buffers: dict[str, dict[int, list[str]]] = {}
        self.item_text_done: dict[str, set[int]] = {}
        self.item_parts_added: dict[str, set[int]] = {}
        self.item_parts_done: dict[str, set[int]] = {}
        self.item_final_text: dict[str, str] = {}
        self.item_refusal: dict[str, str | None] = {}
        self.item_done: set[str] = set()
        self.completed_payload: dict | None = None

    def note_response_id(self, response_id: object) -> None:
        if not isinstance(response_id, str) or not response_id:
            return
        if self.response_id is None:
            self.response_id = response_id
        elif self.response_id != response_id:
            self.fail("conflicting response IDs")

    def fail(self, reason: str) -> None:
        if self.error is None:
            self.error = reason

    def streamed_text(self, item_id: str) -> str:
        """Delta text observed for one item, parts in content order."""
        buffers = self.item_buffers.get(item_id, {})
        return "".join("".join(buffers[i]) for i in sorted(buffers))


class _GatewayAccumulator:
    def __init__(self) -> None:
        self.state = _StreamState()

    def handle(self, frame: SSEFrame) -> None:
        state = self.state
        try:
            payload = json.loads(frame.data) if frame.data else {}
        except (ValueError, RecursionError):
            # JSONDecodeError is a ValueError; excessive nesting raises
            # RecursionError. Both are malformed event payloads inside the
            # transport's byte bounds, never raw crashes.
            state.fail("malformed event payload")
            return
        if not isinstance(payload, dict):
            state.fail("malformed event payload")
            return
        # The pinned dialect emits data-only SSE frames: the JSON "type"
        # field is the event discriminator (the gateway never sends
        # "event:" lines). An explicit SSE event name, when present, must
        # agree with the JSON discriminator; disagreement is a protocol
        # violation that fails closed instead of being treated as an
        # unknown, inert family.
        json_type = payload.get("type")
        if frame.event != "message":
            if not isinstance(json_type, str):
                return  # no JSON discriminator: not a dialect event; inert
            if json_type != frame.event:
                state.fail("event name and payload type disagree")
                return
        event = json_type
        if not isinstance(event, str) or event not in _KNOWN_EVENTS:
            return  # unknown events are inert; never terminals
        state.public_events += 1
        if event == "response.created" or event == "response.in_progress":
            response = payload.get("response")
            if isinstance(response, dict):
                state.note_response_id(response.get("id"))
        elif event == "response.output_item.added":
            self._handle_item_added(payload)
        elif event == "response.content_part.added":
            self._handle_content_part("added", payload)
        elif event == "response.output_text.delta":
            self._handle_text_delta(payload)
        elif event == "response.output_text.done":
            self._handle_text_done(payload)
        elif event == "response.content_part.done":
            self._handle_content_part("done", payload)
        elif event == "response.output_item.done":
            self._handle_item_done(payload)
        elif event == "response.completed":
            self._handle_terminal("completed", payload)
        elif event == "response.failed":
            self._handle_terminal("failed", payload)
        elif event == "response.incomplete":
            self._handle_terminal("incomplete", payload)
        elif event == "error":
            state.terminal = ("error", {})
            state.terminal_reason = "provider error"

    def _handle_item_added(self, payload: dict) -> None:
        state = self.state
        item = payload.get("item")
        if not isinstance(item, dict):
            state.fail("malformed output_item.added")
            return
        item_id = item.get("id")
        if not isinstance(item_id, str) or not item_id:
            state.fail("output item missing ID")
            return
        if item_id in state.item_ids:
            state.fail("duplicate output item ID")
            return
        # Envelope output_index is required in the pinned dialect and must
        # equal the position this item takes in the observed order.
        if _nonneg_int(payload.get("output_index")) != len(state.item_order):
            state.fail("out-of-order output item")
            return
        item_type = item.get("type")
        # Item type/identity is frozen from added through done and final:
        # only supported item types may enter the stream lifecycle, and a
        # model function_call is an unsupported action for this adapter.
        # Guard the type before set membership: a hostile provider may
        # send status {} or []; the same applies to item.type — an
        # unhashable or non-string type is a structural error, never a
        # TypeError and never a salvaged success.
        if not isinstance(item_type, str):
            state.fail("unsupported output item type")
            return
        if item_type == "function_call":
            state.fail("unsupported function_call output item")
            return
        if item_type not in _SUPPORTED_ITEM_TYPES:
            state.fail("unsupported output item type")
            return
        if item_type == "message" and not _valid_message_role(item):
            state.fail("invalid message role")
            return
        state.item_ids.add(item_id)
        state.item_order.append(item_id)
        state.item_types[item_id] = item_type
        state.item_buffers[item_id] = {}
        state.item_text_done[item_id] = set()
        state.item_parts_added[item_id] = set()
        state.item_parts_done[item_id] = set()
        state.item_final_text[item_id] = ""
        state.item_refusal[item_id] = None

    def _coordinates(
        self, payload: dict, item_id: str, *,
        require_added: bool,
        require_explicit_content: bool = False,
        require_explicit_output: bool = False,
        allow_content_index: bool = True,
    ) -> int | None:
        """Shared envelope-coordinate decoder for every recognized event.

        One consistent private validation path: presence and value are
        distinct. An ABSENT optional coordinate keeps the supported
        implicit form (the item's observed position / content part 0), or
        fails when the event form requires the coordinate. A PRESENT
        coordinate that is null or any non-integer is malformed and fails
        closed before any state is read or mutated — a supplied null is
        never absence. A supplied ``output_index`` must equal the item's
        observed position; a supplied ``content_index`` must name a bounded
        part already added (for events that require it). Returns the
        content-part index (0 for the implicit part) or None after latching
        a protocol error.
        """
        state = self.state
        if "output_index" in payload:
            output_index = _nonneg_int(payload["output_index"])
            if output_index is None:
                state.fail("malformed event index")
                return None
            if output_index != state.item_order.index(item_id):
                state.fail("output_index mismatch")
                return None
        elif require_explicit_output:
            state.fail("malformed event index")
            return None
        if allow_content_index and "content_index" in payload:
            part_index = _nonneg_int(payload["content_index"])
            if part_index is None:
                state.fail("malformed content part index")
                return None
            if require_added and part_index not in state.item_parts_added[item_id]:
                state.fail("unknown content part")
                return None
            return part_index
        if "content_index" in payload or require_explicit_content:
            # present-but-not-allowed (item boundary) or required-but-absent
            state.fail("malformed content part index")
            return None
        return 0

    def _handle_text_delta(self, payload: dict) -> None:
        state = self.state
        item_id = payload.get("item_id")
        if not isinstance(item_id, str) or item_id not in state.item_buffers:
            state.fail("delta for unknown output item")
            return
        if state.item_types.get(item_id) != "message":
            # Text events belong to supported message parts: reasoning (or
            # any non-message) item cannot accumulate answer text.
            state.fail("text event for non-message item")
            return
        if item_id in state.item_done:
            state.fail("text event after item done")
            return
        part_index = self._coordinates(payload, item_id, require_added=True,
                                       require_explicit_content=False)
        if part_index is None:
            return
        delta = payload.get("delta")
        if not isinstance(delta, str):
            # Any non-string delta (array, number, bool, null, object) is a
            # malformed stream; it is never silently dropped and the later
            # authoritative text cannot be salvaged around it.
            state.fail("malformed delta type")
            return
        if (part_index in state.item_text_done[item_id]
                or part_index in state.item_parts_done[item_id]):
            state.fail("delta after content part done")
            return
        state.item_buffers[item_id].setdefault(part_index, []).append(delta)

    def _handle_text_done(self, payload: dict) -> None:
        state = self.state
        item_id = payload.get("item_id")
        if not isinstance(item_id, str) or item_id not in state.item_buffers:
            state.fail("done for unknown output item")
            return
        if state.item_types.get(item_id) != "message":
            state.fail("text event for non-message item")
            return
        if item_id in state.item_done:
            state.fail("text event after item done")
            return
        part_index = self._coordinates(payload, item_id, require_added=True,
                                       require_explicit_content=False)
        if part_index is None:
            return
        cumulative = payload.get("text")
        if not isinstance(cumulative, str):
            state.fail("malformed output_text.done")
            return
        if part_index in state.item_text_done[item_id]:
            state.fail("duplicate output_text.done")
            return
        buffers = state.item_buffers[item_id]
        if "".join(buffers.get(part_index, [])) != cumulative:
            state.fail("delta/cumulative text mismatch")
            return
        buffers[part_index] = [cumulative]
        state.item_text_done[item_id].add(part_index)

    def _handle_content_part(self, kind: str, payload: dict) -> None:
        state = self.state
        item_id = payload.get("item_id")
        if not isinstance(item_id, str) or item_id not in state.item_buffers:
            state.fail("content part for unknown output item")
            return
        if state.item_types.get(item_id) != "message":
            state.fail("content part for non-message item")
            return
        if item_id in state.item_done:
            state.fail("content part event after item done")
            return
        part_index = self._coordinates(
            payload, item_id,
            require_added=kind == "done",
            require_explicit_content=True,
        )
        if part_index is None:
            return
        part = payload.get("part")
        if (not isinstance(part, dict) or part.get("type") != "output_text"
                or not isinstance(part.get("text"), str)):
            state.fail("malformed content part")
            return
        if kind == "added":
            if part_index in state.item_parts_added[item_id]:
                state.fail("duplicate content part added")
                return
            # Known bounded part membership/order: explicit parts are
            # numbered 0,1,2,... in the order they are added. A gap,
            # rename or out-of-order coordinate cannot be sorted into a
            # later final part position.
            if part_index != len(state.item_parts_added[item_id]):
                state.fail("out-of-order content part")
                return
            if part.get("text"):
                state.fail("content part added with text")
                return
            state.item_parts_added[item_id].add(part_index)
        else:
            if part_index in state.item_parts_done[item_id]:
                state.fail("duplicate content part done")
                return
            if part_index not in state.item_text_done[item_id]:
                state.fail("content part done before text done")
                return
            if (part.get("text") != "".join(
                    state.item_buffers[item_id].get(part_index, []))):
                state.fail("content part text mismatch")
                return
            state.item_parts_done[item_id].add(part_index)

    def _handle_item_done(self, payload: dict) -> None:
        state = self.state
        item = payload.get("item")
        if not isinstance(item, dict):
            state.fail("malformed output_item.done")
            return
        item_id = item.get("id")
        if not isinstance(item_id, str) or item_id not in state.item_buffers:
            state.fail("done for unknown output item")
            return
        # Shared coordinate decoder at the item boundary: output_index is
        # required; a part-scoped content_index has no meaning here and is
        # malformed whenever present (null included).
        if self._coordinates(payload, item_id, require_added=False,
                             require_explicit_content=False,
                             require_explicit_output=True,
                             allow_content_index=False) is None:
            return
        if item_id in state.item_done:
            # Latch item completion: a duplicate done (or any contradictory
            # re-completion) is refused, never tolerated.
            state.fail("duplicate output_item.done")
            return
        observed_type = state.item_types.get(item_id)
        if item.get("type") != observed_type:
            # Type/identity is frozen from added: a reasoning item cannot
            # become a message with the same ID (or vice versa).
            state.fail("item type changed at done")
            return
        status = item.get("status")
        if observed_type == "message":
            if not _valid_message_role(item):
                state.fail("invalid message role")
                return
            # The done boundary is the item's terminal transition: a
            # nonterminal or untyped status followed by a completed final
            # message is contradictory and fails, never tolerated.
            if not isinstance(status, str) or status not in _MESSAGE_STATUSES:
                state.fail("nonterminal item done status")
                return
            part_texts, part_refusal, structural = _validate_message_parts(
                item.get("content"), status)
            if structural:
                state.fail(structural)
                return
            if status == "refusal":
                state.item_refusal[item_id] = part_refusal or "refusal"
            if any(part_texts) and status == "refusal":
                state.fail("contradictory refusal item with output text")
                return
            if status == "completed" and not any(part_texts):
                state.fail("message item without usable output_text content")
                return
            # Explicit content-part coordinates bind to their actual
            # ordered final part positions: an observed part cannot
            # disappear solely because the final concatenated text happens
            # to match, and each observed part's accumulated text must
            # equal the final part text at its position.
            tracked = sorted(state.item_parts_added[item_id])
            if tracked:
                if len(part_texts) != max(tracked) + 1:
                    state.fail("content part coordinate missing from final content")
                    return
                for index in tracked:
                    if part_texts[index] != "".join(
                            state.item_buffers[item_id].get(index, [])):
                        state.fail("content part text mismatch")
                        return
            state.item_final_text[item_id] = "".join(part_texts)
        elif observed_type == "reasoning":
            # Terminal done status for every supported type: a reasoning
            # item done in a nonterminal state is a contradictory state,
            # even when the final output later shows it completed.
            if not isinstance(status, str) or status != "completed":
                state.fail("contradictory terminal reasoning item status")
                return
        state.item_done.add(item_id)
        streamed = state.streamed_text(item_id)
        if streamed and state.item_final_text[item_id] != streamed:
            state.fail("item text mismatch between delta stream and done item")

    def _handle_terminal(self, kind: str, payload: dict) -> None:
        state = self.state
        if state.terminal is not None:
            state.fail("duplicate terminal event")
            return
        response = payload.get("response")
        if not isinstance(response, dict):
            state.fail("malformed terminal payload")
            return
        # A terminal must carry a valid nonempty response ID consistent
        # with the observed events; a missing or malformed ID fails
        # closed instead of being ignored.
        response_id = response.get("id")
        if not isinstance(response_id, str) or not response_id:
            state.fail("malformed terminal response ID")
            return
        state.note_response_id(response_id)
        if kind == "completed":
            state.completed_payload = response
        elif kind == "failed":
            state.terminal_reason = "provider failure"
        elif kind == "incomplete":
            details = response.get("incomplete_details")
            reason = _allowlisted(details.get("reason"), _INCOMPLETE_REASONS) \
                if isinstance(details, dict) else None
            state.terminal_reason = f"incomplete: {reason}" if reason else "incomplete"
        state.terminal = (kind, response)

    def stream_text(self) -> str | None:
        """Ordered partial/full text across output items, or None if none."""
        ordered: list[str] = []
        for item_id in self.state.item_order:
            text = self.state.item_final_text.get(item_id) or \
                self.state.streamed_text(item_id)
            if text:
                ordered.append(text)
        return "\n".join(ordered) if ordered else None

    def stream_refusal(self) -> str | None:
        for item_id in self.state.item_order:
            if self.state.item_refusal.get(item_id):
                return self.state.item_refusal[item_id]
        return None


def _parse_non_stream(body: bytes, request: GeneratorRequest,
                      backend_fingerprint: str) -> GeneratorResult:
    try:
        text = body.decode("utf-8")
    except UnicodeDecodeError:
        return _terminal_result(request, CompletionOutcome.FAILED,
                                backend_fingerprint=backend_fingerprint,
                                error="provider response is not valid UTF-8")
    try:
        doc = json.loads(text)
    except (ValueError, RecursionError):
        # json.JSONDecodeError is a ValueError subtype, and the interpreter
        # integer digit limit (sys.get_int_max_str_digits; 4300 on the
        # observed interpreters) rejects oversized JSON integers with a
        # plain ValueError. The expected decoder failure class is therefore
        # ValueError; the guard is scoped to this parse call only, so
        # programming errors elsewhere still propagate. RecursionError:
        # nesting beyond the interpreter limit inside the transport byte
        # bounds is malformed input, never a crash.
        return _terminal_result(request, CompletionOutcome.FAILED,
                                backend_fingerprint=backend_fingerprint,
                                error="provider response is not valid JSON")
    if not isinstance(doc, dict):
        return _terminal_result(request, CompletionOutcome.FAILED,
                                backend_fingerprint=backend_fingerprint,
                                error="malformed provider response")
    status = doc.get("status")
    usage = _parse_usage(doc.get("usage"))
    if status == "completed":
        texts, refusal, structural = _collect_output(doc.get("output"))
        if structural:
            return _terminal_result(request, CompletionOutcome.FAILED,
                                    backend_fingerprint=backend_fingerprint,
                                    error=structural, usage=usage)
        if refusal is not None:
            return _terminal_result(request, CompletionOutcome.REFUSAL,
                                    backend_fingerprint=backend_fingerprint,
                                    error=f"refusal: {refusal}", usage=usage)
        return _terminal_result(request, CompletionOutcome.TERMINAL,
                                backend_fingerprint=backend_fingerprint,
                                text="\n".join(texts), usage=usage)
    if status == "incomplete":
        details = doc.get("incomplete_details")
        reason = _allowlisted(details.get("reason"), _INCOMPLETE_REASONS) \
            if isinstance(details, dict) else None
        return _terminal_result(request, CompletionOutcome.INCOMPLETE,
                                backend_fingerprint=backend_fingerprint,
                                error=f"incomplete: {reason}" if reason else "incomplete",
                                usage=usage)
    if status == "failed":
        return _terminal_result(request, CompletionOutcome.FAILED,
                                backend_fingerprint=backend_fingerprint,
                                error="provider failure", usage=usage)
    return _terminal_result(request, CompletionOutcome.FAILED,
                            backend_fingerprint=backend_fingerprint,
                            error="unexpected provider terminal status", usage=usage)


def _finish_stream(acc: _GatewayAccumulator, request: GeneratorRequest,
                   eof_incomplete: bool, backend_fingerprint: str) -> GeneratorResult:
    state = acc.state
    if state.error is not None:
        return _terminal_result(request, CompletionOutcome.FAILED,
                                backend_fingerprint=backend_fingerprint, error=state.error)
    if state.terminal is None:
        if state.public_events == 0:
            return _terminal_result(
                request, CompletionOutcome.UNKNOWN_COMPLETION,
                backend_fingerprint=backend_fingerprint,
                error="stream ended without events after dispatch",
            )
        error = "stream ended without terminal success"
        if state.saw_done:
            error = "stream closed with [DONE] but no terminal success"
        if eof_incomplete:
            error = "stream truncated mid-frame without terminal"
        return _terminal_result(request, CompletionOutcome.INCOMPLETE,
                                backend_fingerprint=backend_fingerprint, text=acc.stream_text(),
                                error=error)
    kind, response = state.terminal
    usage = _parse_usage(response.get("usage"))
    if kind == "completed":
        status = response.get("status")
        if status != "completed":
            return _terminal_result(request, CompletionOutcome.FAILED,
                                    backend_fingerprint=backend_fingerprint,
                                    error="completed event with non-completed status", usage=usage)
        texts, refusal, structural = _collect_output(response.get("output"))
        if structural:
            return _terminal_result(request, CompletionOutcome.FAILED,
                                    backend_fingerprint=backend_fingerprint,
                                    error=structural, usage=usage)
        observed = state.item_order
        if observed:
            completed_ids = [
                item.get("id")
                for item in (response.get("output") or [])
                if isinstance(item, dict) and isinstance(item.get("id"), str)
            ]
            if completed_ids and completed_ids != observed:
                return _terminal_result(
                    request, CompletionOutcome.FAILED,
                    backend_fingerprint=backend_fingerprint,
                    error="completed output does not match observed item order", usage=usage,
                )
            # Type/identity is frozen from added through final: the final
            # array must carry the same type for every observed ID, or a
            # reasoning item could become a message (or vice versa) to
            # salvage text that never streamed.
            final_output = response.get("output")
            if isinstance(final_output, list):
                for observed_id, final_item in zip(observed, final_output):
                    if isinstance(final_item, dict) \
                            and final_item.get("id") == observed_id \
                            and final_item.get("type") != state.item_types.get(observed_id):
                        return _terminal_result(
                            request, CompletionOutcome.FAILED,
                            backend_fingerprint=backend_fingerprint,
                            error="item type changed in final output", usage=usage)
        streamed_text = acc.stream_text()
        completed_text = "\n".join(texts)
        if streamed_text is not None and completed_text != streamed_text:
            return _terminal_result(request, CompletionOutcome.FAILED,
                                    backend_fingerprint=backend_fingerprint,
                                    error="completed text mismatch with observed deltas",
                                    usage=usage)
        if refusal is not None:
            return _terminal_result(request, CompletionOutcome.REFUSAL,
                                    backend_fingerprint=backend_fingerprint,
                                    error=f"refusal: {refusal}", usage=usage)
        return _terminal_result(request, CompletionOutcome.TERMINAL,
                                backend_fingerprint=backend_fingerprint,
                                text=completed_text, usage=usage)
    if kind == "incomplete":
        return _terminal_result(request, CompletionOutcome.INCOMPLETE,
                                backend_fingerprint=backend_fingerprint,
                                text=acc.stream_text(), error=state.terminal_reason or "incomplete",
                                usage=usage)
    return _terminal_result(request, CompletionOutcome.FAILED,
                            backend_fingerprint=backend_fingerprint,
                            error=state.terminal_reason or "stream terminal failure", usage=usage)


class GatewayGenerator:
    """Callable gateway adapter for annotation/visual/answer purposes."""

    def __init__(
        self,
        config: GeneratorConfig,
        *,
        api_key: str | None = None,
        transport: GatewayTransport | None = None,
        image_resolver: ImageResolver | None = None,
        clock: Callable[[], float] | None = None,
    ) -> None:
        self._config = config
        self._api_key = api_key
        self._transport = transport
        self._image_resolver = image_resolver
        # Generator-local monotonic clock: the real monotonic clock by
        # default; an injected deterministic clock makes deadline boundary
        # tests exact without patching the global time module.
        self._clock = clock if clock is not None else time.monotonic

    @property
    def identity(self) -> ModelIdentity | None:
        """Identity of the configured route/model transport (no route -> None).

        Per-request :class:`ModelIdentity` still carries the model-specific
        declared capabilities; this identity identifies the route itself.
        """
        route = self._config.route
        if route is None:
            return None
        return ModelIdentity(name=route.model, adapter="gateway-responses")

    def _transport_instance(self) -> GatewayTransport:
        if self._transport is not None:
            return self._transport
        route = self._config.route
        if route is None:
            raise TransportConfigError("gateway route not configured")
        return GatewayTransport(
            route.base_url,
            timeout_seconds=route.timeout_seconds,
            api_key=self._api_key,
        )

    def _preflight(self, request: GeneratorRequest) -> tuple[dict, list[str]] | str:
        route = self._config.route
        if route is None:
            return "gateway route not configured"
        caps = route.capabilities
        required = request.required_capabilities
        if Capability.STREAMING in required and not caps.streaming:
            return "streaming control refused: route does not advertise Responses streaming"
        # Explicit minimum requirements are honored independently of the
        # actual format/cache-key fields: a constructor-validated request
        # may REQUIRE json_mode or prompt_caching while sending no
        # response_format or prompt_cache_key at all. A model declaration
        # alone is not route support (A13): unqualified minimums refuse
        # locally with zero HTTP; a qualified requirement alone does not
        # invent an output format or cache key.
        if Capability.JSON_MODE in required and not caps.json_mode:
            return "structured output refused: route does not advertise json_mode"
        if Capability.PROMPT_CACHING in required and not caps.prompt_caching:
            return "prompt caching refused: route does not advertise prompt_caching"
        # Vision is gated by route AND model, even when the caller omits the
        # capability from required_capabilities: the semantic input shape,
        # not caller declarations, gates transport, and required
        # capabilities cannot widen the model's declared capabilities.
        if request.images or Capability.VISION in required:
            if not caps.vision:
                return "vision control refused: route does not advertise vision input"
            if request.images and Capability.VISION not in request.model.declared_capabilities:
                return "vision control refused: model does not declare vision input"
        if request.response_format == "json_object" and not caps.json_mode:
            return "structured output refused: route does not advertise json_mode"
        if request.response_format == "json_schema" and not caps.structured_outputs:
            return "structured output refused: route does not advertise structured_outputs"
        if request.prompt_cache_key and not caps.prompt_caching:
            return "prompt caching refused: route does not advertise prompt_caching"
        # The request output budget must fit the configured output reserve;
        # exceeding it is refused before dispatch, never silently clipped.
        if request.max_output_tokens > self._config.output_reserve_tokens:
            return ("output budget refused: max_output_tokens exceeds "
                    "configured output reserve")
        materials: list[str] = []
        if request.images:
            if self._image_resolver is None:
                return "vision transport not materialized (no trusted image resolver configured)"
            for ref in request.images:
                try:
                    material = self._image_resolver.resolve(ref)
                except Exception:
                    return "image resolution failed for authorized reference"
                if not (
                    isinstance(material, str)
                    and (material.startswith(_SAFE_IMAGE_PREFIXES)
                         or _SAFE_IMAGE_URL_RE.fullmatch(material))
                ):
                    return "image material is not bounded safe URL/data form"
                if len(material.encode("utf-8")) > _MAX_IMAGE_MATERIAL_BYTES:
                    return "image material exceeds bounded size"
                materials.append(material)
        stream = Capability.STREAMING in required
        try:
            envelope = build_responses_envelope(request, route, stream=stream,
                                                image_materials=materials or None)
        except ValueError:
            return "image material count mismatch"
        return envelope, materials

    def generate(self, request: GeneratorRequest) -> GeneratorResult:
        """Run one bounded gateway generation; expected failures are safe results."""
        route = self._config.route
        backend_fingerprint = gateway_backend_fingerprint(route) if route is not None else None
        preflight = self._preflight(request)
        if isinstance(preflight, str):
            return _terminal_result(request, CompletionOutcome.FAILED,
                                    backend_fingerprint=backend_fingerprint, error=preflight)
        envelope, _ = preflight
        try:
            transport = self._transport_instance()
        except TransportConfigError as exc:
            return _terminal_result(request, CompletionOutcome.FAILED,
                                    backend_fingerprint=backend_fingerprint, error=str(exc))
        stream = Capability.STREAMING in request.required_capabilities
        deadline = self._clock() + min(request.deadline_seconds,
                                       self._config.deadline_seconds)
        payload = json.dumps(envelope, sort_keys=True, separators=(",", ":"),
                             ensure_ascii=True).encode("utf-8")
        max_attempts = 1 + self._config.max_retries
        attempts = 0
        while True:
            # One total budget for the whole call, including retries: once
            # it is exhausted no further attempt may be dispatched.
            if self._clock() >= deadline:
                return _terminal_result(request, CompletionOutcome.FAILED,
                                        backend_fingerprint=backend_fingerprint,
                                        error="deadline exhausted before dispatch",
                                        attempts=attempts)
            attempts += 1
            try:
                if stream:
                    result = self._run_stream(transport, request, payload, deadline,
                                              backend_fingerprint)
                else:
                    status, body = transport.post_json(RESPONSES_PATH, payload, deadline=deadline)
                    if status >= 400:
                        return _terminal_result(
                            request,
                            CompletionOutcome.FAILED,
                            backend_fingerprint=backend_fingerprint,
                            error=f"request refused (HTTP {status})",
                            attempts=attempts,
                        )
                    result = _parse_non_stream(body, request, backend_fingerprint)
                return result.model_copy(update={"attempts": attempts})
            except TransportConnectError as exc:
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
                # Post-dispatch network failure (e.g. the provider closed the
                # connection after accepting the request) leaves completion
                # unknown (V2-03); only a positively pre-dispatch failure is a
                # safe definite failure.
                outcome = (CompletionOutcome.UNKNOWN_COMPLETION
                           if exc.dispatched else CompletionOutcome.FAILED)
                return _terminal_result(request, outcome,
                                        backend_fingerprint=backend_fingerprint,
                                        error=str(exc), attempts=attempts)

    def _run_stream(self, transport: GatewayTransport, request: GeneratorRequest,
                    payload: bytes, deadline: float,
                    backend_fingerprint: str) -> GeneratorResult:
        acc = _GatewayAccumulator()
        try:
            with transport.open_stream(RESPONSES_PATH, payload, deadline=deadline) as handle:
                frames = handle.frames()
                for frame in frames:
                    if frame.event == "message" and frame.data == "[DONE]":
                        acc.state.saw_done = True
                        continue
                    acc.handle(frame)
                return _finish_stream(acc, request, eof_incomplete=frames.incomplete_trailing,
                                      backend_fingerprint=backend_fingerprint)
        except TransportConnectError:
            if acc.state.error is not None:
                return _finish_stream(acc, request, eof_incomplete=False,
                                      backend_fingerprint=backend_fingerprint)
            raise  # positively pre-dispatch: the outer retry policy decides
        except TransportTimeoutError as exc:
            if acc.state.error is not None:
                return _finish_stream(acc, request, eof_incomplete=False,
                                      backend_fingerprint=backend_fingerprint)
            if exc.retryable:
                raise  # pre-dispatch timeout: the outer retry policy decides
            text = acc.stream_text()
            return _terminal_result(
                request, CompletionOutcome.UNKNOWN_COMPLETION,
                backend_fingerprint=backend_fingerprint,
                text=text, error="deadline exhausted mid-stream",
            )
        except TransportRefusedError as exc:
            if acc.state.error is not None:
                return _finish_stream(acc, request, eof_incomplete=False,
                                      backend_fingerprint=backend_fingerprint)
            # A definitive provider response (redirect/4xx/5xx headers were
            # read): a safe failure, never an ambiguous completion.
            return _terminal_result(request, CompletionOutcome.FAILED,
                                    backend_fingerprint=backend_fingerprint,
                                    error=str(exc))
        except (TransportProtocolError, TransportTruncatedError) as exc:
            if acc.state.error is not None:
                return _finish_stream(acc, request, eof_incomplete=False,
                                      backend_fingerprint=backend_fingerprint)
            return _terminal_result(
                request, CompletionOutcome.FAILED,
                backend_fingerprint=backend_fingerprint, error=str(exc),
            )
        except TransportError as exc:
            if acc.state.error is not None:
                return _finish_stream(acc, request, eof_incomplete=False,
                                      backend_fingerprint=backend_fingerprint)
            text = acc.stream_text()
            return _terminal_result(
                request, CompletionOutcome.UNKNOWN_COMPLETION,
                backend_fingerprint=backend_fingerprint,
                text=text, error=f"stream interrupted: {exc}",
            )
