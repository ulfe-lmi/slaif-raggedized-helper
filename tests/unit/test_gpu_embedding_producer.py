"""Bounded checks of producer authorization and durable binding helpers."""

import hashlib

import pytest

from slaif_raggedized_helper import gpu_embedding_producer as producer


@pytest.mark.parametrize("value", [None, False, True, "A" * 64, "a" * 63, 1, b"a" * 64])
def test_authorization_rejects_non_epoch(value):
    with pytest.raises(ValueError):
        producer._authorize(lambda *_: value, b"{}", "before_model")


def test_authorization_rejects_changed_epoch():
    assert producer._authorize(lambda *_: "a" * 64, b"{}", "before_model") == "a" * 64
    with pytest.raises(ValueError):
        producer._authorize(lambda *_: "b" * 64, b"{}", "before_encode", "a" * 64)


def test_output_binds_exact_metadata():
    result = producer._output(b"{}", "c" * 64)
    assert result == {
        "ref": "sha256:" + "c" * 64,
        "fingerprint": "sha256:" + hashlib.sha256(b"{}").hexdigest(),
        "availability": "verified",
    }
    with pytest.raises(ValueError):
        producer._output(b"{}", "sha256:" + "c" * 64)


def test_clock_refuses_regression(monkeypatch):
    monkeypatch.setattr(producer.time, "time_ns", lambda: 5_000_000)
    assert producer._now(5) == 5
    with pytest.raises(ValueError):
        producer._now(6)


def test_cleanup_attempts_both_owners_and_retains_lease(monkeypatch):
    from slaif_raggedized_helper import gpu_embedding_worker, isolated_gpu_embedding

    session = object.__new__(isolated_gpu_embedding.GPUTextEmbeddingSession)
    worker = object.__new__(gpu_embedding_worker.GPUEmbeddingWorker)
    events = []

    def session_close(obj):
        assert obj is session
        events.append("session")
        if events.count("session") == 1:
            raise ValueError("pending")

    def worker_close(obj):
        assert obj is worker
        events.append("worker")

    class Lease:
        def __exit__(self, *_):
            events.append("lease")

    monkeypatch.setattr(isolated_gpu_embedding.GPUTextEmbeddingSession, "close", session_close)
    monkeypatch.setattr(gpu_embedding_worker.GPUEmbeddingWorker, "close", worker_close)
    owner = producer._CleanupOwner(session, worker, Lease())
    with pytest.raises(ValueError):
        owner.close()
    assert events == ["session", "worker"]
    assert owner.session is session and owner.worker is None and owner.lease is not None
    owner.close()
    assert events == ["session", "worker", "session", "lease"]


def test_cleanup_interrupt_precedes_ordinary_failure(monkeypatch):
    from slaif_raggedized_helper import gpu_embedding_worker, isolated_gpu_embedding

    session = object.__new__(isolated_gpu_embedding.GPUTextEmbeddingSession)
    worker = object.__new__(gpu_embedding_worker.GPUEmbeddingWorker)
    interrupt = KeyboardInterrupt()

    def fail_session(_):
        raise ValueError

    def fail_worker(_):
        raise interrupt

    monkeypatch.setattr(isolated_gpu_embedding.GPUTextEmbeddingSession, "close", fail_session)
    monkeypatch.setattr(gpu_embedding_worker.GPUEmbeddingWorker, "close", fail_worker)
    owner = producer._CleanupOwner(session, worker, object())
    with pytest.raises(KeyboardInterrupt) as raised:
        owner.close()
    assert raised.value is interrupt
    assert owner.session is session and owner.worker is worker and owner.lease is not None


def test_descriptor_uncertainty_stays_sticky_after_resource_drain():
    marker = object()
    owner = producer._CleanupOwner(None, None, None, [marker])
    with pytest.raises(producer.ProducerRefused) as raised:
        owner.close()
    assert raised.value.owner is owner and owner.uncertainty == [marker]


def test_lease_close_uncertainty_is_never_retried():
    class Lease:
        calls = 0

        def __exit__(self, *_):
            self.calls += 1
            raise OSError("unknown close outcome")

    lease = Lease()
    owner = producer._CleanupOwner(None, None, lease)
    with pytest.raises(OSError):
        owner.close()
    with pytest.raises(producer.ProducerRefused):
        owner.close()
    assert lease.calls == 1 and owner.uncertainty == [lease]


def test_forked_cleanup_does_not_touch_creator_owners(monkeypatch):
    owner = producer._CleanupOwner(None, None, object())
    monkeypatch.setattr(producer.os, "getpid", lambda: owner.creator + 1)
    with pytest.raises(producer.ProducerRefused) as raised:
        owner.close()
    assert raised.value.owner is owner and owner.lease is not None


def test_typed_vector_binds_rows_payload_and_policy():
    from dataclasses import replace

    from slaif_raggedized_helper import embedding_vectors

    vectors = embedding_vectors.normalize_rows([[1.0] + [0.0] * 1023])
    encoded = producer._vector(vectors, 1)
    assert encoded.payload_sha256 == vectors.sha256
    with pytest.raises(ValueError):
        producer._vector(replace(vectors, rows=((0.0,) * 1024,)), 1)
    with pytest.raises(ValueError):
        producer._vector(replace(vectors, sha256="0" * 64), 1)
    with pytest.raises(ValueError):
        producer._vector(replace(vectors, policy_id="wrong"), 1)
    with pytest.raises(ValueError):
        producer._vector(vectors, 2)


