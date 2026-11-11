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
    original_open = embedding_artifacts._open_file
    original_admit = embedding_space.admit
    copying = False
    calls = []

    def admit(*args, **kwargs):
        nonlocal copying
        result = original_admit(*args, **kwargs)
        copying = True
        return result

    def interrupted(*args):
        if copying:
            calls.append(True)
            raise OSError("interrupted private path")
        return original_open(*args)

    monkeypatch.setattr(embedding_space, "admit", admit)
    monkeypatch.setattr(embedding_artifacts, "_open_file", interrupted)
    with pytest.raises(embedding_staging.StagingRefused):
        with embedding_staging.stage(raw, root, d, t, inv.inventory_id, parent=tmp_path):
            pytest.fail("unexpected stage")
    assert calls == [True]
    assert sorted(p.name for p in tmp_path.iterdir()) == ["source"]


def test_parent_swap_is_refused_and_owned_tree_cleaned(tmp_path, monkeypatch):
    import os

    root = tmp_path / "source"
    _, raw, inv, d, t = fixture(root)
    embedding_space.admit(raw, root, d, t, inv.inventory_id)
    parent = tmp_path / "parent"
    parent.mkdir(mode=0o700)
    moved = tmp_path / "moved"
    foreign = tmp_path / "foreign"
    foreign.mkdir(mode=0o700)
    (foreign / "keep").write_bytes(b"keep")
    real = os.mkdir
    calls = []

    def swap(name, mode=0o777, *, dir_fd=None):
        if str(name).startswith("embedding-stage-"):
            calls.append(dir_fd)
            parent.rename(moved)
            parent.symlink_to(foreign, target_is_directory=True)
        return real(name, mode, dir_fd=dir_fd)

    monkeypatch.setattr(os, "mkdir", swap)
    with pytest.raises(embedding_staging.StagingRefused, match="^staging refused$"):
        with embedding_staging.stage(raw, root, d, t, inv.inventory_id, parent=parent):
            pytest.fail("replacement parent admitted")
    assert len(calls) == 1 and calls[0] is not None
    assert list(moved.iterdir()) == []
    assert [(p.name, p.read_bytes()) for p in foreign.iterdir()] == [("keep", b"keep")]


def test_mutation_during_copy_refused(tmp_path, monkeypatch):
    import os

    root = tmp_path / "source"
    _, raw, inv, d, t = fixture(root)
    embedding_space.admit(raw, root, d, t, inv.inventory_id)
    original_admit = embedding_space.admit
    original_read = os.read
    copying = False
    changed = []

    def admit(*args, **kwargs):
        nonlocal copying
        result = original_admit(*args, **kwargs)
        copying = True
        return result

    def read(fd, size):
        data = original_read(fd, size)
        if copying and data and not changed:
            target = os.readlink(f"/proc/self/fd/{fd}")
            if target == str(root / "tokenizer.json"):
                (root / "tokenizer.json").write_bytes(b"X" * len(data))
                changed.append(True)
        return data

    monkeypatch.setattr(embedding_space, "admit", admit)
    monkeypatch.setattr(os, "read", read)
    with pytest.raises(embedding_staging.StagingRefused):
        with embedding_staging.stage(raw, root, d, t, inv.inventory_id, parent=tmp_path):
            pytest.fail("changed source admitted")
    assert changed == [True]
    assert sorted(p.name for p in tmp_path.iterdir()) == ["source"]


def test_shared_deadline_expires_after_first_admission(tmp_path, monkeypatch):
    root = tmp_path / "source"
    _, raw, inv, d, t = fixture(root)
    embedding_space.admit(raw, root, d, t, inv.inventory_id)
    original = embedding_space.admit
    clock = [100.0]
    timeouts = []
    monkeypatch.setattr(embedding_staging.time, "monotonic", lambda: clock[0])

    def delayed(*args, **kwargs):
        timeouts.append(kwargs["timeout"])
        result = original(*args, **kwargs)
        clock[0] += 3
        return result

    monkeypatch.setattr(embedding_space, "admit", delayed)
    with pytest.raises(embedding_staging.StagingRefused):
        with embedding_staging.stage(raw, root, d, t, inv.inventory_id, parent=tmp_path, timeout=2):
            pytest.fail("expired stage admitted")
    assert timeouts == [2]
    assert sorted(p.name for p in tmp_path.iterdir()) == ["source"]


