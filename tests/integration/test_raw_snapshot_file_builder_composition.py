"""Three bounded real-source constructor journeys."""

import copy
import json

import pytest

from slaif_raggedized_helper import raw_snapshot_directory as directory
from slaif_raggedized_helper import raw_snapshot_file_builder as builder
from slaif_raggedized_helper import raw_snapshot_publication as publication
from slaif_raggedized_helper import raw_snapshot_selection as selection
from test_raw_snapshot_directory_composition import restore_owned_directories  # noqa: F401
from test_raw_snapshot_files_composition import complete
from test_raw_snapshot_rows import enc
from test_raw_snapshot_source_rows_composition import actual, mapwire  # noqa: F401


def context(mapping):
    return enc(
        dict(
            schema=1,
            kind="slaif-raw-snapshot-query-context-v1",
            space_id=mapping["space_id"],
            definition_fingerprint=mapping["definition_fingerprint"],
            query_policy_fingerprint="b" * 64,
            query_execution_fingerprint="c" * 64,
            precision_qualification_ref="sha256:" + "d" * 64,
        )
    )


def test_positive(actual, tmp_path):  # noqa: F811
    originals, derived, mapping, bundle, _, _ = actual
    result = builder.build(originals, derived, mapwire(mapping), (bundle,), (), context(mapping))
    core, files = complete(originals, derived, mapping, (bundle,))
    q = json.loads(context(mapping))
    for key in (
        "query_policy_fingerprint",
        "query_execution_fingerprint",
        "precision_qualification_ref",
    ):
        core["embedding"][key] = q[key]
    core["validation"]["validator_fingerprint"] = builder.VALIDATION_POLICY_FINGERPRINT
    core["files"].sort(key=lambda d: d["path"])
    assert result.core_bytes == enc(core) and result.files == files
    assert result.qualification == "NOT_QUALIFIED" and result.row_count == 3
    root = tmp_path / "publisher"
    root.mkdir(mode=0o700)
    published = publication.publish_directory(
        originals, derived, str(root), result.core_bytes, result.files
    )
    assert published.snapshot_id == result.snapshot_id
    selected = selection.compare_and_select_data(
        originals, derived, str(root), result.snapshot_id, None
    )
    assert selection.read_selected_data(originals, derived, str(root)) == selected
    assert (
        directory.load_directory(originals, derived, str(root), result.snapshot_id).snapshot_id
        == result.snapshot_id
    )


def test_negative(actual, tmp_path):  # noqa: F811
    originals, derived, mapping, bundle, _, _ = actual
    bad = copy.deepcopy(mapping)
    bad["rows"][0]["batch_row"], bad["rows"][1]["batch_row"] = (
        bad["rows"][1]["batch_row"],
        bad["rows"][0]["batch_row"],
    )
    root = tmp_path / "unused"
    root.mkdir(mode=0o700)
    for data, ids, withdrawn in (
        (mapwire(bad), (bundle,), ()),
        (mapwire(mapping), (), ()),
        (mapwire(mapping), (bundle,), (mapping["rows"][0]["revision_id"],)),
    ):
        with pytest.raises(builder.SnapshotBuildError):
            builder.build(originals, derived, data, ids, withdrawn, context(mapping))
    blob = next((originals.root / "blobs").iterdir())
    old = blob.read_bytes()
    try:
        blob.write_bytes(b"corrupt")
        with pytest.raises(builder.SnapshotBuildError):
            builder.build(originals, derived, mapwire(mapping), (bundle,), (), context(mapping))
    finally:
        blob.write_bytes(old)
    assert list(root.iterdir()) == []


def test_empty(actual):  # noqa: F811
    originals, derived, mapping, bundle, _, _ = actual
    mapping["rows"] = []
    for ids, withdrawn, members in (((bundle,), (), 1), ((), ("sha256:" + "e" * 64,), 0)):
        result = builder.build(
            originals, derived, mapwire(mapping), ids, withdrawn, context(mapping)
        )
        assert (result.row_count, result.partition_count, result.member_count) == (0, 0, members)
        assert [p for p, _ in result.files] == ["map", "members"]
        assert json.loads(result.core_bytes)["sources"]["withdrawn_revisions"] == list(withdrawn)
