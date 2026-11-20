"""Bounded preflight tests for the private source cohort declaration slice.

The expected meter events, charges and final meter states are hard-coded
from the exact base cacc5b3 source (the ``_input_admission`` meter
convention and the accepted binder declaration prefix) as the independent
reference; the committed tests do not run a second copy of the algorithm.
Only synthetic declaration shapes and synthetic dataset bytes are used; no
pin, catalog, producer, vector or source access occurs.
"""

import dataclasses
import hashlib
import inspect
import json
import struct
import time
from pathlib import Path

import pytest

import test_source_cohort_runner as legacy
from slaif_raggedized_helper import source_bound_stage_loss as binder
from slaif_raggedized_helper import source_cohort_runner as runner

DATA_LEN = 646


class ForbiddenBoundary(BaseException):
    pass


def forbid(monkeypatch, module, name):
    def forbidden(*args, **kwargs):
        raise ForbiddenBoundary()

    monkeypatch.setattr(module, name, forbidden)


def record(monkeypatch, module, name, calls):
    real = getattr(module, name)

    def wrapper(*args, **kwargs):
        calls.append(1)
        return real(*args, **kwargs)

    monkeypatch.setattr(module, name, wrapper)


def decl_ids(index):
    return (
        hashlib.sha256(("space-" + str(index)).encode()).hexdigest(),
        "sha256:" + hashlib.sha256(("definition-" + str(index)).encode()).hexdigest(),
        hashlib.sha256(("policy-" + str(index)).encode()).hexdigest(),
        hashlib.sha256(("execution-" + str(index)).encode()).hexdigest(),
    )


def identifiers_for(cohort):
    return tuple(decl_ids(index) for index in range(len(cohort.case_ids)))


class SpyMeter:
    """Delegating spy over the real meter: exact events plus last attempt."""

    def __init__(self, real, events, work_limit, payload_limit, check):
        self.inner = real(work_limit, payload_limit, check)
        self.events = events
        self.last_attempt = None

    def __getattr__(self, name):
        return getattr(self.inner, name)

    def reserve(self, work, payload=0, *, category="local"):
        self.last_attempt = ("reserve", work, payload, category)
        self.inner.reserve(work, payload, category=category)
        self.events.append(self.last_attempt)

    def compare_strings(self, left, right):
        result = self.inner.compare_strings(left, right)
        self.events.append(("compare", len(left), len(right), result))
        return result


_REAL_METER = runner._Meter


def spy_meter(monkeypatch, events, created, made=None):
    def factory(work_limit, payload_limit, check):
        created.append(1)
        spy = SpyMeter(_REAL_METER, events, work_limit, payload_limit, check)
        if made is not None:
            made.append(spy)
        return spy

    monkeypatch.setattr(runner, "_Meter", factory)


def declaration_args(monkeypatch, count=1):
    args, kwargs, calls, _ = legacy.controlled(monkeypatch, count)
    (originals, derived, root, owner, data, cohort, queries, gold_ids) = args
    return args, kwargs, calls


def no_source_boundaries(monkeypatch):
    for module, name in (
        (runner, "_owner_check"),
        (runner, "_produce"),
        (runner, "_bind"),
        (runner, "_pin_observation"),
        (runner, "_aggregate"),
        (binder, "_preflight_inputs"),
    ):
        forbid(monkeypatch, module, name)


