import importlib.util
import json
from pathlib import Path
import sys

import pytest

PATH = Path(__file__).resolve().parents[1] / 'support/real_cpu_toy_probe.py'
spec = importlib.util.spec_from_file_location('real_cpu_toy_probe', PATH)
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


def test_plan_without_framework_import():
    result = probe.run_bounded([sys.executable, str(PATH), '--plan'], {}, 5)
    plan = json.loads(result)
    assert plan['purpose'] == 'random-cpu-toy-only'
    assert plan['limits'] == probe.LIMITS
    assert 'torch' not in sys.modules and 'transformers' not in sys.modules


def permit(tmp_path):
    p = tmp_path / 'permit.json'
    value = {'schema': 1, 'purpose': 'random-cpu-toy-only', 'head': probe.head(),
             'sources': probe.source_hashes(), 'runtime': str(probe.RUNTIME),
             'packages': str(probe.PACKAGES), 'lock_sha256': probe.LOCK,
             'framework_pins': probe.PINS, 'limits': probe.LIMITS}
    p.write_text(json.dumps(value))
    p.chmod(0o600)
    return p, value


def test_permit_closed_and_bound(tmp_path):
    p, value = permit(tmp_path)
    assert probe.permit_check(p, probe.RUNTIME, probe.PACKAGES) == value
    for key in ('head', 'sources', 'limits', 'runtime'):
        changed = dict(value, **{key: 'wrong'})
        p.write_text(json.dumps(changed))
        with pytest.raises(ValueError):
            probe.permit_check(p, probe.RUNTIME, probe.PACKAGES)
    p.write_text('{"schema":1,"schema":1}')
    with pytest.raises(ValueError):
        probe.permit_check(p, probe.RUNTIME, probe.PACKAGES)
    p.write_text(json.dumps(value))
    p.chmod(0o644)
    with pytest.raises(ValueError):
        probe.permit_check(p, probe.RUNTIME, probe.PACKAGES)
    p.chmod(0o600)
    link = tmp_path / 'link'
    link.symlink_to(p)
    with pytest.raises(OSError):
        probe.permit_check(link, probe.RUNTIME, probe.PACKAGES)


def test_capture_limits_and_failures():
    assert probe.run_bounded([sys.executable, '-c', 'print("ok")'], {}, 5) == b'ok\n'
    with pytest.raises(ValueError, match='output limit'):
        probe.run_bounded([sys.executable, '-c', 'print("x" * 101)'], {}, 5, 100)
    with pytest.raises(ValueError, match='child failed'):
        probe.run_bounded([sys.executable, '-c', 'raise SystemExit(1)'], {}, 5)
    with pytest.raises(TimeoutError):
        probe.run_bounded([sys.executable, '-c', 'import time; time.sleep(4)'], {}, .1)
    assert not probe.UNREAPED


def test_target_creation_refuses_existing_and_symlink(tmp_path):
    target = tmp_path / 'target'
    probe.create_target(target)
    assert target.stat().st_mode & 0o777 == 0o700
    sentinel = target / 'sentinel'
    sentinel.write_text('preserve')
    with pytest.raises(FileExistsError):
        probe.create_target(target)
    link = tmp_path / 'link'
    link.symlink_to(target, target_is_directory=True)
    with pytest.raises(OSError):
        probe.create_target(link / 'nested')
    assert sentinel.read_text() == 'preserve'


