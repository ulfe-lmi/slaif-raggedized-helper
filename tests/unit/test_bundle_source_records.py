import json
import hashlib
from dataclasses import asdict

from slaif_raggedized_helper.source_admission import OriginalStore, parse_manifest

import pytest

from slaif_raggedized_helper import bundle_source_records as b, structured_text as s


def make(tmp_path, text, media="text/markdown"):
    root = tmp_path / "input"
    root.mkdir()
    raw = text.encode()
    (root / "a").write_bytes(raw)
    base = dict(
        logical_id="a",
        relative_path="a",
        display_uri="urn:test",
        corpus="c",
        access_labels=[],
        processing_approved=True,
        redistribution_rights="allowed",
        media_type=media,
        size=len(raw),
        sha256=hashlib.sha256(raw).hexdigest(),
    )
    sources = parse_manifest(
        json.dumps(
            {
                "schema_version": 1,
                "sources": [
                    base,
                    dict(
                        base,
                        logical_id="b",
                        version="v2",
                        access_labels=["secret"],
                        redistribution_rights="prohibited",
                    ),
                ],
            }
        ).encode()
    ).sources
    store = OriginalStore(tmp_path / "store")
    return store, [store.admit(root, source) for source in sources]


def serialize(result):
    header = dict(
        dependency=result.dependency.model_dump(),
        adapter="structured_text",
        status="complete_text",
        coverage_kind="unicode_codepoints",
        uncertainty=result.uncertainty,
    )
    blocks = b"".join(x.model_dump_json().encode() + b"\n" for x in result.blocks)
    coverage = dict(
        schema_version=1, kind="unicode_codepoints", spans=[asdict(x) for x in result.coverage]
    )
    return json.dumps(header).encode(), blocks, json.dumps(coverage).encode(), len(result.blocks)


def dump(value):
    return json.dumps(value).encode()


def test_mutations_refused(tmp_path):
    store, revisions = make(
        tmp_path, "# heading\n\n1. WARNING\n\n| A | B |\n| --- | --- |\n| x | V |\ntail"
    )
    rev = revisions[0].revision_id
    header, stream, coverage, count = serialize(s.extract(store, rev))
    h, c = json.loads(header), json.loads(coverage)
    lines = [json.loads(line) for line in stream.splitlines()]
    cases = []
    for key, value in [
        ("adapter", "pdf_extraction"),
        ("status", "partial"),
        ("coverage_kind", "bytes"),
        ("uncertainty", "forged"),
    ]:
        cases.append((dump({**h, key: value}), stream, coverage, count))
    cases.extend(
        [
            (dump({**h, "extra": 1}), stream, coverage, count),
            (b'{"adapter":1,"adapter":2}', stream, coverage, count),
            (b"\xff", stream, coverage, count),
            (header, stream, coverage, True),
            (header, stream, coverage, count + 1),
        ]
    )
    for key, value in [
        ("revision_id", "sha256:" + "0" * 64),
        ("extraction_id", "sha256:" + "0" * 64),
        ("definition", "{}"),
    ]:
        cases.append(
            (dump({**h, "dependency": {**h["dependency"], key: value}}), stream, coverage, count)
        )
    for key, value in [
        ("kind", "code"),
        ("anchor", "forged"),
        ("text", "forged"),
        ("text_sha256", "0" * 64),
        ("origin", "visual_transcription"),
        ("page_ref", "p1"),
        ("crop_ref", "c1"),
        ("geometry", [0.0, 0.0, 1.0, 1.0]),
        ("uncertainty", "forged"),
    ]:
        mutated = [{**lines[0], key: value}, *lines[1:]]
        cases.append((header, b"".join(dump(x) + b"\n" for x in mutated), coverage, count))
    cases.extend(
        [
            (header, b"".join(dump(x) + b"\n" for x in lines[::-1]), coverage, count),
            (header, b"".join(dump(x) + b"\n" for x in lines[:-1]), coverage, count),
            (
                header,
                b"".join(dump(x) + b"\n" for x in [lines[0], *lines[1:-1], lines[0]]),
                coverage,
                count,
            ),
        ]
    )
    for spans in (
        [{**c["spans"][0], "start": 1}, *c["spans"][1:]],
        [{**c["spans"][0], "end": c["spans"][0]["end"] + 1}, *c["spans"][1:]],
        c["spans"][::-1],
        c["spans"][:-1],
        [*c["spans"][:-1], {**c["spans"][-1], "end": c["spans"][-1]["end"] - 1}],
    ):
        cases.append((header, stream, dump({**c, "spans": spans}), count))
    cases.extend(
        [
            (header, stream, dump({**c, "kind": "bytes"}), count),
            (header, stream, dump({**c, "extra": 1}), count),
        ]
    )
    try:
        for args in cases:
            with pytest.raises(b.BundleSourceError, match="^source bundle records refused$"):
                b.validate(store, rev, *args)
    finally:
        store.close()


def test_admission_precedes_parse_and_store(tmp_path, monkeypatch):
    store, revisions = make(tmp_path, "text")
    calls = []

    def forbidden(*args, **kwargs):
        calls.append(True)
        raise AssertionError("early work")

    monkeypatch.setattr(b.bounded, "_parse", forbidden)
    monkeypatch.setattr(s, "extract", forbidden)
    try:
        for args in [
            (object(), revisions[0].revision_id, b"", b"", b"", 1),
            (store, "bad", b"", b"", b"", 1),
            (store, revisions[0].revision_id, bytearray(), b"", b"", 1),
            (store, revisions[0].revision_id, b"x" * (b.HEADER_BYTES + 1), b"", b"", 1),
            (store, revisions[0].revision_id, b"", b"x" * (b.jl.MAX_BYTES + 1), b"", 1),
            (store, revisions[0].revision_id, b"", b"", b"x" * (b.COVERAGE_BYTES + 1), 1),
            (store, revisions[0].revision_id, b"", b"", b"", 0),
        ]:
            with pytest.raises(b.BundleSourceError):
                b.validate(*args)
        assert calls == []
    finally:
        store.close()


def test_empty_and_deadline(tmp_path, monkeypatch):
    store, revisions = make(tmp_path, "")
    try:
        result = s.extract(store, revisions[0].revision_id)
        with pytest.raises(b.BundleSourceError):
            b.validate(store, revisions[0].revision_id, *serialize(result))
        times = iter([0, 31])
        monkeypatch.setattr(b.time, "monotonic", lambda: next(times))
        with pytest.raises(b.BundleSourceError):
            b.validate(store, revisions[0].revision_id, b"{}", b"", b"{}", 1)
    finally:
        store.close()


def test_tree_limits_and_final_deadline(tmp_path, monkeypatch):
    store, revisions = make(tmp_path, "text")
    rev = revisions[0].revision_id
    args = serialize(s.extract(store, rev))
    try:
        deep = b'{"x":' * 20 + b"0" + b"}" * 20
        many = dump({"x": [0] * 10001})
        for bad in (deep, many):
            with pytest.raises(b.BundleSourceError):
                b.validate(store, rev, bad, *args[1:])
        original = b._canonical
        calls = []

        def expire(value):
            result = original(value)
            calls.append(1)
            if len(calls) == 2:
                monkeypatch.setattr(b.time, "monotonic", lambda: 1000)
            return result

        monkeypatch.setattr(b.time, "monotonic", lambda: 0)
        monkeypatch.setattr(b, "_canonical", expire)
        with pytest.raises(b.BundleSourceError):
            b.validate(store, rev, *args)
        assert len(calls) == 2
    finally:
        store.close()
