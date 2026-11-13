"""Pure diagnostics over supplied, unattested stage geometry."""

from bisect import bisect_right
from dataclasses import dataclass, field
import hashlib
import json
import re
import time

from . import declared_span_support, text_evaluation_dataset


class GeometryError(ValueError):
    """A diagnostic invocation was refused."""


@dataclass(frozen=True, repr=False)
class Completion:
    atom_coverage: tuple
    atom_occurrences: tuple
    covered_revisions: tuple
    required_revisions: tuple
    recall: float | None
    undefined_reason: str | None
    metric: str = field(default="DECLARED_REQUIRED_SOURCE_RECALL_NOT_QUALIFIED", init=False)


@dataclass(frozen=True, repr=False)
class Stage:
    name: str
    cutoff: int
    row_count: int
    coverage: declared_span_support.CoverageAtK
    completion: Completion
    fingerprint: str


@dataclass(frozen=True, repr=False)
class Transition:
    source: str
    target: str
    lost_requirements: tuple
    lost_alternatives: tuple
    gained_requirements: tuple
    gained_alternatives: tuple


@dataclass(frozen=True, repr=False)
class Diagnosis:
    invocation_id: str
    stages: tuple
    prefixes: tuple
    transitions: tuple
    work: int
    serialization_budget: int
    chunk_metric_reason: str = field(default="NO_EXPLICIT_CHUNK_RELEVANCE_MAPPING", init=False)
    source_binding: str = field(default="UNVERIFIED", init=False)
    stage_origin: str = field(default="SUPPLIED_STAGE_RELATIONS_ONLY", init=False)
    eligibility: str = field(default="NOT_CHECKED", init=False)
    execution: str = field(default="NOT_ATTESTED", init=False)
    qualification: str = field(default="NOT_QUALIFIED", init=False)


_NAMES = (
    "dense.eligible",
    "dense.ranked",
    "dense.selected",
    "dense.returned",
    "lexical.eligible",
    "lexical.ranked",
    "lexical.selected",
    "lexical.returned",
    "fusion.input",
    "fusion.returned",
)
_ID = re.compile(r"sha256:[0-9a-f]{64}\Z")
_CASE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}\Z")


def _fail():
    raise ValueError


