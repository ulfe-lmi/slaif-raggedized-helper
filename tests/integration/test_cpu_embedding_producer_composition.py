"""Actual source, native tokenizer, journal, typed store and fake CPU protocol."""

import hashlib
import json
import os
from dataclasses import replace
from pathlib import Path

import pytest

from slaif_raggedized_helper import cpu_embedding_producer as producer
from slaif_raggedized_helper import cpu_embedding_worker as cpu
from slaif_raggedized_helper import derived_store, embedding_artifacts, native_tokenizers as nt
from test_cpu_embedding_backend import make_tree
from test_cpu_embedding_worker_composition import FAKE
from test_native_tokenizers import make_native
from test_retrieval_representation_composition import make_bundle
from test_structured_text_composition import create_store


@pytest.fixture
def fixture(tmp_path, monkeypatch):
    tmp_path.chmod(0o700)
    paths, runtime, _ = make_native(tmp_path)
    root = tmp_path / "model"
    manifest, _, _, definition, token = make_tree(root)
    data = paths[0].read_bytes()
    (root / "tokenizer.json").write_bytes(data)
    entry = next(x for x in manifest["files"] if x["role"] == "tokenizer")
    entry.update(size=len(data), sha256=hashlib.sha256(data).hexdigest())
    raw = json.dumps(manifest).encode()
    inv = embedding_artifacts.verify_artifacts(raw, root)
    token = replace(token, sha256=entry["sha256"])
    definitions = (
        replace(token, role="bge_body"),
        token,
        nt.Definition(
            paths[1],
            hashlib.sha256(paths[1].read_bytes()).hexdigest(),
            "0.21.4",
            "reranker_pair",
            inv.model_revision,
            "identity",
        ),
    )
    source, revisions = create_store(tmp_path, "# Heading\n\n" + "hello world. " * 650 + "\n")
    metadata, members, _, chunks = make_bundle(source, revisions[0], definitions, runtime)
    ids = [c.chunk_id for c in chunks.chunks[:2]]
    cpu_runtime = nt.Runtime(
        Path(os.environ["SLAIF_CPU_V2_TEST_ROOT"]),
        Path(os.environ["SLAIF_CPU_V2_TEST_PACKAGES"]),
        "python3.12",
    )
    policy = cpu.Policy(address_bytes=1024**3, cpu_seconds=30, lifetime_seconds=120)
    script = tmp_path / "fake.py"
    script.write_text(FAKE)
    original = cpu._argv
    starts = []

    def intercept(*args):
        starts.append(1)
        result = original(*args)
        result[result.index("/worker.py") - 1] = str(script)
        return result

    monkeypatch.setattr(cpu, "_argv", intercept)
    with derived_store.Store(tmp_path) as store:
        args = (
            source,
            metadata,
            members,
            ids,
            raw,
            root,
            definition,
            token,
            inv.inventory_id,
            runtime,
            cpu_runtime,
            store,
            tmp_path,
        )
        yield args, policy, starts
    source.close()


def test_fresh_and_reuse(fixture):
    args, policy, starts = fixture
    boundaries = []

    def allow(data, boundary):
        assert isinstance(data, bytes)
        boundaries.append(boundary)
        return "a" * 64

    first = producer.produce(*args, allow, worker_policy=policy)
    assert not first.reused and len(first.batch.row_ids) == 2
    assert boundaries == ["before_model", "before_encode", "before_publish", "before_complete"]
    assert len(starts) == 1
    second = producer.produce(*args, allow, worker_policy=policy)
    assert second.reused and second.output_ref == first.output_ref
    assert second.metadata == first.metadata and len(starts) == 1
    assert boundaries[-2:] == ["before_model", "before_reuse"]


def _state(args, policy):
    from slaif_raggedized_helper import cpu_embedding_plan, embedding_job_journal

    prepared = cpu_embedding_plan.build(*args[:11], worker_policy=policy)
    with embedding_job_journal.Journal(args[12]).own(prepared.plan_bytes) as handle:
        return handle.read()[0]["events"][-1]["state"]["status"]


