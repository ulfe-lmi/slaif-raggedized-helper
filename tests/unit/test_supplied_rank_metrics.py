import dataclasses
import json
from pathlib import Path

import pytest

from slaif_raggedized_helper import supplied_rank_metrics as m


def tuples(value):
    return tuple(tuples(v) for v in value) if isinstance(value, list) else value


ORACLE_PATH = (Path(__file__).resolve().parents[2]
               / 'docs/parallel/supplied-rank-metrics-oracle.json')
ORACLE = json.loads(ORACLE_PATH.read_text())
CASES = tuples(ORACLE['cases'])
CUTS = tuples(ORACLE['cutoffs'])
GOLD = CASES[0][1]


def test_frozen_oracle():
    result = m.aggregate(CASES, cutoffs=CUTS)
    assert result.input_fingerprint == ORACLE['fingerprints']['aggregate']
    assert (result.total_queries, result.defined_queries,
            result.undefined_empty_gold_queries) == (3, 2, 1)
    for case, query in zip(CASES, result.query_results):
        assert query == m.score_query(*case, cutoffs=CUTS)
        assert query.input_fingerprint == ORACLE['fingerprints']['queries'][case[0]]
        for row in query.at_k:
            if case[0] == 'q3':
                assert (row.recall, row.reciprocal_rank, row.ndcg,
                        row.dcg, row.idcg) == (None, None, None, 0, 0)
                assert row.undefined_reason == 'UNDEFINED_EMPTY_POSITIVE_GOLD'
            else:
                for key, value in ORACLE['query_expected'][case[0]][str(row.k)].items():
                    assert getattr(row, key) == pytest.approx(value)
    for row in result.at_k:
        for key, value in ORACLE['aggregate_expected']['at_k'][str(row.k)].items():
            assert getattr(row, key) == pytest.approx(value)
    stage = ORACLE['stage']
    actual = m.compare_stage(*(tuples(stage['input'][k]) for k in ('gold', 'before', 'after')))
    assert actual.input_fingerprint == ORACLE['fingerprints']['stage']
    for key, value in stage['expected'].items():
        if isinstance(value, list):
            value = tuples(value)
        elif isinstance(value, float):
            value = pytest.approx(value)
        assert getattr(actual, key) == value


def test_empty_and_stage_semantics():
    row = m.score_query('q', GOLD, (), cutoffs=(5,)).at_k[0]
    assert (row.recall, row.reciprocal_rank, row.ndcg) == (0, 0, 0)
    row = m.score_query('q', (('A', 0),), ('A', 'X'), cutoffs=(5,)).at_k[0]
    assert row.recall is None and row.relevant_returned == 0
    assert m.aggregate((('q', (), ()),), cutoffs=(1,)).at_k[0].mrr is None
    unknown = m.compare_stage(GOLD, None, ())
    assert unknown.before_count is None and unknown.after_count == 0
    assert unknown.removed_ids is None
    assert unknown.gold_metrics_status == 'UNAVAILABLE_STAGE_IDENTITIES'
    empty = m.compare_stage(GOLD, (), ())
    assert empty.recall_before == 0 and empty.retained_fraction is None
    assert m.compare_stage((), ('A',), ()).gold_removed_ids == ()
    with pytest.raises(m.MetricsError):
        m.compare_stage(GOLD, (), ('A',))


@pytest.mark.parametrize('gold,ranking,cutoffs', [
    ((('B', 1), ('A', 1)), (), (1,)), ((('A', True),), (), (1,)),
    ((('A', 4),), (), (1,)), ((('A', 1), ('A', 2)), (), (1,)),
    ((), ('A', 'A'), (1,)), ((), (), (True,)), ((), (), (2, 1)),
    ((), (), (0,)), ((), (), (4097,)), ((), (), ()),
    ((), ('\ud800',), (1,)), ((), (str('x') * 257,), (1,)),
    ([], (), (1,)),
])
def test_refusals(gold, ranking, cutoffs):
    with pytest.raises(m.MetricsError) as exc:
        m.score_query('private', gold, ranking, cutoffs=cutoffs)
    assert str(exc.value) == 'supplied rank metrics refused'
    assert exc.value.__suppress_context__


def test_unicode_and_private_records():
    ids = ('e\u0301', 'é', '😀')
    result = m.score_query('secret', tuple((x, 1) for x in ids), ids, cutoffs=(3,))
    assert result.at_k[0].recall == 1
    assert 'secret' not in repr(result) and 'secret' not in repr(result.at_k[0])
    with pytest.raises(dataclasses.FrozenInstanceError):
        result.qualification = 'yes'
    with pytest.raises(TypeError):
        m.QueryResult('x', 'x', 0, 0, (), qualification='yes')
    class S(str):
        pass
    with pytest.raises(m.MetricsError):
        m.score_query(S('q'), (), ())


def test_deadline_and_baseexception(monkeypatch):
    class Stop(BaseException):
        pass
    sentinel = Stop()
    def fail():
        raise sentinel
    monkeypatch.setattr(m.time, 'monotonic', fail)
    with pytest.raises(Stop) as exc:
        m.score_query('q', (), ())
    assert exc.value is sentinel
    ticks = iter([0.0] + [0.0] * 5 + [1.0] * 100)
    monkeypatch.setattr(m.time, 'monotonic', lambda: next(ticks))
    with pytest.raises(m.MetricsError):
        m.score_query('q', (), (), deadline_ms=1)


def test_resource_limit():
    # Maximum entries across cases is enforced before scoring the final case.
    ids = tuple(f'{i:04}' for i in range(4096))
    cases = tuple((f'{i:03}', (), ids) for i in range(17))
    with pytest.raises(m.MetricsError):
        m.aggregate(cases, cutoffs=(1,))


def test_deadline_during_hash_and_after_result(monkeypatch):
    clock = [0.0]
    monkeypatch.setattr(m.time, 'monotonic', lambda: clock[0])
    real_encoder = m.json.JSONEncoder

    class SlowEncoder(real_encoder):
        def iterencode(self, obj):
            for chunk in super().iterencode(obj):
                clock[0] = 1.0
                yield chunk

    monkeypatch.setattr(m.json, 'JSONEncoder', SlowEncoder)
    with pytest.raises(m.MetricsError):
        m.score_query('q', (), (), deadline_ms=1)
    monkeypatch.setattr(m.json, 'JSONEncoder', real_encoder)
    clock[0] = 0.0
    constructor = m.QueryResult

    def slow_result(*args):
        result = constructor(*args)
        clock[0] = 1.0
        return result

    monkeypatch.setattr(m, 'QueryResult', slow_result)
    with pytest.raises(m.MetricsError):
        m.score_query('q', (), (), deadline_ms=1)
