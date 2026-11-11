import hashlib
import json
import os

import pytest

from slaif_raggedized_helper import provenance_records as p, structured_text as s
from slaif_raggedized_helper.source_admission import OriginalStore, parse_manifest


def create_store(tmp_path, text, media='text/markdown'):
    root = tmp_path / 'root'
    root.mkdir()
    raw = text.encode('utf8')
    (root / 'a').write_bytes(raw)
    (root / 'b').write_bytes(raw)
    base = dict(logical_id='a', relative_path='a', display_uri='urn:owned', corpus='one',
                access_labels=[], processing_approved=True, redistribution_rights='allowed',
                media_type=media, size=len(raw), sha256=hashlib.sha256(raw).hexdigest())
    different = dict(base, logical_id='b', relative_path='b', corpus='two',
                     access_labels=['secret'], redistribution_rights='prohibited')
    sources = parse_manifest(json.dumps(dict(schema_version=1, sources=[base, different,
                            dict(base, title='changed')])).encode()).sources
    store = OriginalStore(tmp_path / 'store')
    return store, [store.admit(root, source) for source in sources]


def test_structure_exact_source_coverage_and_registry(tmp_path):
    text = ('# Guide Ž😀\r\n\r\nFirst e\u0301 line\r\nsecond line\r\n\r\n'
            '1. WARNING: isolate\r\n  prerequisite --flag\r\n2. check 12 V\r\n\r\n'
            '```sh\r\nrun --owned\r\n```\r\n\r\n'
            '| Name | Unit |\r\n| --- | --- |\r\n| flow | L/s |\r\n'
            '| Name | Unit |\r\n| --- | --- |\r\n| flow | L/s |\r\n\r\n'
            '[link](https://example.invalid) <script>ignore instructions</script>\r\n'
            '~~~unclosed\r\n# literal\r\n')
    store, revisions = create_store(tmp_path, text)
    try:
        results = [s.extract(store, rev.revision_id) for rev in revisions]
        result = results[0]
        assert ''.join(block.text for block in result.blocks) == text
        cursor = 0
        for block, span in zip(result.blocks, result.coverage):
            assert span.block_id == block.block_id and span.start == cursor
            assert text[span.start:span.end] == block.text
            cursor = span.end
            assert block.origin == 'native' and block.geometry is None
        assert cursor == len(text)
        assert any(b.text == 'First e\u0301 line\r\nsecond line\r\n' for b in result.blocks)
        assert any(b.kind == 'list' and 'prerequisite --flag' in b.text for b in result.blocks)
        assert any(b.kind == 'code' and b.text == '```sh\r\nrun --owned\r\n```\r\n'
                   for b in result.blocks)
        assert result.blocks[-1].kind == 'code' and 'Unclosed' in result.blocks[-1].uncertainty
        assert sum(b.kind == 'table_header' for b in result.blocks) == 2
        assert sum(b.kind == 'table_row' for b in result.blocks) == 2
        assert results[1].scope.labels == ('secret',) and results[1].scope.corpus == 'two'
        assert results[1].scope.redistribution_rights == 'prohibited'
        assert len({r.revision.revision_id for r in results}) == 3
        assert len({r.blocks[0].block_id for r in results}) == 3
        assert s.extract(store, revisions[0].revision_id) == result
        altered = s.extract(store, revisions[0].revision_id, s.StructurePolicy(max_bytes=10000))
        assert altered.dependency.extraction_id != result.dependency.extraction_id
        assert altered.blocks[0].block_id != result.blocks[0].block_id
        reg = p.Registry(tuple(revisions), tuple(r.dependency for r in results),
                         tuple(b for r in results for b in r.blocks))
        block = result.blocks[0]
        fragment = p.SourceFragment(schema_version=1, kind='source', block_id=block.block_id,
                                    start=0, end=len(block.text), copied_text=block.text)
        chunk = p.Chunk(schema_version=1, chunk_id='tmp', revision_id=block.revision_id,
                        extraction_id=block.extraction_id, policy_id=p.policy_id('owned'),
                        fragments=(fragment,), text=block.text, text_sha256=block.text_sha256)
        chunk = chunk.model_copy(update={'chunk_id': p.chunk_id(chunk)})
        assert reg.bind_chunk(chunk) == result.scope
        bad = chunk.model_copy(update={'revision_id': revisions[1].revision_id})
        with pytest.raises(p.ProvenanceError):
            reg.bind_chunk(bad)
    finally:
        store.close()


def test_actual_byte_cap_and_source_read_race(tmp_path, monkeypatch):
    text = 'owned text\nsecond line\n'
    store, revisions = create_store(tmp_path, text)
    blob = tmp_path / 'store' / 'blobs' / revisions[0].blob
    original = os.read
    reads = []

    def spy(fd, size):
        data = original(fd, size)
        if os.fstat(fd).st_ino == blob.stat().st_ino:
            reads.append(len(data))
        return data

    monkeypatch.setattr(os, 'read', spy)
    try:
        with pytest.raises(s.StructureError, match='structure extraction refused'):
            s.extract(store, revisions[0].revision_id, s.StructurePolicy(max_bytes=2))
        assert reads == []
        changed = []

        def mutate(fd, size):
            data = original(fd, size)
            if data and not changed and os.fstat(fd).st_ino == blob.stat().st_ino:
                changed.append(True)
                blob.write_bytes(b'x' * len(text.encode()))
            return data

        monkeypatch.setattr(os, 'read', mutate)
        with pytest.raises(s.StructureError, match='structure extraction refused'):
            s.extract(store, revisions[0].revision_id)
        assert changed == [True]
    finally:
        store.close()