# Exact reference for the valid one-case declaration: meter events in order,
# then final totals.  Fixed prefix, per-case envelope, accepted binder
# declaration prefix, dataset and selection/authority meter convention.
VALID_EVENTS = [
    ("reserve", 4096, 4096, "local"),  # fixed content-free failure prefix
    ("reserve", 32, 1024, "local"),    # fixed closed input records
    ("reserve", 1, 0, "local"),        # config_id shape
    ("reserve", 4, 0, "local"),        # config_id "cfg"
    ("reserve", 1, 0, "local"),        # declaration_id shape
    ("reserve", 12, 0, "local"),       # declaration_id "declaration"
    ("reserve", 1024, 1024, "local"),  # case envelope
    ("reserve", 8, 0, "local"),        # case id "case000"
    ("reserve", 9, 32, "local"),       # root "/fixture" utf-8
    ("reserve", 9, 0, "local"),        # root slash count
    ("reserve", 9, 8224, "local"),     # root components
    ("reserve", 8, 0, "local"),        # case id grammar
    ("reserve", 1, 0, "local"),        # ident[0] shape
    ("reserve", 65, 0, "local"),       # ident[0] grammar
    ("reserve", 1, 0, "local"),        # ident[1] shape
    ("reserve", 72, 0, "local"),       # ident[1] grammar, sha256: prefix
    ("reserve", 1, 0, "local"),        # ident[2] shape
    ("reserve", 65, 0, "local"),       # ident[2] grammar
    ("reserve", 1, 0, "local"),        # ident[3] shape
    ("reserve", 65, 0, "local"),       # ident[3] grammar
    ("reserve", 647, 646, "local"),    # dataset bytes before parse
    ("reserve", 647, 0, "local"),      # dataset bytes after parse
    ("reserve", 648, 128, "local"),    # case envelope before selection
    ("reserve", 1, 0, "local"),        # dataset case in selection
    ("reserve", 1, 128, "local"),      # split membership
    ("compare", 7, 7, 0),              # declared case id match
    ("reserve", 1, 0, "local"),        # authority: grants record
    ("reserve", 1, 0, "local"),        # corpora field
    ("reserve", 1, 0, "local"),        # corpora entry shape
    ("reserve", 5, 16, "local"),       # corpora entry "demo"
    ("reserve", 1, 0, "local"),        # versions field
    ("reserve", 1, 0, "local"),        # versions entry shape
    ("reserve", 5, 16, "local"),       # versions entry "v1.2"
    ("reserve", 1, 0, "local"),        # labels field
    ("reserve", 1, 0, "local"),        # labels entry shape
    ("reserve", 5, 16, "local"),       # labels entry "test"
    ("reserve", 1, 512, "local"),      # grants section close
    ("reserve", 1, 0, "local"),        # restrictions record, None
    ("reserve", 1, 128, "local"),      # corpora intersection source
    ("reserve", 1, 0, "local"),        # corpora candidate
    ("compare", 4, 4, 0),              # corpora retained
    ("reserve", 1, 128, "local"),      # versions intersection source
    ("reserve", 1, 0, "local"),        # versions candidate
    ("compare", 4, 4, 0),              # versions retained
    ("reserve", 1, 128, "local"),      # labels intersection source
    ("reserve", 1, 0, "local"),        # labels candidate
    ("compare", 4, 4, 0),              # labels retained
    ("reserve", 4, 512, "local"),      # authority close
    ("reserve", 4, 512, "local"),      # selected case stored
    ("reserve", 2, 128, "local"),      # final selection reserve
]
VALID_WORK = 7552
VALID_PAYLOAD = 17398
OLD_ADMISSION_WORK = 15775
OLD_ADMISSION_PAYLOAD = 152566
# Old-path per-case extras over the declaration path: the query identity
# compare (2 * (7 + 7 + 1) work for "case000") and the legacy vector reserve.
QUERY_COMPARE_WORK = 30
VECTOR_RESERVE = (8193, 135168)

# Old-path per-case prefix through the vector reservation, in order.
OLD_CASE_EVENTS = [
    ("reserve", 1024, 1024, "local"),
    ("compare", 7, 7, 0),
    ("reserve", 8, 0, "local"),
    ("reserve", 9, 32, "local"),
    ("reserve", 9, 0, "local"),
    ("reserve", 9, 8224, "local"),
    ("reserve", 8, 0, "local"),
    ("reserve", 1, 0, "local"),
    ("reserve", 65, 0, "local"),
    ("reserve", 1, 0, "local"),
    ("reserve", 72, 0, "local"),
    ("reserve", 1, 0, "local"),
    ("reserve", 65, 0, "local"),
    ("reserve", 1, 0, "local"),
    ("reserve", 65, 0, "local"),
    ("reserve", 8193, 135168, "local"),
]


