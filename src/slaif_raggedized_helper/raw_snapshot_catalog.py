"""Immutable, original-backed conversion of one explicitly named raw snapshot."""

from dataclasses import asdict, dataclass
import hashlib
import json
import re
import time
import unicodedata

from . import derived_store, ingestion_store, provenance_records, raw_snapshot_dense
from . import raw_snapshot_directory, raw_snapshot_source_rows
from .source_admission import OriginalStore


class CatalogError(ValueError):
    """Content-free catalog refusal."""


@dataclass(frozen=True, slots=True)
class CatalogRow:
    declaration_bytes: bytes
    chunk_bytes: bytes
    source_bytes: bytes
    scope_bytes: bytes
    rendered_bytes: bytes
    representation_id: str
    vector_bytes: bytes
    terms: tuple[tuple[str, int, int, str], ...]


@dataclass(frozen=True, slots=True)
class Catalog:
    snapshot_id: str
    core_bytes: bytes
    row_map_bytes: bytes
    revisions: tuple[bytes, ...]
    dependencies: tuple[bytes, ...]
    blocks: tuple[bytes, ...]
    rows: tuple[CatalogRow, ...]
    catalog_id: str


def _json(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'),
                      allow_nan=False).encode('utf-8')


def _digest(value):
    return hashlib.sha256(value).hexdigest()


def _check(value):
    if not value:
        raise ValueError


class _Budget:
    def __init__(self):
        self.total = 0

    def retain(self, data):
        self.total += len(data)
        _check(self.total <= 32 * 1048576)
        return data


def _insert(table, key, value, limit, budget):
    data = _json(value.model_dump(mode='json'))
    if key in table:
        _check(table[key][0] == data)
    else:
        _check(len(table) < limit)
        table[key] = (budget.retain(data), value)


def load_catalog(originals, derived, store_root, snapshot_id, *, deadline_ms=120000):
    """Load DATA, borrowing both stores; this does not establish query authority."""
    try:
        return _load(originals, derived, store_root, snapshot_id, deadline_ms)
    except Exception:
        raise CatalogError('catalog refused') from None