@pytest.mark.parametrize(
    "boundary,status,starts_count",
    [
        ("before_model", None, 0),
        ("before_encode", "FAILED", 1),
        ("before_publish", "UNKNOWN_COMPLETION", 1),
        ("before_complete", "UNKNOWN_COMPLETION", 1),
    ],
)
def test_revocation_at_boundary(fixture, boundary, status, starts_count):
    args, policy, starts = fixture
    calls = []

    def policy_provider(data, name):
        calls.append(name)
        return "b" * 64 if name == boundary else "a" * 64

    # Initial refusal must be an invalid decision; later changes are epoch mismatches.
    def checked(data, name):
        value = policy_provider(data, name)
        return None if name == "before_model" and name == boundary else value

    with pytest.raises(producer.ProducerRefused):
        producer.produce(*args, checked, worker_policy=policy)
    assert boundary in calls and len(starts) == starts_count
    if status is not None:
        assert _state(args, policy) == status
        with pytest.raises(producer.ProducerRefused):
            producer.produce(*args, lambda *_: "a" * 64, worker_policy=policy)
        assert len(starts) == starts_count


def test_observed_mismatch_before_dispatch(fixture, monkeypatch):
    args, policy, starts = fixture
    cls = producer.isolated.IsolatedCPUEmbeddingSession
    original = cls.__enter__
    dispatches = []

    def enter(self):
        result = original(self)
        self.execution_record = b"wrong"
        return result

    monkeypatch.setattr(cls, "__enter__", enter)
    monkeypatch.setattr(cls, "encode", lambda *a: dispatches.append(1))
    with pytest.raises(producer.ProducerRefused):
        producer.produce(*args, lambda *_: "a" * 64, worker_policy=policy)
    assert len(starts) == 1 and dispatches == []
    assert _state(args, policy) == "FAILED"


def test_receipt_mismatch_after_dispatch(fixture, monkeypatch):
    args, policy, starts = fixture
    cls = producer.isolated.IsolatedCPUEmbeddingSession
    original = cls.encode
    calls = []

    def encode(self, texts):
        calls.append(1)
        result = original(self, texts)
        altered = replace(result.receipts[0], count=result.receipts[0].count + 1)
        return replace(result, receipts=(altered, *result.receipts[1:]))

    monkeypatch.setattr(cls, "encode", encode)
    with pytest.raises(producer.ProducerRefused):
        producer.produce(*args, lambda *_: "a" * 64, worker_policy=policy)
    assert len(starts) == len(calls) == 1
    assert _state(args, policy) == "UNKNOWN_COMPLETION"


def test_reuse_refuses_corrupt_output(fixture):
    args, policy, starts = fixture
    result = producer.produce(*args, lambda *_: "a" * 64, worker_policy=policy)
    metadata = json.loads(result.metadata)
    path = args[12] / "derived" / "v1" / "objects" / metadata["vector_container_sha256"]
    path.write_bytes(b"corrupt")
    with pytest.raises(producer.ProducerRefused):
        producer.produce(*args, lambda *_: "a" * 64, worker_policy=policy)
    assert len(starts) == 1
    assert _state(args, policy) == "COMPLETE"


def test_competing_owner_refuses_before_startup(fixture):
    from slaif_raggedized_helper import cpu_embedding_plan, embedding_job_journal

    args, policy, starts = fixture
    prepared = cpu_embedding_plan.build(*args[:11], worker_policy=policy)
    with embedding_job_journal.Journal(args[12]).own(prepared.plan_bytes):
        with pytest.raises(producer.ProducerRefused):
            producer.produce(*args, lambda *_: "a" * 64, worker_policy=policy)
    assert starts == []


@pytest.mark.parametrize("after_commit", [False, True])
def test_complete_commit_failure_is_never_overwritten(fixture, monkeypatch, after_commit):
    from slaif_raggedized_helper import embedding_job_journal

    args, policy, starts = fixture
    original = embedding_job_journal._Owned.append
    attempts = []

    def append(self, state, *other, **kwargs):
        if json.loads(state)["status"] == "COMPLETE":
            attempts.append(1)
            if after_commit:
                original(self, state, *other, **kwargs)
            raise OSError("simulated failure")
        return original(self, state, *other, **kwargs)

    monkeypatch.setattr(embedding_job_journal._Owned, "append", append)
    with pytest.raises(producer.ProducerRefused):
        producer.produce(*args, lambda *_: "a" * 64, worker_policy=policy)
    assert len(starts) == len(attempts) == 1
    assert _state(args, policy) == ("COMPLETE" if after_commit else "UNKNOWN_COMPLETION")
    monkeypatch.setattr(embedding_job_journal._Owned, "append", original)
    if after_commit:
        assert producer.produce(*args, lambda *_: "a" * 64, worker_policy=policy).reused
    else:
        with pytest.raises(producer.ProducerRefused):
            producer.produce(*args, lambda *_: "a" * 64, worker_policy=policy)
    assert len(starts) == 1


