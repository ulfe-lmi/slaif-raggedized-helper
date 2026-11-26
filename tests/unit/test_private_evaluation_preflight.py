"""Bounded preflight tests for the private joint evaluation declaration entry.

The witnesses here are test-local delegating wrappers: they invoke the real
private functions unchanged and record call order, arguments, the shared
deadline, the separate meters and the preserved binder declaration calls.
No witness re-implements admission.  Only synthetic declaration shapes,
synthetic dataset bytes and inert owner references are used; no pin,
catalog, producer, vector, encoder, source, scorer, report or publication
access occurs.
"""

import dataclasses
import hashlib
import inspect
import json
import time
from pathlib import Path

import pytest

import test_source_cohort_runner as fixture
from slaif_raggedized_helper import evaluation_plan_wire as wire
from slaif_raggedized_helper import evaluation_program as program
from slaif_raggedized_helper import private_evaluation_preflight as preflight
from slaif_raggedized_helper import private_report_publication as publication
from slaif_raggedized_helper import provenance_records as provenance
from slaif_raggedized_helper import raw_snapshot_catalog as catalog
from slaif_raggedized_helper import raw_snapshot_pin as pin
from slaif_raggedized_helper import raw_snapshot_publication as snapshot_publication
from slaif_raggedized_helper import source_bound_stage_loss as binder
from slaif_raggedized_helper import source_cohort_runner as runner
from slaif_raggedized_helper import text_evaluation_dataset as dataset_module

_GOLD = ((("sha256:" + "1" * 64, 2),), (("sha256:" + "2" * 64, 1),))
_CATALOG_ID = "sha256:" + "c" * 64
_UNKNOWN_POLICY = "UNJUDGED_AS_ZERO_DIAGNOSTIC"
_OVERLAP_POLICY = "EXPLICIT_CHUNK_IDS_ONLY"


class ForbiddenBoundary(BaseException):
    pass


class _Interrupt(BaseException):
    pass


def forbid(monkeypatch, module, name):
    def forbidden(*args, **kwargs):
        raise ForbiddenBoundary()

    monkeypatch.setattr(module, name, forbidden)


def no_execution_boundaries(monkeypatch):
    """Zero new pin, privileged source, encoder, producer, scorer, report or publication."""

    for module, name in (
        (runner, "_owner_check"),
        (runner, "_produce"),
        (runner, "_bind"),
        (runner, "_pin_observation"),
        (runner, "_aggregate"),
        (runner, "run_cohort"),
        (binder, "_preflight_inputs"),
        (binder, "_canonical_hash"),
        (pin, "_admit"),
        (catalog, "load_catalog"),
        (program, "run_evaluation"),
        (program, "_case"),
        (program, "_finish"),
        (publication, "publish"),
        (snapshot_publication, "publish_directory"),
    ):
        forbid(monkeypatch, module, name)


def decl_ids(index):
    return (
        hashlib.sha256(("space-" + str(index)).encode()).hexdigest(),
        "sha256:" + hashlib.sha256(("definition-" + str(index)).encode()).hexdigest(),
        hashlib.sha256(("policy-" + str(index)).encode()).hexdigest(),
        hashlib.sha256(("execution-" + str(index)).encode()).hexdigest(),
    )


def identifiers_for(cohort):
    return tuple(decl_ids(index) for index in range(len(cohort.case_ids)))


def judgments_for(case_ids, golds):
    return tuple(
        program.Judgments(case_id, gold) for case_id, gold in zip(case_ids, golds, strict=True)
    )


def controlled(monkeypatch, count=1):
    args, kwargs, calls, captured = fixture.controlled(monkeypatch, count)
    (originals, derived, root, owner, data, cohort, _queries, gold_ids) = args
    no_execution_boundaries(monkeypatch)
    return args, kwargs, calls, captured, dict(
        originals=originals, derived=derived, root=root, owner=owner, data=data,
        cohort=cohort, gold_ids=gold_ids,
    )


def setup(monkeypatch, count=2):
    args, kwargs, calls, captured, closed = controlled(monkeypatch, count)
    return dict(
        args=args,
        kwargs=kwargs,
        calls=calls,
        captured=captured,
        dataset=dataset_module.admit(closed["data"]),
        **closed,
    )


def grade_budget():
    return program.GradeBudget(*program._MAX_BUDGET)


def wire_bytes(dataset, captured, judgments, overrides=None):
    obj = {
        "schema": 1,
        "plan_id": "plan",
        "dataset_id": dataset.dataset_id,
        "split_id": dataset.split_id,
        "snapshot_id": captured.pointer.snapshot_id,
        "generation": captured.pointer.generation,
        "catalog_id": _CATALOG_ID,
        "protocol_id": "protocol",
        "unknown_policy": _UNKNOWN_POLICY,
        "overlap_policy": _OVERLAP_POLICY,
        "cutoffs": [20, 60],
        "judgments": [
            {"case_id": judgment.case_id, "gold": [list(pair) for pair in judgment.gold]}
            for judgment in judgments
        ],
    }
    if overrides is not None:
        obj.update(overrides)
    return json.dumps(obj, separators=(",", ":"), ensure_ascii=True).encode("ascii")


