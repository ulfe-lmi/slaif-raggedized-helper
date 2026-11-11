"""Owned session boundaries with the real admission and fake framework."""
import hashlib
import json
import time
import tracemalloc
from pathlib import Path
from dataclasses import replace

import pytest

from slaif_raggedized_helper import cpu_embedding_session as s, embedding_tokenizer as t
from slaif_raggedized_helper.native_tokenizers import Runtime
from test_cpu_embedding_backend import Factory, Model, Torch, make_tree


class Worker:
    def __init__(self, definition, runtime):
        self.definition = definition
        self._policy = t.Policy()
        self._deadline = time.monotonic() + 300
        self._calls = self._input = 0
        self.closed = False
        self.change = lambda x: x

    def encode(self, text):
        self._calls += 1
        self._input += len(json.dumps({"text": text, "nonce": "0" * 32}, ensure_ascii=True,
                                      separators=(",", ":")).encode()) + 1
        d = self.definition
        digest = hashlib.sha256(json.dumps([text, None], ensure_ascii=True,
                                          separators=(",", ":")).encode()).hexdigest()
        return self.change(t.TokenIDReceipt((1, 3, 2), 3, d.sha256, d.backend_version, d.role,
                                            d.model_revision, d.preprocessing, digest, "0" * 32))

    def close(self):
        self.closed = True


@pytest.fixture
def setup(tmp_path, monkeypatch):
    root = tmp_path / "tree"
    _, raw, inv, d, tokenizer = make_tree(root)
    model = Model()
    factory = Factory(model)
    monkeypatch.setattr(s.cpu_embedding_backend, "_framework", lambda: (Torch(), factory))
    monkeypatch.setattr(t, "TokenIDSession", Worker)
    def create():
        runtime = Runtime(Path("/fake"), Path("/fake"))
        return s.CPUEmbeddingSession(raw, root, d, tokenizer, inv.inventory_id, runtime)
    return create, model, factory


def test_positive_reuse_and_fresh_lists(setup):
    create, model, factory = setup
    with create() as obj:
        first = obj.embed(["one", "two"])
        first[0][0] = 999
        assert obj.embed(["one"])[0][0] == 0.03125
        assert len(model.calls) == 2 and len(factory.calls) == 1


@pytest.mark.parametrize("bad", ["x" * 100001, "\ud800", "é" * 40000])
def test_late_invalid_preflight_no_worker_or_forward(setup, bad):
    create, model, _ = setup
    obj = create()
    worker, staged = obj._tokenizer, obj._staged.path
    with pytest.raises(s.SessionRefused, match="^embedding session refused$"):
        obj.embed(["valid", bad])
    assert worker._calls == 0 and not model.calls and worker.closed and not staged.exists()


@pytest.mark.parametrize("changes", [{"count": 2}, {"ids": (1, 999, 2)},
                                      {"input_sha256": "0" * 64}, {"role": "wrong"},
                                      {"serialization": "wrong"}])
def test_bad_receipt_no_forward(setup, changes):
    create, model, _ = setup
    obj = create()
    obj._tokenizer.change = lambda receipt: replace(receipt, **changes)
    with pytest.raises(s.SessionRefused):
        obj.embed(["valid"])
    assert not model.calls and obj._closed


def test_renewal_and_guard(setup):
    create, model, factory = setup
    obj = create()
    old = obj._tokenizer
    old._calls = 1024
    obj.embed(["one"])
    assert old.closed and obj._tokenizer is not old and len(factory.calls) == 1
    assert len(model.calls) == 1
    obj._lock.acquire()
    try:
        with pytest.raises(s.SessionRefused, match="busy"):
            obj.embed(["x"])
        with pytest.raises(s.SessionRefused, match="busy"):
            obj.close()
        assert not obj._closed
    finally:
        obj._lock.release()
    obj.close()
    obj.close()
    with pytest.raises(s.SessionRefused):
        obj.embed(["x"])


def test_forward_failure_and_body_cleanup(setup):
    create, model, _ = setup
    obj = create()
    model.nan = True
    with pytest.raises(s.SessionRefused):
        obj.embed(["private canary"])
    assert obj._closed
    model.nan = False
    with pytest.raises(RuntimeError):
        with create() as obj:
            staged = obj._staged.path
            raise RuntimeError("body")
    assert not staged.exists()


