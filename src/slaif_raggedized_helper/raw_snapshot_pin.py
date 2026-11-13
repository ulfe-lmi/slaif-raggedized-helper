"""Private snapshot lifetime coordination, without authorization or deletion."""

import fcntl
import os
import re
import threading
import time
from dataclasses import dataclass

from . import derived_store, raw_snapshot_directory as directory
from . import raw_snapshot_publication as publication, raw_snapshot_selection as selection
from .source_admission import OriginalStore


class PinError(ValueError):
    """Content-free refusal of a lifetime operation."""


@dataclass(frozen=True, slots=True)
class PinData:
    pointer: selection.Pointer
    data: object


def _admit(originals, derived, root, deadline_ms, snapshot_id=None):
    directory._check(type(originals) is OriginalStore and type(derived) is derived_store.Store)
    publication._path_check(root)
    directory._check(len(root[1:].split("/")) <= 64)
    directory._check(type(deadline_ms) is int and 1 <= deadline_ms <= 120000)
    if snapshot_id is not None:
        directory._check(
            type(snapshot_id) is str and re.fullmatch(r"sha256:[0-9a-f]{64}", snapshot_id)
        )


def _target_lock(op, fd, exclusive):
    while True:
        op.deadline()
        try:
            fcntl.flock(fd, (fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH) | fcntl.LOCK_NB)
            return
        except BlockingIOError:
            time.sleep(min(0.01, max(0, op.end - time.monotonic())))


class _Capture:
    def __init__(self):
        self.pid = os.getpid()
        self.guard = threading.Lock()
        self.state = "NEW"
        self.op = None
        self.target = None
        self.value = None
        self.originals = None
        self.derived = None

    def _enter(self):
        if os.getpid() != self.pid or not self.guard.acquire(blocking=False):
            raise PinError("snapshot lifetime refused")

    def _cleanup(self):
        if self.op is None:
            self.state = "CLOSED"
            return None
        self.state = "CLEANUP_PENDING"
        error = self.op.cleanup()
        self.state = "CLEANUP_PENDING" if error is not None or self.op.owner.unknown else "CLOSED"
        return error

    def _failure(self, error):
        self.state = "CLEANUP_PENDING"
        try:
            cleanup = self._cleanup()
        except BaseException as exc:
            cleanup = exc
        if (
            cleanup is not None
            and isinstance(error, Exception)
            and not isinstance(cleanup, Exception)
        ):
            error = cleanup
        if isinstance(error, Exception):
            raise PinError("snapshot lifetime refused") from None
        raise error

    def _start(self, originals, derived, root, deadline_ms, snapshot_id=None):
        directory._check(self.state == "NEW")
        self.state = "ACQUIRING"
        started = time.monotonic()
        _admit(originals, derived, root, deadline_ms, snapshot_id)
        self.originals, self.derived = originals, derived
        self.op = selection._Operation(root, deadline_ms)
        self.op.end = started + deadline_ms / 1000
        # The operation's construction guard is not the capture's method guard.
        self.op.guard.release()

    def _association(self):
        op = self.op
        op.namespace()
        directory._private(os.fstat(self.target), 0o500, True)
        directory._linked(op.parent, self.value.data.snapshot_id[7:], self.target)
        op.deadline()

    def _load(self, snapshot_id):
        op = self.op
        op.deadline()
        data = directory.load_directory(self.originals, self.derived, op.path, snapshot_id)
        op.deadline()
        return data

    def close(self):
        self._enter()
        try:
            if self.state == "CLOSED":
                return
            error = self._cleanup()
            if error is not None:
                if not isinstance(error, Exception):
                    raise error
                raise PinError("snapshot lifetime refused") from None
            if self.state != "CLOSED":
                raise selection.CleanupPendingError("descriptor close outcome unknown")
        finally:
            self.guard.release()

    def __enter__(self):
        return self

    def __exit__(self, typ, value, tb):
        try:
            self.close()
        except BaseException as exc:
            if value is None or isinstance(value, Exception) and not isinstance(exc, Exception):
                raise
        return False