def invoke(ctx, raw, *, owner=None, config=None, cohort=None, identifiers=None,
           gold_ids=None, source_budget=None, grade_budget_=None, deadline_ms=120000):
    cohort = ctx["cohort"] if cohort is None else cohort
    return preflight._prepare_declaration(
        raw,
        ctx["originals"],
        ctx["derived"],
        ctx["root"],
        ctx["owner"] if owner is None else owner,
        ctx["data"],
        cohort,
        identifiers if identifiers is not None else identifiers_for(cohort),
        gold_ids if gold_ids is not None else ctx["gold_ids"],
        ctx["kwargs"]["grants"],
        ctx["kwargs"]["restrictions"],
        ctx["kwargs"]["config"] if config is None else config,
        source_budget if source_budget is not None else ctx["kwargs"]["budget"],
        grade_budget_ if grade_budget_ is not None else grade_budget(),
        deadline_ms=deadline_ms,
    )


def witness(monkeypatch):
    """Delegating witnesses over the three boundaries plus clock and meter creation."""

    w = {"events": [], "deadlines": [], "meters": [], "binder_calls": []}
    w["real_admit"] = wire.admit
    w["real_source"] = runner._declaration_admission
    w["real_grade"] = program._prepare_plan
    w["real_deadline"] = runner._Deadline
    w["real_meter"] = runner._Meter
    w["real_binder"] = binder._preflight_declaration

    def admit(raw):
        w["events"].append(("wire", "in"))
        result = w["real_admit"](raw)
        w["events"].append(("wire", "out"))
        w["plan_return"] = result
        return result

    def source_admission(*args):
        w["events"].append(("source", "in"))
        w["source_args"] = args
        w["source_clock"] = args[12]
        result = w["real_source"](*args)
        w["events"].append(("source", "out"))
        w["source_return"] = result
        return result

    def grade_plan(state, dataset, selected, clock):
        w["events"].append(("grade", "in"))
        w["grade_clock"] = clock
        w["grade_dataset"] = dataset
        w["grade_selected"] = selected
        result = w["real_grade"](state, dataset, selected, clock)
        w["events"].append(("grade", "out"))
        w["grade_return"] = result
        w["grade_state"] = state
        return result

    def deadline(started, milliseconds):
        result = w["real_deadline"](started, milliseconds)
        w["deadlines"].append(result)
        return result

    def meter(work_limit, payload_limit, check):
        result = w["real_meter"](work_limit, payload_limit, check)
        w["meters"].append(result)
        return result

    def preflight_declaration(root, data, case_id, gold_bundle_ids, identifiers,
                              deadline_ms, meter):
        w["binder_calls"].append((case_id, identifiers, root, data, gold_bundle_ids))
        return w["real_binder"](root, data, case_id, gold_bundle_ids, identifiers,
                                deadline_ms, meter)

    monkeypatch.setattr(wire, "admit", admit)
    monkeypatch.setattr(runner, "_declaration_admission", source_admission)
    monkeypatch.setattr(program, "_prepare_plan", grade_plan)
    monkeypatch.setattr(runner, "_Deadline", deadline)
    monkeypatch.setattr(runner, "_Meter", meter)
    monkeypatch.setattr(binder, "_preflight_declaration", preflight_declaration)
    return w


def patched_clock(monkeypatch, start=1000.0):
    state = {"t": start}
    monkeypatch.setattr(time, "monotonic", lambda: state["t"])
    return state


def phases(w):
    return [name for name, _ in w["events"]]


def raw_for(ctx):
    return wire_bytes(ctx["dataset"], ctx["captured"],
                      judgments_for(ctx["cohort"].case_ids, _GOLD))


def test_assigned_worktree_import_proof():
    here = Path(__file__).resolve()
    root = here.parents[2]
    assert here.parent.is_relative_to(root / "tests" / "unit")
    expected = root / "src" / "slaif_raggedized_helper" / "private_evaluation_preflight.py"
    assert Path(preflight.__file__).resolve() == expected


def test_entry_exposes_no_alternate_clock_or_pre_admitted_plan():
    parameters = inspect.signature(preflight._prepare_declaration).parameters
    names = set(parameters)
    for name in ("plan", "clock", "deadline", "started", "milliseconds"):
        assert name not in names
    assert "plan_wire" in names
    assert "deadline_ms" in names
    assert parameters["deadline_ms"].kind is inspect.Parameter.KEYWORD_ONLY
    assert all(
        parameters[name].kind in (
            inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.KEYWORD_ONLY
        )
        for name in names
    )


