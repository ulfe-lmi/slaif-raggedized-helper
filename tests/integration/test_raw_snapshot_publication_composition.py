"""Original-backed publication and actual private filesystem checks."""

import hashlib

import pytest

from slaif_raggedized_helper import raw_snapshot_publication as publication
from test_raw_snapshot_directory_composition import restore_owned_directories  # noqa: F401
from test_raw_snapshot_files_composition import complete
from test_raw_snapshot_rows import enc
from test_raw_snapshot_source_rows_composition import actual  # noqa: F401


def stable_stat(item):
    st = item.stat() if hasattr(item, "stat") else item
    return st.st_ino, st.st_mode, st.st_mtime_ns, st.st_ctime_ns


def fixture(actual, tmp_path):  # noqa: F811
    originals, derived, mapping, bundle, _, _ = actual
    core, files = complete(originals, derived, mapping, (bundle,))
    root = tmp_path / "private"
    root.mkdir(mode=0o700)
    return originals, derived, enc(core), files, root


def test_roundtrip_and_reuse(actual, tmp_path):  # noqa: F811
    originals, derived, core, files, root = fixture(actual, tmp_path)
    first = publication.publish_directory(originals, derived, str(root), core, files)
    assert first.created and first.snapshot_id == "sha256:" + hashlib.sha256(core).hexdigest()
    target = root / "snapshots" / first.snapshot_id[7:]
    before = target.stat()
    second = publication.publish_directory(originals, derived, str(root), core, files)
    assert not second.created and second.data == first.data
    assert stable_stat(target) == stable_stat(before)
    assert target.stat().st_mode & 0o777 == 0o500
    assert (target / ".core.json").read_bytes() == core
    for path, blob in files:
        assert (target / path).read_bytes() == blob
        assert (target / path).stat().st_mode & 0o777 == 0o400


def test_existing_empty_is_never_replaced(actual, tmp_path, monkeypatch):  # noqa: F811
    originals, derived, core, files, root = fixture(actual, tmp_path)
    snapshots = root / "snapshots"
    snapshots.mkdir(mode=0o700)
    target = snapshots / hashlib.sha256(core).hexdigest()
    target.mkdir(mode=0o500)
    before = target.stat()
    rename = publication._rename_noreplace
    observed = []

    def record(parent, old, new):
        try:
            return rename(parent, old, new)
        except OSError as exc:
            observed.append(exc.errno)
            raise

    monkeypatch.setattr(publication, "_rename_noreplace", record)
    with pytest.raises(publication.PublicationError):
        publication.publish_directory(originals, derived, str(root), core, files)
    assert stable_stat(target) == stable_stat(before) and list(target.iterdir()) == []
    assert list((root / "snapshots").iterdir()) == [target]
    import errno

    assert observed == [errno.EEXIST]


def test_bad_input_before_mutation(actual, tmp_path):  # noqa: F811
    originals, derived, core, files, root = fixture(actual, tmp_path)
    bad = list(files)
    path, blob = bad[0]
    bad[0] = (path, blob + b"x")
    with pytest.raises(publication.PublicationError):
        publication.publish_directory(originals, derived, str(root), core, tuple(bad))
    assert list(root.iterdir()) == []


def test_fsync_failure_leaves_final(actual, tmp_path, monkeypatch):  # noqa: F811
    originals, derived, core, files, root = fixture(actual, tmp_path)
    original = publication._rename_noreplace

    def rename_then_fail(parent, old, new):
        original(parent, old, new)
        raise OSError("uncertain")

    monkeypatch.setattr(publication, "_rename_noreplace", rename_then_fail)
    with pytest.raises(publication.PublicationError) as exc:
        publication.publish_directory(originals, derived, str(root), core, files)
    assert exc.value.publication_may_exist
    assert (root / "snapshots" / hashlib.sha256(core).hexdigest()).is_dir()


