# slaif-raggedized-helper

## Implementation update: gateway integration, CPU/GPU split, and shared-V100 online inference

**Date:** 2026-11-01  
**Status:** Binding architectural addendum for coding-plan preparation; not an implementation or benchmark report.  
**Read together with:** `IMPLEMENTATION-PLAN.md` (2026-11-01).  
**Project name:** `slaif-raggedized-helper`.

> **Instructions to the coding agent:** Read BOTH documents in full. Preserve the original plan's data model, evidence provenance, contextual-retrieval algorithm, source handling, security requirements, license policy, evaluation methodology, and most implementation milestones. **Where the documents conflict, this update takes precedence.** Produce one internally consistent coding/implementation plan, with explicit dependencies, benchmarks, acceptance tests, and deployment profiles. Do not silently revert to the original CPU-only production assumption. Do not treat illustrative capacities or anticipated speedups as already measured. Do not alter the original plan merely to hide the differences.

---

## 1. Executive decisions (agreed configuration)

The project implements Anthropic-style Contextual Retrieval for a substantial documentation corpus (illustratively 10,000 pages). It will maintain **two distinct workload profiles** and **three GPU operating modes** rather than pretending all components must run continuously with the same memory allocation.

1. **The online help bot normally calls Qwen through the existing `slaif-api-gateway` `POST /v1/responses` interface.** It must not assume that end users access llama.cpp directly. Follow the gateway's *actual, bounded* Responses contract rather than assuming complete OpenAI feature coverage.
2. **A direct llama.cpp inference adapter is permitted, especially for trusted offline contextualization**, if benchmarking demonstrates significantly better prefix reuse, lower prefill work, or reduced overhead. Direct mode is opt-in, access-controlled, and never exposed as a public bypass around gateway quotas or authorization.
3. **The online query embedder runs on CPU by default.** Each query is short, while the document vectors have already been computed and stored. Keep BGE-M3 resident in RAM; measure CPU query latency. There is no need to load the embedder onto the production V100 unless measured latency justifies a change.
4. **Offline document embedding should use the GPU with exclusive access**, in appropriately sized batches. This is the main high-throughput embedding job. The index stores the result for subsequent CPU-side retrieval. Qwen is not kept resident on the same GPU during this phase.
5. **The reranker runs on the same V100 32 GB GPU as online Qwen, in FP16, if measured VRAM and latency permit.** Initial model: `BAAI/bge-reranker-v2-m3`. This replaces the original plan's CPU-reranking production default.
6. **Reduce the V100 online Qwen context to approximately 32,768 tokens initially**, rather than retaining the 190k-token allocation while serving RAG questions. A 16k-64k tuning sweep is allowed; 32k is the starting point, not a guaranteed optimum or hard limit.
7. **Retain the already-working long-context, vision-enabled Qwen configurations for offline jobs:** approximately 190k on V100 32 GB and approximately 100k on RTX 3090 24 GB. The offline profile and online profile are separate process configurations. No proposal to invalidate or replace the proven long-context setup.
8. **Prefer the existing Q6 model for reference-quality contextualization and initial online deployment.** Test Q4 only when needed for VRAM/performance or as an explicit quality experiment. Do not presume Q4 and Q6 are quality-equivalent.
9. **Do not allocate a separate GTX 1080 or dual-Xeon SGI machine for reranking unless co-residency fails or measurements favor it.** They remain possible fallbacks, not part of the target architecture.
10. **Keep licensing restricted as specified in the original plan:** project-owned code and selected distributable/model components under MIT, BSD, or Apache; audit transitive dependencies and report CUDA/driver/platform exceptions explicitly.

### Default online topology

```text
                   User / authorized calling application
                                    |
                             raggedized API
                                    |
                            authorization scope
                                    |
                 +------------------+------------------+
                 |                                     |
          CPU query embedder                    CPU BM25 search
          BGE-M3 (FP32)                         + dense vector dot
                 |                                     |
                 +-------------+-----------------------+
                               |
                   RRF fusion, filtered candidates
                               |
                        GPU reranker
                 BGE-reranker-v2-m3 (FP16)
                   same V100 as Qwen
                               |
                  original evidence + citations
                               |
                  SLAIF API Gateway /v1/responses
                               |
                  vision-enabled Qwen, Q6, ~32k
                        same V100 32 GB
                               |
                       grounded final answer
```

The reranker and Qwen **co-reside in VRAM**. A single question normally performs reranking *before* Qwen generation; they are not both doing substantial GPU computation simultaneously for that question. Under concurrency they can overlap, so the service must enforce throughput and memory limits.

### Default offline topology

