"""Pure plan-wire admission evidence; no source, native, model or network.

Fully default-collected and offline.  Compatibility cases drive the
actual ``evaluation_program._plan_admission`` code against a manually
constructed exact Plan and the wire-parsed Plan, so the parser is never
its own oracle.  Construction-unreached regressions install a
``BaseException`` sentinel as ``json.loads``: it escapes the
implementation's broad ``Exception`` handling, so if the strict
pre-materialization scanner failed to refuse an input, the sentinel
would surface instead of :class:`PlanWireError`.  The sentinel is a
monkeypatched attribute of the real ``json`` module (auto-restored): no
fake modules, no ``sys.modules`` pollution.
"""

import dataclasses
import json
import time
from pathlib import Path

import pytest

import test_source_cohort_runner as fixture
from slaif_raggedized_helper import evaluation_plan_wire as wire
from slaif_raggedized_helper import evaluation_program as program
from slaif_raggedized_helper import source_cohort_runner as runner
from slaif_raggedized_helper import text_evaluation_dataset as dataset_module

_MAX_RAW = 8388608
_TOP_KEYS = (
    "schema", "plan_id", "dataset_id", "split_id", "snapshot_id", "generation",
    "catalog_id", "protocol_id", "unknown_policy", "overlap_policy", "cutoffs",
    "judgments",
)
_UNKNOWN_POLICY = "UNJUDGED_AS_ZERO_DIAGNOSTIC"
_OVERLAP_POLICY = "EXPLICIT_CHUNK_IDS_ONLY"


def _chunk(seed, index):
    return "sha256:" + format(seed + index, "064x")


def _case(index, pair_count=0, seed=0):
    gold = [[_chunk(seed, i), i % 4] for i in range(pair_count)]
    return {"case_id": "case%03d" % index, "gold": gold}


def _obj(**overrides):
    obj = {
        "schema": 1,
        "plan_id": "plan",
        "dataset_id": "sha256:" + "1" * 64,
        "split_id": "sha256:" + "2" * 64,
        "snapshot_id": "sha256:" + "3" * 64,
        "generation": 1,
        "catalog_id": "sha256:" + "4" * 64,
        "protocol_id": "protocol",
        "unknown_policy": _UNKNOWN_POLICY,
        "overlap_policy": _OVERLAP_POLICY,
        "cutoffs": [20, 60],
        "judgments": [_case(0)],
    }
    obj.update(overrides)
    return obj


def _render(obj):
    return json.dumps(obj, separators=(",", ":"), ensure_ascii=True).encode("ascii")


def _valid_raw_template(generation=b"1", plan_id=b'"PLAN"'):
    parts = [
        b'{"schema":1,"plan_id":', plan_id,
        b',"dataset_id":"sha256:' + b"1" * 64 + b'",',
        b'"split_id":"sha256:' + b"2" * 64 + b'",',
        b'"snapshot_id":"sha256:' + b"3" * 64 + b'",',
        b'"generation":' + generation + b',',
        b'"catalog_id":"sha256:' + b"4" * 64 + b'",',
        b'"protocol_id":"protocol",',
        b'"unknown_policy":"UNJUDGED_AS_ZERO_DIAGNOSTIC",',
        b'"overlap_policy":"EXPLICIT_CHUNK_IDS_ONLY",',
        b'"cutoffs":[20,60],',
        b'"judgments":[{"case_id":"case000","gold":[]}]}',
    ]
    return b"".join(parts)


def _max_shape_obj():
    # N=16, K=16, fifteen 4096-pair cases and one 3136-pair case:
    # entries = 64576 + 960 = 65536 (exact cap), work = 1823488.
    cutoffs = [20, 40, 60, 80, 100, 200, 300, 400,
               500, 600, 700, 800, 900, 1000, 2000, 4096]
    cases = [_case(i, 4096, seed=i * 100000) for i in range(15)]
    cases.append(_case(15, 3136, seed=15 * 100000))
    return _obj(cutoffs=cutoffs, judgments=cases)


def _program_envelope(cutoff_count, pair_counts):
    """Independent re-derivation of the program entries/work arithmetic."""
    entries = 0
    work = 0
    for g in pair_counts:
        entries += g + 60
        work += (g + 60) * cutoff_count + g * max(1, (max(1, g) - 1).bit_length())
    return entries, work


class _NoopMeter:
    def reserve(self, *args):
        pass


class _NoopClock:
    def check(self):
        pass


class _WireInterrupt(BaseException):
    pass


class _ConstructionReached(BaseException):
    """Sentinel escaping the implementation's broad Exception handling."""


def _forbid_construction(monkeypatch):
    def forbidden(*args, **kwargs):
        raise _ConstructionReached()

    monkeypatch.setattr(json, "loads", forbidden)


