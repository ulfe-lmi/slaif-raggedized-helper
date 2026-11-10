"""Bounded read-only local resource telemetry (OAP objective 004-d).

Strict, finite, VERSIONED observations of THIS caller process on THIS
devhost, composed with the actual finite repeated-parent trials of
objective 004. Everything here is read-only, owned and bounded:

- scope is OWN-PROCESS only: the collector measures the process that
  runs it (CPU user/system time via ``getrusage(RUSAGE_SELF)``, current
  RSS via ``/proc/self/status`` VmRSS, lifetime high-water mark via
  ``ru_maxrss``). No unknown PID/process inspection and no allocator
  attribution. A standalone trial client is NOT the remote model
  process; local devhost measurements never establish the remote
  inference host or an assigned production device/process/model;
- availability is exact: absent stays unavailable/null, a known 0
  remains 0; boolean-as-number, nonfinite, negative and contradictory
  values are refused at the contract boundary;
- the optional ``nvidia-smi`` metadata query uses a FIXED whitelisted
  argv with ``shell=False``, a finite subprocess timeout and actual
  stdout/stderr byte bounds enforced at the pipe boundary (enforced
  WHILE the child produces data, never after unbounded capture); each
  read is bounded by the REMAINING declared allowance plus an explicit
  bounded one-byte lookahead at the cap, and reported byte counts are
  the ACTUAL observed bytes, never the configured cap; only the exact
  owned collector child is ever stopped/killed; missing tool, no GPU,
  permission failure, malformed output, timeout or oversize produce
  exact unavailable/error evidence — never 0 used/full/free, and raw
  stderr/command output is never dumped;
- device-WIDE memory is recorded when queried; per-process/CUDA
  allocated/reserved/worker peaks remain unavailable until actually
  instrumented by an owned worker (supplied worker measurements are
  supplied-unverified). Sampling does not prove ownership/exclusivity,
  real model load, absence of contention/OOM or a true worst-case
  peak;
- the trial observer is a NARROW trusted loop seam: it receives only
  phase/ordinal/deadline/ledger facts (strict :class:`PhaseEvent`),
  never raw prompts/outputs/credentials or arbitrary callbacks
  selected by JSON. Constructing the observer starts NO work; work
  starts only when the ACTUAL single trial deadline is bound;
- the trial's ONE absolute deadline still spans all warmups,
  repetitions, retries, template/model calls AND sampling (no
  extension/reset); the single startup metadata query is clipped to
  the remaining trial AND observer duration, and admission is
  rechecked after the startup query and before EVERY sample/query, so
  no sample is admitted late (and none is labelled t=0 when it is not
  admitted at the series start); on finish/failure/cancellation — on
  EVERY execution exit path, including in-process
  ``KeyboardInterrupt``/``BaseException`` with a surviving caller —
  the observer stops new work and joins within an explicit finite
  cleanup bound; never a detached sampler;
- the existing plain qualification run v1 evidence stays INTACT: the
  opt-in resource shape is an explicit versioned WRAPPER whose
  ``trial`` member is the unchanged v1 document.

Deadline and admission semantics (004-e): if the trial deadline is
already reached at startup, nothing is queried, sampled or started;
explicit bounded cleanup may follow expiry but never authorizes
further collection or model dispatch. The trial runner stops and
finitely joins the owned observer on every execution exit path and
preserves the original exception.

Aggregate accounting semantics (004-e): collection calls, observed
bytes and observed time are enforced BEFORE work, across the whole
observer lifetime (never reset per phase). ``bytes_read`` is the sum
of ACTUAL observed read bytes (honest), while the bounded read cap is
RESERVED for each admitted sample so the aggregate can never exceed
the finite cap and the exported record stays valid at exhaustion
(stop reason ``resource_exhausted``). Startup (t=0) and final
observations and device work are included in their documented
applicable allowances; known 0 stays 0 and unavailable stays null;
collector work never consumes or invents model attempts.

Source binding (004-e): the collector record binds the bounded
collector identity, the code source module and the ACTUAL executing
package version; the Git source revision is explicitly unavailable
(no attestation/signing system, no Git subprocess on import or
default commands). Schema versions refuse booleans and wrong numeric
types.

Library MAX values are finite implementation bounds, NOT production
hard limits and NOT the order's small local execution allowance; the
installed CLI diagnostic is capped at the bounded allowance (5
seconds / 64 samples / at most ONE nvidia-smi metadata query with
timeout <= 1 s and stdout <= 16 KiB / stderr <= 4 KiB).
"""

from __future__ import annotations

import math
import os
import platform
import resource as _resource_module
import select
import shutil
import subprocess
import threading
import time
from typing import Any, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictFloat,
    StrictInt,
    field_validator,
    model_validator,
)

from .. import __version__ as PACKAGE_VERSION
from .spec import (
    MAX_DEADLINE_SECONDS,
    MAX_DISPATCHES,
    MAX_REPETITIONS,
    MAX_WARMUPS,
)

RESOURCE_TELEMETRY_VERSION = 1
RESOURCE_WRAPPER_VERSION = 1

# ---------------------------------------------------------------------------
# finite library bounds (implementation MAX values; the installed CLI
# diagnostic is separately capped at the D0 bounded allowance below)
# ---------------------------------------------------------------------------
MAX_OBSERVATION_DURATION_SECONDS = MAX_DEADLINE_SECONDS  # 86400 s
MAX_SAMPLES = 10_000
MAX_COLLECTION_CALLS = 1_000_000
MAX_COLLECTOR_BYTES = 8 * 1024 * 1024
MAX_DEVICE_QUERIES = 16
MAX_DEVICE_QUERY_TIMEOUT_SECONDS = 5.0
MAX_DEVICE_QUERY_STDOUT_BYTES = 64 * 1024
MAX_DEVICE_QUERY_STDERR_BYTES = 16 * 1024
MAX_DEVICES = 8
MAX_DEVICE_INDEX = 255
MAX_DEVICE_NAME_CHARS = 128
MAX_OBSERVER_INTERVAL_SECONDS = 10.0
MAX_CLEANUP_BOUND_SECONDS = 5.0
MAX_PHASE_EVENTS = MAX_WARMUPS + MAX_REPETITIONS
MAX_NOTE_CHARS = 1024
MAX_PROVENANCE_ENTRIES = 8
# Bounded read chunk for the pipe-boundary collector loop (a READ
# SIZE, not a byte allowance; the remaining declared allowance plus
# one lookahead byte always applies on top of it).
_PIPE_READ_CHUNK_BYTES = 4096

# Bounded collector identity / code-source binding (004-e): fixed,
# safe, non-unique-identifying values; no host identity, no Git
# subprocess, no attestation or signing.
MAX_COLLECTOR_ID_CHARS = 64
MAX_COLLECTOR_SOURCE_CHARS = 128
MAX_CODE_VERSION_CHARS = 32
COLLECTOR_ID = "slaif-raggedized-helper-resource-collector"
COLLECTOR_SOURCE = "slaif_raggedized_helper.qualification.resources"
SOURCE_REVISION_UNAVAILABLE = "unavailable"

