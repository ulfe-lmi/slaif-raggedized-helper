"""Bounded probe logic (003-h): budgets, boundary accounting, evidence safety.

Unit-level: synthetic fixtures and an injected fake inner transport
(NO network, NO keys, NO model). Real composition over owned loopback
HTTP lives in tests/integration/test_probe_composition.py.
"""

from __future__ import annotations

import json
import os

import pytest
from pydantic import ValidationError

from slaif_raggedized_helper.config import (
    RaggedizedConfig,
    RouteCapabilities,
    SecretRef,
)
from slaif_raggedized_helper.probes import (
    BudgetedTransport,
    ProbeBudgets,
    _BudgetExhausted,
    resolve_secret_value,
    run_repeated_parent_probe,
)
from slaif_raggedized_helper.model_clients.transport import (
    TransportConnectError,
    TransportError,
)
from slaif_raggedized_helper.schema import fingerprint

CANARY_KEY = "sk-unit-probe-canary-003h"


class FakeInner:
    """Scripted stand-in for the REAL transport at the boundary seam."""

    def __init__(self, script=None):
        # script: list of callables(path, body) -> (status, bytes) or raise
        self.script = script or []
        self.calls: list[tuple[str, bytes]] = []

    def post_json(self, path, body, *, deadline=None):
        self.calls.append((path, body))
        if not self.script:
            raise AssertionError(f"unexpected call {path}")
        behavior = self.script.pop(0)
        return behavior(path, body)

    def open_stream(self, path, body, *, deadline=None):
        raise AssertionError("probe must never open streams")


def gateway_terminal_body(text="unit-answer"):
    return (200, json.dumps({
        "id": "r1", "object": "response", "created_at": 1, "status": "completed",
        "model": "synthetic", "output": [{
            "id": "m1", "type": "message", "status": "completed",
            "role": "assistant",
            "content": [{"type": "output_text", "text": text,
                         "annotations": [], "logprobs": None}],
            "phase": None,
        }],
        "usage": {"input_tokens": 9, "output_tokens": 4},
    }).encode())


def native_terminal_body(text="unit-native", prompt_n=4, cache_n=0):
    return (200, json.dumps({
        "content": text, "stop": True, "truncated": False, "stop_type": "eos",
        "tokens_evaluated": prompt_n + cache_n, "tokens_predicted": 3,
        "timings": {"prompt_ms": 20.0, "predicted_ms": 40.0,
                    "prompt_n": prompt_n, "cache_n": cache_n,
                    "predicted_n": 3},
    }).encode())


def _gateway_config(port=1, caps=None, **gen_kwargs):
    route = {"base_url": f"http://127.0.0.1:{port}/v1",
             "model": "synthetic-gw", "api": "v1-responses",
             "timeout_seconds": 5}
    if caps is not None:
        route["capabilities"] = caps.model_dump()
    return RaggedizedConfig.model_validate({
        "schema_version": 1,
        "generator": {
            "route": route,
            "context_expected_tokens": 1024,
            "output_reserve_tokens": 64,
            "deadline_seconds": 30,
            **gen_kwargs,
        },
    })


def _direct_config(port=1, **overrides):
    doc = {
        "mode": "offline_diagnostic",
        "destination": {"base_url": f"http://127.0.0.1:{port}"},
        "trusted_policy": "private_trusted",
        "capabilities": {},
        "model": "synthetic-native",
        "chat_template": None,
        "template_qualification": {
            "template": None, "build_id": "build-1",
            "method": "apply-template",
            "recorded_at": "2026-11-10T00:00:00+00:00",
        },
        "max_output_tokens": 64,
        "deadline_seconds": 30,
        "max_retries": 0,
    }
    doc.update(overrides)
    return RaggedizedConfig.model_validate({
        "schema_version": 1,
        "generator": {"context_expected_tokens": 1024,
                      "output_reserve_tokens": 64, "deadline_seconds": 30},
        "direct_generation": doc,
    })


def _budgets(deadline=10.0, dispatches=8, total=32):
    return ProbeBudgets(deadline_seconds=deadline, max_dispatches=dispatches,
                        max_output_tokens_total=total)


