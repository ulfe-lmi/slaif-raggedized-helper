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
``raggedized qualification gates``
    Print the machine-readable prerequisite projection of the
    architecture section 23.2 mandatory experiment matrix (offline;
    zero model/HTTP/telemetry I/O; real trials NOT_RUN).
``raggedized qualification plan --config PATH --spec PATH``
    Offline qualification plan for one finite repeated-parent trial
    spec: validates the strict spec against the configured identities
    and prints the deterministic plan (workload fingerprints, sequence
    shape, budgets, declared identities, gate projection) with
    execution NOT_RUN. Zero model/HTTP/telemetry I/O; a rejected plan
    is exit 2 with exact safe reasons (zero dispatch).
``raggedized qualification run --config PATH --spec PATH [--synthetic]
[--output PATH]``
    EXPLICIT OPT-IN execution of one finite repeated-parent trial
    against the configured gateway route or materialized offline-
    diagnostic direct destination through the real adapters and real
    transport. One absolute trial deadline and one shared dispatch
    admission allowance span all warmups, repetitions, retries,
    template and model calls (enforced at the transport dispatch
    boundary). ``--synthetic`` is the deterministic explicit synthetic
    route: an owned loopback fixture is started by the process, the
    evidence is labeled MOCK / synthetic-owned-fixture and configured
    secrets are never read. Missing target/adapter prerequisites give
    exact NOT_RUN/BLOCKED evidence, never fake runnable successes.
    Exit codes as ``probe`` (0 complete execution status / 1
    not-run-incomplete / 2 pre-dispatch refusal with zero dispatches /
    3 post-work evidence export failure with the full safe evidence on
    stdout).
    Run the bounded repeated-parent qualification probe against the
    explicitly configured gateway route or materialized offline-diagnostic
    direct destination. Explicit probe opt-in: import, ``--help``,
    ``doctor``, readiness and default tests never dispatch a probe.
    Requires explicit finite budgets (overall wall time, call/attempt
    allowance, total output-token allowance) and actually configured mode
    state; credentials resolve only through deliberate safe operator
    references (bounded, regular-file-only, single-line reads; never the
    command line) BEFORE any HTTP. Emits one safe structured evidence
    document (see docs/generator-contract.md). A knowably invalid
    ``--output`` destination is refused before dispatch; a write failure
    that occurs after the probe returned is an honest post-work
    export-stage error (exit 3) with the full evidence document on
    stdout.

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
            invalid budgets, mode not configured, invalid config,
            absent or invalid credential reference, invalid evidence
            output destination) — always with zero dispatches — and
            ``3`` probe evidence export failure AFTER the probe
            returned (the full evidence document, including the
            transport-boundary spent-attempt accounting that states
            whether dispatch occurred, is written to stdout; blind
            replay is not safe).
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
import tempfile
from pathlib import Path

from . import __version__
from .config import ConfigLoadError, SecretRef, load_config, safe_validation_errors
from .schema import ModelManifest

_SHA256_DIGEST_RE = re.compile(r"sha256:[0-9a-f]{64}\Z")

EXIT_OK = 0
EXIT_ISSUES = 1
EXIT_USAGE = 2
EXIT_EVIDENCE_EXPORT = 3

# Every online/offline serving role must be covered by a model lock/manifest.
REQUIRED_ROLES = ("generator", "embedding", "reranker")


