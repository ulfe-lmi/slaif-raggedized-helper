"""Source-backed lexical DATA search; callers provide static authority."""

from dataclasses import asdict, dataclass, field
import hashlib
import time
import json

from . import provenance_records


class LexicalSearchError(ValueError):
    """Content-free refusal at the search boundary."""


@dataclass(frozen=True, slots=True)
class Hit:
    ordinal: int
    partition_id: str
    chunk_id: str
    revision_id: str
    representation_id: str
    scope_bytes: bytes
    chunk_bytes: bytes
    score: float
    rank: int


@dataclass(frozen=True, slots=True)
class PartitionCount:
    partition_id: str
    eligible: int
    matching: int
    selected: int
    returned: int


@dataclass(frozen=True, slots=True, repr=False)
class LexicalTraceRow:
    ordinal: int
    partition_id: str
    chunk_id: str
    revision_id: str
    representation_id: str


@dataclass(frozen=True, slots=True, repr=False)
class LexicalPartitionTrace:
    partition_id: str
    eligible_ordinals: tuple[int, ...]
    ranked_ordinals: tuple[int, ...]
    selected_ordinals: tuple[int, ...]
    returned_ordinals: tuple[int, ...]


@dataclass(frozen=True, slots=True, repr=False)
class LexicalTrace:
    trace_id: str
    snapshot_id: str
    catalog_id: str
    query_text_sha256: str
    analyzer_fingerprint: str
    backend: str
    method: str
    authority_sha256: str
    k: int
    partition_cap: int
    rows: tuple[LexicalTraceRow, ...]
    partitions: tuple[LexicalPartitionTrace, ...]
    selected_ordinals: tuple[int, ...]
    returned_ordinals: tuple[int, ...]
    input_origin: str = field(default='SUPPLIED_UNVERIFIED', init=False)
    qualification: str = field(default='NOT_QUALIFIED', init=False)
    authorization_status: str = field(default='SUPPLIED_SCOPE_CHECKS_ONLY', init=False)
    execution_status: str = field(default='NOT_ATTESTED', init=False)


@dataclass(frozen=True, slots=True)
class LexicalResult:
    snapshot_id: str
    catalog_id: str
    query_text_sha256: str
    analyzer_fingerprint: str
    backend: str
    method: str
    hits: tuple[Hit, ...]
    partitions: tuple[PartitionCount, ...]
    eligible: int
    matching: int
    selected: int
    returned: int
    partition_cap_applied: bool
    global_cap_applied: bool
    trace: LexicalTrace | None = field(default=None, repr=False)


def _authority(grants, restrictions):
    """Bound caller-owned fields before any recursive copy or key-set allocation."""
    total = 0
    snapshots = []
    for value, cls, names in (
        (grants, provenance_records.Grants, ('corpora', 'versions', 'labels')),
        (restrictions, provenance_records.Restrictions, ('corpora', 'versions')),
    ):
        if value is None:
            snapshots.append(None)
            continue
        if type(value) is not cls or value.__pydantic_extra__ is not None:
            raise ValueError
        fields = value.__dict__
        if type(fields) is not dict or len(fields) != len(names) + 1:
            raise ValueError
        if 'schema_version' not in fields or type(fields['schema_version']) is not int:
            raise ValueError
        if fields['schema_version'] != 1 or not all(name in fields for name in names):
            raise ValueError
        data = {'schema_version': 1}
        for name in names:
            items = fields[name]
            if items is None and cls is provenance_records.Restrictions:
                data[name] = None
                continue
            if type(items) is not tuple or len(items) > 128:
                raise ValueError
            for item in items:
                if type(item) is not str:
                    raise ValueError
                total += len(item)
                if total > 65536:
                    raise ValueError
                item.encode('utf-8', 'strict')
            data[name] = tuple(items)
        snapshots.append(cls.model_validate(data))
    encoded = json.dumps([x.model_dump(mode='json') if x is not None else None
                          for x in snapshots], ensure_ascii=False, sort_keys=True,
                         separators=(',', ':'), allow_nan=False).encode('utf-8')
    if len(encoded) > 262144:
        raise ValueError
    return tuple(snapshots)


def _authority_hash(grants, restrictions):
    pair = [v.model_dump(mode='json') if v is not None else None
            for v in (grants, restrictions)]
    encoded = json.dumps(pair, sort_keys=True, ensure_ascii=False,
                         separators=(',', ':'), allow_nan=False).encode('utf-8')
    if len(encoded) > 262144:
        raise ValueError
    return hashlib.sha256(encoded).hexdigest()