# ---------------------------------------------------------------------------
# budgets
# ---------------------------------------------------------------------------

def test_budgets_refuse_nonfinite_or_nonpositive():
    with pytest.raises(ValidationError):
        ProbeBudgets(deadline_seconds=float("inf"), max_dispatches=2,
                     max_output_tokens_total=4)
    with pytest.raises(ValidationError):
        ProbeBudgets(deadline_seconds=float("nan"), max_dispatches=2,
                     max_output_tokens_total=4)
    with pytest.raises(ValidationError):
        ProbeBudgets(deadline_seconds=0.0, max_dispatches=2,
                     max_output_tokens_total=4)
    with pytest.raises(ValidationError):
        ProbeBudgets(deadline_seconds=1.0, max_dispatches=0,
                     max_output_tokens_total=4)
    with pytest.raises(ValidationError):
        ProbeBudgets(deadline_seconds=1.0, max_dispatches=2,
                     max_output_tokens_total=1)
    with pytest.raises(ValidationError):
        ProbeBudgets(deadline_seconds=1.0, max_dispatches=2,
                     max_output_tokens_total=4, extra_field=1)


def test_budgets_split_the_pair_evenly_and_never_exceed_the_total():
    assert _budgets(total=10).per_request_output_tokens == 5
    assert _budgets(total=7).per_request_output_tokens == 3
    assert 2 * _budgets(total=7).per_request_output_tokens <= 7


# ---------------------------------------------------------------------------
# secret references
# ---------------------------------------------------------------------------

def test_resolve_secret_env_and_file(tmp_path):
    ref = SecretRef(kind="env", name="PROBE_UNIT_ENV_SECRET")
    assert resolve_secret_value(ref) is None
    os.environ["PROBE_UNIT_ENV_SECRET"] = CANARY_KEY
    try:
        assert resolve_secret_value(ref) == CANARY_KEY
    finally:
        del os.environ["PROBE_UNIT_ENV_SECRET"]
    f = tmp_path / "secret.txt"
    f.write_text("file-secret-value\n", encoding="utf-8")
    fref = SecretRef(kind="file", name=str(f))
    assert resolve_secret_value(fref) == "file-secret-value"
    f.write_text("file-secret-no-newline", encoding="utf-8")
    assert resolve_secret_value(fref) == "file-secret-no-newline"
    f.write_text("\n", encoding="utf-8")
    assert resolve_secret_value(fref) is None
    assert resolve_secret_value(SecretRef(kind="file", name=str(tmp_path / "missing"))) is None


# ---------------------------------------------------------------------------
# mode configuration refusals (zero dispatch, exit 2)
# ---------------------------------------------------------------------------

def test_gateway_mode_not_configured_refuses_before_any_transport():
    cfg = RaggedizedConfig.model_validate({
        "schema_version": 1,
        "generator": {"context_expected_tokens": 1024,
                      "output_reserve_tokens": 64, "deadline_seconds": 30},
    })
    fake = FakeInner()
    code, doc = run_repeated_parent_probe(cfg, "gateway", _budgets(),
                                          inner_transport=fake)
    assert code == 2
    assert doc["error"] == "MODE_NOT_CONFIGURED"
    assert fake.calls == []


def test_direct_mode_not_materialized_refuses_with_the_specific_gap():
    cfg = RaggedizedConfig.model_validate({
        "schema_version": 1,
        "generator": {"context_expected_tokens": 1024,
                      "output_reserve_tokens": 64, "deadline_seconds": 30},
        "direct_generation": {"mode": "disabled"},
    })
    fake = FakeInner()
    code, doc = run_repeated_parent_probe(cfg, "direct", _budgets(),
                                          inner_transport=fake)
    assert code == 2
    assert doc["error"] == "MODE_NOT_CONFIGURED"
    assert "offline_diagnostic" in doc["message"]
    assert fake.calls == []


