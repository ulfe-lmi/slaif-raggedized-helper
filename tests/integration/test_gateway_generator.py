"""Full GatewayGenerator behavior tests against owned loopback HTTP (003-b).

Acceptance coverage (oap/orders/003-b criteria 5-7, 003-c protocol
validation, all at generator level over real loopback HTTP):

- the pinned bounded Responses envelope is the only wire content (native
  cache_prompt/id_slot/slot_ids impossible; secret only in the header);
- pre-dispatch capability refusals (stream/vision/structured/cache/output
  budget) never reach the server; actual image input requires route AND
  declared-model vision plus a trusted bounded resolver even when
  required_capabilities omits VISION;
- the actual wire path is /v1/responses for both root and versioned bases
  (never a duplicated /v1/v1/responses), asserted on the recording server;
- accepted-POST-then-close and delayed-header probes return
  UNKNOWN_COMPLETION with no duplicate attempts (exact full-generator
  regression of the 003-b strategic observation, not helper assertions);
- one total budget spans attempts: an expired deadline refuses before
  dispatch/re-dispatch, both normal and streaming;
- output parsing follows the EXACT pinned dialect (f2df0e82): data-only
  SSE frames whose discriminator is the JSON "type" field, envelope-level
  output_index on output_item events, final output items WITHOUT
  output_index; ordered multiple message items; duplicate/foreign/
  out-of-order IDs refused; delta/cumulative/done reconciliation;
  supported non-text terminal states validated (an in-progress reasoning
  item in a final completed response is contradictory, never silently
  skipped); unsupported function_call actions are refused, never salvaged;
  terminal/EOF outcome mapping; refusals/incomplete/failed never become
  success; completed responses without usable text are failures;
  003-c: non-string delta/done types, missing/malformed/conflicting
  terminal response IDs, wrong delta/part output_index, nonterminal
  item.done status, malformed final status objects ({} and []), and
  excessive JSON nesting all fail safe (typed failure, no raw
  exception, no salvaged answer); valid streams with multiple bounded
  content parts and multiple message items succeed with exact text and
  part lifecycle violations fail closed; refusal/incomplete/failed
  terminals keep their distinctions and canary safety; the zero-dispatch
  deadline boundary is a deterministic generator-local clock, not a
  measured machine overhead;
- canaries in provider error/refusal fields never leak into results;
- stable declared backend identity independent of request ID/answer text,
  sensitive to endpoint (port/scheme) and model changes.
"""

from __future__ import annotations

import json
import time

import pytest

from conftest import SYNTHETIC_API_KEY, sse_data_only, sse_frame

from slaif_raggedized_helper.config import (
    GeneratorConfig,
    RouteCapabilities,
    RouteConfig,
)
from slaif_raggedized_helper.model_clients.gateway import (
    GatewayGenerator,
    gateway_backend_fingerprint,
)
from slaif_raggedized_helper.model_clients.transport import TransportConnectError
from slaif_raggedized_helper.schema import (
    Capability,
    CompletionOutcome,
    GeneratorPurpose,
    GeneratorRequest,
    ImageRef,
    ModelIdentity,
    TextItem,
)

_TOLERANCE = 0.35


# ---------------------------------------------------------------------------
# fixtures / helpers
# ---------------------------------------------------------------------------

def make_config(base_url: str, caps: RouteCapabilities | None = None, *,
                timeout_seconds: float = 5.0, max_retries: int = 2) -> GeneratorConfig:
    return GeneratorConfig(
        route=RouteConfig(
            base_url=base_url,
            model="synthetic-qwen",
            timeout_seconds=timeout_seconds,
            capabilities=caps or RouteCapabilities(),
        ),
        context_expected_tokens=1024,
        output_reserve_tokens=64,
        deadline_seconds=30,
        max_retries=max_retries,
    )


def make_request(*, stream: bool = False, deadline: float = 30.0,
                 text: str = "say hello", request_id: str = "req-1",
                 required_capabilities=None, model=None,
                 max_output_tokens: int = 16, **kwargs) -> GeneratorRequest:
    caps = {Capability.TEXT}
    if stream:
        caps.add(Capability.STREAMING)
    if required_capabilities is None:
        required_capabilities = {Capability.STREAMING} if stream else set()
    if model is None:
        model = ModelIdentity(name="synthetic-qwen",
                              declared_capabilities=frozenset(caps))
    return GeneratorRequest(
        request_id=request_id,
        purpose=GeneratorPurpose.ANSWER,
        items=[TextItem(text=text)],
        model=model,
        required_capabilities=frozenset(required_capabilities),
        max_output_tokens=max_output_tokens,
        deadline_seconds=deadline,
        **kwargs,
    )


def make_generator(config: GeneratorConfig) -> GatewayGenerator:
    return GatewayGenerator(config, api_key=SYNTHETIC_API_KEY)


def completed_json(output, usage=None, status="completed", **extra):
    """Pinned top-level completed/failed/incomplete response shape."""
    doc = {
        "id": "resp_pinned_1",
        "object": "response",
        "created_at": 123,
        "status": status,
        "model": "synthetic-qwen",
        "output": output,
    }
    if usage is not None:
        doc["usage"] = usage
    doc.update(extra)
    return doc


def message_item(item_id: str, text: str, status: str = "completed", **extra):
    """One final-dialect message item: array-ordered, NO output_index."""
    if status == "refusal":
        content = [{"type": "refusal", "refusal": "content_filter"}]
    else:
        content = [{"type": "output_text", "text": text,
                    "annotations": [], "logprobs": None}]
    item = {
        "id": item_id,
        "type": "message",
        "status": status,
        "role": "assistant",
        "content": content,
        "phase": None,
    }
    item.update(extra)
    return item


def reasoning_item(item_id: str, status: str = "completed"):
    return {
        "id": item_id,
        "type": "reasoning",
        "status": status,
        "summary": [],
        "content": [],
        "encrypted_content": None,
    }


def function_call_item(item_id: str, status: str = "completed"):
    return {
        "id": item_id,
        "type": "function_call",
        "status": status,
        "namespace": None,
        "name": "local_lookup",
        "arguments": "{}",
        "call_id": "call_1",
        "caller": None,
    }


def valid_stream_frames(text: str = "Hello world", response_id: str = "resp_1"):
    """Exact pinned-dialect stream: data-only frames (JSON "type"
    discriminator, no SSE event names) with envelope-level output_index;
    the final response.completed output item carries NO output_index.
    """
    completed_response = {
        "id": response_id,
        "object": "response",
        "created_at": 123,
        "status": "completed",
        "model": "synthetic-qwen",
        "output": [message_item("msg_1", text)],
        "usage": {"input_tokens": 10, "output_tokens": 2},
    }
    return [
        sse_data_only({"type": "response.created",
                       "response": {"id": response_id, "status": "in_progress"}}),
        sse_data_only({"type": "response.output_item.added", "output_index": 0,
                       "item": {"type": "message", "id": "msg_1",
                                "status": "in_progress", "role": "assistant",
                                "content": [], "phase": None}}),
        sse_data_only({"type": "response.output_text.delta", "item_id": "msg_1",
                       "output_index": 0, "delta": "Hello"}),
        sse_data_only({"type": "response.output_text.delta", "item_id": "msg_1",
                       "output_index": 0, "delta": " world"}),
        sse_data_only({"type": "response.output_text.done", "item_id": "msg_1",
                       "output_index": 0, "text": text}),
        sse_data_only({"type": "response.output_item.done", "output_index": 0,
                       "item": {"type": "message", "id": "msg_1",
                                "status": "completed", "role": "assistant",
                                "content": [{"type": "output_text", "text": text,
                                             "annotations": [], "logprobs": None}],
                                "phase": None}}),
        sse_data_only({"type": "response.completed",
                       "response": completed_response}),
    ]


def stream_scenario(frames):
    def scenario(h, r):
        h._send_headers_only()
        for frame in frames:
            h._write_stream(frame)

    return scenario


class _BudgetConsumingFakeTransport:
    """Injectable fake transport: consumes the whole budget, then fails as a
    positively pre-dispatch connect failure (retryable by policy)."""

    def __init__(self) -> None:
        self.calls = 0

    def post_json(self, path, body, *, deadline=None):
        self.calls += 1
        time.sleep(0.3)
        raise TransportConnectError("fake pre-dispatch connect failure")

    def open_stream(self, path, body, *, deadline=None):
        self.calls += 1
        time.sleep(0.3)
        raise TransportConnectError("fake pre-dispatch connect failure")


class _SteppingClock:
    """Deterministic generator-local clock: call n returns n*step.

    Injected into GatewayGenerator (whose default remains the real
    monotonic clock) so the deadline boundary is exact and
    machine-independent, without patching the global time module."""

    def __init__(self, step: float) -> None:
        self.step = step
        self.calls = 0

    def __call__(self) -> float:
        value = self.step * self.calls
        self.calls += 1
        return value


def make_fake_generator(config: GeneratorConfig, stream: bool = False) -> tuple[
        GatewayGenerator, _BudgetConsumingFakeTransport]:
    fake = _BudgetConsumingFakeTransport()
    gen = GatewayGenerator(config, api_key=SYNTHETIC_API_KEY, transport=fake)
    return gen, fake


# ---------------------------------------------------------------------------
# envelope, wire path, secrets, pinned dialect
# ---------------------------------------------------------------------------

def test_stream_full_dialect_terminal_with_exact_envelope(server):
    srv = server(stream_scenario(valid_stream_frames()))
    caps = RouteCapabilities(streaming=True)
    gen = make_generator(make_config(f"{srv.url}/v1", caps))
    result = gen.generate(make_request(stream=True))
    assert result.outcome is CompletionOutcome.TERMINAL
    assert result.text == "Hello world"
    assert result.attempts == 1
    assert result.usage is not None
    assert result.usage.input_tokens == 10
    assert result.usage.output_tokens == 2
    assert result.fingerprint == gateway_backend_fingerprint(
        make_config(f"{srv.url}/v1", caps).route)
    # Exact wire path (never a duplicated /v1/v1/responses) and one call only.
    assert srv.paths == ["/v1/responses"]
    req = srv.state.requests[0]
    assert req.headers["authorization"] == f"Bearer {SYNTHETIC_API_KEY}"
    envelope = json.loads(req.body)
    assert envelope["model"] == "synthetic-qwen"
    assert envelope["store"] is False
    assert envelope["stream"] is True
    assert envelope["max_output_tokens"] == 16
    assert envelope["input"] == [{"type": "message", "role": "user",
                                  "content": [{"type": "input_text", "text": "say hello"}]}]
    body = req.body.decode("utf-8")
    for native_field in ("cache_prompt", "id_slot", "slot_ids"):
        assert native_field not in body  # native direct fields never on the wire
    assert SYNTHETIC_API_KEY not in body  # secret stays in the header only


