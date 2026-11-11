"""Machine-readable qualification prerequisite projection (OAP 004-a).

Covers every mandatory experiment-matrix ID of ARCHITECTURE.md §23.2
(source SHA-256 4b41905396a3838269fd6cf372614cd23cb2c3b6a37be09f29ed752803c0983a).

This slice's executable entrypoints are the TEXT repeated-parent trial
runner entrypoints (gateway text trial and direct native repeated-parent
trial, explicit opt-in). Every OTHER experiment — and every REAL trial
against an authorized target — stays NOT_RUN: live target authorization
is NONE (no approved actual URL/model/secretref/GPU ownership/corpus), so
no positive topology, cache, speedup, quality, VRAM or license claim may
be derived from this software. Supplied-value parity analysis and local telemetry
are partial tools, not execution of the remaining experiments.

The committed machine-readable document is
``docs/benchmarks/qualification-gates.json`` (exact rendering of
:func:`gate_projection`); a unit test binds the two together.

Bounded local resource telemetry IS implemented in objective 004-d
(own-process CPU/RSS on this devhost, plus at most one bounded
nvidia-smi metadata query; explicit opt-in only). It is read-only
devhost observation, NOT remote/worker/model-process measurement:
every gate above still stays NOT_RUN (live target authorization NONE),
and the gates that named resource telemetry as a prerequisite now
reference the 004-d bounded local scope only.
"""

from __future__ import annotations

import json

GATE_PROJECTION_VERSION = 1
ARCHITECTURE_SHA256 = "4b41905396a3838269fd6cf372614cd23cb2c3b6a37be09f29ed752803c0983a"
GATES_DOC_PATH = "docs/benchmarks/qualification-gates.json"

# Experiment availability is distinct from supplied-value analysis and instrumentation.
_GATE_ROWS = [
    (
        "GATEWAY-01",
        "Text request through the configured local-Qwen Responses route",
        True,
        (
            "Authorized route, credential and real target; raggedized qualification run "
            "is a bounded text trial."
        ),
    ),
    (
        "GATEWAY-02",
        "Authorized visual input through that route",
        False,
        ("016 audited vision path, qualified gateway vision capability and authorized target."),
    ),
    (
        "GATEWAY-03",
        "Equivalent repeated-parent jobs through gateway",
        True,
        (
            "Authorized target; raggedized qualification run sends no cache-key or slot "
            "control; measured cache evidence required."
        ),
    ),
    (
        "DIRECT-01",
        "Repeated parent with different target chunks through direct llama.cpp",
        True,
        (
            "Authorized materialized offline_diagnostic destination and tested build; "
            "cold/warm physical state requires isolation evidence."
        ),
    ),
    (
        "V100-MEM-01",
        "Q6 vision 32k alone, then FP16 reranker batches 1/2/4/8",
        False,
        (
            "012 worker, 015 GPU ownership/mode operations, authorized GPU and actual "
            "model processes; resource diagnose measures own process/devhost only."
        ),
    ),
    (
        "V100-MEM-02",
        "16k/24k and optionally 48k/64k online contexts",
        False,
        (
            "015 GPU ownership, context controls and authorized GPU; resource diagnose "
            "is local partial instrumentation only."
        ),
    ),
    (
        "RERANK-01",
        "10/20/40/80 candidates at several pair lengths",
        False,
        (
            "012 private worker, pair/batch controls, authorized real GPU and measured "
            "experiments; supplied-score analysis is not an experiment."
        ),
    ),
    (
        "EMBED-01",
        "Short-query BGE-M3 on the actual serving CPU",
        False,
        (
            "007 embedding pipeline and authorized real serving CPU; supplied-vector "
            "analysis is not an experiment."
        ),
    ),
    (
        "EMBED-02",
        "Same checkpoint with corpus GPU FP16 versus CPU FP32",
        False,
        (
            "007 embedding pipeline and authorized real CPU/GPU execution; supplied-"
            "vector analysis does not execute either."
        ),
    ),
    (
        "ONLINE-01",
        "Complete authenticated query-to-cited-answer path",
        False,
        ("014 authenticated answer API, 019 held-out quality evaluation and authorized target."),
    ),
    (
        "ONLINE-02",
        "Two or more concurrent requests under explicit limits",
        False,
        (
            "014 authenticated answer API and concurrency implementation; trial "
            "concurrency is limited to one."
        ),
    ),
    (
        "OPS-01",
        "Interrupt annotation and embedding jobs; restart workers",
        False,
        ("007/010 job implementation and 017 updates/recovery with authorized disposable targets."),
    ),
    (
        "OPS-02",
        "Online to offline to online transitions",
        False,
        ("015 GPU mode operations and real GPU ownership journal with authorized target."),
    ),
    (
        "LICENSE-01",
        "Exact dependency/model/renderer inventory",
        False,
        ("018 packaging and license audit; certifi MPL-2.0 exception not granted."),
    ),
]

REQUIRED_GATE_IDS = tuple(row[0] for row in _GATE_ROWS)


def gate_projection() -> dict:
    """The complete machine-readable prerequisite projection.

    Pure and deterministic: the same source matrix always renders the
    same document. ``status`` is NOT_RUN for every gate in this slice
    (live target authorization: NONE).
    """
    gates: dict[str, dict] = {}
    for gate_id, experiment, executable, pending in _GATE_ROWS:
        gates[gate_id] = {
            "experiment": experiment,
            "runner_entrypoint": (
                "raggedized qualification run (text repeated-parent trial; "
                "explicit opt-in; --synthetic for the owned deterministic "
                "MOCK fixture)"
                if executable
                else None
            ),
            "executable_in_this_slice": executable,
            "status": "NOT_RUN",
            "pending": pending,
            "available_analysis": (
                "python -m slaif_raggedized_helper.qualification.parity_cli "
                "embedding: supplied vectors only"
                if gate_id == "EMBED-02"
                else "python -m slaif_raggedized_helper.qualification.parity_cli "
                "rerank: supplied scores only"
                if gate_id == "RERANK-01"
                else None
            ),
            "partial_instrumentation": (
                "raggedized resource diagnose: bounded own-process/devhost observations"
                if gate_id in ("V100-MEM-01", "V100-MEM-02", "RERANK-01")
                else None
            ),
        }
    return {
        "version": GATE_PROJECTION_VERSION,
        "source": (
            "ARCHITECTURE.md section 23.2 mandatory experiment matrix "
            f"(SHA-256 {ARCHITECTURE_SHA256})"
        ),
        "generated_by": "slaif_raggedized_helper.qualification.gates",
        "live_target_authorization": "NONE",
        "real_trials": "NOT_RUN",
        "positive_claims": (
            "none: no topology, cache, speedup, quality, VRAM, license or "
            "readiness claim follows from this projection or from any "
            "synthetic/configured-unverified trial evidence in this slice"
        ),
        "gates": gates,
    }


def gate_projection_bytes() -> bytes:
    """Canonical JSON rendering (sorted keys, 2-space indent, trailing LF)."""
    return (json.dumps(gate_projection(), indent=2, sort_keys=True) + "\n").encode("utf-8")


def executable_gate_ids() -> list[str]:
    return [row[0] for row in _GATE_ROWS if row[2]]
