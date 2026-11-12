"""Filesystem-only identity evidence; no tokenizer or native runtime is executed."""
import dataclasses
import hashlib
import json
import os
import shutil
from pathlib import Path
from unittest import mock

import pytest

from slaif_raggedized_helper import embedding_native_identity as identity
from slaif_raggedized_helper.native_tokenizers import Runtime



@pytest.fixture
def runtime(tmp_path):
    root = tmp_path / 'root'
    (root / 'bin').mkdir(parents=True)
    executable = root / 'bin/python3.12'
    executable.write_bytes(b'synthetic executable fixture')
    executable.chmod(0o755)
    packages = tmp_path / 'packages'
    (packages / 'tokenizers').mkdir(parents=True)
    (packages / 'tokenizers/__init__.py').write_bytes(b'fixture')
    dist = packages / identity.DIST
    dist.mkdir()
    (dist / 'METADATA').write_bytes(b'Name: tokenizers\nVersion: 0.21.4\n\n')
    return Runtime(root, packages, 'python3.12')


def test_actual_and_detached():
    root = Path(os.environ['SLAIF_NATIVE_TEST_ROOT'])
    packages = Path(os.environ['SLAIF_NATIVE_TEST_PACKAGES'])
    python = os.environ['SLAIF_NATIVE_TEST_PYTHON']
    assert python == 'python3.12'
    result = identity.predict(Runtime(root, packages, python))
    obj = json.loads(result.record_bytes)
    assert obj['python']['bytes'] > 0 and len(obj['package']['files']) >= 2
    assert identity.validate_record(result.record_bytes) == result.fingerprint
    with pytest.raises(dataclasses.FrozenInstanceError):
        result.fingerprint = 'changed'
    with mock.patch.object(os, 'open', side_effect=AssertionError('I/O')):
        assert identity.validate_record(result.record_bytes) == result.fingerprint


def test_equal_copies_and_selected_changes(runtime, tmp_path):
    initial = identity.predict(runtime)
    root = tmp_path / 'other-root'
    packages = tmp_path / 'other-packages'
    shutil.copytree(runtime.root, root)
    shutil.copytree(runtime.packages, packages)
    other = Runtime(root, packages, 'python3.12')
    assert identity.predict(other) == initial
    (packages / '.lock').touch()
    assert identity.predict(other) == initial
    (packages / 'tokenizers/__pycache__').mkdir()
    (packages / 'tokenizers/__pycache__/a.pyc').write_bytes(b'bytecode')
    assert identity.predict(other).fingerprint != initial.fingerprint
    (root / 'bin/python3.12').write_bytes(b'changed')
    assert identity.predict(other).fingerprint != initial.fingerprint


@pytest.mark.parametrize('mutation', ['extra', 'metadata', 'duplicate', 'symlink', 'fifo',
                                      'hardlink', 'missing', 'depth', 'lock'])
def test_refusals(runtime, mutation):
    p = runtime.packages
    if mutation == 'extra':
        (p / 'sitecustomize.py').touch()
    elif mutation == 'metadata':
        (p / identity.DIST / 'METADATA').write_bytes(b'Name: tokenizers\nVersion: 9\n')
    elif mutation == 'duplicate':
        (p / identity.DIST / 'METADATA').write_bytes(
            b'Name: tokenizers\nName: tokenizers\nVersion: 0.21.4\n')
    elif mutation == 'symlink':
        (p / 'tokenizers/link').symlink_to('missing')
    elif mutation == 'fifo':
        os.mkfifo(p / 'tokenizers/fifo')
    elif mutation == 'hardlink':
        os.link(p / 'tokenizers/__init__.py', p / 'tokenizers/linked')
    elif mutation == 'missing':
        (p / 'tokenizers/__init__.py').unlink()
    elif mutation == 'depth':
        (p / 'tokenizers/a/b/c/d/e/f/g/h').mkdir(parents=True)
    elif mutation == 'lock':
        (p / '.lock').write_bytes(b'x')
    with pytest.raises(identity.IdentityRefused, match='^native runtime identity refused$'):
        identity.predict(runtime)


