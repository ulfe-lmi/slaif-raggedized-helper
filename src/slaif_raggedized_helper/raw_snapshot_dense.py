"""Fresh stored-source correspondence for a normalized dense partition."""

from dataclasses import dataclass
import hashlib
import re
import time

import numpy as np

from . import derived_store, raw_snapshot_rows, raw_snapshot_source_rows, vector_codec
from .source_admission import OriginalStore


class DenseError(ValueError):
    """Content-free refusal of a dense partition."""


POLICY = vector_codec.Policy(
    max_rows=4096,
    max_elements=4194304,
    max_work=4194304,
    max_bytes=16778000,
    max_header=512,
    deadline_ms=5000,
    norm_tolerance=0.0001,
)


@dataclass(frozen=True, slots=True)
class DensePartition:
    partition_id: str
    row_map_sha256: str
    space_id: str
    definition_fingerprint: str
    normalization_policy_id: str
    row_count: int
    container_bytes: bytes
    container_sha256: str
    payload_sha256: str
    codec_policy_fingerprint: str


def _check(condition):
    if not condition:
        raise ValueError


def _parse(data, digest, rows):
    _check(type(data) is bytes and len(data) <= POLICY.max_bytes)
    _check(type(digest) is str and re.fullmatch(r"[0-9a-f]{64}", digest) is not None)
    _check(type(rows) is int and 1 <= rows <= POLICY.max_rows)
    result = vector_codec.decode(data, digest, POLICY)
    _check(result.shape == (rows, 1024))
    return result


def parse(container_bytes, expected_container_sha256, expected_rows):
    """Validate container data only; does not prove source or authorization."""
    try:
        return _parse(container_bytes, expected_container_sha256, expected_rows)
    except Exception:
        raise DenseError("dense partition refused") from None


def _build(originals, derived, row_map_bytes, partition_id, end):
    def deadline():
        _check(time.monotonic() < end)

    _check(type(originals) is OriginalStore and type(derived) is derived_store.Store)
    _check(
        type(row_map_bytes) is bytes
        and type(partition_id) is str
        and re.fullmatch(r"sha256:[0-9a-f]{64}", partition_id) is not None
    )
    deadline()
    mapping = raw_snapshot_rows.parse(row_map_bytes)
    deadline()
    selected = tuple(row for row in mapping.rows if row.partition_id == partition_id)
    _check(1 <= len(selected) <= 4096 and len(selected) * 4096 <= 16777216)
    groups = {(r.bundle_container_id, r.batch_container_id) for r in selected}
    _check(1 <= len(groups) <= 128)
    subset_hash = hashlib.sha256(raw_snapshot_rows.subset_bytes(mapping, partition_id)).hexdigest()
    blocks = {}
    for bundle_id, batch_id in sorted(groups):
        deadline()
        expected = tuple(
            r
            for r in mapping.rows
            if (r.bundle_container_id, r.batch_container_id) == (bundle_id, batch_id)
        )
        group = raw_snapshot_source_rows.load_group(
            originals, derived, row_map_bytes, bundle_id, batch_id
        )
        deadline()
        _check(
            group.bundle_container_id == bundle_id
            and group.batch_container_id == batch_id
            and group.row_map_sha256 == hashlib.sha256(row_map_bytes).hexdigest()
            and group.normalization_policy_id == mapping.normalization_policy_id
            and tuple(r.declaration for r in group.rows) == expected
            and len(group.vector_payload) == len(expected) * 4096
        )
        for position, row in enumerate(expected):
            deadline()
            if row.partition_id == partition_id:
                _check(row.ordinal not in blocks)
                block = group.vector_payload[position * 4096 : (position + 1) * 4096]
                _check(len(block) == 4096)
                blocks[row.ordinal] = block
        del group, expected
    _check(set(blocks) == {r.ordinal for r in selected})
    payload = b"".join(blocks[r.ordinal] for r in selected)
    _check(len(payload) == len(selected) * 4096)
    deadline()
    matrix = np.frombuffer(payload, dtype="<f4").reshape(len(selected), 1024)
    encoded = vector_codec.encode(matrix, POLICY)
    deadline()
    _check(
        encoded.payload_sha256 == hashlib.sha256(payload).hexdigest()
        and encoded.shape == (len(selected), 1024)
        and encoded.policy_fingerprint == POLICY.fingerprint()
    )
    parsed = _parse(encoded.container, encoded.container_sha256, len(selected))
    deadline()
    _check(parsed.payload_sha256 == encoded.payload_sha256)
    return DensePartition(
        partition_id,
        subset_hash,
        mapping.space_id,
        mapping.definition_fingerprint,
        mapping.normalization_policy_id,
        len(selected),
        encoded.container,
        encoded.container_sha256,
        encoded.payload_sha256,
        encoded.policy_fingerprint,
    )


def build_partition(originals, derived, row_map_bytes, partition_id):
    """Freshly rebuild from borrowed stores; does not publish or authorize."""
    try:
        return _build(originals, derived, row_map_bytes, partition_id, time.monotonic() + 30)
    except Exception:
        raise DenseError("dense partition refused") from None


def _same_container(left, right):
    return left == right


def validate_partition(
    originals, derived, row_map_bytes, partition_id, container_bytes, expected_container_sha256
):
    """Require a valid NPY and exact equality to a fresh stored-source rebuild."""
    try:
        end = time.monotonic() + 30
        _check(type(row_map_bytes) is bytes)
        mapping = raw_snapshot_rows.parse(row_map_bytes)
        rows = sum(r.partition_id == partition_id for r in mapping.rows)
        _parse(container_bytes, expected_container_sha256, rows)
        _check(time.monotonic() < end)
        rebuilt = _build(originals, derived, row_map_bytes, partition_id, end)
        _check(_same_container(container_bytes, rebuilt.container_bytes) and time.monotonic() < end)
        return rebuilt
    except Exception:
        raise DenseError("dense partition refused") from None
