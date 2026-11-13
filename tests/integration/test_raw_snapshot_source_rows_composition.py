"""Actual source, native fixture construction, private stores and vector binding."""
from dataclasses import asdict
import hashlib
import json

import numpy as np
import pytest

from test_native_tokenizers import make_native
from test_retrieval_representation_composition import make_bundle
from test_structured_text_composition import create_store
from slaif_raggedized_helper import derived_store, embedding_batch_store as bs
from slaif_raggedized_helper import embedding_vectors, ingestion_store
from slaif_raggedized_helper import raw_snapshot_source_rows as sr
from slaif_raggedized_helper import retrieval_representation as rr, schema, vector_codec


def digest(data):
    return hashlib.sha256(data).hexdigest()


def wire(obj):
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()


def mapwire(obj):
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()


@pytest.fixture
def actual(tmp_path):
    paths, runtime, make = make_native(tmp_path)
    defs = (make(paths[0], 'bge_body'), make(paths[0], 'bge_representation'),
            make(paths[1], 'reranker_pair'))
    originals, revisions = create_store(
        tmp_path, '# Heading\n\n' + 'alpha beta gamma delta. ' * 600)
    derived = derived_store.Store(tmp_path / 'store')
    try:
        metadata, members, _, built = make_bundle(originals, revisions[2], defs, runtime)
        bundle_id = ingestion_store.publish(originals, derived, metadata, members)
        bundle = ingestion_store.load(originals, derived, bundle_id)
        chunks = sorted(built.chunks, key=lambda c: c.chunk_id)[:3]
        assert len(chunks) == 3
        reps = rr.build_many(originals, metadata, members, [c.chunk_id for c in chunks],
                             defs[1], runtime)
        scope = bundle.scope.model_dump(mode='json')
        partition = schema.fingerprint(dict(schema=1, corpus=scope['corpus'],
                                            version=scope['version'], labels=scope['labels']))
        scope_hash = schema.fingerprint(dict(kind='embedding-source-scope-v1', scope=scope))[7:]
        policy_hash = schema.fingerprint(dict(kind='embedding-representation-policy-v1',
            policy=asdict(rr.Policy()), batch_policy=asdict(rr.BatchPolicy())))[7:]
        deps = dict(space_id='a'*64, inventory_id='b'*64, definition_fingerprint='c'*64,
                    execution_fingerprint='d'*64, tokenizer_sha256=defs[1].sha256,
                    representation_policy_fingerprint=policy_hash,
                    normalization_policy_id=embedding_vectors.POLICY_ID)
        group_rows = []
        for indexes in ((1, 0), (2,)):
            matrix = np.zeros((len(indexes), 1024), dtype='<f4')
            for pos, index in enumerate(indexes):
                matrix[pos, index] = 1
            enc = vector_codec.encode(matrix, bs.POLICY)
            records = [dict(chunk_id=reps[i].chunk_id, revision_id=reps[i].revision_id,
                            extraction_id=reps[i].extraction_id,
                            representation_id=reps[i].representation_id,
                            rendered_sha256=reps[i].rendered_sha256,
                            source_scope_sha256=scope_hash, input_sha256=reps[i].count.input_sha256,
                            token_count=reps[i].count.count) for i in indexes]
            batch_obj = dict(schema=1, kind='embedding-batch-v1', dependencies=deps, rows=records,
                             vector_container_sha256=enc.container_sha256,
                             vector_payload_sha256=enc.payload_sha256,
                             codec_policy_fingerprint=bs.POLICY.fingerprint())
            batch_metadata = wire(batch_obj)
            batch_id = bs.publish(derived, batch_metadata, enc.container)
            for position, index in enumerate(indexes):
                group_rows.append(dict(records[position], partition_id=partition,
                    bundle_container_id=bundle_id,
                    bundle_metadata_sha256=digest(bundle.metadata_json),
                    batch_container_id=batch_id, batch_metadata_sha256=digest(batch_metadata),
                    batch_row=position, execution_fingerprint=deps['execution_fingerprint']))
        group_rows.sort(key=lambda x: (x['partition_id'], x['chunk_id'], x['representation_id']))
        for i, row in enumerate(group_rows):
            row.update(ordinal=i, partition_row=i)
        mapping = dict(schema=1, kind='slaif-raw-row-map-v1', space_id=deps['space_id'],
                       definition_fingerprint='sha256:'+deps['definition_fingerprint'],
                       representation_policy_fingerprint=policy_hash,
                       chunk_policy_fingerprint=chunks[0].policy_id[7:],
                       normalization_policy_id=deps['normalization_policy_id'], rows=group_rows)
        yield originals, derived, mapping, bundle_id, group_rows[0]['batch_container_id'], reps
    finally:
        derived.close()
        originals.close()


