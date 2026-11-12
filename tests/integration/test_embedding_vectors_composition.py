"""Compose actual admission and backend with trusted framework doubles."""

import importlib.util
from pathlib import Path

from slaif_raggedized_helper.embedding_vectors import normalize_rows


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
    first = instance.forward_cls([[2, 3]])
    second = instance.forward_cls([[2, 3]])
    assert first == second == ((2.0,) * 1024,)
    assert len(factory.calls) == 1 and len(factory.model.calls) == 2
    result = normalize_rows(first + second)
    assert result.rows == ((0.03125,) * 1024,) * 2
    assert result.payload == __import__("struct").pack("<2048f", *([0.03125] * 2048))
    instance.close()
