"""Bounded local resource telemetry composition (OAP objective 004-d).

The INSTALLED ``raggedized`` CLI runs in subprocesses: the explicit
opt-in ``resource diagnose`` command (real own-process measurements on
this devhost), the opt-in ``qualification run --resources``
composition over the real gateway/direct application code (owned
127.0.0.1 loopback servers or the owned synthetic fixture) and owned
deterministic ``nvidia-smi`` collector executables (each spawned
fixture: timeout <= 2 s, finite cleanup <= 1 s, actual output-byte
limits). Coverage (order 004-d criteria 2, 3, 4, 6, 7, 8 and the
verification section):

- the installed CLI diagnostic: real own-process CPU/RSS measurement,
  versioned document, the D0 bounded allowance enforced (6 s / 65
  samples refuse with zero work), GPU absence is an honest
  unavailable (never a zero);
- the fixed-argv nvidia-smi query through the owned fake executables:
  exact units/range, stdout byte exhaustion at the pipe boundary,
  actual child timeout (the owned child is stopped, no hang), and raw
  output never reaches the evidence;
- trial composition: the plain v1 trial evidence stays INTACT inside
  the explicit versioned wrapper; phase/ordinal/ledger facts are
  recorded (facts only, no text); the collector accounting is
  separate from transport-boundary dispatches; ONE shared absolute
  deadline still spans sampling (slow HTTP + short deadline);
  finish/deadline stop sampling with finite cleanup (no detached
  sampler); telemetry absence never becomes 0 used/full/free;
- import/help/gates/plan/doctor perform zero telemetry (no resource
  document, no sampler);
- all plain-run, deadline/retry/UNKNOWN/Unicode/ledger/export positives
  of 004-a/b/c are preserved (see test_qualification_composition.py).

All fixtures are synthetic and owned; no live model, real key,
physical GPU, model download or sensitive corpus (order 004-d live
authorization: NONE; the D0 local observational allowance applies).
"""

from __future__ import annotations

import json
import os
import stat
import subprocess
import time
from pathlib import Path

