"""Supplied raw membership eligibility under a genuine supplied policy (PAR-009).

Pure in-memory derivation of the raw partition IDs that are unavailable under
a genuine factory-admitted supplied policy for one admitted supplied raw
membership capture (objective 009,
PAR-009-SUPPLIED-MEMBERSHIP-ELIGIBILITY-A).

Scope of this slice: for each entry of a re-admitted supplied raw membership,
the entry's exact canonical scope bytes are re-admitted through
``provenance_records.admit_record("Scope", ...)`` to obtain the document id
(an entry carries no direct document_id). The policy's already canonical
sorted document rules are located by binary search, and the entry's exact
``(revision_id, source_scope_sha256)`` pair must be admitted by that
document's rule. A missing rule, a missing pair or an empty rule makes the
complete entry partition unavailable. Admitted zero-row entries are included
under this conservative membership rule. The result is the unique sorted
tuple of unavailable partition IDs derived only from this captured
membership.

The membership DTO is constructible and nominal: its exact class is required,
but the nominal constructor is never assumed to authenticate a capture. For
this pure slice the exact canonical ``membership_bytes`` are re-admitted
through the existing ``raw_snapshot_membership.parse`` and full type/field
agreement between the DTO and the re-admitted capture is required before any
field is used. The established ``qualification.parity_io._depth_check`` runs
on strict ASCII text decoded only after the existing 8 MiB byte bound and
before that parser, so arbitrarily deep bytes cannot go through unguarded
JSON decoding.

No I/O, no filesystem calls, no current-policy verification, no principal
traversal and no credential handling. A result is supplied declaration plus
admitted-capture evidence only: it is not current application authorization,
and a future trusted operator may avoid repeating whole membership admission
on real bound pin evidence, scoped separately.
"""

from __future__ import annotations

from . import provenance_records, raw_snapshot_membership, supplied_policy
from .qualification import parity_io
from .raw_snapshot_membership import Membership
from .supplied_policy import SuppliedPolicy

__all__ = [
    "PolicyEligibilityError",
    "unavailable_partitions",
]

_POLICY_ELIGIBILITY_ERROR_MESSAGE = "invalid supplied membership eligibility"


class PolicyEligibilityError(ValueError):
    """Fixed input-free failure at the public supplied-eligibility boundary."""


class _Rejected(Exception):
    """Internal rejection marker; never escapes the public boundary."""

    def __init__(self) -> None:
        super().__init__()


def _find_rule(documents, document_id: str):
    """Binary search of the canonical ascending document rules.

    The factory admits documents in strict ascending document_id order, so a
    plain binary search over the already canonical tuple is exact. No copy,
    reparse or rebuild of the complete policy is performed.
    """
    low, high = 0, len(documents)
    while low < high:
        mid = (low + high) // 2
        if documents[mid].document_id < document_id:
            low = mid + 1
        else:
            high = mid
    if low < len(documents) and documents[low].document_id == document_id:
        return documents[low]
    return None


def _unavailable_inner(policy: SuppliedPolicy, membership: Membership) -> tuple[str, ...]:
    # Exact factory-owned policy carrying the existing typed admission marker.
    if (
        type(policy) is not supplied_policy.SuppliedPolicy
        or getattr(policy, "_admitted", None) is not supplied_policy._ADMITTED_MARKER
    ):
        raise _Rejected()
    # Nominal constructible DTO: use its exact class without assuming the
    # nominal constructor authenticates a capture.
    if type(membership) is not raw_snapshot_membership.Membership:
        raise _Rejected()
    membership_bytes = membership.membership_bytes
    if type(membership_bytes) is not bytes:
        raise _Rejected()
    # Existing 8 MiB byte bound first, strict ASCII decode, then the
    # established depth pre-check, so arbitrarily deep bytes never reach the
    # unguarded JSON decode inside the membership parser.
    if not 0 < len(membership_bytes) <= raw_snapshot_membership._LIMIT:
        raise _Rejected()
    parity_io._depth_check(membership_bytes.decode("ascii"))
    # Re-admit the exact canonical capture bytes through the existing parser.
    admitted = raw_snapshot_membership.parse(membership_bytes)
    _check_dto_agreement(admitted, membership, membership_bytes)
    unavailable = set()
    for entry in admitted.entries:
        # The entry carries no direct document_id: re-admit its exact
        # canonical scope bytes to obtain it.
        scope = provenance_records.admit_record("Scope", entry.scope_bytes)
        rule = _find_rule(policy.documents, scope.document_id)
        pair = (entry.revision_id, entry.source_scope_sha256)
        # A missing rule, a missing pair or an empty rule makes the complete
        # entry partition unavailable; zero-row entries are included.
        if rule is None or pair not in rule.admitted:
            unavailable.add(entry.partition_id)
    return tuple(sorted(unavailable))


