"""Private, bounded orchestration of a declared source cohort.

This module is under construction; it does not expose a public product interface.
"""

from dataclasses import dataclass


@dataclass(frozen=True, repr=False)
class Cohort:
    split: str
    case_ids: tuple


@dataclass(frozen=True, repr=False)
class Query:
    case_id: str
    payload: bytes
    space_id: str
    definition_fingerprint: str
    policy_id: str
    execution_fingerprint: str


@dataclass(frozen=True, repr=False)
class Config:
    config_id: str
    declaration_id: str


@dataclass(frozen=True, repr=False)
class Budget:
    source_directories: int
    source_ingestion_loads: int
    source_derived_batch_loads: int
    source_bytes: int
    pin_calls: int
    producer_calls: int
    binder_calls: int
    catalog_calls: int
    gold_calls: int
    ranking_calls: int
    geometry_calls: int
    aggregate_calls: int
    local_work: int
    local_payload: int
    binder_work: int
    binder_payload: int
    geometry_work: int
    geometry_payload: int
    aggregate_work: int
    aggregate_payload: int


@dataclass(frozen=True, repr=False)
class FailurePrefix:
    phase: str
    intended: int
    attempted: int
    completed: int
    refused: int
    pending: int


class CohortRunnerError(ValueError):
    """Content-free refusal of the entire cohort."""

    __slots__ = ("_progress",)

    def __init__(self, progress):
        super().__init__("cohort runner refused")
        self._progress = progress

    @property
    def progress(self):
        return self._progress


# Fixed independent maximum ceilings from the Root binding. They are logical
# reservations, and do not authorize physical source I/O.
_MAX_BUDGET = (
    7169,
    3965312,
    4391424,
    3391111408059907,
    1537,
    256,
    256,
    2816,
    256,
    256,
    256,
    1,
    134217728,
    268435456,
    34359738368,
    68719476736,
    17179869184,
    34359738368,
    134217728,
    268435456,
)


def _closed(value, cls):
    from dataclasses import fields

    if type(value) is not cls or type(value.__dict__) is not dict:
        return False
    names = tuple(item.name for item in fields(cls))
    attributes = value.__dict__
    if len(attributes) != len(names):
        return False
    max_name = max(map(len, names), default=0)
    for key in attributes:
        if type(key) is not str or len(key) > max_name or key not in names:
            return False
    return True


def _source_reservation(count):
    """Return the independently bounded logical source envelope for count cases."""
    if type(count) is not int or not 1 <= count <= 256:
        raise ValueError
    directories = 17 * count + 1
    ingestion = 9600 * count + 384
    batches = 10752 * count + 512
    size = (
        directories * 100925699
        + (ingestion + batches) * 404750404
        + ingestion * 2016386
        + count * 4986555627809
    )
    return directories + 11 * count, ingestion + 5888 * count, batches + 6400 * count, size


def _validate_budget(budget, count):
    """Admit exact caps and reserve complete fixed source/delegate envelopes."""
    from dataclasses import fields

    if not _closed(budget, Budget):
        raise ValueError
    values = tuple(getattr(budget, item.name) for item in fields(Budget))
    if any(
        type(value) is not int or value < 0 or value > cap
        for value, cap in zip(values, _MAX_BUDGET, strict=True)
    ):
        raise ValueError
    directories, ingestion, batches, size = _source_reservation(count)
    required = (
        directories,
        ingestion,
        batches,
        size,
        1 + 6 * count,
        count,
        count,
        11 * count,
        count,
        count,
        count,
        1,
    )
    if any(available < needed for available, needed in zip(values, required)):
        raise ValueError
    if (
        budget.binder_work < count * 134217728
        or budget.binder_payload < count * 268435456
        or budget.geometry_work < count * 67108864
        or budget.geometry_payload < count * 134217728
    ):
        raise ValueError


class _Meter:
    """Cumulative runner-owned reservations, separate from delegate ledgers."""

    __slots__ = ("work", "payload", "work_limit", "payload_limit", "check")

    def __init__(self, work_limit, payload_limit, check):
        self.work = 0
        self.payload = 0
        self.work_limit = work_limit
        self.payload_limit = payload_limit
        self.check = check

    def reserve(self, work, payload=0, *, category="local"):
        if category not in ("local", "json_emit", "string_compare"):
            raise ValueError
        self.check()
        if (
            type(work) is not int
            or type(payload) is not int
            or work < 0
            or payload < 0
            or work > self.work_limit - self.work
            or payload > self.payload_limit - self.payload
        ):
            raise ValueError
        self.work += work
        self.payload += payload

    def compare_strings(self, left, right):
        if type(left) is not str or type(right) is not str:
            raise ValueError
        charge = len(left) + len(right) + 1
        self.reserve(charge)
        if left < right:
            return -1
        self.reserve(charge)
        if left > right:
            return 1
        return 0


class _Deadline:
    __slots__ = ("end",)

    def __init__(self, started, milliseconds):
        if type(milliseconds) is not int or not 1 <= milliseconds <= 1200000:
            raise ValueError
        self.end = started + milliseconds / 1000

    def check(self):
        import time

        if time.monotonic() >= self.end:
            raise ValueError

    def remaining(self, cap):
        import time

        self.check()
        value = int((self.end - time.monotonic()) * 1000)
        if value < 1:
            raise ValueError
        return min(value, cap)