def test_interrupt_keeps_pending_cleanup_and_lease(fixture, monkeypatch):
    from slaif_raggedized_helper import cpu_embedding_plan, embedding_job_journal

    args, policy, starts = fixture
    cls = producer.isolated.IsolatedCPUEmbeddingSession
    original_encode, original_close = cls.encode, cls.close
    calls = []

    def encode(self, texts):
        original_encode(self, texts)
        raise KeyboardInterrupt()

    def close(self):
        calls.append(1)
        if len(calls) == 1:
            raise producer.isolated.SessionRefused(owner=self)
        return original_close(self)

    monkeypatch.setattr(cls, "encode", encode)
    monkeypatch.setattr(cls, "close", close)
    with pytest.raises(KeyboardInterrupt) as caught:
        producer.produce(*args, lambda *_: "a" * 64, worker_policy=policy)
    assert len(starts) == 1 and len(calls) == 1
    owner = caught.value.cleanup_owner
    prepared = cpu_embedding_plan.build(*args[:11], worker_policy=policy)
    with pytest.raises(embedding_job_journal.JournalError):
        with embedding_job_journal.Journal(args[12]).own(prepared.plan_bytes):
            pass
    owner.close()
    assert _state(args, policy) == "UNKNOWN_COMPLETION"


@pytest.mark.parametrize("boundary", ["dispatch", "publish"])
def test_changed_source_never_publishes(fixture, monkeypatch, boundary):
    args, policy, starts = fixture
    cls = producer.isolated.IsolatedCPUEmbeddingSession
    original_enter, original_encode = cls.__enter__, cls.encode
    dispatches = []
    publishes = []
    original_publish = producer.batch.publish

    def change():
        (args[5] / "tokenizer.json").write_bytes(b"changed")

    def enter(self):
        result = original_enter(self)
        if boundary == "dispatch":
            change()
        return result

    def encode(self, texts):
        dispatches.append(1)
        return original_encode(self, texts)

    def publish(*values):
        publishes.append(1)
        return original_publish(*values)

    def allow(data, name):
        if boundary == "publish" and name == "before_encode":
            change()
        return "a" * 64

    monkeypatch.setattr(cls, "__enter__", enter)
    monkeypatch.setattr(cls, "encode", encode)
    monkeypatch.setattr(producer.batch, "publish", publish)
    with pytest.raises(producer.ProducerRefused):
        producer.produce(*args, allow, worker_policy=policy)
    assert len(starts) == 1 and len(dispatches) == (boundary == "publish")
    assert publishes == []


def test_reuse_revocation_does_not_release(fixture):
    args, policy, starts = fixture
    producer.produce(*args, lambda *_: "a" * 64, worker_policy=policy)
    calls = []

    def allow(data, boundary):
        calls.append(boundary)
        return "b" * 64 if boundary == "before_reuse" else "a" * 64

    with pytest.raises(producer.ProducerRefused):
        producer.produce(*args, allow, worker_policy=policy)
    assert calls == ["before_model", "before_reuse"] and len(starts) == 1
    assert _state(args, policy) == "COMPLETE"


def test_bad_normalization_has_no_publication(fixture, monkeypatch):
    args, policy, starts = fixture
    cls = producer.isolated.IsolatedCPUEmbeddingSession
    original = cls.encode
    calls, publishes = [], []

    def encode(self, texts):
        calls.append(1)
        result = original(self, texts)
        return replace(result, vectors=replace(result.vectors, policy_id="foreign"))

    monkeypatch.setattr(cls, "encode", encode)
    monkeypatch.setattr(producer.batch, "publish", lambda *a: publishes.append(1))
    with pytest.raises(producer.ProducerRefused):
        producer.produce(*args, lambda *_: "a" * 64, worker_policy=policy)
    assert len(starts) == len(calls) == 1 and publishes == []
    assert _state(args, policy) == "UNKNOWN_COMPLETION"