def _diagnose(data, case_id, rows, stages, deadline_ms, start):
    if type(deadline_ms) is not int or not 1 <= deadline_ms <= 10000:
        _fail()
    deadline = start + deadline_ms / 1000

    def check():
        if time.monotonic() >= deadline:
            _fail()

    def remaining(cap):
        check()
        value = int((deadline - time.monotonic()) * 1000)
        if value < 1:
            _fail()
        return min(value, cap)

    if (
        type(data) is not bytes
        or not 1 <= len(data) <= 1048576
        or type(case_id) is not str
        or not 1 <= len(case_id) <= 128
        or type(rows) is not tuple
        or len(rows) > 512
        or type(stages) is not tuple
        or len(stages) != 10
    ):
        _fail()
    f = length = indices = 0
    for row in rows:
        check()
        if type(row) is not tuple or len(row) != 4:
            _fail()
        chunk, revision, extraction, fragments = row
        for value in (chunk, revision, extraction):
            if type(value) is not str or len(value) != 71:
                _fail()
        if type(fragments) is not tuple or not 1 <= len(fragments) <= 256:
            _fail()
        f += len(fragments)
        if f > 8192:
            _fail()
        for fragment in fragments:
            check()
            if type(fragment) is not tuple or len(fragment) != 3:
                _fail()
            block, lo, hi = fragment
            if (
                type(block) is not str
                or not 1 <= len(block) <= 256
                or type(lo) is not int
                or type(hi) is not int
                or not 0 <= lo < hi <= 200000
            ):
                _fail()
            length += len(block)
            if length > 65536:
                _fail()
    for stage_index, stage in enumerate(stages):
        check()
        if type(stage) is not tuple or len(stage) != 2:
            _fail()
        name, ordinals = stage
        if (
            type(name) is not str
            or not 1 <= len(name) <= 32
            or type(ordinals) is not tuple
            or len(ordinals) > 512
            or (stage_index in (3, 7, 9) and len(ordinals) > 60)
        ):
            _fail()
        indices += len(ordinals)
        if indices > 5120:
            _fail()
        for ordinal in ordinals:
            check()
            if type(ordinal) is not int or not 0 <= ordinal < len(rows):
                _fail()
    if not _CASE.fullmatch(case_id):
        _fail()
    # The initial parser has its own bounded 3*D precharge.
    if 3 * len(data) > 67108864:
        _fail()
    dataset = text_evaluation_dataset.admit(data, deadline_ms=remaining(5000))
    check()
    if dataset.case_count > 256 or dataset.gold_atom_count > 512:
        _fail()
    case = next((item for item in dataset.cases if item.case_id == case_id), None)
    if case is None:
        _fail()
    n, g, c, d = len(rows), dataset.gold_atom_count, dataset.case_count, len(data)
    j = max(1, (f + 1).bit_length())
    work = 42 * d + 29 * (f + g + 1) * (j + 6) + 64 * (n + indices + c + g + 1)
    budget = 56 * d + 29 * (4 * length + 96 * f + 256 * n + 128 * g) + 4194304
    if work > 67108864 or budget > 134217728:
        _fail()
    seen = set()
    for chunk, revision, extraction, fragments in rows:
        check()
        if (
            any(not _ID.fullmatch(value) for value in (chunk, revision, extraction))
            or chunk in seen
        ):
            _fail()
        seen.add(chunk)
        for block, _, _ in fragments:
            check()
            if len(block.encode("utf-8")) > 1024:
                _fail()
    sets = []
    for i, (name, ordinals) in enumerate(stages):
        check()
        if name != _NAMES[i] or len(set(ordinals)) != len(ordinals):
            _fail()
        sets.append(set(ordinals))
    if (
        sets[0] != sets[1]
        or sets[0] != sets[4]
        or not sets[5] <= sets[4]
        or not sets[2] <= sets[1]
        or not sets[3] <= sets[2]
        or not sets[6] <= sets[5]
        or not sets[7] <= sets[6]
        or sets[8] != sets[3] | sets[7]
        or not sets[9] <= sets[8]
    ):
        _fail()

    atoms = []
    seen_atoms = set()
    occurrences = []
    for req in case.requirements:
        for alternative_index, alt in enumerate(req.alternatives):
            for atom_index, atom in enumerate(alt):
                check()
                key = (
                    atom.revision_id,
                    atom.extraction_id,
                    atom.block_id,
                    atom.start,
                    atom.end,
                    atom.text_sha256,
                )
                occurrences.append((req.requirement_id, alternative_index, atom_index, key))
                if key not in seen_atoms:
                    seen_atoms.add(key)
                    atoms.append(key)
    atom_ids = []
    for atom in atoms:
        check()
        encoded = json.dumps(atom, ensure_ascii=True, separators=(",", ":")).encode("ascii")
        check()
        atom_ids.append(
            "sha256:" + hashlib.sha256(b"slaif-declared-gold-atom-v1\n" + encoded).hexdigest()
        )
        check()
    atom_id_by_key = dict(zip(atoms, atom_ids))
    occurrence_ids = tuple(
        (req, alt, index, atom_id_by_key[key]) for req, alt, index, key in occurrences
    )
    check()
    mandatory = [
        a for req in case.requirements if len(req.alternatives) == 1 for a in req.alternatives[0]
    ]
    revisions = tuple(sorted({a.revision_id for a in mandatory}))
    reason = (
        "NO_GOLD_SOURCES"
        if not atoms
        else "AMBIGUOUS_ALTERNATIVE_SOURCE_UNIVERSE"
        if any(len(req.alternatives) != 1 for req in case.requirements)
        else None
    )

    def completion(ordinals):
        groups = {}
        for index in ordinals:
            check()
            _, rev, ext, fragments = rows[index]
            for block, lo, hi in fragments:
                check()
                groups.setdefault((rev, ext, block), []).append((lo, hi))
        merged = {}
        for key, intervals in groups.items():
            check()
            intervals.sort()
            check()
            out = []
            for lo, hi in intervals:
                check()
                if out and lo <= out[-1][1]:
                    out[-1] = (out[-1][0], max(out[-1][1], hi))
                else:
                    out.append((lo, hi))
            merged[key] = (tuple(lo for lo, _ in out), tuple(hi for _, hi in out))
        flags = []
        for atom in atoms:
            check()
            pair = merged.get(atom[:3])
            pos = bisect_right(pair[0], atom[3]) - 1 if pair else -1
            flags.append(pos >= 0 and pair[1][pos] >= atom[4])
        flags = tuple(flags)
        check()
        revision_flags = {}
        if reason is None:
            for atom, flag in zip(atoms, flags):
                check()
                revision_flags[atom[0]] = revision_flags.get(atom[0], True) and flag
        covered = tuple(rev for rev in revisions if revision_flags[rev]) if reason is None else ()
        return Completion(
            tuple(zip(atom_ids, flags)),
            occurrence_ids,
            covered,
            revisions if reason is None else (),
            len(covered) / len(revisions) if reason is None else None,
            reason,
        )

    def digest(payload, domain):
        check()
        h = hashlib.sha256(domain)
        encoder = json.JSONEncoder(
            sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False
        )
        size = 0
        for part in encoder.iterencode(payload):
            check()
            size += len(part)
            if size > budget:
                _fail()
            h.update(part.encode("ascii"))
        check()
        return "sha256:" + h.hexdigest()

    def record(name, cutoff, ordinals, coverage, comp, lower_fingerprint):
        fingerprint = digest(
            (
                name,
                cutoff,
                ordinals,
                lower_fingerprint,
                coverage.covered_requirement_ids,
                [(r.requirement_id, r.alternative_covered) for r in coverage.requirements],
                comp.atom_coverage,
                comp.atom_occurrences,
                comp.recall,
                comp.undefined_reason,
            ),
            b"slaif-declared-stage-record-v1\n",
        )
        return Stage(name, cutoff, len(ordinals), coverage, comp, fingerprint)

    full = []
    for name, ordinals in stages:
        check()
        ranking = tuple(rows[i] for i in ordinals)
        check()
        coverage = declared_span_support.score_case(
            data, case_id, ranking, cutoffs=(max(1, len(ordinals)),), deadline_ms=remaining(30000)
        )
        check()
        full.append(
            record(
                name, max(1, len(ordinals)), ordinals, coverage.at_k[0],
                completion(ordinals), coverage.input_fingerprint,
            )
        )
    prefixes = []
    for index in (3, 7, 9):
        name, ordinals = stages[index]
        ranking = tuple(rows[i] for i in ordinals)
        check()
        coverage = declared_span_support.score_case(
            data, case_id, ranking, cutoffs=(20, 60), deadline_ms=remaining(30000)
        )
        check()
        prefixes.append(
            record(
                name, 20, ordinals[:20], coverage.at_k[0],
                completion(ordinals[:20]), coverage.input_fingerprint,
            )
        )
        prefixes.append(
            record(
                name, 60, ordinals, coverage.at_k[1], full[index].completion,
                coverage.input_fingerprint,
            )
        )
    transitions = []
    for a, b in ((0, 1), (1, 2), (2, 3), (4, 5), (5, 6), (6, 7), (8, 9)):
        check()
        before, after = full[a].coverage, full[b].coverage
        br = set(before.covered_requirement_ids)
        ar = set(after.covered_requirement_ids)
        ba = {
            (r.requirement_id, i)
            for r in before.requirements
            for i, v in enumerate(r.alternative_covered)
            if v
        }
        aa = {
            (r.requirement_id, i)
            for r in after.requirements
            for i, v in enumerate(r.alternative_covered)
            if v
        }
        if ar - br or aa - ba:
            _fail()
        transitions.append(
            Transition(_NAMES[a], _NAMES[b], tuple(sorted(br - ar)), tuple(sorted(ba - aa)), (), ())
        )
    check()
    data_hash = hashlib.sha256(data).hexdigest()
    check()
    invocation = digest(
        (
            data_hash,
            case_id,
            "declared-stage-geometry-v1",
            rows,
            stages,
            [x.fingerprint for x in full],
            [x.fingerprint for x in prefixes],
            work,
            budget,
            deadline_ms,
            "NO_EXPLICIT_CHUNK_RELEVANCE_MAPPING",
        ),
        b"slaif-declared-stage-invocation-v1\n",
    )
    result = Diagnosis(invocation, tuple(full), tuple(prefixes), tuple(transitions), work, budget)
    check()
    return result


def diagnose(dataset_bytes, case_id, rows, stages, *, deadline_ms=10000):
    """Diagnose declared coverage; source identity and eligibility are not verified."""
    try:
        start = time.monotonic()
        return _diagnose(dataset_bytes, case_id, rows, stages, deadline_ms, start)
    except Exception:
        raise GeometryError("declared stage geometry refused") from None
