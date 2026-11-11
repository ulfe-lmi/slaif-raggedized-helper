import json

import pytest

from slaif_raggedized_helper import bundle_pdf_records as boundary
from slaif_raggedized_helper import pdf_extraction as pdf, provenance_jsonl as jl
from test_pdf_extraction_composition import (
    configured_runtime,
    make_store,
    nested_form_pdf,
    tiny_pdf,
    visual_pdf,
)


def encode(result):
    header = dict(
        dependency=result.dependency.model_dump(),
        adapter="pdf_extraction",
        status=result.status,
        coverage_kind="pdf_pages",
        uncertainty=result.uncertainty,
    )
    coverage = dict(
        schema_version=1, kind="pdf_pages", pages=[dict(page=n, status=s) for n, s in result.pages]
    )
    blocks = jl.encode("Block", tuple(b.model_dump_json().encode() for b in result.blocks))
    return json.dumps(header).encode(), blocks, json.dumps(coverage).encode()


@pytest.mark.parametrize(
    "data",
    [
        tiny_pdf(),
        tiny_pdf(2),
        nested_form_pdf(),
        visual_pdf("raster"),
        visual_pdf("vector"),
        visual_pdf("raster", text=False),
    ],
)
def test_actual_fixed_producer_roundtrip(tmp_path, monkeypatch, data):
    store, revision = make_store(tmp_path, data)
    try:
        result = pdf.extract(store, revision.revision_id, configured_runtime())
        header, blocks, coverage = encode(result)
        monkeypatch.setattr(pdf, "_run", lambda *a: pytest.fail("parser launched on load"))
        validated = boundary.validate(
            store, revision.revision_id, header, blocks, coverage, len(result.blocks)
        )
        assert (validated.blocks, validated.pages, validated.status) == (
            result.blocks,
            result.pages,
            result.status,
        )
        assert store.read_original(revision.revision_id) == data
        again = boundary.validate(
            store,
            revision.revision_id,
            validated.header_json,
            validated.blocks_jsonl,
            validated.coverage_json,
            len(result.blocks),
        )
        assert validated == again
        if not result.blocks:
            assert validated.status == "partial_visual_needed"
    finally:
        store.close()


@pytest.fixture
def evidence(tmp_path):
    store, revision = make_store(tmp_path, tiny_pdf(2))
    result = pdf.extract(store, revision.revision_id, configured_runtime())
    header, blocks, coverage = encode(result)
    yield (
        store,
        revision,
        result,
        json.loads(header),
        [json.loads(x) for x in blocks.splitlines()],
        json.loads(coverage),
    )
    store.close()


def invoke(evidence, header, blocks, coverage, count=None):
    store, rev, _, _, _, _ = evidence
    packed = b"".join(json.dumps(x).encode() + b"\n" for x in blocks)
    return boundary.validate(
        store,
        rev.revision_id,
        json.dumps(header).encode(),
        packed,
        json.dumps(coverage).encode(),
        len(blocks) if count is None else count,
    )


@pytest.mark.parametrize(
    "field,value",
    [
        ("order", 3),
        ("kind", "heading"),
        ("origin", "visual_transcription"),
        ("page_ref", "page:2"),
        ("anchor", "page:9"),
        ("crop_ref", "crop:1"),
        ("geometry", [3, 2, 1, 4]),
        ("text_sha256", "0" * 64),
        ("block_id", "wrong"),
        ("uncertainty", "certain"),
        ("text", ""),
        ("revision_id", "wrong"),
        ("extraction_id", "wrong"),
        ("unknown", 1),
    ],
)
def test_bad_block_refused(evidence, field, value):
    _, _, _, header, blocks, coverage = evidence
    blocks[0][field] = value
    with pytest.raises(boundary.PdfRecordsError, match="^pdf source records refused$"):
        invoke(evidence, header, blocks, coverage)


@pytest.mark.parametrize(
    "mutation",
    [
        "missing",
        "reordered",
        "duplicate",
        "boolean",
        "extra",
        "status",
        "empty_native",
        "block_reorder",
        "block_duplicate",
        "count",
        "dependency",
        "policy",
        "header_extra",
    ],
)
def test_inconsistent_records_refused(evidence, mutation):
    _, _, _, header, blocks, coverage = evidence
    if mutation == "missing":
        coverage["pages"].pop()
    if mutation == "reordered":
        coverage["pages"].reverse()
    if mutation == "duplicate":
        coverage["pages"][1] = coverage["pages"][0].copy()
    if mutation == "boolean":
        coverage["pages"][0]["page"] = True
    if mutation == "extra":
        coverage["pages"][0]["extra"] = 1
    if mutation == "status":
        header["status"] = "partial_visual_needed"
    if mutation == "empty_native":
        blocks.pop()
    if mutation == "block_reorder":
        blocks.reverse()
    if mutation == "block_duplicate":
        blocks[1] = blocks[0].copy()
    if mutation == "dependency":
        header["dependency"]["extraction_id"] = "wrong"
    if mutation == "policy":
        header["dependency"]["definition"] = "{}"
    if mutation == "header_extra":
        header["extra"] = 1
    with pytest.raises(boundary.PdfRecordsError):
        invoke(evidence, header, blocks, coverage, 99 if mutation == "count" else None)


def test_corrupt_original_refused(evidence, tmp_path):
    store, revision, _, header, blocks, coverage = evidence
    (tmp_path / "store" / "blobs" / revision.blob).write_bytes(b"corrupt")
    with pytest.raises(boundary.PdfRecordsError):
        invoke(evidence, header, blocks, coverage)


def test_final_deadline_refuses_after_canonicalization(evidence, monkeypatch):
    _, _, _, header, blocks, coverage = evidence
    original = boundary.jl.encode

    def expire(*args):
        result = original(*args)
        monkeypatch.setattr(boundary, "MAX_SECONDS", 0)
        return result

    monkeypatch.setattr(boundary.jl, "encode", expire)
    with pytest.raises(boundary.PdfRecordsError):
        invoke(evidence, header, blocks, coverage)


def test_missing_block_field_refused(evidence):
    _, _, _, header, blocks, coverage = evidence
    del blocks[0]["crop_ref"]
    with pytest.raises(boundary.PdfRecordsError):
        invoke(evidence, header, blocks, coverage)


def test_policy_revalidated_even_with_recomputed_dependency(evidence):
    _, _, _, header, blocks, coverage = evidence
    from slaif_raggedized_helper import provenance_records as provenance

    definition = json.loads(header["dependency"]["definition"])
    definition["max_pages"] = 33
    raw = json.dumps(definition, sort_keys=True, separators=(",", ":"))
    header["dependency"]["definition"] = raw
    header["dependency"]["extraction_id"] = provenance.extraction_id(raw)
    with pytest.raises(boundary.PdfRecordsError):
        invoke(evidence, header, blocks, coverage)


def test_wrong_selected_revision_refused(evidence):
    store, _, _, header, blocks, coverage = evidence
    packed = b"".join(json.dumps(x).encode() + b"\n" for x in blocks)
    with pytest.raises(boundary.PdfRecordsError):
        boundary.validate(
            store,
            "sha256:" + "0" * 64,
            json.dumps(header).encode(),
            packed,
            json.dumps(coverage).encode(),
            len(blocks),
        )
