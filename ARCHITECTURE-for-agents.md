# Executor architecture — revision 1.0

Source: `ARCHITECTURE.md`; SHA-256: `48809e248ef226607a2bec27de99b995abe15cc2094dd37b819c0d2c065748fc`.
This is the operative coding projection of A01–A40. Follow the full source's authority;
report a real gap and request a bounded source excerpt or corrected projection. Do not
load the full architecture/roadmap/two input specifications on every coding round.

## A01–A04: product, topology, dependencies

Build local contextual retrieval for documentation, English/Slovenian, expensive resumable
offline preparation and bounded online cited answers. No autonomous tools/shell, ticket
actions, GraphRAG, summary hierarchy, training, cloud requirement, hosted vector DB or K8s.
Python 3.12+ src package, explicit interfaces, FastAPI, files/locks; exact versions get pinned.
CPU API/retrieval, private resident GPU reranker, offline worker, existing external gateway/Qwen.
Default ONLINE: gateway `/v1/responses` → Qwen3.8-27B Q6 vision, actual server 32768 context,
parallel 1 initially; same V100 32 GB reranker FP16; CPU FP32 BGE-M3 queries and CPU search.
OFFLINE CONTEXT: preserve proven ~190k V100/~100k 3090 profiles; unload reranker on same GPU.
OFFLINE EMBED: exclusive GPU, Qwen/reranker unloaded; BGE-M3 FP16 compute, FP32 stored vectors.
Qualification must establish these profiles; reported existing capability is not new proof.
No BF16 assumption on V100, extra GPU requirement, assumed co-location or invented VRAM.
Q6 reference; Q4 only explicit quality/capacity comparison. Safe measured fallback is explicit.
Apache-2.0 original code; direct application/models/assets MIT/BSD/Apache; exact transitive
license/SBOM/notice audit. PSF and NVIDIA terms are separate platform disclosures. Never widen
allowlist automatically. PDF renderer wheels/native deps need audit; source rights separate.
Pin model/tokenizer/runtime/quantizer/GGUF/projector/KV/MTP provenance; preserve existing runtime.

## A05–A12: originals, chunks, context, jobs

Manifest: logical ID, immutable revision/hash, canonical URI, title/product/authority/version/
date/language/ACL/extraction/rights. Dedup bytes while retaining distinct rights/provenance.
Allowlisted roots/domains; resource-limited read-only extraction; preserve headings, lists,
code, tables/headers/units/captions/anchors/order/warnings. Native text first; normalized copy
separate. Blocks record origin and real coordinates only. Chunks retain exact original spans,
neighbors, ACL/version, separate annotation/support IDs/mode/validation/fingerprints/counts.
Generator, embedding, reranker and lexical analyzers are distinct. Use serving GGUF/template
for generator budget and actual image overhead; HF estimates need parity. BGE official CLS
pooling/L2; independently check full reranker pair including specials. No silent truncation.
Initial chunks 512 BGE body target, 768 soft max, ≤64 useful overlap; enriched ≤1024 incl specials;
reranker validated 768/1280 pair cap. Split structural units, repeat original table headers,
shorten context or re-chunk; never cut original tail. Keep warnings/procedures coherent.
Contextualize coherent whole parent within measured budget, stable prefix/varying chunk suffix;
never corpus-wide prompt or feed previous annotations forward. JSON context/support_block_ids/
needs_review; 50–100 Qwen tokens initially, ~160 cap, tested non-thinking, low temperature.
Parent examples 160k/80k leave template/target/output/vision space. Oversized parent uses coherent
section+original references, mode section_plus_references, not invented whole-document claim.
Validate schema/length/support/ACL/version/identifiers/numbers/negation. This is not semantic
entailment proof; sample/high-risk review required. Bounded retries → rejected annotation +
raw-only retrieval. Most restrictive supporting ACL propagates; private context cannot enrich
public evidence. Final evidence includes original supports, never generated context as source.
Jobs keyed by parent revision, span, policies, model/projector/prompt/params/adapter. Parent
changes invalidate contexts. Atomic per-annotation/batch checkpoints, hashes and exact resume;
unchanged artifacts reused. Cache is temporary, outputs/provenance durable.

