"""Real producer handoff; synthetic owned artifacts, portable to clean hosted CI."""
from dataclasses import asdict, replace
import hashlib
import json
import subprocess
import inspect
from pathlib import Path

import numpy as np

import pytest

from slaif_raggedized_helper import raw_hybrid_search as hybrid
from slaif_raggedized_helper import native_tokenizers, provenance_records as p
# This existing provider initializes the inherited test helper path.
import test_retrieval_representation_composition as representation_provider
import test_native_tokenizers
import test_raw_snapshot_rows
import test_raw_snapshot_directory_composition
import test_raw_snapshot_files_composition
import test_raw_snapshot_source_rows_composition
import test_raw_hybrid_search_composition as hybrid_provider

make_sources = hybrid_provider.make_sources
CHECKOUT = Path(__file__).resolve().parents[2]
assert Path(native_tokenizers.__file__).resolve() == (
    CHECKOUT / 'src/slaif_raggedized_helper/native_tokenizers.py')
assert Path(hybrid.__file__).resolve() == (
    CHECKOUT / 'src/slaif_raggedized_helper/raw_hybrid_search.py')
for module, relative in ((representation_provider, 'tests/integration'),
                         (hybrid_provider, 'tests/integration'),
                         (test_native_tokenizers, 'tests/unit'),
                         (test_raw_snapshot_rows, 'tests/unit'),
                         (test_raw_snapshot_directory_composition, 'tests/integration'),
                         (test_raw_snapshot_files_composition, 'tests/integration'),
                         (test_raw_snapshot_source_rows_composition, 'tests/integration')):
    assert Path(module.__file__).resolve().parent == CHECKOUT / relative
for function, module in ((make_sources, hybrid_provider),
                         (representation_provider.make_bundle, representation_provider),
                         (test_native_tokenizers.make_native, test_native_tokenizers)):
    assert Path(inspect.getfile(function)).resolve() == Path(module.__file__).resolve()
    assert Path(function.__code__.co_filename).resolve() == Path(module.__file__).resolve()


@pytest.fixture
def trace_owned(tmp_path, monkeypatch, request):
    """Use owned helper artifacts once; prevent source-builder regeneration."""
    capped = getattr(request, 'param', 'poison') == 'capped'
    limits = dict(dense=2 if capped else 5, lexical=2 if capped else 5,
                  fusion=2 if capped else 3, catalog=16 if capped else 34,
                  score=2 if capped else 5, index=2 if capped else 5, native=200)
    counts = dict.fromkeys(limits, 0)
    def guard(obj, name, key):
        original = getattr(obj, name)
        def bounded(*args, **kwargs):
            counts[key] += 1
            assert counts[key] <= limits[key]
            return original(*args, **kwargs)
        monkeypatch.setattr(obj, name, bounded)
    for obj, name, key in ((hybrid.dense, 'search', 'dense'),
                           (hybrid.lexical, 'search', 'lexical'),
                           (hybrid.fusion, 'fuse', 'fusion'),
                           (hybrid.catalog, 'load_catalog', 'catalog'),
                           (hybrid.dense, '_score', 'score'),
                           (hybrid.lexical, '_index', 'index')):
        guard(obj, name, key)
    paths, runtime, definition = test_native_tokenizers.make_native(tmp_path)
    hashes = ('1432b17ab7e9e4214568327a62acb0004515b6d23d920c3c8ed1150041f2ee32',
              '36583090527cd1a96fb0e9e576053ebece1a8621a7d788fdef6cb380a7e66153')
    assert tuple(hashlib.sha256(path.read_bytes()).hexdigest() for path in paths) == hashes
    popen = subprocess.Popen
    def native_only(argv, *args, **kwargs):
        counts['native'] += 1
        assert counts['native'] <= limits['native'] and type(argv) is list
        one_shot = argv[:5] == ['/usr/bin/prlimit', '--as=536870912', '--cpu=3',
                                '--nofile=32', '--fsize=4096']
        session = argv[:5] == ['/usr/bin/timeout', '--signal=KILL', '20s',
                              '/usr/bin/prlimit', '--as=1073741824']
        assert (one_shot or session) and '/usr/bin/bwrap' in argv
        assert '--unshare-net' in argv and '--clearenv' in argv and '-c' not in argv
        assert '/runtime/bin/python3.12' in argv and '/worker.py' in argv
        assert any(str(x).endswith('tokenizer_worker.py') or
                   str(x).endswith('tokenizer_session_worker.py') for x in argv)
        return popen(argv, *args, **kwargs)
    monkeypatch.setattr(subprocess, 'Popen', native_only)
    monkeypatch.setattr(test_native_tokenizers, 'make_native',
                        lambda _tmp: (paths, runtime, definition))
    sources = make_sources(tmp_path, paired=not capped, three=capped)
    originals, derived, root, ident = sources[:4]
    try:
        core = json.loads((root / 'snapshots' / ident[7:] / '.core.json').read_bytes())
        e = core['embedding']
        vector = np.zeros(1024, dtype='<f4')
        vector[0] = 1
        grants = p.Grants(schema_version=1, corpora=('one',), versions=('v1',), labels=())
        yield dict(originals=originals, derived=derived, store_root=str(root), snapshot_id=ident,
                   text='Heading', query_payload=vector.tobytes(), query_space_id=e['space_id'],
                   query_definition_fingerprint=e['definition_fingerprint'],
                   query_policy_id=e['query_policy_fingerprint'],
                   query_execution_fingerprint=e['query_execution_fingerprint'], grants=grants,
                   dense_k=1, lexical_k=1, partition_cap=1, k=1), root, ident, counts
    finally:
        print('ACTUAL_GUARDED_COUNTS', counts, flush=True)
        derived.close()
        originals.close()