def _check_dto_agreement(admitted, membership, membership_bytes) -> None:
    """Full type/field agreement between the nominal DTO and the capture.

    Exact builtin scalar, tuple and Entry contracts are verified BEFORE any
    value comparison, so caller-supplied equality hooks are never reached;
    tuple lengths are checked against the admitted reference before any
    traversal. Only verified exact values are then compared, and only the
    re-admitted entries are used downstream.
    """
    sha256 = membership.sha256
    row_map_sha256 = membership.row_map_sha256
    row_count = membership.row_count
    entries = membership.entries
    withdrawn = membership.withdrawn_revisions
    if type(sha256) is not str or type(row_map_sha256) is not str:
        raise _Rejected()
    # Exact int: bool is a subclass of int and True equals 1, so it must not
    # be admitted as a row count.
    if type(row_count) is not int:
        raise _Rejected()
    if type(entries) is not tuple or len(entries) != len(admitted.entries):
        raise _Rejected()
    for dto_entry, admitted_entry in zip(entries, admitted.entries):
        if type(dto_entry) is not raw_snapshot_membership.Entry:
            raise _Rejected()
        for field in (
            "revision_id",
            "extraction_id",
            "bundle_container_id",
            "bundle_metadata_sha256",
            "chunk_policy_fingerprint",
            "source_scope_sha256",
            "partition_id",
        ):
            if type(getattr(dto_entry, field)) is not str:
                raise _Rejected()
        if type(dto_entry.scope_bytes) is not bytes:
            raise _Rejected()
        ordinals = dto_entry.ordinals
        if type(ordinals) is not tuple or len(ordinals) != len(admitted_entry.ordinals):
            raise _Rejected()
        for value in ordinals:
            # Exact int per ordinal: True equals 1 and must not be admitted.
            if type(value) is not int:
                raise _Rejected()
    if type(withdrawn) is not tuple or len(withdrawn) != len(admitted.withdrawn_revisions):
        raise _Rejected()
    for value in withdrawn:
        if type(value) is not str:
            raise _Rejected()
    if (
        sha256 != admitted.sha256
        or row_map_sha256 != admitted.row_map_sha256
        or row_count != admitted.row_count
        or entries != admitted.entries
        or withdrawn != admitted.withdrawn_revisions
        or membership_bytes != admitted.membership_bytes
    ):
        raise _Rejected()


def unavailable_partitions(policy: SuppliedPolicy, membership: Membership) -> tuple[str, ...]:
    """Derive the unavailable raw partition IDs for one admitted capture.

    Pure: no I/O, no current-policy verification, no credential handling.
    Any invalid input raises the fixed input-free
    :class:`PolicyEligibilityError` (a ``ValueError``) carrying no caught
    cause or context; interruption identity propagates unchanged.
    """
    error = None
    try:
        return _unavailable_inner(policy, membership)
    except Exception:
        error = PolicyEligibilityError(_POLICY_ELIGIBILITY_ERROR_MESSAGE)
    # Raised after the handler, so the frame holds no active exception and
    # the fixed error carries neither __cause__ nor __context__.
    if error is not None:
        raise error