def test_joint_declaration_admits_two_cases_one_deadline_shared_dataset(monkeypatch):
    ctx = setup(monkeypatch, 2)
    w = witness(monkeypatch)
    judgments = judgments_for(ctx["cohort"].case_ids, _GOLD)
    raw = wire_bytes(ctx["dataset"], ctx["captured"], judgments)
    identifiers = identifiers_for(ctx["cohort"])
    result = invoke(ctx, raw, identifiers=identifiers)

    assert ctx["calls"] == []
    assert phases(w) == ["wire", "wire", "source", "source", "grade", "grade"]
    # One deadline, created at entry, shared by both phases and the entry checks.
    assert len(w["deadlines"]) == 1
    assert w["source_clock"] is w["deadlines"][0]
    assert w["grade_clock"] is w["deadlines"][0]
    # Separate meters from the separate source and grade budgets.
    assert len(w["meters"]) == 2
    assert (w["meters"][0].work_limit, w["meters"][0].payload_limit) == (
        ctx["kwargs"]["budget"].local_work, ctx["kwargs"]["budget"].local_payload
    )
    assert (w["meters"][1].work_limit, w["meters"][1].payload_limit) == (
        grade_budget().local_work, grade_budget().local_payload
    )
    # The genuine source admission ran with its preserved binder calls.
    dataset, selected, selection, source_meter = w["source_return"]
    for call, case_id, ident in zip(
        w["binder_calls"], ctx["cohort"].case_ids, result.identifiers, strict=True
    ):
        assert call == (case_id, ident, ctx["root"], ctx["data"], ctx["gold_ids"])
    # The exact validated per-case encoder-identifier tuples are retained,
    # tied to the selected order.
    assert result.identifiers is identifiers
    assert len(result.identifiers) == len(result.selected)
    # The same admitted dataset and ordered selected values at both phases.
    assert w["grade_dataset"] is dataset
    assert w["grade_selected"] is selected
    assert result.dataset is dataset
    assert result.selected is selected
    assert result.selection == selection == "FULL_ADMITTED_SPLIT"
    assert dataset.canonical_bytes == ctx["data"]
    assert tuple(case.case_id for case, *_ in selected) == ctx["cohort"].case_ids
    # The returned plan has the exact admitted wire meaning.
    assert result.plan is w["plan_return"]
    assert result.plan == w["real_admit"](raw)
    assert type(result.plan) is program.Plan
    assert (result.plan.dataset_id, result.plan.split_id) == (
        dataset.dataset_id, dataset.split_id
    )
    assert (result.plan.snapshot_id, result.plan.generation) == (
        ctx["captured"].pointer.snapshot_id, ctx["captured"].pointer.generation
    )
    assert result.plan.judgments == judgments
    # Actual source and grade accounting, coupled in the bounded result.
    assert source_meter is w["meters"][0]
    assert (result.source_work, result.source_payload) == (
        source_meter.work, source_meter.payload
    )
    assert w["grade_state"].meter is w["meters"][1]
    assert (result.grade_work, result.grade_payload) == (
        w["grade_state"].meter.work, w["grade_state"].meter.payload
    )
    assert w["grade_return"] == (
        result.entries, result.minimum_work, result.minimum_payload
    )
    # The selected values retain the admitted authority snapshots, not caller state.
    for case, original, effective, restricted in result.selected:
        assert type(case) is dataset_module.Case
        assert type(original) is provenance.Grants
        assert type(effective) is provenance.Grants
        assert original is not ctx["kwargs"]["grants"]
        assert restricted is None
        assert (effective.corpora, effective.versions, effective.labels) == (
            case.scope.corpora, case.scope.versions, case.scope.labels
        )
    # No vectors, embeddings or further authority: only admitted identities,
    # selected data and measured integers are coupled in the result.
    for field in dataclasses.fields(result):
        assert type(getattr(result, field.name)) in (
            str, int, program.Plan, dataset_module.Dataset, tuple
        )
    for value in (result.plan, result.dataset):
        for field in dataclasses.fields(value):
            assert type(getattr(value, field.name)) in (str, int, bytes, tuple)
    caller = (
        ctx["originals"], ctx["derived"], ctx["owner"], ctx["kwargs"]["grants"],
        ctx["kwargs"]["restrictions"], ctx["kwargs"]["config"], ctx["kwargs"]["budget"],
    )
    for field in dataclasses.fields(result):
        for value in caller:
            assert getattr(result, field.name) is not value


def test_joint_declaration_preserves_declared_subset_order(monkeypatch):
    ctx = setup(monkeypatch, 3)
    w = witness(monkeypatch)
    subset = runner.Cohort(ctx["cohort"].split, ctx["cohort"].case_ids[::2])
    judgments = judgments_for(subset.case_ids, _GOLD)
    raw = wire_bytes(ctx["dataset"], ctx["captured"], judgments)
    identifiers = tuple(decl_ids(index) for index in (0, 2))
    result = invoke(ctx, raw, cohort=subset, identifiers=identifiers)
    assert ctx["calls"] == []
    assert phases(w) == ["wire", "wire", "source", "source", "grade", "grade"]
    assert result.selection == "DECLARED_SUBSET"
    assert tuple(case.case_id for case, *_ in result.selected) == subset.case_ids
    assert [call[0] for call in w["binder_calls"]] == list(subset.case_ids)
    assert result.plan.judgments == judgments
    assert result.identifiers is identifiers
    assert w["grade_dataset"] is w["source_return"][0]


