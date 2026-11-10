"""Strict contracts for bounded local resource telemetry (OAP 004-d).

Own-process CPU/RSS probes, the strict versioned observation DTOs
(boolean-as-number/nonfinite/negative/contradictory refused; absent
stays null, known 0 stays 0), the bounded fixed-argv nvidia-smi
metadata query (owned deterministic collector executables only;
timeout/byte bounds enforced at the pipe boundary), the narrow trusted
loop observer (no work before the deadline bind; finite cleanup;
phase/ordinal/ledger facts only) and the explicit versioned trial
wrapper (the plain v1 trial evidence stays intact inside it). The
zero-telemetry negative: plan/gates/offline paths never touch the
telemetry seams. Synthetic owned fixtures only; no network, keys,
physical GPU, model or downloads.
"""

from __future__ import annotations

import json
import os
import stat
import threading
import time
from pathlib import Path

import pytest
from pydantic import ValidationError

import slaif_raggedized_helper.qualification.resources as resources
from slaif_raggedized_helper.qualification import (
    PhaseEvent,
    TrialResourceObserver,
    gate_projection_bytes,
    plan_trial,
    validate_resource_wrapper,
    validate_trial_evidence,
    wrap_trial_with_resources,
)
from slaif_raggedized_helper.qualification.resources import (
    CollectorAccounting,
    CpuFacts,
    GpuDevice,
    GpuObservation,
    ProcessScope,
    ResourceDiagnostic,
    ResourceSection,
    ResourceSeries,
    RssFacts,
    SampleObservation,
    cpu_facts,
    lifetime_max_rss_bytes,
    own_process_cpu,
    own_process_rss_bytes,
    process_scope,
    run_gpu_metadata_query,
    run_resource_diagnostic,
)
from test_qualification import (
    _evidence_doc,
    make_config,
    make_spec,
    sample,
)

QUERY_KWARGS = dict(timeout_seconds=0.5, stdout_bytes=16 * 1024,
                    stderr_bytes=4 * 1024)


def _write_executable(path: Path, body: str) -> Path:
    path.write_text(body, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP
               | stat.S_IXOTH)
    return path


def _valid_scope() -> dict:
    return {"scope": "own-process", "pid": 4242, "platform": "linux",
            "note": "own-process note"}


def _valid_samples() -> list[dict]:
    return [
        {"t": 0.0, "cpu_user_seconds": 0.1, "cpu_system_seconds": 0.05,
         "rss_bytes": 1000},
        {"t": 0.2, "cpu_user_seconds": 0.2, "cpu_system_seconds": 0.1,
         "rss_bytes": 2000},
        {"t": 0.4, "cpu_user_seconds": 0.3, "cpu_system_seconds": 0.15,
         "rss_bytes": None},
    ]


def _valid_series(**overrides) -> dict:
    duration = 0.5
    doc = {
        "scope": _valid_scope(),
        "start_offset_seconds": 0.0,
        "interval_seconds": 0.2,
        "duration_seconds": duration,
        "samples": _valid_samples(),
        "cpu": cpu_facts(0.3, 0.15, duration),
        "rss": {"current_bytes": 2000, "lifetime_max_bytes": 5000,
                "lifetime_max_source": "ru_maxrss KiB on Linux",
                "sample_peak_bytes": 2000},
    }
    doc.update(overrides)
    return doc


def _valid_collector(samples: int = 3, queries: int = 0,
                     stop_reason: str = "finished") -> dict:
    return {
        "samples": samples,
        "collection_calls": samples,
        "wall_seconds": 0.5,
        "bytes_read": 1234,
        "device_queries": queries,
        "device_query_wall_seconds": 0.0 if queries == 0 else 0.2,
        "device_query_bytes_read": 0 if queries == 0 else 42,
        "stop_reason": stop_reason,
        "note": "collector accounting note",
    }


def _valid_gpu() -> dict:
    return {
        "status": "available", "reason": None,
        "devices": [
            {"device_index": 0, "device_name": "SYNTHETIC-FAKE-GPU",
             "memory_unit": "mib", "memory_total": 81920,
             "memory_used": 1024, "memory_free": 80000}],
        "query_wall_seconds": 0.2, "stdout_bytes": 33,
        "stderr_bytes": 0, "note": resources.GPU_NOTE,
    }


def _valid_section(trial_status: str = "complete", **overrides) -> dict:
    doc = {
        "kind": "resource-telemetry",
        "version": 1,
        "trial_status": trial_status,
        "series": _valid_series(),
        "gpu": None,
        "collector": _valid_collector(),
        "provenance": list(resources.PROVENANCE_NOTES),
        "phase_events": [
            {"phase": "warmup", "ordinal": 0, "attempted_calls": 0,
             "elapsed_seconds": 0.0},
            {"phase": "measured", "ordinal": 1, "attempted_calls": 1,
             "elapsed_seconds": 0.1},
        ],
    }
    doc.update(overrides)
    return doc


def _valid_trial_doc() -> dict:
    samples = [
        sample("warmup", "terminal", wall=0.5, ordinal=0, suffix_index=0,
               first_repetition=False),
        sample("measured", "terminal", wall=0.25, ordinal=1, suffix_index=1,
               first_repetition=True),
        sample("measured", "terminal", wall=0.75, ordinal=2, suffix_index=0,
               first_repetition=False),
    ]
    doc = _evidence_doc(samples, calls_by_kind={"model_dispatch": 3})
    validate_trial_evidence(doc)
    return doc


# ---------------------------------------------------------------------------
# strict DTO strictness
# ---------------------------------------------------------------------------

