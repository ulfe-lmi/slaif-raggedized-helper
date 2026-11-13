"""Pure, typed boundary fixtures for private snapshot construction."""

from dataclasses import FrozenInstanceError, replace
import hashlib

import pytest

from slaif_raggedized_helper import corpus_embedding_executor as executor
from slaif_raggedized_helper import derived_store
from slaif_raggedized_helper.source_admission import OriginalStore
from slaif_raggedized_helper import raw_snapshot_construction as subject
from slaif_raggedized_helper import raw_snapshot_file_builder as builder
from slaif_raggedized_helper import raw_snapshot_files as files
from slaif_raggedized_helper import raw_snapshot_membership as membership
from slaif_raggedized_helper import raw_snapshot_program_coverage as coverage
from slaif_raggedized_helper import raw_snapshot_publication as publication
from slaif_raggedized_helper import raw_snapshot_rows as rows
from slaif_raggedized_helper import raw_snapshot_selection as selection

SOURCE = "sha256:" + "a" * 64
CORE = b"core"
SNAPSHOT = "sha256:" + hashlib.sha256(CORE).hexdigest()


@pytest.fixture
def boundary(monkeypatch):
    calls = []
    # Exact uninitialized typed stand-ins; all store operations are mocked, no IO.
    original, derived = object.__new__(OriginalStore), object.__new__(derived_store.Store)
    execution = executor.CorpusResult(SOURCE, 1, (), None, None, None)
    covered = coverage.CoveredRowMap(SOURCE, b"map", "m", ("a" * 64,), 1, 1, 1)
    built = builder.BuiltSnapshotFiles(CORE, (("map", b"map"),), SNAPSHOT, 1, 1, 1, "p")
    rowmap = rows.RawRowMap(b"map", "", "", "", "", "", (None,), ())
    members = membership.Membership(b"", "", "", 1, (None,), ())
    data = files.BoundSnapshotData(SNAPSHOT, CORE, rowmap, members, (None,))
    pointer = selection.parse_pointer(selection._encode(1, SNAPSHOT))
    outcomes = [
        b"locator",
        covered,
        built,
        publication.Publication(SNAPSHOT, True, data),
        selection.Selection(pointer, data),
    ]
    modules = [
        (subject.locator, "encode"),
        (subject.coverage, "build"),
        (subject.builder, "build"),
        (subject.publication, "publish_directory"),
        (subject.selection, "compare_and_select_data"),
    ]
    for index, (module, name) in enumerate(modules):

        def invoke(*args, _index=index, **kwargs):
            calls.append((_index, args, kwargs))
            outcome = outcomes[_index]
            if isinstance(outcome, BaseException):
                raise outcome
            return outcome

        monkeypatch.setattr(module, name, invoke)
    args = (original, derived, "/private", b"program", execution, b"decl", b"query", (), None)
    return args, calls, outcomes


def test_success_exact_order_and_arguments(boundary):
    args, calls, outcomes = boundary
    result = subject.build_publish_select_data(*args)
    assert [c[0] for c in calls] == list(range(5))
    assert calls[0][1] == (args[3], args[4])
    assert calls[1][1] == (args[0], args[1], args[3], args[5], outcomes[0])
    assert calls[2][1] == (args[0], args[1], b"map", ("a" * 64,), (), b"query")
    assert calls[3][1] == (args[0], args[1], args[2], CORE, (("map", b"map"),))
    assert calls[4][1] == (args[0], args[1], args[2], SNAPSHOT, None)
    assert all(1 <= calls[i][2]["deadline_ms"] <= 120000 for i in (0, 1, 2, 4))
    assert (
        result.source_program_id,
        result.snapshot_id,
        result.generation,
        result.row_count,
        result.partition_count,
        result.source_count,
    ) == (SOURCE, SNAPSHOT, 1, 1, 1, 1)
    assert (result.state, result.execution_origin, result.qualification) == (
        "SELECTED_DATA",
        "SUPPLIED_UNVERIFIED",
        "NOT_QUALIFIED",
    )
    with pytest.raises(FrozenInstanceError):
        result.generation = 2


@pytest.mark.parametrize(
    "index,stage,pub,sel",
    [
        (0, "locator", False, False),
        (1, "coverage", False, False),
        (2, "files", False, False),
        (3, "publication", True, False),
        (4, "selection", True, True),
    ],
)
def test_fault_stops_after_boundary(boundary, index, stage, pub, sel):
    args, calls, outcomes = boundary
    outcomes[index] = RuntimeError("secret contents")
    with pytest.raises(subject.ConstructionError) as caught:
        subject.build_publish_select_data(*args)
    err = caught.value
    assert str(err) == "snapshot construction refused"
    assert (err.stage, err.publication_attempted, err.selection_attempted) == (stage, pub, sel)
    assert err.candidate_snapshot_id == (SNAPSHOT if index >= 3 else None)
    assert [c[0] for c in calls] == list(range(index + 1))


@pytest.mark.parametrize("index", range(1, 5))
def test_wrong_return_type_stops(boundary, index):
    args, calls, outcomes = boundary
    outcomes[index] = object()
    with pytest.raises(subject.ConstructionError):
        subject.build_publish_select_data(*args)
    assert [c[0] for c in calls] == list(range(index + 1))


