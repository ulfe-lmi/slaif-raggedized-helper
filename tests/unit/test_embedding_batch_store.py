import copy
import json

import numpy as np
import pytest

from slaif_raggedized_helper import embedding_batch_store as batch
from slaif_raggedized_helper import derived_store, embedding_vectors, vector_codec


def fixture(count=2):
    raw = np.zeros((count, 1024), dtype='<f4')
    raw[:, 0] = 2
    normalized = embedding_vectors.normalize_rows(raw.tolist())
    encoded = vector_codec.encode(np.array(normalized.rows, dtype='<f4'), batch.POLICY)
    h = 'a' * 64
    metadata = {'schema': 1, 'kind': 'embedding-batch-v1',
                'dependencies': dict.fromkeys(batch._DEPS, h),
                'rows': [], 'vector_container_sha256': encoded.container_sha256,
                'vector_payload_sha256': encoded.payload_sha256,
                'codec_policy_fingerprint': batch.POLICY.fingerprint()}
    metadata['dependencies']['normalization_policy_id'] = embedding_vectors.POLICY_ID
    for i in range(count):
        metadata['rows'].append({'chunk_id': str(i), 'revision_id': 'r', 'extraction_id': 'e',
                                 'representation_id': f'{i:064x}', 'rendered_sha256': h,
                                 'source_scope_sha256': h, 'input_sha256': h, 'token_count': 2})
    return metadata, encoded


def wire(obj):
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()


@pytest.fixture
def spy(tmp_path, monkeypatch):
    tmp_path.chmod(0o700)
    store = derived_store.Store(tmp_path)
    obj, vectors = fixture()
    identity = batch.publish(store, wire(obj), vectors.container)
    assert batch.load(store, identity, wire(obj)).row_ids
    def fail(*args):
        pytest.fail('unexpected store I/O')
    monkeypatch.setattr(store, 'publish', fail)
    monkeypatch.setattr(store, 'load', fail)
    yield store
    store.close()


@pytest.mark.parametrize('mutation', ['late', 'duplicate', 'count', 'unknown', 'bool', 'hash'])
def test_invalid_metadata_before_io(mutation, spy):
    obj, vectors = fixture()
    obj = copy.deepcopy(obj)
    if mutation == 'late':
        obj['rows'][-1]['chunk_id'] = '\x00'
    elif mutation == 'duplicate':
        obj['rows'][-1]['chunk_id'] = obj['rows'][0]['chunk_id']
    elif mutation == 'count':
        obj['rows'] *= 65
    elif mutation == 'unknown':
        obj['extra'] = 1
    elif mutation == 'bool':
        obj['rows'][-1]['token_count'] = True
    else:
        obj['vector_payload_sha256'] = 'b' * 64
    with pytest.raises(batch.BatchError):
        batch.publish(spy, wire(obj), vectors.container)
    if mutation != 'hash':
        with pytest.raises(batch.BatchError):
            batch.load(spy, 'a' * 64, wire(obj))


@pytest.mark.parametrize('data', [b'{}', b'{"x":1,"x":2}', b'{"x":NaN}', b'\xff\xfe{\x00',
                                  b'"\\ud800"', b' ' * 131073])
def test_bad_syntax_before_io(data, spy):
    with pytest.raises(batch.BatchError):
        batch.publish(spy, data, b'')
    with pytest.raises(batch.BatchError):
        batch.load(spy, 'a' * 64, data)


def test_oversized_vectors_before_io(spy):
    obj, _ = fixture()
    with pytest.raises(batch.BatchError):
        batch.publish(spy, wire(obj), b'x' * 530001)


def test_representation_duplicate_and_surrogate(spy):
    obj, encoded = fixture()
    obj['rows'][1]['representation_id'] = obj['rows'][0]['representation_id']
    with pytest.raises(batch.BatchError):
        batch.publish(spy, wire(obj), encoded.container)
    obj['rows'][1]['representation_id'] = 'b' * 64
    obj['rows'][1]['chunk_id'] = '\ud800'
    data = json.dumps(obj, sort_keys=True, separators=(',', ':')).encode()
    with pytest.raises(batch.BatchError):
        batch.publish(spy, data, encoded.container)


def test_forged_store_refused():
    from types import SimpleNamespace

    obj, encoded = fixture()
    fake = SimpleNamespace(load=lambda _: SimpleNamespace(
        manifest=wire({'metadata': obj}),
        members=(derived_store.Member('vectors', encoded.container),)))
    with pytest.raises(batch.BatchError):
        batch.load(fake, 'c' * 64, wire(obj))
