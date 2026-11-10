"""Doctor CLI behavior: exit/result semantics, offline guarantees, secret canaries."""

from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
from pathlib import Path

import pytest

from slaif_raggedized_helper import cli

REPO_ROOT = Path(__file__).resolve().parents[2]
EXAMPLE_CONFIG = REPO_ROOT / "config/examples/example-config.json"

CANARY = "canary-secret-value-002-xyz"


def qualified_manifest() -> dict:
    """Synthetic live-scope qualification fixture exercising the promotion path.

    Test data only: the doctor validates scope/consistency structurally; it
    cannot verify the truth of recorded evidence.
    """
    return qualified_manifest_for("generator")


def qualified_manifest_for(role: str) -> dict:
    lock = {
        "schema_version": 1,
        "role": role,
        "model_name": f"SyntheticModel-{role}",
        "revision": "rev-synthetic-1",
        "artifact_sha256": "ab" * 32,
        "license_name": "MIT",
        "license_status": "approved",
        "tokenizer_revision": "tok-1",
        "pooling": "cls" if role == "embedding" else None,
        "gguf": (
            {"quantization": "Q6_K", "artifact_sha256": "cd" * 32} if role == "generator" else None
        ),
        "projector": None,
        "runtime": {"name": "synthetic-runtime", "version": "0"},
    }
    return {
        "schema_version": 1,
        "lock": lock,
        "qualification": {
            "schema_version": 1,
            "test_name": "synthetic-smoke",
            "recorded_at": "2026-11-10T00:00:00Z",
            "code_scope": "abc123",
            "model_scope": "rev-synthetic-1",
            "runtime_scope": "cpu-synthetic",
            "mode": "live",
            "status": "pass",
            "metrics": None,
        },
    }


def write_config(tmp_path: Path, **overrides) -> Path:
    config = {
        "schema_version": 1,
        "generator": {
            "route": {
                "base_url": "http://gateway.invalid/v1",
                "model": "SyntheticModel",
                "api": "v1-responses",
                "timeout_seconds": 60,
            },
            "context_expected_tokens": 4096,
            "output_reserve_tokens": 256,
            "deadline_seconds": 30,
        },
        "profiles": [
            {"name": "q", "purpose": "online_query_embedding", "device": "cpu", "dtype": "fp32"}
        ],
        "secrets": {},
        "model_locks": [],
    }
    for key, value in overrides.items():
        node = config
        parts = key.split(".")
        for part in parts[:-1]:
            node = node[part]
        node[parts[-1]] = value
    path = tmp_path / "config.json"
    path.write_text(json.dumps(config), encoding="utf-8")
    return path


def run_main(argv: list[str]) -> int:
    return cli.main(argv)


def test_doctor_ok_exit_zero(tmp_path, capsys, monkeypatch):
    # Fully covered: every required role has a role-matching qualified manifest
    # and the declared gateway key is present. Synthetic test data only.
    monkeypatch.setenv("SLAIF_DOCTOR_TEST_KEY", "test-key-value")
    model_locks = []
    for role in ("generator", "embedding", "reranker"):
        manifest = tmp_path / f"manifest-{role}.json"
        manifest.write_text(json.dumps(qualified_manifest_for(role)), encoding="utf-8")
        model_locks.append({"role": role, "path": str(manifest)})
    config_path = write_config(
        tmp_path,
        **{
            "model_locks": model_locks,
            "secrets": {"gateway_key": {"kind": "env", "name": "SLAIF_DOCTOR_TEST_KEY"}},
        },
    )
    exit_code = run_main(["doctor", "--config", str(config_path)])
    out = capsys.readouterr().out
    assert exit_code == cli.EXIT_OK
    doc = json.loads(out)
    assert doc["status"] == "ok"
    assert doc["config"] == "valid"
    assert doc["readiness"] == "ready"
    assert doc["issues"] == []
    assert [m["qualification"] for m in doc["models"]] == ["qualified"] * 3
    assert {m["role"] for m in doc["models"]} == {"generator", "embedding", "reranker"}
    assert doc["route"]["configured"] is True


