"""Private source-bound diagnostic over owned raw hybrid rankings."""

from dataclasses import dataclass
import hashlib
import json
import math
import re
import struct
import time

from . import derived_store, provenance_records
from . import raw_hybrid_search as hybrid, raw_lexical_search as lexical
from . import raw_dense_search as dense, raw_rank_fusion as fusion
from . import source_bound_text_support as support, declared_span_support as coverage
from . import raw_snapshot_files as files, raw_snapshot_manifest as manifest
from . import raw_snapshot_pin as pin, raw_snapshot_publication as publication
from . import raw_snapshot_selection as selection, text_evaluation_dataset as datasets
from .source_admission import OriginalStore


class StageSupportError(ValueError):
    """Content-free refusal of the complete diagnostic."""


@dataclass(frozen=True, slots=True, repr=False)
class Variant:
    name: str
    ranking_hash: str
    trace_id: str | None
    eligible: int
    selected: int
    returned: int
    matching: int | None
    partition_cap_applied: bool
    global_cap_applied: bool
    support: object


@dataclass(frozen=True, slots=True, repr=False)
class StageSupport:
    invocation_id: str
    dataset_id: str
    split_id: str
    case_id: str
    dataset_sha256: str
    question_sha256: str
    query_payload_sha256: str
    original_authority_sha256: str
    effective_authority_sha256: str
    case_filter_id: str
    pointer_sha256: str
    generation: int
    snapshot_id: str
    catalog_id: str
    hybrid_query_id: str
    variants: tuple
    fusion_dense_input_rows: int
    fusion_lexical_input_rows: int
    fusion_overlap_candidates: int
    filter_policy: str = "case-scope-allowlist-intersection-v1"
    relevance_metrics: str = "UNSPECIFIED_RELEVANCE_UNIT_MAPPING"
    query_origin: str = "SUPPLIED_UNVERIFIED"
    gold_eligibility: str = "NOT_CHECKED"
    execution_status: str = "NOT_ATTESTED"
    temporal_consistency: str = "SEQUENTIAL_OBSERVATIONS_NOT_ATOMIC"
    qualification: str = "NOT_QUALIFIED"


def _check(condition):
    if not condition:
        raise ValueError


def _digest(value):
    return hashlib.sha256(value).hexdigest()


def _identity(kind, value):
    encoded = json.dumps(
        value, sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False
    ).encode("ascii")
    return "sha256:" + _digest(kind.encode("ascii") + b"\n" + encoded)


def _hex(value, prefix=""):
    return (type(value) is str and len(value) == len(prefix) + 64
            and re.fullmatch(re.escape(prefix) + r"[0-9a-f]{64}", value))


def evaluate_case(
    originals,
    derived,
    store_root,
    pin_owner,
    dataset_bytes,
    case_id,
    gold_bundle_ids,
    query_payload,
    *,
    query_space_id,
    query_definition_fingerprint,
    query_policy_id,
    query_execution_fingerprint,
    grants,
    restrictions=None,
    deadline_ms=120000,
):
    """Borrow resources for one private sequential diagnostic, under one deadline."""
    try:
        return _evaluate(
            originals,
            derived,
            store_root,
            pin_owner,
            dataset_bytes,
            case_id,
            gold_bundle_ids,
            query_payload,
            query_space_id,
            query_definition_fingerprint,
            query_policy_id,
            query_execution_fingerprint,
            grants,
            restrictions,
            deadline_ms,
        )
    except Exception:
        raise StageSupportError("raw text stage support refused") from None