def test_exact_legal_source_budget_admits(monkeypatch):
    ctx = setup(monkeypatch, 2)
    w = witness(monkeypatch)
    _directories, ingestion, _batches, _size = runner._source_reservation(
        len(ctx["cohort"].case_ids)
    )
    budget = dataclasses.replace(ctx["kwargs"]["budget"], source_ingestion_loads=ingestion)
    result = invoke(ctx, raw_for(ctx), source_budget=budget)
    assert ctx["calls"] == []
    assert len(w["binder_calls"]) == 2
    assert (w["meters"][0].work_limit, w["meters"][0].payload_limit) == (
        budget.local_work, budget.local_payload
    )
    assert result.selection == "FULL_ADMITTED_SPLIT"


@pytest.mark.parametrize(
    "raw", [b"", b"{}", b'{"schema": 1', b'{"schema": 2}', b'{"schema": "one"}']
)
def test_malformed_wire_refuses_before_source_phase(monkeypatch, raw):
    ctx = setup(monkeypatch, 2)
    w = witness(monkeypatch)
    with pytest.raises(preflight.PreparationError):
        invoke(ctx, raw)
    assert phases(w) == ["wire"]
    assert w["binder_calls"] == []
    assert len(w["meters"]) == 0 and len(w["deadlines"]) == 1
    assert ctx["calls"] == []


def test_non_bytes_wire_refuses_before_source_phase(monkeypatch):
    ctx = setup(monkeypatch, 2)
    w = witness(monkeypatch)
    with pytest.raises(preflight.PreparationError):
        invoke(ctx, "{}")
    assert phases(w) == ["wire"]
    assert w["binder_calls"] == []
    assert ctx["calls"] == []


@pytest.mark.parametrize("deadline_ms", [0, -1, 1200001, "1200000", True])
def test_invalid_deadline_refuses_before_wire(monkeypatch, deadline_ms):
    ctx = setup(monkeypatch, 2)
    w = witness(monkeypatch)
    with pytest.raises(preflight.PreparationError):
        invoke(ctx, raw_for(ctx), deadline_ms=deadline_ms)
    assert phases(w) == []
    assert w["binder_calls"] == []
    assert len(w["meters"]) == 0 and len(w["deadlines"]) == 0
    assert ctx["calls"] == []


def test_non_tuple_identifiers_refuses_before_wire(monkeypatch):
    ctx = setup(monkeypatch, 2)
    w = witness(monkeypatch)
    identifiers = list(identifiers_for(ctx["cohort"]))
    with pytest.raises(preflight.PreparationError):
        invoke(ctx, raw_for(ctx), identifiers=identifiers)
    assert phases(w) == []
    assert w["binder_calls"] == []
    # The entry deadline now exists before the identifier gate refuses.
    assert len(w["meters"]) == 0 and len(w["deadlines"]) == 1
    assert ctx["calls"] == []


def test_invalid_last_declaration_case_refuses_before_grade(monkeypatch):
    ctx = setup(monkeypatch, 2)
    w = witness(monkeypatch)
    bad = identifiers_for(ctx["cohort"])[:-1] + (("a" * 64, "sha256:" + "a" * 64),)
    with pytest.raises(preflight.PreparationError):
        invoke(ctx, raw_for(ctx), identifiers=bad)
    assert phases(w) == ["wire", "wire", "source"]
    assert len(w["binder_calls"]) == 2
    assert len(w["meters"]) == 1
    assert ctx["calls"] == []


def test_undersized_source_budget_refuses_before_grade(monkeypatch):
    ctx = setup(monkeypatch, 2)
    w = witness(monkeypatch)
    _directories, ingestion, _batches, _size = runner._source_reservation(
        len(ctx["cohort"].case_ids)
    )
    budget = dataclasses.replace(
        ctx["kwargs"]["budget"], source_ingestion_loads=ingestion - 1
    )
    with pytest.raises(preflight.PreparationError):
        invoke(ctx, raw_for(ctx), source_budget=budget)
    assert phases(w) == ["wire", "wire", "source"]
    assert w["binder_calls"] == []
    assert len(w["meters"]) == 0
    assert ctx["calls"] == []