def test_gateway_credential_reference_absent_refuses_before_dispatch():
    # config validation requires the declared secret reference
    cfg = RaggedizedConfig.model_validate({
        "schema_version": 1,
        "generator": {
            "route": {"base_url": "http://127.0.0.1:1/v1",
                      "model": "synthetic-gw", "api": "v1-responses",
                      "timeout_seconds": 5},
            "context_expected_tokens": 1024, "output_reserve_tokens": 64,
            "deadline_seconds": 30, "api_key_ref": "gw_key",
        },
        "secrets": {"gw_key": {"kind": "env", "name": "PROBE_UNIT_ABSENT_KEY"}},
    })
    os.environ.pop("PROBE_UNIT_ABSENT_KEY", None)
    fake = FakeInner()
    code, doc = run_repeated_parent_probe(cfg, "gateway", _budgets(),
                                          inner_transport=fake)
    assert code == 2
    assert doc["error"] == "CREDENTIAL_ABSENT"
    assert CANARY_KEY not in json.dumps(doc)
    assert fake.calls == []


# ---------------------------------------------------------------------------
# adapter preflight refusals (not_run, zero transport calls, exit 1)
# ---------------------------------------------------------------------------

def test_gateway_output_reserve_refusal_stops_with_no_transport_calls():
    cfg = _gateway_config()
    fake = FakeInner()
    # per-request 50 tokens > configured output reserve 64? no: use 128 total
    code, doc = run_repeated_parent_probe(
        cfg, "gateway", _budgets(total=200), inner_transport=fake)
    assert code == 1
    assert doc["status"] == "not_run"
    assert doc["stop_reason"] == "preflight_refusal"
    assert doc["requests"]["a"]["outcome"] == "failed"
    assert "output budget refused" in doc["requests"]["a"]["error"]
    assert doc["requests"]["b"] is None
    assert fake.calls == []
    assert doc["transport_boundary"]["attempted_calls"] == 0


def test_direct_operator_limit_refusal_stops_with_no_transport_calls():
    cfg = _direct_config()  # operator max_output_tokens 64
    fake = FakeInner()
    code, doc = run_repeated_parent_probe(
        cfg, "direct", _budgets(total=200), inner_transport=fake)
    assert code == 1
    assert doc["stop_reason"] == "preflight_refusal"
    assert "output budget refused" in doc["requests"]["a"]["error"]
    assert fake.calls == []


# ---------------------------------------------------------------------------
# finite budgets cannot be bypassed by retries or template work
# ---------------------------------------------------------------------------

def test_direct_dispatch_allowance_exhausted_mid_pair():
    cfg = _direct_config()
    fake = FakeInner(script=[
        lambda p, b: (200, json.dumps({"prompt": "rendered"}).encode()),
        lambda p, b: native_terminal_body("native-a"),
        lambda p, b: (200, json.dumps({"prompt": "rendered"}).encode()),
        lambda p, b: AssertionError("B completion must never be dispatched"),
    ])
    code, doc = run_repeated_parent_probe(
        cfg, "direct", _budgets(dispatches=3), inner_transport=fake)
    assert code == 1
    assert doc["status"] == "incomplete"
    assert doc["stop_reason"] == "budget_exhausted_dispatches"
    assert doc["requests"]["a"]["outcome"] == "terminal"
    assert doc["requests"]["b"] is None
    boundary = doc["transport_boundary"]
    assert boundary["attempted_calls"] == 2
    assert boundary["calls_by_kind"] == {"model_dispatch": 1, "template_work": 1}
    assert boundary["remaining_dispatches"] == 1
    assert [p for p, _ in fake.calls] == ["/apply-template", "/completion"]


