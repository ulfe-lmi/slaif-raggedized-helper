"""Fresh original-backed source membership; never a current authorization grant."""

from dataclasses import dataclass
import hashlib
import json
import re
import time

from . import (
    derived_store,
    ingestion_store,
    provenance_records,
    raw_snapshot_manifest,
    raw_snapshot_rows,
    schema,
)
from .source_admission import OriginalStore


class MembershipError(ValueError):
    """Content-free membership refusal."""


@dataclass(frozen=True, slots=True)
class Entry:
    revision_id: str
    extraction_id: str
    bundle_container_id: str
    bundle_metadata_sha256: str
    chunk_policy_fingerprint: str
    source_scope_sha256: str
    partition_id: str
    scope_bytes: bytes
    ordinals: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class Membership:
    membership_bytes: bytes
    sha256: str
    row_map_sha256: str
    row_count: int
    entries: tuple[Entry, ...]
    withdrawn_revisions: tuple[str, ...]


_FIELDS = {
    "revision_id",
    "extraction_id",
    "bundle_container_id",
    "bundle_metadata_sha256",
    "chunk_policy_fingerprint",
    "source_scope_sha256",
    "partition_id",
    "scope",
    "ordinals",
}
_LIMIT = 8 * 1048576


def _check(value):
    if not value:
        raise ValueError


def _hex(value, prefix=""):
    _check(
        type(value) is str and re.fullmatch(re.escape(prefix) + "[0-9a-f]{64}", value) is not None
    )


def _json(value):
    return json.dumps(
        value, sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False
    ).encode("ascii")


def _digest(value):
    return hashlib.sha256(value).hexdigest()


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        _check(key not in result)
        result[key] = value
    return result


def _ids(value, limit, prefix):
    _check(type(value) is tuple and len(value) <= limit)
    for item in value:
        _hex(item, prefix)
    _check(tuple(sorted(set(value))) == value)


def _scope(value, revision):
    _check(
        type(value) is dict
        and type(value.get("labels")) is list
        and type(value.get("processing_approved")) is bool
        and value["processing_approved"]
    )
    labels = value["labels"]
    _check(all(type(x) is str for x in labels) and labels == sorted(set(labels)))
    for item in (
        value.get("document_id"),
        value.get("revision_id"),
        value.get("corpus"),
        value.get("version"),
        *labels,
    ):
        if item is not None:
            _check(type(item) is str)
            item.encode("utf-8")
    scope = provenance_records.admit_record("Scope", value)
    _check(scope.model_dump(mode="json") == value and scope.revision_id == revision)
    return (
        schema.fingerprint({"kind": "embedding-source-scope-v1", "scope": value})[7:],
        schema.fingerprint(
            {"schema": 1, "corpus": value["corpus"], "version": value["version"], "labels": labels}
        ),
    )


