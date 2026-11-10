"""Bounded explicit generator qualification probes (OAP objective 003,
rounds 003-h/003-i).

The probe is an EXPLICIT opt-in composition command, not a readiness poll
and not part of import, ``--help``, ``doctor`` or default test paths:

- the public CLI subcommand ``raggedized probe --mode gateway|direct`` is
  the only dispatch path, and it requires explicit finite budgets
  (overall wall-time, request/call allowance, total output-token
  allowance) plus an actually configured gateway route or materialized
  offline-diagnostic direct mode;
- one absolute experiment deadline spans the complete experiment: both
  paired requests, native template work and every adapter retry. A
  per-call allowance never resets it; the transport boundary rechecks it
  before every invocation;
- a call/attempt allowance is reserved BEFORE every transport invocation
  (model dispatch, template work, failed connects included). Ambiguous
  dispatched work is conservatively counted as spent and is never
  replayed; a finite budget cannot be bypassed by retries or template
  requests;
- credential references resolve through a bounded, safe file read that
  happens BEFORE any HTTP: regular files only (FIFOs/sockets/devices are
  refused via ``fstat`` of a non-blocking open, never a blocking one),
  bounded bytes actually read, single-line UTF-8 shape validation and a
  fixed typed missing/invalid outcome (no raw exception, no value or
  private path echo);
- the repeated-parent experiment deliberately constructs one constant
  bounded synthetic parent plus explicit deterministic child suffixes
  (phases labeled first-call/second-call — cold state is unknown because
  no cache reset/isolation control is authorized or verified), and
  records fingerprints/lengths, never the raw material;
- response text is recorded twice: the label-qualified phase-identity
  fingerprint and a label-independent content fingerprint, so
  same/different output evidence is comparable without raw output; equal
  outputs never establish truth, caching or quality;
- cache conclusions are preceded by validation of the supported
  accounting relation (reported ``cache_hit_tokens`` must not exceed
  reported ``input_tokens`` when both are present): contradictory
  counters are preserved as raw facts only and yield an unqualified
  ``metrics_invalid`` conclusion; the gateway dialect's reported
  ``input_tokens_details.cached_tokens`` (mapped to
  ``cache_hit_tokens``) is a DISTINCT reported fact from the absent
  evaluated-prefill metrics, which stay null/unavailable;
- evidence binds the declared backend identity: the per-request
  ``GeneratorResult.fingerprint`` (adapter dialect, pinned contract,
  declared model, credential-free endpoint, timeout, capability and,
  for direct, template/limit/slot snapshots) is exported per request and
  in ``identities``; the destination is ``target_type: unverified``
  because the runner cannot classify owned fixture vs live target;
- the evidence document is safe structured JSON: declared (unverified)
  identities, exact dialect, budgets, boundary-level call accounting,
  reported metrics with their measurement boundaries and digest-only
  response checks. It never carries an endpoint URL, authorization
  header or secret value, configured instructions, rendered prompts,
  source items, image material, raw response text or provider error
  bodies, and no private credential file path (file references are
  recorded as an opaque digest). Missing measurements stay null and
  yield unqualified conclusions — never a synthetic zero or a claimed
  cache success.

The probe proves executable bounded tooling and synthetic HTTP
composition; real target/hardware/cache/quality qualification remains
NOT RUN (orders 003-h/003-i live authorization: NONE).
"""

from __future__ import annotations

import math
import os
import stat as _stat
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from ._constraints import PositiveFiniteFloat, PositiveInt
from .config import (
    DirectGenerationConfig,
    GeneratorConfig,
    RaggedizedConfig,
    SecretRef,
)
from .model_clients.direct import (
    APPLY_TEMPLATE_PATH,
    DirectNativeGenerator,
    direct_backend_fingerprint,
    NATIVE_REFERENCE_COMMIT,
)
from .model_clients.gateway import (
    gateway_backend_fingerprint,
    GATEWAY_CONTRACT_COMMIT,
    GatewayGenerator,
)
from .model_clients.transport import (
    GatewayTransport,
    TransportConfigError,
    TransportError,
    TransportTimeoutError,
)
from .schema import (
    Capability,
    CompletionOutcome,
    GeneratorPurpose,
    GeneratorRequest,
    GeneratorResult,
    ModelIdentity,
    TextItem,
    fingerprint,
)

PROBE_NAME = "repeated-parent"
PROBE_VERSION = 1

# One constant bounded synthetic parent and explicit deterministic child
# suffixes (003-h criterion 3). Synthetic fixture material only; no corpus
# content. They are recorded in evidence as fingerprints/lengths only.
PROBE_PARENT = (
    "Synthetic repeated-parent probe fixture, constant bounded parent text. "
    "It carries no corpus material and no instructions; it exists only so "
    "the repeated-parent experiment has a stable, bounded, deterministic "
    "prefix across the two child phases."
)
PROBE_SUFFIX_A = " Child suffix A: first-call phase marker."
PROBE_SUFFIX_B = " Child suffix B: second-call phase marker."

