"""Actual owned parent and native-tokenizer software composition; no GPU model."""

import dataclasses
import hashlib
import inspect
import json
import math
import os
from pathlib import Path
import subprocess
import textwrap

import pytest

from slaif_raggedized_helper import embedding_artifacts
from slaif_raggedized_helper import gpu_embedding_worker as parent
from slaif_raggedized_helper import gpu_worker_launch as launch
from slaif_raggedized_helper import isolated_gpu_embedding as bridge
from test_gpu_worker_launch import _prepared_fixture
from test_native_tokenizers import make_native


@pytest.fixture
def owned_parent(tmp_path, monkeypatch, request):
    paths, runtime, _ = make_native(tmp_path)
    args, reservation = _prepared_fixture(tmp_path, monkeypatch)
    args["wire_policy"] = dataclasses.replace(args["wire_policy"], calls=3)
    root = Path(args["artifact_root"])
    token = paths[0].read_bytes()
    (root / "tokenizer.json").write_bytes(token)
    manifest = json.loads(args["manifest"])
    entry = next(item for item in manifest["files"] if item["role"] == "tokenizer")
    entry.update(size=len(token), sha256=hashlib.sha256(token).hexdigest())
    args["manifest"] = json.dumps(manifest).encode()
    args["inventory_id"] = embedding_artifacts.verify_artifacts(args["manifest"], root).inventory_id
    args["tokenizer"] = dataclasses.replace(args["tokenizer"], sha256=entry["sha256"])
    prepared = launch.prepare(**args)
    worker = None
    fake_fd = None
    try:
        script = (Path(prepared._owner.directory) / "worker.py").read_text()
        marker = 'if __name__ == "__main__":\n    sys.exit(main())'
        injection = """
class FakeBackend:
    def __init__(self, manifest, root, definition, tokenizer, inventory, lease, uuid):
        self.space = embedding_space.admit(manifest, root, definition, tokenizer, inventory)
        self._vocab = 20
    def forward_cls(self, rows):
        return [[float(row[0]), float(len(row))] + [0.0] * 1022 for row in rows]
    def close(self):
        pass
gpu_embedding_backend.GPUEmbeddingBackend = FakeBackend
"""
        assert script.count(marker) == 1
        if getattr(request, "param", None) == "wrong-binding":
            predicate = '{**binding, "nonce": nonce, "digest": digest, "rows": result}'
            altered = (
                '{**binding, "space": "0" * 64, "nonce": nonce, "digest": digest, "rows": result}'
            )
            assert script.count(predicate) == 1
            script = script.replace(predicate, altered)
        harness = script.replace(marker, injection + "\n" + marker).encode()
        path = tmp_path / "gpu-harness.py"
        path.write_bytes(harness)
        path.chmod(0o400)
        print("harness_sha256=" + hashlib.sha256(harness).hexdigest())
        fake_fd = os.open(path, os.O_RDONLY | os.O_CLOEXEC)
        worker_fd = prepared._descriptors["worker"]
        original = subprocess.Popen.__init__

        def intercept(process, argv, **kwargs):
            argv = list(argv)
            index = argv.index("/worker.py")
            assert argv[index - 1] == f"/proc/self/fd/{worker_fd}"
            argv[index - 1] = f"/proc/self/fd/{fake_fd}"
            kwargs["pass_fds"] = tuple(
                fake_fd if fd == worker_fd else fd for fd in kwargs["pass_fds"]
            )
            return original(process, argv, **kwargs)

        with monkeypatch.context() as context:
            context.setattr(subprocess.Popen, "__init__", intercept)
            worker = parent.GPUEmbeddingWorker(prepared)
        yield worker, runtime, reservation
    finally:
        if worker is not None:
            worker.close()
        if fake_fd is not None:
            os.close(fake_fd)
        prepared.close()
        reservation.close()


