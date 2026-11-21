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


def _envelope_closed(originals, derived, owner, cohort, case_records, config, budget, data):
    """The exact closed input envelope, shared by both admission entries."""
    from . import derived_store, raw_snapshot_pin
    from .source_admission import OriginalStore

    return (
        type(originals) is OriginalStore
        and type(derived) is derived_store.Store
        and type(owner) is raw_snapshot_pin.PinOwner
        and _closed(cohort, Cohort)
        and type(case_records) is tuple
        and _closed(config, Config)
        and _closed(budget, Budget)
        and type(data) is bytes
        and 1 <= len(data) <= 1048576
        and type(cohort.split) is str
        and cohort.split in ("tuning", "held_out")
        and type(cohort.case_ids) is tuple
        and 1 <= len(cohort.case_ids) <= 256
        and len(case_records) == len(cohort.case_ids)
    )


def _fixed_admission(config, budget, clock):
    """Create the meter and reserve the fixed content-free admission prefix."""
    import re

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
    return meter


def _case_id_shape(meter, ident):
    """Nominal per-case envelope: the fixed reserve and case-ID bounds."""
    meter.reserve(1024, 1024)
    if type(ident) is not str or not 1 <= len(ident) <= 128:
        raise ValueError


def _case_id_grammar(meter, ident, previous):
    """Ordered case-ID grammar; returns the admitted id as the new previous."""
    import re

    meter.reserve(len(ident) + 1)
    if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}", ident) is None:
        raise ValueError
    if previous is not None and meter.compare_strings(previous, ident) >= 0:
        raise ValueError
    return ident


def _dataset_selection_tail(data, cohort, grants, restrictions, meter, clock):
    """The single ordered dataset admission and scope/selection tail."""
    from . import source_bound_stage_loss as binder
    from . import text_evaluation_dataset as dataset_module

    count = len(cohort.case_ids)
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
    return dataset, tuple(selected), selection


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
    from . import source_bound_stage_loss as binder

    clock.check()
    if not _envelope_closed(originals, derived, owner, cohort, queries, config, budget, data):
        raise ValueError
    count = len(cohort.case_ids)
    _validate_budget(budget, count)
    meter = _fixed_admission(config, budget, clock)
    previous = None
    for ident, query in zip(cohort.case_ids, queries, strict=True):
        _case_id_shape(meter, ident)
        if not _closed(query, Query):
            raise ValueError
        if meter.compare_strings(query.case_id, ident):
            raise ValueError
        previous = _case_id_grammar(meter, ident, previous)
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
    dataset, selected, selection = _dataset_selection_tail(
        data, cohort, grants, restrictions, meter, clock
    )
    return dataset, selected, selection, meter


def _declaration_admission(
    originals,
    derived,
    root,
    owner,
    data,
    cohort,
    identifiers,
    gold_ids,
    grants,
    restrictions,
    config,
    budget,
    clock,
):
    """Admit the complete declared cohort before any source use, query-free.

    Private pre-encode twin of _input_admission over the shared private
    pieces: the exact closed envelope, the fixed meter/config admission,
    the ordered case-ID grammar and the single dataset/scope/selection
    tail.  Each declared case differs only in its nominal record check
    and the accepted query-free binder declaration primitive, which
    establishes root, Gold ID and encoder identifier grammar only.  No
    Query, payload or vector work occurs, and no pin, catalog, producer,
    encoding, current policy or source-rights claim is made or checked.
    """
    from . import source_bound_stage_loss as binder

    clock.check()
    if not _envelope_closed(originals, derived, owner, cohort, identifiers, config, budget, data):
        raise ValueError
    count = len(cohort.case_ids)
    _validate_budget(budget, count)
    meter = _fixed_admission(config, budget, clock)
    previous = None
    for ident, case_identifiers in zip(cohort.case_ids, identifiers, strict=True):
        _case_id_shape(meter, ident)
        if type(case_identifiers) is not tuple:
            raise ValueError
        previous = _case_id_grammar(meter, ident, previous)
        # Query-free binder declaration admission enforces path, Gold ID and
        # declared identifier grammar only; it does no source I/O, no vector
        # work, and accepts this meter's interface.
        binder._preflight_declaration(
            root,
            data,
            ident,
            gold_ids,
            case_identifiers,
            min(clock.remaining(120000), 120000),
            meter,
        )
    dataset, selected, selection = _dataset_selection_tail(
        data, cohort, grants, restrictions, meter, clock
    )
    return dataset, selected, selection, meter


