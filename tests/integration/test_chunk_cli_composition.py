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


def test_installed_structural_and_refusals(tmp_path):
    from slaif_raggedized_helper import native_chunking as nc, provenance_records as p
    from slaif_raggedized_helper import structured_text as st, provenance_jsonl as jl
    from slaif_raggedized_helper import ingestion_bundle
    paths, runtime, make = make_native(tmp_path)
    defs = (make(paths[0], 'bge_body'), make(paths[0], 'bge_representation'),
            make(paths[1], 'reranker_pair'))
    def record(d):
        return dict(artifact=str(d.artifact), sha256=d.sha256, backend_version=d.backend_version,
                    model_revision=d.model_revision, preprocessing=d.preprocessing)
    policy = chunking.Policy(pair_max=1280, deadline_ms=15000)
    profile = dict(schema_version=1, native_runtime=dict(root=str(runtime.root),
                   packages=str(runtime.packages), python=runtime.python), bge=record(defs[0]),
                   reranker=record(defs[2]), pdf_runtime=None, chunk_policy=asdict(policy))
    profile_path = tmp_path / 'profile-PRIVATE-CANARY.json'
    profile_path.write_text(json.dumps(profile))
    root = tmp_path / 'root'
    root.mkdir()
    data = ('# Guide PRIVATE-CANARY\n\nWARNING: check units.\n'
            + ''.join(f'{i}. Measure 5 kg.\n' for i in range(1, 81)) + '\n'
            + 'alpha beta gamma delta epsilon. ' * 180 + '\n\n'
            + '| Item | Unit |\n| --- | --- |\n' + '| Mass | kg |\n' * 250
            + '\nTail.\n').encode()
    (root / 'source').write_bytes(data)
    base = dict(logical_id='owned', relative_path='source', display_uri='urn:owned',
                corpus='one', access_labels=[], processing_approved=True,
                redistribution_rights='allowed', media_type='text/markdown', size=len(data),
                sha256=hashlib.sha256(data).hexdigest(), version='1')
    variants = [base, dict(base, corpus='two'), dict(base, access_labels=['secret'],
                redistribution_rights='prohibited'), dict(base, version='2')]
    original = tmp_path / 'original'
    derived_path = tmp_path / 'derived'
    derived_path.mkdir(mode=0o700)
    store = OriginalStore(original)
    revisions = [store.admit(root, parse_manifest(json.dumps(dict(schema_version=1,
                 sources=[v])).encode()).sources[0]) for v in variants]
    store.close()
    common = ['--original-store', str(original), '--derived-store', str(derived_path)]
    def run(args):
        return subprocess.run(['raggedized', 'chunk', *args], capture_output=True, text=True,
                              timeout=60)
    def inspect(ident):
        return run(['inspect', *common, '--bundle', ident])
    ids, chunk_ids, scopes = set(), set(), set()
    for revision in revisions:
        command = [*common, '--revision', revision.revision_id, '--adapter', 'structured_text',
                   '--profile', str(profile_path), '--query', 'hello']
        first = run(command)
        assert first.returncode == 0, first.stdout
        value = json.loads(first.stdout)
        assert json.loads(run(command).stdout) == value
        assert json.loads(inspect(value['bundle_id']).stdout) == value
        ids.add(value['bundle_id'])
        originals = OriginalStore(original)
        try:
            derived = derived_store.Store(derived_path)
            assert originals.read_original(revision.revision_id) == data
            loaded = ingestion_store.load(originals, derived, value['bundle_id'])
            item = st.extract(originals, revision.revision_id)
            registry = p.Registry((revision,), (item.dependency,), item.blocks)
            produced = nc.build(registry, item.blocks, *defs, runtime, 'hello', policy)
            assert loaded.blocks == item.blocks and loaded.coverage == item.coverage
            assert loaded.chunks == produced.chunks and loaded.neighbors == produced.neighbors
            assert loaded.receipts == produced.receipts
            declarations = [dict(role=d.role, artifact_sha256=d.sha256,
                                 backend_version=d.backend_version, model_revision=d.model_revision,
                                 preprocessing=d.preprocessing) for d in defs]
            definition = nc._json(dict(version=1, kind='observed-local-native',
                policy=asdict(policy), definitions=[nc._identity(d) for d in defs],
                query_input_sha256=nc._input_digest('hello', None),
                serialization=nc._SERIALIZATION)).decode()
            metadata = dict(schema_version=1, kind='native-ingestion-bundle',
                revision_id=revision.revision_id, extraction=dict(
                    dependency=item.dependency.model_dump(), adapter='structured_text',
                    status='complete_text', coverage_kind='unicode_codepoints',
                    uncertainty=item.uncertainty), chunking=dict(policy=asdict(policy),
                    query='hello', definitions=declarations, policy_definition=definition,
                    policy_id=p.policy_id(definition)), counts=dict(blocks=len(item.blocks),
                    chunks=len(produced.chunks), neighbors=len(produced.neighbors),
                    receipts=len(produced.receipts)))
            def encode(kind, values):
                return jl.encode(kind, tuple(x.model_dump_json().encode() for x in values))
            members = (('blocks', encode('Block', item.blocks)),
                ('coverage', nc._json(dict(schema_version=1, kind='unicode_codepoints',
                                           spans=[asdict(x) for x in item.coverage]))),
                ('chunks', encode('Chunk', produced.chunks)),
                ('neighbors', encode('Neighbors', produced.neighbors)),
                ('receipts', produced.receipts_json()))
            assert loaded == ingestion_bundle.validate(originals, nc._json(metadata), members)
            assert loaded.scope == item.scope
            scopes.add((item.scope.corpus, item.scope.labels, item.scope.redistribution_rights))
            chunk_ids.add(loaded.chunks[0].chunk_id)
            for i, chunk in enumerate(loaded.chunks):
                assert registry.bind_chunk(chunk) == item.scope
                receipts = loaded.receipts[3*i:3*i+3]
                rep = ''.join(chunk.heading_path) + chunk.text
                assert [r.count.input_sha256 for r in receipts] == [
                    nc._input_digest(chunk.text, None), nc._input_digest(rep, None),
                    nc._input_digest('hello', rep)]
                assert [r.count.count for r in receipts] == [c.count for c in chunk.counts]
            assert registry.bind_neighbors(loaded.chunks, loaded.neighbors) == loaded.neighbors
            for block in item.blocks:
                spans = [(f.start, f.end) for c in loaded.chunks for f in c.fragments
                         if isinstance(f, p.SourceFragment) and f.block_id == block.block_id]
                assert {i for start, end in spans for i in range(start, end)} == set(
                    range(len(block.text)))
            assert any(b.kind == 'list' for b in item.blocks)
            assert any(
                any(a[0] < b[1] and b[0] < a[1] for a, b in zip(spans, spans[1:]))
                for block in item.blocks if block.kind == 'text'
                for spans in [[(f.start, f.end) for c in loaded.chunks for f in c.fragments
                               if isinstance(f, p.SourceFragment) and f.block_id == block.block_id]]
            )
            headers = [b for b in item.blocks if b.kind == 'table_header']
            assert headers and sum(f.block_id == headers[0].block_id for c in loaded.chunks
                                   for f in c.fragments if isinstance(f, p.SourceFragment)) > 1
            assert any(b.text.startswith('Tail') for b in item.blocks)
            if revision == revisions[0]:
                initial_id = value['bundle_id']
                snapshot = derived.load(initial_id)
                meta = json.loads(snapshot.manifest)['metadata']
                meta['revision_id'] = revisions[1].revision_id
                rebound = derived.publish(derived_store._encode(meta), snapshot.members)
                assert derived.load(rebound).members == snapshot.members
        finally:
            derived.close()
            originals.close()
    assert len(ids) == len(chunk_ids) == len({r.revision_id for r in revisions}) == 4
    assert len(scopes) >= 3
    assert inspect(rebound).returncode == 1
    manifest = json.loads((derived_path / 'derived/v1/manifests' / initial_id).read_bytes())
    member = derived_path / 'derived/v1/objects' / manifest['members'][0]['sha256']
    saved = member.read_bytes()
    try:
        member.write_bytes(b'corrupt')
        assert inspect(initial_id).returncode == 1
    finally:
        member.write_bytes(saved)
    blob = original / 'blobs' / hashlib.sha256(data).hexdigest()
    saved = blob.read_bytes()
    try:
        blob.write_bytes(b'corrupt')
        assert inspect(initial_id).returncode == 1
    finally:
        blob.write_bytes(saved)
    assert inspect(initial_id).returncode == 0
    import copy
    for kind in ('hash', 'backend', 'policy', 'profile'):
        bad = copy.deepcopy(profile)
        if kind == 'hash':
            bad['bge']['sha256'] = '0' * 64
        elif kind == 'backend':
            bad['native_runtime']['packages'] = str(tmp_path / 'missing-PRIVATE-CANARY')
        elif kind == 'policy':
            bad['chunk_policy']['target'] = 99999
        else:
            bad['schema_version'] = 99
        profile_path.write_text(json.dumps(bad))
        result = run([*common, '--revision', revisions[0].revision_id, '--adapter',
                      'structured_text', '--profile', str(profile_path), '--query',
                      'PRIVATE-CANARY'])
        assert result.returncode in (1, 2)
        assert 'PRIVATE-CANARY' not in result.stdout + result.stderr
        assert json.loads(result.stdout)['error'] in ('invalid_input', 'ingestion_failed')
