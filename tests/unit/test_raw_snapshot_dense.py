"""Data-only parsing and fixed policy refusal tests."""

import hashlib
import io
from dataclasses import FrozenInstanceError

import numpy as np
import pytest

from slaif_raggedized_helper import raw_snapshot_dense as dense, vector_codec


def encoded(matrix):
    return vector_codec.encode(matrix, dense.POLICY)


def test_parse_and_fixed_policy():
    result = encoded(np.eye(2, 1024, dtype="<f4"))
    parsed = dense.parse(result.container, result.container_sha256, 2)
    assert (
        parsed.payload_sha256 == hashlib.sha256(np.eye(2, 1024, dtype="<f4").tobytes()).hexdigest()
    )
    assert parsed.policy_fingerprint == dense.POLICY.fingerprint()
    assert not parsed.matrix.flags.writeable
    with pytest.raises(FrozenInstanceError):
        dense.DensePartition("p", "a", "b", "c", "d", 2, b"", "e", "f", "g").row_count = 3


@pytest.mark.parametrize(
    "case",
    [
        "hash",
        "rows",
        "bool",
        "bytes",
        "truncated",
        "extra",
        "header",
        "dtype",
        "shape",
        "fortran",
        "nan",
        "norm",
        "cap",
    ],
)
def test_parse_refusals(case):
    matrix = np.eye(2, 1024, dtype="<f4")
    data = encoded(matrix).container
    rows = 2
    if case == "dtype":
        matrix = matrix.astype("<f8")
    elif case == "shape":
        matrix = matrix[:, :3]
    elif case == "fortran":
        matrix = np.asfortranarray(matrix)
    elif case == "nan":
        matrix[0, 0] = np.nan
    elif case == "norm":
        matrix[0, 0] = 0.5
    if case in ("dtype", "shape", "fortran", "nan", "norm"):
        stream = io.BytesIO()
        np.lib.format.write_array(stream, matrix, version=(1, 0), allow_pickle=False)
        data = stream.getvalue()
    if case == "truncated":
        data = data[:-1]
    if case == "extra":
        data += b"x"
    if case == "header":
        data = data[:8] + b"\xff\xff" + data[10:]
    if case == "cap":
        data = b"x" * (dense.POLICY.max_bytes + 1)
    digest = hashlib.sha256(data).hexdigest()
    if case == "hash":
        digest = "0" * 64
    if case == "rows":
        rows = 1
    if case == "bool":
        rows = True
    if case == "bytes":
        data = bytearray(data)
    with pytest.raises(dense.DenseError):
        dense.parse(data, digest, rows)