def test_actual_same_call_and_guard_control(trace_owned, monkeypatch):
    args, _, _, counts = trace_owned
    args.update(text='Heading', dense_k=1, lexical_k=1, partition_cap=1, k=1)
    args['grants'].__dict__['corpora'] = ('one',)
    captured = []
    catalog_reads, score_rows, index_rows = [], [], []
    actual_catalog = hybrid.catalog.load_catalog
    actual_score, actual_index = hybrid.dense._score, hybrid.lexical._index
    def capture_catalog(*a, **kw):
        value = actual_catalog(*a, **kw)
        catalog_reads.append(value)
        return value
    def capture_score(matrix, query):
        score_rows.append(len(matrix))
        return actual_score(matrix, query)
    def capture_index(scorer, rows):
        index_rows.append(rows)
        return actual_index(scorer, rows)
    monkeypatch.setattr(hybrid.catalog, 'load_catalog', capture_catalog)
    monkeypatch.setattr(hybrid.dense, '_score', capture_score)
    monkeypatch.setattr(hybrid.lexical, '_index', capture_index)
    actual_dense, actual_lexical, actual_fuse = (
        hybrid.dense.search, hybrid.lexical.search, hybrid.fusion.fuse)
    def dense(*a, **kw):
        result = actual_dense(*a, **kw)
        captured.append(('dense', kw['trace'], result))
        return result
    def lexical(*a, **kw):
        result = actual_lexical(*a, **kw)
        captured.append(('lexical', kw['trace'], result))
        return result
    def fuse(*a, **kw):
        dr, lr = captured[-2][2], captured[-1][2]
        assert tuple(e.ordinal for e in kw['dense'].entries) == tuple(h.ordinal for h in dr.hits)
        assert tuple(e.ordinal for e in kw['lexical'].entries) == tuple(h.ordinal for h in lr.hits)
        return actual_fuse(*a, **kw)
    monkeypatch.setattr(hybrid.dense, 'search', dense)
    monkeypatch.setattr(hybrid.lexical, 'search', lexical)
    monkeypatch.setattr(hybrid.fusion, 'fuse', fuse)
    plain = hybrid.search(**args)
    traced = hybrid.search(**args, trace=True)
    assert [(name, flag) for name, flag, _ in captured] == [
        ('dense', False), ('lexical', False), ('dense', True), ('lexical', True)]
    assert traced.dense is captured[2][2] and traced.lexical is captured[3][2]
    assert plain.dense.trace is plain.lexical.trace is None
    assert traced.dense.trace is captured[2][2].trace
    assert traced.lexical.trace is captured[3][2].trace
    assert replace(traced.dense, trace=None) == plain.dense
    assert replace(traced.lexical, trace=None) == plain.lexical
    assert replace(traced, dense=plain.dense, lexical=plain.lexical) == plain
    assert all(json.loads(hit.scope_bytes)['corpus'] == 'one' for hit in traced.fusion.hits)
    assert traced.dense.eligible == traced.lexical.eligible == 1
    assert score_rows == [1, 1] and all(len(rows) == 1 for rows in index_rows)
    assert all('deniedonly' not in str(rows).lower() for rows in index_rows)
    source = catalog_reads[0]
    for hit in traced.dense.hits:
        assert hit.original_chunk_bytes == source.rows[hit.ordinal].chunk_bytes
    for hit in traced.lexical.hits:
        assert hit.chunk_bytes == source.rows[hit.ordinal].chunk_bytes

    def inconsistent(*a, **kw):
        result = actual_dense(*a, **kw)
        trace = result.trace
        ordinal = trace.returned_ordinals[0]
        rows = tuple(replace(row, revision_id='sha256:' + 'f' * 64)
                     if row.ordinal == ordinal else row for row in trace.rows)
        trace = replace(trace, rows=rows)
        obj = asdict(trace)
        for name in ('trace_id', 'input_origin', 'qualification', 'authorization_status',
                     'execution_status'):
            obj.pop(name)
        obj.update(schema=1, kind='slaif-raw-dense-authorized-trace-v1')
        trace = replace(trace, trace_id=hybrid.dense._trace_hash(obj, lambda: 100))
        result = replace(result, trace=trace)
        captured.append(('dense', kw['trace'], result))
        return result
    monkeypatch.setattr(hybrid.dense, 'search', inconsistent)
    with pytest.raises(hybrid.HybridSearchError):
        hybrid.search(**args, trace=True)
    guard = hybrid._trace_link
    monkeypatch.setattr(hybrid, '_trace_link', lambda *a, **kw: None)
    control = hybrid.search(**args, trace=True)
    assert control.dense.trace is not None
    monkeypatch.setattr(hybrid, '_trace_link', guard)
    with pytest.raises(hybrid.HybridSearchError):
        hybrid.search(**args, trace=True)
    assert len(catalog_reads) == 34
    assert len(score_rows) == len(index_rows) == 5
    assert {key: counts[key] for key in ('dense', 'lexical', 'fusion', 'catalog',
            'score', 'index')} == dict(dense=5, lexical=5, fusion=3, catalog=34,
                                      score=5, index=5)


@pytest.mark.parametrize('trace_owned', ['capped'], indirect=True)
def test_actual_caps_with_both_trace_modes(trace_owned):
    args, _, _, counts = trace_owned
    plain = hybrid.search(**args)
    traced = hybrid.search(**args, trace=True)
    assert traced.dense.eligible == traced.lexical.eligible == 2
    assert traced.dense.partition_cap_applied and traced.lexical.partition_cap_applied
    assert traced.dense.returned == traced.lexical.returned == 1
    assert traced.dense.global_cap_applied is traced.lexical.global_cap_applied is False
    assert {key: counts[key] for key in ('dense', 'lexical', 'fusion', 'catalog',
            'score', 'index')} == dict(dense=2, lexical=2, fusion=2, catalog=16,
                                      score=2, index=2)
    assert replace(traced, dense=replace(traced.dense, trace=None),
                   lexical=replace(traced.lexical, trace=None)) == plain
