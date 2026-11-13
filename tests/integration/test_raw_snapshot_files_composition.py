"""Whole file-set checks against actual synthetic stored sources."""

import dataclasses
import hashlib
import json
import os
import subprocess
import sys
import types
from pathlib import Path

import numpy as np
import pytest

from slaif_raggedized_helper import derived_store, ingestion_store, vector_codec
from slaif_raggedized_helper import raw_snapshot_dense as dense, raw_snapshot_files as files
from slaif_raggedized_helper import (
    raw_snapshot_lexical as lexical,
    raw_snapshot_membership as membership,
)
from slaif_raggedized_helper import technical_analyzer
from test_raw_snapshot_rows import core_for, enc
from test_raw_snapshot_source_rows_composition import actual, mapwire  # noqa: F401


def complete(originals, derived, mapping, ids, withdrawn=()):
    data = mapwire(mapping)
    member = membership.build(
        originals, derived, data, tuple(sorted(ids)), tuple(sorted(withdrawn))
    )
    core = core_for(mapping)
    for key in ("space_id", "definition_fingerprint", "normalization_policy_id"):
        core["embedding"][key] = mapping[key]
    for key in ("chunk_policy_fingerprint", "representation_policy_fingerprint"):
        core[key] = mapping[key]
    core["analyzer"]["fingerprint"] = technical_analyzer.analyzer_id(technical_analyzer.Policy())[
        7:
    ]
    core["sources"]["active_revisions"] = [e.revision_id for e in member.entries]
    core["sources"]["withdrawn_revisions"] = list(member.withdrawn_revisions)
    payloads = {"map": data, "members": member.membership_bytes}
    for part in core["partitions"]:
        p = part["partition_id"]
        payloads[part["dense_path"]] = dense.build_partition(
            originals, derived, data, p
        ).container_bytes
        payloads[part["lexical_path"]] = lexical.build_partition(originals, derived, data, p)
    for desc in core["files"]:
        blob = payloads[desc["path"]]
        desc.update(bytes=len(blob), sha256=hashlib.sha256(blob).hexdigest())
    return core, tuple(sorted(payloads.items()))


def rehash(core, payloads):
    for d in core["files"]:
        b = dict(payloads)[d["path"]]
        d.update(bytes=len(b), sha256=hashlib.sha256(b).hexdigest())
    return enc(core)


def test_complete_actual_and_semantic_guards(actual, monkeypatch):  # noqa: F811
    originals, derived, mapping, bundle, batch, _ = actual
    core, supplied = complete(originals, derived, mapping, (bundle,))
    assert mapping["rows"][0]["batch_row"] == 1

    def forbidden(*args, **kwargs):
        raise AssertionError("unexpected side effect")

    monkeypatch.setattr(subprocess, "Popen", forbidden)
    monkeypatch.setattr(derived_store.Store, "publish", forbidden)
    with monkeypatch.context() as patch:
        patch.setattr(os, "write", forbidden)
        result = files.validate_files(originals, derived, enc(core), supplied)
    assert result.snapshot_id == "sha256:" + hashlib.sha256(enc(core)).hexdigest()
    part = result.partitions[0]
    assert (
        dense.parse(part.dense.container_bytes, part.dense.container_sha256, 3).matrix.tobytes()
        == np.eye(3, 1024, dtype="<f4").tobytes()
    )
    assert part.lexical.record_bytes == dict(supplied)[core["partitions"][0]["lexical_path"]]
    assert tuple(r.chunk_id for r in part.lexical.rows) == tuple(
        r["chunk_id"] for r in mapping["rows"]
    )
    assert part.lexical.rows[0].terms
    with pytest.raises(dataclasses.FrozenInstanceError):
        part.lexical.rows[0].ordinal = 4
    assert ingestion_store.load(originals, derived, bundle)
    p = core["partitions"][0]
    altered = dict(supplied)
    altered[p["dense_path"]] = vector_codec.encode(
        np.eye(3, 1024, dtype="<f4")[[1, 0, 2]], dense.POLICY
    ).container
    updated = tuple(sorted(altered.items()))
    with pytest.raises(files.SnapshotFilesError):
        files.validate_files(originals, derived, rehash(core, updated), updated)
    altered = dict(supplied)
    terms = json.loads(altered[p["lexical_path"]])
    terms["rows"][0]["terms"][0]["text"] = "forged"
    altered[p["lexical_path"]] = enc(terms)
    updated = tuple(sorted(altered.items()))
    with pytest.raises(files.SnapshotFilesError):
        files.validate_files(originals, derived, rehash(core, updated), updated)
    rehash(core, supplied)
    blob = next((originals.root / "blobs").iterdir())
    old = blob.read_bytes()
    try:
        blob.write_bytes(b"corrupt")
        with pytest.raises(files.SnapshotFilesError):
            files.validate_files(originals, derived, enc(core), supplied)
    finally:
        blob.write_bytes(old)
    snapshot = derived.load(batch)
    obj = (
        originals.root
        / "derived"
        / "v1"
        / "objects"
        / derived_store._parse(snapshot.manifest)["metadata"]["vector_container_sha256"]
    )
    old = obj.read_bytes()
    try:
        obj.write_bytes(b"corrupt")
        with pytest.raises(files.SnapshotFilesError):
            files.validate_files(originals, derived, enc(core), supplied)
    finally:
        obj.write_bytes(old)


def test_empty_zero_selected(actual):  # noqa: F811
    originals, derived, mapping, bundle, _, _ = actual
    mapping["rows"] = []
    core, supplied = complete(originals, derived, mapping, (bundle,))
    result = files.validate_files(originals, derived, enc(core), supplied)
    assert not result.partitions and result.membership.entries[0].ordinals == ()
    empty, empty_files = complete(originals, derived, mapping, (), ("sha256:" + "e" * 64,))
    assert files.validate_files(
        originals, derived, enc(empty), empty_files
    ).membership.withdrawn_revisions


