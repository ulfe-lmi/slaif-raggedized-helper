"""Private source-bound DATA selection; no serving or retention authority."""

import fcntl
import json
import os
import re
import secrets
import threading
import time
from dataclasses import dataclass

from . import raw_snapshot_directory as reader, raw_snapshot_publication as publication


class SelectionError(ValueError):
    """Selection refusal. After a replace attempt the selection may have changed."""

    def __init__(self, selection_may_have_changed=False):
        super().__init__("snapshot selection refused")
        self.selection_may_have_changed = selection_may_have_changed


class CleanupPendingError(RuntimeError):
    """A descriptor close has an unknown outcome and cannot be retried."""


@dataclass(frozen=True, slots=True)
class Pointer:
    pointer_bytes: bytes
    generation: int
    snapshot_id: str
    core_sha256: str


@dataclass(frozen=True, slots=True)
class Selection:
    pointer: Pointer
    data: object


_KIND = "raw-snapshot-selection-data-v1"
_MAX_GENERATION = 2**63 - 1
_pending = []


def parse_pointer(pointer_bytes):
    """Parse the closed canonical pointer representation."""
    try:
        reader._check(type(pointer_bytes) is bytes and len(pointer_bytes) <= 512)
        obj = json.loads(pointer_bytes.decode("ascii"))
        reader._check(
            type(obj) is dict
            and set(obj) == {"schema", "kind", "generation", "snapshot_id", "core_sha256"}
        )
        reader._check(type(obj["schema"]) is int and obj["schema"] == 1)
        reader._check(obj["kind"] == _KIND and type(obj["kind"]) is str)
        generation = obj["generation"]
        reader._check(type(generation) is int and 1 <= generation <= _MAX_GENERATION)
        snapshot = obj["snapshot_id"]
        reader._check(type(snapshot) is str and re.fullmatch(r"sha256:[0-9a-f]{64}", snapshot))
        reader._check(type(obj["core_sha256"]) is str and obj["core_sha256"] == snapshot[7:])
        reader._check(
            json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode(
                "ascii"
            )
            == pointer_bytes
        )
        return Pointer(pointer_bytes, generation, snapshot, obj["core_sha256"])
    except (ValueError, TypeError, UnicodeError, RecursionError):
        raise SelectionError() from None