def _evaluate(
    originals,
    derived,
    root,
    owner,
    dataset_bytes,
    case_id,
    bundle_ids,
    payload,
    space,
    definition,
    policy,
    execution,
    grants,
    restrictions,
    deadline_ms,
):
    _check(type(deadline_ms) is int and 1 <= deadline_ms <= 120000)
    end = time.monotonic() + deadline_ms / 1000

    def remaining(cap=120000):
        ms = min(cap, math.floor((end - time.monotonic()) * 1000))
        _check(ms > 0)
        return ms

    _check(type(originals) is OriginalStore and type(derived) is derived_store.Store)
    _check(type(root) is str and len(root) <= 4096)
    publication._path_check(root)
    _check(len(root[1:].split("/")) <= 64)
    _check(
        type(owner) is pin.PinOwner
        and owner.state == "ACTIVE"
        and owner.op.path == root
        and owner.originals is originals
        and owner.derived is derived
    )
    _check(type(dataset_bytes) is bytes and len(dataset_bytes) <= 16777216)
    _check(
        type(case_id) is str
        and 1 <= len(case_id) <= 128
        and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}", case_id)
    )
    _check(type(bundle_ids) is tuple and len(bundle_ids) <= 128)
    previous = ""
    for ident in bundle_ids:
        _check(_hex(ident) and ident > previous)
        previous = ident
    _check(type(payload) is bytes and len(payload) == 4096)
    for value, prefix in ((space, ""), (definition, "sha256:"), (policy, ""), (execution, "")):
        _check(_hex(value, prefix))
    vector = struct.unpack("<1024f", payload)
    _check(
        all(math.isfinite(v) for v in vector)
        and abs(math.sqrt(sum(v * v for v in vector)) - 1) <= 1e-4
    )
    del vector
    grants, restrictions = lexical._authority(grants, restrictions)
    _check(grants is not None)
    original_hash = lexical._authority_hash(grants, restrictions)
    remaining()
    dataset = datasets.admit(dataset_bytes, deadline_ms=remaining(5000))
    remaining()
    _check(type(dataset) is datasets.Dataset)
    matches = [c for c in dataset.cases if c.case_id == case_id]
    _check(len(matches) == 1 and type(matches[0]) is datasets.Case)
    case = matches[0]
    _check(type(case.scope) is datasets.DeclaredScope)
    fields = {
        name: tuple(sorted(set(getattr(grants, name)) & set(getattr(case.scope, name))))
        for name in ("corpora", "versions", "labels")
    }
    effective = provenance_records.Grants.model_validate(dict(schema_version=1, **fields))
    effective_hash = lexical._authority_hash(effective, restrictions)
    filter_id = _identity("case-scope-allowlist-intersection-v1", fields)
    remaining()
    captured = owner.check(deadline_ms=remaining())
    remaining()
    _check(
        type(captured) is pin.PinData
        and type(captured.pointer) is selection.Pointer
        and type(captured.data) is files.BoundSnapshotData
    )
    pointer, data = captured.pointer, captured.data
    parsed = manifest.parse(data.core_bytes)
    remaining()
    _check(
        parsed.snapshot_id == data.snapshot_id == pointer.snapshot_id
        and _digest(data.core_bytes) == pointer.core_sha256
        and selection.parse_pointer(pointer.pointer_bytes) == pointer
    )

    def check_pin():
        remaining()
        _check(
            owner.state == "ACTIVE"
            and owner.op.path == root
            and owner.originals is originals
            and owner.derived is derived
        )
        _check(owner.check(deadline_ms=remaining()) == captured)
        remaining()

    return _compose(
        originals,
        derived,
        root,
        dataset_bytes,
        case_id,
        bundle_ids,
        payload,
        space,
        definition,
        policy,
        execution,
        restrictions,
        dataset,
        case,
        effective,
        original_hash,
        effective_hash,
        filter_id,
        pointer,
        json.loads(data.core_bytes)["analyzer"]["fingerprint"],
        check_pin,
        remaining,
    )


def _rank(hits, cls, remaining):
    _check(type(hits) is tuple and len(hits) <= 60)
    rows = []
    ordinals, chunks = set(), set()
    for rank, hit in enumerate(hits, 1):
        remaining()
        _check(
            type(hit) is cls
            and type(hit.rank) is int
            and hit.rank == rank
            and type(hit.ordinal) is int
            and 0 <= hit.ordinal < 4096
        )
        _check(
            all(
                _hex(getattr(hit, n), "sha256:")
                for n in ("partition_id", "chunk_id", "revision_id")
            )
            and _hex(hit.representation_id)
            and type(hit.score) is float
            and math.isfinite(hit.score)
        )
        _check(hit.ordinal not in ordinals and hit.chunk_id not in chunks)
        ordinals.add(hit.ordinal)
        chunks.add(hit.chunk_id)
        rows.append(
            (hit.ordinal, hit.partition_id, hit.chunk_id, hit.revision_id, hit.representation_id)
        )
    return tuple(rows)