def _pin_capture_identity(owner, captured, prior, meter, clock):
    """Bounded pointer/core/row-map/identity evidence for one post-reload capture.

    Shared by the legacy owned observation and the guarded private
    initial cohort pin path: the caller performs the genuine reload
    first - the legacy owned ``check`` or the fixed non-reacquiring
    ``PinOwner._held_revalidation`` body while already holding the
    owner guard - and this helper applies the exact same bounded
    pointer, core-digest and row-map identity checks in their original
    order, without re-acquiring custody.
    """
    import hashlib

    from . import raw_snapshot_files, raw_snapshot_pin, raw_snapshot_rows, raw_snapshot_selection

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


def _pin_observation(owner, originals, derived, root, prior, meter, clock):
    """Revalidate the same borrowed capture, including its bounded row map."""
    from . import raw_snapshot_pin

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
    return _pin_capture_identity(owner, captured, prior, meter, clock)


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
    return _run_cohort(
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
    )


def _run_cohort(
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
    _grade=None,
    _started=None,
):
    """Fixed source loop; optional grading state is created only by its module."""
    import time

    started = time.monotonic() if _started is None else _started
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
        if _grade is not None:
            from . import evaluation_program as graded

            if type(_grade) is not graded._State:
                raise ValueError
            graded._prepare(
                _grade,
                dataset,
                selected,
                selection,
                cohort,
                queries,
                gold_bundle_ids,
                config,
                budget,
                clock,
            )
        intended = len(selected)
        admitted = True
        meter.reserve(1)
        if _grade is not None:
            phase = "CATALOG"
        captured = _pin_observation(pin_owner, originals, derived, root, None, meter, clock)
        if _grade is not None:
            phase = "CATALOG"
            graded._catalog(_grade, originals, derived, root, pin_owner, captured, clock)
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
            if _grade is not None:
                phase = "GRADE_PIN"
                graded._case(
                    _grade,
                    originals,
                    derived,
                    root,
                    pin_owner,
                    captured,
                    case,
                    effective,
                    restricted,
                    result,
                    item,
                    clock,
                )
                phase = "GRADE_CASE"
            meter.reserve(4, 256)
            metadata.append(item)
            pairs.append((case.case_id, diagnosis.geometry))
            completed += 1
        phase = "SOURCE_AGGREGATE" if _grade is not None else "AGGREGATE"
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
        phase = "SOURCE_SERIALIZE" if _grade is not None else "SERIALIZE"
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
        if _grade is not None:
            phase = "GRADE_AGGREGATE"
            return graded._finish(
                _grade,
                report,
                dataset,
                cohort,
                selection,
                config,
                captured,
                pin_owner,
                originals,
                derived,
                root,
                clock,
            )
        clock.check()
        return report
    except Exception:
        if _grade is not None:
            from . import evaluation_program as graded

            grade_error = graded._failure(_grade, admitted, phase, intended, attempted, completed)
        else:
            progress = None
            if admitted:
                refused = 1 if phase in ("CASE_PIN", "PRODUCER", "BINDER") else 0
                progress = FailurePrefix(
                    phase, intended, attempted, completed, refused, intended - attempted
                )
            raise CohortRunnerError(progress) from None
    raise grade_error from None


class _PreparedPinRefused(Exception):
    """Internal refusal of the shared prepared pin body with its admission stage."""

    __slots__ = ("admitted", "intended")

    def __init__(self, admitted, intended):
        super().__init__("prepared pin refused")
        self.admitted = admitted
        self.intended = intended


