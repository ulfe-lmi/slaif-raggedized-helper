"""Publish immutable, private snapshot DATA; this does not grant authority."""

import ctypes
import errno
import fcntl
import hashlib
import os
import secrets
import stat
import threading
import time
import unicodedata
from dataclasses import dataclass

from . import raw_snapshot_directory as reader, raw_snapshot_files, raw_snapshot_manifest


class PublicationError(ValueError):
    """Content-free refusal; a candidate may exist after a rename attempt."""

    def __init__(self, snapshot_id=None, publication_may_exist=False):
        super().__init__("snapshot publication refused")
        self.snapshot_id = snapshot_id
        self.publication_may_exist = publication_may_exist


class CleanupPendingError(RuntimeError):
    """Unknown close outcomes remain pending and cannot be retried."""


@dataclass(frozen=True, slots=True)
class Publication:
    snapshot_id: str
    created: bool
    data: raw_snapshot_files.BoundSnapshotData


# Keep owners with uncertain cleanup reachable; do not retry uncertain descriptor closes.
_pending = []


def _rename_noreplace(parent, old, new):
    libc = ctypes.CDLL(None, use_errno=True)
    try:
        call = libc.renameat2
    except AttributeError:
        raise OSError(errno.ENOSYS, "no atomic no-replace primitive") from None
    call.argtypes = (ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint)
    call.restype = ctypes.c_int
    if call(parent, os.fsencode(old), parent, os.fsencode(new), 1) != 0:
        code = ctypes.get_errno()
        raise OSError(code, "atomic publication refused")


def _path_check(path):
    reader._check(
        type(path) is str
        and path.startswith("/")
        and path != "/"
        and len(path.encode("utf-8")) <= 4096
        and all(unicodedata.category(c) != "Cc" for c in path)
        and all(p not in ("", ".", "..") for p in path[1:].split("/"))
    )


def _identity(st):
    return st.st_dev, st.st_ino


class _Operation:
    def __init__(self):
        self.owner = reader._Owner()
        self.pid = os.getpid()
        self.root = None
        self.parent = None
        self.temp = None
        self.target = None
        self.created = []
        self.rename_attempted = False
        self.published = False
        self.guard = threading.Lock()
        self.guard.acquire()

    def linked(self, parent, name, fd):
        reader._check(
            _identity(os.stat(name, dir_fd=parent, follow_symlinks=False))
            == _identity(os.fstat(fd))
        )

    def cleanup_tree(self):
        if self.temp is None or self.published:
            return
        reader._check(os.getpid() == self.pid)
        # Only delete entries that still name the exact inodes created by this operation.
        try:
            self.linked(self.parent, self.temp, self.target)
        except FileNotFoundError:
            if not self.rename_attempted:
                raise
            # The rename may have succeeded. Never follow or remove its final name.
            self.temp = None
            return
        for parent, name, fd, _ in self.created:
            self.linked(parent, name, fd)
        os.fchmod(self.target, 0o700)
        for _, _, fd, isdir in self.created:
            if isdir:
                os.fchmod(fd, 0o700)
        while self.created:
            parent, name, fd, isdir = self.created[-1]
            self.linked(parent, name, fd)
            if isdir:
                os.rmdir(name, dir_fd=parent)
            else:
                os.unlink(name, dir_fd=parent)
            self.created.pop()
        self.linked(self.parent, self.temp, self.target)
        os.rmdir(self.temp, dir_fd=self.parent)
        self.temp = None

    def retry_cleanup(self):
        """Retry known creator-owned resources; report an unknown close as pending."""
        reader._check(os.getpid() == self.pid and self in _pending)
        guard = self.guard
        reader._check(guard.acquire(blocking=False))
        try:
            reader._check(self in _pending)
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

    def cleanup(self):
        error = None
        try:
            self.cleanup_tree()
        except BaseException as exc:
            error = exc
            if self not in _pending:
                _pending.append(self)
        if error is not None:
            return error
        other = self.owner.cleanup()
        if other is not None and (
            error is None or isinstance(error, Exception) and not isinstance(other, Exception)
        ):
            error = other
        if self.owner.unknown and self not in _pending:
            _pending.append(self)
        return error


def _stage(op, core, files):
    parent = op.parent
    name = ".tmp-" + secrets.token_hex(24)
    os.mkdir(name, 0o700, dir_fd=parent)
    op.temp = name
    op.target = op.owner.open(name, reader._DIR, parent=parent)
    op.linked(parent, name, op.target)
    dirs = {"": op.target}
    for path, data in ((".core.json", core), *files):
        parts = path.split("/")
        for i in range(1, len(parts)):
            prefix = "/".join(parts[:i])
            if prefix not in dirs:
                up = dirs["/".join(parts[: i - 1])]
                os.mkdir(parts[i - 1], 0o700, dir_fd=up)
                fd = op.owner.open(parts[i - 1], reader._DIR, parent=up)
                op.created.append((up, parts[i - 1], fd, True))
                op.linked(up, parts[i - 1], fd)
                dirs[prefix] = fd
        up = dirs["/".join(parts[:-1])]
        fd = op.owner.open(
            parts[-1],
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC,
            parent=up,
        )
        op.created.append((up, parts[-1], fd, False))
        reader._check(stat.S_ISREG(os.fstat(fd).st_mode) and os.fstat(fd).st_nlink == 1)
        view = memoryview(data)
        while view:
            n = os.write(fd, view[:1048576])
            reader._check(n > 0)
            view = view[n:]
        os.fchmod(fd, 0o400)
        os.fsync(fd)
        reader._private(os.fstat(fd), 0o400, False)
        reader._check(os.fstat(fd).st_size == len(data))
        op.linked(up, parts[-1], fd)
    for fd in reversed(tuple(dirs.values())):
        os.fchmod(fd, 0o500)
        os.fsync(fd)
    return dirs


