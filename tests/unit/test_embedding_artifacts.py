import hashlib
import json
import os
import secrets
import traceback

import pytest

from slaif_raggedized_helper.embedding_artifacts import ArtifactRefused, verify_artifacts


FIXED = {
    "config": ("config.json", {"model_type": "xlm-roberta", "hidden_size": 1024}),
    "tokenizer": ("tokenizer.json", b'{"synthetic":true}'),
    "tokenizer_config": ("tokenizer_config.json", {"model_max_length": 8192}),
    "special_tokens_map": ("special_tokens_map.json", {}),
    "modules": (
        "modules.json",
        [
            {"idx": 0, "name": "0", "path": "", "type": "sentence_transformers.models.Transformer"},
            {
                "idx": 1,
                "name": "1",
                "path": "1_Pooling",
                "type": "sentence_transformers.models.Pooling",
            },
            {
                "idx": 2,
                "name": "2",
                "path": "2_Normalize",
                "type": "sentence_transformers.models.Normalize",
            },
        ],
    ),
    "pooling": (
        "1_Pooling/config.json",
        {
            "word_embedding_dimension": 1024,
            "pooling_mode_cls_token": True,
            "pooling_mode_mean_tokens": False,
        },
    ),
    "sentence_bert_config": (
        "sentence_bert_config.json",
        {"max_seq_length": 8192, "do_lower_case": False},
    ),
    "sentence_transformers_config": (
        "config_sentence_transformers.json",
        {"__version__": {"sentence_transformers": "2.2.2"}},
    ),
    "weights": ("synthetic.safetensors", b"not real model weights"),
}


def encoded(value):
    return value if isinstance(value, bytes) else json.dumps(value).encode()


def setup_tree(root):
    root.mkdir(mode=0o700)
    entries = []
    for role, (name, value) in FIXED.items():
        data = encoded(value)
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.parent.chmod(0o700)
        path.write_bytes(data)
        path.chmod(0o600)
        entries.append(
            {
                "role": role,
                "path": name,
                "sha256": hashlib.sha256(data).hexdigest(),
                "size": len(data),
            }
        )
    return {"schema": 1, "model_name": "BAAI/bge-m3", "model_revision": "a" * 40, "files": entries}


def write_config(root, manifest, role, value):
    entry = next(x for x in manifest["files"] if x["role"] == role)
    data = encoded(value)
    (root / entry["path"]).write_bytes(data)
    entry.update(size=len(data), sha256=hashlib.sha256(data).hexdigest())


def check(root, manifest, **kwargs):
    return verify_artifacts(encoded(manifest), root, **kwargs)


def test_complete_and_deterministic(tmp_path):
    root = tmp_path / "tree"
    m = setup_tree(root)
    first = check(root, m)
    m["files"].reverse()
    assert check(root, m) == first
    assert len(first.inventory_id) == 64
    assert len(first.files) == 9


@pytest.mark.parametrize(
    "mutation",
    ["tamper", "size", "missing", "symlink", "directory", "worldwrite", "component", "rootlink"],
)
def test_filesystem_refusals(tmp_path, mutation):
    root = tmp_path / "tree"
    m = setup_tree(root)
    path = root / "config.json"
    if mutation == "tamper":
        path.write_bytes(b"x" * path.stat().st_size)
    elif mutation == "size":
        path.write_bytes(path.read_bytes() + b"x")
    elif mutation == "missing":
        path.unlink()
    elif mutation == "symlink":
        path.unlink()
        path.symlink_to(root / "tokenizer.json")
    elif mutation == "directory":
        path.unlink()
        path.mkdir()
    elif mutation == "worldwrite":
        path.chmod(0o666)
    elif mutation == "component":
        (root / "1_Pooling").chmod(0o777)
    else:
        link = tmp_path / "link"
        link.symlink_to(root, target_is_directory=True)
        root = link
    with pytest.raises(ArtifactRefused, match="^artifact verification refused$"):
        check(root, m)


