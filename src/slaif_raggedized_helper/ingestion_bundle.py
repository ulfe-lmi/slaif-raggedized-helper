"""Bounded, source-bound validation of structured-text ingestion bundles."""

from dataclasses import dataclass
import hashlib
import json
import re
import time

from . import bundle_native_records as native, bundle_source_records as source
from . import provenance_jsonl as jl, provenance_records as p
from .source_admission import OriginalStore

METADATA_BYTES = 256 * 1024
TOTAL_BYTES = 96 * 1024 * 1024
NAMES = ("blocks", "coverage", "chunks", "neighbors", "receipts")
CAPS = (16 * 1024 * 1024, 2 * 1024 * 1024, 16 * 1024 * 1024,
        16 * 1024 * 1024, 8000000)


class BundleError(ValueError):
    """Input-free refusal of the entire bundle."""


@dataclass(frozen=True)
class Validated:
    revision: object
    scope: p.Scope
    dependency: p.Dependency
    blocks: tuple
    coverage: tuple
    policy: object
    chunks: tuple
    neighbors: tuple
    receipts: tuple
    metadata_json: bytes
    members: tuple


def _json(obj):
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, allow_nan=False,
                      separators=(",", ":")).encode("utf-8")


def validate(store, metadata_json_bytes, members):
    """Reverify immutable bundle bytes against the trusted original store."""
    start = time.monotonic()

    def check():
        if time.monotonic() - start >= 30:
            raise ValueError

    try:
        if (type(store) is not OriginalStore or type(metadata_json_bytes) is not bytes
                or len(metadata_json_bytes) > METADATA_BYTES or type(members) is not tuple
                or len(members) != 5):
            raise ValueError
        total = len(metadata_json_bytes)
        for i, member in enumerate(members):
            if (type(member) is not tuple or len(member) != 2 or type(member[0]) is not str
                    or member[0] != NAMES[i] or type(member[1]) is not bytes
                    or len(member[1]) > CAPS[i]):
                raise ValueError
            total += len(member[1])
        if total > TOTAL_BYTES:
            raise ValueError
        check()
        metadata = native._parse(metadata_json_bytes, 20000)
        native._fields(metadata, ("schema_version", "kind", "revision_id", "extraction",
                                  "chunking", "counts"))
        if (type(metadata['schema_version']) is not int or metadata['schema_version'] != 1
                or metadata['kind'] != 'native-ingestion-bundle'):
            raise ValueError
        counts = metadata['counts']
        native._fields(counts, ('blocks', 'chunks', 'neighbors', 'receipts'))
        if (any(type(v) is not int for v in counts.values())
                or not 1 <= counts['blocks'] <= 4096 or not 1 <= counts['chunks'] <= 4096
                or counts['neighbors'] != counts['chunks']
                or counts['receipts'] != 3 * counts['chunks']):
            raise ValueError
        extraction = _json(metadata['extraction'])
        chunking = _json(metadata['chunking'])
        if len(extraction) > source.HEADER_BYTES or len(chunking) > native.HEADER_BYTES:
            raise ValueError
        raw = tuple(item[1] for item in members)
        check()
        src = source.validate(store, metadata['revision_id'], extraction, raw[0], raw[1],
                              counts['blocks'])
        check()
        nat = native.validate(chunking, raw[2], raw[4], counts['chunks'])
        check()
        links = jl.decode('Neighbors', raw[3], hashlib.sha256(raw[3]).hexdigest(),
                          counts['neighbors'])
        registry = p.Registry((src.revision,), (src.dependency,), src.blocks)
        paths = {}
        headings = []
        for block in src.blocks:
            check()
            if block.kind == 'heading':
                match = re.match(r'^ {0,3}(#{1,6})[ \t]', block.text)
                level = len(match.group(1)) if match else 1
                headings[:] = headings[:level - 1]
                headings.append(block.text)
            paths[block.block_id] = tuple(headings)
        positions = {b.block_id: i for i, b in enumerate(src.blocks)}
        progress = [0] * len(src.blocks)
        current = 0
        fragments = 0
        for chunk in nat.chunks:
            check()
            if (chunk.revision_id != src.revision.revision_id
                    or chunk.extraction_id != src.dependency.extraction_id):
                raise ValueError
            registry.bind_chunk(chunk)
            for fragment in chunk.fragments:
                fragments += 1
                if fragments > 1048576:
                    raise ValueError
                if isinstance(fragment, p.SourceFragment):
                    i = positions[fragment.block_id]
                    if chunk.heading_path != paths[fragment.block_id]:
                        raise ValueError
                    if fragment.end > progress[i]:
                        if i != current or fragment.start > progress[i]:
                            raise ValueError
                        progress[i] = fragment.end
                        if progress[i] == len(src.blocks[i].text):
                            current += 1
        if current != len(src.blocks):
            raise ValueError
        registry.bind_neighbors(nat.chunks, links)
        for i, link in enumerate(links):
            check()
            if (link.chunk_id != nat.chunks[i].chunk_id
                    or link.previous_chunk_id != (nat.chunks[i-1].chunk_id if i else None)
                    or link.next_chunk_id != (nat.chunks[i+1].chunk_id
                                              if i+1 < len(links) else None)):
                raise ValueError
        metadata['extraction'] = native._parse(src.header_json, 10000)
        metadata['chunking'] = native._parse(nat.header_json, 10000)
        canonical = _json(metadata)
        canonical_links = jl.encode('Neighbors', tuple(x.model_dump_json().encode() for x in links))
        result_members = tuple(zip(NAMES, (src.blocks_jsonl, src.coverage_json,
                                           nat.chunks_jsonl, canonical_links, nat.receipts_json)))
        if (len(canonical) > METADATA_BYTES
                or any(len(v) > cap for (_, v), cap in zip(result_members, CAPS))
                or len(canonical) + sum(len(v) for _, v in result_members) > TOTAL_BYTES):
            raise ValueError
        check()
        return Validated(src.revision, src.scope, src.dependency, src.blocks, src.coverage,
                         nat.policy, nat.chunks, links, nat.receipts, canonical, result_members)
    except Exception:
        raise BundleError('ingestion bundle refused') from None
