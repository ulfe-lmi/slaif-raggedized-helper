"""Hosted synthetic composition for the fixed private expected
selected acquisition (OAP PAR-009-EVALUATE-EXPECTED-PIN-A).

Offline synthetic fixtures only: the real two-snapshot publication
and compare-and-select fixture of the existing raw pin composition
builds the actual pointer, stores and paths, and every byte is
generated here.  No local native witness execution: only the
configured hosted CI executes the two real hosted nodes, and local
proof of this module is collection only.
"""
import fcntl
import os
import re
import time

import pytest

from slaif_raggedized_helper import raw_snapshot_directory as directory
from slaif_raggedized_helper import raw_snapshot_pin as pin
from slaif_raggedized_helper import raw_snapshot_selection as selection
from test_raw_snapshot_directory_composition import restore_owned_directories  # noqa: F401
from test_raw_snapshot_pin_composition import setup_pair
from test_raw_snapshot_source_rows_composition import actual  # noqa: F401

_REAL_OPEN = selection._Operation.open
_REAL_POINTER = selection._Operation.pointer
_REAL_LOAD = directory.load_directory
_REAL_OWNER_OPEN = directory._Owner.open


class _late_clock:
    # Local selection-module clock proxy: before the exact load
    # return boundary it preserves the real monotonic and every other
    # real time behavior; after the boundary the observed monotonic is
    # past the fixed end, so the product's own deadline check decides
    # the refusal.
    def __init__(self, real, offset=3600.0):
        self._real = real
        self._offset = offset
        self._past = False

    def monotonic(self):
        if self._past:
            return self._real.monotonic() + self._offset
        return self._real.monotonic()

    def __getattr__(self, name):
        return getattr(self._real, name)


def _refuse_case(originals, derived, root, snapshot_id, generation, end,
                 monkeypatch, opens, current_pointer=None):
    # One refused expected acquisition with the actual selection-lock
    # open, pointer, directory-load and target-open events counted on
    # the same acquisition operation; the spies are scoped to this
    # refusal so later real selector writes run unspied; the owner is
    # cleaned up truthfully and the denial is the exact fixed
    # content-free PinError.
    owner = pin.PinOwner()
    open_calls, pointer_calls, load_calls, owner_open_calls = [], [], [], []

    def counting_open(op, exclusive):
        open_calls.append((op, exclusive))
        return _REAL_OPEN(op, exclusive)

    def counting_pointer(op):
        pointer = _REAL_POINTER(op)
        pointer_calls.append((op, pointer))
        return pointer

    def counting_load(orig, der, store_root, snap):
        load_calls.append(snap)
        return _REAL_LOAD(orig, der, store_root, snap)

    def counting_owner_open(self, path, flags, *, parent=None):
        owner_open_calls.append((self, path, parent))
        return _REAL_OWNER_OPEN(self, path, flags, parent=parent)

    with monkeypatch.context() as context:
        context.setattr(selection._Operation, "open", counting_open)
        context.setattr(selection._Operation, "pointer", counting_pointer)
        context.setattr(directory, "load_directory", counting_load)
        context.setattr(directory._Owner, "open", counting_owner_open)
        with pytest.raises(pin.PinError) as caught:
            owner._acquire_expected_selected_data(
                originals, derived, root, snapshot_id, generation, end=end)
    assert caught.value.args == ("snapshot lifetime refused",)
    mine = [(op, exclusive) for op, exclusive in open_calls if op is owner.op]
    assert len(mine) == opens
    for op, exclusive in mine:
        assert op.path == root and exclusive is False
    mine_pointers = [pointer for op, pointer in pointer_calls if op is owner.op]
    if current_pointer is None:
        assert mine_pointers == []
    else:
        # The real selected pointer observed under that same
        # operation's real shared-mode open.
        assert mine_pointers == [current_pointer]
    assert load_calls == []
    assert owner.state == "CLOSED"
    assert not owner.guard.locked()
    if owner.op is None:
        # No namespace work at all: the full open, pointer and
        # owner-open logs are empty, not just the same-op filter.
        assert opens == 0
        assert open_calls == [] and pointer_calls == []
        assert owner_open_calls == []
    else:
        # Truthful fd cleanup: no outstanding known fds and no
        # uncertain close numbers.
        assert owner.op.owner.fds == set()
        assert owner.op.owner.unknown == set()
        # No target open of any snapshot directory under the held
        # namespace of the same operation.
        assert not any(
            owner_ is owner.op.owner
            and re.fullmatch(r"[0-9a-f]{64}", name) is not None
            and parent == owner.op.parent
            for owner_, name, parent in owner_open_calls)


