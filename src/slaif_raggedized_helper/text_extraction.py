"""Bounded exact native text extraction from an operator-controlled OriginalStore."""

from __future__ import annotations

import hashlib
import json
import re
import time
from dataclasses import dataclass

from pydantic import ValidationError

from .provenance_records import Block, Dependency, ProvenanceError, Scope, catalog, extraction_id
from .schema import fingerprint
from .source_admission import AdmissionError, OriginalStore, Revision

MAX_BYTES = 2_000_000
MAX_CHARS = 1_000_000
MAX_BLOCKS = 4096
MAX_LINE_CHARS = 200_000
MAX_WORK_SECONDS = 5.0
_HEADING = re.compile(r"^ {0,3}#{1,6}(?:[ \t]|$)")
_LIST = re.compile(r"^ {0,3}(?:[-+*]|[0-9]{1,9}[.)])[ \t]+")
_FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})")


class ExtractionError(ValueError):
    """Input-free extraction refusal; no partial result is returned."""


@dataclass(frozen=True)
class ExtractionPolicy:
    """Limits may only narrow the versioned v1 ceilings."""

    max_bytes: int = MAX_BYTES
    max_chars: int = MAX_CHARS
    max_blocks: int = MAX_BLOCKS
    max_line_chars: int = MAX_LINE_CHARS

    def __post_init__(self) -> None:
        for value, ceiling in (
            (self.max_bytes, MAX_BYTES),
            (self.max_chars, MAX_CHARS),
            (self.max_blocks, MAX_BLOCKS),
            (self.max_line_chars, MAX_LINE_CHARS),
        ):
            if type(value) is not int or not 1 <= value <= ceiling:
                raise ExtractionError("invalid extraction policy")

    @property
    def definition(self) -> str:
        return json.dumps(
            {
                "adapter": "native-text-markdown-lines",
                "version": 1,
                "max_bytes": self.max_bytes,
                "max_chars": self.max_chars,
                "max_blocks": self.max_blocks,
                "max_line_chars": self.max_line_chars,
                "work_seconds": MAX_WORK_SECONDS,
            },
            sort_keys=True,
            separators=(",", ":"),
        )

    @property
    def fingerprint(self) -> str:
        return extraction_id(self.definition)


@dataclass(frozen=True)
class ExtractionResult:
    revision: Revision
    scope: Scope
    dependency: Dependency
    blocks: tuple[Block, ...]


def extract(
    store: OriginalStore, revision_id: str, policy: ExtractionPolicy | None = None
) -> ExtractionResult:
    """Return all exact lines only after source and limit validation succeeds."""
    try:
        if type(store) is not OriginalStore:
            raise ValueError
        if policy is None:
            policy = ExtractionPolicy()
        if type(policy) is not ExtractionPolicy:
            raise ValueError
        # Revalidate even an instance forged with object.__setattr__.
        policy = ExtractionPolicy(
            policy.max_bytes, policy.max_chars, policy.max_blocks, policy.max_line_chars
        )
        deadline = time.monotonic() + MAX_WORK_SECONDS
        revision = store.inspect(revision_id)
        scope = catalog((revision,))[0]
        if revision.source.media_type not in ("text/plain", "text/markdown"):
            raise ValueError
        if revision.source.size > policy.max_bytes or time.monotonic() >= deadline:
            raise ValueError
        raw = store.read_original(revision_id)
        if len(raw) > policy.max_bytes or time.monotonic() >= deadline:
            raise ValueError
        text = raw.decode("utf-8", errors="strict")
        if len(text) > policy.max_chars or time.monotonic() >= deadline:
            raise ValueError
        lines = text.splitlines(keepends=True)
        if len(lines) > policy.max_blocks:
            raise ValueError
        dep = Dependency(
            schema_version=1,
            revision_id=revision.revision_id,
            extraction_id=policy.fingerprint,
            definition=policy.definition,
        )
        blocks = []
        fence_char = None
        fence_length = 0
        for index, line in enumerate(lines):
            if len(line) > policy.max_line_chars or time.monotonic() >= deadline:
                raise ValueError
            kind = "text"
            if revision.source.media_type == "text/markdown":
                marker = _FENCE.match(line)
                if fence_char is not None:
                    kind = "code"
                    if (
                        marker
                        and marker.group(1)[0] == fence_char
                        and len(marker.group(1)) >= fence_length
                    ):
                        # Closing fences require only whitespace after the marker.
                        if not line[marker.end() :].strip():
                            fence_char = None
                elif marker:
                    kind = "code"
                    fence_char, fence_length = marker.group(1)[0], len(marker.group(1))
                elif _HEADING.match(line):
                    kind = "heading"
                elif _LIST.match(line):
                    kind = "list"
            digest = hashlib.sha256(line.encode("utf-8")).hexdigest()
            anchor = f"line:{index + 1}"
            block_id = fingerprint(
                {
                    "kind": "native-text-block",
                    "version": 1,
                    "revision_id": revision.revision_id,
                    "extraction_id": dep.extraction_id,
                    "order": index,
                    "anchor": anchor,
                    "block_kind": kind,
                    "text_sha256": digest,
                }
            )
            blocks.append(
                Block(
                    schema_version=1,
                    block_id=block_id,
                    revision_id=revision.revision_id,
                    extraction_id=dep.extraction_id,
                    order=index,
                    kind=kind,
                    anchor=anchor,
                    text=line,
                    text_sha256=digest,
                    origin="native",
                )
            )
        if time.monotonic() >= deadline:
            raise ValueError
        return ExtractionResult(revision, scope, dep, tuple(blocks))
    except (
        AdmissionError,
        ProvenanceError,
        ValidationError,
        ValueError,
        TypeError,
        AttributeError,
        UnicodeError,
        OverflowError,
    ):
        raise ExtractionError("extraction refused") from None
