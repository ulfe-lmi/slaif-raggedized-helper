"""Controlled unit evidence; these delegates do not prove actual source composition."""

import dataclasses
import hashlib
import json

import pytest

import test_source_cohort_runner as fixture
from slaif_raggedized_helper import evaluation_program as program
from slaif_raggedized_helper import (
    raw_snapshot_catalog,
    source_bound_ranking,
    supplied_rank_metrics,
)
from slaif_raggedized_helper import text_evaluation_dataset


def _origin_assignment(name):
    if name == "slaif_raggedized_helper" or name.startswith("slaif_raggedized_helper."):
        return "src"
    if name.startswith("test_"):
        return "tests/unit"
    return None


def _local_origin_records():
    import sys

    return tuple(
        (name, getattr(module, "__file__", None))
        for name, module in tuple(sys.modules.items())
        if _origin_assignment(name) is not None
    )


def _check_local_origins(records):
    """Strict local-origin provenance over bounded (name, __file__) metadata.

    Every loaded slaif_raggedized_helper package/module must have a real
    local origin resolving under the assigned root/src and every loaded
    test_ module under root/tests/unit; foreign, missing, non-file or
    resolved-escaping origins fail.  This certifies provenance only, not
    total source bytes, RSS or read cost: no global extent sum is applied
    here.  Finite focused execution/readset budgets (the 2 MiB dynamic
    limit of the separately frozen parallel/evaluation-core check
    proposal) bind only to that frozen focused readset, never to an
    arbitrary full default pytest session collecting unrelated tests.
    """
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]
    for name, origin in records:
        assert origin is not None, f"origin missing for {name!r}"
        resolved = Path(origin).resolve()
        assert resolved.is_file(), f"not a real file origin for {name!r}"
        assigned = root / _origin_assignment(name)
        assert resolved.is_relative_to(assigned), f"unsafe origin for {name!r}"


def test_local_program_origins():
    _check_local_origins(_local_origin_records())


def test_origin_metadata_focused_local_passes():
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]
    focused = (
        ("slaif_raggedized_helper", str(root / "src" / "slaif_raggedized_helper" / "__init__.py")),
        ("slaif_raggedized_helper.evaluation_program", str(program.__file__)),
        ("test_evaluation_program", str(__file__)),
        ("test_source_cohort_runner", str(fixture.__file__)),
    )
    _check_local_origins(focused)


def test_origin_metadata_broader_local_session_passes_past_focused_sum(monkeypatch):
    import os
    from pathlib import Path

    own = Path(__file__).resolve()
    other = Path(fixture.__file__).resolve()
    assert own != other
    big = 3 * 1024 * 1024
    sizes = {str(own): big, str(other): big}
    real_stat = Path.stat

    def fake_stat(self, *args, **kwargs):
        result = real_stat(self, *args, **kwargs)
        size = sizes.get(str(self))
        if size is None:
            return result
        values = list(result)
        values[6] = size
        return os.stat_result(values)

    monkeypatch.setattr(Path, "stat", fake_stat)
    records = (
        ("test_evaluation_program", str(own)),
        ("test_source_cohort_runner", str(other)),
    )
    unique = {Path(origin).resolve() for _name, origin in records}
    assert len(unique) == 2
    assert sum(path.stat().st_size for path in unique) > 2 * 1024 * 1024
    _check_local_origins(records)


def test_origin_metadata_foreign_package_origin_fails():
    foreign = (("slaif_raggedized_helper.evaluation_program", str(fixture.__file__)),)
    with pytest.raises(AssertionError):
        _check_local_origins(foreign)


def test_origin_metadata_foreign_test_origin_fails():
    foreign = (("test_evaluation_program", str(program.__file__)),)
    with pytest.raises(AssertionError):
        _check_local_origins(foreign)


def test_origin_metadata_missing_or_nonfile_origin_fails():
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]
    for record in (
        ("slaif_raggedized_helper.evaluation_program", None),
        ("test_evaluation_program", None),
        (
            "slaif_raggedized_helper",
            str(root / "src" / "slaif_raggedized_helper" / "absent_module.py"),
        ),
        ("test_evaluation_program", str(root / "tests" / "unit")),
    ):
        with pytest.raises(AssertionError):
            _check_local_origins((record,))


