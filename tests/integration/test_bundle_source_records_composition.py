import hashlib
import json
from dataclasses import asdict

import pytest

from slaif_raggedized_helper import bundle_source_records as b, structured_text as s
from slaif_raggedized_helper.source_admission import OriginalStore, parse_manifest


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


@pytest.mark.parametrize("media", ["text/plain", "text/markdown"])
def test_owned_reparse_and_canonical_roundtrip(tmp_path, media):
    text = ("# Guide 😀\r\n\r\n1. WARNING: isolate e\u0301\r\n  use 12 V\r\n\r\n"
            "| Flow | Unit |\r\n| --- | --- |\r\n| 2 | L/s |\r\ncontrol:\x01 tail")
    store, revisions = make(tmp_path, text, media)
    try:
        for rev in revisions:
            extracted = s.extract(store, rev.revision_id)
            values = serialize(extracted)
            result = b.validate(store, rev.revision_id, *values)
            assert result.blocks == extracted.blocks and result.coverage == extracted.coverage
            assert "".join(x.text for x in result.blocks) == text
            assert result.scope.version == rev.source.version
            again = b.validate(
                store,
                rev.revision_id,
                result.header_json,
                result.blocks_jsonl,
                result.coverage_json,
                len(result.blocks),
            )
            assert again == result
            assert store.read_original(rev.revision_id) == text.encode()
        assert revisions[0].revision_id != revisions[1].revision_id
        assert revisions[0].source.version is None
    finally:
        store.close()


def test_cross_revision_and_altered_original_refuse(tmp_path):
    store, revisions = make(tmp_path, "original\n")
    try:
        values = serialize(s.extract(store, revisions[0].revision_id))
        with pytest.raises(b.BundleSourceError):
            b.validate(store, revisions[1].revision_id, *values)
        (tmp_path / "store" / "blobs" / revisions[0].blob).write_bytes(b"changed!\n")
        with pytest.raises(b.BundleSourceError):
            b.validate(store, revisions[0].revision_id, *values)
    finally:
        store.close()