def test_cohort_runner_import_originates_from_test_module_checkout():
    test_file = Path(__file__).resolve()
    root = test_file.parents[2]
    assert Path(runner.__file__).resolve() == (
        root / "src" / "slaif_raggedized_helper" / "source_cohort_runner.py"
    ).resolve()
    assert Path(binder.__file__).resolve() == (
        root / "src" / "slaif_raggedized_helper" / "source_bound_stage_loss.py"
    ).resolve()


def test_declaration_admission_has_no_query_or_payload_parameter():
    parameters = inspect.signature(runner._declaration_admission).parameters
    assert "queries" not in parameters
    assert "payload" not in parameters
    assert "identifiers" in parameters


def test_valid_declaration_admits_full_split_without_vector_pin_or_producer(monkeypatch):
    args, kwargs, calls = declaration_args(monkeypatch)
    (originals, derived, root, owner, data, cohort, _queries, gold_ids) = args
    no_source_boundaries(monkeypatch)
    events, created = [], []
    spy_meter(monkeypatch, events, created)
    dataset, selected, selection, meter = runner._declaration_admission(
        originals,
        derived,
        root,
        owner,
        data,
        cohort,
        identifiers_for(cohort),
        gold_ids,
        kwargs["grants"],
        kwargs["restrictions"],
        kwargs["config"],
        kwargs["budget"],
        runner._Deadline(time.monotonic(), 120000),
    )
    assert calls == []
    assert len(created) == 1
    assert events == VALID_EVENTS
    assert (meter.work, meter.payload) == (VALID_WORK, VALID_PAYLOAD)
    assert selection == "FULL_ADMITTED_SPLIT"
    assert dataset.canonical_bytes == data
    assert dataset.case_count == len(cohort.case_ids)
    assert tuple(case.case_id for case, *_ in selected) == cohort.case_ids
    for case, original, effective, restricted in selected:
        assert original == kwargs["grants"] and original is not kwargs["grants"]
        assert restricted is None
        assert effective.corpora == case.scope.corpora
        assert effective.versions == case.scope.versions
        assert effective.labels == case.scope.labels


def test_declaration_declares_subset_selection(monkeypatch):
    args, kwargs, calls = declaration_args(monkeypatch, 3)
    (originals, derived, root, owner, data, cohort, _queries, gold_ids) = args
    no_source_boundaries(monkeypatch)
    subset = runner.Cohort(cohort.split, (cohort.case_ids[0], cohort.case_ids[2]))
    dataset, selected, selection, _meter = runner._declaration_admission(
        originals,
        derived,
        root,
        owner,
        data,
        subset,
        (decl_ids(0), decl_ids(2)),
        gold_ids,
        kwargs["grants"],
        kwargs["restrictions"],
        kwargs["config"],
        kwargs["budget"],
        runner._Deadline(time.monotonic(), 120000),
    )
    assert calls == []
    assert selection == "DECLARED_SUBSET"
    assert dataset.case_count == 3
    assert tuple(case.case_id for case, *_ in selected) == subset.case_ids
    for case, original, effective, restricted in selected:
        assert original == kwargs["grants"] and original is not kwargs["grants"]
        assert effective.corpora == case.scope.corpora
        assert effective.versions == case.scope.versions
        assert effective.labels == case.scope.labels


