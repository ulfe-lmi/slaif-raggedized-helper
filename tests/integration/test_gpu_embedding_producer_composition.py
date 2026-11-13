"""Synthetic GPU parent, actual native tokenizer and source-bound plan checks."""

import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

import pytest

from slaif_raggedized_helper import embedding_artifacts
from slaif_raggedized_helper import gpu_embedding_plan as plan
from slaif_raggedized_helper import gpu_embedding_producer as producer
from slaif_raggedized_helper import gpu_embedding_worker as parent
from slaif_raggedized_helper import gpu_worker_launch as launch
from slaif_raggedized_helper import isolated_gpu_embedding as bridge
from test_gpu_worker_launch import _prepared_fixture
from test_embedding_batch_plan_composition import journey  # noqa: F401
from test_embedding_artifacts import write_config


def test_parent_consumes_preparation_and_independent_drains(journey, tmp_path, monkeypatch):  # noqa: F811
    args = list(journey[0])
    manifest = json.loads(args[4])
    weight = next(item for item in manifest["files"] if item["role"] == "weights")
    (args[5] / weight["path"]).rename(args[5] / "model.safetensors")
    weight["path"] = "model.safetensors"
    write_config(
        args[5],
        manifest,
        "config",
        {"model_type": "xlm-roberta", "hidden_size": 1024, "vocab_size": 20, "pad_token_id": 1},
    )
    args[4] = json.dumps(manifest).encode()
    args[8] = embedding_artifacts.verify_artifacts(args[4], args[5]).inventory_id
    setup, reservation = _prepared_fixture(tmp_path, monkeypatch)
    setup.update(
        artifact_root=str(args[5]),
        manifest=args[4],
        definition=args[6],
        tokenizer=args[7],
        inventory_id=args[8],
    )
    capture_a = launch.PreparationOwner()
    launch_plan = launch.prepare(**setup, preparation_owner=capture_a)
    assert capture_a.prepared is launch_plan
    worker = None
    session = None
    handle = None
    fd = None
    try:
        planned = plan.build(*args, launch_plan)
        assert planned.spec.job_id.startswith("sha256:")
        script = (Path(launch_plan._owner.directory) / "worker.py").read_text()
        marker = 'if __name__ == "__main__":\n    sys.exit(main())'
        injection = """
class FakeBackend:
    def __init__(self, manifest, root, definition, tokenizer, inventory, lease, uuid):
        self.space = embedding_space.admit(manifest, root, definition, tokenizer, inventory)
        self._vocab = 20
    def forward_cls(self, rows):
        return [[float(row[0]), float(len(row))] + [0.0] * 1022 for row in rows]
    def close(self):
        pass
gpu_embedding_backend.GPUEmbeddingBackend = FakeBackend
"""
        assert script.count(marker) == 1
        harness = script.replace(marker, injection + "\n" + marker).encode()
        path = tmp_path / "gpu-harness.py"
        path.write_bytes(harness)
        path.chmod(0o400)
        print("harness_sha256=" + hashlib.sha256(harness).hexdigest())
        fd = os.open(path, os.O_RDONLY | os.O_CLOEXEC)
        worker_fd = launch_plan._descriptors["worker"]
        original = subprocess.Popen.__init__

        def intercept(process, argv, **kwargs):
            argv = list(argv)
            if "/worker.py" in argv:
                index = argv.index("/worker.py")
                assert argv[index - 1] == f"/proc/self/fd/{worker_fd}"
                argv[index - 1] = f"/proc/self/fd/{fd}"
                kwargs["pass_fds"] = tuple(
                    fd if value == worker_fd else value for value in kwargs["pass_fds"]
                )
            return original(process, argv, **kwargs)

        with monkeypatch.context() as context:
            context.setattr(subprocess.Popen, "__init__", intercept)
            worker = parent.GPUEmbeddingWorker.__new__(parent.GPUEmbeddingWorker)
            parent.GPUEmbeddingWorker.__init__(worker, launch_plan)
        session = bridge.GPUTextEmbeddingSession.__new__(bridge.GPUTextEmbeddingSession)
        bridge.GPUTextEmbeddingSession.__init__(session, worker, args[9])
        observed = producer._observe(session, planned, args[6])
        assert observed.execution_record == planned.predicted_record
        from slaif_raggedized_helper import embedding_job_journal

        handle = embedding_job_journal.Journal(tmp_path).own(planned.plan_bytes)
        handle.__enter__()
        cleanup = producer._CleanupOwner(
            session, worker, handle, preparation=launch_plan, capture=capture_a
        )

        def fail_native_drain(_session):
            raise ValueError("controlled actual native drain fault")

        with monkeypatch.context() as context:
            context.setattr(bridge.GPUTextEmbeddingSession, "_drain", fail_native_drain)
            with pytest.raises(ValueError):
                cleanup.close()
        assert cleanup.session is session and cleanup.worker is None
        assert cleanup.preparation is None and cleanup.capture is None and launch_plan._closed
        assert not capture_a.pending
        assert cleanup.lease is handle
        handle.lease.assert_owned()
        worker = None
        cleanup.close()
        assert cleanup.session is None and cleanup.lease is None
        handle = None
        session = None
        with embedding_job_journal.Journal(tmp_path).own(planned.plan_bytes) as reopened:
            assert reopened.read()[0]["events"][-1]["state"]["status"] == "PENDING"
        with pytest.raises(launch.LaunchRefused):
            launch_plan.revalidate()
        with pytest.raises(plan.PlanError):
            plan.build(*args, launch_plan)
        capture_b = launch.PreparationOwner()
        second = launch.prepare(**setup, preparation_owner=capture_b)
        try:
            assert capture_b.prepared is second
            assert second.startup != launch_plan.startup
            assert plan.build(*args, second) == planned
            reservation.assert_owned()
        finally:
            second.close()
            capture_b.close()
    finally:
        if session is not None:
            session.close()
        if worker is not None:
            parent.GPUEmbeddingWorker.close(worker)
        if handle is not None:
            handle.__exit__(None, None, None)
        if fd is not None:
            os.close(fd)
        launch_plan.close()
        reservation.close()