def _input_admission(
    originals,
    derived,
    root,
    owner,
    data,
    cohort,
    queries,
    gold_ids,
    grants,
    restrictions,
    config,
    budget,
    clock,
):
    """Admit the complete declaration and all selected inputs before source use."""
    import re

    from . import derived_store, raw_snapshot_pin, source_bound_stage_loss as binder
    from . import text_evaluation_dataset as dataset_module
    from .source_admission import OriginalStore

    clock.check()
    if (
        type(originals) is not OriginalStore
        or type(derived) is not derived_store.Store
        or type(owner) is not raw_snapshot_pin.PinOwner
        or not _closed(cohort, Cohort)
        or type(queries) is not tuple
        or not _closed(config, Config)
        or not _closed(budget, Budget)
        or type(data) is not bytes
        or not 1 <= len(data) <= 1048576
        or type(cohort.split) is not str
        or cohort.split not in ("tuning", "held_out")
        or type(cohort.case_ids) is not tuple
        or not 1 <= len(cohort.case_ids) <= 256
        or len(queries) != len(cohort.case_ids)
    ):
        raise ValueError
    count = len(cohort.case_ids)
    _validate_budget(budget, count)
    meter = _Meter(budget.local_work, budget.local_payload, clock.check)
    # This precharge reserves the fixed, content-free failure prefix, even if a
    # later operation exhausts the caller's local budget.
    # Fixed admission of the three closed input records and their bounded keys.
    meter.reserve(4096, 4096)
    meter.reserve(32, 1024)
    for ident in (config.config_id, config.declaration_id):
        meter.reserve(1)
        if type(ident) is not str or not 1 <= len(ident) <= 128:
            raise ValueError
        meter.reserve(len(ident) + 1)
        if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}", ident) is None:
            raise ValueError
    previous = None
    for ident, query in zip(cohort.case_ids, queries, strict=True):
        meter.reserve(1024, 1024)
        if type(ident) is not str or not 1 <= len(ident) <= 128 or not _closed(query, Query):
            raise ValueError
        if meter.compare_strings(query.case_id, ident):
            raise ValueError
        meter.reserve(len(ident) + 1)
        if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}", ident) is None:
            raise ValueError
        if previous is not None and meter.compare_strings(previous, ident) >= 0:
            raise ValueError
        previous = ident
        # Pinned binder admission enforces path, Gold ID and exact vector/ID
        # grammar; it does no source I/O and accepts this meter's interface.
        binder._preflight_inputs(
            root,
            data,
            ident,
            gold_ids,
            query.payload,
            (
                query.space_id,
                query.definition_fingerprint,
                query.policy_id,
                query.execution_fingerprint,
            ),
            min(clock.remaining(120000), 120000),
            meter,
        )
    meter.reserve(len(data) + 1, len(data))
    clock.check()
    dataset = _admit_dataset(data, deadline_ms=clock.remaining(5000))
    clock.check()
    meter.reserve(len(data) + 1)
    if (
        type(dataset) is not dataset_module.Dataset
        or type(dataset.cases) is not tuple
        or dataset.canonical_bytes != data
        or dataset.case_count != len(dataset.cases)
        or not 1 <= dataset.case_count <= 256
        or not 0 <= dataset.gold_atom_count <= 512
    ):
        raise ValueError
    meter.reserve(len(data) + 1 + dataset.case_count, len(dataset.cases) * 128)
    selected = []
    split_ids = []
    cursor = 0
    for case in dataset.cases:
        meter.reserve(1)
        if type(case) is not dataset_module.Case:
            raise ValueError
        if case.split == cohort.split:
            meter.reserve(1, 128)
            split_ids.append(case.case_id)
        if cursor < count and meter.compare_strings(case.case_id, cohort.case_ids[cursor]) == 0:
            if case.split != cohort.split:
                raise ValueError
            original, effective, restricted = binder._admit_authority(
                grants, restrictions, case.scope, meter, clock.check
            )
            meter.reserve(4, 512)
            selected.append((case, original, effective, restricted))
            cursor += 1
    if cursor != count:
        raise ValueError
    meter.reserve(count + len(split_ids), 128 * len(split_ids))
    selection = "FULL_ADMITTED_SPLIT" if tuple(split_ids) == cohort.case_ids else "DECLARED_SUBSET"
    return dataset, tuple(selected), selection, meter


