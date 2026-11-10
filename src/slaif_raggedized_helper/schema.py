"""Typed domain contracts for the raggedized helper (OAP objective 002-a).

Contracts covered:

- semantic generator request/result (purpose, bounded trusted input, optional
  authorized images, model/adapter identity, output/time budgets, capability
  declarations, explicit outcomes including unknown completion);
- embedding definition (checkpoint/tokenizer/pooling/L2/query policy/dimension)
  kept distinct from execution device/precision;
- rerank request/result binding pair IDs to finite scores (scores are not
  truth or confidence claims);
- model lock (exact immutable revision/artifact hashes, license status with
  explicit unknowns, tokenizer/pooling and Qwen GGUF/projector/runtime
  metadata);
- qualification records (named test, timestamp, code/model/runtime scope,
  mock/live mode, status, optional measured metrics).

Invariants (architecture A13/A16/A19, V2-02/V2-03/V2-06):

- missing counts are ``None`` (null/unavailable), never invented zero;
- fingerprints are canonical versioned serialization digests, not ``hash()``;
- incompatible or missing qualification evidence fails promotion;
- examples of unqualified manifests are never proof of a downloaded, pinned
  or license-approved model.
"""

from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime
from enum import Enum


from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ._constraints import NonNegativeInt, PositiveFiniteFloat, PositiveInt

FINGERPRINT_VERSION = 1


def _canonical(payload: object) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode(
        "utf-8"
    )


def fingerprint(payload: object) -> str:
    """Canonical versioned serialization digest (never Python ``hash()``)."""
    body = f"slaif-fingerprint-v{FINGERPRINT_VERSION}\n".encode("ascii") + _canonical(payload)
    return "sha256:" + hashlib.sha256(body).hexdigest()


class Capability(str, Enum):
    TEXT = "text"
    VISION = "vision"
    JSON_MODE = "json_mode"
    STREAMING = "streaming"
    PROMPT_CACHING = "prompt_caching"


class ModelIdentity(BaseModel):
    """Identity of the model/adapter a request is addressed to."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str = Field(min_length=1, max_length=256)
    adapter: str | None = Field(default=None, max_length=256)
    revision: str | None = Field(default=None, max_length=256)
    declared_capabilities: frozenset[Capability] = frozenset({Capability.TEXT})


class GeneratorPurpose(str, Enum):
    ANNOTATION = "annotation"
    VISUAL = "visual"
    ANSWER = "answer"


class CompletionOutcome(str, Enum):
    TERMINAL = "terminal"
    REFUSAL = "refusal"
    FAILED = "failed"
    INCOMPLETE = "incomplete"
    UNKNOWN_COMPLETION = "unknown_completion"


MAX_INPUT_ITEMS = 64
MAX_INPUT_CHARS = 200_000
MAX_IMAGES = 16
MAX_INSTRUCTIONS = 16_000
MAX_JSON_SCHEMA_BYTES = 32_768


class TextItem(BaseModel):
    """One bounded trusted text input."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    text: str = Field(min_length=1, max_length=MAX_INPUT_CHARS)


