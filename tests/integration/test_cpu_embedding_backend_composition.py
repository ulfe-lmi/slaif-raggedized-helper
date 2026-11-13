"""Standalone composition uses real admission and the trusted test-only fake."""

import importlib.util
from pathlib import Path


def test_composition(tmp_path, monkeypatch):
    unit = Path(__file__).resolve().parents[1] / "unit"
    monkeypatch.syspath_prepend(str(unit))
    spec = importlib.util.spec_from_file_location(
        "cpu_backend_fixture", unit / "test_cpu_embedding_backend.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    root = tmp_path / "artifacts"
    _, raw, inv, definition, tokenizer = module.make_tree(root)
    fake, factory = module.Torch(), module.Factory(module.Model())
    monkeypatch.setattr(module.backend, "_framework", lambda: (fake, factory))
    instance = module.backend.CPUEmbeddingBackend(
        raw, root, definition, tokenizer, inv.inventory_id
    )
    assert instance.space.inventory_id == inv.inventory_id
    assert instance.forward_cls([[2, 3]]) == ((2.0,) * 1024,)
    instance.close()
