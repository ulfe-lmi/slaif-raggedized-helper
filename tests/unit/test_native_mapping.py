"""Unit tests for the native direct mapping (pure, no network) — 003-e.

Covers the pinned-dialect metric mapping (including the synthetic
100-submitted / 10-new / 90-cached / 12-generated / tokens_cached=112
case), the stop-terminal outcome matrix, the envelope builders and the
identity fingerprint at unit level (the loopback suite covers the same
behavior over real HTTP).
"""

from __future__ import annotations

import json

import pytest

from slaif_raggedized_helper.config import (
    DirectCapabilities,
    DirectDestination,
    DirectGenerationConfig,
    DirectTemplateQualification,
)
from slaif_raggedized_helper.model_clients.direct import (
    _parse_completion,
    _parse_native_timings,
    _parse_native_usage,
    build_apply_template_envelope,
    build_completion_envelope,
    direct_backend_fingerprint,
)
from slaif_raggedized_helper.schema import (
    CompletionOutcome,
    GeneratorPurpose,
    GeneratorRequest,
    ModelIdentity,
    TextItem,
)


def make_request(**kwargs) -> GeneratorRequest:
    base = dict(
        request_id="u1",
        purpose=GeneratorPurpose.ANNOTATION,
        items=[TextItem(text="reference")],
        model=ModelIdentity(name="synthetic-qwen-native"),
        max_output_tokens=16,
        deadline_seconds=30.0,
        instructions="trusted instructions",
    )
    base.update(kwargs)
    return GeneratorRequest(**base)


def make_doc(**overrides) -> dict:
    doc = {
        "index": 0,
        "content": "ok",
        "tokens": [],
        "id_slot": 0,
        "stop": True,
        "model": "synthetic-qwen-native",
        "tokens_predicted": 3,
        "tokens_evaluated": 10,
        "generation_settings": {"n_predict": 16},
        "prompt": "rendered",
        "has_new_line": False,
        "truncated": False,
        "stop_type": "eos",
        "stopping_word": "",
        "tokens_cached": 13,
        "timings": {
            "cache_n": 0, "prompt_n": 10, "predicted_n": 3,
            "prompt_ms": 100.0, "predicted_ms": 300.0,
        },
    }
    doc.update(overrides)
    return doc


def parse(doc: dict) -> "object":
    return _parse_completion(json.dumps(doc).encode("utf-8"), make_request(), "fp")


# ---------------------------------------------------------------------------
# metric mapping (criterion 6)
# ---------------------------------------------------------------------------

def test_synthetic_case_preserves_distinct_facts():
    """100 submitted (10 new / 90 cached), 12 generated, slot prompt total
    112: the four facts stay distinct; tokens_cached (112) never
    substitutes for timings.cache_n (90)."""
    doc = make_doc(
        tokens_evaluated=100,
        tokens_cached=112,
        tokens_predicted=12,
        timings={"cache_n": 90, "prompt_n": 10, "predicted_n": 12,
                 "prompt_ms": 250.0, "predicted_ms": 1300.0},
    )
    result = parse(doc)
    assert result.outcome is CompletionOutcome.TERMINAL
    assert result.usage.input_tokens == 100
    assert result.usage.prefill_tokens == 10
    assert result.usage.cache_hit_tokens == 90
    assert result.usage.output_tokens == 12
    assert 112 not in (result.usage.input_tokens, result.usage.prefill_tokens,
                       result.usage.cache_hit_tokens, result.usage.output_tokens)
    assert result.timings.ttft_seconds == 0.25
    assert result.timings.total_seconds == 1.55


@pytest.mark.parametrize("counter", ["tokens_cached", "tokens_predicted"])
def test_top_level_slot_counters_never_map_when_dialect_fields_absent(counter):
    """tokens_cached is the slot's resulting prompt token count (prompt +
    generated) and tokens_predicted duplicates timings.predicted_n: with
    the dialect fields absent, neither may be substituted for the mapped
    usage fields (nothing is invented)."""
    doc = make_doc(**{counter: 999})
    doc.pop("tokens_evaluated")
    doc["timings"] = {}
    assert _parse_native_usage(doc) is None


