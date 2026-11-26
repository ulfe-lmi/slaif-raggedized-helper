"""Pure byte admission for the private evaluation plan wire v1.

This module is under construction and does not expose a product interface.

``admit`` accepts exactly one ``bytes`` object of length 1..8388608 and
returns the exact existing :class:`evaluation_program.Plan` with nested
:class:`evaluation_program.Judgments` and tuples.  It performs no
filesystem, clock, config, artifact, pin, model, source I/O or resource
acquisition.  A parsed plan is a declaration, never proof of current
principal, rights, execution or relevance meaningfulness, and it cannot
manufacture qualified data or grades.

Safety structure (full reasoning in
docs/parallel/private-evaluation-plan-wire-api.md):

1. exact ``bytes`` type and the 1..8388608 length envelope;
2. a single iterative pre-materialization scan over the admitted bytes
   establishing the finite lexical/structural envelope before any JSON
   object construction: nesting depth <= 6, node count <= 196608, quoted
   string raw <= 770 bytes and decoded <= 128 codepoints, integer token
   <= 20 bytes, ASCII-only (no BOM, DEL or non-ASCII bytes, no raw
   controls outside the four JSON whitespace bytes), strict JSON token
   syntax with string/escape/number recognition, and no bool/null/float
   tokens;
3. strict ``json.loads`` with a duplicate-decoded-key hook, whose work is
   bounded by the admitted lexical envelope;
4. final exact schema validation plus the existing program
   entries/work admission arithmetic.

Every refusal raises :class:`PlanWireError` with the exact fixed message
``private evaluation plan refused``: no raw payload, key, path, hash,
grade or traceback context escapes and no partial result is returned.
``BaseException`` subclasses (``KeyboardInterrupt``, ``SystemExit`` and
the test sentinels) propagate unchanged.
"""

import json
import re

from .evaluation_program import Judgments, Plan

__all__ = ("PlanWireError", "admit")

_MESSAGE = "private evaluation plan refused"

_MAX_RAW = 8388608
_MAX_DEPTH = 6
_MAX_NODES = 196608
_MAX_STRING_RAW = 770
_MAX_STRING_DECODED = 128
_MAX_INT_TOKEN = 20
_MAX_CUTOFFS = 16
_MAX_CASES = 256
_MAX_GOLD = 4096
_MAX_CUTOFF = 4096
_MAX_ENTRIES = 65536
_MAX_WORK = 2097152
_MAX_GENERATION = 2**63 - 1
_MAX_GRADE = 3

_TOP_KEYS = frozenset((
    "schema", "plan_id", "dataset_id", "split_id", "snapshot_id", "generation",
    "catalog_id", "protocol_id", "unknown_policy", "overlap_policy", "cutoffs",
    "judgments",
))
_CASE_KEYS = frozenset(("case_id", "gold"))

_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}\Z", re.ASCII)
_HASH = re.compile(r"sha256:[0-9a-f]{64}\Z", re.ASCII)

_SPACE = (0x09, 0x0A, 0x0D, 0x20)
_HEX = frozenset(b"0123456789abcdefABCDEF")
_SIMPLE_ESCAPES = frozenset((0x22, 0x5C, 0x2F, 0x62, 0x66, 0x6E, 0x72, 0x74))
_FLOAT_MARKS = frozenset((0x2E, 0x65, 0x45))


class PlanWireError(ValueError):
    """Content-free refusal of the entire wire admission."""

    __slots__ = ()

    def __init__(self):
        super().__init__(_MESSAGE)


def _scan_string(raw, start, n):
    """Scan one quoted string opened at ``raw[start]``.

    Returns the index just past the closing quote.  Enforces the raw
    770-byte and decoded 128-codepoint envelopes, the exact JSON escape
    forms, EOF inside a string/escape, unescaped raw controls, DEL and
    non-ASCII bytes.  Escaped codepoints above U+007F (including lone
    surrogates and surrogate pairs) refuse before decoding; escaped ASCII
    (``\\u0041`` style) decodes and stays inside the envelopes.  The
    scanner counts decoded codepoints, never UTF-16 code units.
    """
    i = start + 1
    limit = start + _MAX_STRING_RAW - 1
    decoded = 0
    while True:
        if i > limit:
            raise ValueError
        if i >= n:
            raise ValueError
        b = raw[i]
        if b == 0x22:
            return i + 1
        if b == 0x5C:
            i += 1
            if i >= n:
                raise ValueError
            e = raw[i]
            if e in _SIMPLE_ESCAPES:
                i += 1
            elif e == 0x75:
                i += 1
                if i + 4 > n:
                    raise ValueError
                for j in range(i, i + 4):
                    if raw[j] not in _HEX:
                        raise ValueError
                if int(raw[i:i + 4], 16) > 0x7F:
                    raise ValueError
                i += 4
            else:
                raise ValueError
        elif b < 0x20 or b >= 0x7F:
            raise ValueError
        else:
            i += 1
        decoded += 1
        if decoded > _MAX_STRING_DECODED:
            raise ValueError


