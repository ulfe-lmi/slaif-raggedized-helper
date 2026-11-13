"""Actual private dense stage observations over the existing three-row fixture."""

from dataclasses import asdict

import numpy as np
import pytest

from slaif_raggedized_helper import raw_dense_search as dense
from test_raw_dense_search_composition import call, grants, source  # noqa: F401


def test_restricted_actual(source, monkeypatch):  # noqa: F811
    seen = []
    score = dense._score

    def observe(matrix, query):
        seen.append(matrix.copy())
        return score(matrix, query)

    monkeypatch.setattr(dense, "_score", observe)
    baseline = call(source, grants("one"), partition_cap=1)
    result = call(source, grants("one"), partition_cap=1, trace=True)
    assert asdict(baseline) | {"trace": None} == asdict(result) | {"trace": None}
    assert len(seen) == 2 and all(m.shape == (2, 1024) and not m[:, 2].any() for m in seen)
    trace = result.trace
    assert len(trace.rows) == 2 and len(trace.partitions) == 1
    assert trace.partitions[0].ranked_ordinals == tuple(r.ordinal for r in trace.rows)
    assert trace.selected_ordinals == trace.partitions[0].ranked_ordinals[:1]
    assert trace.returned_ordinals == tuple(h.ordinal for h in result.hits)
    assert set(r.ordinal for r in trace.rows).isdisjoint(
        {r["ordinal"] for r in source[5] if r["partition_id"] != trace.partitions[0].partition_id}
    )
    empty = call(source, None, trace=True)
    assert empty.trace.rows == empty.trace.partitions == ()


def test_ties_actual(source):  # noqa: F811
    originals, derived, root, ident, core, rows, _ = source
    vector = np.zeros(1024, dtype="<f4")
    vector[:3] = np.float32(1 / np.sqrt(3))
    e = core["embedding"]
    result = dense.search(
        originals,
        derived,
        root,
        ident,
        vector.tobytes(),
        query_space_id=e["space_id"],
        query_definition_fingerprint=e["definition_fingerprint"],
        query_policy_id=e["query_policy_fingerprint"],
        query_execution_fingerprint=e["query_execution_fingerprint"],
        grants=grants("one", "two"),
        k=1,
        partition_cap=1,
        trace=True,
    )
    expected = []
    for part in sorted({r["partition_id"] for r in rows}):
        ranked = sorted(
            (r for r in rows if r["partition_id"] == part),
            key=lambda r: (r["chunk_id"], r["revision_id"], r["representation_id"]),
        )
        actual = next(p for p in result.trace.partitions if p.partition_id == part)
        assert actual.ranked_ordinals == tuple(r["ordinal"] for r in ranked)
        expected.append(ranked[0])
    expected.sort(key=lambda r: (r["chunk_id"], r["revision_id"], r["representation_id"]))
    assert result.trace.selected_ordinals == tuple(r["ordinal"] for r in expected)
    assert result.trace.returned_ordinals == (expected[0]["ordinal"],)
    for part in result.trace.partitions:
        assert part.returned_ordinals == tuple(
            h.ordinal for h in result.hits if h.partition_id == part.partition_id
        )


def test_final_refusals_actual(source, monkeypatch):  # noqa: F811
    original_allowed = dense._allowed
    original_reader = dense.p.reader_allows
    eligible_scopes = []
    phase = [False]
    loader = dense.catalog.load_catalog
    loads = []

    def capture(scope, grants_value, restrictions):
        allowed = original_allowed(scope, grants_value, restrictions)
        if allowed:
            eligible_scopes.append(scope)
        return allowed

    def load(*args, **kwargs):
        result = loader(*args, **kwargs)
        loads.append(1)
        if len(loads) == 2:
            phase[0] = True
        return result

    def reject_uncapped(scope, grants_value, restrictions):
        if phase[0] and scope is eligible_scopes[1]:
            return False
        return original_reader(scope, grants_value, restrictions)

    with monkeypatch.context() as patch:
        patch.setattr(dense, "_allowed", capture)
        patch.setattr(dense.catalog, "load_catalog", load)
        patch.setattr(dense.p, "reader_allows", reject_uncapped)
        with pytest.raises(dense.DenseSearchError):
            call(source, grants("one"), partition_cap=1, trace=True)
        assert phase[0] and len(eligible_scopes) == 2

    original_result = dense.DenseResult
    clock = [dense.time.monotonic()]

    def delayed_result(*args, **kwargs):
        value = original_result(*args, **kwargs)
        clock[0] += 2
        return value

    with monkeypatch.context() as patch:
        patch.setattr(dense.time, "monotonic", lambda: clock[0])
        patch.setattr(dense, "DenseResult", delayed_result)
        for enabled in (False, True):
            with pytest.raises(dense.DenseSearchError):
                call(source, grants("one"), deadline_ms=1000, trace=enabled)

    loads.clear()

    def corrupt(*args, **kwargs):
        loads.append(1)
        if len(loads) == 2:
            path = source[6] / "map"
            path.chmod(0o600)
            path.write_bytes(b"corrupt")
            path.chmod(0o400)
        return loader(*args, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(dense.catalog, "load_catalog", corrupt)
        with pytest.raises(dense.DenseSearchError):
            call(source, grants("one"), trace=True)
        assert len(loads) == 2