def _support_check(
    item, dataset, case, dataset_hash, snapshot, catalog, authority, ranking_count, atoms, remaining
):
    _check(type(item) is support.TextSupport)
    for name in ("case_requirement_count", "ranking_count", "case_gold_atom_occurrences",
                 "case_distinct_gold_atoms", "global_gold_atom_occurrences",
                 "global_distinct_gold_atoms"):
        _check(type(getattr(item, name)) is int and 0 <= getattr(item, name) <= 65536)
    _check(
        (
            item.dataset_id,
            item.split_id,
            item.case_id,
            item.dataset_sha256,
            item.snapshot_id,
            item.catalog_id,
            item.authority_sha256,
            item.case_answerability,
            item.case_requirement_count,
            item.ranking_count,
        )
        == (
            dataset.dataset_id,
            dataset.split_id,
            case.case_id,
            dataset_hash,
            snapshot,
            catalog,
            authority,
            case.answerability,
            len(case.requirements),
            ranking_count,
        )
    )
    _check(
        (
            item.case_gold_atom_occurrences,
            item.case_distinct_gold_atoms,
            item.global_gold_atom_occurrences,
            item.global_distinct_gold_atoms,
        )
        == atoms
    )
    for name in ("evaluation_id", "gold_binding_id", "ranking_binding_id", "geometry_fingerprint"):
        _check(_hex(getattr(item, name), "sha256:"))
    _check(type(item.source_fragment_count) is int and 0 <= item.source_fragment_count <= 65536)
    _check(
        (item.global_gold_source_status, item.case_gold_source_status, item.ranking_source_status)
        == (
            "ORIGINALS_REVALIDATED_AT_BIND_TIME" if atoms[3] else "NO_GOLD_SOURCE_VALIDATED",
            "ORIGINAL_GOLD_SPANS_REVALIDATED_AT_CALL_TIME"
            if atoms[1]
            else "NO_CASE_GOLD_REQUIREMENTS",
            "ORIGINALS_REVALIDATED_AT_BIND_TIME"
            if ranking_count
            else "NO_SELECTED_SOURCE_VALIDATED",
        )
    )
    _check(
        (
            item.input_origin,
            item.source_binding,
            item.gold_eligibility,
            item.authorization_status,
            item.execution_status,
            item.temporal_consistency,
            item.qualification,
            item.formula_version,
        )
        == (
            "SUPPLIED_RANKING_UNVERIFIED",
            "OWNED_TEXT_BINDING_CALLS_ONLY",
            "NOT_CHECKED",
            "SUPPLIED_RANK_SCOPE_ONLY_GOLD_RIGHTS_UNVERIFIED",
            "NOT_ATTESTED",
            "SEQUENTIAL_OBSERVATIONS_NOT_ATOMIC",
            "NOT_QUALIFIED",
            "source-bound-text-support-v1",
        )
    )
    _check(type(item.at_k) is tuple and len(item.at_k) == 2)
    for record, k in zip(item.at_k, (20, 60)):
        remaining()
        _check(
            type(record) is coverage.CoverageAtK
            and type(record.k) is int
            and record.k == k
            and type(record.returned_count) is int
            and record.returned_count == min(k, ranking_count)
            and type(record.requirements) is tuple
            and len(record.requirements) == len(case.requirements)
            and type(record.covered_requirement_ids) is tuple
        )
        ids = []
        for row, requirement in zip(record.requirements, case.requirements):
            _check(
                type(row) is coverage.RequirementCoverage
                and row.requirement_id == requirement.requirement_id
                and type(row.alternative_covered) is tuple
                and len(row.alternative_covered) == len(requirement.alternatives)
                and all(type(v) is bool for v in row.alternative_covered)
                and type(row.covered) is bool
                and row.covered == any(row.alternative_covered)
            )
            if row.covered:
                ids.append(row.requirement_id)
        count = len(case.requirements)
        _check(record.requirement_fraction is None if not count else
               (type(record.requirement_fraction) is float and
                math.isfinite(record.requirement_fraction) and
                0.0 <= record.requirement_fraction <= 1.0))
        _check(
            record.covered_requirement_ids == tuple(ids)
            and record.requirement_fraction == (len(ids) / count if count else None)
            and record.complete_requirements is (len(ids) == count if count else None)
            and record.undefined_reason == (None if count else "NO_GOLD_REQUIREMENTS")
        )


