import hashlib
import json

import pytest
from pydantic import ValidationError

from slaif_raggedized_helper.job_records import (
    Attempt,
    JobSpec,
    JobState,
    RecordError,
    admit,
    serialize,
    transition,
)


def D(n):
    return "sha256:" + str(n) * 64


def spec():
    return {
        "version": 1,
        "kind": "annotation",
        "purpose": "prepare",
        "inputs": [
            {"kind": "source_revision", "ref": D(1), "fingerprint": D(2)},
            {"kind": "artifact", "ref": D(3), "fingerprint": D(4)},
        ],
        "configuration": {
            "policy": D(5),
            "model": D(6),
            "prompt": D(7),
            "encoder": D(8),
            "runtime": None,
        },
    }


def state(status, attempt=None, owner=None, output=None, time=10):
    return admit(
        JobState,
        {
            "version": 1,
            "job_id": D(1),
            "status": status,
            "attempt_id": attempt,
            "owner_id": owner,
            "updated_ms": time,
            "output": output,
        },
    )


def attempt(outcome, ident="a", output=None):
    return admit(
        Attempt,
        {
            "version": 1,
            "job_id": D(1),
            "attempt_id": ident,
            "request_id": "request_1",
            "outcome": outcome,
            "started_ms": 1,
            "ended_ms": 10,
            "input_tokens": 0,
            "output_tokens": None,
            "diagnostic_code": None,
            "output": output,
        },
    )


def test_identity_and_all_dependencies():
    data = spec()
    job = admit(JobSpec, data)
    body = {"domain": "job-spec", **data}
    raw = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    assert job.job_id == "sha256:" + hashlib.sha256(b"slaif-fingerprint-v1\n" + raw).hexdigest()
    assert admit(JobSpec, dict(reversed(list(data.items())))).job_id == job.job_id
    for key in ("policy", "model", "prompt", "encoder", "runtime"):
        changed = spec()
        changed["configuration"][key] = D(9)
        assert admit(JobSpec, changed).job_id != job.job_id
    for key in ("ref", "fingerprint"):
        changed = spec()
        changed["inputs"][0][key] = D(9)
        assert admit(JobSpec, changed).job_id != job.job_id
    for key, value in [("purpose", "evaluate"), ("kind", "embedding")]:
        changed = spec()
        changed[key] = value
        assert admit(JobSpec, changed).job_id != job.job_id
    changed = spec()
    changed["inputs"].reverse()
    assert admit(JobSpec, changed).job_id != job.job_id
    data["inputs"][0]["ref"] = D(9)
    assert job.inputs[0].ref == D(1)
    assert admit(JobSpec, serialize(job)) == job


def test_transitions_attempts_and_unknown():
    p = state("PENDING")
    c = state("CLAIMED", "a", "owner")
    r = state("RUNNING", "a", "owner")
    transition(p, c)
    transition(c, r)
    failed = state("RETRYABLE_FAILED", "a")
    a = attempt("RETRYABLE_FAILED")
    assert a.input_tokens == 0 and a.output_tokens is None
    transition(r, failed, a)
    retry = state("PENDING", "a")
    transition(failed, retry)
    with pytest.raises(RecordError):
        transition(retry, state("CLAIMED", "a", "owner"))
    transition(retry, state("CLAIMED", "b", "owner"))
    assert attempt("FAILED", "b").attempt_id != a.attempt_id
    unknown = state("UNKNOWN_COMPLETION", "a")
    transition(r, unknown, attempt("UNKNOWN_COMPLETION"))
    with pytest.raises(RecordError):
        transition(unknown, p)
    with pytest.raises(RecordError):
        transition(r, failed, attempt("RETRYABLE_FAILED", "b"))


def test_output_is_only_an_assertion():
    for availability in ("missing", "unverified", "verified"):
        out = {"ref": D(3), "fingerprint": D(4), "availability": availability}
        final = state("COMPLETE", "a", output=out)
        transition(state("RUNNING", "a", "owner"), final, attempt("COMPLETE", output=out))
        assert final.output.availability == availability
    transition(state("RUNNING", "a", "owner"), state("COMPLETE", "a"), attempt("COMPLETE"))


@pytest.mark.parametrize(
    "mutate",
    [
        lambda x: x.update(version=True),
        lambda x: x.update(extra_secret_location="secret"),
        lambda x: x["inputs"][0].update(ref="secret"),
        lambda x: x["configuration"].update(runtime=float("nan")),
        lambda x: x.update(inputs=x["inputs"] * 129),
        lambda x: x.update(purpose="run_shell"),
    ],
)
def test_safe_admission(mutate):
    data = spec()
    mutate(data)
    with pytest.raises(RecordError, match="^invalid job record$"):
        admit(JobSpec, data)


def test_malformed_records_and_bypass():
    for raw in (b'{"version":1,"version":1}', b"NaN", b"{" + b" " * 65536):
        with pytest.raises(RecordError, match="^invalid job record$"):
            admit(JobSpec, raw)
    bad = attempt("FAILED").model_copy(update={"input_tokens": True})
    with pytest.raises(RecordError):
        serialize(bad)
    with pytest.raises(ValidationError):
        attempt("FAILED").__class__(**{**attempt("FAILED").model_dump(), "ended_ms": 0})
    with pytest.raises(RecordError):
        state("RUNNING", "a")


def test_nested_rejections_and_correlation():
    data = spec()
    data["configuration"]["secret_location"] = "private"
    with pytest.raises(RecordError, match="^invalid job record$"):
        admit(JobSpec, data)
    for field, value in [
        ("started_ms", True),
        ("ended_ms", float("inf")),
        ("input_tokens", -1),
        ("diagnostic_code", "raw error"),
    ]:
        data = attempt("FAILED").model_dump(mode="json")
        data[field] = value
        with pytest.raises(RecordError, match="^invalid job record$"):
            admit(Attempt, data)
    with pytest.raises(RecordError):
        transition(state("RUNNING", "a", "owner"), state("FAILED", "a"), attempt("REJECTED"))
    with pytest.raises(RecordError):
        transition(state("CLAIMED", "a", "owner"), state("RUNNING", "a", "other"))
    with pytest.raises(RecordError):
        state("FAILED", "a", output={"ref": D(1), "fingerprint": D(2), "availability": "verified"})
