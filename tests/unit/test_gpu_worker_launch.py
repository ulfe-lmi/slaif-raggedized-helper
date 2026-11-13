"""Admission boundary tests, without GPU or driver access."""

import dataclasses
import os

import pytest

from slaif_raggedized_helper import gpu_worker_launch as launch


HOST = 'a' * 64
UUID = 'GPU-12345678-1234-1234-1234-123456789abc'


def test_device_plan_rejects_extra_duplicate_and_unbounded_nodes():
    gpu = launch.DeviceNode('/dev/nvidia0', 195, 0)
    ctl = launch.DeviceNode('/dev/nvidiactl', 195, 255)
    plan = launch.DevicePlan(HOST, UUID, (gpu, ctl))
    assert plan.nodes == (gpu, ctl)
    for nodes in ((gpu, ctl, gpu), (gpu,), (gpu, ctl, launch.DeviceNode('/dev', 1, 1)),
                  (launch.DeviceNode('/dev/nvidia00', 1, 1), ctl)):
        with pytest.raises(launch.LaunchRefused):
            launch.DevicePlan(HOST, UUID, nodes)
    with pytest.raises(dataclasses.FrozenInstanceError):
        plan.host_id = 'b' * 64


def test_driver_and_policy_bounds():
    good = launch.DriverFile('/driver/libcuda.so.1', 'libcuda.so.1', 12, 'b' * 64)
    assert launch._driver_list((good,)) == (good,)
    with pytest.raises(launch.LaunchRefused):
        launch._driver_list((good, good))
    with pytest.raises(launch.LaunchRefused):
        launch.DriverFile('/driver/x', '../libcuda.so.1', 1, 'b' * 64)
    assert launch.ResourcePolicy(2**30, 30, 120, 1000, 1000).cpu_seconds == 30
    with pytest.raises(launch.LaunchRefused):
        launch.ResourcePolicy(True, 30, 120, 1000, 1000)


def test_trusted_open_rejects_symlink_and_reads_pinned_inode(tmp_path):
    source = tmp_path / 'source'
    source.write_bytes(b'original')
    source.chmod(0o600)
    owner = launch._Owner()
    fd = launch._open_trusted(str(source), owner=owner)
    try:
        source.rename(tmp_path / 'old')
        source.write_bytes(b'replacement')
        assert launch._read_fd(fd, 64) == b'original'
    finally:
        owner.close_fd(fd)
    (tmp_path / 'link').symlink_to(source)
    with pytest.raises(OSError):
        launch._open_trusted(str(tmp_path / 'link'), owner=owner)
    assert owner.cleanup() == []


def test_capsule_exact_sources_and_cleanup(tmp_path):
    import hashlib
    import shutil
    from pathlib import Path

    from slaif_raggedized_helper import gpu_worker_protocol as wire

    source = tmp_path / 'source'
    package = source / 'src' / 'slaif_raggedized_helper'
    package.mkdir(parents=True)
    lock = source / 'worker_profiles' / 'gpu' / 'uv.lock'
    lock.parent.mkdir(parents=True)
    checkout = Path(__file__).resolve().parents[2]
    for name in wire.CODE_FILES:
        shutil.copyfile(checkout / 'src' / 'slaif_raggedized_helper' / name, package / name)
        (package / name).chmod(0o600)
    shutil.copyfile(checkout / 'worker_profiles' / 'gpu' / 'uv.lock', lock)
    lock.chmod(0o600)
    for directory in (source, source / 'src', package, source / 'worker_profiles', lock.parent):
        directory.chmod(0o700)
    stage = tmp_path / 'stage'
    stage.mkdir(mode=0o700)
    owner = launch._Owner()
    try:
        code_id, snapshots = launch._copy_capsule(owner, str(source), str(stage), ())
        assert code_id == wire.code_id()
        assert len(snapshots) == 13
        capsule = Path(owner.directory)
        names = {p.name for p in (capsule / 'app' / 'src' / 'slaif_raggedized_helper').iterdir()}
        assert names == set(wire.CODE_FILES)
        assert hashlib.sha256((capsule / 'worker.py').read_bytes()).digest() == hashlib.sha256(
            (package / 'gpu_embedding_worker_main.py').read_bytes()).digest()
    finally:
        assert owner.cleanup() == []
    assert not capsule.exists()
    assert owner not in launch._pending


