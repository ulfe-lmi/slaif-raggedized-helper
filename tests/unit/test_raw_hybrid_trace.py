"""Bounded private trace adapter tests; synthetic DTOs, no producer execution."""
from dataclasses import replace
import json

import pytest

from slaif_raggedized_helper import raw_hybrid_search as hybrid

DENSE_LITERAL = (
    '{"authority_sha256":"95cb9b4f84ceff132cc7a875d8c192bf4997016a939ee64141c'
    '1fd628c0e8738","catalog_id":"sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb'
    'bbbbbbbbbbbbbbbbbbbbbbbbbbbb","k":1,"kind":"slaif-raw-dense-authorized-t'
    'race-v1","partition_cap":2,"partitions":[],"query_definition_fingerprint'
    '":"sha256:33333333333333333333333333333333333333333333333333333333333333'
    '33","query_execution_fingerprint":"5555555555555555555555555555555555555'
    '555555555555555555555555555","query_payload_sha256":"1111111111111111111'
    '111111111111111111111111111111111111111111111","query_policy_id":"444444'
    '4444444444444444444444444444444444444444444444444444444444","query_space'
    '_id":"2222222222222222222222222222222222222222222222222222222222222222",'
    '"returned_ordinals":[],"rows":[],"schema":1,"selected_ordinals":[],"snap'
    'shot_id":"sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
    'aaaaaaaaa"}'
)
DENSE_ID = 'sha256:d429a92b45456fbe3382fde5170a1b44f0ead2113b0ce2310876c19a3aa58de1'
LEXICAL_LITERAL = (
    '{"analyzer_fingerprint":"eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee'
    'eeeeeeeeeeeeeeeee","authority_sha256":"95cb9b4f84ceff132cc7a875d8c192bf4'
    '997016a939ee64141c1fd628c0e8738","backend":"bm25s-lucene/0.2.14/2.5.4/1.'
    '18.1","catalog_id":"sha256:ddddddddddddddddddddddddddddddddddddddddddddd'
    'ddddddddddddddddddd","k":1,"kind":"slaif-raw-lexical-authorized-trace-v1'
    '","method":"lucene","partition_cap":1,"partitions":[],"query_text_sha256'
    '":"8ed3f6ad685b959ead7022518e1af76cd816f8e8ec7ccdda1ed4018e8f2223f8","re'
    'turned_ordinals":[],"rows":[],"schema":1,"selected_ordinals":[],"snapsho'
    't_id":"sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccc'
    'cccccc"}'
)
LEXICAL_ID = 'sha256:c8fe15ecc1caa1331f2ad0663b8b3ca3969466b4494eed741d04684e863cf489'


def fixture(engine):
    literal, identity = ((DENSE_LITERAL, DENSE_ID) if engine is hybrid.dense else
                         (LEXICAL_LITERAL, LEXICAL_ID))
    obj = json.loads(literal)
    obj.pop('schema')
    obj.pop('kind')
    for name in ('rows', 'partitions', 'selected_ordinals', 'returned_ordinals'):
        obj[name] = tuple(obj[name])
    trace_type = engine.DenseTrace if engine is hybrid.dense else engine.LexicalTrace
    trace = trace_type(trace_id=identity, **obj)
    expected = {name: getattr(trace, name) for name in obj if name not in
                ('k', 'partition_cap', 'rows', 'partitions', 'selected_ordinals',
                 'returned_ordinals')}
    if engine is hybrid.dense:
        result = engine.DenseResult(trace.snapshot_id, trace.catalog_id, trace.query_payload_sha256,
                                    'SUPPLIED_UNVERIFIED', 'NOT_QUALIFIED', (), (), 0, 0, 0,
                                    False, False, trace)
    else:
        result = engine.LexicalResult(trace.snapshot_id, trace.catalog_id, trace.query_text_sha256,
                                      trace.analyzer_fingerprint, trace.backend, trace.method,
                                      (), (), 0, 0, 0, 0, False, False, trace)
    return result, expected


@pytest.mark.parametrize('engine', [hybrid.dense, hybrid.lexical])
def test_literal_empty_identity_and_link(engine):
    result, expected = fixture(engine)
    hybrid._trace_link(result, engine, expected, result.trace.k, result.trace.partition_cap,
                       lambda: 100)


