"""Fuse bounded, caller-supplied rankings against an actual immutable catalog."""
from dataclasses import dataclass
import json
import math
import re
import time

from . import derived_store, provenance_records as p, raw_snapshot_catalog
from .source_admission import OriginalStore


class FusionError(ValueError):
    """Content-free refusal."""


@dataclass(frozen=True, slots=True)
class Entry:
    ordinal: int
    partition_id: str
    chunk_id: str
    revision_id: str
    representation_id: str
    rank: int


@dataclass(frozen=True, slots=True)
class Ranking:
    modality: str
    declared_status: str
    snapshot_id: str
    catalog_id: str
    query_id: str
    entries: tuple[Entry, ...]


@dataclass(frozen=True, slots=True)
class Hit:
    ordinal: int
    partition_id: str
    chunk_id: str
    revision_id: str
    representation_id: str
    scope_bytes: bytes
    original_chunk_bytes: bytes
    dense_rank: int | None
    lexical_rank: int | None
    score: float
    rank: int


@dataclass(frozen=True, slots=True)
class FusionResult:
    snapshot_id: str
    catalog_id: str
    query_id: str
    ranking_origin: str
    qualification: str
    dense_status: str
    lexical_status: str
    degraded: bool
    hits: tuple[Hit, ...]
    dense_input_rows: int
    lexical_input_rows: int
    unique_candidates: int
    overlap_candidates: int
    returned: int
    global_cap_applied: bool


def _check(value):
    if not value:
        raise ValueError


def _id(value, prefix=''):
    return type(value) is str and re.fullmatch(prefix + r'[0-9a-f]{64}', value) is not None


def _authority(grants, restrictions):
    total = 0
    copies = []
    specs = ((grants, p.Grants, ('schema_version', 'corpora', 'versions', 'labels')),
             (restrictions, p.Restrictions, ('schema_version', 'corpora', 'versions')))
    for obj, cls, fields in specs:
        if obj is None:
            copies.append(None)
            continue
        _check(type(obj) is cls and type(obj.__dict__) is dict and len(obj.__dict__) == len(fields))
        _check(all(key in obj.__dict__ for key in fields))
        _check(getattr(obj, '__pydantic_extra__', None) is None)
        raw = obj.__dict__
        _check(type(raw['schema_version']) is int and raw['schema_version'] == 1)
        values = {'schema_version': 1}
        for key in fields[1:]:
            value = raw[key]
            if value is None and cls is p.Restrictions:
                values[key] = None
                continue
            _check(type(value) is tuple and len(value) <= 128)
            for item in value:
                _check(type(item) is str)
                total += len(item)
                _check(total <= 65536)
                item.encode('utf-8')
            values[key] = tuple(value)
        copies.append(cls.model_validate(values))
    wire = [None if x is None else x.model_dump(mode='json') for x in copies]
    _check(len(json.dumps(wire, sort_keys=True, ensure_ascii=False, separators=(',', ':'),
                          allow_nan=False).encode('utf-8')) <= 262144)
    return tuple(copies)


def _capture_ranking(ranking):
    """Copy only bounded exact DTOs before validating or reading any source."""
    _check(type(ranking) is Ranking)
    modality = ranking.modality
    status = ranking.declared_status
    snapshot = ranking.snapshot_id
    catalog = ranking.catalog_id
    query = ranking.query_id
    entries = ranking.entries
    _check(type(entries) is tuple and len(entries) <= 60)
    copied = []
    for entry in entries:
        _check(type(entry) is Entry)
        copied.append(Entry(entry.ordinal, entry.partition_id, entry.chunk_id,
                            entry.revision_id, entry.representation_id, entry.rank))
    return Ranking(modality, status, snapshot, catalog, query, tuple(copied))


def _ranking(ranking, modality, snapshot_id, query_id):
    _check(type(ranking) is Ranking and type(ranking.modality) is str
           and ranking.modality == modality and type(ranking.declared_status) is str
           and ranking.declared_status in ('COMPLETE', 'UNAVAILABLE')
           and _id(ranking.snapshot_id, 'sha256:') and ranking.snapshot_id == snapshot_id
           and _id(ranking.query_id) and ranking.query_id == query_id
           and _id(ranking.catalog_id, 'sha256:') and type(ranking.entries) is tuple
           and len(ranking.entries) <= 60)
    _check(ranking.declared_status != 'UNAVAILABLE' or not ranking.entries)
    ordinals, representations = set(), set()
    for rank, entry in enumerate(ranking.entries, 1):
        _check(type(entry) is Entry and type(entry.ordinal) is int and 0 <= entry.ordinal <= 4095
               and type(entry.rank) is int and entry.rank == rank
               and _id(entry.partition_id, 'sha256:') and _id(entry.chunk_id, 'sha256:')
               and _id(entry.revision_id, 'sha256:') and _id(entry.representation_id))
        _check(entry.ordinal not in ordinals and entry.representation_id not in representations)
        ordinals.add(entry.ordinal)
        representations.add(entry.representation_id)


def _contribution(rank):
    return 1.0 / (60 + rank)


def _allowed(scope, grants, restrictions):
    return p.reader_allows(scope, grants, restrictions)


