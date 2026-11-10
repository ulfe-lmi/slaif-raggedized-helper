"""Real qualification trial composition (OAP objective 004-a).

The INSTALLED ``raggedized`` CLI runs in a subprocess; the real
GatewayGenerator/DirectNativeGenerator adapters speak to owned
127.0.0.1 loopback servers (the shared conftest recording server) that
record exact paths/order/bodies. Coverage (order 004-a criteria 1, 2,
3, 4, 5, 7 and the verification section):

- exact total calls across warmups/repetitions for gateway AND direct
  (native template work counts against the shared allowance: the
  budget-3 native boundary), multiple repetitions under ONE shared
  allowance, retry consumption of the allowance via failed connects,
  global deadline exhaustion mid-trial (in-flight closure, no replay),
  accepted-then-closed unknown outcome without replay;
- identity/settings preflight with ZERO dispatch (model mismatch,
  fingerprint mismatch, missing route, unmaterialized direct, invalid
  spec, invalid output destination) and the honest post-work
  export-stage failure after actual dispatches (exit 3, full safe
  evidence on stdout with the spent-attempt ledger);
- outcome/metric ambiguity (contradictory reported cache/input
  counters stay raw facts and cannot become positive evidence),
  missing usage stays null;
- deterministic explicit synthetic route (--synthetic): owned
  deterministic loopback fixture, real adapters, evidence labeled
  MOCK / synthetic-owned-fixture, timing-stripped evidence identical
  across runs, configured secrets never read; a configured (even
  loopback) URL is never classified synthetic by a boolean;
- missing target/adapter prerequisites give exact NOT_RUN/BLOCKED
  evidence, never fake runnable successes; plan/gates/help are zero
  model/HTTP/telemetry I/O (closed-port proof).

All fixtures are synthetic; no live model, real key, GPU or corpus
(order 004-a live authorization: NONE).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

from conftest import SYNTHETIC_API_KEY  # noqa: F401  (suite parity)
from test_gateway_generator import completed_json, message_item

from slaif_raggedized_helper import __version__
from slaif_raggedized_helper.qualification import (
    trial_workload_fingerprint,
)

# Unique synthetic canaries for this suite (never real credentials/data).
TRIAL_KEY_CANARY = "sk-qual-trial-canary-004a-DO-NOT-LEAK"
TRIAL_TEXT_1 = "synthetic-trial-answer-1"
TRIAL_TEXT_2 = "synthetic-trial-answer-2"
TRIAL_PROVIDER_CANARY = "PROVIDER-ERROR-CANARY-004a"

REPO_ROOT = Path(__file__).resolve().parents[2]

PARENT = "Synthetic trial parent fixture, constant bounded text."
SUFFIXES = [" Trial suffix A.", " Trial suffix B."]


def _cli_binary() -> str:
    candidate = Path(sys.executable).parent / "raggedized"
    if candidate.exists():
        return str(candidate)
    import shutil
    found = shutil.which("raggedized")
    assert found, "installed raggedized CLI not found on PATH"
    return found


def run_cli(argv: list[str], *, env: dict[str, str] | None = None,
            timeout: float = 90.0) -> subprocess.CompletedProcess:
    return subprocess.run([_cli_binary(), *argv], capture_output=True,
                          text=True, timeout=timeout, env=env)


def write_file(tmp_path: Path, doc: object, name: str) -> Path:
    path = tmp_path / name
    path.write_text(json.dumps(doc), encoding="utf-8")
    return path


def spec_dict(**overrides) -> dict:
    doc = {
        "spec_version": 1,
        "trial_id": "qual-trial-1",
        "workload": "repeated-parent",
        "purpose": "annotation",
        "parent": PARENT,
        "suffixes": list(SUFFIXES),
        "seed": 21,
        "warmups": 1,
        "repetitions": 2,
        "concurrency": 1,
        "code_version": __version__,
        "backend": "gateway",
        "declared_model": "synthetic-trial-gw",
        "profile": None,
        "template_build_id": None,
        "budgets": {
            "deadline_seconds": 20,
            "max_dispatches": 10,
            "max_output_tokens_total": 30,
        },
    }
    doc.update(overrides)
    # The declared fingerprint always tracks the FINAL workload values
    # unless the caller explicitly overrides it (mismatch tests).
    doc.setdefault(
        "workload_fingerprint",
        trial_workload_fingerprint(
            parent=doc["parent"], suffixes=list(doc["suffixes"]),
            seed=doc["seed"], warmups=doc["warmups"],
            repetitions=doc["repetitions"]),
    )
    return doc


def write_spec(tmp_path: Path, **overrides) -> Path:
    return write_file(tmp_path, spec_dict(**overrides), "trial-spec.json")


def gateway_config(port: int, *, api_key_ref: str | None = None,
                   **gen_kwargs) -> dict:
    route = {"base_url": f"http://127.0.0.1:{port}/v1",
             "model": "synthetic-trial-gw", "api": "v1-responses",
             "timeout_seconds": 5}
    generator = {
        "route": route,
        "context_expected_tokens": 1024,
        "output_reserve_tokens": 64,
        "deadline_seconds": 30,
        **gen_kwargs,
    }
    doc = {"schema_version": 1, "generator": generator}
    if api_key_ref is not None:
        generator["api_key_ref"] = api_key_ref
        doc["secrets"] = {api_key_ref: {"kind": "env",
                                        "name": "TRIAL_004A_KEY"}}
    return doc


def direct_config(port: int, *, capabilities=None, max_retries: int = 0,
                  **direct_kwargs) -> dict:
    direct = {
        "mode": "offline_diagnostic",
        "destination": {"base_url": f"http://127.0.0.1:{port}"},
        "trusted_policy": "private_trusted",
        "capabilities": capabilities or {},
        "model": "synthetic-trial-native",
        "chat_template": None,
        "template_qualification": {
            "template": None, "build_id": "build-trial-1",
            "method": "apply-template",
            "recorded_at": "2026-11-10T00:00:00+00:00",
        },
        "max_output_tokens": 64,
        "deadline_seconds": 30,
        "max_retries": max_retries,
        **direct_kwargs,
    }
    return {
        "schema_version": 1,
        "generator": {"context_expected_tokens": 1024,
                      "output_reserve_tokens": 64,
                      "deadline_seconds": 30},
        "direct_generation": direct,
    }


def direct_spec_dict(**overrides) -> dict:
    doc = spec_dict(
        backend="direct",
        trial_id="qual-trial-direct-1",
        declared_model="synthetic-trial-native",
        template_build_id="build-trial-1")
    # overrides may change workload fields: recompute the declared
    # fingerprint from the FINAL values (explicit mismatch tests pass
    # workload_fingerprint themselves).
    doc.pop("workload_fingerprint", None)
    doc.update(overrides)
    doc.setdefault(
        "workload_fingerprint",
        trial_workload_fingerprint(
            parent=doc["parent"], suffixes=list(doc["suffixes"]),
            seed=doc["seed"], warmups=doc["warmups"],
            repetitions=doc["repetitions"]),
    )
    return doc


def qual_argv(config_path: Path, spec_path: Path, sub: str = "run",
              *, extra: list[str] | None = None) -> list[str]:
    argv = ["qualification", sub, "--config", str(config_path),
            "--spec", str(spec_path)]
    return argv + (extra or [])


def gateway_scenario(texts: list[str], *, with_usage: bool = True,
                     cached_tokens: int | None = None,
                     input_tokens: int | None = None):
    state = {"n": 0}

    def scenario(h, r):
        state["n"] += 1
        text = texts[min(state["n"] - 1, len(texts) - 1)]
        if with_usage:
            usage = {"input_tokens": input_tokens if input_tokens is not None
                     else 11,
                     "output_tokens": 5}
            if cached_tokens is not None:
                usage["input_tokens_details"] = {
                    "cached_tokens": cached_tokens}
        else:
            usage = None
        h._send_json(200, completed_json([message_item("m0", text)],
                                         usage=usage))
    return scenario


def native_scenario(texts: list[str], *, cache_n: int = 0,
                    with_timings: bool = True):
    state = {"completion": 0}

    def scenario(h, r):
        body = json.loads(r.body)
        if r.path == "/apply-template":
            user_text = body["messages"][-1]["content"]
            h._send_json(200, {"prompt": "rendered::" + user_text})
            return
        state["completion"] += 1
        n = state["completion"]
        text = texts[min(n - 1, len(texts) - 1)]
        doc = {
            "content": text, "stop": True, "truncated": False,
            "stop_type": "eos",
            "tokens_evaluated": 4 + cache_n,
            "tokens_predicted": 3,
        }
        if with_timings:
            doc["timings"] = {"prompt_ms": 20.0, "predicted_ms": 40.0,
                              "prompt_n": 4, "cache_n": cache_n,
                              "predicted_n": 3}
        h._send_json(200, doc)
    return scenario


def strip_wall(doc: dict) -> dict:
    """Remove wall-clock-derived fields (per-run measurements).

    Everything else — identities, fingerprints, outcomes, accounting,
    usage, conventions, gates — is deterministic for identical inputs.
    """
    out = json.loads(json.dumps(doc))
    out["budgets"] = {k: v for k, v in out["budgets"].items()
                      if k != "elapsed_seconds"}
    for record in out["requests"]:
        record.pop("wall_seconds")
    for group in ("warmups", "measured"):
        out["analysis"][group]["latency_seconds"] = {
            k: v for k, v in
            out["analysis"][group]["latency_seconds"].items()
            if k not in ("min", "p50", "p95", "max")
        }
    return out


# ---------------------------------------------------------------------------
# gateway composition
# ---------------------------------------------------------------------------

def test_gateway_trial_happy_path_shared_allowance(server, tmp_path):
    srv = server(gateway_scenario([TRIAL_TEXT_1, TRIAL_TEXT_2,
                                   TRIAL_TEXT_1]))
    cfg = write_file(tmp_path, gateway_config(srv.port,
                                              api_key_ref="trial_key"),
                     "gw-config.json")
    spec = write_spec(tmp_path, budgets={
        "deadline_seconds": 20, "max_dispatches": 10,
        "max_output_tokens_total": 30})
    result = run_cli(qual_argv(cfg, spec),
                     env={**os.environ, "TRIAL_004A_KEY": TRIAL_KEY_CANARY})
    assert result.returncode == 0, result.stdout + result.stderr
    doc = json.loads(result.stdout)

    # exact wire: 3 POSTs in ordinal order (1 warmup + 2 measured),
    # canary only in the header
    assert srv.paths == ["/v1/responses"] * 3
    for record in srv.state.requests:
        assert record.headers.get("authorization") == \
            f"Bearer {TRIAL_KEY_CANARY}"
        assert TRIAL_KEY_CANARY not in record.body.decode("utf-8")
    bodies = [json.loads(r.body) for r in srv.state.requests]
    assert bodies[0]["input"][0]["content"][0]["text"] == PARENT + SUFFIXES[0]
    assert bodies[1]["input"][0]["content"][0]["text"] == PARENT + SUFFIXES[1]
    assert bodies[2]["input"][0]["content"][0]["text"] == PARENT + SUFFIXES[0]
    # deterministic even share of the shared output allowance (30 // 3)
    assert all(b["max_output_tokens"] == 10 for b in bodies)

    assert doc["status"] == "complete"
    assert doc["backend"] == "gateway"
    assert doc["evidence_class"] == "CONFIGURED_UNVERIFIED"
    # a configured (even loopback) URL is NEVER classified synthetic
    assert doc["target_type"] == "unverified"
    assert doc["qualification_status"] == "NOT_QUALIFIED"
    assert [s["outcome"] for s in doc["requests"]] == \
        ["terminal", "terminal", "terminal"]
    assert [s["phase"] for s in doc["requests"]] == \
        ["warmup", "measured", "measured"]
    assert doc["requests"][1]["first_repetition"] is True
    assert doc["requests"][0]["first_repetition"] is False
    assert all(s["physical_state"] == "unknown" for s in doc["requests"])
    assert all(s["usage"] == {"input_tokens": 11, "output_tokens": 5,
                              "prefill_tokens": None,
                              "cache_hit_tokens": None}
               for s in doc["requests"])
    assert doc["transport_boundary"] == {
        "attempted_calls": 3,
        "calls_by_kind": {"model_dispatch": 3, "template_work": 0},
        "responses_received": 3,
        "ambiguous_dispatches": 0,
        "pre_dispatch_failures": 0,
        "remaining_dispatches": 7,
    }
    # warmups separate from measured; measured set is 2 samples
    assert doc["analysis"]["warmups"]["samples_total"] == 1
    assert doc["analysis"]["measured"]["samples_total"] == 2
    assert doc["analysis"]["measured"]["latency_seconds"]["n"] == 2
    assert doc["analysis"]["qualifying_pass"]["measured"]["possible"] \
        is False
    # no raw material, no URL, no key in evidence
    blob = result.stdout
    assert PARENT not in blob
    assert str(srv.port) not in blob
    assert "127.0.0.1" not in blob
    assert TRIAL_KEY_CANARY not in blob
    assert TRIAL_TEXT_1 not in blob
    assert TRIAL_TEXT_2 not in blob
    assert doc["gates"]["real_trials"] == "NOT_RUN"
    assert doc["gates"]["executable_in_this_slice"] == \
        ["GATEWAY-01", "GATEWAY-03", "DIRECT-01"]


def test_gateway_trial_dispatch_allowance_shared_across_warmups_reps(
        server, tmp_path):
    # 3 samples need 3 dispatches; the allowance of 2 spans warmup AND
    # measured and is never reset per sample: sample 2 (measured) is
    # never dispatched.
    srv = server(gateway_scenario([TRIAL_TEXT_1, TRIAL_TEXT_2]))
    cfg = write_file(tmp_path, gateway_config(srv.port), "gw-config.json")
    spec = write_spec(tmp_path, budgets={
        "deadline_seconds": 20, "max_dispatches": 2,
        "max_output_tokens_total": 30})
    result = run_cli(qual_argv(cfg, spec))
    assert result.returncode == 1, result.stdout + result.stderr
    doc = json.loads(result.stdout)
    assert doc["status"] == "incomplete"
    assert doc["stop_reason"] == "budget_exhausted_dispatches"
    assert [s["outcome"] for s in doc["requests"]] == \
        ["terminal", "terminal"]
    assert doc["requests"][1]["phase"] == "measured"
    assert srv.count("/v1/responses") == 2
    assert doc["transport_boundary"]["remaining_dispatches"] == 0


def test_gateway_trial_deadline_exhausted_mid_trial_no_replay(
        server, tmp_path):
    def slow_scenario(h, r):
        time.sleep(1.5)  # past the 0.6s trial deadline
        h._send_json(200, completed_json([message_item("m0", "late")]))

    srv = server(slow_scenario)
    cfg = write_file(tmp_path, gateway_config(srv.port), "gw-config.json")
    spec = write_spec(tmp_path, budgets={
        "deadline_seconds": 0.6, "max_dispatches": 10,
        "max_output_tokens_total": 30})
    start = time.monotonic()
    result = run_cli(qual_argv(cfg, spec), timeout=30)
    elapsed = time.monotonic() - start
    assert result.returncode == 1, result.stdout + result.stderr
    doc = json.loads(result.stdout)
    assert doc["status"] == "incomplete"
    assert doc["stop_reason"] == "budget_exhausted_deadline"
    # the in-flight exchange was closed at the deadline (unknown
    # completion), and no new work started or replayed after it
    assert doc["requests"][0]["outcome"] == "unknown_completion"
    assert len(doc["requests"]) == 1
    assert srv.count("/v1/responses") == 1
    assert doc["transport_boundary"]["ambiguous_dispatches"] == 1
    assert elapsed < 3.0


def test_gateway_trial_accepted_then_closed_unknown_not_replayed(
        server, tmp_path):
    state = {"n": 0}

    def scenario(h, r):
        state["n"] += 1
        if state["n"] == 1:
            h._accept_then_close()  # ambiguous: the request may have run
        else:
            h._send_json(200, completed_json(
                [message_item("m0", TRIAL_TEXT_2)]))

    srv = server(scenario)
    cfg = write_file(tmp_path, gateway_config(srv.port), "gw-config.json")
    spec = write_spec(tmp_path, budgets={
        "deadline_seconds": 20, "max_dispatches": 10,
        "max_output_tokens_total": 30})
    result = run_cli(qual_argv(cfg, spec))
    assert result.returncode == 0, result.stdout + result.stderr
    doc = json.loads(result.stdout)
    assert doc["status"] == "complete"
    assert doc["requests"][0]["outcome"] == "unknown_completion"
    assert doc["requests"][1]["outcome"] == "terminal"
    assert srv.paths == ["/v1/responses"] * 3  # no duplicate of sample 0
    assert doc["transport_boundary"]["ambiguous_dispatches"] == 1
    assert doc["transport_boundary"]["responses_received"] == 2


def test_gateway_trial_retries_consume_shared_allowance(server,
                                                        closed_port,
                                                        tmp_path):
    # Connection refused is a positively pre-dispatch failure: the
    # adapter's bounded retry (max_retries=1) consumes the SHARED trial
    # allowance at the real transport boundary. Sample 0 = 2 attempts
    # (the whole allowance of 2); sample 1 is never dispatched.
    cfg = write_file(tmp_path, gateway_config(closed_port,
                                              **{"max_retries": 1}),
                     "gw-config.json")
    spec = write_spec(tmp_path, warmups=0, repetitions=2, budgets={
        "deadline_seconds": 20, "max_dispatches": 2,
        "max_output_tokens_total": 10})
    result = run_cli(qual_argv(cfg, spec))
    assert result.returncode == 1, result.stdout + result.stderr
    doc = json.loads(result.stdout)
    assert doc["status"] == "incomplete"
    assert doc["stop_reason"] == "budget_exhausted_dispatches"
    assert len(doc["requests"]) == 1  # sample 1 never started
    assert doc["requests"][0]["outcome"] == "failed"
    assert doc["requests"][0]["adapter_reported_cycles"] == 2
    assert doc["transport_boundary"]["attempted_calls"] == 2
    assert doc["transport_boundary"]["pre_dispatch_failures"] == 2
    assert doc["transport_boundary"]["remaining_dispatches"] == 0


# ---------------------------------------------------------------------------
# direct native composition
# ---------------------------------------------------------------------------

def test_direct_trial_happy_path_template_work_counts(server, tmp_path):
    srv = server(native_scenario(["native-1", "native-2", "native-1"]))
    cfg = write_file(tmp_path, direct_config(srv.port), "direct-config.json")
    spec = write_file(tmp_path, direct_spec_dict(budgets={
        "deadline_seconds": 20, "max_dispatches": 10,
        "max_output_tokens_total": 30}), "direct-spec.json")
    result = run_cli(qual_argv(cfg, spec))
    assert result.returncode == 0, result.stdout + result.stderr
    doc = json.loads(result.stdout)
    # exact native wire: template work + completion per sample
    assert srv.paths == ["/apply-template", "/completion"] * 3
    assert doc["status"] == "complete"
    assert doc["backend"] == "direct"
    assert doc["transport_boundary"]["attempted_calls"] == 6
    assert doc["transport_boundary"]["calls_by_kind"] == {
        "model_dispatch": 3, "template_work": 3}
    assert [s["outcome"] for s in doc["requests"]] == \
        ["terminal", "terminal", "terminal"]
    # native reported metrics map with the correct boundaries:
    # template time is part of caller wall, never TTFT; prefill/decode
    # are the dialect's reported model phases.
    assert doc["requests"][0]["timings"]["ttft_seconds"] is None
    assert doc["requests"][0]["timings"]["prefill_seconds"] == 0.02
    assert doc["requests"][0]["timings"]["decode_seconds"] == 0.04
    assert doc["requests"][0]["usage"]["input_tokens"] == 4
    assert doc["identities"]["declared"]["template_build_id"] == \
        "build-trial-1"
    assert doc["target_type"] == "unverified"


def test_direct_trial_budget3_native_boundary(server, tmp_path):
    # The budget-3 native boundary (004-a verification): template calls
    # count against the ONE shared allowance. sample 0 =
    # template(1)+completion(2); the remaining allowance (1) is below
    # the native minimum (template+completion = 2), so no further
    # sample is STARTED (never a half-dispatched sample) and the trial
    # stops with the exact stop reason.
    srv = server(native_scenario(["native-1", "native-2"]))
    cfg = write_file(tmp_path, direct_config(srv.port), "direct-config.json")
    spec = write_file(tmp_path, direct_spec_dict(
        warmups=0, repetitions=3, budgets={
            "deadline_seconds": 20, "max_dispatches": 3,
            "max_output_tokens_total": 15}), "direct-spec.json")
    result = run_cli(qual_argv(cfg, spec))
    assert result.returncode == 1, result.stdout + result.stderr
    doc = json.loads(result.stdout)
    assert doc["status"] == "incomplete"
    assert doc["stop_reason"] == "budget_exhausted_dispatches"
    assert [s["outcome"] for s in doc["requests"]] == ["terminal"]
    assert doc["transport_boundary"]["attempted_calls"] == 2
    assert doc["transport_boundary"]["calls_by_kind"] == {
        "model_dispatch": 1, "template_work": 1}
    assert doc["transport_boundary"]["remaining_dispatches"] == 1
    assert srv.count("/apply-template") == 1
    assert srv.count("/completion") == 1


def test_direct_trial_budget4_native_boundary_full(server, tmp_path):
    # The budget-4 native boundary completes exactly 2 samples: each
    # native sample consumes template + completion from the ONE shared
    # allowance (the template work is never free).
    srv = server(native_scenario(["native-1", "native-2"]))
    cfg = write_file(tmp_path, direct_config(srv.port), "direct-config.json")
    spec = write_file(tmp_path, direct_spec_dict(
        warmups=0, repetitions=3, budgets={
            "deadline_seconds": 20, "max_dispatches": 4,
            "max_output_tokens_total": 15}), "direct-spec.json")
    result = run_cli(qual_argv(cfg, spec))
    assert result.returncode == 1, result.stdout + result.stderr
    doc = json.loads(result.stdout)
    assert doc["status"] == "incomplete"
    assert doc["stop_reason"] == "budget_exhausted_dispatches"
    assert [s["outcome"] for s in doc["requests"]] == ["terminal", "terminal"]
    assert doc["transport_boundary"]["attempted_calls"] == 4
    assert doc["transport_boundary"]["calls_by_kind"] == {
        "model_dispatch": 2, "template_work": 2}
    assert doc["transport_boundary"]["remaining_dispatches"] == 0
    assert srv.count("/apply-template") == 2
    assert srv.count("/completion") == 2


# ---------------------------------------------------------------------------
# preflight: zero dispatch on invalid identity/settings/output
# ---------------------------------------------------------------------------

def test_trial_preflight_model_mismatch_zero_dispatch(server, tmp_path):
    srv = server(gateway_scenario([TRIAL_TEXT_1]))
    cfg = write_file(tmp_path, gateway_config(srv.port), "gw-config.json")
    spec = write_spec(tmp_path, declared_model="some-other-model")
    result = run_cli(qual_argv(cfg, spec))
    assert result.returncode == 2, result.stdout + result.stderr
    doc = json.loads(result.stdout)
    assert doc["error"] == "TRIAL_PREFLIGHT_REFUSED"
    assert any("declared_model" in reason for reason in doc["reasons"])
    assert srv.state.requests == []  # zero HTTP


def test_trial_preflight_fingerprint_mismatch_zero_dispatch(server,
                                                            tmp_path):
    srv = server(gateway_scenario([TRIAL_TEXT_1]))
    cfg = write_file(tmp_path, gateway_config(srv.port), "gw-config.json")
    wrong_fp = trial_workload_fingerprint(
        parent=PARENT + "tampered", suffixes=list(SUFFIXES), seed=21,
        warmups=1, repetitions=2)
    spec = write_spec(tmp_path, workload_fingerprint=wrong_fp)
    result = run_cli(qual_argv(cfg, spec))
    assert result.returncode == 2, result.stdout + result.stderr
    doc = json.loads(result.stdout)
    assert doc["error"] == "TRIAL_PREFLIGHT_REFUSED"
    assert any("workload_fingerprint" in reason for reason in doc["reasons"])
    assert srv.state.requests == []


def test_trial_missing_route_gives_exact_not_run(server, tmp_path):
    srv = server(gateway_scenario([TRIAL_TEXT_1]))
    config = gateway_config(srv.port)
    del config["generator"]["route"]
    cfg = write_file(tmp_path, config, "no-route-config.json")
    spec = write_spec(tmp_path)
    result = run_cli(qual_argv(cfg, spec))
    assert result.returncode == 2, result.stdout + result.stderr
    doc = json.loads(result.stdout)
    assert doc["error"] == "TRIAL_PREFLIGHT_REFUSED"
    assert any("generator.route" in reason for reason in doc["reasons"])
    assert srv.state.requests == []


def test_trial_direct_mode_refused_when_gateway_only(server, tmp_path):
    srv = server(gateway_scenario([TRIAL_TEXT_1]))
    cfg = write_file(tmp_path, gateway_config(srv.port), "gw-config.json")
    spec = write_file(tmp_path, direct_spec_dict(), "direct-spec.json")
    result = run_cli(qual_argv(cfg, spec))
    assert result.returncode == 2, result.stdout + result.stderr
    doc = json.loads(result.stdout)
    assert doc["error"] == "TRIAL_PREFLIGHT_REFUSED"
    assert any("direct_generation" in reason for reason in doc["reasons"])
    assert srv.state.requests == []


def test_trial_invalid_spec_refused_zero_dispatch(server, tmp_path):
    srv = server(gateway_scenario([TRIAL_TEXT_1]))
    cfg = write_file(tmp_path, gateway_config(srv.port), "gw-config.json")
    spec = write_spec(tmp_path, concurrency=2)
    result = run_cli(qual_argv(cfg, spec))
    assert result.returncode == 2, result.stdout + result.stderr
    doc = json.loads(result.stdout)
    assert doc["error"] == "SPEC_INVALID"
    assert "concurrency" in doc["message"]
    assert srv.state.requests == []


def test_trial_invalid_output_dir_refused_before_dispatch(server,
                                                          tmp_path):
    srv = server(gateway_scenario([TRIAL_TEXT_1]))
    cfg = write_file(tmp_path, gateway_config(srv.port), "gw-config.json")
    spec = write_spec(tmp_path)
    result = run_cli(qual_argv(cfg, spec, extra=[
        "--output", str(tmp_path / "missing-dir" / "evidence.json")]))
    assert result.returncode == 2, result.stdout + result.stderr
    err = json.loads(result.stdout)
    assert err["error"] == "OUTPUT_DESTINATION_INVALID"
    assert "refused before any dispatch" in err["message"]
    assert srv.state.requests == []  # zero HTTP


def test_trial_late_output_write_failure_is_honest_post_work_stage(
        server, tmp_path):
    # The pre-dispatch destination check passes; actual POSTs happen;
    # then the evidence directory is removed before the write. Honest
    # export-stage error (exit 3, NOT a zero-dispatch usage 2) with the
    # full evidence — including the spent-attempt ledger — on stdout.
    import shutil
    out_dir = tmp_path / "evidence-dir"
    out_dir.mkdir()
    out_file = out_dir / "evidence.json"
    state = {"n": 0}

    def scenario(h, r):
        state["n"] += 1
        if state["n"] == 3:
            shutil.rmtree(out_dir)
        text = [TRIAL_TEXT_1, TRIAL_TEXT_2][min(state["n"] - 1, 1)]
        h._send_json(200, completed_json([message_item("m0", text)]))

    srv = server(scenario)
    cfg = write_file(tmp_path, gateway_config(srv.port), "gw-config.json")
    spec = write_spec(tmp_path)
    result = run_cli(qual_argv(cfg, spec, extra=["--output", str(out_file)]))
    assert result.returncode == 3, result.stdout + result.stderr
    doc = json.loads(result.stdout)
    assert doc["status"] == "complete"
    assert doc["transport_boundary"]["attempted_calls"] == 3
    assert doc["transport_boundary"]["responses_received"] == 3
    assert srv.count("/v1/responses") == 3
    err = json.loads(result.stderr)
    assert err["error"] == "EVIDENCE_EXPORT_FAILED"
    assert err["stage"] == "post_work_evidence_export"
    assert "do not replay blindly" in err["message"]
    assert not out_file.exists()


# ---------------------------------------------------------------------------
# outcome/metric ambiguity: raw facts only, no positive evidence
# ---------------------------------------------------------------------------

def test_trial_contradictory_cache_counters_are_raw_facts_only(
        server, tmp_path):
    # Reported cached 999 > input 5: the relation is contradictory.
    # Preserved as raw facts; cannot become positive cache evidence.
    srv = server(gateway_scenario([TRIAL_TEXT_1, TRIAL_TEXT_2, TRIAL_TEXT_1],
                                  cached_tokens=999, input_tokens=5))
    cfg = write_file(tmp_path, gateway_config(srv.port), "gw-config.json")
    spec = write_spec(tmp_path)
    result = run_cli(qual_argv(cfg, spec))
    assert result.returncode == 0, result.stdout + result.stderr
    doc = json.loads(result.stdout)
    consistency = doc["accounting"]["cache_input_consistency"]
    assert consistency["contradictory_samples"] == 3
    assert consistency["consistent_samples"] == 0
    assert all(s["usage"]["cache_hit_tokens"] == 999
               for s in doc["requests"])
    assert all(s["usage"]["input_tokens"] == 5 for s in doc["requests"])
    assert doc["qualification_status"] == "NOT_QUALIFIED"
    assert "raw facts" in consistency["note"]


def test_trial_missing_usage_stays_null(server, tmp_path):
    srv = server(gateway_scenario([TRIAL_TEXT_1], with_usage=False))
    cfg = write_file(tmp_path, gateway_config(srv.port), "gw-config.json")
    spec = write_spec(tmp_path, warmups=0, repetitions=1, budgets={
        "deadline_seconds": 20, "max_dispatches": 2,
        "max_output_tokens_total": 5})
    result = run_cli(qual_argv(cfg, spec))
    assert result.returncode == 0, result.stdout + result.stderr
    doc = json.loads(result.stdout)
    assert doc["requests"][0]["usage"] == {
        "input_tokens": None, "output_tokens": None,
        "prefill_tokens": None, "cache_hit_tokens": None}
    # zero terminal-free/unknown usage never becomes a synthetic zero
    assert doc["accounting"]["cache_input_consistency"] == {
        "consistent_samples": 0, "contradictory_samples": 0,
        "uncheckable_samples": 0,
        "note": doc["accounting"]["cache_input_consistency"]["note"]}


# ---------------------------------------------------------------------------
# deterministic explicit synthetic route (MOCK, owned fixture)
# ---------------------------------------------------------------------------

def test_synthetic_trial_deterministic_mock_route(tmp_path):
    cfg = write_file(tmp_path, gateway_config(1), "gw-config.json")
    spec = write_spec(tmp_path)
    result_a = run_cli(qual_argv(cfg, spec, extra=["--synthetic"]))
    assert result_a.returncode == 0, result_a.stdout + result_a.stderr
    doc_a = json.loads(result_a.stdout)
    assert doc_a["status"] == "complete"
    assert doc_a["evidence_class"] == "MOCK"
    assert doc_a["target_type"] == "synthetic-owned-fixture"
    assert doc_a["qualification_status"] == "NOT_QUALIFIED"
    assert doc_a["transport_boundary"]["attempted_calls"] == 3
    assert [s["outcome"] for s in doc_a["requests"]] == \
        ["terminal", "terminal", "terminal"]
    # deterministic fixture usage, reported-only accounting
    assert all(s["usage"] == {"input_tokens": 12, "output_tokens": 3,
                              "prefill_tokens": None,
                              "cache_hit_tokens": None}
               for s in doc_a["requests"])
    # no real credential was read (no env provided at all)
    assert doc_a["credentials"]["api_key_ref"] == {"kind": "synthetic-canary"}

    result_b = run_cli(qual_argv(cfg, spec, extra=["--synthetic"]))
    assert result_b.returncode == 0
    doc_b = json.loads(result_b.stdout)
    # identical inputs -> identical evidence apart from per-run
    # wall-clock measurements (see strip_wall)
    assert strip_wall(doc_a) == strip_wall(doc_b)
    # synthetic provenance is explicit, never a live/readiness claim
    blob = result_a.stdout
    assert '"live"' not in blob
    assert "MOCK" in blob
    assert doc_a["gates"]["real_trials"] == "NOT_RUN"


def test_synthetic_direct_trial_deterministic_mock_route(tmp_path):
    cfg = write_file(tmp_path, direct_config(1), "direct-config.json")
    spec = write_file(tmp_path, direct_spec_dict(), "direct-spec.json")
    result_a = run_cli(qual_argv(cfg, spec, extra=["--synthetic"]))
    assert result_a.returncode == 0, result_a.stdout + result_a.stderr
    doc_a = json.loads(result_a.stdout)
    assert doc_a["status"] == "complete"
    assert doc_a["evidence_class"] == "MOCK"
    assert doc_a["target_type"] == "synthetic-owned-fixture"
    assert doc_a["transport_boundary"]["calls_by_kind"] == {
        "model_dispatch": 3, "template_work": 3}
    result_b = run_cli(qual_argv(cfg, spec, extra=["--synthetic"]))
    assert result_b.returncode == 0
    assert strip_wall(json.loads(result_a.stdout)) == \
        strip_wall(json.loads(result_b.stdout))


def test_configured_loopback_url_never_synthetic(server, tmp_path):
    # A configured loopback destination under the NON-synthetic route
    # keeps the unverified classification: no boolean makes a configured
    # URL an owned/verified synthetic endpoint.
    srv = server(gateway_scenario([TRIAL_TEXT_1, TRIAL_TEXT_2]))
    cfg = write_file(tmp_path, gateway_config(srv.port), "gw-config.json")
    spec = write_spec(tmp_path, warmups=0, repetitions=1, budgets={
        "deadline_seconds": 20, "max_dispatches": 2,
        "max_output_tokens_total": 5})
    result = run_cli(qual_argv(cfg, spec))
    assert result.returncode == 0, result.stdout + result.stderr
    doc = json.loads(result.stdout)
    assert doc["evidence_class"] == "CONFIGURED_UNVERIFIED"
    assert doc["target_type"] == "unverified"
    assert doc["target_type_note"].startswith(
        "the runner cannot classify the configured destination")


# ---------------------------------------------------------------------------
# zero-I/O planning/gates/help
# ---------------------------------------------------------------------------

def test_plan_and_gates_are_zero_io_on_closed_port(closed_port, tmp_path):
    # The configured route points at a CLOSED port: planning, gates and
    # help must succeed with zero model/HTTP/telemetry I/O.
    cfg = write_file(tmp_path, gateway_config(closed_port),
                     "gw-config.json")
    spec = write_spec(tmp_path)
    plan = run_cli(qual_argv(cfg, spec, sub="plan"))
    assert plan.returncode == 0, plan.stdout + plan.stderr
    doc = json.loads(plan.stdout)
    assert doc["status"] == "PLAN"
    assert doc["execution"].startswith("NOT_RUN")
    assert doc["zero_dispatch"] is True

    gates = run_cli(["qualification", "gates"])
    assert gates.returncode == 0, gates.stdout + gates.stderr
    gate_doc = json.loads(gates.stdout)
    assert set(gate_doc["gates"]) == {
        "GATEWAY-01", "GATEWAY-02", "GATEWAY-03", "DIRECT-01",
        "V100-MEM-01", "V100-MEM-02", "RERANK-01", "EMBED-01",
        "EMBED-02", "ONLINE-01", "ONLINE-02", "OPS-01", "OPS-02",
        "LICENSE-01"}
    assert all(g["status"] == "NOT_RUN" for g in gate_doc["gates"].values())

    help_result = run_cli(["qualification", "run", "--help"])
    assert help_result.returncode == 0
    assert "--synthetic" in help_result.stdout


def test_plan_rejection_is_honest_and_offline(server, tmp_path):
    srv = server(gateway_scenario([TRIAL_TEXT_1]))
    cfg = write_file(tmp_path, gateway_config(srv.port), "gw-config.json")
    spec = write_spec(tmp_path, declared_model="wrong-model")
    plan = run_cli(qual_argv(cfg, spec, sub="plan"))
    assert plan.returncode == 2, plan.stdout + plan.stderr
    doc = json.loads(plan.stdout)
    assert doc["status"] == "PLAN_REJECTED"
    assert doc["zero_dispatch"] is True
    assert srv.state.requests == []


def test_provider_error_canary_never_reaches_evidence(server, tmp_path):
    def error_scenario(h, r):
        h._send_json(500, {"error": {"message": TRIAL_PROVIDER_CANARY}})

    srv = server(error_scenario)
    cfg = write_file(tmp_path, gateway_config(srv.port, **{"max_retries": 0}),
                     "gw-config.json")
    spec = write_spec(tmp_path, budgets={
        "deadline_seconds": 20, "max_dispatches": 10,
        "max_output_tokens_total": 30})
    result = run_cli(qual_argv(cfg, spec))
    # Every sample resolved with DEFINITIVE refusals (HTTP 500 headers
    # were read): truthful failed evidence, complete execution status,
    # and never a qualifying pass.
    assert result.returncode == 0
    doc = json.loads(result.stdout)
    assert doc["status"] == "complete"
    assert all(s["outcome"] == "failed" for s in doc["requests"])
    assert TRIAL_PROVIDER_CANARY not in result.stdout
    assert doc["qualification_status"] == "NOT_QUALIFIED"
    assert srv.count("/v1/responses") == 3