def test_data_only_frames_are_the_supported_dialect(server):
    raw = b"".join(valid_stream_frames())
    assert b"event:" not in raw  # the pinned gateway never sends SSE event names
    srv = server(stream_scenario(valid_stream_frames()))
    caps = RouteCapabilities(streaming=True)
    result = make_generator(make_config(f"{srv.url}/v1", caps)).generate(
        make_request(stream=True))
    assert result.outcome is CompletionOutcome.TERMINAL
    assert result.text == "Hello world"


def test_pinned_completed_fixture_is_terminal(server):
    """Exact shape of the pinned gateway e2e completed response (f2df0e82,
    tests/e2e/test_openai_python_client_responses.py): final message WITHOUT
    output_index; part carries annotations/logprobs; vllm-style usage."""
    completed = {
        "id": "codex-0149-signed-response",
        "object": "response",
        "created_at": 123,
        "status": "completed",
        "model": "synthetic-qwen",
        "output": [
            {
                "type": "message",
                "id": "parser_message_1",
                "status": "completed",
                "role": "assistant",
                "content": [
                    {
                        "type": "output_text",
                        "text": "answer",
                        "annotations": [],
                        "logprobs": None,
                    }
                ],
                "phase": None,
            }
        ],
        "usage": {
            "input_tokens": 3,
            "input_tokens_details": {"cached_tokens": 0,
                                     "input_tokens_per_turn": [3],
                                     "cached_tokens_per_turn": [0]},
            "output_tokens": 2,
            "output_tokens_details": {"reasoning_tokens": 0,
                                      "tool_output_tokens": 0,
                                      "output_tokens_per_turn": [2],
                                      "tool_output_tokens_per_turn": [0]},
            "total_tokens": 5,
        },
    }
    srv = server(lambda h, r: h._send_json(200, completed))
    result = make_generator(make_config(f"{srv.url}/v1")).generate(make_request())
    assert result.outcome is CompletionOutcome.TERMINAL
    assert result.text == "answer"
    assert result.usage.input_tokens == 3
    assert result.usage.cache_hit_tokens == 0
    assert result.usage.output_tokens == 2
    assert srv.paths == ["/v1/responses"]


def test_explicit_event_name_agreement_is_accepted(server):
    # When an SSE event name IS present it must agree with the JSON type.
    frames = [
        sse_frame("response.created",
                  {"type": "response.created",
                   "response": {"id": "r1", "status": "in_progress"}}),
        sse_frame("response.completed",
                  {"type": "response.completed",
                   "response": {"id": "r1", "status": "completed",
                                "output": [message_item("m0", "ok")],
                                "usage": {"input_tokens": 1, "output_tokens": 1}}}),
    ]
    srv = server(stream_scenario(frames))
    caps = RouteCapabilities(streaming=True)
    result = make_generator(make_config(f"{srv.url}/v1", caps)).generate(
        make_request(stream=True))
    assert result.outcome is CompletionOutcome.TERMINAL
    assert result.text == "ok"


def test_explicit_event_name_disagreement_refused(server):
    # A present event name that disagrees with the JSON discriminator is a
    # protocol violation: fail closed, never treat as an unknown family.
    frames = [
        sse_frame("response.output_item.added",
                  {"type": "response.created",
                   "response": {"id": "r1", "status": "in_progress"}}),
        sse_frame("response.completed",
                  {"type": "response.completed",
                   "response": {"id": "r1", "status": "completed",
                                "output": [message_item("m0", "ok")],
                                "usage": {"input_tokens": 1, "output_tokens": 1}}}),
    ]
    srv = server(stream_scenario(frames))
    caps = RouteCapabilities(streaming=True)
    result = make_generator(make_config(f"{srv.url}/v1", caps)).generate(
        make_request(stream=True))
    assert result.outcome is CompletionOutcome.FAILED
    assert "event name and payload type disagree" in (result.error or "")


def test_root_base_hits_same_endpoint(server):
    srv = server(stream_scenario(valid_stream_frames()))
    caps = RouteCapabilities(streaming=True)
    gen = make_generator(make_config(f"{srv.url}", caps))  # root base, no /v1 suffix
    result = gen.generate(make_request(stream=True))
    assert result.outcome is CompletionOutcome.TERMINAL
    assert srv.paths == ["/v1/responses"]


def test_non_stream_multiple_message_items_in_order(server):
    def scenario(h, r):
        h._send_json(200, completed_json(
            [message_item("m0", "t1"), message_item("m1", "t2")],
            usage={"input_tokens": 3, "output_tokens": 7}))

    srv = server(scenario)
    gen = make_generator(make_config(f"{srv.url}/v1"))
    result = gen.generate(make_request())
    assert result.outcome is CompletionOutcome.TERMINAL
    assert result.text == "t1\nt2"
    assert result.usage.input_tokens == 3
    assert srv.paths == ["/v1/responses"]


# ---------------------------------------------------------------------------
# exact full-generator regressions: accepted POST then close / no headers
# ---------------------------------------------------------------------------

def test_full_generator_post_send_close_unknown_no_retry(server):
    """Strategic 003-b observation, non-streaming: server accepts the POST
    then closes before any headers -> UNKNOWN_COMPLETION, attempts == 1
    (no duplicate despite max_retries=2), exact wire path, safe error text.
    """

    def scenario(h, r):
        h._accept_then_close()

    srv = server(scenario)
    config = make_config(f"{srv.url}/v1", timeout_seconds=0.2, max_retries=2)
    result = make_generator(config).generate(make_request(deadline=0.4))
    assert result.outcome is CompletionOutcome.UNKNOWN_COMPLETION
    assert result.attempts == 1
    assert result.error
    assert "CANARY" not in json.dumps(result.model_dump())
    assert srv.paths == ["/v1/responses"]  # accepted exactly once, correct endpoint


def test_full_generator_stream_post_send_close_unknown_no_retry(server):
    def scenario(h, r):
        h._accept_then_close()

    srv = server(scenario)
    caps = RouteCapabilities(streaming=True)
    config = make_config(f"{srv.url}/v1", caps, timeout_seconds=0.2, max_retries=2)
    result = make_generator(config).generate(make_request(stream=True, deadline=0.4))
    assert result.outcome is CompletionOutcome.UNKNOWN_COMPLETION
    assert result.attempts == 1
    assert result.error
    assert srv.paths == ["/v1/responses"]


def test_full_generator_header_delay_unknown_no_retry(server):
    def scenario(h, r):
        time.sleep(0.8)  # past the 0.2s per-operation timeout
        h._send_json(200, completed_json([message_item("m0", "late")]))

    srv = server(scenario)
    config = make_config(f"{srv.url}/v1", timeout_seconds=0.2, max_retries=2)
    start = time.monotonic()
    result = make_generator(config).generate(make_request(deadline=5.0))
    assert result.outcome is CompletionOutcome.UNKNOWN_COMPLETION
    assert result.attempts == 1
    assert srv.paths == ["/v1/responses"]
    assert time.monotonic() - start < 5.0


def test_pre_connect_retry_policy_is_finite(closed_port):
    config = make_config(f"http://127.0.0.1:{closed_port}", max_retries=2)
    result = make_generator(config).generate(make_request(deadline=10.0))
    assert result.outcome is CompletionOutcome.FAILED
    assert result.attempts == 3  # 1 + max_retries, finite allowed policy
    assert "connect" in (result.error or "")


@pytest.mark.parametrize("stream", [False, True], ids=["non-stream", "stream"])
def test_budget_exhausted_retry_refused_before_dispatch(server, stream):
    """A pre-dispatch failure that consumes the whole budget must NOT be
    retried: the loop-top deadline guard refuses before any dispatch."""
    srv = server(lambda h, r: h._send_json(
        200, completed_json([message_item("m0", "x")])))
    caps = RouteCapabilities(streaming=stream)
    gen, fake = make_fake_generator(make_config(f"{srv.url}/v1", caps))
    result = gen.generate(make_request(stream=stream, deadline=0.15))
    assert result.outcome is CompletionOutcome.FAILED
    assert "deadline exhausted before dispatch" in (result.error or "")
    assert result.attempts == 1
    assert fake.calls == 1  # the retry was never dispatched
    assert srv.state.requests == []


@pytest.mark.parametrize("stream", [False, True], ids=["non-stream", "stream"])
def test_already_expired_deadline_refused_before_any_dispatch(server, stream):
    """A deadline already expired when generate() runs refuses with zero
    attempts and zero transport calls (both normal and streaming).

    The boundary is deterministic: a generator-local clock returns 0.0
    when the deadline is computed (deadline = 0.0 + 1.0 = 1.0) and 1.0
    at the loop-top guard, already past the deadline — no measured
    machine overhead and no global time-module patching. The consuming
    fake guards the retry path: if the entry check were ever bypassed,
    the whole budget would burn and the loop-top guard would still
    refuse, making the anomaly visible as a test failure."""
    srv = server(lambda h, r: h._send_json(
        200, completed_json([message_item("m0", "x")])))
    caps = RouteCapabilities(streaming=stream)
    config = make_config(f"{srv.url}/v1", caps)

    fake = _BudgetConsumingFakeTransport()
    gen = GatewayGenerator(config, api_key=SYNTHETIC_API_KEY, transport=fake,
                           clock=_SteppingClock(1.0))
    result = gen.generate(make_request(stream=stream, deadline=1.0))
    assert result.outcome is CompletionOutcome.FAILED
    assert "deadline exhausted before dispatch" in (result.error or "")
    assert result.attempts == 0
    assert fake.calls == 0  # nothing was ever dispatched
    assert srv.state.requests == []