class TestSampleObservationStrict:
    def test_valid_roundtrip(self):
        model = SampleObservation.model_validate(
            {"t": 0.0, "cpu_user_seconds": 0.1,
             "cpu_system_seconds": 0.05, "rss_bytes": 1000})
        assert model.t == 0.0 and model.rss_bytes == 1000

    @pytest.mark.parametrize("field", ["t", "cpu_user_seconds",
                                       "cpu_system_seconds"])
    def test_bool_as_number_refused(self, field):
        doc = {"t": 0.0, "cpu_user_seconds": 0.1,
               "cpu_system_seconds": 0.05, "rss_bytes": None}
        doc[field] = True
        with pytest.raises(ValidationError):
            SampleObservation.model_validate(doc)

    @pytest.mark.parametrize("value", [float("inf"), float("-inf"),
                                       float("nan"), -0.1])
    def test_nonfinite_or_negative_refused(self, value):
        doc = {"t": 0.0, "cpu_user_seconds": 0.1,
               "cpu_system_seconds": 0.05, "rss_bytes": None}
        doc["t"] = value
        with pytest.raises(ValidationError):
            SampleObservation.model_validate(doc)

    def test_negative_rss_refused(self):
        with pytest.raises(ValidationError):
            SampleObservation.model_validate(
                {"t": 0.0, "cpu_user_seconds": None,
                 "cpu_system_seconds": None, "rss_bytes": -1})

    def test_bool_rss_refused(self):
        with pytest.raises(ValidationError):
            SampleObservation.model_validate(
                {"t": 0.0, "cpu_user_seconds": None,
                 "cpu_system_seconds": None, "rss_bytes": True})

    def test_absent_stays_null_and_known_zero_kept(self):
        model = SampleObservation.model_validate(
            {"t": 0.0, "cpu_user_seconds": None,
             "cpu_system_seconds": None, "rss_bytes": 0})
        assert model.cpu_user_seconds is None
        assert model.rss_bytes == 0

    def test_extra_field_refused(self):
        doc = {"t": 0.0, "cpu_user_seconds": None,
               "cpu_system_seconds": None, "rss_bytes": None,
               "raw_text": "never carried"}
        with pytest.raises(ValidationError):
            SampleObservation.model_validate(doc)


class TestCpuFactsStrict:
    def test_consistent_interval_facts(self):
        model = CpuFacts.model_validate(
            cpu_facts(0.3, 0.15, 1.0))
        assert model.total_seconds == 0.3 + 0.15
        assert model.utilization == (0.3 + 0.15) / 1.0

    def test_utilization_may_exceed_one_and_is_disclosed(self):
        model = CpuFacts.model_validate(
            cpu_facts(1.0, 1.0, 0.5))
        assert model.utilization == 4.0
        assert "utilization" in model.normalization_note

    def test_zero_wall_utilization_unavailable_not_fabricated(self):
        with pytest.raises(ValidationError):
            CpuFacts.model_validate(cpu_facts(0.3, 0.15, 0.0)
                                    | {"utilization": 0.7})

    def test_zero_wall_no_utilization_is_consistent(self):
        model = CpuFacts.model_validate(cpu_facts(0.3, 0.15, 0.0))
        assert model.utilization is None

    def test_one_side_unknown_refuses_total(self):
        with pytest.raises(ValidationError):
            CpuFacts.model_validate({
                "user_seconds": 0.3, "system_seconds": None,
                "total_seconds": 0.3, "wall_seconds": 1.0,
                "utilization": None,
                "normalization_note": "note"})

    def test_unknown_side_requires_null_total(self):
        with pytest.raises(ValidationError):
            CpuFacts.model_validate({
                "user_seconds": None, "system_seconds": None,
                "total_seconds": 0.3, "wall_seconds": 1.0,
                "utilization": None,
                "normalization_note": "note"})

    def test_total_mismatch_refused(self):
        with pytest.raises(ValidationError):
            CpuFacts.model_validate({
                "user_seconds": 0.3, "system_seconds": 0.15,
                "total_seconds": 0.9, "wall_seconds": 1.0,
                "utilization": None,
                "normalization_note": "note"})

    def test_utilization_mismatch_refused(self):
        with pytest.raises(ValidationError):
            CpuFacts.model_validate({
                "user_seconds": 0.3, "system_seconds": 0.15,
                "total_seconds": 0.45, "wall_seconds": 1.0,
                "utilization": 0.5,
                "normalization_note": "note"})

    def test_bool_refused(self):
        with pytest.raises(ValidationError):
            CpuFacts.model_validate({
                "user_seconds": True, "system_seconds": 0.15,
                "total_seconds": None, "wall_seconds": 1.0,
                "utilization": None,
                "normalization_note": "note"})


class TestRssFactsStrict:
    def test_valid_and_absent(self):
        model = RssFacts.model_validate({
            "current_bytes": None, "lifetime_max_bytes": None,
            "lifetime_max_source": "s", "sample_peak_bytes": None})
        assert model.current_bytes is None
        assert model.lifetime_max_bytes is None

    def test_known_zero_kept(self):
        model = RssFacts.model_validate({
            "current_bytes": 0, "lifetime_max_bytes": 0,
            "lifetime_max_source": "s", "sample_peak_bytes": 0})
        assert model.current_bytes == 0

    @pytest.mark.parametrize("field", ["current_bytes",
                                       "lifetime_max_bytes",
                                       "sample_peak_bytes"])
    def test_negative_and_bool_refused(self, field):
        with pytest.raises(ValidationError):
            RssFacts.model_validate({
                "current_bytes": None, "lifetime_max_bytes": None,
                "lifetime_max_source": "s",
                "sample_peak_bytes": None} | {field: -1})
        with pytest.raises(ValidationError):
            RssFacts.model_validate({
                "current_bytes": None, "lifetime_max_bytes": None,
                "lifetime_max_source": "s",
                "sample_peak_bytes": None} | {field: True})


