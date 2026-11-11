"""Bounded, non-pickle NPY v1 codec for normalized little-endian FP32 matrices."""

import ast
from dataclasses import asdict, dataclass
import hashlib
import io
import json
import math
import re
import struct
import time

import numpy as np


class CodecError(ValueError):
    """A refusal that does not disclose input bytes."""


@dataclass(frozen=True)
class Policy:
    max_rows: int = 20_000
    max_bytes: int = 82_000_000
    max_header: int = 512
    max_elements: int = 20_480_000
    max_work: int = 20_480_000
    deadline_ms: int = 5000
    norm_tolerance: float = 0.0001

    def fingerprint(self):
        _policy(self)
        data = json.dumps(asdict(self), sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(data.encode()).hexdigest()


@dataclass(frozen=True)
class Result:
    container: bytes
    container_sha256: str
    payload_sha256: str
    shape: tuple[int, int]
    policy_fingerprint: str
    matrix: np.ndarray


_CEILINGS = asdict(Policy())
_SHA = re.compile(r'[0-9a-f]{64}\Z')


def _policy(p):
    if type(p) is not Policy:
        raise ValueError
    for key, value in asdict(p).items():
        if key == 'norm_tolerance':
            if type(value) is not float or not math.isfinite(value) or not 0 < value <= 0.0001:
                raise ValueError
        elif type(value) is not int or not 1 <= value <= _CEILINGS[key]:
            raise ValueError


def _deadline(start, p):
    if time.monotonic() - start > p.deadline_ms / 1000:
        raise ValueError


def _shape(rows, p):
    if type(rows) is not int or not 1 <= rows <= p.max_rows:
        raise ValueError
    elements = rows * 1024
    if elements > p.max_elements or elements > p.max_work:
        raise ValueError
    return elements


def _header(data, p):
    if len(data) < 10 or data[:8] != b'\x93NUMPY\x01\x00':
        raise ValueError
    length = struct.unpack('<H', data[8:10])[0]
    if not 1 <= length <= p.max_header or 10 + length > len(data):
        raise ValueError
    raw = data[10:10 + length]
    if not raw.endswith(b'\n'):
        raise ValueError
    tree = ast.parse(raw.decode('utf-8').strip(), mode='eval')
    nodes = list(ast.walk(tree))
    if len(nodes) > 24 or not isinstance(tree.body, ast.Dict):
        raise ValueError
    d = tree.body
    if len(d.keys) != 3:
        raise ValueError
    keys = []
    for key in d.keys:
        if not isinstance(key, ast.Constant) or type(key.value) is not str:
            raise ValueError
        keys.append(key.value)
    if len(set(keys)) != 3 or set(keys) != {'descr', 'fortran_order', 'shape'}:
        raise ValueError
    fields = dict(zip(keys, d.values, strict=True))
    descr, order, shape = fields['descr'], fields['fortran_order'], fields['shape']
    if (not isinstance(descr, ast.Constant) or descr.value != '<f4'
            or not isinstance(order, ast.Constant) or order.value is not False
            or not isinstance(shape, ast.Tuple) or len(shape.elts) != 2):
        raise ValueError
    if any(not isinstance(x, ast.Constant) or type(x.value) is not int for x in shape.elts):
        raise ValueError
    rows, columns = (x.value for x in shape.elts)
    if columns != 1024:
        raise ValueError
    elements = _shape(rows, p)
    offset = 10 + length
    if len(data) != offset + elements * 4:
        raise ValueError
    return rows, offset


def _values(matrix, p, start):
    for pos in range(0, matrix.shape[0], 128):
        _deadline(start, p)
        block = matrix[pos:pos + 128]
        if not np.isfinite(block).all():
            raise ValueError
        # Float64 accumulation is bounded to 128 rows and avoids FP32 overflow.
        block64 = block.astype(np.float64)
        norms = np.sqrt(np.sum(block64 * block64, axis=1))
        if not np.isfinite(norms).all() or np.any(np.abs(norms - 1.0) > p.norm_tolerance):
            raise ValueError
    _deadline(start, p)


def _decode(data, expected_sha256, p, start):
    if type(data) is not bytes or len(data) > p.max_bytes:
        raise ValueError
    if type(expected_sha256) is not str or not _SHA.fullmatch(expected_sha256):
        raise ValueError
    rows, offset = _header(data, p)
    _deadline(start, p)
    digest = hashlib.sha256(data).hexdigest()
    if digest != expected_sha256:
        raise ValueError
    payload = data[offset:]
    matrix = np.frombuffer(payload, dtype='<f4').reshape(rows, 1024)
    _values(matrix, p, start)
    payload_digest = hashlib.sha256(payload).hexdigest()
    _deadline(start, p)
    return Result(data, digest, payload_digest, (rows, 1024), p.fingerprint(), matrix)


def decode(data, expected_sha256, policy=Policy()):
    """Validate immutable NPY bytes and return checksums and an immutable matrix view."""
    try:
        start = time.monotonic()
        _policy(policy)
        return _decode(data, expected_sha256, policy, start)
    except Exception:
        raise CodecError('vector codec refused') from None


def encode(matrix, policy=Policy()):
    """Snapshot a bounded matrix, write NPY v1 without pickle, and verify the output."""
    try:
        start = time.monotonic()
        _policy(policy)
        if (type(matrix) is not np.ndarray or matrix.ndim != 2 or matrix.shape[1] != 1024
                or matrix.dtype != np.dtype('<f4') or not matrix.flags.c_contiguous):
            raise ValueError
        elements = _shape(matrix.shape[0], policy)
        if elements * 4 + 10 > policy.max_bytes:
            raise ValueError
        snapshot = matrix.tobytes(order='C')
        view = np.frombuffer(snapshot, dtype='<f4').reshape(matrix.shape)
        _values(view, policy, start)
        stream = io.BytesIO()
        np.lib.format.write_array(stream, view, version=(1, 0), allow_pickle=False)
        data = stream.getvalue()
        _deadline(start, policy)
        return _decode(data, hashlib.sha256(data).hexdigest(), policy, start)
    except Exception:
        raise CodecError('vector codec refused') from None