def test_undersized_grade_budget_refuses_before_prepared_output(monkeypatch):
    ctx = setup(monkeypatch, 2)
    (originals, derived, root, owner, data, cohort, _queries, gold_ids) = ctx["args"]
    judgments = judgments_for(cohort.case_ids, _GOLD)
    # Real reference admission to compute the exact report bound.
    clock = runner._Deadline(time.monotonic(), 120000)
    dataset, selected, _selection, _meter = runner._declaration_admission(
        originals, derived, root, owner, data, cohort, identifiers_for(cohort),
        gold_ids, ctx["kwargs"]["grants"], ctx["kwargs"]["restrictions"],
        ctx["kwargs"]["config"], ctx["kwargs"]["budget"], clock,
    )
    plan = program.Plan(
        "plan", dataset.dataset_id, dataset.split_id,
        ctx["captured"].pointer.snapshot_id, ctx["captured"].pointer.generation,
        _CATALOG_ID, "protocol", _UNKNOWN_POLICY, _OVERLAP_POLICY, (20, 60), judgments,
    )
    reference = runner._Meter(
        ctx["kwargs"]["budget"].local_work, ctx["kwargs"]["budget"].local_payload,
        clock.check,
    )
    _entries, _work, report_bound = program._plan_admission(
        plan, grade_budget(), dataset, selected, reference, clock
    )
    budget = dataclasses.replace(grade_budget(), report_bytes=report_bound - 1)

    w = witness(monkeypatch)
    with pytest.raises(preflight.PreparationError):
        invoke(ctx, raw_for(ctx), grade_budget_=budget)
    assert phases(w) == ["wire", "wire", "source", "source", "grade"]
    assert len(w["binder_calls"]) == 2
    assert ctx["calls"] == []


@pytest.mark.parametrize(
    "overrides",
    [
        {"dataset_id": "sha256:" + "0" * 64},
        {"split_id": "sha256:" + "0" * 64},
    ],
)
def test_valid_wire_grade_dataset_disagreement_refuses_before_prepared_output(
    monkeypatch, overrides
):
    ctx = setup(monkeypatch, 2)
    w = witness(monkeypatch)
    raw = wire_bytes(ctx["dataset"], ctx["captured"],
                     judgments_for(ctx["cohort"].case_ids, _GOLD), overrides)
    with pytest.raises(preflight.PreparationError):
        invoke(ctx, raw)
    assert phases(w) == ["wire", "wire", "source", "source", "grade"]
    assert len(w["binder_calls"]) == 2
    assert ctx["calls"] == []


def test_valid_wire_order_disagreement_refuses_before_prepared_output(monkeypatch):
    ctx = setup(monkeypatch, 3)
    w = witness(monkeypatch)
    subset = runner.Cohort(ctx["cohort"].split, ctx["cohort"].case_ids[:2])
    judgments = judgments_for(
        (ctx["cohort"].case_ids[0], ctx["cohort"].case_ids[2]), _GOLD
    )
    raw = wire_bytes(ctx["dataset"], ctx["captured"], judgments)
    with pytest.raises(preflight.PreparationError):
        invoke(ctx, raw, cohort=subset,
               identifiers=tuple(decl_ids(index) for index in (0, 1)))
    # The admitted selection is the declared subset; the plan case order
    # disagrees with it before any prepared output.
    assert phases(w) == ["wire", "wire", "source", "source", "grade"]
    assert tuple(case.case_id for case, *_ in w["source_return"][1]) == subset.case_ids
    assert len(w["binder_calls"]) == 2
    assert ctx["calls"] == []


def test_deadline_exhausted_after_wire_refuses_before_source(monkeypatch):
    state = patched_clock(monkeypatch)
    ctx = setup(monkeypatch, 2)
    w = witness(monkeypatch)
    spy_admit = wire.admit

    def admit_and_exhaust(raw):
        result = spy_admit(raw)
        state["t"] = 1000.0 + 120.0
        return result

    monkeypatch.setattr(wire, "admit", admit_and_exhaust)
    with pytest.raises(preflight.PreparationError):
        invoke(ctx, raw_for(ctx), deadline_ms=120000)
    assert phases(w) == ["wire", "wire"]
    assert w["binder_calls"] == [] and len(w["meters"]) == 0
    assert len(w["deadlines"]) == 1
    assert ctx["calls"] == []


def test_late_success_refused_after_complete_grade(monkeypatch):
    state = patched_clock(monkeypatch)
    ctx = setup(monkeypatch, 2)
    w = witness(monkeypatch)
    spy_grade = program._prepare_plan

    def grade_and_exhaust(state_arg, dataset, selected, clock):
        result = spy_grade(state_arg, dataset, selected, clock)
        state["t"] = 1000.0 + 120.0
        return result

    monkeypatch.setattr(program, "_prepare_plan", grade_and_exhaust)
    with pytest.raises(preflight.PreparationError):
        invoke(ctx, raw_for(ctx), deadline_ms=120000)
    # Both phases completed for real; only the final remaining-time check refuses.
    assert phases(w) == ["wire", "wire", "source", "source", "grade", "grade"]
    assert len(w["binder_calls"]) == 2
    assert ctx["calls"] == []


def test_small_deadline_admits_under_controlled_clock(monkeypatch):
    # A two-millisecond margin keeps every internal remaining-time check
    # inside the representable double distance from the constant clock value;
    # the early usable result is returned while the fixed clock still has time.
    patched_clock(monkeypatch)
    ctx = setup(monkeypatch, 2)
    w = witness(monkeypatch)
    result = invoke(ctx, raw_for(ctx), deadline_ms=2)
    assert ctx["calls"] == []
    assert phases(w) == ["wire", "wire", "source", "source", "grade", "grade"]
    assert len(w["deadlines"]) == 1
    assert result.selection == "FULL_ADMITTED_SPLIT"


