"""Actual isolated native counts flow through chunk construction and bindings."""
import sys
from functools import lru_cache
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'unit'))

from test_native_tokenizers import make_native  # noqa: E402
from test_structured_text_composition import create_store  # noqa: E402

from slaif_raggedized_helper import chunking, provenance_records as p, structured_text as s  # noqa: E402
from slaif_raggedized_helper import native_tokenizers as n  # noqa: E402


def test_independent_callbacks_build_and_bind(tmp_path):
    paths, runtime, definition = make_native(tmp_path)
    body = definition(paths[0], 'bge_body')
    representation = definition(paths[0], 'bge_representation')
    pair = definition(paths[1], 'reranker_pair')
    policy = n.Policy(wall_seconds=2)
    calls = []

    @lru_cache(maxsize=32)
    def single(d, text):
        result = n.count(d, runtime, text, policy=policy)
        calls.append((d.role, text, result.count))
        return result.count

    @lru_cache(maxsize=32)
    def paired(query, text):
        result = n.count(pair, runtime, query, text, policy=policy)
        calls.append((pair.role, (query, text), result.count))
        return result.count

    counters = chunking.Counters('body', 'representation', 'pair',
                                lambda text: single(body, text),
                                lambda text: single(representation, text), paired)
    assert counters.provenance == 'SUPPLIED_UNVERIFIED'
    store, revisions = create_store(tmp_path, 'hello café 世界. Tail remains.\n')
    try:
        item = s.extract(store, revisions[0].revision_id)
        registry = p.Registry((item.revision,), (item.dependency,), item.blocks)
        result = chunking.build(registry, item.blocks, counters, 'hello')
        assert result.chunks
        assert {x[0] for x in calls} == {'bge_body', 'bge_representation', 'reranker_pair'}
        for chunk in result.chunks:
            assert registry.bind_chunk(chunk) == item.scope
            representation_text = ''.join(chunk.heading_path) + chunk.text
            assert tuple(x.count for x in chunk.counts) == (
                single(body, chunk.text), single(representation, representation_text),
                paired('hello', representation_text))
            assert all(count.provenance.startswith('SUPPLIED_UNVERIFIED:')
                       for count in chunk.counts)
        assert registry.bind_neighbors(result.chunks, result.neighbors) == result.neighbors
        for block in item.blocks:
            fragments = [f for ch in result.chunks for f in ch.fragments
                         if isinstance(f, p.SourceFragment) and f.block_id == block.block_id]
            covered = {i for f in fragments for i in range(f.start, f.end)}
            assert covered == set(range(len(block.text)))
            assert all(f.copied_text == block.text[f.start:f.end] for f in fragments)
        assert 'Tail remains.' in ''.join(ch.text for ch in result.chunks)
    finally:
        store.close()
