"""Model lock, qualification and promotion behavior."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from slaif_raggedized_helper.schema import (
    GGUFMetadata,
    LicenseStatus,
    ModelLock,
    ModelManifest,
    QualificationRecord,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def make_lock(**overrides) -> ModelLock:
    data = {
        "schema_version": 1,
        "role": "generator",
        "model_name": "Qwen3.8-27B-Q6",
        "revision": "rev-1",
        "artifact_sha256": None,
        "license_name": None,
        "license_status": "unknown",
        "tokenizer_revision": None,
        "pooling": None,
        "gguf": {"quantization": "Q6_K", "artifact_sha256": None},
        "projector": None,
        "runtime": None,
    }
    data.update(overrides)
    return ModelLock.model_validate(data)


def make_record(**overrides) -> QualificationRecord:
    data = {
        "schema_version": 1,
        "test_name": "synthetic-smoke",
        "recorded_at": "2026-11-10T00:00:00Z",
        "code_scope": "abc123",
        "model_scope": "rev-1",
        "runtime_scope": "cpu-synthetic",
        "mode": "mock",
        "status": "pass",
        "metrics": None,
    }
    data.update(overrides)
    return QualificationRecord.model_validate(data)


def test_unqualified_example_manifest_is_not_model_proof():
    for name in (
        "example-generator-unqualified.json",
        "example-embedding-unqualified.json",
        "example-reranker-unqualified.json",
    ):
        raw = json.loads(
            (REPO_ROOT / "config/examples/model-locks" / name).read_text(encoding="utf-8")
        )
        manifest = ModelManifest.model_validate(raw)
        status, issues = manifest.evaluate()
        assert status == "unqualified"
        assert any("NOT RUN" in issue for issue in issues)
        summary = manifest.summary()
        assert summary["artifact_pinned"] is False
        assert summary["license_status"] == "unknown"
        assert "not proof" in summary["note"]


def test_missing_evidence_fails_promotion():
    manifest = ModelManifest.model_validate({"schema_version": 1, "lock": make_lock().model_dump()})
    status, issues = manifest.evaluate()
    assert status == "unqualified"
    assert any("license" in issue for issue in issues)
    assert any("artifact hash" in issue for issue in issues)
    assert any("NOT RUN" in issue for issue in issues)


def test_mock_pass_never_qualifies_live_promotion():
    lock = make_lock(license_status="approved", artifact_sha256="ab" * 32)
    manifest = ModelManifest.model_validate(
        {
            "schema_version": 1,
            "lock": lock.model_dump(),
            "qualification": make_record(mode="mock").model_dump(),
        }
    )
    status, issues = manifest.evaluate()
    assert status == "unqualified"
    assert any("mock-mode only" in issue for issue in issues)


def test_live_pass_with_pinned_approved_lock_qualifies():
    lock = make_lock(license_status="approved", artifact_sha256="ab" * 32)
    record = make_record(mode="live", status="pass", model_scope="rev-1")
    manifest = ModelManifest.model_validate(
        {
            "schema_version": 1,
            "lock": lock.model_dump(),
            "qualification": record.model_dump(mode="json"),
        }
    )
    status, issues = manifest.evaluate()
    assert status == "qualified"
    assert issues == []


def test_incompatible_qualification_scope_fails_promotion():
    lock = make_lock(license_status="approved", artifact_sha256="ab" * 32)
    record = make_record(mode="live", status="pass", model_scope="rev-OTHER")
    manifest = ModelManifest.model_validate(
        {
            "schema_version": 1,
            "lock": lock.model_dump(),
            "qualification": record.model_dump(mode="json"),
        }
    )
    status, issues = manifest.evaluate()
    assert status == "unqualified"
    assert any("does not match" in issue for issue in issues)


def test_failed_or_blocked_qualification_fails_promotion():
    lock = make_lock(license_status="approved", artifact_sha256="ab" * 32)
    for status in ("fail", "blocked", "not_run"):
        record = make_record(mode="live", status=status)
        manifest = ModelManifest.model_validate(
            {
                "schema_version": 1,
                "lock": lock.model_dump(),
                "qualification": record.model_dump(mode="json"),
            }
        )
        assert manifest.evaluate()[0] == "unqualified"


def test_gguf_metadata_is_generator_only():
    with pytest.raises(ValidationError, match="generator role"):
        make_lock(role="embedding", gguf={"quantization": "Q6_K"})
    make_lock(role="generator", gguf={"quantization": "Q6_K"})


def test_artifact_hash_must_be_64_hex():
    with pytest.raises(ValidationError, match="64 lowercase hex"):
        make_lock(artifact_sha256="zz" * 32)
    with pytest.raises(ValidationError, match="64 lowercase hex"):
        make_lock(artifact_sha256="ab" * 31)
    make_lock(artifact_sha256="ab" * 32)
    with pytest.raises(ValidationError, match="64 lowercase hex"):
        GGUFMetadata.model_validate({"quantization": "Q6_K", "artifact_sha256": "AB" * 32})


def test_qualification_timestamp_must_be_explicit_utc():
    with pytest.raises(ValidationError, match="UTC offset"):
        make_record(recorded_at="2026-11-10T00:00:00")
    make_record(recorded_at="2026-11-10T00:00:00Z")
    make_record(recorded_at="2026-11-10T01:30:00+01:30")


def test_qualification_metrics_must_be_finite_or_null():
    with pytest.raises(ValidationError, match="finite"):
        make_record(metrics={"recall_at_20": float("inf")})
    record = make_record(metrics={"recall_at_20": 0.97})
    assert record.metrics == {"recall_at_20": 0.97}
    dumped = json.loads(make_record().model_dump_json())
    assert dumped["metrics"] is None


def test_lock_rejects_unknown_fields():
    with pytest.raises(ValidationError):
        make_lock(extra="nope")
    assert make_lock().license_status is LicenseStatus.UNKNOWN
