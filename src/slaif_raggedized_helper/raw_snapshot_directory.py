"""Bounded private snapshot directory DATA reader; no authorization or publication."""

import hashlib
import os
import re
import stat
import sys
import time
import unicodedata

from . import raw_snapshot_dense, raw_snapshot_files, raw_snapshot_manifest


class DirectoryError(ValueError):
    """Content-free directory refusal."""


# Owners with uncertain closes remain reachable. A numeric descriptor is never retried.
_pending = []
_DIR = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
_FILE = os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK


def _check(value):
    if not value:
        raise ValueError


def _signature(st):
    return (
        st.st_dev,
        st.st_ino,
        st.st_mode,
        st.st_uid,
        st.st_nlink,
        st.st_size,
        st.st_mtime_ns,
        st.st_ctime_ns,
    )


class _Owner:
    def __init__(self):
        self.pid = os.getpid()
        self.fds = set()
        self.unknown = set()

    def open(self, path, flags, *, parent=None):
        _check(os.getpid() == self.pid)
        fd = os.open(path, flags, dir_fd=parent)
        self.fds.add(fd)
        return fd

    def close(self, fd):
        _check(os.getpid() == self.pid and fd in self.fds)
        self.fds.remove(fd)
        self.unknown.add(fd)
        try:
            os.close(fd)
        except BaseException:
            if self not in _pending:
                _pending.append(self)
            raise
        self.unknown.remove(fd)

    def cleanup(self):
        if os.getpid() != self.pid:
            if self not in _pending:
                _pending.append(self)
            return None
        error = None
        for fd in tuple(self.fds):
            try:
                self.close(fd)
            except BaseException as exc:
                if error is None or isinstance(error, Exception) and not isinstance(exc, Exception):
                    error = exc
        return error


def _finish(owner, fd):
    active = sys.exception()
    try:
        owner.close(fd)
    except BaseException as exc:
        if active is None or isinstance(active, Exception) and not isinstance(exc, Exception):
            raise


def _ancestor(st):
    _check(stat.S_ISDIR(st.st_mode) and st.st_uid in (0, os.getuid()))
    _check(not (st.st_mode & 0o022) or (st.st_uid == 0 and st.st_mode & stat.S_ISVTX))


def _private(st, mode, directory):
    _check(
        (stat.S_ISDIR(st.st_mode) if directory else stat.S_ISREG(st.st_mode))
        and st.st_uid == os.getuid()
        and stat.S_IMODE(st.st_mode) == mode
    )
    if not directory:
        _check(st.st_nlink == 1)


def _root(owner, path):
    fd = owner.open("/", _DIR)
    _ancestor(os.fstat(fd))
    for component in path[1:].split("/"):
        child = owner.open(component, _DIR, parent=fd)
        _ancestor(os.fstat(child))
        owner.close(fd)
        fd = child
    _private(os.fstat(fd), 0o700, True)
    return fd


def _linked(parent, name, fd):
    _check(
        _signature(os.stat(name, dir_fd=parent, follow_symlinks=False)) == _signature(os.fstat(fd))
    )


def _read(owner, parent, name, limit, expected_size=None, deadline=lambda: None):
    fd = owner.open(name, _FILE, parent=parent)
    try:
        before = os.fstat(fd)
        _private(before, 0o400, False)
        _check(
            before.st_size <= limit and (expected_size is None or before.st_size == expected_size)
        )
        chunks = []
        remaining = before.st_size
        while remaining:
            deadline()
            chunk = os.read(fd, min(remaining, 1048576))
            _check(chunk)
            chunks.append(chunk)
            remaining -= len(chunk)
        _check(not os.read(fd, 1))
        _check(_signature(before) == _signature(os.fstat(fd)))
        _linked(parent, name, fd)
        return b"".join(chunks), _signature(before)
    finally:
        _finish(owner, fd)


def _walk(owner, target, files, dirs, deadline):
    found = {}
    count = 0

    def visit(fd, prefix):
        nonlocal count
        with os.scandir(fd) as entries:
            for entry in entries:
                deadline()
                count += 1
                _check(count <= 1033)
                path = prefix + entry.name
                _check(path in files or path in dirs)
                st = os.stat(entry.name, dir_fd=fd, follow_symlinks=False)
                isdir = path in dirs
                _private(st, 0o500 if isdir else 0o400, isdir)
                found[path] = _signature(st)
                if isdir:
                    child = owner.open(entry.name, _DIR, parent=fd)
                    try:
                        _linked(fd, entry.name, child)
                        visit(child, path + "/")
                        _linked(fd, entry.name, child)
                    finally:
                        _finish(owner, child)

    visit(target, "")
    _check(set(found) == files | dirs)
    return found


