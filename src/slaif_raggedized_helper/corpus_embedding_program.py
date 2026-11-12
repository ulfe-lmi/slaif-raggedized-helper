"""Bounded, source-only declarations for complete selected ingestion bundles."""

from dataclasses import asdict, dataclass
import hashlib
import json
import re
import time

from . import ingestion_store, retrieval_representation as rr, schema


class ProgramError(ValueError):
    """Content-free refusal of a source program."""


@dataclass(frozen=True)
class ProgramPolicy:
    version: str = "embedding-source-program-policy-v1"
    max_bundles: int = 128
    max_rows: int = 65536
    max_batches: int = 65536
    max_program_bytes: int = 16777216
    deadline_ms: int = 120000


@dataclass(frozen=True)
class BatchSelection:
    batch_index: int
    bundle_id: str
    first_ordinal: int
    chunk_ids: tuple[str, ...]


@dataclass(frozen=True)
class SourceProgram:
    source_program_id: str
    program_bytes: bytes
    row_count: int
    batch_count: int
    batches: tuple[BatchSelection, ...]


def _encode(value):
    return json.dumps(
        value, sort_keys=True, ensure_ascii=True, allow_nan=False, separators=(",", ":")
    ).encode("ascii")


def _hex(value, prefix=""):
    return (
        type(value) is str and re.fullmatch(re.escape(prefix) + "[0-9a-f]{64}", value) is not None
    )


def _policies(policy, bp, pp):
    if (
        type(policy) is not rr.Policy
        or type(bp) is not rr.BatchPolicy
        or type(pp) is not ProgramPolicy
    ):
        raise ValueError
    # Copy exact values: frozen dataclasses can still be mutated with object.__setattr__.
    policy, bp, pp = (
        rr.Policy(**asdict(policy)),
        rr.BatchPolicy(**asdict(bp)),
        ProgramPolicy(**asdict(pp)),
    )
    if (
        type(policy.version) is not str
        or policy.version != "raw-v1"
        or type(policy.separator) is not str
        or policy.separator != "\n\n"
        or type(policy.max_tokens) is not int
        or not 1 <= policy.max_tokens <= 1024
        or type(policy.max_codepoints) is not int
        or policy.max_codepoints != 100000
        or type(policy.max_request_bytes) is not int
        or policy.max_request_bytes != 200000
        or type(bp.version) is not str
        or bp.version != "raw-batch-v1"
        or type(pp.version) is not str
        or pp.version != "embedding-source-program-policy-v1"
    ):
        raise ValueError
    for obj, bounds in (
        (
            bp,
            {"max_items": 128, "max_total_codepoints": 1000000, "max_total_request_bytes": 4000000},
        ),
        (
            pp,
            {
                "max_bundles": 128,
                "max_rows": 65536,
                "max_batches": 65536,
                "max_program_bytes": 16777216,
                "deadline_ms": 120000,
            },
        ),
    ):
        for key, limit in bounds.items():
            v = getattr(obj, key)
            if type(v) is not int or not 1 <= v <= limit:
                raise ValueError
    return policy, bp, pp


def _check(end):
    if time.monotonic() >= end:
        raise ValueError


def _view(data, doc):
    rows, sources = doc["rows"], doc["sources"]
    batches = tuple(
        BatchSelection(
            b["batch_index"],
            sources[b["source_index"]]["bundle_id"],
            b["first_ordinal"],
            tuple(
                r["chunk_id"]
                for r in rows[b["first_ordinal"] : b["first_ordinal"] + b["row_count"]]
            ),
        )
        for b in doc["batches"]
    )
    ident = hashlib.sha256(b"slaif-embedding-source-program-v1\n" + data).hexdigest()
    return SourceProgram("sha256:" + ident, data, len(rows), len(batches), batches)


