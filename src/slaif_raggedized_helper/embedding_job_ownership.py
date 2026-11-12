"""Nonblocking, per-job POSIX ownership under a trusted private directory."""

import fcntl
import os
from pathlib import Path
import re
import secrets
import stat


class OwnershipRefused(ValueError):
    """Ownership could not be safely established or verified."""


def _refuse():
    raise OwnershipRefused('ownership refused') from None


def _check(st, mode, kind):
    if st.st_uid != os.geteuid() or stat.S_IMODE(st.st_mode) != mode or not kind(st.st_mode):
        _refuse()


_active = {}


class Lease:
    __slots__ = (
        '_job_id', '_owner_id', '_owner_pid', '_fd', '_dirfd', '_rootfd', '_dir_inode', '_inode'
    )

    def __init__(self, *args):
        _refuse()

    @property
    def job_id(self):
        return self._job_id

    @property
    def owner_id(self):
        return self._owner_id

    @property
    def owner_pid(self):
        return self._owner_pid

    def assert_owned(self):
        try:
            if (self._fd is None or os.getpid() != self._owner_pid
                    or _active.get(id(self)) is not self):
                _refuse()
            directory = os.stat('embedding_job_locks', dir_fd=self._rootfd,
                                follow_symlinks=False)
            if (directory.st_dev, directory.st_ino) != self._dir_inode:
                _refuse()
            st = os.fstat(self._fd)
            _check(st, 0o600, stat.S_ISREG)
            entry = os.stat(self._job_id[7:], dir_fd=self._dirfd, follow_symlinks=False)
            if st.st_nlink != 1 or (st.st_dev, st.st_ino) != self._inode or (
                entry.st_dev, entry.st_ino
            ) != self._inode:
                _refuse()
            fcntl.flock(self._fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except Exception:
            _refuse()

    def close(self):
        if self._fd is None:
            return
        fd, self._fd = self._fd, None
        _active.pop(id(self), None)
        failure = None
        if os.getpid() == self._owner_pid:
            try:
                fcntl.flock(fd, fcntl.LOCK_UN)
            except BaseException as exc:
                failure = exc
        for handle in (fd, self._dirfd, self._rootfd):
            try:
                os.close(handle)
            except BaseException as exc:
                if failure is None or (isinstance(failure, Exception)
                                       and not isinstance(exc, Exception)):
                    failure = exc
        if failure is not None:
            if not isinstance(failure, Exception):
                raise failure
            _refuse()

    def __enter__(self):
        try:
            self.assert_owned()
        except BaseException as exc:
            try:
                self.close()
            except BaseException:
                exc.add_note('ownership cleanup refused')
            raise
        return self

    def __exit__(self, *args):
        try:
            self.close()
        except OwnershipRefused:
            if args[1] is None:
                raise
            args[1].add_note('ownership cleanup refused')


def claim(root, job_id):
    """Acquire a lease immediately, or raise OwnershipRefused."""
    fd = dirfd = rootfd = None
    try:
        if type(root) not in (str, Path) and not isinstance(root, Path):
            _refuse()
        path = str(root)
        if (not path.startswith('/') or path == '/' or os.path.normpath(path) != path
                or len(path.encode('utf-8')) > 4096 or type(job_id) is not str
                or re.fullmatch(r'sha256:[0-9a-f]{64}', job_id) is None):
            _refuse()
        flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
        rootfd = os.open(path, flags)
        _check(os.fstat(rootfd), 0o700, stat.S_ISDIR)
        try:
            os.mkdir('embedding_job_locks', 0o700, dir_fd=rootfd)
        except FileExistsError:
            pass
        dirfd = os.open('embedding_job_locks', flags, dir_fd=rootfd)
        directory = os.fstat(dirfd)
        _check(directory, 0o700, stat.S_ISDIR)
        fd = os.open(job_id[7:], os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_CLOEXEC
                     | os.O_NONBLOCK, 0o600, dir_fd=dirfd)
        st = os.fstat(fd)
        _check(st, 0o600, stat.S_ISREG)
        if st.st_nlink != 1:
            _refuse()
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        lease = object.__new__(Lease)
        lease._job_id = job_id
        lease._owner_id = secrets.token_hex(16)
        lease._owner_pid = os.getpid()
        lease._fd, lease._dirfd, lease._inode = fd, dirfd, (st.st_dev, st.st_ino)
        lease._rootfd = rootfd
        lease._dir_inode = (directory.st_dev, directory.st_ino)
        fd = dirfd = rootfd = None
        _active[id(lease)] = lease
        return lease
    except Exception:
        _refuse()
    finally:
        for handle in (fd, dirfd, rootfd):
            if handle is not None:
                os.close(handle)
