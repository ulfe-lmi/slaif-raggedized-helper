"""Full DirectNativeGenerator behavior tests against owned loopback HTTP (003-e).

Acceptance coverage (oap/orders/003-e criteria 1-7, all at generator level
over real loopback HTTP; the fake "server" renders templates
deterministically and answers with the pinned native dialect -- synthetic
qualifications only, no live model/build):

- the direct client materializes only under the explicit offline
  diagnostic policy (private/loopback destination + private_trusted +
  declared model + template qualification + explicit finite operator
  limits) and refuses answer purpose, visual/image input, disabled
  policy and missing operator limits BEFORE any network work (zero
  recorded requests);
- real server-side template rendering through the documented
  /apply-template semantic contract (messages -> prompt, no inference):
  trusted instructions are the system role, ordered TextItems are user
  data with boundaries preserved; literal technical content (including
  the closing-marker sequence) passes through the rendered prompt
  UNCHANGED to /completion (no substring scanning of rendered text);
  unknown template refusal (server 400) and malformed prompt responses
  are safe typed failures;
- /completion sends the bounded formatted prompt, explicit n_predict,
  stream:false and only the supported pinned-dialect controls
  (temperature/top_p, documented json_schema grammar forms gated by the
  tested json_grammar_tested capability — default deny, inferred from the
  actual input shape, cache_prompt only with the tested capability,
  singular id_slot only with the tested capability); unqualified
  json_object/json_schema requests and every other unsupported requested
  behavior refuse locally with zero inference dispatch;
- one total deadline spans template work, generation and retries and is
  never reset per attempt; an expired budget refuses before dispatch even
  after template work; positive pre-dispatch failures use the finite
  retry budget; unknown completion is non-retryable;
- native stop semantics: stop=true means stopped, not successful;
  stop_type=limit, truncated=true, stop_type=none, stop != true,
  missing/invalid terminal reason, unqualified stop-word and empty
  content never become TERMINAL; only eos with usable bounded content
  succeeds;
- metrics map only from the pinned dialect's actual reported fields with
  correct quantities: the synthetic 100-submitted (10 new / 90 cached) +
  12-generated case with tokens_cached=112 preserves the distinct facts;
  bool/NaN/infinity/malformed/unrepresentable (overflow) counters and
  times cannot prove evaluated work or crash generate(); a contradictory
  reported breakdown (100 input with 90 new + 90 cached) is withheld;
  model-phase timings (reported prefill/decode ms, a measured 0ms kept as
  a known zero, the model-scoped phase total) stay separate from caller
  wall time and from the unobserved first-token time (TTFT stays null);
- malformed/canary/error refusals leak no provider bytes; the declared
  identity is stable across requests and responses.

003-g boundary regressions (over real owned-loopback HTTP):

- safe finite phase-total arithmetic: both reported phase times 1e308
  ms are individually finite (each converting to finite 1e305 s) while
  the millisecond sum overflows before division in unsafe arithmetic —
  generate() returns a typed TERMINAL result with the finite derived
  total computed in seconds (2e305 s), the individually valid phases
  retained, TTFT still unavailable and no raw
  OverflowError/ValidationError escaping;
- explicit required JSON_MODE capability admission: a
  constructor-validated request that REQUIRES JSON_MODE (declared by
  the model) while sending no format field at all is refused locally
  with ZERO recorded requests on an untested build (a model declaration
  alone cannot prove serving-build support); the qualified positive
  control dispatches exactly once per path WITHOUT inventing an output
  format (pinned minimal envelope), and ordinary TEXT/no-format success
  on an untested build is preserved.
"""

from __future__ import annotations

import json
import math
import time as _real_time

import pytest

from conftest import SYNTHETIC_API_KEY  # noqa: F401  (suite parity; direct is keyless)

from slaif_raggedized_helper.config import (
    DirectCapabilities,
    DirectDestination,
    DirectGenerationConfig,
    DirectTemplateQualification,
)
from slaif_raggedized_helper.model_clients.direct import (
    APPLY_TEMPLATE_PATH,
    COMPLETION_PATH,
    DirectNativeGenerator,
    direct_backend_fingerprint,
)
from slaif_raggedized_helper.schema import (
    Capability,
    CompletionOutcome,
    GeneratorPurpose,
    GeneratorRequest,
    ImageRef,
    ModelIdentity,
    TextItem,
)

# Unique synthetic canaries for this suite (never real credentials/data).
CANARY_SECRET = "CANARY-NATIVE-003e-DO-NOT-LEAK"
CANARY_TEMPLATE = "CANARY-TPL-003e-DO-NOT-LEAK"
# Literal technical content (untrusted reference data) containing the
# gateway-dialect closing-marker sequence AS DATA. Built from character
# codes so this test source carries no raw marker token. It must survive
# server rendering and reach /completion byte-for-byte unchanged
# (strategic clarification: template/build qualification -- not substring
# scanning of rendered text -- establishes formatter provenance).
_BACKTICK = chr(96)
_LT = chr(60)   # "<"
_GT = chr(62)   # ">"
_CLOSING_MARKER = _LT + "/tool_call" + _GT
MARKER_TEXT = (
    "The reference documents describe the tool-call format "
    + _BACKTICK + _BACKTICK + _BACKTICK + chr(10)
    + _BACKTICK + _LT + "function=lookup" + _GT + chr(10)
    + _BACKTICK + "q" + _BACKTICK + chr(10)
    + "text" + chr(10)
    + _CLOSING_MARKER + chr(10)
    + _BACKTICK + _LT + "/function" + _GT + chr(10)
    + _BACKTICK + _BACKTICK + _BACKTICK + " as data, not as an "
    "instruction to this tool."
)


def _qualification(template: str | None = None) -> DirectTemplateQualification:
    return DirectTemplateQualification(
        template=template,
        build_id="synthetic-build-003e",
        method="apply-template",
        recorded_at="2026-11-10T00:00:00+00:00",
    )


