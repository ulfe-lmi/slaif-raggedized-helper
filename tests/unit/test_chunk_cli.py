import json
from unittest.mock import patch

import pytest

from slaif_raggedized_helper import chunk_cli


def test_inspect_does_not_load_profile(capsys):
    result = {'status': 'complete_text', 'bundle_id': 'known'}
    with patch.object(chunk_cli.ingestion_profile, 'load_profile') as profile, \
         patch.object(chunk_cli.ingestion_prepare, 'inspect', return_value=result) as inspect:
        assert chunk_cli.main(['inspect', '--original-store', '/o', '--derived-store', '/d',
                               '--bundle', 'known']) == 0
    profile.assert_not_called()
    inspect.assert_called_once()
    assert json.loads(capsys.readouterr().out) == result


def test_serialization_failure_retains_published_id(capsys):
    result = {'status': 'complete_text', 'bundle_id': 'known', 'bad': object()}
    with patch.object(chunk_cli.ingestion_prepare, 'inspect', return_value=result):
        assert chunk_cli.main(['inspect', '--original-store', '/o', '--derived-store', '/d',
                               '--bundle', 'known']) == 1
    assert json.loads(capsys.readouterr().out) == {
        'error': 'ingestion_failed', 'published_bundle_id': 'known'}


def test_help_does_not_load_profile_or_store(capsys):
    with patch.object(chunk_cli.ingestion_profile, 'load_profile') as profile, \
         patch.object(chunk_cli.ingestion_prepare, 'inspect') as inspect, \
         patch.object(chunk_cli.ingestion_prepare, 'prepare') as prepare:
        with pytest.raises(SystemExit) as exc:
            chunk_cli.main(['--help'])
    assert exc.value.code == 0
    profile.assert_not_called()
    inspect.assert_not_called()
    prepare.assert_not_called()
    assert 'usage:' in capsys.readouterr().out


def test_deadline_crossed_during_serialization_retains_id(capsys):
    result = {'status': 'complete_text', 'bundle_id': 'known-id'}
    real_dumps = json.dumps
    clock = [0]
    def serialize(value, **kwargs):
        output = real_dumps(value, **kwargs)
        if value is result:
            clock[0] = 181
        return output
    with patch.object(chunk_cli.time, 'monotonic', side_effect=lambda: clock[0]), \
         patch.object(chunk_cli.ingestion_prepare, 'inspect', return_value=result), \
         patch.object(chunk_cli.json, 'dumps', side_effect=serialize):
        assert chunk_cli.main(['inspect', '--original-store', '/o', '--derived-store', '/d',
                               '--bundle', 'known-id']) == 1
    assert json.loads(capsys.readouterr().out) == {
        'error': 'ingestion_failed', 'published_bundle_id': 'known-id'}


def test_fresh_load_refusal_after_publication_closes_resources(capsys):
    from types import SimpleNamespace
    from test_ingestion_prepare import profile
    service = chunk_cli.ingestion_prepare
    calls = []
    class Store:
        def __init__(self, name):
            self.name = name
        def close(self):
            calls.append(self.name)
    block = SimpleNamespace(model_dump_json=lambda: '{}')
    item = SimpleNamespace(revision=object(), coverage=(), blocks=(block,),
                           dependency=SimpleNamespace(model_dump=lambda: {}), uncertainty='')
    built = SimpleNamespace(chunks=(), neighbors=(), receipts_json=lambda: b'')
    parsed = service._profile_snapshot(profile())
    with patch.object(chunk_cli.ingestion_profile, 'load_profile', return_value=parsed), \
         patch.object(service, 'OriginalStore', return_value=Store('original')), \
         patch.object(service.structured_text, 'extract', return_value=item), \
         patch.object(service.p, 'Registry'), \
         patch.object(service.nc, 'build', return_value=built), \
         patch.object(service.jl, 'encode', return_value=b''), \
         patch.object(service.derived_store, 'Store', return_value=Store('derived')), \
         patch.object(service.ingestion_store, 'publish', return_value='known-id'), \
         patch.object(service.ingestion_store, 'load', side_effect=ValueError('PRIVATE-CANARY')):
        assert chunk_cli.main(['--original-store', '/o', '--derived-store', '/d',
                               '--revision', 'sha256:' + 'a' * 64, '--adapter',
                               'structured_text', '--profile', '/p']) == 1
    output = capsys.readouterr().out
    assert json.loads(output) == {'error': 'ingestion_failed', 'published_bundle_id': 'known-id'}
    assert 'PRIVATE-CANARY' not in output
    assert calls == ['derived', 'original', 'derived', 'original']