def test_actual_two_batches_and_renewal(owned_parent, monkeypatch):
    worker, runtime, reservation = owned_parent
    with bridge.GPUTextEmbeddingSession(worker, runtime) as session:
        plan = session._plan
        assert (
            bridge.validate_record(plan.execution_record, plan.native_runtime_record)
            == plan.execution_fingerprint
        )
        child = session._native._child
        read_fd, write_fd = os.pipe()
        forked = os.fork()
        if forked == 0:
            os.close(read_fd)
            try:
                session.close()
            except bridge.SessionRefused:
                os.write(write_fd, b"R")
            finally:
                os.close(write_fd)
                os._exit(0)
        os.close(write_fd)
        try:
            assert os.read(read_fd, 1) == b"R"
            assert os.waitpid(forked, 0)[1] == 0
        finally:
            os.close(read_fd)
        assert session._native._child is child and child.poll() is None
        # Position the actual parent's counter synthetically to prove pre-exposure refusal.
        calls = worker._calls
        worker._calls = worker._policy.calls - 1
        try:
            with pytest.raises(ValueError):
                session._budget(1)
        finally:
            worker._calls = calls
        with pytest.raises(bridge.SessionRefused):
            session.__init__(worker, runtime)
        session._initialized = False
        try:
            with pytest.raises(bridge.SessionRefused):
                session.__init__(worker, runtime)
        finally:
            session._initialized = True
        assert session._native._child is child and child.poll() is None
        assert session._lock.acquire(blocking=False)
        try:
            with pytest.raises(bridge.SessionRefused):
                session.close()
        finally:
            session._lock.release()
        first = session.encode(["hello café 世界", "hello"])
        assert [r.ids for r in first.receipts] == [(1, 3, 4, 5, 2), (1, 3, 2)]
        assert (
            first.receipts[0].input_sha256
            == hashlib.sha256(
                json.dumps(
                    ["hello café 世界", None], ensure_ascii=True, separators=(",", ":")
                ).encode()
            ).hexdigest()
        )
        assert math.isclose(first.vectors.rows[0][0], 1 / math.sqrt(26), rel_tol=1e-6)
        assert math.isclose(first.vectors.rows[0][1], 5 / math.sqrt(26), rel_tol=1e-6)
        assert first.execution_record == plan.execution_record
        forged = dataclasses.replace(first.receipts[0], input_sha256="0" * 64)
        with pytest.raises(ValueError):
            session._receipt(forged, "hello café 世界")
        # Narrow causal control on the actual owned receipt: remove only the digest
        # predicate in a temporary function, without modifying the session or class.
        source = textwrap.dedent(inspect.getsource(type(session)._receipt))
        predicate = "or receipt.input_sha256 != digest"
        assert source.count(predicate) == 1
        namespace = dict(bridge.__dict__)
        exec(
            compile(source.replace(predicate, "or False"), "<receipt-control>", "exec"),
            namespace,
        )
        namespace["_receipt"](session, forged, "hello café 世界")
        saved = session._vocab
        session._vocab = saved + 1
        with pytest.raises(ValueError):
            session._check()
        session._vocab = saved
        planned_fingerprint = plan.execution_fingerprint
        object.__setattr__(plan, "execution_fingerprint", "sha256:" + "0" * 64)
        try:
            with pytest.raises(ValueError):
                session._check()
        finally:
            object.__setattr__(plan, "execution_fingerprint", planned_fingerprint)
        session._native._calls = 1024  # Synthetic budget position, not 1024 real calls.
        second = session.encode(["hello"])
        assert second.receipts[0].ids == (1, 3, 2)
        assert child.poll() is not None and session._native._child is not child
        assert second.execution_fingerprint == first.execution_fingerprint
        # Actual native owner remains retained when cleanup is interrupted; hostile
        # diagnostics must not replace the original non-Exception interruption.
        native_owner = session._native
        real_close = native_owner.close

        class HostileInterrupt(KeyboardInterrupt):
            def add_note(self, note):
                raise RuntimeError("diagnostics unavailable")

            def __setattr__(self, name, value):
                raise RuntimeError("attributes unavailable")

        def interrupted_close():
            raise RuntimeError("synthetic cleanup interruption")

        monkeypatch.setattr(native_owner, "close", interrupted_close)
        interruption = HostileInterrupt()
        with pytest.raises(HostileInterrupt) as caught:
            session._fail(interruption)
        assert caught.value is interruption
        assert bridge._owners[id(session)][3] is native_owner
        assert native_owner._child is not None and native_owner._tmp is not None
        monkeypatch.setattr(native_owner, "close", real_close)
    reservation.assert_owned()
    assert worker._state == "live"
    assert len(worker.forward_cls([[1, 3, 2]]).rows) == 1


