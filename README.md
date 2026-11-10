# slaif-raggedized-helper

A local documentation assistant using contextual retrieval, authorized source evidence,
and Qwen through SLAIF API Gateway (English/Slovenian). This checkout contains the
architecture, a tested concentrated OAP scaffold, the foundation package
(objective 002-a): strict configuration, typed generator/embedding/reranker
contracts, model lock/qualification schemas and an offline `raggedized doctor`
command; the complete objective 003 slice (merged as PR #5): the gateway
`POST /v1/responses` generator adapter with bounded HTTP/SSE transport, the
private offline native llama.cpp `/completion` adapter (explicit
offline-diagnostic policy, server-rendered templates via `/apply-template`,
truthful native stop/metric mapping), the bounded explicit
`raggedized probe` qualification probe and real loopback integration tests
([docs/generator-contract.md](docs/generator-contract.md)); and — open on
PR #6 (branch `oap/004-qualification-harness`, not merged) — the
objective 004 finite qualification trial runner (004-a) plus the
004-b/004-c evidence-contract corrections: strict bounded trial
spec/sample/result contracts with cross-field consistency bindings
(actual-ledger-driven analysis recomputation, backend/fingerprint
bindings, provenance pairs, declared-budget reservation, pure
cache/input consistency derivation) and quartile-complete stage
metrics enforced at the construction/serialization/analysis
boundaries, bounded safe spec file input with decoded-Unicode
admission (special-file/FIFO, byte, UTF-8, JSON-decoder and unpaired-
surrogate typed refusals at zero dispatch), the canonical full strict
result contract at CLI serialization with the actual spent-attempt
ledger preserved on post-work rejection, actual
gateway/direct repeated-parent composition under one absolute trial
deadline and one shared dispatch allowance at the real transport
boundary, reproducible nearest-rank caller-wall latency analysis with
available-stage timing summaries, the deterministic explicit synthetic
route and the machine-readable section 23.2 prerequisite projection
([docs/benchmarks/qualification-protocol.md](docs/benchmarks/qualification-protocol.md)).
Real target/hardware/model qualification remains NOT RUN; snapshot/agent
layers are not implemented yet.

The target uses CPU query embedding/search and measured co-resident V100 Qwen Q6 + FP16
reranking, with separate long-context preprocessing and exclusive GPU bulk embedding modes.
Original documents remain the authority for citations. Generated context improves indexing.

- [Architecture](ARCHITECTURE.md) and [source precedence](SOURCE-MAP.md).
- [Original plan](PLAN.md) and [binding update](docs/sources/IMPLEMENTATION-UPDATE-2026-11-01.md).
- [Work program](oap/strategic-instructions/INITIAL-ROADMAP.md) and [requirement coverage](oap/COMPLETENESS.md).
- [OAP runbook](docs/OAP-RUNBOOK.md), [agent setup](docs/AGENT-ROLE-SETUP.md), [recovery](oap/RECOVERY.md).
- [Readiness](docs/READINESS.md), [security](SECURITY.md), [testing](TESTING.md), [DHA](CRITICAL.md).

Scaffold checks require Python 3 and standard POSIX tooling:

```sh
python3 -m unittest discover -s tests/oap -v
python3 oap/bin/check_state.py --repo-root .
```

These commands do not start agents, model services, product jobs or an OAP objective.

Product foundation (objective 002-a; `uv` required for the locked environment):

```sh
uv sync --locked
uv run raggedized --help
uv run raggedized doctor --config config/examples/example-config.json
uv run raggedized qualification gates   # offline section 23.2 prerequisite projection
uv run raggedized qualification plan --config CONFIG.json --spec SPEC.json   # offline, zero I/O
uv run pytest tests/unit -q
uv run pytest tests/integration -q   # 003-b/i/j + 004-a: owned loopback HTTP/SSE, probe and trial composition, synthetic keys
```

`doctor` validates configuration and inspects model manifests offline (zero
inference/download/network; machine-readable JSON; exit 0 ok / 1 issues /
2 usage error). `probe` is the explicit opt-in bounded repeated-parent
qualification probe against the configured gateway route or
offline-diagnostic direct destination (explicit finite
deadline/dispatch/output-token budgets, bounded safe credential
resolution, safe structured evidence; exit 0 complete / 1
not-run-incomplete / 2 usage-config error with zero dispatches / 3
post-work evidence export failure — after the probe returned, whether
or not any dispatch occurred, as its spent-attempt ledger states —
with the full evidence on stdout; import, help and doctor never
dispatch a probe). `qualification` is the objective 004-a finite trial
runner: `gates` prints the machine-readable section 23.2 prerequisite
projection and `plan` validates one strict trial spec offline (both
zero model/HTTP/telemetry I/O; execution NOT_RUN); `run` is the explicit
opt-in execution of one repeated-parent trial against the configured
gateway route or offline-diagnostic direct destination through the real
adapters/transport (`--synthetic` for the deterministic owned MOCK
fixture; exit 0 complete execution status / 1 not-run-incomplete /
2 pre-dispatch refusal with zero dispatches / 3 post-work evidence
export failure). Full reference, spec fields, budget admission/
accounting semantics, quantile definition and evidence classes:
[docs/benchmarks/qualification-protocol.md](docs/benchmarks/qualification-protocol.md),
[docs/foundation.md](docs/foundation.md) and
[docs/generator-contract.md](docs/generator-contract.md).

The `CI` GitHub Actions workflow runs the OAP scaffold checks (Python 3.12-3.14)
plus a separate product job (locked lightweight environment, real product
tests, owned-loopback integration tests, OAP checks, lint; Python 3.12/3.14;
triggers, permissions and results
in [docs/CI.md](docs/CI.md)). CI produces no hardware evidence; live model and
gateway qualification remains NOT RUN. The public product CLI currently
provides `raggedized doctor`, `probe` (explicit opt-in qualification
probe), `qualification gates|plan|run` (finite qualification trials,
explicit opt-in execution) and `--help`/`--version`; further API
commands remain proposed, not available.
Apache-2.0; retain LICENSE and [THIRD_PARTY_NOTICES](THIRD_PARTY_NOTICES).
