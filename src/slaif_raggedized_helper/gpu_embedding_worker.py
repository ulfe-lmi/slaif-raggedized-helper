"""Private ownership primitives for an isolated GPU worker.

This module is under construction and is not a service or an authorization boundary.
"""

from dataclasses import dataclass
import os
import select
import threading
import weakref
from pathlib import Path


class WorkerRefused(ValueError):
    """The owned worker could not be established or verified."""


def _proc_identity(pid):
    """Read one explicitly identified process, never enumerate the process table."""
    root = Path('/proc') / str(pid)
    status = (root / 'status').read_text(encoding='ascii')
    fields = {}
    for line in status.splitlines():
        key, sep, value = line.partition(':')
        if sep and key in {'Pid', 'PPid', 'Uid', 'NSpid'}:
            if key in fields:
                raise WorkerRefused('worker refused')
            fields[key] = value.split()
    if set(fields) != {'Pid', 'PPid', 'Uid', 'NSpid'}:
        raise WorkerRefused('worker refused')
    stat = (root / 'stat').read_text(encoding='ascii')
    # comm is parenthesized and can itself contain spaces and parentheses.
    end = stat.rfind(')')
    if end < 0:
        raise WorkerRefused('worker refused')
    tail = stat[end + 2:].split()
    if len(tail) < 20 or int(fields['Pid'][0]) != pid:
        raise WorkerRefused('worker refused')
    return (int(fields['PPid'][0]), tuple(map(int, fields['Uid'])),
            tuple(map(int, fields['NSpid'])), int(tail[19]),
            os.stat(root / 'ns/pid').st_ino)


def _verified_init(pid, wrapper_pid, reported_namespace, owner):
    """Return a live pidfd only after verifying ancestry and namespace identity.

    The caller must still retain the unreaped wrapper and own cleanup. No numeric
    process identifier returned here is an authorization to signal by PID.
    """
    if type(pid) is not int or pid <= 1 or type(wrapper_pid) is not int or wrapper_pid <= 1:
        raise WorkerRefused('worker refused')
    try:
        before = _proc_identity(pid)
        fd = owner._candidate_pidfd
        if fd is None:
            fd = os.pidfd_open(pid, 0)
            owner._candidate_pidfd = fd
            _records[id(owner)][6]['_candidate_pidfd'] = fd
            owner._remember_fd(fd, pidfd=True)
        after = _proc_identity(pid)
        if before != after or select.select([fd], [], [], 0)[0]:
            raise WorkerRefused('worker refused')
        parent, uids, nspids, _, namespace = after
        if (not uids or uids[0] != os.geteuid() or not nspids or nspids[-1] != 1
                or namespace != reported_namespace
                or namespace == os.stat('/proc/self/ns/pid').st_ino):
            raise WorkerRefused('worker refused')
        seen = {pid}
        for _ in range(32):
            if parent == wrapper_pid:
                break
            if parent <= 1 or parent in seen:
                raise WorkerRefused('worker refused')
            seen.add(parent)
            ancestor = _proc_identity(parent)
            if not ancestor[1] or ancestor[1][0] != os.geteuid():
                raise WorkerRefused('worker refused')
            parent = ancestor[0]
        else:
            raise WorkerRefused('worker refused')
        if _proc_identity(pid) != after or select.select([fd], [], [], 0)[0]:
            raise WorkerRefused('worker refused')
        owner._pidfd = fd
        _records[id(owner)][6]['_pidfd'] = fd
        owner._candidate_pidfd = None
        _records[id(owner)][6]['_candidate_pidfd'] = None
    except Exception:
        raise WorkerRefused('worker refused') from None


