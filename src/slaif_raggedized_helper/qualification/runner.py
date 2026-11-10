"""Finite qualification trial runner (OAP objective 004-a).

The runner actually invokes the CURRENT gateway/direct application code
(the real ``GatewayGenerator``/``DirectNativeGenerator`` adapters over the
REAL transport) against the configured target — or, only under the
explicit ``--synthetic`` opt-in, against the owned deterministic loopback
fixture. It is an EXPLICIT opt-in composition command, not a readiness
poll and not part of import, ``--help``, ``doctor``, planning or default
test paths.

Budget semantics (004-a criterion 2):

- ONE absolute trial deadline and ONE shared call/attempt admission
  allowance span ALL warmups, repetitions, adapter retries, template and
  model calls. They are never reset per sample;
- both are enforced at the ACTUAL transport dispatch boundary (the
  trusted shared-budget seam from objective 003, reused, not duplicated):
  the deadline is rechecked and the allowance reserved before every
  transport invocation, including failed connects;
- output reservation: each sample reserves its deterministic even share
  of the total output allowance as the request's ``max_output_tokens``;
  observed usage is recorded exactly as reported — unknown usage stays
  null and is never fabricated;
- deadline/cancellation stops NEW work and retries before dispatch and
  the owned in-flight exchange is closed/joined by the transport's own
  bounded cancellation (cooperative in-flight limit; the upstream model
  process is never killed).

Evidence safety (004-a criterion 3): the document carries fingerprints
of inputs/outputs (never the raw material), declared-vs-observed
identities with unavailable physical identities explicit, per-sample
outcomes/errors/known usage, transport-boundary call accounting and the
deterministic analysis summary. No endpoint URL, credential, prompt,
response text or private path; arbitrary supplied JSON (spec files) can
select a workload but can never prove or carry execution evidence.
"""

from __future__ import annotations

import math
import time
from collections.abc import Callable
from typing import Any

from pydantic import ValidationError

from .. import __version__
from ..config import RaggedizedConfig
from ..model_clients.direct import (
    DirectNativeGenerator,
    direct_backend_fingerprint,
)
from ..model_clients.gateway import (
    GatewayGenerator,
    gateway_backend_fingerprint,
)
from ..model_clients.transport import GatewayTransport
from ..probes import (
    BudgetedTransport,
    _direct_materialization_gap,
    _timings_dict,
    _usage_dict,
    resolve_secret_reference,
)
from ..schema import (
    Capability,
    CompletionOutcome,
    GeneratorPurpose,
    GeneratorRequest,
    ModelIdentity,
    TextItem,
    fingerprint,
)
from .analysis import analyze_trial
from .gates import GATES_DOC_PATH, executable_gate_ids
from .spec import TrialSpec
from .synthetic import FIXTURE_ENDPOINT_IDENTITY, SYNTHETIC_API_KEY, SyntheticTrialServer
from .contracts import TrialSample, validate_trial_evidence

STOP_EVIDENCE_CONTRACT_VIOLATION = "evidence_contract_violation"

RUNNER_NAME = "qualification-trial"
RUNNER_VERSION = 1

EXIT_COMPLETE = 0
EXIT_NOT_RUN = 1
EXIT_USAGE = 2

# Minimum real transport calls one sample needs BEFORE adapter retries:
# the gateway sends one /v1/responses dispatch; the native adapter sends
# one /apply-template (non-inference template work) plus one /completion
# dispatch. Template work consumes the shared allowance like any other
# transport call.
_MIN_CALLS_GATEWAY = 1
_MIN_CALLS_DIRECT = 2


def _refusal_document(trial_id: str, error: str, reasons: list[str],
                      message: str) -> dict[str, Any]:
    return {
        "qualification": "trial",
        "runner": RUNNER_NAME,
        "version": RUNNER_VERSION,
        "trial_id": trial_id,
        "status": "error",
        "error": error,
        "reasons": reasons,
        "message": message,
    }


