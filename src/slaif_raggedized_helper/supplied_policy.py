"""Supplied-policy declaration and matching primitives (objective 009, PAR-009).

Implements the FINAL private component contract v1
(``docs/parallel/supplied-policy-primitives-v1.md``): closed typed admission
of a caller-supplied policy view, exact domain-separated framed identity
computed by a bounded stream, and genuine fullscan supplied-credential
matching through ``hmac.compare_digest``.

A successful match is labelled ``SUPPLIED_POLICY_MATCH_ONLY``. It is supplied
declaration plus admitted-credential evidence only: it is not current
application authorization, current-policy verification, credential
provisioning, deployment or release. This module performs no I/O, no
configuration, no model/provider work and no credential acquisition; it only
hashes explicitly supplied bytes. An admission seal is ordinary API
discipline, not an OS security boundary.
"""

from __future__ import annotations

import hashlib
import hmac
import re
from dataclasses import dataclass

from .provenance_records import Grants, admit_record

__all__ = [
    "DocumentRule",
    "PrincipalSpec",
    "PolicyError",
    "SuppliedMatch",
    "SuppliedPolicy",
    "admit_policy",
    "match_supplied",
]

_POLICY_ERROR_MESSAGE = "invalid supplied policy"
_SUPPLIED_POLICY_MATCH_ONLY = "SUPPLIED_POLICY_MATCH_ONLY"

_OPERATION_VOCABULARY = ("answer", "search", "sources:read")
_MAX_PRINCIPALS = 256
_MAX_DOCUMENTS = 20000
_MAX_OPERATIONS = 3
_MAX_GRANTS_VALUES = 128
_MAX_ADMITTED_PER_DOCUMENT = 64
_MAX_ADMITTED_TOTAL = 65536
_MAX_STRING_UTF8_BYTES = 1_048_576
_MAX_MATERIAL_BYTES = 67_108_864
_UTF8_CHUNK_CODEPOINTS = 1024
_MAX_UTF8_CHUNK_BYTES = 4096
_CREDENTIAL_MIN_BYTES = 43
_CREDENTIAL_MAX_BYTES = 256

_PRINCIPAL_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}")
_REVISION_ID_RE = re.compile(r"sha256:[0-9a-f]{64}")
_SCOPE_DIGEST_RE = re.compile(r"[0-9a-f]{64}")
_CREDENTIAL_ALPHABET = frozenset(
    b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789._~-"
)
_FRAMING_MAGIC = b"slaif-supplied-policy-view-v1\n"

_ADMITTED_MARKER = object()


class PolicyError(ValueError):
    """Input-free failure at the public supplied-policy boundary."""


class _Invalid(Exception):
    """Internal rejection marker; never escapes a public boundary."""

    def __init__(self) -> None:
        super().__init__()


@dataclass(frozen=True, slots=True)
class PrincipalSpec:
    """Declaration DTO for one principal; not admitted authority on its own."""

    principal_id: str
    verifier: bytes
    operations: tuple[str, ...]
    grants: Grants

    def __repr__(self) -> str:
        return "PrincipalSpec(<redacted>)"


@dataclass(frozen=True, slots=True)
class DocumentRule:
    """Declaration DTO for one document; not admitted authority on its own."""

    document_id: str
    admitted: tuple[tuple[str, str], ...]

    def __repr__(self) -> str:
        return "DocumentRule(<redacted>)"


@dataclass(frozen=True, slots=True)
class _AdmittedPrincipal:
    principal_id: str
    verifier: bytes
    operations: tuple[str, ...]
    grants: Grants

    def __repr__(self) -> str:
        return "AdmittedPrincipal(<redacted>)"


@dataclass(frozen=True, slots=True)
class _AdmittedDocument:
    document_id: str
    admitted: tuple[tuple[str, str], ...]

    def __repr__(self) -> str:
        return "AdmittedDocument(<redacted>)"


@dataclass(frozen=True, slots=True, init=False)
class SuppliedPolicy:
    """Factory-only admitted supplied-policy view; see :func:`admit_policy`.

    Frozen record: ordinary assignment and deletion of any field (including
    the internal marker) are refused. Internal construction uses private
    object assignment only.
    """

    principals: tuple
    documents: tuple
    policy_id: str
    _admitted: object

    def __init__(self, *_args, **_kwargs) -> None:
        raise PolicyError(_POLICY_ERROR_MESSAGE)

    def __repr__(self) -> str:
        return "SuppliedPolicy(<redacted>)"


