"""Private, pure aggregation of supplied declared stage geometry.

The records in this module describe declared geometry, not observed retrieval.
"""

from dataclasses import dataclass, fields
import hashlib
import json
from math import gcd
import time

from . import declared_span_support as span
from . import declared_stage_geometry as geometry


class CohortMetricsError(ValueError):
    """The entire cohort was refused, without exposing its input."""


@dataclass(frozen=True, repr=False)
class Ratio:
    """A normalized nonnegative exact rational."""

    numerator: int
    denominator: int

    def __post_init__(self):
        if (
            type(self.numerator) is not int
            or type(self.denominator) is not int
            or self.numerator.bit_length() > 8192
            or self.denominator.bit_length() > 8192
            or self.numerator < 0
            or self.denominator <= 0
            or gcd(self.numerator, self.denominator) != 1
        ):
            raise ValueError("invalid ratio")


class _Meter:
    """Cumulative logical reservations and cooperative deadline."""

    def __init__(self, start, deadline_ms, max_work, max_payload):
        if (
            type(deadline_ms) is not int
            or deadline_ms.bit_length() > 8192
            or type(max_work) is not int
            or max_work.bit_length() > 8192
            or type(max_payload) is not int
            or max_payload.bit_length() > 8192
            or not 1 <= deadline_ms <= 10000
            or not 0 <= max_work <= 134217728
            or not 0 <= max_payload <= 268435456
        ):
            raise ValueError
        self.deadline = start + deadline_ms / 1000
        self.max_work = max_work
        self.max_payload = max_payload
        self.work = 0
        self.payload = 0

    def check(self):
        if time.monotonic() >= self.deadline:
            raise ValueError

    def reserve(self, work, payload=0):
        self.check()
        if work < 0 or payload < 0:
            raise ValueError
        if work > self.max_work - self.work or payload > self.max_payload - self.payload:
            raise ValueError
        self.work += work
        self.payload += payload

    def integer(self, value):
        self.reserve(3)
        if type(value) is not int or value.bit_length() > 8192:
            raise ValueError
        return value

    def rational(self, numerator, denominator):
        self.integer(numerator)
        self.integer(denominator)
        if numerator < 0 or denominator <= 0:
            raise ValueError
        bits = numerator.bit_length() + denominator.bit_length() + 2
        # Two gcds (normalization and Ratio's invariant), two divisions and record allocation.
        self.reserve(4 * bits * bits + 8 * bits + 32, 32)
        divisor = gcd(numerator, denominator)
        return Ratio(numerator // divisor, denominator // divisor)


@dataclass(frozen=True, repr=False)
class PrefixCase:
    stage: str
    cutoff: int
    covered_revisions: int
    required_revisions: int
    source_undefined_reason: str | None
    complete: bool | None
    complete_undefined_reason: str | None


@dataclass(frozen=True, repr=False)
class LossCase:
    source: str
    target: str
    complete_before: bool | None
    complete_after: bool | None
    source_before: Ratio | None
    source_after: Ratio | None
    source_undefined_reason: str | None
    requirements_before: int
    requirements_lost: int
    alternatives_before: int
    alternatives_lost: int


@dataclass(frozen=True, repr=False)
class CaseSummary:
    case_id: str
    geometry_id: str
    prefixes: tuple
    losses: tuple


@dataclass(frozen=True, repr=False)
class PrefixSummary:
    stage: str
    cutoff: int
    total: int
    source_defined: int
    source_undefined: int
    source_reasons: tuple
    source_denominator: int
    source_macro: Ratio | None
    source_empty_reason: str | None
    complete_defined: int
    complete_undefined: int
    complete_reasons: tuple
    complete_denominator: int
    complete_rate: Ratio | None
    complete_empty_reason: str | None


@dataclass(frozen=True, repr=False)
class CountLossSummary:
    lost: int
    before: int
    eligible_cases: int
    undefined_cases: int
    pooled: Ratio | None
    macro: Ratio | None
    undefined_reason: str | None


@dataclass(frozen=True, repr=False)
class TransitionSummary:
    source: str
    target: str
    total: int
    complete_defined: int
    complete_undefined: int
    complete_reasons: tuple
    complete_eligible: int
    complete_incomplete_before: int
    complete_lost: int
    complete_rate: Ratio | None
    complete_empty_reason: str | None
    source_defined: int
    source_undefined: int
    source_reasons: tuple
    source_denominator: int
    source_loss: Ratio | None
    source_empty_reason: str | None
    requirements: CountLossSummary
    alternatives: CountLossSummary


@dataclass(frozen=True, repr=False)
class Report:
    case_count: int
    cases: tuple
    prefixes: tuple
    transitions: tuple
    identity: str
    checkpoint_work: int
    checkpoint_payload: int
    final_work: int
    final_payload: int
    max_work: int
    max_payload: int
    formula_version: str = "declared-cohort-metrics-v1"
    source_binding: str = "UNVERIFIED"
    input_origin: str = "SUPPLIED_DECLARED_GEOMETRY_ONLY"
    execution: str = "NOT_ATTESTED"
    qualification: str = "NOT_QUALIFIED"
    chunk_metric_reason: str = "NO_EXPLICIT_CHUNK_RELEVANCE_MAPPING"


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
_EDGES = ((0, 1), (1, 2), (2, 3), (4, 5), (5, 6), (6, 7), (8, 9))
_PREFIXES = ((3, 20), (3, 60), (7, 20), (7, 60), (9, 20), (9, 60))


def _tuple(meter, value, minimum, maximum):
    meter.reserve(4)
    if type(value) is not tuple or not minimum <= len(value) <= maximum:
        raise ValueError
    return value


def _identifier(meter, value, digest=False):
    meter.reserve(5)
    if type(value) is not str or not 1 <= len(value) <= (71 if digest else 128):
        raise ValueError
    # Per character, 18 covers a one-character probe of the 16-character
    # hexadecimal alphabet; the remaining allowance covers visits, ASCII and
    # alphanumeric checks, punctuation probes and the fixed prefix comparison.
    meter.reserve(32 * len(value) + 32, len(value) if digest else 0)
    if digest:
        if (
            len(value) != 71
            or not value.startswith("sha256:")
            or any(c not in "0123456789abcdef" for c in value[7:])
        ):
            raise ValueError
    elif (
        not value[0].isascii()
        or not value[0].isalnum()
        or any(not c.isascii() or not (c.isalnum() or c in "._:-") for c in value)
    ):
        raise ValueError
    return value


def _bounded_int(meter, value, low, high):
    meter.integer(value)
    meter.reserve(2)
    if not low <= value <= high:
        raise ValueError
    return value


def _bool(meter, value):
    meter.reserve(2)
    if type(value) is not bool:
        raise ValueError
    return value


def _equal(meter, left, right, cost=1):
    meter.reserve(2)
    if type(left) is str and type(right) is str:
        cost = max(cost, len(left) + len(right) + 1)
    meter.reserve(cost)
    if left != right:
        raise ValueError


def _marker(meter, value, allowed, *, optional=False):
    meter.reserve(8 * len(allowed) + 8)
    if value is None and optional:
        return
    if type(value) is not str or len(value) > max(map(len, allowed)):
        raise ValueError
    meter.reserve(sum(len(value) + len(item) + 1 for item in allowed))
    if value not in allowed:
        raise ValueError


def _subset(meter, smaller, larger):
    # Inputs are validated sorted unique 71-byte strings. Two-pointer traversal visits
    # each at most once, and each comparison charges both strings and a visit.
    meter.reserve((len(smaller) + len(larger) + 1) * 300)
    i = j = 0
    while i < len(smaller) and j < len(larger):
        if smaller[i] == larger[j]:
            i += 1
            j += 1
        elif smaller[i] > larger[j]:
            j += 1
        else:
            return False
    return i == len(smaller)


def _stage(meter, stage, name, cutoff, expected_rows=None):
    meter.reserve(1)
    if type(stage) is not geometry.Stage:
        raise ValueError
    _equal(meter, _identifier(meter, stage.name), name, len(name) * 2 + 1)
    row_count = _bounded_int(meter, stage.row_count, 0, 512)
    if expected_rows is not None:
        _equal(meter, row_count, expected_rows)
    actual_cutoff = _bounded_int(meter, stage.cutoff, 1, 512)
    _equal(meter, actual_cutoff, cutoff if cutoff else max(1, row_count))
    _identifier(meter, stage.fingerprint, digest=True)
    cov, comp = stage.coverage, stage.completion
    meter.reserve(2)
    if type(cov) is not span.CoverageAtK or type(comp) is not geometry.Completion:
        raise ValueError
    _equal(meter, _bounded_int(meter, cov.k, 1, 512), actual_cutoff)
    _equal(meter, _bounded_int(meter, cov.returned_count, 0, 512), row_count)
    requirements = _tuple(meter, cov.requirements, 0, 16)
    covered_ids = _tuple(meter, cov.covered_requirement_ids, 0, 16)
    meter.reserve(4, 32)
    req_ids, flags, alt_flags, expected_ids = [], [], [], []
    for requirement in requirements:
        meter.reserve(1)
        if type(requirement) is not span.RequirementCoverage:
            raise ValueError
        rid = _identifier(meter, requirement.requirement_id)
        alternatives = _tuple(meter, requirement.alternative_covered, 1, 8)
        for flag in alternatives:
            _bool(meter, flag)
        _bool(meter, requirement.covered)
        meter.reserve(len(alternatives) + 5 + len(req_ids) * (2 * 128 + 1), 4 * 8)
        if requirement.covered != any(alternatives) or rid in req_ids:
            raise ValueError
        req_ids.append(rid)
        flags.append(requirement.covered)
        alt_flags.append(alternatives)
        if requirement.covered:
            expected_ids.append(rid)
    for rid in covered_ids:
        _identifier(meter, rid)
    meter.reserve(1 + len(req_ids) * 257, 8 * len(expected_ids))
    if tuple(expected_ids) != covered_ids:
        raise ValueError
    _marker(meter, cov.undefined_reason, ("NO_GOLD_REQUIREMENTS",), optional=True)
    count, covered = len(requirements), len(expected_ids)
    meter.reserve(4)
    if count:
        if (
            type(cov.requirement_fraction) is not float
            or cov.requirement_fraction != covered / count
            or type(cov.complete_requirements) is not bool
            or cov.complete_requirements != (covered == count)
            or cov.undefined_reason is not None
        ):
            raise ValueError
    elif (
        cov.requirement_fraction is not None
        or cov.complete_requirements is not None
        or cov.undefined_reason != "NO_GOLD_REQUIREMENTS"
    ):
        raise ValueError

    atoms = _tuple(meter, comp.atom_coverage, 0, 512)
    occurrences = _tuple(meter, comp.atom_occurrences, 0, 512)
    meter.reserve(2, 16)
    atom_ids, atom_flags = [], []
    for atom in atoms:
        _tuple(meter, atom, 2, 2)
        aid = _identifier(meter, atom[0], digest=True)
        _bool(meter, atom[1])
        meter.reserve(len(atom_ids) * 143 + 3, 16)
        if aid in atom_ids:
            raise ValueError
        atom_ids.append(aid)
        atom_flags.append(atom[1])
    meter.reserve(1, 8)
    occurrence_keys = []
    for item in occurrences:
        _tuple(meter, item, 4, 4)
        rid = _identifier(meter, item[0])
        alt = _bounded_int(meter, item[1], 0, 7)
        index = _bounded_int(meter, item[2], 0, 7)
        aid = _identifier(meter, item[3], digest=True)
        meter.reserve((2 * len(req_ids) + len(atom_ids) + len(occurrence_keys)) * 260 + 10, 32)
        if rid not in req_ids or aid not in atom_ids:
            raise ValueError
        req_index = req_ids.index(rid)
        if alt >= len(alt_flags[req_index]) or (rid, alt, index) in occurrence_keys:
            raise ValueError
        occurrence_keys.append((rid, alt, index))
    meter.reserve((len(atom_ids) * len(occurrences) + 1) * 143)
    if any(not any(aid == item[3] for item in occurrences) for aid in atom_ids):
        raise ValueError
    # Each declared alternative has a contiguous, nonempty sequence of atoms.
    for rid, alternatives in zip(req_ids, alt_flags):
        for alt in range(len(alternatives)):
            meter.reserve(len(occurrence_keys) * 270 + 10, 48 * len(occurrence_keys) + 32)
            indices = [key[2] for key in occurrence_keys if key[:2] == (rid, alt)]
            if not indices or indices != list(range(len(indices))):
                raise ValueError
            meter.reserve(len(occurrences) * (len(atom_ids) * 143 + 260) + 10)
            expected = all(
                atom_flags[atom_ids.index(item[3])]
                for item in occurrences
                if item[0] == rid and item[1] == alt
            )
            if alternatives[alt] != expected:
                raise ValueError
    required = _tuple(meter, comp.required_revisions, 0, 512)
    revisions = _tuple(meter, comp.covered_revisions, 0, 512)
    for values in (required, revisions):
        previous = None
        for value in values:
            _identifier(meter, value, digest=True)
            meter.reserve(143)
            if previous is not None and previous >= value:
                raise ValueError
            previous = value
    _marker(meter, comp.metric, ("DECLARED_REQUIRED_SOURCE_RECALL_NOT_QUALIFIED",))
    _marker(
        meter,
        comp.undefined_reason,
        ("NO_GOLD_SOURCES", "AMBIGUOUS_ALTERNATIVE_SOURCE_UNIVERSE"),
        optional=True,
    )
    meter.reserve(512 + len(alt_flags) * 8)
    if comp.undefined_reason is None:
        if (
            not required
            or not _subset(meter, revisions, required)
            or type(comp.recall) is not float
            or comp.recall != len(revisions) / len(required)
        ):
            raise ValueError
    elif (
        comp.undefined_reason not in ("NO_GOLD_SOURCES", "AMBIGUOUS_ALTERNATIVE_SOURCE_UNIVERSE")
        or required
        or revisions
        or comp.recall is not None
    ):
        raise ValueError
    if (not occurrences) != (comp.undefined_reason == "NO_GOLD_SOURCES"):
        raise ValueError
    if occurrences and (
        any(len(alt) != 1 for alt in alt_flags)
        != (comp.undefined_reason == "AMBIGUOUS_ALTERNATIVE_SOURCE_UNIVERSE")
    ):
        raise ValueError
    meter.reserve(16 + len(atom_flags) + len(flags) + 8 * len(alt_flags))
    if row_count == 0 and (
        any(atom_flags) or any(flags) or any(any(alt) for alt in alt_flags) or revisions
    ):
        raise ValueError
    meter.reserve(
        len(occurrences) * 8 + len(requirements) * 8 + len(atom_ids) * 4 + 20,
        8 * (4 * len(requirements) + 2 * len(atom_ids) + 9),
    )
    return (
        tuple(req_ids),
        tuple(flags),
        tuple(alt_flags),
        tuple(atom_ids),
        tuple(atom_flags),
        occurrences,
        required,
        revisions,
        comp.undefined_reason,
    )


def _relation(meter, before, after):
    # Both records have already passed scalar and shape admission.
    meter.reserve(
        100 + 520 * (len(before[0]) + len(before[3]) + len(before[5]) + len(before[6])),
        16 * (len(before[2]) + len(after[2])) + 32,
    )
    if (
        before[0] != after[0]
        or tuple(map(len, before[2])) != tuple(map(len, after[2]))
        or before[3] != after[3]
        or before[5] != after[5]
        or before[6] != after[6]
        or before[8] != after[8]
    ):
        raise ValueError


def _same_evidence(meter, before, after):
    _relation(meter, before, after)
    # Flags and revision tuples have already been admitted under the same universe.
    meter.reserve(64 + 16 * (len(before[0]) + len(before[3])) + 143 * len(before[7]))
    if (
        before[1] != after[1]
        or before[2] != after[2]
        or before[4] != after[4]
        or before[7] != after[7]
    ):
        raise ValueError


def _loss(meter, before, after, source, target):
    _relation(meter, before, after)
    meter.reserve(100 + 300 * (len(before[0]) + len(before[3]) + len(before[6])))
    if any(a and not b for a, b in zip(after[4], before[4])):
        raise ValueError
    if not _subset(meter, after[7], before[7]):
        raise ValueError
    meter.reserve(2, 16)
    lost_requirements, lost_alternatives = [], []
    for rid, bflag, aflag, balts, aalts in zip(before[0], before[1], after[1], before[2], after[2]):
        meter.reserve(16 + len(rid) * 4 + len(balts) * 16, 16 + len(balts) * 32)
        if aflag and not bflag:
            raise ValueError
        if bflag and not aflag:
            lost_requirements.append(rid)
        for index, (b, a) in enumerate(zip(balts, aalts)):
            if a and not b:
                raise ValueError
            if b and not a:
                lost_alternatives.append((rid, index))
    count = len(lost_requirements) + len(lost_alternatives)
    # At most count squared string comparisons; 257 covers two maximum IDs and a visit.
    meter.reserve((count * count + 1) * 257 + count * 4, count * 32 + 32)
    return tuple(sorted(lost_requirements)), tuple(sorted(lost_alternatives))


def _diagnosis(meter, diagnosis):
    meter.reserve(1)
    if type(diagnosis) is not geometry.Diagnosis:
        raise ValueError
    _identifier(meter, diagnosis.invocation_id, digest=True)
    _bounded_int(meter, diagnosis.work, 0, 67108864)
    _bounded_int(meter, diagnosis.serialization_budget, 0, 134217728)
    for value, expected in (
        (diagnosis.chunk_metric_reason, "NO_EXPLICIT_CHUNK_RELEVANCE_MAPPING"),
        (diagnosis.source_binding, "UNVERIFIED"),
        (diagnosis.stage_origin, "SUPPLIED_STAGE_RELATIONS_ONLY"),
        (diagnosis.eligibility, "NOT_CHECKED"),
        (diagnosis.execution, "NOT_ATTESTED"),
        (diagnosis.qualification, "NOT_QUALIFIED"),
    ):
        _marker(meter, value, (expected,))
    stages = _tuple(meter, diagnosis.stages, 10, 10)
    prefixes = _tuple(meter, diagnosis.prefixes, 6, 6)
    transitions = _tuple(meter, diagnosis.transitions, 7, 7)
    # Reserve the three owned staging lists (full, prefix_records, losses).
    meter.reserve(3, 24)
    full = []
    for name, stage in zip(_NAMES, stages):
        meter.reserve(2, 8)
        full.append(_stage(meter, stage, name, None))
    for i in (3, 7, 9):
        _bounded_int(meter, stages[i].row_count, 0, 60)
    prefix_records = []
    for prefix, (index, cutoff) in zip(prefixes, _PREFIXES):
        meter.reserve(2, 8)
        record = _stage(meter, prefix, _NAMES[index], cutoff, min(stages[index].row_count, cutoff))
        _relation(meter, full[0], record)
        # A prefix can only remove evidence from its full returned stage.
        _loss(meter, full[index], record, _NAMES[index], _NAMES[index])
        meter.reserve(2)
        if stages[index].row_count <= cutoff:
            _same_evidence(meter, full[index], record)
        prefix_records.append(record)
    for record in full[1:]:
        _relation(meter, full[0], record)
    meter.reserve(32)
    if not stages[0].row_count == stages[1].row_count == stages[4].row_count:
        raise ValueError
    _same_evidence(meter, full[0], full[1])
    _same_evidence(meter, full[0], full[4])
    for a, b in _EDGES:
        meter.reserve(4)
        if stages[b].row_count > stages[a].row_count:
            raise ValueError
        if stages[b].row_count == stages[a].row_count:
            _same_evidence(meter, full[a], full[b])
    meter.reserve(16)
    if not (
        max(stages[3].row_count, stages[7].row_count)
        <= stages[8].row_count
        <= min(stages[3].row_count + stages[7].row_count, stages[0].row_count)
    ):
        raise ValueError
    # Fusion may combine partial fragments: inclusion is necessary, OR equality is not.
    _loss(meter, full[0], full[8], _NAMES[0], _NAMES[8])
    _loss(meter, full[8], full[3], _NAMES[8], _NAMES[3])
    _loss(meter, full[8], full[7], _NAMES[8], _NAMES[7])
    for a, b in ((0, 8), (8, 3), (8, 7)):
        meter.reserve(3)
        if stages[a].row_count == stages[b].row_count:
            _same_evidence(meter, full[a], full[b])
    losses = []
    for transition, (a, b) in zip(transitions, _EDGES):
        meter.reserve(1)
        if type(transition) is not geometry.Transition:
            raise ValueError
        _equal(meter, _identifier(meter, transition.source), _NAMES[a], 65)
        _equal(meter, _identifier(meter, transition.target), _NAMES[b], 65)
        # Validate all exposed transition scalars before comparing them.
        lost_req = _tuple(meter, transition.lost_requirements, 0, 16)
        lost_alt = _tuple(meter, transition.lost_alternatives, 0, 128)
        gained_req = _tuple(meter, transition.gained_requirements, 0, 16)
        gained_alt = _tuple(meter, transition.gained_alternatives, 0, 128)
        for values in (lost_req, gained_req):
            for rid in values:
                _identifier(meter, rid)
        for values in (lost_alt, gained_alt):
            for pair in values:
                _tuple(meter, pair, 2, 2)
                _identifier(meter, pair[0])
                _bounded_int(meter, pair[1], 0, 7)
        expected = _loss(meter, full[a], full[b], _NAMES[a], _NAMES[b])
        meter.reserve(144 * 260 + 100, 24)
        if gained_req or gained_alt or (lost_req, lost_alt) != expected:
            raise ValueError
        losses.append(expected)
    meter.reserve(30, 8 * (len(full) + len(prefix_records) + len(losses)))
    return tuple(full), tuple(prefix_records), tuple(losses)


def _add(meter, left, right, subtract=False):
    # Bound each intermediate before multiplying, and charge for both multiplications and sum.
    a, b, c, d = left.numerator, left.denominator, right.numerator, right.denominator
    meter.reserve((a.bit_length() + b.bit_length() + c.bit_length() + d.bit_length() + 4) ** 2)
    if (
        max(
            a.bit_length() + d.bit_length(),
            c.bit_length() + b.bit_length(),
            b.bit_length() + d.bit_length(),
        )
        > 8191
    ):
        raise ValueError
    numerator = a * d - c * b if subtract else a * d + c * b
    denominator = b * d
    if numerator < 0 or numerator.bit_length() > 8192 or denominator.bit_length() > 8192:
        raise ValueError
    return meter.rational(numerator, denominator)


def _mean(meter, values):
    meter.reserve(1)
    if not values:
        return None
    result = meter.rational(0, 1)
    for value in values:
        meter.reserve(1)
        result = _add(meter, result, value)
    meter.reserve((result.denominator.bit_length() + len(values).bit_length() + 1) ** 2)
    if result.denominator.bit_length() + len(values).bit_length() > 8192:
        raise ValueError
    return meter.rational(result.numerator, result.denominator * len(values))


def _prefix_case(meter, stage, record):
    meter.reserve(12, 96)
    return PrefixCase(
        stage.name,
        stage.cutoff,
        len(record[7]),
        len(record[6]),
        record[8],
        stage.coverage.complete_requirements,
        stage.coverage.undefined_reason,
    )


def _loss_case(meter, before, after, lost, a, b):
    meter.reserve(64 + 32 * (len(before[0]) + 8 * len(before[2])), 128)
    before_source = meter.rational(len(before[7]), len(before[6])) if before[8] is None else None
    after_source = meter.rational(len(after[7]), len(after[6])) if after[8] is None else None
    return LossCase(
        _NAMES[a],
        _NAMES[b],
        all(before[1]) if before[0] else None,
        all(after[1]) if after[0] else None,
        before_source,
        after_source,
        before[8],
        sum(before[1]),
        len(lost[0]),
        sum(sum(flags) for flags in before[2]),
        len(lost[1]),
    )


def _reasons(meter, values):
    # The only permitted reasons were validated in the admission phase.
    meter.reserve(len(values) * 400 + 128, 256)
    return tuple(
        (reason, values.count(reason))
        for reason in (
            "NO_GOLD_REQUIREMENTS",
            "NO_GOLD_SOURCES",
            "AMBIGUOUS_ALTERNATIVE_SOURCE_UNIVERSE",
        )
        if reason in values
    )


def _prefix_summary(meter, values):
    meter.reserve(40 + len(values) * 32, len(values) * 40 + 256)
    source = [
        meter.rational(v.covered_revisions, v.required_revisions)
        for v in values
        if v.source_undefined_reason is None
    ]
    complete = [v.complete for v in values if v.complete is not None]
    sr = [v.source_undefined_reason for v in values if v.source_undefined_reason is not None]
    cr = [v.complete_undefined_reason for v in values if v.complete is None]
    return PrefixSummary(
        values[0].stage,
        values[0].cutoff,
        len(values),
        len(source),
        len(sr),
        _reasons(meter, sr),
        len(source),
        _mean(meter, source),
        None if source else "NO_DEFINED_SOURCE",
        len(complete),
        len(cr),
        _reasons(meter, cr),
        len(complete),
        meter.rational(sum(complete), len(complete)) if complete else None,
        None if complete else "NO_DEFINED_COMPLETE",
    )


def _count_loss(meter, values, before_field, lost_field):
    meter.reserve(len(values) * 32 + 20, len(values) * 24 + 128)
    before = sum(getattr(v, before_field) for v in values)
    lost = sum(getattr(v, lost_field) for v in values)
    eligible = [v for v in values if getattr(v, before_field)]
    ratios = [meter.rational(getattr(v, lost_field), getattr(v, before_field)) for v in eligible]
    return CountLossSummary(
        lost,
        before,
        len(eligible),
        len(values) - len(eligible),
        meter.rational(lost, before) if before else None,
        _mean(meter, ratios),
        None if eligible else "NO_ELIGIBLE_BEFORE",
    )


def _transition_summary(meter, values):
    meter.reserve(len(values) * 40 + 50, len(values) * 48 + 256)
    meaningful = [v for v in values if v.complete_before is not None]
    eligible = [v for v in meaningful if v.complete_before]
    lost = sum(not v.complete_after for v in eligible)
    defined = [v for v in values if v.source_before is not None]
    undefined = [v.source_undefined_reason for v in values if v.source_before is None]
    differences = [_add(meter, v.source_before, v.source_after, subtract=True) for v in defined]
    return TransitionSummary(
        values[0].source,
        values[0].target,
        len(values),
        len(meaningful),
        len(values) - len(meaningful),
        (("NO_GOLD_REQUIREMENTS", len(values) - len(meaningful)),)
        if len(values) != len(meaningful)
        else (),
        len(eligible),
        len(meaningful) - len(eligible),
        lost,
        meter.rational(lost, len(eligible)) if eligible else None,
        None if eligible else "NO_ELIGIBLE_COMPLETED",
        len(defined),
        len(undefined),
        _reasons(meter, undefined),
        len(defined),
        _mean(meter, differences),
        None if defined else "NO_DEFINED_SOURCE",
        _count_loss(meter, values, "requirements_before", "requirements_lost"),
        _count_loss(meter, values, "alternatives_before", "alternatives_lost"),
    )


def _identity(meter, payload):
    meter.reserve(1, 32)
    digest = hashlib.sha256()
    size = 0

    def emit(data):
        nonlocal size
        meter.reserve(len(data) * 2 + 1, len(data) * 2)
        size += len(data)
        if size > 1048576:
            raise ValueError
        digest.update(data)

    def walk(value):
        meter.reserve(16)
        if value is None:
            emit(b"null")
        elif type(value) is bool:
            emit(b"true" if value else b"false")
        elif type(value) is int:
            meter.integer(value)
            if value < 0:
                raise ValueError
            bits = value.bit_length() + 2
            meter.reserve(bits * bits + bits, bits * 2)
            emit(str(value).encode("ascii"))
        elif type(value) is str:
            meter.reserve(12 * len(value) + 4, 12 * len(value) + 4)
            emit(json.dumps(value, ensure_ascii=True, separators=(",", ":")).encode("ascii"))
        elif type(value) is tuple:
            emit(b"[")
            for index, item in enumerate(value):
                if index:
                    emit(b",")
                walk(item)
            emit(b"]")
        elif type(value) is Ratio:
            emit(b'{"num":')
            for index, integer in enumerate((value.numerator, value.denominator)):
                if index:
                    emit(b',"den":')
                meter.integer(integer)
                bits = integer.bit_length() + 2
                meter.reserve(bits * bits + bits, bits)
                walk(str(integer))
            emit(b"}")
        elif type(value) in (
            PrefixCase,
            LossCase,
            CaseSummary,
            PrefixSummary,
            CountLossSummary,
            TransitionSummary,
        ):
            emit(b"{")
            meter.reserve(64, 256)
            for index, item in enumerate(fields(value)):
                if index:
                    emit(b",")
                walk(item.name)
                emit(b":")
                walk(getattr(value, item.name))
            emit(b"}")
        else:
            raise ValueError

    emit(b"slaif-declared-cohort-metrics-v1\n")
    walk(payload)
    meter.reserve(128, 135)
    return "sha256:" + digest.hexdigest()


def _aggregate(cases, deadline_ms, max_work, max_payload, start):
    meter = _Meter(start, deadline_ms, max_work, max_payload)
    _tuple(meter, cases, 1, 256)
    # Validate IDs and tuple shapes before comparisons, hashing or serialization.
    for pair in cases:
        _tuple(meter, pair, 2, 2)
        _identifier(meter, pair[0])
        meter.reserve(1)
        if type(pair[1]) is not geometry.Diagnosis:
            raise ValueError
    previous = None
    meter.reserve(1, 8)
    summaries = []
    occurrences = 0
    for case_id, diagnosis in cases:
        meter.reserve(2 * len(case_id) + (len(previous) if previous is not None else 0) + 2)
        if previous is not None and previous >= case_id:
            raise ValueError
        previous = case_id
        full, prefixes, losses = _diagnosis(meter, diagnosis)
        meter.reserve(4)
        occurrences += len(full[0][5])
        if occurrences > 512:
            raise ValueError
        meter.reserve(32, 256)
        case_prefixes = tuple(
            _prefix_case(meter, stage, record)
            for stage, record in zip(diagnosis.prefixes, prefixes)
        )
        case_losses = tuple(
            _loss_case(meter, full[a], full[b], loss, a, b) for (a, b), loss in zip(_EDGES, losses)
        )
        summaries.append(CaseSummary(case_id, diagnosis.invocation_id, case_prefixes, case_losses))
    meter.reserve(len(summaries) * 32 + 40, len(summaries) * 120 + 256)
    cases_out = tuple(summaries)
    prefix_out = tuple(
        _prefix_summary(meter, tuple(c.prefixes[i] for c in cases_out)) for i in range(6)
    )
    loss_out = tuple(
        _transition_summary(meter, tuple(c.losses[i] for c in cases_out)) for i in range(7)
    )
    meter.reserve(64, 256)
    checkpoint_work, checkpoint_payload = meter.work, meter.payload
    payload = (
        "declared-cohort-metrics-v1",
        "UNVERIFIED",
        "SUPPLIED_DECLARED_GEOMETRY_ONLY",
        "NOT_ATTESTED",
        "NOT_QUALIFIED",
        "NO_EXPLICIT_CHUNK_RELEVANCE_MAPPING",
        max_work,
        max_payload,
        checkpoint_work,
        checkpoint_payload,
        cases_out,
        prefix_out,
        loss_out,
    )
    identity = _identity(meter, payload)
    meter.reserve(32, 160)
    result = Report(
        len(cases_out),
        cases_out,
        prefix_out,
        loss_out,
        identity,
        checkpoint_work,
        checkpoint_payload,
        meter.work,
        meter.payload,
        max_work,
        max_payload,
    )
    meter.check()
    return result


def aggregate(cases, *, deadline_ms=10000, max_work=134217728, max_payload=268435456):
    """Aggregate an entire supplied cohort, refusing any malformed member."""
    try:
        start = time.monotonic()
        return _aggregate(cases, deadline_ms, max_work, max_payload, start)
    except Exception:
        raise CohortMetricsError("cohort metrics refused") from None
