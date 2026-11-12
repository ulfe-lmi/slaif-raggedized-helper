"""Standalone real staged admission and native IDs with only a fake framework."""
import hashlib
import importlib.util
import json
import math
import os
import subprocess

import pytest
from dataclasses import replace
from pathlib import Path

from slaif_raggedized_helper import cpu_embedding_session as session, embedding_artifacts


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_real_composition(tmp_path, monkeypatch):
    unit = Path(__file__).resolve().parents[1] / "unit"
    monkeypatch.syspath_prepend(str(unit))
    backend = load("trusted_backend_fixture", unit / "test_cpu_embedding_backend.py")
    native = load("trusted_native_fixture", unit / "test_native_tokenizers.py")
    paths, runtime, _ = native.make_native(tmp_path)
    root = tmp_path / "tree"
    manifest, _, _, definition, tokenizer = backend.make_tree(root)
    raw_tokenizer = paths[0].read_bytes()
    (root / "tokenizer.json").write_bytes(raw_tokenizer)
    entry = next(x for x in manifest["files"] if x["role"] == "tokenizer")
    entry.update(size=len(raw_tokenizer), sha256=hashlib.sha256(raw_tokenizer).hexdigest())
    raw = json.dumps(manifest).encode()
    inventory = embedding_artifacts.verify_artifacts(raw, root)
    tokenizer = replace(tokenizer, sha256=entry["sha256"])
    class DistinctModel(backend.Model):
        def __call__(self, **kwargs):
            output = super().__call__(**kwargs)
            for row, ids in zip(output.last_hidden_state.data, kwargs["input_ids"].data,
                                strict=True):
                row[0][1] = float(len([token for token in ids if token != 1]))
            return output

    model, torch = DistinctModel(), backend.Torch()
    factory = backend.Factory(model)
    monkeypatch.setattr(backend.backend, "_framework", lambda: (torch, factory))
    with session.CPUEmbeddingSession(raw, root, definition, tokenizer,
                                     inventory.inventory_id, runtime) as obj:
        staged = obj._staged.path
        child = obj._tokenizer._child
        assert staged.exists() and os.stat(staged / "tokenizer.json").st_mode & 0o222 == 0
        first = obj.encode(["hello café 世界", "hello"])
        assert [r.ids for r in first.receipts] == [(1, 3, 4, 5, 2), (1, 3, 2)]
        assert [r.input_sha256 for r in first.receipts] == [
            hashlib.sha256(json.dumps([text, None], ensure_ascii=True,
                                      separators=(",", ":")).encode()).hexdigest()
            for text in ("hello café 世界", "hello")
        ]
        assert model.calls[0]["input_ids"].data == [[1, 3, 4, 5, 2], [1, 3, 2, 1, 1]]
        assert first.space_id == obj.space.space_id
        assert first.definition_fingerprint == definition.fingerprint()
        assert first.execution_fingerprint == obj.execution.fingerprint()
        assert first.policy_id == first.vectors.policy_id
        assert first.vectors.sha256 == hashlib.sha256(first.vectors.payload).hexdigest()
        assert all(abs(math.fsum(x*x for x in row) - 1) < 1e-4 for row in first.vectors.rows)
        assert first.vectors.rows[0] != first.vectors.rows[1]
        assert first.vectors.rows[0][1] > first.vectors.rows[1][1]
        assert len(first.vectors.payload) == 2 * 1024 * 4
        obj._tokenizer._calls = 1024
        second = obj.encode(["hello"])
        assert second.receipts[0].ids == (1, 3, 2)
        assert child.poll() is not None and obj._tokenizer._child is not child
        last = obj._tokenizer._child
        assert len(factory.calls) == 1 and len(model.calls) == 2
    assert last.poll() is not None and not staged.exists()

    # A real native worker exists before a failed neural load and is reaped.
    children = []
    original_popen = subprocess.Popen
    def spawn(*args, **kwargs):
        child = original_popen(*args, **kwargs)
        children.append(child)
        return child
    monkeypatch.setattr(session.embedding_tokenizer.subprocess, "Popen", spawn)
    failed_paths = []
    original_backend = session.cpu_embedding_backend.CPUEmbeddingBackend
    def backend_with_path(*args):
        failed_paths.append(args[1])
        return original_backend(*args)
    monkeypatch.setattr(session.cpu_embedding_backend, "CPUEmbeddingBackend", backend_with_path)
    def framework_failure():
        raise ValueError("private detail")
    monkeypatch.setattr(backend.backend, "_framework", framework_failure)
    with pytest.raises(session.SessionRefused):
        session.CPUEmbeddingSession(raw, root, definition, tokenizer,
                                    inventory.inventory_id, runtime)
    assert len(children) == 1 and children[0].poll() is not None
    assert not failed_paths[0].exists()