def _encode(generation, snapshot):
    return json.dumps(
        {
            "schema": 1,
            "kind": _KIND,
            "generation": generation,
            "snapshot_id": snapshot,
            "core_sha256": snapshot[7:],
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")


def _identity(fd):
    st = os.fstat(fd)
    return st.st_dev, st.st_ino


class _Operation:
    def __init__(self, path, deadline_ms):
        reader._check(type(deadline_ms) is int and 1 <= deadline_ms <= 120000)
        publication._path_check(path)
        self.path = path
        self.end = time.monotonic() + deadline_ms / 1000
        self.owner = reader._Owner()
        self.pid = os.getpid()
        self.guard = threading.Lock()
        self.guard.acquire()
        self.root = None
        self.parent = None
        self.temp = None
        self.temp_fd = None
        self.attempted = False

    def deadline(self):
        reader._check(time.monotonic() < self.end)

    def namespace(self):
        self.deadline()
        reader._private(os.fstat(self.root), 0o700, True)
        fresh = reader._root(self.owner, self.path)
        try:
            reader._check(_identity(fresh) == _identity(self.root))
        finally:
            self.owner.close(fresh)
        if self.parent is None:
            try:
                os.stat("snapshots", dir_fd=self.root, follow_symlinks=False)
            except FileNotFoundError:
                pass
            else:
                raise ValueError("namespace appeared")
        else:
            reader._private(os.fstat(self.parent), 0o700, True)
            st = os.stat("snapshots", dir_fd=self.root, follow_symlinks=False)
            reader._check((st.st_dev, st.st_ino) == _identity(self.parent))

    def open(self, exclusive):
        self.root = reader._root(self.owner, self.path)
        try:
            self.parent = self.owner.open("snapshots", reader._DIR, parent=self.root)
        except FileNotFoundError:
            self.namespace()
            try:
                os.stat("snapshots", dir_fd=self.root, follow_symlinks=False)
            except FileNotFoundError:
                return False
            raise ValueError from None
        reader._private(os.fstat(self.parent), 0o700, True)
        while True:
            self.deadline()
            try:
                fcntl.flock(
                    self.parent, (fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH) | fcntl.LOCK_NB
                )
                break
            except BlockingIOError:
                time.sleep(min(0.01, max(0, self.end - time.monotonic())))
        self.namespace()
        return True

    def pointer(self):
        self.deadline()
        try:
            data, _ = reader._read(
                self.owner, self.root, "current.json", 512, deadline=self.deadline
            )
        except FileNotFoundError:
            try:
                os.stat("current.json", dir_fd=self.root, follow_symlinks=False)
            except FileNotFoundError:
                return None
            raise ValueError from None
        return parse_pointer(data)

    def load(self, originals, derived, pointer):
        self.deadline()
        data = reader.load_directory(originals, derived, self.path, pointer.snapshot_id)
        self.deadline()
        reader._check(data.snapshot_id == pointer.snapshot_id)
        self.namespace()
        return Selection(pointer, data)

    def cleanup(self):
        if os.getpid() != self.pid:
            if self not in _pending:
                _pending.append(self)
            return ValueError("creator process required")
        error = None
        try:
            if self.temp is not None:
                try:
                    st = os.stat(self.temp, dir_fd=self.root, follow_symlinks=False)
                except FileNotFoundError:
                    reader._check(self.attempted)
                else:
                    reader._check(
                        self.temp_fd is not None
                        and (st.st_dev, st.st_ino) == _identity(self.temp_fd)
                    )
                    os.unlink(self.temp, dir_fd=self.root)
                self.temp = None
        except BaseException as exc:
            error = exc
        if error is None:
            error = self.owner.cleanup()
        if error is not None or self.owner.unknown:
            if self not in _pending:
                _pending.append(self)
        return error

    def retry_cleanup(self):
        reader._check(os.getpid() == self.pid and self in _pending)
        guard = self.guard
        reader._check(guard.acquire(blocking=False))
        try:
            error = self.cleanup()
            if error is not None:
                if not isinstance(error, Exception):
                    raise error
                return error
            if self.owner.unknown:
                return CleanupPendingError("descriptor close outcome unknown")
            _pending.remove(self)
            return None
        finally:
            guard.release()


def _run(path, deadline_ms, action):
    op = None
    error = None
    result = None
    try:
        op = _Operation(path, deadline_ms)
        result = action(op)
    except BaseException as exc:
        error = exc
    if op is not None:
        guard = op.guard
        try:
            cleanup = op.cleanup()
        finally:
            guard.release()
        if cleanup is not None:
            if error is None:
                error = cleanup
            elif isinstance(error, Exception) and not isinstance(cleanup, Exception):
                error = cleanup
    if error is None and op is not None:
        try:
            op.deadline()
        except BaseException as exc:
            error = exc
    if error is not None:
        if isinstance(error, Exception):
            raise SelectionError(op is not None and op.attempted) from error
        raise error
    return result


def read_selected_data(originals, derived, store_root, *, deadline_ms=30000):
    """Read current immutable DATA under the publication namespace lock."""

    def read(op):
        exists = op.open(False)
        pointer = op.pointer()
        if not exists:
            reader._check(pointer is None)
        result = None if pointer is None else op.load(originals, derived, pointer)
        op.namespace()
        reader._check(op.pointer() == pointer)
        return result

    return _run(store_root, deadline_ms, read)


def compare_and_select_data(
    originals,
    derived,
    store_root,
    candidate_snapshot_id,
    expected_pointer_bytes,
    *,
    deadline_ms=30000,
):
    """Compare exact current bytes and select a freshly source-validated candidate."""

    def select(op):
        reader._check(
            type(candidate_snapshot_id) is str
            and re.fullmatch(r"sha256:[0-9a-f]{64}", candidate_snapshot_id)
        )
        if expected_pointer_bytes is not None:
            parse_pointer(expected_pointer_bytes)
        reader._check(op.open(True))
        current = op.pointer()
        if current is not None:
            op.load(originals, derived, current)
        reader._check(
            (None if current is None else current.pointer_bytes) == expected_pointer_bytes
        )
        generation = 1 if current is None else current.generation + 1
        reader._check(generation <= _MAX_GENERATION)
        new = parse_pointer(_encode(generation, candidate_snapshot_id))
        op.load(originals, derived, new)
        op.namespace()
        name = ".selection-" + secrets.token_hex(24)
        fd = os.open(
            name,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC,
            0o600,
            dir_fd=op.root,
        )
        op.owner.fds.add(fd)
        op.temp, op.temp_fd = name, fd
        reader._private(os.fstat(fd), 0o600, False)
        remaining = memoryview(new.pointer_bytes)
        while remaining:
            op.deadline()
            count = os.write(fd, remaining)
            reader._check(count > 0)
            remaining = remaining[count:]
        os.fchmod(fd, 0o400)
        os.fsync(fd)
        reader._private(os.fstat(fd), 0o400, False)
        reader._check(os.fstat(fd).st_size == len(new.pointer_bytes))
        reader._linked(op.root, name, fd)
        op.namespace()
        reader._check(op.pointer() == current)
        op.attempted = True
        os.replace(name, "current.json", src_dir_fd=op.root, dst_dir_fd=op.root)
        op.temp = None
        os.fsync(op.root)
        op.namespace()
        actual = op.pointer()
        reader._check(actual == new)
        result = op.load(originals, derived, actual)
        op.namespace()
        reader._check(op.pointer() == new)
        return result

    return _run(store_root, deadline_ms, select)
