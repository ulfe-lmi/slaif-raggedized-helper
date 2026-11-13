"""GPU metadata fixture admission and real backend gate with trusted in-memory facades."""

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

import pytest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "gpu_fixture", ROOT / "tests/support/prepare_gpu_worker_test_backend.py"
)
setup = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(setup)
LOCK = ROOT / "worker_profiles/gpu/uv.lock"
REQ = ROOT / "tests/support/cpu-worker-test-v2-requirements.txt"


def test_fixed_plan_and_tampering(tmp_path, monkeypatch):
    pins, _ = setup.fixed_inputs(LOCK, REQ)
    assert len(pins) == 57 and len(setup.WHEELS) == 6 and len(set(pins) - set(setup.WHEELS)) == 51
    bad = tmp_path / "input"
    bad.write_bytes(REQ.read_bytes() + b"bad==1\n")
    with pytest.raises(ValueError, match="requirements"):
        setup.fixed_inputs(LOCK, bad)
    raw = LOCK.read_bytes()
    for changed in (
        raw + b"\n",
        raw.replace(b"3346235", b"3346234", 1),
        raw.replace(
            b"5075b405006415ea148a992d093699c66eb01952bf59f4d5727089a98bda45a4", b"0" * 64, 1
        ),
        raw.replace(
            b'name = "tokenizers"\nversion = "0.23.1"',
            b'name = "tokenizers"\nversion = "0.23.0"',
            1,
        ),
        raw
        + b'\n[[package]]\nname = "tokenizers"\nversion = "0.23.1"\nsource = { registry = "x" }\n',
        raw.replace(b'name = "annotated-types"', b'name = "unexpected-package"', 1),
    ):
        assert changed != raw
        bad.write_bytes(changed)
        if changed != raw + b"\n":
            monkeypatch.setattr(setup, "LOCK_HASH", hashlib.sha256(changed).hexdigest())
        with pytest.raises(ValueError):
            setup.fixed_inputs(bad, REQ)
        monkeypatch.setattr(setup, "LOCK_HASH", hashlib.sha256(raw).hexdigest())


def test_refusal_before_child_or_install(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(setup._support, "run", lambda *a, **k: calls.append(a))
    monkeypatch.setattr(
        sys, "argv", ["setup", "--runtime-dir", "/nonexistent", "--target", "/tmp/test-gpu"]
    )
    with pytest.raises((ValueError, OSError)):
        setup.main()
    assert not calls
    runtime = os.environ["SLAIF_GPU_TEST_ROOT"]
    with tempfile.TemporaryDirectory(dir="/tmp") as directory:
        target = Path(directory)
        sentinel = target / "sentinel"
        sentinel.write_text("safe")
        monkeypatch.setattr(
            sys, "argv", ["setup", "--runtime-dir", runtime, "--target", str(target)]
        )
        with pytest.raises(ValueError, match="exists"):
            setup.main()
        assert not calls and sentinel.read_text() == "safe"
        link = target.parent / (target.name + "-link")
        link.symlink_to(target)
        try:
            monkeypatch.setattr(
                sys, "argv", ["setup", "--runtime-dir", runtime, "--target", str(link)]
            )
            with pytest.raises(ValueError):
                setup.main()
            assert not calls and sentinel.read_text() == "safe"
        finally:
            link.unlink()
    monkeypatch.setattr(setup.platform, "machine", lambda: "wrong")
    with pytest.raises(ValueError, match="Linux"):
        setup.main()
    assert not calls


def test_actual_inventory_and_backend_gate():
    runtime = Path(os.environ["SLAIF_GPU_TEST_ROOT"])
    packages = Path(os.environ["SLAIF_GPU_TEST_PACKAGES"])
    receipt = json.loads((packages.parent / "setup-evidence.json").read_text())
    pins, _ = setup.fixed_inputs(LOCK, REQ)
    actual, synthetic = receipt["actual_installed"]["actual"], receipt["synthetic_metadata_only"]
    assert receipt["state"] == "complete" and len(actual) == 6 and len(synthetic) == 51
    assert not set(actual) & set(synthetic) and actual | synthetic == pins
    assert receipt["runtime"] == str(runtime) and receipt["network_bytes"] == "UNKNOWN"
    for name, version in synthetic.items():
        info = packages / (name.replace("-", "_") + "-" + version + ".dist-info")
        assert [x.name for x in info.iterdir()] == ["METADATA"]
        assert not (packages / name.replace("-", "_")).exists()
        assert not (packages / (name.replace("-", "_") + ".py")).exists()
    # The isolated interpreter uses the real backend and real distribution metadata.
    code = r"""
import importlib, importlib.metadata, sys, types
sys.path[:0] = [sys.argv[1], sys.argv[2]]
from slaif_raggedized_helper import gpu_embedding_backend as b
original = importlib.import_module
calls = []
factory = object()
def facade(name):
    calls.append(name)
    key = name.replace('_', '-')
    module = types.SimpleNamespace(__version__=b._PINS[key])
    if key == 'transformers': module.XLMRobertaModel = factory
    return module
importlib.import_module = facade
_, result = b._framework()
assert result is factory and len(calls) == 6
calls.clear()
version = importlib.metadata.version
def bad_version(name):
    return '0' if name == 'torch' else version(name)
importlib.metadata.version = bad_version
try: b._framework()
except ValueError: pass
else: raise AssertionError('metadata mismatch accepted')
assert not calls
importlib.metadata.version = version
def bad_module(name):
    obj = facade(name)
    if name == 'torch': obj.__version__ = '0'
    return obj
importlib.import_module = bad_module
try: b._framework()
except ValueError: pass
else: raise AssertionError('module mismatch accepted')
"""
    result = subprocess.run(
        [str(runtime / "bin/python3.12"), "-I", "-c", code, str(ROOT / "src"), str(packages)],
        env={"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8"},
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode == 0, result.stderr


def test_wrong_runtime_facts_refuse_before_target_or_install(monkeypatch):
    import uuid

    runtime = os.environ["SLAIF_GPU_TEST_ROOT"]
    target = Path("/tmp") / ("gpu-facts-" + uuid.uuid4().hex)
    calls = []
    monkeypatch.setattr(sys, "argv", ["setup", "--runtime-dir", runtime, "--target", str(target)])
    monkeypatch.setattr(setup.signal, "alarm", lambda *args: None)
    monkeypatch.setattr(setup.signal, "signal", lambda *args: None)
    monkeypatch.setattr(setup.resource, "setrlimit", lambda *args: None)
    monkeypatch.setattr(setup.shutil, "which", lambda name: "/usr/bin/true")

    def fake_run(argv, *args):
        calls.append(argv)
        return "cpython\n3.11.0\n" + runtime + "\n"

    monkeypatch.setattr(setup._support, "run", fake_run)
    with pytest.raises(ValueError, match="runtime facts"):
        setup.main()
    assert len(calls) == 1 and not target.exists()