def test_forward_timeout_records_unknown(fixture):
    args, policy, starts = fixture
    policy = replace(policy, forward_seconds=1)
    script = args[12] / "fake.py"
    script.write_text(
        FAKE.replace(
            "        ids = kw['input_ids'].data",
            "        import time; time.sleep(10)\n        ids = kw['input_ids'].data",
        )
    )
    calls = []

    def allow(data, boundary):
        calls.append(boundary)
        return "a" * 64

    with pytest.raises(producer.ProducerRefused) as failure:
        producer.produce(*args, allow, worker_policy=policy)
    if failure.value.pending:
        failure.value.owner.close()
    assert len(starts) == 1 and "before_encode" in calls and "before_publish" not in calls
    assert _state(args, policy) == "UNKNOWN_COMPLETION"


@pytest.mark.parametrize("published", [False, True])
def test_publish_failure_never_marks_complete(fixture, monkeypatch, published):
    args, policy, starts = fixture
    original = producer.batch.publish
    calls, ids = [], []

    def fail(*values):
        calls.append(1)
        if published:
            ids.append(original(*values))
        raise OSError("simulated publish interruption")

    monkeypatch.setattr(producer.batch, "publish", fail)
    with pytest.raises(producer.ProducerRefused):
        producer.produce(*args, lambda *_: "a" * 64, worker_policy=policy)
    assert len(starts) == len(calls) == 1 and len(ids) == int(published)
    if published:
        assert args[11].load(ids[0])
    assert _state(args, policy) == "UNKNOWN_COMPLETION"


def test_duplicate_receipt_refused(fixture, monkeypatch):
    args, policy, starts = fixture
    cls = producer.isolated.IsolatedCPUEmbeddingSession
    original = cls.encode
    calls, publishes = [], []

    def encode(self, texts):
        calls.append(1)
        result = original(self, texts)
        # Even identical text must not admit a duplicate foreign native receipt.
        return replace(result, receipts=(result.receipts[0], result.receipts[0]))

    monkeypatch.setattr(cls, "encode", encode)
    monkeypatch.setattr(producer.batch, "publish", lambda *a: publishes.append(1))
    with pytest.raises(producer.ProducerRefused):
        producer.produce(*args, lambda *_: "a" * 64, worker_policy=policy)
    assert len(starts) == len(calls) == 1 and publishes == []
    assert _state(args, policy) == "UNKNOWN_COMPLETION"


def test_interrupt_during_final_lease_cleanup_retains_owner(fixture, monkeypatch):
    from slaif_raggedized_helper import embedding_job_journal

    args, policy, starts = fixture
    original = embedding_job_journal._Owned.__exit__
    calls = []

    def interrupt_once(self, *values):
        calls.append(1)
        if len(calls) == 1:
            raise KeyboardInterrupt()
        return original(self, *values)

    monkeypatch.setattr(embedding_job_journal._Owned, "__exit__", interrupt_once)
    owner = None
    try:
        with pytest.raises(KeyboardInterrupt) as caught:
            producer.produce(*args, lambda *_: "a" * 64, worker_policy=policy)
        owner = caught.value.cleanup_owner
        assert len(starts) == len(calls) == 1
    finally:
        if owner is not None:
            owner.close()
    assert len(calls) == 2
    assert _state(args, policy) == "COMPLETE"
    assert producer.produce(*args, lambda *_: "a" * 64, worker_policy=policy).reused
    assert len(starts) == 1


@pytest.mark.parametrize("operation_interrupt", [False, True])
@pytest.mark.parametrize("cleanup_interrupt", [False, True])
def test_operation_and_journal_cleanup_priority(
    fixture, monkeypatch, operation_interrupt, cleanup_interrupt
):
    from slaif_raggedized_helper import embedding_job_journal

    args, policy, starts = fixture
    operation = KeyboardInterrupt("operation") if operation_interrupt else ValueError("private")
    cleanup = KeyboardInterrupt("cleanup") if cleanup_interrupt else OSError("private")
    original = embedding_job_journal._Owned.__exit__
    calls = []

    def authorization(_plan, boundary):
        if boundary == "before_encode":
            raise operation
        return "a" * 64

    def close(handle, *values):
        calls.append(1)
        original(handle, *values)
        raise cleanup

    monkeypatch.setattr(embedding_job_journal._Owned, "__exit__", close)
    owner = None
    try:
        with pytest.raises(BaseException) as caught:
            producer.produce(*args, authorization, worker_policy=policy)
        expected = operation if operation_interrupt else cleanup if cleanup_interrupt else None
        if expected is None:
            assert type(caught.value) is producer.ProducerRefused
            assert str(caught.value) == "CPU producer refused"
        else:
            assert caught.value is expected
        owner = getattr(caught.value, "cleanup_owner", None) or caught.value.owner
        assert owner is not None and len(starts) == len(calls) == 1
    finally:
        monkeypatch.setattr(embedding_job_journal._Owned, "__exit__", original)
        if owner is not None:
            owner.close()
    assert _state(args, policy) == "FAILED"


