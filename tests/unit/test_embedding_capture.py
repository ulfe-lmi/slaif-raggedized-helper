import pytest

from slaif_raggedized_helper.qualification.embedding_capture import CaptureRefused, _admit


def test_admission_freezes_and_hashes_query():
    ids, queries = _admit(["a"], (("q", "hello", ("a",)),), 1000, 1, 0.1, 0.1)
    assert ids == ("a",)
    assert queries[0][3] == "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"


@pytest.mark.parametrize(
    "queries",
    [
        (("q", "secret", ("missing",)),),
        (("q", "secret", ("a", "a")),),
        (("q", "secret", ()), ("q", "other", ())),
        (("q", "\ud800", ()),),
    ],
)
def test_invalid_queries_are_content_free(queries):
    with pytest.raises(CaptureRefused, match="^capture refused$"):
        _admit(("a",), queries, 1000, 1, 0.1, 0.1)


def test_authorization_forwards_original_boundary_and_enforces_epoch():
    from slaif_raggedized_helper.qualification.embedding_capture import _Epoch

    seen = []

    def provider(data, boundary):
        seen.append((data, boundary))
        return ("a" if len(seen) == 1 else "b") * 64

    epoch = _Epoch(provider, 1000)
    assert epoch(b"original-plan", "before_model") == "a" * 64
    with pytest.raises(CaptureRefused):
        epoch(b"query-identity", "before_query")
    assert seen == [(b"original-plan", "before_model"), (b"query-identity", "before_query")]


def test_plan_comparison_only_excludes_execution_fingerprint():
    from types import SimpleNamespace

    from slaif_raggedized_helper.qualification.embedding_capture import _compare_plans, _wire

    def plan(execution, row):
        return SimpleNamespace(
            plan_bytes=_wire(
                {
                    "dependencies": {"execution_fingerprint": execution, "space_id": "space"},
                    "rows": [row],
                }
            ),
            texts=("text",),
        )

    _compare_plans(plan("cpu", "same"), plan("gpu", "same"))
    with pytest.raises(CaptureRefused):
        _compare_plans(plan("cpu", "first"), plan("gpu", "second"))


def test_query_authorization_identity_contains_digest_not_text():
    import json

    from slaif_raggedized_helper.qualification.embedding_capture import _query_identity

    _, rows = _admit(("a",), (("q", "private query", ("a",)),), 1000, 1, 0, 0)
    data = _query_identity("bundle", ("a",), rows[0])
    assert b"private query" not in data
    assert json.loads(data) == {
        "purpose": "evaluate",
        "bundle_id": "bundle",
        "chunk_ids": ["a"],
        "query_id": "q",
        "query_sha256": rows[0][3],
    }


def test_query_result_rejects_non_query_object_without_echo():
    from slaif_raggedized_helper.qualification.embedding_capture import _query_result

    with pytest.raises(CaptureRefused, match="^capture refused$"):
        _query_result("private payload", None, "space", "execution")


def test_epoch_checks_deadline_before_provider(monkeypatch):
    from slaif_raggedized_helper.qualification.embedding_capture import _Epoch

    times = iter((1.0, 2.0))
    monkeypatch.setattr("time.monotonic", lambda: next(times))
    called = []
    epoch = _Epoch(lambda *args: called.append(args), 1)
    with pytest.raises(CaptureRefused):
        epoch(b"plan", "before_model")
    assert called == []


def test_real_source_loader_rejects_untrusted_stores():
    from slaif_raggedized_helper.qualification.embedding_capture import _Epoch, _source_snapshot

    epoch = _Epoch(lambda *_: "a" * 64, 1000)
    with pytest.raises(CaptureRefused, match="^capture refused$"):
        _source_snapshot(None, None, "0" * 64, epoch)


def test_journal_paths_refuse_aliases_and_nested_paths(tmp_path):
    from slaif_raggedized_helper.qualification.embedding_capture import _journal_paths

    cpu = tmp_path / "cpu"
    gpu = tmp_path / "gpu"
    cpu.mkdir(mode=0o700)
    gpu.mkdir(mode=0o700)
    assert _journal_paths(cpu, gpu) == (str(cpu), str(gpu))
    with pytest.raises(CaptureRefused):
        _journal_paths(cpu, cpu / "nested")
    alias = tmp_path / "alias"
    alias.symlink_to(tmp_path, target_is_directory=True)
    with pytest.raises(CaptureRefused):
        _journal_paths(cpu, alias / "gpu")


