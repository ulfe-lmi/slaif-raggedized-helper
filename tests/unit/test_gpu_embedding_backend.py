import json
import os
import subprocess
import sys
import uuid
from types import SimpleNamespace

import pytest

from slaif_raggedized_helper import embedding_artifacts, embedding_space, gpu_device_lease
from slaif_raggedized_helper import gpu_embedding_backend as backend
from slaif_raggedized_helper.native_tokenizers import Definition
from slaif_raggedized_helper.schema import EmbeddingDefinition
from test_embedding_artifacts import setup_tree, write_config

DEVICE = 'GPU-12345678-1234-1234-1234-123456789abc'
HOST = 'a' * 64


def make_tree(root):
    manifest = setup_tree(root)
    weight = next(x for x in manifest['files'] if x['role'] == 'weights')
    (root / weight['path']).rename(root / 'model.safetensors')
    weight['path'] = 'model.safetensors'
    write_config(root, manifest, 'config', {'model_type': 'xlm-roberta', 'hidden_size': 1024,
                                            'vocab_size': 20, 'pad_token_id': 1})
    raw = json.dumps(manifest).encode()
    inv = embedding_artifacts.verify_artifacts(raw, root)
    files = {x.role: x for x in inv.files}
    definition = EmbeddingDefinition(model_name='BAAI/bge-m3',
                                     checkpoint_revision=inv.model_revision,
                                     checkpoint_sha256=files['weights'].sha256,
                                     tokenizer_revision=inv.model_revision, pooling='cls',
                                     dimensions=1024)
    tokenizer = Definition(root / 'tokenizer.json', files['tokenizer'].sha256, '0.21.4',
                           'bge_representation', inv.model_revision, 'identity')
    return raw, inv, definition, tokenizer


class UUID:
    def __init__(self):
        self.bytes = list(uuid.UUID(DEVICE[4:]).bytes)


class Tensor:
    def __init__(self, data, dtype='fp16', device='cuda', shape=None):
        self.data, self.dtype, self.shape = data, dtype, shape
        self.device = SimpleNamespace(type=device, index=0 if device == 'cuda' else None)

    def is_floating_point(self):
        return self.dtype in ('fp16', 'fp32')

    def __getitem__(self, key):
        assert key == (slice(None), 0, slice(None))
        return Tensor([row[0] for row in self.data], shape=(len(self.data), 1024))

    def to(self, *, device, dtype):
        return Tensor(self.data, dtype, device, self.shape)

    def tolist(self):
        return self.data


class Context:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class Torch:
    float16, float32, long = 'fp16', 'fp32', 'long'
    _C = SimpleNamespace(_CUuuid=UUID)

    def __init__(self):
        self.allocations = []
        self.uuid = UUID()
        self.cuda = SimpleNamespace(is_available=lambda: True, device_count=lambda: 1,
                                    get_device_properties=lambda n: SimpleNamespace(uuid=self.uuid))

    def tensor(self, data, **kwargs):
        self.allocations.append((data, kwargs))
        return Tensor(data, kwargs['dtype'])

    def inference_mode(self):
        return Context()

    def autocast(self, *, device_type, enabled):
        assert device_type == 'cuda' and enabled is False
        return Context()


class Model:
    def __init__(self):
        self.training = True
        self.config = SimpleNamespace(vocab_size=20, pad_token_id=1, hidden_size=1024,
                                      model_type='xlm-roberta')
        self.parameter, self.buffer = Tensor(None), Tensor(None)
        self.calls = []
        self.shape = None
        self.nan = False

    def to(self, **kwargs):
        assert kwargs == {'device': 'cuda:0', 'dtype': 'fp16'}
        return self

    def eval(self):
        self.training = False
        return self

    def parameters(self):
        return iter([self.parameter])

    def buffers(self):
        return iter([self.buffer])

    def __call__(self, **kwargs):
        self.calls.append(kwargs)
        ids = kwargs['input_ids'].data
        data = [[[float(token)] * 1024 for token in row] for row in ids]
        if self.nan:
            data[0][0][0] = float('nan')
        return SimpleNamespace(last_hidden_state=Tensor(
            data, shape=self.shape or (len(ids), len(ids[0]), 1024)))


