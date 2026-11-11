"""Validate stored PDF producer records without executing a PDF parser."""

from dataclasses import dataclass, fields
import hashlib
import json
import math
import re
import time

from . import provenance_jsonl as jl, provenance_records as p
from .pdf_extraction import PdfPolicy, PdfResult
from .schema import fingerprint
from .source_admission import OriginalStore

HEADER_BYTES = 65536
COVERAGE_BYTES = 2 * 1024 * 1024
MAX_NODES = 20000
MAX_DEPTH = 16
MAX_SECONDS = 30


class PdfRecordsError(ValueError):
    """Input-free refusal of the complete source record set."""


@dataclass(frozen=True)
class Validated:
    revision: object
    scope: p.Scope
    dependency: p.Dependency
    blocks: tuple[p.Block, ...]
    pages: tuple[tuple[int, str], ...]
    status: str
    header_json: bytes
    blocks_jsonl: bytes
    coverage_json: bytes


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError
        result[key] = value
    return result


def _parse(raw):
    value = json.loads(
        raw.decode("utf-8"),
        object_pairs_hook=_unique,
        parse_constant=lambda _: (_ for _ in ()).throw(ValueError()),
    )
    stack = [(value, 0)]
    nodes = 0
    while stack:
        item, depth = stack.pop()
        nodes += 1
        if nodes > MAX_NODES or depth > MAX_DEPTH:
            raise ValueError
        if type(item) is dict:
            if len(item) > MAX_NODES:
                raise ValueError
            stack.extend((v, depth + 1) for pair in item.items() for v in pair)
        elif type(item) is list:
            if len(item) > MAX_NODES:
                raise ValueError
            stack.extend((v, depth + 1) for v in item)
        elif type(item) is str:
            item.encode("utf-8")
        elif type(item) is float:
            if not math.isfinite(item):
                raise ValueError
        elif type(item) is int:
            if item.bit_length() > 430:
                raise ValueError
        elif item is not None and type(item) is not bool:
            raise ValueError
    return value


def _fields(value, names):
    if type(value) is not dict or set(value) != set(names):
        raise ValueError


def _canonical(value):
    return json.dumps(
        value, sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(",", ":")
    ).encode("utf-8")


