"""Standalone composition against actual artifact and space admissions."""
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest

from slaif_raggedized_helper import embedding_artifacts, embedding_space, embedding_staging


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_unit = Path(__file__).parents[1] / "unit"
_load("test_embedding_artifacts", _unit / "test_embedding_artifacts.py")
fixture = _load("test_embedding_space", _unit / "test_embedding_space.py").fixture


def test_schema2_complete_lifecycle(tmp_path):
    root = tmp_path / "source"
    manifest, _, old, definition, tokenizer = fixture(root)
    weights = next(item for item in manifest["files"] if item["role"] == "weights")
    (root / weights["path"]).rename(root / "pytorch_model.bin")
    weights["path"] = "pytorch_model.bin"
    manifest.update(schema=2, checkpoint_format="pytorch-state-dict")
    raw = json.dumps(manifest).encode()
    inventory = embedding_artifacts.verify_artifacts(raw, root)
    baseline = embedding_space.admit(raw, root, definition, tokenizer, inventory.inventory_id)
    assert inventory.inventory_id != old.inventory_id
    assert (baseline.inventory_schema, baseline.checkpoint_format) == (2, "pytorch-state-dict")
    (root / "custom.py").write_bytes(b"unlisted canary")
    before = {str(p.relative_to(root)): p.read_bytes() for p in root.rglob("*") if p.is_file()}
    with embedding_staging.stage(
        raw, root, definition, tokenizer, inventory.inventory_id
    ) as staged:
        staged_path = staged.path
        assert staged.manifest_bytes == raw and staged.space == baseline
        assert staged_path != root and staged.space.space_id == baseline.space_id
        actual = {str(p.relative_to(staged_path)): p.read_bytes()
                  for p in staged_path.rglob("*") if p.is_file()}
        assert set(actual) == {item.path for item in inventory.files}
        for item in inventory.files:
            assert actual[item.path] == before[item.path]
            assert hashlib.sha256(actual[item.path]).hexdigest() == item.sha256
        assert staged_path.stat().st_mode & 0o777 == 0o500
        assert all(p.stat().st_mode & 0o777 == (0o500 if p.is_dir() else 0o400)
                   for p in staged_path.rglob("*"))
    assert not staged_path.exists()
    assert before == {str(p.relative_to(root)): p.read_bytes()
                      for p in root.rglob("*") if p.is_file()}
    with pytest.raises(RuntimeError, match="caller exception"):
        with embedding_staging.stage(raw, root, definition, tokenizer, inventory.inventory_id) as s:
            staged_path = s.path
            raise RuntimeError("caller exception")
    assert not staged_path.exists()
