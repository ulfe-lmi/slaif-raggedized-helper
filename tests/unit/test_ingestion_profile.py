import dataclasses
import json
import os
from pathlib import Path
import subprocess
import socket

import pytest

from slaif_raggedized_helper import chunking, ingestion_profile as p
from slaif_raggedized_helper import native_tokenizers, pdf_extraction


def document():
    record = {'artifact': '/toy/tokenizer.json', 'sha256': 'a' * 64,
              'backend_version': '0.21.4', 'model_revision': 'toy', 'preprocessing': 'toy'}
    return {'schema_version': 1, 'native_runtime': {'root': '/toy/runtime',
            'packages': '/toy/packages', 'python': 'python3.12'}, 'bge': record.copy(),
            'reranker': {**record, 'artifact': '/toy/reranker'}, 'pdf_runtime': None,
            'chunk_policy': dataclasses.asdict(chunking.Policy())}


def encoded(value):
    return json.dumps(value).encode()


def test_values_and_frozen():
    doc = document()
    doc['pdf_runtime'] = {'runtime_dir': '/toy/pdf', 'packages_dir': '/toy/pdf-packages'}
    result = p.parse_profile(encoded(doc))
    assert result.native_runtime == native_tokenizers.Runtime(Path('/toy/runtime'),
                                                              Path('/toy/packages'), 'python3.12')
    assert result.pdf_runtime == pdf_extraction.PdfRuntime(
        Path('/toy/pdf'), Path('/toy/pdf-packages'))
    assert result.chunk_policy == chunking.Policy(**doc['chunk_policy'])
    assert [result.bge_body.role, result.bge_representation.role, result.reranker_pair.role] == [
        'bge_body', 'bge_representation', 'reranker_pair']
    assert result.bge_body.artifact == result.bge_representation.artifact
    assert result.bge_body.artifact == Path('/toy/tokenizer.json')
    assert result.reranker_pair.artifact == Path('/toy/reranker')
    with pytest.raises(dataclasses.FrozenInstanceError):
        result.chunk_policy = None
    assert p.parse_profile(encoded(document())).pdf_runtime is None


@pytest.mark.parametrize('change', [
    lambda d: d.pop('bge'), lambda d: d.update(extra=1),
    lambda d: d.update(schema_version=True), lambda d: d['bge'].update(role='bge_body'),
    lambda d: d['bge'].update(sha256='A' * 64),
    lambda d: d['bge'].update(backend_version='0.21.5'),
    lambda d: d['bge'].update(model_revision=''),
    lambda d: d['bge'].update(preprocessing='x' * 257),
    lambda d: d['bge'].update(artifact='relative'),
    lambda d: d['bge'].update(artifact='/bad\0path'),
    lambda d: d['bge'].update(artifact='/' + 'x' * 4096),
    lambda d: d['bge'].update(artifact='/\ud800'),
    lambda d: d['native_runtime'].update(python='python3.13'),
    lambda d: d['native_runtime'].update(root='relative'),
    lambda d: d.update(pdf_runtime={'runtime_dir': '/a'}),
    lambda d: d['chunk_policy'].pop('target'),
    lambda d: d['chunk_policy'].update(extra=1),
    lambda d: d['chunk_policy'].update(target=True),
    lambda d: d['chunk_policy'].update(target=769),
    lambda d: d['chunk_policy'].update(target=float('inf')),
])
def test_invalid_fields(change):
    doc = document()
    change(doc)
    with pytest.raises(p.ProfileError, match='^ingestion profile refused$'):
        p.parse_profile(encoded(doc))


@pytest.mark.parametrize('raw', [bytearray(b'{}'), b'\xff', b'{}' + b' ' * 65535,
    b'{"x":1,"x":2}', b'[' * 18 + b'0' + b']' * 18,
    b'[' + b'0,' * 10001 + b'0]', b'NaN'])
def test_invalid_raw(raw):
    with pytest.raises(p.ProfileError):
        p.parse_profile(raw)


def test_no_execution_or_path_lookup(monkeypatch, tmp_path):
    profile = tmp_path / 'profile.json'
    profile.write_bytes(encoded(document()))
    calls = []
    def forbidden(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError('forbidden')
    raw = profile.read_bytes()
    opens = []
    original_open = os.open
    def record_open(path, flags, *args, **kwargs):
        opens.append(path)
        return original_open(path, flags, *args, **kwargs)
    monkeypatch.setattr(p.os, 'open', record_open)
    monkeypatch.setattr(socket, 'socket', forbidden)
    monkeypatch.setattr(Path, 'resolve', forbidden)
    monkeypatch.setattr(Path, 'stat', forbidden)
    monkeypatch.setattr(subprocess, 'Popen', forbidden)
    monkeypatch.setattr(native_tokenizers, 'count', forbidden)
    monkeypatch.setattr(pdf_extraction, 'extract', forbidden)
    assert p.parse_profile(raw) == p.load_profile(profile)
    assert calls == []
    assert opens == [profile]


def test_file_cases_and_fd_cleanup(tmp_path, monkeypatch):
    data = encoded(document())
    path = tmp_path / 'profile'
    path.write_bytes(data + b' ' * (p.MAX_BYTES - len(data)))
    assert p.load_profile(path) == p.parse_profile(data)
    path.write_bytes(data + b' ' * (p.MAX_BYTES + 1 - len(data)))
    link = tmp_path / 'link'
    link.symlink_to(path)
    fifo = tmp_path / 'fifo'
    os.mkfifo(fifo)
    for candidate in (path, link, fifo, tmp_path):
        with pytest.raises(p.ProfileError):
            p.load_profile(candidate)
    path.write_bytes(data)
    original = p.os.fstat
    count = 0
    def altered(fd):
        nonlocal count
        count += 1
        result = original(fd)
        if count == 2:
            values = list(result)
            values[6] += 1
            return os.stat_result(values)
        return result
    closed = []
    close = p.os.close
    def record_close(fd):
        closed.append(fd)
        close(fd)
    monkeypatch.setattr(p.os, 'fstat', altered)
    monkeypatch.setattr(p.os, 'close', record_close)
    with pytest.raises(p.ProfileError):
        p.load_profile(path)
    assert len(closed) == 1


def test_final_deadline(monkeypatch):
    ticks = iter([0, 0, 0, 6])
    monkeypatch.setattr(p.time, 'monotonic', lambda: next(ticks))
    with pytest.raises(p.ProfileError):
        p.parse_profile(encoded(document()))
