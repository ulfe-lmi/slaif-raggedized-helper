"""Private, ephemeral original-source bindings for a supplied ranking."""

from dataclasses import asdict, dataclass, field
import hashlib
import json
import re
import time
import unicodedata

from . import derived_store, ingestion_store, provenance_records as p
from . import raw_snapshot_catalog, raw_snapshot_rows
from .source_admission import OriginalStore, Revision


class SourceBindingError(Exception):
    """Content-free refusal of a source binding."""


@dataclass(frozen=True, slots=True, repr=False)
class BoundFragment:
    block_id: str
    start: int
    end: int
    text_sha256: str


@dataclass(frozen=True, slots=True, repr=False)
class BoundRow:
    ordinal: int
    partition_id: str
    chunk_id: str
    revision_id: str
    extraction_id: str
    representation_id: str
    bundle_container_id: str
    batch_container_id: str
    scope_sha256: str
    fragments: tuple[BoundFragment, ...]


@dataclass(frozen=True, slots=True, repr=False)
class BoundRanking:
    binding_id: str
    snapshot_id: str
    catalog_id: str
    authority_sha256: str
    rows: tuple[BoundRow, ...]
    row_count: int
    fragment_count: int
    source_binding_status: str
    input_origin: str = field(default="SUPPLIED_RANKING_UNVERIFIED", init=False)
    authorization_status: str = field(default="SUPPLIED_SCOPE_CHECKS_ONLY", init=False)
    execution_status: str = field(default="NOT_ATTESTED", init=False)
    qualification: str = field(default="NOT_QUALIFIED", init=False)


def _check(value):
    if not value:
        raise ValueError