```text
Original documents -> structure/vision extraction -> chunks
                                                 |
                                    contextualize using Qwen
                                  (gateway OR tested direct)
                                    ~190k V100 / ~100k 3090
                                                 |
                                 persist verified annotations
                                                 |
                                    stop/unload Qwen on GPU
                                                 |
                          BGE-M3 batched GPU embedding (FP16)
                                                 |
                          CPU build of BM25 + dense snapshot
                                                 |
                                  atomic publish of snapshot
```

When two different GPUs/hosts are available, one may serve online traffic while the other performs offline work. **Never assume that they are on the same motherboard, share VRAM, or have identical model files.**

---

## 2. Explicit corrections to `IMPLEMENTATION-PLAN.md`

| Original section / wording | Superseding instruction |
|---|---|
| Section 1: local generator integration is generic | Online generator is reached through **`slaif-api-gateway` `POST /v1/responses`** by default. Direct llama.cpp is a configurable offline optimization, and optionally a trusted diagnostic path. |
| Section 3: BGE-M3 is described primarily as a CPU-side operational choice | **CPU for individual online queries; exclusive GPU for bulk offline corpus embedding.** Same pinned embedding model/pooling/tokenizer and vector-space definition. |
| Section 6.6: direct `cache_prompt` / `id_slot` benchmarking without explicit gateway contract | Add gateway-vs-direct comparison. Gateway may filter or translate fields; **do not send undocumented llama.cpp parameters through `/v1/responses`**. Native direct mode can use `/completion` with tested cache/slot controls. |
| Section 6.8: "Initially use CPU FP32 inference or ... optional GPU embedding" | **GPU FP16 batched corpus embedding is the preferred offline baseline**, subject to reference parity testing. CPU FP32 remains the query-time reference/default. |
| Section 7: online retrieval path | Keep hybrid BM25 + dense + RRF + neural reranking + source evidence, but **reranking normally executes on the online V100, not CPU**. Candidate count/batch size remain tunable. |
| Section 7: "Keep the deployed 190k/100k server capability" | Keep it as an **offline profile**. The online V100 Qwen process starts with **32k configured context**, not merely short prompts sent to a 190k server. |
| Section 8: "Production default: Qwen owns the GPU; embedding, BM25, dense search, and reranking run on CPU" | Replace with **CPU query embedding + CPU BM25/vector search + GPU reranking co-resident with online Qwen**. |
| Section 8: "Embedding/reranking GPU passes ... after unloading Qwen" | This continues to apply to **offline bulk embedding**; it does **not** apply to **online reranking** if measured co-residency is safe. |
| Section 12, milestone A | Add GPU co-residency, CPU-vs-GPU embedding parity, gateway/direct protocol checks, two-mode operational safety, and GPU latency benchmarks as **early gates**. |
| Section 12, milestone D: "implement CPU reranking" | Implement **GPU reranking on V100, FP16, bounded batching**, with a CPU or alternate-GPU fallback behind the same interface. |

**Unaffected decisions:** contextual annotations are not authoritative evidence; structural chunking and source spans matter; use separate Qwen/BGE/reranker tokenizers; use BGE-M3 dense embeddings and independent BM25; immutable snapshots; ACL filtering before reranking and answer generation; citations resolve to original sources; vision only when needed; no hosted AI required; model/runtime versions and licenses must be pinned.

---

## 3. Runtime profiles and lifecycle

The codebase must support these **explicit modes**. Operational scripts should perform state transitions and health checks; never assume a new HTTP port implies a new GPU.

### Mode A: `online_rag_v100` (default serving mode)

- Hardware: Tesla V100 32 GB.
- Generator: existing vision-enabled Qwen3.8-27B GGUF, initially Q6.
- Generator context: `32768` tokens initially, with `--parallel 1` as a conservative starting benchmark profile, unless the already-deployed runtime uses an equivalent mechanism. Configure an actual smaller context allocation; sending short prompts to a 190k-configured server is not a substitute.
- Generator API path: **SLAIF Gateway `POST /v1/responses`**. Retain its authentication, policy, model-route selection, accounting, and bounded feature contract.
- Reranker: `BAAI/bge-reranker-v2-m3` on the **same V100** in FP16; isolated worker/process is preferred to control CUDA allocations and failure/restart independently.
- Reranker first batch candidate: 4 query/passage pairs; measure 1, 2, 4, and 8.
- Reranker pair length: start at 768 or 1,280 tokens (under *reranker* tokenizer); do not silently truncate original facts and versions. Test shorter lengths if latency requires.
- Query embedder: BGE-M3, **CPU FP32**, resident in host RAM. Query tokens are generally short, but the model still executes a full forward pass; **benchmark** rather than assume negligible latency.
- Dense index: normalized vectors + CPU dot product / optional FAISS `IndexFlatIP`.
- BM25: CPU.
- Source authorization, fusion, evidence assembly: CPU.
- No online GPU embedding service is required by default.

Keep the original plan's initial evidence budget (~4k-6k tokens, with bounded history, instruction and output reserves). A 32k generator context is a safety/flexibility allowance, not a target to fill.

