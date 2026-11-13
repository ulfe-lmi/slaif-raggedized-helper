"""Real model-free parent ownership and identity composition."""

import hashlib
import inspect
import os
from pathlib import Path
import subprocess
import threading

import pytest

from slaif_raggedized_helper import gpu_embedding_worker as parent
from slaif_raggedized_helper import gpu_worker_identity as identity
from slaif_raggedized_helper import gpu_worker_launch as launch
from slaif_raggedized_helper import gpu_worker_protocol as wire
from test_gpu_worker_launch import _prepared_fixture


def test_actual_parent_identity_and_owned_guards(tmp_path, monkeypatch):
    args, reservation = _prepared_fixture(tmp_path, monkeypatch)
    args['wire_policy'] = wire.Policy(calls=3)
    prepared = launch.prepare(**args)
    predicted = identity.predict(prepared)
    worker_fd = prepared._descriptors['worker']
    script = (Path(prepared._owner.directory) / 'worker.py').read_text()
    marker = 'if __name__ == "__main__":\n    sys.exit(main())'
    injection = '''
class FakeBackend:
    def __init__(self, manifest, root, definition, tokenizer, inventory, lease, uuid):
        self.space = embedding_space.admit(manifest, root, definition, tokenizer, inventory)
        self._vocab = 20
    def forward_cls(self, rows):
        return [[float(row[0])] * 1024 for row in rows]
    def close(self):
        pass
gpu_embedding_backend.GPUEmbeddingBackend = FakeBackend
'''
    assert script.count(marker) == 1
    harness = script.replace(marker, injection + '\n' + marker).encode()
    path = tmp_path / 'harness.py'
    path.write_bytes(harness)
    path.chmod(0o400)
    fake_fd = os.open(path, os.O_RDONLY | os.O_CLOEXEC)
    original = subprocess.Popen.__init__

    def intercept(process, argv, **kwargs):
        argv = list(argv)
        index = argv.index('/worker.py')
        assert argv[index - 1] == f'/proc/self/fd/{worker_fd}'
        argv[index - 1] = f'/proc/self/fd/{fake_fd}'
        kwargs['pass_fds'] = tuple(fake_fd if fd == worker_fd else fd
                                   for fd in kwargs['pass_fds'])
        return original(process, argv, **kwargs)

    worker = None
    print('harness_sha256=' + hashlib.sha256(harness).hexdigest())
    try:
        monkeypatch.setattr(subprocess.Popen, '__init__', intercept)
        worker = parent.GPUEmbeddingWorker(prepared)
        observed = identity.observe(worker)
        assert (observed.record_bytes, observed.fingerprint) == (predicted.record_bytes,
                                                                  predicted.fingerprint)
        assert observed.ready_binding_bytes == parent._records[id(worker)][9][1]
        first = worker.forward_cls([[2, 3]])
        second = worker.forward_cls([[4, 5]])
        assert first.rows[0][0] == 2.0 and second.rows[0][0] == 4.0
        assert identity.observe(worker) == observed
        lock = worker._owned_lock()
        assert lock.acquire(blocking=False)
        try:
            with pytest.raises(identity.IdentityRefused):
                identity.observe(worker)
        finally:
            lock.release()
        actual_lock = worker._lock
        worker._lock = threading.Lock()
        try:
            with pytest.raises(identity.IdentityRefused):
                identity.observe(worker)
        finally:
            worker._lock = actual_lock
        assert identity.observe(worker) == observed
        worker._state = 'pending'
        try:
            with pytest.raises(identity.IdentityRefused):
                identity.observe(worker)
        finally:
            worker._state = 'live'
        worker._busy = True
        try:
            with pytest.raises(identity.IdentityRefused):
                identity.observe(worker)
        finally:
            worker._busy = False
        # Causal control: suppress only the actual-vocab comparison in a temporary
        # in-memory copy; the same real owner must then falsely pass this boundary.
        original_boundary = identity._live_boundary
        source = inspect.getsource(original_boundary)
        predicate = 'worker._vocab != vocab or '
        assert source.count(predicate) == 1
        namespace = dict(identity.__dict__)
        exec(compile(source.replace(predicate, ''), '<private-causal-control>', 'exec'), namespace)
        worker._vocab = 21
        try:
            with pytest.raises(identity.IdentityRefused):
                identity.observe(worker)
            monkeypatch.setattr(identity, '_live_boundary', namespace['_live_boundary'])
            assert identity.observe(worker) == observed
        finally:
            monkeypatch.setattr(identity, '_live_boundary', original_boundary)
            worker._vocab = 20
        assert identity.observe(worker) == observed

        class Stop(BaseException):
            pass

        stop = Stop()
        def interrupt(*unused):
            raise stop
        monkeypatch.setattr(identity, '_live_boundary', interrupt)
        try:
            with pytest.raises(Stop) as caught:
                identity.observe(worker)
            assert caught.value is stop
        finally:
            monkeypatch.setattr(identity, '_live_boundary', original_boundary)
        assert identity.observe(worker) == observed
        snapshot = parent._records[id(worker)][9]
        try:
            parent._records[id(worker)][9] = (snapshot[0], b'{}', *snapshot[2:])
            with pytest.raises(identity.IdentityRefused):
                identity.observe(worker)
        finally:
            parent._records[id(worker)][9] = snapshot
        original_process = worker._process
        worker._process = object()
        try:
            with pytest.raises(identity.IdentityRefused):
                identity.observe(worker)
        finally:
            worker._process = original_process
        read_fd, write_fd = os.pipe()
        child = os.fork()
        if child == 0:
            os.close(read_fd)
            try:
                identity.observe(worker)
            except identity.IdentityRefused:
                os.write(write_fd, b'R')
            os._exit(0)
        os.close(write_fd)
        assert os.read(read_fd, 1) == b'R'
        os.close(read_fd)
        assert os.waitpid(child, 0)[1] == 0
        assert identity.observe(worker) == observed
        config = Path(args['artifact_root']) / 'config.json'
        original_config = config.read_bytes()
        try:
            config.write_bytes(original_config + b' ')
            with pytest.raises(identity.IdentityRefused):
                identity.observe(worker)
        finally:
            config.write_bytes(original_config)
        assert identity.observe(worker) == observed
        worker.close()
        with pytest.raises(identity.IdentityRefused):
            identity.observe(worker)
        reservation.assert_owned()
    finally:
        if worker is not None:
            worker.close()
        os.close(fake_fd)
        prepared.close()
        reservation.assert_owned()
        reservation.close()