# ---------------------------------------------------------------------------
# pre-dispatch capability refusals
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("request_kwargs, caps", [
    (dict(stream=True), RouteCapabilities()),  # streaming not advertised
    (dict(response_format="json_object"), RouteCapabilities()),
    (dict(response_format="json_schema",
          json_schema={"type": "object"}), RouteCapabilities()),
    (dict(prompt_cache_key="pk-1",
          required_capabilities=frozenset({Capability.PROMPT_CACHING}),
          model=ModelIdentity(name="synthetic-qwen",
                              declared_capabilities=frozenset({Capability.TEXT,
                                                               Capability.PROMPT_CACHING}))
          ), RouteCapabilities()),
])
def test_unsupported_controls_refused_before_dispatch(server, request_kwargs, caps):
    srv = server(stream_scenario(valid_stream_frames()))
    gen = make_generator(make_config(f"{srv.url}/v1", caps))
    request = make_request(**request_kwargs)
    result = gen.generate(request)
    assert result.outcome is CompletionOutcome.FAILED
    assert "refused" in (result.error or "")
    assert result.attempts is None or result.attempts == 0
    assert srv.state.requests == []  # nothing reached the provider


def test_image_requires_vision_and_resolver_even_if_omitted(server):
    srv = server(stream_scenario(valid_stream_frames()))
    gen = make_generator(make_config(f"{srv.url}/v1", RouteCapabilities()))
    request = make_request(
        images=[ImageRef(image_id="img-1", source_revision="rev-1")],
        model=ModelIdentity(name="synthetic-qwen",
                            declared_capabilities=frozenset({Capability.TEXT,
                                                             Capability.VISION})))
    result = gen.generate(request)
    assert result.outcome is CompletionOutcome.FAILED
    assert "vision control refused: route" in (result.error or "")
    assert srv.state.requests == []


def test_image_requires_declared_model_vision(server):
    """Route vision alone is not enough: the requested model must also
    declare vision, even when required_capabilities omits it."""
    srv = server(stream_scenario(valid_stream_frames()))
    gen = make_generator(make_config(f"{srv.url}/v1", RouteCapabilities(vision=True)))
    request = make_request(
        images=[ImageRef(image_id="img-1", source_revision="rev-1")])  # TEXT only
    result = gen.generate(request)
    assert result.outcome is CompletionOutcome.FAILED
    assert "model does not declare vision" in (result.error or "")
    assert srv.state.requests == []


def test_image_resolver_unsafe_or_failing_material_refused(server):
    srv = server(stream_scenario(valid_stream_frames()))
    caps = RouteCapabilities(vision=True)
    vision_model = ModelIdentity(name="synthetic-qwen",
                                 declared_capabilities=frozenset({Capability.TEXT,
                                                                  Capability.VISION}))

    class Resolver:
        def __init__(self, behavior):
            self.behavior = behavior

        def resolve(self, ref):
            if self.behavior == "unsafe":
                return "file:///etc/canary-image"
            if self.behavior == "oversize":
                return "data:image/png;base64," + "A" * (5 * 1024 * 1024)
            raise RuntimeError("resolver blew up")

    request = make_request(images=[ImageRef(image_id="img-1", source_revision="rev-1")],
                           model=vision_model)
    for behavior, needle in (("no-resolver", "no trusted image resolver"),
                             ("unsafe", "not bounded safe"),
                             ("oversize", "bounded size"),
                             ("raising", "image resolution failed")):
        if behavior == "no-resolver":
            gen = make_generator(make_config(f"{srv.url}/v1", caps))
        else:
            gen = GatewayGenerator(make_config(f"{srv.url}/v1", caps),
                                   api_key=SYNTHETIC_API_KEY,
                                   image_resolver=Resolver(behavior))
        result = gen.generate(request)
        assert result.outcome is CompletionOutcome.FAILED, behavior
        assert needle in (result.error or ""), behavior
        assert "canary-image" not in json.dumps(result.model_dump())
    assert srv.state.requests == []  # every case refused before dispatch


def test_image_with_safe_resolver_dispatches(server):
    data_url = "data:image/png;base64," + "AAAA"
    srv = server(lambda h, r: h._send_json(
        200, completed_json([message_item("m0", "an image")],
                            usage={"input_tokens": 5, "output_tokens": 1})))

    class Resolver:
        def resolve(self, ref):
            return data_url

    caps = RouteCapabilities(vision=True)
    vision_model = ModelIdentity(name="synthetic-qwen",
                                 declared_capabilities=frozenset({Capability.TEXT,
                                                                  Capability.VISION}))
    gen = GatewayGenerator(make_config(f"{srv.url}/v1", caps),
                           api_key=SYNTHETIC_API_KEY, image_resolver=Resolver())
    request = make_request(images=[ImageRef(image_id="img-1", source_revision="rev-1")],
                           model=vision_model)
    result = gen.generate(request)
    assert result.outcome is CompletionOutcome.TERMINAL
    assert srv.paths == ["/v1/responses"]
    envelope = json.loads(srv.state.requests[0].body)
    assert {"type": "input_image", "image_url": data_url} in envelope["input"][0]["content"]


def test_max_output_tokens_over_reserve_refused_before_dispatch(server):
    srv = server(stream_scenario(valid_stream_frames()))
    gen = make_generator(make_config(f"{srv.url}/v1"))  # output_reserve_tokens=64
    result = gen.generate(make_request(max_output_tokens=65))
    assert result.outcome is CompletionOutcome.FAILED
    assert "output reserve" in (result.error or "")
    assert srv.state.requests == []


# ---------------------------------------------------------------------------
# deterministic refusals, redirects, canaries
# ---------------------------------------------------------------------------

def test_4xx_with_canary_body_is_safe_refusal(server):
    srv = server(lambda h, r: h._send_json(400, {"error": {"code": "CANARY-CODE",
                                                           "message": "CANARY-MSG"}}))
    result = make_generator(make_config(f"{srv.url}/v1")).generate(make_request())
    assert result.outcome is CompletionOutcome.FAILED
    assert result.error == "request refused (HTTP 400)"
    assert "CANARY" not in json.dumps(result.model_dump())
    assert srv.paths == ["/v1/responses"]


def test_stream_4xx_with_canary_body_is_safe_refusal(server):
    srv = server(lambda h, r: h._send_raw(400, b'{"error":"CANARY-MSG"}', "application/json"))
    caps = RouteCapabilities(streaming=True)
    result = make_generator(make_config(f"{srv.url}/v1", caps)).generate(
        make_request(stream=True))
    assert result.outcome is CompletionOutcome.FAILED
    assert result.error == "request refused (HTTP 400)"
    assert "CANARY" not in json.dumps(result.model_dump())
    assert srv.paths == ["/v1/responses"]


def test_redirect_refused_at_gateway(server):
    sink = server(lambda h, r: h._send_json(200, {"ok": True}))
    srv = server(
        lambda h, r: (
            h.send_response(302),
            h.send_header("Location", f"{sink.url}/stolen"),
            h.send_header("Content-Length", "0"),
            h.send_header("Connection", "close"),
            h.end_headers(),
        )
    )
    result = make_generator(make_config(f"{srv.url}/v1")).generate(make_request())
    assert result.outcome is CompletionOutcome.FAILED
    assert "redirect refused" in (result.error or "")
    assert srv.paths == ["/v1/responses"]
    assert sink.state.requests == []


def test_non_stream_refusal_with_allowlisted_reason(server):
    item = message_item("m0", "", status="refusal",
                        content=[{"type": "refusal", "refusal": "content_filter"}])
    srv = server(lambda h, r: h._send_json(200, completed_json([item])))
    result = make_generator(make_config(f"{srv.url}/v1")).generate(make_request())
    assert result.outcome is CompletionOutcome.REFUSAL
    assert result.error == "refusal: content_filter"


def test_stream_refusal_with_allowlisted_reason(server):
    refusal_item = message_item("m0", "", status="refusal",
                                content=[{"type": "refusal", "refusal": "content_filter"}])
    response = {"id": "r1", "object": "response", "created_at": 1,
                "status": "completed", "model": "synthetic-qwen",
                "output": [refusal_item],
                "usage": {"input_tokens": 1, "output_tokens": 1}}
    frames = [
        sse_data_only({"type": "response.created",
                       "response": {"id": "r1", "status": "in_progress"}}),
        sse_data_only({"type": "response.output_item.added", "output_index": 0,
                       "item": {"type": "message", "id": "m0",
                                "status": "in_progress", "role": "assistant",
                                "content": [], "phase": None}}),
        sse_data_only({"type": "response.output_item.done", "output_index": 0,
                       "item": refusal_item}),
        sse_data_only({"type": "response.completed", "response": response}),
    ]
    srv = server(stream_scenario(frames))
    caps = RouteCapabilities(streaming=True)
    result = make_generator(make_config(f"{srv.url}/v1", caps)).generate(
        make_request(stream=True))
    assert result.outcome is CompletionOutcome.REFUSAL
    assert result.error == "refusal: content_filter"


def test_unknown_refusal_reason_is_fixed_safe(server):
    item = message_item("m0", "", status="refusal",
                        content=[{"type": "refusal", "refusal": "CANARY-REFUSAL-XYZ"}])
    srv = server(lambda h, r: h._send_json(200, completed_json([item])))
    result = make_generator(make_config(f"{srv.url}/v1")).generate(make_request())
    assert result.outcome is CompletionOutcome.REFUSAL
    assert result.error == "refusal: refusal"
    assert "CANARY" not in json.dumps(result.model_dump())


def test_failed_status_canary_not_leaked(server):
    srv = server(lambda h, r: h._send_json(
        200, completed_json([message_item("m0", "x")], status="failed",
                            error={"code": "CANARY-CODE", "message": "CANARY-MSG"})))
    result = make_generator(make_config(f"{srv.url}/v1")).generate(make_request())
    assert result.outcome is CompletionOutcome.FAILED
    assert result.error == "provider failure"
    assert "CANARY" not in json.dumps(result.model_dump())


