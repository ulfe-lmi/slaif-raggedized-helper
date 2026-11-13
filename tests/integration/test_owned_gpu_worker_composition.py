"""Actual model-free parent/namespace/protocol composition."""

import hashlib
import os
from pathlib import Path
import subprocess

import pytest

from slaif_raggedized_helper import gpu_device_lease
from slaif_raggedized_helper import gpu_embedding_worker as parent
from slaif_raggedized_helper import gpu_worker_launch as launch
from test_gpu_worker_launch import _prepared_fixture


@pytest.mark.parametrize('end_mode', ['close', 'single', 'single_nofork', 'invalid', 'module',
                                     'binding', 'body_interrupt', 'cleanup_interrupt',
                                     'lock_overlap', 'lock_interrupt', 'race_getter',
                                     'race_forward', 'race_close'])
def test_actual_parent_two_requests_and_drain(tmp_path, monkeypatch, end_mode):
    args, reservation = _prepared_fixture(tmp_path, monkeypatch)
    from slaif_raggedized_helper import gpu_worker_protocol as wire
    args['wire_policy'] = wire.Policy(calls=1 if end_mode in ('single', 'single_nofork') else 3)
    prepared = launch.prepare(**args)
    original = subprocess.Popen.__init__
    worker_fd = prepared._descriptors['worker']
    script = (Path(prepared._owner.directory) / 'worker.py').read_text()
    marker = 'if __name__ == "__main__":\n    sys.exit(main())'
    injection = '''
class FakeBackend:
    constructed = 0
    def __init__(self, manifest, root, definition, tokenizer, inventory, lease, uuid):
        type(self).constructed += 1
        assert type(self).constructed == 1
        assert os.getpid() == 2 and os.getppid() == 1
        self.space = embedding_space.admit(manifest, root, definition, tokenizer, inventory)
        self._vocab = 20
        read_fd, write_fd = os.pipe()
        child = os.fork()
        if child == 0:
            os.close(read_fd)
            os.write(write_fd, b'R')
            os.close(write_fd)
            while True:
                __import__('signal').pause()
        os.close(write_fd)
        assert os.read(read_fd, 1) == b'R'
        os.close(read_fd)
    def forward_cls(self, rows):
        return [[float(row[0])] * 1024 for row in rows]
    def close(self):
        pass
gpu_embedding_backend.GPUEmbeddingBackend = FakeBackend
for candidate_fd in range(128):
    try:
        link = os.readlink('/proc/self/fd/' + str(candidate_fd))
    except OSError:
        continue
    assert link != CONTROL_PIPE_IDENTITY
'''
    if end_mode == 'single_nofork':
        start = injection.index('        read_fd, write_fd = os.pipe()')
        end = injection.index('    def forward_cls', start)
        injection = injection[:start] + injection[end:]
    assert script.count(marker) == 1
    harness = script.replace(marker, injection + '\n' + marker).encode()
    path = tmp_path / 'harness.py'
    path.write_bytes(harness)
    path.chmod(0o400)
    fake_fd = os.open(path, os.O_RDONLY | os.O_CLOEXEC)

    def intercept(process, argv, **kwargs):
        argv = list(argv)
        status_fd = int(argv[argv.index('--json-status-fd') + 1])
        status_identity = os.readlink(f'/proc/self/fd/{status_fd}')
        actual_harness = harness.replace(b'CONTROL_PIPE_IDENTITY', repr(status_identity).encode())
        path.chmod(0o600)
        path.write_bytes(actual_harness)
        path.chmod(0o400)
        print('harness_sha256=' + hashlib.sha256(actual_harness).hexdigest())
        index = argv.index('/worker.py')
        assert argv[index - 1] == f'/proc/self/fd/{worker_fd}'
        argv[index - 1] = f'/proc/self/fd/{fake_fd}'
        kwargs['pass_fds'] = tuple(fake_fd if fd == worker_fd else fd
                                   for fd in kwargs['pass_fds'])
        return original(process, argv, **kwargs)

    worker = None
    try:
        monkeypatch.setattr(subprocess.Popen, '__init__', intercept)
        worker = parent.GPUEmbeddingWorker(prepared)
        init_pid, namespace = worker._init_identity
        assert init_pid != 2
        assert parent._proc_identity(init_pid)[2][-1] == 1
        assert namespace == parent._proc_identity(init_pid)[4]
        assert namespace != os.stat('/proc/self/ns/pid').st_ino
        with pytest.raises(gpu_device_lease.DeviceLeaseRefused):
            gpu_device_lease.acquire(args['lease_root'], args['device'].host_id,
                                     args['device'].device_uuid)
        with pytest.raises(parent.WorkerRefused):
            parent.GPUEmbeddingWorker(prepared)
        actual_process = worker._process
        worker._process = object()
        with pytest.raises(parent.WorkerRefused):
            worker.close()
        assert parent._records[id(worker)][5] is actual_process
        worker._process = actual_process
        actual_pidfd = worker._pidfd
        worker._pidfd = worker._wrapper_fd
        with pytest.raises(parent.WorkerRefused):
            worker.close()
        assert parent._records[id(worker)][6]['_pidfd'] == actual_pidfd
        worker._pidfd = actual_pidfd
        worker._prepared = object()
        with pytest.raises(parent.WorkerRefused):
            worker.close()
        assert parent._records[id(worker)][1] is prepared
        worker._prepared = prepared
        read_fd, write_fd = os.pipe()
        forked = os.fork()
        if forked == 0:
            os.close(read_fd)
            try:
                try:
                    worker._owned_lock()
                except parent.WorkerRefused:
                    pass
                else:
                    os._exit(1)
                worker.close()
            except parent.WorkerRefused:
                os.write(write_fd, b'R')
            finally:
                os._exit(0)
        os.close(write_fd)
        assert os.read(read_fd, 1) == b'R'
        os.close(read_fd)
        assert os.waitpid(forked, 0)[1] == 0
        actual_lock = worker._owned_lock()
        assert parent._records[id(worker)][10] is actual_lock
        fake = object.__new__(parent.GPUEmbeddingWorker)
        with pytest.raises(parent.WorkerRefused):
            fake._owned_lock()
        if end_mode.startswith('race_'):
            import threading

            entered, release = threading.Event(), threading.Event()
            original_check = parent.GPUEmbeddingWorker._owner_ok
            outcome = []
            dispatch = []
            original_exchange = worker._pump.exchange

            def scheduled_check(owner):
                result = original_check(owner)
                if threading.current_thread() is thread and result:
                    entered.set()
                    assert release.wait(10)
                return result

            def run():
                try:
                    action = {'race_getter': worker._owned_lock,
                              'race_forward': lambda: worker.forward_cls([[2, 3]]),
                              'race_close': worker.close}[end_mode]
                    outcome.append(action())
                except BaseException as exc:
                    outcome.append(exc)

            def exchange(*args):
                dispatch.append(True)
                return original_exchange(*args)

            monkeypatch.setattr(worker._pump, 'exchange', exchange)
            monkeypatch.setattr(parent.GPUEmbeddingWorker, '_owner_ok', scheduled_check)
            thread = threading.Thread(target=run)
            thread.start()
            try:
                assert entered.wait(10)
                worker.close()
                assert worker._state == 'closed' and prepared._closed
                assert id(worker) not in parent._records
                reservation.assert_owned()
            finally:
                release.set()
                thread.join(timeout=10)
                assert not thread.is_alive()
            assert len(outcome) == 1 and type(outcome[0]) is parent.WorkerRefused
            assert str(outcome[0]) == 'worker refused' and not dispatch
            assert actual_lock.acquire(blocking=False)
            actual_lock.release()
            return
        if end_mode == 'lock_overlap':
            import inspect
            import textwrap
            import threading

            entered, release = threading.Event(), threading.Event()
            original_exchange = worker._pump.exchange
            outcome = []

            def held_exchange(*values):
                entered.set()
                assert release.wait(10)
                return original_exchange(*values)

            def run_forward():
                try:
                    outcome.append(worker.forward_cls([[2, 3]]))
                except BaseException as exc:
                    outcome.append(exc)

            monkeypatch.setattr(worker._pump, 'exchange', held_exchange)
            thread = threading.Thread(target=run_forward)
            thread.start()
            try:
                assert entered.wait(10)
                worker._lock = threading.Lock()
                worker._busy = False
                with pytest.raises(parent.WorkerRefused):
                    worker._owned_lock()
                with pytest.raises(parent.WorkerRefused):
                    worker.forward_cls([[4, 5]])
                with pytest.raises(parent.WorkerRefused):
                    worker.close()
                # Remove only the lock identity predicate to show its causal effect.
                source = textwrap.dedent(inspect.getsource(parent.GPUEmbeddingWorker._owner_ok))
                predicate = '                and self._lock is record[10]\n'
                assert source.count(predicate) == 1
                namespace = {}
                exec(source.replace(predicate, ''), parent.__dict__, namespace)
                with monkeypatch.context() as control:
                    control.setattr(parent.GPUEmbeddingWorker, '_owner_ok', namespace['_owner_ok'])
                    assert worker._owner_ok()
                    assert worker._owned_lock() is actual_lock
                    with pytest.raises(parent.WorkerRefused):
                        worker.forward_cls([[4, 5]])
                worker._lock = actual_lock
            finally:
                worker._lock = actual_lock
                release.set()
                thread.join(timeout=10)
                assert not thread.is_alive()
                monkeypatch.setattr(worker._pump, 'exchange', original_exchange)
            assert len(outcome) == 1 and outcome[0].rows == ((2.0,) * 1024,)
            assert actual_lock.acquire(blocking=False)
            actual_lock.release()
        elif end_mode == 'lock_interrupt':
            import threading

            class FrozenInterrupt(BaseException):
                def __setattr__(self, name, value):
                    raise RuntimeError('immutable')

            interrupt = FrozenInterrupt()
            original_exchange = worker._pump.exchange

            def interrupt_exchange(*values):
                worker._lock = threading.Lock()
                raise interrupt

            monkeypatch.setattr(worker._pump, 'exchange', interrupt_exchange)
            caught = None
            try:
                worker.forward_cls([[2, 3]])
            except BaseException as exc:
                caught = exc
            assert caught is interrupt
            assert actual_lock.acquire(blocking=False)
            actual_lock.release()
            assert parent._retained[id(prepared._owner)] is worker
            assert not prepared._closed
            reservation.assert_owned()
            worker._lock = actual_lock
            monkeypatch.setattr(worker._pump, 'exchange', original_exchange)
            worker.close()
            assert worker._state == 'closed'
            reservation.assert_owned()
            return
        first = worker.forward_cls([[2, 3]])
        assert first.rows == ((2.0,) * 1024,)
        if end_mode not in ('single', 'single_nofork'):
            second = worker.forward_cls([[4, 5]])
            assert second.rows == ((4.0,) * 1024,)
        if end_mode == 'invalid':
            with pytest.raises(parent.WorkerRefused):
                worker.forward_cls([[True, 2]])
        elif end_mode == 'module':
            from slaif_raggedized_helper import gpu_worker_protocol as wire
            with monkeypatch.context() as changed:
                changed.setattr(wire, 'rows_ok', lambda *args: None)
                with pytest.raises(parent.WorkerRefused):
                    worker.forward_cls([[2, 3]])
        elif end_mode == 'binding':
            worker._binding['space'] = 'f' * 64
            with pytest.raises(parent.WorkerRefused):
                worker.forward_cls([[2, 3]])
        elif end_mode in ('body_interrupt', 'cleanup_interrupt'):
            class FrozenInterrupt(BaseException):
                def __setattr__(self, name, value):
                    raise RuntimeError('immutable')

            body = FrozenInterrupt() if end_mode == 'body_interrupt' else ValueError()
            cleanup = FrozenInterrupt()
            actual_exchange = worker._pump.exchange
            actual_drain = worker._drain_pipes

            def fail_exchange(*args):
                raise body

            def fail_drain():
                raise cleanup

            monkeypatch.setattr(worker._pump, 'exchange', fail_exchange)
            monkeypatch.setattr(worker, '_drain_pipes', fail_drain)
            caught = None
            try:
                worker.forward_cls([[2, 3]])
            except BaseException as exc:
                caught = exc
            monkeypatch.setattr(worker._pump, 'exchange', actual_exchange)
            monkeypatch.setattr(worker, '_drain_pipes', actual_drain)
            assert caught is (body if end_mode == 'body_interrupt' else cleanup)
            assert worker._state == 'pending'
            assert parent._retained[id(prepared._owner)] is worker
            worker.close()
        else:
            actual_drain = worker._drain_pipes
            calls = []

            def interrupt_once():
                calls.append(1)
                if len(calls) == 1:
                    raise KeyboardInterrupt()
                return actual_drain()

            monkeypatch.setattr(worker, '_drain_pipes', interrupt_once)
            with pytest.raises(KeyboardInterrupt):
                worker.close()
            assert worker._state == 'pending'
            assert parent._retained[id(prepared._owner)] is worker
            reservation.assert_owned()
            read_fd, write_fd = os.pipe()
            forked = os.fork()
            if forked == 0:
                os.close(read_fd)
                try:
                    worker.close()
                except parent.WorkerRefused:
                    os.write(write_fd, b'R')
                finally:
                    os._exit(0)
            os.close(write_fd)
            assert os.read(read_fd, 1) == b'R'
            os.close(read_fd)
            assert os.waitpid(forked, 0)[1] == 0
            worker.close()
            assert len(calls) == 2
        assert worker._state == 'closed'
        with pytest.raises(parent.WorkerRefused):
            worker.forward_cls([[2, 3]])
        assert worker._state == 'closed'
        read_fd, write_fd = os.pipe()
        forked = os.fork()
        if forked == 0:
            os.close(read_fd)
            try:
                worker.close()
            except parent.WorkerRefused:
                os.write(write_fd, b'R')
            finally:
                os._exit(0)
        os.close(write_fd)
        assert os.read(read_fd, 1) == b'R'
        os.close(read_fd)
        assert os.waitpid(forked, 0)[1] == 0
        fresh = gpu_device_lease.acquire(args['lease_root'], args['device'].host_id,
                                         args['device'].device_uuid)
        fresh.close()
        reservation.assert_owned()
    finally:
        if worker is not None and worker._state != 'closed':
            worker.close()
        os.close(fake_fd)
        reservation.close()


