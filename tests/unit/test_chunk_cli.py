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