def test_pre_return_ownership_unknown_is_not_session(fixture, monkeypatch):
    import os
    from slaif_raggedized_helper import embedding_job_ownership as ownership

    args, policy, starts = fixture
    original_claim, original_close = ownership.claim, os.close
    held, attempts = [], []

    def claim(*values):
        with monkeypatch.context() as patch:

            def fail_token(_):
                raise OSError("private acquisition")

            def fail_first(fd):
                attempts.append(fd)
                if not held:
                    held.append(fd)  # failure before actual close
                    raise OSError("private cleanup")
                original_close(fd)

            patch.setattr(ownership.secrets, "token_hex", fail_token)
            patch.setattr(os, "close", fail_first)
            return original_claim(*values)

    monkeypatch.setattr(ownership, "claim", claim)
    try:
        with pytest.raises(producer.ProducerRefused) as caught:
            producer.produce(*args, lambda *_: "a" * 64, worker_policy=policy)
        owner = caught.value.owner
        assert caught.value.pending and owner is not None
        assert owner.session is None and owner.uncertainty and not starts
        assert len(attempts) == 3
        with pytest.raises(producer.ProducerRefused) as repeated:
            owner.close()
        assert repeated.value.owner is owner and len(attempts) == 3
    finally:
        for fd in held:
            original_close(fd)


@pytest.mark.parametrize("operation_interrupt", [False, True])
def test_session_cleanup_interrupt_retains_lease(fixture, monkeypatch, operation_interrupt):
    from slaif_raggedized_helper import cpu_embedding_plan, embedding_job_journal

    args, policy, starts = fixture
    operation = KeyboardInterrupt("operation") if operation_interrupt else ValueError("private")
    cleanup = KeyboardInterrupt("cleanup")
    cls = producer.isolated.IsolatedCPUEmbeddingSession
    original = cls.close
    calls = []

    def authorization(_plan, boundary):
        if boundary == "before_encode":
            raise operation
        return "a" * 64

    def close(session):
        calls.append(1)
        raise cleanup

    monkeypatch.setattr(cls, "close", close)
    owner = None
    try:
        with pytest.raises(KeyboardInterrupt) as caught:
            producer.produce(*args, authorization, worker_policy=policy)
        assert caught.value is (operation if operation_interrupt else cleanup)
        owner = caught.value.cleanup_owner
        assert len(starts) == len(calls) == 1
        prepared = cpu_embedding_plan.build(*args[:11], worker_policy=policy)
        with pytest.raises(embedding_job_journal.JournalError):
            with embedding_job_journal.Journal(args[12]).own(prepared.plan_bytes):
                pass
    finally:
        monkeypatch.setattr(cls, "close", original)
        if owner is not None:
            owner.close()
    assert _state(args, policy) == "FAILED"


def test_journal_pending_owner_is_not_a_worker_session(fixture, monkeypatch):
    from slaif_raggedized_helper import embedding_job_journal

    args, policy, starts = fixture
    cls = embedding_job_journal._Owned
    original_read = cls.read
    session_cls = producer.isolated.IsolatedCPUEmbeddingSession
    original_close = session_cls.close
    armed, closes, owners = [], [], []

    def read(handle):
        if armed:
            handle.pending = True
            owners.append(handle)
            error = embedding_job_journal.JournalError("journal refused")
            error.cleanup_owner = handle
            raise error
        return original_read(handle)

    def authorization(_plan, boundary):
        if boundary == "before_encode":
            armed.append(1)
            raise ValueError("private")
        return "a" * 64

    def close(session):
        closes.append(1)
        return original_close(session)

    monkeypatch.setattr(cls, "read", read)
    monkeypatch.setattr(session_cls, "close", close)
    with pytest.raises(producer.ProducerRefused) as caught:
        producer.produce(*args, authorization, worker_policy=policy)
    owner = caught.value.owner
    assert len(starts) == len(closes) == 1 and owners
    assert owner.session is None and owners[0] in owner.uncertainty
    with pytest.raises(embedding_job_journal.JournalError):
        owner.close()


