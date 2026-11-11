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


def test_actual_native_text_bundle(tmp_path):
    paths, runtime, make = make_native(tmp_path)
    defs = (make(paths[0], 'bge_body'), make(paths[0], 'bge_representation'),
            make(paths[1], 'reranker_pair'))
    text = ('# Guide Ž😀\r\n\r\nCafe\u0301 and controls \t.\r\n\r\n'
            'WARNING: check units.\r\n1. Measure 5 kg.\r\n\r\n'
            '| Item | Unit |\r\n| --- | --- |\r\n| Mass | kg |\r\n\r\nTail.\r\n')
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
        valid = bundle.validate(store, nc._json(metadata), members)
        assert valid.chunks == result.chunks
        assert bundle.validate(store, valid.metadata_json, valid.members) == valid
        for bad in (members[::-1], members[:-1], (("bad", members[0][1]), *members[1:])):
            with pytest.raises(bundle.BundleError):
                bundle.validate(store, nc._json(metadata), bad)
        for key, value in [('schema_version', True), ('kind', 'x'), ('extra', 1)]:
            bad = dict(metadata, **{key: value})
            with pytest.raises(bundle.BundleError):
                bundle.validate(store, nc._json(bad), members)
        bad = list(members)
        bad[3] = ('neighbors', b'{}\n')
        with pytest.raises(bundle.BundleError):
            bundle.validate(store, nc._json(metadata), tuple(bad))
        # Coherently rebind a changed source fragment and its native receipts.  The
        # leaf validator accepts these bytes; complete-source composition must refuse.
        records = [json.loads(line) for line in members[2][1].splitlines()]
        candidate = records[0]
        fragment = next(f for f in candidate['fragments'] if f['kind'] == 'source')
        if len(fragment['copied_text']) > 1:
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
            from slaif_raggedized_helper import bundle_native_records as leaf
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
