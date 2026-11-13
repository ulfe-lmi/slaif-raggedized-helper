"""Actual private stores establish stored row-to-vector correspondence."""

import hashlib
import subprocess

import numpy as np
import pytest

from test_raw_snapshot_source_rows_composition import actual, mapwire  # noqa: F401
from slaif_raggedized_helper import derived_store, ingestion_store, raw_snapshot_rows
from slaif_raggedized_helper import raw_snapshot_dense as dense, vector_codec


def test_fresh_stored_bytes_and_causal_control(actual, monkeypatch):  # noqa: F811
    originals, derived, mapping, bundle, _, _ = actual
    data = mapwire(mapping)
    partition = mapping["rows"][0]["partition_id"]
    assert mapping["rows"][0]["batch_row"] == 1

    def forbidden(*args, **kwargs):
        raise AssertionError("unexpected side effect")

    monkeypatch.setattr(subprocess, "Popen", forbidden)
    monkeypatch.setattr(derived_store.Store, "publish", forbidden)
    built = dense.build_partition(originals, derived, data, partition)
    expected = np.eye(3, 1024, dtype="<f4").tobytes()
    assert built.payload_sha256 == hashlib.sha256(expected).hexdigest()
    assert (
        built.row_map_sha256
        == hashlib.sha256(
            raw_snapshot_rows.subset_bytes(raw_snapshot_rows.parse(data), partition)
        ).hexdigest()
    )
    assert (
        dense.parse(built.container_bytes, built.container_sha256, 3).matrix.tobytes() == expected
    )
    assert built.codec_policy_fingerprint == dense.POLICY.fingerprint()
    assert (
        dense.validate_partition(
            originals, derived, data, partition, built.container_bytes, built.container_sha256
        )
        == built
    )
    swapped = vector_codec.encode(np.eye(3, 1024, dtype="<f4")[[1, 0, 2]], dense.POLICY)
    assert dense.parse(swapped.container, swapped.container_sha256, 3).shape == (3, 1024)
    with pytest.raises(dense.DenseError):
        dense.validate_partition(
            originals, derived, data, partition, swapped.container, swapped.container_sha256
        )
    with monkeypatch.context() as patch:
        patch.setattr(dense, "_same_container", lambda left, right: True)
        assert (
            dense.validate_partition(
                originals, derived, data, partition, swapped.container, swapped.container_sha256
            )
            == built
        )
    assert ingestion_store.load(originals, derived, bundle)


def test_fresh_corruption_and_mismatch_refuse(actual):  # noqa: F811
    originals, derived, mapping, bundle, batch, _ = actual
    partition = mapping["rows"][0]["partition_id"]
    data = mapwire(mapping)
    blob = next((originals.root / "blobs").iterdir())
    saved = blob.read_bytes()
    try:
        blob.write_bytes(b"corrupt")
        with pytest.raises(dense.DenseError):
            dense.build_partition(originals, derived, data, partition)
    finally:
        blob.write_bytes(saved)
    snapshot = derived.load(batch)
    metadata = derived_store._parse(snapshot.manifest)["metadata"]
    obj = originals.root / "derived" / "v1" / "objects" / metadata["vector_container_sha256"]
    saved = obj.read_bytes()
    try:
        obj.write_bytes(b"corrupt")
        with pytest.raises(dense.DenseError):
            dense.build_partition(originals, derived, data, partition)
    finally:
        obj.write_bytes(saved)
    mapping["rows"][0]["batch_row"], mapping["rows"][1]["batch_row"] = (
        mapping["rows"][1]["batch_row"],
        mapping["rows"][0]["batch_row"],
    )
    with pytest.raises(dense.DenseError):
        dense.build_partition(originals, derived, mapwire(mapping), partition)
    assert ingestion_store.load(originals, derived, bundle)


def test_unselected_unavailable_partition_is_not_loaded(actual):  # noqa: F811
    originals, derived, mapping, _, _, _ = actual
    partition = mapping["rows"][0]["partition_id"]
    other = dict(mapping["rows"][0])
    other.update(
        partition_id="sha256:" + "f" * 64,
        chunk_id="sha256:" + "e" * 64,
        representation_id="e" * 64,
        batch_container_id="e" * 64,
        bundle_container_id="e" * 64,
        batch_row=0,
        partition_row=0,
    )
    assert partition < other["partition_id"]
    other["ordinal"] = len(mapping["rows"])
    mapping["rows"].append(other)
    result = dense.build_partition(originals, derived, mapwire(mapping), partition)
    assert result.row_count == 3
