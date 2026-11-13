"""Catalog over real owned snapshot, original and derived stores."""
from dataclasses import FrozenInstanceError
import hashlib
import json

import numpy as np
import pytest

from slaif_raggedized_helper import raw_snapshot_catalog as catalog
from slaif_raggedized_helper import raw_snapshot_directory as directory
from test_raw_snapshot_directory_composition import materialize, restore_owned_directories  # noqa: F401
from test_raw_snapshot_files_composition import complete
from test_raw_snapshot_rows import enc
from test_raw_snapshot_source_rows_composition import actual  # noqa: F401


def prepare(fixture, tmp_path, empty=False):
    originals, derived, mapping, bundle, _, reps = fixture
    if empty:
        mapping['rows'] = []
    core, payloads = complete(originals, derived, mapping, (bundle,))
    root, target, ident = materialize(tmp_path, enc(core), payloads)
    return originals, derived, mapping, reps, root, target, ident


def test_permuted_vectors_and_originals(actual, tmp_path, monkeypatch):  # noqa: F811
    retained = []
    original_retain = catalog._Budget.retain
    def observe(self, data):
        retained.append(data)
        return original_retain(self, data)
    monkeypatch.setattr(catalog._Budget, 'retain', observe)
    originals, derived, mapping, reps, root, _, ident = prepare(actual, tmp_path)
    result = catalog.load_catalog(originals, derived, str(root), ident)
    assert len(result.rows) == 3 and len(result.revisions) == 1
    assert mapping['rows'][0]['batch_row'] == 1
    for i, row in enumerate(result.rows):
        assert row.vector_bytes == np.eye(3, 1024, dtype='<f4')[i].tobytes()
        assert row.rendered_bytes == reps[i].text.encode()
        assert json.loads(row.chunk_bytes)['chunk_id'] == mapping['rows'][i]['chunk_id']
        assert row.representation_id == mapping['rows'][i]['representation_id']
        text = row.rendered_bytes.decode()
        offset = text.index('Heading')
        assert ('Heading', offset, offset + 7, 'literal') in row.terms
        assert ('heading', offset, offset + 7, 'nfkc-casefold') in row.terms
    assert result == catalog.load_catalog(originals, derived, str(root), ident)
    with pytest.raises(FrozenInstanceError):
        result.catalog_id = 'x'
    def digest(b):
        return hashlib.sha256(b).hexdigest()
    identity = dict(version=1, snapshot_id=ident, core=digest(result.core_bytes),
        row_map=digest(result.row_map_bytes), revisions=[digest(x) for x in result.revisions],
        dependencies=[digest(x) for x in result.dependencies],
        blocks=[digest(x) for x in result.blocks],
        rows=[[digest(r.declaration_bytes), digest(r.chunk_bytes), digest(r.source_bytes),
               digest(r.scope_bytes), digest(r.rendered_bytes), r.representation_id,
               digest(r.vector_bytes), r.terms] for r in result.rows])
    encoded = json.dumps(identity, sort_keys=True, ensure_ascii=False, separators=(',', ':'),
                         allow_nan=False).encode('utf-8')
    assert result.catalog_id == 'sha256:' + digest(encoded)
    assert result.catalog_id.encode() in retained


def test_empty(actual, tmp_path, monkeypatch):  # noqa: F811
    originals, derived, _, _, root, _, ident = prepare(actual, tmp_path, True)
    original_registry = catalog.provenance_records.Registry
    def checked(*args):
        assert args[0]
        return original_registry(*args)
    monkeypatch.setattr(catalog.provenance_records, 'Registry', checked)
    result = catalog.load_catalog(originals, derived, str(root), ident)
    assert result.rows == result.revisions == result.dependencies == result.blocks == ()
    with pytest.raises(catalog.CatalogError):
        catalog.load_catalog(originals, derived, str(root), 'sha256:' + '0' * 64)


def test_original_changed_at_return(actual, tmp_path, monkeypatch):  # noqa: F811
    originals, derived, _, _, root, _, ident = prepare(actual, tmp_path)
    actual_loader = directory.load_directory
    blob = next((originals.root / 'blobs').iterdir())
    saved = blob.read_bytes()
    calls = 0
    def change(*args):
        nonlocal calls
        calls += 1
        if calls == 2:
            blob.write_bytes(b'corrupt')
        return actual_loader(*args)
    monkeypatch.setattr(directory, 'load_directory', change)
    try:
        with pytest.raises(catalog.CatalogError):
            catalog.load_catalog(originals, derived, str(root), ident)
        assert calls == 2
    finally:
        blob.write_bytes(saved)
    assert hashlib.sha256(blob.read_bytes()).digest() == hashlib.sha256(saved).digest()