def _relative_parent(owner, target, path):
    parts = path.split("/")
    fd = target
    for part in parts[:-1]:
        child = owner.open(part, _DIR, parent=fd)
        _private(os.fstat(child), 0o500, True)
        _linked(fd, part, child)
        if fd != target:
            owner.close(fd)
        fd = child
    return fd, parts[-1]


def _load(owner, originals, derived, store_root, snapshot_id):
    end = time.monotonic() + 60

    def deadline():
        _check(time.monotonic() < end)

    _check(
        type(store_root) is str
        and store_root.startswith("/")
        and store_root != "/"
        and len(store_root.encode("utf-8")) <= 4096
        and all(unicodedata.category(c) != "Cc" for c in store_root)
        and all(p not in ("", ".", "..") for p in store_root[1:].split("/"))
    )
    _check(type(snapshot_id) is str and re.fullmatch(r"sha256:[0-9a-f]{64}", snapshot_id))
    root = _root(owner, store_root)
    snapshots = owner.open("snapshots", _DIR, parent=root)
    _private(os.fstat(snapshots), 0o700, True)
    target = owner.open(snapshot_id[7:], _DIR, parent=snapshots)
    _private(os.fstat(target), 0o500, True)
    _linked(root, "snapshots", snapshots)
    _linked(snapshots, snapshot_id[7:], target)
    namespace_signatures = tuple(_signature(os.fstat(fd)) for fd in (root, snapshots, target))
    core, core_sig = _read(owner, target, ".core.json", 262144, deadline=deadline)
    _check("sha256:" + hashlib.sha256(core).hexdigest() == snapshot_id)
    manifest = raw_snapshot_manifest.parse(core)
    files = {d.path for d in manifest.files} | {".core.json"}
    dirs = set()
    for path in files:
        parts = path.split("/")
        dirs.update("/".join(parts[:i]) for i in range(1, len(parts)))
    _check(not files & dirs)
    before = _walk(owner, target, files, dirs, deadline)
    _check(before[".core.json"] == core_sig)
    data = []
    for desc in manifest.files:
        deadline()
        limit = {
            "row_map": 16 * 1048576,
            "source_membership": 8 * 1048576,
            "lexical_terms": 16 * 1048576,
            "dense": raw_snapshot_dense.POLICY.max_bytes,
        }[desc.role]
        _check(desc.bytes <= limit)
        parent, name = _relative_parent(owner, target, desc.path)
        try:
            blob, sig = _read(owner, parent, name, desc.bytes, desc.bytes, deadline)
        finally:
            if parent != target:
                _finish(owner, parent)
        _check(sig == before[desc.path] and hashlib.sha256(blob).hexdigest() == desc.sha256)
        data.append((desc.path, blob))
    deadline()
    result = raw_snapshot_files.validate_files(originals, derived, core, tuple(data))
    deadline()
    _check(_walk(owner, target, files, dirs, deadline) == before)
    _linked(snapshots, snapshot_id[7:], target)
    _linked(root, "snapshots", snapshots)
    _check(
        tuple(_signature(os.fstat(fd)) for fd in (root, snapshots, target)) == namespace_signatures
    )
    fresh = _root(owner, store_root)
    _check(_signature(os.fstat(fresh)) == _signature(os.fstat(root)))
    owner.close(fresh)
    return result


def load_directory(originals, derived, store_root, snapshot_id):
    """Read and validate detached data from a private configured snapshot directory."""
    owner = _Owner()
    result = None
    error = None
    try:
        result = _load(owner, originals, derived, store_root, snapshot_id)
    except BaseException as exc:
        error = exc
    cleanup = owner.cleanup()
    if cleanup is not None and (
        error is None or isinstance(error, Exception) and not isinstance(cleanup, Exception)
    ):
        error = cleanup
    if error is not None:
        if isinstance(error, Exception):
            raise DirectoryError("snapshot directory refused") from None
        raise error
    return result
