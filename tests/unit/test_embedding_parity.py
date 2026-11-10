import copy

import pytest

from slaif_raggedized_helper.qualification.embedding_parity import ParityError, analyze

D = "a" * 64


def row(ident, vector, **extra):
    return {"id": ident, "input_digest": D, "representation_digest": D, "vector": vector, **extra}


def request():
    definition = {
        "model_name": "fixture",
        "checkpoint_revision": "r1",
        "checkpoint_sha256": D,
        "tokenizer_revision": "t1",
        "pooling": "cls",
        "normalize": True,
        "dimensions": 2,
    }
    return {
        "version": 1,
        "reference": {"definition": definition, "device": "cpu", "dtype": "fp32"},
        "candidate": {"definition": copy.deepcopy(definition), "device": "gpu", "dtype": "fp16"},
        "queries": [row("q", [1, -1], relevant_ids=["a"])],
        "reference_corpus": [row("a", [1, -1]), row("b", [1, 0])],
        "candidate_corpus": [row("b", [3, 0]), row("a", [1, -1])],
        "k": 1,
        "cosine_tolerance": 0.01,
        "score_tolerance": 0.1,
    }


def test_raw_ranking_differs_from_cosine_and_gold():
    result = analyze(request())
    assert result["evidence"] == "SUPPLIED_UNVERIFIED"
    assert result["qualification"] == "NOT_QUALIFIED"
    q = result["queries"][0]
    assert q["reference_top_k"] == ["a"] and q["candidate_top_k"] == ["b"]
    assert q["reference_overlap_at_k"] == 0
    assert q["reference_gold_recall_at_k"] == 1 and q["candidate_gold_recall_at_k"] == 0
    assert result["paired_vectors"][1]["cosine"] == 1
    assert q["scores"][1]["score_delta"] == 2


def test_reordering_and_ties_and_near_tie():
    r = request()
    baseline = analyze(r)
    r["reference_corpus"].reverse()
    r["candidate_corpus"].reverse()
    assert analyze(r) == baseline
    r["queries"][0]["vector"] = [1, 0]
    r["candidate_corpus"] = [row("b", [1.00001, 0]), row("a", [1, -1])]
    q = analyze(r)["queries"][0]
    assert q["reference_top_k"] == ["a"] and q["candidate_top_k"] == ["b"]
    assert q["scores"][0]["rank_delta"] == 1


def test_no_gold_and_effective_k():
    r = request()
    del r["queries"][0]["relevant_ids"]
    r["k"] = 5
    q = analyze(r)["queries"][0]
    assert q["effective_k"] == 2 and q["requested_k"] == 5
    assert q["reference_gold_recall_at_k"] is None and q["gold_denominator"] is None


@pytest.mark.parametrize(
    "mutate,reason",
    [
        (lambda r: r.update(version=True), "invalid_integer"),
        (lambda r: r.update(k="1"), "invalid_integer"),
        (
            lambda r: r["candidate"]["definition"].update(checkpoint_revision="other"),
            "space_mismatch",
        ),
        (lambda r: r["reference_corpus"][0].update(vector=[0, 0]), "zero_vector"),
        (lambda r: r["reference_corpus"][0].update(vector=[True, 1]), "invalid_number"),
        (lambda r: r["reference_corpus"][0].update(vector=[float("nan"), 1]), "invalid_number"),
        (lambda r: r["reference_corpus"][0].update(vector=[1]), "invalid_dimension"),
        (lambda r: r["reference_corpus"].append(r["reference_corpus"][0]), "invalid_count"),
        (lambda r: r["candidate_corpus"][0].update(input_digest="b" * 64), "binding_mismatch"),
        (lambda r: r["queries"][0].update(relevant_ids=["missing"]), "missing_gold_id"),
        (lambda r: r["candidate"].update(device="cpu"), "execution_mismatch"),
        (lambda r: r.update(evidence="EXECUTED"), "invalid_shape"),
    ],
)
def test_refusals(mutate, reason):
    r = request()
    mutate(r)
    with pytest.raises(ParityError, match=reason):
        analyze(r)


def test_duplicate_missing_and_unverified_identity():
    r = request()
    r["candidate_corpus"][0]["id"] = "a"
    with pytest.raises(ParityError, match="duplicate_id"):
        analyze(r)
    r = request()
    r["candidate_corpus"][0]["id"] = "c"
    with pytest.raises(ParityError, match="corpus_ids_mismatch"):
        analyze(r)
    r = request()
    for key in ("reference", "candidate"):
        r[key]["definition"]["checkpoint_sha256"] = None
    assert analyze(r)["space_identity"] == "INCOMPLETE_UNVERIFIED"


def test_extreme_numbers_and_unrepresentable_scores():
    r = request()
    r["queries"][0]["vector"] = [1e-200, 0]
    for corpus in ("reference_corpus", "candidate_corpus"):
        r[corpus][0]["vector"] = [1e200, 0]
        r[corpus][1]["vector"] = [1e200, 1e200]
    assert analyze(r)["queries"][0]["scores"][0]["reference_score"] == pytest.approx(1)
    r["queries"][0]["vector"] = [1e200, 0]
    with pytest.raises(ParityError, match="unrepresentable_score"):
        analyze(r)
    r["queries"][0]["vector"] = [1e-300, 0]
    for corpus in ("reference_corpus", "candidate_corpus"):
        for x in r[corpus]:
            x["vector"] = [1e-300, 0]
    with pytest.raises(ParityError, match="unrepresentable_score"):
        analyze(r)


