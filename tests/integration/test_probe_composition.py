"""Real probe composition: installed CLI + real adapters over owned loopback.

Acceptance coverage (oap/orders/003-h criteria 1, 2, 3, 5, 6): the
INSTALLED ``raggedized`` CLI runs in a subprocess; the real
GatewayGenerator/DirectNativeGenerator adapters speak to owned
127.0.0.1 loopback servers that record exact paths/order/bodies. We
assert exact request counts and order, control payloads, finite
aggregate budgets (deadline + call allowance) across the pair and
retries, no implicit dispatch (import/help/doctor/missing opt-in),
missing-metric nulls, mismatched outputs, unknown-completion no-replay,
secret/provider canary safety and invalid-config refusals before
dispatch. All fixtures are synthetic; no live model, real key, GPU or
corpus (order live authorization: NONE).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

from conftest import SYNTHETIC_API_KEY  # noqa: F401  (suite parity)
from test_gateway_generator import completed_json, message_item

from slaif_raggedized_helper.config import RouteCapabilities
from slaif_raggedized_helper.probes import (
    PROBE_PARENT,
    PROBE_SUFFIX_A,
    PROBE_SUFFIX_B,
)
from slaif_raggedized_helper.schema import fingerprint

# Unique synthetic canaries for this suite (never real credentials/data).
PROBE_KEY_CANARY = "sk-probe-canary-003h-DO-NOT-LEAK"
PROBE_PROVIDER_CANARY = "PROVIDER-ERROR-CANARY-003h"
PROBE_TEXT_A = "synthetic probe answer A"
PROBE_TEXT_B = "synthetic probe answer B"

REPO_ROOT = Path(__file__).resolve().parents[2]


def _cli_binary() -> str:
    # The venv interpreter is usually a symlink to the system python, so
    # do NOT resolve: the installed console script lives next to the venv
    # interpreter path.
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


def write_config(tmp_path: Path, doc: dict) -> Path:
    path = tmp_path / "probe-config.json"
    path.write_text(json.dumps(doc), encoding="utf-8")
    return path


def gateway_config(port: int, *, caps=None, api_key_ref: str | None = None,
                   **gen_kwargs) -> dict:
    route = {"base_url": f"http://127.0.0.1:{port}/v1",
             "model": "synthetic-probe-gw", "api": "v1-responses",
             "timeout_seconds": 5}
    if caps is not None:
        route["capabilities"] = caps.model_dump()
    generator = {
        "route": route,
        "context_expected_tokens": 1024,
        "output_reserve_tokens": 64,
        "deadline_seconds": 30,
        **gen_kwargs,
    }
    doc = {
        "schema_version": 1,
        "generator": generator,
    }
    if api_key_ref is not None:
        generator["api_key_ref"] = api_key_ref
        doc["secrets"] = {api_key_ref: {"kind": "env",
                                        "name": "PROBE_003H_KEY"}}
    return doc


def direct_config(port: int, *, capabilities=None, max_retries: int = 0) -> dict:
    doc = {
        "mode": "offline_diagnostic",
        "destination": {"base_url": f"http://127.0.0.1:{port}"},
        "trusted_policy": "private_trusted",
        "capabilities": capabilities or {},
        "model": "synthetic-probe-native",
        "chat_template": None,
        "template_qualification": {
            "template": None, "build_id": "build-probe-1",
            "method": "apply-template",
            "recorded_at": "2026-11-10T00:00:00+00:00",
        },
        "max_output_tokens": 64,
        "deadline_seconds": 30,
        "max_retries": max_retries,
    }
    return {
        "schema_version": 1,
        "generator": {"context_expected_tokens": 1024,
                      "output_reserve_tokens": 64,
                      "deadline_seconds": 30},
        "direct_generation": doc,
    }


def probe_argv(config_path: Path, mode: str, *, deadline: float = 20.0,
               dispatches: int = 8, total_tokens: int = 32,
               extra: list[str] | None = None) -> list[str]:
    argv = ["probe", "--config", str(config_path), "--mode", mode,
            "--deadline-seconds", str(deadline),
            "--max-dispatches", str(dispatches),
            "--max-output-tokens-total", str(total_tokens)]
    return argv + (extra or [])


def gateway_scenario(text_a: str, text_b: str, *, with_usage: bool = True):
    state = {"n": 0}

    def scenario(h, r):
        state["n"] += 1
        text = text_a if state["n"] == 1 else text_b
        usage = ({"input_tokens": 11, "output_tokens": 5}
                 if with_usage else None)
        h._send_json(200, completed_json([message_item("m0", text)],
                                         usage=usage))
    return scenario


def native_scenario(text_a: str, text_b: str, *, cache_n_a: int = 4,
                    cache_n_b: int = 6, with_timings: bool = True):
    state = {"completion": 0}

    def scenario(h, r):
        body = json.loads(r.body)
        if r.path == "/apply-template":
            user_text = body["messages"][-1]["content"]
            h._send_json(200, {"prompt": "rendered::" + user_text})
            return
        state["completion"] += 1
        second = state["completion"] == 2
        text = text_b if second else text_a
        cache_n = cache_n_b if second else cache_n_a
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


# ---------------------------------------------------------------------------
# gateway composition
# ---------------------------------------------------------------------------

def test_gateway_probe_happy_path_with_credential_reference(
        server, tmp_path):
    srv = server(gateway_scenario(PROBE_TEXT_A, PROBE_TEXT_B))
    cfg = write_config(tmp_path, gateway_config(
        srv.port, api_key_ref="probe_key"))
    digest_a = fingerprint({"kind": "probe-response-text", "label": "a",
                            "text": PROBE_TEXT_A})
    digest_b_wrong = fingerprint({"kind": "probe-response-text", "label": "b",
                                  "text": "something else entirely"})
    result = run_cli(probe_argv(cfg, "gateway", extra=[
        "--expected-output-a", digest_a,
        "--expected-output-b", digest_b_wrong,
    ]), env={**os.environ, "PROBE_003H_KEY": PROBE_KEY_CANARY})
    assert result.returncode == 0, result.stdout + result.stderr
    doc = json.loads(result.stdout)

    # exact wire: two POSTs in phase order, canary only in the header
    assert srv.paths == ["/v1/responses", "/v1/responses"]
    for record in srv.state.requests:
        assert record.headers.get("authorization") == \
            f"Bearer {PROBE_KEY_CANARY}"
        assert PROBE_KEY_CANARY not in record.body.decode("utf-8")
    body_a = json.loads(srv.state.requests[0].body)
    body_b = json.loads(srv.state.requests[1].body)
    assert body_a["input"][0]["content"][0]["text"] == \
        PROBE_PARENT + PROBE_SUFFIX_A
    assert body_b["input"][0]["content"][0]["text"] == \
        PROBE_PARENT + PROBE_SUFFIX_B
    assert body_a["max_output_tokens"] == 16  # 32 total // 2
    assert "prompt_cache_key" not in body_a  # no qualified cache capability

    # evidence: complete, safe, truthful
    assert doc["status"] == "complete"
    assert doc["mode"] == "gateway"
    assert doc["live"] is False
    assert doc["requests"]["a"]["outcome"] == "terminal"
    assert doc["requests"]["b"]["outcome"] == "terminal"
    assert doc["requests"]["a"]["usage"] == {
        "input_tokens": 11, "output_tokens": 5,
        "prefill_tokens": None, "cache_hit_tokens": None}
    assert doc["requests"]["a"]["timings"]["ttft_seconds"] is None
    assert doc["requests"]["a"]["expected_output_check"] == "match"
    assert doc["requests"]["b"]["expected_output_check"] == "mismatch"
    assert doc["transport_boundary"] == {
        "attempted_calls": 2,
        "calls_by_kind": {"model_dispatch": 2, "template_work": 0},
        "responses_received": 2,
        "ambiguous_dispatches": 0,
        "pre_dispatch_failures": 0,
        "remaining_dispatches": 6,
    }
    assert doc["identities"]["credentials"] == {
        "api_key_ref": {"kind": "env", "name": "PROBE_003H_KEY"},
        "resolved": True}
    assert doc["identities"]["runtime_identity"] == "unverified"
    assert doc["identities"]["declared_model"] == "synthetic-probe-gw"
    # safe evidence: no URL, no key, no raw text, no provider content
    blob = result.stdout
    assert str(srv.port) not in blob
    assert "127.0.0.1" not in blob
    assert PROBE_KEY_CANARY not in blob
    assert PROBE_TEXT_A not in blob
    assert PROBE_TEXT_B not in blob
    assert PROBE_PARENT not in blob
    assert PROBE_PROVIDER_CANARY not in blob
    assert doc["experiment"]["cold_state"] == "unknown"
    assert doc["cache_evidence"]["conclusion"] == "no_cache_control"


def test_gateway_probe_qualified_cache_control_is_stable_but_unqualified(
        server, tmp_path):
    srv = server(gateway_scenario(PROBE_TEXT_A, PROBE_TEXT_B))
    cfg = write_config(tmp_path, gateway_config(
        srv.port, caps=RouteCapabilities(prompt_caching=True)))
    result = run_cli(probe_argv(cfg, "gateway"))
    assert result.returncode == 0, result.stdout + result.stderr
    doc = json.loads(result.stdout)
    keys = [json.loads(r.body).get("prompt_cache_key")
            for r in srv.state.requests]
    assert len(set(keys)) == 1 and keys[0] and len(keys[0]) <= 128
    assert doc["experiment"]["cache_control"] == {
        "kind": "prompt_cache_key", "qualified": True,
        "key_fingerprint": doc["experiment"]["cache_control"]
        ["key_fingerprint"]}
    assert doc["experiment"]["cache_control"]["key_fingerprint"].startswith(
        "sha256:")
    # the gateway dialect never reports prefill/cache metrics
    assert doc["cache_evidence"]["conclusion"] == "metrics_unavailable"
    assert doc["cache_evidence"]["reported_prefill_tokens"] == \
        {"a": None, "b": None}


def test_gateway_probe_missing_metrics_stay_null(server, tmp_path):
    srv = server(gateway_scenario(PROBE_TEXT_A, PROBE_TEXT_B,
                                  with_usage=False))
    cfg = write_config(tmp_path, gateway_config(srv.port))
    result = run_cli(probe_argv(cfg, "gateway"))
    assert result.returncode == 0, result.stdout + result.stderr
    doc = json.loads(result.stdout)
    for label in ("a", "b"):
        assert doc["requests"][label]["usage"] == {
            "input_tokens": None, "output_tokens": None,
            "prefill_tokens": None, "cache_hit_tokens": None}
    # no synthetic zero: nulls are recorded, conclusion stays unqualified
    assert doc["cache_evidence"]["reported_input_tokens"] == \
        {"a": None, "b": None}


def test_gateway_probe_dispatch_allowance_exhausted_across_pair(
        server, tmp_path):
    srv = server(gateway_scenario(PROBE_TEXT_A, PROBE_TEXT_B))
    cfg = write_config(tmp_path, gateway_config(srv.port))
    result = run_cli(probe_argv(cfg, "gateway", dispatches=1))
    assert result.returncode == 1, result.stdout + result.stderr
    doc = json.loads(result.stdout)
    assert doc["status"] == "incomplete"
    assert doc["stop_reason"] == "budget_exhausted_dispatches"
    assert doc["requests"]["a"]["outcome"] == "terminal"
    assert doc["requests"]["b"] is None
    assert srv.count("/v1/responses") == 1  # B was never dispatched
    assert doc["transport_boundary"]["remaining_dispatches"] == 0


def test_gateway_probe_deadline_exhausted_during_first_call(
        server, tmp_path):
    def slow_scenario(h, r):
        time.sleep(1.5)  # past the 0.6s experiment deadline
        h._send_json(200, completed_json([message_item("m0", "late")]))

    srv = server(slow_scenario)
    cfg = write_config(tmp_path, gateway_config(srv.port))
    start = time.monotonic()
    result = run_cli(probe_argv(cfg, "gateway", deadline=0.6, dispatches=4),
                     timeout=30)
    elapsed = time.monotonic() - start
    assert result.returncode == 1, result.stdout + result.stderr
    doc = json.loads(result.stdout)
    assert doc["status"] == "incomplete"
    assert doc["stop_reason"] == "budget_exhausted_deadline"
    assert doc["requests"]["a"]["outcome"] == "unknown_completion"
    assert doc["requests"]["b"] is None
    assert srv.count("/v1/responses") == 1  # no replay of the slow call
    assert doc["transport_boundary"]["ambiguous_dispatches"] == 1
    # the experiment stopped at its own deadline, not the server delay
    assert elapsed < 3.0


def test_gateway_probe_unknown_completion_is_never_replayed(server, tmp_path):
    state = {"n": 0}

    def scenario(h, r):
        state["n"] += 1
        if state["n"] == 1:
            h._accept_then_close()  # ambiguous: the request may have run
        else:
            h._send_json(200, completed_json(
                [message_item("m0", PROBE_TEXT_B)]))

    srv = server(scenario)
    cfg = write_config(tmp_path, gateway_config(srv.port))
    result = run_cli(probe_argv(cfg, "gateway", dispatches=4))
    assert result.returncode == 0, result.stdout + result.stderr
    doc = json.loads(result.stdout)
    assert doc["status"] == "complete"
    assert doc["requests"]["a"]["outcome"] == "unknown_completion"
    assert doc["requests"]["a"]["adapter_reported_cycles"] == 1
    assert doc["requests"]["b"]["outcome"] == "terminal"
    assert srv.paths == ["/v1/responses", "/v1/responses"]  # no duplicate
    assert doc["transport_boundary"]["ambiguous_dispatches"] == 1
    assert doc["transport_boundary"]["responses_received"] == 1


# ---------------------------------------------------------------------------
# direct composition
# ---------------------------------------------------------------------------

def test_direct_probe_happy_path_exact_order_and_envelopes(server, tmp_path):
    srv = server(native_scenario(PROBE_TEXT_A, PROBE_TEXT_B,
                                 cache_n_a=4, cache_n_b=0))
    # no cache_prompt_tested capability: no cache control is used at all
    cfg = write_config(tmp_path, direct_config(srv.port))
    result = run_cli(probe_argv(cfg, "direct", total_tokens=32))
    assert result.returncode == 0, result.stdout + result.stderr
    doc = json.loads(result.stdout)

    # exact path order: template + completion per phase, in order
    assert srv.paths == ["/apply-template", "/completion",
                         "/apply-template", "/completion"]
    tmpl_a = json.loads(srv.state.requests[0].body)
    comp_a = json.loads(srv.state.requests[1].body)
    tmpl_b = json.loads(srv.state.requests[2].body)
    comp_b = json.loads(srv.state.requests[3].body)
    # the server-rendered prompt carries the full phase input (raw wire)
    assert tmpl_a["messages"] == [
        {"role": "user", "content": PROBE_PARENT + PROBE_SUFFIX_A}]
    assert tmpl_b["messages"] == [
        {"role": "user", "content": PROBE_PARENT + PROBE_SUFFIX_B}]
    assert comp_a["prompt"].endswith(PROBE_PARENT + PROBE_SUFFIX_A)
    assert comp_b["prompt"].endswith(PROBE_PARENT + PROBE_SUFFIX_B)
    for comp in (comp_a, comp_b):
        assert comp["n_predict"] == 16  # 32 total // 2
        assert comp["stream"] is False
        assert "cache_prompt" not in comp  # capability not tested
        assert "id_slot" not in comp

    # boundary accounting separates model dispatches from template work
    assert doc["status"] == "complete"
    assert doc["transport_boundary"]["calls_by_kind"] == {
        "model_dispatch": 2, "template_work": 2}
    assert doc["requests"]["a"]["usage"] == {
        "input_tokens": 8, "output_tokens": 3,
        "prefill_tokens": 4, "cache_hit_tokens": 4}
    assert doc["requests"]["b"]["usage"]["cache_hit_tokens"] == 0
    # no qualified cache control was used: the conclusion is
    # no_cache_control (reported metrics alone never prove caching)
    assert doc["cache_evidence"]["conclusion"] == "no_cache_control"
    assert doc["identities"]["template_build_id"] == "build-probe-1"
    assert doc["identities"]["slot_control"] == {
        "slot_id": None, "slot_tested": False}
    blob = result.stdout
    assert str(srv.port) not in blob and "127.0.0.1" not in blob
    assert PROBE_TEXT_A not in blob and PROBE_TEXT_B not in blob


@pytest.mark.parametrize("cache_n_b, conclusion", [
    (0, "no_cache_hit_reported"),   # measured zero: a known zero, not null
    (6, "cache_hit_reported"),
])
def test_direct_probe_qualified_cache_control_reaches_the_wire(
        server, tmp_path, cache_n_b, conclusion):
    srv = server(native_scenario(PROBE_TEXT_A, PROBE_TEXT_B,
                                 cache_n_a=0, cache_n_b=cache_n_b))
    cfg = write_config(tmp_path, direct_config(
        srv.port, capabilities={"cache_prompt_tested": True}))
    result = run_cli(probe_argv(cfg, "direct"))
    assert result.returncode == 0, result.stdout + result.stderr
    doc = json.loads(result.stdout)
    for r in srv.state.requests:
        if r.path == "/completion":
            assert json.loads(r.body)["cache_prompt"] is True
    assert doc["experiment"]["cache_control"]["kind"] == "cache_prompt"
    assert doc["experiment"]["cache_control"]["qualified"] is True
    assert doc["cache_evidence"]["conclusion"] == conclusion
    assert doc["cache_evidence"]["reported_cache_hit_tokens"]["b"] == cache_n_b


def test_direct_probe_budget_exhaustion_with_retry_at_closed_port(
        closed_port, tmp_path):
    cfg = write_config(tmp_path, direct_config(closed_port,
                                               max_retries=2))
    result = run_cli(probe_argv(cfg, "direct", dispatches=3, deadline=20.0))
    assert result.returncode == 1, result.stdout + result.stderr
    doc = json.loads(result.stdout)
    # A burns the finite allowance on pre-dispatch template failures
    # (3 attempts, finite); B never starts: explicit incomplete.
    assert doc["status"] == "incomplete"
    assert doc["stop_reason"] == "budget_exhausted_dispatches"
    assert doc["requests"]["a"]["outcome"] == "failed"
    assert doc["requests"]["a"]["adapter_reported_cycles"] == 3
    assert doc["requests"]["b"] is None
    assert doc["transport_boundary"]["attempted_calls"] == 3
    assert doc["transport_boundary"]["pre_dispatch_failures"] == 3
    assert doc["transport_boundary"]["remaining_dispatches"] == 0


def test_direct_probe_ambiguous_completion_spent_not_replayed(
        server, tmp_path):
    state = {"completion": 0}

    def scenario(h, r):
        body = json.loads(r.body)
        if r.path == "/apply-template":
            h._send_json(200, {"prompt": "rendered::"
                                   + body["messages"][-1]["content"]})
            return
        state["completion"] += 1
        if state["completion"] == 1:
            h._accept_then_close()  # ambiguous first completion
            return
        doc = {"content": PROBE_TEXT_B, "stop": True, "truncated": False,
               "stop_type": "eos", "tokens_evaluated": 8,
               "tokens_predicted": 3,
               "timings": {"prompt_ms": 20.0, "predicted_ms": 40.0,
                           "prompt_n": 4, "cache_n": 4, "predicted_n": 3}}
        h._send_json(200, doc)

    srv = server(scenario)
    cfg = write_config(tmp_path, direct_config(srv.port))
    result = run_cli(probe_argv(cfg, "direct", dispatches=4))
    assert result.returncode == 0, result.stdout + result.stderr
    doc = json.loads(result.stdout)
    assert doc["requests"]["a"]["outcome"] == "unknown_completion"
    assert doc["requests"]["b"]["outcome"] == "terminal"
    # exactly one /completion per phase: the ambiguous call was spent,
    # never replayed
    assert srv.count("/completion") == 2
    assert doc["transport_boundary"]["ambiguous_dispatches"] == 1
    assert doc["transport_boundary"]["calls_by_kind"] == {
        "model_dispatch": 2, "template_work": 2}


# ---------------------------------------------------------------------------
# no implicit dispatch; invalid config before dispatch
# ---------------------------------------------------------------------------

def test_doctor_help_and_missing_optin_never_dispatch(server, tmp_path):
    srv = server(gateway_scenario(PROBE_TEXT_A, PROBE_TEXT_B))
    cfg = write_config(tmp_path, gateway_config(srv.port))
    # doctor: offline by contract
    doctor = run_cli(["doctor", "--config", str(cfg)])
    assert doctor.returncode in (0, 1)
    assert json.loads(doctor.stdout)["route"]["host"] == "127.0.0.1"
    # probe without the explicit budget flags: usage error, zero dispatch
    incomplete = run_cli(["probe", "--config", str(cfg), "--mode", "gateway"])
    assert incomplete.returncode == 2
    # help: zero dispatch
    help_result = run_cli(["--help"])
    assert help_result.returncode == 0
    assert "probe" in help_result.stdout
    assert srv.state.requests == []  # NOTHING reached the server


def test_invalid_config_refuses_before_dispatch(server, tmp_path):
    srv = server(gateway_scenario(PROBE_TEXT_A, PROBE_TEXT_B))
    bad = write_config(tmp_path, {})
    result = run_cli(probe_argv(bad, "gateway"))
    assert result.returncode == 2
    assert json.loads(result.stdout)["error"] in ("CONFIG_INVALID",
                                                  "MODE_NOT_CONFIGURED")
    # direct mode without a template qualification record is a config
    # error, refused before any transport exists
    doc = direct_config(srv.port)
    del doc["direct_generation"]["template_qualification"]
    bad_direct = write_config(tmp_path, doc)
    result2 = run_cli(probe_argv(bad_direct, "direct"))
    assert result2.returncode == 2
    assert json.loads(result2.stdout)["error"] == "CONFIG_INVALID"
    assert srv.state.requests == []


def test_direct_mode_refused_when_gateway_only_config(server, tmp_path):
    srv = server(gateway_scenario(PROBE_TEXT_A, PROBE_TEXT_B))
    cfg = write_config(tmp_path, gateway_config(srv.port))
    result = run_cli(probe_argv(cfg, "direct"))
    assert result.returncode == 2
    assert json.loads(result.stdout)["error"] == "MODE_NOT_CONFIGURED"
    assert srv.state.requests == []


def test_provider_error_canary_never_reaches_evidence(server, tmp_path):
    def error_scenario(h, r):
        h._send_json(500, {"error": {"message": PROBE_PROVIDER_CANARY}})

    srv = server(error_scenario)
    cfg = write_config(tmp_path, gateway_config(srv.port,
                                                **{"max_retries": 0}))
    result = run_cli(probe_argv(cfg, "gateway", dispatches=2))
    # Both phases resolved with DEFINITIVE refusals (HTTP 500 is a
    # positive response, not ambiguous): the bounded experiment completes
    # with truthful failed evidence.
    assert result.returncode == 0
    doc = json.loads(result.stdout)
    assert doc["status"] == "complete"
    assert doc["requests"]["a"]["outcome"] == "failed"
    assert "request refused" in doc["requests"]["a"]["error"]
    assert PROBE_PROVIDER_CANARY not in result.stdout
    assert doc["requests"]["b"]["outcome"] == "failed"
    assert srv.count("/v1/responses") == 2
