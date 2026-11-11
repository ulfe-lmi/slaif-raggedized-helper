import hashlib
import io
import struct
from dataclasses import replace

import numpy as np
import pytest

from slaif_raggedized_helper import vector_codec as c


def matrix():
    a = np.zeros((2, 1024), dtype='<f4')
    a[0, 0] = 1
    a[1, :2] = (0.6, 0.8)
    return a


def sha(data):
    return hashlib.sha256(data).hexdigest()


def frame(header, payload=b''):
    header = header.encode() + b'\n'
    return b'\x93NUMPY\x01\x00' + struct.pack('<H', len(header)) + header + payload


def test_roundtrip_interoperability_and_immutability():
    a = matrix()
    result = c.encode(a)
    assert result.shape == (2, 1024)
    assert result.container_sha256 == sha(result.container)
    offset = 10 + int.from_bytes(result.container[8:10], 'little')
    assert result.payload_sha256 == sha(a.tobytes()) == sha(result.container[offset:])
    assert np.array_equal(np.load(io.BytesIO(result.container), allow_pickle=False), a)
    out = io.BytesIO()
    np.lib.format.write_array(out, a, version=(1, 0), allow_pickle=False)
    decoded = c.decode(out.getvalue(), sha(out.getvalue()))
    assert np.array_equal(decoded.matrix, a)
    a[:] = 0
    assert result.matrix[0, 0] == decoded.matrix[0, 0] == 1
    with pytest.raises(ValueError):
        decoded.matrix.setflags(write=True)


def test_policy_boundaries():
    a = matrix()[:1].copy()
    r = c.encode(a)
    length = len(r.container)
    header = int.from_bytes(r.container[8:10], 'little')
    p = replace(c.Policy(), max_rows=1, max_bytes=length, max_header=header,
                max_elements=1024, max_work=1024)
    c.encode(a, p)
    c.decode(r.container, sha(r.container), p)
    for change in ({'max_rows': 1}, {'max_bytes': length - 1}, {'max_header': header - 1},
                   {'max_elements': 1023}, {'max_work': 1023}):
        with pytest.raises(c.CodecError):
            c.encode(matrix() if 'max_rows' in change else a, replace(p, **change))
    for change in ({'max_rows': True}, {'max_work': 1.0}, {'norm_tolerance': float('nan')},
                   {'norm_tolerance': 0.00011}, {'deadline_ms': 0}):
        with pytest.raises(c.CodecError):
            c.encode(a, replace(p, **change))


def test_deadline(monkeypatch):
    ticks = iter([0, 1])
    monkeypatch.setattr(c.time, 'monotonic', lambda: next(ticks))
    with pytest.raises(c.CodecError):
        c.encode(matrix(), replace(c.Policy(), deadline_ms=1))


@pytest.mark.parametrize('value', [float('nan'), float('inf'), 0, 2, 3.4e38])
def test_invalid_values(value):
    a = matrix()[:1].copy()
    a[0, 0] = value
    with pytest.raises(c.CodecError, match='^vector codec refused$'):
        c.encode(a)


def test_invalid_arrays():
    for a in ([], np.zeros((0, 1024), dtype='<f4'), matrix().astype('float64'),
              np.asfortranarray(matrix()), matrix()[:, ::-1], np.zeros((1024,), dtype='<f4')):
        with pytest.raises(c.CodecError):
            c.encode(a)


@pytest.mark.parametrize('header', [
    "{'descr':'<f4','fortran_order':False,'shape':(True,1024)}",
    "{'descr':'<f4','fortran_order':False,'shape':(99999999999999999999,1024)}",
    "{'descr':'<f4','fortran_order':False,'shape':(-1,1024)}",
    "{'descr':'<f4','fortran_order':False,'shape':(1,1024),'shape':(1,1024)}",
    "{'descr':'<f4','fortran_order':False,'shape':(1,1024),'evil':0}",
    "{'descr':'|O','fortran_order':False,'shape':(1,1024)}",
    "{'descr':[('x','<f4')],'fortran_order':False,'shape':(1,1024)}",
    "{'descr':'<f4','fortran_order':True,'shape':(1,1024)}",
    "{'descr':'<f4','fortran_order':False,'shape':(1,1024,1)}",
    "{'descr':__import__('canary'),'fortran_order':False,'shape':(1,1024)}",
])
def test_header_refusals_before_materialization(header, monkeypatch):
    data = frame(header)
    monkeypatch.setattr(c.np, 'frombuffer', lambda *a, **k: pytest.fail('materialized'))
    monkeypatch.setattr(c.np, 'load', lambda *a, **k: pytest.fail('loaded'))
    with pytest.raises(c.CodecError, match='^vector codec refused$'):
        c.decode(data, sha(data))


def test_corrupt_frames():
    data = c.encode(matrix()).container
    variants = [data[:-1], data + b'x', b'bad' + data[3:], data[:6] + b'\x02\x00' + data[8:],
                data[:10] + b'\xff' + data[11:], data[:8] + b'\xff\xff' + data[10:]]
    for value in variants:
        with pytest.raises(c.CodecError):
            c.decode(value, sha(value))
    for checksum in ('0' * 64, 'BAD', None):
        with pytest.raises(c.CodecError):
            c.decode(data, checksum)
    with pytest.raises(c.CodecError):
        c.decode(bytearray(data), sha(data))
