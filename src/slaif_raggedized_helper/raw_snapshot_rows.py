"""Pure codec for declared raw row maps; this does not validate stored payloads."""

import hashlib
import json
import re
from dataclasses import dataclass

from . import raw_snapshot_manifest
from .embedding_vectors import POLICY_ID


class RowMapError(ValueError):
    """Invalid row map or inconsistent declaration, with no content details."""


@dataclass(frozen=True, slots=True)
class Row:
    ordinal: int
    partition_id: str
    partition_row: int
    chunk_id: str
    revision_id: str
    extraction_id: str
    representation_id: str
    rendered_sha256: str
    source_scope_sha256: str
    input_sha256: str
    token_count: int
    bundle_container_id: str
    bundle_metadata_sha256: str
    batch_container_id: str
    batch_metadata_sha256: str
    batch_row: int
    execution_fingerprint: str


@dataclass(frozen=True, slots=True)
class RawRowMap:
    map_bytes: bytes
    space_id: str
    definition_fingerprint: str
    representation_policy_fingerprint: str
    chunk_policy_fingerprint: str
    normalization_policy_id: str
    rows: tuple[Row, ...]
    partition_hashes: tuple[tuple[str, str], ...]


_HEADER = (
    "space_id",
    "definition_fingerprint",
    "representation_policy_fingerprint",
    "chunk_policy_fingerprint",
    "normalization_policy_id",
)
_ROW_FIELDS = tuple(Row.__dataclass_fields__)
_LIMIT = 16 * 1048576


def _check(condition):
    if not condition:
        raise RowMapError()


def _hex(value, prefix=""):
    _check(
        type(value) is str and re.fullmatch(re.escape(prefix) + r"[0-9a-f]{64}", value) is not None
    )


def _integer(value, low, high):
    _check(type(value) is int and low <= value <= high)


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        _check(key not in result)
        result[key] = value
    return result


def _canonical(obj):
    return json.dumps(
        obj, sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False
    ).encode("ascii")


def _subset(obj, partition):
    sub = {k: obj[k] for k in _HEADER}
    sub.update(
        schema=1,
        kind="slaif-raw-partition-row-map-v1",
        partition_id=partition,
        rows=[r for r in obj["rows"] if r["partition_id"] == partition],
    )
    result = _canonical(sub)
    _check(len(result) <= _LIMIT + 4096)
    return result


def parse(row_map_bytes: bytes) -> RawRowMap:
    """Return immutable declarations after bounded canonical validation."""
    try:
        return _parse(row_map_bytes)
    except Exception:
        raise RowMapError() from None


def _parse(data):
    _check(type(data) is bytes and 0 < len(data) <= _LIMIT)

    def reject(_):
        raise RowMapError()

    obj = json.loads(
        data.decode("ascii"), object_pairs_hook=_pairs, parse_float=reject, parse_constant=reject
    )
    _check(type(obj) is dict and set(obj) == set(_HEADER) | {"schema", "kind", "rows"})
    _check(_canonical(obj) == data)
    _check(
        type(obj["schema"]) is int and obj["schema"] == 1 and obj["kind"] == "slaif-raw-row-map-v1"
    )
    for key in ("space_id", "representation_policy_fingerprint", "chunk_policy_fingerprint"):
        _hex(obj[key])
    _hex(obj["definition_fingerprint"], "sha256:")
    _check(obj["normalization_policy_id"] == POLICY_ID)
    rows = obj["rows"]
    _check(type(rows) is list and len(rows) <= 4096)
    counts, batches, bundles = {}, {}, {}
    chunks, reps, batch_rows = set(), set(), set()
    last = None
    parsed = []
    for index, row in enumerate(rows):
        _check(type(row) is dict and set(row) == set(_ROW_FIELDS))
        for key in ("partition_id", "chunk_id", "revision_id", "extraction_id"):
            _hex(row[key], "sha256:")
        for key in (
            "representation_id",
            "rendered_sha256",
            "source_scope_sha256",
            "input_sha256",
            "bundle_container_id",
            "bundle_metadata_sha256",
            "batch_container_id",
            "batch_metadata_sha256",
            "execution_fingerprint",
        ):
            _hex(row[key])
        _integer(row["ordinal"], 0, 4095)
        _integer(row["partition_row"], 0, 4095)
        _integer(row["batch_row"], 0, 127)
        _integer(row["token_count"], 2, 1024)
        part = row["partition_id"]
        _check(row["ordinal"] == index and row["partition_row"] == counts.get(part, 0))
        counts[part] = counts.get(part, 0) + 1
        _check(len(counts) <= 128)
        key = (part, row["chunk_id"], row["representation_id"])
        _check(last is None or last < key)
        last = key
        _check(row["chunk_id"] not in chunks and row["representation_id"] not in reps)
        chunks.add(row["chunk_id"])
        reps.add(row["representation_id"])
        br = (row["batch_container_id"], row["batch_row"])
        _check(br not in batch_rows)
        batch_rows.add(br)
        batch = (row["batch_metadata_sha256"], row["execution_fingerprint"])
        bundle = (
            row["bundle_metadata_sha256"],
            row["revision_id"],
            row["extraction_id"],
            row["source_scope_sha256"],
        )
        _check(batches.setdefault(row["batch_container_id"], batch) == batch)
        _check(bundles.setdefault(row["bundle_container_id"], bundle) == bundle)
        parsed.append(Row(**row))
    hashes = tuple((p, hashlib.sha256(_subset(obj, p)).hexdigest()) for p in counts)
    return RawRowMap(data, *(obj[k] for k in _HEADER), tuple(parsed), hashes)


def subset_bytes(row_map: RawRowMap, partition_id: str) -> bytes:
    """Canonical subset for an existing partition; reject forged descriptors."""
    try:
        _check(type(row_map) is RawRowMap)
        fresh = _parse(row_map.map_bytes)
        _check(row_map == fresh)
        _hex(partition_id, "sha256:")
        _check(partition_id in dict(fresh.partition_hashes))
        return _subset(json.loads(fresh.map_bytes), partition_id)
    except Exception:
        raise RowMapError() from None


def bind(core_bytes: bytes, row_map_bytes: bytes) -> RawRowMap:
    """Cross-check fresh core and row declarations; grants no runtime authority."""
    try:
        core = raw_snapshot_manifest.parse(core_bytes)
        row_map = _parse(row_map_bytes)
        obj = json.loads(core_bytes)
        f = next(f for f in core.files if f.path == obj["row_map_path"])
        _check(
            f.role == "row_map"
            and f.schema == "slaif-raw-row-map-v1"
            and f.bytes == len(row_map_bytes)
            and f.sha256 == hashlib.sha256(row_map_bytes).hexdigest()
        )
        embedding = obj["embedding"]
        for k in _HEADER:
            _check(getattr(row_map, k) == (embedding[k] if k in embedding else obj[k]))
        _check(obj["row_count"] == len(row_map.rows))
        hashes = dict(row_map.partition_hashes)
        _check(set(hashes) == {p.partition_id for p in core.partitions})
        for part in core.partitions:
            _check(
                part.row_map_sha256 == hashes[part.partition_id]
                and part.row_count == sum(r.partition_id == part.partition_id for r in row_map.rows)
            )
        _check(
            all(
                r.revision_id in core.active_revisions
                and r.revision_id not in core.withdrawn_revisions
                for r in row_map.rows
            )
        )
        _check(
            sorted({r.execution_fingerprint for r in row_map.rows})
            == embedding["corpus_execution_fingerprints"]
        )
        return row_map
    except Exception:
        raise RowMapError() from None
