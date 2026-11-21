"""Pure metrics for caller-supplied, unverified relevance units."""

import hashlib
import json
import math
import time
from dataclasses import dataclass, field


class MetricsError(ValueError):
    """An input, resource bound, or deadline was refused."""


@dataclass(frozen=True, repr=False)
class AtK:
    k: int
    returned_at_k: int
    relevant_returned: int
    dcg: float
    idcg: float
    recall: float | None
    reciprocal_rank: float | None
    ndcg: float | None
    undefined_reason: str | None


@dataclass(frozen=True, repr=False)
class AggregateAtK:
    k: int
    mean_recall: float | None
    mrr: float | None
    mean_ndcg: float | None
    defined_queries: int
    undefined_empty_gold_queries: int
    total_queries: int


def _marker(value):
    return field(default=value, init=False)


@dataclass(frozen=True, repr=False)
class QueryResult:
    query_id: str
    input_fingerprint: str
    positive_gold_count: int
    ranking_count: int
    at_k: tuple[AtK, ...]
    input_origin: str = _marker('SUPPLIED_UNVERIFIED')
    qualification: str = _marker('NOT_QUALIFIED')
    relevance_unit: str = _marker('SUPPLIED_UNIT_ID')
    formula_version: str = _marker('supplied-rank-metrics-v1')


@dataclass(frozen=True, repr=False)
class AggregateResult:
    total_queries: int
    defined_queries: int
    undefined_empty_gold_queries: int
    input_fingerprint: str
    query_results: tuple[QueryResult, ...]
    at_k: tuple[AggregateAtK, ...]
    input_origin: str = _marker('SUPPLIED_UNVERIFIED')
    qualification: str = _marker('NOT_QUALIFIED')
    relevance_unit: str = _marker('SUPPLIED_UNIT_ID')
    formula_version: str = _marker('supplied-rank-metrics-v1')


@dataclass(frozen=True, repr=False)
class StageResult:
    input_fingerprint: str
    status: str
    reason: str | None
    positive_gold_count: int
    before_count: int | None
    after_count: int | None
    removed_ids: tuple[str, ...] | None
    gold_removed_ids: tuple[str, ...] | None
    removed_count: int | None
    gold_removed_count: int | None
    recall_before: float | None
    recall_after: float | None
    recall_loss: float | None
    retained_fraction: float | None
    gold_metrics_status: str
    input_origin: str = _marker('SUPPLIED_UNVERIFIED')
    qualification: str = _marker('NOT_QUALIFIED')
    relevance_unit: str = _marker('SUPPLIED_UNIT_ID')
    formula_version: str = _marker('supplied-rank-metrics-v1')


class _Context:
    def __init__(self, started, deadline_ms):
        if type(deadline_ms) is not int or not 1 <= deadline_ms <= 30000:
            raise ValueError
        self.deadline = started + deadline_ms / 1000
        self.bytes = 0
        self.check()

    def check(self):
        if time.monotonic() >= self.deadline:
            raise ValueError

    def ident(self, value):
        self.check()
        if type(value) is not str or not 1 <= len(value) <= 256:
            raise ValueError
        size = len(value.encode('utf-8'))
        if size > 1024:
            raise ValueError
        self.bytes += size
        if self.bytes > 16777216:
            raise ValueError
        self.check()

    def fingerprint(self, domain, value):
        self.check()
        digest = hashlib.sha256(domain)
        count = 0
        encoder = json.JSONEncoder(sort_keys=True, ensure_ascii=True,
                                   separators=(',', ':'), allow_nan=False)
        for chunk in encoder.iterencode(value):
            self.check()
            data = chunk.encode('ascii')
            count += len(data)
            if count > 67108864:
                raise ValueError
            digest.update(data)
        self.check()
        return 'sha256:' + digest.hexdigest()


def _tuple(value, limit, minimum=0):
    if type(value) is not tuple or not minimum <= len(value) <= limit:
        raise ValueError


def _cutoffs(cutoffs):
    _tuple(cutoffs, 16, 1)
    previous = 0
    for k in cutoffs:
        if type(k) is not int or not previous < k <= 4096:
            raise ValueError
        previous = k


def _gold(ctx, gold):
    _tuple(gold, 4096)
    previous = None
    for pair in gold:
        ctx.check()
        _tuple(pair, 2, 2)
        ident, grade = pair
        ctx.ident(ident)
        if previous is not None and ident <= previous:
            raise ValueError
        if type(grade) is not int or not 0 <= grade <= 3:
            raise ValueError
        previous = ident


def _ids(ctx, ids):
    _tuple(ids, 4096)
    seen = set()
    for ident in ids:
        ctx.ident(ident)
        if ident in seen:
            raise ValueError
        seen.add(ident)


def _work(g, r, c):
    return (g + r) * c + g * max(1, (max(1, g) - 1).bit_length())


def _query(ctx, query_id, gold, ranking, cutoffs):
    grades = dict(gold)
    positives = []
    for _, grade in gold:
        ctx.check()
        if grade > 0:
            positives.append(grade)
    ctx.check()
    positives.sort(reverse=True)
    ctx.check()
    g = len(positives)
    results = []
    for k in cutoffs:
        ctx.check()
        contributions = []
        relevant = 0
        rr = 0.0
        for rank, ident in enumerate(ranking[:k], 1):
            ctx.check()
            grade = grades.get(ident, 0)
            if grade:
                relevant += 1
                if not rr:
                    rr = 1.0 / rank
            contributions.append((2**grade - 1) / math.log2(rank + 1))
        dcg = math.fsum(contributions)
        ideal = math.fsum((2**grade - 1) / math.log2(rank + 1)
                          for rank, grade in enumerate(positives[:k], 1))
        ctx.check()
        if g:
            ndcg = dcg / ideal
            if not math.isfinite(ndcg) or not -1e-12 <= ndcg <= 1 + 1e-12:
                raise ValueError
            ndcg = max(0.0, min(1.0, ndcg))
            recall, reason = relevant / g, None
        else:
            recall = rr = ndcg = None
            reason = 'UNDEFINED_EMPTY_POSITIVE_GOLD'
        results.append(AtK(k, min(k, len(ranking)), relevant, dcg, ideal,
                           recall, rr, ndcg, reason))
    fingerprint = ctx.fingerprint(b'slaif-supplied-rank-query-v1\n',
                                  {'query_id': query_id, 'gold': gold,
                                   'ranking': ranking, 'cutoffs': cutoffs})
    result = QueryResult(query_id, fingerprint, g, len(ranking), tuple(results))
    ctx.check()
    return result