def build(originals, derived, bundle_ids, *, policy=None, batch_policy=None, program_policy=None):
    """Revalidate every selected bundle and enumerate all of its actual chunks."""
    try:
        policy, bp, pp = _policies(
            policy if policy is not None else rr.Policy(),
            batch_policy if batch_policy is not None else rr.BatchPolicy(),
            program_policy if program_policy is not None else ProgramPolicy(),
        )
        end = time.monotonic() + pp.deadline_ms / 1000
        if (
            type(bundle_ids) is not tuple
            or not 1 <= len(bundle_ids) <= pp.max_bundles
            or any(not _hex(x) for x in bundle_ids)
            or tuple(sorted(set(bundle_ids))) != bundle_ids
        ):
            raise ValueError
        doc = dict(
            schema=1,
            kind="embedding-source-program-v1",
            token_eligibility="NOT_RUN",
            representation_policy=asdict(policy),
            batch_policy=asdict(bp),
            program_policy=asdict(pp),
            sources=[],
            rows=[],
            batches=[],
        )
        # Exact serialized accounting, including the current pending batch.
        used = len(_encode(doc))
        revisions, chunks_seen = set(), set()

        def retain(key, item):
            nonlocal used
            used += len(_encode(item)) + bool(doc[key])
            if used > pp.max_program_bytes:
                raise ValueError
            doc[key].append(item)

        for si, ident in enumerate(bundle_ids):
            _check(end)
            if len(doc["rows"]) >= pp.max_rows or len(doc["batches"]) >= pp.max_batches:
                raise ValueError
            # Lower bound only: no placeholder is treated as validated source data.
            ordinal = len(doc["rows"])
            zero = "0" * 64
            minimum = (
                (
                    "sources",
                    dict(
                        bundle_id=ident,
                        bundle_metadata_sha256=zero,
                        revision_id="sha256:" + zero,
                        extraction_id="sha256:" + zero,
                        source_scope_sha256=zero,
                        first_ordinal=ordinal,
                        row_count=1,
                    ),
                ),
                (
                    "rows",
                    dict(
                        ordinal=ordinal,
                        source_index=si,
                        chunk_id="sha256:" + zero,
                        rendered_sha256=zero,
                        codepoints=0,
                        native_request_bytes=1,
                    ),
                ),
                (
                    "batches",
                    dict(
                        batch_index=len(doc["batches"]),
                        source_index=si,
                        first_ordinal=ordinal,
                        row_count=1,
                        total_codepoints=0,
                        total_native_request_bytes=1,
                    ),
                ),
            )
            if (
                used + sum(len(_encode(item)) + bool(doc[key]) for key, item in minimum)
                > pp.max_program_bytes
            ):
                raise ValueError
            value = ingestion_store.load(originals, derived, ident)
            _check(end)
            if not value.chunks or len(value.chunks) > pp.max_rows - len(doc["rows"]):
                raise ValueError
            revision = value.revision.revision_id
            if revision in revisions:
                raise ValueError
            revisions.add(revision)
            ordered = sorted(value.chunks, key=lambda c: c.chunk_id)
            first = len(doc["rows"])
            scope = schema.fingerprint(
                {"kind": "embedding-source-scope-v1", "scope": value.scope.model_dump(mode="json")}
            )
            retain(
                "sources",
                dict(
                    bundle_id=ident,
                    bundle_metadata_sha256=hashlib.sha256(value.metadata_json).hexdigest(),
                    revision_id=revision,
                    extraction_id=ordered[0].extraction_id,
                    source_scope_sha256=scope[7:],
                    first_ordinal=first,
                    row_count=len(ordered),
                ),
            )
            current = None
            pending_size = 0
            for chunk in ordered:
                _check(end)
                if chunk.chunk_id in chunks_seen or chunk.extraction_id != ordered[0].extraction_id:
                    raise ValueError
                chunks_seen.add(chunk.chunk_id)
                text, wire = rr._format_raw(
                    value.revision.source.title, chunk.heading_path, chunk.text, policy
                )
                _check(end)
                chars = len(text)
                if chars > bp.max_total_codepoints or wire > bp.max_total_request_bytes:
                    raise ValueError
                if current is None or (
                    current["row_count"] == bp.max_items
                    or current["total_codepoints"] + chars > bp.max_total_codepoints
                    or current["total_native_request_bytes"] + wire > bp.max_total_request_bytes
                ):
                    if current is not None:
                        doc["batches"].append(current)
                        pending_size = 0
                    if len(doc["batches"]) >= pp.max_batches:
                        raise ValueError
                    current = dict(
                        batch_index=len(doc["batches"]),
                        source_index=si,
                        first_ordinal=len(doc["rows"]),
                        row_count=0,
                        total_codepoints=0,
                        total_native_request_bytes=0,
                    )
                current["row_count"] += 1
                current["total_codepoints"] += chars
                current["total_native_request_bytes"] += wire
                new_size = len(_encode(current)) + bool(doc["batches"])
                used += new_size - pending_size
                pending_size = new_size
                if used > pp.max_program_bytes:
                    raise ValueError
                retain(
                    "rows",
                    dict(
                        ordinal=len(doc["rows"]),
                        source_index=si,
                        chunk_id=chunk.chunk_id,
                        rendered_sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(),
                        codepoints=chars,
                        native_request_bytes=wire,
                    ),
                )
            doc["batches"].append(current)
            del value, ordered
        _check(end)
        data = _encode(doc)
        if len(data) > pp.max_program_bytes:
            raise ValueError
        _check(end)
        return _view(data, doc)
    except Exception:
        raise ProgramError("source program refused") from None


