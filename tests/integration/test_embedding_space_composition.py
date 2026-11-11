import hashlib
import json
import os
import secrets
import traceback
from dataclasses import replace

import pytest

from slaif_raggedized_helper import embedding_artifacts, embedding_space
from test_embedding_space import fixture


def update_config(root, manifest, role, changes):
    entry = next(e for e in manifest["files"] if e["role"] == role)
    path = root / entry["path"]
    config = json.loads(path.read_bytes())
    config.update(changes)
    data = json.dumps(config).encode()
    path.write_bytes(data)
    entry.update(size=len(data), sha256=hashlib.sha256(data).hexdigest())
    return json.dumps(manifest).encode()


def claim(manifest):
    canonical = dict(manifest, files=sorted(manifest["files"], key=lambda f: f["path"]))
    return hashlib.sha256(
        json.dumps(canonical, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    ).hexdigest()


def test_config_bytes_bind_space(tmp_path):
    root = tmp_path / "one"
    m, raw, inv, d, t = fixture(root)
    baseline = embedding_space.admit(raw, root, d, t, inv.inventory_id)
    _, raw2, inv2, d2, t2 = fixture(tmp_path / "two")
    assert embedding_space.admit(raw2, tmp_path / "two", d2, t2, inv2.inventory_id) == baseline
    changed = update_config(root, m, "config", {"test_metadata": "safe"})
    new = embedding_artifacts.verify_artifacts(changed, root)
    result = embedding_space.admit(changed, root, d, t, new.inventory_id)
    assert result.definition_fingerprint == baseline.definition_fingerprint
    assert result.tokenizer_sha256 == baseline.tokenizer_sha256
    assert new.inventory_id != inv.inventory_id and result.space_id != baseline.space_id
    with pytest.raises(embedding_space.SpaceRefused):
        embedding_space.admit(changed, root, d, t, inv.inventory_id)


@pytest.mark.parametrize(
    "changes", [{"word_embedding_dimension": 512}, {"pooling_mode_cls_token": False}]
)
def test_coherent_bad_semantics(tmp_path, monkeypatch, changes):
    root = tmp_path / "tree"
    m, raw, inv, d, t = fixture(root)
    real = embedding_artifacts.verify_artifacts
    calls = []

    def witness(*args, **kwargs):
        calls.append(1)
        return real(*args, **kwargs)

    monkeypatch.setattr(embedding_artifacts, "verify_artifacts", witness)
    embedding_space.admit(raw, root, d, t, inv.inventory_id)
    assert claim(m) == inv.inventory_id
    bad = update_config(root, m, "pooling", changes)
    with pytest.raises(embedding_space.SpaceRefused):
        embedding_space.admit(bad, root, d, t, claim(m))
    assert calls == [1, 1]


def test_private_missing_root(tmp_path, monkeypatch):
    root = tmp_path / "tree"
    _, raw, inv, d, t = fixture(root)
    assert embedding_space.admit(raw, root, d, t, inv.inventory_id).inventory_id == inv.inventory_id
    canary = secrets.token_hex(16)
    missing = tmp_path / canary
    real = os.open
    seen = []

    def witness(path, *args, **kwargs):
        if path == canary:
            seen.append(True)
        return real(path, *args, **kwargs)

    monkeypatch.setattr(os, "open", witness)
    with pytest.raises(embedding_space.SpaceRefused) as exc:
        embedding_space.admit(
            raw, missing, d, replace(t, artifact=missing / "tokenizer.json"), inv.inventory_id
        )
    assert seen and canary not in str(exc.value)
    assert canary not in "".join(traceback.format_exception(exc.value))


def test_shared_deadline(tmp_path, monkeypatch):
    root = tmp_path / "tree"
    _, raw, inv, d, t = fixture(root)
    real = embedding_artifacts.verify_artifacts
    clock = [100.0]
    calls = []
    monkeypatch.setattr(embedding_space.time, "monotonic", lambda: clock[0])

    def witness(*args, **kwargs):
        calls.append(kwargs["timeout"])
        result = real(*args, **kwargs)
        clock[0] += 31
        return result

    monkeypatch.setattr(embedding_artifacts, "verify_artifacts", witness)
    with pytest.raises(embedding_space.SpaceRefused):
        embedding_space.admit(raw, root, d, t, inv.inventory_id, timeout=30)
    assert len(calls) == 1 and 0 < calls[0] <= 30