def test_fresh_plan_with_seeded_typed_journal_binding(journey, tmp_path, monkeypatch):  # noqa: F811
    """Seeded synthetic vectors test durable binding, not neural provenance."""
    from slaif_raggedized_helper import derived_store, embedding_batch_store
    from slaif_raggedized_helper import embedding_job_journal, embedding_vectors

    args = journey[0]
    setup, reservation = _prepared_fixture(tmp_path, monkeypatch)
    setup.update(
        artifact_root=str(args[5]),
        manifest=args[4],
        definition=args[6],
        tokenizer=args[7],
        inventory_id=args[8],
    )
    launch_plan = launch.prepare(**setup)
    try:
        prepared = plan.build(*args, launch_plan)
        parsed = json.loads(prepared.plan_bytes)
        rows = [[1.0] + [0.0] * 1023 for _ in parsed["rows"]]
        vector = producer._vector(embedding_vectors.normalize_rows(rows), len(rows))
        metadata = producer._metadata(parsed, vector)
        with derived_store.Store(tmp_path) as store:
            identifier = embedding_batch_store.publish(store, metadata, vector.container)
            output = producer._output(metadata, identifier)
            assert producer._reuse_metadata(store, output["ref"], parsed) == metadata
            changed = dict(
                parsed, rows=[dict(parsed["rows"][0], token_count=3), *parsed["rows"][1:]]
            )
            with pytest.raises(ValueError):
                producer._reuse_metadata(store, output["ref"], changed)
            import inspect
            import textwrap

            code = textwrap.dedent(inspect.getsource(producer._reuse_metadata))
            predicate = "obj[k] != plan[k]"
            assert code.count(predicate) == 1
            modified = code.replace(predicate, '(obj[k] != plan[k] and k != "rows")')
            scope = dict(producer.__dict__)
            exec(compile(modified, "<row-binding-control>", "exec"), scope)
            assert scope["_reuse_metadata"](store, output["ref"], changed) == metadata
            print("row_control_sha256=" + hashlib.sha256(modified.encode()).hexdigest())
            with embedding_job_journal.Journal(tmp_path).own(prepared.plan_bytes) as handle:
                state, rev = handle.read()
                now = state["events"][-1]["state"]["updated_ms"]
                attempt = producer._Attempt(handle, prepared, store, rev, now, "a" * 48)
                attempt.append("CLAIMED", now)
                attempt.append("RUNNING", now)
                original_commit = handle._commit

                def committed_then_error(*values):
                    original_commit(*values)
                    raise OSError("synthetic post-commit error")

                monkeypatch.setattr(handle, "_commit", committed_then_error)
                with pytest.raises(Exception):
                    attempt.append("COMPLETE", now, output, metadata)
                monkeypatch.setattr(handle, "_commit", original_commit)
                assert attempt.reconcile(True) == "COMPLETE"
                assert [entry["state"]["status"] for entry in handle.read()[0]["events"]] == [
                    "PENDING",
                    "CLAIMED",
                    "RUNNING",
                    "COMPLETE",
                ]
                assert handle.verified_output(store, metadata).ref == output["ref"]
                assert embedding_batch_store.load(store, identifier, metadata).metadata == metadata
            inputs = producer.LaunchInputs(
                *(
                    setup[key]
                    for key in (
                        "source_root",
                        "staging_root",
                        "runtime_root",
                        "packages_root",
                        "lease_root",
                        "device",
                        "drivers",
                        "resource",
                        "wire_policy",
                    )
                )
            )
            boundaries = []

            def trusted_test_authorization(data, boundary):
                assert data == prepared.plan_bytes
                boundaries.append(boundary)
                return "a" * 64

            def no_parent(*_args, **_kwargs):
                raise AssertionError("reuse must not start a GPU parent")

            with monkeypatch.context() as context:
                context.setattr(parent.GPUEmbeddingWorker, "__init__", no_parent)
                result = producer.produce(
                    *args, inputs, reservation, store, tmp_path, trusted_test_authorization
                )
            assert result.reused and result.output_ref == output["ref"]
            assert result.metadata == metadata
            assert boundaries == ["before_model", "before_reuse"]

            def changed_epoch(_data, boundary):
                return "b" * 64 if boundary == "before_reuse" else "a" * 64

            with monkeypatch.context() as context:
                context.setattr(parent.GPUEmbeddingWorker, "__init__", no_parent)
                with pytest.raises(producer.ProducerRefused):
                    producer.produce(*args, inputs, reservation, store, tmp_path, changed_epoch)
            with embedding_job_journal.Journal(tmp_path).own(prepared.plan_bytes) as handle:
                assert handle.read()[0]["events"][-1]["state"]["status"] == "COMPLETE"
            reservation.assert_owned()
            (tmp_path / "derived" / "v1" / "objects" / vector.container_sha256).write_bytes(
                b"corrupt"
            )
            with embedding_job_journal.Journal(tmp_path).own(prepared.plan_bytes) as handle:
                with pytest.raises(embedding_job_journal.JournalError):
                    handle.verified_output(store, metadata)
            with monkeypatch.context() as context:
                context.setattr(parent.GPUEmbeddingWorker, "__init__", no_parent)
                with pytest.raises(producer.ProducerRefused):
                    producer.produce(
                        *args, inputs, reservation, store, tmp_path, trusted_test_authorization
                    )
            with embedding_job_journal.Journal(tmp_path).own(prepared.plan_bytes) as handle:
                assert handle.read()[0]["events"][-1]["state"]["status"] == "COMPLETE"
    finally:
        launch_plan.close()
        reservation.close()