def test_plan_builder_reaches_real_cpu_admission_before_gpu_launch():
    from slaif_raggedized_helper import cpu_embedding_plan
    from slaif_raggedized_helper.qualification.embedding_capture import _build_plans, _Epoch

    epoch = _Epoch(lambda *_: "a" * 64, 1000)
    with pytest.raises(cpu_embedding_plan.PlanError, match="CPU embedding plan refused"):
        _build_plans(
            (None,) * 10,
            None,
            None,
            None,
            epoch,
            representation_policy=None,
            batch_policy=None,
            cpu_worker_policy=None,
        )


def test_capture_rejects_bad_gold_before_touching_dependencies():
    from slaif_raggedized_helper.qualification.embedding_capture import capture

    with pytest.raises(CaptureRefused, match="^capture refused$"):
        capture(
            None,
            None,
            "bundle",
            ("a",),
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            (("q", "secret", ("missing",)),),
            None,
            deadline_ms=1000,
            k=1,
            cosine_tolerance=0,
            score_tolerance=0,
        )


def test_authorization_provider_error_is_content_free_and_interrupt_preserved():
    from slaif_raggedized_helper.qualification.embedding_capture import _Epoch

    def error(*_):
        raise ValueError("private input")

    with pytest.raises(CaptureRefused, match="^capture refused$"):
        _Epoch(error, 1000)(b"plan", "before_model")
    interrupt = KeyboardInterrupt()

    def interrupted(*_):
        raise interrupt

    with pytest.raises(KeyboardInterrupt) as caught:
        _Epoch(interrupted, 1000)(b"plan", "before_model")
    assert caught.value is interrupt


def test_analyzer_uses_reloaded_matrix_and_preserves_unqualified_semantics():
    import numpy as np
    from types import SimpleNamespace

    from slaif_raggedized_helper import schema
    from slaif_raggedized_helper.qualification.embedding_capture import _analyze

    definition = schema.EmbeddingDefinition(
        model_name="test", checkpoint_revision="r", pooling="cls", dimensions=1024
    )
    vector = (1.0,) + (0.0,) * 1023
    batch = SimpleNamespace(matrix=np.asarray([vector], dtype="<f4"))
    queries = (("q", "private", ("a",), "a" * 64),)
    rows = [{"chunk_id": "a", "input_sha256": "b" * 64, "representation_id": "c" * 64}]
    result = _analyze(definition, queries, (vector,), rows, batch, batch, 1, 0, 0)
    assert result["evidence"] == "SUPPLIED_UNVERIFIED"
    assert result["qualification"] == "NOT_QUALIFIED"
    assert result["input_fingerprint"]


def test_authorization_rechecks_configuration_after_provider():
    from slaif_raggedized_helper.qualification.embedding_capture import _Epoch

    state = {"changed": False}

    def provider(*_):
        state["changed"] = True
        return "a" * 64

    def guard():
        if state["changed"]:
            raise CaptureRefused("capture refused")

    epoch = _Epoch(provider, 1000)
    epoch.guard = guard
    with pytest.raises(CaptureRefused):
        epoch(b"plan", "before_encode")


def test_producer_interrupt_identity_and_cleanup_owner_are_preserved(monkeypatch):
    from slaif_raggedized_helper import cpu_embedding_producer, gpu_embedding_producer
    from slaif_raggedized_helper.qualification.embedding_capture import _Epoch, _produce_pair

    interrupt = KeyboardInterrupt()
    owner = object()
    interrupt.cleanup_owner = owner
    calls = []

    def interrupted(*_args, **_kwargs):
        calls.append("cpu")
        raise interrupt

    def gpu_unreachable(*_args, **_kwargs):
        calls.append("gpu")
        raise AssertionError("unexpected GPU entry")

    monkeypatch.setattr(cpu_embedding_producer, "produce", interrupted)
    monkeypatch.setattr(gpu_embedding_producer, "produce", gpu_unreachable)
    with pytest.raises(KeyboardInterrupt) as caught:
        _produce_pair(
            (None,) * 10,
            None,
            None,
            None,
            None,
            None,
            None,
            _Epoch(lambda *_: "a" * 64, 1000),
            None,
            None,
            lambda: None,
            representation_policy=None,
            batch_policy=None,
            cpu_worker_policy=None,
        )
    assert caught.value is interrupt and caught.value.cleanup_owner is owner
    assert calls == ["cpu"]