def _assert_real_global_origins():
    import sys

    root = Path(__file__).resolve().parents[2]
    checked = 0
    for name, module in tuple(sys.modules.items()):
        if name == "slaif_raggedized_helper" or name.startswith("slaif_raggedized_helper."):
            base = root / "src"
        elif name.startswith("test_"):
            base = root / "tests/unit"
        else:
            continue
        origin = getattr(module, "__file__", None)
        assert origin is not None
        origin_path = Path(origin).resolve()
        assert origin_path.is_file()
        assert origin_path.is_relative_to(base)
        checked += 1
    assert checked > 0


def test_module_origins_are_assigned_worktree():
    # Opening guard: every loaded product/test module originates from a real
    # regular file under the assigned resolved worktree roots.
    _assert_real_global_origins()


class _BytesSubclass(bytes):
    pass


@pytest.mark.parametrize(
    "value",
    [
        "{}",
        bytearray(b"{}"),
        memoryview(b"{}"),
        _BytesSubclass(b"{}"),
        None,
        123,
        (b"{}",),
    ],
)
def test_non_bytes_refused_without_coercion(value):
    with pytest.raises(wire.PlanWireError):
        wire.admit(value)


def test_length_envelope():
    with pytest.raises(wire.PlanWireError):
        wire.admit(b"")
    with pytest.raises(wire.PlanWireError):
        wire.admit(b" " * (_MAX_RAW + 1))
    # Exactly 8MiB of allowed whitespace is inside the length envelope but
    # has no root object, so it still refuses on shape.
    with pytest.raises(wire.PlanWireError):
        wire.admit(b" " * _MAX_RAW)


@pytest.mark.parametrize(
    "raw",
    [
        b"",
        b"[",
        b'{"a":}',
        b"\x80",
        b"\xef\xbb\xbf" + b"{}",
        _render(_obj(judgments=[])),
        _render(_obj(schema=2)),
    ],
)
def test_refusal_message_sanitized(raw):
    with pytest.raises(wire.PlanWireError) as exc:
        wire.admit(raw)
    assert str(exc.value) == "private evaluation plan refused"
    assert exc.value.args == ("private evaluation plan refused",)
    assert type(exc.value) is wire.PlanWireError
    assert isinstance(exc.value, ValueError)
    assert exc.value.__context__ is None
    assert exc.value.__cause__ is None


def test_refusal_returns_no_partial_result():
    with pytest.raises(wire.PlanWireError) as exc:
        wire.admit(_render(_obj(judgments=[])))
    assert not hasattr(exc.value, "plan")
    assert not hasattr(exc.value, "progress")


def test_base_exception_identity_propagates(monkeypatch):
    sentinel = _WireInterrupt()

    def forbidden(*args, **kwargs):
        raise sentinel

    monkeypatch.setattr(json, "loads", forbidden)
    with pytest.raises(_WireInterrupt) as exc:
        wire.admit(_render(_obj()))
    assert exc.value is sentinel


def test_minimal_explicit_20_60_plan_admits():
    obj = _obj(judgments=[_case(0, 1, seed=7)])
    plan = wire.admit(_render(obj))
    assert type(plan) is program.Plan
    assert (
        plan.plan_id, plan.dataset_id, plan.split_id, plan.snapshot_id,
        plan.generation, plan.catalog_id, plan.protocol_id,
    ) == (
        "plan", "sha256:" + "1" * 64, "sha256:" + "2" * 64,
        "sha256:" + "3" * 64, 1, "sha256:" + "4" * 64, "protocol",
    )
    assert (plan.unknown_policy, plan.overlap_policy) == (
        _UNKNOWN_POLICY, _OVERLAP_POLICY,
    )
    assert type(plan.cutoffs) is tuple and plan.cutoffs == (20, 60)
    assert type(plan.judgments) is tuple and len(plan.judgments) == 1
    judgment = plan.judgments[0]
    assert type(judgment) is program.Judgments
    assert judgment.case_id == "case000"
    assert judgment.gold == (("sha256:" + format(7, "064x"), 0),)


def test_minimal_empty_gold_admits():
    plan = wire.admit(_render(_obj(judgments=[_case(0)])))
    assert plan.judgments[0].gold == ()


def test_full_256_cases_admit():
    obj = _obj(judgments=[_case(i) for i in range(256)])
    plan = wire.admit(_render(obj))
    assert len(plan.judgments) == 256
    entries, work = _program_envelope(2, [0] * 256)
    assert entries == 15360 and work == 30720


