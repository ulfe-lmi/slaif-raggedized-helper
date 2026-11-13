"""Actual source-backed lifetime and narrowly isolated lock control."""

import fcntl
import hashlib
import inspect
import json
import os
import subprocess
import sys
import threading

import pytest

from slaif_raggedized_helper import raw_snapshot_pin as pin
from slaif_raggedized_helper import raw_snapshot_publication as publication
from slaif_raggedized_helper import raw_snapshot_selection as selection
from test_raw_snapshot_directory_composition import restore_owned_directories  # noqa: F401
from test_raw_snapshot_publication_composition import fixture
from test_raw_snapshot_source_rows_composition import actual  # noqa: F401


def setup_pair(actual, tmp_path):  # noqa: F811
    originals, derived, core, files, root = fixture(actual, tmp_path)
    first = publication.publish_directory(originals, derived, str(root), core, files)
    altered = json.loads(core)
    altered["validation"]["validator_fingerprint"] = "f" * 64
    second_core = json.dumps(altered, sort_keys=True, separators=(",", ":")).encode()
    second = publication.publish_directory(originals, derived, str(root), second_core, files)
    current = selection.compare_and_select_data(
        originals, derived, str(root), first.snapshot_id, None
    )
    return originals, derived, str(root), first.snapshot_id, second.snapshot_id, current


def test_actual_lifetimes(actual, tmp_path, monkeypatch):  # noqa: F811
    originals, derived, root, a, b, current = setup_pair(actual, tmp_path)
    owner = pin.PinOwner()
    captured = owner.acquire_selected_data(originals, derived, root)
    selected = selection.compare_and_select_data(
        originals, derived, root, b, current.pointer.pointer_bytes
    )
    assert owner.check() == captured and captured.data.snapshot_id == a
    with pytest.raises(pin.PinError):
        pin.RetirementOwner().acquire_unselected_data(originals, derived, root, b)
    lock_calls = []
    real_lock = pin._target_lock

    def record_lock(op, fd, exclusive):
        lock_calls.append(exclusive)
        return real_lock(op, fd, exclusive)

    monkeypatch.setattr(pin, "_target_lock", record_lock)
    blocked = pin.RetirementOwner()
    with pytest.raises(pin.PinError):
        blocked.acquire_unselected_data(originals, derived, root, a, deadline_ms=1000)
    assert blocked.state == "CLOSED" and lock_calls == [True]
    # A separate interpreter opens its own file description and observes the actual lock.
    code = (
        "import fcntl,os,sys; f=os.open(sys.argv[1],os.O_RDONLY|os.O_DIRECTORY); "
        "fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)"
    )
    child = subprocess.run(
        [sys.executable, "-c", code, root + "/snapshots/" + a[7:]],
        capture_output=True,
        timeout=10,
        check=False,
    )
    assert child.returncode != 0 and b"BlockingIOError" in child.stderr
    # An independent same-process open description also conflicts.
    fd = os.open(root + "/snapshots/" + a[7:], os.O_RDONLY | os.O_DIRECTORY)
    try:
        with pytest.raises(BlockingIOError):
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    finally:
        os.close(fd)
    owner.close()
    guard = pin.RetirementOwner()
    guard.acquire_unselected_data(originals, derived, root, a)
    assert guard.check().data.snapshot_id == a
    outcomes = []
    contended = threading.Event()
    real_flock = fcntl.flock
    namespace_identity = selection._identity(guard.op.parent)

    def observe_flock(fd, operation):
        try:
            return real_flock(fd, operation)
        except BlockingIOError:
            if (
                threading.current_thread().name == "pin-test-writer"
                and selection._identity(fd) == namespace_identity
                and operation == fcntl.LOCK_EX | fcntl.LOCK_NB
            ):
                contended.set()
            raise

    monkeypatch.setattr(fcntl, "flock", observe_flock)

    def writer():
        outcomes.append(
            selection.compare_and_select_data(
                originals, derived, root, a, selected.pointer.pointer_bytes, deadline_ms=10000
            )
        )

    thread = threading.Thread(target=writer, name="pin-test-writer")
    thread.start()
    try:
        assert contended.wait(5) and thread.is_alive() and not outcomes
    finally:
        guard.close()
        thread.join(10)
    assert not thread.is_alive() and outcomes[0].pointer.snapshot_id == a
    print(
        "phases=pin:1,cas_b:1,current_refusal:1,old_timeout:1,process:1,independent_fd:1,guard:1,writer:1"
    )


def test_target_lock_causal_control(actual, tmp_path, monkeypatch):  # noqa: F811
    originals, derived, root, a, b, current = setup_pair(actual, tmp_path)
    original = inspect.getsource(pin._target_lock)
    needle = "    while True:\n"
    assert original.count(needle) == 1
    changed = original.replace(needle, "    if not exclusive:\n        return\n" + needle, 1)
    scope = dict(pin.__dict__)
    exec(compile(changed, "<target-sh-omitted>", "exec"), scope)
    print("original_sha256=" + hashlib.sha256(original.encode()).hexdigest())
    print("control_sha256=" + hashlib.sha256(changed.encode()).hexdigest())
    calls = []
    real_lock = pin._target_lock

    def record_lock(op, fd, exclusive):
        calls.append(exclusive)
        return real_lock(op, fd, exclusive)

    monkeypatch.setattr(pin, "_target_lock", record_lock)
    reader = pin.PinOwner()
    reader.acquire_selected_data(originals, derived, root)
    selection.compare_and_select_data(originals, derived, root, b, current.pointer.pointer_bytes)
    with pytest.raises(pin.PinError):
        pin.RetirementOwner().acquire_unselected_data(originals, derived, root, a, deadline_ms=1000)
    assert calls == [False, True]
    reader.close()
    with monkeypatch.context() as patch:
        patch.setattr(pin, "_target_lock", scope["_target_lock"])
        descriptive = pin.PinOwner()
        # Pin A while selected, then select B using actual CAS.
        old = selection.read_selected_data(originals, derived, root)
        new = selection.compare_and_select_data(
            originals, derived, root, a, old.pointer.pointer_bytes
        )
        descriptive.acquire_selected_data(originals, derived, root)
        selection.compare_and_select_data(originals, derived, root, b, new.pointer.pointer_bytes)
        guard = pin.RetirementOwner()
        guard.acquire_unselected_data(originals, derived, root, a)
        assert descriptive.check().data.snapshot_id == a and guard.check().data.snapshot_id == a
        guard.close()
        descriptive.close()
    old = selection.read_selected_data(originals, derived, root)
    new = selection.compare_and_select_data(originals, derived, root, a, old.pointer.pointer_bytes)
    calls.clear()
    reader = pin.PinOwner()
    reader.acquire_selected_data(originals, derived, root)
    selection.compare_and_select_data(originals, derived, root, b, new.pointer.pointer_bytes)
    with pytest.raises(pin.PinError):
        pin.RetirementOwner().acquire_unselected_data(originals, derived, root, a, deadline_ms=1000)
    assert calls == [False, True]
    reader.close()
    guard = pin.RetirementOwner()
    guard.acquire_unselected_data(originals, derived, root, a)
    guard.close()
    print("phases=original_exclusion:1,omitted_sh_guard:1,restored_exclusion:1,post_close_guard:1")