@pytest.mark.parametrize('engine', [hybrid.dense, hybrid.lexical])
@pytest.mark.parametrize('field,value', [
    ('trace_id', 'x' * 129), ('rows', (None,) * 4097),
    ('selected_ordinals', (0,) * 4097), ('returned_ordinals', (0, 1)),
    ('authority_sha256', 'f' * 64),
])
def test_refusal_before_validator_or_hash(monkeypatch, engine, field, value):
    result, expected = fixture(engine)
    result = replace(result, trace=replace(result.trace, **{field: value}))
    def forbidden(*args, **kwargs):
        raise AssertionError('late work reached')
    monkeypatch.setattr(engine, '_validate_trace', forbidden)
    monkeypatch.setattr(engine, '_trace_hash', forbidden)
    with pytest.raises(ValueError):
        hybrid._trace_link(result, engine, expected, result.trace.k, result.trace.partition_cap,
                           lambda: 100)


@pytest.mark.parametrize('value', [0, 1, None, 'true'])
def test_flag_refused_before_dependencies(monkeypatch, value):
    def forbidden(*args, **kwargs):
        raise AssertionError('dependency reached')
    monkeypatch.setattr(hybrid, '_search', forbidden)
    with pytest.raises(hybrid.HybridSearchError):
        hybrid.search(None, None, None, None, None, None, query_space_id=None,
                      query_definition_fingerprint=None, query_policy_id=None,
                      query_execution_fingerprint=None, grants=None, trace=value)

