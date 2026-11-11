"""Session isolation and count regressions with owned native fixtures."""
from dataclasses import replace

import pytest

from slaif_raggedized_helper import native_tokenizers as n
from slaif_raggedized_helper.tokenizer_session import Session
from test_native_tokenizers import make_native


def test_sessions_reuse_and_bind(tmp_path):
    paths, runtime, definition = make_native(tmp_path)
    body = definition(paths[0], 'bge_body')
    representation = definition(paths[0], 'bge_representation')
    pair = definition(paths[1], 'reranker_pair')
    with Session((body, representation, pair), runtime) as session:
        child = session._child
        for i in range(30):
            text = 'hello ' * i
            actual = session.count('bge_body', text)
            assert actual.count == i + 2
            assert actual == n.count(body, runtime, text)
        assert session.count('bge_representation', '').count == 2
        assert session.count('reranker_pair', '', '').count == 4
        assert session._child is child
    assert child.poll() is not None
    session.close()
    with pytest.raises(n.TokenizerError):
        session.count('bge_body', 'x')


def test_invalid_input_closes_session(tmp_path):
    paths, runtime, definition = make_native(tmp_path)
    body = definition(paths[0])
    with pytest.raises(n.TokenizerError):
        Session((replace(body, sha256='0' * 64),), runtime)
    session = Session((body,), runtime)
    child = session._child
    with pytest.raises(n.TokenizerError, match='session refused'):
        session.count('bge_body', 'private canary', '')
    assert child.poll() is not None


@pytest.mark.parametrize('response', [
    b'\xff', b'{}', b'{"nonce":"x","nonce":"y"}', b'{"count":NaN}',
    b'{"nonce":"wrong","role":"bge_body","artifact":0,"count":1,'
    b'"digest":"wrong","version":"0.21.4"}',
    b'{"extra":1}', b'x' * 4097,
])
def test_malformed_response_closes_worker(tmp_path, monkeypatch, response):
    paths, runtime, definition = make_native(tmp_path)
    session = Session((definition(paths[0]),), runtime)
    child = session._child
    monkeypatch.setattr(session, '_read', lambda deadline: response)
    with pytest.raises(n.TokenizerError, match='tokenizer session refused'):
        session.count('bge_body', 'private canary')
    assert child.poll() is not None


def test_dead_worker_and_exhaustion(tmp_path):
    paths, runtime, definition = make_native(tmp_path)
    body = definition(paths[0])
    session = Session((body,), runtime)
    child = session._child
    child.kill()
    child.wait()
    with pytest.raises(n.TokenizerError):
        session.count('bge_body', 'x')
    for attr, value in (('_calls', 16384), ('_input', 16_000_000),
                        ('_output', 4_000_000)):
        session = Session((body,), runtime)
        child = session._child
        setattr(session, attr, value)
        with pytest.raises(n.TokenizerError):
            session.count('bge_body', 'x')
        assert child.poll() is not None


@pytest.mark.parametrize(('field', 'value'), [
    ('nonce', 'wrong'), ('role', 'wrong'), ('artifact', True), ('digest', 'wrong'),
    ('version', 'wrong'), ('count', True), ('count', 200001), ('extra', 1),
])
def test_misbound_response(tmp_path, monkeypatch, field, value):
    paths, runtime, definition = make_native(tmp_path)
    session = Session((definition(paths[0]),), runtime)
    child = session._child
    original = session._parse

    def corrupt(data):
        result = original(data)
        result[field] = value
        return result

    monkeypatch.setattr(session, '_parse', corrupt)
    with pytest.raises(n.TokenizerError):
        session.count('bge_body', 'canary')
    assert child.poll() is not None


def test_idle_worker_has_actual_lifetime_limit(tmp_path):
    import time

    paths, runtime, definition = make_native(tmp_path)
    session = Session((definition(paths[0]),), runtime)
    child = session._child
    try:
        child.wait(timeout=21)
        with pytest.raises(n.TokenizerError):
            session.count('bge_body', 'x')
    finally:
        session.close()
    assert child.poll() is not None
    assert time.monotonic() >= session._deadline - 1


def test_actual_request_ceiling_and_immutable_artifacts(tmp_path):
    paths, runtime, definition = make_native(tmp_path)
    before = [path.read_bytes() for path in paths]
    with Session((definition(paths[0]),), runtime) as session:
        for i in range(16384):
            assert session.count('bge_body', str(i)).count == 3
        with pytest.raises(n.TokenizerError):
            session.count('bge_body', 'x')
    assert [path.read_bytes() for path in paths] == before


def test_oversized_request_and_unicode_canary(tmp_path):
    paths, runtime, definition = make_native(tmp_path)
    for text in ('x' * 100001, '\ud800', 'private canary' * 20000):
        session = Session((definition(paths[0]),), runtime)
        with pytest.raises(n.TokenizerError) as exc:
            session.count('bge_body', text)
        assert str(exc.value) == 'tokenizer session refused'