def fuse(originals, derived, store_root, snapshot_id, query_id, *, dense, lexical, grants,
         restrictions=None, k=60, deadline_ms=120000):
    """Return static-authority DATA; no execution, current-policy or readiness proof."""
    try:
        return _fuse(originals, derived, store_root, snapshot_id, query_id, dense, lexical,
                     grants, restrictions, k, deadline_ms)
    except Exception:
        raise FusionError('fusion refused') from None


def _fuse(originals, derived, root, snapshot_id, query_id, dense, lexical, grants, restrictions,
          k, deadline_ms):
    _check(type(deadline_ms) is int and 1 <= deadline_ms <= 120000)
    end = time.monotonic() + deadline_ms / 1000

    def remaining():
        ms = math.floor((end - time.monotonic()) * 1000)
        _check(ms > 0)
        return ms

    _check(type(originals) is OriginalStore and type(derived) is derived_store.Store)
    _check(type(root) is str and root.startswith('/') and root != '/' and len(root) <= 4096
           and len(root.encode('utf-8')) <= 4096
           and all(part not in ('', '.', '..') for part in root[1:].split('/'))
           and all(ord(c) >= 32 and not 127 <= ord(c) <= 159 for c in root))
    _check(_id(snapshot_id, 'sha256:') and _id(query_id) and type(k) is int and 1 <= k <= 60)
    dense = _capture_ranking(dense)
    lexical = _capture_ranking(lexical)
    _ranking(dense, 'dense', snapshot_id, query_id)
    _ranking(lexical, 'lexical', snapshot_id, query_id)
    _check(dense.catalog_id == lexical.catalog_id
           and (dense.declared_status == 'COMPLETE' or lexical.declared_status == 'COMPLETE'))
    grants, restrictions = _authority(grants, restrictions)
    _check(grants is not None)
    catalog = raw_snapshot_catalog.load_catalog(originals, derived, root, snapshot_id,
                                                deadline_ms=remaining())
    _check(catalog.catalog_id == dense.catalog_id)
    candidates = {}
    representations = {}
    for ranking in (dense, lexical):
        for entry in ranking.entries:
            remaining()
            _check(entry.ordinal < len(catalog.rows))
            row = catalog.rows[entry.ordinal]
            declaration = json.loads(row.declaration_bytes)
            chunk = p.admit_record('Chunk', row.chunk_bytes)
            scope = p.admit_record('Scope', row.scope_bytes)
            _check((declaration['ordinal'], declaration['partition_id'], declaration['chunk_id'],
                    declaration['revision_id'], declaration['representation_id']) ==
                   (entry.ordinal, entry.partition_id, entry.chunk_id, entry.revision_id,
                    entry.representation_id))
            _check((chunk.chunk_id, chunk.revision_id, row.representation_id) ==
                   (entry.chunk_id, entry.revision_id, entry.representation_id))
            _check(_allowed(scope, grants, restrictions))
            _check(entry.representation_id not in representations or
                   representations[entry.representation_id] == entry.ordinal)
            representations[entry.representation_id] = entry.ordinal
            if entry.ordinal not in candidates:
                candidates[entry.ordinal] = [entry, row, None, None]
            item = candidates[entry.ordinal]
            _check(item[0].partition_id == entry.partition_id and item[0].chunk_id == entry.chunk_id
                   and item[0].revision_id == entry.revision_id
                   and item[0].representation_id == entry.representation_id and item[1] == row)
            item[2 if ranking.modality == 'dense' else 3] = entry.rank
    remaining()
    scored = []
    for entry, row, dr, lr in candidates.values():
        remaining()
        score = sum(_contribution(rank) for rank in (dr, lr) if rank is not None)
        _check(math.isfinite(score) and score > 0)
        scored.append((entry, row, dr, lr, score))
    scored.sort(key=lambda x: (-x[4], x[0].chunk_id, x[0].revision_id, x[0].representation_id))
    hits = []
    for rank, (entry, row, dr, lr, score) in enumerate(scored[:k], 1):
        remaining()
        actual = catalog.rows[entry.ordinal]
        declaration = json.loads(actual.declaration_bytes)
        scope = p.admit_record('Scope', actual.scope_bytes)
        _check(actual == row and (declaration['ordinal'], declaration['partition_id'],
               declaration['chunk_id'], declaration['revision_id'],
               declaration['representation_id'])
               == (entry.ordinal, entry.partition_id, entry.chunk_id, entry.revision_id,
                   entry.representation_id) and _allowed(scope, grants, restrictions))
        hits.append(Hit(entry.ordinal, entry.partition_id, entry.chunk_id, entry.revision_id,
                        entry.representation_id, actual.scope_bytes, actual.chunk_bytes, dr, lr,
                        score, rank))
    fresh = raw_snapshot_catalog.load_catalog(originals, derived, root, snapshot_id,
                                              deadline_ms=remaining())
    remaining()
    _check(fresh == catalog)
    return FusionResult(snapshot_id, catalog.catalog_id, query_id, 'SUPPLIED_UNVERIFIED',
                        'NOT_QUALIFIED', dense.declared_status, lexical.declared_status,
                        'UNAVAILABLE' in (dense.declared_status, lexical.declared_status),
                        tuple(hits), len(dense.entries), len(lexical.entries), len(scored),
                        sum(1 for x in scored if x[2] is not None and x[3] is not None),
                        len(hits), len(scored) > k)
