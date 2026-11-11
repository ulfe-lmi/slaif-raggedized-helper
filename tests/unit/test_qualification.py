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

import os
import time

import pytest
from pydantic import ValidationError

from slaif_raggedized_helper import __version__
from slaif_raggedized_helper.qualification import (
    GATES_DOC_PATH,
    TrialEvidence,
    TrialSample,
    analyze_trial,
    gate_projection,
    gate_projection_bytes,
    load_trial_spec_json,
    plan_trial,
    preflight_issues,
    quantile_nearest_rank,
    trial_workload_fingerprint,
    validate_trial_evidence,
)
from slaif_raggedized_helper.qualification.contracts import (
    StageMetric,
    derive_cache_input_consistency_counts,
)
from slaif_raggedized_helper.qualification.spec import TrialSpec
from slaif_raggedized_helper.qualification.specio import (
    MAX_SPEC_FILE_BYTES,
    REASON_ABSENT,
    REASON_INTEGER_OVERFLOW,
    REASON_NOT_JSON,
    REASON_NOT_REGULAR,
    REASON_NOT_UTF8,
    REASON_TOO_DEEP,
    REASON_TOO_LONG,
    SPEC_ERROR_MISSING,
)
from slaif_raggedized_helper.config import (
    RaggedizedConfig,
    safe_validation_errors,
)
from slaif_raggedized_helper.schema import fingerprint

REPO_ROOT = Path(__file__).resolve().parents[2]

PARENT = "Unit qualification parent fixture, constant bounded text."
SUFFIXES = [" Suffix A.", " Suffix B."]

# The observed per-trial backend binding used by the evidence fixtures:
# every KNOWN per-sample backend fingerprint must equal it (004-c);
# an absent binding stays null.
OBSERVED_BACKEND_FP = "sha256:" + "1" * 64


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

def sample(phase: str, outcome: str, wall: float | None = 0.1,
           ordinal: int = 0, timings: dict | None = None,
           usage: dict | None = None, error: str | None = None,
           suffix_index: int = 0, first_repetition: bool = False,
           **extra) -> dict:
    """One FULL strict-contract sample record (004-b).

    ``analyze_trial`` validates every sample against the TrialSample
    contract at the analysis boundary, so fixtures must be complete
    sample records, not loose dicts.
    """
    doc = {
        "ordinal": ordinal,
        "phase": phase,
        "first_repetition": first_repetition,
        "physical_state": "unknown",
        "suffix_index": suffix_index,
        "input_chars": 10,
        "input_fingerprint": fingerprint(
            {"kind": "trial-input", "ordinal": ordinal,
             "text": "fixture input"}),
        "outcome": outcome,
        "error": error,
        "adapter_reported_cycles": 1,
        "text_fingerprint": None,
        "content_fingerprint": None,
        "backend_fingerprint": OBSERVED_BACKEND_FP,
        "usage": usage or {"input_tokens": None, "output_tokens": None,
                           "prefill_tokens": None,
                           "cache_hit_tokens": None},
        "timings": timings or {"ttft_seconds": None,
                               "prefill_seconds": None,
                               "decode_seconds": None,
                               "total_seconds": None},
        "wall_seconds": wall,
    }
    doc.update(extra)
    return doc


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
# bounded spec file input (004-b criterion 1 / 004-F01)
# ---------------------------------------------------------------------------