# ---------------------------------------------------------------------------
# D0 bounded local observational allowance for the installed CLI
# (own-process diagnosis; at most ONE optional nvidia-smi metadata query)
# ---------------------------------------------------------------------------
DIAGNOSTIC_MAX_DURATION_SECONDS = 5.0
DIAGNOSTIC_MAX_SAMPLES = 64
DIAGNOSTIC_DEFAULT_DURATION_SECONDS = 5.0
DIAGNOSTIC_DEFAULT_SAMPLES = 64
DIAGNOSTIC_GPU_TIMEOUT_SECONDS = 1.0
DIAGNOSTIC_GPU_STDOUT_BYTES = 16 * 1024
DIAGNOSTIC_GPU_STDERR_BYTES = 4 * 1024

OBSERVER_DEFAULT_INTERVAL_SECONDS = 0.25
OBSERVER_DEFAULT_CLEANUP_BOUND_SECONDS = 1.0
_PROC_STATUS_READ_BYTES = 8192

# Fixed whitelisted argv — the ONLY device query shape; no argument or
# command is selectable by config, spec JSON or caller strings.
NVIDIA_SMI_ARGV = (
    "nvidia-smi",
    "--query-gpu=index,name,memory.total,memory.used,memory.free",
    "--format=csv,noheader,nounits",
)

GPU_UNIT = "mib"  # nvidia-smi --format=nounits memory.* units (MiB)

GPU_STATUS_VALUES = ("available", "unavailable", "error")
GPU_UNAVAILABLE_REASONS = ("tool_absent", "no_devices", "query_budget_exhausted")
GPU_ERROR_REASONS = (
    "spawn_failed", "timeout", "stdout_oversize", "stderr_oversize",
    "query_failed", "malformed_output", "contradictory_values",
)
GPU_NOTE = (
    "device-wide memory as queried by the fixed nvidia-smi argv; "
    "per-process/CUDA allocated/reserved and worker peaks are DISTINCT "
    "and remain unavailable until actually instrumented by an owned "
    "worker (supplied worker measurements are supplied-unverified); "
    "sampling does not prove ownership/exclusivity, real model load, "
    "absence of contention/OOM or a true worst-case peak; no allocator "
    "zero is invented"
)

SCOPE_NOTE = (
    "own-process measurement of THIS caller process on THIS devhost; it "
    "is never evidence about a remote inference host or an assigned "
    "production device/process/model; a standalone trial client is not "
    "the remote model process; local devhost measurements never "
    "establish the remote target"
)

LIFETIME_MAX_RSS_NOTE = (
    "ru_maxrss process-lifetime high-water mark: KIBOBYTES on Linux "
    "(converted to bytes); unavailable, not zero, where the platform "
    "unit is not the documented Linux one"
)

CPU_NORMALIZATION_NOTE = (
    "utilization = (ru_utime + ru_stime) / wall_seconds over the "
    "observed interval, disclosed as a ratio: it may exceed 1.0 on "
    "multi-core CPUs and is unavailable (null), never fabricated, when "
    "the interval wall time is missing or zero"
)

PROVENANCE_NOTES = (
    SCOPE_NOTE,
    "peaks are OBSERVED SAMPLE PEAKS over the finite sampled interval, "
    "never true process/device worst-case peaks; missing or zero "
    "intervals are unavailable, not fabricated utilization",
    "phase events are caller stage DECLARATIONS recorded by the trusted "
    "loop observer; they are not owned model-service lifecycle evidence "
    "(prerequisite 015); beginning a trial against an already running "
    "service is not cold model startup",
    GPU_NOTE,
    "the ~2 GiB architecture margin is a DECLARED criterion, not a "
    "measured default or a passing gate",
    "collector identity and code source are bound on the collector "
    "record (collector_id, collector_source, code_version = the "
    "executing package version); the Git source revision is "
    "explicitly unavailable (no attestation, signing or Git "
    "subprocess on import or default commands)",
)

STOP_REASON_VALUES = (
    "not_started", "finished", "stopped", "duration_reached",
    "samples_reached", "deadline_reached", "cleanup_timed_out",
    "resource_exhausted",
)


def _finite_nonneg_float(value: Any, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field_name} must be a finite non-negative number")
    number = float(value)
    if not math.isfinite(number) or number < 0:
        raise ValueError(f"{field_name} must be finite and non-negative")
    return number


def _finite_positive_float(value: Any, field_name: str) -> float:
    number = _finite_nonneg_float(value, field_name)
    if number <= 0:
        raise ValueError(f"{field_name} must be finite and strictly positive")
    return number


def _raw_nonneg_int(value: Any, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field_name} must be an integer, not a boolean")
    if value < 0:
        raise ValueError(f"{field_name} must be non-negative")
    return value


def _optional_finite_nonneg(value: float | None, field_name: str) -> float | None:
    if value is None:
        return None
    return _finite_nonneg_float(value, field_name)


def _optional_nonneg_int(value: int | None, field_name: str) -> int | None:
    if value is None:
        return None
    return _raw_nonneg_int(value, field_name)


class ProcessScope(BaseModel):
    """The exact measurement scope (own process of this devhost)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    scope: Literal["own-process"]
    pid: StrictInt = Field(ge=1)
    platform: str = Field(min_length=1, max_length=32)
    note: str = Field(min_length=1, max_length=MAX_NOTE_CHARS)

    @field_validator("platform")
    @classmethod
    def _check_platform(cls, value: str) -> str:
        if not value.isascii() or any(ch.isspace() for ch in value):
            raise ValueError("platform must be a bounded non-space ASCII token")
        return value


class SampleObservation(BaseModel):
    """One bounded point sample of the own process.

    The cpu fields are the CUMULATIVE own-process ru_utime/ru_stime at
    sample time (honest getrusage values, never deltas); the series'
    final :class:`CpuFacts` carries the INTERVAL deltas over the
    observed window.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    # Monotonic offset (seconds) from the series start.
    t: StrictFloat
    # Cumulative own-process user CPU seconds at sample time.
    cpu_user_seconds: StrictFloat | None
    # Cumulative own-process system CPU seconds at sample time.
    cpu_system_seconds: StrictFloat | None
    # Current sampled RSS (bytes); unavailable stays null.
    rss_bytes: StrictInt | None

    @field_validator("t", "cpu_user_seconds", "cpu_system_seconds")
    @classmethod
    def _finite(cls, value: float | None, info: Any) -> float | None:
        return _optional_finite_nonneg(value, info.field_name)

    @field_validator("rss_bytes")
    @classmethod
    def _rss(cls, value: int | None) -> int | None:
        return _optional_nonneg_int(value, "rss_bytes")


