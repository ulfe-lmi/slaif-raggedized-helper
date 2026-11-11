import hashlib
import json
import sys
from dataclasses import asdict
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'unit'))
from test_native_tokenizers import make_native  # noqa: E402
from test_bundle_pdf_records_composition import encode  # noqa: E402
from test_pdf_extraction_composition import (  # noqa: E402
    configured_runtime, make_store, nested_form_pdf, tiny_pdf, visual_pdf,
)
from slaif_raggedized_helper import chunking, ingestion_bundle as bundle  # noqa: E402
from slaif_raggedized_helper import native_chunking as nc, pdf_extraction as pdf  # noqa: E402
from slaif_raggedized_helper import provenance_jsonl as jl, provenance_records as p  # noqa: E402


def build(tmp_path, data):
    paths, runtime, make = make_native(tmp_path)
    defs = (make(paths[0], 'bge_body'), make(paths[0], 'bge_representation'),
            make(paths[1], 'reranker_pair'))
    store, revision = make_store(tmp_path, data)
    item = pdf.extract(store, revision.revision_id, configured_runtime())
    header, blocks, coverage = encode(item)
    policy, query = chunking.Policy(pair_max=1280), 'hello'
    if not item.blocks:
        return store, revision, item, None, None
    result = nc.build(p.Registry((revision,), (item.dependency,), item.blocks), item.blocks,
                      *defs, runtime, query, policy)
    declarations = [dict(role=d.role, artifact_sha256=d.sha256,
                         backend_version=d.backend_version, model_revision=d.model_revision,
                         preprocessing=d.preprocessing) for d in defs]
    definition = nc._json(dict(version=1, kind='observed-local-native', policy=asdict(policy),
                               definitions=[nc._identity(d) for d in defs],
                               query_input_sha256=nc._input_digest(query, None),
                               serialization=nc._SERIALIZATION)).decode()
    metadata = dict(schema_version=1, kind='native-ingestion-bundle',
                    revision_id=revision.revision_id, extraction=json.loads(header),
                    chunking=dict(policy=asdict(policy), query=query, definitions=declarations,
                                  policy_definition=definition, policy_id=p.policy_id(definition)),
                    counts=dict(blocks=len(item.blocks), chunks=len(result.chunks),
                                neighbors=len(result.chunks), receipts=3 * len(result.chunks)))
    def enc(kind, values):
        return jl.encode(kind, tuple(x.model_dump_json().encode() for x in values))
    members = (('blocks', blocks), ('coverage', coverage), ('chunks', enc('Chunk', result.chunks)),
               ('neighbors', enc('Neighbors', result.neighbors)),
               ('receipts', result.receipts_json()))
    return store, revision, item, metadata, members


@pytest.mark.parametrize('data', [tiny_pdf(), tiny_pdf(2), nested_form_pdf(),
                                  visual_pdf('raster'), visual_pdf('vector')])
def test_pdf_native_composition(tmp_path, monkeypatch, data):
    store, revision, item, metadata, members = build(tmp_path, data)
    try:
        monkeypatch.setattr(pdf, '_run', lambda *a: pytest.fail('PDF launched on load'))
        monkeypatch.setattr(nc, 'build', lambda *a, **k: pytest.fail('native launched on load'))
        value = bundle.validate(store, nc._json(metadata), members)
        assert value.pages == item.pages and value.coverage == ()
        assert (value.adapter, value.status, value.coverage_kind) == (
            'pdf_extraction', item.status, 'pdf_pages')
        assert value.blocks == item.blocks and value.scope == p.catalog((revision,))[0]
        assert all(c.heading_path == () for c in value.chunks)
        assert len(value.receipts) == 3 * len(value.chunks)
        progress = {b.block_id: 0 for b in value.blocks}
        for i, chunk in enumerate(value.chunks):
            link = value.neighbors[i]
            assert (link.chunk_id, link.previous_chunk_id, link.next_chunk_id) == (
                chunk.chunk_id, value.chunks[i - 1].chunk_id if i else None,
                value.chunks[i + 1].chunk_id if i + 1 < len(value.chunks) else None)
            for fragment in chunk.fragments:
                if (isinstance(fragment, p.SourceFragment)
                        and fragment.end > progress[fragment.block_id]):
                    assert fragment.start <= progress[fragment.block_id]
                    progress[fragment.block_id] = fragment.end
            representation = ''.join(chunk.heading_path) + chunk.text
            for receipt, role, pair in zip(
                value.receipts[3 * i:3 * i + 3],
                ('bge_body', 'bge_representation', 'reranker_pair'),
                ((chunk.text, None), (representation, None), ('hello', representation)),
            ):
                assert receipt.chunk_id == chunk.chunk_id and receipt.count.role == role
                assert receipt.count.input_sha256 == nc._input_digest(*pair)
        assert progress == {b.block_id: len(b.text) for b in value.blocks}
        assert bundle.validate(store, value.metadata_json, value.members) == value
        assert store.read_original(revision.revision_id) == data
        for field, bad in [('adapter', 'unknown'), ('coverage_kind', 'unicode_codepoints'),
                           ('status', 'complete_text')]:
            changed = json.loads(nc._json(metadata))
            changed['extraction'][field] = bad
            with pytest.raises(bundle.BundleError):
                bundle.validate(store, nc._json(changed), members)
        changed = list(members)
        coverage = json.loads(changed[1][1])
        coverage['pages'][0]['page'] = 99
        changed[1] = ('coverage', nc._json(coverage))
        with pytest.raises(bundle.BundleError):
            bundle.validate(store, nc._json(metadata), tuple(changed))
        changed = list(members)
        blocks = [json.loads(x) for x in changed[0][1].splitlines()]
        blocks[0]['geometry'] = [3, 2, 1, 4]
        changed[0] = ('blocks', b''.join(nc._json(x) + b'\n' for x in blocks))
        with pytest.raises(bundle.BundleError):
            bundle.validate(store, nc._json(metadata), tuple(changed))
        changed = json.loads(nc._json(metadata))
        changed['revision_id'] = 'sha256:' + '0' * 64
        with pytest.raises(bundle.BundleError):
            bundle.validate(store, nc._json(changed), members)
    finally:
        store.close()


