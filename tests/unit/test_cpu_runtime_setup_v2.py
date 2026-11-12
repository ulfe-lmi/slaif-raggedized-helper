"""Controlled-fake tests; never acquire or import framework packages.

Root amendment 1 (oap/reviews/007-h-ci-portability-addendum-1.md, same
active 007-h): the frozen D preflight consumed the production Root
absolute runtime/UV host paths, which do not exist on clean CI
runners. Per that amendment, the run_setup fake-flow cases use a
self-contained controlled-fake preflight in OWN tmp_path (scoped
m.RUNTIME/m.UV to owned private dummy files plus a narrow test-only
identity boundary for the designated dummy bytes only; all other
hashing stays real). Test-only fake identity is NOT actual binary
qualification; no stub binary is executed, and no test needs Root's
real fixed path, real UV/interpreter binaries, network or framework
packages.
"""

import hashlib
import importlib.util
import io
from email.message import Message
from pathlib import Path
import sys
import time

import pytest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "runtime_setup_v2", ROOT / "tests/support/prepare_cpu_runtime_v2.py"
)
m = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m)

PY_DUMMY = b"cpu-v2-fake-python-dummy"
UV_DUMMY = b"cpu-v2-fake-uv-dummy"
INTERPRETER_IDENTITY = "708fefcd7df61b1327cb7b9740fafd42cb2f6cd1d387378892d4a28b7479fb78"
UV_IDENTITY = "b65f23a420c4acc96427efb30e5ed9bc0f7e25d2d712000f6ede77c1a0de5f46"


class _Digest:
    def __init__(self, hexdigest):
        self._hexdigest = hexdigest

    def hexdigest(self):
        return self._hexdigest


class FakeIdentityBoundary:
    """Narrow test-only identity boundary (amendment 007-h-1).

    Maps ONLY the designated dummy binary byte sequences to the
    production identity digests; every other hash is computed by the
    real hashlib. Test-only fake identity, not actual binary
    qualification.
    """

    def __init__(self, mapping):
        self._mapping = mapping

    def __getattr__(self, name):
        return getattr(hashlib, name)

    def sha256(self, data=b"", *args, **kwargs):
        raw = bytes(data) if isinstance(data, (bytes, bytearray)) else None
        if raw is not None and raw in self._mapping:
            return _Digest(self._mapping[raw])
        return hashlib.sha256(data, *args, **kwargs)


def install_fake_preflight(monkeypatch, tmp_path, interpreter_bytes=PY_DUMMY, uv_bytes=UV_DUMMY):
    """Self-contained controlled-fake preflight in OWN tmp_path (amendment
    007-h-1): scoped m.RUNTIME/m.UV to owned private dummy files with the
    narrow identity boundary for the designated dummy bytes only. All
    other hashing is delegated to the real hashlib; no stub binary is
    executed and production constants are not changed."""
    runtime = tmp_path / "fake-runtime"
    (runtime / "bin").mkdir(parents=True, exist_ok=True)
    (runtime / "bin" / "python3.12").write_bytes(interpreter_bytes)
    uv = tmp_path / "fake-uv"
    uv.write_bytes(uv_bytes)
    monkeypatch.setattr(m, "RUNTIME", runtime)
    monkeypatch.setattr(m, "UV", uv)
    mapping = {}
    if interpreter_bytes == PY_DUMMY:
        mapping[PY_DUMMY] = INTERPRETER_IDENTITY
    if uv_bytes == UV_DUMMY:
        mapping[UV_DUMMY] = UV_IDENTITY
    monkeypatch.setattr(m, "hashlib", FakeIdentityBoundary(mapping))
    return runtime


class Response:
    def __init__(self, data, url, size=None, content_type="application/octet-stream"):
        self.data = io.BytesIO(data)
        self.url = url
        self.status = 200
        self.headers = Message()
        self.headers["Content-Length"] = str(len(data) if size is None else size)
        if content_type is not None:
            self.headers["Content-Type"] = content_type

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.data.close()

    def geturl(self):
        return self.url

    def read(self, size):
        return self.data.read(size)


class Opener:
    def __init__(self, response):
        self.response, self.calls = response, 0

    def open(self, req, timeout):
        self.calls += 1
        return self.response