## A13–A18: interfaces, embeddings and snapshots

One semantic GeneratorClient for annotation/visual/answer; capabilities explicit; safe results
contain actual usage/timings/fingerprints, missing metrics stay unknown. Gateway is online
default: discover configured route/contract and pin gateway commit; no guessed hosts/IDs,
JSON/stream/vision/cache support or complete OpenAI parity. Parse all text items. Timeouts,
cancel and retries bounded; do not blindly repeat ambiguously completed costly calls.
Direct llama is private trusted OFFLINE opt-in; native /completion cache_prompt/id_slot only
on tested build. No direct online fallback on gateway failure/denial; no exposed model/slot
controls. Compare gateway/direct output and true evaluated prefill tokens/time at 8k/32k/80k/
near-budget, vision/MTP/restart/hybrid correctness. Low latency alone does not prove cache.
Never silently patch working llama runtime. Small multi-chunk optimization requires ablation.
BGE-M3 dense 1024, pinned same model/tokenizer/CLS/L2/text-template across CPU queries and GPU
corpus. Test FP16-vs-FP32 cosine, ranking and Recall@k; otherwise validated FP32 path. Store
normalized FP32 vectors. Entire snapshot rebuilt on space change; equal dimensions insufficient.
No generator hidden-state embeddings. Alternative models/ONNX/INT8 require evaluation/rollback.
Enriched indexing text = trusted headings + accepted context + original; keep raw-only variant.
BM25 independent technical analyzer preserves identifiers/components/flags/paths/versions/negation,
no indiscriminate English stemming on Slovenian. CPU exact dot product; FAISS only if useful.
Snapshot binds dense/BM25/row map/chunks/all hashes/ACL/deletions. Validate IDs/counts/finite
normalized vectors/checksums/space/ACL/smoke. Exclusive writer/temp/fsync/atomic pointer; readers
pin one complete snapshot. Reject corrupt/missing/incompatible/unaudited snapshots. No pickle.

## A19–A26: online relevance, evidence and security

Initial 60 dense+60 lexical → dedup/RRF sum(1/(60+rank)) → 40 reranked → ~6–10 evidence chunks.
Tune from recall/loss at each stage; do not sum raw scores. Private pinned bge-reranker-v2-m3
V100 FP16, CPU FP32 reference, initial batch 4 with 1/2/4/8 sweep; bound length/queue/timeout/
in-flight/cancel. Rerank contextualized passage; scores are not confidence. Online embedder
stays CPU. Readiness distinguishes configured model from loaded/warm worker.
Evidence = authorized original spans and needed supports, minimal trusted metadata, versions,
warnings, units; overlap dedup. Initial 4k–6k evidence/≤12k total input/~1536 output, measured
template and visual reserve; fail explicitly if essential evidence cannot fit.
One normal answer call, user language, exact technical names, version/contradiction/insufficiency
honesty. No routine rewrite; unresolved follow-up allows bounded rewrite/clarification. At most
one extra retrieval with total time/token cap. Citation-ID validity does not prove support.
Authenticated /v1/search, /v1/answer and source/image access; exact schemas ordered before code.
Principal→server-owned corpus/version scope; user filters narrow only. Proposed local auth is
hashed bearer-to-scope mapping from protected operator config, no public enrollment or permissive
default. Gateway identity never replaces RAG-user ACL. Admin jobs/activation private CLI only.
V1 ACL partition indexes or proved filtering before scoring; no unauthorized text reaches
reranker/generator/expansion/cache/diagnostics/source endpoints. Recheck current ACL when serving
sources and images; rollback cannot resurrect access. Cache scope/policy+question+model+snapshot.
Sources/queries are hostile data: no tool/shell/network authority, no prompt secrets, approved
roots/domains, bounded extraction/image decode, no traversal/SSRF/pickle. Model URLs/paths never
authorize source access. Delimiters are not isolation. Escape at display boundaries.
Corpus retention is explicit. Routine prompt/query/answer logging off; optional diagnostic full
text access-controlled/time-limited. Redact secrets/content/private paths; log safe IDs, stages,
fingerprints, timing, queue/usage availability/failure/degradation. No unauthorized existence leak.

