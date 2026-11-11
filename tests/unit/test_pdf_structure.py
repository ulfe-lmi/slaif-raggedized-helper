import pytest

from slaif_raggedized_helper.pdf_structure import Line, StructureError, classify


def lines(*texts):
    return tuple(Line(1, t, (0.0, 0.0, 1.0, 1.0)) for t in texts)


def test_witness_and_determinism():
    data = lines(
        "Parameter       Value (kg)",
        "--------------------------",
        *(f"Item{i:02d}          {i} kg" for i in range(1, 21)),
        "TAILCANARY 99 kg",
    )
    expected = ("table_header",) + ("table_row",) * 21 + ("text",)
    assert classify(data) == classify(data) == expected
    assert data[0].text == "Parameter       Value (kg)"


def test_incomplete_and_procedure():
    assert classify(lines("ordinary  prose", "not a rule", "1. Mix", "Warning: do not mix")) == (
        "text",
        "text",
        "list",
        "text",
    )
    assert classify(lines("Name  Unit", "----------", "A     kg")) == ("text",) * 3


def test_pages_and_adjacent_tables():
    a = lines(
        "Name  Unit",
        "----------",
        "A     kg",
        "B     no",
        "Name  Unit",
        "----------",
        "C     kg",
        "D     no",
    )
    assert classify(a) == ("table_header", "table_row", "table_row", "table_row") * 2
    assert classify(a[:3] + (Line(2, "B     no", (0.0, 0.0, 1.0, 1.0)),)) == ("text",) * 4


def test_validation():
    assert len(classify(lines(*(["x"] * 4096)))) == 4096
    with pytest.raises(StructureError):
        classify(lines(*(["x"] * 4097)))
    for bad in (
        (Line(True, "x", (0, 0, 1, 1)),),
        (Line(1, "\ud800", (0, 0, 1, 1)),),
        (Line(1, "x", (0, 0, float("nan"), 1)),),
        (Line(1, "x" * 200001, (0, 0, 1, 1)),),
        [Line(1, "x", (0, 0, 1, 1))],
    ):
        with pytest.raises(StructureError):
            classify(bad)


def test_pipe_and_rejections():
    assert classify(lines("| Name | Unit |", "|---|---|", "| A | kg |", "| B | no |")) == (
        "table_header",
        "table_row",
        "table_row",
        "table_row",
    )
    for data in (
        lines("| Name | Unit |", "|---|", "| A | kg |", "| B | no |"),
        lines("Name  Unit", "---", "A     kg", "B     no"),
        lines("Name  Unit", "----------", "A    kg", "B     no"),
        lines("Name  Unit", "----------", "", "B     no"),
        lines("Name  Unit", "----------", "A     kg", "unrelated"),
    ):
        assert classify(data) == ("text",) * len(data)


def test_limits_and_bad_values():
    assert classify(lines("x" * 200000)) == ("text",)
    assert len(classify(lines("x" * 200000, "x" * 200000, "x" * 100000))) == 3
    for data in (
        lines("x" * 200000, "x" * 200000, "x" * 100001),
        (object(),),
        (Line(0, "x", (0, 0, 1, 1)),),
        (Line(33, "x", (0, 0, 1, 1)),),
        (Line(1, "x", (False, 0, 1, 1)),),
        (Line(1, "x", (0, 0, 10**1000, 1)),),
        (Line(1, "x", (1, 0, 0, 1)),),
        (Line(1, "x", (0, 0, float("inf"), 1)),),
    ):
        with pytest.raises(StructureError):
            classify(data)
    assert classify(lines("μ kg", "- warning: do not mix", "2. 5 mg")) == ("text", "list", "list")


def test_final_deadline(monkeypatch):
    import slaif_raggedized_helper.pdf_structure as module

    ticks = iter((0.0, 2.0))
    monkeypatch.setattr(module.time, "monotonic", lambda: next(ticks))
    with pytest.raises(StructureError, match="budget"):
        classify(())


def test_long_spaces_bounded_process():
    import subprocess
    import sys

    code = (
        "from slaif_raggedized_helper.pdf_structure import *; "
        "assert classify((Line(1, ' '*200000, (0,0,1,1)),) + "
        "tuple(Line(1, 'x', (0,0,1,1)) for _ in range(3))) == ('text',)*4"
    )
    subprocess.run([sys.executable, "-c", code], check=True, timeout=2.5)


def test_one_character_header_offset_requires_consistent_rows():
    header = "Parameter       Value (kg)"
    rule = "--------------------------"
    assert classify(lines(header, rule, "Item001          1 kg", "Item002          2 kg")) == (
        "table_header", "table_row", "table_row", "table_row"
    )
    for rows in (("Item001          1 kg", "Item002           2 kg"),
                 ("Item001           1 kg", "Item002           2 kg")):
        assert classify(lines(header, rule, *rows)) == ("text",) * 4