def test_reference_validation():
    value = {'kind': 'synthetic-random-toy', 'input_ids': [[0, 4, 5, 2], [0, 5, 2]],
             'reference': [[1.0] * 1024, [2.0] * 1024], 'synthetic_revision': probe.hashlib.sha256(
                 b'slaif-random-toy-seed-20261112-v1').hexdigest()[:40],
             'inventories': {fmt: {'schema': 2, 'model_name': 'BAAI/bge-m3',
                                   'model_revision': probe.hashlib.sha256(
                                       b'slaif-random-toy-seed-20261112-v1').hexdigest()[:40],
                                   'checkpoint_format': fmt}
                             for fmt in ('safetensors', 'pytorch-state-dict')},
             'generation_threads': {'intra_op': 1, 'inter_op': 1},
             'package_versions': probe.PINS,
             'package_origins': {name: '/packages/' + name for name in probe.PINS},
             'runtime_executable': '/runtime/bin/python3.12', 'runtime_prefix': '/runtime'}
    assert probe.validate_reference(value) == value['reference']
    revision = value['inventories']['safetensors']['model_revision']
    value['inventories']['safetensors']['model_revision'] = 'a' * 40
    with pytest.raises(ValueError, match='inventory identity'):
        probe.validate_reference(value)
    value['inventories']['safetensors']['model_revision'] = revision
    value['reference'][0][0] = float('nan')
    with pytest.raises(ValueError):
        probe.validate_reference(value)


def test_profile_rejects_wrong_and_extra_metadata(tmp_path):
    import tomllib

    raw = (probe.ROOT / 'worker_profiles/cpu/uv.lock').read_bytes()
    entries = tomllib.loads(raw.decode())['package']
    pins = {p['name']: p['version'] for p in entries if 'registry' in p['source']}
    for name, version in pins.items():
        info = tmp_path / (name + '.dist-info')
        info.mkdir()
        (info / 'METADATA').write_text(f'Name: {name}\nVersion: {version}\n')
    assert len(probe.verify_profile(tmp_path)) == 64
    extra = tmp_path / 'extra.dist-info'
    extra.mkdir()
    (extra / 'METADATA').write_text('Name: extra\nVersion: 1\n')
    with pytest.raises(ValueError):
        probe.verify_profile(tmp_path)


def test_fixed_generation_isolation_argv(tmp_path):
    argv = probe.generation_argv(tmp_path / 'new')
    assert argv[:4] == ['/usr/bin/timeout', '--signal=KILL', '120s', '/usr/bin/prlimit']
    assert '--unshare-net' in argv and '--clearenv' in argv
    assert '--as=4294967296' in argv and '--fsize=134217728' in argv
    assert argv[-4:] == ['/runtime/bin/python3.12', '-I', '-S', '/worker.py', '/output'][-4:]
    assert '/dev/nvidia0' not in argv
    bind = argv.index('--bind')
    assert argv[bind + 1:bind + 3] == [str(tmp_path / 'new'), '/output']


def test_timeout_kills_owned_descendant(tmp_path):
    import os
    import signal
    import time

    pidfile = tmp_path / 'pid'
    script = ('import subprocess,sys,time; '
              'p=subprocess.Popen([sys.executable,"-c","import time; time.sleep(4)"]); '
              'start=open("/proc/%d/stat" % p.pid).read().rsplit(")",1)[1].split()[19]; '
              'open(sys.argv[1],"w").write(str(p.pid)+" "+start); time.sleep(4)')
    try:
        with pytest.raises(TimeoutError):
            probe.run_bounded([sys.executable, '-c', script, str(pidfile)], {}, 1)
        pid, _ = pidfile.read_text().split()
        deadline = time.monotonic() + 2
        while time.monotonic() < deadline:
            try:
                state = Path(f'/proc/{pid}/stat').read_text().rsplit(')', 1)[1].split()[0]
            except FileNotFoundError:
                break
            if state == 'Z':
                break
            time.sleep(.02)
        else:
            pytest.fail('owned descendant remains live')
        assert not probe.UNREAPED
    finally:
        if pidfile.exists():
            pid, start = pidfile.read_text().split()
            try:
                fd = os.pidfd_open(int(pid))
                try:
                    stat = Path(f'/proc/{pid}/stat').read_text().rsplit(')', 1)[1].split()
                    if stat[19] == start and stat[0] != 'Z':
                        signal.pidfd_send_signal(fd, signal.SIGKILL)
                finally:
                    os.close(fd)
            except ProcessLookupError:
                pass