def test_both_entries_invoke_the_shared_private_admission_pieces(monkeypatch):
    args, kwargs, calls = declaration_args(monkeypatch)
    (originals, derived, root, owner, data, cohort, queries, gold_ids) = args
    for module, name in (
        (runner, "_pin_observation"),
        (runner, "_produce"),
        (runner, "_bind"),
        (runner, "_aggregate"),
    ):
        forbid(monkeypatch, module, name)
    envelope_calls, grammar_calls, tail_calls = [], [], []
    record(monkeypatch, runner, "_envelope_closed", envelope_calls)
    record(monkeypatch, runner, "_case_id_grammar", grammar_calls)
    record(monkeypatch, runner, "_dataset_selection_tail", tail_calls)
    old = runner._input_admission(
        *args,
        kwargs["grants"],
        kwargs["restrictions"],
        kwargs["config"],
        kwargs["budget"],
        runner._Deadline(time.monotonic(), 120000),
    )
    assert calls == []
    assert envelope_calls == [1]
    assert grammar_calls == [1]
    assert tail_calls == [1]
    envelope_calls.clear()
    grammar_calls.clear()
    tail_calls.clear()
    forbid(monkeypatch, binder, "_preflight_inputs")
    new = runner._declaration_admission(
        originals,
        derived,
        root,
        owner,
        data,
        cohort,
        identifiers_for(cohort),
        gold_ids,
        kwargs["grants"],
        kwargs["restrictions"],
        kwargs["config"],
        kwargs["budget"],
        runner._Deadline(time.monotonic(), 120000),
    )
    assert calls == []
    assert envelope_calls == [1]
    assert grammar_calls == [1]
    assert tail_calls == [1]
    # The shared tail returns the identical admitted evidence; the only
    # meter difference is the legacy query identity compare and vector.
    assert new[0] == old[0]
    assert new[1] == old[1]
    assert new[2] == old[2]
    assert old[3].work - new[3].work == QUERY_COMPARE_WORK + VECTOR_RESERVE[0]
    assert old[3].payload - new[3].payload == VECTOR_RESERVE[1]


def test_declaration_evidence_matches_old_admission_with_exact_meter_delta(monkeypatch):
    args, kwargs, _calls = declaration_args(monkeypatch)
    (originals, derived, root, owner, data, cohort, queries, gold_ids) = args
    old_dataset, old_selected, old_selection, old_meter = runner._input_admission(
        originals,
        derived,
        root,
        owner,
        data,
        cohort,
        queries,
        gold_ids,
        kwargs["grants"],
        kwargs["restrictions"],
        kwargs["config"],
        kwargs["budget"],
        runner._Deadline(time.monotonic(), 120000),
    )
    new_dataset, new_selected, new_selection, new_meter = runner._declaration_admission(
        originals,
        derived,
        root,
        owner,
        data,
        cohort,
        identifiers_for(cohort),
        gold_ids,
        kwargs["grants"],
        kwargs["restrictions"],
        kwargs["config"],
        kwargs["budget"],
        runner._Deadline(time.monotonic(), 120000),
    )
    assert new_dataset == old_dataset
    assert new_selected == old_selected
    assert new_selection == old_selection
    assert (old_meter.work, old_meter.payload) == (OLD_ADMISSION_WORK, OLD_ADMISSION_PAYLOAD)
    assert (new_meter.work, new_meter.payload) == (VALID_WORK, VALID_PAYLOAD)
    assert old_meter.work - new_meter.work == QUERY_COMPARE_WORK + VECTOR_RESERVE[0]
    assert old_meter.payload - new_meter.payload == VECTOR_RESERVE[1]