def test_stream_error_event_canary_not_leaked(server):
    frames = [
        sse_data_only({"type": "response.created", "response": {"id": "r1"}}),
        sse_data_only({"type": "error", "code": "CANARY-CODE",
                       "message": "CANARY-MSG"}),
    ]
    srv = server(stream_scenario(frames))
    caps = RouteCapabilities(streaming=True)
    result = make_generator(make_config(f"{srv.url}/v1", caps)).generate(
        make_request(stream=True))
    assert result.outcome is CompletionOutcome.FAILED
    assert result.error == "provider error"
    assert "CANARY" not in json.dumps(result.model_dump())


# ---------------------------------------------------------------------------
# output parsing: structure, ordering, reconciliation, EOF outcomes
# ---------------------------------------------------------------------------

def test_duplicate_output_item_id_refused(server):
    srv = server(lambda h, r: h._send_json(
        200, completed_json([message_item("m0", "a"), message_item("m0", "b")])))
    result = make_generator(make_config(f"{srv.url}/v1")).generate(make_request())
    assert result.outcome is CompletionOutcome.FAILED
    assert "duplicate output item ID" in (result.error or "")


def test_out_of_order_output_index_refused(server):
    # A genuinely present final-item index must equal its array position.
    srv = server(lambda h, r: h._send_json(
        200, completed_json([message_item("m0", "a", output_index=1)])))
    result = make_generator(make_config(f"{srv.url}/v1")).generate(make_request())
    assert result.outcome is CompletionOutcome.FAILED
    assert "out-of-order output item" in (result.error or "")


def test_final_item_without_output_index_accepted(server):
    # Pinned dialect: final items do NOT carry output_index (the coordinate
    # is an event-envelope field). Array order is authoritative.
    item = {"type": "message", "id": "m0", "status": "completed",
            "role": "assistant",
            "content": [{"type": "output_text", "text": "plain",
                         "annotations": [], "logprobs": None}],
            "phase": None}
    srv = server(lambda h, r: h._send_json(
        200, completed_json([item], usage={"input_tokens": 1, "output_tokens": 1})))
    result = make_generator(make_config(f"{srv.url}/v1")).generate(make_request())
    assert result.outcome is CompletionOutcome.TERMINAL
    assert result.text == "plain"


def test_reasoning_completed_is_supported_non_text(server):
    srv = server(lambda h, r: h._send_json(
        200, completed_json([reasoning_item("rs0"), message_item("m0", "t1")],
                            usage={"input_tokens": 3, "output_tokens": 7})))
    result = make_generator(make_config(f"{srv.url}/v1")).generate(make_request())
    assert result.outcome is CompletionOutcome.TERMINAL
    assert result.text == "t1"


@pytest.mark.parametrize("bad_status", ["in_progress", "incomplete", "failed", None])
def test_reasoning_non_completed_mixed_refused(server, bad_status):
    """Criterion 6 contradictory-state protection applies to supported
    non-text items too: a preceding reasoning item that is not completed
    must fail the whole response, never be silently skipped and salvaged."""
    item = reasoning_item("rs0")
    if bad_status is None:
        item.pop("status")
    else:
        item["status"] = bad_status

    def scenario(h, r):
        h._send_json(200, completed_json([item, message_item("m0", "t1")]))

    srv = server(scenario)
    result = make_generator(make_config(f"{srv.url}/v1")).generate(make_request())
    assert result.outcome is CompletionOutcome.FAILED, bad_status
    assert result.outcome is not CompletionOutcome.TERMINAL
    assert "contradictory terminal reasoning item status" in (result.error or ""), bad_status


@pytest.mark.parametrize("call_status", ["completed", "in_progress"])
def test_function_call_unsupported_action_not_salvaged(server, call_status):
    """This bounded adapter never declares tools, so a model function_call
    is an unsupported action: refuse the whole response, including when a
    valid text message is present (no silent salvage)."""

    def scenario(h, r):
        h._send_json(200, completed_json(
            [function_call_item("fc0", status=call_status), message_item("m0", "t1")]))

    srv = server(scenario)
    result = make_generator(make_config(f"{srv.url}/v1")).generate(make_request())
    assert result.outcome is CompletionOutcome.FAILED, call_status
    assert result.outcome is not CompletionOutcome.TERMINAL
    assert "unsupported function_call output item" in (result.error or ""), call_status


def test_function_call_only_is_explicitly_unsupported(server):
    srv = server(lambda h, r: h._send_json(
        200, completed_json([function_call_item("fc0")])))
    result = make_generator(make_config(f"{srv.url}/v1")).generate(make_request())
    assert result.outcome is CompletionOutcome.FAILED
    assert "unsupported function_call output item" in (result.error or "")


def test_stream_in_progress_reasoning_mixed_refused(server):
    """Same protection at the stream boundary: observed in-progress
    reasoning item + final completed response -> FAILED, not TERMINAL."""
    text = "Hello world"
    reasoning_done = reasoning_item("rs0", status="in_progress")
    frames = [
        sse_data_only({"type": "response.created",
                       "response": {"id": "r1", "status": "in_progress"}}),
        sse_data_only({"type": "response.output_item.added", "output_index": 0,
                       "item": reasoning_item("rs0", status="in_progress")}),
        sse_data_only({"type": "response.output_item.done", "output_index": 0,
                       "item": reasoning_done}),
        sse_data_only({"type": "response.output_item.added", "output_index": 1,
                       "item": {"type": "message", "id": "m1",
                                "status": "in_progress", "role": "assistant",
                                "content": [], "phase": None}}),
        sse_data_only({"type": "response.output_text.delta", "item_id": "m1",
                       "output_index": 1, "delta": text}),
        sse_data_only({"type": "response.output_text.done", "item_id": "m1",
                       "output_index": 1, "text": text}),
        sse_data_only({"type": "response.output_item.done", "output_index": 1,
                       "item": message_item("m1", text)}),
        sse_data_only({"type": "response.completed",
                       "response": {"id": "r1", "object": "response",
                                    "created_at": 1, "status": "completed",
                                    "model": "synthetic-qwen",
                                    "output": [reasoning_done, message_item("m1", text)],
                                    "usage": {"input_tokens": 2, "output_tokens": 3}}}),
    ]
    srv = server(stream_scenario(frames))
    caps = RouteCapabilities(streaming=True)
    result = make_generator(make_config(f"{srv.url}/v1", caps)).generate(
        make_request(stream=True))
    assert result.outcome is CompletionOutcome.FAILED
    assert "contradictory terminal reasoning item status" in (result.error or "")


def test_completed_without_usable_text_is_failure(server):
    cases = [
        ([], "non-empty"),
        ([message_item("m0", "")], "usable"),
    ]
    for output, needle in cases:
        srv = server(lambda h, r, out=output: h._send_json(200, completed_json(out)))
        result = make_generator(make_config(f"{srv.url}/v1")).generate(make_request())
        assert result.outcome is CompletionOutcome.FAILED, output
        assert result.outcome is not CompletionOutcome.TERMINAL
        assert result.error and needle in result.error, output


def test_stream_delta_cumulative_mismatch_refused(server):
    frames = valid_stream_frames(text="Hello world")
    # The done event carries a different cumulative text than the deltas.
    frames[4] = sse_data_only({"type": "response.output_text.done",
                               "item_id": "msg_1", "output_index": 0,
                               "text": "MISMATCH"})
    srv = server(stream_scenario(frames))
    caps = RouteCapabilities(streaming=True)
    result = make_generator(make_config(f"{srv.url}/v1", caps)).generate(
        make_request(stream=True))
    assert result.outcome is CompletionOutcome.FAILED
    assert "mismatch" in (result.error or "")


def test_stream_delta_for_unknown_item_refused(server):
    frames = [
        sse_data_only({"type": "response.created", "response": {"id": "r1"}}),
        sse_data_only({"type": "response.output_text.delta",
                       "item_id": "stranger", "output_index": 0, "delta": "hi"}),
    ]
    srv = server(stream_scenario(frames))
    caps = RouteCapabilities(streaming=True)
    result = make_generator(make_config(f"{srv.url}/v1", caps)).generate(
        make_request(stream=True))
    assert result.outcome is CompletionOutcome.FAILED
    assert "unknown output item" in (result.error or "")


def test_stream_duplicate_terminal_refused(server):
    frames = valid_stream_frames()
    frames.append(frames[6])  # a second response.completed
    srv = server(stream_scenario(frames))
    caps = RouteCapabilities(streaming=True)
    result = make_generator(make_config(f"{srv.url}/v1", caps)).generate(
        make_request(stream=True))
    assert result.outcome is CompletionOutcome.FAILED
    assert "duplicate terminal" in (result.error or "")


def test_stream_eof_without_terminal_is_incomplete_not_success(server):
    frames = valid_stream_frames()[:5]  # created, added, deltas, done — no terminal
    srv = server(stream_scenario(frames))
    caps = RouteCapabilities(streaming=True)
    result = make_generator(make_config(f"{srv.url}/v1", caps)).generate(
        make_request(stream=True))
    assert result.outcome is CompletionOutcome.INCOMPLETE
    assert result.text == "Hello world"  # partial text preserved, but not a success
    assert result.error


def test_stream_eof_without_events_is_unknown_completion(server):
    srv = server(lambda h, r: h._send_headers_only())  # 200 then immediate clean EOF
    caps = RouteCapabilities(streaming=True)
    result = make_generator(make_config(f"{srv.url}/v1", caps)).generate(
        make_request(stream=True))
    assert result.outcome is CompletionOutcome.UNKNOWN_COMPLETION
    assert "without events" in (result.error or "")


def test_stream_completed_output_mismatch_refused(server):
    frames = valid_stream_frames()
    # The completed event claims a different output item than the stream observed.
    completed = json.loads(frames[6].split(b"data: ", 1)[1].rstrip(b"\n"))
    completed["response"]["output"] = [message_item("other", "Hello world")]
    frames[6] = sse_data_only(completed)
    srv = server(stream_scenario(frames))
    caps = RouteCapabilities(streaming=True)
    result = make_generator(make_config(f"{srv.url}/v1", caps)).generate(
        make_request(stream=True))
    assert result.outcome is CompletionOutcome.FAILED
    assert "does not match observed item order" in (result.error or "")