def test_mismatched_split_refuses_before_grade(monkeypatch):
    ctx = setup(monkeypatch, 2)
    w = witness(monkeypatch)
    other = "held_out" if ctx["cohort"].split == "tuning" else "tuning"
    cohort = runner.Cohort(other, ctx["cohort"].case_ids)
    with pytest.raises(preflight.PreparationError):
        invoke(ctx, raw_for(ctx), cohort=cohort)
    assert phases(w) == ["wire", "wire", "source"]
    assert len(w["binder_calls"]) == 2
    assert ctx["calls"] == []


def test_out_of_scope_case_refuses_before_grade(monkeypatch):
    ctx = setup(monkeypatch, 2)
    w = witness(monkeypatch)
    out_of_scope = ctx["cohort"].case_ids[0] + "x"
    cohort = runner.Cohort(ctx["cohort"].split, (ctx["cohort"].case_ids[0], out_of_scope))
    raw = wire_bytes(ctx["dataset"], ctx["captured"], judgments_for(cohort.case_ids, _GOLD))
    with pytest.raises(preflight.PreparationError):
        invoke(ctx, raw, cohort=cohort, identifiers=(decl_ids(0), decl_ids(9)))
    assert phases(w) == ["wire", "wire", "source"]
    assert [call[0] for call in w["binder_calls"]] == list(cohort.case_ids)
    assert ctx["calls"] == []


@pytest.mark.parametrize(
    "gold_ids",
    [
        ("a" * 64, "a" * 64),
        ("a" * 63, "b" * 64),
        ("b" * 64, "a" * 64),
    ],
)
def test_invalid_gold_declaration_refuses_before_grade(monkeypatch, gold_ids):
    ctx = setup(monkeypatch, 2)
    w = witness(monkeypatch)
    with pytest.raises(preflight.PreparationError):
        invoke(ctx, raw_for(ctx), gold_ids=gold_ids)
    assert phases(w) == ["wire", "wire", "source"]
    assert len(w["binder_calls"]) == 1
    assert ctx["calls"] == []


@pytest.mark.parametrize("fault", ["owner", "config"])
def test_nominal_owner_or_config_layout_refuses_before_grade(monkeypatch, fault):
    ctx = setup(monkeypatch, 2)
    w = witness(monkeypatch)
    if fault == "owner":

        # A bare object: the closed envelope admits the exact PinOwner type
        # only, so any other nominal owner layout is refused.
        overrides = {"owner": object()}
    else:
        overrides = {"config": runner.Config("cfg", "decl aration")}
    with pytest.raises(preflight.PreparationError):
        invoke(ctx, raw_for(ctx), **overrides)
    assert phases(w) == ["wire", "wire", "source"]
    assert w["binder_calls"] == []
    assert ctx["calls"] == []


def test_coincident_wire_and_source_faults_refuse_at_wire(monkeypatch):
    ctx = setup(monkeypatch, 2)
    w = witness(monkeypatch)
    _directories, ingestion, _batches, _size = runner._source_reservation(
        len(ctx["cohort"].case_ids)
    )
    budget = dataclasses.replace(
        ctx["kwargs"]["budget"], source_ingestion_loads=ingestion - 1
    )
    bad = identifiers_for(ctx["cohort"])[:-1] + (("a" * 64, "sha256:" + "a" * 64),)
    with pytest.raises(preflight.PreparationError):
        invoke(ctx, b"{}", identifiers=bad, source_budget=budget)
    assert phases(w) == ["wire"]
    assert w["binder_calls"] == [] and len(w["meters"]) == 0
    assert ctx["calls"] == []


def test_source_fault_outranks_grade_fault(monkeypatch):
    ctx = setup(monkeypatch, 2)
    w = witness(monkeypatch)
    raw = wire_bytes(ctx["dataset"], ctx["captured"],
                     judgments_for(ctx["cohort"].case_ids, _GOLD),
                     {"dataset_id": "sha256:" + "0" * 64})
    _directories, ingestion, _batches, _size = runner._source_reservation(
        len(ctx["cohort"].case_ids)
    )
    budget = dataclasses.replace(
        ctx["kwargs"]["budget"], source_ingestion_loads=ingestion - 1
    )
    with pytest.raises(preflight.PreparationError):
        invoke(ctx, raw, source_budget=budget)
    assert phases(w) == ["wire", "wire", "source"]
    assert w["binder_calls"] == []
    assert ctx["calls"] == []


def test_interruption_identity_propagates_at_wire(monkeypatch):
    ctx = setup(monkeypatch, 2)

    def interrupt(raw):
        raise _Interrupt()

    monkeypatch.setattr(wire, "admit", interrupt)
    with pytest.raises(_Interrupt):
        invoke(ctx, raw_for(ctx))