class PinOwner(_Capture):
    """Caller-owned pin of source-validated selected data."""

    def __init_subclass__(cls, **kwargs):
        raise TypeError("PinOwner cannot be subclassed")

    def acquire_selected_data(self, originals, derived, store_root, *, deadline_ms=30000):
        self._enter()
        try:
            if self.state != "NEW":
                raise PinError("snapshot lifetime refused")
            try:
                self._start(originals, derived, store_root, deadline_ms)
                op = self.op
                directory._check(op.open(False))
                pointer = op.pointer()
                directory._check(pointer is not None)
                data = op.load(originals, derived, pointer).data
                self.target = op.owner.open(
                    pointer.snapshot_id[7:], directory._DIR, parent=op.parent
                )
                directory._private(os.fstat(self.target), 0o500, True)
                _target_lock(op, self.target, False)
                self.value = PinData(pointer, data)
                self._association()
                directory._check(self._load(pointer.snapshot_id) == data)
                self._association()
                directory._check(op.pointer() == pointer)
                independent = op.owner.open("snapshots", directory._DIR, parent=op.root)
                directory._check(selection._identity(independent) == selection._identity(op.parent))
                locked = op.parent
                op.parent = independent
                op.owner.close(locked)
                self._association()
                self.state = "ACTIVE"
                return self.value
            except BaseException as exc:
                self._failure(exc)
        finally:
            self.guard.release()

    def check(self, *, deadline_ms=30000):
        self._enter()
        try:
            try:
                directory._check(self.state == "ACTIVE")
                directory._check(type(deadline_ms) is int and 1 <= deadline_ms <= 120000)
                self.op.end = time.monotonic() + deadline_ms / 1000
                self._association()
                data = self._load(self.value.data.snapshot_id)
                self._association()
                directory._check(data == self.value.data)
                return self.value
            except Exception:
                raise PinError("snapshot lifetime refused") from None
        finally:
            self.guard.release()


class RetirementOwner(_Capture):
    """Live exclusive guard for an unselected snapshot; performs no removal."""

    def __init_subclass__(cls, **kwargs):
        raise TypeError("RetirementOwner cannot be subclassed")

    def acquire_unselected_data(
        self, originals, derived, store_root, snapshot_id, *, deadline_ms=30000
    ):
        self._enter()
        try:
            if self.state != "NEW":
                raise PinError("snapshot lifetime refused")
            try:
                directory._check(
                    type(snapshot_id) is str and re.fullmatch(r"sha256:[0-9a-f]{64}", snapshot_id)
                )
                self._start(originals, derived, store_root, deadline_ms, snapshot_id)
                op = self.op
                directory._check(op.open(True))
                pointer = op.pointer()
                directory._check(pointer is None or pointer.snapshot_id != snapshot_id)
                if pointer is not None:
                    op.load(originals, derived, pointer)
                data = self._load(snapshot_id)
                self.target = op.owner.open(snapshot_id[7:], directory._DIR, parent=op.parent)
                directory._private(os.fstat(self.target), 0o500, True)
                _target_lock(op, self.target, True)
                self.value = PinData(pointer, data)
                self._association()
                directory._check(self._load(snapshot_id) == data)
                self._association()
                directory._check(op.pointer() == pointer)
                self.state = "ACTIVE"
                return self.value
            except BaseException as exc:
                self._failure(exc)
        finally:
            self.guard.release()

    def check(self, *, deadline_ms=30000):
        self._enter()
        try:
            try:
                directory._check(self.state == "ACTIVE")
                directory._check(type(deadline_ms) is int and 1 <= deadline_ms <= 120000)
                self.op.end = time.monotonic() + deadline_ms / 1000
                self._association()
                directory._check(self.op.pointer() == self.value.pointer)
                data = self._load(self.value.data.snapshot_id)
                self._association()
                directory._check(
                    self.op.pointer() == self.value.pointer and data == self.value.data
                )
                return self.value
            except Exception:
                raise PinError("snapshot lifetime refused") from None
        finally:
            self.guard.release()