def _compose(
    originals,
    derived,
    root,
    dataset_bytes,
    case_id,
    bundle_ids,
    payload,
    space,
    definition,
    policy,
    execution,
    restrictions,
    dataset,
    case,
    effective,
    original_hash,
    effective_hash,
    filter_id,
    pointer,
    analyzer,
    check_pin,
    remaining,
):
    question_hash = _digest(case.question.encode("utf-8"))
    payload_hash = _digest(payload)
    dataset_hash = _digest(dataset_bytes)
    check_pin()
    result = hybrid.search(
        originals,
        derived,
        root,
        pointer.snapshot_id,
        case.question,
        payload,
        query_space_id=space,
        query_definition_fingerprint=definition,
        query_policy_id=policy,
        query_execution_fingerprint=execution,
        grants=effective,
        restrictions=restrictions,
        dense_k=60,
        lexical_k=60,
        partition_cap=60,
        k=60,
        trace=True,
        deadline_ms=remaining(),
    )
    remaining()
    check_pin()
    _check(
        type(result) is hybrid.HybridResult
        and _hex(result.catalog_id, "sha256:")
        and (
            result.snapshot_id,
            result.query_text_sha256,
            result.query_payload_sha256,
            result.authority_sha256,
            result.query_origin,
            result.qualification,
        )
        == (
            pointer.snapshot_id,
            question_hash,
            payload_hash,
            effective_hash,
            "SUPPLIED_UNVERIFIED",
            "NOT_QUALIFIED",
        )
    )
    expected_query = hybrid._sha(
        hybrid._wire(
            dict(
                kind="raw-hybrid-query/v1",
                snapshot_id=pointer.snapshot_id,
                catalog_id=result.catalog_id,
                query_text_sha256=question_hash,
                query_payload_sha256=payload_hash,
                query_space_id=space,
                query_definition_fingerprint=definition,
                query_policy_id=policy,
                query_execution_fingerprint=execution,
                authority_sha256=effective_hash,
                dense_k=60,
                lexical_k=60,
                partition_cap=60,
                k=60,
            )
        )
    )
    _check(
        result.query_id == expected_query
        and type(result.dense) is dense.DenseResult
        and type(result.lexical) is lexical.LexicalResult
        and type(result.fusion) is fusion.FusionResult
    )
    dr, lr, fr = result.dense, result.lexical, result.fusion
    _check(
        (dr.snapshot_id, dr.catalog_id, dr.query_payload_sha256, dr.query_origin, dr.qualification)
        == (
            pointer.snapshot_id,
            result.catalog_id,
            payload_hash,
            "SUPPLIED_UNVERIFIED",
            "NOT_QUALIFIED",
        )
    )
    _check(
        (
            lr.snapshot_id,
            lr.catalog_id,
            lr.query_text_sha256,
            lr.analyzer_fingerprint,
            lr.backend,
            lr.method,
        )
        == (
            pointer.snapshot_id,
            result.catalog_id,
            question_hash,
            analyzer,
            "bm25s-lucene/0.2.14/2.5.4/1.18.1",
            "lucene",
        )
    )
    common = dict(
        snapshot_id=pointer.snapshot_id,
        catalog_id=result.catalog_id,
        authority_sha256=effective_hash,
    )
    hybrid._trace_link(
        dr,
        dense,
        dict(
            **common,
            query_payload_sha256=payload_hash,
            query_space_id=space,
            query_definition_fingerprint=definition,
            query_policy_id=policy,
            query_execution_fingerprint=execution,
        ),
        60,
        60,
        remaining,
    )
    hybrid._trace_link(
        lr,
        lexical,
        dict(
            **common,
            query_text_sha256=question_hash,
            analyzer_fingerprint=analyzer,
            backend="bm25s-lucene/0.2.14/2.5.4/1.18.1",
            method="lucene",
        ),
        60,
        60,
        remaining,
    )
    _check(
        (
            fr.snapshot_id,
            fr.catalog_id,
            fr.query_id,
            fr.ranking_origin,
            fr.qualification,
            fr.dense_status,
            fr.lexical_status,
            fr.degraded,
        )
        == (
            pointer.snapshot_id,
            result.catalog_id,
            expected_query,
            "SUPPLIED_UNVERIFIED",
            "NOT_QUALIFIED",
            "COMPLETE",
            "COMPLETE",
            False,
        )
        and type(fr.degraded) is bool
    )
    rankings = (
        _rank(dr.hits, dense.Hit, remaining),
        _rank(lr.hits, lexical.Hit, remaining),
        _rank(fr.hits, fusion.Hit, remaining),
    )
    dense_rows = {row[0]: (i, row) for i, row in enumerate(rankings[0], 1)}
    lexical_rows = {row[0]: (i, row) for i, row in enumerate(rankings[1], 1)}
    for hit, row in zip(fr.hits, rankings[2]):
        a, b = dense_rows.get(hit.ordinal), lexical_rows.get(hit.ordinal)
        _check(
            (a is not None or b is not None)
            and (a is None or a[1] == row)
            and (b is None or b[1] == row)
            and (hit.dense_rank is None if a is None else type(hit.dense_rank) is int)
            and (hit.lexical_rank is None if b is None else type(hit.lexical_rank) is int)
            and hit.dense_rank == (a[0] if a else None)
            and hit.lexical_rank == (b[0] if b else None)
        )
    union = set(dense_rows) | set(lexical_rows)
    for value in (fr.dense_input_rows, fr.lexical_input_rows, fr.unique_candidates,
                  fr.overlap_candidates, fr.returned):
        _check(type(value) is int and 0 <= value <= 120)
    _check(type(fr.global_cap_applied) is bool)
    expected_rows = []
    for ordinal in union:
        a, b = dense_rows.get(ordinal), lexical_rows.get(ordinal)
        row = (a or b)[1]
        _check(a is None or b is None or a[1] == b[1])
        score = sum(fusion._contribution(v[0]) for v in (a, b) if v is not None)
        expected_rows.append((-score, row[2], row[3], row[4], row))
    expected_rows.sort()
    _check(rankings[2] == tuple(item[-1] for item in expected_rows[:60]))
    _check(
        (
            fr.dense_input_rows,
            fr.lexical_input_rows,
            fr.unique_candidates,
            fr.overlap_candidates,
            fr.returned,
            fr.global_cap_applied,
        )
        == (
            len(rankings[0]),
            len(rankings[1]),
            len(union),
            len(set(dense_rows) & set(lexical_rows)),
            len(rankings[2]),
            len(union) > 60,
        )
    )
    all_atoms, chosen_atoms = set(), set()
    all_count = chosen_count = 0
    for c in dataset.cases:
        for req in c.requirements:
            for alt in req.alternatives:
                for span in alt:
                    remaining()
                    atom = support._atom(span)
                    all_atoms.add(atom)
                    all_count += 1
                    if c is case:
                        chosen_atoms.add(atom)
                        chosen_count += 1
    atoms = (chosen_count, len(chosen_atoms), all_count, len(all_atoms))
    variants = []
    for name, ranking, trace, counts in zip(
        ("dense", "lexical", "fusion"),
        rankings,
        (dr.trace.trace_id, lr.trace.trace_id, None),
        (
            (
                dr.eligible,
                dr.selected,
                dr.returned,
                None,
                dr.partition_cap_applied,
                dr.global_cap_applied,
            ),
            (
                lr.eligible,
                lr.selected,
                lr.returned,
                lr.matching,
                lr.partition_cap_applied,
                lr.global_cap_applied,
            ),
            (fr.unique_candidates, fr.unique_candidates, fr.returned, None, False,
             fr.global_cap_applied),
        ),
    ):
        rank_hash = _identity("raw-text-stage-rank-v1", ranking)
        chunk_ids = tuple(row[2] for row in ranking)
        check_pin()
        item = support.score_case(
            originals,
            derived,
            root,
            pointer.snapshot_id,
            result.catalog_id,
            dataset_bytes,
            case_id,
            bundle_ids,
            chunk_ids,
            grants=effective,
            restrictions=restrictions,
            cutoffs=(20, 60),
            deadline_ms=remaining(30000),
        )
        remaining()
        check_pin()
        _support_check(
            item,
            dataset,
            case,
            dataset_hash,
            pointer.snapshot_id,
            result.catalog_id,
            effective_hash,
            len(ranking),
            atoms,
            remaining,
        )
        if variants:
            _check(all(item is not v.support for v in variants))
            _check(item.gold_binding_id == variants[0].support.gold_binding_id)
        variants.append(Variant(name, rank_hash, trace, *counts, item))
    pointer_hash = _digest(pointer.pointer_bytes)
    identity = dict(
        dataset_id=dataset.dataset_id,
        split_id=dataset.split_id,
        case_id=case_id,
        dataset_sha256=dataset_hash,
        question_sha256=question_hash,
        query_payload_sha256=payload_hash,
        query_space_id=space,
        query_definition_fingerprint=definition,
        query_policy_id=policy,
        query_execution_fingerprint=execution,
        original_authority_sha256=original_hash,
        effective_authority_sha256=effective_hash,
        case_filter_id=filter_id,
        pointer_sha256=pointer_hash,
        generation=pointer.generation,
        snapshot_id=pointer.snapshot_id,
        catalog_id=result.catalog_id,
        hybrid_query_id=expected_query,
        caps=[60, 60, 60, 60],
        cutoffs=[20, 60],
        variants=[(v.name, v.ranking_hash, v.trace_id, v.support.evaluation_id) for v in variants],
    )
    output = StageSupport(
        _identity("raw-text-stage-support-invocation-v1", identity),
        dataset.dataset_id,
        dataset.split_id,
        case_id,
        dataset_hash,
        question_hash,
        payload_hash,
        original_hash,
        effective_hash,
        filter_id,
        pointer_hash,
        pointer.generation,
        pointer.snapshot_id,
        result.catalog_id,
        expected_query,
        tuple(variants),
        fr.dense_input_rows,
        fr.lexical_input_rows,
        fr.overlap_candidates,
    )
    check_pin()
    remaining()
    return output
