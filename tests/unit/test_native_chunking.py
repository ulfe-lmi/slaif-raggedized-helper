from dataclasses import replace
from pathlib import Path

from slaif_raggedized_helper import native_chunking as nc, native_tokenizers as n


def test_definition_identity_binds_all_declarations():
    d = n.Definition(Path('/unused'), '0' * 64, '0.21.4', 'bge_body', 'rev', 'identity')
    baseline = nc._identity(d)
    for changed in (replace(d, sha256='1' * 64), replace(d, backend_version='other'),
                    replace(d, role='bge_representation'), replace(d, model_revision='r2'),
                    replace(d, preprocessing='other')):
        assert nc._identity(changed) != baseline
    assert nc._input_digest('a', None) != nc._input_digest('a', '')
    assert nc._input_digest('é', None) != nc._input_digest('e', None)


def test_receipt_output_ceiling_and_safe_error(monkeypatch):
    import pytest
    monkeypatch.setattr(nc, '_json', lambda value: b'x' * 8_000_001)
    with pytest.raises(nc.NativeChunkingError, match='^native chunk construction refused$'):
        nc.Result((), (), ()).receipts_json()


def test_invalid_definitions_refused_before_identity_or_session(monkeypatch):
    import pytest

    definitions = tuple(n.Definition(Path('/unused'), '0' * 64, '0.21.4', role, 'rev', 'prep')
                        for role in ('bge_body', 'bge_representation', 'reranker_pair'))
    events = []
    for name in ('_identity', '_json', 'Session'):
        monkeypatch.setattr(nc, name, lambda *args, name=name: events.append(name))
    invalid = {
        'role': [True, '', 'wrong', 'x' * 257, 'x' * 1_048_576, '\ud800'],
        'backend_version': [True, '', '0.21.5', 'x' * 257, 'x' * 1_048_576, '\ud800'],
        'sha256': [True, '', 'A' * 64, 'g' * 64, '0' * 63, '0' * 257,
                   '0' * 1_048_576, '\ud800'],
        'model_revision': [True, '', 'x' * 257, 'x' * 1_048_576, '\ud800'],
        'preprocessing': [True, '', 'x' * 257, 'x' * 1_048_576, '\ud800'],
    }
    for index in range(3):
        for field, values in invalid.items():
            for value in values:
                ds = list(definitions)
                ds[index] = replace(ds[index], **{field: value})
                with pytest.raises(nc.NativeChunkingError,
                                   match='^native chunk construction refused$'):
                    nc.build(None, (), *ds, None, 'query')
                assert events == []
    with pytest.raises(nc.NativeChunkingError, match='^native chunk construction refused$'):
        nc.build(None, (), object(), *definitions[1:], None, 'query')
    assert events == []
