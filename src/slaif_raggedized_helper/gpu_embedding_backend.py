"""Private fixed-profile GPU raw CLS backend; caller owns rights and device lease."""

import hashlib
import importlib
import importlib.metadata
import json
import os
import platform
import threading
import tomllib
import uuid
from pathlib import Path

from . import (embedding_artifacts, embedding_space, gpu_device_lease, gpu_worker_protocol,
               native_tokenizers)
from .cpu_embedding_backend import _closed_tree
from .schema import EmbeddingDefinition


class BackendRefused(ValueError):
    """The backend contract was not met."""


_PROFILE_HASH = 'd3f47d3d2943759967a95694017f32e20b8a29ee7de4df790465a402bc17c334'
_PINS = {'torch': '2.14.0+cu126', 'transformers': '5.22.2', 'tokenizers': '0.23.1',
         'safetensors': '0.8.0', 'huggingface-hub': '1.31.0', 'numpy': '2.5.4'}
# Retain owners on failure until explicit local close; this does not prove physical drain.
_retained = []


def _framework():
    if platform.python_implementation() != 'CPython' or os.sys.version_info[:2] != (3, 12):
        raise ValueError
    lock = gpu_worker_protocol._profile_path(Path(__file__).resolve().parent)
    data = native_tokenizers._read_artifact(lock, 65536)
    if hashlib.sha256(data).hexdigest() != _PROFILE_HASH:
        raise ValueError
    packages = tomllib.loads(data.decode())['package']
    selected = {p['name']: p['version'] for p in packages if 'registry' in p.get('source', {})}
    if len(selected) != 57 or any(selected.get(k) != v for k, v in _PINS.items()):
        raise ValueError
    if any(importlib.metadata.version(k) != v for k, v in selected.items()):
        raise ValueError
    modules = {k: importlib.import_module(k.replace('-', '_')) for k in _PINS}
    if any(modules[k].__version__ != v for k, v in _PINS.items()):
        raise ValueError
    return modules['torch'], modules['transformers'].XLMRobertaModel


def _device(torch, expected):
    if os.environ.get('CUDA_VISIBLE_DEVICES') != expected:
        raise ValueError
    count = torch.cuda.device_count() if torch.cuda.is_available() is True else None
    if type(count) is not int or count != 1:
        raise ValueError
    value = torch.cuda.get_device_properties  # Only the pinned public property binding.
    prop = value(0).uuid
    if type(prop) is not torch._C._CUuuid:
        raise ValueError
    raw = prop.bytes
    if type(raw) is not list or len(raw) != 16 or any(
        type(v) is not int or not 0 <= v <= 255 for v in raw
    ):
        raise ValueError
    if 'GPU-' + str(uuid.UUID(bytes=bytes(raw))) != expected:
        raise ValueError


def _model_ok(model, torch, vocab, pad):
    if model.training is not False:
        raise ValueError
    config = model.config
    if (type(config.vocab_size) is not int or config.vocab_size != vocab
            or type(config.pad_token_id) is not int or config.pad_token_id != pad
            or type(config.hidden_size) is not int or config.hidden_size != 1024
            or config.model_type != 'xlm-roberta'):
        raise ValueError
    floating = False
    for parameter in model.parameters():
        if parameter.device.type != 'cuda' or parameter.device.index != 0:
            raise ValueError
        if parameter.is_floating_point():
            floating = True
            if parameter.dtype != torch.float16:
                raise ValueError
    if not floating:
        raise ValueError
    for buffer in model.buffers():
        if (buffer.device.type != 'cuda' or buffer.device.index != 0
                or (buffer.is_floating_point() and buffer.dtype != torch.float16)):
            raise ValueError