def test_interruption_identity_propagates_at_source(monkeypatch):
    ctx = setup(monkeypatch, 2)

    def interrupt(*args):
        raise _Interrupt()

    monkeypatch.setattr(runner, "_declaration_admission", interrupt)
    with pytest.raises(_Interrupt):
        invoke(ctx, raw_for(ctx))


def test_refusal_is_fixed_ordinary_and_content_free(monkeypatch):
    ctx = setup(monkeypatch, 2)
    w = witness(monkeypatch)
    judgments = judgments_for(ctx["cohort"].case_ids, _GOLD)
    wire_fault = b"{}"
    grade_fault = wire_bytes(ctx["dataset"], ctx["captured"], judgments,
                             {"dataset_id": "sha256:" + "0" * 64})
    for raw in (wire_fault, grade_fault):
        with pytest.raises(preflight.PreparationError) as caught:
            invoke(ctx, raw)
        exc = caught.value
        assert type(exc) is preflight.PreparationError
        assert issubclass(preflight.PreparationError, ValueError)
        assert str(exc) == "private evaluation preparation refused"
        assert exc.__cause__ is None
        assert exc.__context__ is None
        assert "wire" not in str(exc) and "grade" not in str(exc)
    # The wire fault never reached the source; the grade fault refused after
    # the completed source phase; the fixed message is identical for both.
    assert phases(w) == ["wire", "wire", "wire", "source", "source", "grade"]
    assert len(w["binder_calls"]) == 2
    assert ctx["calls"] == []


def test_distinct_gold_config_and_budget_declarations_remain_distinguishable(monkeypatch):
    ctx = setup(monkeypatch, 2)
    w = witness(monkeypatch)
    golds_a = ("a" * 64, "b" * 64)
    golds_b = ("a" * 64, "b" * 64, "c" * 64)
    config_a = runner.Config("cfg-a", "decl-a")
    config_b = runner.Config("cfg-b", "decl-b")
    budget_b = dataclasses.replace(grade_budget(), report_bytes=program._MAX_BUDGET[12] - 1)
    result_a = invoke(ctx, raw_for(ctx), gold_ids=golds_a, config=config_a)
    result_b = invoke(ctx, raw_for(ctx), gold_ids=golds_b, config=config_b,
                      grade_budget_=budget_b)
    assert ctx["calls"] == []
    # One fresh shared deadline per entry; both phases of each entry use it.
    assert phases(w) == ["wire", "wire", "source", "source", "grade", "grade"] * 2
    assert len(w["deadlines"]) == 2
    # Actual source and grade accounting per entry, from the separate budgets.
    assert (result_a.source_work, result_a.source_payload) == (
        w["meters"][0].work, w["meters"][0].payload
    )
    assert (result_a.grade_work, result_a.grade_payload) == (
        w["meters"][1].work, w["meters"][1].payload
    )
    assert (result_b.source_work, result_b.source_payload) == (
        w["meters"][2].work, w["meters"][2].payload
    )
    assert (result_b.grade_work, result_b.grade_payload) == (
        w["meters"][3].work, w["meters"][3].payload
    )
    # The extra admissible Gold declaration is metered by the source phase.
    assert result_b.source_work > result_a.source_work
    # The distinct admissible grade budget limit changes nothing metered.
    assert (result_a.grade_work, result_a.grade_payload) == (
        result_b.grade_work, result_b.grade_payload
    )
    assert (result_a.entries, result_a.minimum_work, result_a.minimum_payload) == (
        result_b.entries, result_b.minimum_work, result_b.minimum_payload
    )
    # The declared scope is identical at both entries.
    assert result_a.plan == result_b.plan
    assert result_a.dataset == result_b.dataset
    assert result_a.selection == result_b.selection
    assert tuple(case.case_id for case, *_ in result_a.selected) == ctx["cohort"].case_ids
    assert tuple(case.case_id for case, *_ in result_b.selected) == ctx["cohort"].case_ids
    # The distinct Gold, config and budget inputs remain distinguishable in
    # the coupled result, as immutable primitive snapshots.
    assert result_a.gold_ids is golds_a and result_b.gold_ids is golds_b
    assert result_a.config == ("cfg-a", "decl-a")
    assert result_b.config == ("cfg-b", "decl-b")
    assert result_a.source_budget == result_b.source_budget
    assert result_a.source_budget == tuple(
        getattr(ctx["kwargs"]["budget"], field.name) for field in dataclasses.fields(runner.Budget)
    )
    assert result_a.grade_budget != result_b.grade_budget
    assert result_a.grade_budget == tuple(
        getattr(grade_budget(), field.name) for field in dataclasses.fields(program.GradeBudget)
    )
    assert result_b.grade_budget == tuple(
        getattr(budget_b, field.name) for field in dataclasses.fields(program.GradeBudget)
    )


