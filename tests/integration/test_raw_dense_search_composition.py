"""Actual versioned original, stored batches and catalog through dense scoring."""

from dataclasses import FrozenInstanceError, asdict
import hashlib
import json

import numpy as np
import pytest

from slaif_raggedized_helper import derived_store, embedding_batch_store as bs
from slaif_raggedized_helper import embedding_vectors, ingestion_store, provenance_records as p
from slaif_raggedized_helper import raw_dense_search as search
from slaif_raggedized_helper import retrieval_representation as rr, schema, vector_codec
from slaif_raggedized_helper.source_admission import OriginalStore, parse_manifest
from test_retrieval_representation_composition import make_bundle
from test_native_tokenizers import make_native
from test_raw_snapshot_directory_composition import materialize
from test_raw_snapshot_files_composition import complete
from test_raw_snapshot_rows import enc
from test_raw_snapshot_source_rows_composition import actual, wire  # noqa: F401


@pytest.fixture
def source(tmp_path):
    paths, runtime, make = make_native(tmp_path)
    defs = (
        make(paths[0], "bge_body"),
        make(paths[0], "bge_representation"),
        make(paths[1], "reranker_pair"),
    )
    root = tmp_path / "original-input"
    root.mkdir()
    text = "# Heading\n\n" + "alpha beta gamma delta. " * 600
    raw = text.encode()
    (root / "a").write_bytes(raw)
    (root / "b").write_bytes(raw)
    base = dict(
        logical_id="a",
        relative_path="a",
        display_uri="urn:owned",
        corpus="one",
        version="v1",
        access_labels=[],
        processing_approved=True,
        redistribution_rights="allowed",
        media_type="text/markdown",
        size=len(raw),
        sha256=hashlib.sha256(raw).hexdigest(),
    )
    sources = parse_manifest(
        json.dumps(
            dict(
                schema_version=1,
                sources=[
                    base,
                    dict(
                        base,
                        logical_id="b",
                        relative_path="b",
                        corpus="two",
                        access_labels=["secret"],
                    ),
                ],
            )
        ).encode()
    ).sources
    originals = OriginalStore(tmp_path / "store")
    revisions = [originals.admit(root, s) for s in sources]
    derived = derived_store.Store(tmp_path / "store")
    try:
        ph = schema.fingerprint(
            dict(
                kind="embedding-representation-policy-v1",
                policy=asdict(rr.Policy()),
                batch_policy=asdict(rr.BatchPolicy()),
            )
        )[7:]
        deps = dict(
            space_id="a" * 64,
            inventory_id="b" * 64,
            definition_fingerprint="c" * 64,
            execution_fingerprint="d" * 64,
            tokenizer_sha256=defs[1].sha256,
            representation_policy_fingerprint=ph,
            normalization_policy_id=embedding_vectors.POLICY_ID,
        )
        rows, bundles = [], []
        chunk_policy = None
        for i, rev in enumerate(revisions):
            metadata, members, _, built = make_bundle(originals, rev, defs, runtime)
            bid = ingestion_store.publish(originals, derived, metadata, members)
            bundle = ingestion_store.load(originals, derived, bid)
            chunks = sorted(built.chunks, key=lambda c: c.chunk_id)[: 2 if i == 0 else 1]
            assert len(chunks) == (2 if i == 0 else 1)
            reps = rr.build_many(
                originals, metadata, members, [c.chunk_id for c in chunks], defs[1], runtime
            )
            scope = bundle.scope.model_dump(mode="json")
            partition = schema.fingerprint(
                dict(
                    schema=1,
                    corpus=scope["corpus"],
                    version=scope["version"],
                    labels=scope["labels"],
                )
            )
            scope_hash = schema.fingerprint(dict(kind="embedding-source-scope-v1", scope=scope))[7:]
            matrix = np.zeros((len(reps), 1024), dtype="<f4")
            for j in range(len(reps)):
                matrix[j, j if i == 0 else 2] = 1
            vector = vector_codec.encode(matrix, bs.POLICY)
            records = [
                dict(
                    chunk_id=rep.chunk_id,
                    revision_id=rep.revision_id,
                    extraction_id=rep.extraction_id,
                    representation_id=rep.representation_id,
                    rendered_sha256=rep.rendered_sha256,
                    source_scope_sha256=scope_hash,
                    input_sha256=rep.count.input_sha256,
                    token_count=rep.count.count,
                )
                for rep in reps
            ]
            batch_meta = wire(
                dict(
                    schema=1,
                    kind="embedding-batch-v1",
                    dependencies=deps,
                    rows=records,
                    vector_container_sha256=vector.container_sha256,
                    vector_payload_sha256=vector.payload_sha256,
                    codec_policy_fingerprint=bs.POLICY.fingerprint(),
                )
            )
            batch = bs.publish(derived, batch_meta, vector.container)
            for j, record in enumerate(records):
                rows.append(
                    dict(
                        record,
                        partition_id=partition,
                        bundle_container_id=bid,
                        bundle_metadata_sha256=hashlib.sha256(bundle.metadata_json).hexdigest(),
                        batch_container_id=batch,
                        batch_metadata_sha256=hashlib.sha256(batch_meta).hexdigest(),
                        batch_row=j,
                        execution_fingerprint=deps["execution_fingerprint"],
                    )
                )
            bundles.append(bid)
            chunk_policy = chunks[0].policy_id[7:]
        rows.sort(key=lambda r: (r["partition_id"], r["chunk_id"], r["representation_id"]))
        positions = {}
        for ordinal, row in enumerate(rows):
            part = row["partition_id"]
            row.update(ordinal=ordinal, partition_row=positions.get(part, 0))
            positions[part] = row["partition_row"] + 1
        mapping = dict(
            schema=1,
            kind="slaif-raw-row-map-v1",
            space_id=deps["space_id"],
            definition_fingerprint="sha256:" + deps["definition_fingerprint"],
            representation_policy_fingerprint=ph,
            chunk_policy_fingerprint=chunk_policy,
            normalization_policy_id=deps["normalization_policy_id"],
            rows=rows,
        )
        core, payloads = complete(originals, derived, mapping, tuple(bundles))
        root_path, target, ident = materialize(tmp_path, enc(core), payloads)
        yield originals, derived, str(root_path), ident, core, rows, target
    finally:
        derived.close()
        originals.close()