def _one_batch_scenario(journey_data, tmp_path, monkeypatch, deny_before_encode):
    """Full synthetic parent composition, without a real model or physical GPU."""
    from slaif_raggedized_helper import derived_store

    args = list(journey_data[0])
    manifest = json.loads(args[4])
    weight = next(item for item in manifest["files"] if item["role"] == "weights")
    (args[5] / weight["path"]).rename(args[5] / "model.safetensors")
    weight["path"] = "model.safetensors"
    write_config(
        args[5],
        manifest,
        "config",
        {"model_type": "xlm-roberta", "hidden_size": 1024, "vocab_size": 20, "pad_token_id": 1},
    )
    args[4] = json.dumps(manifest).encode()
    args[8] = embedding_artifacts.verify_artifacts(args[4], args[5]).inventory_id
    args[3] = args[3][:1]
    setup, reservation = _prepared_fixture(tmp_path, monkeypatch)
    inputs = producer.LaunchInputs(
        *(
            setup[key]
            for key in (
                "source_root",
                "staging_root",
                "runtime_root",
                "packages_root",
                "lease_root",
                "device",
                "drivers",
                "resource",
                "wire_policy",
            )
        )
    )
    starts, descriptors, boundaries, plan_bytes = [], [], [], []
    prepared_calls = []
    receipt_fault_calls = []
    late_owner = None
    cpu_start = None
    interrupt = KeyboardInterrupt("synthetic authorization interruption")

    class HostileInterrupt(BaseException):
        def __setattr__(self, _name, _value):
            raise RuntimeError("cannot attach exception attributes")

    hostile = HostileInterrupt()
    original = subprocess.Popen.__init__

    def intercept(process, argv, **kwargs):
        argv = list(argv)
        if argv[0] == "/usr/bin/prlimit" and "/worker.py" in argv:
            starts.append(1)
            index = argv.index("/worker.py")
            old_fd = int(argv[index - 1].rsplit("/", 1)[-1])
            script = Path(f"/proc/self/fd/{old_fd}").read_text()
            marker = 'if __name__ == "__main__":\n    sys.exit(main())'
            injection = """
class FakeBackend:
    def __init__(self, manifest, root, definition, tokenizer, inventory, lease, uuid):
        self.space = embedding_space.admit(manifest, root, definition, tokenizer, inventory)
        self._vocab = 20
    def forward_cls(self, rows):
        return [[float(row[0]), float(len(row))] + [0.0] * 1022 for row in rows]
    def close(self):
        pass
gpu_embedding_backend.GPUEmbeddingBackend = FakeBackend
"""
            assert script.count(marker) == 1
            harness = script.replace(marker, injection + "\n" + marker).encode()
            print("producer_harness_sha256=" + hashlib.sha256(harness).hexdigest(), flush=True)
            path = tmp_path / "producer-harness.py"
            path.write_bytes(harness)
            path.chmod(0o400)
            fd = os.open(path, os.O_RDONLY | os.O_CLOEXEC)
            descriptors.append(fd)
            argv[index - 1] = f"/proc/self/fd/{fd}"
            kwargs["pass_fds"] = tuple(
                fd if value == old_fd else value for value in kwargs["pass_fds"]
            )
        return original(process, argv, **kwargs)

    def trusted_test_authorization(data, boundary):
        assert type(data) is bytes
        boundaries.append(boundary)
        plan_bytes.append(data)
        print("authorization_boundary=" + boundary, flush=True)
        if cpu_start is not None:
            print(f"producer_cpu_at_{boundary}={time.process_time() - cpu_start:.3f}", flush=True)
        if deny_before_encode == "interrupt" and boundary == "before_encode":
            raise interrupt
        if (
            deny_before_encode in ("hostile_interrupt", "hostile_pending")
            and boundary == "before_encode"
        ):
            raise hostile
        if deny_before_encode is True and boundary == "before_encode":
            return "b" * 64
        if deny_before_encode == "publish_epoch" and boundary == "before_publish":
            return "b" * 64
        if deny_before_encode == "complete_epoch" and boundary == "before_complete":
            return "b" * 64
        return "a" * 64

    try:
        with derived_store.Store(tmp_path) as store:
            with monkeypatch.context() as context:
                context.setattr(subprocess.Popen, "__init__", intercept)
                cpu_start = time.process_time()
                wall_start = time.monotonic()
                if deny_before_encode == "b_close_fault":
                    real_prepare = launch.prepare
                    real_close = launch.PreparedLaunch.close

                    def observe_prepare(**kwargs):
                        value = real_prepare(**kwargs)
                        prepared_calls.append(value)
                        return value

                    def fail_only_b(prepared):
                        if len(prepared_calls) >= 2 and prepared is prepared_calls[1]:
                            raise OSError("controlled B close before cleanup")
                        return real_close(prepared)

                    context.setattr(launch, "prepare", observe_prepare)
                    context.setattr(launch.PreparedLaunch, "close", fail_only_b)
                if deny_before_encode == "hostile_pending":

                    def fail_native_cleanup(_session):
                        raise OSError("controlled native cleanup failure")

                    context.setattr(bridge.GPUTextEmbeddingSession, "_drain", fail_native_cleanup)
                if deny_before_encode in ("receipt_fault", "record_fault"):
                    from dataclasses import replace

                    actual_encode = bridge.GPUTextEmbeddingSession.encode

                    def corrupt_actual_receipt(session, texts):
                        actual = actual_encode(session, texts)
                        receipt_fault_calls.append(1)
                        if deny_before_encode == "record_fault":
                            return replace(actual, execution_record=actual.execution_record + b" ")
                        wrong = replace(actual.receipts[0], count=actual.receipts[0].count + 1)
                        return replace(actual, receipts=(wrong, *actual.receipts[1:]))

                    context.setattr(
                        bridge.GPUTextEmbeddingSession, "encode", corrupt_actual_receipt
                    )
                if deny_before_encode in ("dispatch_fail", "dispatch_interrupt"):

                    def fault_preflight(_session, _texts):
                        if deny_before_encode == "dispatch_interrupt":
                            raise interrupt
                        raise ValueError("controlled actual encode preflight fault")

                    context.setattr(bridge.GPUTextEmbeddingSession, "_preflight", fault_preflight)
                if deny_before_encode in ("hostile_interrupt", "hostile_pending"):
                    with pytest.raises(HostileInterrupt) as raised:
                        producer.produce(
                            *args, inputs, reservation, store, tmp_path, trusted_test_authorization
                        )
                    assert raised.value is hostile
                elif deny_before_encode in ("interrupt", "dispatch_interrupt"):
                    with pytest.raises(KeyboardInterrupt) as raised:
                        producer.produce(
                            *args, inputs, reservation, store, tmp_path, trusted_test_authorization
                        )
                    assert raised.value is interrupt
                elif deny_before_encode:
                    with pytest.raises(producer.ProducerRefused) as refused:
                        producer.produce(
                            *args, inputs, reservation, store, tmp_path, trusted_test_authorization
                        )
                    if deny_before_encode == "b_close_fault":
                        late_owner = refused.value.owner
                        assert late_owner is not None and late_owner.lease is not None
                        assert (
                            late_owner.capture is not None
                            and late_owner.preparation is prepared_calls[1]
                        )
                        late_owner.lease.lease.assert_owned()
                    else:
                        assert refused.value.owner is None
                else:
                    result = producer.produce(
                        *args, inputs, reservation, store, tmp_path, trusted_test_authorization
                    )
                    print(f"producer_call_cpu={time.process_time() - cpu_start:.3f}", flush=True)
                    print(f"producer_call_wall={time.monotonic() - wall_start:.3f}", flush=True)
            assert starts == [1]
            if deny_before_encode in ("receipt_fault", "record_fault"):
                assert receipt_fault_calls == [1]
            if late_owner is not None:
                late_owner.close()
                assert late_owner.preparation is None and late_owner.capture is None
                assert late_owner.lease is None
            if deny_before_encode == "hostile_pending":
                pending = producer.pending_cleanup(hostile)
                assert pending is not None
                assert pending.session is not None and pending.worker is None
                assert pending.lease is not None and pending.preparation is None
                pending.lease.lease.assert_owned()
                pending.close()
                assert pending.session is None and pending.lease is None
                assert producer.pending_cleanup(hostile) is None
            if deny_before_encode:
                from slaif_raggedized_helper import embedding_job_journal

                expected_boundaries = ["before_model", "before_encode"]
                if deny_before_encode in ("publish_epoch", "complete_epoch", "b_close_fault"):
                    expected_boundaries.append("before_publish")
                if deny_before_encode in ("complete_epoch", "b_close_fault"):
                    expected_boundaries.append("before_complete")
                assert boundaries == expected_boundaries
                with embedding_job_journal.Journal(tmp_path).own(plan_bytes[0]) as handle:
                    expected = (
                        "UNKNOWN_COMPLETION"
                        if deny_before_encode
                        in (
                            "dispatch_fail",
                            "dispatch_interrupt",
                            "receipt_fault",
                            "record_fault",
                            "publish_epoch",
                            "complete_epoch",
                            "b_close_fault",
                        )
                        else "FAILED"
                    )
                    assert handle.read()[0]["events"][-1]["state"]["status"] == expected
                if deny_before_encode in ("publish_epoch", "complete_epoch", "b_close_fault"):
                    objects = tmp_path / "derived" / "v1" / "objects"
                    published = objects.exists() and any(objects.iterdir())
                    assert published is (deny_before_encode != "publish_epoch")
            else:
                assert not result.reused and len(result.batch.row_ids) == 1
                assert boundaries == [
                    "before_model",
                    "before_encode",
                    "before_publish",
                    "before_complete",
                ]
                from slaif_raggedized_helper import embedding_job_journal

                with embedding_job_journal.Journal(tmp_path).own(plan_bytes[0]) as handle:
                    states = [entry["state"]["status"] for entry in handle.read()[0]["events"]]
                    assert states == ["PENDING", "CLAIMED", "RUNNING", "COMPLETE"]
                    assert handle.verified_output(store, result.metadata).ref == result.output_ref
                assert store.load(result.output_ref[7:]).manifest
                revision = json.loads(plan_bytes[0])["rows"][0]["revision_id"]
                assert args[0].read_original(revision)
                assert not list(Path(setup["staging_root"]).iterdir())
                print("job_id=" + result.job_id, flush=True)
                print("output_ref=" + result.output_ref, flush=True)
                print("metadata_sha256=" + hashlib.sha256(result.metadata).hexdigest(), flush=True)
                print(
                    "execution_record_sha256="
                    + hashlib.sha256(result.execution_record).hexdigest(),
                    flush=True,
                )
                print(
                    "native_record_sha256="
                    + hashlib.sha256(result.native_runtime_record).hexdigest(),
                    flush=True,
                )
                print("journal_trace=" + ",".join(states), flush=True)
                split_root = os.environ.get("SLAIF_PRODUCER_SPLIT_ROOT")
                if split_root:
                    import base64

                    success = {
                        "state_root": str(tmp_path),
                        "manifest": base64.b64encode(args[4]).decode(),
                        "inventory": args[8],
                        "ids": args[3],
                        "job_id": result.job_id,
                        "output_ref": result.output_ref,
                        "metadata_sha256": hashlib.sha256(result.metadata).hexdigest(),
                        "execution_sha256": hashlib.sha256(result.execution_record).hexdigest(),
                        "native_sha256": hashlib.sha256(result.native_runtime_record).hexdigest(),
                    }
                    (Path(split_root) / "success.json").write_text(
                        json.dumps(success, sort_keys=True)
                    )
            reservation.assert_owned()
    finally:
        for fd in descriptors:
            os.close(fd)
        reservation.close()