class CpuFacts(BaseModel):
    """Own-process CPU user/system time over the OBSERVED INTERVAL.

    Values are deltas from the baseline taken at series start (the
    process may have consumed CPU before the series began; that
    pre-series time is not attributed to the interval).
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    user_seconds: StrictFloat | None
    system_seconds: StrictFloat | None
    # user + system when BOTH are known, otherwise unavailable.
    total_seconds: StrictFloat | None
    wall_seconds: StrictFloat | None
    # total / wall only when wall is known and > 0; never fabricated.
    utilization: StrictFloat | None
    normalization_note: str = Field(min_length=1, max_length=MAX_NOTE_CHARS)

    @field_validator("user_seconds", "system_seconds", "total_seconds",
                     "wall_seconds", "utilization")
    @classmethod
    def _finite(cls, value: float | None, info: Any) -> float | None:
        return _optional_finite_nonneg(value, info.field_name)

    @model_validator(mode="after")
    def _check_relations(self) -> "CpuFacts":
        if (self.user_seconds is not None) != (self.system_seconds is not None):
            raise ValueError(
                "cpu user and system time must be both known or both "
                "unavailable")
        if self.user_seconds is not None:
            assert self.system_seconds is not None
            expected_total = self.user_seconds + self.system_seconds
            if self.total_seconds is None or self.total_seconds != expected_total:
                raise ValueError(
                    "cpu total must equal user + system when both are known")
        else:
            if self.total_seconds is not None:
                raise ValueError(
                    "cpu total is unavailable when user/system is unavailable")
        if self.total_seconds is not None:
            if self.wall_seconds is None or self.wall_seconds <= 0:
                if self.utilization is not None:
                    raise ValueError(
                        "cpu utilization is unavailable when the interval "
                        "wall time is missing or zero")
            else:
                expected = self.total_seconds / self.wall_seconds
                if self.utilization is None or self.utilization != expected:
                    raise ValueError(
                        "cpu utilization must equal total / wall over the "
                        "observed interval")
        else:
            if self.utilization is not None:
                raise ValueError(
                    "cpu utilization requires a known total")
        return self


class RssFacts(BaseModel):
    """Own-process RSS facts with EXACT unit/provenance documentation."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    # The last CURRENT sampled RSS (bytes); unavailable stays null.
    current_bytes: StrictInt | None
    # Process-LIFETIME high-water mark (bytes); distinct from the
    # sampled current value and from the observed interval peak.
    lifetime_max_bytes: StrictInt | None
    lifetime_max_source: str = Field(min_length=1, max_length=MAX_NOTE_CHARS)
    # PEAK of the recorded interval samples (bytes); distinct from the
    # lifetime high-water mark; unavailable stays null.
    sample_peak_bytes: StrictInt | None

    @field_validator("current_bytes", "lifetime_max_bytes",
                     "sample_peak_bytes")
    @classmethod
    def _nonneg(cls, value: int | None, info: Any) -> int | None:
        return _optional_nonneg_int(value, info.field_name)


