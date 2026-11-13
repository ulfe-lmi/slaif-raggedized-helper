"""Actual source, journals, synthetic workers and resident query composition."""

import hashlib
import json
import os
from pathlib import Path
import subprocess
import resource
import time

from slaif_raggedized_helper import cpu_embedding_worker, derived_store, embedding_artifacts
from slaif_raggedized_helper import gpu_embedding_producer, ingestion_store, native_tokenizers
from slaif_raggedized_helper.qualification.embedding_capture import capture
from slaif_raggedized_helper.query_embedding import ResidentQueryEncoder
from test_cpu_embedding_worker_composition import FAKE
from test_embedding_artifacts import write_config
from test_embedding_batch_plan_composition import journey  # noqa: F401
from test_gpu_worker_launch import _prepared_fixture


def test_actual_synthetic_capture_and_reuse(request, tmp_path, monkeypatch):
    started = time.monotonic()
    before = resource.getrusage(resource.RUSAGE_SELF)
    children_before = resource.getrusage(resource.RUSAGE_CHILDREN)

    def check_budget():
        parent = resource.getrusage(resource.RUSAGE_SELF)
        child = resource.getrusage(resource.RUSAGE_CHILDREN)
        total = (
            parent.ru_utime
            + parent.ru_stime
            - before.ru_utime
            - before.ru_stime
            + child.ru_utime
            + child.ru_stime
            - children_before.ru_utime
            - children_before.ru_stime
        )
        assert total <= 180 and time.monotonic() - started < 360

    journey_data = request.getfixturevalue("journey")
    check_budget()
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
    inputs = gpu_embedding_producer.LaunchInputs(
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
    runtime = native_tokenizers.Runtime(
        Path(os.environ["SLAIF_CPU_V2_TEST_ROOT"]),
        Path(os.environ["SLAIF_CPU_V2_TEST_PACKAGES"]),
        "python3.12",
    )
    policy = cpu_embedding_worker.Policy(
        address_bytes=1024**3, cpu_seconds=30, lifetime_seconds=120
    )
    script = tmp_path / "cpu-fake.py"
    script.write_text(FAKE)
    original_argv = cpu_embedding_worker._argv

    def cpu_argv(*values):
        argv = original_argv(*values)
        argv[argv.index("/worker.py") - 1] = str(script)
        return argv

    monkeypatch.setattr(cpu_embedding_worker, "_argv", cpu_argv)
    original_popen = subprocess.Popen.__init__
    descriptors = []

    def popen(process, argv, **kwargs):
        argv = list(argv)
        if argv[0] == "/usr/bin/prlimit" and "/worker.py" in argv:
            index = argv.index("/worker.py")
            old_fd = int(argv[index - 1].rsplit("/", 1)[-1])
            source = Path(f"/proc/self/fd/{old_fd}").read_text()
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
            assert source.count(marker) == 1
            harness = source.replace(marker, injection + "\n" + marker).encode()
            print("gpu_harness_sha256=" + hashlib.sha256(harness).hexdigest(), flush=True)
            path = tmp_path / "gpu-harness.py"
            path.write_bytes(harness)
            path.chmod(0o400)
            fd = os.open(path, os.O_RDONLY | os.O_CLOEXEC)
            descriptors.append(fd)
            argv[index - 1] = f"/proc/self/fd/{fd}"
            kwargs["pass_fds"] = tuple(
                fd if value == old_fd else value for value in kwargs["pass_fds"]
            )
        return original_popen(process, argv, **kwargs)

    monkeypatch.setattr(subprocess.Popen, "__init__", popen)
    try:
        with derived_store.Store(tmp_path) as store:
            bundle = ingestion_store.publish(args[0], store, args[1], args[2])
            encoder = ResidentQueryEncoder(
                args[4], args[5], args[6], args[7], args[8], args[9], runtime, worker_policy=policy
            )
            with encoder:
                (tmp_path / "cpu-journal").mkdir(mode=0o700)
                (tmp_path / "gpu-journal").mkdir(mode=0o700)

                def run():
                    return capture(
                        args[0],
                        store,
                        bundle,
                        args[3],
                        args[4],
                        args[5],
                        args[6],
                        args[7],
                        args[8],
                        args[9],
                        runtime,
                        inputs,
                        reservation,
                        tmp_path / "cpu-journal",
                        tmp_path / "gpu-journal",
                        encoder,
                        (("query", "hello", (args[3][0],)),),
                        lambda *_: "a" * 64,
                        deadline_ms=180000,
                        k=1,
                        cosine_tolerance=2,
                        score_tolerance=2,
                        cpu_worker_policy=policy,
                    )

                first = run()
                check_budget()
                second = run()
                check_budget()
                first_data, second_data = (
                    json.loads(first.capture_bytes),
                    json.loads(second.capture_bytes),
                )
                assert first_data["origin"] == "OBSERVED_LOCAL_SOFTWARE_PATHS_UNQUALIFIED"
                assert first_data["qualification"] == "NOT_QUALIFIED"
                assert first.analyzer_result["evidence"] == "SUPPLIED_UNVERIFIED"
                assert not first_data["cpu"]["reused"] and not first_data["gpu"]["reused"]
                assert second_data["cpu"]["reused"] and second_data["gpu"]["reused"]
                assert b"hello" not in first.capture_bytes
    finally:
        for fd in descriptors:
            os.close(fd)
        reservation.close()
        after = resource.getrusage(resource.RUSAGE_SELF)
        children = resource.getrusage(resource.RUSAGE_CHILDREN)
        parent_cpu = after.ru_utime + after.ru_stime - before.ru_utime - before.ru_stime
        child_cpu = (
            children.ru_utime
            + children.ru_stime
            - children_before.ru_utime
            - children_before.ru_stime
        )
        print(
            f"proof_wall_seconds={time.monotonic() - started:.3f} "
            f"parent_cpu_seconds={parent_cpu:.3f} "
            f"children_cpu_seconds={child_cpu:.3f} "
            f"parent_peak_rss_kib={after.ru_maxrss} children_peak_rss_kib={children.ru_maxrss}",
            flush=True,
        )


def test_actual_bad_gpu_root_refuses_before_cpu_entry(request, tmp_path, monkeypatch):
    import pytest
    from slaif_raggedized_helper import cpu_embedding_producer
    from slaif_raggedized_helper.qualification.embedding_capture import CaptureRefused

    entered = []
    actual = capture

    def cpu_entry(*_args, **_kwargs):
        entered.append(True)
        raise AssertionError("CPU entry reached")

    def bad_root(*args, **kwargs):
        path = args[14]
        path.rmdir()
        path.write_bytes(b"not a directory")
        path.chmod(0o600)
        return actual(*args, **kwargs)

    monkeypatch.setattr(cpu_embedding_producer, "produce", cpu_entry)
    monkeypatch.setitem(globals(), "capture", bad_root)
    with pytest.raises(CaptureRefused, match="^capture refused$"):
        test_actual_synthetic_capture_and_reuse(request, tmp_path, monkeypatch)
    assert not entered


def test_actual_epoch_revocation_refuses_before_cpu_forward(request, tmp_path, monkeypatch):
    import pytest
    from slaif_raggedized_helper import cpu_embedding_producer, isolated_cpu_embedding

    actual = capture
    entered = []
    gpu = []

    def inject(*args, **kwargs):
        def denied(_data, boundary):
            return ("b" if boundary == "before_encode" else "a") * 64

        def no_forward(*_args, **_kwargs):
            entered.append(True)
            raise AssertionError("document encode reached")

        def no_gpu(*_args, **_kwargs):
            gpu.append(True)
            raise AssertionError("GPU producer reached")

        values = list(args)
        values[17] = denied
        monkeypatch.setattr(
            isolated_cpu_embedding.IsolatedCPUEmbeddingSession, "encode", no_forward
        )
        monkeypatch.setattr(gpu_embedding_producer, "produce", no_gpu)
        return actual(*values, **kwargs)

    monkeypatch.setitem(globals(), "capture", inject)
    with pytest.raises(cpu_embedding_producer.ProducerRefused):
        test_actual_synthetic_capture_and_reuse(request, tmp_path, monkeypatch)
    assert not entered and not gpu


def test_actual_query_binding_valid_and_corrupt(tmp_path, monkeypatch):
    from dataclasses import replace
    import pytest
    from slaif_raggedized_helper.qualification.embedding_capture import (
        CaptureRefused,
        _query_result,
    )
    from test_cpu_embedding_backend import make_tree
    from test_native_tokenizers import make_native

    paths, tokenizer_runtime, _ = make_native(tmp_path)
    root = tmp_path / "query-model"
    manifest, _, _, definition, token = make_tree(root)
    data = paths[0].read_bytes()
    (root / "tokenizer.json").write_bytes(data)
    entry = next(item for item in manifest["files"] if item["role"] == "tokenizer")
    entry.update(size=len(data), sha256=hashlib.sha256(data).hexdigest())
    raw = json.dumps(manifest).encode()
    inventory = embedding_artifacts.verify_artifacts(raw, root)
    token = replace(token, sha256=entry["sha256"])
    runtime = native_tokenizers.Runtime(
        Path(os.environ["SLAIF_CPU_V2_TEST_ROOT"]),
        Path(os.environ["SLAIF_CPU_V2_TEST_PACKAGES"]),
        "python3.12",
    )
    policy = cpu_embedding_worker.Policy(
        address_bytes=1024**3, cpu_seconds=30, lifetime_seconds=120
    )
    script = tmp_path / "query-fake.py"
    script.write_text(FAKE)
    original = cpu_embedding_worker._argv

    def argv(*args):
        result = original(*args)
        result[result.index("/worker.py") - 1] = str(script)
        return result

    monkeypatch.setattr(cpu_embedding_worker, "_argv", argv)
    encoder = ResidentQueryEncoder(
        raw,
        root,
        definition,
        token,
        inventory.inventory_id,
        tokenizer_runtime,
        runtime,
        worker_policy=policy,
    )
    with encoder:
        result = ResidentQueryEncoder.encode_query(encoder, "hello")
        vector = _query_result(
            result, definition, result.space_id, result.intended_execution_fingerprint
        )
        assert len(vector) == 1024
        for bad in (
            replace(result, space_id="0" * 64),
            replace(result, payload_sha256="0" * 64),
            replace(result, execution_fingerprint="sha256:" + "0" * 64),
        ):
            with pytest.raises(CaptureRefused):
                _query_result(
                    bad, definition, result.space_id, result.intended_execution_fingerprint
                )
