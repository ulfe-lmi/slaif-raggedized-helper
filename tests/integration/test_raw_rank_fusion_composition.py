"""Actual versioned original/derived/native snapshot fusion proof."""
from dataclasses import asdict
import hashlib
import json

import numpy as np
import pytest

from slaif_raggedized_helper import derived_store, embedding_batch_store as bs
from slaif_raggedized_helper import embedding_vectors, ingestion_store, provenance_records as p
from slaif_raggedized_helper import raw_rank_fusion as f, raw_snapshot_catalog as c
from slaif_raggedized_helper import retrieval_representation as rr, schema, vector_codec
from slaif_raggedized_helper.source_admission import OriginalStore, parse_manifest
from test_retrieval_representation_composition import make_bundle
from test_native_tokenizers import make_native
from test_raw_snapshot_catalog_composition import materialize, restore_owned_directories  # noqa: F401
from test_raw_snapshot_files_composition import complete
from test_raw_snapshot_rows import enc
from test_raw_snapshot_source_rows_composition import wire


@pytest.fixture
def source(tmp_path, request):
    version = getattr(request, 'param', 'v1')
    paths, runtime, make = make_native(tmp_path)
    defs = (make(paths[0], 'bge_body'), make(paths[0], 'bge_representation'),
            make(paths[1], 'reranker_pair'))
    root = tmp_path / 'input'
    root.mkdir()
    text = ('# Heading\n\n' + 'alpha beta gamma delta. ' * 600).encode()
    (root / 'a').write_bytes(text)
    (root / 'b').write_bytes(text)
    base = dict(logical_id='a', relative_path='a', display_uri='urn:owned', corpus='one',
                version=version, access_labels=[], processing_approved=True,
                redistribution_rights='allowed', media_type='text/markdown', size=len(text),
                sha256=hashlib.sha256(text).hexdigest())
    specs = parse_manifest(json.dumps(dict(schema_version=1, sources=[base,
        dict(base, logical_id='b', relative_path='b', corpus='two', access_labels=['secret'])]
        )).encode()).sources
    originals = OriginalStore(tmp_path / 'store')
    revisions = [originals.admit(root, spec) for spec in specs]
    derived = derived_store.Store(tmp_path / 'store')
    try:
        policy = schema.fingerprint(dict(kind='embedding-representation-policy-v1',
            policy=asdict(rr.Policy()), batch_policy=asdict(rr.BatchPolicy())))[7:]
        deps = dict(space_id='a'*64, inventory_id='b'*64, definition_fingerprint='c'*64,
                    execution_fingerprint='d'*64, tokenizer_sha256=defs[1].sha256,
                    representation_policy_fingerprint=policy,
                    normalization_policy_id=embedding_vectors.POLICY_ID)
        rows, bundles = [], []
        for index, revision in enumerate(revisions):
            metadata, members, _, built = make_bundle(originals, revision, defs, runtime)
            bundle_id = ingestion_store.publish(originals, derived, metadata, members)
            bundle = ingestion_store.load(originals, derived, bundle_id)
            chunks = sorted(built.chunks, key=lambda x: x.chunk_id)[:2 if index == 0 else 1]
            reps = rr.build_many(originals, metadata, members, [x.chunk_id for x in chunks],
                                 defs[1], runtime)
            scope = bundle.scope.model_dump(mode='json')
            partition = schema.fingerprint(dict(schema=1, corpus=scope['corpus'],
                                                version=scope['version'], labels=scope['labels']))
            scope_hash = schema.fingerprint(dict(kind='embedding-source-scope-v1', scope=scope))[7:]
            matrix = np.zeros((len(chunks), 1024), dtype='<f4')
            for pos in range(len(chunks)):
                matrix[pos, index * 2 + pos] = 1
            vector = vector_codec.encode(matrix, bs.POLICY)
            records = [dict(chunk_id=rep.chunk_id, revision_id=rep.revision_id,
                            extraction_id=rep.extraction_id,
                            representation_id=rep.representation_id,
                            rendered_sha256=rep.rendered_sha256, source_scope_sha256=scope_hash,
                            input_sha256=rep.count.input_sha256, token_count=rep.count.count)
                       for rep in reps]
            batch_metadata = wire(dict(schema=1, kind='embedding-batch-v1', dependencies=deps,
                rows=records, vector_container_sha256=vector.container_sha256,
                vector_payload_sha256=vector.payload_sha256,
                codec_policy_fingerprint=bs.POLICY.fingerprint()))
            batch = bs.publish(derived, batch_metadata, vector.container)
            for pos, record in enumerate(records):
                rows.append(dict(record, partition_id=partition, bundle_container_id=bundle_id,
                    bundle_metadata_sha256=hashlib.sha256(bundle.metadata_json).hexdigest(),
                    batch_container_id=batch,
                    batch_metadata_sha256=hashlib.sha256(batch_metadata).hexdigest(),
                    batch_row=pos, execution_fingerprint=deps['execution_fingerprint']))
            bundles.append(bundle_id)
        rows.sort(key=lambda r: (r['partition_id'], r['chunk_id'], r['representation_id']))
        parts = {}
        for ordinal, row in enumerate(rows):
            part = row['partition_id']
            row.update(ordinal=ordinal, partition_row=parts.get(part, 0))
            parts[part] = parts.get(part, 0) + 1
        mapping = dict(schema=1, kind='slaif-raw-row-map-v1', space_id=deps['space_id'],
            definition_fingerprint='sha256:' + deps['definition_fingerprint'],
            representation_policy_fingerprint=policy,
            chunk_policy_fingerprint=chunks[0].policy_id[7:],
            normalization_policy_id=deps['normalization_policy_id'], rows=rows)
        core, payloads = complete(originals, derived, mapping, tuple(bundles))
        store_root, target, ident = materialize(tmp_path, enc(core), payloads)
        catalog = c.load_catalog(originals, derived, str(store_root), ident)
        grants = p.Grants(schema_version=1, corpora=('one', 'two'), versions=('v1',),
                          labels=('secret',))
        yield originals, derived, str(store_root), target, ident, catalog, grants
    finally:
        derived.close()
        originals.close()


