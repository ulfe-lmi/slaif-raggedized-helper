import pytest

from slaif_raggedized_helper import retrieval_representation as rr


def test_invalid_inputs_refuse_without_disclosure():
    with pytest.raises(rr.RepresentationError, match='^retrieval representation refused$'):
        rr.build(None, b'secret', (), 'secret', None, None)
    with pytest.raises(rr.RepresentationError):
        rr.build(None, b'', (), '', None, None, rr.Policy(max_tokens=1025))


@pytest.mark.parametrize('policy', [
    rr.Policy(max_codepoints=100000.0), rr.Policy(max_request_bytes=200000.0),
    rr.Policy(max_codepoints=True), rr.Policy(max_request_bytes=True),
    rr.Policy(max_tokens=True), rr.Policy(max_tokens=1.0),
    rr.Policy(version='other'), rr.Policy(separator='secret'),
])
def test_invalid_policy_refuses_before_validation(policy, monkeypatch):
    reached = []
    def forbidden(*args):
        reached.append(True)
        raise AssertionError('validation reached')
    monkeypatch.setattr(rr.ingestion_bundle, 'validate', forbidden)
    definition = rr.native_tokenizers.Definition(None, '0' * 64, '0.21.4',
                                                  'bge_representation', 'r', 'p')
    runtime = rr.native_tokenizers.Runtime(None, None)
    with pytest.raises(rr.RepresentationError, match='^retrieval representation refused$'):
        rr.build(None, b'secret', (), 'secret', definition, runtime, policy)
    assert not reached


def controlled(monkeypatch, text='hello'):
    from types import SimpleNamespace as NS
    from pathlib import Path
    definition = rr.native_tokenizers.Definition(Path('/unused'), 'a' * 64, '0.21.4',
                                                  'bge_representation', 'revision', 'raw')
    runtime = rr.native_tokenizers.Runtime(Path('/unused'), Path('/unused'))
    chunk = NS(chunk_id='chunk', heading_path=(), text=text, extraction_id='extraction',
               revision_id='revision')
    class Metadata:
        title = None
        def model_dump(self, mode): return {}
    validated = NS(chunks=(chunk,), revision=NS(source=Metadata(), revision_id='revision'),
                   scope=Metadata())
    monkeypatch.setattr(rr.ingestion_bundle, 'validate', lambda *args: validated)
    return definition, runtime, chunk


def test_early_size_bounds(monkeypatch):
    import json
    definition, runtime, chunk = controlled(monkeypatch, '😀' * 20000)
    assert len(chunk.text) <= 100000
    wire = json.dumps({'text': chunk.text, 'pair': None, 'nonce': '0' * 32,
                       'role': definition.role, 'artifact': 0}, ensure_ascii=True,
                      separators=(',', ':')).encode() + b'\n'
    assert len(wire) > 200000
    reached = []
    def forbidden(*args, **kwargs):
        reached.append(True)
        raise AssertionError('expensive operation reached')
    monkeypatch.setattr(rr, 'Session', forbidden)
    monkeypatch.setattr(rr.hashlib, 'sha256', forbidden)
    with pytest.raises(rr.RepresentationError, match='^retrieval representation refused$'):
        rr.build(None, b'', (), 'chunk', definition, runtime)
    assert not reached
    chunk.text = 'x' * 100001
    monkeypatch.setattr(rr.json, 'dumps', forbidden)
    with pytest.raises(rr.RepresentationError, match='^retrieval representation refused$'):
        rr.build(None, b'', (), 'chunk', definition, runtime)
    assert not reached


def test_definition_metadata_rejected_before_validation(monkeypatch):
    from dataclasses import replace
    definition, runtime, _ = controlled(monkeypatch)
    reached = []
    monkeypatch.setattr(rr.ingestion_bundle, 'validate', lambda *args: reached.append(True))
    for bad in (replace(definition, model_revision='x' * 257),
                replace(definition, preprocessing=''), replace(definition, sha256='x' * 1000000),
                replace(definition, sha256=None)):
        with pytest.raises(rr.RepresentationError, match='^retrieval representation refused$'):
            rr.build(None, b'', (), 'chunk', bad, runtime)
        assert not reached


