"""Bounded structural chunk construction over a validated provenance registry."""
from __future__ import annotations

import hashlib
import json
import re
import time
from dataclasses import dataclass
from typing import Callable

from . import provenance_records as p


class ChunkingError(ValueError):
    """Fixed, input-free refusal; no partial result is returned."""


@dataclass(frozen=True)
class Policy:
    target: int = 512
    soft_max: int = 768
    representation_max: int = 1024
    pair_max: int = 512
    query_reserve: int = 64
    max_blocks: int = 4096
    max_chars: int = 1000000
    max_chunks: int = 4096
    max_calls: int = 20000
    max_work_chars: int = 20000000
    deadline_ms: int = 5000

    def __post_init__(self):
        caps = (768, 768, 1024, 10000000, 10000000, 4096, 1000000, 4096,
                20000, 20000000, 15000)
        if any(type(v) is not int or not 1 <= v <= cap
               for v, cap in zip(self.__dict__.values(), caps)):
            raise ChunkingError('invalid policy')
        if self.target > self.soft_max or self.query_reserve >= self.pair_max:
            raise ChunkingError('invalid policy')


@dataclass(frozen=True)
class Counters:
    body_identity: str
    representation_identity: str
    pair_identity: str
    body: Callable[[str], int]
    representation: Callable[[str], int]
    pair: Callable[[str, str], int]
    provenance: str = 'SUPPLIED_UNVERIFIED'


@dataclass(frozen=True)
class Result:
    chunks: tuple[p.Chunk, ...]
    neighbors: tuple[p.Neighbors, ...]


def build(registry: p.Registry, blocks: tuple[p.Block, ...], counters: Counters,
          query: str, policy: Policy | None = None) -> Result:
    """Build all chunks or refuse. Callbacks are trusted and must cooperate with limits."""
    try:
        return _build(registry, blocks, counters, query, policy)
    except Exception:
        raise ChunkingError('chunk construction refused') from None


