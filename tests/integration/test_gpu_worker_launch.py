"""Private model-free sandbox witness; this test owns every child process."""

import hashlib
import importlib.util
import os
from pathlib import Path
import select
import signal
import subprocess
import time

import pytest

from slaif_raggedized_helper import gpu_device_lease, gpu_worker_launch as launch
from slaif_raggedized_helper import gpu_worker_protocol as wire
_spec = importlib.util.spec_from_file_location(
    "gpu_launch_unit_fixture",
    Path(__file__).resolve().parents[1] / "unit/test_gpu_worker_launch.py",
)
_fixture = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_fixture)
HOST, UUID, _prepared_fixture = _fixture.HOST, _fixture.UUID, _fixture._prepared_fixture


def _frame(stream):
    data = bytearray()
    end = time.monotonic() + 25
    while True:
        remaining = end - time.monotonic()
        assert remaining > 0 and select.select([stream], [], [], remaining)[0]
        byte = os.read(stream.fileno(), 1)
        assert byte and len(data) < 1024 * 1024
        if byte == b'\n':
            return wire.parse(bytes(data))
        data.extend(byte)


def test_real_child_namespace_lease_and_protocol(tmp_path, monkeypatch):
    args, reservation = _prepared_fixture(tmp_path, monkeypatch)
    args["wire_policy"] = wire.Policy(calls=3)
    prepared = None
    child = None
    try:
        prepared = launch.prepare(**args)
        argv, fds = prepared.launch_arguments()
        artifacts = Path(args['artifact_root'])
        artifacts.rename(tmp_path / 'original-artifacts')
        artifacts.mkdir(mode=0o700)
        capsule = Path(prepared._owner.directory)
        assert sum(p.stat().st_size for p in capsule.rglob('*') if p.is_file()) < 64 * 1024**2
        worker = capsule / 'worker.py'
        script = worker.read_text()
        marker = 'if __name__ == "__main__":\n    sys.exit(main())'
        assert script.count(marker) == 1
        fake = """
# Private test-only injection into the copied entry, not a production test mode.
assert not os.path.exists('/home')
assert not os.path.exists('/sys')
assert not os.path.exists('/proc/HOST_PROCESS')
assert os.stat('/dev/nvidia0').st_rdev == os.makedev(1, 3)
assert os.stat('/dev/nvidiactl').st_rdev == os.makedev(1, 3)
assert os.stat('/proc/self/ns/net').st_ino != HOST_NET
assert os.stat('/proc/self/ns/pid').st_ino != HOST_PID
class FakeBackend:
    def __init__(self, manifest, root, definition, tokenizer, inventory, lease, uuid):
        self.space = embedding_space.admit(manifest, root, definition, tokenizer, inventory)
        self._vocab = 20
    def forward_cls(self, rows):
        return [[float(row[0])] * 1024 for row in rows]
    def close(self):
        pass
gpu_embedding_backend.GPUEmbeddingBackend = FakeBackend
""".replace('HOST_NET', str(os.stat('/proc/self/ns/net').st_ino)).replace(
            'HOST_PID', str(os.stat('/proc/self/ns/pid').st_ino)).replace(
            'HOST_PROCESS', str(os.getpid()))
        worker.chmod(0o600)
        witness = script.replace(marker, fake + '\n' + marker)
        worker.write_text(witness)
        print('witness_sha256=' + hashlib.sha256(witness.encode()).hexdigest(),
              'plan_id=' + prepared.plan_id, 'code_id=' + prepared.code_id,
              'profile_id=' + prepared.profile_id)
        child = subprocess.Popen(argv, pass_fds=fds, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, start_new_session=True)
        assert child.stdin is not None and child.stdout is not None
        child.stdin.write(prepared.startup + b'\n')
        child.stdin.flush()
        ready = _frame(child.stdout)
        assert ready['ready'] is True and ready['code_id'] == prepared.code_id
        with pytest.raises(gpu_device_lease.DeviceLeaseRefused):
            gpu_device_lease.acquire(args['lease_root'], HOST, UUID)
        for index, rows in enumerate(([[2, 3]], [[4, 5]]), 1):
            request = {'nonce': str(index) * 32, 'rows': rows,
                       'digest': hashlib.sha256(wire.encode(rows)).hexdigest()}
            child.stdin.write(wire.encode(request) + b'\n')
            child.stdin.flush()
            reply = _frame(child.stdout)
            assert reply['nonce'] == request['nonce'] and reply['digest'] == request['digest']
            assert reply['rows'] == [[float(rows[0][0])] * 1024]
        assert child.poll() is None
        os.killpg(child.pid, signal.SIGTERM)
        child.wait(timeout=10)
        deadline = time.monotonic() + 5
        while True:
            try:
                fresh = gpu_device_lease.acquire(args['lease_root'], HOST, UUID)
                break
            except gpu_device_lease.DeviceLeaseRefused:
                if time.monotonic() >= deadline:
                    raise
                time.sleep(0.02)
        fresh.assert_owned()
        fresh.close()
    finally:
        if child is not None:
            if child.poll() is None:
                os.killpg(child.pid, signal.SIGKILL)
                child.wait(timeout=5)
            for stream in (child.stdin, child.stdout, child.stderr):
                if stream is not None and not stream.closed:
                    stream.close()
        if prepared is not None:
            prepared.close()
        reservation.close()