def call(source, grants, **kwargs):
    originals, derived, root, ident, core, _, _ = source
    vector = np.zeros(1024, dtype="<f4")
    vector[:3] = [0.6, 0, 0.8]
    e = core["embedding"]
    return search.search(
        originals,
        derived,
        root,
        ident,
        vector.tobytes(),
        query_space_id=e["space_id"],
        query_definition_fingerprint=e["definition_fingerprint"],
        query_policy_id=e["query_policy_fingerprint"],
        query_execution_fingerprint=e["query_execution_fingerprint"],
        grants=grants,
        **kwargs,
    )


def grants(*corpora):
    return p.Grants(schema_version=1, corpora=corpora, versions=("v1",), labels=("secret",))


def test_positive_caps_and_privacy(source, monkeypatch):
    observed = []
    real_score = search._score

    def observe(matrix, query):
        observed.append(matrix.copy())
        return real_score(matrix, query)

    monkeypatch.setattr(search, "_score", observe)
    caller_grants = grants("one")
    result = call(source, caller_grants)
    object.__setattr__(caller_grants, "corpora", ("two",))
    assert result.eligible == 2
    with pytest.raises(FrozenInstanceError):
        result.eligible = 0
    with pytest.raises(FrozenInstanceError):
        result.hits[0].rank = 9
    assert (result.eligible, result.selected, result.returned) == (2, 2, 2)
    assert [round(h.score, 4) for h in result.hits] == [0.6, 0.0]
    assert len(observed) == 1 and not observed[0][:, 2].any()
    observed.clear()
    all_result = call(source, grants("one", "two"), k=1, partition_cap=1)
    assert (all_result.eligible, all_result.selected, all_result.returned) == (3, 2, 1)
    assert all_result.partition_cap_applied and all_result.global_cap_applied
    assert round(all_result.hits[0].score, 4) == 0.8
    assert len(observed) == 2
    assert (
        all_result.hits[0].representation_id
        == source[5][all_result.hits[0].ordinal]["representation_id"]
    )
    observed.clear()
    assert call(source, None).hits == ()
    assert not observed
    denied = p.Restrictions(schema_version=1, corpora=("two",), versions=None)
    assert call(source, grants("one", "two"), restrictions=denied).eligible == 1
    observed.clear()
    with monkeypatch.context() as patch:
        patch.setattr(search, "_allowed", lambda *_: True)
        with pytest.raises(search.DenseSearchError):
            call(source, grants("one"))
    assert any(m[:, 2].any() for m in observed)
    observed.clear()
    assert call(source, grants("one")).eligible == 2
    assert not observed[0][:, 2].any()


def test_final_source_refusal(source, monkeypatch):
    loader = search.catalog.load_catalog
    calls = []

    def mutate(*args, **kwargs):
        calls.append(1)
        if len(calls) == 2:
            path = source[6] / "map"
            path.chmod(0o600)
            path.write_bytes(b"corrupt")
            path.chmod(0o400)
        return loader(*args, **kwargs)

    monkeypatch.setattr(search.catalog, "load_catalog", mutate)
    with pytest.raises(search.DenseSearchError):
        call(source, grants("one"))
    assert len(calls) == 2