def rankings(source, dense=(0, 1), lexical=(1, 2), statuses=('COMPLETE', 'COMPLETE')):
    _, _, _, _, snapshot, catalog, _ = source
    def make(modality, status, indexes):
        entries = []
        for rank, index in enumerate(indexes, 1):
            row = json.loads(catalog.rows[index].declaration_bytes)
            entries.append(f.Entry(row['ordinal'], row['partition_id'], row['chunk_id'],
                                   row['revision_id'], row['representation_id'], rank))
        return f.Ranking(modality, status, snapshot, catalog.catalog_id, 'a'*64, tuple(entries))
    return make('dense', statuses[0], dense), make('lexical', statuses[1], lexical)


def call(source, dense, lexical, **kwargs):
    originals, derived, root, _, snapshot, _, grants = source
    return f.fuse(originals, derived, root, snapshot, 'a'*64, dense=dense, lexical=lexical,
                  grants=kwargs.pop('grants', grants), **kwargs)


def test_tiny_positive(source):
    dense, lexical = rankings(source)
    result = call(source, dense, lexical, k=2)
    assert (result.unique_candidates, result.overlap_candidates, result.returned,
            result.global_cap_applied) == (3, 1, 2, True)
    assert result.hits[0].ordinal == 1
    assert result.hits[0].score == 1 / 62 + 1 / 61
    assert result.hits[0].scope_bytes == source[5].rows[1].scope_bytes
    assert result.hits[0].original_chunk_bytes == source[5].rows[1].chunk_bytes
    assert (result.ranking_origin, result.qualification) == ('SUPPLIED_UNVERIFIED', 'NOT_QUALIFIED')


def test_denial_before_contribution_and_causal_control(source, monkeypatch):
    dense, lexical = rankings(source, (0, 1, 2), ())
    scopes = [json.loads(row.scope_bytes) for row in source[5].rows]
    denied = next(i for i, scope in enumerate(scopes) if scope['corpus'] == 'two')
    # Put the denied row last so a cap of one would otherwise truncate it.
    order = tuple(i for i in range(3) if i != denied) + (denied,)
    dense, lexical = rankings(source, order, ())
    grant = p.Grants(schema_version=1, corpora=('one',), versions=('v1',), labels=())
    calls = []
    contribution = f._contribution
    def observe(rank):
        calls.append(rank)
        return contribution(rank)
    monkeypatch.setattr(f, '_contribution', observe)
    with pytest.raises(f.FusionError):
        call(source, dense, lexical, grants=grant, k=1)
    assert calls == []
    # Override only the pre-contribution predicate for the denied row. The actual later
    # output guard, catalog checks, and arithmetic remain active; select all rows.
    allowed = f._allowed
    count = 0
    def isolate(scope, grants, restrictions):
        nonlocal count
        count += 1
        if count <= 3 and scope.corpus == 'two':
            return True
        return allowed(scope, grants, restrictions)
    monkeypatch.setattr(f, '_allowed', isolate)
    with pytest.raises(f.FusionError):
        call(source, dense, lexical, grants=grant, k=3)
    assert calls == [1, 2, 3]
    assert count > 3
    monkeypatch.setattr(f, '_allowed', allowed)
    calls.clear()
    with pytest.raises(f.FusionError):
        call(source, dense, lexical, grants=grant, k=1)
    assert calls == []


