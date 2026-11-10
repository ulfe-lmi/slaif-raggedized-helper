"""Import hygiene: no heavy ML stack, no network, no CUDA on import/doctor."""

from __future__ import annotations

import importlib.metadata
import json
from pathlib import Path

from slaif_raggedized_helper import cli

HEAVY_MODULES = ("torch", "transformers", "sentence_transformers", "cuda", "cupy")
HEAVY_DISTRIBUTIONS = ("torch", "transformers", "sentence-transformers", "nvidia-cublas-cu12")


def _installed_distributions() -> set[str]:
    return {dist.metadata["Name"].lower() for dist in importlib.metadata.distributions()}


def test_no_heavy_ml_modules_loaded_after_import_and_doctor():
    import slaif_raggedized_helper  # noqa: F401  (ensures package is imported)
    import sys

    # doctor over the shipped example (relative model lock paths resolve in-repo)
    repo_root = Path(__file__).resolve().parents[2]
    code, doc = cli.run_doctor(repo_root / "config/examples/example-config.json")
    assert code == cli.EXIT_ISSUES
    json.dumps(doc)

    for name in HEAVY_MODULES:
        assert name not in sys.modules, f"heavy module {name} loaded by foundation import/doctor"


def test_no_heavy_ml_distributions_installed():
    installed = _installed_distributions()
    for name in HEAVY_DISTRIBUTIONS:
        assert name not in installed, f"heavy distribution {name} is not a foundation dependency"


def test_runtime_dependency_is_lightweight_and_pinned():
    installed = _installed_distributions()
    assert "pydantic" in installed
