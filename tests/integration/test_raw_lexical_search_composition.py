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
    if three:
        (source_root / 'c').write_bytes(raw)
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
        manifests.append(dict(base, logical_id='c', relative_path='c'))
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


def test_real_sources_oracle_and_access_control(tmp_path, monkeypatch):
    originals, derived, root, ident = make_sources(tmp_path)
    try:
        source = catalog.load_catalog(originals, derived, str(root), ident)
        grants = p.Grants(schema_version=1, corpora=('one', 'two'), versions=('v1',),
                          labels=('secret',))
        result = lexical.search(originals, derived, str(root), ident, 'Heading Heading',
                                grants=grants)
        assert len(result.hits) == 2
        assert (result.eligible, result.matching, result.selected, result.returned) == (2, 2, 2, 2)
        tokens = [[t[0] for t in row.terms] for row in source.rows]
        terms = ['Heading', 'heading', 'Heading', 'heading']
        avg = sum(map(len, tokens)) / len(tokens)
        for hit in result.hits:
            doc = tokens[hit.ordinal]
            oracle = 0.0
            for term in terms:
                tf = doc.count(term)
                df = sum(term in other for other in tokens)
                if tf:
                    oracle += math.log(1 + (len(tokens) - df + 0.5) / (df + 0.5)) * (
                        tf / (tf + 1.5 * (1 - 0.75 + 0.75 * len(doc) / avg)))
            assert hit.score == pytest.approx(oracle, rel=1e-5)
            assert hit.chunk_bytes == source.rows[hit.ordinal].chunk_bytes
        empty = lexical.search(originals, derived, str(root), ident, 'absent', grants=grants)
        assert empty.hits == ()
        single = grants.model_copy(update={'corpora': ('one',)})
        baseline = lexical.search(originals, derived, str(root), ident, 'Heading', grants=single)
        assert (baseline.eligible, baseline.matching, baseline.returned) == (1, 1, 1)
        observed = []
        real_index = lexical._index
        def capture(scorer, rows):
            observed.append(len(rows))
            return real_index(scorer, rows)
        monkeypatch.setattr(lexical, '_index', capture)
        monkeypatch.setattr(lexical, '_allowed_before_index', lambda *args: True)
        with pytest.raises(lexical.LexicalSearchError):
            lexical.search(originals, derived, str(root), ident, 'Heading', grants=single)
        assert observed == [2]
    finally:
        derived.close()
        originals.close()


def test_rendered_title_caps_restriction_and_fresh_source(tmp_path, monkeypatch):
    originals, derived, root, ident = make_sources(tmp_path)
    try:
        grants = p.Grants(schema_version=1, corpora=('one', 'two'), versions=('v1',),
                          labels=('secret',))
        result = lexical.search(originals, derived, str(root), ident, 'uniquetitle',
                                grants=grants, k=1)
        assert (result.eligible, result.matching, result.selected, result.returned) == (2, 2, 2, 1)
        assert result.global_cap_applied and not result.partition_cap_applied
        assert all('uniquetitle' not in json.loads(hit.chunk_bytes)['text'] for hit in result.hits)
        restrictions = p.Restrictions(schema_version=1, corpora=('one',), versions=('v1',))
        result = lexical.search(originals, derived, str(root), ident, 'uniquetitle',
                                grants=grants, restrictions=restrictions)
        assert (result.eligible, result.returned, len(result.partitions)) == (1, 1, 1)
        original_loader = catalog.load_catalog
        path = root / 'snapshots' / ident[7:] / '.core.json'
        saved = path.read_bytes()
        calls = []
        def corrupt_after_first(*args, **kwargs):
            calls.append(1)
            if len(calls) == 2:
                path.chmod(0o600)
                path.write_bytes(b'corrupt')
                path.chmod(0o400)
            return original_loader(*args, **kwargs)
        monkeypatch.setattr(catalog, 'load_catalog', corrupt_after_first)
        try:
            with pytest.raises(lexical.LexicalSearchError):
                lexical.search(originals, derived, str(root), ident, 'uniquetitle', grants=grants)
            assert len(calls) == 2
        finally:
            path.chmod(0o600)
            path.write_bytes(saved)
            path.chmod(0o400)
    finally:
        derived.close()
        originals.close()


def test_unversioned_denied_and_interrupt(tmp_path, monkeypatch):
    originals, derived, root, ident = make_sources(tmp_path, version=None)
    try:
        grants = p.Grants(schema_version=1, corpora=('one', 'two'), versions=('v1',),
                          labels=('secret',))
        calls = []
        monkeypatch.setattr(lexical, '_index', lambda *args: calls.append('index'))
        result = lexical.search(originals, derived, str(root), ident, 'uniquetitle', grants=grants)
        assert result.hits == result.partitions == ()
        assert result.eligible == 0 and calls == []
        result = lexical.search(originals, derived, str(root), ident, '', grants=None)
        assert result.hits == result.partitions == () and calls == []
        marker = KeyboardInterrupt()
        def interrupt(*args, **kwargs):
            raise marker
        monkeypatch.setattr(catalog, 'load_catalog', interrupt)
        with pytest.raises(KeyboardInterrupt) as caught:
            lexical.search(originals, derived, str(root), ident, 'q', grants=grants)
        assert caught.value is marker
    finally:
        derived.close()
        originals.close()