DENSE_ROWS_LITERAL = (
    '{"authority_sha256":"09d4cf4038a6102fe378951f1f6b69fd0ba8c50308d75984b7e'
    '2877750bcc7f6","catalog_id":"sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb'
    'bbbbbbbbbbbbbbbbbbbbbbbbbbbb","k":1,"kind":"slaif-raw-dense-authorized-t'
    'race-v1","partition_cap":2,"partitions":[{"eligible_ordinals":[0,1],"par'
    'tition_id":"sha256:ccccccccccccccccccccccccccccccccccccccccccccccccccccc'
    'ccccccccccc","ranked_ordinals":[0,1],"returned_ordinals":[],"selected_or'
    'dinals":[0,1]},{"eligible_ordinals":[2],"partition_id":"sha256:fffffffff'
    'fffffffffffffffffffffffffffffffffffffffffffffffffffffff","ranked_ordinal'
    's":[2],"returned_ordinals":[2],"selected_ordinals":[2]}],"query_definiti'
    'on_fingerprint":"sha256:333333333333333333333333333333333333333333333333'
    '3333333333333333","query_execution_fingerprint":"55555555555555555555555'
    '55555555555555555555555555555555555555555","query_payload_sha256":"11111'
    '11111111111111111111111111111111111111111111111111111111111","query_poli'
    'cy_id":"4444444444444444444444444444444444444444444444444444444444444444'
    '","query_space_id":"2222222222222222222222222222222222222222222222222222'
    '222222222222","returned_ordinals":[2],"rows":[{"chunk_id":"sha256:dddddd'
    'dddddddddddddddddddddddddddddddddddddddddddddddddddddddddd","ordinal":0,'
    '"partition_id":"sha256:ccccccccccccccccccccccccccccccccccccccccccccccccc'
    'ccccccccccccccc","representation_id":"7777777777777777777777777777777777'
    '777777777777777777777777777777","revision_id":"sha256:666666666666666666'
    '6666666666666666666666666666666666666666666666"},{"chunk_id":"sha256:eee'
    'eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee","ordinal"'
    ':1,"partition_id":"sha256:cccccccccccccccccccccccccccccccccccccccccccccc'
    'cccccccccccccccccc","representation_id":"8888888888888888888888888888888'
    '888888888888888888888888888888888","revision_id":"sha256:666666666666666'
    '6666666666666666666666666666666666666666666666666"},{"chunk_id":"sha256:'
    '0000000000000000000000000000000000000000000000000000000000000000","ordin'
    'al":2,"partition_id":"sha256:fffffffffffffffffffffffffffffffffffffffffff'
    'fffffffffffffffffffff","representation_id":"aaaaaaaaaaaaaaaaaaaaaaaaaaaa'
    'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","revision_id":"sha256:999999999999'
    '9999999999999999999999999999999999999999999999999999"}],"schema":1,"sele'
    'cted_ordinals":[2,0,1],"snapshot_id":"sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaa'
    'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}'
)
DENSE_ROWS_ID = 'sha256:829a8f38a6b3bc2e93c79e766b027065317684349304da12617aee72dc56d4f4'
LEXICAL_ROWS_LITERAL = (
    '{"analyzer_fingerprint":"eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee'
    'eeeeeeeeeeeeeeeee","authority_sha256":"09d4cf4038a6102fe378951f1f6b69fd0'
    'ba8c50308d75984b7e2877750bcc7f6","backend":"bm25s-lucene/0.2.14/2.5.4/1.'
    '18.1","catalog_id":"sha256:ddddddddddddddddddddddddddddddddddddddddddddd'
    'ddddddddddddddddddd","k":1,"kind":"slaif-raw-lexical-authorized-trace-v1'
    '","method":"lucene","partition_cap":1,"partitions":[{"eligible_ordinals"'
    ':[0,2],"partition_id":"sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
    'aaaaaaaaaaaaaaaaaaaaaa","ranked_ordinals":[0,2],"returned_ordinals":[0],'
    '"selected_ordinals":[0]},{"eligible_ordinals":[1,3],"partition_id":"sha2'
    '56:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb","ra'
    'nked_ordinals":[1],"returned_ordinals":[],"selected_ordinals":[1]}],"que'
    'ry_text_sha256":"8ed3f6ad685b959ead7022518e1af76cd816f8e8ec7ccdda1ed4018'
    'e8f2223f8","returned_ordinals":[0],"rows":[{"chunk_id":"sha256:111111111'
    '1111111111111111111111111111111111111111111111111111111","ordinal":0,"pa'
    'rtition_id":"sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
    'aaaaaaaaaaaa","representation_id":"1111111111111111111111111111111111111'
    '111111111111111111111111111","revision_id":"sha256:fffffffffffffffffffff'
    'fffffffffffffffffffffffffffffffffffffffffff"},{"chunk_id":"sha256:222222'
    '2222222222222222222222222222222222222222222222222222222222","ordinal":1,'
    '"partition_id":"sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb'
    'bbbbbbbbbbbbbbb","representation_id":"2222222222222222222222222222222222'
    '222222222222222222222222222222","revision_id":"sha256:ffffffffffffffffff'
    'ffffffffffffffffffffffffffffffffffffffffffffff"},{"chunk_id":"sha256:333'
    '3333333333333333333333333333333333333333333333333333333333333","ordinal"'
    ':2,"partition_id":"sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
    'aaaaaaaaaaaaaaaaaa","representation_id":"3333333333333333333333333333333'
    '333333333333333333333333333333333","revision_id":"sha256:fffffffffffffff'
    'fffffffffffffffffffffffffffffffffffffffffffffffff"},{"chunk_id":"sha256:'
    '4444444444444444444444444444444444444444444444444444444444444444","ordin'
    'al":3,"partition_id":"sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb'
    'bbbbbbbbbbbbbbbbbbbbb","representation_id":"4444444444444444444444444444'
    '444444444444444444444444444444444444","revision_id":"sha256:ffffffffffff'
    'ffffffffffffffffffffffffffffffffffffffffffffffffffff"}],"schema":1,"sele'
    'cted_ordinals":[0,1],"snapshot_id":"sha256:ccccccccccccccccccccccccccccc'
    'ccccccccccccccccccccccccccccccccccc"}'
)
LEXICAL_ROWS_ID = 'sha256:5c738788de5a5c3a3e43be97d4584edb63a4ec48afcd36a2dcb66af2ad07d78a'