@pytest.mark.parametrize('bypass', [False, True])
def test_wrong_ready_binding_causal_control(tmp_path, monkeypatch, bypass):
    args, reservation = _prepared_fixture(tmp_path, monkeypatch)
    prepared = launch.prepare(**args)
    owner_key = id(prepared._owner)
    script = (Path(prepared._owner.directory) / 'worker.py').read_text()
    marker = 'if __name__ == "__main__":\n    sys.exit(main())'
    injection = '''
class FakeBackend:
    def __init__(self, manifest, root, definition, tokenizer, inventory, lease, uuid):
        self.space = embedding_space.admit(manifest, root, definition, tokenizer, inventory)
        self._vocab = 20
    def forward_cls(self, rows):
        return [[0.0] * 1024 for row in rows]
    def close(self):
        pass
gpu_embedding_backend.GPUEmbeddingBackend = FakeBackend
original_write = wire.Pipe.write
def altered_write(self, value, *args):
    if value.get('ready') is True:
        value = dict(value, space='f' * 64)
    return original_write(self, value, *args)
wire.Pipe.write = altered_write
'''
    assert script.count(marker) == 1
    harness = script.replace(marker, injection + '\n' + marker).encode()
    path = tmp_path / 'wrong-binding.py'
    path.write_bytes(harness)
    path.chmod(0o400)
    print('wrong_binding_harness_sha256=' + hashlib.sha256(harness).hexdigest())
    fake_fd = os.open(path, os.O_RDONLY | os.O_CLOEXEC)
    worker_fd = prepared._descriptors['worker']
    original_popen = subprocess.Popen.__init__
    original_check = parent._check_ready
    observed_wrong = []

    def intercept(process, argv, **kwargs):
        argv = list(argv)
        index = argv.index('/worker.py')
        assert argv[index - 1] == f'/proc/self/fd/{worker_fd}'
        argv[index - 1] = f'/proc/self/fd/{fake_fd}'
        kwargs['pass_fds'] = tuple(fake_fd if fd == worker_fd else fd
                                   for fd in kwargs['pass_fds'])
        return original_popen(process, argv, **kwargs)

    def bypass_space(observed, expected):
        assert observed['space'] != expected['space']
        observed_wrong.append(observed['space'])
        original_check(dict(observed, space=expected['space']), expected)

    worker = None
    try:
        monkeypatch.setattr(subprocess.Popen, '__init__', intercept)
        if bypass:
            monkeypatch.setattr(parent, '_check_ready', bypass_space)
            worker = parent.GPUEmbeddingWorker(prepared)
            assert observed_wrong == ['f' * 64]
            assert parent._retained[owner_key] is worker
            worker.close()
        else:
            with pytest.raises(parent.WorkerRefused):
                parent.GPUEmbeddingWorker(prepared)
        assert owner_key not in parent._retained
        reservation.assert_owned()
    finally:
        if worker is not None and worker._state != 'closed':
            worker.close()
        os.close(fake_fd)
        reservation.close()