def test_refusal_traceback_is_sanitized(tmp_path):
    import traceback

    root = tmp_path / "source"
    _, raw, inv, d, t = fixture(root)
    embedding_space.admit(raw, root, d, t, inv.inventory_id)
    secret = "private-parent-canary-12345"
    with pytest.raises(embedding_staging.StagingRefused) as caught:
        with embedding_staging.stage(raw, root, d, t, inv.inventory_id, parent=tmp_path / secret):
            pytest.fail("missing parent admitted")
    assert secret not in str(caught.value)
    assert secret not in "".join(traceback.format_exception(caught.value))


@pytest.mark.parametrize("timeout", [0, -1, 121, float("nan"), float("inf"), True, "1"])
def test_timeout_validation(tmp_path, timeout):
    root = tmp_path / "source"
    _, raw, inv, d, t = fixture(root)
    embedding_space.admit(raw, root, d, t, inv.inventory_id)
    with pytest.raises(embedding_staging.StagingRefused):
        with embedding_staging.stage(raw, root, d, t, inv.inventory_id, timeout=timeout):
            pytest.fail("invalid timeout admitted")


def test_cleanup_failure_preserves_caller_exception(tmp_path, monkeypatch):
    root = tmp_path / "source"
    _, raw, inv, d, t = fixture(root)
    embedding_space.admit(raw, root, d, t, inv.inventory_id)
    original = embedding_staging._cleanup

    def failing(entries):
        original(entries)
        raise RuntimeError("staging cleanup failed")

    monkeypatch.setattr(embedding_staging, "_cleanup", failing)
    with pytest.raises(LookupError, match="caller") as exc:
        with embedding_staging.stage(raw, root, d, t, inv.inventory_id, parent=tmp_path):
            raise LookupError("caller")
    assert exc.value.__notes__ == ["staging cleanup failed"]
    assert sorted(p.name for p in tmp_path.iterdir()) == ["source"]


@pytest.mark.parametrize("change", ["same_size", "longer", "shorter"])
def test_bytes_changed_before_copy_refused(tmp_path, monkeypatch, change):
    root = tmp_path / "source"
    _, raw, inv, d, t = fixture(root)
    embedding_space.admit(raw, root, d, t, inv.inventory_id)
    original = embedding_space.admit
    changed = []

    def mutate(*args, **kwargs):
        result = original(*args, **kwargs)
        target = root / "tokenizer.json"
        data = target.read_bytes()
        replacement = {"same_size": b"x" * len(data), "longer": data + b"x", "shorter": b""}
        target.write_bytes(replacement[change])
        changed.append(True)
        return result

    monkeypatch.setattr(embedding_space, "admit", mutate)
    with pytest.raises(embedding_staging.StagingRefused):
        with embedding_staging.stage(raw, root, d, t, inv.inventory_id, parent=tmp_path):
            pytest.fail("changed source admitted")
    assert changed == [True]
    assert sorted(p.name for p in tmp_path.iterdir()) == ["source"]


def test_write_interruption_removes_partial_files(tmp_path, monkeypatch):
    import os

    root = tmp_path / "source"
    _, raw, inv, d, t = fixture(root)
    embedding_space.admit(raw, root, d, t, inv.inventory_id)
    original = os.write
    writes = []

    def interrupted(fd, data):
        writes.append(len(data))
        if len(writes) == 1:
            return original(fd, data[:1])
        raise OSError("injected copy failure")

    monkeypatch.setattr(os, "write", interrupted)
    with pytest.raises(embedding_staging.StagingRefused):
        with embedding_staging.stage(raw, root, d, t, inv.inventory_id, parent=tmp_path):
            pytest.fail("partial copy admitted")
    assert len(writes) == 2
    assert sorted(p.name for p in tmp_path.iterdir()) == ["source"]


def test_deadline_expires_during_copy(tmp_path, monkeypatch):
    import os

    root = tmp_path / "source"
    _, raw, inv, d, t = fixture(root)
    embedding_space.admit(raw, root, d, t, inv.inventory_id)
    original_admit = embedding_space.admit
    original_read = os.read
    clock = [100.0]
    copying = False
    reads = []
    monkeypatch.setattr(embedding_staging.time, "monotonic", lambda: clock[0])

    def admitted(*args, **kwargs):
        nonlocal copying
        result = original_admit(*args, **kwargs)
        copying = True
        return result

    def delayed(fd, size):
        result = original_read(fd, size)
        if copying and result:
            reads.append(size)
            clock[0] += 3
        return result

    monkeypatch.setattr(embedding_space, "admit", admitted)
    monkeypatch.setattr(os, "read", delayed)
    with pytest.raises(embedding_staging.StagingRefused):
        with embedding_staging.stage(raw, root, d, t, inv.inventory_id, parent=tmp_path, timeout=2):
            pytest.fail("expired copy admitted")
    assert reads == [65536]
    assert sorted(p.name for p in tmp_path.iterdir()) == ["source"]


