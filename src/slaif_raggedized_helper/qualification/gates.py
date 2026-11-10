"""Machine-readable qualification prerequisite projection (OAP 004-a).

Covers every mandatory experiment-matrix ID of ARCHITECTURE.md §23.2
(source SHA-256 4b41905396a3838269fd6cf372614cd23cb2c3b6a37be09f29ed752803c0983a).

This slice's executable entrypoints are the TEXT repeated-parent trial
runner entrypoints (gateway text trial and direct native repeated-parent
trial, explicit opt-in). Every OTHER experiment — and every REAL trial
against an authorized target — stays NOT_RUN: live target authorization
is NONE (no approved actual URL/model/secretref/GPU ownership/corpus), so
no positive topology, cache, speedup, quality, VRAM or license claim may
be derived from this software. Other implementations/telemetry/parity
are explicitly pending 004-b or the named later objectives.

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
ARCHITECTURE_SHA256 = ("4b41905396a3838269fd6cf372614cd23cb2c3b6a37be09f29"
                       "ed752803c0983a")
GATES_DOC_PATH = "docs/benchmarks/qualification-gates.json"

# (ID, experiment, executable in this slice?, named pending prerequisites)
_GATE_ROWS: list[tuple[str, str, bool, str]] = [
    (
        "GATEWAY-01",
        "Text request through the configured local-Qwen Responses route",
        True,
        "real target authorization (approved URL/credential/route identity) "
        "and 004-b telemetry/parity composition; runner entrypoint available",
    ),
    (
        "GATEWAY-02",
        "Authorized visual input through that route",
        False,
        "004-b + 016 (audited vision path) + qualified gateway vision "
        "capability + real target authorization",
    ),
    (
        "GATEWAY-03",
        "Equivalent repeated-parent jobs through gateway",
        True,
        "real target authorization and 004-b composition; repeated-parent "
        "gateway trial entrypoint available (no assumed slot reuse: the "
        "trial sends no cache-key/slot control)",
    ),
    (
        "DIRECT-01",
        "Repeated parent with different target chunks through direct llama.cpp",
        True,
        "materialized offline_diagnostic destination on an authorized real "
        "build + real target authorization; repeated-parent direct trial "
        "entrypoint available (cold/warm physical state stays unknown "
        "without cache reset/isolation evidence)",
    ),
    (
        "V100-MEM-01",
        "Q6 vision 32k alone, then FP16 reranker batches 1/2/4/8",
        False,
        "015 (GPU ownership/mode operations) + 004-d bounded local "
        "resource telemetry (own-process/devhost scope only) + "
        "authorized real GPU",
    ),
    (
        "V100-MEM-02",
        "16k/24k and optionally 48k/64k online contexts",
        False,
        "015 + 004-d bounded local resource telemetry (own-process/devhost "
        "scope only) + authorized real GPU",
    ),
    (
        "RERANK-01",
        "10/20/40/80 candidates at several pair lengths",
        False,
        "012 (private reranker worker) + 004-d bounded local "
        "resource telemetry (own-process/devhost scope only) + "
        "authorized real GPU",
    ),
    (
        "EMBED-01",
        "Short-query BGE-M3 on the actual serving CPU",
        False,
        "007 (embedding pipeline) + real serving CPU target",
    ),
    (
        "EMBED-02",
        "Same checkpoint with corpus GPU FP16 versus CPU FP32",
        False,
        "007 (embedding pipeline) + authorized real GPU",
    ),
    (
        "ONLINE-01",
        "Complete authenticated query-to-cited-answer path",
        False,
        "014 (authenticated answer API) + 004-b composition",
    ),
    (
        "ONLINE-02",
        "Two or more concurrent requests under explicit limits",
        False,
        "014 + 004-b (concurrency above 1 is unimplemented in this slice)",
    ),
    (
        "OPS-01",
        "Interrupt annotation and embedding jobs; restart workers",
        False,
        "017 (updates/recovery) + 007/010 job implementation",
    ),
    (
        "OPS-02",
        "Online to offline to online transitions",
        False,
        "015 (GPU mode operations) + real GPU ownership journal",
    ),
    (
        "LICENSE-01",
        "Exact dependency/model/renderer inventory",
        False,
        "018 (packaging and license audit); the certifi (MPL-2.0) policy "
        "exception has not been granted",
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
                "MOCK fixture)" if executable else None),
            "executable_in_this_slice": executable,
            "status": "NOT_RUN",
            "pending": pending,
        }
    return {
        "version": GATE_PROJECTION_VERSION,
        "source": (
            "ARCHITECTURE.md section 23.2 mandatory experiment matrix "
            f"(SHA-256 {ARCHITECTURE_SHA256})"
        ),
        "generated_by": "slaif_raggedized_helper.qualification.gates (004-a)",
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
    return (json.dumps(gate_projection(), indent=2, sort_keys=True)
            + "\n").encode("utf-8")


def executable_gate_ids() -> list[str]:
    return [row[0] for row in _GATE_ROWS if row[2]]
