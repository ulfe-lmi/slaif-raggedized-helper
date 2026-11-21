"""Supplied-policy wire decoder (objective 009, PAR-009-SUPPLIED-POLICY-WIRE-A).

Implements the FINAL private component contract v1
(``docs/parallel/supplied-policy-wire-v1.md``): a closed pure decoder for
the exact framed payload of the typed supplied-policy component
(``supplied_policy.py``), returning the real typed admitted object.

The decoder performs structural admission only: exact bytes, type and
length gates, bounds-first framing over a monotone offset, strict UTF-8,
actual material M and actual canonical C accounting for this exact
grammar, and reconstruction of real ``PrincipalSpec`` and ``DocumentRule``
records. Every Grants record is reconstructed through the real public
controlled-mapping admission
(``provenance_records.admit_record``), and every domain check, the
authoritative Grants snapshots and the framed identity hash remain in the
real typed ``admit_policy``. The decoder never replaces the typed API.

This module performs no I/O, no configuration, no model/provider work and
no credential acquisition or currentness check. It is a private
supplied-policy prerequisite: protected selection, issuance, delivery and
application policy remain separate obligations. An admission seal is
ordinary API discipline, not an OS security boundary.
"""

from __future__ import annotations

from .provenance_records import admit_record
from .supplied_policy import DocumentRule, PrincipalSpec, SuppliedPolicy, admit_policy

__all__ = [
    "PolicyWireError",
    "admit_policy_bytes",
]

_WIRE_ERROR_MESSAGE = "invalid supplied policy wire"

_FRAMING_MAGIC = b"slaif-supplied-policy-view-v1\n"
_MIN_WIRE_BYTES = 42
_MAX_WIRE_BYTES = 67_108_864
_MAX_MATERIAL_BYTES = 67_108_864
_MAX_STRING_UTF8_BYTES = 1_048_576
_SCHEMA = 1
_U32_BYTES = 4
_VERIFIER_BYTES = 32
_MAX_PRINCIPALS = 256
_MAX_DOCUMENTS = 20_000
_MAX_OPERATIONS = 3
_MAX_GRANTS_VALUES = 128
_MAX_ADMITTED_PER_DOCUMENT = 64
_MAX_ADMITTED_TOTAL = 65_536
_MAX_PRINCIPAL_ID_BYTES = 128
_MAX_OPERATION_BYTES = 12
_MAX_DOCUMENT_ID_BYTES = 1024
_MAX_REVISION_ID_BYTES = 71
_MAX_SCOPE_DIGEST_BYTES = 64


class PolicyWireError(ValueError):
    """Input-free failure at the public supplied-policy wire boundary."""


class _WireInvalid(Exception):
    """Internal rejection marker; never escapes a public boundary."""

    def __init__(self) -> None:
        super().__init__()


class _Cursor:
    """Monotone offset over exact wire bytes; every read is bounds-first."""

    __slots__ = ("_data", "_pos")

    def __init__(self, data: bytes, pos: int) -> None:
        self._data = data
        self._pos = pos

    def u32(self) -> int:
        data = self._data
        pos = self._pos
        if pos + _U32_BYTES > len(data):
            raise _WireInvalid()
        value = int.from_bytes(data[pos : pos + _U32_BYTES], "big")
        self._pos = pos + _U32_BYTES
        return value

    def framed_text(self, field_max_bytes: int) -> str:
        # Length frame, then both byte bounds, then remaining data: the
        # slice and the strict UTF-8 decode only happen once the declared
        # length is bounded AND fully present. The declared length is
        # checked before remaining data so an over-bound declaration is
        # refused without scanning; a bounded declaration whose bytes are
        # not fully present is refused before any slice.
        data = self._data
        pos = self._pos
        if pos + _U32_BYTES > len(data):
            raise _WireInvalid()
        declared = int.from_bytes(data[pos : pos + _U32_BYTES], "big")
        pos += _U32_BYTES
        if declared > _MAX_STRING_UTF8_BYTES or declared > field_max_bytes:
            raise _WireInvalid()
        if pos + declared > len(data):
            raise _WireInvalid()
        self._pos = pos + declared
        return data[pos : pos + declared].decode("utf-8")

    def fixed_bytes(self, length: int) -> bytes:
        data = self._data
        pos = self._pos
        if pos + length > len(data):
            raise _WireInvalid()
        self._pos = pos + length
        return data[pos : pos + length]

    def at_end(self) -> bool:
        return self._pos == len(self._data)