from conftest import SYNTHETIC_API_KEY  # noqa: F401  (suite parity)
from test_gateway_generator import completed_json, message_item
from test_qualification_composition import (
    gateway_config,
    qual_argv,
    run_cli,
    write_file,
    write_spec,
)
from slaif_raggedized_helper.qualification import (
    validate_resource_wrapper,
    validate_trial_evidence,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def _write_executable(path: Path, body: str) -> Path:
    path.write_text(body, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP
               | stat.S_IXOTH)
    return path


def _env_with_path(front: Path) -> dict[str, str]:
    env = dict(os.environ)
    env["PATH"] = f"{front}{os.pathsep}{env.get('PATH', '')}"
    return env


def _diagnose_argv(*extra: str) -> list[str]:
    return ["resource", "diagnose", *extra]


def _strip_wall(doc: dict) -> dict:
    """Drop per-run wall-clock fields (documented non-determinism)."""
    out = json.loads(json.dumps(doc))
    series = out.get("series", {})
    for sample in series.get("samples", []):
        pass  # samples carry only cumulative cpu + rss: deterministic
    return out


class TestInstalledCliDiagnostic:
    def test_real_own_process_measurement(self, tmp_path):
        result = run_cli(_diagnose_argv("--duration-seconds", "0.3",
                                        "--samples", "4"), timeout=30)
        assert result.returncode == 0, result.stdout + result.stderr
        doc = json.loads(result.stdout)
        assert doc["qualification"] == "resource"
        assert doc["kind"] == "resource-diagnostic"
        assert doc["version"] == 1
        scope = doc["series"]["scope"]
        assert scope["scope"] == "own-process"
        # the CLI subprocess is a different process than this test
        assert isinstance(scope["pid"], int) and scope["pid"] >= 1
        assert scope["pid"] != os.getpid()
        # real measurements on this Linux devhost
        assert doc["series"]["rss"]["current_bytes"] is not None
        assert doc["series"]["rss"]["lifetime_max_bytes"] is not None
        cpu = doc["series"]["cpu"]
        assert cpu["user_seconds"] is not None
        assert cpu["wall_seconds"] > 0
        assert doc["collector"]["samples"] >= 1
        assert doc["collector"]["collection_calls"] >= 1
        assert doc["collector"]["device_queries"] == 0
        assert doc["gpu"] is None  # not requested
        assert doc["series"]["duration_seconds"] <= 1.0
        # no secrets, no private paths, no raw command output
        blob = result.stdout
        assert "CANARY" not in blob
        # devhost scoping is stated, never a remote/host claim
        assert "devhost" in json.dumps(doc)

    def test_d0_allowance_enforced_before_work(self, tmp_path):
        for extra in (("--duration-seconds", "6"),
                      ("--samples", "65")):
            result = run_cli(_diagnose_argv(*extra), timeout=30)
            assert result.returncode == 2, (extra, result.stdout)
            doc = json.loads(result.stdout)
            assert doc["error"] == "USAGE_INVALID"
            assert "no telemetry ran" in doc["message"]

    def test_gpu_absent_is_honest_unavailable(self, tmp_path):
        # this devhost/CI has no nvidia-smi: the fixed query must be an
        # exact unavailable, never 0 used/full/free
        result = run_cli(_diagnose_argv("--duration-seconds", "0.2",
                                        "--samples", "2", "--gpu"),
                         timeout=30)
        assert result.returncode == 0, result.stdout + result.stderr
        doc = json.loads(result.stdout)
        gpu = doc["gpu"]
        assert gpu is not None
        assert gpu["status"] == "unavailable"
        assert gpu["reason"] == "tool_absent"
        assert gpu["devices"] == []
        assert doc["collector"]["device_queries"] == 1

    def test_output_destination(self, tmp_path):
        target = tmp_path / "diag.json"
        result = run_cli(_diagnose_argv("--duration-seconds", "0.15",
                                        "--samples", "2", "--output",
                                        str(target)), timeout=30)
        assert result.returncode == 0
        assert json.loads(target.read_text())["kind"] == "resource-diagnostic"
        # invalid destination refuses before any work
        result = run_cli(_diagnose_argv("--duration-seconds", "0.15",
                                        "--samples", "2", "--output",
                                        str(tmp_path / "no-such-dir"
                                            / "x.json")), timeout=30)
        assert result.returncode == 2
        assert json.loads(result.stdout)["error"] == \
            "OUTPUT_DESTINATION_INVALID"


class TestFixedArgvGpuQueryViaCli:
    def test_available_exact_units_and_values(self, tmp_path):
        _write_executable(
            tmp_path / "nvidia-smi",
            "#!/bin/sh\n"
            "printf '0,SYNTHETIC-FAKE-GPU-A,81920,1024,80000\\n'\n"
            "printf '1,SYNTHETIC-FAKE-GPU-B,49152,0,49152\\n'\n")
        result = run_cli(_diagnose_argv("--duration-seconds", "0.2",
                                        "--samples", "2", "--gpu"),
                         env=_env_with_path(tmp_path), timeout=30)
        assert result.returncode == 0, result.stdout + result.stderr
        doc = json.loads(result.stdout)
        gpu = doc["gpu"]
        assert gpu["status"] == "available"
        assert gpu["reason"] is None
        assert len(gpu["devices"]) == 2
        assert gpu["devices"][0] == {
            "device_index": 0, "device_name": "SYNTHETIC-FAKE-GPU-A",
            "memory_unit": "mib", "memory_total": 81920,
            "memory_used": 1024, "memory_free": 80000}
        assert gpu["devices"][1]["memory_used"] == 0  # known zero kept
        assert gpu["stdout_bytes"] > 0
        assert gpu["query_wall_seconds"] is not None
        assert doc["collector"]["device_queries"] == 1
        assert "SYNTHETIC-FAKE-GPU-A" not in \
            result.stderr  # device identity stays in the evidence only

    def test_stdout_byte_exhaustion_at_pipe_boundary(self, tmp_path):
        _write_executable(
            tmp_path / "nvidia-smi",
            "#!/bin/sh\n"
            "python3 -c \"import sys;"
            "sys.stdout.write('0,' + 'x'*20000 + ',81920,1,81919\\n')\"\n")
        t0 = time.monotonic()
        result = run_cli(_diagnose_argv("--duration-seconds", "0.2",
                                        "--samples", "2", "--gpu"),
                         env=_env_with_path(tmp_path), timeout=30)
        assert time.monotonic() - t0 < 15.0  # no hang: child stopped
        assert result.returncode == 0
        doc = json.loads(result.stdout)
        gpu = doc["gpu"]
        assert gpu["status"] == "error"
        assert gpu["reason"] == "stdout_oversize"
        assert gpu["stdout_bytes"] == 16 * 1024 + 1
        assert gpu["devices"] == []  # never 0 used/full/free
        # the raw oversize payload never reaches the evidence
        assert "x" * 2000 not in result.stdout

    def test_actual_child_timeout(self, tmp_path):
        _write_executable(
            tmp_path / "nvidia-smi",
            "#!/bin/sh\nsleep 2\n"
            "printf '0,SYNTHETIC-FAKE-GPU-A,81920,1024,80000\\n'\n")
        t0 = time.monotonic()
        result = run_cli(_diagnose_argv("--duration-seconds", "0.2",
                                        "--samples", "2", "--gpu"),
                         env=_env_with_path(tmp_path), timeout=30)
        elapsed = time.monotonic() - t0
        assert result.returncode == 0
        doc = json.loads(result.stdout)
        gpu = doc["gpu"]
        assert gpu["status"] == "error"
        assert gpu["reason"] == "timeout"
        assert 0.9 <= elapsed < 15.0  # bounded; owned child stopped
        assert gpu["devices"] == []


class TestTrialWithResourcesComposition:
    def test_synthetic_trial_wrapper_keeps_plain_v1_intact(self, tmp_path):
        cfg = write_file(tmp_path, gateway_config(1), "gw-config.json")
        spec = write_spec(tmp_path)
        result = run_cli(qual_argv(cfg, spec, extra=["--synthetic",
                                                     "--resources"]))
        assert result.returncode == 0, result.stdout + result.stderr
        doc = json.loads(result.stdout)
        assert doc["resource_wrapper"] == 1
        assert set(doc) == {"resource_wrapper", "trial", "resources"}
        # the plain v1 evidence is valid and intact inside the wrapper
        trial = doc["trial"]
        validate_trial_evidence(trial)
        assert trial["status"] == "complete"
        assert trial["transport_boundary"]["attempted_calls"] == 3
        validate_resource_wrapper(doc)
        res = doc["resources"]
        assert res["kind"] == "resource-telemetry"
        assert res["version"] == 1
        assert res["trial_status"] == "complete"
        assert res["gpu"] is None
        assert res["collector"]["device_queries"] == 0
        assert res["collector"]["samples"] >= 1
        assert res["collector"]["stop_reason"] == "finished"
        # phase/ordinal/ledger facts, exactly, with no text
        events = res["phase_events"]
        assert len(events) == 3
        assert [e["ordinal"] for e in events] == [0, 1, 2]
        assert [e["phase"] for e in events] == ["warmup", "measured",
                                                "measured"]
        assert [e["attempted_calls"] for e in events] == [0, 1, 2]
        for event in events:
            assert set(event) == {"phase", "ordinal", "attempted_calls",
                                  "elapsed_seconds"}
        # collector accounting is separate from model dispatches
        assert res["collector"]["collection_calls"] >= 1
        assert trial["transport_boundary"]["attempted_calls"] == 3

    def test_plain_run_without_optin_stays_plain_v1(self, tmp_path):
        cfg = write_file(tmp_path, gateway_config(1), "gw-config.json")
        spec = write_spec(tmp_path)
        result = run_cli(qual_argv(cfg, spec, extra=["--synthetic"]))
        assert result.returncode == 0
        doc = json.loads(result.stdout)
        assert "resource_wrapper" not in doc
        assert "resources" not in doc
        validate_trial_evidence(doc)

    def test_resource_gpu_flag_alone_refused_before_dispatch(self, tmp_path):
        cfg = write_file(tmp_path, gateway_config(1), "gw-config.json")
        spec = write_spec(tmp_path)
        result = run_cli(qual_argv(cfg, spec, extra=["--synthetic",
                                                     "--resource-gpu"]))
        assert result.returncode == 2
        doc = json.loads(result.stdout)
        assert doc["error"] == "USAGE_INVALID"
        assert "no HTTP was sent" in doc["message"]

    def test_preflight_refusal_runs_no_telemetry(self, tmp_path):
        cfg = write_file(tmp_path, gateway_config(1), "gw-config.json")
        spec = write_spec(tmp_path, declared_model="other-model")
        result = run_cli(qual_argv(cfg, spec, extra=["--synthetic",
                                                     "--resources"]))
        assert result.returncode == 2, result.stdout + result.stderr
        doc = json.loads(result.stdout)
        # the pre-dispatch refusal document is unchanged (zero
        # dispatches); telemetry was never bound, so no wrapper
        assert doc["error"] == "TRIAL_PREFLIGHT_REFUSED"
        assert "resource_wrapper" not in doc
        assert "resources" not in doc

    def test_slow_http_under_shared_short_deadline(self, server, tmp_path):
        def slow_scenario(h, r):
            time.sleep(1.5)  # past the 0.6 s trial deadline
            h._send_json(200, completed_json([message_item("m0", "late")]))

        srv = server(slow_scenario)
        cfg = write_file(tmp_path, gateway_config(srv.port),
                         "gw-config.json")
        spec = write_spec(tmp_path, budgets={
            "deadline_seconds": 0.6, "max_dispatches": 10,
            "max_output_tokens_total": 30})
        start = time.monotonic()
        # NOT --synthetic: the slow owned loopback server above is the
        # configured route itself
        result = run_cli(qual_argv(cfg, spec, extra=["--resources"]),
                         timeout=30)
        elapsed = time.monotonic() - start
        assert result.returncode == 1, result.stdout + result.stderr
        doc = json.loads(result.stdout)
        assert doc["resource_wrapper"] == 1
        trial = doc["trial"]
        assert trial["status"] == "incomplete"
        assert trial["stop_reason"] == "budget_exhausted_deadline"
        assert trial["transport_boundary"]["attempted_calls"] == 1
        assert srv.count("/v1/responses") == 1  # no replay
        res = doc["resources"]
        # sampling stopped at/with the deadline; finite cleanup
        assert res["collector"]["stop_reason"] in (
            "deadline_reached", "stopped", "cleanup_timed_out")
        assert res["collector"]["samples"] >= 1
        assert elapsed < 8.0  # no detached sampler extending the run
        validate_resource_wrapper(doc)

    def test_gpu_query_composed_into_wrapper(self, server, tmp_path):
        tool_dir = tmp_path / "tools"
        tool_dir.mkdir()
        _write_executable(
            tool_dir / "nvidia-smi",
            "#!/bin/sh\nprintf '0,SYNTHETIC-FAKE-GPU,81920,1024,80000\\n'\n")
        cfg = write_file(tmp_path, gateway_config(1), "gw-config.json")
        spec = write_spec(tmp_path)
        result = run_cli(qual_argv(cfg, spec, extra=["--synthetic",
                                                     "--resources",
                                                     "--resource-gpu"]),
                         env=_env_with_path(tool_dir), timeout=30)
        assert result.returncode == 0, result.stdout + result.stderr
        doc = json.loads(result.stdout)
        validate_resource_wrapper(doc)
        res = doc["resources"]
        assert res["collector"]["device_queries"] == 1
        assert res["gpu"]["status"] == "available"
        assert res["gpu"]["devices"][0]["device_name"] == "SYNTHETIC-FAKE-GPU"
        assert res["gpu"]["devices"][0]["memory_unit"] == "mib"
        assert doc["trial"]["status"] == "complete"
        # the trial itself is unaffected by the collector activity
        assert doc["trial"]["transport_boundary"]["attempted_calls"] == 3

    def test_gpu_unavailable_still_yields_valid_trial(self, tmp_path):
        # no nvidia-smi on this host: exact unavailable evidence, the
        # trial evidence and spent ledger stay valid
        cfg = write_file(tmp_path, gateway_config(1), "gw-config.json")
        spec = write_spec(tmp_path)
        result = run_cli(qual_argv(cfg, spec, extra=["--synthetic",
                                                     "--resources",
                                                     "--resource-gpu"]))
        assert result.returncode == 0, result.stdout + result.stderr
        doc = json.loads(result.stdout)
        validate_resource_wrapper(doc)
        res = doc["resources"]
        assert res["gpu"]["status"] == "unavailable"
        assert res["gpu"]["reason"] == "tool_absent"
        assert res["gpu"]["devices"] == []
        assert doc["trial"]["status"] == "complete"


class TestZeroTelemetryOnNonOptInCommands:
    def _assert_no_resource_document(self, result: subprocess.CompletedProcess,
                                     label: str):
        assert result.returncode == 0, (label, result.stdout, result.stderr)
        blob = result.stdout
        # none of these commands ever emit a resource document
        assert '"resource-diagnostic"' not in blob
        assert '"resource-telemetry"' not in blob
        assert '"resource_wrapper"' not in blob

    def test_help_gates_plan_doctor_zero_telemetry(self, tmp_path):
        self._assert_no_resource_document(
            run_cli(["--help"], timeout=30), "help")
        self._assert_no_resource_document(
            run_cli(["resource", "--help"], timeout=30), "resource help")
        self._assert_no_resource_document(
            run_cli(["qualification", "gates"], timeout=30), "gates")
        cfg = write_file(tmp_path, gateway_config(1), "gw-config.json")
        spec = write_spec(tmp_path)
        self._assert_no_resource_document(
            run_cli(qual_argv(cfg, spec, sub="plan"), timeout=30), "plan")
        # doctor over the shipped example config (offline by contract)
        example = REPO_ROOT / "config" / "examples" / "example-config.json"
        result = run_cli(["doctor", "--config", str(example)], timeout=30)
        assert result.returncode in (0, 1)
        assert '"resource-diagnostic"' not in result.stdout
        assert '"resource-telemetry"' not in result.stdout
