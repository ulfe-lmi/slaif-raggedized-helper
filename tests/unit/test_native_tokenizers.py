import hashlib
import os
import subprocess
import sys
import time
from dataclasses import replace
from pathlib import Path

import pytest

from slaif_raggedized_helper import native_tokenizers as n

def make_native(tmp_path):
    """Generate owned artifacts with the explicitly configured trusted backend."""
    root = os.environ.get('SLAIF_NATIVE_TEST_ROOT')
    packages = os.environ.get('SLAIF_NATIVE_TEST_PACKAGES')
    python = os.environ.get('SLAIF_NATIVE_TEST_PYTHON')
    if not all((root, packages, python)):
        pytest.fail('set SLAIF_NATIVE_TEST_ROOT, SLAIF_NATIVE_TEST_PACKAGES and '
                    'SLAIF_NATIVE_TEST_PYTHON for required native tests')
    runtime = n.Runtime(Path(root), Path(packages), python)
    generator = """
import sys
from tokenizers import Tokenizer, models, pre_tokenizers, processors
for name, vocab, single, pair, specials in [
 ('a', {'[UNK]':0,'[CLS]':1,'[SEP]':2,'hello':3,'café':4,'世界':5},
  '[CLS] $A [SEP]', '[CLS] $A [SEP] $B:1 [SEP]:1', [('[CLS]',1),('[SEP]',2)]),
 ('b', {'<unk>':0,'<s>':1,'</s>':2,'hello':3,'café':4},
  '<s> $A </s>', '<s> $A </s> </s> $B:1 </s>:1', [('<s>',1),('</s>',2)])]:
 t = Tokenizer(models.WordLevel(vocab, unk_token=next(iter(vocab))))
 t.pre_tokenizer = pre_tokenizers.Whitespace()
 t.post_processor = processors.TemplateProcessing(single=single, pair=pair, special_tokens=specials)
 t.enable_truncation(max_length=5)
 t.enable_padding(length=20, pad_id=0, pad_token=next(iter(vocab)))
 t.save(sys.argv[1] + '/' + name + '.json')
"""
    env = {**os.environ, 'PYTHONPATH': packages, 'TOKENIZERS_PARALLELISM': 'false'}
    subprocess.run([str(Path(root) / 'bin' / python), '-c', generator, str(tmp_path)],
                   check=True, timeout=2, env=env)
    paths = [tmp_path / 'a.json', tmp_path / 'b.json']

    def definition(path, role='bge_body'):
        return n.Definition(path, hashlib.sha256(path.read_bytes()).hexdigest(), '0.21.4',
                            role, 'synthetic-revision', 'identity')
    return paths, runtime, definition


@pytest.fixture
def native(tmp_path, monkeypatch):
    original = n.count

    def bounded(*args, **kwargs):
        kwargs.setdefault('policy', n.Policy(wall_seconds=2))
        return original(*args, **kwargs)
    monkeypatch.setattr(n, 'count', bounded)
    return make_native(tmp_path)


def test_actual_full_counts(native):
    paths, runtime, definition = native
    a, b = [definition(p) for p in paths]
    assert n.count(a, runtime, 'hello café 世界').count == 5
    assert n.count(a, runtime, 'hello ' * 10000).count == 10002
    assert n.count(a, runtime, '').count == 2
    pair_a = n.count(replace(a, role='reranker_pair'), runtime, 'hello', 'café 世界')
    pair_b = n.count(replace(b, role='reranker_pair'), runtime, 'hello', 'café 世界')
    assert (pair_a.count, pair_b.count) == (6, 7)
    assert pair_a.artifact_sha256 != pair_b.artifact_sha256
    assert pair_a.mode == 'pair' and len(pair_a.input_sha256) == 64
    assert b'"truncation"' in paths[0].read_bytes()


def test_refusals(native, tmp_path):
    paths, runtime, definition = native
    d = definition(paths[0])
    cases = [(replace(d, sha256='0' * 64), 'hello', None),
             (replace(d, backend_version='other'), 'hello', None),
             (replace(d, role='reranker_pair'), 'hello', None),
             (d, 'hello', 'world'), (d, '\ud800', None), (d, 'x' * 100001, None)]
    for item, text, pair in cases:
        with pytest.raises(n.TokenizerError):
            n.count(item, runtime, text, pair)
    with pytest.raises(n.TokenizerError):
        n.Policy(max_chars=True)
    link = tmp_path / 'link'
    link.symlink_to(paths[0])
    with pytest.raises(n.TokenizerError):
        n.count(replace(d, artifact=link), runtime, 'x')
    with pytest.raises(n.TokenizerError):
        n.count(replace(d, artifact=tmp_path), runtime, 'x')
    paths[0].write_bytes(b'bad')
    with pytest.raises(n.TokenizerError):
        n.count(replace(d, sha256=hashlib.sha256(b'bad').hexdigest()), runtime, 'x')


