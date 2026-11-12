"""Boundaries and ownership of isolated composition."""

import dataclasses
import os
from pathlib import Path

import pytest

from slaif_raggedized_helper import cpu_embedding_worker as cpu, native_tokenizers
from slaif_raggedized_helper.isolated_cpu_embedding import (
    IsolatedCPUEmbeddingSession,
    SessionRefused,
)
from test_cpu_embedding_backend import make_tree


@pytest.fixture
def args(tmp_path):
    _, raw, inv, definition, token = make_tree(tmp_path / "tree")
    runtime = native_tokenizers.Runtime(Path("/runtime"), Path("/packages"), "python3.12")
    return [raw, tmp_path / "tree", definition, token, inv.inventory_id, runtime, runtime]


def test_constructor_is_preflight_and_mutated_policy_refused(args, monkeypatch):
    monkeypatch.setattr(
        "slaif_raggedized_helper.embedding_staging.stage",
        lambda *a, **k: pytest.fail("unexpected I/O"),
    )
    policy = cpu.Policy()
    object.__setattr__(policy, "max_rows", 129)
    with pytest.raises(SessionRefused):
        IsolatedCPUEmbeddingSession(*args, worker_policy=policy)
    args[5] = dataclasses.replace(args[5], python="python3.14")
    with pytest.raises(SessionRefused):
        IsolatedCPUEmbeddingSession(*args)


def test_input_bounds_and_busy_postclose(args):
    obj = IsolatedCPUEmbeddingSession(*args)
    assert obj._preflight(["hello"])
    for bad in ([], ["x"] * 9, ["x" * 100001], [object()], "hello"):
        with pytest.raises(ValueError):
            obj._preflight(bad)
    obj._lock.acquire()
    try:
        with pytest.raises(SessionRefused, match="busy"):
            obj.close()
    finally:
        obj._lock.release()
    obj.close()
    obj.close()
    with pytest.raises(SessionRefused):
        obj.encode(["hello"])
    obj._pid = os.getpid() + 1
    with pytest.raises(SessionRefused):
        obj.close()


def test_stage_cleanup_failure_never_reuses_generator(args):
    obj = IsolatedCPUEmbeddingSession(*args)

    class Stage:
        calls = 0

        def __exit__(self, *args):
            self.calls += 1
            raise ValueError("private path")

    stage = Stage()
    obj._stage = stage
    with pytest.raises(SessionRefused) as caught:
        obj.close()
    assert caught.value.owner is obj and caught.value.pending
    with pytest.raises(SessionRefused):
        obj.close()
    assert stage.calls == 1


def test_body_exception_kept_when_cleanup_fails(args):
    obj = IsolatedCPUEmbeddingSession(*args)

    class Stage:
        def __exit__(self, *args):
            raise KeyboardInterrupt()

    obj._stage = Stage()
    body = RuntimeError("body")
    assert obj.__exit__(RuntimeError, body, None) is False
    assert body.cleanup_owner is obj and body.__notes__ == ["embedding session cleanup pending"]


def test_late_bad_receipt_prevents_forward_and_closes(args, monkeypatch):
    from slaif_raggedized_helper import embedding_tokenizer as tokenizer

    obj = IsolatedCPUEmbeddingSession(*args)
    obj._state = "open"
    obj._token_definition = args[3]
    calls = []

    class Native:
        _policy = tokenizer.Policy()

        def encode(self, text):
            import hashlib
            import json

            digest = hashlib.sha256(
                json.dumps([text, None], ensure_ascii=True, separators=(",", ":")).encode()
            ).hexdigest()
            if text == "second":
                digest = "0" * 64
            d = obj._token_definition
            return tokenizer.TokenIDReceipt(
                (1, 2),
                2,
                d.sha256,
                d.backend_version,
                d.role,
                d.model_revision,
                d.preprocessing,
                digest,
                "a" * 32,
            )

        def close(self):
            calls.append("native-close")

    class Worker:
        vocab_size = 20
        _child = None

        def forward_cls(self, rows):
            calls.append("forward")

        def close(self):
            calls.append("worker-close")

    obj._tokenizer, obj._worker = Native(), Worker()
    obj._token_definition = args[3]
    obj._tokenizer._definition = obj._token_definition
    obj._native_policy_snapshot = dataclasses.astuple(obj._tokenizer._policy)
    monkeypatch.setattr(obj, "_renew", lambda sizes: None)
    with pytest.raises(SessionRefused) as caught:
        obj.encode(["first", "second"])
    assert "first" not in str(caught.value) and calls == ["native-close", "worker-close"]
    with pytest.raises(SessionRefused):
        obj.encode(["first"])


