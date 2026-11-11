import hashlib
import json
import subprocess
from dataclasses import asdict
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'unit'))
from test_native_tokenizers import make_native  # noqa: E402
from slaif_raggedized_helper import chunking  # noqa: E402
from slaif_raggedized_helper.source_admission import OriginalStore, parse_manifest  # noqa: E402


def test_installed_text_roundtrip(tmp_path):
    paths, runtime, make = make_native(tmp_path)
    root = tmp_path / 'root'
    root.mkdir()
    data = '# Owned Ž😀\r\n\r\nhello world\r\n'.encode()
    (root / 'source').write_bytes(data)
    source = dict(logical_id='owned', relative_path='source', display_uri='urn:owned',
                  corpus='private', access_labels=[], processing_approved=True,
                  redistribution_rights='allowed', media_type='text/markdown',
                  size=len(data), sha256=hashlib.sha256(data).hexdigest(), version='1')
    entry = parse_manifest(json.dumps(dict(schema_version=1, sources=[source])).encode()).sources[0]
    original = tmp_path / 'original'
    store = OriginalStore(original)
    revision = store.admit(root, entry)
    store.close()
    def record(path):
        d = make(path)
        return dict(artifact=str(path), sha256=d.sha256, backend_version=d.backend_version,
                    model_revision=d.model_revision, preprocessing=d.preprocessing)
    profile = dict(schema_version=1, native_runtime=dict(root=str(runtime.root),
                   packages=str(runtime.packages), python=runtime.python), bge=record(paths[0]),
                   reranker=record(paths[1]), pdf_runtime=None,
                   chunk_policy=asdict(chunking.Policy(pair_max=1280, deadline_ms=15000)))
    path = tmp_path / 'profile.json'
    path.write_text(json.dumps(profile))
    (tmp_path / 'derived').mkdir(mode=0o700)
    common = ['--original-store', str(original), '--derived-store', str(tmp_path / 'derived')]
    command = ['raggedized', 'chunk', *common, '--revision', revision.revision_id,
               '--adapter', 'structured_text', '--profile', str(path)]
    first = subprocess.run(command, capture_output=True, text=True, timeout=60, check=True)
    value = json.loads(first.stdout)
    again = subprocess.run(command, capture_output=True, text=True, timeout=60, check=True)
    assert json.loads(again.stdout) == value
    inspected = subprocess.run(['raggedized', 'chunk', 'inspect', *common, '--bundle',
                                value['bundle_id']], capture_output=True, text=True,
                               timeout=60, check=True)
    assert json.loads(inspected.stdout) == value
    store = OriginalStore(original)
    try:
        assert store.read_original(revision.revision_id) == data
    finally:
        store.close()