def test_guard_control(actual):  # noqa: F811
    from unittest.mock import patch
    from slaif_raggedized_helper import raw_snapshot_source_rows as source_rows
    from test_raw_snapshot_source_rows_composition import mapwire

    originals, derived, mapping, bundle, batch, _ = actual
    original = source_rows.load_group(originals, derived, mapwire(mapping), bundle, batch)
    selected = [r for r in mapping['rows'] if r['batch_container_id'] == batch]
    selected[0]['batch_row'], selected[1]['batch_row'] = (
        selected[1]['batch_row'], selected[0]['batch_row'])
    with pytest.raises(source_rows.SourceRowsError):
        source_rows.load_group(originals, derived, mapwire(mapping), bundle, batch)
    with patch.object(source_rows, '_corresponds', return_value=True):
        wrong = source_rows.load_group(originals, derived, mapwire(mapping), bundle, batch)
        assert wrong.vector_payload == (
            original.vector_payload[4096:] + original.vector_payload[:4096])
    selected[0]['batch_row'], selected[1]['batch_row'] = (
        selected[1]['batch_row'], selected[0]['batch_row'])
    assert source_rows.load_group(originals, derived, mapwire(mapping), bundle, batch) == original


def test_corruption_namespace_and_interrupt(actual, tmp_path, monkeypatch):  # noqa: F811
    originals, derived, _, _, root, target, ident = prepare(actual, tmp_path)
    assert catalog.load_catalog(originals, derived, str(root), ident).rows
    file = target / 'map'
    saved = file.read_bytes()
    file.chmod(0o600)
    file.write_bytes(b'corrupt')
    file.chmod(0o400)
    with pytest.raises(catalog.CatalogError):
        catalog.load_catalog(originals, derived, str(root), ident)
    file.chmod(0o600)
    file.write_bytes(saved)
    file.chmod(0o400)
    target.chmod(0o700)
    (target / 'extra').write_bytes(b'x')
    (target / 'extra').chmod(0o400)
    target.chmod(0o500)
    with pytest.raises(catalog.CatalogError):
        catalog.load_catalog(originals, derived, str(root), ident)
    target.chmod(0o700)
    (target / 'extra').unlink()
    target.chmod(0o500)
    assert catalog.load_catalog(originals, derived, str(root), ident).rows
    marker = KeyboardInterrupt()
    def interrupt(*args):
        raise marker
    monkeypatch.setattr(directory, 'load_directory', interrupt)
    with pytest.raises(KeyboardInterrupt) as caught:
        catalog.load_catalog(originals, derived, str(root), ident)
    assert caught.value is marker


def test_deadline_after_actual_loader(actual, tmp_path, monkeypatch):  # noqa: F811
    originals, derived, _, _, root, _, ident = prepare(actual, tmp_path)
    loader = directory.load_directory
    original_clock = catalog.time.monotonic
    clock = [original_clock()]
    def delayed(*args):
        result = loader(*args)
        clock[0] += 2
        return result
    monkeypatch.setattr(catalog.time, 'monotonic', lambda: clock[0])
    monkeypatch.setattr(directory, 'load_directory', delayed)
    with pytest.raises(catalog.CatalogError):
        catalog.load_catalog(originals, derived, str(root), ident, deadline_ms=1000)