def _pin_observation(owner, originals, derived, root, prior, meter, clock):
    """Revalidate the same borrowed capture, including its bounded row map."""
    import hashlib

    from . import raw_snapshot_files, raw_snapshot_pin, raw_snapshot_rows, raw_snapshot_selection

    if (
        type(owner) is not raw_snapshot_pin.PinOwner
        or owner.state != "ACTIVE"
        or owner.originals is not originals
        or owner.derived is not derived
        or owner.op is None
        or owner.op.path != root
    ):
        raise ValueError
    meter.reserve(1)
    clock.check()
    captured = _owner_check(owner, deadline_ms=clock.remaining(120000))
    clock.check()
    if (
        type(captured) is not raw_snapshot_pin.PinData
        or type(captured.pointer) is not raw_snapshot_selection.Pointer
        or type(captured.data) is not raw_snapshot_files.BoundSnapshotData
        or type(captured.data.row_map) is not raw_snapshot_rows.RawRowMap
        or captured is not owner.value
        or (prior is not None and captured is not prior)
    ):
        raise ValueError
    pointer = captured.pointer
    if type(pointer.pointer_bytes) is not bytes or len(pointer.pointer_bytes) > 512:
        raise ValueError
    meter.reserve(len(pointer.pointer_bytes) + 1, len(pointer.pointer_bytes))
    clock.check()
    parsed_pointer = raw_snapshot_selection.parse_pointer(pointer.pointer_bytes)
    clock.check()
    if parsed_pointer != pointer or captured.data.snapshot_id != pointer.snapshot_id:
        raise ValueError
    core = captured.data.core_bytes
    if type(core) is not bytes or len(core) > 262144:
        raise ValueError
    meter.reserve(len(core) + 66, 192)
    clock.check()
    digest = hashlib.sha256(core).hexdigest()
    clock.check()
    if meter.compare_strings(digest, pointer.core_sha256):
        raise ValueError
    row_map = captured.data.row_map
    if (
        type(row_map.rows) is not tuple
        or len(row_map.rows) > 512
        or type(row_map.map_bytes) is not bytes
        or len(row_map.map_bytes) > 16777216
    ):
        raise ValueError
    meter.reserve(len(row_map.map_bytes) + len(row_map.rows) + 1, len(row_map.map_bytes))
    clock.check()
    parsed = raw_snapshot_rows.parse(row_map.map_bytes)
    clock.check()
    meter.reserve(len(row_map.map_bytes) + len(row_map.rows) + 1)
    if parsed != row_map:
        raise ValueError
    return captured