# Base transport calls one request needs BEFORE adapter retries: the
# gateway sends one /v1/responses dispatch; the native adapter sends one
# /apply-template (non-inference template work) plus one /completion
# dispatch.
_MIN_CALLS_GW = 1
_MIN_CALLS_DIRECT = 2

EXIT_COMPLETE = 0
EXIT_NOT_RUN = 1
EXIT_USAGE = 2

# A supported credential file is one bounded single line; the file must
# not exceed this many BYTES (including one optional trailing newline).
# More is invalid input, never a credential to read unboundedly (003-i
# criterion 1).
MAX_CREDENTIAL_FILE_BYTES = 8192

# Fixed reason vocabulary for typed credential resolution outcomes.
SECRET_REASON_ENV_ABSENT = "env_absent_or_empty"
SECRET_REASON_FILE_ABSENT = "file_absent_or_unreadable"
SECRET_REASON_FILE_NOT_REGULAR = "file_not_regular"
SECRET_REASON_FILE_UNREADABLE = "file_unreadable"
SECRET_REASON_FILE_TOO_LONG = "file_too_long"
SECRET_REASON_FILE_NOT_UTF8 = "file_not_utf8"
SECRET_REASON_FILE_NOT_SINGLE_LINE = "file_not_single_line"
SECRET_REASON_FILE_EMPTY = "file_empty"
# The resolved value is used verbatim as the Bearer credential of the
# HTTP Authorization header by every adapter. HTTP field values are
# Latin-1 (RFC 7230) and must not contain control characters; values
# outside that shape would raise a raw UnicodeEncodeError mid-dispatch
# or produce a malformed request whose ambiguity consumes budget.
SECRET_REASON_VALUE_CONTROL = "value_contains_control_character"
SECRET_REASON_VALUE_NOT_LATIN1 = "value_not_latin1"

