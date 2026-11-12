"""DATA-only scalar and result-shape checks; these do not prove producer execution."""

from dataclasses import FrozenInstanceError

import pytest

from slaif_raggedized_helper import corpus_embedding_executor as executor


def invoke(**changes):
    values = dict(
        originals=object.__new__(executor.OriginalStore),
        derived=object.__new__(executor.derived_store.Store),
        program_bytes=b"{}",
        manifest_bytes=b"{}",
        artifact_root="/tmp/artifact",
        embedding_definition=None,
        tokenizer_definition=None,
        expected_inventory_id="a" * 64,
        runtime=None,
        launch_inputs=None,
        reservation=None,
        journal_root="/tmp/journal",
        authorization_provider=lambda *_: "a" * 64,
        deadline_ms=1000,
        purpose="prepare",
    )
    values.update(changes)
    return executor.run(**values)


@pytest.mark.parametrize(
    "changes",
    [
        {"deadline_ms": True},
        {"deadline_ms": 0},
        {"deadline_ms": 86400001},
        {"program_bytes": bytearray(b"{}")},
        {"program_bytes": b""},
        {"manifest_bytes": b""},
        {"authorization_provider": None},
        {"purpose": "query"},
    ],
)
def test_cheap_preflight_refuses_before_snapshot(changes, monkeypatch):
    monkeypatch.setattr(executor, "_snapshot", lambda *_: pytest.fail("snapshot reached"))
    with pytest.raises(executor.ExecutorRefused):
        invoke(**changes)


def test_completion_is_frozen_lightweight_data():
    item = executor.BatchCompletion(0, "job", "output", "a" * 64, True)
    with pytest.raises(FrozenInstanceError):
        item.reused = False
    assert set(item.__dict__) == {
        "batch_index",
        "job_id",
        "output_ref",
        "metadata_sha256",
        "reused",
    }


def test_epoch_forwards_each_distinct_plan_and_boundary_without_caching():
    seen = []

    def provider(plan, boundary):
        seen.append((plan, boundary))
        return "a" * 64 if len(seen) < 3 else "b" * 64

    epoch = executor._Epoch(provider)
    assert epoch(b"plan-one", "before_model") == "a" * 64
    assert epoch(b"plan-one", "before_encode") == "a" * 64
    with pytest.raises(executor.ExecutorRefused):
        epoch(b"plan-two", "before_model")
    assert seen == [
        (b"plan-one", "before_model"),
        (b"plan-one", "before_encode"),
        (b"plan-two", "before_model"),
    ]


@pytest.mark.parametrize("bad", [None, "A" * 64, "a" * 63, "sha256:" + "a" * 64])
def test_epoch_refuses_invalid_provider_result(bad):
    with pytest.raises(executor.ExecutorRefused):
        executor._Epoch(lambda *_: bad)(b"actual plan data", "before_model")


def test_expired_deadline_stops_before_source_validation(monkeypatch):
    ticks = iter([100.0, 101.0])
    monkeypatch.setattr(executor.time, "monotonic", lambda: next(ticks))
    monkeypatch.setattr(executor, "_snapshot", lambda *_: ())
    monkeypatch.setattr(executor.program, "validate", lambda *_: pytest.fail("validation reached"))
    with pytest.raises(executor.ExecutorRefused):
        invoke(
            deadline_ms=1,
            originals=object.__new__(executor.OriginalStore),
            derived=object.__new__(executor.derived_store.Store),
            artifact_root="/tmp/artifact",
            journal_root="/tmp/journal",
            expected_inventory_id="a" * 64,
        )
