"""Stable identity for a prepared raw GPU worker; this is not authority to run one."""

import dataclasses
import hashlib
import os
import re
from pathlib import Path

from . import gpu_worker_launch as launch, gpu_worker_protocol as wire
from . import native_tokenizers
from .schema import EmbeddingDefinition


class IdentityRefused(ValueError):
    """Identity cannot be established."""


_DOMAIN = b'slaif-gpu-fp16-cls-worker-identity-v1\n'
_SCOPE = ('Pinned Python, explicit driver bytes, code, selected lock/profile and package '
          'name/version metadata; excludes package contents, launcher and system libraries, '
          'CUDA/driver/runtime compatibility, physical ownership or vacancy, and hardware '
          'qualification.')
_HEX = re.compile(r'[0-9a-f]{64}\Z')


@dataclasses.dataclass(frozen=True)
class PlannedWorkerIdentity:
    record_bytes: bytes
    fingerprint: str


def _source_hash(module):
    raw = native_tokenizers._read_artifact(Path(module.__file__), 1024 * 1024)
    return hashlib.sha256(raw).hexdigest()


def _digest(raw):
    return 'sha256:' + hashlib.sha256(_DOMAIN + raw).hexdigest()


def _hex(value):
    return type(value) is str and _HEX.fullmatch(value) is not None


def _validate(value):
    keys = {'schema', 'contract', 'space_id', 'definition_fingerprint', 'inventory_id',
            'profile_id', 'code_id', 'wire_api', 'wire_schema', 'wire_policy', 'wire_policy_id',
            'python_sha256', 'resource', 'host_id', 'device_uuid', 'nodes', 'drivers',
            'parent_sha256', 'launch_sha256', 'identity_sha256', 'hardware_qualification',
            'runtime_integrity_scope'}
    if type(value) is not dict or set(value) != keys:
        raise ValueError
    if (type(value['schema']) is not int or value['schema'] != 1
            or value['contract'] != 'gpu-fp16-cls-worker-v1'
            or value['wire_api'] != wire.API or type(value['wire_schema']) is not int
            or value['wire_schema'] != wire.SCHEMA
            or value['hardware_qualification'] != 'unknown'
            or value['runtime_integrity_scope'] != _SCOPE):
        raise ValueError
    for key in ('space_id', 'inventory_id', 'profile_id', 'code_id', 'wire_policy_id',
                'python_sha256', 'parent_sha256', 'launch_sha256', 'identity_sha256'):
        if not _hex(value[key]):
            raise ValueError
    fp = value['definition_fingerprint']
    if type(fp) is not str or not fp.startswith('sha256:') or not _hex(fp[7:]):
        raise ValueError
    policy = value['wire_policy']
    if type(policy) is not dict or set(policy) != {f.name for f in dataclasses.fields(wire.Policy)}:
        raise ValueError
    if wire.policy_id(wire.Policy(**policy)) != value['wire_policy_id']:
        raise ValueError
    resource = value['resource']
    resource_keys = {f.name for f in dataclasses.fields(launch.ResourcePolicy)}
    if type(resource) is not dict or set(resource) != resource_keys:
        raise ValueError
    launch.ResourcePolicy(**resource)
    nodes = value['nodes']
    if type(nodes) is not list or not 2 <= len(nodes) <= 4:
        raise ValueError
    parsed = []
    for item in nodes:
        if type(item) is not dict or set(item) != {'path', 'major', 'minor', 'observed_rdev'}:
            raise ValueError
        observed = item['observed_rdev']
        if observed is not None and (type(observed) is not list or len(observed) != 2
                or any(type(n) is not int or n < 0 for n in observed)
                or observed != [item['major'], item['minor']]):
            raise ValueError
        parsed.append(launch.DeviceNode(item['path'], item['major'], item['minor']))
    launch.DevicePlan(value['host_id'], value['device_uuid'], tuple(parsed))
    if [n['path'] for n in nodes] != sorted(n['path'] for n in nodes):
        raise ValueError
    drivers = value['drivers']
    if type(drivers) is not list or len(drivers) > 8:
        raise ValueError
    for item in drivers:
        if type(item) is not dict or set(item) != {'name', 'size', 'sha256'}:
            raise ValueError
        launch.DriverFile('/identity/' + item['name'], item['name'], item['size'], item['sha256'])
    if (len({d['name'] for d in drivers}) != len(drivers)
            or [d['name'] for d in drivers] != sorted(d['name'] for d in drivers)
            or sum(d['size'] for d in drivers) > 1024**3):
        raise ValueError