def test_max_shape_admits_at_exact_entry_cap_and_actual_max_work():
    raw = _render(_max_shape_obj())
    plan = wire.admit(raw)
    assert len(plan.judgments) == 16 and len(plan.cutoffs) == 16
    entries, work = _program_envelope(16, [4096] * 15 + [3136])
    assert entries == 65536
    assert work == 1823488 <= 2097152
    assert [len(j.gold) for j in plan.judgments] == [4096] * 15 + [3136]


def test_max_shape_compact_wire_fits_eight_mib_and_coarse_partition():
    raw = _render(_max_shape_obj())
    assert len(raw) < _MAX_RAW
    # Coarse documented partition for this shape class: 2048 root +
    # 200/case + 78/pair + 5/cutoff.
    assert len(raw) <= 2048 + 200 * 16 + 78 * 64576 + 5 * 16


def test_entry_cap_plus_one_refused():
    # 3137 instead of 3136: entries = 65537 > 65536 while work stays at
    # 1823516 < 2097152, so the entries envelope is the violated bound.
    obj = _max_shape_obj()
    last = obj["judgments"][-1]["gold"]
    last.append(["sha256:" + format(15 * 100000 + 3136, "064x"), 0])
    with pytest.raises(wire.PlanWireError):
        wire.admit(_render(obj))


def test_over_work_necessarily_violates_earlier_envelopes():
    # 256 cases sharing 100000 pairs with 16 cutoffs: entries = 115360 and
    # work > 2097152 both exceed their caps, but the 196608 node envelope
    # is the earliest violated bound while the raw stays under 8MiB.  No
    # fixture can violate the work bound alone under the current caps, so
    # attribution belongs to the earliest envelope; work normativity is
    # proven by the formula equality in the max-shape test.
    counts = [391] * 160 + [390] * 96
    assert sum(counts) == 100000
    entries, work = _program_envelope(16, counts)
    assert entries > 65536 and work > 2097152
    parts = []
    for i, g in enumerate(counts):
        pairs = b",".join(
            b'["sha256:' + format(i * 5000 + j, "064x").encode("ascii")
            + b'",0]'
            for j in range(g)
        )
        parts.append(b'{"case_id":"case%03d","gold":[' % i + pairs + b"]}")
    raw = (
        b'{"schema":1,"plan_id":"plan","dataset_id":"sha256:' + b"1" * 64
        + b'","split_id":"sha256:' + b"2" * 64 + b'","snapshot_id":"sha256:'
        + b"3" * 64 + b'","generation":1,"catalog_id":"sha256:' + b"4" * 64
        + b'","protocol_id":"protocol",'
        b'"unknown_policy":"UNJUDGED_AS_ZERO_DIAGNOSTIC",'
        b'"overlap_policy":"EXPLICIT_CHUNK_IDS_ONLY",'
        b'"cutoffs":[20,40,60,80,100,200,300,400,500,600,700,800,'
        b'900,1000,2000,4096],"judgments":['
        + b",".join(parts) + b"]}"
    )
    assert len(raw) < _MAX_RAW
    with pytest.raises(wire.PlanWireError):
        wire.admit(raw)


def test_gold_per_case_cap_exact():
    plan = wire.admit(_render(_obj(judgments=[_case(0, 4096, seed=3)])))
    assert len(plan.judgments[0].gold) == 4096


def test_gold_per_case_over_cap_refused():
    with pytest.raises(wire.PlanWireError):
        wire.admit(_render(_obj(judgments=[_case(0, 4097, seed=3)])))


def test_case_count_over_cap_refused():
    obj = _obj(judgments=[_case(i) for i in range(257)])
    with pytest.raises(wire.PlanWireError):
        wire.admit(_render(obj))


def test_cutoff_count_over_cap_refused():
    cutoffs = [20, 60] + [100 + 10 * i for i in range(15)]
    assert len(cutoffs) == 17
    with pytest.raises(wire.PlanWireError):
        wire.admit(_render(_obj(cutoffs=cutoffs)))


def test_wired_plan_field_value_identity_vs_manual():
    obj = _obj(judgments=[_case(0, 2, seed=5), _case(1)])
    wired = wire.admit(_render(obj))
    manual = program.Plan(
        "plan", "sha256:" + "1" * 64, "sha256:" + "2" * 64,
        "sha256:" + "3" * 64, 1, "sha256:" + "4" * 64, "protocol",
        _UNKNOWN_POLICY, _OVERLAP_POLICY, (20, 60),
        (
            program.Judgments(
                "case000",
                ((_chunk(5, 0), 0), (_chunk(5, 1), 1)),
            ),
            program.Judgments("case001", ()),
        ),
    )
    assert wired == manual
    assert type(wired) is program.Plan
    assert program._closed(wired, program.Plan)
    for judgment in wired.judgments:
        assert type(judgment) is program.Judgments
        assert program._closed(judgment, program.Judgments)
        assert type(judgment.gold) is tuple
    for pair in wired.judgments[0].gold:
        assert type(pair) is tuple and len(pair) == 2