class TestGpuDeviceStrict:
    def test_valid(self):
        model = GpuDevice.model_validate(
            {"device_index": 1, "device_name": "SYNTHETIC-FAKE-GPU",
             "memory_unit": "mib", "memory_total": 49152,
             "memory_used": 0, "memory_free": 49152})
        assert model.memory_used == 0  # known zero kept

    def test_used_above_total_refused(self):
        with pytest.raises(ValidationError):
            GpuDevice.model_validate(
                {"device_index": 0, "device_name": "X",
                 "memory_unit": "mib", "memory_total": 100,
                 "memory_used": 101, "memory_free": 0})

    def test_free_above_total_refused(self):
        with pytest.raises(ValidationError):
            GpuDevice.model_validate(
                {"device_index": 0, "device_name": "X",
                 "memory_unit": "mib", "memory_total": 100,
                 "memory_used": 0, "memory_free": 101})

    def test_zero_total_refused(self):
        with pytest.raises(ValidationError):
            GpuDevice.model_validate(
                {"device_index": 0, "device_name": "X",
                 "memory_unit": "mib", "memory_total": 0,
                 "memory_used": 0, "memory_free": 0})

    @pytest.mark.parametrize("value", [float("inf"), -5, True])
    def test_nonfinite_negative_bool_memory_refused(self, value):
        with pytest.raises(ValidationError):
            GpuDevice.model_validate(
                {"device_index": 0, "device_name": "X",
                 "memory_unit": "mib", "memory_total": 100,
                 "memory_used": value, "memory_free": 0})

    def test_unit_must_be_mib(self):
        with pytest.raises(ValidationError):
            GpuDevice.model_validate(
                {"device_index": 0, "device_name": "X",
                 "memory_unit": "bytes", "memory_total": 100,
                 "memory_used": 0, "memory_free": 100})

    def test_name_bounded(self):
        with pytest.raises(ValidationError):
            GpuDevice.model_validate(
                {"device_index": 0, "device_name": "X" * 200,
                 "memory_unit": "mib", "memory_total": 100,
                 "memory_used": 0, "memory_free": 100})


class TestGpuObservationStrict:
    def test_valid_available(self):
        model = GpuObservation.model_validate(_valid_gpu())
        assert model.status == "available" and model.reason is None

    def test_available_requires_devices_and_no_reason(self):
        doc = _valid_gpu()
        doc["devices"] = []
        with pytest.raises(ValidationError):
            GpuObservation.model_validate(doc)
        doc2 = _valid_gpu()
        doc2["reason"] = "timeout"
        with pytest.raises(ValidationError):
            GpuObservation.model_validate(doc2)

    def test_unavailable_requires_unavailable_reason(self):
        doc = {"status": "unavailable", "reason": "tool_absent",
               "devices": [], "query_wall_seconds": None,
               "stdout_bytes": None, "stderr_bytes": None,
               "note": resources.GPU_NOTE}
        GpuObservation.model_validate(doc)
        doc["reason"] = "timeout"
        with pytest.raises(ValidationError):
            GpuObservation.model_validate(doc)

    def test_error_requires_error_reason(self):
        doc = {"status": "error", "reason": "timeout", "devices": [],
               "query_wall_seconds": 0.5, "stdout_bytes": 0,
               "stderr_bytes": 0, "note": resources.GPU_NOTE}
        GpuObservation.model_validate(doc)
        doc["reason"] = "no_devices"
        with pytest.raises(ValidationError):
            GpuObservation.model_validate(doc)

    def test_unknown_reason_refused(self):
        doc = {"status": "unavailable", "reason": "whatever",
               "devices": [], "query_wall_seconds": None,
               "stdout_bytes": None, "stderr_bytes": None,
               "note": resources.GPU_NOTE}
        with pytest.raises(ValidationError):
            GpuObservation.model_validate(doc)

    def test_ran_query_requires_query_facts(self):
        doc = {"status": "error", "reason": "timeout", "devices": [],
               "query_wall_seconds": None, "stdout_bytes": None,
               "stderr_bytes": None, "note": resources.GPU_NOTE}
        with pytest.raises(ValidationError):
            GpuObservation.model_validate(doc)

    def test_no_query_reasons_carry_no_facts(self):
        for reason in ("tool_absent", "query_budget_exhausted",
                       "spawn_failed"):
            status = "unavailable" if reason in (
                "tool_absent", "query_budget_exhausted") else "error"
            GpuObservation.model_validate({
                "status": status, "reason": reason, "devices": [],
                "query_wall_seconds": None, "stdout_bytes": None,
                "stderr_bytes": None, "note": resources.GPU_NOTE})
            with pytest.raises(ValidationError):
                GpuObservation.model_validate({
                    "status": status, "reason": reason, "devices": [],
                    "query_wall_seconds": 0.1, "stdout_bytes": None,
                    "stderr_bytes": None, "note": resources.GPU_NOTE})


class TestCollectorAndPhaseStrict:
    def test_valid_collector(self):
        model = CollectorAccounting.model_validate(_valid_collector())
        assert model.samples == 3

    def test_samples_cannot_exceed_calls(self):
        with pytest.raises(ValidationError):
            CollectorAccounting.model_validate(
                _valid_collector() | {"collection_calls": 2})

    def test_stop_reason_vocabulary(self):
        with pytest.raises(ValidationError):
            CollectorAccounting.model_validate(
                _valid_collector() | {"stop_reason": "exploded"})

    def test_bool_counts_refused(self):
        with pytest.raises(ValidationError):
            CollectorAccounting.model_validate(
                _valid_collector() | {"samples": True})

    def test_phase_event_valid(self):
        model = PhaseEvent.model_validate(
            {"phase": "measured", "ordinal": 1, "attempted_calls": 2,
             "elapsed_seconds": 0.1})
        assert model.attempted_calls == 2

    def test_phase_event_null_ledger_fact_allowed(self):
        model = PhaseEvent.model_validate(
            {"phase": "warmup", "ordinal": 0, "attempted_calls": None,
             "elapsed_seconds": 0.0})
        assert model.attempted_calls is None

    def test_phase_event_rejects_non_ledger_fields(self):
        for extra in ("prompt", "output", "credential", "callback"):
            with pytest.raises(ValidationError):
                PhaseEvent.model_validate(
                    {"phase": "warmup", "ordinal": 0,
                     "attempted_calls": 0, "elapsed_seconds": 0.0,
                     extra: "never carried"})

    @pytest.mark.parametrize("field, value", [
        ("ordinal", -1), ("ordinal", True),
        ("attempted_calls", -1), ("attempted_calls", True),
        ("elapsed_seconds", float("inf")), ("elapsed_seconds", -0.1),
    ])
    def test_phase_event_numeric_strictness(self, field, value):
        with pytest.raises(ValidationError):
            PhaseEvent.model_validate(
                {"phase": "warmup", "ordinal": 0,
                 "attempted_calls": 0, "elapsed_seconds": 0.0}
                | {field: value})