def test_source_and_parent_symlink_refusal(tmp_path):
    from dataclasses import replace

    root = tmp_path / "source"
    _, raw, inv, d, t = fixture(root)
    embedding_space.admit(raw, root, d, t, inv.inventory_id)
    link = tmp_path / "link"
    link.symlink_to(root, target_is_directory=True)
    with pytest.raises(embedding_staging.StagingRefused):
        with embedding_staging.stage(raw, link, d, replace(t, artifact=link / "tokenizer.json"),
                                     inv.inventory_id):
            pytest.fail("symlink source admitted")
    with pytest.raises(embedding_staging.StagingRefused):
        with embedding_staging.stage(raw, root, d, t, inv.inventory_id, parent=link):
            pytest.fail("symlink parent admitted")


@pytest.mark.parametrize("case", ["file", "total"])
def test_manifest_size_bounds_without_allocation(tmp_path, case):
    root = tmp_path / "source"
    manifest, raw, inv, d, t = fixture(root)
    embedding_space.admit(raw, root, d, t, inv.inventory_id)
    weight = next(entry for entry in manifest["files"] if entry["role"] == "weights")
    if case == "file":
        weight["size"] = 4 * 1024**3 + 1
    else:
        fixed_total = sum(entry["size"] for entry in manifest["files"] if entry is not weight)
        weight["size"] = 4 * 1024**3
        second = dict(weight, path="second.safetensors", size=4 * 1024**3 - fixed_total)
        manifest["files"].append(second)
        embedding_artifacts._admit(json.dumps(manifest).encode())
        second["size"] += 1
    oversized = json.dumps(manifest).encode()
    with pytest.raises(embedding_artifacts.ArtifactRefused):
        embedding_artifacts._admit(oversized)
    with pytest.raises(embedding_staging.StagingRefused):
        with embedding_staging.stage(oversized, root, d, t, inv.inventory_id):
            pytest.fail("oversized manifest admitted")


@pytest.mark.parametrize("case", ["root", "nested"])
def test_directory_open_failure_cleans_created_directory(tmp_path, monkeypatch, case):
    import errno
    import os

    root = tmp_path / "source"
    _, raw, inv, d, t = fixture(root)
    embedding_space.admit(raw, root, d, t, inv.inventory_id)
    parent = tmp_path / "parent"
    parent.mkdir(mode=0o700)
    with embedding_staging.stage(raw, root, d, t, inv.inventory_id, parent=parent) as staged:
        assert staged.space.inventory_id == inv.inventory_id
    assert list(parent.iterdir()) == []
    original = os.open
    original_mkdir = os.mkdir
    reached = []
    created = []

    def mkdir(name, mode=0o777, *, dir_fd=None):
        result = original_mkdir(name, mode, dir_fd=dir_fd)
        if str(name).startswith("embedding-stage-"):
            created.append(True)
        return result

    def fail(name, flags, mode=0o777, *, dir_fd=None):
        leaf = os.fspath(name)
        targeted = ((case == "root" and leaf.startswith("embedding-stage-")) or
                    (case == "nested" and leaf == "1_Pooling"))
        if created and targeted and dir_fd is not None and flags & os.O_DIRECTORY:
            reached.append(True)
            raise OSError(errno.EMFILE, "injected descriptor exhaustion")
        return original(name, flags, mode, dir_fd=dir_fd)

    monkeypatch.setattr(os, "mkdir", mkdir)
    monkeypatch.setattr(os, "open", fail)
    with pytest.raises(embedding_staging.StagingRefused, match="^staging refused$") as exc:
        with embedding_staging.stage(raw, root, d, t, inv.inventory_id, parent=parent):
            pytest.fail("directory open unexpectedly succeeded")
    assert created == [True] and reached == [True]
    assert not getattr(exc.value, "__notes__", [])
    assert list(parent.iterdir()) == []