def test_real_operation_reservation_and_dedicated_lease_root(tmp_path):
    from slaif_raggedized_helper import embedding_job_ownership as ownership
    from slaif_raggedized_helper.schema import fingerprint

    plan = launch.DevicePlan(HOST, UUID, (launch.DeviceNode('/dev/nvidia0', 195, 0),
                                          launch.DeviceNode('/dev/nvidiactl', 195, 255)))
    root = tmp_path / 'owner'
    root.mkdir(mode=0o700)
    key = fingerprint({'kind': 'gpu-mode-operation-v1', 'host_id': HOST, 'device_uuid': UUID})
    reservation = ownership.claim(root, key)
    lease = tmp_path / 'lease'
    lease.mkdir(mode=0o700)
    try:
        launch._reservation(reservation, plan)
        with pytest.raises(launch.LaunchRefused):
            launch._reservation(object(), plan)
        owner = launch._Owner()
        fd = launch._lease_root(str(lease), owner)
        owner.close_fd(fd)
        (lease / 'unrelated').write_text('x')
        with pytest.raises(launch.LaunchRefused):
            launch._lease_root(str(lease), owner)
        assert owner.cleanup() == []
        reservation.assert_owned()
    finally:
        reservation.close()


def _prepared_fixture(tmp_path, monkeypatch):
    import shutil
    from pathlib import Path

    from slaif_raggedized_helper import embedding_job_ownership as ownership
    from slaif_raggedized_helper import gpu_worker_protocol as wire
    from slaif_raggedized_helper.schema import fingerprint
    from test_gpu_embedding_backend import make_tree

    checkout = Path(__file__).resolve().parents[2]
    source = tmp_path / 'source'
    package = source / 'src' / 'slaif_raggedized_helper'
    package.mkdir(parents=True)
    lock = source / 'worker_profiles' / 'gpu' / 'uv.lock'
    lock.parent.mkdir(parents=True)
    for name in wire.CODE_FILES:
        shutil.copyfile(checkout / 'src' / 'slaif_raggedized_helper' / name, package / name)
    shutil.copyfile(checkout / 'worker_profiles' / 'gpu' / 'uv.lock', lock)
    shutil.copyfile(checkout / 'pyproject.toml', source / 'pyproject.toml')
    stage, lease, reservation_dir = (tmp_path / name for name in ('stage', 'lease', 'reservation'))
    for directory in (stage, lease, reservation_dir):
        directory.mkdir(mode=0o700)
    raw, inventory, definition, tokenizer = make_tree(tmp_path / 'artifacts')
    key = fingerprint({'kind': 'gpu-mode-operation-v1', 'host_id': HOST, 'device_uuid': UUID})
    reservation = ownership.claim(reservation_dir, key)
    plan = launch.DevicePlan(HOST, UUID, (launch.DeviceNode('/dev/nvidia0', 195, 0),
                                         launch.DeviceNode('/dev/nvidiactl', 195, 255)))

    def null_pins(owner, device):
        pins = []
        for node in device.nodes:
            fd = owner.add(os.open('/dev/null', os.O_RDONLY | os.O_CLOEXEC))
            st = os.fstat(fd)
            pins.append((node.path, fd, st.st_dev, st.st_ino, st.st_rdev))
        return tuple(pins)

    monkeypatch.setattr(launch, '_pin_devices', null_pins)
    args = dict(source_root=str(source), staging_root=str(stage),
                runtime_root=os.environ['SLAIF_GPU_TEST_ROOT'],
                packages_root=os.environ['SLAIF_GPU_TEST_PACKAGES'],
                artifact_root=str(tmp_path / 'artifacts'), lease_root=str(lease), manifest=raw,
                definition=definition, tokenizer=tokenizer, inventory_id=inventory.inventory_id,
                device=plan, drivers=(), resource=launch.ResourcePolicy(2**30, 30, 120,
                                                                        8 * 1024**2, 65536),
                wire_policy=wire.Policy(calls=2), reservation=reservation)
    return args, reservation


