"""Bounded preflight tests for the shared binder declaration slice.

The expected event order, charges and final meter states are hard-coded
from the exact legacy binder source (base 416009c ``_preflight_inputs``)
as the independent reference; the committed tests do not run a second
copy of the algorithm.  Only synthetic declaration shapes and synthetic
payloads are used; no dependency or source access occurs.
"""

import struct
from pathlib import Path

import pytest

from slaif_raggedized_helper import source_bound_stage_loss as binder

ROOT = "/safe/root"
DATA = b"{}"
CASE = "case"
GOLD = ("0" * 64, "1" * 64)
IDS = ("a" * 64, "sha256:" + "b" * 64, "c" * 64, "d" * 64)
DEADLINE_MS = 1
PAYLOAD = struct.pack("<1024f", 1.0, *([0.0] * 1023))

# Exact legacy-source reference for the shared declaration prefix: meter
# events in order, then final totals and per-category accounting.
DECLARATION_EVENTS = [
    ("reserve", 11, 40, "local"),    # root utf-8 reserve
    ("reserve", 11, 0, "local"),     # root slash-count reserve
    ("reserve", 11, 8232, "local"),  # root component reserve
    ("reserve", 5, 0, "local"),      # case-id reserve
    ("reserve", 1, 0, "local"),      # gold[0] shape reserve
    ("reserve", 65, 0, "local"),     # gold[0] grammar reserve
    ("reserve", 1, 0, "local"),      # gold[1] shape reserve
    ("reserve", 65, 0, "local"),     # gold[1] grammar reserve
    ("compare", 64, 64, -1),         # gold[0] < gold[1], one 129 charge
    ("reserve", 1, 0, "local"),      # identifiers[0] shape reserve
    ("reserve", 65, 0, "local"),     # identifiers[0] grammar reserve
    ("reserve", 1, 0, "local"),      # identifiers[1] shape reserve
    ("reserve", 72, 0, "local"),     # identifiers[1] grammar reserve
    ("reserve", 1, 0, "local"),      # identifiers[2] shape reserve
    ("reserve", 65, 0, "local"),     # identifiers[2] grammar reserve
    ("reserve", 1, 0, "local"),      # identifiers[3] shape reserve
    ("reserve", 65, 0, "local"),     # identifiers[3] grammar reserve
]
DECLARATION_WORK = 570
DECLARATION_PAYLOAD = 8272
LOCAL_PREFIX = (441, 8272)
STRING_COMPARE_PREFIX = (129, 0)
VECTOR_EVENT = ("reserve", 8193, 135168, "local")
OLD_WORK = 8763
OLD_PAYLOAD = 143440


class SpyMeter:
    """Delegating spy: committed events plus the last reserve attempt."""

    def __init__(self, work_limit=134217728, payload_limit=268435456):
        self.inner = binder._Meter(work_limit=work_limit, payload_limit=payload_limit)
        self.events = []
        self.last_attempt = None

    def reserve(self, work, payload=0, *, category="local"):
        self.last_attempt = ("reserve", work, payload, category)
        self.inner.reserve(work, payload, category=category)
        self.events.append(self.last_attempt)

    def compare_strings(self, left, right):
        result = self.inner.compare_strings(left, right)
        self.events.append(("compare", len(left), len(right), result))
        return result


def _states(spy):
    return (
        (spy.inner.work, spy.inner.payload),
        dict(spy.inner.categories),
    )


def test_binder_import_originates_from_test_module_checkout():
    test_file = Path(__file__).resolve()
    expected = (
        test_file.parents[2] / "src" / "slaif_raggedized_helper" / "source_bound_stage_loss.py"
    ).resolve()
    assert Path(binder.__file__).resolve() == expected


def test_valid_declaration_matches_legacy_metered_prefix():
    declared = SpyMeter()
    binder._preflight_declaration(ROOT, DATA, CASE, GOLD, IDS, DEADLINE_MS, declared)
    assert declared.events == DECLARATION_EVENTS
    assert _states(declared) == (
        (DECLARATION_WORK, DECLARATION_PAYLOAD),
        {
            "local": list(LOCAL_PREFIX),
            "string_compare": list(STRING_COMPARE_PREFIX),
            "json_emit": [0, 0],
            "pure_delegate": [0, 0],
        },
    )
    legacy = SpyMeter()
    binder._preflight_inputs(ROOT, DATA, CASE, GOLD, PAYLOAD, IDS, DEADLINE_MS, legacy)
    assert legacy.events == DECLARATION_EVENTS + [VECTOR_EVENT]
    assert legacy.inner.work == OLD_WORK
    assert legacy.inner.payload == OLD_PAYLOAD


