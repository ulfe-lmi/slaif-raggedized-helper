"""Typed contract behavior: outcomes, null metrics, fingerprints, pair binding."""

from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from slaif_raggedized_helper.schema import (
    Capability,
    CompletionOutcome,
    Device,
    Dtype,
    EmbeddingDefinition,
    EmbeddingExecution,
    GeneratorPurpose,
    GeneratorRequest,
    GeneratorResult,
    ModelIdentity,
    RerankRequest,
    RerankResult,
    UsageMetrics,
    bind_rerank_scores,
)


def make_identity(**overrides) -> ModelIdentity:
    data = {
        "name": "Qwen3.8-27B-Q6",
        "adapter": "gateway-v1",
        "revision": "rev-1",
    }
    data.update(overrides)
    return ModelIdentity.model_validate(data)


def make_request(**overrides) -> GeneratorRequest:
    data = {
        "request_id": "req-1",
        "purpose": GeneratorPurpose.ANSWER,
        "items": [{"text": "What is the rerank pair cap?"}],
        "images": None,
        "model": make_identity().model_dump(),
        "required_capabilities": frozenset(),
        "max_output_tokens": 1536,
        "deadline_seconds": 60.0,
    }
    data.update(overrides)
    return GeneratorRequest.model_validate(data)


def test_answer_request_construction_with_identity_capabilities():
    # Regression: ModelIdentity must expose declared_capabilities so a plain
    # answer request validates (no AttributeError in request construction).
    request = make_request()
    assert request.model.declared_capabilities == frozenset({Capability.TEXT})
    request = make_request(
        model=make_identity(
            declared_capabilities=frozenset({Capability.TEXT, Capability.VISION})
        ).model_dump(),
        purpose=GeneratorPurpose.VISUAL,
        images=[{"image_id": "img-1", "source_revision": "rev-doc-1"}],
        required_capabilities=frozenset({Capability.VISION}),
    )
    assert request.model.declared_capabilities == frozenset({Capability.TEXT, Capability.VISION})


def test_terminal_outcome_requires_text():
    with pytest.raises(ValidationError, match="terminal outcome requires"):
        GeneratorResult.model_validate(
            {"request_id": "r", "outcome": "terminal", "text": None}
        )


def test_failed_and_unknown_completion_require_safe_reason():
    for outcome in ("failed", "unknown_completion"):
        with pytest.raises(ValidationError, match="requires a safe error reason"):
            GeneratorResult.model_validate({"request_id": "r", "outcome": outcome, "error": None})
    result = GeneratorResult.model_validate(
        {
            "request_id": "r",
            "outcome": "unknown_completion",
            "error": "timed out after bounded retry",
        }
    )
    assert result.outcome is CompletionOutcome.UNKNOWN_COMPLETION


def test_missing_usage_counts_stay_null_not_zero():
    result = GeneratorResult.model_validate(
        {"request_id": "r", "outcome": "terminal", "text": "answer", "usage": {}}
    )
    assert result.usage is not None
    assert result.usage.input_tokens is None
    dumped = json.loads(result.model_dump_json())
    assert dumped["usage"] == {
        "input_tokens": None,
        "output_tokens": None,
        "prefill_tokens": None,
        "cache_hit_tokens": None,
    }


def test_negative_usage_counts_rejected_and_measured_zero_allowed():
    with pytest.raises(ValidationError, match="non-negative"):
        UsageMetrics.model_validate({"input_tokens": -5})
    with pytest.raises(ValidationError, match="non-negative"):
        UsageMetrics.model_validate({"output_tokens": -1})
    usage = UsageMetrics.model_validate({"input_tokens": 0, "output_tokens": 0})
    assert usage.input_tokens == 0


def test_visual_purpose_requires_authorized_images():
    with pytest.raises(ValidationError, match="authorized image"):
        make_request(purpose=GeneratorPurpose.VISUAL, images=None)
    make_request(
        purpose=GeneratorPurpose.VISUAL,
        images=[{"image_id": "img-1", "source_revision": "rev-doc-1"}],
    )


def test_required_capabilities_must_be_declared_by_model():
    model = make_identity()  # no declared capabilities beyond default TEXT
    with pytest.raises(ValidationError, match="does not declare"):
        make_request(
            model=model.model_dump(),
            required_capabilities=frozenset({Capability.VISION}),
        )


