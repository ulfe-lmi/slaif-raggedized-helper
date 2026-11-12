import os
import traceback

import pytest

from slaif_raggedized_helper.embedding_job_ownership import OwnershipRefused, claim

JOB = 'sha256:' + 'a' * 64


def test_lifecycle_and_fork(tmp_path):
    with claim(tmp_path, JOB) as lease:
        lease.assert_owned()
        with pytest.raises(OwnershipRefused):
            claim(tmp_path, JOB)
        pid = os.fork()
        if pid == 0:
            try:
                with pytest.raises(OwnershipRefused):
                    lease.assert_owned()
                lease.close()
                os._exit(0)
            except BaseException:
                os._exit(1)
        assert os.waitpid(pid, 0)[1] == 0
        lease.assert_owned()
        with pytest.raises(OwnershipRefused):
            claim(tmp_path, JOB)
    with pytest.raises(OwnershipRefused):
        lease.assert_owned()
    with claim(tmp_path, JOB):
        pass


def test_refusals_and_exception(tmp_path):
    marker = 'private-marker-938465'
    with pytest.raises(OwnershipRefused) as exc:
        claim(tmp_path / marker, marker)
    assert marker not in ''.join(traceback.format_exception(exc.value))
    with pytest.raises(RuntimeError, match='body'):
        with claim(tmp_path, JOB):
            raise RuntimeError('body')
    path = tmp_path / 'embedding_job_locks' / JOB[7:]
    inode = path.stat().st_ino
    assert path.stat().st_mode & 0o777 == 0o600
    with claim(tmp_path, JOB):
        assert path.stat().st_ino == inode
    path.chmod(0o644)
    with pytest.raises(OwnershipRefused):
        claim(tmp_path, JOB)
    assert path.stat().st_ino == inode


def test_replaced_and_fifo(tmp_path):
    lease = claim(tmp_path, JOB)
    path = tmp_path / 'embedding_job_locks' / JOB[7:]
    path.unlink()
    os.mkfifo(path, 0o600)
    with pytest.raises(OwnershipRefused):
        lease.assert_owned()
    with pytest.raises(OwnershipRefused):
        claim(tmp_path, JOB)
    lease.close()


def test_directory_replaced(tmp_path):
    with claim(tmp_path, JOB) as old:
        (tmp_path / 'embedding_job_locks').rename(tmp_path / 'old')
        with claim(tmp_path, JOB) as new:
            new.assert_owned()
            with pytest.raises(OwnershipRefused):
                old.assert_owned()


def test_cleanup_failure_preserves_body(tmp_path, monkeypatch):
    import fcntl

    real = fcntl.flock

    def fail_unlock(fd, op):
        if op == fcntl.LOCK_UN:
            raise OSError('private cleanup marker')
        return real(fd, op)

    lease = claim(tmp_path, JOB)
    monkeypatch.setattr(fcntl, 'flock', fail_unlock)
    with pytest.raises(RuntimeError, match='body') as exc:
        with lease:
            raise RuntimeError('body')
    assert 'private cleanup marker' not in ''.join(traceback.format_exception(exc.value))
    lease = claim(tmp_path, JOB)
    with pytest.raises(OwnershipRefused) as exc:
        lease.close()
    assert 'private cleanup marker' not in ''.join(traceback.format_exception(exc.value))


def test_private_missing_root_and_symlinks(tmp_path):
    import secrets

    marker = secrets.token_hex(24)
    with pytest.raises(OwnershipRefused) as exc:
        claim(tmp_path / marker, JOB)
    assert marker not in ''.join(traceback.format_exception(exc.value))
    target = tmp_path / 'target'
    target.mkdir(mode=0o700)
    link = tmp_path / 'link'
    link.symlink_to(target, target_is_directory=True)
    with pytest.raises(OwnershipRefused):
        claim(link, JOB)
    locks = tmp_path / 'embedding_job_locks'
    locks.symlink_to(target, target_is_directory=True)
    with pytest.raises(OwnershipRefused):
        claim(tmp_path, JOB)
    locks.unlink()
    locks.mkdir(mode=0o700)
    sentinel = target / 'sentinel'
    sentinel.write_bytes(b'unchanged')
    (locks / JOB[7:]).symlink_to(sentinel)
    with pytest.raises(OwnershipRefused):
        claim(tmp_path, JOB)
    assert sentinel.read_bytes() == b'unchanged'


def test_failed_enter_releases(tmp_path, monkeypatch):
    from slaif_raggedized_helper.embedding_job_ownership import Lease

    lease = claim(tmp_path, JOB)
    lease.assert_owned()
    with monkeypatch.context() as patch:
        def fail(_self):
            raise OwnershipRefused('failed')

        patch.setattr(Lease, 'assert_owned', fail)
        with pytest.raises(OwnershipRefused):
            with lease:
                pass
    with claim(tmp_path, JOB) as current:
        current.assert_owned()


def test_interrupted_close_closes_descriptors(tmp_path, monkeypatch):
    import fcntl

    lease = claim(tmp_path, JOB)
    lease.assert_owned()
    handles = (lease._fd, lease._dirfd, lease._rootfd)
    real = fcntl.flock

    def interrupt(fd, op):
        if op == fcntl.LOCK_UN:
            raise KeyboardInterrupt
        return real(fd, op)

    with monkeypatch.context() as patch:
        patch.setattr(fcntl, 'flock', interrupt)
        with pytest.raises(KeyboardInterrupt):
            lease.close()
    for fd in handles:
        with pytest.raises(OSError):
            os.fstat(fd)
    with claim(tmp_path, JOB) as current:
        current.assert_owned()