def preflight_issues(config: RaggedizedConfig,
                     spec: TrialSpec) -> list[str]:
    """All safe pre-dispatch consistency refusals for one spec/config pair.

    Missing required execution inputs and inconsistent fingerprints or
    settings refuse BEFORE ANY DISPATCH (004-a criterion 1). An empty
    list means the trial may be executed (it does not mean it will
    succeed: complete/exit-0 is execution status only).
    """
    issues: list[str] = []
    if spec.code_version != __version__:
        issues.append(
            f"declared code_version {spec.code_version!r} does not match "
            f"the executing package version {__version__!r}")
    if not spec.declared_workload_fingerprint_matches():
        issues.append(
            "declared workload_fingerprint is inconsistent with the exact "
            "declared workload (refused before dispatch; the workload "
            "fingerprint is recomputed, never re-bound)")
    if spec.profile is not None:
        profile_names = {profile.name for profile in config.profiles}
        if spec.profile not in profile_names:
            issues.append(
                f"declared profile {spec.profile!r} is not a configured "
                "profile name")
    per_sample = spec.per_sample_output_tokens
    if spec.backend == "gateway":
        route = config.generator.route
        if route is None:
            issues.append(
                "generator.route is not configured (no gateway route; the "
                "configured target is a missing prerequisite)")
        else:
            if route.model != spec.declared_model:
                issues.append(
                    f"declared_model {spec.declared_model!r} does not match "
                    f"the configured route model {route.model!r}")
            if per_sample > config.generator.output_reserve_tokens:
                issues.append(
                    f"per-sample output allowance {per_sample} exceeds the "
                    f"configured output_reserve_tokens "
                    f"{config.generator.output_reserve_tokens}")
    else:
        direct = config.direct_generation
        gap = _direct_materialization_gap(direct)
        if gap is not None:
            issues.append("direct_generation is not materialized: " + gap)
        else:
            if direct.model != spec.declared_model:
                issues.append(
                    f"declared_model {spec.declared_model!r} does not match "
                    f"the configured native model identity {direct.model!r}")
            if (spec.template_build_id is not None
                    and direct.template_qualification is not None
                    and spec.template_build_id
                    != direct.template_qualification.build_id):
                issues.append(
                    "declared template_build_id does not match the "
                    "configured template qualification build_id")
            if per_sample > direct.max_output_tokens:
                issues.append(
                    f"per-sample output allowance {per_sample} exceeds the "
                    f"configured native operator limit "
                    f"{direct.max_output_tokens}")
    return issues


def _min_calls(spec: TrialSpec) -> int:
    return _MIN_CALLS_GATEWAY if spec.backend == "gateway" else _MIN_CALLS_DIRECT


