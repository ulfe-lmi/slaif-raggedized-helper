"""Fresh actual store and analyzer correspondence for lexical payloads."""
from dataclasses import asdict
import hashlib
import json
import subprocess

import pytest

from test_raw_snapshot_source_rows_composition import digest, mapwire, wire
from test_native_tokenizers import make_native
from test_retrieval_representation_composition import make_bundle
from test_structured_text_composition import create_store
import numpy as np
from slaif_raggedized_helper import embedding_batch_store as bs, embedding_vectors
from slaif_raggedized_helper import retrieval_representation as rr, schema, vector_codec
from slaif_raggedized_helper import derived_store, ingestion_store, raw_snapshot_rows
from slaif_raggedized_helper import raw_snapshot_lexical as lex
from slaif_raggedized_helper import raw_snapshot_source_rows as sr, technical_analyzer as ta


@pytest.fixture
def actual(tmp_path):
    paths, runtime, make = make_native(tmp_path)
    defs = (make(paths[0], 'bge_body'), make(paths[0], 'bge_representation'),
            make(paths[1], 'reranker_pair'))
    originals, revisions = create_store(
        tmp_path, '# Heading Ω HTTP/2\n\n' + 'alpha café 25kg C++ delta. ' * 600)
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



def test_fresh_build_validate_and_narrow_control(actual, monkeypatch):
    originals, derived, mapping, bundle, _, reps = actual
    rowmap = mapwire(mapping)
    partition = mapping['rows'][0]['partition_id']
    with monkeypatch.context() as patch:
        def forbidden(*args, **kwargs):
            raise AssertionError('unexpected side effect')
        patch.setattr(subprocess, 'Popen', forbidden)
        patch.setattr(derived_store.Store, 'publish', forbidden)
        data = lex.build_partition(originals, derived, rowmap, partition)
        result = lex.validate_partition(originals, derived, rowmap, partition, data)
    assert result.sha256 == hashlib.sha256(data).hexdigest()
    assert result.row_map_sha256 == hashlib.sha256(raw_snapshot_rows.subset_bytes(
        raw_snapshot_rows.parse(rowmap), partition)).hexdigest()
    assert len({r['batch_container_id'] for r in mapping['rows']}) == 2
    assert [r.chunk_id for r in result.rows] == [r['chunk_id'] for r in mapping['rows']]
    for row, rep in zip(result.rows, reps):
        assert row.rendered_sha256 == hashlib.sha256(rep.text.encode()).hexdigest()
        assert [asdict(t) for t in row.terms] == [asdict(t) for t in ta.analyze(rep.text).terms]
        assert any(t.text == 'Heading' for t in row.terms)
        assert any(t.text == 'HTTP/2' for t in row.terms)
        assert any(t.text == 'Ω' for t in row.terms)
    for field, value in (('derivation', 'component'), ('end', 100000)):
        altered = json.loads(data)
        altered['rows'][0]['terms'][0][field] = value
        candidate = lex._canonical(altered)
        assert lex.parse(candidate)
        with pytest.raises(lex.LexicalError):
            lex.validate_partition(originals, derived, rowmap, partition, candidate)
    altered = json.loads(data)
    altered['rows'][0]['rendered_sha256'] = 'f' * 64
    candidate = lex._canonical(altered)
    assert lex.parse(candidate)
    with pytest.raises(lex.LexicalError):
        lex.validate_partition(originals, derived, rowmap, partition, candidate)
    obj = json.loads(data)
    obj['rows'][0]['terms'][0]['text'] = 'tampered'
    forged = lex._canonical(obj)
    assert lex.parse(forged)
    with pytest.raises(lex.LexicalError):
        lex.validate_partition(originals, derived, rowmap, partition, forged)
    calls = []
    original_build = lex._build
    def observed(*args):
        calls.append(True)
        return original_build(*args)
    with monkeypatch.context() as patch:
        patch.setattr(lex, '_build', observed)
        patch.setattr(lex, '_same_bytes', lambda left, right: True)
        assert lex.validate_partition(originals, derived, rowmap, partition, forged)
    assert calls == [True]
    assert ingestion_store.load(originals, derived, bundle)


def test_fresh_corruption_refused(actual):
    originals, derived, mapping, _, batch, _ = actual
    rowmap = mapwire(mapping)
    part = mapping['rows'][0]['partition_id']
    data = lex.build_partition(originals, derived, rowmap, part)
    blob = next((originals.root / 'blobs').iterdir())
    snapshot = derived.load(batch)
    vector = originals.root / 'derived' / 'v1' / 'objects' / derived_store._parse(
        snapshot.manifest)['metadata']['vector_container_sha256']
    for path in (blob, vector):
        saved = path.read_bytes()
        try:
            path.write_bytes(b'corrupt')
            with pytest.raises(lex.LexicalError):
                lex.validate_partition(originals, derived, rowmap, part, data)
        finally:
            path.write_bytes(saved)
    assert lex.validate_partition(originals, derived, rowmap, part, data)


def test_group_budget_admission_before_next_actual_load(actual, monkeypatch):
    originals, derived, mapping, _, _, _ = actual
    rowmap = mapwire(mapping)
    partition = mapping['rows'][0]['partition_id']
    groups = list(dict.fromkeys((r['bundle_container_id'], r['batch_container_id'])
                                for r in mapping['rows']))
    loaded = [sr.load_group(originals, derived, rowmap, *group) for group in groups]
    first = sum(len(r.rendered_text) for r in loaded[0].rows)
    total = sum(len(r.rendered_text) for group in loaded for r in group.rows)
    total_bytes = sum(len(r.rendered_text.encode('utf-8')) for group in loaded for r in group.rows)
    real = sr.load_group
    calls = []
    def observed(*args):
        calls.append(args[-2:])
        return real(*args)
    monkeypatch.setattr(sr, 'load_group', observed)
    monkeypatch.setattr(lex, '_MAX_CHARS', total)
    monkeypatch.setattr(lex, '_MAX_RENDERED_BYTES', total_bytes)
    assert lex.build_partition(originals, derived, rowmap, partition)
    assert calls == groups
    calls.clear()
    monkeypatch.setattr(lex, '_MAX_CHARS', first - 1)
    with pytest.raises(lex.LexicalError):
        lex.build_partition(originals, derived, rowmap, partition)
    assert calls == groups[:1]
    calls.clear()
    monkeypatch.setattr(lex, '_MAX_CHARS', total)
    first_bytes = sum(len(r.rendered_text.encode('utf-8')) for r in loaded[0].rows)
    monkeypatch.setattr(lex, '_MAX_RENDERED_BYTES', first_bytes - 1)
    with pytest.raises(lex.LexicalError):
        lex.build_partition(originals, derived, rowmap, partition)
    assert calls == groups[:1]
