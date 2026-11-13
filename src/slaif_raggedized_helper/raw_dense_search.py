"""Private, source-backed exact dense DATA scoring; no model or policy authority."""

from dataclasses import asdict, dataclass, field
import hashlib
import json
import math
import re
import time
import unicodedata

import numpy as np

from . import derived_store, provenance_records as p, raw_snapshot_catalog as catalog
from . import raw_snapshot_manifest, raw_snapshot_rows
from .source_admission import OriginalStore


class DenseSearchError(ValueError):
    """Content-free refusal of a complete search."""


@dataclass(frozen=True, slots=True)
class Hit:
    ordinal: int
    partition_id: str
    chunk_id: str
    revision_id: str
    representation_id: str
    scope_bytes: bytes
    original_chunk_bytes: bytes
    rank: int
    score: float


@dataclass(frozen=True, slots=True)
class PartitionCount:
    partition_id: str
    eligible: int
    selected: int
    returned: int


@dataclass(frozen=True, slots=True, repr=False)
class DenseTraceRow:
    ordinal: int
    partition_id: str
    chunk_id: str
    revision_id: str
    representation_id: str


@dataclass(frozen=True, slots=True, repr=False)
class DensePartitionTrace:
    partition_id: str
    eligible_ordinals: tuple[int, ...]
    ranked_ordinals: tuple[int, ...]
    selected_ordinals: tuple[int, ...]
    returned_ordinals: tuple[int, ...]


@dataclass(frozen=True, slots=True, repr=False)
class DenseTrace:
    trace_id: str
    snapshot_id: str
    catalog_id: str
    query_payload_sha256: str
    query_space_id: str
    query_definition_fingerprint: str
    query_policy_id: str
    query_execution_fingerprint: str
    authority_sha256: str
    k: int
    partition_cap: int
    rows: tuple[DenseTraceRow, ...]
    partitions: tuple[DensePartitionTrace, ...]
    selected_ordinals: tuple[int, ...]
    returned_ordinals: tuple[int, ...]
    input_origin: str = field(default="SUPPLIED_UNVERIFIED", init=False)
    qualification: str = field(default="NOT_QUALIFIED", init=False)
    authorization_status: str = field(default="SUPPLIED_SCOPE_CHECKS_ONLY", init=False)
    execution_status: str = field(default="NOT_ATTESTED", init=False)


@dataclass(frozen=True, slots=True)
class DenseResult:
    snapshot_id: str
    catalog_id: str
    query_payload_sha256: str
    query_origin: str
    qualification: str
    hits: tuple[Hit, ...]
    allowed_partition_counts: tuple[PartitionCount, ...]
    eligible: int
    selected: int
    returned: int
    partition_cap_applied: bool
    global_cap_applied: bool
    trace: DenseTrace | None = field(default=None, repr=False)


def _check(value):
    if not value:
        raise ValueError


