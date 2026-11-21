"""Pure selected-publication policy record parser evidence.

Offline and fully default-collected.  A test-side canonical emitter is an
independent re-derivation, so the parser is never its own oracle; one
literal hand-written canonical record pins the exact bytes.  The
construction-unreached sentinel installs a ``BaseException`` as
``json.loads`` (monkeypatched attribute of the real ``json`` module,
auto-restored): it escapes the implementation's broad ``Exception``
handling, so any interrupt identity loss would surface.
"""

import dataclasses
import json
from pathlib import Path

import pytest

from slaif_raggedized_helper import policy_selection as selection


_KIND = "slaif-current-policy-selection-v1"
_MAX_GENERATION = 2**63 - 1


class _BytesSubclass(bytes):
    pass


class _Interrupt(BaseException):
    pass


def _obj(**overrides):
    obj = {
        "generation": 1,
        "kind": _KIND,
        "schema": 1,
        "wire_bytes": 42,
        "wire_sha256": "0" * 64,
    }
    obj.update(overrides)
    return obj


def _render(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")


def _refuse(raw):
    with pytest.raises(selection.PolicySelectionError):
        selection.parse_policy_selection(raw)


def test_module_origin_is_assigned_worktree():
    # Portable guard derived from the resolved test path: both modules
    # originate from real files under the assigned isolated worktree.
    root = Path(__file__).resolve().parents[2]
    assert Path(__file__).resolve() == root / "tests/unit/test_policy_selection.py"
    assert (
        Path(selection.__file__).resolve()
        == root / "src/slaif_raggedized_helper/policy_selection.py"
    )


def test_literal_canonical_record():
    literal = (
        b'{"generation":1,'
        b'"kind":"slaif-current-policy-selection-v1",'
        b'"schema":1,'
        b'"wire_bytes":42,'
        b'"wire_sha256":"' + b"0" * 64 + b'"}'
    )
    assert len(literal) == 167
    record = selection.parse_policy_selection(literal)
    assert record.selection_bytes == literal
    assert (record.generation, record.wire_bytes, record.wire_sha256) == (1, 42, "0" * 64)
    # Independent re-derivation agrees with the literal byte-for-byte.
    assert literal == _render(
        {
            "generation": record.generation,
            "kind": _KIND,
            "schema": 1,
            "wire_bytes": record.wire_bytes,
            "wire_sha256": record.wire_sha256,
        }
    )


def test_record_is_frozen_nominal():
    record = selection.parse_policy_selection(_render(_obj()))
    assert type(record) is selection.PolicySelection
    assert dataclasses.is_dataclass(record) and record.__dataclass_params__.frozen is True
    with pytest.raises(dataclasses.FrozenInstanceError):
        record.selection_bytes = b""
    with pytest.raises(dataclasses.FrozenInstanceError):
        record.generation = 2
    with pytest.raises(dataclasses.FrozenInstanceError):
        record.wire_bytes = 43
    with pytest.raises(dataclasses.FrozenInstanceError):
        record.wire_sha256 = "f" * 64
    assert dataclasses.fields(record)
    assert [field.name for field in dataclasses.fields(record)] == [
        "selection_bytes",
        "generation",
        "wire_bytes",
        "wire_sha256",
    ]


def test_wire_length_boundaries():
    for wire in (42, 67108864):
        record = selection.parse_policy_selection(_render(_obj(wire_bytes=wire)))
        assert record.wire_bytes == wire
    for wire in (41, 67108865, 0, -1, True, 42.0, "42"):
        _refuse(_render(_obj(wire_bytes=wire)))


def test_generation_boundaries():
    for generation in (1, _MAX_GENERATION):
        record = selection.parse_policy_selection(_render(_obj(generation=generation)))
        assert record.generation == generation
    for generation in (0, _MAX_GENERATION + 1, -1, True, 1.0, "1"):
        _refuse(_render(_obj(generation=generation)))


def test_sha256_boundary_admission():
    for sha in ("f" * 64, "a" * 64, "0123456789abcdef" * 4):
        record = selection.parse_policy_selection(_render(_obj(wire_sha256=sha)))
        assert record.wire_sha256 == sha


@pytest.mark.parametrize(
    ("value", "case"),
    [
        (_render(_obj()).decode("ascii"), "str"),
        (bytearray(_render(_obj())), "bytearray"),
        (memoryview(_render(_obj())), "memoryview"),
        (_BytesSubclass(_render(_obj())), "bytes-subclass"),
        (None, "none"),
        (123, "int"),
        ((_render(_obj()),), "tuple"),
    ],
    ids=[c for c in ("str", "bytearray", "memoryview", "bytes-subclass", "none", "int", "tuple")],
)
def test_non_bytes_refused_without_coercion(value, case):
    _refuse(value)


def test_outer_byte_cap(monkeypatch):
    calls = []
    real_loads = json.loads

    def counting(*args, **kwargs):
        calls.append(1)
        return real_loads(*args, **kwargs)

    monkeypatch.setattr(json, "loads", counting)
    # 513 bytes: refused by the envelope before any decode.
    _refuse(b" " * 513)
    assert calls == []
    # 512 bytes: inside the envelope, decode attempted, refused on content.
    _refuse(b" " * 512)
    assert calls == [1]
    # A valid 167-byte record is inside the envelope; padding it to 513
    # with ASCII keeps it decode-bounded but out of range.
    padded = _render(_obj()) + b" " * (513 - 167)
    _refuse(padded)
    assert calls == [1]


def test_exact_canonical_bytes():
    canonical = _render(_obj())
    assert selection.parse_policy_selection(canonical).selection_bytes == canonical
    # Key order is canonical sorted order; any other order is refused.
    shuffled = json.dumps(
        {
            "wire_sha256": "0" * 64,
            "kind": _KIND,
            "wire_bytes": 42,
            "generation": 1,
            "schema": 1,
        },
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("ascii")
    _refuse(shuffled)
    # Noncanonical whitespace anywhere is refused.
    _refuse(canonical.replace(b":", b": ", 1))
    _refuse(canonical.replace(b",", b", ", 1))
    _refuse(canonical.replace(b"{", b"{ ", 1))


def test_trailing_and_leading_data_refused():
    canonical = _render(_obj())
    _refuse(canonical + b"\n")
    _refuse(canonical + b" ")
    _refuse(canonical + b"\n\n")
    _refuse(canonical + b"{}")
    _refuse(canonical + b"x")
    _refuse(b" " + canonical)
    _refuse(b"\n" + canonical)
    _refuse(canonical[:-1] + b" }")


@pytest.mark.parametrize(
    ("field", "value", "case"),
    [
        ("generation", True, "gen-bool"),
        ("generation", "1", "gen-str"),
        ("generation", 1.0, "gen-float"),
        ("schema", True, "schema-bool"),
        ("schema", 2, "schema-two"),
        ("schema", "1", "schema-str"),
        ("kind", "SLAIF-CURRENT-POLICY-SELECTION-V1", "kind-upper"),
        ("kind", "slaif-current-policy-selection-v2", "kind-v2"),
        ("kind", "raw-snapshot-selection-data-v1", "kind-wrong"),
        ("kind", _KIND[:-2], "kind-trimmed"),
        ("kind", 1, "kind-int"),
    ],
    ids=[
        "gen-bool",
        "gen-str",
        "gen-float",
        "schema-bool",
        "schema-two",
        "schema-str",
        "kind-upper",
        "kind-v2",
        "kind-wrong",
        "kind-trimmed",
        "kind-int",
    ],
)
def test_type_bool_schema_kind_refused(field, value, case):
    _refuse(_render(_obj(**{field: value})))


@pytest.mark.parametrize(
    ("sha", "case"),
    [
        ("A" * 64, "upper"),
        ("Ab" + "a" * 62, "mixed-case"),
        ("0" * 63, "short"),
        ("0" * 65, "long"),
        ("", "empty"),
        ("0" * 32 + "g" + "0" * 31, "letter-g"),
        ("0" * 32 + "z" + "0" * 31, "letter-z"),
        ("0" * 32 + "+" + "0" * 31, "plus"),
        ("0" * 32 + " " + "0" * 31, "space"),
    ],
    ids=["upper", "mixed-case", "short", "long", "empty", "letter-g", "letter-z", "plus", "space"],
)
def test_wire_sha256_case_length_alphabet_refused(sha, case):
    _refuse(_render(_obj(wire_sha256=sha)))


def test_non_ascii_and_encoding_refused():
    canonical = _render(_obj())
    # Raw non-ASCII bytes inside the 512-byte envelope are refused.
    start = canonical.index(b'"wire_sha256":"') + len(b'"wire_sha256":"')
    _refuse(canonical[:start] + b"\xe9" + canonical[start + 1 :])
    _refuse(b"\x80")
    # Non-ASCII byte inside a key position.
    _refuse(canonical.replace(b"kind", b"ki\xff"))
    # Alternate encodings of the same canonical object.
    text = canonical.decode("ascii")
    _refuse(text.encode("utf-16"))
    _refuse(text.encode("utf-16-be"))
    _refuse(b"\xff\xfe" + text.encode("utf-16-le"))
    # BOMs are padding and refused.
    _refuse(b"\xef\xbb\xbf" + canonical)
    # Non-ASCII value text is canonical-escaped, hence noncanonical bytes.
    _refuse(_render(_obj(wire_sha256="0" * 31 + "\u00e9" + "0" * 31)))


def test_key_set_refusals():
    canonical = _render(_obj())
    _refuse(canonical.replace(b'{"generation":1,', b'{"generation":1,"generation":1,'))
    _refuse(canonical.replace(b'"schema":1,', b'"schema":1,"schema":1,'))
    _refuse(canonical[:-1] + b',"policy_id":"p"}')
    _refuse(canonical.replace(b'"wire_bytes":42,', b""))
    _refuse(canonical.replace(b'"kind":"' + _KIND.encode("ascii") + b'",', b""))
    _refuse(b"{}")


@pytest.mark.parametrize(
    "raw",
    [b"[1,2]", b'"kind"', b"1", b"null", b"true", b"{", b'{"generation":1'],
    ids=["array", "string", "int", "null", "true", "open-brace", "truncated"],
)
def test_non_object_root_refused(raw):
    _refuse(raw)


def test_error_hygiene():
    for raw in (b"", b"x" * 513, b"\x80", b"{}", _render(_obj(wire_sha256="A" * 64))):
        with pytest.raises(selection.PolicySelectionError) as exc:
            selection.parse_policy_selection(raw)
        assert str(exc.value) == "policy selection refused"
        assert exc.value.args == ("policy selection refused",)
        assert type(exc.value) is selection.PolicySelectionError
        assert isinstance(exc.value, ValueError)
        assert exc.value.__cause__ is None
        assert exc.value.__context__ is None
        assert exc.value.__suppress_context__
        # No partial result or input echo escapes the boundary.
        assert not hasattr(exc.value, "selection_bytes")
        assert not hasattr(exc.value, "generation")
        assert b"wire_sha256" not in repr(exc.value).encode("ascii", "replace")


def test_non_exception_interrupt_identity(monkeypatch):
    sentinel = _Interrupt()

    def forbidden(*args, **kwargs):
        raise sentinel

    monkeypatch.setattr(json, "loads", forbidden)
    with pytest.raises(_Interrupt) as exc:
        selection.parse_policy_selection(_render(_obj()))
    assert exc.value is sentinel
