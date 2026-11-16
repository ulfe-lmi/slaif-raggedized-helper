"""Private, bounded evaluation of declared chunk judgments.

This module is under construction and does not expose a product interface.
"""

from dataclasses import dataclass, fields
import re


@dataclass(frozen=True, repr=False)
class Judgments:
    case_id: str
    gold: tuple


@dataclass(frozen=True, repr=False)
class Plan:
    plan_id: str
    dataset_id: str
    split_id: str
    snapshot_id: str
    generation: int
    catalog_id: str
    protocol_id: str
    unknown_policy: str
    overlap_policy: str
    cutoffs: tuple
    judgments: tuple


@dataclass(frozen=True, repr=False)
class GradeBudget:
    source_directories: int
    source_ingestion_loads: int
    source_derived_batch_loads: int
    source_bytes: int
    pin_calls: int
    catalog_calls: int
    judgment_binding_calls: int
    metric_aggregate_calls: int
    metric_entries: int
    metric_work: int
    local_work: int
    local_payload: int
    report_bytes: int


@dataclass(frozen=True, repr=False)
class Report:
    identity_payload: bytes
    identity: str
    plan_identity: str
    final_work: int
    final_payload: int


@dataclass(frozen=True, repr=False)
class FailurePrefix:
    phase: str
    intended: int
    attempted: int
    completed: int
    refused: int
    pending: int


class EvaluationError(ValueError):
    """Content-free refusal of the entire evaluation."""

    __slots__ = ("_progress",)

    def __init__(self, progress):
        super().__init__("evaluation program refused")
        self._progress = progress

    @property
    def progress(self):
        return self._progress


_MAX_BUDGET = (
    1540,
    853888,
    919808,
    719781365958412,
    514,
    513,
    256,
    3,
    196608,
    6291456,
    134217728,
    268435456,
    12582912,
)
_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}\Z", re.ASCII)
_HASH = re.compile(r"sha256:[0-9a-f]{64}\Z", re.ASCII)
_BARE_HASH = re.compile(r"[0-9a-f]{64}\Z", re.ASCII)


def _closed(value, cls):
    if type(value) is not cls or type(value.__dict__) is not dict:
        return False
    names = tuple(field.name for field in fields(cls))
    return len(value.__dict__) == len(names) and all(name in value.__dict__ for name in names)