def test_validator_strict(runtime):
    raw = identity.predict(runtime).record_bytes
    obj = json.loads(raw)
    expected = 'sha256:' + hashlib.sha256(identity.DOMAIN + raw).hexdigest()
    assert identity.validate_record(raw) == expected
    bad = [raw + b'\n', b'{"schema":1,"schema":1}', b'{}']
    for change in ('extra', 'bool', 'path', 'policy', 'fingerprint'):
        altered = json.loads(raw)
        if change == 'extra':
            altered['extra'] = 1
        elif change == 'bool':
            altered['schema'] = True
        elif change == 'path':
            altered['package']['files'][0]['path'] = '../escape'
        elif change == 'policy':
            altered['policy']['max_ids'] = True
        else:
            altered['package']['fingerprint'] = '0' * 64
        bad.append(identity._canonical(altered))
    for item in bad:
        with pytest.raises(identity.IdentityRefused):
            identity.validate_record(item)
    assert obj['qualification'] == 'unknown'


def test_interrupt_closes_owned_descriptors(runtime):
    interruption = KeyboardInterrupt('same object')
    before = len(os.listdir('/proc/self/fd'))
    with mock.patch.object(identity, '_scan', side_effect=interruption):
        with pytest.raises(KeyboardInterrupt) as caught:
            identity.predict(runtime)
    assert caught.value is interruption
    assert len(os.listdir('/proc/self/fd')) == before


def test_original_narrow_guard_causal(runtime):
    # Only the original hardlink predicate is disabled in an in-memory copy.
    original = Path(identity.__file__).read_text()
    needle = 'before.st_nlink != 1'
    assert original.count(needle) == 1
    os.link(runtime.packages / 'tokenizers/__init__.py', runtime.packages / 'tokenizers/linked')
    with pytest.raises(identity.IdentityRefused):
        identity.predict(runtime)
    namespace = dict(identity.__dict__)
    exec(compile(original.replace(needle, 'False'), identity.__file__, 'exec'), namespace)
    assert namespace['predict'](runtime).record_bytes


def test_limits_and_path_guards(runtime, tmp_path):
    for index in range(513):
        (runtime.packages / 'tokenizers' / str(index)).touch()
    with pytest.raises(identity.IdentityRefused):
        identity.predict(runtime)
    for entry in (runtime.packages / 'tokenizers').iterdir():
        if entry.name != '__init__.py':
            entry.unlink()
    # Baseline: the unmodified small fixture with the actual fstat predicts
    # successfully.
    assert identity.predict(runtime).record_bytes
    # Unit guard test of the production size guard: the owned real file stays
    # small, so its creation never exceeds an inherited RLIMIT_FSIZE; the
    # oversized condition is simulated at the fstat boundary for this one
    # actual device/inode only. The reported-oversized size is a boundary
    # simulation, not an actual oversized-file claim.
    large = runtime.packages / 'tokenizers/large'
    large.write_bytes(b'fixture')
    target = (os.stat(large).st_dev, os.stat(large).st_ino)
    original_fstat = os.fstat
    original_read = os.read

    def bounded_fstat(fd):
        result = original_fstat(fd)
        if (result.st_dev, result.st_ino) == target:
            values = list(result)
            values[6] = identity.MAX_FILE + 1
            return os.stat_result(values)
        return result

    reads = []

    def bounded_read(fd, nbytes):
        data = original_read(fd, nbytes)
        st = original_fstat(fd)
        if (st.st_dev, st.st_ino) == target:
            reads.append(len(data))
        return data

    with mock.patch.object(os, 'fstat', bounded_fstat), \
            mock.patch.object(os, 'read', bounded_read):
        # The production size guard must refuse before reading that file.
        with pytest.raises(identity.IdentityRefused):
            identity.predict(runtime)
        assert reads == []
        # One-guard-omission control: with ONLY the initial size guard removed
        # in an owned temporary in-memory source copy, the actual file IS read
        # and the intact bytes-read/st_size consistency guard still refuses.
        # This demonstrates early refusal, not admission of inconsistent stat
        # data.
        source = Path(identity.__file__).read_text()
        needle = 'or before.st_size > limit'
        assert source.count(needle) == 1
        namespace = dict(identity.__dict__)
        exec(compile(source.replace(needle, 'or False'), identity.__file__,
                     'exec'), namespace)
        with pytest.raises(namespace['IdentityRefused']):
            namespace['predict'](runtime)
        # The actual read observes the 7 fixture bytes then the 0-byte EOF.
        assert reads == [len(b'fixture'), 0]
    large.unlink()
    link = tmp_path / 'alias'
    link.symlink_to(runtime.root, target_is_directory=True)
    with pytest.raises(identity.IdentityRefused):
        identity.predict(Runtime(link, runtime.packages, 'python3.12'))
    with pytest.raises(identity.IdentityRefused):
        identity.predict(Runtime(runtime.root, runtime.packages, 'python3.14'))


