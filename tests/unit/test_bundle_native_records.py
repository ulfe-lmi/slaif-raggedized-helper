import pytest
from slaif_raggedized_helper import bundle_native_records as b


@pytest.mark.parametrize(
    "header,chunks,receipts,count",
    [
        (b"{}", b"", b"{}", True),
        (b"x" * 65537, b"", b"{}", 1),
        (b"{}", b"x" * (16 * 1024 * 1024 + 1), b"{}", 1),
        (b"{}", b"", b"x" * 8000001, 1),
        (b"\xff", b"", b"{}", 1),
        (b'{"x":1,"x":2}', b"", b"{}", 1),
        (b"[" * 20 + b"0" + b"]" * 20, b"", b"{}", 1),
    ],
)
def test_refusal(header, chunks, receipts, count):
    with pytest.raises(b.BundleRecordsError, match="^native bundle records refused$"):
        b.validate(header, chunks, receipts, count)


def test_early_refusal(monkeypatch):
    called = []

    def forbidden(*args):
        called.append(True)
        raise AssertionError("parse should not run")

    monkeypatch.setattr(b, "_parse", forbidden)
    with pytest.raises(b.BundleRecordsError):
        b.validate(b"x" * 65537, b"", b"", 1)
    assert not called


def test_tree_node_limit():
    with pytest.raises(ValueError):
        b._parse(b"[1,2,3]", 3)


@pytest.mark.parametrize(
    "raw,limit,accepted",
    [
        (b"[1,2,3]", 4, True),
        (b"[1,2,3]", 3, False),
        (b'{"a":1}', 3, True),
        (b'{"a":1}', 2, False),
        (b"[" * 16 + b"0" + b"]" * 16, 17, True),
        (b"[" * 17 + b"0" + b"]" * 17, 18, False),
        (b'{"\\ud800":1}', 3, False),
    ],
)
def test_tree_admission_boundaries(raw, limit, accepted):
    if accepted:
        b._parse(raw, limit)
    else:
        with pytest.raises(ValueError):
            b._parse(raw, limit)


def test_queue_admission_precedes_expansion():
    import sys

    peak = []

    def trace(frame, event, arg):
        if frame.f_code is b._parse.__code__ and event == "line":
            peak.append(len(frame.f_locals.get("stack", ())))
        return trace

    sys.settrace(trace)
    try:
        with pytest.raises(ValueError):
            b._parse(b"[" + b"0," * 15000 + b"0]", 10000)
    finally:
        sys.settrace(None)
    assert max(peak) <= 10000