def test_gateway_retry_budget_is_consumed_at_the_boundary():
    cfg = _gateway_config(max_retries=2)
    fake = FakeInner(script=[
        lambda p, b: (_ for _ in ()).throw(TransportConnectError("conn refused")),
        lambda p, b: (_ for _ in ()).throw(TransportConnectError("conn refused")),
        lambda p, b: gateway_terminal_body("after-retries"),
        lambda p, b: gateway_terminal_body("phase-b"),
    ])
    code, doc = run_repeated_parent_probe(
        cfg, "gateway", _budgets(dispatches=5), inner_transport=fake)
    assert code == 0
    assert doc["requests"]["a"]["outcome"] == "terminal"
    assert doc["requests"]["a"]["adapter_reported_cycles"] == 3
    assert doc["requests"]["b"]["outcome"] == "terminal"
    boundary = doc["transport_boundary"]
    assert boundary["attempted_calls"] == 4
    assert boundary["pre_dispatch_failures"] == 2
    assert boundary["responses_received"] == 2
    assert boundary["remaining_dispatches"] == 1


def test_retry_that_exhausts_the_total_budget_never_dispatches_beyond():
    cfg = _gateway_config(max_retries=5)
    def always_refused(p, b):
        raise TransportConnectError("conn refused")
    fake = FakeInner(script=[always_refused] * 10)
    code, doc = run_repeated_parent_probe(
        cfg, "gateway", _budgets(dispatches=3), inner_transport=fake)
    # A: attempts 1-3 are pre-dispatch failures consuming the finite
    # allowance; the 4th attempt is REFUSED at the boundary (safe fixed
    # message, zero dispatch). No allowance remains for B: explicit
    # incomplete, no further dispatch beyond the budget.
    assert code == 1
    assert doc["status"] == "incomplete"
    assert doc["stop_reason"] == "budget_exhausted_dispatches"
    assert doc["requests"]["a"]["outcome"] == "failed"
    assert "probe dispatch allowance exhausted" in doc["requests"]["a"]["error"]
    assert doc["requests"]["a"]["adapter_reported_cycles"] == 4
    assert doc["requests"]["b"] is None
    assert doc["transport_boundary"]["attempted_calls"] == 3
    assert doc["transport_boundary"]["remaining_dispatches"] == 0
    assert len(fake.calls) == 3


# ---------------------------------------------------------------------------
# the single absolute deadline spans the experiment
# ---------------------------------------------------------------------------

class _ManualClock:
    """Deterministic clock: returns a controllable instant."""

    def __init__(self, t=0.0):
        self.t = float(t)

    def __call__(self):
        return self.t

    def advance(self, dt):
        self.t += dt


class _ScriptedClock:
    """Returns a scripted sequence of instants (last value repeats)."""

    def __init__(self, values):
        self.values = [float(v) for v in values]
        self.i = 0

    def __call__(self):
        value = self.values[min(self.i, len(self.values) - 1)]
        self.i += 1
        return value


def test_deadline_exhausted_between_phases_stops_without_dispatch():
    cfg = _gateway_config()
    # Phase A runs entirely at t=1000.0 (deadline 1005.0); every clock read
    # from phase B onward returns t=1006.0, past the single experiment
    # deadline: B refuses before dispatch with zero transport calls.
    clock = _ScriptedClock([1000.0] * 6 + [1006.0] * 16)
    fake = FakeInner(script=[
        lambda p, b: gateway_terminal_body("phase-a"),
    ])
    code, doc = run_repeated_parent_probe(
        cfg, "gateway", _budgets(deadline=5.0), inner_transport=fake,
        clock=clock)
    assert code == 1
    assert doc["status"] == "incomplete"
    assert doc["stop_reason"] == "budget_exhausted_deadline"
    assert doc["requests"]["a"]["outcome"] == "terminal"
    assert doc["requests"]["b"] is None
    assert len(fake.calls) == 1  # B was never even attempted


def test_boundary_refuses_when_deadline_passes_mid_experiment():
    inner = FakeInner(script=[lambda p, b: gateway_terminal_body("a"),
                              lambda p, b: gateway_terminal_body("b")])
    clock = _ManualClock(1000.0)
    budgeted = BudgetedTransport(inner, deadline=1001.0, max_dispatches=4,
                                 clock=clock)
    budgeted.post_json("/v1/responses", b"{}", deadline=2000.0)
    # the single experiment deadline passes; a per-call allowance of 2000
    # must NOT reset it
    clock.advance(10.0)
    with pytest.raises(_BudgetExhausted):
        budgeted.post_json("/v1/responses", b"{}", deadline=2000.0)
    assert budgeted.attempted_calls == 1  # the refused call consumed nothing