def _plan_admission(plan, grade_budget, dataset, selected, meter, clock):
    """Validate complete graded declarations and reserve lower logical envelopes.

    This is only one part of joint admission; it does not authorize execution.
    """
    meter.reserve(4096, 4096)
    if not _closed(plan, Plan) or not _closed(grade_budget, GradeBudget):
        raise ValueError
    values = tuple(getattr(grade_budget, field.name) for field in fields(GradeBudget))
    if any(
        type(v) is not int or not 0 <= v <= cap for v, cap in zip(values, _MAX_BUDGET, strict=True)
    ):
        raise ValueError
    for value in (plan.plan_id, plan.protocol_id):
        meter.reserve(129)
        if type(value) is not str or _ID.fullmatch(value) is None:
            raise ValueError
    for value in (plan.dataset_id, plan.split_id, plan.snapshot_id, plan.catalog_id):
        meter.reserve(72)
        if type(value) is not str or _HASH.fullmatch(value) is None:
            raise ValueError
    if (
        plan.dataset_id != dataset.dataset_id
        or plan.split_id != dataset.split_id
        or type(plan.generation) is not int
        or not 1 <= plan.generation < 2**63
        or type(plan.unknown_policy) is not str
        or plan.unknown_policy != "UNJUDGED_AS_ZERO_DIAGNOSTIC"
        or type(plan.overlap_policy) is not str
        or plan.overlap_policy != "EXPLICIT_CHUNK_IDS_ONLY"
    ):
        raise ValueError
    cutoffs = plan.cutoffs
    if type(cutoffs) is not tuple or not 1 <= len(cutoffs) <= 16:
        raise ValueError
    previous = 0
    for cutoff in cutoffs:
        meter.reserve(1)
        if type(cutoff) is not int or not previous < cutoff <= 4096:
            raise ValueError
        previous = cutoff
    if 20 not in cutoffs or 60 not in cutoffs:
        raise ValueError
    n = len(selected)
    if type(plan.judgments) is not tuple or len(plan.judgments) != n:
        raise ValueError
    entries = work = 0
    for judgment, (case, _, _, _) in zip(plan.judgments, selected, strict=True):
        clock.check()
        meter.reserve(512, 128)
        if (
            not _closed(judgment, Judgments)
            or type(judgment.case_id) is not str
            or judgment.case_id != case.case_id
            or type(judgment.gold) is not tuple
            or len(judgment.gold) > 4096
        ):
            raise ValueError
        previous = None
        for pair in judgment.gold:
            clock.check()
            meter.reserve(256, 128)
            if type(pair) is not tuple or len(pair) != 2:
                raise ValueError
            ident, grade = pair
            if (
                type(ident) is not str
                or _HASH.fullmatch(ident) is None
                or (previous is not None and ident <= previous)
                or type(grade) is not int
                or not 0 <= grade <= 3
            ):
                raise ValueError
            previous = ident
        g = len(judgment.gold)
        entries += g + 60
        work += (g + 60) * len(cutoffs) + g * max(1, (max(1, g) - 1).bit_length())
    if entries > 65536 or work > 2097152:
        raise ValueError
    d, t, u = 6 * n + 4, 3328 * n + 1920, 3584 * n + 2304
    size = d * 100925699 + (t + u) * 404750404 + t * 2016386
    report_bound = (
        65536
        + 2048 * n
        + 1642496
        + 3 * (n * (1024 + 448 * len(cutoffs)) + 4096 + 512 * len(cutoffs))
    )
    required = (d, t, u, size, 2 + 2 * n, 1 + 2 * n, n, 3, 3 * entries, 3 * work)
    if any(have < need for have, need in zip(values, required)):
        raise ValueError
    if grade_budget.report_bytes < report_bound:
        raise ValueError
    return entries, work, report_bound


def _expected_queries(plan, selected, queries, meter, clock):
    """Derive producer identities before any source or pin observation."""
    import hashlib

    from . import source_bound_stage_loss as binder

    identities = []
    seen = set()
    for query, (case, original, effective, restricted) in zip(queries, selected, strict=True):
        clock.check()
        meter.reserve(len(case.question) + 1, 4 * len(case.question))
        question = case.question.encode("utf-8")
        meter.reserve(len(question) + len(query.payload) + 132, 384)
        question_hash = hashlib.sha256(question).hexdigest()
        payload_hash = hashlib.sha256(query.payload).hexdigest()
        hashes = []
        for authority in (original, effective):
            meter.reserve(2048, 2048)
            collections = (
                authority.corpora,
                authority.versions,
                authority.labels,
                () if restricted is None or restricted.corpora is None else restricted.corpora,
                () if restricted is None or restricted.versions is None else restricted.versions,
            )
            item_count = sum(len(group) for group in collections)
            meter.reserve(item_count + 1)
            chars = sum(len(value) for group in collections for value in group)
            meter.reserve(chars + item_count + 1, 4096 + 16 * chars + 128 * item_count)
            wire = [
                authority.model_dump(mode="json"),
                None if restricted is None else restricted.model_dump(mode="json"),
            ]
            hashes.append(
                binder._canonical_hash(
                    wire, b"", meter, clock.check, ensure_ascii=False, limit=262144
                )
            )
        original_hash, effective_hash = hashes
        query_id = binder._canonical_hash(
            {
                "kind": "raw-hybrid-query/v1",
                "snapshot_id": plan.snapshot_id,
                "catalog_id": plan.catalog_id,
                "query_text_sha256": question_hash,
                "query_payload_sha256": payload_hash,
                "query_space_id": query.space_id,
                "query_definition_fingerprint": query.definition_fingerprint,
                "query_policy_id": query.policy_id,
                "query_execution_fingerprint": query.execution_fingerprint,
                "authority_sha256": effective_hash,
                "dense_k": 60,
                "lexical_k": 60,
                "partition_cap": 60,
                "k": 60,
            },
            b"",
            meter,
            clock.check,
            ensure_ascii=False,
        )
        meter.reserve(256, 512)
        if query_id in seen:
            raise ValueError
        seen.add(query_id)
        identities.append((query_id, question_hash, payload_hash, original_hash, effective_hash))
    return tuple(identities)


