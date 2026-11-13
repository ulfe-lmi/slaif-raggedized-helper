import hashlib
import json
import subprocess

import pytest

from slaif_raggedized_helper import derived_store, ingestion_store, raw_snapshot_membership as m
from test_raw_snapshot_source_rows_composition import mapwire

from test_raw_snapshot_rows import core_for, enc

pytest_plugins = ("test_raw_snapshot_source_rows_composition",)


def core(mapping, member):
    c = core_for(mapping)
    for key in ("space_id", "definition_fingerprint", "normalization_policy_id"):
        c["embedding"][key] = mapping[key]
    for key in ("chunk_policy_fingerprint", "representation_policy_fingerprint"):
        c[key] = mapping[key]
    c["sources"]["active_revisions"] = [e.revision_id for e in member.entries]
    c["sources"]["withdrawn_revisions"] = list(member.withdrawn_revisions)
    c["files"][1].update(bytes=len(member.membership_bytes), sha256=member.sha256)
    return enc(c)


def test_actual_subset_zero_and_corruption(actual, monkeypatch):
    originals, derived, mapping, ident, _, _ = actual
    mapping["rows"] = mapping["rows"][:1]
    data = mapwire(mapping)

    def forbidden(*args, **kwargs):
        raise AssertionError("unexpected side effect")

    monkeypatch.setattr(subprocess, "Popen", forbidden)
    monkeypatch.setattr(derived_store.Store, "publish", forbidden)
    member = m.build(originals, derived, data, (ident,), ())
    assert member.entries[0].ordinals == (0,)
    assert (
        m.validate(originals, derived, core(mapping, member), data, member.membership_bytes)
        == member
    )
    mapping["rows"] = []
    empty = mapwire(mapping)
    zero = m.build(originals, derived, empty, (ident,), ())
    assert zero.entries[0].ordinals == ()
    assert m.validate(originals, derived, core(mapping, zero), empty, zero.membership_bytes) == zero
    blob = next((originals.root / "blobs").iterdir())
    saved = blob.read_bytes()
    try:
        blob.write_bytes(b"corrupt")
        with pytest.raises(m.MembershipError):
            m.build(originals, derived, empty, (ident,), ())
    finally:
        blob.write_bytes(saved)
    assert ingestion_store.load(originals, derived, ident)


def test_actual_mismatch_and_omission(actual):
    originals, derived, mapping, ident, _, _ = actual
    data = mapwire(mapping)
    with pytest.raises(m.MembershipError):
        m.build(originals, derived, data, (), ())
    with pytest.raises(m.MembershipError):
        m.build(originals, derived, data, ("f" * 64,), ())
    for field in ("bundle_metadata_sha256", "source_scope_sha256", "extraction_id"):
        saved = [r[field] for r in mapping["rows"]]
        for row in mapping["rows"]:
            row[field] = ("sha256:" if field == "extraction_id" else "") + "e" * 64
        with pytest.raises(m.MembershipError):
            m.build(originals, derived, mapwire(mapping), (ident,), ())
        for row, value in zip(mapping["rows"], saved):
            row[field] = value


def test_actual_fresh_correspondence_control(actual):
    import sys
    import types
    from pathlib import Path
    from slaif_raggedized_helper import schema

    originals, derived, mapping, ident, _, _ = actual
    mapping["rows"] = []
    data = mapwire(mapping)
    member = m.build(originals, derived, data, (ident,), ())
    forged = json.loads(member.membership_bytes)
    scope = forged["entries"][0]["scope"]
    scope["document_id"] += "-forged"
    forged["entries"][0]["source_scope_sha256"] = schema.fingerprint(
        dict(kind="embedding-source-scope-v1", scope=scope)
    )[7:]
    forged_bytes = enc(forged)
    declared = m.parse(forged_bytes)
    c = core(mapping, declared)
    assert m.bind(c, data, forged_bytes) == declared
    with pytest.raises(m.MembershipError):
        m.validate(originals, derived, c, data, forged_bytes)
    source = Path(m.__file__).read_bytes()
    old = b"_check(rebuilt.membership_bytes == membership_bytes)"
    new = b"_check(True)"
    assert source.count(old) == 1
    control = source.replace(old, new)
    name = "slaif_raggedized_helper._membership_control"
    module = types.ModuleType(name)
    module.__package__ = "slaif_raggedized_helper"
    sys.modules[name] = module
    try:
        exec(compile(control, "<owned-control>", "exec"), module.__dict__)
        assert (
            module.validate(originals, derived, c, data, forged_bytes).membership_bytes
            == member.membership_bytes
        )
    finally:
        del sys.modules[name]
    print("source_sha256=" + hashlib.sha256(source).hexdigest())
    print("control_sha256=" + hashlib.sha256(control).hexdigest())


