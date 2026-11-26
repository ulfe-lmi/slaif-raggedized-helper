"""Pure private selected-publication policy record parser; no I/O or writer."""

import json
import re
from dataclasses import dataclass


class PolicySelectionError(ValueError):
    """Fixed, input-free selected-publication refusal."""

    def __init__(self):
        super().__init__("policy selection refused")


@dataclass(frozen=True, slots=True)
class PolicySelection:
    """Frozen record identity; wire and semantic IDs stay distinct."""

    selection_bytes: bytes
    generation: int
    wire_bytes: int
    wire_sha256: str


_KIND = "slaif-current-policy-selection-v1"
_MAX_GENERATION = 2**63 - 1
_MIN_WIRE_BYTES = 42
_MAX_WIRE_BYTES = 67108864
_MAX_RECORD_BYTES = 512
_KEYS = ("generation", "kind", "schema", "wire_bytes", "wire_sha256")


def _check(value):
    if not value:
        raise ValueError


def parse_policy_selection(data: bytes) -> PolicySelection:
    """Parse the closed canonical selected-publiculation record."""
    refused = False
    record = None
    try:
        # Type and size are validated before any decode; every later step
        # stays bounded by the 512-byte envelope.
        _check(type(data) is bytes and 1 <= len(data) <= _MAX_RECORD_BYTES)
        obj = json.loads(data.decode("ascii"))
        _check(type(obj) is dict and set(obj) == set(_KEYS))
        generation = obj["generation"]
        _check(type(generation) is int and 1 <= generation <= _MAX_GENERATION)
        _check(type(obj["kind"]) is str and obj["kind"] == _KIND)
        _check(type(obj["schema"]) is int and obj["schema"] == 1)
        wire_bytes = obj["wire_bytes"]
        _check(type(wire_bytes) is int and _MIN_WIRE_BYTES <= wire_bytes <= _MAX_WIRE_BYTES)
        wire_sha256 = obj["wire_sha256"]
        _check(
            type(wire_sha256) is str and re.fullmatch(r"[0-9a-f]{64}", wire_sha256) is not None
        )
        # Exact canonical bytes: sorted keys, compact separators, ASCII.
        # Duplicate keys, alternate spellings, noncanonical whitespace,
        # padding, BOM, trailing LF and any other deviation fail closed.
        _check(
            json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode(
                "ascii"
            )
            == data
        )
        record = PolicySelection(data, generation, wire_bytes, wire_sha256)
    except Exception:
        refused = True
    if refused:
        # Raised after the handler exits: no caught cause or context is retained.
        raise PolicySelectionError() from None
    return record
