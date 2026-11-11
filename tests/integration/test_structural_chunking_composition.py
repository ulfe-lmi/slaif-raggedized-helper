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


def test_default_thresholds_and_exact_counter_calls(tmp_path):
    # Each word is one supplied fixture token; specials are deliberately explicit.
    calls = []

    def body(text):
        calls.append(('body', text))
        return len(text.split()) + 2

    def rep(text):
        calls.append(('representation', text))
        return len(text.split()) + 258

    def pair(query, text):
        calls.append(('pair', query, text))
        return len(query.split()) + len(text.split()) + 3

    ctr = c.Counters('fixture-bge', 'fixture-bge', 'fixture-reranker', body, rep, pair)
    for n, expected_chunks in ((510, 1), (511, 2)):
        path = tmp_path / str(n)
        path.mkdir()
        text = ' '.join(['a'] * (n - 1)) + '\n\nb\n'
        store, revisions = create_store(path, text)
        try:
            item = s.extract(store, revisions[0].revision_id)
            reg = p.Registry((item.revision,), (item.dependency,), item.blocks)
            out = c.build(reg, item.blocks, ctr, 'q', c.Policy(pair_max=1100))
            assert len(out.chunks) == expected_chunks
            for ch in out.chunks:
                representation = ''.join(ch.heading_path) + ch.text
                assert ('body', ch.text) in calls
                assert ('representation', representation) in calls
                assert ('pair', 'q', representation) in calls
                assert ('pair', '', representation) in calls
                assert ('pair', 'q', '') in calls
                assert tuple(x.count for x in ch.counts) == (
                    len(ch.text.split()) + 2, len(representation.split()) + 258,
                    len(representation.split()) + 4)
        finally:
            store.close()
    for n in (766, 767):
        path = tmp_path / ('hard' + str(n))
        path.mkdir()
        store, revisions = create_store(path, ' '.join(['x'] * n))
        try:
            item = s.extract(store, revisions[0].revision_id)
            reg = p.Registry((item.revision,), (item.dependency,), item.blocks)
            if n == 766:
                out = c.build(reg, item.blocks, ctr, 'q', c.Policy(pair_max=1100))
                assert tuple(x.count for x in out.chunks[0].counts) == (768, 1024, 770)
            else:
                with pytest.raises(c.ChunkingError, match='^chunk construction refused$'):
                    c.build(reg, item.blocks, ctr, 'q', c.Policy(pair_max=1100))
        finally:
            store.close()


def test_pair_and_query_reserve_exact_specials(tmp_path):
    store, revisions = create_store(tmp_path, 'one two three\n')
    try:
        item = s.extract(store, revisions[0].revision_id)
        reg = p.Registry((item.revision,), (item.dependency,), item.blocks)
        seen = []
        def pair(q, text):
            seen.append((q, text))
            return len(q.split()) + len(text.split()) + 3
        ctr = c.Counters('bge', 'bge', 'reranker', lambda x: len(x.split()) + 2,
                         lambda x: len(x.split()) + 2, pair)
        out = c.build(reg, item.blocks, ctr, 'one two',
                      c.Policy(pair_max=8, query_reserve=5))
        assert out.chunks[0].counts[2].count == 8
        assert ('one two', out.chunks[0].text) in seen and ('one two', '') in seen
        for policy in (c.Policy(pair_max=7, query_reserve=5),
                       c.Policy(pair_max=8, query_reserve=4)):
            with pytest.raises(c.ChunkingError, match='^chunk construction refused$'):
                c.build(reg, item.blocks, ctr, 'one two', policy)
    finally:
        store.close()


def test_multi_warning_priority_and_no_bridging(tmp_path):
    text = ('WARNING: isolate power.\r\n\r\nPrerequisite: use lock.\r\n\r\n'
            '1. perform step --flag\r\n\r\nUnrelated text.\r\n\r\n'
            'WARNING: never bypass.\r\n\r\n1. Stop now\r\n')
    store, revisions = create_store(tmp_path, text)
    try:
        item = s.extract(store, revisions[0].revision_id)
        reg = p.Registry((item.revision,), (item.dependency,), item.blocks)
        ctr = c.Counters('bge', 'bge', 'reranker', lambda x: len(x.split()) + 2,
                         lambda x: len(x.split()) + 2,
                         lambda q, x: len(q.split()) + len(x.split()) + 3)
        out = c.build(reg, item.blocks, ctr, 'q',
                      c.Policy(target=5, soft_max=24, representation_max=30,
                               pair_max=50, query_reserve=8))
        group = next(ch for ch in out.chunks if 'isolate' in ch.text)
        assert all(x in group.text for x in ('Prerequisite', '--flag'))
        assert group.counts[0].count > 5 and 'Unrelated' not in group.text
        assert any('never bypass' in ch.text and 'Stop now' in ch.text for ch in out.chunks)
        assert all(f.copied_text == next(b.text for b in item.blocks if b.block_id == f.block_id)
                   [f.start:f.end] for ch in out.chunks for f in ch.fragments)
        narrow = c.build(reg, item.blocks, ctr, 'q',
                         c.Policy(target=5, soft_max=8, representation_max=30,
                                  pair_max=50, query_reserve=8))
        assert not any('isolate' in ch.text and '--flag' in ch.text for ch in narrow.chunks)
        assert all(any(b.text in ch.text for ch in narrow.chunks) for b in item.blocks if b.text)
    finally:
        store.close()


