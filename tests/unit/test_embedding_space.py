import json
from dataclasses import replace

import pytest

from slaif_raggedized_helper import embedding_artifacts, embedding_space
from slaif_raggedized_helper.native_tokenizers import Definition
from slaif_raggedized_helper.schema import EmbeddingDefinition
from test_embedding_artifacts import setup_tree


def fixture(root):
    manifest = setup_tree(root)
    raw = json.dumps(manifest).encode()
    inv = embedding_artifacts.verify_artifacts(raw, root)
    files = {f.role: f for f in inv.files}
    d = EmbeddingDefinition(
        model_name="BAAI/bge-m3",
        checkpoint_revision=inv.model_revision,
        checkpoint_sha256=files["weights"].sha256,
        tokenizer_revision=inv.model_revision,
        pooling="cls",
        dimensions=1024,
    )
    t = Definition(
        root / "tokenizer.json",
        files["tokenizer"].sha256,
        "0.21.4",
        "bge_representation",
        inv.model_revision,
        "identity",
    )
    return manifest, raw, inv, d, t


def test_real_verification_and_root_independence(tmp_path, monkeypatch):
    m, raw, inv, d, t = fixture(tmp_path / "one")
    _, raw2, inv2, d2, t2 = fixture(tmp_path / "two")
    original = embedding_artifacts.verify_artifacts
    calls = []

    def witness(*a, **kw):
        calls.append(1)
        return original(*a, **kw)

    monkeypatch.setattr(embedding_artifacts, "verify_artifacts", witness)
    a = embedding_space.admit(raw, tmp_path / "one", d, t, inv.inventory_id)
    b = embedding_space.admit(raw2, tmp_path / "two", d2, t2, inv2.inventory_id)
    assert calls == [1, 1]
    assert a == b
    m["model_revision"] = "b" * 40
    raw3 = json.dumps(m).encode()
    inv3 = original(raw3, tmp_path / "one")
    d3 = d.model_copy(update={"checkpoint_revision": "b" * 40, "tokenizer_revision": "b" * 40})
    t3 = replace(t, model_revision="b" * 40)
    assert (
        embedding_space.admit(raw3, tmp_path / "one", d3, t3, inv3.inventory_id).space_id
        != a.space_id
    )


@pytest.mark.parametrize(
    "field,value",
    [
        ("checkpoint_sha256", "f" * 64),
        ("checkpoint_revision", "b" * 40),
        ("tokenizer_revision", "b" * 40),
        ("pooling", "mean"),
        ("normalize", False),
        ("dimensions", 512),
        ("query_prefix", "x"),
        ("model_name", "x" * 10000),
    ],
)
def test_definition_refused(tmp_path, field, value):
    _, raw, inv, d, t = fixture(tmp_path / "tree")
    with pytest.raises(embedding_space.SpaceRefused, match="^space admission refused$"):
        embedding_space.admit(
            raw, tmp_path / "tree", d.model_copy(update={field: value}), t, inv.inventory_id
        )


@pytest.mark.parametrize(
    "change",
    [
        "digest",
        "path",
        "revision",
        "role",
        "backend",
        "preprocessing",
        "expected",
        "bytes",
        "timeout",
        "shards",
    ],
)
def test_refusals(tmp_path, change):
    root = tmp_path / "tree"
    m, raw, inv, d, t = fixture(root)
    expected, timeout = inv.inventory_id, 30
    if change == "digest":
        t = replace(t, sha256="f" * 64)
    if change == "path":
        t = replace(t, artifact=root / "other")
    if change == "revision":
        t = replace(t, model_revision="b" * 40)
    if change == "role":
        t = replace(t, role="other")
    if change == "backend":
        t = replace(t, backend_version="other")
    if change == "preprocessing":
        t = replace(t, preprocessing="other")
    if change == "expected":
        expected = "f" * 64
    if change == "bytes":
        (root / "tokenizer.json").write_bytes(b"changed")
    if change == "timeout":
        timeout = 1e-100
    if change == "shards":
        entry = dict(m["files"][-1], path="second.safetensors")
        (root / entry["path"]).write_bytes((root / m["files"][-1]["path"]).read_bytes())
        (root / entry["path"]).chmod(0o600)
        m["files"].append(entry)
        raw = json.dumps(m).encode()
        expected = embedding_artifacts.verify_artifacts(raw, root).inventory_id
    with pytest.raises(embedding_space.SpaceRefused, match="^space admission refused$"):
        embedding_space.admit(raw, root, d, t, expected, timeout=timeout)


def test_preflight_before_file_work_and_private_error(tmp_path, monkeypatch):
    _, raw, inv, d, t = fixture(tmp_path / "tree")

    def forbidden(*args, **kwargs):
        pytest.fail("file work before preflight")

    monkeypatch.setattr(embedding_artifacts, "verify_artifacts", forbidden)
    with pytest.raises(embedding_space.SpaceRefused) as exc:
        embedding_space.admit(
            raw,
            tmp_path / "tree",
            d.model_copy(update={"model_name": "x" * 10000}),
            t,
            inv.inventory_id,
        )
    assert str(tmp_path) not in str(exc.value)
    with pytest.raises(embedding_space.SpaceRefused):
        embedding_space.admit(raw, str(tmp_path / "tree") + "/../tree", d, t, inv.inventory_id)


@pytest.mark.parametrize(
    "fmt,name", [("pytorch-state-dict", "pytorch_model.bin"), ("safetensors", "model.safetensors")]
)
def test_schema2_actual_files_and_space(tmp_path, fmt, name):
    root = tmp_path / "tree"
    m, _, old, d, t = fixture(root)
    weight = next(x for x in m["files"] if x["role"] == "weights")
    (root / weight["path"]).rename(root / name)
    weight["path"] = name
    m.update(schema=2, checkpoint_format=fmt)
    raw = json.dumps(m).encode()
    inv = embedding_artifacts.verify_artifacts(raw, root)
    admitted = embedding_space.admit(raw, root, d, t, inv.inventory_id)
    assert (admitted.inventory_schema, admitted.checkpoint_format) == (2, fmt)
    assert inv.inventory_id != old.inventory_id
    with pytest.raises(embedding_space.SpaceRefused):
        embedding_space.admit(raw, root, d, t, "0" * 64)
    m["checkpoint_format"] = "safetensors" if fmt == "pytorch-state-dict" else "pytorch-state-dict"
    with pytest.raises(embedding_artifacts.ArtifactRefused):
        embedding_artifacts.verify_artifacts(json.dumps(m).encode(), root)