def test_one_batch_owned_preparations(tmp_path, monkeypatch, request):
    if os.environ.get("SLAIF_PRODUCER_SPLIT_REUSE") == "1":
        _reuse_split_fixture(tmp_path, monkeypatch)
    elif os.environ.get("SLAIF_PRODUCER_SPLIT_ROOT"):
        _produce_split_fixture(tmp_path, monkeypatch)
    else:
        _one_batch_scenario(request.getfixturevalue("journey"), tmp_path, monkeypatch, False)


def test_epoch_change_before_encode_drains_owned_parent(journey, tmp_path, monkeypatch):  # noqa: F811
    _one_batch_scenario(journey, tmp_path, monkeypatch, True)


def test_interrupt_before_encode_preserves_original(journey, tmp_path, monkeypatch):  # noqa: F811
    _one_batch_scenario(journey, tmp_path, monkeypatch, "interrupt")


def test_encode_entry_fault_records_unknown_completion(journey, tmp_path, monkeypatch):  # noqa: F811
    _one_batch_scenario(journey, tmp_path, monkeypatch, "dispatch_fail")


def test_encode_entry_interrupt_preserves_unknown_and_original(journey, tmp_path, monkeypatch):  # noqa: F811
    _one_batch_scenario(journey, tmp_path, monkeypatch, "dispatch_interrupt")


def test_hostile_interruption_before_encode_preserves_identity(journey, tmp_path, monkeypatch):  # noqa: F811
    _one_batch_scenario(journey, tmp_path, monkeypatch, "hostile_interrupt")


def test_hostile_interrupt_with_pending_native_cleanup(journey, tmp_path, monkeypatch):  # noqa: F811
    _one_batch_scenario(journey, tmp_path, monkeypatch, "hostile_pending")


def test_epoch_change_before_publish_after_dispatch(journey, tmp_path, monkeypatch):  # noqa: F811
    _one_batch_scenario(journey, tmp_path, monkeypatch, "publish_epoch")


def test_epoch_change_before_complete_leaves_orphan(journey, tmp_path, monkeypatch):  # noqa: F811
    _one_batch_scenario(journey, tmp_path, monkeypatch, "complete_epoch")


def test_b_close_failure_retains_journal_and_orphan(journey, tmp_path, monkeypatch):  # noqa: F811
    _one_batch_scenario(journey, tmp_path, monkeypatch, "b_close_fault")


def test_actual_receipt_mismatch_after_encode(journey, tmp_path, monkeypatch):  # noqa: F811
    _one_batch_scenario(journey, tmp_path, monkeypatch, "receipt_fault")


def test_actual_execution_record_mismatch_after_encode(journey, tmp_path, monkeypatch):  # noqa: F811
    _one_batch_scenario(journey, tmp_path, monkeypatch, "record_fault")


def test_preparation_fault_owner_attribution(tmp_path, monkeypatch):
    """An actual pre-return failure does not attach the pending launch owner."""
    import shutil

    setup, reservation = _prepared_fixture(tmp_path, monkeypatch)
    pending_before = set(map(id, launch._pending))
    original = launch.PreparedLaunch.revalidate
    remove = shutil.rmtree

    def fail_after_admission(prepared):
        original(prepared)
        raise OSError("controlled post-admission failure")

    def refuse_remove(path, *args, **kwargs):
        raise OSError("controlled pre-removal failure")

    try:
        with monkeypatch.context() as context:
            context.setattr(launch.PreparedLaunch, "revalidate", fail_after_admission)
            context.setattr(shutil, "rmtree", refuse_remove)
            with pytest.raises(launch.LaunchRefused) as raised:
                launch.prepare(**setup)
        new_pending = [item for item in launch._pending if id(item) not in pending_before]
        assert len(new_pending) == 1 and new_pending[0].pending
        assert not hasattr(raised.value, "cleanup_owner")
        assert new_pending[0].directory is not None
        assert new_pending[0].cleanup() == []
        assert not new_pending[0].pending
    finally:
        assert shutil.rmtree is remove
        reservation.close()


@pytest.mark.parametrize(
    "unfinished", ["CLAIMED", "RUNNING", "CANCELLED", "FAILED", "UNKNOWN_COMPLETION"]
)
def test_refuses_actual_unfinished_journal(journey, tmp_path, monkeypatch, unfinished):  # noqa: F811
    """Unfinished durable attempts are not stolen or restarted."""
    from slaif_raggedized_helper import derived_store, embedding_job_journal

    args = journey[0]
    setup, reservation = _prepared_fixture(tmp_path, monkeypatch)
    setup.update(
        artifact_root=str(args[5]),
        manifest=args[4],
        definition=args[6],
        tokenizer=args[7],
        inventory_id=args[8],
    )
    inputs = producer.LaunchInputs(
        *(
            setup[key]
            for key in (
                "source_root",
                "staging_root",
                "runtime_root",
                "packages_root",
                "lease_root",
                "device",
                "drivers",
                "resource",
                "wire_policy",
            )
        )
    )
    preparation = launch.prepare(**setup)
    try:
        planned = plan.build(*args, preparation)
        with derived_store.Store(tmp_path) as store:
            with embedding_job_journal.Journal(tmp_path).own(planned.plan_bytes) as handle:
                envelope, revision = handle.read()
                timestamp = envelope["events"][-1]["state"]["updated_ms"]
                attempt = producer._Attempt(handle, planned, store, revision, timestamp, "a" * 48)
                attempt.append("CLAIMED", timestamp)
                if unfinished in ("RUNNING", "FAILED", "UNKNOWN_COMPLETION"):
                    attempt.append("RUNNING", timestamp)
                if unfinished in ("CANCELLED", "FAILED", "UNKNOWN_COMPLETION"):
                    assert attempt.reconcile(unfinished == "UNKNOWN_COMPLETION") == unfinished

            def no_parent(*_args, **_kwargs):
                raise AssertionError("unfinished job must not start a GPU parent")

            with monkeypatch.context() as context:
                context.setattr(parent.GPUEmbeddingWorker, "__init__", no_parent)
                with pytest.raises(producer.ProducerRefused):
                    producer.produce(
                        *args, inputs, reservation, store, tmp_path, lambda *_: "a" * 64
                    )
            with embedding_job_journal.Journal(tmp_path).own(planned.plan_bytes) as handle:
                assert handle.read()[0]["events"][-1]["state"]["status"] == unfinished
            reservation.assert_owned()
    finally:
        preparation.close()
        reservation.close()


def test_mutated_launch_config_refused_before_preparation(tmp_path, monkeypatch):
    """Actual reservation plus mutated frozen data cannot authorize fresh pins."""
    from dataclasses import FrozenInstanceError, replace

    setup, reservation = _prepared_fixture(tmp_path, monkeypatch)
    inputs = producer.LaunchInputs(
        *(
            setup[key]
            for key in (
                "source_root",
                "staging_root",
                "runtime_root",
                "packages_root",
                "lease_root",
                "device",
                "drivers",
                "resource",
                "wire_policy",
            )
        )
    )
    try:
        snapshot = producer._launch_snapshot(inputs, reservation)
        capture = launch.PreparationOwner()
        with pytest.raises(FrozenInstanceError):
            inputs.wire_policy = replace(inputs.wire_policy, calls=1)
        object.__setattr__(inputs, "wire_policy", replace(inputs.wire_policy, calls=1))

        def forbidden(**_kwargs):
            raise AssertionError("changed launch data must not prepare")

        with monkeypatch.context() as context:
            context.setattr(launch, "prepare", forbidden)
            with pytest.raises(ValueError):
                producer._prepare(
                    inputs,
                    reservation,
                    snapshot,
                    setup["manifest"],
                    setup["artifact_root"],
                    setup["definition"],
                    setup["tokenizer"],
                    setup["inventory_id"],
                    capture,
                )
        capture.close()
        reservation.assert_owned()
    finally:
        reservation.close()