def test_origin_metadata_resolved_path_escape_fails():
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]
    escapes = (
        (
            "slaif_raggedized_helper.evaluation_program",
            str(root / "src" / "slaif_raggedized_helper" / ".." / ".." / "tests" / "unit"
                / "test_source_cohort_runner.py"),
        ),
        (
            "test_evaluation_program",
            str(root / "tests" / "unit" / ".." / ".." / "src" / "slaif_raggedized_helper"
                / "evaluation_program.py"),
        ),
    )
    for record in escapes:
        with pytest.raises(AssertionError):
            _check_local_origins((record,))


def setup_case(monkeypatch, count=1, judgments=None):
    args, kwargs, calls, captured = fixture.controlled(monkeypatch, count)
    dataset = text_evaluation_dataset.admit(args[4])
    catalog_id = "sha256:" + "c" * 64
    if judgments is None:
        judgments = tuple(program.Judgments(case_id, ()) for case_id in args[5].case_ids)
    plan = program.Plan(
        "plan",
        dataset.dataset_id,
        dataset.split_id,
        captured.pointer.snapshot_id,
        captured.pointer.generation,
        catalog_id,
        "protocol",
        "UNJUDGED_AS_ZERO_DIAGNOSTIC",
        "EXPLICIT_CHUNK_IDS_ONLY",
        (20, 60),
        judgments,
    )
    budget = program.GradeBudget(*program._MAX_BUDGET)

    def catalog(*a, **kw):
        calls.append("catalog")
        return raw_snapshot_catalog.Catalog(
            captured.pointer.snapshot_id, b"", b"", (), (), (), (), catalog_id
        )

    def bind(
        _originals,
        _derived,
        _root,
        snapshot,
        expected_catalog,
        ids,
        *,
        grants,
        restrictions,
        deadline_ms,
    ):
        calls.append("grade_bind")
        authority = hashlib.sha256(
            fixture.wire(
                [
                    grants.model_dump(mode="json"),
                    None if restrictions is None else restrictions.model_dump(mode="json"),
                ]
            )
        ).hexdigest()
        marker = "sha256:" + "d" * 64
        rows = tuple(
            source_bound_ranking.BoundRow(
                i,
                marker,
                ident,
                marker,
                marker,
                "d" * 64,
                "d" * 64,
                "d" * 64,
                "a" * 64,
                (source_bound_ranking.BoundFragment(marker, 0, 1, "b" * 64),),
            )
            for i, ident in enumerate(ids)
        )
        return source_bound_ranking.BoundRanking(
            marker,
            snapshot,
            expected_catalog,
            authority,
            rows,
            len(rows),
            len(rows),
            "ORIGINALS_REVALIDATED_AT_BIND_TIME" if rows else "NO_SELECTED_SOURCE_VALIDATED",
        )

    monkeypatch.setattr(raw_snapshot_catalog, "load_catalog", catalog)
    monkeypatch.setattr(source_bound_ranking, "bind", bind)
    return args, kwargs, calls, captured, plan, budget


def invoke(args, kwargs, plan, budget):
    return program.run_evaluation(*args, **kwargs, plan=plan, grade_budget=budget)


def test_two_cases_empty_and_unretrieved_positive(monkeypatch):
    ident = "sha256:" + "1" * 64
    judgments = (program.Judgments("case000", ()), program.Judgments("case001", ((ident, 2),)))
    args, kwargs, calls, _, plan, budget = setup_case(monkeypatch, 2, judgments)
    aggregate = supplied_rank_metrics.aggregate
    seen = []

    def checked(*a, **kw):
        seen.append(a[0])
        return aggregate(*a, **kw)

    monkeypatch.setattr(supplied_rank_metrics, "aggregate", checked)
    report = invoke(args, kwargs, plan, budget)
    obj = json.loads(report.identity_payload)
    assert len(seen) == 3 and all(len(cases) == 2 for cases in seen)
    assert calls.count("producer") == calls.count("binder") == calls.count("grade_bind") == 2
    assert calls.count("pin") == 9 and calls.count("catalog") == 1
    assert all(
        v["defined_queries"] == 1 and v["undefined_empty_gold_queries"] == 1
        for v in obj["variants"].values()
    )
    assert (
        report.identity
        == "sha256:"
        + hashlib.sha256(
            b"slaif-graded-evaluation-program-v1\n" + report.identity_payload
        ).hexdigest()
    )
    assert b"Synthetic question" not in report.identity_payload
    assert ident.encode() not in report.identity_payload
    assert "case000" not in repr(report)


