"""Actual artifact and kernel lease composition with controlled fake framework."""

import importlib.util
from pathlib import Path


def test_composition(tmp_path, monkeypatch):
    unit = Path(__file__).resolve().parents[1] / 'unit'
    monkeypatch.syspath_prepend(str(unit))
    spec = importlib.util.spec_from_file_location('gpu_backend_fixture',
                                                  unit / 'test_gpu_embedding_backend.py')
    fixture = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fixture)
    root = tmp_path / 'artifacts'
    raw, inv, definition, tokenizer = fixture.make_tree(root)
    locks = tmp_path / 'locks'
    locks.mkdir(mode=0o700)
    torch, factory = fixture.Torch(), fixture.Factory()
    monkeypatch.setenv('CUDA_VISIBLE_DEVICES', fixture.DEVICE)
    monkeypatch.setattr(fixture.backend, '_framework', lambda: (torch, factory))
    with fixture.gpu_device_lease.acquire(str(locks), fixture.HOST, fixture.DEVICE) as lease:
        obj = fixture.backend.GPUEmbeddingBackend(raw, root, definition, tokenizer,
                                                  inv.inventory_id, lease, fixture.DEVICE)
        assert obj.space.inventory_id == inv.inventory_id
        assert obj.forward_cls([[2, 3]]) == ((2.0,) * 1024,)
        obj.close()
        lease.assert_owned()