def _publish(op, originals, derived, store_root, core_bytes, files):
    # The actual original-backed validation precedes any filesystem mutation.
    expected = raw_snapshot_files.validate_files(originals, derived, core_bytes, files)
    snapshot_id = expected.snapshot_id
    manifest = raw_snapshot_manifest.parse(core_bytes)
    paths = {d.path for d in manifest.files} | {".core.json"}
    dirs = {"/".join(p.split("/")[:i]) for p in paths for i in range(1, len(p.split("/")))}
    reader._check(len(paths) == len(files) + 1 and not paths & dirs and len(paths | dirs) <= 1033)
    _path_check(store_root)
    op.root = reader._root(op.owner, store_root)
    try:
        os.mkdir("snapshots", 0o700, dir_fd=op.root)
    except FileExistsError:
        pass
    else:
        os.fsync(op.root)
    op.parent = op.owner.open("snapshots", reader._DIR, parent=op.root)
    reader._private(os.fstat(op.parent), 0o700, True)
    op.linked(op.root, "snapshots", op.parent)
    # Serialize cooperating writers so their private staging does not invalidate the
    # reader's namespace-stability proof. Non-cooperating changes still refuse.
    deadline = time.monotonic() + 30
    while True:
        try:
            fcntl.flock(op.parent, fcntl.LOCK_EX | fcntl.LOCK_NB)
            break
        except BlockingIOError:
            reader._check(time.monotonic() < deadline)
            time.sleep(0.01)
    op.linked(op.root, "snapshots", op.parent)
    os.fsync(op.root)
    _stage(op, core_bytes, files)
    before = reader._walk(op.owner, op.target, paths, dirs, lambda: None)
    for path, expected_bytes in ((".core.json", core_bytes), *files):
        parent, name = reader._relative_parent(op.owner, op.target, path)
        try:
            blob, signature = reader._read(
                op.owner, parent, name, len(expected_bytes), len(expected_bytes)
            )
            reader._check(blob == expected_bytes and signature == before[path])
        finally:
            if parent != op.target:
                op.owner.close(parent)
    reader._check(reader._walk(op.owner, op.target, paths, dirs, lambda: None) == before)
    op.linked(op.parent, op.temp, op.target)
    op.linked(op.root, "snapshots", op.parent)
    fresh = reader._root(op.owner, store_root)
    reader._check(_identity(os.fstat(fresh)) == _identity(os.fstat(op.root)))
    op.owner.close(fresh)
    op.rename_attempted = True
    try:
        _rename_noreplace(op.parent, op.temp, snapshot_id[7:])
    except OSError as exc:
        if exc.errno != errno.EEXIST:
            raise
        op.cleanup_tree()
        created = False
    else:
        op.published = True
        os.fsync(op.parent)
        created = True
    op.linked(op.root, "snapshots", op.parent)
    fresh = reader._root(op.owner, store_root)
    reader._check(_identity(os.fstat(fresh)) == _identity(os.fstat(op.root)))
    op.owner.close(fresh)
    data = reader.load_directory(originals, derived, store_root, snapshot_id)
    reader._check(data == expected and data.core_bytes == core_bytes)
    op.linked(op.root, "snapshots", op.parent)
    reader._private(os.fstat(op.parent), 0o700, True)
    fresh = reader._root(op.owner, store_root)
    reader._check(_identity(os.fstat(fresh)) == _identity(os.fstat(op.root)))
    op.owner.close(fresh)
    if created:
        op.linked(op.parent, snapshot_id[7:], op.target)
    return Publication(snapshot_id, created, data)


def publish_directory(originals, derived, store_root, core_bytes, files):
    """Validate source, publish once, and freshly read detached snapshot DATA."""
    op = _Operation()
    result = None
    error = None
    try:
        result = _publish(op, originals, derived, store_root, core_bytes, files)
    except BaseException as exc:
        error = exc
    guard = op.guard
    try:
        cleanup = op.cleanup()
    finally:
        guard.release()
    if cleanup is not None and (
        error is None or isinstance(error, Exception) and not isinstance(cleanup, Exception)
    ):
        error = cleanup
    if error is not None:
        if isinstance(error, Exception):
            candidate = (
                "sha256:" + hashlib.sha256(core_bytes).hexdigest()
                if type(core_bytes) is bytes and len(core_bytes) <= 262144
                else None
            )
            raise PublicationError(candidate, op.rename_attempted) from None
        raise error
    return result