def test_boundary_reserves_before_every_call_including_failed_connects():
    inner = FakeInner(script=[
        lambda p, b: (_ for _ in ()).throw(TransportConnectError("refused")),
        lambda p, b: gateway_terminal_body("ok"),
    ])
    budgeted = BudgetedTransport(inner, deadline=100.0, max_dispatches=2,
                                 clock=_ManualClock(0.0))
    with pytest.raises(TransportConnectError):
        budgeted.post_json("/apply-template", b"{}")
    assert budgeted.pre_dispatch_failures == 1
    assert budgeted.attempted_calls == 1
    assert budgeted.post_json("/completion", b"{}")[0] == 200
    assert budgeted.kind_counts == {"model_dispatch": 1, "template_work": 1}
    assert budgeted.remaining_dispatches == 0
    with pytest.raises(_BudgetExhausted):
        budgeted.post_json("/completion", b"{}")
    # and streams never open
    with pytest.raises(_BudgetExhausted):
        budgeted.open_stream("/v1/responses", b"{}")


# ---------------------------------------------------------------------------
# unknown completion: conservatively spent, never replayed
# ---------------------------------------------------------------------------

def test_unknown_completion_counts_spent_and_never_replays():
    def first_call_ambiguous(p, b):
        raise TransportError("transport failure: ReadError", dispatched=True)

    cfg = _gateway_config()
    fake = FakeInner(script=[
        first_call_ambiguous,
        lambda p, b: gateway_terminal_body("phase-b"),
    ])
    code, doc = run_repeated_parent_probe(
        cfg, "gateway", _budgets(dispatches=4), inner_transport=fake)
    assert code == 0  # both phases resolved (one unknown)
    assert doc["status"] == "complete"
    assert doc["requests"]["a"]["outcome"] == "unknown_completion"
    assert doc["requests"]["a"]["adapter_reported_cycles"] == 1
    assert doc["requests"]["b"]["outcome"] == "terminal"
    boundary = doc["transport_boundary"]
    assert boundary["attempted_calls"] == 2
    assert boundary["ambiguous_dispatches"] == 1
    assert boundary["responses_received"] == 1
    # exactly one POST per phase: the ambiguous call was never replayed
    assert len(fake.calls) == 2


# ---------------------------------------------------------------------------
# evidence safety and output-correctness checks
# ---------------------------------------------------------------------------

def test_evidence_carries_no_url_secret_prompt_or_response_text():
    cfg = _gateway_config(port=43211)
    fake = FakeInner(script=[
        lambda p, b: gateway_terminal_body("SECRET-RESPONSE-TEXT-003h"),
        lambda p, b: gateway_terminal_body("SECRET-RESPONSE-TEXT-003h-B"),
    ])
    code, doc = run_repeated_parent_probe(
        cfg, "gateway", _budgets(), inner_transport=fake)
    assert code == 0
    blob = json.dumps(doc)
    assert "43211" not in blob                    # endpoint URL/port
    assert "127.0.0.1" not in blob
    assert "SECRET-RESPONSE-TEXT" not in blob     # raw response text
    assert PROBE_PARENT_TEXT_MARKER not in blob   # raw probe input
    assert CANARY_KEY not in blob
    # digests are present and stable
    assert doc["requests"]["a"]["text_fingerprint"].startswith("sha256:")
    assert doc["identities"]["endpoint_fingerprint"].startswith("sha256:")
    assert doc["identities"]["endpoint_fingerprint"] == fingerprint(
        {"kind": "probe-endpoint", "endpoint": "http://127.0.0.1:43211/v1"})
    assert doc["identities"]["runtime_identity"] == "unverified"
    assert doc["live"] is False
    assert doc["model_quality"] == "not_assessed"
    assert doc["experiment"]["cold_state"] == "unknown"
    assert doc["experiment"]["phase_labels"] == ["first-call", "second-call"]


