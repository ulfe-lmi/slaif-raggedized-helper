import hashlib
import json
import math
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import pytest

from slaif_raggedized_helper import cpu_embedding_worker as worker


def test_profile_actual_metadata():
    lock = Path(__file__).resolve().parents[2] / "worker_profiles/cpu/uv.lock"
    packages = Path(os.environ["SLAIF_CPU_WORKER_TEST_PACKAGES"])
    assert len(worker._lock(lock)) == 28
    assert len(worker._profile(lock, packages)) == 64


@pytest.mark.parametrize("value", [b'{"a":1,"a":2}', b'{"a":NaN}', b"\xff"])
def test_strict_json(value):
    with pytest.raises((ValueError, UnicodeError)):
        worker._parse(value)


@pytest.mark.parametrize(
    "value", [[], [[True, 1]], [[1]], [[1, 20]], [[1, 2]] * 9, [[1, 2], [1, -1]]]
)
def test_admit_all_ids(value):
    with pytest.raises(ValueError):
        worker._rows(value, 20, 8)


@pytest.mark.parametrize("value", [True, 1, math.nan, math.inf, 0.1, 1e100])
def test_reject_non_fp32_output(value):
    with pytest.raises(ValueError):
        worker._output([[value] * 1024], 1)


def test_canonical_batch_and_immutable_output():
    rows = [[1, 2], [3, 4]]
    worker._rows(rows, 20, 8)
    assert (
        hashlib.sha256(worker._json(rows)).hexdigest()
        == hashlib.sha256(b"[[1,2],[3,4]]").hexdigest()
    )
    assert worker._output([[1.0] * 1024], 1) == ((1.0,) * 1024,)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"max_rows": 129},
        {"forward_seconds": 121},
        {"cpu_seconds": 601},
        {"calls": True},
        {"request_bytes": 2 * 1024**2 + 1},
    ],
)
def test_policy_ceiling(kwargs):
    with pytest.raises(worker.WorkerRefused):
        worker.Policy(**kwargs)


def test_bad_lock(tmp_path):
    path = tmp_path / "lock"
    path.write_text(json.dumps({"package": []}))
    with pytest.raises(ValueError):
        worker._lock(path)