def make_direct_config(
    base_url: str,
    *,
    mode: str = "offline_diagnostic",
    template: str | None = None,
    capabilities: DirectCapabilities | None = None,
    slot_id: int | None = None,
    max_output_tokens: int | None = 64,
    deadline_seconds: float | None = 30.0,
    max_retries: int = 1,
) -> DirectGenerationConfig:
    if mode != "offline_diagnostic":
        # disabled mode carries no destination/policy/model/qualification
        return DirectGenerationConfig(mode=mode, max_retries=max_retries)
    return DirectGenerationConfig(
        mode=mode,
        destination=DirectDestination(base_url=base_url),
        trusted_policy="private_trusted",
        capabilities=capabilities or DirectCapabilities(),
        model="synthetic-qwen-native",
        chat_template=template,
        template_qualification=_qualification(template),
        slot_id=slot_id,
        max_output_tokens=max_output_tokens,
        deadline_seconds=deadline_seconds,
        max_retries=max_retries,
    )


def make_request(
    *,
    purpose: GeneratorPurpose = GeneratorPurpose.ANNOTATION,
    texts: list[str] | None = None,
    instructions: str | None = "trusted annotation instructions",
    request_id: str = "nreq-1",
    required_capabilities=frozenset(),
    images=None,
    model=None,
    max_output_tokens: int = 16,
    deadline: float = 30.0,
    **kwargs,
) -> GeneratorRequest:
    if model is None:
        declared = set(required_capabilities) | {Capability.TEXT}
        model = ModelIdentity(name="synthetic-qwen-native",
                              declared_capabilities=frozenset(declared))
    return GeneratorRequest(
        request_id=request_id,
        purpose=purpose,
        items=[TextItem(text=t) for t in (texts or ["reference material one"])],
        images=images,
        model=model,
        required_capabilities=frozenset(required_capabilities),
        max_output_tokens=max_output_tokens,
        deadline_seconds=deadline,
        instructions=instructions,
        **kwargs,
    )


def make_generator(config: DirectGenerationConfig) -> DirectNativeGenerator:
    return DirectNativeGenerator(config)


def render_prompt(messages: list[dict]) -> str:
    """Deterministic synthetic server-side template rendering."""
    parts = []
    for message in messages:
        role = message.get("role")
        text = message.get("content")
        if not isinstance(role, str) or not isinstance(text, str):
            raise ValueError("cannot render non-string message")
        parts.append("<|" + role + "|>" + text)
    return "SYNTH-TPL::" + chr(1).join(parts)


def completion_doc(
    *,
    content: str = "annotated span [3, 11]",
    stop_type: str = "eos",
    stop: bool = True,
    truncated: bool = False,
    tokens_evaluated: int | None = 10,
    tokens_cached: int | None = None,
    tokens_predicted: int | None = None,
    timings: dict | None = None,
    error: dict | None = None,
    extra: dict | None = None,
) -> dict:
    """Pinned native non-OAI final /completion response shape."""
    doc = {
        "index": 0,
        "content": content,
        "tokens": [],
        "id_slot": 0,
        "stop": stop,
        "model": "synthetic-qwen-native",
        "tokens_predicted": 1,
        "tokens_evaluated": 10,
        "generation_settings": {"n_predict": 16},
        "prompt": "SYNTH-TPL::rendered",
        "has_new_line": False,
        "truncated": truncated,
        "stop_type": stop_type,
        "stopping_word": "",
        "tokens_cached": 11,
        "timings": {
            "cache_n": 0,
            "prompt_n": 10,
            "prompt_ms": 12.5,
            "prompt_per_token_ms": 1.25,
            "prompt_per_second": 800.0,
            "predicted_n": 1,
            "predicted_ms": 4.0,
            "predicted_per_token_ms": 4.0,
            "predicted_per_second": 250.0,
        },
    }
    if tokens_evaluated is not None:
        doc["tokens_evaluated"] = tokens_evaluated
    if tokens_cached is not None:
        doc["tokens_cached"] = tokens_cached
    if tokens_predicted is not None:
        doc["tokens_predicted"] = tokens_predicted
    if timings is not None:
        doc["timings"] = timings
    if error is not None:
        doc["error"] = error
    if extra:
        doc.update(extra)
    return doc


class NativeScenario:
    """One fake native server: /apply-template renders, /completion answers."""

    def __init__(
        self,
        *,
        render=None,
        completion: dict | str | None = None,
        completion_status: int = 200,
        completion_body: bytes | None = None,
        template_status: int = 200,
        template_body: dict | str | None = None,
    ) -> None:
        self.render = render if render is not None else render_prompt
        self.completion = completion
        self.completion_status = completion_status
        self.completion_body = completion_body
        self.template_status = template_status
        self.template_body = template_body

    def scenario(self, h, r):
        if r.path == APPLY_TEMPLATE_PATH:
            if self.template_status == 200 and self.template_body is None:
                doc = json.loads(r.body)
                prompt = self.render(doc.get("messages"))
                h._send_json(200, {"prompt": prompt})
            else:
                if self.template_body is None:
                    h._send_json(self.template_status, {"error": {"message": CANARY_TEMPLATE}})
                else:
                    h._send_json(self.template_status, self.template_body)
        elif r.path == COMPLETION_PATH:
            if self.completion_body is not None:
                h._send_raw(self.completion_status,
                            self.completion_body, "application/json")
            elif isinstance(self.completion, str):
                h._send_raw(self.completion_status,
                            self.completion.encode("utf-8"), "application/json")
            else:
                doc = self.completion
                if doc is None:
                    prompt = json.loads(r.body).get("prompt") or ""
                    doc = completion_doc(content=f"annotated span [0, {len(prompt)}]")
                h._send_json(self.completion_status, doc)
        else:
            h._send_json(404, {"error": {"message": "no such path"}})


def run_native(server, scenario: NativeScenario, request=None, config=None):
    srv = server(scenario.scenario)
    request = request if request is not None else make_request()
    config = config if config is not None else make_direct_config(srv.url)
    result = make_generator(config).generate(request)
    return srv, result


# ---------------------------------------------------------------------------
# materialization and pre-dispatch refusal (criterion 1)
# ---------------------------------------------------------------------------

def test_disabled_mode_refuses_with_zero_network(server):
    srv = server(lambda h, r: h._send_json(200, {}))
    config = make_direct_config(srv.url, mode="disabled")
    result = make_generator(config).generate(make_request())
    assert result.outcome is CompletionOutcome.FAILED
    assert "direct mode is disabled" in (result.error or "")
    assert srv.paths == []


