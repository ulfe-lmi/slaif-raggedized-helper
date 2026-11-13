"""Actual source and filesystem selection composition."""

import pytest

from slaif_raggedized_helper import raw_snapshot_publication as publication
from slaif_raggedized_helper import raw_snapshot_selection as selection
from test_raw_snapshot_publication_composition import fixture
from test_raw_snapshot_directory_composition import restore_owned_directories  # noqa: F401
from test_raw_snapshot_source_rows_composition import actual  # noqa: F401


def test_selection_cas(actual, tmp_path):  # noqa: F811
    originals, derived, core, files, root = fixture(actual, tmp_path)
    assert selection.read_selected_data(originals, derived, str(root)) is None
    snapshot = publication.publish_directory(originals, derived, str(root), core, files)
    first = selection.compare_and_select_data(
        originals, derived, str(root), snapshot.snapshot_id, None
    )
    assert first.pointer.generation == 1
    second = selection.compare_and_select_data(
        originals, derived, str(root), snapshot.snapshot_id, first.pointer.pointer_bytes
    )
    assert second.pointer.generation == 2
    with pytest.raises(selection.SelectionError) as exc:
        selection.compare_and_select_data(
            originals, derived, str(root), snapshot.snapshot_id, first.pointer.pointer_bytes
        )
    assert not exc.value.selection_may_have_changed
    assert selection.read_selected_data(originals, derived, str(root)) == second


def test_rollback_and_guard_control(actual, tmp_path, monkeypatch):  # noqa: F811
    import hashlib
    import inspect
    import json

    originals, derived, core, files, root = fixture(actual, tmp_path)
    first = publication.publish_directory(originals, derived, str(root), core, files)
    altered = json.loads(core)
    altered["validation"]["validator_fingerprint"] = "f" * 64
    second_core = json.dumps(altered, sort_keys=True, separators=(",", ":")).encode()
    second = publication.publish_directory(originals, derived, str(root), second_core, files)
    assert first.snapshot_id != second.snapshot_id
    a = selection.compare_and_select_data(originals, derived, str(root), first.snapshot_id, None)
    selection.compare_and_select_data(
        originals, derived, str(root), second.snapshot_id, a.pointer.pointer_bytes
    )
    before = (root / "current.json").read_bytes()
    with pytest.raises(selection.SelectionError):
        selection.compare_and_select_data(
            originals, derived, str(root), first.snapshot_id, a.pointer.pointer_bytes
        )
    assert (root / "current.json").read_bytes() == before
    source = inspect.getsource(selection.compare_and_select_data)
    needle = (
        "reader._check(\n"
        "            (None if current is None else current.pointer_bytes)"
        " == expected_pointer_bytes\n"
        "        )"
    )
    assert source.count(needle) == 1
    changed = source.replace(needle, "pass  # exact comparison omitted for control")
    scope = dict(selection.__dict__)
    exec(compile(changed, "<cas-guard-control>", "exec"), scope)
    c = scope["compare_and_select_data"](
        originals, derived, str(root), first.snapshot_id, a.pointer.pointer_bytes
    )
    assert c.pointer.generation == 3 and c.pointer.snapshot_id == first.snapshot_id
    assert selection.read_selected_data(originals, derived, str(root)) == c
    print("guard_original_sha256=" + hashlib.sha256(source.encode()).hexdigest())
    print("guard_omitted_sha256=" + hashlib.sha256(changed.encode()).hexdigest())


def test_pre_and_post_replace_failure(actual, tmp_path, monkeypatch):  # noqa: F811
    import os

    originals, derived, core, files, root = fixture(actual, tmp_path)
    snapshot = publication.publish_directory(originals, derived, str(root), core, files)
    initial = selection.compare_and_select_data(
        originals, derived, str(root), snapshot.snapshot_id, None
    )
    real_fsync = os.fsync

    def fail(_fd):
        raise OSError("controlled")

    with monkeypatch.context() as patch:
        patch.setattr(selection.os, "fsync", fail)
        with pytest.raises(selection.SelectionError) as exc:
            selection.compare_and_select_data(
                originals, derived, str(root), snapshot.snapshot_id, initial.pointer.pointer_bytes
            )
        assert not exc.value.selection_may_have_changed
    assert selection.read_selected_data(originals, derived, str(root)) == initial
    calls = []

    def fail_second(fd):
        calls.append(fd)
        if len(calls) == 2:
            raise OSError("controlled")
        return real_fsync(fd)

    with monkeypatch.context() as patch:
        patch.setattr(selection.os, "fsync", fail_second)
        with pytest.raises(selection.SelectionError) as exc:
            selection.compare_and_select_data(
                originals, derived, str(root), snapshot.snapshot_id, initial.pointer.pointer_bytes
            )
        assert exc.value.selection_may_have_changed
    assert selection.read_selected_data(originals, derived, str(root)).pointer.generation == 2