# ---------------------------------------------------------------------------
# 003-c: protocol validation — types, IDs, coordinates, statuses, parts
# ---------------------------------------------------------------------------

def _streaming_result(srv, frames):
    """Send frames through the real GatewayGenerator on an owned loopback."""
    caps = RouteCapabilities(streaming=True)
    return make_generator(make_config(f"{srv.url}/v1", caps)).generate(
        make_request(stream=True))


def multipart_stream_frames(part_texts, response_id="resp_mp"):
    """Valid pinned-dialect stream: one message item with N bounded
    output_text parts, each with complete part-added/delta/text-done/
    part-done events and consistent item/final data (the actual gateway
    shape observed at the pinned revision)."""
    parts = [
        {"type": "output_text", "text": text, "annotations": [],
         "logprobs": None}
        for text in part_texts
    ]
    completed_response = {
        "id": response_id,
        "object": "response",
        "created_at": 123,
        "status": "completed",
        "model": "synthetic-qwen",
        "output": [{
            "id": "msg_1", "type": "message", "status": "completed",
            "role": "assistant", "content": parts, "phase": None,
        }],
        "usage": {"input_tokens": 10, "output_tokens": 2 * len(part_texts)},
    }
    frames = [
        sse_data_only({"type": "response.created",
                       "response": {"id": response_id, "status": "in_progress"}}),
        sse_data_only({"type": "response.output_item.added", "output_index": 0,
                       "item": {"type": "message", "id": "msg_1",
                                "status": "in_progress", "role": "assistant",
                                "content": [], "phase": None}}),
    ]
    for content_index, text in enumerate(part_texts):
        common = {"item_id": "msg_1", "output_index": 0,
                  "content_index": content_index}
        frames.append(sse_data_only({"type": "response.content_part.added",
                                     **common,
                                     "part": {"type": "output_text",
                                              "text": "", "annotations": [],
                                              "logprobs": []}}))
        frames.append(sse_data_only({"type": "response.output_text.delta",
                                     **common, "delta": text, "logprobs": []}))
        frames.append(sse_data_only({"type": "response.output_text.done",
                                     **common, "text": text, "logprobs": []}))
        frames.append(sse_data_only({"type": "response.content_part.done",
                                     **common,
                                     "part": {"type": "output_text",
                                              "text": text, "annotations": [],
                                              "logprobs": None}}))
    frames.append(sse_data_only({"type": "response.output_item.done",
                                 "output_index": 0,
                                 "item": completed_response["output"][0]}))
    frames.append(sse_data_only({"type": "response.completed",
                                 "response": completed_response}))
    return frames


def two_message_stream_frames():
    """Two message items in order, each fully delta-streamed."""
    completed_response = {
        "id": "r1", "object": "response", "created_at": 1,
        "status": "completed", "model": "synthetic-qwen",
        "output": [message_item("m0", "alpha"), message_item("m1", "beta")],
        "usage": {"input_tokens": 4, "output_tokens": 2},
    }
    frames = [sse_data_only({"type": "response.created",
                             "response": {"id": "r1", "status": "in_progress"}})]
    for index, (item_id, text) in enumerate([("m0", "alpha"), ("m1", "beta")]):
        frames.append(sse_data_only({
            "type": "response.output_item.added", "output_index": index,
            "item": {"type": "message", "id": item_id, "status": "in_progress",
                     "role": "assistant", "content": [], "phase": None}}))
        frames.append(sse_data_only({"type": "response.output_text.delta",
                                     "item_id": item_id, "output_index": index,
                                     "delta": text}))
        frames.append(sse_data_only({"type": "response.output_text.done",
                                     "item_id": item_id, "output_index": index,
                                     "text": text}))
        frames.append(sse_data_only({"type": "response.output_item.done",
                                     "output_index": index,
                                     "item": message_item(item_id, text)}))
    frames.append(sse_data_only({"type": "response.completed",
                                 "response": completed_response}))
    return frames


def test_stream_array_delta_refused_not_salvaged(server):
    """003-b reproduction: an array delta followed by an empty done text
    and empty item data must fail safely; the authoritative terminal text
    must never be salvaged into a successful answer."""
    frames = valid_stream_frames(text="answer", response_id="r1")
    frames[2] = sse_data_only({"type": "response.output_text.delta",
                               "item_id": "msg_1", "output_index": 0,
                               "delta": []})
    frames[3] = sse_data_only({"type": "response.output_text.done",
                               "item_id": "msg_1", "output_index": 0,
                               "text": ""})
    frames[4] = sse_data_only({"type": "response.output_item.done",
                               "output_index": 0,
                               "item": {"type": "message", "id": "msg_1",
                                        "status": "completed",
                                        "role": "assistant",
                                        "content": [], "phase": None}})
    srv = server(stream_scenario(frames))
    result = _streaming_result(srv, frames)
    assert result.outcome is CompletionOutcome.FAILED
    assert "malformed delta type" in (result.error or "")
    assert result.text is None  # no salvaged answer
    assert srv.paths == ["/v1/responses"]


@pytest.mark.parametrize("delta", [[], 7, True, None, {}])
def test_stream_non_string_delta_refused(server, delta):
    frames = valid_stream_frames()
    frames[2] = sse_data_only({"type": "response.output_text.delta",
                               "item_id": "msg_1", "output_index": 0,
                               "delta": delta})
    srv = server(stream_scenario(frames))
    result = _streaming_result(srv, frames)
    assert result.outcome is CompletionOutcome.FAILED, delta
    assert "malformed delta type" in (result.error or ""), delta
    assert result.text is None


@pytest.mark.parametrize("text", [7, [], None, {}])
def test_stream_non_string_done_text_refused(server, text):
    frames = valid_stream_frames()
    frames[4] = sse_data_only({"type": "response.output_text.done",
                               "item_id": "msg_1", "output_index": 0,
                               "text": text})
    srv = server(stream_scenario(frames))
    result = _streaming_result(srv, frames)
    assert result.outcome is CompletionOutcome.FAILED, text
    assert "malformed output_text.done" in (result.error or ""), text
    assert result.text is None


def test_stream_missing_terminal_response_id_refused(server):
    """A completed event without a valid nonempty response ID fails; the
    ID cannot be ignored."""
    frames = valid_stream_frames()
    completed = json.loads(frames[6].split(b"data: ", 1)[1].rstrip(b"\n"))
    del completed["response"]["id"]
    frames[6] = sse_data_only(completed)
    srv = server(stream_scenario(frames))
    result = _streaming_result(srv, frames)
    assert result.outcome is CompletionOutcome.FAILED
    assert "malformed terminal response ID" in (result.error or "")
    assert result.text is None


@pytest.mark.parametrize("bad_id", [{}, [], 7])
def test_stream_malformed_terminal_response_id_refused(server, bad_id):
    frames = valid_stream_frames()
    completed = json.loads(frames[6].split(b"data: ", 1)[1].rstrip(b"\n"))
    completed["response"]["id"] = bad_id
    frames[6] = sse_data_only(completed)
    srv = server(stream_scenario(frames))
    result = _streaming_result(srv, frames)
    assert result.outcome is CompletionOutcome.FAILED, bad_id
    assert "malformed terminal response ID" in (result.error or ""), bad_id
    assert result.text is None


def test_stream_conflicting_terminal_response_id_refused(server):
    frames = valid_stream_frames(response_id="r1")
    completed = json.loads(frames[6].split(b"data: ", 1)[1].rstrip(b"\n"))
    completed["response"]["id"] = "other"
    frames[6] = sse_data_only(completed)
    srv = server(stream_scenario(frames))
    result = _streaming_result(srv, frames)
    assert result.outcome is CompletionOutcome.FAILED
    assert "conflicting response IDs" in (result.error or "")


def test_stream_wrong_delta_output_index_refused(server):
    """A wrong delta.output_index is refused even when item_id names a
    known item."""
    frames = valid_stream_frames()
    frames[2] = sse_data_only({"type": "response.output_text.delta",
                               "item_id": "msg_1", "output_index": 9,
                               "delta": "Hello"})
    srv = server(stream_scenario(frames))
    result = _streaming_result(srv, frames)
    assert result.outcome is CompletionOutcome.FAILED
    assert "output_index mismatch" in (result.error or "")
    assert result.text is None


def test_stream_delta_other_item_output_index_refused(server):
    frames = two_message_stream_frames()
    # The delta for item m0 (observed position 0) claims position 1.
    frames[3] = sse_data_only({"type": "response.output_text.delta",
                               "item_id": "m0", "output_index": 1,
                               "delta": "alpha"})
    srv = server(stream_scenario(frames))
    result = _streaming_result(srv, frames)
    assert result.outcome is CompletionOutcome.FAILED
    assert "output_index mismatch" in (result.error or "")


@pytest.mark.parametrize("status", ["in_progress", "incomplete", "failed",
                                    {}, [], None])
def test_stream_nonterminal_item_done_status_refused(server, status):
    """A nonterminal item.done status followed by a completed final message
    is contradictory, never success."""
    frames = valid_stream_frames()
    item_done = json.loads(frames[5].split(b"data: ", 1)[1].rstrip(b"\n"))
    item_done["item"]["status"] = status
    frames[5] = sse_data_only(item_done)
    srv = server(stream_scenario(frames))
    result = _streaming_result(srv, frames)
    assert result.outcome is CompletionOutcome.FAILED, status
    assert "nonterminal item done status" in (result.error or ""), status
    assert result.text is None


def test_stream_nonterminal_item_done_status_canary_not_leaked(server):
    frames = valid_stream_frames()
    item_done = json.loads(frames[5].split(b"data: ", 1)[1].rstrip(b"\n"))
    item_done["item"]["status"] = "canary_status_003c"
    frames[5] = sse_data_only(item_done)
    srv = server(stream_scenario(frames))
    result = _streaming_result(srv, frames)
    assert result.outcome is CompletionOutcome.FAILED
    assert "nonterminal item done status" in (result.error or "")
    assert "canary" not in (result.error or "")


