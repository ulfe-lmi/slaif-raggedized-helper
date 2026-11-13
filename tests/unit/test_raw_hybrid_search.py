"""Cheap input boundaries before any catalog or engine work."""
import pytest

from slaif_raggedized_helper import derived_store, provenance_records as p
from slaif_raggedized_helper import raw_hybrid_search as hybrid
from slaif_raggedized_helper.source_admission import OriginalStore


def arguments():
    return dict(originals=object.__new__(OriginalStore),
                derived=object.__new__(derived_store.Store),
                store_root='/owned', snapshot_id='sha256:' + 'a' * 64, text='private',
                query_payload=b'\0' * 4096, query_space_id='a' * 64,
                query_definition_fingerprint='sha256:' + 'b' * 64, query_policy_id='c' * 64,
                query_execution_fingerprint='d' * 64,
                grants=p.Grants(schema_version=1, corpora=(), versions=(), labels=()))


@pytest.mark.parametrize(('field', 'value'), [
    ('store_root', '/a/../b'), ('snapshot_id', 'bad'), ('text', 'x' * 8193),
    ('query_payload', b'x'), ('query_space_id', 'bad'), ('dense_k', True),
    ('lexical_k', 0), ('partition_cap', 61), ('k', False), ('deadline_ms', 0),
    ('grants', None),
])
def test_invalid_before_source_or_engines(monkeypatch, field, value):
    calls = []
    for obj, name in ((hybrid.catalog, 'load_catalog'), (hybrid.dense, 'search'),
                      (hybrid.lexical, 'search'), (hybrid.fusion, 'fuse')):
        monkeypatch.setattr(obj, name, lambda *a, **k: calls.append(1))
    args = arguments()
    args[field] = value
    with pytest.raises(hybrid.HybridSearchError, match='^hybrid search refused$'):
        hybrid.search(**args)
    assert not calls


def test_authority_copy_is_independent():
    authority = p.Grants(schema_version=1, corpora=('one',), versions=('v1',), labels=())
    captured, _ = hybrid.lexical._authority(authority, None)
    authority.__dict__['corpora'] = ('two',)
    assert captured.corpora == ('one',)


def test_non_exception_identity(monkeypatch):
    marker = KeyboardInterrupt()
    def interrupt(*args, **kwargs):
        raise marker
    monkeypatch.setattr(hybrid.lexical, '_authority', interrupt)
    with pytest.raises(KeyboardInterrupt) as caught:
        hybrid.search(**arguments())
    assert caught.value is marker


def test_missing_backend_refuses_before_source(monkeypatch):
    calls = []
    def missing(_):
        raise hybrid.importlib.metadata.PackageNotFoundError
    monkeypatch.setattr(hybrid.importlib.metadata, 'version', missing)
    monkeypatch.setattr(hybrid.catalog, 'load_catalog', lambda *a, **kw: calls.append(1))
    with pytest.raises(hybrid.HybridSearchError):
        hybrid.search(**arguments())
    assert not calls


def test_extra_authority_fields_refuse_before_source(monkeypatch):
    args = arguments()
    args['grants'].__dict__['unexpected'] = 'private'
    calls = []
    monkeypatch.setattr(hybrid.catalog, 'load_catalog', lambda *a, **kw: calls.append(1))
    with pytest.raises(hybrid.HybridSearchError):
        hybrid.search(**args)
    assert not calls