def test_bounds_preflight():
    r = request()
    r["queries"] = [r["queries"][0]] * 129
    with pytest.raises(ParityError, match="invalid_count"):
        analyze(r)
    r = request()
    for key in ("reference", "candidate"):
        r[key]["definition"]["dimensions"] = 4096
    r["reference_corpus"] = [None] * 500
    r["candidate_corpus"] = [None] * 500
    with pytest.raises(ParityError, match="work_limit"):
        analyze(r)


def test_work_and_result_caps_before_row_parsing():
    r = request()
    r["queries"] = [None] * 128
    r["reference_corpus"] = [None] * 257
    r["candidate_corpus"] = [None] * 257
    with pytest.raises(ParityError, match="work_limit"):
        analyze(r)
    for key in ("reference", "candidate"):
        r[key]["definition"]["dimensions"] = 1024
    r["queries"] = [None] * 10
    r["reference_corpus"] = [None] * 400
    r["candidate_corpus"] = [None] * 400
    with pytest.raises(ParityError, match="work_limit"):
        analyze(r)


def test_cancellation_and_safe_error():
    r = request()
    r["queries"][0]["vector"] = [1e200, 1e200]
    for corpus in ("reference_corpus", "candidate_corpus"):
        for item in r[corpus]:
            item["vector"] = [1e200, -1e200]
    assert analyze(r)["queries"][0]["scores"][0]["reference_score"] == 0
    r["queries"][0]["id"] = "private value with spaces"
    with pytest.raises(ParityError) as exc:
        analyze(r)
    assert "private" not in str(exc.value)


def test_output_binds_rows_vectors_criteria_and_declared_space():
    original = request()
    result = analyze(original)
    fingerprint = result["input_fingerprint"]
    assert len(fingerprint) == 64
    assert result["queries"][0]["input_digest"] == D
    assert result["queries"][0]["representation_digest"] == D
    assert result["paired_vectors"][0]["input_digest"] == D
    assert result["paired_vectors"][0]["representation_digest"] == D

    for change in (
        lambda r: r["queries"][0]["vector"].__setitem__(0, 2),
        lambda r: r["reference_corpus"][0]["vector"].__setitem__(0, 2),
        lambda r: r["candidate_corpus"][0]["vector"].__setitem__(0, 2),
        lambda r: r["queries"][0].update(input_digest="b" * 64),
        lambda r: r["queries"][0].update(representation_digest="b" * 64),
        lambda r: r["queries"][0].update(relevant_ids=["b"]),
        lambda r: r.update(k=2),
        lambda r: r.update(cosine_tolerance=0.02),
        lambda r: r.update(score_tolerance=0.2),
    ):
        modified = copy.deepcopy(original)
        change(modified)
        assert analyze(modified)["input_fingerprint"] != fingerprint
    modified = copy.deepcopy(original)
    for corpus in ("reference_corpus", "candidate_corpus"):
        next(x for x in modified[corpus] if x["id"] == "a")["input_digest"] = "b" * 64
    assert analyze(modified)["input_fingerprint"] != fingerprint
    modified = copy.deepcopy(original)
    for key in ("reference", "candidate"):
        modified[key]["definition"]["checkpoint_revision"] = "r2"
    assert analyze(modified)["input_fingerprint"] != fingerprint


def test_fingerprint_permutations_and_storage_provenance():
    r = request()
    r["queries"].append(row("q2", [-1, 1], relevant_ids=["b", "a"]))
    expected = analyze(r)
    r["queries"].reverse()
    r["queries"][0]["relevant_ids"].reverse()
    r["reference_corpus"].reverse()
    r["candidate_corpus"].reverse()
    assert analyze(r) == expected
    assert expected["candidate_storage"] == {
        "required_target_dtype": "fp32",
        "supplied_dtype": None,
        "observed_dtype": None,
        "provenance": "unavailable",
    }
    assert "candidate_storage_dtype" not in expected
    assert expected["evidence"] == "SUPPLIED_UNVERIFIED"
    assert expected["qualification"] == "NOT_QUALIFIED"
    r["candidate_storage_dtype"] = "fp32"
    with pytest.raises(ParityError, match="invalid_shape"):
        analyze(r)


def test_extreme_vectors_do_not_claim_fp32_storage():
    r = request()
    r["queries"][0]["vector"] = [1e-200, 0]
    for corpus in ("reference_corpus", "candidate_corpus"):
        for item in r[corpus]:
            item["vector"] = [1e200, 0]
    result = analyze(r)
    assert result["queries"][0]["scores"][0]["candidate_score"] == pytest.approx(1)
    assert result["candidate_storage"]["supplied_dtype"] is None
    assert result["candidate_storage"]["observed_dtype"] is None