@pytest.mark.parametrize(
    "change",
    [
        lambda p: dataclasses.replace(p, dataset_id="sha256:" + "0" * 64),
        lambda p: dataclasses.replace(p, split_id="sha256:" + "0" * 64),
        lambda p: dataclasses.replace(p, generation=True),
        lambda p: dataclasses.replace(p, cutoffs=(20, 20, 60)),
        lambda p: dataclasses.replace(p, judgments=p.judgments[:-1]),
        lambda p: dataclasses.replace(
            p,
            judgments=(
                p.judgments[0],
                program.Judgments("case001", (("sha256:" + "1" * 64, True),)),
            ),
        ),
    ],
)
def test_later_invalid_declarations_precede_pin(monkeypatch, change):
    args, kwargs, calls, _, plan, budget = setup_case(monkeypatch, 2)
    with pytest.raises(program.EvaluationError) as exc:
        invoke(args, kwargs, change(plan), budget)
    assert str(exc.value) == "evaluation program refused"
    assert exc.value.progress is None and calls == []


def test_wrong_snapshot_and_catalog_refuse_before_producer(monkeypatch):
    args, kwargs, calls, _, plan, budget = setup_case(monkeypatch)
    plan = dataclasses.replace(plan, snapshot_id="sha256:" + "0" * 64)
    with pytest.raises(program.EvaluationError) as exc:
        invoke(args, kwargs, plan, budget)
    assert exc.value.progress.phase == "CATALOG"
    assert "producer" not in calls


def test_grade_refusal_has_no_subset_report(monkeypatch):
    args, kwargs, calls, _, plan, budget = setup_case(monkeypatch, 2)
    old = source_bound_ranking.bind

    def fail_second(*a, **kw):
        if calls.count("grade_bind"):
            raise ValueError("private")
        return old(*a, **kw)

    monkeypatch.setattr(source_bound_ranking, "bind", fail_second)
    with pytest.raises(program.EvaluationError) as exc:
        invoke(args, kwargs, plan, budget)
    assert (
        exc.value.progress.phase,
        exc.value.progress.attempted,
        exc.value.progress.completed,
        exc.value.progress.refused,
        exc.value.progress.pending,
    ) == ("GRADE_BIND", 2, 1, 1, 0)
    assert "private" not in str(exc.value)


def test_budget_refusal_before_pin(monkeypatch):
    args, kwargs, calls, _, plan, budget = setup_case(monkeypatch)
    with pytest.raises(program.EvaluationError) as exc:
        invoke(args, kwargs, plan, dataclasses.replace(budget, metric_aggregate_calls=2))
    assert exc.value.progress is None and not calls


@pytest.mark.parametrize("count,mixed,index", [(1, False, 0), (256, False, 1), (3, True, 2)])
def test_legacy_root_golden(monkeypatch, count, mixed, index):
    from pathlib import Path
    from slaif_raggedized_helper import source_cohort_runner

    args, kwargs, calls, _ = fixture.controlled(monkeypatch, count, mixed=mixed)
    report = source_cohort_runner.run_cohort(*args, **kwargs)
    oracle_path = (
        Path(__file__).resolve().parents[2]
        / "docs/parallel/source-runner-legacy-identity-oracle.json"
    )
    expected = json.loads(oracle_path.read_text())["scenarios"][index]
    assert report.identity == expected["identity"]
    assert hashlib.sha256(report.identity_payload).hexdigest() == expected["payload_sha256"]
    assert len(report.identity_payload) == expected["payload_bytes"]
    assert (report.final_work, report.final_payload) == (
        expected["final_work"],
        expected["final_payload"],
    )
    assert {key: calls.count(key) for key in ("pin", "producer", "binder")} == expected["counts"]
    assert calls == ["pin"] + [
        item for _ in range(expected["selected_cases"]) for item in ("pin", "producer", "binder")
    ]