@pytest.mark.parametrize(
    "mutate",
    [
        "identifiers_list",
        "identifiers_length",
        "case_ids_list",
        "data_str",
        "foreign_config",
    ],
)
def test_full_shape_refusal_at_zero_meter_before_delegate_and_source(monkeypatch, mutate):
    args, kwargs, calls = declaration_args(monkeypatch)
    (originals, derived, root, owner, data, cohort, _queries, gold_ids) = args
    identifiers = identifiers_for(cohort)
    if mutate == "identifiers_list":
        identifiers = list(identifiers)
    elif mutate == "identifiers_length":
        identifiers = (identifiers[0], identifiers[0])
    elif mutate == "case_ids_list":
        cohort = runner.Cohort(cohort.split, list(cohort.case_ids))
    elif mutate == "data_str":
        data = data.decode("ascii")
    elif mutate == "foreign_config":
        kwargs = dict(kwargs, config=object())
    no_source_boundaries(monkeypatch)
    delegate, dataset_calls = [], []
    record(monkeypatch, binder, "_preflight_declaration", delegate)
    record(monkeypatch, runner, "_admit_dataset", dataset_calls)
    events, created = [], []
    spy_meter(monkeypatch, events, created)
    with pytest.raises(ValueError):
        runner._declaration_admission(
            originals,
            derived,
            root,
            owner,
            data,
            cohort,
            identifiers,
            gold_ids,
            kwargs["grants"],
            kwargs["restrictions"],
            kwargs["config"],
            kwargs["budget"],
            runner._Deadline(time.monotonic(), 120000),
        )
    assert created == []
    assert events == []
    assert delegate == []
    assert dataset_calls == []
    assert calls == []


@pytest.mark.parametrize(
    "field,value",
    [("local_work", 0), ("binder_work", 134217727)],
)
def test_budget_shortfall_and_precharge_refuse_before_dataset_and_source(
    monkeypatch, field, value
):
    args, kwargs, calls = declaration_args(monkeypatch)
    (originals, derived, root, owner, data, cohort, _queries, gold_ids) = args
    kwargs = dict(kwargs, budget=dataclasses.replace(kwargs["budget"], **{field: value}))
    no_source_boundaries(monkeypatch)
    delegate, dataset_calls = [], []
    record(monkeypatch, binder, "_preflight_declaration", delegate)
    record(monkeypatch, runner, "_admit_dataset", dataset_calls)
    events, created, made = [], [], []
    spy_meter(monkeypatch, events, created, made)
    with pytest.raises(ValueError):
        runner._declaration_admission(
            originals,
            derived,
            root,
            owner,
            data,
            cohort,
            identifiers_for(cohort),
            gold_ids,
            kwargs["grants"],
            kwargs["restrictions"],
            kwargs["config"],
            kwargs["budget"],
            runner._Deadline(time.monotonic(), 120000),
        )
    if field == "binder_work":
        # The exact floor check refuses before the meter exists.
        assert created == []
        assert made == []
    else:
        # The zero local budget refuses at the fixed failure-prefix
        # precharge; a refused reserve records no event.
        assert created == [1]
        assert len(made) == 1
        assert made[0].last_attempt == ("reserve", 4096, 4096, "local")
        assert (made[0].work, made[0].payload) == (0, 0)
    assert events == []
    assert delegate == []
    assert dataset_calls == []
    assert calls == []


