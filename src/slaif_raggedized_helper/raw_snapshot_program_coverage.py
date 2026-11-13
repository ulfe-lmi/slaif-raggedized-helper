"""Construct a row map covering one freshly validated selected-source program."""

from dataclasses import asdict, dataclass
import hashlib
import json
import re
import time

from . import corpus_embedding_program as program
from . import derived_store, embedding_batch_store, ingestion_store
from . import raw_snapshot_row_builder, raw_snapshot_rows, retrieval_representation as rr
from .source_admission import OriginalStore


class CoverageError(ValueError):
    """Content-free refusal of a selected-program coverage request."""


@dataclass(frozen=True, slots=True)
class CoveredRowMap:
    program_id: str
    map_bytes: bytes
    map_sha256: str
    active_bundle_ids: tuple[str, ...]
    row_count: int
    batch_count: int
    source_count: int
    coverage: str = "COMPLETE_SELECTED_PROGRAM"
    execution_origin: str = "SUPPLIED_UNVERIFIED"
    qualification: str = "NOT_QUALIFIED"


def _check(value):
    if not value:
        raise ValueError


def _pairs(items):
    result = {}
    for key, value in items:
        _check(key not in result)
        result[key] = value
    return result


def _reject(_value):
    raise ValueError


def _hash(data):
    return hashlib.sha256(data).hexdigest()


def _locator(data, ident, count):
    _check(type(data) is bytes and 1 <= len(data) <= 65536)
    obj = json.loads(
        data.decode("ascii"), object_pairs_hook=_pairs, parse_float=_reject, parse_constant=_reject
    )
    _check(type(obj) is dict and set(obj) == {"schema", "kind", "source_program_id", "outputs"})
    _check(type(obj["schema"]) is int and obj["schema"] == 1)
    _check(obj["kind"] == "slaif-raw-program-output-selection-v1")
    _check(obj["source_program_id"] == ident)
    _check(
        json.dumps(
            obj, sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False
        ).encode("ascii")
        == data
    )
    outputs = obj["outputs"]
    _check(type(outputs) is list and len(outputs) == count)
    ids = set()
    for index, output in enumerate(outputs):
        _check(
            type(output) is dict
            and set(output) == {"batch_index", "container_id", "metadata_sha256"}
        )
        _check(type(output["batch_index"]) is int and output["batch_index"] == index)
        for key in ("container_id", "metadata_sha256"):
            _check(type(output[key]) is str and re.fullmatch(r"[0-9a-f]{64}", output[key]))
        _check(output["container_id"] not in ids)
        ids.add(output["container_id"])
    return outputs


def build(
    originals, derived, program_bytes, declaration_bytes, completion_bytes, *, deadline_ms=30000
):
    """Validate supplied DATA and construct coverage of exactly the selected program."""
    start = time.monotonic()
    try:
        return _build(
            originals,
            derived,
            program_bytes,
            declaration_bytes,
            completion_bytes,
            deadline_ms,
            start,
        )
    except Exception:
        raise CoverageError("program coverage refused") from None


def _build(
    originals, derived, program_bytes, declaration_bytes, completion_bytes, deadline_ms, start
):
    _check(type(deadline_ms) is int and 1 <= deadline_ms <= 120000)
    end = start + deadline_ms / 1000

    def check_time():
        _check(time.monotonic() < end)

    check_time()
    _check(type(originals) is OriginalStore and type(derived) is derived_store.Store)
    _check(type(program_bytes) is bytes and 1 <= len(program_bytes) <= 16777216)
    parsed, doc = program._parse(program_bytes)
    check_time()
    _check(parsed.row_count <= 4096 and parsed.batch_count <= 128 and len(doc["sources"]) <= 128)
    _check(doc["representation_policy"] == asdict(rr.Policy()))
    _check(doc["batch_policy"] == asdict(rr.BatchPolicy()))
    outputs = _locator(completion_bytes, parsed.source_program_id, parsed.batch_count)
    check_time()
    fresh = program.validate(originals, derived, program_bytes)
    check_time()
    _check(fresh == parsed)
    sources = doc["sources"]
    active = tuple(source["bundle_id"] for source in sources)
    groups = []
    expected = {}
    batch_metadata = []
    common_deps = None
    for selection, batch_doc, output in zip(fresh.batches, doc["batches"], outputs, strict=True):
        check_time()
        source = sources[batch_doc["source_index"]]
        bundle = ingestion_store.load(originals, derived, selection.bundle_id)
        check_time()
        _check(_hash(bundle.metadata_json) == source["bundle_metadata_sha256"])
        snapshot = derived.load(output["container_id"])
        check_time()
        metadata = derived_store._encode(derived_store._parse(snapshot.manifest)["metadata"])
        _check(_hash(metadata) == output["metadata_sha256"])
        embedding_batch_store.load(derived, output["container_id"], metadata)
        batch_metadata.append((output["container_id"], metadata))
        check_time()
        obj = embedding_batch_store._metadata(metadata)
        if common_deps is None:
            common_deps = obj["dependencies"]
        _check(obj["dependencies"] == common_deps)
        first = batch_doc["first_ordinal"]
        rows = doc["rows"][first : first + batch_doc["row_count"]]
        _check(len(rows) == len(obj["rows"]) == len(selection.chunk_ids))
        for index, (row, record) in enumerate(zip(rows, obj["rows"], strict=True)):
            _check(record["chunk_id"] == row["chunk_id"] == selection.chunk_ids[index])
            _check(record["rendered_sha256"] == row["rendered_sha256"])
            _check(
                all(
                    record[k] == source[k]
                    for k in ("revision_id", "extraction_id", "source_scope_sha256")
                )
            )
            _check(row["chunk_id"] not in expected)
            expected[row["chunk_id"]] = (record, source, output, index)
        groups.append((selection.bundle_id, output["container_id"]))
    groups = tuple(sorted(groups))
    _check(len(groups) == len(set(groups)))
    check_time()
    built = raw_snapshot_row_builder.build(
        originals, derived, declaration_bytes, groups, deadline_ms=deadline_ms
    )
    check_time()
    mapped = raw_snapshot_rows.parse(built.map_bytes)
    _check(built.row_count == len(mapped.rows) == fresh.row_count == len(expected))
    _check(built.group_count == fresh.batch_count)
    _check({row.chunk_id for row in mapped.rows} == set(expected))
    for row in mapped.rows:
        record, source, output, index = expected[row.chunk_id]
        _check(all(getattr(row, key) == value for key, value in record.items()))
        _check(row.bundle_container_id == source["bundle_id"])
        _check(row.bundle_metadata_sha256 == source["bundle_metadata_sha256"])
        _check(row.batch_container_id == output["container_id"])
        _check(row.batch_metadata_sha256 == output["metadata_sha256"] and row.batch_row == index)
    check_time()
    _check(program.validate(originals, derived, program_bytes) == fresh)
    check_time()
    for container_id, metadata in batch_metadata:
        embedding_batch_store.load(derived, container_id, metadata)
        check_time()
    result = CoveredRowMap(
        fresh.source_program_id,
        built.map_bytes,
        _hash(built.map_bytes),
        active,
        fresh.row_count,
        fresh.batch_count,
        len(sources),
    )
    check_time()
    return result
