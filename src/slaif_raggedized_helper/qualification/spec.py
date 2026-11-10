"""Strict finite trial specification contracts (OAP objective 004-a).

The trial spec is an EXACT, BOUNDED, FROZEN declaration of one finite
repeated-parent qualification trial. It binds declared identities
(code/backend/model/profile/purpose/workload/seed) and total
time/call/output allowances, and it distinguishes three identity classes
that the runner must never conflate:

- DECLARED identity: what the spec/config says (verified pre-dispatch);
- OBSERVED evidence: what the executed adapters/transport actually
  reported (recorded per sample; missing stays null);
- UNAVAILABLE physical identity: runtime/GGUF/tokenizer hardware facts the
  runner cannot measure on this host (recorded as ``unverified`` /
  ``unavailable``, never guessed).

Refusal semantics (004-a criterion 1): unknown settings, unimplemented
workload controls, bool-as-number, nonfinite/negative/invalid values,
inconsistent fingerprints or settings all REFUSE BEFORE DISPATCH with a
fixed safe reason (zero HTTP). The only supported workload is
``repeated-parent`` with concurrency 1 and the annotation purpose;
context/pair/batch/precision/seed-variation controls are not implemented
and are refused with their named prerequisites, never silently claimed.

Spec files are operator-supplied declarations: they can select a workload
and budgets, but they can never carry or prove execution evidence.
"""

from __future__ import annotations

import math
import re
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from ..schema import fingerprint

TRIAL_SPEC_VERSION = 1
SUPPORTED_WORKLOAD = "repeated-parent"

# Explicit finite bounds (no unbounded fields anywhere in the contract).
MAX_TRIAL_ID_CHARS = 100
MAX_CODE_VERSION_CHARS = 64
MAX_DECLARED_MODEL_CHARS = 256
MAX_PROFILE_CHARS = 128
MAX_TEMPLATE_BUILD_ID_CHARS = 128
MAX_PARENT_CHARS = 4096
MAX_SUFFIXES = 8
MAX_SUFFIX_CHARS = 256
MAX_WARMUPS = 16
MAX_REPETITIONS = 64
MAX_SEED = 2**32 - 1
MAX_DEADLINE_SECONDS = 86_400.0
MAX_DISPATCHES = 4_096
MAX_OUTPUT_TOKENS_TOTAL = 1_000_000

_SHA256_DIGEST_RE = re.compile(r"sha256:[0-9a-f]{64}\Z")
# Plain identity token: no whitespace/control, no path shape.
_PLAIN_TOKEN_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z")

# Controls this slice deliberately does NOT implement. Declaring any of
# them is refused with its named prerequisite instead of being silently
# treated as applied (004-a criterion 1).
UNSUPPORTED_CONTROLS: dict[str, str] = {
    "context": ("context controls are not implemented in this slice; "
                "prerequisite 004-b (full gate composition)"),
    "pair": ("pair workloads are not implemented in this slice; "
             "prerequisite 004-b"),
    "batch": ("batch workloads are not implemented in this slice; "
              "prerequisite 004-b"),
    "precision": ("precision controls are not implemented in this slice; "
                  "prerequisite 004-b"),
    "seed_variation": ("seed-driven content variation is not implemented; "
                       "the seed is a bound identity only "
                       "(prerequisite 004-b)"),
    "concurrency_policy": ("concurrency policy is not implemented; only "
                           "concurrency=1 is supported (prerequisite 004-b "
                           "/ ONLINE-02)"),
}


def _plain_token(value: str, field_name: str, max_length: int) -> str:
    if value.strip() != value or not _PLAIN_TOKEN_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a plain non-empty token")
    if len(value) > max_length:
        raise ValueError(f"{field_name} exceeds the bounded length")
    return value


def _not_bool(value: Any, field_name: str) -> int:
    if isinstance(value, bool):
        raise ValueError(f"{field_name} must be an integer, not a boolean")
    return value  # type: ignore[return-value]


