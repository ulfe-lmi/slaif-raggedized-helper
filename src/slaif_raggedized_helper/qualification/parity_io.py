"""Bounded operator-local JSON I/O for pure parity analyzers.

``read_document(path)`` returns a document and SHA-256/size of its exact bytes.
``preflight_output(path)`` checks an operator-selected destination without creating it;
``run_export(document, analyzer, destination)`` preflights before calling the trusted
analyzer and returns its result, or raises ExportError carrying that result after work.
A CLI can map Refusal to 2, ExportError to 3, and success to 0. Analyzer errors
remain the analyzer's responsibility. No transport or model accounting is implied.

Input/output defaults are 16 MiB, maximum 64 MiB; depth 64, 2 million nodes,
1 MiB per string and 128 characters per numeric token. Encoding is UTF-8 JSON,
sorted keys, compact separators, non-ASCII preserved, no trailing newline. All
limits apply to both directions. File paths are operator choices, never JSON data.
Final components must be regular files, never symlinks. Descriptor type and size
are checked on the opened object, reads are capped at limit+1, and metadata changes
while reading are refused. Parent directories and hard links are trusted operator
choices; concurrent in-place changes that restore metadata cannot be detected.
Preflight is advisory: destination races or write failures are post-work errors;
export verifies the opened descriptor before truncation, but is not atomic or durable.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

DEFAULT_BYTES = 16 * 1024 * 1024
MAX_BYTES = 64 * 1024 * 1024
MAX_DEPTH = 64
MAX_NODES = 2_000_000
MAX_STRING = 1024 * 1024
MAX_NUMBER = 128


class Refusal(ValueError):
    """Fixed, input-free pre-work refusal."""


class ExportError(Exception):
    """Post-work export failure; evidence retains the analyzer's result."""

    def __init__(self, evidence: Any):
        super().__init__("export failed after analysis")
        self.evidence = evidence


@dataclass(frozen=True)
class AdmittedDocument:
    document: Any
    sha256: str
    byte_count: int


def _limit(limit: int) -> None:
    if type(limit) is not int or not 1 <= limit <= MAX_BYTES:
        raise Refusal("invalid byte limit")


def _number(token: str, convert: Callable) -> Any:
    if len(token) > MAX_NUMBER:
        raise Refusal("invalid JSON number")
    value = convert(token)
    if isinstance(value, float) and not math.isfinite(value):
        raise Refusal("invalid JSON number")
    return value


def _pairs(pairs: list) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise Refusal("duplicate JSON key")
        result[key] = value
    return result


def _validate(value: Any) -> None:
    stack = [(value, 0)]
    count = 0
    while stack:
        item, depth = stack.pop()
        count += 1
        if count > MAX_NODES or depth > MAX_DEPTH:
            raise Refusal("JSON structure limit exceeded")
        if isinstance(item, str):
            if len(item) > MAX_STRING:
                raise Refusal("JSON string limit exceeded")
            try:
                item.encode("utf-8")
            except UnicodeEncodeError:
                raise Refusal("invalid JSON Unicode") from None
        elif item is None or type(item) is bool:
            pass
        elif type(item) is int:
            if item.bit_length() > 430:
                raise Refusal("invalid JSON number")
        elif type(item) is float:
            if not math.isfinite(item):
                raise Refusal("invalid JSON number")
        elif type(item) is list:
            stack.extend((x, depth + 1) for x in item)
        elif type(item) is dict:
            if any(type(k) is not str for k in item):
                raise Refusal("invalid JSON value")
            stack.extend((x, depth + 1) for pair in item.items() for x in pair)
        else:
            raise Refusal("invalid JSON value")


def _depth_check(text: str) -> None:
    depth = 0
    quoted = escaped = False
    for char in text:
        if quoted:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                quoted = False
        elif char == '"':
            quoted = True
        elif char in "[{":
            depth += 1
            if depth > MAX_DEPTH:
                raise Refusal("JSON structure limit exceeded")
        elif char in "]}":
            depth -= 1


def read_document(path: str | Path, *, max_bytes: int = DEFAULT_BYTES) -> AdmittedDocument:
    _limit(max_bytes)
    fd = None
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW | os.O_CLOEXEC)
        before = os.fstat(fd)
        if not stat.S_ISREG(before.st_mode):
            raise Refusal("unsupported input file")
        chunks = []
        remaining = max_bytes + 1
        while remaining:
            chunk = os.read(fd, min(65536, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        raw = b"".join(chunks)
        after = os.fstat(fd)
        if len(raw) > max_bytes:
            raise Refusal("input byte limit exceeded")
        if (before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (
            after.st_size, after.st_mtime_ns, after.st_ctime_ns
        ) or len(raw) != after.st_size:
            raise Refusal("input changed during read")
        text = raw.decode("utf-8")
        _depth_check(text)
        document = json.loads(text, object_pairs_hook=_pairs,
                              parse_int=lambda s: _number(s, int),
                              parse_float=lambda s: _number(s, float),
                              parse_constant=lambda _: (_ for _ in ()).throw(
                                  Refusal("invalid JSON number")))
        _validate(document)
        return AdmittedDocument(document, hashlib.sha256(raw).hexdigest(), len(raw))
    except Refusal:
        raise
    except (OSError, ValueError, UnicodeError, RecursionError, TypeError):
        raise Refusal("invalid input file or JSON") from None
    finally:
        if fd is not None:
            os.close(fd)


def render_json(value: Any, *, max_bytes: int = DEFAULT_BYTES) -> bytes:
    _limit(max_bytes)
    _validate(value)
    try:
        encoder = json.JSONEncoder(ensure_ascii=False, allow_nan=False, sort_keys=True,
                                   separators=(",", ":"))
        result = bytearray()
        for part in encoder.iterencode(value):
            encoded = part.encode("utf-8")
            if len(result) + len(encoded) > max_bytes:
                raise Refusal("output byte limit exceeded")
            result.extend(encoded)
        return bytes(result)
    except Refusal:
        raise
    except (ValueError, TypeError, UnicodeError, RecursionError):
        raise Refusal("invalid JSON value") from None


def preflight_output(path: str | Path) -> None:
    try:
        p = Path(path)
        if not p.name or not p.parent.is_dir():
            raise Refusal("invalid output destination")
        if p.exists() or p.is_symlink():
            if not stat.S_ISREG(p.lstat().st_mode) or not os.access(p, os.W_OK):
                raise Refusal("invalid output destination")
        elif not os.access(p.parent, os.W_OK | os.X_OK):
            raise Refusal("invalid output destination")
    except Refusal:
        raise
    except (OSError, ValueError, TypeError):
        raise Refusal("invalid output destination") from None


def run_export(document: Any, analyzer: Callable[[Any], Any], destination: str | Path,
               *, max_bytes: int = DEFAULT_BYTES) -> Any:
    _limit(max_bytes)
    preflight_output(destination)
    evidence = analyzer(document)
    fd = None
    try:
        data = render_json(evidence, max_bytes=max_bytes)
        fd = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_NONBLOCK | os.O_NOFOLLOW
                     | os.O_CLOEXEC, 0o600)
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            raise OSError("unsupported output")
        os.ftruncate(fd, 0)
        view = memoryview(data)
        while view:
            written = os.write(fd, view)
            if written <= 0:
                raise OSError("short write")
            view = view[written:]
        return evidence
    except (OSError, Refusal, ValueError, TypeError):
        raise ExportError(evidence) from None
    finally:
        if fd is not None:
            os.close(fd)
