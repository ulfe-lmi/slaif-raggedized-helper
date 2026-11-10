"""Explicit strict bounded sample/result evidence contracts (OAP 004-b/c).

004-a criterion 1 (004-F02): the per-sample records and the trial
result envelope are EXACT, BOUNDED, FROZEN DTOs — no untyped
``dict[str, Any]`` at the construction, serialization or analysis
boundaries:

- they bind the schema/version, sample ordinal/phase, the fixed
  outcome vocabulary, declared/observed identities, workload/backend
  fingerprints, known-or-null reported counters and timings, the
  actual transport-boundary call accounting and finite
  collection/field limits;
- malformed identity/outcome/numeric shapes and bool-as-number are
  REFUSED; unknown values stay null, a reported known 0 is preserved,
  and contradictory reported cache/input facts remain valid raw facts
  (their invalidity label lives in the accounting section, never in a
  mutation of the raw value);
- a missing metric is NEVER fabricated as 0, upstream semantics are
  not changed, and spent accounting is never dropped after work;
- the public dict JSON compatibility is preserved through validated
  DTO serialization (the rendered document is the DTO projection of
  the same values);
- ``validate_trial_evidence`` additionally requires the analysis
  section to equal the PURE recomputation from the recorded samples —
  a forged or drifted analysis is a contract violation.
  004-c (004B-F01): the recomputation is driven by the ACTUAL
  transport-boundary call ledger (``transport_boundary.calls_by_kind``),
  never by the analysis's own copy of the call counts — a duplicated
  fact that drifts from the ledger is a contract violation.

All scalar fields are STRICT: no implicit coercion (a bool is never a
number, a float is never an integer counter, a string is never a
boolean).

Cross-field bindings enforced by the envelope (004-c, 004B-F01):

- the envelope backend equals the declared backend;
- every KNOWN per-sample backend fingerprint equals the observed
  per-trial backend binding (an absent binding stays null, never
  guessed);
- the output-reservation metadata equals the same declared
  total/per-sample budget used by execution, and the per-sample share
  is the floor even share over the DECLARED scheduled sample count
  (never the shorter recorded prefix after an early stop);
- the provenance pair is consistent (MOCK iff
  synthetic-owned-fixture; CONFIGURED_UNVERIFIED iff unverified);
- the cache/input consistency counts equal the pure derivation from
  the ACTUALLY RECORDED raw usage (raw contradictory facts stay valid
  sample values; the label lives in the accounting section).
"""

from __future__ import annotations

import math
from typing import Any, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictBool,
    StrictFloat,
    StrictInt,
    field_validator,
    model_validator,
)

from .spec import (
    MAX_DEADLINE_SECONDS,
    MAX_DISPATCHES,
    MAX_OUTPUT_TOKENS_TOTAL,
    MAX_PARENT_CHARS,
    MAX_REPETITIONS,
    MAX_SEED,
    MAX_SUFFIX_CHARS,
    MAX_SUFFIXES,
    MAX_TRIAL_ID_CHARS,
    MAX_WARMUPS,
    _PLAIN_TOKEN_RE,
    _SHA256_DIGEST_RE,
)

MAX_REQUESTS = MAX_WARMUPS + MAX_REPETITIONS
MAX_INPUT_CHARS = MAX_PARENT_CHARS + MAX_SUFFIX_CHARS
MAX_ERROR_CHARS = 1024
MAX_FINGERPRINT_FIELD_CHARS = 1024
MAX_NOTE_CHARS = 4096
MAX_KIND_KEY_CHARS = 64

OUTCOME_VALUES = (
    "terminal", "refusal", "failed", "incomplete", "unknown_completion"
)
STAGE_METRIC_KEYS = (
    "caller_wall_seconds", "prefill_seconds", "decode_seconds",
    "model_total_seconds", "ttft_seconds",
)


