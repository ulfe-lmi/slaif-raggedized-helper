"""Source-backed composition; execution requires a separate approved proof plan."""

import json
from dataclasses import replace
from pathlib import Path

# This existing provider initializes the repository's helper import layout first.
import test_raw_snapshot_program_coverage_composition as provider
import test_retrieval_representation_composition as representation_provider
import test_native_tokenizers as native_provider
import test_raw_snapshot_directory_composition as directory_provider
import test_raw_snapshot_file_builder_composition as builder_provider
from test_raw_snapshot_program_coverage_composition import actual, wire  # noqa: F401
from test_raw_snapshot_directory_composition import restore_owned_directories  # noqa: F401
from test_raw_snapshot_file_builder_composition import context
import pytest
from slaif_raggedized_helper import corpus_embedding_executor as executor
from slaif_raggedized_helper import raw_snapshot_construction as construction
from slaif_raggedized_helper import raw_snapshot_pin as pin
from slaif_raggedized_helper import raw_snapshot_selection as selection


_CHECKOUT = Path(__file__).resolve().parents[2]
for module, relative in (
    (provider, "tests/integration/test_raw_snapshot_program_coverage_composition.py"),
    (representation_provider, "tests/integration/test_retrieval_representation_composition.py"),
    (native_provider, "tests/unit/test_native_tokenizers.py"),
    (directory_provider, "tests/integration/test_raw_snapshot_directory_composition.py"),
    (builder_provider, "tests/integration/test_raw_snapshot_file_builder_composition.py"),
    (construction, "src/slaif_raggedized_helper/raw_snapshot_construction.py"),
    (executor, "src/slaif_raggedized_helper/corpus_embedding_executor.py"),
    (pin, "src/slaif_raggedized_helper/raw_snapshot_pin.py"),
    (selection, "src/slaif_raggedized_helper/raw_snapshot_selection.py"),
):
    assert Path(module.__file__).resolve() == _CHECKOUT / relative
assert Path(wire.__code__.co_filename).resolve() == Path(provider.__file__).resolve()
assert Path(context.__code__.co_filename).resolve() == Path(builder_provider.__file__).resolve()
assert (
    Path(representation_provider.make_bundle.__code__.co_filename).resolve()
    == Path(representation_provider.__file__).resolve()
)
assert (
    Path(native_provider.make_native.__code__.co_filename).resolve()
    == Path(native_provider.__file__).resolve()
)


def test_source_construction_and_pin(actual, tmp_path):  # noqa: F811
    assert Path(construction.__file__).resolve() == (
        Path(__file__).resolve().parents[2]
        / "src/slaif_raggedized_helper/raw_snapshot_construction.py"
    )
    originals, derived, program, declaration, locator, mapping = actual
    completions = tuple(
        executor.BatchCompletion(
            item["batch_index"],
            None,
            "sha256:" + item["container_id"],
            item["metadata_sha256"],
            None,
        )
        for item in locator["outputs"]
    )
    result = executor.CorpusResult(
        program.source_program_id, program.row_count, completions, None, None, None
    )
    root = tmp_path / "construction"
    root.mkdir(mode=0o700)
    forged = replace(result, source_program_id="sha256:" + "0" * 64)
    with pytest.raises(construction.ConstructionError) as refused:
        construction.build_publish_select_data(
            originals,
            derived,
            str(root),
            program.program_bytes,
            forged,
            wire(declaration),
            context(mapping),
            (),
            None,
        )
    assert not refused.value.publication_attempted and not refused.value.selection_attempted
    assert list(root.iterdir()) == []
    missing = replace(
        result,
        completions=(replace(completions[0], output_ref="sha256:" + "0" * 64), *completions[1:]),
    )
    with pytest.raises(construction.ConstructionError) as refused:
        construction.build_publish_select_data(
            originals,
            derived,
            str(root),
            program.program_bytes,
            missing,
            wire(declaration),
            context(mapping),
            (),
            None,
        )
    assert refused.value.stage == "coverage"
    assert not refused.value.publication_attempted and not refused.value.selection_attempted
    assert list(root.iterdir()) == []
    first = construction.build_publish_select_data(
        originals,
        derived,
        str(root),
        program.program_bytes,
        result,
        wire(declaration),
        context(mapping),
        (),
        None,
    )
    old = selection.read_selected_data(originals, derived, str(root))
    assert old.pointer.pointer_bytes == first.pointer_bytes
    assert old.data.row_map.map_bytes == wire(mapping)
    owner = pin.PinOwner()
    try:
        captured = owner.acquire_selected_data(originals, derived, str(root))
        query = json.loads(context(mapping))
        query["query_execution_fingerprint"] = "e" * 64
        second = construction.build_publish_select_data(
            originals,
            derived,
            str(root),
            program.program_bytes,
            result,
            wire(declaration),
            wire(query),
            (),
            first.pointer_bytes,
        )
        fresh = selection.read_selected_data(originals, derived, str(root))
        assert second.snapshot_id != first.snapshot_id and second.generation == 2
        assert owner.check() == captured and captured.data == old.data
        assert fresh.pointer.pointer_bytes == second.pointer_bytes
        assert fresh.data.row_map.map_bytes == wire(mapping)
    finally:
        owner.close()
