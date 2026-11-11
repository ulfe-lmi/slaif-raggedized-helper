"""Bounded, in-memory JSONL framing for admitted provenance records."""

import hashlib
import json
import re
import time

from . import provenance_records as p

MAX_RECORDS = 4096
MAX_BYTES = 16 * 1024 * 1024
MAX_SECONDS = 5.0
KINDS = frozenset(
    {
        "Scope",
        "Dependency",
        "Block",
        "SourceFragment",
        "Separator",
        "TokenCount",
        "Chunk",
        "Neighbors",
        "Derived",
        "Grants",
        "Restrictions",
    }
)


class JsonlError(ValueError):
    """Input-free framing, limit or admission failure."""


def _check(start):
    if time.monotonic() - start >= MAX_SECONDS:
        raise ValueError


def _kind(kind):
    if type(kind) is not str or kind not in KINDS:
        raise ValueError


def encode(kind: str, records: tuple[bytes, ...]) -> bytes:
    """Admit each raw JSON record, returning canonical UTF-8 JSONL bytes."""
    start = time.monotonic()
    try:
        _kind(kind)
        if type(records) is not tuple or len(records) > MAX_RECORDS:
            raise ValueError
        total = 0
        for raw in records:
            _check(start)
            if type(raw) is not bytes or len(raw) > p.MAX_ADMISSION_BYTES:
                raise ValueError
            total += len(raw)
            if total > MAX_BYTES:
                raise ValueError
        output = []
        total = 0
        for raw in records:
            _check(start)
            p.admit_record(kind, raw)
            # Admission has already rejected duplicate keys, invalid Unicode and nonfinite values.
            obj = json.loads(raw.decode("utf-8"))
            line = json.dumps(
                obj, sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(",", ":")
            ).encode("utf-8")
            total += len(line) + 1
            if len(line) > p.MAX_ADMISSION_BYTES or total > MAX_BYTES:
                raise ValueError
            output.append(line + b"\n")
            _check(start)
        result = b"".join(output)
        _check(start)
        return result
    except (ValueError, TypeError, UnicodeError, RecursionError, p.ProvenanceError):
        raise JsonlError("invalid JSONL") from None


def decode(
    kind: str, data: bytes, expected_sha256: str, expected_count: int
) -> tuple[p.Record, ...]:
    """Verify exact bytes/count and admit each framed record; no cross-record binding."""
    start = time.monotonic()
    try:
        _kind(kind)
        if (
            type(data) is not bytes
            or len(data) > MAX_BYTES
            or type(expected_sha256) is not str
            or re.fullmatch(r"[0-9a-f]{64}", expected_sha256) is None
            or type(expected_count) is not int
            or not 0 <= expected_count <= MAX_RECORDS
        ):
            raise ValueError
        _check(start)
        if hashlib.sha256(data).hexdigest() != expected_sha256:
            raise ValueError
        _check(start)
        offsets = []
        pos = 0
        while pos < len(data):
            _check(start)
            end = data.find(b"\n", pos, min(len(data), pos + p.MAX_ADMISSION_BYTES + 1))
            if end < 0 or end == pos or data.find(b"\r", pos, end) != -1:
                raise ValueError
            offsets.append((pos, end))
            if len(offsets) > MAX_RECORDS:
                raise ValueError
            pos = end + 1
        if len(offsets) != expected_count:
            raise ValueError
        result = []
        for pos, end in offsets:
            _check(start)
            result.append(p.admit_record(kind, data[pos:end]))
            _check(start)
        return tuple(result)
    except (ValueError, TypeError, UnicodeError, RecursionError, p.ProvenanceError):
        raise JsonlError("invalid JSONL") from None