def test_two_actual_bundles_and_wrong_existing_bundle(tmp_path):
    from test_native_tokenizers import make_native
    from test_retrieval_representation_composition import make_bundle
    from test_structured_text_composition import create_store
    from test_raw_snapshot_rows import mapping as empty_mapping

    paths, runtime, make = make_native(tmp_path)
    definitions = (
        make(paths[0], "bge_body"),
        make(paths[0], "bge_representation"),
        make(paths[1], "reranker_pair"),
    )
    originals, revisions = create_store(tmp_path, "# Heading\n\nowned text\n")
    derived = derived_store.Store(tmp_path / "store")
    try:
        ids = []
        for revision in revisions[:2]:
            metadata, members, _, _ = make_bundle(originals, revision, definitions, runtime)
            ids.append(ingestion_store.publish(originals, derived, metadata, members))
        first = ingestion_store.load(originals, derived, ids[0])
        rowmap = empty_mapping()
        rowmap["chunk_policy_fingerprint"] = json.loads(first.metadata_json)["chunking"][
            "policy_id"
        ][7:]
        data = enc(rowmap)
        both = m.build(originals, derived, data, tuple(sorted(ids)), ())
        assert len(both.entries) == 2 and all(not e.ordinals for e in both.entries)
        declared = json.loads(both.membership_bytes)
        declared["entries"][0]["bundle_container_id"] = (
            ids[1] if declared["entries"][0]["bundle_container_id"] == ids[0] else ids[0]
        )
        # Preserve distinct IDs while swapping two existing bundle declarations.
        declared["entries"][1]["bundle_container_id"] = (
            ids[0] if declared["entries"][0]["bundle_container_id"] == ids[1] else ids[1]
        )
        forged = m.parse(enc(declared))
        with pytest.raises(m.MembershipError):
            m.validate(originals, derived, core(rowmap, forged), data, forged.membership_bytes)
        assert ingestion_store.load(originals, derived, ids[1])
    finally:
        derived.close()
        originals.close()


def test_exact_full_output_budget_stops_before_later_actual_bundle(tmp_path, monkeypatch):
    from test_native_tokenizers import make_native
    from test_retrieval_representation_composition import make_bundle
    from test_structured_text_composition import create_store
    from test_raw_snapshot_rows import mapping

    paths, runtime, make = make_native(tmp_path)
    definitions = (
        make(paths[0], "bge_body"),
        make(paths[0], "bge_representation"),
        make(paths[1], "reranker_pair"),
    )
    originals, revisions = create_store(tmp_path, "# Heading\n\nowned text\n")
    derived = derived_store.Store(tmp_path / "store")
    try:
        ids = []
        for rev in revisions[:2]:
            metadata, members, _, _ = make_bundle(originals, rev, definitions, runtime)
            ids.append(ingestion_store.publish(originals, derived, metadata, members))
        ids = tuple(sorted(ids))
        bundle = ingestion_store.load(originals, derived, ids[0])
        rowmap = mapping()
        rowmap["chunk_policy_fingerprint"] = json.loads(bundle.metadata_json)["chunking"][
            "policy_id"
        ][7:]
        data = enc(rowmap)
        first = m.build(originals, derived, data, (ids[0],), ())
        assert len(m.build(originals, derived, data, ids, ()).entries) == 2
        actual_load = ingestion_store.load
        seen = []

        def observe(*args):
            seen.append(args[-1])
            return actual_load(*args)

        with monkeypatch.context() as patch:
            patch.setattr(m, "_LIMIT", len(first.membership_bytes))
            patch.setattr(ingestion_store, "load", observe)
            with pytest.raises(m.MembershipError):
                m.build(originals, derived, data, ids, ())
        assert seen == [ids[0]], seen
        print("PASS: exact output budget prevents later actual bundle load")
        print("reduced_test_limit=" + str(len(first.membership_bytes)))
        assert ingestion_store.load(originals, derived, ids[0])
    finally:
        derived.close()
        originals.close()