def test_two_writers_one_wins(actual, tmp_path):  # noqa: F811
    import multiprocessing

    originals, derived, core, files, root = fixture(actual, tmp_path)
    snapshot = publication.publish_directory(originals, derived, str(root), core, files)
    first = selection.compare_and_select_data(
        originals, derived, str(root), snapshot.snapshot_id, None
    )
    ctx = multiprocessing.get_context("fork")
    barrier, queue = ctx.Barrier(2, timeout=20), ctx.Queue()

    def worker():
        try:
            barrier.wait()
            value = selection.compare_and_select_data(
                originals, derived, str(root), snapshot.snapshot_id, first.pointer.pointer_bytes
            )
            queue.put(("ok", value.pointer.generation))
        except selection.SelectionError:
            queue.put(("stale", None))

    children = [ctx.Process(target=worker) for _ in range(2)]
    for child in children:
        child.start()
    try:
        results = [queue.get(timeout=30) for _ in children]
        for child in children:
            child.join(timeout=5)
            assert child.exitcode == 0
    finally:
        for child in children:
            if child.is_alive():
                child.terminate()
                child.join()
    assert sorted(results) == [("ok", 2), ("stale", None)]
    assert selection.read_selected_data(originals, derived, str(root)).pointer.generation == 2


@pytest.mark.parametrize("kind", ["symlink", "hardlink", "oversize", "corrupt"])
def test_unsafe_pointer_refused(actual, tmp_path, kind):  # noqa: F811
    import os

    originals, derived, core, files, root = fixture(actual, tmp_path)
    snapshot = publication.publish_directory(originals, derived, str(root), core, files)
    initial = selection.compare_and_select_data(
        originals, derived, str(root), snapshot.snapshot_id, None
    )
    pointer = root / "current.json"
    if kind == "symlink":
        pointer.unlink()
        pointer.symlink_to("missing")
    elif kind == "hardlink":
        os.link(pointer, tmp_path / "alias")
    else:
        pointer.chmod(0o600)
        pointer.write_bytes(b"x" * (513 if kind == "oversize" else 2))
        pointer.chmod(0o400)
    with pytest.raises(selection.SelectionError):
        selection.read_selected_data(originals, derived, str(root))
    with pytest.raises(selection.SelectionError) as exc:
        selection.compare_and_select_data(
            originals, derived, str(root), snapshot.snapshot_id, initial.pointer.pointer_bytes
        )
    assert not exc.value.selection_may_have_changed


def test_cleanup_retry_and_original_interrupt(actual, tmp_path, monkeypatch):  # noqa: F811
    import os

    originals, derived, core, files, root = fixture(actual, tmp_path)
    snapshot = publication.publish_directory(originals, derived, str(root), core, files)
    initial = selection.compare_and_select_data(
        originals, derived, str(root), snapshot.snapshot_id, None
    )
    interruption = KeyboardInterrupt("original")

    def interrupt(_fd):
        raise interruption

    def fail_unlink(*args, **kwargs):
        raise OSError("cleanup")

    before = len(selection._pending)
    with monkeypatch.context() as patch:
        patch.setattr(selection.os, "fsync", interrupt)
        patch.setattr(selection.os, "unlink", fail_unlink)
        with pytest.raises(KeyboardInterrupt) as exc:
            selection.compare_and_select_data(
                originals, derived, str(root), snapshot.snapshot_id, initial.pointer.pointer_bytes
            )
        assert exc.value is interruption
    assert len(selection._pending) == before + 1
    owner = selection._pending[-1]
    assert owner.guard.acquire(blocking=False)
    try:
        with pytest.raises(ValueError):
            owner.retry_cleanup()
    finally:
        owner.guard.release()
    assert owner.retry_cleanup() is None
    assert selection.read_selected_data(originals, derived, str(root)) == initial
    assert not [x for x in os.listdir(root) if x.startswith(".selection-")]