def test_answer_purpose_refused_before_any_network(server):
    srv = server(lambda h, r: h._send_json(200, {}))
    config = make_direct_config(srv.url)
    request = make_request(purpose=GeneratorPurpose.ANSWER)
    result = make_generator(config).generate(request)
    assert result.outcome is CompletionOutcome.FAILED
    assert "annotation purpose" in (result.error or "")
    assert result.text is None
    assert srv.paths == []


def test_visual_image_requests_refused_before_dispatch(server):
    srv = server(lambda h, r: h._send_json(200, {}))
    config = make_direct_config(srv.url)
    # visual purpose (requires images) and explicit image refs, plus the
    # VISION capability alone, all refuse locally with zero dispatch.
    vision_model = ModelIdentity(name="synthetic-qwen-native",
                                 declared_capabilities=frozenset({Capability.VISION}))
    # the purpose gate is outermost: a VISUAL purpose refuses on purpose
    # (still zero network); image-bearing annotation requests and the
    # VISION capability itself refuse on the visual serializer gate.
    result = make_generator(config).generate(
        make_request(purpose=GeneratorPurpose.VISUAL,
                     images=[ImageRef(image_id="i1", source_revision="rev1")]))
    assert result.outcome is CompletionOutcome.FAILED
    assert "annotation purpose" in (result.error or "")
    for request in (
        make_request(images=[ImageRef(image_id="i1", source_revision="rev1")]),
        make_request(required_capabilities={Capability.VISION}, model=vision_model),
    ):
        result = make_generator(config).generate(request)
        assert result.outcome is CompletionOutcome.FAILED
        assert "visual/image" in (result.error or "")
    assert srv.paths == []


def test_disabled_policy_destination_never_materializes():
    # A public destination cannot even be configured: config-level refusal.
    from pydantic import ValidationError

    from slaif_raggedized_helper.config import DirectDestination

    with pytest.raises(ValidationError, match="private/loopback"):
        DirectDestination(base_url="http://8.8.8.8:8080")


def test_operator_limit_missing_refuses_before_dispatch():
    # Config-level: offline_diagnostic without explicit finite operator
    # limits is an invalid configuration (no uncapped caller allowance).
    from pydantic import ValidationError

    with pytest.raises(ValidationError, match="max_output_tokens"):
        make_direct_config("http://127.0.0.1:9", max_output_tokens=None)
    with pytest.raises(ValidationError, match="deadline_seconds"):
        make_direct_config("http://127.0.0.1:9", deadline_seconds=None)


@pytest.mark.parametrize(
    "control",
    [
        {"required_capabilities": {Capability.PROMPT_CACHING}},
        {"prompt_cache_key": "k1",
         "required_capabilities": {Capability.PROMPT_CACHING}},
        {"required_capabilities": {Capability.STREAMING}},
        {"response_format": "json_object"},
        {"response_format": "json_schema", "json_schema": {"type": "object"}},
        # 003-g: the EXPLICIT minimum requirement, with no format field
        # at all (the model declares the capability; the constructor
        # validates the request).
        {"required_capabilities": {Capability.JSON_MODE}},
    ],
    ids=["prompt-caching-untested", "cache-key-untested", "streaming",
         "json-object-unqualified", "json-schema-unqualified",
         "json-capability-untested"],
)
def test_unsupported_controls_refused_before_any_dispatch(server, control):
    srv = server(lambda h, r: h._send_json(200, {}))
    config = make_direct_config(srv.url, capabilities=DirectCapabilities())
    declared = control.get("required_capabilities") or frozenset()
    model = ModelIdentity(name="synthetic-qwen-native",
                          declared_capabilities=frozenset(declared))
    request = make_request(model=model, **control)
    result = make_generator(config).generate(request)
    assert result.outcome is CompletionOutcome.FAILED
    assert "refused" in (result.error or "")
    assert srv.paths == []


@pytest.mark.parametrize(
    "shape, expected_grammar",
    [
        ({"response_format": "json_object"}, {}),
        ({"response_format": "json_schema", "json_schema": {"type": "object"}},
         {"type": "object"}),
    ],
    ids=["json-object-qualified", "json-schema-qualified"],
)
def test_qualified_json_controls_preserve_request_semantics(server,
                                                            shape,
                                                            expected_grammar):
    """Qualified build (json_grammar_tested): the pinned request semantics
    are preserved — json_object maps to the reference's any-JSON grammar
    form {} (NOT a stronger object-shape guarantee) and json_schema sends
    the caller's exact schema; both calls happen exactly once."""
    scenario = NativeScenario()
    srv = server(scenario.scenario)
    config = make_direct_config(
        srv.url, capabilities=DirectCapabilities(json_grammar_tested=True))
    result = make_generator(config).generate(make_request(**shape))
    assert result.outcome is CompletionOutcome.TERMINAL
    assert srv.paths == [APPLY_TEMPLATE_PATH, COMPLETION_PATH]
    assert srv.count(APPLY_TEMPLATE_PATH) == 1
    envelope = json.loads(srv.requests[1].body)
    assert envelope["json_schema"] == expected_grammar
    assert set(envelope) == {"prompt", "n_predict", "stream", "json_schema"}


def test_required_json_mode_capability_refused_before_any_dispatch(server):
    """003-g actual-HTTP regression: a constructor-validated request that
    EXPLICITLY REQUIRES JSON_MODE (the model declares TEXT + JSON_MODE)
    while sending NO format field at all (response_format None, no
    json_schema) must be refused locally — the explicit minimum
    capability is honored independently of the actual input shape, and a
    model capability declaration alone cannot prove serving-build
    support: typed FAILED with the fixed safe reason and exactly ZERO
    recorded requests (no /apply-template, no /completion)."""
    srv = server(lambda h, r: h._send_json(200, {}))
    config = make_direct_config(srv.url)  # default DirectCapabilities: untested
    request = make_request(required_capabilities={Capability.JSON_MODE})
    assert request.response_format is None
    assert request.json_schema is None
    result = make_generator(config).generate(request)
    assert result.outcome is CompletionOutcome.FAILED
    assert "json_schema grammar support is not tested" in (result.error or "")
    assert result.text is None
    assert srv.paths == []  # exactly zero refused dispatch