class TestSpecInputReader:
    def _write(self, tmp_path, name, data: bytes) -> str:
        path = tmp_path / name
        path.write_bytes(data)
        return str(path)

    def test_valid_regular_file_roundtrip(self, tmp_path):
        data = json.dumps({"a": 1}).encode("utf-8")
        path = self._write(tmp_path, "spec.json", data)
        result, refusal = load_trial_spec_json(path)
        assert refusal is None
        assert result == {"a": 1}

    def test_absent_file_is_typed_missing(self, tmp_path):
        result, refusal = load_trial_spec_json(str(tmp_path / "nope.json"))
        assert result is None
        assert refusal.error == SPEC_ERROR_MISSING
        assert refusal.reason == REASON_ABSENT
        assert str(tmp_path) not in refusal.message  # no private-path echo

    def test_fifo_refused_without_blocking(self, tmp_path):
        fifo = tmp_path / "spec-fifo.json"
        os.mkfifo(str(fifo))  # no writer ever opens it
        started = time.monotonic()
        result, refusal = load_trial_spec_json(str(fifo))
        assert time.monotonic() - started < 5.0  # finite bound, no hang
        assert result is None
        assert refusal.reason == REASON_NOT_REGULAR

    def test_symlink_to_fifo_refused_on_opened_descriptor(self, tmp_path):
        fifo = tmp_path / "real-fifo"
        os.mkfifo(str(fifo))
        link = tmp_path / "spec-link.json"
        link.symlink_to(fifo)
        result, refusal = load_trial_spec_json(str(link))
        assert result is None
        assert refusal.reason == REASON_NOT_REGULAR

    def test_symlink_to_regular_file_is_admitted(self, tmp_path):
        real = tmp_path / "real.json"
        real.write_text('{"ok": true}', encoding="utf-8")
        link = tmp_path / "spec-link.json"
        link.symlink_to(real)
        result, refusal = load_trial_spec_json(str(link))
        assert refusal is None
        assert result == {"ok": True}

    def test_directory_refused(self, tmp_path):
        result, refusal = load_trial_spec_json(str(tmp_path))
        assert result is None
        assert refusal.reason == REASON_NOT_REGULAR

    def test_oversized_file_refused_at_bound(self, tmp_path):
        path = self._write(tmp_path, "big.json", b"{" + b" " * (MAX_SPEC_FILE_BYTES + 10))
        result, refusal = load_trial_spec_json(path)
        assert result is None
        assert refusal.reason == REASON_TOO_LONG

    def test_file_at_exact_bound_admitted(self, tmp_path):
        from slaif_raggedized_helper.qualification.specio import (
            read_spec_file)
        payload = b"{" + b" " * (MAX_SPEC_FILE_BYTES - 2) + b"}"
        assert len(payload) == MAX_SPEC_FILE_BYTES
        path = self._write(tmp_path, "exact.json", payload)
        raw, refusal = read_spec_file(path)
        assert refusal is None
        assert len(raw) == MAX_SPEC_FILE_BYTES

    def test_invalid_utf8_refused_before_fingerprinting(self, tmp_path):
        path = self._write(tmp_path, "bad-utf8.json", b"\xff\xfe{}")
        result, refusal = load_trial_spec_json(path)
        assert result is None
        assert refusal.reason == REASON_NOT_UTF8
        # invalid Unicode is refused, never replaced/truncated: the
        # refusal message is fixed safe text, not a decoded fragment
        assert "\xff" not in refusal.message

    def test_malformed_json_is_typed_with_line(self, tmp_path):
        path = self._write(tmp_path, "bad.json", b"\n{")
        result, refusal = load_trial_spec_json(path)
        assert result is None
        assert refusal.reason == REASON_NOT_JSON
        assert refusal.line == 2
        assert "line 2" in refusal.message

    def test_oversize_integer_is_typed_and_global_limit_untouched(self,
                                                                  tmp_path):
        import json as _json
        limit_before = getattr(_json.decoder, "MAX_INT_DIGITS", None)
        path = self._write(
            tmp_path, "int.json", b"{" + b'"seed":' + b"9" * 5000 + b"}")
        result, refusal = load_trial_spec_json(path)
        assert result is None
        assert refusal.reason == REASON_INTEGER_OVERFLOW
        # no process-global decoder-limit change as a workaround: the
        # interpreter's own decoder still enforces its fixed bound
        assert getattr(_json.decoder, "MAX_INT_DIGITS", None) == limit_before
        with pytest.raises(ValueError):
            _json.loads('{"a": ' + "9" * 5000 + '}')

    def test_deep_nesting_is_typed(self, tmp_path):
        # Within the 64 KiB file bound the C decoder of current
        # interpreters copes; the typed branch is exercised at the
        # parse boundary where the interpreter's recursion bound trips
        # (200k levels), and any interpreter that trips earlier on a
        # file still gets the same typed refusal (never a crash).
        from slaif_raggedized_helper.qualification.specio import (
            parse_spec_json)
        deep = "[" * 200_000 + "]" * 200_000
        result, refusal = parse_spec_json(deep)
        assert result is None
        assert refusal.reason == REASON_TOO_DEEP

    def test_refusal_messages_never_echo_the_path(self, tmp_path):
        path = self._write(tmp_path, "secret-name.json", b"\xff")
        result, refusal = load_trial_spec_json(path)
        assert refusal is not None
        assert "secret-name" not in refusal.message
        assert str(tmp_path) not in refusal.message


# ---------------------------------------------------------------------------
# strict sample/result contracts (004-b criterion 2 / 004-F02)
# ---------------------------------------------------------------------------

def _usage(**overrides) -> dict:
    doc = {"input_tokens": None, "output_tokens": None,
           "prefill_tokens": None, "cache_hit_tokens": None}
    doc.update(overrides)
    return doc


def _timings(**overrides) -> dict:
    doc = {"ttft_seconds": None, "prefill_seconds": None,
           "decode_seconds": None, "total_seconds": None}
    doc.update(overrides)
    return doc