def test_malformed_later_case_declaration_refuses_before_dataset(monkeypatch):
    args, kwargs, calls = declaration_args(monkeypatch, 2)
    (originals, derived, root, owner, data, cohort, _queries, gold_ids) = args
    no_source_boundaries(monkeypatch)
    identifiers = (
        decl_ids(0),
        ("a" * 63, "sha256:" + "a" * 64, "a" * 64, "a" * 64),
    )
    dataset_calls = []
    record(monkeypatch, runner, "_admit_dataset", dataset_calls)
    events, created = [], []
    spy_meter(monkeypatch, events, created)
    with pytest.raises(ValueError):
        runner._declaration_admission(
            originals,
            derived,
            root,
            owner,
            data,
            cohort,
            identifiers,
            gold_ids,
            kwargs["grants"],
            kwargs["restrictions"],
            kwargs["config"],
            kwargs["budget"],
            runner._Deadline(time.monotonic(), 120000),
        )
    assert len(created) == 1
    assert dataset_calls == []
    assert calls == []
    assert events == [
        ("reserve", 4096, 4096, "local"),
        ("reserve", 32, 1024, "local"),
        ("reserve", 1, 0, "local"),
        ("reserve", 4, 0, "local"),
        ("reserve", 1, 0, "local"),
        ("reserve", 12, 0, "local"),
        ("reserve", 1024, 1024, "local"),
        ("reserve", 8, 0, "local"),
        ("reserve", 9, 32, "local"),
        ("reserve", 9, 0, "local"),
        ("reserve", 9, 8224, "local"),
        ("reserve", 8, 0, "local"),
        ("reserve", 1, 0, "local"),
        ("reserve", 65, 0, "local"),
        ("reserve", 1, 0, "local"),
        ("reserve", 72, 0, "local"),
        ("reserve", 1, 0, "local"),
        ("reserve", 65, 0, "local"),
        ("reserve", 1, 0, "local"),
        ("reserve", 65, 0, "local"),
        ("reserve", 1024, 1024, "local"),
        ("reserve", 8, 0, "local"),
        ("compare", 7, 7, -1),
        ("reserve", 9, 32, "local"),
        ("reserve", 9, 0, "local"),
        ("reserve", 9, 8224, "local"),
        ("reserve", 8, 0, "local"),
        ("reserve", 1, 0, "local"),
    ]
    assert events[-1] == ("reserve", 1, 0, "local")
    # The ascending case-id compare charged once (15 work) outside the
    # reserve stream; the reserve stream alone is exact below.
    assert sum(e[1] for e in events if e[0] == "reserve") + 15 == 6567
    assert sum(e[2] for e in events if e[0] == "reserve") == 23680


def test_malformed_dataset_refuses_after_complete_declaration_prefix(monkeypatch):
    args, kwargs, calls = declaration_args(monkeypatch)
    (originals, derived, root, owner, data, cohort, _queries, gold_ids) = args
    no_source_boundaries(monkeypatch)
    corrupt = data[:-1] + b"x"
    assert len(corrupt) == DATA_LEN
    dataset_calls = []
    record(monkeypatch, runner, "_admit_dataset", dataset_calls)
    events, created = [], []
    spy_meter(monkeypatch, events, created)
    with pytest.raises(ValueError):
        runner._declaration_admission(
            originals,
            derived,
            root,
            owner,
            corrupt,
            cohort,
            identifiers_for(cohort),
            gold_ids,
            kwargs["grants"],
            kwargs["restrictions"],
            kwargs["config"],
            kwargs["budget"],
            runner._Deadline(time.monotonic(), 120000),
        )
    assert len(created) == 1
    assert dataset_calls == [1]
    assert calls == []
    assert events == VALID_EVENTS[:21]
    assert events[-1] == ("reserve", 647, 646, "local")
    assert sum(e[1] for e in events if e[0] == "reserve") == 6131
    assert sum(e[2] for e in events if e[0] == "reserve") == 15046


