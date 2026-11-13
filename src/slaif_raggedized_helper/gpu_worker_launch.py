"""Preparation primitives for the private GPU worker (no process is launched here).

This module is not a controller and does not grant permission to use a GPU.
"""

import dataclasses
import os
import re
import threading
import weakref

from . import gpu_device_lease


class LaunchRefused(ValueError):
    """The requested fixed launch cannot be admitted."""


@dataclasses.dataclass(frozen=True)
class DeviceNode:
    path: str
    major: int
    minor: int


@dataclasses.dataclass(frozen=True)
class DevicePlan:
    host_id: str
    device_uuid: str
    nodes: tuple[DeviceNode, ...]

    def __post_init__(self):
        if (type(self.host_id) is not str
                or gpu_device_lease._HOST.fullmatch(self.host_id) is None
                or type(self.device_uuid) is not str
                or gpu_device_lease._UUID.fullmatch(self.device_uuid) is None
                or type(self.nodes) is not tuple or not 2 <= len(self.nodes) <= 4):
            raise LaunchRefused('invalid device plan')
        paths = []
        for node in self.nodes:
            if (type(node) is not DeviceNode or type(node.path) is not str
                    or type(node.major) is not int or not 0 <= node.major <= 4095
                    or type(node.minor) is not int or not 0 <= node.minor <= 1048575):
                raise LaunchRefused('invalid device node')
            paths.append(node.path)
        gpu = [p for p in paths if re.fullmatch(r'/dev/nvidia(?:0|[1-9][0-9]{0,2})', p)]
        if (len(gpu) != 1 or '/dev/nvidiactl' not in paths or len(set(paths)) != len(paths)
                or any(p not in {gpu[0], '/dev/nvidiactl', '/dev/nvidia-uvm',
                                 '/dev/nvidia-uvm-tools'} for p in paths)):
            raise LaunchRefused('invalid device set')


@dataclasses.dataclass(frozen=True)
class DriverFile:
    path: str
    name: str
    size: int
    sha256: str

    def __post_init__(self):
        if (type(self.path) is not str or not self.path.startswith('/')
                or os.path.normpath(self.path) != self.path or self.path == '/'
                or type(self.name) is not str
                or re.fullmatch(r'(?:libcuda|libnvidia-[a-zA-Z0-9_-]+)\.so\.[a-zA-Z0-9._-]+',
                                self.name) is None
                or type(self.size) is not int or not 1 <= self.size <= 256 * 1024**2
                or type(self.sha256) is not str
                or re.fullmatch(r'[0-9a-f]{64}', self.sha256) is None):
            raise LaunchRefused('invalid driver file')


@dataclasses.dataclass(frozen=True)
class ResourcePolicy:
    address_space: int
    cpu_seconds: int
    wall_seconds: int
    output_bytes: int
    stderr_bytes: int

    def __post_init__(self):
        caps = (2**50, 86400, 86400, 2**30, 2**30)
        if any(type(v) is not int or not 1 <= v <= cap
               for v, cap in zip(dataclasses.astuple(self), caps, strict=True)):
            raise LaunchRefused('invalid resource policy')


def _driver_list(files):
    if (type(files) is not tuple or len(files) > 8
            or any(type(item) is not DriverFile for item in files)
            or len({item.name for item in files}) != len(files)
            or len({item.path for item in files}) != len(files)
            or sum(item.size for item in files) > 1024**3):
        raise LaunchRefused('invalid driver list')
    for item in files:
        DriverFile(item.path, item.name, item.size, item.sha256)
    return files


def _trusted(st):
    import stat

    # Root-owned sticky directories such as /tmp cannot have another user's
    # entries removed or replaced; every subsequent component is checked.
    sticky = st.st_uid == 0 and bool(st.st_mode & stat.S_ISVTX)
    return (st.st_uid in (0, os.geteuid())
            and (not st.st_mode & 0o022 or (stat.S_ISDIR(st.st_mode) and sticky)))


def _open_trusted(path, *, owner, directory=False, character=False):
    """Open each absolute path component without symlink traversal."""

    if (type(path) is not str or not path.startswith('/') or path == '/'
            or os.path.normpath(path) != path or len(os.fsencode(path)) > 4096):
        raise LaunchRefused('invalid path')
    import stat

    parts = path[1:].split('/')
    fd = owner.add(os.open('/', os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC))
    try:
        if not _trusted(os.fstat(fd)):
            raise LaunchRefused('untrusted path')
        protected = False
        for i, part in enumerate(parts):
            flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK
            if i < len(parts) - 1 or directory:
                flags |= os.O_DIRECTORY
            next_fd = owner.add(os.open(part, flags, dir_fd=fd))
            owner.close_fd(fd)
            fd = next_fd
            st = os.fstat(fd)
            device = (character and i == len(parts) - 1 and st.st_uid == 0
                      and stat.S_ISCHR(st.st_mode))
            if (not _trusted(st) and not device
                    and not (protected and st.st_uid in (0, os.geteuid()))):
                raise LaunchRefused('untrusted path')
            if st.st_uid == os.geteuid() and st.st_mode & 0o077 == 0:
                protected = True
        return fd
    except BaseException:
        raise