@pytest.mark.parametrize("count,gold_cases", [(1, (0,)), (3, (0, 2, 1))])
def test_wired_and_manual_plans_admit_identically_in_program(
        monkeypatch, count, gold_cases):
    args, kwargs, calls, captured = fixture.controlled(monkeypatch, count)
    dataset = dataset_module.admit(args[4])
    snapshot_id = "sha256:" + "3" * 64
    catalog_id = "sha256:" + "4" * 64
    case_ids = tuple(c.case_id for c in dataset.cases)
    judgments = []
    for i, case_id in enumerate(case_ids):
        gold = [[_chunk(i * 100, j), j % 4] for j in range(2)] if i in gold_cases else []
        judgments.append({"case_id": case_id, "gold": gold})
    obj = {
        "schema": 1,
        "plan_id": "plan",
        "dataset_id": dataset.dataset_id,
        "split_id": dataset.split_id,
        "snapshot_id": snapshot_id,
        "generation": 1,
        "catalog_id": catalog_id,
        "protocol_id": "protocol",
        "unknown_policy": _UNKNOWN_POLICY,
        "overlap_policy": _OVERLAP_POLICY,
        "cutoffs": [20, 60],
        "judgments": judgments,
    }
    wired = wire.admit(_render(obj))
    manual = program.Plan(
        "plan", dataset.dataset_id, dataset.split_id, snapshot_id, 1,
        catalog_id, "protocol", _UNKNOWN_POLICY, _OVERLAP_POLICY, (20, 60),
        tuple(
            program.Judgments(
                case_id,
                tuple((_chunk(i * 100, j), j % 4) for j in range(2))
                if i in gold_cases else (),
            )
            for i, case_id in enumerate(case_ids)
        ),
    )
    assert wired == manual
    selected = tuple((c, None, None, None) for c in dataset.cases)
    budget = program.GradeBudget(*program._MAX_BUDGET)
    left = program._plan_admission(
        wired, budget, dataset, selected, _NoopMeter(), _NoopClock())
    right = program._plan_admission(
        manual, budget, dataset, selected, _NoopMeter(), _NoopClock())
    assert left == right
    # Negative control: the same program admission is case-sensitive, so
    # identity is not vacuous.
    mismatch = dataclasses.replace(
        manual,
        judgments=(program.Judgments("case999", ()), *manual.judgments[1:]),
    )
    with pytest.raises(ValueError):
        program._plan_admission(
            mismatch, budget, dataset, selected, _NoopMeter(), _NoopClock())


def test_wire_and_manual_plans_share_real_program_plan_identity(monkeypatch):
    # Genuine controlled preflight/identity: the real
    # source._input_admission over the fixture pin, data, queries and
    # authority, then the real program._prepare/_State computing
    # plan_identity through the real binder._canonical_hash, mirroring the
    # run_cohort sequence up to (and excluding) any pin, source, native or
    # model use.  The fixture's recorded lower delegates stay uninvoked.
    args, kwargs, calls, _ = fixture.controlled(monkeypatch, 1)
    clock = runner._Deadline(time.monotonic(), 120000)
    dataset, selected, selection, _ = runner._input_admission(
        *args,
        kwargs["grants"],
        kwargs["restrictions"],
        kwargs["config"],
        kwargs["budget"],
        clock,
    )
    assert selection == "FULL_ADMITTED_SPLIT"
    assert calls == []
    snapshot_id = "sha256:" + "3" * 64
    catalog_id = "sha256:" + "4" * 64
    case_ids = tuple(c.case_id for c in dataset.cases)
    obj = {
        "schema": 1,
        "plan_id": "plan",
        "dataset_id": dataset.dataset_id,
        "split_id": dataset.split_id,
        "snapshot_id": snapshot_id,
        "generation": 1,
        "catalog_id": catalog_id,
        "protocol_id": "protocol",
        "unknown_policy": _UNKNOWN_POLICY,
        "overlap_policy": _OVERLAP_POLICY,
        "cutoffs": [20, 60],
        "judgments": [
            {
                "case_id": case_id,
                "gold": [[_chunk(i * 100, j), j % 4] for j in range(2)],
            }
            for i, case_id in enumerate(case_ids)
        ],
    }
    wired = wire.admit(_render(obj))
    manual = program.Plan(
        "plan", dataset.dataset_id, dataset.split_id, snapshot_id, 1,
        catalog_id, "protocol", _UNKNOWN_POLICY, _OVERLAP_POLICY, (20, 60),
        tuple(
            program.Judgments(
                case_id,
                tuple((_chunk(i * 100, j), j % 4) for j in range(2)),
            )
            for i, case_id in enumerate(case_ids)
        ),
    )
    assert wired == manual

    def prepare(plan):
        state = program._State(
            plan, program.GradeBudget(*program._MAX_BUDGET))
        program._prepare(
            state, dataset, selected, selection, args[5], args[6], args[7],
            kwargs["config"], kwargs["budget"], clock,
        )
        return state

    identity = prepare(wired).plan_identity
    assert prepare(manual).plan_identity == identity
    assert type(identity) is str and identity.startswith("sha256:")
    assert len(identity) == 71
    assert all(c in "0123456789abcdef" for c in identity[7:])
    # The wire schema discriminator is fixed to 1 at admission and is not a
    # Plan field, so it cannot enter the identity content.
    assert "schema" not in tuple(f.name for f in dataclasses.fields(program.Plan))
    # Equivalent wire spelling of the same decoded plan: escaped ASCII must
    # not change the real identity.
    escaped = _render(obj).replace(
        b'"plan_id":"plan"', b'"plan_id":"pl\\u0061n"', 1)
    assert json.loads(b'"pl\\u0061n"') == "plan"
    assert prepare(wire.admit(escaped)).plan_identity == identity
    # Non-vacuity control: one semantic change moves the identity.
    changed = dict(obj, generation=2)
    assert prepare(wire.admit(_render(changed))).plan_identity != identity


