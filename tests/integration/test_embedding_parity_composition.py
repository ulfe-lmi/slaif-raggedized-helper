from slaif_raggedized_helper.qualification.embedding_parity import analyze
from slaif_raggedized_helper.schema import EmbeddingDefinition, EmbeddingExecution


def test_schema_execution_composition_1024():
    definition = EmbeddingDefinition(
        model_name="synthetic",
        checkpoint_revision="r",
        checkpoint_sha256="a" * 64,
        tokenizer_revision="t",
        pooling="cls",
        normalize=True,
        dimensions=1024,
    )
    ref = EmbeddingExecution(definition=definition, device="cpu", dtype="fp32")
    candidate = EmbeddingExecution(definition=definition, device="gpu", dtype="fp16")
    row = {
        "id": "p",
        "input_digest": "b" * 64,
        "representation_digest": "c" * 64,
        "vector": [1.0] + [0.0] * 1023,
    }
    query = dict(row, id="q", relevant_ids=["p"])
    result = analyze(
        {
            "version": 1,
            "reference": ref,
            "candidate": candidate,
            "queries": [query],
            "reference_corpus": [row],
            "candidate_corpus": [row],
            "k": 1,
            "cosine_tolerance": 0,
            "score_tolerance": 0,
        }
    )
    assert result["space_fingerprint"] == definition.fingerprint()
    assert result["reference_execution_fingerprint"] == ref.fingerprint()
    assert result["candidate_execution_fingerprint"] == candidate.fingerprint()
    assert result["queries"][0]["candidate_gold_recall_at_k"] == 1
    assert result["evidence"] == "SUPPLIED_UNVERIFIED"
    assert result["queries"][0]["input_digest"] == "b" * 64
    assert result["paired_vectors"][0]["representation_digest"] == "c" * 64
    assert len(result["input_fingerprint"]) == 64
    assert result["candidate_storage"]["observed_dtype"] is None
