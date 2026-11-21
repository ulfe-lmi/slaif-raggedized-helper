"""Narrowly private joint declaration preparation for declared evaluation.

This module is under construction; it does not expose a product interface.

``_prepare_declaration`` binds the three accepted declaration envelopes in
one bounded pass: the exact evaluation plan wire admission, the genuine
source cohort declaration admission, and the actual grade declaration
preparation against the exact same admitted dataset and ordered selected
values.  One existing source ``_Deadline`` with its documented positive
bounded range (an ``int`` of 1..1200000 milliseconds) is created at entry,
before the wire phase, and used through return; an out-of-range deadline
is refused before the wire, and each phase checks the remaining time.

The entry takes raw grade plan wire bytes (never a pre-admitted Plan) and
the existing closed source declaration inputs, including the existing
owner references and the separate source and grade budgets.  It exposes no
alternate caller clock, callable or pre-admitted Plan.  A prepared
declaration is returned only after every declared case and the complete
grade scope have passed; passing the first preparation step alone does not
qualify a request.  The exact nominal config, source budget and grade
budget are checked and snapshotted to owned primitive values before their
admission; the genuine gates run on those owned nominal records, and the
result couples the admitted identities, the selected data and the measured
declarations, retaining the exact validated per-case encoder-identifier
tuples tied to the selected order, the exact validated Gold bundle ID
tuple, and the pre-admission config, source budget and grade budget
snapshots in field order, without raw caller-owned mutable state.
No pin, privileged source, encoder, producer,
scorer, report or publication work occurs; physical I/O, question
encoding, current-policy matching, ranking and grading remain with their
dedicated owners.
"""

from dataclasses import dataclass, fields

from . import evaluation_plan_wire as wire
from . import evaluation_program as program
from . import source_cohort_runner as source
from . import text_evaluation_dataset as dataset_module

_MESSAGE = "private evaluation preparation refused"


class PreparationError(ValueError):
    """Fixed ordinary content-free refusal of the paired preparation."""

    __slots__ = ()

    def __init__(self):
        super().__init__(_MESSAGE)


@dataclass(frozen=True, repr=False)
class PreparedDeclaration:
    """The bounded coupled result of the paired declaration preparation."""

    plan: program.Plan
    dataset: dataset_module.Dataset
    selected: tuple
    identifiers: tuple
    gold_ids: tuple
    config: tuple
    source_budget: tuple
    grade_budget: tuple
    selection: str
    source_work: int
    source_payload: int
    grade_work: int
    grade_payload: int
    entries: int
    minimum_work: int
    minimum_payload: int


def _prepare_declaration(
    plan_wire,
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
    source_budget,
    grade_budget,
    *,
    deadline_ms,
):
    """Bind wire admission, source declaration admission and grade preparation.

    The exact ``evaluation_plan_wire.admit`` runs first, then the genuine
    source cohort ``_declaration_admission`` with its preserved binder calls
    and meter, then the actual grade ``_prepare_plan`` against the exact
    same admitted dataset and ordered selected values with its separate
    nominal grade budget.  One ``_Deadline`` (the documented positive
    bounded range) is created at entry from the process monotonic clock,
    before any snapshot or admission work, and bounds the preparation
    through return.  It is checked after the pre-admission snapshots
    and before the genuine wire call, so late snapshot time reaches no
    wire, source or grade boundary.  The exact nominal config, source
    budget and grade budget are checked and snapshotted to owned
    primitive values before admission, and the genuine gates run on
    those owned nominal records.

    Every ordinary exception inside the preparation is translated, after the
    caught handler has left, into the fixed :class:`PreparationError`
    without a retained cause; the fixed clock is checked again after the
    prepared result is assembled so a late usable output is refused;
    ``BaseException`` interruption identities propagate unchanged.
    """
    import time

    refused = False
    result = None
    try:
        clock = source._Deadline(time.monotonic(), deadline_ms)
        result, _state = _prepare_declaration_body(
            plan_wire,
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
            source_budget,
            grade_budget,
            clock,
        )
        # The fixed clock is checked after the prepared result is assembled:
        # a late usable output is refused before it can leave the entry.
        clock.check()
    except Exception:
        refused = True
    if refused:
        # Raised after the caught handler has left, so this boundary does not
        # retain the caught ordinary error as context; from None keeps the
        # suppression explicit.
        raise PreparationError() from None
    return result


def _prepare_declaration_body(
    plan_wire,
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
    source_budget,
    grade_budget,
    clock,
):
    """The existing private preparation body under one already-owned clock.

    The exact nominal config, source budget and grade budget are checked
    and snapshotted to owned primitive values before their admission, the
    genuine wire admission, the genuine source cohort declaration
    admission and the actual grade preparation run on those owned nominal
    records, all under the one caller-owned ``source._Deadline``.  No
    clock is constructed here; the returned internal grade state carries
    the bounded grade meter for the grade computation.
    """
    if type(identifiers) is not tuple:
        raise ValueError
    if not source._closed(config, source.Config):
        raise ValueError
    config_snapshot = (config.config_id, config.declaration_id)
    config_record = source.Config(*config_snapshot)
    if not source._closed(source_budget, source.Budget):
        raise ValueError
    source_budget_snapshot = tuple(
        getattr(source_budget, field.name) for field in fields(source.Budget)
    )
    source_budget_record = source.Budget(*source_budget_snapshot)
    if not source._closed(grade_budget, program.GradeBudget):
        raise ValueError
    grade_budget_snapshot = tuple(
        getattr(grade_budget, field.name) for field in fields(program.GradeBudget)
    )
    grade_budget_record = program.GradeBudget(*grade_budget_snapshot)
    clock.check()
    plan = wire.admit(plan_wire)
    clock.check()
    dataset, selected, selection, source_meter = source._declaration_admission(
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
        config_record,
        source_budget_record,
        clock,
    )
    clock.check()
    state = program._State(plan, grade_budget_record)
    entries, minimum_work, minimum_payload = program._prepare_plan(
        state, dataset, selected, clock
    )
    result = PreparedDeclaration(
        plan,
        dataset,
        selected,
        identifiers,
        gold_ids,
        config_snapshot,
        source_budget_snapshot,
        grade_budget_snapshot,
        selection,
        source_meter.work,
        source_meter.payload,
        state.meter.work,
        state.meter.payload,
        entries,
        minimum_work,
        minimum_payload,
    )
    return result, state
