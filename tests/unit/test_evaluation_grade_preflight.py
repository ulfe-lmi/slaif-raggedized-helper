"""Private bounded evidence for the query-independent grade declaration slice.

Every witness here is a test-local delegating wrapper: it invokes the real
private function unchanged and records call order, arguments and meter state.
No witness re-implements admission, and no source, query, pin or catalog
delegate is invoked by any case in this module.
"""

import dataclasses
import time
from dataclasses import fields
from pathlib import Path

import pytest

import test_source_cohort_runner as fixture
from slaif_raggedized_helper import evaluation_program as program
from slaif_raggedized_helper import source_bound_stage_loss as binder
from slaif_raggedized_helper import source_cohort_runner as runner

_GOLD = ((("sha256:" + "1" * 64, 2),), (("sha256:" + "2" * 64, 1),))


def _admitted(monkeypatch, count):
    """Real bounded synthetic declarations admitted through the runner entry."""
    args, kwargs, calls, captured = fixture.controlled(monkeypatch, count)
    clock = runner._Deadline(time.monotonic(), kwargs["deadline_ms"])
    dataset, selected, selection, _input_meter = runner._input_admission(
        *args,
        kwargs["grants"],
        kwargs["restrictions"],
        kwargs["config"],
        kwargs["budget"],
        clock,
    )
    return args, kwargs, calls, captured, dataset, selected, selection, clock


def _plan(dataset, captured, judgments):
    return program.Plan(
        "plan",
        dataset.dataset_id,
        dataset.split_id,
        captured.pointer.snapshot_id,
        captured.pointer.generation,
        "sha256:" + "c" * 64,
        "protocol",
        "UNJUDGED_AS_ZERO_DIAGNOSTIC",
        "EXPLICIT_CHUNK_IDS_ONLY",
        (20, 60),
        judgments,
    )


def _judgments(count, golds):
    return tuple(
        program.Judgments(f"case{index:03}", tuple(gold)) for index, gold in enumerate(golds)
    )


def _budget():
    return program.GradeBudget(*program._MAX_BUDGET)


def _shift(point, delta):
    return (point[0] + delta[0], point[1] + delta[1])


def _delta(before, after):
    return (after[0] - before[0], after[1] - before[1])


def test_assigned_worktree_import_proof():
    """The physical import must resolve inside the assigned worktree tree."""
    here = Path(__file__).resolve()
    root = here.parents[2]
    assert here.parent.is_relative_to(root / "tests" / "unit")
    expected = root / "src" / "slaif_raggedized_helper" / "evaluation_program.py"
    assert Path(program.__file__).resolve() == expected


def test_declaration_helper_argument_shape():
    code = program._prepare_plan.__code__
    assert code.co_argcount == 4
    assert code.co_varnames[: code.co_argcount] == ("state", "dataset", "selected", "clock")
    for name in (
        "queries",
        "query",
        "payload",
        "expected",
        "pin",
        "catalog",
        "dispatch",
        "gold",
        "cohort",
        "config",
        "selection",
    ):
        assert name not in code.co_varnames


def test_private_preparation_exact_metered_declaration(monkeypatch):
    (_args, _kwargs, calls, captured, dataset, selected, _selection, clock) = _admitted(
        monkeypatch, 2
    )
    plan = _plan(dataset, captured, _judgments(2, _GOLD))
    budget = _budget()
    state = program._State(plan, budget)
    admission_args = []
    real_admission = program._plan_admission

    def admission(*a, **kw):
        admission_args.append(a)
        result = real_admission(*a, **kw)
        return result

    monkeypatch.setattr(program, "_plan_admission", admission)
    entries, minimum_work, minimum_payload = program._prepare_plan(
        state, dataset, selected, clock
    )

    assert len(admission_args) == 1
    assert admission_args[0] == (plan, budget, dataset, selected, state.meter, clock)
    assert type(state.meter) is runner._Meter
    # The helper meters nothing beyond the shared admission: the returned meter
    # state equals the admission's own exit state.
    assert (state.meter.work, state.meter.payload) > (0, 0)
    reference = runner._Meter(budget.local_work, budget.local_payload, clock.check)
    entries_w, _work_w, report_bound = real_admission(
        plan, budget, dataset, selected, reference, clock
    )
    assert entries == entries_w == 60 * len(selected) + sum(len(gold) for gold in _GOLD)
    n = len(selected)
    grades = entries_w - 60 * n
    assert minimum_work == 4000000 + 220000 * n + 8000 * grades + 16 * report_bound
    assert minimum_payload == 12000000 + 220000 * n + 12000 * grades + 16 * report_bound
    # Post-preparation expected/reserve state is unchanged by the declaration.
    assert state.expected == ()
    assert state.reserve_work == 0 and state.reserve_payload == 0
    assert state.plan_identity is None and state.phase is None
    assert calls == []
    # The helper's meter and the shared admission's exit state agree exactly.
    assert (state.meter.work, state.meter.payload) == (reference.work, reference.payload)


