from dataclasses import replace
from pathlib import Path
import secrets
import traceback
import warnings

import pytest

from slaif_raggedized_helper import embedding_batch_plan as plan, native_tokenizers as nt
from slaif_raggedized_helper import retrieval_representation as rr, schema
from slaif_raggedized_helper.source_admission import OriginalStore


@pytest.fixture
def inputs(tmp_path):
    d = schema.EmbeddingDefinition(
        model_name="BAAI/bge-m3",
        checkpoint_revision="a" * 40,
        checkpoint_sha256="b" * 64,
        tokenizer_revision="a" * 40,
        pooling="cls",
        dimensions=1024,
    )
    t = nt.Definition(
        tmp_path / "tokenizer.json", "c" * 64, "0.21.4", "bge_representation", "a" * 40, "identity"
    )
    return [
        object.__new__(OriginalStore),
        b"{}",
        tuple((n, b"{}") for n in ("blocks", "coverage", "chunks", "neighbors", "receipts")),
        ["a"],
        b"{}",
        tmp_path,
        d,
        t,
        "d" * 64,
        nt.Runtime(Path("/runtime"), Path("/packages"), "python3.12"),
    ]


def test_preflight_refuses_before_admission(inputs, monkeypatch):
    called = []

    def stop(*args, **kwargs):
        called.append(1)
        raise RuntimeError

    monkeypatch.setattr(plan.embedding_space, "admit", stop)
    monkeypatch.setattr(plan.retrieval_representation, "build_many", stop)
    invalid = []
    for index, value in [
        (0, None),
        (1, b""),
        (2, ()),
        (3, []),
        (3, ["a", "a"]),
        (3, ["x" * 72]),
        (3, [str(i) for i in range(129)]),
        (1, b"x" * (256 * 1024 + 1)),
        (4, b"x" * (256 * 1024 + 1)),
        (3, iter(["a"])),
        (4, b""),
        (8, "bad"),
        (9, object()),
    ]:
        x = inputs.copy()
        x[index] = value
        invalid.append(x)
    for field, value in [
        ("pooling", "mean"),
        ("dimensions", True),
        ("model_name", object()),
        ("query_prefix", "prefix"),
    ]:
        x = inputs.copy()
        x[6] = inputs[6].model_copy(update={field: value})
        invalid.append(x)
    for field, value in [
        ("model_revision", "b" * 40),
        ("preprocessing", "raw"),
        ("role", "bge_body"),
    ]:
        x = inputs.copy()
        x[7] = replace(inputs[7], **{field: value})
        invalid.append(x)
    for x in invalid:
        with pytest.raises(plan.PlanError):
            plan.build(*x)
    for kwargs in (
        {"purpose": "other"},
        {"purpose": True},
        {"representation_policy": rr.Policy(max_tokens=0)},
        {"batch_policy": rr.BatchPolicy(max_items=0)},
    ):
        with pytest.raises(plan.PlanError):
            plan.build(*inputs, **kwargs)
    mutated = rr.Policy()
    object.__setattr__(mutated, "separator", "secret")
    with pytest.raises(plan.PlanError):
        plan.build(*inputs, representation_policy=mutated)
    mutated_batch = rr.BatchPolicy()
    object.__setattr__(mutated_batch, "max_items", True)
    with pytest.raises(plan.PlanError):
        plan.build(*inputs, batch_policy=mutated_batch)
    assert not called
    with pytest.raises(plan.PlanError):
        plan.build(*inputs)
    assert called == [1]
    inputs[3] = [str(i) for i in range(128)]
    with pytest.raises(plan.PlanError):
        plan.build(*inputs)
    assert called == [1, 1]


def test_privacy_on_unchecked_fields(inputs, monkeypatch):
    marker = secrets.token_hex(24)
    inputs[6] = inputs[6].model_copy(update={"model_name": marker})
    monkeypatch.setattr(plan.embedding_space, "admit", lambda *a: pytest.fail("admission reached"))
    with warnings.catch_warnings(record=True) as seen:
        with pytest.raises(plan.PlanError) as exc:
            plan.build(*inputs)
    assert marker not in "".join(traceback.format_exception(exc.value))
    assert marker not in repr(seen)


def test_preallocated_large_inputs_are_bounded(inputs, monkeypatch):
    import tracemalloc

    called = []

    def admission(*args):
        called.append(1)
        raise ValueError

    monkeypatch.setattr(plan.embedding_space, "admit", admission)
    huge = "x" * 1_000_000
    cases = [
        (3, [huge]),
        (5, "/" + huge),
        (5, Path("/" + huge)),
        (7, replace(inputs[7], artifact=Path("/" + huge))),
        (9, nt.Runtime(Path("/" + huge), Path("/packages"), "python3.12")),
    ]
    for index, value in cases:
        candidate = inputs.copy()
        candidate[index] = value
        tracemalloc.start()
        try:
            with pytest.raises(plan.PlanError):
                plan.build(*candidate)
            _, peak = tracemalloc.get_traced_memory()
        finally:
            tracemalloc.stop()
        assert peak < 100_000
    assert not called
    with pytest.raises(plan.PlanError):
        plan.build(*inputs)
    assert called == [1]


def test_prefix_conversion_is_strict():
    for value in ("0" * 64, "f" * 64):
        assert plan._unprefix("sha256:" + value) == value
    for value in (
        "0" * 64,
        "sha256:" + "A" * 64,
        "sha256:" + "0" * 63,
        "sha256:" + "0" * 65,
        "SHA256:" + "0" * 64,
    ):
        with pytest.raises(ValueError):
            plan._unprefix(value)
