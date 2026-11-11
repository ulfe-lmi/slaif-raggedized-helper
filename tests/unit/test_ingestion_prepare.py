import math
import time
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import pytest

from slaif_raggedized_helper import chunking, ingestion_prepare as service
from slaif_raggedized_helper import ingestion_profile, native_tokenizers as native


def profile():
    runtime = native.Runtime(Path('/runtime'), Path('/packages'), 'python3.12')
    def definition(role):
        return native.Definition(Path('/artifact'), 'a' * 64, '0.21.4', role, 'rev', 'identity')
    return ingestion_profile.Profile(runtime, definition('bge_body'),
                                     definition('bge_representation'),
                                     definition('reranker_pair'), None, chunking.Policy())


@pytest.mark.parametrize('end', [math.nan, math.inf, -math.inf, 0, 'invalid', True])
def test_invalid_deadline_before_store(end):
    calls = []
    with patch.object(service, 'OriginalStore', side_effect=lambda *a: calls.append(a)):
        with pytest.raises(service.PrepareError):
            service.inspect('/original', '/derived', 'x', end)
    assert calls == []


def test_overlong_deadline_before_store():
    calls = []
    with patch.object(service, 'OriginalStore', side_effect=lambda *a: calls.append(a)):
        with pytest.raises(service.PrepareError):
            service.prepare('/original', '/derived', 'sha256:' + 'a' * 64,
                            'structured_text', profile(), end=time.monotonic() + 181)
    assert calls == []


@pytest.mark.parametrize('bad', ['role', 'policy', 'query', 'revision'])
def test_invalid_inputs_precede_store(bad):
    value = profile()
    query = ''
    revision = 'sha256:' + 'a' * 64
    if bad == 'role':
        value = replace(value, bge_body=replace(value.bge_body, role='reranker_pair'))
    elif bad == 'policy':
        policy = chunking.Policy()
        object.__setattr__(policy, 'target', 99999)
        value = replace(value, chunk_policy=policy)
    elif bad == 'query':
        query = '\ud800'
    else:
        revision = 'bad'
    calls = []
    with patch.object(service, 'OriginalStore', side_effect=lambda *a: calls.append(a)):
        with pytest.raises(service.PrepareError):
            service.prepare('/original', '/derived', revision, 'structured_text', value, query)
    assert calls == []


def test_cleanup_failure_is_typed():
    class Store:
        def close(self):
            raise RuntimeError('secret')
    with patch.object(service, 'OriginalStore', return_value=Store()), \
         patch.object(service.derived_store, 'Store', return_value=Store()), \
         patch.object(service.ingestion_store, 'load', side_effect=ValueError):
        with pytest.raises(service.PrepareError, match='ingestion failed'):
            service.inspect('/original', '/derived', 'x')


def test_empty_text_reports_source_status_and_never_publishes():
    from types import SimpleNamespace
    store = SimpleNamespace(close=lambda: None)
    item = SimpleNamespace(revision=None, coverage=(), blocks=())
    with patch.object(service, 'OriginalStore', return_value=store), \
         patch.object(service.structured_text, 'extract', return_value=item), \
         patch.object(service.nc, 'build') as build, \
         patch.object(service.derived_store, 'Store') as derived:
        result = service.prepare('/original', '/derived', 'sha256:' + 'a' * 64,
                                 'structured_text', profile())
    assert result['status'] == 'no_native_chunks'
    assert result['source_status'] == 'complete_text'
    assert 'bundle_id' not in result
    build.assert_not_called()
    derived.assert_not_called()


def test_cleanup_attempts_both_stores_and_keeps_published_id():
    calls = []
    class Store:
        def __init__(self, name):
            self.name = name
        def close(self):
            calls.append(self.name)
            raise RuntimeError('secret')
    with pytest.raises(service.PrepareError) as error:
        service._close(Store('original'), Store('derived'), 'known-id')
    assert error.value.published_bundle_id == 'known-id'
    assert calls == ['derived', 'original']


def test_valid_parsed_profile_postpublish_cleanup_failure_keeps_id():
    from types import SimpleNamespace
    parsed = service._profile_snapshot(profile())
    calls = []
    class Store:
        def __init__(self, name):
            self.name = name
        def close(self):
            calls.append(self.name)
            if self.name == 'derived':
                raise RuntimeError('private cleanup detail')
    original, derived = Store('original'), Store('derived')
    block = SimpleNamespace(model_dump_json=lambda: '{}')
    item = SimpleNamespace(revision=object(), coverage=(), blocks=(block,),
                           dependency=SimpleNamespace(model_dump=lambda: {}), uncertainty='')
    result = SimpleNamespace(chunks=(), neighbors=(), receipts_json=lambda: b'')
    with patch.object(service, 'OriginalStore', return_value=original), \
         patch.object(service.structured_text, 'extract', return_value=item), \
         patch.object(service.p, 'Registry'), \
         patch.object(service.nc, 'build', return_value=result), \
         patch.object(service.jl, 'encode', return_value=b''), \
         patch.object(service.derived_store, 'Store', return_value=derived), \
         patch.object(service.ingestion_store, 'publish', return_value='known-id') as publish:
        with pytest.raises(service.PrepareError) as error:
            service.prepare('/original', '/derived', 'sha256:' + 'a' * 64,
                            'structured_text', parsed)
    publish.assert_called_once()
    assert error.value.published_bundle_id == 'known-id'
    assert 'original' in calls and 'derived' in calls
    assert 'private cleanup detail' not in str(error.value)


def test_valid_deadline_passes_unchanged_to_fresh_inspect():
    end = time.monotonic() + 60
    assert service._deadline(end) == end


def test_cancellation_is_not_masked_by_cleanup_failure():
    class Store:
        def close(self):
            raise RuntimeError('private cleanup detail')
    with patch.object(service, 'OriginalStore', return_value=Store()), \
         patch.object(service.structured_text, 'extract', side_effect=KeyboardInterrupt):
        with pytest.raises(KeyboardInterrupt):
            service.prepare('/original', '/derived', 'sha256:' + 'a' * 64,
                            'structured_text', service._profile_snapshot(profile()))
