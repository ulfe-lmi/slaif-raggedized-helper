"""Private operator-only source-bound declared geometry diagnostic."""

from dataclasses import asdict, dataclass, field
import hashlib
import json
import re
import time
import unicodedata

from . import declared_span_support, source_bound_ranking, text_evaluation_dataset
from . import text_evaluation_gold_binding


class TextSupportError(ValueError):
    """Content-free refusal."""


@dataclass(frozen=True, slots=True, repr=False)
class TextSupport:
    evaluation_id: str
    dataset_id: str
    split_id: str
    case_id: str
    dataset_sha256: str
    gold_binding_id: str
    ranking_binding_id: str
    snapshot_id: str
    catalog_id: str
    authority_sha256: str
    case_answerability: str
    case_requirement_count: int
    case_gold_atom_occurrences: int
    case_distinct_gold_atoms: int
    global_gold_atom_occurrences: int
    global_distinct_gold_atoms: int
    ranking_count: int
    source_fragment_count: int
    global_gold_source_status: str
    case_gold_source_status: str
    ranking_source_status: str
    geometry_fingerprint: str
    at_k: tuple
    input_origin: str = field(default="SUPPLIED_RANKING_UNVERIFIED", init=False)
    source_binding: str = field(default="OWNED_TEXT_BINDING_CALLS_ONLY", init=False)
    gold_eligibility: str = field(default="NOT_CHECKED", init=False)
    authorization_status: str = field(
        default="SUPPLIED_RANK_SCOPE_ONLY_GOLD_RIGHTS_UNVERIFIED", init=False
    )
    execution_status: str = field(default="NOT_ATTESTED", init=False)
    temporal_consistency: str = field(default="SEQUENTIAL_OBSERVATIONS_NOT_ATOMIC", init=False)
    qualification: str = field(default="NOT_QUALIFIED", init=False)
    formula_version: str = field(default="source-bound-text-support-v1", init=False)


def _atom(value):
    return (
        value.revision_id,
        value.extraction_id,
        value.block_id,
        value.start,
        value.end,
        value.text_sha256,
    )


