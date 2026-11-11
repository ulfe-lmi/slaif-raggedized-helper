import json
import subprocess
import sys

import pytest

from slaif_raggedized_helper import bundle_pdf_records as b
from slaif_raggedized_helper.source_admission import OriginalStore


def test_early_admission_before_parse_hash_and_store(monkeypatch):
    store = object.__new__(OriginalStore)

    def forbidden(*args, **kwargs):
        pytest.fail("work before admission")

    monkeypatch.setattr(b, "_parse", forbidden)
    monkeypatch.setattr(b.hashlib, "sha256", forbidden)
    monkeypatch.setattr(OriginalStore, "read_verified", forbidden)
    for args in (
        (store, "bad", b"{}", b"", b"{}", 0),
        (store, "sha256:" + "a" * 64, b"x" * (b.HEADER_BYTES + 1), b"", b"{}", 0),
        (store, "sha256:" + "a" * 64, b"{}", b"x" * (b.jl.MAX_BYTES + 1), b"{}", 0),
        (store, "sha256:" + "a" * 64, b"{}", b"", b"x" * (b.COVERAGE_BYTES + 1), 0),
        (store, "sha256:" + "a" * 64, b"{}", b"", b"{}", True),
        (store, "sha256:" + "a" * 64, bytearray(b"{}"), b"", b"{}", 0),
    ):
        with pytest.raises(b.PdfRecordsError):
            b.validate(*args)


@pytest.mark.parametrize(
    "raw",
    [
        b'{"x":1,"x":2}',
        b'"\\ud800"',
        b"NaN",
        b"\xff",
        b"[" * 18 + b"0" + b"]" * 18,
        b"[" + b"0," * 20001 + b"0]",
    ],
)
def test_bad_json_tree(raw):
    with pytest.raises((ValueError, UnicodeError)):
        b._parse(raw)


def test_deadline_before_parser(monkeypatch):
    ticks = iter([0, 31])
    monkeypatch.setattr(b.time, "monotonic", lambda: next(ticks))
    monkeypatch.setattr(b, "_parse", lambda *_: pytest.fail("parser after deadline"))
    with pytest.raises(b.PdfRecordsError):
        b.validate(object.__new__(OriginalStore), "sha256:" + "a" * 64, b"{}", b"", b"{}", 0)


def test_import_does_not_launch_parser_or_work():
    script = """
import builtins, subprocess, socket
original = builtins.__import__
def guard(name, *args, **kwargs):
    if name.split('.')[0] in ('pdfminer', 'torch', 'transformers'):
        raise AssertionError(name)
    return original(name, *args, **kwargs)
def fail(*args, **kwargs): raise AssertionError('external work')
builtins.__import__ = guard
subprocess.Popen = fail
socket.socket.connect = fail
import slaif_raggedized_helper.bundle_pdf_records
"""
    proc = subprocess.run([sys.executable, "-c", script], capture_output=True, timeout=5)
    assert proc.returncode == 0, proc.stderr


def test_oversized_record_refused_before_parse(monkeypatch):
    monkeypatch.setattr(b, "_parse", lambda *_: pytest.fail("parse before record cap"))
    with pytest.raises(b.PdfRecordsError):
        b.validate(
            object.__new__(OriginalStore),
            "sha256:" + "a" * 64,
            b"{}",
            b"x" * (b.p.MAX_ADMISSION_BYTES + 1) + b"\n",
            b"{}",
            1,
        )


def test_node_boundaries_and_cumulative_pending():
    def parse(value):
        return b._parse(json.dumps(value).encode())

    # Dictionary keys and values both count, including the root.
    exact_dict = {str(i): 0 for i in range(9999)}
    exact_dict["0"] = [0]  # Replace one scalar with a list and its child.
    assert parse(exact_dict) == exact_dict
    with pytest.raises(ValueError):
        parse({str(i): 0 for i in range(10000)})

    exact_list = [0] * 19999
    assert parse(exact_list) == exact_list
    with pytest.raises(ValueError):
        parse([0] * 20000)

    # One sibling remains pending while the other is already visited and expanded.
    exact_nested = [[0] * 9997, [0] * 10000]
    assert parse(exact_nested) == exact_nested
    with pytest.raises(ValueError):
        parse([[0] * 9998, [0] * 10000])


def test_depth_boundary():
    exact = b"[" * b.MAX_DEPTH + b"0" + b"]" * b.MAX_DEPTH
    assert b._parse(exact) is not None
    with pytest.raises(ValueError):
        b._parse(b"[" + exact + b"]")