def test_constructor_transient_pidfd_verification_drains_actual_owner(tmp_path, monkeypatch):
    args, reservation = _prepared_fixture(tmp_path, monkeypatch)
    prepared = launch.prepare(**args)
    key = id(prepared._owner)
    actual_verify = parent._verified_init
    attempts = []

    def transient(pid, wrapper_pid, namespace, owner):
        attempts.append((pid, wrapper_pid, namespace, owner))
        if len(attempts) == 1:
            __import__('time').sleep(0.2)
            raise OSError('synthetic verification interruption')
        return actual_verify(pid, wrapper_pid, namespace, owner)

    monkeypatch.setattr(parent, '_verified_init', transient)
    try:
        with pytest.raises(parent.WorkerRefused):
            parent.GPUEmbeddingWorker(prepared)
        assert len(attempts) == 2
        assert attempts[0] == attempts[1]
        assert attempts[0][3]._prepared is prepared
        assert attempts[0][3]._state == 'closed'
        assert key not in parent._retained
        assert prepared._closed
        reservation.assert_owned()
    finally:
        reservation.close()


@pytest.mark.parametrize('mode', ['replay', 'digest', 'extra', 'noncanonical', 'trailing',
                                  'oversized', 'fp32'])
def test_actual_parent_rejects_hostile_reply(tmp_path, monkeypatch, mode):
    from slaif_raggedized_helper import gpu_worker_protocol as wire

    args, reservation = _prepared_fixture(tmp_path, monkeypatch)
    args['wire_policy'] = wire.Policy(calls=2, response_bytes=8192)
    prepared = launch.prepare(**args)
    worker_fd = prepared._descriptors['worker']
    script = (Path(prepared._owner.directory) / 'worker.py').read_text()
    marker = 'if __name__ == "__main__":\n    sys.exit(main())'
    injection = '''
class FakeBackend:
    def __init__(self, manifest, root, definition, tokenizer, inventory, lease, uuid):
        self.space = embedding_space.admit(manifest, root, definition, tokenizer, inventory)
        self._vocab = 20
    def forward_cls(self, rows):
        return [[0.0] * 1024 for row in rows]
    def close(self):
        pass
gpu_embedding_backend.GPUEmbeddingBackend = FakeBackend
original_write = wire.Pipe.write
MODE = MODE_VALUE
def hostile_write(self, value, *args):
    if 'nonce' not in value:
        return original_write(self, value, *args)
    value = dict(value)
    if MODE == 'replay':
        value['nonce'] = 'f' * 32
    elif MODE == 'digest':
        value['digest'] = 'f' * 64
    elif MODE == 'extra':
        value['extra'] = True
    elif MODE == 'fp32':
        value['rows'] = [[0.1] * 1024]
    if MODE == 'oversized':
        raw = b'x' * 9000 + b'\\n'
    elif MODE == 'noncanonical':
        raw = b'{ "a":1}\\n'
    elif MODE == 'trailing':
        raw = b'{}\\n{}\\n'
    else:
        raw = wire.encode(value) + b'\\n'
    os.write(self.w, raw)
wire.Pipe.write = hostile_write
'''.replace('MODE_VALUE', repr(mode))
    assert script.count(marker) == 1
    harness = script.replace(marker, injection + '\n' + marker).encode()
    path = tmp_path / 'hostile.py'
    path.write_bytes(harness)
    path.chmod(0o400)
    print('hostile_' + mode + '_sha256=' + hashlib.sha256(harness).hexdigest())
    fake_fd = os.open(path, os.O_RDONLY | os.O_CLOEXEC)
    original_popen = subprocess.Popen.__init__

    def intercept(process, argv, **kwargs):
        argv = list(argv)
        index = argv.index('/worker.py')
        assert argv[index - 1] == f'/proc/self/fd/{worker_fd}'
        argv[index - 1] = f'/proc/self/fd/{fake_fd}'
        kwargs['pass_fds'] = tuple(fake_fd if fd == worker_fd else fd
                                   for fd in kwargs['pass_fds'])
        return original_popen(process, argv, **kwargs)

    worker = None
    try:
        monkeypatch.setattr(subprocess.Popen, '__init__', intercept)
        worker = parent.GPUEmbeddingWorker(prepared)
        with pytest.raises(parent.WorkerRefused):
            worker.forward_cls([[2, 3]])
        assert worker._state == 'closed'
        assert id(prepared._owner) not in parent._retained
        reservation.assert_owned()
    finally:
        if worker is not None and worker._state != 'closed':
            worker.close()
        os.close(fake_fd)
        reservation.close()


