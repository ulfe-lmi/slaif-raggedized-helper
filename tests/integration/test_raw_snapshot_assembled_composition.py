"""One synthetic selected program through rows, current files and private loading."""

import copy
import hashlib
import json
import os
import subprocess
from pathlib import Path

import numpy as np
import pytest

import test_retrieval_representation_composition as provider
import test_native_tokenizers
import test_raw_snapshot_program_coverage_composition as coverage_fixture
from test_raw_snapshot_program_coverage_composition import wire
from test_raw_snapshot_files_composition import complete
from test_raw_snapshot_directory_composition import materialize, restore_owned_directories  # noqa: F401
from slaif_raggedized_helper import ingestion_store, native_tokenizers
from slaif_raggedized_helper import corpus_embedding_program as program_api
from slaif_raggedized_helper import embedding_batch_store as batch_store
from slaif_raggedized_helper import raw_snapshot_dense as dense
from slaif_raggedized_helper import raw_snapshot_directory as directory
from slaif_raggedized_helper import raw_snapshot_files as files
from slaif_raggedized_helper import raw_snapshot_program_coverage as coverage
from slaif_raggedized_helper import raw_snapshot_row_builder as builder
from slaif_raggedized_helper import raw_snapshot_source_rows as source_rows


# Provider initialization and the fixtures must come from this checkout.
_CHECKOUT = Path(__file__).resolve().parents[2]
assert Path(provider.__file__).resolve() == (
    _CHECKOUT / "tests/integration/test_retrieval_representation_composition.py"
)
assert Path(test_native_tokenizers.__file__).resolve() == (
    _CHECKOUT / "tests/unit/test_native_tokenizers.py"
)
assert Path(coverage_fixture.__file__).resolve() == (
    _CHECKOUT / "tests/integration/test_raw_snapshot_program_coverage_composition.py"
)
assert Path(provider.make_bundle.__code__.co_filename).resolve() == (
    Path(provider.__file__).resolve()
)
assert Path(test_native_tokenizers.make_native.__code__.co_filename).resolve() == (
    Path(test_native_tokenizers.__file__).resolve()
)
assert Path(coverage_fixture.actual.__wrapped__.__code__.co_filename).resolve() == (
    Path(coverage_fixture.__file__).resolve()
)


assert Path(complete.__code__.co_filename).resolve() == (
    _CHECKOUT / "tests/integration/test_raw_snapshot_files_composition.py"
)
assert Path(materialize.__code__.co_filename).resolve() == (
    _CHECKOUT / "tests/integration/test_raw_snapshot_directory_composition.py"
)
assert Path(restore_owned_directories.__wrapped__.__code__.co_filename).resolve() == (
    _CHECKOUT / "tests/integration/test_raw_snapshot_directory_composition.py"
)


@pytest.fixture
def actual(tmp_path, monkeypatch):
    """Use cached owned toy bytes only for the explicitly budgeted proof run."""
    if os.environ.get("SLAIF_PDA_CACHED_TOYS") == "1":
        cached = (
            ("/tmp/text-support-v3-aac9pkoo/case/test_actual_source_support0/a.json",
             "1432b17ab7e9e4214568327a62acb0004515b6d23d920c3c8ed1150041f2ee32"),
            ("/tmp/text-support-v3-aac9pkoo/case/test_actual_source_support0/b.json",
             "36583090527cd1a96fb0e9e576053ebece1a8621a7d788fdef6cb380a7e66153"),
        )
        def cached_native(path):
            paths = []
            for index, (source, expected_hash) in enumerate(cached):
                data = Path(source).read_bytes()
                assert hashlib.sha256(data).hexdigest() == expected_hash
                target = path / ("a.json" if index == 0 else "b.json")
                target.write_bytes(data)
                paths.append(target)
            runtime = native_tokenizers.Runtime(
                Path(os.environ["SLAIF_NATIVE_TEST_ROOT"]),
                Path(os.environ["SLAIF_NATIVE_TEST_PACKAGES"]),
                os.environ["SLAIF_NATIVE_TEST_PYTHON"],
            )
            def definition(artifact, role="bge_body"):
                return native_tokenizers.Definition(
                    artifact, hashlib.sha256(artifact.read_bytes()).hexdigest(), "0.21.4",
                    role, "synthetic-revision", "identity",
                )
            return paths, runtime, definition

        monkeypatch.setattr(coverage_fixture, "make_native", cached_native)
        popen = subprocess.Popen
        calls = []
        def bounded_popen(argv, *args, **kwargs):
            assert len(calls) < 2 and argv[0] == "/usr/bin/timeout"
            calls.append(argv[0])
            return popen(argv, *args, **kwargs)
        monkeypatch.setattr(subprocess, "Popen", bounded_popen)
        original_load = ingestion_store.load
        load_counts = {"setup": 0, "test": 0, "teardown": 0}
        phase = {"name": "setup"}
        def bounded_load(*args, **kwargs):
            assert sum(load_counts.values()) < 200
            load_counts[phase["name"]] += 1
            return original_load(*args, **kwargs)
        monkeypatch.setattr(ingestion_store, "load", bounded_load)
        publish_bundle = ingestion_store.publish
        bundle_calls = []
        def bounded_bundle(*args, **kwargs):
            assert len(bundle_calls) < 1
            bundle_calls.append(1)
            return publish_bundle(*args, **kwargs)
        monkeypatch.setattr(ingestion_store, "publish", bounded_bundle)
        publish_batch = batch_store.publish
        batch_calls = []
        def bounded_batch(*args, **kwargs):
            assert len(batch_calls) < 1
            batch_calls.append(1)
            return publish_batch(*args, **kwargs)
        monkeypatch.setattr(batch_store, "publish", bounded_batch)
        build_program = program_api.build
        def bounded_program(originals, derived, bundle_ids, **kwargs):
            assert len(bundle_ids) == 1
            bundle = ingestion_store.load(originals, derived, bundle_ids[0])
            assert 2 <= len(bundle.chunks) <= 16
            result = build_program(originals, derived, bundle_ids, **kwargs)
            assert 2 <= result.row_count <= 16 and result.batch_count == 1
            return result
        monkeypatch.setattr(program_api, "build", bounded_program)
        load_group = source_rows.load_group
        seen_groups = set()
        def bounded_group(originals, derived, row_map_bytes, bundle_id, batch_id):
            group = (bundle_id, batch_id)
            assert group in seen_groups or len(seen_groups) < 1
            seen_groups.add(group)
            return load_group(originals, derived, row_map_bytes, bundle_id, batch_id)
        monkeypatch.setattr(source_rows, "load_group", bounded_group)
    fixture = coverage_fixture.actual.__wrapped__(tmp_path)
    try:
        data = next(fixture)
        if os.environ.get("SLAIF_PDA_CACHED_TOYS") == "1":
            phase["name"] = "test"
        yield data
    finally:
        if os.environ.get("SLAIF_PDA_CACHED_TOYS") == "1":
            phase["name"] = "teardown"
        try:
            fixture.close()
        finally:
            if os.environ.get("SLAIF_PDA_CACHED_TOYS") == "1":
                print("PDA_COUNTS " + json.dumps({
                    "bundle_load_by_phase": load_counts,
                    "bundle_load_total": sum(load_counts.values()),
                    "popen": len(calls), "bundle_publish": len(bundle_calls),
                    "batch_publish": len(batch_calls), "groups": len(seen_groups),
                }, sort_keys=True), flush=True)
    if os.environ.get("SLAIF_PDA_CACHED_TOYS") == "1":
        assert len(calls) == 2 and len(bundle_calls) == 1 and len(batch_calls) == 1
        assert len(seen_groups) == 1


