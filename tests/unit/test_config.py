"""Strict configuration behavior: cross-field invariants, not type mirrors."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from slaif_raggedized_helper import config as cfg

REPO_ROOT = Path(__file__).resolve().parents[2]


def base_config() -> dict:
    return {
        "schema_version": 1,
        "generator": {
            "route": {
                "base_url": "http://gateway.invalid/v1",
                "model": "Qwen3.8-27B-Q6",
                "api": "v1-responses",
                "timeout_seconds": 60,
            },
            "context_expected_tokens": 32768,
            "output_reserve_tokens": 1536,
            "deadline_seconds": 120,
            "max_inflight": 1,
        },
        "profiles": [
            {"name": "q", "purpose": "online_query_embedding", "device": "cpu", "dtype": "fp32"},
            {"name": "r", "purpose": "online_rerank", "device": "gpu", "dtype": "fp16"},
            {"name": "e", "purpose": "offline_embed", "device": "gpu", "dtype": "fp16"},
        ],
        "embedding": {"exclusive_offline_gpu": True, "store_dtype": "fp32"},
        "direct_generation": {"enabled": False},
        "secrets": {},
        "model_locks": [],
    }


def test_example_config_loads():
    config = cfg.load_config(REPO_ROOT / "config/examples/example-config.json")
    assert config.generator.route is not None
    assert config.generator.route.host == "gateway.invalid"


def test_unknown_field_rejected_at_every_level():
    data = base_config()
    data["unexpected_top"] = 1
    with pytest.raises(ValidationError, match="unexpected_top"):
        cfg.RaggedizedConfig.model_validate(data)

    data = base_config()
    data["generator"]["surprise"] = True
    with pytest.raises(ValidationError, match="surprise"):
        cfg.RaggedizedConfig.model_validate(data)

    data = base_config()
    data["profiles"][0]["gpu"] = True
    with pytest.raises(ValidationError, match="gpu"):
        cfg.RaggedizedConfig.model_validate(data)


@pytest.mark.parametrize(
    "field, value",
    [
        ("generator.deadline_seconds", float("inf")),
        ("generator.deadline_seconds", float("nan")),
        ("generator.route.timeout_seconds", float("inf")),
        ("generator.route.timeout_seconds", float("nan")),
        ("generator.context_expected_tokens", 0),
        ("generator.context_expected_tokens", -5),
        ("generator.output_reserve_tokens", 0),
        ("generator.max_inflight", 0),
    ],
)
def test_invalid_budgets_rejected(field, value):
    data = base_config()
    node = data
    parts = field.split(".")
    for part in parts[:-1]:
        node = node[part]
    node[parts[-1]] = value
    with pytest.raises(ValidationError):
        cfg.RaggedizedConfig.model_validate(data)


def test_nonpositive_timeout_rejected():
    data = base_config()
    data["generator"]["route"]["timeout_seconds"] = 0
    with pytest.raises(ValidationError):
        cfg.RaggedizedConfig.model_validate(data)


def test_output_reserve_must_fit_inside_context():
    data = base_config()
    data["generator"]["context_expected_tokens"] = 100
    data["generator"]["output_reserve_tokens"] = 200
    with pytest.raises(ValidationError, match="strictly smaller"):
        cfg.RaggedizedConfig.model_validate(data)

    data = base_config()
    data["generator"]["context_expected_tokens"] = 100
    data["generator"]["output_reserve_tokens"] = 100
    with pytest.raises(ValidationError, match="strictly smaller"):
        cfg.RaggedizedConfig.model_validate(data)

    data = base_config()
    data["generator"]["context_expected_tokens"] = 100
    data["generator"]["output_reserve_tokens"] = 99
    cfg.RaggedizedConfig.model_validate(data)


def test_stored_vectors_must_be_fp32():
    data = base_config()
    data["embedding"]["store_dtype"] = "fp16"
    with pytest.raises(ValidationError, match="FP32"):
        cfg.RaggedizedConfig.model_validate(data)
    data = base_config()
    data["embedding"]["store_dtype"] = "fp32"
    cfg.RaggedizedConfig.model_validate(data)


def test_route_url_query_credentials_refused():
    for base_url in (
        "http://gateway.invalid/v1?api_key=secret-value",
        "http://gateway.invalid/v1#token=secret-value",
    ):
        data = base_config()
        data["generator"]["route"]["base_url"] = base_url
        with pytest.raises(ValidationError, match="forbidden"):
            cfg.RaggedizedConfig.model_validate(data)


def test_offline_embed_allows_qualified_gpu_fp32_corpus_mode():
    data = base_config()
    data["profiles"] = [{"name": "e", "purpose": "offline_embed", "device": "gpu", "dtype": "fp32"}]
    cfg.RaggedizedConfig.model_validate(data)
    # but CPU offline embedding remains forbidden
    data["profiles"] = [{"name": "e", "purpose": "offline_embed", "device": "cpu", "dtype": "fp32"}]
    with pytest.raises(ValidationError, match="does not permit"):
        cfg.RaggedizedConfig.model_validate(data)


def test_env_secret_reference_uses_env_name_grammar():
    for name in ("9BAD", "has-dash", "with space", "SLAIF_GATEWAY_KEY/extra"):
        with pytest.raises(ValidationError, match="environment variable name"):
            cfg.SecretRef.model_validate({"kind": "env", "name": name})
    cfg.SecretRef.model_validate({"kind": "env", "name": "SLAIF_GATEWAY_KEY"})
    cfg.SecretRef.model_validate({"kind": "env", "name": "_A1"})
    # file references remain path-shaped
    cfg.SecretRef.model_validate({"kind": "file", "name": "/etc/slaif/key.pem"})


def test_rejected_config_error_never_echoes_embedded_secret(tmp_path):
    secret = "FAKE_TEST_SECRET-002"
    data = base_config()
    data["generator"]["route"]["base_url"] = f"http://user:{secret}@example.invalid/v1"
    with pytest.raises(cfg.ConfigLoadError) as excinfo:
        import json as _json

        path = tmp_path / "secret.json"
        path.write_text(_json.dumps(data), encoding="utf-8")
        cfg.load_config(path)
    assert secret not in str(excinfo.value)
@pytest.mark.parametrize(
    ("purpose", "device", "dtype", "allowed"),
    [
        ("online_query_embedding", "cpu", "fp32", True),
        ("online_query_embedding", "gpu", "fp16", False),
        ("online_query_embedding", "cpu", "fp16", False),
        ("online_rerank", "gpu", "fp16", True),
        ("online_rerank", "cpu", "fp32", False),
        ("offline_embed", "gpu", "fp16", True),
        ("offline_embed", "cpu", "fp32", False),
        ("offline_context", "gpu", "fp16", True),
    ],
)
def test_profile_purpose_device_dtype_matrix(purpose, device, dtype, allowed):
    data = base_config()
    data["profiles"] = [{"name": "p", "purpose": purpose, "device": device, "dtype": dtype}]
    if allowed:
        config = cfg.RaggedizedConfig.model_validate(data)
        assert len(config.profiles) == 1
    else:
        with pytest.raises(ValidationError, match="does not permit"):
            cfg.RaggedizedConfig.model_validate(data)


def test_direct_online_generation_refused():
    data = base_config()
    data["direct_generation"]["enabled"] = True
    with pytest.raises(ValidationError, match="direct generation is not permitted"):
        cfg.RaggedizedConfig.model_validate(data)


# ---------------------------------------------------------------------------
# native direct configuration (003-e: reference registry, template identity)
# ---------------------------------------------------------------------------

def test_pinned_reference_registry_matches_upstream_source():
    """The reference registry is the actual pinned 3b4d6ab --chat-template
    list: versioned mistral/phi entries present, the false five-name set
    (llava / bare mistral / phi-2) absent."""
    names = cfg.PINNED_LLAMA_BUILTIN_CHAT_TEMPLATES
    for name in ("mistral-v1", "mistral-v3", "mistral-v7", "phi3", "phi4",
                 "chatml", "zephyr", "llama3"):
        assert name in names
    for name in ("llava", "mistral", "phi-2"):
        assert name not in names
    assert len(names) == len(set(names))


def _direct_offline(**overrides):
    from datetime import datetime, timezone

    direct = {
        "mode": "offline_diagnostic",
        "destination": {"base_url": "http://127.0.0.1:8080"},
        "trusted_policy": "private_trusted",
        "model": "synthetic-qwen",
        "chat_template": None,
        "template_qualification": {
            "template": None,
            "build_id": "b1",
            "method": "apply-template",
            "recorded_at": datetime.now(timezone.utc).isoformat(),
        },
        "max_output_tokens": 64,
        "deadline_seconds": 30.0,
    }
    direct.update(overrides)
    return cfg.DirectGenerationConfig.model_validate(direct)


def test_model_metadata_default_template_is_supported():
    """chat_template None = the server's model-metadata default template
    (Jinja enabled on the pinned reference); the qualification record must
    carry the matching None identity."""
    config = _direct_offline()
    assert config.chat_template is None
    assert config.template_qualification.template is None


def test_operator_jinja_template_name_is_not_allowlisted():
    """No arbitrary local-name allowlist: a declared operator Jinja
    template identity outside the reference registry is valid config; the
    server renders it via /apply-template and refuses unknown templates
    itself (the name is an identity, not a local renderer claim)."""
    config = _direct_offline(
        chat_template="my-project-jinja-template",
        template_qualification={"template": "my-project-jinja-template",
                                "build_id": "b1", "method": "apply-template",
                                "recorded_at": "2026-11-10T00:00:00+00:00"},
    )
    assert config.chat_template == "my-project-jinja-template"
    # a pinned reference built-in remains a valid declared identity too
    config = _direct_offline(
        chat_template="mistral-v3",
        template_qualification={"template": "mistral-v3",
                                "build_id": "b1", "method": "apply-template",
                                "recorded_at": "2026-11-10T00:00:00+00:00"},
    )
    assert config.chat_template == "mistral-v3"


@pytest.mark.parametrize(
    "bad_template",
    [
        "has space",
        "with\ttab",
        "path/to/template",
        "./relative",
        "close" + chr(60) + "/tool_call" + chr(62) + "marker",  # the native closing-marker sequence
    ],
)
def test_template_identity_token_rules(bad_template):
    with pytest.raises(ValidationError):
        _direct_offline(
            chat_template=bad_template,
            template_qualification={"template": bad_template, "build_id": "b1",
                                    "method": "apply-template",
                                    "recorded_at": "2026-11-10T00:00:00+00:00"},
        )


def test_qualification_must_match_declared_template_identity():
    with pytest.raises(ValidationError, match="does not match"):
        _direct_offline(
            chat_template="mistral-v3",
            template_qualification={"template": "zephyr", "build_id": "b1",
                                    "method": "apply-template",
                                    "recorded_at": "2026-11-10T00:00:00+00:00"},
        )
    # a named declaration must not be qualified by the model-default record
    with pytest.raises(ValidationError, match="does not match"):
        _direct_offline(
            chat_template="mistral-v3",
            template_qualification={"template": None, "build_id": "b1",
                                    "method": "apply-template",
                                    "recorded_at": "2026-11-10T00:00:00+00:00"},
        )


def test_offline_diagnostic_requires_declared_model_identity():
    with pytest.raises(ValidationError, match="model identity"):
        _direct_offline(model=None)


def test_implicit_degradation_rejected():
    data = base_config()
    data["generator"]["fallback"] = "smaller-context"
    with pytest.raises(ValidationError, match="implicit degradation"):
        cfg.RaggedizedConfig.model_validate(data)

    data = base_config()
    data["generator"]["degradation"] = {"enabled": True, "allow": [{"name": "other"}]}
    data["generator"]["fallback"] = "smaller-context"
    with pytest.raises(ValidationError, match="not one of the explicitly allowed"):
        cfg.RaggedizedConfig.model_validate(data)

    data = base_config()
    data["generator"]["degradation"] = {
        "enabled": True,
        "allow": [{"name": "smaller-context"}],
    }
    data["generator"]["fallback"] = "smaller-context"
    config = cfg.RaggedizedConfig.model_validate(data)
    assert config.generator.fallback == "smaller-context"


def test_enabled_degradation_without_steps_rejected():
    data = base_config()
    data["generator"]["degradation"] = {"enabled": True, "allow": []}
    with pytest.raises(ValidationError, match="must name at least one explicit"):
        cfg.RaggedizedConfig.model_validate(data)


@pytest.mark.parametrize(
    "base_url",
    [
        "http://user:pass@gateway.invalid/v1",
        "https://token@gateway.invalid/v1",
        "ftp://gateway.invalid/v1",
        "http:///v1",
    ],
)
def test_route_url_credentials_and_schemes_refused(base_url):
    data = base_config()
    data["generator"]["route"]["base_url"] = base_url
    with pytest.raises(ValidationError):
        cfg.RaggedizedConfig.model_validate(data)


def test_missing_route_is_valid_config_with_honest_gap():
    data = base_config()
    data["generator"]["route"] = None
    config = cfg.RaggedizedConfig.model_validate(data)
    assert config.generator.route is None


def test_secrets_store_names_not_values():
    data = base_config()
    data["secrets"] = {"gateway_key": {"kind": "env", "name": "SLAIF_GATEWAY_KEY"}}
    config = cfg.RaggedizedConfig.model_validate(data)
    dumped = config.model_dump_json()
    assert "SLAIF_GATEWAY_KEY" in dumped
    # no value field exists to serialize; nothing secret-shaped is present
    assert '"value"' not in dumped


def test_shared_offline_embedding_policy_refused():
    data = base_config()
    data["embedding"]["exclusive_offline_gpu"] = False
    with pytest.raises(ValidationError, match="exclusive-GPU"):
        cfg.RaggedizedConfig.model_validate(data)


def test_duplicate_profile_names_rejected():
    data = base_config()
    data["profiles"] = [
        {"name": "p", "purpose": "online_query_embedding", "device": "cpu", "dtype": "fp32"},
        {"name": "p", "purpose": "online_rerank", "device": "gpu", "dtype": "fp16"},
    ]
    with pytest.raises(ValidationError, match="unique"):
        cfg.RaggedizedConfig.model_validate(data)


def test_config_load_errors_are_typed(tmp_path):
    with pytest.raises(cfg.ConfigLoadError, match="cannot read config"):
        cfg.load_config(tmp_path / "absent.json")
    bad = tmp_path / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    with pytest.raises(cfg.ConfigLoadError, match="not valid JSON"):
        cfg.load_config(bad)
