import hashlib
import math
import struct
from dataclasses import FrozenInstanceError

import pytest

from slaif_raggedized_helper.embedding_vectors import VectorRefused, normalize_rows


def test_values_order_and_immutability():
    row = [3.0, 4.0] + [0.0] * 1022
    other = [0.0, 5.0] + [0.0] * 1022
    result = normalize_rows([row, other])
    assert result.rows[0][:2] == pytest.approx((0.6, 0.8))
    assert math.sqrt(sum(v * v for v in result.rows[0])) == pytest.approx(1)
    assert struct.unpack("<2048f", result.payload) == sum(result.rows, ())
    assert result.sha256 == hashlib.sha256(result.payload).hexdigest()
    assert normalize_rows([row, other]) == result
    assert normalize_rows([other, row]).payload == result.payload[4096:] + result.payload[:4096]
    row[0] = 0.0
    assert result.rows[0][0] == pytest.approx(0.6)
    with pytest.raises(FrozenInstanceError):
        result.payload = b""
    assert len(normalize_rows([other] * 128).payload) == 524288


def test_refusals():
    good = [1.0] + [0.0] * 1023
    assert normalize_rows([good]).rows[0][0] == 1.0
    marker = "private-marker-92812"
    bad_values = [True, 1, marker, float("nan"), float("inf"), 1e100, 0.1]
    cases = [
        [],
        [good] * 129,
        [good[:-1]],
        [tuple(good), [0.0] * 1024],
        [[1e-13] + [0.0] * 1023],
        iter([good]),
    ]
    cases += [[good, [v] + good[1:]] for v in bad_values]
    for value in cases:
        with pytest.raises(VectorRefused) as exc:
            normalize_rows(value)
        assert marker not in str(exc.value)
        assert exc.value.__cause__ is None


def test_tiny_exact_fp32_norm_guard():
    from pathlib import Path
    import types
    import slaif_raggedized_helper.embedding_vectors as vectors

    tiny = 2.0**-45
    assert struct.unpack("<f", struct.pack("<f", tiny))[0] == tiny
    assert normalize_rows([[1.0] + [0.0] * 1023]).rows[0][0] == 1.0
    row = [tiny] + [0.0] * 1023
    with pytest.raises(VectorRefused):
        normalize_rows([row])
    # Mutation witness: changing only the threshold admits this same input.
    source = Path(vectors.__file__).read_text().replace("norm <= 1e-12", "norm <= 0")
    mutated = types.ModuleType("mutated_vectors")
    import sys

    sys.modules[mutated.__name__] = mutated
    try:
        exec(compile(source, vectors.__file__, "exec"), mutated.__dict__)
        assert mutated.normalize_rows([row]).rows[0][0] == 1.0
    finally:
        del sys.modules[mutated.__name__]


def test_no_conversion_or_subclass_hooks_and_trace_privacy():
    import traceback
    import uuid

    marker = uuid.uuid4().hex

    class Trap:
        def __float__(self):
            raise AssertionError(marker)

        def __repr__(self):
            raise AssertionError(marker)

    class TrapList(list):
        def __len__(self):
            raise AssertionError(marker)

        def __iter__(self):
            raise AssertionError(marker)

    good = [1.0] + [0.0] * 1023
    for value in (TrapList([good]), [TrapList(good)], [[Trap()] + good[1:]], [[marker] + good[1:]]):
        with pytest.raises(VectorRefused) as exc:
            normalize_rows(value)
        assert marker not in "".join(traceback.format_exception(exc.value))