def _scan_int(raw, start, n):
    """Scan one JSON integer token opened at ``raw[start]``.

    Accepts exactly ``-?(0|[1-9][0-9]*)`` with at most 20 bytes including
    an optional minus; a following ``.``, ``e`` or ``E`` marks a float or
    exponent form and refuses.  Returns the index just past the token.
    """
    i = start
    if raw[i] == 0x2D:
        i += 1
        if i >= n or not 0x30 <= raw[i] <= 0x39:
            raise ValueError
    if raw[i] == 0x30:
        i += 1
        if i < n and 0x30 <= raw[i] <= 0x39:
            raise ValueError
    else:
        while i < n and 0x30 <= raw[i] <= 0x39:
            i += 1
    if i - start > _MAX_INT_TOKEN:
        raise ValueError
    if i < n and raw[i] in _FLOAT_MARKS:
        raise ValueError
    return i


def _scan(raw):
    """Bounded single-pass structural/lexical envelope scan.

    Iterative, with a fixed frame stack bounded by the depth cap.  Counts
    every container, object key and scalar exactly once, keys at the
    member-value depth.  Raises ``ValueError`` before any JSON object
    construction: on malformed token/escape/number syntax, disallowed
    bytes, over-envelope depth/node/string/integer-token size, content
    after the root, or any unsupported literal form (bool/null/float/
    exponent/nonfinite).  No recursion, token list, decoded string or
    container is built before the limits hold.
    """
    n = len(raw)
    i = 0
    nodes = 0
    stack = []
    state = "root_value"
    while True:
        while i < n and raw[i] in _SPACE:
            i += 1
        if i >= n:
            if state != "end":
                raise ValueError
            return
        b = raw[i]
        if state == "value_or_end" and b != 0x5D:
            state = "value"
        if state == "root_value":
            if b != 0x7B:
                raise ValueError
            i += 1
            nodes += 1
            if nodes > _MAX_NODES:
                raise ValueError
            stack.append((0x7B, "key_or_end"))
            state = "key_or_end"
        elif state == "end":
            raise ValueError
        elif state == "key_or_end":
            if b == 0x7D:
                i += 1
                stack.pop()
                state = "end" if not stack else "comma_or_end"
            elif b == 0x22:
                if len(stack) + 1 > _MAX_DEPTH:
                    raise ValueError
                nodes += 1
                if nodes > _MAX_NODES:
                    raise ValueError
                i = _scan_string(raw, i, n)
                stack[-1] = (0x7B, "colon")
                state = "colon"
            else:
                raise ValueError
        elif state == "key_required":
            # After a comma inside an object a key is required; a closing
            # brace here is a trailing comma and refuses.
            if b != 0x22:
                raise ValueError
            if len(stack) + 1 > _MAX_DEPTH:
                raise ValueError
            nodes += 1
            if nodes > _MAX_NODES:
                raise ValueError
            i = _scan_string(raw, i, n)
            stack[-1] = (0x7B, "colon")
            state = "colon"
        elif state == "colon":
            if b != 0x3A:
                raise ValueError
            i += 1
            stack[-1] = (0x7B, "value")
            state = "value"
        elif state == "value":
            if b in (0x7B, 0x5B):
                if len(stack) + 1 > _MAX_DEPTH:
                    raise ValueError
                nodes += 1
                if nodes > _MAX_NODES:
                    raise ValueError
                i += 1
                if b == 0x7B:
                    stack.append((0x7B, "key_or_end"))
                    state = "key_or_end"
                else:
                    stack.append((0x5B, "value_or_end"))
                    state = "value_or_end"
            elif b == 0x22:
                if len(stack) + 1 > _MAX_DEPTH:
                    raise ValueError
                nodes += 1
                if nodes > _MAX_NODES:
                    raise ValueError
                i = _scan_string(raw, i, n)
                stack[-1] = (stack[-1][0], "comma_or_end")
                state = "comma_or_end"
            elif b == 0x2D or 0x30 <= b <= 0x39:
                if len(stack) + 1 > _MAX_DEPTH:
                    raise ValueError
                nodes += 1
                if nodes > _MAX_NODES:
                    raise ValueError
                i = _scan_int(raw, i, n)
                stack[-1] = (stack[-1][0], "comma_or_end")
                state = "comma_or_end"
            else:
                raise ValueError
        elif state == "value_or_end":
            i += 1
            stack.pop()
            state = "end" if not stack else "comma_or_end"
        else:  # state == "comma_or_end"
            if b == 0x2C:
                i += 1
                if stack[-1][0] == 0x7B:
                    stack[-1] = (0x7B, "key_required")
                    state = "key_required"
                else:
                    stack[-1] = (0x5B, "value")
                    state = "value"
            elif b == 0x7D:
                if stack[-1][0] != 0x7B:
                    raise ValueError
                i += 1
                stack.pop()
                state = "end" if not stack else "comma_or_end"
            elif b == 0x5D:
                if stack[-1][0] != 0x5B:
                    raise ValueError
                i += 1
                stack.pop()
                state = "end" if not stack else "comma_or_end"
            else:
                raise ValueError


