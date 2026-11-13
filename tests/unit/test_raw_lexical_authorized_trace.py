"""Source-only checks of the lexical trace contract and cooperative deadline."""
import dataclasses
import importlib.metadata
import json
import sys
import types
from pathlib import Path

import pytest

from slaif_raggedized_helper import derived_store, provenance_records as p
from slaif_raggedized_helper import raw_lexical_search as lexical
from slaif_raggedized_helper import raw_snapshot_catalog, technical_analyzer
from slaif_raggedized_helper.source_admission import OriginalStore

ORACLE = Path(__file__).parents[2] / 'docs/parallel/raw-lexical-authorized-trace-oracle.json'


def args():
    return (object.__new__(OriginalStore), object.__new__(derived_store.Store), '/valid',
            'sha256:' + '0' * 64, 'query')


def test_authority_vectors():
    vectors = json.loads(ORACLE.read_text())['authority_vectors']
    assert lexical._authority_hash(*lexical._authority(None, None)) == vectors[0]['sha256']
    grants = p.Grants(schema_version=1, corpora=('one', 'two'), versions=('v1', 'Ž😀'),
                      labels=('secret',))
    admitted = lexical._authority(grants, None)
    assert lexical._authority_hash(*admitted) == vectors[1]['sha256']


def test_literal_trace_vectors_and_geometry():
    for vector in json.loads(ORACLE.read_text())['vectors']:
        obj = vector['object']
        rows = tuple(lexical.LexicalTraceRow(**r) for r in obj['rows'])
        parts = tuple(lexical.LexicalPartitionTrace(
            x['partition_id'], *(tuple(x[n]) for n in ('eligible_ordinals', 'ranked_ordinals',
                                                       'selected_ordinals', 'returned_ordinals')))
            for x in obj['partitions'])
        counts = tuple(lexical.PartitionCount(*c) for c in vector['expected_partition_counts'])
        lexical._validate_trace(rows, parts, tuple(obj['selected_ordinals']),
                                tuple(obj['returned_ordinals']), counts,
                                obj['partition_cap'], obj['k'], lambda: None)
        assert lexical._trace_hash(obj, lambda: None) == vector['trace_id']
        assert json.dumps(obj, sort_keys=True, ensure_ascii=True, separators=(',', ':'),
                          allow_nan=False) == vector['canonical_ascii']
        assert tuple(sum(getattr(c, name) for c in counts) for name in
                     ('eligible', 'matching', 'selected', 'returned')) == tuple(
                         vector['expected_counts'][name] for name in
                         ('eligible', 'matching', 'selected', 'returned'))
        expected = vector['expected_counts']
        assert vector['expected_cap_flags'] == dict(
            partition_cap_applied=expected['matching'] > expected['selected'],
            global_cap_applied=expected['selected'] > expected['returned'])


def test_invalid_trace_before_dependencies_and_valid_flags_reach_them(monkeypatch):
    calls = []
    marker = KeyboardInterrupt('sentinel')
    def version(_):
        calls.append('backend')
        raise marker
    monkeypatch.setattr(importlib.metadata, 'version', version)
    monkeypatch.setattr(raw_snapshot_catalog, 'load_catalog',
                        lambda *a, **k: calls.append('catalog'))
    grants = p.Grants(schema_version=1, corpora=('c',), versions=('v',), labels=())
    for flag in (1, None, 'true', 0):
        with pytest.raises(lexical.LexicalSearchError):
            lexical.search(*args(), grants=grants, trace=flag)
        assert calls == []
    for flag in (False, True):
        with pytest.raises(KeyboardInterrupt) as caught:
            lexical.search(*args(), grants=grants, trace=flag)
        assert caught.value is marker
    assert calls == ['backend', 'backend']


def test_private_frozen_and_old_constructor():
    row = lexical.LexicalTraceRow(0, 'p', 'c', 'r', 'x')
    assert 'ordinal=' not in repr(row)
    with pytest.raises(dataclasses.FrozenInstanceError):
        row.ordinal = 1
    result = lexical.LexicalResult('s', 'c', 'q', 'a', 'b', 'm', (), (), 0, 0, 0, 0,
                                   False, False)
    assert result.trace is None and 'trace' not in repr(result)
    assert 'trace' in dataclasses.asdict(result)
    fields = lexical.LexicalTrace.__dataclass_fields__
    for name, value in [('input_origin', 'SUPPLIED_UNVERIFIED'),
                        ('qualification', 'NOT_QUALIFIED'),
                        ('authorization_status', 'SUPPLIED_SCOPE_CHECKS_ONLY'),
                        ('execution_status', 'NOT_ATTESTED')]:
        assert not fields[name].init and fields[name].default == value


def test_hash_ceiling_private_guard():
    with pytest.raises(ValueError):
        lexical._trace_hash({'x': 'a' * 4194304}, lambda: None)


def test_final_constructor_deadline_both_flags(monkeypatch):
    now = [0.0]
    monkeypatch.setattr(lexical.time, 'monotonic', lambda: now[0])
    versions = {'bm25s': '0.2.14', 'numpy': '2.5.4', 'scipy': '1.18.1'}
    monkeypatch.setattr(importlib.metadata, 'version', versions.__getitem__)
    monkeypatch.setitem(sys.modules, 'bm25s', types.ModuleType('bm25s'))
    monkeypatch.setitem(sys.modules, 'numpy', types.ModuleType('numpy'))
    core = {'analyzer': {'fingerprint': 'a' * 64, 'backend': 'bm25s-lucene',
                         'bm25s_version': '0.2.14', 'numpy_version': '2.5.4',
                         'scipy_version': '1.18.1'}}
    cat = types.SimpleNamespace(core_bytes=json.dumps(core).encode(), rows=(),
                                catalog_id='sha256:' + 'b' * 64)
    calls = []
    monkeypatch.setattr(raw_snapshot_catalog, 'load_catalog',
                        lambda *a, **kw: calls.append(kw['deadline_ms']) or cat)
    monkeypatch.setattr(technical_analyzer, 'analyze', lambda *a: types.SimpleNamespace(
        analyzer_id='sha256:' + 'a' * 64, terms=()))
    constructor = lexical.LexicalResult
    for flag in (False, True):
        now[0] = 0
        assert lexical.search(*args(), grants=None, trace=flag, deadline_ms=1000)
        def late(*a, **kw):
            result = constructor(*a, **kw)
            now[0] = 2
            return result
        monkeypatch.setattr(lexical, 'LexicalResult', late)
        now[0] = 0
        with pytest.raises(lexical.LexicalSearchError):
            lexical.search(*args(), grants=None, trace=flag, deadline_ms=1000)
        monkeypatch.setattr(lexical, 'LexicalResult', constructor)
    assert len(calls) == 8
    real_hash = lexical._trace_hash
    hashes = []
    def late_hash(obj, remaining):
        result = real_hash(obj, remaining)
        hashes.append(result)
        now[0] = 2
        return result
    monkeypatch.setattr(lexical, '_trace_hash', late_hash)
    now[0] = 0
    with pytest.raises(lexical.LexicalSearchError):
        lexical.search(*args(), grants=None, trace=True, deadline_ms=1000)
    assert len(hashes) == 1 and len(calls) == 10


def test_late_hash_deadline(monkeypatch):
    now = [0]
    def remaining():
        now[0] += 1
        if now[0] == 4:
            raise TimeoutError
    with pytest.raises(TimeoutError):
        lexical._trace_hash({'key': 'value'}, remaining)
    assert now[0] == 4