def test_empty_data_and_missing_backend(tmp_path, monkeypatch):
    import importlib.metadata

    originals, derived, root, ident = make_sources(tmp_path, empty=True)
    try:
        grants = p.Grants(schema_version=1, corpora=('one',), versions=('v1',), labels=())
        result = lexical.search(originals, derived, str(root), ident, 'q', grants=grants)
        assert result.hits == result.partitions == () and result.eligible == 0
        calls = []
        monkeypatch.setattr(catalog, 'load_catalog', lambda *args, **kwargs: calls.append('load'))
        def absent(_):
            raise importlib.metadata.PackageNotFoundError
        monkeypatch.setattr(importlib.metadata, 'version', absent)
        with pytest.raises(lexical.LexicalSearchError):
            lexical.search(originals, derived, str(root), ident, 'q', grants=grants)
        assert calls == []
    finally:
        derived.close()
        originals.close()


def test_original_deadline_is_not_renewed(tmp_path, monkeypatch):
    import time

    originals, derived, root, ident = make_sources(tmp_path)
    try:
        grants = p.Grants(schema_version=1, corpora=('one',), versions=('v1',), labels=())
        actual_loader = catalog.load_catalog
        clock = time.monotonic
        calls = []
        def delayed(*args, **kwargs):
            calls.append(kwargs['deadline_ms'])
            result = actual_loader(*args, **kwargs)
            monkeypatch.setattr(time, 'monotonic', lambda: clock() + 2)
            return result
        monkeypatch.setattr(catalog, 'load_catalog', delayed)
        with pytest.raises(lexical.LexicalSearchError):
            lexical.search(originals, derived, str(root), ident, 'q', grants=grants,
                           deadline_ms=1000)
        assert len(calls) == 1 and 0 < calls[0] <= 1000
    finally:
        derived.close()
        originals.close()


def test_three_row_partition_cap_and_ties(tmp_path):
    originals, derived, root, ident = make_sources(tmp_path, three=True)
    try:
        grants = p.Grants(schema_version=1, corpora=('one', 'two'), versions=('v1',),
                          labels=('secret',))
        uncapped = lexical.search(originals, derived, str(root), ident, 'uniquetitle',
                                  grants=grants)
        assert (uncapped.eligible, uncapped.matching, uncapped.returned) == (3, 3, 3)
        assert len({hit.score for hit in uncapped.hits}) == 1
        assert [h.chunk_id for h in uncapped.hits] == sorted(h.chunk_id for h in uncapped.hits)
        capped = lexical.search(originals, derived, str(root), ident, 'uniquetitle',
                                grants=grants, partition_cap=1, k=1)
        assert (capped.eligible, capped.matching, capped.selected, capped.returned) == (3, 3, 2, 1)
        assert capped.partition_cap_applied and capped.global_cap_applied
        assert sorted((p.eligible, p.matching, p.selected) for p in capped.partitions) == [
            (1, 1, 1), (2, 2, 1)]
        assert capped.hits == uncapped.hits[:1]
    finally:
        derived.close()
        originals.close()


def test_invalid_backend_scores_refuse(tmp_path, monkeypatch):
    originals, derived, root, ident = make_sources(tmp_path)
    try:
        grants = p.Grants(schema_version=1, corpora=('one', 'two'), versions=('v1',),
                          labels=('secret',))
        for invalid in (np.array([float('nan'), 1], dtype='float32'),
                        np.array([1], dtype='float32'), np.array([1, 1], dtype='float64')):
            monkeypatch.setattr(lexical, '_score', lambda *args, result=invalid: result)
            with pytest.raises(lexical.LexicalSearchError):
                lexical.search(originals, derived, str(root), ident, 'uniquetitle', grants=grants)
    finally:
        derived.close()
        originals.close()


def test_denied_source_addition_does_not_change_allowed_results(tmp_path):
    originals, derived, root, ident, subset_root, subset_id = make_sources(tmp_path, paired=True)
    try:
        grants = p.Grants(schema_version=1, corpora=('one',), versions=('v1',), labels=())
        full = catalog.load_catalog(originals, derived, str(root), ident)
        assert len(full.rows) == 2
        assert any(term[0] == 'DeniedOnly' for row in full.rows for term in row.terms)
        before = lexical.search(originals, derived, str(subset_root), subset_id, 'Heading',
                                grants=grants)
        after = lexical.search(originals, derived, str(root), ident, 'Heading', grants=grants)
        assert (before.eligible, before.matching, before.selected, before.returned) == (1, 1, 1, 1)
        assert (after.eligible, after.matching, after.selected, after.returned) == (1, 1, 1, 1)
        left, right = before.hits[0], after.hits[0]
        assert (left.chunk_id, left.revision_id, left.representation_id, left.scope_bytes,
                left.chunk_bytes, left.score, left.rank) == (
                    right.chunk_id, right.revision_id, right.representation_id, right.scope_bytes,
                    right.chunk_bytes, right.score, right.rank)
        assert before.partitions == after.partitions
    finally:
        derived.close()
        originals.close()


def test_no_index_for_empty_oov_and_denied(tmp_path, monkeypatch):
    originals, derived, root, ident = make_sources(tmp_path)
    try:
        grants = p.Grants(schema_version=1, corpora=('one', 'two'), versions=('v1',),
                          labels=('secret',))
        calls = []
        monkeypatch.setattr(lexical, '_index', lambda *args: calls.append('index'))
        monkeypatch.setattr(lexical, '_score', lambda *args: calls.append('score'))
        for text, authority in (('', grants), ('absentxyz', grants), ('Heading', None)):
            result = lexical.search(originals, derived, str(root), ident, text, grants=authority)
            assert result.hits == ()
        assert calls == []
    finally:
        derived.close()
        originals.close()