def _expected_binding_unchecked(prepared):
    """Snapshot the ready message from the admitted plan and pinned config."""
    import json

    from . import gpu_device_lease, gpu_worker_launch as launch, gpu_worker_protocol as wire
    from .schema import EmbeddingDefinition

    if type(prepared) is not launch.PreparedLaunch:
        raise WorkerRefused('worker refused')
    prepared.revalidate()
    start = wire.parse(prepared.startup)
    definition = EmbeddingDefinition.model_validate(start['definition'], strict=True)
    config = json.loads(_owned_read('config.json', prepared._descriptors['artifacts']))
    vocab, pad = config.get('vocab_size'), config.get('pad_token_id')
    if (type(vocab) is not int or not 1 <= vocab <= 10000000 or type(pad) is not int
            or not 0 <= pad < vocab):
        raise WorkerRefused('worker refused')
    binding = {'schema': wire.SCHEMA, 'api': wire.API,
               'startup_nonce': start['startup_nonce'], 'space': start['space'],
               'definition': definition.fingerprint(), 'profile': prepared.profile_id,
               'code_id': prepared.code_id, 'policy_id': start['policy_id'],
               'device_uuid': prepared._device.device_uuid,
               'device_key': gpu_device_lease._key(prepared._device.host_id,
                                                    prepared._device.device_uuid)}
    ready = {**binding, 'ready': True, 'vocab': vocab, 'contract': 'gpu-fp16-cls'}
    policy = wire.Policy(**start['policy'])
    if (start['profile'] != prepared.profile_id or start['code_id'] != prepared.code_id
            or start['device_uuid'] != prepared._device.device_uuid
            or start['host'] != prepared._device.host_id
            or start['policy_id'] != wire.policy_id(policy)
            or len(wire.encode(ready)) + 1 > policy.response_bytes
            or len(wire.encode(ready)) + 1 > policy.total_output_bytes
            or len(wire.encode(ready)) + 1 > prepared._resource.output_bytes):
        raise WorkerRefused('worker refused')
    prepared.revalidate()
    return binding, vocab, policy


def _expected_binding(prepared):
    try:
        return _expected_binding_unchecked(prepared)
    except Exception:
        raise WorkerRefused('worker refused') from None


class _Duplex:
    """Bounded concurrent request write and response/stderr/control drain."""

    def __init__(self, stdin, stdout, stderr, control, policy, resource, lifetime):
        import time

        self.stdin, self.stdout, self.stderr, self.control = stdin, stdout, stderr, control
        self.policy, self.resource = policy, resource
        self.deadline = time.monotonic() + lifetime
        self.written = self.read = self.stderr_read = 0
        for fd in (stdin, stdout, stderr, control):
            os.set_blocking(fd, False)

    def exchange(self, frame, response_cap):
        import time

        from . import gpu_worker_protocol as wire

        data = frame + b'\n'
        policy = self.policy
        if (type(response_cap) is not int or not 1 <= response_cap <= policy.response_bytes
                or len(data) > policy.request_bytes
                or self.written + len(data) > policy.total_input_bytes
                or self.read + response_cap > policy.total_output_bytes
                or self.read + response_cap > self.resource.output_bytes):
            raise WorkerRefused('worker refused')
        end = min(self.deadline, time.monotonic() + policy.io_seconds)
        offset = 0
        response = bytearray()
        while True:
            remaining = end - time.monotonic()
            if remaining <= 0:
                raise WorkerRefused('worker refused')
            reads, writes, _ = select.select(
                [self.stdout, self.stderr, self.control],
                [self.stdin] if offset < len(data) else [], [], remaining)
            if not reads and not writes:
                raise WorkerRefused('worker refused')
            if self.stderr in reads:
                chunk = os.read(self.stderr, min(4096, self.resource.stderr_bytes
                                                  - self.stderr_read + 1))
                self.stderr_read += len(chunk)
                if not chunk or self.stderr_read > self.resource.stderr_bytes:
                    raise WorkerRefused('worker refused')
            if self.control in reads:
                # Control bytes after the initial verified status indicate exit or corruption.
                raise WorkerRefused('worker refused')
            if self.stdout in reads:
                chunk = os.read(self.stdout, min(4096, response_cap - len(response) + 1))
                self.read += len(chunk)
                if (not chunk or self.read > policy.total_output_bytes
                        or self.read > self.resource.output_bytes):
                    raise WorkerRefused('worker refused')
                response.extend(chunk)
                if len(response) > response_cap:
                    raise WorkerRefused('worker refused')
                newline = response.find(b'\n')
                if newline >= 0:
                    if newline != len(response) - 1 or offset != len(data):
                        raise WorkerRefused('worker refused')
                    # A queued second frame or EOF cannot be accepted as this reply.
                    if select.select([self.stdout, self.control], [], [], 0)[0]:
                        raise WorkerRefused('worker refused')
                    return wire.parse(bytes(response[:-1]))
            if self.stdin in writes:
                count = os.write(self.stdin, data[offset:offset + 4096])
                if count <= 0:
                    raise WorkerRefused('worker refused')
                offset += count
                self.written += count


