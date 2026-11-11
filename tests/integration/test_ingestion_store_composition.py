import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
import sys
import os
import subprocess
from dataclasses import asdict
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'unit'))
from test_native_tokenizers import make_native  # noqa: E402
from slaif_raggedized_helper import ingestion_bundle as bundle, chunking  # noqa: E402
from slaif_raggedized_helper import native_chunking as nc, provenance_jsonl as jl  # noqa: E402
from slaif_raggedized_helper import provenance_records as p, structured_text as st  # noqa: E402



from slaif_raggedized_helper import ingestion_store as adapter, derived_store  # noqa: E402
from slaif_raggedized_helper.source_admission import OriginalStore, parse_manifest  # noqa: E402


def test_store_real_native_and_fresh_process(tmp_path, monkeypatch):
    paths, runtime, make = make_native(tmp_path)
    defs = (make(paths[0], 'bge_body'), make(paths[0], 'bge_representation'),
            make(paths[1], 'reranker_pair'))
    assert tuple(d.role for d in defs) == ('bge_body', 'bge_representation', 'reranker_pair')
    assert defs[0].sha256 == defs[1].sha256 != defs[2].sha256
    text = ('# Guide Ž😀\r\n\r\nCafe\u0301 and controls \t.\r\n\r\n'
            'WARNING: check units.\r\n1. Measure 5 kg.\r\n\r\n'
            + ('alpha beta gamma delta epsilon. ' * 180) + '\r\n\r\n'
            + '| Item | Unit |\r\n| --- | --- |\r\n'
            + '| Mass | kg |\r\n' * 250 + '\r\nTail.\r\n')
    root = tmp_path / 'root'
    root.mkdir()
    raw = text.encode()
    (root / 'a').write_bytes(raw)
    (root / 'b').write_bytes(raw)
    base = dict(logical_id='a', relative_path='a', display_uri='urn:owned', corpus='one',
                access_labels=[], processing_approved=True, redistribution_rights='allowed',
                media_type='text/markdown', size=len(raw), sha256=hashlib.sha256(raw).hexdigest(),
                version='v1')
    other = dict(base, logical_id='b', relative_path='b', corpus='two',
                 access_labels=['secret'], redistribution_rights='prohibited')
    entries = parse_manifest(json.dumps(dict(schema_version=1, sources=[
        base, other, dict(base, version='v2')])).encode()).sources
    store = OriginalStore(tmp_path / 'store')
    revisions = [store.admit(root, entry) for entry in entries]
    try:
        item = st.extract(store, revisions[0].revision_id)
        registry = p.Registry((revisions[0],), (item.dependency,), item.blocks)
        policy = chunking.Policy(pair_max=1280)
        query = 'hello'
        result = nc.build(registry, item.blocks, *defs, runtime, query, policy)
        declarations = [dict(role=d.role, artifact_sha256=d.sha256,
                             backend_version=d.backend_version, model_revision=d.model_revision,
                             preprocessing=d.preprocessing) for d in defs]
        definition = nc._json(dict(version=1, kind='observed-local-native', policy=asdict(policy),
                                   definitions=[nc._identity(d) for d in defs],
                                   query_input_sha256=nc._input_digest(query, None),
                                   serialization=nc._SERIALIZATION)).decode()
        extraction = dict(dependency=item.dependency.model_dump(), adapter='structured_text',
                          status='complete_text', coverage_kind='unicode_codepoints',
                          uncertainty=item.uncertainty)
        metadata = dict(schema_version=1, kind='native-ingestion-bundle',
                        revision_id=revisions[0].revision_id, extraction=extraction,
                        chunking=dict(policy=asdict(policy), query=query, definitions=declarations,
                                      policy_definition=definition,
                                      policy_id=p.policy_id(definition)),
                        counts=dict(blocks=len(item.blocks), chunks=len(result.chunks),
                                    neighbors=len(result.chunks), receipts=3*len(result.chunks)))
        def encode(kind, values):
            return jl.encode(kind, tuple(x.model_dump_json().encode() for x in values))
        members = (('blocks', encode('Block', item.blocks)),
                   ('coverage', nc._json(dict(schema_version=1, kind='unicode_codepoints',
                                               spans=[asdict(x) for x in item.coverage]))),
                   ('chunks', encode('Chunk', result.chunks)),
                   ('neighbors', encode('Neighbors', result.neighbors)),
                   ('receipts', result.receipts_json()))
        metadata_bytes = nc._json(metadata)
        expected = bundle.validate(store, metadata_bytes, members)
        with derived_store.Store(tmp_path / 'store') as derived:
            ident = adapter.publish(store, derived, metadata_bytes, members)
            assert adapter.publish(store, derived, metadata_bytes, members) == ident
            assert len(ident) == 64 and int(ident, 16) >= 0
            assert adapter.load(store, derived, ident) == expected
            with ThreadPoolExecutor(max_workers=3) as pool:
                simultaneous = list(pool.map(
                    lambda _: adapter.publish(store, derived, metadata_bytes, members), range(3)))
            assert simultaneous == [ident] * 3
            identities = {ident}
            for revision in revisions[1:]:
                extracted = st.extract(store, revision.revision_id)
                reg = p.Registry((revision,), (extracted.dependency,), extracted.blocks)
                built = nc.build(reg, extracted.blocks, *defs, runtime, query, policy)
                revised_meta = dict(metadata, revision_id=revision.revision_id,
                    extraction=dict(dependency=extracted.dependency.model_dump(),
                        adapter='structured_text', status='complete_text',
                        coverage_kind='unicode_codepoints', uncertainty=extracted.uncertainty),
                    counts=dict(blocks=len(extracted.blocks), chunks=len(built.chunks),
                        neighbors=len(built.neighbors), receipts=3*len(built.chunks)))
                revised_members = (('blocks', encode('Block', extracted.blocks)),
                    ('coverage', nc._json(dict(schema_version=1, kind='unicode_codepoints',
                        spans=[asdict(x) for x in extracted.coverage]))),
                    ('chunks', encode('Chunk', built.chunks)),
                    ('neighbors', encode('Neighbors', built.neighbors)),
                    ('receipts', built.receipts_json()))
                revised_id = adapter.publish(
                    store, derived, nc._json(revised_meta), revised_members)
                loaded = adapter.load(store, derived, revised_id)
                assert loaded.revision == revision and loaded.scope == extracted.scope
                identities.add(revised_id)
            assert len(identities) == 3
            # No publication happens when semantic validation rejects the input.
            calls = []
            original_publish = derived_store.Store.publish
            def spy(self, *args):
                calls.append(args)
                return original_publish(self, *args)
            with monkeypatch.context() as patch:
                patch.setattr(derived_store.Store, 'publish', spy)
                for field, value in [('kind', 'opaque'), ('schema_version', 2),
                                     ('revision_id', revisions[1].revision_id)]:
                    bad = dict(metadata, **{field: value})
                    with pytest.raises(adapter.IngestionStoreError):
                        adapter.publish(store, derived, nc._json(bad), members)
                bad_policy = dict(metadata, chunking=dict(metadata['chunking'], policy_id='wrong'))
                with pytest.raises(adapter.IngestionStoreError):
                    adapter.publish(store, derived, nc._json(bad_policy), members)
                for index in range(5):
                    bad = list(members)
                    bad[index] = (bad[index][0], b'{}')
                    with pytest.raises(adapter.IngestionStoreError):
                        adapter.publish(store, derived, metadata_bytes, tuple(bad))
                assert not calls
            other_root = tmp_path / 'other'
            other_root.mkdir(mode=0o700)
            with derived_store.Store(other_root) as other:
                with pytest.raises(adapter.IngestionStoreError):
                    adapter.load(store, other, ident)
            wrong_revision = dict(metadata, revision_id=revisions[1].revision_id)
            cross_id = derived.publish(nc._json(wrong_revision), tuple(
                derived_store.Member(name, data) for name, data in members))
            with pytest.raises(adapter.IngestionStoreError):
                adapter.load(store, derived, cross_id)
            opaque = derived.publish(b'{}', (derived_store.Member('part', b'opaque'),))
            with pytest.raises(adapter.IngestionStoreError):
                adapter.load(store, derived, opaque)
            for bad in ('A' * 64, '../x', '0' * 64):
                with pytest.raises(adapter.IngestionStoreError):
                    adapter.load(store, derived, bad)
            # Simulate expiry after the actual store has committed a new manifest.
            late_root = tmp_path / 'late'
            late_root.mkdir(mode=0o700)
            late_store = derived_store.Store(late_root)
            real_publish = derived_store.Store.publish
            def late(self, *args):
                result = real_publish(self, *args)
                patch.setattr(adapter, '_check', lambda end: (_ for _ in ()).throw(ValueError()))
                return result
            with monkeypatch.context() as patch:
                patch.setattr(derived_store.Store, 'publish', late)
                with pytest.raises(adapter.IngestionStoreError):
                    adapter.publish(store, late_store, metadata_bytes, members)
            assert adapter.load(store, late_store, ident) == expected
            assert adapter.publish(store, late_store, metadata_bytes, members) == ident
            late_store.close()
            # Integrity errors are rejected before semantic validation.
            snap = derived.load(ident)
            manifest_path = tmp_path / 'store' / 'derived' / 'v1' / 'manifests' / ident
            object_path = (tmp_path / 'store' / 'derived' / 'v1' / 'objects' /
                           hashlib.sha256(snap.members[0].data).hexdigest())
            for path in (manifest_path, object_path):
                contents = path.read_bytes()
                path.write_bytes(contents + b'x')
                with monkeypatch.context() as patch:
                    patch.setattr(bundle, 'validate', lambda *args: pytest.fail('semantic trust'))
                    with pytest.raises(adapter.IngestionStoreError):
                        adapter.load(store, derived, ident)
                path.write_bytes(contents)
            # Final load return must also enforce the outer deadline.
            real_validate = bundle.validate
            def late_validate(*args):
                value = real_validate(*args)
                patch.setattr(adapter, '_check', lambda end: (_ for _ in ()).throw(ValueError()))
                return value
            with monkeypatch.context() as patch:
                patch.setattr(bundle, 'validate', late_validate)
                with pytest.raises(adapter.IngestionStoreError):
                    adapter.load(store, derived, ident)
            blob = tmp_path / 'store' / 'blobs' / revisions[0].blob
            original = blob.read_bytes()
            blob.write_bytes(b'changed')
            with pytest.raises(adapter.IngestionStoreError):
                adapter.load(store, derived, ident)
            blob.write_bytes(original)
            assert adapter.load(store, derived, ident) == expected
        store.close()
        sentinel = tmp_path / 'sentinel'
        sentinel.write_bytes(b'unchanged')
        fd = os.open(sentinel, os.O_RDWR)
        try:
            with derived_store.Store(tmp_path / 'store') as ds:
                with pytest.raises(adapter.IngestionStoreError):
                    adapter.load(store, ds, ident)
            assert sentinel.read_bytes() == b'unchanged'
        finally:
            os.close(fd)
        store = None
        fresh = OriginalStore(tmp_path / 'store')
        try:
            with derived_store.Store(tmp_path / 'store') as ds:
                assert adapter.load(fresh, ds, ident) == expected
        finally:
            fresh.close()
        witness = hashlib.sha256(
            expected.metadata_json + b"".join(x[1] for x in expected.members)).hexdigest()
        code = ("from slaif_raggedized_helper.source_admission import OriginalStore; "
                "from slaif_raggedized_helper.derived_store import Store; "
                "from slaif_raggedized_helper.ingestion_store import load; "
                f"a=OriginalStore({str(tmp_path / 'store')!r}); "
                f"b=Store({str(tmp_path / 'store')!r}); v=load(a,b,{ident!r}); "
                "import hashlib; "
                "digest=hashlib.sha256(v.metadata_json + b''.join(x[1] for x in v.members)); "
                f"assert digest.hexdigest() == {witness!r}; "
                "a.close(); b.close()")
        subprocess.run([sys.executable, '-c', code], check=True, env=os.environ.copy(), timeout=30)
        assert (tmp_path / 'root' / 'a').read_bytes() == text.encode()
    finally:
        if store is not None:
            store.close()