class TestSampleContracts:
    def test_full_sample_roundtrip(self):
        doc = sample(
            "measured", "terminal", wall=0.125, ordinal=2,
            usage=_usage(input_tokens=11, output_tokens=5,
                         prefill_tokens=0, cache_hit_tokens=0),
            timings=_timings(prefill_seconds=0.02, decode_seconds=0.04,
                             total_seconds=0.06))
        model = TrialSample.model_validate(doc)
        assert model.model_dump() == doc
        # JSON roundtrip preserves the public dict compatibility
        assert TrialSample.model_validate(
            json.loads(json.dumps(doc))) == model

    def test_bool_as_number_refused_everywhere(self):
        doc = sample("measured", "terminal", wall=0.1,
                     usage=_usage(input_tokens=True),
                     timings=_timings(prefill_seconds=False))
        with pytest.raises(ValidationError) as excinfo:
            TrialSample.model_validate(doc)
        errors = {str(e["loc"][0]) + "." + str(e["loc"][1])
                  for e in excinfo.value.errors()}
        assert errors == {"usage.input_tokens",
                          "timings.prefill_seconds"}
        doc = sample("warmup", "terminal", wall=True)
        with pytest.raises(ValidationError) as excinfo:
            TrialSample.model_validate(doc)
        assert {tuple(e["loc"]) for e in excinfo.value.errors()} == {
            ("wall_seconds",)}

    def test_extra_and_missing_fields_refused(self):
        doc = sample("measured", "terminal")
        doc["injected"] = 1
        with pytest.raises(ValidationError):
            TrialSample.model_validate(doc)
        del doc["usage"]
        with pytest.raises(ValidationError):
            TrialSample.model_validate(doc)

    def test_malformed_outcome_and_fingerprints_refused(self):
        doc = sample("measured", "terminal")
        doc["outcome"] = "qualified"
        with pytest.raises(ValidationError):
            TrialSample.model_validate(doc)
        doc = sample("measured", "terminal")
        doc["input_fingerprint"] = "sha256:zz"
        with pytest.raises(ValidationError):
            TrialSample.model_validate(doc)

    def test_numeric_shapes_refused(self):
        doc = sample("measured", "terminal",
                     usage=_usage(input_tokens=-1))
        with pytest.raises(ValidationError):
            TrialSample.model_validate(doc)
        doc = sample("measured", "terminal",
                     timings=_timings(decode_seconds=float("inf")))
        with pytest.raises(ValidationError):
            TrialSample.model_validate(doc)
        doc = sample("measured", "terminal", wall=-0.5)
        with pytest.raises(ValidationError):
            TrialSample.model_validate(doc)

    def test_known_zero_and_all_null_preserved(self):
        doc = sample("measured", "terminal",
                     usage=_usage(input_tokens=0, output_tokens=0),
                     timings=_timings(prefill_seconds=0.0,
                                      decode_seconds=0.0))
        model = TrialSample.model_validate(doc)
        assert model.usage.input_tokens == 0
        assert model.timings.prefill_seconds == 0.0
        empty = sample("measured", "terminal",
                       usage=_usage(), timings=_timings())
        model = TrialSample.model_validate(empty)
        assert model.usage.input_tokens is None
        assert model.timings.decode_seconds is None

    def test_contradictory_cache_facts_are_valid_raw_facts(self):
        # reported cache 999 > input 5 stays a VALID raw fact; the
        # invalidity label lives in the accounting section, never in a
        # mutation of the sample value
        doc = sample("measured", "terminal",
                     usage=_usage(input_tokens=5, cache_hit_tokens=999))
        model = TrialSample.model_validate(doc)
        assert model.usage.cache_hit_tokens == 999
        assert model.usage.input_tokens == 5


def _evidence_doc(samples, *, calls_by_kind, evidence_class="MOCK",
                  backend="gateway", max_dispatches=10,
                  stop_reason=None, status=None,
                  declared_warmups=None, declared_repetitions=None,
                  max_output_tokens_total=30, per_sample_output_tokens=10,
                  reservation_total=None, reservation_per_sample=None) -> dict:
    """Build a strict-contract evidence envelope for tests.

    ``declared_warmups``/``declared_repetitions`` default to the
    recorded split; an incomplete/not-run envelope declares the FULL
    sequence while recording only the executed prefix.

    ``per_sample_output_tokens``/``reservation_total``/
    ``reservation_per_sample`` default to the consistent declared
    budget (floor even share over the declared scheduled sample
    count); pass explicit values to build a contradictory document.
    """
    analysis = analyze_trial(samples, calls_by_kind=calls_by_kind,
                             evidence_class=evidence_class)
    recorded_warmups = sum(1 for s in samples if s["phase"] == "warmup")
    recorded_repetitions = sum(
        1 for s in samples if s["phase"] == "measured")
    warmups = (recorded_warmups if declared_warmups is None
               else declared_warmups)
    repetitions = (recorded_repetitions if declared_repetitions is None
                   else declared_repetitions)
    if reservation_total is None:
        reservation_total = max_output_tokens_total
    if reservation_per_sample is None:
        reservation_per_sample = per_sample_output_tokens
    attempted = sum(calls_by_kind.values())
    if status is None:
        if len(samples) == warmups + repetitions:
            status = "complete"
        elif attempted == 0:
            status = "not_run"
        else:
            status = "incomplete"
    suffixes = [" Suffix A.", " Suffix B."]
    doc = {
        "qualification": "trial",
        "runner": "qualification-trial",
        "version": 1,
        "trial_id": "unit-evidence-trial",
        "backend": backend,
        "status": status,
        "stop_reason": stop_reason,
        "evidence_class": evidence_class,
        "target_type": "synthetic-owned-fixture",
        "target_type_note": "owned fixture note",
        "qualification_status": "NOT_QUALIFIED",
        "qualification_note": "execution status only, never qualification",
        "workload": {
            "kind": "repeated-parent",
            "parent_chars": 20,
            "parent_fingerprint": fingerprint(
                {"kind": "trial-parent", "text": "unit parent"}),
            "suffixes": [
                {"index": i, "chars": len(t),
                 "fingerprint": fingerprint(
                     {"kind": "trial-suffix", "text": t})}
                for i, t in enumerate(suffixes)],
            "samples": warmups + repetitions,
            "warmups": warmups,
            "repetitions": repetitions,
            "concurrency": 1,
            "seed": 11,
            "seed_semantics": "bound identity only",
            "workload_fingerprint": trial_workload_fingerprint(
                parent="unit parent", suffixes=suffixes, seed=11,
                warmups=warmups, repetitions=repetitions),
            "workload_fingerprint_verified_pre_dispatch": True,
            "cache_control": "none",
        },
        "budgets": {
            "deadline_seconds": 30,
            "max_dispatches": max_dispatches,
            "max_output_tokens_total": max_output_tokens_total,
            "per_sample_output_tokens": per_sample_output_tokens,
            "elapsed_seconds": 0.1,
            "elapsed_seconds_scope": "trial only",
            "semantics": "one absolute deadline, one shared allowance",
        },
        "identities": {
            "declared": {
                "code_version": "0.164.0",
                "backend": backend,
                "model": "unit-gw-model",
                "profile": None,
                "purpose": "annotation",
                "template_build_id": None,
                "endpoint_fingerprint": fingerprint(
                    {"kind": "trial-endpoint",
                     "endpoint": "fixture"}),
            },
            "observed": {
                "backend_fingerprint": OBSERVED_BACKEND_FP,
                "runtime_identity": "unverified",
                "model_runtime_identity": "unverified",
                "tokenizer_identity": "unavailable",
            },
            "identity_note": "declared verified pre-dispatch",
        },
        "credentials": {
            "api_key_ref": {"kind": "synthetic-canary"},
            "resolved": True,
            "note": "owned fixture canary",
        },
        "requests": samples,
        "transport_boundary": {
            "attempted_calls": attempted,
            "calls_by_kind": dict(calls_by_kind),
            "responses_received": attempted,
            "ambiguous_dispatches": 0,
            "pre_dispatch_failures": 0,
            "remaining_dispatches": max_dispatches - attempted,
        },
        "accounting": {
            "output_reservation": {
                "total": reservation_total,
                "per_sample": reservation_per_sample,
                "semantics": "reserved before dispatch",
            },
            "cache_input_consistency": {
                "consistent_samples": 0,
                "contradictory_samples": 0,
                "uncheckable_samples": 0,
                "note": "raw facts only",
            },
        },
        "analysis": analysis,
        "gates": {
            "machine_readable_document": GATES_DOC_PATH,
            "executable_in_this_slice": ["GATEWAY-01", "GATEWAY-03",
                                         "DIRECT-01"],
            "real_trials": "NOT_RUN",
            "note": "execution status only",
        },
    }
    return doc


