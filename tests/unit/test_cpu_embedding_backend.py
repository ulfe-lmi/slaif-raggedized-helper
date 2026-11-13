import json
from types import SimpleNamespace

import pytest

from slaif_raggedized_helper import cpu_embedding_backend as backend, embedding_artifacts
from test_embedding_artifacts import setup_tree, write_config
from test_embedding_space import fixture


class Tensor:
    def __init__(self, data=None, dtype="fp32", device="cpu", shape=None):
        self.data, self.dtype = data, dtype
        self.device = SimpleNamespace(type=device)
        self.shape = shape

    def is_floating_point(self):
        return self.dtype in ("fp32", "fp16")

    def __getitem__(self, key):
        assert key == (slice(None), 0, slice(None))
        return Tensor([row[0] for row in self.data])

    def tolist(self):
        return self.data


class Context:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class Torch:
    float32 = "fp32"
    long = "long"

    def __init__(self):
        self.allocations = []

    def tensor(self, data, **kwargs):
        self.allocations.append((data, kwargs))
        return Tensor(data, kwargs["dtype"])

    def inference_mode(self):
        return Context()

    def autocast(self, **kwargs):
        assert kwargs == {"device_type": "cpu", "enabled": False}
        return Context()


class Model:
    def __init__(self):
        self.training = True
        self.parameter = Tensor()
        self.buffer = Tensor()
        self.config = SimpleNamespace(vocab_size=20, pad_token_id=1)
        self.calls = []
        self.shape = None
        self.nan = False

    def to(self, **kwargs):
        assert kwargs == {"device": "cpu", "dtype": "fp32"}
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
        ids = kwargs["input_ids"].data
        data = [[[float(token)] * 1024 for token in row] for row in ids]
        if self.nan:
            data[0][0][0] = float("nan")
        return SimpleNamespace(
            last_hidden_state=Tensor(data, shape=self.shape or (len(ids), len(ids[0]), 1024))
        )