def test_prepared_argv_and_mutation_rejection(tmp_path, monkeypatch):
    from pathlib import Path

    args, reservation = _prepared_fixture(tmp_path, monkeypatch)
    try:
        prepared = launch.prepare(**args)
        try:
            argv, fds = prepared.launch_arguments()
            assert argv[:2] == ('/usr/bin/prlimit', '--as=1073741824')
            assert '--unshare-net' in argv and '--unshare-pid' in argv and '--clearenv' in argv
            assert '--share-net' not in argv and len(fds) == 11
            assert argv[-4:] == ('/python/bin/python3.12', '-I', '-S', '/worker.py')
            assert len(prepared.plan_id) == 64
            path = Path(prepared._owner.directory) / 'app/src/slaif_raggedized_helper/schema.py'
            path.chmod(0o600)
            path.write_bytes(path.read_bytes() + b'\n')
            with pytest.raises(launch.LaunchRefused):
                prepared.launch_arguments()
        finally:
            prepared.close()
        reservation.assert_owned()
    finally:
        reservation.close()


@pytest.mark.parametrize('mutation', ['module', 'source', 'lease', 'policy', 'capsule_extra',
                                     'artifact', 'profile'])
def test_revalidation_rejects_changes(tmp_path, monkeypatch, mutation):
    from pathlib import Path

    args, reservation = _prepared_fixture(tmp_path, monkeypatch)
    prepared = launch.prepare(**args)
    try:
        prepared.launch_arguments()
        if mutation == 'module':
            monkeypatch.setattr(launch, '_fixed_argv', lambda *args: ())
        elif mutation == 'source':
            source = Path(args['source_root']) / 'src/slaif_raggedized_helper/schema.py'
            source.write_bytes(source.read_bytes() + b'\n')
        elif mutation == 'lease':
            (Path(args['lease_root']) / 'extra').write_text('x')
        elif mutation == 'policy':
            object.__setattr__(prepared._resource, 'cpu_seconds', 31)
        elif mutation == 'capsule_extra':
            (Path(prepared._owner.directory) / 'app/extra.py').write_text('pass')
        elif mutation == 'artifact':
            (Path(args['artifact_root']) / 'tokenizer.json').write_bytes(b'bad')
        else:
            lock = Path(args['source_root']) / 'worker_profiles/gpu/uv.lock'
            lock.write_bytes(b'bad')
        with pytest.raises((launch.LaunchRefused, ValueError)):
            prepared.launch_arguments()
    finally:
        prepared.close()
        reservation.close()


def test_cleanup_never_retries_an_uncertain_descriptor(monkeypatch):
    owner = launch._Owner()
    fd = owner.add(os.open('/dev/null', os.O_RDONLY))
    close = os.close
    attempts = []

    def uncertain(number):
        if number == fd:
            attempts.append(number)
            raise KeyboardInterrupt()
        close(number)

    monkeypatch.setattr(os, 'close', uncertain)
    try:
        errors = owner.cleanup()
        assert len(errors) == 1 and isinstance(errors[0], KeyboardInterrupt)
        assert owner.pending and owner in launch._pending
        assert owner.cleanup() == []
        assert attempts == [fd] and owner.pending
    finally:
        close(fd)
        launch._pending.remove(owner)