def _digest(value: str) -> str:
    if _SHA256_DIGEST_RE.fullmatch(value) is None:
        raise ValueError("must be a sha256:<64 lowercase hex> digest")
    return value


def trial_workload_fingerprint(
    *,
    parent: str,
    suffixes: list[str],
    seed: int,
    warmups: int,
    repetitions: int,
) -> str:
    """Canonical digest of the EXACT declared workload (004-a criterion 1).

    The runner recomputes this from the admitted spec before any dispatch
    and refuses on a mismatch with the declared ``workload_fingerprint``:
    an inconsistent fingerprint is a refused trial, never a re-bind.
    """
    return fingerprint(
        {
            "kind": "trial-workload",
            "version": TRIAL_SPEC_VERSION,
            "workload": SUPPORTED_WORKLOAD,
            "parent": parent,
            "suffixes": list(suffixes),
            "seed": seed,
            "warmups": warmups,
            "repetitions": repetitions,
            "concurrency": 1,
        }
    )


class TrialBudgets(BaseModel):
    """Explicit finite trial budgets (validated before any dispatch).

    - ``deadline_seconds``: ONE absolute wall-time budget spanning the
      WHOLE trial: every warmup, every repetition, every adapter retry,
      every template and model call. It is never reset per sample;
    - ``max_dispatches``: ONE shared call/attempt admission allowance
      reserved before every real transport invocation (model dispatches,
      template work and failed connects all consume it). It is never
      reset per sample;
    - ``max_output_tokens_total``: the total output-token allowance across
      ALL samples; each sample receives the deterministic even share
      (``total // sample_count``), so the summed per-sample reservation
      never exceeds the total and no single sample may claim the whole
      budget. Observed usage is recorded as reported by the backend;
      unknown usage stays null and is never fabricated.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    deadline_seconds: float
    max_dispatches: int
    max_output_tokens_total: int

    @model_validator(mode="before")
    @classmethod
    def _refuse_bool_numbers(cls, data: Any) -> Any:
        if isinstance(data, dict):
            for field_name in ("deadline_seconds", "max_dispatches",
                               "max_output_tokens_total"):
                if isinstance(data.get(field_name), bool):
                    raise ValueError(
                        f"{field_name} must be a number, not a boolean")
        return data

    @field_validator("deadline_seconds")
    @classmethod
    def _check_deadline(cls, value: Any) -> float:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError("deadline_seconds must be a finite positive number")
        number = float(value)
        if not math.isfinite(number) or number <= 0:
            raise ValueError("deadline_seconds must be finite and strictly positive")
        if number > MAX_DEADLINE_SECONDS:
            raise ValueError(f"deadline_seconds exceeds the bound {MAX_DEADLINE_SECONDS}")
        return number

    @field_validator("max_dispatches")
    @classmethod
    def _check_dispatches(cls, value: Any) -> int:
        _not_bool(value, "max_dispatches")
        if isinstance(value, int) and (value < 1 or value > MAX_DISPATCHES):
            raise ValueError(f"max_dispatches must be an integer in 1..{MAX_DISPATCHES}")
        return value  # type: ignore[return-value]

    @field_validator("max_output_tokens_total")
    @classmethod
    def _check_output_total(cls, value: Any) -> int:
        _not_bool(value, "max_output_tokens_total")
        if isinstance(value, int) and (
                value < 1 or value > MAX_OUTPUT_TOKENS_TOTAL):
            raise ValueError(
                f"max_output_tokens_total must be an integer in "
                f"1..{MAX_OUTPUT_TOKENS_TOTAL}")
        return value  # type: ignore[return-value]


class TrialSpec(BaseModel):
    """One finite repeated-parent qualification trial declaration.

    Every field is bounded; unknown fields are refused (and the known
    unimplemented workload controls are refused with their named
    prerequisite); the spec is frozen after validation.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    spec_version: Literal[1]
    # Plain trial identity token (bounded; part of request IDs, so
    # request_id = trial-{trial_id}-{ordinal} stays within 128 chars).
    trial_id: str
    workload: str
    purpose: str
    # The constant bounded synthetic parent and the explicit deterministic
    # child suffixes. Sequence assignment is ordinal % len(suffixes).
    parent: str
    suffixes: list[str]
    # Bound identity only: bound into the workload fingerprint; no
    # seed-driven variation is implemented (prerequisite 004-b).
    seed: int
    warmups: int
    repetitions: int
    # Only 1 is supported in this slice; any other value refuses with the
    # named prerequisite (004-b / ONLINE-02), never a silent claim.
    concurrency: int
    # Declared identities (verified pre-dispatch against the executing
    # package and the configured backend).
    code_version: str
    backend: Literal["gateway", "direct"]
    declared_model: str
    # Optional serving profile name; when present it must exist in the
    # configured profiles.
    profile: str | None
    # Direct native trials only: must equal the configured template
    # qualification build_id when both are present.
    template_build_id: str | None
    budgets: TrialBudgets
    # Declared digest of the exact workload; the runner recomputes it and
    # refuses on mismatch before dispatch.
    workload_fingerprint: str

    @model_validator(mode="before")
    @classmethod
    def _refuse_unsupported_controls(cls, data: Any) -> Any:
        if isinstance(data, dict):
            for key in data:
                if key in UNSUPPORTED_CONTROLS:
                    raise ValueError(
                        f"unsupported control {key!r}: "
                        f"{UNSUPPORTED_CONTROLS[key]}")
            for field_name in ("seed", "warmups", "repetitions",
                               "concurrency"):
                if isinstance(data.get(field_name), bool):
                    raise ValueError(
                        f"{field_name} must be an integer, not a boolean")
        return data

    @field_validator("trial_id")
    @classmethod
    def _check_trial_id(cls, value: str) -> str:
        return _plain_token(value, "trial_id", MAX_TRIAL_ID_CHARS)

    @field_validator("workload")
    @classmethod
    def _check_workload(cls, value: str) -> str:
        if value != SUPPORTED_WORKLOAD:
            raise ValueError(
                f"workload must be {SUPPORTED_WORKLOAD!r} in this slice; "
                "other workloads (context/pair/batch/precision) are "
                "unimplemented (prerequisite 004-b)")
        return value

    @field_validator("purpose")
    @classmethod
    def _check_purpose(cls, value: str) -> str:
        if value != "annotation":
            raise ValueError(
                "purpose must be 'annotation' in this slice; visual requires "
                "the qualified vision path (prerequisite 016) and answer "
                "requires the online answer path (prerequisite 014)")
        return value

    @field_validator("parent")
    @classmethod
    def _check_parent(cls, value: str) -> str:
        if not value:
            raise ValueError("parent must not be empty")
        if len(value) > MAX_PARENT_CHARS:
            raise ValueError(f"parent exceeds the bound {MAX_PARENT_CHARS} chars")
        return value

    @field_validator("suffixes")
    @classmethod
    def _check_suffixes(cls, value: list[str]) -> list[str]:
        if not value:
            raise ValueError("suffixes must contain at least one entry")
        if len(value) > MAX_SUFFIXES:
            raise ValueError(f"suffixes exceeds the bound {MAX_SUFFIXES} entries")
        for suffix in value:
            if not isinstance(suffix, str) or not suffix:
                raise ValueError("each suffix must be a non-empty string")
            if len(suffix) > MAX_SUFFIX_CHARS:
                raise ValueError(
                    f"each suffix exceeds the bound {MAX_SUFFIX_CHARS} chars")
        return value

    @field_validator("seed")
    @classmethod
    def _check_seed(cls, value: Any) -> int:
        _not_bool(value, "seed")
        if not isinstance(value, int) or value < 0 or value > MAX_SEED:
            raise ValueError(f"seed must be an integer in 0..{MAX_SEED}")
        return value

    @field_validator("warmups")
    @classmethod
    def _check_warmups(cls, value: Any) -> int:
        _not_bool(value, "warmups")
        if not isinstance(value, int) or value < 0 or value > MAX_WARMUPS:
            raise ValueError(f"warmups must be an integer in 0..{MAX_WARMUPS}")
        return value

    @field_validator("repetitions")
    @classmethod
    def _check_repetitions(cls, value: Any) -> int:
        _not_bool(value, "repetitions")
        if not isinstance(value, int) or value < 1 or value > MAX_REPETITIONS:
            raise ValueError(f"repetitions must be an integer in 1..{MAX_REPETITIONS}")
        return value

    @field_validator("concurrency")
    @classmethod
    def _check_concurrency(cls, value: Any) -> int:
        if value != 1:
            raise ValueError(
                "concurrency must be 1 in this slice; concurrency above 1 is "
                "unimplemented (prerequisite 004-b / ONLINE-02)")
        return value

    @field_validator("code_version")
    @classmethod
    def _check_code_version(cls, value: str) -> str:
        return _plain_token(value, "code_version", MAX_CODE_VERSION_CHARS)

    @field_validator("declared_model")
    @classmethod
    def _check_declared_model(cls, value: str) -> str:
        if not value or len(value) > MAX_DECLARED_MODEL_CHARS:
            raise ValueError(
                f"declared_model must be 1..{MAX_DECLARED_MODEL_CHARS} chars")
        return value

    @field_validator("profile")
    @classmethod
    def _check_profile(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _plain_token(value, "profile", MAX_PROFILE_CHARS)

    @field_validator("template_build_id")
    @classmethod
    def _check_template_build_id(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _plain_token(value, "template_build_id", MAX_TEMPLATE_BUILD_ID_CHARS)

    @field_validator("workload_fingerprint")
    @classmethod
    def _check_workload_fingerprint(cls, value: str) -> str:
        return _digest(value)

    @model_validator(mode="after")
    def _check_cross_fields(self) -> "TrialSpec":
        if self.backend == "gateway" and self.template_build_id is not None:
            raise ValueError(
                "template_build_id applies to direct native trials only")
        sample_count = self.warmups + self.repetitions
        if self.budgets.max_output_tokens_total < sample_count:
            raise ValueError(
                "max_output_tokens_total must cover at least one output token "
                f"per sample (samples={sample_count})")
        return self

    @property
    def sample_count(self) -> int:
        return self.warmups + self.repetitions

    @property
    def per_sample_output_tokens(self) -> int:
        """Deterministic even share; the summed reservation never exceeds
        the total allowance (004-a criterion 2)."""
        return self.budgets.max_output_tokens_total // self.sample_count

    @property
    def expected_workload_fingerprint(self) -> str:
        return trial_workload_fingerprint(
            parent=self.parent,
            suffixes=list(self.suffixes),
            seed=self.seed,
            warmups=self.warmups,
            repetitions=self.repetitions,
        )

    def declared_workload_fingerprint_matches(self) -> bool:
        return self.workload_fingerprint == self.expected_workload_fingerprint

    def declared_sequence(self) -> list[tuple[int, str, str, int]]:
        """The exact deterministic dispatch sequence.

        Returns ``(ordinal, phase, input_text, suffix_index)`` tuples;
        ``phase`` is ``warmup`` for the first ``warmups`` samples and
        ``measured`` for the remaining ``repetitions``. First/repeated
        order is this ordinal; physical cold/warm state is UNKNOWN and is
        never inferred from position.
        """
        sequence: list[tuple[int, str, str, int]] = []
        for ordinal in range(self.sample_count):
            phase = "warmup" if ordinal < self.warmups else "measured"
            suffix_index = ordinal % len(self.suffixes)
            sequence.append(
                (ordinal, phase, self.parent + self.suffixes[suffix_index],
                 suffix_index))
        return sequence
