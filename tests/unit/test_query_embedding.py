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


@pytest.mark.parametrize('text', [None, True, b'hello', '', ' \n\t', '\ud800', 'x' * 8193],
                         ids=("none", "bool", "bytes", "empty", "whitespace", "lone-surrogate",
                              "oversize"))
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


def _admitted_encoder(tmp_path, monkeypatch):
    import hashlib
    import json
    import time
    from pathlib import Path
    from slaif_raggedized_helper import (
        cpu_embedding_worker as cpu, embedding_tokenizer as tokenizer, native_tokenizers)
    from test_cpu_embedding_backend import make_tree

    _, raw, inv, definition, token = make_tree(tmp_path / 'tree')
    runtime = native_tokenizers.Runtime(Path('/runtime'), Path('/packages'), 'python3.12')
    calls = []

    class Native:
        # Controlled delegation boundary: the native tokenizer session child.
        def __init__(self, token_definition, native_runtime):
            self._policy = tokenizer.Policy()
            self._definition = token_definition
            self._child = None
            self._deadline = time.monotonic() + 600
            self._calls = 0
            self._input = 0
            self._output = 0

        def encode(self, text):
            calls.append('native')
            d = self._definition
            digest = hashlib.sha256(
                json.dumps([text, None], ensure_ascii=True, separators=(',', ':')).encode()
            ).hexdigest()
            return tokenizer.TokenIDReceipt(
                (1, 2), 2, d.sha256, d.backend_version, d.role, d.model_revision,
                d.preprocessing, digest, 'a' * 32)

        def close(self):
            calls.append('native-close')

    class Worker:
        # Controlled delegation boundary: the CPU embedding worker child.
        vocab_size = 20
        _child = None

        def __init__(self, manifest_bytes, path, definition, token_definition,
                     inventory, cpu_runtime, policy):
            from slaif_raggedized_helper import embedding_space

            self.space = embedding_space.admit(
                manifest_bytes, path, definition, token_definition, inventory)
            self.policy = policy
            self.profile = 'a' * 64
            self.code_fingerprint = 'b' * 64
            self.policy_fingerprint = cpu._policy_identity(policy)

        def forward_cls(self, rows):
            calls.append('forward')
            return ((1.0,) + (0.0,) * 1023,)

        def close(self):
            calls.append('worker-close')

    monkeypatch.setattr(tokenizer, 'TokenIDSession', Native)
    monkeypatch.setattr(cpu, 'CPUEmbeddingWorker', Worker)
    encoder = q.ResidentQueryEncoder(raw, tmp_path / 'tree', definition, token,
                                     inv.inventory_id, runtime, runtime)
    encoder.__enter__()
    s = encoder.cleanup_owner
    assert s._state == 'open' and encoder._state == 'open'
    assert s.execution_record == s._record_snapshot
    assert s.execution_fingerprint == s._fingerprint_snapshot
    assert s._identity == s._worker_identity()
    return encoder, s, calls


def _expected_tuple(s):
    return (s.space.space_id, s.definition.fingerprint(), q._POLICY_DIGEST,
            s.execution_fingerprint[7:])


def test_admitted_identity_reaches_session_encode_once(tmp_path, monkeypatch):
    import hashlib
    import json
    import struct

    encoder, s, calls = _admitted_encoder(tmp_path, monkeypatch)
    expected = _expected_tuple(s)
    real_encode = s.encode

    def traced(texts):
        calls.append('session-encode')
        return real_encode(texts)

    real_identity = s._worker_identity

    def gate():
        calls.append('gate')
        return real_identity()

    s.encode, s._worker_identity = traced, gate
    try:
        result = encoder._encode_expected_identity('hello', expected)
    finally:
        s.encode, s._worker_identity = real_encode, real_identity
    assert calls == ['gate', 'session-encode', 'native', 'forward', 'gate', 'gate']
    assert type(result) is q.QueryEmbedding
    assert (result.space_id, result.definition_fingerprint, result.query_policy_id,
            result.execution_fingerprint) == (
                expected[0], expected[1], expected[2], 'sha256:' + expected[3])
    assert result.execution_record == s.execution_record
    assert result.intended_execution_fingerprint == s.intended_execution_fingerprint
    assert len(result.payload) == 4096
    assert hashlib.sha256(result.payload).hexdigest() == result.payload_sha256
    assert struct.unpack('<1024f', result.payload)[0] == 1.0
    record = json.loads(s.execution_record)
    assert record['bridge'] == q.cpu_execution_contract._bridge()
    assert record['worker'] == real_identity()
    assert encoder.cleanup_owner is s and s._state == 'open' and encoder._state == 'open'


