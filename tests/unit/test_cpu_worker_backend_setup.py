"""Behavioral checks for the isolated synthetic worker capsule setup."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / 'tests/support/prepare_cpu_worker_test_backend.py'
SPEC = importlib.util.spec_from_file_location('cpu_setup', SCRIPT)
setup = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(setup)
LOCK = ROOT / 'worker_profiles/cpu/uv.lock'
REQ = ROOT / 'tests/support/cpu-worker-test-requirements.txt'
RUNTIME = os.environ.get('SLAIF_CPU_WORKER_TEST_ROOT')
PACKAGES = os.environ.get('SLAIF_CPU_WORKER_TEST_PACKAGES')


def test_fixed_wheel_pins_and_tampering(tmp_path):
    pins, _ = setup.fixed_inputs(LOCK, REQ)
    assert len(pins) == 28 and len(setup.WHEELS) == 6
    bad = tmp_path / 'requirements'
    bad.write_bytes(REQ.read_bytes() + b'other==1 --hash=sha256:00\n')
    with pytest.raises(ValueError):
        setup.fixed_inputs(LOCK, bad)
    bad.write_bytes(REQ.read_bytes().replace(b'pydantic==2.14.3', b'pydantic==2.14.2'))
    with pytest.raises(ValueError):
        setup.fixed_inputs(LOCK, bad)
    lock = tmp_path / 'lock'
    lock.write_bytes(LOCK.read_bytes() + b'\n')
    with pytest.raises(ValueError):
        setup.fixed_inputs(lock, REQ)


def test_child_capture_timeout_output_limit_and_reap(tmp_path):
    env = {'PATH': '/usr/bin:/bin'}
    assert setup.run([sys.executable, '-c', 'print("ok")'], env, 3) == 'ok\n'
    code = 'import sys; sys.stdout.write("x" * int(sys.argv[1]))'
    assert len(setup.run([sys.executable, '-c', code, '8192'], env, 3)) == 8192
    with pytest.raises(RuntimeError, match='output'):
        setup.run([sys.executable, '-c', code, '8193'], env, 3)
    pidfile = tmp_path / 'pid'
    code = 'import os,sys,time; open(sys.argv[1],"w").write(str(os.getpid())); time.sleep(30)'
    with pytest.raises(TimeoutError):
        setup.run([sys.executable, '-c', code, str(pidfile)], env, 0.5)
    pid = int(pidfile.read_text())
    with pytest.raises(ProcessLookupError):
        os.kill(pid, 0)


def test_existing_and_symlink_target_preserve_sentinel(tmp_path):
    assert RUNTIME, 'SLAIF_CPU_WORKER_TEST_ROOT is required'
    existing = tmp_path / 'existing'
    existing.mkdir()
    sentinel = existing / 'sentinel'
    sentinel.write_text('preserved')
    link = tmp_path / 'link'
    link.symlink_to(existing, target_is_directory=True)
    env = dict(os.environ, PYTHONPATH='secret-pythonpath-value',
               PIP_INDEX_URL='https://secret-user:secret-password@example.invalid/simple',
               UV_INDEX_URL='https://secret-user:secret-password@example.invalid/simple')
    for target in (existing, link):
        result = subprocess.run([sys.executable, str(SCRIPT), '--runtime-dir', RUNTIME,
                                 '--target', str(target)], env=env, capture_output=True,
                                text=True, timeout=15)
        assert result.returncode != 0
        assert 'secret-' not in result.stdout + result.stderr
        assert sentinel.read_text() == 'preserved'


def test_real_capsule_inventory_and_data_only_classification():
    assert PACKAGES and RUNTIME, 'explicit setup environment is required'
    packages = Path(PACKAGES)
    evidence = json.loads((packages.parent / 'setup-evidence.json').read_text())
    assert evidence['fixturekind'] == 'synthetic-cpu-worker-test-v1'
    assert evidence['state'] == 'complete'
    real = evidence['actual_installed']['actual']
    fake = evidence['synthetic_metadata_only']
    assert len(real) == 6 and len(fake) == 22 and not (set(real) & set(fake))
    assert real['tokenizers'] == '0.21.4'
    assert (packages / 'tokenizers/__init__.py').is_file()
    for name, version in fake.items():
        info = packages / (name.replace('-', '_') + '-' + version + '.dist-info')
        assert sorted(p.name for p in info.iterdir()) == ['METADATA']
        assert info.joinpath('METADATA').read_text().splitlines()[1:] == [
            'Name: ' + name, 'Version: ' + version]
        assert not (packages / name.replace('-', '_')).exists()


def test_wrong_or_extra_real_metadata_rejected():
    assert PACKAGES, 'SLAIF_CPU_WORKER_TEST_PACKAGES is required'
    evidence = json.loads((Path(PACKAGES).parent / 'setup-evidence.json').read_text())
    actual = evidence['actual_installed']
    setup.validate_actual(actual)
    actual['actual']['pydantic'] = '0.0'
    with pytest.raises(RuntimeError, match='inventory'):
        setup.validate_actual(actual)
    actual['actual']['pydantic'] = '2.14.3'
    actual['actual']['unexpected'] = '1'
    with pytest.raises(RuntimeError, match='inventory'):
        setup.validate_actual(actual)


def test_nonzero_child_is_reaped(monkeypatch):
    real_popen = setup.subprocess.Popen
    children = []

    def track(*args, **kwargs):
        child = real_popen(*args, **kwargs)
        children.append(child)
        return child

    monkeypatch.setattr(setup.subprocess, 'Popen', track)
    with pytest.raises(RuntimeError, match='child failed'):
        setup.run([sys.executable, '-c', 'raise SystemExit(7)'], {'PATH': '/usr/bin:/bin'}, 3)
    assert children[0].poll() == 7


def test_cleanup_once_interrupted_retries_and_preserves_interrupt(monkeypatch):
    real_kill = setup.os.killpg
    calls = []
    children = []
    real_popen = setup.subprocess.Popen

    def track(*args, **kwargs):
        child = real_popen(*args, **kwargs)
        children.append(child)
        return child

    def interrupted(pid, sig):
        calls.append(pid)
        if len(calls) == 1:
            raise KeyboardInterrupt()
        return real_kill(pid, sig)

    monkeypatch.setattr(setup.subprocess, 'Popen', track)
    monkeypatch.setattr(setup.os, 'killpg', interrupted)
    with pytest.raises(KeyboardInterrupt):
        setup.run([sys.executable, '-c', 'print("ok")'], {'PATH': '/usr/bin:/bin'}, 3)
    assert len(calls) == 2 and children[0].poll() == 0


def test_timeout_kills_owned_descendant(tmp_path):
    import time

    pidfile = tmp_path / 'descendant'
    code = ('import subprocess,sys,time; '
            'p=subprocess.Popen([sys.executable,"-c","import time; time.sleep(30)"]); '
            'open(sys.argv[1],"w").write(str(p.pid)); time.sleep(30)')
    with pytest.raises(TimeoutError):
        setup.run([sys.executable, '-c', code, str(pidfile)], {'PATH': '/usr/bin:/bin'}, 0.7)
    pid = int(pidfile.read_text())
    deadline = time.monotonic() + 2
    while time.monotonic() < deadline:
        stat = Path(f'/proc/{pid}/stat')
        if not stat.exists() or stat.read_text().rsplit(')', 1)[1].split()[0] == 'Z':
            break
        time.sleep(0.02)
    else:
        pytest.fail('owned descendant remained running')


def test_unreaped_handle_retained_after_bounded_wait(monkeypatch):
    child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)'],
                             stdout=subprocess.PIPE, start_new_session=True)
    original_wait = child.wait
    attempts = []

    def refuses_wait(*, timeout):
        attempts.append(timeout)
        raise subprocess.TimeoutExpired('owned', timeout)

    monkeypatch.setattr(child, 'wait', refuses_wait)
    try:
        assert isinstance(setup.cleanup(child), subprocess.TimeoutExpired)
        assert attempts == [1, 1] and child in setup.UNREAPED
    finally:
        setup.UNREAPED.remove(child)
        original_wait(timeout=2)


def test_timeout_remains_primary_during_cleanup_interrupt(monkeypatch):
    real_kill = setup.os.killpg
    calls = []

    def interrupted(pid, sig):
        calls.append(pid)
        if len(calls) == 1:
            raise KeyboardInterrupt()
        return real_kill(pid, sig)

    monkeypatch.setattr(setup.os, 'killpg', interrupted)
    with pytest.raises(TimeoutError) as caught:
        setup.run([sys.executable, '-c', 'import time; time.sleep(30)'],
                  {'PATH': '/usr/bin:/bin'}, 0.5)
    assert len(calls) == 2 and caught.value.__notes__