@pytest.mark.parametrize(
    "fault",
    [
        lambda p, d, c: dataclasses.replace(p, dataset_id="sha256:" + "0" * 64),
        lambda p, d, c: dataclasses.replace(p, split_id="sha256:" + "0" * 64),
        lambda p, d, c: dataclasses.replace(p, generation=True),
        lambda p, d, c: dataclasses.replace(p, cutoffs=(20, 20, 60)),
        lambda p, d, c: dataclasses.replace(p, cutoffs=(60,)),
        lambda p, d, c: dataclasses.replace(p, judgments=p.judgments[:-1]),
        lambda p, d, c: dataclasses.replace(
            p, judgments=(program.Judgments("case009", p.judgments[0].gold), p.judgments[1])
        ),
        lambda p, d, c: dataclasses.replace(
            p,
            judgments=(
                p.judgments[0],
                program.Judgments("case001", (("sha256:" + "1" * 64, 4),)),
            ),
        ),
        lambda p, d, c: dataclasses.replace(
            p,
            judgments=(
                p.judgments[0],
                program.Judgments(
                    "case001", (("sha256:" + "3" * 64, 1), ("sha256:" + "2" * 64, 1))
                ),
            ),
        ),
    ],
)
def test_private_preparation_bad_plan_refuses_before_identity(monkeypatch, fault):
    (_args, _kwargs, calls, captured, dataset, selected, _selection, clock) = _admitted(
        monkeypatch, 2
    )
    plan = fault(_plan(dataset, captured, _judgments(2, _GOLD)), dataset, captured)
    state = program._State(plan, _budget())
    hash_calls = []

    def forbidden_hash(*a, **kw):
        hash_calls.append(a)

    monkeypatch.setattr(binder, "_canonical_hash", forbidden_hash)
    with pytest.raises(ValueError):
        program._prepare_plan(state, dataset, selected, clock)
    assert hash_calls == [] and calls == []
    # The partial-refusal boundary is observable and exactly matches the shared
    # admission's own refusal boundary on a fresh meter.
    assert state.meter is not None
    reference = runner._Meter(state.budget.local_work, state.budget.local_payload, clock.check)
    with pytest.raises(ValueError):
        program._plan_admission(plan, state.budget, dataset, selected, reference, clock)
    assert (state.meter.work, state.meter.payload) == (reference.work, reference.payload)
    assert state.expected == ()
    assert state.reserve_work == 0 and state.reserve_payload == 0
    assert state.plan_identity is None and state.phase is None


def test_private_preparation_bad_budget_refuses_before_meter(monkeypatch):
    (_args, _kwargs, calls, captured, dataset, selected, _selection, clock) = _admitted(
        monkeypatch, 2
    )
    plan = _plan(dataset, captured, _judgments(2, _GOLD))

    class Derived(program.GradeBudget):
        pass

    for budget in (Derived(*program._MAX_BUDGET), dataclasses.replace(_budget(), local_work=True)):
        state = program._State(plan, budget)
        with pytest.raises(ValueError):
            program._prepare_plan(state, dataset, selected, clock)
        assert state.meter is None
        assert state.expected == () and state.reserve_work == 0
        assert state.reserve_payload == 0 and state.plan_identity is None
    assert calls == []


