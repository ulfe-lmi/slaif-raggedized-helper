"""Finite qualification trials (OAP objective 004-a).

Strict trial spec/sample/result contracts, a finite trial runner over
the real gateway/direct application code (one absolute trial deadline
and one shared dispatch allowance at the real transport boundary),
reproducible latency analysis and the machine-readable prerequisite
projection of the architecture §23.2 experiment matrix.

Execution is an explicit opt-in (``raggedized qualification run``);
planning and the gate projection are offline with zero model/HTTP/
telemetry I/O. Importing this package performs no I/O.
"""

from .analysis import analyze_trial, quantile_nearest_rank
from .gates import GATES_DOC_PATH, gate_projection, gate_projection_bytes
from .resources import (
    PhaseEvent,
    TrialResourceObserver,
    run_resource_diagnostic,
    run_gpu_metadata_query,
    validate_resource_wrapper,
    wrap_trial_with_resources,
)
from .contracts import (
    TrialEvidence,
    TrialSample,
    UsageFacts,
    TimingsFacts,
    validate_trial_evidence,
)
from .runner import (
    EXIT_COMPLETE,
    EXIT_NOT_RUN,
    EXIT_USAGE,
    RUNNER_NAME,
    RUNNER_VERSION,
    plan_trial,
    preflight_issues,
    run_trial,
)
from .spec import (
    SUPPORTED_WORKLOAD,
    TRIAL_SPEC_VERSION,
    TrialBudgets,
    TrialSpec,
    trial_workload_fingerprint,
)
from .specio import (
    MAX_SPEC_FILE_BYTES,
    SpecFileRefusal,
    load_trial_spec_json,
)
from .synthetic import SYNTHETIC_API_KEY, SyntheticTrialServer

__all__ = [
    "MAX_SPEC_FILE_BYTES",
    "GATES_DOC_PATH",
    "PhaseEvent",
    "TrialResourceObserver",
    "run_gpu_metadata_query",
    "run_resource_diagnostic",
    "validate_resource_wrapper",
    "wrap_trial_with_resources",
    "EXIT_COMPLETE",
    "EXIT_NOT_RUN",
    "EXIT_USAGE",
    "RUNNER_NAME",
    "RUNNER_VERSION",
    "SYNTHETIC_API_KEY",
    "SUPPORTED_WORKLOAD",
    "SyntheticTrialServer",
    "TRIAL_SPEC_VERSION",
    "TrialBudgets",
    "TrialEvidence",
    "TrialSample",
    "TimingsFacts",
    "TrialSpec",
    "UsageFacts",
    "SpecFileRefusal",
    "analyze_trial",
    "gate_projection",
    "gate_projection_bytes",
    "plan_trial",
    "preflight_issues",
    "quantile_nearest_rank",
    "load_trial_spec_json",
    "validate_trial_evidence",
    "run_trial",
    "trial_workload_fingerprint",
]