def test_invalid_input_drains_only_native_before_exposure(owned_parent):
    worker, runtime, reservation = owned_parent
    session = bridge.GPUTextEmbeddingSession(worker, runtime)
    native = session._native
    child = native._child
    with pytest.raises(bridge.SessionRefused):
        session.encode(["\ud800"])
    assert native._calls == 0 and child.poll() is not None
    assert native._child is None and native._tmp is None
    assert worker._state == "live"
    reservation.assert_owned()
    assert len(worker.forward_cls([[1, 3, 2]]).rows) == 1
    session.close()


def test_constructor_interrupt_drains_owned_native_and_preserves_parent(owned_parent, monkeypatch):
    worker, runtime, reservation = owned_parent
    actual_init = subprocess.Popen.__init__
    children = []

    def interrupt_after_creation(process, argv, **kwargs):
        # GPU interceptor is already restored. This boundary is native worker startup.
        assert "/worker.py" in argv and "/artifact.json" in argv
        actual_init(process, argv, **kwargs)
        children.append(process)
        raise KeyboardInterrupt("synthetic native startup interruption")

    session = bridge.GPUTextEmbeddingSession.__new__(bridge.GPUTextEmbeddingSession)
    with monkeypatch.context() as context:
        context.setattr(subprocess.Popen, "__init__", interrupt_after_creation)
        with pytest.raises(KeyboardInterrupt, match="synthetic native startup"):
            session.__init__(worker, runtime)
    assert len(children) == 1 and children[0].poll() is not None
    assert session._admit()[3] is None
    session.close()
    assert worker._state == "live"
    reservation.assert_owned()
    assert len(worker.forward_cls([[1, 3, 2]]).rows) == 1


def test_context_preserves_body_interrupt_and_retains_actual_native(owned_parent, monkeypatch):
    worker, runtime, reservation = owned_parent
    session = bridge.GPUTextEmbeddingSession(worker, runtime)
    native = session._native
    actual_close = native.close

    class BodyInterrupt(KeyboardInterrupt):
        def add_note(self, note):
            raise RuntimeError("notes unavailable")

        def __setattr__(self, name, value):
            raise RuntimeError("attributes unavailable")

    def failed_close():
        raise RuntimeError("synthetic pending cleanup")

    monkeypatch.setattr(native, "close", failed_close)
    interrupt = BodyInterrupt()
    with pytest.raises(BodyInterrupt) as caught:
        with session:
            raise interrupt
    assert caught.value is interrupt
    assert bridge._owners[id(session)][3] is native
    assert native._child is not None and native._tmp is not None
    monkeypatch.setattr(native, "close", actual_close)
    session.close()
    assert native._child is None and native._tmp is None
    assert worker._state == "live"
    reservation.assert_owned()


@pytest.mark.parametrize("owned_parent", ["wrong-binding"], indirect=True)
def test_actual_wrong_binding_fault_drains_only_native_and_parent_own_cleanup(owned_parent):
    worker, runtime, reservation = owned_parent
    session = bridge.GPUTextEmbeddingSession(worker, runtime)
    native = session._native
    with pytest.raises(bridge.SessionRefused):
        session.encode(["hello"])
    assert native._child is None and native._tmp is None
    # The parent performs its own ordered fault cleanup for a hostile reply.
    assert worker._state != "live"
    reservation.assert_owned()
    session.close()


