"""Real private-directory composition with synthetic original and derived stores."""

import hashlib
import os
import subprocess

import pytest

from slaif_raggedized_helper import raw_snapshot_directory as directory, raw_snapshot_files
# Existing fixture provider initializes this checkout’s unit helper path.
import test_retrieval_representation_composition  # noqa: F401
from test_raw_snapshot_files_composition import complete, rehash
from test_raw_snapshot_rows import enc
from test_raw_snapshot_source_rows_composition import actual  # noqa: F401


@pytest.fixture(autouse=True)
def restore_owned_directories(tmp_path):
    yield
    for current, dirs, _ in os.walk(tmp_path, topdown=True, followlinks=False):
        os.chmod(current, 0o700)
        for name in dirs:
            path = os.path.join(current, name)
            if not os.path.islink(path):
                os.chmod(path, 0o700)


def materialize(tmp_path, core, payloads):
    root = tmp_path / "private"
    target = root / "snapshots" / hashlib.sha256(core).hexdigest()
    target.mkdir(parents=True)
    (target / ".core.json").write_bytes(core)
    for path, data in payloads:
        file = target / path
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_bytes(data)
    for path in target.rglob("*"):
        path.chmod(0o500 if path.is_dir() else 0o400)
    target.chmod(0o500)
    root.chmod(0o700)
    (root / "snapshots").chmod(0o700)
    return root, target, "sha256:" + target.name


def test_complete_and_closed_tree(actual, tmp_path, monkeypatch):  # noqa: F811
    originals, derived, mapping, bundle, _, _ = actual
    core, payloads = complete(originals, derived, mapping, (bundle,))
    wire = enc(core)
    expected = raw_snapshot_files.validate_files(originals, derived, wire, payloads)
    root, target, snapshot_id = materialize(tmp_path, wire, payloads)

    def forbidden(*args, **kwargs):
        raise AssertionError("unexpected side effect")

    with monkeypatch.context() as patch:
        patch.setattr(subprocess, "Popen", forbidden)
        patch.setattr(os, "write", forbidden)
        assert directory.load_directory(originals, derived, str(root), snapshot_id) == expected
    with pytest.raises(directory.DirectoryError):
        directory.load_directory(originals, derived, str(root), "sha256:" + "0" * 64)
    target.chmod(0o700)
    (target / "extra").write_bytes(b"x")
    (target / "extra").chmod(0o400)
    target.chmod(0o500)
    with pytest.raises(directory.DirectoryError):
        directory.load_directory(originals, derived, str(root), snapshot_id)


def test_empty_and_hardlink(actual, tmp_path):  # noqa: F811
    originals, derived, mapping, bundle, _, _ = actual
    mapping["rows"] = []
    core, payloads = complete(originals, derived, mapping, (bundle,))
    wire = enc(core)
    root, target, snapshot_id = materialize(tmp_path, wire, payloads)
    assert directory.load_directory(
        originals, derived, str(root), snapshot_id
    ) == raw_snapshot_files.validate_files(originals, derived, wire, payloads)
    os.link(target / payloads[0][0], tmp_path / "alias")
    with pytest.raises(directory.DirectoryError):
        directory.load_directory(originals, derived, str(root), snapshot_id)


def test_fresh_corruption(actual, tmp_path):  # noqa: F811
    originals, derived, mapping, bundle, _, _ = actual
    core, payloads = complete(originals, derived, mapping, (bundle,))
    wire = rehash(core, payloads)
    root, _, snapshot_id = materialize(tmp_path, wire, payloads)
    blob = next((originals.root / "blobs").iterdir())
    old = blob.read_bytes()
    try:
        blob.write_bytes(b"corrupt")
        with pytest.raises(directory.DirectoryError):
            directory.load_directory(originals, derived, str(root), snapshot_id)
    finally:
        blob.write_bytes(old)


def test_actual_hardlink_control(actual, tmp_path):  # noqa: F811
    import sys
    import types

    originals, derived, mapping, bundle, _, _ = actual
    core, payloads = complete(originals, derived, mapping, (bundle,))
    wire = enc(core)
    root, target, snapshot_id = materialize(tmp_path, wire, payloads)
    os.link(target / payloads[0][0], tmp_path / "outside-alias")
    with pytest.raises(directory.DirectoryError):
        directory.load_directory(originals, derived, str(root), snapshot_id)
    source = open(directory.__file__, "rb").read()
    needle = b"_check(st.st_nlink == 1)"
    assert source.count(needle) == 1
    mutant = source.replace(needle, b"_check(True)")
    name = "slaif_raggedized_helper._directory_control"
    module = types.ModuleType(name)
    module.__package__ = directory.__package__
    sys.modules[name] = module
    try:
        exec(compile(mutant, "<owned-control>", "exec"), module.__dict__)
        assert module.load_directory(
            originals, derived, str(root), snapshot_id
        ) == raw_snapshot_files.validate_files(originals, derived, wire, payloads)
    finally:
        del sys.modules[name]
    with pytest.raises(directory.DirectoryError):
        directory.load_directory(originals, derived, str(root), snapshot_id)
    print("source_sha256=" + hashlib.sha256(source).hexdigest())
    print("mutant_sha256=" + hashlib.sha256(mutant).hexdigest())