@pytest.mark.parametrize('field', [0, 1, 2, 3],
                         ids=('space', 'definition', 'policy', 'execution'))
def test_wrong_same_shape_identity_refused_before_session_encode(tmp_path, monkeypatch, field):
    encoder, s, calls = _admitted_encoder(tmp_path, monkeypatch)
    expected = list(_expected_tuple(s))
    if field == 0:
        expected[0] = ('c' if expected[0][0] != 'c' else 'd') + expected[0][1:]
    elif field == 1:
        expected[1] = 'sha256:' + 'f' * 64
    elif field == 2:
        expected[2] = 'f' * 64
    else:
        expected[3] = expected[3][:-1] + ('0' if expected[3][-1] != '0' else '1')
    wrong = tuple(expected)
    assert wrong != _expected_tuple(s)
    real_encode = s.encode

    def counted(texts):
        calls.append('session-encode')
        return real_encode(texts)

    s.encode = counted
    try:
        with pytest.raises(q.QueryRefused, match='refused'):
            encoder._encode_expected_identity('hello', wrong)
        assert calls == ['native-close', 'worker-close']
        assert encoder._state == 'refused' and encoder.cleanup_owner is s
        with pytest.raises(q.QueryRefused):
            encoder._encode_expected_identity('hello', _expected_tuple(s))
        assert calls == ['native-close', 'worker-close']
    finally:
        s.encode = real_encode


@pytest.mark.parametrize('field', ['space', 'profile', 'code', 'policy'],
                         ids=('worker-space', 'worker-profile', 'worker-code', 'worker-policy'))
def test_changed_live_worker_identity_refused_before_session_encode(
        tmp_path, monkeypatch, field):
    from slaif_raggedized_helper import embedding_space

    encoder, s, calls = _admitted_encoder(tmp_path, monkeypatch)
    expected = _expected_tuple(s)
    if field == 'space':
        s._worker.space = embedding_space.AdmittedSpace(
            'e' * 64, s.definition.fingerprint(), 'd' * 64, 'identity', 1024, 'cls', True,
            'f' * 64)
    elif field == 'profile':
        s._worker.profile = 'e' * 64
    elif field == 'code':
        s._worker.code_fingerprint = 'e' * 64
    else:
        s._worker.policy_fingerprint = 'e' * 64
    real_encode = s.encode

    def counted(texts):
        calls.append('session-encode')
        return real_encode(texts)

    s.encode = counted
    try:
        with pytest.raises(q.QueryRefused, match='refused'):
            encoder._encode_expected_identity('hello', expected)
        assert calls == ['native-close', 'worker-close']
        assert encoder._state == 'refused' and encoder.cleanup_owner is s
    finally:
        s.encode = real_encode


def test_coherent_record_fingerprint_drift_refused_before_session_encode(tmp_path, monkeypatch):
    encoder, s, calls = _admitted_encoder(tmp_path, monkeypatch)
    s._worker.code_fingerprint = 'e' * 64
    drifted_identity = s._worker_identity()
    s.execution_record, s.execution_fingerprint = q.cpu_execution_contract._record(
        s.space, s.definition, s._token_definition, drifted_identity, s._tokenizer._policy)
    expected = _expected_tuple(s)
    assert expected[3] == s.execution_fingerprint[7:]
    real_encode = s.encode

    def counted(texts):
        calls.append('session-encode')
        return real_encode(texts)

    s.encode = counted
    try:
        with pytest.raises(q.QueryRefused, match='refused'):
            encoder._encode_expected_identity('hello', expected)
        assert calls == ['native-close', 'worker-close']
        assert 'session-encode' not in calls and 'native' not in calls and 'forward' not in calls
        assert encoder._state == 'refused' and encoder.cleanup_owner is s
    finally:
        s.encode = real_encode