def test_two_sources_two_scopes(tmp_path):
    from dataclasses import asdict
    from slaif_raggedized_helper import derived_store, embedding_batch_store as bs
    from slaif_raggedized_helper import embedding_vectors, ingestion_store
    from slaif_raggedized_helper import retrieval_representation as rr, schema, vector_codec
    from test_native_tokenizers import make_native
    from test_retrieval_representation_composition import make_bundle
    from test_structured_text_composition import create_store
    from test_raw_snapshot_source_rows_composition import wire

    paths, runtime, make = make_native(tmp_path)
    defs = (make(paths[0], 'bge_body'), make(paths[0], 'bge_representation'),
            make(paths[1], 'reranker_pair'))
    originals, revisions = create_store(tmp_path, '# Heading\n\nalpha beta gamma. ' * 20)
    derived = derived_store.Store(tmp_path / 'store')
    try:
        policy_hash = schema.fingerprint(dict(kind='embedding-representation-policy-v1',
            policy=asdict(rr.Policy()), batch_policy=asdict(rr.BatchPolicy())))[7:]
        deps = dict(space_id='a' * 64, inventory_id='b' * 64, definition_fingerprint='c' * 64,
                    execution_fingerprint='d' * 64, tokenizer_sha256=defs[1].sha256,
                    representation_policy_fingerprint=policy_hash,
                    normalization_policy_id=embedding_vectors.POLICY_ID)
        rows, bundles, expected = [], [], {}
        chunk_policy = None
        for i, revision in enumerate(revisions[:2]):
            metadata, members, _, built = make_bundle(originals, revision, defs, runtime)
            bundle_id = ingestion_store.publish(originals, derived, metadata, members)
            bundle = ingestion_store.load(originals, derived, bundle_id)
            chunk = built.chunks[0]
            chunk_policy = chunk.policy_id[7:]
            rep = rr.build_many(originals, metadata, members, [chunk.chunk_id], defs[1], runtime)[0]
            scope = bundle.scope.model_dump(mode='json')
            partition = schema.fingerprint(dict(schema=1, corpus=scope['corpus'],
                                                version=scope['version'], labels=scope['labels']))
            scope_hash = schema.fingerprint(dict(kind='embedding-source-scope-v1', scope=scope))[7:]
            matrix = np.zeros((1, 1024), dtype='<f4')
            matrix[0, i] = 1
            vector = vector_codec.encode(matrix, bs.POLICY)
            record = dict(chunk_id=rep.chunk_id, revision_id=rep.revision_id,
                          extraction_id=rep.extraction_id, representation_id=rep.representation_id,
                          rendered_sha256=rep.rendered_sha256, source_scope_sha256=scope_hash,
                          input_sha256=rep.count.input_sha256, token_count=rep.count.count)
            batch_metadata = wire(dict(schema=1, kind='embedding-batch-v1', dependencies=deps,
                rows=[record], vector_container_sha256=vector.container_sha256,
                vector_payload_sha256=vector.payload_sha256,
                codec_policy_fingerprint=bs.POLICY.fingerprint()))
            batch = bs.publish(derived, batch_metadata, vector.container)
            rows.append(dict(record, partition_id=partition, bundle_container_id=bundle_id,
                bundle_metadata_sha256=hashlib.sha256(bundle.metadata_json).hexdigest(),
                batch_container_id=batch,
                batch_metadata_sha256=hashlib.sha256(batch_metadata).hexdigest(),
                batch_row=0, execution_fingerprint=deps['execution_fingerprint']))
            expected[rep.chunk_id] = (scope, rep.text.encode(), matrix.tobytes())
            bundles.append(bundle_id)
        rows.sort(key=lambda r: (r['partition_id'], r['chunk_id'], r['representation_id']))
        for ordinal, row in enumerate(rows):
            row.update(ordinal=ordinal, partition_row=0)
        mapping = dict(schema=1, kind='slaif-raw-row-map-v1', space_id=deps['space_id'],
            definition_fingerprint='sha256:' + deps['definition_fingerprint'],
            representation_policy_fingerprint=policy_hash, chunk_policy_fingerprint=chunk_policy,
            normalization_policy_id=deps['normalization_policy_id'], rows=rows)
        core, payloads = complete(originals, derived, mapping, tuple(bundles))
        root, _, ident = materialize(tmp_path, enc(core), payloads)
        result = catalog.load_catalog(originals, derived, str(root), ident)
        assert len(result.revisions) == len(result.dependencies) == len(result.rows) == 2
        assert len({json.loads(row.scope_bytes)['corpus'] for row in result.rows}) == 2
        for row in result.rows:
            scope, rendered, vector = expected[json.loads(row.chunk_bytes)['chunk_id']]
            assert json.loads(row.scope_bytes) == scope
            assert row.rendered_bytes == rendered and row.vector_bytes == vector
    finally:
        derived.close()
        originals.close()


@pytest.mark.parametrize('role', ['dense', 'lexical_terms'])
def test_partition_corruption(actual, tmp_path, role):  # noqa: F811
    originals, derived, mapping, bundle, _, _ = actual
    core, payloads = complete(originals, derived, mapping, (bundle,))
    root, target, ident = materialize(tmp_path, enc(core), payloads)
    path = next(d['path'] for d in core['files'] if d['role'] == role)
    file = target / path
    saved = file.read_bytes()
    file.chmod(0o600)
    file.write_bytes(saved[:-1] + bytes([saved[-1] ^ 1]))
    file.chmod(0o400)
    with pytest.raises(catalog.CatalogError):
        catalog.load_catalog(originals, derived, str(root), ident)
    file.chmod(0o600)
    file.write_bytes(saved)
    file.chmod(0o400)
    assert len(catalog.load_catalog(originals, derived, str(root), ident).rows) == 3


def test_scalar_preflight_real_stores(actual, monkeypatch):  # noqa: F811
    originals, derived, _, _, _, _ = actual
    calls = []
    def forbidden(*args):
        calls.append(True)
        raise AssertionError('loader called')
    monkeypatch.setattr(directory, 'load_directory', forbidden)
    for root, ident, deadline in [('/a/../b', 'sha256:' + '0' * 64, 1),
                                  ('/a', '0' * 64, 1),
                                  ('/a', 'sha256:' + '0' * 64, True),
                                  ('/a', 'sha256:' + '0' * 64, 120001)]:
        with pytest.raises(catalog.CatalogError):
            catalog.load_catalog(originals, derived, root, ident, deadline_ms=deadline)
    assert calls == []