@pytest.mark.parametrize(
    "changed", ["space_id", "tokenizer_sha256", "representation_policy_fingerprint"]
)
def test_plan_comparison_refuses_shared_dependency_mutation(changed):
    from types import SimpleNamespace

    from slaif_raggedized_helper.qualification.embedding_capture import _compare_plans, _wire

    shared = {
        "execution_fingerprint": "cpu",
        "space_id": "space",
        "tokenizer_sha256": "token",
        "representation_policy_fingerprint": "policy",
    }
    different = dict(shared, execution_fingerprint="gpu")
    different[changed] = "different"
    cpu = SimpleNamespace(plan_bytes=_wire({"dependencies": shared, "rows": [1]}), texts=("x",))
    gpu = SimpleNamespace(plan_bytes=_wire({"dependencies": different, "rows": [1]}), texts=("x",))
    with pytest.raises(CaptureRefused, match="^capture refused$"):
        _compare_plans(cpu, gpu)


def test_result_loader_rejects_untrusted_result_before_store_access():
    from slaif_raggedized_helper.qualification.embedding_capture import _load_result

    with pytest.raises(CaptureRefused, match="^capture refused$"):
        _load_result(None, object(), None, gpu=False)
    with pytest.raises(CaptureRefused, match="^capture refused$"):
        _load_result(None, object(), None, gpu=True)


def test_actual_ingestion_store_type_guard_controls_load_boundary(monkeypatch):
    from slaif_raggedized_helper import ingestion_store
    from slaif_raggedized_helper.qualification.embedding_capture import _Epoch, _source_snapshot

    reached = []

    class SentinelStore:
        def load(self, identifier):
            reached.append(identifier)
            raise ValueError("sentinel")

    epoch = _Epoch(lambda *_: "a" * 64, 1000)
    with pytest.raises(CaptureRefused):
        _source_snapshot(None, SentinelStore(), "0" * 64, epoch)
    assert reached == []
    # Control removes only the existing store-type guard. The actual loader then
    # reaches the sentinel store load; it is never replaced by a success result.
    monkeypatch.setattr(ingestion_store, "_stores", lambda *_: None)
    with pytest.raises(CaptureRefused):
        _source_snapshot(None, SentinelStore(), "0" * 64, epoch)
    assert reached == ["0" * 64]


def test_gold_guard_control_reaches_real_journal_boundary(monkeypatch):
    import hashlib
    import sys
    import types
    from pathlib import Path

    from slaif_raggedized_helper.qualification import embedding_capture as actual

    source = Path(actual.__file__).read_text()
    needle = "if len(set(gold)) != len(gold) or not set(gold) <= set(ids):"
    assert source.count(needle) == 1
    control = source.replace(needle, "if len(set(gold)) != len(gold):")
    name = "slaif_raggedized_helper.qualification._capture_gold_control"
    module = types.ModuleType(name)
    module.__package__ = "slaif_raggedized_helper.qualification"
    sys.modules[name] = module
    reached = []
    try:
        exec(compile(control, "<gold guard control>", "exec"), module.__dict__)
        real_paths = actual._journal_paths

        def observe(*args):
            reached.append(args)
            return real_paths(*args)

        monkeypatch.setattr(actual, "_journal_paths", observe)
        monkeypatch.setattr(module, "_journal_paths", observe)
        args = (
            None,
            None,
            "bundle",
            ("a",),
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            "relative",
            "also-relative",
            None,
            (("q", "private", ("missing",)),),
            lambda *_: "a" * 64,
        )
        options = dict(deadline_ms=1000, k=1, cosine_tolerance=0, score_tolerance=0)
        with pytest.raises(actual.CaptureRefused):
            actual.capture(*args, **options)
        assert not reached
        with pytest.raises(actual.CaptureRefused):
            module.capture(*args, **options)
        assert reached == [("relative", "also-relative")]
        print("gold_guard_control_sha256=" + hashlib.sha256(control.encode()).hexdigest())
    finally:
        del sys.modules[name]


def test_gpu_validator_and_plan_fingerprints_are_distinct_domains():
    import hashlib

    from slaif_raggedized_helper import isolated_gpu_embedding

    record = b"example execution record"
    assert isolated_gpu_embedding._digest(record) == (
        "sha256:" + hashlib.sha256(isolated_gpu_embedding.DOMAIN + record).hexdigest()
    )
    assert isolated_gpu_embedding._digest(record) != hashlib.sha256(record).hexdigest()


