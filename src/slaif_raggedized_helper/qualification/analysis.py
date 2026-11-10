"""Reproducible, finite latency analysis for trial samples (OAP 004-a).

Quantile convention (documented, deterministic):

- statistics are computed over the FINITE, NON-NEGATIVE caller-wall
  seconds of samples whose outcome is ``terminal`` ONLY; failed,
  unknown-completion, refusal, incomplete and invalid observations are
  counted separately and never averaged into model latency;
- a quantile p (0 < p < 100) uses the NEAREST-RANK method: sort the
  sample ascending, take rank = ceil(p/100 * n), 1-based, clamped to
  1..n, and return the value at that rank; p50/p95 are defined this way
  and ``max`` is the last sorted value;
- zero-sample sets (no terminal observations in a group) produce ``n=0``
  and ALL-NULL metrics — they can never produce a qualifying pass;
- the analysis is a PURE function of the recorded sample observations:
  the same observations always produce the same summary (deterministic
  summaries; wall-clock observations are real per-run measurements and
  are not faked).

Wall-time boundary (004-a criterion 3): the per-sample ``wall_seconds``
is CALLER wall time around one ``generate()`` call (it includes adapter
cycles, template work and transport time). It is never model work time.
Native template time is NOT TTFT; the gateway dialect reports no
prefill/TTFT at all, so those stay null and missing prefill stays null.
"""

from __future__ import annotations

import math
from typing import Any

OUTCOME_TERMINAL = "terminal"

# Fixed reason vocabulary for why a group cannot qualify (never a pass).
NO_SAMPLES = "no_terminal_samples"
UNQUALIFIED_EVIDENCE = "evidence_not_qualified"


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


def _group_stats(samples: list[dict[str, Any]]) -> dict[str, Any]:
    """One deterministic latency/outcome summary for one sample group."""
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
            "convention": (
                "nearest-rank quantiles (rank = ceil(p/100*n), 1-based, "
                "clamped) over finite non-negative caller-wall seconds of "
                "terminal-outcome samples only; failed/unknown/refusal/"
                "incomplete/invalid observations are counted separately "
                "and never averaged into model latency; caller wall time "
                "includes adapter cycles and template work and is NOT "
                "model work time"
            ),
        },
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
    """
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
