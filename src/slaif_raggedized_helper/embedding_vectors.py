"""Bounded normalization of newly produced raw CLS rows."""

import hashlib
import math
import struct
from dataclasses import dataclass

POLICY_ID = "cls-l2-f64-fp32le-d1024-eps1e-12-tol1e-4-v1"


class VectorRefused(ValueError):
    """Input does not satisfy the vector producer contract."""


@dataclass(frozen=True)
class NormalizedVectors:
    rows: tuple[tuple[float, ...], ...]
    payload: bytes
    sha256: str
    policy_id: str


def normalize_rows(rows):
    """Normalize 1–128 rows of 1024 exact finite binary32 floats."""
    try:
        if type(rows) not in (list, tuple) or not 1 <= len(rows) <= 128:
            raise ValueError
        admitted = []
        for row in rows:
            if type(row) not in (list, tuple) or len(row) != 1024:
                raise ValueError
            copy = []
            for value in row:
                if type(value) is not float or not math.isfinite(value):
                    raise ValueError
                if struct.unpack("<f", struct.pack("<f", value))[0] != value:
                    raise ValueError
                copy.append(value)
            admitted.append(copy)
        normalized = []
        chunks = []
        for row in admitted:
            norm = math.sqrt(math.fsum(v * v for v in row))
            if not math.isfinite(norm) or norm <= 1e-12:
                raise ValueError
            chunk = struct.pack("<1024f", *(v / norm for v in row))
            result = struct.unpack("<1024f", chunk)
            output_norm = math.sqrt(math.fsum(v * v for v in result))
            if not all(math.isfinite(v) for v in result) or abs(output_norm - 1) > 1e-4:
                raise ValueError
            normalized.append(result)
            chunks.append(chunk)
        payload = b"".join(chunks)
        return NormalizedVectors(
            tuple(normalized), payload, hashlib.sha256(payload).hexdigest(), POLICY_ID
        )
    except (ValueError, OverflowError, struct.error):
        raise VectorRefused("Vector input refused") from None