class TestSeriesSectionStrict:
    def test_valid_series(self):
        model = ResourceSeries.model_validate(_valid_series())
        assert model.rss.sample_peak_bytes == 2000

    def test_non_monotonic_samples_refused(self):
        samples = _valid_samples()
        samples[2]["t"] = 0.15  # back in time
        with pytest.raises(ValidationError):
            ResourceSeries.model_validate(_valid_series(samples=samples))

    def test_sample_beyond_duration_refused(self):
        samples = _valid_samples()
        samples[2]["t"] = 0.9
        with pytest.raises(ValidationError):
            ResourceSeries.model_validate(_valid_series(samples=samples))

    def test_sample_peak_binding_mismatch_refused(self):
        with pytest.raises(ValidationError):
            ResourceSeries.model_validate(
                _valid_series() | {"rss": _valid_series()["rss"]
                                   | {"sample_peak_bytes": 1500}})

    def test_sample_peak_without_known_values_refused(self):
        series = _valid_series()
        series["samples"] = [
            {"t": 0.0, "cpu_user_seconds": None,
             "cpu_system_seconds": None, "rss_bytes": None}]
        series["cpu"] = cpu_facts(None, None, 0.5)
        with pytest.raises(ValidationError):
            ResourceSeries.model_validate(series)

    def test_all_null_series_is_consistent(self):
        series = _valid_series()
        series["samples"] = [
            {"t": 0.0, "cpu_user_seconds": None,
             "cpu_system_seconds": None, "rss_bytes": None}]
        series["cpu"] = cpu_facts(None, None, 0.5)
        series["rss"] = {"current_bytes": None, "lifetime_max_bytes": None,
                         "lifetime_max_source": "s",
                         "sample_peak_bytes": None}
        model = ResourceSeries.model_validate(series)
        assert model.rss.sample_peak_bytes is None

    def test_wall_must_equal_duration(self):
        series = _valid_series()
        series["cpu"] = cpu_facts(0.3, 0.15, 0.4)  # != duration 0.5
        with pytest.raises(ValidationError):
            ResourceSeries.model_validate(series)

    def test_interval_bound_refused(self):
        with pytest.raises(ValidationError):
            ResourceSeries.model_validate(
                _valid_series() | {"interval_seconds": 11.0})

    def test_scope_strictness(self):
        scope = _valid_scope() | {"scope": "other-pid"}
        with pytest.raises(ValidationError):
            ProcessScope.model_validate(scope)
        scope = _valid_scope() | {"pid": -1}
        with pytest.raises(ValidationError):
            ProcessScope.model_validate(scope)

    def test_section_collector_sample_binding(self):
        with pytest.raises(ValidationError):
            ResourceSection.model_validate(
                _valid_section() | {"collector": _valid_collector(4)})

    def test_section_gpu_requires_queries(self):
        with pytest.raises(ValidationError):
            ResourceSection.model_validate(
                _valid_section() | {"gpu": _valid_gpu()})

    def test_section_queries_without_gpu_refused(self):
        with pytest.raises(ValidationError):
            ResourceSection.model_validate(
                _valid_section() | {"collector": _valid_collector(
                    samples=0, queries=1)})

    def test_section_valid_with_gpu(self):
        section = _valid_section()
        section["gpu"] = _valid_gpu()
        section["collector"] = _valid_collector(queries=1)
        model = ResourceSection.model_validate(section)
        assert model.gpu.status == "available"

    def test_section_trial_status_vocabulary(self):
        with pytest.raises(ValidationError):
            ResourceSection.model_validate(
                _valid_section() | {"trial_status": "qualified"})


class TestWrapperContract:
    def test_valid_wrapper(self):
        trial = _valid_trial_doc()
        wrapper = wrap_trial_with_resources(trial, _valid_section())
        validate_resource_wrapper(wrapper)
        assert wrapper["resource_wrapper"] == 1

    def test_trial_member_is_byte_identical_v1_document(self):
        trial = _valid_trial_doc()
        wrapper = wrap_trial_with_resources(trial, _valid_section())
        assert set(wrapper) == {"resource_wrapper", "trial", "resources"}
        assert json.dumps(wrapper["trial"], sort_keys=True) == \
            json.dumps(trial, sort_keys=True)
        validate_trial_evidence(wrapper["trial"])

    def test_wrong_version_refused(self):
        wrapper = wrap_trial_with_resources(_valid_trial_doc(),
                                            _valid_section())
        for bad in (0, 2, True, "1"):
            with pytest.raises((ValidationError, ValueError)):
                validate_resource_wrapper(
                    {**wrapper, "resource_wrapper": bad})

    def test_extra_or_missing_key_refused(self):
        wrapper = wrap_trial_with_resources(_valid_trial_doc(),
                                            _valid_section())
        with pytest.raises(ValueError):
            validate_resource_wrapper(
                {**wrapper, "extra": "nope"})
        del wrapper["resources"]
        with pytest.raises(ValueError):
            validate_resource_wrapper(wrapper)

    def test_trial_status_mismatch_refused(self):
        trial = _valid_trial_doc()
        section = _valid_section(trial_status="incomplete")
        with pytest.raises((ValidationError, ValueError)):
            validate_resource_wrapper(
                wrap_trial_with_resources(trial, section))

    def test_tampered_inner_trial_refused(self):
        trial = _valid_trial_doc()
        trial["analysis"]["measured"]["latency_seconds"]["p50"] = 99.0
        with pytest.raises((ValidationError, ValueError)):
            validate_resource_wrapper(
                wrap_trial_with_resources(trial, _valid_section()))

    def test_invalid_resource_section_refused(self):
        trial = _valid_trial_doc()
        section = _valid_section()
        section["collector"]["samples"] = 99
        with pytest.raises(ValidationError):
            validate_resource_wrapper(
                wrap_trial_with_resources(trial, section))


