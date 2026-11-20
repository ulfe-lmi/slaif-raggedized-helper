"""Pure unit tests for supplied_policy (PAR-009-SUPPLIED-POLICY-A).

Synthetic fixed fixtures only: no network, credentials, models, GPU or source
runtime. The 20000-declaration and material/canonical cap witnesses are finite
pure-unit evidence, never source/snapshot capacity evidence. Identity oracles
are independent test-side framings of the contract grammar, never
implementation counters.
"""

from __future__ import annotations

import hashlib
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from slaif_raggedized_helper import provenance_records as pr
from slaif_raggedized_helper import supplied_policy as sp
from slaif_raggedized_helper.provenance_records import (
    Grants,
    Restrictions,
    Scope,
    reader_allows,
)

SYNTHETIC_CREDENTIAL_43 = b"synthetic-credential-" + b"a" * 22  # exactly 43
SYNTHETIC_CREDENTIAL_256 = b"synthetic-credential-" + b"b" * 235  # exactly 256
CREDS = [b"synthetic-credential-" + bytes([0x61 + i]) * 22 for i in range(3)]
EMPTY_CRED = b"e" * 43

MAX_MATERIAL = 67_108_864
SUFFICIENT_MATERIAL = 66_021_078
CHUNK_CODEPOINTS = 1024
CHUNK_BYTES = 4096


def _assert_module_origins() -> None:
    # Derived from this test file's resolved physical location
    # (tests/unit/test_supplied_policy.py -> worktree root / src), so a
    # canonical transfer or CI keeps the same fail-closed origin check.
    src = Path(__file__).resolve().parents[2] / "src"
    for module in (sp, pr):
        path = Path(module.__file__).resolve()
        assert path.is_relative_to(src), "module origin outside assigned worktree"


_assert_module_origins()


# ---------------------------------------------------------------- fixtures


def verifier_for(credential: bytes) -> bytes:
    return hashlib.sha256(credential).digest()


