"""Actual original and native counting with a borrowed, unstarted GPU launch."""

import dataclasses
import hashlib
import inspect
import json
import subprocess
import textwrap

import pytest

from test_embedding_batch_plan_composition import journey  # noqa: F401
from test_gpu_worker_launch import _prepared_fixture
from slaif_raggedized_helper import embedding_batch_plan as source
from slaif_raggedized_helper import gpu_embedding_plan as plan
from slaif_raggedized_helper import gpu_worker_launch as launch
from slaif_raggedized_helper import isolated_gpu_embedding as bridge


@pytest.fixture
def actual(journey, tmp_path, monkeypatch):  # noqa: F811
    args = journey[0]
    setup, reservation = _prepared_fixture(tmp_path, monkeypatch)
    setup.update(
        artifact_root=str(args[5]),
        manifest=args[4],
        definition=args[6],
        tokenizer=args[7],
        inventory_id=args[8],
    )
    prepared = launch.prepare(**setup)
    try:
        yield args, prepared, reservation, journey[1]
    finally:
        prepared.close()
        reservation.close()


def test_real_source_prediction_and_immutable_result(actual, monkeypatch):
    args, prepared, reservation, revisions = actual
    from slaif_raggedized_helper import embedding_batch_store, gpu_embedding_worker

    def forbidden(*args, **kwargs):
        raise AssertionError("planning must not publish or start a GPU parent")

    monkeypatch.setattr(embedding_batch_store, "publish", forbidden)
    monkeypatch.setattr(plan.embedding_job_journal.Journal, "__init__", forbidden)
    monkeypatch.setattr(gpu_embedding_worker.GPUEmbeddingWorker, "__init__", forbidden)
    original = subprocess.Popen.__init__
    launches = []

    def only_native(process, argv, **kwargs):
        launches.append(argv)
        assert "tokenizer_session_worker.py" in str(argv)
        return original(process, argv, **kwargs)

    monkeypatch.setattr(subprocess.Popen, "__init__", only_native)
    result = plan.build(*args, prepared)
    generic = source.build(*args)
    assert launches
    before, after = json.loads(generic.plan_bytes), json.loads(result.plan_bytes)
    assert result.texts == generic.texts
    assert before["rows"] == after["rows"]
    assert result.execution_fingerprint == hashlib.sha256(result.predicted_record).hexdigest()
    assert after["dependencies"]["execution_fingerprint"] == result.execution_fingerprint
    assert before["dependencies"]["execution_fingerprint"] != result.execution_fingerprint
    assert result.spec == plan.embedding_job_journal.make_spec(result.plan_bytes)
    assert result == plan.build(*args, prepared)
    assert plan.build(*args[:3], args[3][::-1], *args[4:], prepared).texts == result.texts[::-1]
    assert plan.build(*args, prepared, purpose="evaluate").spec.job_id != result.spec.job_id
    assert bridge.validate_record(result.predicted_record, result.native_runtime_record)
    with pytest.raises(dataclasses.FrozenInstanceError):
        result.space_id = "x"
    reservation.assert_owned()
    prepared.revalidate()


def test_actual_binding_and_causal_control(actual):
    args, prepared, _, _ = actual
    prediction, record = plan._prediction(prepared, args[9])
    start = plan.wire.parse(prepared.startup)
    with pytest.raises(ValueError):
        plan._bind(start, record, prediction, b"wrong", args[6], args[7], args[8])
    code = textwrap.dedent(inspect.getsource(plan._bind))
    predicate = 'start["manifest"].encode("utf-8") != manifest'
    assert code.count(predicate) == 1
    scope = dict(plan.__dict__)
    exec(compile(code.replace(predicate, "False"), "<binding-control>", "exec"), scope)
    scope["_bind"](start, record, prediction, b"wrong", args[6], args[7], args[8])
    print(
        "binding_control_sha256="
        + hashlib.sha256(code.replace(predicate, "False").encode()).hexdigest()
    )
    for candidate in [
        (*args[:4], b"wrong", *args[5:]),
        (*args[:8], "0" * 64, args[9]),
        (*args[:7], dataclasses.replace(args[7], sha256="0" * 64), *args[8:]),
    ]:
        with pytest.raises(plan.PlanError):
            plan.build(*candidate, prepared)
    with pytest.raises(plan.PlanError):
        plan.build(*args, prepared, purpose="invalid")