def _valid_evidence() -> dict:
    samples = [
        sample("warmup", "terminal", wall=0.5, ordinal=0, suffix_index=0,
               first_repetition=False),
        sample("measured", "terminal", wall=0.25, ordinal=1, suffix_index=1,
               first_repetition=True),
        sample("measured", "terminal", wall=0.75, ordinal=2, suffix_index=0,
               first_repetition=False),
    ]
    return _evidence_doc(samples, calls_by_kind={"model_dispatch": 3})


class TestEvidenceEnvelope:
    def test_valid_envelope_passes_full_validation(self):
        doc = _valid_evidence()
        model = validate_trial_evidence(doc)
        assert isinstance(model, TrialEvidence)
        assert model.analysis == TrialEvidence.model_validate(doc).analysis

    def test_forged_analysis_refused(self):
        doc = _valid_evidence()
        doc["analysis"]["measured"]["latency_seconds"]["p50"] = 99.0
        with pytest.raises((ValidationError, ValueError),
                           match="pure recomputation|quartile|p50"):
            validate_trial_evidence(doc)

    def test_drifted_group_count_refused(self):
        doc = _valid_evidence()
        doc["analysis"]["measured"]["samples_total"] = 5
        with pytest.raises(ValidationError):
            validate_trial_evidence(doc)

    def test_tampered_identity_refused(self):
        doc = _valid_evidence()
        doc["identities"]["observed"]["runtime_identity"] = "verified"
        with pytest.raises(ValidationError):
            TrialEvidence.model_validate(doc)

    def test_ordinal_and_phase_mismatch_refused(self):
        doc = _valid_evidence()
        doc["requests"][1]["ordinal"] = 9
        with pytest.raises(ValidationError):
            TrialEvidence.model_validate(doc)
        doc = _valid_evidence()
        doc["requests"][2]["phase"] = "warmup"
        with pytest.raises(ValidationError):
            TrialEvidence.model_validate(doc)

    def test_status_and_accounting_relations_enforced(self):
        doc = _valid_evidence()
        doc["status"] = "incomplete"  # complete with no stop reason drift
        with pytest.raises(ValidationError):
            TrialEvidence.model_validate(doc)
        doc = _valid_evidence()
        doc["stop_reason"] = "budget_exhausted_deadline"
        with pytest.raises(ValidationError):
            TrialEvidence.model_validate(doc)
        doc = _valid_evidence()
        doc["transport_boundary"]["remaining_dispatches"] = 99
        with pytest.raises(ValidationError):
            TrialEvidence.model_validate(doc)

    def test_not_run_envelope_with_zero_dispatch_is_valid(self):
        doc = _evidence_doc([], calls_by_kind={}, max_dispatches=4,
                            status="not_run", declared_warmups=1,
                            declared_repetitions=2)
        assert doc["status"] == "not_run"
        assert doc["workload"]["samples"] == 3
        validate_trial_evidence(doc)

    def test_incomplete_prefix_envelope_is_valid(self):
        # Declared 3 (1 warmup + 2 measured), recorded 1 after a
        # deadline stop: requests are the exact leading prefix, the
        # declared workload keeps the full sequence, and the analysis
        # groups reflect the recorded split.
        samples = [sample("warmup", "terminal", wall=0.5, ordinal=0)]
        doc = _evidence_doc(
            samples, calls_by_kind={"model_dispatch": 1}, max_dispatches=4,
            status="incomplete", stop_reason="budget_exhausted_deadline",
            declared_warmups=1, declared_repetitions=2)
        assert doc["workload"]["samples"] == 3
        assert len(doc["requests"]) == 1
        assert doc["analysis"]["measured"]["samples_total"] == 0
        validate_trial_evidence(doc)

    def test_incomplete_requires_stop_reason_and_tail(self):
        samples = [
            sample("warmup", "terminal", wall=0.5, ordinal=0),
            sample("measured", "terminal", wall=0.25, ordinal=1,
                   suffix_index=1, first_repetition=True),
            sample("measured", "terminal", wall=0.75, ordinal=2,
                   suffix_index=0, first_repetition=False),
        ]
        doc = _evidence_doc(samples, calls_by_kind={"model_dispatch": 3},
                            status="incomplete", stop_reason=None)
        with pytest.raises(ValidationError, match="stop reason"):
            TrialEvidence.model_validate(doc)
        # incomplete with the FULL sequence recorded is contradictory
        doc = _evidence_doc(samples, calls_by_kind={"model_dispatch": 3},
                            status="incomplete",
                            stop_reason="budget_exhausted_deadline")
        with pytest.raises(ValidationError, match="unrecorded tail"):
            TrialEvidence.model_validate(doc)

    def test_not_run_envelope_may_carry_zero_dispatch_refusals(self):
        # deterministic adapter preflight refusal: one recorded refusal
        # sample, zero transport calls, honest not_run
        samples = [sample("warmup", "refusal", wall=0.0, ordinal=0,
                          error="FIXED_SAFE_ERROR_CLASS")]
        doc = _evidence_doc(samples, calls_by_kind={},
                            status="not_run", declared_warmups=1,
                            declared_repetitions=2)
        doc["credentials"] = {"api_key_ref": None, "resolved": None}
        validate_trial_evidence(doc)