def validate_record(record_bytes):
    """Validate canonical persisted bytes and return their fingerprint, never owner authority."""
    try:
        if type(record_bytes) is not bytes or len(record_bytes) > 16384:
            raise ValueError
        value = wire.parse(record_bytes)
        _validate(value)
        return _digest(record_bytes)
    except Exception:
        raise IdentityRefused('identity refused') from None


def predict(prepared):
    """Revalidate a current prepared launch and describe its stable worker identity."""
    try:
        if type(prepared) is not launch.PreparedLaunch or prepared._pid != os.getpid():
            raise ValueError
        prepared.revalidate()
        start = wire.parse(prepared.startup)
        definition = EmbeddingDefinition.model_validate(start['definition'], strict=True)
        policy = wire.Policy(**start['policy'])
        if (start['profile'] != prepared.profile_id or start['code_id'] != prepared.code_id
                or start['policy_id'] != wire.policy_id(policy)
                or start['host'] != prepared._device.host_id
                or start['device_uuid'] != prepared._device.device_uuid):
            raise ValueError
        nodes = []
        for index, node in enumerate(prepared._device.nodes):
            rdev = os.fstat(prepared._descriptors[f'device{index}']).st_rdev
            observed = [os.major(rdev), os.minor(rdev)]
            if observed == [1, 3]:
                observed = None  # Explicit private /dev/null fixture, not an NVIDIA observation.
            elif observed != [node.major, node.minor]:
                raise ValueError
            nodes.append({'path': node.path, 'major': node.major, 'minor': node.minor,
                          'observed_rdev': observed})
        from . import gpu_embedding_worker as parent
        import sys
        record = {'schema': 1, 'contract': 'gpu-fp16-cls-worker-v1',
                  'space_id': start['space'], 'definition_fingerprint': definition.fingerprint(),
                  'inventory_id': start['inventory'], 'profile_id': prepared.profile_id,
                  'code_id': prepared.code_id, 'wire_api': wire.API, 'wire_schema': wire.SCHEMA,
                  'wire_policy': dataclasses.asdict(policy), 'wire_policy_id': start['policy_id'],
                  'python_sha256': launch._hash_open_file(
                      prepared._descriptors['python'], 128 * 1024**2),
                  'resource': dataclasses.asdict(prepared._resource),
                  'host_id': prepared._device.host_id,
                  'device_uuid': prepared._device.device_uuid,
                  'nodes': sorted(nodes, key=lambda item: item['path']),
                  'drivers': sorted(({'name': d.name, 'size': d.size, 'sha256': d.sha256}
                                     for d in prepared._recheck['drivers']),
                                    key=lambda d: d['name']),
                  'parent_sha256': _source_hash(parent), 'launch_sha256': _source_hash(launch),
                  'identity_sha256': _source_hash(sys.modules[__name__]),
                  'hardware_qualification': 'unknown', 'runtime_integrity_scope': _SCOPE}
        raw = wire.encode(record)
        fingerprint = validate_record(raw)
        prepared.revalidate()
        return PlannedWorkerIdentity(raw, fingerprint)
    except Exception:
        raise IdentityRefused('identity refused') from None


@dataclasses.dataclass(frozen=True)
class ObservedWorkerIdentity:
    record_bytes: bytes
    fingerprint: str
    ready_binding_bytes: bytes


