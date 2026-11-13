"""Owned tiny source-backed hybrid composition proof."""
import hashlib
import json

import numpy as np
import pytest

from slaif_raggedized_helper import provenance_records as p
from slaif_raggedized_helper import raw_hybrid_search as hybrid
from slaif_raggedized_helper import raw_snapshot_catalog as catalog
from test_raw_snapshot_directory_composition import materialize, restore_owned_directories  # noqa: F401
from test_raw_snapshot_files_composition import complete
from test_raw_snapshot_rows import enc

def close_owned_stores(derived, originals, failure=None):
    """Attempt both closes; preserve a body failure and expose cleanup failures."""
    first = None
    failed = False
    for store in (derived, originals):
        if store is None:
            continue
        try:
            store.close()
        except BaseException as exc:
            failed = True
            if first is None:
                first = exc
    if failed:
        target = failure if failure is not None else first
        try:
            BaseException.add_note(target, "Store close failed; cleanup may be incomplete.")
        except BaseException:
            pass
        if failure is None:
            raise first



def make_sources(tmp_path, *, version='v1', empty=False, three=True, paired=False):
    from dataclasses import asdict
    from slaif_raggedized_helper import derived_store, embedding_batch_store as bs
    from slaif_raggedized_helper import embedding_vectors, ingestion_store
    from slaif_raggedized_helper import retrieval_representation as rr, schema, vector_codec
    from test_native_tokenizers import make_native
    from test_retrieval_representation_composition import make_bundle
    from slaif_raggedized_helper.source_admission import OriginalStore, parse_manifest
    from test_raw_snapshot_source_rows_composition import wire

    paths, runtime, make = make_native(tmp_path)
    defs = (make(paths[0], 'bge_body'), make(paths[0], 'bge_representation'),
            make(paths[1], 'reranker_pair'))
    source_root = tmp_path / 'source'
    source_root.mkdir()
    raw = ('# Heading\n\nalpha beta gamma. ' * 20).encode()
    (source_root / 'a').write_bytes(raw)
    denied_raw = raw + b'\n\nDeniedOnly DeniedOnly' if paired else raw
    (source_root / 'b').write_bytes(denied_raw)
    if three:
        third_raw = raw + b'\n\nDistinctiveZephyr'
        (source_root / 'c').write_bytes(third_raw)
    base = dict(logical_id='a', relative_path='a', display_uri='urn:owned', corpus='one',
                version=version, title='uniquetitle', access_labels=[], processing_approved=True,
                redistribution_rights='allowed', media_type='text/markdown', size=len(raw),
                sha256=hashlib.sha256(raw).hexdigest())
    second = dict(base, logical_id='b', relative_path='b', corpus='two',
                  access_labels=['secret'])
    if paired:
        second.update(size=len(denied_raw), sha256=hashlib.sha256(denied_raw).hexdigest())
    manifests = [base, second]
    if three:
        manifests.append(dict(base, logical_id='c', relative_path='c', size=len(third_raw),
                              sha256=hashlib.sha256(third_raw).hexdigest()))
    sources = parse_manifest(json.dumps(dict(schema_version=1, sources=manifests)).encode())
    originals = OriginalStore(tmp_path / 'store')
    derived = None
    try:
        revisions = [originals.admit(source_root, source) for source in sources.sources]
        derived = derived_store.Store(tmp_path / 'store')
        policy_hash = schema.fingerprint(dict(kind='embedding-representation-policy-v1',
            policy=asdict(rr.Policy()), batch_policy=asdict(rr.BatchPolicy())))[7:]
        deps = dict(space_id='a' * 64, inventory_id='b' * 64, definition_fingerprint='c' * 64,
                    execution_fingerprint='d' * 64, tokenizer_sha256=defs[1].sha256,
                    representation_policy_fingerprint=policy_hash,
                    normalization_policy_id=embedding_vectors.POLICY_ID)
        rows, bundles, expected = [], [], {}
        chunk_policy = None
        for i, revision in enumerate(revisions):
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
        partition_sizes = {}
        for ordinal, row in enumerate(rows):
            part = row['partition_id']
            row.update(ordinal=ordinal, partition_row=partition_sizes.get(part, 0))
            partition_sizes[part] = partition_sizes.get(part, 0) + 1
        mapping = dict(schema=1, kind='slaif-raw-row-map-v1', space_id=deps['space_id'],
            definition_fingerprint='sha256:' + deps['definition_fingerprint'],
            representation_policy_fingerprint=policy_hash, chunk_policy_fingerprint=chunk_policy,
            normalization_policy_id=deps['normalization_policy_id'], rows=rows)
        if empty:
            mapping['rows'] = []
        core, payloads = complete(originals, derived, mapping, tuple(bundles))
        root, _, ident = materialize(tmp_path, enc(core), payloads)
        if paired:
            permitted = [r for r in rows if expected[r['chunk_id']][0]['corpus'] == 'one']
            assert len(permitted) == 1
            one = dict(permitted[0], ordinal=0, partition_row=0)
            subset = dict(mapping, rows=[one])
            subset_core, subset_payloads = complete(
                originals, derived, subset, (one['bundle_container_id'],))
            subset_dir = tmp_path / 'subset'
            subset_dir.mkdir(mode=0o700)
            subset_root, _, subset_id = materialize(subset_dir, enc(subset_core), subset_payloads)
            return originals, derived, root, ident, subset_root, subset_id
        return originals, derived, root, ident
    except BaseException as failure:
        close_owned_stores(derived, originals, failure)
        raise