def _read_fd(fd, maximum):
    import stat

    before = os.fstat(fd)
    if not stat.S_ISREG(before.st_mode) or before.st_size > maximum:
        raise LaunchRefused('invalid file')
    result = bytearray()
    while len(result) <= maximum:
        chunk = os.read(fd, min(65536, maximum + 1 - len(result)))
        if not chunk:
            break
        result.extend(chunk)
    after = os.fstat(fd)
    if (len(result) > maximum or len(result) != before.st_size
            or (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns,
                before.st_ctime_ns) != (after.st_dev, after.st_ino, after.st_size,
                                       after.st_mtime_ns, after.st_ctime_ns)):
        raise LaunchRefused('file changed')
    return bytes(result)


# Strong references keep pending resources reachable even if preparation fails.
_pending = []


class _Owner:
    def __init__(self):
        self.fds = []
        self.directory = None
        self.directory_identity = None
        self.pending = True
        self.unknown_fd = False
        _pending.append(self)

    def add(self, fd):
        self.fds.append((fd, None))
        self.fds[-1] = (fd, _owner_identity(fd))
        return fd

    def close_fd(self, fd):
        matches = [(index, record) for index, record in enumerate(self.fds) if record[0] == fd]
        if len(matches) != 1:
            raise LaunchRefused('descriptor is not owned')
        index, (_, expected) = matches[0]
        previous_unknown = self.unknown_fd
        self.unknown_fd = True
        del self.fds[index]
        if expected is None or _owner_identity(fd) != expected:
            raise LaunchRefused('descriptor ownership unknown')
        os.close(fd)
        self.unknown_fd = previous_unknown

    def cleanup(self):
        import shutil
        import stat

        errors = []
        # A failed close has unknown state; never retry the descriptor number.
        handles, self.fds = self.fds, []
        for fd, expected in reversed(handles):
            try:
                if expected is None or _owner_identity(fd) != expected:
                    raise LaunchRefused('descriptor ownership unknown')
                os.close(fd)
            except BaseException as exc:
                self.unknown_fd = True
                errors.append(exc)
        if self.directory is not None:
            try:
                st = os.lstat(self.directory)
                if (not stat.S_ISDIR(st.st_mode)
                        or (st.st_dev, st.st_ino) != self.directory_identity):
                    raise LaunchRefused('capsule identity changed')
                shutil.rmtree(self.directory)
            except FileNotFoundError:
                self.directory = None
            except BaseException as exc:
                errors.append(exc)
            else:
                self.directory = None
        self.pending = self.unknown_fd or bool(errors) or self.directory is not None
        if not self.pending and self in _pending:
            _pending.remove(self)
        return errors


# The registry binds an exact, unmodifiable capture to its actual owner. It is
# not used to discover which operation failed. Weak keys avoid retaining drained
# captures; _pending independently retains owners with uncertain resources.
_preparation_records = weakref.WeakKeyDictionary()
_preparation_records_lock = threading.Lock()


def _preparation_after_fork():
    # A lock held by a vanished thread must not block a borrower in the child.
    global _preparation_records_lock
    _preparation_records_lock = threading.Lock()


os.register_at_fork(after_in_child=_preparation_after_fork)


class PreparationOwner:
    """Caller-held, one-use association with preparation cleanup state."""

    __slots__ = ('__weakref__',)

    def __init__(self):
        if type(self) is not PreparationOwner:
            raise LaunchRefused('invalid preparation owner')
        with _preparation_records_lock:
            if self in _preparation_records:
                raise LaunchRefused('preparation owner already initialized')
            _preparation_records[self] = [os.getpid(), _Owner(), 'unused', threading.Lock(), None]

    def _record(self):
        if type(self) is not PreparationOwner:
            raise LaunchRefused('invalid preparation owner')
        with _preparation_records_lock:
            record = _preparation_records.get(self)
        if record is None or record[0] != os.getpid():
            raise LaunchRefused('invalid preparation owner')
        return record

    @property
    def pending(self):
        return PreparationOwner._record(self)[1].pending

    @property
    def prepared(self):
        record = PreparationOwner._record(self)
        if not record[3].acquire(blocking=False):
            raise LaunchRefused('preparation owner busy')
        try:
            return record[4] if record[2] == 'handoff' else None
        finally:
            record[3].release()

    def close(self):
        record = PreparationOwner._record(self)
        if not record[3].acquire(blocking=False):
            raise LaunchRefused('preparation owner busy')
        try:
            if record[2] == 'handoff' and record[1].pending:
                raise LaunchRefused('preparation ownership transferred')
            if record[2] == 'unused':
                record[2] = 'closed'
            errors = record[1].cleanup() if record[1].pending else []
            if errors:
                _failure(errors[0], errors[1:])
            if record[1].pending:
                raise LaunchRefused('cleanup remains pending')
        finally:
            record[3].release()


