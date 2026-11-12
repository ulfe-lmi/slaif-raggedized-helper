"""Basic refusal and input-boundary tests for the GPU text bridge."""

import pytest

from slaif_raggedized_helper import isolated_gpu_embedding as bridge


def test_invalid_declarations_and_fake_owner_refuse():
    for raw in (b"{}", b'{"schema":1,"schema":1}', b" " * 32769, b"\xff"):
        with pytest.raises(bridge.SessionRefused):
            bridge.validate_record(raw, b"{}")
    with pytest.raises(bridge.SessionRefused):
        bridge.predict(object(), object())
    with pytest.raises(bridge.SessionRefused):
        bridge.GPUTextEmbeddingSession(object(), object())


def test_preflight_rejects_invalid_input_before_native_exposure():
    session = bridge.GPUTextEmbeddingSession.__new__(bridge.GPUTextEmbeddingSession)
    session._max_rows = 128
    assert session._preflight(["hello"])[0] == ("hello",)
    for bad in (
        [],
        [True],
        ["\ud800"],
        ["x" * 100001],
        ["x"] * 129,
        "text",
        ["x" * 100000] * 11,
        ["é" * 40000] * 8,
    ):
        with pytest.raises((ValueError, UnicodeError)):
            session._preflight(bad)


def test_planned_record_is_closed_and_cross_bound(tmp_path, monkeypatch):
    import dataclasses
    import hashlib
    import json
    from pathlib import Path

    from slaif_raggedized_helper import embedding_artifacts, gpu_worker_launch
    from test_gpu_worker_launch import _prepared_fixture
    from test_native_tokenizers import make_native

    paths, runtime, _ = make_native(tmp_path)
    args, reservation = _prepared_fixture(tmp_path, monkeypatch)
    root = Path(args["artifact_root"])
    raw = paths[0].read_bytes()
    (root / "tokenizer.json").write_bytes(raw)
    manifest = json.loads(args["manifest"])
    item = next(x for x in manifest["files"] if x["role"] == "tokenizer")
    item.update(size=len(raw), sha256=hashlib.sha256(raw).hexdigest())
    args["manifest"] = json.dumps(manifest).encode()
    args["inventory_id"] = embedding_artifacts.verify_artifacts(args["manifest"], root).inventory_id
    args["tokenizer"] = dataclasses.replace(args["tokenizer"], sha256=item["sha256"])
    prepared = gpu_worker_launch.prepare(**args)
    try:
        plan = bridge.predict(prepared, runtime)
        assert (
            bridge.validate_record(plan.execution_record, plan.native_runtime_record)
            == plan.execution_fingerprint
        )
        record = json.loads(plan.execution_record)
        for key, value in [
            ("schema", True),
            ("space_id", "0" * 64),
            ("intended_execution_fingerprint", "sha256:" + "0" * 64),
            ("hardware_qualification", "qualified"),
            ("unknown", 1),
        ]:
            bad = dict(record, **{key: value})
            with pytest.raises(bridge.SessionRefused):
                bridge.validate_record(bridge._json(bad), plan.native_runtime_record)
        for key, value in [
            ("role", "other"),
            ("runtime_record_sha256", "0" * 64),
            ("model_revision", "bad"),
        ]:
            bad = dict(record, native=dict(record["native"], **{key: value}))
            with pytest.raises(bridge.SessionRefused):
                bridge.validate_record(bridge._json(bad), plan.native_runtime_record)
        with pytest.raises(bridge.SessionRefused):
            bridge.validate_record(plan.execution_record, plan.native_runtime_record + b" ")
        changed = dict(record, native=dict(record["native"], artifact_sha256="0" * 64))
        assert (
            bridge.validate_record(bridge._json(changed), plan.native_runtime_record)
            != plan.execution_fingerprint
        )
        changed = dict(record, native=dict(record["native"], model_revision="c" * 40))
        # A declaration cannot recover a checkpoint revision from its digest.
        assert (
            bridge.validate_record(bridge._json(changed), plan.native_runtime_record)
            != plan.execution_fingerprint
        )
        changed = dict(record, bridge=dict(record["bridge"], native_tokenizers_py="0" * 64))
        with pytest.raises(bridge.SessionRefused):
            bridge.validate_record(bridge._json(changed), plan.native_runtime_record)
        changed = dict(record, bridge=dict(record["bridge"]))
        changed["bridge"]["native_tokenizers.py"] = "0" * 64
        with pytest.raises(bridge.SessionRefused):
            bridge.validate_record(bridge._json(changed), plan.native_runtime_record)
        with pytest.raises(bridge.SessionRefused):
            bridge.validate_record(b'{"schema":1,"schema":1}', plan.native_runtime_record)
        with pytest.raises(bridge.SessionRefused):
            bridge.validate_record(json.dumps(record).encode(), plan.native_runtime_record)
    finally:
        prepared.close()
        reservation.close()