def _digest_field(value: str, field_name: str) -> str:
    if _SHA256_DIGEST_RE.fullmatch(value) is not None:
        return value
    raise ValueError(f"{field_name} must be a sha256:<64 lowercase hex> digest")


def _finite_nonneg_float(value: Any, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field_name} must be a finite non-negative number")
    number = float(value)
    if not math.isfinite(number) or number < 0:
        raise ValueError(f"{field_name} must be finite and non-negative")
    return number


def _plain_token(value: str, field_name: str) -> str:
    if _PLAIN_TOKEN_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a plain non-empty token")
    return value


def _raw_nonneg_int(value: Any, field_name: str) -> int:
    """Strict non-negative integer on the RAW (pre-coercion) value."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field_name} must be an integer, not a boolean")
    if value < 0:
        raise ValueError(f"{field_name} must be non-negative")
    return value


class UsageFacts(BaseModel):
    """Reported-only usage counters; unknown stays null, known 0 kept."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    input_tokens: StrictInt | None = Field(default=None, ge=0)
    output_tokens: StrictInt | None = Field(default=None, ge=0)
    prefill_tokens: StrictInt | None = Field(default=None, ge=0)
    cache_hit_tokens: StrictInt | None = Field(default=None, ge=0)


class TimingsFacts(BaseModel):
    """Reported-only model-phase timings; unknown stays null, known 0 kept.

    A missing gateway prefill or a native TTFT stays null (unavailable),
    never a fabricated zero.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    ttft_seconds: StrictFloat | None = None
    prefill_seconds: StrictFloat | None = None
    decode_seconds: StrictFloat | None = None
    total_seconds: StrictFloat | None = None

    @field_validator("ttft_seconds", "prefill_seconds", "decode_seconds",
                     "total_seconds")
    @classmethod
    def _finite(cls, value: float | None, info: Any) -> float | None:
        if value is None:
            return None
        return _finite_nonneg_float(value, info.field_name)


class TrialSample(BaseModel):
    """One executed sample record (bounded; raw text never present)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    ordinal: StrictInt = Field(ge=0, le=MAX_REQUESTS - 1)
    phase: Literal["warmup", "measured"]
    first_repetition: StrictBool
    # Physical cold/warm state is UNKNOWN without cache reset/isolation
    # evidence and is never inferred from position.
    physical_state: Literal["unknown"]
    suffix_index: StrictInt = Field(ge=0, le=MAX_SUFFIXES - 1)
    input_chars: StrictInt = Field(ge=0, le=MAX_INPUT_CHARS)
    input_fingerprint: str
    outcome: Literal["terminal", "refusal", "failed", "incomplete",
                     "unknown_completion"]
    # Fixed safe error class (no provider raw body); absent on clean
    # outcomes.
    error: str | None = Field(default=None, max_length=MAX_ERROR_CHARS)
    # Adapter-reported cycle count (NOT the authoritative dispatch
    # count, which lives in the transport boundary); unknown stays null.
    adapter_reported_cycles: StrictInt | None = Field(default=None, ge=0)
    text_fingerprint: str | None = None
    content_fingerprint: str | None = None
    # Per-request declared backend binding exported by the adapter;
    # an absent binding stays null, never guessed.
    backend_fingerprint: str | None = Field(
        default=None, max_length=MAX_FINGERPRINT_FIELD_CHARS)
    usage: UsageFacts
    timings: TimingsFacts
    # Caller wall time around one generate(); measured, never faked;
    # null only when the observation is missing.
    wall_seconds: StrictFloat | None = None

    @field_validator("input_fingerprint")
    @classmethod
    def _check_input_fp(cls, value: str) -> str:
        return _digest_field(value, "input_fingerprint")

    @field_validator("text_fingerprint", "content_fingerprint")
    @classmethod
    def _check_text_fp(cls, value: str | None, info: Any) -> str | None:
        if value is None:
            return None
        return _digest_field(value, info.field_name)

    @field_validator("wall_seconds")
    @classmethod
    def _check_wall(cls, value: float | None) -> float | None:
        if value is None:
            return None
        return _finite_nonneg_float(value, "wall_seconds")


