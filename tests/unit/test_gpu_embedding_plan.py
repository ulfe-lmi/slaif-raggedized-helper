"""Planner preflight refuses without touching the prediction boundary."""

import pytest
from slaif_raggedized_helper import gpu_embedding_plan as plan


def test_bad_inputs_refuse_before_prediction(monkeypatch):
    def forbidden(*args):
        raise AssertionError("prediction should not run")

    monkeypatch.setattr(plan.bridge, "predict", forbidden)
    with pytest.raises(plan.PlanError, match="^GPU embedding plan refused$"):
        plan.build(None, b"", (), [], b"", "/", None, None, "", None, None)


def test_interruption_is_not_converted(monkeypatch):
    def interrupt(*args):
        raise KeyboardInterrupt

    monkeypatch.setattr(plan.source, "_preflight", interrupt)
    with pytest.raises(KeyboardInterrupt):
        plan.build(None, b"", (), [], b"", "/", None, None, "", None, None)
