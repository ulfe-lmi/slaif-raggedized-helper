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

import ipaddress
import json
import re
from enum import Enum
from pathlib import Path
from datetime import datetime
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


class RouteCapabilities(BaseModel):
    """Explicit transport capabilities advertised by the configured route.

    Everything is default-deny: an optional control (streaming, vision,
    structured output, prompt caching) is usable only when its route
    capability is explicitly declared here (architecture A13/A18: no JSON/
    stream/vision/cache support is guessed).
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    streaming: bool = False
    vision: bool = False
    json_mode: bool = False
    structured_outputs: bool = False
    prompt_caching: bool = False
    stored_responses: bool = False


class RouteConfig(BaseModel):
    """Explicit gateway route contract reference (never guessed)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    base_url: str = Field(min_length=1, max_length=1024)
    model: str = Field(min_length=1, max_length=256)
    api: Literal["v1-responses"] = "v1-responses"
    timeout_seconds: PositiveFiniteFloat
    capabilities: RouteCapabilities = Field(default_factory=RouteCapabilities)

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
        # Pinned v1-responses contract: the base is the gateway root (any
        # reverse-proxy prefix preserved) or that root plus the /v1 API
        # segment. Anything else cannot be interpreted without guessing.
        if parts.path not in ("", "/") and not parts.path.endswith("/v1"):
            raise ValueError(
                "route base_url path must be the gateway root or end with "
                "the /v1 API segment"
            )
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
    api_key_ref: str | None = Field(default=None, max_length=256)
    max_retries: int = Field(default=1, ge=0, le=5)

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


# Built-in chat template names of the pinned llama.cpp server reference
# (ggml-org/llama.cpp commit 3b4d6ab3f79651935fba1dd93732f29022a7f5f5,
# ``--chat-template`` registry). This is a REFERENCE registry copied from the
# pinned upstream source, not a hard client-side allowlist: a qualified
# server-rendered identity is the model-metadata default template (Jinja
# enabled by default on that reference) or an operator-declared Jinja
# template, and it is rendered by the server through ``/apply-template`` —
# the client never guesses special tokens or enforces an arbitrary local
# name list (unknown template names are refused by the server itself, and
# that refusal is mapped to a safe typed failure). A name in this registry
# is still NOT qualification: offline_diagnostic mode requires a
# DirectTemplateQualification record binding the declared template identity
# to a tested build (README /apply-template or pinned-upstream verification).
# The reference revision is not the unknown deployed build.
PINNED_LLAMA_BUILTIN_CHAT_TEMPLATES = (
    "bailing", "bailing-think", "bailing2", "chatglm3", "chatglm4",
    "chatml", "command-r", "deepseek", "deepseek-ocr", "deepseek2",
    "deepseek3", "exaone-moe", "exaone3", "exaone4", "falcon3", "gemma",
    "gigachat", "glmedge", "gpt-oss", "granite", "granite-4.0",
    "granite-4.1", "grok-2", "hunyuan-dense", "hunyuan-moe",
    "hunyuan-vl", "kimi-k2", "llama2", "llama2-sys", "llama2-sys-bos",
    "llama2-sys-strip", "llama3", "llama4", "megrez", "minicpm",
    "mistral-v1", "mistral-v3", "mistral-v3-tekken", "mistral-v7",
    "mistral-v7-tekken", "monarch", "openchat", "orion",
    "pangu-embedded", "phi3", "phi4", "rwkv-world", "seed_oss",
    "smolvlm", "solar-open", "vicuna", "vicuna-orca", "yandex",
    "zephyr",
)

# The native message closing marker of the gateway-style dialect. A declared
# TEMPLATE IDENTITY carrying this sequence is refused at config time because
# formatter provenance must come from the qualified server template (or an
# actually qualified local renderer), never from a hand-invented delimiter.
# This is an identity-token rule: it does not ban the literal substring in
# message content or in a server-rendered prompt (source content is data and
# is preserved verbatim; template/build qualification — not substring
# scanning of rendered text — establishes formatter provenance).
TEMPLATE_IDENTITY_FORBIDDEN_SEQUENCE = "\x3c/tool_call\x3e"



class DirectCapabilities(BaseModel):
    """Tested native /completion capabilities of the private llama build.

    ``cache_prompt``/slot selection enter the wire envelope only when the
    capability was actually tested on that build (architecture A13: native
    cache_prompt/id_slot only on tested builds).
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    cache_prompt_tested: bool = False
    slot_tested: bool = False


class DirectDestination(BaseModel):
    """Private trusted /completion destination (never a public caller choice).

    Private IP/localhost alone is not access-control proof: enabling direct
    mode additionally requires the explicit ``private_trusted`` policy
    declaration on :class:`DirectGenerationConfig`.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    base_url: str = Field(min_length=1, max_length=1024)

    @field_validator("base_url")
    @classmethod
    def _check_private_url(cls, value: str) -> str:
        parts = urlsplit(value)
        if parts.scheme not in ("http", "https"):
            raise ValueError("direct destination must use http or https")
        if parts.username is not None or parts.password is not None:
            raise ValueError("credentials in the direct destination URL are forbidden")
        if parts.query or parts.fragment:
            raise ValueError("query/fragment strings in the direct destination URL are forbidden")
        hostname = parts.hostname
        if not hostname:
            raise ValueError("direct destination must contain a hostname")
        if not _is_private_destination_host(hostname):
            raise ValueError(
                "direct destination must be a private/loopback host "
                "(private IP alone is not access-control proof; declare the "
                "trusted policy explicitly)"
            )
        return value


def _is_private_destination_host(hostname: str) -> bool:
    host = hostname.strip("[]").lower()
    if host == "localhost" or host.endswith(".localhost"):
        return True
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        return False
    if address.is_unspecified:
        return False
    return address.is_private or address.is_loopback or address.is_link_local