def test_file_shape_refused_before_store_io(actual, monkeypatch):  # noqa: F811
    originals, derived, mapping, bundle, _, _ = actual
    core, supplied = complete(originals, derived, mapping, (bundle,))

    def forbidden(*args, **kwargs):
        raise AssertionError("store accessed")

    monkeypatch.setattr(derived_store.Store, "load", forbidden)
    bad = [
        supplied[:-1],
        supplied + (("zz", b"x"),),
        tuple(reversed(supplied)),
        (supplied[0], supplied[0], *supplied[2:]),
        list(supplied),
        ((supplied[0][0], bytearray(supplied[0][1])), *supplied[1:]),
        (("wrong", supplied[0][1]), *supplied[1:]),
        ((supplied[0][0], supplied[0][1] + b"x"), *supplied[1:]),
        ((supplied[0][0], b"x" * len(supplied[0][1])), *supplied[1:]),
    ]
    for value in bad:
        with pytest.raises(files.SnapshotFilesError):
            files.validate_files(originals, derived, enc(core), value)
    core["files"][0]["bytes"] += 1
    with pytest.raises(files.SnapshotFilesError):
        files.validate_files(originals, derived, enc(core), supplied)


def test_declared_mismatches_and_closed_stores(actual):  # noqa: F811
    originals, derived, mapping, bundle, _, _ = actual
    core, supplied = complete(originals, derived, mapping, (bundle,))
    for mutate in (
        lambda c: c["embedding"].update(space_id="e" * 64),
        lambda c: c["embedding"].update(definition_fingerprint="sha256:" + "e" * 64),
        lambda c: c["embedding"].update(corpus_execution_fingerprints=["e" * 64]),
        lambda c: c.update(chunk_policy_fingerprint="e" * 64),
        lambda c: c["partitions"][0].update(row_map_sha256="e" * 64),
        lambda c: c["sources"].update(active_revisions=[]),
        lambda c: c["validation"].update(state="failed"),
    ):
        c = json.loads(enc(core))
        mutate(c)
        with pytest.raises(files.SnapshotFilesError):
            files.validate_files(originals, derived, enc(c), supplied)
    derived.close()
    with pytest.raises(files.SnapshotFilesError):
        files.validate_files(originals, derived, enc(core), supplied)


def test_analyzer_control_with_full_actual_partitions(actual):  # noqa: F811
    originals, derived, mapping, bundle, _, _ = actual
    core, supplied = complete(originals, derived, mapping, (bundle,))
    core["analyzer"]["fingerprint"] = "f" * 64
    with pytest.raises(files.SnapshotFilesError):
        files.validate_files(originals, derived, enc(core), supplied)
    source = Path(files.__file__).read_bytes()
    needle = b'and obj["analyzer"]["fingerprint"] == analyzer[7:]'
    assert source.count(needle) == 1
    control = source.replace(needle, b"and True")
    name = "slaif_raggedized_helper._files_control_full"
    module = types.ModuleType(name)
    module.__package__ = files.__package__
    sys.modules[name] = module
    try:
        exec(compile(control, "<owned-control>", "exec"), module.__dict__)
        assert module.validate_files(originals, derived, enc(core), supplied).partitions
    finally:
        del sys.modules[name]
    with pytest.raises(files.SnapshotFilesError):
        files.validate_files(originals, derived, enc(core), supplied)
    print("source_sha256=" + hashlib.sha256(source).hexdigest())
    print("control_sha256=" + hashlib.sha256(control).hexdigest())


def test_updated_hash_corruptions_reach_binding(actual):  # noqa: F811
    originals, derived, mapping, bundle, _, _ = actual
    core, supplied = complete(originals, derived, mapping, (bundle,))
    member = json.loads(dict(supplied)["members"])
    member["entries"][0]["scope"]["document_id"] += "-forged"
    changed = dict(supplied)
    changed["members"] = enc(member)
    changed = tuple(sorted(changed.items()))
    c = json.loads(enc(core))
    with pytest.raises(files.SnapshotFilesError):
        files.validate_files(originals, derived, rehash(c, changed), changed)
    c = json.loads(enc(core))
    altered = json.loads(dict(supplied)["map"])
    altered["rows"][0]["batch_row"], altered["rows"][1]["batch_row"] = (
        altered["rows"][1]["batch_row"],
        altered["rows"][0]["batch_row"],
    )
    new_map = enc(altered)
    changed = dict(supplied)
    changed["map"] = new_map
    member = json.loads(changed["members"])
    member["row_map_sha256"] = hashlib.sha256(new_map).hexdigest()
    changed["members"] = enc(member)
    from slaif_raggedized_helper import raw_snapshot_rows

    c["partitions"][0]["row_map_sha256"] = dict(raw_snapshot_rows.parse(new_map).partition_hashes)[
        c["partitions"][0]["partition_id"]
    ]
    changed = tuple(sorted(changed.items()))
    with pytest.raises(files.SnapshotFilesError):
        files.validate_files(originals, derived, rehash(c, changed), changed)


def test_empty_inventory_does_not_load(actual, monkeypatch):  # noqa: F811
    originals, derived, mapping, _, _, _ = actual
    mapping["rows"] = []
    core, supplied = complete(originals, derived, mapping, ())

    def forbidden(*args, **kwargs):
        raise AssertionError("unexpected load")

    monkeypatch.setattr(derived_store.Store, "load", forbidden)
    assert not files.validate_files(originals, derived, enc(core), supplied).membership.entries