def populated(engine):
    is_dense = engine is hybrid.dense
    literal, identity = ((DENSE_ROWS_LITERAL, DENSE_ROWS_ID) if is_dense else
                         (LEXICAL_ROWS_LITERAL, LEXICAL_ROWS_ID))
    obj = json.loads(literal)
    obj.pop('schema')
    obj.pop('kind')
    row_type = engine.DenseTraceRow if is_dense else engine.LexicalTraceRow
    part_type = engine.DensePartitionTrace if is_dense else engine.LexicalPartitionTrace
    trace_type = engine.DenseTrace if is_dense else engine.LexicalTrace
    obj['rows'] = tuple(row_type(**row) for row in obj['rows'])
    for part in obj['partitions']:
        for name in ('eligible_ordinals', 'ranked_ordinals', 'selected_ordinals',
                     'returned_ordinals'):
            part[name] = tuple(part[name])
    obj['partitions'] = tuple(part_type(**part) for part in obj['partitions'])
    for name in ('selected_ordinals', 'returned_ordinals'):
        obj[name] = tuple(obj[name])
    trace = trace_type(trace_id=identity, **obj)
    expected = {name: getattr(trace, name) for name in obj if name not in
                ('k', 'partition_cap', 'rows', 'partitions', 'selected_ordinals',
                 'returned_ordinals')}
    by_ordinal = {row.ordinal: row for row in trace.rows}
    hits = []
    for rank, ordinal in enumerate(trace.returned_ordinals, 1):
        row = by_ordinal[ordinal]
        fields = (ordinal, row.partition_id, row.chunk_id, row.revision_id,
                  row.representation_id, b'scope', b'chunk')
        hits.append(engine.Hit(*fields, rank, 1.0) if is_dense else
                    engine.Hit(*fields, 1.0, rank))
    counts = []
    for part in trace.partitions:
        values = (part.partition_id, len(part.eligible_ordinals))
        if not is_dense:
            values += (len(part.ranked_ordinals),)
        values += (len(part.selected_ordinals), len(part.returned_ordinals))
        counts.append(engine.PartitionCount(*values))
    if is_dense:
        result = engine.DenseResult(trace.snapshot_id, trace.catalog_id, trace.query_payload_sha256,
            'SUPPLIED_UNVERIFIED', 'NOT_QUALIFIED', tuple(hits), tuple(counts), 3, 3, 1,
            False, True, trace)
    else:
        result = engine.LexicalResult(trace.snapshot_id, trace.catalog_id, trace.query_text_sha256,
            trace.analyzer_fingerprint, trace.backend, trace.method, tuple(hits), tuple(counts),
            4, 3, 2, 1, True, True, trace)
    return result, expected


@pytest.mark.parametrize('engine', [hybrid.dense, hybrid.lexical])
def test_literal_populated_and_valid_hash_inconsistent_hit(engine):
    result, expected = populated(engine)
    hybrid._trace_link(result, engine, expected, result.trace.k, result.trace.partition_cap,
                       lambda: 100)
    # The trace remains the independent literal with its valid old hash; only the actual hit
    # identity is altered, proving the result link rather than the digest rejects it.
    hit = replace(result.hits[0], revision_id='sha256:' + '0' * 64)
    broken = replace(result, hits=(hit,))
    with pytest.raises(ValueError):
        hybrid._trace_link(broken, engine, expected, result.trace.k, result.trace.partition_cap,
                           lambda: 100)


@pytest.mark.parametrize('engine', [hybrid.dense, hybrid.lexical])
def test_cumulative_ordinal_refused_before_validator(monkeypatch, engine):
    result, expected = fixture(engine)
    part_type = (engine.DensePartitionTrace if engine is hybrid.dense else
                 engine.LexicalPartitionTrace)
    seq = (0,) * 4096
    parts = tuple(part_type('sha256:' + 'a' * 64, seq, seq, seq, ()) for _ in range(2))
    result = replace(result, trace=replace(result.trace, partitions=parts))
    def forbidden(*args, **kwargs):
        raise AssertionError('validator reached')
    monkeypatch.setattr(engine, '_validate_trace', forbidden)
    with pytest.raises(ValueError):
        hybrid._trace_link(result, engine, expected, result.trace.k, result.trace.partition_cap,
                           lambda: 100)