def _pure_payload(report, pairs, meter, clock, max_work, max_payload):
    """Validate and stream the pinned pure identity preimage exactly once."""
    import json
    from dataclasses import fields
    from math import gcd
    from types import UnionType
    from typing import get_args

    from . import declared_cohort_metrics as pure

    if (
        not _closed(report, pure.Report)
        or type(report.cases) is not tuple
        or type(report.prefixes) is not tuple
        or type(report.transitions) is not tuple
        or type(report.case_count) is not int
        or not 1 <= report.case_count <= 256
        or report.case_count != len(pairs)
        or len(report.cases) != len(pairs)
        or len(report.prefixes) != 6
        or len(report.transitions) != 7
        or (
            report.formula_version,
            report.source_binding,
            report.input_origin,
            report.execution,
            report.qualification,
            report.chunk_metric_reason,
        )
        != (
            "declared-cohort-metrics-v1",
            "UNVERIFIED",
            "SUPPLIED_DECLARED_GEOMETRY_ONLY",
            "NOT_ATTESTED",
            "NOT_QUALIFIED",
            "NO_EXPLICIT_CHUNK_RELEVANCE_MAPPING",
        )
        or report.max_work != max_work
        or report.max_payload != max_payload
    ):
        raise ValueError
    for value, cap in (
        (report.checkpoint_work, max_work),
        (report.final_work, max_work),
        (report.checkpoint_payload, max_payload),
        (report.final_payload, max_payload),
    ):
        meter.reserve(1)
        if type(value) is not int or not 0 <= value <= cap:
            raise ValueError
    if (
        report.checkpoint_work > report.final_work
        or report.checkpoint_payload > report.final_payload
    ):
        raise ValueError
    for case, (case_id, geometry) in zip(report.cases, pairs, strict=True):
        meter.reserve(1)
        if (
            type(case) is not pure.CaseSummary
            or case.case_id != case_id
            or case.geometry_id != geometry.invocation_id
            or type(case.prefixes) is not tuple
            or len(case.prefixes) != 6
            or type(case.losses) is not tuple
            or len(case.losses) != 7
            or any(type(item) is not pure.PrefixCase for item in case.prefixes)
            or any(type(item) is not pure.LossCase for item in case.losses)
        ):
            raise ValueError
    if (
        any(type(item) is not pure.PrefixSummary for item in report.prefixes)
        or any(type(item) is not pure.TransitionSummary for item in report.transitions)
        or any(
            type(item.requirements) is not pure.CountLossSummary
            or type(item.alternatives) is not pure.CountLossSummary
            for item in report.transitions
        )
    ):
        raise ValueError
    expected_prefixes = tuple((pure._NAMES[index], cutoff) for index, cutoff in pure._PREFIXES)
    expected_edges = tuple((pure._NAMES[a], pure._NAMES[b]) for a, b in pure._EDGES)
    meter.reserve(64 + len(pairs) * 32, 2048)
    for case in report.cases:
        if (
            tuple((v.stage, v.cutoff) for v in case.prefixes) != expected_prefixes
            or tuple((v.source, v.target) for v in case.losses) != expected_edges
        ):
            raise ValueError
    if (
        tuple((v.stage, v.cutoff) for v in report.prefixes) != expected_prefixes
        or tuple((v.source, v.target) for v in report.transitions) != expected_edges
    ):
        raise ValueError
    if any(v.total != len(pairs) for v in (*report.prefixes, *report.transitions)):
        raise ValueError
    payload = (
        report.formula_version,
        report.source_binding,
        report.input_origin,
        report.execution,
        report.qualification,
        report.chunk_metric_reason,
        report.max_work,
        report.max_payload,
        report.checkpoint_work,
        report.checkpoint_payload,
        report.cases,
        report.prefixes,
        report.transitions,
    )
    allowed = (
        pure.PrefixCase,
        pure.LossCase,
        pure.CaseSummary,
        pure.PrefixSummary,
        pure.CountLossSummary,
        pure.TransitionSummary,
    )
    out = bytearray()

    def emit(part):
        meter.reserve(2 * len(part) + 1, 2 * len(part))
        if len(out) + len(part) > 1048576:
            raise ValueError
        out.extend(part)

    def walk(value, depth=0):
        meter.reserve(16)
        if depth > 16:
            raise ValueError
        if value is None:
            emit(b"null")
        elif type(value) is bool:
            emit(b"true" if value else b"false")
        elif type(value) is int:
            if value < 0 or value.bit_length() > 8192:
                raise ValueError
            bits = value.bit_length() + 2
            meter.reserve(bits * bits + bits, bits * 2)
            emit(str(value).encode("ascii"))
        elif type(value) is str:
            if len(value) > 8192:
                raise ValueError
            meter.reserve(12 * len(value) + 4, 12 * len(value) + 4)
            emit(json.dumps(value, ensure_ascii=True, separators=(",", ":")).encode("ascii"))
        elif type(value) is tuple:
            if len(value) > 256:
                raise ValueError
            emit(b"[")
            for index, item in enumerate(value):
                if index:
                    emit(b",")
                walk(item, depth + 1)
            emit(b"]")
        elif type(value) is pure.Ratio:
            meter.reserve(16, 128)
            if not _closed(value, pure.Ratio):
                raise ValueError
            a, b = value.numerator, value.denominator
            if (
                type(a) is not int
                or type(b) is not int
                or a < 0
                or b <= 0
                or a.bit_length() > 8192
                or b.bit_length() > 8192
            ):
                raise ValueError
            bits = a.bit_length() + b.bit_length() + 2
            meter.reserve(bits * bits + bits, 128)
            if gcd(a, b) != 1:
                raise ValueError
            emit(b'{"num":')
            walk(str(a), depth + 1)
            emit(b',"den":')
            walk(str(b), depth + 1)
            emit(b"}")
        elif type(value) in allowed:
            meter.reserve(64, 256)
            if not _closed(value, type(value)):
                raise ValueError
            emit(b"{")
            for index, item in enumerate(fields(value)):
                annotation = item.type
                types = get_args(annotation) if type(annotation) is UnionType else (annotation,)
                child = getattr(value, item.name)
                meter.reserve(2)
                if not any(type(child) is expected for expected in types):
                    raise ValueError
                if (
                    item.name.endswith("reason")
                    and child is not None
                    and child
                    not in (
                        "NO_GOLD_REQUIREMENTS",
                        "NO_GOLD_SOURCES",
                        "AMBIGUOUS_ALTERNATIVE_SOURCE_UNIVERSE",
                        "NO_DEFINED_SOURCE",
                        "NO_DEFINED_COMPLETE",
                        "NO_ELIGIBLE_BEFORE",
                        "NO_ELIGIBLE_COMPLETED",
                    )
                ):
                    raise ValueError
                if item.name.endswith("reasons"):
                    previous = ""
                    if len(child) > 3:
                        raise ValueError
                    for pair in child:
                        meter.reserve(8)
                        if (
                            type(pair) is not tuple
                            or len(pair) != 2
                            or pair[0]
                            not in (
                                "NO_GOLD_REQUIREMENTS",
                                "NO_GOLD_SOURCES",
                                "AMBIGUOUS_ALTERNATIVE_SOURCE_UNIVERSE",
                            )
                            or type(pair[1]) is not int
                            or not 1 <= pair[1] <= len(pairs)
                            or pair[0] == previous
                        ):
                            raise ValueError
                        previous = pair[0]
                if index:
                    emit(b",")
                walk(item.name, depth + 1)
                emit(b":")
                walk(child, depth + 1)
            emit(b"}")
        else:
            raise ValueError

    walk(payload)
    return _finish_pure(out, report.identity, meter, clock)