def test_receipt_validation_rejects_binding_and_shape_changes():
    import dataclasses
    import hashlib
    import json
    from pathlib import Path

    from slaif_raggedized_helper import embedding_tokenizer, native_tokenizers

    session = bridge.GPUTextEmbeddingSession.__new__(bridge.GPUTextEmbeddingSession)
    session._vocab = 20
    session._definition = native_tokenizers.Definition(
        Path("/tmp/unused"), "a" * 64, "0.21.4", "bge_representation", "b" * 40, "identity"
    )
    digest = hashlib.sha256(json.dumps(["hello", None], separators=(",", ":")).encode()).hexdigest()
    receipt = embedding_tokenizer.TokenIDReceipt(
        (1, 3, 2),
        3,
        "a" * 64,
        "0.21.4",
        "bge_representation",
        "b" * 40,
        "identity",
        digest,
        "c" * 32,
    )
    session._receipt(receipt, "hello")
    for field, value in [
        ("ids", (1, True)),
        ("ids", (1, 20)),
        ("ids", (1,)),
        ("ids", (1,) * 1025),
        ("count", 2),
        ("artifact_sha256", "0" * 64),
        ("backend_version", "wrong"),
        ("role", "wrong"),
        ("model_revision", "c" * 40),
        ("preprocessing", "wrong"),
        ("input_sha256", "0" * 64),
        ("nonce", "wrong"),
        ("serialization", "wrong"),
    ]:
        with pytest.raises(ValueError):
            session._receipt(dataclasses.replace(receipt, **{field: value}), "hello")


def test_closed_uninitialized_instance_cannot_be_reinitialized():
    session = bridge.GPUTextEmbeddingSession.__new__(bridge.GPUTextEmbeddingSession)
    session.close()
    session.close()
    with pytest.raises(bridge.SessionRefused):
        session.__init__(object(), object())


def test_raw_binding_cardinality_and_binary32_validation():
    from slaif_raggedized_helper import gpu_embedding_worker, gpu_worker_protocol

    ready = gpu_worker_protocol.encode({"nonce": "x"})
    row = tuple([1.0] * 1024)
    result = gpu_embedding_worker.RawCLSResult((("nonce", "x"),), (row,))
    assert bridge._raw_rows(result, ready, 1) == (row,)
    for bad in (
        gpu_embedding_worker.RawCLSResult((("nonce", "y"),), (row,)),
        gpu_embedding_worker.RawCLSResult((("nonce", "x"), ("nonce", "x")), (row,)),
        gpu_embedding_worker.RawCLSResult((("nonce", "x"),), (row, row)),
        gpu_embedding_worker.RawCLSResult((("nonce", "x"),), ((float("nan"),) * 1024,)),
        gpu_embedding_worker.RawCLSResult((("nonce", "x"),), ((0.1,) * 1024,)),
    ):
        with pytest.raises(ValueError):
            bridge._raw_rows(bad, ready, 1)


def test_closed_session_is_not_kept_alive_by_cleanup_registry():
    import gc
    import weakref

    session = bridge.GPUTextEmbeddingSession.__new__(bridge.GPUTextEmbeddingSession)
    identifier = id(session)
    reference = weakref.ref(session)
    session.close()
    assert identifier not in bridge._owners
    del session
    gc.collect()
    assert reference() is None
