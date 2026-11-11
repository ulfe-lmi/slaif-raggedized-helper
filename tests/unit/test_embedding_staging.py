import json

import pytest

from slaif_raggedized_helper import embedding_artifacts, embedding_space, embedding_staging
from test_embedding_space import fixture


def test_schema2_copy_and_cleanup(tmp_path):
    root = tmp_path / "source"
    manifest, _, _, d, t = fixture(root)
    weight = next(x for x in manifest["files"] if x["role"] == "weights")
    (root / weight["path"]).rename(root / "pytorch_model.bin")
    weight["path"] = "pytorch_model.bin"
    manifest.update(schema=2, checkpoint_format="pytorch-state-dict")
    raw = json.dumps(manifest).encode()
    inv = embedding_artifacts.verify_artifacts(raw, root)
    expected = embedding_space.admit(raw, root, d, t, inv.inventory_id)
    (root / "custom.py").write_text("canary")
    with embedding_staging.stage(raw, root, d, t, inv.inventory_id) as staged:
        path = staged.path
        assert staged.space == expected
        assert {str(p.relative_to(path)) for p in path.rglob("*") if p.is_file()} == {
            f.path for f in inv.files
        }
        for f in inv.files:
            assert (path / f.path).read_bytes() == (root / f.path).read_bytes()
    assert not path.exists()
    assert (root / "custom.py").read_text() == "canary"
    with pytest.raises(RuntimeError):
        with embedding_staging.stage(raw, root, d, t, inv.inventory_id) as staged:
            path = staged.path
            raise RuntimeError
    assert not path.exists()


def test_mutation_after_admission_refused(tmp_path, monkeypatch):
    root = tmp_path / "source"
    _, raw, inv, d, t = fixture(root)
    embedding_space.admit(raw, root, d, t, inv.inventory_id)
    original = embedding_space.admit

    def mutate(*args, **kwargs):
        result = original(*args, **kwargs)
        (root / "tokenizer.json").write_bytes(b"changed")
        return result

    monkeypatch.setattr(embedding_space, "admit", mutate)
    with pytest.raises(ValueError):
        with embedding_staging.stage(raw, root, d, t, inv.inventory_id, parent=tmp_path):
            pytest.fail("staged changed bytes")
    assert sorted(p.name for p in tmp_path.iterdir()) == ["source"]


def test_bad_parent_timeout_and_source(tmp_path):
    root = tmp_path / "source"
    _, raw, inv, d, t = fixture(root)
    embedding_space.admit(raw, root, d, t, inv.inventory_id)
    parent = tmp_path / "public"
    parent.mkdir(mode=0o755)
    for kwargs in ({"parent": parent}, {"timeout": 1e-100}):
        with pytest.raises(ValueError):
            with embedding_staging.stage(raw, root, d, t, inv.inventory_id, **kwargs):
                pytest.fail("unexpected stage")
    (root / "tokenizer.json").unlink()
    (root / "tokenizer.json").symlink_to(root / "config.json")
    with pytest.raises(ValueError):
        with embedding_staging.stage(raw, root, d, t, inv.inventory_id):
            pytest.fail("unexpected stage")


def test_interrupted_copy_cleans_up(tmp_path, monkeypatch):
    root = tmp_path / "source"
    _, raw, inv, d, t = fixture(root)
    embedding_space.admit(raw, root, d, t, inv.inventory_id)
    original = embedding_artifacts._open_file
    calls = 0

    def interrupted(*args):
        nonlocal calls
        calls += 1
        if calls == 19:
            raise OSError("interrupted")
        return original(*args)

    monkeypatch.setattr(embedding_artifacts, "_open_file", interrupted)
    with pytest.raises(OSError):
        with embedding_staging.stage(raw, root, d, t, inv.inventory_id, parent=tmp_path):
            pytest.fail("unexpected stage")
    assert sorted(p.name for p in tmp_path.iterdir()) == ["source"]