def plan_trial(config: RaggedizedConfig,
               spec: TrialSpec) -> tuple[int, dict[str, Any]]:
    """Offline qualification plan: ZERO model/HTTP/telemetry I/O.

    Validates the spec against the configured identities and renders the
    deterministic plan (workload fingerprints, sequence shape, budgets,
    declared identities, gate projection) with execution NOT_RUN. An
    invalid/missing prerequisite yields the exact refusal reasons with
    zero dispatch (exit 2); a clean plan is exit 0 (the plan itself is
    never execution and never qualification).
    """
    issues = preflight_issues(config, spec)
    exit_code = EXIT_USAGE if issues else EXIT_COMPLETE
    suffix_fingerprints = [
        {"index": i, "chars": len(suffix),
         "fingerprint": fingerprint({"kind": "trial-suffix", "text": suffix})}
        for i, suffix in enumerate(spec.suffixes)
    ]
    min_calls = _min_calls(spec)
    document: dict[str, Any] = {
        "qualification": "trial",
        "runner": RUNNER_NAME,
        "version": RUNNER_VERSION,
        "trial_id": spec.trial_id,
        "status": "PLAN_REJECTED" if issues else "PLAN",
        "reasons": issues,
        "workload": {
            "kind": "repeated-parent",
            "parent_chars": len(spec.parent),
            "parent_fingerprint": fingerprint(
                {"kind": "trial-parent", "text": spec.parent}),
            "suffixes": suffix_fingerprints,
            "samples": spec.sample_count,
            "warmups": spec.warmups,
            "repetitions": spec.repetitions,
            "concurrency": 1,
            "seed": spec.seed,
            "seed_semantics": (
                "bound identity only; no seed-driven variation is "
                "implemented (prerequisite 004-b)"
            ),
            "workload_fingerprint": spec.expected_workload_fingerprint,
            "declared_workload_fingerprint": spec.workload_fingerprint,
            "workload_fingerprint_consistent":
                spec.declared_workload_fingerprint_matches(),
            "cache_control": (
                "none (no cache-key/slot control in this slice; no assumed "
                "slot reuse)"
            ),
            "unsupported_controls": "context/pair/batch/precision/"
                                     "seed-variation refuse with named "
                                     "prerequisites (004-b); see the spec "
                                     "contract",
        },
        "budgets": {
            "deadline_seconds": spec.budgets.deadline_seconds,
            "max_dispatches": spec.budgets.max_dispatches,
            "max_output_tokens_total": spec.budgets.max_output_tokens_total,
            "per_sample_output_tokens": spec.per_sample_output_tokens,
            "min_dispatches_per_sample": min_calls,
            "min_dispatches_full_trial": min_calls * spec.sample_count,
            "semantics": (
                "one absolute trial deadline and one shared dispatch "
                "admission allowance span all warmups, repetitions, "
                "retries, template and model calls; they are never reset "
                "per sample and are enforced at the real transport "
                "dispatch boundary"
            ),
        },
        "identities": {
            "declared": {
                "code_version": spec.code_version,
                "backend": spec.backend,
                "model": spec.declared_model,
                "profile": spec.profile,
                "purpose": spec.purpose,
                "template_build_id": spec.template_build_id,
            },
            "observed": None,
            "identity_note": (
                "declared identities are verified pre-dispatch against the "
                "executing package and the configured backend; runtime/"
                "GGUF/tokenizer physical identities are unavailable on "
                "this host and remain unverified; observation happens "
                "only during an explicitly opted-in execution"
            ),
        },
        "gates": {
            "machine_readable_document": GATES_DOC_PATH,
            "executable_in_this_slice": executable_gate_ids(),
            "real_trials": "NOT_RUN",
        },
        "execution": "NOT_RUN (plan only; dispatch requires the explicit "
                      "opt-in `raggedized qualification run`)",
        "zero_dispatch": True,
    }
    return exit_code, document


def _sample_record(ordinal: int, phase: str, text: str, suffix_index: int,
                   first_repetition: bool,
                   result: Any,
                   wall_seconds: float) -> dict[str, Any]:
    """Build ONE safe per-sample record through the strict contract.

    The record is validated against :class:`TrialSample` at the
    construction boundary (004-b criterion 2) and the DTO projection
    (same values, bounded shape) is what the trial stores and renders.
    """
    record = {
        "ordinal": ordinal,
        "phase": phase,
        "first_repetition": first_repetition,
        # First/repeated ORDER is the ordinal; physical cold/warm state is
        # UNKNOWN without cache reset/isolation evidence and is never
        # inferred from position (004-a criterion 3).
        "physical_state": "unknown",
        "suffix_index": suffix_index,
        "input_chars": len(text),
        "input_fingerprint": fingerprint(
            {"kind": "trial-input", "ordinal": ordinal, "text": text}),
        "outcome": result.outcome.value,
        "error": result.error,
        "adapter_reported_cycles": result.attempts,
        # Label-qualified (phase identity) plus label-independent content
        # fingerprints; raw output text never leaves the process.
        "text_fingerprint": (
            fingerprint({"kind": "trial-response-text",
                         "label": str(ordinal), "text": result.text})
            if result.text is not None else None),
        "content_fingerprint": (
            fingerprint({"kind": "trial-response-content",
                         "text": result.text})
            if result.text is not None else None),
        # The per-request declared backend binding exported by the
        # adapter (003 binding, reused).
        "backend_fingerprint": result.fingerprint,
        "usage": _usage_dict(result),
        "timings": _timings_dict(result),
    }
    record["wall_seconds"] = wall_seconds
    return TrialSample.model_validate(record).model_dump()