# ---------------------------------------------------------------------------
# analysis section
# ---------------------------------------------------------------------------

def derive_cache_input_consistency_counts(
        samples: list[dict[str, Any]]) -> tuple[int, int, int]:
    """Derive the supported cache/input accounting relation per sample.

    Over the ACTUALLY RECORDED raw usage (shared by the runner and the
    result validator, 004-c): a sample that reports no
    ``cache_hit_tokens`` is uncounted (unknown stays unknown); a known
    ``cache_hit_tokens`` with missing ``input_tokens`` is
    ``uncheckable``; ``cache_hit_tokens > input_tokens`` is
    ``contradictory``; otherwise ``consistent``. Contradictory counters
    remain valid raw sample facts — the label lives here, never in a
    mutation of the raw value.
    """
    consistent = contradictory = uncheckable = 0
    for sample in samples:
        usage = sample["usage"]
        cache_hit = usage["cache_hit_tokens"]
        input_tokens = usage["input_tokens"]
        if cache_hit is None:
            continue
        if input_tokens is None:
            uncheckable += 1
        elif cache_hit > input_tokens:
            contradictory += 1
        else:
            consistent += 1
    return consistent, contradictory, uncheckable


class _QuartileBlock(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    n: StrictInt = Field(ge=0, le=MAX_REQUESTS)
    min: StrictFloat | None = None
    p50: StrictFloat | None = None
    p95: StrictFloat | None = None
    max: StrictFloat | None = None

    @model_validator(mode="after")
    def _check_quartile_completeness(self) -> "_QuartileBlock":
        # n == 0 requires ALL-NULL quartiles; n > 0 requires EVERY
        # quartile present (004B-F02: a partial quartile set with a
        # positive count contradicts the summary contract), finite,
        # non-negative and ordered min <= p50 <= p95 <= max.
        quartiles = (self.min, self.p50, self.p95, self.max)
        if self.n == 0:
            if any(value is not None for value in quartiles):
                raise ValueError(
                    "n==0 requires all-null quartiles")
            return self
        if any(value is None for value in quartiles):
            raise ValueError(
                "n>0 requires every quartile present (min, p50, p95, max)")
        values = [
            _finite_nonneg_float(value, name)
            for name, value in zip(("min", "p50", "p95", "max"),
                                   quartiles)
        ]
        if not (values[0] <= values[1] <= values[2] <= values[3]):
            raise ValueError(
                "quartiles must be ordered min <= p50 <= p95 <= max")
        return self


class LatencySeconds(_QuartileBlock):
    convention: str = Field(min_length=1, max_length=MAX_NOTE_CHARS)


class StageMetric(_QuartileBlock):
    """One reported metric's stage summary for one phase group.

    Missingness is preserved explicitly: a null reported value is
    ABSENT from the metric set (never a zero); a non-finite/negative
    reported value is counted invalid and excluded.
    """

    missing: StrictInt = Field(ge=0, le=MAX_REQUESTS)
    invalid_observations: StrictInt = Field(ge=0, le=MAX_REQUESTS)
    source: str = Field(min_length=1, max_length=MAX_NOTE_CHARS)


class StageMetrics(BaseModel):
    """Per-metric stage summaries for one phase group (004-F03).

    Native reported prefill/decode/model-total stay distinct from
    caller wall time/template work; the pinned gateway dialect reports
    no prefill and neither dialect reports a TTFT, so those stages stay
    unavailable (n=0, all null) — never 0.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    convention: str = Field(min_length=1, max_length=MAX_NOTE_CHARS)
    caller_wall_seconds: StageMetric
    prefill_seconds: StageMetric
    decode_seconds: StageMetric
    model_total_seconds: StageMetric
    ttft_seconds: StageMetric

    def stage_values(self) -> tuple[StageMetric, ...]:
        return (
            self.caller_wall_seconds,
            self.prefill_seconds,
            self.decode_seconds,
            self.model_total_seconds,
            self.ttft_seconds,
        )


class GroupStats(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    samples_total: StrictInt = Field(ge=0, le=MAX_REQUESTS)
    outcome_counts: dict[str, int]
    terminal_samples: StrictInt = Field(ge=0, le=MAX_REQUESTS)
    invalid_wall_observations: StrictInt = Field(ge=0, le=MAX_REQUESTS)
    latency_seconds: LatencySeconds
    stage_metrics: StageMetrics

    @field_validator("outcome_counts", mode="before")
    @classmethod
    def _check_outcome_counts(cls, value: Any) -> dict[str, int]:
        if not isinstance(value, dict):
            raise ValueError("outcome_counts must be a mapping")
        checked: dict[str, int] = {}
        for key, count in value.items():
            if not isinstance(key, str) or key not in OUTCOME_VALUES:
                raise ValueError(
                    f"unknown outcome {key!r} in outcome_counts")
            _raw_nonneg_int(count, f"outcome_counts[{key}]")
            if count < 1:
                raise ValueError("outcome counts are positive integers")
            checked[key] = count
        return checked

    @model_validator(mode="after")
    def _check_consistency(self) -> "GroupStats":
        if sum(self.outcome_counts.values()) != self.samples_total:
            raise ValueError("outcome_counts must sum to samples_total")
        if self.terminal_samples != self.outcome_counts.get("terminal", 0):
            raise ValueError("terminal_samples must equal the terminal count")
        if (self.terminal_samples != self.latency_seconds.n
                + self.invalid_wall_observations):
            raise ValueError(
                "terminal samples are exactly the finite wall values plus "
                "the unusable wall observations")
        for metric in self.stage_metrics.stage_values():
            if (metric.n + metric.missing + metric.invalid_observations
                    != self.terminal_samples):
                raise ValueError(
                    "stage metric "
                    f"{type(metric).__name__}: n + missing + invalid must "
                    "equal terminal samples")
        return self


class TimingBoundaryNotes(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    wall_seconds_scope: str = Field(min_length=1, max_length=MAX_NOTE_CHARS)
    native_template_time: str = Field(min_length=1, max_length=MAX_NOTE_CHARS)
    gateway_prefill: str = Field(min_length=1, max_length=MAX_NOTE_CHARS)
    reported_cache_tokens: str = Field(min_length=1, max_length=MAX_NOTE_CHARS)


class QualifyingPassGroup(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    possible: StrictBool
    reason: str = Field(min_length=1, max_length=256)


class QualifyingPass(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    warmups: QualifyingPassGroup
    measured: QualifyingPassGroup
    note: str = Field(min_length=1, max_length=MAX_NOTE_CHARS)


class AnalysisSection(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    warmups: GroupStats
    measured: GroupStats
    transport_calls_by_kind: dict[str, int]
    timing_boundary_notes: TimingBoundaryNotes
    qualifying_pass: QualifyingPass

    @field_validator("transport_calls_by_kind", mode="before")
    @classmethod
    def _check_kinds(cls, value: Any) -> dict[str, int]:
        if not isinstance(value, dict):
            raise ValueError("transport_calls_by_kind must be a mapping")
        checked: dict[str, int] = {}
        for key, count in value.items():
            if not isinstance(key, str) or not key or len(key) > MAX_KIND_KEY_CHARS:
                raise ValueError("kind keys are bounded non-empty strings")
            _raw_nonneg_int(count, f"transport_calls_by_kind[{key}]")
            checked[key] = count
        return checked


# ---------------------------------------------------------------------------
# result envelope sections
# ---------------------------------------------------------------------------

class SuffixEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    index: StrictInt = Field(ge=0, le=MAX_SUFFIXES - 1)
    chars: StrictInt = Field(ge=1, le=MAX_SUFFIX_CHARS)
    fingerprint: str

    @field_validator("fingerprint")
    @classmethod
    def _check_fp(cls, value: str) -> str:
        return _digest_field(value, "fingerprint")


class WorkloadSection(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: Literal["repeated-parent"]
    parent_chars: StrictInt = Field(ge=1, le=MAX_PARENT_CHARS)
    parent_fingerprint: str
    suffixes: list[SuffixEvidence] = Field(
        min_length=1, max_length=MAX_SUFFIXES)
    samples: StrictInt = Field(ge=1, le=MAX_REQUESTS)
    warmups: StrictInt = Field(ge=0, le=MAX_WARMUPS)
    repetitions: StrictInt = Field(ge=1, le=MAX_REPETITIONS)
    concurrency: Literal[1]
    seed: StrictInt = Field(ge=0, le=MAX_SEED)
    seed_semantics: str = Field(min_length=1, max_length=MAX_NOTE_CHARS)
    workload_fingerprint: str
    workload_fingerprint_verified_pre_dispatch: StrictBool
    cache_control: str = Field(min_length=1, max_length=512)

    @field_validator("parent_fingerprint", "workload_fingerprint")
    @classmethod
    def _check_fps(cls, value: str, info: Any) -> str:
        return _digest_field(value, info.field_name)

    @model_validator(mode="after")
    def _check_sequence(self) -> "WorkloadSection":
        if self.warmups + self.repetitions != self.samples:
            raise ValueError("samples must equal warmups + repetitions")
        for position, suffix in enumerate(self.suffixes):
            if suffix.index != position:
                raise ValueError("suffix indices must be positional")
        return self


class BudgetsSection(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    deadline_seconds: StrictFloat
    max_dispatches: StrictInt = Field(ge=1, le=MAX_DISPATCHES)
    max_output_tokens_total: StrictInt = Field(
        ge=1, le=MAX_OUTPUT_TOKENS_TOTAL)
    per_sample_output_tokens: StrictInt = Field(
        ge=1, le=MAX_OUTPUT_TOKENS_TOTAL)
    elapsed_seconds: StrictFloat | None = None
    elapsed_seconds_scope: str = Field(min_length=1, max_length=MAX_NOTE_CHARS)
    semantics: str = Field(min_length=1, max_length=MAX_NOTE_CHARS)

    @field_validator("deadline_seconds")
    @classmethod
    def _check_deadline(cls, value: float) -> float:
        if not math.isfinite(value) or value <= 0:
            raise ValueError("deadline_seconds must be finite and positive")
        if value > MAX_DEADLINE_SECONDS:
            raise ValueError(
                f"deadline_seconds exceeds the bound {MAX_DEADLINE_SECONDS}")
        return value

    @field_validator("elapsed_seconds")
    @classmethod
    def _check_elapsed(cls, value: float | None) -> float | None:
        if value is None:
            return None
        return _finite_nonneg_float(value, "elapsed_seconds")


class DeclaredIdentities(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    code_version: str
    backend: Literal["gateway", "direct"]
    model: str = Field(min_length=1, max_length=256)
    profile: str | None = None
    purpose: Literal["annotation"]
    template_build_id: str | None = None
    endpoint_fingerprint: str

    @field_validator("code_version", "profile", "template_build_id")
    @classmethod
    def _check_tokens(cls, value: str | None, info: Any) -> str | None:
        if value is None:
            return None
        return _plain_token(value, info.field_name)

    @field_validator("endpoint_fingerprint")
    @classmethod
    def _check_fp(cls, value: str) -> str:
        return _digest_field(value, "endpoint_fingerprint")


class ObservedIdentities(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    # The per-trial declared backend binding exported by the adapters.
    backend_fingerprint: str = Field(
        min_length=1, max_length=MAX_FINGERPRINT_FIELD_CHARS)
    # Unavailable physical identities stay explicit, never guessed.
    runtime_identity: Literal["unverified"]
    model_runtime_identity: Literal["unverified"]
    tokenizer_identity: Literal["unavailable"]


class IdentitiesSection(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    declared: DeclaredIdentities
    observed: ObservedIdentities
    identity_note: str = Field(min_length=1, max_length=MAX_NOTE_CHARS)


class ApiKeyRef(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: Literal["env", "file", "synthetic-canary"]
    name: str | None = Field(default=None, max_length=256)
    name_digest: str | None = None

    @field_validator("name_digest")
    @classmethod
    def _check_fp(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _digest_field(value, "name_digest")

    @model_validator(mode="after")
    def _check_kind_binding(self) -> "ApiKeyRef":
        if self.kind == "env" and not self.name:
            raise ValueError("env credential reference requires a name")
        if self.kind == "file" and self.name_digest is None:
            raise ValueError(
                "file credential reference requires an opaque digest")
        if self.kind == "synthetic-canary" and (self.name or self.name_digest):
            raise ValueError("synthetic canary carries no name or digest")
        return self


class CredentialsSection(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    api_key_ref: ApiKeyRef | None = None
    resolved: StrictBool | None = None
    note: str | None = Field(default=None, max_length=MAX_NOTE_CHARS)


class TransportBoundarySection(BaseModel):
    """Actual transport-boundary call accounting (never dropped)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    attempted_calls: StrictInt = Field(ge=0, le=MAX_DISPATCHES)
    calls_by_kind: dict[str, int]
    responses_received: StrictInt = Field(ge=0, le=MAX_DISPATCHES)
    ambiguous_dispatches: StrictInt = Field(ge=0, le=MAX_DISPATCHES)
    pre_dispatch_failures: StrictInt = Field(ge=0, le=MAX_DISPATCHES)
    remaining_dispatches: StrictInt = Field(ge=0, le=MAX_DISPATCHES)

    @field_validator("calls_by_kind", mode="before")
    @classmethod
    def _check_kinds(cls, value: Any) -> dict[str, int]:
        if not isinstance(value, dict):
            raise ValueError("calls_by_kind must be a mapping")
        checked: dict[str, int] = {}
        for key, count in value.items():
            if not isinstance(key, str) or not key or len(key) > MAX_KIND_KEY_CHARS:
                raise ValueError("kind keys are bounded non-empty strings")
            _raw_nonneg_int(count, f"calls_by_kind[{key}]")
            checked[key] = count
        return checked

    @model_validator(mode="after")
    def _check_relation(self) -> "TransportBoundarySection":
        if sum(self.calls_by_kind.values()) != self.attempted_calls:
            raise ValueError(
                "calls_by_kind must sum to the attempted call count")
        if self.remaining_dispatches + self.attempted_calls > MAX_DISPATCHES:
            raise ValueError(
                "remaining + attempted dispatches exceed the allowance bound")
        return self


class OutputReservation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    total: StrictInt = Field(ge=1, le=MAX_OUTPUT_TOKENS_TOTAL)
    per_sample: StrictInt = Field(ge=1, le=MAX_OUTPUT_TOKENS_TOTAL)
    semantics: str = Field(min_length=1, max_length=MAX_NOTE_CHARS)


class CacheInputConsistency(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    consistent_samples: StrictInt = Field(ge=0, le=MAX_REQUESTS)
    contradictory_samples: StrictInt = Field(ge=0, le=MAX_REQUESTS)
    uncheckable_samples: StrictInt = Field(ge=0, le=MAX_REQUESTS)
    note: str = Field(min_length=1, max_length=MAX_NOTE_CHARS)


class AccountingSection(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    output_reservation: OutputReservation
    cache_input_consistency: CacheInputConsistency


class GatesSection(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    machine_readable_document: str = Field(min_length=1, max_length=512)
    executable_in_this_slice: list[str] = Field(
        default_factory=list, max_length=32)
    real_trials: Literal["NOT_RUN"]
    note: str = Field(min_length=1, max_length=MAX_NOTE_CHARS)

    @field_validator("executable_in_this_slice")
    @classmethod
    def _check_ids(cls, value: list[str]) -> list[str]:
        for gate in value:
            if not isinstance(gate, str) or not gate or len(gate) > 64:
                raise ValueError("gate ids are bounded non-empty strings")
        return value


class TrialEvidence(BaseModel):
    """The complete strict trial result envelope (004-b)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    qualification: Literal["trial"]
    runner: str = Field(min_length=1, max_length=128)
    version: Literal[1]
    trial_id: str
    backend: Literal["gateway", "direct"]
    status: Literal["complete", "incomplete", "not_run"]
    stop_reason: str | None = Field(default=None, max_length=128)
    evidence_class: Literal["MOCK", "CONFIGURED_UNVERIFIED"]
    target_type: Literal["synthetic-owned-fixture", "unverified"]
    target_type_note: str = Field(min_length=1, max_length=MAX_NOTE_CHARS)
    qualification_status: Literal["NOT_QUALIFIED"]
    qualification_note: str = Field(min_length=1, max_length=MAX_NOTE_CHARS)
    workload: WorkloadSection
    budgets: BudgetsSection
    identities: IdentitiesSection
    credentials: CredentialsSection
    requests: list[TrialSample] = Field(
        default_factory=list, max_length=MAX_REQUESTS)
    transport_boundary: TransportBoundarySection
    accounting: AccountingSection
    analysis: AnalysisSection
    gates: GatesSection

    @field_validator("trial_id")
    @classmethod
    def _check_trial_id(cls, value: str) -> str:
        if len(value) > MAX_TRIAL_ID_CHARS:
            raise ValueError(f"trial_id exceeds {MAX_TRIAL_ID_CHARS} chars")
        return _plain_token(value, "trial_id")

    @model_validator(mode="after")
    def _check_trial_relations(self) -> "TrialEvidence":
        requests = self.requests
        # 004-c cross-field bindings: duplicated facts and references
        # are bound to their authoritative section. These checks prove
        # INTERNAL consistency only — never that the declared metadata
        # is true, that a hash proves deployed hardware/model identity,
        # or that imported JSON was executed here.
        if self.backend != self.identities.declared.backend:
            raise ValueError(
                "envelope backend must equal the declared backend")
        expected_target = ("synthetic-owned-fixture"
                           if self.evidence_class == "MOCK"
                           else "unverified")
        if self.target_type != expected_target:
            raise ValueError(
                "target_type must be consistent with the evidence "
                "class (MOCK iff synthetic-owned-fixture; "
                "CONFIGURED_UNVERIFIED iff unverified)")
        # The recorded samples are an EXACT PREFIX of the declared
        # sequence: a complete trial records all of them; an incomplete
        # trial records the leading prefix actually executed (deadline,
        # dispatch exhaustion, preflight refusal or contract violation
        # stop NEW work, never rewrite history).
        if len(requests) > self.workload.samples:
            raise ValueError("requests cannot exceed the declared samples")
        for position, sample in enumerate(requests):
            if sample.ordinal != position:
                raise ValueError("sample ordinals must be 0..n-1 in order")
            expected_phase = ("warmup" if position < self.workload.warmups
                              else "measured")
            if sample.phase != expected_phase:
                raise ValueError(
                    f"sample {position} phase must be {expected_phase}")
            if sample.suffix_index != position % len(self.workload.suffixes):
                raise ValueError(
                    f"sample {position} suffix index must be "
                    "position mod len(suffixes)")
            expected_first = (sample.phase == "measured"
                              and position == self.workload.warmups)
            if sample.first_repetition != expected_first:
                raise ValueError(
                    f"sample {position} first_repetition must be "
                    f"{expected_first}")
            if (sample.backend_fingerprint is not None
                    and sample.backend_fingerprint
                    != self.identities.observed.backend_fingerprint):
                raise ValueError(
                    f"sample {position} backend fingerprint conflicts "
                    "with the observed per-trial backend binding")
        if (self.analysis.warmups.samples_total
                != min(self.workload.warmups, len(requests))):
            raise ValueError(
                "warmup group size must equal the recorded warmups")
        if (self.analysis.measured.samples_total
                != max(0, len(requests) - self.workload.warmups)):
            raise ValueError(
                "measured group size must equal the recorded repetitions")
        # Output reservation metadata is the SAME declared budget used
        # by execution: the per-sample share is the floor even share
        # over the DECLARED scheduled sample count (never the shorter
        # recorded prefix), so an incomplete trial still carries the
        # reservation computed from the full declared sequence.
        if (self.budgets.per_sample_output_tokens
                != (self.budgets.max_output_tokens_total
                    // self.workload.samples)):
            raise ValueError(
                "per-sample output allowance must be the floor even "
                "share of the declared total over the declared "
                "scheduled sample count")
        if (self.accounting.output_reservation.total
                != self.budgets.max_output_tokens_total):
            raise ValueError(
                "output reservation total must equal the declared "
                "max_output_tokens_total budget")
        if (self.accounting.output_reservation.per_sample
                != self.budgets.per_sample_output_tokens):
            raise ValueError(
                "output reservation per-sample must equal the declared "
                "per-sample output budget")
        derived = derive_cache_input_consistency_counts(
            [sample.model_dump() for sample in requests])
        declared = self.accounting.cache_input_consistency
        if ((declared.consistent_samples,
             declared.contradictory_samples,
             declared.uncheckable_samples) != derived):
            raise ValueError(
                "cache/input consistency counts must equal the pure "
                "derivation from the actually recorded raw usage")
        if self.transport_boundary.remaining_dispatches \
                + self.transport_boundary.attempted_calls \
                != self.budgets.max_dispatches:
            raise ValueError(
                "remaining + attempted dispatches must equal the declared "
                "max_dispatches allowance")
        if self.status == "complete":
            if len(requests) != self.workload.samples:
                raise ValueError(
                    "complete status requires every declared sample")
            if self.stop_reason is not None:
                raise ValueError("complete status carries no stop reason")
        elif self.status == "not_run":
            if self.transport_boundary.attempted_calls != 0:
                raise ValueError(
                    "not_run status requires zero attempted calls")
        elif self.status == "incomplete":
            if self.stop_reason is None:
                raise ValueError("incomplete status requires a stop reason")
            if len(requests) == self.workload.samples:
                raise ValueError(
                    "incomplete status requires an unrecorded tail")
        return self


def validate_trial_evidence(document: dict[str, Any]) -> TrialEvidence:
    """Validate one complete trial result envelope at a boundary.

    Checks the strict shape AND requires the analysis section to equal
    the pure recomputation from the recorded samples (the analysis is a
    pure function of its observations; a forged or drifted analysis is
    a contract violation). Raises ``pydantic.ValidationError`` with
    field locations on any violation.

    004-c (004B-F01): the recomputation's call accounting is driven by
    the ACTUAL transport-boundary ledger
    (``transport_boundary.calls_by_kind``), never by the analysis's
    own copy of the call counts — the analysis section is checked
    against the ledger, and an analysis call count different from the
    ledger is refused (adapter cycles can differ legitimately; they
    never replace actual transport attempts).
    """
    from .analysis import analyze_trial

    model = TrialEvidence.model_validate(document)
    expected = analyze_trial(
        [sample.model_dump() for sample in model.requests],
        calls_by_kind=dict(model.transport_boundary.calls_by_kind),
        evidence_class=model.evidence_class,
    )
    actual = model.analysis.model_dump()
    if actual != expected:
        raise ValueError(
            "analysis section is not the pure recomputation from the "
            "recorded samples (strict result contract violation)")
    return model