# ---------------------------------------------------------------------------
# 004-c cross-field bindings (004B-F01) and metric completeness (004B-F02)
# ---------------------------------------------------------------------------

class TestCrossFieldBindings:
    """The canonical full validator binds every duplicated fact.

    Each test flips ONE field of a valid envelope and requires the
    refusal; the unaltered envelope stays a positive control. Internal
    consistency is proven — never that the declared metadata is true
    or that imported JSON was executed here.
    """

    def test_unaltered_envelope_is_the_positive_control(self):
        validate_trial_evidence(_valid_evidence())

    def test_analysis_call_count_conflicts_with_actual_ledger_refused(self):
        # 004B-F01: the recomputation is driven by the ACTUAL
        # transport-boundary ledger, not the analysis's own copy — a
        # duplicated count that drifts from the ledger is refused.
        doc = _valid_evidence()
        doc["analysis"]["transport_calls_by_kind"]["model_dispatch"] += 1
        with pytest.raises((ValidationError, ValueError),
                           match="pure recomputation"):
            validate_trial_evidence(doc)
        # the reverse drift (ledger intact, analysis under-counts) too
        doc = _valid_evidence()
        doc["analysis"]["transport_calls_by_kind"]["model_dispatch"] -= 1
        with pytest.raises((ValidationError, ValueError),
                           match="pure recomputation"):
            validate_trial_evidence(doc)

    def test_envelope_backend_conflicts_with_declared_backend_refused(self):
        doc = _valid_evidence()
        doc["backend"] = "direct"
        with pytest.raises(ValidationError, match="declared backend"):
            TrialEvidence.model_validate(doc)

    def test_sample_backend_fp_conflicts_with_observed_binding_refused(self):
        doc = _valid_evidence()
        doc["requests"][0]["backend_fingerprint"] = "sha256:" + "0" * 64
        with pytest.raises(ValidationError,
                           match="backend fingerprint conflicts"):
            TrialEvidence.model_validate(doc)

    def test_null_sample_backend_fp_stays_allowed(self):
        # an absent binding stays null, never guessed — failure
        # samples without a declared binding remain valid
        doc = _valid_evidence()
        doc["requests"][0]["backend_fingerprint"] = None
        validate_trial_evidence(doc)

    def test_target_type_conflicts_with_evidence_class_refused(self):
        doc = _valid_evidence()  # MOCK / synthetic-owned-fixture
        doc["target_type"] = "unverified"
        with pytest.raises(ValidationError, match="consistent with the evidence class"):
            TrialEvidence.model_validate(doc)
        doc = _valid_evidence()
        doc["evidence_class"] = "CONFIGURED_UNVERIFIED"
        with pytest.raises(ValidationError, match="consistent with the evidence class"):
            TrialEvidence.model_validate(doc)

    def test_configured_unverified_pair_is_the_other_valid_pair(self):
        doc = _valid_evidence()
        doc["evidence_class"] = "CONFIGURED_UNVERIFIED"
        doc["target_type"] = "unverified"
        doc["analysis"] = analyze_trial(
            [s.model_dump() for s in
             TrialEvidence.model_validate(_valid_evidence()).requests],
            calls_by_kind={"model_dispatch": 3},
            evidence_class="CONFIGURED_UNVERIFIED")
        validate_trial_evidence(doc)

    def test_output_reservation_conflicts_with_budget_refused(self):
        doc = _valid_evidence()
        doc["accounting"]["output_reservation"]["total"] += 1
        with pytest.raises(ValidationError,
                           match="reservation total must equal"):
            TrialEvidence.model_validate(doc)
        doc = _valid_evidence()
        doc["accounting"]["output_reservation"]["per_sample"] += 1
        with pytest.raises(ValidationError,
                           match="reservation per-sample must equal"):
            TrialEvidence.model_validate(doc)

    def test_per_sample_must_be_even_share_of_declared_count(self):
        # declared 3 samples, total 30 -> share 10; a share computed
        # from the SHORTER recorded prefix (1 sample -> 30) refuses
        samples = [sample("warmup", "terminal", wall=0.5, ordinal=0)]
        doc = _evidence_doc(samples, calls_by_kind={"model_dispatch": 1},
                            status="incomplete",
                            stop_reason="budget_exhausted_deadline",
                            declared_warmups=1, declared_repetitions=2,
                            per_sample_output_tokens=30)
        with pytest.raises(ValidationError,
                           match="floor even share"):
            TrialEvidence.model_validate(doc)
        # the declared-count share (10) with the incomplete recorded
        # prefix stays valid
        doc = _evidence_doc(samples, calls_by_kind={"model_dispatch": 1},
                            status="incomplete",
                            stop_reason="budget_exhausted_deadline",
                            declared_warmups=1, declared_repetitions=2)
        validate_trial_evidence(doc)

    def test_cache_consistency_claim_without_reported_cache_refused(self):
        doc = _valid_evidence()  # no sample reports cache_hit_tokens
        doc["accounting"]["cache_input_consistency"]["consistent_samples"] = 1
        with pytest.raises(ValidationError,
                           match="pure derivation from the actually recorded raw usage"):
            TrialEvidence.model_validate(doc)

    def test_cache_consistency_counts_derived_from_recorded_usage(self):
        # raw facts: contradictory cache 999 > input 5 stays a VALID
        # sample value; the label must equal the pure derivation
        doc = _valid_evidence()
        doc["requests"][0]["usage"] = _usage(input_tokens=5,
                                             cache_hit_tokens=999)
        doc["accounting"]["cache_input_consistency"] = {
            "consistent_samples": 0,
            "contradictory_samples": 1,
            "uncheckable_samples": 0,
            "note": "raw facts only",
        }
        validate_trial_evidence(doc)
        # uncheckable: known cache, missing input
        doc = _valid_evidence()
        doc["requests"][0]["usage"] = _usage(input_tokens=None,
                                             cache_hit_tokens=3)
        doc["accounting"]["cache_input_consistency"] = {
            "consistent_samples": 0,
            "contradictory_samples": 0,
            "uncheckable_samples": 1,
            "note": "raw facts only",
        }
        validate_trial_evidence(doc)
        # consistent: cache 3 <= input 12
        doc = _valid_evidence()
        doc["requests"][0]["usage"] = _usage(input_tokens=12,
                                             cache_hit_tokens=3)
        doc["accounting"]["cache_input_consistency"] = {
            "consistent_samples": 1,
            "contradictory_samples": 0,
            "uncheckable_samples": 0,
            "note": "raw facts only",
        }
        validate_trial_evidence(doc)