def test_source_and_policy_change_identity_or_refuse(runtime):
    initial = identity.predict(runtime)
    source = identity._sources()
    altered = dict(source)
    name = 'embedding_tokenizer_worker.py'
    entry = list(altered[name])
    entry[1] = '0' * 64
    altered[name] = tuple(entry)
    with mock.patch.object(identity, '_sources', return_value=altered):
        assert identity.predict(runtime).fingerprint != initial.fingerprint
    with mock.patch.object(identity, '_policy', return_value={'unexpected': 1}):
        with pytest.raises(identity.IdentityRefused):
            identity.validate_record(initial.record_bytes)


def test_aggregate_limit_and_race(runtime):
    for index in range(3):
        with (runtime.packages / 'tokenizers' / str(index)).open('wb') as output:
            output.truncate(23 * 1024 * 1024)
    with pytest.raises(identity.IdentityRefused):
        identity.predict(runtime)
    for index in range(3):
        (runtime.packages / 'tokenizers' / str(index)).unlink()
    original = identity._scan
    count = 0

    def changed(fd):
        nonlocal count
        value = original(fd)
        count += 1
        if count == 1:
            (runtime.packages / 'tokenizers/__init__.py').write_bytes(b'changed')
        return value

    with mock.patch.object(identity, '_scan', side_effect=changed):
        with pytest.raises(identity.IdentityRefused):
            identity.predict(runtime)


def test_unsafe_record_paths(runtime):
    obj = json.loads(identity.predict(runtime).record_bytes)
    for path in ('/absolute', 'tokenizers/../bad', 'tokenizers/a\\b', 'tokenizers/\n'):
        obj['package']['files'][0]['path'] = path
        obj['package']['fingerprint'] = hashlib.sha256(
            identity._canonical(obj['package']['files'])).hexdigest()
        with pytest.raises(identity.IdentityRefused):
            identity.validate_record(identity._canonical(obj))


def test_cleanup_interrupt_priority_and_uncertainty(tmp_path, monkeypatch):
    class Stop(BaseException):
        pass

    fd = os.open(tmp_path / 'file', os.O_CREAT | os.O_RDONLY, 0o600)
    real_close = os.close
    stop = Stop('cleanup')
    try:
        with monkeypatch.context() as patch:
            patch.setattr(identity.os, 'close', lambda _: (_ for _ in ()).throw(stop))
            try:
                raise ValueError('ordinary')
            except ValueError:
                with pytest.raises(Stop) as caught:
                    identity._close(fd)
            assert caught.value is stop
            assert 'cleanup uncertain' in stop.__notes__[0]
        os.fstat(fd)
    finally:
        real_close(fd)


