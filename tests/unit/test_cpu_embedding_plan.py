from dataclasses import replace

import pytest

from slaif_raggedized_helper import cpu_embedding_plan as plan, cpu_embedding_worker as cpu
from slaif_raggedized_helper import cpu_execution_contract as contract
import test_embedding_batch_plan


@pytest.fixture
def inputs(tmp_path):
    return test_embedding_batch_plan.inputs.__wrapped__(tmp_path)


def test_selection_and_mutated_policy_rejected_before_io(inputs, monkeypatch):
    calls = []

    def mark(name):
        def forbidden(*args, **kwargs):
            calls.append(name)
            raise ValueError("stopped at admission")

        return forbidden

    monkeypatch.setattr(contract, "prepare", mark("contract"))
    monkeypatch.setattr(plan.embedding_batch_plan, "build", mark("source"))
    monkeypatch.setattr(
        plan.embedding_batch_plan.retrieval_representation, "Session", mark("native")
    )
    monkeypatch.setattr(cpu.CPUEmbeddingWorker, "__init__", mark("model"))
    runtime = inputs[-1]
    # A valid selection reaches the intended contract admission boundary.
    with pytest.raises(plan.PlanError):
        plan.build(*inputs, runtime, worker_policy=cpu.Policy(max_rows=1))
    assert calls == ["contract"]
    calls.clear()
    with pytest.raises(plan.PlanError):
        plan.build(
            *inputs[:3], ["a", "b"], *inputs[4:], runtime, worker_policy=cpu.Policy(max_rows=1)
        )
    assert calls == [], "invalid row selection reached admission"
    policy = cpu.Policy()
    object.__setattr__(policy, "max_rows", True)
    with pytest.raises(plan.PlanError):
        plan.build(*inputs, runtime, worker_policy=policy)
    assert calls == [], "invalid policy reached admission"
    policy = replace(cpu.Policy(), max_rows=1)
    object.__setattr__(policy, "request_bytes", "x" * 1000000)
    with pytest.raises(plan.PlanError):
        plan.build(*inputs, runtime, worker_policy=policy)
    assert calls == [], "oversized policy reached admission"


def test_contract_refuses_before_admission(inputs, monkeypatch):
    monkeypatch.setattr(contract.embedding_space, "admit", lambda *a: pytest.fail("admission"))
    with pytest.raises(contract.ContractError):
        contract.prepare(*inputs[4:9], inputs[9], inputs[9], worker_policy=True)
