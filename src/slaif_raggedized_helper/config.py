"""Strict deployment configuration (OAP objective 002-a).

Rules enforced here (architecture A01/A13/A16/A19/A20, V2-01/V2-06, SECURITY S03):

- unknown fields are rejected at every level (``extra='forbid'``);
- budgets are finite and strictly positive;
- profile purpose/device/dtype combinations are explicit and checked against
  the supported matrix (online query embedding stays CPU FP32; GPU FP16
  reranker; exclusive-GPU offline embedding; no BF16 assumption);
- direct online generation is refused (gateway route is the only online path);
- degradation is either explicit (enabled + named allowed steps) or absent —
  a fallback configured outside an explicit degradation policy is rejected;
- secrets appear only as env/file *references* (names), never as values;
- network destinations must not embed credentials (no URL userinfo);
- a missing deployment route or artifact is an honest ``doctor`` issue, not a
  guessed config value or an import failure.
"""

from __future__ import annotations

import json
import re
from enum import Enum
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ._constraints import PositiveFiniteFloat, PositiveInt
from .schema import Device, Dtype

ENV_NAME_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")


def safe_validation_errors(exc: Exception, limit: int = 8) -> str:
    """Render a validation failure without echoing any input values.

    Only field locations and message templates are reported; ``input_value``,
    ``ctx`` and provider payloads are never serialized, so a rejected
    configuration cannot leak credentials embedded in the input.
    """
    errors = getattr(exc, "errors", None)
    if callable(errors):
        try:
            details = list(errors())
        except Exception:
            details = []
    else:
        details = []
    parts = []
    for detail in details[:limit]:
        location = ".".join(str(part) for part in detail.get("loc", ()))
        message = str(detail.get("msg", "invalid"))
        parts.append(f"{location}: {message}" if location else message)
    if not parts:
        parts.append("validation failed")
    suffix = "; ..." if len(details) > limit else ""
    return "; ".join(parts) + suffix


class ProfilePurpose(str, Enum):
    ONLINE_QUERY_EMBEDDING = "online_query_embedding"
    ONLINE_RERANK = "online_rerank"
    OFFLINE_EMBED = "offline_embed"
    OFFLINE_CONTEXT = "offline_context"


# Explicit purpose/device/dtype matrix. Anything else is a configuration error.
# Offline embedding allows the qualified GPU FP32 corpus mode in addition to the
# FP16 default (architecture A01/A16); FP32 storage is separate from compute.
ALLOWED_PROFILE_SHAPE: dict[ProfilePurpose, frozenset[tuple[Device, Dtype]]] = {
    ProfilePurpose.ONLINE_QUERY_EMBEDDING: frozenset({(Device.CPU, Dtype.FP32)}),
    ProfilePurpose.ONLINE_RERANK: frozenset({(Device.GPU, Dtype.FP16)}),
    ProfilePurpose.OFFLINE_EMBED: frozenset({(Device.GPU, Dtype.FP16), (Device.GPU, Dtype.FP32)}),
    ProfilePurpose.OFFLINE_CONTEXT: frozenset({(Device.GPU, Dtype.FP16)}),
}


class SecretRef(BaseModel):
    """A secret *name* or secret-file reference. Never a raw secret value."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: Literal["env", "file"]
    name: str = Field(min_length=1, max_length=256)

    @field_validator("name")
    @classmethod
    def _check_name(cls, value: str) -> str:
        if "\x00" in value or value.strip() != value:
            raise ValueError("secret reference name must be a plain non-empty token/path")
        return value

    @model_validator(mode="after")
    def _check_env_grammar(self) -> SecretRef:
        if self.kind == "env" and ENV_NAME_RE.fullmatch(self.name) is None:
            raise ValueError("env secret reference must be a valid environment variable name")
        return self


class RouteConfig(BaseModel):
    """Explicit gateway route contract reference (never guessed)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    base_url: str = Field(min_length=1, max_length=1024)
    model: str = Field(min_length=1, max_length=256)
    api: Literal["v1-responses"] = "v1-responses"
    timeout_seconds: PositiveFiniteFloat

    @field_validator("base_url")
    @classmethod
    def _check_url(cls, value: str) -> str:
        parts = urlsplit(value)
        if parts.scheme not in ("http", "https"):
            raise ValueError("route base_url must use http or https")
        if parts.username is not None or parts.password is not None:
            raise ValueError("credentials in the route URL are forbidden (no userinfo)")
        if parts.query or parts.fragment:
            raise ValueError(
                "query/fragment strings in the route URL are forbidden "
                "(no credentials or tokens in URLs)"
            )
        if not parts.hostname:
            raise ValueError("route base_url must contain a hostname")
        return value

    @property
    def host(self) -> str:
        return urlsplit(self.base_url).hostname or ""