def test_doctor_valid_config_without_manifests_or_secrets_is_not_success(tmp_path, capsys):
    # Success by omission must not happen: a syntactically valid config with a
    # route and a profile but no model locks or credential references stays
    # config-valid yet readiness-not-ready with actionable issues.
    exit_code = run_main(["doctor", "--config", str(write_config(tmp_path))])
    out = capsys.readouterr().out
    assert exit_code == cli.EXIT_ISSUES
    doc = json.loads(out)
    assert doc["config"] == "valid"
    assert doc["readiness"] == "not_ready"
    assert doc["status"] == "issues"
    codes = [issue["code"] for issue in doc["issues"]]
    assert codes.count("MODEL_COVERAGE_MISSING") == 3
    assert "SECRETS_MISSING" in codes
    assert "MODEL_UNQUALIFIED" not in codes


def test_doctor_declared_but_absent_secret_is_actionable_issue(tmp_path, capsys, monkeypatch):
    monkeypatch.delenv("SLAIF_DOCTOR_ABSENT_KEY", raising=False)
    config_path = write_config(
        tmp_path,
        **{"secrets": {"gateway_key": {"kind": "env", "name": "SLAIF_DOCTOR_ABSENT_KEY"}}},
    )
    exit_code = run_main(["doctor", "--config", str(config_path)])
    doc = json.loads(capsys.readouterr().out)
    assert exit_code == cli.EXIT_ISSUES
    assert "SECRET_ABSENT" in {i["code"] for i in doc["issues"]}
    assert doc["secrets"]["gateway_key"] == {"kind": "env", "present": False}


def test_doctor_role_mismatch_between_ref_and_manifest(tmp_path, capsys):
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps(qualified_manifest_for("generator")), encoding="utf-8")
    config_path = write_config(
        tmp_path,
        **{"model_locks": [{"role": "embedding", "path": str(manifest)}]},
    )
    exit_code = run_main(["doctor", "--config", str(config_path)])
    doc = json.loads(capsys.readouterr().out)
    assert exit_code == cli.EXIT_ISSUES
    codes = {i["code"] for i in doc["issues"]}
    assert "MODEL_ROLE_MISMATCH" in codes
    assert doc["models"][0]["status"] == "role_mismatch"


def test_doctor_never_echoes_url_secret_on_rejected_config(tmp_path, capsys):
    secret = "FAKE_TEST_SECRET-002"
    data = json.loads(EXAMPLE_CONFIG.read_text(encoding="utf-8"))
    data["generator"]["route"]["base_url"] = f"http://user:{secret}@example.invalid/v1"
    data["model_locks"] = []
    data["secrets"] = {}
    path = tmp_path / "secret-route.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    exit_code = run_main(["doctor", "--config", str(path)])
    out = capsys.readouterr()
    assert exit_code == cli.EXIT_ISSUES
    assert secret not in out.out
    assert secret not in out.err
    doc = json.loads(out.out)
    assert doc["config"] == "invalid"
    assert "CONFIG_INVALID" in {i["code"] for i in doc["issues"]}


def test_doctor_example_reports_honest_unqualified_issues(capsys):
    exit_code = run_main(["doctor", "--config", str(EXAMPLE_CONFIG)])
    out = capsys.readouterr().out
    assert exit_code == cli.EXIT_ISSUES
    doc = json.loads(out)
    assert doc["status"] == "issues"
    assert doc["config"] == "valid"
    assert doc["readiness"] == "not_ready"
    codes = {issue["code"] for issue in doc["issues"]}
    assert "MODEL_UNQUALIFIED" in codes
    # the .invalid route is configured, so no ROUTE_MISSING for the example
    assert "ROUTE_MISSING" not in codes
    for model in doc["models"]:
        assert model["qualification"] == "unqualified"


def test_doctor_missing_route_is_honest_issue(tmp_path, capsys):
    config_path = write_config(tmp_path, **{"generator.route": None})
    exit_code = run_main(["doctor", "--config", str(config_path)])
    doc = json.loads(capsys.readouterr().out)
    assert exit_code == cli.EXIT_ISSUES
    codes = [i["code"] for i in doc["issues"]]
    assert "ROUTE_MISSING" in codes
    assert codes.count("MODEL_COVERAGE_MISSING") == 3
    assert "SECRETS_MISSING" not in codes  # no route configured, nothing to authenticate
    assert doc["route"] == {"configured": False, "host": None, "model": None}
    assert doc["readiness"] == "not_ready"
    assert doc["config"] == "valid"


