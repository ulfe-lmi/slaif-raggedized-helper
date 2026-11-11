import hashlib
import json

import pytest

from slaif_raggedized_helper import structured_text as s
from slaif_raggedized_helper.source_admission import OriginalStore, parse_manifest


def make_store(tmp_path, data, media='text/markdown'):
    root = tmp_path / 'root'
    root.mkdir()
    (root / 'doc').write_bytes(data)
    obj = dict(logical_id='owned', relative_path='doc', display_uri='urn:owned', corpus='c',
               access_labels=[], processing_approved=True, redistribution_rights='unknown',
               media_type=media, size=len(data), sha256=hashlib.sha256(data).hexdigest())
    source = parse_manifest(json.dumps(dict(schema_version=1, sources=[obj])).encode()).sources[0]
    store = OriginalStore(tmp_path / 'store')
    return store, store.admit(root, source)


@pytest.mark.parametrize('fields', [
    {'max_bytes': True}, {'max_chars': float('nan')}, {'max_lines': 0},
    {'max_blocks': 4097}, {'max_block_chars': 200001}, {'max_lines': 1.5},
])
def test_invalid_policy(fields):
    with pytest.raises(s.StructureError, match='invalid structure policy'):
        s.StructurePolicy(**fields)


def test_limits_and_forged_policy_refuse_without_partial(tmp_path):
    store, revision = make_store(tmp_path, b'first line\nsecond line\n\nthird line\n')
    try:
        for policy in (s.StructurePolicy(max_bytes=2), s.StructurePolicy(max_chars=3),
                       s.StructurePolicy(max_lines=2), s.StructurePolicy(max_blocks=1),
                       s.StructurePolicy(max_block_chars=3)):
            with pytest.raises(s.StructureError, match='structure extraction refused'):
                s.extract(store, revision.revision_id, policy)
        forged = s.StructurePolicy()
        object.__setattr__(forged, 'max_lines', True)
        with pytest.raises(s.StructureError, match='invalid structure policy'):
            s.extract(store, revision.revision_id, forged)
    finally:
        store.close()


@pytest.mark.parametrize('name,data,media', [
    ('invalid', b'\xffSECRET_CANARY', 'text/plain'),
    ('pdf', b'%PDF-canary', 'application/pdf'),
])
def test_invalid_media_or_encoding_is_safe(tmp_path, name, data, media):
    store, revision = make_store(tmp_path, data, media)
    try:
        with pytest.raises(s.StructureError, match='structure extraction refused') as error:
            s.extract(store, revision.revision_id)
        assert 'SECRET_CANARY' not in str(error.value) and str(tmp_path) not in str(error.value)
    finally:
        store.close()


def test_corrupt_source_and_cooperative_deadline(tmp_path, monkeypatch):
    store, revision = make_store(tmp_path, b'first\nsecond\n')
    try:
        clock = iter([0.0, 0.0, 0.0, 6.0])
        monkeypatch.setattr(s.time, 'monotonic', lambda: next(clock))
        with pytest.raises(s.StructureError, match='structure extraction refused'):
            s.extract(store, revision.revision_id)
        monkeypatch.undo()
        (tmp_path / 'store' / 'blobs' / revision.blob).write_bytes(b'x' * 13)
        with pytest.raises(s.StructureError, match='structure extraction refused'):
            s.extract(store, revision.revision_id)
    finally:
        store.close()


def test_empty_plain_and_literal_unknown_syntax(tmp_path):
    empty = tmp_path / 'empty'
    empty.mkdir()
    store, revision = make_store(empty, b'', 'text/plain')
    try:
        result = s.extract(store, revision.revision_id)
        assert result.blocks == () and result.coverage == ()
    finally:
        store.close()
    plain = tmp_path / 'plain'
    plain.mkdir()
    store, revision = make_store(plain, b'# literal\nnext line\n\n1. step\n', 'text/plain')
    try:
        result = s.extract(store, revision.revision_id)
        assert [x.kind for x in result.blocks] == ['text', 'text', 'list']
        assert result.blocks[0].text == '# literal\nnext line\n'
        assert 'unsupported Markdown' in result.uncertainty
    finally:
        store.close()