class TestCacheDerivation:
    """The shared pure derivation over recorded raw usage (004-c)."""

    @staticmethod
    def _s(input_tokens, cache_hit_tokens):
        return {"usage": {"input_tokens": input_tokens,
                          "output_tokens": None, "prefill_tokens": None,
                          "cache_hit_tokens": cache_hit_tokens}}

    def test_all_unknown_is_all_zero(self):
        assert derive_cache_input_consistency_counts(
            [self._s(None, None), self._s(5, None)]) == (0, 0, 0)

    def test_known_zero_cache_is_a_fact(self):
        # reported 0 <= reported 0 is CONSISTENT (a known zero is a
        # measurement, not unknown)
        assert derive_cache_input_consistency_counts(
            [self._s(0, 0)]) == (1, 0, 0)

    def test_known_cache_with_unknown_input_is_uncheckable(self):
        assert derive_cache_input_consistency_counts(
            [self._s(None, 3)]) == (0, 0, 1)

    def test_contradictory_counters_are_raw_facts(self):
        assert derive_cache_input_consistency_counts(
            [self._s(3, 5)]) == (0, 1, 0)

    def test_within_relation_is_consistent(self):
        assert derive_cache_input_consistency_counts(
            [self._s(12, 3), self._s(None, None)]) == (1, 0, 0)


