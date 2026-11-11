import pytest

from slaif_raggedized_helper import chunking as c, provenance_records as p, structured_text as s
from test_structured_text_composition import create_store


def counters():
    return c.Counters('body fixture', 'representation fixture', 'pair fixture',
                      lambda x: len(x.split()), lambda x: len(x.split()) + 2,
                      lambda q, x: len(q.split()) + len(x.split()) + 3)


def test_owned_composition_and_scope(tmp_path):
    text = ('# Navodila Ž\r\n\r\nPrvi stavek. Drugi stavek. Tretji stavek.\r\n\r\n'
            '1. WARNING: ne zaženi\r\n2. prerequisite --ver=2\r\n\r\n'
            '```sh\r\necho Ž\r\n```\r\n\r\n'
            '| Ime | Unit |\r\n| --- | --- |\r\n| A | L/s |\r\n| B | V |\r\n')
    store, revisions = create_store(tmp_path, text)
    try:
        extracted = [s.extract(store, r.revision_id) for r in revisions]
        reg = p.Registry(tuple(revisions), tuple(x.dependency for x in extracted),
                         tuple(b for x in extracted for b in x.blocks))
        policy = c.Policy(target=12, soft_max=18, representation_max=30,
                          pair_max=35, query_reserve=8)
        results = [c.build(reg, x.blocks, counters(), 'query', policy) for x in extracted]
        assert c.build(reg, extracted[0].blocks, counters(), 'query', policy) == results[0]
        assert results[0].chunks[0].chunk_id != results[1].chunks[0].chunk_id
        assert results[0].chunks[0].chunk_id != results[2].chunks[0].chunk_id
        for result, original in zip(results, extracted):
            assert all(reg.bind_chunk(chunk) == original.scope for chunk in result.chunks)
            assert reg.bind_neighbors(result.chunks, result.neighbors) == result.neighbors
            copied = [(f.block_id, f.start, f.end) for ch in result.chunks for f in ch.fragments
                      if isinstance(f, p.SourceFragment)]
            for b in original.blocks:
                covered = set()
                for bid, start, end in copied:
                    if bid == b.block_id:
                        covered.update(range(start, end))
                assert covered == set(range(len(b.text)))
            assert any('Ž' in ch.text for ch in result.chunks)
            assert any(ch.heading_path for ch in result.chunks)
        with pytest.raises(c.ChunkingError, match='chunk construction refused'):
            c.build(reg, extracted[0].blocks[:-1], counters(), 'query', policy)
    finally:
        store.close()


def test_counter_failures_and_bounded_table(tmp_path):
    text = ('| Name | Unit |\n| --- | --- |\n| alpha | V |\n| beta | A |\n'
            '| gamma | L/s |\n\nTail warning. Never remove.\n')
    store, revisions = create_store(tmp_path, text)
    try:
        item = s.extract(store, revisions[0].revision_id)
        reg = p.Registry((item.revision,), (item.dependency,), item.blocks)
        policy = c.Policy(target=8, soft_max=16, representation_max=20,
                          pair_max=25, query_reserve=6)
        result = c.build(reg, item.blocks, counters(), 'q', policy)
        header = next(b for b in item.blocks if b.kind == 'table_header')
        rows = [ch for ch in result.chunks if any(
            isinstance(f, p.SourceFragment) and f.block_id in {
                b.block_id for b in item.blocks if b.kind == 'table_row'} for f in ch.fragments)]
        assert len(rows) >= 2
        assert all(any(isinstance(f, p.SourceFragment) and f.block_id == header.block_id
                       for f in ch.fragments) for ch in rows)
        assert 'Never remove.' in ''.join(ch.text for ch in result.chunks)
        bad = c.Counters('b', 'r', 'p', lambda _: True, lambda _: 1, lambda _q, _p: 1)
        with pytest.raises(c.ChunkingError):
            c.build(reg, item.blocks, bad, 'q', policy)
        too_long_pair = c.Counters('b', 'r', 'p', lambda _: 1, lambda _: 1,
                                   lambda q, passage: 100 if passage else 1)
        with pytest.raises(c.ChunkingError):
            c.build(reg, item.blocks, too_long_pair, 'q', policy)
        with pytest.raises(c.ChunkingError):
            c.build(reg, item.blocks, counters(), 'q', c.Policy(max_calls=1))
        forged = item.blocks[0].model_copy(update={'text': 'canary'})
        with pytest.raises(c.ChunkingError, match='^chunk construction refused$'):
            c.build(reg, (forged,) + item.blocks[1:], counters(), 'q', policy)
    finally:
        store.close()
