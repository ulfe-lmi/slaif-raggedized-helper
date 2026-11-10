"""Reproducible, finite latency analysis for trial samples (OAP 004-a/b).

Quantile convention (documented, deterministic):

- statistics are computed over the FINITE, NON-NEGATIVE actually-known
  reported values of samples whose outcome is ``terminal`` ONLY;
  failed, unknown-completion, refusal, incomplete and invalid
  observations are counted separately and never averaged into model
  latency;
- a quantile p (0 < p < 100) uses the NEAREST-RANK method: sort the
  sample ascending, take rank = ceil(p/100 * n), 1-based, clamped to
  1..n, and return the value at that rank; p50/p95 are defined this way
  and ``max`` is the last sorted value;
- zero-sample sets (no terminal observations in a group) produce ``n=0``
  and ALL-NULL metrics — they can never produce a qualifying pass;
- a reported KNOWN ZERO is a measurement and counts; a MISSING (null)
  reported value is absent (counted in ``missing``), never a zero; a
  non-finite or negative reported value is counted invalid and
  excluded;
- the analysis is a PURE function of the recorded sample observations:
  the same observations always produce the same summary (deterministic
  summaries; wall-clock observations are real per-run measurements and
  are not faked);
- the analysis boundary (004-b criterion 2) validates every sample
  against the strict :class:`TrialSample` contract before computing:
  a malformed sample shape is a typed ``ValidationError``, never a
  silent partial summary.

Wall-time boundary (004-a criterion 3): the per-sample ``wall_seconds``
is CALLER wall time around one ``generate()`` call (it includes adapter
cycles, template work and transport time). It is never model work time.
Native template time is NOT TTFT; the gateway dialect reports no
prefill/TTFT at all, so those stages stay unavailable (n=0, all null)
and missing prefill stays null — never a zero.
"""

from __future__ import annotations

import math
from typing import Any

from .contracts import STAGE_METRIC_KEYS, TrialSample

OUTCOME_TERMINAL = "terminal"

# Fixed reason vocabulary for why a group cannot qualify (never a pass).
NO_SAMPLES = "no_terminal_samples"
UNQUALIFIED_EVIDENCE = "evidence_not_qualified"

LATENCY_CONVENTION = (
    "nearest-rank quantiles (rank = ceil(p/100*n), 1-based, "
    "clamped) over finite non-negative caller-wall seconds of "
    "terminal-outcome samples only; failed/unknown/refusal/"
    "incomplete/invalid observations are counted separately "
    "and never averaged into model latency; caller wall time "
    "includes adapter cycles and template work and is NOT "
    "model work time"
)
STAGE_CONVENTION = (
    "nearest-rank quantiles (rank = ceil(p/100*n), 1-based, "
    "clamped) over the actually-known finite non-negative "
    "reported values of terminal-outcome samples only; a "
    "reported known 0 counts as a measurement; a missing "
    "(null) reported value is absent (counted in missing), "
    "never a zero; a non-finite or negative reported value is "
    "counted invalid and excluded; native reported "
    "prefill/decode/model-total are distinct from caller "
    "wall time and template work; the pinned gateway "
    "dialect reports no prefill and neither dialect "
    "reports a TTFT, so those stages stay unavailable "
    "(n=0, all null), never 0"
)

_STAGE_SOURCES = {
    "caller_wall_seconds": (
        "caller wall time around one generate() call, including "
        "adapter cycles, template work and transport; not model "
        "work time and never TTFT"
    ),
    "prefill_seconds": (
        "native-reported evaluated-prefill seconds; the pinned "
        "gateway dialect never reports it, so it stays "
        "unavailable (n=0, all null), never 0"
    ),
    "decode_seconds": (
        "native-reported decode seconds (reported "
        "predicted_ms/1000); distinct from caller wall time"
    ),
    "model_total_seconds": (
        "native-reported model total seconds (reported "
        "prompt_ms/1000 + predicted_ms/1000, only when both are "
        "reported); distinct from caller wall time"
    ),
    "ttft_seconds": (
        "first-token latency; never reported by the pinned "
        "dialects, so it stays unavailable (n=0, all null), "
        "never 0"
    ),
}


def _finite_nonneg(values: list[float]) -> list[float]:
    return sorted(v for v in values
                  if isinstance(v, (int, float))
                  and not isinstance(v, bool)
                  and math.isfinite(v) and v >= 0)


def quantile_nearest_rank(sorted_values: list[float], p: float) -> float | None:
    """Nearest-rank quantile over a pre-sorted finite ascending list.

    rank = ceil(p/100 * n), 1-based, clamped to 1..n; empty input is
    None (a missing measurement, never an invented zero).
    """
    if not sorted_values:
        return None
    n = len(sorted_values)
    rank = math.ceil(p / 100.0 * n)
    rank = max(1, min(n, rank))
    return sorted_values[rank - 1]


def _stage_metric(terminal: list[dict[str, Any]], getter) -> dict[str, Any]:
    """One reported metric's n/min/p50/p95/max over terminal samples.

    ``getter`` returns the reported value (or None when the metric is
    absent for the sample). Missing values are absent (never zero);
    non-finite/negative values are counted invalid and excluded.
    """
    known: list[float] = []
    missing = 0
    invalid = 0
    for sample in terminal:
        value = getter(sample)
        if value is None:
            missing += 1
            continue
        if (isinstance(value, (int, float)) and not isinstance(value, bool)
                and math.isfinite(value) and value >= 0):
            known.append(float(value))
        else:
            invalid += 1
    known.sort()
    return {
        "n": len(known),
        "min": known[0] if known else None,
        "p50": quantile_nearest_rank(known, 50),
        "p95": quantile_nearest_rank(known, 95),
        "max": known[-1] if known else None,
        "missing": missing,
        "invalid_observations": invalid,
    }


