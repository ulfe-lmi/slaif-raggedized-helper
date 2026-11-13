"""Admission of structural, unverified text-evaluation declarations."""

from dataclasses import dataclass, field
import hashlib
import json
import re
import time


class DatasetError(ValueError):
    """A dataset could not be admitted."""


@dataclass(frozen=True, repr=False)
class GoldSpan:
    revision_id: str
    extraction_id: str
    block_id: str
    start: int
    end: int
    text_sha256: str


@dataclass(frozen=True, repr=False)
class Requirement:
    requirement_id: str
    grade: int
    alternatives: tuple


@dataclass(frozen=True, repr=False)
class DeclaredScope:
    corpora: tuple
    versions: tuple
    labels: tuple


@dataclass(frozen=True, repr=False)
class Case:
    case_id: str
    family_id: str
    split: str
    origin: str
    authorship_ref: str
    rights_ref: str
    split_review_ref: str
    question: str
    language: str
    product: str | None
    version: str | None
    scope: DeclaredScope
    answerability: str
    modality: str
    acceptable_facts: tuple
    disallowed_claims: tuple
    requirements: tuple


@dataclass(frozen=True, repr=False)
class Dataset:
    canonical_bytes: bytes
    namespace: str
    split_policy_ref: str
    cases: tuple
    dataset_id: str
    split_id: str
    case_count: int
    gold_atom_count: int
    synthetic_count: int
    human_declared_count: int
    tuning_count: int
    held_out_count: int
    held_out_human_declared_count: int
    qualification: str = field(default="NOT_QUALIFIED", init=False)
    authorship_status: str = field(default="DECLARED_UNVERIFIED", init=False)
    rights_status: str = field(default="DECLARED_UNVERIFIED", init=False)
    split_status: str = field(default="STRUCTURAL_ONLY", init=False)


def _refuse():
    raise ValueError


def _integer(value):
    negative = value.startswith("-")
    digits = value[1:] if negative else value
    limit = "9223372036854775808" if negative else "9223372036854775807"
    if len(digits) > 19 or (len(digits) == 19 and digits > limit):
        _refuse()
    return int(value)


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            _refuse()
        result[key] = value
    return result


def _dump(value):
    return json.dumps(
        value, sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False
    ).encode("ascii")


def _keys(value, names):
    if type(value) is not dict or value.keys() != set(names.split()):
        _refuse()


def _text(value, chars, size, *, controls=False, nonblank=False):
    if (
        type(value) is not str
        or not value
        or (nonblank and not value.strip())
        or len(value) > chars
        or len(value.encode("utf-8")) > size
        or (controls and any(ord(c) < 32 or 127 <= ord(c) <= 159 for c in value))
    ):
        _refuse()
    return value


def _identifier(value):
    if type(value) is not str or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}", value):
        _refuse()
    return value


def _list(value, minimum, maximum):
    if type(value) is not list or not minimum <= len(value) <= maximum:
        _refuse()
    return value


def _sorted_unique(values):
    if any(a >= b for a, b in zip(values, values[1:])):
        _refuse()


