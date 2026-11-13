import json
from dataclasses import asdict

import pytest

from slaif_raggedized_helper import corpus_embedding_program as cp, retrieval_representation as rr


def data():
    def h(n):
        return format(n, "064x")

    rows = [
        dict(
            ordinal=i,
            source_index=0,
            chunk_id="sha256:" + h(i + 1),
            rendered_sha256=h(i + 8),
            codepoints=3,
            native_request_bytes=100,
        )
        for i in range(3)
    ]
    doc = dict(
        schema=1,
        kind="embedding-source-program-v1",
        token_eligibility="NOT_RUN",
        representation_policy=asdict(rr.Policy()),
        batch_policy=asdict(rr.BatchPolicy(max_items=2)),
        program_policy=asdict(cp.ProgramPolicy()),
        sources=[
            dict(
                bundle_id=h(1),
                bundle_metadata_sha256=h(2),
                revision_id="sha256:" + h(3),
                extraction_id="sha256:" + h(4),
                source_scope_sha256=h(5),
                first_ordinal=0,
                row_count=3,
            )
        ],
        rows=rows,
        batches=[
            dict(
                batch_index=0,
                source_index=0,
                first_ordinal=0,
                row_count=2,
                total_codepoints=6,
                total_native_request_bytes=200,
            ),
            dict(
                batch_index=1,
                source_index=0,
                first_ordinal=2,
                row_count=1,
                total_codepoints=3,
                total_native_request_bytes=100,
            ),
        ],
    )
    return doc


def test_parse_data_and_reject_aliases():
    doc = data()
    raw = cp._encode(doc)
    value = cp.parse(raw)
    assert value.row_count == 3 and value.batch_count == 2
    assert [len(b.chunk_ids) for b in value.batches] == [2, 1]
    for bad in (
        raw + b" ",
        raw.replace(b'"schema":1', b'"schema":true'),
        raw.replace(b'"schema":1', b'"schema":1,"schema":1'),
        raw.replace(b'"row_count":3', b'"row_count":4'),
    ):
        with pytest.raises(cp.ProgramError):
            cp.parse(bad)
    doc["rows"][1]["chunk_id"] = doc["rows"][0]["chunk_id"]
    with pytest.raises(cp.ProgramError):
        cp.parse(cp._encode(doc))


def test_render_wire_exact_unicode_and_bounds():
    text, count = rr._format_raw("Ž", ("😀", ""), "e\u0301", rr.Policy())
    assert text == "Ž\n\n😀\n\ne\u0301"
    wire = (
        json.dumps(
            dict(text=text, pair=None, nonce="0" * 32, role="bge_representation", artifact=0),
            ensure_ascii=True,
            separators=(",", ":"),
        ).encode()
        + b"\n"
    )
    assert count == len(wire)
    with pytest.raises(ValueError):
        rr._format_raw(None, (), "😀" * 20000, rr.Policy())
    policy = cp.ProgramPolicy()
    object.__setattr__(policy, "max_rows", True)
    with pytest.raises(cp.ProgramError):
        cp.build(None, None, ("0" * 64,), program_policy=policy)


def test_large_structural_data_only():
    doc = data()
    h = lambda n: format(n, "064x")  # noqa: E731
    doc["rows"] = [
        dict(
            ordinal=i,
            source_index=0,
            chunk_id="sha256:" + h(i + 1),
            rendered_sha256=h(i + 1),
            codepoints=3,
            native_request_bytes=100,
        )
        for i in range(20000)
    ]
    doc["sources"][0]["row_count"] = 20000
    doc["batch_policy"]["max_items"] = 128
    doc["batches"] = [
        dict(
            batch_index=i // 128,
            source_index=0,
            first_ordinal=i,
            row_count=min(128, 20000 - i),
            total_codepoints=3 * min(128, 20000 - i),
            total_native_request_bytes=100 * min(128, 20000 - i),
        )
        for i in range(0, 20000, 128)
    ]
    value = cp.parse(cp._encode(doc))
    assert value.row_count == 20000 and value.batch_count == 157