def test_post_replace_path_swap_refused(actual, tmp_path, monkeypatch):  # noqa: F811
    import os

    originals, derived, core, files, root = fixture(actual, tmp_path)
    snapshot = publication.publish_directory(originals, derived, str(root), core, files)
    initial = selection.compare_and_select_data(
        originals, derived, str(root), snapshot.snapshot_id, None
    )
    replace = os.replace

    def swap(*args, **kwargs):
        replace(*args, **kwargs)
        root.rename(tmp_path / "displaced")
        root.mkdir(mode=0o700)

    with monkeypatch.context() as patch:
        patch.setattr(selection.os, "replace", swap)
        with pytest.raises(selection.SelectionError) as exc:
            selection.compare_and_select_data(
                originals, derived, str(root), snapshot.snapshot_id, initial.pointer.pointer_bytes
            )
        assert exc.value.selection_may_have_changed
    assert (tmp_path / "displaced" / "current.json").exists()
    assert selection.read_selected_data(originals, derived, str(root)) is None


def test_unknown_close_remains_pending(actual, tmp_path, monkeypatch):  # noqa: F811
    import os

    originals, derived, core, files, root = fixture(actual, tmp_path)
    snapshot = publication.publish_directory(originals, derived, str(root), core, files)
    close = os.close
    replace = os.replace
    armed = []

    def arm(*args, **kwargs):
        replace(*args, **kwargs)
        armed.append(True)

    def uncertain(fd):
        close(fd)
        if armed:
            armed.pop()
            raise OSError("unknown close")

    before = len(selection._pending)
    with monkeypatch.context() as patch:
        patch.setattr(selection.os, "replace", arm)
        patch.setattr(selection.os, "close", uncertain)
        with pytest.raises(selection.SelectionError) as exc:
            selection.compare_and_select_data(
                originals, derived, str(root), snapshot.snapshot_id, None
            )
        assert exc.value.selection_may_have_changed
    assert len(selection._pending) == before + 1
    owner = selection._pending[-1]
    assert isinstance(owner.retry_cleanup(), selection.CleanupPendingError)
    assert owner.owner.unknown and owner in selection._pending
    assert selection.read_selected_data(originals, derived, str(root)).pointer.generation == 1


def test_reader_during_selection_observes_complete_data(actual, tmp_path):  # noqa: F811
    import json
    import multiprocessing

    originals, derived, core, files, root = fixture(actual, tmp_path)
    first = publication.publish_directory(originals, derived, str(root), core, files)
    altered = json.loads(core)
    altered["validation"]["validator_fingerprint"] = "f" * 64
    other_core = json.dumps(altered, sort_keys=True, separators=(",", ":")).encode()
    second = publication.publish_directory(originals, derived, str(root), other_core, files)
    before = selection.compare_and_select_data(
        originals, derived, str(root), first.snapshot_id, None
    )
    ctx = multiprocessing.get_context("fork")
    gate, queue = ctx.Barrier(2, timeout=20), ctx.Queue()

    def writer():
        try:
            gate.wait()
            x = selection.compare_and_select_data(
                originals, derived, str(root), second.snapshot_id, before.pointer.pointer_bytes
            )
            queue.put(("ok", x.pointer.snapshot_id))
        except BaseException as exc:
            queue.put(("error", repr(exc)))

    child = ctx.Process(target=writer)
    child.start()
    try:
        gate.wait()
        observed = selection.read_selected_data(originals, derived, str(root))
        assert observed.pointer.snapshot_id in (first.snapshot_id, second.snapshot_id)
        assert observed.data.snapshot_id == observed.pointer.snapshot_id
        assert queue.get(timeout=30) == ("ok", second.snapshot_id)
        child.join(timeout=5)
        assert child.exitcode == 0
    finally:
        if child.is_alive():
            child.terminate()
            child.join()


