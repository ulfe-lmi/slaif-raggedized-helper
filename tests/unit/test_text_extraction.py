import hashlib
import json

import pytest

from slaif_raggedized_helper import text_extraction as t
from slaif_raggedized_helper.source_admission import OriginalStore, parse_manifest


def make_store(tmp_path, data, media="text/markdown", approved=True):
    root = tmp_path / "root"
    root.mkdir()
    (root / "file").write_bytes(data)
    source = dict(
        logical_id="doc",
        relative_path="file",
        display_uri="urn:x",
        corpus="c",
        access_labels=["private"],
        processing_approved=approved,
        redistribution_rights="prohibited",
        media_type=media,
        size=len(data),
        sha256=hashlib.sha256(data).hexdigest(),
    )
    m = parse_manifest(json.dumps(dict(schema_version=1, sources=[source])).encode())
    store = OriginalStore(tmp_path / "store")
    revision = store.admit(root, m.sources[0])
    return store, revision


def test_limits_and_policy():
    for args in (
        {"max_bytes": True},
        {"max_bytes": 0},
        {"max_chars": -1},
        {"max_blocks": 4097},
        {"max_line_chars": 200001},
        {"max_chars": 1.5},
    ):
        with pytest.raises(t.ExtractionError, match="^invalid extraction policy$"):
            t.ExtractionPolicy(**args)
    assert t.ExtractionPolicy().fingerprint != t.ExtractionPolicy(max_bytes=3).fingerprint


def test_exact_classification_and_unclosed_fence(tmp_path):
    text = "# Naslov 😀\r\n\r\n- Opozorilo e\u0301\n```sh\nrm --example\n# not heading\n"
    store, revision = make_store(tmp_path, text.encode())
    try:
        result = t.extract(store, revision.revision_id)
        assert "".join(block.text for block in result.blocks) == text
        assert [b.kind for b in result.blocks] == [
            "heading",
            "text",
            "list",
            "code",
            "code",
            "code",
        ]
        assert [b.anchor for b in result.blocks] == [f"line:{n}" for n in range(1, 7)]
        assert all(b.origin == "native" and b.geometry is None for b in result.blocks)
        assert t.extract(store, revision.revision_id) == result
        changed = t.extract(store, revision.revision_id, t.ExtractionPolicy(max_bytes=1000))
        assert changed.dependency.extraction_id != result.dependency.extraction_id
        assert changed.blocks[0].block_id != result.blocks[0].block_id
    finally:
        store.close()


def test_narrow_limits_and_empty(tmp_path):
    store, rev = make_store(tmp_path, b"abc\ndef")
    try:
        for policy in (
            t.ExtractionPolicy(max_bytes=3),
            t.ExtractionPolicy(max_chars=3),
            t.ExtractionPolicy(max_blocks=1),
            t.ExtractionPolicy(max_line_chars=3),
        ):
            with pytest.raises(t.ExtractionError, match="^extraction refused$"):
                t.extract(store, rev.revision_id, policy)
    finally:
        store.close()


def test_invalid_utf8_media_corruption_and_safe_errors(tmp_path):
    for name, data, media in [
        ("bad", b"\xff", "text/plain"),
        ("pdf", b"%PDF-test", "application/pdf"),
    ]:
        sub = tmp_path / name
        sub.mkdir()
        store, rev = make_store(sub, data, media)
        try:
            with pytest.raises(t.ExtractionError, match="^extraction refused$"):
                t.extract(store, rev.revision_id)
        finally:
            store.close()
    sub = tmp_path / "corrupt"
    sub.mkdir()
    store, rev = make_store(sub, b"private-canary")
    try:
        (sub / "store" / "blobs" / rev.blob).write_bytes(b"corrupt")
        with pytest.raises(t.ExtractionError, match="^extraction refused$") as error:
            t.extract(store, rev.revision_id)
        assert "private-canary" not in str(error.value)
    finally:
        store.close()


def test_deadline_refusal_no_partial_and_forged_policy(tmp_path, monkeypatch):
    store, rev = make_store(tmp_path, b"first\nsecond\n")
    try:
        fake = iter([0.0, 0.0, 0.0, 0.0, 0.0, 6.0])
        monkeypatch.setattr(t.time, "monotonic", lambda: next(fake))
        with pytest.raises(t.ExtractionError, match="^extraction refused$"):
            t.extract(store, rev.revision_id)
        forged = t.ExtractionPolicy()
        object.__setattr__(forged, "max_blocks", True)
        with pytest.raises(t.ExtractionError):
            t.extract(store, rev.revision_id, forged)
    finally:
        store.close()


def test_empty_and_plain_text_are_explicit(tmp_path):
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    store, rev = make_store(empty_dir, b"", "text/plain")
    try:
        result = t.extract(store, rev.revision_id)
        assert result.blocks == () and result.revision.source.size == 0
    finally:
        store.close()
    plain_dir = tmp_path / "plain"
    plain_dir.mkdir()
    store, rev = make_store(plain_dir, b"# literal\n- literal\n", "text/plain")
    try:
        result = t.extract(store, rev.revision_id)
        assert [b.kind for b in result.blocks] == ["text", "text"]
        assert "".join(b.text for b in result.blocks) == "# literal\n- literal\n"
    finally:
        store.close()