def test_child_environment_is_explicit(monkeypatch):
    monkeypatch.setenv('SYNTHETIC_PRIVATE_CREDENTIAL', 'do-not-forward')
    script = 'import os; print(os.environ.get("SYNTHETIC_PRIVATE_CREDENTIAL", "absent"))'
    assert probe.run_bounded([sys.executable, '-c', script], {}, 5) == b'absent\n'


def test_refusal_precedes_dispatch(tmp_path, monkeypatch):
    p, _ = permit(tmp_path)
    p.write_text('{}')
    monkeypatch.setattr(sys, 'argv', [str(PATH), '--permit', str(p), '--target',
                                     str(tmp_path / 'new'), '--runtime-dir', str(probe.RUNTIME),
                                     '--packages', str(probe.PACKAGES)])
    monkeypatch.setattr(probe, 'run_bounded', lambda *a, **kw: pytest.fail('dispatched'))
    with pytest.raises(ValueError, match='permit mismatch'):
        probe.main()
    assert not (tmp_path / 'new').exists()


def test_budget_counts_outputs_and_rejects_symlink(tmp_path):
    budget = probe.Budget()
    budget.charge_output(b'a' * probe.LIMITS['output_bytes'])
    with pytest.raises(ValueError, match='aggregate output'):
        budget.charge_output(b'a')
    (tmp_path / 'link').symlink_to('/tmp')
    with pytest.raises(ValueError, match='symlink'):
        budget.check(tmp_path)


def test_ordered_reference_and_normalized_validation():
    import struct

    rows = [[1.0] * 1024, [2.0] * 1024]
    assert probe.compare_rows(rows, rows) == 0.0
    with pytest.raises(ValueError, match='reference mismatch'):
        probe.compare_rows(rows, list(reversed(rows)))
    changed = [row[:] for row in rows]
    changed[0][0] = float('nan')
    with pytest.raises(ValueError, match='FP32'):
        probe.compare_rows(rows, changed)
    payload = struct.pack('<2048f', *([0.03125] * 2048))
    assert probe.validate_normalized(payload) == [1.0, 1.0]
    with pytest.raises(ValueError, match='norm'):
        probe.validate_normalized(bytes(8192))


def test_permit_rejects_boolean_integer_equivalence(tmp_path):
    p, value = permit(tmp_path)
    value['schema'] = True
    p.write_text(json.dumps(value))
    with pytest.raises(ValueError, match='permit mismatch'):
        probe.permit_check(p, probe.RUNTIME, probe.PACKAGES)


def test_cleanup_retries_interrupted_group_kill(monkeypatch):
    import signal
    import subprocess

    child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(4)'],
                             stdout=subprocess.PIPE, start_new_session=True)
    original = probe.os.killpg
    calls = []

    def interrupted_once(pid, sig):
        calls.append((pid, sig))
        if len(calls) == 1:
            raise KeyboardInterrupt()
        return original(pid, sig)

    try:
        monkeypatch.setattr(probe.os, 'killpg', interrupted_once)
        error = probe.cleanup(child)
        assert isinstance(error, KeyboardInterrupt)
        assert calls == [(child.pid, signal.SIGKILL)] * 2
        assert child.poll() is not None and not probe.UNREAPED
    finally:
        if child.poll() is None:
            child.kill()
        child.wait(timeout=2)


def test_reference_rejects_non_profile_origin():
    value = {'kind': 'synthetic-random-toy', 'input_ids': [[0, 4, 5, 2], [0, 5, 2]],
             'reference': [[1.0] * 1024, [2.0] * 1024], 'synthetic_revision': probe.hashlib.sha256(
                 b'slaif-random-toy-seed-20261112-v1').hexdigest()[:40],
             'inventories': {fmt: {'schema': 2, 'model_name': 'BAAI/bge-m3',
                                   'model_revision': probe.hashlib.sha256(
                                       b'slaif-random-toy-seed-20261112-v1').hexdigest()[:40],
                                   'checkpoint_format': fmt}
                             for fmt in ('safetensors', 'pytorch-state-dict')},
             'generation_threads': {'intra_op': 1, 'inter_op': 1},
             'package_versions': dict(probe.PINS),
             'package_origins': {name: '/packages/' + name for name in probe.PINS},
             'runtime_executable': '/runtime/bin/python3.12', 'runtime_prefix': '/runtime'}
    value['package_origins']['torch'] = '/foreign/torch.py'
    with pytest.raises(ValueError, match='origin'):
        probe.validate_reference(value)
    value['package_origins']['torch'] = '/packages/torch/__init__.py'
    value['package_versions']['torch'] = 'wrong'
    with pytest.raises(ValueError, match='pin'):
        probe.validate_reference(value)