def _parse(data):
    _check(type(data) is bytes and 0 < len(data) <= _LIMIT)

    def reject(_):
        raise ValueError

    obj = json.loads(
        data.decode("ascii"), object_pairs_hook=_pairs, parse_float=reject, parse_constant=reject
    )
    _check(
        type(obj) is dict
        and set(obj)
        == {"schema", "kind", "row_map_sha256", "row_count", "entries", "withdrawn_revisions"}
    )
    _check(
        _json(obj) == data
        and type(obj["schema"]) is int
        and obj["schema"] == 1
        and obj["kind"] == "slaif-raw-source-membership-v1"
    )
    _hex(obj["row_map_sha256"])
    count = obj["row_count"]
    _check(type(count) is int and 0 <= count <= 4096)
    entries, withdrawn = obj["entries"], obj["withdrawn_revisions"]
    _check(type(entries) is list and len(entries) <= 128 and type(withdrawn) is list)
    _ids(tuple(withdrawn), 1024, "sha256:")
    parsed, revisions, bundles, ordinals = [], [], set(), []
    for entry in entries:
        _check(type(entry) is dict and set(entry) == _FIELDS and len(_json(entry)) <= 131072)
        for k in ("revision_id", "extraction_id", "partition_id"):
            _hex(entry[k], "sha256:")
        for k in (
            "bundle_container_id",
            "bundle_metadata_sha256",
            "chunk_policy_fingerprint",
            "source_scope_sha256",
        ):
            _hex(entry[k])
        _check(entry["bundle_container_id"] not in bundles)
        bundles.add(entry["bundle_container_id"])
        revisions.append(entry["revision_id"])
        scope_hash, partition = _scope(entry["scope"], entry["revision_id"])
        _check((scope_hash, partition) == (entry["source_scope_sha256"], entry["partition_id"]))
        numbers = entry["ordinals"]
        _check(
            type(numbers) is list
            and len(numbers) <= 4096
            and all(type(n) is int and 0 <= n <= 4095 for n in numbers)
            and numbers == sorted(set(numbers))
        )
        ordinals.extend(numbers)
        parsed.append(
            Entry(
                *(
                    entry[k]
                    for k in (
                        "revision_id",
                        "extraction_id",
                        "bundle_container_id",
                        "bundle_metadata_sha256",
                        "chunk_policy_fingerprint",
                        "source_scope_sha256",
                        "partition_id",
                    )
                ),
                _json(entry["scope"]),
                tuple(numbers),
            )
        )
    _check(
        revisions == sorted(set(revisions))
        and not set(revisions) & set(withdrawn)
        and sorted(ordinals) == list(range(count))
    )
    return Membership(
        data, _digest(data), obj["row_map_sha256"], count, tuple(parsed), tuple(withdrawn)
    )


def parse(membership_bytes):
    """Parse canonical declarations only."""
    try:
        return _parse(membership_bytes)
    except Exception:
        raise MembershipError("membership refused") from None


def _rows_match(entry, rows, policy):
    _check(entry.chunk_policy_fingerprint == policy)
    matching = tuple(r for r in rows if r.revision_id == entry.revision_id)
    _check(tuple(r.ordinal for r in matching) == entry.ordinals)
    for row in matching:
        _check(
            (
                row.bundle_container_id,
                row.bundle_metadata_sha256,
                row.extraction_id,
                row.source_scope_sha256,
                row.partition_id,
            )
            == (
                entry.bundle_container_id,
                entry.bundle_metadata_sha256,
                entry.extraction_id,
                entry.source_scope_sha256,
                entry.partition_id,
            )
        )


def bind(core_bytes, row_map_bytes, membership_bytes):
    """Bind fresh declarations without accessing stores."""
    try:
        rows = raw_snapshot_rows.bind(core_bytes, row_map_bytes)
        core = raw_snapshot_manifest.parse(core_bytes)
        membership = _parse(membership_bytes)
        obj = json.loads(core_bytes)
        descriptor = next(f for f in core.files if f.path == obj["membership_path"])
        _check(
            (descriptor.role, descriptor.schema, descriptor.bytes, descriptor.sha256)
            == (
                "source_membership",
                "slaif-raw-source-membership-v1",
                len(membership_bytes),
                membership.sha256,
            )
        )
        _check(
            membership.row_map_sha256 == _digest(row_map_bytes)
            and membership.row_count == len(rows.rows)
            and tuple(e.revision_id for e in membership.entries) == core.active_revisions
            and membership.withdrawn_revisions == core.withdrawn_revisions
        )
        for entry in membership.entries:
            _rows_match(entry, rows.rows, rows.chunk_policy_fingerprint)
        return membership
    except Exception:
        raise MembershipError("membership refused") from None