def test_full_256_moderate_controlled_cases(monkeypatch):
    args, kwargs, calls, _, plan, budget = setup_case(monkeypatch, 256)
    report = invoke(args, kwargs, plan, budget)
    obj = json.loads(report.identity_payload)
    assert obj["selected_case_count"] == 256
    assert all(value["total_queries"] == 256 for value in obj["variants"].values())
    assert calls.count("producer") == calls.count("grade_bind") == 256
    assert calls.count("pin") == 771


@pytest.mark.parametrize(
    "gold",
    [
        (("sha256:" + "1" * 64, 0.0),),
        (("sha256:" + "1" * 64, True),),
        (("sha256:" + "1" * 64, 1), ("sha256:" + "1" * 64, 2)),
        (("sha256:" + "1" * 64, 4),),
        (("1" * 64, 1),),
    ],
)
def test_exact_judgment_admission(monkeypatch, gold):
    args, kwargs, calls, _, plan, budget = setup_case(monkeypatch)
    plan = dataclasses.replace(plan, judgments=(program.Judgments("case000", gold),))
    with pytest.raises(program.EvaluationError) as exc:
        invoke(args, kwargs, plan, budget)
    assert exc.value.progress is None and exc.value.__context__ is None and not calls


def test_final_pin_refusal_returns_no_report(monkeypatch):
    from slaif_raggedized_helper import source_cohort_runner

    args, kwargs, calls, _, plan, budget = setup_case(monkeypatch)
    original = source_cohort_runner._owner_check

    def final_refusal(*a, **kw):
        if calls.count("pin") == 5:
            raise ValueError("private")
        return original(*a, **kw)

    monkeypatch.setattr(source_cohort_runner, "_owner_check", final_refusal)
    with pytest.raises(program.EvaluationError) as exc:
        invoke(args, kwargs, plan, budget)
    assert (
        exc.value.progress.phase,
        exc.value.progress.completed,
        exc.value.progress.refused,
        exc.value.progress.pending,
    ) == ("FINAL_PIN", 1, 0, 0)
    assert exc.value.__context__ is None


def test_base_exception_identity_propagates(monkeypatch):
    args, kwargs, _, _, plan, budget = setup_case(monkeypatch)
    sentinel = fixture.ForbiddenBoundary()

    def interrupt(*a, **kw):
        raise sentinel

    monkeypatch.setattr(source_bound_ranking, "bind", interrupt)
    with pytest.raises(fixture.ForbiddenBoundary) as exc:
        invoke(args, kwargs, plan, budget)
    assert exc.value is sentinel and args[3].state == "ACTIVE"


def test_unjudged_rank_gap_and_zero_grade(monkeypatch):
    from slaif_raggedized_helper import raw_dense_search, raw_lexical_search, raw_rank_fusion
    from slaif_raggedized_helper import source_cohort_runner

    wanted, other, zero = ("sha256:" + c * 64 for c in "123")
    judgments = (program.Judgments("case000", ((wanted, 2), (zero, 0))),)
    args, kwargs, _, _, plan, budget = setup_case(monkeypatch, 1, judgments)
    produce = source_cohort_runner._produce
    marker = "sha256:" + "a" * 64

    def ranked(*a, **kw):
        result = produce(*a, **kw)
        dense = tuple(
            raw_dense_search.Hit(i, marker, ident, marker, marker, b"", b"", i + 1, 1.0)
            for i, ident in enumerate((other, wanted))
        )
        lexical = tuple(
            raw_lexical_search.Hit(i, marker, ident, marker, marker, b"", b"", 1.0, i + 1)
            for i, ident in enumerate((other, wanted))
        )
        fusion = tuple(
            raw_rank_fusion.Hit(
                i, marker, ident, marker, marker, b"", b"", i + 1, i + 1, 1.0, i + 1
            )
            for i, ident in enumerate((other, wanted))
        )
        return dataclasses.replace(
            result,
            dense=dataclasses.replace(result.dense, hits=dense),
            lexical=dataclasses.replace(result.lexical, hits=lexical),
            fusion=dataclasses.replace(result.fusion, hits=fusion),
        )

    monkeypatch.setattr(source_cohort_runner, "_produce", ranked)
    payload = json.loads(invoke(args, kwargs, plan, budget).identity_payload)
    for variant in payload["variants"].values():
        metric = variant["query_results"][0]["at_k"][0]
        assert metric["reciprocal_rank"] == 0.5 and metric["recall"] == 1.0
        assert 0 < metric["ndcg"] < 1


