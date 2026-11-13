"""Tiny actual versioned sources for authorized lexical DATA."""
import hashlib
import json
import math

import numpy as np
import pytest

from slaif_raggedized_helper import provenance_records as p
from slaif_raggedized_helper import raw_lexical_search as lexical
from slaif_raggedized_helper import raw_snapshot_catalog as catalog
from test_raw_snapshot_directory_composition import materialize, restore_owned_directories  # noqa: F401
from test_raw_snapshot_files_composition import complete
from test_raw_snapshot_rows import enc

def make_sources(tmp_path, *, version='v1', empty=False, three=False, paired=False):
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
    (source_root / 'c').write_bytes(raw)
    (source_root / 'd').write_bytes(b'# Different\n\nnonmatching text')
    (source_root / 'e').write_bytes(raw + b' DeniedOnly')
    base = dict(logical_id='a', relative_path='a', display_uri='urn:owned', corpus='one',
                version=version, title='uniquetitle', access_labels=[], processing_approved=True,
                redistribution_rights='allowed', media_type='text/markdown', size=len(raw),
                sha256=hashlib.sha256(raw).hexdigest())
    second = dict(base, logical_id='b', relative_path='b', corpus='two',
                  access_labels=['secret'])
    if paired:
        second.update(size=len(denied_raw), sha256=hashlib.sha256(denied_raw).hexdigest())
    manifests = [base, second]
    manifests.append(dict(base, logical_id='c', relative_path='c'))
    nonmatch = (source_root / 'd').read_bytes()
    denied = (source_root / 'e').read_bytes()
    manifests.append(dict(base, logical_id='d', relative_path='d', corpus='two',
                          title='different', access_labels=['secret'], size=len(nonmatch),
                          sha256=hashlib.sha256(nonmatch).hexdigest()))
    manifests.append(dict(base, logical_id='e', relative_path='e', corpus='denied',
                          size=len(denied), sha256=hashlib.sha256(denied).hexdigest()))
    sources = parse_manifest(json.dumps(dict(schema_version=1, sources=manifests)).encode())
    originals = OriginalStore(tmp_path / 'store')
    revisions = [originals.admit(source_root, source) for source in sources.sources]
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
    except BaseException:
        derived.close()
        originals.close()
        raise