def test_pending_preparation_retains_real_journal_until_retry(tmp_path, monkeypatch):
    """A real preparation cleanup failure keeps the real job lease until drain."""
    import shutil

    from slaif_raggedized_helper import embedding_job_journal
    from test_embedding_job_journal import plan as fixture_plan, wire

    setup, reservation = _prepared_fixture(tmp_path, monkeypatch)
    prepared = launch.prepare(**setup)
    handle = embedding_job_journal.Journal(tmp_path).own(wire(fixture_plan()))
    handle.__enter__()
    owner = producer._CleanupOwner(None, None, handle, preparation=prepared)
    original_remove = shutil.rmtree

    def fail_before_remove(*_args, **_kwargs):
        raise OSError("controlled owned capsule cleanup failure")

    try:
        with monkeypatch.context() as context:
            context.setattr(shutil, "rmtree", fail_before_remove)
            with pytest.raises(launch.LaunchRefused):
                owner.close()
        assert owner.preparation is prepared and owner.lease is handle
        assert prepared.pending
        handle.lease.assert_owned()
        assert shutil.rmtree is original_remove
        owner.close()
        assert owner.preparation is None and owner.lease is None
        reservation.assert_owned()
    finally:
        if owner.preparation is not None or owner.lease is not None:
            owner.close()
        reservation.close()


def test_before_model_authorization_refusal_is_pre_journal(journey, tmp_path, monkeypatch):  # noqa: F811
    """Fresh real planning cannot turn a refused test provider into a claim."""
    from slaif_raggedized_helper import derived_store

    args = journey[0]
    setup, reservation = _prepared_fixture(tmp_path, monkeypatch)
    inputs = producer.LaunchInputs(
        *(
            setup[key]
            for key in (
                "source_root",
                "staging_root",
                "runtime_root",
                "packages_root",
                "lease_root",
                "device",
                "drivers",
                "resource",
                "wire_policy",
            )
        )
    )
    seen = []

    def refuse(data, boundary):
        assert type(data) is bytes
        seen.append(boundary)
        return None

    def no_parent(*_args, **_kwargs):
        raise AssertionError("refused authorization must not start a GPU parent")

    try:
        with derived_store.Store(tmp_path) as store, monkeypatch.context() as context:
            context.setattr(parent.GPUEmbeddingWorker, "__init__", no_parent)
            with pytest.raises(producer.ProducerRefused) as raised:
                producer.produce(*args, inputs, reservation, store, tmp_path, refuse)
            assert raised.value.owner is None
        assert seen == ["before_model"]
        assert not (tmp_path / "embedding_job_journals").exists()
        assert not list(Path(setup["staging_root"]).iterdir())
        reservation.assert_owned()
    finally:
        reservation.close()


def test_corrupt_original_source_refuses_before_model(journey, tmp_path, monkeypatch):  # noqa: F811
    """Fresh source bytes are checked before the parent or authorization boundary."""
    from slaif_raggedized_helper import derived_store

    args, revisions = journey[:2]
    setup, reservation = _prepared_fixture(tmp_path, monkeypatch)
    inputs = producer.LaunchInputs(
        *(
            setup[key]
            for key in (
                "source_root",
                "staging_root",
                "runtime_root",
                "packages_root",
                "lease_root",
                "device",
                "drivers",
                "resource",
                "wire_policy",
            )
        )
    )
    blob = args[0].root / "blobs" / revisions[0].blob
    original = blob.read_bytes()
    calls = []
    try:
        blob.write_bytes(b"corrupt")
        with derived_store.Store(tmp_path) as store:
            with pytest.raises(producer.ProducerRefused):
                producer.produce(
                    *args,
                    inputs,
                    reservation,
                    store,
                    tmp_path,
                    lambda *_: calls.append(1) or "a" * 64,
                )
        assert calls == []
        assert not (tmp_path / "embedding_job_journals").exists()
        assert not list(Path(setup["staging_root"]).iterdir())
        reservation.assert_owned()
    finally:
        blob.write_bytes(original)
        reservation.close()


def test_actual_job_lease_collision_refuses_without_stealing(journey, tmp_path, monkeypatch):  # noqa: F811
    """A second producer cannot seize an actual live per-job lease."""
    from slaif_raggedized_helper import derived_store, embedding_job_journal

    args = journey[0]
    setup, reservation = _prepared_fixture(tmp_path, monkeypatch)
    setup.update(
        artifact_root=str(args[5]),
        manifest=args[4],
        definition=args[6],
        tokenizer=args[7],
        inventory_id=args[8],
    )
    inputs = producer.LaunchInputs(
        *(
            setup[key]
            for key in (
                "source_root",
                "staging_root",
                "runtime_root",
                "packages_root",
                "lease_root",
                "device",
                "drivers",
                "resource",
                "wire_policy",
            )
        )
    )
    preparation = launch.prepare(**setup)
    try:
        planned = plan.build(*args, preparation)
        with derived_store.Store(tmp_path) as store:
            with embedding_job_journal.Journal(tmp_path).own(planned.plan_bytes) as holder:
                original_owner = holder.owner_id

                def no_parent(*_args, **_kwargs):
                    raise AssertionError("collision must not start a parent")

                with monkeypatch.context() as context:
                    context.setattr(parent.GPUEmbeddingWorker, "__init__", no_parent)
                    with pytest.raises(producer.ProducerRefused) as refused:
                        producer.produce(
                            *args, inputs, reservation, store, tmp_path, lambda *_: "a" * 64
                        )
                assert refused.value.owner is None
                assert holder.owner_id == original_owner
                assert holder.read()[0]["events"][-1]["state"]["status"] == "PENDING"
                holder.lease.assert_owned()
                reservation.assert_owned()
    finally:
        preparation.close()
        reservation.close()


def test_journal_prereturn_descriptor_uncertainty_is_retained(journey, tmp_path, monkeypatch):  # noqa: F811
    """Actual journal pre-return close fault remains sticky; no numeric retry."""
    from slaif_raggedized_helper import derived_store, embedding_job_journal

    args = journey[0]
    setup, reservation = _prepared_fixture(tmp_path, monkeypatch)
    inputs = producer.LaunchInputs(
        *(
            setup[key]
            for key in (
                "source_root",
                "staging_root",
                "runtime_root",
                "packages_root",
                "lease_root",
                "device",
                "drivers",
                "resource",
                "wire_policy",
            )
        )
    )
    original_close = os.close
    target = []
    attempts = []

    def fail_initial_commit(handle, _envelope, _revision):
        target.append(handle.dirfd)
        raise OSError("controlled journal initialization error")

    def fail_one_close(fd):
        if target and fd == target[0]:
            attempts.append(fd)
            raise OSError("controlled pre-close fault")
        return original_close(fd)

    try:
        with derived_store.Store(tmp_path) as store, monkeypatch.context() as context:
            context.setattr(embedding_job_journal._Owned, "_commit", fail_initial_commit)
            context.setattr(os, "close", fail_one_close)
            with pytest.raises(producer.ProducerRefused) as raised:
                producer.produce(*args, inputs, reservation, store, tmp_path, lambda *_: "a" * 64)
            assert raised.value.pending and raised.value.owner is not None
            assert len(attempts) == 1
            with pytest.raises(producer.ProducerRefused):
                raised.value.owner.close()
            assert len(attempts) == 1
        # The intentionally unresolved descriptor is left to this owned test process's exit;
        # its number is never retried or treated as proof of a retained lock.
        reservation.assert_owned()
    finally:
        reservation.close()


