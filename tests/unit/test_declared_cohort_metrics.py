"""Hand-oracle checks over declared geometry, with no source execution."""

import dataclasses
from fractions import Fraction
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from slaif_raggedized_helper import declared_cohort_metrics as subject
from slaif_raggedized_helper import declared_stage_geometry as geometry


ROOT = Path(__file__).parents[2]
ORACLE = json.loads((ROOT / "docs/parallel/declared-cohort-metrics-oracle.json").read_text())
BASE = json.loads(
    json.loads((ROOT / "docs/parallel/declared-span-support-oracle.json").read_text())[
        "dataset_ascii"
    ]
)


def ident(value):
    return "sha256:" + format(value, "064x")


def fixture_data():
    obj = json.loads(json.dumps(BASE))
    template = obj["cases"][0]
    gold = {5, 10, 15, 30, 90, 135}

    def atom(number):
        return dict(
            revision_id=ident(1000 + number),
            extraction_id=ident(999),
            block_id=f"x{number:03}",
            start=0,
            end=1,
            text_sha256="a" * 64,
        )

    def req(name, *numbers):
        return dict(
            requirement_id=name, grade=1, alternatives=[[atom(number)] for number in numbers]
        )

    specs = (
        ("A", [req("a", 10)]),
        ("B", [req("b1", 5), req("b2", 30), req("b3", 90)]),
        ("C", [req("c", 15, 135)]),
        ("D", []),
    )
    cases = []
    for label, requirements in specs:
        case = json.loads(json.dumps(template))
        case["case_id"] = label
        case["family_id"] = "family" + label
        case["requirements"] = requirements
        if not requirements:
            case["answerability"] = "unknown"
            case["acceptable_facts"] = []
        cases.append(case)
    obj["cases"] = cases
    data = json.dumps(obj, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode()
    rows = tuple(
        (
            ident(n),
            ident(1000 + n if n in gold else (1 if n <= 70 else 2)),
            ident(999),
            ((f"x{n:03}", 0, 1),),
        )
        for n in range(1, 141)
    )
    all_rows = tuple(range(140))
    selected = tuple(range(60)) + tuple(range(70, 130))
    dense = tuple(range(60))
    lexical = tuple(range(30)) + tuple(range(70, 100))
    fusion = tuple(range(60)) + tuple(range(70, 100))
    stages = tuple(
        zip(
            geometry._NAMES,
            (
                all_rows,
                all_rows,
                selected,
                dense,
                all_rows,
                all_rows,
                selected,
                lexical,
                fusion,
                dense,
            ),
        )
    )
    return data, rows, stages


@pytest.fixture(scope="module")
def cohort():
    data, rows, stages = fixture_data()
    return tuple((case, geometry.diagnose(data, case, rows, stages)) for case in "ABCD")


def rational(value):
    return None if value is None else Fraction(value.numerator, value.denominator)


def test_independent_four_case_oracle(cohort):
    report = subject.aggregate(cohort)
    assert report.case_count == 4
    for index, key in enumerate(
        ("20_all", "60_dense_fusion", "20_all", "60_lexical", "20_all", "60_dense_fusion")
    ):
        expected = ORACLE["prefixes"][key]
        actual = report.prefixes[index]
        assert rational(actual.source_macro) == Fraction(expected["source_macro"])
        assert rational(actual.complete_rate) == Fraction(expected["completion_macro"])
        assert (actual.source_defined, actual.source_undefined, actual.source_denominator) == (
            2,
            2,
            2,
        )
        assert (
            actual.complete_defined,
            actual.complete_undefined,
            actual.complete_denominator,
        ) == (3, 1, 3)
        assert dict(actual.source_reasons) == {
            "NO_GOLD_SOURCES": 1,
            "AMBIGUOUS_ALTERNATIVE_SOURCE_UNIVERSE": 1,
        }
        for case, case_result in zip("ABCD", report.cases):
            pref = case_result.prefixes[index]
            recall, complete = expected[case]
            assert (
                Fraction(pref.covered_revisions, pref.required_revisions)
                if pref.required_revisions
                else None
            ) == (Fraction(recall) if recall else None)
            assert pref.complete is complete
    for actual, expected in zip(report.transitions, ORACLE["transition_cohort_root_d0"]):
        assert actual.source + "->" + actual.target == expected["transition"]
        assert rational(actual.complete_rate) == Fraction(expected["complete"])
        assert rational(actual.source_loss) == Fraction(expected["source_macro_loss"])
        assert (
            actual.complete_defined,
            actual.complete_undefined,
            actual.complete_eligible,
            actual.complete_incomplete_before,
        ) == (3, 1, 3, 0)
        assert (actual.source_defined, actual.source_undefined, actual.source_denominator) == (
            2,
            2,
            2,
        )
        for kind in ("requirements", "alternatives"):
            result = getattr(actual, kind)
            witness = expected[kind]
            lost, before = map(int, witness["lost_before"].split("/"))
            assert (result.lost, result.before, result.eligible_cases, result.undefined_cases) == (
                lost,
                before,
                3,
                1,
            )
            assert rational(result.pooled) == Fraction(witness["pooled"])
            assert rational(result.macro) == Fraction(witness["case_macro"])
    assert report.identity == subject.aggregate(cohort).identity
    assert report.checkpoint_work < report.final_work
    assert report.checkpoint_payload < report.final_payload
    assert report.source_binding == "UNVERIFIED"
    assert report.qualification == "NOT_QUALIFIED"
    assert "A" not in repr(report)


def test_undefined_only_and_or(cohort):
    report = subject.aggregate((cohort[3],))
    for prefix in report.prefixes:
        assert prefix.source_macro is None and prefix.complete_rate is None
        assert prefix.source_empty_reason == "NO_DEFINED_SOURCE"
    for item in report.transitions:
        assert item.complete_rate is None and item.complete_empty_reason == "NO_ELIGIBLE_COMPLETED"
        assert item.source_loss is None and item.source_empty_reason == "NO_DEFINED_SOURCE"
        assert item.requirements.macro is None and item.requirements.pooled is None
        assert item.alternatives.undefined_reason == "NO_ELIGIBLE_BEFORE"
    report = subject.aggregate((cohort[2],))
    assert report.prefixes[0].source_macro is None
    assert rational(report.prefixes[0].complete_rate) == 1
    assert rational(report.transitions[1].alternatives.pooled) == Fraction(1, 2)


def test_256_and_257(cohort):
    diagnosis = cohort[3][1]
    cases = tuple((f"case{i:03}", diagnosis) for i in range(256))
    assert subject.aggregate(cases).case_count == 256
    with pytest.raises(subject.CohortMetricsError, match="^cohort metrics refused$"):
        subject.aggregate(cases + (("case256", diagnosis),))


def replace_stage(diagnosis, index, stage):
    stages = list(diagnosis.stages)
    stages[index] = stage
    return dataclasses.replace(diagnosis, stages=tuple(stages))


@pytest.mark.parametrize(
    "mutation",
    (
        "duplicate",
        "unsorted",
        "bool",
        "tuple_subclass",
        "diagnosis_subclass",
        "nan",
        "huge",
        "nested",
        "universe",
        "gain",
        "flag",
        "fingerprint",
    ),
)
def test_refusals(cohort, mutation):
    diagnosis = cohort[0][1]
    stage = diagnosis.stages[0]
    if mutation == "duplicate":
        cases = (cohort[0], cohort[0])
    elif mutation == "unsorted":
        cases = (cohort[1], cohort[0])
    elif mutation == "bool":
        cases = (("A", replace_stage(diagnosis, 0, dataclasses.replace(stage, row_count=True))),)
    elif mutation == "tuple_subclass":

        class T(tuple):
            pass

        cases = T((cohort[0],))
    elif mutation == "diagnosis_subclass":

        class D(geometry.Diagnosis):
            pass

        cases = (
            (
                "A",
                D(
                    diagnosis.invocation_id,
                    diagnosis.stages,
                    diagnosis.prefixes,
                    diagnosis.transitions,
                    diagnosis.work,
                    diagnosis.serialization_budget,
                ),
            ),
        )
    elif mutation == "nan":
        comp = dataclasses.replace(stage.completion, recall=float("nan"))
        cases = (("A", replace_stage(diagnosis, 0, dataclasses.replace(stage, completion=comp))),)
    elif mutation == "huge":
        cases = (
            ("A", replace_stage(diagnosis, 0, dataclasses.replace(stage, row_count=1 << 9000))),
        )
    elif mutation == "nested":
        comp = dataclasses.replace(stage.completion, atom_occurrences=(("a", 0, 0),))
        cases = (("A", replace_stage(diagnosis, 0, dataclasses.replace(stage, completion=comp))),)
    elif mutation == "universe":
        comp = dataclasses.replace(
            stage.completion, required_revisions=(ident(99999),), covered_revisions=(ident(99999),)
        )
        cases = (("A", replace_stage(diagnosis, 0, dataclasses.replace(stage, completion=comp))),)
    elif mutation == "gain":
        transitions = list(diagnosis.transitions)
        transitions[0] = dataclasses.replace(transitions[0], gained_requirements=("a",))
        cases = (("A", dataclasses.replace(diagnosis, transitions=tuple(transitions))),)
    elif mutation == "flag":
        req = stage.coverage.requirements[0]
        req = dataclasses.replace(req, covered=not req.covered)
        cov = dataclasses.replace(stage.coverage, requirements=(req,))
        cases = (("A", replace_stage(diagnosis, 0, dataclasses.replace(stage, coverage=cov))),)
    else:
        cases = (("A", dataclasses.replace(diagnosis, invocation_id="bad")),)
    with pytest.raises(subject.CohortMetricsError, match="^cohort metrics refused$"):
        subject.aggregate(cases)


def test_budget_deadline_and_interrupt(cohort):
    with patch.object(subject, "_identity", side_effect=AssertionError("emitted")) as emit:
        for kw in ({"max_work": 0}, {"max_payload": 0}, {"max_work": 1}, {"max_payload": 1}):
            with pytest.raises(subject.CohortMetricsError):
                subject.aggregate(cohort, **kw)
        emit.assert_not_called()
    with patch.object(subject.time, "monotonic", side_effect=(0, 20)):
        with pytest.raises(subject.CohortMetricsError):
            subject.aggregate(cohort, deadline_ms=1)
    marker = KeyboardInterrupt("marker")
    with patch.object(subject.time, "monotonic", side_effect=marker):
        with pytest.raises(KeyboardInterrupt) as caught:
            subject.aggregate(cohort)
    assert caught.value is marker
    for kw in (
        {"deadline_ms": True},
        {"max_work": True},
        {"max_payload": -1},
        {"max_work": 134217729},
    ):
        with pytest.raises(subject.CohortMetricsError):
            subject.aggregate(cohort, **kw)


def test_immutable_private_output(cohort):
    before = repr(cohort)
    result = subject.aggregate(cohort)
    assert repr(cohort) == before
    with pytest.raises(dataclasses.FrozenInstanceError):
        result.case_count = 0
    assert type(result.cases) is tuple and type(result.prefixes) is tuple
    assert not hasattr(result.cases[0], "requirements")
    assert not hasattr(result.cases[0].prefixes[0], "covered_revision_ids")
    assert "sha256:" not in repr(result)


def test_private_fields_and_borrowed_unchanged(cohort):
    before = tuple(dataclasses.astuple(diagnosis) for _, diagnosis in cohort)
    report = subject.aggregate(cohort)
    assert before == tuple(dataclasses.astuple(diagnosis) for _, diagnosis in cohort)
    exposed = repr(dataclasses.astuple(report))
    for _, diagnosis in cohort:
        for stage in diagnosis.stages:
            for atom, _ in stage.completion.atom_coverage:
                assert atom not in exposed
            for revision in stage.completion.required_revisions:
                assert revision not in exposed
            for requirement in stage.coverage.requirements:
                assert repr(requirement.requirement_id) not in exposed
    with pytest.raises((TypeError, ValueError)):
        dataclasses.replace(cohort[0][1], source_binding="VERIFIED")


def test_later_loss_and_universe_inconsistency(cohort):
    diagnosis = cohort[1][1]
    transition = diagnosis.transitions[2]
    changed = dataclasses.replace(transition, lost_requirements=())
    transitions = list(diagnosis.transitions)
    transitions[2] = changed
    with pytest.raises(subject.CohortMetricsError):
        subject.aggregate((("B", dataclasses.replace(diagnosis, transitions=tuple(transitions))),))
    stage = diagnosis.stages[2]
    comp = dataclasses.replace(stage.completion, required_revisions=())
    with pytest.raises(subject.CohortMetricsError):
        subject.aggregate(
            (("B", replace_stage(diagnosis, 2, dataclasses.replace(stage, completion=comp))),)
        )


def test_long_ids_and_alternative_losses():
    data, rows, stages = fixture_data()
    dataset = json.loads(data)
    case = dataset["cases"][2]
    case["requirements"][0]["requirement_id"] = "r" * 128
    dataset["cases"] = [case]
    encoded = json.dumps(dataset, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode()
    diagnosis = geometry.diagnose(encoded, "C", rows, stages)
    report = subject.aggregate((("C", diagnosis),))
    assert report.transitions[1].alternatives.lost == 1
    assert rational(report.transitions[1].alternatives.macro) == Fraction(1, 2)
    assert report.transitions[1].requirements.lost == 0
    assert "r" * 128 not in repr(dataclasses.astuple(report))


def test_bounded_markers_and_oversized_caps(cohort):
    diagnosis = dataclasses.replace(cohort[0][1])
    object.__setattr__(diagnosis, "source_binding", "X" * 100000)
    with pytest.raises(subject.CohortMetricsError):
        subject.aggregate((("A", diagnosis),))
    stage = cohort[0][1].stages[0]
    completion = dataclasses.replace(stage.completion)
    object.__setattr__(completion, "metric", "X" * 100000)
    with pytest.raises(subject.CohortMetricsError):
        subject.aggregate(
            (
                (
                    "A",
                    replace_stage(
                        cohort[0][1], 0, dataclasses.replace(stage, completion=completion)
                    ),
                ),
            )
        )
    for name in ("max_work", "max_payload", "deadline_ms"):
        with pytest.raises(subject.CohortMetricsError):
            subject.aggregate(cohort, **{name: 1 << 9000})


def test_charged_comparison_boundary():
    values = tuple(ident(i) for i in (1, 3, 5))
    meter = subject._Meter(0, 10000, 0, 10000)
    with patch.object(subject.time, "monotonic", return_value=1):
        with pytest.raises(ValueError):
            subject._subset(meter, values, values)
    assert meter.work == 0
    meter = subject._Meter(0, 10000, 100000, 10000)
    with patch.object(subject.time, "monotonic", return_value=1):
        assert subject._subset(meter, (ident(1), ident(5)), values)
        assert not subject._subset(meter, (ident(1), ident(4)), values)
        assert subject._subset(meter, (), values)
        assert not subject._subset(meter, (ident(1),), ())


def _small_diagnosis(case, ordinals):
    data, rows, _ = fixture_data()
    stages = tuple((name, ordinals) for name in geometry._NAMES)
    return geometry.diagnose(data, case, rows, stages)


def _replace_prefix(diagnosis, index, stage):
    prefixes = list(diagnosis.prefixes)
    prefixes[index] = stage
    return dataclasses.replace(diagnosis, prefixes=tuple(prefixes))


def test_zero_rows_defined_zero_and_no_gold(cohort):
    empty_gold = _small_diagnosis("A", ())
    empty_no_gold = _small_diagnosis("D", ())
    report = subject.aggregate((("A", empty_gold), cohort[1], ("D", empty_no_gold)))
    assert rational(report.prefixes[0].source_macro) == Fraction(1, 6)
    assert rational(report.prefixes[0].complete_rate) == 0
    assert (report.prefixes[0].source_defined, report.prefixes[0].source_undefined) == (2, 1)
    assert report.cases[0].prefixes[0].complete is False
    assert report.cases[2].prefixes[0].complete is None

    hit = _small_diagnosis("A", (9,))
    stage = hit.stages[0]
    cov = dataclasses.replace(stage.coverage, k=1, returned_count=0)
    forged = dataclasses.replace(stage, row_count=0, cutoff=1, coverage=cov)
    with pytest.raises(subject.CohortMetricsError):
        subject.aggregate((("A", replace_stage(hit, 0, forged)),))


def test_short_returned_prefix_must_match():
    hit = _small_diagnosis("A", (9,))
    empty = _small_diagnosis("A", ())
    prefix = hit.prefixes[0]
    empty_cov = dataclasses.replace(empty.prefixes[0].coverage, returned_count=1)
    forged = dataclasses.replace(
        prefix, coverage=empty_cov, completion=empty.prefixes[0].completion
    )
    with pytest.raises(subject.CohortMetricsError):
        subject.aggregate((("A", _replace_prefix(hit, 0, forged)),))


@pytest.mark.parametrize(
    "kind", ("equal_sets", "count_increase", "equal_count", "fusion_count", "fusion_containment")
)
def test_impossible_stage_relations(cohort, kind):
    diagnosis = cohort[0][1]
    if kind == "equal_sets":
        index = 1
        stage = diagnosis.stages[index]
        # A different admitted row count cannot represent the equal eligible/ranked sets.
        cov = dataclasses.replace(stage.coverage, k=139, returned_count=139)
        stage = dataclasses.replace(stage, cutoff=139, row_count=139, coverage=cov)
    elif kind == "count_increase":
        index = 2
        stage = diagnosis.stages[index]
        cov = dataclasses.replace(stage.coverage, k=141, returned_count=141)
        stage = dataclasses.replace(stage, cutoff=141, row_count=141, coverage=cov)
    elif kind == "equal_count":
        # A zero-evidence selected set cannot equal the equally sized ranked set with evidence.
        hit = _small_diagnosis("A", (9,))
        empty = _small_diagnosis("A", ())
        diagnosis, index = hit, 2
        stage = hit.stages[index]
        cov = dataclasses.replace(empty.stages[index].coverage, returned_count=1)
        stage = dataclasses.replace(stage, coverage=cov, completion=empty.stages[index].completion)
    elif kind == "fusion_count":
        index = 8
        stage = diagnosis.stages[index]
        cov = dataclasses.replace(stage.coverage, k=59, returned_count=59)
        stage = dataclasses.replace(stage, cutoff=59, row_count=59, coverage=cov)
    else:
        # Returned evidence cannot exceed its purported fusion input.
        hit = _small_diagnosis("A", (9,))
        empty = _small_diagnosis("A", ())
        diagnosis, index = hit, 8
        stage = hit.stages[index]
        cov = dataclasses.replace(empty.stages[index].coverage, returned_count=1)
        stage = dataclasses.replace(stage, coverage=cov, completion=empty.stages[index].completion)
    with pytest.raises(subject.CohortMetricsError):
        subject.aggregate((("A", replace_stage(diagnosis, index, stage)),))


def test_complementary_fragments_are_valid_fusion():
    data, _, _ = fixture_data()
    dataset = json.loads(data)
    case = dataset["cases"][0]
    case["requirements"][0]["alternatives"][0][0]["end"] = 2
    dataset["cases"] = [case]
    data = json.dumps(dataset, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode()
    rows = (
        (ident(1), ident(1010), ident(999), (("x010", 0, 1),)),
        (ident(2), ident(1010), ident(999), (("x010", 1, 2),)),
    )
    both = (0, 1)
    ordinals = (both, both, both, (0,), both, both, both, (1,), both, both)
    stages = tuple(zip(geometry._NAMES, ordinals))
    diagnosis = geometry.diagnose(data, "A", rows, stages)
    assert diagnosis.stages[3].coverage.complete_requirements is False
    assert diagnosis.stages[7].coverage.complete_requirements is False
    assert diagnosis.stages[8].coverage.complete_requirements is True
    result = subject.aggregate((("A", diagnosis),))
    assert rational(result.prefixes[0].complete_rate) == 0
    assert rational(result.prefixes[4].complete_rate) == 1


@pytest.fixture(scope="module")
def one_row_hit_and_miss():
    return _small_diagnosis("A", (9,)), _small_diagnosis("A", (0,))


def _with_evidence(stage, other):
    return dataclasses.replace(stage, coverage=other.coverage, completion=other.completion)


def test_zero_row_forgery_with_coherent_stage_relations(one_row_hit_and_miss):
    hit, _ = one_row_hit_and_miss
    stages = tuple(
        dataclasses.replace(
            stage,
            row_count=0,
            cutoff=1,
            coverage=dataclasses.replace(stage.coverage, k=1, returned_count=0),
        )
        for stage in hit.stages
    )
    prefixes = tuple(
        dataclasses.replace(
            stage, row_count=0, coverage=dataclasses.replace(stage.coverage, returned_count=0)
        )
        for stage in hit.prefixes
    )
    forged = dataclasses.replace(hit, stages=stages, prefixes=prefixes)
    with pytest.raises(subject.CohortMetricsError):
        subject.aggregate((("A", forged),))


def test_equal_cardinality_removal_with_coherent_losses(one_row_hit_and_miss):
    hit, miss = one_row_hit_and_miss
    stages = list(hit.stages)
    for index in (2, 3):
        stages[index] = _with_evidence(stages[index], miss.stages[index])
    prefixes = list(hit.prefixes)
    for index in (0, 1):
        prefixes[index] = _with_evidence(prefixes[index], miss.prefixes[index])
    transitions = list(hit.transitions)
    transitions[1] = dataclasses.replace(
        transitions[1], lost_requirements=("a",), lost_alternatives=(("a", 0),)
    )
    forged = dataclasses.replace(
        hit, stages=tuple(stages), prefixes=tuple(prefixes), transitions=tuple(transitions)
    )
    with pytest.raises(subject.CohortMetricsError):
        subject.aggregate((("A", forged),))


def test_fusion_containment_with_coherent_fusion_loss(one_row_hit_and_miss):
    hit, miss = one_row_hit_and_miss
    stages = list(hit.stages)
    for index in (8, 9):
        stages[index] = _with_evidence(stages[index], miss.stages[index])
    prefixes = list(hit.prefixes)
    for index in (4, 5):
        prefixes[index] = _with_evidence(prefixes[index], miss.prefixes[index])
    forged = dataclasses.replace(hit, stages=tuple(stages), prefixes=tuple(prefixes))
    with pytest.raises(subject.CohortMetricsError):
        subject.aggregate((("A", forged),))