def _object_pairs(pairs):
    """Build a JSON object while refusing duplicate decoded keys."""
    seen = set()
    result = {}
    for key, value in pairs:
        if key in seen:
            raise ValueError
        seen.add(key)
        result[key] = value
    return result


def _id(value):
    return type(value) is str and _ID.fullmatch(value) is not None


def _hash_id(value):
    return type(value) is str and _HASH.fullmatch(value) is not None


def _int_in(value, low, high):
    return type(value) is int and low <= value <= high


def _validate(root):
    """Apply the exact wire schema and the program entries/work caps."""
    if type(root) is not dict or frozenset(root) != _TOP_KEYS:
        raise ValueError
    if type(root["schema"]) is not int or root["schema"] != 1:
        raise ValueError
    plan_id = root["plan_id"]
    protocol_id = root["protocol_id"]
    if not _id(plan_id) or not _id(protocol_id):
        raise ValueError
    dataset_id = root["dataset_id"]
    split_id = root["split_id"]
    snapshot_id = root["snapshot_id"]
    catalog_id = root["catalog_id"]
    if not all(_hash_id(v) for v in (dataset_id, split_id, snapshot_id, catalog_id)):
        raise ValueError
    if not _int_in(root["generation"], 1, _MAX_GENERATION):
        raise ValueError
    unknown_policy = root["unknown_policy"]
    if type(unknown_policy) is not str or unknown_policy != "UNJUDGED_AS_ZERO_DIAGNOSTIC":
        raise ValueError
    overlap_policy = root["overlap_policy"]
    if type(overlap_policy) is not str or overlap_policy != "EXPLICIT_CHUNK_IDS_ONLY":
        raise ValueError
    cutoffs = root["cutoffs"]
    if type(cutoffs) is not list or not 1 <= len(cutoffs) <= _MAX_CUTOFFS:
        raise ValueError
    previous = 0
    for cutoff in cutoffs:
        if not _int_in(cutoff, 1, _MAX_CUTOFF) or not previous < cutoff:
            raise ValueError
        previous = cutoff
    if 20 not in cutoffs or 60 not in cutoffs:
        raise ValueError
    judgments = root["judgments"]
    if type(judgments) is not list or not 1 <= len(judgments) <= _MAX_CASES:
        raise ValueError
    cases = []
    previous_case = None
    entries = 0
    work = 0
    k = len(cutoffs)
    for case in judgments:
        if type(case) is not dict or frozenset(case) != _CASE_KEYS:
            raise ValueError
        case_id = case["case_id"]
        if not _id(case_id):
            raise ValueError
        if previous_case is not None and not previous_case < case_id:
            raise ValueError
        previous_case = case_id
        gold = case["gold"]
        if type(gold) is not list or len(gold) > _MAX_GOLD:
            raise ValueError
        pairs = []
        previous_chunk = None
        for pair in gold:
            if type(pair) is not list or len(pair) != 2:
                raise ValueError
            chunk_id, grade = pair
            if not _hash_id(chunk_id):
                raise ValueError
            if previous_chunk is not None and not previous_chunk < chunk_id:
                raise ValueError
            previous_chunk = chunk_id
            if not _int_in(grade, 0, _MAX_GRADE):
                raise ValueError
            pairs.append((chunk_id, grade))
        g = len(pairs)
        entries += g + 60
        work += (g + 60) * k + g * max(1, (max(1, g) - 1).bit_length())
        cases.append(Judgments(case_id, tuple(pairs)))
    if entries > _MAX_ENTRIES or work > _MAX_WORK:
        raise ValueError
    return Plan(
        plan_id, dataset_id, split_id, snapshot_id, root["generation"],
        catalog_id, protocol_id, unknown_policy, overlap_policy,
        tuple(cutoffs), tuple(cases),
    )


def admit(raw):
    """Admit exact plan wire bytes and return the exact existing Plan.

    Pure byte admission: no filesystem, clock, config, artifact, pin,
    model, source I/O or resource acquisition.  Refusals raise
    :class:`PlanWireError` with the exact fixed message and no partial
    result; ``BaseException`` subclasses propagate unchanged.
    """
    if type(raw) is not bytes or not 1 <= len(raw) <= _MAX_RAW:
        raise PlanWireError()
    refused = False
    plan = None
    try:
        _scan(raw)
        root = json.loads(raw, object_pairs_hook=_object_pairs)
        plan = _validate(root)
    except Exception:
        refused = True
    if refused:
        # Raised after the routine-exception handler has left, so this
        # boundary does not retain its caught parser/schema exception as
        # context; from None keeps the suppression explicit.
        raise PlanWireError() from None
    return plan