class Factory:
    def __init__(self, model):
        self.model, self.calls = model, []

    def from_pretrained(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        return self.model


def make_tree(root):
    m = setup_tree(root)
    old = next(f for f in m["files"] if f["role"] == "weights")
    (root / old["path"]).rename(root / "model.safetensors")
    old["path"] = "model.safetensors"
    write_config(
        root,
        m,
        "config",
        {"model_type": "xlm-roberta", "hidden_size": 1024, "vocab_size": 20, "pad_token_id": 1},
    )
    raw = json.dumps(m).encode()
    inv = embedding_artifacts.verify_artifacts(raw, root)
    # Build the real space definitions from the fixture's convention.
    from slaif_raggedized_helper.native_tokenizers import Definition
    from slaif_raggedized_helper.schema import EmbeddingDefinition

    files = {f.role: f for f in inv.files}
    d = EmbeddingDefinition(
        model_name="BAAI/bge-m3",
        checkpoint_revision=inv.model_revision,
        checkpoint_sha256=files["weights"].sha256,
        tokenizer_revision=inv.model_revision,
        pooling="cls",
        dimensions=1024,
    )
    t = Definition(
        root / "tokenizer.json",
        files["tokenizer"].sha256,
        "0.21.4",
        "bge_representation",
        inv.model_revision,
        "identity",
    )
    return m, raw, inv, d, t


@pytest.fixture
def ready(tmp_path, monkeypatch):
    root = tmp_path / "tree"
    m, raw, inv, d, t = make_tree(root)
    torch, model = Torch(), Model()
    factory = Factory(model)
    monkeypatch.setattr(backend, "_framework", lambda: (torch, factory))

    def load():
        return backend.CPUEmbeddingBackend(raw, root, d, t, inv.inventory_id)

    return root, m, raw, inv, d, t, torch, model, factory, load


def test_load_once_forward_and_close(ready):
    root, _, _, _, _, _, torch, model, factory, load = ready
    obj = load()
    assert factory.calls == [
        (
            (str(root),),
            dict(
                local_files_only=True,
                trust_remote_code=False,
                token=False,
                weights_only=True,
                use_safetensors=True,
                torch_dtype="fp32",
                device_map=None,
            ),
        )
    ]
    result = obj.forward_cls([[3, 4], [5, 6, 7]])
    assert result == ((3.0,) * 1024, (5.0,) * 1024)
    assert torch.allocations[0][0] == [[3, 4, 1], [5, 6, 7]]
    assert torch.allocations[1][0] == [[1, 1, 0], [1, 1, 1]]
    obj.forward_cls([[8, 9]])
    assert len(factory.calls) == 1 and len(model.calls) == 2
    obj.close()
    obj.close()
    with pytest.raises(backend.BackendRefused):
        obj.forward_cls([[1, 2]])


def test_bad_tree_and_metadata_precede_factory(ready):
    root, _, raw, inv, d, t, _, _, factory, load = ready
    (root / "extra.py").write_text("unsafe")
    with pytest.raises(backend.BackendRefused):
        load()
    (root / "extra.py").unlink()
    (root / "config.json").write_text("{}")
    with pytest.raises(backend.BackendRefused):
        backend.CPUEmbeddingBackend(raw, root, d, t, inv.inventory_id)
    assert not factory.calls


@pytest.mark.parametrize(
    "state", ["parameter_gpu", "parameter_fp16", "buffer_gpu", "buffer_fp16", "training"]
)
def test_model_state_refused(ready, state):
    *_, model, factory, load = ready
    obj = load()
    if state == "parameter_gpu":
        model.parameter.device.type = "cuda"
    elif state == "parameter_fp16":
        model.parameter.dtype = "fp16"
    elif state == "buffer_gpu":
        model.buffer.device.type = "cuda"
    elif state == "buffer_fp16":
        model.buffer.dtype = "fp16"
    else:
        model.training = True
    with pytest.raises(backend.BackendRefused):
        obj.forward_cls([[1, 2]])
    assert len(factory.calls) == 1 and not model.calls


@pytest.mark.parametrize(
    "rows", [[], [[True, 1]], [[-1, 1]], [[20, 1]], [[1]], [[1] * 1025], [[1, 2]] * 129, "bad"]
)
def test_invalid_before_tensor_allocation(ready, rows):
    *_, torch, model, _, load = ready
    obj = load()
    with pytest.raises(backend.BackendRefused):
        obj.forward_cls(rows)
    assert not torch.allocations and not model.calls


@pytest.mark.parametrize("failure", ["shape", "nan"])
def test_output_refusal(ready, failure):
    *_, model, _, load = ready
    obj = load()
    if failure == "shape":
        model.shape = (1, 2, 3)
    else:
        model.nan = True
    with pytest.raises(backend.BackendRefused):
        obj.forward_cls([[1, 2]])


def test_version_refused_before_import(monkeypatch):
    monkeypatch.setattr(backend.sys, "version_info", (3, 12))
    monkeypatch.setattr(backend.importlib.metadata, "version", lambda _: "wrong")
    with pytest.raises(ValueError):
        backend._framework()


def test_legacy_synthetic_refused(tmp_path, monkeypatch):
    root = tmp_path / "tree"
    _, raw, inv, d, t = fixture(root)
    monkeypatch.setattr(backend, "_framework", lambda: pytest.fail("factory reached"))
    with pytest.raises(backend.BackendRefused):
        backend.CPUEmbeddingBackend(raw, root, d, t, inv.inventory_id)


def test_bad_model_at_load_cleans_up(ready):
    *_, model, factory, load = ready
    model.buffer.device.type = "cuda"
    with pytest.raises(backend.BackendRefused):
        load()
    assert len(factory.calls) == 1


def test_schema2_bin_fixed_format(tmp_path, monkeypatch):
    root = tmp_path / "tree"
    m, _, _, d, t = make_tree(root)
    weight = next(f for f in m["files"] if f["role"] == "weights")
    (root / weight["path"]).rename(root / "pytorch_model.bin")
    weight["path"] = "pytorch_model.bin"
    m.update(schema=2, checkpoint_format="pytorch-state-dict")
    raw = json.dumps(m).encode()
    inv = embedding_artifacts.verify_artifacts(raw, root)
    factory = Factory(Model())
    monkeypatch.setattr(backend, "_framework", lambda: (Torch(), factory))
    obj = backend.CPUEmbeddingBackend(raw, root, d, t, inv.inventory_id)
    assert factory.calls[0][1]["use_safetensors"] is False
    obj.close()


def test_failure_closes_instance(ready):
    *_, load = ready
    obj = load()
    with pytest.raises(backend.BackendRefused):
        obj.forward_cls([[True, 1]])
    with pytest.raises(backend.BackendRefused):
        obj.forward_cls([[1, 2]])


def test_unknown_directory_refused_without_descending(ready, monkeypatch):
    root, _, _, inv, *_ = ready
    extra = root / "unexpected"
    extra.mkdir()
    original = backend.os.scandir
    scanned = []

    def guarded(path):
        scanned.append(path)
        assert path != extra
        return original(path)

    monkeypatch.setattr(backend.os, "scandir", guarded)
    with pytest.raises(ValueError):
        backend._closed_tree(root, inv.files)
    assert extra not in scanned


def test_false_return_dict_configuration(ready, monkeypatch):
    root, m, _, _, d, t, torch, model, _, _ = ready
    write_config(
        root,
        m,
        "config",
        {
            "model_type": "xlm-roberta",
            "hidden_size": 1024,
            "vocab_size": 20,
            "pad_token_id": 1,
            "return_dict": False,
        },
    )
    raw = json.dumps(m).encode()
    inv = embedding_artifacts.verify_artifacts(raw, root)

    class ConfiguredModel(Model):
        def __call__(self, **kwargs):
            result = super().__call__(**kwargs)
            return result if kwargs.get("return_dict") is True else (result.last_hidden_state,)

    configured = ConfiguredModel()
    monkeypatch.setattr(backend, "_framework", lambda: (torch, Factory(configured)))
    obj = backend.CPUEmbeddingBackend(raw, root, d, t, inv.inventory_id)
    assert obj.forward_cls([[2, 3]]) == ((2.0,) * 1024,)
    assert configured.calls[0]["return_dict"] is True
    obj.close()
