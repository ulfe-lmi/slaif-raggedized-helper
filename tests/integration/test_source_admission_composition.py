import json

from slaif_raggedized_helper.source_admission import OriginalStore, parse_manifest


def test_public_journey(tmp_path):
    import hashlib

    root = tmp_path / "input"
    root.mkdir()
    data = b"owned synthetic original"
    (root / "a").write_bytes(data)
    (root / "b").write_bytes(data)
    common = dict(
        display_uri="urn:fixture",
        corpus="corpus",
        processing_approved=True,
        media_type="text/plain",
        size=len(data),
        sha256=hashlib.sha256(data).hexdigest(),
    )
    a = dict(
        common, logical_id="a", relative_path="a", access_labels=[], redistribution_rights="allowed"
    )
    b = dict(
        common,
        logical_id="b",
        relative_path="b",
        access_labels=["private"],
        redistribution_rights="prohibited",
    )
    manifest = parse_manifest(json.dumps(dict(schema_version=1, sources=[a, b])).encode())
    store = OriginalStore(tmp_path / "store")
    first, second = [store.admit(root, item) for item in manifest.sources]
    changed = dict(a, title="corrected")
    third = store.admit(
        root,
        parse_manifest(json.dumps(dict(sources=[changed], schema_version=1)).encode()).sources[0],
    )
    assert len({first.revision_id, second.revision_id, third.revision_id}) == 3
    assert len(list((tmp_path / "store" / "blobs").iterdir())) == 1
    assert store.inspect(first.revision_id) == first
    assert store.admit(root, manifest.sources[1]) == second
    assert store.inspect(second.revision_id).source.access_labels == ["private"]
    assert third.source.redistribution_rights == "allowed"
    store.close()