class GPUEmbeddingBackend:
    """One local model under a caller-owned, live device lease; raw FP32 CLS only."""

    def __init__(self, manifest_bytes, artifact_root, definition, tokenizer_definition,
                 expected_inventory_id, lease, expected_device_uuid):
        self._model = None
        self._state = 'initializing'
        self._guard = threading.Lock()
        self._pid = os.getpid()
        try:
            if (type(manifest_bytes) is not bytes or len(manifest_bytes) > 262144
                    or type(definition) is not EmbeddingDefinition
                    or type(tokenizer_definition) is not native_tokenizers.Definition
                    or type(lease) is not gpu_device_lease.DeviceLease
                    or type(expected_device_uuid) is not str or len(expected_device_uuid) != 40
                    or gpu_device_lease._UUID.fullmatch(expected_device_uuid) is None):
                raise ValueError
            if (type(artifact_root) not in (str, type(Path()))
                    or not 1 <= len(str(artifact_root)) <= 4096
                    or type(expected_inventory_id) is not str or len(expected_inventory_id) != 64
                    or any(type(value) is not str or len(value) > limit for value, limit in (
                        (definition.model_name, 256), (definition.checkpoint_revision, 40),
                        (definition.checkpoint_sha256, 64), (definition.tokenizer_revision, 40),
                        (definition.pooling, 16), (tokenizer_definition.sha256, 64),
                        (tokenizer_definition.backend_version, 32),
                        (tokenizer_definition.role, 64), (tokenizer_definition.model_revision, 40),
                        (tokenizer_definition.preprocessing, 64)))
                    or definition.query_prefix is not None or definition.normalize is not True
                    or type(definition.dimensions) is not int or definition.dimensions != 1024
                    or type(tokenizer_definition.artifact) is not type(Path())
                    or len(str(tokenizer_definition.artifact)) > 4096):
                raise ValueError
            lease.assert_owned()
            record = gpu_device_lease._live.get(id(lease))
            if record is None or record[0] is not lease or record[3] != expected_device_uuid:
                raise ValueError
            self._lease, self._lease_identity = lease, record[:8]
            self._device_uuid = expected_device_uuid
            self._definition, self._tokenizer_definition = definition, tokenizer_definition
            self._snapshot = self._definition_snapshot()
            self.space = embedding_space.admit(manifest_bytes, artifact_root, definition,
                                               tokenizer_definition, expected_inventory_id)
            self._stable()
            inv = embedding_artifacts.verify_artifacts(manifest_bytes, artifact_root)
            if inv.inventory_id != self.space.inventory_id:
                raise ValueError
            weight = next(f for f in inv.files if f.role == 'weights')
            if weight.path != ('model.safetensors' if inv.checkpoint_format == 'safetensors'
                               else 'pytorch_model.bin'):
                raise ValueError
            root = Path(artifact_root)
            _closed_tree(root, inv.files)
            fd = embedding_artifacts._root(root)
            try:
                config_fd = embedding_artifacts._open_file(fd, 'config.json')
                with os.fdopen(config_fd, 'rb') as stream:
                    config = json.load(stream)
            finally:
                os.close(fd)
            vocab, pad = config.get('vocab_size'), config.get('pad_token_id')
            if (type(vocab) is not int or not 1 <= vocab <= 10000000
                    or type(pad) is not int or not 0 <= pad < vocab):
                raise ValueError
            self._vocab, self._pad = vocab, pad
            self._stable()
            if (embedding_artifacts.verify_artifacts(manifest_bytes, root).inventory_id
                    != inv.inventory_id):
                raise ValueError
            _closed_tree(root, inv.files)
            if os.environ.get('CUDA_VISIBLE_DEVICES') != self._device_uuid:
                raise ValueError
            torch, factory = _framework()
            self._torch = torch
            self._stable()
            _device(torch, self._device_uuid)
            model = factory.from_pretrained(
                str(root), local_files_only=True, trust_remote_code=False, token=False,
                weights_only=True, use_safetensors=inv.checkpoint_format == 'safetensors',
                torch_dtype=torch.float16,
            )
            self._model = model
            model.to(device='cuda:0', dtype=torch.float16)
            model.eval()
            _model_ok(model, torch, vocab, pad)
            self._stable()
            _device(torch, self._device_uuid)
            self._state = 'open'
        except BaseException as exc:
            self._state = 'refused'
            if self._model is not None:
                _retained.append(self)
                if not isinstance(exc, Exception):
                    try:
                        exc.backend_owner = self
                    except BaseException:
                        pass  # Preserve the original interruption.
            if isinstance(exc, Exception):
                error = BackendRefused('backend refused')
                if self._model is not None:
                    error.backend_owner = self
                raise error from None
            raise

    def _definition_snapshot(self):
        d, t = self._definition, self._tokenizer_definition
        fields = ((d.model_name, 256), (d.checkpoint_revision, 40),
                  (d.checkpoint_sha256, 64), (d.tokenizer_revision, 40), (d.pooling, 16),
                  (t.sha256, 64), (t.backend_version, 32), (t.role, 64),
                  (t.model_revision, 40), (t.preprocessing, 64))
        if (any(type(value) is not str or len(value) > limit for value, limit in fields)
                or d.query_prefix is not None or d.normalize is not True
                or type(d.dimensions) is not int or d.dimensions != 1024
                or type(t.artifact) is not type(Path())):
            raise ValueError
        path = str(t.artifact)
        if len(path) > 4096:
            raise ValueError
        return tuple(value for value, _ in fields) + (
            d.normalize, d.query_prefix, d.dimensions, path
        )

    def _stable(self):
        if os.getpid() != self._pid or self._definition_snapshot() != self._snapshot:
            raise ValueError
        self._lease.assert_owned()
        record = gpu_device_lease._live.get(id(self._lease))
        if (record is None or record[:8] != self._lease_identity
                or type(self._device_uuid) is not str or self._device_uuid != record[3]):
            raise ValueError

    def forward_cls(self, sequences):
        if not self._guard.acquire(blocking=False):
            error = BackendRefused('backend busy')
            if self._model is not None:
                error.backend_owner = self
            raise error
        try:
            if self._state != 'open' or type(sequences) not in (list, tuple):
                raise ValueError
            outer = sequences[:129]
            if not 1 <= len(outer) <= 128 or any(type(row) not in (list, tuple) for row in outer):
                raise ValueError
            sequences = tuple(tuple(row[:1025]) for row in outer)
            if (any(not 2 <= len(row) <= 1024 for row in sequences)
                    or sum(map(len, sequences)) > 131072
                    or any(type(token) is not int or not 0 <= token < self._vocab
                           for row in sequences for token in row)):
                raise ValueError
            self._stable()
            torch, model = self._torch, self._model
            _device(torch, self._device_uuid)
            _model_ok(model, torch, self._vocab, self._pad)
            width = max(map(len, sequences))
            ids = torch.tensor([list(row) + [self._pad] * (width - len(row)) for row in sequences],
                               dtype=torch.long, device='cuda:0')
            mask = torch.tensor([[1] * len(row) + [0] * (width - len(row)) for row in sequences],
                                dtype=torch.long, device='cuda:0')
            with torch.inference_mode(), torch.autocast(device_type='cuda', enabled=False):
                output = model(input_ids=ids, attention_mask=mask, return_dict=True)
            self._stable()
            _device(torch, self._device_uuid)
            _model_ok(model, torch, self._vocab, self._pad)
            hidden = output.last_hidden_state
            if (tuple(hidden.shape) != (len(sequences), width, 1024)
                    or hidden.device.type != 'cuda' or hidden.device.index != 0
                    or hidden.dtype != torch.float16):
                raise ValueError
            cls = hidden[:, 0, :].to(device='cpu', dtype=torch.float32)
            if (tuple(cls.shape) != (len(sequences), 1024) or cls.device.type != 'cpu'
                    or cls.dtype != torch.float32):
                raise ValueError
            rows = cls.tolist()
            import math
            if (type(rows) is not list or len(rows) != len(sequences)
                    or any(type(row) is not list or len(row) != 1024
                           or any(type(x) is not float or not math.isfinite(x) for x in row)
                           for row in rows)):
                raise ValueError
            self._stable()
            _device(torch, self._device_uuid)
            return tuple(tuple(row) for row in rows)
        except BaseException as exc:
            if self._state == 'open':
                self._state = 'refused'
                _retained.append(self)
            if self._model is not None:
                if not isinstance(exc, Exception):
                    try:
                        exc.backend_owner = self
                    except BaseException:
                        pass  # Preserve the original interruption.
            if isinstance(exc, Exception):
                error = BackendRefused('backend refused')
                if self._model is not None:
                    error.backend_owner = self
                raise error from None
            raise
        finally:
            self._guard.release()

    def close(self):
        if not self._guard.acquire(blocking=False):
            error = BackendRefused('backend busy')
            if self._model is not None:
                error.backend_owner = self
            raise error
        try:
            if os.getpid() != self._pid:
                error = BackendRefused('backend forked')
                if self._model is not None:
                    error.backend_owner = self
                raise error
            self._model = None
            _retained[:] = [owner for owner in _retained if owner is not self]
            self._state = 'closed'
        finally:
            self._guard.release()