@pytest.mark.parametrize('bypass', [False, True])
def test_actual_popen_acquisition_interrupt_and_causal_control(tmp_path, monkeypatch, bypass):
    import json
    import select
    import signal

    args, reservation = _prepared_fixture(tmp_path, monkeypatch)
    prepared = launch.prepare(**args)
    key = id(prepared._owner)
    capsule = Path(prepared._owner.directory)
    script = b'import os,time\nos.write(1,b"R")\ntime.sleep(30)\n'
    harness = tmp_path / 'acquisition-harness.py'
    harness.write_bytes(script)
    harness.chmod(0o400)
    print('acquisition_harness_sha256=' + hashlib.sha256(script).hexdigest())
    fake_fd = os.open(harness, os.O_RDONLY | os.O_CLOEXEC)
    original = subprocess.Popen.__init__
    worker_fd = prepared._descriptors['worker']
    witness = {}

    class FrozenInterrupt(BaseException):
        def __setattr__(self, *args):
            raise RuntimeError('immutable')

    interruption = FrozenInterrupt()

    def intercept(process, argv, **kwargs):
        argv = list(argv)
        index = argv.index('/worker.py')
        assert argv[index - 1] == f'/proc/self/fd/{worker_fd}'
        argv[index - 1] = f'/proc/self/fd/{fake_fd}'
        kwargs['pass_fds'] = tuple(fake_fd if fd == worker_fd else fd
                                   for fd in kwargs['pass_fds'])
        original(process, argv, **kwargs)
        witness['process'] = process
        owner = parent._retained[key]
        assert select.select([owner._control_r], [], [], 4)[0]
        raw = os.read(owner._control_r, 4096)
        status = json.loads(raw)
        host_init = status['child-pid']
        assert parent._proc_identity(host_init)[2][-1] == 1
        assert parent._proc_identity(host_init)[4] == status['pid-namespace']
        ancestor = parent._proc_identity(host_init)[0]
        for _ in range(32):
            if ancestor == process.pid:
                break
            assert ancestor > 1
            ancestor = parent._proc_identity(ancestor)[0]
        else:
            raise AssertionError('namespace init not descended from owned wrapper')
        witness['pidfd'] = os.pidfd_open(host_init, 0)
        assert select.select([process.stdout], [], [], 4)[0]
        assert os.read(process.stdout.fileno(), 1) == b'R'
        raise interruption

    caught = None
    try:
        monkeypatch.setattr(subprocess.Popen, '__init__', intercept)
        if bypass:
            monkeypatch.setattr(parent, '_register_process', lambda owner, process: None)
        try:
            parent.GPUEmbeddingWorker(prepared)
        except BaseException as exc:
            caught = exc
        assert caught is interruption
        process = witness['process']
        if bypass:
            assert key not in parent._retained
            assert prepared._closed and not capsule.exists()
            assert not select.select([witness['pidfd']], [], [], 0)[0]
        else:
            owner = parent._retained[key]
            assert owner._process is process and owner._prepared is prepared
            assert parent._records[id(owner)][5] is process
            assert owner._state == 'pending'
            assert not prepared._closed and capsule.exists()
        reservation.assert_owned()
    finally:
        if 'pidfd' in witness:
            try:
                signal.pidfd_send_signal(witness['pidfd'], signal.SIGKILL)
            except ProcessLookupError:
                pass
            assert select.select([witness['pidfd']], [], [], 5)[0]
            os.close(witness['pidfd'])
        owner = parent._retained.get(key)
        if 'process' in witness:
            witness['process'].wait(timeout=5)
            assert os.read(witness['process'].stdout.fileno(), 1) == b''
            assert os.read(witness['process'].stderr.fileno(), 1) == b''
            streams = (witness['process'].stdin, witness['process'].stdout,
                       witness['process'].stderr)
            for stream in streams:
                if owner is None:
                    stream.close()
                else:
                    owner._close_stream(stream)
        if owner is not None:
            # The witness independently proved the actual namespace pidfd exited,
            # wrapper was reaped, and all pipes reached EOF before test-only disposal.
            control = bytearray()
            while True:
                chunk = os.read(owner._control_r, 4097 - len(control))
                if not chunk:
                    break
                control.extend(chunk)
                assert len(control) <= 4096
            owner._close_fd('_control_r')
            owner._close_fd('_wrapper_fd')
            assert not owner._fd_identities
        if not prepared._closed:
            prepared.close()
        if owner is not None:
            assert parent._records[id(owner)][0] is owner
            assert parent._retained[key] is owner
            del parent._records[id(owner)]
            del parent._retained[key]
        reservation.assert_owned()
        reservation.close()
        os.close(fake_fd)