@pytest.mark.parametrize(
    "mutation",
    [
        "duplicate_role",
        "duplicate_path",
        "bad_path",
        "url",
        "huge",
        "bool_size",
        "missing_role",
        "unknown",
        "weight",
    ],
)
def test_manifest_refusals(tmp_path, mutation):
    root = tmp_path / "tree"
    m = setup_tree(root)
    if mutation == "duplicate_role":
        m["files"].append(dict(m["files"][0], path="other"))
    elif mutation == "duplicate_path":
        m["files"][-1]["path"] = m["files"][0]["path"]
    elif mutation == "bad_path":
        m["files"][-1]["path"] = "../escape.safetensors"
    elif mutation == "url":
        m["files"][-1]["path"] = "https://x/y.safetensors"
    elif mutation == "huge":
        m["files"][-1]["size"] = 4 * 1024**3 + 1
    elif mutation == "bool_size":
        m["files"][-1]["size"] = True
    elif mutation == "missing_role":
        m["files"].pop()
    elif mutation == "unknown":
        m["surprise"] = 1
    else:
        m["files"][-1]["path"] = "weights.bin"
    with pytest.raises(ArtifactRefused):
        check(root, m)


def test_duplicate_json_and_deadline(tmp_path):
    root = tmp_path / "tree"
    m = setup_tree(root)
    with pytest.raises(ArtifactRefused):
        verify_artifacts(b'{"schema":1,"schema":1}', root)
    with pytest.raises(ArtifactRefused):
        check(root, m, timeout=0)
    with pytest.raises(ArtifactRefused):
        check(root, m, timeout=1e-100)


@pytest.mark.parametrize(
    ("role", "value"),
    [
        (
            "pooling",
            {
                "word_embedding_dimension": 1024,
                "pooling_mode_cls_token": False,
                "pooling_mode_mean_tokens": True,
            },
        ),
        ("pooling", {"word_embedding_dimension": 768, "pooling_mode_cls_token": True}),
        ("config", {"model_type": "xlm-roberta", "hidden_size": 768}),
        ("config", {"model_type": "xlm-roberta", "hidden_size": 1024, "auto_map": {}}),
        ("tokenizer_config", {"model_max_length": 8192, "tokenizer_class": "EvilTokenizer"}),
        ("modules", [{"idx": 0, "name": "0", "path": "", "type": "evil.Module"}]),
        ("sentence_bert_config", {"max_seq_length": 8192, "do_lower_case": True}),
        ("special_tokens_map", b'{"x":1,"x":2}'),
    ],
)
def test_coherent_but_unsafe_config(tmp_path, role, value):
    root = tmp_path / "tree"
    m = setup_tree(root)
    write_config(root, m, role, value)
    before = {p: p.read_bytes() for p in root.rglob("*") if p.is_file()}
    with pytest.raises(ArtifactRefused):
        check(root, m)
    assert before == {p: p.read_bytes() for p in root.rglob("*") if p.is_file()}


def test_concurrent_replacement(tmp_path, monkeypatch):
    root = tmp_path / "tree"
    m = setup_tree(root)
    original = os.read
    changed = False

    def replace(fd, size):
        nonlocal changed
        data = original(fd, size)
        if data and not changed and os.readlink(f"/proc/self/fd/{fd}") == str(root / "config.json"):
            changed = True
            path = root / "config.json"
            replacement = root / "new"
            replacement.write_bytes(path.read_bytes())
            replacement.chmod(0o600)
            replacement.replace(path)
        return data

    monkeypatch.setattr(os, "read", replace)
    with pytest.raises(ArtifactRefused):
        check(root, m)
    assert changed