def item(data=b"fixture"):
    return {
        "name": "example",
        "version": "1",
        "url": "https://files.pythonhosted.org/example.whl",
        "size": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def test_real_selection_and_lock_provenance(tmp_path):
    selected = m.select()
    assert len(selected) == 38 and len({x["name"] for x in selected}) == 38
    torch = next(x for x in selected if x["name"] == "torch")
    assert (torch["version"], torch["sha256"], torch["size"], torch["size_source"]) == (
        "2.14.0+cpu",
        m.TORCH_HASH,
        196253793,
        "independent HEAD",
    )
    assert sum(x["size"] for x in selected) < m.PAYLOAD_LIMIT
    bad = tmp_path / "lock"
    bad.write_bytes(m.LOCK.read_bytes() + b"\n")
    with pytest.raises(ValueError, match="lock"):
        m.select(bad)


def test_bad_url_and_ambiguous_wheel(monkeypatch, tmp_path):
    for url in (
        "http://files.pythonhosted.org/a.whl",
        "https://a@files.pythonhosted.org/a.whl",
        "https://files.pythonhosted.org/a.whl?token=x",
        "https://evil.test/a.whl",
    ):
        with pytest.raises(ValueError):
            m.check_url(url, "example")
    raw = m.LOCK.read_bytes()
    line = next(
        x for x in raw.splitlines(keepends=True) if b"annotated_doc-0.0.6-py3-none-any.whl" in x
    )
    changed = raw.replace(line, line + line, 1)
    bad = tmp_path / "lock"
    bad.write_bytes(changed)
    monkeypatch.setattr(m, "LOCK_HASH", hashlib.sha256(changed).hexdigest())
    with pytest.raises(ValueError, match="ambiguous"):
        m.select(bad)


def test_stream_success_and_failures(tmp_path, monkeypatch):
    data = b"fixture"
    spec = item(data)
    counter = [0]
    op = Opener(Response(data, spec["url"]))
    assert m.download(spec, tmp_path / "ok", counter, time.monotonic() + 10, op) == len(data)
    assert counter == [len(data)] and (tmp_path / "ok").read_bytes() == data and op.calls == 1
    for label, response, alter in [
        ("short", Response(data[:-1], spec["url"], len(data)), {}),
        ("long", Response(data + b"x", spec["url"], len(data)), {}),
        ("hash", Response(data, spec["url"]), {"sha256": "0" * 64}),
        ("redirect", Response(data, "https://evil.test/a.whl"), {}),
        ("type", Response(data, spec["url"], content_type="text/html"), {}),
    ]:
        calls = Opener(response)
        with pytest.raises(ValueError):
            m.download(spec | alter, tmp_path / label, [0], time.monotonic() + 10, calls)
        assert calls.calls == 1
    calls = Opener(Response(data, spec["url"]))
    with pytest.raises(ValueError, match="payload"):
        m.download(spec, tmp_path / "budget", [m.PAYLOAD_LIMIT], time.monotonic() + 10, calls)
    assert calls.calls == 1
    calls = Opener(Response(data, spec["url"]))
    with pytest.raises(TimeoutError):
        m.download(spec, tmp_path / "deadline", [0], time.monotonic() - 1, calls)
    assert calls.calls == 0


def test_target_and_early_refusal(tmp_path, monkeypatch):
    sentinel = tmp_path / "sentinel"
    sentinel.write_text("safe")
    calls = []
    for name in ("PYTHONPATH", "VIRTUAL_ENV", "CONDA_PREFIX"):
        monkeypatch.delenv(name, raising=False)
    install_fake_preflight(monkeypatch, tmp_path)
    with pytest.raises(ValueError, match="direct /tmp child"):
        m.run_setup(tmp_path, m.RUNTIME, runner=lambda *a: calls.append(a))
    assert calls == [] and sentinel.read_text() == "safe"
    with pytest.raises(ValueError, match="runtime mismatch"):
        m.run_setup(Path("/tmp/anything"), Path("/bad"), runner=lambda *a: calls.append(a))
    assert calls == []
    monkeypatch.setattr(m.platform, "machine", lambda: "wrong")
    with pytest.raises(ValueError, match="platform mismatch"):
        m.run_setup(Path("/tmp/anything"), m.RUNTIME, runner=lambda *a: calls.append(a))
    assert calls == []


def test_fake_preflight_identity_probe_and_ambient_negatives(tmp_path, monkeypatch):
    """Wrong interpreter/UV identity and ambient application environment
    are refused before any runner call, download or target operation;
    wrong runtime facts are refused before any target operation."""
    import shutil
    import uuid

    for name in ("PYTHONPATH", "VIRTUAL_ENV", "CONDA_PREFIX"):
        monkeypatch.delenv(name, raising=False)
    target = Path("/tmp") / ("cpu-v2-negative-" + uuid.uuid4().hex)
    facts_runner_calls = []

    def facts_runner(*args, **kwargs):
        facts_runner_calls.append(1)
        return "cpython\n3.12.15\n" + str(m.RUNTIME) + "\n"

    try:
        install_fake_preflight(monkeypatch, tmp_path, interpreter_bytes=PY_DUMMY + b"-wrong")
        with pytest.raises(ValueError, match="interpreter identity mismatch"):
            m.run_setup(target, m.RUNTIME, runner=facts_runner)
        assert facts_runner_calls == [] and not target.exists()

        install_fake_preflight(monkeypatch, tmp_path, uv_bytes=UV_DUMMY + b"-wrong")
        with pytest.raises(ValueError, match="uv identity mismatch"):
            m.run_setup(target, m.RUNTIME, runner=facts_runner)
        assert facts_runner_calls == [] and not target.exists()

        install_fake_preflight(monkeypatch, tmp_path)
        with pytest.raises(ValueError, match="interpreter facts mismatch"):
            m.run_setup(
                target,
                m.RUNTIME,
                runner=lambda *a, **k: "cpython\n3.13.0\n" + str(m.RUNTIME) + "\n",
            )
        assert facts_runner_calls == [] and not target.exists()

        monkeypatch.setenv("VIRTUAL_ENV", "/fake/venv")
        with pytest.raises(ValueError, match="ambient application environment"):
            m.run_setup(target, m.RUNTIME, runner=facts_runner)
        assert facts_runner_calls == [] and not target.exists()
    finally:
        if target.exists():
            shutil.rmtree(target)


def test_metadata_and_offline_commands(tmp_path):
    selected = [{"name": "a", "version": "1"}, {"name": "b", "version": "2"}]
    assert m.validate_metadata([["a", "1", ["b>=2"]], ["b", "2", []]], selected) == {
        "a": "1",
        "b": "2",
    }
    for rows in (
        [["a", "1", []], ["a", "1", []]],
        [["a", "1", []]],
        [["a", "1", ["b>2"]], ["b", "2", []]],
        [["a", "1", []], ["b", "2", []], ["c", "1", []]],
    ):
        with pytest.raises(ValueError):
            m.validate_metadata(rows, selected)
    create, install = m.install_commands(tmp_path, selected)
    assert "--offline" in create and "--no-python-downloads" in create
    assert all(
        x in install
        for x in ("--offline", "--no-index", "--no-deps", "--require-hashes", "--only-binary")
    )
    env = m.sanitized_env(tmp_path)
    assert "PYTHONPATH" not in env and "HTTPS_PROXY" not in env and env["UV_OFFLINE"] == "1"


def test_real_bounded_process():
    assert (
        m.run(
            [sys.executable, "-I", "-S", "-c", 'print("ok")'], {"PATH": "/usr/bin:/bin"}, 5
        ).strip()
        == "ok"
    )
    with pytest.raises(RuntimeError):
        m.run(
            [sys.executable, "-I", "-S", "-c", "raise SystemExit(1)"], {"PATH": "/usr/bin:/bin"}, 5
        )
    with pytest.raises(TimeoutError):
        m.run(
            [sys.executable, "-I", "-S", "-c", "import time; time.sleep(2)"],
            {"PATH": "/usr/bin:/bin"},
            0.1,
        )
    assert not m.UNREAPED


def test_full_fake_flow_and_no_install_before_verification(monkeypatch, tmp_path):
    import json
    import shutil
    import uuid

    items = []
    for i in range(38):
        payload = f"wheel-{i}".encode()
        items.append(
            {
                "name": f"pkg-{i}",
                "version": "1",
                "filename": f"pkg_{i}-1-py3-none-any.whl",
                "url": f"https://files.pythonhosted.org/{i}.whl",
                "size": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest(),
            }
        )
    torch_data = b"wheel-37"
    items[-1].update(name="torch", version="2.14.0+cpu", url=m.TORCH_URL)
    monkeypatch.setattr(m, "TORCH_HASH", hashlib.sha256(torch_data).hexdigest())
    monkeypatch.setattr(m, "TORCH_SIZE", len(torch_data))
    monkeypatch.setattr(m, "select", lambda: items)
    for name in ("PYTHONPATH", "VIRTUAL_ENV", "CONDA_PREFIX"):
        monkeypatch.delenv(name, raising=False)
    install_fake_preflight(monkeypatch, tmp_path)

    class FakeOpener:
        def __init__(self, fail=None):
            self.count, self.fail = 0, fail

        def open(self, req, timeout):
            i = self.count
            self.count += 1
            data = f"wheel-{i}".encode()
            if self.fail == "interrupt" and i == 10:
                raise KeyboardInterrupt()
            return Response(
                data if i != self.fail else b"broken!",
                req.full_url,
                len(data),
                content_type=None if i == 37 else "application/octet-stream",
            )

    for fail in (None, 10, "interrupt"):
        target = Path("/tmp") / ("cpu-v2-fake-" + uuid.uuid4().hex)
        op = FakeOpener(fail)
        commands = []

        def runner(argv, env, timeout, root=None):
            commands.append(argv)
            if "-c" in argv and "implementation.name" in argv[-1]:
                return "cpython\n3.12.15\n" + str(m.RUNTIME) + "\n"
            if "-c" in argv:
                return json.dumps([[x["name"], x["version"], []] for x in items])
            assert op.count == 38
            return ""

        try:
            if fail is None:
                result = m.run_setup(target, m.RUNTIME, opener=op, runner=runner)
                assert result["state"] == "complete" and len(result["verified"]) == 38
                assert result["payload_bytes_observed"] == sum(x["size"] for x in items)
                assert len(commands) == 4 and op.count == 38
                torch_obs = result["verification_details"][-1]
                assert torch_obs["content_type_raw"] is None
                assert torch_obs["content_type_policy"] == "exact_torch_missing"
                assert torch_obs["actual_sha256"] == m.TORCH_HASH
                assert torch_obs["actual_bytes"] == len(torch_data)
            else:
                with pytest.raises(KeyboardInterrupt if fail == "interrupt" else ValueError):
                    m.run_setup(target, m.RUNTIME, opener=op, runner=runner)
                receipt = json.loads((target / "setup-evidence.json").read_text())
                assert receipt["state"] == "partial" and len(receipt["verified"]) == 10
                assert len(commands) == 1 and op.count == 11
        finally:
            if target.exists():
                shutil.rmtree(target)


def test_uncertain_cleanup_retains_owned_handle(monkeypatch):
    import os
    import signal

    original_killpg = os.killpg

    def deny(*args):
        raise PermissionError("controlled cleanup failure")

    monkeypatch.setattr(m.os, "killpg", deny)
    try:
        with pytest.raises(TimeoutError):
            m.run(
                [sys.executable, "-I", "-S", "-c", "import time; time.sleep(10)"],
                {"PATH": "/usr/bin:/bin"},
                0.05,
            )
        assert len(m.UNREAPED) == 1
        assert m.UNREAPED[0].poll() is None
    finally:
        for child in m.UNREAPED:
            original_killpg(child.pid, signal.SIGKILL)
            child.wait(timeout=2)
        m.UNREAPED.clear()


def test_existing_direct_target_and_bad_lock_no_operations(monkeypatch, tmp_path):
    import tempfile
    import uuid

    for name in ("PYTHONPATH", "VIRTUAL_ENV", "CONDA_PREFIX"):
        monkeypatch.delenv(name, raising=False)
    install_fake_preflight(monkeypatch, tmp_path)
    calls = []
    with tempfile.TemporaryDirectory(dir="/tmp") as existing:
        target = Path(existing)
        sentinel = target / "sentinel"
        sentinel.write_text("preserved")
        with pytest.raises(ValueError, match="already exists"):
            m.run_setup(target, m.RUNTIME, runner=lambda *a: calls.append(a))
        assert calls == [] and sentinel.read_text() == "preserved"
    target = Path("/tmp") / ("cpu-v2-absent-" + uuid.uuid4().hex)
    monkeypatch.setattr(m, "LOCK_HASH", "0" * 64)
    with pytest.raises(ValueError, match="lock"):
        m.run_setup(target, m.RUNTIME, runner=lambda *a: calls.append(a))
    assert calls == [] and not target.exists()


def test_receipt_failure_priority_and_atomic_partial(monkeypatch, tmp_path):
    import json
    import os
    import shutil
    import uuid

    for name in ("PYTHONPATH", "VIRTUAL_ENV", "CONDA_PREFIX"):
        monkeypatch.delenv(name, raising=False)
    install_fake_preflight(monkeypatch, tmp_path)

    class BrokenInterrupt(KeyboardInterrupt):
        def __str__(self):
            raise RuntimeError("string conversion must not run")

        def add_note(self, value):
            raise RuntimeError("diagnostic failure")

    for primary, secondary in (
        (BrokenInterrupt(), OSError("write")),
        (OSError("network"), KeyboardInterrupt("write")),
        (OSError("network"), OSError("write")),
    ):
        target = Path("/tmp") / ("cpu-v2-priority-" + uuid.uuid4().hex)
        counts = {"open": 0, "replace": 0}
        real_replace = os.replace

        class Opener:
            def open(self, *args, **kwargs):
                counts["open"] += 1
                raise primary

        def replace(src, dst):
            counts["replace"] += 1
            if counts["replace"] == 2:
                raise secondary
            return real_replace(src, dst)

        def runner(*args):
            return "cpython\n3.12.15\n" + str(m.RUNTIME) + "\n"

        try:
            with monkeypatch.context() as patch:
                patch.setattr(m.os, "replace", replace)
                observed = None
                try:
                    m.run_setup(target, m.RUNTIME, opener=Opener(), runner=runner)
                except BaseException as exc:
                    observed = exc
            expected = (
                secondary
                if isinstance(primary, Exception) and not isinstance(secondary, Exception)
                else primary
            )
            assert observed is expected
            assert counts == {"open": 1, "replace": 2}
            assert json.loads((target / "setup-evidence.json").read_text())["state"] == "partial"
            assert (target / ".setup-evidence.pending").exists()
        finally:
            if target.exists():
                shutil.rmtree(target)


def test_run_cleanup_and_note_interrupt_priority(monkeypatch):
    import os
    import signal

    original_killpg = os.killpg

    class Fault(OSError):
        def __init__(self, diagnostic):
            super().__init__("controlled operation")
            self.diagnostic = diagnostic

        def add_note(self, note):
            raise self.diagnostic

    cases = [
        (OSError("operation"), KeyboardInterrupt("cleanup"), None, "cleanup"),
        (Fault(KeyboardInterrupt("note")), OSError("cleanup"), None, "note"),
        (KeyboardInterrupt("first"), KeyboardInterrupt("later"), None, "primary"),
        (Fault(OSError("note")), OSError("cleanup"), None, "primary"),
    ]
    for primary, cleanup, _, expectation in cases:
        calls = []

        def fail_remaining(deadline):
            raise primary

        def fail_cleanup(pid, sig):
            calls.append((pid, sig))
            original_killpg(pid, sig)
            raise cleanup

        seen = None
        try:
            with monkeypatch.context() as patch:
                patch.setattr(m, "remaining", fail_remaining)
                patch.setattr(m.os, "killpg", fail_cleanup)
                try:
                    m.run(
                        [sys.executable, "-I", "-S", "-c", "import time; time.sleep(5)"],
                        {"PATH": "/usr/bin:/bin"},
                        1,
                    )
                except BaseException as exc:
                    seen = exc
            expected = {
                "primary": primary,
                "cleanup": cleanup,
                "note": getattr(primary, "diagnostic", None),
            }[expectation]
            assert seen is expected
            assert len(calls) == 1 and calls[0][1] == signal.SIGKILL
            assert len(m.UNREAPED) == 1 and m.UNREAPED[0].returncode is not None
        finally:
            m.UNREAPED.clear()


def test_missing_type_exact_torch_and_refusals(tmp_path, monkeypatch):
    data = b"tiny torch fixture"
    digest = hashlib.sha256(data).hexdigest()
    monkeypatch.setattr(m, "TORCH_HASH", digest)
    monkeypatch.setattr(m, "TORCH_SIZE", len(data))
    spec = {
        "name": "torch",
        "version": "2.14.0+cpu",
        "url": m.TORCH_URL,
        "size": len(data),
        "sha256": digest,
    }
    obs, total = {}, [0]
    assert m.download(
        spec,
        tmp_path / "ok-torch",
        total,
        time.monotonic() + 5,
        Opener(Response(data, spec["url"], content_type=None)),
        observation=obs,
    ) == len(data)
    assert total == [len(data)]
    assert obs == {
        "stage": "verified",
        "artifact": "torch",
        "error_code": None,
        "content_type_raw": None,
        "content_type_policy": "exact_torch_missing",
        "declared_content_length": str(len(data)),
        "actual_bytes": len(data),
        "actual_sha256": digest,
    }
    variants = [
        spec | {"name": "other", "url": "https://files.pythonhosted.org/a.whl"},
        spec | {"url": m.TORCH_URL.replace("%2B", "+")},
        spec | {"version": "2"},
        spec | {"sha256": "0" * 64},
        spec | {"size": len(data) + 1},
    ]
    for i, bad in enumerate(variants):
        counter = [0]
        op = Opener(Response(data, bad["url"], content_type=None))
        with pytest.raises(ValueError, match="content type"):
            m.download(bad, tmp_path / f"bad-{i}", counter, time.monotonic() + 5, op)
        assert counter == [0] and op.calls == 1
    for i, typ in enumerate(("text/html", "text/plain", "invalid", "application/zip; broken")):
        counter = [0]
        with pytest.raises(ValueError, match="content type"):
            m.download(
                spec,
                tmp_path / f"type-{i}",
                counter,
                time.monotonic() + 5,
                Opener(Response(data, spec["url"], content_type=typ)),
            )
        assert counter == [0]
    response = Response(data, spec["url"])
    response.headers["Content-Type"] = "application/zip"
    counter = [0]
    with pytest.raises(ValueError, match="content type"):
        m.download(spec, tmp_path / "duplicate", counter, time.monotonic() + 5, Opener(response))
    assert counter == [0]
    counter = [0]
    with pytest.raises(ValueError, match="digest"):
        m.download(
            spec,
            tmp_path / "hash-failure",
            counter,
            time.monotonic() + 5,
            Opener(Response(b"x" * len(data), spec["url"], content_type=None)),
        )
    assert counter == [len(data)]


def test_missing_type_policy_guard_is_causal(tmp_path, monkeypatch):
    spec = item()

    def rejects():
        counter = [0]
        op = Opener(Response(b"fixture", spec["url"], content_type=None))
        rejected = False
        try:
            m.download(spec, tmp_path / "guard", counter, time.monotonic() + 5, op)
        except ValueError:
            rejected = True
        assert rejected and counter == [0] and op.calls == 1

    rejects()
    monkeypatch.setattr(m, "missing_type_allowed", lambda item: True)
    with pytest.raises(AssertionError):
        rejects()


def test_disk_sampling_disappearance_and_errors(tmp_path, monkeypatch):
    import os

    temporary = tmp_path / "temporary"
    temporary.write_bytes(b"gone")
    (tmp_path / "stable").write_bytes(b"kept")
    assert m.disk_size(tmp_path) == 8
    walk = os.walk

    def churn(path, **kwargs):
        for parent, dirs, files in walk(path, **kwargs):
            if temporary.name in files:
                temporary.unlink()
            yield parent, dirs, files

    with monkeypatch.context() as patch:
        patch.setattr(m.os, "walk", churn)
        assert m.disk_size(tmp_path) == 4
    original = Path.lstat
    for error in (PermissionError("denied"), OSError("other")):

        def fail(path, *args, **kwargs):
            if path.name == "stable":
                raise error
            return original(path, *args, **kwargs)

        with monkeypatch.context() as patch:
            patch.setattr(Path, "lstat", fail)
            with pytest.raises(type(error)):
                m.disk_size(tmp_path)


def test_child_failure_status_and_output_limits():
    env = {"PATH": "/usr/bin:/bin"}
    with pytest.raises(m.ChildFailure) as exc:
        m.run([sys.executable, "-I", "-S", "-c", "print('known'); raise SystemExit(7)"], env, 5)
    assert (exc.value.code, exc.value.output) == (7, "known\n")
    for code in ("print('x'*70000)", "import os; os.write(1,b'\\xff')", "print('\\x01')"):
        with pytest.raises((RuntimeError, ValueError, UnicodeDecodeError)):
            m.run([sys.executable, "-I", "-S", "-c", code], env, 5)


def test_failed_command_receipt(monkeypatch, tmp_path):
    import json
    import shutil
    import uuid

    for name in ("PYTHONPATH", "VIRTUAL_ENV", "CONDA_PREFIX"):
        monkeypatch.delenv(name, raising=False)
    install_fake_preflight(monkeypatch, tmp_path)
    selected = [
        {"name": f"pkg-{i}", "version": "1", "sha256": "0" * 64, "filename": f"{i}.whl"}
        for i in range(38)
    ]
    monkeypatch.setattr(m, "select", lambda: selected)

    def download(item, dest, total, deadline, opener, sample, observation):
        observation.clear()
        observation.update(stage="verified", artifact=item["name"], actual_bytes=1)

    monkeypatch.setattr(m, "download", download)

    def runner(argv, env, timeout, root=None):
        if root is None:
            return "cpython\n3.12.15\n" + str(m.RUNTIME) + "\n"
        return m.run(
            [sys.executable, "-I", "-S", "-c", "print('failed'); raise SystemExit(7)"],
            env,
            timeout,
            root,
        )

    target = Path("/tmp") / ("cpu-v2-failure-test-" + uuid.uuid4().hex)
    try:
        with pytest.raises(m.ChildFailure):
            m.run_setup(target, m.RUNTIME, opener=object(), runner=runner)
        receipt = json.loads((target / "setup-evidence.json").read_text())
        assert receipt["state"] == "partial" and len(receipt["verified"]) == 38
        assert receipt["commands"][-1]["exit"] == 7
        assert receipt["commands"][-1]["output"] == "failed\n"
        assert receipt["commands"][-1]["output_bytes"] == 7
        assert receipt["observation"] == {
            "stage": "install",
            "artifact": None,
            "error_code": "install_failed",
        }
        assert receipt["verification_details"][-1]["actual_bytes"] == 1
    finally:
        if target.exists():
            shutil.rmtree(target)


def test_disk_sampling_directory_disappearance_and_root_errors(tmp_path, monkeypatch):
    import os
    import shutil

    subtree = tmp_path / "temporary"
    subtree.mkdir()
    (subtree / "payload").write_bytes(b"new")
    (tmp_path / "stable").write_bytes(b"kept")
    assert m.disk_size(tmp_path) >= 7
    walk = os.walk

    def churn(path, **kwargs):
        for parent, dirs, files in walk(path, **kwargs):
            if Path(parent) == tmp_path and subtree.name in dirs:
                shutil.rmtree(subtree)
            yield parent, dirs, files

    with monkeypatch.context() as patch:
        patch.setattr(m.os, "walk", churn)
        assert m.disk_size(tmp_path) == 4
    with pytest.raises(FileNotFoundError):
        m.disk_size(tmp_path / "missing")

    def walk_error(path, **kwargs):
        kwargs["onerror"](PermissionError(13, "denied", str(path)))
        yield from ()

    with monkeypatch.context() as patch:
        patch.setattr(m.os, "walk", walk_error)
        with pytest.raises(PermissionError):
            m.disk_size(tmp_path)