def _failure(original, errors):
    selected = original
    if isinstance(original, Exception):
        selected = next((error for error in errors if not isinstance(error, Exception)), original)
    if isinstance(selected, Exception):
        raise LaunchRefused('launch preparation refused') from None
    raise selected from None


def _close_after(owner, fd):
    # Preserve the body exception even if closing raises a hostile BaseException.
    import sys

    original = sys.exception()
    try:
        owner.close_fd(fd)
    except BaseException as cleanup:
        if original is not None:
            _failure(original, [cleanup])
        raise


def _source_mapping(source_root):
    """Map the finite capsule inventory from an explicit recognized source."""
    from pathlib import Path
    from . import gpu_worker_protocol as wire

    source = Path(source_root)
    if not source.is_absolute() or str(source) != os.path.normpath(str(source)):
        raise LaunchRefused('invalid source root')
    if source.name == 'slaif_raggedized_helper':
        package = source
        lock = wire._profile_path(package)
        if lock != package / '_worker_profiles/gpu/uv.lock':
            raise LaunchRefused('installed package asset required')
    else:
        package = source / 'src/slaif_raggedized_helper'
        lock = wire._profile_path(package)
        if lock != source / 'worker_profiles/gpu/uv.lock':
            raise LaunchRefused('project source required')
    mapping = {f'src/slaif_raggedized_helper/{name}': package / name
               for name in wire.CODE_FILES}
    mapping['worker_profiles/gpu/uv.lock'] = lock
    return mapping


def _copy_capsule(owner, source_root, staging_root, drivers, mapping=None):
    """Copy the finite source set and explicit driver files into a private capsule."""
    import hashlib
    import secrets
    import time
    from pathlib import Path

    from . import gpu_worker_protocol as wire

    root_fd = _open_trusted(staging_root, owner=owner, directory=True)
    try:
        st = os.fstat(root_fd)
        if st.st_uid != os.geteuid() or st.st_mode & 0o077:
            raise LaunchRefused('staging root must be private')
    finally:
        _close_after(owner, root_fd)
    for _ in range(4):
        capsule = os.path.join(staging_root, 'gpu-launch-' + secrets.token_hex(16))
        owner.directory = capsule  # Retain the candidate before creating anything.
        try:
            os.mkdir(capsule, 0o700)
        except FileExistsError:
            owner.directory = None
            continue
        st = os.lstat(capsule)
        owner.directory_identity = (st.st_dev, st.st_ino)
        break
    else:
        raise LaunchRefused('unable to allocate capsule')
    app = Path(capsule) / 'app'
    package = app / 'src' / 'slaif_raggedized_helper'
    package.mkdir(parents=True, mode=0o700)
    lockdir = app / 'worker_profiles' / 'gpu'
    lockdir.mkdir(parents=True, mode=0o700)
    libdir = Path(capsule) / 'driver'
    libdir.mkdir(mode=0o700)
    for directory in (app, app / 'src', package, app / 'worker_profiles', lockdir, libdir):
        directory.chmod(0o700)
    source = Path(source_root)
    snapshots = {}
    if mapping is None:
        mapping = {relative: source / relative for relative in
                   [*(f'src/slaif_raggedized_helper/{name}' for name in wire.CODE_FILES),
                    'worker_profiles/gpu/uv.lock']}
    for relative, path in mapping.items():
        path = str(path)
        fd = _open_trusted(path, owner=owner)
        try:
            initial = os.fstat(fd)
            raw = _read_fd(fd, 65536 if relative.endswith('uv.lock') else 131072)
        finally:
            _close_after(owner, fd)
        snapshots[relative] = (initial.st_dev, initial.st_ino, hashlib.sha256(raw).hexdigest())
        target = app / relative
        target.write_bytes(raw)
        target.chmod(0o400)
    if snapshots['worker_profiles/gpu/uv.lock'][2] != wire.PROFILE_HASH:
        raise LaunchRefused('profile changed')
    (Path(capsule) / 'worker.py').write_bytes(
        (package / 'gpu_embedding_worker_main.py').read_bytes())
    (Path(capsule) / 'worker.py').chmod(0o400)
    deadline = time.monotonic() + 30
    for item in _driver_list(drivers):
        fd = _open_trusted(item.path, owner=owner)
        try:
            digest = hashlib.sha256()
            size = 0
            with (libdir / item.name).open('xb') as target:
                before = os.fstat(fd)
                import stat
                if not stat.S_ISREG(before.st_mode) or before.st_size != item.size:
                    raise LaunchRefused('invalid driver source')
                while True:
                    if time.monotonic() > deadline:
                        raise LaunchRefused('driver copy deadline')
                    block = os.read(fd, min(65536, item.size + 1 - size))
                    if not block:
                        break
                    size += len(block)
                    if size > item.size:
                        raise LaunchRefused('driver too large')
                    digest.update(block)
                    target.write(block)
                after = os.fstat(fd)
                if (size != item.size or digest.hexdigest() != item.sha256
                        or (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns,
                            before.st_ctime_ns) != (after.st_dev, after.st_ino, after.st_size,
                                                   after.st_mtime_ns, after.st_ctime_ns)):
                    raise LaunchRefused('driver changed')
            (libdir / item.name).chmod(0o400)
        finally:
            pass  # The admitted source remains pinned until owner cleanup.
    for relative, expected in snapshots.items():
        fd = _open_trusted(str(mapping[relative]), owner=owner)
        try:
            st = os.fstat(fd)
            raw = _read_fd(fd, 65536 if relative.endswith('uv.lock') else 131072)
        finally:
            _close_after(owner, fd)
        if (st.st_dev, st.st_ino, hashlib.sha256(raw).hexdigest()) != expected:
            raise LaunchRefused('source changed')
    files = {name: hashlib.sha256((package / name).read_bytes()).hexdigest()
             for name in wire.CODE_FILES}
    if any(files[name] != snapshots[f'src/slaif_raggedized_helper/{name}'][2]
           for name in wire.CODE_FILES):
        raise LaunchRefused('capsule copy changed')
    return wire.identity({'api': wire.API, 'schema': wire.SCHEMA, 'files': files}), snapshots