class _State:
    __slots__ = (
        "plan",
        "budget",
        "meter",
        "plan_identity",
        "expected",
        "cases",
        "phase",
        "reserve_work",
        "reserve_payload",
    )

    def __init__(self, plan, budget):
        self.plan = plan
        self.budget = budget
        self.meter = None
        self.plan_identity = None
        self.expected = ()
        self.cases = []
        self.phase = None
        self.reserve_work = self.reserve_payload = 0


def _prepare(state, dataset, selected, selection, cohort, queries, gold_ids, config, budget, clock):
    from . import source_bound_stage_loss as binder, source_cohort_runner as source

    grade_budget = state.budget
    if not _closed(grade_budget, GradeBudget):
        raise ValueError
    for value, cap in zip(
        (getattr(grade_budget, f.name) for f in fields(GradeBudget)), _MAX_BUDGET, strict=True
    ):
        if type(value) is not int or not 0 <= value <= cap:
            raise ValueError
    meter = source._Meter(grade_budget.local_work, grade_budget.local_payload, clock.check)
    state.meter = meter
    entries, _, report_bound = _plan_admission(
        state.plan, grade_budget, dataset, selected, meter, clock
    )
    # Reserve a conservative envelope for preflight metadata and the report before
    # any source use. Actual operations are charged separately as they occur.
    n = len(selected)
    grades = entries - 60 * n
    minimum_work = 4000000 + 220000 * n + 8000 * grades + 16 * report_bound
    minimum_payload = 12000000 + 220000 * n + 12000 * grades + 16 * report_bound
    if (
        minimum_work > grade_budget.local_work - meter.work
        or minimum_payload > grade_budget.local_payload - meter.payload
    ):
        raise ValueError
    state.expected = _expected_queries(state.plan, selected, queries, meter, clock)
    meter.reserve(4096 + 256 * n + 128 * entries, 4096 + 512 * n + 256 * entries)
    query_records = tuple(
        {
            "case_id": query.case_id,
            "query_id": expected[0],
            "question_sha256": expected[1],
            "payload_sha256": expected[2],
            "original_authority_sha256": expected[3],
            "effective_authority_sha256": expected[4],
            "space_id": query.space_id,
            "definition_fingerprint": query.definition_fingerprint,
            "policy_id": query.policy_id,
            "execution_fingerprint": query.execution_fingerprint,
        }
        for query, expected in zip(queries, state.expected, strict=True)
    )
    plan = state.plan
    identity = {
        "schema": "slaif-graded-evaluation-plan-v1",
        "plan": {
            field.name: getattr(plan, field.name)
            for field in fields(Plan)
            if field.name != "judgments"
        },
        "judgments": tuple((item.case_id, item.gold) for item in plan.judgments),
        "dataset_id": dataset.dataset_id,
        "split_id": dataset.split_id,
        "cohort": (cohort.split, cohort.case_ids),
        "selection": selection,
        "config": (config.config_id, config.declaration_id),
        "queries": query_records,
        "gold_bundle_ids": gold_ids,
        "source_budget": tuple(getattr(budget, f.name) for f in fields(source.Budget)),
        "grade_budget": tuple(getattr(grade_budget, f.name) for f in fields(GradeBudget)),
    }
    state.plan_identity = "sha256:" + binder._canonical_hash(
        identity, b"slaif-graded-evaluation-plan-v1\n", meter, clock.check, limit=8388608
    )
    state.reserve_work = minimum_work
    state.reserve_payload = minimum_payload
    if (
        meter.work + minimum_work > meter.work_limit
        or meter.payload + minimum_payload > meter.payload_limit
    ):
        raise ValueError


