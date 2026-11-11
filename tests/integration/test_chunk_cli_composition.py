import hashlib
import json
import subprocess
from dataclasses import asdict
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'unit'))
from test_native_tokenizers import make_native  # noqa: E402
from slaif_raggedized_helper import chunking, derived_store, ingestion_store  # noqa: E402
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
    derived = derived_store.Store(tmp_path / 'derived')
    try:
        assert store.read_original(revision.revision_id) == data
        loaded = ingestion_store.load(store, derived, value['bundle_id'])
        assert loaded.revision.revision_id == revision.revision_id
        assert len(loaded.receipts) == 3 * len(loaded.chunks) > 0
        assert len(loaded.neighbors) == len(loaded.chunks)
    finally:
        derived.close()
        store.close()
    failed = subprocess.run(command + ['--query', 'PRIVATE-CANARY-' + 'x' * 10001],
                            capture_output=True, text=True, timeout=60)
    assert failed.returncode == 2
    assert 'PRIVATE-CANARY' not in failed.stdout + failed.stderr
    reserved = subprocess.run(command + ['--query', 'hello ' * 100], capture_output=True,
                              text=True, timeout=60)
    assert reserved.returncode == 1
    assert 'hello hello' not in reserved.stdout + reserved.stderr
    assert 'Owned Ž' not in first.stdout + first.stderr + inspected.stdout + inspected.stderr
    (root / 'empty').write_bytes(b'')
    empty_source = dict(source, logical_id='empty', relative_path='empty', size=0,
                        sha256=hashlib.sha256(b'').hexdigest())
    entry = parse_manifest(json.dumps(dict(schema_version=1, sources=[empty_source])).encode())
    store = OriginalStore(original)
    empty_revision = store.admit(root, entry.sources[0])
    store.close()
    empty_command = ['raggedized', 'chunk', *common, '--revision', empty_revision.revision_id,
                     '--adapter', 'structured_text', '--profile', str(path)]
    empty = subprocess.run(empty_command, capture_output=True, text=True, timeout=60)
    assert empty.returncode == 1
    empty_result = json.loads(empty.stdout)
    assert empty_result['status'] == 'no_native_chunks'
    assert empty_result['source_status'] == 'complete_text'
    assert 'bundle_id' not in empty_result


def test_installed_pdf_roundtrip_and_visual_refusal(tmp_path):
    import os
    from test_pdf_extraction_composition import nested_form_pdf, tiny_pdf, visual_pdf
    paths, runtime, make = make_native(tmp_path)
    pdf_root = os.environ['PDF_TEST_RUNTIME']
    pdf_packages = os.environ['PDF_TEST_PACKAGES']
    assert Path(pdf_root, 'bin/python3.12').is_file()
    assert Path(pdf_packages, 'pdfminer/__init__.py').is_file()
    def record(path):
        d = make(path)
        return dict(artifact=str(path), sha256=d.sha256, backend_version=d.backend_version,
                    model_revision=d.model_revision, preprocessing=d.preprocessing)
    profile = dict(schema_version=1, native_runtime=dict(root=str(runtime.root),
                   packages=str(runtime.packages), python=runtime.python), bge=record(paths[0]),
                   reranker=record(paths[1]), pdf_runtime=dict(runtime_dir=pdf_root,
                   packages_dir=pdf_packages),
                   chunk_policy=asdict(chunking.Policy(pair_max=1280, deadline_ms=15000)))
    path = tmp_path / 'profile.json'
    path.write_text(json.dumps(profile))
    root = tmp_path / 'root'
    root.mkdir()
    original = tmp_path / 'original'
    derived = tmp_path / 'derived'
    derived.mkdir(mode=0o700)
    cases = [('native', tiny_pdf(2)), ('nested', nested_form_pdf()),
             ('raster', visual_pdf('raster')), ('vector', visual_pdf('vector')),
             ('visual', visual_pdf('raster', text=False))]
    for name, data in cases:
        (root / name).write_bytes(data)
        source = dict(logical_id=name, relative_path=name, display_uri='urn:owned',
                      corpus='private', access_labels=[], processing_approved=True,
                      redistribution_rights='allowed', media_type='application/pdf',
                      size=len(data), sha256=hashlib.sha256(data).hexdigest(), version='1')
        entry = parse_manifest(json.dumps(dict(schema_version=1, sources=[source])).encode())
        store = OriginalStore(original)
        revision = store.admit(root, entry.sources[0])
        store.close()
        common = ['--original-store', str(original), '--derived-store', str(derived)]
        command = ['raggedized', 'chunk', *common, '--revision', revision.revision_id,
                   '--adapter', 'pdf_extraction', '--profile', str(path)]
        result = subprocess.run(command, capture_output=True, text=True, timeout=60)
        value = json.loads(result.stdout)
        if name == 'visual':
            assert result.returncode == 1
            assert value['status'] == 'no_native_chunks'
            assert value['source_status'] == 'partial_visual_needed'
            assert 'bundle_id' not in value
        else:
            assert result.returncode == 0, result.stdout
            expected = 'partial_visual_needed' if name in ('raster', 'vector') else 'native_text'
            assert value['status'] == expected
            inspected = subprocess.run(['raggedized', 'chunk', 'inspect', *common, '--bundle',
                                       value['bundle_id']], capture_output=True, text=True,
                                      timeout=60, check=True)
            assert json.loads(inspected.stdout) == value
        store = OriginalStore(original)
        assert store.read_original(revision.revision_id) == data
        store.close()