class TestQuartileCompleteness:
    """n=0 iff all quartiles null; n>0 requires EVERY quartile."""

    @staticmethod
    def _stage(**over):
        doc = dict(n=2, min=1.0, p50=1.0, p95=2.0, max=2.0, missing=0,
                   invalid_observations=0, source="owned-fixture")
        doc.update(over)
        return doc

    def test_valid_quartiles_admitted(self):
        StageMetric.model_validate(self._stage())
        StageMetric.model_validate(self._stage(n=0, min=None, p50=None,
                                               p95=None, max=None))

    @pytest.mark.parametrize("field", ["min", "p50", "p95", "max"])
    def test_positive_count_partial_quartile_refused(self, field):
        with pytest.raises(ValidationError,
                           match="every quartile present"):
            StageMetric.model_validate(self._stage(**{field: None}))

    @pytest.mark.parametrize("over", [
        {"min": 2.0, "p50": 1.0},
        {"p50": 3.0, "p95": 2.0},
        {"p95": 3.0, "max": 2.0},
    ])
    def test_malformed_ordering_refused(self, over):
        with pytest.raises(ValidationError, match="ordered"):
            StageMetric.model_validate(self._stage(**over))

    @pytest.mark.parametrize("field", ["min", "p50", "p95", "max"])
    @pytest.mark.parametrize("value", [float("inf"), -1.0])
    def test_nonfinite_or_negative_quartile_refused(self, field, value):
        with pytest.raises(ValidationError):
            StageMetric.model_validate(self._stage(**{field: value}))

    def test_bool_sample_count_refused(self):
        with pytest.raises(ValidationError):
            StageMetric.model_validate(self._stage(n=True))

    def test_zero_count_with_present_quartile_refused(self):
        with pytest.raises(ValidationError, match="all-null"):
            StageMetric.model_validate(self._stage(n=0))


class TestSpecUnicodeAdmission:
    """Invalid decoded workload Unicode refuses at spec admission."""

    def _spec(self, **overrides) -> dict:
        # Matched-fingerprint fixture: the declared fingerprint always
        # tracks the EXACT declared material, so a refusal can only
        # come from the decoded-Unicode admission (not a fingerprint
        # mismatch).
        parent = overrides.get("parent", PARENT)
        suffixes = list(overrides.get("suffixes", list(SUFFIXES)))
        doc = make_spec_dict(parent=parent, suffixes=list(suffixes))
        doc["workload_fingerprint"] = trial_workload_fingerprint(
            parent=parent, suffixes=list(suffixes), seed=11, warmups=1,
            repetitions=2)
        return doc

    def test_lone_high_surrogate_parent_refused(self):
        doc = self._spec(parent="\ud800")
        with pytest.raises(ValidationError) as excinfo:
            TrialSpec.model_validate(doc)
        errors = excinfo.value.errors()
        assert [tuple(e["loc"]) for e in errors] == [("parent",)]
        assert "invalid decoded Unicode" in errors[0]["msg"]
        # fixed safe message: the input value is never echoed
        assert "\ud800" not in str(errors[0]["msg"])

    def test_lone_low_surrogate_first_suffix_refused(self):
        doc = self._spec(suffixes=["\udfff", " Suffix B."])
        with pytest.raises(ValidationError) as excinfo:
            TrialSpec.model_validate(doc)
        errors = excinfo.value.errors()
        assert [tuple(e["loc"]) for e in errors] == [("suffixes",)]
        assert "invalid decoded Unicode" in errors[0]["msg"]

    @pytest.mark.parametrize("parent,suffixes", [
        ("Owned \U0001f600 \u0161\u010d\u0360.", [" Suffix A.", " Suffix B."]),
        ("Valid astral \U0001f1e7\U0001f1e7 text", [" A"]),
    ])
    def test_valid_unicode_admitted_unchanged(self, parent, suffixes):
        doc = self._spec(parent=parent, suffixes=list(suffixes))
        spec = TrialSpec.model_validate(doc)
        assert spec.parent == parent
        assert spec.suffixes == list(suffixes)
        # the fingerprint is computed from the exact admitted text
        assert spec.declared_workload_fingerprint_matches()

    def test_refusal_performs_no_replacement_or_truncation(self):
        doc = self._spec(parent="canary-parent\ud800-tail")
        with pytest.raises(ValidationError) as excinfo:
            TrialSpec.model_validate(doc)
        # the fixed safe message and the CLI's rendered error string
        # (safe_validation_errors) never echo the input value
        assert "canary-parent" not in excinfo.value.errors()[0]["msg"]
        rendered = safe_validation_errors(excinfo.value)
        assert "canary-parent" not in rendered
        assert "\ud800" not in rendered


# ---------------------------------------------------------------------------
# available-stage summaries (004-b criterion 3 / 004-F03)
# ---------------------------------------------------------------------------