def _authority(value, cls, fields, optional, budget):
    if value is None:
        budget[1] += 4
        return None
    _check(
        type(value) is cls
        and type(value.__dict__) is dict
        and len(value.__dict__) == len(fields) + 1
        and "schema_version" in value.__dict__
        and all(name in value.__dict__ for name in fields)
        and not value.__pydantic_extra__
        and type(value.schema_version) is int
        and value.schema_version == 1
    )
    chars = 0
    for name in fields:
        items = value.__dict__[name]
        if items is None:
            _check(optional)
            continue
        _check(type(items) is tuple and len(items) <= 128)
        for item in items:
            _check(type(item) is str)
            chars += len(item)
            budget[0] += len(item)
            _check(chars <= 65536 and budget[0] <= 65536)
            item.encode("utf-8")
    copy = p._snapshot(value, cls)
    encoded = json.dumps(
        copy.model_dump(mode="json"),
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    budget[1] += len(encoded)
    _check(budget[1] <= 262144)
    return copy


def _score(matrix, query):
    return matrix @ query


def _allowed(scope, grants, restrictions):
    return p.reader_allows(scope, grants, restrictions)


def _authority_hash(grants, restrictions):
    pair = [v.model_dump(mode="json") if v is not None else None for v in (grants, restrictions)]
    encoded = json.dumps(
        pair, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")
    _check(len(encoded) <= 262144)
    return hashlib.sha256(encoded).hexdigest()


def _trace_hash(obj, remaining):
    digest = hashlib.sha256(b"slaif-raw-dense-authorized-trace-v1\n")
    size = 0
    encoder = json.JSONEncoder(
        sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False
    )
    for chunk in encoder.iterencode(obj):
        remaining()
        data = chunk.encode("ascii")
        size += len(data)
        _check(size <= 4194304)
        digest.update(data)
    return "sha256:" + digest.hexdigest()


def _validate_trace(rows, parts, selected, returned, counts, cap, k):
    _check(type(rows) is tuple and type(parts) is tuple and len(rows) <= 4096 and len(parts) <= 128)
    _check(type(selected) is tuple and type(returned) is tuple)
    _check(
        all(
            type(r) is DenseTraceRow
            and type(r.ordinal) is int
            and all(
                type(getattr(r, n)) is str
                for n in ("partition_id", "chunk_id", "revision_id", "representation_id")
            )
            for r in rows
        )
    )
    ids = [r.ordinal for r in rows]
    _check(
        ids == sorted(set(ids))
        and len({r.chunk_id for r in rows}) == len(rows)
        and len({r.representation_id for r in rows}) == len(rows)
    )
    _check(
        all(
            type(p) is DensePartitionTrace
            and type(p.partition_id) is str
            and all(
                type(seq) is tuple and all(type(i) is int for i in seq)
                for seq in (
                    p.eligible_ordinals,
                    p.ranked_ordinals,
                    p.selected_ordinals,
                    p.returned_ordinals,
                )
            )
            for p in parts
        )
    )
    _check([p.partition_id for p in parts] == sorted({p.partition_id for p in parts}))
    _check(len(parts) == len(counts))
    for part, count in zip(parts, counts, strict=True):
        eligible = tuple(r.ordinal for r in rows if r.partition_id == part.partition_id)
        _check(
            bool(eligible)
            and part.eligible_ordinals == eligible
            and len(part.ranked_ordinals) == len(eligible)
            and set(part.ranked_ordinals) == set(eligible)
            and part.selected_ordinals == part.ranked_ordinals[:cap]
            and part.returned_ordinals == tuple(i for i in returned if i in eligible)
            and (count.partition_id, count.eligible, count.selected, count.returned)
            == (
                part.partition_id,
                len(eligible),
                len(part.selected_ordinals),
                len(part.returned_ordinals),
            )
        )
    _check(sum(len(p.eligible_ordinals) for p in parts) == len(rows))
    all_selected = tuple(i for p in parts for i in p.selected_ordinals)
    _check(
        all(type(i) is int for i in selected + returned)
        and len(selected) == len(set(selected))
        and set(selected) == set(all_selected)
        and len(selected) == len(all_selected)
        and returned == selected[:k]
    )
    _check(
        sum(
            len(p.eligible_ordinals)
            + len(p.ranked_ordinals)
            + len(p.selected_ordinals)
            + len(p.returned_ordinals)
            for p in parts
        )
        + len(selected)
        + len(returned)
        <= 16504
    )


def search(
    originals,
    derived,
    store_root,
    snapshot_id,
    query_payload,
    *,
    query_space_id,
    query_definition_fingerprint,
    query_policy_id,
    query_execution_fingerprint,
    grants,
    restrictions=None,
    k=60,
    partition_cap=60,
    deadline_ms=120000,
    trace=False,
):
    """Return immutable complete DATA or refuse without exposing content in the error."""
    try:
        return _search(
            originals,
            derived,
            store_root,
            snapshot_id,
            query_payload,
            query_space_id,
            query_definition_fingerprint,
            query_policy_id,
            query_execution_fingerprint,
            grants,
            restrictions,
            k,
            partition_cap,
            deadline_ms,
            trace,
        )
    except Exception:
        raise DenseSearchError("dense search refused") from None


def _search(
    originals,
    derived,
    root,
    snapshot_id,
    payload,
    space,
    definition,
    policy,
    execution,
    grants,
    restrictions,
    k,
    cap,
    deadline_ms,
    trace,
):
    started = time.monotonic()
    _check(type(trace) is bool)
    _check(type(deadline_ms) is int and 1 <= deadline_ms <= 120000)
    end = started + deadline_ms / 1000

    def remaining():
        ms = math.floor((end - time.monotonic()) * 1000)
        _check(ms > 0)
        return min(ms, 120000)

    _check(type(originals) is OriginalStore and type(derived) is derived_store.Store)
    _check(
        type(root) is str
        and root.startswith("/")
        and root != "/"
        and len(root.encode("utf-8")) <= 4096
        and all(unicodedata.category(c) != "Cc" for c in root)
        and all(x not in ("", ".", "..") for x in root[1:].split("/"))
    )
    _check(type(snapshot_id) is str and re.fullmatch(r"sha256:[0-9a-f]{64}", snapshot_id))
    for value, prefix in ((space, ""), (definition, "sha256:"), (policy, ""), (execution, "")):
        _check(type(value) is str and re.fullmatch(re.escape(prefix) + "[0-9a-f]{64}", value))
    _check(type(k) is int and 1 <= k <= 60 and type(cap) is int and 1 <= cap <= 60)
    _check(type(payload) is bytes and len(payload) == 4096 and np.__version__ == "2.5.4")
    query = np.frombuffer(payload, dtype="<f4")
    _check(np.isfinite(query).all() and abs(float(np.linalg.norm(query)) - 1) <= 1e-4)
    budget = [0, 3]
    grants = _authority(grants, p.Grants, ("corpora", "versions", "labels"), False, budget)
    restrictions = _authority(restrictions, p.Restrictions, ("corpora", "versions"), True, budget)
    _check(budget[1] <= 262144)
    remaining()
    source = catalog.load_catalog(originals, derived, root, snapshot_id, deadline_ms=remaining())
    remaining()
    raw_snapshot_manifest.parse(source.core_bytes)
    embedding = json.loads(source.core_bytes)["embedding"]
    _check(
        (space, definition, policy, execution)
        == (
            embedding["space_id"],
            embedding["definition_fingerprint"],
            embedding["query_policy_fingerprint"],
            embedding["query_execution_fingerprint"],
        )
    )
    mapping = raw_snapshot_rows.parse(source.row_map_bytes)
    _check(len(source.rows) == len(mapping.rows) <= 4096)
    groups = {}
    for row, declaration in zip(source.rows, mapping.rows, strict=True):
        remaining()
        data = json.loads(row.declaration_bytes)
        _check(
            data == {name: getattr(declaration, name) for name in declaration.__dataclass_fields__}
            and row.representation_id == declaration.representation_id
            and len(row.vector_bytes) == 4096
        )
        scope = p.admit_record("Scope", row.scope_bytes)
        chunk = p.admit_record("Chunk", row.chunk_bytes)
        _check(
            chunk.chunk_id == declaration.chunk_id
            and chunk.revision_id == declaration.revision_id
            and scope.revision_id == declaration.revision_id
        )
        identity = (scope.corpus, scope.version, scope.labels)
        group = groups.setdefault(declaration.partition_id, [identity, []])
        _check(group[0] == identity)
        if _allowed(scope, grants, restrictions):
            group[1].append((row, declaration, scope))
    _check(len(groups) <= 128)
    selected = []
    counts = []
    trace_ranked = {} if trace else None
    for partition_id in sorted(groups):
        remaining()
        entries = groups[partition_id][1]
        if not entries:
            continue
        matrix = np.stack([np.frombuffer(row.vector_bytes, dtype="<f4") for row, _, _ in entries])
        _check(
            matrix.shape == (len(entries), 1024)
            and np.isfinite(matrix).all()
            and np.all(np.abs(np.linalg.norm(matrix, axis=1) - 1) <= 1e-4)
        )
        scores = _score(matrix, query)
        _check(scores.shape == (len(entries),) and np.isfinite(scores).all())
        ranked = [
            (float(score), row, dec, scope)
            for score, (row, dec, scope) in zip(scores, entries, strict=True)
        ]
        ranked.sort(key=lambda x: (-x[0], x[2].chunk_id, x[2].revision_id, x[2].representation_id))
        chosen = ranked[:cap]
        if trace:
            trace_ranked[partition_id] = tuple(item[2].ordinal for item in ranked)
        selected.extend(chosen)
        counts.append((partition_id, len(entries), len(chosen)))
    selected.sort(key=lambda x: (-x[0], x[2].chunk_id, x[2].revision_id, x[2].representation_id))
    for score, row, dec, scope in selected:
        remaining()
        _check(
            math.isfinite(score)
            and p.reader_allows(scope, grants, restrictions)
            and row is source.rows[dec.ordinal]
            and json.loads(row.chunk_bytes)["chunk_id"] == dec.chunk_id
            and p.admit_record("Scope", row.scope_bytes) == scope
        )
    returned = selected[:k]
    hits = tuple(
        Hit(
            dec.ordinal,
            dec.partition_id,
            dec.chunk_id,
            dec.revision_id,
            dec.representation_id,
            row.scope_bytes,
            row.chunk_bytes,
            i,
            score,
        )
        for i, (score, row, dec, _) in enumerate(returned, 1)
    )
    partition_counts = tuple(
        PartitionCount(part, eligible, chosen, sum(hit.partition_id == part for hit in hits))
        for part, eligible, chosen in counts
    )
    fresh = catalog.load_catalog(originals, derived, root, snapshot_id, deadline_ms=remaining())
    remaining()
    _check(fresh.catalog_id == source.catalog_id and fresh == source)
    eligible = sum(c.eligible for c in partition_counts)
    payload_hash = hashlib.sha256(payload).hexdigest()
    captured_trace = None
    if trace:
        eligible_entries = sorted(
            (entry for _, entries in groups.values() for entry in entries),
            key=lambda entry: entry[1].ordinal,
        )
        for row, dec, scope in eligible_entries:
            remaining()
            _check(
                row is source.rows[dec.ordinal]
                and fresh.rows[dec.ordinal] == row
                and p.admit_record("Scope", row.scope_bytes) == scope
                and p.reader_allows(scope, grants, restrictions)
            )
        rows = tuple(
            DenseTraceRow(
                dec.ordinal, dec.partition_id, dec.chunk_id, dec.revision_id, dec.representation_id
            )
            for _, dec, _ in eligible_entries
        )
        selected_ids = tuple(item[2].ordinal for item in selected)
        returned_ids = tuple(hit.ordinal for hit in hits)
        parts = tuple(
            DensePartitionTrace(
                c.partition_id,
                tuple(r.ordinal for r in rows if r.partition_id == c.partition_id),
                trace_ranked[c.partition_id],
                trace_ranked[c.partition_id][:cap],
                tuple(hit.ordinal for hit in hits if hit.partition_id == c.partition_id),
            )
            for c in partition_counts
        )
        _validate_trace(rows, parts, selected_ids, returned_ids, partition_counts, cap, k)
        remaining()
        authority_hash = _authority_hash(grants, restrictions)
        remaining()
        obj = dict(
            schema=1,
            kind="slaif-raw-dense-authorized-trace-v1",
            snapshot_id=snapshot_id,
            catalog_id=source.catalog_id,
            query_payload_sha256=payload_hash,
            query_space_id=space,
            query_definition_fingerprint=definition,
            query_policy_id=policy,
            query_execution_fingerprint=execution,
            authority_sha256=authority_hash,
            k=k,
            partition_cap=cap,
            rows=[asdict(r) for r in rows],
            partitions=[asdict(part) for part in parts],
            selected_ordinals=selected_ids,
            returned_ordinals=returned_ids,
        )
        trace_id = _trace_hash(obj, remaining)
        captured_trace = DenseTrace(
            trace_id,
            snapshot_id,
            source.catalog_id,
            payload_hash,
            space,
            definition,
            policy,
            execution,
            authority_hash,
            k,
            cap,
            rows,
            parts,
            selected_ids,
            returned_ids,
        )
    result = DenseResult(
        snapshot_id,
        source.catalog_id,
        payload_hash,
        "SUPPLIED_UNVERIFIED",
        "NOT_QUALIFIED",
        hits,
        partition_counts,
        eligible,
        len(selected),
        len(hits),
        eligible > len(selected),
        len(selected) > len(hits),
        captured_trace,
    )
    remaining()
    return result
