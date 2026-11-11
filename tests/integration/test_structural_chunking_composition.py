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


def test_priority_overlap_and_identity(tmp_path):
    text = ('WARNING: isolate power.\n\n1. perform step --flag\n\n'
            'One two three four. Five six seven eight. Nine ten eleven twelve.\n')
    store, revisions = create_store(tmp_path, text)
    try:
        item = s.extract(store, revisions[0].revision_id)
        reg = p.Registry((item.revision,), (item.dependency,), item.blocks)
        ctr = c.Counters('same', 'same', 'independent', lambda x: len(x.split()) + 2,
                         lambda x: len(x.split()) + 2,
                         lambda q, x: len(q.split()) + len(x.split()) + 3)
        policy = c.Policy(target=5, soft_max=12, representation_max=30,
                          pair_max=50, query_reserve=8)
        out = c.build(reg, item.blocks, ctr, 'q', policy)
        assert any('WARNING' in ch.text and '--flag' in ch.text for ch in out.chunks)
        narrow = c.Policy(target=5, soft_max=7, representation_max=30,
                          pair_max=50, query_reserve=8)
        out = c.build(reg, item.blocks, ctr, 'q', narrow)
        spans = [(f.block_id, f.start, f.end) for ch in out.chunks for f in ch.fragments
                 if isinstance(f, p.SourceFragment)]
        assert any(a[0] == b[0] and a[1] < b[1] < a[2] <= b[2]
                   for a in spans for b in spans)
        for ch in out.chunks:
            assert ch.counts[0].count <= 7 and ch.counts[1].count <= 30
            assert ch.counts[2].count <= 50
        for block in item.blocks:
            assert {i for bid, start, end in spans if bid == block.block_id
                    for i in range(start, end)} == set(range(len(block.text)))
        with pytest.raises(c.ChunkingError):
            c.build(reg, item.blocks, c.Counters('same', 'same', 'same',
                    ctr.body, ctr.representation, ctr.pair), 'q', policy)
    finally:
        store.close()


def test_limits_counter_validation_and_code(tmp_path, monkeypatch):
    store, revisions = create_store(tmp_path, '```sh\necho Ž --no-delete\n```\n\nTail warning.\n')
    try:
        item = s.extract(store, revisions[0].revision_id)
        reg = p.Registry((item.revision,), (item.dependency,), item.blocks)
        good = counters()
        out = c.build(reg, item.blocks, good, 'q')
        assert any('```sh\necho Ž --no-delete\n```' in ch.text for ch in out.chunks)
        assert any('Tail warning.' in ch.text for ch in out.chunks)
        for bad_value in (True, -1, float('nan'), float('inf'), 10000001, '3'):
            bad = c.Counters('b', 'b', 'p', lambda _, v=bad_value: v,
                             good.representation, good.pair)
            with pytest.raises(c.ChunkingError, match='^chunk construction refused$'):
                c.build(reg, item.blocks, bad, 'private canary')
        for policy in (c.Policy(max_blocks=1), c.Policy(max_chars=1),
                       c.Policy(max_calls=1), c.Policy(max_work_chars=1),
                       c.Policy(target=1, soft_max=1, representation_max=1,
                                pair_max=8, query_reserve=4)):
            with pytest.raises(c.ChunkingError):
                c.build(reg, item.blocks, good, 'q', policy)
        bad_pair = c.Counters('b', 'b', 'p', good.body, good.representation,
                              lambda q, x: 1 if q and x else 2)
        with pytest.raises(c.ChunkingError):
            c.build(reg, item.blocks, bad_pair, 'q')
        ticks = iter([0, 6])
        monkeypatch.setattr(c.time, 'monotonic', lambda: next(ticks, 6))
        with pytest.raises(c.ChunkingError):
            c.build(reg, item.blocks, good, 'q')
    finally:
        store.close()


def test_exact_limits_and_pair_are_independent(tmp_path):
    store, revisions = create_store(tmp_path, 'one two three\n')
    try:
        item = s.extract(store, revisions[0].revision_id)
        reg = p.Registry((item.revision,), (item.dependency,), item.blocks)
        ctr = c.Counters('b', 'b', 'r', lambda x: len(x.split()),
                         lambda x: len(x.split()) + 1,
                         lambda q, x: len(q.split()) + len(x.split()) + 2)
        policy = c.Policy(target=3, soft_max=3, representation_max=4,
                          pair_max=6, query_reserve=3)
        out = c.build(reg, item.blocks, ctr, 'q', policy)
        assert tuple(n.count for n in out.chunks[0].counts) == (3, 4, 6)
        with pytest.raises(c.ChunkingError):
            c.build(reg, item.blocks, ctr, 'q',
                    c.Policy(target=2, soft_max=2, representation_max=4,
                             pair_max=6, query_reserve=3))
        with pytest.raises(c.ChunkingError):
            c.build(reg, item.blocks, ctr, 'q',
                    c.Policy(target=3, soft_max=3, representation_max=4,
                             pair_max=5, query_reserve=3))
    finally:
        store.close()


def test_chunk_cap_and_inconsistent_counter(tmp_path):
    store, revisions = create_store(tmp_path, 'First sentence.\n\nSecond sentence.\n')
    try:
        item = s.extract(store, revisions[0].revision_id)
        reg = p.Registry((item.revision,), (item.dependency,), item.blocks)
        with pytest.raises(c.ChunkingError):
            c.build(reg, item.blocks, counters(), 'q',
                    c.Policy(target=1, soft_max=3, representation_max=10,
                             pair_max=15, query_reserve=5, max_chunks=1))
        calls = {}

        def changing(text):
            calls[text] = calls.get(text, 0) + 1
            return calls[text]

        good = counters()
        bad = c.Counters('b', 'b', 'p', changing, good.representation, good.pair)
        with pytest.raises(c.ChunkingError):
            c.build(reg, item.blocks, bad, 'q')
    finally:
        store.close()


def test_fragment_limit_and_default_boundaries(tmp_path):
    text = ''.join('x\n\n' for _ in range(130))
    store, revisions = create_store(tmp_path, text)
    try:
        item = s.extract(store, revisions[0].revision_id)
        reg = p.Registry((item.revision,), (item.dependency,), item.blocks)
        zero = c.Counters('b', 'b', 'p', lambda _: 1, lambda _: 1, lambda _q, _x: 1)
        with pytest.raises(c.ChunkingError):
            c.build(reg, item.blocks, zero, 'q')
    finally:
        store.close()
    other = tmp_path / 'boundary'
    other.mkdir()
    store, revisions = create_store(other, ' '.join(['word'] * 768))
    try:
        item = s.extract(store, revisions[0].revision_id)
        reg = p.Registry((item.revision,), (item.dependency,), item.blocks)
        ctr = c.Counters('b', 'b', 'p', lambda x: len(x.split()),
                         lambda x: len(x.split()) + 256,
                         lambda q, x: len(x.split()) + len(q.split()) + 1)
        policy = c.Policy(pair_max=1000)
        result = c.build(reg, item.blocks, ctr, 'q', policy)
        assert result.chunks[0].counts[0].count == 768
        assert result.chunks[0].counts[1].count == 1024
        with pytest.raises(c.ChunkingError):
            c.build(reg, item.blocks, ctr, 'q',
                    c.Policy(soft_max=767, target=512, pair_max=1000))
    finally:
        store.close()