def test_invalid_candidate_and_changed_source_do_not_mutate(actual, tmp_path):  # noqa: F811
    originals, derived, core, files, root = fixture(actual, tmp_path)
    snapshot = publication.publish_directory(originals, derived, str(root), core, files)
    first = selection.compare_and_select_data(
        originals, derived, str(root), snapshot.snapshot_id, None
    )
    pointer = root / "current.json"
    before = pointer.read_bytes()
    with pytest.raises(selection.SelectionError) as exc:
        selection.compare_and_select_data(
            originals, derived, str(root), "sha256:" + "f" * 64, before
        )
    assert not exc.value.selection_may_have_changed and pointer.read_bytes() == before
    blob = next((originals.root / "blobs").iterdir())
    original = blob.read_bytes()
    try:
        blob.write_bytes(b"corrupt")
        with pytest.raises(selection.SelectionError) as exc:
            selection.compare_and_select_data(
                originals, derived, str(root), snapshot.snapshot_id, before
            )
        assert not exc.value.selection_may_have_changed and pointer.read_bytes() == before
        with pytest.raises(selection.SelectionError):
            selection.read_selected_data(originals, derived, str(root))
    finally:
        blob.write_bytes(original)
    assert selection.read_selected_data(originals, derived, str(root)) == first


def test_unsafe_or_missing_namespace_with_pointer_refused(actual, tmp_path):  # noqa: F811
    originals, derived, core, files, root = fixture(actual, tmp_path)
    snapshot = publication.publish_directory(originals, derived, str(root), core, files)
    first = selection.compare_and_select_data(
        originals, derived, str(root), snapshot.snapshot_id, None
    )
    snapshots = root / "snapshots"
    moved = tmp_path / "detached-snapshots"
    snapshots.rename(moved)
    with pytest.raises(selection.SelectionError):
        selection.read_selected_data(originals, derived, str(root))
    snapshots.symlink_to(moved, target_is_directory=True)
    with pytest.raises(selection.SelectionError):
        selection.read_selected_data(originals, derived, str(root))
    snapshots.unlink()
    moved.rename(snapshots)
    assert selection.read_selected_data(originals, derived, str(root)) == first


def test_failed_write_preserves_pointer(actual, tmp_path, monkeypatch):  # noqa: F811
    originals, derived, core, files, root = fixture(actual, tmp_path)
    snapshot = publication.publish_directory(originals, derived, str(root), core, files)
    first = selection.compare_and_select_data(
        originals, derived, str(root), snapshot.snapshot_id, None
    )
    before = (root / "current.json").read_bytes()

    def fail(*args):
        raise OSError("controlled write")

    with monkeypatch.context() as patch:
        patch.setattr(selection.os, "write", fail)
        with pytest.raises(selection.SelectionError) as exc:
            selection.compare_and_select_data(
                originals, derived, str(root), snapshot.snapshot_id, before
            )
        assert not exc.value.selection_may_have_changed
    assert (root / "current.json").read_bytes() == before
    assert selection.read_selected_data(originals, derived, str(root)) == first
    assert not list(root.glob(".selection-*"))


def test_interrupt_after_replace_preserves_actual_selection(actual, tmp_path, monkeypatch):  # noqa: F811
    import os

    originals, derived, core, files, root = fixture(actual, tmp_path)
    snapshot = publication.publish_directory(originals, derived, str(root), core, files)
    first = selection.compare_and_select_data(
        originals, derived, str(root), snapshot.snapshot_id, None
    )
    replace = os.replace
    interruption = KeyboardInterrupt("after replace")

    def replace_then_interrupt(*args, **kwargs):
        replace(*args, **kwargs)
        raise interruption

    with monkeypatch.context() as patch:
        patch.setattr(selection.os, "replace", replace_then_interrupt)
        with pytest.raises(KeyboardInterrupt) as exc:
            selection.compare_and_select_data(
                originals, derived, str(root), snapshot.snapshot_id, first.pointer.pointer_bytes
            )
        assert exc.value is interruption
    current = selection.read_selected_data(originals, derived, str(root))
    assert current.pointer.generation == 2
    assert not list(root.glob(".selection-*"))