def _json(value):
    return json.dumps(
        value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


def _hash(data):
    return hashlib.sha256(data).hexdigest()


def _timed_hash(data, check):
    check()
    result = _hash(data)
    check()
    return result


def _authority(value, cls, fields, optional, budget, check):
    check()
    if value is None:
        return None
    _check(
        type(value) is cls
        and type(value.__dict__) is dict
        and len(value.__dict__) == len(fields) + 1
        and "schema_version" in value.__dict__
        and all(name in value.__dict__ for name in fields)
        and not value.__pydantic_extra__
        and type(value.schema_version) is int
        and value.schema_version == 1
    )
    for name in fields:
        check()
        items = value.__dict__[name]
        if items is None:
            _check(optional)
            continue
        _check(type(items) is tuple and len(items) <= 128)
        for item in items:
            check()
            _check(type(item) is str)
            budget[0] += len(item)
            _check(budget[0] <= 65536)
            item.encode("utf-8")
    clone = p._snapshot(value, cls)
    check()
    return clone


class _PassBudget:
    """Count selected occurrences, including repeated content, for one pass."""

    __slots__ = ("blocks", "bundle_bytes", "fragments", "copied_bytes", "block_id_bytes")

    def __init__(self):
        self.blocks = self.bundle_bytes = self.fragments = self.copied_bytes = 0
        self.block_id_bytes = 0

    def bundle(self, blocks, size):
        self.blocks += blocks
        self.bundle_bytes += size
        _check(self.blocks <= 4096 and self.bundle_bytes <= 100663296)

    def member(self, size):
        self.bundle_bytes += size
        _check(self.bundle_bytes <= 100663296)

    def fragment(self, copied, block_id):
        self.fragments += 1
        self.copied_bytes += copied
        self.block_id_bytes += block_id
        _check(
            self.fragments <= 65536
            and self.copied_bytes <= 16777216
            and self.block_id_bytes <= 2097152
        )


def _binding_hash(obj, check, limit=16777216):
    digest = hashlib.sha256(b"slaif-source-bound-supplied-ranking-v1\n")
    size = 0
    encoder = json.JSONEncoder(
        sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False
    )
    for piece in encoder.iterencode(obj):
        check()
        data = piece.encode("ascii")
        size += len(data)
        _check(size <= limit)
        digest.update(data)
        check()
    return "sha256:" + digest.hexdigest()


def _pass(catalog, originals, derived, ids, grants, restrictions, check):
    check()
    mapping = raw_snapshot_rows.parse(catalog.row_map_bytes)
    check()
    _check(len(mapping.rows) == len(catalog.rows))
    lookup = {}
    for i, (declaration, row) in enumerate(zip(mapping.rows, catalog.rows)):
        check()
        _check(
            declaration.ordinal == i
            and row.declaration_bytes == _json(asdict(declaration))
            and row.representation_id == declaration.representation_id
            and declaration.chunk_id not in lookup
        )
        lookup[declaration.chunk_id] = (declaration, row)
    for ident in ids:
        check()
        _check(ident in lookup)
    groups = {}
    for ident in ids:
        check()
        declaration, row = lookup[ident]
        groups.setdefault(declaration.bundle_container_id, []).append((declaration, row))
    _check(len(groups) <= 128)
    if not ids:
        return (), ()
    check()

    def admit_all(values, fn):
        result = []
        for value in values:
            check()
            result.append(fn(value))
            check()
        return tuple(result)

    revisions = admit_all(catalog.revisions, Revision.model_validate_json)
    dependencies = admit_all(catalog.dependencies, lambda x: p.admit_record("Dependency", x))
    blocks = admit_all(catalog.blocks, lambda x: p.admit_record("Block", x))
    check()
    registry = p.Registry(revisions, dependencies, blocks)
    check()
    revision_bytes, dependency_bytes, block_bytes = (
        set(catalog.revisions),
        set(catalog.dependencies),
        set(catalog.blocks),
    )
    output, observations = {}, []
    budget = _PassBudget()
    for bundle_id in sorted(groups):
        check()
        bundle = ingestion_store.load(originals, derived, bundle_id)
        check()
        budget.bundle(len(bundle.blocks), len(bundle.metadata_json))
        members = []
        for name, data in bundle.members:
            check()
            budget.member(len(data))
            members.append((name, len(data), _timed_hash(data, check)))
            check()
        metadata_hash = _timed_hash(bundle.metadata_json, check)
        observations.append(
            (
                bundle_id,
                bundle.adapter,
                bundle.status,
                bundle.coverage_kind,
                len(bundle.metadata_json),
                metadata_hash,
                tuple(members),
            )
        )
        _check(
            (bundle.adapter, bundle.status, bundle.coverage_kind)
            == ("structured_text", "complete_text", "unicode_codepoints")
            and bundle.revision.source.media_type in ("text/plain", "text/markdown")
            and _json(bundle.revision.model_dump(mode="json")) in revision_bytes
            and _json(bundle.dependency.model_dump(mode="json")) in dependency_bytes
        )
        block_map = {}
        for block in bundle.blocks:
            check()
            _check(
                block.kind != "visual"
                and block.origin == "native"
                and _json(block.model_dump(mode="json")) in block_bytes
                and block.block_id not in block_map
            )
            block_map[block.block_id] = block
        chunks = {}
        for chunk in bundle.chunks:
            check()
            _check(chunk.chunk_id not in chunks)
            chunks[chunk.chunk_id] = chunk
        for decl, row in groups[bundle_id]:
            check()
            _check(
                decl.bundle_metadata_sha256 == metadata_hash
                and decl.revision_id == bundle.revision.revision_id
                and decl.extraction_id == bundle.dependency.extraction_id
            )
            chunk = chunks[decl.chunk_id]
            _check(
                chunk.revision_id == decl.revision_id
                and chunk.extraction_id == decl.extraction_id
                and _json(chunk.model_dump(mode="json")) == row.chunk_bytes
                and _json(bundle.revision.source.model_dump(mode="json")) == row.source_bytes
            )
            check()
            scope = registry.bind_chunk(chunk)
            check()
            _check(
                scope == bundle.scope and _json(scope.model_dump(mode="json")) == row.scope_bytes
            )
            _check(p.reader_allows(scope, grants, restrictions))
            check()
            fragments = []
            for fragment in chunk.fragments:
                check()
                if type(fragment) is p.Separator:
                    continue
                _check(type(fragment) is p.SourceFragment)
                block = block_map[fragment.block_id]
                _check(
                    0 <= fragment.start < fragment.end <= len(block.text) <= 200000
                    and block.text[fragment.start : fragment.end] == fragment.copied_text
                )
                data = fragment.copied_text.encode("utf-8")
                budget.fragment(len(data), len(fragment.block_id.encode("utf-8")))
                fragments.append(
                    BoundFragment(
                        fragment.block_id, fragment.start, fragment.end, _timed_hash(data, check)
                    )
                )
                check()
            _check(fragments)
            output[decl.chunk_id] = BoundRow(
                decl.ordinal,
                decl.partition_id,
                decl.chunk_id,
                decl.revision_id,
                decl.extraction_id,
                decl.representation_id,
                decl.bundle_container_id,
                decl.batch_container_id,
                _timed_hash(row.scope_bytes, check),
                tuple(fragments),
            )
            check()
        del bundle, chunks, block_map, members, data, chunk, block, fragment, scope
    return tuple(output[x] for x in ids), tuple(observations)


def bind(
    originals,
    derived,
    store_root,
    snapshot_id,
    expected_catalog_id,
    chunk_ids,
    *,
    grants,
    restrictions=None,
    deadline_ms=30000,
):
    """Bind ordered supplied IDs to revalidated originals, without attesting a query."""
    try:
        start = time.monotonic()
        _check(type(deadline_ms) is int and 1 <= deadline_ms <= 30000)
        end = start + deadline_ms / 1000

        def check():
            _check(time.monotonic() < end)

        def remaining():
            check()
            value = int((end - time.monotonic()) * 1000)
            _check(value >= 1)
            return value

        check()
        _check(type(originals) is OriginalStore and type(derived) is derived_store.Store)
        _check(
            type(store_root) is str
            and store_root.startswith("/")
            and store_root != "/"
            and len(store_root.encode("utf-8")) <= 4096
            and all(unicodedata.category(c) != "Cc" for c in store_root)
            and all(x not in ("", ".", "..") for x in store_root[1:].split("/"))
        )
        for ident in (snapshot_id, expected_catalog_id):
            _check(type(ident) is str and re.fullmatch(r"sha256:[0-9a-f]{64}", ident))
        _check(type(chunk_ids) is tuple and len(chunk_ids) <= 4096)
        seen = set()
        for ident in chunk_ids:
            check()
            _check(
                type(ident) is str
                and re.fullmatch(r"sha256:[0-9a-f]{64}", ident)
                and ident not in seen
            )
            seen.add(ident)
        budget = [0]
        grants = _authority(
            grants, p.Grants, ("corpora", "versions", "labels"), False, budget, check
        )
        restrictions = _authority(
            restrictions, p.Restrictions, ("corpora", "versions"), True, budget, check
        )
        pair = [
            x.model_dump(mode="json") if x is not None else None for x in (grants, restrictions)
        ]
        encoded = _json(pair)
        _check(len(encoded) <= 262144)
        authority_hash = _timed_hash(encoded, check)
        check()
        first = raw_snapshot_catalog.load_catalog(
            originals, derived, store_root, snapshot_id, deadline_ms=remaining()
        )
        check()
        _check(first.snapshot_id == snapshot_id and first.catalog_id == expected_catalog_id)
        rows, observations = _pass(
            first, originals, derived, chunk_ids, grants, restrictions, check
        )
        check()
        second = raw_snapshot_catalog.load_catalog(
            originals, derived, store_root, snapshot_id, deadline_ms=remaining()
        )
        check()
        _check(
            first == second
            and second.snapshot_id == snapshot_id
            and second.catalog_id == expected_catalog_id
        )
        rows2, observations2 = _pass(
            second, originals, derived, chunk_ids, grants, restrictions, check
        )
        _check(rows == rows2 and observations == observations2)
        check()
        count = 0
        serial_rows = []
        for row in rows:
            check()
            count += len(row.fragments)
            serial_rows.append(asdict(row))
            check()
        status = "ORIGINALS_REVALIDATED_AT_BIND_TIME" if rows else "NO_SELECTED_SOURCE_VALIDATED"
        obj = dict(
            schema=1,
            kind="slaif-source-bound-supplied-ranking-v1",
            snapshot_id=snapshot_id,
            catalog_id=expected_catalog_id,
            authority_sha256=authority_hash,
            rows=serial_rows,
            row_count=len(rows),
            fragment_count=count,
            source_binding_status=status,
        )
        binding_id = _binding_hash(obj, check)
        check()
        result = BoundRanking(
            binding_id,
            snapshot_id,
            expected_catalog_id,
            authority_hash,
            rows,
            len(rows),
            count,
            status,
        )
        check()
        return result
    except Exception:
        raise SourceBindingError("source bound ranking refused") from None