def mocked_journey(monkeypatch):
    """Only the boundary is real; catalog and producers are typed synthetic DATA."""
    import hashlib
    import struct
    from dataclasses import asdict
    from slaif_raggedized_helper import derived_store, provenance_records
    from slaif_raggedized_helper.source_admission import OriginalStore

    snapshot, catalog_id = 'sha256:' + 'a' * 64, 'sha256:' + 'b' * 64
    payload = struct.pack('<f', 1) + bytes(4092)
    payload_hash = 'f7e4b7df98e2b9533216f4a9c1261224bda07083b93fe9357ea76c0f83477cee'
    text_hash = '8ed3f6ad685b959ead7022518e1af76cd816f8e8ec7ccdda1ed4018e8f2223f8'
    authority = '0bb2b22c9c2d57d4162d8d5ad387cdb366b82bb2f11a79b70732d9810d54487d'
    common = dict(snapshot_id=snapshot, catalog_id=catalog_id, authority_sha256=authority)
    dense_header = dict(**common, query_payload_sha256=payload_hash, query_space_id='c' * 64,
                        query_definition_fingerprint='sha256:' + 'd' * 64,
                        query_policy_id='e' * 64, query_execution_fingerprint='f' * 64)
    lex_header = dict(**common, query_text_sha256=text_hash, analyzer_fingerprint='1' * 64,
                      backend='bm25s-lucene/0.2.14/2.5.4/1.18.1', method='lucene')
    def make_trace(engine, header):
        modality = 'dense' if engine is hybrid.dense else 'lexical'
        kind = 'slaif-raw-' + modality + '-authorized-trace-v1'
        obj = dict(schema=1, kind=kind, **header, k=1, partition_cap=1, rows=[], partitions=[],
                   selected_ordinals=[], returned_ordinals=[])
        wire = json.dumps(obj, sort_keys=True, ensure_ascii=True, separators=(',', ':')).encode()
        trace_id = 'sha256:' + hashlib.sha256((kind + '\n').encode() + wire).hexdigest()
        cls = engine.DenseTrace if engine is hybrid.dense else engine.LexicalTrace
        return cls(trace_id=trace_id, **header, k=1, partition_cap=1, rows=(), partitions=(),
                   selected_ordinals=(), returned_ordinals=())
    dt, lt = make_trace(hybrid.dense, dense_header), make_trace(hybrid.lexical, lex_header)
    source = hybrid.catalog.Catalog(snapshot, b'{"analyzer":{"fingerprint":"' +
        b'1' * 64 + b'"}}', b'', (), (), (), (), catalog_id)
    calls = []
    def dense_search(*args, **kwargs):
        trace = dt if kwargs['trace'] else None
        result = hybrid.dense.DenseResult(snapshot, catalog_id, payload_hash,
            'SUPPLIED_UNVERIFIED', 'NOT_QUALIFIED', (), (), 0, 0, 0, False, False, trace)
        calls.append(('dense', kwargs['trace'], result))
        return result
    def lexical_search(*args, **kwargs):
        trace = lt if kwargs['trace'] else None
        result = hybrid.lexical.LexicalResult(snapshot, catalog_id, text_hash, '1' * 64,
            lex_header['backend'], 'lucene', (), (), 0, 0, 0, 0, False, False, trace)
        calls.append(('lexical', kwargs['trace'], result))
        return result
    def fuse(*args, **kwargs):
        calls.append(('fusion', kwargs['dense'], kwargs['lexical']))
        assert kwargs['dense'].entries == kwargs['lexical'].entries == ()
        return hybrid.fusion.FusionResult(snapshot, catalog_id, args[4], 'SUPPLIED_UNVERIFIED',
            'NOT_QUALIFIED', 'COMPLETE', 'COMPLETE', False, (), 0, 0, 0, 0, 0, False)
    monkeypatch.setattr(hybrid.catalog, 'load_catalog', lambda *args, **kwargs: source)
    monkeypatch.setattr(hybrid.dense, 'search', dense_search)
    monkeypatch.setattr(hybrid.lexical, 'search', lexical_search)
    monkeypatch.setattr(hybrid.fusion, 'fuse', fuse)
    args = dict(originals=object.__new__(OriginalStore),
        derived=object.__new__(derived_store.Store),
        store_root='/owned', snapshot_id=snapshot, text='alpha', query_payload=payload,
        query_space_id='c' * 64, query_definition_fingerprint='sha256:' + 'd' * 64,
        query_policy_id='e' * 64, query_execution_fingerprint='f' * 64,
        grants=provenance_records.Grants(schema_version=1, corpora=(), versions=(), labels=()),
        dense_k=1, lexical_k=1, partition_cap=1, k=1)
    return args, calls, (dt, lt), asdict