def test_required_json_mode_capability_qualified_without_invented_format(server):
    """003-g qualified positive control: the SAME explicit requirement on
    a qualified build (json_grammar_tested=True) dispatches exactly once
    per path and does NOT invent an output format: with no format
    selected the pinned minimal envelope is sent unchanged (no
    json_schema key)."""
    scenario = NativeScenario()
    srv = server(scenario.scenario)
    config = make_direct_config(
        srv.url, capabilities=DirectCapabilities(json_grammar_tested=True))
    result = make_generator(config).generate(
        make_request(required_capabilities={Capability.JSON_MODE}))
    assert result.outcome is CompletionOutcome.TERMINAL
    assert srv.paths == [APPLY_TEMPLATE_PATH, COMPLETION_PATH]
    assert srv.count(APPLY_TEMPLATE_PATH) == 1
    assert srv.count(COMPLETION_PATH) == 1
    envelope = json.loads(srv.requests[1].body)
    assert "json_schema" not in envelope
    assert set(envelope) == {"prompt", "n_predict", "stream"}


def test_ordinary_text_without_format_preserved_on_untested_build(server):
    """003-g ordinary TEXT positive control: no format, no required
    capabilities, untested build — the capability gate must not broaden
    the refusal; the ordinary request still succeeds with both dispatches."""
    srv, result = run_native(server, NativeScenario())
    assert result.outcome is CompletionOutcome.TERMINAL
    assert srv.paths == [APPLY_TEMPLATE_PATH, COMPLETION_PATH]


def test_output_budget_refused_before_dispatch(server):
    srv = server(lambda h, r: h._send_json(200, {}))
    config = make_direct_config(srv.url, max_output_tokens=32)
    request = make_request(max_output_tokens=33)
    result = make_generator(config).generate(request)
    assert result.outcome is CompletionOutcome.FAILED
    assert "output budget refused" in (result.error or "")
    assert srv.paths == []


def test_output_budget_equal_to_operator_limit_is_accepted(server):
    scenario = NativeScenario()
    srv = server(scenario.scenario)
    config = make_direct_config(srv.url, max_output_tokens=64)
    result = make_generator(config).generate(make_request(max_output_tokens=64))
    assert result.outcome is CompletionOutcome.TERMINAL
    completion = srv.requests[1]
    assert json.loads(completion.body)["n_predict"] == 64


# ---------------------------------------------------------------------------
# real server-side template rendering (criterion 2)
# ---------------------------------------------------------------------------

def test_apply_template_wire_is_exact_messages_contract(server):
    srv, result = run_native(server, NativeScenario())
    assert result.outcome is CompletionOutcome.TERMINAL
    assert srv.paths == [APPLY_TEMPLATE_PATH, COMPLETION_PATH]
    apply_body = json.loads(srv.requests[0].body)
    assert apply_body == {
        "messages": [
            {"role": "system", "content": "trusted annotation instructions"},
            {"role": "user", "content": "reference material one"},
        ]
    }
    # /apply-template performs no inference: exactly one request per path.
    assert srv.count(APPLY_TEMPLATE_PATH) == 1
    assert srv.count(COMPLETION_PATH) == 1


def test_ordered_items_keep_boundaries_and_roles(server):
    texts = ["first reference", "second reference", "third reference"]
    srv, result = run_native(
        server, NativeScenario(), request=make_request(texts=texts, instructions=None))
    assert result.outcome is CompletionOutcome.TERMINAL
    apply_body = json.loads(srv.requests[0].body)
    roles = [m["role"] for m in apply_body["messages"]]
    contents = [m["content"] for m in apply_body["messages"]]
    assert roles == ["user", "user", "user"]
    assert contents == texts
    # the rendered prompt carries the ordered boundaries exactly
    prompt = json.loads(srv.requests[1].body)["prompt"]
    assert prompt == "SYNTH-TPL::" + chr(1).join("<|user|>" + t for t in texts)


def test_literal_marker_content_reaches_completion_unchanged(server):
    """Positive owned-HTTP literal-marker case (strategic clarification):
    untrusted reference data containing the closing-marker sequence as
    data is rendered by the server and forwarded to /completion
    byte-for-byte unchanged -- no blanket rejection, no stripping."""
    assert _CLOSING_MARKER in MARKER_TEXT
    srv, result = run_native(
        server, NativeScenario(), request=make_request(texts=[MARKER_TEXT]))
    assert result.outcome is CompletionOutcome.TERMINAL
    prompt = json.loads(srv.requests[1].body)["prompt"]
    assert MARKER_TEXT in prompt
    # exact rendered bytes: the literal sequence appears exactly once,
    # inside the user-data segment, unmodified
    assert prompt.count(_CLOSING_MARKER) == 1
    # the exact qualified prompt (literal tool-call close AND the Markdown
    # fence data) reaches /completion byte-for-byte unchanged
    expected_prompt = "SYNTH-TPL::" + chr(1).join([
        "<|system|>trusted annotation instructions",
        "<|user|>" + MARKER_TEXT,
    ])
    assert prompt == expected_prompt
    assert result.text == f"annotated span [0, {len(prompt)}]"


def test_template_refusal_is_safe_and_stops_before_completion(server):
    srv = server(NativeScenario(
        template_status=400,
        template_body={"error": {"code": 400, "type": "invalid_request_error",
                                 "message": CANARY_TEMPLATE}}).scenario)
    result = make_generator(make_direct_config(srv.url)).generate(make_request())
    assert result.outcome is CompletionOutcome.FAILED
    assert "template application refused (HTTP 400)" in (result.error or "")
    assert CANARY_TEMPLATE not in (result.error or "")
    assert srv.paths == [APPLY_TEMPLATE_PATH]


@pytest.mark.parametrize("bad_prompt", [None, "", 7, True, ["p"], {}])
def test_apply_template_malformed_prompt_refused(server, bad_prompt):
    srv = server(NativeScenario(template_body={"prompt": bad_prompt}).scenario)
    result = make_generator(make_direct_config(srv.url)).generate(make_request())
    assert result.outcome is CompletionOutcome.FAILED
    assert "no usable prompt" in (result.error or "")
    assert srv.count(COMPLETION_PATH) == 0


def test_apply_template_missing_prompt_refused(server):
    srv = server(NativeScenario(template_body={"notprompt": "x"}).scenario)
    result = make_generator(make_direct_config(srv.url)).generate(make_request())
    assert result.outcome is CompletionOutcome.FAILED
    assert "no usable prompt" in (result.error or "")
    assert srv.count(COMPLETION_PATH) == 0