class ImageRef(BaseModel):
    """Reference to an authorized image bound to a source revision (no raw bytes)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    image_id: str = Field(min_length=1, max_length=256)
    source_revision: str = Field(min_length=1, max_length=256)


class GeneratorRequest(BaseModel):
    """Typed semantic generator request (annotation/visual/answer)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    request_id: str = Field(min_length=1, max_length=128)
    purpose: GeneratorPurpose
    items: list[TextItem] = Field(min_length=1, max_length=MAX_INPUT_ITEMS)
    images: list[ImageRef] | None = Field(default=None, max_length=MAX_IMAGES)
    model: ModelIdentity
    required_capabilities: frozenset[Capability] = frozenset()
    max_output_tokens: PositiveInt
    deadline_seconds: PositiveFiniteFloat
    instructions: str | None = Field(default=None, max_length=MAX_INSTRUCTIONS)
    temperature: float | None = Field(default=None, ge=0.0, le=2.0)
    top_p: float | None = Field(default=None, gt=0.0, le=1.0)
    response_format: Literal["text", "json_object", "json_schema"] | None = None
    json_schema: dict[str, Any] | None = None
    prompt_cache_key: str | None = Field(default=None, min_length=1, max_length=128)

    @field_validator("json_schema")
    @classmethod
    def _check_json_schema_bound(cls, value: dict[str, Any] | None) -> dict[str, Any] | None:
        if value is None:
            return None
        payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        if len(payload.encode("utf-8")) > MAX_JSON_SCHEMA_BYTES:
            raise ValueError("json_schema exceeds the bounded wire size")
        return value

    @model_validator(mode="after")
    def _check_purpose_and_capabilities(self) -> GeneratorRequest:
        if self.purpose is GeneratorPurpose.VISUAL and not self.images:
            raise ValueError("visual purpose requires at least one authorized image")
        missing = self.required_capabilities - self.model.declared_capabilities
        if missing:
            raise ValueError(
                "request requires capabilities the model does not declare: "
                + ", ".join(sorted(c.value for c in missing))
            )
        if self.response_format == "json_schema" and self.json_schema is None:
            raise ValueError("response_format json_schema requires a bounded json_schema payload")
        if self.json_schema is not None and self.response_format != "json_schema":
            raise ValueError("json_schema payload requires response_format json_schema")
        if self.prompt_cache_key is not None:
            if Capability.PROMPT_CACHING not in self.required_capabilities:
                raise ValueError("prompt_cache_key requires the prompt_caching capability")
        return self


class UsageMetrics(BaseModel):
    """Available usage counters.

    Missing counts stay null/unavailable and must never be invented as zero;
    a measured zero is legitimate, negative counts are not.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    input_tokens: NonNegativeInt | None = None
    output_tokens: NonNegativeInt | None = None
    prefill_tokens: NonNegativeInt | None = None
    cache_hit_tokens: NonNegativeInt | None = None


class TimingMetrics(BaseModel):
    """Available timings. Missing measurements stay null/unavailable, never zero."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    ttft_seconds: PositiveFiniteFloat | None = None
    total_seconds: PositiveFiniteFloat | None = None


class GeneratorResult(BaseModel):
    """Typed semantic generator result with an explicit completion outcome."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    request_id: str = Field(min_length=1, max_length=128)
    outcome: CompletionOutcome
    text: str | None = None
    usage: UsageMetrics | None = None
    timings: TimingMetrics | None = None
    fingerprint: str | None = None
    error: str | None = Field(default=None, max_length=1024)
    attempts: NonNegativeInt | None = None

    @model_validator(mode="after")
    def _check_outcome_consistency(self) -> GeneratorResult:
        if self.outcome is CompletionOutcome.TERMINAL and self.text is None:
            raise ValueError("terminal outcome requires answer text")
        if (
            self.outcome in (CompletionOutcome.FAILED, CompletionOutcome.UNKNOWN_COMPLETION)
            and not self.error
        ):
            raise ValueError(
                f"{self.outcome.value} outcome requires a safe error reason (no provider raw body)"
            )
        return self


class Device(str, Enum):
    CPU = "cpu"
    GPU = "gpu"


class Dtype(str, Enum):
    FP32 = "fp32"
    FP16 = "fp16"


class EmbeddingDefinition(BaseModel):
    """Embedding *space* definition: checkpoint/tokenizer/pooling/L2/query policy/dimension.

    Deliberately distinct from execution device/precision (see
    :class:`EmbeddingExecution`); a qualified CPU/GPU pairing is recorded
    explicitly, never inferred (architecture V2-02/A16).
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    model_name: str = Field(min_length=1, max_length=256)
    checkpoint_revision: str = Field(min_length=1, max_length=256)
    checkpoint_sha256: str | None = Field(default=None, max_length=71)
    tokenizer_revision: str | None = Field(default=None, max_length=256)
    pooling: Literal["cls", "mean"]
    normalize: bool = True
    query_prefix: str | None = Field(default=None, max_length=128)
    dimensions: PositiveInt

    @field_validator("checkpoint_sha256")
    @classmethod
    def _check_sha(cls, value: str | None) -> str | None:
        if value is not None and _is_lower_hex64(value) is False:
            raise ValueError("checkpoint_sha256 must be 64 lowercase hex characters")
        return value

    def fingerprint(self) -> str:
        """Space fingerprint over the definition identity fields."""
        return fingerprint(
            {
                "version": FINGERPRINT_VERSION,
                "kind": "embedding-space",
                "model_name": self.model_name,
                "checkpoint_revision": self.checkpoint_revision,
                "checkpoint_sha256": self.checkpoint_sha256,
                "tokenizer_revision": self.tokenizer_revision,
                "pooling": self.pooling,
                "normalize": self.normalize,
                "query_prefix": self.query_prefix,
                "dimensions": self.dimensions,
            }
        )