def _catalog(state, originals, derived, root, owner, captured, clock):
    from . import raw_snapshot_catalog, source_cohort_runner as source

    state.phase = "CATALOG"
    plan, meter = state.plan, state.meter
    if (
        captured.pointer.snapshot_id != plan.snapshot_id
        or captured.pointer.generation != plan.generation
    ):
        raise ValueError
    meter.reserve(1)
    catalog = raw_snapshot_catalog.load_catalog(
        originals, derived, root, plan.snapshot_id, deadline_ms=clock.remaining(120000)
    )
    clock.check()
    if (
        type(catalog) is not raw_snapshot_catalog.Catalog
        or type(catalog.snapshot_id) is not str
        or catalog.snapshot_id != plan.snapshot_id
        or type(catalog.catalog_id) is not str
        or catalog.catalog_id != plan.catalog_id
    ):
        raise ValueError
    del catalog
    source._pin_observation(owner, originals, derived, root, captured, meter, clock)
    # The captured row map is known only after the first source pin. Reserve all
    # remaining grade-owned observations before the first producer invocation.
    pointer_size = len(captured.pointer.pointer_bytes)
    core_size = len(captured.data.core_bytes)
    row_map = captured.data.row_map
    map_size, rows = len(row_map.map_bytes), len(row_map.rows)
    pin_work = pointer_size + core_size + 2 * map_size + 2 * rows + 1095
    pin_payload = pointer_size + map_size + 192
    remaining_pins = 2 * len(state.plan.judgments) + 1
    if (
        meter.work + state.reserve_work + pin_work * remaining_pins > meter.work_limit
        or meter.payload + state.reserve_payload + pin_payload * remaining_pins
        > meter.payload_limit
    ):
        raise ValueError
    state.phase = None