def _generate_split_fixture(journey_data):
    """Persist only owned fixture data; live store objects do not cross processes."""
    import base64

    target = os.environ.get("SLAIF_PRODUCER_SPLIT_ROOT")
    if not target:
        raise RuntimeError("explicit private split-fixture root required")
    args = journey_data[0]
    encode = lambda data: base64.b64encode(data).decode("ascii")  # noqa: E731
    record = {
        "source_root": str(args[0].root),
        "metadata": encode(args[1]),
        "members": [[name, encode(data)] for name, data in args[2]],
        "ids": args[3],
        "manifest": encode(args[4]),
        "artifact_root": str(args[5]),
        "definition": args[6].model_dump(mode="json"),
        "token": {
            "sha256": args[7].sha256,
            "backend_version": args[7].backend_version,
            "role": args[7].role,
            "model_revision": args[7].model_revision,
            "preprocessing": args[7].preprocessing,
        },
        "inventory": args[8],
        "runtime": {
            "root": str(args[9].root),
            "packages": str(args[9].packages),
            "python": args[9].python,
        },
    }
    path = Path(target) / "fixture.json"
    path.write_text(json.dumps(record, sort_keys=True))
    print("split_fixture_sha256=" + hashlib.sha256(path.read_bytes()).hexdigest())


def _produce_split_fixture(tmp_path, monkeypatch):
    """Fresh process opens stores and creates its own reservation and preparations."""
    import base64

    from slaif_raggedized_helper import native_tokenizers, schema, source_admission

    root = os.environ.get("SLAIF_PRODUCER_SPLIT_ROOT")
    if not root:
        raise RuntimeError("explicit private split-fixture root required")
    data = json.loads((Path(root) / "fixture.json").read_bytes())
    decode = lambda value: base64.b64decode(value, validate=True)  # noqa: E731
    artifact_root = Path(data["artifact_root"])
    definition = schema.EmbeddingDefinition.model_validate(data["definition"], strict=True)
    token = native_tokenizers.Definition(artifact_root / "tokenizer.json", **data["token"])
    runtime = native_tokenizers.Runtime(
        Path(data["runtime"]["root"]), Path(data["runtime"]["packages"]), data["runtime"]["python"]
    )
    source = source_admission.OriginalStore(Path(data["source_root"]))
    try:
        args = (
            source,
            decode(data["metadata"]),
            tuple((name, decode(value)) for name, value in data["members"]),
            data["ids"],
            decode(data["manifest"]),
            artifact_root,
            definition,
            token,
            data["inventory"],
            runtime,
        )
        mode = os.environ.get("SLAIF_PRODUCER_TEST_MODE")
        measure_only = os.environ.get("SLAIF_PRODUCER_MEASURE_BEFORE_ENCODE") == "1"
        _one_batch_scenario((args,), tmp_path, monkeypatch, mode or measure_only)
    finally:
        source.close()


def test_invalid_config_after_prepare_drains_actual_owner(tmp_path, monkeypatch):
    """A post-return invalid mutation cannot strand a real prepared capsule."""
    setup, reservation = _prepared_fixture(tmp_path, monkeypatch)
    inputs = producer.LaunchInputs(
        *(
            setup[key]
            for key in (
                "source_root",
                "staging_root",
                "runtime_root",
                "packages_root",
                "lease_root",
                "device",
                "drivers",
                "resource",
                "wire_policy",
            )
        )
    )
    snapshot = producer._launch_snapshot(inputs, reservation)
    capture = launch.PreparationOwner()
    original = launch.prepare
    returned = []

    def prepare_then_invalidate(**kwargs):
        result = original(**kwargs)
        returned.append(result)
        object.__setattr__(inputs, "source_root", "relative")
        return result

    try:
        with monkeypatch.context() as context:
            context.setattr(launch, "prepare", prepare_then_invalidate)
            with pytest.raises(ValueError):
                producer._prepare(
                    inputs,
                    reservation,
                    snapshot,
                    setup["manifest"],
                    setup["artifact_root"],
                    setup["definition"],
                    setup["tokenizer"],
                    setup["inventory_id"],
                    capture,
                )
        assert len(returned) == 1 and capture.prepared is returned[0]
        cleanup = producer._CleanupOwner(None, None, None, capture=capture)
        cleanup.close()
        assert returned[0]._closed and not returned[0].pending
        assert not list(Path(setup["staging_root"]).iterdir())
        reservation.assert_owned()
    finally:
        if returned and not returned[0]._closed:
            returned[0].close()
        reservation.close()


def test_invalid_post_prepare_cleanup_fault_retains_real_owner(tmp_path, monkeypatch):
    """A failed owned cleanup remains attributable and can use its supported retry."""
    import shutil

    setup, reservation = _prepared_fixture(tmp_path, monkeypatch)
    inputs = producer.LaunchInputs(
        *(
            setup[key]
            for key in (
                "source_root",
                "staging_root",
                "runtime_root",
                "packages_root",
                "lease_root",
                "device",
                "drivers",
                "resource",
                "wire_policy",
            )
        )
    )
    snapshot = producer._launch_snapshot(inputs, reservation)
    capture = launch.PreparationOwner()
    original = launch.prepare
    returned = []

    def prepare_then_invalidate(**kwargs):
        result = original(**kwargs)
        returned.append(result)
        object.__setattr__(inputs, "source_root", "relative")
        return result

    def refuse_remove(*_args, **_kwargs):
        raise OSError("controlled pre-removal failure")

    owner = None
    try:
        with monkeypatch.context() as context:
            context.setattr(launch, "prepare", prepare_then_invalidate)
            context.setattr(shutil, "rmtree", refuse_remove)
            with pytest.raises(ValueError):
                producer._prepare(
                    inputs,
                    reservation,
                    snapshot,
                    setup["manifest"],
                    setup["artifact_root"],
                    setup["definition"],
                    setup["tokenizer"],
                    setup["inventory_id"],
                    capture,
                )
            assert len(returned) == 1 and capture.prepared is returned[0]
            owner = producer._CleanupOwner(None, None, None, capture=capture)
            with pytest.raises(launch.LaunchRefused):
                owner.close()
            assert owner.preparation is returned[0] and owner.capture is capture
        owner.close()
        assert owner.preparation is None and owner.capture is None and not returned[0].pending
        reservation.assert_owned()
    finally:
        if owner is not None and owner.preparation is not None:
            owner.close()
        reservation.close()


from test_isolated_gpu_embedding_composition import owned_parent  # noqa: E402, F401


def test_owned_gpu_encode_cpu_boundary(owned_parent):  # noqa: F811
    """Measure one actual guarded synthetic encode, not a durable-batch proof."""
    from slaif_raggedized_helper import embedding_vectors

    worker, runtime, reservation = owned_parent
    started = time.process_time()
    with bridge.GPUTextEmbeddingSession(worker, runtime) as session:
        print(f"owned_session_init_cpu={time.process_time() - started:.3f}", flush=True)
        start_encode = time.process_time()
        encoded = bridge.GPUTextEmbeddingSession.encode(session, ("hello", "café"))
        print(f"owned_encode_cpu={time.process_time() - start_encode:.3f}", flush=True)
        assert type(encoded) is bridge.EncodedBatch
        assert type(encoded.vectors) is embedding_vectors.NormalizedVectors
        assert [receipt.count for receipt in encoded.receipts] == [3, 3]
        assert encoded.receipts[0].nonce != encoded.receipts[1].nonce
        assert encoded.receipts[0].ids != encoded.receipts[1].ids
        assert len(encoded.vectors.rows) == 2
    reservation.assert_owned()


