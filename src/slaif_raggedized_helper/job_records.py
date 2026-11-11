"""Versioned, bounded data-only job and attempt contracts; no execution or storage."""

from __future__ import annotations

import json
import re
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictInt,
    ValidationError,
    field_validator,
    model_validator,
)

from .schema import fingerprint

MAX_BYTES = 65536
MAX_NODES = 4096
MAX_STRING = 256
_DIGEST = re.compile(r"sha256:[0-9a-f]{64}\Z")
_OPAQUE = re.compile(r"[A-Za-z0-9_-]{1,64}\Z")
_CODE = re.compile(r"[A-Z][A-Z0-9_]{0,63}\Z")


class RecordError(ValueError):
    """Input-free refusal at public admission boundaries."""


class Record(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    @field_validator("version", mode="before", check_fields=False)
    @classmethod
    def strict_version(cls, value: object) -> object:
        if type(value) is not int:
            raise ValueError("invalid version")
        return value


class InputRef(Record):
    kind: Literal["source_revision", "artifact"]
    ref: str
    fingerprint: str

    @field_validator("ref", "fingerprint")
    @classmethod
    def digest(cls, value: str) -> str:
        if not _DIGEST.fullmatch(value):
            raise ValueError("invalid digest")
        return value


class Configuration(Record):
    policy: str
    model: str
    prompt: str
    encoder: str
    runtime: str | None

    @field_validator("policy", "model", "prompt", "encoder", "runtime")
    @classmethod
    def digests(cls, value: str | None) -> str | None:
        if value is not None and not _DIGEST.fullmatch(value):
            raise ValueError("invalid digest")
        return value


class JobSpec(Record):
    version: Literal[1]
    kind: Literal["extraction", "chunking", "annotation", "embedding", "snapshot"]
    purpose: Literal["prepare", "evaluate"]
    inputs: tuple[InputRef, ...] = Field(min_length=1, max_length=128)
    configuration: Configuration

    @model_validator(mode="after")
    def unique_inputs(self) -> JobSpec:
        if len(set((x.kind, x.ref) for x in self.inputs)) != len(self.inputs):
            raise ValueError("duplicate input")
        return self

    @property
    def job_id(self) -> str:
        # Input order is meaningful: it can express ordered spans/artifacts.
        return fingerprint({"domain": "job-spec", **self.model_dump(mode="json")})


Status = Literal[
    "PENDING",
    "CLAIMED",
    "RUNNING",
    "COMPLETE",
    "RETRYABLE_FAILED",
    "UNKNOWN_COMPLETION",
    "REJECTED",
    "FAILED",
    "CANCELLED",
]
Outcome = Literal[
    "COMPLETE", "RETRYABLE_FAILED", "UNKNOWN_COMPLETION", "REJECTED", "FAILED", "CANCELLED"
]


class OutputRef(Record):
    ref: str
    fingerprint: str
    availability: Literal["unverified", "missing", "verified"]

    _digests = field_validator("ref", "fingerprint")(InputRef.digest.__func__)


class Attempt(Record):
    version: Literal[1]
    job_id: str
    attempt_id: str
    request_id: str | None
    outcome: Outcome
    started_ms: StrictInt = Field(ge=0, le=2**63 - 1)
    ended_ms: StrictInt = Field(ge=0, le=2**63 - 1)
    input_tokens: StrictInt | None = Field(ge=0, le=2**63 - 1)
    output_tokens: StrictInt | None = Field(ge=0, le=2**63 - 1)
    diagnostic_code: str | None
    output: OutputRef | None

    @field_validator("job_id")
    @classmethod
    def job_digest(cls, value: str) -> str:
        return InputRef.digest(value)

    @field_validator("attempt_id", "request_id")
    @classmethod
    def opaque(cls, value: str | None) -> str | None:
        if value is not None and not _OPAQUE.fullmatch(value):
            raise ValueError("invalid identifier")
        return value

    @field_validator("diagnostic_code")
    @classmethod
    def code(cls, value: str | None) -> str | None:
        if value is not None and not _CODE.fullmatch(value):
            raise ValueError("invalid code")
        return value

    @model_validator(mode="after")
    def consistent(self) -> Attempt:
        if self.ended_ms < self.started_ms or (
            self.output is not None and self.outcome != "COMPLETE"
        ):
            raise ValueError("inconsistent attempt")
        return self


class JobState(Record):
    version: Literal[1]
    job_id: str
    status: Status
    attempt_id: str | None
    owner_id: str | None
    updated_ms: StrictInt = Field(ge=0, le=2**63 - 1)
    output: OutputRef | None

    _job_digest = field_validator("job_id")(Attempt.job_digest.__func__)
    _opaque = field_validator("attempt_id", "owner_id")(Attempt.opaque.__func__)

    @model_validator(mode="after")
    def consistent(self) -> JobState:
        if self.status == "PENDING" and (self.owner_id or self.output):
            raise ValueError("inconsistent state")
        if self.status in ("CLAIMED", "RUNNING") and (not self.attempt_id or not self.owner_id):
            raise ValueError("inconsistent state")
        if (
            self.status not in ("PENDING", "CLAIMED", "RUNNING", "CANCELLED")
            and not self.attempt_id
        ):
            raise ValueError("inconsistent state")
        if self.status not in ("CLAIMED", "RUNNING") and self.owner_id is not None:
            raise ValueError("inconsistent state")
        if self.output is not None and self.status != "COMPLETE":
            raise ValueError("inconsistent state")
        return self


_TRANSITIONS = {
    "PENDING": {"CLAIMED", "CANCELLED"},
    "CLAIMED": {"RUNNING", "CANCELLED"},
    "RUNNING": {
        "COMPLETE",
        "RETRYABLE_FAILED",
        "UNKNOWN_COMPLETION",
        "REJECTED",
        "FAILED",
        "CANCELLED",
    },
    "RETRYABLE_FAILED": {"PENDING"},
}


def transition(
    previous: JobState, next_state: JobState, attempt: Attempt | None = None
) -> JobState:
    """Validate a pure transition; never claim ownership or authorize a retry."""
    try:
        previous = admit(JobState, _snapshot(previous))
        next_state = admit(JobState, _snapshot(next_state))
        if next_state.status not in _TRANSITIONS.get(previous.status, set()):
            raise ValueError
        if previous.job_id != next_state.job_id or next_state.updated_ms < previous.updated_ms:
            raise ValueError
        if previous.status == "RETRYABLE_FAILED" and next_state.attempt_id != previous.attempt_id:
            raise ValueError
        if (
            previous.status == "PENDING"
            and next_state.status == "CLAIMED"
            and previous.attempt_id == next_state.attempt_id
        ):
            raise ValueError
        if (
            previous.status in ("CLAIMED", "RUNNING")
            and next_state.attempt_id != previous.attempt_id
        ):
            raise ValueError
        if (
            previous.status == "CLAIMED"
            and next_state.status == "RUNNING"
            and previous.owner_id != next_state.owner_id
        ):
            raise ValueError
        terminal = next_state.status in (
            "COMPLETE",
            "RETRYABLE_FAILED",
            "UNKNOWN_COMPLETION",
            "REJECTED",
            "FAILED",
            "CANCELLED",
        )
        pending_cancel = previous.status == "PENDING" and next_state.status == "CANCELLED"
        if pending_cancel:
            if attempt is not None or next_state.attempt_id != previous.attempt_id:
                raise ValueError
        elif terminal:
            if attempt is None:
                raise ValueError
            attempt = admit(Attempt, _snapshot(attempt))
            if (
                attempt.job_id != next_state.job_id
                or attempt.attempt_id != next_state.attempt_id
                or attempt.outcome != next_state.status
                or attempt.output != next_state.output
                or attempt.ended_ms < previous.updated_ms
                or attempt.ended_ms > next_state.updated_ms
            ):
                raise ValueError
        elif attempt is not None:
            raise ValueError
        return next_state
    except (AttributeError, TypeError, ValueError, ValidationError, RecordError):
        raise RecordError("invalid transition") from None


def _unique(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError
        result[key] = value
    return result


def _bounds(value: object) -> None:
    stack = [value]
    nodes = 0
    while stack:
        item = stack.pop()
        nodes += 1
        if nodes > MAX_NODES:
            raise ValueError
        if type(item) is str:
            if len(item) > MAX_STRING:
                raise ValueError
        elif type(item) is dict:
            if len(item) > 128 or any(type(k) is not str or len(k) > MAX_STRING for k in item):
                raise ValueError
            stack.extend(item.values())
        elif type(item) is list:
            if len(item) > 128:
                raise ValueError
            stack.extend(item)
        elif item is not None and type(item) not in (bool, int, float):
            raise ValueError


def admit(record_type: type[Record], data: object) -> Record:
    """Admit a JSON-shaped mapping or UTF-8 JSON bytes with a fixed safe refusal."""
    try:
        if record_type not in (JobSpec, JobState, Attempt, InputRef, OutputRef, Configuration):
            raise ValueError
        if type(data) is bytes:
            if len(data) > MAX_BYTES:
                raise ValueError
            data = json.loads(
                data.decode("utf-8"),
                object_pairs_hook=_unique,
                parse_constant=lambda _: (_ for _ in ()).throw(ValueError()),
            )
        _bounds(data)
        raw = json.dumps(data, ensure_ascii=True, allow_nan=False, separators=(",", ":")).encode()
        if len(raw) > MAX_BYTES:
            raise ValueError
        # JSON mode supports immutable tuples while maintaining strict scalar validation.
        return record_type.model_validate_json(raw)
    except (ValueError, TypeError, UnicodeError, RecursionError, OverflowError, ValidationError):
        raise RecordError("invalid job record") from None


def _snapshot(value: object) -> object:
    if isinstance(value, Record):
        return {name: _snapshot(getattr(value, name)) for name in type(value).model_fields}
    if type(value) in (tuple, list):
        return [_snapshot(item) for item in value]
    if type(value) is dict:
        return {key: _snapshot(item) for key, item in value.items()}
    return value


def serialize(record: Record) -> bytes:
    """Revalidate even unchecked copies before bounded deterministic serialization."""
    try:
        checked = admit(type(record), _snapshot(record))
        raw = json.dumps(
            checked.model_dump(mode="json"),
            sort_keys=True,
            ensure_ascii=True,
            allow_nan=False,
            separators=(",", ":"),
        ).encode()
        if len(raw) > MAX_BYTES:
            raise ValueError
        return raw
    except (AttributeError, TypeError, ValueError, RecursionError, RecordError):
        raise RecordError("invalid job record") from None