def test_close_after_effect_does_not_retry_reused_descriptor(tmp_path, monkeypatch):
    class Stop(BaseException):
        pass

    sentinel_path = tmp_path / 'sentinel'
    sentinel_path.write_bytes(b'owned sentinel')
    real_close = os.close
    stop = Stop('after close')
    state = {'sentinel': None, 'injected': False}

    def close_then_raise(fd):
        if not state['injected']:
            state['injected'] = True
            real_close(fd)
            state['sentinel'] = os.open(sentinel_path, os.O_RDONLY | os.O_CLOEXEC)
            assert state['sentinel'] == fd
            raise stop
        return real_close(fd)

    try:
        with monkeypatch.context() as patch:
            patch.setattr(identity.os, 'close', close_then_raise)
            with pytest.raises(Stop) as caught:
                identity._directory(str(tmp_path))
            assert caught.value is stop
        assert os.fstat(state['sentinel']).st_size == len(b'owned sentinel')
    finally:
        if state['sentinel'] is not None:
            real_close(state['sentinel'])


def test_original_interrupt_outranks_cleanup_error(tmp_path, monkeypatch):
    class Stop(BaseException):
        pass

    fd = os.open(tmp_path / 'file', os.O_CREAT | os.O_RDONLY, 0o600)
    real_close = os.close
    stop = Stop('original')
    try:
        with monkeypatch.context() as patch:
            patch.setattr(identity.os, 'close', lambda _: (_ for _ in ()).throw(OSError()))
            with pytest.raises(Stop) as caught:
                try:
                    raise stop
                finally:
                    identity._close(fd)
            assert caught.value is stop
            assert 'cleanup uncertain' in stop.__notes__[0]
    finally:
        real_close(fd)


def test_hostile_exception_diagnostics_never_replace_refusal(runtime, monkeypatch):
    class DiagnosticStop(BaseException):
        pass

    class Hostile(ValueError):
        def __getattribute__(self, name):
            if name in ('__notes__', 'add_note'):
                raise DiagnosticStop()
            return super().__getattribute__(name)

    with monkeypatch.context() as patch:
        patch.setattr(identity, '_scan', lambda _: (_ for _ in ()).throw(Hostile()))
        with pytest.raises(identity.IdentityRefused):
            identity.predict(runtime)
    with monkeypatch.context() as patch:
        patch.setattr(identity, '_validate', lambda _: (_ for _ in ()).throw(Hostile()))
        with pytest.raises(identity.IdentityRefused):
            identity.validate_record(b'{}')


def test_hostile_add_note_preserves_interruption(tmp_path, monkeypatch):
    class Stop(BaseException):
        def __getattribute__(self, name):
            if name == 'add_note':
                raise RuntimeError('hostile diagnostic')
            return super().__getattribute__(name)

    fd = os.open(tmp_path / 'file', os.O_CREAT | os.O_RDONLY, 0o600)
    real_close = os.close
    stop = Stop()
    before = identity._uncertain_closes
    try:
        with monkeypatch.context() as patch:
            patch.setattr(identity.os, 'close', lambda _: (_ for _ in ()).throw(stop))
            with pytest.raises(Stop) as caught:
                identity._close(fd)
            assert caught.value is stop
        assert identity._uncertain_closes == before + 1
        os.fstat(fd)
    finally:
        real_close(fd)


def test_caller_exception_does_not_hide_uncertain_close(runtime, monkeypatch):
    real_close = os.close
    state = {'fd': None, 'failed': False}
    before = len(os.listdir('/proc/self/fd'))

    def fail_once(fd):
        if not state['failed']:
            state['failed'] = True
            state['fd'] = fd
            raise OSError('controlled before-effect failure')
        return real_close(fd)

    try:
        with monkeypatch.context() as patch:
            patch.setattr(identity.os, 'close', fail_once)
            try:
                raise ValueError('unrelated caller context')
            except ValueError:
                with pytest.raises(identity.IdentityRefused) as caught:
                    identity.predict(runtime)
        assert 'cleanup uncertain' in caught.value.__notes__[0]
        os.fstat(state['fd'])
        assert len(os.listdir('/proc/self/fd')) == before + 1
    finally:
        if state['fd'] is not None:
            real_close(state['fd'])