def _admit(data, deadline_ms, start):
    if (
        type(data) is not bytes
        or not 1 <= len(data) <= 16777216
        or type(deadline_ms) is not int
        or not 1 <= deadline_ms <= 30000
    ):
        _refuse()
    deadline = start + deadline_ms / 1000

    def check():
        if time.monotonic() >= deadline:
            _refuse()

    root = json.loads(
        data.decode("ascii"),
        parse_int=_integer,
        parse_float=lambda _: _refuse(),
        parse_constant=lambda _: _refuse(),
        object_pairs_hook=_pairs,
    )
    check()
    nodes = text = 0
    stack = [(root, 0)]
    while stack:
        value, depth = stack.pop()
        nodes += 1
        if nodes > 200000 or depth > 16:
            _refuse()
        if type(value) is str:
            value.encode("utf-8")
            text += len(value)
            if text > 4000000:
                _refuse()
        elif type(value) is dict:
            for key, item in value.items():
                stack.append((key, depth + 1))
                stack.append((item, depth + 1))
        elif type(value) is list:
            stack.extend((item, depth + 1) for item in value)
        check()
    if _dump(root) != data:
        _refuse()
    check()
    _keys(root, "schema kind namespace split_policy_ref cases")
    if (
        type(root["schema"]) is not int
        or root["schema"] != 1
        or root["kind"] != "slaif-text-evaluation-dataset-v1"
    ):
        _refuse()
    namespace = _identifier(root["namespace"])
    policy = _text(root["split_policy_ref"], 512, 2048, controls=True, nonblank=True)
    cases = []
    assignments = []
    families, questions, intervals = {}, {}, {}
    atoms = facts = 0
    for case in _list(root["cases"], 1, 512):
        check()
        _keys(
            case,
            "case_id family_id split origin authorship_ref rights_ref split_review_ref "
            "question language product version scope answerability modality acceptable_facts "
            "disallowed_claims requirements",
        )
        cid, family = _identifier(case["case_id"]), _identifier(case["family_id"])
        split, origin = case["split"], case["origin"]
        if split not in ("tuning", "held_out") or origin not in ("synthetic", "human_declared"):
            _refuse()
        for name in ("authorship_ref", "rights_ref", "split_review_ref"):
            _text(case[name], 512, 2048, controls=True, nonblank=True)
        question = _text(case["question"], 8192, 32768, nonblank=True)
        language = case["language"]
        if type(language) is not str or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]{0,63}", language):
            _refuse()
        for name in ("product", "version"):
            if case[name] is not None:
                _text(case[name], 256, 1024)
        for mapping, key in ((families, family), (questions, question)):
            if key in mapping and mapping[key] != split:
                _refuse()
            mapping[key] = split
        scope = case["scope"]
        _keys(scope, "corpora versions labels")
        scoped = []
        for name, maximum in (("corpora", 128), ("versions", 128), ("labels", 64)):
            values = _list(scope[name], 0, maximum)
            for value in values:
                _text(value, 256, 1024)
            _sorted_unique(values)
            scoped.append(tuple(values))
        lists = []
        for name in ("acceptable_facts", "disallowed_claims"):
            values = _list(case[name], 0, 64)
            for value in values:
                _text(value, 2000, 8000, nonblank=True)
            if len(set(values)) != len(values):
                _refuse()
            facts += len(values)
            lists.append(tuple(values))
        if facts > 8192 or set(lists[0]) & set(lists[1]):
            _refuse()
        answer = case["answerability"]
        requirements = []
        for req in _list(case["requirements"], 0, 16):
            _keys(req, "requirement_id grade alternatives")
            rid = _identifier(req["requirement_id"])
            if type(req["grade"]) is not int or not 1 <= req["grade"] <= 3:
                _refuse()
            alternatives, alternative_bytes = [], []
            for alternative in _list(req["alternatives"], 1, 8):
                alternative_bytes.append(_dump(alternative))
                spans, span_keys = [], []
                for span in _list(alternative, 1, 8):
                    check()
                    _keys(span, "revision_id extraction_id block_id start end text_sha256")
                    for name in ("revision_id", "extraction_id"):
                        if type(span[name]) is not str or not re.fullmatch(
                            r"sha256:[0-9a-f]{64}", span[name]
                        ):
                            _refuse()
                    block = _text(span["block_id"], 256, 1024)
                    lo, hi, digest = span["start"], span["end"], span["text_sha256"]
                    if (
                        type(lo) is not int
                        or type(hi) is not int
                        or not 0 <= lo < hi <= 200000
                        or type(digest) is not str
                        or not re.fullmatch(r"[0-9a-f]{64}", digest)
                    ):
                        _refuse()
                    interval = (span["revision_id"], span["extraction_id"], block, lo, hi)
                    if interval in intervals and intervals[interval] != digest:
                        _refuse()
                    intervals[interval] = digest
                    span_keys.append((*interval, digest))
                    spans.append(GoldSpan(*interval, digest))
                    atoms += 1
                    if atoms > 4096:
                        _refuse()
                _sorted_unique(span_keys)
                alternatives.append(tuple(spans))
            _sorted_unique(alternative_bytes)
            requirements.append(Requirement(rid, req["grade"], tuple(alternatives)))
        _sorted_unique([r.requirement_id for r in requirements])
        if (
            answer not in ("answerable", "unanswerable", "unknown")
            or case["modality"] != "text"
            or (answer == "answerable" and (not lists[0] or not requirements))
            or (answer != "answerable" and requirements)
        ):
            _refuse()
        cases.append(
            Case(
                cid,
                family,
                split,
                origin,
                case["authorship_ref"],
                case["rights_ref"],
                case["split_review_ref"],
                question,
                language,
                case["product"],
                case["version"],
                DeclaredScope(*scoped),
                answer,
                "text",
                *lists,
                tuple(requirements),
            )
        )
        assignments.append(
            dict(
                case_id=cid,
                family_id=family,
                split=split,
                origin=origin,
                question_sha256=hashlib.sha256(question.encode("utf-8")).hexdigest(),
            )
        )
    _sorted_unique([c.case_id for c in cases])
    dataset_id = (
        "sha256:" + hashlib.sha256(b"slaif-text-evaluation-dataset-v1\n" + data).hexdigest()
    )
    check()
    split_bytes = _dump(dict(namespace=namespace, split_policy_ref=policy, assignments=assignments))
    check()
    split_id = (
        "sha256:" + hashlib.sha256(b"slaif-text-evaluation-split-v1\n" + split_bytes).hexdigest()
    )
    check()
    result = Dataset(
        data,
        namespace,
        policy,
        tuple(cases),
        dataset_id,
        split_id,
        len(cases),
        atoms,
        sum(c.origin == "synthetic" for c in cases),
        sum(c.origin == "human_declared" for c in cases),
        sum(c.split == "tuning" for c in cases),
        sum(c.split == "held_out" for c in cases),
        sum(c.split == "held_out" and c.origin == "human_declared" for c in cases),
    )
    check()
    return result


def admit(dataset_bytes, *, deadline_ms=5000):
    """Admit canonical bytes as declarations, without verifying their provenance."""
    try:
        start = time.monotonic()
        return _admit(dataset_bytes, deadline_ms, start)
    except Exception:
        raise DatasetError("text evaluation dataset refused") from None
