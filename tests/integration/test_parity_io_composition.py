import json

import pytest

from slaif_raggedized_helper.qualification import parity_io as io
from slaif_raggedized_helper.qualification.rerank_parity import analyze_rerank_parity


def test_real_rerank_file_export_and_late_failure(tmp_path, monkeypatch):
    pair = {"pair_id": "p", "query_id": "q", "passage_id": "d",
            "query_digest": "a" * 64, "passage_digest": "b" * 64, "score": 0.5}
    side = {"definition": {"model": "m", "checkpoint": "c", "tokenizer": "t",
                           "pair_budget": 1280},
            "execution": {"device": "cpu", "precision": "fp32",
                          "provenance": "SUPPLIED_UNVERIFIED"}, "pairs": [pair]}
    source = tmp_path / "input"
    source.write_text(json.dumps({"version": 1, "reference": side, "candidate": side,
                                  "criteria": {"top_k": 1, "max_absolute_delta": 0,
                                               "min_top_k_overlap": 1}}))
    doc = io.read_document(source)
    out = tmp_path / "output"
    result = io.run_export(doc.document, analyze_rerank_parity, out)
    assert result["criteria_passed"]
    assert json.loads(out.read_bytes()) == result
    real_open = io.os.open

    def fail_output(path, flags, *args):
        if path == out:
            raise OSError("private-canary")
        return real_open(path, flags, *args)

    monkeypatch.setattr(io.os, "open", fail_output)
    with pytest.raises(io.ExportError) as error:
        io.run_export(doc.document, analyze_rerank_parity, out)
    assert error.value.evidence == result
    assert "private-canary" not in str(error.value)