def test_concurrent_same_id(actual, tmp_path):  # noqa: F811
    import multiprocessing

    originals, derived, core, files, root = fixture(actual, tmp_path)
    context = multiprocessing.get_context("fork")
    gate = context.Barrier(2, timeout=20)
    output = context.Queue()

    def worker():
        try:
            gate.wait()
            result = publication.publish_directory(originals, derived, str(root), core, files)
            output.put((result.created, result.snapshot_id))
        except BaseException as exc:
            output.put(("error", type(exc).__name__))

    children = [context.Process(target=worker) for _ in range(2)]
    for child in children:
        child.start()
    try:
        results = [output.get(timeout=30) for _ in children]
        for child in children:
            child.join(timeout=5)
            assert child.exitcode == 0
    finally:
        for child in children:
            if child.is_alive():
                child.terminate()
                child.join()
    sid = "sha256:" + hashlib.sha256(core).hexdigest()
    assert set(results) == {(False, sid), (True, sid)}, results
    assert len({snapshot_id for _, snapshot_id in results}) == 1
    assert len(list((root / "snapshots").iterdir())) == 1


def test_source_change_after_staging(actual, tmp_path, monkeypatch):  # noqa: F811
    originals, derived, core, files, root = fixture(actual, tmp_path)
    blob = next((originals.root / "blobs").iterdir())
    original_bytes = blob.read_bytes()
    original = publication._rename_noreplace

    def change(parent, old, new):
        original(parent, old, new)
        blob.write_bytes(b"corrupt")

    monkeypatch.setattr(publication, "_rename_noreplace", change)
    try:
        with pytest.raises(publication.PublicationError) as exc:
            publication.publish_directory(originals, derived, str(root), core, files)
        assert exc.value.publication_may_exist
        assert (root / "snapshots" / hashlib.sha256(core).hexdigest()).is_dir()
    finally:
        blob.write_bytes(original_bytes)


def test_pre_rename_failure_cleans_own_tree(actual, tmp_path, monkeypatch):  # noqa: F811
    originals, derived, core, files, root = fixture(actual, tmp_path)

    def fail(*args):
        raise OSError("controlled failure")

    monkeypatch.setattr(publication, "_rename_noreplace", fail)
    with pytest.raises(publication.PublicationError):
        publication.publish_directory(originals, derived, str(root), core, files)
    assert list((root / "snapshots").iterdir()) == []


def test_configured_root_replaced_after_rename(actual, tmp_path, monkeypatch):  # noqa: F811
    originals, derived, core, files, root = fixture(actual, tmp_path)
    original = publication._rename_noreplace

    def swap(parent, old, new):
        original(parent, old, new)
        root.rename(tmp_path / "displaced")
        root.mkdir(mode=0o700)

    monkeypatch.setattr(publication, "_rename_noreplace", swap)
    with pytest.raises(publication.PublicationError) as exc:
        publication.publish_directory(originals, derived, str(root), core, files)
    assert exc.value.publication_may_exist
    assert (tmp_path / "displaced" / "snapshots" / hashlib.sha256(core).hexdigest()).is_dir()
    assert list(root.iterdir()) == []


def test_post_rename_parent_fsync_failure(actual, tmp_path, monkeypatch):  # noqa: F811
    originals, derived, core, files, root = fixture(actual, tmp_path)
    rename = publication._rename_noreplace
    fsync = publication.os.fsync
    changed = []

    def publish(parent, old, new):
        rename(parent, old, new)
        changed.append(parent)

    def fail(fd):
        if changed and fd == changed[0]:
            raise OSError("controlled fsync")
        return fsync(fd)

    monkeypatch.setattr(publication, "_rename_noreplace", publish)
    monkeypatch.setattr(publication.os, "fsync", fail)
    with pytest.raises(publication.PublicationError) as exc:
        publication.publish_directory(originals, derived, str(root), core, files)
    assert exc.value.publication_may_exist
    assert (root / "snapshots" / hashlib.sha256(core).hexdigest()).is_dir()


