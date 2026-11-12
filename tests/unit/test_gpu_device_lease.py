import hashlib
import json
import os
import tracemalloc

import pytest

from slaif_raggedized_helper import gpu_device_lease as gpu

HOST = 'a' * 64
DEVICE = 'GPU-12345678-1234-1234-1234-123456789abc'


def test_key_and_real_owner(tmp_path):
    root = str(tmp_path)
    payload = {'kind': 'gpu-device-lease-v1', 'host_id': HOST, 'device_uuid': DEVICE}
    body = json.dumps(payload, sort_keys=True, separators=(',', ':'), ensure_ascii=True)
    expected = 'sha256:' + hashlib.sha256(('slaif-fingerprint-v1\n' + body).encode()).hexdigest()
    with gpu.acquire(root, HOST, DEVICE) as lease:
        assert lease.key == expected
        assert len(lease.owner_id) == 32
        assert lease.owner_pid == os.getpid()
        lease.assert_owned()
    lease.close()
    with pytest.raises(gpu.DeviceLeaseRefused):
        lease.assert_owned()


@pytest.mark.parametrize('root,host,device', [
    ('/' + 'a' * 1_000_000, HOST, DEVICE), ('/tmp/../bad', HOST, DEVICE),
    ('relative', HOST, DEVICE), ('/tmp', True, DEVICE), ('/tmp', HOST, 'bad'),
    ('/tmp\x00bad', HOST, DEVICE),
])
def test_preflight_without_io(monkeypatch, root, host, device):
    calls = []
    def forbidden(*args):
        calls.append(args)
        raise AssertionError('unexpected claim')
    monkeypatch.setattr(gpu.ownership, 'claim', forbidden)
    with pytest.raises(gpu.DeviceLeaseRefused):
        gpu.acquire(root, host, device)
    assert calls == []


def test_mutation_and_forgery(tmp_path):
    lease = gpu.acquire(str(tmp_path), HOST, DEVICE)
    lease._host_id = 'b' * 64
    with pytest.raises(gpu.DeviceLeaseRefused):
        lease.assert_owned()
    lease.close()
    with pytest.raises(gpu.DeviceLeaseRefused):
        object.__new__(gpu.DeviceLease).assert_owned()


def test_cleanup_failure_is_sticky(tmp_path, monkeypatch):
    lease = gpu.acquire(str(tmp_path), HOST, DEVICE)
    owner = lease._owner
    original = type(owner).close
    calls = []
    def fail(self):
        calls.append(self)
        original(self)
        raise OSError('cleanup uncertain')
    monkeypatch.setattr(type(owner), 'close', fail)
    with pytest.raises(gpu.DeviceLeaseRefused):
        lease.close()
    with pytest.raises(gpu.DeviceLeaseRefused):
        lease.close()
    assert calls == [owner]
    assert gpu._live[id(lease)][5] is owner


def test_inode_replacement_refused(tmp_path):
    lease = gpu.acquire(str(tmp_path), HOST, DEVICE)
    path = tmp_path / 'embedding_job_locks' / lease.key[7:]
    path.rename(path.with_suffix('.old'))
    path.touch(mode=0o600)
    with pytest.raises(gpu.DeviceLeaseRefused):
        lease.assert_owned()
    lease.close()
    assert path.exists()


def test_body_exception_survives_cleanup_failure(tmp_path, monkeypatch):
    lease = gpu.acquire(str(tmp_path), HOST, DEVICE)
    original = type(lease._owner).close
    def fail(owner):
        original(owner)
        raise OSError('cleanup')
    monkeypatch.setattr(type(lease._owner), 'close', fail)
    with pytest.raises(RuntimeError, match='body') as caught:
        with lease:
            raise RuntimeError('body')
    assert 'pending or unknown' in caught.value.__notes__[0]


def test_interrupt_preserved_during_entry_cleanup(tmp_path, monkeypatch):
    lease = gpu.acquire(str(tmp_path), HOST, DEVICE)
    original = type(lease._owner).close
    def interrupt(self):
        raise KeyboardInterrupt('entry')
    def fail(owner):
        original(owner)
        raise OSError('cleanup')
    monkeypatch.setattr(gpu.DeviceLease, 'assert_owned', interrupt)
    monkeypatch.setattr(type(lease._owner), 'close', fail)
    with pytest.raises(KeyboardInterrupt, match='entry') as caught:
        lease.__enter__()
    assert 'pending or unknown' in caught.value.__notes__[0]


