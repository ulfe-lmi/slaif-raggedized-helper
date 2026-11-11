from slaif_raggedized_helper.qualification.rerank_parity import analyze_rerank_parity
from slaif_raggedized_helper.schema import (
    RerankPair, RerankRequest, RerankResult, bind_rerank_scores,
)


def test_public_composition_with_shared_contract():
    request = RerankRequest(pairs=[RerankPair(pair_id="p", query_id="q", passage_id="d")],
                            deadline_seconds=1)
    scores = RerankResult(scores={"p": -0.5})
    bind_rerank_scores(request, scores)
    pair = {**request.pairs[0].model_dump(), "query_digest": "a" * 64,
            "passage_digest": "b" * 64, "score": scores.scores["p"]}
    side = {"definition": {"model": "m", "checkpoint": "c", "tokenizer": "t",
                           "pair_budget": 1280},
            "execution": {"device": "cpu", "precision": "fp32",
                          "provenance": "SUPPLIED_UNVERIFIED"}, "pairs": [pair]}
    result = analyze_rerank_parity({"version": 1, "reference": side, "candidate": side,
                                    "criteria": {"top_k": 1, "max_absolute_delta": 0,
                                                 "min_top_k_overlap": 1}})
    assert result["criteria_passed"] and result["pairs"][0]["absolute_delta"] == 0
    assert result["provenance"] == "SUPPLIED_UNVERIFIED"
