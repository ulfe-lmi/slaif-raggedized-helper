"""Pure unit tests for supplied_policy_wire (PAR-009-SUPPLIED-POLICY-WIRE-A).

Synthetic fixed fixtures only: no network, credentials, models, GPU or
source runtime. The 20000-declaration and actual M/C cap witnesses are
finite pure-unit evidence, never source/snapshot capacity evidence.
Identity oracles are independent test-side framings of the contract
grammar, never implementation counters. Actual transport size (wire
bytes) is kept distinct from typed canonical semantics (M/H/C); no heap,
RSS or latency claim is made.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from slaif_raggedized_helper import provenance_records as pr
from slaif_raggedized_helper import supplied_policy as sp
from slaif_raggedized_helper import supplied_policy_wire as spw

MAGIC = b"slaif-supplied-policy-view-v1\n"
MAX_WIRE_BYTES = 67_108_864
SUFFICIENT_MATERIAL = 66_021_078

CREDENTIAL_43 = b"synthetic-credential-" + b"a" * 22  # exactly 43
CREDENTIAL_2 = b"synthetic-credential-" + b"b" * 22  # exactly 43
CREDENTIAL_3 = b"synthetic-credential-" + b"c" * 22  # exactly 43


def _assert_module_origins() -> None:
    # Derived from this test file's resolved physical location
    # (tests/unit/test_supplied_policy_wire.py -> worktree root / src), so a
    # canonical transfer or CI keeps the same fail-closed origin check.
    src = Path(__file__).resolve().parents[2] / "src"
    for module in (spw, sp, pr):
        path = Path(module.__file__).resolve()
        assert path.is_relative_to(src), "module origin outside assigned worktree"


_assert_module_origins()


# ------------------------------------------------------------ encoders/oracles


def _u32(value: int) -> bytes:
    return value.to_bytes(4, "big")


def _s(text: str) -> bytes:
    raw = text.encode("utf-8")
    return _u32(len(raw)) + raw


def _verifier(credential: bytes) -> bytes:
    return hashlib.sha256(credential).digest()


def encode_principal(principal_id, verifier, operations, corpora=(), versions=(), labels=()):
    parts = [_s(principal_id), _u32(32) + verifier, _u32(len(operations))]
    for operation in operations:
        parts.append(_s(operation))
    parts.append(_u32(1))
    for values in (corpora, versions, labels):
        parts.append(_u32(len(values)))
        for value in values:
            parts.append(_s(value))
    return b"".join(parts)


def encode_policy(principals, documents):
    """Independent test-side wire framing per the typed component grammar."""
    parts = [MAGIC, _u32(1), _u32(len(principals))]
    for principal in principals:
        parts.append(encode_principal(*principal))
    parts.append(_u32(len(documents)))
    for document_id, pairs in documents:
        parts.append(_s(document_id))
        parts.append(_u32(len(pairs)))
        for revision_id, scope_digest in pairs:
            parts.append(_s(revision_id))
            parts.append(_s(scope_digest))
    return b"".join(parts)


def golden_policy_id(principals, documents):
    """Independent test-side identity framing per contract v1 section 3."""
    parts = [MAGIC, _u32(1), _u32(len(principals))]
    for principal_id, verifier, operations, corpora, versions, labels in principals:
        raw_id = principal_id.encode("utf-8")
        parts.append(_u32(len(raw_id)) + raw_id)
        parts.append(_u32(32) + verifier)
        parts.append(_u32(len(operations)))
        for operation in operations:
            raw_op = operation.encode("utf-8")
            parts.append(_u32(len(raw_op)) + raw_op)
        parts.append(_u32(1))
        for values in (corpora, versions, labels):
            parts.append(_u32(len(values)))
            for value in values:
                raw_value = value.encode("utf-8")
                parts.append(_u32(len(raw_value)) + raw_value)
    parts.append(_u32(len(documents)))
    for document_id, pairs in documents:
        raw_doc = document_id.encode("utf-8")
        parts.append(_u32(len(raw_doc)) + raw_doc)
        parts.append(_u32(len(pairs)))
        for revision_id, scope_digest in pairs:
            raw_rev = revision_id.encode("utf-8")
            raw_digest = scope_digest.encode("utf-8")
            parts.append(_u32(len(raw_rev)) + raw_rev)
            parts.append(_u32(len(raw_digest)) + raw_digest)
    return "sha256:" + hashlib.sha256(b"".join(parts)).hexdigest()


def material_canonical(principals, documents):
    """Independent test-side (M, H, C) per the typed component contract v1."""
    material = 0
    operation_frames = 0
    grants_frames = 0
    pair_count = 0
    for principal_id, verifier, operations, corpora, versions, labels in principals:
        material += len(principal_id.encode("utf-8")) + len(verifier)
        operation_frames += len(operations)
        material += sum(len(operation.encode("utf-8")) for operation in operations)
        grants_frames += len(corpora) + len(versions) + len(labels)
        material += sum(len(value.encode("utf-8")) for value in (*corpora, *versions, *labels))
    for document_id, pairs in documents:
        material += len(document_id.encode("utf-8"))
        pair_count += len(pairs)
        material += sum(len(revision_id) + len(scope_digest) for revision_id, scope_digest in pairs)
    string_frames = (
        len(principals) + operation_frames + grants_frames + len(documents) + 2 * pair_count
    )
    framing = 42 + 4 * string_frames + 24 * len(principals) + 4 * len(documents)
    return material, framing, material + framing


def pair(index):
    return ("sha256:" + format(index, "064x"), format(index + 10**12, "064x"))


# ---------------------------------------------------------- raw wire builders


def raw_principal(
    id_bytes=b"p",
    verifier=b"\x01" * 32,
    ops=(b"search",),
    grants_schema=1,
    vectors=(),
):
    """Raw principal bytes with per-frame control (caps/schema witnesses)."""
    parts = [_u32(len(id_bytes)) + id_bytes, _u32(len(verifier)) + verifier]
    parts.append(_u32(len(ops)))
    for operation in ops:
        parts.append(_u32(len(operation)) + operation)
    parts.append(_u32(grants_schema))
    for values in vectors:
        parts.append(_u32(len(values)))
        for value in values:
            parts.append(_u32(len(value)) + value)
    for _ in range(3 - len(vectors)):
        parts.append(_u32(0))
    return b"".join(parts)


def raw_document(doc_id=b"doc", pair_count=0, pairs=()):
    parts = [_u32(len(doc_id)) + doc_id, _u32(pair_count)]
    for revision_id, scope_digest in pairs:
        parts.append(_u32(len(revision_id)) + revision_id)
        parts.append(_u32(len(scope_digest)) + scope_digest)
    return b"".join(parts)


def raw_wire(principals, documents=(), schema=1):
    parts = [MAGIC, _u32(schema), _u32(len(principals))]
    parts.extend(principals)
    parts.append(_u32(len(documents)))
    parts.extend(documents)
    return b"".join(parts)


def _medium_wire():
    principals = [
        (
            "alpha-1",
            _verifier(CREDENTIAL_43),
            ("answer", "search", "sources:read"),
            ("alpha",),
            ("v1",),
            ("l1",),
        ),
        ("beta-2", _verifier(CREDENTIAL_2), ("search",), (), (), ()),
    ]
    documents = [("doc-1", (pair(1), pair(2))), ("doc-2", (pair(3),))]
    return principals, documents, encode_policy(principals, documents)


def _principal_tail(id_bytes):
    return (
        _u32(32)
        + b"\x01" * 32
        + _u32(1)
        + _u32(6)
        + b"search"
        + _u32(1)
        + _u32(0)
        + _u32(0)
        + _u32(0)
        + _u32(0)
    )


def _one_principal_wire(id_bytes):
    return MAGIC + _u32(1) + _u32(1) + _u32(len(id_bytes)) + id_bytes + _principal_tail(id_bytes)


class _Sentinel(BaseException):
    pass


# ------------------------------------------------------------------ origins


def test_module_origins_inside_assigned_worktree():
    _assert_module_origins()


# ------------------------------------------------------------ public surface


def test_public_api_surface():
    assert hasattr(spw, "PolicyWireError")
    assert hasattr(spw, "admit_policy_bytes")
    assert issubclass(spw.PolicyWireError, ValueError)


def test_error_message_fixed_input_free():
    marker = "m!rker-xyz-987"
    wire = encode_policy([(marker, _verifier(CREDENTIAL_43), ("search",), (), (), ())], [])
    with pytest.raises(spw.PolicyWireError) as excinfo:
        spw.admit_policy_bytes(wire)
    error = excinfo.value
    assert str(error) == "invalid supplied policy wire"
    assert marker not in str(error)
    assert marker not in repr(error)
    assert all(marker not in str(argument) for argument in error.args)


HYGIENE_CASES = [
    ("structural-short", MAGIC + b"short"),
    ("structural-prefix", MAGIC[:-1] + b"X" + _u32(1) + _u32(0) + _u32(0)),
    ("utf8-caught", _one_principal_wire(b"\xff")),
    (
        "factory-caught",
        encode_policy([("p!1", _verifier(CREDENTIAL_43), ("search",), (), (), ())], []),
    ),
]


@pytest.mark.parametrize(
    ("case", "payload"), HYGIENE_CASES, ids=[case for case, _ in HYGIENE_CASES]
)
def test_error_hygiene_cause_context(case, payload):
    with pytest.raises(spw.PolicyWireError) as excinfo:
        spw.admit_policy_bytes(payload)
    error = excinfo.value
    assert type(error) is spw.PolicyWireError
    assert isinstance(error, ValueError)
    assert str(error) == "invalid supplied policy wire"
    assert error.__cause__ is None
    assert error.__context__ is None


# ------------------------------------------------------- byte-exact admission


def test_empty_policy_exact_bytes():
    exact = MAGIC + _u32(1) + _u32(0) + _u32(0)
    assert len(exact) == 42
    policy = spw.admit_policy_bytes(exact)
    assert policy.principals == ()
    assert policy.documents == ()
    assert policy.policy_id == "sha256:" + hashlib.sha256(exact).hexdigest()


def test_single_principal_direct_field_equality():
    principal_id = "alpha-1"
    verifier = _verifier(CREDENTIAL_43)
    operations = ("answer", "search", "sources:read")
    corpora, versions, labels = ("alpha", "beta"), ("v1",), ("l1", "l2")
    pairs = (pair(1), pair(2))
    principals = [(principal_id, verifier, operations, corpora, versions, labels)]
    documents = [("doc-1", pairs), ("doc-2", ())]
    policy = spw.admit_policy_bytes(encode_policy(principals, documents))
    admitted = policy.principals[0]
    assert len(policy.principals) == 1
    assert admitted.principal_id == principal_id
    assert admitted.verifier == verifier
    assert admitted.operations == operations
    assert type(admitted.grants) is pr.Grants
    assert admitted.grants.schema_version == 1
    assert admitted.grants.corpora == corpora
    assert admitted.grants.versions == versions
    assert admitted.grants.labels == labels
    assert len(policy.documents) == 2
    assert policy.documents[0].document_id == "doc-1"
    assert policy.documents[0].admitted == pairs
    assert policy.documents[1].document_id == "doc-2"
    assert policy.documents[1].admitted == ()
    assert policy.policy_id == golden_policy_id(principals, documents)


def test_grants_admission_is_real_controlled_mapping(monkeypatch):
    calls = []
    real_admit_record = pr.admit_record

    def recording(kind, value):
        calls.append((kind, dict(value)))
        return real_admit_record(kind, value)

    monkeypatch.setattr(spw, "admit_record", recording)
    principals = [
        ("alpha-1", _verifier(CREDENTIAL_43), ("search",), ("alpha", "beta"), ("v1",), ("l1",)),
        ("beta-2", _verifier(CREDENTIAL_2), ("answer", "search", "sources:read"), (), (), ()),
    ]
    policy = spw.admit_policy_bytes(encode_policy(principals, [("doc-1", (pair(1),))]))
    assert len(calls) == 2
    kinds, mappings = zip(*calls)
    assert all(kind == "Grants" for kind in kinds)
    for mapping in mappings:
        assert set(mapping) == {"schema_version", "corpora", "versions", "labels"}
        assert mapping["schema_version"] == 1
        assert type(mapping["corpora"]) is tuple
        assert type(mapping["versions"]) is tuple
        assert type(mapping["labels"]) is tuple
    assert mappings[0]["corpora"] == ("alpha", "beta")
    assert mappings[0]["versions"] == ("v1",)
    assert mappings[0]["labels"] == ("l1",)
    assert mappings[1]["corpora"] == ()
    assert type(policy.principals[0].grants) is pr.Grants
    assert policy.principals[0].grants.corpora == ("alpha", "beta")


def test_returns_real_typed_admitted_object():
    principals = [("alpha-1", _verifier(CREDENTIAL_43), ("search",), (), (), ())]
    documents = [("doc-1", (pair(1),))]
    policy = spw.admit_policy_bytes(encode_policy(principals, documents))
    assert type(policy) is sp.SuppliedPolicy
    direct = sp.admit_policy(
        (
            sp.PrincipalSpec(
                "alpha-1",
                _verifier(CREDENTIAL_43),
                ("search",),
                pr.Grants(schema_version=1, corpora=(), versions=(), labels=()),
            ),
        ),
        (sp.DocumentRule("doc-1", (pair(1),)),),
    )
    assert policy.policy_id == direct.policy_id
    with pytest.raises(sp.PolicyError):
        sp.SuppliedPolicy()


def test_independent_golden_identity_and_value_change():
    principals = [
        ["alpha-1", _verifier(CREDENTIAL_43), ("search",), ("alpha",), ("v1",), ("l1",)],
        ["beta-2", _verifier(CREDENTIAL_2), ("answer", "search", "sources:read"), (), (), ()],
    ]
    documents = [("doc-\u4e2d", (pair(7),))]
    wire = encode_policy(principals, documents)
    policy = spw.admit_policy_bytes(wire)
    assert policy.policy_id == golden_policy_id(principals, documents)
    assert policy.policy_id == "sha256:" + hashlib.sha256(wire).hexdigest()
    baseline = policy.policy_id
    principals[0][3] = ("alpah",)  # one value byte changed, still ordered
    changed = spw.admit_policy_bytes(encode_policy(principals, documents))
    assert changed.policy_id != baseline
    assert golden_policy_id(principals, documents) != baseline


def test_independent_test_side_framings_agree():
    shapes = [
        ([], []),
        ([("alpha-1", _verifier(CREDENTIAL_43), ("search",), (), (), ())], []),
        (
            [
                (
                    "p-uni",
                    _verifier(CREDENTIAL_2),
                    ("answer", "search", "sources:read"),
                    ("a", "b"),
                    ("v1",),
                    ("l",),
                )
            ],
            [("d-\u4e2d", (pair(9),)), ("e-1", ())],
        ),
    ]
    for principals, documents in shapes:
        expected = "sha256:" + hashlib.sha256(encode_policy(principals, documents)).hexdigest()
        assert golden_policy_id(principals, documents) == expected


UNICODE_EMPTY_CASES = [
    (
        "unicode-ids",
        [("p-unicode", _verifier(CREDENTIAL_43), ("search",), ("g\u00fc",), ("v1",), ("l1",))],
        [("doc-\u00e9", (pair(1),))],
    ),
    (
        "grants-empty-string",
        [("alpha-1", _verifier(CREDENTIAL_43), ("search",), ("", "x"), (), ())],
        [],
    ),
    (
        "control-grants-value",
        [("alpha-1", _verifier(CREDENTIAL_43), ("search",), ("\tctl",), (), ())],
        [],
    ),
    (
        "withdrawn-document",
        [("alpha-1", _verifier(CREDENTIAL_43), ("search",), (), (), ())],
        [("doc-1", ())],
    ),
    ("zero-documents", [("alpha-1", _verifier(CREDENTIAL_43), ("search",), (), (), ())], []),
]


@pytest.mark.parametrize(
    ("case", "principals", "documents"),
    UNICODE_EMPTY_CASES,
    ids=[case for case, _, _ in UNICODE_EMPTY_CASES],
)
def test_unicode_control_and_empty_cases(case, principals, documents):
    wire = encode_policy(principals, documents)
    policy = spw.admit_policy_bytes(wire)
    assert policy.policy_id == golden_policy_id(principals, documents)
    assert policy.policy_id == "sha256:" + hashlib.sha256(wire).hexdigest()
    if documents:
        assert len(policy.documents) == len(documents)
    else:
        assert policy.documents == ()


# -------------------------------------------------- actual capacity witnesses


def test_actual_20000_declarations():
    principals = [("p", _verifier(CREDENTIAL_43), ("search",), (), (), ())]
    documents = [("d%06d" % index, (pair(index),)) for index in range(20000)]
    material, framing, canonical = material_canonical(principals, documents)
    assert (material, framing, canonical) == (2840039, 320074, 3160113)
    wire = encode_policy(principals, documents)
    assert len(wire) == canonical
    policy = spw.admit_policy_bytes(wire)
    assert len(policy.principals) == 1
    assert len(policy.documents) == 20000
    assert policy.policy_id == golden_policy_id(principals, documents)


def test_actual_20000_zero_principal_variant():
    documents = [("d%06d" % index, (pair(index),)) for index in range(20000)]
    material, framing, canonical = material_canonical([], documents)
    assert (material, framing, canonical) == (2840000, 320042, 3160042)
    wire = encode_policy([], documents)
    assert len(wire) == canonical
    policy = spw.admit_policy_bytes(wire)
    assert policy.principals == ()
    assert len(policy.documents) == 20000
    assert policy.policy_id == golden_policy_id([], documents)


def _wide_values(count, per_string):
    tail_len = 6
    head = "0" * (per_string - tail_len)
    values = []
    for index in range(count):
        tail = ""
        remaining = index
        for _ in range(tail_len):
            tail = "abcdefghijklmnopqrstuvwxyz"[remaining % 26] + tail
            remaining //= 26
        values.append(head + tail)
    return tuple(values)


def _wide_views(per_string):
    principals = [
        ("p%03d" % index, bytes([index]) * 32, ("search",), _wide_values(113, per_string), (), ())
        for index in range(256)
    ]
    documents = [("d%06d" % index, (pair(index),)) for index in range(20000)]
    return principals, documents


def test_actual_m_above_sufficient_admitted():
    principals, documents = _wide_views(2200)
    material, framing, canonical = material_canonical(principals, documents)
    assert material == 66492352
    assert canonical == 66936298
    assert SUFFICIENT_MATERIAL < material <= MAX_WIRE_BYTES
    assert canonical <= MAX_WIRE_BYTES
    policy = spw.admit_policy_bytes(encode_policy(principals, documents))
    assert len(policy.principals) == 256
    assert len(policy.documents) == 20000
    assert policy.policy_id == golden_policy_id(principals, documents)


def test_actual_canonical_cap_crossing_refused():
    principals, documents = _wide_views(2214)
    material, framing, canonical = material_canonical(principals, documents)
    assert material == 66897344
    assert canonical == 67341290
    assert material <= MAX_WIRE_BYTES
    assert canonical > MAX_WIRE_BYTES
    with pytest.raises(spw.PolicyWireError):
        spw.admit_policy_bytes(encode_policy(principals, documents))


# -------------------------------------------------- size/count/remaining/EOF


def test_type_gate_exact_bytes_only():
    empty = MAGIC + _u32(1) + _u32(0) + _u32(0)
    for payload in (empty.decode("ascii"), bytearray(empty), memoryview(empty)):
        with pytest.raises(spw.PolicyWireError):
            spw.admit_policy_bytes(payload)


def test_length_boundaries():
    too_small = MAGIC + _u32(1) + _u32(0) + b"\x00\x00\x00"
    assert len(too_small) == 41
    with pytest.raises(spw.PolicyWireError):
        spw.admit_policy_bytes(too_small)
    at_cap_invalid_content = b"\x00" * MAX_WIRE_BYTES
    assert len(at_cap_invalid_content) == MAX_WIRE_BYTES
    with pytest.raises(spw.PolicyWireError):
        spw.admit_policy_bytes(at_cap_invalid_content)
    oversized = b"\x00" * (MAX_WIRE_BYTES + 1)
    assert len(oversized) == MAX_WIRE_BYTES + 1
    with pytest.raises(spw.PolicyWireError):
        spw.admit_policy_bytes(oversized)
    exact = MAGIC + _u32(1) + _u32(0) + _u32(0)
    assert spw.admit_policy_bytes(exact).principals == ()


TRUNCATION_CUTS = (
    30,
    34,
    38,
    40,
    43,
    50,
    66,
    90,
    100,
    120,
    140,
    150,
    170,
    200,
    240,
    260,
    545,
    696,
)


@pytest.mark.parametrize("cut", TRUNCATION_CUTS, ids=["cut%d" % cut for cut in TRUNCATION_CUTS])
def test_truncation_refused(cut):
    _, _, wire = _medium_wire()
    assert len(wire) == 697
    assert spw.admit_policy_bytes(wire) is not None
    with pytest.raises(spw.PolicyWireError):
        spw.admit_policy_bytes(wire[:cut])


@pytest.mark.parametrize("extra", (1, 4, 17), ids=("one-byte", "four-bytes", "seventeen-bytes"))
def test_trailing_bytes_refused(extra):
    _, _, wire = _medium_wire()
    with pytest.raises(spw.PolicyWireError):
        spw.admit_policy_bytes(wire + b"\x00" * extra)


def test_principal_count_cap_refused_before_traversal(monkeypatch):
    # 43-byte input (>= 42 minimum) with the 257 declaration: the real
    # decoder must refuse at the count check before any framed text read.
    sentinel = _Sentinel()
    monkeypatch.setattr(
        spw._Cursor,
        "framed_text",
        lambda self, field_max_bytes: (_ for _ in ()).throw(sentinel),
    )
    wire = MAGIC + _u32(1) + _u32(257) + _u32(1) + b"p"
    assert len(wire) == 43
    with pytest.raises(spw.PolicyWireError) as excinfo:
        spw.admit_policy_bytes(wire)
    assert str(excinfo.value) == "invalid supplied policy wire"
    # If the decoder had begun traversing the first principal, the
    # non-Exception sentinel would have propagated by identity instead
    # of the sanitized PolicyWireError.
    _ = sentinel


def test_document_count_cap_refused():
    with pytest.raises(spw.PolicyWireError):
        spw.admit_policy_bytes(MAGIC + _u32(1) + _u32(0) + _u32(20001))


def test_operation_count_refused():
    for operations in ((), (b"aa", b"bb", b"cc", b"dd")):
        wire = raw_wire([raw_principal(ops=operations)])
        with pytest.raises(spw.PolicyWireError):
            spw.admit_policy_bytes(wire)


def test_grants_vector_count_cap_refused():
    wire = raw_wire([raw_principal(vectors=((b"x",) * 129,))])
    with pytest.raises(spw.PolicyWireError):
        spw.admit_policy_bytes(wire)


def test_pair_count_cap_refused():
    wire = raw_wire([raw_principal()], documents=[raw_document(pair_count=65)])
    with pytest.raises(spw.PolicyWireError):
        spw.admit_policy_bytes(wire)


def _pair_views_65536():
    """1024 fixed-width sorted documents with 64 valid pairs each (65536)."""
    principals = [("alpha-1", _verifier(CREDENTIAL_43), ("search",), (), (), ())]
    documents = []
    pair_index = 0
    for doc_index in range(1024):
        pairs = tuple(
            (
                "sha256:" + format(pair_index + offset, "064x"),
                format(pair_index + offset + 10**12, "064x"),
            )
            for offset in range(64)
        )
        documents.append(("doc-%05d" % doc_index, pairs))
        pair_index += 64
    return principals, documents, pair_index


def test_cumulative_pair_total_boundary_admitted():
    principals, documents, _ = _pair_views_65536()
    policy = spw.admit_policy_bytes(encode_policy(principals, documents))
    assert len(policy.documents) == 1024
    assert sum(len(document.admitted) for document in policy.documents) == 65536
    assert policy.documents[0].document_id == "doc-00000"
    assert policy.documents[0].admitted[0] == (
        "sha256:" + format(0, "064x"),
        format(10**12, "064x"),
    )
    assert policy.documents[1023].admitted[-1] == (
        "sha256:" + format(65535, "064x"),
        format(65535 + 10**12, "064x"),
    )
    assert policy.policy_id == golden_policy_id(principals, documents)


def test_cumulative_pair_total_refused_before_pair_traversal(monkeypatch):
    record = []
    original = spw._Cursor.framed_text

    def observing(self, field_max_bytes):
        record.append(field_max_bytes)
        return original(self, field_max_bytes)

    monkeypatch.setattr(spw._Cursor, "framed_text", observing)
    principals, documents, pair_index = _pair_views_65536()
    extra_pair = (
        "sha256:" + format(pair_index, "064x"),
        format(pair_index + 10**12, "064x"),
    )
    documents.append(("doc-01024", (extra_pair,)))  # the 65537th pair
    wire = encode_policy(principals, documents)
    with pytest.raises(spw.PolicyWireError) as excinfo:
        spw.admit_policy_bytes(wire)
    assert str(excinfo.value) == "invalid supplied policy wire"
    # The genuine framed reads observed: the one real principal ID (field
    # cap 128) and its one search operation (field cap 12), then 1025
    # document IDs (field cap 1024) plus exactly 2 x 65536 pair strings;
    # the 65537th pair's revision frame (field cap 71) is never traversed.
    assert record[0] == 128
    assert record[1] == 12
    assert len(record) == 2 + 1025 + 2 * 65536
    assert record[-1] == 1024
    assert sum(field_max == 128 for field_max in record) == 1
    assert sum(field_max == 12 for field_max in record) == 1
    assert sum(field_max == 71 for field_max in record) == 65536
    assert sum(field_max == 64 for field_max in record) == 65536


FIELD_CAP_CASES = [
    ("principal-129", raw_wire([raw_principal(id_bytes=b"a" * 129)])),
    ("operation-13", raw_wire([raw_principal(ops=(b"b" * 13,))])),
    ("document-1025", raw_wire([raw_principal()], documents=[raw_document(b"d" * 1025)])),
    (
        "revision-72",
        raw_wire([raw_principal()], documents=[raw_document(b"doc", 1, ((b"r" * 72, b"s" * 64),))]),
    ),
    (
        "digest-65",
        raw_wire([raw_principal()], documents=[raw_document(b"doc", 1, ((b"r" * 71, b"s" * 65),))]),
    ),
    ("grants-value-1mib1", raw_wire([raw_principal(vectors=((b"x" * 1048577,),))])),
]


@pytest.mark.parametrize(
    ("case", "wire"), FIELD_CAP_CASES, ids=[case for case, _ in FIELD_CAP_CASES]
)
def test_field_byte_caps_refused(case, wire):
    with pytest.raises(spw.PolicyWireError):
        spw.admit_policy_bytes(wire)


def test_field_byte_cap_boundaries_admitted():
    principal_id = "a" + "b" * 127  # 128 ASCII bytes, valid charset
    document_id = "d" + "a" * 255  # 256 codepoints = 1024 UTF-8 bytes
    principals = [(principal_id, _verifier(CREDENTIAL_43), ("search",), (), (), ())]
    documents = [(document_id, (pair(1),))]
    policy = spw.admit_policy_bytes(encode_policy(principals, documents))
    assert policy.principals[0].principal_id == principal_id
    assert policy.documents[0].document_id == document_id
    assert policy.policy_id == golden_policy_id(principals, documents)


@pytest.mark.parametrize(
    ("case", "verifier_frame", "body"),
    [
        ("length-31", _u32(31), b"\x01" * 31),
        ("length-33", _u32(33), b"\x01" * 33),
        ("length-32-truncated", _u32(32), b"\x01" * 31),
    ],
)
def test_verifier_frame_refused(case, verifier_frame, body):
    if case == "length-32-truncated":
        wire = MAGIC + _u32(1) + _u32(1) + _u32(1) + b"p" + verifier_frame + body
    else:
        wire = (
            MAGIC
            + _u32(1)
            + _u32(1)
            + _u32(1)
            + b"p"
            + verifier_frame
            + body
            + _u32(1)
            + _u32(6)
            + b"search"
            + _u32(1)
            + _u32(0)
            + _u32(0)
            + _u32(0)
            + _u32(0)
        )
    with pytest.raises(spw.PolicyWireError):
        spw.admit_policy_bytes(wire)


INVALID_UTF8_CASES = [
    ("lone-continuation", b"\x80"),
    ("invalid-lead", b"\xff"),
    ("overlong", b"\xc0\x80"),
    ("surrogate", b"\xed\xa0\x80"),
    ("above-range", b"\xf4\x90\x80\x80"),
    ("incomplete", b"\xe4\xb8"),
]


@pytest.mark.parametrize(
    ("case", "raw_id"), INVALID_UTF8_CASES, ids=[case for case, _ in INVALID_UTF8_CASES]
)
def test_invalid_utf8_refused(case, raw_id):
    with pytest.raises(spw.PolicyWireError):
        spw.admit_policy_bytes(_one_principal_wire(raw_id))


@pytest.mark.parametrize(
    ("case", "top_schema", "grants_schema"),
    [
        ("top-level-zero", 0, 1),
        ("top-level-two", 2, 1),
        ("grants-zero", 1, 0),
        ("grants-two", 1, 2),
    ],
)
def test_schema_refusals(case, top_schema, grants_schema):
    wire = raw_wire([raw_principal(grants_schema=grants_schema)], schema=top_schema)
    with pytest.raises(spw.PolicyWireError):
        spw.admit_policy_bytes(wire)


@pytest.mark.parametrize(
    "position", (0, 15, 29), ids=("first-byte", "mid-magic", "last-byte-newline")
)
def test_prefix_refusals(position):
    magic = bytearray(MAGIC)
    magic[position] ^= 0x01
    wire = bytes(magic) + _u32(1) + _u32(0) + _u32(0)
    with pytest.raises(spw.PolicyWireError):
        spw.admit_policy_bytes(wire)


# ------------------------------------- structurally valid, semantically refused


SEMANTIC_CASES = [
    ("id-charset", [("p!1", _verifier(CREDENTIAL_43), ("search",), (), (), ())], []),
    ("id-leading-punct", [(".hidden", _verifier(CREDENTIAL_43), ("search",), (), (), ())], []),
    (
        "duplicate-principal-ids",
        [
            ("a", _verifier(CREDENTIAL_43), ("search",), (), (), ()),
            ("a", _verifier(CREDENTIAL_2), ("search",), (), (), ()),
        ],
        [],
    ),
    (
        "unsorted-principals",
        [
            ("b", _verifier(CREDENTIAL_43), ("search",), (), (), ()),
            ("a", _verifier(CREDENTIAL_2), ("search",), (), (), ()),
        ],
        [],
    ),
    (
        "duplicate-verifiers",
        [
            ("a", _verifier(CREDENTIAL_43), ("search",), (), (), ()),
            ("b", _verifier(CREDENTIAL_43), ("search",), (), (), ()),
        ],
        [],
    ),
    (
        "operations-unsorted",
        [("a", _verifier(CREDENTIAL_43), ("search", "answer"), (), (), ())],
        [],
    ),
    ("operations-vocabulary", [("a", _verifier(CREDENTIAL_43), ("list",), (), (), ())], []),
    ("answer-closure", [("a", _verifier(CREDENTIAL_43), ("answer",), (), (), ())], []),
    (
        "revision-shape",
        [("a", _verifier(CREDENTIAL_43), ("search",))],
        [("doc", (("sha256:" + "g" * 64, "0" * 64),))],
    ),
    (
        "digest-shape",
        [("a", _verifier(CREDENTIAL_43), ("search",))],
        [("doc", (("sha256:" + "0" * 64, "g" * 64),))],
    ),
    (
        "documents-unsorted",
        [("a", _verifier(CREDENTIAL_43), ("search",))],
        [("b-doc", (pair(1),)), ("a-doc", (pair(2),))],
    ),
    (
        "documents-duplicate",
        [("a", _verifier(CREDENTIAL_43), ("search",))],
        [("a-doc", (pair(1),)), ("a-doc", (pair(2),))],
    ),
    (
        "pairs-unsorted",
        [("a", _verifier(CREDENTIAL_43), ("search",))],
        [("doc", (pair(2), pair(1)))],
    ),
    (
        "pairs-duplicate",
        [("a", _verifier(CREDENTIAL_43), ("search",))],
        [("doc", (pair(1), pair(1)))],
    ),
]


@pytest.mark.parametrize(
    ("case", "principals", "documents"), SEMANTIC_CASES, ids=[case for case, _, _ in SEMANTIC_CASES]
)
def test_structurally_valid_semantic_refusals(case, principals, documents):
    wire = encode_policy(principals, documents)
    with pytest.raises(spw.PolicyWireError) as excinfo:
        spw.admit_policy_bytes(wire)
    assert str(excinfo.value) == "invalid supplied policy wire"


def test_grants_unsorted_api_valid_refused():
    mapping = {"schema_version": 1, "corpora": ("zeta", "alpha"), "versions": (), "labels": ()}
    grants = pr.admit_record("Grants", mapping)  # real public admission accepts unsorted
    assert grants.corpora == ("zeta", "alpha")
    spec = sp.PrincipalSpec("alpha-1", _verifier(CREDENTIAL_43), ("search",), grants)
    with pytest.raises(sp.PolicyError):
        sp.admit_policy((spec,), ())
    wire = encode_policy(
        [("alpha-1", _verifier(CREDENTIAL_43), ("search",), ("zeta", "alpha"), (), ())], []
    )
    with pytest.raises(spw.PolicyWireError):
        spw.admit_policy_bytes(wire)


# ------------------------------------------------ real outputs and predicates


def test_real_supplied_matching_through_wire():
    principals = [
        ("alpha-1", _verifier(CREDENTIAL_43), ("search",), (), (), ()),
        (
            "beta-2",
            _verifier(CREDENTIAL_2),
            ("answer", "search", "sources:read"),
            ("corpus-a",),
            ("v1",),
            ("l1",),
        ),
        ("gamma-3", _verifier(CREDENTIAL_3), ("search", "sources:read"), (), (), ()),
    ]
    policy = spw.admit_policy_bytes(encode_policy(principals, [("doc-1", (pair(1),))]))
    match = sp.match_supplied(policy, CREDENTIAL_2, ("answer", "sources:read"))
    assert type(match) is sp.SuppliedMatch
    assert match.principal_id == "beta-2"
    assert match.authorization_status == "SUPPLIED_POLICY_MATCH_ONLY"
    assert match.operations == ("answer", "search", "sources:read")
    assert match.policy_id == policy.policy_id
    assert type(match.grants) is pr.Grants
    assert match.grants.corpora == ("corpus-a",)
    assert match.grants.versions == ("v1",)
    assert match.grants.labels == ("l1",)
    assert sp.match_supplied(policy, CREDENTIAL_43, ("search",)).principal_id == "alpha-1"
    assert sp.match_supplied(policy, CREDENTIAL_3, ("search",)).principal_id == "gamma-3"
    with pytest.raises(sp.PolicyError):
        sp.match_supplied(policy, b"synthetic-credential-" + b"z" * 22, ("search",))
    with pytest.raises(sp.PolicyError):
        sp.match_supplied(policy, CREDENTIAL_43, ("answer",))


def _scope_bytes(corpus, version, labels):
    return pr.admit_record(
        "Scope",
        {
            "schema_version": 1,
            "document_id": "doc-1",
            "revision_id": "sha256:" + "ab" * 32,
            "corpus": corpus,
            "version": version,
            "labels": list(labels),
            "processing_approved": True,
            "redistribution_rights": "allowed",
        },
    )


def test_real_provenance_query_predicate_on_returned_grants():
    principals = [
        (
            "beta-2",
            _verifier(CREDENTIAL_2),
            ("answer", "search", "sources:read"),
            ("corpus-a", "corpus-b"),
            ("v1",),
            ("l1", "l2"),
        )
    ]
    policy = spw.admit_policy_bytes(encode_policy(principals, [("doc-1", (pair(1),))]))
    grants = policy.principals[0].grants
    assert type(grants) is pr.Grants
    scope_ok = _scope_bytes("corpus-a", "v1", ("l1", "l2"))
    assert pr.reader_allows(scope_ok, grants) is True
    assert pr.reader_allows(_scope_bytes("corpus-b", "v1", ("l2",)), grants) is True
    assert pr.reader_allows(_scope_bytes("corpus-x", "v1", ()), grants) is False
    assert pr.reader_allows(_scope_bytes("corpus-a", "v2", ()), grants) is False
    assert pr.reader_allows(_scope_bytes("corpus-a", None, ()), grants) is False
    assert pr.reader_allows(scope_ok, None) is False
    restrictions_ok = pr.admit_record(
        "Restrictions", {"schema_version": 1, "corpora": ["corpus-a"], "versions": ["v1"]}
    )
    assert pr.reader_allows(scope_ok, grants, restrictions_ok) is True
    restrictions_narrow = pr.admit_record(
        "Restrictions", {"schema_version": 1, "corpora": ["corpus-x"]}
    )
    assert pr.reader_allows(scope_ok, grants, restrictions_narrow) is False


# ------------------------------------------------------------ exception identity


def test_sentinel_at_grants_admission_propagates_by_identity(monkeypatch):
    sentinel = _Sentinel()

    def explode(kind, value):
        raise sentinel

    monkeypatch.setattr(spw, "admit_record", explode)
    wire = encode_policy([("alpha-1", _verifier(CREDENTIAL_43), ("search",), (), (), ())], [])
    with pytest.raises(_Sentinel) as excinfo:
        spw.admit_policy_bytes(wire)
    assert excinfo.value is sentinel


def test_sentinel_at_typed_factory_propagates_by_identity(monkeypatch):
    sentinel = _Sentinel()

    def explode(principals, documents):
        raise sentinel

    monkeypatch.setattr(spw, "admit_policy", explode)
    wire = encode_policy([("alpha-1", _verifier(CREDENTIAL_43), ("search",), (), (), ())], [])
    with pytest.raises(_Sentinel) as excinfo:
        spw.admit_policy_bytes(wire)
    assert excinfo.value is sentinel


# ------------------------------------------- transport size vs canonical semantics


def test_transport_size_and_canonical_semantics():
    principals = [
        (
            "alpha-1",
            _verifier(CREDENTIAL_43),
            ("answer", "sources:read"),
            ("alpha",),
            ("v1",),
            ("l1",),
        ),
        ("beta-2", _verifier(CREDENTIAL_2), ("search",), (), (), ()),
    ]
    documents = [("doc-1", (pair(1),)), ("doc-2", ())]
    wire = encode_policy(principals, documents)
    material, framing, canonical = material_canonical(principals, documents)
    # Actual transport size: for this exact grammar the wire bytes ARE the
    # canonical payload. Typed canonical semantics (M/H/C) are asserted
    # separately; no heap, RSS or latency claim is made.
    assert len(wire) == canonical == material + framing
    policy = spw.admit_policy_bytes(wire)
    assert policy.policy_id == "sha256:" + hashlib.sha256(wire).hexdigest()