def test_actual_correspondence_and_narrow_causal_control(actual, monkeypatch):
    originals, derived, mapping, bundle_id, batch_id, reps = actual
    group = sr.load_group(originals, derived, mapwire(mapping), bundle_id, batch_id)
    assert len(group.rows) == 2
    assert [r.declaration.chunk_id for r in group.rows] == [r.chunk_id for r in reps[:2]]
    assert group.rows[0].rendered_text == reps[0].text
    assert group.vector_payload == (np.eye(2, 1024, dtype='<f4')).tobytes()
    assert group.payload_sha256 == digest(group.vector_payload)
    rows = mapping['rows']
    rows[0]['batch_row'], rows[1]['batch_row'] = rows[1]['batch_row'], rows[0]['batch_row']
    with pytest.raises(sr.SourceRowsError):
        sr.load_group(originals, derived, mapwire(mapping), bundle_id, batch_id)
    with monkeypatch.context() as patch:
        patch.setattr(sr, '_corresponds', lambda row, actual: True)
        swapped = sr.load_group(originals, derived, mapwire(mapping), bundle_id, batch_id)
        assert swapped.vector_payload == group.vector_payload[4096:] + group.vector_payload[:4096]
    assert ingestion_store.load(originals, derived, bundle_id)
    second = next(r['batch_container_id'] for r in rows if r['batch_container_id'] != batch_id)
    assert len(sr.load_group(originals, derived, mapwire(mapping), bundle_id, second).rows) == 1


def test_mismatched_declarations_refuse(actual):
    originals, derived, mapping, bundle_id, batch_id, _ = actual
    for key in ('rendered_sha256', 'input_sha256', 'representation_id', 'source_scope_sha256',
                'bundle_metadata_sha256', 'batch_metadata_sha256', 'execution_fingerprint'):
        original = mapping['rows'][0][key]
        mapping['rows'][0][key] = 'e' * 64
        with pytest.raises(sr.SourceRowsError):
            sr.load_group(originals, derived, mapwire(mapping), bundle_id, batch_id)
        mapping['rows'][0][key] = original
    for key in ('representation_policy_fingerprint', 'chunk_policy_fingerprint', 'space_id'):
        original = mapping[key]
        mapping[key] = 'e' * 64
        with pytest.raises(sr.SourceRowsError):
            sr.load_group(originals, derived, mapwire(mapping), bundle_id, batch_id)
        mapping[key] = original
    with pytest.raises(sr.SourceRowsError):
        sr.load_group(originals, derived, mapwire(mapping), 'f'*64, batch_id)


def test_fresh_original_is_required(actual):
    originals, derived, mapping, bundle_id, batch_id, _ = actual
    before = sr.load_group(originals, derived, mapwire(mapping), bundle_id, batch_id)
    blob = next((originals.root / 'blobs').iterdir())
    saved = blob.read_bytes()
    try:
        blob.write_bytes(b'corrupted original')
        with pytest.raises(sr.SourceRowsError):
            sr.load_group(originals, derived, mapwire(mapping), bundle_id, batch_id)
    finally:
        blob.write_bytes(saved)
    assert sr.load_group(originals, derived, mapwire(mapping), bundle_id, batch_id) == before


