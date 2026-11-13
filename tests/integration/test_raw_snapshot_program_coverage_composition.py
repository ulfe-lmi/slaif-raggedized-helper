"""Real stores, all selected chunks, and independent map construction."""

from dataclasses import asdict
import hashlib
import json

import numpy as np
import pytest

# Existing fixture provider initializes this checkout’s unit helper path.
from test_retrieval_representation_composition import make_bundle
from test_native_tokenizers import make_native
from test_structured_text_composition import create_store
from slaif_raggedized_helper import corpus_embedding_program as program
from slaif_raggedized_helper import derived_store, embedding_batch_store as bs
from slaif_raggedized_helper import embedding_vectors, ingestion_store, raw_snapshot_membership
from slaif_raggedized_helper import raw_snapshot_program_coverage as coverage
from slaif_raggedized_helper import retrieval_representation as rr, schema, vector_codec


def wire(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def digest(data):
    return hashlib.sha256(data).hexdigest()


@pytest.fixture
def actual(tmp_path):
    paths, runtime, make = make_native(tmp_path)
    defs = (
        make(paths[0], "bge_body"),
        make(paths[0], "bge_representation"),
        make(paths[1], "reranker_pair"),
    )
    originals, revisions = create_store(
        tmp_path, "# Heading\n\n" + "alpha beta gamma delta. " * 600
    )
    derived = derived_store.Store(tmp_path / "store")
    try:
        metadata, members, _, _ = make_bundle(originals, revisions[2], defs, runtime)
        bundle_id = ingestion_store.publish(originals, derived, metadata, members)
        bundle = ingestion_store.load(originals, derived, bundle_id)
        p = program.build(originals, derived, (bundle_id,))
        chunks = sorted(bundle.chunks, key=lambda c: c.chunk_id)
        reps = rr.build_many(
            originals, metadata, members, [c.chunk_id for c in chunks], defs[1], runtime
        )
        assert tuple(c.chunk_id for c in chunks) == tuple(x for b in p.batches for x in b.chunk_ids)
        scope = bundle.scope.model_dump(mode="json")
        partition = schema.fingerprint(
            dict(schema=1, corpus=scope["corpus"], version=scope["version"], labels=scope["labels"])
        )
        scope_hash = schema.fingerprint(dict(kind="embedding-source-scope-v1", scope=scope))[7:]
        policy_hash = schema.fingerprint(
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
            representation_policy_fingerprint=policy_hash,
            normalization_policy_id=embedding_vectors.POLICY_ID,
        )
        records, outputs = [], []
        by_id = {r.chunk_id: r for r in reps}
        for batch in p.batches:
            selected = [by_id[c] for c in batch.chunk_ids]
            matrix = np.zeros((len(selected), 1024), dtype="<f4")
            for i in range(len(selected)):
                matrix[i, i] = 1
            enc = vector_codec.encode(matrix, bs.POLICY)
            rows = [
                dict(
                    chunk_id=r.chunk_id,
                    revision_id=r.revision_id,
                    extraction_id=r.extraction_id,
                    representation_id=r.representation_id,
                    rendered_sha256=r.rendered_sha256,
                    source_scope_sha256=scope_hash,
                    input_sha256=r.count.input_sha256,
                    token_count=r.count.count,
                )
                for r in selected
            ]
            obj = dict(
                schema=1,
                kind="embedding-batch-v1",
                dependencies=deps,
                rows=rows,
                vector_container_sha256=enc.container_sha256,
                vector_payload_sha256=enc.payload_sha256,
                codec_policy_fingerprint=bs.POLICY.fingerprint(),
            )
            meta = wire(obj)
            container = bs.publish(derived, meta, enc.container)
            outputs.append(
                dict(
                    batch_index=batch.batch_index,
                    container_id=container,
                    metadata_sha256=digest(meta),
                )
            )
            for i, row in enumerate(rows):
                records.append(
                    dict(
                        row,
                        partition_id=partition,
                        bundle_container_id=bundle_id,
                        bundle_metadata_sha256=digest(bundle.metadata_json),
                        batch_container_id=container,
                        batch_metadata_sha256=digest(meta),
                        batch_row=i,
                        execution_fingerprint=deps["execution_fingerprint"],
                    )
                )
        records.sort(key=lambda r: (r["partition_id"], r["chunk_id"], r["representation_id"]))
        for i, row in enumerate(records):
            row.update(ordinal=i, partition_row=i)
        mapping = dict(
            schema=1,
            kind="slaif-raw-row-map-v1",
            space_id=deps["space_id"],
            definition_fingerprint="sha256:" + deps["definition_fingerprint"],
            representation_policy_fingerprint=policy_hash,
            chunk_policy_fingerprint=chunks[0].policy_id[7:],
            normalization_policy_id=deps["normalization_policy_id"],
            rows=records,
        )
        declaration = {k: v for k, v in mapping.items() if k != "rows"}
        declaration["kind"] = "slaif-raw-row-map-build-declaration-v1"
        locator = dict(
            schema=1,
            kind="slaif-raw-program-output-selection-v1",
            source_program_id=p.source_program_id,
            outputs=outputs,
        )
        yield originals, derived, p, declaration, locator, mapping
    finally:
        derived.close()
        originals.close()


def test_actual_positive(actual):
    originals, derived, p, declaration, locator, mapping = actual
    result = coverage.build(originals, derived, p.program_bytes, wire(declaration), wire(locator))
    assert result.map_bytes == wire(mapping)
    assert result.row_count == len(mapping["rows"]) == p.row_count
    assert result.batch_count == p.batch_count
    assert result.active_bundle_ids == (mapping["rows"][0]["bundle_container_id"],)
    membership = raw_snapshot_membership.build(
        originals, derived, result.map_bytes, result.active_bundle_ids, ()
    )
    assert membership
    assert derived.load(locator["outputs"][0]["container_id"])
    assert ingestion_store.load(originals, derived, result.active_bundle_ids[0])


def test_actual_negative(actual, monkeypatch):
    originals, derived, p, declaration, locator, mapping = actual
    good = coverage.build(originals, derived, p.program_bytes, wire(declaration), wire(locator))
    assert good.map_bytes == wire(mapping)

    def refused(value):
        with pytest.raises(coverage.CoverageError):
            coverage.build(originals, derived, p.program_bytes, wire(declaration), wire(value))

    import copy

    for mutate in (
        lambda x: x["outputs"].pop(),
        lambda x: x["outputs"].append(copy.deepcopy(x["outputs"][0])),
        lambda x: x["outputs"][0].update(batch_index=1),
        lambda x: x["outputs"][0].update(container_id="f" * 64),
        lambda x: x["outputs"][0].update(metadata_sha256="f" * 64),
    ):
        bad = copy.deepcopy(locator)
        mutate(bad)
        refused(bad)
    snapshot = derived.load(locator["outputs"][0]["container_id"])
    obj = derived_store._parse(snapshot.manifest)["metadata"]
    obj["dependencies"]["inventory_id"] = "e" * 64
    replacement = bs.publish(derived, wire(obj), snapshot.members[0].data)
    bad = copy.deepcopy(locator)
    bad["outputs"][0].update(container_id=replacement, metadata_sha256=digest(wire(obj)))
    # A single batch has no peer dependency to compare; row-builder validates its declared subset.
    # Alter source binding as well, so this is an independently invalid stored output.
    obj["rows"][0]["source_scope_sha256"] = "e" * 64
    replacement = bs.publish(derived, wire(obj), snapshot.members[0].data)
    bad["outputs"][0].update(container_id=replacement, metadata_sha256=digest(wire(obj)))
    refused(bad)
    original_validate = program.validate
    calls = 0
    blob = next((originals.root / "blobs").iterdir())
    saved = blob.read_bytes()

    def corrupt_at_final(*args):
        nonlocal calls
        calls += 1
        if calls == 2:
            blob.write_bytes(b"corrupt")
        return original_validate(*args)

    try:
        monkeypatch.setattr(program, "validate", corrupt_at_final)
        refused(locator)
        assert calls == 2
    finally:
        blob.write_bytes(saved)
    monkeypatch.setattr(program, "validate", original_validate)
    vector_path = originals.root / "derived" / "v1" / "objects" / obj["vector_container_sha256"]
    vector_saved = vector_path.read_bytes()
    calls = 0

    def corrupt_vector_at_final(*args):
        nonlocal calls
        calls += 1
        fresh = original_validate(*args)
        if calls == 2:
            vector_path.write_bytes(b"corrupt")
        return fresh

    try:
        monkeypatch.setattr(program, "validate", corrupt_vector_at_final)
        refused(locator)
        assert calls == 2
    finally:
        vector_path.write_bytes(vector_saved)


def test_supplement_multisource_and_foreign(tmp_path):
    """Planned only: two selected sources and one real foreign source."""
    import copy

    paths, runtime, make = make_native(tmp_path)
    defs = (
        make(paths[0], "bge_body"),
        make(paths[0], "bge_representation"),
        make(paths[1], "reranker_pair"),
    )
    originals, revisions = create_store(
        tmp_path, "# Heading\n\n" + "alpha beta gamma delta. " * 600
    )
    derived = derived_store.Store(tmp_path / "store")
    try:
        bundles = {}
        for revision in revisions:
            metadata, members, _, _ = make_bundle(originals, revision, defs, runtime)
            bundle_id = ingestion_store.publish(originals, derived, metadata, members)
            bundle = ingestion_store.load(originals, derived, bundle_id)
            reps = rr.build_many(
                originals,
                metadata,
                members,
                [c.chunk_id for c in sorted(bundle.chunks, key=lambda c: c.chunk_id)],
                defs[1],
                runtime,
            )
            bundles[bundle_id] = (bundle, {r.chunk_id: r for r in reps})
        assert len(bundles) == 3
        selected = tuple(sorted(bundles)[:2])
        foreign = next(key for key in bundles if key not in selected)
        p = program.build(originals, derived, selected)
        foreign_program = program.build(originals, derived, (foreign,))
        assert p.batch_count >= 2 and foreign_program.batch_count >= 1
        policy_hash = schema.fingerprint(
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
            representation_policy_fingerprint=policy_hash,
            normalization_policy_id=embedding_vectors.POLICY_ID,
        )

        def publish(batch, dependencies):
            bundle, reps = bundles[batch.bundle_id]
            scope = bundle.scope.model_dump(mode="json")
            scope_hash = schema.fingerprint(dict(kind="embedding-source-scope-v1", scope=scope))[7:]
            selected_reps = [reps[c] for c in batch.chunk_ids]
            matrix = np.zeros((len(selected_reps), 1024), dtype="<f4")
            for index in range(len(selected_reps)):
                matrix[index, index] = 1
            enc = vector_codec.encode(matrix, bs.POLICY)
            rows = [
                dict(
                    chunk_id=r.chunk_id,
                    revision_id=r.revision_id,
                    extraction_id=r.extraction_id,
                    representation_id=r.representation_id,
                    rendered_sha256=r.rendered_sha256,
                    source_scope_sha256=scope_hash,
                    input_sha256=r.count.input_sha256,
                    token_count=r.count.count,
                )
                for r in selected_reps
            ]
            obj = dict(
                schema=1,
                kind="embedding-batch-v1",
                dependencies=dependencies,
                rows=rows,
                vector_container_sha256=enc.container_sha256,
                vector_payload_sha256=enc.payload_sha256,
                codec_policy_fingerprint=bs.POLICY.fingerprint(),
            )
            metadata = wire(obj)
            container = bs.publish(derived, metadata, enc.container)
            # Verify the alternative output itself is typed and valid before using it.
            bs.load(derived, container, metadata)
            return dict(
                batch_index=batch.batch_index,
                container_id=container,
                metadata_sha256=digest(metadata),
            )

        outputs = [publish(batch, deps) for batch in p.batches]
        foreign_output = publish(foreign_program.batches[0], deps)
        different_deps = dict(deps, inventory_id="e" * 64)
        differing_output = publish(p.batches[1], different_deps)
        chunk = bundles[selected[0]][0].chunks[0]
        declaration = dict(
            schema=1,
            kind="slaif-raw-row-map-build-declaration-v1",
            space_id=deps["space_id"],
            definition_fingerprint="sha256:" + deps["definition_fingerprint"],
            representation_policy_fingerprint=policy_hash,
            chunk_policy_fingerprint=chunk.policy_id[7:],
            normalization_policy_id=deps["normalization_policy_id"],
        )
        locator = dict(
            schema=1,
            kind="slaif-raw-program-output-selection-v1",
            source_program_id=p.source_program_id,
            outputs=outputs,
        )

        def call(value):
            return coverage.build(
                originals, derived, p.program_bytes, wire(declaration), wire(value)
            )

        complete = call(locator)
        assert complete.active_bundle_ids == selected
        assert complete.row_count == sum(len(bundles[b][0].chunks) for b in selected)
        assert complete.batch_count == len(outputs) == p.batch_count
        actual_ids = {
            row.chunk_id for row in coverage.raw_snapshot_rows.parse(complete.map_bytes).rows
        }
        expected_ids = {c.chunk_id for b in selected for c in bundles[b][0].chunks}
        assert actual_ids == expected_ids
        mutations = []
        missing = copy.deepcopy(locator)
        missing["outputs"].pop()
        mutations.append(missing)
        duplicate = copy.deepcopy(locator)
        duplicate["outputs"][1]["batch_index"] = 0
        mutations.append(duplicate)
        reordered = copy.deepcopy(locator)
        reordered["outputs"][0], reordered["outputs"][1] = (
            reordered["outputs"][1],
            reordered["outputs"][0],
        )
        mutations.append(reordered)
        swapped = copy.deepcopy(locator)
        for key in ("container_id", "metadata_sha256"):
            swapped["outputs"][0][key], swapped["outputs"][1][key] = (
                swapped["outputs"][1][key],
                swapped["outputs"][0][key],
            )
        mutations.append(swapped)
        wrong_source = copy.deepcopy(locator)
        for key in ("container_id", "metadata_sha256"):
            wrong_source["outputs"][0][key] = foreign_output[key]
        mutations.append(wrong_source)
        wrong_deps = copy.deepcopy(locator)
        for key in ("container_id", "metadata_sha256"):
            wrong_deps["outputs"][1][key] = differing_output[key]
        mutations.append(wrong_deps)
        for bad in mutations:
            with pytest.raises(coverage.CoverageError):
                call(bad)
    finally:
        derived.close()
        originals.close()
