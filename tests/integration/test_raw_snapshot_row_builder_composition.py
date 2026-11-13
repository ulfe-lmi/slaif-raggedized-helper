# ruff: noqa: F811
"""Three real-store construction cases, with the existing independent hand map."""

import json

import pytest

from test_raw_snapshot_source_rows_composition import actual, mapwire, wire  # noqa: F401
from slaif_raggedized_helper import derived_store, embedding_batch_store, ingestion_store
from slaif_raggedized_helper import raw_snapshot_row_builder as builder, raw_snapshot_source_rows


def inputs(actual):
    originals, derived, mapping, bundle_id, _, _ = actual
    declaration = {k: v for k, v in mapping.items() if k != "rows"}
    declaration["kind"] = "slaif-raw-row-map-build-declaration-v1"
    groups = tuple(sorted({(bundle_id, r["batch_container_id"]) for r in mapping["rows"]}))
    return originals, derived, mapwire(declaration), groups


def test_actual_positive(actual):
    originals, derived, declaration, groups = inputs(actual)
    result = builder.build(originals, derived, declaration, groups)
    assert result.map_bytes == mapwire(actual[2])
    assert result == builder.build(originals, derived, declaration, groups)
    assert (result.row_count, result.group_count) == (3, 2)
    assert sorted(
        sorted(r["batch_row"] for r in actual[2]["rows"] if r["batch_container_id"] == b)
        for _, b in groups
    ) == [[0], [0, 1]]
    for bundle, batch in groups:
        group = raw_snapshot_source_rows.load_group(
            originals, derived, result.map_bytes, bundle, batch
        )
        assert len(group.vector_payload) == len(group.rows) * 4096
        for i, row in enumerate(group.rows):
            expected = actual[-1].index(
                next(x for x in actual[-1] if x.chunk_id == row.declaration.chunk_id)
            )
            assert (
                group.vector_payload[i * 4096 + expected * 4 : i * 4096 + expected * 4 + 4]
                == b"\x00\x00\x80\x3f"
            )
    assert ingestion_store.load(originals, derived, groups[0][0])
    assert derived.load(groups[0][1])


def test_actual_corruption(actual):
    originals, derived, declaration, groups = inputs(actual)
    before = builder.build(originals, derived, declaration, groups)
    blob = next((originals.root / "blobs").iterdir())
    saved = blob.read_bytes()
    try:
        blob.write_bytes(b"corrupted original")
        with pytest.raises(builder.BuildError):
            builder.build(originals, derived, declaration, groups)
    finally:
        blob.write_bytes(saved)
    assert builder.build(originals, derived, declaration, groups) == before


def test_actual_overlap_and_declarations(actual):
    originals, derived, declaration, groups = inputs(actual)
    bundle, batch = groups[0]
    snapshot = derived.load(batch)
    obj = derived_store._parse(snapshot.manifest)["metadata"]
    obj["dependencies"]["inventory_id"] = "e" * 64
    replacement = embedding_batch_store.publish(derived, wire(obj), snapshot.members[0].data)
    assert replacement != batch
    with pytest.raises(builder.BuildError):
        builder.build(
            originals, derived, declaration, tuple(sorted(((bundle, batch), (bundle, replacement))))
        )
    for field, value in [
        ("definition_fingerprint", "sha256:" + "f" * 64),
        ("chunk_policy_fingerprint", "f" * 64),
    ]:
        obj = json.loads(declaration)
        obj[field] = value
        with pytest.raises(builder.BuildError):
            builder.build(originals, derived, mapwire(obj), groups)