def test_permit_rejects_hardlink_and_stale_source(tmp_path, monkeypatch):
    p, value = permit(tmp_path)
    link = tmp_path / 'hardlink'
    link.hardlink_to(p)
    with pytest.raises(ValueError, match='private'):
        probe.permit_check(p, probe.RUNTIME, probe.PACKAGES)
    link.unlink()
    stale = dict(value['sources'])
    stale[next(iter(stale))] = '0' * 64
    monkeypatch.setattr(probe, 'source_hashes', lambda: stale)
    with pytest.raises(ValueError, match='permit mismatch'):
        probe.permit_check(p, probe.RUNTIME, probe.PACKAGES)


def test_budget_reserves_whole_child_allowance(monkeypatch):
    budget = probe.Budget()
    budget.reserve(cpu=30, wall=120)
    monkeypatch.setattr(budget, 'check', lambda target=None: 100)
    with pytest.raises(TimeoutError, match='CPU budget'):
        budget.reserve(cpu=20, wall=90)
    with pytest.raises(ValueError, match='accounting'):
        budget.charge_size(-1)


def test_generation_stage_refuses_before_target_or_dispatch(tmp_path, monkeypatch):
    p, _ = permit(tmp_path)
    p.write_text('{}')
    monkeypatch.setattr(probe, 'run_bounded', lambda *a, **kw: pytest.fail('dispatched'))
    monkeypatch.setattr(probe, 'verify_profile', lambda *a: pytest.fail('profile scanned'))
    with pytest.raises(ValueError, match='permit mismatch'):
        probe.generation_stage(p, tmp_path / 'target', probe.RUNTIME, probe.PACKAGES,
                               probe.Budget())
    assert not (tmp_path / 'target').exists()


def test_generation_stage_refuses_insufficient_memory_before_target(tmp_path, monkeypatch):
    p, _ = permit(tmp_path)
    monkeypatch.setattr(probe, 'verify_profile', lambda *a: 'profile')
    monkeypatch.setattr(probe, 'memory_available',
                        lambda: (_ for _ in ()).throw(ValueError('insufficient memory')))
    monkeypatch.setattr(probe, 'run_bounded', lambda *a, **kw: pytest.fail('dispatched'))
    with pytest.raises(ValueError, match='insufficient memory'):
        probe.generation_stage(p, tmp_path / 'target', probe.RUNTIME, probe.PACKAGES,
                               probe.Budget())
    assert not (tmp_path / 'target').exists()


def test_format_identity_separation():
    def result(inventory, space):
        return {'forwards': 2, 'identity': {'inventory_id': inventory * 64,
                'space_id': space * 64, 'profile': 'c' * 64, 'policy_id': 'd' * 64,
                'code_id': 'e' * 64}}

    results = {'safetensors': result('a', '1'), 'pytorch-state-dict': result('b', '2')}
    probe.validate_format_identities(results, 'c' * 64)
    results['pytorch-state-dict']['identity']['space_id'] = '1' * 64
    with pytest.raises(ValueError, match='distinct'):
        probe.validate_format_identities(results, 'c' * 64)


