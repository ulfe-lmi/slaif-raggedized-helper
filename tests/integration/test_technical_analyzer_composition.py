import unicodedata

from slaif_raggedized_helper import chunking as c, provenance_records as p
from slaif_raggedized_helper import structured_text as s, technical_analyzer as a
from test_structured_text_composition import create_store


def test_owned_sources_through_chunk_and_terms(tmp_path):
    text = '# Ž 😀\r\n\r\nWARNING: ne zaženi --no-cache /a/b. e\u0301\r\n'
    store, revisions = create_store(tmp_path, text)
    try:
        items = [s.extract(store, r.revision_id) for r in revisions[:2]]
        assert revisions[0].blob == revisions[1].blob
        assert revisions[0].revision_id != revisions[1].revision_id
        assert items[0].scope.labels != items[1].scope.labels
        assert items[0].scope.redistribution_rights != items[1].scope.redistribution_rights
        reg = p.Registry(tuple(revisions[:2]), tuple(x.dependency for x in items),
                         tuple(b for x in items for b in x.blocks))
        ctr = c.Counters('body', 'rep', 'pair', lambda x: len(x.split()),
                         lambda x: len(x.split()) + 2,
                         lambda q, x: len(q.split()) + len(x.split()) + 3)
        outputs = [c.build(reg, item.blocks, ctr, 'q') for item in items]
        for item, output in zip(items, outputs):
            assert ''.join(b.text for b in item.blocks) == text
            for chunk in output.chunks:
                assert reg.bind_chunk(chunk) == item.scope
                original = chunk.text
                analysis = a.analyze(original)
                assert any(t.text == '--no-cache' for t in analysis.terms)
                for term in analysis.terms:
                    span = original[term.start:term.end]
                    expected = (unicodedata.normalize('NFKC', span).casefold()
                                if 'nfkc' in term.derivation else span)
                    assert term.text == expected
                assert chunk.text == original
                for fragment in chunk.fragments:
                    if isinstance(fragment, p.SourceFragment):
                        block = next(b for b in item.blocks if b.block_id == fragment.block_id)
                        assert fragment.copied_text == block.text[fragment.start:fragment.end]
        assert outputs[0].chunks[0].chunk_id != outputs[1].chunks[0].chunk_id
    finally:
        store.close()
