"""Query policy and lifecycle checks; explicitly fake the isolated session boundary."""
import os
from dataclasses import FrozenInstanceError

import pytest

from slaif_raggedized_helper import query_embedding as q


@pytest.fixture
def fake(monkeypatch):
    class Session:
        def __init__(self, *args, **kwargs):
            self.calls = []
            self.closed = 0
        def _validate_state(self):
            pass
        def __enter__(self):
            return self
        def close(self):
            self.closed += 1
        def encode(self, texts):
            self.calls.append(texts)
            raise ValueError('private input')
    monkeypatch.setattr(q.isolated_cpu_embedding, 'IsolatedCPUEmbeddingSession', Session)
    return q.ResidentQueryEncoder(*([None] * 7))


@pytest.mark.parametrize('text', [None, True, b'hello', '', ' \n\t', '\ud800', 'x' * 8193])
def test_raw_refusal_before_dispatch(fake, text):
    with fake:
        with pytest.raises(q.QueryRefused, match='refused'):
            fake.encode_query(text)
        assert fake.cleanup_owner.calls == []
        assert fake._state == 'open'


def test_sticky_failure_and_lifecycle(fake):
    with pytest.raises(q.QueryRefused):
        fake.encode_query('valid')
    with fake:
        with pytest.raises(q.QueryRefused):
            fake.__enter__()
        with pytest.raises(q.QueryRefused) as caught:
            fake.encode_query(' private ')
        assert 'private' not in str(caught.value)
        assert fake.cleanup_owner.calls == [[' private ']]
        with pytest.raises(q.QueryRefused):
            fake.encode_query('second')
    with pytest.raises(q.QueryRefused):
        fake.encode_query('later')


def test_busy_and_fork_refusal(fake, monkeypatch):
    fake._lock.acquire()
    try:
        with pytest.raises(q.QueryRefused):
            fake.close()
    finally:
        fake._lock.release()
    monkeypatch.setattr(q.os, 'getpid', lambda: os.getppid())
    with pytest.raises(q.QueryRefused):
        fake.close()


def test_result_frozen():
    result = q.QueryEmbedding(b'', '', '', '', '', b'', '', '')
    with pytest.raises(FrozenInstanceError):
        result.payload = b'other'


def test_interrupt_identity_and_owner(fake):
    class Uncooperative(BaseException):
        def __setattr__(self, name, value):
            raise RuntimeError('cannot annotate')
    original = Uncooperative()
    def fail(_):
        raise original
    fake.cleanup_owner.encode = fail
    with fake:
        with pytest.raises(Uncooperative) as caught:
            fake.encode_query('hello')
        assert caught.value is original
        assert fake.cleanup_owner.closed == 1


def test_result_validation_with_fake_session(fake, monkeypatch):
    import hashlib
    import struct
    from dataclasses import replace
    from types import SimpleNamespace
    from slaif_raggedized_helper import embedding_vectors as vectors, isolated_cpu_embedding as iso

    s = fake.cleanup_owner
    row = (1.0,) + (0.0,) * 1023
    payload = struct.pack('<1024f', *row)
    v = vectors.NormalizedVectors((row,), payload, hashlib.sha256(payload).hexdigest(),
                                  vectors.POLICY_ID)
    definition = SimpleNamespace(fingerprint=lambda: 'definition')
    s.definition = definition
    s.space = SimpleNamespace(space_id='space', definition_fingerprint='definition')
    s.execution_record = b'record'
    s.execution_fingerprint = 'actual'
    s.intended_execution_fingerprint = 'intended'
    s._worker_identity = lambda: 'worker'
    s._receipt = lambda receipt, text: None
    monkeypatch.setattr(q, 'EmbeddingExecution', lambda **kw: SimpleNamespace(
        fingerprint=lambda: 'intended'))
    monkeypatch.setattr(q.cpu_execution_contract, '_validate', lambda _: {
        'space': 'space', 'definition': 'definition', 'worker': 'worker'})
    monkeypatch.setattr(q, 'fingerprint', lambda _: 'actual')
    good = iso.EncodedBatch(v, ('receipt',), 'space', 'definition', 'intended', b'record', 'actual')
    variants = [
        replace(good, space_id='other'), replace(good, definition_fingerprint='other'),
        replace(good, execution_fingerprint='other'), replace(good, execution_record=b'other'),
        replace(good, intended_execution_fingerprint='other'),
        replace(good, vectors=replace(v, sha256='0' * 64)),
        replace(good, vectors=replace(v, policy_id='other')),
        replace(good, vectors=replace(v, rows=((True,) + row[1:],))),
        replace(good, vectors=replace(v, rows=((float('nan'),) + row[1:],))),
        replace(good, vectors=replace(v, rows=((0.5,) + row[1:],))),
        replace(good, vectors=replace(v, payload=b'\0' * 4096)),
        replace(good, receipts=()),
    ]
    fake.__enter__()
    s.encode = lambda _: good
    assert fake.encode_query(' first ').payload == payload
    for variant in variants:
        fake._state = 'open'  # each independent case uses the explicit fake boundary
        s.encode = lambda _, item=variant: item
        with pytest.raises(q.QueryRefused):
            fake.encode_query('secret')
        assert fake._state == 'refused'
    fake.close()