class EmbeddingExecution(BaseModel):
    """Execution device/precision bound to one embedding definition."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    definition: EmbeddingDefinition
    device: Device
    dtype: Dtype

    def fingerprint(self) -> str:
        """Execution fingerprint: space fingerprint + device + precision."""
        return fingerprint(
            {
                "version": FINGERPRINT_VERSION,
                "kind": "embedding-execution",
                "space": self.definition.fingerprint(),
                "device": self.device.value,
                "dtype": self.dtype.value,
            }
        )


class RerankPair(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    pair_id: str = Field(min_length=1, max_length=128)
    query_id: str = Field(min_length=1, max_length=128)
    passage_id: str = Field(min_length=1, max_length=128)


class RerankRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    pairs: list[RerankPair] = Field(min_length=1, max_length=512)
    deadline_seconds: PositiveFiniteFloat

    @model_validator(mode="after")
    def _check_unique_pair_ids(self) -> RerankRequest:
        seen = {p.pair_id for p in self.pairs}
        if len(seen) != len(self.pairs):
            raise ValueError("pair_id values must be unique")
        return self


class RerankResult(BaseModel):
    """Finite rerank scores keyed by pair ID.

    Scores are relative relevance estimates only; they are not truth or
    confidence claims (architecture A19).
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    scores: dict[str, float]

    @field_validator("scores")
    @classmethod
    def _check_finite(cls, value: dict[str, float]) -> dict[str, float]:
        for pair_id, score in value.items():
            if not math.isfinite(score):
                raise ValueError(f"score for {pair_id!r} must be finite")
        return value


class RerankBindingError(ValueError):
    """Raised when rerank scores do not bind exactly to the submitted pair IDs."""


def bind_rerank_scores(request: RerankRequest, result: RerankResult) -> None:
    """Require exactly one finite score for each submitted pair ID (V2-06)."""
    expected = {p.pair_id for p in request.pairs}
    got = set(result.scores)
    missing = expected - got
    extra = got - expected
    if missing or extra:
        raise RerankBindingError(
            "rerank result must bind exactly the submitted pair IDs "
            f"(missing={sorted(missing)}, extra={sorted(extra)})"
        )


class LicenseStatus(str, Enum):
    APPROVED = "approved"
    UNKNOWN = "unknown"