def test_wrong_catalog_refuses_after_initial_pin(monkeypatch):
    args, kwargs, calls, _, plan, budget = setup_case(monkeypatch)
    with pytest.raises(program.EvaluationError) as exc:
        invoke(args, kwargs, dataclasses.replace(plan, catalog_id="sha256:" + "0" * 64), budget)
    assert exc.value.progress.phase == "CATALOG"
    assert calls == ["pin", "catalog"]


def test_aggregate_refusal_has_complete_case_prefix(monkeypatch):
    args, kwargs, calls, _, plan, budget = setup_case(monkeypatch)

    def fail(*a, **kw):
        raise ValueError("private metrics context")

    monkeypatch.setattr(supplied_rank_metrics, "aggregate", fail)
    with pytest.raises(program.EvaluationError) as exc:
        invoke(args, kwargs, plan, budget)
    assert exc.value.progress.phase == "GRADE_AGGREGATE"
    assert (
        exc.value.progress.attempted,
        exc.value.progress.completed,
        exc.value.progress.refused,
        exc.value.progress.pending,
    ) == (1, 1, 0, 0)
    assert exc.value.__context__ is None and calls.count("grade_bind") == 1


def test_zero_grade_grounded_and_undefined(monkeypatch):
    ident = "sha256:" + "1" * 64
    judgments = (program.Judgments("case000", ((ident, 0),)),)
    args, kwargs, calls, _, plan, budget = setup_case(monkeypatch, 1, judgments)
    obj = json.loads(invoke(args, kwargs, plan, budget).identity_payload)
    assert calls.count("grade_bind") == 1 and obj["cases"][0]["row_count"] == 1
    assert all(
        v["defined_queries"] == 0
        and v["undefined_empty_gold_queries"] == 1
        and v["at_k"][0]["mrr"] is None
        for v in obj["variants"].values()
    )


def test_extra_fields_and_subclass_refused(monkeypatch):
    args, kwargs, calls, _, plan, budget = setup_case(monkeypatch)
    object.__setattr__(plan, "extra", "private")
    with pytest.raises(program.EvaluationError) as exc:
        invoke(args, kwargs, plan, budget)
    assert exc.value.progress is None and not calls

    class DerivedBudget(program.GradeBudget):
        pass

    fresh = dataclasses.replace(plan)
    with pytest.raises(program.EvaluationError) as exc:
        invoke(args, kwargs, fresh, DerivedBudget(*program._MAX_BUDGET))
    assert exc.value.progress is None and not calls