def _reservation(reservation, plan):
    from . import embedding_job_ownership as ownership
    from .schema import fingerprint

    key = fingerprint({'kind': 'gpu-mode-operation-v1', 'host_id': plan.host_id,
                       'device_uuid': plan.device_uuid})
    if (type(reservation) is not ownership.Lease or reservation.owner_pid != os.getpid()
            or reservation.job_id != key):
        raise LaunchRefused('invalid operation reservation')
    reservation.assert_owned()


def _lease_root(path, owner):
    import stat

    fd = _open_trusted(path, owner=owner, directory=True)
    try:
        st = os.fstat(fd)
        if st.st_uid != os.geteuid() or stat.S_IMODE(st.st_mode) != 0o700:
            raise LaunchRefused('invalid lease root')
        found = False
        with os.scandir(fd) as entries:
            for entry in entries:
                if found or entry.name != 'embedding_job_locks':
                    raise LaunchRefused('lease root contains unrelated entries')
                found = True
        if found:
            child = owner.add(os.open('embedding_job_locks', os.O_RDONLY | os.O_DIRECTORY
                                      | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=fd))
            try:
                st = os.fstat(child)
                if st.st_uid != os.geteuid() or stat.S_IMODE(st.st_mode) != 0o700:
                    raise LaunchRefused('invalid lease directory')
                with os.scandir(child) as entries:
                    for count, item in enumerate(entries, 1):
                        if count > 4096:
                            raise LaunchRefused('too many lease files')
                        entry = item.stat(follow_symlinks=False)
                        if (re.fullmatch(r'[0-9a-f]{64}', item.name) is None
                                or not stat.S_ISREG(entry.st_mode)
                                or entry.st_uid != os.geteuid()
                                or stat.S_IMODE(entry.st_mode) != 0o600 or entry.st_nlink != 1
                                or entry.st_size != 0):
                            raise LaunchRefused('invalid lease file')
            finally:
                _close_after(owner, child)
        return fd
    except BaseException:
        raise


def _pin_devices(owner, plan):
    import stat

    result = []
    for node in plan.nodes:
        fd = _open_trusted(node.path, owner=owner, character=True)
        st = os.fstat(fd)
        if (not stat.S_ISCHR(st.st_mode) or os.major(st.st_rdev) != node.major
                or os.minor(st.st_rdev) != node.minor):
            raise LaunchRefused('device identity mismatch')
        result.append((node.path, fd, st.st_dev, st.st_ino, st.st_rdev))
    return tuple(result)


def _owner_identity(fd):
    import stat

    st = os.fstat(fd)
    return (st.st_dev, st.st_ino, stat.S_IFMT(st.st_mode), st.st_rdev)


