"""Independent synthetic oracles for supplied geometry; no source attestation."""

import ast
import builtins
from contextlib import ExitStack
import dataclasses
import io
import os
import socket
import subprocess
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from slaif_raggedized_helper import declared_stage_geometry as subject

ORACLE = json.loads(
    (Path(__file__).parents[2] / "docs/parallel/declared-span-support-oracle.json").read_text()
)
BASE = json.loads(ORACLE["dataset_ascii"])


def ident(n):
    return "sha256:" + format(n, "064x")


def atom(rev, block, end, start=0, extraction=90):
    return dict(
        revision_id=ident(rev),
        extraction_id=ident(extraction),
        block_id=block,
        start=start,
        end=end,
        text_sha256="a" * 64,
    )


def data(or_alternative=False, duplicate=False, empty=False):
    obj = json.loads(json.dumps(BASE))
    case = obj["cases"][0]
    case["requirements"] = (
        []
        if empty
        else [
            dict(
                requirement_id="R1",
                grade=3,
                alternatives=[[atom(1, "A", 4), atom(2, "B", 3)]]
                + ([[atom(3, "C", 2)]] if or_alternative else []),
            ),
            dict(
                requirement_id="R2",
                grade=1,
                alternatives=[[atom(1, "A", 4) if duplicate else atom(4, "D", 1)]],
            ),
        ]
    )
    if empty:
        case["answerability"] = "unknown"
    return json.dumps(obj, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode("ascii")


def row(n, rev, block, lo, hi, ext=90):
    return (ident(100 + n), ident(rev), ident(ext), ((block, lo, hi),))


def rows():
    return (
        row(0, 1, "A", 0, 2),
        (ident(101), ident(1), ident(90), (("A", 2, 4),)),
        row(2, 2, "B", 0, 3),
        row(3, 3, "C", 0, 2),
        row(4, 4, "D", 0, 1),
    )


def stages(all_indices, lexical=None, selected=None, returned=None):
    lexical = all_indices if lexical is None else lexical
    selected = lexical if selected is None else selected
    returned = selected if returned is None else returned
    return tuple(
        zip(
            subject._NAMES,
            (
                all_indices,
                all_indices,
                all_indices,
                all_indices,
                all_indices,
                lexical,
                selected,
                returned,
                all_indices,
                all_indices,
            ),
        )
    )


def test_or_alternative_and_requirement_loss_and_13_actual_calls():
    rs = rows()
    # Dense returned contributes all rows, so fusion input equals their union.
    ss = stages((0, 1, 2, 3, 4), (0, 1, 2, 4), (0, 4), (0,))
    real = subject.declared_span_support.score_case
    with patch.object(subject.declared_span_support, "score_case", wraps=real) as calls:
        result = subject.diagnose(data(True), "case1", rs, ss)
    assert calls.call_count == 13
    assert result.transitions[3].lost_alternatives == (("R1", 1),)
    assert result.transitions[3].lost_requirements == ()
    assert result.transitions[4].lost_requirements == ("R1",)
    assert result.transitions[5].lost_requirements == ("R2",)
    assert result.stages[0].completion.undefined_reason == "AMBIGUOUS_ALTERNATIVE_SOURCE_UNIVERSE"
    assert result.chunk_metric_reason == "NO_EXPLICIT_CHUNK_RELEVANCE_MAPPING"
    assert result.source_binding == "UNVERIFIED"
    assert "case1" not in repr(result)


def test_flat_full_denominator_and_rank_21():
    base = rows()
    irrelevant = tuple(row(10 + i, 20 + i, "irrelevant", 0, 1) for i in range(18))
    rs = (base[0], base[4], *irrelevant, base[1], base[2])
    all_indices = tuple(range(len(rs)))
    result = subject.diagnose(data(), "case1", rs, stages(all_indices))
    twenty, sixty = result.prefixes[:2]
    assert twenty.completion.recall == 1 / 3
    assert twenty.coverage.covered_requirement_ids == ("R2",)
    assert sixty.completion.recall == 1
    assert sixty.coverage.covered_requirement_ids == ("R1", "R2")
    assert sixty.completion is result.stages[3].completion
    assert result.stages[0].completion.recall == 1


def test_duplicate_and_empty():
    rs = rows()
    result = subject.diagnose(data(duplicate=True), "case1", rs, stages((0, 1, 2)))
    assert result.stages[0].completion.recall == 1
    assert len(result.stages[0].completion.atom_coverage) == 2
    occurrences = result.stages[0].completion.atom_occurrences
    assert len(occurrences) == 3
    assert occurrences[0][3] == occurrences[2][3]
    assert len(result.stages[0].completion.required_revisions) == 2
    empty = subject.diagnose(data(empty=True), "case1", (), stages(()))
    assert empty.stages[0].completion.undefined_reason == "NO_GOLD_SOURCES"
    assert empty.stages[0].coverage.undefined_reason == "NO_GOLD_REQUIREMENTS"
    no_rows = subject.diagnose(data(), "case1", (), stages(()))
    assert no_rows.stages[0].completion.recall == 0


def test_touch_gap_extraction_and_block():
    rs = rows()
    touching = subject.diagnose(data(), "case1", rs, stages((0, 1, 2, 4)))
    assert touching.stages[0].completion.recall == 1
    bad = (rs[0], row(1, 1, "A", 3, 4), row(2, 2, "B", 0, 3, 91), row(4, 4, "other", 0, 1))
    result = subject.diagnose(data(), "case1", bad, stages((0, 1, 2, 3)))
    assert result.stages[0].completion.recall == 0


@pytest.mark.parametrize(
    "mutation", ["bool", "duplicate", "relation", "name", "subclass", "oversize"], ids=str
)
def test_invalid_inputs(mutation):
    rs = rows()
    ss = stages((0, 1, 2, 3, 4))

    class T(tuple):
        pass

    if mutation == "bool":
        ss = tuple((name, (True,) if i == 0 else ords) for i, (name, ords) in enumerate(ss))
    elif mutation == "duplicate":
        ss = tuple((name, (0, 0) if i == 0 else ords) for i, (name, ords) in enumerate(ss))
    elif mutation == "relation":
        ss = tuple((name, () if i == 1 else ords) for i, (name, ords) in enumerate(ss))
    elif mutation == "name":
        ss = (("x" * 33, ss[0][1]), *ss[1:])
    elif mutation == "subclass":
        rs = T(rs)
    else:
        rs = ((ident(1), ident(2), ident(3), (("x" * 257, 0, 1),)),)
    with pytest.raises(subject.GeometryError, match="^declared stage geometry refused$") as error:
        subject.diagnose(data(), "case1", rs, ss)
    assert error.value.__cause__ is None


def test_clock_and_baseexception():
    sentinel = KeyboardInterrupt()
    with patch.object(subject.text_evaluation_dataset, "admit", side_effect=sentinel):
        with pytest.raises(KeyboardInterrupt) as error:
            subject.diagnose(data(), "case1", (), stages(()))
    assert error.value is sentinel
    with patch.object(subject.time, "monotonic", side_effect=[0, 2]):
        with pytest.raises(subject.GeometryError):
            subject.diagnose(data(), "case1", (), stages(()), deadline_ms=1)


def test_same_revision_requires_all_atoms_and_unicode_codepoints():
    obj = json.loads(data())
    reqs = obj["cases"][0]["requirements"]
    reqs[0]["alternatives"] = [[atom(1, "Ž😀", 2)]]
    reqs[1]["alternatives"] = [[atom(1, "Ž😀", 4, 2)]]
    encoded = json.dumps(obj, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode()
    first = row(0, 1, "Ž😀", 0, 2)
    second = row(1, 1, "Ž😀", 2, 4)
    result = subject.diagnose(encoded, "case1", (first, second), stages((0, 1), (0,), (0,), (0,)))
    assert result.stages[5].coverage.covered_requirement_ids == ("R1",)
    assert result.stages[5].completion.recall == 0
    assert result.stages[0].completion.recall == 1


def test_full_stage_beyond_60_and_order_identity():
    rs = tuple(row(20 + i, 20 + i, "x", 0, 1) for i in range(60)) + rows()[:3] + (rows()[4],)
    universe = tuple(range(64))
    returned = tuple(range(60))
    ss = tuple(
        zip(
            subject._NAMES,
            (
                universe,
                universe,
                universe,
                returned,
                universe,
                universe,
                universe,
                returned,
                returned,
                returned,
            ),
        )
    )
    result = subject.diagnose(data(), "case1", rs, ss)
    assert result.stages[0].coverage.complete_requirements is True
    assert result.stages[3].coverage.complete_requirements is False
    assert result.stages[0].completion.recall == 1
    assert result.stages[3].completion.recall == 0
    reordered = tuple(
        zip(
            subject._NAMES,
            (
                universe,
                universe,
                universe,
                returned[::-1],
                universe,
                universe,
                universe,
                returned,
                returned,
                returned,
            ),
        )
    )
    other = subject.diagnose(data(), "case1", rs, reordered)
    assert result.invocation_id != other.invocation_id
    assert result.stages[3].fingerprint != other.stages[3].fingerprint


def test_preflight_refuses_before_parser_or_hash():
    with patch.object(
        subject.text_evaluation_dataset, "admit", side_effect=AssertionError("parser")
    ) as parser:
        with pytest.raises(subject.GeometryError):
            subject.diagnose(
                data(), "case1", ((ident(1), ident(2), ident(3), (("x" * 257, 0, 1),)),), stages(())
            )
    parser.assert_not_called()


def test_deadline_after_lower_and_exception_privacy():
    clock = [0.0]

    def lower(*args, **kwargs):
        clock[0] = 10
        return object()

    with (
        patch.object(subject.time, "monotonic", side_effect=lambda: clock[0]),
        patch.object(subject.declared_span_support, "score_case", side_effect=lower),
    ):
        with pytest.raises(subject.GeometryError, match="^declared stage geometry refused$"):
            subject.diagnose(data(), "case1", (), stages(()), deadline_ms=1000)
    with patch.object(
        subject.declared_span_support, "score_case", side_effect=ValueError("secret")
    ):
        with pytest.raises(subject.GeometryError) as error:
            subject.diagnose(data(), "case1", (), stages(()))
    assert "secret" not in str(error.value)
    assert error.value.__suppress_context__


def test_ledger_formula():
    rs = rows()
    ss = stages((0, 1, 2, 3, 4))
    raw = data()
    result = subject.diagnose(raw, "case1", rs, ss)
    # Dataset contains four chosen atoms plus one atom in case3.
    d, f, length, n, g, c, i = len(raw), 5, 5, 5, 4, 3, 50
    j = (f + 1).bit_length()
    assert result.work == 42 * d + 29 * (f + g + 1) * (j + 6) + 64 * (n + i + c + g + 1)
    assert (
        result.serialization_budget
        == 56 * d + 29 * (4 * length + 96 * f + 256 * n + 128 * g) + 4194304
    )


def test_ledger_cap_reachability_from_component_maxima():
    # All component maxima simultaneously give an upper bound; the actual admission
    # domain is tighter. Therefore no admitted input can land exactly on either cap.
    d, f, length, n, g, c, i = 1048576, 8192, 65536, 512, 512, 256, 5120
    j = (f + 1).bit_length()
    assert 42 * d + 29 * (f + g + 1) * (j + 6) + 64 * (n + i + c + g + 1) == 49498756
    assert 56 * d + 29 * (4 * length + 96 * f + 256 * n + 128 * g) + 4194304 == 99024896


def test_same_count_different_stage_identity_refused():
    rs = rows()
    ss = stages((0, 1, 2, 3, 4))
    changed = tuple(
        (name, (0, 1, 2, 3) if i == 0 else (0, 1, 2, 4) if i == 1 else ords)
        for i, (name, ords) in enumerate(ss)
    )
    with pytest.raises(subject.GeometryError):
        subject.diagnose(data(), "case1", rs, changed)


def test_exact_scalar_and_tuple_subclasses():
    class S(str):
        pass

    class IntegerSubclass(int):
        pass

    class T(tuple):
        pass

    good = rows()
    cases = [
        (good, T(stages((0, 1, 2, 3, 4))), 'case1', 10000),
        ((T(good[0]),), stages((0,)), 'case1', 10000),
        (((S(good[0][0]), *good[0][1:]),), stages((0,)), 'case1', 10000),
        (((*good[0][:3], (('A', IntegerSubclass(0), 2),)),), stages((0,)), 'case1', 10000),
        (good, stages((0, 1, 2, 3, 4)), S('case1'), 10000),
        (good, stages((0, 1, 2, 3, 4)), 'case1', True),
    ]
    for rs, ss, cid, deadline in cases:
        with pytest.raises(subject.GeometryError):
            subject.diagnose(data(), cid, rs, ss, deadline_ms=deadline)


def test_hash_deadline_and_lower_baseexception():
    sentinel = KeyboardInterrupt()
    with patch.object(subject.declared_span_support, 'score_case', side_effect=sentinel):
        with pytest.raises(KeyboardInterrupt) as error:
            subject.diagnose(data(), 'case1', (), stages(()))
    assert error.value is sentinel

    clock = [0.0]
    real_admit = subject.text_evaluation_dataset.admit
    real_hash = subject.hashlib.sha256

    def admit(*args, **kwargs):
        dataset = real_admit(*args, **kwargs)
        def late_hash(*args, **kwargs):
            result = real_hash(*args, **kwargs)
            clock[0] = 10
            return result
        patcher = patch.object(subject.hashlib, 'sha256', side_effect=late_hash)
        patcher.start()
        patches.append(patcher)
        return dataset

    patches = []
    try:
        with patch.object(subject.time, 'monotonic', side_effect=lambda: clock[0]), \
             patch.object(subject.text_evaluation_dataset, 'admit', side_effect=admit):
            with pytest.raises(subject.GeometryError):
                subject.diagnose(data(), 'case1', rows(), stages((0,1,2,3,4)), deadline_ms=1000)
    finally:
        for patcher in patches:
            patcher.stop()


def test_stage_fingerprint_binds_geometry_even_when_coverage_is_unchanged():
    original = rows()
    changed = (row(0, 1, "A", 0, 1), *original[1:])
    selected = (0,)
    first = subject.diagnose(data(), "case1", original, stages(selected))
    second = subject.diagnose(data(), "case1", changed, stages(selected))
    assert first.stages[0].coverage.covered_requirement_ids == ()
    assert second.stages[0].coverage.covered_requirement_ids == ()
    assert first.stages[0].fingerprint != second.stages[0].fingerprint
    assert first.invocation_id != second.invocation_id


@pytest.mark.parametrize(
    ("index", "ordinals"),
    [
        (2, (0, 1, 2, 3, 4, 5)),
        (3, (0, 1, 2, 3, 4, 5)),
        (5, (0, 1, 2, 3, 4, 5)),
        (6, (0, 1, 2, 3, 4, 5)),
        (7, (0, 1, 2, 3, 4, 5)),
        (8, (0, 1, 2, 3)),
        (9, (0, 1, 2, 3, 4, 5)),
    ],
    ids=("dense-selected", "dense-returned", "lexical-ranked", "lexical-selected",
         "lexical-returned", "fusion-union", "fusion-returned"),
)
def test_each_stage_relation_rejects_violations(index, ordinals):
    # The sixth row exists in the supplied universe but is absent from every stage.
    rs = rows() + (row(9, 9, "extra", 0, 1),)
    ss = stages((0, 1, 2, 3, 4))
    altered = tuple((name, ordinals if i == index else values)
                    for i, (name, values) in enumerate(ss))
    with pytest.raises(subject.GeometryError):
        subject.diagnose(data(), "case1", rs, altered)


@pytest.mark.parametrize(
    "kind",
    ("dataset", "rows", "fragments", "total-fragments", "block-chars", "stage-count"),
    ids=("dataset", "rows", "fragments", "total-fragments", "block-chars", "stage-count"),
)
def test_component_limits_reject_before_parser(kind):
    raw = data()
    rs = ()
    ss = stages(())
    if kind == "dataset":
        raw = b"x" * (1048576 + 1)
    elif kind == "rows":
        rs = (row(0, 1, "A", 0, 1),) * 513
    elif kind == "fragments":
        rs = ((ident(1), ident(2), ident(3), (("A", 0, 1),) * 257),)
    elif kind == "total-fragments":
        rs = tuple((ident(i), ident(2), ident(3), (("A", 0, 1),) * 256) for i in range(33))
    elif kind == "block-chars":
        rs = tuple((ident(i), ident(2), ident(3), (("A" * 256, 0, 1),) * 256)
                   for i in range(2))
    else:
        ss = ss[:-1]
    with patch.object(subject.text_evaluation_dataset, "admit") as parser:
        with pytest.raises(subject.GeometryError):
            subject.diagnose(raw, "case1", rs, ss)
        parser.assert_not_called()


def test_inconsistent_lower_gain_refused_unit_double_only():
    from dataclasses import replace

    actual = subject.declared_span_support.score_case
    calls = [0]

    def inconsistent(*args, **kwargs):
        result = actual(*args, **kwargs)
        calls[0] += 1
        if calls[0] == 2:
            coverage = result.at_k[0]
            coverage = replace(coverage, covered_requirement_ids=("R1",))
            return replace(result, at_k=(coverage,))
        return result

    # With no rows, all real coverage is empty; a fabricated gain must fail closed.
    with patch.object(subject.declared_span_support, "score_case", side_effect=inconsistent):
        with pytest.raises(subject.GeometryError):
            subject.diagnose(data(), "case1", (), stages(()))


def test_output_structure_excludes_input_stage_and_geometry_tuples():
    supplied_rows = rows()
    supplied_stages = stages((0, 1, 2, 3, 4))
    result = subject.diagnose(data(), "case1", supplied_rows, supplied_stages)
    assert tuple(field.name for field in dataclasses.fields(subject.Stage)) == (
        "name", "cutoff", "row_count", "coverage", "completion", "fingerprint"
    )
    assert all(type(stage.row_count) is int and stage.row_count == 5
               for stage in result.stages)
    forbidden = [supplied_rows, supplied_stages]
    forbidden.extend(supplied_rows)
    forbidden.extend(stage[1] for stage in supplied_stages)

    def inspect(value):
        assert all(value is not original for original in forbidden)
        if dataclasses.is_dataclass(value) and not isinstance(value, type):
            assert "case1" not in repr(value)
            for field in dataclasses.fields(value):
                inspect(getattr(value, field.name))
        elif type(value) is tuple:
            for item in value:
                inspect(item)
        else:
            assert type(value) in (str, int, float, bool, type(None))

    inspect(result)
    with pytest.raises(dataclasses.FrozenInstanceError):
        result.stages[0].row_count = 0


@pytest.mark.parametrize("index", (3, 7, 9), ids=("dense", "lexical", "fusion"))
def test_returned_stage_cap_precedes_parser(index):
    many = tuple(row(i, i + 1, "x", 0, 1) for i in range(61))
    all_indices = tuple(range(61))
    supplied = tuple((name, all_indices if i == index else ())
                     for i, name in enumerate(subject._NAMES))
    with patch.object(subject.text_evaluation_dataset, "admit") as parser:
        with pytest.raises(subject.GeometryError):
            subject.diagnose(data(), "case1", many, supplied)
        parser.assert_not_called()


def test_distinct_revision_completion_is_not_erased_by_other_missing_revision():
    rs = rows()
    supplied = stages((0, 1, 2, 4), (0, 4), (0, 4), (0, 4))
    result = subject.diagnose(data(), "case1", rs, supplied)
    assert result.stages[5].coverage.covered_requirement_ids == ("R2",)
    assert result.stages[5].completion.required_revisions == (ident(1), ident(2), ident(4))
    assert result.stages[5].completion.covered_revisions == (ident(4),)
    assert result.stages[5].completion.recall == 1 / 3


def test_original_clock_after_admission_refuses_before_geometry():
    clock = [0.0]
    real_admit = subject.text_evaluation_dataset.admit

    def late_admit(*args, **kwargs):
        result = real_admit(*args, **kwargs)
        clock[0] = 2.0
        return result

    with (
        patch.object(subject.time, "monotonic", side_effect=lambda: clock[0]),
        patch.object(subject.text_evaluation_dataset, "admit", side_effect=late_admit),
        patch.object(subject.declared_span_support, "score_case") as lower,
    ):
        with pytest.raises(subject.GeometryError):
            subject.diagnose(data(), "case1", (), stages(()), deadline_ms=1000)
        lower.assert_not_called()


def test_invalid_unicode_block_and_duplicate_chunk_refuse():
    first = row(0, 1, "A", 0, 1)
    invalid = (first[0], first[1], first[2], (("\ud800", 0, 1),))
    duplicate = (first, first)
    for supplied_rows in ((invalid,), duplicate):
        with pytest.raises(subject.GeometryError):
            subject.diagnose(
                data(), "case1", supplied_rows, stages(tuple(range(len(supplied_rows))))
            )


def test_chunk_alias_conflict_and_shared_revision_complementary_chunks():
    first = row(0, 1, "A", 0, 2)
    alias = (first[0], ident(7), ident(8), (("different", 1, 3),))
    with pytest.raises(subject.GeometryError):
        subject.diagnose(data(), "case1", (first, alias), stages((0, 1)))
    second = row(1, 1, "A", 2, 4)
    result = subject.diagnose(data(), "case1", (first, second), stages((0, 1)))
    assert result.stages[0].completion.covered_revisions == (ident(1),)
    assert result.stages[0].completion.recall == 1 / 3


def test_final_construction_after_deadline_refused():
    clock = [0.0]
    real = subject.Diagnosis

    def late(*args, **kwargs):
        result = real(*args, **kwargs)
        clock[0] = 2.0
        return result

    with (
        patch.object(subject.time, "monotonic", side_effect=lambda: clock[0]),
        patch.object(subject, "Diagnosis", side_effect=late),
    ):
        with pytest.raises(subject.GeometryError, match="^declared stage geometry refused$"):
            subject.diagnose(data(), "case1", (), stages(()), deadline_ms=1000)


def test_module_import_whitelist_and_no_resource_activity_unit_guards():
    source = Path(subject.__file__).read_text()
    tree = ast.parse(source)
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append((node.level, node.module, tuple(alias.name for alias in node.names)))
    assert imports == [
        (0, "bisect", ("bisect_right",)),
        (0, "dataclasses", ("dataclass", "field")),
        "hashlib", "json", "re", "time",
        (1, None, ("declared_span_support", "text_evaluation_dataset")),
    ]
    raw, supplied_rows, supplied_stages = data(), rows(), stages((0, 1, 2, 3, 4))
    # Unit-only guards; this is not an actual source or runtime qualification.
    with ExitStack() as stack:
        for owner, name in (
            (builtins, "open"), (io, "open"), (os, "open"),
            (socket, "socket"), (subprocess, "Popen"), (os, "system"),
        ):
            stack.enter_context(patch.object(owner, name, side_effect=SystemExit("resource call")))
        result = subject.diagnose(raw, "case1", supplied_rows, supplied_stages)
    assert result.stages[0].completion.recall == 1
