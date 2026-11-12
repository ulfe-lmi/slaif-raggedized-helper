import os
import subprocess
import resource
import sys
import time

from slaif_raggedized_helper import gpu_device_lease as gpu

HOST = 'a' * 64
DEVICE = 'GPU-12345678-1234-1234-1234-123456789abc'
OTHER = 'GPU-12345678-1234-1234-1234-123456789abd'
SCRIPT = '''
import sys
import time
from slaif_raggedized_helper.gpu_device_lease import acquire
try:
    lease = acquire(sys.argv[1], sys.argv[2], sys.argv[3])
except ValueError:
    sys.exit(7)
lease.assert_owned()
lease.close()
'''


def limits():
    resource.setrlimit(resource.RLIMIT_CPU, (3, 3))
    resource.setrlimit(resource.RLIMIT_AS, (1024**3, 1024**3))


def test_process_contention_and_release(tmp_path):
    def child(root, device):
        return subprocess.run([sys.executable, '-c', SCRIPT, root, HOST, device],
                              timeout=5, check=False, env=os.environ.copy(),
                              preexec_fn=limits).returncode
    root = str(tmp_path)
    second = tmp_path / 'other'
    second.mkdir(mode=0o700)
    with gpu.acquire(root, HOST, DEVICE):
        assert child(root, DEVICE) == 7
        assert child(root, OTHER) == 0
        assert child(str(second), DEVICE) == 0
    assert child(root, DEVICE) == 0


def test_forked_child_cannot_assert_or_close(tmp_path):
    lease = gpu.acquire(str(tmp_path), HOST, DEVICE)
    pid = os.fork()
    if pid == 0:
        try:
            limits()
            for operation in (lease.assert_owned, lease.close):
                try:
                    operation()
                except gpu.DeviceLeaseRefused:
                    continue
                os._exit(1)
            os._exit(0)
        except BaseException:
            os._exit(2)
    def token():
        try:
            with open(f'/proc/{pid}/stat') as handle:
                return handle.read().rsplit(')', 1)[1].split()[19]
        except (OSError, IndexError):
            return None

    identity = token()
    reaped = False
    try:
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            found, status = os.waitpid(pid, os.WNOHANG)
            if found:
                reaped = True
                break
            time.sleep(0.01)
        assert reaped, 'owned child exceeded deadline'
        assert os.waitstatus_to_exitcode(status) == 0
        lease.assert_owned()
    finally:
        if not reaped:
            if identity is not None and token() == identity:
                os.kill(pid, 9)
            deadline = time.monotonic() + 1
            while time.monotonic() < deadline:
                found, _ = os.waitpid(pid, os.WNOHANG)
                if found:
                    reaped = True
                    break
                time.sleep(0.01)
            if not reaped:
                import warnings
                warnings.warn('owned child reap remains pending', RuntimeWarning)
        lease.close()
