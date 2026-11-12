"""Real staged admission and native and CPU sandbox protocols with a trusted fake framework."""

import hashlib
import importlib.util
import json
import math
import os
import select
import signal
import struct
import threading
import time

import pytest
from dataclasses import replace
from pathlib import Path

from slaif_raggedized_helper import cpu_embedding_worker, embedding_artifacts, native_tokenizers
from slaif_raggedized_helper.isolated_cpu_embedding import IsolatedCPUEmbeddingSession
from slaif_raggedized_helper.schema import fingerprint


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_owned_composition(tmp_path, monkeypatch):
    tests = Path(__file__).resolve().parents[1]
    monkeypatch.syspath_prepend(str(tests / "unit"))
    backend = load("isolated_backend_fixture", tests / "unit/test_cpu_embedding_backend.py")
    native = load("isolated_native_fixture", tests / "unit/test_native_tokenizers.py")
    worker_fixture = load(
        "isolated_worker_fixture", tests / "integration/test_cpu_embedding_worker_composition.py"
    )
    paths, runtime, _ = native.make_native(tmp_path)
    root = tmp_path / "tree"
    manifest, _, _, definition, tokenizer = backend.make_tree(root)
    token = paths[0].read_bytes()
    (root / "tokenizer.json").write_bytes(token)
    entry = next(item for item in manifest["files"] if item["role"] == "tokenizer")
    entry.update(size=len(token), sha256=hashlib.sha256(token).hexdigest())
    raw = json.dumps(manifest).encode()
    inventory = embedding_artifacts.verify_artifacts(raw, root)
    tokenizer = replace(tokenizer, sha256=entry["sha256"])
    script = tmp_path / "fake.py"
    script.write_text(
        worker_fixture.FAKE.replace(
            "[[[float(x)] * 1024 for x in row] for row in ids]",
            "[[[float(x), float(len([i for i in row if i != 1]))] + [0.0] * 1022 "
            "for x in row] for row in ids]",
        )
    )
    original = cpu_embedding_worker._argv

    def intercept(*args):
        argv = original(*args)
        argv[argv.index("/worker.py") - 1] = str(script)
        return argv

    monkeypatch.setattr(cpu_embedding_worker, "_argv", intercept)
    cpu_runtime = native_tokenizers.Runtime(
        Path(os.environ["SLAIF_CPU_WORKER_TEST_ROOT"]),
        Path(os.environ["SLAIF_CPU_WORKER_TEST_PACKAGES"]),
        "python3.12",
    )
    policy = cpu_embedding_worker.Policy(
        address_bytes=1024**3, cpu_seconds=30, lifetime_seconds=120
    )
    with IsolatedCPUEmbeddingSession(
        raw,
        root,
        definition,
        tokenizer,
        inventory.inventory_id,
        runtime,
        cpu_runtime,
        worker_policy=policy,
    ) as obj:
        with pytest.raises(Exception):
            obj.__enter__()
        stage = obj._stage.gen.gi_frame.f_locals["stage_path"]
        cpu_child, native_child = obj._worker._child, obj._tokenizer._child
        first = obj.encode(["hello café 世界", "hello"])
        assert [r.ids for r in first.receipts] == [(1, 3, 4, 5, 2), (1, 3, 2)]
        assert math.isclose(first.vectors.rows[0][0], 1 / math.sqrt(17), rel_tol=1e-6)
        assert math.isclose(first.vectors.rows[0][1], 4 / math.sqrt(17), rel_tol=1e-6)
        assert math.isclose(first.vectors.rows[1][1], 2 / math.sqrt(5), rel_tol=1e-6)
        assert all(v == 0 for v in first.vectors.rows[0][2:])
        assert first.vectors.payload[:4096] == struct.pack(
            "<1024f", 1 / math.sqrt(17), 4 / math.sqrt(17), *([0.0] * 1022)
        )
        record = json.loads(first.execution_record)
        assert first.execution_fingerprint == fingerprint(
            {"kind": "isolated-cpu-embedding-execution-v2", **record}
        )
        obj._tokenizer._calls = 1024
        second = obj.encode(["hello"])
        assert second.receipts[0].ids == (1, 3, 2)
        assert native_child.poll() is not None and obj._tokenizer._child is not native_child
        vectors = obj.embed(["hello"])
        assert isinstance(vectors, list) and isinstance(vectors[0], list)
        vectors[0][0] = 99
        assert second.vectors.rows[0][0] != 99
        assert obj._worker._child is cpu_child and stage.exists()
        # A competing request must not shut down an in-flight forward.
        started, release = threading.Event(), threading.Event()
        actual_forward = obj._worker.forward_cls

        def held_forward(rows):
            started.set()
            assert release.wait(3)
            return actual_forward(rows)

        monkeypatch.setattr(obj._worker, "forward_cls", held_forward)
        outcome = []

        def run():
            try:
                outcome.append(obj.encode(["hello"]))
            except BaseException as error:
                outcome.append(error)

        thread = threading.Thread(target=run)
        thread.start()
        try:
            assert started.wait(3)
            with pytest.raises(Exception, match="busy"):
                obj.encode(["other"])
            assert cpu_child.poll() is None and stage.exists()
        finally:
            release.set()
            thread.join(timeout=5)
        assert (
            not thread.is_alive()
            and len(outcome) == 1
            and not isinstance(outcome[0], BaseException)
        )
        # The child process cannot close the parent's worker or stage.
        read_fd, write_fd = os.pipe()
        pid = os.fork()
        if pid == 0:
            os.close(read_fd)
            try:
                obj.close()
            except Exception:
                os.write(write_fd, b"refused")
            finally:
                os.close(write_fd)
                os._exit(0)
        os.close(write_fd)
        status = None
        try:
            assert select.select([read_fd], [], [], 3)[0]
            assert os.read(read_fd, 16) == b"refused"
            deadline = time.monotonic() + 3
            while time.monotonic() < deadline:
                completed, status = os.waitpid(pid, os.WNOHANG)
                if completed:
                    break
                status = None
                time.sleep(0.01)
            assert status is not None and os.waitstatus_to_exitcode(status) == 0
        finally:
            os.close(read_fd)
            if status is None:
                try:
                    os.kill(pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                deadline = time.monotonic() + 2
                while time.monotonic() < deadline:
                    completed, _ = os.waitpid(pid, os.WNOHANG)
                    if completed:
                        break
                    time.sleep(0.01)
                else:
                    raise AssertionError("owned fork child not reaped")
        assert cpu_child.poll() is None and stage.exists()
    assert cpu_child.poll() is not None and not stage.exists()
    with IsolatedCPUEmbeddingSession(
        raw,
        root,
        definition,
        tokenizer,
        inventory.inventory_id,
        runtime,
        cpu_runtime,
        worker_policy=replace(policy, max_rows=7),
    ) as changed_policy:
        result_policy = changed_policy.encode(["hello"])
        actual_forward = changed_policy._worker.forward_cls

        def alter_identity(rows):
            result = actual_forward(rows)
            changed_policy._worker.profile = "0" * 64
            return result

        monkeypatch.setattr(changed_policy._worker, "forward_cls", alter_identity)
        with pytest.raises(Exception):
            changed_policy.encode(["hello"])
    assert result_policy.space_id == first.space_id
    assert result_policy.intended_execution_fingerprint == first.intended_execution_fingerprint
    assert result_policy.execution_fingerprint != first.execution_fingerprint
    original_read = native_tokenizers._read_artifact

    def alternate_code(path, limit):
        content = original_read(path, limit)
        return (
            content + b"\n# simulated alternate bridge"
            if Path(path).name == ("isolated_cpu_embedding.py")
            else content
        )

    monkeypatch.setattr(native_tokenizers, "_read_artifact", alternate_code)
    with IsolatedCPUEmbeddingSession(
        raw,
        root,
        definition,
        tokenizer,
        inventory.inventory_id,
        runtime,
        cpu_runtime,
        worker_policy=policy,
    ) as changed_code:
        result_code = changed_code.encode(["hello"])
        actual_encode = changed_code._tokenizer.encode
        forwards = []

        def corrupt_second(text):
            receipt = actual_encode(text)
            return replace(receipt, ids=(1, 99999)) if text == "second" else receipt

        monkeypatch.setattr(changed_code._tokenizer, "encode", corrupt_second)
        monkeypatch.setattr(changed_code._worker, "forward_cls", lambda rows: forwards.append(rows))
        with pytest.raises(Exception):
            changed_code.encode(["hello", "second"])
        assert not forwards
    assert result_code.space_id == first.space_id
    assert result_code.execution_fingerprint != first.execution_fingerprint
    assert (
        json.loads(result_code.execution_record)["bridge"]
        != json.loads(first.execution_record)["bridge"]
    )


def test_failed_constructor_retains_owned_child_and_stage(tmp_path, monkeypatch):
    from slaif_raggedized_helper.isolated_cpu_embedding import SessionRefused

    tests = Path(__file__).resolve().parents[1]
    monkeypatch.syspath_prepend(str(tests / "unit"))
    backend = load("pending_backend_fixture", tests / "unit/test_cpu_embedding_backend.py")
    native = load("pending_native_fixture", tests / "unit/test_native_tokenizers.py")
    paths, runtime, _ = native.make_native(tmp_path)
    root = tmp_path / "tree"
    manifest, _, _, definition, tokenizer = backend.make_tree(root)
    token = paths[0].read_bytes()
    (root / "tokenizer.json").write_bytes(token)
    entry = next(item for item in manifest["files"] if item["role"] == "tokenizer")
    entry.update(size=len(token), sha256=hashlib.sha256(token).hexdigest())
    raw = json.dumps(manifest).encode()
    inventory = embedding_artifacts.verify_artifacts(raw, root)
    tokenizer = replace(tokenizer, sha256=entry["sha256"])
    script = tmp_path / "sleep.py"
    script.write_text("import time; time.sleep(4)")
    original_argv = cpu_embedding_worker._argv

    def intercept(*args):
        argv = original_argv(*args)
        argv[argv.index("/worker.py") - 1] = str(script)
        return argv

    monkeypatch.setattr(cpu_embedding_worker, "_argv", intercept)
    import subprocess

    methods = {}

    def fail_after_spawn(worker, *args):
        child = worker._child
        for name in ("poll", "wait", "terminate", "kill"):
            methods[name] = getattr(child, name)
        child.poll = lambda: None
        child.wait = lambda timeout=None: (_ for _ in ()).throw(
            subprocess.TimeoutExpired("owned-child", timeout)
        )
        child.terminate = lambda: None
        child.kill = lambda: None
        raise ValueError("private")

    monkeypatch.setattr(cpu_embedding_worker.CPUEmbeddingWorker, "_exchange", fail_after_spawn)
    cpu_runtime = native_tokenizers.Runtime(
        Path(os.environ["SLAIF_CPU_WORKER_TEST_ROOT"]),
        Path(os.environ["SLAIF_CPU_WORKER_TEST_PACKAGES"]),
        "python3.12",
    )
    policy = cpu_embedding_worker.Policy(address_bytes=1024**3, cpu_seconds=30, lifetime_seconds=5)
    obj = IsolatedCPUEmbeddingSession(
        raw,
        root,
        definition,
        tokenizer,
        inventory.inventory_id,
        runtime,
        cpu_runtime,
        worker_policy=policy,
    )
    child = None
    try:
        with pytest.raises(SessionRefused) as caught:
            obj.__enter__()
        assert caught.value.owner is obj and caught.value.pending
        child = obj._worker._child
        stage = obj._stage.gen.gi_frame.f_locals["stage_path"]
        assert child is not None and stage.exists()
        for name, method in methods.items():
            setattr(child, name, method)
        obj.close()
        assert child.poll() is not None and not stage.exists()
    finally:
        if child is not None:
            for name, method in methods.items():
                setattr(child, name, method)
        if child is not None and child.poll() is None:
            child.kill()
            child.wait(timeout=2)
        if obj._worker is not None:
            obj.close()


def test_context_exit_interrupt_after_actual_encode(tmp_path, monkeypatch):
    tests = Path(__file__).resolve().parents[1]
    monkeypatch.syspath_prepend(str(tests / "unit"))
    producer = load(
        "exit_producer_fixture", tests / "integration/test_cpu_embedding_producer_composition.py"
    )
    fixture = producer.fixture.__wrapped__(tmp_path, monkeypatch)
    args, policy, _ = next(fixture)
    obj = IsolatedCPUEmbeddingSession(*args[4:11], worker_policy=policy)
    interrupt = KeyboardInterrupt("cleanup")
    try:
        with pytest.raises(KeyboardInterrupt) as caught:
            with obj:
                assert len(obj.encode(["hello"]).vectors.rows) == 1
                child = obj._worker._child
                stage = obj._stage.gen.gi_frame.f_locals["stage_path"]
                original_close = obj._tokenizer.close

                def interrupted_close():
                    original_close()
                    raise interrupt

                monkeypatch.setattr(obj._tokenizer, "close", interrupted_close)
                raise RuntimeError("body")
        assert caught.value is interrupt and interrupt.cleanup_owner is obj
        assert obj._tokenizer is not None and obj._stage is not None and stage.exists()
        assert child.poll() is not None
        monkeypatch.setattr(obj._tokenizer, "close", original_close)
        obj.close()
        assert obj._tokenizer is None and obj._stage is None and not stage.exists()
    finally:
        if obj._tokenizer is not None:
            monkeypatch.setattr(obj._tokenizer, "close", original_close)
        obj.close()
        fixture.close()