def test_owned_bwrap_child_has_private_environment(monkeypatch):
    monkeypatch.setenv('SYNTHETIC_PRIVATE_CREDENTIAL', 'not-for-child')
    script = ('import json,os; print(json.dumps({"user":os.getenv("USER"),'
              '"home":os.getenv("HOME"),"secret":os.getenv("SYNTHETIC_PRIVATE_CREDENTIAL"),'
              '"gpu":os.path.exists("/dev/nvidia0"),"host_home":os.path.exists("/home")}))')
    argv = ['/usr/bin/prlimit', '--as=1073741824', '--cpu=3', '/usr/bin/timeout', '5',
            '/usr/bin/bwrap', '--unshare-user', '--unshare-pid', '--unshare-net',
            '--die-with-parent', '--clearenv', '--ro-bind', '/usr', '/usr',
            '--symlink', 'usr/lib', '/lib', '--symlink', 'usr/lib64', '/lib64',
            '--proc', '/proc', '--dev', '/dev', '--tmpfs', '/tmp', '--setenv', 'HOME', '/tmp',
            '--setenv', 'USER', 'raggedized-toy', '--', '/usr/bin/python3', '-c', script]
    value = json.loads(probe.run_bounded(argv, dict(probe.os.environ), 10))
    assert value == {'user': 'raggedized-toy', 'home': '/tmp', 'secret': None,
                     'gpu': False, 'host_home': False}


def test_cleanup_retains_failed_group_ownership(monkeypatch):
    class Done:
        pid = 123456789

        class Stream:
            def close(self):
                pass

        stdout = Stream()

        def wait(self, timeout):
            return 0

    def refused(*args):
        raise OSError('synthetic')

    monkeypatch.setattr(probe.os, 'killpg', refused)
    child = Done()
    try:
        assert isinstance(probe.cleanup(child), OSError)
        assert probe.PENDING_GROUPS[-1] == child.pid
    finally:
        probe.PENDING_GROUPS.remove(child.pid)


def test_parent_limits_in_owned_process():
    script = ("import importlib.util,json,resource,signal,sys; "
              "s=importlib.util.spec_from_file_location('probe',sys.argv[1]); "
              "m=importlib.util.module_from_spec(s); s.loader.exec_module(m); "
              "m.install_parent_limits(); "
              "print(json.dumps([resource.getrlimit(resource.RLIMIT_CPU),"
              "resource.getrlimit(resource.RLIMIT_FSIZE),signal.alarm(0)]))")
    values = json.loads(probe.run_bounded([sys.executable, '-c', script, str(PATH)], {}, 5))
    assert values[0][0] <= 120 and values[0][1] <= 120
    assert values[1][0] <= 128 * 1024**2 and values[1][1] <= 128 * 1024**2
    assert 1 <= values[2] <= 600


def test_worker_orchestration_uses_two_calls_and_verified_profile(tmp_path, monkeypatch):
    from types import SimpleNamespace
    from slaif_raggedized_helper import cpu_embedding_worker
    from test_cpu_embedding_backend import make_tree

    root = tmp_path / 'safetensors'
    manifest, _, _, _, _ = make_tree(root)
    manifest.update(schema=2, checkpoint_format='safetensors')
    rows = ((1.0,) * 1024, (2.0,) * 1024)
    observed = []

    class FakeWorker:
        def __init__(self, raw, artifact_root, definition, tokenizer, inventory, runtime, policy):
            observed.append((artifact_root, policy.max_rows, policy.calls))
            self._child, self._output, self._calls = SimpleNamespace(poll=lambda: None), 0, 0
            self.profile = 'c' * 64
            self.space = SimpleNamespace(inventory_id=inventory, space_id='d' * 64)
            self.policy_fingerprint, self.code_fingerprint = 'e' * 64, 'f' * 64

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def close(self):
            self._child = None

        def forward_cls(self, ids):
            assert ids == [[0, 4, 5, 2], [0, 5, 2]]
            self._calls += 1
            self._output += 20
            return rows

    monkeypatch.setattr(cpu_embedding_worker, 'CPUEmbeddingWorker', FakeWorker)
    monkeypatch.setattr(probe, 'memory_available', lambda: 8 * 1024**3)
    value = probe.verify_worker_format(tmp_path, 'safetensors', manifest, rows,
                                       probe.Budget(), 'c' * 64)
    assert observed == [(root, 2, 2)]
    assert value['forwards'] == 2 and value['max_abs_error'] == 0.0
    assert value['normalized']['norms'] == [1.0, 1.0]


