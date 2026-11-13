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


def test_acquisition_cleanup_attempts_all_and_retains_uncertainty(tmp_path, monkeypatch):
    from slaif_raggedized_helper import embedding_job_ownership as m

    with claim(tmp_path, JOB) as positive:
        positive.assert_owned()
    sentinel = os.open(tmp_path / 'sentinel', os.O_CREAT | os.O_RDWR, 0o600)
    real_close = os.close
    calls = []
    def fail_one(fd):
        calls.append(fd)
        real_close(fd)
        if len(calls) == 1:
            raise OSError('private')
    def fail_token(_n):
        raise KeyboardInterrupt('original')
    try:
        with monkeypatch.context() as patch:
            patch.setattr(m.secrets, 'token_hex', fail_token)
            patch.setattr(m.os, 'close', fail_one)
            with pytest.raises(KeyboardInterrupt, match='original') as caught:
                claim(tmp_path, JOB)
        owner = caught.value.cleanup_owner
        assert owner.pending and len(calls) == 3 and len(set(calls)) == 3
        assert sentinel not in calls
        os.fstat(sentinel)
        assert [a[2] for a in owner.attempts] == ['unknown', 'done', 'done']
        with claim(tmp_path, JOB) as positive:
            positive.assert_owned()
    finally:
        real_close(sentinel)


def test_new_cleanup_interrupt_has_priority_and_is_sticky(tmp_path, monkeypatch):
    from slaif_raggedized_helper import embedding_job_ownership as m

    lease = claim(tmp_path, JOB)
    handles = (lease._fd, lease._dirfd, lease._rootfd)
    real_close = os.close
    calls = []
    def interrupt(fd):
        calls.append(fd)
        real_close(fd)
        if len(calls) == 1:
            raise KeyboardInterrupt('cleanup interrupt')
    with monkeypatch.context() as patch:
        patch.setattr(m.os, 'close', interrupt)
        with pytest.raises(KeyboardInterrupt, match='cleanup interrupt') as caught:
            lease.close()
    assert set(calls) == set(handles)
    assert caught.value.cleanup_owner is lease.cleanup_owner
    with pytest.raises(OwnershipRefused) as pending:
        lease.close()
    assert pending.value.cleanup_owner is lease.cleanup_owner


def test_acquisition_new_cleanup_interrupt_beats_ordinary(tmp_path, monkeypatch):
    from slaif_raggedized_helper import embedding_job_ownership as m

    with claim(tmp_path, JOB):
        pass
    real_close = os.close
    calls = []
    def interrupt(fd):
        calls.append(fd)
        real_close(fd)
        if len(calls) == 1:
            raise KeyboardInterrupt('new interrupt')
    def fail(_n):
        raise OSError('private acquisition failure')
    with monkeypatch.context() as patch:
        patch.setattr(m.secrets, 'token_hex', fail)
        patch.setattr(m.os, 'close', interrupt)
        with pytest.raises(KeyboardInterrupt, match='new interrupt') as caught:
            claim(tmp_path, JOB)
    assert len(calls) == 3
    assert caught.value.cleanup_owner.pending
    with claim(tmp_path, JOB):
        pass


def test_acquisition_close_fails_before_close_retains_exact_owned_fd(tmp_path, monkeypatch):
    from slaif_raggedized_helper import embedding_job_ownership as m

    with claim(tmp_path, JOB) as positive:
        positive.assert_owned()
    sentinel = os.open(tmp_path / 'sentinel', os.O_CREAT | os.O_RDWR, 0o600)
    real_close = os.close
    calls = []
    retained = []
    def fail_before_close(fd):
        calls.append(fd)
        if len(calls) == 1:
            st = os.fstat(fd)
            retained.append((fd, st.st_dev, st.st_ino))
            raise OSError('before close')
        real_close(fd)
    def interrupt(_n):
        raise KeyboardInterrupt('original interrupt')
    try:
        with monkeypatch.context() as patch:
            patch.setattr(m.os, 'close', fail_before_close)
            patch.setattr(m.secrets, 'token_hex', interrupt)
            with pytest.raises(KeyboardInterrupt, match='original interrupt') as caught:
                claim(tmp_path, JOB)
        owner = caught.value.cleanup_owner
        assert owner.pending
        assert len(calls) == 3 and len(set(calls)) == 3 and sentinel not in calls
        assert [item[2] for item in owner.attempts] == ['unknown', 'done', 'done']
        fd, dev, ino = retained[0]
        st = os.fstat(fd)
        assert (st.st_dev, st.st_ino) == (dev, ino)
        os.fstat(sentinel)
        # No cleanup retry is made by inspection or by the retained owner.
        assert len(calls) == 3
    finally:
        if retained:
            fd, dev, ino = retained[0]
            try:
                st = os.fstat(fd)
                if (st.st_dev, st.st_ino) == (dev, ino):
                    real_close(fd)
            except OSError:
                pass
        real_close(sentinel)