def test_tokens_evaluated_maps_and_slot_counter_does_not_shadow_it():
    doc = make_doc(tokens_evaluated=5, tokens_cached=999)
    usage = _parse_native_usage(doc)
    assert usage.input_tokens == 5
    # the slot total must not leak into cache_hit_tokens
    assert usage.cache_hit_tokens == 0  # timings.cache_n, not tokens_cached


@pytest.mark.parametrize(
    "field, value",
    [
        ("tokens_evaluated", True),
        ("tokens_evaluated", -1),
        ("tokens_evaluated", 10.5),
        ("timings.prompt_n", True),
        ("timings.cache_n", float("nan")),
        ("timings.predicted_n", float("inf")),
        ("timings.prompt_ms", float("nan")),
        ("timings.prompt_ms", -1),
        ("timings.predicted_ms", "12.5"),
    ],
)
def test_unsafe_counter_types_are_rejected(field, value):
    doc = make_doc()
    if field.startswith("timings."):
        doc["timings"][field.split(".", 1)[1]] = value
    else:
        doc[field] = value
    result = parse(doc)
    assert result.outcome is CompletionOutcome.TERMINAL  # counters are not the outcome
    if field == "tokens_evaluated":
        assert result.usage.input_tokens is None
    elif field == "timings.prompt_n":
        assert result.usage.prefill_tokens is None
    elif field == "timings.cache_n":
        assert result.usage.cache_hit_tokens is None
    elif field == "timings.predicted_n":
        assert result.usage.output_tokens is None
    else:
        if field == "timings.prompt_ms":
            assert result.timings is None or result.timings.ttft_seconds is None
        else:
            assert result.timings is None or result.timings.total_seconds is None


def test_missing_metrics_stay_null():
    doc = make_doc()
    doc.pop("tokens_evaluated")
    doc["timings"] = {}
    result = parse(doc)
    assert result.outcome is CompletionOutcome.TERMINAL
    assert result.usage is None
    assert result.timings is None


def test_zero_millisecond_values_are_null_in_positive_contract():
    assert _parse_native_timings({"prompt_ms": 0, "predicted_ms": 0}) is None
    # a measured zero prompt_ms with a positive predicted_ms: ttft null,
    # total requires both -> null as well
    assert _parse_native_timings({"prompt_ms": 0, "predicted_ms": 50}) is None


def test_timings_map_only_from_reported_fields():
    timings = _parse_native_timings({"prompt_ms": 250.0, "predicted_ms": 750.0})
    assert timings.ttft_seconds == 0.25
    assert timings.total_seconds == 1.0
    assert _parse_native_timings(None) is None
    assert _parse_native_timings("nope") is None


# ---------------------------------------------------------------------------
# stop terminal matrix (criterion 5)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    ("overrides", "outcome"),
    [
        ({}, CompletionOutcome.TERMINAL),
        ({"stop_type": "limit"}, CompletionOutcome.INCOMPLETE),
        ({"truncated": True}, CompletionOutcome.INCOMPLETE),
        ({"stop_type": "none"}, CompletionOutcome.INCOMPLETE),
        ({"stop": False}, CompletionOutcome.INCOMPLETE),
        ({"stop": "true"}, CompletionOutcome.INCOMPLETE),
        ({"content": ""}, CompletionOutcome.INCOMPLETE),
        ({"stop_type": "word"}, CompletionOutcome.FAILED),
        ({"stop_type": None}, CompletionOutcome.FAILED),
        ({"stop_type": []}, CompletionOutcome.FAILED),
        ({"stop_type": "other"}, CompletionOutcome.FAILED),
        ({"content": None}, CompletionOutcome.FAILED),
        ({"content": ["ok"]}, CompletionOutcome.FAILED),
        ({"error": {"message": "boom"}}, CompletionOutcome.FAILED),
    ],
)
def test_terminal_outcome_matrix(overrides, outcome):
    result = parse(make_doc(**overrides))
    assert result.outcome is outcome
    if outcome is not CompletionOutcome.TERMINAL:
        assert result.text is None
        assert result.error