def _trace_hash(obj, remaining):
    digest = hashlib.sha256(b'slaif-raw-lexical-authorized-trace-v1\n')
    size = 0
    remaining()
    for chunk in json.JSONEncoder(sort_keys=True, ensure_ascii=True,
                                  separators=(',', ':'), allow_nan=False).iterencode(obj):
        remaining()
        data = chunk.encode('ascii')
        size += len(data)
        if size > 4194304:
            raise ValueError
        digest.update(data)
    remaining()
    return 'sha256:' + digest.hexdigest()


def _validate_trace(rows, parts, selected, returned, counts, cap, k, remaining):
    import re

    def check(value):
        if not value:
            raise ValueError

    check(type(rows) is tuple and type(parts) is tuple and len(rows) <= 4096
          and len(parts) <= 128 and type(selected) is tuple and type(returned) is tuple)
    for row in rows:
        remaining()
        check(type(row) is LexicalTraceRow and type(row.ordinal) is int
              and 0 <= row.ordinal < 4096)
        for value in (row.partition_id, row.chunk_id, row.revision_id):
            check(type(value) is str and re.fullmatch(r'sha256:[0-9a-f]{64}', value))
        check(type(row.representation_id) is str
              and re.fullmatch(r'[0-9a-f]{64}', row.representation_id))
    ids = [row.ordinal for row in rows]
    check(ids == sorted(set(ids)) and len({r.chunk_id for r in rows}) == len(rows)
          and len({r.representation_id for r in rows}) == len(rows))
    check(len(parts) == len(counts))
    check(all(type(p) is LexicalPartitionTrace and type(p.partition_id) is str for p in parts))
    check([p.partition_id for p in parts] == sorted({p.partition_id for p in parts}))
    for part, count in zip(parts, counts, strict=True):
        remaining()
        eligible = tuple(r.ordinal for r in rows if r.partition_id == part.partition_id)
        for seq in (part.eligible_ordinals, part.ranked_ordinals,
                    part.selected_ordinals, part.returned_ordinals):
            check(type(seq) is tuple and all(type(i) is int and 0 <= i < 4096 for i in seq)
                  and len(seq) == len(set(seq)))
        check(bool(eligible) and part.eligible_ordinals == eligible
              and set(part.ranked_ordinals) <= set(eligible)
              and part.selected_ordinals == part.ranked_ordinals[:cap]
              and part.returned_ordinals == tuple(i for i in returned if i in eligible)
              and (count.partition_id, count.eligible, count.matching, count.selected,
                   count.returned) == (part.partition_id, len(eligible),
                   len(part.ranked_ordinals), len(part.selected_ordinals),
                   len(part.returned_ordinals)))
    check(sum(len(p.eligible_ordinals) for p in parts) == len(rows))
    all_selected = tuple(i for p in parts for i in p.selected_ordinals)
    check(all(type(i) is int and 0 <= i < 4096 for i in selected + returned)
          and len(selected) == len(set(selected)) and set(selected) == set(all_selected)
          and len(selected) == len(all_selected) and returned == selected[:k])
    check(sum(len(p.eligible_ordinals) + len(p.ranked_ordinals) +
              len(p.selected_ordinals) + len(p.returned_ordinals) for p in parts)
          + len(selected) + len(returned) <= 16504)


def _allowed_before_index(scope, grants, restrictions):
    return provenance_records.reader_allows(scope, grants, restrictions)


def _index(scorer, token_rows):
    scorer.index(token_rows, show_progress=False)


def _score(scorer, query_terms):
    return scorer.get_scores(query_terms)


def search(originals, derived, store_root, snapshot_id, text, *, grants,
           restrictions=None, k=60, partition_cap=60, deadline_ms=120000, trace=False):
    """Search authorized source-backed DATA under a cooperative deadline."""
    start = time.monotonic()
    try:
        if type(trace) is not bool:
            raise ValueError
        return _search(originals, derived, store_root, snapshot_id, text, grants,
                       restrictions, k, partition_cap, deadline_ms, trace, start)
    except Exception:
        raise LexicalSearchError('lexical search refused') from None