@pytest.mark.parametrize('fail_index', [3, 4])
def test_actual_acquisition_handle_registration_interrupt(tmp_path, monkeypatch, fail_index):
    import select

    args, reservation = _prepared_fixture(tmp_path, monkeypatch)
    prepared = launch.prepare(**args)
    key = id(prepared._owner)
    script = b'import os,time\nos.write(1,b"R")\ntime.sleep(30)\n'
    harness = tmp_path / 'handle-harness.py'
    harness.write_bytes(script)
    harness.chmod(0o400)
    print('handle_harness_sha256=' + hashlib.sha256(script).hexdigest())
    fake_fd = os.open(harness, os.O_RDONLY | os.O_CLOEXEC)
    worker_fd = prepared._descriptors['worker']
    original_init = subprocess.Popen.__init__
    original_remember = parent.GPUEmbeddingWorker._remember_fd
    calls = []
    owners = []

    class FrozenInterrupt(BaseException):
        def __setattr__(self, *args):
            raise RuntimeError('immutable')

    interruption = FrozenInterrupt()

    def intercept(process, argv, **kwargs):
        argv = list(argv)
        index = argv.index('/worker.py')
        assert argv[index - 1] == f'/proc/self/fd/{worker_fd}'
        argv[index - 1] = f'/proc/self/fd/{fake_fd}'
        kwargs['pass_fds'] = tuple(fake_fd if fd == worker_fd else fd
                                   for fd in kwargs['pass_fds'])
        return original_init(process, argv, **kwargs)

    def fail_after_register(owner, fd, *, pidfd=False):
        original_remember(owner, fd, pidfd=pidfd)
        calls.append(fd)
        if len(calls) == fail_index:
            owners.append(owner)
            assert select.select([owner._control_r], [], [], 4)[0]
            assert select.select([owner._process.stdout], [], [], 4)[0]
            assert os.read(owner._process.stdout.fileno(), 1) == b'R'
            raise interruption

    caught = None
    try:
        monkeypatch.setattr(subprocess.Popen, '__init__', intercept)
        monkeypatch.setattr(parent.GPUEmbeddingWorker, '_remember_fd', fail_after_register)
        try:
            parent.GPUEmbeddingWorker(prepared)
        except BaseException as exc:
            caught = exc
        assert caught is interruption
        owner = owners[0]
        assert owner._prepared is prepared
        assert owner._state == 'closed' and key not in parent._retained
        assert prepared._closed
        reservation.assert_owned()
    finally:
        reservation.close()
        os.close(fake_fd)