def _protocol_worker(script, policy=None):
    import os
    import subprocess
    import sys
    import threading
    import time
    from types import SimpleNamespace

    obj = worker.CPUEmbeddingWorker.__new__(worker.CPUEmbeddingWorker)
    obj._guard = threading.Lock()
    obj._close_guard = threading.Lock()
    obj._timer = None
    obj.policy = policy or worker.Policy(forward_seconds=1, lifetime_seconds=5)
    obj._input = obj._output = obj._calls = 0
    obj._buffer = bytearray()
    obj._deadline = time.monotonic() + obj.policy.lifetime_seconds
    obj.vocab_size = 20
    obj.space = SimpleNamespace(space_id="space")
    obj.profile = "profile"
    obj._child = subprocess.Popen(
        ["/usr/bin/prlimit", "--as=1073741824", "--cpu=30", sys.executable, "-c", script],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    os.set_blocking(obj._child.stdin.fileno(), False)
    os.set_blocking(obj._child.stdout.fileno(), False)
    return obj


@pytest.mark.parametrize(
    "mutation",
    [
        "nonce",
        "digest",
        "space",
        "profile",
        "rows",
        "integer",
        "unknown",
        "duplicate",
        "nan",
        "eof",
        "hang",
        "oversize",
    ],
)
def test_bad_reply_kills_child(mutation):
    script = (
        """
import json,sys,time
req = json.loads(sys.stdin.readline())
r = dict(nonce=req['nonce'],digest=req['digest'],space='space',profile='profile',rows=[[1.0]*1024])
mutation = %r
if mutation in ('nonce','digest','space','profile'): r[mutation] = 'wrong'
if mutation == 'rows': r['rows'] = []
if mutation == 'integer': r['rows'][0][0] = 1
if mutation == 'unknown': r['extra'] = 1
if mutation == 'eof': sys.exit(0)
if mutation == 'hang': time.sleep(10)
if mutation == 'oversize': sys.stdout.write('x' * 20000 + '\\n'); sys.stdout.flush(); time.sleep(10)
if mutation == 'nan': r['rows'][0][0] = float('nan')
raw = json.dumps(r)
if mutation == 'duplicate': raw = raw[:-1] + ', "nonce":"bad"}'
sys.stdout.write(raw + '\\n'); sys.stdout.flush(); time.sleep(10)
"""
        % mutation
    )
    policy = worker.Policy(forward_seconds=2, lifetime_seconds=10, response_bytes=16384)
    positive_script = script.replace("mutation = %r" % mutation, "mutation = 'valid'")
    positive = _protocol_worker(positive_script, policy)
    assert positive.forward_cls([[1, 2]]) == ((1.0,) * 1024,)
    positive.close()
    obj = _protocol_worker(script, policy)
    child = obj._child
    with pytest.raises(worker.WorkerRefused):
        obj.forward_cls([[1, 2]])
    assert child.poll() is not None and obj._child is None
    with pytest.raises(worker.WorkerRefused):
        obj.forward_cls([[1, 2]])


def test_late_invalid_batch_sends_nothing():
    obj = _protocol_worker("import time; time.sleep(10)")
    child = obj._child
    with pytest.raises(worker.WorkerRefused):
        obj.forward_cls([[1, 2], [3, True]])
    assert obj._input == 0 and child.poll() is not None


def test_busy_does_not_kill_owned_child():
    obj = _protocol_worker("import time; time.sleep(10)")
    child = obj._child
    obj._guard.acquire()
    try:
        with pytest.raises(worker.WorkerRefused, match="busy"):
            obj.forward_cls([[1, 2]])
        assert child.poll() is None
    finally:
        obj._guard.release()
        obj.close()


def test_context_preserves_body_exception():
    obj = _protocol_worker("import time; time.sleep(10)")
    with pytest.raises(RuntimeError, match="body"):
        with obj:
            raise RuntimeError("body")
    assert obj._child is None


def test_child_malformed_startup_never_constructs(monkeypatch):
    import io
    from types import SimpleNamespace
    from slaif_raggedized_helper import cpu_embedding_backend, cpu_embedding_worker_main as main

    monkeypatch.setattr(main.sys, "version_info", (3, 12))
    monkeypatch.setattr(worker, "_profile", lambda *args: "profile")
    monkeypatch.setattr(
        cpu_embedding_backend, "CPUEmbeddingBackend", lambda *args: pytest.fail("model reached")
    )
    monkeypatch.setattr(main.sys, "stdin", SimpleNamespace(buffer=io.BytesIO(b'{"bad":1}\n')))
    monkeypatch.setattr(main.sys, "stdout", SimpleNamespace(buffer=io.BytesIO()))
    assert main.main() == 1


def test_partial_construction_and_private_error(tmp_path, monkeypatch, capsys):
    from test_cpu_embedding_backend import make_tree
    from slaif_raggedized_helper import native_tokenizers

    root = tmp_path / "private-synthetic-path"
    _, raw, inv, definition, tokenizer = make_tree(root)
    packages = Path(os.environ["SLAIF_CPU_WORKER_TEST_PACKAGES"])
    runtime = native_tokenizers.Runtime(
        Path(os.environ["SLAIF_CPU_WORKER_TEST_ROOT"]),
        packages,
        "python3.12",
    )

    def fail(*args, **kwargs):
        raise OSError("private-synthetic-path")

    monkeypatch.setattr(worker.subprocess, "Popen", fail)
    with pytest.raises(worker.WorkerRefused) as caught:
        worker.CPUEmbeddingWorker(raw, root, definition, tokenizer, inv.inventory_id, runtime)
    assert "private-synthetic-path" not in str(caught.value)
    captured = capsys.readouterr()
    assert "private-synthetic-path" not in captured.out + captured.err
    assert root.exists()


def test_child_rejects_bad_digest_before_forward(tmp_path, monkeypatch):
    import dataclasses
    import io
    from types import SimpleNamespace

    from slaif_raggedized_helper import cpu_embedding_backend, cpu_embedding_worker_main as main
    from test_cpu_embedding_backend import make_tree

    root = tmp_path / "tree"
    _, raw, inv, definition, tokenizer = make_tree(root)
    actual_space = worker.embedding_space.admit(raw, root, definition, tokenizer, inv.inventory_id)
    seen = []

    class FakeBackend:
        space = actual_space
        _vocab = 20

        def forward_cls(self, rows):
            pytest.fail("bad request reached forward")

        def close(self):
            seen.append("closed")

    startup = dict(
        manifest=raw.decode(),
        definition=definition.model_dump(),
        tokenizer={k: v for k, v in dataclasses.asdict(tokenizer).items() if k != "artifact"},
        inventory=inv.inventory_id,
        space=actual_space.space_id,
        profile="profile",
        policy=dataclasses.asdict(worker.Policy()),
        policy_id=worker._policy_identity(worker.Policy()),
        code_id=worker._code_identity(),
    )
    request = dict(nonce="a" * 32, digest="b" * 64, rows=[[1, 2]])
    stdin = io.BytesIO(worker._json(startup) + b"\n" + worker._json(request) + b"\n")
    stdout = io.BytesIO()
    monkeypatch.setattr(main.sys, "version_info", (3, 12))
    monkeypatch.setattr(main.sys, "stdin", SimpleNamespace(buffer=stdin))
    monkeypatch.setattr(main.sys, "stdout", SimpleNamespace(buffer=stdout))
    monkeypatch.setattr(worker, "_profile", lambda *args: "profile")
    monkeypatch.setattr(worker.embedding_space, "admit", lambda *args: actual_space)

    def construct(*args):
        seen.append("constructed")
        return FakeBackend()

    monkeypatch.setattr(cpu_embedding_backend, "CPUEmbeddingBackend", construct)
    assert main.main() == 1
    assert worker._parse(stdout.getvalue().strip())["ready"] is True
    assert seen == ["constructed", "closed"]
    for field in ("space", "profile", "policy_id", "code_id"):
        changed = dict(startup, **{field: "wrong"})
        monkeypatch.setattr(
            main.sys, "stdin", SimpleNamespace(buffer=io.BytesIO(worker._json(changed) + b"\n"))
        )
        second_stdout = io.BytesIO()
        monkeypatch.setattr(main.sys, "stdout", SimpleNamespace(buffer=second_stdout))
        assert main.main() == 1
        assert second_stdout.getvalue() == b""
        assert seen == ["constructed", "closed"]


def test_profile_rejects_unlisted_metadata(tmp_path):
    lock = Path(__file__).resolve().parents[2] / "worker_profiles/cpu/uv.lock"
    for name, version in worker._lock(lock).items():
        directory = tmp_path / (name + ".dist-info")
        directory.mkdir()
        (directory / "METADATA").write_text(
            f"Metadata-Version: 2.1\nName: {name}\nVersion: {version}\n"
        )
    assert worker._profile(lock, tmp_path)
    extra = tmp_path / "extra.dist-info"
    extra.mkdir()
    (extra / "METADATA").write_text("Metadata-Version: 2.1\nName: extra\nVersion: 1\n")
    with pytest.raises(ValueError):
        worker._profile(lock, tmp_path)


def test_close_busy_and_retry_unreaped_child():
    import subprocess

    obj = _protocol_worker("import time; time.sleep(10)")
    child = obj._child
    obj._guard.acquire()
    try:
        with pytest.raises(worker.WorkerRefused, match="busy"):
            obj.close()
        assert child.poll() is None
    finally:
        obj._guard.release()
        obj.close()

    class Unreaped:
        stdin = stdout = None

        def poll(self):
            return None

        def terminate(self):
            pass

        def kill(self):
            pass

        def wait(self, timeout):
            raise subprocess.TimeoutExpired("synthetic", timeout)

    obj._child = Unreaped()
    with pytest.raises(worker.WorkerRefused, match="cleanup"):
        obj.close()
    assert isinstance(obj._child, Unreaped)
    obj._child = None


def test_mutated_policy_and_bad_definition_refused_before_profile(tmp_path, monkeypatch):
    import warnings
    from slaif_raggedized_helper import native_tokenizers
    from test_cpu_embedding_backend import make_tree

    root = tmp_path / "tree"
    _, raw, inv, definition, tokenizer = make_tree(root)
    runtime = native_tokenizers.Runtime(
        Path(os.environ["SLAIF_CPU_WORKER_TEST_ROOT"]),
        Path(os.environ["SLAIF_CPU_WORKER_TEST_PACKAGES"]),
        "python3.12",
    )
    monkeypatch.setattr(worker, "_profile", lambda *args: pytest.fail("profile scanned"))
    policy = worker.Policy()
    object.__setattr__(policy, "max_rows", 129)
    with pytest.raises(worker.WorkerRefused):
        worker.CPUEmbeddingWorker(
            raw, root, definition, tokenizer, inv.inventory_id, runtime, policy
        )
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        with pytest.raises(worker.WorkerRefused):
            worker.CPUEmbeddingWorker(
                raw,
                root,
                definition.model_copy(update={"dimensions": "private-marker"}),
                tokenizer,
                inv.inventory_id,
                runtime,
            )
    assert not any("private-marker" in str(w.message) for w in caught)


def test_interrupt_reaps_and_propagates(monkeypatch):
    obj = _protocol_worker("import time; time.sleep(10)")
    child = obj._child

    def interrupt(*args):
        raise KeyboardInterrupt()

    monkeypatch.setattr(obj, "_exchange", interrupt)
    with pytest.raises(KeyboardInterrupt):
        obj.forward_cls([[1, 2]])
    assert child.poll() is not None


@pytest.mark.parametrize(
    "point,exception",
    [
        ("stream", KeyboardInterrupt),
        ("terminate", KeyboardInterrupt),
        ("wait", KeyboardInterrupt),
        ("terminate", OSError),
        ("wait", OSError),
    ],
)
def test_cleanup_interrupted_once_still_reaps(monkeypatch, point, exception):
    import time

    obj = _protocol_worker("import time; time.sleep(20)")
    child = obj._child
    stdin, stdout = child.stdin, child.stdout
    if point == "stream":

        class Once:
            @property
            def closed(self):
                return stdin.closed

            def close(self):
                if not hasattr(self, "hit"):
                    self.hit = True
                    raise exception("private")
                stdin.close()

        child.stdin = Once()
    else:
        original = getattr(child, point)
        seen = []

        def once(*args, **kwargs):
            if not seen:
                seen.append(True)
                raise exception("private")
            return original(*args, **kwargs)

        monkeypatch.setattr(child, point, once)
    start = time.monotonic()
    with pytest.raises(
        KeyboardInterrupt if exception is KeyboardInterrupt else worker.WorkerRefused
    ):
        obj.close()
    assert time.monotonic() - start < 3
    assert child.poll() is not None and stdin.closed and stdout.closed and obj._child is None


def test_body_exception_preserved_on_cleanup_interrupt():
    obj = _protocol_worker("import time; time.sleep(20)")
    child = obj._child
    stream = child.stdin

    class Once:
        @property
        def closed(self):
            return stream.closed

        def close(self):
            if not hasattr(self, "hit"):
                self.hit = True
                raise KeyboardInterrupt("private")
            stream.close()

    child.stdin = Once()
    with pytest.raises(RuntimeError, match="body") as caught:
        with obj:
            raise RuntimeError("body")
    assert caught.value.__notes__ == ["worker cleanup refused"]
    assert child.poll() is not None and stream.closed