def test_positive_actual_journey(tmp_path, monkeypatch):
    import time

    originals, derived, root, ident = make_sources(tmp_path)
    try:
        core = json.loads((root / 'snapshots' / ident[7:] / '.core.json').read_bytes())
        e = core['embedding']
        grants = p.Grants(schema_version=1, corpora=('one', 'two'), versions=('v1',),
                          labels=('secret',))
        vector = np.zeros(1024, dtype='<f4')
        vector[:3] = [0.6, 0, 0.8]
        calls = []
        actual = catalog.load_catalog

        def measured(*args, **kwargs):
            start = time.monotonic()
            try:
                return actual(*args, **kwargs)
            finally:
                calls.append(round(time.monotonic() - start, 6))

        monkeypatch.setattr(catalog, 'load_catalog', measured)
        result = hybrid.search(originals, derived, str(root), ident, 'DistinctiveZephyr',
            vector.tobytes(), query_space_id=e['space_id'],
            query_definition_fingerprint=e['definition_fingerprint'],
            query_policy_id=e['query_policy_fingerprint'],
            query_execution_fingerprint=e['query_execution_fingerprint'], grants=grants,
            dense_k=3, lexical_k=3, partition_cap=3, k=3)
        assert len(calls) == 8
        assert (result.dense.eligible, result.dense.returned) == (3, 3)
        assert (result.lexical.eligible, result.lexical.matching,
                result.lexical.returned) == (3, 1, 1)
        assert (result.fusion.dense_input_rows, result.fusion.lexical_input_rows,
                result.fusion.unique_candidates, result.fusion.overlap_candidates) == (3, 1, 3, 1)
        dense_hits = result.dense.hits
        assert [h.score for h in dense_hits] == pytest.approx([0.8, 0.6, 0.0])
        assert result.lexical.hits[0].chunk_id == dense_hits[0].chunk_id
        assert result.fusion.hits[0].score == pytest.approx(2 / 61)
        assert [h.dense_rank for h in result.fusion.hits] == [1, 2, 3]
        print('catalog_seconds=', calls, 'catalog_calls=', len(calls), flush=True)
    finally:
        derived.close()
        originals.close()


@pytest.fixture
def owned(tmp_path, monkeypatch):
    import time

    observations = []
    def instrument(obj, name):
        actual = getattr(obj, name)
        def wrapped(*a, **kw):
            start = time.monotonic()
            try:
                return actual(*a, **kw)
            finally:
                observations.append((name, round(time.monotonic() - start, 6)))
        monkeypatch.setattr(obj, name, wrapped)
    for obj, name in ((catalog, "load_catalog"), (hybrid.dense, "search"),
                      (hybrid.lexical, "search"), (hybrid.fusion, "fuse")):
        instrument(obj, name)
    originals, derived, root, ident = make_sources(tmp_path)
    try:
        core = json.loads((root / 'snapshots' / ident[7:] / '.core.json').read_bytes())
        e = core['embedding']
        vector = np.zeros(1024, dtype='<f4')
        vector[:3] = [0.6, 0, 0.8]
        grants = p.Grants(schema_version=1, corpora=('one', 'two'), versions=('v1',),
                          labels=('secret',))
        args = dict(originals=originals, derived=derived, store_root=str(root), snapshot_id=ident,
                    text='DistinctiveZephyr', query_payload=vector.tobytes(),
                    query_space_id=e['space_id'],
                    query_definition_fingerprint=e['definition_fingerprint'],
                    query_policy_id=e['query_policy_fingerprint'],
                    query_execution_fingerprint=e['query_execution_fingerprint'], grants=grants,
                    dense_k=3, lexical_k=3, partition_cap=3, k=3)
        yield args, root, ident
    finally:
        print('STAGE_OBSERVATIONS', observations, flush=True)
        derived.close()
        originals.close()