def test_terminal_requires_usable_content():
    result = parse(make_doc(content="usable text"))
    assert result.outcome is CompletionOutcome.TERMINAL
    assert result.text == "usable text"


def test_response_model_alias_does_not_change_outcome():
    result = parse(make_doc(model="some-other-alias"))
    assert result.outcome is CompletionOutcome.TERMINAL
    assert result.text == "ok"


# ---------------------------------------------------------------------------
# envelope builders (criterion 3)
# ---------------------------------------------------------------------------

def test_apply_template_envelope_serialization():
    request = make_request(items=[TextItem(text="a"), TextItem(text="b")])
    envelope = build_apply_template_envelope(request)
    assert envelope == {
        "messages": [
            {"role": "system", "content": "trusted instructions"},
            {"role": "user", "content": "a"},
            {"role": "user", "content": "b"},
        ]
    }
    # no instructions -> no system message; items keep order
    request = make_request(instructions=None)
    assert build_apply_template_envelope(request) == {
        "messages": [{"role": "user", "content": "reference"}]
    }


def test_completion_envelope_allows_only_supported_controls():
    request = make_request(temperature=0.5, top_p=0.8,
                           response_format="json_schema",
                           json_schema={"type": "string"})
    envelope = build_completion_envelope(
        request, prompt="P", n_predict=8, cache_prompt=True, id_slot=1)
    assert envelope == {
        "prompt": "P", "n_predict": 8, "stream": False,
        "temperature": 0.5, "top_p": 0.8,
        "json_schema": {"type": "string"},
        "cache_prompt": True, "id_slot": 1,
    }
    # invented slot arrays / keys cannot appear
    assert "slot_ids" not in envelope
    assert "prompt_cache_key" not in envelope


def test_completion_envelope_json_object_is_any_json_grammar():
    request = make_request(response_format="json_object")
    envelope = build_completion_envelope(request, prompt="P", n_predict=8,
                                         cache_prompt=False, id_slot=None)
    assert envelope["json_schema"] == {}


def test_completion_envelope_minimal_by_default():
    request = make_request()
    envelope = build_completion_envelope(request, prompt="P", n_predict=8,
                                         cache_prompt=False, id_slot=None)
    assert envelope == {"prompt": "P", "n_predict": 8, "stream": False}


# ---------------------------------------------------------------------------
# identity fingerprint (criterion 5)
# ---------------------------------------------------------------------------

def _config(**overrides) -> DirectGenerationConfig:
    base = dict(
        mode="offline_diagnostic",
        destination=DirectDestination(base_url="http://127.0.0.1:8080"),
        trusted_policy="private_trusted",
        model="synthetic-qwen-native",
        chat_template=None,
        template_qualification=DirectTemplateQualification(
            template=None, build_id="b1", method="apply-template",
            recorded_at="2026-11-10T00:00:00+00:00"),
        max_output_tokens=64,
        deadline_seconds=30.0,
    )
    base.update(overrides)
    return DirectGenerationConfig.model_validate(base)


def test_fingerprint_stable_and_sensitive():
    config = _config()
    fp = direct_backend_fingerprint(config)
    assert fp.startswith("sha256:")
    # stable across calls
    assert direct_backend_fingerprint(config) == fp
    # sensitive to declared identity pieces
    assert direct_backend_fingerprint(
        _config(model="other-model")) != fp
    assert direct_backend_fingerprint(
        _config(destination=DirectDestination(base_url="http://127.0.0.1:9090"))) != fp
    assert direct_backend_fingerprint(
        _config(chat_template="mistral-v3",
                template_qualification=DirectTemplateQualification(
                    template="mistral-v3", build_id="b1",
                    method="apply-template",
                    recorded_at="2026-11-10T00:00:00+00:00"))) != fp
    assert direct_backend_fingerprint(
        _config(capabilities=DirectCapabilities(cache_prompt_tested=True))) != fp
    assert direct_backend_fingerprint(
        _config(max_output_tokens=65)) != fp
    assert direct_backend_fingerprint(
        _config(slot_id=1, capabilities=DirectCapabilities(slot_tested=True))) != fp