def _current_cohort_prepared_pin(
    admission,
    pin_owner,
    dataset_bytes,
    cohort,
    identifiers,
    gold_ids,
    config,
    budget,
    *,
    deadline_ms,
    case_id=None,
):
    """Shared genuine query-free declaration and guarded first cohort pin body.

    The factored fixed internal prepared state of the guarded private
    initial source-cohort pin entry, shared with the one genuine
    encoder-to-producer selected case entry: the exact owner-selected
    operation, root and stores retained before the genuine declaration
    admission, one actual source deadline started once and clipped to
    the genuine admission's original end before any semantic work, the
    genuine source declaration admission over the canonical dataset and
    exact selected cohort, one genuine nonblocking borrowed owner guard
    with the pre-dispatch PinData retained and tied to the exact
    retained operation, root and stores, the pure all-case scope
    admission with the real reader checks, the same held value and
    operation at the pre-load association, the genuine same-admission
    selected reread immediately before the real fixed
    ``PinOwner._held_revalidation`` body that calls ``_load`` and the
    full directory, the same held value and operation after the actual
    reload, the shared bounded pointer/core/row-map identity checks
    with the retained value as prior, the detached full-grants
    verification and the trailing meter charge before the final real
    selected observation, and the exact cutoff and required
    restoration/release.  One actual cohort pin reload and the original
    saved end throughout; the saved operation's end is restored and the
    guard released on all exits.  When an exact selected case ID is
    supplied, the genuine declaration's exact selected case index is
    resolved from the one genuine declaration before the actual initial
    reload and carried out as an internal result; the legacy path with
    no case ID keeps the original body unchanged.  Ordinary refusal
    raises the internal ``_PreparedPinRefused`` carrying the admission
    stage; a non-Exception BaseException propagates by identity.
    """
    import time

    from . import private_policy_pin_eligibility as pin_eligibility
    from . import private_policy_request as policy_request
    from . import provenance_records as provenance
    from . import raw_snapshot_pin, raw_snapshot_rows
    from . import raw_snapshot_selection as snapshot_selection
    from . import supplied_policy_eligibility as policy_eligibility

    admitted = False
    intended = 0
    try:
        if (
            type(admission) is not policy_request.PolicyRequestAdmission
            or type(pin_owner) is not raw_snapshot_pin.PinOwner
            or type(dataset_bytes) is not bytes
            or not 1 <= len(dataset_bytes) <= 1048576
            or not _closed(cohort, Cohort)
            or not _closed(config, Config)
            or not _closed(budget, Budget)
            or type(cohort.case_ids) is not tuple
            or not 1 <= len(cohort.case_ids) <= 256
            or type(identifiers) is not tuple
            or len(identifiers) != len(cohort.case_ids)
            or type(gold_ids) is not tuple
            or type(deadline_ms) is not int
            or not 1 <= deadline_ms <= 30000
            or (case_id is not None
                and (type(case_id) is not str or not 1 <= len(case_id) <= 128))
            or pin_owner.op is None
            or pin_owner.value is None
            or pin_owner.originals is None
            or pin_owner.derived is None
        ):
            raise ValueError
        # The exact owner-selected operation, root and stores retained
        # for the genuine declaration admission; the active owner is
        # tied to them under the guard before any protected work.
        saved_op = pin_owner.op
        saved_originals = pin_owner.originals
        saved_derived = pin_owner.derived
        saved_root = saved_op.path
        # One actual source deadline, started once and clipped to the
        # genuine admission's original end before any semantic work; the
        # request end is never reset or extended.
        started = time.monotonic()
        clock = _Deadline(started, deadline_ms)
        clock.end = min(clock.end, admission._end)
        clock.check()
        # Reuse the isolated selected-policy and bounded full principal
        # primitives: one bounded coherent in-memory isolated snapshot of
        # the retained selected policy, the verified immutable full
        # principal anchor and the detached nominal authority bound to
        # it; no independent parse or trust of caller-selected authority.
        policy_snapshot = pin_eligibility._isolated_policy_snapshot(admission)
        anchor_snapshot = pin_eligibility._bounded_admission(
            pin_eligibility._admitted_principal_grants(policy_snapshot, admission.principal_id)
        )
        grants = pin_eligibility._bound_grants(admission, anchor_snapshot)
        clock.check()
        # The genuine source declaration admission over the canonical
        # dataset and exact selected cohort, supplied declaration grammar
        # and verified full principal anchor, with no added restriction.
        dataset, selected, selection, meter = _declaration_admission(
            saved_originals,
            saved_derived,
            saved_root,
            pin_owner,
            dataset_bytes,
            cohort,
            identifiers,
            gold_ids,
            grants,
            None,
            config,
            budget,
            clock,
        )
        intended = len(selected)
        admitted = True
        # The exact selected case index of the complete ordered
        # declaration, resolved from the one genuine declaration before
        # the actual initial reload and carried out as an internal
        # result, with no new I/O.
        position = None
        if case_id is not None:
            for index, (case, _original, _effective, _restricted) in enumerate(selected):
                meter.reserve(1)
                if meter.compare_strings(case.case_id, case_id) == 0:
                    position = index
                    break
            if position is None:
                raise ValueError
            meter.reserve(1)
            clock.check()
        # One genuine nonblocking borrowed owner guard; the exact
        # original operation, value and their association are retained
        # and verified, never trusted.
        pin_eligibility._borrowed_owner(pin_owner)
        try:
            # The pre-dispatch PinData retained under the genuine guard;
            # the active owner is tied to the exact retained operation,
            # root and stores before any protected work, never trusted.
            saved_value = pin_owner.value
            if (
                pin_owner.state != "ACTIVE"
                or pin_owner.op is not saved_op
                or saved_op.path != saved_root
                or pin_owner.originals is not saved_originals
                or pin_owner.derived is not saved_derived
                or type(saved_op) is not snapshot_selection._Operation
                or type(saved_value) is not raw_snapshot_pin.PinData
            ):
                raise ValueError
            meter.reserve(1)
            clock.check()
            _pointer, core, membership, _membership_bytes = pin_eligibility._held_capture(
                pin_owner
            )
            meter.reserve(1)
            clock.check()
            # One unavailable table and the actual canonical row binding
            # under the guard, from the retained pre-dispatch value.
            unavailable = set(
                policy_eligibility.unavailable_partitions(policy_snapshot, membership)
            )
            meter.reserve(1)
            row_map = saved_value.data.row_map
            if type(row_map) is not raw_snapshot_rows.RawRowMap:
                raise ValueError
            if raw_snapshot_rows.bind(core, row_map.map_bytes) != row_map:
                raise ValueError
            meter.reserve(len(row_map.map_bytes) + 1, len(row_map.map_bytes))
            clock.check()
            # Bounded scope admission with the real reader checks, in
            # the original declaration order: every derived per-case
            # scope must have readable members and every readable
            # retained member must be available for every exact selected
            # case before any new full directory or source read; an
            # unavailable partition outside the effective case scope does
            # not deny the case.  Each retained scope is admitted once
            # as its typed canonical record and reused by the per-case
            # scan instead of re-parsing the same whole scopes.
            scoped = []
            for entry in membership.entries:
                meter.reserve(1)
                scoped.append(
                    (entry, provenance.admit_record("Scope", entry.scope_bytes))
                )
            meter.reserve(1)
            clock.check()
            for _case, _original, effective, _restricted in selected:
                meter.reserve(1)
                usable = False
                for entry, scope in scoped:
                    meter.reserve(1)
                    if not provenance.reader_allows(scope, effective, None):
                        continue
                    usable = True
                    if entry.partition_id in unavailable:
                        raise ValueError
                if not usable:
                    raise ValueError
                meter.reserve(1)
                clock.check()
            # The guarded variant: the actual clipped cooperative end
            # on the saved operation, with its actual prior end restored
            # on all exits.
            prior_end = saved_op.end
            saved_op.end = clock.end
            try:
                # The same held value and operation at the pre-load
                # association, never trusted.
                if pin_owner.op is not saved_op or pin_owner.value is not saved_value:
                    raise ValueError
                pin_owner._association()
                meter.reserve(1)
                clock.check()
                # The genuine same-admission selected reread immediately
                # before the real fixed _held_revalidation that calls
                # _load and the full directory.
                pin_eligibility._genuine_recheck(admission, clock.end)
                value = pin_owner._held_revalidation()
                meter.reserve(1)
                clock.check()
                # The same operation and pre-dispatch PinData after the
                # real held revalidation, never trusted.
                if pin_owner.op is not saved_op or value is not saved_value:
                    raise ValueError
                meter.reserve(1)
                clock.check()
                # The full retained pointer/core/row-map identity checks
                # with the retained pre-dispatch value as prior, before
                # the final genuine selected observation.
                captured = _pin_capture_identity(pin_owner, value, saved_value,
                                                 meter, clock)
                meter.reserve(1)
                clock.check()
                # The remaining pure accounting: the detached full-grants
                # verification against the immutable anchor, with the
                # trailing meter charge before the final observation.
                if pin_eligibility._bound_grants(admission, anchor_snapshot) != grants:
                    raise ValueError
                meter.reserve(1)
                clock.check()
                # The final genuine selected observation; after it only
                # the exact cutoff and the required restoration/release
                # intervene.
                pin_eligibility._genuine_recheck(admission, clock.end)
                clock.check()
            finally:
                saved_op.end = prior_end
        finally:
            pin_owner.guard.release()
        return dataset, selected, selection, meter, clock, captured, position
    except Exception:
        raise _PreparedPinRefused(admitted, intended) from None