def _cache_input_consistency(samples: list[dict[str, Any]]) -> dict[str, int]:
    """Supported accounting relation per sample (raw facts only).

    ``cache_hit_tokens <= input_tokens`` when both are reported;
    contradictory counters are raw facts and can never become positive
    evidence; an uncheckable relation (input missing) stays explicit.
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
    return {
        "consistent_samples": consistent,
        "contradictory_samples": contradictory,
        "uncheckable_samples": uncheckable,
        "note": (
            "contradictory reported cache/input counters are preserved as "
            "raw facts only and cannot become positive evidence; reported "
            "cache tokens are distinct reported facts, not "
            "evaluated-prefill work"
        ),
    }


def run_trial(
    config: RaggedizedConfig,
    spec: TrialSpec,
    *,
    clock: Callable[[], float] | None = None,
    inner_transport: GatewayTransport | None = None,
    synthetic: bool = False,
    synthetic_server: SyntheticTrialServer | None = None,
) -> tuple[int, dict[str, Any]]:
    """Run one finite repeated-parent qualification trial.

    Returns ``(exit_code, evidence_document)``. Exit codes: ``0``
    complete (every declared sample resolved; an EXECUTION status that
    may contain failed/unknown samples, never qualification), ``1``
    not-run/incomplete (finite budget or adapter preflight stop), ``2``
    pre-dispatch refusal (invalid spec/config consistency, mode not
    configured, absent or invalid credential reference) — always with
    zero dispatches.

    ``inner_transport`` is a test seam only: production (the CLI) always
    passes ``None`` and the real transport is built from the configured
    route/destination (or, under the explicit synthetic opt-in, from the
    owned fixture). The shared-budget seam always wraps the inner
    transport regardless of its origin.
    """
    _clock = clock if clock is not None else time.monotonic
    issues = preflight_issues(config, spec)
    if issues:
        return EXIT_USAGE, _refusal_document(
            spec.trial_id, "TRIAL_PREFLIGHT_REFUSED", issues,
            "trial spec/config consistency refused before dispatch "
            "(zero HTTP; no transport was constructed)")

    # Only the explicit synthetic opt-in (and no test seam) starts the
    # owned fixture; a caller-provided server is owned by the caller.
    fixture: SyntheticTrialServer | None = None
    if synthetic and synthetic_server is None:
        fixture = SyntheticTrialServer(spec.backend)
    try:
        return _run_trial_inner(
            config, spec,
            clock=_clock,
            inner_transport=inner_transport,
            synthetic=synthetic,
            synthetic_server=synthetic_server if synthetic_server is not None else fixture,
        )
    finally:
        if fixture is not None:
            fixture.shutdown()


def _run_trial_inner(
    config: RaggedizedConfig,
    spec: TrialSpec,
    *,
    clock: Callable[[], float],
    inner_transport: GatewayTransport | None,
    synthetic: bool,
    synthetic_server: SyntheticTrialServer | None,
) -> tuple[int, dict[str, Any]]:
    # ---- target materialization (before any transport is built) --------
    if spec.backend == "gateway":
        route = config.generator.route
        base_url = route.base_url
        api_key: str | None = None
        if synthetic:
            assert synthetic_server is not None
            base_url = synthetic_server.gateway_base_url
            # Owned fixture canary; configured secret references are never
            # read in synthetic mode (zero access to real credentials).
            api_key = SYNTHETIC_API_KEY
            credential_evidence: dict[str, Any] = {
                "api_key_ref": {"kind": "synthetic-canary"},
                "resolved": True,
                "note": (
                    "owned fixture canary; configured secret references "
                    "are never read in synthetic mode"
                ),
            }
        else:
            credential_evidence = {"api_key_ref": None, "resolved": None}
            if config.generator.api_key_ref is not None:
                ref = config.secrets[config.generator.api_key_ref]
                if ref.kind == "env":
                    credential_evidence["api_key_ref"] = {
                        "kind": "env", "name": ref.name}
                else:
                    credential_evidence["api_key_ref"] = {
                        "kind": "file",
                        "name_digest": fingerprint(
                            {"kind": "trial-credential-file-ref",
                             "name": ref.name}),
                    }
                resolution = resolve_secret_reference(ref)
                if resolution.status == "missing":
                    return EXIT_USAGE, _refusal_document(
                        spec.trial_id, "CREDENTIAL_ABSENT",
                        [f"reason: {resolution.reason}"],
                        "credential reference is not present on this host; "
                        "provision it out-of-band (values never in config, "
                        "command line or evidence)")
                if resolution.status == "invalid":
                    return EXIT_USAGE, _refusal_document(
                        spec.trial_id, "CREDENTIAL_INVALID",
                        [f"reason: {resolution.reason}"],
                        "credential reference is not a supported single-"
                        "line credential reference; values never in "
                        "config, command line or evidence")
                api_key = resolution.value
                credential_evidence["resolved"] = True
        min_calls = _MIN_CALLS_GATEWAY
        if inner_transport is None:
            inner_transport = GatewayTransport(
                base_url, timeout_seconds=route.timeout_seconds,
                api_key=api_key)
    else:
        direct = config.direct_generation
        base_url = direct.destination.base_url  # type: ignore[union-attr]
        if synthetic:
            assert synthetic_server is not None
            base_url = synthetic_server.native_base_url
        credential_evidence = {"api_key_ref": None, "resolved": None}
        min_calls = _MIN_CALLS_DIRECT
        if inner_transport is None:
            inner_transport = GatewayTransport(
                base_url,
                timeout_seconds=direct.deadline_seconds,  # type: ignore[union-attr]
                endpoint_contract="native")

    # ---- one absolute deadline + one shared allowance ------------------
    start = clock()
    trial_deadline = start + spec.budgets.deadline_seconds
    transport = BudgetedTransport(
        inner_transport,
        deadline=trial_deadline,
        max_dispatches=spec.budgets.max_dispatches,
        clock=clock,
    )
    # The REAL application adapters, bound to the budgeted REAL transport.
    if spec.backend == "gateway":
        adapter: GatewayGenerator | DirectNativeGenerator = GatewayGenerator(
            config.generator, api_key=api_key, transport=transport,
            clock=clock)
    else:
        adapter = DirectNativeGenerator(config.direct_generation,
                                        transport=transport, clock=clock)

    sequence = spec.declared_sequence()
    samples: list[dict[str, Any]] = []
    stop_reason: str | None = None
    for ordinal, phase, text, suffix_index in sequence:
        now = clock()
        if now >= trial_deadline:
            stop_reason = "budget_exhausted_deadline"
            break
        if transport.remaining_dispatches < min_calls:
            stop_reason = "budget_exhausted_dispatches"
            break
        remaining = trial_deadline - now
        if remaining <= 0:
            stop_reason = "budget_exhausted_deadline"
            break
        request = GeneratorRequest(
            request_id=f"trial-{spec.trial_id}-{ordinal}",
            purpose=GeneratorPurpose.ANNOTATION,
            items=[TextItem(text=text)],
            model=ModelIdentity(
                name=spec.declared_model,
                adapter=("gateway-responses" if spec.backend == "gateway"
                         else "native-completion"),
                declared_capabilities=frozenset({Capability.TEXT}),
            ),
            required_capabilities=frozenset(),
            max_output_tokens=spec.per_sample_output_tokens,
            # Per-call allowance can only TIGHTEN the absolute trial
            # deadline (enforced again at the transport boundary).
            deadline_seconds=remaining,
        )
        calls_before = transport.attempted_calls
        wall_start = clock()
        result = adapter.generate(request)
        wall_seconds = clock() - wall_start
        if not math.isfinite(wall_seconds) or wall_seconds < 0:
            wall_seconds = 0.0
        try:
            record = _sample_record(
                ordinal, phase, text, suffix_index,
                first_repetition=(phase == "measured"
                                  and ordinal == spec.warmups),
                result=result,
                wall_seconds=round(wall_seconds, 9))
        except ValidationError:
            # Defensive construction-boundary invariant: the record was
            # not admitted by the strict contract, so it is not stored.
            # The spent transport accounting is retained in the
            # transport boundary of the document that follows.
            stop_reason = STOP_EVIDENCE_CONTRACT_VIOLATION
            break
        samples.append(record)
        # An adapter preflight refusal consumes no transport call and is
        # deterministic for every following sample: stop without extra
        # generation.
        if (transport.attempted_calls == calls_before
                and result.outcome is CompletionOutcome.FAILED):
            stop_reason = "preflight_refusal"
            break

    if len(samples) == spec.sample_count:
        status = "complete"
        stop_reason = None
    elif transport.attempted_calls == 0:
        status = "not_run"
    else:
        status = "incomplete"

    elapsed = round(clock() - start, 9)
    if not math.isfinite(elapsed) or elapsed < 0:
        elapsed = 0.0

    if spec.backend == "gateway":
        declared_backend_fingerprint = gateway_backend_fingerprint(route)
        template_build_id = None
    else:
        declared_backend_fingerprint = direct_backend_fingerprint(direct)
        template_build_id = (direct.template_qualification.build_id
                             if direct.template_qualification is not None
                             else None)

    if synthetic:
        endpoint_fingerprint = fingerprint(
            {"kind": "trial-endpoint", "endpoint": FIXTURE_ENDPOINT_IDENTITY})
        target_type = "synthetic-owned-fixture"
        target_type_note = (
            "owned deterministic loopback fixture started by this process "
            "under the explicit --synthetic opt-in; this is a MOCK route, "
            "never a real target")
        evidence_class = "MOCK"
    else:
        endpoint_fingerprint = fingerprint(
            {"kind": "trial-endpoint", "endpoint": base_url.rstrip("/")})
        # The runner cannot classify the configured destination as an
        # owned synthetic fixture or a live target; a localhost address
        # or an order live allowance does not establish target type.
        target_type = "unverified"
        target_type_note = (
            "the runner cannot classify the configured destination as an "
            "owned synthetic fixture or a live target; a localhost "
            "address or an order live allowance does not establish target "
            "type; explicit synthetic provenance is valid only for the "
            "owned fixtures started by the explicit synthetic route")
        evidence_class = "CONFIGURED_UNVERIFIED"

    analysis = analyze_trial(samples,
                             calls_by_kind=dict(transport.kind_counts),
                             evidence_class=evidence_class)

    evidence: dict[str, Any] = {
        "qualification": "trial",
        "runner": RUNNER_NAME,
        "version": RUNNER_VERSION,
        "trial_id": spec.trial_id,
        "backend": spec.backend,
        "status": status,
        "stop_reason": stop_reason,
        "evidence_class": evidence_class,
        "target_type": target_type,
        "target_type_note": target_type_note,
        "qualification_status": "NOT_QUALIFIED",
        "qualification_note": (
            "complete/exit-0 is execution status only and may contain "
            "failed/unknown samples; synthetic (MOCK) and "
            "configured-unverified evidence is never hardware/model/"
            "cache/quality feasibility; real qualification gates "
            "(004-b/019/ICA) remain open with live target authorization "
            "NONE"
        ),
        "workload": {
            "kind": "repeated-parent",
            "parent_chars": len(spec.parent),
            "parent_fingerprint": fingerprint(
                {"kind": "trial-parent", "text": spec.parent}),
            "suffixes": [
                {"index": i, "chars": len(suffix),
                 "fingerprint": fingerprint(
                     {"kind": "trial-suffix", "text": suffix})}
                for i, suffix in enumerate(spec.suffixes)
            ],
            "samples": spec.sample_count,
            "warmups": spec.warmups,
            "repetitions": spec.repetitions,
            "concurrency": 1,
            "seed": spec.seed,
            "seed_semantics": (
                "bound identity only; no seed-driven variation is "
                "implemented (prerequisite 004-b)"
            ),
            "workload_fingerprint": spec.workload_fingerprint,
            "workload_fingerprint_verified_pre_dispatch": True,
            "cache_control": (
                "none (no cache-key/slot control in this slice; no assumed "
                "slot reuse)"
            ),
        },
        "budgets": {
            "deadline_seconds": spec.budgets.deadline_seconds,
            "max_dispatches": spec.budgets.max_dispatches,
            "max_output_tokens_total": spec.budgets.max_output_tokens_total,
            "per_sample_output_tokens": spec.per_sample_output_tokens,
            "elapsed_seconds": elapsed,
            "elapsed_seconds_scope": (
                "trial only: measured after preflight and target "
                "materialization, from the first dispatch decision through "
                "the last recorded sample"
            ),
            "semantics": (
                "one absolute trial deadline and one shared dispatch "
                "admission allowance span all warmups, repetitions, "
                "retries, template and model calls; never reset per "
                "sample; enforced at the real transport dispatch boundary"
            ),
        },
        "identities": {
            "declared": {
                "code_version": spec.code_version,
                "backend": spec.backend,
                "model": spec.declared_model,
                "profile": spec.profile,
                "purpose": spec.purpose,
                "template_build_id": (
                    spec.template_build_id
                    if spec.template_build_id is not None
                    else (template_build_id if spec.backend == "direct"
                          else None)),
                "endpoint_fingerprint": endpoint_fingerprint,
            },
            "observed": {
                # Per-request declared backend binding exported by the
                # adapters (dialect, pinned contract, declared model,
                # credential-free endpoint, capability snapshot).
                "backend_fingerprint": declared_backend_fingerprint,
                # Unavailable physical identities stay explicit, never
                # guessed: this host cannot measure the deployed
                # runtime/GGUF or tokenizer identity.
                "runtime_identity": "unverified",
                "model_runtime_identity": "unverified",
                "tokenizer_identity": "unavailable",
            },
            "identity_note": (
                "declared identities were verified pre-dispatch against "
                "the executing package and the configured backend; "
                "runtime/GGUF/tokenizer physical identities are "
                "unavailable and remain unverified; per-sample observed "
                "backend fingerprints are bound in each sample record"
            ),
        },
        "credentials": credential_evidence,
        "requests": samples,
        "transport_boundary": {
            "attempted_calls": transport.attempted_calls,
            "calls_by_kind": dict(transport.kind_counts),
            "responses_received": transport.responses_received,
            "ambiguous_dispatches": transport.ambiguous_dispatches,
            "pre_dispatch_failures": transport.pre_dispatch_failures,
            "remaining_dispatches": transport.remaining_dispatches,
        },
        "accounting": {
            "output_reservation": {
                "total": spec.budgets.max_output_tokens_total,
                "per_sample": spec.per_sample_output_tokens,
                "semantics": (
                    "reserved before dispatch as each request's "
                    "max_output_tokens; the summed per-sample reservation "
                    "never exceeds the total; observed usage is recorded "
                    "exactly as reported and unknown usage stays null, "
                    "never fabricated"
                ),
            },
            "cache_input_consistency": _cache_input_consistency(samples),
        },
        "analysis": analysis,
        "gates": {
            "machine_readable_document": GATES_DOC_PATH,
            "executable_in_this_slice": executable_gate_ids(),
            "real_trials": "NOT_RUN",
            "note": (
                "only the text/repeated-parent runner entrypoints are "
                "executable in this slice; all other experiments and ALL "
                "real trials are pending the named prerequisites (004-b, "
                "007, 012, 014, 015, 016, 018) and real target "
                "authorization"
            ),
        },
    }
    try:
        # Serialization-boundary invariant (004-b criterion 2): the
        # complete envelope must satisfy the strict result contract,
        # including the analysis == pure-recomputation check.
        validate_trial_evidence(evidence)
    except (ValidationError, ValueError) as exc:
        return EXIT_NOT_RUN, {
            **_refusal_document(
                spec.trial_id, "EVIDENCE_CONTRACT_VIOLATION",
                [f"internal invariant: {type(exc).__name__}"],
                "the constructed evidence document failed the strict "
                "sample/result contract (internal invariant); the "
                "transport-boundary spent ledger is preserved"),
            "transport_boundary": {
                "attempted_calls": transport.attempted_calls,
                "calls_by_kind": dict(transport.kind_counts),
                "responses_received": transport.responses_received,
                "ambiguous_dispatches": transport.ambiguous_dispatches,
                "pre_dispatch_failures": transport.pre_dispatch_failures,
                "remaining_dispatches": transport.remaining_dispatches,
            },
        }
    exit_code = EXIT_COMPLETE if status == "complete" else EXIT_NOT_RUN
    return exit_code, evidence