def test_interrupt_after_rename_preserves_identity(actual, tmp_path, monkeypatch):  # noqa: F811
    originals, derived, core, files, root = fixture(actual, tmp_path)
    rename = publication._rename_noreplace
    interruption = KeyboardInterrupt("control")

    def interrupt(parent, old, new):
        rename(parent, old, new)
        raise interruption

    monkeypatch.setattr(publication, "_rename_noreplace", interrupt)
    with pytest.raises(KeyboardInterrupt) as exc:
        publication.publish_directory(originals, derived, str(root), core, files)
    assert exc.value is interruption
    assert (root / "snapshots" / hashlib.sha256(core).hexdigest()).is_dir()


def test_unsafe_existing_root_and_corrupt_target(actual, tmp_path):  # noqa: F811
    originals, derived, core, files, root = fixture(actual, tmp_path)
    root.chmod(0o755)
    with pytest.raises(publication.PublicationError):
        publication.publish_directory(originals, derived, str(root), core, files)
    assert list(root.iterdir()) == []
    root.chmod(0o700)
    result = publication.publish_directory(originals, derived, str(root), core, files)
    target = root / "snapshots" / result.snapshot_id[7:]
    target.chmod(0o700)
    extra = target / "extra"
    extra.write_bytes(b"x")
    extra.chmod(0o400)
    target.chmod(0o500)
    before = (target.stat().st_ino, extra.stat().st_ino, extra.read_bytes())
    with pytest.raises(publication.PublicationError):
        publication.publish_directory(originals, derived, str(root), core, files)
    assert before == (target.stat().st_ino, extra.stat().st_ino, extra.read_bytes())


def test_cleanup_failure_retains_owner_for_creator_retry(actual, tmp_path, monkeypatch):  # noqa: F811
    originals, derived, core, files, root = fixture(actual, tmp_path)

    def fail_rename(*args):
        raise OSError("controlled rename")

    unlink = publication.os.unlink

    def fail_unlink(*args, **kwargs):
        raise OSError("controlled cleanup")

    monkeypatch.setattr(publication, "_rename_noreplace", fail_rename)
    monkeypatch.setattr(publication.os, "unlink", fail_unlink)
    before = len(publication._pending)
    with pytest.raises(publication.PublicationError):
        publication.publish_directory(originals, derived, str(root), core, files)
    assert len(publication._pending) == before + 1
    owner = publication._pending[-1]
    assert owner.temp is not None and owner.owner.fds
    monkeypatch.setattr(publication.os, "unlink", unlink)
    assert owner.retry_cleanup() is None
    assert owner not in publication._pending
    assert list((root / "snapshots").iterdir()) == []


def test_unknown_close_is_not_retried(actual, tmp_path, monkeypatch):  # noqa: F811
    originals, derived, core, files, root = fixture(actual, tmp_path)
    rename = publication._rename_noreplace
    close = publication.os.close
    active = []

    def arm(parent, old, new):
        rename(parent, old, new)
        active.append(True)

    def uncertain(fd):
        if active:
            active.pop()
            close(fd)
            raise OSError("unknown close outcome")
        close(fd)

    monkeypatch.setattr(publication, "_rename_noreplace", arm)
    monkeypatch.setattr(publication.os, "close", uncertain)
    before = len(publication._pending)
    with pytest.raises(publication.PublicationError):
        publication.publish_directory(originals, derived, str(root), core, files)
    assert len(publication._pending) == before + 1
    owner = publication._pending[-1]
    assert owner.owner.unknown
    assert isinstance(owner.retry_cleanup(), publication.CleanupPendingError)
    assert owner in publication._pending and owner.owner.unknown
    assert (root / "snapshots" / hashlib.sha256(core).hexdigest()).is_dir()


