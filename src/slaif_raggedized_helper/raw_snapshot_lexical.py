"""Canonical lexical partition declarations and fresh source correspondence."""

from dataclasses import asdict, dataclass
import hashlib
import json
import re
import time

from . import derived_store, raw_snapshot_rows, raw_snapshot_source_rows, technical_analyzer
from .embedding_vectors import POLICY_ID
from .source_admission import OriginalStore


class LexicalError(ValueError):
    """Content-free refusal of lexical input."""


@dataclass(frozen=True, slots=True)
class Term:
    text: str
    start: int
    end: int
    derivation: str


@dataclass(frozen=True, slots=True)
class Row:
    ordinal: int
    partition_row: int
    chunk_id: str
    representation_id: str
    rendered_sha256: str
    terms: tuple[Term, ...]


@dataclass(frozen=True, slots=True)
class LexicalPartition:
    record_bytes: bytes
    sha256: str
    partition_id: str
    row_map_sha256: str
    space_id: str
    definition_fingerprint: str
    representation_policy_fingerprint: str
    chunk_policy_fingerprint: str
    normalization_policy_id: str
    analyzer_fingerprint: str
    rows: tuple[Row, ...]


_HEADER = ('partition_id', 'row_map_sha256', 'space_id', 'definition_fingerprint',
           'representation_policy_fingerprint', 'chunk_policy_fingerprint',
           'normalization_policy_id', 'analyzer_fingerprint')
_MAX_CHARS = 1000000
_MAX_RENDERED_BYTES = 8 * 1048576
_DERIVATIONS = {'literal', 'nfkc-casefold', 'component', 'component-nfkc-casefold'}


def _check(value):
    if not value:
        raise ValueError


def _hex(value, prefix=''):
    _check(type(value) is str and re.fullmatch(re.escape(prefix) + '[0-9a-f]{64}', value))


def _int(value, low, high):
    _check(type(value) is int and low <= value <= high)


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        _check(key not in result)
        result[key] = value
    return result


def _canonical(obj):
    return json.dumps(obj, sort_keys=True, ensure_ascii=True, separators=(',', ':'),
                      allow_nan=False).encode('ascii')


def parse(payload_bytes):
    """Parse detached immutable data; this does not establish correspondence."""
    try:
        return _parse(payload_bytes)
    except Exception:
        raise LexicalError('lexical payload refused') from None


def _parse(data):
    _check(type(data) is bytes and 0 < len(data) <= 16 * 1048576)

    def reject(_):
        raise ValueError

    obj = json.loads(data.decode('ascii'), object_pairs_hook=_pairs,
                     parse_float=reject, parse_constant=reject)
    _check(type(obj) is dict and set(obj) == set(_HEADER) | {'schema', 'kind', 'rows'})
    _check(_canonical(obj) == data)
    _check(type(obj['schema']) is int and obj['schema'] == 1
           and obj['kind'] == 'slaif-raw-lexical-v1')
    _hex(obj['partition_id'], 'sha256:')
    _hex(obj['definition_fingerprint'], 'sha256:')
    for key in ('row_map_sha256', 'space_id', 'representation_policy_fingerprint',
                'chunk_policy_fingerprint', 'analyzer_fingerprint'):
        _hex(obj[key])
    _check(obj['normalization_policy_id'] == POLICY_ID)
    rows = obj['rows']
    _check(type(rows) is list and 1 <= len(rows) <= 4096)
    parsed, chunks, reps = [], set(), set()
    previous, previous_ordinal, total = None, -1, 0
    for index, row in enumerate(rows):
        _check(type(row) is dict and set(row) == set(Row.__dataclass_fields__))
        _int(row['ordinal'], 0, 4095)
        _int(row['partition_row'], 0, 4095)
        _check(row['ordinal'] > previous_ordinal and row['partition_row'] == index)
        previous_ordinal = row['ordinal']
        _hex(row['chunk_id'], 'sha256:')
        _hex(row['representation_id'])
        _hex(row['rendered_sha256'])
        key = row['chunk_id'], row['representation_id']
        _check((previous is None or previous < key) and key[0] not in chunks
               and key[1] not in reps)
        previous = key
        chunks.add(key[0])
        reps.add(key[1])
        terms = row['terms']
        _check(type(terms) is list and len(terms) <= 100000)
        total += len(terms)
        _check(total <= 250000)
        parsed_terms = []
        for term in terms:
            _check(type(term) is dict and set(term) == set(Term.__dataclass_fields__))
            value = term['text']
            _check(type(value) is str and 0 < len(value) <= 4096
                   and len(value.encode('utf-8', 'strict')) <= 16384)
            _int(term['start'], 0, 100000)
            _int(term['end'], 0, 100000)
            _check(term['start'] < term['end'] and type(term['derivation']) is str
                   and term['derivation'] in _DERIVATIONS)
            parsed_terms.append(Term(**term))
        parsed.append(Row(row['ordinal'], row['partition_row'], *key,
                          row['rendered_sha256'], tuple(parsed_terms)))
    return LexicalPartition(data, hashlib.sha256(data).hexdigest(),
                            *(obj[k] for k in _HEADER), tuple(parsed))