### Mode B: `offline_context_long` (expensive document contextualization)

- Hardware: whichever established machine is assigned to the batch: V100 with ~190k context **or** RTX 3090 with ~100k context, both supporting vision as already deployed.
- Generator: Qwen Q6 preferred for the reference run; Q4 is an evaluation/VRAM alternative.
- API path: initially support Gateway `/v1/responses`; optionally choose the **direct llama.cpp adapter** after measuring actual prefill and reuse.
- **Do not require the online V100 reranker to remain resident while running a 190k-context Qwen profile.** Stop/unload it when changing to long-context mode on that GPU.
- Chunk processing: group by coherent parent document; stable prefix + varying chunk suffix; checkpoint annotation output to durable storage.
- Cache behavior: test full parent-prefill cost, reused-prefix cost, and recurrent-state correctness for the actual llama.cpp build. Do not assume cache persistence or output equivalence across adapter modes.
- Vision: use it for targeted extraction/verification as specified in the original plan, not every page unconditionally.

If the RTX 3090 runs offline contextualization while the V100 serves traffic, keep service/host boundaries explicit and store outputs in a shared or transferred artifact directory with integrity checks.

### Mode C: `offline_embed_gpu` (exclusive bulk embedding)

- Hardware: dedicated V100 **or** RTX 3090 GPU for the duration of a batch.
- **Unload Qwen and the online reranker from that GPU first**; a different process/port does not guarantee VRAM availability.
- Model: exact same pinned `BAAI/bge-m3` checkpoint and pooling logic as the online query embedder.
- Use GPU FP16 in batches by default; tune batch size and token lengths against measured peak VRAM and throughput. GPU embedding may also be done in FP32 if it is needed for quality or available capacity; it is not mandatory to quantize embeddings.
- Normalize dense vectors consistently and **store them in FP32** for indexing, unless an alternate index format is deliberately validated.
- Durable, resumable batch outputs: mapping of `chunk_id` -> embedding, processing fingerprint, checksum, completion state. Do not re-embed completed, unchanged chunks.
- Build/publish BM25 and exact dense index on CPU afterwards, atomically as in original plan.
- When scheduled on the same GPU as online serving, switch via an explicit maintenance window/operational lock; do not silently terminate active user requests.

**Precision compatibility is a required test:** GPU FP16 document vectors and CPU FP32 query vectors are generated by the same model but need not be bit-identical. Compare both encodings on reference passages and queries; record vector cosine agreement, score/rank stability, and retrieval Recall@k. Pin the same tokenizer, pooling, normalization, text construction, and checkpoint revision. If unacceptable, try GPU FP32 for corpus embeddings or an explicitly validated CPU/ONNX inference path; do not mix embeddings from different *models*.

### Resource-lock/state-machine requirements

```text
             online_rag_v100
              |           ^
     drain user work         restart + health-check
              v           |
      offline_context_long
              |
        persist annotations
              v
       offline_embed_gpu
              |
       build/validate index
              v
      activate snapshot
              |
     restore online services
```

This depicts **one GPU's mutually exclusive heavy-job modes**. On separate hosts, online service and offline work can run in parallel if each host independently respects GPU ownership and access control. Implement actual idempotent start/stop/drain/restore operations and a state/ownership lock. Failure must leave durable job progress intact and must not silently restart an incompatible profile.

---

## 4. Memory budgeting and co-residency: measure before hard-coding

The V100's 32 GB is the controlling resource for online deployment. A smaller Qwen context saves KV-cache memory, but it **does not reduce the Q6 weight size**. Actual footprint also includes recurrent-state buffers, vision projector, temporary compute buffers, CUDA contexts, allocator caching/fragmentation, and reranker activations.

Initial planning hypotheses (not measured facts for this deployment):

- The FP16 weights of a roughly 568M-parameter reranker are about **1.14 GB decimal**, before activations, CUDA workspace, runtime overhead and fragmentation.
- A **2-4 GB reranker VRAM envelope** for modest batches is a *working estimate only*. Some combinations of input length, model implementation, batch size and concurrent requests may exceed it.
- Prior arithmetic suggesting a ~22 GB Q6 weight allocation, ~2 GB 32k KV, or ~5 GB remaining is **illustrative, not an authoritative `nvidia-smi` measurement**. Do not turn those numbers into constants or guarantee that a 32k Q6 vision deployment and reranker will fit.
- Qwen's hybrid attention/recurrent architecture means context-memory calculations need to be matched to the **actual loaded GGUF, KV data types, parallel slots and llama.cpp build**. Do not extrapolate naively from conventional transformer KV formulas.

### Mandatory V100 benchmark matrix

Measure the following **with the real GGUF, projector, MTP configuration, KV configuration and runtime**:

