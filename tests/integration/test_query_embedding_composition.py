"""Actual native and sandbox protocols, with a test-only fake framework."""
import hashlib
import json
import math
import os
import struct
from dataclasses import replace
from pathlib import Path

import pytest

from slaif_raggedized_helper import cpu_embedding_worker as cpu, embedding_artifacts
from slaif_raggedized_helper import native_tokenizers
from slaif_raggedized_helper.query_embedding import QueryRefused, ResidentQueryEncoder
from test_cpu_embedding_backend import make_tree
from test_cpu_embedding_worker_composition import FAKE
from test_native_tokenizers import make_native


def test_resident_composition(tmp_path, monkeypatch):
    paths, runtime, _ = make_native(tmp_path)
    root = tmp_path / 'tree'
    manifest, _, _, definition, token = make_tree(root)
    data = paths[0].read_bytes()
    (root / 'tokenizer.json').write_bytes(data)
    entry = next(x for x in manifest['files'] if x['role'] == 'tokenizer')
    entry.update(size=len(data), sha256=hashlib.sha256(data).hexdigest())
    raw = json.dumps(manifest).encode()
    inv = embedding_artifacts.verify_artifacts(raw, root)
    token = replace(token, sha256=entry['sha256'])
    script = tmp_path / 'fake.py'
    script.write_text(FAKE.replace(
        '[[[float(x)] * 1024 for x in row] for row in ids]',
        '[[[float(x), float(len([i for i in row if i != 1]))] + [0.0] * 1022 '
        'for x in row] for row in ids]'))
    original = cpu._argv
    starts = []

    def intercept(*args):
        starts.append(1)
        argv = original(*args)
        argv[argv.index('/worker.py') - 1] = str(script)
        return argv

    monkeypatch.setattr(cpu, '_argv', intercept)
    cpu_runtime = native_tokenizers.Runtime(Path(os.environ['SLAIF_CPU_V2_TEST_ROOT']),
        Path(os.environ['SLAIF_CPU_V2_TEST_PACKAGES']), 'python3.12')
    policy = cpu.Policy(address_bytes=1024**3, cpu_seconds=30, lifetime_seconds=120)
    encoder = ResidentQueryEncoder(raw, root, definition, token, inv.inventory_id,
                                   runtime, cpu_runtime, worker_policy=policy)
    with encoder:
        session = encoder.cleanup_owner
        child = session._worker._child
        stage = session._stage.gen.gi_frame.f_locals['stage_path']
        native = session._tokenizer.encode
        forward = session._worker.forward_cls
        observed, forwards = [], []

        def tokenize(text):
            receipt = native(text)
            observed.append((text.encode('utf-8'), receipt.ids))
            return receipt

        def dispatch(ids):
            forwards.append(ids)
            return forward(ids)

        monkeypatch.setattr(session._tokenizer, 'encode', tokenize)
        monkeypatch.setattr(session._worker, 'forward_cls', dispatch)
        first = encoder.encode_query(' hello café 世界\n')
        second = encoder.encode_query('hello')
        assert observed == [(' hello café 世界\n'.encode(), (1, 3, 4, 5, 2)),
                            (b'hello', (1, 3, 2))]
        assert forwards == [[(1, 3, 4, 5, 2)], [(1, 3, 2)]]
        assert len(starts) == 1 and session._worker._child is child
        assert first.payload == struct.pack('<1024f', 1 / math.sqrt(17),
                                             4 / math.sqrt(17), *([0.0] * 1022))
        assert first.space_id == second.space_id == session.space.space_id
        assert first.query_policy_id == second.query_policy_id
        with pytest.raises(QueryRefused):
            encoder.encode_query('hello ' * 1023)
        assert len(forwards) == 2 and len(starts) == 1
    assert child.poll() is not None and not stage.exists()


@pytest.mark.parametrize('boundary', ['native', 'cpu'])
def test_owned_boundary_preserves_hostile_interruption(tmp_path, monkeypatch, boundary):
    paths, runtime, _ = make_native(tmp_path)
    root = tmp_path / 'tree'
    manifest, _, _, definition, token = make_tree(root)
    data = paths[0].read_bytes()
    (root / 'tokenizer.json').write_bytes(data)
    entry = next(x for x in manifest['files'] if x['role'] == 'tokenizer')
    entry.update(size=len(data), sha256=hashlib.sha256(data).hexdigest())
    raw = json.dumps(manifest).encode()
    inv = embedding_artifacts.verify_artifacts(raw, root)
    token = replace(token, sha256=entry['sha256'])
    script = tmp_path / 'fake.py'
    script.write_text(FAKE)
    original_argv = cpu._argv
    starts, failures, cleanups = [], [], []

    def intercept(*args):
        starts.append(1)
        argv = original_argv(*args)
        argv[argv.index('/worker.py') - 1] = str(script)
        return argv

    monkeypatch.setattr(cpu, '_argv', intercept)
    cpu_runtime = native_tokenizers.Runtime(Path(os.environ['SLAIF_CPU_V2_TEST_ROOT']),
        Path(os.environ['SLAIF_CPU_V2_TEST_PACKAGES']), 'python3.12')
    encoder = ResidentQueryEncoder(raw, root, definition, token, inv.inventory_id,
        runtime, cpu_runtime, worker_policy=cpu.Policy(address_bytes=1024**3,
                                                       cpu_seconds=30, lifetime_seconds=120))
    encoder.__enter__()
    session = encoder.cleanup_owner
    assert len(encoder.encode_query('hello').payload) == 4096 and starts == [1]
    worker, tokenizer = session._worker, session._tokenizer
    child = worker._child
    native_child = tokenizer._child
    stage = session._stage.gen.gi_frame.f_locals['stage_path']
    assert child.poll() is None and native_child.poll() is None and stage.exists()
    secondary = KeyboardInterrupt('diagnostic')

    class Hostile(BaseException):
        def add_note(self, note):
            raise secondary

        def __setattr__(self, name, value):
            raise secondary

    primary = Hostile('primary')

    def fail(*args):
        failures.append(1)
        raise primary

    def stuck():
        cleanups.append(1)
        raise ValueError('cleanup')

    target = tokenizer if boundary == 'native' else worker
    failure_method = '_read' if boundary == 'native' else '_exchange'
    cleanup_method = 'close' if boundary == 'native' else '_shutdown'
    original_cleanup = getattr(target, cleanup_method)
    monkeypatch.setattr(target, failure_method, fail)
    monkeypatch.setattr(target, cleanup_method, stuck)
    try:
        with pytest.raises(Hostile) as caught:
            encoder.encode_query('hello')
        assert caught.value is primary and failures == [1] and cleanups
        assert encoder.cleanup_owner is session and session._stage is not None and stage.exists()
        if boundary == 'native':
            assert session._tokenizer is tokenizer and tokenizer._child is native_child
            assert child.poll() is not None
        else:
            assert session._worker is worker and worker._child is child and child.poll() is None
    finally:
        monkeypatch.setattr(target, cleanup_method, original_cleanup)
        encoder.close()
    assert session._worker is None and session._tokenizer is None and session._stage is None
    assert child.poll() is not None and native_child.poll() is not None and not stage.exists()
