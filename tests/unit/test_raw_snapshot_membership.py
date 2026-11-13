import copy
from dataclasses import FrozenInstanceError
import hashlib
import json

import pytest

from slaif_raggedized_helper import raw_snapshot_membership as m, schema
from test_raw_snapshot_rows import core_for, enc, mapping


def declared():
    revision = "sha256:" + "1" * 64
    scope = dict(
        schema_version=1,
        document_id="doc",
        revision_id=revision,
        corpus="c",
        version="v",
        labels=["a"],
        processing_approved=True,
        redistribution_rights="unknown",
    )
    entry = dict(
        revision_id=revision,
        extraction_id="sha256:" + "2" * 64,
        bundle_container_id="3" * 64,
        bundle_metadata_sha256="4" * 64,
        chunk_policy_fingerprint="a" * 64,
        source_scope_sha256=schema.fingerprint(dict(kind="embedding-source-scope-v1", scope=scope))[
            7:
        ],
        partition_id=schema.fingerprint(dict(schema=1, corpus="c", version="v", labels=["a"])),
        scope=scope,
        ordinals=[],
    )
    rowmap = mapping()
    obj = dict(
        schema=1,
        kind="slaif-raw-source-membership-v1",
        row_map_sha256=hashlib.sha256(enc(rowmap)).hexdigest(),
        row_count=0,
        entries=[entry],
        withdrawn_revisions=[],
    )
    return rowmap, obj


def core(rowmap, obj):
    value = core_for(rowmap)
    value["sources"]["active_revisions"] = [e["revision_id"] for e in obj["entries"]]
    value["sources"]["withdrawn_revisions"] = obj["withdrawn_revisions"]
    data = enc(obj)
    value["files"][1].update(bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
    return enc(value)


def test_zero_row_and_immutable():
    rowmap, obj = declared()
    result = m.bind(core(rowmap, obj), enc(rowmap), enc(obj))
    assert result.entries[0].ordinals == ()
    with pytest.raises(FrozenInstanceError):
        result.entries[0].revision_id = "x"
    obj["entries"][0]["scope"]["labels"].append("b")
    assert json.loads(result.entries[0].scope_bytes)["labels"] == ["a"]


@pytest.mark.parametrize(
    "change",
    ["extra", "bool", "float", "digest", "scope", "ordinal", "duplicate", "withdrawn", "labels"],
)
def test_invalid_data(change):
    _, obj = declared()
    e = obj["entries"][0]
    if change == "extra":
        obj["extra"] = 1
    if change == "bool":
        obj["row_count"] = False
    if change == "float":
        obj["row_count"] = 0.0
    if change == "digest":
        e["source_scope_sha256"] = "f" * 64
    if change == "scope":
        e["scope"]["processing_approved"] = False
    if change == "ordinal":
        e["ordinals"] = [0]
    if change == "duplicate":
        obj["entries"].append(copy.deepcopy(e))
    if change == "withdrawn":
        obj["withdrawn_revisions"] = [e["revision_id"]]
    if change == "labels":
        e["scope"]["labels"] = ["z", "a"]
    with pytest.raises(m.MembershipError):
        m.parse(enc(obj))


def test_canonical_and_bounds():
    _, obj = declared()
    data = enc(obj)
    for bad in (data + b"\n", b'{"schema":1,"schema":1}', b" " * (8 * 1048576 + 1)):
        with pytest.raises(m.MembershipError):
            m.parse(bad)


def test_bind_refuses_mismatch():
    rowmap, obj = declared()
    c = core(rowmap, obj)
    altered = copy.deepcopy(obj)
    altered["row_map_sha256"] = "f" * 64
    with pytest.raises(m.MembershipError):
        m.bind(core(rowmap, altered), enc(rowmap), enc(altered))
    value = json.loads(c)
    value["sources"]["active_revisions"] = []
    with pytest.raises(m.MembershipError):
        m.bind(enc(value), enc(rowmap), enc(obj))


def test_interrupt_is_not_wrapped(monkeypatch):
    class Stop(BaseException):
        pass

    def interrupt(_):
        raise Stop()

    monkeypatch.setattr(m, "_parse", interrupt)
    with pytest.raises(Stop):
        m.parse(b"{}")


def test_entry_and_list_limits():
    _, obj = declared()
    obj["withdrawn_revisions"] = ["sha256:" + f"{n:064x}" for n in range(1025)]
    with pytest.raises(m.MembershipError):
        m.parse(enc(obj))
    _, obj = declared()
    obj["entries"][0]["scope"]["document_id"] = "x" * 131073
    with pytest.raises(m.MembershipError):
        m.parse(enc(obj))


def test_nonempty_cross_binding():
    from test_raw_snapshot_rows import row

    rowmap, obj = declared()
    entry = obj["entries"][0]
    r = row(0)
    r.update(
        revision_id=entry["revision_id"],
        extraction_id=entry["extraction_id"],
        bundle_container_id=entry["bundle_container_id"],
        bundle_metadata_sha256=entry["bundle_metadata_sha256"],
        source_scope_sha256=entry["source_scope_sha256"],
        partition_id=entry["partition_id"],
    )
    rowmap["rows"] = [r]
    entry["ordinals"] = [0]
    obj["row_count"] = 1
    obj["row_map_sha256"] = hashlib.sha256(enc(rowmap)).hexdigest()
    assert m.bind(core(rowmap, obj), enc(rowmap), enc(obj)).row_count == 1
    for field in ("extraction_id", "bundle_container_id", "bundle_metadata_sha256"):
        bad = copy.deepcopy(obj)
        bad["entries"][0][field] = ("sha256:" if field == "extraction_id" else "") + "f" * 64
        with pytest.raises(m.MembershipError):
            m.bind(core(rowmap, bad), enc(rowmap), enc(bad))
    bad = copy.deepcopy(rowmap)
    bad["rows"][0]["revision_id"] = "sha256:" + "f" * 64
    obj["row_map_sha256"] = hashlib.sha256(enc(bad)).hexdigest()
    c = json.loads(core(bad, obj))
    # Core accepts only declared active revisions, so both revisions are listed.
    c["sources"]["active_revisions"] = sorted([entry["revision_id"], bad["rows"][0]["revision_id"]])
    with pytest.raises(m.MembershipError):
        m.bind(enc(c), enc(bad), enc(obj))


def test_admission_before_store_access(monkeypatch, tmp_path):
    from slaif_raggedized_helper import derived_store, ingestion_store
    import importlib.util
    from pathlib import Path

    fixture_path = (Path(__file__).resolve().parents[1] / "integration"
                    / "test_structured_text_composition.py")
    spec = importlib.util.spec_from_file_location(
        "_raw_membership_structured_fixture", fixture_path)
    fixture = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fixture)
    create_store = fixture.create_store

    originals, _ = create_store(tmp_path, "source")
    derived = derived_store.Store(tmp_path / "store")
    calls = []
    monkeypatch.setattr(ingestion_store, "load", lambda *args: calls.append(args))
    try:
        for ids, withdrawn in ((("f" * 64, "a" * 64), ()), ((), ("bad",))):
            with pytest.raises(m.MembershipError):
                m.build(originals, derived, enc(mapping()), ids, withdrawn)
        with pytest.raises(m.MembershipError):
            m.build(originals, derived, b"bad", (), ())
        assert not calls
    finally:
        derived.close()
        originals.close()