class TestStageSummaries:
    def test_hand_computed_stage_quantiles(self):
        # 15 measured terminal samples with known finite values:
        # wall 1..15, decode 0.1*i, prefill 0.02*i
        samples = [
            sample("measured", "terminal", wall=float(i), ordinal=i,
                   suffix_index=i % 2,
                   first_repetition=(i == 0),
                   timings=_timings(prefill_seconds=0.02 * i,
                                    decode_seconds=0.1 * i,
                                    total_seconds=0.125 * i))
            for i in range(1, 16)
        ]
        summary = analyze_trial(samples,
                                calls_by_kind={"model_dispatch": 15},
                                evidence_class="MOCK")
        stage = summary["measured"]["stage_metrics"]
        wall = stage["caller_wall_seconds"]
        assert wall["n"] == 15
        assert wall["min"] == 1.0
        # nearest rank: p50 -> ceil(0.5*15)=8 -> 8.0; p95 -> ceil(14.25)=15
        assert wall["p50"] == 8.0
        assert wall["p95"] == 15.0
        assert wall["max"] == 15.0
        assert wall["missing"] == 0
        assert wall["invalid_observations"] == 0
        decode = stage["decode_seconds"]
        assert decode["n"] == 15
        assert decode["p50"] == 0.8
        assert decode["max"] == 1.5
        prefill = stage["prefill_seconds"]
        assert prefill["n"] == 15
        assert prefill["max"] == 0.3
        total = stage["model_total_seconds"]
        assert total["n"] == 15
        assert total["p95"] == 1.875
        assert total["max"] == 1.875
        # native TTFT is never reported: unavailable, not 0
        ttft = stage["ttft_seconds"]
        assert ttft["n"] == 0
        assert ttft["min"] is None and ttft["max"] is None
        assert ttft["missing"] == 15

    def test_gateway_prefill_stays_unavailable_not_zero(self):
        samples = [sample("measured", "terminal", wall=0.5, ordinal=0)]
        summary = analyze_trial(samples,
                                calls_by_kind={"model_dispatch": 1},
                                evidence_class="CONFIGURED_UNVERIFIED")
        stage = summary["measured"]["stage_metrics"]
        for key in ("prefill_seconds", "ttft_seconds"):
            assert stage[key]["n"] == 0
            assert stage[key]["min"] is None
            assert stage[key]["p50"] is None
            assert stage[key]["max"] is None
            assert stage[key]["missing"] == 1

    def test_known_zero_counts_missing_is_absent(self):
        samples = [
            sample("measured", "terminal", wall=0.5, ordinal=0,
                   suffix_index=0,
                   timings=_timings(decode_seconds=0.0,
                                    total_seconds=0.0)),
            sample("measured", "terminal", wall=0.25, ordinal=1,
                   suffix_index=1,
                   timings=_timings()),  # missing: absent, not zero
        ]
        summary = analyze_trial(samples,
                                calls_by_kind={"model_dispatch": 2},
                                evidence_class="MOCK")
        decode = summary["measured"]["stage_metrics"]["decode_seconds"]
        assert decode["n"] == 1
        assert decode["min"] == 0.0 and decode["max"] == 0.0
        assert decode["missing"] == 1
        assert decode["invalid_observations"] == 0

    def test_failed_and_unknown_outcomes_excluded_from_stages(self):
        samples = [
            sample("measured", "terminal", wall=0.1, ordinal=0,
                   timings=_timings(decode_seconds=0.4)),
            sample("measured", "failed", wall=9.9, ordinal=1, suffix_index=1,
                   timings=_timings(decode_seconds=9.0)),
            sample("measured", "unknown_completion", wall=8.8, ordinal=2,
                   suffix_index=0,
                   timings=_timings(decode_seconds=8.0)),
        ]
        summary = analyze_trial(samples,
                                calls_by_kind={"model_dispatch": 3},
                                evidence_class="MOCK")
        group = summary["measured"]
        assert group["terminal_samples"] == 1
        assert group["outcome_counts"] == {
            "failed": 1, "terminal": 1, "unknown_completion": 1}
        decode = group["stage_metrics"]["decode_seconds"]
        assert decode["n"] == 1
        assert decode["max"] == 0.4
        wall = group["stage_metrics"]["caller_wall_seconds"]
        assert wall["n"] == 1 and wall["max"] == 0.1

    def test_warmup_and_measured_stages_separate(self):
        samples = [
            sample("warmup", "terminal", wall=1.0, ordinal=0,
                   timings=_timings(decode_seconds=1.0)),
            sample("measured", "terminal", wall=2.0, ordinal=1,
                   suffix_index=1,
                   timings=_timings(decode_seconds=2.0)),
        ]
        summary = analyze_trial(samples,
                                calls_by_kind={"model_dispatch": 2},
                                evidence_class="MOCK")
        assert summary["warmups"]["stage_metrics"][
            "caller_wall_seconds"]["max"] == 1.0
        assert summary["measured"]["stage_metrics"][
            "decode_seconds"]["max"] == 2.0

    def test_stage_summaries_deterministic(self):
        samples = [
            sample("warmup", "terminal", wall=0.5, ordinal=0),
            sample("measured", "terminal", wall=0.25, ordinal=1,
                   suffix_index=1,
                   timings=_timings(prefill_seconds=0.02,
                                    decode_seconds=0.04,
                                    total_seconds=0.06)),
        ]
        first = analyze_trial(copy.deepcopy(samples),
                              calls_by_kind={"model_dispatch": 2},
                              evidence_class="MOCK")
        second = analyze_trial(copy.deepcopy(samples),
                               calls_by_kind={"model_dispatch": 2},
                               evidence_class="MOCK")
        assert first == second

    def test_analysis_boundary_refuses_malformed_samples(self):
        bad = sample("measured", "terminal",
                     usage=_usage(input_tokens="lots"))
        with pytest.raises(ValidationError):
            analyze_trial([bad], calls_by_kind={}, evidence_class="MOCK")
        missing_field = sample("measured", "terminal")
        del missing_field["usage"]
        with pytest.raises(ValidationError):
            analyze_trial([missing_field], calls_by_kind={},
                          evidence_class="MOCK")


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