@pytest.mark.parametrize("status", [{}, []])
def test_stream_malformed_final_status_object_refused(server, status):
    """message.status {} or [] must be guarded before set membership: a
    safe typed failure, never a raw TypeError."""
    frames = valid_stream_frames()
    completed = json.loads(frames[6].split(b"data: ", 1)[1].rstrip(b"\n"))
    completed["response"]["output"][0]["status"] = status
    frames[6] = sse_data_only(completed)
    srv = server(stream_scenario(frames))
    result = _streaming_result(srv, frames)
    assert result.outcome is CompletionOutcome.FAILED, status
    assert "contradictory terminal message item status" in (result.error or ""), status
    assert result.text is None


@pytest.mark.parametrize("status", [{}, []])
def test_non_stream_malformed_final_status_refused(server, status):
    item = message_item("m0", "a")
    item["status"] = status
    srv = server(lambda h, r: h._send_json(200, completed_json([item])))
    result = make_generator(make_config(f"{srv.url}/v1")).generate(make_request())
    assert result.outcome is CompletionOutcome.FAILED, status
    assert "contradictory terminal message item status" in (result.error or ""), status


def _nesting_probe(max_depth: int) -> tuple[int | None, int]:
    """Probe the C scanner's nesting capacity of the running interpreter.

    The depth at which ``json.loads`` raises ``RecursionError`` depends on
    the interpreter build and its C stack size (fixed at interpreter
    startup, not on the Python recursion limit), so the trigger depth
    cannot be hardcoded. Returns ``(trigger_depth, deepest_safe_depth)``:
    the smallest probed depth that raises ``RecursionError`` (None if the
    capacity exceeds the bound) and the deepest probed depth that parsed
    cleanly (a wire payload at that depth is guaranteed to parse in this
    interpreter)."""
    depth = 256
    last_safe = 256
    while depth <= max_depth:
        payload = b'{"j": ' + b"[" * depth + b"]" * depth + b"}"
        try:
            json.loads(payload)
        except RecursionError:
            return depth, last_safe
        last_safe = depth
        depth *= 2
    return None, last_safe


def test_non_stream_excessive_json_nesting_refused(server):
    """JSON nesting beyond the interpreter's C-scanner capacity inside the
    byte bounds is a safe JSON failure, never a raw RecursionError. The
    trigger depth is probed per interpreter; when the capacity exceeds
    the byte-bound parseable depth, the deepest proven-parseable nesting
    must still yield a safe typed result (no raw exception)."""
    max_depth = 900_000  # 2*900_000 + 7 bytes < 2,000,000 body bound
    trigger, safe_depth = _nesting_probe(max_depth)
    depth = trigger or safe_depth
    body = b'{"j": ' + b"[" * depth + b"]" * depth + b"}"

    def scenario(h, r):
        h._send_raw(200, body, "application/json")

    srv = server(scenario)
    result = make_generator(make_config(f"{srv.url}/v1")).generate(make_request())
    assert result.outcome is CompletionOutcome.FAILED
    if trigger is not None:
        assert "not valid JSON" in (result.error or "")
    else:
        # Parsed cleanly: a document without a recognized terminal status.
        assert "unexpected provider terminal status" in (result.error or "")


def test_stream_excessive_json_nesting_refused(server):
    """Same bound at the SSE frame boundary: a deeply nested event JSON
    that exceeds the C scanner's capacity is a malformed event payload
    (safe typed failure, never a raw RecursionError); when the
    interpreter's capacity exceeds the 262,144-byte event bound, the
    deepest proven-parseable nesting stays an inert non-terminal event
    and the clean EOF maps to INCOMPLETE — in both cases a safe typed
    result, no raw exception. The trigger depth is probed per
    interpreter (capacity is build/C-stack dependent)."""
    max_depth = 120_000  # 2*120_000 + 13 bytes < 262,144 event bound
    trigger, safe_depth = _nesting_probe(max_depth)
    depth = trigger or safe_depth
    deep = b'{"j": ' + b"[" * depth + b"]" * depth + b"}"
    frames = [
        sse_data_only({"type": "response.created",
                       "response": {"id": "r1", "status": "in_progress"}}),
        b"data: " + deep + b"\n\n",
    ]
    srv = server(stream_scenario(frames))
    result = _streaming_result(srv, frames)
    if trigger is not None:
        assert result.outcome is CompletionOutcome.FAILED
        assert "malformed event payload" in (result.error or "")
    else:
        assert result.outcome is CompletionOutcome.INCOMPLETE
        assert result.error


def test_stream_valid_multiple_content_parts_succeeds(server):
    """A message with two output_text parts and complete part lifecycle
    events is a valid supported stream: exact part-concatenated text,
    one request, no refusal of multipart streams."""
    frames = multipart_stream_frames(["first", "second"])
    srv = server(stream_scenario(frames))
    result = _streaming_result(srv, frames)
    assert result.outcome is CompletionOutcome.TERMINAL
    assert result.text == "firstsecond"
    assert srv.paths == ["/v1/responses"]
    assert srv.count("/v1/responses") == 1


def test_stream_multiple_messages_in_order_succeeds(server):
    frames = two_message_stream_frames()
    srv = server(stream_scenario(frames))
    result = _streaming_result(srv, frames)
    assert result.outcome is CompletionOutcome.TERMINAL
    assert result.text == "alpha\nbeta"
    assert srv.paths == ["/v1/responses"]


def test_stream_delta_after_text_done_refused(server):
    """A delta after the part's text done is a lifecycle violation."""
    frames = multipart_stream_frames(["first", "second"])
    frames.insert(5, sse_data_only({"type": "response.output_text.delta",
                                    "item_id": "msg_1", "output_index": 0,
                                    "content_index": 0, "delta": "extra"}))
    srv = server(stream_scenario(frames))
    result = _streaming_result(srv, frames)
    assert result.outcome is CompletionOutcome.FAILED
    assert "delta after content part done" in (result.error or "")


def test_stream_duplicate_text_done_refused(server):
    frames = multipart_stream_frames(["first", "second"])
    frames.insert(5, frames[4])
    srv = server(stream_scenario(frames))
    result = _streaming_result(srv, frames)
    assert result.outcome is CompletionOutcome.FAILED
    assert "duplicate output_text.done" in (result.error or "")


def test_stream_unknown_content_part_refused(server):
    """An explicit content_index naming a never-added part cannot be
    silently accepted or merged."""
    frames = valid_stream_frames()
    frames.insert(3, sse_data_only({"type": "response.output_text.delta",
                                    "item_id": "msg_1", "output_index": 0,
                                    "content_index": 5, "delta": "x"}))
    srv = server(stream_scenario(frames))
    result = _streaming_result(srv, frames)
    assert result.outcome is CompletionOutcome.FAILED
    assert "unknown content part" in (result.error or "")


def test_stream_part_done_before_text_done_refused(server):
    frames = [
        sse_data_only({"type": "response.created",
                       "response": {"id": "r1", "status": "in_progress"}}),
        sse_data_only({"type": "response.output_item.added", "output_index": 0,
                       "item": {"type": "message", "id": "msg_1",
                                "status": "in_progress", "role": "assistant",
                                "content": [], "phase": None}}),
        sse_data_only({"type": "response.content_part.added", "item_id": "msg_1",
                       "output_index": 0, "content_index": 0,
                       "part": {"type": "output_text", "text": "",
                                "annotations": [], "logprobs": []}}),
        sse_data_only({"type": "response.content_part.done", "item_id": "msg_1",
                       "output_index": 0, "content_index": 0,
                       "part": {"type": "output_text", "text": "",
                                "annotations": [], "logprobs": None}}),
    ]
    srv = server(stream_scenario(frames))
    result = _streaming_result(srv, frames)
    assert result.outcome is CompletionOutcome.FAILED
    assert "content part done before text done" in (result.error or "")


def test_stream_part_added_with_text_refused(server):
    frames = multipart_stream_frames(["first"])
    added = json.loads(frames[2].split(b"data: ", 1)[1].rstrip(b"\n"))
    added["part"]["text"] = "pre"
    frames[2] = sse_data_only(added)
    srv = server(stream_scenario(frames))
    result = _streaming_result(srv, frames)
    assert result.outcome is CompletionOutcome.FAILED
    assert "content part added with text" in (result.error or "")


def test_stream_part_done_text_mismatch_refused(server):
    frames = multipart_stream_frames(["first"])
    done = json.loads(frames[5].split(b"data: ", 1)[1].rstrip(b"\n"))
    done["part"]["text"] = "wrong"
    frames[5] = sse_data_only(done)
    srv = server(stream_scenario(frames))
    result = _streaming_result(srv, frames)
    assert result.outcome is CompletionOutcome.FAILED
    assert "content part text mismatch" in (result.error or "")


def test_stream_part_event_wrong_output_index_refused(server):
    frames = multipart_stream_frames(["first"])
    added = json.loads(frames[2].split(b"data: ", 1)[1].rstrip(b"\n"))
    added["output_index"] = 9
    frames[2] = sse_data_only(added)
    srv = server(stream_scenario(frames))
    result = _streaming_result(srv, frames)
    assert result.outcome is CompletionOutcome.FAILED
    assert "output_index mismatch" in (result.error or "")


def test_stream_part_event_unknown_item_refused(server):
    frames = multipart_stream_frames(["first"])
    added = json.loads(frames[2].split(b"data: ", 1)[1].rstrip(b"\n"))
    added["item_id"] = "stranger"
    frames[2] = sse_data_only(added)
    srv = server(stream_scenario(frames))
    result = _streaming_result(srv, frames)
    assert result.outcome is CompletionOutcome.FAILED
    assert "content part for unknown output item" in (result.error or "")


def test_stream_part_event_non_message_item_refused(server):
    frames = [
        sse_data_only({"type": "response.created",
                       "response": {"id": "r1", "status": "in_progress"}}),
        sse_data_only({"type": "response.output_item.added", "output_index": 0,
                       "item": reasoning_item("rs0", status="in_progress")}),
        sse_data_only({"type": "response.content_part.added", "item_id": "rs0",
                       "output_index": 0, "content_index": 0,
                       "part": {"type": "output_text", "text": "",
                                "annotations": [], "logprobs": []}}),
    ]
    srv = server(stream_scenario(frames))
    result = _streaming_result(srv, frames)
    assert result.outcome is CompletionOutcome.FAILED
    assert "content part for non-message item" in (result.error or "")