def test_all_visual_refuses_full_bundle(tmp_path):
    store, _, item, _, _ = build(tmp_path, visual_pdf('raster', text=False))
    try:
        assert not item.blocks and item.status == 'partial_visual_needed'
        header, blocks, coverage = encode(item)
        metadata = dict(schema_version=1, kind='native-ingestion-bundle',
                        revision_id=item.revision.revision_id, extraction=json.loads(header),
                        chunking={}, counts=dict(blocks=0, chunks=0, neighbors=0, receipts=0))
        members = (('blocks', blocks), ('coverage', coverage), ('chunks', b''),
                   ('neighbors', b''), ('receipts', b''))
        with pytest.raises(bundle.BundleError):
            bundle.validate(store, nc._json(metadata), members)
    finally:
        store.close()


@pytest.mark.parametrize('defect', ['gap', 'tail', 'neighbor'])
def test_coherent_fragment_and_neighbor_defects_refused(tmp_path, defect):
    from slaif_raggedized_helper import bundle_native_records as leaf

    store, _, _, metadata, members = build(tmp_path, tiny_pdf(2))
    try:
        changed = list(members)
        records = [json.loads(x) for x in members[2][1].splitlines()]
        links = [json.loads(x) for x in members[3][1].splitlines()]
        receipts = json.loads(members[4][1])
        if defect == 'neighbor':
            links[0]['next_chunk_id'] = None if links[0]['next_chunk_id'] else 'bogus'
        else:
            i = 0 if defect == 'gap' else len(records) - 1
            record = records[i]
            fragment = next(f for f in record['fragments'] if f['kind'] == 'source')
            assert len(fragment['copied_text']) > 1
            if defect == 'gap':
                fragment['start'] += 1
                fragment['copied_text'] = fragment['copied_text'][1:]
            else:
                fragment['end'] -= 1
                fragment['copied_text'] = fragment['copied_text'][:-1]
            old = record['chunk_id']
            record['text'] = ''.join(f.get('copied_text', f.get('text', ''))
                                     for f in record['fragments'])
            record['text_sha256'] = hashlib.sha256(record['text'].encode()).hexdigest()
            record['chunk_id'] = p.chunk_id(p.admit_record('Chunk', nc._json(record)))
            representation = ''.join(record['heading_path']) + record['text']
            for j, pair in enumerate(((record['text'], None), (representation, None),
                                      (metadata['chunking']['query'], representation))):
                receipts['receipts'][3 * i + j]['chunk_id'] = record['chunk_id']
                receipts['receipts'][3 * i + j]['count']['input_sha256'] = nc._input_digest(*pair)
            for link in links:
                for key in ('chunk_id', 'previous_chunk_id', 'next_chunk_id'):
                    if link[key] == old:
                        link[key] = record['chunk_id']
        changed[2] = ('chunks', b''.join(nc._json(x) + b'\n' for x in records))
        changed[3] = ('neighbors', b''.join(nc._json(x) + b'\n' for x in links))
        changed[4] = ('receipts', nc._json(receipts))
        leaf.validate(nc._json(metadata['chunking']), changed[2][1], changed[4][1], len(records))
        with pytest.raises(bundle.BundleError):
            bundle.validate(store, nc._json(metadata), tuple(changed))
    finally:
        store.close()
