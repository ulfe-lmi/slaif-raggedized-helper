"""Pure, bounded codec for declared raw snapshot cores."""

import hashlib
import json
import re
from dataclasses import dataclass

from .embedding_vectors import POLICY_ID


class ManifestError(ValueError):
    """Invalid manifest; details deliberately omitted."""


@dataclass(frozen=True, slots=True)
class FileDescriptor:
    path: str
    role: str
    schema: str
    bytes: int
    sha256: str


@dataclass(frozen=True, slots=True)
class PartitionDescriptor:
    partition_id: str
    row_count: int
    row_map_sha256: str
    dense_path: str
    lexical_path: str


@dataclass(frozen=True, slots=True)
class RawSnapshotManifest:
    core_bytes: bytes
    snapshot_id: str
    files: tuple[FileDescriptor, ...]
    partitions: tuple[PartitionDescriptor, ...]
    active_revisions: tuple[str, ...]
    withdrawn_revisions: tuple[str, ...]


def _check(value):
    if not value:
        raise ManifestError()


def _keys(obj, keys):
    _check(type(obj) is dict and set(obj) == set(keys.split()))


def _integer(value, low, high):
    _check(type(value) is int and low <= value <= high)


def _hex(value, prefix=""):
    _check(
        type(value) is str and re.fullmatch(re.escape(prefix) + "[0-9a-f]{64}", value) is not None
    )


def _path(value):
    _check(
        type(value) is str
        and len(value) <= 240
        and re.fullmatch(r"[a-z0-9][a-z0-9_.-]{0,79}(?:/[a-z0-9][a-z0-9_.-]{0,79}){0,3}", value)
        is not None
    )


def _list(value, limit):
    _check(type(value) is list and len(value) <= limit)


def _ordered(value):
    _check(value == sorted(set(value)))


def _pairs(pairs):
    obj = {}
    for key, value in pairs:
        _check(key not in obj)
        obj[key] = value
    return obj


def parse(core_bytes: bytes) -> RawSnapshotManifest:
    """Parse canonical bytes; validity only describes the declared core."""
    try:
        return _parse(core_bytes)
    except Exception:
        raise ManifestError() from None


def _parse(data):
    _check(type(data) is bytes and 0 < len(data) <= 262144)
    obj = json.loads(
        data.decode("ascii"),
        object_pairs_hook=_pairs,
        parse_float=lambda _: (_ for _ in ()).throw(ManifestError()),
        parse_constant=lambda _: (_ for _ in ()).throw(ManifestError()),
    )
    _check(
        json.dumps(
            obj, sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False
        ).encode("ascii")
        == data
    )
    _keys(
        obj,
        "schema kind representation embedding analyzer chunk_policy_fingerprint "
        "representation_policy_fingerprint sources row_count row_map_path "
        "membership_path files partitions validation",
    )
    _check(
        type(obj["schema"]) is int
        and obj["schema"] == 1
        and obj["kind"] == "slaif-raw-snapshot-core-v1"
        and obj["representation"] == "raw"
    )
    _integer(obj["row_count"], 0, 4096)
    for k in ("chunk_policy_fingerprint", "representation_policy_fingerprint"):
        _hex(obj[k])
    e = obj["embedding"]
    _keys(
        e,
        "space_id definition_fingerprint query_policy_fingerprint "
        "query_execution_fingerprint corpus_execution_fingerprints "
        "normalization_policy_id precision_qualification_ref",
    )
    for k in ("space_id", "query_policy_fingerprint", "query_execution_fingerprint"):
        _hex(e[k])
    _hex(e["definition_fingerprint"], "sha256:")
    _check(e["normalization_policy_id"] == POLICY_ID)
    if e["precision_qualification_ref"] is not None:
        _hex(e["precision_qualification_ref"], "sha256:")
    executions = e["corpus_execution_fingerprints"]
    _list(executions, 128)
    for v in executions:
        _hex(v)
    _ordered(executions)
    _check(not obj["row_count"] or executions)
    a = obj["analyzer"]
    _keys(a, "fingerprint backend bm25s_version numpy_version scipy_version")
    _hex(a["fingerprint"])
    _check(
        (a["backend"], a["bm25s_version"], a["numpy_version"], a["scipy_version"])
        == ("bm25s-lucene", "0.2.14", "2.5.4", "1.18.1")
    )
    s = obj["sources"]
    _keys(s, "active_revisions withdrawn_revisions")
    for values in s.values():
        _list(values, 1024)
        for v in values:
            _hex(v, "sha256:")
        _ordered(values)
    _check(not set(s["active_revisions"]) & set(s["withdrawn_revisions"]))
    v = obj["validation"]
    _keys(v, "state validator_fingerprint")
    _check(v["state"] in ("unproven", "passed", "failed"))
    if v["state"] == "unproven":
        _check(v["validator_fingerprint"] is None)
    else:
        _hex(v["validator_fingerprint"])
    roles = {
        "row_map": "slaif-raw-row-map-v1",
        "source_membership": "slaif-raw-source-membership-v1",
        "dense": "slaif-normalized-fp32le-d1024-npy-v1",
        "lexical_terms": "slaif-raw-lexical-terms-v1",
    }
    _list(obj["files"], 258)
    files = []
    for f in obj["files"]:
        _keys(f, "path role schema bytes sha256")
        _path(f["path"])
        _check(type(f["role"]) is str and f["role"] in roles and f["schema"] == roles[f["role"]])
        _integer(f["bytes"], 0, (64 if f["role"] == "dense" else 16) * 1048576)
        _hex(f["sha256"])
        files.append(FileDescriptor(**f))
    _ordered([f.path for f in files])
    _check(sum(f.bytes for f in files) <= 96 * 1048576)
    by_path = {f.path: f for f in files}
    used = set()

    def use(path, role):
        _path(path)
        _check(path in by_path and path not in used and by_path[path].role == role)
        used.add(path)

    use(obj["row_map_path"], "row_map")
    use(obj["membership_path"], "source_membership")
    _list(obj["partitions"], 128)
    partitions = []
    for p in obj["partitions"]:
        _keys(p, "partition_id row_count row_map_sha256 dense_path lexical_path")
        _hex(p["partition_id"], "sha256:")
        _integer(p["row_count"], 1, 4096)
        _hex(p["row_map_sha256"])
        use(p["dense_path"], "dense")
        use(p["lexical_path"], "lexical_terms")
        partitions.append(PartitionDescriptor(**p))
    _ordered([p.partition_id for p in partitions])
    _check(sum(p.row_count for p in partitions) == obj["row_count"] and len(used) == len(files))
    return RawSnapshotManifest(
        data,
        "sha256:" + hashlib.sha256(data).hexdigest(),
        tuple(files),
        tuple(partitions),
        tuple(s["active_revisions"]),
        tuple(s["withdrawn_revisions"]),
    )
