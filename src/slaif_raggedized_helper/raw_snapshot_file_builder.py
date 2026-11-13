"""Construct unqualified raw snapshot DATA files from borrowed source stores."""

from dataclasses import dataclass
import hashlib
import json
import re
import time

from . import (
    derived_store,
    raw_snapshot_dense,
    raw_snapshot_files,
    raw_snapshot_lexical,
    raw_snapshot_manifest,
    raw_snapshot_membership,
    raw_snapshot_rows,
    technical_analyzer,
)
from .source_admission import OriginalStore


class SnapshotBuildError(ValueError):
    """Content-free snapshot construction refusal."""


@dataclass(frozen=True, slots=True)
class BuiltSnapshotFiles:
    core_bytes: bytes
    files: tuple[tuple[str, bytes], ...]
    snapshot_id: str
    row_count: int
    partition_count: int
    member_count: int
    validation_policy_fingerprint: str
    execution_origin: str = "SUPPLIED_UNVERIFIED"
    qualification: str = "NOT_QUALIFIED"


def _json(value):
    return json.dumps(
        value, sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False
    ).encode("ascii")


_POLICY = dict(
    schema=1,
    kind="slaif-raw-snapshot-build-validation-policy-v1",
    core_schema="slaif-raw-snapshot-core-v1",
    row_map_schema="slaif-raw-row-map-v1",
    membership_schema="slaif-raw-source-membership-v1",
    dense_schema="slaif-normalized-fp32le-d1024-npy-v1",
    lexical_schema="slaif-raw-lexical-terms-v1",
    validator="raw_snapshot_files.validate_files-v1",
    qualification="NOT_QUALIFIED",
)
VALIDATION_POLICY_FINGERPRINT = hashlib.sha256(_json(_POLICY)).hexdigest()


def _check(value):
    if not value:
        raise ValueError


def _hex(value, prefix=""):
    _check(type(value) is str and re.fullmatch(re.escape(prefix) + r"[0-9a-f]{64}", value))


def _ids(value, limit, prefix):
    _check(type(value) is tuple and len(value) <= limit)
    for item in value:
        _hex(item, prefix)
    _check(tuple(sorted(set(value))) == value)


def _context(data):
    _check(type(data) is bytes and 0 < len(data) <= 4096)

    def pairs(items):
        result = {}
        for k, v in items:
            _check(k not in result)
            result[k] = v
        return result

    def reject(_):
        raise ValueError

    obj = json.loads(
        data.decode("ascii"), object_pairs_hook=pairs, parse_float=reject, parse_constant=reject
    )
    _check(
        type(obj) is dict
        and set(obj)
        == {
            "schema",
            "kind",
            "space_id",
            "definition_fingerprint",
            "query_policy_fingerprint",
            "query_execution_fingerprint",
            "precision_qualification_ref",
        }
        and _json(obj) == data
    )
    _check(
        type(obj["schema"]) is int
        and obj["schema"] == 1
        and obj["kind"] == "slaif-raw-snapshot-query-context-v1"
    )
    for k in ("space_id", "query_policy_fingerprint", "query_execution_fingerprint"):
        _hex(obj[k])
    _hex(obj["definition_fingerprint"], "sha256:")
    if obj["precision_qualification_ref"] is not None:
        _hex(obj["precision_qualification_ref"], "sha256:")
    return obj


def build(
    originals,
    derived,
    row_map_bytes,
    active_bundle_ids,
    withdrawn_revisions,
    query_context_bytes,
    *,
    deadline_ms=30000,
):
    """Build and independently validate selected DATA; never publish or qualify it."""
    try:
        return _build(
            originals,
            derived,
            row_map_bytes,
            active_bundle_ids,
            withdrawn_revisions,
            query_context_bytes,
            deadline_ms,
        )
    except Exception:
        raise SnapshotBuildError("snapshot construction refused") from None