# Actual owners remain reachable even when construction or cleanup raises.
_retained = {}
_records = {}
_closed = weakref.WeakKeyDictionary()
_registry_lock = threading.Lock()
_used_nonces = set()


def _initial_status(process, control, limit, deadline, state=None):
    import json
    import time

    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError
            result[key] = value
        return result

    if state is None:
        state = [bytearray(), 0]
    status = state[0]
    outputs = [control, process.stdout.fileno(), process.stderr.fileno()]
    for fd in outputs:
        os.set_blocking(fd, False)
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise WorkerRefused('worker refused')
        ready = select.select(outputs, [], [], remaining)[0]
        if not ready:
            raise WorkerRefused('worker refused')
        if process.stdout.fileno() in ready:
            raise WorkerRefused('worker refused')
        if process.stderr.fileno() in ready:
            data = os.read(process.stderr.fileno(), min(4096, limit - state[1] + 1))
            state[1] += len(data)
            if not data or state[1] > limit:
                raise WorkerRefused('worker refused')
        if control in ready:
            # Read one byte so the exit status cannot be accidentally consumed.
            data = os.read(control, 1)
            if not data or len(status) >= 4096:
                raise WorkerRefused('worker refused')
            if data == b'\n':
                value = json.loads(status.decode('utf-8'), object_pairs_hook=pairs)
                if (type(value) is not dict or set(value) != {
                        'child-pid', 'ipc-namespace', 'mnt-namespace', 'net-namespace',
                        'pid-namespace', 'uts-namespace'}
                        or any(type(v) is not int or v <= 1 for v in value.values())):
                    raise WorkerRefused('worker refused')
                return value['child-pid'], value['pid-namespace'], state[1]
            status.extend(data)


def _owned_read(path, directory=None):
    from . import gpu_worker_launch as launch

    owner = launch._Owner()
    body = None
    result = None
    try:
        fd = owner.add(os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC
                               | os.O_NONBLOCK, dir_fd=directory))
        result = launch._read_fd(fd, 1024 * 1024)
    except BaseException as exc:
        body = exc
    try:
        errors = owner.cleanup()
        cleanup = next((error for error in errors if not isinstance(error, Exception)),
                       errors[0] if errors else None)
        if owner.pending and cleanup is None:
            cleanup = WorkerRefused('worker refused')
    except BaseException as exc:
        cleanup = exc
    selected = _select_error(body, cleanup)
    if selected is not None:
        raise selected from None
    return result


def _self_identity():
    import hashlib

    return hashlib.sha256(_owned_read(__file__)).digest()


def _dependency_guard(prepared):
    import types

    from . import (cpu_embedding_backend, embedding_artifacts, embedding_job_ownership,
                   embedding_space, gpu_device_lease, gpu_worker_launch, gpu_worker_protocol,
                   native_tokenizers, schema)

    modules = (cpu_embedding_backend, embedding_artifacts, embedding_job_ownership,
               embedding_space, gpu_device_lease, gpu_worker_launch, gpu_worker_protocol,
               native_tokenizers, schema)
    if gpu_worker_protocol.code_id() != prepared.code_id:
        raise WorkerRefused('worker refused')
    functions = tuple((module.__name__, name, value)
                      for module in modules for name, value in sorted(vars(module).items())
                      if isinstance(value, types.FunctionType)
                      and value.__module__ == module.__name__)
    return functions + (gpu_worker_launch.PreparedLaunch.revalidate,
                        gpu_worker_launch.PreparedLaunch.launch_arguments,
                        gpu_worker_launch.PreparedLaunch.close,
                        schema.EmbeddingDefinition.fingerprint)