def _build(registry, blocks, counters, query, policy, reuse=False):
    if type(registry) is not p.Registry or type(blocks) is not tuple or not blocks:
        raise ValueError
    if type(counters) is not Counters or type(query) is not str or len(query) > 10000:
        raise ValueError
    query.encode('utf-8')
    if policy is not None and type(policy) is not Policy:
        raise ValueError
    policy = Policy() if policy is None else Policy(**policy.__dict__)
    if type(counters.provenance) is not str or counters.provenance != 'SUPPLIED_UNVERIFIED':
        raise ValueError
    identities = (counters.body_identity, counters.representation_identity, counters.pair_identity)
    if (any(type(x) is not str or not 1 <= len(x) <= 128 for x in identities)
            or identities[2] in identities[:2]
            or not all(callable(x) for x in
                       (counters.body, counters.representation, counters.pair))):
        raise ValueError
    if len(blocks) > policy.max_blocks or sum(len(b.text) for b in blocks) > policy.max_chars:
        raise ValueError
    key = (blocks[0].revision_id, blocks[0].extraction_id)
    if (any(type(b) is not p.Block or registry._blocks.get(b.block_id) != b for b in blocks)
            or len({b.block_id for b in blocks}) != len(blocks)
            or any((b.revision_id, b.extraction_id) != key for b in blocks)
            or any(a.order >= b.order for a, b in zip(blocks, blocks[1:]))
            or {b.block_id for b in blocks} != {b.block_id for b in registry._blocks.values()
                                                 if (b.revision_id, b.extraction_id) == key}):
        raise ValueError
    # Revalidate even unchecked Pydantic copies against the registry snapshot.
    for b in blocks:
        if p.Block.model_validate(b.model_dump(warnings=False)) != b:
            raise ValueError
    definition = json.dumps({'version': 2, 'policy': policy.__dict__, 'identities': identities,
                             'provenance': counters.provenance,
                             'query_sha256': hashlib.sha256(query.encode('utf-8')).hexdigest()},
                            sort_keys=True, ensure_ascii=True, separators=(',', ':'))
    pid = p.policy_id(definition)
    deadline = time.monotonic() + policy.deadline_ms / 1000
    calls = work = 0
    seen = {}
    measured = {}

    def count(fn, mode, *args):
        nonlocal calls, work
        calls += 1
        work += sum(len(x) for x in args)
        if calls > policy.max_calls or work > policy.max_work_chars or time.monotonic() >= deadline:
            raise ValueError
        value = fn(*args)
        if (type(value) is not int or not 0 <= value <= 10000000
                or time.monotonic() >= deadline):
            raise ValueError
        k = (mode, args)
        if k in seen and seen[k] != value:
            raise ValueError
        seen[k] = value
        return value

    def measure(fragments, headings):
        text = ''.join(f.copied_text if isinstance(f, p.SourceFragment) else f.text
                       for f in fragments)
        representation = ''.join(headings) + text
        key = (text, representation)
        if reuse and key in measured:
            if time.monotonic() >= deadline:
                raise ValueError
            return measured[key]
        body = count(counters.body, 'body', text)
        rep = count(counters.representation, 'representation', representation)
        pair = count(counters.pair, 'pair', query, representation)
        empty_pair = count(counters.pair, 'pair', '', representation)
        query_pair = count(counters.pair, 'pair', query, '')
        if (pair < empty_pair or pair < query_pair
                or query_pair > policy.query_reserve):
            raise ValueError
        result = (text, (body, rep, pair), (body <= policy.soft_max
                  and rep <= policy.representation_max and pair <= policy.pair_max))
        if reuse:
            measured[key] = result
        return result

    def fragment(block, start, end):
        return p.SourceFragment(schema_version=1, kind='source', block_id=block.block_id,
                                start=start, end=end, copied_text=block.text[start:end])

    output = []
    pending = []
    headings = []
    pending_headings = ()
    pending_result = None
    table_header = None

    def flush():
        nonlocal pending, pending_result
        if not pending:
            return
        text, counts, fits = pending_result if reuse else measure(pending, pending_headings)
        if not fits or len(pending) > 256 or len(output) >= policy.max_chunks:
            raise ValueError
        chunk = p.Chunk(schema_version=1, chunk_id='pending', revision_id=key[0],
                        extraction_id=key[1], policy_id=pid, fragments=tuple(pending), text=text,
                        text_sha256=hashlib.sha256(text.encode()).hexdigest(),
                        heading_path=pending_headings,
                        counts=tuple(p.TokenCount(schema_version=1, availability='available',
                                     count=n, provenance=f'{counters.provenance}:{identity}')
                                     for n, identity in zip(counts, identities)))
        chunk = chunk.model_copy(update={'chunk_id': p.chunk_id(chunk)})
        registry.bind_chunk(chunk)
        output.append(chunk)
        pending = []
        pending_result = None

    def append_unit(unit, path, unit_result=None):
        nonlocal pending, pending_headings, pending_result
        if pending and pending_headings != path:
            flush()
        candidate = None
        if pending:
            candidate = measure(pending + unit, path)
            if not candidate[2] or candidate[1][0] > policy.target:
                flush()
                candidate = None
        if not pending:
            pending_headings = path
            candidate = unit_result if reuse and unit_result else measure(unit, path)
        if not reuse and pending:
            candidate = measure(pending + unit, path)
        if not candidate[2]:
            raise ValueError
        pending += unit
        pending_result = candidate

    # Adjacent warning/prerequisite and numbered procedure, with at most one
    # literal blank block between them. Never bridge unrelated content.
    def warning(b):
        return b.kind in ('text', 'list') and bool(re.search(
            r'(?i)\b(warning|caution|danger|prerequisite|prerequisites)\b', b.text))

    def procedure(b):
        return b.kind == 'list' and bool(re.match(r'\s*\d+[.)]\s', b.text))

    # Maximal adjacent runs keep multiple warnings/prerequisites with a procedure.
    # One literal blank block may separate consecutive recognized units.
    grouped = {}
    pairs = {}
    i = 0
    while i < len(blocks):
        if not (warning(blocks[i]) or procedure(blocks[i])):
            i += 1
            continue
        run = [i]
        j = i
        while True:
            nxt = j + 1
            if nxt < len(blocks) and blocks[nxt].kind == 'text' and not blocks[nxt].text.strip():
                nxt += 1
            if nxt >= len(blocks) or not (warning(blocks[nxt]) or procedure(blocks[nxt])):
                break
            run.append(nxt)
            j = nxt
        if any(warning(blocks[k]) for k in run) and any(procedure(blocks[k]) for k in run):
            grouped[run[0]] = run[-1]
            # If the entire run cannot fit, preserve a fitting adjacent pair.
            for left, right in zip(run, run[1:]):
                if ((warning(blocks[left]) and procedure(blocks[right]))
                        or (procedure(blocks[left]) and warning(blocks[right]))):
                    pairs[left] = right
        i = j + 1

    skip_until = -1
    for index, block in enumerate(blocks):
        if index <= skip_until:
            continue
        if not block.text:
            continue
        if block.kind == 'heading':
            flush()
            match = re.match(r'^ {0,3}(#{1,6})[ \t]', block.text)
            level = len(match.group(1)) if match else 1
            headings[:] = headings[:level - 1]
            headings.append(block.text)
        path = tuple(headings)
        if block.kind == 'table_header':
            flush()
            table_header = fragment(block, 0, len(block.text))
        elif block.kind != 'table_row':
            table_header = None
        unit = [fragment(block, 0, len(block.text))]
        if index in grouped or index in pairs:
            end_index = grouped.get(index, pairs.get(index))
            group = [fragment(b, 0, len(b.text)) for b in blocks[index:end_index + 1]
                     if b.text]
            group_result = measure(group, path)
            group_fits = group_result[2]
            if not group_fits and index in pairs and pairs[index] != end_index:
                end_index = pairs[index]
                group = [fragment(b, 0, len(b.text)) for b in blocks[index:end_index + 1]
                         if b.text]
                group_result = measure(group, path)
            group_fits = group_result[2]
            if group_fits:
                # Give the local relationship priority over the target, but not
                # over any hard limit or unrelated preceding material.
                flush()
                pending_headings = path
                pending = group
                pending_result = group_result
                skip_until = end_index
                continue
        if block.kind == 'table_row' and not pending and table_header is not None:
            unit.insert(0, table_header)
        unit_result = measure(unit, path)
        if unit_result[2]:
            if block.kind == 'table_row' and pending:
                candidate = measure(pending + unit, path)
                if not candidate[2] or candidate[1][0] > policy.target:
                    flush()
                    if table_header is not None:
                        unit.insert(0, table_header)
                        if reuse:
                            unit_result = measure(unit, path)
                elif reuse:
                    pending += unit
                    pending_result = candidate
                    continue
            append_unit(unit, path, unit_result)
            continue
        if block.kind != 'text':
            raise ValueError
        # Only sentence boundaries are safe split candidates; never slice an indivisible sentence.
        flush()
        starts = [0] + [m.end() for m in re.finditer(r'(?<=[.!?])\s+', block.text)]
        starts = sorted(set(starts + [len(block.text)]))
        previous = None
        for start, end in zip(starts, starts[1:]):
            if start == end:
                continue
            current = fragment(block, start, end)
            if pending:
                candidate = measure(pending + [current], path)
                if not candidate[2] or candidate[1][0] > policy.target:
                    flush()
                    # Repeat only the immediately preceding sentence within the
                    # same split paragraph, if the actual body counter permits.
                    if previous is not None:
                        # Try longest word-boundary suffix first. Offsets remain
                        # original source offsets, even when only a suffix fits.
                        offsets = [previous.start] + [
                            previous.start + m.end()
                            for m in re.finditer(r'\s+', previous.copied_text)
                            if m.end() < len(previous.copied_text)]
                        for offset in offsets:
                            overlap = fragment(block, offset, previous.end)
                            overlap_count = count(counters.body, 'body', overlap.copied_text)
                            overlap_result = measure([overlap, current], path)
                            if overlap_count <= 64 and overlap_result[2]:
                                pending_headings = path
                                pending = [overlap, current]
                                pending_result = overlap_result
                                break
                        if pending:
                            previous = current
                            continue
                elif reuse:
                    pending += [current]
                    pending_result = candidate
                    previous = current
                    continue
            append_unit([current], path)
            previous = current
    flush()
    if not output:
        raise ValueError
    # Coverage is a union: repeated table headers and overlap are deliberate.
    covered = {b.block_id: [] for b in blocks}
    for chunk in output:
        for f in chunk.fragments:
            if isinstance(f, p.SourceFragment):
                covered[f.block_id].append((f.start, f.end))
    for b in blocks:
        end = 0
        for start, stop in sorted(covered[b.block_id]):
            if start > end:
                raise ValueError
            end = max(end, stop)
        if end != len(b.text):
            raise ValueError
    chunks = tuple(output)
    links = tuple(p.Neighbors(schema_version=1, chunk_id=c.chunk_id,
                              previous_chunk_id=chunks[i - 1].chunk_id if i else None,
                              next_chunk_id=chunks[i + 1].chunk_id if i + 1 < len(chunks) else None)
                  for i, c in enumerate(chunks))
    registry.bind_neighbors(chunks, links)
    return Result(chunks, links)
