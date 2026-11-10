import hashlib
import json
import os

import pytest

from slaif_raggedized_helper.source_admission import AdmissionError, OriginalStore, parse_manifest
from slaif_raggedized_helper.source_cli import _manifest_bytes


def entry(data=b"hello", **updates):
    result = dict(
        logical_id="doc",
        relative_path="file",
        display_uri="urn:test",
        corpus="c",
        access_labels=[],
        processing_approved=True,
        redistribution_rights="unknown",
        media_type="text/plain",
        size=len(data),
        sha256=hashlib.sha256(data).hexdigest(),
    )
    result.update(updates)
    return result


def manifest(*sources):
    return json.dumps(dict(schema_version=1, sources=sources)).encode()


def test_unicode_and_json_boundaries():
    assert (
        parse_manifest(manifest(entry(title="Slovenščina 😀"))).sources[0].title == "Slovenščina 😀"
    )
    for data in (
        b"\xff",
        b"\xff\xfe{\x00}",
        b'{"schema_version":1,"sources":[],"x":NaN}',
        b'{"schema_version":1,"sources":[],"x":"\\ud800"}',
        b'{"schema_version":1,"schema_version":1,"sources":[]}',
    ):
        with pytest.raises(AdmissionError, match="^invalid manifest$"):
            parse_manifest(data)


def test_manifest_descriptor_bounds_and_special_files(tmp_path):
    path = tmp_path / "manifest"
    path.write_bytes(b" " * 256001)
    with pytest.raises(ValueError):
        _manifest_bytes(str(path))
    path.write_bytes(b"{}")
    link = tmp_path / "link"
    link.symlink_to(path)
    with pytest.raises(OSError):
        _manifest_bytes(str(link))
    fifo = tmp_path / "fifo"
    os.mkfifo(fifo)
    with pytest.raises(ValueError):
        _manifest_bytes(str(fifo))


def test_verified_original_reads_and_detects_corruption(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    data = "č😀".encode()
    (root / "file").write_bytes(data)
    store = OriginalStore(tmp_path / "store")
    try:
        revision = store.admit(root, parse_manifest(manifest(entry(data))).sources[0])
        assert store.read_original(revision.revision_id) == data
        blob = tmp_path / "store" / "blobs" / revision.blob
        blob.write_bytes(b"x" * len(data))
        with pytest.raises(AdmissionError, match="^invalid stored revision$"):
            store.read_original(revision.revision_id)
        with pytest.raises(AdmissionError):
            store.read_original("../private-canary")
    finally:
        store.close()


def test_manifest_growth_refused(tmp_path, monkeypatch):
    path = tmp_path / "manifest"
    path.write_bytes(b"{}")
    actual = os.read

    def grow(fd, count):
        with path.open("ab") as f:
            f.write(b"!")
        return actual(fd, count)

    monkeypatch.setattr(os, "read", grow)
    with pytest.raises(ValueError):
        _manifest_bytes(str(path))


def test_verified_read_detects_mid_read_mutation(tmp_path, monkeypatch):
    root = tmp_path / "root"
    root.mkdir()
    (root / "file").write_bytes(b"hello")
    store = OriginalStore(tmp_path / "store")
    try:
        rev = store.admit(root, parse_manifest(manifest(entry())).sources[0])
        blob = tmp_path / "store" / "blobs" / rev.blob
        original = os.read
        fired = False

        def mutate(fd, count):
            nonlocal fired
            result = original(fd, count)
            if not fired and os.fstat(fd).st_ino == blob.stat().st_ino:
                fired = True
                blob.write_bytes(b"HELLO")
            return result

        monkeypatch.setattr(os, "read", mutate)
        with pytest.raises(AdmissionError):
            store.read_original(rev.revision_id)
        assert fired
    finally:
        store.close()
