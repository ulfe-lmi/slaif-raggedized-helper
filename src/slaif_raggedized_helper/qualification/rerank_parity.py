"""Version 1 supplied-score rerank parity, with no inference or qualification.

``analyze_rerank_parity(mapping_or_ParityInput)`` accepts a strict mapping or DTO.
Each side supplies the same definition (model, checkpoint, tokenizer, pair_budget),
its own execution declaration and a list of scored pairs. Each pair contains
pair_id, query_id, passage_id, query_digest and passage_digest (lowercase SHA-256
hex strings), and score. Execution has device, precision and provenance; only
SUPPLIED_UNVERIFIED is admitted. Identifiers and execution labels are declarations,
not verified artifacts. The sides may arrive in any order. Pair, query/passage and
digest identities must bind exactly; repeated query IDs must share a query digest,
and repeated passage IDs must share a passage digest. A query/passage combination
may occur only once. No raw text is accepted.

Criteria declare max_absolute_delta, min_top_k_overlap and top_k. Ranks descend by
score, ties ordered by ascending pair_id. Per-query overlap uses min(top_k, count)
as denominator; it is reference agreement, never gold recall. The result includes
paired signed (candidate minus reference) and absolute deltas, ranks, query overlap,
counts and whether all declared criteria passed. Missing gold is unavailable.
Limits: 512 pairs, 128 queries, 512 candidates/query, 1024 score values,
262144 estimated sort-work units and 512 output pairs. Scores/thresholds are
finite and bounded by 1e100 to keep arithmetic finite. Errors never echo inputs.
"""
from __future__ import annotations

import math
from collections import defaultdict
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from ..schema import RerankPair, RerankRequest, RerankResult, bind_rerank_scores


class ParityError(ValueError):
    """Invalid or incompatible supplied parity evidence; message is input-free."""


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)


class Definition(_Strict):
    model: str = Field(min_length=1, max_length=128)
    checkpoint: str = Field(min_length=1, max_length=128)
    tokenizer: str = Field(min_length=1, max_length=128)
    pair_budget: int = Field(ge=1, le=1_000_000)


class Execution(_Strict):
    device: str = Field(min_length=1, max_length=128)
    precision: str = Field(min_length=1, max_length=128)
    provenance: Literal["SUPPLIED_UNVERIFIED"]


class ScoredPair(_Strict):
    pair_id: str = Field(min_length=1, max_length=128)
    query_id: str = Field(min_length=1, max_length=128)
    passage_id: str = Field(min_length=1, max_length=128)
    query_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    passage_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    score: float

    @field_validator("score", mode="before")
    @classmethod
    def score_is_finite(cls, value: object) -> object:
        return _number(value, -1e100, 1e100)


class Side(_Strict):
    definition: Definition
    execution: Execution
    pairs: list[ScoredPair] = Field(min_length=1, max_length=512)


class Criteria(_Strict):
    top_k: int = Field(ge=1, le=512)
    max_absolute_delta: float
    min_top_k_overlap: float

    @field_validator("max_absolute_delta", mode="before")
    @classmethod
    def delta_is_finite(cls, value: object) -> object:
        return _number(value, 0, 2e100)

    @field_validator("min_top_k_overlap", mode="before")
    @classmethod
    def overlap_is_finite(cls, value: object) -> object:
        return _number(value, 0, 1)


def _number(value: object, lower: float, upper: float) -> object:
    if type(value) not in (int, float):
        raise ValueError("invalid number")
    try:
        if not math.isfinite(value) or not lower <= value <= upper:
            raise ValueError("invalid number")
    except OverflowError:
        raise ValueError("invalid number") from None
    return value


class ParityInput(_Strict):
    version: Literal[1]
    reference: Side
    candidate: Side
    criteria: Criteria

    @field_validator("version", mode="before")
    @classmethod
    def version_is_int(cls, value: object) -> object:
        if type(value) is not int:
            raise ValueError("invalid version")
        return value


