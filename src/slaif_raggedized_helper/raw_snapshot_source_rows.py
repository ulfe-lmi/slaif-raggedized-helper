"""Fresh source and stored-vector correspondence for one declared group."""

from dataclasses import asdict, dataclass
import hashlib
import json
import re
import time

from . import derived_store, embedding_batch_store, ingestion_store, raw_snapshot_rows
from . import retrieval_representation, schema
from .source_admission import OriginalStore


class SourceRowsError(ValueError):
    """Content-free refusal of a group."""


@dataclass(frozen=True, slots=True)
class BoundRow:
    declaration: raw_snapshot_rows.Row
    chunk_bytes: bytes
    source_bytes: bytes
    scope_bytes: bytes
    rendered_text: str


@dataclass(frozen=True, slots=True)
class BoundGroup:
    row_map_sha256: str
    bundle_container_id: str
    batch_container_id: str
    bundle_metadata: bytes
    batch_metadata: bytes
    rows: tuple[BoundRow, ...]
    vector_payload: bytes
    payload_sha256: str
    normalization_policy_id: str


def _canonical(obj):
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(',', ':'),
                      allow_nan=False).encode('utf-8')


def _digest(data):
    return hashlib.sha256(data).hexdigest()


def _check(condition):
    if not condition:
        raise ValueError


def _corresponds(row, actual):
    return all(getattr(row, key) == actual[key] for key in (
        'chunk_id', 'revision_id', 'extraction_id', 'representation_id',
        'rendered_sha256', 'source_scope_sha256', 'input_sha256', 'token_count'))


def load_group(originals, derived, row_map_bytes, bundle_container_id, batch_container_id):
    """Freshly bind one group; returned data is not an authorization or neural proof."""
    try:
        return _load_group(originals, derived, row_map_bytes, bundle_container_id,
                           batch_container_id)
    except Exception:
        raise SourceRowsError('source rows refused') from None


def _load_group(originals, derived, row_map_bytes, bundle_id, batch_id):
    end = time.monotonic() + 30

    def check_time():
        _check(time.monotonic() < end)

    _check(type(originals) is OriginalStore and type(derived) is derived_store.Store)
    _check(type(row_map_bytes) is bytes)
    for ident in (bundle_id, batch_id):
        _check(type(ident) is str and re.fullmatch(r'[0-9a-f]{64}', ident) is not None)
    parsed = raw_snapshot_rows.parse(row_map_bytes)
    policy = retrieval_representation.Policy()
    batch_policy = retrieval_representation.BatchPolicy()
    policy_hash = schema.fingerprint(dict(kind='embedding-representation-policy-v1',
                                          policy=asdict(policy),
                                          batch_policy=asdict(batch_policy)))[7:]
    _check(parsed.representation_policy_fingerprint == policy_hash)
    rows = tuple(r for r in parsed.rows if r.bundle_container_id == bundle_id
                 and r.batch_container_id == batch_id)
    _check(1 <= len(rows) <= 128)
    check_time()
    bundle = ingestion_store.load(originals, derived, bundle_id)
    check_time()
    _check(all(r.bundle_metadata_sha256 == _digest(bundle.metadata_json) for r in rows))
    snapshot = derived.load(batch_id)
    check_time()
    manifest = derived_store._parse(snapshot.manifest)
    batch_metadata = derived_store._encode(manifest['metadata'])
    _check(all(r.batch_metadata_sha256 == _digest(batch_metadata) for r in rows))
    batch = embedding_batch_store.load(derived, batch_id, batch_metadata)
    check_time()
    obj = embedding_batch_store._metadata(batch_metadata)
    deps = obj['dependencies']
    _check(deps['space_id'] == parsed.space_id
           and 'sha256:' + deps['definition_fingerprint'] == parsed.definition_fingerprint
           and deps['representation_policy_fingerprint'] == policy_hash
           and deps['normalization_policy_id'] == parsed.normalization_policy_id)
    metadata = json.loads(bundle.metadata_json)
    definitions = [d for d in metadata['chunking']['definitions']
                   if d['role'] == 'bge_representation']
    _check(len(definitions) == 1 and definitions[0]['artifact_sha256'] == deps['tokenizer_sha256'])
    source = bundle.revision.source.model_dump(mode='json')
    scope = bundle.scope.model_dump(mode='json')
    source_bytes, scope_bytes = _canonical(source), _canonical(scope)
    scope_hash = schema.fingerprint(dict(kind='embedding-source-scope-v1', scope=scope))[7:]
    partition = schema.fingerprint(dict(schema=1, corpus=scope['corpus'],
                                        version=scope['version'], labels=scope['labels']))
    chunks = {c.chunk_id: c for c in bundle.chunks}
    _check(len(chunks) == len(bundle.chunks))
    selected, vectors = [], []
    total_chars = total_wire = total_output = 0
    for row in rows:
        check_time()
        chunk = chunks[row.chunk_id]
        _check(chunk.revision_id == row.revision_id == bundle.revision.revision_id
               and chunk.extraction_id == row.extraction_id == bundle.dependency.extraction_id
               and chunk.policy_id == 'sha256:' + parsed.chunk_policy_fingerprint
               and row.partition_id == partition and row.source_scope_sha256 == scope_hash
               and row.execution_fingerprint == deps['execution_fingerprint'])
        components = [bundle.revision.source.title, *chunk.heading_path, chunk.text]
        _check((components[0] is None or type(components[0]) is str)
               and all(type(c) is str for c in components[1:]))
        text = policy.separator.join([c for c in components[:-1] if c] + [components[-1]])
        encoded = text.encode('utf-8', errors='strict')
        wire = json.dumps(dict(text=text, pair=None, nonce='0' * 32,
                               role='bge_representation', artifact=0), ensure_ascii=True,
                          separators=(',', ':')).encode('ascii') + b'\n'
        total_chars += len(text)
        total_wire += len(wire)
        _check(len(text) <= 100000 and len(wire) <= 200000 and total_chars <= 1000000
               and total_wire <= 4000000)
        rendered = _digest(encoded)
        input_hash = _digest(json.dumps([text, None], ensure_ascii=True,
                                        separators=(',', ':')).encode('ascii'))
        identity = dict(revision_id=row.revision_id, extraction_id=row.extraction_id,
                        chunk_id=row.chunk_id, source=source, scope=scope, variant='raw',
                        policy=asdict(policy), rendered_sha256=rendered)
        representation = _digest(json.dumps(identity, sort_keys=True, ensure_ascii=True,
                                             separators=(',', ':')).encode('ascii'))
        _check((row.rendered_sha256, row.input_sha256, row.representation_id)
               == (rendered, input_hash, representation))
        _check(row.batch_row < len(obj['rows']) and _corresponds(row, obj['rows'][row.batch_row]))
        chunk_bytes = _canonical(chunk.model_dump(mode='json'))
        total_output += len(encoded) + len(chunk_bytes) + len(source_bytes) + len(scope_bytes)
        _check(total_output <= 16 * 1048576)
        selected.append(BoundRow(row, chunk_bytes, source_bytes, scope_bytes, text))
        vectors.append(batch.matrix[row.batch_row].tobytes(order='C'))
    payload = b''.join(vectors)
    _check(len(payload) == len(rows) * 1024 * 4)
    check_time()
    return BoundGroup(_digest(row_map_bytes), bundle_id, batch_id, bundle.metadata_json,
                      batch_metadata, tuple(selected), payload, _digest(payload),
                      parsed.normalization_policy_id)