def test_failure_priority_does_not_use_exception_diagnostics():
    class Hostile(BaseException):
        def __setattr__(self, name, value):
            raise RuntimeError('diagnostics forbidden')

    original = Hostile()
    with pytest.raises(Hostile) as caught:
        launch._failure(original, [KeyboardInterrupt()])
    assert caught.value is original
    interrupt = Hostile()
    with pytest.raises(Hostile) as caught:
        launch._failure(ValueError(), [interrupt])
    assert caught.value is interrupt


def test_real_device_pin_checks_rdev_with_private_null_facade(monkeypatch):
    original_open = os.open

    def fake_open(path, **kwargs):
        assert path in ('/dev/nvidia0', '/dev/nvidiactl')
        return kwargs['owner'].add(original_open('/dev/null', os.O_RDONLY | os.O_CLOEXEC))

    monkeypatch.setattr(launch, '_open_trusted', fake_open)
    plan = launch.DevicePlan(HOST, UUID, (launch.DeviceNode('/dev/nvidia0', 1, 3),
                                         launch.DeviceNode('/dev/nvidiactl', 1, 3)))
    owner = launch._Owner()
    try:
        pins = launch._pin_devices(owner, plan)
        assert len(pins) == 2 and all(os.fstat(pin[1]).st_rdev == os.makedev(1, 3)
                                      for pin in pins)
    finally:
        assert owner.cleanup() == []
    bad = launch.DevicePlan(HOST, UUID, (launch.DeviceNode('/dev/nvidia0', 1, 4),
                                        launch.DeviceNode('/dev/nvidiactl', 1, 3)))
    owner = launch._Owner()
    try:
        with pytest.raises(launch.LaunchRefused):
            launch._pin_devices(owner, bad)
    finally:
        assert owner.cleanup() == []


def test_synthetic_driver_copy_hash_and_source_pin(tmp_path, monkeypatch):
    import hashlib
    from pathlib import Path

    args, reservation = _prepared_fixture(tmp_path, monkeypatch)
    source = tmp_path / 'fake-library'
    source.write_bytes(b'synthetic driver bytes; no real driver')
    driver = launch.DriverFile(str(source), 'libcuda.so.1', source.stat().st_size,
                               hashlib.sha256(source.read_bytes()).hexdigest())
    args['drivers'] = (driver,)
    prepared = None
    try:
        prepared = launch.prepare(**args)
        copied = Path(prepared._owner.directory) / 'driver/libcuda.so.1'
        assert copied.read_bytes() == source.read_bytes()
        assert any(os.fstat(fd).st_ino == source.stat().st_ino for fd, _ in prepared._owner.fds)
        prepared.launch_arguments()
    finally:
        if prepared is not None:
            prepared.close()
        reservation.close()


@pytest.mark.parametrize('target', ['device', 'resource', 'wire', 'driver'])
def test_prepare_rejects_frozen_object_guard_bypass(tmp_path, monkeypatch, target):
    args, reservation = _prepared_fixture(tmp_path, monkeypatch)
    try:
        prepared = launch.prepare(**args)
        prepared.launch_arguments()
        prepared.close()
        if target == 'device':
            object.__setattr__(args['device'].nodes[0], 'path', '/dev')
        elif target == 'resource':
            object.__setattr__(args['resource'], 'wall_seconds', 0)
        elif target == 'wire':
            object.__setattr__(args['wire_policy'], 'calls', 0)
        else:
            driver = launch.DriverFile('/fake', 'libcuda.so.1', 1, 'a' * 64)
            object.__setattr__(driver, 'name', '../escape')
            args['drivers'] = (driver,)
        with pytest.raises(launch.LaunchRefused):
            launch.prepare(**args)
        reservation.assert_owned()
    finally:
        reservation.close()


def test_cleanup_refuses_reused_foreign_descriptor(tmp_path):
    owner = launch._Owner()
    old = owner.add(os.open('/dev/null', os.O_RDONLY))
    os.close(old)
    other = tmp_path / 'foreign'
    other.write_bytes(b'foreign')
    fd = os.open(other, os.O_RDONLY)
    try:
        assert fd == old
        errors = owner.cleanup()
        assert errors and owner.pending
        assert os.read(fd, 7) == b'foreign'
        assert owner.cleanup() == [] and owner.pending
    finally:
        os.close(fd)
        launch._pending.remove(owner)