def test_real_authority_mutation_does_not_widen(owned, monkeypatch):
    args, _, _ = owned
    args['grants'].__dict__['corpora'] = ('one',)
    original = hybrid.dense.search
    def mutate_after_dense(*a, **kw):
        result = original(*a, **kw)
        args['grants'].__dict__['corpora'] = ('one', 'two')
        return result
    monkeypatch.setattr(hybrid.dense, 'search', mutate_after_dense)
    result = hybrid.search(**args)
    assert result.dense.eligible == result.lexical.eligible == 2
    assert all(json.loads(h.scope_bytes)['corpus'] == 'one' for h in result.fusion.hits)


def test_real_lexical_query_mismatch_refuses_before_fusion(owned, monkeypatch):
    args, _, _ = owned
    actual = hybrid.lexical.search
    fusion_calls = []
    def other_query(*a, **kw):
        changed = list(a)
        changed[4] = 'Heading'
        result = actual(*changed, **kw)
        assert result.query_text_sha256 == hashlib.sha256(b'Heading').hexdigest()
        assert result.matching == 3
        return result
    monkeypatch.setattr(hybrid.lexical, 'search', other_query)
    monkeypatch.setattr(hybrid.fusion, 'fuse', lambda *a, **kw: fusion_calls.append(1))
    with pytest.raises(hybrid.HybridSearchError):
        hybrid.search(**args)
    assert fusion_calls == []


def test_real_lexical_query_mismatch_guard_is_causal(owned, monkeypatch):
    from pathlib import Path
    import sys
    import types

    args, _, _ = owned
    source = Path(hybrid.__file__).read_text()
    original = 'lr.query_text_sha256, lr.analyzer_fingerprint,'
    changed = 'text_sha, lr.analyzer_fingerprint,'
    assert source.count(original) == 1
    module = types.ModuleType('slaif_raggedized_helper._temporary_hybrid_control')
    module.__package__ = 'slaif_raggedized_helper'
    monkeypatch.setitem(sys.modules, module.__name__, module)
    exec(compile(source.replace(original, changed), '<temporary-hybrid-control>', 'exec'),
         module.__dict__)
    actual_lexical = hybrid.lexical.search
    actual_fuse = hybrid.fusion.fuse
    fuse_calls = []
    def count_fusion(*a, **kw):
        fuse_calls.append(1)
        return actual_fuse(*a, **kw)
    def other_query(*a, **kw):
        changed_args = list(a)
        changed_args[4] = 'Heading'
        result = actual_lexical(*changed_args, **kw)
        assert result.matching == 3
        return result
    monkeypatch.setattr(hybrid.fusion, 'fuse', count_fusion)
    monkeypatch.setattr(hybrid.lexical, 'search', other_query)
    with pytest.raises(hybrid.HybridSearchError):
        hybrid.search(**args)
    assert fuse_calls == []
    result = module.search(**args)
    assert result.lexical.query_text_sha256 == hashlib.sha256(b'Heading').hexdigest()
    assert result.fusion.lexical_input_rows == 3
    assert all(hit.lexical_rank is not None for hit in result.fusion.hits)
    assert len(fuse_calls) == 1
    with pytest.raises(hybrid.HybridSearchError):
        hybrid.search(**args)
    assert len(fuse_calls) == 1
    monkeypatch.setattr(hybrid.lexical, 'search', actual_lexical)
    baseline = hybrid.search(**args)
    assert baseline.lexical.matching == 1 and baseline.fusion.lexical_input_rows == 1
    assert len(fuse_calls) == 2
    print('CONTROL_PREDICATE', original, '->', changed, flush=True)
    digest = hashlib.sha256(source.replace(original, changed).encode()).hexdigest()
    print('CONTROL_SOURCE_SHA256', digest, 'FUSION_COUNTS', [0, 1, 1, 2], flush=True)


