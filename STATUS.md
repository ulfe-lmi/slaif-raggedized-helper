# Project status

## Current state (2026-11-10)

- Active objective: 003-c (gateway protocol validation), open on PR #5,
  branch oap/003-generator-adapters-and-cache-probes; live PR/CI/merge
  state is queried on GitHub, not asserted here.
- Product implementation: IN PROGRESS — foundation (objective 002-a,
  merged) plus the 003 gateway/transport slice (open on PR #5, see
  history). Hardware/model qualification: NOT RUN. ICA: NOT RUN.
- The coding client is active on objective 003 (PR #5), not idle.
- Current main is the 002-a merge commit 93b4317 (PR #4); PR #5 builds
  from it.
- The 2026-11-10 human MVP activation re-enabled the strategic runtime
  for the current MVP; the executed program is docs/MVP-EXECUTION-PLAN.md
  (strategic, copied unchanged).
- GitHub branch/PR state must be queried live; no current SHA or active
  objective is asserted in durable constitutions beyond the recorded
  merge commits below.

## Historical events (chronological)

Bootstrap/materialization: VALIDATED LOCALLY, 2026-11-01; 39 helper tests
passed. See docs/bootstrap/BOOTSTRAP-RECEIPT.md for exact scope, evidence
and limitations. Product implementation was absent at that time; no
product order/control signal, commit, push or PR was created during the
bootstrap.

000-a (OAP scaffold publication + CI): merged as PR #1 (merge commit
08b21db). CI covers the OAP scaffold only (docs/CI.md); product/hardware
evidence remains absent.

Architecture revision 2.0 publication: merged as PR #2 (merge commit
976381e). Main CI 42721733037 successful for Python 3.12/3.13/3.14 per the
activated order's verified dependencies.

001-a (environment/contract inventory): merged as PR #3 (merge commit
3178650). Published docs/environment-inventory.md (CPU-only development
host facts; gateway repository contract pinned to
f2df0e82df8766740d9ac169ea56ffd7a3cb1f1e; reported long-context capability
kept separate from unmeasured target configurations; unknown deployed
facts and exact prerequisites), persisted docs/MVP-EXECUTION-PLAN.md
unchanged, and committed the 000 strategic resolution unchanged. No live
service was changed.

002-a (foundation and qualification harness): merged as PR #4 (merge
commit 93b4317, the current main), branched from main 3178650. Added the
installable src package (slaif_raggedized_helper: strict config, typed
generator/embedding/reranker contracts, model lock/qualification schemas,
offline `raggedized doctor`), locked lightweight environment (uv.lock;
pydantic runtime; pytest/ruff dev), focused product tests (tests/unit)
plus an OAP fixture source-copy boundary fix, a separate product CI job,
docs/foundation.md, JSON schemas and THIRD_PARTY_NOTICES. Foundation code
and mocked contract composition only: product runtime qualification
remains NOT RUN/UNKNOWN; no model, GPU, live route or service change.

003 slice (generator adapters + transport/gateway correctness; open on
PR #5, branch oap/003-generator-adapters-and-cache-probes from main
93b4317):
- 003-a PARTIAL checkpoint: the gateway `POST /v1/responses` adapter and
  bounded HTTP/SSE transport (one total deadline, pre-dispatch-only retry,
  UNKNOWN_COMPLETION ambiguity semantics, bounded queue backpressure and
  cancellation) plus real loopback HTTP/SSE integration tests
  (tests/integration) wired into the product CI job; actual behavior and
  contract: docs/generator-contract.md. Round report:
  oap/reports/003-a-generator-adapters-and-cache-probes.md.
- 003-b bounded transport/gateway repair: published round report
  oap/reports/003-b-transport-gateway-correctness.md; strategic review
  CONTINUE/NOT_ACCEPTED at the 003-b report candidate (actual malformed
  wire successes/raw exception and valid multipart rejection contradicted
  criterion 6).
- 003-c (current round): gateway protocol validation repair of the
  remaining structural gaps (malformed type/ID/coordinate/status
  handling, valid multipart streams, deterministic zero-dispatch deadline
  boundary, scoped docs).
- The native direct `/completion` adapter and qualification probes of
  objective 003 remain pending (separately finalized continuations of the
  same PR). Objective 003 as a whole is unresolved, not merged, not
  deployed; no model, GPU, live route or service change.