def _hash_open_file(fd, limit):
    import hashlib
    import time

    before = os.fstat(fd)
    if before.st_size > limit:
        raise LaunchRefused('file too large')
    deadline = time.monotonic() + 30
    digest = hashlib.sha256()
    offset = 0
    while True:
        if time.monotonic() > deadline:
            raise LaunchRefused('file hash deadline')
        block = os.pread(fd, min(65536, limit + 1 - offset), offset)
        if not block:
            break
        offset += len(block)
        if offset > limit:
            raise LaunchRefused('file too large')
        digest.update(block)
    after = os.fstat(fd)
    if (offset != before.st_size or (before.st_dev, before.st_ino, before.st_size,
                                    before.st_mtime_ns, before.st_ctime_ns) !=
            (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns)):
        raise LaunchRefused('file changed')
    return digest.hexdigest()


def _identity(fd):
    st = os.fstat(fd)
    return (st.st_dev, st.st_ino, st.st_mode, st.st_uid, st.st_rdev)


def _capsule_inventory(directory, drivers, owner):
    import hashlib
    import stat
    import time
    from pathlib import Path

    from . import gpu_worker_protocol as wire

    deadline = time.monotonic() + 30
    root = Path(directory)
    expected = {f'app/src/slaif_raggedized_helper/{name}' for name in wire.CODE_FILES}
    expected |= {'app/worker_profiles/gpu/uv.lock', 'worker.py'}
    expected |= {f'driver/{driver.name}' for driver in drivers}
    directories = {'app', 'app/src', 'app/src/slaif_raggedized_helper',
                   'app/worker_profiles', 'app/worker_profiles/gpu', 'driver'}
    found = {}
    found_dirs = set()
    for base, dirs, files in os.walk(root, followlinks=False):
        for name in dirs:
            path = Path(base) / name
            relative = path.relative_to(root).as_posix()
            st = path.lstat()
            if (relative not in directories or not stat.S_ISDIR(st.st_mode)
                    or st.st_uid != os.geteuid() or stat.S_IMODE(st.st_mode) != 0o700):
                raise LaunchRefused('invalid capsule directory')
            found_dirs.add(relative)
        for name in files:
            path = Path(base) / name
            relative = path.relative_to(root).as_posix()
            if relative not in expected:
                raise LaunchRefused('unexpected capsule entry')
            fd = owner.add(os.open(path, os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW
                                   | os.O_NONBLOCK))
            try:
                st = os.fstat(fd)
                limit = next((d.size for d in drivers if relative == f'driver/{d.name}'), 131072)
                if (not stat.S_ISREG(st.st_mode) or st.st_uid != os.geteuid()
                        or stat.S_IMODE(st.st_mode) != 0o400 or st.st_size > limit):
                    raise LaunchRefused('invalid capsule file')
                digest = hashlib.sha256()
                count = 0
                while True:
                    if time.monotonic() > deadline:
                        raise LaunchRefused('capsule hash deadline')
                    block = os.read(fd, 65536)
                    if not block:
                        break
                    count += len(block)
                    if count > limit:
                        raise LaunchRefused('capsule file too large')
                    digest.update(block)
                after = os.fstat(fd)
                if (count != st.st_size or (st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns,
                                            st.st_ctime_ns)
                        != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns,
                            after.st_ctime_ns)):
                    raise LaunchRefused('capsule changed')
                found[relative] = digest.hexdigest()
            finally:
                _close_after(owner, fd)
    if set(found) != expected or found_dirs != directories:
        raise LaunchRefused('incomplete capsule')
    if (found['app/worker_profiles/gpu/uv.lock'] != wire.PROFILE_HASH
            or found['worker.py'] != found['app/src/slaif_raggedized_helper/'
                                           'gpu_embedding_worker_main.py']
            or any(found[f'driver/{d.name}'] != d.sha256 for d in drivers)):
        raise LaunchRefused('capsule content mismatch')
    code = wire.identity({'api': wire.API, 'schema': wire.SCHEMA,
                          'files': {name: found[f'app/src/slaif_raggedized_helper/{name}']
                                    for name in wire.CODE_FILES}})
    return code, found