@pytest.mark.parametrize("failure", ["nonfinite", "shape", "zero", "forward"])
def test_no_partial_output_or_retry_on_forward_or_normalization_refusal(args, monkeypatch, failure):
    import hashlib
    import json
    from types import SimpleNamespace
    from slaif_raggedized_helper import embedding_tokenizer as tokenizer
    from slaif_raggedized_helper import isolated_cpu_embedding as session

    bridge = {"test.py": "a" * 64}
    monkeypatch.setattr(session, "_bridge", lambda: bridge)
    monkeypatch.setattr(session.native_tokenizers, "_read_artifact", lambda path, limit: b"code")
    calls = []

    def ready(fault):
        obj = IsolatedCPUEmbeddingSession(*args)
        obj._state = "open"
        obj._token_definition = args[3]

        class Native:
            _policy = tokenizer.Policy()
            _definition = args[3]

            def encode(self, text):
                d = self._definition
                digest = hashlib.sha256(
                    json.dumps([text, None], ensure_ascii=True, separators=(",", ":")).encode()
                ).hexdigest()
                return tokenizer.TokenIDReceipt(
                    (1, 2),
                    2,
                    d.sha256,
                    d.backend_version,
                    d.role,
                    d.model_revision,
                    d.preprocessing,
                    digest,
                    "a" * 32,
                )

            def close(self):
                pass

        class Worker:
            vocab_size = 20
            _child = None
            policy = obj._policy
            profile, code_fingerprint = "a" * 64, "b" * 64
            policy_fingerprint = cpu._policy_identity(policy)
            space = SimpleNamespace(space_id="c" * 64, definition_fingerprint=args[2].fingerprint())

            def forward_cls(self, rows):
                calls.append("forward")
                if fault == "forward":
                    raise ValueError("private")
                if fault == "shape":
                    return ((1.0,),)
                if fault == "nonfinite":
                    return ((float("nan"),) * 1024,)
                if fault == "zero":
                    return ((0.0,) * 1024,)
                return ((1.0,) + (0.0,) * 1023,)

            def close(self):
                calls.append("close")

        obj._tokenizer, obj._worker = Native(), Worker()
        obj.space = obj._worker.space
        obj._identity = obj._worker_identity()
        obj._native_policy_snapshot = session._native_values(obj._tokenizer._policy)
        record = {
            "bridge": bridge,
            "native": {"worker_sha256": hashlib.sha256(b"code").hexdigest()},
        }
        obj.execution_record = session._json(record)
        obj._record_snapshot = obj.execution_record
        obj.execution_fingerprint = session.fingerprint(
            {"kind": "isolated-cpu-embedding-execution-v1", **record}
        )
        obj._fingerprint_snapshot = obj.execution_fingerprint
        monkeypatch.setattr(obj, "_renew", lambda sizes: None)
        return obj

    valid = ready(None)
    result = valid.encode(["secret"])
    assert result.vectors.rows[0][0] == 1.0 and calls == ["forward"]
    valid.close()
    calls.clear()
    invalid = ready(failure)
    with pytest.raises(SessionRefused):
        invalid.encode(["secret"])
    assert calls == ["forward", "close"]