def test_real_corruption_and_changed_prediction(actual, monkeypatch):
    args, prepared, reservation, revisions = actual
    blob = args[0].root / "blobs" / revisions[0].blob
    old = blob.read_bytes()
    blob.write_bytes(b"corrupt")
    try:
        with pytest.raises(plan.PlanError):
            plan.build(*args, prepared)
    finally:
        blob.write_bytes(old)
    real = plan._prediction
    calls = []

    def changed(*values):
        result = real(*values)
        calls.append(result)
        if len(calls) == 2:
            return dataclasses.replace(result[0], space_id="0" * 64), result[1]
        return result

    monkeypatch.setattr(plan, "_prediction", changed)
    with pytest.raises(plan.PlanError):
        plan.build(*args, prepared)
    assert len(calls) == 2
    reservation.assert_owned()
    prepared.revalidate()


def test_max_rows_rejected_before_count(journey, tmp_path, monkeypatch):  # noqa: F811
    args = journey[0]
    setup, reservation = _prepared_fixture(tmp_path, monkeypatch)
    setup.update(
        artifact_root=str(args[5]),
        manifest=args[4],
        definition=args[6],
        tokenizer=args[7],
        inventory_id=args[8],
        wire_policy=plan.wire.Policy(max_rows=1),
    )
    prepared = launch.prepare(**setup)
    try:

        def forbidden(*args, **kwargs):
            raise AssertionError("count must not start")

        monkeypatch.setattr(source, "build", forbidden)
        with pytest.raises(plan.PlanError):
            plan.build(*args, prepared)
        reservation.assert_owned()
    finally:
        prepared.close()
        reservation.close()


def test_artifact_and_detached_record_refusal(actual):
    args, prepared, reservation, _ = actual
    predicted, _ = plan._prediction(prepared, args[9])
    with pytest.raises(bridge.SessionRefused):
        bridge.validate_record(predicted.execution_record, predicted.native_runtime_record + b" ")
    artifact = args[5] / "tokenizer.json"
    original = artifact.read_bytes()
    artifact.write_bytes(b"corrupted")
    try:
        with pytest.raises(plan.PlanError):
            plan.build(*args, prepared)
    finally:
        artifact.write_bytes(original)
    reservation.assert_owned()
    prepared.revalidate()


def test_policy_changes_identity(actual):
    args, prepared, _, _ = actual
    first = plan.build(*args, prepared)
    changed = plan.build(
        *args, prepared, batch_policy=plan.retrieval_representation.BatchPolicy(max_items=127)
    )
    assert first.spec.job_id != changed.spec.job_id
    assert first.texts == changed.texts


def test_prediction_source_space_guard_control(actual):
    args, prepared, _, _ = actual
    prediction, record = plan._prediction(prepared, args[9])
    generic = source.build(*args)
    dep = json.loads(generic.plan_bytes)["dependencies"]
    legacy = dep["execution_fingerprint"]
    policy, bp = plan.retrieval_representation.Policy(), plan.retrieval_representation.BatchPolicy()
    plan._bind_source(dep, prediction, record, legacy, args[8], policy, bp)
    foreign = dataclasses.replace(prediction, space_id="0" * 64)
    with pytest.raises(ValueError):
        plan._bind_source(dep, foreign, record, legacy, args[8], policy, bp)
    code = textwrap.dedent(inspect.getsource(plan._bind_source))
    predicate = 'dep["space_id"] != prediction.space_id'
    assert code.count(predicate) == 1
    modified = code.replace(predicate, "False")
    scope = dict(plan.__dict__)
    exec(compile(modified, "<source-binding-control>", "exec"), scope)
    scope["_bind_source"](dep, foreign, record, legacy, args[8], policy, bp)
    print("source_control_sha256=" + hashlib.sha256(modified.encode()).hexdigest())


def test_native_file_change_during_count(actual, tmp_path, monkeypatch):
    import shutil

    args, prepared, reservation, _ = actual
    packages = tmp_path / "private-packages"
    shutil.copytree(args[9].packages, packages)
    runtime = dataclasses.replace(args[9], packages=packages)
    private_args = (*args[:9], runtime)
    real = source.build
    target = packages / "tokenizers" / "__init__.py"

    def change_after_count(*values, **kwargs):
        result = real(*values, **kwargs)
        target.write_bytes(target.read_bytes() + b"\n# changed\n")
        return result

    monkeypatch.setattr(source, "build", change_after_count)
    with pytest.raises(plan.PlanError):
        plan.build(*private_args, prepared)
    reservation.assert_owned()
    prepared.revalidate()