def test_real_source_change_between_stages_refuses(owned, monkeypatch):
    args, root, ident = owned
    path = root / 'snapshots' / ident[7:] / '.core.json'
    saved = path.read_bytes()
    actual = hybrid.dense.search
    def corrupt_after_dense(*a, **kw):
        result = actual(*a, **kw)
        path.chmod(0o600)
        path.write_bytes(b'corrupt')
        path.chmod(0o400)
        return result
    monkeypatch.setattr(hybrid.dense, 'search', corrupt_after_dense)
    try:
        with pytest.raises(hybrid.HybridSearchError):
            hybrid.search(**args)
    finally:
        path.chmod(0o600)
        path.write_bytes(saved)
        path.chmod(0o400)


def test_real_source_change_before_final_refuses(owned, monkeypatch):
    args, root, ident = owned
    path = root / 'snapshots' / ident[7:] / '.core.json'
    saved = path.read_bytes()
    actual = hybrid.fusion.fuse
    def corrupt_after_fusion(*a, **kw):
        result = actual(*a, **kw)
        path.chmod(0o600)
        path.write_bytes(b'corrupt')
        path.chmod(0o400)
        return result
    monkeypatch.setattr(hybrid.fusion, 'fuse', corrupt_after_fusion)
    try:
        with pytest.raises(hybrid.HybridSearchError):
            hybrid.search(**args)
    finally:
        path.chmod(0o600)
        path.write_bytes(saved)
        path.chmod(0o400)


def test_real_dense_then_elapsed_deadline_refuses(owned, monkeypatch):
    import time
    args, _, _ = owned
    args['deadline_ms'] = 20000
    actual = hybrid.dense.search
    clock = time.monotonic
    budgets = []
    def expire(*a, **kw):
        budgets.append(kw['deadline_ms'])
        result = actual(*a, **kw)
        monkeypatch.setattr(time, 'monotonic', lambda: clock() + 30)
        return result
    monkeypatch.setattr(hybrid.dense, 'search', expire)
    with pytest.raises(hybrid.HybridSearchError):
        hybrid.search(**args)
    assert len(budgets) == 1 and 0 < budgets[0] < 20000


def test_real_empty_authority_is_complete(owned):
    args, _, _ = owned
    args['grants'] = p.Grants(schema_version=1, corpora=(), versions=(), labels=())
    result = hybrid.search(**args)
    assert result.dense.hits == result.lexical.hits == result.fusion.hits == ()
    assert result.fusion.degraded is False


def test_actual_engine_failure_is_not_empty(owned, monkeypatch):
    args, _, _ = owned
    calls = []
    def fail(*a, **kw):
        calls.append('dense')
        raise RuntimeError('private failure')
    monkeypatch.setattr(hybrid.dense, 'search', fail)
    with pytest.raises(hybrid.HybridSearchError, match='^hybrid search refused$'):
        hybrid.search(**args)
    assert calls == ['dense']


def test_real_bm25_oracle_ties_and_caps(owned, monkeypatch):
    import math
    from slaif_raggedized_helper import technical_analyzer

    args, _, _ = owned
    args.update(text='Heading', dense_k=1, lexical_k=1, partition_cap=1, k=1)
    loaded = []
    actual = catalog.load_catalog
    def capture(*a, **kw):
        result = actual(*a, **kw)
        loaded.append(result)
        return result
    monkeypatch.setattr(catalog, 'load_catalog', capture)
    result = hybrid.search(**args)
    source = loaded[0]
    tokens = [[term[0] for term in row.terms] for row in source.rows]
    query = [term.text for term in technical_analyzer.analyze(
        'Heading', technical_analyzer.Policy()).terms]
    avg = sum(map(len, tokens)) / len(tokens)
    for hit in result.lexical.hits:
        doc = tokens[hit.ordinal]
        oracle = 0.0
        for term in query:
            tf = doc.count(term)
            df = sum(term in other for other in tokens)
            if tf:
                oracle += math.log(1 + (len(tokens) - df + 0.5) / (df + 0.5)) * (
                    tf / (tf + 1.5 * (1 - 0.75 + 0.75 * len(doc) / avg)))
        assert hit.score == pytest.approx(oracle, rel=1e-5)
        assert hit.chunk_bytes == source.rows[hit.ordinal].chunk_bytes
    assert (result.lexical.eligible, result.lexical.matching,
            result.lexical.selected, result.lexical.returned) == (3, 3, 2, 1)
    assert result.lexical.partition_cap_applied and result.lexical.global_cap_applied
    assert result.dense.partition_cap_applied and result.dense.global_cap_applied
    assert result.fusion.returned == 1