@dataclass(frozen=True, slots=True, init=False)
class SuppliedMatch:
    """Factory-only match result; see :func:`match_supplied`.

    Carries exactly principal_id, grants (fresh real Grants snapshot),
    operations (the principal's FULL allowed tuple), policy_id and the fixed
    authorization_status label. No verifier, credential or document rule.
    Frozen record; its constructor cannot confer authority.
    """

    principal_id: str
    grants: Grants
    operations: tuple[str, ...]
    policy_id: str
    authorization_status: str
    _admitted: object

    def __init__(self, *_args, **_kwargs) -> None:
        raise PolicyError(_POLICY_ERROR_MESSAGE)

    def __repr__(self) -> str:
        return "SuppliedMatch(<redacted>)"


def _utf8_byte_length(value: str) -> int:
    """Exact UTF8 byte length; bounded chunks, early cap, surrogate-free."""
    if len(value) > _MAX_STRING_UTF8_BYTES:
        raise _Invalid()
    total = 0
    for start in range(0, len(value), _UTF8_CHUNK_CODEPOINTS):
        encoded = value[start : start + _UTF8_CHUNK_CODEPOINTS].encode("utf-8")
        if len(encoded) > _MAX_UTF8_CHUNK_BYTES:
            raise _Invalid()
        total += len(encoded)
        if total > _MAX_STRING_UTF8_BYTES:
            raise _Invalid()
    return total


def _check_principal_spec(item) -> None:
    if type(item) is not PrincipalSpec:
        raise _Invalid()
    principal_id = item.principal_id
    if type(principal_id) is not str or _PRINCIPAL_ID_RE.fullmatch(principal_id) is None:
        raise _Invalid()
    verifier = item.verifier
    if type(verifier) is not bytes or len(verifier) != 32:
        raise _Invalid()
    operations = item.operations
    if type(operations) is not tuple or not 1 <= len(operations) <= _MAX_OPERATIONS:
        raise _Invalid()
    for index, operation in enumerate(operations):
        if type(operation) is not str or operation not in _OPERATION_VOCABULARY:
            raise _Invalid()
        if index and operations[index - 1] >= operation:
            raise _Invalid()
    if "answer" in operations and "sources:read" not in operations:
        raise _Invalid()
    grants = item.grants
    if type(grants) is not Grants:
        raise _Invalid()
    if type(grants.schema_version) is not int or grants.schema_version != 1:
        raise _Invalid()
    for field in ("corpora", "versions", "labels"):
        values = getattr(grants, field)
        if type(values) is not tuple or len(values) > _MAX_GRANTS_VALUES:
            raise _Invalid()


def _u32(value: int) -> bytes:
    return value.to_bytes(4, "big")


def _framed_text(value):
    """Bounded framing: length frame from bounded count, then chunk bytes."""
    yield _u32(_utf8_byte_length(value))
    for start in range(0, len(value), _UTF8_CHUNK_CODEPOINTS):
        chunk = value[start : start + _UTF8_CHUNK_CODEPOINTS].encode("utf-8")
        if len(chunk) > _MAX_UTF8_CHUNK_BYTES:
            raise _Invalid()
        yield chunk


def _framed_payload(principals, documents):
    """Bounded per-part framing stream; never a complete canonical payload."""
    yield _FRAMING_MAGIC
    yield _u32(1)
    yield _u32(len(principals))
    for principal_id, verifier, operations, grants in principals:
        yield from _framed_text(principal_id)
        yield _u32(len(verifier))
        yield verifier
        yield _u32(len(operations))
        for operation in operations:
            yield from _framed_text(operation)
        yield _u32(1)
        for values in (grants.corpora, grants.versions, grants.labels):
            yield _u32(len(values))
            for value in values:
                yield from _framed_text(value)
    yield _u32(len(documents))
    for document_id, pairs in documents:
        yield from _framed_text(document_id)
        yield _u32(len(pairs))
        for revision_id, scope_digest in pairs:
            yield from _framed_text(revision_id)
            yield from _framed_text(scope_digest)