def test_registration_failure_closes_owner(tmp_path, monkeypatch):
    class BrokenRegistry(dict):
        def __setitem__(self, key, value):
            raise RuntimeError('registration sentinel')
    monkeypatch.setattr(gpu, '_live', BrokenRegistry())
    with pytest.raises(RuntimeError, match='registration sentinel'):
        gpu.acquire(str(tmp_path), HOST, DEVICE)
    # The actual kernel lock was released by cleanup.
    monkeypatch.setattr(gpu, '_live', {})
    gpu.acquire(str(tmp_path), HOST, DEVICE).close()


def test_large_preallocated_path_has_bounded_admission_memory(monkeypatch):
    path = '/' + 'a' * 1_000_000
    calls = []
    def forbidden(*args):
        calls.append(args)
        raise AssertionError('unexpected claim')
    monkeypatch.setattr(gpu.ownership, 'claim', forbidden)
    tracemalloc.start()
    try:
        with pytest.raises(gpu.DeviceLeaseRefused):
            gpu.acquire(path, HOST, DEVICE)
        _, peak = tracemalloc.get_traced_memory()
        assert peak < 100_000
    finally:
        tracemalloc.stop()
    assert calls == []


def test_pending_same_key_refused_other_device_and_closed_collects(tmp_path, monkeypatch):
    import gc
    import weakref

    lease = gpu.acquire(str(tmp_path), HOST, DEVICE)
    ref = weakref.ref(lease)
    lease.close()
    lease.close()
    del lease
    gc.collect()
    assert ref() is None
    lease = gpu.acquire(str(tmp_path), HOST, DEVICE)
    original = type(lease._owner).close
    def fail(owner):
        original(owner)
        raise OSError('private')
    with monkeypatch.context() as patch:
        patch.setattr(type(lease._owner), 'close', fail)
        with pytest.raises(gpu.DeviceLeaseRefused) as failure:
            lease.close()
    assert failure.value.cleanup_owner is lease.cleanup_owner
    with pytest.raises(gpu.DeviceLeaseRefused) as pending:
        gpu.acquire(str(tmp_path), HOST, DEVICE)
    assert pending.value.cleanup_owner is lease.cleanup_owner
    other = 'GPU-12345678-1234-1234-1234-123456789abd'
    gpu.acquire(str(tmp_path), HOST, other).close()


def test_acquisition_pending_exposed_and_refused(tmp_path, monkeypatch):
    real_close = os.close
    calls = []
    def fail(fd):
        calls.append(fd)
        real_close(fd)
        if len(calls) == 1:
            raise OSError('private')
    def interrupt(_n):
        raise KeyboardInterrupt('acquisition')
    with monkeypatch.context() as patch:
        patch.setattr(gpu.ownership.os, 'close', fail)
        patch.setattr(gpu.ownership.secrets, 'token_hex', interrupt)
        with pytest.raises(KeyboardInterrupt, match='acquisition') as caught:
            gpu.acquire(str(tmp_path), HOST, DEVICE)
    assert caught.value.cleanup_owner.pending
    with pytest.raises(gpu.DeviceLeaseRefused) as pending:
        gpu.acquire(str(tmp_path), HOST, DEVICE)
    assert pending.value.cleanup_owner is caught.value.cleanup_owner
    assert len(calls) == 3


def test_contention_is_public_refusal(tmp_path):
    with gpu.acquire(str(tmp_path), HOST, DEVICE):
        with pytest.raises(gpu.DeviceLeaseRefused):
            gpu.acquire(str(tmp_path), HOST, DEVICE)


def test_preflight_spy_positive_actual_claim(tmp_path, monkeypatch):
    actual = gpu.ownership.claim
    calls = []
    def observed(*args):
        calls.append(args)
        return actual(*args)
    monkeypatch.setattr(gpu.ownership, 'claim', observed)
    with gpu.acquire(str(tmp_path), HOST, DEVICE) as lease:
        lease.assert_owned()
    assert len(calls) == 1
    assert calls[0][0] == str(tmp_path)


def test_preflight_bypass_is_detected(monkeypatch):
    with monkeypatch.context() as patch:
        patch.setattr(gpu, '_validate', lambda *args: None)
        with pytest.raises(AssertionError):
            test_preflight_without_io(patch, 'relative', HOST, DEVICE)