def _case(
    state,
    originals,
    derived,
    root,
    owner,
    captured,
    case,
    effective,
    restricted,
    result,
    item,
    clock,
):
    from . import raw_dense_search, raw_lexical_search, raw_rank_fusion
    from . import source_bound_ranking as binding, source_cohort_runner as source
    from . import source_bound_stage_loss as binder

    meter, plan = state.meter, state.plan
    meter.reserve(2048, 2048)
    index = len(state.cases)
    expected = state.expected[index]
    judgment = plan.judgments[index]
    if (
        result.catalog_id != plan.catalog_id
        or result.query_id != expected[0]
        or tuple(item[1:5]) != tuple(expected[1:5])
    ):
        raise ValueError
    state.phase = "GRADE_PIN"
    source._pin_observation(owner, originals, derived, root, captured, meter, clock)
    meter.reserve(len(judgment.gold) + 1, 128 * len(judgment.gold))
    ids = tuple(pair[0] for pair in judgment.gold)
    state.phase = "GRADE_BIND"
    bound = binding.bind(
        originals,
        derived,
        root,
        plan.snapshot_id,
        plan.catalog_id,
        ids,
        grants=effective,
        restrictions=restricted,
        deadline_ms=clock.remaining(30000),
    )
    clock.check()
    state.phase = "GRADE_PIN"
    source._pin_observation(owner, originals, derived, root, captured, meter, clock)
    state.phase = "GRADE_CASE"
    if (
        type(bound) is not binding.BoundRanking
        or bound.snapshot_id != plan.snapshot_id
        or bound.catalog_id != plan.catalog_id
        or bound.authority_sha256 != expected[4]
        or type(bound.rows) is not tuple
        or type(bound.row_count) is not int
        or bound.row_count != len(ids)
        or len(bound.rows) != len(ids)
        or type(bound.fragment_count) is not int
        or not 0 <= bound.fragment_count <= 65536
        or bound.source_binding_status
        != ("ORIGINALS_REVALIDATED_AT_BIND_TIME" if ids else "NO_SELECTED_SOURCE_VALIDATED")
        or bound.input_origin != "SUPPLIED_RANKING_UNVERIFIED"
        or bound.authorization_status != "SUPPLIED_SCOPE_CHECKS_ONLY"
        or bound.execution_status != "NOT_ATTESTED"
        or bound.qualification != "NOT_QUALIFIED"
        or type(bound.binding_id) is not str
        or _HASH.fullmatch(bound.binding_id) is None
    ):
        raise ValueError
    count = 0
    for row, ident in zip(bound.rows, ids, strict=True):
        meter.reserve(1024, 256)
        if (
            type(row) is not binding.BoundRow
            or row.chunk_id != ident
            or type(row.ordinal) is not int
            or not 0 <= row.ordinal <= 4095
            or type(row.fragments) is not tuple
            or not row.fragments
        ):
            raise ValueError
        for value in (row.partition_id, row.chunk_id, row.revision_id, row.extraction_id):
            if type(value) is not str or _HASH.fullmatch(value) is None:
                raise ValueError
        for value in (
            row.representation_id,
            row.bundle_container_id,
            row.batch_container_id,
            row.scope_sha256,
        ):
            if type(value) is not str or _BARE_HASH.fullmatch(value) is None:
                raise ValueError
        # The genuine binder validates native fragments and their identities.
        # Count its bounded tuples here without retaining or copying them.
        count += len(row.fragments)
        if count > 65536:
            raise ValueError
    if count != bound.fragment_count:
        raise ValueError
    rankings = []
    for actual, cls in (
        (result.dense, raw_dense_search.Hit),
        (result.lexical, raw_lexical_search.Hit),
        (result.fusion, raw_rank_fusion.Hit),
    ):
        if type(actual.hits) is not tuple or len(actual.hits) > 60:
            raise ValueError
        meter.reserve(256 * len(actual.hits) + 1, 128 * len(actual.hits))
        ranked = []
        seen = set()
        for rank, hit in enumerate(actual.hits, 1):
            if (
                type(hit) is not cls
                or type(hit.chunk_id) is not str
                or _HASH.fullmatch(hit.chunk_id) is None
                or hit.chunk_id in seen
                or type(hit.rank) is not int
                or hit.rank != rank
            ):
                raise ValueError
            seen.add(hit.chunk_id)
            ranked.append(hit.chunk_id)
        rankings.append(tuple(ranked))
    fingerprint = "sha256:" + binder._canonical_hash(
        judgment.gold, b"slaif-graded-judgments-v1\n", meter, clock.check, limit=1048576
    )
    meter.reserve(1024, 2048)
    state.cases.append(
        (
            case.case_id,
            expected[0],
            expected[3],
            expected[4],
            bound.binding_id,
            bound.row_count,
            bound.fragment_count,
            bound.source_binding_status,
            fingerprint,
            judgment.gold,
            tuple(rankings),
        )
    )
    state.phase = None


