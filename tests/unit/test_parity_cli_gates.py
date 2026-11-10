from pathlib import Path

from slaif_raggedized_helper.qualification.gates import gate_projection, gate_projection_bytes


def test_real_gate_scope_and_generated_document():
    projection = gate_projection()
    gates = projection["gates"]
    assert len(gates) == 14 and projection["live_target_authorization"] == "NONE"
    assert all(row["status"] == "NOT_RUN" for row in gates.values())
    assert "supplied vectors" in gates["EMBED-02"]["available_analysis"]
    assert "supplied scores" in gates["RERANK-01"]["available_analysis"]
    assert "012" in gates["RERANK-01"]["pending"]
    assert "015" in gates["V100-MEM-01"]["pending"]
    assert "own-process" in gates["V100-MEM-01"]["partial_instrumentation"]
    assert "019" in gates["ONLINE-01"]["pending"]
    assert "slot control" in gates["GATEWAY-03"]["pending"]
    assert Path("docs/benchmarks/qualification-gates.json").read_bytes() == gate_projection_bytes()
