"""Fresh complete raw snapshot DATA correspondence, without authority or IO publication."""

from dataclasses import dataclass
import hashlib
import json
import re
import time

from . import (
    derived_store,
    raw_snapshot_dense,
    raw_snapshot_lexical,
    raw_snapshot_manifest,
    raw_snapshot_membership,
    raw_snapshot_rows,
    technical_analyzer,
)
from .source_admission import OriginalStore


class SnapshotFilesError(ValueError):
    """Content-free whole snapshot refusal."""


@dataclass(frozen=True, slots=True)
class BoundPartition:
    partition_id: str
    row_map_sha256: str
    dense: raw_snapshot_dense.DensePartition
    lexical: raw_snapshot_lexical.LexicalPartition


@dataclass(frozen=True, slots=True)
class BoundSnapshotData:
    snapshot_id: str
    core_bytes: bytes
    row_map: raw_snapshot_rows.RawRowMap
    membership: raw_snapshot_membership.Membership
    partitions: tuple[BoundPartition, ...]


def _check(value):
    if not value:
        raise ValueError


def validate_files(originals, derived, core_bytes, files):
    """Validate all supplied bytes against fresh original-backed historical data."""
    try:
        return _validate(originals, derived, core_bytes, files)
    except Exception:
        raise SnapshotFilesError("snapshot files refused") from None


def _validate(originals, derived, core_bytes, files):
    end = time.monotonic() + 60

    def deadline():
        _check(time.monotonic() < end)

    _check(type(originals) is OriginalStore and type(derived) is derived_store.Store)
    deadline()
    core = raw_snapshot_manifest.parse(core_bytes)
    deadline()
    obj = json.loads(core_bytes)
    _check(obj["validation"]["state"] != "failed")
    _check(type(files) is tuple and 2 <= len(files) <= 258 and len(files) == len(core.files))
    lookup = {}
    total = 0
    for item, descriptor in zip(files, core.files):
        deadline()
        _check(type(item) is tuple and len(item) == 2)
        path, data = item
        _check(type(path) is str and type(data) is bytes and path == descriptor.path)
        total += len(data)
        _check(total <= 96 * 1048576 and len(data) == descriptor.bytes)
        limit = {
            "row_map": 16 * 1048576,
            "source_membership": 8 * 1048576,
            "lexical_terms": 16 * 1048576,
            "dense": raw_snapshot_dense.POLICY.max_bytes,
        }[descriptor.role]
        _check(len(data) <= limit)
    for (path, data), descriptor in zip(files, core.files):
        deadline()
        _check(hashlib.sha256(data).hexdigest() == descriptor.sha256)
        lookup[path] = data
    deadline()
    map_bytes = lookup[obj["row_map_path"]]
    membership_bytes = lookup[obj["membership_path"]]
    mapping = raw_snapshot_rows.bind(core_bytes, map_bytes)
    deadline()
    declared = raw_snapshot_membership.bind(core_bytes, map_bytes, membership_bytes)
    deadline()
    _check(
        len(mapping.rows) <= 4096
        and len(core.partitions) <= 128
        and len(declared.entries) <= 128
        and len({(r.bundle_container_id, r.batch_container_id) for r in mapping.rows}) <= 128
    )
    analyzer = technical_analyzer.analyzer_id(technical_analyzer.Policy())
    _check(
        type(analyzer) is str
        and re.fullmatch(r"sha256:[0-9a-f]{64}", analyzer)
        and obj["analyzer"]["fingerprint"] == analyzer[7:]
    )
    deadline()
    membership = raw_snapshot_membership.validate(
        originals, derived, core_bytes, map_bytes, membership_bytes
    )
    deadline()
    descriptors = {f.path: f for f in core.files}
    partitions = []
    for part in core.partitions:
        deadline()
        dense_bytes = lookup[part.dense_path]
        lexical_bytes = lookup[part.lexical_path]
        dense_desc = descriptors[part.dense_path]
        lexical_desc = descriptors[part.lexical_path]
        dense = raw_snapshot_dense.validate_partition(
            originals, derived, map_bytes, part.partition_id, dense_bytes, dense_desc.sha256
        )
        deadline()
        lexical = raw_snapshot_lexical.validate_partition(
            originals, derived, map_bytes, part.partition_id, lexical_bytes
        )
        deadline()
        selected = tuple(r for r in mapping.rows if r.partition_id == part.partition_id)
        _check(
            (
                dense.partition_id,
                dense.row_map_sha256,
                dense.space_id,
                dense.definition_fingerprint,
                dense.normalization_policy_id,
                dense.row_count,
                dense.container_bytes,
                dense.container_sha256,
                dense.codec_policy_fingerprint,
            )
            == (
                part.partition_id,
                part.row_map_sha256,
                mapping.space_id,
                mapping.definition_fingerprint,
                mapping.normalization_policy_id,
                part.row_count,
                dense_bytes,
                dense_desc.sha256,
                raw_snapshot_dense.POLICY.fingerprint(),
            )
        )
        _check(
            (
                lexical.partition_id,
                lexical.row_map_sha256,
                lexical.space_id,
                lexical.definition_fingerprint,
                lexical.normalization_policy_id,
                lexical.representation_policy_fingerprint,
                lexical.chunk_policy_fingerprint,
                lexical.analyzer_fingerprint,
                lexical.record_bytes,
                lexical.sha256,
                len(lexical.rows),
            )
            == (
                part.partition_id,
                part.row_map_sha256,
                mapping.space_id,
                mapping.definition_fingerprint,
                mapping.normalization_policy_id,
                mapping.representation_policy_fingerprint,
                mapping.chunk_policy_fingerprint,
                analyzer[7:],
                lexical_bytes,
                lexical_desc.sha256,
                part.row_count,
            )
        )
        _check(
            tuple(
                (r.ordinal, r.partition_row, r.chunk_id, r.representation_id, r.rendered_sha256)
                for r in lexical.rows
            )
            == tuple(
                (r.ordinal, r.partition_row, r.chunk_id, r.representation_id, r.rendered_sha256)
                for r in selected
            )
        )
        partitions.append(BoundPartition(part.partition_id, part.row_map_sha256, dense, lexical))
    deadline()
    return BoundSnapshotData(core.snapshot_id, core_bytes, mapping, membership, tuple(partitions))