def _refusal_stream_frames(reason):
    item = {
        "id": "m0", "type": "message", "status": "refusal",
        "role": "assistant",
        "content": [{"type": "refusal", "refusal": reason}],
        "phase": None,
    }
    return [
        sse_data_only({"type": "response.created",
                       "response": {"id": "r1", "status": "in_progress"}}),
        sse_data_only({"type": "response.output_item.added", "output_index": 0,
                       "item": {"type": "message", "id": "m0",
                                "status": "in_progress", "role": "assistant",
                                "content": [], "phase": None}}),
        sse_data_only({"type": "response.output_item.done", "output_index": 0,
                       "item": item}),
        sse_data_only({"type": "response.completed",
                       "response": {"id": "r1", "object": "response",
                                    "created_at": 1, "status": "completed",
                                    "model": "synthetic-qwen",
                                    "output": [item],
                                    "usage": {"input_tokens": 1,
                                              "output_tokens": 1}}}),
    ]


def test_stream_valid_refusal_terminal(server):
    srv = server(stream_scenario(_refusal_stream_frames("content_filter")))
    result = _streaming_result(srv, _refusal_stream_frames("content_filter"))
    assert result.outcome is CompletionOutcome.REFUSAL
    assert result.error == "refusal: content_filter"
    assert result.text is None
    assert srv.paths == ["/v1/responses"]


def test_stream_refusal_canary_reason_is_fixed(server):
    frames = _refusal_stream_frames("canary_refusal_003c")
    srv = server(stream_scenario(frames))
    result = _streaming_result(srv, frames)
    assert result.outcome is CompletionOutcome.REFUSAL
    assert result.error == "refusal: refusal"
    assert "canary" not in (result.error or "")


def test_stream_incomplete_terminal_preserved(server):
    frames = [
        sse_data_only({"type": "response.created",
                       "response": {"id": "r1", "status": "in_progress"}}),
        sse_data_only({"type": "response.output_item.added", "output_index": 0,
                       "item": {"type": "message", "id": "m0",
                                "status": "in_progress", "role": "assistant",
                                "content": [], "phase": None}}),
        sse_data_only({"type": "response.output_text.delta", "item_id": "m0",
                       "output_index": 0, "delta": "partial"}),
        sse_data_only({"type": "response.incomplete",
                       "response": {"id": "r1", "object": "response",
                                    "created_at": 1, "status": "incomplete",
                                    "incomplete_details": {
                                        "reason": "max_output_tokens"}}}),
    ]
    srv = server(stream_scenario(frames))
    result = _streaming_result(srv, frames)
    assert result.outcome is CompletionOutcome.INCOMPLETE
    assert result.error == "incomplete: max_output_tokens"
    assert result.text == "partial"


def test_stream_failed_terminal_canary_not_leaked(server):
    frames = [
        sse_data_only({"type": "response.created",
                       "response": {"id": "r1", "status": "in_progress"}}),
        sse_data_only({"type": "response.failed",
                       "response": {"id": "r1", "object": "response",
                                    "created_at": 1, "status": "failed",
                                    "error": {"code": "canary_code_003c",
                                              "message": "canary_message_003c"}}}),
    ]
    srv = server(stream_scenario(frames))
    result = _streaming_result(srv, frames)
    assert result.outcome is CompletionOutcome.FAILED
    assert result.error == "provider failure"
    assert "canary" not in (result.error or "")


# ---------------------------------------------------------------------------
# deadlines mid-stream, identity stability
# ---------------------------------------------------------------------------

def test_stream_total_deadline_mid_body_unknown_with_partial_text(server):
    def scenario(h, r):
        h._send_headers_only()
        frames = valid_stream_frames()
        h._write_stream(frames[0])  # created
        h._write_stream(frames[1])  # item added
        h._write_stream(frames[2])  # first delta "Hello"
        time.sleep(1.2)  # past the 0.4s request deadline
        h._write_stream(frames[6])

    srv = server(scenario)
    caps = RouteCapabilities(streaming=True)
    config = make_config(f"{srv.url}/v1", caps, timeout_seconds=10)
    start = time.monotonic()
    result = make_generator(config).generate(make_request(stream=True, deadline=0.4))
    assert result.outcome is CompletionOutcome.UNKNOWN_COMPLETION
    assert result.text == "Hello"  # observed partial text preserved
    assert time.monotonic() - start <= 0.4 + _TOLERANCE
    assert srv.paths == ["/v1/responses"]


def test_stream_valid_slow_inside_budget_succeeds(server):
    def scenario(h, r):
        h._send_headers_only()
        for frame in valid_stream_frames():
            h._write_stream(frame)
            time.sleep(0.05)  # ~0.35s total, well inside the budget

    srv = server(scenario)
    caps = RouteCapabilities(streaming=True)
    result = make_generator(make_config(f"{srv.url}/v1", caps)).generate(
        make_request(stream=True, deadline=10.0))
    assert result.outcome is CompletionOutcome.TERMINAL
    assert result.text == "Hello world"
    assert srv.paths == ["/v1/responses"]


def test_backend_identity_stable_across_requests_and_responses(server):
    def scenario(h, r):
        # do_POST records the request before invoking the scenario, so the
        # first answer is the one where exactly one request has been seen.
        text = "first" if len(h._server_state.requests) == 1 else "second"
        h._send_json(200, completed_json([message_item("m0", text)]))

    srv = server(scenario)
    config = make_config(f"{srv.url}/v1")
    gen = make_generator(config)
    first = gen.generate(make_request(request_id="req-A", text="first question"))
    second = gen.generate(make_request(request_id="req-B", text="totally different question"))
    assert first.outcome is CompletionOutcome.TERMINAL
    assert second.outcome is CompletionOutcome.TERMINAL
    assert first.text == "first"
    assert second.text == "second"
    # Request ID/answer changes do not change the declared backend identity.
    assert first.fingerprint == second.fingerprint
    assert first.fingerprint == gateway_backend_fingerprint(config.route)
    # Endpoint identity (credential-free configured base): a different port
    # or scheme on the same host is a different declared backend.
    other_port = make_config("http://127.0.0.1:1/v1")
    assert gateway_backend_fingerprint(other_port.route) != first.fingerprint
    tls = make_config(f"https://127.0.0.1:{srv.port}/v1")
    assert gateway_backend_fingerprint(tls.route) != first.fingerprint
    # A declared model change also changes it.
    other_route = config.route.model_copy(update={"model": "other-model"})
    assert gateway_backend_fingerprint(other_route) != first.fingerprint


# ---------------------------------------------------------------------------
# 003-d: structural validation closure — supplied-null coordinates, part
# coordinate binding, item type/identity freeze, done latch, per-type
# terminal done status (actual HTTP, owned loopback)
# ---------------------------------------------------------------------------

def _mutate_frame(frames, index, **changes):
    """Return frames with the JSON payload of one data-only frame updated."""
    payload = json.loads(frames[index].split(b"data: ", 1)[1].rstrip(b"\n"))
    payload.update(changes)
    frames[index] = sse_data_only(payload)
    return frames


def _streaming_failure(server, frames, needle, *, path="/v1/responses"):
    """Shared actual-HTTP assertion for a structurally malformed stream:
    safe FAILED outcome, exact error vocabulary, no salvaged answer, one
    request on the exact wire path."""
    srv = server(stream_scenario(frames))
    result = _streaming_result(srv, frames)
    assert result.outcome is CompletionOutcome.FAILED
    assert needle in (result.error or "")
    assert result.text is None  # no salvaged answer
    assert result.attempts == 1
    assert srv.paths == [path]
    assert srv.count(path) == 1
    return result


def test_stream_null_delta_output_index_refused(server):
    """A PRESENT null output_index on a delta is malformed, distinct from
    absence: the implicit position form applies only to an absent key."""
    frames = valid_stream_frames()
    frames[2] = sse_data_only({"type": "response.output_text.delta",
                               "item_id": "msg_1", "output_index": None,
                               "delta": "Hello"})
    _streaming_failure(server, frames, "malformed event index")


def test_stream_null_delta_content_index_refused(server):
    """A present null content_index on a delta is malformed, not the
    implicit part-0 form."""
    frames = valid_stream_frames()
    frames[2] = sse_data_only({"type": "response.output_text.delta",
                               "item_id": "msg_1", "output_index": 0,
                               "content_index": None, "delta": "Hello"})
    _streaming_failure(server, frames, "malformed content part index")


def test_stream_null_text_done_content_index_refused(server):
    frames = valid_stream_frames()
    frames[4] = sse_data_only({"type": "response.output_text.done",
                               "item_id": "msg_1", "output_index": 0,
                               "content_index": None, "text": "Hello world"})
    _streaming_failure(server, frames, "malformed content part index")


def test_stream_null_content_part_index_refused(server):
    frames = multipart_stream_frames(["first", "second"])
    added = json.loads(frames[2].split(b"data: ", 1)[1].rstrip(b"\n"))
    added["content_index"] = None
    frames[2] = sse_data_only(added)
    _streaming_failure(server, frames, "malformed content part index")


def test_stream_null_item_done_output_index_refused(server):
    frames = valid_stream_frames()
    done = json.loads(frames[5].split(b"data: ", 1)[1].rstrip(b"\n"))
    done["output_index"] = None
    frames[5] = sse_data_only(done)
    _streaming_failure(server, frames, "malformed event index")


def test_stream_item_done_content_index_refused(server):
    """content_index has no meaning at the item boundary: present on
    output_item.done it is malformed (null included), never ignored."""
    frames = valid_stream_frames()
    done = json.loads(frames[5].split(b"data: ", 1)[1].rstrip(b"\n"))
    done["content_index"] = 0
    frames[5] = sse_data_only(done)
    _streaming_failure(server, frames, "malformed content part index")


def test_final_item_null_output_index_refused(server):
    """Presence and value are distinct in the final array too: a supplied
    null final output_index is malformed, absence stays the pinned form."""
    item = message_item("m0", "a", output_index=None)
    srv = server(lambda h, r: h._send_json(200, completed_json([item])))
    result = make_generator(make_config(f"{srv.url}/v1")).generate(make_request())
    assert result.outcome is CompletionOutcome.FAILED
    assert "malformed output item index" in (result.error or "")
    assert result.text is None


