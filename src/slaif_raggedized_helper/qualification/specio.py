"""Bounded operator spec file input (OAP 004-b).

The trial spec file is operator-supplied UNTRUSTED input. This reader
enforces, in order, BEFORE any fingerprinting or dispatch:

1. descriptor/type: the file is opened NON-BLOCKING
   (``O_RDONLY | O_NONBLOCK``) and the ACTUAL OPENED descriptor is
   ``fstat``-checked. Directories, FIFOs, sockets and character/block
   devices — including a path that resolves through a symlink to a
   special file — are refused without ever blocking on a writer-less
   open (004-F01: an owned TEMP spec FIFO must not hang the CLI);
2. bytes: a finite documented read bound (``MAX_SPEC_FILE_BYTES``). The
   bound bounds admission, not the exact content: the bounded loop may
   read one 4096-byte chunk past the bound to detect the overflow;
3. encoding: STRICT UTF-8. Invalid Unicode is refused before
   fingerprinting/dispatch — never replaced or truncated into a new
   workload;
4. JSON: the expected decoder/type/depth/integer failures are normalized
   to FIXED typed refusal evidence. No raw traceback, no input or
   private-path echo, and no process-global decoder-limit change (the
   interpreter's integer-digit and recursion limits are left untouched;
   the failures they raise are caught and converted to typed refusals).

The CLI maps a refusal to its exit-code distinction: ``SPEC_MISSING``
(absent/unreadable) and ``SPEC_INVALID`` (fixed reason) are both
pre-dispatch refusals with zero HTTP.
"""

from __future__ import annotations

import json
import os
import stat
from dataclasses import dataclass
from typing import Any

MAX_SPEC_FILE_BYTES = 65_536
_CHUNK_BYTES = 4_096

SPEC_ERROR_MISSING = "SPEC_MISSING"
SPEC_ERROR_INVALID = "SPEC_INVALID"

REASON_ABSENT = "absent"
REASON_NOT_REGULAR = "special_file"
REASON_TOO_LONG = "file_too_long"
REASON_NOT_UTF8 = "not_utf8"
REASON_NOT_JSON = "not_json"
REASON_INTEGER_OVERFLOW = "integer_too_large"
REASON_TOO_DEEP = "too_deep"

_REASONS = {
    REASON_ABSENT: "spec file is absent or unreadable on this host",
    REASON_NOT_REGULAR: (
        "spec path is not a regular file (directory, FIFO, socket or "
        "device, including a path resolving to one); refused without "
        "blocking"
    ),
    REASON_TOO_LONG: (
        f"spec file exceeds the bounded read limit of "
        f"{MAX_SPEC_FILE_BYTES} bytes"
    ),
    REASON_NOT_UTF8: (
        "spec file is not valid UTF-8; invalid Unicode is refused, "
        "never replaced or truncated"
    ),
    REASON_NOT_JSON: "spec is not valid JSON",
    REASON_INTEGER_OVERFLOW: (
        "spec JSON integer exceeds the decoder's fixed digit bound"
    ),
    REASON_TOO_DEEP: (
        "spec JSON nesting exceeds the interpreter's recursion bound"
    ),
}


@dataclass(frozen=True)
class SpecFileRefusal:
    """Fixed typed refusal evidence for one bounded spec input failure.

    ``error`` is ``SPEC_MISSING``/``SPEC_INVALID``; ``reason`` is a fixed
    vocabulary code; ``message`` is fixed safe text (never an input
    value or a private path); ``line`` carries the decoder line number
    for ``not_json`` only.
    """

    error: str
    reason: str
    message: str
    line: int | None = None