def credential_for(index: int) -> bytes:
    # 66 distinct valid 43-byte synthetic credentials from the public
    # alphabet: two rotating letters repeated 11 times.
    return (
        b"synthetic-credential-"
        + (chr(ord("a") + index // 26) + chr(ord("a") + index % 26)).encode() * 11
    )


def grants_of(corpora=(), versions=(), labels=()):
    return Grants(
        schema_version=1,
        corpora=corpora,
        versions=versions,
        labels=labels,
    )


def spec(
    principal_id="p-1",
    credential=SYNTHETIC_CREDENTIAL_43,
    operations=("search",),
    corpora=(),
    versions=(),
    labels=(),
    verifier=None,
    grants=None,
):
    return sp.PrincipalSpec(
        principal_id,
        verifier if verifier is not None else verifier_for(credential),
        operations,
        grants if grants is not None else grants_of(corpora, versions, labels),
    )


def rule(document_id, pairs=()):
    return sp.DocumentRule(document_id, pairs)


def pair(index):
    return ("sha256:" + format(index, "064x"), format(index + 10**12, "064x"))


def admit(principals=(), documents=()):
    return sp.admit_policy(tuple(principals), tuple(documents))


def _u32(value):
    return value.to_bytes(4, "big")


def golden_policy_id(principals, documents):
    """Independent test-side framing per contract v1 section 3."""
    parts = [b"slaif-supplied-policy-view-v1\n", _u32(1), _u32(len(principals))]
    for principal_id, verifier, operations, corpora, versions, labels in principals:
        encoded_id = principal_id.encode("utf-8")
        parts.append(_u32(len(encoded_id)) + encoded_id)
        parts.append(_u32(32) + verifier)
        parts.append(_u32(len(operations)))
        for operation in operations:
            parts.append(_u32(len(operation)) + operation.encode("ascii"))
        parts.append(_u32(1))
        for values in (corpora, versions, labels):
            parts.append(_u32(len(values)))
            for value in values:
                encoded = value.encode("utf-8")
                parts.append(_u32(len(encoded)) + encoded)
    parts.append(_u32(len(documents)))
    for document_id, pairs in documents:
        encoded_id = document_id.encode("utf-8")
        parts.append(_u32(len(encoded_id)) + encoded_id)
        parts.append(_u32(len(pairs)))
        for revision_id, scope_digest in pairs:
            parts.append(_u32(len(revision_id)) + revision_id.encode("ascii"))
            parts.append(_u32(len(scope_digest)) + scope_digest.encode("ascii"))
    return "sha256:" + hashlib.sha256(b"".join(parts)).hexdigest()


def material_canonical(principals, documents):
    """Independent test-side (M, H, C) per contract v1; no implementation state."""
    material = 0
    operation_frames = 0
    grants_frames = 0
    pair_count = 0
    for principal_id, verifier, operations, corpora, versions, labels in principals:
        material += len(principal_id.encode("utf-8")) + len(verifier)
        operation_frames += len(operations)
        material += sum(len(op.encode("utf-8")) for op in operations)
        grants_frames += len(corpora) + len(versions) + len(labels)
        material += sum(len(v.encode("utf-8")) for v in (*corpora, *versions, *labels))
    for document_id, pairs in documents:
        material += len(document_id.encode("utf-8"))
        pair_count += len(pairs)
        material += sum(len(rev) + len(dig) for rev, dig in pairs)
    string_frames = (
        len(principals) + operation_frames + grants_frames + len(documents) + 2 * pair_count
    )
    framing = 42 + 4 * string_frames + 24 * len(principals) + 4 * len(documents)
    return material, framing, material + framing


def golden_views(policy):
    golden_principals = [
        (
            p.principal_id,
            p.verifier,
            p.operations,
            p.grants.corpora,
            p.grants.versions,
            p.grants.labels,
        )
        for p in policy.principals
    ]
    golden_documents = [(d.document_id, d.admitted) for d in policy.documents]
    return golden_principals, golden_documents


def _scope(corpus="corpus-a", version="v1", labels=(), document_id="doc-1"):
    return Scope(
        schema_version=1,
        document_id=document_id,
        revision_id="sha256:" + "ab" * 32,
        corpus=corpus,
        version=version,
        labels=tuple(labels),
        processing_approved=True,
        redistribution_rights="allowed",
    )


def _wide_grants_specs(per_string):
    """256 principals, 113 fixed-length strictly increasing corpora strings."""
    tail_len = 6
    head = "0" * (per_string - tail_len)
    strings = []
    for i in range(113):
        tail = ""
        n = i
        for _ in range(tail_len):
            tail = "abcdefghijklmnopqrstuvwxyz"[n % 26] + tail
            n //= 26
        strings.append(head + tail)
    specs = []
    for principal_index in range(256):
        verifier = bytes([principal_index] * 32)
        specs.append(
            sp.PrincipalSpec(
                "p%03d" % principal_index,
                verifier,
                ("search",),
                grants_of(corpora=tuple(strings)),
            )
        )
    return specs


def _documents_20000():
    return [rule("d%06d" % i, (pair(i),)) for i in range(20000)]


class _Sentinel(BaseException):
    pass


class _TupleSubclass(tuple):
    pass


# ------------------------------------------------------------------ origins


def test_module_origins_inside_assigned_worktree():
    _assert_module_origins()


# ------------------------------------------------------------ public surface


def test_public_api_surface():
    for name in (
        "PrincipalSpec",
        "DocumentRule",
        "SuppliedPolicy",
        "SuppliedMatch",
        "PolicyError",
        "admit_policy",
        "match_supplied",
    ):
        assert hasattr(sp, name), name
    assert issubclass(sp.PolicyError, ValueError)


def test_public_construction_refused():
    with pytest.raises(sp.PolicyError):
        sp.SuppliedPolicy()
    with pytest.raises(sp.PolicyError):
        sp.SuppliedPolicy(object(), object(), object())
    with pytest.raises(sp.PolicyError):
        sp.SuppliedMatch()
    with pytest.raises(sp.PolicyError):
        sp.SuppliedMatch(*[object()] * 5)


def test_policy_and_match_records_frozen():
    policy = admit([spec()], [rule("doc-a")])
    for name in ("principals", "documents", "policy_id", "_admitted"):
        with pytest.raises(FrozenInstanceError):
            setattr(policy, name, object())
        with pytest.raises(FrozenInstanceError):
            delattr(policy, name)
    match = sp.match_supplied(policy, SYNTHETIC_CREDENTIAL_43, ("search",))
    for name in (
        "principal_id",
        "grants",
        "operations",
        "policy_id",
        "authorization_status",
        "_admitted",
    ):
        with pytest.raises(FrozenInstanceError):
            setattr(match, name, object())
        with pytest.raises(FrozenInstanceError):
            delattr(match, name)
    # Real behavior is preserved on the frozen records.
    assert match.policy_id == policy.policy_id
    assert match.operations == ("search",)


def test_uninitialized_objects_refused_by_match():
    uninitialized = object.__new__(sp.SuppliedPolicy)
    with pytest.raises(sp.PolicyError):
        sp.match_supplied(uninitialized, SYNTHETIC_CREDENTIAL_43, ("search",))


def test_declaration_dto_frozen_slots():
    spec_obj = spec()
    rule_obj = rule("doc-a", (pair(1),))
    with pytest.raises(FrozenInstanceError):
        spec_obj.principal_id = "x"
    with pytest.raises(FrozenInstanceError):
        rule_obj.document_id = "y"
    with pytest.raises(AttributeError):
        object.__setattr__(spec_obj, "extra", 1)


def test_no_subclass_admission():
    class SubSpec(sp.PrincipalSpec):
        pass

    class SubRule(sp.DocumentRule):
        pass

    sub = SubSpec("a", b"\x01" * 32, ("search",), grants_of())
    with pytest.raises(sp.PolicyError):
        sp.admit_policy((sub,), ())
    with pytest.raises(sp.PolicyError):
        sp.admit_policy((), (SubRule("doc-a", ()),))


def test_exact_outer_and_container_types():
    with pytest.raises(sp.PolicyError):
        sp.admit_policy([spec()], [])
    with pytest.raises(sp.PolicyError):
        sp.admit_policy((spec(),), [rule("doc-a")])
    with pytest.raises(sp.PolicyError):
        sp.admit_policy(_TupleSubclass([spec()]), ())
    with pytest.raises(sp.PolicyError):
        sp.admit_policy((), _TupleSubclass([rule("doc-a")]))


def test_reprs_do_not_reveal_payload():
    marker_id = "repr-marker-id"
    marker_grant = "repr-marker-grant"
    marker_doc = "repr-marker-doc"
    policy = admit([spec(principal_id=marker_id, corpora=(marker_grant,))], [rule(marker_doc)])
    match = sp.match_supplied(policy, SYNTHETIC_CREDENTIAL_43, ("search",))
    objects = (
        policy.principals[0],
        policy.documents[0],
        policy,
        match,
        spec(principal_id=marker_id),
        rule(marker_doc),
    )
    for obj in objects:
        text = repr(obj)
        assert marker_id not in text
        assert marker_grant not in text
        assert marker_doc not in text
    for text in (repr(policy), repr(match)):
        encoded = text.encode("ascii")
        assert SYNTHETIC_CREDENTIAL_43 not in encoded
        assert policy.principals[0].verifier not in encoded


# --------------------------------------------------------------- principal id


@pytest.mark.parametrize(
    "principal_id",
    ["a", "A", "9", "a.b_c-d:e", "a" * 128],
    ids=["single-lower", "single-upper", "digit-lead", "allowed-punct", "len-128"],
)
def test_principal_id_valid(principal_id):
    assert admit([spec(principal_id=principal_id)]).principals


@pytest.mark.parametrize(
    "principal_id",
    ["", "-", "a" * 129, "a b", "a/b", "a\nb", "\u00e9", "1a b"],
    ids=[
        "empty",
        "leading-punct",
        "len-129",
        "space",
        "slash",
        "newline",
        "non-ascii",
        "mixed-invalid",
    ],
)
def test_principal_id_refused(principal_id):
    with pytest.raises(sp.PolicyError):
        admit([spec(principal_id=principal_id)])


# ------------------------------------------------------------------- verifier


@pytest.mark.parametrize(
    "verifier",
    [b"x" * 31, b"x" * 33, "x" * 32, bytearray(b"x" * 32), memoryview(b"x" * 32), b""],
    ids=["len-31", "len-33", "str", "bytearray", "memoryview", "empty"],
)
def test_verifier_refused(verifier):
    with pytest.raises(sp.PolicyError):
        admit([spec(verifier=verifier)])


# ----------------------------------------------------------------- operations


@pytest.mark.parametrize(
    "operations",
    [
        ("search",),
        ("sources:read",),
        ("answer", "sources:read"),
        ("search", "sources:read"),
        ("answer", "search", "sources:read"),
    ],
    ids=["search", "sources-read", "answer-closure", "search-sources", "full"],
)
def test_operations_valid(operations):
    policy = admit([spec(operations=operations)])
    assert policy.principals[0].operations == tuple(operations)


@pytest.mark.parametrize(
    "operations",
    [
        (),
        ("answer",),
        ("answer", "search"),
        ("search2",),
        ("ANSWER",),
        ("answer:read",),
        ("search", "search"),
        ("sources:read", "search"),
        ("search", "search", "search", "search"),
        ["search"],
        "search",
    ],
    ids=[
        "empty",
        "answer-missing-closure",
        "answer-search-missing-closure",
        "unknown-op",
        "wrong-case",
        "unknown-op-2",
        "duplicate",
        "unsorted",
        "four-ops",
        "list",
        "str",
    ],
)
def test_operations_refused(operations):
    with pytest.raises(sp.PolicyError):
        admit([spec(operations=operations)])


# -------------------------------------------------------------------- grants


@pytest.mark.parametrize(
    "field,values",
    [
        ("corpora", ("", "a")),
        ("versions", ("v1",)),
        ("labels", ("l1", "l2")),
        ("corpora", tuple("c%03d" % i for i in range(128))),
        ("labels", ("\u00e9", "\u00f1")),
    ],
    ids=["empty-string-allowed", "version", "labels", "len-128", "unicode-values"],
)
def test_grants_values_valid(field, values):
    policy = admit([spec(**{field: tuple(values)})])
    assert getattr(policy.principals[0].grants, field) == tuple(values)


@pytest.mark.parametrize(
    "field,values",
    [
        ("corpora", ("b", "a")),
        ("versions", ("v1", "v1")),
        ("labels", ("l1", "l2", "l1")),
    ],
    ids=["unsorted", "duplicate", "not-increasing"],
)
def test_grants_values_refused(field, values):
    with pytest.raises(sp.PolicyError):
        admit([spec(**{field: tuple(values)})])


def test_grants_tuple_over_128_refused():
    # 129 values cannot be held by a public Grants (its own bound is 128),
    # so a bypassed record exercises the admission bound directly.
    values = tuple("v%04d" % i for i in range(129))
    with pytest.raises(sp.PolicyError):
        admit([_bypassed_spec(_bypassed_grants(corpora=values))])


def _bypassed_grants(**overrides):
    base = {"schema_version": 1, "corpora": ("a",), "versions": (), "labels": ()}
    base.update(overrides)
    return Grants.model_construct(**base)


def _bypassed_spec(grants):
    return sp.PrincipalSpec("p-1", b"\x01" * 32, ("search",), grants)


@pytest.mark.parametrize(
    "overrides",
    [
        {"schema_version": 2},
        {"schema_version": True},
        {"schema_version": "1"},
        {"corpora": ["a"]},
        {"corpora": ("a", 1)},
        {"corpora": ("b", "a")},
        {"corpora": None},
        {"corpora": "a"},
    ],
    ids=["schema-2", "schema-bool", "schema-str", "list", "int-member", "unsorted", "none", "str"],
)
def test_grants_bypassed_malformed_refused(overrides):
    with pytest.raises(sp.PolicyError):
        admit([_bypassed_spec(_bypassed_grants(**overrides))])


def test_grants_uninitialized_refused():
    with pytest.raises(sp.PolicyError):
        admit([_bypassed_spec(object.__new__(Grants))])


def test_grants_wrong_type_refused():
    for grants in ({}, (), None, "Grants", 1):
        with pytest.raises(sp.PolicyError):
            admit([_bypassed_spec(grants)])


def test_grants_subclass_refused():
    class SubGrants(Grants):
        pass

    sub = SubGrants(schema_version=1, corpora=("a",), versions=(), labels=())
    with pytest.raises(sp.PolicyError):
        admit([_bypassed_spec(sub)])


def test_grants_existing_serialization_limit_still_applies():
    # 300000 ASCII control characters fit the local material/canonical
    # accounting, but the public controlled-mapping JSON admission escapes
    # each control as \uXXXX and refuses the >1MiB serialized record.
    with pytest.raises(sp.PolicyError):
        admit([spec(corpora=("\x01" * 300000,))])


# --------------------------------------------------- ordering and duplicates


def test_principal_order_and_duplicates():
    with pytest.raises(sp.PolicyError):
        admit(
            [
                spec(principal_id="b", verifier=b"\x01" * 32),
                spec(principal_id="a", verifier=b"\x02" * 32),
            ]
        )
    with pytest.raises(sp.PolicyError):
        admit(
            [
                spec(principal_id="a", verifier=b"\x01" * 32),
                spec(principal_id="a", verifier=b"\x02" * 32),
            ]
        )
    with pytest.raises(sp.PolicyError):
        admit(
            [
                spec(principal_id="a", verifier=b"\x01" * 32),
                spec(principal_id="b", verifier=b"\x01" * 32),
            ]
        )


def test_document_order_and_duplicates():
    with pytest.raises(sp.PolicyError):
        admit([], [rule("b"), rule("a")])
    with pytest.raises(sp.PolicyError):
        admit([], [rule("a"), rule("a")])


def test_pair_order_and_duplicates():
    with pytest.raises(sp.PolicyError):
        admit([], [rule("doc-a", (pair(2), pair(1)))])
    with pytest.raises(sp.PolicyError):
        admit([], [rule("doc-a", (pair(1), pair(1)))])


def test_grants_order_and_duplicates():
    with pytest.raises(sp.PolicyError):
        admit([spec(corpora=("b", "a"))])
    with pytest.raises(sp.PolicyError):
        admit([spec(corpora=("a", "a"))])
    with pytest.raises(sp.PolicyError):
        admit([spec(versions=("b", "a"))])
    with pytest.raises(sp.PolicyError):
        admit([spec(labels=("b", "a"))])


# ----------------------------------------------------------------- cardinal


def test_principal_cardinality_boundary():
    specs = [spec(principal_id="p%03d" % i, verifier=bytes([i] * 32)) for i in range(256)]
    assert len(admit(specs).principals) == 256
    specs.append(spec(principal_id="p256", verifier=b"\xff" * 32))
    with pytest.raises(sp.PolicyError):
        admit(specs)


def test_document_cardinality_boundary():
    documents = [rule("d%05d" % i) for i in range(20001)]
    with pytest.raises(sp.PolicyError):
        admit([], documents)


def test_admitted_pair_cardinality():
    assert (
        len(admit([], [rule("doc-a", tuple(pair(i) for i in range(64)))]).documents[0].admitted)
        == 64
    )
    with pytest.raises(sp.PolicyError):
        admit([], [rule("doc-a", tuple(pair(i) for i in range(65)))])


def test_total_pair_cardinality():
    base = [rule("d%04d" % i, tuple(pair(i * 64 + j) for j in range(64))) for i in range(1024)]
    assert sum(len(r.admitted) for r in base) == 65536
    admit([], base)
    overflow = base + [rule("d%04d" % 1024, (pair(65536),))]
    with pytest.raises(sp.PolicyError):
        admit([], overflow)


def test_grants_tuple_cardinality():
    values = tuple("v%03d" % i for i in range(128))
    assert len(admit([spec(versions=values)]).principals[0].grants.versions) == 128
    over = tuple("v%04d" % i for i in range(129))
    with pytest.raises(sp.PolicyError):
        admit([_bypassed_spec(_bypassed_grants(versions=over))])


# ----------------------------------------------------------- utf8 semantics


def test_document_id_surrogates_refused():
    with pytest.raises(sp.PolicyError):
        admit([], [rule("a\ud800b")])


def test_document_id_codepoint_bounds():
    admit([], [rule("\U00010000" * 256)])
    with pytest.raises(sp.PolicyError):
        admit([], [rule("\U00010000" * 257)])


def test_document_id_no_normalization():
    policy_nfd = admit([], [rule("e\u0301")])
    policy_nfc = admit([], [rule("\u00e9")])
    assert policy_nfd.policy_id != policy_nfc.policy_id
    assert policy_nfd.documents[0].document_id == "e\u0301"


def test_utf8_chunk_boundaries_admitted():
    one_chunk = "\U00010000" * 1024  # exactly one 1024-codepoint chunk
    two_chunks = "\U00010000" * 2048  # two full chunks
    odd = "x" * 1025  # 1024 + 1 codepoints
    corpora = (odd, one_chunk, two_chunks)
    policy = admit([spec(corpora=corpora)])
    assert policy.principals[0].grants.corpora == corpora


def test_grants_values_not_ascii_restricted():
    values = ("corpus-\u00e9-\u00f1", "corpus-\u00f1")
    assert admit([spec(corpora=values)]).principals[0].grants.corpora == values


# ------------------------------------------------- history withdrawn absent


def test_multiple_history_pairs_admitted():
    pairs = (pair(1), pair(2), pair(3))
    policy = admit([], [rule("doc-a", pairs)])
    assert policy.documents[0].admitted == pairs


def test_withdrawn_document_empty_admitted():
    policy = admit([], [rule("doc-a"), rule("doc-b", (pair(1),))])
    assert policy.documents[0].admitted == ()
    assert len(policy.documents) == 2


def test_absent_document_stays_absent():
    policy = admit([], [rule("doc-a")])
    assert [d.document_id for d in policy.documents] == ["doc-a"]


# -------------------------------------------------------------- identity


def test_identity_matches_independent_golden():
    documents = [
        rule("doc-1", (pair(1), pair(2))),
        rule("doc-2"),
        rule("doc-3", (pair(9),)),
    ]
    policy = admit(
        [
            spec(
                principal_id="alpha",
                operations=("search", "sources:read"),
                corpora=("c1",),
                versions=("v1",),
                labels=("l1",),
            )
        ],
        documents,
    )
    golden_principals, golden_documents = golden_views(policy)
    assert policy.policy_id == golden_policy_id(golden_principals, golden_documents)
    assert policy.policy_id.startswith("sha256:")
    assert len(policy.policy_id) == 7 + 64


def test_identity_changes_on_value_change():
    base = admit([spec(corpora=("base-value",))], [rule("doc-1", (pair(1),))])
    assert base.policy_id == golden_policy_id(*golden_views(base))
    changed = admit([spec(corpora=("base-valxe",))], [rule("doc-1", (pair(1),))])
    assert changed.policy_id != base.policy_id
    assert changed.policy_id == golden_policy_id(*golden_views(changed))


def test_identity_distinguishes_framing_layout():
    one = admit(
        [
            spec(principal_id="a", verifier=b"\x01" * 32, corpora=("x", "y")),
            spec(principal_id="b", verifier=b"\x02" * 32),
        ]
    )
    two = admit(
        [
            spec(principal_id="a", verifier=b"\x01" * 32, corpora=("x",)),
            spec(principal_id="b", verifier=b"\x02" * 32, corpora=("y",)),
        ]
    )
    assert one.policy_id != two.policy_id


# ------------------------------------------------------------------ match


def _three_principal_policy():
    return admit(
        [
            spec(principal_id="p0", credential=CREDS[0]),
            spec(principal_id="p1", credential=CREDS[1]),
            spec(principal_id="p2", credential=CREDS[2]),
        ]
    )


def test_match_fullscan_first_middle_last_unknown(monkeypatch):
    calls = []
    real = sp.hmac.compare_digest

    def recorder(left, right):
        calls.append((left, right))
        return real(left, right)

    monkeypatch.setattr(sp.hmac, "compare_digest", recorder)
    policy = _three_principal_policy()
    assert sp.match_supplied(policy, CREDS[0], ("search",)).principal_id == "p0"
    assert len(calls) == 3
    calls.clear()
    assert sp.match_supplied(policy, CREDS[1], ("search",)).principal_id == "p1"
    assert len(calls) == 3
    calls.clear()
    assert sp.match_supplied(policy, CREDS[2], ("search",)).principal_id == "p2"
    assert len(calls) == 3
    calls.clear()
    with pytest.raises(sp.PolicyError):
        sp.match_supplied(policy, b"z" * 43, ("search",))
    assert len(calls) == 3


def test_match_result_exposes_exactly_contract_fields():
    policy = admit(
        [
            spec(
                principal_id="match-principal",
                operations=("answer", "search", "sources:read"),
                corpora=("corpus-a",),
                versions=("v1",),
                labels=("l1", "l2"),
            )
        ]
    )
    match = sp.match_supplied(policy, SYNTHETIC_CREDENTIAL_43, ("search",))
    assert set(type(match).__slots__) == {
        "principal_id",
        "grants",
        "operations",
        "policy_id",
        "authorization_status",
        "_admitted",
    }
    assert match.principal_id == "match-principal"
    assert match.operations == ("answer", "search", "sources:read")
    assert match.authorization_status == "SUPPLIED_POLICY_MATCH_ONLY"
    assert match.policy_id == policy.policy_id
    assert type(match.grants) is Grants
    assert match.grants.corpora == ("corpus-a",)
    assert match.grants.versions == ("v1",)
    assert match.grants.labels == ("l1", "l2")
    assert match.grants is not policy.principals[0].grants


def test_match_required_operation_subsets_allowed():
    policy = admit([spec(operations=("answer", "search", "sources:read"))])
    for required in (
        ("search",),
        ("sources:read",),
        ("answer", "search"),
        ("answer", "sources:read"),
        ("search", "sources:read"),
        ("answer", "search", "sources:read"),
    ):
        match = sp.match_supplied(policy, SYNTHETIC_CREDENTIAL_43, required)
        assert match.operations == ("answer", "search", "sources:read")


def test_match_answer_closure_enforced_on_declaration():
    closed = admit([spec(operations=("answer", "sources:read"))])
    assert sp.match_supplied(closed, SYNTHETIC_CREDENTIAL_43, ("answer",)).principal_id == "p-1"
    search_only = admit([spec(operations=("search",))])
    with pytest.raises(sp.PolicyError):
        sp.match_supplied(search_only, SYNTHETIC_CREDENTIAL_43, ("answer",))


@pytest.mark.parametrize(
    "required",
    [
        (),
        ("search", "search"),
        ("search", "answer"),
        ("answer", "search", "sources:read", "search"),
        ["search"],
        ("SEARCH",),
        ("bogus",),
        ("search", 1),
    ],
    ids=["empty", "duplicate", "unsorted", "four", "list", "wrong-case", "unknown", "non-str"],
)
def test_match_required_operations_malformed_refused(required):
    policy = admit([spec()])
    with pytest.raises(sp.PolicyError):
        sp.match_supplied(policy, SYNTHETIC_CREDENTIAL_43, required)


@pytest.mark.parametrize(
    "credential",
    [
        b"a" * 42,
        b"a" * 257,
        b"a" * 42 + b"/",
        b"a" * 42 + b"+",
        b"a" * 42 + b"*",
        b"a" * 42 + b"\x7f",
        b"a" * 42 + b"\x80",
        "a" * 43,
    ],
    ids=["len-42", "len-257", "slash", "plus", "star", "del", "non-ascii", "str"],
)
def test_match_credential_malformed_refused(credential):
    policy = admit([spec()])
    with pytest.raises(sp.PolicyError):
        sp.match_supplied(policy, credential, ("search",))


def test_match_credential_boundary_lengths_allowed():
    long_credential = b"m" * 235 + b"synthetic-credential-"
    policy = admit([spec(credential=long_credential)])
    assert sp.match_supplied(policy, long_credential, ("search",)).principal_id == "p-1"
    assert len(long_credential) == 256


def test_match_refuses_non_policy():
    for policy in (None, object(), {}, {"principals": ()}, sp.SuppliedPolicy, 42):
        with pytest.raises(sp.PolicyError):
            sp.match_supplied(policy, SYNTHETIC_CREDENTIAL_43, ("search",))


def test_empty_policy_refuses_matching():
    policy = admit((), ())
    assert policy.principals == ()
    with pytest.raises(sp.PolicyError):
        sp.match_supplied(policy, SYNTHETIC_CREDENTIAL_43, ("search",))


# ------------------------------------------------- sentinel and hygiene


@pytest.mark.parametrize(
    "boundary",
    ["digest", "comparison", "admission-match", "admission-policy"],
    ids=["digest", "comparison", "admission-match", "admission-policy"],
)
def test_base_exception_sentinel_identity(monkeypatch, boundary):
    policy = admit([spec()])  # built before any patching
    sentinel = _Sentinel()

    def raise_sentinel(*args, **kwargs):
        raise sentinel

    if boundary == "digest":
        monkeypatch.setattr(sp.hashlib, "sha256", raise_sentinel)
    elif boundary == "comparison":
        monkeypatch.setattr(sp.hmac, "compare_digest", raise_sentinel)
    else:
        monkeypatch.setattr(sp, "admit_record", raise_sentinel)
    if boundary == "admission-policy":
        with pytest.raises(_Sentinel) as excinfo:
            sp.admit_policy((spec(),), ())
    else:
        with pytest.raises(_Sentinel) as excinfo:
            sp.match_supplied(policy, SYNTHETIC_CREDENTIAL_43, ("search",))
    assert excinfo.value is sentinel


def test_error_message_and_context_hygiene():
    bad = sp.PrincipalSpec("p-1", b"short", ("search",), grants_of())
    with pytest.raises(sp.PolicyError) as excinfo:
        sp.admit_policy((bad,), ())
    error = excinfo.value
    assert str(error) == "invalid supplied policy"
    assert error.args == ("invalid supplied policy",)
    assert error.__cause__ is None
    assert error.__context__ is None
    assert "p-1" not in repr(error)

    # Real bad Unicode: a surrogate document id raises a genuine
    # UnicodeEncodeError inside the handler; the public error must not
    # retain it as cause or context.
    with pytest.raises(sp.PolicyError) as unicode_info:
        sp.admit_policy((), (sp.DocumentRule("a\ud800b", ()),))
    unicode_error = unicode_info.value
    assert unicode_error.__cause__ is None
    assert unicode_error.__context__ is None

    marker_policy = admit([spec(corpora=("SECRETGRANTMARKER",))])
    with pytest.raises(sp.PolicyError) as match_info:
        sp.match_supplied(marker_policy, b"q" * 43, ("search",))
    match_error = match_info.value
    assert str(match_error) == "invalid supplied policy"
    assert match_error.__cause__ is None
    assert match_error.__context__ is None
    assert "SECRETGRANTMARKER" not in str(match_error)
    assert "SECRETGRANTMARKER" not in repr(match_error)

    with pytest.raises(sp.PolicyError) as non_policy_info:
        sp.match_supplied(object(), SYNTHETIC_CREDENTIAL_43, ("search",))
    assert non_policy_info.value.__cause__ is None
    assert non_policy_info.value.__context__ is None

    with pytest.raises(sp.PolicyError):
        admit([spec(corpora=("\x01" * 300000,))])
    # A valid admission after failures proves no retained partial state.
    assert admit([spec()]).principals


def test_oversized_string_refused_before_later_work(monkeypatch):
    huge = "a" * 1_048_577  # one codepoint over the per-string byte cap
    specs = [
        spec(principal_id="a", verifier=b"\x01" * 32, corpora=("ok-value", huge)),
        spec(principal_id="b", verifier=b"\x02" * 32),
    ]
    later_work = []
    real_admit = sp.admit_record
    real_sha256 = sp.hashlib.sha256

    def guard_admit(*args, **kwargs):
        later_work.append("admit_record")
        return real_admit(*args, **kwargs)

    def guard_sha256(*args, **kwargs):
        later_work.append("sha256")
        return real_sha256(*args, **kwargs)

    monkeypatch.setattr(sp, "admit_record", guard_admit)
    monkeypatch.setattr(sp.hashlib, "sha256", guard_sha256)
    try:
        with pytest.raises(sp.PolicyError):
            sp.admit_policy(tuple(specs), ())
    finally:
        monkeypatch.undo()
    assert later_work == []


def test_multibyte_string_byte_cap_refused():
    # 900000 astral codepoints pass the O(1) codepoint pre-bound
    # (<= 1MiB codepoints) but encode to 3.6 MiB UTF8 bytes.
    with pytest.raises(sp.PolicyError):
        admit([spec(corpora=("\U00010000" * 900000,))])


def test_global_material_refused_during_accumulation():
    # 68 full-size grant strings: every per-string cap holds, but the
    # summed material exceeds 67108864 before the principal completes.
    head = "a" * (1_048_576 - 8)
    values = tuple(head + "%08d" % i for i in range(68))
    assert all(len(v) == 1_048_576 for v in values)
    assert all(values[i] < values[i + 1] for i in range(len(values) - 1))
    with pytest.raises(sp.PolicyError):
        admit([spec(corpora=values)])


def test_grants_values_after_refusal_not_counted(monkeypatch):
    # F4-followup witness: 65 earlier principals spend M so the 66th
    # principal's base lands exactly on the 67108864 cap; its first Grants
    # value (2000 bytes) overflows the remaining zero allowance. A test-
    # local recorder delegates to the real routine and filters its record
    # to the genuine test Grants strings by object identity, so it shows
    # exactly which values were ever counted: the 65 filler values and that
    # first value only. The 127 values after it are never encoded, counted
    # or order-compared. No production hook: the patch lives in this test.
    filler = tuple("f" * (1_032_401 + i) for i in range(64)) + ("f" * 1_030_412,)
    refuse_values = tuple("g" * (2000 + index) for index in range(128))
    principals = [
        spec(
            principal_id="p-%02d" % index,
            credential=credential_for(index),
            corpora=(filler[index],),
        )
        for index in range(65)
    ]
    principals.append(
        spec(
            principal_id="refu",
            credential=credential_for(65),
            corpora=refuse_values,
        )
    )
    genuine = {id(value) for value in filler} | {id(value) for value in refuse_values}
    record = []
    real_length = sp._utf8_byte_length

    def recording(value):
        length = real_length(value)
        if id(value) in genuine:
            record.append(length)
        return length

    monkeypatch.setattr(sp, "_utf8_byte_length", recording)
    with pytest.raises(sp.PolicyError):
        admit(principals)
    assert record == [1_032_401 + index for index in range(64)] + [1_030_412, 2000]


def test_streaming_chunks_bounded_and_genuine(monkeypatch):
    values = tuple(("\U00010000" * 3000 + "%04d" % i) for i in range(2))
    specs = [spec(corpora=values)]  # built before patching (real sha256)
    updates = []
    real_sha256 = sp.hashlib.sha256

    class _RecordingDigest:
        def __init__(self):
            self._digest = real_sha256()

        def update(self, data):
            updates.append(len(data))
            self._digest.update(data)

        def hexdigest(self):
            return self._digest.hexdigest()

    monkeypatch.setattr(sp.hashlib, "sha256", lambda *a, **k: _RecordingDigest())
    try:
        policy = admit(specs)
    finally:
        monkeypatch.undo()
    assert all(length <= CHUNK_BYTES for length in updates)
    assert CHUNK_BYTES in updates
    golden_principals, golden_documents = golden_views(policy)
    assert policy.policy_id == golden_policy_id(golden_principals, golden_documents)
    material, _framing, canonical = material_canonical(golden_principals, golden_documents)
    assert sum(updates) == canonical


# -------------------------------------------------------- real reader_allows


def test_reader_allows_real_semantics():
    grants = grants_of(corpora=("corpus-a",), versions=("v1",), labels=("l1", "l2"))
    empty = grants_of()
    assert reader_allows(_scope(), empty) is False
    assert reader_allows(_scope(), grants) is True
    assert reader_allows(_scope(labels=("l1",)), grants) is True
    assert reader_allows(_scope(labels=("l1", "l3")), grants) is False
    assert reader_allows(_scope(corpus="corpus-b"), grants) is False
    assert reader_allows(_scope(version="v2"), grants) is False
    assert reader_allows(_scope(version=None), grants) is False
    assert (
        reader_allows(
            _scope(),
            grants,
            Restrictions(schema_version=1, corpora=("corpus-a",), versions=("v1",)),
        )
        is True
    )
    assert (
        reader_allows(_scope(), grants, Restrictions(schema_version=1, corpora=("corpus-b",)))
        is False
    )
    assert (
        reader_allows(_scope(), grants, Restrictions(schema_version=1, versions=("v9",))) is False
    )
    assert reader_allows(_scope(), grants, Restrictions(schema_version=1, corpora=())) is False


def test_match_snapshot_grants_drive_real_reader_allows():
    policy = admit(
        [
            spec(
                principal_id="p-reader",
                corpora=("corpus-a",),
                versions=("v1",),
                labels=("l1", "l2"),
            )
        ]
    )
    match = sp.match_supplied(policy, SYNTHETIC_CREDENTIAL_43, ("search",))
    assert reader_allows(_scope(labels=("l1",)), match.grants) is True
    assert reader_allows(_scope(corpus="corpus-b"), match.grants) is False
    assert reader_allows(_scope(version=None), match.grants) is False
    empty_policy = admit([spec(principal_id="p-empty", verifier=verifier_for(EMPTY_CRED))])
    empty_match = sp.match_supplied(empty_policy, EMPTY_CRED, ("search",))
    assert reader_allows(_scope(), empty_match.grants) is False


# ---------------------------------------------------------------- witnesses


def test_witness_20000_declarations():
    documents = _documents_20000()
    assert len(documents) == 20000
    policy = admit([spec(principal_id="p")], documents)
    assert len(policy.documents) == 20000
    golden_principals, golden_documents = golden_views(policy)
    assert policy.policy_id == golden_policy_id(golden_principals, golden_documents)
    material, framing, canonical = material_canonical(golden_principals, golden_documents)
    assert (material, framing, canonical) == (2840039, 320074, 3160113)


def test_witness_20000_zero_principals():
    documents = _documents_20000()
    policy = admit([], documents)
    assert policy.principals == ()
    golden_principals, golden_documents = golden_views(policy)
    assert policy.policy_id == golden_policy_id(golden_principals, golden_documents)
    material, framing, canonical = material_canonical(golden_principals, golden_documents)
    assert (material, framing, canonical) == (2840000, 320042, 3160042)


def test_witness_fits_above_sufficient_threshold():
    policy = admit(_wide_grants_specs(2298))
    golden_principals, golden_documents = golden_views(policy)
    assert policy.policy_id == golden_policy_id(golden_principals, golden_documents)
    material, _framing, canonical = material_canonical(golden_principals, golden_documents)
    assert material > SUFFICIENT_MATERIAL
    assert canonical <= MAX_MATERIAL


def test_witness_canonical_cap_boundary():
    fit = admit(_wide_grants_specs(2315))
    golden_principals, golden_documents = golden_views(fit)
    material, _framing, canonical = material_canonical(golden_principals, golden_documents)
    assert canonical <= MAX_MATERIAL
    over_specs = _wide_grants_specs(2316)
    with pytest.raises(sp.PolicyError):
        admit(over_specs)
    over_views = [
        (
            s.principal_id,
            s.verifier,
            s.operations,
            s.grants.corpora,
            s.grants.versions,
            s.grants.labels,
        )
        for s in over_specs
    ]
    material, _framing, canonical = material_canonical(over_views, [])
    assert material <= MAX_MATERIAL
    assert canonical > MAX_MATERIAL
