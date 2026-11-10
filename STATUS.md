# Project status

## Current state (2026-11-10)

- Active objective: 003-i (probe evidence and credential boundaries),
  open on PR #5, branch oap/003-generator-adapters-and-cache-probes;
  live PR/CI/merge state is queried on GitHub, not asserted here.
- Product implementation: IN PROGRESS — foundation (objective 002-a,
  merged) plus the 003 gateway/transport/native slice and the bounded
  explicit probe/CLI composition (open on PR #5, see history).
  Hardware/model qualification: NOT RUN. ICA: NOT RUN.
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
- 003-c: gateway protocol validation repair of the
  remaining structural gaps (malformed type/ID/coordinate/status
  handling, valid multipart streams, deterministic zero-dispatch deadline
  boundary, scoped docs); round report
  oap/reports/003-c-gateway-protocol-validation.md; strategic review
  CONTINUE/NOT_ACCEPTED at the 003-c report candidate (six supplied-null /
  part-coordinate / item-type / done-latch / reasoning-status variants
  still produced TERMINAL).
- 003-d: structural validation closure of the shared coordinate and
  item-lifecycle invariants behind those six variants (supplied-null vs
  absent coordinates, bounded sequential content-part numbering bound to
  final part positions, item type/identity freeze added through done/
  final, latched item completion, per-type terminal done status),
  actual-HTTP regressions, scoped docs.
- 003-e: the private trusted OFFLINE native llama.cpp
  `/completion` adapter (model_clients/direct.py): explicit
  offline_diagnostic materialization policy (private/loopback destination,
  private_trusted, declared model identity, template qualification,
  explicit finite operator limits), annotation-only purpose with visual/
  image and answer refusals before any network work, server-rendered
  templates through the pinned `/apply-template` contract (no local
  rendering, no local name allowlist; corrected pinned reference
  template registry), exact bounded `/completion` envelopes with
  tested-only cache_prompt/id_slot, one total deadline spanning template
  work + generation + retries (pre-inference expiry refuses), finite
  pre-dispatch-only retry, the fail-closed stop-terminal matrix (stop=true
  is stopped, not successful; only eos with usable content succeeds),
  metric mapping from the pinned dialect's actual reported fields
  (tokens_cached is the slot prompt total, never a cache-hit
  substitute), actual-HTTP loopback regressions, the narrow
  JSON-integer-digit-limit ValueError guard at the gateway non-stream
  parse with actual-HTTP regressions (in-process and a controlled-limit
  isolated subprocess), regenerated JSON schema and scoped docs. Whole-003
  probe / live qualification remains pending.
- 003-f/g: native metric-quantity and default-deny JSON/schema
  corrections, then the native boundary closure (safe finite phase-total
  arithmetic; explicit required-JSON_MODE capability admission) with
  actual-HTTP regressions; round reports
  oap/reports/003-f-native-contract-corrections.md and
  oap/reports/003-g-native-boundary-closure.md.
- 003-h: the bounded explicit generator qualification
  probe (`src/slaif_raggedized_helper/probes.py` + `raggedized probe`
  CLI): explicit opt-in repeated-parent experiment with one overall
  experiment deadline, finite call/attempt and total output-token
  budgets enforced at the real transport boundary (call allowance
  reserved before every transport invocation; ambiguous dispatched
  work spent and never replayed; retries/template work cannot bypass
  the budget), safe structured evidence (declared unverified
  identities, opaque endpoint digest, fingerprinted inputs,
  digest-only output checks, reported-metric-only cache conclusions),
  installed-CLI subprocess composition over owned loopback HTTP, the
  documented gateway minimum-capability admission repair (explicit
  required JSON_MODE/PROMPT_CACHING honored independently of the
  format/cache-key fields; unqualified minimums refuse at zero HTTP;
  qualified minimum-only and ordinary TEXT positive controls retained),
  and docs/README/TESTING/STATUS updates. Live qualification,
  caching-effectiveness and hardware evidence remain NOT RUN.
- 003-i (current round): probe evidence and credential boundary
  corrections over the same probe/CLI, scoped to the demonstrated
  gaps: bounded, non-blocking, regular-file-only single-line
  credential resolution with fixed typed missing/invalid outcomes
  (no raw UnicodeDecodeError; owned FIFO refused without a blocking
  open and no killed child) and file references recorded in evidence
  as opaque digests (no private path, no value); label-independent
  same/different output evidence with phase-identity fingerprints kept
  separate and the documented namespaced expected-digest format;
  reported-vs-validated cache counters (supported accounting relation
  checked before any qualification conclusion; contradictory
  counters are raw facts only and unqualified; the pinned gateway
  dialect's reported cached_tokens corrected as distinct from its
  absent evaluated-prefill metrics); exported declared backend
  fingerprint per request and in identities with `target_type:
  unverified` replacing the unsupported hard-coded fixture/live
  classification; knowably invalid `--output` destinations refused
  before dispatch (exit 2, zero HTTP) and post-work write failures
  returning the honest exit-3 export-stage error with the full
  spent-attempt evidence on stdout. Unit and installed-CLI owned-
  loopback regressions for every corrected case plus the retained
  003-h positive controls; docs/README/TESTING/STATUS updates. Live
  qualification, caching-effectiveness and hardware evidence remain
  NOT RUN.
- The live-target evidence of objective 003 remains pending (separately
  finalized continuations of the same PR). Objective 003 as a whole is
  unresolved, not merged, not deployed; no model, GPU, live route or
  service change.