def read_spec_file(path: str) -> tuple[bytes | None, SpecFileRefusal | None]:
    """Bounded non-blocking read of the spec file (bytes, refusal).

    Checks the descriptor ACTUALLY OPENED (fstat after a non-blocking
    open), so a symlink to a special file is caught where it matters; a
    writer-less FIFO never blocks the CLI.
    """
    flags = os.O_RDONLY | getattr(os, "O_NONBLOCK", 0)
    try:
        fd = os.open(path, flags)
    except IsADirectoryError:
        return None, SpecFileRefusal(
            SPEC_ERROR_INVALID, REASON_NOT_REGULAR,
            _REASONS[REASON_NOT_REGULAR])
    except OSError:
        return None, SpecFileRefusal(
            SPEC_ERROR_MISSING, REASON_ABSENT, _REASONS[REASON_ABSENT])
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            return None, SpecFileRefusal(
                SPEC_ERROR_INVALID, REASON_NOT_REGULAR,
                _REASONS[REASON_NOT_REGULAR])
        chunks: list[bytes] = []
        total = 0
        while total <= MAX_SPEC_FILE_BYTES:
            chunk = os.read(fd, _CHUNK_BYTES)
            if not chunk:
                break
            chunks.append(chunk)
            total += len(chunk)
        raw = b"".join(chunks)
    except OSError:
        return None, SpecFileRefusal(
            SPEC_ERROR_MISSING, REASON_ABSENT, _REASONS[REASON_ABSENT])
    finally:
        os.close(fd)
    if len(raw) > MAX_SPEC_FILE_BYTES:
        return None, SpecFileRefusal(
            SPEC_ERROR_INVALID, REASON_TOO_LONG, _REASONS[REASON_TOO_LONG])
    return raw, None


def decode_spec_text(raw: bytes) -> tuple[str | None, SpecFileRefusal | None]:
    """Strict UTF-8 decode; invalid Unicode refuses (never replaced)."""
    try:
        return raw.decode("utf-8"), None
    except UnicodeDecodeError:
        return None, SpecFileRefusal(
            SPEC_ERROR_INVALID, REASON_NOT_UTF8, _REASONS[REASON_NOT_UTF8])


def parse_spec_json(text: str) -> tuple[Any | None, SpecFileRefusal | None]:
    """JSON decode with FIXED typed handling of the expected failures.

    - malformed JSON: ``not_json`` with the decoder line number;
    - an integer literal beyond the interpreter's fixed digit bound
      raises a plain ``ValueError`` from the decoder: ``integer_too_large``
      (the process-global limit is intentionally NOT raised to work
      around the failure);
    - nesting beyond the interpreter's recursion bound raises
      ``RecursionError``: ``too_deep``;
    - a syntactically valid but wrong-type document (e.g. a top-level
      array) is a SPEC contract failure, handled by the caller's
      ``TrialSpec`` validation, not here.
    """
    try:
        return json.loads(text), None
    except json.JSONDecodeError as exc:
        return None, SpecFileRefusal(
            SPEC_ERROR_INVALID, REASON_NOT_JSON,
            f"{_REASONS[REASON_NOT_JSON]}: line {exc.lineno}",
            line=exc.lineno)
    except ValueError:
        # json.JSONDecodeError is a ValueError subclass and is handled
        # above; any remaining ValueError is the fixed integer-digit
        # bound failure (no process-global limit change is attempted).
        return None, SpecFileRefusal(
            SPEC_ERROR_INVALID, REASON_INTEGER_OVERFLOW,
            _REASONS[REASON_INTEGER_OVERFLOW])
    except RecursionError:
        return None, SpecFileRefusal(
            SPEC_ERROR_INVALID, REASON_TOO_DEEP,
            _REASONS[REASON_TOO_DEEP])


def load_trial_spec_json(path: str) -> tuple[Any | None, SpecFileRefusal | None]:
    """One bounded safe spec read: file -> bytes -> UTF-8 -> JSON.

    Returns ``(data, None)`` on success or ``(None, refusal)`` with a
    fixed typed refusal otherwise. This runs before fingerprinting or
    dispatch: a refused spec consumes zero HTTP.
    """
    raw, refusal = read_spec_file(path)
    if refusal is not None:
        return None, refusal
    assert raw is not None
    text, refusal = decode_spec_text(raw)
    if refusal is not None:
        return None, refusal
    assert text is not None
    return parse_spec_json(text)
