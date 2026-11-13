"""Closed selection pointer codec."""

import json

import pytest

from slaif_raggedized_helper import raw_snapshot_selection as selection


def test_codec_closed():
    sid = "sha256:" + "a" * 64
    raw = selection._encode(1, sid)
    assert selection.parse_pointer(raw).snapshot_id == sid
    for bad in (
        raw + b"\n",
        raw.replace(b'"generation":1', b'"generation":true'),
        raw.replace(b'"schema":1', b'"schema":2'),
        b"{}",
        b"x" * 513,
        json.dumps({"generation": 1}).encode(),
    ):
        with pytest.raises(selection.SelectionError):
            selection.parse_pointer(bad)


def test_pointer_boundaries_and_duplicates():
    sid = "sha256:" + "0" * 64
    assert selection.parse_pointer(selection._encode(2**63 - 1, sid)).generation == 2**63 - 1
    for raw in (
        selection._encode(0, sid),
        selection._encode(2**63, sid),
        selection._encode(1, sid).replace(b'"schema":1', b'"schema":1,"schema":1'),
        selection._encode(1, sid).replace(b'"generation":1', b'"generation":1.0'),
        selection._encode(1, sid).replace(b'"core_sha256":"0', b'"core_sha256":"A'),
    ):
        with pytest.raises(selection.SelectionError):
            selection.parse_pointer(raw)


def test_bad_deadline_refused_before_path_access():
    for budget in (0, 120001, True, 1.0):
        with pytest.raises(selection.SelectionError):
            selection.read_selected_data(None, None, "/missing", deadline_ms=budget)


def test_creator_and_busy_cleanup_refusal(tmp_path, monkeypatch):
    import os

    root = tmp_path / "private"
    root.mkdir(mode=0o700)
    op = selection._Operation(str(root), 30000)
    op.root = selection.reader._root(op.owner, str(root))
    selection._pending.append(op)
    fds = set(op.owner.fds)
    with pytest.raises(ValueError):
        op.retry_cleanup()
    assert op.owner.fds == fds
    op.guard.release()
    real_pid = os.getpid()
    with monkeypatch.context() as patch:
        patch.setattr(selection.os, "getpid", lambda: real_pid + 1)
        with pytest.raises(ValueError):
            op.retry_cleanup()
        assert op.owner.fds == fds
    assert op.retry_cleanup() is None


def test_cleanup_releases_acquired_guard_when_attribute_changes(tmp_path, monkeypatch):
    import threading

    root = tmp_path / "private"
    root.mkdir(mode=0o700)
    cleanup = selection._Operation.cleanup
    held = []

    def change_guard(op):
        held.append(op.guard)
        result = cleanup(op)
        op.guard = threading.Lock()
        return result

    with monkeypatch.context() as patch:
        patch.setattr(selection._Operation, "cleanup", change_guard)
        assert selection.read_selected_data(None, None, str(root)) is None
    assert len(held) == 1 and not held[0].locked()

    op = selection._Operation(str(root), 30000)
    op.guard.release()
    selection._pending.append(op)
    with monkeypatch.context() as patch:
        patch.setattr(selection._Operation, "cleanup", change_guard)
        assert op.retry_cleanup() is None
    assert not held[-1].locked()