class GGUFMetadata(BaseModel):
    """Qwen GGUF serving metadata (generator role)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    quantization: str = Field(min_length=1, max_length=32)
    artifact_sha256: str | None = Field(default=None, max_length=71)

    @field_validator("artifact_sha256")
    @classmethod
    def _check_sha(cls, value: str | None) -> str | None:
        if value is not None and _is_lower_hex64(value) is False:
            raise ValueError("artifact hashes must be 64 lowercase hex characters")
        return value


def _is_lower_hex64(value: str) -> bool:
    return len(value) == 64 and all(c in "0123456789abcdef" for c in value)


class RuntimeMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str = Field(min_length=1, max_length=256)
    version: str | None = Field(default=None, max_length=128)


class ModelLock(BaseModel):
    """Exact immutable model revision/artifact and license record.

    Unknown values are explicit nulls/``unknown`` — an unqualified lock is not
    proof that a model was downloaded, pinned or license-approved.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal[1] = 1
    role: Literal["generator", "embedding", "reranker"]
    model_name: str = Field(min_length=1, max_length=256)
    revision: str = Field(min_length=1, max_length=256)
    artifact_sha256: str | None = Field(default=None, max_length=71)
    license_name: str | None = Field(default=None, max_length=128)
    license_status: LicenseStatus = LicenseStatus.UNKNOWN
    tokenizer_revision: str | None = Field(default=None, max_length=256)
    pooling: str | None = Field(default=None, max_length=64)
    gguf: GGUFMetadata | None = None
    projector: str | None = Field(default=None, max_length=256)
    runtime: RuntimeMetadata | None = None

    @field_validator("artifact_sha256", "gguf")
    @classmethod
    def _check_hex(cls, value: object) -> object:
        if isinstance(value, str) and _is_lower_hex64(value) is False:
            raise ValueError("artifact hashes must be 64 lowercase hex characters")
        return value

    @model_validator(mode="after")
    def _check_role_specifics(self) -> ModelLock:
        if self.gguf is not None and self.role != "generator":
            raise ValueError("gguf metadata is only valid for the generator role")
        return self


class QualificationRecord(BaseModel):
    """Named test evidence for one model at one code/model/runtime scope."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal[1] = 1
    test_name: str = Field(min_length=1, max_length=256)
    recorded_at: datetime
    code_scope: str = Field(min_length=1, max_length=128)
    model_scope: str = Field(min_length=1, max_length=256)
    runtime_scope: str = Field(min_length=1, max_length=256)
    mode: Literal["mock", "live"]
    status: Literal["pass", "fail", "not_run", "blocked"]
    metrics: dict[str, float] | None = None

    @field_validator("recorded_at")
    @classmethod
    def _check_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("recorded_at must carry an explicit UTC offset")
        return value

    @field_validator("metrics")
    @classmethod
    def _check_metrics(cls, value: dict[str, float] | None) -> dict[str, float] | None:
        if value is not None:
            for key, metric in value.items():
                if not math.isfinite(metric):
                    raise ValueError(f"metric {key!r} must be finite")
        return value


class ModelManifest(BaseModel):
    """A model lock plus its qualification evidence; unqualified by default."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal[1] = 1
    lock: ModelLock
    qualification: QualificationRecord | None = None

    def evaluate(self) -> tuple[str, list[str]]:
        """Return ``(qualification_status, issues)``; incompatible/missing
        evidence fails promotion (returns ``unqualified``)."""
        issues: list[str] = []
        lock = self.lock
        if lock.license_status is not LicenseStatus.APPROVED:
            issues.append("license status is not approved (explicit unknown remains unresolved)")
        if lock.artifact_sha256 is None:
            issues.append("artifact hash is unknown (no pinned artifact evidence)")
        record = self.qualification
        if record is None:
            issues.append("no qualification record (NOT RUN)")
        else:
            if record.status != "pass":
                issues.append(f"qualification status is {record.status}")
            elif record.model_scope != lock.revision:
                issues.append(
                    f"qualification model_scope {record.model_scope!r} does not match "
                    f"lock revision {lock.revision!r}"
                )
            if record.mode == "mock":
                issues.append("qualification evidence is mock-mode only (live proof absent)")
        status = "qualified" if not issues else "unqualified"
        return status, issues

    def summary(self) -> dict[str, object]:
        """Safe machine-readable summary for doctor output (no raw artifacts)."""
        status, issues = self.evaluate()
        return {
            "role": self.lock.role,
            "model_name": self.lock.model_name,
            "revision": self.lock.revision,
            "license_status": self.lock.license_status.value,
            "artifact_pinned": self.lock.artifact_sha256 is not None,
            "qualification": status,
            "qualification_mode": self.qualification.mode if self.qualification else None,
            "issues": issues,
            "note": (
                "qualification reflects recorded evidence only; it is not proof of a "
                "downloaded, pinned or license-approved model"
            ),
        }