def test_real_stage_substitution_retains_foreign_sentinel(args, tmp_path):
    from slaif_raggedized_helper import embedding_staging

    parent = tmp_path / "private"
    parent.mkdir(mode=0o700)
    stage = embedding_staging.stage(*args[:5], parent=parent)
    staged = stage.__enter__()
    original = staged.path.with_name(staged.path.name + "-owned")
    os.rename(staged.path, original)
    staged.path.mkdir(mode=0o700)
    sentinel = staged.path / "foreign"
    sentinel.write_text("untouched")
    obj = IsolatedCPUEmbeddingSession(*args)
    obj._stage = stage
    try:
        with pytest.raises(SessionRefused) as caught:
            obj.close()
        assert caught.value.owner is obj and sentinel.read_text() == "untouched"
        with pytest.raises(SessionRefused):
            obj.close()
        assert sentinel.read_text() == "untouched"
    finally:
        sentinel.unlink()
        staged.path.rmdir()
        original.rmdir()


def test_mutated_policy_refused_before_tokenizer(args, monkeypatch):
    obj = IsolatedCPUEmbeddingSession(*args)
    obj._state = "open"
    from slaif_raggedized_helper import embedding_tokenizer

    class Native:
        _policy = embedding_tokenizer.Policy()

        def close(self):
            pass

    obj._tokenizer = Native()
    obj._native_policy_snapshot = dataclasses.astuple(obj._tokenizer._policy)
    object.__setattr__(obj._policy, "max_rows", 7)
    monkeypatch.setattr(obj, "_preflight", lambda _: pytest.fail("preflight must not run"))
    with pytest.raises(SessionRefused):
        obj.encode(["secret"])


@pytest.mark.parametrize(
    "field,value",
    [
        ("ids", (1, 20)),
        ("ids", (1, True)),
        ("count", 3),
        ("artifact_sha256", "0" * 64),
        ("backend_version", "wrong"),
        ("role", "wrong"),
        ("model_revision", "0" * 40),
        ("preprocessing", "wrong"),
        ("input_sha256", "0" * 64),
        ("nonce", "bad"),
        ("serialization", "wrong"),
    ],
)
def test_receipt_identity_validation_has_positive_control(args, field, value):
    import hashlib
    import json
    from slaif_raggedized_helper import embedding_tokenizer

    obj = IsolatedCPUEmbeddingSession(*args)
    obj._token_definition = args[3]

    class Worker:
        vocab_size = 20

    obj._worker = Worker()
    token = args[3]
    digest = hashlib.sha256(
        json.dumps(["hello", None], ensure_ascii=True, separators=(",", ":")).encode()
    ).hexdigest()
    receipt = embedding_tokenizer.TokenIDReceipt(
        (1, 2),
        2,
        token.sha256,
        token.backend_version,
        token.role,
        token.model_revision,
        token.preprocessing,
        digest,
        "a" * 32,
    )
    obj._receipt(receipt, "hello")
    with pytest.raises(ValueError):
        obj._receipt(dataclasses.replace(receipt, **{field: value}), "hello")


def test_excess_batch_refused_before_native_or_cpu(args):
    from slaif_raggedized_helper import embedding_tokenizer

    obj = IsolatedCPUEmbeddingSession(*args)
    obj._state = "open"
    calls = []

    class Native:
        _policy = embedding_tokenizer.Policy()

        def encode(self, text):
            calls.append("encode")

        def close(self):
            calls.append("native-close")

    class Worker:
        _child = None

        def forward_cls(self, rows):
            calls.append("forward")

        def close(self):
            calls.append("worker-close")

    obj._tokenizer, obj._worker = Native(), Worker()
    obj._token_definition = args[3]
    obj._tokenizer._definition = obj._token_definition
    obj._native_policy_snapshot = dataclasses.astuple(obj._tokenizer._policy)
    with pytest.raises(SessionRefused):
        obj.encode(["secret"] * 9)
    assert calls == ["native-close", "worker-close"]