def test_stream_missing_optional_coordinates_succeeds(server):
    """Positive boundary: ABSENT optional coordinates keep the supported
    implicit forms (observed item position / part 0) and the stream
    succeeds with exact text."""
    frames = valid_stream_frames()
    for index in (2, 3, 4):  # both deltas and the text done
        payload = json.loads(frames[index].split(b"data: ", 1)[1].rstrip(b"\n"))
        payload.pop("output_index", None)
        payload.pop("content_index", None)
        frames[index] = sse_data_only(payload)
    srv = server(stream_scenario(frames))
    result = _streaming_result(srv, frames)
    assert result.outcome is CompletionOutcome.TERMINAL
    assert result.text == "Hello world"
    assert srv.paths == ["/v1/responses"]
    assert srv.count("/v1/responses") == 1


def test_stream_gap_content_part_coordinate_refused(server):
    """Explicit multipart coordinate gap: the second part is renamed 1 to
    7 throughout the events while the final content has only two parts.
    The bounded sequential part numbering refuses the gap instead of
    sorting it into apparent valid text."""
    frames = multipart_stream_frames(["first", "second"])
    for index, frame in enumerate(frames):
        payload = json.loads(frame.split(b"data: ", 1)[1].rstrip(b"\n"))
        if "content_index" in payload and payload["content_index"] == 1:
            payload["content_index"] = 7
            frames[index] = sse_data_only(payload)
    _streaming_failure(server, frames, "out-of-order content part")


def test_stream_out_of_order_content_part_added_refused(server):
    """Explicit parts are numbered 0,1,2,... in added order: adding part 1
    before part 0 is an out-of-order bounded-coordinate violation."""
    frames = multipart_stream_frames(["first", "second"])
    added_zero = json.loads(frames[2].split(b"data: ", 1)[1].rstrip(b"\n"))
    added_one = json.loads(frames[6].split(b"data: ", 1)[1].rstrip(b"\n"))
    frames[2] = sse_data_only(added_one)
    frames[6] = sse_data_only(added_zero)
    _streaming_failure(server, frames, "out-of-order content part")


def test_stream_disappeared_content_part_refused(server):
    """An observed part cannot disappear solely because the final
    concatenated text happens to match: the full lifecycle of two parts
    with a final content carrying one concatenated part fails."""
    frames = multipart_stream_frames(["first", "second"])
    single = {"type": "output_text", "text": "firstsecond",
              "annotations": [], "logprobs": None}
    done = json.loads(frames[-2].split(b"data: ", 1)[1].rstrip(b"\n"))
    done["item"]["content"] = [json.loads(json.dumps(single))]
    frames[-2] = sse_data_only(done)
    completed = json.loads(frames[-1].split(b"data: ", 1)[1].rstrip(b"\n"))
    completed["response"]["output"][0]["content"] = [
        json.loads(json.dumps(single))]
    frames[-1] = sse_data_only(completed)
    _streaming_failure(server, frames,
                       "content part coordinate missing from final content")


def test_stream_text_event_for_non_message_item_refused(server):
    """Text events belong to supported message parts: a reasoning item
    (added type reasoning) cannot accumulate output_text deltas."""
    frames = valid_stream_frames()
    added = json.loads(frames[1].split(b"data: ", 1)[1].rstrip(b"\n"))
    added["item"]["type"] = "reasoning"
    frames[1] = sse_data_only(added)
    _streaming_failure(server, frames, "text event for non-message item")


def test_stream_item_type_changed_at_done_refused(server):
    """Item type/identity is frozen from added through done: a reasoning
    item that appears as a message at its done boundary with the same ID
    is refused (no text events in this variant)."""
    frames = [
        sse_data_only({"type": "response.created",
                       "response": {"id": "r1", "status": "in_progress"}}),
        sse_data_only({"type": "response.output_item.added", "output_index": 0,
                       "item": reasoning_item("m1", status="in_progress")}),
        sse_data_only({"type": "response.output_item.done", "output_index": 0,
                       "item": message_item("m1", "answer")}),
        sse_data_only({"type": "response.completed",
                       "response": {"id": "r1", "object": "response",
                                    "created_at": 1, "status": "completed",
                                    "model": "synthetic-qwen",
                                    "output": [message_item("m1", "answer")],
                                    "usage": {"input_tokens": 1,
                                              "output_tokens": 1}}}),
    ]
    _streaming_failure(server, frames, "item type changed at done")


def test_stream_final_item_type_changed_refused(server):
    """The freeze extends to the final array: a reasoning item observed in
    the stream cannot become a message with the same ID in the final
    output to salvage text that never streamed."""
    frames = [
        sse_data_only({"type": "response.created",
                       "response": {"id": "r1", "status": "in_progress"}}),
        sse_data_only({"type": "response.output_item.added", "output_index": 0,
                       "item": reasoning_item("m1", status="in_progress")}),
        sse_data_only({"type": "response.output_item.done", "output_index": 0,
                       "item": reasoning_item("m1", status="completed")}),
        sse_data_only({"type": "response.completed",
                       "response": {"id": "r1", "object": "response",
                                    "created_at": 1, "status": "completed",
                                    "model": "synthetic-qwen",
                                    "output": [message_item("m1", "answer")],
                                    "usage": {"input_tokens": 1,
                                              "output_tokens": 1}}}),
    ]
    _streaming_failure(server, frames, "item type changed in final output")


def test_stream_duplicate_item_done_refused(server):
    """Item completion is latched: a duplicate output_item.done for the
    same item is refused, never re-accepted."""
    frames = valid_stream_frames()
    frames.insert(6, frames[5])
    _streaming_failure(server, frames, "duplicate output_item.done")


def test_stream_text_event_after_item_done_refused(server):
    """Contradictory state after latched completion is refused: a delta
    after the item's done event cannot extend the answer."""
    frames = valid_stream_frames()
    frames.insert(6, sse_data_only({"type": "response.output_text.delta",
                                    "item_id": "msg_1", "output_index": 0,
                                    "delta": " extra"}))
    _streaming_failure(server, frames, "text event after item done")


def test_stream_content_part_event_after_item_done_refused(server):
    frames = multipart_stream_frames(["first"])
    part_added = json.loads(frames[2].split(b"data: ", 1)[1].rstrip(b"\n"))
    # position 7: after the item done (position 6), before the terminal
    frames.insert(7, sse_data_only(part_added))
    _streaming_failure(server, frames, "content part event after item done")


def test_stream_nonterminal_reasoning_done_refused(server):
    """Terminal done status for every supported type: a reasoning item
    done with status in_progress is contradictory even when the final
    output later shows it completed (actual HTTP reproduction of the
    strategic 003-d variant)."""
    text = "answer"
    reasoning_final = reasoning_item("rs1", status="completed")
    frames = [
        sse_data_only({"type": "response.created",
                       "response": {"id": "r1", "status": "in_progress"}}),
        sse_data_only({"type": "response.output_item.added", "output_index": 0,
                       "item": reasoning_item("rs1", status="in_progress")}),
        sse_data_only({"type": "response.output_item.done", "output_index": 0,
                       "item": reasoning_item("rs1", status="in_progress")}),
        sse_data_only({"type": "response.output_item.added", "output_index": 1,
                       "item": {"type": "message", "id": "m1",
                                "status": "in_progress", "role": "assistant",
                                "content": [], "phase": None}}),
        sse_data_only({"type": "response.output_text.delta", "item_id": "m1",
                       "output_index": 1, "delta": text}),
        sse_data_only({"type": "response.output_text.done", "item_id": "m1",
                       "output_index": 1, "text": text}),
        sse_data_only({"type": "response.output_item.done", "output_index": 1,
                       "item": message_item("m1", text)}),
        sse_data_only({"type": "response.completed",
                       "response": {"id": "r1", "object": "response",
                                    "created_at": 1, "status": "completed",
                                    "model": "synthetic-qwen",
                                    "output": [reasoning_final,
                                               message_item("m1", text)],
                                    "usage": {"input_tokens": 2,
                                              "output_tokens": 3}}}),
    ]
    result = _streaming_failure(server, frames,
                                "contradictory terminal reasoning item status")
    # No internal reasoning content or canary bytes may leak into the
    # safe error text.
    assert "canary" not in (result.error or "")


def test_stream_reasoning_plus_message_valid_succeeds(server):
    """Valid counterexample: a completed reasoning item followed by a
    completed message item is a supported stream; the answer text is the
    message text only (no internal reasoning becomes answer text)."""
    text = "t1"
    frames = [
        sse_data_only({"type": "response.created",
                       "response": {"id": "r1", "status": "in_progress"}}),
        sse_data_only({"type": "response.output_item.added", "output_index": 0,
                       "item": reasoning_item("rs0", status="in_progress")}),
        sse_data_only({"type": "response.output_item.done", "output_index": 0,
                       "item": reasoning_item("rs0", status="completed")}),
        sse_data_only({"type": "response.output_item.added", "output_index": 1,
                       "item": {"type": "message", "id": "m1",
                                "status": "in_progress", "role": "assistant",
                                "content": [], "phase": None}}),
        sse_data_only({"type": "response.output_text.delta", "item_id": "m1",
                       "output_index": 1, "delta": text}),
        sse_data_only({"type": "response.output_text.done", "item_id": "m1",
                       "output_index": 1, "text": text}),
        sse_data_only({"type": "response.output_item.done", "output_index": 1,
                       "item": message_item("m1", text)}),
        sse_data_only({"type": "response.completed",
                       "response": {"id": "r1", "object": "response",
                                    "created_at": 1, "status": "completed",
                                    "model": "synthetic-qwen",
                                    "output": [reasoning_item("rs0"),
                                               message_item("m1", text)],
                                    "usage": {"input_tokens": 2,
                                              "output_tokens": 2}}}),
    ]
    srv = server(stream_scenario(frames))
    result = _streaming_result(srv, frames)
    assert result.outcome is CompletionOutcome.TERMINAL
    assert result.text == text
    assert srv.paths == ["/v1/responses"]
    assert srv.count("/v1/responses") == 1