def _snapshot_grants(grants: Grants) -> Grants:
    """Re-admit checked grants through the public controlled-mapping API."""
    controlled_mapping = {
        "schema_version": grants.schema_version,
        "corpora": grants.corpora,
        "versions": grants.versions,
        "labels": grants.labels,
    }
    return admit_record("Grants", controlled_mapping)


def _admit_policy_inner(principals, documents) -> SuppliedPolicy:
    if type(principals) is not tuple or type(documents) is not tuple:
        raise _Invalid()
    principal_count = len(principals)
    document_count = len(documents)
    if principal_count > _MAX_PRINCIPALS or document_count > _MAX_DOCUMENTS:
        raise _Invalid()

    admitted = []
    seen_principal_ids = set()
    seen_verifiers = set()
    operation_frames = 0
    grants_string_frames = 0
    material = 0
    previous_id = None
    for item in principals:
        _check_principal_spec(item)
        principal_id = item.principal_id
        verifier = item.verifier
        if previous_id is not None and previous_id >= principal_id:
            raise _Invalid()
        previous_id = principal_id
        if principal_id in seen_principal_ids or verifier in seen_verifiers:
            raise _Invalid()
        seen_principal_ids.add(principal_id)
        seen_verifiers.add(verifier)
        operations = item.operations
        grants = item.grants
        grant_strings = grants.corpora + grants.versions + grants.labels
        operation_frames += len(operations)
        grants_string_frames += len(grant_strings)
        material += _utf8_byte_length(principal_id) + len(verifier)
        if material > _MAX_MATERIAL_BYTES:
            raise _Invalid()
        for operation in operations:
            material += len(operation)
            if material > _MAX_MATERIAL_BYTES:
                raise _Invalid()
        for values in (grants.corpora, grants.versions, grants.labels):
            previous = None
            for value in values:
                # Cheap codepoint bound before encoding: more codepoints
                # than the byte cap necessarily exceed the UTF8 byte cap.
                if type(value) is not str or len(value) > _MAX_STRING_UTF8_BYTES:
                    raise _Invalid()
                material += _utf8_byte_length(value)
                if material > _MAX_MATERIAL_BYTES:
                    raise _Invalid()
                # Order comparison only after this value's bytes are charged
                # to M: values after an aggregate refusal are never counted
                # or compared.
                if previous is not None and previous >= value:
                    raise _Invalid()
                previous = value
        admitted.append((principal_id, verifier, operations, grants))

    documents_admitted = []
    total_pairs = 0
    previous_id = None
    for item in documents:
        if type(item) is not DocumentRule:
            raise _Invalid()
        document_id = item.document_id
        if type(document_id) is not str or not 1 <= len(document_id) <= 256:
            raise _Invalid()
        if previous_id is not None and previous_id >= document_id:
            raise _Invalid()
        previous_id = document_id
        pairs = item.admitted
        if type(pairs) is not tuple or len(pairs) > _MAX_ADMITTED_PER_DOCUMENT:
            raise _Invalid()
        total_pairs += len(pairs)
        if total_pairs > _MAX_ADMITTED_TOTAL:
            raise _Invalid()
        material += _utf8_byte_length(document_id)
        if material > _MAX_MATERIAL_BYTES:
            raise _Invalid()
        previous_pair = None
        for pair in pairs:
            if type(pair) is not tuple or len(pair) != 2:
                raise _Invalid()
            revision_id, scope_digest = pair
            if (
                type(revision_id) is not str
                or type(scope_digest) is not str
                or _REVISION_ID_RE.fullmatch(revision_id) is None
                or _SCOPE_DIGEST_RE.fullmatch(scope_digest) is None
            ):
                raise _Invalid()
            pair_value = (revision_id, scope_digest)
            if previous_pair is not None and previous_pair >= pair_value:
                raise _Invalid()
            previous_pair = pair_value
            material += len(revision_id) + len(scope_digest)
            if material > _MAX_MATERIAL_BYTES:
                raise _Invalid()
        documents_admitted.append((document_id, tuple(pairs)))

    string_frames = (
        principal_count + operation_frames + grants_string_frames + document_count + 2 * total_pairs
    )
    framing = 42 + 4 * string_frames + 24 * principal_count + 4 * document_count
    canonical = material + framing
    if material > _MAX_MATERIAL_BYTES or canonical > _MAX_MATERIAL_BYTES:
        raise _Invalid()

    final_principals = [
        (principal_id, verifier, operations, _snapshot_grants(grants))
        for principal_id, verifier, operations, grants in admitted
    ]

    digest = hashlib.sha256()
    streamed = 0

    def update(payload: bytes) -> None:
        nonlocal streamed
        streamed += len(payload)
        if streamed > _MAX_MATERIAL_BYTES:
            raise _Invalid()
        digest.update(payload)

    for payload in _framed_payload(final_principals, documents_admitted):
        update(payload)

    policy = object.__new__(SuppliedPolicy)
    object.__setattr__(
        policy, "principals", tuple(_AdmittedPrincipal(*fields) for fields in final_principals)
    )
    object.__setattr__(
        policy,
        "documents",
        tuple(_AdmittedDocument(document_id, pairs) for document_id, pairs in documents_admitted),
    )
    object.__setattr__(policy, "policy_id", "sha256:" + digest.hexdigest())
    object.__setattr__(policy, "_admitted", _ADMITTED_MARKER)
    return policy