def _validate_metrics(result, triples, cutoffs, meter, clock):
    import math

    from . import supplied_rank_metrics as metrics

    def metric_record(value, cls):
        if type(value) is not cls or type(value.__dict__) is not dict:
            return False
        spec = fields(cls)
        allowed = {field.name for field in spec}
        required = {field.name for field in spec if field.init}
        return required <= value.__dict__.keys() <= allowed

    def ratio(value):
        return type(value) is float and math.isfinite(value) and 0 <= value <= 1

    def marker(obj):
        return all(
            type(value) is str and value == expected
            for value, expected in (
                (obj.input_origin, "SUPPLIED_UNVERIFIED"),
                (obj.qualification, "NOT_QUALIFIED"),
                (obj.relevance_unit, "SUPPLIED_UNIT_ID"),
                (obj.formula_version, "supplied-rank-metrics-v1"),
            )
        )

    meter.reserve(4096, 4096)
    n = len(triples)
    if (
        not metric_record(result, metrics.AggregateResult)
        or not marker(result)
        or type(result.query_results) is not tuple
        or len(result.query_results) != n
        or type(result.at_k) is not tuple
        or len(result.at_k) != len(cutoffs)
        or type(result.total_queries) is not int
        or result.total_queries != n
    ):
        raise ValueError
    meter.reserve(256 * n + 1, 256 * n)
    expected_hash = _metric_hash(
        {"cases": triples, "cutoffs": cutoffs},
        b"slaif-supplied-rank-aggregate-v1\n",
        len(triples),
        sum(len(gold) + len(ranking) for _, gold, ranking in triples),
        len(cutoffs),
        meter,
        clock,
    )
    if type(result.input_fingerprint) is not str or result.input_fingerprint != expected_hash:
        raise ValueError
    defined = 0
    for item, (qid, gold, ranking) in zip(result.query_results, triples, strict=True):
        clock.check()
        meter.reserve(512 + len(gold) + len(ranking), 512)
        positive = sum(grade > 0 for _, grade in gold)
        defined += bool(positive)
        if (
            not metric_record(item, metrics.QueryResult)
            or not marker(item)
            or type(item.query_id) is not str
            or item.query_id != qid
            or type(item.positive_gold_count) is not int
            or item.positive_gold_count != positive
            or type(item.ranking_count) is not int
            or item.ranking_count != len(ranking)
            or type(item.at_k) is not tuple
            or len(item.at_k) != len(cutoffs)
        ):
            raise ValueError
        expected_query = _metric_hash(
            {"query_id": qid, "gold": gold, "ranking": ranking, "cutoffs": cutoffs},
            b"slaif-supplied-rank-query-v1\n",
            1,
            len(gold) + len(ranking),
            len(cutoffs),
            meter,
            clock,
        )
        if type(item.input_fingerprint) is not str or item.input_fingerprint != expected_query:
            raise ValueError
        for value, cutoff in zip(item.at_k, cutoffs, strict=True):
            meter.reserve(128, 128)
            if (
                not metric_record(value, metrics.AtK)
                or type(value.k) is not int
                or value.k != cutoff
                or type(value.returned_at_k) is not int
                or value.returned_at_k != min(cutoff, len(ranking))
                or type(value.relevant_returned) is not int
                or not 0 <= value.relevant_returned <= min(positive, value.returned_at_k)
                or type(value.dcg) is not float
                or not math.isfinite(value.dcg)
                or not 0 <= value.dcg <= 28672
                or type(value.idcg) is not float
                or not math.isfinite(value.idcg)
                or not 0 <= value.idcg <= 28672
            ):
                raise ValueError
            if positive:
                if (
                    not all(ratio(x) for x in (value.recall, value.reciprocal_rank, value.ndcg))
                    or value.undefined_reason is not None
                    or value.idcg <= 0
                ):
                    raise ValueError
            elif (
                value.recall is not None
                or value.reciprocal_rank is not None
                or value.ndcg is not None
                or value.dcg != 0
                or value.idcg != 0
                or value.relevant_returned != 0
                or value.undefined_reason != "UNDEFINED_EMPTY_POSITIVE_GOLD"
            ):
                raise ValueError
    if (
        type(result.defined_queries) is not int
        or result.defined_queries != defined
        or type(result.undefined_empty_gold_queries) is not int
        or result.undefined_empty_gold_queries != n - defined
    ):
        raise ValueError
    for value, cutoff in zip(result.at_k, cutoffs, strict=True):
        meter.reserve(128, 128)
        if (
            not metric_record(value, metrics.AggregateAtK)
            or type(value.k) is not int
            or value.k != cutoff
            or type(value.defined_queries) is not int
            or value.defined_queries != defined
            or type(value.undefined_empty_gold_queries) is not int
            or value.undefined_empty_gold_queries != n - defined
            or type(value.total_queries) is not int
            or value.total_queries != n
        ):
            raise ValueError
        vals = (value.mean_recall, value.mrr, value.mean_ndcg)
        if (defined and not all(ratio(v) for v in vals)) or (not defined and vals != (None,) * 3):
            raise ValueError


