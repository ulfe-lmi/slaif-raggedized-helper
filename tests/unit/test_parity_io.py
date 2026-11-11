import hashlib
import json
import math
import os

import pytest

from slaif_raggedized_helper.qualification import parity_io as io


def test_bytes_and_unicode(tmp_path):
    raw = b'{ "text": "\\ud83d\\ude00 \xc5\xbe" }\n'
    path = tmp_path / "input"
    path.write_bytes(raw)
    result = io.read_document(path, max_bytes=len(raw))
    assert result.document == {"text": "😀 ž"}
    assert result.sha256 == hashlib.sha256(raw).hexdigest()
    assert result.byte_count == len(raw)
    with pytest.raises(io.Refusal, match="byte limit"):
        io.read_document(path, max_bytes=len(raw) - 1)


@pytest.mark.parametrize("raw", [b'{"a":1,"a":2}', b'NaN', b'1e999', b'"\\ud800"',
                                  b'"\xff"', b'[' * 65 + b'0' + b']' * 65,
                                  b'1' * 129, b'{'])
def test_invalid_json_is_safe(tmp_path, raw):
    path = tmp_path / "private-canary"
    path.write_bytes(raw)
    with pytest.raises(io.Refusal) as error:
        io.read_document(path)
    assert "private-canary" not in str(error.value)
    assert "Traceback" not in str(error.value)


def test_special_files_and_symlink_refused(tmp_path):
    path = tmp_path / "file"
    path.write_text("{}")
    link = tmp_path / "link"
    link.symlink_to(path)
    fifo = tmp_path / "fifo"
    os.mkfifo(fifo)
    for target in (link, fifo, tmp_path):
        with pytest.raises(io.Refusal):
            io.read_document(target)


def test_changes_during_read_are_refused(tmp_path, monkeypatch):
    path = tmp_path / "file"
    path.write_text('{"a":1}')
    original = os.read

    def changing(fd, size):
        result = original(fd, size)
        if result:
            path.write_text('{}')
        return result

    monkeypatch.setattr(io.os, "read", changing)
    with pytest.raises(io.Refusal, match="changed"):
        io.read_document(path)


def test_growth_is_bounded(tmp_path, monkeypatch):
    path = tmp_path / "file"
    path.write_text('{}')
    original = os.read

    def growing(fd, size):
        path.write_bytes(b' ' * 100)
        return original(fd, size)

    monkeypatch.setattr(io.os, "read", growing)
    with pytest.raises(io.Refusal, match="byte limit"):
        io.read_document(path, max_bytes=4)


def test_render_and_preflight(tmp_path):
    assert io.render_json({"ž": "😀", "a": 1}) == '{"a":1,"ž":"😀"}'.encode()
    with pytest.raises(io.Refusal):
        io.render_json({"v": float("nan")})
    with pytest.raises(io.Refusal):
        io.render_json({"v": object()})
    with pytest.raises(io.Refusal, match="byte limit"):
        io.render_json({"a": "x"}, max_bytes=3)
    calls = []
    with pytest.raises(io.Refusal):
        io.run_export({}, lambda doc: calls.append(doc), tmp_path / "missing" / "out")
    assert calls == []
    link = tmp_path / "link"
    link.symlink_to(tmp_path / "missing")
    with pytest.raises(io.Refusal):
        io.preflight_output(link)
    out = tmp_path / "out"
    assert io.run_export({}, lambda _: {"ok": True}, out) == {"ok": True}
    assert json.loads(out.read_bytes()) == {"ok": True}


def test_float_underflow_and_representable_zero(tmp_path):
    path = tmp_path / "numeric"
    for token in ("1e-999", "-1e-999", "0.0001e-999"):
        path.write_text('{"score":' + token + '}')
        with pytest.raises(io.Refusal, match="invalid JSON number") as error:
            io.read_document(path)
        assert token not in str(error.value)
    for token, expected in (("-0e-999", -0.0), ("0.0e999", 0.0),
                            ("5e-324", 5e-324), ("-5e-324", -5e-324)):
        path.write_text('{"score":' + token + '}')
        actual = io.read_document(path).document["score"]
        assert actual == expected
        assert math.copysign(1, actual) == math.copysign(1, expected)


def test_nul_destination_refused_before_analysis(tmp_path):
    calls = []
    with pytest.raises(io.Refusal, match="invalid output destination"):
        io.run_export({}, lambda value: calls.append(value), str(tmp_path / "out") + "\x00bad")
    assert calls == []
