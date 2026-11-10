import hashlib
import json
import os

import pytest

from slaif_raggedized_helper.source_admission import AdmissionError, OriginalStore, parse_manifest


def manifest(data=b"hello", **changes):
    source = dict(
        logical_id="doc",
        relative_path="file",
        display_uri="urn:fixture",
        corpus="c",
        access_labels=[],
        processing_approved=True,
        redistribution_rights="unknown",
        media_type="text/plain",
        size=len(data),
        sha256=hashlib.sha256(data).hexdigest(),
    )
    source.update(changes)
    return json.dumps(dict(schema_version=1, sources=[source])).encode()


def source(data=b"hello", **changes):
    return parse_manifest(manifest(data, **changes)).sources[0]


def test_strict_manifest():
    obj = json.loads(manifest())
    del obj["sources"][0]["access_labels"]
    with pytest.raises(AdmissionError, match="invalid manifest"):
        parse_manifest(json.dumps(obj).encode())
    for path in ("../file", "/file", "a//file", "a/./file"):
        with pytest.raises(AdmissionError):
            source(relative_path=path)
    with pytest.raises(AdmissionError):
        parse_manifest(b'{"schema_version":1,"schema_version":1,"sources":[]}')
    with pytest.raises(AdmissionError):
        parse_manifest(b" " * 256001)


def test_open_boundaries(tmp_path):
    root = tmp_path / "input"
    root.mkdir()
    (root / "file").write_bytes(b"hello")
    (root / "link").symlink_to("file")
    (root / "dirlink").symlink_to(root, target_is_directory=True)
    os.mkfifo(root / "pipe")
    store = OriginalStore(tmp_path / "store")
    for path in ("link", "dirlink/file", "pipe"):
        with pytest.raises(AdmissionError):
            store.admit(root, source(relative_path=path))
    with pytest.raises(AdmissionError):
        store.admit(root, source(size=4))
    store.close()


def test_intermediate_replacement_and_growth(tmp_path):
    root = tmp_path / "input"
    (root / "dir").mkdir(parents=True)
    (root / "dir" / "file").write_bytes(b"hello")

    def replace(stage):
        if stage == "directory_opened":
            (root / "dir").rename(root / "moved")
            (root / "dir").symlink_to(root / "moved", target_is_directory=True)

    store = OriginalStore(tmp_path / "store", fault=replace)
    with pytest.raises(AdmissionError):
        store.admit(root, source(relative_path="dir/file"))
    store.close()
    (root / "dir").unlink()
    (root / "moved").rename(root / "dir")
    fired = False

    def grow(stage):
        nonlocal fired
        if stage == "before_read" and not fired:
            fired = True
            with (root / "dir" / "file").open("ab") as f:
                f.write(b"!")

    store = OriginalStore(tmp_path / "store", fault=grow)
    with pytest.raises(AdmissionError):
        store.admit(root, source(relative_path="dir/file"))
    store.close()


def test_corruption_conflict_and_retry(tmp_path):
    root = tmp_path / "input"
    root.mkdir()
    (root / "file").write_bytes(b"hello")

    def interrupt(stage):
        if stage == "after_blob_publish":
            raise RuntimeError("interrupt")

    store = OriginalStore(tmp_path / "store", fault=interrupt)
    with pytest.raises(RuntimeError):
        store.admit(root, source())
    store.close()
    store = OriginalStore(tmp_path / "store")
    assert not list((tmp_path / "store" / "revisions").iterdir())
    revision = store.admit(root, source())
    record = tmp_path / "store" / "revisions" / revision.revision_id[7:]
    record.write_bytes(b'{"schema_version":2}')
    with pytest.raises(AdmissionError):
        store.inspect(revision.revision_id)
    with pytest.raises(AdmissionError):
        store.admit(root, source())
    record.unlink()
    (tmp_path / "store" / "blobs" / revision.blob).write_bytes(b"wrong")
    with pytest.raises(AdmissionError):
        store.admit(root, source())
    store.close()