# ---------------------------------------------------------------------------
# own-process probes (owned seams; no other PID is ever inspected)
# ---------------------------------------------------------------------------

class _FakeUsage:
    def __init__(self, utime, stime, maxrss):
        self.ru_utime = utime
        self.ru_stime = stime
        self.ru_maxrss = maxrss


class TestOwnProcessProbes:
    def test_cpu_values(self, monkeypatch):
        monkeypatch.setattr(
            resources, "getrusage_self",
            lambda: _FakeUsage(1.25, 0.5, 1024))
        assert own_process_cpu() == (1.25, 0.5)

    def test_cpu_invalid_side_stays_none(self, monkeypatch):
        monkeypatch.setattr(
            resources, "getrusage_self",
            lambda: _FakeUsage(float("nan"), -1.0, 1024))
        assert own_process_cpu() == (None, None)

    def test_cpu_getrusage_failure_unavailable(self, monkeypatch):
        def boom():
            raise OSError("no rusage")

        monkeypatch.setattr(resources, "getrusage_self", boom)
        assert own_process_cpu() == (None, None)

    def test_rss_from_status_bytes(self, monkeypatch):
        data = b"Name:\tpython3\nVmRSS:\t   44704 kB\nVmData:\t 848 kB\n"
        monkeypatch.setattr(resources, "read_proc_self_status",
                            lambda *a, **k: data)
        assert own_process_rss_bytes() == 44704 * 1024

    def test_rss_line_without_unit(self, monkeypatch):
        monkeypatch.setattr(
            resources, "read_proc_self_status",
            lambda *a, **k: b"VmRSS: 123\n")
        assert own_process_rss_bytes() == 123 * 1024

    @pytest.mark.parametrize("data", [
        b"Name:\tpython3\n",                       # line absent
        b"VmRSS:\t\n",                              # malformed
        b"VmRSS:\t-5 kB\n",                         # negative
        b"VmRSS:\t12 MiB\n",                        # unknown unit
        b"VmRSS:\t12 34 kB\n",                      # too many fields
        None,                                       # read failure
    ])
    def test_rss_unavailable_never_zero(self, monkeypatch, data):
        monkeypatch.setattr(resources, "read_proc_self_status",
                            lambda *a, **k: data)
        assert own_process_rss_bytes() is None

    def test_lifetime_max_linux_kibibytes(self, monkeypatch):
        monkeypatch.setattr(resources, "getrusage_self",
                            lambda: _FakeUsage(0.1, 0.1, 2048))
        if resources.platform.system() == "Linux":
            assert lifetime_max_rss_bytes() == 2048 * 1024
        else:
            assert lifetime_max_rss_bytes() is None

    def test_lifetime_max_negative_unavailable(self, monkeypatch):
        monkeypatch.setattr(resources, "getrusage_self",
                            lambda: _FakeUsage(0.1, 0.1, -1))
        assert lifetime_max_rss_bytes() is None

    def test_scope_is_own_process(self):
        scope = process_scope()
        assert scope["scope"] == "own-process"
        assert scope["pid"] == os.getpid()
        assert "devhost" in scope["note"]


# ---------------------------------------------------------------------------
# bounded fixed-argv nvidia-smi metadata query (owned fake executables)
# ---------------------------------------------------------------------------