def _fixed_argv(policy, device, descriptors):
    """Construct the only supported command, with descriptor-pinned mounts."""
    def source(key):
        return f'/proc/self/fd/{descriptors[key]}'

    argv = ['/usr/bin/prlimit', f'--as={policy.address_space}', f'--cpu={policy.cpu_seconds}',
            '--nofile=128', f'--fsize={max(policy.output_bytes, policy.stderr_bytes)}',
            '/usr/bin/timeout', '--signal=TERM', '--kill-after=2', str(policy.wall_seconds),
            '/usr/bin/bwrap', '--unshare-user', '--unshare-pid', '--unshare-net',
            '--unshare-ipc', '--unshare-uts', '--die-with-parent', '--new-session', '--clearenv',
            '--proc', '/proc', '--dev', '/dev', '--tmpfs', '/tmp', '--chdir', '/tmp',
            '--ro-bind', '/usr/lib/x86_64-linux-gnu', '/usr/lib/x86_64-linux-gnu',
            '--ro-bind', '/usr/lib64', '/usr/lib64', '--symlink', 'usr/lib', '/lib',
            '--symlink', 'usr/lib64', '/lib64']
    for key, destination in (('runtime', '/python'), ('packages', '/packages'),
                             ('app', '/app'), ('artifacts', '/artifacts'),
                             ('driver', '/driver/lib'), ('worker', '/worker.py'),
                             ('lock', '/profile.lock'), ('python', '/python/bin/python3.12')):
        argv += ['--ro-bind', source(key), destination]
    argv += ['--bind', source('lease'), '/lease']
    for index, node in enumerate(device.nodes):
        argv += ['--dev-bind', source(f'device{index}'), node.path]
    env = {'PYTHONPATH': '/packages:/app/src', 'PYTHONDONTWRITEBYTECODE': '1',
           'TOKENIZERS_PARALLELISM': 'false', 'HF_HUB_OFFLINE': '1',
           'TRANSFORMERS_OFFLINE': '1', 'HF_DATASETS_OFFLINE': '1',
           'OPENBLAS_NUM_THREADS': '1', 'OMP_NUM_THREADS': '1', 'MKL_NUM_THREADS': '1',
           'RAYON_NUM_THREADS': '1', 'NUMEXPR_NUM_THREADS': '1', 'HOME': '/tmp',
           'CUDA_VISIBLE_DEVICES': device.device_uuid, 'LD_LIBRARY_PATH': '/driver/lib'}
    for key, value in env.items():
        argv += ['--setenv', key, value]
    return tuple(argv + ['/python/bin/python3.12', '-I', '-S', '/worker.py'])


class PreparedLaunch:
    """Own pinned descriptors and capsule until a future parent confirms child drain.

    Closing this object is not evidence of GPU vacancy.  The caller retains the
    operation reservation and protected artifact tree throughout that lifetime.
    """

    def __init__(self, owner, plan, resource, reservation, descriptors, identities,
                 capsule_files, code_id, profile_id, startup, plan_id, recheck):
        self._owner = owner
        self._device = plan
        self._resource = resource
        self._reservation = reservation
        self._descriptors = descriptors
        self._identities = identities
        self._capsule_files = capsule_files
        self.code_id = code_id
        self.profile_id = profile_id
        self.startup = startup
        self.plan_id = plan_id
        self._recheck = recheck
        self._guard = (owner, reservation, recheck, recheck['admit'], recheck['drivers'],
                       tuple(recheck['bindings'].items()), type(self).revalidate,
                       type(self).launch_arguments, type(self).close)
        self._pid = os.getpid()
        self._closed = False
        self._argv = _fixed_argv(resource, plan, descriptors)
        self._snapshot = (dataclasses.astuple(plan), dataclasses.astuple(resource),
                          dict(descriptors), dict(identities), dict(capsule_files),
                          code_id, profile_id, startup, plan_id, self._argv)

    @property
    def pending(self):
        return self._owner.pending

    def revalidate(self):
        if self._closed or self._pid != os.getpid():
            raise LaunchRefused('launch owner is not live')
        guard = (self._owner, self._reservation, self._recheck, self._recheck['admit'],
                 self._recheck['drivers'], tuple(self._recheck['bindings'].items()),
                 type(self).revalidate, type(self).launch_arguments, type(self).close)
        if guard != self._guard:
            raise LaunchRefused('launch owner changed')
        _reservation(self._reservation, self._device)
        snapshot = (dataclasses.astuple(self._device), dataclasses.astuple(self._resource),
                    dict(self._descriptors), dict(self._identities), dict(self._capsule_files),
                    self.code_id, self.profile_id, self.startup, self.plan_id, self._argv)
        if snapshot != self._snapshot:
            raise LaunchRefused('prepared plan changed')
        if any(_identity(fd) != self._identities[name] for name, fd in self._descriptors.items()):
            raise LaunchRefused('mount descriptor changed')
        code, files = _capsule_inventory(self._owner.directory, self._recheck['drivers'],
                                         self._owner)
        if code != self.code_id or files != self._capsule_files:
            raise LaunchRefused('capsule changed')
        if any(globals().get(name) is not value
               for name, value in self._recheck['bindings'].items()):
            raise LaunchRefused('launch module changed')
        self._recheck['admit']()
        _reservation(self._reservation, self._device)

    def launch_arguments(self):
        """Return fixed argv and descriptors; caller must retain this owner until drain."""
        self.revalidate()
        return self._argv, tuple(self._descriptors.values())

    def close(self):
        if self._pid != os.getpid():
            raise LaunchRefused('foreign process cannot close owner')
        if self._closed:
            if self._owner.pending:
                errors = self._owner.cleanup()
                if errors:
                    _failure(errors[0], errors[1:])
                if self._owner.pending:
                    raise LaunchRefused('cleanup remains pending')
            return
        self._closed = True
        errors = self._owner.cleanup()
        if errors:
            _failure(errors[0], errors[1:])
        if self._owner.pending:
            raise LaunchRefused('cleanup remains pending')