def test_close_after_preserves_original_interrupt():
    class BodyInterrupt(BaseException):
        pass

    class CleanupInterrupt(BaseException):
        pass

    class Owner:
        def close_fd(self, fd):
            raise CleanupInterrupt()

    body = BodyInterrupt()
    with pytest.raises(BodyInterrupt) as caught:
        try:
            raise body
        finally:
            launch._close_after(Owner(), 1)
    assert caught.value is body
    with pytest.raises(CleanupInterrupt):
        try:
            raise ValueError()
        finally:
            launch._close_after(Owner(), 1)


@pytest.mark.parametrize('state', ['open', 'closed', 'pending'])
def test_forked_close_refuses_before_every_state_branch(tmp_path, monkeypatch, state):
    import shutil
    import signal
    import time
    from pathlib import Path

    args, reservation = _prepared_fixture(tmp_path, monkeypatch)
    prepared = launch.prepare(**args)
    prepared.launch_arguments()
    capsule = Path(prepared._owner.directory)
    original_rmtree = shutil.rmtree
    try:
        if state == 'closed':
            prepared.close()
            assert not capsule.exists()
        elif state == 'pending':
            def refuse(*args, **kwargs):
                raise OSError('controlled cleanup failure')

            monkeypatch.setattr(shutil, 'rmtree', refuse)
            with pytest.raises(launch.LaunchRefused):
                prepared.close()
            assert prepared.pending and capsule.exists()
            monkeypatch.setattr(shutil, 'rmtree', original_rmtree)
        else:
            assert capsule.exists()
        child = os.fork()
        if child == 0:
            signal.alarm(5)
            try:
                prepared.close()
            except launch.LaunchRefused:
                os._exit(23)
            os._exit(0)
        deadline = time.monotonic() + 6
        while True:
            pid, status = os.waitpid(child, os.WNOHANG)
            if pid:
                break
            if time.monotonic() >= deadline:
                os.kill(child, signal.SIGKILL)
                os.waitpid(child, 0)
                pytest.fail('owned fork did not exit')
            time.sleep(0.01)
        assert os.waitstatus_to_exitcode(status) == 23
        assert capsule.exists() == (state != 'closed')
        reservation.assert_owned()
        if state == 'open':
            prepared.launch_arguments()
        prepared.close()
        assert not capsule.exists()
        reservation.assert_owned()
    finally:
        monkeypatch.setattr(shutil, 'rmtree', original_rmtree)
        prepared.close()
        reservation.close()


def test_startup_frame_exact_boundary_and_original_tiny_cap_bypass(tmp_path, monkeypatch):
    from slaif_raggedized_helper import gpu_worker_protocol as wire

    args, reservation = _prepared_fixture(tmp_path, monkeypatch)
    try:
        positive = launch.prepare(**args)
        size = len(positive.startup) + 1
        assert size > 1
        positive.launch_arguments()
        positive.close()
        args['wire_policy'] = wire.Policy(calls=2, request_bytes=size, total_input_bytes=size)
        provisional = launch.prepare(**args)
        size = len(provisional.startup) + 1
        provisional.close()
        args['wire_policy'] = wire.Policy(calls=2, request_bytes=size, total_input_bytes=size)
        exact = launch.prepare(**args)
        try:
            assert len(exact.startup) + 1 == size
            exact.launch_arguments()
        finally:
            exact.close()
        for policy in (wire.Policy(request_bytes=1, total_input_bytes=1),
                       wire.Policy(request_bytes=size - 1, total_input_bytes=size),
                       wire.Policy(request_bytes=size, total_input_bytes=size - 1)):
            args['wire_policy'] = policy
            with pytest.raises(launch.LaunchRefused):
                launch.prepare(**args)
        reservation.assert_owned()
    finally:
        reservation.close()