def test_all_tokenization_before_forward_and_late_bad_receipt(setup):
    create, model, _ = setup
    obj = create()
    worker = obj._tokenizer
    original = worker.encode
    def encode(text):
        assert not model.calls
        receipt = original(text)
        return replace(receipt, count=0) if text == "second" else receipt
    worker.encode = encode
    with pytest.raises(s.SessionRefused):
        obj.embed(["first", "second"])
    assert worker._calls == 2 and not model.calls


@pytest.mark.parametrize("counter", ["time", "bytes"])
def test_budget_renewal(setup, counter):
    create, _, factory = setup
    obj = create()
    old = obj._tokenizer
    if counter == "time":
        old._deadline = time.monotonic() + 6
    else:
        old._input = old._policy.max_input_bytes
    obj.embed(["valid"])
    assert old.closed and obj._tokenizer is not old and len(factory.calls) == 1
    obj.close()


def test_normalization_failure_is_sanitized_and_closes(setup, monkeypatch):
    create, _, _ = setup
    obj = create()
    staged, worker = obj._staged.path, obj._tokenizer
    import secrets
    secret = secrets.token_hex(16)
    def fail(_):
        raise ValueError(secret)
    monkeypatch.setattr(s.embedding_vectors, "normalize_rows", fail)
    with pytest.raises(s.SessionRefused, match="^embedding session refused$") as exc:
        obj.embed([secret])
    import traceback
    assert secret not in "".join(traceback.format_exception(exc.value))
    assert worker.closed and not staged.exists()


def test_bad_metadata_before_framework(tmp_path, monkeypatch):
    root = tmp_path / "tree"
    _, raw, inv, d, tokenizer = make_tree(root)
    monkeypatch.setattr(s.cpu_embedding_backend, "_framework", lambda: pytest.fail("load reached"))
    with pytest.raises(s.SessionRefused):
        s.CPUEmbeddingSession(raw, root, d, replace(tokenizer, sha256="0" * 64),
                              inv.inventory_id, Runtime(Path("/fake"), Path("/fake")))


def test_partial_construction_closes_stage_and_worker(setup, monkeypatch):
    create, _, factory = setup
    workers = []
    class TrackedWorker(Worker):
        def __init__(self, *args):
            super().__init__(*args)
            workers.append(self)
    monkeypatch.setattr(t, "TokenIDSession", TrackedWorker)
    paths = []
    def fail(*args):
        paths.append(args[1])
        raise ValueError("private detail")
    monkeypatch.setattr(s.cpu_embedding_backend, "CPUEmbeddingBackend", fail)
    with pytest.raises(s.SessionRefused):
        create()
    assert workers[0].closed and not paths[0].exists() and not factory.calls


def test_shape_checked_before_copy(setup):
    create, _, _ = setup
    obj = create()
    assert obj.embed(["ok"])[0][0] == 0.03125
    selection = ["ok"] * 1_000_000
    tracemalloc.start()
    try:
        with pytest.raises(s.SessionRefused):
            obj.embed(selection)
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    assert peak < 200_000


def test_body_exception_preserved_when_cleanup_fails(setup, monkeypatch):
    create, _, _ = setup
    obj = create()
    actual = obj._cleanup
    def fail():
        actual()
        raise ValueError("private cleanup detail")
    monkeypatch.setattr(obj, "_cleanup", fail)
    with pytest.raises(RuntimeError, match="body") as exc:
        with obj:
            raise RuntimeError("body")
    assert exc.value.__notes__ == ["embedding session cleanup failed"]


def test_invalid_runtime_never_loads_framework(tmp_path, monkeypatch):
    root = tmp_path / "tree"
    _, raw, inv, definition, tokenizer = make_tree(root)
    calls = []
    monkeypatch.setattr(s.cpu_embedding_backend, "_framework", lambda: calls.append(True))
    with pytest.raises(s.SessionRefused):
        s.CPUEmbeddingSession(raw, root, definition, tokenizer, inv.inventory_id, object())
    assert not calls


def test_wrong_rows_and_forward_error_close(setup, monkeypatch):
    create, _, _ = setup
    for mode in ("rows", "failure"):
        obj = create()
        worker, staged = obj._tokenizer, obj._staged.path
        def forward(_):
            if mode == "failure":
                raise ValueError("private detail")
            return ((1.0,) * 1024,)
        monkeypatch.setattr(obj._backend, "forward_cls", forward)
        with pytest.raises(s.SessionRefused):
            obj.embed(["one", "two"])
        assert worker.closed and not staged.exists()
