import hashlib
import json
import sys
from dataclasses import asdict
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'unit'))
from test_native_tokenizers import make_native  # noqa: E402
from test_structured_text_composition import create_store  # noqa: E402
from slaif_raggedized_helper import ingestion_bundle as bundle, chunking  # noqa: E402
from slaif_raggedized_helper import native_chunking as nc, provenance_jsonl as jl  # noqa: E402
from slaif_raggedized_helper import provenance_records as p, structured_text as st  # noqa: E402


def test_actual_native_text_bundle(tmp_path, monkeypatch):
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
    store, revisions = create_store(tmp_path, text)
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
        # The producer must actually split this paragraph with overlap and repeat
        # the original table header in multiple chunks; neither is inferred from size.
        paragraph = next(x for x in item.blocks if x.text.startswith('alpha beta'))
        header = next(x for x in item.blocks if x.kind == 'table_header')
        spans = [(f.start, f.end) for c in result.chunks for f in c.fragments
                 if isinstance(f, p.SourceFragment) and f.block_id == paragraph.block_id]
        assert len(spans) > 1 and max(end for _, end in spans) == len(paragraph.text)
        assert any(b[0] < a[1] for a, b in zip(spans, spans[1:]))
        assert sum(any(isinstance(f, p.SourceFragment) and f.block_id == header.block_id
                       for f in c.fragments) for c in result.chunks) > 1
        valid = bundle.validate(store, nc._json(metadata), members)
        assert valid.chunks == result.chunks
        assert bundle.validate(store, valid.metadata_json, valid.members) == valid
        # Small instrumented caps exercise exact admission and one byte over
        # against real canonical producer output, including the aggregate limit.
        sizes = tuple(len(payload) for _, payload in valid.members)
        total = len(valid.metadata_json) + sum(sizes)
        with monkeypatch.context() as patch:
            patch.setattr(bundle, 'METADATA_BYTES', len(valid.metadata_json))
            patch.setattr(bundle, 'CAPS', sizes)
            patch.setattr(bundle, 'TOTAL_BYTES', total)
            assert bundle.validate(store, valid.metadata_json, valid.members) == valid
            for cap_index in range(7):
                with monkeypatch.context() as limited:
                    if cap_index == 0:
                        limited.setattr(bundle, 'METADATA_BYTES', len(valid.metadata_json) - 1)
                    elif cap_index == 6:
                        limited.setattr(bundle, 'TOTAL_BYTES', total - 1)
                    else:
                        caps = list(sizes)
                        caps[cap_index - 1] -= 1
                        limited.setattr(bundle, 'CAPS', tuple(caps))
                    calls = []
                    limited.setattr(bundle.source, 'validate', lambda *a: calls.append(a))
                    with pytest.raises(bundle.BundleError, match='^ingestion bundle refused$'):
                        bundle.validate(store, valid.metadata_json, valid.members)
                    assert not calls
        # Rebind chunk identity and receipt input digests so each malformed
        # composition first passes the independent native leaf and registry.
        from slaif_raggedized_helper import bundle_native_records as leaf
        original_receipts = json.loads(members[4][1])['receipts']
        def coordinated(chunks, neighbor_mode=None):
            receipt_groups = {c.chunk_id: original_receipts[3*i:3*i+3]
                              for i, c in enumerate(result.chunks)}
            rebuilt, receipts = [], []
            for old_id, chunk in chunks:
                chunk = chunk.model_copy(update={'text': ''.join(
                    f.copied_text if isinstance(f, p.SourceFragment) else f.text
                    for f in chunk.fragments)})
                chunk = chunk.model_copy(update={'text_sha256': hashlib.sha256(
                    chunk.text.encode()).hexdigest()})
                chunk = chunk.model_copy(update={'chunk_id': p.chunk_id(chunk)})
                registry.bind_chunk(chunk)
                rebuilt.append(chunk)
                group = json.loads(json.dumps(receipt_groups[old_id]))
                rep = ''.join(chunk.heading_path) + chunk.text
                for receipt, pair in zip(group, ((chunk.text, None), (rep, None), (query, rep))):
                    receipt['chunk_id'] = chunk.chunk_id
                    receipt['count']['input_sha256'] = nc._input_digest(*pair)
                receipts.extend(group)
            links = [p.Neighbors(schema_version=1, chunk_id=c.chunk_id,
                     previous_chunk_id=rebuilt[i-1].chunk_id if i else None,
                     next_chunk_id=rebuilt[i+1].chunk_id if i+1 < len(rebuilt) else None)
                     for i, c in enumerate(rebuilt)]
            if neighbor_mode == 'missing':
                links.pop()
            elif neighbor_mode == 'extra_null':
                links[1] = links[1].model_copy(update={'previous_chunk_id': None})
            elif neighbor_mode == 'wrong':
                links[0] = links[0].model_copy(update={'next_chunk_id': rebuilt[2].chunk_id})
                links[1] = links[1].model_copy(update={'previous_chunk_id': None})
                links[2] = links[2].model_copy(update={'previous_chunk_id': None})
            registry.bind_neighbors(tuple(rebuilt), tuple(links))
            changed = list(members)
            changed[2] = ('chunks', encode('Chunk', rebuilt))
            changed[3] = ('neighbors', encode('Neighbors', links))
            changed[4] = ('receipts', nc._json({'version': 1, 'receipts': receipts}))
            meta = json.loads(nc._json(metadata))
            meta['counts'].update(chunks=len(rebuilt), neighbors=len(rebuilt),
                                  receipts=3*len(rebuilt))
            leaf.validate(nc._json(meta['chunking']), changed[2][1], changed[4][1], len(rebuilt))
            with pytest.raises(bundle.BundleError, match='^ingestion bundle refused$'):
                bundle.validate(store, nc._json(meta), tuple(changed))

        originals = [(c.chunk_id, c) for c in result.chunks]
        assert len(originals) >= 3
        coordinated(originals[:-1])  # complete final chunk and its tail removed
        coordinated([originals[1], originals[0], *originals[2:]])
        c = result.chunks[0]
        coordinated([(c.chunk_id, c.model_copy(update={'heading_path': ('forged',)})),
                     *originals[1:]])
        coordinated(originals, 'missing')
        coordinated(originals, 'extra_null')
        coordinated(originals, 'wrong')
        # Remove the first character of the first paragraph interval: the
        # preceding block remains complete but the new block starts with a gap.
        ci = next(i for i, c in enumerate(result.chunks) if any(
            isinstance(f, p.SourceFragment) and f.block_id == paragraph.block_id
            and f.start == 0 for f in c.fragments))
        c = result.chunks[ci]
        fi = next(i for i, f in enumerate(c.fragments) if isinstance(f, p.SourceFragment)
                  and f.block_id == paragraph.block_id and f.start == 0)
        fragments = list(c.fragments)
        f = fragments[fi]
        assert len(f.copied_text) > 1
        fragments[fi] = f.model_copy(update={'start': 1, 'copied_text': f.copied_text[1:]})
        altered = list(originals)
        altered[ci] = (c.chunk_id, c.model_copy(update={'fragments': tuple(fragments)}))
        coordinated(altered)

        # Advance only the outer module's clock after its final canonicalization.
        from types import SimpleNamespace
        real_json = bundle._json
        canonicalized = []
        def track_json(value):
            out = real_json(value)
            if isinstance(value, dict) and value.get('kind') == 'native-ingestion-bundle':
                canonicalized.append(True)
            return out
        with monkeypatch.context() as patch:
            patch.setattr(bundle, '_json', track_json)
            patch.setattr(bundle, 'time', SimpleNamespace(
                monotonic=lambda: 31 if canonicalized else 0))
            with pytest.raises(bundle.BundleError, match='^ingestion bundle refused$'):
                bundle.validate(store, nc._json(metadata), members)
        assert canonicalized
        # Same bytes with distinct source identities, rights and an explicit
        # version must each produce independently bound, accepted bundles.
        assert revisions[0].source.version is None
        versioned = store.admit(tmp_path / 'root', revisions[0].source.model_copy(
            update={'version': 'v2'}))
        accepted = [valid]
        for revision in (revisions[1], revisions[2], versioned):
            extracted = st.extract(store, revision.revision_id)
            reg = p.Registry((revision,), (extracted.dependency,), extracted.blocks)
            produced = nc.build(reg, extracted.blocks, *defs, runtime, query, policy)
            meta = json.loads(nc._json(metadata))
            meta['revision_id'] = revision.revision_id
            meta['extraction']['dependency'] = extracted.dependency.model_dump()
            meta['extraction']['uncertainty'] = extracted.uncertainty
            meta['counts'].update(blocks=len(extracted.blocks), chunks=len(produced.chunks),
                                  neighbors=len(produced.chunks), receipts=3*len(produced.chunks))
            value_members = (('blocks', encode('Block', extracted.blocks)),
                ('coverage', nc._json(dict(schema_version=1, kind='unicode_codepoints',
                                            spans=[asdict(x) for x in extracted.coverage]))),
                ('chunks', encode('Chunk', produced.chunks)),
                ('neighbors', encode('Neighbors', produced.neighbors)),
                ('receipts', produced.receipts_json()))
            accepted.append(bundle.validate(store, nc._json(meta), value_members))
        assert len({v.revision.revision_id for v in accepted}) == len(accepted)
        assert len({v.chunks[0].chunk_id for v in accepted}) == len(accepted)
        assert accepted[1].scope.labels == ('secret',)
        assert accepted[1].scope.redistribution_rights == 'prohibited'
        assert accepted[-1].revision.source.version == 'v2'
        for bad in (members[::-1], members[:-1], (("bad", members[0][1]), *members[1:])):
            with pytest.raises(bundle.BundleError):
                bundle.validate(store, nc._json(metadata), bad)
        for key, value in [('schema_version', True), ('kind', 'x'), ('extra', 1)]:
            bad = dict(metadata, **{key: value})
            with pytest.raises(bundle.BundleError):
                bundle.validate(store, nc._json(bad), members)
        missing = dict(metadata)
        del missing['counts']
        with pytest.raises(bundle.BundleError, match='^ingestion bundle refused$'):
            bundle.validate(store, nc._json(missing), members)
        bad = list(members)
        bad[3] = ('neighbors', b'{}\n')
        with pytest.raises(bundle.BundleError):
            bundle.validate(store, nc._json(metadata), tuple(bad))
        # Coherently rebind a changed source fragment and its native receipts.  The
        # leaf validator accepts these bytes; complete-source composition must refuse.
        records = [json.loads(line) for line in members[2][1].splitlines()]
        candidate = records[0]
        fragment = next(f for f in candidate['fragments'] if f['kind'] == 'source')
        assert len(fragment['copied_text']) > 1
        fragment['start'] += 1
        fragment['copied_text'] = fragment['copied_text'][1:]
        candidate['text'] = ''.join(f.get('copied_text', f.get('text', ''))
                                    for f in candidate['fragments'])
        candidate['text_sha256'] = hashlib.sha256(candidate['text'].encode()).hexdigest()
        candidate['chunk_id'] = p.chunk_id(p.admit_record('Chunk', nc._json(candidate)))
        receipts = json.loads(members[4][1])
        representation = ''.join(candidate['heading_path']) + candidate['text']
        for i, pair in enumerate(((candidate['text'], None), (representation, None),
                                  (query, representation))):
            receipts['receipts'][i]['chunk_id'] = candidate['chunk_id']
            receipts['receipts'][i]['count']['input_sha256'] = nc._input_digest(*pair)
        links = [json.loads(line) for line in members[3][1].splitlines()]
        links[0]['chunk_id'] = candidate['chunk_id']
        if len(links) > 1:
            links[1]['previous_chunk_id'] = candidate['chunk_id']
        changed = list(members)
        changed[2] = ('chunks', b''.join(nc._json(x) + b'\n' for x in records))
        changed[3] = ('neighbors', b''.join(nc._json(x) + b'\n' for x in links))
        changed[4] = ('receipts', nc._json(receipts))
        leaf.validate(nc._json(metadata['chunking']), changed[2][1], changed[4][1],
                      len(result.chunks))
        with pytest.raises(bundle.BundleError):
            bundle.validate(store, nc._json(metadata), tuple(changed))
        for index in (0, 1, 4):
            changed = list(members)
            changed[index] = (changed[index][0], changed[index][1] + b'!')
            with pytest.raises(bundle.BundleError):
                bundle.validate(store, nc._json(metadata), tuple(changed))
        bad = json.loads(nc._json(metadata))
        bad['revision_id'] = revisions[1].revision_id
        with pytest.raises(bundle.BundleError):
            bundle.validate(store, nc._json(bad), members)
    finally:
        store.close()