def test_invalid_input_admission_does_not_claim_pending_cleanup(args, monkeypatch):
    from slaif_raggedized_helper import embedding_staging

    obj = IsolatedCPUEmbeddingSession(*args)

    class InvalidStage:
        def __enter__(self):
            raise embedding_staging.StagingRefused("invalid")

    monkeypatch.setattr(embedding_staging, "stage", lambda *a, **k: InvalidStage())
    with pytest.raises(SessionRefused) as caught:
        obj.__enter__()
    assert not caught.value.pending


def test_oversized_path_rejected_without_copy_or_filesystem_access(args, monkeypatch):
    import tracemalloc
    from slaif_raggedized_helper import embedding_staging

    positive = IsolatedCPUEmbeddingSession(*args)
    assert positive._state == "new"
    huge_path = Path("/" + "x" * 1_000_000)
    bad = list(args)
    bad[1] = huge_path
    monkeypatch.setattr(embedding_staging, "stage", lambda *a, **k: pytest.fail("unexpected I/O"))
    tracemalloc.start()
    try:
        with pytest.raises(SessionRefused):
            IsolatedCPUEmbeddingSession(*bad)
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    assert peak < 100_000


def test_mutated_policy_rejected_before_copy_hook(args):
    import tracemalloc

    class NoDeepCopy(list):
        def __deepcopy__(self, memo):
            pytest.fail("caller deepcopy hook executed")

    assert IsolatedCPUEmbeddingSession(*args, worker_policy=cpu.Policy())._state == "new"
    payload = NoDeepCopy([0] * 100_000)
    policy = cpu.Policy()
    object.__setattr__(policy, "max_rows", payload)
    tracemalloc.start()
    try:
        with pytest.raises(SessionRefused):
            IsolatedCPUEmbeddingSession(*args, worker_policy=policy)
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    assert peak < 100_000


def test_mutated_definition_refused_before_entry_or_serialization(args, monkeypatch):
    import tracemalloc
    from slaif_raggedized_helper import embedding_staging

    calls = []

    class StopStage:
        def __enter__(self):
            calls.append("stage-entry")
            raise embedding_staging.StagingRefused("test")

    def stage(*a, **k):
        calls.append("stage-created")
        return StopStage()

    monkeypatch.setattr(embedding_staging, "stage", stage)
    positive = IsolatedCPUEmbeddingSession(*args)
    with pytest.raises(SessionRefused):
        positive.__enter__()
    assert calls == ["stage-created", "stage-entry"]
    calls.clear()
    obj = IsolatedCPUEmbeddingSession(*args)
    oversized = "x" * 1_000_000
    object.__setattr__(obj.definition, "dimensions", oversized)
    tracemalloc.start()
    try:
        with pytest.raises(SessionRefused):
            obj.__enter__()
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    assert peak < 100_000 and calls == []


@pytest.mark.parametrize("runtime_name", ["_native_runtime", "_cpu_runtime"])
def test_mutated_runtime_refused_before_renew_or_dispatch(args, monkeypatch, runtime_name):
    from slaif_raggedized_helper import embedding_tokenizer

    args[6] = dataclasses.replace(args[6])
    events = []

    def make_session():
        obj = IsolatedCPUEmbeddingSession(*args)
        obj._state = "open"
        obj._token_definition = args[3]

        class Native:
            _policy = embedding_tokenizer.Policy()
            _definition = args[3]

            def encode(self, text):
                events.append("native-dispatch")
                raise ValueError("stop before forward")

            def close(self):
                pass

        class Worker:
            _child = None

            def forward_cls(self, rows):
                events.append("forward")

            def close(self):
                pass

        obj._tokenizer, obj._worker = Native(), Worker()
        obj._native_policy_snapshot = dataclasses.astuple(obj._tokenizer._policy)
        monkeypatch.setattr(obj, "_renew", lambda sizes: events.append("native-renew"))
        return obj

    positive = make_session()
    with pytest.raises(SessionRefused):
        positive.encode(["hello"])
    assert events == ["native-renew", "native-dispatch"]
    events.clear()
    obj = make_session()
    object.__setattr__(getattr(obj, runtime_name), "packages", Path("/changed"))
    with pytest.raises(SessionRefused):
        obj.encode(["hello"])
    assert events == []