| Trial | Qwen configured context | Reranker FP16 batch | Criterion |
|---|---:|---:|---|
| Baseline | 32k | Not loaded | Qwen alone, cold/warm VRAM and prompt/decode timings |
| Candidate 1 | 32k | 1 | Both loaded; worst-case rerank + Qwen text/vision workload |
| Candidate 2 | 32k | 2 | Both loaded; concurrency 1 |
| **Candidate 3** | **32k** | **4** | **Preferred if stable with memory margin** |
| Candidate 4 | 32k | 8 | Only if VRAM allows and latency benefits |
| Smaller context | 16k / 24k | Best tested | Fallback if 32k cannot safely coexist |
| Larger context | 48k / 64k | Best tested | Optional if it clearly fits and improves answers |
| Quantization A/B | 32k, Q4 vs Q6 | Best tested | Only if Q6 cannot meet capacity/latency targets or for planned quality study |

For every trial, log:

1. GPU physical capacity and `nvidia-smi` process allocation **after loading**, after warm-up, and at **peak** sustained/vision load.
2. CUDA allocator allocated/reserved bytes inside the reranker worker, when applicable.
3. Qwen model/GGUF, projector, KV types, context/slots, batch settings, and build fingerprint.
4. Reranker checkpoint/revision, dtype, max pair length, batch size, peak activation memory, and actual candidate count.
5. Time-to-first-token and decode speed for Qwen, reranking p50/p95, entire RAG p50/p95, GPU power/utilization, and time spent waiting for a GPU slot.
6. Repeatability and behavior after process restart; include realistic simultaneous-query stress testing.

**Safety criterion:** both processes should coexist with a measured margin (initial target at least ~2 GiB remaining at the *observed worst-case peak*, adjustable after tests) and no CUDA OOM, service lockup, or unexpected Qwen correctness regression. Free memory immediately after process initialization alone is insufficient. Size buffers and concurrency for the maximum *permitted* batch and context, not merely an easy warm-up.

If Qwen Q6 + 32k + reranker does **not** safely fit, try in order:

1. Limit reranker batch size to 1-2 and pair length to a validated budget; bound in-flight jobs.
2. Test a 24k or 16k **online** generator context while preserving evidence/output reserves.
3. Reduce configured concurrency/slot and compute-buffer allocations where supported and measured safe.
4. Compare Q4 vs Q6 on accuracy and deployment stability rather than automatically sacrificing the offline Q6 reference.
5. If necessary, switch reranking to CPU or a separate GTX 1080/1080 Ti (mind Pascal FP16 limitations); the old dual-socket SGI CPU host is another measured fallback, **not** an assumed performance solution.

Do not deploy an unstable co-resident setup merely to avoid a second GPU.

---

## 5. Qwen inference adapters and SLAIF Gateway contract

### 5.1 Two adapters behind one application interface

Build one Qwen-facing interface with at least these implementations:

- `SlaifResponsesGenerator` (the normal **online** route): OpenAI-compatible client configured for the organization's gateway base URL and key; calls `POST /v1/responses`, with the route/model identifier configured rather than guessed.
- `DirectLlamaGenerator` (**offline opt-in**): sends requests directly to a known, explicitly configured, private llama.cpp endpoint. For prefix-controlled contextualization, use the **native `/completion` interface** if the installed build implements and verifies `cache_prompt` and `id_slot`; optionally use direct `/v1/responses` if it retains the necessary controls and multimodal behavior.

Recommended logical interface (names illustrative):

```python
class GeneratorClient(Protocol):
    def generate(self, request: GenerateRequest) -> GenerateResult: ...

# Request contains:
#   purpose: context_annotation | visual_extraction | answer
#   trusted metadata, messages or canonical prompt, optional images
#   response schema / desired output, max output tokens, sampling options
#   parent-cache key / slot preference only when adapter supports them
# Result contains:
#   text and parsed structured output (when requested)
#   token usage if actually available, elapsed/prefill/decode metrics
#   adapter name, model/backend fingerprint, failure diagnostics
```

Do not force every backend into the exact same wire format: native `/completion` accepts formatted prompts and may use different multimodal handling. The adapter must preserve equivalent **semantic input and output requirements** and document any cache-specific differences. Cache/slot controls are capabilities, not fields to blindly forward to the gateway.

### 5.2 Online contract: gateway first

- The gateway's README describes `/v1/responses` as a **bounded** implementation, not a promise that every Responses field, JSON-schema mode, caching hint, multimodal message format or tool is supported.
- Before coding the final client, inspect its *current* compatibility matrix, the deployed route's local-Qwen upstream profile, the model catalog and a real successful user request. Pin the gateway version/commit used for testing.
- Support text input, streaming if actually supported on that route, and documented vision inputs when relevant. Gracefully handle non-streaming mode for correctness tests.
- Parse output items according to the gateway's actual Responses schema; do not assume the first output element contains all user-visible text or blindly trust provider-specific extensions.
- Use bounded timeouts, retries only for retryable failures, request IDs, safe error reporting, and **correct accounting** for long offline requests when the gateway is chosen.
- Do not add gateway features or alter its authorization layer merely because the RAG service needs a convenience parameter. First use the documented contract or the explicit direct adapter.
- Keep the public RAG API authenticated and ACL-enforced regardless of the downstream generator path.

