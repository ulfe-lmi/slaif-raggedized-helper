import pytest

from slaif_raggedized_helper import cpu_embedding_producer as producer


@pytest.mark.parametrize("value", [None, False, True, "A" * 64, "a" * 63, 1, b"a" * 64])
def test_authorization_rejects_non_epoch(value):
    with pytest.raises(ValueError):
        producer._authorize(lambda *_: value, b"{}", "before_model")


def test_authorization_requires_same_epoch():
    assert producer._authorize(lambda *_: "a" * 64, b"{}", "before_model") == "a" * 64
    with pytest.raises(ValueError):
        producer._authorize(lambda *_: "b" * 64, b"{}", "before_encode", "a" * 64)


def test_clock_never_fabricates_time(monkeypatch):
    monkeypatch.setattr(producer.time, "time_ns", lambda: 5_000_000)
    assert producer._now(5) == 5
    with pytest.raises(ValueError):
        producer._now(6)


def test_cleanup_owner_holds_lease_until_session_drained():
    events = []

    class Session:
        def close(self):
            events.append("session")
            if len(events) == 1:
                raise RuntimeError

    class Lease:
        def __exit__(self, *_):
            events.append("lease")

    owner = producer._CleanupOwner(Session(), Lease())
    with pytest.raises(RuntimeError):
        owner.close()
    assert events == ["session"]
    owner.close()
    assert events == ["session", "session", "lease"]


def test_invalid_scalar_preflight_avoids_plan_io(tmp_path, monkeypatch):
    from slaif_raggedized_helper import derived_store

    tmp_path.chmod(0o700)
    calls = []
    monkeypatch.setattr(producer.plan, "build", lambda *a, **k: calls.append(1))
    with derived_store.Store(tmp_path) as store:
        with pytest.raises(producer.ProducerRefused):
            producer.produce(
                None,
                None,
                None,
                [True] * 129,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                store,
                tmp_path,
                lambda *_: "a" * 64,
            )
        with pytest.raises(producer.ProducerRefused):
            producer.produce(
                None,
                None,
                None,
                [],
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                store,
                tmp_path,
                None,
            )
    assert calls == []