def test_status_and_final_source(source, monkeypatch):
    from slaif_raggedized_helper import raw_snapshot_directory as directory
    dense, lexical = rankings(source, (), ())
    assert call(source, dense, lexical).hits == ()
    dense, lexical = rankings(source, (0,), (), ('COMPLETE', 'UNAVAILABLE'))
    result = call(source, dense, lexical)
    assert result.degraded
    assert (result.dense_status, result.lexical_status) == ('COMPLETE', 'UNAVAILABLE')
    both = rankings(source, (), (), ('UNAVAILABLE', 'UNAVAILABLE'))
    with pytest.raises(f.FusionError):
        call(source, *both)
    loader = directory.load_directory
    blob = next((source[0].root / 'blobs').iterdir())
    saved = blob.read_bytes()
    count = 0
    def corrupt(*args):
        nonlocal count
        count += 1
        if count == 3:
            blob.write_bytes(b'corrupt')
        return loader(*args)
    monkeypatch.setattr(directory, 'load_directory', corrupt)
    try:
        with pytest.raises(f.FusionError):
            call(source, dense, lexical)
        assert count == 3
    finally:
        blob.write_bytes(saved)


def test_source_query_and_interrupt(source, monkeypatch):
    from dataclasses import replace
    dense, lexical = rankings(source)
    with pytest.raises(f.FusionError):
        call(source, replace(dense, query_id='b'*64), lexical)
    with pytest.raises(f.FusionError):
        call(source, replace(dense, catalog_id='sha256:'+'f'*64), lexical)
    with pytest.raises(f.FusionError):
        wrong = replace(dense.entries[0], chunk_id='sha256:'+'f'*64)
        call(source, replace(dense, entries=(wrong,)), lexical)
    marker = KeyboardInterrupt()
    def interrupt(*args, **kwargs):
        raise marker
    monkeypatch.setattr(c, 'load_catalog', interrupt)
    with pytest.raises(KeyboardInterrupt) as caught:
        call(source, dense, lexical)
    assert caught.value is marker


def test_ties_empty_and_static_denial(source):
    dense, lexical = rankings(source, (0, 1), (1, 0))
    result = call(source, dense, lexical)
    assert [hit.chunk_id for hit in result.hits] == sorted(hit.chunk_id for hit in result.hits)
    assert all(hit.score == 1 / 61 + 1 / 62 for hit in result.hits)
    assert (result.dense_input_rows, result.lexical_input_rows,
            result.overlap_candidates) == (2, 2, 2)
    with pytest.raises(f.FusionError):
        call(source, dense, lexical, grants=None)
    empty = rankings(source, (), ())
    with pytest.raises(f.FusionError):
        call(source, *empty, grants=None)


def test_elapsed_cooperative_deadline(source, monkeypatch):
    dense, lexical = rankings(source, (0,), ())
    loader = c.load_catalog
    clock = [f.time.monotonic()]
    def delayed(*args, **kwargs):
        result = loader(*args, **kwargs)
        clock[0] += 2
        return result
    monkeypatch.setattr(f.time, 'monotonic', lambda: clock[0])
    monkeypatch.setattr(c, 'load_catalog', delayed)
    with pytest.raises(f.FusionError):
        call(source, dense, lexical, deadline_ms=1000)


@pytest.mark.parametrize('source', [None], indirect=True)
def test_unknown_version_denied_before_contribution(source, monkeypatch):
    dense, lexical = rankings(source, (0,), ())
    calls = []
    monkeypatch.setattr(f, '_contribution', lambda rank: calls.append(rank))
    with pytest.raises(f.FusionError):
        call(source, dense, lexical)
    assert calls == []


@pytest.mark.parametrize('field', ['status', 'rank'])
def test_actual_source_then_caller_mutation(source, monkeypatch, field):
    dense, lexical = rankings(source, (0,), ())
    original = call(source, dense, lexical)
    actual_loader = c.load_catalog
    capture = f._capture_ranking
    target = dense if field == 'status' else dense.entries[0]
    attr, mutated = ('declared_status', 'UNAVAILABLE') if field == 'status' else ('rank', 7)
    saved = getattr(target, attr)

    def run(capture_function):
        calls = []
        def actual_then_mutate(*args, **kwargs):
            catalog = actual_loader(*args, **kwargs)
            calls.append(catalog.catalog_id)
            if len(calls) == 1:
                object.__setattr__(target, attr, mutated)
            return catalog
        try:
            with monkeypatch.context() as patch:
                patch.setattr(c, 'load_catalog', actual_then_mutate)
                patch.setattr(f, '_capture_ranking', capture_function)
                result = call(source, dense, lexical)
            assert len(calls) == 2
            return result
        finally:
            object.__setattr__(target, attr, saved)

    assert run(capture) == original
    control = run(lambda ranking: ranking)
    if field == 'status':
        assert control.dense_status == 'UNAVAILABLE'
        assert control.dense_input_rows == 1 and control.hits[0].dense_rank == 1
    else:
        assert control.hits[0].dense_rank == 7
        assert control.hits[0].score == 1 / 67
    assert call(source, dense, lexical) == original