def test_private_preparation_envelope_shortfall_refuses_at_boundary(monkeypatch):
    (_args, _kwargs, calls, captured, dataset, selected, _selection, clock) = _admitted(
        monkeypatch, 2
    )
    plan = _plan(dataset, captured, _judgments(2, _GOLD))
    budget = _budget()
    reference = program._State(plan, budget)
    entries, minimum_work, minimum_payload = program._prepare_plan(
        reference, dataset, selected, clock
    )
    work_used, payload_used = reference.meter.work, reference.meter.payload

    for field, limit in (
        ("local_work", work_used + minimum_work - 1),
        ("local_payload", payload_used + minimum_payload - 1),
    ):
        state = program._State(plan, dataclasses.replace(budget, **{field: limit}))
        with pytest.raises(ValueError):
            program._prepare_plan(state, dataset, selected, clock)
        # The refusal happens at the same partial-refusal boundary as the
        # reference admission: no envelope reservation is ever metered.
        assert (state.meter.work, state.meter.payload) == (work_used, payload_used)
        assert state.expected == ()
        assert state.reserve_work == 0 and state.reserve_payload == 0
        assert state.plan_identity is None and state.phase is None
    assert entries == 60 * len(selected) + sum(len(gold) for gold in _GOLD)
    assert calls == []


def _legacy_witness(monkeypatch, state):
    """Delegating witnesses recording order, args, meter and captured returns."""
    events = []
    returns = {}
    real_prepare_plan = program._prepare_plan
    real_admission = program._plan_admission
    real_expected = program._expected_queries
    real_hash = binder._canonical_hash

    def sample():
        meter = state.meter
        return None if meter is None else (meter.work, meter.payload)

    def prepare_plan(*a, **kw):
        events.append(("prepare_plan", "in", sample()))
        result = real_prepare_plan(*a, **kw)
        returns["prepare_plan"] = result
        events.append(("prepare_plan", "out", sample()))
        return result

    def admission(*a, **kw):
        events.append(("plan_admission", "in", sample(), a))
        result = real_admission(*a, **kw)
        returns["plan_admission"] = result
        events.append(("plan_admission", "out", sample()))
        return result

    def expected(*a, **kw):
        events.append(("expected_queries", "in", sample()))
        result = real_expected(*a, **kw)
        returns["expected_queries"] = result
        events.append(("expected_queries", "out", sample()))
        return result

    def canonical(value, domain, meter, check, **kw):
        events.append(("canonical_hash", "in", kw.get("limit"), sample()))
        result = real_hash(value, domain, meter, check, **kw)
        events.append(("canonical_hash", "out", kw.get("limit"), sample()))
        return result

    monkeypatch.setattr(program, "_prepare_plan", prepare_plan)
    monkeypatch.setattr(program, "_plan_admission", admission)
    monkeypatch.setattr(program, "_expected_queries", expected)
    monkeypatch.setattr(binder, "_canonical_hash", canonical)
    return events, returns, real_hash


def _identity_preimage(plan, dataset, cohort, selection, config, queries, expected,
                       gold_ids, source_budget, grade_budget):
    """The declared plan identity preimage, built by the test itself."""
    query_records = tuple(
        {
            "case_id": query.case_id,
            "query_id": value[0],
            "question_sha256": value[1],
            "payload_sha256": value[2],
            "original_authority_sha256": value[3],
            "effective_authority_sha256": value[4],
            "space_id": query.space_id,
            "definition_fingerprint": query.definition_fingerprint,
            "policy_id": query.policy_id,
            "execution_fingerprint": query.execution_fingerprint,
        }
        for query, value in zip(queries, expected, strict=True)
    )
    return {
        "schema": "slaif-graded-evaluation-plan-v1",
        "plan": {
            field.name: getattr(plan, field.name)
            for field in fields(program.Plan)
            if field.name != "judgments"
        },
        "judgments": tuple((item.case_id, item.gold) for item in plan.judgments),
        "dataset_id": dataset.dataset_id,
        "split_id": dataset.split_id,
        "cohort": (cohort.split, cohort.case_ids),
        "selection": selection,
        "config": (config.config_id, config.declaration_id),
        "queries": query_records,
        "gold_bundle_ids": gold_ids,
        "source_budget": tuple(
            getattr(source_budget, field.name) for field in fields(runner.Budget)
        ),
        "grade_budget": tuple(
            getattr(grade_budget, field.name) for field in fields(program.GradeBudget)
        ),
    }


def _identity_digest(identity, clock, budget, hasher=None):
    if hasher is None:
        hasher = binder._canonical_hash
    meter = runner._Meter(budget.local_work, budget.local_payload, clock.check)
    return "sha256:" + hasher(
        identity, b"slaif-graded-evaluation-plan-v1\n", meter, clock.check, limit=8388608
    )