def test_scope_snapshot_admission_and_fixed_errors(tmp_path):
    store, revisions = create_store(tmp_path, 'first\n\nsecond\n')
    try:
        items = [s.extract(store, r.revision_id) for r in revisions]
        reg = p.Registry(tuple(revisions), tuple(i.dependency for i in items),
                         tuple(b for i in items for b in i.blocks))
        assert items[0].scope.labels != items[1].scope.labels
        invalid = [(items[0].blocks[0], items[1].blocks[-1]),
                   items[0].blocks + (items[0].blocks[0],),
                   items[0].blocks[::-1], items[0].blocks[:-1],
                   (items[0].blocks[0].model_copy(update={'block_id': 'unknown-canary'}),),
                   (items[0].blocks[0].model_copy(update={'text': 'private-canary'}),)]
        for blocks in invalid:
            with pytest.raises(c.ChunkingError, match='^chunk construction refused$'):
                c.build(reg, blocks, counters(), 'private-canary')
        # Invalid snapshots fail at construction, before chunking can receive them.
        with pytest.raises(p.ProvenanceError, match='^invalid provenance registry$'):
            p.Registry((items[0].revision,), (), items[0].blocks)
        with pytest.raises(p.ProvenanceError, match='^invalid provenance registry$'):
            p.Registry((items[0].revision,), (items[0].dependency,),
                       items[0].blocks + (items[0].blocks[0],))
        bad = items[0].blocks[0].model_copy(update={'text': 'private-canary'})
        with pytest.raises(p.ProvenanceError, match='^invalid provenance registry$'):
            p.Registry((items[0].revision,), (items[0].dependency,), (bad,))
    finally:
        store.close()


def test_overlap_table_references_and_neighbor_coverage(tmp_path):
    text = ('# Ž navodila\r\n\r\nOne two three four five six. Seven eight nine ten eleven twelve. '
            'Thirteen fourteen fifteen sixteen seventeen eighteen. '
            'Nineteen twenty twentyone twentytwo.\r\n\r\n'
            '| Name | Unit |\r\n| --- | --- |\r\n| flow | L/s |\r\n'
            '| volt | V |\r\n| current | A |\r\n\r\n'
            '```sh\r\necho --no-delete Ž\r\n```\r\n\r\nTail warning: never erase.\r\n')
    store, revisions = create_store(tmp_path, text)
    try:
        item = s.extract(store, revisions[0].revision_id)
        reg = p.Registry((item.revision,), (item.dependency,), item.blocks)
        ctr = c.Counters('bge', 'bge', 'reranker', lambda x: len(x.split()) + 2,
                         lambda x: len(x.split()) + 2,
                         lambda q, x: len(q.split()) + len(x.split()) + 3)
        policy = c.Policy(target=5, soft_max=20, representation_max=30,
                          pair_max=35, query_reserve=6)
        out = c.build(reg, item.blocks, ctr, 'q', policy)
        assert out == c.build(reg, item.blocks, ctr, 'q', policy)
        assert all(ch.heading_path == ('# Ž navodila\r\n',) for ch in out.chunks)
        for i, link in enumerate(out.neighbors):
            assert link.previous_chunk_id == (out.chunks[i-1].chunk_id if i else None)
            expected_next = out.chunks[i+1].chunk_id if i+1 < len(out.chunks) else None
            assert link.next_chunk_id == expected_next
        fragments = [f for ch in out.chunks for f in ch.fragments]
        for b in item.blocks:
            spans = [f for f in fragments if f.block_id == b.block_id]
            assert all(f.copied_text == b.text[f.start:f.end] for f in spans)
            assert {i for f in spans for i in range(f.start, f.end)} == set(range(len(b.text)))
        para = next(b for b in item.blocks if b.text.startswith('One two'))
        para_spans = [f for f in fragments if f.block_id == para.block_id]
        assert len(para_spans) > 1
        overlaps = [(a, b) for a, b in zip(para_spans, para_spans[1:]) if b.start < a.end]
        assert overlaps
        for a, b in overlaps:
            assert ctr.body(para.text[b.start:min(a.end, b.end)]) <= 64
        header = next(b for b in item.blocks if b.kind == 'table_header')
        rows = {b.block_id for b in item.blocks if b.kind == 'table_row'}
        row_chunks = [ch for ch in out.chunks if any(f.block_id in rows for f in ch.fragments)]
        assert len(row_chunks) > 1
        assert all(any(f.block_id == header.block_id and f.copied_text == header.text
                       for f in ch.fragments) for ch in row_chunks)
        assert '| --- | --- |' in header.text and 'L/s' in text
        code = next(b for b in item.blocks if b.kind == 'code')
        assert sum(f.block_id == code.block_id for f in fragments) == 1
        assert any('never erase' in ch.text for ch in out.chunks)
        for ch in out.chunks:
            assert ch.counts[0].count <= 20 and ch.counts[1].count <= 30
            assert ch.counts[2].count <= 35
    finally:
        store.close()


