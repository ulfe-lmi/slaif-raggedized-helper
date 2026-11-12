"""Model-free checks for the private owned GPU supervisor."""

import os

import pytest

from slaif_raggedized_helper import gpu_embedding_worker as parent
from slaif_raggedized_helper import gpu_worker_launch as launch
from slaif_raggedized_helper import gpu_worker_protocol as wire
from test_gpu_worker_launch import HOST, UUID, _prepared_fixture


def test_ready_snapshot_uses_actual_prepared_config(tmp_path, monkeypatch):
    args, reservation = _prepared_fixture(tmp_path, monkeypatch)
    prepared = None
    try:
        prepared = launch.prepare(**args)
        binding, vocab, policy = parent._expected_binding(prepared)
        start = wire.parse(prepared.startup)
        assert vocab == 20
        assert binding['startup_nonce'] == start['startup_nonce']
        assert binding['space'] == start['space']
        assert binding['definition'] == args['definition'].fingerprint()
        assert binding['device_uuid'] == UUID
        assert binding['device_key'] == parent_key(HOST, UUID)
        assert policy == args['wire_policy']
        (tmp_path / 'artifacts' / 'config.json').write_text('{}')
        with pytest.raises(parent.WorkerRefused):
            parent._expected_binding(prepared)
    finally:
        if prepared is not None:
            prepared.close()
        reservation.close()


def parent_key(host, device):
    from slaif_raggedized_helper.gpu_device_lease import _key
    return _key(host, device)


def test_pidfd_verification_rejects_current_namespace():
    assert parent._proc_identity(os.getpid())[1][0] == os.geteuid()
    class Owner:
        _candidate_pidfd = None
        _pidfd = None

        def _remember_fd(self, fd, *, pidfd=False):
            pass

    owner = Owner()
    try:
        with pytest.raises(parent.WorkerRefused):
            parent._verified_init(os.getpid(), os.getppid(),
                                  os.stat('/proc/self/ns/pid').st_ino, owner)
    finally:
        if owner._candidate_pidfd is not None:
            os.close(owner._candidate_pidfd)