def test_bounded_trusted_input():
    with pytest.raises(ValidationError):
        make_request(items=[])
    with pytest.raises(ValidationError):
        make_request(items=[{"text": "x" * (200_001)}])
    make_request(items=[{"text": "ok"}])


def test_embedding_space_fingerprint_distinctions():
    def definition(**overrides) -> EmbeddingDefinition:
        data = {
            "model_name": "BGE-M3",
            "checkpoint_revision": "rev-ckpt-1",
            "pooling": "cls",
            "normalize": True,
            "query_prefix": "Represent: ",
            "dimensions": 1024,
        }
        data.update(overrides)
        return EmbeddingDefinition.model_validate(data)

    base = definition()
    assert base.fingerprint() == definition().fingerprint()
    # dimension change changes the space (equal dimensions alone is insufficient)
    assert base.fingerprint() != definition(dimensions=768).fingerprint()
    assert base.fingerprint() != definition(pooling="mean").fingerprint()
    assert base.fingerprint() != definition(normalize=False).fingerprint()
    assert base.fingerprint() != definition(query_prefix=None).fingerprint()
    assert base.fingerprint() != definition(checkpoint_revision="rev-ckpt-2").fingerprint()
    assert base.fingerprint() != definition(checkpoint_sha256="ab" * 32).fingerprint()


def test_execution_fingerprint_separates_device_precision_from_space():
    definition = EmbeddingDefinition.model_validate(
        {
            "model_name": "BGE-M3",
            "checkpoint_revision": "rev-ckpt-1",
            "pooling": "cls",
            "dimensions": 1024,
        }
    )
    cpu_fp32 = EmbeddingExecution.model_validate(
        {"definition": definition, "device": Device.CPU, "dtype": Dtype.FP32}
    )
    gpu_fp16 = EmbeddingExecution.model_validate(
        {"definition": definition, "device": Device.GPU, "dtype": Dtype.FP16}
    )
    # same space, different execution
    assert cpu_fp32.definition.fingerprint() == gpu_fp16.definition.fingerprint()
    assert cpu_fp32.fingerprint() != gpu_fp16.fingerprint()
    # same execution is stable
    assert cpu_fp32.fingerprint() == EmbeddingExecution.model_validate(
        {"definition": definition, "device": Device.CPU, "dtype": Dtype.FP32}
    ).fingerprint()


def test_rerank_pair_ids_must_be_unique():
    with pytest.raises(ValidationError, match="unique"):
        RerankRequest.model_validate(
            {
                "pairs": [
                    {"pair_id": "p1", "query_id": "q", "passage_id": "a"},
                    {"pair_id": "p1", "query_id": "q", "passage_id": "b"},
                ],
                "deadline_seconds": 30,
            }
        )


def test_rerank_scores_must_be_finite():
    with pytest.raises(ValidationError, match="finite"):
        RerankResult.model_validate({"scores": {"p1": float("inf")}})
    with pytest.raises(ValidationError, match="finite"):
        RerankResult.model_validate({"scores": {"p1": float("nan")}})


def test_rerank_binding_requires_exact_pair_coverage():
    request = RerankRequest.model_validate(
        {
            "pairs": [
                {"pair_id": "p1", "query_id": "q", "passage_id": "a"},
                {"pair_id": "p2", "query_id": "q", "passage_id": "b"},
            ],
            "deadline_seconds": 30,
        }
    )
    exact = RerankResult.model_validate({"scores": {"p1": 0.9, "p2": 0.4}})
    bind_rerank_scores(request, exact)  # no raise

    with pytest.raises(Exception, match="missing"):
        bind_rerank_scores(request, RerankResult.model_validate({"scores": {"p1": 0.9}}))
    with pytest.raises(Exception, match="extra"):
        bind_rerank_scores(
            request, RerankResult.model_validate({"scores": {"p1": 0.9, "p2": 0.4, "p3": 0.1}})
        )


def test_usage_metrics_accept_partial_availability():
    usage = UsageMetrics.model_validate({"input_tokens": 100, "output_tokens": None})
    assert usage.prefill_tokens is None
    dumped = json.loads(usage.model_dump_json())
    assert dumped["output_tokens"] is None and dumped["input_tokens"] == 100