@pytest.mark.parametrize(
    "cohort_case,cohort_split",
    [
        ("zzz999", "tuning"),
        ("case000", "held_out"),
    ],
)
def test_malformed_selection_refuses_before_or_at_authority(
    monkeypatch, cohort_case, cohort_split
):
    args, kwargs, calls = declaration_args(monkeypatch)
    (originals, derived, root, owner, data, cohort, _queries, gold_ids) = args
    no_source_boundaries(monkeypatch)
    subset = runner.Cohort(cohort_split, (cohort_case,))
    authority_calls = []
    record(monkeypatch, binder, "_admit_authority", authority_calls)
    events, created = [], []
    spy_meter(monkeypatch, events, created)
    with pytest.raises(ValueError):
        runner._declaration_admission(
            originals,
            derived,
            root,
            owner,
            data,
            subset,
            (decl_ids(0),),
            gold_ids,
            kwargs["grants"],
            kwargs["restrictions"],
            kwargs["config"],
            kwargs["budget"],
            runner._Deadline(time.monotonic(), 120000),
        )
    assert len(created) == 1
    assert calls == []
    if cohort_case == "zzz999":
        # Declared id absent from the dataset: selection closure fails after
        # the split membership charge and the non-matching compare.
        assert events == [
            *VALID_EVENTS[:6],
            ("reserve", 1024, 1024, "local"),
            ("reserve", 7, 0, "local"),
            ("reserve", 9, 32, "local"),
            ("reserve", 9, 0, "local"),
            ("reserve", 9, 8224, "local"),
            ("reserve", 7, 0, "local"),
            ("reserve", 1, 0, "local"),
            ("reserve", 65, 0, "local"),
            ("reserve", 1, 0, "local"),
            ("reserve", 72, 0, "local"),
            ("reserve", 1, 0, "local"),
            ("reserve", 65, 0, "local"),
            ("reserve", 1, 0, "local"),
            ("reserve", 65, 0, "local"),
            ("reserve", 647, 646, "local"),
            ("reserve", 647, 0, "local"),
            ("reserve", 648, 128, "local"),
            ("reserve", 1, 0, "local"),
            ("reserve", 1, 128, "local"),
            ("compare", 7, 6, -1),
        ]
        assert authority_calls == []
        work = 7440
        payload = 15302
    else:
        # Declared id present but the dataset split disagrees: the split
        # mismatch refuses before any authority delegation.
        assert events == [
            *VALID_EVENTS[:6],
            ("reserve", 1024, 1024, "local"),
            ("reserve", 8, 0, "local"),
            ("reserve", 9, 32, "local"),
            ("reserve", 9, 0, "local"),
            ("reserve", 9, 8224, "local"),
            ("reserve", 8, 0, "local"),
            ("reserve", 1, 0, "local"),
            ("reserve", 65, 0, "local"),
            ("reserve", 1, 0, "local"),
            ("reserve", 72, 0, "local"),
            ("reserve", 1, 0, "local"),
            ("reserve", 65, 0, "local"),
            ("reserve", 1, 0, "local"),
            ("reserve", 65, 0, "local"),
            ("reserve", 647, 646, "local"),
            ("reserve", 647, 0, "local"),
            ("reserve", 648, 128, "local"),
            ("reserve", 1, 0, "local"),
            ("compare", 7, 7, 0),
        ]
        assert authority_calls == []
        work = 7457
        payload = 15174
    assert sum(e[1] for e in events if e[0] == "reserve") + (
        14 if cohort_case == "zzz999" else 30
    ) == work
    assert sum(e[2] for e in events if e[0] == "reserve") == payload


def test_full_shape_and_later_authority_refusals_are_distinguishable(monkeypatch):
    args, kwargs, calls = declaration_args(monkeypatch)
    (originals, derived, root, owner, data, cohort, _queries, gold_ids) = args
    no_source_boundaries(monkeypatch)
    # (1) Full-shape refusal: the envelope gate refuses before the meter is
    # created, before any delegated validator and before the dataset.
    delegate, dataset_calls = [], []
    record(monkeypatch, binder, "_preflight_declaration", delegate)
    record(monkeypatch, runner, "_admit_dataset", dataset_calls)
    events, created = [], []
    spy_meter(monkeypatch, events, created)
    with pytest.raises(ValueError):
        runner._declaration_admission(
            originals,
            derived,
            root,
            owner,
            data,
            cohort,
            list(identifiers_for(cohort)),
            gold_ids,
            kwargs["grants"],
            kwargs["restrictions"],
            kwargs["config"],
            kwargs["budget"],
            runner._Deadline(time.monotonic(), 120000),
        )
    assert created == []
    assert events == []
    assert delegate == []
    assert dataset_calls == []
    # (2) Later authority refusal: the complete declaration prefix and the
    # admitted dataset pass, then the delegated authority validator refuses
    # the missing grants after exactly its first metered record check.
    authority_calls = []
    record(monkeypatch, binder, "_admit_authority", authority_calls)
    events2, created2 = [], []
    spy_meter(monkeypatch, events2, created2)
    with pytest.raises(ValueError):
        runner._declaration_admission(
            originals,
            derived,
            root,
            owner,
            data,
            cohort,
            identifiers_for(cohort),
            gold_ids,
            None,
            kwargs["restrictions"],
            kwargs["config"],
            kwargs["budget"],
            runner._Deadline(time.monotonic(), 120000),
        )
    assert len(created2) == 1
    assert authority_calls == [1]
    assert calls == []
    assert events2 == VALID_EVENTS[:26] + [
        ("reserve", 1, 0, "local"),  # authority: grants record
    ]
    work2 = (
        sum(e[1] for e in events2 if e[0] == "reserve")
        + 30  # equal case-id compare charged twice
    )
    assert work2 == 7459
    assert sum(e[2] for e in events2 if e[0] == "reserve") == 15302
    assert events2 != events and len(events2) > len(events)