class TestGpuMetadataQuery:
    def test_fixed_argv_never_selectable(self):
        # the argv is a module constant; no parameter can change it
        assert resources.NVIDIA_SMI_ARGV[0] == "nvidia-smi"
        assert "--query-gpu=index,name,memory.total,memory.used," \
            "memory.free" in resources.NVIDIA_SMI_ARGV[1]

    def test_tool_absent_when_which_fails(self, monkeypatch):
        monkeypatch.setattr(resources.shutil, "which",
                            lambda name: None)
        result = run_gpu_metadata_query(**QUERY_KWARGS)
        assert result["status"] == "unavailable"
        assert result["reason"] == "tool_absent"
        assert result["query_wall_seconds"] is None

    def test_spawn_failed_for_missing_executable(self):
        result = run_gpu_metadata_query(
            executable="/nonexistent/no-such-smi", **QUERY_KWARGS)
        assert result["status"] == "error"
        assert result["reason"] == "spawn_failed"

    def test_available_exact_units_and_values(self, tmp_path):
        script = _write_executable(
            tmp_path / "smi",
            "#!/bin/sh\n"
            "printf '0,SYNTHETIC-FAKE-GPU-A,81920,1024,80000\\n'\n"
            "printf '1,SYNTHETIC-FAKE-GPU-B,49152,0,49152\\n'\n")
        result = run_gpu_metadata_query(executable=str(script),
                                        **QUERY_KWARGS)
        assert result["status"] == "available"
        assert result["reason"] is None
        assert len(result["devices"]) == 2
        dev = result["devices"][0]
        assert dev == {"device_index": 0,
                       "device_name": "SYNTHETIC-FAKE-GPU-A",
                       "memory_unit": "mib", "memory_total": 81920,
                       "memory_used": 1024, "memory_free": 80000}
        assert result["devices"][1]["memory_used"] == 0  # known zero
        assert result["stdout_bytes"] > 0
        assert result["stderr_bytes"] == 0
        GpuObservation.model_validate(result)

    def test_stdout_oversize_kills_owned_child(self, tmp_path):
        script = _write_executable(
            tmp_path / "smi",
            "#!/bin/sh\n"
            "python3 -c \"import sys;"
            "sys.stdout.write('0,' + 'x'*20000 + ',81920,1,81919\\n')\"\n")
        t0 = time.monotonic()
        result = run_gpu_metadata_query(executable=str(script),
                                        **QUERY_KWARGS)
        assert result["status"] == "error"
        assert result["reason"] == "stdout_oversize"
        assert result["stdout_bytes"] == 16 * 1024 + 1
        # the owned child was stopped at the pipe boundary
        assert time.monotonic() - t0 < 5.0

    def test_stderr_oversize(self, tmp_path):
        script = _write_executable(
            tmp_path / "smi",
            "#!/bin/sh\n"
            "python3 -c \"import sys;"
            "sys.stderr.write('E'*(4096+500))\"\n"
            "printf '0,X,81920,1,81919\\n'\n")
        result = run_gpu_metadata_query(executable=str(script),
                                        **QUERY_KWARGS)
        assert result["status"] == "error"
        assert result["reason"] == "stderr_oversize"
        assert result["stderr_bytes"] == 4 * 1024 + 1

    def test_timeout_kills_owned_child(self, tmp_path):
        marker = tmp_path / "done"
        script = _write_executable(
            tmp_path / "smi",
            f"#!/bin/sh\nsleep 2\ntouch {marker}\n"
            "printf '0,X,81920,1,81919\\n'\n")
        t0 = time.monotonic()
        result = run_gpu_metadata_query(
            executable=str(script), timeout_seconds=0.5,
            stdout_bytes=16 * 1024, stderr_bytes=4 * 1024)
        elapsed = time.monotonic() - t0
        assert result["status"] == "error"
        assert result["reason"] == "timeout"
        assert 0.4 <= elapsed < 2.0
        assert result["query_wall_seconds"] is not None

    def test_nonzero_exit_is_query_failed_without_raw_stderr(self, tmp_path):
        script = _write_executable(
            tmp_path / "smi",
            "#!/bin/sh\necho 'CANARY-RAW-STDERR-004D' >&2\nexit 9\n")
        result = run_gpu_metadata_query(executable=str(script),
                                        **QUERY_KWARGS)
        assert result["status"] == "error"
        assert result["reason"] == "query_failed"
        assert result["stderr_bytes"] > 0
        blob = json.dumps(result)
        assert "CANARY-RAW-STDERR-004D" not in blob  # raw stderr never kept
        assert "SYNTHETIC" not in blob

    def test_empty_output_is_no_devices(self, tmp_path):
        script = _write_executable(tmp_path / "smi", "#!/bin/sh\n:\n")
        result = run_gpu_metadata_query(executable=str(script),
                                        **QUERY_KWARGS)
        assert result["status"] == "unavailable"
        assert result["reason"] == "no_devices"

    @pytest.mark.parametrize("line", [
        "0,X,81920,1",                          # too few fields
        "0,X,81920,1,81919,extra",              # too many fields
        "zero,X,81920,1,81919",                 # non-integer index
        "0,X,81920,one,81919",                  # non-integer memory
        "0,X,-5,1,81919",                       # negative total
    ])
    def test_malformed_output(self, tmp_path, line):
        script = _write_executable(
            tmp_path / "smi", f"#!/bin/sh\nprintf '{line}\\n'\n")
        result = run_gpu_metadata_query(executable=str(script),
                                        **QUERY_KWARGS)
        assert result["status"] == "error"
        assert result["reason"] == "malformed_output"

    def test_contradictory_values(self, tmp_path):
        script = _write_executable(
            tmp_path / "smi",
            "#!/bin/sh\nprintf '0,X,81920,90000,80000\\n'\n")
        result = run_gpu_metadata_query(executable=str(script),
                                        **QUERY_KWARGS)
        assert result["status"] == "error"
        assert result["reason"] == "contradictory_values"

    def test_too_many_devices_malformed(self, tmp_path):
        lines = "\n".join(
            f"{i},X{i},81920,1,81919" for i in range(9))
        script = _write_executable(
            tmp_path / "smi",
            "#!/bin/sh\nprintf '" + lines.replace("\n", "\\n") + "\\n'\n")
        result = run_gpu_metadata_query(executable=str(script),
                                        **QUERY_KWARGS)
        assert result["status"] == "error"
        assert result["reason"] == "malformed_output"

    @pytest.mark.parametrize("kwargs", [
        dict(timeout_seconds=0),
        dict(timeout_seconds=float("inf")),
        dict(stdout_bytes=0),
        dict(stderr_bytes=-1),
        dict(timeout_seconds=True),
    ])
    def test_invalid_query_budgets_refused(self, kwargs):
        with pytest.raises(ValueError):
            run_gpu_metadata_query(**{**QUERY_KWARGS, **kwargs})


# ---------------------------------------------------------------------------
# the narrow trusted loop observer
# ---------------------------------------------------------------------------

