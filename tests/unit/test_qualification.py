"""Unit contracts for the finite qualification trial slice (OAP 004-a).

Strict trial spec/sample/result models, preflight consistency refusals,
the offline plan, the deterministic latency analysis (nearest-rank
quantile convention) and the machine-readable section 23.2 gate
projection. Synthetic fixtures only: no network, keys, GPU or model
downloads.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from slaif_raggedized_helper import __version__
from slaif_raggedized_helper.qualification import (
    GATES_DOC_PATH,
    analyze_trial,
    gate_projection,
    gate_projection_bytes,
    plan_trial,
    preflight_issues,
    quantile_nearest_rank,
    trial_workload_fingerprint,
)
from slaif_raggedized_helper.qualification.spec import TrialSpec
from slaif_raggedized_helper.config import RaggedizedConfig

REPO_ROOT = Path(__file__).resolve().parents[2]

PARENT = "Unit qualification parent fixture, constant bounded text."
SUFFIXES = [" Suffix A.", " Suffix B."]


def make_spec_dict(**overrides) -> dict:
    doc = {
        "spec_version": 1,
        "trial_id": "unit-trial-1",
        "workload": "repeated-parent",
        "purpose": "annotation",
        "parent": PARENT,
        "suffixes": list(SUFFIXES),
        "seed": 11,
        "warmups": 1,
        "repetitions": 2,
        "concurrency": 1,
        "code_version": __version__,
        "backend": "gateway",
        "declared_model": "unit-gw-model",
        "profile": None,
        "template_build_id": None,
        "budgets": {
            "deadline_seconds": 30,
            "max_dispatches": 10,
            "max_output_tokens_total": 30,
        },
        "workload_fingerprint": trial_workload_fingerprint(
            parent=PARENT, suffixes=list(SUFFIXES), seed=11, warmups=1,
            repetitions=2),
    }
    doc.update(overrides)
    return doc


def make_spec(**overrides) -> TrialSpec:
    return TrialSpec.model_validate(make_spec_dict(**overrides))


def make_config(**gen_kwargs) -> RaggedizedConfig:
    return RaggedizedConfig.model_validate({
        "schema_version": 1,
        "generator": {
            "route": {
                "base_url": "http://127.0.0.1:1/v1",
                "model": "unit-gw-model",
                "api": "v1-responses",
                "timeout_seconds": 5,
            },
            "context_expected_tokens": 1024,
            "output_reserve_tokens": 64,
            "deadline_seconds": 30,
            **gen_kwargs,
        },
    })


# ---------------------------------------------------------------------------
# spec strictness
# ---------------------------------------------------------------------------

class TestTrialSpecStrictness:
    def test_valid_spec_and_sequence(self):
        spec = make_spec()
        assert spec.sample_count == 3
        assert spec.per_sample_output_tokens == 10
        sequence = spec.declared_sequence()
        assert [item[1] for item in sequence] == ["warmup", "measured",
                                                  "measured"]
        assert [item[3] for item in sequence] == [0, 1, 0]
        assert sequence[0][2] == PARENT + " Suffix A."
        assert spec.declared_workload_fingerprint_matches()

    def test_unknown_field_refused(self):
        with pytest.raises(ValueError, match="Extra inputs are not permitted"):
            make_spec(extra_control=1)

    @pytest.mark.parametrize("control", [
        "context", "pair", "batch", "precision", "seed_variation",
        "concurrency_policy"])
    def test_unsupported_controls_refused_with_prerequisite(self, control):
        with pytest.raises(ValueError) as excinfo:
            make_spec(**{control: "on"})
        message = str(excinfo.value)
        assert control in message
        assert "prerequisite" in message  # named prerequisite, not silent

    def test_workload_must_be_repeated_parent(self):
        with pytest.raises(ValueError, match="repeated-parent"):
            make_spec(workload="pair")

    @pytest.mark.parametrize("purpose,error", [
        ("visual", "016"),
        ("answer", "014"),
    ])
    def test_purpose_annotation_only_with_prerequisite(self, purpose, error):
        with pytest.raises(ValueError) as excinfo:
            make_spec(purpose=purpose)
        assert error in str(excinfo.value)

    def test_concurrency_must_be_one(self):
        with pytest.raises(ValueError) as excinfo:
            make_spec(concurrency=2)
        message = str(excinfo.value)
        assert "concurrency must be 1" in message
        assert "ONLINE-02" in message

    @pytest.mark.parametrize("field,value", [
        ("max_dispatches", True),
        ("max_output_tokens_total", True),
        ("deadline_seconds", True),
    ])
    def test_bool_as_number_refused(self, field, value):
        doc = make_spec_dict()
        doc["budgets"][field] = value
        with pytest.raises(ValueError) as excinfo:
            TrialSpec.model_validate(doc)
        assert "boolean" in str(excinfo.value)

    @pytest.mark.parametrize("field", ["seed", "warmups", "repetitions"])
    def test_bool_as_number_refused_top_level(self, field):
        with pytest.raises(ValueError) as excinfo:
            make_spec(**{field: True})
        assert "boolean" in str(excinfo.value)

    @pytest.mark.parametrize("deadline", [0, -1, float("inf"),
                                          float("nan"), 86_401])
    def test_nonfinite_or_invalid_deadline_refused(self, deadline):
        doc = make_spec_dict()
        doc["budgets"]["deadline_seconds"] = deadline
        with pytest.raises(ValueError):
            TrialSpec.model_validate(doc)

    @pytest.mark.parametrize("overrides", [
        {"repetitions": 0},
        {"repetitions": 65},
        {"warmups": -1},
        {"warmups": 17},
        {"suffixes": []},
        {"suffixes": ["a"] * 9},
        {"suffixes": ["a" * 257]},
        {"parent": "p" * 4097},
        {"parent": ""},
        {"seed": -1},
        {"seed": 2**32},
        {"max_dispatches": 0 if False else None},
    ])
    def test_invalid_bounded_values_refused(self, overrides):
        doc = make_spec_dict()
        if overrides.get("max_dispatches") is None:
            del doc["budgets"]["max_dispatches"]
        doc.update({k: v for k, v in overrides.items()
                    if v is not None})
        with pytest.raises(ValueError):
            TrialSpec.model_validate(doc)

    @pytest.mark.parametrize("field,value", [
        ("max_dispatches", 0),
        ("max_dispatches", 4097),
        ("max_output_tokens_total", 0),
        ("max_output_tokens_total", 1_000_001),
    ])
    def test_budget_bounds_refused(self, field, value):
        doc = make_spec_dict()
        doc["budgets"][field] = value
        with pytest.raises(ValueError):
            TrialSpec.model_validate(doc)

    def test_workload_fingerprint_format_and_mismatch(self):
        with pytest.raises(ValueError, match="sha256"):
            make_spec(workload_fingerprint="sha256:zz")
        doc = make_spec_dict()
        doc["workload_fingerprint"] = trial_workload_fingerprint(
            parent=PARENT + "tampered", suffixes=list(SUFFIXES), seed=11,
            warmups=1, repetitions=2)
        spec = TrialSpec.model_validate(doc)
        assert not spec.declared_workload_fingerprint_matches()

    def test_output_total_must_cover_samples(self):
        # 3 samples need at least 3 output tokens total.
        with pytest.raises(ValueError, match="per sample"):
            make_spec(budgets={
                "deadline_seconds": 30, "max_dispatches": 10,
                "max_output_tokens_total": 2})

    def test_gateway_spec_cannot_carry_template_build_id(self):
        with pytest.raises(ValueError, match="direct native"):
            make_spec(template_build_id="build-x")

    def test_frozen_spec(self):
        spec = make_spec()
        with pytest.raises(Exception):
            spec.seed = 12  # frozen

    def test_per_sample_reservation_never_exceeds_total(self):
        spec = make_spec(budgets={
            "deadline_seconds": 30, "max_dispatches": 10,
            "max_output_tokens_total": 7})  # 3 samples -> 2,2,2 <= 7
        assert spec.per_sample_output_tokens == 2
        assert spec.per_sample_output_tokens * spec.sample_count <= \
            7


# ---------------------------------------------------------------------------
# preflight consistency refusals (all before dispatch)
# ---------------------------------------------------------------------------

class TestPreflight:
    def test_clean_preflight(self):
        assert preflight_issues(make_config(), make_spec()) == []

    def test_code_version_mismatch(self):
        spec = make_spec(code_version="9.9.9")
        issues = preflight_issues(make_config(), spec)
        assert any("code_version" in issue for issue in issues)

    def test_fingerprint_mismatch_refused(self):
        doc = make_spec_dict()
        doc["workload_fingerprint"] = trial_workload_fingerprint(
            parent="different parent", suffixes=list(SUFFIXES), seed=11,
            warmups=1, repetitions=2)
        issues = preflight_issues(make_config(), TrialSpec.model_validate(doc))
        assert any("workload_fingerprint" in issue for issue in issues)

    def test_unknown_profile_refused(self):
        config = RaggedizedConfig.model_validate({
            "schema_version": 1,
            "generator": make_config().generator.model_dump(),
            "profiles": [{"name": "other", "purpose": "online_rerank",
                          "device": "gpu", "dtype": "fp16"}],
        })
        issues = preflight_issues(config, make_spec(profile="missing"))
        assert any("profile" in issue for issue in issues)

    def test_known_profile_accepted(self):
        config = RaggedizedConfig.model_validate({
            "schema_version": 1,
            "generator": make_config().generator.model_dump(),
            "profiles": [{"name": "reranker", "purpose": "online_rerank",
                          "device": "gpu", "dtype": "fp16"}],
        })
        assert preflight_issues(config, make_spec(profile="reranker")) == []

    def test_gateway_route_missing(self):
        config = RaggedizedConfig.model_validate({
            "schema_version": 1,
            "generator": {
                "context_expected_tokens": 1024,
                "output_reserve_tokens": 64,
                "deadline_seconds": 30,
            },
        })
        issues = preflight_issues(config, make_spec())
        assert any("generator.route" in issue for issue in issues)

    def test_declared_model_mismatch(self):
        issues = preflight_issues(make_config(),
                                  make_spec(declared_model="other-model"))
        assert any("declared_model" in issue for issue in issues)

    def test_output_allowance_above_reserve_refused(self):
        config = make_config(output_reserve_tokens=5)
        # 3 samples, total 30 -> per-sample 10 > reserve 5
        issues = preflight_issues(config, make_spec())
        assert any("output_reserve_tokens" in issue for issue in issues)

    def test_direct_not_materialized(self):
        spec = make_spec(backend="direct")
        issues = preflight_issues(make_config(), spec)
        assert any("direct_generation" in issue for issue in issues)

    def test_direct_model_and_template_mismatch(self):
        config = RaggedizedConfig.model_validate({
            "schema_version": 1,
            "generator": {
                "context_expected_tokens": 1024,
                "output_reserve_tokens": 64,
                "deadline_seconds": 30,
            },
            "direct_generation": {
                "mode": "offline_diagnostic",
                "destination": {"base_url": "http://127.0.0.1:1"},
                "trusted_policy": "private_trusted",
                "model": "unit-native-model",
                "chat_template": None,
                "template_qualification": {
                    "template": None, "build_id": "build-1",
                    "method": "apply-template",
                    "recorded_at": "2026-11-10T00:00:00+00:00"},
                "max_output_tokens": 64,
                "deadline_seconds": 30,
            },
        })
        issues = preflight_issues(config, make_spec(
            backend="direct", declared_model="wrong",
            template_build_id="wrong-build"))
        assert any("declared_model" in issue for issue in issues)
        assert any("template_build_id" in issue for issue in issues)


# ---------------------------------------------------------------------------
# offline plan (zero model/HTTP/telemetry I/O)
# ---------------------------------------------------------------------------

class TestPlan:
    def test_clean_plan_not_run_zero_dispatch(self):
        code, doc = plan_trial(make_config(), make_spec())
        assert code == 0
        assert doc["status"] == "PLAN"
        assert doc["execution"].startswith("NOT_RUN")
        assert doc["zero_dispatch"] is True
        assert doc["workload"]["samples"] == 3
        assert doc["workload"]["workload_fingerprint_consistent"] is True
        assert doc["budgets"]["min_dispatches_per_sample"] == 1
        assert doc["budgets"]["min_dispatches_full_trial"] == 3
        assert doc["gates"]["real_trials"] == "NOT_RUN"

    def test_rejected_plan_with_exact_reasons(self):
        code, doc = plan_trial(make_config(), make_spec(declared_model="x"))
        assert code == 2
        assert doc["status"] == "PLAN_REJECTED"
        assert doc["reasons"]
        assert doc["zero_dispatch"] is True

    def test_direct_plan_min_calls(self):
        config = RaggedizedConfig.model_validate({
            "schema_version": 1,
            "generator": {
                "context_expected_tokens": 1024,
                "output_reserve_tokens": 64,
                "deadline_seconds": 30,
            },
            "direct_generation": {
                "mode": "offline_diagnostic",
                "destination": {"base_url": "http://127.0.0.1:1"},
                "trusted_policy": "private_trusted",
                "model": "unit-native-model",
                "chat_template": None,
                "template_qualification": {
                    "template": None, "build_id": "build-1",
                    "method": "apply-template",
                    "recorded_at": "2026-11-10T00:00:00+00:00"},
                "max_output_tokens": 64,
                "deadline_seconds": 30,
            },
        })
        code, doc = plan_trial(config, make_spec(
            backend="direct", declared_model="unit-native-model",
            template_build_id="build-1"))
        assert code == 0
        assert doc["budgets"]["min_dispatches_per_sample"] == 2
        assert doc["budgets"]["min_dispatches_full_trial"] == 6


# ---------------------------------------------------------------------------
# deterministic latency analysis (nearest-rank convention)
# ---------------------------------------------------------------------------

def sample(phase: str, outcome: str, wall: float | None = 0.1) -> dict:
    return {"phase": phase, "outcome": outcome, "wall_seconds": wall,
            "usage": {"input_tokens": None, "output_tokens": None,
                      "prefill_tokens": None, "cache_hit_tokens": None}}


class TestAnalysis:
    def test_quantile_nearest_rank(self):
        assert quantile_nearest_rank([], 50) is None
        assert quantile_nearest_rank([4.0], 95) == 4.0
        values = [1.0, 2.0, 3.0, 4.0]
        assert quantile_nearest_rank(values, 50) == 2.0
        assert quantile_nearest_rank(values, 95) == 4.0
        values10 = [float(value) for value in range(1, 11)]
        assert quantile_nearest_rank(values10, 50) == 5.0
        assert quantile_nearest_rank(values10, 95) == 10.0

    def test_zero_sample_sets_stay_null_and_cannot_qualify(self):
        summary = analyze_trial([], calls_by_kind={"model_dispatch": 0},
                                evidence_class="MOCK")
        for group in ("warmups", "measured"):
            latency = summary[group]["latency_seconds"]
            assert latency["n"] == 0
            assert latency["p50"] is None
            assert latency["p95"] is None
            assert latency["max"] is None
            assert summary["qualifying_pass"][group]["possible"] is False
            assert summary["qualifying_pass"][group]["reason"] == \
                "no_terminal_samples"

    def test_failed_and_unknown_samples_never_enter_latency(self):
        samples = [
            sample("measured", "terminal", 0.10),
            sample("measured", "failed", 9.9),
            sample("measured", "unknown_completion", 8.8),
            sample("measured", "refusal", 7.7),
            sample("measured", "incomplete", 6.6),
        ]
        summary = analyze_trial(samples,
                                calls_by_kind={"model_dispatch": 5},
                                evidence_class="CONFIGURED_UNVERIFIED")
        latency = summary["measured"]["latency_seconds"]
        assert latency["n"] == 1
        assert latency["p50"] == 0.10
        assert latency["max"] == 0.10
        assert summary["measured"]["samples_total"] == 5
        assert summary["measured"]["outcome_counts"] == {
            "failed": 1, "incomplete": 1, "refusal": 1, "terminal": 1,
            "unknown_completion": 1}
        # even with terminal samples this slice never qualifies
        assert summary["qualifying_pass"]["measured"]["possible"] is False

    def test_warmups_separate_from_measured(self):
        samples = [
            sample("warmup", "terminal", 1.0),
            sample("measured", "terminal", 2.0),
        ]
        summary = analyze_trial(samples,
                                calls_by_kind={"model_dispatch": 2},
                                evidence_class="MOCK")
        assert summary["warmups"]["latency_seconds"]["n"] == 1
        assert summary["warmups"]["latency_seconds"]["max"] == 1.0
        assert summary["measured"]["latency_seconds"]["n"] == 1
        assert summary["measured"]["latency_seconds"]["max"] == 2.0

    def test_analysis_is_pure_and_deterministic(self):
        base = [sample("warmup", "terminal", 0.5),
                sample("measured", "terminal", 0.25),
                sample("measured", "terminal", None),
                sample("measured", "failed", 9.9)]
        first = analyze_trial(copy.deepcopy(base),
                              calls_by_kind={"model_dispatch": 3},
                              evidence_class="MOCK")
        second = analyze_trial(copy.deepcopy(base),
                               calls_by_kind={"model_dispatch": 3},
                               evidence_class="MOCK")
        assert first == second
        # the terminal sample with a non-finite/None wall observation is
        # counted, never faked; the failed sample never enters latency
        assert second["measured"]["invalid_wall_observations"] == 1
        assert second["measured"]["latency_seconds"]["n"] == 1
        assert second["measured"]["latency_seconds"]["max"] == 0.25
        # timing boundary notes are present and explicit
        notes = first["timing_boundary_notes"]
        assert "NOT TTFT" in notes["native_template_time"]
        assert "stays null" in notes["gateway_prefill"]


# ---------------------------------------------------------------------------
# machine-readable section 23.2 gate projection
# ---------------------------------------------------------------------------

class TestGates:
    EXPECTED_IDS = {
        "GATEWAY-01", "GATEWAY-02", "GATEWAY-03",
        "DIRECT-01",
        "V100-MEM-01", "V100-MEM-02",
        "RERANK-01",
        "EMBED-01", "EMBED-02",
        "ONLINE-01", "ONLINE-02",
        "OPS-01", "OPS-02",
        "LICENSE-01",
    }

    def test_all_section_23_2_ids_present(self):
        doc = gate_projection()
        assert set(doc["gates"]) == self.EXPECTED_IDS
        assert doc["real_trials"] == "NOT_RUN"
        assert doc["live_target_authorization"] == "NONE"
        for gate in doc["gates"].values():
            assert gate["status"] == "NOT_RUN"

    def test_executable_entrypoints_are_text_repeated_parent_only(self):
        doc = gate_projection()
        executable = {gate_id for gate_id, gate in doc["gates"].items()
                      if gate["executable_in_this_slice"]}
        assert executable == {"GATEWAY-01", "GATEWAY-03", "DIRECT-01"}

    def test_license_gate_names_certifi_question(self):
        doc = gate_projection()
        assert "certifi" in doc["gates"]["LICENSE-01"]["pending"]

    def test_projection_is_deterministic_bytes(self):
        assert gate_projection_bytes() == gate_projection_bytes()
        assert json.loads(gate_projection_bytes()) == gate_projection()

    def test_committed_document_matches_canonical(self):
        committed = (REPO_ROOT / GATES_DOC_PATH).read_bytes()
        assert committed == gate_projection_bytes()