def _metric_hash(value, domain, cases, entries, cutoff_count, meter, clock):
    """Hash a bounded metric input after charging its entire JSON allocation."""
    import hashlib
    import json

    bound = 512 + 128 * cases + 96 * entries + 8 * cutoff_count
    meter.reserve(4 * bound, 4 * bound)
    clock.check()
    payload = json.dumps(
        value, sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False
    ).encode("ascii")
    if len(payload) > bound:
        raise ValueError
    clock.check()
    digest = hashlib.sha256(domain)
    digest.update(payload)
    clock.check()
    return "sha256:" + digest.hexdigest()


def _encoded(value, limit, meter, clock):
    import json

    meter.reserve(4 * limit + 1, 4 * limit + 1)
    clock.check()
    result = json.dumps(
        value, sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False
    ).encode("ascii")
    clock.check()
    if len(result) > limit:
        raise ValueError
    meter.reserve(len(result) + 1, len(result))
    return result


def _finish(
    state,
    source_report,
    dataset,
    cohort,
    selection,
    config,
    captured,
    owner,
    originals,
    derived,
    root,
    clock,
):
    import hashlib
    from dataclasses import asdict

    from . import source_cohort_runner as source, supplied_rank_metrics as metrics

    plan, meter = state.plan, state.meter
    meter.reserve(4096, 4096)
    n, c = len(state.cases), len(plan.cutoffs)
    if n != len(plan.judgments) or type(source_report) is not source.CohortReport:
        raise ValueError
    variants = []
    for index, name in enumerate(("dense", "lexical", "fusion")):
        state.phase = "GRADE_AGGREGATE"
        meter.reserve(1024 * n + 1, 512 * n)
        triples = tuple(
            sorted(
                ((item[1], item[9], item[10][index]) for item in state.cases),
                key=lambda item: item[0],
            )
        )
        result = metrics.aggregate(triples, cutoffs=plan.cutoffs, deadline_ms=clock.remaining(5000))
        clock.check()
        _validate_metrics(result, triples, plan.cutoffs, meter, clock)
        limit = 4096 + 512 * c + n * (1024 + 448 * c)
        state.phase = "SERIALIZE"
        meter.reserve(4 * limit, 4 * limit)
        variants.append((name, _encoded(asdict(result), limit, meter, clock)))
    state.phase = "SERIALIZE"
    if (
        type(source_report.identity_payload) is not bytes
        or len(source_report.identity_payload) > 1642496
        or type(source_report.identity) is not str
        or _HASH.fullmatch(source_report.identity) is None
        or type(source_report.final_work) is not int
        or source_report.final_work < 0
        or type(source_report.final_payload) is not int
        or source_report.final_payload < 0
    ):
        raise ValueError
    meter.reserve(
        len(source_report.identity_payload) + 64, len(source_report.identity_payload) + 64
    )
    if (
        source_report.identity
        != "sha256:"
        + hashlib.sha256(
            b"slaif-source-cohort-runner-v1\n" + source_report.identity_payload
        ).hexdigest()
    ):
        raise ValueError
    case_records = []
    for item in state.cases:
        meter.reserve(512, 2048)
        case_records.append(
            _encoded(
                dict(
                    zip(
                        (
                            "case_id",
                            "query_id",
                            "original_authority_sha256",
                            "effective_authority_sha256",
                            "binding_id",
                            "row_count",
                            "fragment_count",
                            "source_binding_status",
                            "judgment_fingerprint",
                        ),
                        item[:9],
                        strict=True,
                    )
                ),
                2048,
                meter,
                clock,
            )
        )
    meter.reserve(65536, 65536)
    header = {
        "schema": "slaif-graded-evaluation-program-v1",
        "plan_id": plan.plan_id,
        "plan_identity": state.plan_identity,
        "protocol_id": plan.protocol_id,
        "unknown_policy": plan.unknown_policy,
        "overlap_policy": plan.overlap_policy,
        "unit": "FROZEN_SNAPSHOT_CHUNK_ID",
        "dataset_id": dataset.dataset_id,
        "split_id": dataset.split_id,
        "split": cohort.split,
        "selection": selection,
        "dataset_case_count": dataset.case_count,
        "selected_case_count": n,
        "snapshot_id": captured.pointer.snapshot_id,
        "generation": captured.pointer.generation,
        "catalog_id": plan.catalog_id,
        "config_id": config.config_id,
        "source_identity": source_report.identity,
        "source_final_work": source_report.final_work,
        "source_final_payload": source_report.final_payload,
        "grade_budget": {f.name: getattr(state.budget, f.name) for f in fields(GradeBudget)},
        "statuses": {
            "baseline": "NOT_RUN",
            "authorship": "DECLARED_UNVERIFIED",
            "rights": "DECLARED_UNVERIFIED",
            "current_policy": "NOT_CHECKED",
            "encoder": "NOT_QUALIFIED",
            "model": "NOT_QUALIFIED",
            "scale": "NOT_QUALIFIED",
            "quality": "NOT_QUALIFIED",
            "visual": "NOT_QUALIFIED",
            "mvp": "NOT_QUALIFIED",
        },
    }
    # Encode independent bounded components, then join sorted outer keys with the
    # original source payload as an exact JSON value, once.
    components = {key: _encoded(value, 65536, meter, clock) for key, value in header.items()}
    meter.reserve(2048 * n + 2, 2048 * n + 2)
    components["cases"] = b"[" + b",".join(case_records) + b"]"
    meter.reserve(
        sum(len(value) + 64 for _, value in variants) + 2,
        sum(len(value) + 64 for _, value in variants) + 2,
    )
    components["variants"] = (
        b"{"
        + b",".join(
            _encoded(name, 32, meter, clock) + b":" + value for name, value in sorted(variants)
        )
        + b"}"
    )
    components["source_payload"] = source_report.identity_payload
    size = sum(len(key) + len(value) + 4 for key, value in components.items()) + 2
    if size > state.budget.report_bytes or size > 12582912:
        raise ValueError
    meter.reserve(4 * size + 1, 4 * size + 1)
    parts = [
        _encoded(key, 128, meter, clock) + b":" + components[key] for key in sorted(components)
    ]
    payload = b"{" + b",".join(parts) + b"}"
    if len(payload) > state.budget.report_bytes:
        raise ValueError
    clock.check()
    meter.reserve(len(payload) + 64, len(payload) + 64)
    digest = hashlib.sha256(b"slaif-graded-evaluation-program-v1\n")
    digest.update(payload)
    identity = "sha256:" + digest.hexdigest()
    state.phase = "FINAL_PIN"
    source._pin_observation(owner, originals, derived, root, captured, meter, clock)
    clock.check()
    return Report(payload, identity, state.plan_identity, meter.work, meter.payload)


def _failure(state, admitted, phase, intended, attempted, completed):
    active = state.phase or phase
    progress = None
    if admitted:
        per_case = active in (
            "CASE_PIN",
            "PRODUCER",
            "BINDER",
            "GRADE_PIN",
            "GRADE_BIND",
            "GRADE_CASE",
        )
        progress = FailurePrefix(
            active, intended, attempted, completed, 1 if per_case else 0, intended - attempted
        )
    return EvaluationError(progress)


def run_evaluation(
    originals,
    derived,
    root,
    pin_owner,
    dataset_bytes,
    cohort,
    queries,
    gold_bundle_ids,
    *,
    grants,
    restrictions,
    config,
    budget,
    plan,
    grade_budget,
    deadline_ms,
):
    """Evaluate every selected case or refuse without returning a partial report."""
    import time

    started = time.monotonic()
    from . import source_cohort_runner as source

    state = _State(plan, grade_budget)
    return source._run_cohort(
        originals,
        derived,
        root,
        pin_owner,
        dataset_bytes,
        cohort,
        queries,
        gold_bundle_ids,
        grants=grants,
        restrictions=restrictions,
        config=config,
        budget=budget,
        deadline_ms=deadline_ms,
        _grade=state,
        _started=started,
    )
