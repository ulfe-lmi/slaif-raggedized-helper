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
        Path(os.environ["SLAIF_CPU_WORKER_TEST_ROOT"]),
        Path(os.environ["SLAIF_CPU_WORKER_TEST_PACKAGES"]),
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
