"""Cheap refusal boundaries, with observable forbidden loader calls."""

import numpy as np
import pytest

from slaif_raggedized_helper import derived_store, provenance_records as p
from slaif_raggedized_helper import raw_dense_search as dense
from slaif_raggedized_helper.source_admission import OriginalStore


def test_preflight_never_loads(tmp_path, monkeypatch):
    originals = OriginalStore(tmp_path / "store")
    derived = derived_store.Store(tmp_path / "store")
    calls = []
    monkeypatch.setattr(dense.catalog, "load_catalog", lambda *a, **kw: calls.append(1))
    payload = np.eye(1, 1024, dtype="<f4").tobytes()
    good = dict(
        query_space_id="a" * 64,
        query_definition_fingerprint="sha256:" + "b" * 64,
        query_policy_id="c" * 64,
        query_execution_fingerprint="d" * 64,
        grants=p.Grants(schema_version=1, corpora=("x",), versions=("v",), labels=()),
    )
    bad_grants = [
        good["grants"].model_copy(update={"corpora": ("\ud800",)}),
        good["grants"].model_copy(update={"corpora": ("x",) * 129}),
        good["grants"].model_copy(update={"corpora": ["x"]}),
        good["grants"].model_copy(update={"labels": ("x" * 65537,)}),
        good["grants"].model_copy(update={"extra": "x"}),
    ]
    try:
        for updates in [
            dict(k=True),
            dict(deadline_ms=0),
            dict(partition_cap=61),
            dict(query_space_id="sha256:" + "a" * 64),
            dict(query_definition_fingerprint="b" * 64),
            *[dict(grants=g) for g in bad_grants],
        ]:
            with pytest.raises(dense.DenseSearchError):
                dense.search(
                    originals, derived, "/valid", "sha256:" + "0" * 64, payload, **(good | updates)
                )
        for value in (b"", bytes(4096), np.full(1024, np.nan, dtype="<f4").tobytes()):
            with pytest.raises(dense.DenseSearchError):
                dense.search(originals, derived, "/valid", "sha256:" + "0" * 64, value, **good)
        assert calls == []
    finally:
        derived.close()
        originals.close()


def test_scope_version_none_denies():
    scope = p.Scope(
        schema_version=1,
        document_id="d",
        revision_id="r",
        corpus="c",
        version=None,
        labels=(),
        processing_approved=True,
        redistribution_rights="allowed",
    )
    grants = p.Grants(schema_version=1, corpora=("c",), versions=("v",), labels=())
    assert not dense._allowed(scope, grants, None)


def test_large_extra_and_combined_authority_preflight(tmp_path, monkeypatch):
    import tracemalloc

    originals = OriginalStore(tmp_path / "store")
    derived = derived_store.Store(tmp_path / "store")
    calls = []
    monkeypatch.setattr(dense.catalog, "load_catalog", lambda *a, **kw: calls.append(1))
    payload = np.eye(1, 1024, dtype="<f4").tobytes()
    extra = p.Grants(schema_version=1, corpora=(), versions=(), labels=())
    extra.__dict__.update({f"extra{i}": "x" for i in range(100000)})
    astral = "\U0001f600" * 32768
    grants = p.Grants(schema_version=1, corpora=(astral,), versions=(), labels=())
    restrictions = p.Restrictions(schema_version=1, corpora=(astral,), versions=None)
    args = dict(
        query_space_id="a" * 64,
        query_definition_fingerprint="sha256:" + "b" * 64,
        query_policy_id="c" * 64,
        query_execution_fingerprint="d" * 64,
    )
    try:
        tracemalloc.start()
        with pytest.raises(dense.DenseSearchError):
            dense.search(
                originals, derived, "/valid", "sha256:" + "0" * 64, payload, grants=extra, **args
            )
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        assert peak < 200000
        with pytest.raises(dense.DenseSearchError):
            dense.search(
                originals,
                derived,
                "/valid",
                "sha256:" + "0" * 64,
                payload,
                grants=grants,
                restrictions=restrictions,
                **args,
            )
        assert calls == []
    finally:
        derived.close()
        originals.close()