def test_selected_program_to_private_directory(actual, tmp_path, monkeypatch):  # noqa: F811
    originals, derived, program, declaration, locator, expected = actual
    covered = coverage.build(
        originals, derived, program.program_bytes, wire(declaration), wire(locator)
    )
    assert covered.map_bytes == wire(expected)
    assert covered.row_count == program.row_count == len(expected['rows'])
    assert covered.batch_count == program.batch_count == len(locator['outputs'])
    assert covered.coverage == 'COMPLETE_SELECTED_PROGRAM'
    assert covered.execution_origin == 'SUPPLIED_UNVERIFIED'
    assert covered.qualification == 'NOT_QUALIFIED'
    rows = expected['rows']
    assert 2 <= len(rows) <= 16
    assert len({r['partition_id'] for r in rows}) == 1
    print('PDA_INVENTORY ' + json.dumps({
        'rows': len(rows), 'batches': program.batch_count,
        'partitions': len({r['partition_id'] for r in rows}),
    }, sort_keys=True), flush=True)
    groups = tuple(sorted({(r['bundle_container_id'], r['batch_container_id']) for r in rows}))
    assert {b for _, b in groups} == {o['container_id'] for o in locator['outputs']}
    built = builder.build(originals, derived, wire(declaration), groups)
    assert built.map_bytes == covered.map_bytes
    core, payloads = complete(originals, derived, expected, covered.active_bundle_ids)
    core_bytes = wire(core)
    bound = files.validate_files(originals, derived, core_bytes, payloads)
    root, _, snapshot_id = materialize(tmp_path, core_bytes, payloads)
    loaded = directory.load_directory(originals, derived, str(root), snapshot_id)
    assert loaded == bound
    assert tuple(r.chunk_id for r in loaded.row_map.rows) == tuple(r['chunk_id'] for r in rows)
    matrices = {
        part.partition_id: dense.parse(part.dense.container_bytes, part.dense.container_sha256,
                                       len(part.lexical.rows)).matrix
        for part in loaded.partitions
    }
    for bundle, batch in groups:
        group = source_rows.load_group(originals, derived, covered.map_bytes, bundle, batch)
        vectors = np.frombuffer(group.vector_payload, dtype='<f4').reshape(-1, 1024)
        for i, item in enumerate(group.rows):
            row = next(r for r in rows if r['chunk_id'] == item.declaration.chunk_id)
            assert np.array_equal(vectors[i], matrices[row['partition_id']][row['partition_row']])
            assert item.rendered_text
        assert derived.load(batch)
        assert ingestion_store.load(originals, derived, bundle)

    # Swap two real selected rows in one batch; the correspondence guard must cause refusal.
    bundle, batch = next((b, c) for b, c in groups
                         if sum(r['batch_container_id'] == c for r in rows) >= 2)
    altered = copy.deepcopy(expected)
    selected = [r for r in altered['rows'] if r['batch_container_id'] == batch][:2]
    selected[0]['batch_row'], selected[1]['batch_row'] = (
        selected[1]['batch_row'], selected[0]['batch_row'])
    with pytest.raises(source_rows.SourceRowsError):
        source_rows.load_group(originals, derived, wire(altered), bundle, batch)
    calls = []
    with monkeypatch.context() as patch:
        def bypass(row, actual_row):
            calls.append(row)
            return True
        patch.setattr(source_rows, '_corresponds', bypass)
        assert source_rows.load_group(originals, derived, wire(altered), bundle, batch)
        assert calls
    with pytest.raises(source_rows.SourceRowsError):
        source_rows.load_group(originals, derived, wire(altered), bundle, batch)
    assert directory.load_directory(originals, derived, str(root), snapshot_id) == bound
    assert json.loads(covered.map_bytes) == expected