def test_partition_tokens_and_early_refusal(actual, monkeypatch):
    originals, derived, mapping, bundle_id, batch_id, _ = actual
    first = mapping['rows'][0]
    first['token_count'] = 2 if first['token_count'] != 2 else 3
    with pytest.raises(sr.SourceRowsError):
        sr.load_group(originals, derived, mapwire(mapping), bundle_id, batch_id)
    first['token_count'] = actual[-1][0].count.count
    saved = [r['partition_id'] for r in mapping['rows']]
    for row in mapping['rows']:
        row['partition_id'] = 'sha256:' + 'e' * 64
    with pytest.raises(sr.SourceRowsError):
        sr.load_group(originals, derived, mapwire(mapping), bundle_id, batch_id)
    for row, partition in zip(mapping['rows'], saved):
        row['partition_id'] = partition
    calls = []
    def forbidden(*args, **kwargs):
        calls.append(True)
        raise AssertionError('unexpected store access')
    monkeypatch.setattr(derived_store.Store, 'load', forbidden)
    # A missing group and a valid but unsupported policy are rejected before I/O.
    with pytest.raises(sr.SourceRowsError):
        sr.load_group(originals, derived, mapwire(mapping), 'f' * 64, batch_id)
    mapping['representation_policy_fingerprint'] = 'f' * 64
    with pytest.raises(sr.SourceRowsError):
        sr.load_group(originals, derived, mapwire(mapping), bundle_id, batch_id)
    assert not calls


def test_group_does_not_spawn_or_publish(actual, monkeypatch):
    import subprocess
    originals, derived, mapping, bundle_id, batch_id, _ = actual
    def forbidden(*args, **kwargs):
        raise AssertionError('unexpected side effect')
    monkeypatch.setattr(subprocess, 'Popen', forbidden)
    monkeypatch.setattr(derived_store.Store, 'publish', forbidden)
    assert sr.load_group(originals, derived, mapwire(mapping), bundle_id, batch_id).rows


def test_fresh_batch_corruption_refuses(actual):
    originals, derived, mapping, bundle_id, batch_id, _ = actual
    snapshot = derived.load(batch_id)
    manifest = derived_store._parse(snapshot.manifest)
    metadata = manifest['metadata']
    obj = originals.root / 'derived' / 'v1' / 'objects' / metadata['vector_container_sha256']
    saved = obj.read_bytes()
    try:
        obj.write_bytes(b'corrupt')
        with pytest.raises(sr.SourceRowsError):
            sr.load_group(originals, derived, mapwire(mapping), bundle_id, batch_id)
    finally:
        obj.write_bytes(saved)
    assert sr.load_group(originals, derived, mapwire(mapping), bundle_id, batch_id).rows


@pytest.mark.parametrize('field', ['chunk_id', 'revision_id', 'extraction_id',
                                   'representation_id', 'rendered_sha256',
                                   'source_scope_sha256', 'input_sha256', 'token_count'])
def test_actual_batch_field_mismatch(actual, field):
    originals, derived, mapping, bundle_id, batch_id, _ = actual
    snapshot = derived.load(batch_id)
    obj = derived_store._parse(snapshot.manifest)['metadata']
    selected = next(r for r in mapping['rows'] if r['batch_container_id'] == batch_id)
    target = obj['rows'][selected['batch_row']]
    target[field] = 3 if field == 'token_count' and target[field] != 3 else (
        4 if field == 'token_count' else 'e' * 64)
    metadata = wire(obj)
    replacement = bs.publish(derived, metadata, snapshot.members[0].data)
    for row in mapping['rows']:
        if row['batch_container_id'] == batch_id:
            row['batch_container_id'] = replacement
            row['batch_metadata_sha256'] = digest(metadata)
    with pytest.raises(sr.SourceRowsError):
        sr.load_group(originals, derived, mapwire(mapping), bundle_id, replacement)
