import hashlib

import pytest

from slaif_raggedized_helper import provenance_jsonl as j


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read(data, count=1, kind="Separator"):
    return j.decode(kind, data, digest(data), count)


def test_canonical_unicode_and_empty():
    raw = '{ "text": "😀é\\r\\n\u2028\u2029", "kind":"separator", "schema_version":1 }'.encode()
    data = j.encode("Separator", (raw,))
    assert (
        data == '{"kind":"separator","schema_version":1,"text":"😀é\\r\\n\u2028\u2029"}\n'.encode()
    )
    assert read(data)[0].text == "😀é\r\n\u2028\u2029"
    assert j.encode("Separator", ()) == b""
    assert read(b"", 0) == ()


@pytest.mark.parametrize(
    "data",
    [
        b"{}",
        b"\n",
        b"{}\r\n",
        b"\xef\xbb\xbf{}\n",
        b"{}\n\n",
        b'{"schema_version":1,"schema_version":1,"kind":"separator","text":"x"}\n',
        b'{"schema_version":1,"kind":"separator","text":"x","extra":1}\n',
        b'{"schema_version":1,"kind":"separator","text":"\\ud800"}\n',
        b'{"schema_version":1,"kind":"separator","text":NaN}\n',
        b"[" * 40 + b"0" + b"]" * 40 + b"\n",
        b"\xff\n",
    ],
)
def test_bad_input(data):
    with pytest.raises(j.JsonlError, match="^invalid JSONL$"):
        read(data)


def test_preflight_and_integrity_before_admission(monkeypatch):
    raw = b'{"schema_version":1,"kind":"separator","text":"x"}'
    calls = []
    monkeypatch.setattr(j.p, "admit_record", lambda *args: calls.append(args))
    for fn in (
        lambda: j.encode("Separator", (raw, object())),
        lambda: j.encode("Separator", (raw,) * 4097),
        lambda: j.encode("Separator", (b"x" * (j.p.MAX_ADMISSION_BYTES + 1),)),
        lambda: j.encode("Separator", (b"x" * j.p.MAX_ADMISSION_BYTES,) * 17),
        lambda: j.decode("Separator", raw + b"\n", "0" * 64, 1),
        lambda: read(raw + b"\n" + raw + b"\n", 1),
        lambda: read(b"x" * (j.p.MAX_ADMISSION_BYTES + 1) + b"\n"),
        lambda: read(b"x" * (j.MAX_BYTES + 1)),
        lambda: j.decode("Separator", b"", digest(b""), True),
        lambda: j.decode("Separator", b"", None, 0),
        lambda: j.decode("unknown", b"", digest(b""), 0),
    ):
        with pytest.raises(j.JsonlError):
            fn()
    assert calls == []


def test_count_boundaries_and_deadline(monkeypatch):
    raw = b'{"schema_version":1,"kind":"separator","text":"x"}'
    data = j.encode("Separator", (raw,) * j.MAX_RECORDS)
    assert len(read(data, j.MAX_RECORDS)) == j.MAX_RECORDS
    for value in (-1, 4097, False, 1.0):
        with pytest.raises(j.JsonlError):
            j.decode("Separator", data, digest(data), value)
    clock = iter((0.0, 5.0))
    monkeypatch.setattr(j.time, "monotonic", lambda: next(clock))
    with pytest.raises(j.JsonlError):
        j.encode("Separator", (raw,))


def test_exact_record_size_and_corruption():
    raw = b'{"schema_version":1,"kind":"separator","text":"x"}'
    padded = raw + b" " * (j.p.MAX_ADMISSION_BYTES - len(raw))
    assert read(padded + b"\n")[0].text == "x"
    assert j.encode("Separator", (padded,)) == j.encode("Separator", (raw,))
    good = raw + b"\n"
    for broken in (good[:-1], good.replace(b'"x"', b'"y"'), good + good):
        with pytest.raises(j.JsonlError):
            j.decode("Separator", broken, digest(good), 1)
    with pytest.raises(j.JsonlError):
        read(good + good, 1)