def test_missing_member_and_hardlink_existing_target(actual, tmp_path):  # noqa: F811
    import os

    originals, derived, core, files, root = fixture(actual, tmp_path)
    result = publication.publish_directory(originals, derived, str(root), core, files)
    target = root / "snapshots" / result.snapshot_id[7:]
    member = target / files[0][0]
    alias = tmp_path / "hardlink"
    os.link(member, alias)
    with pytest.raises(publication.PublicationError):
        publication.publish_directory(originals, derived, str(root), core, files)
    alias.unlink()
    parent = member.parent
    parent.chmod(0o700)
    member.unlink()
    parent.chmod(0o500)
    with pytest.raises(publication.PublicationError):
        publication.publish_directory(originals, derived, str(root), core, files)
    assert not member.exists()


def test_symlink_root_rejected(actual, tmp_path):  # noqa: F811
    originals, derived, core, files, root = fixture(actual, tmp_path)
    alias = tmp_path / "alias"
    alias.symlink_to(root, target_is_directory=True)
    with pytest.raises(publication.PublicationError):
        publication.publish_directory(originals, derived, str(alias), core, files)
    assert list(root.iterdir()) == []


def test_prefix_collision_before_mutation(actual, tmp_path):  # noqa: F811
    originals, derived, mapping, bundle, _, _ = actual
    core, files = complete(originals, derived, mapping, (bundle,))
    old = core["membership_path"]
    new = core["row_map_path"] + "/child"
    core["membership_path"] = new
    for desc in core["files"]:
        if desc["path"] == old:
            desc["path"] = new
    core["files"].sort(key=lambda item: item["path"])
    files = tuple(sorted((new if path == old else path, data) for path, data in files))
    root = tmp_path / "private"
    root.mkdir(mode=0o700)
    with pytest.raises(publication.PublicationError):
        publication.publish_directory(originals, derived, str(root), enc(core), files)
    assert list(root.iterdir()) == []


