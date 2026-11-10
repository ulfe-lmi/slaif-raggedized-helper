# slaif-raggedized-helper

A local documentation assistant using contextual retrieval, authorized source evidence,
and Qwen through SLAIF API Gateway (English/Slovenian). This checkout contains the
architecture, a tested concentrated OAP scaffold, the foundation package
(objective 002-a): strict configuration, typed generator/embedding/reranker
contracts, model lock/qualification schemas and an offline `raggedized doctor`
command, and — open on PR #5 (branch `oap/003-generator-adapters-and-cache-probes`,
not merged) — the gateway `POST /v1/responses` generator adapter with bounded
HTTP/SSE transport and real loopback integration tests
([docs/generator-contract.md](docs/generator-contract.md)). The native direct
adapter and qualification probes of objective 003 remain pending; snapshot/agent
layers and hardware qualification are not implemented yet.

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
uv run pytest tests/unit -q
uv run pytest tests/integration -q   # 003-b: owned loopback HTTP/SSE, synthetic keys
```

`doctor` validates configuration and inspects model manifests offline (zero
inference/download/network; machine-readable JSON; exit 0 ok / 1 issues /
2 usage error). Full reference, config schema, contracts and honest
unresolved-artifact state: [docs/foundation.md](docs/foundation.md).

The `CI` GitHub Actions workflow runs the OAP scaffold checks (Python 3.12-3.14)
plus a separate product job (locked lightweight environment, real product
tests, owned-loopback integration tests, OAP checks, lint; Python 3.12/3.14;
triggers, permissions and results
in [docs/CI.md](docs/CI.md)). CI produces no hardware evidence; live model and
gateway qualification remains NOT RUN. Product CLI/API commands beyond
`raggedized doctor`/`--help`/`--version` remain proposed, not available.
Apache-2.0; retain LICENSE and [THIRD_PARTY_NOTICES](THIRD_PARTY_NOTICES).