def _search(originals, derived, root, snapshot_id, text, grants, restrictions,
            k, partition_cap, deadline_ms, trace, start):
    import importlib.metadata
    import re
    import unicodedata

    from . import derived_store, raw_snapshot_catalog, technical_analyzer
    from .source_admission import OriginalStore

    def check(condition):
        if not condition:
            raise ValueError

    check(type(deadline_ms) is int and 1 <= deadline_ms <= 120000)
    end = start + deadline_ms / 1000

    def remaining():
        ms = int((end - time.monotonic()) * 1000)
        check(ms > 0)
        return ms

    remaining()
    check(type(originals) is OriginalStore and type(derived) is derived_store.Store)
    check(type(root) is str and len(root) <= 4096 and root.startswith('/') and root != '/')
    check(len(root.encode('utf-8')) <= 4096 and
          all(unicodedata.category(c) != 'Cc' for c in root) and
          all(p not in ('', '.', '..') for p in root[1:].split('/')))
    check(type(snapshot_id) is str and re.fullmatch(r'sha256:[0-9a-f]{64}', snapshot_id))
    check(type(k) is int and 1 <= k <= 60 and
          type(partition_cap) is int and 1 <= partition_cap <= 60)
    check(type(text) is str and len(text) <= 8192)
    text_bytes = text.encode('utf-8', 'strict')
    check(len(text_bytes) <= 32768)
    grants, restrictions = _authority(grants, restrictions)
    remaining()
    for package, version in (('bm25s', '0.2.14'), ('numpy', '2.5.4'), ('scipy', '1.18.1')):
        check(importlib.metadata.version(package) == version)
    import bm25s
    import numpy as np

    remaining()
    catalog = raw_snapshot_catalog.load_catalog(originals, derived, root, snapshot_id,
                                                deadline_ms=remaining())
    remaining()
    core = json.loads(catalog.core_bytes)
    analysis = technical_analyzer.analyze(text, technical_analyzer.Policy())
    remaining()
    analyzer = core['analyzer']
    check(analysis.analyzer_id == 'sha256:' + analyzer['fingerprint'])
    check((analyzer['backend'], analyzer['bm25s_version'], analyzer['numpy_version'],
           analyzer['scipy_version']) == ('bm25s-lucene', '0.2.14', '2.5.4', '1.18.1'))
    query = [term.text for term in analysis.terms]
    check(len(query) <= 2048)
    allowed = []
    token_count = 0
    for row in catalog.rows:
        remaining()
        decl = json.loads(row.declaration_bytes)
        scope = provenance_records.admit_record('Scope', row.scope_bytes)
        chunk = provenance_records.admit_record('Chunk', row.chunk_bytes)
        check((chunk.chunk_id, chunk.revision_id, scope.revision_id, row.representation_id) ==
              (decl['chunk_id'], decl['revision_id'], decl['revision_id'],
               decl['representation_id']))
        if _allowed_before_index(scope, grants, restrictions):
            token_count += len(row.terms)
            check(token_count <= 200000)
            allowed.append((row, decl, scope))
    check(len(query) * len(allowed) <= 4000000)
    vocab = set()
    postings = 0
    token_rows = []
    for row, _, _ in allowed:
        remaining()
        tokens = [term[0] for term in row.terms]
        unique = set(tokens)
        postings += len(unique)
        check(postings <= 200000)
        vocab.update(unique)
        check(len(vocab) <= 100000)
        token_rows.append(tokens)
    qset = set(query)
    candidates = []
    counts = {}
    for _, decl, _ in allowed:
        remaining()
        counts.setdefault(decl['partition_id'], [0, 0, 0, 0])[0] += 1
    if allowed and vocab and qset & vocab:
        scorer = bm25s.BM25(method='lucene', idf_method='lucene', k1=1.5, b=0.75,
                            delta=0.5, dtype='float32', int_dtype='int32', backend='numpy')
        check((scorer.method, scorer.idf_method, scorer.k1, scorer.b, scorer.delta,
               scorer.dtype, scorer.int_dtype, scorer.backend) ==
              ('lucene', 'lucene', 1.5, 0.75, 0.5, 'float32', 'int32', 'numpy'))
        remaining()
        _index(scorer, token_rows)
        remaining()
        check(scorer.scores['num_docs'] == len(allowed))
        scores = _score(scorer, query)
        remaining()
        check(type(scores) is np.ndarray and scores.dtype == np.dtype('float32') and
              scores.shape == (len(allowed),) and bool(np.isfinite(scores).all()))
        for i, (row, decl, scope) in enumerate(allowed):
            remaining()
            if qset.intersection(token_rows[i]):
                score = float(scores[i])
                check(score > 0)
                counts[decl['partition_id']][1] += 1
                candidates.append((score, row, decl, scope))
    def key(item):
        score, _, decl, _ = item
        return (-score, decl['chunk_id'], decl['revision_id'], decl['representation_id'])
    remaining()
    candidates.sort(key=key)
    remaining()
    selected = []
    for item in candidates:
        remaining()
        count = counts[item[2]['partition_id']]
        if count[2] < partition_cap:
            count[2] += 1
            selected.append(item)
    returned = selected[:k]
    hits = []
    for rank, (score, row, decl, scope) in enumerate(returned, 1):
        remaining()
        check(provenance_records.reader_allows(scope, grants, restrictions))
        counts[decl['partition_id']][3] += 1
        hits.append(Hit(decl['ordinal'], decl['partition_id'], decl['chunk_id'],
                        decl['revision_id'], row.representation_id, row.scope_bytes,
                        row.chunk_bytes, score, rank))
    partitions = tuple(PartitionCount(part, *counts[part]) for part in sorted(counts))
    totals = tuple(sum(getattr(p, field) for p in partitions)
                   for field in ('eligible', 'matching', 'selected', 'returned'))
    fresh = raw_snapshot_catalog.load_catalog(originals, derived, root, snapshot_id,
                                              deadline_ms=remaining())
    remaining()
    check(fresh == catalog and fresh.catalog_id == catalog.catalog_id)
    query_hash = hashlib.sha256(text_bytes).hexdigest()
    backend = 'bm25s-lucene/0.2.14/2.5.4/1.18.1'
    captured = None
    if trace:
        for row, decl, scope in allowed:
            remaining()
            ordinal = decl['ordinal']
            check(type(ordinal) is int and 0 <= ordinal < len(catalog.rows)
                  and catalog.rows[ordinal] is row and fresh.rows[ordinal] == row
                  and provenance_records.admit_record('Scope', row.scope_bytes) == scope
                  and provenance_records.reader_allows(scope, grants, restrictions))
        rows = tuple(LexicalTraceRow(d['ordinal'], d['partition_id'], d['chunk_id'],
                                     d['revision_id'], d['representation_id'])
                     for _, d, _ in sorted(allowed, key=lambda entry: entry[1]['ordinal']))
        selected_ids = tuple(item[2]['ordinal'] for item in selected)
        returned_ids = tuple(hit.ordinal for hit in hits)
        remaining()
        parts = tuple(LexicalPartitionTrace(
            c.partition_id,
            tuple(r.ordinal for r in rows if r.partition_id == c.partition_id),
            tuple(item[2]['ordinal'] for item in candidates
                  if item[2]['partition_id'] == c.partition_id),
            tuple(item[2]['ordinal'] for item in selected
                  if item[2]['partition_id'] == c.partition_id),
            tuple(hit.ordinal for hit in hits if hit.partition_id == c.partition_id))
            for c in partitions)
        remaining()
        _validate_trace(rows, parts, selected_ids, returned_ids, partitions, partition_cap, k,
                        remaining)
        remaining()
        authority_hash = _authority_hash(grants, restrictions)
        remaining()
        obj = dict(schema=1, kind='slaif-raw-lexical-authorized-trace-v1',
                   snapshot_id=snapshot_id, catalog_id=catalog.catalog_id,
                   query_text_sha256=query_hash, analyzer_fingerprint=analyzer['fingerprint'],
                   backend=backend, method='lucene', authority_sha256=authority_hash,
                   k=k, partition_cap=partition_cap, rows=[asdict(r) for r in rows],
                   partitions=[asdict(p) for p in parts], selected_ordinals=selected_ids,
                   returned_ordinals=returned_ids)
        trace_id = _trace_hash(obj, remaining)
        captured = LexicalTrace(trace_id, snapshot_id, catalog.catalog_id, query_hash,
                                analyzer['fingerprint'], backend, 'lucene', authority_hash,
                                k, partition_cap, rows, parts, selected_ids, returned_ids)
    result = LexicalResult(snapshot_id, catalog.catalog_id, query_hash,
                           analyzer['fingerprint'], backend, 'lucene', tuple(hits),
                           partitions, *totals, totals[1] > totals[2], totals[2] > totals[3],
                           captured)
    remaining()
    return result
