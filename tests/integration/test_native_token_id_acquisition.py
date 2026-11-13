"""Actual native worker ownership across interrupted acquisition and fork."""
import importlib.util
import json
import os
import select
import subprocess
from pathlib import Path

import pytest

from slaif_raggedized_helper import embedding_tokenizer as e
from slaif_raggedized_helper import native_tokenizers as n

spec = importlib.util.spec_from_file_location(
    'token_id_fixture', Path(__file__).parents[1] / 'unit/test_embedding_tokenizer.py')
fixture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixture)


class Stop(BaseException):
    def add_note(self, note):
        raise RuntimeError('hostile note')

    def __setattr__(self, name, value):
        raise RuntimeError('hostile attribute')


@pytest.mark.parametrize('pending', [False, True])
def test_actual_ready_before_return_retained_or_reaped(tmp_path, monkeypatch, pending):
    definition, runtime = fixture.make_native(tmp_path)
    original = subprocess.Popen.__init__
    stop = Stop('same stop')
    captured = []
    def intercept(child, *args, **kwargs):
        original(child, *args, **kwargs)
        assert select.select([child.stdout], [], [], 5)[0]
        assert json.loads(os.read(child.stdout.fileno(), 256)) == {'ready': '0.21.4'}
        captured.append((child, child.wait))
        if pending:
            monkeypatch.setattr(child, 'wait', lambda **kw: (_ for _ in ()).throw(OSError('wait')))
        raise stop
    before = set(e._OWNERS)
    with monkeypatch.context() as patch:
        patch.setattr(subprocess.Popen, '__init__', intercept)
        with pytest.raises(Stop) as caught:
            e.TokenIDSession(definition, runtime)
        assert caught.value is stop
        child, wait = captured[0]
        owners = e._OWNERS - before
        if pending:
            assert len(owners) == 1
            owner = owners.pop()
            assert owner._child is child and Path(owner._tmp.name).exists()
            monkeypatch.setattr(child, 'wait', wait)
            owner.close()
            assert owner not in e._OWNERS and owner._tmp is None
        else:
            assert child.poll() is not None and not owners
    assert child.poll() is not None



def test_actual_started_initializer_fault_reaps(tmp_path, monkeypatch):
    definition, runtime = fixture.make_native(tmp_path)
    original = subprocess.Popen.__init__
    stop = Stop('after start')
    captured = []
    before = set(e._OWNERS)
    def intercept(child, *args, **kwargs):
        original(child, *args, **kwargs)
        captured.append(child)
        raise stop
    monkeypatch.setattr(subprocess.Popen, '__init__', intercept)
    with pytest.raises(Stop) as caught:
        e.TokenIDSession(definition, runtime)
    assert caught.value is stop and len(captured) == 1
    assert captured[0].poll() is not None and e._OWNERS == before


def test_no_start_metadata_refusal_releases_owner(tmp_path):
    definition, runtime = fixture.make_native(tmp_path)
    before = set(e._OWNERS)
    from dataclasses import replace
    with pytest.raises(n.TokenizerError):
        e.TokenIDSession(replace(definition, sha256='bad'), runtime)
    assert e._OWNERS == before



def test_initializer_interrupted_before_start(tmp_path, monkeypatch):
    definition, runtime = fixture.make_native(tmp_path)
    stop = Stop('before init')
    before = set(e._OWNERS)
    captured = []
    def intercept(child, *args, **kwargs):
        captured.append(child)
        raise stop
    monkeypatch.setattr(subprocess.Popen, '__init__', intercept)
    with pytest.raises(Stop) as caught:
        e.TokenIDSession(definition, runtime)
    assert caught.value is stop and len(captured) == 1
    assert not hasattr(captured[0], '_waitpid_lock') and e._OWNERS == before


def test_fork_cannot_mutate_parent_owner(tmp_path):
    definition, runtime = fixture.make_native(tmp_path)
    with e.TokenIDSession(definition, runtime) as session:
        child = session._child
        artifact = Path(session._tmp.name)
        pid = os.fork()
        if pid == 0:
            try:
                if session._tmp._finalizer.alive:
                    os._exit(3)
                for operation in (lambda: session.encode('hello'), session.close,
                                  lambda: session.__exit__(None, None, None)):
                    try:
                        operation()
                    except n.TokenizerError:
                        continue
                    os._exit(1)
                os._exit(0)
            except BaseException:
                os._exit(2)
        _, status = os.waitpid(pid, 0)
        assert os.waitstatus_to_exitcode(status) == 0
        assert artifact.exists() and session._tmp._finalizer.alive and child.poll() is None
        assert session.encode('hello').ids == (1, 3, 2)


def test_actual_reinitialization_refused_before_owner_mutation(tmp_path):
    definition, runtime = fixture.make_native(tmp_path)
    session = e.TokenIDSession(definition, runtime)
    child, private = session._child, session._tmp
    try:
        with pytest.raises(n.TokenizerError):
            session.__init__(definition, runtime)
        assert session._child is child and session._tmp is private
        assert session in e._OWNERS and child.poll() is None
        assert session.encode('hello').ids == (1, 3, 2)
    finally:
        session.close()
    with pytest.raises(n.TokenizerError):
        session.__init__(definition, runtime)
    assert session._child is None and session._tmp is None and session not in e._OWNERS


def test_fork_context_preserves_body_interrupt_and_refuses_reinit(tmp_path):
    definition, runtime = fixture.make_native(tmp_path)
    with e.TokenIDSession(definition, runtime) as session:
        child, private = session._child, Path(session._tmp.name)
        pid = os.fork()
        if pid == 0:
            try:
                primary = Stop('body')
                try:
                    session.__init__(definition, runtime)
                except n.TokenizerError:
                    pass
                else:
                    os._exit(1)
                # Returning False preserves the original body exception in a with statement.
                try:
                    with session:
                        raise primary
                except Stop as caught:
                    os._exit(0 if caught is primary else 2)
                os._exit(3)
            except BaseException:
                os._exit(4)
        _, status = os.waitpid(pid, 0)
        assert os.waitstatus_to_exitcode(status) == 0
        assert private.exists() and child.poll() is None
        assert session.encode('hello').ids == (1, 3, 2)
