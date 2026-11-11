"""Bounded mechanical validation of native policy, chunks and exported receipts."""

from dataclasses import dataclass, fields
import hashlib
import json
import re
import time

from . import chunking, native_chunking as nc, provenance_jsonl as jl, provenance_records as p
from .native_tokenizers import Count


class BundleRecordsError(ValueError):
    """Input-free refusal of the complete bundle boundary."""


@dataclass(frozen=True)
class Validated:
    policy: chunking.Policy
    chunks: tuple
    receipts: tuple
    header_json: bytes
    chunks_jsonl: bytes
    receipts_json: bytes


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError
        result[key] = value
    return result


def _parse(raw, max_nodes):
    obj = json.loads(
        raw.decode("utf-8"),
        object_pairs_hook=_unique,
        parse_constant=lambda _: (_ for _ in ()).throw(ValueError()),
    )
    stack = [(obj, 0)]
    nodes = 0
    while stack:
        value, depth = stack.pop()
        nodes += 1
        if nodes > max_nodes or depth > 16:
            raise ValueError
        if type(value) is dict:
            stack.extend((x, depth + 1) for x in value.values())
            for key in value:
                key.encode("utf-8")
        elif type(value) is list:
            stack.extend((x, depth + 1) for x in value)
        elif type(value) is str:
            value.encode("utf-8")
        elif type(value) not in (int, float, bool, type(None)):
            raise ValueError
        elif type(value) is float:
            import math

            if not math.isfinite(value):
                raise ValueError
    return obj


def _fields(obj, names):
    if type(obj) is not dict or set(obj) != set(names):
        raise ValueError


