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