def test_apply_template_error_object_refused(server):
    srv = server(NativeScenario(template_body={"error": {"message": CANARY_TEMPLATE}}).scenario)
    result = make_generator(make_direct_config(srv.url)).generate(make_request())
    assert result.outcome is CompletionOutcome.FAILED
    assert "template application failed at the native server" in (result.error or "")
    assert CANARY_TEMPLATE not in (result.error or "")
    assert srv.count(COMPLETION_PATH) == 0


# ---------------------------------------------------------------------------
# /completion envelope controls (criterion 3)
# ---------------------------------------------------------------------------

def test_completion_envelope_exact_minimal(server):
    srv, result = run_native(server, NativeScenario())
    assert result.outcome is CompletionOutcome.TERMINAL
    envelope = json.loads(srv.requests[1].body)
    expected_prompt = "SYNTH-TPL::" + chr(1).join([
        "<|system|>trusted annotation instructions",
        "<|user|>reference material one",
    ])
    assert envelope == {"prompt": expected_prompt, "n_predict": 16, "stream": False}


def test_completion_envelope_supported_sampling_and_json_controls(server):
    srv = server(NativeScenario().scenario)
    # qualified build: the json_schema grammar control is tested
    config = make_direct_config(
        srv.url, capabilities=DirectCapabilities(json_grammar_tested=True))
    result = make_generator(config).generate(
        make_request(temperature=0.2, top_p=0.9,
                     response_format="json_schema",
                     json_schema={"type": "object"}))
    assert result.outcome is CompletionOutcome.TERMINAL
    envelope = json.loads(srv.requests[1].body)
    assert envelope["temperature"] == 0.2
    assert envelope["top_p"] == 0.9
    assert envelope["json_schema"] == {"type": "object"}
    assert set(envelope) == {"prompt", "n_predict", "stream",
                             "temperature", "top_p", "json_schema"}


def test_completion_envelope_json_object_maps_to_any_json_grammar(server):
    """Pinned reference: json_schema {} is the any-JSON grammar form
    (qualified build; an unqualified request refuses before dispatch)."""
    srv = server(NativeScenario().scenario)
    config = make_direct_config(
        srv.url, capabilities=DirectCapabilities(json_grammar_tested=True))
    result = make_generator(config).generate(
        make_request(response_format="json_object"))
    assert result.outcome is CompletionOutcome.TERMINAL
    envelope = json.loads(srv.requests[1].body)
    assert envelope["json_schema"] == {}


@pytest.mark.parametrize("tested", [True, False], ids=["cache-tested", "cache-untested"])
def test_cache_prompt_only_with_tested_capability(server, tested):
    scenario = NativeScenario()
    srv = server(scenario.scenario)
    config = make_direct_config(
        srv.url, capabilities=DirectCapabilities(cache_prompt_tested=tested))
    result = make_generator(config).generate(
        make_request(prompt_cache_key="k1",
                     required_capabilities={Capability.PROMPT_CACHING}))
    envelope = json.loads(srv.requests[1].body) if tested else None
    if tested:
        assert result.outcome is CompletionOutcome.TERMINAL
        assert envelope["cache_prompt"] is True
        # the application-level key never appears on the native wire: the
        # documented native cache identity is the rendered prompt prefix
        # (plus the slot), not a key field
        assert "prompt_cache_key" not in envelope
        assert "slot_ids" not in envelope
    else:
        assert result.outcome is CompletionOutcome.FAILED
        assert "prompt caching refused" in (result.error or "")
        assert srv.paths == []




def test_id_slot_sent_when_tested(server):
    scenario = NativeScenario()
    srv = server(scenario.scenario)
    config = make_direct_config(srv.url, slot_id=2,
                                capabilities=DirectCapabilities(slot_tested=True))
    result = make_generator(config).generate(make_request())
    assert result.outcome is CompletionOutcome.TERMINAL
    envelope = json.loads(srv.requests[1].body)
    assert envelope["id_slot"] == 2
    assert "slot_ids" not in envelope


def test_untested_slot_id_is_config_error():
    from pydantic import ValidationError

    with pytest.raises(ValidationError, match="tested slot capability"):
        make_direct_config("http://127.0.0.1:9", slot_id=1,
                           capabilities=DirectCapabilities(slot_tested=False))


# ---------------------------------------------------------------------------
# deadline, retry, unknown completion (criterion 4)
# ---------------------------------------------------------------------------

class _FakeNativeTransport:
    """Injectable fake: ``fail_times`` positively pre-dispatch connect
    failures, then success on both pinned endpoints."""

    def __init__(self, fail_times: int) -> None:
        self.fail_times = fail_times
        self.calls = 0
        self.paths: list[str] = []

    def post_json(self, path, body, *, deadline=None):
        self.calls += 1
        self.paths.append(path)
        if self.calls <= self.fail_times:
            from slaif_raggedized_helper.model_clients.transport import (
                TransportConnectError,
            )
            raise TransportConnectError("fake pre-dispatch connect failure")
        if path == APPLY_TEMPLATE_PATH:
            doc = json.loads(body)
            return 200, json.dumps(
                {"prompt": render_prompt(doc["messages"])}).encode("utf-8")
        return 200, json.dumps(completion_doc()).encode("utf-8")


class _SteppingClock:
    """Deterministic generator-local clock (exact boundaries, no global
    time patching). Starts at zero; use _RealOffsetSteppingClock when the
    deadline must also be meaningful to the real transport clock."""

    def __init__(self, step: float) -> None:
        self.step = step
        self.calls = 0

    def __call__(self) -> float:
        value = self.step * self.calls
        self.calls += 1
        return value


class _RealOffsetSteppingClock:
    """Real monotonic base plus deterministic steps: the computed deadline
    is a genuine future real-time instant (the transport's own deadline
    checks stay meaningful) while the generator-local budget advances in
    exact steps."""

    def __init__(self, step: float) -> None:
        self.step = step
        self.base = _real_time.monotonic()
        self.calls = 0

    def __call__(self) -> float:
        value = self.base + self.step * self.calls
        self.calls += 1
        return value