def test_generation_overflow_and_invalid_expectation_refused(actual, tmp_path):  # noqa: F811
    originals, derived, core, files, root = fixture(actual, tmp_path)
    snapshot = publication.publish_directory(originals, derived, str(root), core, files)
    pointer = root / "current.json"
    maximum = selection._encode(2**63 - 1, snapshot.snapshot_id)
    pointer.write_bytes(maximum)
    pointer.chmod(0o400)
    assert (
        selection.read_selected_data(originals, derived, str(root)).pointer.generation == 2**63 - 1
    )
    for expected in (maximum, b"not a pointer"):
        with pytest.raises(selection.SelectionError) as exc:
            selection.compare_and_select_data(
                originals, derived, str(root), snapshot.snapshot_id, expected
            )
        assert not exc.value.selection_may_have_changed
        assert pointer.read_bytes() == maximum


def test_real_loader_finishes_after_caller_deadline_refuses(actual, tmp_path, monkeypatch):  # noqa: F811
    import time

    originals, derived, core, files, root = fixture(actual, tmp_path)
    snapshot = publication.publish_directory(originals, derived, str(root), core, files)
    real_load = selection.reader.load_directory
    real_monotonic = time.monotonic
    offset = [0]
    validated = []

    def clock():
        return real_monotonic() + offset[0]

    def delayed(*args):
        data = real_load(*args)
        validated.append(data.snapshot_id)
        offset[0] = 31
        return data

    with monkeypatch.context() as patch:
        patch.setattr(selection.time, "monotonic", clock)
        patch.setattr(selection.reader, "load_directory", delayed)
        with pytest.raises(selection.SelectionError) as exc:
            selection.compare_and_select_data(
                originals, derived, str(root), snapshot.snapshot_id, None
            )
        assert not exc.value.selection_may_have_changed
    assert validated == [snapshot.snapshot_id]
    assert not (root / "current.json").exists()
    assert not list(root.glob(".selection-*"))


def test_deadline_expiry_during_cleanup_is_not_success(actual, tmp_path, monkeypatch):  # noqa: F811
    import time

    originals, derived, core, files, root = fixture(actual, tmp_path)
    snapshot = publication.publish_directory(originals, derived, str(root), core, files)
    clock = time.monotonic
    cleanup = selection._Operation.cleanup
    offset = [0]

    def timed_cleanup(op):
        result = cleanup(op)
        offset[0] = 31
        return result

    with monkeypatch.context() as patch:
        patch.setattr(selection.time, "monotonic", lambda: clock() + offset[0])
        patch.setattr(selection._Operation, "cleanup", timed_cleanup)
        with pytest.raises(selection.SelectionError) as exc:
            selection.compare_and_select_data(
                originals, derived, str(root), snapshot.snapshot_id, None
            )
        assert exc.value.selection_may_have_changed
    assert selection.read_selected_data(originals, derived, str(root)).pointer.generation == 1


def test_hostile_diagnostics_do_not_mask_original_interruption(actual, tmp_path, monkeypatch):  # noqa: F811
    import os

    originals, derived, core, files, root = fixture(actual, tmp_path)
    snapshot = publication.publish_directory(originals, derived, str(root), core, files)
    baseline = selection.compare_and_select_data(
        originals, derived, str(root), snapshot.snapshot_id, None
    )
    pointer = selection._Operation.pointer
    close = os.close
    armed = []

    class Original(BaseException):
        def add_note(self, text):
            raise RuntimeError("hostile diagnostic")

        def __repr__(self):
            raise RuntimeError("hostile representation")

    interruption = Original()

    def interrupt(op):
        assert pointer(op) == baseline.pointer
        armed.append(True)
        raise interruption

    def uncertain_close(fd):
        close(fd)
        if armed:
            armed.pop()
            raise OSError("unknown close")

    before = len(selection._pending)
    with monkeypatch.context() as patch:
        patch.setattr(selection._Operation, "pointer", interrupt)
        patch.setattr(selection.os, "close", uncertain_close)
        with pytest.raises(Original) as exc:
            selection.read_selected_data(originals, derived, str(root))
        assert exc.value is interruption
    assert len(selection._pending) == before + 1
    owner = selection._pending[-1]
    assert owner.owner.unknown
    assert isinstance(owner.retry_cleanup(), selection.CleanupPendingError)
    assert selection.read_selected_data(originals, derived, str(root)) == baseline