def _score(
    originals,
    derived,
    store_root,
    snapshot_id,
    expected_catalog_id,
    dataset_bytes,
    case_id,
    gold_bundle_ids,
    chunk_ids,
    grants,
    restrictions,
    cutoffs,
    deadline_ms,
    start,
):
    if type(deadline_ms) is not int or not 1 <= deadline_ms <= 30000:
        raise ValueError
    end = start + deadline_ms / 1000

    def check():
        if time.monotonic() >= end:
            raise ValueError

    def remaining(cap):
        check()
        value = min(cap, int((end - time.monotonic()) * 1000))
        if value < 1:
            raise ValueError
        return value

    check()
    if (
        type(dataset_bytes) is not bytes
        or len(dataset_bytes) > 16777216
        or type(store_root) is not str
        or not 1 <= len(store_root) <= 4096
        or type(case_id) is not str
        or not 1 <= len(case_id) <= 128
        or type(gold_bundle_ids) is not tuple
        or len(gold_bundle_ids) > 128
        or type(chunk_ids) is not tuple
        or len(chunk_ids) > 4096
        or type(cutoffs) is not tuple
        or not 1 <= len(cutoffs) <= 16
    ):
        raise ValueError
    # Bound every scalar before encoding or constructing lookup containers.
    for ident in (snapshot_id, expected_catalog_id):
        check()
        if type(ident) is not str or len(ident) != 71:
            raise ValueError
    for ident in gold_bundle_ids:
        check()
        if type(ident) is not str or len(ident) != 64:
            raise ValueError
    for ident in chunk_ids:
        check()
        if type(ident) is not str or len(ident) != 71:
            raise ValueError
    for k in cutoffs:
        check()
        if type(k) is not int or not 1 <= k <= 4096:
            raise ValueError
    if len(store_root.encode("utf-8")) > 4096:
        raise ValueError
    check()
    if (
        not store_root.startswith("/")
        or store_root == "/"
        or any(unicodedata.category(char) == "Cc" for char in store_root)
        or any(part in ("", ".", "..") for part in store_root[1:].split("/"))
    ):
        raise ValueError
    check()
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}", case_id):
        raise ValueError
    for ident in (snapshot_id, expected_catalog_id):
        check()
        if (
            type(ident) is not str
            or len(ident) != 71
            or not re.fullmatch(r"sha256:[0-9a-f]{64}", ident)
        ):
            raise ValueError
    previous = ""
    for ident in gold_bundle_ids:
        check()
        if (
            type(ident) is not str
            or len(ident) != 64
            or not re.fullmatch(r"[0-9a-f]{64}", ident)
            or ident <= previous
        ):
            raise ValueError
        previous = ident
    seen = set()
    for ident in chunk_ids:
        check()
        if (
            type(ident) is not str
            or len(ident) != 71
            or not re.fullmatch(r"sha256:[0-9a-f]{64}", ident)
            or ident in seen
        ):
            raise ValueError
        seen.add(ident)
    previous_k = 0
    for k in cutoffs:
        check()
        if type(k) is not int or not previous_k < k <= 4096:
            raise ValueError
        previous_k = k
    dataset = text_evaluation_dataset.admit(dataset_bytes, deadline_ms=remaining(30000))
    check()
    case = next((c for c in dataset.cases if c.case_id == case_id), None)
    if case is None:
        raise ValueError
    dataset_hash = hashlib.sha256(dataset_bytes).hexdigest()
    check()
    gold = text_evaluation_gold_binding.bind(
        originals, derived, dataset_bytes, gold_bundle_ids, deadline_ms=remaining(120000)
    )
    check()
    if (gold.dataset_id, gold.split_id, gold.dataset_sha256, gold.case_count) != (
        dataset.dataset_id,
        dataset.split_id,
        dataset_hash,
        dataset.case_count,
    ):
        raise ValueError
    all_atoms = set()
    selected_atoms = set()
    occurrences = selected_occurrences = 0
    for c in dataset.cases:
        for req in c.requirements:
            for alternative in req.alternatives:
                for span in alternative:
                    check()
                    key = _atom(span)
                    all_atoms.add(key)
                    occurrences += 1
                    if c is case:
                        selected_atoms.add(key)
                        selected_occurrences += 1
    if len(all_atoms) > 4096 or len(gold.bindings) > 4096:
        raise ValueError
    lookup = {}
    for binding in gold.bindings:
        check()
        key = _atom(binding)
        if key in lookup or not binding.bundle_ids:
            raise ValueError
        lookup[key] = binding
    if (
        set(lookup) != all_atoms
        or gold.distinct_atom_count != len(all_atoms)
        or gold.gold_atom_occurrences != occurrences
        or not selected_atoms <= lookup.keys()
    ):
        raise ValueError
    check()
    rank = source_bound_ranking.bind(
        originals,
        derived,
        store_root,
        snapshot_id,
        expected_catalog_id,
        chunk_ids,
        grants=grants,
        restrictions=restrictions,
        deadline_ms=remaining(30000),
    )
    check()
    if (
        rank.snapshot_id != snapshot_id
        or rank.catalog_id != expected_catalog_id
        or rank.row_count != len(chunk_ids)
        or len(rank.rows) != len(chunk_ids)
    ):
        raise ValueError
    total = 0
    for row, ident in zip(rank.rows, chunk_ids):
        check()
        if row.chunk_id != ident or len(row.fragments) > 256:
            raise ValueError
        total += len(row.fragments)
        if total > 65536:
            raise ValueError
    if total != rank.fragment_count:
        raise ValueError
    geometry = []
    for row in rank.rows:
        check()
        fragments = []
        for fragment in row.fragments:
            check()
            fragments.append((fragment.block_id, fragment.start, fragment.end))
        geometry.append((row.chunk_id, row.revision_id, row.extraction_id, tuple(fragments)))
    check()
    coverage = declared_span_support.score_case(
        dataset_bytes, case_id, tuple(geometry), cutoffs=cutoffs, deadline_ms=remaining(30000)
    )
    check()
    if (
        coverage.dataset_id,
        coverage.split_id,
        coverage.case_id,
        coverage.ranking_count,
        coverage.requirement_count,
    ) != (dataset.dataset_id, dataset.split_id, case_id, len(chunk_ids), len(case.requirements)):
        raise ValueError
    data = dict(
        dataset_id=dataset.dataset_id,
        split_id=dataset.split_id,
        case_id=case_id,
        dataset_sha256=dataset_hash,
        gold_binding_id=gold.binding_id,
        ranking_binding_id=rank.binding_id,
        snapshot_id=rank.snapshot_id,
        catalog_id=rank.catalog_id,
        authority_sha256=rank.authority_sha256,
        case_answerability=case.answerability,
        case_requirement_count=len(case.requirements),
        case_gold_atom_occurrences=selected_occurrences,
        case_distinct_gold_atoms=len(selected_atoms),
        global_gold_atom_occurrences=occurrences,
        global_distinct_gold_atoms=len(all_atoms),
        ranking_count=len(chunk_ids),
        source_fragment_count=total,
        global_gold_source_status=gold.source_binding_status,
        case_gold_source_status=(
            "ORIGINAL_GOLD_SPANS_REVALIDATED_AT_CALL_TIME"
            if selected_atoms
            else "NO_CASE_GOLD_REQUIREMENTS"
        ),
        ranking_source_status=rank.source_binding_status,
        geometry_fingerprint=coverage.input_fingerprint,
        at_k=coverage.at_k,
    )
    del dataset, case, gold, rank, lookup, all_atoms, selected_atoms, geometry
    c = req = alternative = span = binding = row = fragment = fragments = None
    check()
    preimage = dict(
        data,
        schema=1,
        kind="slaif-source-bound-text-support-v1",
        cutoffs=cutoffs,
        at_k=[asdict(item) for item in coverage.at_k],
    )
    check()
    digest = hashlib.sha256(b"slaif-source-bound-text-support-v1\n")
    size = 0
    encoder = json.JSONEncoder(
        sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False
    )
    for part in encoder.iterencode(preimage):
        check()
        encoded = part.encode("ascii")
        size += len(encoded)
        if size > 1048576:
            raise ValueError
        digest.update(encoded)
        check()
    check()
    ident = "sha256:" + digest.hexdigest()
    check()
    result = TextSupport(evaluation_id=ident, **data)
    check()
    return result


def score_case(
    originals,
    derived,
    store_root,
    snapshot_id,
    expected_catalog_id,
    dataset_bytes,
    case_id,
    gold_bundle_ids,
    chunk_ids,
    *,
    grants,
    restrictions=None,
    cutoffs=(20, 60),
    deadline_ms=30000,
):
    """Calculate private declared support; no current rights or query execution is attested."""
    try:
        start = time.monotonic()
        return _score(
            originals,
            derived,
            store_root,
            snapshot_id,
            expected_catalog_id,
            dataset_bytes,
            case_id,
            gold_bundle_ids,
            chunk_ids,
            grants,
            restrictions,
            cutoffs,
            deadline_ms,
            start,
        )
    except Exception:
        raise TextSupportError("source bound text support refused") from None