def test_policy_and_source_mutation_refused_before_dispatch(fake, monkeypatch):
    fake.__enter__()
    monkeypatch.setattr(q, 'POLICY_ID', 'changed')
    with pytest.raises(q.QueryRefused):
        fake.encode_query('hello')
    assert fake.cleanup_owner.calls == []
    monkeypatch.undo()
    fake._state = 'open'
    monkeypatch.setattr(q, '_source_hash', lambda: 'changed')
    with pytest.raises(q.QueryRefused):
        fake.encode_query('hello')
    assert fake.cleanup_owner.calls == []


def test_actual_pending_owner_and_uncooperative_cleanup_interrupt(tmp_path):
    from pathlib import Path
    from slaif_raggedized_helper import native_tokenizers
    from test_cpu_embedding_backend import make_tree

    _, raw, inv, definition, token = make_tree(tmp_path / 'tree')
    runtime = native_tokenizers.Runtime(Path('/runtime'), Path('/packages'), 'python3.12')
    encoder = q.ResidentQueryEncoder(raw, tmp_path / 'tree', definition, token,
                                     inv.inventory_id, runtime, runtime)

    class Uncooperative(BaseException):
        def __setattr__(self, name, value):
            raise RuntimeError('attributes rejected')

    interrupt = Uncooperative()
    class Stage:
        def __exit__(self, *args):
            raise interrupt

    actual = encoder.cleanup_owner
    stage = Stage()
    actual._stage = stage
    with pytest.raises(Uncooperative) as caught:
        encoder.close()
    assert caught.value is interrupt
    assert encoder.cleanup_owner is actual and actual._stage is stage and actual._stage_failed


def test_context_cleanup_interrupt_priority(fake):
    interrupt = KeyboardInterrupt('cleanup')
    def fail():
        raise interrupt
    fake.cleanup_owner.close = fail
    with pytest.raises(KeyboardInterrupt) as caught:
        with fake:
            raise ValueError('body')
    assert caught.value is interrupt


def test_actual_session_failure_preserves_original_uncooperative_interrupt(tmp_path, monkeypatch):
    from pathlib import Path
    from slaif_raggedized_helper import native_tokenizers
    from test_cpu_embedding_backend import make_tree

    _, raw, inv, definition, token = make_tree(tmp_path / 'tree')
    runtime = native_tokenizers.Runtime(Path('/runtime'), Path('/packages'), 'python3.12')
    encoder = q.ResidentQueryEncoder(raw, tmp_path / 'tree', definition, token,
                                     inv.inventory_id, runtime, runtime)
    actual = encoder.cleanup_owner

    class Uncooperative(BaseException):
        def __setattr__(self, name, value):
            raise RuntimeError('attributes rejected')

    original = Uncooperative()
    class Stage:
        def __exit__(self, *args):
            raise ValueError('cleanup')
    actual._stage = Stage()
    encoder._state = 'open'
    def fail(_):
        try:
            raise original
        except BaseException as error:
            actual._fail(error)
    monkeypatch.setattr(actual, 'encode', fail)
    with pytest.raises(Uncooperative) as caught:
        encoder.encode_query('hello')
    assert caught.value is original
    assert encoder.cleanup_owner is actual and actual._stage is not None


def test_earlier_handled_interrupt_not_resurrected(fake):
    with fake:
        old = KeyboardInterrupt('earlier')
        try:
            raise old
        except KeyboardInterrupt:
            with pytest.raises(q.QueryRefused):
                fake.encode_query('hello')