def test_query_payload_validation_refuses_corrupt_real_result():
    from slaif_raggedized_helper.query_embedding import QueryEmbedding
    from slaif_raggedized_helper.qualification.embedding_capture import _query_result

    result = QueryEmbedding(
        b"private bytes",
        "0" * 64,
        "space",
        "definition",
        "execution",
        b"{}",
        "fingerprint",
        "policy",
    )
    with pytest.raises(CaptureRefused, match="^capture refused$"):
        _query_result(result, None, "space", "execution")


def test_authorization_rechecks_deadline_after_provider(monkeypatch):
    from slaif_raggedized_helper.qualification.embedding_capture import _Epoch

    readings = iter((0.0, 0.0, 2.0))
    monkeypatch.setattr("time.monotonic", lambda: next(readings))
    epoch = _Epoch(lambda *_: "a" * 64, 1000)
    with pytest.raises(CaptureRefused, match="^capture refused$"):
        epoch(b"plan", "before_encode")


@pytest.mark.parametrize(
    "ids, queries, deadline, k, ct, st",
    [
        (tuple(str(x) for x in range(9)), (("q", "x", ()),), 1000, 1, 0, 0),
        (("a", "a"), (("q", "x", ()),), 1000, 1, 0, 0),
        (("a",), tuple((str(x), "x", ()) for x in range(9)), 1000, 1, 0, 0),
        (("a",), (("q", "x", ()),), True, 1, 0, 0),
        (("a",), (("q", "x", ()),), 1000, 0, 0, 0),
        (("a",), (("q", "x", ()),), 1000, 1, float("nan"), 0),
        (("a",), (("q", "x", ()),), 1000, 1, 0, float("inf")),
    ],
)
def test_limits_refuse_before_any_dependency(ids, queries, deadline, k, ct, st):
    with pytest.raises(CaptureRefused, match="^capture refused$"):
        _admit(ids, queries, deadline, k, ct, st)


def test_query_epoch_change_refuses_before_encoder_entry(monkeypatch):
    from slaif_raggedized_helper import query_embedding
    from slaif_raggedized_helper.qualification.embedding_capture import _encode_queries, _Epoch

    entered = []
    monkeypatch.setattr(
        query_embedding.ResidentQueryEncoder, "encode_query", lambda *_: entered.append(True)
    )
    epoch = _Epoch(lambda _, boundary: ("a" if boundary == "before_model" else "b") * 64, 1000)
    epoch(b"actual-plan", "before_model")
    with pytest.raises(CaptureRefused, match="^capture refused$"):
        _encode_queries(
            None,
            (("q", "private", (), "0" * 64),),
            "bundle",
            ("a",),
            None,
            "space",
            "execution",
            epoch,
            lambda: None,
        )
    assert not entered


def test_query_result_refuses_other_semantic_space():
    import hashlib
    from types import SimpleNamespace

    from slaif_raggedized_helper import query_embedding
    from slaif_raggedized_helper.qualification.embedding_capture import _query_result

    payload = b"\x00" * 4096
    actual = query_embedding.QueryEmbedding(
        payload,
        hashlib.sha256(payload).hexdigest(),
        "other-space",
        "definition",
        "execution",
        b"{}",
        "fingerprint",
        query_embedding.POLICY_ID,
    )
    with pytest.raises(CaptureRefused, match="^capture refused$"):
        _query_result(
            actual, SimpleNamespace(fingerprint=lambda: "definition"), "expected-space", "execution"
        )


def test_private_journal_identity_detects_replacement_and_mode_change(tmp_path):
    from slaif_raggedized_helper.qualification.embedding_capture import _journal_identity

    root = tmp_path / "journal"
    root.mkdir(mode=0o700)
    original = _journal_identity(str(root))
    (root / "legitimate-child").mkdir()
    assert _journal_identity(str(root)) == original
    root.rename(tmp_path / "old-journal")
    root.mkdir(mode=0o700)
    assert _journal_identity(str(root)) != original
    root.chmod(0o755)
    with pytest.raises(CaptureRefused):
        _journal_identity(str(root))


def test_journal_preflight_preserves_actual_lstat_interrupt(tmp_path, monkeypatch):
    import os

    from slaif_raggedized_helper.qualification.embedding_capture import _journal_identity

    root = tmp_path / "journal"
    root.mkdir(mode=0o700)
    assert _journal_identity(str(root))
    actual_lstat = os.lstat
    interrupt = KeyboardInterrupt()

    def interrupted(path, *args, **kwargs):
        actual_lstat(path, *args, **kwargs)
        raise interrupt

    monkeypatch.setattr(os, "lstat", interrupted)
    with pytest.raises(KeyboardInterrupt) as caught:
        _journal_identity(str(root))
    assert caught.value is interrupt