def test_duplicate_query_identity_refuses_before_pin(monkeypatch):
    args, kwargs, calls, _, plan, budget = setup_case(monkeypatch, 2)
    wire = json.loads(args[4])
    wire["cases"][1]["question"] = wire["cases"][0]["question"]
    data = json.dumps(wire, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode()
    dataset = text_evaluation_dataset.admit(data)
    args = (*args[:4], data, *args[5:])
    plan = dataclasses.replace(plan, dataset_id=dataset.dataset_id, split_id=dataset.split_id)
    with pytest.raises(program.EvaluationError) as exc:
        invoke(args, kwargs, plan, budget)
    assert exc.value.progress is None and not calls


def test_grade_pin_refusal_has_case_prefix(monkeypatch):
    from slaif_raggedized_helper import source_cohort_runner

    args, kwargs, calls, _, plan, budget = setup_case(monkeypatch)
    original = source_cohort_runner._owner_check

    def fail(*a, **kw):
        if calls.count("pin") == 3:
            raise ValueError("private")
        return original(*a, **kw)

    monkeypatch.setattr(source_cohort_runner, "_owner_check", fail)
    with pytest.raises(program.EvaluationError) as exc:
        invoke(args, kwargs, plan, budget)
    assert (
        exc.value.progress.phase,
        exc.value.progress.attempted,
        exc.value.progress.completed,
        exc.value.progress.refused,
    ) == ("GRADE_PIN", 1, 0, 1)
    assert "grade_bind" not in calls


def test_serialization_failure_returns_no_report(monkeypatch):
    args, kwargs, _, _, plan, budget = setup_case(monkeypatch)

    def fail(*a, **kw):
        raise ValueError("private")

    monkeypatch.setattr(program, "_encoded", fail)
    with pytest.raises(program.EvaluationError) as exc:
        invoke(args, kwargs, plan, budget)
    assert exc.value.progress.phase == "SERIALIZE"
    assert exc.value.progress.completed == 1 and exc.value.__context__ is None


@pytest.mark.parametrize("deadline", [0, True, 1.5, 1200001])
def test_deadline_rejected_without_delegates(monkeypatch, deadline):
    args, kwargs, calls, _, plan, budget = setup_case(monkeypatch)
    kwargs["deadline_ms"] = deadline
    with pytest.raises(program.EvaluationError) as exc:
        invoke(args, kwargs, plan, budget)
    assert exc.value.progress is None and not calls


def test_z_final_module_origins():
    test_local_program_origins()


def test_unretrieved_zero_judgment_refused_by_source_binding(monkeypatch):
    ident = "sha256:" + "1" * 64
    args, kwargs, calls, _, plan, budget = setup_case(
        monkeypatch, 1, (program.Judgments("case000", ((ident, 0),)),)
    )

    def refused(*a, **kw):
        assert a[5] == (ident,)
        raise source_bound_ranking.SourceBindingError("private authorization")

    monkeypatch.setattr(source_bound_ranking, "bind", refused)
    with pytest.raises(program.EvaluationError) as exc:
        invoke(args, kwargs, plan, budget)
    assert exc.value.progress.phase == "GRADE_BIND"
    assert exc.value.progress.completed == 0 and exc.value.__context__ is None
    assert calls.count("producer") == calls.count("binder") == 1


def test_later_case_interrupt_propagates_without_subset(monkeypatch):
    args, kwargs, calls, _, plan, budget = setup_case(monkeypatch, 2)
    original = source_bound_ranking.bind
    sentinel = fixture.ForbiddenBoundary()

    def interrupt(*a, **kw):
        if calls.count("grade_bind"):
            raise sentinel
        return original(*a, **kw)

    monkeypatch.setattr(source_bound_ranking, "bind", interrupt)
    with pytest.raises(fixture.ForbiddenBoundary) as exc:
        invoke(args, kwargs, plan, budget)
    assert exc.value is sentinel and calls.count("grade_bind") == 1
    assert args[3].state == "ACTIVE"


def test_grade_int_subclass_and_later_duplicate_refused(monkeypatch):
    class Grade(int):
        pass

    args, kwargs, calls, _, plan, budget = setup_case(monkeypatch, 2)
    ident = "sha256:" + "1" * 64
    for gold in (((ident, Grade(1)),), ((ident, 1), (ident, 0))):
        judgments = (plan.judgments[0], program.Judgments("case001", gold))
        with pytest.raises(program.EvaluationError) as exc:
            invoke(args, kwargs, dataclasses.replace(plan, judgments=judgments), budget)
        assert exc.value.progress is None and not calls


def test_generation_mismatch_refused_before_producer(monkeypatch):
    args, kwargs, calls, captured, plan, budget = setup_case(monkeypatch)
    with pytest.raises(program.EvaluationError) as exc:
        invoke(
            args,
            kwargs,
            dataclasses.replace(plan, generation=captured.pointer.generation + 1),
            budget,
        )
    assert exc.value.progress.phase == "CATALOG" and calls == ["pin"]


def test_zz_last_module_origins():
    test_local_program_origins()


@pytest.mark.parametrize(
    "field,value", [("local_work", 1), ("local_payload", 1), ("report_bytes", 1)]
)
def test_local_and_output_preflight_refuse_before_pin(monkeypatch, field, value):
    args, kwargs, calls, _, plan, budget = setup_case(monkeypatch)
    with pytest.raises(program.EvaluationError) as exc:
        invoke(args, kwargs, plan, dataclasses.replace(budget, **{field: value}))
    assert exc.value.progress is None and calls == []


def test_zzz_final_origins_after_all_cases():
    test_local_program_origins()