def build_partition(originals, derived, row_map_bytes, partition_id):
    """Build using fresh actual source groups and the current default analyzer."""
    try:
        return _build(originals, derived, row_map_bytes, partition_id)
    except Exception:
        raise LexicalError('lexical payload refused') from None


def _build(originals, derived, row_map_bytes, partition_id):
    deadline = time.monotonic() + 30

    def check_time():
        _check(time.monotonic() < deadline)

    _check(type(originals) is OriginalStore and type(derived) is derived_store.Store
           and type(row_map_bytes) is bytes)
    _hex(partition_id, 'sha256:')
    check_time()
    row_map = raw_snapshot_rows.parse(row_map_bytes)
    check_time()
    selected = tuple(r for r in row_map.rows if r.partition_id == partition_id)
    _check(1 <= len(selected) <= 4096)
    groups = tuple(dict.fromkeys((r.bundle_container_id, r.batch_container_id) for r in selected))
    _check(len(groups) <= 128)
    subset = raw_snapshot_rows.subset_bytes(row_map, partition_id)
    check_time()
    actual = {}
    chars = byte_count = 0
    for bundle, batch in groups:
        check_time()
        group = raw_snapshot_source_rows.load_group(
            originals, derived, row_map_bytes, bundle, batch)
        check_time()
        declared = tuple(r for r in row_map.rows if (r.bundle_container_id,
                                                       r.batch_container_id) == (bundle, batch))
        _check(tuple(r.declaration for r in group.rows) == declared)
        for bound in group.rows:
            if bound.declaration.partition_id == partition_id:
                _check(bound.declaration.ordinal not in actual)
                rendered = bound.rendered_text
                chars += len(rendered)
                byte_count += len(rendered.encode('utf-8', 'strict'))
                _check(chars <= _MAX_CHARS and byte_count <= _MAX_RENDERED_BYTES)
                actual[bound.declaration.ordinal] = rendered
        del bound, group
    _check(set(actual) == {r.ordinal for r in selected})
    policy = technical_analyzer.Policy()
    analyzer_id = technical_analyzer.analyzer_id(policy)
    check_time()
    output, term_count = [], 0
    for row in selected:
        check_time()
        text = actual[row.ordinal]
        analysis = technical_analyzer.analyze(text, policy)
        check_time()
        _check(analysis.analyzer_id == analyzer_id)
        term_count += len(analysis.terms)
        _check(term_count <= 250000)
        output.append(dict(ordinal=row.ordinal, partition_row=row.partition_row,
                           chunk_id=row.chunk_id, representation_id=row.representation_id,
                           rendered_sha256=row.rendered_sha256,
                           terms=[asdict(term) for term in analysis.terms]))
    obj = {key: getattr(row_map, key) for key in _HEADER if hasattr(row_map, key)}
    obj.update(schema=1, kind='slaif-raw-lexical-v1', partition_id=partition_id,
               row_map_sha256=hashlib.sha256(subset).hexdigest(),
               analyzer_fingerprint=analyzer_id.removeprefix('sha256:'), rows=output)
    data = _canonical(obj)
    check_time()
    _parse(data)
    check_time()
    return data


def _same_bytes(left, right):
    return left == right


def validate_partition(originals, derived, row_map_bytes, partition_id, payload_bytes):
    """Parse then compare against a fresh source and analyzer build."""
    try:
        parsed = _parse(payload_bytes)
        fresh = _build(originals, derived, row_map_bytes, partition_id)
        _check(_same_bytes(payload_bytes, fresh))
        return parsed
    except Exception:
        raise LexicalError('lexical payload refused') from None
