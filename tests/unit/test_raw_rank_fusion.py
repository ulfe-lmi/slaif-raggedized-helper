"""Preflight refuses malformed bounded inputs before any source read or scoring."""
from dataclasses import replace

import pytest

from slaif_raggedized_helper import derived_store, provenance_records as p, raw_rank_fusion as f
from slaif_raggedized_helper.source_admission import OriginalStore


def test_preflight_refusals(monkeypatch):
    snap = 'sha256:' + 'a'*64
    ident = 'sha256:' + 'b'*64
    entry = f.Entry(0, ident, ident, ident, 'c'*64, 1)
    dense = f.Ranking('dense', 'COMPLETE', snap, ident, 'd'*64, (entry,))
    lexical = f.Ranking('lexical', 'COMPLETE', snap, ident, 'd'*64, ())
    good = p.Grants(schema_version=1, corpora=('x',), versions=('v',), labels=())
    calls = []
    monkeypatch.setattr(f.raw_snapshot_catalog, 'load_catalog',
                        lambda *a, **k: calls.append('load'))
    monkeypatch.setattr(f, '_contribution', lambda *a: calls.append('score'))
    originals, derived = object.__new__(OriginalStore), object.__new__(derived_store.Store)
    def invoke(d=dense, lex=lexical, grants=good, **kw):
        with pytest.raises(f.FusionError):
            f.fuse(originals, derived, '/owned', snap, 'd'*64, dense=d, lexical=lex,
                   grants=grants, **kw)
    for wrong in (replace(entry, rank=True), replace(entry, rank=2),
                  replace(entry, ordinal=True), replace(entry, representation_id=ident)):
        invoke(d=replace(dense, entries=(wrong,)))
    invoke(d=replace(dense, entries=(entry, replace(entry, rank=2))))
    invoke(d=replace(dense, entries=(entry, replace(entry, ordinal=1, rank=2))))
    invoke(d=replace(dense, entries=tuple(replace(entry, ordinal=i, rank=i + 1)
                                         for i in range(61))))
    invoke(lex=replace(lexical, catalog_id='sha256:' + 'e'*64))
    invoke(lex=replace(lexical, modality='dense'))
    invoke(restrictions=p.Restrictions(schema_version=1).model_copy(
        update={'versions': ('😀'*65536,)}))
    invoke(d=replace(dense, entries=[entry]))
    invoke(d=replace(dense, declared_status='UNAVAILABLE'))
    invoke(d=replace(dense, declared_status='PARTIAL'))
    invoke(d=replace(dense, query_id='e'*64))
    invoke(grants=None)
    invoke(k=True)
    invoke(deadline_ms=0)
    invoke(grants=good.model_copy(update={'unknown': 'x'*200000}))
    invoke(grants=good.model_copy(update={'corpora': ('x'*65537,)}))
    invoke(grants=good.model_copy(update={'corpora': ('\ud800',)}))
    invoke(grants=good.model_copy(update={'corpora': ('x',)*129}))
    assert calls == []


def test_frozen_schemas():
    from dataclasses import FrozenInstanceError
    e = f.Entry(0, '', '', '', '', 1)
    with pytest.raises(FrozenInstanceError):
        e.rank = 2


def test_authority_budgets_and_independent_snapshot():
    good = p.Grants(schema_version=1, corpora=('one',), versions=('v',), labels=())
    restrictions = p.Restrictions(schema_version=1, corpora=('one',), versions=None)
    grant_copy, restriction_copy = f._authority(good, restrictions)
    assert grant_copy == good and grant_copy is not good
    assert restriction_copy == restrictions and restriction_copy is not restrictions
    for bad in (
        good.model_copy(update={'schema_version': True}),
        good.model_copy(update={'corpora': ['one']}),
        good.model_copy(update={'corpora': ('😀' * 65536,)}),
        good.model_copy(update={'corpora': ('one',), 'unexpected': 'x' * 100000}),
    ):
        with pytest.raises((ValueError, TypeError)):
            f._authority(bad, None)
    for bad in (
        restrictions.model_copy(update={'versions': ('\ud800',)}),
        restrictions.model_copy(update={'corpora': ('x',) * 129}),
    ):
        with pytest.raises((ValueError, TypeError, UnicodeError)):
            f._authority(good, bad)


def test_ranking_capture_is_independent_and_bounded():
    ident = 'sha256:' + 'a' * 64
    entry = f.Entry(0, ident, ident, ident, 'b' * 64, 1)
    source = f.Ranking('dense', 'COMPLETE', ident, ident, 'c' * 64, (entry,))
    captured = f._capture_ranking(source)
    assert captured == source and captured is not source
    assert captured.entries[0] is not entry
    object.__setattr__(source, 'declared_status', 'UNAVAILABLE')
    object.__setattr__(entry, 'rank', 7)
    assert captured.declared_status == 'COMPLETE' and captured.entries[0].rank == 1
    with pytest.raises(ValueError):
        f._capture_ranking(replace(source, entries=(entry,) * 61))
    with pytest.raises(ValueError):
        f._capture_ranking(replace(source, entries=[entry]))