def test_changed_private_artifact_refuses_before_text_and_keeps_parent(owned_parent):
    worker, runtime, reservation = owned_parent
    session = bridge.GPUTextEmbeddingSession(worker, runtime)
    native = session._native
    artifact = Path(native._tmp.name) / "artifact.json"
    artifact.write_bytes(b"changed synthetic artifact")
    with pytest.raises(bridge.SessionRefused):
        session.encode(["hello"])
    assert native._calls == 0 and native._child is None and native._tmp is None
    assert worker._state == "live"
    reservation.assert_owned()
    session.close()


def test_changed_native_policy_type_refuses_actual_owner(owned_parent):
    worker, runtime, reservation = owned_parent
    session = bridge.GPUTextEmbeddingSession(worker, runtime)
    policy = session._native._policy
    original = policy.lifetime_seconds
    object.__setattr__(policy, "lifetime_seconds", float(original))
    try:
        with pytest.raises(ValueError):
            session._check()
    finally:
        object.__setattr__(policy, "lifetime_seconds", original)
        session.close()
    assert worker._state == "live"
    reservation.assert_owned()


def test_parent_instance_shadow_cannot_replace_actual_forward(owned_parent, monkeypatch):
    from slaif_raggedized_helper import gpu_worker_protocol as wire

    worker, runtime, reservation = owned_parent
    session = bridge.GPUTextEmbeddingSession(worker, runtime)
    native = session._native
    callbacks = []
    try:

        def forged(rows):
            callbacks.append(rows)
            return parent.RawCLSResult(
                tuple(sorted(wire.parse(session._ready).items())), ((1.0,) + (0.0,) * 1023,)
            )

        with monkeypatch.context() as patch:
            patch.setattr(worker, "forward_cls", forged)
            result = session.encode(["hello"])
        assert callbacks == []
        assert native._calls == 1 and worker._calls == 1
        assert result.receipts[0].ids == (1, 3, 2)
        assert math.isclose(result.vectors.rows[0][1], 3 / math.sqrt(10), rel_tol=1e-6)
    finally:
        session.close()
    assert native._child is None and native._tmp is None
    reservation.assert_owned()
    assert len(worker.forward_cls([[1, 3, 2]]).rows) == 1


def test_native_instance_shadow_cannot_replace_actual_encode(owned_parent, monkeypatch):
    from slaif_raggedized_helper import embedding_tokenizer

    worker, runtime, reservation = owned_parent
    session = bridge.GPUTextEmbeddingSession(worker, runtime)
    native = session._native
    callbacks = []
    definition = session._definition
    try:

        def forged(text):
            callbacks.append(text)
            digest = hashlib.sha256(
                json.dumps([text, None], ensure_ascii=True, separators=(",", ":")).encode()
            ).hexdigest()
            return embedding_tokenizer.TokenIDReceipt(
                (1, 3, 3, 3, 2),
                5,
                definition.sha256,
                definition.backend_version,
                definition.role,
                definition.model_revision,
                definition.preprocessing,
                digest,
                "c" * 32,
            )

        with monkeypatch.context() as patch:
            patch.setattr(native, "encode", forged)
            result = session.encode(["hello"])
        assert callbacks == []
        assert native._calls == 1 and worker._calls == 1
        assert result.receipts[0].ids == (1, 3, 2)
        assert math.isclose(result.vectors.rows[0][1], 3 / math.sqrt(10), rel_tol=1e-6)
    finally:
        session.close()
    assert native._child is None and native._tmp is None
    reservation.assert_owned()
    assert len(worker.forward_cls([[1, 3, 2]]).rows) == 1