def test_failed_constructor_reaps_owned_child():
    import subprocess

    children = []

    class StartupFailure:
        def __init__(self):
            self._child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(4)'])
            children.append(self._child)
            raise ValueError('startup')

        def close(self):
            self._child.kill()
            self._child.wait(timeout=2)
            self._child = None

    try:
        with pytest.raises(ValueError, match='startup'):
            with probe.OwnedSession(StartupFailure):
                pytest.fail('entered')
        assert children[0].poll() is not None and not probe.PENDING_OWNERS
    finally:
        for child in children:
            if child.poll() is None:
                child.kill()
            child.wait(timeout=2)


def test_token_owner_retains_then_retries_without_deleting_sentinel(tmp_path):
    sentinel = tmp_path / 'sentinel'
    sentinel.write_text('keep')

    class Child:
        alive = True

        def poll(self):
            return None if self.alive else 0

        def terminate(self):
            pass

        def kill(self):
            pass

        def wait(self, timeout):
            if self.alive:
                raise probe.subprocess.TimeoutExpired('owned', timeout)
            return 0

    class Temporary:
        def cleanup(self):
            assert not child.alive

    class Token:
        def __init__(self):
            self._child = child
            self._tmp = Temporary()

        def close(self):
            self._child = None
            self._tmp.cleanup()
            self._tmp = None

    child = Child()
    guard = probe.OwnedSession(probe.token_owner_class(Token))
    try:
        with pytest.raises(RuntimeError, match='pending'):
            with guard:
                pass
        assert guard in probe.PENDING_OWNERS and guard.owner._child is child
        assert sentinel.read_text() == 'keep'
        with pytest.raises(RuntimeError, match='pending owned'):
            probe.OwnedSession(Token)
        child.alive = False
        guard.close()
        assert guard not in probe.PENDING_OWNERS and sentinel.read_text() == 'keep'
    finally:
        child.alive = False
        if guard in probe.PENDING_OWNERS:
            guard.close()


def test_cleanup_interrupt_preserves_original_and_reaps():
    import subprocess

    children = []

    class Interrupted:
        def __init__(self):
            self._child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(4)'])
            children.append(self._child)
            self.calls = 0

        def close(self):
            self.calls += 1
            if self.calls == 1:
                raise KeyboardInterrupt()
            self._child.kill()
            self._child.wait(timeout=2)
            self._child = None

    try:
        with pytest.raises(ValueError, match='body') as caught:
            with probe.OwnedSession(Interrupted):
                raise ValueError('body')
        assert caught.value.__notes__ == ['session cleanup pending or refused']
        assert children[0].poll() is not None and not probe.PENDING_OWNERS
    finally:
        for child in children:
            if child.poll() is None:
                child.kill()
            child.wait(timeout=2)


def test_token_guard_reaps_real_owned_child_before_temporary_cleanup(tmp_path):
    import subprocess

    events, children = [], []
    sentinel = tmp_path / 'sentinel'
    sentinel.write_text('keep')

    class Temporary:
        def cleanup(self):
            assert children[0].poll() is not None
            events.append('temporary cleaned')

    class Token:
        def __init__(self):
            self._child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(4)'])
            children.append(self._child)
            self._tmp = Temporary()

        def close(self):
            self._child = None
            self._tmp.cleanup()
            self._tmp = None

    try:
        with probe.OwnedSession(probe.token_owner_class(Token)):
            assert children[0].poll() is None
        assert children[0].poll() is not None and events == ['temporary cleaned']
        assert sentinel.read_text() == 'keep' and not probe.PENDING_OWNERS
    finally:
        for child in children:
            if child.poll() is None:
                child.kill()
            child.wait(timeout=2)