def test_doctor_invalid_config_still_machine_readable(tmp_path, capsys):
    path = tmp_path / "bad.json"
    data = json.loads(EXAMPLE_CONFIG.read_text(encoding="utf-8"))
    data["generator"]["deadline_seconds"] = 0
    path.write_text(json.dumps(data), encoding="utf-8")
    exit_code = run_main(["doctor", "--config", str(path)])
    out = capsys.readouterr().out
    assert exit_code == cli.EXIT_ISSUES
    doc = json.loads(out)
    assert doc["config"] == "invalid"
    assert {i["code"] for i in doc["issues"]} == {"CONFIG_INVALID"}
    assert "Traceback" not in out


def test_doctor_missing_config_file(tmp_path, capsys):
    exit_code = run_main(["doctor", "--config", str(tmp_path / "absent.json")])
    doc = json.loads(capsys.readouterr().out)
    assert exit_code == cli.EXIT_ISSUES
    assert doc["config"] == "missing"
    assert {i["code"] for i in doc["issues"]} == {"CONFIG_MISSING"}


def test_doctor_missing_model_lock_file(tmp_path, capsys):
    config_path = write_config(
        tmp_path, **{"model_locks": [{"role": "embedding", "path": "absent-manifest.json"}]}
    )
    exit_code = run_main(["doctor", "--config", str(config_path)])
    doc = json.loads(capsys.readouterr().out)
    assert exit_code == cli.EXIT_ISSUES
    assert "MODEL_LOCK_MISSING" in {i["code"] for i in doc["issues"]}


def test_help_and_version_work_offline(tmp_path, monkeypatch):
    def blocked(*args, **kwargs):
        raise AssertionError("network attempted during --help")

    monkeypatch.setattr(socket, "socket", blocked)
    monkeypatch.setattr(socket, "create_connection", blocked)
    monkeypatch.setattr(socket, "getaddrinfo", blocked)
    with pytest.raises(SystemExit) as exc:
        run_main(["--help"])
    assert exc.value.code == 0
    with pytest.raises(SystemExit) as exc:
        run_main(["--version"])
    assert exc.value.code == 0


def test_usage_error_exit_two():
    with pytest.raises(SystemExit) as exc:
        run_main([])
    assert exc.value.code == cli.EXIT_USAGE


def test_doctor_performs_no_network(tmp_path, monkeypatch, capsys):
    def blocked(*args, **kwargs):
        raise AssertionError("network attempted during doctor")

    monkeypatch.setattr(socket, "socket", blocked)
    monkeypatch.setattr(socket, "create_connection", blocked)
    monkeypatch.setattr(socket, "getaddrinfo", blocked)
    exit_code = run_main(["doctor", "--config", str(EXAMPLE_CONFIG)])
    doc = json.loads(capsys.readouterr().out)
    assert exit_code == cli.EXIT_ISSUES
    assert doc["status"] == "issues"


def test_doctor_never_reveals_secret_values(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("SLAIF_DOCTOR_CANARY", CANARY)
    secret_file = tmp_path / "secret-file.txt"
    secret_file.write_text(CANARY, encoding="utf-8")
    config_path = write_config(
        tmp_path,
        **{
            "secrets": {
                "env_secret": {"kind": "env", "name": "SLAIF_DOCTOR_CANARY"},
                "file_secret": {"kind": "file", "name": str(secret_file)},
                "absent_secret": {"kind": "env", "name": "SLAIF_DOCTOR_ABSENT"},
            }
        },
    )
    exit_code = run_main(["doctor", "--config", str(config_path)])
    out = capsys.readouterr()
    assert exit_code == cli.EXIT_ISSUES
    assert CANARY not in out.out
    assert CANARY not in out.err
    doc = json.loads(out.out)
    assert doc["secrets"] == {
        "env_secret": {"kind": "env", "present": True},
        "file_secret": {"kind": "file", "present": True},
        "absent_secret": {"kind": "env", "present": False},
    }


def test_import_and_doctor_are_network_free_in_subprocess(tmp_path):
    """Fresh interpreter: block sockets before import, then import and run doctor."""
    script = (
        "import socket\n"
        "def blocked(*a, **k):\n"
        "    raise AssertionError('network attempted')\n"
        "socket.socket = blocked\n"
        "socket.create_connection = blocked\n"
        "socket.getaddrinfo = blocked\n"
        "import slaif_raggedized_helper\n"
        "from slaif_raggedized_helper.cli import run_doctor\n"
        f"code, doc = run_doctor({str(EXAMPLE_CONFIG)!r})\n"
        "print(code, doc['status'])\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": str(REPO_ROOT / "src")},
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == f"{cli.EXIT_ISSUES} issues"