class DegradationStep(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str = Field(min_length=1, max_length=128)


class DegradationPolicy(BaseModel):
    """Explicit degradation: disabled by default; when enabled it must name the
    allowed fallback steps. Implicit degradation is a configuration error."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    enabled: bool = False
    allow: list[DegradationStep] = Field(default_factory=list)

    @model_validator(mode="after")
    def _check_explicit(self) -> DegradationPolicy:
        names = [step.name for step in self.allow]
        if len(set(names)) != len(names):
            raise ValueError("degradation step names must be unique")
        if self.enabled and not self.allow:
            raise ValueError(
                "enabled degradation must name at least one explicit fallback step"
            )
        return self


class GeneratorConfig(BaseModel):
    """Online generation through the configured gateway route only."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    route: RouteConfig | None = None
    context_expected_tokens: PositiveInt
    output_reserve_tokens: PositiveInt
    deadline_seconds: PositiveFiniteFloat
    max_inflight: PositiveInt = 1
    degradation: DegradationPolicy = Field(default_factory=DegradationPolicy)
    fallback: str | None = Field(default=None, max_length=128)

    @model_validator(mode="after")
    def _check_degradation_explicitness(self) -> GeneratorConfig:
        if self.fallback is not None:
            if not self.degradation.enabled:
                raise ValueError(
                    "implicit degradation: a fallback is configured while the "
                    "degradation policy is disabled"
                )
            if self.fallback not in [step.name for step in self.degradation.allow]:
                raise ValueError(
                    "fallback is not one of the explicitly allowed degradation steps"
                )
        return self

    @model_validator(mode="after")
    def _check_output_reserve_fits_context(self) -> GeneratorConfig:
        if self.output_reserve_tokens >= self.context_expected_tokens:
            raise ValueError(
                "output_reserve_tokens must be strictly smaller than "
                "context_expected_tokens (input must retain room in the context)"
            )
        return self


class DirectGenerationConfig(BaseModel):
    """Direct (non-gateway) generation. Online direct generation is refused;
    a private trusted offline opt-in is a later explicit slice."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    enabled: bool = False

    @field_validator("enabled")
    @classmethod
    def _refuse_enabled(cls, value: bool) -> bool:
        if value:
            raise ValueError(
                "direct generation is not permitted in this slice: online generation "
                "must use the gateway route (no direct online fallback)"
            )
        return value


class ProfileConfig(BaseModel):
    """One named serving profile with an explicit purpose/device/dtype shape."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str = Field(min_length=1, max_length=128)
    purpose: ProfilePurpose
    device: Device
    dtype: Dtype

    @model_validator(mode="after")
    def _check_shape(self) -> ProfileConfig:
        allowed = ALLOWED_PROFILE_SHAPE[self.purpose]
        if (self.device, self.dtype) not in allowed:
            raise ValueError(
                f"profile {self.name!r}: purpose {self.purpose.value} does not permit "
                f"device={self.device.value} dtype={self.dtype.value}"
            )
        return self


class EmbeddingPolicy(BaseModel):
    """Exclusive offline embedding policy: offline embedding runs on an
    exclusive GPU (FP16 or qualified FP32 compute) and stores normalized FP32
    vectors (architecture A16: stored vectors are always FP32)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    exclusive_offline_gpu: bool = True
    store_dtype: Dtype = Dtype.FP32

    @field_validator("exclusive_offline_gpu")
    @classmethod
    def _refuse_shared(cls, value: bool) -> bool:
        if not value:
            raise ValueError(
                "offline embedding requires the exclusive-GPU policy (Qwen/reranker "
                "unloaded); a shared offline embedding profile is not permitted"
            )
        return value

    @field_validator("store_dtype")
    @classmethod
    def _require_fp32_store(cls, value: Dtype) -> Dtype:
        if value is not Dtype.FP32:
            raise ValueError("stored vectors must be normalized FP32 (architecture A16)")
        return value


class ModelLockRef(BaseModel):
    """Reference to a model lock/manifest file inspected by ``doctor``."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    role: Literal["generator", "embedding", "reranker"]
    path: str = Field(min_length=1, max_length=1024)


class RaggedizedConfig(BaseModel):
    """Top-level strict configuration loaded by ``raggedized doctor``."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal[1] = 1
    generator: GeneratorConfig
    profiles: list[ProfileConfig] = Field(default_factory=list)
    embedding: EmbeddingPolicy = Field(default_factory=EmbeddingPolicy)
    direct_generation: DirectGenerationConfig = Field(default_factory=DirectGenerationConfig)
    secrets: dict[str, SecretRef] = Field(default_factory=dict)
    model_locks: list[ModelLockRef] = Field(default_factory=list)

    @model_validator(mode="after")
    def _check_unique_names(self) -> RaggedizedConfig:
        names = [profile.name for profile in self.profiles]
        if len(set(names)) != len(names):
            raise ValueError("profile names must be unique")
        return self


class ConfigLoadError(ValueError):
    """Raised when a configuration file is missing, unreadable or invalid."""


def load_config(path: str | Path) -> RaggedizedConfig:
    """Load and strictly validate one JSON configuration file.

    Raises :class:`ConfigLoadError` for missing/unreadable/invalid input.
    No network, model loading or CUDA is involved.
    Error messages never echo input values (credentials embedded in a rejected
    configuration cannot leak through the error path).
    """
    config_path = Path(path)
    try:
        raw = config_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ConfigLoadError(f"cannot read config {config_path}: {exc.strerror or exc}") from exc
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ConfigLoadError(
            f"config is not valid JSON: line {exc.lineno} column {exc.colno}"
        ) from exc
    try:
        return RaggedizedConfig.model_validate(data)
    except Exception as exc:  # pydantic.ValidationError and friends
        raise ConfigLoadError(f"config validation failed: {safe_validation_errors(exc)}") from exc