def _load(originals, derived, root, snapshot_id, deadline_ms):
    _check(type(originals) is OriginalStore and type(derived) is derived_store.Store)
    _check(type(root) is str and root.startswith('/') and root != '/'
           and len(root.encode('utf-8')) <= 4096
           and all(unicodedata.category(c) != 'Cc' for c in root)
           and all(p not in ('', '.', '..') for p in root[1:].split('/')))
    _check(type(snapshot_id) is str and re.fullmatch(r'sha256:[0-9a-f]{64}', snapshot_id))
    _check(type(deadline_ms) is int and 1 <= deadline_ms <= 120000)
    end = time.monotonic() + deadline_ms / 1000

    def deadline():
        _check(time.monotonic() < end)

    budget = _Budget()
    retain = budget.retain

    deadline()
    snapshot = raw_snapshot_directory.load_directory(originals, derived, root, snapshot_id)
    deadline()
    _check(snapshot.snapshot_id == snapshot_id)
    mapping = snapshot.row_map
    _check(len(mapping.rows) <= 4096 and len(snapshot.partitions) <= 128)
    groups = sorted({(r.bundle_container_id, r.batch_container_id) for r in mapping.rows})
    bundles = sorted({r.bundle_container_id for r in mapping.rows})
    _check(len(groups) <= 128 and len(bundles) <= 128)
    core = retain(snapshot.core_bytes)
    map_bytes = retain(mapping.map_bytes)
    retain(snapshot_id.encode())
    revisions, dependencies, blocks = {}, {}, {}

    for bundle_id in bundles:
        deadline()
        bundle = ingestion_store.load(originals, derived, bundle_id)
        deadline()
        _insert(revisions, bundle.revision.revision_id, bundle.revision, 128, budget)
        _insert(dependencies, (bundle.dependency.revision_id, bundle.dependency.extraction_id),
                bundle.dependency, 128, budget)
        for block in bundle.blocks:
            deadline()
            _insert(blocks, block.block_id, block, 4096, budget)
        del bundle
    registry = None
    if mapping.rows:
        registry = provenance_records.Registry(
            tuple(revisions[k][1] for k in sorted(revisions)),
            tuple(dependencies[k][1] for k in sorted(dependencies)),
            tuple(blocks[k][1] for k in sorted(blocks)))
    parts = {p.partition_id: p for p in snapshot.partitions}
    _check(len(parts) == len(snapshot.partitions))
    result = {}
    for bundle_id, batch_id in groups:
        deadline()
        bundle = ingestion_store.load(originals, derived, bundle_id)
        deadline()
        group = raw_snapshot_source_rows.load_group(originals, derived, map_bytes,
                                                     bundle_id, batch_id)
        deadline()
        selected = tuple(r for r in mapping.rows if (r.bundle_container_id, r.batch_container_id)
                         == (bundle_id, batch_id))
        _check(tuple(r.declaration for r in group.rows) == selected
               and group.row_map_sha256 == _digest(map_bytes)
               and group.bundle_container_id == bundle_id and group.batch_container_id == batch_id
               and group.bundle_metadata == bundle.metadata_json
               and len(group.vector_payload) == len(selected) * 4096)
        chunks = {c.chunk_id: c for c in bundle.chunks}
        _check(len(chunks) == len(bundle.chunks))
        decoded_parts = {}
        for partition_id in {r.partition_id for r in selected}:
            deadline()
            part = parts[partition_id]
            decoded_parts[partition_id] = raw_snapshot_dense.parse(
                part.dense.container_bytes, part.dense.container_sha256, part.dense.row_count)
        for position, bound in enumerate(group.rows):
            deadline()
            row = bound.declaration
            chunk = chunks[row.chunk_id]
            scope = registry.bind_chunk(chunk)
            _check(scope == bundle.scope
                   and bound.scope_bytes == _json(scope.model_dump(mode='json'))
                   and bound.source_bytes == _json(bundle.revision.source.model_dump(mode='json'))
                   and bound.chunk_bytes == _json(chunk.model_dump(mode='json')))
            part = parts[row.partition_id]
            lexical = part.lexical.rows[row.partition_row]
            _check((lexical.ordinal, lexical.partition_row, lexical.chunk_id,
                    lexical.representation_id, lexical.rendered_sha256)
                   == (row.ordinal, row.partition_row, row.chunk_id, row.representation_id,
                       row.rendered_sha256))
            decoded = decoded_parts[row.partition_id]
            vector = group.vector_payload[position * 4096:(position + 1) * 4096]
            _check(vector == decoded.matrix[row.partition_row].tobytes(order='C'))
            terms = tuple((t.text, t.start, t.end, t.derivation) for t in lexical.terms)
            declaration = retain(_json(asdict(row)))
            chunk_bytes = retain(bound.chunk_bytes)
            source_bytes = retain(bound.source_bytes)
            scope_bytes = retain(bound.scope_bytes)
            rendered = retain(bound.rendered_text.encode('utf-8'))
            retain(_json(terms))
            retain(row.representation_id.encode())
            _check(row.ordinal not in result and len(vector) == 4096)
            result[row.ordinal] = CatalogRow(declaration, chunk_bytes, source_bytes, scope_bytes,
                                             rendered, row.representation_id, vector, terms)
            del decoded
        del group, bundle, decoded_parts
    _check(set(result) == set(range(len(mapping.rows))))
    rows = tuple(result[i] for i in range(len(result)))
    rev = tuple(revisions[k][0] for k in sorted(revisions))
    dep = tuple(dependencies[k][0] for k in sorted(dependencies))
    blk = tuple(blocks[k][0] for k in sorted(blocks))
    identity = {'version': 1, 'snapshot_id': snapshot_id, 'core': _digest(core),
                'row_map': _digest(map_bytes), 'revisions': list(map(_digest, rev)),
                'dependencies': list(map(_digest, dep)), 'blocks': list(map(_digest, blk)),
                'rows': [[_digest(r.declaration_bytes), _digest(r.chunk_bytes),
                          _digest(r.source_bytes), _digest(r.scope_bytes),
                          _digest(r.rendered_bytes), r.representation_id,
                          _digest(r.vector_bytes), r.terms] for r in rows]}
    catalog_id = 'sha256:' + _digest(_json(identity))
    retain(catalog_id.encode('utf-8'))
    deadline()
    fresh = raw_snapshot_directory.load_directory(originals, derived, root, snapshot_id)
    deadline()
    _check(fresh == snapshot)
    return Catalog(snapshot_id, core, map_bytes, rev, dep, blk, rows, catalog_id)
