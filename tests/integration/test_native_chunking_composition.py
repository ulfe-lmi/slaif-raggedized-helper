import json
import sys
from dataclasses import replace
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'unit'))
from test_native_tokenizers import make_native  # noqa: E402
from test_structured_text_composition import create_store  # noqa: E402

from slaif_raggedized_helper import chunking, native_chunking as nc  # noqa: E402
from slaif_raggedized_helper import provenance_records as p, structured_text as s  # noqa: E402


def test_owned_pipeline_and_invalidation(tmp_path):
    paths, runtime, definition = make_native(tmp_path)
    defs = (definition(paths[0], 'bge_body'), definition(paths[0], 'bge_representation'),
            definition(paths[1], 'reranker_pair'))
    text = ('# Guide Ž😀\r\n\r\nHello café 世界.\r\n\r\nWARNING: isolate power.\r\n'
            '1. Check 12 V.\r\n\r\n| Name | Unit |\r\n| --- | --- |\r\n'
            '| flow | L/s |\r\n\r\nTail warning remains.\r\n')
    store, revs = create_store(tmp_path, text)
    try:
        items = [s.extract(store, rev.revision_id) for rev in revs[:2]]
        reg = p.Registry(tuple(revs[:2]), tuple(x.dependency for x in items),
                         tuple(b for x in items for b in x.blocks))
        before = (tmp_path / 'root' / 'a').read_bytes()
        def run(item, ds=defs, query='hello', policy=None):
            return nc.build(reg, item.blocks, *ds, runtime, query, policy)
        boundary = tuple(replace(d, model_revision='é' * 256, preprocessing='界' * 256)
                         for d in defs)
        assert run(items[0], boundary).chunks
        result = run(items[0])
        assert result == run(items[0])
        assert result.chunks[0].chunk_id != run(items[1]).chunks[0].chunk_id
        assert items[1].scope.labels == ('secret',)
        assert reg.bind_neighbors(result.chunks, result.neighbors) == result.neighbors
        for chunk in result.chunks:
            assert reg.bind_chunk(chunk) == items[0].scope
            receipts = [r for r in result.receipts if r.chunk_id == chunk.chunk_id]
            rep = ''.join(chunk.heading_path) + chunk.text
            assert [r.count.input_sha256 for r in receipts] == [
                nc._input_digest(chunk.text, None), nc._input_digest(rep, None),
                nc._input_digest('hello', rep)]
            assert [r.count.count for r in receipts] == [c.count for c in chunk.counts]
            assert all(c.provenance.startswith('OBSERVED_LOCAL_NATIVE_TOKENIZATION:')
                       for c in chunk.counts)
        assert len(json.loads(result.receipts_json())['receipts']) == 3 * len(result.chunks)
        assert text.encode() == before == (tmp_path / 'root' / 'a').read_bytes()
        for block in items[0].blocks:
            spans = [f for c in result.chunks for f in c.fragments
                     if isinstance(f, p.SourceFragment) and f.block_id == block.block_id]
            assert {i for f in spans for i in range(f.start, f.end)} == set(range(len(block.text)))
        for ds, query, policy in [
            ((replace(defs[0], model_revision='changed'), *defs[1:]), 'hello', None),
            ((replace(defs[0], preprocessing='changed'), *defs[1:]), 'hello', None),
            ((definition(paths[1], 'bge_body'), *defs[1:]), 'hello', None),
            (defs, 'café', None), (defs, 'hello', chunking.Policy(pair_max=1280, target=511)),
            (defs, 'hello', chunking.Policy(pair_max=1280, deadline_ms=9999))]:
            assert result.chunks[0].chunk_id != run(items[0], ds, query, policy).chunks[0].chunk_id
        forged = (items[0].blocks[0].model_copy(update={'text': 'canary-secret'}),
                  *items[0].blocks[1:])
        with pytest.raises(nc.NativeChunkingError, match='^native chunk construction refused$'):
            nc.build(reg, forged, *defs, runtime, 'hello')
        with pytest.raises(nc.NativeChunkingError):
            run(items[0], (replace(defs[0], sha256='0' * 64), *defs[1:]))
    finally:
        store.close()


@pytest.mark.parametrize('field,value', [
    ('role', 'reranker_pair'), ('artifact_sha256', '0' * 64), ('input_sha256', '0' * 64),
    ('backend_version', 'bad'), ('mode', 'pair'), ('model_revision', 'bad'),
    ('preprocessing', 'bad'), ('serialization', 'bad'), ('count', True),
])
def test_corrupt_count_closes_worker(tmp_path, monkeypatch, field, value):
    paths, runtime, definition = make_native(tmp_path)
    defs = (definition(paths[0], 'bge_body'), definition(paths[0], 'bge_representation'),
            definition(paths[1], 'reranker_pair'))
    store, revs = create_store(tmp_path, '# Guide\n\nhello canary-secret\n')
    item = s.extract(store, revs[0].revision_id)
    reg = p.Registry((revs[0],), (item.dependency,), item.blocks)
    original = nc.Session.count
    children = []
    def corrupt(self, *args):
        children.append(self._child)
        return replace(original(self, *args), **{field: value})
    monkeypatch.setattr(nc.Session, 'count', corrupt)
    try:
        with pytest.raises(nc.NativeChunkingError, match='^native chunk construction refused$'):
            nc.build(reg, item.blocks, *defs, runtime, 'hello')
        assert children and all(child.poll() is not None for child in children)
    finally:
        store.close()