class ProbeBudgets(BaseModel):
    """Explicit finite probe budgets (validated before any dispatch).

    - ``deadline_seconds``: ONE overall wall-time budget spanning the whole
      experiment (both paired requests, template work and retries);
    - ``max_dispatches``: the total call/attempt allowance reserved before
      every transport invocation (model dispatches, template work and
      failed connects all consume it);
    - ``max_output_tokens_total``: the total output-token allowance across
      the pair. Each request receives the deterministic even half
      (``total // 2``), so the pair's summed allowance never exceeds the
      total and no single request may claim the whole budget.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    deadline_seconds: PositiveFiniteFloat
    max_dispatches: PositiveInt
    max_output_tokens_total: PositiveInt = Field(ge=2)

    @property
    def per_request_output_tokens(self) -> int:
        return self.max_output_tokens_total // 2


@dataclass(frozen=True)
class SecretResolution:
    """Fixed typed outcome of one secret reference resolution (003-i).

    ``status`` is ``resolved``/``missing``/``invalid``; ``reason`` is a
    fixed vocabulary code when not ``resolved``. The raw value is held
    only when resolved, for direct adapter injection, and must never be
    written to evidence, logs, errors or command lines. The repr never
    echoes the value.
    """

    status: Literal["resolved", "missing", "invalid"]
    reason: str | None
    value: str | None

    def __repr__(self) -> str:
        return (f"SecretResolution(status={self.status!r}, "
                f"reason={self.reason!r})")


def _header_value_unsafe_reason(value: str) -> str | None:
    """Fixed reason when a resolved value cannot be a Bearer credential.

    See the ``Authorization`` header-usability rule in
    :func:`resolve_secret_reference` (003-i criterion 1).
    """
    for ch in value:
        cp = ord(ch)
        if cp < 0x20 or cp == 0x7F:
            return SECRET_REASON_VALUE_CONTROL
    if any(ord(ch) > 0xFF for ch in value):
        return SECRET_REASON_VALUE_NOT_LATIN1
    return None


def resolve_secret_reference(ref: SecretRef) -> SecretResolution:
    """Resolve one deliberate safe operator reference, bounded and safe.

    Only ``env`` (environment variable) and ``file`` (single-line secret
    file) references are resolved, matching the configured reference
    kinds (003-i criterion 1):

    - file references are opened NON-BLOCKING and the opened descriptor
      is ``fstat``-checked: FIFOs, sockets and character/block devices
      are refused (``file_not_regular``) without ever blocking on an
      open that needs a writer; a directory is refused the same way;
    - at most ``MAX_CREDENTIAL_FILE_BYTES`` bytes are actually read;
    - the content must be valid UTF-8 and a single line (one optional
      trailing newline, no other line breaks or CR);
    - missing/empty references and malformed content return a fixed
      typed outcome (``missing``/``invalid`` with a fixed reason) —
      never a raw exception — and the value never appears in errors,
      logs or evidence;
    - because the resolved value is used verbatim as the Bearer
      credential of the HTTP ``Authorization`` header, it must be
      header-usable: every code point must be Latin-1 representable and
      no control character (C0 or DEL) may occur. A non-Latin-1 value
      (``value_not_latin1``) or a control/NUL-bearing value
      (``value_contains_control_character``) is refused pre-dispatch as
      a fixed typed invalid outcome instead of a raw
      ``UnicodeEncodeError`` or a malformed request that would consume
      dispatch budget ambiguously.

    The resolved value is for direct adapter injection (the
    ``Authorization`` header) only.
    """
    if ref.kind == "env":
        value = os.environ.get(ref.name)
        if value is None or value == "":
            return SecretResolution("missing", SECRET_REASON_ENV_ABSENT, None)
        unsafe = _header_value_unsafe_reason(value)
        if unsafe is not None:
            return SecretResolution("invalid", unsafe, None)
        return SecretResolution("resolved", None, value)
    if ref.kind == "file":
        flags = os.O_RDONLY | getattr(os, "O_NONBLOCK", 0)
        try:
            fd = os.open(ref.name, flags)
        except IsADirectoryError:
            return SecretResolution("invalid", SECRET_REASON_FILE_NOT_REGULAR,
                                    None)
        except OSError:
            return SecretResolution("missing", SECRET_REASON_FILE_ABSENT, None)
        try:
            mode = os.fstat(fd).st_mode
            if not _stat.S_ISREG(mode):
                # A non-blocking open of a FIFO succeeds even without a
                # writer, so the fstat of the actual opened descriptor
                # is the authoritative special-file check.
                return SecretResolution("invalid",
                                        SECRET_REASON_FILE_NOT_REGULAR, None)
            chunks: list[bytes] = []
            total = 0
            while total <= MAX_CREDENTIAL_FILE_BYTES:
                chunk = os.read(fd, 4096)
                if not chunk:
                    break
                chunks.append(chunk)
                total += len(chunk)
            raw = b"".join(chunks)
        except OSError:
            return SecretResolution("invalid", SECRET_REASON_FILE_UNREADABLE,
                                    None)
        finally:
            os.close(fd)
        if len(raw) > MAX_CREDENTIAL_FILE_BYTES:
            return SecretResolution("invalid", SECRET_REASON_FILE_TOO_LONG,
                                    None)
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            return SecretResolution("invalid", SECRET_REASON_FILE_NOT_UTF8,
                                    None)
        if text.endswith("\n"):
            text = text[:-1]
        if "\n" in text or "\r" in text:
            return SecretResolution("invalid",
                                    SECRET_REASON_FILE_NOT_SINGLE_LINE, None)
        if text == "":
            return SecretResolution("missing", SECRET_REASON_FILE_EMPTY, None)
        unsafe = _header_value_unsafe_reason(text)
        if unsafe is not None:
            return SecretResolution("invalid", unsafe, None)
        return SecretResolution("resolved", None, text)
    # pragma: no cover - pydantic Literal forbids other kinds
    return SecretResolution("invalid", "unsupported_reference_kind", None)


class _BudgetExhausted(TransportConfigError):
    """Safe pre-dispatch probe-budget refusal (fixed vocabulary).

    Raised by the transport boundary when the single experiment deadline
    is exhausted or no call/attempt allowance remains. It is a positively
    pre-dispatch, non-retryable refusal: the adapters map it to a safe
    FAILED result and it never replays a spent or ambiguous call.
    """


class BudgetedTransport:
    """Transport-boundary budget guard wrapping the REAL transport.

    The probe exercises the actual transport boundary: this wrapper
    delegates every call to the real :class:`GatewayTransport` (no mock
    substitution) after reserving budget, so dispatch counts are measured
    where dispatches happen, never estimated from adapter results (the
    native ``GeneratorResult.attempts`` counts template/generation
    cycles, which is NOT an authoritative model-dispatch count).

    Guarantees (003-h criterion 2):

    - the single absolute experiment deadline is rechecked before every
      invocation and passed through (tightened, never extended);
    - one call/attempt allowance is reserved BEFORE every transport
      invocation, including template work and failed connects;
    - ambiguous dispatched work (post-dispatch network failure) is
      counted as spent; only positively pre-dispatch failures are left
      for the adapter's finite retry policy to reuse remaining budget;
    - model dispatches and non-inference template work are counted
      separately, as are known responses, ambiguous dispatches and
      pre-dispatch failures.
    """

    def __init__(
        self,
        inner: GatewayTransport,
        *,
        deadline: float,
        max_dispatches: int,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._inner = inner
        self._deadline = deadline
        self._remaining = int(max_dispatches)
        self._clock = clock
        self.attempted_calls = 0
        self.kind_counts: dict[str, int] = {"model_dispatch": 0, "template_work": 0}
        self.responses_received = 0
        self.ambiguous_dispatches = 0
        self.pre_dispatch_failures = 0

    @property
    def remaining_dispatches(self) -> int:
        return self._remaining

    @property
    def deadline(self) -> float:
        return self._deadline

    @staticmethod
    def _kind(path: str) -> str:
        return "template_work" if path == APPLY_TEMPLATE_PATH else "model_dispatch"

    def _reserve(self) -> None:
        if self._clock() >= self._deadline:
            raise _BudgetExhausted("probe experiment deadline exhausted before dispatch")
        if self._remaining <= 0:
            raise _BudgetExhausted("probe dispatch allowance exhausted before dispatch")
        self._remaining -= 1

    def post_json(self, path: str, body: bytes,
                 *, deadline: float | None = None) -> tuple[int, bytes]:
        self._reserve()
        self.attempted_calls += 1
        self.kind_counts[self._kind(path)] += 1
        effective = self._deadline
        if deadline is not None and deadline < effective:
            effective = deadline
        try:
            result = self._inner.post_json(path, body, deadline=effective)
        except TransportTimeoutError as exc:
            if exc.dispatched:
                self.ambiguous_dispatches += 1
            else:
                self.pre_dispatch_failures += 1
            raise
        except TransportError as exc:
            if exc.dispatched:
                self.ambiguous_dispatches += 1
            else:
                self.pre_dispatch_failures += 1
            raise
        self.responses_received += 1
        return result

    def open_stream(self, path: str, body: bytes, *, deadline: float | None = None):  # type: ignore[override]
        # The bounded probe never streams (it requests no STREAMING
        # capability); if a stream were ever attempted it is a safe
        # pre-dispatch refusal, not an unbudgeted dispatch.
        raise _BudgetExhausted("probe experiment does not open streams")


def _probe_cache_key(parent: str) -> str:
    """Deterministic parent-derived cache key (bounded, no raw material)."""
    digest = fingerprint({"kind": "probe-parent", "text": parent})
    return "probe-" + digest.removeprefix("sha256:")[:24]


def _request_fingerprint(text: str) -> tuple[int, str]:
    return len(text), fingerprint({"kind": "probe-input", "text": text})


def _response_text_fingerprint(label: str, text: str) -> str:
    """Label-qualified response fingerprint: the PHASE IDENTITY digest.

    The label is part of the payload on purpose: it keeps phase
    identities separate (003-i criterion 2). The same text under a
    different label produces a different fingerprint here; use
    :func:`_content_fingerprint` for label-independent comparison.
    """
    return fingerprint({"kind": "probe-response-text", "label": label, "text": text})


def _content_fingerprint(text: str) -> str:
    """Label-independent response content fingerprint (003-i criterion 2).

    Identical terminal text in different phases produces the same
    fingerprint, so same/different output evidence is comparable without
    raw output. It is not a semantic, truth or quality claim.
    """
    return fingerprint({"kind": "probe-response-content", "text": text})


def _expected_check(label: str, text: str | None,
                    expected_digests: dict[str, str] | None) -> str | None:
    """Available exact expected-output check (digest equality only).

    Returns ``match``/``mismatch`` when an operator-supplied expected
    digest exists and terminal text is present, ``not_provided`` when the
    check is available (terminal text) but no expectation was supplied,
    and ``None`` when there is no terminal text to compare. An equal
    digest does not establish truth (003-h criterion 5).
    """
    if text is None:
        return None
    provided = (expected_digests or {}).get(label)
    if provided is None:
        return "not_provided"
    return "match" if _response_text_fingerprint(label, text) == provided else "mismatch"


def _usage_dict(result: GeneratorResult) -> dict[str, int | None]:
    usage = result.usage
    return {
        "input_tokens": usage.input_tokens if usage else None,
        "output_tokens": usage.output_tokens if usage else None,
        "prefill_tokens": usage.prefill_tokens if usage else None,
        "cache_hit_tokens": usage.cache_hit_tokens if usage else None,
    }


def _timings_dict(result: GeneratorResult) -> dict[str, float | None]:
    timings = result.timings
    return {
        "ttft_seconds": timings.ttft_seconds if timings else None,
        "prefill_seconds": timings.prefill_seconds if timings else None,
        "decode_seconds": timings.decode_seconds if timings else None,
        "total_seconds": timings.total_seconds if timings else None,
    }


def _build_probe_request(
    *,
    label: str,
    input_text: str,
    model_name: str,
    cache_control_used: bool,
    cache_key: str | None,
    per_request_output_tokens: int,
    deadline_seconds: float,
) -> GeneratorRequest:
    required: set[Capability] = set()
    declared: set[Capability] = {Capability.TEXT}
    if cache_control_used:
        required.add(Capability.PROMPT_CACHING)
        declared.add(Capability.PROMPT_CACHING)
    return GeneratorRequest(
        request_id=f"probe-{label}",
        purpose=GeneratorPurpose.ANNOTATION,
        items=[TextItem(text=input_text)],
        model=ModelIdentity(name=model_name, declared_capabilities=frozenset(declared)),
        required_capabilities=frozenset(required),
        max_output_tokens=per_request_output_tokens,
        deadline_seconds=deadline_seconds,
        prompt_cache_key=cache_key if cache_control_used else None,
    )


def _mode_not_configured(mode: str, message: str) -> tuple[int, dict[str, Any]]:
    return EXIT_USAGE, {
        "probe": PROBE_NAME,
        "version": PROBE_VERSION,
        "mode": mode,
        "status": "error",
        "error": "MODE_NOT_CONFIGURED",
        "message": message,
    }


def _config_error(message: str) -> tuple[int, dict[str, Any]]:
    return EXIT_USAGE, {
        "probe": PROBE_NAME,
        "version": PROBE_VERSION,
        "status": "error",
        "error": "CONFIG_INVALID",
        "message": message,
    }


def _direct_materialization_gap(direct: DirectGenerationConfig) -> str | None:
    """First unmet offline-diagnostic materialization gate (safe message)."""
    if direct.mode != "offline_diagnostic":
        return "direct_generation.mode is not offline_diagnostic"
    if direct.destination is None:
        return "direct_generation.destination is missing"
    if direct.trusted_policy != "private_trusted":
        return "direct_generation.trusted_policy is not private_trusted"
    if direct.model is None:
        return "direct_generation.model identity is missing"
    if direct.template_qualification is None:
        return "direct_generation.template_qualification record is missing"
    if direct.max_output_tokens is None or direct.deadline_seconds is None:
        return "direct_generation explicit finite operator limits are missing"
    return None


def _cache_evidence(
    control_used: bool,
    records: dict[str, dict[str, Any] | None],
) -> dict[str, Any]:
    """Reported-metric-only cache conclusion (never wall-time proof).

    Before any qualification conclusion the supported accounting
    relation is validated for each phase (003-i criterion 3): the pinned
    gateway (f2df0e82) validates ``cached + cache_write <= input_tokens``
    on its own reported usage; the probe observes only the cached
    counter, so the checkable supported relation is
    ``cache_hit_tokens <= input_tokens`` when both are reported.
    Contradictory reported counters are preserved as RAW FACTS only and
    yield the unqualified ``metrics_invalid`` conclusion; a counter
    whose relation cannot be checked (input missing) stays explicitly
    unqualified (``metrics_unvalidated``). Missing counters stay
    null/unavailable (``metrics_unavailable``).
    """
    rec_a = records.get("a")
    rec_b = records.get("b")
    reported = {
        "reported_prefill_tokens": {
            "a": rec_a["usage"]["prefill_tokens"] if rec_a else None,
            "b": rec_b["usage"]["prefill_tokens"] if rec_b else None,
        },
        "reported_cache_hit_tokens": {
            "a": rec_a["usage"]["cache_hit_tokens"] if rec_a else None,
            "b": rec_b["usage"]["cache_hit_tokens"] if rec_b else None,
        },
        "reported_input_tokens": {
            "a": rec_a["usage"]["input_tokens"] if rec_a else None,
            "b": rec_b["usage"]["input_tokens"] if rec_b else None,
        },
        "wall_seconds": {
            "a": rec_a["wall_seconds"] if rec_a else None,
            "b": rec_b["wall_seconds"] if rec_b else None,
        },
    }

    def _validity(label: str) -> str:
        rec = records.get(label)
        if rec is None:
            return "not_run"
        cache_hit = rec["usage"]["cache_hit_tokens"]
        input_tokens = rec["usage"]["input_tokens"]
        if cache_hit is None:
            return "unreported"
        if input_tokens is None:
            return "uncheckable:input_tokens_missing"
        if cache_hit > input_tokens:
            return "invalid:cache_hit_exceeds_input"
        return "valid"

    validity = {"a": _validity("a"), "b": _validity("b")}
    if not control_used:
        conclusion = "no_cache_control"
    elif rec_b is None:
        conclusion = "not_run"
    elif validity["b"].startswith("invalid"):
        # A contradictory reported counter is a raw fact only; it can
        # never qualify cache or work reduction.
        conclusion = "metrics_invalid"
    elif rec_b["usage"]["cache_hit_tokens"] is None:
        # Missing/invalid measurements yield an unqualified conclusion;
        # submitted input tokens or faster wall time cannot substitute
        # for reported evaluated work.
        conclusion = "metrics_unavailable"
    elif validity["b"].startswith("uncheckable"):
        # The supported relation cannot be validated with the reported
        # counters: the measurement stays explicitly unqualified.
        conclusion = "metrics_unvalidated"
    elif rec_b["usage"]["cache_hit_tokens"] == 0:
        conclusion = "no_cache_hit_reported"
    else:
        conclusion = "cache_hit_reported"
    return {
        **reported,
        "accounting_relation": (
            "cache_hit_tokens <= input_tokens when both are reported "
            "(the pinned gateway f2df0e82 validates cached + cache_write "
            "<= input_tokens on its own reported usage; the probe "
            "observes only the cached counter)"
        ),
        "accounting_validity": validity,
        "wall_note": (
            "probe-level wall time around each request; it is caller time, "
            "not evaluated model work and never cache proof"
        ),
        "conclusion": conclusion,
    }


def run_repeated_parent_probe(
    config: RaggedizedConfig,
    mode: Literal["gateway", "direct"],
    budgets: ProbeBudgets,
    *,
    expected_output_digests: dict[str, str] | None = None,
    clock: Callable[[], float] | None = None,
    inner_transport: GatewayTransport | None = None,
) -> tuple[int, dict[str, Any]]:
    """Run the bounded repeated-parent probe for one explicitly configured
    mode. Returns ``(exit_code, evidence_document)``.

    Exit codes: ``0`` complete (both paired requests resolved), ``1``
    not-run/incomplete (finite budget or adapter preflight stop), ``2``
    usage/config error (invalid config, mode not actually configured,
    credential reference absent or invalid) — always with zero
    dispatches.

    ``inner_transport`` is a test seam only: production (the CLI) always
    passes ``None`` and the real transport is built from the configured
    route/destination. The budget boundary always wraps the inner
    transport regardless of its origin.
    """
    if not (isinstance(budgets.deadline_seconds, float)
            and math.isfinite(budgets.deadline_seconds)):
        return EXIT_USAGE, {"probe": PROBE_NAME, "version": PROBE_VERSION,
                            "status": "error", "error": "INVALID_BUDGET",
                            "message": "budgets must be finite and strictly positive"}
    _clock = clock if clock is not None else time.monotonic

    # ---- mode configuration (before any transport is built) -----------
    if mode == "gateway":
        generator: GeneratorConfig = config.generator
        route = generator.route
        if route is None:
            return _mode_not_configured(
                mode, "generator.route is not configured (no gateway route)")
        api_key: str | None = None
        credential_ref_evidence: dict[str, str] | None = None
        if generator.api_key_ref is not None:
            ref = config.secrets[generator.api_key_ref]
            # Evidence retains the configured reference without
            # exporting the value or a private file path (003-i
            # criterion 1): env names are plain tokens and stay as-is;
            # file references are recorded as an opaque digest of the
            # path (stable per path, never the path itself).
            if ref.kind == "env":
                credential_ref_evidence = {"kind": "env", "name": ref.name}
            else:
                credential_ref_evidence = {
                    "kind": "file",
                    "name_digest": fingerprint(
                        {"kind": "probe-credential-file-ref",
                         "name": ref.name}),
                }
            resolution = resolve_secret_reference(ref)
            if resolution.status == "missing":
                return EXIT_USAGE, {
                    "probe": PROBE_NAME, "version": PROBE_VERSION,
                    "mode": mode,
                    "status": "error", "error": "CREDENTIAL_ABSENT",
                    "reason": resolution.reason,
                    "message": ("credential reference is not present on this "
                                "host; provision it out-of-band (values never "
                                "in config, command line or evidence)"),
                }
            if resolution.status == "invalid":
                return EXIT_USAGE, {
                    "probe": PROBE_NAME, "version": PROBE_VERSION,
                    "mode": mode,
                    "status": "error", "error": "CREDENTIAL_INVALID",
                    "reason": resolution.reason,
                    "message": ("credential reference is not a supported "
                                "single-line credential file reference "
                                "(" + (resolution.reason or "invalid")
                                + "); values never in config, command line "
                                "or evidence"),
                }
            api_key = resolution.value
        model_name = route.model
        min_calls = _MIN_CALLS_GW
        dialect = f"v1-responses@{GATEWAY_CONTRACT_COMMIT}"
        cache_control_qualified = bool(route.capabilities.prompt_caching)
        base_url = route.base_url
        if inner_transport is None:
            inner_transport = GatewayTransport(
                route.base_url,
                timeout_seconds=route.timeout_seconds,
                api_key=api_key,
            )
    else:
        direct: DirectGenerationConfig = config.direct_generation
        gap = _direct_materialization_gap(direct)
        if gap is not None:
            return _mode_not_configured(mode, gap)
        model_name = direct.model or ""
        min_calls = _MIN_CALLS_DIRECT
        dialect = f"llama-server-native@{NATIVE_REFERENCE_COMMIT}"
        cache_control_qualified = bool(direct.capabilities.cache_prompt_tested)
        base_url = direct.destination.base_url  # type: ignore[union-attr]
        if inner_transport is None:
            inner_transport = GatewayTransport(
                base_url,
                timeout_seconds=direct.deadline_seconds,  # type: ignore[union-attr]
                endpoint_contract="native",
            )

    # ---- experiment budget --------------------------------------------
    start = _clock()
    experiment_deadline = start + budgets.deadline_seconds
    per_request = budgets.per_request_output_tokens

    # One absolute deadline spans the whole experiment; the per-call
    # allowances of the adapters can only tighten it, never reset it.
    # The REAL transport is wrapped at the transport boundary so dispatch
    # counts are measured where dispatches happen.
    transport = BudgetedTransport(
        inner_transport,
        deadline=experiment_deadline,
        max_dispatches=budgets.max_dispatches,
        clock=_clock,
    )
    if mode == "gateway":
        adapter: GatewayGenerator | DirectNativeGenerator = GatewayGenerator(
            generator, api_key=api_key, transport=transport, clock=_clock,
        )
    else:
        adapter = DirectNativeGenerator(direct, transport=transport, clock=_clock)

    parent_len, parent_fp = _request_fingerprint(PROBE_PARENT)
    a_len, a_fp = _request_fingerprint(PROBE_PARENT + PROBE_SUFFIX_A)
    b_len, b_fp = _request_fingerprint(PROBE_PARENT + PROBE_SUFFIX_B)
    cache_key = _probe_cache_key(PROBE_PARENT) if cache_control_qualified else None

    records: dict[str, dict[str, Any] | None] = {"a": None, "b": None}
    stop_reason: str | None = None

    for label in ("a", "b"):
        now = _clock()
        if now >= experiment_deadline:
            stop_reason = "budget_exhausted_deadline"
            break
        if transport.remaining_dispatches < min_calls:
            stop_reason = "budget_exhausted_dispatches"
            break
        remaining = experiment_deadline - now
        request = _build_probe_request(
            label=label,
            input_text=PROBE_PARENT + (PROBE_SUFFIX_A if label == "a" else PROBE_SUFFIX_B),
            model_name=model_name,
            cache_control_used=cache_control_qualified,
            cache_key=cache_key,
            per_request_output_tokens=per_request,
            deadline_seconds=remaining,
        )
        calls_before = transport.attempted_calls
        wall_start = _clock()
        result: GeneratorResult = adapter.generate(request)
        wall_seconds = _clock() - wall_start
        records[label] = {
            "label": label,
            "outcome": result.outcome.value,
            "error": result.error,
            "adapter_reported_cycles": result.attempts,
            "text_fingerprint": (_response_text_fingerprint(label, result.text)
                                 if result.text is not None else None),
            # Label-independent content fingerprint: comparable across
            # phases without raw output (003-i criterion 2).
            "content_fingerprint": (_content_fingerprint(result.text)
                                    if result.text is not None else None),
            # Exported GeneratorResult.fingerprint: the declared backend
            # binding for this response (003-i criterion 4).
            "backend_fingerprint": result.fingerprint,
            "expected_output_check": _expected_check(
                label, result.text, expected_output_digests),
            "usage": _usage_dict(result),
            "timings": _timings_dict(result),
            "wall_seconds": round(wall_seconds, 9),
        }
        # An adapter preflight refusal consumes no transport call and is
        # deterministic for both phases: stop without extra generation.
        if (transport.attempted_calls == calls_before
                and result.outcome is CompletionOutcome.FAILED):
            stop_reason = "preflight_refusal"
            break

    if records["a"] is not None and records["b"] is not None:
        status = "complete"
        stop_reason = None
    elif transport.attempted_calls == 0:
        # Nothing was ever dispatched (adapter preflight or probe-level
        # budget stop before the first call): the experiment did not run.
        status = "not_run"
    else:
        status = "incomplete"

    elapsed = round(_clock() - start, 9)
    if not math.isfinite(elapsed) or elapsed < 0:
        elapsed = 0.0

    if mode == "gateway":
        declared_backend_fingerprint = gateway_backend_fingerprint(route)
    else:
        declared_backend_fingerprint = direct_backend_fingerprint(direct)

    identities: dict[str, Any] = {
        "dialect": dialect,
        "declared_model": model_name,
        # Opaque digest of the configured endpoint: binds the identity
        # without disclosing the URL (003-h criterion 5).
        "endpoint_fingerprint": fingerprint(
            {"kind": "probe-endpoint", "endpoint": base_url.rstrip("/")}),
        # Full declared backend binding (dialect, pinned contract,
        # declared model, credential-free endpoint, timeout, capability
        # and, for direct, template/limit/slot snapshots) — an endpoint
        # hash alone does not bind all backend controls (003-i
        # criterion 4). The deployed runtime identity is unverified.
        "backend_fingerprint": declared_backend_fingerprint,
        "runtime_identity": "unverified",
    }
    if mode == "gateway":
        identities["route_capabilities"] = dict(sorted(route.capabilities.model_dump().items()))  # type: ignore[union-attr]
        identities["template_identity"] = None
        identities["template_build_id"] = None
        identities["template_method"] = None
        identities["native_capabilities"] = None
        identities["slot_control"] = None
        identities["credentials"] = {
            "api_key_ref": credential_ref_evidence,
            # resolved: the reference was present and resolved for adapter
            # injection; null when no reference is declared (keyless route).
            "resolved": (credential_ref_evidence is not None
                         and api_key is not None),
        }
    else:
        qual = direct.template_qualification
        identities["route_capabilities"] = None
        identities["template_identity"] = direct.chat_template
        identities["template_build_id"] = qual.build_id if qual is not None else None
        identities["template_method"] = qual.method if qual is not None else None
        identities["native_capabilities"] = dict(
            sorted(direct.capabilities.model_dump().items()))
        identities["slot_control"] = {
            "slot_id": direct.slot_id,
            "slot_tested": bool(direct.capabilities.slot_tested),
        }
        identities["credentials"] = {"api_key_ref": None, "resolved": None}

    evidence: dict[str, Any] = {
        "probe": PROBE_NAME,
        "version": PROBE_VERSION,
        "mode": mode,
        "status": status,
        "stop_reason": stop_reason,
        # The runner cannot classify the configured destination as an
        # owned synthetic fixture or a live target; a localhost address
        # or an order live allowance does not establish target type
        # (003-i criterion 4). Explicit synthetic provenance is valid
        # only for owned fixtures under test.
        "target_type": "unverified",
        "target_type_note": (
            "the runner cannot classify the configured destination as an "
            "owned synthetic fixture or a live target; a localhost "
            "address or an order live allowance does not establish "
            "target type; explicit synthetic provenance is valid only "
            "for owned fixtures under test"
        ),
        "model_quality": "not_assessed",
        "budgets": {
            "deadline_seconds": budgets.deadline_seconds,
            "max_dispatches": budgets.max_dispatches,
            "max_output_tokens_total": budgets.max_output_tokens_total,
            "per_request_output_tokens": per_request,
            "elapsed_seconds": elapsed,
            # Honest time boundary (003-i criterion 1): credential
            # resolution and mode preflight happen BEFORE the measured
            # experiment and are excluded from elapsed_seconds.
            "elapsed_seconds_scope": (
                "experiment only: measured after credential resolution "
                "and mode preflight, before the first dispatch"
            ),
        },
        "identities": identities,
        "experiment": {
            "purpose": GeneratorPurpose.ANNOTATION.value,
            "parent_chars": parent_len,
            "parent_fingerprint": parent_fp,
            "suffix_a_chars": len(PROBE_SUFFIX_A),
            "suffix_a_fingerprint": fingerprint(
                {"kind": "probe-suffix", "text": PROBE_SUFFIX_A}),
            "suffix_b_chars": len(PROBE_SUFFIX_B),
            "suffix_b_fingerprint": fingerprint(
                {"kind": "probe-suffix", "text": PROBE_SUFFIX_B}),
            "input_a_chars": a_len,
            "input_a_fingerprint": a_fp,
            "input_b_chars": b_len,
            "input_b_fingerprint": b_fp,
            "phase_labels": ["first-call", "second-call"],
            "cold_state": "unknown",
            "cache_control": {
                "kind": ("prompt_cache_key" if mode == "gateway"
                         else "cache_prompt") if cache_control_qualified else "none",
                "qualified": cache_control_qualified,
                "key_fingerprint": (fingerprint(
                    {"kind": "probe-cache-key", "key": cache_key})
                    if cache_key is not None else None),
            },
        },
        "requests": records,
        # Label-independent same/different output evidence (003-i
        # criterion 2): computed from the per-phase content
        # fingerprints, independent of phase labels and of any semantic
        # claim. Equal outputs never establish truth, caching or
        # quality; a non-terminal or missing phase keeps the comparison
        # unknown (null), never a forced verdict.
        "pair_comparison": {
            "same_output": (
                (records["a"]["content_fingerprint"]
                 == records["b"]["content_fingerprint"])
                if (records["a"] is not None and records["b"] is not None
                    and records["a"]["content_fingerprint"] is not None
                    and records["b"]["content_fingerprint"] is not None)
                else None
            ),
            "note": (
                "label-independent content fingerprints; equal outputs "
                "never establish truth, caching or model quality; a "
                "non-terminal or missing phase keeps the comparison "
                "unknown (null)"
            ),
        },
        "transport_boundary": {
            "attempted_calls": transport.attempted_calls,
            "calls_by_kind": dict(transport.kind_counts),
            "responses_received": transport.responses_received,
            "ambiguous_dispatches": transport.ambiguous_dispatches,
            "pre_dispatch_failures": transport.pre_dispatch_failures,
            "remaining_dispatches": transport.remaining_dispatches,
        },
        "cache_evidence": _cache_evidence(cache_control_qualified, records),
    }
    exit_code = EXIT_COMPLETE if status == "complete" else EXIT_NOT_RUN
    return exit_code, evidence