def test_default_and_true_use_same_call_results_and_keep_identity(monkeypatch):
    args, calls, traces, asdict = mocked_journey(monkeypatch)
    plain = hybrid.search(**args)
    traced = hybrid.search(**args, trace=True)
    assert [(c[0], c[1]) for c in calls if c[0] != 'fusion'] == [
        ('dense', False), ('lexical', False), ('dense', True), ('lexical', True)]
    assert traced.dense is calls[3][2] and traced.lexical is calls[4][2]
    assert traced.dense.trace is traces[0] and traced.lexical.trace is traces[1]
    assert plain.dense.trace is plain.lexical.trace is None
    assert plain.query_id == traced.query_id == (
        '8906df93e5eafc1eb7284036016e5de7ed6fc8e255fdf15f2bc6316a707777e4')
    assert replace(traced, dense=plain.dense, lexical=plain.lexical) == plain
    before, after = asdict(plain), asdict(traced)
    assert before['dense']['trace'] is before['lexical']['trace'] is None
    assert after['dense']['trace'] == asdict(traces[0])
    assert after['lexical']['trace'] == asdict(traces[1])
    for field in before:
        if field not in ('dense', 'lexical'):
            assert before[field] == after[field]
    for field in ('dense', 'lexical'):
        for key in before[field]:
            if key != 'trace':
                assert before[field][key] == after[field][key]


def test_constructor_deadline_refuses_and_no_extra_engine_calls(monkeypatch):
    args, calls, _, _ = mocked_journey(monkeypatch)
    original = hybrid.HybridResult
    now = [0.0]
    monkeypatch.setattr(hybrid.time, 'monotonic', lambda: now[0])
    def slow_constructor(*a, **kw):
        result = original(*a, **kw)
        now[0] = 121.0
        return result
    monkeypatch.setattr(hybrid, 'HybridResult', slow_constructor)
    with pytest.raises(hybrid.HybridSearchError, match='^hybrid search refused$'):
        hybrid.search(**args, trace=True)
    assert [call[0] for call in calls] == ['dense', 'lexical', 'fusion']

NO_MATCH_LITERAL = (
    '{"analyzer_fingerprint":"eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee'
    'eeeeeeeeeeeeeeeee","authority_sha256":"09d4cf4038a6102fe378951f1f6b69fd0'
    'ba8c50308d75984b7e2877750bcc7f6","backend":"bm25s-lucene/0.2.14/2.5.4/1.'
    '18.1","catalog_id":"sha256:ddddddddddddddddddddddddddddddddddddddddddddd'
    'ddddddddddddddddddd","k":3,"kind":"slaif-raw-lexical-authorized-trace-v1'
    '","method":"lucene","partition_cap":2,"partitions":[{"eligible_ordinals"'
    ':[0,2],"partition_id":"sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
    'aaaaaaaaaaaaaaaaaaaaaa","ranked_ordinals":[],"returned_ordinals":[],"sel'
    'ected_ordinals":[]},{"eligible_ordinals":[1,3],"partition_id":"sha256:bb'
    'bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb","ranked_'
    'ordinals":[],"returned_ordinals":[],"selected_ordinals":[]}],"query_text'
    '_sha256":"e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b8'
    '55","returned_ordinals":[],"rows":[{"chunk_id":"sha256:11111111111111111'
    '11111111111111111111111111111111111111111111111","ordinal":0,"partition_'
    'id":"sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
    'aaaa","representation_id":"111111111111111111111111111111111111111111111'
    '1111111111111111111","revision_id":"sha256:fffffffffffffffffffffffffffff'
    'fffffffffffffffffffffffffffffffffff"},{"chunk_id":"sha256:22222222222222'
    '22222222222222222222222222222222222222222222222222","ordinal":1,"partiti'
    'on_id":"sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb'
    'bbbbbbb","representation_id":"222222222222222222222222222222222222222222'
    '2222222222222222222222","revision_id":"sha256:ffffffffffffffffffffffffff'
    'ffffffffffffffffffffffffffffffffffffff"},{"chunk_id":"sha256:33333333333'
    '33333333333333333333333333333333333333333333333333333","ordinal":2,"part'
    'ition_id":"sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
    'aaaaaaaaaa","representation_id":"333333333333333333333333333333333333333'
    '3333333333333333333333333","revision_id":"sha256:fffffffffffffffffffffff'
    'fffffffffffffffffffffffffffffffffffffffff"},{"chunk_id":"sha256:44444444'
    '44444444444444444444444444444444444444444444444444444444","ordinal":3,"p'
    'artition_id":"sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb'
    'bbbbbbbbbbbbb","representation_id":"444444444444444444444444444444444444'
    '4444444444444444444444444444","revision_id":"sha256:ffffffffffffffffffff'
    'ffffffffffffffffffffffffffffffffffffffffffff"}],"schema":1,"selected_ord'
    'inals":[],"snapshot_id":"sha256:cccccccccccccccccccccccccccccccccccccccc'
    'cccccccccccccccccccccccc"}'
)
NO_MATCH_ID = 'sha256:198bfc445fc01d4d52023e33bebe04217e3dd18629eab23ce1456f258c105f8a'