class TestObserverLifecycle:
    def test_construction_starts_no_work(self, monkeypatch):
        calls = []
        monkeypatch.setattr(
            resources, "own_process_cpu",
            lambda: (calls.append(1) or (0.1, 0.05)))
        before = {thread.name for thread in threading.enumerate()}
        TrialResourceObserver(interval_seconds=0.05,
                              max_duration_seconds=0.2,
                              max_samples=4)
        assert calls == []  # no telemetry before the deadline bind
        assert {thread.name for thread in threading.enumerate()} == before

    def test_double_start_refused(self):
        observer = TrialResourceObserver(interval_seconds=0.05,
                                         max_duration_seconds=0.2,
                                         max_samples=2)
        observer.start(None)
        try:
            with pytest.raises(ValueError):
                observer.start(None)
        finally:
            observer.stop("finished")

    def test_deadline_already_passed_samples_nothing(self):
        observer = TrialResourceObserver(interval_seconds=0.05,
                                         max_duration_seconds=0.2,
                                         max_samples=4)
        observer.start(time.monotonic() - 1.0)
        section = observer.finish("not_run")
        assert section["collector"]["stop_reason"] == "deadline_reached"
        assert section["collector"]["samples"] == 0
        assert section["series"]["samples"] == []

    def test_phase_events_recorded_then_dropped_after_stop(self):
        observer = TrialResourceObserver(interval_seconds=0.05,
                                         max_duration_seconds=0.2,
                                         max_samples=4)
        observer.start(None)
        observer.record_phase(PhaseEvent(
            phase="warmup", ordinal=0, attempted_calls=0,
            elapsed_seconds=0.0))
        observer.stop("stopped")
        observer.record_phase(PhaseEvent(
            phase="measured", ordinal=1, attempted_calls=1,
            elapsed_seconds=0.1))
        section = observer.finish("not_run")
        assert len(section["phase_events"]) == 1
        assert section["phase_events"][0]["phase"] == "warmup"

    def test_phase_event_type_enforced(self):
        observer = TrialResourceObserver()
        observer.start(None)
        try:
            with pytest.raises(TypeError):
                observer.record_phase({"phase": "warmup", "ordinal": 0,
                                       "attempted_calls": 0,
                                       "elapsed_seconds": 0.0})
        finally:
            observer.stop("finished")

    def test_stop_reason_vocabulary_enforced(self):
        observer = TrialResourceObserver()
        with pytest.raises(ValueError):
            observer.stop("exploded")

    def test_stop_idempotent(self):
        observer = TrialResourceObserver(interval_seconds=0.05,
                                         max_duration_seconds=0.2,
                                         max_samples=2)
        observer.start(None)
        observer.stop("stopped")
        observer.stop("finished")  # no-op
        section = observer.finish("not_run")
        assert section["collector"]["stop_reason"] == "stopped"

    def test_cpu_interval_deltas_from_baseline(self, monkeypatch):
        # baseline at start, then point samples, then the final read
        # (the sequence holds its last value for any further reads)
        values = [(1.0, 0.5), (1.5, 0.6), (2.0, 0.7)]
        state = {"index": 0}

        def fake_cpu():
            value = values[min(state["index"], len(values) - 1)]
            state["index"] += 1
            return value

        monkeypatch.setattr(resources, "own_process_cpu", fake_cpu)
        monkeypatch.setattr(resources, "own_process_rss_bytes",
                            lambda: None)
        observer = TrialResourceObserver(interval_seconds=0.05,
                                         max_duration_seconds=0.2,
                                         max_samples=2)
        observer.start(None)
        time.sleep(0.12)
        section = observer.finish("not_run")
        cpu = section["series"]["cpu"]
        assert cpu["user_seconds"] == 2.0 - 1.0    # baseline subtracted
        assert cpu["system_seconds"] == 0.7 - 0.5  # baseline subtracted
        assert cpu["total_seconds"] == (2.0 - 1.0) + (0.7 - 0.5)
        # the pre-series CPU time (baseline) is not attributed
        assert cpu["user_seconds"] < 2.0

    def test_unavailable_probes_stay_null_not_zero(self, monkeypatch):
        monkeypatch.setattr(resources, "own_process_cpu",
                            lambda: (None, None))
        monkeypatch.setattr(resources, "own_process_rss_bytes",
                            lambda: None)
        monkeypatch.setattr(resources, "lifetime_max_rss_bytes",
                            lambda: None)
        observer = TrialResourceObserver(interval_seconds=0.05,
                                         max_duration_seconds=0.15,
                                         max_samples=4)
        observer.start(None)
        time.sleep(0.1)
        section = observer.finish("not_run")
        assert section["series"]["cpu"]["user_seconds"] is None
        assert section["series"]["rss"]["current_bytes"] is None
        assert section["series"]["rss"]["lifetime_max_bytes"] is None
        assert section["series"]["rss"]["sample_peak_bytes"] is None
        ResourceSection.model_validate(section)

    def test_sample_cap_reached(self):
        observer = TrialResourceObserver(interval_seconds=0.05,
                                         max_duration_seconds=1.0,
                                         max_samples=2)
        observer.start(None)
        time.sleep(0.4)  # let the sampler exhaust the sample cap
        section = observer.finish("not_run")
        assert section["collector"]["samples"] == 2
        assert section["collector"]["stop_reason"] == "samples_reached"

    def test_trial_deadline_stops_sampling(self):
        observer = TrialResourceObserver(interval_seconds=0.05,
                                         max_duration_seconds=5.0,
                                         max_samples=64)
        observer.start(time.monotonic() + 0.2)
        time.sleep(0.5)  # past the bound deadline
        section = observer.finish("incomplete")
        assert section["collector"]["stop_reason"] == "deadline_reached"
        assert section["collector"]["samples"] <= 5

    def test_finish_is_idempotent_and_validated(self):
        observer = TrialResourceObserver(interval_seconds=0.05,
                                         max_duration_seconds=0.1,
                                         max_samples=2)
        observer.start(None)
        time.sleep(0.12)
        section = observer.finish("complete")
        ResourceSection.model_validate(section)
        # a second finish keeps the SAME stop state (idempotent stop);
        # only the measured duration of the re-read window differs
        again = observer.finish("complete")
        ResourceSection.model_validate(again)
        assert again["collector"]["stop_reason"] == \
            section["collector"]["stop_reason"]
        assert again["series"]["samples"] == section["series"]["samples"]

    def test_invalid_construction_bounds_refused(self):
        for kwargs in (
            dict(interval_seconds=0),
            dict(interval_seconds=float("inf")),
            dict(interval_seconds=True),
            dict(max_duration_seconds=0),
            dict(max_samples=0),
            dict(max_samples=True),
            dict(cleanup_bound_seconds=0),
            dict(gpu_query="yes"),
        ):
            with pytest.raises(ValueError):
                TrialResourceObserver(**kwargs)


