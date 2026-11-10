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
