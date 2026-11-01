# slaif-raggedized-helper

A planned local documentation assistant using contextual retrieval, authorized source evidence,
and Qwen through SLAIF API Gateway. This checkout currently contains architecture and a tested
concentrated OAP scaffold; the RAG application and hardware qualification are not implemented.

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

These commands do not start agents, model services, product jobs or an OAP objective. The same
two commands run in the `CI` GitHub Actions workflow (OAP scaffold scope only; triggers,
matrix, permissions and results in [docs/CI.md](docs/CI.md)). CI produces no product or
hardware evidence. Product CLI/API commands in the plan are proposed, not available.
Apache-2.0; retain LICENSE.