def test_refuse_nonregular_fifo_and_root_permissions(tmp_path):
    root = tmp_path / "tree"
    m = setup_tree(root)
    target = root / "config.json"
    target.unlink()
    os.mkfifo(target, 0o600)
    with pytest.raises(ArtifactRefused):
        check(root, m)
    target.unlink()
    target.write_bytes(encoded(FIXED["config"][1]))
    target.chmod(0o600)
    root.chmod(0o720)
    with pytest.raises(ArtifactRefused):
        check(root, m)


def test_total_size_and_strict_json(tmp_path):
    root = tmp_path / "tree"
    m = setup_tree(root)
    for i in range(3):
        m["files"].append(
            {"role": "weights", "path": f"{i}.safetensors", "sha256": "a" * 64, "size": 4 * 1024**3}
        )
    with pytest.raises(ArtifactRefused):
        check(root, m)
    for bad in (b'{"x":NaN}', b" " * (256 * 1024 + 1)):
        with pytest.raises(ArtifactRefused):
            verify_artifacts(bad, root)


def test_timeout_during_stream(tmp_path, monkeypatch):
    import slaif_raggedized_helper.embedding_artifacts as artifacts

    root = tmp_path / "tree"
    m = setup_tree(root)
    real_read = os.read
    current = [0.0]
    monkeypatch.setattr(artifacts.time, "monotonic", lambda: current[0])

    def slow_read(fd, size):
        current[0] = 2.0
        return real_read(fd, size)

    monkeypatch.setattr(os, "read", slow_read)
    with pytest.raises(ArtifactRefused):
        check(root, m, timeout=1)


@pytest.mark.parametrize("encoding", ["utf-16", "utf-32"])
def test_reject_non_utf8_json(tmp_path, encoding):
    root = tmp_path / "tree"
    m = setup_tree(root)
    with pytest.raises(ArtifactRefused, match="^artifact verification refused$"):
        verify_artifacts(json.dumps(m).encode(encoding), root)
    write_config(root, m, "config", json.dumps(FIXED["config"][1]).encode(encoding))
    with pytest.raises(ArtifactRefused, match="^artifact verification refused$"):
        check(root, m)


def test_unicode_admission_and_privacy(tmp_path, monkeypatch):
    root = tmp_path / "tree"
    m = setup_tree(root)
    m["files"][-1]["path"] = "\ud800.safetensors"
    with monkeypatch.context() as patch:
        patch.setattr(os, "open", lambda *a, **k: pytest.fail("opened before admission"))
        with pytest.raises(ArtifactRefused, match="^artifact verification refused$"):
            check(root, m)
    m["files"][-1]["path"] = "é.safetensors"
    (root / "synthetic.safetensors").rename(root / "é.safetensors")
    write_config(
        root, m, "config", '{"model_type":"xlm-roberta","hidden_size":1024,"é":"é"}'.encode()
    )
    check(root, m)
    for payload, path in [
        (encoded(m), None),
        (b"\xff", root),
        (b"\xef\xbb\xbf{}", root),
        (b"[" * 2000, root),
    ]:
        with pytest.raises(ArtifactRefused, match="^artifact verification refused$"):
            verify_artifacts(payload, path)


def test_public_trace_suppresses_dynamic_path_and_path_object_errors(tmp_path, monkeypatch):
    manifest = setup_tree(tmp_path / "fixture")
    canary = secrets.token_hex(24)

    calls = []
    real_open = os.open

    def tracked_open(path, *args, **kwargs):
        if canary in os.fsdecode(path):
            calls.append("open")
        return real_open(path, *args, **kwargs)

    monkeypatch.setattr(os, "open", tracked_open)

    class BadPath:
        def __fspath__(self):
            calls.append("fspath")
            raise OSError(canary)

    for root in (tmp_path / canary, BadPath()):
        with pytest.raises(ArtifactRefused) as caught:
            verify_artifacts(encoded(manifest), root)
        assert str(caught.value) == "artifact verification refused"
        assert canary not in "".join(traceback.format_exception(caught.value))
    assert calls == ["open", "fspath"]