def build(originals, derived, row_map_bytes, bundle_ids, withdrawn_revisions):
    """Build membership from freshly verified actual bundles; stores remain borrowed."""
    try:
        end = time.monotonic() + 30

        def check_time():
            _check(time.monotonic() < end)

        _check(type(originals) is OriginalStore and type(derived) is derived_store.Store)
        _ids(bundle_ids, 128, "")
        _ids(withdrawn_revisions, 1024, "sha256:")
        rows = raw_snapshot_rows.parse(row_map_bytes)
        _check({r.bundle_container_id for r in rows.rows} <= set(bundle_ids))
        entries = []
        base_size = len(
            _json(
                dict(
                    schema=1,
                    kind="slaif-raw-source-membership-v1",
                    row_map_sha256=_digest(row_map_bytes),
                    row_count=len(rows.rows),
                    entries=[],
                    withdrawn_revisions=list(withdrawn_revisions),
                )
            )
        )
        entries_size = 0
        minimum_entry = dict(
            revision_id="sha256:" + "0" * 64,
            extraction_id="sha256:" + "0" * 64,
            bundle_container_id="0" * 64,
            bundle_metadata_sha256="0" * 64,
            chunk_policy_fingerprint="0" * 64,
            source_scope_sha256="0" * 64,
            partition_id="sha256:" + "0" * 64,
            scope=dict(
                schema_version=1,
                document_id="x",
                revision_id="sha256:" + "0" * 64,
                corpus="x",
                version="",
                labels=[],
                processing_approved=True,
                redistribution_rights="allowed",
            ),
            ordinals=[],
        )
        minimum_entry_size = len(_json(minimum_entry))
        for ident in bundle_ids:
            check_time()
            _check(base_size + entries_size + (1 if entries else 0) + minimum_entry_size <= _LIMIT)
            bundle = ingestion_store.load(originals, derived, ident)
            check_time()
            scope = bundle.scope.model_dump(mode="json")
            revision = bundle.revision.revision_id
            scope_hash, partition = _scope(scope, revision)
            policy = json.loads(bundle.metadata_json)["chunking"]["policy_id"]
            _hex(policy, "sha256:")
            _check(policy[7:] == rows.chunk_policy_fingerprint)
            selected = tuple(r for r in rows.rows if r.revision_id == revision)
            chunks = {chunk.chunk_id: chunk for chunk in bundle.chunks}
            for row in selected:
                chunk = chunks[row.chunk_id]
                _check(
                    (
                        row.bundle_container_id,
                        row.bundle_metadata_sha256,
                        row.extraction_id,
                        row.source_scope_sha256,
                        row.partition_id,
                    )
                    == (
                        ident,
                        _digest(bundle.metadata_json),
                        bundle.dependency.extraction_id,
                        scope_hash,
                        partition,
                    )
                )
                _check(
                    (chunk.revision_id, chunk.extraction_id, chunk.policy_id)
                    == (revision, bundle.dependency.extraction_id, policy)
                )
            entry = dict(
                revision_id=revision,
                extraction_id=bundle.dependency.extraction_id,
                bundle_container_id=ident,
                bundle_metadata_sha256=_digest(bundle.metadata_json),
                chunk_policy_fingerprint=policy[7:],
                source_scope_sha256=scope_hash,
                partition_id=partition,
                scope=scope,
                ordinals=[r.ordinal for r in selected],
            )
            entry_size = len(_json(entry))
            _check(entry_size <= 131072)
            _check(base_size + entries_size + entry_size + (1 if entries else 0) <= _LIMIT)
            entries_size += entry_size + (1 if entries else 0)
            entries.append(entry)
            if selected:
                del chunk
            del chunks, bundle, selected, scope, entry
            check_time()
        entries.sort(key=lambda e: e["revision_id"])
        obj = dict(
            schema=1,
            kind="slaif-raw-source-membership-v1",
            row_map_sha256=_digest(row_map_bytes),
            row_count=len(rows.rows),
            entries=entries,
            withdrawn_revisions=list(withdrawn_revisions),
        )
        result = _parse(_json(obj))
        for entry in result.entries:
            _rows_match(entry, rows.rows, rows.chunk_policy_fingerprint)
        check_time()
        return result
    except Exception:
        raise MembershipError("membership refused") from None


def validate(originals, derived, core_bytes, row_map_bytes, membership_bytes):
    """Bind declarations and rebuild from fresh original-backed bundles."""
    try:
        declared = bind(core_bytes, row_map_bytes, membership_bytes)
        ids = tuple(sorted(e.bundle_container_id for e in declared.entries))
        rebuilt = build(originals, derived, row_map_bytes, ids, declared.withdrawn_revisions)
        _check(rebuilt.membership_bytes == membership_bytes)
        return rebuilt
    except Exception:
        raise MembershipError("membership refused") from None