def _group_stats(samples: list[dict[str, Any]]) -> dict[str, Any]:
    """One deterministic latency/stage summary for one sample group."""
    total = len(samples)
    terminal = [s for s in samples if s.get("outcome") == OUTCOME_TERMINAL]
    counts: dict[str, int] = {}
    for sample in samples:
        outcome = str(sample.get("outcome"))
        counts[outcome] = counts.get(outcome, 0) + 1
    invalid_wall = 0
    wall_values: list[float] = []
    for sample in terminal:
        wall = sample.get("wall_seconds")
        if (isinstance(wall, (int, float)) and not isinstance(wall, bool)
                and math.isfinite(wall) and wall >= 0):
            wall_values.append(float(wall))
        else:
            invalid_wall += 1
    finite = _finite_nonneg(wall_values)

    def _timings_field(field: str):
        def getter(sample: dict[str, Any]):
            timings = sample.get("timings")
            return timings.get(field) if isinstance(timings, dict) else None

        return getter

    stage_metrics = {
        "convention": STAGE_CONVENTION,
        "caller_wall_seconds": {
            **_stage_metric(terminal, lambda s: s.get("wall_seconds")),
            "source": _STAGE_SOURCES["caller_wall_seconds"],
        },
    }
    for key in STAGE_METRIC_KEYS:
        if key == "caller_wall_seconds":
            continue
        field = "ttft_seconds" if key == "ttft_seconds" else (
            "prefill_seconds" if key == "prefill_seconds"
            else ("decode_seconds" if key == "decode_seconds"
                  else "total_seconds"))
        stage_metrics[key] = {
            **_stage_metric(terminal, _timings_field(field)),
            "source": _STAGE_SOURCES[key],
        }

    return {
        "samples_total": total,
        "outcome_counts": dict(sorted(counts.items())),
        "terminal_samples": len(terminal),
        "invalid_wall_observations": invalid_wall,
        "latency_seconds": {
            "n": len(finite),
            "min": finite[0] if finite else None,
            "p50": quantile_nearest_rank(finite, 50),
            "p95": quantile_nearest_rank(finite, 95),
            "max": finite[-1] if finite else None,
            "convention": LATENCY_CONVENTION,
        },
        "stage_metrics": stage_metrics,
    }


def analyze_trial(
    samples: list[dict[str, Any]],
    *,
    calls_by_kind: dict[str, int],
    evidence_class: str,
) -> dict[str, Any]:
    """Deterministic per-trial latency/accounting summary.

    ``samples`` are the safe per-sample records (one dict per executed
    sample, in ordinal order); ``calls_by_kind`` is the transport-boundary
    kind accounting (``model_dispatch`` / ``template_work``);
    ``evidence_class`` is the trial's MOCK/CONFIGURED_UNVERIFIED class.
    The result is a pure function of its inputs.

    The analysis boundary validates every sample against the strict
    ``TrialSample`` contract (004-b criterion 2): a malformed shape,
    identity or numeric value raises ``pydantic.ValidationError``
    instead of producing a partial summary.
    """
    for sample in samples:
        TrialSample.model_validate(sample)
    warmups = [s for s in samples if s.get("phase") == "warmup"]
    measured = [s for s in samples if s.get("phase") == "measured"]
    summary = {
        "warmups": _group_stats(warmups),
        "measured": _group_stats(measured),
        "transport_calls_by_kind": dict(sorted(calls_by_kind.items())),
        "timing_boundary_notes": {
            "wall_seconds_scope": (
                "caller wall time around one generate() call, including "
                "adapter cycles, template work and transport; not model "
                "work and never TTFT"
            ),
            "native_template_time": (
                "native /apply-template time is part of caller wall time "
                "and is NOT TTFT; the native dialect reports no "
                "first-token measurement, so ttft_seconds stays null"
            ),
            "gateway_prefill": (
                "the pinned gateway dialect reports no evaluated-prefill "
                "metrics; prefill stays null/unavailable and missing "
                "prefill is never a zero"
            ),
            "reported_cache_tokens": (
                "reported cache counters are distinct reported facts, not "
                "evaluated-prefill work; contradictory cache/input "
                "accounting is preserved as raw facts only and cannot "
                "become positive evidence"
            ),
        },
    }

    def _qualifying_pass_possible(group: dict[str, Any]) -> tuple[bool, str]:
        if group["terminal_samples"] == 0 or group["latency_seconds"]["n"] == 0:
            return False, NO_SAMPLES
        return False, UNQUALIFIED_EVIDENCE

    summary["qualifying_pass"] = {
        "warmups": {"possible": _qualifying_pass_possible(summary["warmups"])[0],
                    "reason": _qualifying_pass_possible(summary["warmups"])[1]},
        "measured": {"possible": _qualifying_pass_possible(summary["measured"])[0],
                     "reason": _qualifying_pass_possible(summary["measured"])[1]},
        "note": (
            "probe complete/exit-0 is execution status only; this slice's "
            f"evidence class is {evidence_class}, so no latency set can "
            "qualify: real target/model/hardware feasibility requires the "
            "ordered real trials (004-b/019/ICA)"
        ),
    }
    return summary