def test_lexical_no_match_with_eligible_rows():
    obj = json.loads(NO_MATCH_LITERAL)
    obj.pop('schema')
    obj.pop('kind')
    obj['rows'] = tuple(hybrid.lexical.LexicalTraceRow(**row) for row in obj['rows'])
    parts = []
    for item in obj['partitions']:
        for name in ('eligible_ordinals', 'ranked_ordinals', 'selected_ordinals',
                     'returned_ordinals'):
            item[name] = tuple(item[name])
        parts.append(hybrid.lexical.LexicalPartitionTrace(**item))
    obj['partitions'] = tuple(parts)
    obj['selected_ordinals'] = obj['returned_ordinals'] = ()
    trace = hybrid.lexical.LexicalTrace(trace_id=NO_MATCH_ID, **obj)
    expected = {key: value for key, value in obj.items() if key not in
                ('k', 'partition_cap', 'rows', 'partitions', 'selected_ordinals',
                 'returned_ordinals')}
    counts = tuple(hybrid.lexical.PartitionCount(part.partition_id, 2, 0, 0, 0)
                   for part in parts)
    result = hybrid.lexical.LexicalResult(trace.snapshot_id, trace.catalog_id,
        trace.query_text_sha256, trace.analyzer_fingerprint, trace.backend, trace.method,
        (), counts, 4, 0, 0, 0, False, False, trace)
    hybrid._trace_link(result, hybrid.lexical, expected, trace.k, trace.partition_cap, lambda: 100)


@pytest.mark.parametrize('engine', [hybrid.dense, hybrid.lexical])
@pytest.mark.parametrize('mutation', ['request', 'authority', 'cap', 'stage', 'row', 'count'])
def test_valid_old_hash_does_not_hide_link_mismatch(engine, mutation):
    import hashlib
    from dataclasses import asdict
    result, expected = populated(engine)
    trace = result.trace
    if mutation == 'request':
        name = 'query_payload_sha256' if engine is hybrid.dense else 'query_text_sha256'
        trace = replace(trace, **{name: '0' * 64})
    elif mutation == 'authority':
        trace = replace(trace, authority_sha256='0' * 64)
    elif mutation == 'cap':
        trace = replace(trace, partition_cap=trace.partition_cap + 1)
    elif mutation == 'stage':
        trace = replace(trace, returned_ordinals=())
    elif mutation == 'row':
        ordinal = trace.returned_ordinals[0]
        rows = tuple(replace(row, revision_id='sha256:' + '0' * 64)
                     if row.ordinal == ordinal else row for row in trace.rows)
        trace = replace(trace, rows=rows)
    obj = asdict(trace)
    for name in ('trace_id', 'input_origin', 'qualification', 'authorization_status',
                 'execution_status'):
        obj.pop(name)
    modality = 'dense' if engine is hybrid.dense else 'lexical'
    kind = 'slaif-raw-' + modality + '-authorized-trace-v1'
    obj.update(schema=1, kind=kind)
    wire = json.dumps(obj, sort_keys=True, ensure_ascii=True, separators=(',', ':')).encode()
    digest = hashlib.sha256((kind + '\n').encode() + wire).hexdigest()
    trace = replace(trace, trace_id='sha256:' + digest)
    broken = replace(result, trace=trace)
    if mutation == 'count':
        broken = replace(broken, eligible=result.eligible - 1)
    with pytest.raises(ValueError):
        hybrid._trace_link(broken, engine, expected, result.trace.k, result.trace.partition_cap,
                           lambda: 100)