def _current_cohort_initial_pin(
    admission,
    pin_owner,
    dataset_bytes,
    cohort,
    identifiers,
    gold_ids,
    config,
    budget,
    *,
    deadline_ms,
):
    """Guard the initial full pin read for one declared source cohort.

    The fixed private initial source-cohort pin entry: only the genuine
    current ``PolicyRequestAdmission``, the exact live ``PinOwner``
    (which alone selects the origin stores, root and capture), the
    bounded canonical dataset bytes, the exact closed ``Cohort``, the
    declared encoder identifier tuples, the declared Gold ID tuple, the
    exact ``Config``, the bounded source ``Budget`` and one 1..30000 ms
    deadline.  No caller grants, restrictions, path/stores, snapshot,
    Plan, query payload, provider, callback or clock is accepted, and at
    most one private trusted initial ``PinData`` value is returned.

    The exact owner-selected operation, root and stores are retained
    before the admission and passed to it.  The genuine source
    ``_declaration_admission`` admits the canonical dataset and exact
    selected cohort over the supplied declaration grammar and the
    verified full principal anchor with no added restriction, under one
    actual source ``_Deadline`` started once and clipped to the genuine
    admission's original end before any semantic work - checked again
    immediately before the authority snapshot work and its bounded
    completion - and the request end is never reset or extended.  Under
    one genuine nonblocking borrowed owner guard the pre-dispatch PinData
    is retained, the active owner is tied to the exact retained
    operation, root and stores before any protected work, and the saved
    operation carries the prior end.  After the pure scope admission -
    every derived per-case scope has readable members and every readable
    retained member is available for every exact selected case, over one
    captured sealed membership, the actual canonical row binding from
    the retained value and one unavailable table with the real reader
    checks, in the original declaration order, each retained scope
    admitted once as its typed canonical record and reused by the
    per-case scan - the same held value and operation are required at
    the pre-load association, then the actual metadata association and
    the genuine same-admission selected reread run immediately before
    the real fixed ``PinOwner._held_revalidation`` body that calls
    ``_load`` and the full directory.  The same held value and
    operation are verified after the actual reload, the shared bounded
    pointer/core/row-map identity checks run with the retained value as
    prior, then the remaining pure accounting - the detached
    full-grants verification against the immutable anchor - and the
    trailing meter charge complete before the final real selected
    observation, after which only the exact cutoff and the required
    restoration/release intervene.  The saved operation's end is
    restored and the guard released on all exits; no nested borrow,
    extra pin, catalog, producer, grading or report execution occurs.
    Every ordinary failure is the fixed
    content-free ``CohortRunnerError`` - an admitted initial refusal
    retains the PREFLIGHT prefix with the actual intended count and no
    attempted or refused cases - while a non-Exception BaseException
    propagates by identity.
    """
    try:
        (
            _dataset,
            _selected,
            _selection,
            _meter,
            _clock,
            captured,
            _position,
        ) = _current_cohort_prepared_pin(
            admission,
            pin_owner,
            dataset_bytes,
            cohort,
            identifiers,
            gold_ids,
            config,
            budget,
            deadline_ms=deadline_ms,
        )
        return captured
    except _PreparedPinRefused as error:
        progress = None
        if error.admitted:
            progress = FailurePrefix("PREFLIGHT", error.intended, 0, 0,
                                     0, error.intended)
        raise CohortRunnerError(progress) from None


