import pytest

from slaif_raggedized_helper import embedding_job_journal as journal


@pytest.mark.parametrize(
    "field,value",
    [
        ("metadata_bytes", b""),
        ("container_id", "x"),
        ("expected_revision", "x"),
        ("expected_state_bytes", b"{}"),
        ("deadline_ms", True),
        ("deadline_ms", 0),
        ("deadline_ms", 120001),
        ("validate_current", None),
    ],
)
def test_invalid_inputs_refused_before_handle_use(field, value):
    args = dict(
        metadata_bytes=b"{}",
        container_id="a" * 64,
        expected_revision="b" * 64,
        expected_state_bytes=b"{}",
        store=None,
        validate_current=lambda *_: "c" * 64,
        deadline_ms=5000,
    )
    args[field] = value
    with pytest.raises(journal.JournalError):
        journal._Owned.repair_running_output(None, **args)


def test_result_is_immutable():
    result = journal.OutputRepairResult(None, "a", "b", "c", "d", "e", 1)
    with pytest.raises((AttributeError, TypeError)):
        result.accounting = "KNOWN"
    assert result.physical_drain == result.accounting == "UNKNOWN"


def test_observation_is_wall_clock_and_refuses_rollback(monkeypatch):
    monkeypatch.setattr(journal.time, "time_ns", lambda: 123456789000000)
    assert journal._observation_ms(123456788) == 123456789
    assert journal._observation_ms(123456789) == 123456789
    with pytest.raises(ValueError):
        journal._observation_ms(123456790)


def test_same_owner_and_closed_handle_refuse_before_provider(tmp_path):
    import json
    from slaif_raggedized_helper import (
        embedding_batch_store as batch,
        embedding_vectors,
        job_records,
    )

    tmp_path.chmod(0o700)
    h = "a" * 64
    dep = dict.fromkeys(batch._DEPS, h)
    dep["normalization_policy_id"] = embedding_vectors.POLICY_ID
    plan = {
        "format": "embedding-job-plan-v1",
        "purpose": "prepare",
        "dependencies": dep,
        "codec_policy_fingerprint": batch.POLICY.fingerprint(),
        "rows": [
            dict(
                chunk_id="c",
                revision_id="r",
                extraction_id="e",
                representation_id=h,
                rendered_sha256=h,
                source_scope_sha256=h,
                input_sha256=h,
                token_count=2,
            )
        ],
    }

    def wire(v):
        return json.dumps(v, sort_keys=True, separators=(",", ":")).encode()

    def forbidden(*_):
        pytest.fail("provider called for refused state")

    with journal.Journal(tmp_path).own(wire(plan)) as handle:
        envelope, rev = handle.read()
        pending = job_records.serialize(
            job_records.admit(job_records.JobState, envelope["events"][0]["state"])
        )
        with pytest.raises(journal.JournalError):
            handle.repair_running_output(
                b"{}", h, rev, pending, store=None, validate_current=forbidden
            )
        assert handle.read()[1] == rev
        for invalid in (pending + b" ", pending.replace(b"PENDING", b"PENDING ")):
            with pytest.raises(journal.JournalError):
                handle.repair_running_output(
                    b"{}", h, rev, invalid, store=None, validate_current=forbidden
                )
        assert handle.read()[1] == rev
        state = dict(
            envelope["events"][0]["state"],
            status="CLAIMED",
            attempt_id="a",
            owner_id=handle.owner_id,
        )
        _, rev = handle.append(wire(state), None, rev)
        state["status"] = "RUNNING"
        _, rev = handle.append(wire(state), None, rev)
        raw = job_records.serialize(job_records.admit(job_records.JobState, state))
        with pytest.raises(journal.JournalError):
            handle.repair_running_output(b"{}", h, rev, raw, store=None, validate_current=forbidden)
        assert handle.read()[1] == rev
    with pytest.raises(journal.JournalError):
        handle.repair_running_output(b"{}", h, rev, raw, store=None, validate_current=forbidden)