def test_expired_after_hash_refuses(monkeypatch):
    args, calls, _, _ = mocked_journey(monkeypatch)
    now = [0.0]
    monkeypatch.setattr(hybrid.time, 'monotonic', lambda: now[0])
    original = hybrid.dense._trace_hash
    def slow(*a, **kw):
        value = original(*a, **kw)
        now[0] = 121.0
        return value
    monkeypatch.setattr(hybrid.dense, '_trace_hash', slow)
    with pytest.raises(hybrid.HybridSearchError):
        hybrid.search(**args, trace=True)
    assert [call[0] for call in calls] == ['dense', 'lexical']


@pytest.mark.parametrize(('flag', 'force_trace'), [(False, True), (True, False)])
def test_wrong_presence_refuses_before_fusion(monkeypatch, flag, force_trace):
    args, calls, traces, _ = mocked_journey(monkeypatch)
    producer = hybrid.dense.search
    def altered(*a, **kw):
        result = producer(*a, **kw)
        return replace(result, trace=traces[0] if force_trace else None)
    monkeypatch.setattr(hybrid.dense, 'search', altered)
    with pytest.raises(hybrid.HybridSearchError):
        hybrid.search(**args, trace=flag)
    assert [call[0] for call in calls] == ['dense', 'lexical']


def test_expired_after_validation_refuses(monkeypatch):
    args, calls, _, _ = mocked_journey(monkeypatch)
    now = [0.0]
    monkeypatch.setattr(hybrid.time, 'monotonic', lambda: now[0])
    original = hybrid.dense._validate_trace
    def slow(*a, **kw):
        original(*a, **kw)
        now[0] = 121.0
    monkeypatch.setattr(hybrid.dense, '_validate_trace', slow)
    with pytest.raises(hybrid.HybridSearchError):
        hybrid.search(**args, trace=True)
    assert [call[0] for call in calls] == ['dense', 'lexical']


@pytest.mark.parametrize('engine', [hybrid.dense, hybrid.lexical])
def test_forged_fixed_marker_refused(engine):
    result, expected = fixture(engine)
    object.__setattr__(result.trace, 'execution_status', 'ATTESTED')
    with pytest.raises(ValueError):
        hybrid._trace_link(result, engine, expected, result.trace.k, result.trace.partition_cap,
                           lambda: 100)


def test_deadline_expires_during_bounded_admission_before_downstream(monkeypatch):
    args, calls, traces, _ = mocked_journey(monkeypatch)
    now = [0.0]
    original_match = hybrid.re.fullmatch
    monkeypatch.setattr(hybrid.time, 'monotonic', lambda: now[0])
    def expire_during_trace_id(pattern, value, *a, **kw):
        matched = original_match(pattern, value, *a, **kw)
        if value == traces[0].trace_id:
            now[0] = 121.0
        return matched
    def forbidden(*a, **kw):
        raise SystemExit('downstream validation, hashing or fusion reached')
    monkeypatch.setattr(hybrid.re, 'fullmatch', expire_during_trace_id)
    monkeypatch.setattr(hybrid.dense, '_validate_trace', forbidden)
    monkeypatch.setattr(hybrid.lexical, '_validate_trace', forbidden)
    monkeypatch.setattr(hybrid.dense, '_trace_hash', forbidden)
    monkeypatch.setattr(hybrid.lexical, '_trace_hash', forbidden)
    monkeypatch.setattr(hybrid.fusion, 'fuse', forbidden)
    with pytest.raises(hybrid.HybridSearchError, match='^hybrid search refused$'):
        hybrid.search(**args, trace=True)
    assert [call[0] for call in calls] == ['dense', 'lexical']