## A27–A31: modes, capacity, vision

GPU ownership keyed physical host/device with owner incarnation, durable transition journal and
bounded queue/drain. online_rag_v100 → drain → offline_context_long → offline_embed_gpu → build/
validate/activate → restore/health. No unknown process kill, forced lock deletion or incompatible
restart. Checkpoint survives failure; failed restore remains visible/not-ready. Separate hosts
own separate locks and verify transferred artifacts.
Readiness needs safe profile ownership, actual Qwen allocation/projector/route, warm reranker/
peak margin, CPU encoder+snapshot fingerprint, ACL/citation smoke. Bound concurrency/cancel/CPU
threads; test overlapping requests, OOM/deadlock/queue wait/restart. Explicit configured lexical-
only/RRF-only modes labeled; no hidden direct fallback or infinite OOM restart.
Benchmark actual Q6/vision/KV/MTP/runtime at 32k and batch 1/2/4/8, maximum permitted lengths and
concurrency; record startup/warm/peak GPU+allocator/RSS and TTFT/decode/stage p50/p95/max/queue.
~2 GiB spare at observed peak is initial target, not result. Fallback order: smaller validated
batches/pairs; 24k/16k; slots/buffers; evaluated Q4; measured CPU/separate GPU. Optional 48k/64k
needs benefit/margin. Benchmark actual CPU query and reranker 10/20/40/80, multiple lengths.
Vision is targeted, after audited rasterizer, extracting page/crop once with literal text/units/
labels/unreadable markers and explicit uncertainty; preserve original images. Visual answer
retrieves textual representation then authorized bounded originals via tested gateway vision.
Count image budget in actual 32k profile; no image-vector capability claim. Text core can have
separate readiness; full visual scope stays unproven until licensing/capability/quality proof.

## A32–A40: evaluation, operations and authority

Human question set → representative few hundred, held-out untouched, synthetic supplemental;
gold spans/facts/disallowed claims/language/version/ACL/answerability; private data out of Git.
Ablate raw BM25/dense/hybrid, contextual hybrid, reranker, Q4/Q6, alternate embedder, vision.
Measure Recall@20/60/multi-source/MRR/nDCG/candidate loss/answer+citation support/identifiers/
abstention/languages/latency. Proposed ≥95% held-out single-source Recall@20; zero observed leaks,
invalid citations/truncation, meaningful enrichment/rerank benefit, no material optimization
regression. Declare thresholds before selection; humans inspect errors and sampled contexts.
Updates/deletes invalidate dependent artifacts and prevent revoked access through snapshots or
rollback. Proposed tombstones/reversible retention; no irreversible source purge without authority.
Prove crash/concurrent-reader/checksum/backup/restore/delete behavior with disposable data.
Profiles explicitly configure secret references, route/GPU/model/precision/budgets/scopes/roots/
degradation; no invented deployment values. Desired context is supervisor expectation. Proposed
CLI doctor/ingest/chunk/contextualize/build-index/evaluate/activate/serve and mode controls become
documented commands only after implemented. Private examples/runbooks cannot modify real services.
Early A0 inventory then A1 GATEWAY/DIRECT/V100-MEM/RERANK/EMBED qualification; ONLINE/OPS after
their code exists; LICENSE throughout. Missing access = BLOCKED/NOT RUN, not pass. Synthetic
tests need no keys/GPU/downloads. Focused evidence normally; phase/release suites when justified.
ICA evaluates full scope at exact merged revision, not queue completion; independent review and
applicable human DHA/release gates remain. Strategy owns architecture/orders/review/delegated
merge; coding never merges, chooses roadmap or authors D1. Every order has H/A/E/I/C provenance.
Protect other repos/services/GPUs/credentials/corpora; no live inference, downloads, service change,
network exposure, destructive data, license exception, tag/deploy without scoped authority.
Read-only contracts and disposable local tests are allowed. Preserve human agent model/profile.