def test_policy_and_input_refusals(tmp_path):
    paths, runtime, definition = make_native(tmp_path)
    defs = (definition(paths[0], 'bge_body'), definition(paths[0], 'bge_representation'),
            definition(paths[1], 'reranker_pair'))
    store, revs = create_store(tmp_path, 'hello café 世界\n')
    try:
        item = s.extract(store, revs[0].revision_id)
        reg = p.Registry((revs[0],), (item.dependency,), item.blocks)
        good = nc.build(reg, item.blocks, *defs, runtime, 'hello')
        pair_count = good.chunks[0].counts[2].count
        exact = chunking.Policy(pair_max=pair_count, query_reserve=5)
        assert nc.build(reg, item.blocks, *defs, runtime, 'hello', exact).chunks
        with pytest.raises(nc.NativeChunkingError):
            nc.build(reg, item.blocks, *defs, runtime, 'hello',
                     chunking.Policy(pair_max=pair_count - 1, query_reserve=5))
        for query in ('\ud800', 'x' * 10001, True):
            with pytest.raises(nc.NativeChunkingError):
                nc.build(reg, item.blocks, *defs, runtime, query)
        for blocks in ([], (), item.blocks + item.blocks):
            with pytest.raises(nc.NativeChunkingError):
                nc.build(reg, blocks, *defs, runtime, 'hello')
        with pytest.raises(nc.NativeChunkingError):
            nc.build(reg, item.blocks, *defs, runtime, 'hello',
                     chunking.Policy(max_calls=1))
    finally:
        store.close()


@pytest.mark.parametrize('kind', ['procedure', 'table'])
def test_representative_native_documents(tmp_path, monkeypatch, kind):
    from slaif_raggedized_helper import native_tokenizers as native

    paths, runtime, definition = make_native(tmp_path)
    defs = (definition(paths[0], 'bge_body'), definition(paths[0], 'bge_representation'),
            definition(paths[1], 'reranker_pair'))
    if kind == 'procedure':
        text = ('# Procedure\n\n' + ''.join(
            f'WARNING {i}: isolate power before service.\n\n1. Check pressure {i} kPa.\n'
            '2. If hot, wait until safe.\n\n' for i in range(80))
            + 'Tail: restore power only after inspection.\n')
    else:
        text = ('# Measurements\n\n' + ''.join(
            '| Parameter | Value | Unit | Condition |\n| --- | --- | --- | --- |\n' + ''.join(
                f'| flow {i}-{k} | {k} | L/s | if valve open |\n' for k in range(8)) + '\n'
            for i in range(24)) + 'Tail: confirm units.\n')
    store, revs = create_store(tmp_path, text)
    observed = []
    original = nc.Session.count

    def count(self, role, text, pair=None):
        observed.append((role, text, pair))
        return original(self, role, text, pair)

    monkeypatch.setattr(nc.Session, 'count', count)
    try:
        item = s.extract(store, revs[0].revision_id)
        reg = p.Registry((revs[0],), (item.dependency,), item.blocks)
        before = (tmp_path / 'root' / 'a').read_bytes()
        result = nc.build(reg, item.blocks, *defs, runtime, 'hello')
        first_calls = tuple(observed)
        assert 1024 < len(first_calls) < 8192
        assert len(first_calls) == len(set(first_calls))
        assert result == nc.build(reg, item.blocks, *defs, runtime, 'hello')
        assert tuple(observed[len(first_calls):]) == first_calls
        assert len(result.receipts) == 3 * len(result.chunks)
        assert reg.bind_neighbors(result.chunks, result.neighbors) == result.neighbors
        assert 'Tail:' in result.chunks[-1].text
        for block in item.blocks:
            spans = [f for c in result.chunks for f in c.fragments
                     if isinstance(f, p.SourceFragment) and f.block_id == block.block_id]
            assert {i for f in spans for i in range(f.start, f.end)} == set(range(len(block.text)))
        for chunk in (result.chunks[0], result.chunks[len(result.chunks) // 2], result.chunks[-1]):
            rep = ''.join(chunk.heading_path) + chunk.text
            expected = (native.count(defs[0], runtime, chunk.text),
                        native.count(defs[1], runtime, rep),
                        native.count(defs[2], runtime, 'hello', rep))
            receipts = [r.count for r in result.receipts if r.chunk_id == chunk.chunk_id]
            assert tuple(receipts) == expected
            assert chunk.counts[0].count <= 768
            assert chunk.counts[1].count <= 1024
            assert chunk.counts[2].count <= 1280
        assert (tmp_path / 'root' / 'a').read_bytes() == before == text.encode()
    finally:
        store.close()