def validate(chunking_header_json_bytes, chunks_jsonl_bytes, receipts_json_bytes, expected_chunks):
    """Validate immutable bytes without source access or tokenizer execution."""
    start = time.monotonic()

    def check():
        if time.monotonic() - start >= 30:
            raise ValueError

    try:
        if (
            any(
                type(x) is not bytes
                for x in (chunking_header_json_bytes, chunks_jsonl_bytes, receipts_json_bytes)
            )
            or len(chunking_header_json_bytes) > 65536
            or len(chunks_jsonl_bytes) > jl.MAX_BYTES
            or len(receipts_json_bytes) > 8000000
            or type(expected_chunks) is not int
            or not 1 <= expected_chunks <= 4096
        ):
            raise ValueError
        header = _parse(chunking_header_json_bytes, 10000)
        _fields(header, ("policy", "query", "definitions", "policy_definition", "policy_id"))
        _fields(header["policy"], (f.name for f in fields(chunking.Policy)))
        policy = chunking.Policy(**header["policy"])
        query = header["query"]
        if type(query) is not str or len(query) > 10000:
            raise ValueError
        definitions = header["definitions"]
        if type(definitions) is not list or len(definitions) != 3:
            raise ValueError
        identities = []
        for d, role in zip(definitions, nc._ROLES):
            _fields(
                d, ("role", "artifact_sha256", "backend_version", "model_revision", "preprocessing")
            )
            if (
                d["role"] != role
                or d["backend_version"] != "0.21.4"
                or type(d["artifact_sha256"]) is not str
                or re.fullmatch("[0-9a-f]{64}", d["artifact_sha256"]) is None
                or any(
                    type(d[k]) is not str or not 1 <= len(d[k]) <= 256
                    for k in ("model_revision", "preprocessing")
                )
            ):
                raise ValueError
            identities.append(
                nc._digest(
                    nc._json(
                        {
                            "version": 1,
                            **d,
                            "mode": "pair" if role == "reranker_pair" else "single",
                            "serialization": nc._SERIALIZATION,
                        }
                    )
                )
            )
        definition = nc._json(
            {
                "version": 1,
                "kind": "observed-local-native",
                "policy": header["policy"],
                "definitions": identities,
                "query_input_sha256": nc._input_digest(query, None),
                "serialization": nc._SERIALIZATION,
            }
        ).decode()
        if header["policy_definition"] != definition or header["policy_id"] != p.policy_id(
            definition
        ):
            raise ValueError
        check()
        chunks = jl.decode(
            "Chunk",
            chunks_jsonl_bytes,
            hashlib.sha256(chunks_jsonl_bytes).hexdigest(),
            expected_chunks,
        )
        check()
        receipt_doc = _parse(receipts_json_bytes, 250000)
        _fields(receipt_doc, ("version", "receipts"))
        receipts = receipt_doc["receipts"]
        if (
            type(receipt_doc["version"]) is not int
            or receipt_doc["version"] != 1
            or type(receipts) is not list
            or len(receipts) != expected_chunks * 3
        ):
            raise ValueError
        seen = set()
        work = 0
        serialized_work = 0
        admitted_receipts = []
        for i, chunk in enumerate(chunks):
            check()
            if (
                chunk.chunk_id in seen
                or chunk.chunk_id != p.chunk_id(chunk)
                or chunk.policy_id != header["policy_id"]
                or len(chunk.counts) != 3
                or hashlib.sha256(chunk.text.encode()).hexdigest() != chunk.text_sha256
            ):
                raise ValueError
            seen.add(chunk.chunk_id)
            parts = []
            for fragment in chunk.fragments:
                if isinstance(fragment, p.SourceFragment):
                    if (
                        fragment.end - fragment.start != len(fragment.copied_text)
                        or fragment.end <= fragment.start
                    ):
                        raise ValueError
                    parts.append(fragment.copied_text)
                else:
                    parts.append(fragment.text)
            if "".join(parts) != chunk.text:
                raise ValueError
            rep = "".join(chunk.heading_path) + chunk.text
            for j, (d, ident) in enumerate(zip(definitions, identities)):
                receipt = receipts[3 * i + j]
                _fields(receipt, ("chunk_id", "definition_fingerprint", "count"))
                count = receipt["count"]
                _fields(
                    count,
                    (
                        "count",
                        "artifact_sha256",
                        "backend_version",
                        "role",
                        "model_revision",
                        "preprocessing",
                        "input_sha256",
                        "mode",
                        "serialization",
                    ),
                )
                text, pair = ((chunk.text, None), (rep, None), (query, rep))[j]
                chars = len(text) + (len(pair) if pair is not None else 0)
                work += chars
                if chars > 100000 or work > 20000000:
                    raise ValueError
                serialized = json.dumps(
                    [text, pair], ensure_ascii=True, separators=(",", ":")
                ).encode()
                serialized_work += len(serialized)
                if len(serialized) > 200000 or serialized_work > 20000000:
                    raise ValueError
                expected = {
                    **d,
                    "count": chunk.counts[j].count,
                    "input_sha256": hashlib.sha256(serialized).hexdigest(),
                    "mode": "pair" if j == 2 else "single",
                    "serialization": nc._SERIALIZATION,
                }
                if (
                    receipt["chunk_id"] != chunk.chunk_id
                    or receipt["definition_fingerprint"] != ident
                    or type(count["count"]) is not int
                    or not 0 <= count["count"] <= 200000
                    or count != expected
                    or chunk.counts[j].availability != "available"
                    or chunk.counts[j].provenance != "OBSERVED_LOCAL_NATIVE_TOKENIZATION:" + ident
                    or count["count"]
                    > (policy.soft_max, policy.representation_max, policy.pair_max)[j]
                ):
                    raise ValueError
                admitted_receipts.append(nc.Receipt(chunk.chunk_id, ident, Count(**count)))
        canonical_header = nc._json(header)
        canonical_receipts = nc._json(receipt_doc)
        canonical_chunks = jl.encode("Chunk", tuple(c.model_dump_json().encode() for c in chunks))
        check()
        return Validated(
            policy,
            chunks,
            tuple(admitted_receipts),
            canonical_header,
            canonical_chunks,
            canonical_receipts,
        )
    except Exception:
        raise BundleRecordsError("native bundle records refused") from None