def admit_policy(principals, documents) -> SuppliedPolicy:
    """Closed admission of a supplied policy view (contract v1 sections 2-3)."""
    error = None
    try:
        result = _admit_policy_inner(principals, documents)
    except _Invalid:
        error = PolicyError(_POLICY_ERROR_MESSAGE)
    except Exception:
        error = PolicyError(_POLICY_ERROR_MESSAGE)
    # Raised after the handlers, so the frame holds no active exception and
    # the public error carries neither __cause__ nor __context__ from the
    # caught payload. Not a zeroization or traceback-locals claim.
    if error is not None:
        raise error
    return result


def _match_inner(policy, credential, required_operations) -> SuppliedMatch:
    if (
        type(policy) is not SuppliedPolicy
        or getattr(policy, "_admitted", None) is not _ADMITTED_MARKER
    ):
        raise _Invalid()
    if (
        type(credential) is not bytes
        or not _CREDENTIAL_MIN_BYTES <= len(credential) <= _CREDENTIAL_MAX_BYTES
    ):
        raise _Invalid()
    if any(byte not in _CREDENTIAL_ALPHABET for byte in credential):
        raise _Invalid()
    if (
        type(required_operations) is not tuple
        or not 1 <= len(required_operations) <= _MAX_OPERATIONS
    ):
        raise _Invalid()
    for index, operation in enumerate(required_operations):
        if type(operation) is not str or operation not in _OPERATION_VOCABULARY:
            raise _Invalid()
        if index and required_operations[index - 1] >= operation:
            raise _Invalid()

    digest = hashlib.sha256(credential).digest()
    match_count = 0
    matched_index = -1
    for index, admitted in enumerate(policy.principals):
        if hmac.compare_digest(digest, admitted.verifier):
            match_count += 1
            matched_index = index
    if match_count != 1:
        raise _Invalid()
    admitted = policy.principals[matched_index]
    if not set(required_operations) <= set(admitted.operations):
        raise _Invalid()

    match = object.__new__(SuppliedMatch)
    object.__setattr__(match, "principal_id", admitted.principal_id)
    object.__setattr__(match, "grants", _snapshot_grants(admitted.grants))
    object.__setattr__(match, "operations", admitted.operations)
    object.__setattr__(match, "policy_id", policy.policy_id)
    object.__setattr__(match, "authorization_status", _SUPPLIED_POLICY_MATCH_ONLY)
    object.__setattr__(match, "_admitted", _ADMITTED_MARKER)
    return match


def match_supplied(policy, credential, required_operations) -> SuppliedMatch:
    """Fullscan matching of an exact supplied credential (contract v1 4)."""
    error = None
    try:
        result = _match_inner(policy, credential, required_operations)
    except _Invalid:
        error = PolicyError(_POLICY_ERROR_MESSAGE)
    except Exception:
        error = PolicyError(_POLICY_ERROR_MESSAGE)
    if error is not None:
        raise error
    return result