class Factory:
    def __init__(self):
        self.model, self.calls = Model(), []

    def from_pretrained(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        return self.model


@pytest.fixture
def ready(tmp_path, monkeypatch):
    root = tmp_path / 'tree'
    raw, inv, definition, tokenizer = make_tree(root)
    lease_root = tmp_path / 'locks'
    lease_root.mkdir(mode=0o700)
    lease = gpu_device_lease.acquire(str(lease_root), HOST, DEVICE)
    torch, factory = Torch(), Factory()
    calls = []
    monkeypatch.setenv('CUDA_VISIBLE_DEVICES', DEVICE)
    monkeypatch.setattr(backend, '_framework', lambda: (calls.append(1) or (torch, factory)))

    def load():
        return backend.GPUEmbeddingBackend(raw, root, definition, tokenizer, inv.inventory_id,
                                           lease, DEVICE)

    yield SimpleNamespace(root=root, raw=raw, inv=inv, definition=definition, tokenizer=tokenizer,
                          lease=lease, torch=torch, factory=factory, calls=calls, load=load,
                          lease_root=lease_root)
    lease.close()


def test_valid_two_forwards_and_lease(ready):
    r = ready
    obj = r.load()
    assert obj.space == embedding_space.admit(r.raw, r.root, r.definition, r.tokenizer,
                                              r.inv.inventory_id)
    assert obj.forward_cls([[3, 4], [5, 6, 7]]) == ((3.0,) * 1024, (5.0,) * 1024)
    assert obj.forward_cls([[8, 9]]) == ((8.0,) * 1024,)
    assert len(r.factory.calls) == 1 and len(r.factory.model.calls) == 2
    assert r.factory.calls[0] == ((str(r.root),), dict(local_files_only=True,
        trust_remote_code=False, token=False, weights_only=True, use_safetensors=True,
        torch_dtype='fp16'))
    assert r.torch.allocations[:2] == [([[3, 4, 1], [5, 6, 7]],
        {'dtype': 'long', 'device': 'cuda:0'}), ([[1, 1, 0], [1, 1, 1]],
        {'dtype': 'long', 'device': 'cuda:0'})]
    assert r.factory.model.calls[0]['return_dict'] is True
    obj.close()
    r.lease.assert_owned()
    with pytest.raises(gpu_device_lease.DeviceLeaseRefused):
        gpu_device_lease.acquire(str(r.lease_root), HOST, DEVICE)
    with pytest.raises(backend.BackendRefused):
        obj.forward_cls([[1, 2]])


@pytest.mark.parametrize('rows', [[], [[True, 1]], [[-1, 1]], [[20, 1]], [[1]],
                                   [[1] * 1025], [[1, 2]] * 129, 'bad'])
def test_invalid_no_tensor(ready, rows):
    obj = ready.load()
    with pytest.raises(backend.BackendRefused):
        obj.forward_cls(rows)
    assert ready.torch.allocations == [] and ready.factory.model.calls == []


def test_invalid_tree_and_lease_before_import(ready):
    (ready.root / 'extra').write_text('x')
    with pytest.raises(backend.BackendRefused):
        ready.load()
    assert ready.calls == [] and ready.factory.calls == []
    (ready.root / 'extra').unlink()
    with pytest.raises(backend.BackendRefused):
        backend.GPUEmbeddingBackend(ready.raw, ready.root, ready.definition, ready.tokenizer,
                                    ready.inv.inventory_id, object(), DEVICE)
    assert ready.calls == []


@pytest.mark.parametrize('failure', ['env', 'uuid_type', 'uuid_bytes', 'count', 'available'])
def test_device_refusal_before_load(ready, monkeypatch, failure):
    if failure == 'env':
        monkeypatch.setenv('CUDA_VISIBLE_DEVICES', '0')
    elif failure == 'uuid_type':
        ready.torch.uuid = object()
    elif failure == 'uuid_bytes':
        ready.torch.uuid.bytes[0] = True
    elif failure == 'count':
        ready.torch.cuda.device_count = lambda: 2
    else:
        ready.torch.cuda.is_available = lambda: False
    with pytest.raises(backend.BackendRefused):
        ready.load()
    assert ready.factory.calls == []


@pytest.mark.parametrize('failure', ['shape', 'nan', 'device', 'dtype', 'training', 'config'])
def test_model_or_output_refused(ready, failure):
    obj = ready.load()
    model = ready.factory.model
    if failure == 'shape':
        model.shape = (1, 2, 3)
    elif failure == 'nan':
        model.nan = True
    elif failure == 'device':
        model.parameter.device.index = 1
    elif failure == 'dtype':
        model.parameter.dtype = 'fp32'
    elif failure == 'training':
        model.training = True
    else:
        model.config.hidden_size = 3
    with pytest.raises(backend.BackendRefused):
        obj.forward_cls([[1, 2]])
    with pytest.raises(backend.BackendRefused):
        obj.forward_cls([[1, 2]])


def test_busy_mutation_fork_and_interrupt(ready, monkeypatch):
    obj = ready.load()
    obj._guard.acquire()
    try:
        with pytest.raises(backend.BackendRefused, match='busy'):
            obj.forward_cls([[1, 2]])
    finally:
        obj._guard.release()
    monkeypatch.setattr(backend.os, 'getpid', lambda: -1)
    with pytest.raises(backend.BackendRefused):
        obj.forward_cls([[1, 2]])
    monkeypatch.undo()


def test_definition_mutation(ready):
    obj = ready.load()
    object.__setattr__(ready.tokenizer, 'preprocessing', 'changed')
    with pytest.raises(backend.BackendRefused):
        obj.forward_cls([[1, 2]])
    assert ready.torch.allocations == []


def test_interrupt_retains_model(ready, monkeypatch):
    obj = ready.load()
    def interrupt(*args, **kwargs):
        raise KeyboardInterrupt('stop')
    monkeypatch.setattr(ready.torch, 'tensor', interrupt)
    with pytest.raises(KeyboardInterrupt, match='stop'):
        obj.forward_cls([[1, 2]])
    assert obj in backend._retained
    ready.lease.assert_owned()


def test_runtime_version_refused_before_import(monkeypatch):
    calls = []
    monkeypatch.setattr(backend.platform, 'python_implementation', lambda: 'not-cpython')
    monkeypatch.setattr(backend.importlib, 'import_module', lambda name: calls.append(name))
    with pytest.raises(ValueError):
        backend._framework()
    assert calls == []


def test_profile_full_metadata_and_module_versions(monkeypatch):
    import tomllib
    from pathlib import Path

    lock = Path(backend.__file__).resolve().parents[2] / 'worker_profiles/gpu/uv.lock'
    packages = tomllib.loads(lock.read_text())['package']
    versions = {p['name']: p['version'] for p in packages if 'registry' in p.get('source', {})}
    imports, queried = [], []
    monkeypatch.setattr(backend.platform, 'python_implementation', lambda: 'CPython')
    monkeypatch.setattr(backend.os.sys, 'version_info', (3, 12))
    def version(name):
        queried.append(name)
        return versions[name]
    def module(name):
        imports.append(name)
        key = name.replace('_', '-')
        return SimpleNamespace(__version__=versions[key], XLMRobertaModel=Factory)
    monkeypatch.setattr(backend.importlib.metadata, 'version', version)
    monkeypatch.setattr(backend.importlib, 'import_module', module)
    _, factory = backend._framework()
    assert factory is Factory and set(queried) == set(versions) and len(queried) == 57
    assert set(imports) == {x.replace('-', '_') for x in backend._PINS}
    imports.clear()
    monkeypatch.setattr(backend.importlib.metadata, 'version', lambda _: 'wrong')
    with pytest.raises(ValueError):
        backend._framework()
    assert imports == []


def test_wrong_uuid_and_forged_lease_before_framework(ready):
    other = 'GPU-12345678-1234-1234-1234-123456789abd'
    with pytest.raises(backend.BackendRefused):
        backend.GPUEmbeddingBackend(ready.raw, ready.root, ready.definition, ready.tokenizer,
                                    ready.inv.inventory_id, ready.lease, other)
    with pytest.raises(backend.BackendRefused):
        backend.GPUEmbeddingBackend(ready.raw, ready.root, ready.definition, ready.tokenizer,
                                    ready.inv.inventory_id,
                                    object.__new__(gpu_device_lease.DeviceLease), DEVICE)
    assert ready.calls == [] and ready.factory.calls == []


def test_post_load_failure_retains_owner(ready):
    ready.factory.model.parameter.dtype = 'fp32'
    with pytest.raises(backend.BackendRefused) as caught:
        ready.load()
    assert caught.value.backend_owner._model is ready.factory.model
    assert caught.value.backend_owner in backend._retained and len(ready.factory.calls) == 1
    ready.lease.assert_owned()


def test_observed_other_uuid_before_load(ready):
    ready.torch.uuid.bytes[-1] ^= 1
    with pytest.raises(backend.BackendRefused):
        ready.load()
    assert ready.factory.calls == []


def test_other_process_cannot_acquire_while_backend_closed(ready):
    obj = ready.load()
    obj.close()
    code = ("import sys; from slaif_raggedized_helper import gpu_device_lease as g; "
            "g.acquire(sys.argv[1], sys.argv[2], sys.argv[3])")
    child = subprocess.run([sys.executable, '-c', code, str(ready.lease_root), HOST, DEVICE],
                           env=os.environ.copy(), capture_output=True, timeout=5, check=False)
    assert child.returncode != 0 and b'DeviceLeaseRefused' in child.stderr
    ready.lease.assert_owned()


def test_real_fork_refuses_parent_backend(ready):
    import select
    import signal
    import time
    from pathlib import Path

    def token(pid):
        try:
            return (Path('/proc') / str(pid) / 'stat').read_text().rsplit(')', 1)[1].split()[19]
        except (OSError, IndexError):
            return None

    def reap_until(pid, deadline):
        while time.monotonic() < deadline:
            waited, status = os.waitpid(pid, os.WNOHANG)
            if waited == pid:
                return status
            time.sleep(0.01)
        return None

    obj = ready.load()
    read_fd, write_fd = os.pipe()
    pid = os.fork()
    if pid == 0:
        os.close(read_fd)
        try:
            obj.forward_cls([[1, 2]])
        except backend.BackendRefused:
            os.write(write_fd, b'R')
        finally:
            os.close(write_fd)
            os._exit(0)
    os.close(write_fd)
    identity = token(pid)
    status = None
    try:
        assert identity is not None, 'child identity unavailable; cleanup uncertain'
        readable, _, _ = select.select([read_fd], [], [], 5)
        assert readable, 'child response timed out'
        assert os.read(read_fd, 1) == b'R'
    finally:
        os.close(read_fd)
        status = reap_until(pid, time.monotonic() + 1)
        if status is None:
            if identity is not None and token(pid) == identity:
                try:
                    os.kill(pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                status = reap_until(pid, time.monotonic() + 1)
            if status is None:
                pytest.fail('owned child cleanup unconfirmed; no further signal attempted')
    assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0
    ready.lease.assert_owned()
    obj.close()


def test_actual_module_version_mismatch(monkeypatch):
    import tomllib
    from pathlib import Path

    lock = Path(backend.__file__).resolve().parents[2] / 'worker_profiles/gpu/uv.lock'
    packages = tomllib.loads(lock.read_text())['package']
    versions = {p['name']: p['version'] for p in packages if 'registry' in p.get('source', {})}
    monkeypatch.setattr(backend.platform, 'python_implementation', lambda: 'CPython')
    monkeypatch.setattr(backend.os.sys, 'version_info', (3, 12))
    monkeypatch.setattr(backend.importlib.metadata, 'version', versions.__getitem__)
    monkeypatch.setattr(backend.importlib, 'import_module', lambda _: SimpleNamespace(
        __version__='wrong', XLMRobertaModel=Factory))
    with pytest.raises(ValueError):
        backend._framework()


def test_rows_frozen_before_device_callback(ready, monkeypatch):
    obj = ready.load()
    assert obj.forward_cls([[2, 3]]) == ((2.0,) * 1024,)
    rows = [[2, 3]]
    original = ready.torch.cuda.get_device_properties
    def mutate(index):
        rows[0][0] = 99999999
        return original(index)
    monkeypatch.setattr(ready.torch.cuda, 'get_device_properties', mutate)
    assert obj.forward_cls(rows) == ((2.0,) * 1024,)
    assert ready.torch.allocations[-2][0] == [[2, 3]]
    obj.close()


def test_device_configuration_mutation_refused_before_allocation(ready, monkeypatch):
    obj = ready.load()
    assert obj.forward_cls([[2, 3]]) == ((2.0,) * 1024,)
    other = 'GPU-12345678-1234-1234-1234-123456789abd'
    obj._device_uuid = other
    ready.torch.uuid.bytes = list(uuid.UUID(other[4:]).bytes)
    monkeypatch.setenv('CUDA_VISIBLE_DEVICES', other)
    before = len(ready.torch.allocations)
    with pytest.raises(backend.BackendRefused) as caught:
        obj.forward_cls([[2, 3]])
    assert caught.value.backend_owner is obj and len(ready.torch.allocations) == before
    obj.close()
    ready.lease.assert_owned()


def test_autocast_disabled_and_restored(ready, monkeypatch):
    obj = ready.load()
    assert obj.forward_cls([[2, 3]]) == ((2.0,) * 1024,)
    ambient = [True]
    class Autocast:
        def __enter__(self):
            self.old, ambient[0] = ambient[0], False
        def __exit__(self, *args):
            ambient[0] = self.old
    def autocast(*, device_type, enabled):
        assert device_type == 'cuda' and enabled is False
        return Autocast()
    original = type(ready.factory.model).__call__
    def forward(model, **kwargs):
        result = original(model, **kwargs)
        if ambient[0]:
            result.last_hidden_state.dtype = 'bf16'
        return result
    monkeypatch.setattr(ready.torch, 'autocast', autocast)
    monkeypatch.setattr(type(ready.factory.model), '__call__', forward)
    assert obj.forward_cls([[2, 3]]) == ((2.0,) * 1024,)
    assert ambient == [True]
    obj.close()


def test_mutated_definition_bounded_before_unknown_operations(ready, monkeypatch):
    import inspect
    import textwrap
    import tracemalloc

    obj = ready.load()
    assert obj.forward_cls([[2, 3]]) == ((2.0,) * 1024,)
    calls = []
    class Unknown:
        def __eq__(self, other):
            calls.append('eq')
            raise AssertionError('unknown equality')
        def __len__(self):
            return 1
        def __str__(self):
            calls.append('str')
            raise AssertionError('unknown string')
    unknown = Unknown()
    object.__setattr__(ready.definition, 'model_name', unknown)
    before = len(ready.torch.allocations)
    with pytest.raises(backend.BackendRefused):
        obj.forward_cls([[2, 3]])
    assert calls == [] and len(ready.torch.allocations) == before
    obj.close()
    object.__setattr__(ready.definition, 'model_name', 'BAAI/bge-m3')
    obj = ready.load()
    source = textwrap.dedent(inspect.getsource(backend.GPUEmbeddingBackend._definition_snapshot))
    original = 'type(value) is not str or len(value) > limit'
    assert source.count(original) == 1
    namespace = dict(backend.__dict__)
    exec(source.replace(original, 'len(value) > limit'), namespace)
    object.__setattr__(ready.definition, 'model_name', unknown)
    with monkeypatch.context() as patch:
        patch.setattr(backend.GPUEmbeddingBackend, '_definition_snapshot',
                      namespace['_definition_snapshot'])
        with pytest.raises(backend.BackendRefused):
            obj.forward_cls([[2, 3]])
    assert calls == ['eq']  # The same no-calls assertion detects the removed guard.
    obj.close()
    object.__setattr__(ready.definition, 'model_name', 'BAAI/bge-m3')
    obj = ready.load()
    payload = 'x' * 1000000
    object.__setattr__(ready.definition, 'model_name', payload)
    tracemalloc.start()
    try:
        with pytest.raises(backend.BackendRefused):
            obj.forward_cls([[2, 3]])
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    assert peak < 200000
    obj.close()


def test_failure_owner_reference_and_close(ready, monkeypatch):
    obj = ready.load()
    assert obj.forward_cls([[2, 3]]) == ((2.0,) * 1024,)
    interruption = KeyboardInterrupt('forward')
    def interrupt(*args, **kwargs):
        raise interruption
    monkeypatch.setattr(ready.torch, 'tensor', interrupt)
    with pytest.raises(KeyboardInterrupt) as caught:
        obj.forward_cls([[2, 3]])
    assert caught.value is interruption and caught.value.backend_owner is obj
    assert obj in backend._retained
    obj.close()
    assert obj not in backend._retained and obj._model is None
    ready.lease.assert_owned()


class LockedInterrupt(KeyboardInterrupt):
    def __setattr__(self, name, value):
        raise KeyboardInterrupt('diagnostic interrupt')


@pytest.mark.parametrize('stage', ['forward', 'post_load'])
def test_locked_interrupt_preserved_with_owner(ready, monkeypatch, stage):
    interrupt = LockedInterrupt('original')
    def fail(*args, **kwargs):
        raise interrupt
    if stage == 'forward':
        obj = ready.load()
        monkeypatch.setattr(ready.torch, 'tensor', fail)
        def action():
            return obj.forward_cls([[2, 3]])
    else:
        monkeypatch.setattr(ready.factory.model, 'to', fail)
        action = ready.load
    with pytest.raises(LockedInterrupt) as caught:
        action()
    assert caught.value is interrupt
    owner = next(x for x in backend._retained if x._model is ready.factory.model)
    assert owner._state == 'refused'
    owner.close()
    ready.lease.assert_owned()


@pytest.mark.parametrize('interrupt', [False, True])
def test_loader_failure_before_return_has_no_owner(ready, monkeypatch, interrupt):
    original = LockedInterrupt('loader') if interrupt else ValueError('loader')
    def fail(*args, **kwargs):
        raise original
    before = tuple(backend._retained)
    monkeypatch.setattr(ready.factory, 'from_pretrained', fail)
    with pytest.raises(LockedInterrupt if interrupt else backend.BackendRefused) as caught:
        ready.load()
    if interrupt:
        assert caught.value is original
    assert not hasattr(caught.value, 'backend_owner')
    assert tuple(backend._retained) == before
    ready.lease.assert_owned()