class _BudgetConsumingNativeScenario:
    """Fake transport: consumes the whole budget, then fails as a
    positively pre-dispatch connect failure (retryable by policy)."""

    def __init__(self) -> None:
        self.calls = 0

    def post_json(self, path, body, *, deadline=None):
        self.calls += 1
        import time as _time
        _time.sleep(0.3)
        from slaif_raggedized_helper.model_clients.transport import (
            TransportConnectError,
        )
        raise TransportConnectError("fake pre-dispatch connect failure")


def test_retry_on_pre_dispatch_failure_shares_one_budget():
    # Two positively pre-dispatch failures, then success: the finite retry
    # budget is used and the whole generation (template + completion)
    # completes under the one shared budget.
    fake = _FakeNativeTransport(fail_times=2)
    config = make_direct_config("http://127.0.0.1:9", max_retries=2)
    generator = DirectNativeGenerator(config, transport=fake)
    result = generator.generate(make_request())
    assert result.outcome is CompletionOutcome.TERMINAL
    assert result.attempts == 3
    assert fake.paths.count(APPLY_TEMPLATE_PATH) == 3
    assert fake.paths.count(COMPLETION_PATH) == 1


def test_retry_budget_is_finite():
    # More pre-dispatch failures than the budget allows: exactly
    # 1 + max_retries attempts, then a safe failure (never an unknown
    # completion, because nothing was ever dispatched).
    fake = _FakeNativeTransport(fail_times=10)
    config = make_direct_config("http://127.0.0.1:9", max_retries=1)
    generator = DirectNativeGenerator(config, transport=fake)
    result = generator.generate(make_request())
    assert result.outcome is CompletionOutcome.FAILED
    assert result.attempts == 2
    assert "pre-dispatch connect failure" in (result.error or "")


def test_expired_deadline_refuses_before_re_dispatch_after_template_work(server):
    """Template work succeeds; the budget expires before the /completion
    dispatch of the (only) remaining attempt: no second dispatch, safe
    failure, no retry."""
    state = {"template_done": False}

    def scenario(h, r):
        if r.path == APPLY_TEMPLATE_PATH:
            doc = json.loads(r.body)
            h._send_json(200, {"prompt": render_prompt(doc["messages"])})
            state["template_done"] = True
        else:
            h._accept_then_close()

    srv = server(scenario)
    config = make_direct_config(srv.url, deadline_seconds=30, max_retries=2)
    # deterministic generator-local clock: deadline budget 1.0; after the
    # (real) template call the next budget check jumps past the deadline,
    # so the /completion dispatch must be refused before the send.
    clock = _RealOffsetSteppingClock(step=0.6)
    generator = DirectNativeGenerator(config, clock=clock)
    result = generator.generate(make_request(deadline=1.0))
    assert state["template_done"] is True
    assert result.outcome in (CompletionOutcome.FAILED, CompletionOutcome.UNKNOWN_COMPLETION)
    assert result.attempts == 1
    assert srv.count(COMPLETION_PATH) == 0


def test_pre_dispatch_timeout_is_retryable_within_budget():
    """A positively pre-dispatch connect timeout (closed port) uses the
    finite retry budget and then fails safe; no unknown completion is
    claimed for a call that never dispatched."""
    import socket

    probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    probe.bind(("127.0.0.1", 0))
    port = probe.getsockname()[1]
    probe.close()
    config = make_direct_config(f"http://127.0.0.1:{port}", max_retries=1,
                                deadline_seconds=30)
    result = make_generator(config).generate(make_request())
    assert result.outcome is CompletionOutcome.FAILED
    assert result.attempts == 2
    assert "connection failed before dispatch" in (result.error or "")


def test_budget_exhausted_refuses_before_first_dispatch(server):
    scenario = NativeScenario()
    srv = server(scenario.scenario)
    config = make_direct_config(srv.url, deadline_seconds=30)
    clock = _SteppingClock(step=100.0)  # first call already past the budget
    generator = DirectNativeGenerator(config, clock=clock)
    result = generator.generate(make_request(deadline=1.0))
    assert result.outcome is CompletionOutcome.FAILED
    assert result.attempts == 0
    assert "deadline exhausted before dispatch" in (result.error or "")
    assert srv.paths == []


# ---------------------------------------------------------------------------
# native stop semantics (criterion 5)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    ("doc_kwargs", "outcome", "needle"),
    [
        ({"stop_type": "limit"}, CompletionOutcome.INCOMPLETE, "n_predict"),
        ({"truncated": True}, CompletionOutcome.INCOMPLETE, "truncated"),
        ({"stop_type": "none"}, CompletionOutcome.INCOMPLETE, "still generating"),
        ({"stop": False}, CompletionOutcome.INCOMPLETE, "stop != true"),
        ({"content": ""}, CompletionOutcome.INCOMPLETE, "usable content"),
        ({"stop_type": "word"}, CompletionOutcome.FAILED, "stop-word"),
        ({"stop_type": "weird"}, CompletionOutcome.FAILED, "terminal reason"),
        ({"stop_type": None}, CompletionOutcome.FAILED, "terminal reason"),
        ({"stop_type": 7}, CompletionOutcome.FAILED, "terminal reason"),
        ({"content": 5}, CompletionOutcome.FAILED, "content"),
    ],
    ids=["limit", "truncated", "still-generating", "not-stopped",
         "empty-content", "unqualified-word", "unknown-stop-type",
         "null-stop-type", "non-string-stop-type", "non-string-content"],
)
def test_non_successful_terminals_never_become_terminal(server, doc_kwargs, outcome, needle):
    srv, result = run_native(server, NativeScenario(completion=completion_doc(**doc_kwargs)))
    assert result.outcome is outcome
    assert needle in (result.error or "")
    assert result.text is None
    assert srv.count(COMPLETION_PATH) == 1


def test_eos_with_usable_content_is_terminal(server):
    srv, result = run_native(server, NativeScenario())
    assert result.outcome is CompletionOutcome.TERMINAL
    prompt = json.loads(srv.requests[1].body)["prompt"]
    assert result.text == f"annotated span [0, {len(prompt)}]"
    assert result.error is None


def test_server_error_object_is_safe_refusal(server):
    srv, result = run_native(server, NativeScenario(completion={
        "error": {"code": 500, "type": "server_error", "message": CANARY_SECRET}}))
    assert result.outcome is CompletionOutcome.FAILED
    assert "native completion failed at the server" in (result.error or "")
    assert CANARY_SECRET not in (result.error or "")