class DirectTemplateQualification(BaseModel):
    """Explicit qualification record binding a chat template to a build.

    The template name alone never proves qualification: offline direct
    mode requires this record, produced by ``POST /apply-template`` against
    the tested build or by pinned-upstream verification of the exact
    built-in template rendering.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    # The qualified template identity: a declared template name, or None for
    # the server's model-metadata default template (Jinja enabled on the
    # pinned reference). None must match a config chat_template of None.
    template: str | None = Field(default=None, min_length=1, max_length=64)
    build_id: str = Field(min_length=1, max_length=128)
    method: Literal["apply-template", "pinned-upstream"]
    recorded_at: datetime

    @field_validator("recorded_at")
    @classmethod
    def _check_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("recorded_at must carry an explicit UTC offset")
        return value


class DirectGenerationConfig(BaseModel):
    """Direct (non-gateway) generation.

    Online direct generation is unconditionally refused: the ``enabled``
    guard from the foundation slice is retained and no online direct mode
    exists. ``mode: offline_diagnostic`` is the narrow explicit offline
    opt-in for context-annotation/visual-extraction diagnostics against a
    private trusted destination; it is never an answer fallback.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    enabled: bool = False
    mode: Literal["disabled", "offline_diagnostic"] = "disabled"
    destination: DirectDestination | None = None
    trusted_policy: Literal["private_trusted"] | None = None
    capabilities: DirectCapabilities = Field(default_factory=DirectCapabilities)
    # Declared model identity (the operator-declared model/alias of the
    # private build). Distinct from response text/IDs; the deployed
    # runtime/GGUF identity stays explicitly unverified. Required for
    # offline_diagnostic mode; absent means the identity is unknown, not
    # guessed.
    model: str | None = Field(default=None, min_length=1, max_length=256)
    # Declared template identity: a template name (pinned built-in or
    # operator Jinja template) or None for the server's model-metadata
    # default template. Rendered by the server via /apply-template; the
    # client performs no local template rendering (unimplemented local
    # modes are refused, never claimed qualified).
    chat_template: str | None = Field(default=None, max_length=64)
    template_qualification: DirectTemplateQualification | None = None
    slot_id: int | None = Field(default=None, ge=0)
    # Explicit finite operator limits for the materialized offline mode:
    # None is not permission to use an uncapped caller allowance; missing
    # operator limits refuse before template/generation dispatch.
    max_output_tokens: PositiveInt | None = None
    deadline_seconds: PositiveFiniteFloat | None = None
    max_retries: int = Field(default=0, ge=0, le=3)

    @field_validator("enabled")
    @classmethod
    def _refuse_enabled(cls, value: bool) -> bool:
        if value:
            raise ValueError(
                "direct generation is not permitted in this slice: online generation "
                "must use the gateway route (no direct online fallback)"
            )
        return value

    @field_validator("chat_template")
    @classmethod
    def _check_template(cls, value: str | None) -> str | None:
        # None = the server's model-metadata default template (Jinja enabled
        # on the pinned reference); a name = a declared template identity
        # (pinned built-in or operator Jinja template). No arbitrary local
        # name allowlist: the server renders via /apply-template and refuses
        # unknown templates itself. Only the template IDENTITY token is
        # constrained here (plain token; the forbidden closing-marker
        # sequence is not a legal identity because formatter provenance must
        # come from the qualified server template).
        if value is None:
            return None
        if any(ch.isspace() or ord(ch) < 0x20 or ord(ch) == 0x7F for ch in value):
            raise ValueError("chat_template must be a plain non-empty token")
        if "/" in value or value.startswith("."):
            raise ValueError("chat_template is a template identity, not a path")
        if TEMPLATE_IDENTITY_FORBIDDEN_SEQUENCE in value:
            raise ValueError(
                "chat_template identity must not carry the native closing "
                "marker sequence"
            )
        return value

    @model_validator(mode="after")
    def _check_offline_opt_in(self) -> DirectGenerationConfig:
        if self.mode == "offline_diagnostic":
            if self.destination is None:
                raise ValueError("offline_diagnostic mode requires a private destination")
            if self.trusted_policy != "private_trusted":
                raise ValueError(
                    "offline_diagnostic mode requires the explicit private_trusted policy"
                )
            if self.model is None:
                raise ValueError(
                    "offline_diagnostic mode requires the declared model identity"
                )
            if self.template_qualification is None:
                raise ValueError(
                    "offline_diagnostic mode requires a template qualification record"
                )
            if self.template_qualification.template != self.chat_template:
                raise ValueError(
                    "template qualification record does not match the declared "
                    "chat_template (None is the model-metadata default)"
                )
            if self.max_output_tokens is None:
                raise ValueError(
                    "offline_diagnostic mode requires the explicit finite operator "
                    "max_output_tokens (a None limit is not an uncapped allowance)"
                )
            if self.deadline_seconds is None:
                raise ValueError(
                    "offline_diagnostic mode requires the explicit finite operator "
                    "deadline_seconds (a None limit is not an uncapped allowance)"
                )
            if self.slot_id is not None and not self.capabilities.slot_tested:
                raise ValueError("slot_id requires the tested slot capability")
        else:
            if self.destination is not None or self.trusted_policy is not None:
                raise ValueError(
                    "disabled direct mode must not carry a destination or trusted policy"
                )
        return self


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

    @model_validator(mode="after")
    def _check_api_key_ref(self) -> RaggedizedConfig:
        ref = self.generator.api_key_ref
        if ref is not None and ref not in self.secrets:
            raise ValueError(
                f"generator.api_key_ref {ref!r} does not name a declared secret reference"
            )
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