def _splice_after_first_value_quote(raw, replacement):
    idx = raw.find(b'"plan"')
    assert idx != -1
    return raw[: idx + 1] + replacement + raw[idx + 2:]


def test_allowed_whitespace_admitted():
    raw = (
        b"\t \r\n"
        b'{"schema": 1, "plan_id": "plan", "dataset_id": "sha256:'
        + b"1" * 64
        + b'", "split_id": "sha256:'
        + b"2" * 64
        + b'", "snapshot_id": "sha256:'
        + b"3" * 64
        + b'", "generation": 1, "catalog_id": "sha256:'
        + b"4" * 64
        + b'", "protocol_id": "protocol", "unknown_policy": "'
        + b"UNJUDGED_AS_ZERO_DIAGNOSTIC"
        + b'", "overlap_policy": "'
        + b"EXPLICIT_CHUNK_IDS_ONLY"
        + b'", "cutoffs": [ 20 , 60 ], "judgments": [ {"case_id": "case000", '
        b'"gold": []} ]}\r\n\t '
    )
    plan = wire.admit(raw)
    assert plan.cutoffs == (20, 60)
    assert plan.judgments[0].gold == ()


@pytest.mark.parametrize("control", [0x00, 0x01, 0x08, 0x0B, 0x0C, 0x0E, 0x1F])
def test_forbidden_raw_controls_outside_strings(control):
    with pytest.raises(wire.PlanWireError):
        wire.admit(bytes([control]) + b"{}")


@pytest.mark.parametrize("control", [0x00, 0x01, 0x1F])
def test_unescaped_controls_inside_strings_refused(control):
    raw = _splice_after_first_value_quote(_render(_obj()), bytes([control]))
    with pytest.raises(wire.PlanWireError):
        wire.admit(raw)


@pytest.mark.parametrize("byte", [0x7F, 0x80, 0xC3, 0xE9, 0xFF])
def test_del_and_non_ascii_bytes_refused(byte):
    raw = _splice_after_first_value_quote(_render(_obj()), bytes([byte]))
    with pytest.raises(wire.PlanWireError):
        wire.admit(raw)


def test_bom_prefix_refused():
    with pytest.raises(wire.PlanWireError):
        wire.admit(b"\xef\xbb\xbf" + _render(_obj()))


@pytest.mark.parametrize(
    "escape",
    [
        b"\\u00e9",
        b"\\ud83d",
        b"\\udc00",
        b"\\ud83d\\ude00",
        b"\\u0000",
    ],
)
def test_escaped_non_ascii_and_surrogates_refused(escape):
    raw = _valid_raw_template(plan_id=b'"pl' + escape + b'an"')
    with pytest.raises(wire.PlanWireError):
        wire.admit(raw)


def test_escaped_ascii_stays_admitted():
    raw = _valid_raw_template(plan_id=b'"pl\\u0061n"')
    assert json.loads(b'"pl\\u0061n"') == "plan"
    plan = wire.admit(raw)
    assert plan.plan_id == "plan"