def _reuse_split_fixture(tmp_path, monkeypatch):
    """Reopen durable files in a new process with newly owned handles."""
    import base64
    import math
    import struct

    from slaif_raggedized_helper import derived_store, native_tokenizers, schema, source_admission

    split_root = Path(os.environ["SLAIF_PRODUCER_SPLIT_ROOT"])
    data = json.loads((split_root / "fixture.json").read_bytes())
    success = json.loads((split_root / "success.json").read_bytes())
    decode = lambda value: base64.b64decode(value, validate=True)  # noqa: E731
    artifact = Path(data["artifact_root"])
    definition = schema.EmbeddingDefinition.model_validate(data["definition"], strict=True)
    token = native_tokenizers.Definition(artifact / "tokenizer.json", **data["token"])
    runtime = native_tokenizers.Runtime(
        Path(data["runtime"]["root"]), Path(data["runtime"]["packages"]), data["runtime"]["python"]
    )
    source = source_admission.OriginalStore(Path(data["source_root"]))
    setup, reservation = _prepared_fixture(tmp_path, monkeypatch)
    inputs = producer.LaunchInputs(
        *(
            setup[key]
            for key in (
                "source_root",
                "staging_root",
                "runtime_root",
                "packages_root",
                "lease_root",
                "device",
                "drivers",
                "resource",
                "wire_policy",
            )
        )
    )
    seen = []
    plan_bytes = []

    def allow(data_bytes, boundary):
        assert type(data_bytes) is bytes
        seen.append(boundary)
        plan_bytes.append(data_bytes)
        return "a" * 64

    def no_parent(*_args, **_kwargs):
        raise AssertionError("reuse cannot start a GPU parent")

    try:
        with derived_store.Store(Path(success["state_root"])) as store:
            with monkeypatch.context() as context:
                context.setattr(parent.GPUEmbeddingWorker, "__init__", no_parent)
                start = time.process_time()
                result = producer.produce(
                    source,
                    decode(data["metadata"]),
                    tuple((name, decode(value)) for name, value in data["members"]),
                    success["ids"],
                    decode(success["manifest"]),
                    artifact,
                    definition,
                    token,
                    success["inventory"],
                    runtime,
                    inputs,
                    reservation,
                    store,
                    Path(success["state_root"]),
                    allow,
                )
                print(f"reuse_call_cpu={time.process_time() - start:.3f}", flush=True)
            assert result.reused and result.job_id == success["job_id"]
            assert result.output_ref == success["output_ref"]
            assert hashlib.sha256(result.metadata).hexdigest() == success["metadata_sha256"]
            assert (
                hashlib.sha256(result.execution_record).hexdigest() == success["execution_sha256"]
            )
            assert (
                hashlib.sha256(result.native_runtime_record).hexdigest() == success["native_sha256"]
            )
            assert seen == ["before_model", "before_reuse"]
            assert store.load(result.output_ref[7:]).manifest
            assert plan_bytes[0] == plan_bytes[1]
            metadata_obj = json.loads(result.metadata)
            matrix = result.batch.matrix
            assert not matrix.flags.writeable
            assert (
                hashlib.sha256(matrix.tobytes(order="C")).hexdigest()
                == metadata_obj["vector_payload_sha256"]
            )
            # This private fake emits [CLS token ID, receipt length, 0, ...];
            # its test tokenizer has CLS=1. Compare an independently packed FP32 row.
            token_count = metadata_obj["rows"][0]["token_count"]
            magnitude = math.sqrt(1.0 + float(token_count) ** 2)
            expected = struct.pack(
                "<1024f", 1.0 / magnitude, token_count / magnitude, *([0.0] * 1022)
            )
            assert matrix.tobytes(order="C") == expected
            evidence = split_root / "verified-evidence-expected-vector"
            evidence.mkdir(mode=0o700)
            for name, payload in (
                ("plan.json", plan_bytes[0]),
                ("metadata.json", result.metadata),
                ("execution.json", result.execution_record),
                ("native.json", result.native_runtime_record),
            ):
                (evidence / name).write_bytes(payload)
                print(name + "_sha256=" + hashlib.sha256(payload).hexdigest(), flush=True)
            assert not list(Path(setup["staging_root"]).iterdir())
            reservation.assert_owned()
            print("reuse_job_id=" + result.job_id, flush=True)
            print("reuse_output_ref=" + result.output_ref, flush=True)
    finally:
        source.close()
        reservation.close()


def test_capture_a_actual_pre_return_fault_retains_operation(journey, tmp_path, monkeypatch):  # noqa: F811
    """Actual failed A remains associated even when exception attributes are hostile."""
    import shutil

    from slaif_raggedized_helper import derived_store

    args = journey[0]
    setup, reservation = _prepared_fixture(tmp_path, monkeypatch)
    inputs = producer.LaunchInputs(
        *(
            setup[key]
            for key in (
                "source_root",
                "staging_root",
                "runtime_root",
                "packages_root",
                "lease_root",
                "device",
                "drivers",
                "resource",
                "wire_policy",
            )
        )
    )
    original_revalidate = launch.PreparedLaunch.revalidate
    actual_attach = producer._attach_owner
    captured = []

    class Hostile(BaseException):
        def __setattr__(self, _name, _value):
            raise RuntimeError("no exception annotation")

    interrupt = Hostile()

    def fail_after_admission(prepared):
        original_revalidate(prepared)
        raise interrupt

    def refuse_remove(*_args, **_kwargs):
        raise OSError("controlled capsule cleanup refusal")

    def observe_attach(error, owner):
        captured.append((error, owner))
        return actual_attach(error, owner)

    cleanup = None
    try:
        with derived_store.Store(tmp_path) as store:
            with monkeypatch.context() as context:
                context.setattr(launch.PreparedLaunch, "revalidate", fail_after_admission)
                context.setattr(shutil, "rmtree", refuse_remove)
                context.setattr(producer, "_attach_owner", observe_attach)
                with pytest.raises(Hostile) as raised:
                    producer.produce(
                        *args, inputs, reservation, store, tmp_path, lambda *_: "a" * 64
                    )
                assert raised.value is interrupt
                assert len(captured) == 1 and captured[0][0] is interrupt
                cleanup = captured[0][1]
                assert type(cleanup.capture) is launch.PreparationOwner
                assert cleanup.capture.pending and cleanup.capture.prepared is None
                assert cleanup.worker is None and cleanup.session is None and cleanup.lease is None
            cleanup.close()
            assert cleanup.capture is None and not list(Path(setup["staging_root"]).iterdir())
            reservation.assert_owned()
    finally:
        if cleanup is not None and cleanup.capture is not None:
            cleanup.close()
        reservation.close()


def test_capture_a_interrupted_actual_return_recovers_same_handoff(journey, tmp_path, monkeypatch):  # noqa: F811
    """Trace interruption at actual successful return; no child has started."""
    import inspect
    import sys

    from slaif_raggedized_helper import derived_store

    args = journey[0]
    setup, reservation = _prepared_fixture(tmp_path, monkeypatch)
    inputs = producer.LaunchInputs(
        *(
            setup[key]
            for key in (
                "source_root",
                "staging_root",
                "runtime_root",
                "packages_root",
                "lease_root",
                "device",
                "drivers",
                "resource",
                "wire_policy",
            )
        )
    )
    lines, first = inspect.getsourcelines(launch.prepare)
    targets = [first + i for i, line in enumerate(lines) if line.strip() == "return result"]
    assert len(targets) == 1
    observed = []
    interrupt = KeyboardInterrupt("controlled actual handoff return")

    def trace(frame, event, _arg):
        if (
            frame.f_code is launch.prepare.__code__
            and event == "line"
            and frame.f_lineno == targets[0]
        ):
            observed.append((frame.f_locals["preparation_owner"], frame.f_locals["result"]))
            raise interrupt
        return trace

    try:
        with derived_store.Store(tmp_path) as store:
            sys.settrace(trace)
            try:
                with pytest.raises(KeyboardInterrupt) as raised:
                    producer.produce(
                        *args, inputs, reservation, store, tmp_path, lambda *_: "a" * 64
                    )
            finally:
                sys.settrace(None)
            assert raised.value is interrupt and len(observed) == 1
            capture, prepared = observed[0]
            assert type(capture) is launch.PreparationOwner
            assert capture.prepared is prepared and prepared._closed and not capture.pending
            assert not list(Path(setup["staging_root"]).iterdir())
            assert not (tmp_path / "embedding_job_journals").exists()
            reservation.assert_owned()
    finally:
        sys.settrace(None)
        reservation.close()


