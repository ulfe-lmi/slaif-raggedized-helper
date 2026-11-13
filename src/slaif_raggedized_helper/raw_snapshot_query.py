"""Private, borrowed pinned query composition; not an authentication boundary."""

from dataclasses import dataclass
import hashlib
import json
import math
import re
import time

from . import derived_store, provenance_records as records, query_embedding
from . import raw_dense_search as dense, raw_hybrid_search as hybrid
from . import raw_lexical_search as lexical, raw_snapshot_manifest as manifest
from . import raw_snapshot_pin as pin, raw_snapshot_publication as publication
from . import raw_snapshot_files as files, raw_snapshot_selection as selection
from .source_admission import OriginalStore


class PinnedQueryError(ValueError):
    """Content-free refusal of the entire query."""


class ScopeUnavailableError(PinnedQueryError):
    """An affected readable scope cannot be queried."""


class _Unavailable(Exception):
    pass


@dataclass(frozen=True, slots=True)
class QueryAdmission:
    snapshot_id: str
    core_sha256: str
    question_sha256: str
    operation: str = "search"


@dataclass(frozen=True, slots=True)
class QueryAuthority:
    epoch: str
    grants: records.Grants
    restrictions: records.Restrictions | None
    unavailable_partitions: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class PinnedQueryResult:
    snapshot_id: str
    generation: int
    pointer_bytes: bytes
    question_sha256: str
    query_payload_sha256: str
    query_execution_fingerprint: str
    authority_sha256: str
    policy_epoch: str
    hybrid: hybrid.HybridResult
    execution_origin: str = "SUPPLIED_UNVERIFIED"
    authorization_status: str = "SUPPLIED_POLICY_PROVIDER_ONLY"
    qualification: str = "NOT_QUALIFIED"


def _check(value):
    if not value:
        raise ValueError


def _hex(value, prefix=""):
    return (
        type(value) is str and re.fullmatch(re.escape(prefix) + r"[0-9a-f]{64}", value) is not None
    )


def search_pinned_data(
    originals,
    derived,
    store_root,
    pin_owner,
    encoder,
    text,
    authorization_provider,
    *,
    dense_k=60,
    lexical_k=60,
    partition_cap=60,
    k=60,
    deadline_ms=120000,
    trace=False,
):
    """Borrow active owners for one query; caller retains exclusive lifetime ownership."""
    try:
        return _search(
            originals,
            derived,
            store_root,
            pin_owner,
            encoder,
            text,
            authorization_provider,
            dense_k,
            lexical_k,
            partition_cap,
            k,
            deadline_ms,
            trace,
        )
    except _Unavailable:
        raise ScopeUnavailableError("query scope unavailable") from None
    except Exception:
        raise PinnedQueryError("pinned query refused") from None