@pytest.mark.parametrize(
    "plan_id",
    [
        b'"pl\\q"',
        b'"pl\\x41"',
        b'"pl\\u12G4"',
        b'"pl\\u00"',
    ],
)
def test_escape_syntax_refused(plan_id):
    with pytest.raises(wire.PlanWireError):
        wire.admit(_valid_raw_template(plan_id=plan_id))


def test_unicode_escape_incomplete_at_eof():
    with pytest.raises(wire.PlanWireError):
        wire.admit(b'{"plan_id":"pl\\u12')


def test_backslash_at_eof():
    with pytest.raises(wire.PlanWireError):
        wire.admit(b'{"plan_id":"pl\\')


def test_unterminated_string_at_eof():
    with pytest.raises(wire.PlanWireError):
        wire.admit(b'{"plan_id":"pl')


def test_unterminated_container_at_eof():
    with pytest.raises(wire.PlanWireError):
        wire.admit(_valid_raw_template()[:-1])


def test_string_raw_envelope_boundary():
    escaped = b"\\u0061" * 128
    raw = _valid_raw_template(plan_id=b'"' + escaped + b'"')
    assert len(escaped) + 2 == 770
    plan = wire.admit(raw)
    assert plan.plan_id == "a" * 128


def test_string_over_envelope_refused():
    # 129 escaped codepoints: raw 776 > 770 and decoded 129 > 128; the raw
    # envelope is the earliest violated bound in the scanner.
    escaped = b"\\u0061" * 129
    with pytest.raises(wire.PlanWireError):
        wire.admit(_valid_raw_template(plan_id=b'"' + escaped + b'"'))


@pytest.mark.parametrize(
    "generation",
    [
        b"01", b"007", b"-01", b"+1", b"1.5", b"1e2", b"1E2", b"1.", b".5",
        b"0e5", b"9" * 21, b"-",
    ],
)
def test_integer_token_grammar_refused(generation):
    with pytest.raises(wire.PlanWireError):
        wire.admit(_valid_raw_template(generation=generation))


def test_max_generation_admitted():
    raw = _valid_raw_template(generation=b"9223372036854775807")
    plan = wire.admit(raw)
    assert plan.generation == 2**63 - 1


@pytest.mark.parametrize(
    "literal", ["true", "null", "1e2", "NaN", "Infinity", "1", "0x1"]
)
def test_quoted_literal_looks_remain_ids(literal):
    plan = wire.admit(_render(_obj(plan_id=literal)))
    assert plan.plan_id == literal


@pytest.mark.parametrize(
    "value", ["", "_plan", "-plan", ".plan", "plan id", "a" * 129, "pl\u00e9"]
)
def test_id_grammar_refused(value):
    for field in ("plan_id", "protocol_id"):
        obj = _obj(**{field: value})
        with pytest.raises(wire.PlanWireError):
            wire.admit(_render(obj))


def test_id_grammar_positive_edges():
    obj = _obj(plan_id="a.b_c-d:9", protocol_id="Z" * 128)
    plan = wire.admit(_render(obj))
    assert plan.plan_id == "a.b_c-d:9"
    assert plan.protocol_id == "Z" * 128


@pytest.mark.parametrize(
    "value",
    [
        "1" * 64,
        "sha512:" + "1" * 64,
        "sha256:" + "1" * 63,
        "sha256:" + "1" * 65,
        "sha256:" + "1" * 63 + "g",
        "sha256:" + "A" * 64,
    ],
)
def test_hash_grammar_refused(value):
    for field in ("dataset_id", "split_id", "snapshot_id", "catalog_id"):
        obj = _obj(**{field: value})
        with pytest.raises(wire.PlanWireError):
            wire.admit(_render(obj))


@pytest.mark.parametrize("schema", [0, 2, -1, "1", None, True, False, 1.5])
def test_schema_must_be_exact_int_1(schema):
    obj = _obj(schema=schema)
    with pytest.raises(wire.PlanWireError):
        wire.admit(_render(obj))


@pytest.mark.parametrize("value", [0, -1, 2**63, True, "1", 1.5])
def test_generation_refused(value):
    obj = _obj(generation=value)
    with pytest.raises(wire.PlanWireError):
        wire.admit(_render(obj))


@pytest.mark.parametrize(
    "value",
    [
        "UNJUDGED_AS_ZERO",
        "UNJUDGED_AS_ZERO_DIAGNOSTIC ",
        "unjudged_as_zero_diagnostic",
        None,
        1,
    ],
)
def test_unknown_policy_refused(value):
    obj = _obj(unknown_policy=value)
    with pytest.raises(wire.PlanWireError):
        wire.admit(_render(obj))


