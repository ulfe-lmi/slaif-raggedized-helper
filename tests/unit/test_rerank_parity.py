import copy

import pytest

from slaif_raggedized_helper.qualification.rerank_parity import (
    ParityError,
    ParityInput,
    analyze_rerank_parity,
)


def fixture():
    definition = {"model": "m", "checkpoint": "c", "tokenizer": "t", "pair_budget": 1280}
    execution = {"device": "cpu", "precision": "fp32", "provenance": "SUPPLIED_UNVERIFIED"}
    pairs = [
        {"pair_id": "a", "query_id": "q", "passage_id": "a", "query_digest": "a" * 64,
         "passage_digest": "1" * 64, "score": -1},
        {"pair_id": "b", "query_id": "q", "passage_id": "b", "query_digest": "a" * 64,
         "passage_digest": "2" * 64, "score": 0},
        {"pair_id": "c", "query_id": "q", "passage_id": "c", "query_digest": "a" * 64,
         "passage_digest": "3" * 64, "score": 0},
        {"pair_id": "d", "query_id": "q2", "passage_id": "d", "query_digest": "b" * 64,
         "passage_digest": "4" * 64, "score": -2},
    ]
    side = {"definition": definition, "execution": execution, "pairs": pairs}
    return {"version": 1, "reference": side, "candidate": copy.deepcopy(side),
            "criteria": {"top_k": 1, "max_absolute_delta": 0, "min_top_k_overlap": 1}}


def test_ties_negative_permutation_and_queries():
    data = fixture()
    data["candidate"]["pairs"].reverse()
    result = analyze_rerank_parity(ParityInput.model_validate(data))
    assert result["criteria_passed"] and result["pair_count"] == 4 and result["query_count"] == 2
    assert [(p["pair_id"], p["reference_rank"]) for p in result["pairs"]] == [
        ("a", 3), ("b", 1), ("c", 2), ("d", 1)]
    assert result["gold_recall"] is None


def test_inversion_does_not_compare_sorted_magnitudes():
    data = fixture()
    data["reference"]["pairs"][0]["score"] = -2
    data["candidate"]["pairs"][0]["score"] = 0
    data["candidate"]["pairs"][1]["score"] = -2
    result = analyze_rerank_parity(data)
    assert not result["criteria_passed"]
    assert result["queries"][0]["top_k_overlap"] == 0
    assert result["pairs"][0]["signed_delta"] == 2


@pytest.mark.parametrize("change", ["duplicate", "missing", "extra", "combination", "query",
                                    "digest", "model", "checkpoint", "tokenizer", "budget",
                                    "live"])
def test_identity_and_provenance_refusals(change):
    data = fixture()
    side = data["candidate"]
    if change == "duplicate":
        side["pairs"].append(copy.deepcopy(side["pairs"][0]))
    elif change == "missing":
        side["pairs"].pop()
    elif change == "extra":
        p = copy.deepcopy(side["pairs"][0])
        p.update(pair_id="new", passage_id="new")
        side["pairs"].append(p)
    elif change == "combination":
        side["pairs"][1]["passage_id"] = "a"
    elif change == "query":
        side["pairs"][0]["query_id"] = "other"
    elif change == "digest":
        side["pairs"][0]["query_digest"] = "f" * 64
    elif change in ("model", "checkpoint", "tokenizer"):
        side["definition"][change] = "other"
    elif change == "budget":
        side["definition"]["pair_budget"] = 1024
    else:
        side["execution"]["provenance"] = "LIVE"
    with pytest.raises(ParityError) as error:
        analyze_rerank_parity(data)
    assert "other" not in str(error.value)


@pytest.mark.parametrize("bad", [True, "1", float("nan"), float("inf"), -float("inf"), 10**400])
def test_bad_scores(bad):
    data = fixture()
    data["candidate"]["pairs"][0]["score"] = bad
    with pytest.raises(ParityError):
        analyze_rerank_parity(data)


@pytest.mark.parametrize("field,bad", [("version", True), ("version", "1")])
def test_strict_version(field, bad):
    data = fixture()
    data[field] = bad
    with pytest.raises(ParityError):
        analyze_rerank_parity(data)


def test_limits():
    data = fixture()
    data["reference"]["pairs"] *= 129
    with pytest.raises(ParityError):
        analyze_rerank_parity(data)
    data = fixture()
    data["criteria"]["top_k"] = True
    with pytest.raises(ParityError):
        analyze_rerank_parity(data)


def test_maximum_pairs_and_query_limit():
    data = fixture()
    pairs = [dict(data["reference"]["pairs"][0], pair_id=str(i), passage_id=str(i))
             for i in range(512)]
    data["reference"]["pairs"] = pairs
    data["candidate"]["pairs"] = copy.deepcopy(pairs)
    assert analyze_rerank_parity(data)["pair_count"] == 512
    for i, pair in enumerate(pairs[:129]):
        pair["query_id"] = str(i)
    data["candidate"]["pairs"] = copy.deepcopy(pairs)
    with pytest.raises(ParityError):
        analyze_rerank_parity(data)


def test_mutated_dto_is_revalidated():
    dto = ParityInput.model_validate(fixture())
    dto.candidate.pairs.clear()
    with pytest.raises(ParityError):
        analyze_rerank_parity(dto)