PROBE_PARENT_TEXT_MARKER = "Synthetic repeated-parent probe fixture"


def test_expected_output_check_match_mismatch_not_provided():
    from slaif_raggedized_helper.schema import fingerprint as fp
    text = "checked-answer"
    digest = fp({"kind": "probe-response-text", "label": "a", "text": text})
    cfg = _gateway_config()
    fake = FakeInner(script=[
        lambda p, b: gateway_terminal_body(text),
        lambda p, b: gateway_terminal_body("different-answer"),
    ])
    code, doc = run_repeated_parent_probe(
        cfg, "gateway", _budgets(), inner_transport=fake,
        expected_output_digests={"a": digest,
                                 "b": fp({"kind": "probe-response-text",
                                          "label": "b",
                                          "text": "other"})})
    assert code == 0
    assert doc["requests"]["a"]["expected_output_check"] == "match"
    assert doc["requests"]["b"]["expected_output_check"] == "mismatch"

    fake2 = FakeInner(script=[
        lambda p, b: gateway_terminal_body(text),
        lambda p, b: gateway_terminal_body("x"),
    ])
    code2, doc2 = run_repeated_parent_probe(
        cfg, "gateway", _budgets(), inner_transport=fake2)
    assert doc2["requests"]["a"]["expected_output_check"] == "not_provided"
    # non-terminal text has nothing to compare
    fake3 = FakeInner(script=[
        lambda p, b: (500, b'{"error": "boom"}'),
        lambda p, b: gateway_terminal_body("x"),
    ])
    _, doc3 = run_repeated_parent_probe(cfg, "gateway", _budgets(),
                                        inner_transport=fake3,
                                        expected_output_digests={
                                            "a": digest})
    assert doc3["requests"]["a"]["outcome"] == "failed"
    assert doc3["requests"]["a"]["expected_output_check"] is None


# ---------------------------------------------------------------------------
# cache evidence conclusions
# ---------------------------------------------------------------------------

def test_cache_evidence_no_control_by_default():
    cfg = _gateway_config()
    fake = FakeInner(script=[
        lambda p, b: gateway_terminal_body("a"),
        lambda p, b: gateway_terminal_body("b"),
    ])
    _, doc = run_repeated_parent_probe(cfg, "gateway", _budgets(),
                                       inner_transport=fake)
    assert doc["cache_evidence"]["conclusion"] == "no_cache_control"
    assert doc["experiment"]["cache_control"]["qualified"] is False
    # no cache key was sent to the wire
    for _, body in fake.calls:
        assert b"prompt_cache_key" not in body


def test_gateway_qualified_cache_control_sends_key_but_stays_unqualified():
    cfg = _gateway_config(caps=RouteCapabilities(prompt_caching=True))
    fake = FakeInner(script=[
        lambda p, b: gateway_terminal_body("a"),
        lambda p, b: gateway_terminal_body("b"),
    ])
    _, doc = run_repeated_parent_probe(cfg, "gateway", _budgets(),
                                       inner_transport=fake)
    assert doc["experiment"]["cache_control"]["qualified"] is True
    assert doc["experiment"]["cache_control"]["kind"] == "prompt_cache_key"
    keys = [json.loads(b)["prompt_cache_key"] for _, b in fake.calls]
    assert len(set(keys)) == 1  # stable parent-derived key for both phases
    assert len(keys[0]) <= 128
    # the gateway dialect never reports prefill/cache metrics:
    assert doc["cache_evidence"]["conclusion"] == "metrics_unavailable"
    assert doc["cache_evidence"]["reported_prefill_tokens"] == {
        "a": None, "b": None}
    assert doc["identities"]["credentials"]["api_key_ref"] is None