def _current_cohort_encoder_producer(
    admission,
    pin_owner,
    dataset_bytes,
    cohort,
    identifiers,
    gold_ids,
    config,
    budget,
    encoder,
    case_id,
):
    """One genuine encoder-to-producer selected case over the complete ordered cohort.

    The fixed private current-cohort encoder producer entry: only the
    genuine current ``PolicyRequestAdmission``, the exact live
    ``PinOwner`` (which alone selects the origin stores, root and
    capture), the bounded canonical dataset bytes, the exact closed
    ``Cohort``, the declared encoder identifier tuples, the declared
    Gold ID tuple, the exact ``Config``, the bounded source ``Budget``,
    the exact open ``ResidentQueryEncoder`` and one explicitly selected
    case ID over the complete ordered cohort, with no caller deadline:
    the one operation clock is the fixed 30000 ms allowance from before
    any semantic work clipped to the genuine admission's original
    guaranteed 1..30000 ms extent, and every later call clips that same
    end.  No raw question, supplied payload or receipt, caller grants,
    path/stores, snapshot, Plan, provider, callback, clock or deadline
    is accepted, and the request end is never reset or extended.

    The exact original operation and PinData are retained before the
    shared genuine query-free declaration and guarded first cohort pin
    body, which performs its pure all-case scope before actual source
    I/O, resolves the exact selected case index from the one genuine
    declaration before the actual initial reload and carries it out as
    an internal result, and completes one actual cohort pin reload with
    the original saved end.  This entry consumes the actual owned
    ordered case and identifier material, the exact held PinData, the
    carried selected case index and the result of the guarded reload
    without a duplicate cohort declaration or a second initial reload.
    Before T1 the complete ordered case declaration and its readable
    and available scopes are already admitted by the shared body; under
    one bounded genuine short borrow the exact original operation,
    PinData, original/derived stores and root are bound to the
    already-proven capture, the exact prior operation end is saved on
    the original operation marker itself and that marker is set to the
    existing source clock end for the real association and all checks,
    the same held live core is verified and every declared encoder
    tuple is verified against the held core's exact four immutable
    query identities, the same original operation, held PinData,
    active state and stores/root are required after the real
    association, the marker's exact prior end is restored on all exits
    and the guard is released independently with the actual clock
    checked only after the release, and the borrow never spans the
    guarded resident call, adding no selected reread or physical pin.
    The genuine resident's narrow fixed
    private pure multi-tuple check then runs the exact declared tuple
    grammar and the exact observed runtime/worker/bridge identity
    checks of the same actual session under its own existing lock and
    the exact genuine admission's checks from its actual end, released
    before the real encoder invocation.  The actual encoder attempt is
    charged only immediately before the exact selected case question is
    encoded once through the existing real guarded resident operation;
    the validated exact ``QueryEmbedding`` real one-row payload, hash
    and query identifiers form the internal ``Query`` in the currently
    defined bare and prefixed field formats.  Those exact payload bytes
    and identity are used on one ``raw_hybrid_search.search_pinned_case``
    call, reported separately from the encoder as its own PRODUCER
    phase, with the same admission and owner, the original case bytes,
    the case ID, the existing k and trace configuration and the real
    O1 through O5, without supplementing O1 with a fictional pre-encode
    observation, restarting the deadline or running another producer.
    The returned real result's retained snapshot, exact canonical
    question and payload identity are verified, and the exact same
    active operation, held value and store/root identity are required
    after the real association under one brief genuine bounded
    association with equivalent custody and restoration - the prior
    operation end saved and restored on the original operation marker
    itself and the actual clock checked only after the independent
    unconditional release - before the private return.  No guard
    spans a second borrower, the
    legitimate per-transport child caps can shorten but never extend
    the request, and the internal HybridResult status fields are
    preserved.  The entry returns at most the internal owned case
    evidence - the selected case ID, the internal Query and the
    HybridResult - which is never a full stage, grade, report or
    delivery attestation.  Every ordinary failure is the fixed
    content-free ``CohortRunnerError`` with no scoped result exposed,
    while a non-Exception BaseException propagates by identity.
    """
    import hashlib
    import json

    from . import private_policy_pin_eligibility as pin_eligibility
    from . import private_policy_request as policy_request
    from . import query_embedding as embedding_module
    from . import raw_hybrid_search
    from . import raw_snapshot_pin
    from . import raw_snapshot_selection as snapshot_selection

    admitted = False
    intended = 0
    phase = "PREFLIGHT"
    attempted = 0
    try:
        if (
            type(admission) is not policy_request.PolicyRequestAdmission
            or type(pin_owner) is not raw_snapshot_pin.PinOwner
            or type(dataset_bytes) is not bytes
            or not 1 <= len(dataset_bytes) <= 1048576
            or not _closed(cohort, Cohort)
            or not _closed(config, Config)
            or not _closed(budget, Budget)
            or type(cohort.case_ids) is not tuple
            or not 1 <= len(cohort.case_ids) <= 256
            or type(identifiers) is not tuple
            or len(identifiers) != len(cohort.case_ids)
            or type(gold_ids) is not tuple
            or type(encoder) is not embedding_module.ResidentQueryEncoder
            or type(case_id) is not str
            or not 1 <= len(case_id) <= 128
            or pin_owner.op is None
            or pin_owner.value is None
            or pin_owner.originals is None
            or pin_owner.derived is None
        ):
            raise ValueError
        # The exact original operation and PinData retained before any
        # shared work; the live core and the immutable query tuple are
        # verified against them after the guarded reload.
        original_op = pin_owner.op
        held_value = pin_owner.value
        saved_originals = pin_owner.originals
        saved_derived = pin_owner.derived
        saved_root = pin_owner.op.path
        # The shared genuine query-free declaration and guarded first
        # cohort pin body: its pure all-case scope precedes actual
        # source I/O, one actual cohort pin reload and the original
        # saved end, and the one operation clock started before any
        # semantic work; the actual owned ordered case and identifier
        # material, the exact held PinData and the result of the
        # guarded reload are consumed without a duplicate cohort
        # declaration or a second initial reload; the fixed 30000 ms
        # allowance from before any semantic work is clipped to the
        # genuine admission's original extent, and the exact selected
        # case index is resolved before the actual initial reload.
        (
            _dataset,
            selected,
            _selection,
            meter,
            clock,
            captured,
            position,
        ) = _current_cohort_prepared_pin(
            admission,
            pin_owner,
            dataset_bytes,
            cohort,
            identifiers,
            gold_ids,
            config,
            budget,
            deadline_ms=30000,
            case_id=case_id,
        )
        admitted = True
        intended = len(selected)
        meter.reserve(1)
        clock.check()
        selected_case = selected[position][0]
        # Under one bounded genuine short borrow the exact saved
        # operation, PinData, original/derived stores and root are
        # bound to the already-proven capture; the exact prior
        # operation end is saved on the original operation marker
        # itself, that marker is set to the existing source clock end
        # for the real association and all checks, restored on all
        # exits and the guard released independently; the same
        # original operation, held PinData, active state and
        # stores/root are required after the real association, and the
        # actual clock is checked only after the independent
        # unconditional release; no selected reread or physical pin is
        # added and the borrow never spans the encoder or producer.
        if (pin_owner.value is not captured or pin_owner.value is not held_value):
            raise ValueError
        meter.reserve(1)
        clock.check()
        pin_eligibility._borrowed_owner(pin_owner)
        try:
            if (
                pin_owner.state != "ACTIVE"
                or type(pin_owner.op) is not snapshot_selection._Operation
                or pin_owner.op is not original_op
                or type(pin_owner.value) is not raw_snapshot_pin.PinData
                or pin_owner.value is not captured
                or pin_owner.originals is not saved_originals
                or pin_owner.derived is not saved_derived
                or pin_owner.op.path != saved_root
            ):
                raise ValueError
            prior_end = original_op.end
            original_op.end = clock.end
            try:
                pin_owner._association()
                if (
                    pin_owner.state != "ACTIVE"
                    or pin_owner.op is not original_op
                    or pin_owner.value is not captured
                    or pin_owner.originals is not saved_originals
                    or pin_owner.derived is not saved_derived
                    or pin_owner.op.path != saved_root
                ):
                    raise ValueError
                meter.reserve(1)
                clock.check()
                core = captured.data.core_bytes
                if type(core) is not bytes or len(core) > 262144:
                    raise ValueError
                meter.reserve(len(core) + 66, 192)
                clock.check()
                if hashlib.sha256(core).hexdigest() != captured.pointer.core_sha256:
                    raise ValueError
                embedding = json.loads(core.decode("ascii"))["embedding"]
                core_tuple = (
                    embedding["space_id"],
                    embedding["definition_fingerprint"],
                    embedding["query_policy_fingerprint"],
                    embedding["query_execution_fingerprint"],
                )
                if any(type(value) is not str for value in core_tuple):
                    raise ValueError
                meter.reserve(1)
                clock.check()
                # Every declared encoder tuple against the held core's
                # exact four immutable query identities: the
                # distinction between declaration grammar, scope, real
                # held core and runtime identity is preserved, with no
                # fallback.
                for declared in identifiers:
                    meter.reserve(1)
                    if type(declared) is not tuple or len(declared) != 4:
                        raise ValueError
                    for left, right in zip(declared, core_tuple, strict=True):
                        meter.reserve(1)
                        if meter.compare_strings(left, right) != 0:
                            raise ValueError
                    meter.reserve(1)
                    clock.check()
            finally:
                original_op.end = prior_end
        finally:
            pin_owner.guard.release()
        meter.reserve(1)
        clock.check()
        # The genuine resident's existing expected identity checks over
        # the same declared tuples: the narrow fixed private resident
        # pure multi-tuple check under its own existing ownership lock,
        # the same actual session, exact observed runtime/worker/bridge
        # data and the exact genuine admission's checks from its actual
        # end, released before the real encoder invocation; a tuple or
        # identity refusal here retains the PREFLIGHT phase.
        encoder._check_declared_identities(tuple(identifiers), admission)
        meter.reserve(1)
        clock.check()
        # The actual encoder attempt is charged only immediately before
        # the exact selected case question is encoded once through the
        # existing real guarded resident operation; each final per-
        # encode runtime validation and the genuine T1 and T2 stay
        # inside it.
        phase = "T1"
        attempted = 1
        embedding_result = encoder._encode_expected_identity_admitted(
            selected_case.question, identifiers[position], admission)
        if (
            type(embedding_result) is not embedding_module.QueryEmbedding
            or type(embedding_result.payload) is not bytes
            or len(embedding_result.payload) != 4096
            or type(embedding_result.payload_sha256) is not str
        ):
            raise ValueError
        meter.reserve(len(embedding_result.payload) + 132, 256)
        clock.check()
        if (hashlib.sha256(embedding_result.payload).hexdigest()
                != embedding_result.payload_sha256):
            raise ValueError
        # The real one-row payload, hash and query identifiers bound to
        # the declared tuple in the currently defined bare and prefixed
        # field formats, with no fallback.
        declared = identifiers[position]
        pairs = (
            (embedding_result.space_id, declared[0]),
            (embedding_result.definition_fingerprint, declared[1]),
            (embedding_result.query_policy_id, declared[2]),
            (embedding_result.execution_fingerprint, "sha256:" + declared[3]),
        )
        for left, right in pairs:
            meter.reserve(1)
            if meter.compare_strings(left, right) != 0:
                raise ValueError
        meter.reserve(1)
        clock.check()
        # The internal Query formed from the actual returned bytes and
        # IDs, preserving the currently defined bare and prefixed field
        # formats.
        query = Query(
            case_id=selected_case.case_id,
            payload=embedding_result.payload,
            space_id=embedding_result.space_id,
            definition_fingerprint=embedding_result.definition_fingerprint,
            policy_id=embedding_result.query_policy_id,
            execution_fingerprint=embedding_result.execution_fingerprint[7:],
        )
        meter.reserve(1)
        clock.check()
        # One producer dispatch: the exact payload bytes and identity on
        # one search_pinned_case call with the same admission and owner,
        # the original case bytes, the case ID, the existing k and trace
        # configuration and the real O1 through O5; no fictional
        # pre-encode observation supplements O1, no deadline restart, no
        # second producer and the reported PRODUCER phase separate from
        # the encoder's own T1 and T2.
        phase = "PRODUCER"
        result = raw_hybrid_search.search_pinned_case(
            admission,
            pin_owner,
            dataset_bytes,
            case_id,
            query.payload,
            query_space_id=query.space_id,
            query_definition_fingerprint=query.definition_fingerprint,
            query_policy_id=query.policy_id,
            query_execution_fingerprint=query.execution_fingerprint,
            dense_k=60,
            lexical_k=60,
            partition_cap=60,
            k=60,
            deadline_ms=30000,
            trace=True,
        )
        meter.reserve(1)
        clock.check()
        if (
            type(result) is not raw_hybrid_search.HybridResult
            or result.query_origin != "SUPPLIED_UNVERIFIED"
            or result.qualification != "NOT_QUALIFIED"
        ):
            raise ValueError
        meter.reserve(1)
        clock.check()
        # The returned real result's retained snapshot, exact canonical
        # question and payload identity, verified before the private
        # return.
        if (
            result.snapshot_id != held_value.data.snapshot_id
            or result.query_text_sha256 != hashlib.sha256(
                selected_case.question.encode()).hexdigest()
            or result.query_payload_sha256 != hashlib.sha256(
                query.payload).hexdigest()
        ):
            raise ValueError
        # The exact same active operation, held value and store/root
        # identity, required under one brief genuine bounded
        # association with equivalent custody and restoration: the
        # exact prior operation end is saved on the original operation
        # marker itself, set to the existing source clock end for the
        # real association, restored on all exits and the guard is
        # released independently; the same original operation, held
        # PinData, active state and stores/root are required after the
        # real association, and the actual clock is checked only after
        # the independent unconditional release; no selected reread or
        # physical pin and the guard never spans the encoder or
        # producer.
        pin_eligibility._borrowed_owner(pin_owner)
        try:
            if (
                pin_owner.state != "ACTIVE"
                or pin_owner.op is not original_op
                or pin_owner.value is not captured
                or pin_owner.originals is not saved_originals
                or pin_owner.derived is not saved_derived
                or pin_owner.op.path != saved_root
            ):
                raise ValueError
            prior_end = original_op.end
            original_op.end = clock.end
            try:
                pin_owner._association()
                if (
                    pin_owner.state != "ACTIVE"
                    or pin_owner.op is not original_op
                    or pin_owner.value is not captured
                    or pin_owner.originals is not saved_originals
                    or pin_owner.derived is not saved_derived
                    or pin_owner.op.path != saved_root
                ):
                    raise ValueError
            finally:
                original_op.end = prior_end
        finally:
            pin_owner.guard.release()
        meter.reserve(1)
        clock.check()
        return selected_case.case_id, query, result
    except _PreparedPinRefused as error:
        admitted = error.admitted
        intended = error.intended
    except Exception:
        pass
    progress = None
    if admitted:
        refused = 1 if phase in ("T1", "PRODUCER") else 0
        progress = FailurePrefix(phase, intended, attempted, 0, refused,
                                 intended - attempted)
    raise CohortRunnerError(progress) from None