def test_query_domains_ties_and_snapshot_refusal(source, monkeypatch):
    originals, derived, root, ident, core, rows, _ = source
    vector = np.zeros(1024, dtype="<f4")
    vector[1] = 1
    e = core["embedding"]
    args = dict(
        query_space_id=e["space_id"],
        query_definition_fingerprint=e["definition_fingerprint"],
        query_policy_id=e["query_policy_fingerprint"],
        query_execution_fingerprint=e["query_execution_fingerprint"],
        grants=grants("one", "two"),
    )
    result = search.search(originals, derived, root, ident, vector.tobytes(), **args)
    assert result.hits[0].score == 1
    tied = result.hits[1:]
    assert all(h.score == 0 for h in tied)
    assert [h.chunk_id for h in tied] == sorted(h.chunk_id for h in tied)
    assert [h.rank for h in result.hits] == [1, 2, 3]
    assert sum(c.eligible for c in result.allowed_partition_counts) == 3
    calls = []
    monkeypatch.setattr(search, "_score", lambda *a: calls.append(1))
    for key in (
        "query_space_id",
        "query_definition_fingerprint",
        "query_policy_id",
        "query_execution_fingerprint",
    ):
        replacement = ("sha256:" if key == "query_definition_fingerprint" else "") + "f" * 64
        with pytest.raises(search.DenseSearchError):
            search.search(
                originals, derived, root, ident, vector.tobytes(), **(args | {key: replacement})
            )
    with pytest.raises(search.DenseSearchError):
        search.search(originals, derived, root, "sha256:" + "0" * 64, vector.tobytes(), **args)
    assert calls == []
    assert len(rows) == 3


def test_empty_actual(source, tmp_path, monkeypatch):
    originals, derived, _, _, core, rows, _ = source
    mapping = json.loads(
        search.catalog.load_catalog(originals, derived, source[2], source[3]).row_map_bytes
    )
    mapping["rows"] = []
    empty_core, payloads = complete(originals, derived, mapping, ())
    (tmp_path / "empty").mkdir(mode=0o700)
    root, _, ident = materialize(tmp_path / "empty", enc(empty_core), payloads)
    calls = []
    monkeypatch.setattr(search, "_score", lambda *a: calls.append(1))
    e = empty_core["embedding"]
    vector = np.eye(1, 1024, dtype="<f4").tobytes()
    args = dict(
        query_space_id=e["space_id"],
        query_definition_fingerprint=e["definition_fingerprint"],
        query_policy_id=e["query_policy_fingerprint"],
        query_execution_fingerprint=e["query_execution_fingerprint"],
        grants=None,
    )
    result = search.search(originals, derived, str(root), ident, vector, **args)
    assert result.hits == result.allowed_partition_counts == ()
    assert (result.eligible, result.selected, result.returned) == (0, 0, 0)
    with pytest.raises(search.DenseSearchError):
        search.search(
            originals,
            derived,
            str(root),
            ident,
            vector,
            **(args | {"grants": grants("one").model_copy(update={"labels": ("\ud800",)})}),
        )
    assert calls == []
    assert len(rows) == 3 and core["row_count"] == 3


def test_unversioned_actual_denies(actual, tmp_path, monkeypatch):  # noqa: F811
    from test_raw_snapshot_catalog_composition import prepare

    originals, derived, _, _, root, _, ident = prepare(actual, tmp_path)
    cat = search.catalog.load_catalog(originals, derived, str(root), ident)
    scope = p.admit_record("Scope", cat.rows[0].scope_bytes)
    assert scope.version is None
    e = json.loads(cat.core_bytes)["embedding"]
    calls = []
    monkeypatch.setattr(search, "_score", lambda *a: calls.append(1))
    result = search.search(
        originals,
        derived,
        str(root),
        ident,
        np.eye(1, 1024, dtype="<f4").tobytes(),
        query_space_id=e["space_id"],
        query_definition_fingerprint=e["definition_fingerprint"],
        query_policy_id=e["query_policy_fingerprint"],
        query_execution_fingerprint=e["query_execution_fingerprint"],
        grants=p.Grants(
            schema_version=1, corpora=(scope.corpus,), versions=("v1",), labels=scope.labels
        ),
    )
    assert result.hits == () and result.eligible == 0 and calls == []


def test_actual_deadline_and_interrupt(source, monkeypatch):
    from slaif_raggedized_helper import raw_snapshot_directory as directory

    real_loader = search.catalog.load_catalog
    now = [search.time.monotonic()]
    monkeypatch.setattr(search.time, "monotonic", lambda: now[0])
    calls = []

    def delayed(*args, **kwargs):
        value = real_loader(*args, **kwargs)
        calls.append(value.catalog_id)
        now[0] += 2
        return value

    monkeypatch.setattr(search.catalog, "load_catalog", delayed)
    scored = []
    monkeypatch.setattr(search, "_score", lambda *args: scored.append(1))
    with pytest.raises(search.DenseSearchError):
        call(source, grants("one"), deadline_ms=1000)
    assert len(calls) == 1 and scored == []
    monkeypatch.setattr(search.catalog, "load_catalog", real_loader)
    marker = KeyboardInterrupt()

    def interrupt(*args, **kwargs):
        raise marker

    monkeypatch.setattr(directory, "load_directory", interrupt)
    with pytest.raises(KeyboardInterrupt) as caught:
        call(source, grants("one"))
    assert caught.value is marker and scored == []
