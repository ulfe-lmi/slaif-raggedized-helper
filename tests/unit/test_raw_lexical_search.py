"""Admission bounds and content-free lexical refusal."""
import pytest

from slaif_raggedized_helper import provenance_records as p
from slaif_raggedized_helper import raw_lexical_search as search


def test_authority_bounded_snapshot():
    grants = p.Grants(schema_version=1, corpora=('c',), versions=('v',), labels=('l',))
    restrictions = p.Restrictions(schema_version=1, corpora=('c',), versions=None)
    frozen, limited = search._authority(grants, restrictions)
    assert frozen == grants and frozen is not grants
    assert limited == restrictions and limited is not restrictions
    assert search._authority(None, None) == (None, None)
    object.__setattr__(grants, '__dict__', {'schema_version': 1, 'corpora': ('x',),
                                           'versions': ('v',), 'labels': ('l',), 'extra': 1})
    with pytest.raises(ValueError):
        search._authority(grants, None)


def test_authority_rejects_bypassed_fields():
    grants = p.Grants(schema_version=1, corpora=('c',), versions=('v',), labels=())
    for value in (['c'], ('\ud800',), ('x' * 65537,), tuple('x' for _ in range(129))):
        bad = grants.model_copy(update={'corpora': value})
        with pytest.raises((ValueError, UnicodeError)):
            search._authority(bad, None)


def test_invalid_preflight_never_loads(monkeypatch):
    from slaif_raggedized_helper import raw_snapshot_catalog
    calls = []
    monkeypatch.setattr(raw_snapshot_catalog, 'load_catalog', lambda *a, **k: calls.append(1))
    with pytest.raises(search.LexicalSearchError, match='lexical search refused'):
        search.search(None, None, '/a', 'sha256:' + '0' * 64, '', grants=None)
    assert calls == []


def test_scalar_and_authority_preflight_skip_source_and_index(monkeypatch):
    from slaif_raggedized_helper import derived_store, raw_snapshot_catalog
    from slaif_raggedized_helper.source_admission import OriginalStore

    originals, derived = object.__new__(OriginalStore), object.__new__(derived_store.Store)
    calls = []
    monkeypatch.setattr(raw_snapshot_catalog, 'load_catalog', lambda *a, **kw: calls.append('load'))
    monkeypatch.setattr(search, '_index', lambda *a: calls.append('index'))
    good = p.Grants(schema_version=1, corpora=('c',), versions=('v',), labels=())
    invalid_grants = good.model_copy(update={'corpora': ('x' * 65537,)})
    cases = [
        dict(root='/x/../y'), dict(root='/' + 'a' * 4096),
        dict(snapshot='0' * 64), dict(text='\ud800'),
        dict(text='x' * 8193), dict(k=True), dict(partition_cap=0),
        dict(deadline_ms=True), dict(grants=invalid_grants),
    ]
    for change in cases:
        args = dict(root='/valid', snapshot='sha256:' + '0' * 64, text='q', grants=good,
                    k=60, partition_cap=60, deadline_ms=120000)
        args.update(change)
        with pytest.raises(search.LexicalSearchError):
            search.search(originals, derived, args.pop('root'), args.pop('snapshot'),
                          args.pop('text'), **args)
    assert calls == []


def test_authority_combined_json_byte_budget_and_schema():
    grants = p.Grants(schema_version=1, corpora=('😀' * 65536,), versions=(), labels=())
    with pytest.raises(ValueError):
        search._authority(grants, None)
    valid = p.Grants(schema_version=1, corpora=('c',), versions=('v',), labels=())
    for version in (True, 2, '1'):
        with pytest.raises(ValueError):
            search._authority(valid.model_copy(update={'schema_version': version}), None)


def test_result_types_are_frozen():
    from dataclasses import FrozenInstanceError

    count = search.PartitionCount('partition', 1, 1, 1, 1)
    with pytest.raises(FrozenInstanceError):
        count.eligible = 2


def test_pydantic_extra_refused_before_loader_or_index(monkeypatch):
    from slaif_raggedized_helper import derived_store, raw_snapshot_catalog
    from slaif_raggedized_helper.source_admission import OriginalStore

    originals = object.__new__(OriginalStore)
    derived = object.__new__(derived_store.Store)
    grants = p.Grants(schema_version=1, corpora=('c',), versions=('v',), labels=())
    restrictions = p.Restrictions(schema_version=1, corpora=None, versions=None)
    calls = []
    monkeypatch.setattr(raw_snapshot_catalog, 'load_catalog', lambda *a, **k: calls.append('load'))
    monkeypatch.setattr(search, '_index', lambda *a: calls.append('index'))
    for target in (grants, restrictions):
        object.__setattr__(target, '__pydantic_extra__', {'unrecognized': 'value'})
        with pytest.raises(search.LexicalSearchError):
            search.search(originals, derived, '/valid', 'sha256:' + '0' * 64, 'query',
                          grants=grants, restrictions=restrictions)
        assert calls == []
        object.__setattr__(target, '__pydantic_extra__', None)


def test_unbounded_caller_keys_refused_before_loader(monkeypatch):
    from slaif_raggedized_helper import derived_store, raw_snapshot_catalog
    from slaif_raggedized_helper.source_admission import OriginalStore

    grants = p.Grants(schema_version=1, corpora=('c',), versions=('v',), labels=())
    grants.__dict__.update({f'extra_{i}': i for i in range(10000)})
    calls = []
    monkeypatch.setattr(raw_snapshot_catalog, 'load_catalog', lambda *a, **k: calls.append('load'))
    monkeypatch.setattr(search, '_index', lambda *a: calls.append('index'))
    with pytest.raises(search.LexicalSearchError):
        search.search(object.__new__(OriginalStore), object.__new__(derived_store.Store),
                      '/valid', 'sha256:' + '0' * 64, 'q', grants=grants)
    assert calls == []