def test_declaration_path_performs_no_vector_work():
    budget = DECLARATION_WORK + 100
    declared = SpyMeter(work_limit=budget)
    binder._preflight_declaration(ROOT, DATA, CASE, GOLD, IDS, DEADLINE_MS, declared)
    assert declared.events == DECLARATION_EVENTS
    assert declared.inner.work == DECLARATION_WORK
    assert declared.inner.payload == DECLARATION_PAYLOAD
    # The same budget on the old path is refused at the vector
    # reservation, before unpack, finite or norm work: the committed
    # meter stops at the declaration prefix and the last attempt is the
    # vector reservation itself.
    legacy = SpyMeter(work_limit=budget)
    with pytest.raises(ValueError):
        binder._preflight_inputs(ROOT, DATA, CASE, GOLD, PAYLOAD, IDS, DEADLINE_MS, legacy)
    assert legacy.events == DECLARATION_EVENTS
    assert legacy.last_attempt == VECTOR_EVENT
    assert legacy.inner.work == DECLARATION_WORK
    assert legacy.inner.payload == DECLARATION_PAYLOAD
    # A tighter budget refuses the declaration before its third guarded
    # root operation, at the third root reservation.
    tight = SpyMeter(work_limit=30)
    with pytest.raises(ValueError):
        binder._preflight_declaration(ROOT, DATA, CASE, GOLD, IDS, DEADLINE_MS, tight)
    assert tight.events == DECLARATION_EVENTS[:2]
    assert tight.last_attempt == DECLARATION_EVENTS[2]
    assert (tight.inner.work, tight.inner.payload) == (22, 40)


def test_legacy_path_refuses_missing_foreign_and_falsy_payload_before_first_metered_check():
    bad_payloads = (
        None,
        "x" * 4096,
        b"\x00" * 4095,
        b"",
        0,
        object(),
        binder._LEGACY_PAYLOAD_MODE,
        binder._DECLARATION_MODE,
    )
    for bad_payload in bad_payloads:
        meter = SpyMeter()
        with pytest.raises(ValueError):
            binder._preflight_inputs(
                ROOT, DATA, CASE, GOLD, bad_payload, IDS, DEADLINE_MS, meter
            )
        assert meter.events == []
        assert (meter.inner.work, meter.inner.payload) == (0, 0)


def test_legacy_vector_checks_keep_reserve_order_and_reject_bad_values():
    for bad_payload in (
        struct.pack("<1024f", float("nan"), *([0.0] * 1023)),
        struct.pack("<1024f", 2.0, *([0.0] * 1023)),
    ):
        meter = SpyMeter()
        with pytest.raises(ValueError):
            binder._preflight_inputs(
                ROOT, DATA, CASE, GOLD, bad_payload, IDS, DEADLINE_MS, meter
            )
        assert meter.events == DECLARATION_EVENTS + [VECTOR_EVENT]
        assert (meter.inner.work, meter.inner.payload) == (OLD_WORK, OLD_PAYLOAD)


def test_declaration_and_legacy_reject_bad_path_at_identical_point():
    bad_root = "/safe/../root"
    prefix = [
        ("reserve", 14, 52, "local"),
        ("reserve", 14, 0, "local"),
        ("reserve", 14, 8244, "local"),
    ]
    declared = SpyMeter()
    with pytest.raises(ValueError):
        binder._preflight_declaration(bad_root, DATA, CASE, GOLD, IDS, DEADLINE_MS, declared)
    legacy = SpyMeter()
    with pytest.raises(ValueError):
        binder._preflight_inputs(
            bad_root, DATA, CASE, GOLD, PAYLOAD, IDS, DEADLINE_MS, legacy
        )
    assert declared.events == prefix
    assert legacy.events == prefix
    assert (declared.inner.work, declared.inner.payload) == (42, 8296)
    assert (legacy.inner.work, legacy.inner.payload) == (42, 8296)


def test_declaration_and_legacy_reject_nonascending_gold_at_identical_point():
    gold = ("1" * 64, "0" * 64)
    declared = SpyMeter()
    with pytest.raises(ValueError):
        binder._preflight_declaration(ROOT, DATA, CASE, gold, IDS, DEADLINE_MS, declared)
    legacy = SpyMeter()
    with pytest.raises(ValueError):
        binder._preflight_inputs(ROOT, DATA, CASE, gold, PAYLOAD, IDS, DEADLINE_MS, legacy)
    prefix = DECLARATION_EVENTS[:8] + [("compare", 64, 64, 1)]
    assert declared.events == prefix
    assert legacy.events == prefix
    assert (declared.inner.work, declared.inner.payload) == (428, 8272)
    assert (legacy.inner.work, legacy.inner.payload) == (428, 8272)


def test_declaration_and_legacy_reject_bad_identifier_at_identical_point():
    bad_ids = ("a" * 64, "b" * 64, "c" * 64, "d" * 64)
    declared = SpyMeter()
    with pytest.raises(ValueError):
        binder._preflight_declaration(ROOT, DATA, CASE, GOLD, bad_ids, DEADLINE_MS, declared)
    legacy = SpyMeter()
    with pytest.raises(ValueError):
        binder._preflight_inputs(ROOT, DATA, CASE, GOLD, PAYLOAD, bad_ids, DEADLINE_MS, legacy)
    prefix = DECLARATION_EVENTS[:9] + [
        ("reserve", 1, 0, "local"),
        ("reserve", 65, 0, "local"),
        ("reserve", 1, 0, "local"),
    ]
    assert declared.events == prefix
    assert legacy.events == prefix
    assert (declared.inner.work, declared.inner.payload) == (366, 8272)
    assert (legacy.inner.work, legacy.inner.payload) == (366, 8272)