def validate(
    store,
    revision_id,
    extraction_header_json_bytes,
    blocks_jsonl_bytes,
    coverage_json_bytes,
    expected_blocks,
):
    """Revalidate stored bytes and their verified original; no PDF extraction is performed."""
    started = time.monotonic()

    def check():
        if time.monotonic() - started >= MAX_SECONDS:
            raise ValueError

    try:
        if (
            type(store) is not OriginalStore
            or type(revision_id) is not str
            or re.fullmatch(r"sha256:[0-9a-f]{64}", revision_id) is None
            or any(
                type(x) is not bytes
                for x in (extraction_header_json_bytes, blocks_jsonl_bytes, coverage_json_bytes)
            )
            or len(extraction_header_json_bytes) > HEADER_BYTES
            or len(blocks_jsonl_bytes) > jl.MAX_BYTES
            or len(coverage_json_bytes) > COVERAGE_BYTES
            or type(expected_blocks) is not int
            or not 0 <= expected_blocks <= 4096
        ):
            raise ValueError
        check()
        # Check framing and per-record caps before any parsing, hashing, or store access.
        offsets = []
        pos = 0
        while pos < len(blocks_jsonl_bytes):
            check()
            end = blocks_jsonl_bytes.find(b"\n", pos, pos + p.MAX_ADMISSION_BYTES + 1)
            if end <= pos or b"\r" in blocks_jsonl_bytes[pos:end]:
                raise ValueError
            offsets.append((pos, end))
            if len(offsets) > expected_blocks:
                raise ValueError
            pos = end + 1
        if len(offsets) != expected_blocks:
            raise ValueError
        header = _parse(extraction_header_json_bytes)
        _fields(header, ("dependency", "adapter", "status", "coverage_kind", "uncertainty"))
        if (
            header["adapter"] != "pdf_extraction"
            or header["coverage_kind"] != "pdf_pages"
            or header["status"] not in ("native_text", "partial_visual_needed")
            or header["uncertainty"] != PdfResult.__dataclass_fields__["uncertainty"].default
        ):
            raise ValueError
        _fields(
            header["dependency"], ("schema_version", "revision_id", "extraction_id", "definition")
        )
        dep = p.admit_record("Dependency", _canonical(header["dependency"]))
        if dep.revision_id != revision_id or dep.extraction_id != p.extraction_id(dep.definition):
            raise ValueError
        definition = _parse(dep.definition.encode("utf-8"))
        policy_names = tuple(f.name for f in fields(PdfPolicy))
        _fields(definition, (*policy_names, "adapter", "version", "geometry", "isolation"))
        policy = PdfPolicy(**{name: definition[name] for name in policy_names})
        if dep.definition != policy.definition:
            raise ValueError
        check()
        coverage = _parse(coverage_json_bytes)
        _fields(coverage, ("schema_version", "kind", "pages"))
        pages = coverage["pages"]
        if (
            type(coverage["schema_version"]) is not int
            or coverage["schema_version"] != 1
            or coverage["kind"] != "pdf_pages"
            or type(pages) is not list
            or not 1 <= len(pages) <= policy.max_pages
        ):
            raise ValueError
        page_values = []
        for index, page in enumerate(pages, 1):
            _fields(page, ("page", "status"))
            if (
                type(page["page"]) is not int
                or page["page"] != index
                or page["status"] not in ("native_text", "visual_needed")
            ):
                raise ValueError
            page_values.append((index, page["status"]))
        status = (
            "partial_visual_needed"
            if any(s == "visual_needed" for _, s in page_values)
            else "native_text"
        )
        if header["status"] != status:
            raise ValueError
        check()
        # The generic DTO permits omitted optional fields; this leaf requires the full record.
        for start, end in offsets:
            check()
            _fields(_parse(blocks_jsonl_bytes[start:end]), p.Block.model_fields)
        blocks = jl.decode(
            "Block",
            blocks_jsonl_bytes,
            hashlib.sha256(blocks_jsonl_bytes).hexdigest(),
            expected_blocks,
        )
        check()
        revision, raw = store.read_verified(revision_id, max_bytes=policy.max_bytes)
        scope = p.catalog((revision,))[0]
        if revision.revision_id != revision_id or revision.source.media_type != "application/pdf":
            raise ValueError
        del raw
        counts = [0] * len(pages)
        last_page = chars = 0
        seen = set()
        for index, block in enumerate(blocks):
            check()
            match = re.fullmatch(r"page:([1-9][0-9]*)", block.page_ref or "")
            if match is None:
                raise ValueError
            page = int(match.group(1))
            geometry = block.geometry
            digest = hashlib.sha256(block.text.encode("utf-8")).hexdigest()
            chars += len(block.text)
            if (
                block.order != index
                or block.block_id in seen
                or block.revision_id != revision_id
                or block.extraction_id != dep.extraction_id
                or block.kind != "text"
                or block.origin != "native"
                or not block.text
                or chars > policy.max_chars
                or block.text_sha256 != digest
                or not last_page <= page <= len(pages)
                or block.anchor != block.page_ref
                or block.crop_ref is not None
                or block.uncertainty != "PDF native text and order are layout heuristic."
                or geometry is None
                or any(not math.isfinite(v) for v in geometry)
                or geometry[0] > geometry[2]
                or geometry[1] > geometry[3]
            ):
                raise ValueError
            expected_id = fingerprint(
                {
                    "kind": "pdf-native-block",
                    "version": 1,
                    "revision_id": revision_id,
                    "extraction_id": dep.extraction_id,
                    "order": index,
                    "page": page,
                    "text_sha256": digest,
                    "geometry": list(geometry),
                }
            )
            if block.block_id != expected_id:
                raise ValueError
            seen.add(block.block_id)
            counts[page - 1] += 1
            last_page = page
        if any(
            not count and status == "native_text" for count, (_, status) in zip(counts, page_values)
        ):
            raise ValueError
        p.Registry((revision,), (dep,), blocks)
        canonical_header = _canonical(header)
        canonical_coverage = _canonical(coverage)
        canonical_blocks = jl.encode("Block", tuple(b.model_dump_json().encode() for b in blocks))
        if (
            len(canonical_header) > HEADER_BYTES
            or len(canonical_coverage) > COVERAGE_BYTES
            or len(canonical_blocks) > jl.MAX_BYTES
        ):
            raise ValueError
        check()
        return Validated(
            revision,
            scope,
            dep,
            blocks,
            tuple(page_values),
            status,
            canonical_header,
            canonical_blocks,
            canonical_coverage,
        )
    except Exception:
        raise PdfRecordsError("pdf source records refused") from None