@pytest.mark.parametrize("status", [400, 404, 500])
def test_http_error_statuses_are_safe(server, status):
    srv, result = run_native(
        server, NativeScenario(completion_body=b'{"error":{"message":"'
                                               + CANARY_SECRET.encode() + b'"}}',
                               completion_status=status))
    assert result.outcome is CompletionOutcome.FAILED
    assert f"native completion refused (HTTP {status})" in (result.error or "")
    assert CANARY_SECRET not in (result.error or "")


@pytest.mark.parametrize(
    "body",
    [
        b'{"content": "ok", "error": {"message": "CANARY-NATIVE-003e-DO-NOT-LEAK"}}',
        b"not json at all",
        b"",
        b"[1, 2, 3]",
        b"\xff\xfe invalid utf-8",
        b'{"content": ' + b"9" * 5000 + b"}",
    ],
    ids=["error-object-200", "not-json", "empty", "array", "invalid-utf8",
         "oversized-integer"],
)
def test_malformed_completion_bodies_are_safe(server, body):
    srv, result = run_native(server, NativeScenario(completion_body=body,
                                                    completion_status=200))
    assert result.outcome is CompletionOutcome.FAILED
    assert result.text is None
    assert CANARY_SECRET not in (result.error or "")
    assert srv.count(COMPLETION_PATH) == 1


def test_oversized_integer_in_native_response_is_safe():
    """The native parse guards the same expected decoder ValueError: a
    5000-digit counter (interpreter limit 4300 on observed hosts) is a
    malformed response, not a raw exception."""
    import sys as _sys

    body = (b'{"stop":true,"truncated":false,"stop_type":"eos","content":"ok",'
            b'"tokens_evaluated":' + b"9" * 5000 + b"}")
    from slaif_raggedized_helper.model_clients.direct import _parse_completion

    request = make_request()
    limit = _sys.get_int_max_str_digits()
    result = _parse_completion(body, request, "fp")
    if limit is not None and 5000 > limit:
        assert result.outcome is CompletionOutcome.FAILED
        assert "not valid JSON" in (result.error or "")
    else:
        assert result.outcome is CompletionOutcome.TERMINAL


# ---------------------------------------------------------------------------
# metrics (criterion 6)
# ---------------------------------------------------------------------------

def test_synthetic_metric_case_preserves_distinct_facts(server):
    """100-token submitted prompt: 10 newly evaluated / 90 cached, 12
    generated; the slot's resulting prompt reports 112 tokens. The
    top-level tokens_cached (= slot prompt total) must NOT substitute for
    timings.cache_n."""
    doc = completion_doc(
        content="x" * 12,
        tokens_evaluated=100,
        tokens_cached=112,
        tokens_predicted=12,
        timings={
            "cache_n": 90, "prompt_n": 10, "predicted_n": 12,
            "prompt_ms": 250.0, "predicted_ms": 1300.0,
            "prompt_per_token_ms": 25.0, "predicted_per_token_ms": 108.3,
        },
    )
    srv, result = run_native(server, NativeScenario(completion=doc))
    assert result.outcome is CompletionOutcome.TERMINAL
    usage = result.usage
    assert usage is not None
    assert usage.input_tokens == 100      # tokens_evaluated (task total)
    assert usage.prefill_tokens == 10     # timings.prompt_n (new work)
    assert usage.cache_hit_tokens == 90   # timings.cache_n (KV reuse)
    assert usage.output_tokens == 12      # timings.predicted_n
    timings = result.timings
    assert timings is not None
    assert timings.ttft_seconds is None       # never observed in this dialect
    assert timings.prefill_seconds == 0.25    # prompt_ms/1000 (not TTFT)
    assert timings.decode_seconds == 1.3      # predicted_ms/1000
    assert timings.total_seconds == 1.55      # model-scoped phase sum


@pytest.mark.parametrize(
    "field, bad_value",
    [
        ("tokens_evaluated", True),
        ("tokens_evaluated", -1),
        ("tokens_evaluated", 10.5),
        ("timings.prompt_n", True),
        ("timings.cache_n", float("nan")),
        ("timings.predicted_n", float("inf")),
        ("timings.prompt_ms", float("nan")),
        ("timings.prompt_ms", True),
        ("timings.predicted_ms", -5),
    ],
)
def test_malformed_or_unsafe_counters_stay_null(server, field, bad_value):
    doc = completion_doc()
    if field.startswith("timings."):
        doc["timings"][field.split(".", 1)[1]] = bad_value
    else:
        doc[field] = bad_value
    srv, result = run_native(server, NativeScenario(completion=doc))
    assert result.outcome is CompletionOutcome.TERMINAL
    usage = result.usage
    if field == "tokens_evaluated":
        assert usage.input_tokens is None
    elif field == "timings.prompt_n":
        assert usage.prefill_tokens is None
    elif field == "timings.cache_n":
        assert usage.cache_hit_tokens is None
    elif field == "timings.predicted_n":
        assert usage.output_tokens is None
    elif field == "timings.prompt_ms":
        assert result.timings is None or (
            result.timings.prefill_seconds is None
            and result.timings.total_seconds is None)
    else:  # timings.predicted_ms
        assert result.timings is None or (
            result.timings.decode_seconds is None
            and result.timings.total_seconds is None)


def test_missing_metric_fields_stay_null(server):
    doc = completion_doc()
    doc["timings"] = {}
    del doc["tokens_evaluated"]
    srv, result = run_native(server, NativeScenario(completion=doc))
    assert result.outcome is CompletionOutcome.TERMINAL
    assert result.usage is None
    assert result.timings is None


def test_reported_zero_millisecond_prefill_is_a_known_zero(server):
    """A measured reported 0ms is a known zero, not None; preserving the
    prefill zero must not discard the available decode."""
    doc = completion_doc(timings={"prompt_ms": 0, "predicted_ms": 60,
                                  "prompt_n": 10, "cache_n": 0, "predicted_n": 3})
    srv, result = run_native(server, NativeScenario(completion=doc))
    assert result.outcome is CompletionOutcome.TERMINAL
    timings = result.timings
    assert timings is not None
    assert timings.prefill_seconds == 0.0   # known zero, not null
    assert timings.decode_seconds == 0.06   # available decode preserved
    assert timings.total_seconds == 0.06    # model-scoped phase sum
    assert timings.ttft_seconds is None     # never observed in this dialect
    assert result.usage.prefill_tokens == 10