def test_output_and_timeout_cleanup(monkeypatch):
    for script in ('import time; time.sleep(10)', 'import os; os.write(1,b"x"*100000)',
                   'import os; os._exit(3)'):
        start = time.monotonic()
        with pytest.raises(n.TokenizerError):
            n._run([sys.executable, '-c', script], 100, time.monotonic() + 0.3)
        assert time.monotonic() - start < 2


def test_invalid_child_output(native, monkeypatch):
    paths, runtime, definition = native
    for result in (b'{}', b'{"nonce":"wrong","count":1,"version":"0.21.4"}',
                   b'{"count":NaN}', b'not json'):
        monkeypatch.setattr(n, '_run', lambda *args: result)
        with pytest.raises(n.TokenizerError):
            n.count(definition(paths[0]), runtime, 'x')


def test_child_cancellation_cleanup(monkeypatch):
    original = subprocess.Popen
    children = []
    def spawn(*args, **kwargs):
        child = original(*args, **kwargs)
        children.append(child)
        return child
    monkeypatch.setattr(n.subprocess, 'Popen', spawn)
    class InterruptedSelector:
        def register(self, *args):
            pass
        def select(self, *args):
            raise KeyboardInterrupt
        def close(self):
            pass
    monkeypatch.setattr(n.selectors, 'DefaultSelector', InterruptedSelector)
    with pytest.raises(KeyboardInterrupt):
        n._run([sys.executable, '-c', 'import time; time.sleep(10)'], 100,
               time.monotonic() + 2)
    assert children[0].poll() is not None


def test_os_isolation_and_resources(native, tmp_path):
    import json
    import socket

    paths, runtime, _ = native
    request = tmp_path / 'request'
    request.write_text('{}')
    canary = tmp_path / 'outside-canary'
    canary.write_text('owned')
    listener = socket.socket()
    listener.bind(('127.0.0.1', 0))
    listener.listen()
    fd = os.open(canary, os.O_RDONLY)
    os.set_inheritable(fd, True)
    probe = tmp_path / 'probe.py'
    probe.write_text('''import json, os, resource, socket\n'''
                     f'''canary={str(canary)!r}\nfd={fd}\nport={listener.getsockname()[1]}\n'''
                     '''result = {'outside': os.path.exists(canary),
 'home': os.path.exists('/home'),
 'gpu': os.path.exists('/dev/nvidia0'), 'cpu': resource.getrlimit(resource.RLIMIT_CPU)[0],
 'memory': resource.getrlimit(resource.RLIMIT_AS)[0]}
try:
 os.fstat(fd); result['fd'] = True
except OSError:
 result['fd'] = False
try:
 socket.create_connection(('127.0.0.1', port), timeout=0.2); result['network'] = True
except OSError:
 result['network'] = False
try:
 open('/artifact.json', 'ab'); result['write'] = True
except OSError:
 result['write'] = False
try:
 bytearray(1024 * 1024 * 1024); result['allocation'] = True
except MemoryError:
 result['allocation'] = False
print(json.dumps(result))
''')
    try:
        argv = n._argv(runtime, paths[0], request)
        argv[argv.index('/worker.py') - 1] = str(probe)
        result = json.loads(n._run(argv, 4096, time.monotonic() + 2))
    finally:
        os.close(fd)
        listener.close()
    assert result == {'outside': False, 'home': False, 'gpu': False, 'cpu': 3,
                      'memory': 536870912, 'fd': False, 'network': False, 'write': False,
                      'allocation': False}


def test_artifact_growth_and_byte_limit(native, monkeypatch):
    paths, runtime, definition = native
    d = definition(paths[0])
    with pytest.raises(n.TokenizerError):
        n.count(d, runtime, 'x', policy=n.Policy(max_artifact_bytes=10))
    original = n.os.read
    changed = False
    def grow(fd, length):
        nonlocal changed
        result = original(fd, length)
        if not changed:
            changed = True
            with paths[0].open('ab') as target:
                target.write(b' ')
        return result
    monkeypatch.setattr(n.os, 'read', grow)
    with pytest.raises(n.TokenizerError):
        n.count(d, runtime, 'x')