def test_reaped_during_popen_initialization_stays_pending(tmp_path, monkeypatch):
    import json
    import select

    args, reservation = _prepared_fixture(tmp_path, monkeypatch)
    prepared = launch.prepare(**args)
    key = id(prepared._owner)
    worker_fd = prepared._descriptors['worker']
    script = b'import os,time\nos.write(1,b"R")\ntime.sleep(0.3)\n'
    harness = tmp_path / 'reaped-harness.py'
    harness.write_bytes(script)
    harness.chmod(0o400)
    print('reaped_harness_sha256=' + hashlib.sha256(script).hexdigest())
    fake_fd = os.open(harness, os.O_RDONLY | os.O_CLOEXEC)
    original_init = subprocess.Popen.__init__
    original_pidfd_open = os.pidfd_open
    witness = {}
    attempts = []

    class FrozenInterrupt(BaseException):
        def __setattr__(self, *args):
            raise RuntimeError('immutable')

    interruption = FrozenInterrupt()

    def intercept(process, argv, **kwargs):
        argv = list(argv)
        index = argv.index('/worker.py')
        assert argv[index - 1] == f'/proc/self/fd/{worker_fd}'
        argv[index - 1] = f'/proc/self/fd/{fake_fd}'
        kwargs['pass_fds'] = tuple(fake_fd if fd == worker_fd else fd
                                   for fd in kwargs['pass_fds'])
        original_init(process, argv, **kwargs)
        witness['process'] = process
        owner = parent._retained[key]
        assert select.select([owner._control_r], [], [], 4)[0]
        status = json.loads(os.read(owner._control_r, 4096))
        init_pid = status['child-pid']
        assert parent._proc_identity(init_pid)[2][-1] == 1
        assert parent._proc_identity(init_pid)[4] == status['pid-namespace']
        witness['pidfd'] = original_pidfd_open(init_pid, 0)
        assert select.select([process.stdout], [], [], 4)[0]
        assert os.read(process.stdout.fileno(), 1) == b'R'
        assert process.wait(timeout=5) == 0
        assert select.select([witness['pidfd']], [], [], 5)[0]
        raise interruption

    def track_pidfd(pid, flags=0):
        attempts.append(pid)
        return original_pidfd_open(pid, flags)

    caught = None
    try:
        monkeypatch.setattr(subprocess.Popen, '__init__', intercept)
        monkeypatch.setattr(os, 'pidfd_open', track_pidfd)
        try:
            parent.GPUEmbeddingWorker(prepared)
        except BaseException as exc:
            caught = exc
        assert caught is interruption
        owner = parent._retained[key]
        assert owner._process is witness['process']
        assert owner._process.returncode == 0 and owner._state == 'pending'
        assert not prepared._closed and attempts == []
        reservation.assert_owned()
    finally:
        if 'pidfd' in witness:
            assert select.select([witness['pidfd']], [], [], 5)[0]
            os.close(witness['pidfd'])
        owner = parent._retained.get(key)
        if 'process' in witness:
            process = witness['process']
            assert process.returncode == 0
            assert os.read(process.stdout.fileno(), 1) == b''
            assert os.read(process.stderr.fileno(), 1) == b''
            for stream in (process.stdin, process.stdout, process.stderr):
                stream.close()
        if owner is not None:
            owner._close_fd('_control_w')
            assert select.select([owner._control_r], [], [], 5)[0]
            control = bytearray()
            while True:
                data = os.read(owner._control_r, 4097 - len(control))
                if not data:
                    break
                control.extend(data)
                assert len(control) <= 4096
            for attr in ('_control_r', '_control_w'):
                owner._close_fd(attr)
            assert not owner._fd_identities
        if not prepared._closed:
            prepared.close()
        if owner is not None:
            assert parent._records[id(owner)][0] is owner
            assert parent._retained[key] is owner
            del parent._records[id(owner)]
            del parent._retained[key]
        reservation.assert_owned()
        reservation.close()
        os.close(fake_fd)