def _live_boundary(worker, parent):
    import select

    if not worker._owner_ok() or worker._state != 'live' or worker._busy:
        raise ValueError
    record = parent._records.get(id(worker))
    if record is None or record[10] is not worker._lock:
        raise ValueError
    if (worker._source_hash != parent._self_identity()
            or worker._guards != (parent._expected_binding, parent._verified_init,
                parent._initial_status, parent._check_ready, parent._check_reply,
                parent._copy_rows, parent._Duplex, parent._dependency_guard,
                parent._self_identity, parent._owned_read, type(worker).forward_cls,
                type(worker).close, type(worker)._close_owned)
            or parent._dependency_guard(worker._prepared) != worker._dependencies):
        raise ValueError
    worker._prepared.revalidate()
    snapshot = record[9]
    expected, vocab, policy = parent._expected_binding(worker._prepared)
    pump = worker._pump
    process = worker._process
    if (type(snapshot) is not tuple or len(snapshot) != 5 or pump is not snapshot[0]
            or wire.encode(worker._binding) != snapshot[1] or worker._binding != expected
            or worker._vocab != vocab or vocab != snapshot[2]
            or wire.policy_id(worker._policy) != snapshot[3] or worker._policy != policy
            or pump.policy is not worker._policy or pump.resource is not worker._prepared._resource
            or pump.deadline != snapshot[4]
            or (pump.stdin, pump.stdout, pump.stderr, pump.control)
            != (process.stdin.fileno(), process.stdout.fileno(), process.stderr.fileno(),
                worker._control_r)
            or worker._unknown_fd or worker._candidate_pidfd is not None
            or worker._pidfd is None or worker._wrapper_fd is None
            or worker._init_identity is None):
        raise ValueError
    for fd in (pump.stdin, pump.stdout, pump.stderr, pump.control,
               worker._pidfd, worker._wrapper_fd):
        saved = worker._fd_identities.get(fd)
        st = os.fstat(fd)
        if saved is None or saved[0] != (st.st_dev, st.st_ino, st.st_mode):
            raise ValueError
    if (not worker._fd_identities[worker._pidfd][1]
            or not worker._fd_identities[worker._wrapper_fd][1]
            or select.select([worker._pidfd, worker._wrapper_fd], [], [], 0)[0]):
        raise ValueError
    with process._waitpid_lock:
        parent._require_unreaped(process)
        pid, namespace = worker._init_identity
        info = parent._proc_identity(pid)
        if (not info[1] or info[1][0] != os.geteuid() or not info[2]
                or info[2][-1] != 1 or info[4] != namespace
                or namespace == os.stat('/proc/self/ns/pid').st_ino):
            raise ValueError
        ancestor, seen = info[0], {pid}
        for _ in range(32):
            if ancestor == process.pid:
                break
            if ancestor <= 1 or ancestor in seen:
                raise ValueError
            seen.add(ancestor)
            step = parent._proc_identity(ancestor)
            if not step[1] or step[1][0] != os.geteuid():
                raise ValueError
            ancestor = step[0]
        else:
            raise ValueError
        if (parent._proc_identity(pid) != info
                or select.select([worker._pidfd, worker._wrapper_fd], [], [], 0)[0]):
            raise ValueError
    if parent._dependency_guard(worker._prepared) != worker._dependencies or not worker._owner_ok():
        raise ValueError
    return bytes(snapshot[1])


def observe(worker):
    """Observe an actual registered live parent; retain no ownership of it."""
    try:
        from . import gpu_embedding_worker as parent
        if type(worker) is not parent.GPUEmbeddingWorker or worker._pid != os.getpid():
            raise ValueError
        lock = worker._owned_lock()
        if not lock.acquire(blocking=False):
            raise ValueError
        try:
            ready = _live_boundary(worker, parent)
            planned = predict(worker._prepared)
            if _live_boundary(worker, parent) != ready:
                raise ValueError
            return ObservedWorkerIdentity(planned.record_bytes, planned.fingerprint, ready)
        finally:
            lock.release()
    except Exception:
        raise IdentityRefused('identity refused') from None
