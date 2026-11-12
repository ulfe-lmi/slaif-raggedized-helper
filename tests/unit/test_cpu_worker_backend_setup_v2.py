"""Admission and actual synthetic fixture checks for the v2 profile."""

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "tests/support/prepare_cpu_worker_test_backend_v2.py"
SPEC = importlib.util.spec_from_file_location("cpu_setup_v2", SCRIPT)
setup = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(setup)
LOCK = ROOT / "worker_profiles/cpu-v2/uv.lock"
REQ = ROOT / "tests/support/cpu-worker-test-v2-requirements.txt"


def test_fixed_inputs_valid_and_changed_inputs_refused(tmp_path, monkeypatch):
    pins, _ = setup.fixed_inputs(LOCK, REQ)
    assert len(pins) == 38 and len(setup.WHEELS) == 6
    bad = tmp_path / "lock"
    bad.write_bytes(LOCK.read_bytes() + b"\n")
    with pytest.raises(ValueError, match="lock"):
        setup.fixed_inputs(bad, REQ)
    bad_req = tmp_path / "req"
    bad_req.write_bytes(REQ.read_bytes() + b"\n")
    with pytest.raises(ValueError, match="requirements"):
        setup.fixed_inputs(LOCK, bad_req)
    for old, new in [
        (b"3346235", b"3346234"),
        (b"5075b405006415ea148a992d093699c66eb01952bf59f4d5727089a98bda45a4", b"0" * 64),
        (b'[[package]]\nname = "tokenizers"', b'[[package]]\nname = "wrong-tokenizers"'),
    ]:
        altered = LOCK.read_bytes().replace(old, new, 1)
        assert altered != LOCK.read_bytes()
        bad.write_bytes(altered)
        monkeypatch.setattr(setup, "LOCK_HASH", hashlib.sha256(altered).hexdigest())
        with pytest.raises(ValueError):
            setup.fixed_inputs(bad, REQ)
    monkeypatch.setattr(setup, "LOCK_HASH", hashlib.sha256(LOCK.read_bytes()).hexdigest())
    duplicate = (
        LOCK.read_bytes() + b'\n[[package]]\nname = "tokenizers"\nversion = "0.23.1"\n'
        b'source = { registry = "https://pypi.org/simple" }\n'
    )
    bad.write_bytes(duplicate)
    monkeypatch.setattr(setup, "LOCK_HASH", hashlib.sha256(duplicate).hexdigest())
    with pytest.raises(ValueError, match="inventory"):
        setup.fixed_inputs(bad, REQ)


def test_refusals_before_target_and_child_calls(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(setup._support, "run", lambda *a, **k: calls.append(a))
    target = tmp_path / "target"
    monkeypatch.setattr(
        sys, "argv", ["setup", "--runtime-dir", str(tmp_path), "--target", str(target)]
    )
    with pytest.raises(ValueError, match="runtime"):
        setup.main()
    assert calls == [] and not target.exists()
    monkeypatch.setattr(
        sys,
        "argv",
        ["setup", "--runtime-dir", os.environ["SLAIF_CPU_V2_TEST_ROOT"], "--target", str(target)],
    )
    with pytest.raises(ValueError, match="target"):
        setup.main()
    assert calls == [] and not target.exists()
    monkeypatch.setattr(setup, "LOCK_HASH", "0" * 64)
    with pytest.raises(ValueError, match="lock"):
        setup.main()
    assert calls == [] and not target.exists()


def test_actual_fixture():
    packages = Path(os.environ["SLAIF_CPU_V2_TEST_PACKAGES"])
    receipt = json.loads((packages.parent / "setup-evidence.json").read_text())
    assert receipt["state"] == "complete"
    actual = receipt["actual_installed"]["actual"]
    synthetic = receipt["synthetic_metadata_only"]
    assert len(actual) == 6 and len(synthetic) == 32 and not set(actual) & set(synthetic)
    assert actual["tokenizers"] == "0.23.1"
    pins, _ = setup.fixed_inputs(LOCK, REQ)
    assert actual | synthetic == pins
    for name, version in synthetic.items():
        info = packages / (name.replace("-", "_") + "-" + version + ".dist-info")
        assert sorted(p.name for p in info.iterdir()) == ["METADATA"]
        assert not (packages / name.replace("-", "_")).exists()
    assert receipt["network_bytes"] == "UNKNOWN"
    assert receipt["sampled_peak_disk_bytes"] < 96 * 1024**2


def test_existing_target_refused_before_children(monkeypatch):
    calls = []
    monkeypatch.setattr(setup._support, "run", lambda *a, **k: calls.append(a))
    with tempfile.TemporaryDirectory(dir="/tmp", prefix="slaif-v2-test-") as directory:
        target = Path(directory)
        sentinel = target / "sentinel"
        sentinel.write_text("preserved")
        monkeypatch.setattr(
            sys,
            "argv",
            [
                "setup",
                "--runtime-dir",
                os.environ["SLAIF_CPU_V2_TEST_ROOT"],
                "--target",
                str(target),
            ],
        )
        with pytest.raises(ValueError, match="already exists"):
            setup.main()
        assert calls == [] and sentinel.read_text() == "preserved"


@pytest.mark.parametrize(
    "facts", ["pypy\n3.12.1\n{root}", "cpython\n3.14.0\n{root}", "cpython\n3.12.1\n/tmp"]
)
def test_runtime_facts_refused_before_install(tmp_path, monkeypatch, facts):
    root = tmp_path / "runtime"
    (root / "bin").mkdir(parents=True)
    python = root / "bin/python3.12"
    python.write_text("stub")
    python.chmod(0o700)
    target = Path("/tmp") / ("slaif-test-" + tmp_path.name)
    calls = []
    monkeypatch.setattr(setup.shutil, "which", lambda _: "/usr/bin/true")
    monkeypatch.setattr(setup.os, "access", lambda *a: True)
    monkeypatch.setattr(
        setup._support, "run", lambda *a, **k: calls.append(a) or facts.format(root=root)
    )
    monkeypatch.setattr(sys, "argv", ["setup", "--runtime-dir", str(root), "--target", str(target)])
    with pytest.raises(ValueError, match="runtime facts"):
        setup.main()
    assert len(calls) == 1 and not target.exists()