def prepare(*, source_root, staging_root, runtime_root, packages_root, artifact_root,
            lease_root, manifest, definition, tokenizer, inventory_id, device, drivers,
            resource, wire_policy, reservation, preparation_owner=None):
    """Prepare with an optional caller-retained cleanup association."""
    record = None
    if preparation_owner is not None:
        record = PreparationOwner._record(preparation_owner)
        if not record[3].acquire(blocking=False):
            raise LaunchRefused('preparation owner busy')
        if record[2] != 'unused':
            record[3].release()
            raise LaunchRefused('preparation owner already used')
        record[2] = 'busy'
    try:
        result = _prepare_impl(source_root=source_root, staging_root=staging_root,
                               runtime_root=runtime_root, packages_root=packages_root,
                               artifact_root=artifact_root, lease_root=lease_root,
                               manifest=manifest, definition=definition, tokenizer=tokenizer,
                               inventory_id=inventory_id, device=device, drivers=drivers,
                               resource=resource, wire_policy=wire_policy,
                               reservation=reservation, owner=record[1] if record else None)
        if record is not None:
            record[4] = result
            record[2] = 'handoff'
        return result
    finally:
        if record is not None:
            if record[2] == 'busy':
                record[2] = 'failed'
            record[3].release()


def _prepare_impl(*, source_root, staging_root, runtime_root, packages_root, artifact_root,
                  lease_root, manifest, definition, tokenizer, inventory_id, device, drivers,
                  resource, wire_policy, reservation, owner):
    """Prepare only; no process is created and no GPU authorization is implied."""
    import secrets
    import stat
    from pathlib import Path

    from . import embedding_artifacts, embedding_space, gpu_worker_protocol as wire
    from .cpu_embedding_backend import _closed_tree
    from .schema import EmbeddingDefinition

    if owner is None:
        owner = _Owner()
    try:
        if (type(device) is not DevicePlan or type(resource) is not ResourcePolicy
                or type(wire_policy) is not wire.Policy or type(manifest) is not bytes
                or type(definition) is not EmbeddingDefinition):
            raise LaunchRefused('invalid preparation arguments')
        DevicePlan(device.host_id, device.device_uuid, device.nodes)
        ResourcePolicy(*dataclasses.astuple(resource))
        wire.Policy(*dataclasses.astuple(wire_policy))
        _driver_list(drivers)
        _reservation(reservation, device)
        descriptors = {}
        for key, path in (('runtime', runtime_root), ('packages', packages_root),
                          ('artifacts', artifact_root)):
            descriptors[key] = _open_trusted(path, owner=owner, directory=True)
        descriptors['lease'] = _lease_root(lease_root, owner)
        mapping = _source_mapping(source_root)
        lock_path = mapping['worker_profiles/gpu/uv.lock']
        source_lock = _open_trusted(str(lock_path), owner=owner)
        if _hash_open_file(source_lock, 65536) != wire.PROFILE_HASH:
            raise LaunchRefused('profile changed')
        profile = wire.profile(lock_path, Path(packages_root))
        admitted = embedding_space.admit(manifest, Path(artifact_root), definition, tokenizer,
                                         inventory_id)
        inventory = embedding_artifacts.verify_artifacts(manifest, Path(artifact_root))
        _closed_tree(Path(artifact_root), inventory.files)
        code_id, source_snapshots = _copy_capsule(
            owner, source_root, staging_root, drivers, mapping)
        actual_code, capsule_files = _capsule_inventory(owner.directory, drivers, owner)
        if code_id != actual_code:
            raise LaunchRefused('code identity mismatch')
        module_fd = owner.add(os.open(__file__, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC))
        module_hash = _hash_open_file(module_fd, 1024 * 1024)
        for key, path in (('app', owner.directory + '/app'),
                          ('driver', owner.directory + '/driver')):
            descriptors[key] = _open_trusted(path, owner=owner, directory=True)
        for key, path in (('worker', owner.directory + '/worker.py'),
                          ('lock', owner.directory + '/app/worker_profiles/gpu/uv.lock')):
            descriptors[key] = _open_trusted(path, owner=owner)
        executable = _open_trusted(runtime_root + '/bin/python3.12', owner=owner)
        st = os.fstat(executable)
        if not stat.S_ISREG(st.st_mode) or not st.st_mode & 0o111:
            raise LaunchRefused('invalid Python runtime')
        descriptors['python'] = executable
        runtime_hash = _hash_open_file(executable, 128 * 1024**2)
        pins = _pin_devices(owner, device)
        for index, (_, fd, _, _, _) in enumerate(pins):
            descriptors[f'device{index}'] = fd
        if any(fd >= 128 for fd in descriptors.values()):
            raise LaunchRefused('descriptor exceeds child limit')
        identities = {key: _identity(fd) for key, fd in descriptors.items()}
        startup = wire.encode({'schema': wire.SCHEMA, 'api': wire.API,
                               'startup_nonce': secrets.token_hex(16),
                               'manifest': manifest.decode('utf-8', 'strict'),
                               'definition': definition.model_dump(mode='json'),
                               'tokenizer': {'sha256': tokenizer.sha256,
                                             'backend_version': tokenizer.backend_version,
                                             'role': tokenizer.role,
                                             'model_revision': tokenizer.model_revision,
                                             'preprocessing': tokenizer.preprocessing},
                               'inventory': inventory_id, 'space': admitted.space_id,
                               'profile': profile, 'policy': dataclasses.asdict(wire_policy),
                               'policy_id': wire.policy_id(wire_policy), 'code_id': code_id,
                               'host': device.host_id, 'device_uuid': device.device_uuid})
        frame_size = len(startup) + 1
        if (frame_size > 2 * 1024**2 or frame_size > wire_policy.request_bytes
                or frame_size > wire_policy.total_input_bytes):
            raise LaunchRefused('startup frame exceeds policy')
        plan_id = wire.identity({'device': dataclasses.asdict(device),
                                 'drivers': [dataclasses.asdict(d) for d in drivers],
                                 'resource': dataclasses.asdict(resource),
                                 'wire_policy': dataclasses.asdict(wire_policy),
                                 'mounts': identities, 'source': source_snapshots,
                                 'source_layout': {key: str(value)
                                                   for key, value in mapping.items()},
                                 'profile': profile, 'code': code_id, 'space': admitted.space_id,
                                 'runtime_sha256': runtime_hash,
                                 'launch_module_sha256': module_hash})

        policy_snapshot = wire.policy_id(wire_policy)
        drivers_snapshot = wire.encode([dataclasses.asdict(item) for item in drivers])
        module_bindings = {name: globals()[name] for name in
                           ('_fixed_argv', '_pin_devices', '_capsule_inventory', '_reservation',
                            '_source_mapping',
                            '_open_trusted', '_lease_root', '_identity', '_hash_open_file',
                            '_read_fd', 'PreparedLaunch')}

        def admit_again():
            import hashlib

            if (wire.policy_id(wire_policy) != policy_snapshot
                    or wire.encode([dataclasses.asdict(item) for item in drivers])
                    != drivers_snapshot):
                raise LaunchRefused('policy or drivers changed')
            if _hash_open_file(module_fd, 1024 * 1024) != module_hash:
                raise LaunchRefused('launch module changed')
            if _hash_open_file(executable, 128 * 1024**2) != runtime_hash:
                raise LaunchRefused('runtime changed')

            for relative, expected in source_snapshots.items():
                fd = _open_trusted(str(mapping[relative]), owner=owner)
                try:
                    st = os.fstat(fd)
                    raw = _read_fd(fd, 65536 if relative.endswith('uv.lock') else 131072)
                finally:
                    _close_after(owner, fd)
                if (st.st_dev, st.st_ino, hashlib.sha256(raw).hexdigest()) != expected:
                    raise LaunchRefused('source changed')
            if _source_mapping(source_root) != mapping:
                raise LaunchRefused('source layout changed')
            current_profile = wire.profile(lock_path, Path(packages_root))
            current = embedding_space.admit(manifest, Path(artifact_root), definition, tokenizer,
                                            inventory_id)
            current_inventory = embedding_artifacts.verify_artifacts(manifest, Path(artifact_root))
            _closed_tree(Path(artifact_root), current_inventory.files)
            lease_fd = _lease_root(lease_root, owner)
            try:
                if _identity(lease_fd) != identities['lease']:
                    raise LaunchRefused('lease root changed')
            finally:
                _close_after(owner, lease_fd)
            if current != admitted or current_profile != profile:
                raise LaunchRefused('admission changed')

        prepared = PreparedLaunch(owner, device, resource, reservation, descriptors, identities,
                                  capsule_files, code_id, profile, startup, plan_id,
                                  {'drivers': drivers, 'admit': admit_again,
                                   'bindings': module_bindings})
        prepared.revalidate()
        return prepared
    except BaseException as exc:
        errors = owner.cleanup()
        _failure(exc, errors)