def test_changed_live_worker_policy_refused_before_session_encode(tmp_path, monkeypatch):
    import dataclasses
    from slaif_raggedized_helper import cpu_embedding_worker as cpu

    encoder, s, calls = _admitted_encoder(tmp_path, monkeypatch)
    expected = _expected_tuple(s)
    s._worker.policy = dataclasses.replace(
        s._worker.policy, max_rows=s._worker.policy.max_rows + 1)
    assert s._worker.policy_fingerprint == s._identity['policy']
    assert cpu._policy_identity(s._worker.policy) != s._identity['policy']
    real_encode = s.encode

    def counted(texts):
        calls.append('session-encode')
        return real_encode(texts)

    s.encode = counted
    try:
        with pytest.raises(q.QueryRefused, match='refused'):
            encoder._encode_expected_identity('hello', expected)
        assert calls == ['native-close', 'worker-close']
        assert 'session-encode' not in calls and 'native' not in calls and 'forward' not in calls
        assert encoder._state == 'refused' and encoder.cleanup_owner is s
    finally:
        s.encode = real_encode


def test_none_expected_refused_and_owner_stays_usable(tmp_path, monkeypatch):
    encoder, s, calls = _admitted_encoder(tmp_path, monkeypatch)
    expected = _expected_tuple(s)
    real_encode = s.encode

    def counted(texts):
        calls.append('session-encode')
        return real_encode(texts)

    s.encode = counted
    try:
        with pytest.raises(q.QueryRefused, match='refused'):
            encoder._encode_expected_identity('synthetic', None)
        assert calls == []
        result = encoder._encode_expected_identity('hello', expected)
        assert type(result) is q.QueryEmbedding
        assert calls == ['session-encode', 'native', 'forward']
        calls.clear()
        legacy = encoder.encode_query('again')
        assert type(legacy) is q.QueryEmbedding
        assert calls == ['session-encode', 'native', 'forward']
    finally:
        s.encode = real_encode


def test_permitted_encode_then_tampered_result_refused(tmp_path, monkeypatch):
    from dataclasses import replace

    encoder, s, calls = _admitted_encoder(tmp_path, monkeypatch)
    expected = _expected_tuple(s)
    real_encode = s.encode

    def first(texts):
        calls.append('session-encode')
        return real_encode(texts)

    s.encode = first
    try:
        assert encoder._encode_expected_identity('hello', expected) is not None
        calls.clear()

        def tampered(texts):
            calls.append('session-encode')
            last = '0' if s.execution_fingerprint[-1] != '0' else '1'
            return replace(real_encode(texts),
                           execution_fingerprint='sha256:' + last * 64)

        s.encode = tampered
        with pytest.raises(q.QueryRefused, match='refused'):
            encoder._encode_expected_identity('hello', expected)
    finally:
        s.encode = real_encode
    assert calls == ['session-encode', 'native', 'forward', 'native-close', 'worker-close']
    assert encoder._state == 'refused' and encoder.cleanup_owner is s


def test_permitted_encode_receipt_fault_refused(tmp_path, monkeypatch):
    from dataclasses import replace

    encoder, s, calls = _admitted_encoder(tmp_path, monkeypatch)
    expected = _expected_tuple(s)
    real_encode = s.encode
    real_native = s._tokenizer.encode

    def traced(texts):
        calls.append('session-encode')
        return real_encode(texts)

    def faulty(text):
        receipt = real_native(text)
        if text == 'fault':
            return replace(receipt, input_sha256='0' * 64)
        return receipt

    s.encode, s._tokenizer.encode = traced, faulty
    try:
        with pytest.raises(q.QueryRefused, match='refused'):
            encoder._encode_expected_identity('fault', expected)
    finally:
        s.encode = real_encode
        if s._tokenizer is not None:
            s._tokenizer.encode = real_native
    assert calls == ['session-encode', 'native', 'native-close', 'worker-close']
    assert encoder._state == 'refused' and encoder.cleanup_owner is s


