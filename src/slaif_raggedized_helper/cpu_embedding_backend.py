"""Resident fixed CPU CLS transformer; admission precedes framework import."""

import importlib.metadata
import json
import math
import os
import stat
import sys
from pathlib import Path

from . import embedding_artifacts, embedding_space


class BackendRefused(ValueError):
    """The requested operation did not satisfy the backend contract."""


_PINS = {
    "torch": "2.10.0+cpu",
    "transformers": "4.51.3",
    "tokenizers": "0.21.4",
    "safetensors": "0.5.3",
    "huggingface-hub": "0.30.2",
    "numpy": "2.2.6",
}


def _framework():
    if sys.version_info[:2] != (3, 12):
        raise ValueError
    if any(importlib.metadata.version(k) != v for k, v in _PINS.items()):
        raise ValueError
    import torch
    import transformers

    if torch.__version__ != _PINS["torch"] or transformers.__version__ != _PINS["transformers"]:
        raise ValueError
    return torch, transformers.XLMRobertaModel


def _closed_tree(root, files):
    expected_files = {f.path for f in files}
    dirs = {str(p) for f in expected_files for p in Path(f).parents if str(p) != "."}
    seen_files, seen_dirs = set(), set()
    budget = len(expected_files) + len(dirs)

    def scan(directory):
        nonlocal budget
        with os.scandir(directory) as entries:
            for entry in entries:
                budget -= 1
                if budget < 0:
                    raise ValueError
                path = Path(entry.path)
                relative = path.relative_to(root).as_posix()
                st = entry.stat(follow_symlinks=False)
                if relative in dirs:
                    if not stat.S_ISDIR(st.st_mode):
                        raise ValueError
                    seen_dirs.add(relative)
                    scan(path)
                elif relative in expected_files:
                    if not stat.S_ISREG(st.st_mode):
                        raise ValueError
                    seen_files.add(relative)
                else:
                    raise ValueError

    scan(root)
    if seen_files != expected_files or seen_dirs != dirs:
        raise ValueError


def _model_ok(model, torch):
    if model.training is not False:
        raise ValueError
    floating = False
    for parameter in model.parameters():
        if parameter.device.type != "cpu":
            raise ValueError
        if parameter.is_floating_point():
            floating = True
            if parameter.dtype != torch.float32:
                raise ValueError
    if not floating:
        raise ValueError
    for buffer in model.buffers():
        if buffer.device.type != "cpu" or (
            buffer.is_floating_point() and buffer.dtype != torch.float32
        ):
            raise ValueError


class CPUEmbeddingBackend:
    """Own one admitted local model until close; return raw FP32 CLS rows."""

    def __init__(
        self, manifest_bytes, artifact_root, definition, tokenizer_definition, expected_inventory_id
    ):
        self._model = None
        try:
            self.space = embedding_space.admit(
                manifest_bytes,
                artifact_root,
                definition,
                tokenizer_definition,
                expected_inventory_id,
            )
            inv = embedding_artifacts.verify_artifacts(manifest_bytes, artifact_root)
            if inv.inventory_id != self.space.inventory_id:
                raise ValueError
            weight = next(f for f in inv.files if f.role == "weights")
            expected = (
                "model.safetensors"
                if inv.checkpoint_format == "safetensors"
                else "pytorch_model.bin"
            )
            if weight.path != expected:
                raise ValueError
            root = Path(artifact_root)
            _closed_tree(root, inv.files)
            fd = embedding_artifacts._root(root)
            try:
                config_fd = embedding_artifacts._open_file(fd, "config.json")
                try:
                    with os.fdopen(config_fd, "rb") as stream:
                        config = json.load(stream)
                finally:
                    pass
            finally:
                os.close(fd)
            vocab, pad = config.get("vocab_size"), config.get("pad_token_id")
            if (
                type(vocab) is not int
                or not 1 <= vocab <= 10000000
                or type(pad) is not int
                or not 0 <= pad < vocab
            ):
                raise ValueError
            # Verify again immediately at the load boundary under the protected-tree assumption.
            if (
                embedding_artifacts.verify_artifacts(manifest_bytes, root).inventory_id
                != inv.inventory_id
            ):
                raise ValueError
            _closed_tree(root, inv.files)
            torch, factory = _framework()
            model = factory.from_pretrained(
                str(root),
                local_files_only=True,
                trust_remote_code=False,
                token=False,
                weights_only=True,
                use_safetensors=inv.checkpoint_format == "safetensors",
                torch_dtype=torch.float32,
                device_map=None,
            )
            self._model = model
            model.to(device="cpu", dtype=torch.float32)
            model.eval()
            _model_ok(model, torch)
            if (
                type(model.config.vocab_size) is not int
                or model.config.vocab_size != vocab
                or type(model.config.pad_token_id) is not int
                or model.config.pad_token_id != pad
            ):
                raise ValueError
            self._torch, self._vocab, self._pad = torch, vocab, pad
        except Exception:
            self.close()
            raise BackendRefused("backend refused") from None

    def forward_cls(self, sequences):
        try:
            if (
                self._model is None
                or type(sequences) not in (list, tuple)
                or not 1 <= len(sequences) <= 128
            ):
                raise ValueError
            if any(
                type(row) not in (list, tuple) or not 2 <= len(row) <= 1024 for row in sequences
            ):
                raise ValueError
            if sum(map(len, sequences)) > 131072 or any(
                type(token) is not int or not 0 <= token < self._vocab
                for row in sequences
                for token in row
            ):
                raise ValueError
            torch, model = self._torch, self._model
            _model_ok(model, torch)
            width = max(map(len, sequences))
            ids = torch.tensor(
                [list(row) + [self._pad] * (width - len(row)) for row in sequences],
                dtype=torch.long,
                device="cpu",
            )
            mask = torch.tensor(
                [[1] * len(row) + [0] * (width - len(row)) for row in sequences],
                dtype=torch.long,
                device="cpu",
            )
            with torch.inference_mode(), torch.autocast(device_type="cpu", enabled=False):
                output = model(input_ids=ids, attention_mask=mask, return_dict=True)
            _model_ok(model, torch)
            hidden = output.last_hidden_state
            if (
                tuple(hidden.shape) != (len(sequences), width, 1024)
                or hidden.device.type != "cpu"
                or hidden.dtype != torch.float32
            ):
                raise ValueError
            rows = hidden[:, 0, :].tolist()
            if len(rows) != len(sequences) or any(
                len(row) != 1024 or any(type(x) is not float or not math.isfinite(x) for x in row)
                for row in rows
            ):
                raise ValueError
            return tuple(tuple(row) for row in rows)
        except Exception:
            self.close()
            raise BackendRefused("backend refused") from None

    def close(self):
        self._model = None
