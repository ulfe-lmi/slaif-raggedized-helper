"""Actual source and pre-dispatch checks; no simulated producer success."""

from dataclasses import replace

import pytest

from slaif_raggedized_helper import corpus_embedding_executor as executor
from slaif_raggedized_helper import corpus_embedding_program as program
from slaif_raggedized_helper import derived_store, ingestion_store
from slaif_raggedized_helper import gpu_embedding_producer as producer
from slaif_raggedized_helper import gpu_worker_protocol as wire
from test_embedding_batch_plan_composition import journey  # noqa: F401
from test_gpu_worker_launch import _prepared_fixture


def test_actual_whole_program_rowfit_refuses_before_dispatch(journey, tmp_path, monkeypatch):  # noqa: F811
    import hashlib
    import sys
    import types
    from pathlib import Path

    args = journey[0]
    setup, reservation = _prepared_fixture(tmp_path, monkeypatch)
    inputs = producer.LaunchInputs(
        *(
            setup[k]
            for k in (
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
    inputs = replace(inputs, wire_policy=wire.Policy(max_rows=1))
    path = tmp_path / "corpus-derived"
    path.mkdir(mode=0o700)
    try:
        with derived_store.Store(path) as derived:
            ident = ingestion_store.publish(args[0], derived, args[1], args[2])
            selected = program.build(args[0], derived, (ident,))
            assert any(len(b.chunk_ids) > 1 for b in selected.batches)

            class ReachedProducer(Exception):
                pass

            def stop_at_entry(*_args, **_kwargs):
                raise ReachedProducer()

            monkeypatch.setattr(producer, "produce", stop_at_entry)
            call = (
                args[0],
                derived,
                selected.program_bytes,
                args[4],
                args[5],
                args[6],
                args[7],
                args[8],
                args[9],
                inputs,
                reservation,
                tmp_path,
                lambda *_: "a" * 64,
            )
            with pytest.raises(executor.ExecutorRefused):
                executor.run(*call, deadline_ms=120000)
            # Private in-memory control removes only the whole-program row-fit guard.
            # It reaches the entry sentinel, never a simulated producer result.
            source = Path(executor.__file__).read_text()
            needle = (
                "if any(\n        len(batch.chunk_ids) > launch_inputs.wire_policy.max_rows "
                "for batch in validated.batches\n    ):"
            )
            assert source.count(needle) == 1
            control_source = source.replace(needle, "if False:")
            module = types.ModuleType("slaif_raggedized_helper._executor_rowfit_control")
            module.__package__ = "slaif_raggedized_helper"
            sys.modules[module.__name__] = module
            try:
                exec(compile(control_source, "<rowfit control>", "exec"), module.__dict__)
                with pytest.raises(ReachedProducer):
                    module.run(*call, deadline_ms=120000)
            finally:
                del sys.modules[module.__name__]
            with pytest.raises(executor.ExecutorRefused):
                executor.run(*call, deadline_ms=120000)
            print("rowfit_control_sha256=" + hashlib.sha256(control_source.encode()).hexdigest())
            reservation.assert_owned()
    finally:
        reservation.close()


def _prepare_proof_data(journey, target):  # noqa: F811
    """Persist source fixture data, never live authority objects, for creator processes."""
    import base64
    import json
    from slaif_raggedized_helper import embedding_artifacts, retrieval_representation
    from test_embedding_artifacts import write_config

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
    raw = json.dumps(manifest).encode()
    inventory = embedding_artifacts.verify_artifacts(raw, args[5]).inventory_id
    state = target / "state"
    state.mkdir(mode=0o700)
    with derived_store.Store(state) as derived:
        ident = ingestion_store.publish(args[0], derived, args[1], args[2])
        loaded = ingestion_store.load(args[0], derived, ident)
        count = len(loaded.chunks)
        assert 2 <= count <= 16
        policy = retrieval_representation.BatchPolicy(max_items=(count + 1) // 2)
        selected = program.build(args[0], derived, (ident,), batch_policy=policy)
        assert selected.batch_count == 2 and selected.row_count == count
        (target / "program.json").write_bytes(selected.program_bytes)
    data = {
        "source_root": str(args[0].root),
        "state": str(state),
        "artifact_root": str(args[5]),
        "manifest": base64.b64encode(raw).decode(),
        "inventory": inventory,
        "definition": args[6].model_dump(mode="json"),
        "token": {
            "sha256": args[7].sha256,
            "backend_version": args[7].backend_version,
            "role": args[7].role,
            "model_revision": args[7].model_revision,
            "preprocessing": args[7].preprocessing,
        },
        "runtime": {
            "root": str(args[9].root),
            "packages": str(args[9].packages),
            "python": args[9].python,
        },
        "rows": count,
        "batches": selected.batch_count,
    }
    (target / "fixture.json").write_text(json.dumps(data, sort_keys=True))
    print(f"proof_rows={count} proof_batches={selected.batch_count}", flush=True)


def _actual_creator_phase(tmp_path, monkeypatch):
    """Run the real producer; only the isolated synthetic backend is substituted."""
    import base64
    import hashlib
    import json
    import os
    from pathlib import Path
    import subprocess

    from slaif_raggedized_helper import embedding_job_journal, native_tokenizers, schema
    from slaif_raggedized_helper import gpu_embedding_worker, source_admission

    root = Path(os.environ["SLAIF_CORPUS_PROOF_ROOT"])
    phase = os.environ["SLAIF_CORPUS_PROOF_PHASE"]
    assert phase in ("stop", "resume")
    data = json.loads((root / "fixture.json").read_bytes())
    artifact = Path(data["artifact_root"])
    definition = schema.EmbeddingDefinition.model_validate(data["definition"], strict=True)
    token = native_tokenizers.Definition(artifact / "tokenizer.json", **data["token"])
    runtime = native_tokenizers.Runtime(
        Path(data["runtime"]["root"]), Path(data["runtime"]["packages"]), data["runtime"]["python"]
    )
    originals = source_admission.OriginalStore(Path(data["source_root"]))
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
    descriptors, starts, plans, boundaries = [], [], [], []
    original_popen = subprocess.Popen.__init__

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
            print("harness_sha256=" + hashlib.sha256(harness).hexdigest(), flush=True)
            path = tmp_path / f"harness-{len(starts)}.py"
            path.write_bytes(harness)
            path.chmod(0o400)
            fd = os.open(path, os.O_RDONLY | os.O_CLOEXEC)
            descriptors.append(fd)
            argv[index - 1] = f"/proc/self/fd/{fd}"
            kwargs["pass_fds"] = tuple(
                fd if item == old_fd else item for item in kwargs["pass_fds"]
            )
        return original_popen(process, argv, **kwargs)

    def authorize(plan_bytes, boundary):
        plans.append(plan_bytes)
        boundaries.append(boundary)
        return "a" * 64

    class StopBeforeNext(BaseException):
        pass

    real_check = executor._check

    def stop_after_return(end):
        real_check(end)
        if boundaries and boundaries[-1] == "before_complete":
            raise StopBeforeNext()

    monkeypatch.setattr(subprocess.Popen, "__init__", intercept)
    if phase == "stop":
        monkeypatch.setattr(executor, "_check", stop_after_return)
    try:
        with derived_store.Store(Path(data["state"])) as derived:
            args = (
                originals,
                derived,
                (root / "program.json").read_bytes(),
                base64.b64decode(data["manifest"], validate=True),
                artifact,
                definition,
                token,
                data["inventory"],
                runtime,
                inputs,
                reservation,
                Path(data["state"]),
                authorize,
            )
            if phase == "stop":
                with pytest.raises(StopBeforeNext):
                    executor.run(*args, deadline_ms=180000)
                assert starts == [1]
                assert boundaries == [
                    "before_model",
                    "before_encode",
                    "before_publish",
                    "before_complete",
                ]
                with embedding_job_journal.Journal(Path(data["state"])).own(plans[-1]) as handle:
                    current = handle.read()[0]["events"][-1]["state"]
                    assert current["status"] == "COMPLETE"
                    first = {"job_id": current["job_id"], "output_ref": current["output"]["ref"]}
                (root / "first.json").write_text(json.dumps(first, sort_keys=True))
                print("first_complete=" + json.dumps(first, sort_keys=True), flush=True)
            else:
                first = json.loads((root / "first.json").read_bytes())
                result = executor.run(*args, deadline_ms=180000)
                assert result.row_count == data["rows"] and len(result.completions) == 2
                assert [c.reused for c in result.completions] == [True, False]
                assert result.completions[0].job_id == first["job_id"]
                assert result.completions[0].output_ref == first["output_ref"]
                assert starts == [1]
                assert boundaries == [
                    "before_model",
                    "before_reuse",
                    "before_model",
                    "before_encode",
                    "before_publish",
                    "before_complete",
                ]
                monkeypatch.setattr(
                    gpu_embedding_worker.GPUEmbeddingWorker,
                    "__init__",
                    lambda *_a, **_k: pytest.fail("reuse started GPU parent"),
                )
                before = len(starts)
                again = executor.run(*args, deadline_ms=180000)
                assert len(starts) == before and all(c.reused for c in again.completions)
                assert [(c.job_id, c.output_ref, c.metadata_sha256) for c in again.completions] == [
                    (c.job_id, c.output_ref, c.metadata_sha256) for c in result.completions
                ]
                assert (
                    again.execution_record,
                    again.native_runtime_record,
                    again.execution_fingerprint,
                ) == (
                    result.execution_record,
                    result.native_runtime_record,
                    result.execution_fingerprint,
                )
                print("completions=" + repr(result.completions), flush=True)
                print("execution_sha256=" + hashlib.sha256(result.execution_record).hexdigest())
                print("native_sha256=" + hashlib.sha256(result.native_runtime_record).hexdigest())
            reservation.assert_owned()
    finally:
        for fd in descriptors:
            os.close(fd)
        reservation.close()
        originals.close()


def test_actual_changed_source_refuses_before_producer(journey, tmp_path, monkeypatch):  # noqa: F811
    import json

    args, revisions = journey[:2]
    setup, reservation = _prepared_fixture(tmp_path, monkeypatch)
    inputs = producer.LaunchInputs(
        *(
            setup[k]
            for k in (
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
    path = tmp_path / "corpus-derived"
    path.mkdir(mode=0o700)
    try:
        with derived_store.Store(path) as derived:
            ident = ingestion_store.publish(args[0], derived, args[1], args[2])
            selected = program.build(args[0], derived, (ident,))
            blob = tmp_path / "store" / "blobs" / revisions[0].blob
            old = blob.read_bytes()
            blob.write_bytes(old + b"corrupt")
            monkeypatch.setattr(producer, "produce", lambda *a, **k: pytest.fail("dispatched"))
            try:
                with pytest.raises(program.ProgramError):
                    executor.run(
                        args[0],
                        derived,
                        selected.program_bytes,
                        args[4],
                        args[5],
                        args[6],
                        args[7],
                        args[8],
                        args[9],
                        inputs,
                        reservation,
                        tmp_path,
                        lambda *_: "a" * 64,
                        deadline_ms=120000,
                    )
            finally:
                blob.write_bytes(old)
            assert program.validate(args[0], derived, selected.program_bytes) == selected
            doc = json.loads(selected.program_bytes)
            removed = doc["rows"].pop()
            doc["sources"][-1]["row_count"] -= 1
            last = doc["batches"][-1]
            last["row_count"] -= 1
            last["total_codepoints"] -= removed["codepoints"]
            last["total_native_request_bytes"] -= removed["native_request_bytes"]
            candidate = program._encode(doc)
            assert program.parse(candidate).row_count == selected.row_count - 1
            with pytest.raises(program.ProgramError):
                executor.run(
                    args[0],
                    derived,
                    candidate,
                    args[4],
                    args[5],
                    args[6],
                    args[7],
                    args[8],
                    args[9],
                    inputs,
                    reservation,
                    tmp_path,
                    lambda *_: "a" * 64,
                    deadline_ms=120000,
                )
            reservation.assert_owned()
    finally:
        reservation.close()


def test_actual_changed_launch_after_validation_refuses_before_producer(
    journey,  # noqa: F811
    tmp_path,
    monkeypatch,
):
    args = journey[0]
    setup, reservation = _prepared_fixture(tmp_path, monkeypatch)
    inputs = producer.LaunchInputs(
        *(
            setup[k]
            for k in (
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
    path = tmp_path / "corpus-derived"
    path.mkdir(mode=0o700)
    try:
        with derived_store.Store(path) as derived:
            ident = ingestion_store.publish(args[0], derived, args[1], args[2])
            selected = program.build(args[0], derived, (ident,))
            original_validate = program.validate

            def mutate_after_validate(*a):
                result = original_validate(*a)
                object.__setattr__(inputs.wire_policy, "calls", 1)
                return result

            monkeypatch.setattr(program, "validate", mutate_after_validate)
            monkeypatch.setattr(producer, "produce", lambda *a, **k: pytest.fail("dispatched"))
            with pytest.raises(executor.ExecutorRefused):
                executor.run(
                    args[0],
                    derived,
                    selected.program_bytes,
                    args[4],
                    args[5],
                    args[6],
                    args[7],
                    args[8],
                    args[9],
                    inputs,
                    reservation,
                    tmp_path,
                    lambda *_: "a" * 64,
                    deadline_ms=120000,
                )
            reservation.assert_owned()
    finally:
        reservation.close()


def test_actual_complete_resume_driver(request, tmp_path, monkeypatch):
    """One driver runs two creator-owned phases; the ordinary suite needs no special env."""
    import os
    from pathlib import Path
    import resource
    import subprocess
    import sys
    import time

    phase = os.environ.get("SLAIF_CORPUS_PROOF_PHASE")
    if phase:
        for kind, ceiling in ((resource.RLIMIT_CPU, 120), (resource.RLIMIT_AS, 1073741824)):
            soft, hard = resource.getrlimit(kind)
            limit = min(ceiling, *(x for x in (soft, hard) if x != resource.RLIM_INFINITY))
            resource.setrlimit(kind, (limit, hard))
        _actual_creator_phase(tmp_path, monkeypatch)
        return
    start = time.monotonic()
    before = resource.getrusage(resource.RUSAGE_CHILDREN)
    own_before = resource.getrusage(resource.RUSAGE_SELF)
    configured = os.environ.get("SLAIF_CORPUS_PROOF_ROOT")
    if configured:
        root = Path(configured)
    else:
        root = tmp_path / "proof"
        root.mkdir(mode=0o700)
        _prepare_proof_data(request.getfixturevalue("journey"), root)
    env = os.environ.copy()
    env["SLAIF_CORPUS_PROOF_ROOT"] = str(root)
    for name in (
        "OMP_NUM_THREADS",
        "OPENBLAS_NUM_THREADS",
        "MKL_NUM_THREADS",
        "RAYON_NUM_THREADS",
        "NUMEXPR_NUM_THREADS",
    ):
        env[name] = "1"
    selector = str(Path(__file__).resolve()) + "::test_actual_complete_resume_driver"
    for name in ("stop", "resume"):
        remaining = 180 - (time.monotonic() - start)
        assert remaining > 0
        env["SLAIF_CORPUS_PROOF_PHASE"] = name
        command = [
            sys.executable,
            "-m",
            "pytest",
            "-s",
            "-q",
            selector,
            "--basetemp=" + str(root / ("phase-" + name)),
        ]
        print("creator_command=" + repr(command), flush=True)
        subprocess.run(command, env=env, check=True, timeout=remaining)
        usage = resource.getrusage(resource.RUSAGE_CHILDREN)
        children_cpu = usage.ru_utime + usage.ru_stime - before.ru_utime - before.ru_stime
        own = resource.getrusage(resource.RUSAGE_SELF)
        own_cpu = own.ru_utime + own.ru_stime - own_before.ru_utime - own_before.ru_stime
        print(
            f"phase={name} children_cpu={children_cpu:.3f} "
            f"own_cpu={own_cpu:.3f} "
            f"wall={time.monotonic() - start:.3f}",
            flush=True,
        )
        assert children_cpu + own_cpu <= 120


def test_actual_provider_refusal_stops_before_later_batch(journey, tmp_path, monkeypatch):  # noqa: F811
    import json

    from slaif_raggedized_helper import embedding_artifacts, retrieval_representation
    from slaif_raggedized_helper import gpu_embedding_worker
    from test_embedding_artifacts import write_config

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
    inputs = producer.LaunchInputs(
        *(
            setup[k]
            for k in (
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
    path = tmp_path / "corpus-derived"
    path.mkdir(mode=0o700)
    seen = []

    def deny(plan, boundary):
        seen.append((plan, boundary))
        return "invalid-epoch"

    monkeypatch.setattr(
        gpu_embedding_worker.GPUEmbeddingWorker,
        "__init__",
        lambda *_a, **_k: pytest.fail("GPU parent started"),
    )
    try:
        with derived_store.Store(path) as derived:
            ident = ingestion_store.publish(args[0], derived, args[1], args[2])
            selected = program.build(
                args[0],
                derived,
                (ident,),
                batch_policy=retrieval_representation.BatchPolicy(max_items=1),
            )
            assert selected.batch_count > 1
            with pytest.raises(producer.ProducerRefused) as refused:
                executor.run(
                    args[0],
                    derived,
                    selected.program_bytes,
                    args[4],
                    args[5],
                    args[6],
                    args[7],
                    args[8],
                    args[9],
                    inputs,
                    reservation,
                    path,
                    deny,
                    deadline_ms=120000,
                )
            assert refused.value.owner is None
            assert [boundary for _, boundary in seen] == ["before_model"]
            assert json.loads(seen[0][0])["rows"][0]["chunk_id"] == selected.batches[0].chunk_ids[0]
            reservation.assert_owned()
    finally:
        reservation.close()


@pytest.mark.parametrize("status", ["FAILED", "UNKNOWN_COMPLETION"])
def test_actual_terminal_journal_stops_corpus(journey, tmp_path, monkeypatch, status):  # noqa: F811
    from slaif_raggedized_helper import embedding_job_journal, gpu_embedding_plan
    from slaif_raggedized_helper import (
        gpu_embedding_worker,
        gpu_worker_launch,
        retrieval_representation,
    )

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
            setup[k]
            for k in (
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
    path = tmp_path / "corpus-derived"
    path.mkdir(mode=0o700)
    preparation = None
    try:
        with derived_store.Store(path) as derived:
            ident = ingestion_store.publish(args[0], derived, args[1], args[2])
            bp = retrieval_representation.BatchPolicy(max_items=1)
            selected = program.build(args[0], derived, (ident,), batch_policy=bp)
            assert selected.batch_count > 1
            value = ingestion_store.load(args[0], derived, ident)
            preparation = gpu_worker_launch.prepare(**setup)
            plan = gpu_embedding_plan.build(
                args[0],
                value.metadata_json,
                value.members,
                selected.batches[0].chunk_ids,
                *args[4:],
                preparation,
                representation_policy=retrieval_representation.Policy(),
                batch_policy=bp,
            )
            preparation.close()
            preparation = None
            with embedding_job_journal.Journal(path).own(plan.plan_bytes) as handle:
                envelope, revision = handle.read()
                timestamp = envelope["events"][-1]["state"]["updated_ms"]
                attempt = producer._Attempt(handle, plan, derived, revision, timestamp, "a" * 48)
                attempt.append("CLAIMED", timestamp)
                attempt.append("RUNNING", timestamp)
                assert attempt.reconcile(status == "UNKNOWN_COMPLETION") == status
            monkeypatch.setattr(
                gpu_embedding_worker.GPUEmbeddingWorker,
                "__init__",
                lambda *_a, **_k: pytest.fail("GPU parent started"),
            )
            seen = []

            def authorize(plan_bytes, boundary):
                seen.append((plan_bytes, boundary))
                return "a" * 64

            with pytest.raises(producer.ProducerRefused):
                executor.run(
                    args[0],
                    derived,
                    selected.program_bytes,
                    args[4],
                    args[5],
                    args[6],
                    args[7],
                    args[8],
                    args[9],
                    inputs,
                    reservation,
                    path,
                    authorize,
                    deadline_ms=120000,
                )
            assert seen == [(plan.plan_bytes, "before_model")]
            with embedding_job_journal.Journal(path).own(plan.plan_bytes) as handle:
                assert handle.read()[0]["events"][-1]["state"]["status"] == status
            reservation.assert_owned()
    finally:
        if preparation is not None:
            preparation.close()
        reservation.close()


@pytest.mark.parametrize("fault", ["epoch", "output", "cross_epoch"])
def test_actual_complete_reuse_refuses_changed_epoch_or_output(
    journey,  # noqa: F811
    tmp_path,
    monkeypatch,
    fault,  # noqa: F811
):
    """Seed typed DATA only; this tests actual journal/reuse checks, not neural origin."""
    import json
    from slaif_raggedized_helper import (
        embedding_batch_store,
        embedding_job_journal,
        embedding_vectors,
    )
    from slaif_raggedized_helper import gpu_embedding_plan, gpu_embedding_worker
    from slaif_raggedized_helper import gpu_worker_launch, retrieval_representation

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
            setup[k]
            for k in (
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
    path = tmp_path / "corpus-derived"
    path.mkdir(mode=0o700)
    preparation = None
    try:
        with derived_store.Store(path) as derived:
            ident = ingestion_store.publish(args[0], derived, args[1], args[2])
            bp = retrieval_representation.BatchPolicy(max_items=1)
            selected = program.build(args[0], derived, (ident,), batch_policy=bp)
            assert selected.batch_count > 1
            value = ingestion_store.load(args[0], derived, ident)
            preparation = gpu_worker_launch.prepare(**setup)
            plan = gpu_embedding_plan.build(
                args[0],
                value.metadata_json,
                value.members,
                selected.batches[0].chunk_ids,
                *args[4:],
                preparation,
                representation_policy=retrieval_representation.Policy(),
                batch_policy=bp,
            )
            parsed = json.loads(plan.plan_bytes)
            vectors = producer._vector(embedding_vectors.normalize_rows([[1.0] + [0.0] * 1023]), 1)
            metadata = producer._metadata(parsed, vectors)
            identifier = embedding_batch_store.publish(derived, metadata, vectors.container)
            output = producer._output(metadata, identifier)
            preparation.close()
            preparation = None
            with embedding_job_journal.Journal(path).own(plan.plan_bytes) as handle:
                envelope, revision = handle.read()
                now = envelope["events"][-1]["state"]["updated_ms"]
                attempt = producer._Attempt(handle, plan, derived, revision, now, "a" * 48)
                attempt.append("CLAIMED", now)
                attempt.append("RUNNING", now)
                attempt.append("COMPLETE", now, output, metadata)
            if fault == "output":
                (path / "derived" / "v1" / "objects" / vectors.container_sha256).write_bytes(
                    b"corrupt"
                )
            monkeypatch.setattr(
                gpu_embedding_worker.GPUEmbeddingWorker,
                "__init__",
                lambda *_a, **_k: pytest.fail("GPU parent started"),
            )
            seen = []

            def authorize(plan_bytes, boundary):
                seen.append((plan_bytes, boundary))
                changed = (fault == "epoch" and boundary == "before_reuse") or (
                    fault == "cross_epoch" and len(seen) == 3
                )
                return "b" * 64 if changed else "a" * 64

            with pytest.raises(producer.ProducerRefused):
                executor.run(
                    args[0],
                    derived,
                    selected.program_bytes,
                    args[4],
                    args[5],
                    args[6],
                    args[7],
                    args[8],
                    args[9],
                    inputs,
                    reservation,
                    path,
                    authorize,
                    deadline_ms=120000,
                )
            assert seen[0][0] == plan.plan_bytes
            if fault == "cross_epoch":
                assert [b for _, b in seen] == ["before_model", "before_reuse", "before_model"]
                assert seen[1][0] == plan.plan_bytes and seen[2][0] != plan.plan_bytes
                assert (
                    json.loads(seen[2][0])["rows"][0]["chunk_id"]
                    == selected.batches[1].chunk_ids[0]
                )
            else:
                assert all(p == plan.plan_bytes for p, _ in seen)
                assert [b for _, b in seen] == (
                    ["before_model", "before_reuse"] if fault == "epoch" else ["before_model"]
                )
            with embedding_job_journal.Journal(path).own(plan.plan_bytes) as handle:
                assert handle.read()[0]["events"][-1]["state"]["status"] == "COMPLETE"
            reservation.assert_owned()
    finally:
        if preparation is not None:
            preparation.close()
        reservation.close()


def test_actual_hostile_interrupt_retains_producer_cleanup(journey, tmp_path, monkeypatch):  # noqa: F811
    import json
    import os
    from pathlib import Path
    import subprocess

    from slaif_raggedized_helper import embedding_artifacts, isolated_gpu_embedding
    from slaif_raggedized_helper import retrieval_representation
    from test_embedding_artifacts import write_config

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
    inputs = producer.LaunchInputs(
        *(
            setup[k]
            for k in (
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
    original_popen = subprocess.Popen.__init__
    descriptors, boundaries, starts = [], [], []

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
            path = tmp_path / "hostile-harness.py"
            path.write_text(script.replace(marker, injection + "\n" + marker))
            path.chmod(0o400)
            fd = os.open(path, os.O_RDONLY | os.O_CLOEXEC)
            descriptors.append(fd)
            argv[index - 1] = f"/proc/self/fd/{fd}"
            kwargs["pass_fds"] = tuple(
                fd if item == old_fd else item for item in kwargs["pass_fds"]
            )
        return original_popen(process, argv, **kwargs)

    class Hostile(BaseException):
        def __setattr__(self, _name, _value):
            raise RuntimeError("attribute assignment refused")

    hostile = Hostile()

    def authorize(_plan, boundary):
        boundaries.append(boundary)
        if boundary == "before_encode":
            raise hostile
        return "a" * 64

    path = tmp_path / "corpus-derived"
    path.mkdir(mode=0o700)
    monkeypatch.setattr(subprocess.Popen, "__init__", intercept)
    try:
        with derived_store.Store(path) as derived:
            ident = ingestion_store.publish(args[0], derived, args[1], args[2])
            selected = program.build(
                args[0],
                derived,
                (ident,),
                batch_policy=retrieval_representation.BatchPolicy(max_items=1),
            )
            assert selected.batch_count > 1
            with monkeypatch.context() as context:
                context.setattr(
                    isolated_gpu_embedding.GPUTextEmbeddingSession,
                    "_drain",
                    lambda *_: (_ for _ in ()).throw(OSError("controlled drain fault")),
                )
                with pytest.raises(Hostile) as raised:
                    executor.run(
                        args[0],
                        derived,
                        selected.program_bytes,
                        args[4],
                        args[5],
                        args[6],
                        args[7],
                        args[8],
                        args[9],
                        inputs,
                        reservation,
                        path,
                        authorize,
                        deadline_ms=120000,
                    )
                assert raised.value is hostile
                pending = producer.pending_cleanup(hostile)
                assert (
                    pending is not None
                    and pending.session is not None
                    and pending.lease is not None
                )
                assert starts == [1] and boundaries == ["before_model", "before_encode"]
            pending.close()
            assert producer.pending_cleanup(hostile) is None
            reservation.assert_owned()
    finally:
        for fd in descriptors:
            os.close(fd)
        reservation.close()