def test_nested_retry_refused_before_tree_or_fd_access(actual, tmp_path, monkeypatch):  # noqa: F811
    originals, derived, core, files, root = fixture(actual, tmp_path)
    unlink = publication.os.unlink

    def fail(*args, **kwargs):
        raise OSError("controlled failure")

    with monkeypatch.context() as patch:
        patch.setattr(publication, "_rename_noreplace", fail)
        patch.setattr(publication.os, "unlink", fail)
        with pytest.raises(publication.PublicationError):
            publication.publish_directory(originals, derived, str(root), core, files)
    owner = publication._pending[-1]
    calls = []

    def nested(*args, **kwargs):
        if not calls:
            tree = list(owner.created)
            fds = set(owner.owner.fds)
            with pytest.raises(ValueError):
                owner.retry_cleanup()
            assert owner.created == tree and owner.owner.fds == fds
            assert owner in publication._pending
            calls.append(True)
        return unlink(*args, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(publication.os, "unlink", nested)
        assert owner.retry_cleanup() is None
    assert calls == [True] and owner not in publication._pending
    assert list((root / "snapshots").iterdir()) == []


def test_actual_no_replace_flag_control(actual, tmp_path, monkeypatch):  # noqa: F811
    # Adapted from Root witness /tmp/raggedized-root-publication-4c67-controls.py.
    import inspect

    originals, derived, core, files, root = fixture(actual, tmp_path)
    snapshots = root / "snapshots"
    snapshots.mkdir(mode=0o700)
    target = snapshots / hashlib.sha256(core).hexdigest()
    target.mkdir(mode=0o500)
    before = target.stat().st_ino
    source = inspect.getsource(publication._rename_noreplace)
    needle = "os.fsencode(new), 1)"
    assert source.count(needle) == 1
    with pytest.raises(publication.PublicationError):
        publication.publish_directory(originals, derived, str(root), core, files)
    assert target.stat().st_ino == before and not list(target.iterdir())
    changed = source.replace(needle, "os.fsencode(new), 0)")
    scope = dict(publication.__dict__)
    exec(compile(changed, "<Root-rename-flag-only>", "exec"), scope)
    with monkeypatch.context() as patch:
        patch.setattr(publication, "_rename_noreplace", scope["_rename_noreplace"])
        result = publication.publish_directory(originals, derived, str(root), core, files)
    assert result.created and result.data.core_bytes == core and target.stat().st_ino != before
    other = tmp_path / "baseline"
    other.mkdir(mode=0o700)
    (other / "snapshots").mkdir(mode=0o700)
    last = other / "snapshots" / hashlib.sha256(core).hexdigest()
    last.mkdir(mode=0o500)
    inode = last.stat().st_ino
    with pytest.raises(publication.PublicationError):
        publication.publish_directory(originals, derived, str(other), core, files)
    assert last.stat().st_ino == inode and not list(last.iterdir())
    print("original_guard_sha256=" + hashlib.sha256(source.encode()).hexdigest())
    print("single_flag_control_sha256=" + hashlib.sha256(changed.encode()).hexdigest())


def test_retry_interrupt_identity_and_guard_release(actual, tmp_path, monkeypatch):  # noqa: F811
    originals, derived, core, files, root = fixture(actual, tmp_path)

    def fail(*args, **kwargs):
        raise OSError("controlled")

    with monkeypatch.context() as patch:
        patch.setattr(publication, "_rename_noreplace", fail)
        patch.setattr(publication.os, "unlink", fail)
        with pytest.raises(publication.PublicationError):
            publication.publish_directory(originals, derived, str(root), core, files)
    owner = publication._pending[-1]
    interrupt = KeyboardInterrupt("controlled")

    def interrupt_unlink(*args, **kwargs):
        raise interrupt

    with monkeypatch.context() as patch:
        patch.setattr(publication.os, "unlink", interrupt_unlink)
        with pytest.raises(KeyboardInterrupt) as exc:
            owner.retry_cleanup()
        assert exc.value is interrupt
        assert owner in publication._pending and not owner.guard.locked()
    assert owner.retry_cleanup() is None
    assert owner not in publication._pending


def test_initial_cleanup_holds_guard(actual, tmp_path, monkeypatch):  # noqa: F811
    originals, derived, core, files, root = fixture(actual, tmp_path)
    owners = []
    init = publication._Operation.__init__
    unlink = publication.os.unlink

    def capture(self):
        init(self)
        owners.append(self)

    def fail(*args):
        raise OSError("controlled")

    observed = []

    def check_guard(*args, **kwargs):
        observed.append(owners[0].guard.locked())
        return unlink(*args, **kwargs)

    monkeypatch.setattr(publication._Operation, "__init__", capture)
    monkeypatch.setattr(publication, "_rename_noreplace", fail)
    monkeypatch.setattr(publication.os, "unlink", check_guard)
    with pytest.raises(publication.PublicationError):
        publication.publish_directory(originals, derived, str(root), core, files)
    assert observed and all(observed) and not owners[0].guard.locked()


def test_oversized_core_is_not_hashed_or_published(actual, tmp_path, monkeypatch):  # noqa: F811
    # Adapted from Root witness /tmp/raggedized-root-publication-4c67-oversize.py.
    originals, derived, _, files, root = fixture(actual, tmp_path)
    real = publication.hashlib.sha256
    calls = []

    def observe(data=b"", *args, **kwargs):
        calls.append(len(data))
        return real(data, *args, **kwargs)

    monkeypatch.setattr(publication.hashlib, "sha256", observe)
    with pytest.raises(publication.PublicationError) as exc:
        publication.publish_directory(originals, derived, str(root), b"x" * 262145, files)
    assert exc.value.snapshot_id is None and not exc.value.publication_may_exist
    assert 262145 not in calls and not list(root.iterdir())