@pytest.mark.parametrize(
    "value",
    [
        "EXPLICIT_CHUNK_IDS_ONLY ",
        "explicit_chunk_ids_only",
        "EXPLICIT_CHUNK_IDS",
        None,
        1,
    ],
)
def test_overlap_policy_refused(value):
    obj = _obj(overlap_policy=value)
    with pytest.raises(wire.PlanWireError):
        wire.admit(_render(obj))


@pytest.mark.parametrize(
    "cutoffs",
    [
        [],
        [20],
        [60],
        [20, 20, 60],
        [60, 20],
        [0, 20, 60],
        [20, 60, 4097],
        [20, 60, "61"],
        [20, True, 60],
        [20, 60.0],
        [20, 60] + [100 + 10 * i for i in range(15)],
        [[20, 60]],
        {"a": 1},
        42,
    ],
)
def test_cutoffs_refused(cutoffs):
    obj = _obj(cutoffs=cutoffs)
    with pytest.raises(wire.PlanWireError):
        wire.admit(_render(obj))


def test_judgments_count_and_shape_refused():
    for judgments in ([], "case000", 123, [{}], ["case000"], [123]):
        obj = _obj(judgments=judgments)
        with pytest.raises(wire.PlanWireError):
            wire.admit(_render(obj))


@pytest.mark.parametrize("keys", [("case_id",), ("gold",), ("case_id", "gold", "extra")])
def test_case_key_set_refused(keys):
    case = {}
    for key in keys:
        case[key] = "case000" if key == "case_id" else []
    with pytest.raises(wire.PlanWireError):
        wire.admit(_render(_obj(judgments=[case])))


def test_case_id_order_and_duplicate_refused():
    obj = _obj(judgments=[_case(1), _case(0)])
    with pytest.raises(wire.PlanWireError):
        wire.admit(_render(obj))
    obj = _obj(judgments=[_case(0), _case(0)])
    with pytest.raises(wire.PlanWireError):
        wire.admit(_render(obj))


def test_chunk_id_grammar_and_order_refused():
    chunk = "sha256:" + "5" * 64
    for gold in (
        [[chunk, 1], [chunk, 0]],
        [["sha256:" + "6" * 64, 1], [chunk, 0]],
        [["1" * 64, 1]],
        [["sha256:" + "A" * 64, 1]],
        [[chunk, 1], [chunk, 1]],
    ):
        obj = _obj(judgments=[{"case_id": "case000", "gold": gold}])
        with pytest.raises(wire.PlanWireError):
            wire.admit(_render(obj))


@pytest.mark.parametrize("grade", [4, -1, True, "1", 1.0])
def test_grade_refused(grade):
    gold = [["sha256:" + "5" * 64, grade]]
    obj = _obj(judgments=[{"case_id": "case000", "gold": gold}])
    with pytest.raises(wire.PlanWireError):
        wire.admit(_render(obj))


def test_gold_pair_shape_refused():
    chunk = "sha256:" + "5" * 64
    for gold in (
        {"a": 1},
        [[chunk]],
        [[chunk, 1, 2]],
        [chunk, 1],
        [[chunk, [1]]],
        ["x"],
    ):
        obj = _obj(judgments=[{"case_id": "case000", "gold": gold}])
        with pytest.raises(wire.PlanWireError):
            wire.admit(_render(obj))


def test_missing_top_level_keys_refused():
    for key in _TOP_KEYS:
        obj = _obj()
        del obj[key]
        with pytest.raises(wire.PlanWireError):
            wire.admit(_render(obj))


@pytest.mark.parametrize("key", ["grade_budget", "source", "model", "budget", "x"])
def test_unknown_top_level_key_refused(key):
    # Trusted runtime inputs (GradeBudget, source, model, credentials) stay
    # outside the wire; unknown-key rejection enforces that separation.
    obj = _obj()
    obj[key] = 1
    with pytest.raises(wire.PlanWireError):
        wire.admit(_render(obj))


def test_escaped_decoded_duplicate_root_keys_refused():
    # Decoded, the escaped key is exactly plan_id; with last-key-wins the
    # document would still be a fully valid plan, so refusal must come from
    # decoded duplicate detection, not from an unknown key.
    dup = b'"plan_id":"plan","pl\\u0061n_id":"plan"'
    raw = _valid_raw_template().replace(b'"plan_id":"PLAN"', dup, 1)
    assert json.loads(b'"pl\\u0061n_id"') == "plan_id"
    with pytest.raises(wire.PlanWireError):
        wire.admit(raw)


def test_escaped_decoded_duplicate_schema_key_refused():
    assert json.loads(b'"s\\u0063hema"') == "schema"
    raw = _valid_raw_template().replace(b'"schema":1', b'"schema":1,"s\\u0063hema":1', 1)
    with pytest.raises(wire.PlanWireError):
        wire.admit(raw)