def _invoke(fn, *args, **kwargs):
    try:
        started = time.monotonic()
        return fn(started, *args, **kwargs)
    except Exception:
        raise MetricsError('supplied rank metrics refused') from None


def _score_query(started, query_id, gold, ranking, *, cutoffs=(20, 60), deadline_ms=5000):
    ctx = _Context(started, deadline_ms)
    _cutoffs(cutoffs)
    _tuple(gold, 4096)
    _tuple(ranking, 4096)
    if _work(len(gold), len(ranking), len(cutoffs)) > 2097152:
        raise ValueError
    ctx.ident(query_id)
    _gold(ctx, gold)
    _ids(ctx, ranking)
    return _query(ctx, query_id, gold, ranking, cutoffs)


def _aggregate(started, cases, *, cutoffs=(20, 60), deadline_ms=5000):
    ctx = _Context(started, deadline_ms)
    _cutoffs(cutoffs)
    _tuple(cases, 512, 1)
    entries = work = 0
    previous = None
    for case in cases:
        ctx.check()
        _tuple(case, 3, 3)
        qid, gold, ranking = case
        _tuple(gold, 4096)
        _tuple(ranking, 4096)
        entries += len(gold) + len(ranking)
        work += _work(len(gold), len(ranking), len(cutoffs))
        if entries > 65536 or work > 2097152:
            raise ValueError
        ctx.ident(qid)
        if previous is not None and qid <= previous:
            raise ValueError
        previous = qid
        _gold(ctx, gold)
        _ids(ctx, ranking)
    results = tuple(_query(ctx, q, g, r, cutoffs) for q, g, r in cases)
    defined = sum(result.positive_gold_count > 0 for result in results)
    total = len(results)
    summaries = []
    for index, k in enumerate(cutoffs):
        ctx.check()
        vals = [result.at_k[index] for result in results if result.positive_gold_count]
        def mean(attr):
            return math.fsum(getattr(v, attr) for v in vals) / defined if defined else None
        summaries.append(AggregateAtK(k, mean('recall'), mean('reciprocal_rank'),
                                      mean('ndcg'), defined, total - defined, total))
    fingerprint = ctx.fingerprint(b'slaif-supplied-rank-aggregate-v1\n',
                                  {'cases': cases, 'cutoffs': cutoffs})
    result = AggregateResult(total, defined, total - defined, fingerprint,
                             results, tuple(summaries))
    ctx.check()
    return result


def _compare_stage(started, gold, before, after, *, deadline_ms=5000):
    ctx = _Context(started, deadline_ms)
    _tuple(gold, 4096)
    for stage in (before, after):
        if stage is not None:
            _tuple(stage, 4096)
    b = len(before) if before is not None else 0
    a = len(after) if after is not None else 0
    if len(gold) + b + a + 2 * b * max(1, (max(1, b) - 1).bit_length()) > 2097152:
        raise ValueError
    _gold(ctx, gold)
    for stage in (before, after):
        if stage is not None:
            _ids(ctx, stage)
    positive = {ident for ident, grade in gold if grade > 0}
    g = len(positive)
    fingerprint = ctx.fingerprint(b'slaif-supplied-rank-stage-loss-v1\n',
                                  {'gold': gold, 'before': before, 'after': after})
    if before is None or after is None:
        result = StageResult(fingerprint, 'UNAVAILABLE', 'MISSING_STAGE_IDENTITIES', g,
                             None if before is None else b, None if after is None else a,
                             None, None, None, None, None, None, None, None,
                             'UNAVAILABLE_STAGE_IDENTITIES')
    else:
        bset, aset = set(before), set(after)
        if not aset <= bset:
            raise ValueError
        ctx.check()
        removed = tuple(sorted(bset - aset))
        ctx.check()
        gold_removed = tuple(sorted(set(removed) & positive))
        ctx.check()
        result = StageResult(fingerprint, 'AVAILABLE', None, g, b, a, removed,
                             gold_removed, len(removed), len(gold_removed),
                             len(bset & positive) / g if g else None,
                             len(aset & positive) / g if g else None,
                             len(gold_removed) / g if g else None,
                             a / b if b else None,
                             'DEFINED' if g else 'UNDEFINED_EMPTY_POSITIVE_GOLD')
    ctx.check()
    return result


def score_query(query_id, gold, ranking, *, cutoffs=(20, 60), deadline_ms=5000):
    return _invoke(_score_query, query_id, gold, ranking, cutoffs=cutoffs,
                   deadline_ms=deadline_ms)


def aggregate(cases, *, cutoffs=(20, 60), deadline_ms=5000):
    return _invoke(_aggregate, cases, cutoffs=cutoffs, deadline_ms=deadline_ms)


def compare_stage(gold, before, after, *, deadline_ms=5000):
    return _invoke(_compare_stage, gold, before, after, deadline_ms=deadline_ms)
