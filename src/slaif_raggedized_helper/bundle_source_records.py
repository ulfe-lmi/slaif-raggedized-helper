"""Source-bound validation of structured text bundle records."""

from dataclasses import asdict, dataclass, fields
import hashlib
import json
import re
import time

from . import bundle_native_records as bounded
from . import provenance_jsonl as jl, provenance_records as p, structured_text as st
from .source_admission import OriginalStore, Revision

HEADER_BYTES = 65536
COVERAGE_BYTES = 2 * 1024 * 1024


class BundleSourceError(ValueError):
    """Input-free refusal of the complete source boundary."""


@dataclass(frozen=True)
class Validated:
    revision: Revision
    scope: p.Scope
    dependency: p.Dependency
    blocks: tuple[p.Block, ...]
    coverage: tuple[st.Coverage, ...]
    header_json: bytes
    blocks_jsonl: bytes
    coverage_json: bytes


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
    """Re-extract bounded original text and bind every supplied record to that result."""
    start = time.monotonic()

    def check():
        if time.monotonic() - start >= 30:
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
            or not 1 <= expected_blocks <= 4096
        ):
            raise ValueError
        check()
        header = bounded._parse(extraction_header_json_bytes, 10000)
        bounded._fields(header, ("dependency", "adapter", "status", "coverage_kind", "uncertainty"))
        if (
            header["adapter"] != "structured_text"
            or header["status"] != "complete_text"
            or header["coverage_kind"] != "unicode_codepoints"
            or type(header["uncertainty"]) is not str
            or not 1 <= len(header["uncertainty"]) <= 1024
        ):
            raise ValueError
        dep = p.admit_record("Dependency", header["dependency"])
        if dep.revision_id != revision_id or dep.extraction_id != p.extraction_id(dep.definition):
            raise ValueError
        definition = bounded._parse(dep.definition.encode("utf-8"), 100)
        policy_fields = tuple(f.name for f in fields(st.StructurePolicy))
        bounded._fields(definition, ("adapter", "version", *policy_fields, "work_seconds"))
        if (
            definition["adapter"] != "native-structured-text"
            or type(definition["version"]) is not int
            or definition["version"] != 1
            or type(definition["work_seconds"]) is not float
            or definition["work_seconds"] != st.MAX_SECONDS
        ):
            raise ValueError
        policy = st.StructurePolicy(**{name: definition[name] for name in policy_fields})
        if dep.definition != policy.definition:
            raise ValueError
        check()
        blocks = jl.decode(
            "Block",
            blocks_jsonl_bytes,
            hashlib.sha256(blocks_jsonl_bytes).hexdigest(),
            expected_blocks,
        )
        check()
        doc = bounded._parse(coverage_json_bytes, 50000)
        bounded._fields(doc, ("schema_version", "kind", "spans"))
        if (
            type(doc["schema_version"]) is not int
            or doc["schema_version"] != 1
            or doc["kind"] != "unicode_codepoints"
            or type(doc["spans"]) is not list
            or len(doc["spans"]) != expected_blocks
        ):
            raise ValueError
        spans = []
        for item in doc["spans"]:
            check()
            bounded._fields(item, ("block_id", "start", "end"))
            if (
                type(item["block_id"]) is not str
                or not 1 <= len(item["block_id"]) <= 256
                or type(item["start"]) is not int
                or type(item["end"]) is not int
                or not 0 <= item["start"] < item["end"] <= st.MAX_CHARS
            ):
                raise ValueError
            spans.append(st.Coverage(**item))
        check()
        actual = st.extract(store, revision_id, policy)
        check()
        if (
            not actual.blocks
            or blocks != actual.blocks
            or tuple(spans) != actual.coverage
            or dep != actual.dependency
            or header["uncertainty"] != actual.uncertainty
        ):
            raise ValueError
        canonical_header = _canonical(header)
        canonical_blocks = jl.encode("Block", tuple(b.model_dump_json().encode() for b in blocks))
        canonical_coverage = _canonical(
            {
                "schema_version": 1,
                "kind": "unicode_codepoints",
                "spans": [asdict(span) for span in spans],
            }
        )
        if (
            len(canonical_header) > HEADER_BYTES
            or len(canonical_blocks) > jl.MAX_BYTES
            or len(canonical_coverage) > COVERAGE_BYTES
        ):
            raise ValueError
        check()
        return Validated(
            actual.revision,
            actual.scope,
            dep,
            blocks,
            tuple(spans),
            canonical_header,
            canonical_blocks,
            canonical_coverage,
        )
    except Exception:
        raise BundleSourceError("source bundle records refused") from None
