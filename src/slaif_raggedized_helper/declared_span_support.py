"""Unverified geometry over supplied original-span declarations."""

from bisect import bisect_right
from dataclasses import dataclass, field
import hashlib
import json
import re
import time

from . import text_evaluation_dataset


class SpanSupportError(ValueError):
    """Input or deadline refused without exposing its contents."""


@dataclass(frozen=True, repr=False)
class RequirementCoverage:
    requirement_id: str
    alternative_covered: tuple
    covered: bool


@dataclass(frozen=True, repr=False)
class CoverageAtK:
    k: int
    returned_count: int
    covered_requirement_ids: tuple
    requirement_fraction: float | None
    complete_requirements: bool | None
    undefined_reason: str | None
    requirements: tuple


@dataclass(frozen=True, repr=False)
class CaseCoverage:
    dataset_id: str
    split_id: str
    case_id: str
    input_fingerprint: str
    requirement_count: int
    ranking_count: int
    at_k: tuple
    input_origin: str = field(default="SUPPLIED_UNVERIFIED", init=False)
    source_binding: str = field(default="UNVERIFIED", init=False)
    qualification: str = field(default="NOT_QUALIFIED", init=False)
    formula_version: str = field(default="declared-span-support-v1", init=False)


def _fail():
    raise ValueError


def _utf8_width(value, check):
    if type(value) is not str or not 1 <= len(value) <= 256:
        _fail()
    size = 0
    for char in value:
        check()
        n = ord(char)
        if 0xD800 <= n <= 0xDFFF:
            _fail()
        size += 1 if n < 0x80 else 2 if n < 0x800 else 3 if n < 0x10000 else 4
    if size > 1024:
        _fail()
    return size


def _score(dataset_bytes, case_id, ranking, cutoffs, deadline_ms, start):
    if type(deadline_ms) is not int or not 1 <= deadline_ms <= 30000:
        _fail()
    deadline = start + deadline_ms / 1000

    def check():
        if time.monotonic() >= deadline:
            _fail()

    if (
        type(dataset_bytes) is not bytes
        or type(case_id) is not str
        or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}", case_id)
        or type(ranking) is not tuple
        or len(ranking) > 4096
        or type(cutoffs) is not tuple
        or not 1 <= len(cutoffs) <= 16
    ):
        _fail()
    previous = 0
    for k in cutoffs:
        check()
        if type(k) is not int or not previous < k <= 4096:
            _fail()
        previous = k
    # Inspect tuple structure and all scalar types before consuming any contents.
    f = 0
    for row in ranking:
        check()
        if type(row) is not tuple or len(row) != 4:
            _fail()
        chunk, revision, extraction, fragments = row
        if (
            type(chunk) is not str
            or type(revision) is not str
            or type(extraction) is not str
            or type(fragments) is not tuple
            or not 1 <= len(fragments) <= 256
        ):
            _fail()
        f += len(fragments)
        if f > 65536:
            _fail()
        for fragment in fragments:
            check()
            if (
                type(fragment) is not tuple
                or len(fragment) != 3
                or type(fragment[0]) is not str
                or type(fragment[1]) is not int
                or type(fragment[2]) is not int
            ):
                _fail()
    remaining = int((deadline - time.monotonic()) * 1000)
    if remaining < 1:
        _fail()
    dataset = text_evaluation_dataset.admit(dataset_bytes, deadline_ms=min(remaining, 30000))
    check()
    case = next((c for c in dataset.cases if c.case_id == case_id), None)
    if case is None:
        _fail()
    u = len(case_id)
    seen = set()
    for chunk, revision, extraction, fragments in ranking:
        check()
        for value in (chunk, revision, extraction):
            if not re.fullmatch(r"sha256:[0-9a-f]{64}", value):
                _fail()
        if chunk in seen:
            _fail()
        seen.add(chunk)
        u += 213
        if u > 16777216:
            _fail()
        for block, lo, hi in fragments:
            check()
            if not 0 <= lo < hi <= 200000:
                _fail()
            u += _utf8_width(block, check)
            if u > 16777216:
                _fail()
    atoms = 0
    for requirement in case.requirements:
        check()
        for alternative in requirement.alternatives:
            for atom in alternative:
                check()
                atoms += 1
                u += (
                    len(atom.revision_id)
                    + len(atom.extraction_id)
                    + _utf8_width(atom.block_id, check)
                )
    log_f = max(1, (max(1, f) - 1).bit_length())
    if (
        len(cutoffs) * (f * (log_f + 2) + atoms * (log_f + 2) + len(case.requirements) + u)
        > 8388608
    ):
        _fail()
    results = []
    for k in cutoffs:
        check()
        groups = {}
        for _, revision, extraction, fragments in ranking[:k]:
            check()
            for block, lo, hi in fragments:
                check()
                groups.setdefault((revision, extraction, block), []).append((lo, hi))
        indexed = {}
        for key, intervals in groups.items():
            check()
            intervals.sort()
            check()
            merged = []
            for lo, hi in intervals:
                check()
                if merged and lo <= merged[-1][1]:
                    merged[-1] = (merged[-1][0], max(merged[-1][1], hi))
                else:
                    merged.append((lo, hi))
            indexed[key] = (tuple(x[0] for x in merged), tuple(x[1] for x in merged))
        rows = []
        for req in case.requirements:
            check()
            alternatives = []
            for alt in req.alternatives:
                covered = True
                for atom in alt:
                    check()
                    pair = indexed.get((atom.revision_id, atom.extraction_id, atom.block_id))
                    if pair is None:
                        covered = False
                    else:
                        pos = bisect_right(pair[0], atom.start) - 1
                        if pos < 0 or pair[1][pos] < atom.end:
                            covered = False
                alternatives.append(covered)
            alternatives = tuple(alternatives)
            rows.append(RequirementCoverage(req.requirement_id, alternatives, any(alternatives)))
        ids = tuple(row.requirement_id for row in rows if row.covered)
        count = len(rows)
        results.append(
            CoverageAtK(
                k,
                min(k, len(ranking)),
                ids,
                len(ids) / count if count else None,
                len(ids) == count if count else None,
                None if count else "NO_GOLD_REQUIREMENTS",
                tuple(rows),
            )
        )
    check()
    digest = hashlib.sha256(b"slaif-declared-span-support-v1\n")
    encoder = json.JSONEncoder(
        sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False
    )
    size = 0
    for part in encoder.iterencode(
        dict(dataset_id=dataset.dataset_id, case_id=case_id, ranking=ranking, cutoffs=cutoffs)
    ):
        check()
        size += len(part)
        if size > 67108864:
            _fail()
        digest.update(part.encode("ascii"))
    check()
    result = CaseCoverage(
        dataset.dataset_id,
        dataset.split_id,
        case_id,
        "sha256:" + digest.hexdigest(),
        len(case.requirements),
        len(ranking),
        tuple(results),
    )
    check()
    return result


def score_case(dataset_bytes, case_id, ranking, *, cutoffs=(20, 60), deadline_ms=5000):
    """Calculate declared coverage; the declarations remain unverified."""
    try:
        start = time.monotonic()
        return _score(dataset_bytes, case_id, ranking, cutoffs, deadline_ms, start)
    except Exception:
        raise SpanSupportError("declared span support refused") from None
