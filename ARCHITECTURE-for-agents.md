# Executor architecture — revision 2.0

Source: `ARCHITECTURE.md`; SHA-256: `4b41905396a3838269fd6cf372614cd23cb2c3b6a37be09f29ed752803c0983a`.
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
Principal→server-owned corpus/version scope; user filters narrow only. Local auth is
hashed high-entropy bearer-to-scope mapping from protected operator config, no public enrollment or permissive
default. Gateway identity never replaces RAG-user ACL. Admin jobs/activation private CLI only.
V1 uses access-partitioned indexes before scoring; no unauthorized text reaches
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


## Concrete implementation contracts from full architecture revision 2.0

V2-01 (full §§4–6,19–20; A02/A03/A20/A28/A35): API/CLI are thin adapters over shared
application services, typed domain contracts and filesystem/model/supervisor interfaces.
Use FastAPI/Pydantic and HTTPX adapters, official Sentence Transformers/Transformers model
configuration, model-specific tokenizer assets, NumPy/bm25s, pdfminer.six and optionally
license-audited pypdfium2/PDFium. Pin exact compatible versions; package import/config loading
must not fetch models, execute unpinned remote model code, infer or allocate CUDA.
Initially one API process owns resident CPU encoding/indexes; a separate private GPU worker
owns reranking; offline preparation is explicit. API corpus mounts are read-only. Default
worker transport is permission-restricted Unix-domain HTTP; separate-host transport requires
explicit authentication/encryption and qualification. Start with one admitted answer pipeline;
CPU/BLAS threads, per-principal/global queues and GPU work are bounded. Serving does not seize
GPU ownership or replace existing Qwen supervision. Host/GPU IDs and exact service handles
are configured; cooperative locks do not isolate arbitrary external CUDA users.

V2-02 (full §§7–8; A05/A07/A12/A16): distinguish logical document, original blob hash,
metadata-sensitive document revision, blocks, chunks, separate annotations, vectors and
snapshots. Spans are half-open Unicode code-point offsets into unmodified extracted block
text; reconstruct exactly and mark inserted separators. Never conflate offsets with bytes,
PDF coordinates or tokenizer positions. Duplicate bytes retain distinct rights/source identity.
Fingerprint canonical versioned serialization, not Python hash(). Encoder definition
(model/tokenizer/pooling/normalization/query policy) is distinct from representation and
execution precision/device fingerprints. A qualified CPU/GPU pairing is recorded explicitly.

V2-03 (full §§8,12,21; A12/A18/A34): publish a validated/flushed atomic output before marking
its job complete. Reconcile stale job records from exact valid artifacts; COMPLETE without
valid output is an error. A timed-out submitted model call can be UNKNOWN_COMPLETION; preserve
attempt/request identity and require bounded deliberate retry, no exactly-once/cost claim.
Snapshot core manifest hashes avoid self-reference and bind schema, source/partition membership,
representation/model/analyzer/precision qualification and every file/row mapping. Build on one
qualified filesystem; validate with a fresh loader; publish immutable directory; under publisher
lock compare expected pointer generation then flush/replace current.json. Readers pin one
snapshot through the request. Keep pinned/retained references out of GC. Current authorization
is separate and is never rolled back with data. Cross-host transfer stages and validates locally;
no assumed NFS/SMB or multi-host writer equivalence.

V2-04 (full §§10,13,22; A11/A23/A24/A25): v1 source ACL is uniform per document revision and
its blocks/pages. Mixed-visibility originals need explicit approved logical units; never expose
the unsplit original through a narrower unit. All required labels must be held by the principal;
empty labels mean public source classification, not anonymous API access. Context parent view
must be compatible with the target before generation, regardless of offline worker filesystem
privilege. Reject cross-boundary supports; use raw-only chunk on rejected context. Most restrictive
support permissions can never widen. Do not trust declared support IDs as the sole leak boundary.
Atomic current policy epoch controls principal revocation and scopes. A source withdrawal/ACL
tightening blocks its affected snapshot partition before rebuild; selected blocked scope returns
explicit unavailable, not stale/broader results. Recheck current permission before downstream
model dispatch and final answer/source/image delivery. Previously authorized delivered data
cannot be recalled. Cache identity includes principal/effective scope/policy epoch/snapshot/model.

V2-05 (full §§13,16; A23/A24): generate application bearers with at least 256 bits of entropy;
store SHA-256 verifiers in protected operator configuration, compare in constant time, deliver
raw value once. Explicit operations search/answer/sources:read plus corpus/version/label scope;
answer scope must include corresponding citation-source read. Gateway credentials are distinct.
Remote use needs operator TLS; private listener and no permissive CORS default. Readers cannot
set trusted labels, paths, model routes, system prompts or process commands. Private CLI manages
policy/jobs/publication; no public indexing or GPU-management API.

V2-06 (full §§14–17; A14/A20/A21/A22/A23/A28): candidate scoring uses authorized partitions.
Reserve a configured query budget during reranker-passage qualification, then validate actual
complete pairs; reject overlong questions/index-policy mismatches, never silently trim evidence.
Worker request has server request/pair IDs, expected fingerprint and deadline; no caller-selected
device/model path. Require exactly one finite score for each submitted ID. Missing-stage scores
and usage are absent/null with reason, never invented zero. Explicit degradation starts disabled
unless configured/qualified. Gateway failure cannot select direct online inference.
Public routes: /healthz, /readyz, POST /v1/search, POST /v1/answer, authenticated
/v1/sources/{revision}, /v1/sources/{revision}/spans/{span_id}, /v1/images/{image_id}.
Canonical answer is validated final JSON with snapshot, outcome, source registry and bounded
metrics. Optional public SSE sends status then one validated result/error; no blind upstream
event or unchecked token/citation relay. Upstream streaming capability is separate. EOF without
terminal result is failure. Measure upstream TTFT separately from user-visible final-answer time.
API errors distinguish auth/scope, invalid/oversize input, queue overload, unavailable scope/model,
downstream failure and deadline; never leak private source existence or raw provider bodies.

V2-07 (full §§19–25; A27/A28/A29/A35/A36/A37/A39): startup/qualification smokes have explicit
scope/budgets. Routine readiness does not generate expensive inference per poll; it checks live
ownership/profile/compatibility and applicable qualification. Changed configuration/incarnation
requires relevant recheck. Cancelling a GPU batch may discard its result only after a kernel
returns; release capacity when actually available, without cancelling unrelated work. Restore
prior known-good profile even if new index build failed. Full real qualification, source quality,
license evidence, ICA and human deployment gates remain separate from mocked/scaffold CI.
Full §16 supplies detailed API shapes and §§7–8/12 supply data contracts: an implementation order
must include the needed bounded excerpts if this projection alone does not settle a detail.

V2-08 (full §§7/13; A07/A08/A24): persist annotation input/output token counts with source/availability. Cache query identity preserves case, punctuation and versions; exact validated question text is the baseline.
