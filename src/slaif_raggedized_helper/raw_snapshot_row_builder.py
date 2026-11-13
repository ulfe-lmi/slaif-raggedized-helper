"""Construct bounded row-map DATA from selected, freshly validated stored batches."""

from dataclasses import asdict, dataclass
import hashlib
import json
import re
import time

from . import derived_store, embedding_batch_store, ingestion_store, raw_snapshot_rows
from . import raw_snapshot_source_rows, retrieval_representation, schema
from .source_admission import OriginalStore


class BuildError(ValueError):
    """Content-free construction refusal."""


@dataclass(frozen=True, slots=True)
class BuiltRowMap:
    map_bytes: bytes
    map_sha256: str
    row_count: int
    group_count: int
    execution_origin: str = "SUPPLIED_UNVERIFIED"
    qualification: str = "NOT_QUALIFIED"


def _check(value):
    if not value:
        raise ValueError


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        _check(key not in result)
        result[key] = value
    return result


def _reject(_value):
    raise ValueError


def _wire(value):
    return json.dumps(
        value, sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False
    ).encode("ascii")


def _hash(value):
    return hashlib.sha256(value).hexdigest()


def build(originals, derived, declaration_bytes, groups, *, deadline_ms=30000):
    """Build DATA for explicit whole batches; does not establish rights or qualification."""
    start = time.monotonic()
    try:
        return _build(originals, derived, declaration_bytes, groups, deadline_ms, start)
    except Exception:
        raise BuildError("row map build refused") from None


def _build(originals, derived, declaration_bytes, groups, deadline_ms, start):
    _check(type(deadline_ms) is int and 1 <= deadline_ms <= 120000)
    end = start + deadline_ms / 1000

    def check_time():
        _check(time.monotonic() < end)

    check_time()
    _check(type(originals) is OriginalStore and type(derived) is derived_store.Store)
    _check(type(declaration_bytes) is bytes and 1 <= len(declaration_bytes) <= 4096)
    _check(type(groups) is tuple and len(groups) <= 128)
    captured = []
    for pair in groups:
        _check(type(pair) is tuple and len(pair) == 2)
        _check(all(type(x) is str and re.fullmatch(r"[0-9a-f]{64}", x) for x in pair))
        captured.append((pair[0], pair[1]))
    captured = tuple(captured)
    _check(tuple(sorted(captured)) == captured and len(set(captured)) == len(captured))
    _check(len({p[1] for p in captured}) == len(captured))
    declaration = json.loads(
        declaration_bytes.decode("ascii"),
        object_pairs_hook=_pairs,
        parse_float=_reject,
        parse_constant=_reject,
    )
    headers = raw_snapshot_rows._HEADER
    _check(type(declaration) is dict and set(declaration) == set(headers) | {"schema", "kind"})
    _check(type(declaration["schema"]) is int and declaration["schema"] == 1)
    _check(declaration["kind"] == "slaif-raw-row-map-build-declaration-v1")
    _check(_wire(declaration) == declaration_bytes)
    policy_hash = schema.fingerprint(
        dict(
            kind="embedding-representation-policy-v1",
            policy=asdict(retrieval_representation.Policy()),
            batch_policy=asdict(retrieval_representation.BatchPolicy()),
        )
    )[7:]
    _check(declaration["representation_policy_fingerprint"] == policy_hash)
    obj = {key: declaration[key] for key in headers}
    obj.update(schema=1, kind="slaif-raw-row-map-v1", rows=[])
    raw_snapshot_rows.parse(_wire(obj))
    check_time()
    rows = []
    expected_counts = {}
    chunks_seen, reps_seen = set(), set()
    for bundle_id, batch_id in captured:
        check_time()
        bundle = ingestion_store.load(originals, derived, bundle_id)
        check_time()
        snapshot = derived.load(batch_id)
        check_time()
        manifest = derived_store._parse(snapshot.manifest)
        metadata = derived_store._encode(manifest["metadata"])
        batch = embedding_batch_store.load(derived, batch_id, metadata)
        check_time()
        batch_obj = embedding_batch_store._metadata(metadata)
        deps = batch_obj["dependencies"]
        _check(
            deps["space_id"] == obj["space_id"]
            and "sha256:" + deps["definition_fingerprint"] == obj["definition_fingerprint"]
            and deps["representation_policy_fingerprint"] == policy_hash
            and deps["normalization_policy_id"] == obj["normalization_policy_id"]
        )
        bundle_obj = json.loads(bundle.metadata_json)
        definitions = [
            d for d in bundle_obj["chunking"]["definitions"] if d["role"] == "bge_representation"
        ]
        _check(
            len(definitions) == 1 and definitions[0]["artifact_sha256"] == deps["tokenizer_sha256"]
        )
        scope = bundle.scope.model_dump(mode="json")
        partition = schema.fingerprint(
            dict(schema=1, corpus=scope["corpus"], version=scope["version"], labels=scope["labels"])
        )
        scope_hash = schema.fingerprint(dict(kind="embedding-source-scope-v1", scope=scope))[7:]
        chunks = {c.chunk_id: c for c in bundle.chunks}
        _check(len(chunks) == len(bundle.chunks))
        records = batch_obj["rows"]
        _check(len(rows) + len(records) <= 4096)
        expected_counts[(bundle_id, batch_id)] = len(records)
        bundle_hash, batch_hash = _hash(bundle.metadata_json), _hash(metadata)
        for index, record in enumerate(records):
            check_time()
            chunk = chunks[record["chunk_id"]]
            _check(
                chunk.revision_id == record["revision_id"] == bundle.revision.revision_id
                and chunk.extraction_id
                == record["extraction_id"]
                == bundle.dependency.extraction_id
                and chunk.policy_id == "sha256:" + obj["chunk_policy_fingerprint"]
                and record["source_scope_sha256"] == scope_hash
            )
            _check(
                record["chunk_id"] not in chunks_seen
                and record["representation_id"] not in reps_seen
            )
            chunks_seen.add(record["chunk_id"])
            reps_seen.add(record["representation_id"])
            rows.append(
                dict(
                    record,
                    partition_id=partition,
                    bundle_container_id=bundle_id,
                    bundle_metadata_sha256=bundle_hash,
                    batch_container_id=batch_id,
                    batch_metadata_sha256=batch_hash,
                    batch_row=index,
                    execution_fingerprint=deps["execution_fingerprint"],
                )
            )
        del batch, snapshot, bundle, chunks, batch_obj, records
    rows.sort(key=lambda r: (r["partition_id"], r["chunk_id"], r["representation_id"]))
    counts = {}
    for index, row in enumerate(rows):
        part = row["partition_id"]
        row.update(ordinal=index, partition_row=counts.get(part, 0))
        counts[part] = counts.get(part, 0) + 1
    _check(len(counts) <= 128)
    obj["rows"] = rows
    data = _wire(obj)
    parsed = raw_snapshot_rows.parse(data)
    check_time()
    for bundle_id, batch_id in captured:
        check_time()
        bound = raw_snapshot_source_rows.load_group(originals, derived, data, bundle_id, batch_id)
        check_time()
        _check(len(bound.rows) == expected_counts[(bundle_id, batch_id)])
        _check({r.declaration.batch_row for r in bound.rows} == set(range(len(bound.rows))))
        del bound
    result = BuiltRowMap(data, _hash(data), len(parsed.rows), len(captured))
    check_time()
    return result