def test_legacy_prepare_identity_and_meter_preimage(monkeypatch):
    (args, kwargs, calls, captured, dataset, selected, selection, clock) = _admitted(monkeypatch, 2)
    plan = _plan(dataset, captured, _judgments(2, _GOLD))
    budget = _budget()
    state = program._State(plan, budget)
    events, returns, real_hash = _legacy_witness(monkeypatch, state)

    program._prepare(
        state,
        dataset,
        selected,
        selection,
        args[5],
        args[6],
        args[7],
        kwargs["config"],
        kwargs["budget"],
        clock,
    )

    entered = [event for event in events if event[1] == "in"]
    assert [event[0] for event in entered] == (
        ["prepare_plan", "plan_admission", "expected_queries"] + ["canonical_hash"] * 7
    )
    assert entered[1][3] == (plan, budget, dataset, selected, state.meter, clock)
    # Two authority hashes plus one query identity hash per query, then the plan.
    assert [event[2] for event in entered[3:]] == [262144, 262144, None] * 2 + [8388608]

    def point(name, when):
        return next(event for event in events if event[0] == name and event[1] == when)[2]

    admission_in = point("plan_admission", "in")
    admission_out = point("plan_admission", "out")
    prepare_out = point("prepare_plan", "out")
    identities_in = point("expected_queries", "in")
    identities_out = point("expected_queries", "out")
    assert admission_in == (0, 0)
    assert prepare_out == admission_out  # declaration meters nothing beyond admission
    assert identities_in == admission_out
    entries, _work, _report_bound = returns["plan_admission"]
    fixed = (
        4096 + 256 * len(selected) + 128 * entries,
        4096 + 512 * len(selected) + 256 * entries,
    )
    plan_hash_in = next(
        event
        for event in events
        if event[0] == "canonical_hash" and event[1] == "in" and event[2] == 8388608
    )
    # The fixed charge sits exactly between the identity work and the plan hash.
    assert plan_hash_in[3] == _shift(
        _shift(admission_out, _delta(identities_in, identities_out)), fixed
    )
    # Identity reservations precede the first hash; the meter only accumulates.
    assert entered[3][3] > admission_out
    hash_samples = [event[3] for event in events if event[0] == "canonical_hash"]
    assert all(
        after[0] >= before[0] and after[1] >= before[1]
        for before, after in zip(hash_samples, hash_samples[1:])
    )
    # The last event is the plan identity hash completing; no reservation follows.
    assert events[-1][0] == "canonical_hash" and events[-1][1] == "out"
    assert events[-1][2] == 8388608
    assert (state.meter.work, state.meter.payload) == events[-1][3]
    assert state.meter.work_limit == budget.local_work
    assert state.meter.payload_limit == budget.local_payload

    entries_r, minimum_work, minimum_payload = returns["prepare_plan"]
    assert state.reserve_work == minimum_work and state.reserve_payload == minimum_payload
    assert state.expected == returns["expected_queries"]
    assert calls == []

    # Exact identity preimage: the test builds the declared identity itself from
    # the witnessed query identities and hashes it with the shared primitive.
    expected_identity = _identity_digest(
        _identity_preimage(
            plan,
            dataset,
            args[5],
            selection,
            kwargs["config"],
            args[6],
            returns["expected_queries"],
            args[7],
            kwargs["budget"],
            budget,
        ),
        clock,
        budget,
        hasher=real_hash,
    )
    assert state.plan_identity == expected_identity


def test_legacy_prepare_first_error_before_identity_work(monkeypatch):
    (args, kwargs, calls, captured, dataset, selected, selection, clock) = _admitted(monkeypatch, 2)
    plan = _plan(dataset, captured, _judgments(2, _GOLD))
    budget = _budget()
    faulty = dataclasses.replace(plan, dataset_id="sha256:" + "0" * 64)

    # Bad plan: the first error is the declaration, before any identity work.
    state = program._State(faulty, budget)
    events, _returns, _real_hash = _legacy_witness(monkeypatch, state)
    with pytest.raises(ValueError):
        program._prepare(
            state,
            dataset,
            selected,
            selection,
            args[5],
            args[6],
            args[7],
            kwargs["config"],
            kwargs["budget"],
            clock,
        )
    assert [event[0] for event in events if event[1] == "in"] == [
        "prepare_plan",
        "plan_admission",
    ]
    reference = runner._Meter(
        state.budget.local_work, state.budget.local_payload, clock.check
    )
    with pytest.raises(ValueError):
        program._plan_admission(faulty, budget, dataset, selected, reference, clock)
    assert (state.meter.work, state.meter.payload) == (reference.work, reference.payload)
    assert state.plan_identity is None and state.expected == ()
    assert state.reserve_work == 0 and state.reserve_payload == 0
    assert calls == []


