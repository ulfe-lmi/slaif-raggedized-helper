import copy
import dataclasses
import hashlib
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from slaif_raggedized_helper import text_evaluation_dataset as dataset


ORACLE = json.loads(
    (Path(__file__).parents[2] / "docs/parallel/text-evaluation-dataset-oracle.json").read_text()
)


def encode(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode(
        "ascii"
    )


def fixture():
    return json.loads(ORACLE["dataset_ascii"])


def refused(value):
    with pytest.raises(dataset.DatasetError, match="^text evaluation dataset refused$") as exc:
        dataset.admit(value if type(value) is bytes else encode(value))
    assert exc.value.__suppress_context__


def test_oracle_and_frozen_private_records():
    result = dataset.admit(ORACLE["dataset_ascii"].encode("ascii"))
    for key, expected in ORACLE["expected"].items():
        assert getattr(result, key) == expected
    case = result.cases[0]
    span = case.requirements[0].alternatives[0][0]
    assert case.question == "Kako ohraniti --no-cache Ž😀 e\u0301?"
    assert hashlib.sha256("Ž😀abc"[span.start : span.end].encode()).hexdigest() == span.text_sha256
    for record in (result, case, case.scope, case.requirements[0], span):
        assert "synthetic" not in repr(record).lower()
        with pytest.raises(dataclasses.FrozenInstanceError):
            record.secret = 1
    with pytest.raises(TypeError):
        dataclasses.replace(result, qualification="QUALIFIED")


def test_split_identity_and_version_distinctions():
    data = fixture()
    original = dataset.admit(encode(data))
    data["cases"][0]["acceptable_facts"] = ["Changed fact"]
    changed = dataset.admit(encode(data))
    assert changed.dataset_id != original.dataset_id and changed.split_id == original.split_id
    data = fixture()
    other = copy.deepcopy(data["cases"][0])
    other.update(case_id="case3", version="v2")
    data["cases"].append(other)
    dataset.admit(encode(data))
    other["split"] = "held_out"
    refused(data)
    other["question"] = "Different"
    refused(data)  # same family still crosses split


def test_conjunctive_atoms_and_alternatives_and_conflict():
    data = fixture()
    req = data["cases"][0]["requirements"][0]
    atom = req["alternatives"][0][0]
    second = dict(atom, start=2, end=3, text_sha256="a" * 64)
    req["alternatives"] = [[atom, second], [second]]
    req["alternatives"].sort(key=encode)
    result = dataset.admit(encode(data))
    assert sorted(map(len, result.cases[0].requirements[0].alternatives)) == [1, 2]
    req["alternatives"][0].append(dict(atom, text_sha256="b" * 64))
    req["alternatives"][0].sort(
        key=lambda x: tuple(
            x[k]
            for k in ("revision_id", "extraction_id", "block_id", "start", "end", "text_sha256")
        )
    )
    req["alternatives"].sort(key=encode)
    refused(data)


@pytest.mark.parametrize(
    "mutate",
    [
        lambda d: d.update(extra=1),
        lambda d: d.update(schema=True),
        lambda d: d["cases"][0].update(question=" "),
        lambda d: d["cases"][0].update(answerability="unknown"),
        lambda d: d["cases"][0].update(acceptable_facts=[]),
        lambda d: d["cases"][0]["requirements"][0].update(grade=True),
        lambda d: d["cases"][0]["requirements"][0]["alternatives"][0][0].update(end=0),
        lambda d: d["cases"][0]["scope"].update(labels=["z", "a"]),
        lambda d: d["cases"][0].update(question="\ud800"),
        lambda d: d["cases"][0].update(product="x" * 257),
    ],
)
def test_invalid_fields(mutate):
    data = fixture()
    mutate(data)
    refused(data)


def test_decoder_and_exact_input():
    raw = ORACLE["dataset_ascii"].encode("ascii")
    for invalid in (
        raw + b" ",
        raw.replace(b'"schema":1', b'"schema":1,"schema":1'),
        raw.replace(b'"schema":1', b'"schema":1.0'),
        raw.replace(b'"schema":1', b'"schema":9223372036854775808'),
        raw.replace(b'"schema":1', b'"schema":' + b"9" * 5000),
        b"\xff",
    ):
        refused(invalid)
    with pytest.raises(dataset.DatasetError):
        dataset.admit(bytearray(raw))
    with pytest.raises(dataset.DatasetError):
        dataset.admit(raw, deadline_ms=True)


def test_interrupt_identity_and_deadline_after_hash():
    raw = ORACLE["dataset_ascii"].encode("ascii")
    interruption = KeyboardInterrupt()
    with patch.object(dataset.json, "loads", side_effect=interruption):
        with pytest.raises(KeyboardInterrupt) as exc:
            dataset.admit(raw)
    assert exc.value is interruption
    real_hash = dataset.hashlib.sha256
    clock = [0.0]

    def slow_hash(*args):
        result = real_hash(*args)
        clock[0] = 10.0
        return result

    with (
        patch.object(dataset.time, "monotonic", side_effect=lambda: clock[0]),
        patch.object(dataset.hashlib, "sha256", side_effect=slow_hash),
    ):
        refused(raw)


def test_tree_and_aggregate_bounds():
    data = fixture()
    data["extra"] = [None] * 200000
    refused(data)
    data["extra"] = "x" * 4000001
    refused(data)
    nested = None
    for _ in range(17):
        nested = [nested]
    data["extra"] = nested
    refused(data)


def test_signed_integer_and_canonical_boundaries():
    assert dataset._integer("9223372036854775807") == 9223372036854775807
    assert dataset._integer("-9223372036854775808") == -9223372036854775808
    for value in ("9223372036854775808", "-9223372036854775809", "9" * 5000):
        with pytest.raises(ValueError):
            dataset._integer(value)
    raw = ORACLE["dataset_ascii"].encode("ascii")
    refused(raw.replace(b'"schema":1', b'"schema":-0'))
    refused(raw.replace(b'"schema":1', b'"schema":NaN'))


def test_unverified_refs_and_exact_unicode_scope():
    data = fixture()
    case = data["cases"][0]
    case["authorship_ref"] = "unreviewed"
    case["rights_ref"] = "unknown"
    case["scope"]["labels"] = [" ", "é", "😀"]
    result = dataset.admit(encode(data))
    assert result.cases[0].scope.labels == (" ", "é", "😀")
    assert result.authorship_status == result.rights_status == "DECLARED_UNVERIFIED"


def test_aggregate_fact_and_atom_limits():
    data = fixture()
    template = data["cases"][0]
    cases = []
    for i in range(65):
        case = copy.deepcopy(template)
        case["case_id"] = f"c{i:03d}"
        case["acceptable_facts"] = [f"fact {j}" for j in range(64)]
        case["disallowed_claims"] = [f"claim {j}" for j in range(64)]
        cases.append(case)
    data["cases"] = cases
    refused(data)
    for case in cases:
        case["acceptable_facts"] = ["fact"]
        case["disallowed_claims"] = []
        atom = case["requirements"][0]["alternatives"][0][0]
        alternatives = []
        for i in range(8):
            alternatives.append([dict(atom, start=i * 8 + j, end=i * 8 + j + 1) for j in range(8)])
        alternatives.sort(key=encode)
        case["requirements"][0]["alternatives"] = alternatives
    refused(data)