@pytest.mark.parametrize('expected', [
    ('a' * 64, 'sha256:' + 'b' * 64, 'c' * 64, 'd' * 64, 'e' * 64),
    ('a' * 64, 'sha256:' + 'b' * 64, 'c' * 64),
    ('A' * 64, 'sha256:' + 'b' * 64, 'c' * 64, 'd' * 64),
    ('a' * 63, 'sha256:' + 'b' * 64, 'c' * 64, 'd' * 64),
    ('a' * 64, 'b' * 64, 'c' * 64, 'd' * 64),
    ('a' * 64, 'SHA256:' + 'b' * 64, 'c' * 64, 'd' * 64),
    ('a' * 64, 'sha256:' + 'b' * 64, 'c' * 64, 123),
    ('a' * 64, 'sha256:' + 'b' * 64, 'c' * 64, b'd' * 64),
    ['a' * 64, 'sha256:' + 'b' * 64, 'c' * 64, 'd' * 64],
    None,
], ids=('five-fields', 'three-fields', 'upper-space', 'short-space', 'bare-definition',
        'upper-prefix', 'int-execution', 'bytes-execution', 'list-not-tuple', 'none'))
def test_malformed_expected_identity_refused_without_dispatch(fake, expected):
    fake.__enter__()
    try:
        with pytest.raises(q.QueryRefused, match='refused'):
            fake._encode_expected_identity('hello', expected)
        assert fake.cleanup_owner.calls == []
        assert fake.cleanup_owner.closed == 0
        assert fake._state == 'open'
        with pytest.raises(q.QueryRefused):
            fake._encode_expected_identity('hello', expected)
        assert fake.cleanup_owner.calls == [] and fake.cleanup_owner.closed == 0
    finally:
        fake.close()


@pytest.mark.parametrize('text', [None, True, b'hello', '', ' \n\t', '\ud800', 'x' * 8193],
                         ids=("none", "bool", "bytes", "empty", "whitespace", "lone-surrogate",
                              "oversize"))
def test_expected_entry_raw_refusal_before_dispatch(fake, text):
    fake.__enter__()
    try:
        with pytest.raises(q.QueryRefused, match='refused') as caught:
            fake._encode_expected_identity(text, ('a' * 64, 'sha256:' + 'b' * 64, 'c' * 64,
                                                  'd' * 64))
        assert 'hello' not in str(caught.value)
        assert fake.cleanup_owner.calls == []
        assert fake._state == 'open'
    finally:
        fake.close()


def test_expected_entry_text_refusal_keeps_path_open(tmp_path, monkeypatch):
    encoder, s, calls = _admitted_encoder(tmp_path, monkeypatch)
    expected = _expected_tuple(s)
    with pytest.raises(q.QueryRefused, match='refused'):
        encoder._encode_expected_identity('', expected)
    assert calls == [] and s._state == 'open' and encoder._state == 'open'
    result = encoder._encode_expected_identity('hello', expected)
    assert type(result) is q.QueryEmbedding and calls == ['native', 'forward']


def test_expected_entry_busy_and_fork_refusal(fake, monkeypatch):
    fake.__enter__()
    try:
        identity = ('a' * 64, 'sha256:' + 'b' * 64, 'c' * 64, 'd' * 64)
        fake._lock.acquire()
        try:
            with pytest.raises(q.QueryRefused):
                fake._encode_expected_identity('hello', identity)
        finally:
            fake._lock.release()
        monkeypatch.setattr(q.os, 'getpid', lambda: os.getppid())
        with pytest.raises(q.QueryRefused):
            fake._encode_expected_identity('hello', identity)
        monkeypatch.undo()
        assert fake.cleanup_owner.calls == [] and fake._state == 'open'
    finally:
        fake.close()


def test_expected_entry_gate_interrupt_preserved_and_lock_released(tmp_path, monkeypatch):
    encoder, s, calls = _admitted_encoder(tmp_path, monkeypatch)
    expected = _expected_tuple(s)
    interrupt = KeyboardInterrupt('gate')

    def hostile():
        raise interrupt

    s._worker_identity = hostile
    with pytest.raises(KeyboardInterrupt) as caught:
        encoder._encode_expected_identity('hello', expected)
    assert caught.value is interrupt
    assert encoder._state == 'refused'
    encoder.close()
    assert s._state == 'closed' and calls == ['native-close', 'worker-close']