class TestObserverGpuQuery:
    def test_at_most_one_bounded_query(self, tmp_path):
        script = _write_executable(
            tmp_path / "smi",
            "#!/bin/sh\nprintf '0,SYNTHETIC-FAKE-GPU,81920,1024,80000\\n'\n")
        observer = TrialResourceObserver(
            interval_seconds=0.05, max_duration_seconds=0.1,
            max_samples=2, gpu_query=True,
            gpu_executable=str(script),
            gpu_timeout_seconds=1.0,
            gpu_stdout_bytes=16 * 1024,
            gpu_stderr_bytes=4 * 1024)
        observer.start(None)
        section = observer.finish("complete")
        assert section["collector"]["device_queries"] == 1
        assert section["gpu"]["status"] == "available"
        assert len(section["gpu"]["devices"]) == 1
        assert section["gpu"]["devices"][0]["memory_unit"] == "mib"
        assert section["collector"]["device_query_bytes_read"] > 0
        ResourceSection.model_validate(section)

    def test_gpu_unavailable_still_valid_section(self, tmp_path):
        script = _write_executable(tmp_path / "smi", "#!/bin/sh\n:\n")
        observer = TrialResourceObserver(
            interval_seconds=0.05, max_duration_seconds=0.1,
            max_samples=2, gpu_query=True,
            gpu_executable=str(script),
            gpu_timeout_seconds=1.0,
            gpu_stdout_bytes=16 * 1024,
            gpu_stderr_bytes=4 * 1024)
        observer.start(None)
        section = observer.finish("complete")
        assert section["gpu"]["status"] == "unavailable"
        assert section["gpu"]["reason"] == "no_devices"
        assert section["collector"]["device_queries"] == 1
        ResourceSection.model_validate(section)


# ---------------------------------------------------------------------------
# standalone diagnostic (explicit opt-in; bounded D0 allowance)
# ---------------------------------------------------------------------------

class TestDiagnostic:
    def test_bounded_allowance(self):
        code, doc = run_resource_diagnostic(duration_seconds=0.2,
                                            samples=3)
        assert code == 0
        ResourceDiagnostic.model_validate(doc)
        assert doc["kind"] == "resource-diagnostic"
        assert doc["collector"]["samples"] >= 1
        assert doc["series"]["duration_seconds"] <= 0.5

    @pytest.mark.parametrize("kwargs", [
        dict(duration_seconds=5.1, samples=4),
        dict(duration_seconds=0, samples=4),
        dict(duration_seconds=float("inf"), samples=4),
        dict(duration_seconds=0.5, samples=65),
        dict(duration_seconds=0.5, samples=0),
        dict(duration_seconds=0.5, samples=True),
        dict(duration_seconds=0.5, samples=4.0),
    ])
    def test_allowance_violations_refused(self, kwargs):
        with pytest.raises(ValueError):
            run_resource_diagnostic(**kwargs)

    def test_real_own_process_measurement(self):
        # this devhost: /proc exists, so RSS must be a real measurement
        code, doc = run_resource_diagnostic(duration_seconds=0.15,
                                            samples=2)
        if resources.platform.system() == "Linux":
            assert doc["series"]["rss"]["current_bytes"] is not None
            assert doc["series"]["rss"]["current_bytes"] >= 0
        assert doc["collector"]["collection_calls"] >= 1

    def test_gpu_flag_with_absent_tool_is_honest_unavailable(self):
        code, doc = run_resource_diagnostic(duration_seconds=0.1,
                                            samples=2, gpu_query=True)
        gpu = doc["gpu"]
        assert gpu is not None
        GpuObservation.model_validate(gpu)
        # this host: either the tool is absent or the query produced
        # exact evidence; never a fabricated zero/used/full
        if gpu["status"] != "available":
            assert gpu["reason"] in (
                "tool_absent", "spawn_failed", "no_devices",
                "query_failed", "timeout", "stdout_oversize",
                "stderr_oversize", "malformed_output",
                "contradictory_values")


# ---------------------------------------------------------------------------
# zero telemetry on the non-opt-in paths (criterion 7)
# ---------------------------------------------------------------------------

class TestZeroTelemetryOnNonOptInPaths:
    def test_plan_and_gates_never_touch_telemetry_seams(self, monkeypatch):
        calls = []

        def record(*args, **kwargs):
            calls.append(1)
            raise AssertionError("telemetry seam touched on offline path")

        for name in ("getrusage_self", "read_proc_self_status",
                     "own_process_cpu", "own_process_rss_bytes",
                     "lifetime_max_rss_bytes", "run_gpu_metadata_query"):
            monkeypatch.setattr(resources, name, record)

        before = {thread.name for thread in threading.enumerate()}
        config = make_config()
        spec = make_spec()
        exit_code, plan = plan_trial(config, spec)
        assert exit_code == 0
        gate_projection_bytes()
        assert calls == []
        after = {thread.name for thread in threading.enumerate()}
        assert after == before  # no sampler thread was created
        assert "resource" not in plan

    def test_import_creates_no_sampler_thread(self):
        # the module body is pure definitions: importing (fresh or
        # cached) performs no telemetry and starts no thread
        before = {thread.name for thread in threading.enumerate()}
        import importlib

        importlib.import_module("slaif_raggedized_helper.cli")
        importlib.import_module(
            "slaif_raggedized_helper.qualification.resources")
        after = {thread.name for thread in threading.enumerate()}
        assert after == before
        assert not any(name == "trial-resource-observer"
                       for name in after)
