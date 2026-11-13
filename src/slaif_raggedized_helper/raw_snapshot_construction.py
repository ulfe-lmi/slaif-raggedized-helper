"""Private composition of fresh DATA validation, publication, and selection."""

from dataclasses import dataclass
import hashlib
import re
import time

from . import raw_snapshot_completion_locator as locator
from . import raw_snapshot_program_coverage as coverage
from . import raw_snapshot_file_builder as builder
from . import raw_snapshot_publication as publication
from . import raw_snapshot_selection as selection
from . import raw_snapshot_files as files
from . import derived_store
from .source_admission import OriginalStore


@dataclass(frozen=True, slots=True)
class ConstructionResult:
    source_program_id: str
    snapshot_id: str
    pointer_bytes: bytes
    generation: int
    row_count: int
    partition_count: int
    source_count: int
    execution_origin: str = "SUPPLIED_UNVERIFIED"
    qualification: str = "NOT_QUALIFIED"
    state: str = "SELECTED_DATA"


class ConstructionError(ValueError):
    """Content-free refusal; attempted operations require independent reconciliation."""

    def __init__(self, stage, candidate_snapshot_id, publication_attempted, selection_attempted):
        super().__init__("snapshot construction refused")
        self.stage = stage
        self.candidate_snapshot_id = candidate_snapshot_id
        self.publication_attempted = publication_attempted
        self.selection_attempted = selection_attempted


def _check(value):
    if not value:
        raise ValueError


def build_publish_select_data(
    originals,
    derived,
    store_root,
    program_bytes,
    execution_result,
    declaration_bytes,
    query_context_bytes,
    withdrawn_revisions,
    expected_pointer_bytes,
    *,
    deadline_ms=120000,
):
    """Construct and select supplied DATA; the stores remain owned by the caller."""
    stage, candidate, pub_attempted, sel_attempted = "admission", None, False, False
    try:
        _check(type(deadline_ms) is int and 1 <= deadline_ms <= 120000)
        end = time.monotonic() + deadline_ms / 1000

        def remaining():
            left = int((end - time.monotonic()) * 1000)
            _check(left >= 1)
            return min(left, 120000)

        remaining()
        _check(type(originals) is OriginalStore and type(derived) is derived_store.Store)
        publication._path_check(store_root)
        for value, limit in (
            (program_bytes, 16777216),
            (declaration_bytes, 4096),
            (query_context_bytes, 4096),
        ):
            _check(type(value) is bytes and 1 <= len(value) <= limit)
        _check(type(withdrawn_revisions) is tuple and len(withdrawn_revisions) <= 1024)
        _check(
            all(
                type(v) is str and re.fullmatch(r"sha256:[0-9a-f]{64}", v)
                for v in withdrawn_revisions
            )
        )
        _check(tuple(sorted(set(withdrawn_revisions))) == withdrawn_revisions)
        expected = None
        if expected_pointer_bytes is not None:
            _check(type(expected_pointer_bytes) is bytes and len(expected_pointer_bytes) <= 512)
            expected = selection.parse_pointer(expected_pointer_bytes)
            _check(type(expected) is selection.Pointer and expected.generation < 2**63 - 1)
        remaining()
        stage = "locator"
        loc = locator.encode(program_bytes, execution_result, deadline_ms=remaining())
        remaining()
        _check(type(loc) is bytes and 1 <= len(loc) <= 65536)
        stage = "coverage"
        covered = coverage.build(
            originals, derived, program_bytes, declaration_bytes, loc, deadline_ms=remaining()
        )
        remaining()
        _check(
            type(covered) is coverage.CoveredRowMap
            and covered.program_id == execution_result.source_program_id
            and covered.row_count == execution_result.row_count
            and type(covered.row_count) is int
            and 1 <= covered.row_count <= 4096
            and type(covered.source_count) is int
            and 1 <= covered.source_count <= 128
            and type(covered.batch_count) is int
            and 1 <= covered.batch_count <= 128
        )
        stage = "files"
        built = builder.build(
            originals,
            derived,
            covered.map_bytes,
            covered.active_bundle_ids,
            withdrawn_revisions,
            query_context_bytes,
            deadline_ms=remaining(),
        )
        remaining()
        _check(
            type(built) is builder.BuiltSnapshotFiles
            and built.row_count == covered.row_count
            and built.member_count == covered.source_count
            and type(built.core_bytes) is bytes
            and type(built.row_count) is int
            and type(built.member_count) is int
            and type(built.partition_count) is int
            and 1 <= built.partition_count <= 128
        )
        ident = "sha256:" + hashlib.sha256(built.core_bytes).hexdigest()
        _check(built.snapshot_id == ident)
        candidate = ident
        remaining()
        stage = "publication"
        pub_attempted = True
        published = publication.publish_directory(
            originals, derived, store_root, built.core_bytes, built.files
        )
        remaining()
        _check(
            type(published) is publication.Publication
            and published.snapshot_id == candidate
            and type(published.data) is files.BoundSnapshotData
        )
        data = published.data
        _check(
            data.snapshot_id == candidate
            and data.core_bytes == built.core_bytes
            and data.row_map.map_bytes == covered.map_bytes
            and len(data.row_map.rows) == built.row_count
            and len(data.partitions) == built.partition_count
            and len(data.membership.entries) == built.member_count
        )
        remaining()
        stage = "selection"
        budget = remaining()
        sel_attempted = True
        selected = selection.compare_and_select_data(
            originals, derived, store_root, candidate, expected_pointer_bytes, deadline_ms=budget
        )
        remaining()
        _check(
            type(selected) is selection.Selection
            and type(selected.pointer) is selection.Pointer
            and type(selected.data) is files.BoundSnapshotData
            and selected.data == data
        )
        pointer = selected.pointer
        _check(
            selection.parse_pointer(pointer.pointer_bytes) == pointer
            and pointer.snapshot_id == candidate
            and pointer.core_sha256 == candidate[7:]
            and pointer.generation == (1 if expected is None else expected.generation + 1)
        )
        remaining()
        stage = "final"
        result = ConstructionResult(
            covered.program_id,
            candidate,
            pointer.pointer_bytes,
            pointer.generation,
            built.row_count,
            built.partition_count,
            covered.source_count,
        )
        remaining()
        return result
    except Exception:
        raise ConstructionError(stage, candidate, pub_attempted, sel_attempted) from None
