# Evidence gaps — bootstrap baseline

These are qualification work, not D1 judgment debt. All start NOT RUN/UNKNOWN.

| ID | Unknown | Resolving work / blocked claim |
|---|---|---|
| U01 | Deployed gateway commit, local-Qwen route and successful accepted payload | 001/003; no live Responses compatibility claim |
| U02 | Actual host/GPU UUIDs, Qwen/GGUF/projector/KV/MTP/runtime/startup fingerprints | 001/004; no deployment profile mutation |
| U03 | Q6 32k vision + FP16 reranker peak margin/concurrency | 004/019; no co-resident readiness |
| U04 | CPU query latency and CPU/GPU embedding parity | 004/007; no mixed-precision qualification |
| U05 | Gateway/direct prefix reuse and hybrid correctness | 003/004; no caching speedup claim |
| U06 | Representative corpus rights/ACL/language/versions and human gold questions | 005/009; no final quality claim |
| U07 | Exact distributions/model licenses/PDF binary dependencies | 002/016/018; no redistribution clearance |
| U08 | Product p95 objective and expected concurrency after baseline | 004/019; no latency promise |
| U09 | Real GPU/service/corpus/inference authorization scopes | relevant live orders; independent code/harness work may proceed |
| U10 | Actual installed-client fresh-context instruction discovery | operational qualification; helper fixtures alone do not prove it |
| U11 | Human signing/attribution configuration for mechanical DHA gate clearing | human setup before applicable adjudication; no fabricated approval |

Record observations with date and exact revision. Preserve superseded interpretations and
distinguish failed tests from environment access blockers. No placeholders count as evidence.

## Observations

### 2026-11-10, order 001-a (environment inventory)

- U01 narrowed: the gateway repository contract is pinned to ulfe-lmi/slaif-api-gateway
  commit f2df0e82df8766740d9ac169ea56ffd7a3cb1f1e (version 0.1.0rc2) with its bounded
  endpoint families and Responses contract documented in
  docs/environment-inventory.md. Still unknown: the deployed gateway commit, the
  local-Qwen route identity/capabilities and a successful accepted payload; the
  repository's "Qwen3.8-27B text / Codex 0.148 candidate" is explicitly
  `mocked-conformant, unregistered, live target absent`. No live Responses
  compatibility claim.
- U02 narrowed: the coding development host (Ubuntu 26.04.1, 40 logical CPU, 121 GiB RAM)
  has no NVIDIA device, tool or CUDA install, no model caches and no local model
  processes; it is a CPU-only development host. Target GPU hosts, Qwen/GGUF/projector/
  KV/MTP/runtime/startup fingerprints remain unknown. No deployment profile mutation.
- U03-U11 unchanged by this round; their resolving work stands.

### 2026-11-10, order 003-h (bounded probes and objective closure)

- The bounded explicit probe/CLI composition is now executable
  (`raggedized probe`, objective 003 criterion 5 tooling) with synthetic
  owned-loopback evidence only: U05 (gateway/direct prefix reuse)
  remains OPEN — no live prefix-reuse, cache-hit or speedup observation
  exists; the probe's cache conclusion is driven solely by reported
  evaluated metrics of the second phase and stays unqualified whenever
  they are absent (the gateway dialect never reports prefill/cache
  metrics).
- U01 narrowed further: the gateway adapter's explicit-minimum
  capability admission (required JSON_MODE/PROMPT_CACHING independent of
  the format/cache-key fields) is now enforced and regression-tested
  over real loopback HTTP; this is wire-level admission behavior at the
  pinned contract revision, not live compatibility proof.
- U02-U4, U06-U11 unchanged by this round; their resolving work stands.
No live target/model/GPU/corpus work was performed (order 003-h live
authorization: NONE); the certifi (MPL-2.0) policy gate remains an open
human question.

### 2026-11-10, order 003-i (probe evidence and credential boundaries)

- U05 CORRECTION of the 003-h observation (superseded wording
  preserved above): the pinned gateway dialect (f2df0e82,
  responses_gateway.py usage handling) DOES report
  `usage.input_tokens_details.cached_tokens` — the 003-h wording that
  the gateway "never reports prefill/cache metrics" was wrong for the
  cache half. It remains true that the pinned dialect does NOT report
  evaluated-prefill metrics (prefill stays null/unavailable). The
  probe now validates the supported accounting relation
  (`cache_hit_tokens <= input_tokens` when both are reported; the
  pinned gateway validates `cached + cache_write <= input_tokens`)
  before any qualification conclusion: a valid present cached counter
  qualifies (`cache_hit_reported`), the demonstrated contradictory
  cached-999/input-5 case is `metrics_invalid` with the raw facts
  preserved as such only, an uncheckable relation is
  `metrics_unvalidated`, and absent counters stay
  `metrics_unavailable`. No live prefix-reuse, cache-hit or speedup
  observation exists; U05 stays OPEN for real qualification.
- U05 also narrowed on tooling: the probe now records
  label-independent same/different output evidence (equal outputs
  never establish truth, caching or quality), exports the declared
  backend fingerprint (the endpoint hash alone does not bind all
  backend controls), and classifies the destination as
  `target_type: unverified` (a localhost address or order live
  allowance cannot establish target type).
- No live target/model/GPU/corpus work was performed (order 003-i
  live authorization: NONE); the certifi (MPL-2.0) policy gate
  remains an open human question.