def _fields(obj, names):
    if type(obj) is not dict or set(obj) != set(names.split()):
        raise ValueError


def _integer(value, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ValueError


def _parse(data):
    if type(data) is not bytes or not 1 <= len(data) <= 16777216:
        raise ValueError
    started = time.monotonic()
    end = started + 120

    def pairs(items):
        result = {}
        for k, v in items:
            if k in result:
                raise ValueError
            result[k] = v
        return result

    doc = json.loads(
        data.decode("ascii"),
        object_pairs_hook=pairs,
        parse_constant=lambda _: (_ for _ in ()).throw(ValueError()),
    )
    _check(end)
    if _encode(doc) != data:
        raise ValueError
    _fields(
        doc,
        "schema kind token_eligibility representation_policy batch_policy "
        "program_policy sources rows batches",
    )
    if (
        type(doc["schema"]) is not int
        or doc["schema"] != 1
        or doc["kind"] != "embedding-source-program-v1"
        or doc["token_eligibility"] != "NOT_RUN"
    ):
        raise ValueError
    _fields(
        doc["representation_policy"],
        "max_tokens version separator max_codepoints max_request_bytes",
    )
    _fields(doc["batch_policy"], "version max_items max_total_codepoints max_total_request_bytes")
    _fields(
        doc["program_policy"],
        "version max_bundles max_rows max_batches max_program_bytes deadline_ms",
    )
    policy, bp, pp = _policies(
        rr.Policy(**doc["representation_policy"]),
        rr.BatchPolicy(**doc["batch_policy"]),
        ProgramPolicy(**doc["program_policy"]),
    )
    end = min(end, started + pp.deadline_ms / 1000)
    _check(end)
    sources, rows, batches = doc["sources"], doc["rows"], doc["batches"]
    if (
        len(data) > pp.max_program_bytes
        or type(sources) is not list
        or type(rows) is not list
        or type(batches) is not list
        or not 1 <= len(sources) <= pp.max_bundles
        or not 1 <= len(rows) <= pp.max_rows
        or not 1 <= len(batches) <= pp.max_batches
    ):
        raise ValueError
    revisions, ids, seen = set(), [], set()
    cursor = 0
    for si, source in enumerate(sources):
        _check(end)
        _fields(
            source,
            "bundle_id bundle_metadata_sha256 revision_id extraction_id "
            "source_scope_sha256 first_ordinal row_count",
        )
        if (
            not _hex(source["bundle_id"])
            or not _hex(source["bundle_metadata_sha256"])
            or not _hex(source["source_scope_sha256"])
            or not _hex(source["revision_id"], "sha256:")
            or not _hex(source["extraction_id"], "sha256:")
            or source["revision_id"] in revisions
        ):
            raise ValueError
        revisions.add(source["revision_id"])
        ids.append(source["bundle_id"])
        _integer(source["first_ordinal"], 0, len(rows))
        _integer(source["row_count"], 1, len(rows))
        if source["first_ordinal"] != cursor or cursor + source["row_count"] > len(rows):
            raise ValueError
        previous = ""
        for row in rows[cursor : cursor + source["row_count"]]:
            _check(end)
            _fields(
                row, "ordinal source_index chunk_id rendered_sha256 codepoints native_request_bytes"
            )
            _integer(row["ordinal"], 0, len(rows) - 1)
            _integer(row["source_index"], 0, len(sources) - 1)
            _integer(row["codepoints"], 0, policy.max_codepoints)
            _integer(row["native_request_bytes"], 1, policy.max_request_bytes)
            if (
                row["ordinal"] != cursor
                or row["source_index"] != si
                or not _hex(row["chunk_id"], "sha256:")
                or row["chunk_id"] <= previous
                or row["chunk_id"] in seen
                or not _hex(row["rendered_sha256"])
            ):
                raise ValueError
            previous = row["chunk_id"]
            seen.add(previous)
            cursor += 1
    if cursor != len(rows) or ids != sorted(set(ids)):
        raise ValueError
    cursor = 0
    for bi, batch in enumerate(batches):
        _check(end)
        _fields(
            batch,
            "batch_index source_index first_ordinal row_count total_codepoints "
            "total_native_request_bytes",
        )
        for key, low, high in (
            ("batch_index", 0, len(batches) - 1),
            ("source_index", 0, len(sources) - 1),
            ("first_ordinal", 0, len(rows) - 1),
            ("row_count", 1, bp.max_items),
            ("total_codepoints", 0, bp.max_total_codepoints),
            ("total_native_request_bytes", 1, bp.max_total_request_bytes),
        ):
            _integer(batch[key], low, high)
        n = batch["row_count"]
        if batch["batch_index"] != bi or batch["first_ordinal"] != cursor or cursor + n > len(rows):
            raise ValueError
        selected = rows[cursor : cursor + n]
        if (
            any(r["source_index"] != batch["source_index"] for r in selected)
            or sum(r["codepoints"] for r in selected) != batch["total_codepoints"]
            or sum(r["native_request_bytes"] for r in selected)
            != batch["total_native_request_bytes"]
        ):
            raise ValueError
        # Every non-final same-source batch must have been closed by the greedy rule.
        if cursor + n < len(rows) and rows[cursor + n]["source_index"] == batch["source_index"]:
            next_row = rows[cursor + n]
            if (
                n < bp.max_items
                and batch["total_codepoints"] + next_row["codepoints"] <= bp.max_total_codepoints
                and batch["total_native_request_bytes"] + next_row["native_request_bytes"]
                <= bp.max_total_request_bytes
            ):
                raise ValueError
        cursor += n
    if cursor != len(rows):
        raise ValueError
    _check(end)
    return _view(data, doc), doc


def parse(program_bytes):
    """Parse canonical structural data; it provides no source authority."""
    try:
        return _parse(program_bytes)[0]
    except Exception:
        raise ProgramError("source program refused") from None


def validate(originals, derived, program_bytes):
    """Freshly rebuild and compare the complete declared selection."""
    try:
        _, doc = _parse(program_bytes)
        fresh = build(
            originals,
            derived,
            tuple(s["bundle_id"] for s in doc["sources"]),
            policy=rr.Policy(**doc["representation_policy"]),
            batch_policy=rr.BatchPolicy(**doc["batch_policy"]),
            program_policy=ProgramPolicy(**doc["program_policy"]),
        )
        if fresh.program_bytes != program_bytes:
            raise ValueError
        return fresh
    except Exception:
        raise ProgramError("source program refused") from None
