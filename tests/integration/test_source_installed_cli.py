"""Installed `raggedized source` route: thin delegation to the source CLI.

Runs the INSTALLED console script on owned disposable fixtures; synthetic and
offline. Proves the installed application import/inspect/reuse/revision
behavior through the canonical `raggedized source` prefix and its safe
refusals, plus zero model/network work on help and import.
"""

import hashlib
import json
import os
import shutil
import subprocess

DATA = "Živjo skupno 😀\n".encode("utf-8")


def invoke(*args, env_extra=None):
    executable = shutil.which("raggedized")
    assert executable is not None
    env = os.environ.copy()
    if env_extra:
        env.update(env_extra)
    return subprocess.run([executable, "source", *map(str, args)],
                          capture_output=True, text=True, timeout=15, env=env)


def entry(**updates):
    result = dict(
        logical_id="doc",
        relative_path="file",
        display_uri="urn:test",
        corpus="c",
        access_labels=[],
        processing_approved=True,
        redistribution_rights="unknown",
        media_type="text/plain",
        size=len(DATA),
        sha256=hashlib.sha256(DATA).hexdigest(),
    )
    result.update(updates)
    return result


def test_installed_import_inspect_shared_bytes_distinct_rights(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    (root / "a").write_bytes(DATA)
    (root / "b").write_bytes(DATA)
    a = dict(entry(logical_id="a", relative_path="a", corpus="one",
                   access_labels=[], redistribution_rights="allowed"))
    b = dict(entry(logical_id="b", relative_path="b", corpus="two",
                   access_labels=["private"], redistribution_rights="prohibited"))
    manifest = tmp_path / "manifest"
    manifest.write_text(json.dumps(dict(schema_version=1, sources=[a, b])),
                        encoding="utf-8")
    store = tmp_path / "store"
    args = ("import", "--root", root, "--store", store, "--manifest", manifest)
    first = invoke(*args)
    assert first.returncode == 0, first.stderr
    ids = json.loads(first.stdout)["revisions"]
    assert len(set(ids)) == 2
    # Two logical documents share one verified original blob.
    blobs = list((store / "blobs").iterdir())
    assert [path.name for path in blobs] == [hashlib.sha256(DATA).hexdigest()]
    # Identical retry reuses the verified revisions.
    assert json.loads(invoke(*args).stdout)["revisions"] == ids
    # Separate correct document revisions/classifications.
    inspected = json.loads(
        invoke("inspect", "--store", store, "--revision", ids[1]).stdout)
    source = inspected["revision"]["source"]
    assert inspected["revision"]["revision_id"] == ids[1]
    assert (source["corpus"], source["access_labels"],
            source["redistribution_rights"]) == ("two", ["private"], "prohibited")
    # Verified loading through the installed package API returns exact bytes.
    from slaif_raggedized_helper.source_admission import OriginalStore

    store_api = OriginalStore(store)
    try:
        assert store_api.read_original(ids[0]) == DATA
        assert store_api.read_original(ids[1]) == DATA
    finally:
        store_api.close()
    # A relevant metadata correction produces a new immutable revision while
    # the unchanged document and the shared blob are reused.
    a_revised = dict(a, title="popravljen naslov č😀")
    manifest.write_text(json.dumps(dict(schema_version=1, sources=[a_revised, b])),
                        encoding="utf-8")
    revised = json.loads(invoke(*args).stdout)["revisions"]
    assert revised[0] != ids[0] and revised[1] == ids[1]
    assert len(list((store / "blobs").iterdir())) == 1
    revised_meta = json.loads(
        invoke("inspect", "--store", store, "--revision", revised[0]).stdout)
    assert revised_meta["revision"]["source"]["title"] == "popravljen naslov č😀"


def test_installed_preflight_refusals_are_safe(tmp_path):
    root = tmp_path / "private-canary"
    root.mkdir()
    (root / "file").write_bytes(DATA)
    valid = entry()
    manifest = tmp_path / "manifest"
    store = tmp_path / "store"
    args = ("import", "--root", root, "--store", store, "--manifest", manifest)

    def write(*sources):
        manifest.write_text(json.dumps(dict(schema_version=1, sources=list(sources))),
                            encoding="utf-8")

    # Unapproved processing, missing labels and traversal are refused before
    # any store object is published; errors never echo the private root.
    for broken in (dict(valid, processing_approved=False),
                   {k: v for k, v in valid.items() if k != "access_labels"},
                   dict(valid, relative_path="../private-canary")):
        write(valid, broken)
        result = invoke(*args)
        assert result.returncode == 1, result.stderr
        error = json.loads(result.stderr)
        assert error["completed_revisions"] == [] and "stage" in error
        assert "private-canary" not in result.stderr
        assert not store.exists()
    # Argument errors are typed failures, not tracebacks.
    bad = invoke("import", "--root", root)
    assert bad.returncode == 1 and "Traceback" not in bad.stderr
    unknown = invoke("bogus")
    assert unknown.returncode == 1 and "Traceback" not in unknown.stderr
    # The manifest itself must be a regular file: a FIFO is refused.
    os.mkfifo(tmp_path / "fifo")
    result = invoke("import", "--root", root, "--store", store,
                    "--manifest", tmp_path / "fifo")
    assert result.returncode == 1 and not store.exists()


def test_installed_inspect_refusals_after_corruption(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    (root / "file").write_bytes(DATA)
    manifest = tmp_path / "manifest"
    manifest.write_text(json.dumps(dict(schema_version=1, sources=[entry()])),
                        encoding="utf-8")
    store = tmp_path / "store"
    args = ("import", "--root", root, "--store", store, "--manifest", manifest)
    first = invoke(*args)
    assert first.returncode == 0, first.stderr
    revision = json.loads(first.stdout)["revisions"][0]
    # Corrupt the stored blob: inspect must refuse with a safe fixed error.
    (store / "blobs" / hashlib.sha256(DATA).hexdigest()).write_bytes(b"tampered")
    result = invoke("inspect", "--store", store, "--revision", revision)
    assert result.returncode == 1
    error = json.loads(result.stderr)
    assert error["stage"] == "inspect"
    assert "synthetic" not in result.stderr and str(tmp_path) not in result.stderr
    # Unknown revisions and missing stores fail safely too.
    missing = invoke("inspect", "--store", store,
                     "--revision", "sha256:" + "0" * 64)
    assert missing.returncode == 1 and json.loads(missing.stderr)["stage"] == "inspect"


def test_installed_source_route_no_model_or_network(tmp_path):
    guard_dir = tmp_path / "guard"
    guard_dir.mkdir()
    (guard_dir / "sitecustomize.py").write_text(
        "import builtins, socket\n"
        "_import = builtins.__import__\n"
        "def guard(name, *args, **kwargs):\n"
        "    top = name.split('.')[0]\n"
        "    if top in {'torch', 'transformers', 'sentence_transformers'}:\n"
        "        raise AssertionError('model import ' + top)\n"
        "    return _import(name, *args, **kwargs)\n"
        "builtins.__import__ = guard\n"
        "def forbidden(*args, **kwargs):\n"
        "    raise AssertionError('network access')\n"
        "socket.socket = forbidden\n",
        encoding="utf-8")
    env_extra = {"PYTHONPATH": str(guard_dir)}
    help_result = invoke("--help", env_extra=env_extra)
    assert help_result.returncode == 0, help_result.stderr
    assert "Import or inspect" in help_result.stdout
    root = tmp_path / "root"
    root.mkdir()
    (root / "file").write_bytes(DATA)
    manifest = tmp_path / "manifest"
    manifest.write_text(json.dumps(dict(schema_version=1, sources=[entry()])),
                        encoding="utf-8")
    result = invoke("import", "--root", root, "--store", tmp_path / "store",
                    "--manifest", manifest, env_extra=env_extra)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["status"] == "complete"


def test_installed_top_level_help_lists_source_route(tmp_path):
    executable = shutil.which("raggedized")
    assert executable is not None
    result = subprocess.run([executable, "--help"], capture_output=True,
                            text=True, timeout=15)
    assert result.returncode == 0
    assert "source" in result.stdout
    # The route must not swallow other top-level commands.
    version = subprocess.run([executable, "--version"], capture_output=True,
                             text=True, timeout=15)
    assert version.returncode == 0 and version.stdout.startswith("raggedized ")