def _native_cache_metrics_conclusion(cache_n_b, conclusion):
    cfg = _direct_config(capabilities={"cache_prompt_tested": True})
    fake = FakeInner(script=[
        lambda p, b: (200, json.dumps({"prompt": "rendered"}).encode()),
        lambda p, b: native_terminal_body("a", cache_n=0),
        lambda p, b: (200, json.dumps({"prompt": "rendered"}).encode()),
        lambda p, b: native_terminal_body("b", cache_n=cache_n_b),
    ])
    _, doc = run_repeated_parent_probe(cfg, "direct", _budgets(),
                                       inner_transport=fake)
    assert doc["cache_evidence"]["conclusion"] == conclusion
    # the qualified cache_prompt control reached the native wire
    for p, body in fake.calls:
        if p == "/completion":
            assert json.loads(body)["cache_prompt"] is True


@pytest.mark.parametrize("cache_n_b, conclusion", [
    (0, "no_cache_hit_reported"),
    (6, "cache_hit_reported"),
])
def test_native_cache_metrics_reported_param(cache_n_b, conclusion):
    _native_cache_metrics_conclusion(cache_n_b, conclusion)


# ---------------------------------------------------------------------------
# CLI wiring (in-process; subprocess composition is the integration suite)
# ---------------------------------------------------------------------------

def test_cli_probe_requires_explicit_opt_in_and_budgets(tmp_path):
    from slaif_raggedized_helper import cli
    cfg_path = tmp_path / "cfg.json"
    cfg_path.write_text(json.dumps(_gateway_config().model_dump()),
                        encoding="utf-8")
    # missing required budget flags -> argparse usage error, exit 2
    with pytest.raises(SystemExit) as exc:
        cli.main(["probe", "--config", str(cfg_path), "--mode", "gateway"])
    assert exc.value.code == 2
    # invalid budget values -> argparse usage error, exit 2
    with pytest.raises(SystemExit) as exc:
        cli.main(["probe", "--config", str(cfg_path), "--mode", "gateway",
                  "--deadline-seconds", "inf", "--max-dispatches", "1",
                  "--max-output-tokens-total", "2"])
    assert exc.value.code == 2
    with pytest.raises(SystemExit) as exc:
        cli.main(["probe", "--config", str(cfg_path), "--mode", "gateway",
                  "--deadline-seconds", "1", "--max-dispatches", "1",
                  "--max-output-tokens-total", "1"])
    assert exc.value.code == 2
    # invalid expected digest -> usage error
    with pytest.raises(SystemExit) as exc:
        cli.main(["probe", "--config", str(cfg_path), "--mode", "gateway",
                  "--deadline-seconds", "1", "--max-dispatches", "1",
                  "--max-output-tokens-total", "2",
                  "--expected-output-a", "not-a-digest"])
    assert exc.value.code == 2


def test_cli_probe_invalid_config_refuses_with_exit_2(tmp_path, capsys):
    from slaif_raggedized_helper import cli
    path = tmp_path / "bad.json"
    path.write_text("{not json", encoding="utf-8")
    code = cli.main(["probe", "--config", str(path), "--mode", "gateway",
                     "--deadline-seconds", "1", "--max-dispatches", "1",
                     "--max-output-tokens-total", "2"])
    assert code == 2
    out = capsys.readouterr().out
    assert json.loads(out)["error"] == "CONFIG_INVALID"


def test_cli_probe_writes_evidence_file_and_exit_codes(tmp_path):
    from slaif_raggedized_helper import cli
    # route points at a closed port: pre-dispatch failures, finite budget
    srv_port = _closed_port()
    cfg = _gateway_config(port=srv_port)
    cfg_path = tmp_path / "cfg.json"
    cfg_path.write_text(json.dumps(cfg.model_dump()), encoding="utf-8")
    out_path = tmp_path / "evidence.json"
    code = cli.main([
        "probe", "--config", str(cfg_path), "--mode", "gateway",
        "--deadline-seconds", "5", "--max-dispatches", "1",
        "--max-output-tokens-total", "4",
        "--output", str(out_path),
    ])
    assert code == 1  # not_run/incomplete (connection failures)
    doc = json.loads(out_path.read_text(encoding="utf-8"))
    assert doc["status"] == "incomplete"
    assert doc["transport_boundary"]["pre_dispatch_failures"] == 1
    assert "127.0.0.1" not in out_path.read_text(encoding="utf-8")


def _closed_port():
    import socket
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port