def test_ordinary_exception_translated_to_fixed_refusal(monkeypatch):
    ctx = setup(monkeypatch, 2)
    w = witness(monkeypatch)
    spy_grade = program._prepare_plan
    failures = []

    def grade_and_fail(state_arg, dataset, selected, clock):
        result = spy_grade(state_arg, dataset, selected, clock)
        failures.append(result)
        raise RuntimeError("ordinary-failure-marker")

    monkeypatch.setattr(program, "_prepare_plan", grade_and_fail)
    with pytest.raises(preflight.PreparationError) as caught:
        invoke(ctx, raw_for(ctx))
    exc = caught.value
    assert type(exc) is preflight.PreparationError
    assert str(exc) == "private evaluation preparation refused"
    assert exc.__cause__ is None
    assert exc.__context__ is None
    assert "marker" not in str(exc) and "RuntimeError" not in str(exc)
    # The counted real grade delegate completed for real after the real
    # source admission; only the boundary translation changes the error.
    assert len(failures) == 1
    assert phases(w) == ["wire", "wire", "source", "source", "grade", "grade"]
    assert len(w["binder_calls"]) == 2
    assert ctx["calls"] == []


def test_result_retains_gate_admitted_nominals_despite_late_alias_mutation(monkeypatch):
    ctx = setup(monkeypatch, 2)
    w = witness(monkeypatch)
    config = runner.Config("admitted-config", "admitted-declaration")
    source_budget = dataclasses.replace(ctx["kwargs"]["budget"])
    grade_budget_ = grade_budget()
    expected_source = tuple(
        getattr(source_budget, field.name) for field in dataclasses.fields(runner.Budget)
    )
    expected_grade = tuple(
        getattr(grade_budget_, field.name) for field in dataclasses.fields(program.GradeBudget)
    )
    spy_grade = program._prepare_plan
    observed = []

    def grade_then_mutate(state_arg, dataset, selected, clock):
        result = spy_grade(state_arg, dataset, selected, clock)
        observed.append(state_arg.budget.local_work)
        # Change only the original caller-owned nominal aliases, after the
        # real grade gate returned.
        config.__dict__["config_id"] = "caller-changed-after-admission"
        source_budget.__dict__["local_work"] = 0
        grade_budget_.__dict__["local_work"] = 0
        return result

    monkeypatch.setattr(program, "_prepare_plan", grade_then_mutate)
    result = invoke(ctx, raw_for(ctx), config=config, source_budget=source_budget,
                    grade_budget_=grade_budget_)
    # The genuine gates ran on owned nominal records, not the caller aliases.
    assert observed == [program._MAX_BUDGET[10]]
    assert w["source_args"][10] is not config
    assert type(w["source_args"][10]) is runner.Config
    assert w["source_args"][11] is not source_budget
    assert type(w["source_args"][11]) is runner.Budget
    assert tuple(
        getattr(w["source_args"][11], field.name) for field in dataclasses.fields(runner.Budget)
    ) == expected_source
    assert w["grade_state"].budget is not grade_budget_
    assert type(w["grade_state"].budget) is program.GradeBudget
    # The complete result retains the exact values those gates used.
    assert result.config == ("admitted-config", "admitted-declaration")
    assert result.source_budget == expected_source
    assert result.grade_budget == expected_grade
    assert 0 not in result.source_budget and 0 not in result.grade_budget
    assert (result.source_work, result.source_payload) == (
        w["meters"][0].work, w["meters"][0].payload
    )
    assert (result.grade_work, result.grade_payload) == (
        w["meters"][1].work, w["meters"][1].payload
    )
    assert ctx["calls"] == []


def test_snapshot_work_is_bound_by_entry_deadline_before_wire(monkeypatch):
    state = patched_clock(monkeypatch)
    ctx = setup(monkeypatch, 2)
    w = witness(monkeypatch)
    spy_closed = runner._closed
    advanced = [False]

    def closed_config_and_advance(value, record_type):
        result = spy_closed(value, record_type)
        if record_type is runner.Config and not advanced[0]:
            advanced[0] = True
            state["t"] += 65.0
        return result

    monkeypatch.setattr(runner, "_closed", closed_config_and_advance)
    # Early stable positive: the 65 ms of snapshot work stays inside.
    result = invoke(ctx, raw_for(ctx), deadline_ms=120000)
    assert result.config == (ctx["kwargs"]["config"].config_id,
                             ctx["kwargs"]["config"].declaration_id)
    assert phases(w) == ["wire", "wire", "source", "source", "grade", "grade"]
    assert ctx["calls"] == []
    # Late fixed refusal: the same 65 ms exhausts a 50 ms entry deadline
    # before any wire, source or grade boundary is reached.
    state["t"] = 1000.0
    advanced[0] = False
    offset = len(w["events"])
    deadlines_before = len(w["deadlines"])
    with pytest.raises(preflight.PreparationError) as excinfo:
        invoke(ctx, raw_for(ctx), deadline_ms=50)
    assert excinfo.value.__cause__ is None and excinfo.value.__context__ is None
    assert w["events"][offset:] == []
    assert len(w["deadlines"]) == deadlines_before + 1
    assert ctx["calls"] == []