def _output_destination_refusal(output_path: str) -> str | None:
    """Pre-dispatch validation of the evidence ``--output`` destination.

    Returns a safe refusal reason when the destination is KNOWABLY
    invalid before any dispatch (so the CLI refuses with exit 2 and
    zero HTTP), or ``None`` when it is structurally writable (003-i
    criterion 6). A write that fails only after the experiment has
    already dispatched is a distinct post-dispatch export failure
    (exit 3 with the full evidence on stdout), never a misleading
    zero-dispatch usage error.

    A destination whose parent cannot be searched (e.g. mode 000) is
    also knowably invalid: nothing inside it can be written. The stat
    helpers behave differently across interpreter versions (Python 3.12
    ``Path.exists()`` raises ``PermissionError`` there, newer
    interpreters return ``False``), so every filesystem probe is
    exception-safe and any unprovable destination refuses pre-dispatch.
    """
    target = Path(output_path)
    parent = target.parent
    try:
        if not parent.exists():
            return "evidence output parent directory does not exist"
        if not parent.is_dir():
            return "evidence output parent path is not a directory"
        if target.exists():
            if not target.is_file():
                return "evidence output path exists and is not a regular file"
            # A pre-existing regular file the current user cannot write
            # is knowably invalid before any dispatch; the write would
            # fail only after costly transport work (late export
            # failure).
            if not os.access(target, os.W_OK):
                return "evidence output file exists and is not writable"
        # Prove writability of the parent directory by creating and
        # removing a private temp file (safe local filesystem work; no
        # network).
        fd, tmp = tempfile.mkstemp(prefix=".probe-output-precheck-",
                                   dir=str(parent))
    except OSError as exc:
        return ("evidence output directory is not searchable or "
                "writable: " + (getattr(exc, "strerror", None)
                                or "I/O error"))
    try:
        os.close(fd)
        os.unlink(tmp)
    except OSError:
        pass
    return None


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
    unconfigured mode, an absent or invalid credential reference,
    invalid budget arguments and a knowably invalid ``--output``
    destination all refuse BEFORE any transport is constructed (exit 2,
    always zero HTTP). A write failure that occurs AFTER the probe has
    returned is an honest post-dispatch export-stage error (exit 3):
    the full safe evidence document — including the transport-boundary
    spent-attempt accounting that states whether dispatch occurred — is
    written to stdout and blind replay is not invited.

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
    if output_path is not None:
        # Reject a knowably invalid destination BEFORE the costly calls
        # (003-i criterion 6): exit 2 keeps its zero-dispatch promise.
        refusal = _output_destination_refusal(output_path)
        if refusal is not None:
            print(json.dumps({"probe": "repeated-parent", "status": "error",
                              "error": "OUTPUT_DESTINATION_INVALID",
                              "message": refusal + " (refused before any "
                                         "dispatch; no HTTP was sent)"},
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
        except OSError:
            # Late write failure after the probe returned: an honest
            # export-stage outcome, not a usage error. The full safe
            # document is preserved on stdout and the stage states
            # honestly whether any transport call occurred.
            attempted = int(
                document.get("transport_boundary", {})
                .get("attempted_calls", 0) or 0)
            if attempted:
                dispatch_note = (
                    f"{attempted} transport call(s) were attempted "
                    "(see transport_boundary in the evidence) — do not "
                    "replay blindly: ambiguous or spent work may have "
                    "occurred")
            else:
                dispatch_note = (
                    "no transport call was attempted by this run; the "
                    "document carries the pre-dispatch refusal facts")
            sys.stdout.write(rendered)
            print(json.dumps(
                {"probe": "repeated-parent", "status": "error",
                 "error": "EVIDENCE_EXPORT_FAILED",
                 "stage": "post_work_evidence_export",
                 "message": ("evidence file write failed after the probe "
                             "returned; the full document was written to "
                             "stdout; " + dispatch_note)},
                indent=2, sort_keys=True), file=sys.stderr)
            return EXIT_EVIDENCE_EXPORT
    else:
        sys.stdout.write(rendered)
    return exit_code


def run_qualification_gates() -> int:
    """Print the machine-readable prerequisite projection (offline).

    Zero model/HTTP/telemetry I/O: the projection is a pure rendering of
    the architecture section 23.2 matrix with real trials NOT_RUN (live
    target authorization NONE).
    """
    from .qualification import gate_projection_bytes

    sys.stdout.buffer.write(gate_projection_bytes())
    return EXIT_OK


def _load_qualification_inputs(
        config_path: str, spec_path: str) -> tuple[int, object, object]:
    """Safe config/spec loading; (exit_code, config, spec or error doc)."""
    try:
        config = load_config(config_path)
    except ConfigLoadError as exc:
        print(json.dumps({"qualification": "trial", "status": "error",
                          "error": "CONFIG_INVALID", "message": str(exc)},
                         indent=2, sort_keys=True))
        sys.stdout.write("\n")
        return EXIT_USAGE, None, None
    # Bounded safe spec input (004-b criterion 1): the descriptor
    # actually opened is type-checked (special files refuse without
    # blocking), the read is byte-bounded, UTF-8 is strict, and the
    # expected JSON decoder/integer/depth failures are fixed typed
    # refusals — before fingerprinting or dispatch, at zero HTTP.
    from .qualification.specio import load_trial_spec_json

    data, refusal = load_trial_spec_json(spec_path)
    if refusal is not None:
        print(json.dumps({"qualification": "trial", "status": "error",
                          "error": refusal.error,
                          "reason": refusal.reason,
                          "message": refusal.message},
                         indent=2, sort_keys=True))
        sys.stdout.write("\n")
        return EXIT_USAGE, None, None
    from .qualification import TrialSpec
    try:
        spec = TrialSpec.model_validate(data)
    except Exception as exc:
        print(json.dumps({"qualification": "trial", "status": "error",
                          "error": "SPEC_INVALID",
                          "message": safe_validation_errors(exc)},
                         indent=2, sort_keys=True))
        sys.stdout.write("\n")
        return EXIT_USAGE, None, None
    return EXIT_OK, config, spec


def run_qualification_plan(config_path: str, spec_path: str) -> int:
    """Offline qualification plan (zero model/HTTP/telemetry I/O)."""
    code, config, spec = _load_qualification_inputs(config_path, spec_path)
    if code != EXIT_OK:
        return code
    from .qualification import plan_trial

    exit_code, document = plan_trial(config, spec)
    sys.stdout.write(json.dumps(document, indent=2, sort_keys=True) + "\n")
    return exit_code


def run_qualification_run(config_path: str, spec_path: str,
                          synthetic: bool, output_path: str | None) -> int:
    """EXPLICIT opt-in trial execution. Returns the process exit code.

    Zero-dispatch guarantees: invalid/missing config or spec, a spec/
    config consistency refusal, an unconfigured target, an absent or
    invalid credential reference and a knowably invalid ``--output``
    destination all refuse BEFORE any transport is constructed (exit 2,
    always zero HTTP). A write failure that occurs AFTER the trial
    returned is an honest post-work export-stage error (exit 3): the
    full safe evidence document — including the transport-boundary
    spent-attempt accounting that states whether dispatch occurred — is
    written to stdout and blind replay is not invited.
    """
    code, config, spec = _load_qualification_inputs(config_path, spec_path)
    if code != EXIT_OK:
        return code
    if output_path is not None:
        refusal = _output_destination_refusal(output_path)
        if refusal is not None:
            print(json.dumps({"qualification": "trial", "status": "error",
                              "error": "OUTPUT_DESTINATION_INVALID",
                              "message": refusal + " (refused before any "
                                         "dispatch; no HTTP was sent)"},
                             indent=2, sort_keys=True))
            sys.stdout.write("\n")
            return EXIT_USAGE
    from .qualification import TrialEvidence, run_trial
    from pydantic import ValidationError

    exit_code, document = run_trial(config, spec, synthetic=synthetic)
    # Serialization-boundary invariant (004-b criterion 2): the full
    # result envelope must satisfy the strict sample/result contract
    # before it is rendered or exported. A violation is an internal
    # post-work failure (honest exit 3), never a silent export.
    if document.get("status") in ("complete", "incomplete", "not_run"):
        try:
            TrialEvidence.model_validate(document)
        except (ValidationError, ValueError):
            attempted = int(
                document.get("transport_boundary", {})
                .get("attempted_calls", 0) or 0)
            dispatch_note = (
                f"{attempted} transport call(s) were attempted (see the "
                "runner transport-boundary ledger) — do not replay "
                "blindly: ambiguous or spent work may have occurred"
                if attempted else
                "no transport call was attempted by this run")
            print(json.dumps(
                {"qualification": "trial", "status": "error",
                 "error": "EVIDENCE_CONTRACT_VIOLATION",
                 "stage": "post_work_evidence_contract",
                 "message": ("the evidence document failed the strict "
                             "sample/result contract (internal "
                             "invariant); no evidence is claimable; "
                             + dispatch_note)},
                indent=2, sort_keys=True), file=sys.stderr)
            return EXIT_EVIDENCE_EXPORT
    rendered = json.dumps(document, indent=2, sort_keys=True) + "\n"
    if output_path is not None:
        try:
            Path(output_path).write_text(rendered, encoding="utf-8")
        except OSError:
            attempted = int(
                document.get("transport_boundary", {})
                .get("attempted_calls", 0) or 0)
            if attempted:
                dispatch_note = (
                    f"{attempted} transport call(s) were attempted "
                    "(see transport_boundary in the evidence) — do not "
                    "replay blindly: ambiguous or spent work may have "
                    "occurred")
            else:
                dispatch_note = (
                    "no transport call was attempted by this run; the "
                    "document carries the pre-dispatch refusal facts")
            sys.stdout.write(rendered)
            print(json.dumps(
                {"qualification": "trial", "status": "error",
                 "error": "EVIDENCE_EXPORT_FAILED",
                 "stage": "post_work_evidence_export",
                 "message": ("evidence file write failed after the trial "
                             "returned; the full document was written to "
                             "stdout; " + dispatch_note)},
                indent=2, sort_keys=True), file=sys.stderr)
            return EXIT_EVIDENCE_EXPORT
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
    qualification = subparsers.add_parser(
        "qualification",
        help="finite qualification trials: offline gates/plan (zero I/O) "
             "and explicit opt-in repeated-parent execution over the real "
             "gateway/direct application code",
    )
    qualification_sub = qualification.add_subparsers(
        dest="qualification_command", required=True)
    qualification_sub.add_parser(
        "gates",
        help="print the machine-readable section 23.2 prerequisite "
             "projection (offline; real trials NOT_RUN)",
    )
    qual_plan = qualification_sub.add_parser(
        "plan",
        help="offline trial plan for one strict spec (zero "
             "model/HTTP/telemetry I/O; execution NOT_RUN)",
    )
    qual_plan.add_argument("--config", required=True,
                           help="path to the JSON configuration file")
    qual_plan.add_argument("--spec", required=True,
                           help="path to the strict trial spec JSON file")
    qual_run = qualification_sub.add_parser(
        "run",
        help="EXPLICIT opt-in trial execution against the configured "
             "gateway route or offline-diagnostic direct destination "
             "(--synthetic: owned deterministic MOCK fixture; safe "
             "structured evidence; no live claims)",
    )
    qual_run.add_argument("--config", required=True,
                          help="path to the JSON configuration file")
    qual_run.add_argument("--spec", required=True,
                          help="path to the strict trial spec JSON file")
    qual_run.add_argument("--synthetic", action="store_true",
                          help="use the deterministic explicit synthetic "
                               "route (owned loopback fixture; evidence "
                               "labeled MOCK; configured secrets never "
                               "read)")
    qual_run.add_argument("--output", default=None,
                          help="write the evidence document to this file "
                               "(default: stdout)")
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
    if args.command == "qualification":
        if args.qualification_command == "gates":
            return run_qualification_gates()
        if args.qualification_command == "plan":
            return run_qualification_plan(args.config, args.spec)
        return run_qualification_run(args.config, args.spec,
                                     args.synthetic, args.output)
    parser.error("unknown command")
    return EXIT_USAGE


if __name__ == "__main__":
    raise SystemExit(main())
