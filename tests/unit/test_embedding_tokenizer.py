"""Real native token IDs and session boundary tests with owned fixtures."""
import hashlib
import importlib.util
import json
import os
import socket
import subprocess
from dataclasses import FrozenInstanceError, replace
from pathlib import Path

import pytest

from slaif_raggedized_helper import embedding_tokenizer as e
from slaif_raggedized_helper import native_tokenizers as n
from slaif_raggedized_helper.tokenizer_session import Session


def make_native(tmp_path):
    path = Path(__file__).with_name('test_native_tokenizers.py')
    spec = importlib.util.spec_from_file_location('trusted_native_fixture', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    paths, runtime, definition = module.make_native(tmp_path)
    return replace(definition(paths[0]), role='bge_representation', model_revision='1' * 40,
                   preprocessing='identity'), runtime


def test_real_reuse_and_receipts(tmp_path, monkeypatch):
    d, runtime = make_native(tmp_path)
    actual_popen = subprocess.Popen.__init__
    children = []

    def spy(child, *args, **kwargs):
        actual_popen(child, *args, **kwargs)
        children.append(child)

    monkeypatch.setattr(subprocess.Popen, '__init__', spy)
    with e.TokenIDSession(d, runtime) as session:
        child = session._child
        first = session.encode('hello café 世界')
        second = session.encode('hello ' * 100)
        assert session._child is child and len(children) == 1
        assert first.ids == (1, 3, 4, 5, 2)
        assert len(second.ids) == 102
        assert first.input_sha256 == hashlib.sha256(
            json.dumps(['hello café 世界', None], ensure_ascii=True,
                       separators=(',', ':')).encode()).hexdigest()
        assert (first.artifact_sha256, first.model_revision, first.preprocessing) == (
            d.sha256, d.model_revision, 'identity')
        with pytest.raises(FrozenInstanceError):
            first.count = 0
    assert child.poll() is not None
    monkeypatch.setattr(subprocess.Popen, '__init__', actual_popen)
    with Session((d,), runtime) as counts:
        assert counts.count(d.role, 'hello café 世界').count == first.count
        assert counts.count(d.role, 'hello ' * 100).count == second.count
    session.close()
    with pytest.raises(n.TokenizerError):
        session.encode('x')


@pytest.mark.parametrize(('field', 'value'), [
    ('sha256', '0' * 64), ('model_revision', 'x' * 40), ('model_revision', '1' * 39),
    ('preprocessing', 'other'), ('role', 'bge_body'), ('backend_version', '0.0'),
])
def test_bad_metadata(tmp_path, field, value):
    d, runtime = make_native(tmp_path)
    with pytest.raises(n.TokenizerError):
        e.TokenIDSession(replace(d, **{field: value}), runtime)


@pytest.mark.parametrize('kwargs', [
    {'max_calls': True}, {'max_calls': 1025}, {'max_ids': 0}, {'lifetime_seconds': float('nan')},
    {'request_seconds': 2.1}, {'max_response_bytes': 16385}, {'max_artifact_bytes': 32000001},
])
def test_policy_rejected(kwargs):
    with pytest.raises(n.TokenizerError):
        e.Policy(**kwargs)


@pytest.mark.parametrize('text', [None, 'x' * 100001, '\ud800', 'é' * 40000],
                         ids=['type', 'chars', 'surrogate', 'wire'])
def test_bad_input_closes(tmp_path, text):
    d, runtime = make_native(tmp_path)
    session = e.TokenIDSession(d, runtime)
    child = session._child
    with pytest.raises(n.TokenizerError, match='^tokenizer session refused$'):
        session.encode(text)
    assert child.poll() is not None


@pytest.mark.parametrize('response', [b'{}', b'\xff', b'{"a":NaN}', b'{"a":1,"a":2}',
                                      b'x' * 16385, b'{}\nextra'])
def test_malformed_response(tmp_path, monkeypatch, response):
    d, runtime = make_native(tmp_path)
    session = e.TokenIDSession(d, runtime)
    child = session._child
    monkeypatch.setattr(session, '_read', lambda deadline: response)
    with pytest.raises(n.TokenizerError):
        session.encode('private canary')
    assert child.poll() is not None


@pytest.mark.parametrize(('field', 'value'), [
    ('nonce', 'wrong'), ('digest', 'wrong'), ('version', 'wrong'), ('count', True),
    ('count', 4), ('ids', [1, True]), ('ids', [1, -1]), ('ids', [1, 2**31]),
    ('ids', [1]), ('ids', [1] * 1025), ('extra', 1),
])
def test_misbound_result(tmp_path, monkeypatch, field, value):
    d, runtime = make_native(tmp_path)
    session = e.TokenIDSession(d, runtime)
    original = session._parse

    def corrupt(data):
        result = original(data)
        result[field] = value
        if field == 'ids':
            result['count'] = len(value)
        return result

    monkeypatch.setattr(session, '_parse', corrupt)
    with pytest.raises(n.TokenizerError):
        session.encode('hello')
    assert session._child is None


def test_budgets_deadline_and_exception_cleanup(tmp_path):
    d, runtime = make_native(tmp_path)
    for policy in (e.Policy(max_calls=1), e.Policy(max_input_bytes=1),
                   e.Policy(max_output_bytes=1), e.Policy(max_ids=2)):
        session = None
        try:
            session = e.TokenIDSession(d, runtime, policy)
            with pytest.raises(n.TokenizerError):
                if policy.max_calls == 1:
                    session.encode('hello')
                session.encode('hello')
        except n.TokenizerError:
            assert policy.max_output_bytes == 1
        finally:
            if session:
                session.close()
    with pytest.raises(RuntimeError):
        with e.TokenIDSession(d, runtime) as session:
            child = session._child
            raise RuntimeError('caller')
    assert child.poll() is not None
    session = e.TokenIDSession(d, runtime, e.Policy(lifetime_seconds=0.5))
    child = session._child
    child.wait(timeout=2)
    with pytest.raises(n.TokenizerError):
        session.encode('x')


def test_isolation_probe(tmp_path, monkeypatch):
    d, runtime = make_native(tmp_path)
    canary = tmp_path / 'host-canary'
    canary.write_text('owned')
    listener = socket.socket()
    listener.bind(('127.0.0.1', 0))
    listener.listen()
    probe = tmp_path / 'probe.py'
    probe.write_text('import os, socket, sys\n'
                     f'path={str(canary)!r}; port={listener.getsockname()[1]}\n'
                     'assert not os.path.exists(path)\n'
                     's=socket.socket(); s.settimeout(0.2)\n'
                     'try: s.connect(("127.0.0.1", port)); sys.exit(1)\n'
                     'except OSError: pass\n'
                     'print(\'{"ready":"0.21.4"}\', flush=True)\n'
                     'sys.stdin.buffer.readline()\n')
    original = subprocess.Popen.__init__

    def intercept(child, argv, **kwargs):
        argv = list(argv)
        argv[argv.index('/worker.py') - 1] = str(probe)
        return original(child, argv, **kwargs)

    monkeypatch.setattr(subprocess.Popen, '__init__', intercept)
    try:
        with e.TokenIDSession(d, runtime) as session:
            assert session._child.poll() is None
    finally:
        listener.close()


def test_metadata_precedes_artifact_read(tmp_path, monkeypatch):
    d, runtime = make_native(tmp_path)

    def forbidden(*args):
        pytest.fail('artifact read before metadata validation')

    monkeypatch.setattr(n, '_read_artifact', forbidden)
    with pytest.raises(n.TokenizerError):
        e.TokenIDSession(replace(d, model_revision='bad'), runtime)


def test_dead_child_and_actual_request_timeout(tmp_path, monkeypatch):
    d, runtime = make_native(tmp_path)
    session = e.TokenIDSession(d, runtime)
    child = session._child
    child.kill()
    child.wait()
    with pytest.raises(n.TokenizerError):
        session.encode('hello')
    probe = tmp_path / 'hang.py'
    probe.write_text('import sys, time\nprint(\'{"ready":"0.21.4"}\', flush=True)\n'
                     'sys.stdin.buffer.readline()\ntime.sleep(20)\n')
    original = subprocess.Popen.__init__

    def intercept(child, argv, **kwargs):
        argv = list(argv)
        argv[argv.index('/worker.py') - 1] = str(probe)
        return original(child, argv, **kwargs)

    monkeypatch.setattr(subprocess.Popen, '__init__', intercept)
    session = e.TokenIDSession(d, runtime, e.Policy(request_seconds=0.2))
    child = session._child
    with pytest.raises(n.TokenizerError):
        session.encode('hello')
    assert child.poll() is not None


def test_actual_trailing_output_refused(tmp_path, monkeypatch):
    d, runtime = make_native(tmp_path)
    probe = tmp_path / 'extra.py'
    probe.write_text('import sys\nprint(\'{"ready":"0.21.4"}\', flush=True)\n'
                     'sys.stdin.buffer.readline()\n'
                     'sys.stdout.buffer.write(b"{}\\nextra\\n"); sys.stdout.buffer.flush()\n')
    original = subprocess.Popen.__init__

    def intercept(child, argv, **kwargs):
        argv = list(argv)
        argv[argv.index('/worker.py') - 1] = str(probe)
        return original(child, argv, **kwargs)

    monkeypatch.setattr(subprocess.Popen, '__init__', intercept)
    with e.TokenIDSession(d, runtime) as session:
        with pytest.raises(n.TokenizerError):
            session.encode('hello')


def test_real_id_limit_and_call_limit(tmp_path):
    d, runtime = make_native(tmp_path)
    with e.TokenIDSession(d, runtime) as session:
        assert len(session.encode('hello ' * 1022).ids) == 1024
        child = session._child
        with pytest.raises(n.TokenizerError):
            session.encode('hello ' * 1023)
        assert child.poll() is not None
    with e.TokenIDSession(d, runtime) as session:
        for _ in range(1024):
            assert session.encode('').ids == (1, 2)
        with pytest.raises(n.TokenizerError):
            session.encode('')


def test_owned_process_retained_until_retry_after_wait_failure(tmp_path, monkeypatch):
    import sys
    import tempfile

    child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(5)'],
                             stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    session = object.__new__(e.TokenIDSession)
    session._creator_pid = os.getpid()
    session._child = child
    session._tmp = tempfile.TemporaryDirectory(dir=tmp_path)
    private = Path(session._tmp.name)
    foreign = tmp_path / 'foreign'
    foreign.write_text('untouched')
    real_wait = child.wait
    monkeypatch.setattr(child, 'wait', lambda **kw: (_ for _ in ()).throw(OSError('wait')))
    try:
        with pytest.raises(OSError, match='wait'):
            session.close()
        assert session._child is child and private.exists()
        assert child.stdin.closed and child.stdout.closed
        monkeypatch.setattr(child, 'wait', real_wait)
        session.close()
        assert session._child is None and not private.exists()
        assert foreign.read_text() == 'untouched'
    finally:
        monkeypatch.setattr(child, 'wait', real_wait)
        if child.poll() is None:
            child.kill()
        child.wait(timeout=1)
        session.close()


def test_constructor_failure_preserves_original_and_pending_owner(tmp_path, monkeypatch):
    d, runtime = make_native(tmp_path)
    original_popen = subprocess.Popen.__init__
    children = []

    def spawn(child, *args, **kwargs):
        original_popen(child, *args, **kwargs)
        children.append((child, child.wait))
        monkeypatch.setattr(child, 'wait', lambda **kw: (_ for _ in ()).throw(OSError('wait')))

    monkeypatch.setattr(subprocess.Popen, '__init__', spawn)
    monkeypatch.setattr(e.TokenIDSession, '_read', lambda *a: (_ for _ in ()).throw(
        KeyboardInterrupt('startup')))
    try:
        with pytest.raises(KeyboardInterrupt, match='startup') as caught:
            e.TokenIDSession(d, runtime)
        owner = caught.value.cleanup_owner
        child, wait = children[0]
        assert owner._child is child and Path(owner._tmp.name).exists()
        monkeypatch.setattr(child, 'wait', wait)
        owner.close()
        assert owner._child is None and owner._tmp is None
    finally:
        for child, wait in children:
            monkeypatch.setattr(child, 'wait', wait)
            if child.poll() is None:
                child.kill()
            child.wait(timeout=1)


def test_stdout_interruption_retains_owner_and_preserves_exception(tmp_path):
    import sys
    import tempfile

    child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(5)'],
                             stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    session = object.__new__(e.TokenIDSession)
    session._creator_pid = os.getpid()
    session._child = child
    session._tmp = tempfile.TemporaryDirectory(dir=tmp_path)
    real_stdout = child.stdout

    class InterruptedOutput:
        def close(self):
            raise KeyboardInterrupt('stdout interrupted')

    child.stdout = InterruptedOutput()
    try:
        with pytest.raises(KeyboardInterrupt, match='stdout interrupted'):
            session.close()
        assert session._child is child and Path(session._tmp.name).exists()
        child.stdout = real_stdout
        session.close()
        assert child.stdin.closed and real_stdout.closed and session._tmp is None
    finally:
        child.stdout = real_stdout
        if child.poll() is None:
            child.kill()
        child.wait(timeout=1)
        session.close()


def test_operation_refusal_propagates_cleanup_interrupt_with_owner(tmp_path, monkeypatch):
    import sys
    import tempfile

    child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(5)'],
                             stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    session = object.__new__(e.TokenIDSession)
    session._creator_pid = os.getpid()
    session._child = child
    session._tmp = tempfile.TemporaryDirectory(dir=tmp_path)
    private = Path(session._tmp.name)
    foreign = tmp_path / 'foreign'
    foreign.write_text('safe')
    real_wait = child.wait
    calls = []

    def wait(**kwargs):
        calls.append(1)
        if len(calls) == 1:
            raise KeyboardInterrupt('cleanup interrupt')
        return real_wait(**kwargs)

    monkeypatch.setattr(child, 'wait', wait)
    try:
        with pytest.raises(KeyboardInterrupt, match='cleanup interrupt') as caught:
            session._refuse(ValueError('operation'))
        assert caught.value.cleanup_owner is session and session._child is child
        assert private.exists() and foreign.read_text() == 'safe'
        monkeypatch.setattr(child, 'wait', real_wait)
        session.close()
        assert not private.exists() and foreign.read_text() == 'safe'
    finally:
        monkeypatch.setattr(child, 'wait', real_wait)
        if child.poll() is None:
            child.kill()
        child.wait(timeout=1)
        session.close()


def test_later_interrupt_outranks_pipe_error_and_retry_drains(tmp_path, monkeypatch):
    import sys
    import tempfile

    child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(5)'],
                             stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    session = object.__new__(e.TokenIDSession)
    session._creator_pid = os.getpid()
    session._child = child
    session._tmp = tempfile.TemporaryDirectory(dir=tmp_path)
    private = Path(session._tmp.name)
    foreign = tmp_path / 'foreign'
    foreign.write_text('safe')
    stdin, real_wait = child.stdin, child.wait
    calls = []

    class BrokenInput:
        def close(self):
            raise OSError('pipe')

    def wait(**kwargs):
        calls.append(1)
        if len(calls) == 1:
            raise KeyboardInterrupt('wait interrupt')
        return real_wait(**kwargs)

    child.stdin = BrokenInput()
    monkeypatch.setattr(child, 'wait', wait)
    try:
        with pytest.raises(KeyboardInterrupt, match='wait interrupt'):
            session.close()
        assert session._child is child and private.exists() and child.stdout.closed
        child.stdin = stdin
        monkeypatch.setattr(child, 'wait', real_wait)
        session.close()
        assert stdin.closed and not private.exists() and foreign.read_text() == 'safe'
    finally:
        child.stdin = stdin
        monkeypatch.setattr(child, 'wait', real_wait)
        if child.poll() is None:
            child.kill()
        child.wait(timeout=1)
        session.close()


@pytest.mark.parametrize('diagnostic_failure', [ValueError('note'), KeyboardInterrupt('note')])
@pytest.mark.parametrize('cleanup', [ValueError('close'), KeyboardInterrupt('close')])
def test_refuse_selects_primary_before_hostile_diagnostics(diagnostic_failure, cleanup):
    class Hostile(BaseException):
        def add_note(self, note):
            raise diagnostic_failure

        def __setattr__(self, name, value):
            raise diagnostic_failure

    obj = object.__new__(e.TokenIDSession)
    obj._creator_pid = os.getpid()
    obj._child, obj._tmp = object(), object()
    primary = Hostile('primary')

    def close():
        raise cleanup

    obj.close = close
    with pytest.raises(Hostile) as caught:
        obj._refuse(primary)
    assert caught.value is primary and obj._child is not None and obj._tmp is not None


@pytest.mark.parametrize('diagnostic_failure', [ValueError('attr'), KeyboardInterrupt('attr')])
def test_refuse_cleanup_interrupt_with_hostile_attributes(diagnostic_failure):
    class Hostile(KeyboardInterrupt):
        def add_note(self, note):
            raise diagnostic_failure

        def __setattr__(self, name, value):
            raise diagnostic_failure

    obj = object.__new__(e.TokenIDSession)
    obj._creator_pid = os.getpid()
    obj._child, obj._tmp = object(), object()
    cleanup = Hostile('cleanup')
    obj.close = lambda: (_ for _ in ()).throw(cleanup)
    with pytest.raises(Hostile) as caught:
        obj._refuse(ValueError('primary'))
    assert caught.value is cleanup and obj._child is not None and obj._tmp is not None


@pytest.mark.parametrize('body,cleanup,selected', [
    (KeyboardInterrupt('body'), ValueError('cleanup'), 'body'),
    (KeyboardInterrupt('body'), KeyboardInterrupt('cleanup'), 'body'),
    (ValueError('body'), KeyboardInterrupt('cleanup'), 'cleanup'),
    (None, ValueError('cleanup'), 'cleanup'),
])
def test_native_context_exception_priority(body, cleanup, selected):
    obj = object.__new__(e.TokenIDSession)
    obj._creator_pid = os.getpid()
    obj._child, obj._tmp = object(), object()
    obj.close = lambda: (_ for _ in ()).throw(cleanup)
    expected = body if selected == 'body' else cleanup
    with pytest.raises(type(expected)) as caught:
        with obj:
            if body is not None:
                raise body
    assert caught.value is expected
    assert obj._child is not None and obj._tmp is not None


@pytest.mark.parametrize('diagnostic_failure', [ValueError('note'), KeyboardInterrupt('note')])
def test_context_hostile_diagnostics_keep_original(diagnostic_failure):
    class Hostile(BaseException):
        def add_note(self, note):
            raise diagnostic_failure

        def __setattr__(self, name, value):
            raise diagnostic_failure

    body = Hostile('body')
    obj = object.__new__(e.TokenIDSession)
    obj._creator_pid = os.getpid()
    obj._child, obj._tmp = object(), object()
    obj.close = lambda: (_ for _ in ()).throw(KeyboardInterrupt('cleanup'))
    with pytest.raises(Hostile) as caught:
        with obj:
            raise body
    assert caught.value is body and obj._child is not None and obj._tmp is not None