def test_capture_b_failure_holds_actual_journal_until_drained(tmp_path, monkeypatch):
    """B-style no-child capture fault with an actual held journal lease."""
    import shutil

    from slaif_raggedized_helper import embedding_job_journal
    from test_embedding_job_journal import plan as fixture_plan, wire

    setup, reservation = _prepared_fixture(tmp_path, monkeypatch)
    inputs = producer.LaunchInputs(
        *(
            setup[key]
            for key in (
                "source_root",
                "staging_root",
                "runtime_root",
                "packages_root",
                "lease_root",
                "device",
                "drivers",
                "resource",
                "wire_policy",
            )
        )
    )
    snapshot = producer._launch_snapshot(inputs, reservation)
    capture = launch.PreparationOwner()
    handle = embedding_job_journal.Journal(tmp_path).own(wire(fixture_plan()))
    handle.__enter__()
    cleanup = producer._CleanupOwner(None, None, handle, capture=capture)
    original = launch.PreparedLaunch.revalidate

    def fail_after_admission(prepared):
        original(prepared)
        raise ValueError("controlled B admission failure")

    def refuse_remove(*_args, **_kwargs):
        raise OSError("controlled B capsule cleanup refusal")

    try:
        with monkeypatch.context() as context:
            context.setattr(launch.PreparedLaunch, "revalidate", fail_after_admission)
            context.setattr(shutil, "rmtree", refuse_remove)
            with pytest.raises(launch.LaunchRefused):
                producer._prepare(
                    inputs,
                    reservation,
                    snapshot,
                    setup["manifest"],
                    setup["artifact_root"],
                    setup["definition"],
                    setup["tokenizer"],
                    setup["inventory_id"],
                    capture,
                )
            assert capture.prepared is None and capture.pending
            with pytest.raises(launch.LaunchRefused):
                cleanup.close()
            assert cleanup.capture is capture and cleanup.lease is handle
            handle.lease.assert_owned()
        cleanup.close()
        assert cleanup.capture is None and cleanup.lease is None
        reservation.assert_owned()
    finally:
        if cleanup.capture is not None or cleanup.lease is not None:
            cleanup.close()
        reservation.close()


def test_capture_b_interrupted_return_recovers_actual_handoff_and_lease(tmp_path, monkeypatch):
    """A B-style no-child handoff interruption preserves its held real journal."""
    import inspect
    import sys

    from slaif_raggedized_helper import embedding_job_journal
    from test_embedding_job_journal import plan as fixture_plan, wire

    setup, reservation = _prepared_fixture(tmp_path, monkeypatch)
    inputs = producer.LaunchInputs(
        *(
            setup[key]
            for key in (
                "source_root",
                "staging_root",
                "runtime_root",
                "packages_root",
                "lease_root",
                "device",
                "drivers",
                "resource",
                "wire_policy",
            )
        )
    )
    snapshot = producer._launch_snapshot(inputs, reservation)
    capture = launch.PreparationOwner()
    handle = embedding_job_journal.Journal(tmp_path).own(wire(fixture_plan()))
    handle.__enter__()
    cleanup = producer._CleanupOwner(None, None, handle, capture=capture)
    lines, first = inspect.getsourcelines(launch.prepare)
    targets = [first + index for index, line in enumerate(lines) if line.strip() == "return result"]
    assert len(targets) == 1
    interrupt = KeyboardInterrupt("controlled B handoff return")
    observed = []

    def trace(frame, event, _arg):
        if (
            frame.f_code is launch.prepare.__code__
            and event == "line"
            and frame.f_lineno == targets[0]
        ):
            observed.append((frame.f_locals["preparation_owner"], frame.f_locals["result"]))
            raise interrupt
        return trace

    try:
        sys.settrace(trace)
        try:
            with pytest.raises(KeyboardInterrupt) as raised:
                producer._prepare(
                    inputs,
                    reservation,
                    snapshot,
                    setup["manifest"],
                    setup["artifact_root"],
                    setup["definition"],
                    setup["tokenizer"],
                    setup["inventory_id"],
                    capture,
                )
        finally:
            sys.settrace(None)
        assert raised.value is interrupt and len(observed) == 1
        assert observed[0][0] is capture and capture.prepared is observed[0][1]
        assert capture.pending and cleanup.lease is handle
        handle.lease.assert_owned()
        cleanup.close()
        assert cleanup.capture is None and cleanup.lease is None
        assert observed[0][1]._closed and not capture.pending
        reservation.assert_owned()
    finally:
        sys.settrace(None)
        if cleanup.capture is not None or cleanup.lease is not None:
            cleanup.close()
        reservation.close()


def test_forked_cleanup_cannot_release_actual_capture_or_journal(tmp_path, monkeypatch):
    """A child cannot drain creator-owned preparation or release its job lease."""
    from slaif_raggedized_helper import embedding_job_journal
    from test_embedding_job_journal import plan as fixture_plan, wire

    setup, reservation = _prepared_fixture(tmp_path, monkeypatch)
    capture = launch.PreparationOwner()
    prepared = launch.prepare(**setup, preparation_owner=capture)
    handle = embedding_job_journal.Journal(tmp_path).own(wire(fixture_plan()))
    handle.__enter__()
    owner = producer._CleanupOwner(None, None, handle, preparation=prepared, capture=capture)
    read_fd, write_fd = os.pipe()
    child = os.fork()
    if child == 0:
        os.close(read_fd)
        try:
            owner.close()
        except producer.ProducerRefused:
            os.write(write_fd, b"R")
        finally:
            os.close(write_fd)
            os._exit(0)
    os.close(write_fd)
    try:
        assert os.read(read_fd, 1) == b"R"
        assert os.waitstatus_to_exitcode(os.waitpid(child, 0)[1]) == 0
        assert capture.prepared is prepared and capture.pending
        prepared.revalidate()
        handle.lease.assert_owned()
        reservation.assert_owned()
        owner.close()
        assert not capture.pending and owner.lease is None
    finally:
        os.close(read_fd)
        if owner.capture is not None or owner.lease is not None:
            owner.close()
        reservation.close()


def test_busy_capture_keeps_actual_journal_and_preparation(tmp_path, monkeypatch):
    """A busy exact capture cannot release the real journal or its preparation."""
    from slaif_raggedized_helper import embedding_job_journal
    from test_embedding_job_journal import plan as fixture_plan, wire

    setup, reservation = _prepared_fixture(tmp_path, monkeypatch)
    capture = launch.PreparationOwner()
    prepared = launch.prepare(**setup, preparation_owner=capture)
    handle = embedding_job_journal.Journal(tmp_path).own(wire(fixture_plan()))
    handle.__enter__()
    owner = producer._CleanupOwner(None, None, handle, capture=capture)
    lock = launch.PreparationOwner._record(capture)[3]
    try:
        assert lock.acquire(blocking=False)
        try:
            with pytest.raises(launch.LaunchRefused):
                owner.close()
            assert owner.capture is capture and owner.lease is handle
            assert prepared.pending and not prepared._closed
            handle.lease.assert_owned()
            reservation.assert_owned()
        finally:
            lock.release()
        owner.close()
        assert owner.capture is None and owner.lease is None
        assert prepared._closed and not capture.pending
        reservation.assert_owned()
    finally:
        if owner.capture is not None or owner.lease is not None:
            owner.close()
        reservation.close()