@pytest.mark.parametrize("index", [0, 1, 2, 3, 4])
def test_nonexception_propagates(boundary, index):
    args, calls, outcomes = boundary
    outcomes[index] = KeyboardInterrupt()
    with pytest.raises(KeyboardInterrupt):
        subject.build_publish_select_data(*args)
    assert len(calls) == index + 1


@pytest.mark.parametrize(
    "change",
    [
        {0: object()},
        {1: object()},
        {2: "relative"},
        {3: b""},
        {5: b""},
        {6: b""},
        {7: ("bad",)},
        {7: ("sha256:" + "a" * 64,) * 2},
        {8: b"bad"},
        {8: selection._encode(2**63 - 1, SNAPSHOT)},
    ],
)
def test_admission_refuses_before_calls(boundary, change):
    args, calls, _ = boundary
    values = list(args)
    for key, value in change.items():
        values[key] = value
    with pytest.raises(subject.ConstructionError) as caught:
        subject.build_publish_select_data(*values)
    assert caught.value.stage == "admission" and calls == []
    assert not caught.value.publication_attempted and not caught.value.selection_attempted


@pytest.mark.parametrize(
    "index,mutate",
    [
        (1, lambda x: replace(x, program_id="sha256:" + "b" * 64)),
        (1, lambda x: replace(x, row_count=2)),
        (2, lambda x: replace(x, snapshot_id="sha256:" + "b" * 64)),
        (2, lambda x: replace(x, member_count=2)),
        (3, lambda x: replace(x, data=replace(x.data, core_bytes=b"other"))),
        (4, lambda x: replace(x, pointer=selection.parse_pointer(selection._encode(2, SNAPSHOT)))),
    ],
)
def test_identity_mismatch_refuses(boundary, index, mutate):
    args, calls, outcomes = boundary
    outcomes[index] = mutate(outcomes[index])
    with pytest.raises(subject.ConstructionError):
        subject.build_publish_select_data(*args)
    assert len(calls) == index + 1


@pytest.mark.parametrize("index", range(5))
def test_deadline_after_boundary_preserves_attempts(boundary, monkeypatch, index):
    args, calls, _ = boundary
    clock = [0.0]
    monkeypatch.setattr(subject.time, "monotonic", lambda: clock[0])
    targets = [
        (subject.locator, "encode"),
        (subject.coverage, "build"),
        (subject.builder, "build"),
        (subject.publication, "publish_directory"),
        (subject.selection, "compare_and_select_data"),
    ]
    module, name = targets[index]
    original = getattr(module, name)

    def late(*a, **kw):
        result = original(*a, **kw)
        clock[0] = 2
        return result

    monkeypatch.setattr(module, name, late)
    with pytest.raises(subject.ConstructionError) as caught:
        subject.build_publish_select_data(*args, deadline_ms=1000)
    assert len(calls) == index + 1
    assert caught.value.publication_attempted == (index >= 3)
    assert caught.value.selection_attempted == (index >= 4)


def test_deadline_after_result_constructor(boundary, monkeypatch):
    args, calls, _ = boundary
    clock = [0.0]
    monkeypatch.setattr(subject.time, "monotonic", lambda: clock[0])
    constructor = subject.ConstructionResult

    def late(*args):
        result = constructor(*args)
        clock[0] = 2
        return result

    monkeypatch.setattr(subject, "ConstructionResult", late)
    with pytest.raises(subject.ConstructionError) as caught:
        subject.build_publish_select_data(*args, deadline_ms=1000)
    assert len(calls) == 5 and caught.value.stage == "final"
    assert caught.value.publication_attempted and caught.value.selection_attempted


@pytest.mark.parametrize("index", [3, 4])
def test_late_durable_error_remains_uncertain(boundary, monkeypatch, index):
    args, calls, _ = boundary
    state = []
    module, name = (
        (subject.publication, "publish_directory")
        if index == 3
        else (subject.selection, "compare_and_select_data")
    )

    def effect_then_raise(*unused_args, **unused_kwargs):
        state.append("possible durable change")
        raise RuntimeError("late failure")

    monkeypatch.setattr(module, name, effect_then_raise)
    with pytest.raises(subject.ConstructionError) as caught:
        subject.build_publish_select_data(*args)
    assert state == ["possible durable change"]
    assert caught.value.publication_attempted
    assert caught.value.selection_attempted == (index == 4)
    assert len(calls) == index
    assert str(caught.value) == "snapshot construction refused"


def test_existing_pointer_advances_exactly_once(boundary):
    args, calls, outcomes = boundary
    previous = selection._encode(17, "sha256:" + "b" * 64)
    args = (*args[:-1], previous)
    outcomes[4] = replace(
        outcomes[4], pointer=selection.parse_pointer(selection._encode(18, SNAPSHOT))
    )
    result = subject.build_publish_select_data(*args)
    assert result.generation == 18
    assert calls[4][1][-1] == previous
    assert len(calls) == 5