def test_empty_and_invalid_counter_contracts(tmp_path):
    store, revisions = create_store(tmp_path, '')
    try:
        item = s.extract(store, revisions[0].revision_id)
        assert item.blocks == ()
        reg = p.Registry((item.revision,), (item.dependency,), item.blocks)
        with pytest.raises(c.ChunkingError, match='^chunk construction refused$'):
            c.build(reg, item.blocks, counters(), 'q')
    finally:
        store.close()
    path = tmp_path / 'nonempty'
    path.mkdir()
    store, revisions = create_store(path, 'private-canary\n')
    try:
        item = s.extract(store, revisions[0].revision_id)
        reg = p.Registry((item.revision,), (item.dependency,), item.blocks)
        good = counters()
        for ctr in (c.Counters('', 'b', 'p', good.body, good.representation, good.pair),
                    c.Counters('b', 'b', 'b', good.body, good.representation, good.pair),
                    c.Counters('b', 'b', 'p', None, good.representation, good.pair),
                    c.Counters('b', 'b', 'p', good.body, good.representation, good.pair,
                               'qualified')):
            with pytest.raises(c.ChunkingError, match='^chunk construction refused$'):
                c.build(reg, item.blocks, ctr, 'private-canary')
        for value in (True, -1, float('nan'), float('inf'), 10000001):
            for role in ('representation', 'pair'):
                rep = (lambda _, v=value: v) if role == 'representation' else good.representation
                pair = (lambda _q, _x, v=value: v) if role == 'pair' else good.pair
                with pytest.raises(c.ChunkingError, match='^chunk construction refused$'):
                    c.build(reg, item.blocks, c.Counters('b', 'b', 'p', good.body, rep, pair),
                            'private-canary')
    finally:
        store.close()


def test_representation_limit_and_zero_length_block(tmp_path):
    import hashlib

    store, revisions = create_store(tmp_path, 'x\n')
    try:
        item = s.extract(store, revisions[0].revision_id)
        block = item.blocks[0]
        empty = block.model_copy(update={'block_id': 'empty-owned', 'order': 1, 'text': '',
                                         'text_sha256': hashlib.sha256(b'').hexdigest()})
        reg = p.Registry((item.revision,), (item.dependency,), (block, empty))
        def ctr(rep_count):
            return c.Counters('bge', 'bge', 'independent', lambda _: 1,
                              lambda _: rep_count, lambda _q, _x: 3)
        out = c.build(reg, (block, empty), ctr(1024), 'q')
        assert out.chunks[0].counts[1].count == 1024
        assert out.chunks[0].text == block.text
        with pytest.raises(c.ChunkingError, match='^chunk construction refused$'):
            c.build(reg, (block, empty), ctr(1025), 'q')
        empty_only = p.Registry((item.revision,), (item.dependency,), (empty,))
        with pytest.raises(c.ChunkingError, match='^chunk construction refused$'):
            c.build(empty_only, (empty,), counters(), 'q')
    finally:
        store.close()


def test_cooperative_deadline_refuses_slow_callback(tmp_path):
    import time

    store, revisions = create_store(tmp_path, 'small text\n')
    try:
        item = s.extract(store, revisions[0].revision_id)
        reg = p.Registry((item.revision,), (item.dependency,), item.blocks)
        def slow(text):
            time.sleep(0.01)
            return len(text.split())
        callbacks = c.Counters('body', 'rep', 'pair', slow, slow, lambda q, x: 1)
        with pytest.raises(c.ChunkingError):
            c.build(reg, item.blocks, callbacks, 'q', c.Policy(deadline_ms=1))
    finally:
        store.close()


def test_structural_query_digest_policy_v2(tmp_path):
    import hashlib
    import json

    store, revisions = create_store(tmp_path, 'hello\n')
    try:
        item = s.extract(store, revisions[0].revision_id)
        reg = p.Registry((item.revision,), (item.dependency,), item.blocks)
        ctr = counters()
        policy = c.Policy()
        query = 'é' * 10000
        result = c.build(reg, item.blocks, ctr, query, policy)
        definition = json.dumps(
            {'version': 2, 'policy': policy.__dict__,
             'identities': (ctr.body_identity, ctr.representation_identity, ctr.pair_identity),
             'provenance': ctr.provenance,
             'query_sha256': hashlib.sha256(query.encode('utf-8')).hexdigest()},
            sort_keys=True, ensure_ascii=True, separators=(',', ':'))
        assert all(ch.policy_id == p.policy_id(definition) for ch in result.chunks)
        assert result.chunks[0].policy_id != c.build(
            reg, item.blocks, ctr, 'è' * 10000, policy).chunks[0].policy_id
    finally:
        store.close()