def test_interrupted_success_path_session_close_is_not_retried(fixture, monkeypatch):
    from slaif_raggedized_helper import cpu_embedding_plan, embedding_job_journal

    args, policy, starts = fixture
    cls = producer.isolated.IsolatedCPUEmbeddingSession
    original = cls.close
    interrupt = KeyboardInterrupt("session cleanup")
    calls = []

    def close(session):
        calls.append(1)
        raise interrupt

    monkeypatch.setattr(cls, "close", close)
    owner = None
    try:
        with pytest.raises(KeyboardInterrupt) as caught:
            producer.produce(*args, lambda *_: "a" * 64, worker_policy=policy)
        assert caught.value is interrupt and len(calls) == len(starts) == 1
        owner = caught.value.cleanup_owner
        prepared = cpu_embedding_plan.build(*args[:11], worker_policy=policy)
        with pytest.raises(embedding_job_journal.JournalError):
            with embedding_job_journal.Journal(args[12]).own(prepared.plan_bytes):
                pass
    finally:
        monkeypatch.setattr(cls, "close", original)
        if owner is not None:
            owner.close()
    assert _state(args, policy) == "UNKNOWN_COMPLETION"


def test_old_source_complete_is_not_reused(fixture, monkeypatch, tmp_path):
    """The base profile/code and bridge hashes represent the real pre-cutover source."""
    from slaif_raggedized_helper import cpu_embedding_plan, cpu_execution_contract

    args, policy, starts = fixture
    old_profile = "7ca03c1a42c7040867f13790371001a912fdae3b90272ff7ba98ed1726848638"
    old_code = "b650eb650b014a57c58fba85b9b64474c97f0cd21f5a8664fa4123b8b8420d7d"
    old_bridge = "279438b12953e6f000399551e3cab543bcf35b9278097661e2c4f266e4ea395f"
    original_argv = cpu._argv
    bridge = cpu_execution_contract._bridge()
    fake = tmp_path / "old-identity-fake.py"
    fake.write_text(
        FAKE.replace(
            "sys.exit(m.main())",
            "from slaif_raggedized_helper import cpu_embedding_worker as w\n"
            f"w._profile = lambda *a: {old_profile!r}\n"
            f"w._code_identity = lambda: {old_code!r}\n"
            "sys.exit(m.main())",
        )
    )

    def old_argv(*a):
        argv = original_argv(*a)
        argv[argv.index("/worker.py") - 1] = str(fake)
        return argv

    with monkeypatch.context() as patcher:
        patcher.setattr(cpu, "_profile", lambda *a: old_profile)
        patcher.setattr(cpu, "_code_identity", lambda: old_code)
        patcher.setattr(
            cpu_execution_contract,
            "_bridge",
            lambda: {
                **bridge,
                "cpu_execution_contract.py": old_bridge,
            },
        )
        patcher.setattr(cpu, "_argv", old_argv)
        old_plan = cpu_embedding_plan.build(*args[:11], worker_policy=policy)
        old_result = producer.produce(*args, lambda *_: "a" * 64, worker_policy=policy)
        assert not old_result.reused
    new_plan = cpu_embedding_plan.build(*args[:11], worker_policy=policy)
    assert new_plan.spec.job_id != old_plan.spec.job_id
    assert new_plan.execution_fingerprint != old_plan.execution_fingerprint
    assert new_plan.intended_execution_fingerprint == old_plan.intended_execution_fingerprint
    assert (
        json.loads(new_plan.predicted_record)["space"]
        == json.loads(old_plan.predicted_record)["space"]
    )
    new_result = producer.produce(*args, lambda *_: "a" * 64, worker_policy=policy)
    assert not new_result.reused and new_result.job_id != old_result.job_id
    assert len(starts) == 2