def _copy_rows(rows, vocab, limit):
    from . import gpu_worker_protocol as wire

    if type(rows) is not list:
        raise WorkerRefused('worker refused')
    outer = rows[:limit + 1]
    if not 1 <= len(outer) <= limit or any(type(row) is not list for row in outer):
        raise WorkerRefused('worker refused')
    copied = [row[:1025] for row in outer]
    wire.rows_ok(copied, vocab, limit)
    return copied


def _check_ready(observed, expected):
    if (type(observed) is not dict or observed != expected
            or any(type(observed[k]) is not type(v) for k, v in expected.items())):
        raise WorkerRefused('worker refused')


def _check_reply(reply, binding, nonce, digest, count):
    from . import gpu_worker_protocol as wire

    if (type(reply) is not dict or set(reply) != (set(binding) | {'nonce', 'digest', 'rows'})
            or any(type(reply[k]) is not type(v) or reply[k] != v for k, v in binding.items())
            or reply['nonce'] != nonce or reply['digest'] != digest):
        raise WorkerRefused('worker refused')
    wire.output_ok(reply['rows'], count)
    return tuple(tuple(row) for row in reply['rows'])


def _register_process(owner, process):
    """Retain the actual object before its initialization may create a child."""
    owner._process = process
    _records[id(owner)][5] = process


def _require_unreaped(process):
    # Caller holds Popen's wait lock, so its returncode cannot change via Popen.wait/poll.
    if process.returncode is not None:
        raise WorkerRefused('worker refused')


def _select_error(body, cleanup):
    if body is not None and not isinstance(body, Exception):
        return body
    if cleanup is not None and not isinstance(cleanup, Exception):
        return cleanup
    return body if body is not None else cleanup


