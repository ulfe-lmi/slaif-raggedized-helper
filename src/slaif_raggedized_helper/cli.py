"""``raggedized`` console entry (OAP objective 002-a).

Commands
--------
``raggedized --version``
    Print the package version.
``raggedized doctor --config PATH``
    Validate the local configuration and inspect referenced model
    lock/manifest files. Returns a safe machine-readable JSON status with
    actionable missing prerequisites.
``raggedized probe --config PATH --mode {gateway,direct} --deadline-seconds
S --max-dispatches N --max-output-tokens-total T
[--expected-output-a sha256:<64hex>] [--expected-output-b sha256:<64hex>]
[--output PATH]``
    Run the bounded repeated-parent qualification probe against the
    explicitly configured gateway route or materialized offline-diagnostic
    direct destination. Explicit probe opt-in: import, ``--help``,
    ``doctor``, readiness and default tests never dispatch a probe.
    Requires explicit finite budgets (overall wall time, call/attempt
    allowance, total output-token allowance) and actually configured mode
    state; credentials resolve only through deliberate safe operator
    references (never the command line). Emits one safe structured
    evidence document (see docs/generator-contract.md).

Doctor guarantees
-----------------
- zero inference, zero downloads, zero network by default (URLs are checked
  syntactically only; no DNS/connection is attempted);
- secret values are never revealed: secret references report kind and
  presence only, even when the secret is provided via an environment variable;
- a missing route/artifact is an honest issue with an actionable message,
  never a guessed value or an import failure.

Exit codes: ``0`` ok (probe: complete), ``1`` validation/
            prerequisite issues (probe: explicit not-run/incomplete
            with published evidence), ``2`` usage error (probe:
            invalid budgets, mode not configured, config or
            credential errors) with zero dispatches.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
from pathlib import Path

from . import __version__
from .config import ConfigLoadError, SecretRef, load_config, safe_validation_errors
from .schema import ModelManifest

_SHA256_DIGEST_RE = re.compile(r"sha256:[0-9a-f]{64}\Z")

EXIT_OK = 0
EXIT_ISSUES = 1
EXIT_USAGE = 2

# Every online/offline serving role must be covered by a model lock/manifest.
REQUIRED_ROLES = ("generator", "embedding", "reranker")


def _secret_status(ref: SecretRef) -> dict[str, object]:
    """Presence only; the secret value is never read or returned."""
    if ref.kind == "env":
        present = ref.name in os.environ
    else:
        present = Path(ref.name).is_file()
    return {"kind": ref.kind, "present": present}


def _manifest_issue(code: str, message: str) -> dict[str, str]:
    return {"code": code, "message": message}


def run_doctor(config_path: str | Path) -> tuple[int, dict[str, object]]:
    """Run the offline doctor. Returns ``(exit_code, report_document)``.

    The report distinguishes configuration validity (``config``) from
    qualification/readiness (``readiness``): a syntactically valid config with
    missing manifests or absent credential references is ``config: valid`` but
    ``readiness: not_ready`` with actionable issues — never success by omission.
    """
    issues: list[dict[str, str]] = []
    report: dict[str, object] = {
        "status": "ok",
        "config_path": str(config_path),
        "config": "valid",
        "readiness": None,
        "issues": issues,
        "models": None,
        "route": None,
        "secrets": {},
        "version": __version__,
    }

    def issue(code: str, message: str) -> None:
        issues.append(_manifest_issue(code, message))

    config = None
    try:
        config = load_config(config_path)
    except ConfigLoadError as exc:
        code = "CONFIG_MISSING" if "cannot read config" in str(exc) else "CONFIG_INVALID"
        issue(code, str(exc))
        report["config"] = "missing" if code == "CONFIG_MISSING" else "invalid"
    except Exception as exc:  # defensive: doctor must always emit a safe document
        issue("CONFIG_UNEXPECTED", f"unexpected config error: {type(exc).__name__}")
        report["config"] = "invalid"

    if config is not None:
        if config.generator.route is None:
            issue(
                "ROUTE_MISSING",
                "deployment route is not configured; set generator.route "
                "(base_url/model/api/timeout_seconds) for the gateway",
            )
            report["route"] = {"configured": False, "host": None, "model": None}
        else:
            report["route"] = {
                "configured": True,
                "host": config.generator.route.host,
                "model": config.generator.route.model,
            }

        if not config.profiles:
            issue(
                "PROFILES_MISSING",
                "no serving profiles configured; declare explicit "
                "purpose/device/dtype profiles (see docs/foundation.md)",
            )

        if config.generator.route is not None and not config.secrets:
            issue(
                "SECRETS_MISSING",
                "route is configured but no secret references are declared; declare "
                "the gateway key as an env/file reference (values never in config)",
            )
        secret_presence: dict[str, object] = {}
        for name, ref in config.secrets.items():
            status = _secret_status(ref)
            secret_presence[name] = status
            if not status["present"]:
                issue(
                    "SECRET_ABSENT",
                    f"secret reference {name!r} ({ref.kind}:{ref.name}) is not present "
                    "on this host; provision it out-of-band",
                )
        report["secrets"] = secret_presence

        models: list[dict[str, object]] = []
        declared_roles = {lock_ref.role for lock_ref in config.model_locks}
        for role in REQUIRED_ROLES:
            if role not in declared_roles:
                issue(
                    "MODEL_COVERAGE_MISSING",
                    f"no model lock declared for required role {role!r}; every role "
                    "(generator/embedding/reranker) needs a lock/manifest reference",
                )
        for lock_ref in config.model_locks:
            path = Path(lock_ref.path)
            if not path.is_absolute():
                path = Path(config_path).resolve().parent / path
            entry: dict[str, object] = {
                "role": lock_ref.role,
                "path": str(path),
                "status": "missing",
                "issues": [],
            }
            try:
                raw = path.read_text(encoding="utf-8")
                data = json.loads(raw)
            except OSError:
                entry["issues"].append(
                    f"model lock file not found or unreadable: {path} (provide the "
                    "artifact manifest; absence is not a passing check)"
                )
                issue("MODEL_LOCK_MISSING", f"role {lock_ref.role!r}: {path}")
                models.append(entry)
                continue
            except json.JSONDecodeError as exc:
                entry["status"] = "invalid"
                entry["issues"].append(f"model lock is not valid JSON: line {exc.lineno}")
                issue("MODEL_LOCK_INVALID", f"role {lock_ref.role!r}: {path}: invalid JSON")
                models.append(entry)
                continue
            try:
                manifest = ModelManifest.model_validate(data)
            except Exception as exc:
                entry["status"] = "invalid"
                entry["issues"].append(
                    f"model lock schema validation failed: {safe_validation_errors(exc)}"
                )
                issue("MODEL_LOCK_INVALID", f"role {lock_ref.role!r}: {path}: invalid manifest")
                models.append(entry)
                continue

            if manifest.lock.role != lock_ref.role:
                entry["status"] = "role_mismatch"
                entry["issues"].append(
                    f"declared role {lock_ref.role!r} does not match manifest role "
                    f"{manifest.lock.role!r}"
                )
                issue(
                    "MODEL_ROLE_MISMATCH",
                    f"{path}: declared role {lock_ref.role!r} != manifest role "
                    f"{manifest.lock.role!r}",
                )
                models.append(entry)
                continue

            status, manifest_issues = manifest.evaluate()
            summary = manifest.summary()
            entry.update(
                {
                    "model_name": summary["model_name"],
                    "revision": summary["revision"],
                    "license_status": summary["license_status"],
                    "artifact_pinned": summary["artifact_pinned"],
                    "qualification": status,
                    "qualification_mode": summary["qualification_mode"],
                    "issues": manifest_issues,
                }
            )
            entry["status"] = "ok" if status == "qualified" else "unqualified"
            if status != "qualified":
                issue(
                    "MODEL_UNQUALIFIED",
                    f"role {lock_ref.role!r} model {manifest.lock.model_name!r} "
                    f"({path}): " + "; ".join(manifest_issues),
                )
            models.append(entry)
        report["models"] = models
        report["readiness"] = "ready" if not issues else "not_ready"

    report["status"] = "ok" if not issues else "issues"
    return (EXIT_OK if not issues else EXIT_ISSUES), report


def _positive_finite_float_arg(value: str) -> float:
    try:
        number = float(value)
    except ValueError:
        raise argparse.ArgumentTypeError("must be a number")
    if not math.isfinite(number) or number <= 0:
        raise argparse.ArgumentTypeError("must be finite and strictly positive")
    return number


def _positive_int_arg(value: str) -> int:
    try:
        number = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError("must be an integer")
    if number <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return number


def _output_token_total_arg(value: str) -> int:
    try:
        number = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError("must be an integer")
    if number < 2:
        raise argparse.ArgumentTypeError("must be an integer of at least 2")
    return number


def _digest_arg(value: str) -> str:
    if _SHA256_DIGEST_RE.fullmatch(value) is None:
        raise argparse.ArgumentTypeError("must be a sha256:<64 lowercase hex> digest")
    return value


def run_probe(config_path: str, mode: str, deadline_seconds: float,
              max_dispatches: int, max_output_tokens_total: int,
              expected_output_a: str | None, expected_output_b: str | None,
              output_path: str | None) -> int:
    """Run the bounded repeated-parent probe. Returns the process exit code.

    Zero-dispatch guarantees: invalid/missing configuration, an
    unconfigured mode, absent credential references and invalid budget
    arguments all refuse BEFORE any transport is constructed (exit 2).
    The evidence document is safe structured JSON (see probes.py); it is
    written to ``--output`` or stdout.
    """
    # Lazy import: the probe module (and its transport/adapter
    # stack) loads only when the probe is explicitly opted into;
    # import, --help, doctor and readiness stay lightweight and
    # network-free.
    from .probes import ProbeBudgets, run_repeated_parent_probe

    try:
        config = load_config(config_path)
    except ConfigLoadError as exc:
        print(json.dumps({"probe": "repeated-parent", "status": "error",
                          "error": "CONFIG_INVALID",
                          "message": str(exc)}, indent=2, sort_keys=True))
        sys.stdout.write("\n")
        return EXIT_USAGE
    try:
        budgets = ProbeBudgets(
            deadline_seconds=deadline_seconds,
            max_dispatches=max_dispatches,
            max_output_tokens_total=max_output_tokens_total,
        )
    except Exception:
        print(json.dumps({"probe": "repeated-parent", "status": "error",
                          "error": "INVALID_BUDGET",
                          "message": "budgets must be finite and strictly positive "
                                     "(total output tokens >= 2)"},
                         indent=2, sort_keys=True))
        sys.stdout.write("\n")
        return EXIT_USAGE
    expected: dict[str, str] = {}
    if expected_output_a is not None:
        expected["a"] = expected_output_a
    if expected_output_b is not None:
        expected["b"] = expected_output_b
    exit_code, document = run_repeated_parent_probe(
        config, mode, budgets, expected_output_digests=expected)
    rendered = json.dumps(document, indent=2, sort_keys=True) + "\n"
    if output_path is not None:
        try:
            Path(output_path).write_text(rendered, encoding="utf-8")
        except OSError as exc:
            print(json.dumps(
                {"probe": "repeated-parent", "status": "error",
                 "error": "OUTPUT_WRITE_FAILED",
                 "message": ("cannot write evidence file: "
                            + (exc.strerror or "I/O error"))},
                indent=2, sort_keys=True))
            sys.stdout.write("\n")
            return EXIT_USAGE
    else:
        sys.stdout.write(rendered)
    return exit_code


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="raggedized",
        description="Local contextual retrieval foundation CLI (offline by default).",
    )
    parser.add_argument("--version", action="version", version=f"raggedized {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)
    doctor = subparsers.add_parser(
        "doctor",
        help="validate configuration and inspect model manifests offline "
        "(zero inference/download/network)",
    )
    doctor.add_argument("--config", required=True, help="path to the JSON configuration file")
    probe = subparsers.add_parser(
        "probe",
        help="explicit opt-in bounded repeated-parent qualification probe "
        "against the configured gateway route or offline-diagnostic direct "
        "destination (safe structured evidence; no live claims)",
    )
    probe.add_argument("--config", required=True, help="path to the JSON configuration file")
    probe.add_argument("--mode", required=True, choices=("gateway", "direct"),
                       help="the actually configured generation mode to probe")
    probe.add_argument("--deadline-seconds", required=True, type=_positive_finite_float_arg,
                       help="ONE overall wall-time budget for the whole experiment")
    probe.add_argument("--max-dispatches", required=True, type=_positive_int_arg,
                       help="total call/attempt allowance (model dispatches, "
                            "template work and failed connects all consume it)")
    probe.add_argument("--max-output-tokens-total", required=True, type=_output_token_total_arg,
                       help="total output-token allowance across the pair "
                            "(each request gets the even half)")
    probe.add_argument("--expected-output-a", type=_digest_arg, default=None,
                       help="expected sha256 digest of phase A terminal text "
                            "(digest-only exact-output check)")
    probe.add_argument("--expected-output-b", type=_digest_arg, default=None,
                       help="expected sha256 digest of phase B terminal text "
                            "(digest-only exact-output check)")
    probe.add_argument("--output", default=None,
                       help="write the evidence document to this file (default: stdout)")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.command == "doctor":
        exit_code, report = run_doctor(args.config)
        json.dump(report, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
        return exit_code
    if args.command == "probe":
        return run_probe(args.config, args.mode, args.deadline_seconds,
                         args.max_dispatches, args.max_output_tokens_total,
                         args.expected_output_a, args.expected_output_b,
                         args.output)
    parser.error("unknown command")
    return EXIT_USAGE


if __name__ == "__main__":
    raise SystemExit(main())