def test_forged_matching_identity_rejects_invalid_counts(native, monkeypatch):
    import json
    paths, runtime, definition = native
    for value in (True, -1, 200001, 1.5):
        def forged(argv, cap, deadline):
            req = Path(argv[argv.index('/request.json') - 1])
            nonce = json.loads(req.read_text())['nonce']
            return json.dumps({'nonce': nonce, 'version': '0.21.4', 'count': value}).encode()
        monkeypatch.setattr(n, '_run', forged)
        with pytest.raises(n.TokenizerError):
            n.count(definition(paths[0]), runtime, 'x')


def test_cpu_limit_refuses_runaway(native, tmp_path):
    paths, runtime, _ = native
    request = tmp_path / 'request'
    request.write_text('{}')
    probe = tmp_path / 'cpu.py'
    probe.write_text('while True: pass\n')
    argv = n._argv(runtime, paths[0], request)
    argv[argv.index('/worker.py') - 1] = str(probe)
    argv[2] = '--cpu=1'
    start = time.monotonic()
    with pytest.raises(n.TokenizerError):
        n._run(argv, 4096, start + 2)
    assert time.monotonic() - start < 3


def test_serialized_padding_is_disabled(native):
    paths, runtime, definition = native
    assert n.count(definition(paths[0]), runtime, 'hello').count == 3


def test_native_worker_under_restrictive_resources(native, tmp_path):
    import json
    paths, runtime, _ = native
    request = tmp_path / 'request'
    request.write_text(json.dumps({'text': 'hello', 'pair': None, 'nonce': 'test',
                                   'version': '0.21.4'}))
    for limit in ('--as=16777216', '--cpu=0'):
        argv = n._argv(runtime, paths[0], request)
        argv[1 if limit.startswith('--as') else 2] = limit
        with pytest.raises(n.TokenizerError):
            n._run(argv, 4096, time.monotonic() + 2)


def test_output_encoding_and_duplicate_keys(native, monkeypatch):
    import json
    paths, runtime, definition = native
    for codec in ('utf-8', 'utf-16', 'utf-32'):
        def forged(argv, cap, deadline):
            req = json.loads(Path(argv[argv.index('/request.json') - 1]).read_text())
            return json.dumps({'nonce': req['nonce'], 'version': '0.21.4',
                               'count': 2}).encode(codec)
        monkeypatch.setattr(n, '_run', forged)
        if codec == 'utf-8':
            assert n.count(definition(paths[0]), runtime, 'x').count == 2
        else:
            with pytest.raises(n.TokenizerError):
                n.count(definition(paths[0]), runtime, 'x')
    def duplicate(argv, cap, deadline):
        req = json.loads(Path(argv[argv.index('/request.json') - 1]).read_text())
        return ('{"nonce":"' + req['nonce'] + '","version":"0.21.4",'
                '"count":1,"count":2}').encode()
    monkeypatch.setattr(n, '_run', duplicate)
    with pytest.raises(n.TokenizerError):
        n.count(definition(paths[0]), runtime, 'x')


def test_large_valid_artifact_and_max(native, monkeypatch):
    paths, runtime, definition = native
    path = paths[0]
    path.write_bytes(path.read_bytes() + b' ' * 17_100_000)
    d = definition(path)
    assert n.count(d, runtime, 'hello café 世界').count == 5
    assert n.count(replace(d, role='reranker_pair'), runtime, 'hello', 'café 世界').count == 6
    original = n.os.read
    def forbidden_read(*args):
        raise AssertionError('oversize descriptor must be refused before read')
    monkeypatch.setattr(n.os, 'read', forbidden_read)
    with pytest.raises(n.TokenizerError):
        n.count(d, runtime, 'x', policy=n.Policy(max_artifact_bytes=1000, wall_seconds=2))
    monkeypatch.setattr(n.os, 'read', original)
    with path.open('ab') as f:
        f.truncate(32_000_001)
    with pytest.raises(n.TokenizerError):
        n.count(d, runtime, 'x')
    with pytest.raises(n.TokenizerError):
        n.Policy(max_artifact_bytes=32_000_001)


def test_missing_runtime_refuses_offline(tmp_path):
    with pytest.raises(n.TokenizerPrerequisiteError):
        n._argv(n.Runtime(tmp_path, tmp_path), tmp_path, tmp_path)


def test_growth_over_hard_max(native, monkeypatch):
    paths, runtime, definition = native
    path = paths[0]
    with path.open('ab') as f:
        f.truncate(32_000_000)
    d = definition(path)
    original = n.os.read
    changed = False

    def grow(fd, size):
        nonlocal changed
        result = original(fd, size)
        if not changed:
            changed = True
            with path.open('ab') as target:
                target.write(b' ')
        return result

    monkeypatch.setattr(n.os, 'read', grow)
    with pytest.raises(n.TokenizerError):
        n.count(d, runtime, 'x')
    assert changed
