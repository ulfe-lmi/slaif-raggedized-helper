"""Real source/native admission and isolated protocol with trusted fake CPU provider."""

import hashlib
import json
import os
import subprocess
import tomllib
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import pytest

from slaif_raggedized_helper import cpu_embedding_backend, cpu_embedding_plan as plan
from slaif_raggedized_helper import cpu_embedding_worker as cpu
from slaif_raggedized_helper import cpu_execution_contract as contract
from slaif_raggedized_helper import embedding_artifacts, embedding_batch_plan, embedding_tokenizer
from slaif_raggedized_helper import isolated_cpu_embedding as isolated, native_tokenizers as nt
from slaif_raggedized_helper import tokenizer_session
from test_cpu_embedding_backend import make_tree
from test_native_tokenizers import make_native
from test_retrieval_representation_composition import make_bundle
from test_structured_text_composition import create_store
from test_cpu_embedding_worker_composition import FAKE


def test_source_plan_before_worker_and_observed_contract(tmp_path, monkeypatch):
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
    store, revisions = create_store(tmp_path, "# Heading\n\n" + "hello world. " * 650 + "\n")
    try:
        metadata, members, _, result = make_bundle(store, revisions[0], definitions, runtime)
        ids = [c.chunk_id for c in result.chunks[:2]]
        args = (
            store,
            metadata,
            members,
            ids,
            raw,
            root,
            definition,
            token,
            inv.inventory_id,
            runtime,
        )
        cpu_runtime = nt.Runtime(
            Path(os.environ["SLAIF_CPU_V2_TEST_ROOT"]),
            Path(os.environ["SLAIF_CPU_V2_TEST_PACKAGES"]),
            "python3.12",
        )
        policy = cpu.Policy(address_bytes=1024**3, cpu_seconds=30, lifetime_seconds=120)
        wrong_packages = tmp_path / "wrong-packages"
        wrong_packages.mkdir(mode=0o700)
        wrong_runtime = replace(cpu_runtime, packages=wrong_packages)
        with pytest.raises(contract.ContractError):
            contract.prepare(
                raw,
                root,
                definition,
                token,
                inv.inventory_id,
                runtime,
                wrong_runtime,
                worker_policy=policy,
            )
        # Old selected metadata must fail prediction before any child or model activity.
        old_packages = tmp_path / "old-metadata"
        old_packages.mkdir(mode=0o700)
        old_lock = Path(__file__).resolve().parents[2] / "worker_profiles/cpu/uv.lock"
        for item in tomllib.loads(old_lock.read_text())["package"]:
            if "registry" in item["source"]:
                directory = old_packages / (item["name"] + ".dist-info")
                directory.mkdir()
                (directory / "METADATA").write_text(
                    f"Name: {item['name']}\nVersion: {item['version']}\n"
                )
        old_runtime = replace(cpu_runtime, packages=old_packages)
        calls = []
        with (
            patch.object(subprocess, "Popen", side_effect=lambda *a, **k: calls.append("child")),
            patch.object(
                cpu_embedding_backend, "_framework", side_effect=lambda: calls.append("model")
            ),
        ):
            with pytest.raises(contract.ContractError):
                contract.prepare(
                    raw,
                    root,
                    definition,
                    token,
                    inv.inventory_id,
                    runtime,
                    old_runtime,
                    worker_policy=policy,
                )
            with pytest.raises(cpu.WorkerRefused):
                cpu.CPUEmbeddingWorker(
                    raw,
                    root,
                    definition,
                    token,
                    inv.inventory_id,
                    old_runtime,
                    policy,
                )
        assert calls == []
        calls = []

        def forbidden(name):
            def stop(*args, **kwargs):
                calls.append(name)
                raise AssertionError("unexpected operation")

            return stop

        with (
            patch.object(subprocess, "Popen", forbidden("subprocess")),
            patch.object(tokenizer_session.Session, "__init__", forbidden("count session")),
            patch.object(embedding_tokenizer.TokenIDSession, "__init__", forbidden("token IDs")),
            patch.object(cpu.CPUEmbeddingWorker, "__init__", forbidden("CPU worker")),
            patch.object(isolated.IsolatedCPUEmbeddingSession, "__enter__", forbidden("enter")),
            patch.object(cpu_embedding_backend, "_framework", forbidden("framework")),
        ):
            direct = contract.prepare(
                raw,
                root,
                definition,
                token,
                inv.inventory_id,
                runtime,
                cpu_runtime,
                worker_policy=policy,
            )
            assert calls == []
        with (
            patch.object(cpu.CPUEmbeddingWorker, "__init__", side_effect=AssertionError),
            patch.object(
                isolated.IsolatedCPUEmbeddingSession, "__enter__", side_effect=AssertionError
            ),
            patch.object(
                embedding_tokenizer.TokenIDSession, "__init__", side_effect=AssertionError
            ),
            patch.object(cpu_embedding_backend, "_framework", side_effect=AssertionError),
        ):
            predicted = plan.build(*args, cpu_runtime, worker_policy=policy)
            assert predicted == plan.build(*args, cpu_runtime, worker_policy=policy)
            assert direct.record_bytes == predicted.predicted_record
            assert direct.fingerprint == predicted.execution_fingerprint
            # Simulated identity changes exercise binding; these do not qualify a profile.
            for name in ("_profile", "_code_identity"):
                with patch.object(cpu, name, return_value="f" * 64):
                    simulated = plan.build(*args, cpu_runtime, worker_policy=policy)
                assert simulated.spec.job_id != predicted.spec.job_id
                assert simulated.execution_fingerprint != predicted.execution_fingerprint
                assert (
                    simulated.intended_execution_fingerprint
                    == predicted.intended_execution_fingerprint
                )
                assert json.loads(simulated.predicted_record)["space"] == direct.space_id
            with patch.object(cpu, "_profile", side_effect=ValueError("bad pinned profile")):
                with pytest.raises(contract.ContractError):
                    contract.prepare(
                        raw,
                        root,
                        definition,
                        token,
                        inv.inventory_id,
                        runtime,
                        cpu_runtime,
                        worker_policy=policy,
                    )
            legacy = embedding_batch_plan.build(*args)
            old, new = json.loads(legacy.plan_bytes), json.loads(predicted.plan_bytes)
            assert (
                new["dependencies"].pop("execution_fingerprint")
                == predicted.execution_fingerprint[7:]
            )
            assert (
                old["dependencies"].pop("execution_fingerprint")
                == predicted.intended_execution_fingerprint[7:]
            )
            assert old == new and legacy.texts == predicted.texts
            assert legacy.spec.job_id != predicted.spec.job_id
            assert b"hello" not in predicted.predicted_record
            reversed_plan = plan.build(
                *args[:3], ids[::-1], *args[4:], cpu_runtime, worker_policy=policy
            )
            assert reversed_plan.spec.job_id != predicted.spec.job_id
            changed_manifest = dict(manifest, model_revision="b" * 40)
            changed_raw = json.dumps(changed_manifest).encode()
            changed_inv = embedding_artifacts.verify_artifacts(changed_raw, root)
            changed_d = definition.model_copy(
                update={"checkpoint_revision": "b" * 40, "tokenizer_revision": "b" * 40}
            )
            changed_t = replace(token, model_revision="b" * 40)
            changed_defs = (
                replace(changed_t, role="bge_body"),
                changed_t,
                replace(definitions[2], model_revision="b" * 40),
            )
            meta2, members2, _, chunks2 = make_bundle(store, revisions[0], changed_defs, runtime)
            changed_model = plan.build(
                store,
                meta2,
                members2,
                [c.chunk_id for c in chunks2.chunks[:2]],
                changed_raw,
                root,
                changed_d,
                changed_t,
                changed_inv.inventory_id,
                runtime,
                cpu_runtime,
                worker_policy=policy,
            )
            assert changed_model.spec.job_id != predicted.spec.job_id
            assert changed_model.execution_fingerprint != predicted.execution_fingerprint
            record = json.loads(predicted.predicted_record)
            assert record["hardware_qualification"] == "unknown"
            for invalid in (
                predicted.predicted_record.replace(b'"schema":2', b'"schema":true'),
                predicted.predicted_record.replace(b'"schema":2', b'"schema":1'),
                predicted.predicted_record.replace(b'"schema":2', b'"schema":2,"schema":2'),
                predicted.predicted_record + b" ",
            ):
                with pytest.raises(ValueError):
                    contract._validate(invalid)
            with pytest.raises(ValueError):
                embedding_batch_plan._unprefix(predicted.execution_fingerprint[7:])
            with patch.object(
                contract,
                "_bridge",
                return_value={**record["bridge"], "cpu_execution_contract.py": "0" * 64},
            ):
                changed = plan.build(*args, cpu_runtime, worker_policy=policy)
            assert changed.spec.job_id != predicted.spec.job_id
            assert json.loads(changed.predicted_record)["space"] == record["space"]
            with patch.object(
                embedding_batch_plan,
                "build",
                return_value=replace(
                    legacy,
                    plan_bytes=legacy.plan_bytes.replace(inv.inventory_id.encode(), b"0" * 64),
                ),
            ):
                with pytest.raises(plan.PlanError):
                    plan.build(*args, cpu_runtime, worker_policy=policy)
            assert (
                plan.build(*args, cpu_runtime, worker_policy=replace(policy, calls=1)).spec.job_id
                != predicted.spec.job_id
            )
            with pytest.raises(plan.PlanError):
                plan.build(*args[:3], ["foreign"], *args[4:], cpu_runtime, worker_policy=policy)
        script = tmp_path / "fake.py"
        script.write_text(FAKE)
        original = cpu._argv

        def intercept(*argv):
            result = original(*argv)
            result[result.index("/worker.py") - 1] = str(script)
            return result

        monkeypatch.setattr(cpu, "_argv", intercept)
        with isolated.IsolatedCPUEmbeddingSession(
            raw,
            root,
            definition,
            token,
            inv.inventory_id,
            runtime,
            cpu_runtime,
            worker_policy=policy,
        ) as session:
            observed = session.encode(["hello"])
            assert observed.execution_record == predicted.predicted_record
            assert observed.execution_fingerprint == predicted.execution_fingerprint
            assert json.loads(observed.execution_record)["schema"] == 2
    finally:
        store.close()