class GPUEmbeddingWorker:
    """Own one prepared isolated worker; callers retain their reservation and artifacts."""

    def __new__(cls, *args, **kwargs):
        instance = super().__new__(cls)
        instance._constructor_creator = os.getpid()
        instance._constructor_lock = threading.Lock()
        return instance

    def __init__(self, prepared):
        if self.__dict__.get('_constructor_creator') != os.getpid():
            raise WorkerRefused('worker refused')
        with self._constructor_lock:
            if '_constructor_started' in self.__dict__:
                raise WorkerRefused('worker refused')
            self._constructor_started = True
        import subprocess
        import time

        from . import gpu_worker_launch as launch, gpu_worker_protocol as wire

        if (type(prepared) is not launch.PreparedLaunch
                or prepared._pid != os.getpid()):
            raise WorkerRefused('worker refused')
        self._pid = os.getpid()
        self._prepared = prepared
        self._process = None
        self._control_r = self._control_w = self._pidfd = self._wrapper_fd = None
        self._candidate_pidfd = None
        self._fd_identities = {}
        self._unknown_fd = False
        self._init_identity = None
        self._status_state = [bytearray(), 0]
        self._exit_status = bytearray()
        self._drain_stdout = self._drain_stderr = 0
        self._seen_calls = set()
        self._state = 'starting'
        self._ns_drained = False
        self._reaped = False
        self._busy = False
        self._lock = threading.Lock()
        self._calls = 0
        self._binding = None
        self._vocab = None
        self._pump = None
        self._owner_key = id(prepared._owner)
        with _registry_lock:
            if self._owner_key in _retained:
                raise WorkerRefused('worker refused')
            _retained[self._owner_key] = self
            _records[id(self)] = [self, prepared, prepared._owner, self._pid,
                                  self._owner_key, None,
                                  {name: None for name in ('_control_r', '_control_w',
                                   '_pidfd', '_candidate_pidfd', '_wrapper_fd')}, None,
                                  self._fd_identities, None, self._lock]
        try:
            self._source_hash = _self_identity()
            self._guards = (_expected_binding, _verified_init, _initial_status, _check_ready,
                            _check_reply, _copy_rows, _Duplex, _dependency_guard, _self_identity,
                            _owned_read,
                            type(self).forward_cls, type(self).close, type(self)._close_owned)
            self._dependencies = _dependency_guard(prepared)
            binding, vocab, policy = _expected_binding(prepared)
            nonce = binding['startup_nonce']
            with _registry_lock:
                if nonce in _used_nonces:
                    raise WorkerRefused('worker refused')
                _used_nonces.add(nonce)
            argv, fds = prepared.launch_arguments()
            self._control_r, self._control_w = os.pipe2(os.O_CLOEXEC)
            _records[id(self)][6].update(_control_r=self._control_r,
                                         _control_w=self._control_w)
            self._remember_fd(self._control_r)
            self._remember_fd(self._control_w)
            if self._control_w >= 128:
                raise WorkerRefused('worker refused')
            argv = list(argv)
            index = argv.index('/usr/bin/bwrap') + 1
            argv[index:index] = ['--json-status-fd', str(self._control_w)]
            started = time.monotonic()
            # Keep the actual Popen object reachable before its initialization can launch.
            process = object.__new__(subprocess.Popen)
            _register_process(self, process)
            subprocess.Popen.__init__(process, argv, pass_fds=(*fds, self._control_w),
                                      stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE, start_new_session=True)
            self._reconcile_process()
            self._close_fd('_control_w')
            deadline = min(time.monotonic() + policy.io_seconds,
                           started + prepared._resource.wall_seconds)
            init_pid, namespace, stderr = _initial_status(self._process, self._control_r,
                                                prepared._resource.stderr_bytes, deadline,
                                                self._status_state)
            self._init_identity = (init_pid, namespace)
            with self._process._waitpid_lock:
                _require_unreaped(self._process)
                _verified_init(init_pid, self._process.pid, namespace, self)
            self._pump = _Duplex(self._process.stdin.fileno(), self._process.stdout.fileno(),
                                 self._process.stderr.fileno(), self._control_r, policy,
                                 prepared._resource, prepared._resource.wall_seconds)
            self._pump.deadline = started + prepared._resource.wall_seconds
            self._pump.stderr_read = stderr
            ready = {**binding, 'ready': True, 'vocab': vocab, 'contract': 'gpu-fp16-cls'}
            observed = self._pump.exchange(prepared.startup, len(wire.encode(ready)) + 1)
            _check_ready(observed, ready)
            self._binding, self._vocab, self._policy = binding, vocab, policy
            _records[id(self)][9] = (self._pump, wire.encode(binding), vocab,
                                      wire.policy_id(policy), self._pump.deadline)
            self._state = 'live'
        except BaseException as body:
            self._state = 'faulted'
            cleanup = None
            try:
                self.close()
            except BaseException as exc:
                cleanup = exc
            selected = _select_error(body, cleanup)
            if isinstance(selected, Exception):
                raise WorkerRefused('worker refused') from None
            raise selected from None

    def _reconcile_process(self):
        """Adopt handles already attached to the pre-registered actual process."""
        process = self._process
        record = _records[id(self)]
        if (record[5] is not process or type(getattr(process, 'pid', None)) is not int
                or process.pid <= 1 or getattr(process, '_child_created', None) is not True):
            raise WorkerRefused('worker refused')
        if self._wrapper_fd is None:
            with process._waitpid_lock:
                _require_unreaped(process)
                self._wrapper_fd = os.pidfd_open(process.pid, 0)
                record[6]['_wrapper_fd'] = self._wrapper_fd
                self._remember_fd(self._wrapper_fd, pidfd=True)
        else:
            self._check_fd(self._wrapper_fd)
        streams = (getattr(process, 'stdin', None), getattr(process, 'stdout', None),
                   getattr(process, 'stderr', None))
        if any(stream is None or stream.closed for stream in streams):
            raise WorkerRefused('worker refused')
        if record[7] is None:
            record[7] = streams
        if any(actual is not captured for actual, captured in zip(streams, record[7], strict=True)):
            raise WorkerRefused('worker refused')
        for stream in streams:
            fd = stream.fileno()
            if fd not in self._fd_identities:
                self._remember_fd(fd)
            else:
                self._check_fd(fd)

    def _remember_fd(self, fd, *, pidfd=False):
        st = os.fstat(fd)
        identity = (st.st_dev, st.st_ino, st.st_mode)
        self._fd_identities[fd] = (identity, pidfd)

    def _check_fd(self, fd):
        expected = self._fd_identities.get(fd)
        if expected is None:
            self._unknown_fd = True
            raise WorkerRefused('worker refused')
        try:
            st = os.fstat(fd)
            if (st.st_dev, st.st_ino, st.st_mode) != expected[0]:
                raise WorkerRefused('worker refused')
        except BaseException:
            self._unknown_fd = True
            raise

    def _close_fd(self, attr):
        fd = getattr(self, attr)
        if fd is None:
            return
        self._check_fd(fd)
        # Never retry a descriptor number after close may have taken effect.
        setattr(self, attr, None)
        _records[id(self)][6][attr] = None
        del self._fd_identities[fd]
        self._unknown_fd = True
        os.close(fd)
        self._unknown_fd = False

    def _close_stream(self, stream):
        if stream.closed:
            return
        fd = stream.fileno()
        self._check_fd(fd)
        del self._fd_identities[fd]
        self._unknown_fd = True
        stream.close()
        self._unknown_fd = False

    def _owner_ok(self):
        try:
            record = _records.get(id(self))
            return (record is not None and record[0] is self and record[3] == os.getpid()
                    and self._pid == record[3] and self._prepared is record[1]
                    and self._prepared._owner is record[2] and self._owner_key == record[4]
                    and self._process is record[5] and self._fd_identities is record[8]
                    and self._lock is record[10]
                    and _retained.get(record[4]) is self
                    and (record[5] is None or record[7] is None
                         or record[7] == (record[5].stdin, record[5].stdout, record[5].stderr))
                    and all(getattr(self, name) == fd for name, fd in record[6].items()))
        except Exception:
            return False

    def _owned_lock(self):
        record = _records.get(id(self))
        if (record is None or not self._owner_ok()
                or _records.get(id(self)) is not record):
            raise WorkerRefused('worker refused')
        return record[10]

    def close(self):
        record = _records.get(id(self))
        if record is None:
            if _closed.get(self) == os.getpid():
                return
            raise WorkerRefused('worker refused')
        lock = self._owned_lock()
        if not lock.acquire(blocking=False):
            raise WorkerRefused('worker refused')
        try:
            if not self._owner_ok():
                raise WorkerRefused('worker refused')
            self._close_owned()
        except Exception:
            raise WorkerRefused('worker refused') from None
        finally:
            lock.release()

    def _close_owned(self):
        import signal
        import subprocess
        import time

        if self._pid != os.getpid():
            raise WorkerRefused('worker refused')
        if self._state == 'closed':
            return
        if self._busy or not self._owner_ok():
            raise WorkerRefused('worker refused')
        self._state = 'pending'
        process = self._process
        if process is not None:
            try:
                self._reconcile_process()
            except Exception:
                self._stop_unverified_wrapper()
                raise
            if self._control_w is not None:
                self._close_fd('_control_w')
            if self._pidfd is None and self._init_identity is None and self._control_r is not None:
                try:
                    for fd in (self._control_r, process.stdout.fileno(), process.stderr.fileno()):
                        self._check_fd(fd)
                    child, namespace, _ = _initial_status(
                        process, self._control_r, self._prepared._resource.stderr_bytes,
                        time.monotonic() + 1, self._status_state)
                    self._init_identity = (child, namespace)
                except Exception:
                    pass
            if self._pidfd is None and self._init_identity is not None:
                try:
                    with process._waitpid_lock:
                        _require_unreaped(process)
                        _verified_init(*self._init_identity[:1], process.pid,
                                       self._init_identity[1], self)
                except Exception:
                    pass
            if self._wrapper_fd is not None:
                self._check_fd(self._wrapper_fd)
            if self._pidfd is None:
                # Keep the owner pending when the namespace cannot be verified.
                self._stop_unverified_wrapper()
                raise WorkerRefused('worker refused')
            self._check_fd(self._pidfd)
            if not self._ns_drained:
                try:
                    signal.pidfd_send_signal(self._pidfd, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                if not select.select([self._pidfd], [], [], 5)[0]:
                    raise WorkerRefused('worker refused')
                self._ns_drained = True
            if not self._reaped:
                if self._wrapper_fd is None:
                    raise WorkerRefused('worker refused')
                with process._waitpid_lock:
                    if process.returncode is None and not select.select(
                            [self._wrapper_fd], [], [], 2)[0]:
                        try:
                            _require_unreaped(process)
                            if os.getpgid(process.pid) != process.pid:
                                raise WorkerRefused('worker refused')
                            os.killpg(process.pid, signal.SIGTERM)
                        except ProcessLookupError:
                            pass
                        if not select.select([self._wrapper_fd], [], [], 2)[0]:
                            try:
                                _require_unreaped(process)
                                if os.getpgid(process.pid) != process.pid:
                                    raise WorkerRefused('worker refused')
                                os.killpg(process.pid, signal.SIGKILL)
                            except ProcessLookupError:
                                pass
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    raise WorkerRefused('worker refused') from None
                self._reaped = True
            self._drain_pipes()
        if self._unknown_fd:
            raise WorkerRefused('worker refused')
        for attr in ('_control_w', '_control_r', '_pidfd', '_wrapper_fd'):
            self._close_fd(attr)
        self._prepared.close()
        self._state = 'closed'
        with _registry_lock:
            _closed[self] = os.getpid()
            del _retained[self._owner_key]
            del _records[id(self)]

    def _stop_unverified_wrapper(self):
        import signal

        process = self._process
        if self._wrapper_fd is None:
            return
        self._check_fd(self._wrapper_fd)
        with process._waitpid_lock:
            _require_unreaped(process)
            if select.select([self._wrapper_fd], [], [], 0)[0]:
                return
            try:
                _require_unreaped(process)
                if os.getpgid(process.pid) != process.pid:
                    raise WorkerRefused('worker refused')
                os.killpg(process.pid, signal.SIGTERM)
                if not select.select([self._wrapper_fd], [], [], 2)[0]:
                    _require_unreaped(process)
                    if os.getpgid(process.pid) != process.pid:
                        raise WorkerRefused('worker refused')
                    os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass

    def _drain_pipes(self):
        import json
        import time

        process = self._process
        if process.stdin is not None and not process.stdin.closed:
            self._close_stream(process.stdin)
        streams = [stream for stream in (process.stdout, process.stderr)
                   if stream is not None and not stream.closed]
        # Discard only bounded already-owned output; never capture request contents.
        fds = {stream.fileno(): stream for stream in streams}
        if self._control_r is not None:
            fds[self._control_r] = None
        stdout_fd = process.stdout.fileno() if not process.stdout.closed else None
        stderr_fd = process.stderr.fileno() if not process.stderr.closed else None
        stdout_before = self._pump.read if self._pump is not None else 0
        stderr_before = (self._pump.stderr_read if self._pump is not None
                         else self._status_state[1])
        end = time.monotonic() + 5
        while fds:
            remaining = end - time.monotonic()
            if remaining <= 0:
                raise WorkerRefused('worker refused')
            ready = select.select(list(fds), [], [], remaining)[0]
            if not ready:
                raise WorkerRefused('worker refused')
            for fd in ready:
                self._check_fd(fd)
                data = os.read(fd, 4096)
                if fd == stdout_fd:
                    self._drain_stdout += len(data)
                elif fd == stderr_fd:
                    self._drain_stderr += len(data)
                if (stdout_before + self._drain_stdout > self._prepared._resource.output_bytes
                        or stderr_before + self._drain_stderr
                        > self._prepared._resource.stderr_bytes):
                    raise WorkerRefused('worker refused')
                if fd == self._control_r:
                    self._exit_status.extend(data)
                    if len(self._exit_status) > 4096:
                        raise WorkerRefused('worker refused')
                if not data:
                    stream = fds.pop(fd)
                    if stream is not None:
                        self._close_stream(stream)
        try:
            raw = bytes(self._exit_status)
            if not raw.endswith(b'\n') or raw.count(b'\n') != 1:
                raise ValueError
            def pairs(items):
                value = {}
                for key, item in items:
                    if key in value:
                        raise ValueError
                    value[key] = item
                return value
            status = json.loads(raw[:-1], object_pairs_hook=pairs)
            if (type(status) is not dict or set(status) != {'exit-code'}
                    or type(status['exit-code']) is not int
                    or not 0 <= status['exit-code'] <= 255):
                raise ValueError
        except Exception:
            raise WorkerRefused('worker refused') from None

    def forward_cls(self, rows):
        import hashlib
        import secrets

        from . import gpu_worker_protocol as wire

        lock = self._owned_lock()
        if not lock.acquire(blocking=False):
            raise WorkerRefused('worker refused')
        try:
            if self._state != 'live' or self._busy or not self._owner_ok():
                raise WorkerRefused('worker refused')
            try:
                self._busy = True
                if (self._source_hash != _self_identity()
                        or self._guards != (_expected_binding, _verified_init, _initial_status,
                                            _check_ready, _check_reply, _copy_rows, _Duplex,
                                            _dependency_guard,
                                            _self_identity, _owned_read, type(self).forward_cls,
                                            type(self).close, type(self)._close_owned)):
                    raise WorkerRefused('worker refused')
                if _dependency_guard(self._prepared) != self._dependencies:
                    raise WorkerRefused('worker refused')
                self._prepared.revalidate()
                snapshot = _records[id(self)][9]
                expected, vocab, policy = _expected_binding(self._prepared)
                if (self._pump is not snapshot[0] or wire.encode(self._binding) != snapshot[1]
                        or self._binding != expected or self._vocab != vocab or vocab != snapshot[2]
                        or wire.policy_id(self._policy) != snapshot[3] or self._policy != policy
                        or self._pump.policy is not self._policy
                        or self._pump.resource is not self._prepared._resource
                        or self._pump.deadline != snapshot[4]
                        or (self._pump.stdin, self._pump.stdout,
                            self._pump.stderr, self._pump.control)
                        != (self._process.stdin.fileno(), self._process.stdout.fileno(),
                            self._process.stderr.fileno(), self._control_r)):
                    raise WorkerRefused('worker refused')
                for fd in (self._pump.stdin, self._pump.stdout, self._pump.stderr, self._control_r):
                    self._check_fd(fd)
                if _dependency_guard(self._prepared) != self._dependencies:
                    raise WorkerRefused('worker refused')
                copied = _copy_rows(rows, self._vocab, self._policy.max_rows)
                if self._calls >= self._policy.calls:
                    raise WorkerRefused('worker refused')
                digest = hashlib.sha256(wire.encode(copied)).hexdigest()
                nonce = secrets.token_hex(16)
                if nonce in self._seen_calls:
                    raise WorkerRefused('worker refused')
                self._seen_calls.add(nonce)
                request = {'nonce': nonce, 'digest': digest, 'rows': copied}
                cap = len(wire.encode(self._binding)) + len(copied) * 32770 + 512
                reply = self._pump.exchange(wire.encode(request),
                                            min(cap, self._policy.response_bytes))
                result = _check_reply(reply, self._binding, nonce, digest, len(copied))
                self._prepared.revalidate()
                if _dependency_guard(self._prepared) != self._dependencies:
                    raise WorkerRefused('worker refused')
                self._calls += 1
                return RawCLSResult(tuple(sorted(self._binding.items())),
                                    result)
            except BaseException as body:
                self._state = 'faulted'
                self._busy = False
                cleanup = None
                try:
                    self._close_owned()
                except BaseException as exc:
                    cleanup = exc
                selected = _select_error(body, cleanup)
                if isinstance(selected, Exception):
                    raise WorkerRefused('worker refused') from None
                raise selected from None
            finally:
                self._busy = False

        finally:
            lock.release()


@dataclass(frozen=True)
class RawCLSResult:
    """Observed binding and ordered raw finite FP32 CLS rows."""

    binding: tuple
    rows: tuple