def test_owned_trace_composition(tmp_path, monkeypatch):
    from dataclasses import fields
    originals, derived, root, ident = make_sources(tmp_path)
    try:
        grants = p.Grants(schema_version=1, corpora=('one', 'two'), versions=('v1',),
                          labels=('secret',))
        observed = []
        index = lexical._index
        def capture(scorer, rows):
            observed.append(tuple(tuple(row) for row in rows))
            return index(scorer, rows)
        monkeypatch.setattr(lexical, '_index', capture)
        score_calls = []
        score = lexical._score
        def capture_score(scorer, terms):
            score_calls.append(tuple(terms))
            return score(scorer, terms)
        monkeypatch.setattr(lexical, '_score', capture_score)
        kwargs = dict(grants=grants, partition_cap=1, k=1)
        plain = lexical.search(originals, derived, str(root), ident, 'Heading', **kwargs)
        traced = lexical.search(originals, derived, str(root), ident, 'Heading',
                                trace=True, **kwargs)
        assert all(getattr(plain, f.name) == getattr(traced, f.name)
                   for f in fields(plain) if f.name != 'trace')
        assert (traced.eligible, traced.matching, traced.selected, traced.returned) == (4, 3, 2, 1)
        assert traced.partition_cap_applied and traced.global_cap_applied
        assert len(observed) == 2 and all(len(rows) == 4 for rows in observed)
        assert all('deniedonly' not in row for rows in observed for row in rows)
        assert all(any('heading' in row for row in rows) for rows in observed)
        # Source identities and terms come from the original-backed catalog, not the trace.
        source_for_scores = catalog.load_catalog(originals, derived, str(root), ident)
        by_name = {}
        for row in source_for_scores.rows:
            src = json.loads(row.source_bytes)
            decl = json.loads(row.declaration_bytes)
            scope = json.loads(row.scope_bytes)
            name = src['logical_id']
            assert name not in by_name
            by_name[name] = (row, decl, scope)
        assert set(by_name) == set('abcde')
        for name, (row, decl, scope) in by_name.items():
            src = json.loads(row.source_bytes)
            chunk = json.loads(row.chunk_bytes)
            assert src['relative_path'] == scope['document_id'] == name
            assert (src['corpus'], src['version'], src['access_labels']) == (
                scope['corpus'], scope['version'], scope['labels'])
            assert (chunk['chunk_id'], chunk['revision_id'], row.representation_id) == (
                decl['chunk_id'], decl['revision_id'], decl['representation_id'])
            assert scope['revision_id'] == decl['revision_id']
            partition = dict(schema=1, corpus=scope['corpus'], version=scope['version'],
                             labels=scope['labels'])
            canonical = json.dumps(partition, sort_keys=True, separators=(',', ':'),
                                   ensure_ascii=True).encode()
            assert decl['partition_id'] == 'sha256:' + hashlib.sha256(
                b'slaif-fingerprint-v1\n' + canonical).hexdigest()
            assert scope['corpus'] == {'a': 'one', 'b': 'two', 'c': 'one',
                                       'd': 'two', 'e': 'denied'}[name]
            assert scope['version'] == 'v1'
            assert scope['labels'] == (['secret'] if name in 'bd' else [])
            assert decl['ordinal'] == source_for_scores.rows.index(by_name[name][0])
        authorized = [by_name[name] for name in 'abcd']
        tokens = {decl['ordinal']: [term[0] for term in row.terms]
                  for row, decl, _ in authorized}
        assert {name for name in 'abcd' if set(tokens[by_name[name][1]['ordinal']])
                & {'Heading', 'heading'}} == set('abc')
        avg = sum(map(len, tokens.values())) / 4
        scores = {}
        for name in 'abc':
            _, decl, _ = by_name[name]
            row_tokens = tokens[decl['ordinal']]
            value = 0.0
            for term in ('Heading', 'heading'):
                tf = row_tokens.count(term)
                df = sum(term in ts for ts in tokens.values())
                if tf:
                    value += math.log(1 + (4 - df + 0.5) / (df + 0.5)) * (
                        tf / (tf + 1.5 * (1 - 0.75 + 0.75 * len(row_tokens) / avg)))
            scores[decl['ordinal']] = value
        assert len(set(scores.values())) == 1  # Fixture exercises the complete tie key.
        ranked = sorted((by_name[name][1] for name in 'abc'),
                        key=lambda d: (-scores[d['ordinal']], d['chunk_id'],
                                       d['revision_id'], d['representation_id']))
        parts = sorted({decl['partition_id'] for _, decl, _ in authorized})
        assert len(parts) == 2
        selected = []
        for decl in ranked:
            if decl['partition_id'] not in {d['partition_id'] for d in selected}:
                selected.append(decl)
        returned = selected[:1]
        def ids(ds):
            return tuple(d['ordinal'] for d in ds)
        def identity(d):
            return (d['ordinal'], d['partition_id'], d['chunk_id'],
                    d['revision_id'], d['representation_id'])
        assert tuple((r.ordinal, r.partition_id, r.chunk_id, r.revision_id,
                      r.representation_id) for r in traced.trace.rows) == tuple(
                          identity(d) for _, d, _ in sorted(authorized,
                                                          key=lambda x: x[1]['ordinal']))
        assert tuple(p.partition_id for p in traced.trace.partitions) == tuple(parts)
        for part, count in zip(traced.trace.partitions, traced.partitions, strict=True):
            eligible = sorted(
                (d for _, d, _ in authorized if d['partition_id'] == part.partition_id),
                key=lambda d: d['ordinal'])
            partition_ranked = [d for d in ranked if d['partition_id'] == part.partition_id]
            partition_selected = [d for d in selected if d['partition_id'] == part.partition_id]
            partition_returned = [d for d in returned if d['partition_id'] == part.partition_id]
            expected_arrays = tuple(map(ids, (eligible, partition_ranked,
                                              partition_selected, partition_returned)))
            assert (part.eligible_ordinals, part.ranked_ordinals, part.selected_ordinals,
                    part.returned_ordinals) == expected_arrays
            assert (count.partition_id, count.eligible, count.matching, count.selected,
                    count.returned) == (part.partition_id, len(eligible), len(partition_ranked),
                                        len(partition_selected), len(partition_returned))
        assert traced.trace.selected_ordinals == ids(selected)
        assert traced.trace.returned_ordinals == ids(returned)
        assert tuple(hit.ordinal for hit in traced.hits) == ids(returned)
        for hit in traced.hits:
            assert hit.score == pytest.approx(scores[hit.ordinal], rel=1e-5)
        empty = lexical.search(originals, derived, str(root), ident, '', grants=None, trace=True)
        assert empty.trace.rows == empty.trace.partitions == ()
        oov = lexical.search(originals, derived, str(root), ident, 'absentxyz', grants=grants,
                             trace=True)
        assert len(oov.trace.rows) == 4 and oov.matching == 0
        loader = catalog.load_catalog
        load_calls = []
        real_allows = p.reader_allows
        def after_load(*a, **kw):
            result = loader(*a, **kw)
            load_calls.append(1)
            return result
        monkeypatch.setattr(catalog, 'load_catalog', after_load)
        # Controlled static-policy fault targets fixture d, independently of the trace.
        source = loader(originals, derived, str(root), ident)
        assert source == source_for_scores
        nonmatch_row, nonmatch_decl, _ = by_name['d']
        assert nonmatch_decl['ordinal'] in tokens
        assert not set(tokens[nonmatch_decl['ordinal']]) & {'Heading', 'heading'}
        denied_scope = p.admit_record('Scope', nonmatch_row.scope_bytes)
        def late_deny(scope, g, r):
            if len(load_calls) >= 2 and scope == denied_scope:
                return False
            return real_allows(scope, g, r)
        monkeypatch.setattr(p, 'reader_allows', late_deny)
        with pytest.raises(lexical.LexicalSearchError):
            lexical.search(originals, derived, str(root), ident, 'Heading', trace=True, **kwargs)
        assert len(load_calls) == 2
        monkeypatch.setattr(p, 'reader_allows', real_allows)
        load_calls.clear()
        assert lexical.search(originals, derived, str(root), ident, 'Heading', trace=True, **kwargs)
        assert len(load_calls) == 2
        load_calls.clear()
        path = next((originals.root / 'blobs').iterdir())
        saved = path.read_bytes()
        def corrupt_second(*a, **kw):
            load_calls.append(1)
            if len(load_calls) == 2:
                path.chmod(0o600)
                path.write_bytes(b'corrupt')
                path.chmod(0o400)
            return loader(*a, **kw)
        monkeypatch.setattr(catalog, 'load_catalog', corrupt_second)
        try:
            with pytest.raises(lexical.LexicalSearchError):
                lexical.search(originals, derived, str(root), ident, 'Heading',
                               trace=True, **kwargs)
            assert len(load_calls) == 2
            assert len(observed) == len(score_calls) == 5
        finally:
            path.chmod(0o600)
            path.write_bytes(saved)
            path.chmod(0o400)
    finally:
        derived.close()
        originals.close()
