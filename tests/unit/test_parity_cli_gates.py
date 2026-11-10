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


def test_trial_control_prerequisites_and_positive_roundtrip():
    import pytest
    from pydantic import ValidationError

    from slaif_raggedized_helper import __version__
    from slaif_raggedized_helper.qualification.spec import TrialSpec, trial_workload_fingerprint

    doc = {
        "spec_version": 1,
        "trial_id": "fixture",
        "workload": "repeated-parent",
        "purpose": "annotation",
        "parent": "parent",
        "suffixes": ["suffix"],
        "seed": 1,
        "warmups": 0,
        "repetitions": 1,
        "concurrency": 1,
        "code_version": __version__,
        "backend": "gateway",
        "declared_model": "fixture",
        "profile": None,
        "template_build_id": None,
        "budgets": {"deadline_seconds": 5, "max_dispatches": 1, "max_output_tokens_total": 10},
        "workload_fingerprint": trial_workload_fingerprint(
            parent="parent", suffixes=["suffix"], seed=1, warmups=0, repetitions=1
        ),
    }
    original = TrialSpec.model_validate(doc)
    assert TrialSpec.model_validate(original.model_dump()) == original
    for control, expected in {
        "context": "context-control implementation",
        "pair": "012",
        "batch": "007/012",
        "precision": "007/012",
        "seed_variation": "seed-variation implementation",
        "concurrency_policy": "ONLINE-02",
        "workload": "context controls",
        "concurrency": "ONLINE-02",
    }.items():
        changed = dict(doc, **{control: 2 if control == "concurrency" else "unsupported"})
        with pytest.raises(ValidationError) as error:
            TrialSpec.model_validate(changed)
        assert expected in str(error.value)
        assert "004-b" not in str(error.value)