class GpuDevice(BaseModel):
    """One queried device identity with device-wide memory facts."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    device_index: StrictInt = Field(ge=0, le=MAX_DEVICE_INDEX)
    device_name: str = Field(min_length=1, max_length=MAX_DEVICE_NAME_CHARS)
    memory_unit: Literal["mib"]
    memory_total: StrictInt = Field(ge=1)
    memory_used: StrictInt = Field(ge=0)
    memory_free: StrictInt = Field(ge=0)

    @field_validator("device_name")
    @classmethod
    def _check_name(cls, value: str) -> str:
        if any(ch.isspace() and ch not in " \t" for ch in value):
            raise ValueError("device_name must not contain control whitespace")
        return value.strip()

    @model_validator(mode="after")
    def _check_ranges(self) -> "GpuDevice":
        if self.memory_used > self.memory_total:
            raise ValueError("device memory used exceeds total (contradiction)")
        if self.memory_free > self.memory_total:
            raise ValueError("device memory free exceeds total (contradiction)")
        return self


class GpuObservation(BaseModel):
    """Exact unavailable/error/available evidence for ONE metadata query."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    status: Literal["available", "unavailable", "error"]
    reason: str | None
    devices: list[GpuDevice] = Field(default_factory=list, max_length=MAX_DEVICES)
    query_wall_seconds: StrictFloat | None
    stdout_bytes: StrictInt | None
    stderr_bytes: StrictInt | None
    note: str = Field(min_length=1, max_length=MAX_NOTE_CHARS)

    @field_validator("query_wall_seconds")
    @classmethod
    def _wall(cls, value: float | None) -> float | None:
        return _optional_finite_nonneg(value, "query_wall_seconds")

    @field_validator("stdout_bytes", "stderr_bytes")
    @classmethod
    def _bytes(cls, value: int | None, info: Any) -> int | None:
        return _optional_nonneg_int(value, info.field_name)

    @field_validator("reason")
    @classmethod
    def _check_reason(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if value not in GPU_UNAVAILABLE_REASONS + GPU_ERROR_REASONS:
            raise ValueError("reason must be one of the fixed vocabulary")
        return value

    @model_validator(mode="after")
    def _check_binding(self) -> "GpuObservation":
        if self.status == "available":
            if self.reason is not None:
                raise ValueError("available gpu observation carries no reason")
            if not self.devices:
                raise ValueError("available gpu observation requires devices")
        else:
            if self.reason is None:
                raise ValueError(
                    "unavailable/error gpu observation requires the exact "
                    "reason")
            if self.devices:
                raise ValueError(
                    "unavailable/error gpu observation carries no devices")
        if self.status == "unavailable" and self.reason not in GPU_UNAVAILABLE_REASONS:
            raise ValueError("unavailable requires an unavailable reason")
        if self.status == "error" and self.reason not in GPU_ERROR_REASONS:
            raise ValueError("error requires an error reason")
        no_facts = self.reason in (
            "tool_absent", "query_budget_exhausted", "spawn_failed", None)
        ran_query = not (no_facts and self.status != "available")
        if self.status == "available" or ran_query:
            for field_name in ("query_wall_seconds", "stdout_bytes",
                               "stderr_bytes"):
                if getattr(self, field_name) is None:
                    raise ValueError(
                        f"{field_name} is required once a query was run")
        else:
            if (self.query_wall_seconds is not None
                    or self.stdout_bytes is not None
                    or self.stderr_bytes is not None):
                raise ValueError(
                    "no-query gpu observation carries no query facts")
        return self


class CollectorAccounting(BaseModel):
    """Collector activity accounting (separate from model dispatches)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    samples: StrictInt = Field(ge=0, le=MAX_SAMPLES)
    collection_calls: StrictInt = Field(ge=0, le=MAX_COLLECTION_CALLS)
    wall_seconds: StrictFloat
    bytes_read: StrictInt = Field(ge=0, le=MAX_COLLECTOR_BYTES)
    device_queries: StrictInt = Field(ge=0, le=MAX_DEVICE_QUERIES)
    device_query_wall_seconds: StrictFloat
    device_query_bytes_read: StrictInt = Field(ge=0)
    stop_reason: str
    note: str = Field(min_length=1, max_length=MAX_NOTE_CHARS)
    # Bounded collector identity / code-source binding (004-e). The
    # values are safe fixed tokens plus the ACTUAL executing package
    # version; the Git source revision is explicitly unavailable.
    collector_id: str = Field(min_length=1, max_length=MAX_COLLECTOR_ID_CHARS)
    collector_source: str = Field(
        min_length=1, max_length=MAX_COLLECTOR_SOURCE_CHARS)
    code_version: str = Field(min_length=1, max_length=MAX_CODE_VERSION_CHARS)
    source_revision: Literal["unavailable"]

    @field_validator("wall_seconds", "device_query_wall_seconds")
    @classmethod
    def _finite(cls, value: float, info: Any) -> float:
        return _finite_nonneg_float(value, info.field_name)

    @field_validator("collector_id", "collector_source", "code_version")
    @classmethod
    def _source_tokens(cls, value: str, info: Any) -> str:
        if not value.isascii() or any(ch.isspace() for ch in value):
            raise ValueError(
                f"{info.field_name} must be a bounded non-space ASCII "
                "token")
        return value

    @field_validator("stop_reason")
    @classmethod
    def _check_stop(cls, value: str) -> str:
        if value not in STOP_REASON_VALUES:
            raise ValueError("stop_reason must be one of the fixed vocabulary")
        return value

    @model_validator(mode="after")
    def _check_counts(self) -> "CollectorAccounting":
        if self.samples > self.collection_calls:
            raise ValueError("samples cannot exceed collection calls")
        return self


class PhaseEvent(BaseModel):
    """Narrow trusted loop facts for the observer.

    Structurally cannot carry raw prompts/outputs/credentials (no text
    or payload fields) and cannot select callbacks (it is data, not a
    callable): phase/ordinal/deadline/ledger facts only.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    phase: Literal["warmup", "measured"]
    ordinal: StrictInt = Field(ge=0, le=MAX_PHASE_EVENTS)
    # Transport-boundary ledger fact at the phase boundary; unknown
    # stays null, never assumed zero.
    attempted_calls: StrictInt | None = Field(ge=0, le=MAX_DISPATCHES)
    elapsed_seconds: StrictFloat

    @field_validator("elapsed_seconds")
    @classmethod
    def _finite(cls, value: float) -> float:
        return _finite_nonneg_float(value, "elapsed_seconds")


class ResourceSeries(BaseModel):
    """One finite versioned observation series (monotonic, bounded)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    scope: ProcessScope
    # Offset (seconds) of the series start within the trial (0 for a
    # standalone diagnostic).
    start_offset_seconds: StrictFloat
    interval_seconds: StrictFloat
    duration_seconds: StrictFloat
    samples: list[SampleObservation] = Field(
        default_factory=list, max_length=MAX_SAMPLES)
    cpu: CpuFacts
    rss: RssFacts

    @field_validator("start_offset_seconds", "interval_seconds",
                     "duration_seconds")
    @classmethod
    def _finite(cls, value: float, info: Any) -> float:
        field_name = info.field_name
        if field_name == "interval_seconds":
            number = _finite_positive_float(value, field_name)
            if number > MAX_OBSERVER_INTERVAL_SECONDS:
                raise ValueError(
                    f"interval_seconds exceeds the bound "
                    f"{MAX_OBSERVER_INTERVAL_SECONDS}")
            return number
        number = _finite_nonneg_float(value, field_name)
        if number > MAX_OBSERVATION_DURATION_SECONDS:
            raise ValueError(
                f"{field_name} exceeds the bound "
                f"{MAX_OBSERVATION_DURATION_SECONDS}")
        return number

    @model_validator(mode="after")
    def _check_series(self) -> "ResourceSeries":
        previous = -1.0
        for sample in self.samples:
            if sample.t < previous:
                raise ValueError("sample times must be monotonic non-decreasing")
            if sample.t > self.duration_seconds:
                raise ValueError("sample time exceeds the observed duration")
            previous = sample.t
        known = [s.rss_bytes for s in self.samples if s.rss_bytes is not None]
        if known:
            if self.rss.sample_peak_bytes != max(known):
                raise ValueError(
                    "rss sample peak must equal the peak of the recorded "
                    "interval samples")
        else:
            if self.rss.sample_peak_bytes is not None:
                raise ValueError(
                    "rss sample peak is unavailable when no sample has a "
                    "known rss")
        if self.cpu.wall_seconds != self.duration_seconds:
            raise ValueError(
                "cpu wall_seconds must equal the observed series duration")
        return self


class ResourceSection(BaseModel):
    """The versioned opt-in resource section bound to one trial."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: Literal["resource-telemetry"]
    version: Literal[1]
    trial_status: Literal["complete", "incomplete", "not_run"]
    series: ResourceSeries
    gpu: GpuObservation | None
    collector: CollectorAccounting
    provenance: list[str] = Field(min_length=1, max_length=MAX_PROVENANCE_ENTRIES)
    # Trusted loop facts only (phase/ordinal/ledger); never text.
    phase_events: list[PhaseEvent] = Field(
        default_factory=list, max_length=MAX_PHASE_EVENTS)

    @field_validator("version", mode="before")
    @classmethod
    def _strict_version(cls, value: Any) -> int:
        if (isinstance(value, bool) or not isinstance(value, int)
                or value != RESOURCE_TELEMETRY_VERSION):
            raise ValueError(
                "version must be the exact integer 1 (booleans and "
                "other numeric types are refused)")
        return value

    @field_validator("provenance")
    @classmethod
    def _check_provenance(cls, value: list[str]) -> list[str]:
        for entry in value:
            if not isinstance(entry, str) or not 1 <= len(entry) <= MAX_NOTE_CHARS:
                raise ValueError("provenance entries are bounded non-empty strings")
        return value

    @model_validator(mode="after")
    def _check_binding(self) -> "ResourceSection":
        if self.collector.samples != len(self.series.samples):
            raise ValueError(
                "collector samples must equal the recorded series samples")
        if self.gpu is not None and self.collector.device_queries < 1:
            raise ValueError("a gpu observation requires at least one query")
        if self.gpu is None and self.collector.device_queries != 0:
            raise ValueError("device queries without an observation are refused")
        return self


class ResourceDiagnostic(BaseModel):
    """The versioned standalone diagnostic document (own process)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    qualification: Literal["resource"]
    kind: Literal["resource-diagnostic"]
    version: Literal[1]
    series: ResourceSeries
    gpu: GpuObservation | None
    collector: CollectorAccounting
    notes: list[str] = Field(min_length=1, max_length=MAX_PROVENANCE_ENTRIES)

    @field_validator("version", mode="before")
    @classmethod
    def _strict_version(cls, value: Any) -> int:
        if (isinstance(value, bool) or not isinstance(value, int)
                or value != RESOURCE_TELEMETRY_VERSION):
            raise ValueError(
                "version must be the exact integer 1 (booleans and "
                "other numeric types are refused)")
        return value

    @field_validator("notes")
    @classmethod
    def _check_notes(cls, value: list[str]) -> list[str]:
        for entry in value:
            if not isinstance(entry, str) or not 1 <= len(entry) <= MAX_NOTE_CHARS:
                raise ValueError("notes are bounded non-empty strings")
        return value

    @model_validator(mode="after")
    def _check_binding(self) -> "ResourceDiagnostic":
        if self.collector.samples != len(self.series.samples):
            raise ValueError("collector samples must equal the recorded samples")
        if self.gpu is not None and self.collector.device_queries < 1:
            raise ValueError("a gpu observation requires at least one query")
        if self.gpu is None and self.collector.device_queries != 0:
            raise ValueError("device queries without an observation are refused")
        return self


# ---------------------------------------------------------------------------
# read-only own-process probes (module-level seams for owned tests)
# ---------------------------------------------------------------------------

# Thread-local observed-byte counter for the CURRENT bounded read. The
# owning observer installs it around its own sample; the ACTUAL
# observed byte count (never the read cap) is what gets charged to the
# aggregate accounting.
_read_accounting = threading.local()


def getrusage_self() -> Any:
    """ru_rusage of the OWN process (the only process inspected)."""
    return _resource_module.getrusage(_resource_module.RUSAGE_SELF)


def read_proc_self_status(limit: int = _PROC_STATUS_READ_BYTES) -> bytes | None:
    """Bounded read of /proc/self/status (own process only); None on any failure."""
    try:
        with open("/proc/self/status", "rb") as handle:
            data = handle.read(limit)
    except OSError:
        return None
    counter = getattr(_read_accounting, "count", None)
    if counter is not None:
        counter[0] += len(data)
    return data


def own_process_cpu() -> tuple[float | None, float | None]:
    """(ru_utime, ru_stime) seconds of the own process; None on invalid."""
    try:
        usage = getrusage_self()
    except (OSError, ValueError, AttributeError):
        return None, None
    user = float(usage.ru_utime)
    system = float(usage.ru_stime)
    if not math.isfinite(user) or user < 0:
        user = None
    if not math.isfinite(system) or system < 0:
        system = None
    return user, system


def own_process_rss_bytes() -> int | None:
    """Current own-process RSS (bytes) from /proc/self/status VmRSS."""
    data = read_proc_self_status()
    if data is None:
        return None
    for line in data.splitlines():
        if not line.startswith(b"VmRSS:"):
            continue
        parts = line.split()
        if len(parts) not in (2, 3):
            return None
        try:
            kibibytes = int(parts[1])
        except ValueError:
            return None
        if len(parts) == 3 and parts[2] != b"kB":
            return None
        if kibibytes < 0:
            return None
        return kibibytes * 1024
    return None


def lifetime_max_rss_bytes() -> int | None:
    """ru_maxrss lifetime high-water mark in BYTES (Linux: KiB converted)."""
    try:
        usage = getrusage_self()
    except (OSError, ValueError, AttributeError):
        return None
    value = int(usage.ru_maxrss)
    if value < 0:
        return None
    if platform.system() == "Linux":
        return value * 1024  # documented Linux unit: KiB
    return None  # unit not the documented Linux one: unavailable


def cpu_facts(user: float | None, system: float | None,
              wall: float | None) -> dict[str, Any]:
    """Consistent CPU facts (total only when both known; ratio disclosed)."""
    total = (user + system) if (user is not None and system is not None) else None
    utilization: float | None = None
    if total is not None and wall is not None and wall > 0:
        utilization = total / wall
    return {
        "user_seconds": user,
        "system_seconds": system,
        "total_seconds": total,
        "wall_seconds": wall,
        "utilization": utilization,
        "normalization_note": CPU_NORMALIZATION_NOTE,
    }


def process_scope() -> dict[str, Any]:
    return {
        "scope": "own-process",
        "pid": os.getpid(),
        "platform": platform.system().lower() or "unknown",
        "note": SCOPE_NOTE,
    }


# ---------------------------------------------------------------------------
# bounded nvidia-smi metadata query (fixed argv; owned child only)
# ---------------------------------------------------------------------------

def _gpu_unavailable(reason: str, *, wall: float | None = None,
                     stdout: int | None = None,
                     stderr: int | None = None) -> dict[str, Any]:
    return {
        "status": "unavailable", "reason": reason, "devices": [],
        "query_wall_seconds": wall, "stdout_bytes": stdout,
        "stderr_bytes": stderr, "note": GPU_NOTE,
    }


def _gpu_error(reason: str, *, wall: float | None = None,
               stdout: int | None = None, stderr: int | None = None) -> dict[str, Any]:
    return {
        "status": "error", "reason": reason, "devices": [],
        "query_wall_seconds": wall, "stdout_bytes": stdout,
        "stderr_bytes": stderr, "note": GPU_NOTE,
    }


def run_gpu_metadata_query(
    *,
    timeout_seconds: float,
    stdout_bytes: int,
    stderr_bytes: int,
    executable: str | None = None,
    env: dict[str, str] | None = None,
    clock=time.monotonic,
) -> dict[str, Any]:
    """ONE bounded nvidia-smi metadata query (fixed whitelisted argv).

    ``shell=False``; the finite timeout and the stdout/stderr byte
    bounds are enforced AT THE PIPE BOUNDARY while the child produces
    data (never after unbounded capture). On timeout/oversize only the
    EXACT owned collector child is terminated/killed. Raw stderr and
    command output are NEVER returned or dumped: only the fixed safe
    reason and byte counts.
    """
    if (isinstance(timeout_seconds, bool)
            or not isinstance(timeout_seconds, (int, float))
            or not math.isfinite(float(timeout_seconds))
            or not 0 < float(timeout_seconds) <= MAX_DEVICE_QUERY_TIMEOUT_SECONDS):
        raise ValueError("timeout_seconds must be finite in (0, MAX bound]")
    if (isinstance(stdout_bytes, bool) or not isinstance(stdout_bytes, int)
            or not 0 < stdout_bytes <= MAX_DEVICE_QUERY_STDOUT_BYTES):
        raise ValueError("stdout_bytes must be in (0, MAX bound]")
    if (isinstance(stderr_bytes, bool) or not isinstance(stderr_bytes, int)
            or not 0 < stderr_bytes <= MAX_DEVICE_QUERY_STDERR_BYTES):
        raise ValueError("stderr_bytes must be in (0, MAX bound]")
    argv0 = executable if executable is not None else shutil.which("nvidia-smi")
    if argv0 is None:
        return _gpu_unavailable("tool_absent")
    argv = [argv0, *NVIDIA_SMI_ARGV[1:]]
    start = clock()
    try:
        process = subprocess.Popen(
            argv, shell=False, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, env=env, stdin=subprocess.DEVNULL)
    except OSError:
        return _gpu_error("spawn_failed")
    wall = None
    stdout_data = b""
    stderr_data = b""
    status: str | None = None
    try:
        stdout_done = False
        stderr_done = False
        deadline = start + timeout_seconds
        while not (stdout_done and stderr_done):
            remaining = deadline - clock()
            if remaining <= 0:
                status = "timeout"
                break
            try:
                readable, _, _ = select.select(
                    [process.stdout, process.stderr], [], [],
                    min(remaining, 0.05))
            except (OSError, ValueError):
                status = "query_failed"
                break
            for stream, done_flag in ((process.stdout, stdout_done),
                                      (process.stderr, stderr_done)):
                if stream not in readable:
                    continue
                is_stdout = stream is process.stdout
                acc = len(stdout_data) if is_stdout else len(stderr_data)
                cap = stdout_bytes if is_stdout else stderr_bytes
                remaining = cap - acc
                # Enforce the REMAINING declared allowance: never read
                # past the cap; AT the cap take the explicit bounded
                # one-byte lookahead that distinguishes exact fit from
                # overflow. Reported counts are the actual observed
                # bytes, never the configured cap.
                read_size = min(_PIPE_READ_CHUNK_BYTES, max(1, remaining))
                try:
                    chunk = os.read(stream.fileno(), read_size)
                except OSError:
                    status = "query_failed"
                    break
                if not chunk:
                    if is_stdout:
                        stdout_done = True
                    else:
                        stderr_done = True
                    continue
                if is_stdout:
                    stdout_data += chunk
                    if len(stdout_data) > stdout_bytes:
                        status = "stdout_oversize"
                else:
                    stderr_data += chunk
                    if len(stderr_data) > stderr_bytes:
                        status = "stderr_oversize"
                if status is not None:
                    break
            if status is not None:
                break
    finally:
        # Stop ONLY the exact owned collector child, bounded.
        for stream in (process.stdout, process.stderr):
            try:
                if stream is not None:
                    stream.close()
            except OSError:
                pass
        if process.poll() is None:
            try:
                process.terminate()
            except OSError:
                pass
            try:
                process.wait(timeout=1.0)
            except subprocess.TimeoutExpired:
                try:
                    process.kill()
                except OSError:
                    pass
                try:
                    process.wait(timeout=1.0)
                except subprocess.TimeoutExpired:
                    pass
        wall = max(0.0, clock() - start)
    wall = round(wall, 9)
    if status == "timeout":
        return _gpu_error("timeout", wall=wall,
                          stdout=len(stdout_data), stderr=len(stderr_data))
    if status == "stdout_oversize":
        return _gpu_error("stdout_oversize", wall=wall,
                          stdout=len(stdout_data), stderr=len(stderr_data))
    if status == "stderr_oversize":
        return _gpu_error("stderr_oversize", wall=wall,
                          stdout=len(stdout_data), stderr=len(stderr_data))
    if status == "query_failed":
        return _gpu_error("query_failed", wall=wall,
                          stdout=len(stdout_data), stderr=len(stderr_data))
    returncode = process.returncode
    if returncode != 0:
        return _gpu_error("query_failed", wall=wall,
                          stdout=len(stdout_data),
                          stderr=len(stderr_data))
    try:
        text = stdout_data.decode("utf-8")
    except UnicodeDecodeError:
        return _gpu_error("malformed_output", wall=wall,
                          stdout=len(stdout_data),
                          stderr=len(stderr_data))
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return _gpu_unavailable("no_devices", wall=wall,
                                stdout=len(stdout_data),
                                stderr=len(stderr_data))
    if len(lines) > MAX_DEVICES:
        return _gpu_error("malformed_output", wall=wall,
                          stdout=len(stdout_data),
                          stderr=len(stderr_data))
    devices: list[dict[str, Any]] = []
    for line in lines:
        parts = [part.strip() for part in line.split(",")]
        if len(parts) != 5:
            return _gpu_error("malformed_output", wall=wall,
                              stdout=len(stdout_data),
                              stderr=len(stderr_data))
        try:
            device_index = int(parts[0])
            memory_total = int(parts[2])
            memory_used = int(parts[3])
            memory_free = int(parts[4])
        except ValueError:
            return _gpu_error("malformed_output", wall=wall,
                              stdout=len(stdout_data),
                              stderr=len(stderr_data))
        device_name = parts[1]
        try:
            device = GpuDevice.model_validate({
                "device_index": device_index,
                "device_name": device_name,
                "memory_unit": GPU_UNIT,
                "memory_total": memory_total,
                "memory_used": memory_used,
                "memory_free": memory_free,
            })
        except ValueError:
            reason = ("contradictory_values"
                      if memory_total > 0
                      and (memory_used > memory_total
                           or memory_free > memory_total)
                      else "malformed_output")
            return _gpu_error(reason, wall=wall,
                              stdout=len(stdout_data),
                              stderr=len(stderr_data))
        devices.append(device.model_dump())
    return {
        "status": "available", "reason": None, "devices": devices,
        "query_wall_seconds": wall, "stdout_bytes": len(stdout_data),
        "stderr_bytes": len(stderr_data), "note": GPU_NOTE,
    }


# ---------------------------------------------------------------------------
# the narrow trusted loop observer
# ---------------------------------------------------------------------------

class TrialResourceObserver:
    """Bounded own-process resource observer for ONE trial.

    Construction starts NO work (no thread, no sample, no query).
    ``start`` begins sampling only after the ACTUAL single trial
    deadline is bound (or, for the standalone diagnostic, with a finite
    duration bound and no deadline). ``record_phase`` accepts only the
    strict :class:`PhaseEvent` facts. ``stop`` is idempotent and joins
    the sampler within an explicit finite cleanup bound; no detached
    sampler survives.
    """

    def __init__(
        self,
        *,
        interval_seconds: float = OBSERVER_DEFAULT_INTERVAL_SECONDS,
        max_duration_seconds: float = MAX_OBSERVATION_DURATION_SECONDS,
        max_samples: int = MAX_SAMPLES,
        gpu_query: bool = False,
        gpu_timeout_seconds: float = DIAGNOSTIC_GPU_TIMEOUT_SECONDS,
        gpu_stdout_bytes: int = DIAGNOSTIC_GPU_STDOUT_BYTES,
        gpu_stderr_bytes: int = DIAGNOSTIC_GPU_STDERR_BYTES,
        gpu_executable: str | None = None,
        gpu_env: dict[str, str] | None = None,
        cleanup_bound_seconds: float = OBSERVER_DEFAULT_CLEANUP_BOUND_SECONDS,
        clock=time.monotonic,
    ) -> None:
        if isinstance(interval_seconds, bool) or not isinstance(
                interval_seconds, (int, float)):
            raise ValueError("interval_seconds must be a number")
        interval = float(interval_seconds)
        if not math.isfinite(interval) or not 0 < interval <= MAX_OBSERVER_INTERVAL_SECONDS:
            raise ValueError(
                f"interval_seconds must be finite in (0, {MAX_OBSERVER_INTERVAL_SECONDS}]")
        duration = float(max_duration_seconds)
        if (isinstance(max_duration_seconds, bool)
                or not math.isfinite(duration)
                or not 0 < duration <= MAX_OBSERVATION_DURATION_SECONDS):
            raise ValueError(
                f"max_duration_seconds must be finite in "
                f"(0, {MAX_OBSERVATION_DURATION_SECONDS}]")
        if isinstance(max_samples, bool) or not isinstance(max_samples, int) \
                or not 1 <= max_samples <= MAX_SAMPLES:
            raise ValueError(
                f"max_samples must be an integer in 1..{MAX_SAMPLES}")
        if isinstance(gpu_query, bool) is False:
            raise ValueError("gpu_query must be a boolean")
        cleanup = float(cleanup_bound_seconds)
        if (isinstance(cleanup_bound_seconds, bool)
                or not math.isfinite(cleanup)
                or not 0 < cleanup <= MAX_CLEANUP_BOUND_SECONDS):
            raise ValueError(
                f"cleanup_bound_seconds must be finite in "
                f"(0, {MAX_CLEANUP_BOUND_SECONDS}]")
        self._interval = interval
        self._max_duration = duration
        self._max_samples = max_samples
        self._gpu_query = gpu_query
        self._gpu_timeout = gpu_timeout_seconds
        self._gpu_stdout_bytes = gpu_stdout_bytes
        self._gpu_stderr_bytes = gpu_stderr_bytes
        self._gpu_executable = gpu_executable
        self._gpu_env = gpu_env
        self._cleanup_bound = cleanup
        self._clock = clock
        # State (all access under self._lock; the sampler thread is the
        # only other accessor).
        self._lock = threading.Lock()
        self._state = "constructed"  # constructed|running|stopped
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._samples: list[dict[str, Any]] = []
        self._phase_events: list[dict[str, Any]] = []
        self._collection_calls = 0
        self._bytes_read = 0
        self._device_queries = 0
        self._device_query_wall = 0.0
        self._device_query_bytes = 0
        self._gpu_observation: dict[str, Any] | None = None
        self._deadline: float | None = None
        self._start_time: float | None = None
        self._baseline_user: float | None = None
        self._baseline_system: float | None = None
        self._stop_reason = "not_started"
        self._thread_stop_reason: str | None = None

    # -- lifecycle ----------------------------------------------------------
    def _stop_locked(self, reason: str) -> None:
        """Terminal stop WITHOUT a sampler thread (caller holds the lock)."""
        self._state = "stopped"
        if self._stop_reason == "not_started":
            self._stop_reason = reason

    def _admission_refusal_locked(self) -> str | None:
        """Aggregate admission check BEFORE any collection work.

        The bounded read cap is RESERVED for the next admitted sample
        so the aggregate can never exceed the finite cap (the exported
        record stays valid at exhaustion); actual observed bytes are
        charged after the read. The caller holds the lock and must set
        the stop reason when this returns a reason.
        """
        if self._collection_calls >= MAX_COLLECTION_CALLS:
            return "resource_exhausted"
        if self._bytes_read + _PROC_STATUS_READ_BYTES > MAX_COLLECTOR_BYTES:
            return "resource_exhausted"
        return None

    def start(self, deadline: float | None = None) -> None:
        """Begin bounded sampling (idempotent refusal after start).

        ``deadline`` is the ACTUAL single trial deadline (monotonic
        absolute) when bound to a trial, or None for the standalone
        duration-bound diagnostic. Work starts here — never earlier.

        When bound to a trial deadline, the single startup metadata
        query (when opted in) is clipped to the remaining trial AND
        observer duration; if the deadline is already reached nothing
        is queried, sampled or started; admission is rechecked after
        the query, so a slow startup query can never admit a late
        first sample or start a sampler past expiry. The standalone
        diagnostic (no deadline) keeps the query's own documented
        finite bound (D0: timeout <= 1 s).
        """
        with self._lock:
            if self._state != "constructed":
                raise ValueError("observer can be started exactly once")
            now = self._clock()
            if deadline is not None:
                if (isinstance(deadline, bool) or not isinstance(
                        deadline, (int, float))
                        or not math.isfinite(float(deadline))):
                    raise ValueError("deadline must be a finite number")
                deadline = float(deadline)
            if deadline is not None and deadline <= now:
                # The trial deadline is already exhausted: nothing is
                # queried, sampled or started, nothing is fabricated.
                self._start_time = now
                self._stop_locked("deadline_reached")
                return
            self._deadline = deadline
            self._start_time = now
            self._baseline_user, self._baseline_system = own_process_cpu()
            # A metadata query (at most one) happens BEFORE the sampler
            # thread starts: finite, bounded, owned child only, with
            # the allowance clipped to the remaining trial AND observer
            # duration (expiry never authorizes further collection).
            if self._gpu_query:
                query_timeout = self._gpu_timeout
                if deadline is not None:
                    # The startup query allowance is clipped to the
                    # remaining trial AND observer duration; expiry
                    # never authorizes the query or work after it.
                    allowance = min(self._max_duration, deadline - now)
                    if allowance <= 0:
                        self._stop_locked("deadline_reached")
                        return
                    query_timeout = min(query_timeout, allowance)
                self._gpu_observation = self._run_one_gpu_query(
                    timeout_seconds=query_timeout)
                # Recheck admission AFTER the startup query: no late
                # first sample, no sampler started past expiry.
                if deadline is not None and self._clock() >= deadline:
                    self._stop_locked("deadline_reached")
                    return
            # t=0 sample admission: aggregate bounds checked before work.
            reason = self._admission_refusal_locked()
            if reason is not None:
                self._stop_locked(reason)
                return
            self._record_sample_locked()  # the t=0 sample (>=1 sample)
            self._state = "running"
            self._stop_event.clear()
            thread = threading.Thread(
                target=self._sampler_loop, name="trial-resource-observer",
                daemon=True)
            self._thread = thread
            thread.start()

    def _run_one_gpu_query(self, timeout_seconds: float) -> dict[str, Any]:
        self._device_queries += 1
        start = self._clock()
        observation = run_gpu_metadata_query(
            timeout_seconds=timeout_seconds,
            stdout_bytes=self._gpu_stdout_bytes,
            stderr_bytes=self._gpu_stderr_bytes,
            executable=self._gpu_executable,
            env=self._gpu_env,
            clock=self._clock,
        )
        wall = max(0.0, self._clock() - start)
        self._device_query_wall = (
            round(self._device_query_wall + wall, 9))
        self._device_query_bytes += (
            (observation.get("stdout_bytes") or 0)
            + (observation.get("stderr_bytes") or 0))
        return observation

    def _record_sample_locked(self) -> None:
        """One bounded own-process sample (caller holds the lock)."""
        now = self._clock()
        assert self._start_time is not None
        _read_accounting.count = [0]
        try:
            user, system = own_process_cpu()
            rss = own_process_rss_bytes()
        finally:
            observed_bytes = _read_accounting.count[0]
            _read_accounting.count = None
        self._collection_calls += 1
        # Actual OBSERVED read bytes (honest), never the read cap.
        self._bytes_read += observed_bytes
        if len(self._samples) >= self._max_samples:
            return
        self._samples.append({
            "t": round(max(0.0, now - self._start_time), 9),
            "cpu_user_seconds": user,
            "cpu_system_seconds": system,
            "rss_bytes": rss,
        })

    def _sampler_loop(self) -> None:
        while not self._stop_event.wait(self._interval):
            with self._lock:
                if self._state != "running":
                    return
                now = self._clock()
                assert self._start_time is not None
                if self._deadline is not None and now >= self._deadline:
                    self._thread_stop_reason = "deadline_reached"
                    return
                if (now - self._start_time) >= self._max_duration:
                    self._thread_stop_reason = "duration_reached"
                    return
                if len(self._samples) >= self._max_samples:
                    self._thread_stop_reason = "samples_reached"
                    return
                reason = self._admission_refusal_locked()
                if reason is not None:
                    self._thread_stop_reason = reason
                    return
                self._record_sample_locked()

    def observe_for(self, seconds: float) -> None:
        """Standalone diagnostic: observe for up to ``seconds``.

        The bounded sampler thread performs the work; this call only
        waits (it cannot extend the sampler's own finite bounds).
        """
        if (isinstance(seconds, bool) or not isinstance(seconds, (int, float))
                or not math.isfinite(float(seconds)) or float(seconds) <= 0):
            raise ValueError("seconds must be a finite positive number")
        self._stop_event.wait(float(seconds))

    def record_phase(self, event: PhaseEvent) -> None:
        """Bind one trusted loop fact (validated; dropped after stop)."""
        if not isinstance(event, PhaseEvent):
            raise TypeError("record_phase accepts only PhaseEvent facts")
        with self._lock:
            if self._state != "running":
                return
            if len(self._phase_events) >= MAX_PHASE_EVENTS:
                return
            self._phase_events.append(event.model_dump())

    def stop(self, reason: str) -> None:
        """Stop new samples and join within the finite cleanup bound."""
        if reason not in STOP_REASON_VALUES:
            raise ValueError("stop reason must be one of the fixed vocabulary")
        with self._lock:
            if self._state == "stopped":
                return
            if self._state == "constructed":
                # Never started: nothing to join, nothing sampled.
                self._state = "stopped"
                if self._stop_reason == "not_started":
                    self._stop_reason = reason
                return
            self._state = "stopped"
            if self._stop_reason in ("not_started",):
                self._stop_reason = reason
            self._stop_event.set()
            thread = self._thread
        if thread is not None:
            thread.join(timeout=self._cleanup_bound)
            with self._lock:
                if thread.is_alive():
                    if self._thread_stop_reason is None:
                        self._stop_reason = "cleanup_timed_out"
                elif self._thread_stop_reason is not None:
                    self._stop_reason = self._thread_stop_reason

    def finish(self, trial_status: str) -> dict[str, Any]:
        """The validated versioned resource section (idempotent stop).

        The single FINAL own-process observation (CPU interval end +
        lifetime high-water read) is collector work: it counts once
        against the documented collection-call allowance; the recorded
        sample count stays the observed series length.
        """
        if trial_status not in ("complete", "incomplete", "not_run"):
            raise ValueError("trial_status must be a trial execution status")
        self.stop("finished")
        final_user, final_system = own_process_cpu()
        with self._lock:
            self._collection_calls += 1
            samples = list(self._samples)
            duration = (
                round(max(0.0, self._clock() - self._start_time), 9)
                if self._start_time is not None else 0.0)
            collection_calls = self._collection_calls
            bytes_read = self._bytes_read
            device_queries = self._device_queries
            device_query_wall = self._device_query_wall
            device_query_bytes = self._device_query_bytes
            gpu_observation = self._gpu_observation
            stop_reason = self._stop_reason
        if (self._baseline_user is not None and self._baseline_system
                is not None and final_user is not None
                and final_system is not None):
            user = max(0.0, final_user - self._baseline_user)
            system = max(0.0, final_system - self._baseline_system)
        else:
            user = None
            system = None
        lifetime = lifetime_max_rss_bytes()
        return {
            "kind": "resource-telemetry",
            "version": RESOURCE_TELEMETRY_VERSION,
            "trial_status": trial_status,
            "series": {
                "scope": process_scope(),
                "start_offset_seconds": 0.0,
                "interval_seconds": self._interval,
                "duration_seconds": duration,
                "samples": samples,
                "cpu": cpu_facts(user, system, duration),
                "rss": {
                    "current_bytes": (
                        samples[-1]["rss_bytes"] if samples else None),
                    "lifetime_max_bytes": lifetime,
                    "lifetime_max_source": LIFETIME_MAX_RSS_NOTE,
                    "sample_peak_bytes": (
                        max((s["rss_bytes"] for s in samples
                             if s["rss_bytes"] is not None), default=None)),
                },
            },
            "gpu": gpu_observation,
            "collector": {
                "samples": len(samples),
                "collection_calls": collection_calls,
                "wall_seconds": duration,
                "bytes_read": bytes_read,
                "device_queries": device_queries,
                "device_query_wall_seconds": device_query_wall,
                "device_query_bytes_read": device_query_bytes,
                "stop_reason": stop_reason,
                "note": (
                    "collector activity accounting; separate from model/"
                    "template dispatches (transport boundary) and from "
                    "output allowances; sampling never extends or resets "
                    "the trial deadline"
                ),
                # Bounded collector identity / code-source binding
                # (004-e): safe fixed tokens plus the ACTUAL executing
                # package version; the Git source revision is explicit
                # unavailable (no attestation, signing or Git
                # subprocess on import or default commands).
                "collector_id": COLLECTOR_ID,
                "collector_source": COLLECTOR_SOURCE,
                "code_version": PACKAGE_VERSION,
                "source_revision": SOURCE_REVISION_UNAVAILABLE,
            },
            "provenance": list(PROVENANCE_NOTES),
            "phase_events": list(self._phase_events),
        }


def validate_resource_section(document: dict[str, Any]) -> ResourceSection:
    section = ResourceSection.model_validate(document)
    return section


def wrap_trial_with_resources(trial_document: dict[str, Any],
                              resources_section: dict[str, Any]) -> dict[str, Any]:
    """The explicit versioned opt-in wrapper around the INTACT v1 trial."""
    return {
        "resource_wrapper": RESOURCE_WRAPPER_VERSION,
        "trial": trial_document,
        "resources": resources_section,
    }


def validate_resource_wrapper(document: Any) -> None:
    """Strict wrapper contract.

    The ``trial`` member must be a valid plain v1 trial evidence
    document (the canonical full strict result contract); the
    ``resources`` member must be the strict versioned section with the
    trial status bound to the trial's own status. Raises
    ``pydantic.ValidationError``/``ValueError`` on any violation.
    """
    from .contracts import validate_trial_evidence

    if not isinstance(document, dict):
        raise ValueError("resource wrapper must be a mapping")
    if set(document) != {"resource_wrapper", "trial", "resources"}:
        raise ValueError(
            "resource wrapper must contain exactly "
            "resource_wrapper/trial/resources")
    wrapper_version = document["resource_wrapper"]
    if isinstance(wrapper_version, bool) or wrapper_version != RESOURCE_WRAPPER_VERSION:
        raise ValueError("resource wrapper version must be 1")
    trial_document = document["trial"]
    validate_trial_evidence(trial_document)
    section = ResourceSection.model_validate(document["resources"])
    if section.trial_status != trial_document.get("status"):
        raise ValueError(
            "resource section trial_status must equal the trial status")
    del section


def run_resource_diagnostic(
    *,
    duration_seconds: float,
    samples: int,
    gpu_query: bool = False,
    gpu_timeout_seconds: float = DIAGNOSTIC_GPU_TIMEOUT_SECONDS,
    gpu_stdout_bytes: int = DIAGNOSTIC_GPU_STDOUT_BYTES,
    gpu_stderr_bytes: int = DIAGNOSTIC_GPU_STDERR_BYTES,
    gpu_executable: str | None = None,
    gpu_env: dict[str, str] | None = None,
    clock=time.monotonic,
) -> tuple[int, dict[str, Any]]:
    """One bounded standalone own-process diagnostic (explicit opt-in).

    Zero model/network work: own-process CPU/RSS sampling only, plus at
    most ONE bounded nvidia-smi metadata query when requested. Capped
    at the D0 bounded allowance (<= 5 s, <= 64 samples). Returns
    ``(exit_code, document)``.
    """
    if (isinstance(duration_seconds, bool)
            or not math.isfinite(float(duration_seconds))
            or not 0 < float(duration_seconds) <= DIAGNOSTIC_MAX_DURATION_SECONDS):
        raise ValueError(
            f"duration_seconds must be finite in "
            f"(0, {DIAGNOSTIC_MAX_DURATION_SECONDS}]")
    if (isinstance(samples, bool) or not isinstance(samples, int)
            or not 1 <= samples <= DIAGNOSTIC_MAX_SAMPLES):
        raise ValueError(
            f"samples must be an integer in 1..{DIAGNOSTIC_MAX_SAMPLES}")
    duration = float(duration_seconds)
    interval = max(0.01, duration / samples)
    observer = TrialResourceObserver(
        interval_seconds=min(interval, MAX_OBSERVER_INTERVAL_SECONDS),
        max_duration_seconds=duration,
        max_samples=samples,
        gpu_query=gpu_query,
        gpu_timeout_seconds=gpu_timeout_seconds,
        gpu_stdout_bytes=gpu_stdout_bytes,
        gpu_stderr_bytes=gpu_stderr_bytes,
        gpu_executable=gpu_executable,
        gpu_env=gpu_env,
        clock=clock,
    )
    observer.start(None)
    observer.observe_for(duration)
    # finish() performs the idempotent stop (finite cleanup bound) and
    # builds the validated section; the diagnostic document projects it.
    resource_section = observer.finish("not_run")
    ResourceSection.model_validate(resource_section)
    document = {
        "qualification": "resource",
        "kind": "resource-diagnostic",
        "version": RESOURCE_TELEMETRY_VERSION,
        "series": resource_section["series"],
        "gpu": resource_section["gpu"],
        "collector": resource_section["collector"],
        "notes": list(PROVENANCE_NOTES),
    }
    ResourceDiagnostic.model_validate(document)
    return 0, document
