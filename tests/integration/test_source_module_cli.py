import hashlib
import json
import os
import subprocess
import sys

from slaif_raggedized_helper.source_admission import OriginalStore


def run(*args):
    return subprocess.run(
        [sys.executable, "-m", "slaif_raggedized_helper.source_cli", *map(str, args)],
        capture_output=True,
        text=True,
        timeout=5,
        env=os.environ.copy(),
    )


def test_import_inspect_retry_and_partial(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    data = "Živjo 😀\n".encode()
    (root / "a").write_bytes(data)
    (root / "b").write_bytes(data)
    common = dict(
        display_uri="urn:inert",
        processing_approved=True,
        media_type="text/plain",
        size=len(data),
        sha256=hashlib.sha256(data).hexdigest(),
        version="1",
    )
    a = dict(
        common,
        logical_id="a",
        relative_path="a",
        corpus="one",
        access_labels=[],
        redistribution_rights="allowed",
    )
    b = dict(
        common,
        logical_id="b",
        relative_path="b",
        corpus="two",
        access_labels=["private"],
        redistribution_rights="prohibited",
    )
    manifest = tmp_path / "manifest"

    def write(items):
        manifest.write_text(
            json.dumps(dict(schema_version=1, sources=items), ensure_ascii=False), encoding="utf-8"
        )

    write([a, b])
    store_path = tmp_path / "store"
    args = ("import", "--root", root, "--store", store_path, "--manifest", manifest)
    first = run(*args)
    assert first.returncode == 0, first.stderr
    ids = json.loads(first.stdout)["revisions"]
    assert len(set(ids)) == 2
    assert json.loads(run(*args).stdout)["revisions"] == ids
    assert len(list((store_path / "blobs").iterdir())) == 1
    inspect = run("inspect", "--store", store_path, "--revision", ids[1])
    assert inspect.returncode == 0
    source = json.loads(inspect.stdout)["revision"]["source"]
    assert (source["corpus"], source["access_labels"], source["redistribution_rights"]) == (
        "two",
        ["private"],
        "prohibited",
    )
    store = OriginalStore(store_path)
    try:
        assert store.read_original(ids[0]) == data == store.read_original(ids[1])
    finally:
        store.close()
    write([dict(a, title="naslov č😀")])
    third = json.loads(run(*args).stdout)["revisions"][0]
    assert third not in ids
    changed = dict(a, title="newly published")
    write([changed, dict(b, relative_path="missing")])
    failure = run(*args)
    assert failure.returncode != 0
    err = json.loads(failure.stderr)
    assert err["stage"] == "import" and len(err["completed_revisions"]) == 1
    partial_id = err["completed_revisions"][0]
    assert partial_id not in ids and partial_id != third
    assert run("inspect", "--store", store_path, "--revision", partial_id).returncode == 0
    assert err["current_document"] == "unknown"
    write([changed, b])
    assert json.loads(run(*args).stdout)["revisions"] == [partial_id, ids[1]]


def test_preflight_safe_errors_and_help(tmp_path):
    root = tmp_path / "private-canary"
    root.mkdir()
    data = b"synthetic"
    (root / "file").write_bytes(data)
    source = dict(
        logical_id="x",
        relative_path="file",
        display_uri="urn:x",
        corpus="c",
        access_labels=[],
        processing_approved=True,
        redistribution_rights="unknown",
        media_type="text/plain",
        size=len(data),
        sha256=hashlib.sha256(data).hexdigest(),
    )
    manifest = tmp_path / "manifest"
    store = tmp_path / "store"
    args = ("import", "--root", root, "--store", store, "--manifest", manifest)
    for broken in (
        dict(source, processing_approved=False),
        {k: v for k, v in source.items() if k != "access_labels"},
        dict(source, relative_path="../private-canary"),
    ):
        manifest.write_text(json.dumps(dict(schema_version=1, sources=[source, broken])))
        result = run(*args)
        assert result.returncode != 0 and "private-canary" not in result.stderr
        assert not store.exists()
    assert run("--help").returncode == 0
    bad = run("--private-canary")
    assert bad.returncode != 0 and "private-canary" not in bad.stderr
    os.mkfifo(tmp_path / "fifo")
    result = run("import", "--root", root, "--store", store, "--manifest", tmp_path / "fifo")
    assert result.returncode != 0 and not store.exists()


def test_source_symlink_and_corrupt_store_safe(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    (root / "file").write_bytes(b"x")
    (root / "link").symlink_to("file")
    source = dict(
        logical_id="doc",
        relative_path="link",
        display_uri="urn:x",
        corpus="c",
        access_labels=[],
        processing_approved=True,
        redistribution_rights="unknown",
        media_type="text/plain",
        size=1,
        sha256=hashlib.sha256(b"x").hexdigest(),
    )
    manifest = tmp_path / "manifest"
    manifest.write_text(json.dumps(dict(schema_version=1, sources=[source])))
    store = tmp_path / "store"
    args = ("import", "--root", root, "--store", store, "--manifest", manifest)
    result = run(*args)
    assert result.returncode != 0 and json.loads(result.stderr)["completed_revisions"] == []
    source["relative_path"] = "file"
    manifest.write_text(json.dumps(dict(schema_version=1, sources=[source])))
    revision = json.loads(run(*args).stdout)["revisions"][0]
    (store / "blobs" / source["sha256"]).write_bytes(b"y")
    result = run("inspect", "--store", store, "--revision", revision)
    assert result.returncode != 0 and json.loads(result.stderr)["stage"] == "inspect"
    assert "file" not in result.stderr and str(tmp_path) not in result.stderr


def test_help_and_import_no_network_or_model_import(tmp_path):
    code = """
import builtins, runpy, socket, sys
original = builtins.__import__
def guard(name, *args, **kwargs):
    if name.split('.')[0] in {'torch', 'transformers', 'sentence_transformers'}:
        raise AssertionError('model import')
    return original(name, *args, **kwargs)
builtins.__import__ = guard
def forbidden(*args, **kwargs):
    raise AssertionError('network access')
socket.socket = forbidden
sys.argv = ['source_cli'] + sys.argv[1:]
runpy.run_module('slaif_raggedized_helper.source_cli', run_name='__main__')
"""
    result = subprocess.run(
        [sys.executable, "-c", code, "--help"], capture_output=True, text=True, timeout=5
    )
    assert result.returncode == 0, result.stderr
    assert "Import or inspect" in result.stdout
    root = tmp_path / "root"
    root.mkdir()
    (root / "file").write_bytes(b"x")
    source = dict(
        logical_id="x",
        relative_path="file",
        display_uri="urn:x",
        corpus="c",
        access_labels=[],
        processing_approved=True,
        redistribution_rights="unknown",
        media_type="text/plain",
        size=1,
        sha256=hashlib.sha256(b"x").hexdigest(),
    )
    manifest = tmp_path / "manifest"
    manifest.write_text(json.dumps(dict(schema_version=1, sources=[source])))
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            code,
            "import",
            "--root",
            str(root),
            "--store",
            str(tmp_path / "store"),
            "--manifest",
            str(manifest),
        ],
        capture_output=True,
        text=True,
        timeout=5,
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["status"] == "complete"
