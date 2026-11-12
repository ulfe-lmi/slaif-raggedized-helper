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
_pending = []


class CleanupOwner:
    """Retained history of one finite cleanup attempt, not proof of a lock."""

    def __init__(self):
        self.handles = []
        self.attempts = []
        self.pending = False

    def add(self, fd):
        self.handles.append(fd)
        return fd

    def cleanup(self, unlock_fd=None):
        failures = []
        if unlock_fd is not None:
            try:
                fcntl.flock(unlock_fd, fcntl.LOCK_UN)
            except BaseException as exc:
                failures.append(exc)
                self.attempts.append(('unlock', unlock_fd, 'unknown'))
            else:
                self.attempts.append(('unlock', unlock_fd, 'done'))
        for fd in reversed(self.handles):
            try:
                os.close(fd)
            except BaseException as exc:
                failures.append(exc)
                self.attempts.append(('close', fd, 'unknown'))
            else:
                self.attempts.append(('close', fd, 'done'))
        self.handles.clear()
        self.pending = bool(failures)
        if self.pending:
            _pending.append(self)
        return failures


def _attach(exc, owner):
    if owner.pending:
        exc.cleanup_owner = owner
        exc.add_note('ownership cleanup pending or unknown; retained owner is not proof of lock')


def _raise_failure(original, failures, owner):
    # Original interrupt wins; a newly encountered interrupt wins over ordinary errors.
    selected = original
    if isinstance(original, Exception):
        selected = next((e for e in failures if not isinstance(e, Exception)), original)
    if isinstance(selected, Exception):
        selected = OwnershipRefused('ownership refused')
    _attach(selected, owner)
    raise selected from None


class Lease:
    __slots__ = (
        '_job_id', '_owner_id', '_owner_pid', '_fd', '_dirfd', '_rootfd', '_dir_inode', '_inode',
        '_cleanup_owner', '_state'
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

    @property
    def cleanup_owner(self):
        return self._cleanup_owner if self._state == 'pending' else None

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
        if self._state == 'closed':
            return
        if self._state == 'pending':
            error = OwnershipRefused('ownership cleanup pending or unknown')
            _attach(error, self._cleanup_owner)
            raise error
        fd, self._fd = self._fd, None
        _active.pop(id(self), None)
        self._state = 'pending'
        failures = self._cleanup_owner.cleanup(fd if os.getpid() == self._owner_pid else None)
        if failures:
            _raise_failure(failures[0], failures[1:], self._cleanup_owner)
        self._state = 'closed'

    def __enter__(self):
        try:
            self.assert_owned()
        except BaseException as exc:
            try:
                self.close()
            except BaseException as cleanup:
                _attach(exc, self._cleanup_owner)
                if isinstance(exc, Exception) and not isinstance(cleanup, Exception):
                    raise
            raise
        return self

    def __exit__(self, exc_type, exc, tb):
        try:
            self.close()
        except BaseException as cleanup:
            if exc is None:
                raise
            _attach(exc, self._cleanup_owner)
            if isinstance(exc, Exception) and not isinstance(cleanup, Exception):
                raise
        return False


def claim(root, job_id):
    """Acquire a lease immediately, or raise OwnershipRefused."""
    owner = CleanupOwner()
    lease = None
    try:
        if type(root) not in (str, Path) and not isinstance(root, Path):
            _refuse()
        path = str(root)
        if (not path.startswith('/') or path == '/' or os.path.normpath(path) != path
                or len(path.encode('utf-8')) > 4096 or type(job_id) is not str
                or re.fullmatch(r'sha256:[0-9a-f]{64}', job_id) is None):
            _refuse()
        flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
        rootfd = owner.add(os.open(path, flags))
        _check(os.fstat(rootfd), 0o700, stat.S_ISDIR)
        try:
            os.mkdir('embedding_job_locks', 0o700, dir_fd=rootfd)
        except FileExistsError:
            pass
        dirfd = owner.add(os.open('embedding_job_locks', flags, dir_fd=rootfd))
        directory = os.fstat(dirfd)
        _check(directory, 0o700, stat.S_ISDIR)
        fd = owner.add(os.open(job_id[7:], os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_CLOEXEC
                               | os.O_NONBLOCK, 0o600, dir_fd=dirfd))
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
        lease._cleanup_owner, lease._state = owner, 'live'
        _active[id(lease)] = lease
        return lease
    except BaseException as exc:
        if lease is not None:
            _active.pop(id(lease), None)
        failures = owner.cleanup()
        _raise_failure(exc, failures, owner)
