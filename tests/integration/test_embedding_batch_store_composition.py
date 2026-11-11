import json

import numpy as np
import pytest

from slaif_raggedized_helper import derived_store, embedding_batch_store as batch
from slaif_raggedized_helper import embedding_vectors, vector_codec


def fixture(count):
    raw = np.zeros((count, 1024), dtype='<f4')
    raw[np.arange(count), np.arange(count)] = 2
    normalized = embedding_vectors.normalize_rows(raw.tolist())
    encoded = vector_codec.encode(np.array(normalized.rows, dtype='<f4'), batch.POLICY)
    h = 'a' * 64
    deps = dict.fromkeys(batch._DEPS, h)
    deps['normalization_policy_id'] = embedding_vectors.POLICY_ID
    rows = [{'chunk_id': str(i), 'revision_id': 'r', 'extraction_id': 'e',
             'representation_id': f'{i:064x}', 'rendered_sha256': h,
             'source_scope_sha256': h, 'input_sha256': h, 'token_count': 2}
            for i in range(count)]
    obj = {'schema': 1, 'kind': 'embedding-batch-v1', 'dependencies': deps, 'rows': rows,
           'vector_container_sha256': encoded.container_sha256,
           'vector_payload_sha256': encoded.payload_sha256,
           'codec_policy_fingerprint': batch.POLICY.fingerprint()}
    return obj, encoded


def wire(obj):
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()


@pytest.mark.parametrize('count', [2, 128])
def test_real_store_reopen(tmp_path, count):
    tmp_path.chmod(0o700)
    obj, encoded = fixture(count)
    with derived_store.Store(tmp_path) as store:
        identity = batch.publish(store, wire(obj), encoded.container)
        assert batch.publish(store, wire(obj), encoded.container) == identity
    with derived_store.Store(tmp_path) as store:
        loaded = batch.load(store, identity, wire(obj))
        assert loaded.metadata == wire(obj)
        assert [r[0] for r in loaded.row_ids] == [str(i) for i in range(count)]
        assert np.array_equal(loaded.matrix, encoded.matrix)
        assert np.allclose(np.linalg.norm(loaded.matrix, axis=1), 1)
        assert not loaded.matrix.flags.writeable
        obj['rows'][0]['chunk_id'] = 'different'
        with pytest.raises(batch.BatchError):
            batch.load(store, identity, wire(obj))
    with pytest.raises(batch.BatchError):
        batch.load(store, identity, wire(obj))


def test_opaque_store_invalid_members(tmp_path):
    tmp_path.chmod(0o700)
    obj, encoded = fixture(2)
    with derived_store.Store(tmp_path) as store:
        for members in [(derived_store.Member('vectors', b'bad'),),
                        (derived_store.Member('vectors', encoded.container),
                         derived_store.Member('extra', b'x'))]:
            identity = store.publish(wire(obj), members)
            with pytest.raises(batch.BatchError):
                batch.load(store, identity, wire(obj))


def test_opaque_semantic_mismatch_and_corruption(tmp_path):
    tmp_path.chmod(0o700)
    obj, encoded = fixture(2)
    with derived_store.Store(tmp_path) as store:
        bad = dict(obj)
        bad['unknown'] = 'marker-private'
        identity = store.publish(wire(bad), (derived_store.Member('vectors', encoded.container),))
        with pytest.raises(batch.BatchError) as exc:
            batch.load(store, identity, wire(obj))
        assert 'marker-private' not in str(exc.value)
        bad = dict(obj)
        bad['vector_payload_sha256'] = 'b' * 64
        identity = store.publish(wire(bad), (derived_store.Member('vectors', encoded.container),))
        with pytest.raises(batch.BatchError):
            batch.load(store, identity, wire(bad))
        identity = batch.publish(store, wire(obj), encoded.container)
        object_path = tmp_path / 'derived' / 'v1' / 'objects' / encoded.container_sha256
        object_path.write_bytes(b'corrupt')
        with pytest.raises(batch.BatchError):
            batch.load(store, identity, wire(obj))


def test_publish_readback_failure(tmp_path, monkeypatch):
    tmp_path.chmod(0o700)
    obj, encoded = fixture(2)
    with derived_store.Store(tmp_path) as store:
        def fail(_):
            raise derived_store.StoreError('marker-private')
        monkeypatch.setattr(store, 'load', fail)
        with pytest.raises(batch.BatchError) as exc:
            batch.publish(store, wire(obj), encoded.container)
        assert 'marker-private' not in str(exc.value)


@pytest.mark.parametrize('key', sorted(batch._DEPS))
def test_changed_dependency_refuses(tmp_path, key):
    tmp_path.chmod(0o700)
    obj, encoded = fixture(2)
    with derived_store.Store(tmp_path) as store:
        identity = batch.publish(store, wire(obj), encoded.container)
        obj['dependencies'][key] = 'b' * 64
        with pytest.raises(batch.BatchError):
            batch.load(store, identity, wire(obj))


def test_trace_sanitized(tmp_path, monkeypatch):
    import secrets
    import traceback

    tmp_path.chmod(0o700)
    obj, encoded = fixture(2)
    marker = secrets.token_hex(16)
    with derived_store.Store(tmp_path) as store:
        def fail(_):
            raise derived_store.StoreError(marker)
        monkeypatch.setattr(store, 'load', fail)
        try:
            batch.publish(store, wire(obj), encoded.container)
        except batch.BatchError:
            assert marker not in traceback.format_exc()
        else:
            pytest.fail('expected refusal')
