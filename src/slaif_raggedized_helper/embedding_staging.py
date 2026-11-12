"""Private, temporary staging of an admitted embedding inventory."""

import hashlib
import math
import os
import secrets
import stat
import sys
import tempfile
import time
from contextlib import contextmanager
from dataclasses import dataclass, replace
from pathlib import Path

from . import embedding_artifacts as artifacts, embedding_space


class StagingRefused(ValueError):
    """Staging failed without exposing caller input."""


@dataclass(frozen=True)
class Staged:
    path: Path
    manifest_bytes: bytes
    space: embedding_space.AdmittedSpace


def _identity(st):
    return st.st_dev, st.st_ino


def _parent(path, *, default):
    """Pin a parent through no-follow components; callers trust its ancestry."""
    if not isinstance(path, (str, Path)):
        raise ValueError
    path = os.fspath(path)
    if (type(path) is not str or not path.startswith("/") or path == "/"
            or os.path.normpath(path) != path or len(os.fsencode(path)) > 4096):
        raise ValueError
    fd = os.open("/", os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for part in path.split("/")[1:]:
            nxt = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = nxt
        st = os.fstat(fd)
        private = st.st_uid == os.geteuid() and not st.st_mode & 0o077
        sticky = (default and st.st_uid in (0, os.geteuid())
                  and bool(st.st_mode & stat.S_ISVTX))
        if not (private or sticky):
            raise ValueError
        return fd
    except BaseException:
        os.close(fd)
        raise


def _same_name(parent_fd, name, expected):
    return _identity(os.stat(name, dir_fd=parent_fd, follow_symlinks=False)) == expected


def _path_matches(parent_path, parent_fd, name, stage_fd, default):
    check = _parent(parent_path, default=default)
    try:
        return (_identity(os.fstat(check)) == _identity(os.fstat(parent_fd))
                and _same_name(check, name, _identity(os.fstat(stage_fd))))
    finally:
        os.close(check)


def _record_directory(parent_fd, name, entries):
    """Record a just-created name before attempting to acquire its descriptor."""
    st = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
    if not stat.S_ISDIR(st.st_mode) or st.st_uid != os.geteuid():
        raise ValueError
    identity = _identity(st)
    index = len(entries)
    entries.append((parent_fd, name, identity, True, None))
    fd = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent_fd)
    try:
        if _identity(os.fstat(fd)) != identity:
            raise ValueError
        entries[index] = (parent_fd, name, identity, True, fd)
    except BaseException:
        os.close(fd)
        raise
    return fd


def _cleanup(entries):
    """Remove only recorded names still bound to the inodes we created."""
    failed = False
    for _, _, _, is_dir, fd in entries:
        if is_dir and fd is not None:
            try:
                os.fchmod(fd, 0o700)
            except OSError:
                failed = True
    for parent_fd, name, identity, is_dir, fd in reversed(entries):
        try:
            if not _same_name(parent_fd, name, identity):
                failed = True
                continue
            if is_dir:
                os.rmdir(name, dir_fd=parent_fd)
            else:
                os.unlink(name, dir_fd=parent_fd)
        except OSError:
            failed = True
    for _, _, _, _, fd in reversed(entries):
        if fd is not None:
            try:
                os.close(fd)
            except OSError:
                failed = True
    if failed:
        raise RuntimeError("staging cleanup failed") from None


@contextmanager
def stage(manifest_bytes, artifact_root, definition, tokenizer_definition,
          expected_inventory_id, *, parent=None, timeout=120):
    """Yield a verified private copy for the lifetime of this context."""
    entries = []
    parent_fd = root = None
    try:
        try:
            if (type(timeout) not in (int, float) or not math.isfinite(timeout)
                    or not 0 < timeout <= 120):
                raise ValueError
            deadline = time.monotonic() + timeout

            def remaining():
                value = deadline - time.monotonic()
                if value <= 0:
                    raise ValueError
                return min(value, 30)

            space = embedding_space.admit(manifest_bytes, artifact_root, definition,
                                          tokenizer_definition, expected_inventory_id,
                                          timeout=remaining())
            _, files, _, _ = artifacts._admit(manifest_bytes)
            default = parent is None
            parent_path = tempfile.gettempdir() if default else parent
            parent_fd = _parent(parent_path, default=default)
            parent_path = Path(parent_path)
            # Random names are created exclusively relative to the pinned parent.
            for _ in range(10):
                name = "embedding-stage-" + secrets.token_hex(16)
                try:
                    os.mkdir(name, 0o700, dir_fd=parent_fd)
                    break
                except FileExistsError:
                    continue
            else:
                raise ValueError
            stage_fd = _record_directory(parent_fd, name, entries)
            os.fchmod(stage_fd, 0o700)
            stage_path = parent_path / name
            root = artifacts._root(artifact_root)
            dirs = {(): stage_fd}
            for item in files:
                remaining()
                parts = artifacts._path(item.path)
                for index in range(1, len(parts)):
                    key = tuple(parts[:index])
                    if key not in dirs:
                        pfd = dirs[key[:-1]]
                        os.mkdir(key[-1], 0o700, dir_fd=pfd)
                        fd = _record_directory(pfd, key[-1], entries)
                        os.fchmod(fd, 0o700)
                        dirs[key] = fd
                pfd = dirs[tuple(parts[:-1])]
                source_fd = artifacts._open_file(root, item.path)
                try:
                    before = os.fstat(source_fd)
                    out = os.open(parts[-1], os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                                  0o600, dir_fd=pfd)
                    try:
                        entries.append((pfd, parts[-1], _identity(os.fstat(out)), False, None))
                        os.fchmod(out, 0o600)
                        digest = hashlib.sha256()
                        count = 0
                        while True:
                            remaining()
                            chunk = os.read(source_fd, 65536)
                            if not chunk:
                                break
                            count += len(chunk)
                            if count > item.size:
                                raise ValueError
                            digest.update(chunk)
                            view = memoryview(chunk)
                            while view:
                                remaining()
                                written = os.write(out, view)
                                if written <= 0:
                                    raise OSError
                                view = view[written:]
                        after = os.fstat(source_fd)
                        if (count != item.size or digest.hexdigest() != item.sha256 or
                                artifacts._signature(before) != artifacts._signature(after)):
                            raise ValueError
                        os.fchmod(out, 0o400)
                    finally:
                        os.close(out)
                finally:
                    os.close(source_fd)
            if not _path_matches(parent_path, parent_fd, name, stage_fd, default):
                raise ValueError
            staged_space = embedding_space.admit(
                manifest_bytes, stage_path, definition,
                replace(tokenizer_definition, artifact=stage_path / "tokenizer.json"),
                expected_inventory_id, timeout=remaining())
            if (staged_space != space or
                    not _path_matches(parent_path, parent_fd, name, stage_fd, default)):
                raise ValueError
            for fd in reversed(list(dirs.values())):
                os.fchmod(fd, 0o500)
            remaining()
        except Exception:
            raise StagingRefused("staging refused") from None
        yield Staged(stage_path, manifest_bytes, staged_space)
    finally:
        active_exception = sys.exception()
        try:
            _cleanup(entries)
        except Exception:
            if active_exception is None:
                raise
            active_exception.add_note("staging cleanup failed")
        finally:
            if root is not None:
                os.close(root)
            if parent_fd is not None:
                os.close(parent_fd)