def _search(
    originals, derived, root, owner, encoder, text, provider, dk, lk, cap, k, deadline_ms, trace
):
    _check(type(deadline_ms) is int and 1 <= deadline_ms <= 120000)
    end = time.monotonic() + deadline_ms / 1000

    def remaining():
        ms = math.floor((end - time.monotonic()) * 1000)
        _check(ms > 0)
        return ms

    _check(type(originals) is OriginalStore and type(derived) is derived_store.Store)
    publication._path_check(root)
    _check(len(root[1:].split("/")) <= 64)
    _check(
        type(owner) is pin.PinOwner
        and owner.state == "ACTIVE"
        and owner.op.path == root
        and owner.originals is originals
        and owner.derived is derived
    )
    _check(type(encoder) is query_embedding.ResidentQueryEncoder and encoder._state == "open")
    _check(callable(provider) and type(trace) is bool)
    _check(all(type(v) is int and 1 <= v <= 60 for v in (dk, lk, cap, k)))
    query_embedding._query(text)
    question_sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
    remaining()
    captured = owner.check(deadline_ms=remaining())
    remaining()
    _check(type(captured) is pin.PinData)
    pointer, data = captured.pointer, captured.data
    _check(type(pointer) is selection.Pointer and type(data) is files.BoundSnapshotData)
    parsed = manifest.parse(data.core_bytes)
    remaining()
    _check(
        parsed.snapshot_id == data.snapshot_id == pointer.snapshot_id
        and hashlib.sha256(data.core_bytes).hexdigest() == pointer.core_sha256
    )
    embedding = json.loads(data.core_bytes)["embedding"]
    admission = QueryAdmission(pointer.snapshot_id, pointer.core_sha256, question_sha)
    entries = data.membership.entries
    partitions = {entry.partition_id for entry in entries}

    def policy(boundary):
        remaining()
        value = provider(boundary, admission)
        remaining()
        _check(type(value) is QueryAuthority and _hex(value.epoch))
        grants, restrictions = lexical._authority(value.grants, value.restrictions)
        _check(grants is not None)
        unavailable = value.unavailable_partitions
        _check(type(unavailable) is tuple and len(unavailable) <= 128)
        _check(all(_hex(item, "sha256:") for item in unavailable))
        _check(tuple(sorted(set(unavailable))) == unavailable and set(unavailable) <= partitions)
        authority_hash = lexical._authority_hash(grants, restrictions)
        remaining()
        return value.epoch, grants, restrictions, unavailable, authority_hash

    def check_pin():
        remaining()
        _check(owner.check(deadline_ms=remaining()) == captured)
        remaining()

    first = policy("before_encode")
    for entry in entries:
        remaining()
        if entry.partition_id in first[3]:
            scope = records.admit_record("Scope", entry.scope_bytes)
            if records.reader_allows(scope, first[1], first[2]):
                raise _Unavailable()
    check_pin()
    remaining()
    encoded = encoder.encode_query(text)
    remaining()
    _check(
        type(encoded) is query_embedding.QueryEmbedding
        and type(encoded.payload) is bytes
        and len(encoded.payload) == 4096
        and _hex(encoded.payload_sha256)
        and hashlib.sha256(encoded.payload).hexdigest() == encoded.payload_sha256
        and _hex(encoded.space_id)
        and _hex(encoded.definition_fingerprint, "sha256:")
        and _hex(encoded.query_policy_id)
        and _hex(encoded.execution_fingerprint, "sha256:")
    )
    execution = encoded.execution_fingerprint[7:]
    _check(
        (encoded.space_id, encoded.definition_fingerprint, encoded.query_policy_id, execution)
        == (
            embedding["space_id"],
            embedding["definition_fingerprint"],
            embedding["query_policy_fingerprint"],
            embedding["query_execution_fingerprint"],
        )
    )

    def same_policy(boundary):
        fresh = policy(boundary)
        _check((fresh[0], fresh[3], fresh[4]) == (first[0], first[3], first[4]))

    same_policy("before_retrieval")
    check_pin()
    result = hybrid.search(
        originals,
        derived,
        root,
        pointer.snapshot_id,
        text,
        encoded.payload,
        query_space_id=encoded.space_id,
        query_definition_fingerprint=encoded.definition_fingerprint,
        query_policy_id=encoded.query_policy_id,
        query_execution_fingerprint=execution,
        grants=first[1],
        restrictions=first[2],
        dense_k=dk,
        lexical_k=lk,
        partition_cap=cap,
        k=k,
        deadline_ms=remaining(),
        trace=trace,
    )
    remaining()
    _check(
        type(result) is hybrid.HybridResult
        and (
            result.snapshot_id,
            result.query_text_sha256,
            result.query_payload_sha256,
            result.authority_sha256,
            result.query_origin,
            result.qualification,
        )
        == (
            pointer.snapshot_id,
            question_sha,
            encoded.payload_sha256,
            first[4],
            "SUPPLIED_UNVERIFIED",
            "NOT_QUALIFIED",
        )
    )
    for part, cls in ((result.dense, dense.DenseTrace), (result.lexical, lexical.LexicalTrace)):
        t = part.trace
        if trace:
            _check(
                type(t) is cls
                and (t.input_origin, t.qualification, t.authorization_status, t.execution_status)
                == (
                    "SUPPLIED_UNVERIFIED",
                    "NOT_QUALIFIED",
                    "SUPPLIED_SCOPE_CHECKS_ONLY",
                    "NOT_ATTESTED",
                )
            )
        else:
            _check(t is None)
    check_pin()
    same_policy("before_return")
    output = PinnedQueryResult(
        pointer.snapshot_id,
        pointer.generation,
        pointer.pointer_bytes,
        question_sha,
        encoded.payload_sha256,
        execution,
        first[4],
        first[0],
        result,
    )
    remaining()
    return output