def _case_checks(
    dataset, case, query, original, effective, restricted, captured, result, diagnosis, meter, clock
):
    """Cross-check the producer and binder against independently derived inputs."""
    import hashlib
    import re

    from . import declared_stage_geometry as geometry_module
    from . import raw_dense_search, raw_hybrid_search, raw_lexical_search, raw_rank_fusion
    from . import source_bound_stage_loss as binder

    if (
        type(result) is not raw_hybrid_search.HybridResult
        or type(result.dense) is not raw_dense_search.DenseResult
        or type(result.lexical) is not raw_lexical_search.LexicalResult
        or type(result.fusion) is not raw_rank_fusion.FusionResult
        or type(result.dense.trace) is not raw_dense_search.DenseTrace
        or type(result.lexical.trace) is not raw_lexical_search.LexicalTrace
        or type(diagnosis) is not binder._Diagnosis
        or type(diagnosis.geometry) is not geometry_module.Diagnosis
    ):
        raise ValueError
    meter.reserve(len(case.question) + 1, 4 * len(case.question))
    question_bytes = case.question.encode("utf-8")
    meter.reserve(len(question_bytes) + len(query.payload) + 132, 384)
    clock.check()
    question_hash = hashlib.sha256(question_bytes).hexdigest()
    payload_hash = hashlib.sha256(query.payload).hexdigest()
    pointer_hash = hashlib.sha256(captured.pointer.pointer_bytes).hexdigest()
    clock.check()

    def authority_hash(grant):
        meter.reserve(8, 8 * 128 + 262144)
        clock.check()
        wire = [
            grant.model_dump(mode="json"),
            None if restricted is None else restricted.model_dump(mode="json"),
        ]
        clock.check()
        return binder._canonical_hash(
            wire, b"", meter, clock.check, ensure_ascii=False, limit=262144
        )

    original_hash = authority_hash(original)
    effective_hash = authority_hash(effective)
    meter.reserve(4, 512)
    filter_id = "sha256:" + binder._canonical_hash(
        {
            "original_authority": original_hash,
            "case_id": case.case_id,
            "policy": "case-scope-intersection-v1",
        },
        b"slaif-stage-filter-v1\n",
        meter,
        clock.check,
    )
    query_id = binder._canonical_hash(
        {
            "kind": "raw-hybrid-query/v1",
            "snapshot_id": captured.pointer.snapshot_id,
            "catalog_id": result.catalog_id,
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
    pairs = (
        (result.snapshot_id, captured.pointer.snapshot_id),
        (result.query_id, query_id),
        (result.query_text_sha256, question_hash),
        (result.query_payload_sha256, payload_hash),
        (result.authority_sha256, effective_hash),
        (result.query_origin, "SUPPLIED_UNVERIFIED"),
        (result.qualification, "NOT_QUALIFIED"),
        (diagnosis.dataset_id, dataset.dataset_id),
        (diagnosis.split_id, dataset.split_id),
        (diagnosis.case_id, case.case_id),
        (diagnosis.question_sha256, question_hash),
        (diagnosis.payload_sha256, payload_hash),
        (diagnosis.authority_sha256, effective_hash),
        (diagnosis.original_authority_sha256, original_hash),
        (diagnosis.filter_id, filter_id),
        (diagnosis.pointer_sha256, pointer_hash),
        (diagnosis.snapshot_id, result.snapshot_id),
        (diagnosis.catalog_id, result.catalog_id),
        (diagnosis.query_id, result.query_id),
        (diagnosis.dense_trace_id, result.dense.trace.trace_id),
        (diagnosis.lexical_trace_id, result.lexical.trace.trace_id),
        (result.dense.trace.query_space_id, query.space_id),
        (result.dense.trace.query_definition_fingerprint, query.definition_fingerprint),
        (result.dense.trace.query_policy_id, query.policy_id),
        (result.dense.trace.query_execution_fingerprint, query.execution_fingerprint),
        (result.dense.trace.snapshot_id, result.snapshot_id),
        (result.dense.trace.catalog_id, result.catalog_id),
        (result.dense.trace.query_payload_sha256, payload_hash),
        (result.dense.trace.authority_sha256, effective_hash),
        (result.lexical.trace.snapshot_id, result.snapshot_id),
        (result.lexical.trace.catalog_id, result.catalog_id),
        (result.lexical.trace.query_text_sha256, question_hash),
        (result.lexical.trace.authority_sha256, effective_hash),
        (result.fusion.snapshot_id, result.snapshot_id),
        (result.fusion.catalog_id, result.catalog_id),
        (result.fusion.query_id, result.query_id),
        (result.dense.trace.input_origin, "SUPPLIED_UNVERIFIED"),
        (result.dense.trace.qualification, "NOT_QUALIFIED"),
        (result.dense.trace.authorization_status, "SUPPLIED_SCOPE_CHECKS_ONLY"),
        (result.dense.trace.execution_status, "NOT_ATTESTED"),
        (result.lexical.trace.input_origin, "SUPPLIED_UNVERIFIED"),
        (result.lexical.trace.qualification, "NOT_QUALIFIED"),
        (result.lexical.trace.authorization_status, "SUPPLIED_SCOPE_CHECKS_ONLY"),
        (result.lexical.trace.execution_status, "NOT_ATTESTED"),
    )
    for left, right in pairs:
        if meter.compare_strings(left, right) != 0:
            raise ValueError
    markers = (
        (diagnosis.source_status, "OWNED_BINDING_CALLS_ONLY"),
        (diagnosis.authorization, "SUPPLIED_SCOPE_CHECKS_ONLY"),
        (diagnosis.score_order, "SUPPLIED_SCORE_ORDER_NOT_REEXECUTED"),
        (diagnosis.execution, "NOT_ATTESTED"),
        (diagnosis.temporal, "SEQUENTIAL_OBSERVATIONS_NOT_ATOMIC"),
        (diagnosis.gold_eligibility, "NOT_CHECKED"),
        (diagnosis.held_out, "NOT_CHECKED"),
        (diagnosis.origin, "SUPPLIED_UNVERIFIED"),
        (diagnosis.current_rights, "NOT_CHECKED"),
        (diagnosis.scale, "NOT_QUALIFIED"),
        (diagnosis.model, "NOT_QUALIFIED"),
        (diagnosis.quality, "NOT_QUALIFIED"),
        (diagnosis.visual, "NOT_QUALIFIED"),
        (diagnosis.license, "NOT_CHECKED"),
        (diagnosis.independent_audit, "NOT_CHECKED"),
        (diagnosis.mvp, "NOT_QUALIFIED"),
        (diagnosis.qualification, "NOT_QUALIFIED"),
        (diagnosis.accounting, "FINAL_TOTALS_NOT_IN_INVOCATION_ID"),
        (diagnosis.geometry.chunk_metric_reason, "NO_EXPLICIT_CHUNK_RELEVANCE_MAPPING"),
        (diagnosis.geometry.stage_origin, "SUPPLIED_STAGE_RELATIONS_ONLY"),
        (diagnosis.geometry.eligibility, "NOT_CHECKED"),
        (diagnosis.geometry.execution, "NOT_ATTESTED"),
    )
    for actual, expected in markers:
        if meter.compare_strings(actual, expected):
            raise ValueError
    for value, ceiling in (
        (diagnosis.pre_final_work, 134217728),
        (diagnosis.final_work, 134217728),
        (diagnosis.pre_final_payload, 268435456),
        (diagnosis.final_payload, 268435456),
        (diagnosis.geometry.work, 67108864),
        (diagnosis.geometry.serialization_budget, 134217728),
    ):
        meter.reserve(1)
        if type(value) is not int or not 0 <= value <= ceiling:
            raise ValueError
    if (
        diagnosis.pre_final_work > diagnosis.final_work
        or diagnosis.pre_final_payload > diagnosis.final_payload
    ):
        raise ValueError
    meter.reserve(64, 2048)
    chosen = 0
    for requirement in case.requirements:
        meter.reserve(1)
        for alternative in requirement.alternatives:
            meter.reserve(1)
            chosen += len(alternative)
    if (
        type(diagnosis.generation) is not int
        or diagnosis.generation != captured.pointer.generation
        or type(diagnosis.dataset_case_count) is not int
        or not 1 <= diagnosis.dataset_case_count <= 256
        or diagnosis.dataset_case_count != dataset.case_count
        or type(diagnosis.dataset_atom_occurrences) is not int
        or not 0 <= diagnosis.dataset_atom_occurrences <= 512
        or diagnosis.dataset_atom_occurrences != dataset.gold_atom_count
        or type(diagnosis.chosen_atom_occurrences) is not int
        or not 0 <= diagnosis.chosen_atom_occurrences <= 512
        or diagnosis.chosen_atom_occurrences != chosen
        or type(diagnosis.eligible_row_count) is not int
        or not 0 <= diagnosis.eligible_row_count <= 4096
        or diagnosis.source_envelope != (5888, 6400, 12288, 4986555627809)
        or diagnosis.geometry.source_binding != "UNVERIFIED"
        or diagnosis.geometry.qualification != "NOT_QUALIFIED"
        or result.dense.trace.k != 60
        or result.dense.trace.partition_cap != 60
        or result.lexical.trace.k != 60
        or result.lexical.trace.partition_cap != 60
    ):
        raise ValueError
    for name in ("invocation_id", "gold_binding_id", "ranking_binding_id"):
        value = getattr(diagnosis, name)
        meter.reserve(72)
        if type(value) is not str or re.fullmatch(r"sha256:[0-9a-f]{64}", value) is None:
            raise ValueError
    if (
        type(diagnosis.geometry.invocation_id) is not str
        or re.fullmatch(r"sha256:[0-9a-f]{64}", diagnosis.geometry.invocation_id) is None
    ):
        raise ValueError
    return (
        case.case_id,
        question_hash,
        payload_hash,
        original_hash,
        effective_hash,
        filter_id,
        result.catalog_id,
        result.query_id,
        diagnosis.gold_binding_id,
        diagnosis.ranking_binding_id,
        diagnosis.invocation_id,
        diagnosis.geometry.invocation_id,
        dataset.case_count,
        dataset.gold_atom_count,
        chosen,
        diagnosis.eligible_row_count,
    )


@dataclass(frozen=True, repr=False)
class CohortReport:
    identity_payload: bytes
    identity: str
    final_work: int
    final_payload: int


def _serialize(
    dataset,
    cohort,
    selection,
    config,
    budget,
    captured,
    metadata,
    pure_report,
    pure_payload,
    binder_totals,
    meter,
    clock,
):
    """Emit a bounded private identity, embedding the pure JSON value once."""
    import hashlib
    import json
    from dataclasses import fields

    def encode(value, limit):
        # All operands here were bounded at admission or are fixed metadata.
        meter.reserve(65536, 65536)
        clock.check()
        encoded = json.dumps(
            value, ensure_ascii=True, separators=(",", ":"), allow_nan=False
        ).encode("ascii")
        clock.check()
        if len(encoded) > limit:
            raise ValueError
        meter.reserve(len(encoded) + 1, len(encoded))
        return encoded

    count = len(metadata)
    case_keys = (
        "case_id",
        "question_sha256",
        "payload_sha256",
        "original_authority_sha256",
        "effective_authority_sha256",
        "filter_id",
        "catalog_id",
        "query_id",
        "gold_binding_id",
        "ranking_binding_id",
        "binder_invocation_id",
        "geometry_invocation_id",
        "dataset_case_count",
        "dataset_atom_occurrences",
        "chosen_atom_occurrences",
        "eligible_row_count",
    )
    meter.reserve(len(captured.pointer.pointer_bytes) + 66, 192)
    pointer_hash = hashlib.sha256(captured.pointer.pointer_bytes).hexdigest()
    caps = {item.name: getattr(budget, item.name) for item in fields(Budget)}
    sources = _source_reservation(count)
    ledger = {
        "direct_own_observed": {
            "dataset": 1,
            "pin": 1 + count,
            "producer": count,
            "binder": count,
            "aggregate": 1,
        },
        "static_worstcase_reserved": {
            "directories": sources[0],
            "ingestion_loads": sources[1],
            "derived_batch_loads": sources[2],
            "bytes": sources[3],
            "transitive_pin": 5 * count,
            "catalog": 11 * count,
            "gold": count,
            "ranking": count,
            "geometry": count,
        },
        "binder_callee_reported": binder_totals,
        "dataset_internal": "UNMEASURED_BY_RUNNER",
        "binder_geometry": "OVERLAPPING_NOT_ADDITIVE",
        "source_observation": "SEQUENTIAL_NOT_ATOMIC",
    }
    header = {
        "schema": "slaif-source-cohort-runner-v1",
        "formula": "source-cohort-v1",
        "dataset_id": dataset.dataset_id,
        "split_id": dataset.split_id,
        "config_id": config.config_id,
        "declaration_id": config.declaration_id,
        "split": cohort.split,
        "selection_kind": selection,
        "dataset_case_count": dataset.case_count,
        "dataset_gold_occurrences": dataset.gold_atom_count,
        "synthetic_count": dataset.synthetic_count,
        "human_declared_count": dataset.human_declared_count,
        "selected_count": count,
        "progress": {
            "intended": count,
            "attempted": count,
            "completed": count,
            "refused": 0,
            "pending": 0,
        },
        "pointer_sha256": pointer_hash,
        "generation": captured.pointer.generation,
        "snapshot_id": captured.pointer.snapshot_id,
        "statuses": {
            "split": "STRUCTURAL_ONLY",
            "authorship": "DECLARED_UNVERIFIED",
            "rights": "DECLARED_UNVERIFIED",
            "producer": "COMPLETED",
            "current_rights": "NOT_CHECKED",
            "policy": "NOT_CHECKED",
            "encoder": "NOT_QUALIFIED",
            "model": "NOT_QUALIFIED",
            "baseline": "NOT_RUN",
            "source": "SEQUENTIAL_NOT_ATOMIC",
        },
        "caps": caps,
        "ledger": ledger,
    }
    # The checkpoint precedes final encoding and hashing; final counters are
    # returned separately, so neither identity is self-referential.
    meter.reserve(128, 4096)
    header["checkpoint_work"] = meter.work
    header["checkpoint_payload"] = meter.payload
    encoded_header = encode(header, 65536)
    pieces = [encoded_header[:-1], b',"cases":[']
    for index, item in enumerate(metadata):
        meter.reserve(16, 2048)
        if index:
            pieces.append(b",")
        pieces.append(encode(dict(zip(case_keys, item, strict=True)), 2048))
    wrapper = {
        "identity": pure_report.identity,
        "final_work": pure_report.final_work,
        "final_payload": pure_report.final_payload,
    }
    wrapper_bytes = encode(wrapper, 4096)
    pieces.extend((b'],"pure":{"identity_payload":', pure_payload, b",", wrapper_bytes[1:], b"}"))
    size = sum(len(piece) for piece in pieces)
    if size > 1642496 or size > 2097152:
        raise ValueError
    return _finish_outer(pieces, size, meter, clock)



def _hash_identity(domain, payload):
    import hashlib

    return "sha256:" + hashlib.sha256(domain + payload).hexdigest()


def _copy_payload(value):
    return bytes(value)


def _join_payload(pieces):
    return b"".join(pieces)


def _finish_pure(out, expected, meter, clock):
    domain = b"slaif-declared-cohort-metrics-v1\n"
    size = len(out)
    # Reserve concatenation, hash traversal, and the returned bytes copy before any.
    meter.reserve(3 * size + 2 * len(domain) + 128, 2 * size + len(domain) + 192)
    clock.check()
    identity = _hash_identity(domain, out)
    clock.check()
    if identity != expected:
        raise ValueError
    return _copy_payload(out)


def _finish_outer(pieces, size, meter, clock):
    domain = b"slaif-source-cohort-runner-v1\n"
    # Reserve the join, domain concatenation, and hash traversal together.
    meter.reserve(3 * size + 2 * len(domain) + 128, 2 * size + len(domain) + 192)
    clock.check()
    payload = _join_payload(pieces)
    identity = _hash_identity(domain, payload)
    clock.check()
    meter.reserve(16, 256)
    return CohortReport(payload, identity, meter.work, meter.payload)

def _admit_dataset(*args, **kwargs):
    from . import text_evaluation_dataset

    return text_evaluation_dataset.admit(*args, **kwargs)


def _owner_check(owner, **kwargs):
    return owner.check(**kwargs)


def _produce(*args, **kwargs):
    from . import raw_hybrid_search

    return raw_hybrid_search.search(*args, **kwargs)


def _bind(*args, **kwargs):
    from . import source_bound_stage_loss

    return source_bound_stage_loss.bind_stages(*args, **kwargs)


def _aggregate(*args, **kwargs):
    from . import declared_cohort_metrics

    return declared_cohort_metrics.aggregate(*args, **kwargs)


def run_cohort(
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
    deadline_ms,
):
    """Run the entire supplied cohort or refuse without returning partial metrics."""
    import time

    started = time.monotonic()
    admitted = False
    phase = "PREFLIGHT"
    intended = attempted = completed = 0
    try:
        clock = _Deadline(started, deadline_ms)
        dataset, selected, selection, meter = _input_admission(
            originals,
            derived,
            root,
            pin_owner,
            dataset_bytes,
            cohort,
            queries,
            gold_bundle_ids,
            grants,
            restrictions,
            config,
            budget,
            clock,
        )
        intended = len(selected)
        admitted = True
        meter.reserve(1)
        captured = _pin_observation(pin_owner, originals, derived, root, None, meter, clock)
        metadata = []
        pairs = []
        binder_work = binder_payload = 0
        for query, (case, original, effective, restricted) in zip(queries, selected, strict=True):
            phase = "CASE_PIN"
            attempted += 1
            meter.reserve(1)
            _pin_observation(pin_owner, originals, derived, root, captured, meter, clock)
            phase = "PRODUCER"
            meter.reserve(1)
            clock.check()
            result = _produce(
                originals,
                derived,
                root,
                captured.pointer.snapshot_id,
                case.question,
                query.payload,
                query_space_id=query.space_id,
                query_definition_fingerprint=query.definition_fingerprint,
                query_policy_id=query.policy_id,
                query_execution_fingerprint=query.execution_fingerprint,
                grants=effective,
                restrictions=restricted,
                dense_k=60,
                lexical_k=60,
                partition_cap=60,
                k=60,
                deadline_ms=clock.remaining(120000),
                trace=True,
            )
            clock.check()
            phase = "BINDER"
            meter.reserve(1)
            clock.check()
            diagnosis = _bind(
                originals,
                derived,
                root,
                pin_owner,
                dataset_bytes,
                case.case_id,
                gold_bundle_ids,
                result,
                query.payload,
                query_space_id=query.space_id,
                query_definition_fingerprint=query.definition_fingerprint,
                query_policy_id=query.policy_id,
                query_execution_fingerprint=query.execution_fingerprint,
                grants=original,
                restrictions=restricted,
                deadline_ms=clock.remaining(120000),
            )
            clock.check()
            item = _case_checks(
                dataset,
                case,
                query,
                original,
                effective,
                restricted,
                captured,
                result,
                diagnosis,
                meter,
                clock,
            )
            if (
                type(diagnosis.final_work) is not int
                or not 0 <= diagnosis.final_work <= 134217728
                or type(diagnosis.final_payload) is not int
                or not 0 <= diagnosis.final_payload <= 268435456
            ):
                raise ValueError
            binder_work += diagnosis.final_work
            binder_payload += diagnosis.final_payload
            meter.reserve(4, 256)
            metadata.append(item)
            pairs.append((case.case_id, diagnosis.geometry))
            completed += 1
        phase = "AGGREGATE"
        meter.reserve(len(pairs) + 1, 128 * len(pairs))
        pairs = tuple(pairs)
        clock.check()
        aggregate = _aggregate(
            pairs,
            deadline_ms=clock.remaining(10000),
            max_work=budget.aggregate_work,
            max_payload=budget.aggregate_payload,
        )
        clock.check()
        phase = "SERIALIZE"
        payload = _pure_payload(
            aggregate, pairs, meter, clock, budget.aggregate_work, budget.aggregate_payload
        )
        report = _serialize(
            dataset,
            cohort,
            selection,
            config,
            budget,
            captured,
            metadata,
            aggregate,
            payload,
            {"work": binder_work, "payload": binder_payload},
            meter,
            clock,
        )
        clock.check()
        return report
    except Exception:
        progress = None
        if admitted:
            refused = 1 if phase in ("CASE_PIN", "PRODUCER", "BINDER") else 0
            progress = FailurePrefix(
                phase, intended, attempted, completed, refused, intended - attempted
            )
        raise CohortRunnerError(progress) from None