def test_escaped_decoded_nested_case_key_refused():
    dup = b'"case_id":"case000","c\\u0061se_id":"case001"'
    raw = _valid_raw_template().replace(b'"case_id":"case000"', dup, 1)
    assert json.loads(b'"c\\u0061se_id"') == "case_id"
    with pytest.raises(wire.PlanWireError):
        wire.admit(raw)


def test_root_must_be_one_plain_object():
    for raw in (
        b"[]",
        b"[1]",
        b"1",
        b'"plan"',
        b"null",
        b"true",
        b"false",
        b"NaN",
        b"Infinity",
        b"-Infinity",
        b"1.0",
        b"1e2",
        b"0x1",
        b"{}",
        b"{} {}",
        b"{}{}",
        b'{"schema":1} extra',
        b'{} // not a comment',
        b'{} # not a comment',
    ):
        with pytest.raises(wire.PlanWireError):
            wire.admit(raw)


@pytest.mark.parametrize(
    "raw",
    [
        b'{"x":0,}',
        b'{"x":{"y":0,}}',
        _valid_raw_template()[:-1] + b",}",
        _valid_raw_template().replace(b'"gold":[]', b'"gold":[],}', 1),
        b"[1,]",
        b"[1,2,]",
        b'{"a":1,,}',
        b'{"a":,1}',
        b'{"a":1 "b":2}',
        b'{"a" 1}',
        b'{"a":1}}',
        b'{{"a":1}}',
        b":",
    ],
)
def test_malformed_structure_refused(raw):
    with pytest.raises(wire.PlanWireError):
        wire.admit(raw)


def test_depth_seven_refused_before_construction(monkeypatch):
    # A pair whose grade is a one-element array pushes a scalar to depth 7.
    _forbid_construction(monkeypatch)
    obj = _obj()
    obj["judgments"] = [
        {"case_id": "case000", "gold": [["sha256:" + "5" * 64, [0]]]}
    ]
    with pytest.raises(wire.PlanWireError):
        wire.admit(_render(obj))


def test_node_envelope_refused_before_construction(monkeypatch):
    # 98304 two-node members plus the root object: 196609 nodes, depth 2,
    # far below the 8MiB raw cap and the string/int envelopes.
    _forbid_construction(monkeypatch)
    pairs = b",".join(b'"k%05d":0' % i for i in range(98304))
    raw = b"{" + pairs + b"}"
    assert len(raw) < _MAX_RAW
    with pytest.raises(wire.PlanWireError):
        wire.admit(raw)


def _construction_guard_raws():
    node_raw = b"{" + b",".join(b'"k%05d":0' % i for i in range(98304)) + b"}"
    obj = _obj()
    obj["judgments"] = [
        {"case_id": "case000", "gold": [["sha256:" + "5" * 64, [0]]]}
    ]
    depth7 = _render(obj)
    return [
        (b'{"x":0,}', "object trailing comma root"),
        (b'{"x":{"y":0,}}', "object trailing comma nested"),
        (_valid_raw_template()[:-1] + b",}", "valid root trailing comma"),
        (
            _valid_raw_template().replace(b'"gold":[]', b'"gold":[],}', 1),
            "valid case trailing comma",
        ),
        (b" " * (_MAX_RAW + 1), "over 8MiB length"),
        (b"\xef\xbb\xbf" + _valid_raw_template(), "BOM prefix"),
        (_valid_raw_template(generation=b"9" * 21), "21 digit integer token"),
        (
            _valid_raw_template(plan_id=b'"' + b"\\u0061" * 129 + b'"'),
            "over raw string envelope",
        ),
        (depth7, "depth seven"),
        (node_raw, "over node envelope"),
    ]


_GUARD_IDS = [name for _, name in _construction_guard_raws()]


@pytest.mark.parametrize(
    "raw", [raw for raw, _ in _construction_guard_raws()], ids=_GUARD_IDS
)
def test_scanner_refusals_never_reach_construction(monkeypatch, raw):
    # The sentinel escapes the broad Exception handling: if any of these
    # inputs reached the general JSON decoder, the sentinel BaseException
    # would surface instead of PlanWireError and the test would fail.
    _forbid_construction(monkeypatch)
    with pytest.raises(wire.PlanWireError) as exc:
        wire.admit(raw)
    assert str(exc.value) == "private evaluation plan refused"


def test_final_restored_global_origins():
    # Final restored-state guard, last in this module: after every
    # monkeypatched case above (each auto-restored by monkeypatch), the
    # loaded product/test origins are still real regular files under the
    # assigned resolved worktree roots.
    _assert_real_global_origins()
