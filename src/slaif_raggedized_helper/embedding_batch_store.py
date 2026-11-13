"""Bounded typed persistence for declared embedding batches."""

from dataclasses import dataclass
import json
import re

from . import derived_store, embedding_vectors, vector_codec

POLICY = vector_codec.Policy(max_rows=128, max_elements=131072, max_work=131072,
                             max_bytes=530000, max_header=512, deadline_ms=5000,
                             norm_tolerance=0.0001)
_HEX = re.compile(r'[0-9a-f]{64}\Z')
_ROOT = {'schema', 'kind', 'dependencies', 'rows', 'vector_container_sha256',
         'vector_payload_sha256', 'codec_policy_fingerprint'}
_DEPS = {'space_id', 'inventory_id', 'definition_fingerprint', 'execution_fingerprint',
         'tokenizer_sha256', 'representation_policy_fingerprint', 'normalization_policy_id'}
_ROW = {'chunk_id', 'revision_id', 'extraction_id', 'representation_id', 'rendered_sha256',
        'source_scope_sha256', 'input_sha256', 'token_count'}


class BatchError(ValueError):
    """Input-free batch refusal."""


@dataclass(frozen=True)
class ValidatedBatch:
    container_id: str
    metadata: bytes
    row_ids: tuple
    matrix: object


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError
        result[key] = value
    return result


def _reject(_):
    raise ValueError


def _hex(value):
    return type(value) is str and _HEX.fullmatch(value) is not None


def _metadata(data):
    if type(data) is not bytes or not 1 <= len(data) <= 131072:
        raise ValueError
    obj = json.loads(data.decode('utf-8'), object_pairs_hook=_pairs, parse_float=_reject,
                     parse_constant=_reject,
                     parse_int=lambda s: int(s) if len(s) <= 4 else _reject(s))
    if (type(obj) is not dict or set(obj) != _ROOT or type(obj['schema']) is not int
            or obj['schema'] != 1 or obj['kind'] != 'embedding-batch-v1'):
        raise ValueError
    if json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False,
                  allow_nan=False).encode('utf-8') != data:
        raise ValueError
    dep = obj['dependencies']
    if type(dep) is not dict or set(dep) != _DEPS:
        raise ValueError
    if dep['normalization_policy_id'] != embedding_vectors.POLICY_ID:
        raise ValueError
    if not all(_hex(dep[k]) for k in _DEPS - {'normalization_policy_id'}):
        raise ValueError
    if not all(_hex(obj[k]) for k in ('vector_container_sha256', 'vector_payload_sha256',
                                      'codec_policy_fingerprint')):
        raise ValueError
    if obj['codec_policy_fingerprint'] != POLICY.fingerprint():
        raise ValueError
    rows = obj['rows']
    if type(rows) is not list or not 1 <= len(rows) <= 128:
        raise ValueError
    for row in rows:
        if type(row) is not dict or set(row) != _ROW:
            raise ValueError
        for key in ('chunk_id', 'revision_id', 'extraction_id'):
            value = row[key]
            if (type(value) is not str or not 1 <= len(value.encode('utf-8')) <= 71
                    or any(ord(c) < 32 or 127 <= ord(c) <= 159 for c in value)):
                raise ValueError
        if not all(_hex(row[k]) for k in ('representation_id', 'rendered_sha256',
                                          'source_scope_sha256', 'input_sha256')):
            raise ValueError
        if type(row['token_count']) is not int or not 2 <= row['token_count'] <= 1024:
            raise ValueError
    if any(len({r[k] for r in rows}) != len(rows) for k in ('chunk_id', 'representation_id')):
        raise ValueError
    return obj


def _vectors(obj, data):
    if type(data) is not bytes or len(data) > 530000:
        raise ValueError
    result = vector_codec.decode(data, obj['vector_container_sha256'], POLICY)
    if result.payload_sha256 != obj['vector_payload_sha256'] or result.shape[0] != len(obj['rows']):
        raise ValueError
    return result


def load(store, container_id, expected_metadata_json_bytes):
    """Freshly load and validate against the caller's complete current declaration."""
    try:
        obj = _metadata(expected_metadata_json_bytes)
        if type(store) is not derived_store.Store:
            raise ValueError
        snapshot = store.load(container_id)
        # The manifest is canonical and the store validated its integrity.
        manifest = json.loads(snapshot.manifest.decode('utf-8'))
        actual = json.dumps(manifest['metadata'], sort_keys=True, separators=(',', ':'),
                            ensure_ascii=False, allow_nan=False).encode('utf-8')
        if actual != expected_metadata_json_bytes or len(snapshot.members) != 1:
            raise ValueError
        member = snapshot.members[0]
        if member.name != 'vectors':
            raise ValueError
        result = _vectors(obj, member.data)
        ids = tuple((r['chunk_id'], r['revision_id'], r['extraction_id'],
                     r['representation_id']) for r in obj['rows'])
        return ValidatedBatch(container_id, expected_metadata_json_bytes, ids, result.matrix)
    except Exception:
        raise BatchError('batch refused') from None


def publish(store, metadata_json_bytes, vector_container_bytes):
    """Admit, publish, and freshly revalidate an immutable batch."""
    try:
        if type(vector_container_bytes) is not bytes or len(vector_container_bytes) > 530000:
            raise ValueError
        obj = _metadata(metadata_json_bytes)
        if type(store) is not derived_store.Store:
            raise ValueError
        _vectors(obj, vector_container_bytes)
        container_id = store.publish(metadata_json_bytes,
                                     (derived_store.Member('vectors', vector_container_bytes),))
        load(store, container_id, metadata_json_bytes)
        return container_id
    except Exception:
        raise BatchError('batch refused') from None