def _decode_policy_bytes(data: bytes) -> SuppliedPolicy:
    # Type and length precede any field work.
    if type(data) is not bytes:
        raise _WireInvalid()
    size = len(data)
    if not _MIN_WIRE_BYTES <= size <= _MAX_WIRE_BYTES:
        raise _WireInvalid()
    if data[: len(_FRAMING_MAGIC)] != _FRAMING_MAGIC:
        raise _WireInvalid()

    cursor = _Cursor(data, len(_FRAMING_MAGIC))
    if cursor.u32() != _SCHEMA:
        raise _WireInvalid()

    principal_count = cursor.u32()
    if principal_count > _MAX_PRINCIPALS:
        raise _WireInvalid()

    material = 0
    operation_frames = 0
    grants_frames = 0
    principal_views = []
    for _ in range(principal_count):
        principal_id = cursor.framed_text(_MAX_PRINCIPAL_ID_BYTES)
        material += len(principal_id.encode("utf-8"))
        if material > _MAX_MATERIAL_BYTES:
            raise _WireInvalid()

        # The verifier length frame must be exactly 32 before its body.
        if cursor.u32() != _VERIFIER_BYTES:
            raise _WireInvalid()
        verifier = cursor.fixed_bytes(_VERIFIER_BYTES)
        material += _VERIFIER_BYTES
        if material > _MAX_MATERIAL_BYTES:
            raise _WireInvalid()

        operation_count = cursor.u32()
        if not 1 <= operation_count <= _MAX_OPERATIONS:
            raise _WireInvalid()
        operations = []
        for _ in range(operation_count):
            operation = cursor.framed_text(_MAX_OPERATION_BYTES)
            material += len(operation.encode("utf-8"))
            if material > _MAX_MATERIAL_BYTES:
                raise _WireInvalid()
            operations.append(operation)
        operation_frames += operation_count

        if cursor.u32() != _SCHEMA:
            raise _WireInvalid()
        grant_vectors = []
        for _ in range(3):
            value_count = cursor.u32()
            if value_count > _MAX_GRANTS_VALUES:
                raise _WireInvalid()
            values = []
            for _ in range(value_count):
                value = cursor.framed_text(_MAX_STRING_UTF8_BYTES)
                material += len(value.encode("utf-8"))
                if material > _MAX_MATERIAL_BYTES:
                    raise _WireInvalid()
                values.append(value)
            grant_vectors.append(tuple(values))
            grants_frames += value_count
        principal_views.append((principal_id, verifier, tuple(operations), tuple(grant_vectors)))

    document_count = cursor.u32()
    if document_count > _MAX_DOCUMENTS:
        raise _WireInvalid()

    document_views = []
    total_pairs = 0
    for _ in range(document_count):
        document_id = cursor.framed_text(_MAX_DOCUMENT_ID_BYTES)
        material += len(document_id.encode("utf-8"))
        if material > _MAX_MATERIAL_BYTES:
            raise _WireInvalid()

        pair_count = cursor.u32()
        if pair_count > _MAX_ADMITTED_PER_DOCUMENT:
            raise _WireInvalid()
        if total_pairs + pair_count > _MAX_ADMITTED_TOTAL:
            raise _WireInvalid()
        pairs = []
        for _ in range(pair_count):
            revision_id = cursor.framed_text(_MAX_REVISION_ID_BYTES)
            material += len(revision_id.encode("utf-8"))
            if material > _MAX_MATERIAL_BYTES:
                raise _WireInvalid()
            scope_digest = cursor.framed_text(_MAX_SCOPE_DIGEST_BYTES)
            material += len(scope_digest.encode("utf-8"))
            if material > _MAX_MATERIAL_BYTES:
                raise _WireInvalid()
            pairs.append((revision_id, scope_digest))
        total_pairs += pair_count
        document_views.append((document_id, tuple(pairs)))

    if not cursor.at_end():
        raise _WireInvalid()

    # Actual C for this exact grammar: M already accumulated per
    # occurrence; H from the exact count formula. The sufficient-but-not-
    # necessary 66021078 material threshold is NOT imposed.
    string_frames = (
        principal_count + operation_frames + grants_frames + document_count + 2 * total_pairs
    )
    framing = 42 + 4 * string_frames + 24 * principal_count + 4 * document_count
    if material + framing > _MAX_MATERIAL_BYTES:
        raise _WireInvalid()

    # Reconstruct real nominal DTO records without sorting, normalizing or
    # coercing; each Grants record through the controlled public mapping
    # with exactly four keys. The real typed factory then performs every
    # domain check, re-snapshots Grants and computes the framed hash.
    principals = [
        PrincipalSpec(
            principal_id,
            verifier,
            operations,
            admit_record(
                "Grants",
                {
                    "schema_version": _SCHEMA,
                    "corpora": corpora,
                    "versions": versions,
                    "labels": labels,
                },
            ),
        )
        for principal_id, verifier, operations, (corpora, versions, labels) in principal_views
    ]
    documents = [DocumentRule(document_id, pairs) for document_id, pairs in document_views]
    return admit_policy(tuple(principals), tuple(documents))


def admit_policy_bytes(data: bytes) -> SuppliedPolicy:
    """Closed pure admission of exact framed supplied-policy bytes.

    Accepts only exact ``bytes`` of length 42 through 67108864 shaped as
    the typed component's exact framed payload (contract v1 "Boundary").
    Structural admission (framing, strict UTF-8, actual M and C for this
    exact grammar) happens here; all domain checks, the authoritative
    Grants snapshots and the framed identity hash remain in the real
    typed ``admit_policy``. All ordinary failures raise one fixed
    input-free :class:`PolicyWireError` with no own caught payload as
    cause or context; a non-Exception BaseException propagates by
    identity. No partial output, no I/O, no currentness check.
    """
    error = None
    try:
        result = _decode_policy_bytes(data)
    except _WireInvalid:
        error = PolicyWireError(_WIRE_ERROR_MESSAGE)
    except Exception:
        error = PolicyWireError(_WIRE_ERROR_MESSAGE)
    # Raised after the handlers, so the frame holds no active exception
    # and the public error carries neither __cause__ nor __context__ from
    # the caught payload. Not a zeroization or traceback-locals claim.
    if error is not None:
        raise error
    return result