def test_replacement_while_pinned(actual, tmp_path, monkeypatch):  # noqa: F811
    originals, derived, mapping, bundle, _, _ = actual
    core, payloads = complete(originals, derived, mapping, (bundle,))
    root, target, snapshot_id = materialize(tmp_path, enc(core), payloads)
    original_walk = directory._walk
    calls = []

    def swap(*args):
        result = original_walk(*args)
        if not calls:
            calls.append(True)
            parent = target.parent
            parent.chmod(0o700)
            target.rename(parent / "displaced")
            target.mkdir(mode=0o500)
        return result

    monkeypatch.setattr(directory, "_walk", swap)
    with pytest.raises(directory.DirectoryError):
        directory.load_directory(originals, derived, str(root), snapshot_id)
    assert calls


def test_metadata_symlink_and_bytes(actual, tmp_path):  # noqa: F811
    originals, derived, mapping, bundle, _, _ = actual
    core, payloads = complete(originals, derived, mapping, (bundle,))
    root, target, snapshot_id = materialize(tmp_path, enc(core), payloads)
    file = target / payloads[0][0]
    old = file.read_bytes()
    file.chmod(0o600)
    with pytest.raises(directory.DirectoryError):
        directory.load_directory(originals, derived, str(root), snapshot_id)
    file.write_bytes(old + b"x")
    file.chmod(0o400)
    with pytest.raises(directory.DirectoryError):
        directory.load_directory(originals, derived, str(root), snapshot_id)
    file.chmod(0o600)
    file.write_bytes(old)
    file.chmod(0o400)
    parent = file.parent
    parent.chmod(0o700)
    file.unlink()
    file.symlink_to(tmp_path / "outside")
    parent.chmod(0o500)
    with pytest.raises(directory.DirectoryError):
        directory.load_directory(originals, derived, str(root), snapshot_id)


def test_semantic_dense_corruption_with_updated_hash(actual, tmp_path):  # noqa: F811
    import numpy as np
    from slaif_raggedized_helper import raw_snapshot_dense, vector_codec

    originals, derived, mapping, bundle, _, _ = actual
    core, payloads = complete(originals, derived, mapping, (bundle,))
    changed = dict(payloads)
    path = core["partitions"][0]["dense_path"]
    changed[path] = vector_codec.encode(
        np.eye(3, 1024, dtype="<f4")[[1, 0, 2]], raw_snapshot_dense.POLICY
    ).container
    supplied = tuple(sorted(changed.items()))
    root, _, snapshot_id = materialize(tmp_path, rehash(core, supplied), supplied)
    with pytest.raises(directory.DirectoryError):
        directory.load_directory(originals, derived, str(root), snapshot_id)


def test_prefix_collision_and_core_hash(actual, tmp_path):  # noqa: F811
    originals, derived, mapping, bundle, _, _ = actual
    mapping["rows"] = []
    core, payloads = complete(originals, derived, mapping, (bundle,))
    # Two valid core descriptors are physically incompatible as file and directory.
    old = core["membership_path"]
    core["membership_path"] = core["row_map_path"] + "/child"
    for desc in core["files"]:
        if desc["path"] == old:
            desc["path"] = core["membership_path"]
    core["files"].sort(key=lambda item: item["path"])
    wire = enc(core)
    root = tmp_path / "private"
    target = root / "snapshots" / hashlib.sha256(wire).hexdigest()
    target.mkdir(parents=True)
    (target / ".core.json").write_bytes(wire)
    (target / ".core.json").chmod(0o400)
    target.chmod(0o500)
    root.chmod(0o700)
    (root / "snapshots").chmod(0o700)
    with pytest.raises(directory.DirectoryError):
        directory.load_directory(originals, derived, str(root), "sha256:" + target.name)
    target.chmod(0o700)
    (target / ".core.json").chmod(0o600)
    (target / ".core.json").write_bytes(wire + b"x")
    (target / ".core.json").chmod(0o400)
    target.chmod(0o500)
    with pytest.raises(directory.DirectoryError):
        directory.load_directory(originals, derived, str(root), "sha256:" + target.name)


def test_root_alias_and_directory_in_file_position(actual, tmp_path):  # noqa: F811
    originals, derived, mapping, bundle, _, _ = actual
    core, payloads = complete(originals, derived, mapping, (bundle,))
    root, target, snapshot_id = materialize(tmp_path, enc(core), payloads)
    alias = tmp_path / "root-alias"
    alias.symlink_to(root, target_is_directory=True)
    with pytest.raises(directory.DirectoryError):
        directory.load_directory(originals, derived, str(alias), snapshot_id)
    root.chmod(0o750)
    with pytest.raises(directory.DirectoryError):
        directory.load_directory(originals, derived, str(root), snapshot_id)
    root.chmod(0o700)
    file = target / payloads[0][0]
    parent = file.parent
    parent.chmod(0o700)
    file.unlink()
    file.mkdir(mode=0o500)
    parent.chmod(0o500)
    with pytest.raises(directory.DirectoryError):
        directory.load_directory(originals, derived, str(root), snapshot_id)