def test_expected_acquisition_accepts_exact_selected_id_and_generation(
        actual, tmp_path, monkeypatch):  # noqa: F811
    originals, derived, root, a, b, current = setup_pair(actual, tmp_path)
    owner = pin.PinOwner()
    end = time.monotonic() + 60.0
    loads = []

    def counting_load(orig, der, store_root, snap):
        loads.append((owner.op.end, snap))
        return _REAL_LOAD(orig, der, store_root, snap)

    try:
        with monkeypatch.context() as context:
            context.setattr(directory, "load_directory", counting_load)
            value = owner._acquire_expected_selected_data(
                originals, derived, root, a, current.pointer.generation,
                end=end)
        assert value is owner.value
        assert value.pointer == current.pointer
        assert value.pointer.snapshot_id == a
        assert value.pointer.generation == current.pointer.generation
        assert value.data.snapshot_id == a
        assert owner.state == "ACTIVE"
        # The original absolute end is held unchanged through both
        # real loads and on the retained operation and returned
        # PinData.
        assert [snap for _observed, snap in loads] == [a, a]
        assert [observed for observed, _snap in loads] == [end, end]
        assert owner.op.end == end
    finally:
        owner.close()
    assert owner.state == "CLOSED"
    # The close released the real held target: a separate file
    # description takes the exclusive target lock.
    target = os.open(root + "/snapshots/" + a[7:], os.O_RDONLY | os.O_DIRECTORY)
    try:
        fcntl.flock(target, fcntl.LOCK_EX | fcntl.LOCK_NB)
    finally:
        os.close(target)
    # One closely bounded subcase: the real nested load returns late
    # at the exact return boundary, so no PinData becomes usable at
    # the original end and the exact cleanup runs.
    late_owner = pin.PinOwner()
    late_end = time.monotonic() + 60.0
    late_loads = []
    clock = _late_clock(time)

    def late_load(orig, der, store_root, snap):
        result = _REAL_LOAD(orig, der, store_root, snap)
        # The deterministic test-only observation at the exact load
        # return boundary: from here on the selection module's
        # observed clock is past the fixed end; the product's own
        # deadline check decides the refusal.
        clock._past = True
        late_loads.append(snap)
        return result

    with monkeypatch.context() as context:
        context.setattr(selection, "time", clock)
        context.setattr(directory, "load_directory", late_load)
        with pytest.raises(pin.PinError) as late_caught:
            late_owner._acquire_expected_selected_data(
                originals, derived, root, a, current.pointer.generation,
                end=late_end)
    assert late_caught.value.args == ("snapshot lifetime refused",)
    # The actual late load ran once.
    assert late_loads == [a]
    # No PinData and no target stage credit became usable at the
    # original end.
    assert late_owner.value is None and late_owner.target is None
    # The exact code still used the fixed original end and its
    # finite cleanup after the observed expiry.
    assert late_owner.op.end == late_end
    assert late_owner.op.owner.fds == set()
    assert late_owner.op.owner.unknown == set()
    late_owner.close()
    assert late_owner.state == "CLOSED"


def test_expected_acquisition_refuses_malformed_stale_and_changed(
        actual, tmp_path, monkeypatch):  # noqa: F811
    originals, derived, root, a, b, current = setup_pair(actual, tmp_path)
    end = time.monotonic() + 60.0
    generation = current.pointer.generation
    # Malformed, missing or expired expectations refuse before any
    # namespace work.
    _refuse_case(originals, derived, root, None, generation, end, monkeypatch, 0)
    _refuse_case(originals, derived, root, a, True, end, monkeypatch, 0)
    _refuse_case(originals, derived, root, a, 0, end, monkeypatch, 0)
    _refuse_case(
        originals, derived, root, a, selection._MAX_GENERATION + 1, end,
        monkeypatch, 0)
    _refuse_case(originals, derived, root, "sha256:" + "f" * 63, generation,
                 end, monkeypatch, 0)
    _refuse_case(None, derived, root, a, generation, end, monkeypatch, 0)
    # An already elapsed end refuses before any namespace work.
    _refuse_case(originals, derived, root, a, generation,
                 time.monotonic() - 1.0, monkeypatch, 0)
    # A wrong ID: the real shared selection lock opens on the same
    # operation and the real selected pointer is observed under it,
    # but there is zero actual data load and zero target open.
    _refuse_case(originals, derived, root, b, generation, end, monkeypatch, 1,
                 current_pointer=current.pointer)
    # A stale same-ID generation after a real same-ID reselection.
    resel = selection.compare_and_select_data(
        originals, derived, root, a, current.pointer.pointer_bytes)
    assert resel.pointer.snapshot_id == a
    assert resel.pointer.generation == generation + 1
    _refuse_case(originals, derived, root, a, generation, end, monkeypatch, 1,
                 current_pointer=resel.pointer)
    # A real intervening selected change before acquiring under the
    # lock still refuses before loading the newly selected snapshot.
    changed = selection.compare_and_select_data(
        originals, derived, root, b, resel.pointer.pointer_bytes)
    assert changed.pointer.snapshot_id == b
    assert changed.pointer.generation == generation + 2
    _refuse_case(originals, derived, root, a, generation, end, monkeypatch, 1,
                 current_pointer=changed.pointer)