def test_old_path_vector_fault_precedes_dataset_fault(monkeypatch):
    args, kwargs, calls = declaration_args(monkeypatch)
    zero = struct.pack("<1024f", 0.0, *([0.0] * 1023))
    bad = dataclasses.replace(args[6][0], payload=zero)
    corrupt = args[4][:-1] + b"x"
    events, created = [], []
    spy_meter(monkeypatch, events, created)
    dataset_calls = []
    record(monkeypatch, runner, "_admit_dataset", dataset_calls)
    with pytest.raises(runner.CohortRunnerError) as exc:
        runner.run_cohort(*args[:4], corrupt, args[5], (bad,), args[7], **kwargs)
    assert exc.value.progress is None
    assert dataset_calls == []
    assert calls == []
    assert len(created) == 1
    assert events == VALID_EVENTS[:6] + OLD_CASE_EVENTS
    assert events[-1] == ("reserve", 8193, 135168, "local")
    work = sum(e[1] for e in events if e[0] == "reserve") + 30  # equal compare
    assert work == 13707
    assert sum(e[2] for e in events if e[0] == "reserve") == 149568


def test_old_path_dataset_fault_after_full_per_query_preflight(monkeypatch):
    args, kwargs, calls = declaration_args(monkeypatch)
    corrupt = args[4][:-1] + b"x"
    events, created = [], []
    spy_meter(monkeypatch, events, created)
    dataset_calls = []
    record(monkeypatch, runner, "_admit_dataset", dataset_calls)
    with pytest.raises(runner.CohortRunnerError) as exc:
        runner.run_cohort(*args[:4], corrupt, args[5], args[6], args[7], **kwargs)
    assert exc.value.progress is None
    assert dataset_calls == [1]
    assert calls == []
    assert len(created) == 1
    assert events == VALID_EVENTS[:6] + OLD_CASE_EVENTS + [
        ("reserve", 647, 646, "local"),
    ]
    work = sum(e[1] for e in events if e[0] == "reserve") + 30  # equal compare
    assert work == 14354
    assert sum(e[2] for e in events if e[0] == "reserve") == 150214


def test_old_path_report_identity_and_metering_unchanged(monkeypatch):
    args, kwargs, calls, _ = legacy.controlled(monkeypatch)
    report = runner.run_cohort(*args, **kwargs)
    payload = json.loads(report.identity_payload)
    assert payload["selection_kind"] == "FULL_ADMITTED_SPLIT"
    assert payload["progress"] == dict(
        intended=1, attempted=1, completed=1, refused=0, pending=0
    )
    assert report.identity == "sha256:" + legacy.digest(
        b"slaif-source-cohort-runner-v1\n" + report.identity_payload
    )
    assert calls == ["pin", "pin", "producer", "binder"]
