"""Version 1 supplied-vector embedding parity analysis, with no model execution.

``analyze(request)`` accepts a mapping with exactly: version=1, reference and
candidate execution declarations (schema EmbeddingExecution or mappings), queries,
reference_corpus, candidate_corpus, k, cosine_tolerance and score_tolerance.
Each row is {id, input_digest, representation_digest, vector}; digests are lowercase
SHA-256 hex and bind the encoded input and representation. Query rows may also have
``relevant_ids`` (nonempty unique corpus IDs); absent or empty means recall unavailable.
Reference is declared CPU/FP32 and candidate GPU/FP16; FP32 storage is a target,
not an observation or supplied declaration. Queries are
always the same CPU/FP32 vectors for both rankings. Definitions and execution
fingerprints are declarations, not proof. Missing artifact/tokenizer identity yields
an unverified space, even when the fingerprints match. Declared query_prefix=None
means no prefix; it is part of the schema fingerprint.

Bounds: dimension <=4096, queries <=128, passages <=2048, numeric elements <=2M,
query*passage*dimension <=4M, query*passage <=32768, k <=2048. Scores are raw
stored-vector dot products; ranks sort descending score then ascending durable ID.
Gold recall denominator is the number of explicitly supplied relevant IDs. Tolerances
are comparison criteria only. Refusals use a fixed safe reason and never echo inputs.

The input fingerprint is SHA-256 over length-framed canonical JSON records. Each
record is UTF-8 JSON with sorted keys, ASCII escaping, and compact separators, preceded
by its byte length as an unsigned 8-byte big-endian integer. The first record contains
schema version, full validated execution declarations, requested k and tolerances as
Python float.hex strings. Subsequent records are sorted by section (queries, reference,
candidate, in that order) then durable ID; each includes section, ID, both digests,
the admitted float.hex vector, and sorted relevant IDs for queries. This binds the
normalized admitted input, including signed zero, and does not retain raw vectors.
No digest proves that the supplied values or declared executions were actually produced
by a model. Storage provenance is unavailable for these generic supplied vectors.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections.abc import Mapping
from decimal import Decimal, localcontext

from pydantic import ValidationError

from slaif_raggedized_helper.schema import EmbeddingDefinition, EmbeddingExecution


class ParityError(ValueError):
    """Safe typed refusal of invalid or unrepresentable supplied evidence."""


def _refuse(reason: str) -> None:
    raise ParityError(reason)


def _keys(value: object, required: set[str], optional: set[str] = frozenset()) -> dict:
    if (
        not isinstance(value, Mapping)
        or not required <= value.keys()
        or value.keys() - required - optional
    ):
        _refuse("invalid_shape")
    return dict(value)


def _integer(value: object, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        _refuse("invalid_integer")
    return value


def _number(value: object) -> float:
    if type(value) not in (int, float):
        _refuse("invalid_number")
    try:
        n = float(value)
    except (OverflowError, ValueError):
        _refuse("invalid_number")
    if not math.isfinite(n):
        _refuse("invalid_number")
    return n


def _execution(value: object) -> EmbeddingExecution:
    if isinstance(value, EmbeddingExecution):
        return value
    raw = _keys(value, {"definition", "device", "dtype"})
    definition = raw["definition"]
    if isinstance(definition, EmbeddingDefinition):
        raw["definition"] = definition
    else:
        d = _keys(
            definition,
            {"model_name", "checkpoint_revision", "pooling", "dimensions"},
            {"checkpoint_sha256", "tokenizer_revision", "normalize", "query_prefix"},
        )
        _integer(d["dimensions"], 1, 4096)
        if "normalize" in d and type(d["normalize"]) is not bool:
            _refuse("invalid_definition")
        raw["definition"] = d
    try:
        return EmbeddingExecution.model_validate(raw)
    except (ValidationError, ValueError, TypeError):
        _refuse("invalid_execution")


def _identifier(value: object) -> str:
    if (
        not isinstance(value, str)
        or not 1 <= len(value) <= 128
        or not value.isascii()
        or not re.fullmatch(r"[A-Za-z0-9._:-]+", value)
    ):
        _refuse("invalid_id")
    return value


def _digest(value: object) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
        _refuse("invalid_digest")
    return value


def _rows(value: object, dimension: int, query: bool) -> dict:
    if not isinstance(value, list) or not 1 <= len(value) <= (128 if query else 2048):
        _refuse("invalid_count")
    result = {}
    for item in value:
        row = _keys(
            item,
            {"id", "input_digest", "representation_digest", "vector"},
            {"relevant_ids"} if query else set(),
        )
        ident = _identifier(row["id"])
        if ident in result:
            _refuse("duplicate_id")
        vector = row["vector"]
        if not isinstance(vector, list) or len(vector) != dimension:
            _refuse("invalid_dimension")
        vec = tuple(_number(x) for x in vector)
        if not any(vec):
            _refuse("zero_vector")
        norm = math.hypot(*vec)
        if not math.isfinite(norm) or norm == 0:
            _refuse("unrepresentable_norm")
        relevant = row.get("relevant_ids", [])
        if not isinstance(relevant, list) or len(relevant) > 2048:
            _refuse("invalid_gold")
        ids = [_identifier(x) for x in relevant]
        if len(set(ids)) != len(ids):
            _refuse("invalid_gold")
        result[ident] = (
            _digest(row["input_digest"]),
            _digest(row["representation_digest"]),
            vec,
            norm,
            ids,
        )
    return result


def _cosine(a: tuple, b: tuple) -> float:
    ma, mb = max(map(abs, a)), max(map(abs, b))
    aa, bb = [x / ma for x in a], [x / mb for x in b]
    return max(
        -1.0,
        min(
            1.0,
            math.fsum(x * y for x, y in zip(aa, bb, strict=True))
            / math.hypot(*aa)
            / math.hypot(*bb),
        ),
    )


def _dot(a: tuple, b: tuple) -> float:
    # Decimal avoids overflow and underflow in intermediate products, including cancellation.
    with localcontext() as ctx:
        ctx.prec = 2200
        result = sum(
            (Decimal.from_float(x) * Decimal.from_float(y) for x, y in zip(a, b, strict=True)),
            Decimal(0),
        )
        try:
            out = float(result)
        except (OverflowError, ValueError):
            _refuse("unrepresentable_score")
    if not math.isfinite(out) or (out == 0.0 and result != 0):
        _refuse("unrepresentable_score")
    return out


def _input_fingerprint(ref, cand, k, ct, st, queries, reference, candidate) -> str:
    digest = hashlib.sha256()

    def add(record: dict) -> None:
        data = json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode(
            "ascii"
        )
        digest.update(len(data).to_bytes(8, "big"))
        digest.update(data)

    add(
        {
            "format": "embedding-parity-input-v1",
            "reference": ref.model_dump(mode="json"),
            "candidate": cand.model_dump(mode="json"),
            "k": k,
            "cosine_tolerance": ct.hex(),
            "score_tolerance": st.hex(),
        }
    )
    for section, rows in (("queries", queries), ("reference", reference), ("candidate", candidate)):
        for ident in sorted(rows):
            row = rows[ident]
            record = {
                "section": section,
                "id": ident,
                "input_digest": row[0],
                "representation_digest": row[1],
                "vector": [value.hex() for value in row[2]],
            }
            if section == "queries":
                record["relevant_ids"] = sorted(row[4])
            add(record)
    return digest.hexdigest()


def analyze(request: Mapping) -> dict:
    """Analyze bounded caller-supplied vectors; return SUPPLIED_UNVERIFIED evidence."""
    req = _keys(
        request,
        {
            "version",
            "reference",
            "candidate",
            "queries",
            "reference_corpus",
            "candidate_corpus",
            "k",
            "cosine_tolerance",
            "score_tolerance",
        },
    )
    _integer(req["version"], 1, 1)
    k = _integer(req["k"], 1, 2048)
    ct, st = _number(req["cosine_tolerance"]), _number(req["score_tolerance"])
    if not 0 <= ct <= 2 or st < 0:
        _refuse("invalid_tolerance")
    ref, cand = _execution(req["reference"]), _execution(req["candidate"])
    dim = _integer(ref.definition.dimensions, 1, 4096)
    _integer(cand.definition.dimensions, 1, 4096)
    if ref.definition.fingerprint() != cand.definition.fingerprint():
        _refuse("space_mismatch")
    if (ref.device.value, ref.dtype.value, cand.device.value, cand.dtype.value) != (
        "cpu",
        "fp32",
        "gpu",
        "fp16",
    ):
        _refuse("execution_mismatch")
    q, r, c = req["queries"], req["reference_corpus"], req["candidate_corpus"]
    if not all(isinstance(x, list) for x in (q, r, c)):
        _refuse("invalid_count")
    nq, nr, nc = len(q), len(r), len(c)
    if not (1 <= nq <= 128 and 1 <= nr <= 2048 and nc == nr):
        _refuse("invalid_count")
    if (nq + nr + nc) * dim > 2_000_000 or nq * nr * dim > 4_000_000 or nq * nr > 32768:
        _refuse("work_limit")
    queries, reference, candidate = _rows(q, dim, True), _rows(r, dim, False), _rows(c, dim, False)
    if reference.keys() != candidate.keys():
        _refuse("corpus_ids_mismatch")
    for ident in reference:
        if reference[ident][:2] != candidate[ident][:2]:
            _refuse("binding_mismatch")
    paired = []
    for ident in sorted(reference):
        a, b = reference[ident], candidate[ident]
        cos = _cosine(a[2], b[2])
        paired.append(
            {
                "id": ident,
                "input_digest": a[0],
                "representation_digest": a[1],
                "cosine": cos,
                "cosine_within_tolerance": 1 - cos <= ct,
                "reference_norm": a[3],
                "candidate_norm": b[3],
                "reference_l2_deviation": abs(a[3] - 1),
                "candidate_l2_deviation": abs(b[3] - 1),
            }
        )
    results = []
    for ident in sorted(queries):
        row = queries[ident]
        gold = set(row[4])
        if not gold <= reference.keys():
            _refuse("missing_gold_id")
        rs = {p: _dot(row[2], reference[p][2]) for p in reference}
        cs = {p: _dot(row[2], candidate[p][2]) for p in reference}
        rr = sorted(rs, key=lambda p: (-rs[p], p))
        cr = sorted(cs, key=lambda p: (-cs[p], p))
        ranks_r = {p: i + 1 for i, p in enumerate(rr)}
        ranks_c = {p: i + 1 for i, p in enumerate(cr)}
        effective = min(k, nr)
        drift = []
        for p in sorted(reference):
            delta = cs[p] - rs[p]
            if not math.isfinite(delta):
                _refuse("unrepresentable_score_drift")
            drift.append(
                {
                    "id": p,
                    "reference_score": rs[p],
                    "candidate_score": cs[p],
                    "score_delta": delta,
                    "score_within_tolerance": abs(delta) <= st,
                    "reference_rank": ranks_r[p],
                    "candidate_rank": ranks_c[p],
                    "rank_delta": ranks_c[p] - ranks_r[p],
                }
            )
        results.append(
            {
                "id": ident,
                "input_digest": row[0],
                "representation_digest": row[1],
                "sample_count": 1,
                "query_norm": row[3],
                "query_l2_deviation": abs(row[3] - 1),
                "candidate_count": nr,
                "requested_k": k,
                "effective_k": effective,
                "reference_top_k": rr[:effective],
                "candidate_top_k": cr[:effective],
                "reference_overlap_at_k": len(set(rr[:effective]) & set(cr[:effective]))
                / effective,
                "gold_denominator": len(gold) if gold else None,
                "reference_gold_recall_at_k": len(gold & set(rr[:effective])) / len(gold)
                if gold
                else None,
                "candidate_gold_recall_at_k": len(gold & set(cr[:effective])) / len(gold)
                if gold
                else None,
                "scores": drift,
            }
        )
    definition = ref.definition
    return {
        "version": 1,
        "evidence": "SUPPLIED_UNVERIFIED",
        "qualification": "NOT_QUALIFIED",
        "space_identity": "DECLARED_COMPLETE_UNVERIFIED"
        if definition.checkpoint_sha256 and definition.tokenizer_revision
        else "INCOMPLETE_UNVERIFIED",
        "space_fingerprint": definition.fingerprint(),
        "reference_execution_fingerprint": ref.fingerprint(),
        "candidate_execution_fingerprint": cand.fingerprint(),
        "input_fingerprint": _input_fingerprint(
            ref, cand, k, ct, st, queries, reference, candidate
        ),
        "candidate_storage": {
            "required_target_dtype": "fp32",
            "supplied_dtype": None,
            "observed_dtype": None,
            "provenance": "unavailable",
        },
        "cosine_tolerance": ct,
        "score_tolerance": st,
        "paired_vectors": paired,
        "queries": results,
    }