@pytest.mark.parametrize(
    ("state", "dispatched", "expected"),
    [
        ("CLAIMED", False, "CANCELLED"),
        ("RUNNING", False, "FAILED"),
        ("RUNNING", True, "UNKNOWN_COMPLETION"),
    ],
)
def test_reconcile_actual_journal_attempt(tmp_path, state, dispatched, expected):
    from types import SimpleNamespace

    from slaif_raggedized_helper import embedding_job_journal as journal
    from test_embedding_job_journal import plan, wire

    tmp_path.chmod(0o700)
    data = wire(plan())  # Structural fixture only, not a source or model proof.
    with journal.Journal(tmp_path).own(data) as handle:
        current, revision = handle.read()
        started = current["events"][-1]["state"]["updated_ms"]
        transaction = producer._Attempt(
            handle, SimpleNamespace(spec=handle.spec), None, revision, started, "a" * 48
        )
        transaction.append("CLAIMED", started)
        if state == "RUNNING":
            transaction.append("RUNNING", started)
        assert transaction.reconcile(dispatched) == expected
        durable = handle.read()[0]["events"][-1]
        assert durable["state"]["status"] == expected
        assert durable["attempt"]["outcome"] == expected


def test_hostile_interrupt_preserves_identity_and_retains_owner():
    class HostileInterrupt(BaseException):
        def __setattr__(self, _name, _value):
            raise RuntimeError("cannot attach")

    error = HostileInterrupt()
    owner = producer._CleanupOwner(None, None, None)
    producer._attach_owner(error, owner)
    assert any(item is owner for item in producer._retained_cleanup)
    assert producer.pending_cleanup(error) is owner
    assert producer.pending_cleanup(HostileInterrupt()) is None
    assert producer._prefer(error, KeyboardInterrupt()) is error
    owner.close()
    assert producer.pending_cleanup(error) is None


def test_actual_journal_committed_complete_survives_interruption(tmp_path, monkeypatch):
    """Seeded typed fixture: a post-commit interruption cannot erase COMPLETE."""
    from types import SimpleNamespace

    from slaif_raggedized_helper import derived_store, embedding_batch_store
    from slaif_raggedized_helper import embedding_job_journal
    from test_embedding_batch_store import fixture, wire

    tmp_path.chmod(0o700)
    metadata_obj, vector = fixture(count=1)
    plan = {
        "format": "embedding-job-plan-v1",
        "purpose": "prepare",
        "dependencies": metadata_obj["dependencies"],
        "rows": metadata_obj["rows"],
        "codec_policy_fingerprint": metadata_obj["codec_policy_fingerprint"],
    }
    metadata = wire(metadata_obj)
    interrupt = KeyboardInterrupt("controlled post-commit interruption")
    with (
        derived_store.Store(tmp_path) as store,
        embedding_job_journal.Journal(tmp_path).own(wire(plan)) as handle,
    ):
        envelope, revision = handle.read()
        now = envelope["events"][-1]["state"]["updated_ms"]
        attempt = producer._Attempt(
            handle, SimpleNamespace(spec=handle.spec), store, revision, now, "a" * 48
        )
        attempt.append("CLAIMED", now)
        attempt.append("RUNNING", now)
        identifier = embedding_batch_store.publish(store, metadata, vector.container)
        output = producer._output(metadata, identifier)
        actual_commit = handle._commit

        def commit_then_interrupt(*args):
            actual_commit(*args)
            raise interrupt

        with monkeypatch.context() as context:
            context.setattr(handle, "_commit", commit_then_interrupt)
            with pytest.raises(KeyboardInterrupt) as raised:
                attempt.append("COMPLETE", now, output, metadata)
        assert raised.value is interrupt
        assert attempt.reconcile(True) == "COMPLETE"
        assert handle.verified_output(store, metadata).ref == output["ref"]
        assert embedding_batch_store.load(store, identifier, metadata).metadata == metadata
        assert [event["state"]["status"] for event in handle.read()[0]["events"]] == [
            "PENDING",
            "CLAIMED",
            "RUNNING",
            "COMPLETE",
        ]


def test_cleanup_uncertainty_does_not_release_known_journal_lease():
    class Lease:
        calls = 0

        def __exit__(self, *_args):
            self.calls += 1

    lease = Lease()
    marker = object()
    owner = producer._CleanupOwner(None, None, lease, [marker])
    with pytest.raises(producer.ProducerRefused) as raised:
        owner.close()
    assert raised.value.owner is owner
    assert owner.lease is lease and lease.calls == 0 and owner.uncertainty == [marker]


def test_reused_exception_does_not_select_an_ambiguous_owner():
    error = KeyboardInterrupt()
    first = producer._CleanupOwner(None, None, None)
    second = producer._CleanupOwner(None, None, None)
    producer._attach_owner(error, first)
    producer._attach_owner(error, second)
    assert producer.pending_cleanup(error) is None
    assert error.cleanup_owner is None
    first.close()
    assert producer.pending_cleanup(error) is second
    second.close()
    assert producer.pending_cleanup(error) is None
