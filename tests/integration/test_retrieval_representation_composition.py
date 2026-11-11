import hashlib
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


def test_representation_native_composition(tmp_path):
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
        from slaif_raggedized_helper import retrieval_representation as rr
        c = valid.chunks[0]
        value = rr.build(store, nc._json(metadata), members, c.chunk_id, defs[1], runtime)
        expected = "\n\n".join(
            [x for x in [revisions[0].source.title, *c.heading_path] if x] + [c.text])
        assert value.text == expected
        assert value.rendered_sha256 == hashlib.sha256(expected.encode()).hexdigest()
        assert value.count.input_sha256 == nc._input_digest(expected, None)
        assert value.scope == valid.scope
        assert value == rr.build(store, nc._json(metadata), members, c.chunk_id, defs[1], runtime)
        with pytest.raises(rr.RepresentationError):
            rr.build(store, nc._json(metadata), members, 'wrong', defs[1], runtime)
        with pytest.raises(rr.RepresentationError):
            rr.build(store, nc._json(metadata), members, c.chunk_id, defs[0], runtime)
        with pytest.raises(rr.RepresentationError):
            rr.build(store, nc._json(metadata), members[::-1], c.chunk_id, defs[1], runtime)
        with pytest.raises(rr.RepresentationError):
            rr.build(store, nc._json(metadata), members, c.chunk_id, defs[1], runtime,
                     rr.Policy(max_tokens=1))
        lower = rr.build(store, nc._json(metadata), members, c.chunk_id, defs[1], runtime,
                         rr.Policy(max_tokens=value.count.count))
        assert lower.representation_id != value.representation_id
        bad_definition = defs[1].__class__(defs[1].artifact, '0' * 64, '0.21.4',
                                           'bge_representation', 'revision', 'raw')
        with pytest.raises(rr.RepresentationError):
            rr.build(store, nc._json(metadata), members, c.chunk_id, bad_definition, runtime)
    finally:
        store.close()