def test_overflow_reported_time_is_safe_over_http(server):
    """A reported prompt_ms of 10**400 is valid JSON within the byte/digit
    bounds but unrepresentable as a float: generate() must return a safe
    result (no raw OverflowError), the invalid phase stays unavailable and
    the other reported phase is preserved."""
    doc = completion_doc(timings={"prompt_ms": 10**400, "predicted_ms": 60.0,
                                  "prompt_n": 10, "cache_n": 0, "predicted_n": 3})
    srv, result = run_native(server, NativeScenario(completion=doc))
    assert result.outcome is CompletionOutcome.TERMINAL
    assert srv.count(COMPLETION_PATH) == 1
    timings = result.timings
    assert timings is not None
    assert timings.prefill_seconds is None
    assert timings.decode_seconds == 0.06
    assert timings.total_seconds is None  # both phases required for the sum
    assert timings.ttft_seconds is None


def test_finite_phase_sum_overflow_is_safe_over_http(server):
    """003-g actual-HTTP regression: both reported phase times are 1e308
    ms — individually finite, each converting to finite seconds (1e305) —
    but the millisecond sum overflows before division in the unsafe
    arithmetic. generate() must return a typed TERMINAL result (no raw
    OverflowError/ValidationError): the finite derived total is computed
    in SECONDS from the individually validated phases (2e305 s), the
    individually valid phase values are retained, TTFT stays unavailable,
    and no arbitrary physical-time cutoff is applied."""
    doc = completion_doc(timings={"prompt_n": 10, "cache_n": 0, "predicted_n": 3,
                                  "prompt_ms": 1e308, "predicted_ms": 1e308})
    srv, result = run_native(server, NativeScenario(completion=doc))
    assert result.outcome is CompletionOutcome.TERMINAL
    assert srv.count(COMPLETION_PATH) == 1
    assert result.usage is not None
    assert result.usage.input_tokens == 10
    assert result.usage.output_tokens == 3
    timings = result.timings
    assert timings is not None
    assert timings.prefill_seconds == 1e305
    assert timings.decode_seconds == 1e305
    assert timings.total_seconds == 2e305
    assert math.isfinite(timings.total_seconds)
    assert timings.ttft_seconds is None


def test_contradictory_reported_counters_are_withheld(server):
    """100 input with 90 new + 90 cached contradicts the supported
    dialect (prompt_n + cache_n must equal tokens_evaluated): the
    evaluated/cache breakdown is withheld (never fabricated work/caching
    proof); the directly reported task total keeps its own provenance and
    the generated count is unaffected."""
    doc = completion_doc(tokens_evaluated=100,
                         timings={"prompt_n": 90, "cache_n": 90,
                                  "predicted_n": 12,
                                  "prompt_ms": 30.0, "predicted_ms": 60.0})
    srv, result = run_native(server, NativeScenario(completion=doc))
    assert result.outcome is CompletionOutcome.TERMINAL
    usage = result.usage
    assert usage.input_tokens == 100
    assert usage.prefill_tokens is None
    assert usage.cache_hit_tokens is None
    assert usage.output_tokens == 12


def test_model_timings_are_model_reported_not_caller_wall(server):
    """The result timings come only from the dialect's own ms fields; the
    caller wall time (request deadline) never appears in them."""
    doc = completion_doc(timings={"prompt_ms": 1000.0, "predicted_ms": 1000.0})
    srv, result = run_native(server, NativeScenario(completion=doc))
    assert result.timings.prefill_seconds == 1.0
    assert result.timings.decode_seconds == 1.0
    assert result.timings.total_seconds == 2.0
    assert result.timings.ttft_seconds is None
    values = (result.timings.prefill_seconds, result.timings.decode_seconds,
              result.timings.total_seconds)
    assert 30.0 not in values


# ---------------------------------------------------------------------------
# identity and canaries
# ---------------------------------------------------------------------------

def test_identity_stable_and_distinct_from_response_text(server):
    scenario = NativeScenario()
    srv = server(scenario.scenario)
    config = make_direct_config(srv.url)
    generator = make_generator(config)
    assert generator.identity is not None
    assert generator.identity.name == "synthetic-qwen-native"
    assert generator.identity.adapter == "native-completion"
    fp1 = direct_backend_fingerprint(config)
    result1 = generator.generate(make_request(request_id="a",
                                               texts=["first text"]))
    result2 = generator.generate(make_request(request_id="b",
                                               texts=["second text"],
                                               instructions="other trusted"))
    fp2 = direct_backend_fingerprint(config)
    assert fp1 == fp2
    assert result1.fingerprint == result2.fingerprint == fp1
    assert result1.text != result2.text
    # response model alias and text never enter the identity
    assert "synthetic" not in fp1.replace("synthetic-qwen-native", "")


def test_identity_changes_with_declared_identity():
    # Fingerprint is a pure declared-identity function (no network): the
    # declared template identity (model-metadata default vs named) and the
    # endpoint/model/limits all must move it.
    url = "http://127.0.0.1:9"
    base = make_direct_config(url, template=None)
    named = make_direct_config(url, template="chatml")
    other_model = make_direct_config(url, template="zephyr")
    other_endpoint = make_direct_config("http://127.0.0.1:10", template=None)
    other_limits = make_direct_config(url, template=None, max_output_tokens=65)
    assert direct_backend_fingerprint(base) != direct_backend_fingerprint(named)
    assert direct_backend_fingerprint(named) != direct_backend_fingerprint(other_model)
    assert direct_backend_fingerprint(base) != direct_backend_fingerprint(other_endpoint)
    assert direct_backend_fingerprint(base) != direct_backend_fingerprint(other_limits)


def test_canary_in_rendered_prompt_stays_data(server):
    """Server-rendered canary text flows as DATA: it appears in the wire
    prompt bytes (the recorded request) but the result carries only the
    generated content."""
    text = "reference says " + CANARY_TEMPLATE
    srv, result = run_native(server, NativeScenario(), request=make_request(texts=[text]))
    assert result.outcome is CompletionOutcome.TERMINAL
    prompt = json.loads(srv.requests[1].body)["prompt"]
    assert CANARY_TEMPLATE in prompt
    assert result.text == f"annotated span [0, {len(prompt)}]"