def test_legacy_prepare_envelope_shortfall_before_identity_work(monkeypatch):
    (args, kwargs, calls, captured, dataset, selected, selection, clock) = _admitted(monkeypatch, 2)
    plan = _plan(dataset, captured, _judgments(2, _GOLD))
    budget = _budget()
    reference = program._State(plan, budget)
    _entries, minimum_work, _minimum_payload = program._prepare_plan(
        reference, dataset, selected, clock
    )
    short = dataclasses.replace(budget, local_work=reference.meter.work + minimum_work - 1)
    state = program._State(plan, short)
    events, _returns, _real_hash = _legacy_witness(monkeypatch, state)
    with pytest.raises(ValueError):
        program._prepare(
            state,
            dataset,
            selected,
            selection,
            args[5],
            args[6],
            args[7],
            kwargs["config"],
            kwargs["budget"],
            clock,
        )
    assert [event[0] for event in events if event[1] == "in"] == [
        "prepare_plan",
        "plan_admission",
    ]
    assert (state.meter.work, state.meter.payload) == (
        reference.meter.work,
        reference.meter.payload,
    )
    assert state.plan_identity is None and state.expected == ()
    assert state.reserve_work == 0 and state.reserve_payload == 0
    assert calls == []


def test_legacy_prepare_residual_checked_after_identity_work(monkeypatch):
    (args, kwargs, calls, captured, dataset, selected, selection, clock) = _admitted(monkeypatch, 2)
    plan = _plan(dataset, captured, _judgments(2, _GOLD))
    budget = _budget()
    reference = program._State(plan, budget)
    entries, minimum_work, minimum_payload = program._prepare_plan(
        reference, dataset, selected, clock
    )
    work_used = reference.meter.work
    # The declaration envelope passes exactly; only the after-identity residual
    # check can refuse, so the identity work must have run before the error.
    tight = dataclasses.replace(budget, local_work=work_used + minimum_work)
    state = program._State(plan, tight)
    events, returns, _real_hash = _legacy_witness(monkeypatch, state)
    with pytest.raises(ValueError):
        program._prepare(
            state,
            dataset,
            selected,
            selection,
            args[5],
            args[6],
            args[7],
            kwargs["config"],
            kwargs["budget"],
            clock,
        )
    entered = [event[0] for event in events if event[1] == "in"]
    assert "expected_queries" in entered and entered[-1] == "canonical_hash"
    assert state.plan_identity is not None
    assert state.reserve_work == minimum_work and state.reserve_payload == minimum_payload
    assert returns["prepare_plan"][0] == entries
    assert state.meter.work > work_used
    assert state.phase is None
    assert calls == []


def test_legacy_prepare_budget_snapshot_bound_before_identity_work(monkeypatch):
    """The legacy identity serializes the budget bound before identity work."""
    (args, kwargs, calls, captured, dataset, selected, selection, clock) = _admitted(monkeypatch, 2)
    plan = _plan(dataset, captured, _judgments(2, _GOLD))
    budget = _budget()
    state = program._State(plan, budget)
    # A valid distinct budget swapped in during identity work: a late re-read
    # would serialize it, the exact old snapshot behavior keeps the admitted one.
    swapped = dataclasses.replace(budget, report_bytes=program._MAX_BUDGET[12] - 1)
    identity_returns = []
    real_expected = program._expected_queries

    def expected(*a, **kw):
        result = real_expected(*a, **kw)
        identity_returns.append(result)
        state.budget = swapped
        return result

    monkeypatch.setattr(program, "_expected_queries", expected)
    program._prepare(
        state,
        dataset,
        selected,
        selection,
        args[5],
        args[6],
        args[7],
        kwargs["config"],
        kwargs["budget"],
        clock,
    )
    # The swap really happened during identity work and is identity-relevant.
    assert state.budget is swapped
    common = (
        plan, dataset, args[5], selection, kwargs["config"],
        args[6], identity_returns[0], args[7], kwargs["budget"],
    )
    original_identity = _identity_digest(
        _identity_preimage(*common, budget), clock, budget
    )
    swapped_identity = _identity_digest(
        _identity_preimage(*common, swapped), clock, budget
    )
    assert original_identity != swapped_identity
    assert state.plan_identity == original_identity
    assert calls == []