def _build(originals, derived, data, ids, withdrawn, query, deadline_ms):
    start = time.monotonic()
    _check(type(deadline_ms) is int and 1 <= deadline_ms <= 120000)
    end = start + deadline_ms / 1000

    def deadline():
        _check(time.monotonic() < end)

    deadline()
    _check(type(originals) is OriginalStore and type(derived) is derived_store.Store)
    _check(type(data) is bytes and type(query) is bytes)
    _ids(ids, 128, "")
    _ids(withdrawn, 1024, "sha256:")
    context = _context(query)
    deadline()
    mapping = raw_snapshot_rows.parse(data)
    deadline()
    _check(
        context["space_id"] == mapping.space_id
        and context["definition_fingerprint"] == mapping.definition_fingerprint
    )
    _check(len({(r.bundle_container_id, r.batch_container_id) for r in mapping.rows}) <= 128)
    _check({r.bundle_container_id for r in mapping.rows} <= set(ids))
    member = raw_snapshot_membership.build(originals, derived, data, ids, withdrawn)
    deadline()
    active = sorted(e.revision_id for e in member.entries)
    _check(not set(active) & set(withdrawn))
    analyzer = technical_analyzer.analyzer_id(technical_analyzer.Policy())
    _hex(analyzer, "sha256:")
    payloads = []
    descriptors = []
    total = 0

    def add(path, role, schema, blob, limit):
        nonlocal total
        deadline()
        _check(type(blob) is bytes and len(blob) <= limit and len(payloads) < 258)
        total += len(blob)
        _check(total <= 96 * 1048576)
        digest = hashlib.sha256(blob).hexdigest()
        deadline()
        payloads.append((path, blob))
        descriptors.append(
            dict(path=path, role=role, schema=schema, bytes=len(blob), sha256=digest)
        )

    add("map", "row_map", "slaif-raw-row-map-v1", data, 16 * 1048576)
    add(
        "members",
        "source_membership",
        "slaif-raw-source-membership-v1",
        member.membership_bytes,
        8 * 1048576,
    )
    parts = []
    for i, (part, digest) in enumerate(sorted(mapping.partition_hashes)):
        deadline()
        dense = raw_snapshot_dense.build_partition(originals, derived, data, part)
        deadline()
        add(
            f"z/{i}dense",
            "dense",
            "slaif-normalized-fp32le-d1024-npy-v1",
            dense.container_bytes,
            raw_snapshot_dense.POLICY.max_bytes,
        )
        del dense
        deadline()
        terms = raw_snapshot_lexical.build_partition(originals, derived, data, part)
        deadline()
        add(f"z/{i}terms", "lexical_terms", "slaif-raw-lexical-terms-v1", terms, 16 * 1048576)
        del terms
        parts.append(
            dict(
                partition_id=part,
                row_count=sum(r.partition_id == part for r in mapping.rows),
                row_map_sha256=digest,
                dense_path=f"z/{i}dense",
                lexical_path=f"z/{i}terms",
            )
        )
    core = dict(
        schema=1,
        kind="slaif-raw-snapshot-core-v1",
        representation="raw",
        embedding=dict(
            space_id=mapping.space_id,
            definition_fingerprint=mapping.definition_fingerprint,
            query_policy_fingerprint=context["query_policy_fingerprint"],
            query_execution_fingerprint=context["query_execution_fingerprint"],
            corpus_execution_fingerprints=sorted({r.execution_fingerprint for r in mapping.rows}),
            normalization_policy_id=mapping.normalization_policy_id,
            precision_qualification_ref=context["precision_qualification_ref"],
        ),
        analyzer=dict(
            fingerprint=analyzer[7:],
            backend="bm25s-lucene",
            bm25s_version="0.2.14",
            numpy_version="2.5.4",
            scipy_version="1.18.1",
        ),
        chunk_policy_fingerprint=mapping.chunk_policy_fingerprint,
        representation_policy_fingerprint=mapping.representation_policy_fingerprint,
        sources=dict(active_revisions=active, withdrawn_revisions=list(withdrawn)),
        row_count=len(mapping.rows),
        row_map_path="map",
        membership_path="members",
        files=sorted(descriptors, key=lambda d: d["path"]),
        partitions=parts,
        validation=dict(state="passed", validator_fingerprint=VALIDATION_POLICY_FINGERPRINT),
    )
    core_bytes = _json(core)
    _check(len(core_bytes) <= 262144)
    files = tuple(sorted(payloads))
    deadline()
    manifest = raw_snapshot_manifest.parse(core_bytes)
    deadline()
    bound = raw_snapshot_files.validate_files(originals, derived, core_bytes, files)
    deadline()
    snapshot_id = "sha256:" + hashlib.sha256(core_bytes).hexdigest()
    _check(
        bound.snapshot_id == manifest.snapshot_id == snapshot_id and bound.core_bytes == core_bytes
    )
    _check(
        tuple((d.path, d.bytes, d.sha256) for d in manifest.files)
        == tuple((p, len(b), hashlib.sha256(b).hexdigest()) for p, b in files)
    )
    result = BuiltSnapshotFiles(
        core_bytes,
        files,
        snapshot_id,
        len(mapping.rows),
        len(parts),
        len(member.entries),
        VALIDATION_POLICY_FINGERPRINT,
    )
    del bound
    deadline()
    return result