### 5.3 Direct mode: allowed for speed, not for security bypass

Direct access is a legitimate engineering option, most attractive in `offline_context_long` where the same 30k-160k-token parent prefix may be reused for many annotations.

- Bind the direct endpoint to loopback/private networking; restrict to a trusted worker identity and host-level access controls (or an authenticated internal proxy where necessary).
- Do not copy a gateway key into the llama.cpp URL or leak secrets into prompts/logs.
- Preserve a per-job record of which adapter generated each annotation. Compare output quality between gateway and direct modes on the same pilot set.
- Avoid exposing `/completion`, `/slots`, `/props`, process management or model-control endpoints to untrusted callers.
- **No direct online bypass by default.** If later proposed, require a deliberate security/accounting review and demonstrated benefit; do not make it an invisible fallback when gateway admission rejects a request.

### 5.4 Prefix-cache benchmark and correctness gate

Benchmark at least 8k, 32k, 80k and near-available-context parent documents:

```text
A. Gateway /v1/responses, chunk A (cold parent)
B. Gateway /v1/responses, chunk B (same parent prefix)
C. Direct llama.cpp, chunk A (cold parent)
D. Direct llama.cpp, chunk B (same parent, cache_prompt / id_slot)
E. Repeat with a vision-relevant parent and with the production MTP options
```

For each path, record **actual newly evaluated prompt tokens**, not simply submitted prompt length or HTTP round-trip time. Compare cold/warm prefill seconds, cache hits/recurrent checkpoint behavior, output-token counts, annotation correctness, and GPU memory. A faster response without evidence of cache reuse is a useful speed result but not proof of prefix caching.

Process a parent's chunks in sequence when cache reuse is available. Keep stable prefix bytes **and tokenized template** identical. If gateway routing changes upstream slots, assume no cache affinity until measured. The direct adapter may explicitly pin a slot, but it must also verify hybrid/recurrent-state correctness and behavior on restart.

If direct mode is **not** faster or alters the annotation quality unacceptably, use the gateway. Offline work is allowed to take more time; do not compromise source fidelity to save prefill.

---

## 6. Embedding and reranking implementation specifics

### 6.1 Offline embedding versus online query embedding

The **same** `BAAI/bge-m3` embedding space must serve both tasks:

| Workload | Default device | Precision | Notes |
|---|---|---|---|
| Corpus vectors (~20k chunks illustrative) | Exclusive GPU | FP16 compute, FP32 stored vectors | Large batches, resumable, profile throughput/VRAM |
| New user query | CPU | FP32 | Single short text or small query batch; keep model loaded |
| Query-corpus similarity | CPU | FP32 dot-product | Normalized vectors, exact search initially |
| BM25 | CPU | N/A | Separate, keyword-aware lexical index |

This difference in inference precision is permitted **only after cross-device parity tests**. Do not replace BGE's CLS pooling or normalize documents and queries differently. Keep exact model/tokenizer revisions and the enrichment-text template recorded in snapshot metadata.

The model must not be loaded *twice* into GPU memory merely because both embedding and reranking use the BGE family. They are separate trained checkpoints for different tasks. **The online embedding model stays on CPU.** The reranker alone needs to coexist with Qwen on V100.

### 6.2 GPU reranking

Initial implementation choices:

- Model: `BAAI/bge-reranker-v2-m3`, pinned checkpoint and tokenizer.
- Device: `cuda` on **V100 32 GB** during online serving.
- Weight/activation precision: **FP16** on V100, verified by a correctness regression against a CPU FP32 reference subset. Do not use BF16 as a presumed V100 feature.
- Default candidate count: **40 after RRF fusion** (keep the original plan's 60 dense + 60 BM25 initial retrieval settings as tunable starting points).
- Start batch size: **4**; reduce or increase according to actual measured memory and throughput.
- Rerank input: query + **contextualized** candidate chunk, with token-length checks. Final Qwen evidence remains original text plus necessary supporting source spans.
- Return scores, sorted IDs, source metadata and timings. Scores measure relative relevance, not factual truth or calibrated confidence.
- Make device, dtype, batch size, candidate count, max pair length and timeout configurable.

A GPU worker can be an internal long-lived process on the V100 host, reachable through a private local socket/loopback, or an isolated process supervised by the service. Do not require a public reranker REST API unless deployment genuinely needs it. Add a readiness probe to distinguish "GPU loaded and ready" from "model configured but failing".

### 6.3 Fallback semantics

- If reranking fails or violates an agreed latency budget, an **explicitly configured** degraded mode may serve RRF-only results; record this in diagnostics and evaluation. Never silently change evidence ranking and claim neural reranking was performed.
- If Qwen/Gateway fails, return a transparent error or a source-only search result as a separate supported API behavior. Do **not** fail open to an unauthenticated direct generator.
- If the embedding model is unavailable, lexical-only retrieval may be a controlled degradation; ACL filtering and citation validation still apply.
- Batch asynchronous offline work may retry; interactive requests should have bounded retries and cancellation.

### 6.4 Benchmark the latency that actually matters

Measure separately:

```text
CPU embed(query)
CPU dense matrix search + BM25 + RRF
GPU rerank(10, 20, 40, 80 candidates; 256, 512, 1024 tokens)
Qwen prefill + decode via gateway
Total end-to-end /v1/answer including network overhead
```

Collect p50, p95, and maximum for both *single-user* and realistic concurrent load, with cold and warm reranker. Publish raw timings and hardware/software configuration. No hard-coded claims that a V100 can rerank 40 passages within a specific number of milliseconds.

For CPU embedding, benchmark the **actual production CPU**, not a newer workstation. The user's older dual-Xeon equipment may be slow at neural inference because of limited SIMD; this is a possible host-placement concern, not a reason to keep all embeddings on GPU by default.

---

## 7. Concrete configuration shape (example, not an implemented API)

Use separate profile files or equivalent configuration. This is a proposed **schema**, not a promise that any specific CLI options, route IDs, services or hostnames already exist:

```yaml
profiles:
  online_rag_v100:
    generator:
      backend: slaif_responses
      base_url_env: SLAIF_GATEWAY_BASE_URL
      api_key_env: SLAIF_GATEWAY_API_KEY
      model_env: SLAIF_QWEN_ROUTE_MODEL
      endpoint: /v1/responses
      desired_context_tokens: 32768
      vision: true
      preferred_quantization: Q6
    query_embedding:
      model: BAAI/bge-m3
      device: cpu
      precision: fp32
      normalize: true
    retrieval:
      initial_dense_k: 60
      initial_bm25_k: 60
      fusion: rrf
      rrf_k: 60
      rerank_k: 40
    reranker:
      model: BAAI/bge-reranker-v2-m3
      device: cuda:0
      dtype: fp16
      batch_size: 4
      max_pair_tokens: 1280
      fallback: explicit_rrf_only
    evidence:
      target_source_tokens: 6000
      generator_input_soft_cap: 12000
  offline_context_long:
    generator:
      backend: configurable_gateway_or_direct
      default_backend: slaif_responses
      direct_url_env: LLAMA_DIRECT_BASE_URL
      direct_cache_probe_required: true
      use_tested_long_context_profile: true
      prefer_quantization: Q6
    unload_online_gpu_reranker_if_same_gpu: true
    checkpoint_each_chunk: true
  offline_embed_gpu:
    embedding:
      model: BAAI/bge-m3
      device: cuda:0
      compute_precision: fp16
      storage_dtype: fp32
      batch_size: auto_benchmark
      normalize: true
    require_exclusive_gpu: true
    require_cpu_fp32_parity_report: true
```

The `desired_context_tokens` field is a **deployment expectation**; the RAG HTTP caller cannot resize an already-running Qwen process. The online Qwen process supervisor must actually start the appropriate llama.cpp server profile and verify it. Keep physical GPU IDs configurable (especially when multiple machines or mixed GPUs exist).

Do not assume that all gateway-supported features are available for all model routes; run a capability probe at deployment and document incompatibilities.

---

## 8. Deployment and operational details to add to the coding plan

### A. Separate worker processes and ownership

Strongly prefer distinct ownership boundaries for:

- `raggedized-api`: authorization, query CPU embedding, BM25/dense retrieval, source evidence and answer/citation handling.
- `raggedized-reranker`: resident GPU cross-encoder worker, one or a few bounded in-flight batches; private access only.
- `raggedized-preprocess`: offline ingestion, extraction, Qwen contextualization and checkpointed GPU corpus embedding (one heavy GPU job at a time per GPU).
- `qwen-online`: existing llama.cpp instance/routing behind SLAIF Gateway, configured for a measured smaller online context.

This is a conceptual separation; systemd, containers or existing supervisors can implement it without introducing Kubernetes or an unnecessary model-serving framework. Avoid creating a second public control plane.

### B. Startup order

For the online V100 profile:

1. Acquire deployment/GPU-mode ownership, confirm no conflicting offline job.
2. Start and health-check Qwen with the **actual online context allocation** and vision projector.
3. Check observed free VRAM before loading the reranker.
4. Load/warm up the reranker with a representative maximum permitted pair length and batch size.
5. Run a concurrent smoke test (reranking followed by Qwen text and vision generation) and check VRAM margin and absence of OOM.
6. Load CPU BGE-M3 and retrieval snapshot, check embedding fingerprint/index compatibility.
7. Open application readiness only after ACL, retrieval, gateway route and citation smoke tests pass.

If a co-residency check fails, prefer a documented degraded/alternate deployment over repeatedly restarting processes into a GPU OOM loop.

### C. Offline transition safeguards

- Drain or reject new online work deliberately; preserve in-flight requests according to configured shutdown timeouts.
- Stop/unload reranker; optionally stop/restart Qwen to enter the selected long-context or embedding profile.
- Record the previously working process/profile metadata before switch.
- Validate owner lock and GPU vacancy; fail instead of forcibly killing unknown processes.
- Checkpoint after every completed annotation/embedding batch.
- On completion or failure, recover the previous online profile and run readiness/health checks. Failed recovery must be visible to operators.

### D. Capacity and performance assumptions

At the 10,000-page scale, raw vector search over tens of thousands of 1,024-dimensional vectors is a CPU task. Using the original plan's example of 20,000 chunks, FP32 vectors occupy about 82 MB decimal. GPU compute is much more valuable for **batch embedding and cross-encoder reranking** than for exact dot-product search on this index size.

The online answer budget remains much smaller than the 32k configured context. Once online Qwen's context shrinks, the freed memory is available for co-resident reranking **only to the extent actually released by the runtime**. A 32k configuration must be benchmarked with vision enabled, not inferred from the old 190k server solely by arithmetic.

---

## 9. Revised pre-implementation experiments and acceptance gates

**Do the following before committing to a deployment implementation.** A coding agent should make them the first executable tasks and attach evidence, not substitute guesses.

| Test ID | Experiment | Required output |
|---|---|---|
| `GATEWAY-01` | Valid text `POST /v1/responses` to the configured local-Qwen route | Request/response shape, route identifier, usage fields, error/stream behavior, gateway version |
| `GATEWAY-02` | Vision input via same route, when supported | Confirmed payload format, image count/size constraints, token/latency handling |
| `DIRECT-01` | Direct llama.cpp contextualization with identical parent prefix, multiple chunks | Cold/warm prefill token counts, cache effectiveness, equivalence checks |
| `GATEWAY-03` | Equivalent repeated-parent jobs through gateway | Gateway vs direct prefill and wall-clock comparison, behavior under provider routing |
| `V100-MEM-01` | Q6 online 32k vision, alone and with FP16 reranker batch 1/2/4/8 | Startup, idle, peak VRAM, margin, OOM/lockups, stable process lifetime |
| `V100-MEM-02` | 16k/24k/48k/64k contexts as necessary | Evidence-based context selection and fallback plan |
| `RERANK-01` | GPU reranker 10/20/40/80 candidate pairs, varying lengths | p50/p95 cold/warm time, peak VRAM, correct ordering vs CPU reference |
| `EMBED-01` | BGE-M3 on production CPU for a short query | p50/p95 latency, RSS and CPU/thread usage |
| `EMBED-02` | Same BGE-M3 checkpoint: corpus-style GPU FP16 vs CPU FP32 | Vector similarity, rank/Recall@k parity, maximum stable batch/throughput |
| `ONLINE-01` | Full hybrid retrieval, GPU rerank, gateway Qwen answer | End-to-end p50/p95, evidence/citation correctness, source ACL enforcement |
| `ONLINE-02` | Two or more simultaneous help-bot requests | Memory and GPU contention, queueing, correct cancellation and no deadlock |
| `OPS-01` | Interrupt contextualization and embedding; reboot workers; resume | No lost/duplicated completed chunks; correct snapshot fingerprints |
| `OPS-02` | Switch online -> offline -> online | Service drain, recovery, health and safe rollback |
| `LICENSE-01` | Dependency/model license and SBOM audit | MIT/BSD/Apache selection plus explicit NVIDIA/Python/platform exceptions |

**Minimum release requirements:**

- A demonstrably stable co-resident online profile (or a documented, tested fallback profile), with memory margin at **observed peak**, not just startup.
- No silent fallback from authorized gateway requests into an unauthenticated direct inference call.
- No unannounced model/tokenizer/precision/index-space mismatch.
- Corpus embedding reproducible enough for evaluation with CPU query embeddings; discrepancies disclosed and measured.
- GPU reranking shows benefit on held-out support questions, or is disabled with an explicit evidence-based decision.
- Authorization is applied before reranker evidence exposure and Qwen generation.
- Original source citations remain intact; generated contextual descriptions are never treated as authoritative citations.
- Offline jobs resume correctly and online service can be restored without losing the published retrieval index.

The actual p95 latency target should be chosen after baseline measurements and a stated expected concurrency level. Do not invent a subsecond guarantee for 40 cross-encoder pairs on V100.

---

## 10. Revised implementation priorities for the coding agent

Merge the original milestone structure with these changes. Suggested order:

**Milestone A0: Existing environment discovery (new and mandatory).**
Inspect current SLAIF Gateway `/v1/responses` compatibility and route; capture current V100/3090 Qwen startup profiles, GGUF/projector hashes, context/KV settings, GPU assignment and model versions. Discover where the actual generator backend runs. Do not patch it in this phase. Produce a verified configuration inventory.

**Milestone A1: GPU-sharing and adapter feasibility (new and mandatory).**
Prototype the gateway Responses adapter, direct llama adapter, repeated-prefix cache benchmark and V100 32k + reranker co-residency benchmark. Measure CPU query embedding and GPU bulk embedding. Outcome: choose safe online profile and offline generator path. This milestone is a gate before assuming deployment topology.

**Milestone B: Preserve original ingestion/chunking/raw hybrid retrieval.**
Implement provenance-respecting ingestion and evaluation-first raw BM25/BGE retrieval. Add CPU query embedder and offline GPU corpus embedder behind the same model/revision contract. Build immutable indices; verify CPU-vs-GPU precision compatibility.

**Milestone C: Document-aware contextualization.**
Implement durable offline Qwen jobs using configurable gateway/direct adapters, stable document prefix and source-backed annotations. Support resume, cache metrics, failure validation, targeted vision extraction and parent version invalidation. Keep Q6 as reference configuration.

**Milestone D: Online V100 help bot.**
Implement GPU FP16 reranker (separately supervised worker preferred), bounded rerank batching, GPU contention protection, source evidence packing, gateway `/v1/responses` answering, citations, authorization and latency reporting. Do not implement CPU reranking as the default simply because the original milestone said so.

**Milestone E: Visual documents and visual answers.**
Retain the original audited PDF rendering, image provenance and selective Qwen vision requirements; validate them with the 32k online allocation and actual gateway input support.

**Milestone F: Operations/security/release.**
Safe online/offline mode transitions, drain/recovery, immutable snapshot activation, ACLs, logging redaction, deterministic fingerprints, benchmarks, licensing audit, rollback, and documented fallback behavior.

**Output expected from the coding agent after reading the two documents:**

1. A **single coherent implementation plan** (not a second contradictory architecture), with resolved online/offline service topology and precise staged work packages.
2. An explicit **supersession list** matching section 2 of this addendum; the old production CPU-reranker assumption must be removed.
3. A dependency/task graph, API contract tests, config schema, file/module plan, and hardware benchmark harness design.
4. An uncertainty register distinguishing **verified installed capabilities** from expectations and benchmark-dependent choices.
5. Milestone exit tests, estimated integration risks, and decisions requiring measured evidence before implementation or release.

Do not silently invent service hostnames, model route IDs, OpenAI Responses features, deployed ports, exact Qwen VRAM allocations, available CPU instruction sets, or license compliance. Discover these from the environment and record them.

---

## 11. Sources, existing plans, and verification status

**Local project documents:**

- `IMPLEMENTATION-PLAN.md` (2026-11-01): normative design details retained unless superseded here.
- This document: new execution/deployment priorities and explicit overrides.

**External reference documentation:**

- SLAIF API Gateway repository and its bounded endpoint contract: https://github.com/ulfe-lmi/slaif-api-gateway
- llama.cpp server API reference (native `/completion`, `cache_prompt`, `id_slot`, tokenization): https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md
- llama.cpp prompt-cache/slot tutorial: https://github.com/ggml-org/llama.cpp/discussions/13606
- BGE-M3 model card and license: https://huggingface.co/BAAI/bge-m3
- BGE model CPU/GPU precision FAQ: https://bge-model.com/FAQ/
- BGE-reranker-v2-m3 model card and license: https://huggingface.co/BAAI/bge-reranker-v2-m3
- Anthropic Contextual Retrieval: https://www.anthropic.com/research/contextual-retrieval

**Verification boundary as of 2026-11-01:** public documentation confirms the types of interfaces and models proposed. It does **not** verify the deployed gateway route's exact accepted payloads, the user's current llama.cpp build/slot-cache behavior, or real VRAM/latency of Qwen Q6 and BGE reranker co-resident on the V100. Those are acceptance tests, not assumptions.

---

## 12. One-sentence target architecture

**Use the V100 in a short-context (`~32k`) online Qwen Q6 + FP16 GPU-reranker configuration, with CPU query embedding and CPU search; use the existing long-context, vision-enabled Qwen deployment for resumable offline contextualization (gateway or benchmark-justified direct access), and give the GPU exclusively to BGE-M3 for batch corpus embedding in a separate offline phase.**