def _bind(side: Side) -> dict[str, ScoredPair]:
    pairs = side.pairs
    by_id = {p.pair_id: p for p in pairs}
    if len(by_id) != len(pairs):
        raise ParityError("duplicate pair identity")
    combinations = {(p.query_id, p.passage_id) for p in pairs}
    if len(combinations) != len(pairs):
        raise ParityError("duplicate query and passage identity")
    queries: dict[str, str] = {}
    passages: dict[str, str] = {}
    for p in pairs:
        if (p.query_id in queries and queries[p.query_id] != p.query_digest) or (
            p.passage_id in passages and passages[p.passage_id] != p.passage_digest
        ):
            raise ParityError("inconsistent input identity")
        queries[p.query_id] = p.query_digest
        passages[p.passage_id] = p.passage_digest
    if len(queries) > 128:
        raise ParityError("work limit exceeded")
    request = RerankRequest(pairs=[RerankPair(pair_id=p.pair_id, query_id=p.query_id,
                                               passage_id=p.passage_id) for p in pairs],
                            deadline_seconds=1.0)
    result = RerankResult(scores={p.pair_id: p.score for p in pairs})
    bind_rerank_scores(request, result)
    return by_id


def analyze_rerank_parity(data: dict | ParityInput) -> dict:
    """Analyze declared supplied scores; raise :class:`ParityError` on refusal."""
    try:
        # Revalidate DTOs too: Pydantic's frozen lists can still be mutated.
        raw = data.model_dump() if isinstance(data, ParityInput) else data
        value = ParityInput.model_validate(raw)
        ref = _bind(value.reference)
        candidate = _bind(value.candidate)
        if value.reference.definition != value.candidate.definition:
            raise ParityError("definition mismatch")
        if ref.keys() != candidate.keys():
            raise ParityError("pair identity mismatch")
        groups: dict[str, list[str]] = defaultdict(list)
        for pair_id, left in ref.items():
            right = candidate[pair_id]
            if (left.query_id, left.passage_id, left.query_digest, left.passage_digest) != (
                right.query_id, right.passage_id, right.query_digest, right.passage_digest
            ):
                raise ParityError("input identity mismatch")
            groups[left.query_id].append(pair_id)
        # A conservative quadratic bound also covers the actual sort and output work.
        if sum(len(ids) ** 2 for ids in groups.values()) > 262144:
            raise ParityError("work limit exceeded")
        rows = []
        queries = []
        passed = True
        for query_id in sorted(groups):
            ids = groups[query_id]
            a = sorted(ids, key=lambda i: (-ref[i].score, i))
            b = sorted(ids, key=lambda i: (-candidate[i].score, i))
            rank_a = {pair_id: n for n, pair_id in enumerate(a, 1)}
            rank_b = {pair_id: n for n, pair_id in enumerate(b, 1)}
            k = min(value.criteria.top_k, len(ids))
            overlap = len(set(a[:k]) & set(b[:k])) / k
            passed &= overlap >= value.criteria.min_top_k_overlap
            queries.append({"query_id": query_id, "sample_count": len(ids), "top_k": k,
                            "top_k_overlap": overlap, "rank_agreement": a == b})
            for pair_id in sorted(ids):
                delta = candidate[pair_id].score - ref[pair_id].score
                passed &= abs(delta) <= value.criteria.max_absolute_delta
                rows.append({"pair_id": pair_id, "query_id": query_id,
                             "signed_delta": delta, "absolute_delta": abs(delta),
                             "reference_rank": rank_a[pair_id], "candidate_rank": rank_b[pair_id]})
        return {"version": 1, "provenance": "SUPPLIED_UNVERIFIED", "criteria_passed": passed,
                "pair_count": len(rows), "query_count": len(queries), "pairs": rows,
                "queries": queries, "gold_recall": None,
                "reference_execution": value.reference.execution.model_dump(),
                "candidate_execution": value.candidate.execution.model_dump()}
    except ParityError:
        raise
    except (ValidationError, ValueError, TypeError, OverflowError):
        raise ParityError("invalid parity input") from None