def test_duplex_drains_stderr_while_writing():
    import subprocess
    import sys

    control_r, control_w = os.pipe()
    script = ("import os,sys; os.write(2,b'x'*60000); "
              "data=sys.stdin.buffer.readline(); "
              "os.write(1,b'{\"ok\":true}\\n')")
    process = subprocess.Popen([sys.executable, '-c', script], stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        pump = parent._Duplex(process.stdin.fileno(), process.stdout.fileno(),
                              process.stderr.fileno(), control_r,
                              wire.Policy(), launch.ResourcePolicy(2**30, 30, 120,
                                                                    8 * 1024**2, 65536), 5)
        assert pump.exchange(b'1' * 100000, 1024) == {'ok': True}
        assert pump.written == 100001
        assert pump.stderr_read == 60000
        assert process.wait(timeout=5) == 0
    finally:
        if process.returncode is None:
            process.kill()
            process.wait()
        for stream in (process.stdin, process.stdout, process.stderr):
            stream.close()
        os.close(control_r)
        os.close(control_w)


def test_exception_priority_preserves_interrupt():
    body = KeyboardInterrupt()
    cleanup = SystemExit()
    ordinary = ValueError()
    assert parent._select_error(body, cleanup) is body
    assert parent._select_error(ordinary, cleanup) is cleanup
    assert parent._select_error(ordinary, ValueError()) is ordinary


@pytest.mark.parametrize('raw', [b'{"child-pid":2}\n',
                                 b'{"child-pid":2,"child-pid":3}\n',
                                 b'x' * 4097 + b'\n'])
def test_control_rejects_missing_duplicate_and_oversize(raw):
    import time
    from types import SimpleNamespace

    control_r, control_w = os.pipe()
    stdout_r, stdout_w = os.pipe()
    stderr_r, stderr_w = os.pipe()
    stdout = os.fdopen(stdout_r, 'rb')
    stderr = os.fdopen(stderr_r, 'rb')
    try:
        os.write(control_w, raw)
        with pytest.raises((parent.WorkerRefused, ValueError)):
            parent._initial_status(SimpleNamespace(stdout=stdout, stderr=stderr),
                                   control_r, 65536, time.monotonic() + 2)
    finally:
        stdout.close()
        stderr.close()
        for fd in (control_r, control_w, stdout_w, stderr_w):
            os.close(fd)


@pytest.mark.parametrize('payload,cap', [
    (b'{ "ok":true}\n', 1024),
    (b'{"ok":true}\n{"extra":1}\n', 1024),
    (b'123456789\n', 8),
    (b'{"ok":', 1024),
])
def test_duplex_rejects_invalid_trailing_oversized_and_eof(payload, cap):
    import subprocess
    import sys

    control_r, control_w = os.pipe()
    script = ('import os,sys; sys.stdin.buffer.readline(); '
              f'os.write(1,{payload!r})')
    process = subprocess.Popen([sys.executable, '-c', script], stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        pump = parent._Duplex(process.stdin.fileno(), process.stdout.fileno(),
                              process.stderr.fileno(), control_r,
                              wire.Policy(), launch.ResourcePolicy(2**30, 30, 120,
                                                                    8 * 1024**2, 65536), 5)
        with pytest.raises((ValueError, parent.WorkerRefused)):
            pump.exchange(b'{}', cap)
        process.wait(timeout=5)
    finally:
        if process.returncode is None:
            process.kill()
            process.wait()
        for stream in (process.stdin, process.stdout, process.stderr):
            stream.close()
        os.close(control_r)
        os.close(control_w)


def test_reply_checks_replay_binding_cardinality_and_fp32():
    binding = {'schema': 1, 'space': 'a' * 64}
    reply = {**binding, 'nonce': 'b' * 32, 'digest': 'c' * 64, 'rows': [[0.5] * 1024]}
    rows = parent._check_reply(reply, binding, 'b' * 32, 'c' * 64, 1)
    reply['rows'][0][0] = 1.0
    assert rows[0][0] == 0.5
    for change in ({'nonce': 'd' * 32}, {'digest': 'd' * 64}, {'schema': True},
                   {'space': 'd' * 64}, {'rows': []}, {'rows': [[0.1] * 1024]},
                   {'extra': 1}):
        with pytest.raises(ValueError):
            parent._check_reply({**reply, **change}, binding, 'b' * 32, 'c' * 64, 1)


def test_descriptor_identity_prevents_foreign_close():
    worker = object.__new__(parent.GPUEmbeddingWorker)
    worker._fd_identities = {}
    worker._unknown_fd = False
    first_r, first_w = os.pipe()
    foreign_r, foreign_w = os.pipe()
    try:
        worker._control_r = first_r
        worker._remember_fd(first_r)
        os.close(first_r)
        os.dup2(foreign_r, first_r)
        with pytest.raises(parent.WorkerRefused):
            worker._close_fd('_control_r')
        assert worker._unknown_fd
        os.fstat(first_r)
    finally:
        for fd in (first_r, first_w, foreign_r, foreign_w):
            os.close(fd)


def test_duplex_timeout_and_preexposure_budget():
    import subprocess
    import sys
    import time

    control_r, control_w = os.pipe()
    process = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(5)'],
                               stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    try:
        policy = wire.Policy(io_seconds=1, total_input_bytes=2)
        resource = launch.ResourcePolicy(2**30, 30, 120, 8 * 1024**2, 65536)
        pump = parent._Duplex(process.stdin.fileno(), process.stdout.fileno(),
                              process.stderr.fileno(), control_r, policy, resource, 5)
        with pytest.raises(parent.WorkerRefused):
            pump.exchange(b'12', 10)
        assert pump.written == 0
        started = time.monotonic()
        with pytest.raises(parent.WorkerRefused):
            pump.exchange(b'1', 10)
        assert 0.8 <= time.monotonic() - started < 3
        assert pump.written == 2
    finally:
        process.kill()
        process.wait()
        for stream in (process.stdin, process.stdout, process.stderr):
            stream.close()
        os.close(control_r)
        os.close(control_w)


@pytest.mark.parametrize('body_interrupt', [False, True])
def test_constructor_failure_retains_owner_and_selects_interrupt(tmp_path, monkeypatch,
                                                                 body_interrupt):
    args, reservation = _prepared_fixture(tmp_path, monkeypatch)
    prepared = launch.prepare(**args)
    key = id(prepared._owner)

    class FrozenInterrupt(BaseException):
        def __setattr__(self, name, value):
            raise RuntimeError('immutable')

    original_body = FrozenInterrupt() if body_interrupt else ValueError()
    cleanup = FrozenInterrupt()

    def fail_binding(_):
        raise original_body

    def fail_close():
        raise cleanup

    monkeypatch.setattr(parent, '_expected_binding', fail_binding)
    monkeypatch.setattr(prepared, 'close', fail_close)
    try:
        with pytest.raises(FrozenInterrupt) as caught:
            parent.GPUEmbeddingWorker(prepared)
        assert caught.value is (original_body if body_interrupt else cleanup)
        owner = parent._retained[key]
        assert owner._prepared is prepared and owner._state == 'pending'
        snapshot = dict(owner.__dict__)
        record = parent._records[id(owner)]
        with pytest.raises(parent.WorkerRefused):
            parent.GPUEmbeddingWorker.__init__(owner, prepared)
        assert owner.__dict__ == snapshot
        assert parent._records[id(owner)] is record
        assert parent._retained[key] is owner
        monkeypatch.undo()
        owner.close()
        assert key not in parent._retained
        reservation.assert_owned()
    finally:
        reservation.close()


def test_bounded_copy_rejects_oversized_rows_and_detaches_input():
    source = [[1, 2], [3, 4]]
    copied = parent._copy_rows(source, 10, 2)
    source[0][0] = 9
    assert copied == [[1, 2], [3, 4]]
    for rows in ([[1] * 1025], [[1, 2]] * 3, [[True, 2]], [(1, 2)]):
        with pytest.raises(ValueError):
            parent._copy_rows(rows, 10, 2)


def test_duplex_partial_response_and_stderr_overflow():
    import subprocess
    import sys

    control_r, control_w = os.pipe()
    script = ("import os,sys,time; sys.stdin.buffer.readline(); "
              "os.write(2,b'x'*65); os.write(1,b'{\"ok\":'); "
              "time.sleep(0.05); os.write(1,b'true}\\n')")
    process = subprocess.Popen([sys.executable, '-c', script], stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        policy = wire.Policy(io_seconds=2)
        resource = launch.ResourcePolicy(2**30, 30, 120, 1024, 64)
        pump = parent._Duplex(process.stdin.fileno(), process.stdout.fileno(),
                              process.stderr.fileno(), control_r, policy, resource, 5)
        with pytest.raises(parent.WorkerRefused):
            pump.exchange(b'{}', 100)
        assert pump.stderr_read == 65
    finally:
        if process.poll() is None:
            process.kill()
        process.wait()
        for stream in (process.stdin, process.stdout, process.stderr):
            stream.close()
        os.close(control_r)
        os.close(control_w)


def test_duplex_reassembles_partial_response():
    import subprocess
    import sys

    control_r, control_w = os.pipe()
    script = ("import os,sys,time; sys.stdin.buffer.readline(); "
              "os.write(1,b'{\"ok\":'); time.sleep(0.05); "
              "os.write(1,b'true}\\n'); time.sleep(0.2)")
    process = subprocess.Popen([sys.executable, '-c', script], stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        policy = wire.Policy(io_seconds=2)
        resource = launch.ResourcePolicy(2**30, 30, 120, 1024, 64)
        pump = parent._Duplex(process.stdin.fileno(), process.stdout.fileno(),
                              process.stderr.fileno(), control_r, policy, resource, 5)
        assert pump.exchange(b'{}', 100) == {'ok': True}
        assert pump.read == len(b'{"ok":true}\n')
    finally:
        if process.poll() is None:
            process.kill()
        process.wait()
        for stream in (process.stdin, process.stdout, process.stderr):
            stream.close()
        os.close(control_r)
        os.close(control_w)


def test_initial_status_preserves_exit_frame_and_counts_stderr():
    import time
    from types import SimpleNamespace

    control_r, control_w = os.pipe()
    stdout_r, stdout_w = os.pipe()
    stderr_r, stderr_w = os.pipe()
    stdout = os.fdopen(stdout_r, 'rb')
    stderr = os.fdopen(stderr_r, 'rb')
    status = (b'{"child-pid":42,"ipc-namespace":101,"mnt-namespace":102,'
              b'"net-namespace":103,"pid-namespace":104,"uts-namespace":105}\n')
    try:
        os.write(control_w, status + b'{"exit-code":137}\n')
        os.write(stderr_w, b'warning')
        pid, namespace, count = parent._initial_status(
            SimpleNamespace(stdout=stdout, stderr=stderr), control_r, 64, time.monotonic() + 2)
        assert (pid, namespace, count) == (42, 104, 7)
        assert os.read(control_r, 100) == b'{"exit-code":137}\n'
    finally:
        stdout.close()
        stderr.close()
        for fd in (control_r, control_w, stdout_w, stderr_w):
            os.close(fd)


def test_popen_failure_before_child_remains_owned_until_reconciled(tmp_path, monkeypatch):
    import subprocess

    args, reservation = _prepared_fixture(tmp_path, monkeypatch)
    prepared = launch.prepare(**args)
    key = id(prepared._owner)
    captured = []

    def fail(process, *args, **kwargs):
        captured.append(process)
        raise OSError('private fault detail')

    monkeypatch.setattr(subprocess.Popen, '__init__', fail)
    try:
        with pytest.raises(parent.WorkerRefused, match='^worker refused$'):
            parent.GPUEmbeddingWorker(prepared)
        owner = parent._retained[key]
        assert owner._process is captured[0]
        assert parent._records[id(owner)][5] is captured[0]
        assert owner._state == 'pending' and not prepared._closed
        assert not hasattr(captured[0], 'pid')
        reservation.assert_owned()
        # The test stub proves no launch happened; production does not assume this.
        owner._close_fd('_control_w')
        owner._close_fd('_control_r')
        prepared.close()
        assert parent._records[id(owner)][5] is captured[0]
        assert parent._retained[key] is owner
        del parent._records[id(owner)]
        del parent._retained[key]
    finally:
        reservation.close()


def test_status_partial_timeout_can_resume_without_losing_accounting():
    import time
    from types import SimpleNamespace

    control_r, control_w = os.pipe()
    stdout_r, stdout_w = os.pipe()
    stderr_r, stderr_w = os.pipe()
    stdout = os.fdopen(stdout_r, 'rb')
    stderr = os.fdopen(stderr_r, 'rb')
    process = SimpleNamespace(stdout=stdout, stderr=stderr)
    state = [bytearray(), 0]
    try:
        os.write(control_w, b'{"child-pid":42,')
        os.write(stderr_w, b'abc')
        with pytest.raises(parent.WorkerRefused):
            parent._initial_status(process, control_r, 16, time.monotonic() + 0.05, state)
        assert bytes(state[0]) == b'{"child-pid":42,'
        assert state[1] == 3
        os.write(control_w, b'"ipc-namespace":101,"mnt-namespace":102,'
                            b'"net-namespace":103,"pid-namespace":104,"uts-namespace":105}\n')
        assert parent._initial_status(process, control_r, 16, time.monotonic() + 1, state) == (
            42, 104, 3)
    finally:
        stdout.close()
        stderr.close()
        for fd in (control_r, control_w, stdout_w, stderr_w):
            os.close(fd)


def test_actual_reaped_wrapper_refuses_numeric_targets_with_causal_control(monkeypatch):
    import subprocess
    import sys

    process = subprocess.Popen([sys.executable, '-I', '-S', '-c', 'pass'],
                               stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, start_new_session=True)
    wrapper_fd = os.pidfd_open(process.pid, 0)
    assert process.wait(timeout=5) == 0
    owner = object.__new__(parent.GPUEmbeddingWorker)
    owner._process = process
    owner._wrapper_fd = None
    owner._fd_identities = {}
    owner._unknown_fd = False
    parent._records[id(owner)] = [owner, None, None, os.getpid(), None, process,
                                   {'_wrapper_fd': None}, None, owner._fd_identities]
    lookups = []

    class StopLookup(Exception):
        pass

    def spy(pid, flags=0):
        lookups.append(pid)
        raise StopLookup()

    try:
        with monkeypatch.context() as patch:
            patch.setattr(os, 'pidfd_open', spy)
            with pytest.raises(parent.WorkerRefused):
                owner._reconcile_process()
            assert lookups == []
            # Only the known-reaped guard is bypassed; the spy prevents an OS lookup.
            patch.setattr(parent, '_require_unreaped', lambda process: None)
            with pytest.raises(StopLookup):
                owner._reconcile_process()
            assert lookups == [process.pid]
        owner._wrapper_fd = wrapper_fd
        owner._remember_fd(wrapper_fd, pidfd=True)
        calls = []
        with monkeypatch.context() as patch:
            patch.setattr(os, 'getpgid', lambda pid: calls.append(pid))
            with pytest.raises(parent.WorkerRefused):
                owner._stop_unverified_wrapper()
        assert calls == []
    finally:
        del parent._records[id(owner)]
        os.close(wrapper_fd)
        for stream in (process.stdin, process.stdout, process.stderr):
            stream.close()