def test_actual_parent_single_initialization(tmp_path, monkeypatch):
    args, reservation = _prepared_fixture(tmp_path, monkeypatch)
    prepared = launch.prepare(**args)
    key = id(prepared._owner)
    source = (Path(prepared._owner.directory) / 'worker.py').read_text()
    marker = 'if __name__ == "__main__":\n    sys.exit(main())'
    injection = '''
class FakeBackend:
    def __init__(self, manifest, root, definition, tokenizer, inventory, lease, uuid):
        self.space=embedding_space.admit(manifest,root,definition,tokenizer,inventory)
        self._vocab=20
    def forward_cls(self,rows):
        return [[float(row[0])]*1024 for row in rows]
    def close(self): pass
gpu_embedding_backend.GPUEmbeddingBackend=FakeBackend
'''
    assert source.count(marker) == 1
    harness = tmp_path / 'private-worker.py'
    harness.write_text(source.replace(marker, injection + '\n' + marker))
    harness.chmod(0o400)
    print('single_init_harness_sha256=' + hashlib.sha256(harness.read_bytes()).hexdigest())
    fakefd = os.open(harness, os.O_RDONLY | os.O_CLOEXEC)
    oldfd = prepared._descriptors['worker']
    popen_init = subprocess.Popen.__init__
    def intercept(process, argv, **kwargs):
        argv = list(argv)
        i = argv.index('/worker.py')
        assert argv[i-1] == f'/proc/self/fd/{oldfd}'
        argv[i-1] = f'/proc/self/fd/{fakefd}'
        kwargs['pass_fds'] = tuple(fakefd if fd == oldfd else fd for fd in kwargs['pass_fds'])
        return popen_init(process, argv, **kwargs)
    monkeypatch.setattr(subprocess.Popen, '__init__', intercept)
    worker = None
    actual = None
    try:
        worker = parent.GPUEmbeddingWorker(prepared)
        snapshot = dict(worker.__dict__)
        process = worker._process
        record = parent._records[id(worker)]
        record_snapshot = list(record)
        retained_snapshot = dict(parent._retained)
        actual = worker._owned_lock()
        never_started = parent.GPUEmbeddingWorker.__new__(parent.GPUEmbeddingWorker)
        with pytest.raises(parent.WorkerRefused):
            parent.GPUEmbeddingWorker.__init__(worker, prepared)
        assert worker.__dict__ == snapshot
        assert all(worker.__dict__[name] is value for name, value in snapshot.items())
        assert parent._records[id(worker)] is record and record == record_snapshot
        assert parent._retained == retained_snapshot and not prepared._closed
        assert worker._process is process and worker._lock is actual
        assert parent._records[id(worker)][5] is process and process.poll() is None
        assert parent._retained[key] is worker and worker._owner_ok()
        child_dir = tmp_path / 'child'
        child_dir.mkdir()
        forked = os.fork()
        if forked == 0:
            try:
                child_args, child_reservation = _prepared_fixture(child_dir, monkeypatch)
                child_prepared = launch.prepare(**child_args)
                try:
                    assert child_prepared._pid == os.getpid()
                    before = dict(worker.__dict__)
                    records = dict(parent._records)
                    retained = dict(parent._retained)
                    with pytest.raises(parent.WorkerRefused):
                        parent.GPUEmbeddingWorker.__init__(worker, child_prepared)
                    assert worker.__dict__ == before
                    assert parent._records == records and parent._retained == retained
                    with pytest.raises(parent.WorkerRefused):
                        parent.GPUEmbeddingWorker.__init__(never_started, child_prepared)
                    assert '_constructor_started' not in never_started.__dict__
                    assert not child_prepared._closed
                finally:
                    child_prepared.close()
                    child_reservation.close()
                os._exit(0)
            except BaseException:
                import traceback
                traceback.print_exc()
                os._exit(1)
        assert os.waitpid(forked, 0)[1] == 0
        assert worker.__dict__ == snapshot and worker._owner_ok()
        assert worker.forward_cls([[2, 3]]).rows == ((2.0,) * 1024,)
        worker.close()
        closed = dict(worker.__dict__)
        with pytest.raises(parent.WorkerRefused):
            parent.GPUEmbeddingWorker.__init__(worker, prepared)
        assert worker.__dict__ == closed
        fresh = launch.prepare(**args)
        try:
            with pytest.raises(parent.WorkerRefused):
                parent.GPUEmbeddingWorker.__init__(worker, fresh)
            assert worker.__dict__ == closed and not fresh._closed
        finally:
            fresh.close()
        assert key not in parent._retained
    finally:
        if worker is not None:
            if worker._state != 'closed':
                worker.close()
            assert worker._state == 'closed' and key not in parent._retained
        elif not prepared._closed:
            prepared.close()
        reservation.assert_owned()
        reservation.close()
        os.close(fakefd)
