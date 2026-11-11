"""Bounded, literal native text/Markdown structural extraction."""
from __future__ import annotations

import hashlib
import json
import re
import time
from dataclasses import dataclass

from .provenance_records import Block, Dependency, Scope, catalog, extraction_id
from .schema import fingerprint
from .source_admission import OriginalStore, Revision

MAX_BYTES = 2_000_000
MAX_CHARS = 1_000_000
MAX_LINES = 100_000
MAX_BLOCKS = 4096
MAX_BLOCK_CHARS = 200_000
MAX_SECONDS = 5.0
_HEADING = re.compile(r'^ {0,3}#{1,6}(?:[ \t]|$)')
_LIST = re.compile(r'^ {0,3}(?:[-+*]|[0-9]{1,9}[.)])[ \t]+')
_FENCE = re.compile(r'^ {0,3}(`{3,}|~{3,})')
_CELL = re.compile(r'^:?-{3,}:?$')


class StructureError(ValueError):
    """Input-free failure without partial extraction."""


@dataclass(frozen=True)
class StructurePolicy:
    max_bytes: int = MAX_BYTES
    max_chars: int = MAX_CHARS
    max_lines: int = MAX_LINES
    max_blocks: int = MAX_BLOCKS
    max_block_chars: int = MAX_BLOCK_CHARS

    def __post_init__(self):
        for value, maximum in ((self.max_bytes, MAX_BYTES), (self.max_chars, MAX_CHARS),
                               (self.max_lines, MAX_LINES), (self.max_blocks, MAX_BLOCKS),
                               (self.max_block_chars, MAX_BLOCK_CHARS)):
            if type(value) is not int or not 1 <= value <= maximum:
                raise StructureError('invalid structure policy')

    @property
    def definition(self):
        return json.dumps({'adapter': 'native-structured-text', 'version': 1,
                           **self.__dict__, 'work_seconds': MAX_SECONDS},
                          sort_keys=True, separators=(',', ':'))


@dataclass(frozen=True)
class Coverage:
    block_id: str
    start: int
    end: int


@dataclass(frozen=True)
class StructureResult:
    revision: Revision
    scope: Scope
    dependency: Dependency
    blocks: tuple[Block, ...]
    coverage: tuple[Coverage, ...]
    uncertainty: str = ('Bounded structural subset; unsupported Markdown remains literal and '
                        'is not fully classified.')


def _cells(line: str) -> list[str]:
    stripped = line.strip()
    if '|' not in stripped:
        return []
    return [part.strip() for part in stripped.strip('|').split('|')]


def _table_start(lines: list[str], index: int) -> bool:
    if index + 1 >= len(lines):
        return False
    header, rule = _cells(lines[index]), _cells(lines[index + 1])
    return len(header) >= 2 and len(header) == len(rule) and all(_CELL.fullmatch(x) for x in rule)


def extract(store: OriginalStore, revision_id: str,
            policy: StructurePolicy | None = None) -> StructureResult:
    """Extract exact ordered units; coverage offsets index decoded Unicode code points."""
    try:
        if (type(store) is not OriginalStore
                or (policy is not None and type(policy) is not StructurePolicy)):
            raise ValueError
        policy = StructurePolicy() if policy is None else StructurePolicy(**policy.__dict__)
        deadline = time.monotonic() + MAX_SECONDS
        revision, raw = store.read_verified(revision_id, max_bytes=policy.max_bytes)
        scope = catalog((revision,))[0]
        if revision.source.media_type not in ('text/plain', 'text/markdown'):
            raise ValueError
        if time.monotonic() >= deadline:
            raise ValueError
        text = raw.decode('utf-8', errors='strict')
        if len(text) > policy.max_chars or time.monotonic() >= deadline:
            raise ValueError
        lines = text.splitlines(keepends=True)
        if len(lines) > policy.max_lines:
            raise ValueError
        markdown = revision.source.media_type == 'text/markdown'
        dep = Dependency(schema_version=1, revision_id=revision_id,
                         extraction_id=extraction_id(policy.definition),
                         definition=policy.definition)
        blocks: list[Block] = []
        coverage: list[Coverage] = []
        index = offset = 0
        section = 0
        while index < len(lines):
            if time.monotonic() >= deadline or len(blocks) >= policy.max_blocks:
                raise ValueError
            start_line = index
            first = lines[index]
            uncertainty = None
            marker = _FENCE.match(first) if markdown else None
            if not first.strip():
                kind = 'text'
                index += 1
                while index < len(lines) and not lines[index].strip():
                    index += 1
            elif marker:
                kind = 'code'
                char, width = marker.group(1)[0], len(marker.group(1))
                index += 1
                closed = False
                while index < len(lines):
                    closing = _FENCE.match(lines[index])
                    index += 1
                    if (closing and closing.group(1)[0] == char
                            and len(closing.group(1)) >= width
                            and not lines[index - 1][closing.end():].strip()):
                        closed = True
                        break
                if not closed:
                    uncertainty = 'Unclosed fence; remainder retained as literal code.'
            elif markdown and _HEADING.match(first):
                kind = 'heading'
                section = index + 1
                index += 1
            elif markdown and _table_start(lines, index):
                kind = 'table_header'
                index += 2  # original header and separator remain together
            elif _LIST.match(first):
                kind = 'list'
                index += 1
                while (index < len(lines) and lines[index].strip()
                       and (lines[index].startswith('  ') or lines[index].startswith('\t'))
                       and not _LIST.match(lines[index])):
                    index += 1
            elif (markdown and _cells(first) and blocks
                  and blocks[-1].kind in ('table_header', 'table_row')):
                kind = 'table_row'
                index += 1
            else:
                kind = 'text'
                index += 1
                while index < len(lines):
                    line = lines[index]
                    if (not line.strip() or _LIST.match(line)
                            or (markdown and (_HEADING.match(line) or _FENCE.match(line)
                                              or _table_start(lines, index)))):
                        break
                    index += 1
            unit = ''.join(lines[start_line:index])
            if len(unit) > policy.max_block_chars or time.monotonic() >= deadline:
                raise ValueError
            digest = hashlib.sha256(unit.encode('utf-8')).hexdigest()
            anchor = f'section:{section}/line:{start_line + 1}'
            block_id = fingerprint({'kind': 'structured-native-block', 'version': 1,
                                    'revision_id': revision_id, 'extraction_id': dep.extraction_id,
                                    'order': len(blocks), 'anchor': anchor, 'block_kind': kind,
                                    'text_sha256': digest})
            blocks.append(Block(schema_version=1, block_id=block_id, revision_id=revision_id,
                                extraction_id=dep.extraction_id, order=len(blocks), kind=kind,
                                anchor=anchor, text=unit, text_sha256=digest, origin='native',
                                uncertainty=uncertainty))
            coverage.append(Coverage(block_id, offset, offset + len(unit)))
            offset += len(unit)
        if offset != len(text) or time.monotonic() >= deadline:
            raise ValueError
        return StructureResult(revision, scope, dep, tuple(blocks), tuple(coverage))
    except StructureError:
        raise
    except Exception:
        raise StructureError('structure extraction refused') from None