def test_forged_receipts_and_close(monkeypatch):
    from dataclasses import asdict, replace
    import hashlib
    import json
    definition, runtime, _ = controlled(monkeypatch)
    digest = hashlib.sha256(json.dumps(['hello', None], ensure_ascii=True,
                                      separators=(',', ':')).encode()).hexdigest()
    count = rr.native_tokenizers.Count(3, definition.sha256, '0.21.4',
                                       'bge_representation', 'revision', 'raw', digest, 'single')
    cases = [dict(input_sha256='0' * 64), dict(role='bge_body'),
             dict(artifact_sha256='0' * 64), dict(backend_version='bad'),
             dict(model_revision='bad'), dict(preprocessing='bad'), dict(mode='pair'),
             dict(serialization='bad'), dict(count=True), dict(count=1.5), dict(count=-1),
             dict(count=1025)]
    closed = []
    class FakeSession:
        def __init__(self, *args): pass
        def __enter__(self): return self
        def __exit__(self, *args): closed.append(True)
        def count(self, *args): return current[0]
    monkeypatch.setattr(rr, 'Session', FakeSession)
    for change in cases:
        current = [count]
        positive = rr.build(None, b'', (), 'chunk', definition, runtime)
        assert isinstance(positive, rr.Representation)
        assert positive.rendered_sha256 == hashlib.sha256(b'hello').hexdigest()
        identity = dict(revision_id='revision', extraction_id='extraction', chunk_id='chunk',
                        source={}, scope={}, variant='raw', policy=asdict(rr.Policy()),
                        rendered_sha256=positive.rendered_sha256)
        identity_bytes = json.dumps(identity, sort_keys=True, ensure_ascii=True,
                                    separators=(',', ':')).encode()
        assert positive.representation_id == hashlib.sha256(identity_bytes).hexdigest()
        assert positive.scope.model_dump(mode='json') == {}
        assert positive.source.model_dump(mode='json') == {}
        assert positive.count == count
        current = [replace(count, **change)]
        with pytest.raises(rr.RepresentationError, match='^retrieval representation refused$'):
            rr.build(None, b'secret', (), 'chunk', definition, runtime)
    assert len(closed) == 2 * len(cases)
    class FailingSession(FakeSession):
        def count(self, *args): raise ValueError('secret')
    monkeypatch.setattr(rr, 'Session', FailingSession)
    with pytest.raises(rr.RepresentationError, match='^retrieval representation refused$'):
        rr.build(None, b'secret', (), 'chunk', definition, runtime)
    assert len(closed) == 2 * len(cases) + 1


@pytest.mark.parametrize('changes', [
    {'version': 'bad'}, {'version': True}, {'max_items': True},
    {'max_items': 1.0}, {'max_items': 0}, {'max_items': 129},
    {'max_total_codepoints': False}, {'max_total_codepoints': 0},
    {'max_total_codepoints': 1000001}, {'max_total_request_bytes': 1.0},
    {'max_total_request_bytes': 0}, {'max_total_request_bytes': 4000001},
])
def test_invalid_batch_policy_before_validation(monkeypatch, changes):
    from dataclasses import replace
    definition, runtime, _ = controlled(monkeypatch)
    def forbidden(*args):
        pytest.fail('validator reached')
    monkeypatch.setattr(rr.ingestion_bundle, 'validate', forbidden)
    with pytest.raises(rr.RepresentationError, match='^retrieval representation refused$'):
        rr.build_many(None, b'', (), ['chunk'], definition, runtime,
                      batch_policy=replace(rr.BatchPolicy(), **changes))


def test_batch_preflight_and_later_failure(monkeypatch):
    from types import SimpleNamespace as NS
    from dataclasses import replace
    import hashlib
    import json
    definition, runtime, first = controlled(monkeypatch, 'hello')
    second = NS(chunk_id='second', heading_path=(), text='world', extraction_id='extraction',
                revision_id='revision')
    class Metadata:
        title = None
        def model_dump(self, mode): return {}
    validated = NS(chunks=(first, second), revision=NS(source=Metadata(), revision_id='revision'),
                   scope=Metadata())
    monkeypatch.setattr(rr.ingestion_bundle, 'validate', lambda *args: validated)
    closed = []
    mode = ['good']
    class Session:
        def __init__(self, *args): self.calls = 0
        def __enter__(self): return self
        def __exit__(self, *args): closed.append(True)
        def count(self, role, text):
            self.calls += 1
            digest = hashlib.sha256(json.dumps([text, None], ensure_ascii=True,
                                    separators=(',', ':')).encode()).hexdigest()
            count = rr.native_tokenizers.Count(3, definition.sha256, '0.21.4', role,
                                                'revision', 'raw', digest, 'single')
            if self.calls == 2 and mode[0] == 'raise':
                raise ValueError('secret')
            if self.calls == 2 and mode[0] == 'bad':
                return replace(count, input_sha256='0' * 64)
            return count
    monkeypatch.setattr(rr, 'Session', Session)
    args = (None, b'', (), ['chunk', 'second'], definition, runtime)
    assert len(rr.build_many(*args)) == 2
    for failure in ('bad', 'raise'):
        mode[0] = failure
        with pytest.raises(rr.RepresentationError, match='^retrieval representation refused$'):
            rr.build_many(*args)
    assert len(closed) == 3
    mode[0] = 'good'
    def wire(text):
        return len(json.dumps({'text': text, 'pair': None, 'nonce': '0' * 32,
                                           'role': definition.role, 'artifact': 0},
                                          ensure_ascii=True, separators=(',', ':')).encode()) + 1
    assert wire('hello') < wire('hello') + wire('world')
    def forbidden(*args, **kwargs): pytest.fail('worker or hash reached')
    monkeypatch.setattr(rr, 'Session', forbidden)
    monkeypatch.setattr(rr.hashlib, 'sha256', forbidden)
    with pytest.raises(rr.RepresentationError):
        rr.build_many(*args, batch_policy=rr.BatchPolicy(max_total_request_bytes=wire('hello') + 1))
    with pytest.raises(rr.RepresentationError):
        rr.build_many(*args, batch_policy=rr.BatchPolicy(max_total_codepoints=9))
