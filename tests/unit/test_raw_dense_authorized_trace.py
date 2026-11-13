"""Source-only synthetic checks; no actual catalog execution is claimed."""

from dataclasses import FrozenInstanceError, asdict
import json
from pathlib import Path

import pytest

from slaif_raggedized_helper import raw_dense_search as dense


def test_root_encoding_vectors():
    oracle = json.loads(
        (
            Path(__file__).parents[2] / "docs/parallel/raw-dense-authorized-trace-oracle.json"
        ).read_text()
    )
    for vector in oracle["vectors"]:
        assert dense._trace_hash(vector["object"], lambda: None) == vector["trace_id"]
    from slaif_raggedized_helper import provenance_records as p

    # Encoding vectors only: these are supplied synthetic authorities, not rights evidence.
    for vector in oracle["authority_vectors"]:
        grant_data, restriction_data = vector["pair"]

        def tuple_fields(data):
            return {
                key: tuple(value) if isinstance(value, list) else value
                for key, value in data.items()
            }

        grants = (
            p.Grants.model_validate(tuple_fields(grant_data)) if grant_data is not None else None
        )
        restrictions = (
            p.Restrictions.model_validate(restriction_data)
            if restriction_data is not None
            else None
        )
        budget = [0, 3]
        grants = dense._authority(
            grants, p.Grants, ("corpora", "versions", "labels"), False, budget
        )
        restrictions = dense._authority(
            restrictions, p.Restrictions, ("corpora", "versions"), True, budget
        )
        assert dense._authority_hash(grants, restrictions) == vector["sha256"]


def test_private_markers_and_legacy_result():
    result = dense.DenseResult(
        "s", "c", "q", "SUPPLIED_UNVERIFIED", "NOT_QUALIFIED", (), (), 0, 0, 0, False, False
    )
    assert result.trace is None and asdict(result)["trace"] is None
    trace = dense.DenseTrace(
        "id", "s", "c", "q", "space", "def", "policy", "exec", "auth", 1, 1, (), (), (), ()
    )
    assert (
        trace.input_origin,
        trace.qualification,
        trace.authorization_status,
        trace.execution_status,
    ) == ("SUPPLIED_UNVERIFIED", "NOT_QUALIFIED", "SUPPLIED_SCOPE_CHECKS_ONLY", "NOT_ATTESTED")
    assert "auth" not in repr(trace)
    with pytest.raises(FrozenInstanceError):
        trace.k = 2
    dense._validate_trace((), (), (), (), (), 1, 1)


def test_synthetic_structure_refusals():
    row = dense.DenseTraceRow(0, "p", "c", "r", "x")
    count = dense.PartitionCount("p", 1, 1, 1)
    good = dense.DensePartitionTrace("p", (0,), (0,), (0,), (0,))
    dense._validate_trace((row,), (good,), (0,), (0,), (count,), 1, 1)
    for bad in (
        dense.DensePartitionTrace("p", (0,), (1,), (1,), (0,)),
        dense.DensePartitionTrace("p", (0,), (0, 0), (0,), (0,)),
    ):
        with pytest.raises(ValueError):
            dense._validate_trace((row,), (bad,), (0,), (0,), (count,), 1, 1)


def test_bad_flag_before_lower_admission(tmp_path, monkeypatch):
    import numpy as np
    from slaif_raggedized_helper import derived_store
    from slaif_raggedized_helper.source_admission import OriginalStore

    originals = OriginalStore(tmp_path / "store")
    derived = derived_store.Store(tmp_path / "store")
    calls = []

    def sentinel(*args, **kwargs):
        calls.append(1)
        raise ValueError("sentinel")

    monkeypatch.setattr(dense.catalog, "load_catalog", sentinel)
    args = dict(
        query_space_id="a" * 64,
        query_definition_fingerprint="sha256:" + "b" * 64,
        query_policy_id="c" * 64,
        query_execution_fingerprint="d" * 64,
        grants=None,
    )
    payload = np.eye(1, 1024, dtype="<f4").tobytes()
    try:
        for invalid in (1, None, "true", 0):
            with pytest.raises(dense.DenseSearchError):
                dense.search(
                    originals,
                    derived,
                    "/valid",
                    "sha256:" + "0" * 64,
                    payload,
                    trace=invalid,
                    **args,
                )
            assert calls == []
        for valid in (False, True):
            with pytest.raises(dense.DenseSearchError):
                dense.search(
                    originals, derived, "/valid", "sha256:" + "0" * 64, payload, trace=valid, **args
                )
        assert calls == [1, 1]
    finally:
        derived.close()
        originals.close()


def test_mocked_empty_final_deadline_and_interrupt(tmp_path, monkeypatch):
    """Mocked lower admission: deadline and exception guard, not actual trace proof."""
    from types import SimpleNamespace
    import numpy as np
    from slaif_raggedized_helper import derived_store
    from slaif_raggedized_helper.source_admission import OriginalStore

    originals = OriginalStore(tmp_path / "store")
    derived = derived_store.Store(tmp_path / "store")
    embedding = dict(
        space_id="a" * 64,
        definition_fingerprint="sha256:" + "b" * 64,
        query_policy_fingerprint="c" * 64,
        query_execution_fingerprint="d" * 64,
    )
    source = SimpleNamespace(
        core_bytes=json.dumps({"embedding": embedding}).encode(),
        row_map_bytes=b"",
        rows=(),
        catalog_id="sha256:" + "e" * 64,
    )
    monkeypatch.setattr(dense.catalog, "load_catalog", lambda *a, **kw: source)
    monkeypatch.setattr(dense.raw_snapshot_manifest, "parse", lambda _: None)
    monkeypatch.setattr(dense.raw_snapshot_rows, "parse", lambda _: SimpleNamespace(rows=()))
    clock = [100.0]
    monkeypatch.setattr(dense.time, "monotonic", lambda: clock[0])
    original_result = dense.DenseResult

    def late(*args, **kwargs):
        result = original_result(*args, **kwargs)
        clock[0] += 2
        return result

    args = dict(
        query_space_id=embedding["space_id"],
        query_definition_fingerprint=embedding["definition_fingerprint"],
        query_policy_id=embedding["query_policy_fingerprint"],
        query_execution_fingerprint=embedding["query_execution_fingerprint"],
        grants=None,
        deadline_ms=1000,
    )
    payload = np.eye(1, 1024, dtype="<f4").tobytes()
    try:
        for enabled in (False, True):
            with monkeypatch.context() as patch:
                patch.setattr(dense, "DenseResult", late)
                with pytest.raises(dense.DenseSearchError):
                    dense.search(
                        originals,
                        derived,
                        "/valid",
                        "sha256:" + "0" * 64,
                        payload,
                        trace=enabled,
                        **args,
                    )
        marker = KeyboardInterrupt()

        def interrupt(*args, **kwargs):
            raise marker

        monkeypatch.setattr(dense.catalog, "load_catalog", interrupt)
        with pytest.raises(KeyboardInterrupt) as caught:
            dense.search(originals, derived, "/valid", "sha256:" + "0" * 64, payload, **args)
        assert caught.value is marker
    finally:
        originals.close()
        derived.close()
