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

### 2026-11-10, order 003-j (credential header domain and output preflight docs)

- U01/U05 unchanged in kind, corrected in the credential-value
  boundary: the probe's admitted credential domain is now exactly
  what the locked HTTPX 0.28.1 string-header serializer accepts
  (the transport passes the `Authorization` header as a Python str
  encoded as ASCII with no encoding override, i.e. code points
  0x20-0x7E). The 003-i guard's abstract Latin-1 (RFC 7230) allowance
  was wrong for this transport: 0x80-0xFF values (e.g. U+00E9)
  decoded fine from valid UTF-8 file/env bytes yet raised a raw
  `UnicodeEncodeError` at the real transport. They are now refused
  pre-dispatch with the fixed typed `CREDENTIAL_INVALID` /
  `value_not_ascii` outcome (exit 2, zero HTTP, no key or path echo),
  replacing the 003-i `value_not_latin1` reason; outside-Latin-1
  values keep the same fixed outcome. This is wire-path correctness
  at the pinned dependency, not live compatibility proof: U01/U05
  stay OPEN for real qualification, and no live target/model/GPU/
  corpus work was performed (order 003-j live authorization: NONE).
- Scope fidelity corrected in current docs (no historical report
  edits): objective 003 software acceptance is the adapters/probe
  tooling qualified by synthetic owned-loopback HTTP (order 003-a
  Runtime: live authorization NONE); live-target evidence is NOT a
  003 closure prerequisite but belongs to the separate 004/019/
  full-MVP qualification gates, which remain OPEN and NOT RUN. The
  8192-byte credential-file size cap (bounded lookahead), the real
  probe module path and the post-work (not necessarily
  post-dispatch) export stage are documented as actually
  implemented. The certifi (MPL-2.0) policy gate remains an open
  human question.

### 2026-11-10, order 004-a (trial runner and gateway/direct composition)

- U02/U03-U5 unchanged in kind; the 004-a slice (finite qualification
  trial runner, strict trial spec/sample/result contracts, actual
  gateway/direct repeated-parent composition, deterministic synthetic
  MOCK route, machine-readable section 23.2 gate projection) is
  executable synthetic-only software: U01/U02 stay OPEN — the
  runner's declared identities are verified pre-dispatch but the
  deployed runtime/GGUF/tokenizer identities remain unverified/
  unavailable, and target provenance of any configured destination
  stays `unverified` (only the explicit `--synthetic` owned fixture is
  classified `synthetic-owned-fixture` / MOCK).
- U05 unchanged: no live prefix-reuse, cache-hit or speedup
  observation exists; the trial records reported cache counters as
  raw facts only (contradictory cache/input accounting cannot become
  positive evidence), sends no cache-key/slot control (no assumed
  slot reuse), and keeps physical cold/warm state unknown without
  cache reset/isolation evidence.
- U03/U04/U08 unchanged: no resource telemetry, parity analysis or
  latency promise in this slice; nearest-rank quantiles over caller-
  wall terminal samples are instrumentation, not a product p95
  objective. 004-b (strategic activation required) adds resource
  telemetry, parity analysis and full named gate composition.
- Operational: the 004-a ordered replacement of
  `oap/prompts/coding-startup.txt` with the `/goal`-first bounded-goal
  prompt (SHA-256 6d2323bb832e5f78e4cd86d6951c04c0b3975dc80730c473fc7834820965a98e,
  manifest measurement updated) is NOT operationally validated by
  file hash alone; U10 stays OPEN — strategy qualifies the new
  startup during the same-objective 004-b fresh control handoff,
  before final 004 acceptance. No self-triggering.
- No live target/model/GPU/corpus work was performed (order 004-a
  live authorization: NONE); the certifi (MPL-2.0) policy gate
  remains an open human question (LICENSE-01).
### 2026-11-10, order 004-b (evidence contracts and input boundaries)

- U01-U09 unchanged in kind: the 004-b slice completes the evidence
  contracts and input boundaries of the verified 004-a head (strict
  bounded spec/sample/result DTOs used at the construction/analysis/
  serialization boundaries, typed bounded spec file input refusals,
  available-stage summaries) and is executable synthetic-only
  software. U01/U02 stay OPEN — declared identities are verified
  pre-dispatch, but the deployed runtime/GGUF/tokenizer identities
  remain unverified/unavailable and target provenance of any
  configured destination stays `unverified`.
- U05 unchanged: no live prefix-reuse, cache-hit or speedup
  observation exists; reported cache/input counters stay raw facts
  with their invalidity labels and cannot become positive evidence.
- U03/U04/U08 unchanged: no resource telemetry, parity analysis or
  latency promise in this slice; the available-stage summaries
  (native prefill/decode/model-total included) are instrumentation
  over reported values only — gateway prefill/TTFT remain
  unavailable (n=0, all-null), not zero. Resource telemetry,
  vector/rank parity and full named gate composition remain required
  in later proof-sized 004 continuations.
- Operational: the 004-b fresh-handoff /goal-first startup
  qualification is RECORDED FAILED (upstream payload refusal before
  any implementation; the stalled goal was cleared; the sole control
  OK was consumed and was never replayed). The previously qualified
  ordinary startup was restored, and the bounded native goal
  sequence is set by strategy after that ordinary startup. U10 stays
  OPEN — no operational validation is claimed from file hash alone.
- No live target/model/GPU/corpus work was performed (order 004-b
  live authorization: NONE); the certifi (MPL-2.0) policy gate
  remains an open human question (LICENSE-01).
### 2026-11-10, order 004-c (evidence consistency and metric completeness)

- U01-U09 unchanged in kind: the 004-c slice closes the
  independently reproduced cross-field evidence-consistency, metric-
  completeness, decoded-Unicode and serializer/spent-ledger gaps on
  the verified 004-b head (actual-ledger-driven analysis
  recomputation; envelope/declared/sample backend and fingerprint
  bindings; provenance pairs; declared-budget reservation and floor
  even share over the declared sample count; pure cache/input
  consistency derivation; quartile-complete stage metrics; unpaired-
  surrogate refusal at spec admission; canonical full strict result
  contract at CLI serialization with the actual valid spent ledger
  preserved on post-work rejection) and is executable synthetic-only
  software. U01/U02 stay OPEN — the new bindings prove INTERNAL
  consistency of the evidence document only: declared identities are
  still verified pre-dispatch, but the deployed runtime/GGUF/tokenizer
  identities remain unverified/unavailable, a fingerprint does not
  prove deployed hardware/model identity, and consistent imported
  metadata is still not trusted local execution or qualification
  evidence.
- U05 unchanged in kind, strengthened in bound: reported
  cache/input counters stay raw facts; the consistency LABEL is now
  bound to the shared pure derivation from the actually recorded raw
  usage (unreported cache uncounted, known cache with unknown input
  uncheckable, cache > input contradictory — a known 0 is a fact).
  No positive cache/latency evidence follows from any of this.
- U03/U04/U08 unchanged: no resource telemetry, parity analysis or
  latency promise in this slice; the quartile-complete stage summaries
  are instrumentation over reported values only — gateway
  prefill/TTFT remain unavailable (n=0, all-null), not zero. Resource
  telemetry, vector/rank parity and full named gate composition
  remain required in later proof-sized 004 continuations.
- Operational: the 004-a /goal-first startup qualification remains
  RECORDED FAILED history (never relabeled passed); strategy restored
  the exact previously qualified 582-byte ordinary startup prompt
  (committed byte-unchanged with this round, manifest entry
  preserved) and the root-authored startup docs record the actual
  supported two-step sequence (ordinary startup first, then one
  bounded native goal) and its bounds. Real restored
  wrapper/role/order/post-start-goal qualification is performed by
  strategy on this actual handoff, never inferred from file hash;
  U10 stays OPEN.
- No live target/model/GPU/corpus work was performed (order 004-c
  live authorization: NONE); the certifi (MPL-2.0) policy gate
  remains an open human question (LICENSE-01).

### 2026-11-10, order 004-d (bounded resource telemetry)

- U03/U04/U08 updated in kind: 004-d delivers the bounded read-only
  LOCAL resource telemetry that earlier 004 slices named as pending —
  strict versioned own-process CPU/RSS observations on THIS devhost
  (interval CPU deltas with disclosed utilization normalization, RSS
  current vs ru_maxrss lifetime high-water mark vs observed interval
  sample peak, exact unavailable/error vocabulary, bounded fixed-argv
  nvidia-smi metadata query with pipe-boundary byte limits and owned-
  child timeout/kill), composed with the actual finite repeated-parent
  trials behind the explicit opt-in `--resources`/`resource diagnose`
  commands (plain v1 trial evidence intact inside the versioned
  wrapper; phase/ordinal/ledger facts only; one shared deadline still
  spans sampling; finite cleanup). What it does NOT resolve: no
  remote inference host, worker or model-process measurement exists
  (per-process/CUDA allocated/reserved and worker peaks stay
  unavailable until an owned worker instruments them; supplied worker
  measurements are supplied-unverified); peaks are observed sample
  peaks, not true worst-case peaks; vector/rank parity and full named
  gate composition remain required before whole-004 acceptance; all
  real gates/trials stay NOT_RUN and the ~2 GiB margin is still a
  declared criterion, not a measured default. Local devhost
  measurements never establish the remote target or an assigned
  production device/process/model.
- U05 unchanged: no cache/prefix-reuse claim from telemetry; cache
  counters stay reported raw facts.
- Operational (narrow U10 evidence from the final 004-c review,
  recorded here preserving the failed goal-first history): on the
  actual 004-c handoff, strategy's post-handoff startup sequence —
  the restored qualified ordinary startup FIRST, then ONE bounded
  native goal — was QUALIFIED in the final 004-c review (actual
  wrapper/role/order/tools, Goal ACTIVE, subsequent tools, goal
  marked complete before clear). The 004-a/004-b goal-FIRST startup
  attempts remain RECORDED FAILED history and are never relabeled
  passed; U10 stays OPEN for future handoffs — operational
  qualification is per-handoff work, never inferred from file hash.
- No live target/model/GPU/corpus work was performed (order 004-d
  live authorization: NONE; only the D0 bounded local observational
  allowance applied, with real unique host/device metadata kept out
  of Git/public reports); the certifi (MPL-2.0) policy gate remains
  an open human question (LICENSE-01).

### 2026-11-10, order 004-e (resource lifecycle and budget corrections)

- The final 004-d review independently reproduced five resource
  lifecycle/accounting/contract failures (F01-F05), and the
  published 004-d report's corresponding guarantees were OVERSTATED:
  the pipe-bound byte bound was claimed from a cap+1 count while a
  4096-byte read could actually occur; the aggregate byte/call
  admission was not enforced (an over-limit invalid document could
  be produced); the owned sampler survived an in-process
  KeyboardInterrupt with a surviving caller; late export failures
  mislabelled real spent calls as zero/pre-dispatch for the wrapper
  document; and the resource schemas admitted boolean versions and
  carried no collector/code source binding. The 004-e correction
  closes these on the same PR: shared-deadline startup admission
  with the query allowance clipped and admission rechecked after the
  startup query and before every sample; remaining-allowance pipe
  reads with a bounded one-byte lookahead and ACTUAL observed byte
  counts; aggregate calls/bytes/time enforced before work across the
  whole observer lifetime with a valid honest partial record at
  resource_exhausted (known 0 stays 0, unavailable stays null);
  every-exit-path stop/finite join of the owned observer with the
  original exception preserved; canonical inner-trial-ledger
  late-export accounting (actual known calls with a replay warning,
  explicit unknown when the ledger is missing/invalid, true zero
  only for genuine pre-dispatch refusals); and strict integer-1
  versions plus the bounded collector identity/code-source binding
  (code_version = actual executing package version; Git source
  revision explicitly unavailable; no attestation/signing, no Git
  subprocess on import or default commands). The retained
  independent 004-d witnesses were rerun unchanged and now
  demonstrate the corrected behaviors.
- What this does NOT resolve: the telemetry remains OWN-PROCESS
  devhost evidence only — no remote inference host, worker or
  model-process measurement, no true worst-case peaks, no allocator
  or worker instrumentation; vector/rank parity, the full named
  gate composition and all real gates/trials stay NOT_RUN; the
  ~2 GiB margin remains a declared criterion; LICENSE-01 (certifi
  MPL-2.0) remains an open human question. The immutable 004-d
  report is not rewritten; this correction supersedes its over-
  claimed statements.
### 2026-11-11, order 005-a (canonical source integration)

- U06 narrowed in software only: the integrated admission/store now
  carries explicit per-revision access labels (empty means public
  classification), independent redistribution rights, corpus and
  declared metadata with unknown facts staying unknown, and byte
  deduplication that preserves distinct rights/ACL/corpus identities.
  Representative corpus rights/ACL/language/version evidence and human
  gold questions are still absent; U06 stays OPEN for 005/009 work.
- U07 unchanged: processing approval is operator metadata, never a
  redistribution clearance; the open MIT-0/certifi/native-component
  license questions are unaffected by this slice.
- Documented local trust assumptions (honest boundary, not a fix):
  the private operator store and its parent must be protected from
  untrusted local mutation; the store filesystem must support atomic
  hard links and directory fsync (same-filesystem POSIX scope);
  admitted approvals are not authentication, and the store provides no
  access enforcement, revocation, snapshot isolation, source serving or
  legal verification. Source bytes/metadata cannot choose output paths,
  add locations, invoke tools or cause fetches; display URIs are inert
  data. Extraction/parsing remains 006/016 scope and all real
  qualification stays NOT RUN.

### 2026-11-11, order 005-b (canonical provenance and job records)

- U06 narrowed further in software only: provenance records now bind
  exact original block text, code-point spans, extraction/dependency
  and chunk-policy identities, all-label source-revision
  classifications (empty = public classification), separate
  redistribution rights, same-source derived support with label union
  and cross-boundary rejection, and pure reader grant/restriction
  intersection that fails closed on unknown versions. The supplied
  synthetic extraction records are assertions, not real extraction;
  representative corpus rights/ACL/language/version evidence and human
  gold questions are still absent; U06 stays OPEN for 005/009 work.
- Job/attempt DTOs are data-only: a COMPLETE state with an OutputRef
  is a caller assertion, verified or not, and is not artifact, cache
  or exactly-once execution proof; UNKNOWN_COMPLETION has no automatic
  retry path. Claim ownership, output-first publication, bounded
  retry execution and artifact reconciliation remain 010 scope.
- U07 unchanged: processing approval and operator grants remain
  metadata, never authentication or redistribution clearance; the open
  MIT-0/certifi/native-component license questions are unaffected.
  Real extraction, tokenization, embedding, model, GPU, license and
  corpus qualification all remain NOT RUN.

### 2026-11-11, order 006-a (native extraction first slice)

- U06 narrowed further in software only: real native extraction now
  exists on owned originals — exact literal lines, the bounded
  structural subset with contiguous code-point coverage, and the
  isolated PDF worker with native/visual-needed page semantics — all
  bound to the accepted 005 revision/scope/dependency records and
  Registry. Reading order, layout and geometry remain heuristic; the
  structural subset is not CommonMark; PDF visual content is not
  extracted. Representative corpus quality, real source rights/ACL
  evidence and human gold questions are still absent; U06 stays OPEN
  for 006 continuation/009 work.
- The fixed PDF worker is a trusted isolated development worker, not a
  hostile-PDF security boundary: namespaces plus prlimit bounds are
  real but no seccomp policy is supplied, the cooperative parent
  deadline cannot interrupt blocked filesystem calls, and the
  request nonce correlates but does not authenticate a compromised
  worker. Real isolation hardening stays 016/017 scope.
- U07 unchanged: processing approval and operator grants remain
  metadata, never authentication or redistribution clearance. The
  required PDF development backend is DEV-only (pdfminer.six 20260107,
  charset-normalizer 3.5.2, cryptography 50.0.2, cffi 2.0.0,
  pycparser 3.12, SHA-256 verified): it adds no project dependency,
  lock, allowlist entry, license exception or application graph
  change; cffi MIT-0 and the remaining transitive/native/platform
  model license questions stay release and redistribution gates.
- Structural chunking, native tokenizer sessions, contextualization,
  embedding, snapshot/retrieval, GPU/vision and all physical/model/
  domain/license/ICA qualification remain NOT RUN.

### 2026-11-11, order 006-b (observed native counts and chunks)

- U06 narrowed further in software only: canonical extraction now
  produces observed local native token counts and structural chunks
  bound to the same accepted 005 records: three frozen count receipts
  per chunk bind the exact role inputs (body, heading+body,
  query-pair), observed artifact SHA, backend tokenizers 0.21.4,
  declared revision/preprocessing and input digests, with 512/768/
  1024 budgets, up-to-64-token word-boundary overlap and no
  discarded tail. Observed local tokenization of locally generated
  toy artifacts is not inference preprocessing parity, deployed-model
  equivalence, serving or quality evidence; representative corpus
  counts on real assets and human gold questions are still absent;
  U06 stays OPEN for 006 continuation/009 work.
- Observed usability limit (2026-11-11, independent rerun): the
  accepted session's 1024-call budget refuses the 7876-byte procedure
  source (403 blocks) and the 9269-byte table source (243 blocks) at
  attempted session call 1025 before any chunk/neighbor/receipt
  output, while the 938-byte Unicode source (765 calls) and the
  148-byte manual (150 calls) complete. The refusal is total and
  honest (no partial output); it is a precise observed bound, not a
  capacity proof, and no representative large-document PASS is
  claimed from the tiny bounded fixtures. The commissioned isolated
  PAR-006-NATIVE-EFFICIENCY-A correction is required same-PR 006 work
  before whole-006 acceptance; durable derived bundles/loaders and
  the private installed chunk command remain separate required
  same-PR work.
- U07 unchanged: the required native development backend is a DEV-only
  engine-only capsule (pinned hash-verified tokenizers==0.21.4 with
  --no-deps in a new private 0700 target): it adds no project
  dependency, lock, allowlist entry, license exception or application
  graph change and is not upstream complete-app dependency or license
  clearance; the open MIT-0 and transitive/native/platform/model
  license questions stay release and redistribution gates. Processing
  approval and operator grants remain metadata, never authentication
  or clearance. Real tokenization on deployed assets, model, GPU,
  license and corpus qualification all remain NOT RUN.

### 2026-11-11, order 006-c (durable record integration)

- U06 narrowed further in software only: the accepted native
  efficiency/query correction now runs under the current session hard
  caps (16,384 calls / 32 MB input / 4 MB output), the 15,000 ms
  native default builder deadline (legacy explicit default 5,000 ms,
  maximum 15,000 ms), per-build reuse with duplicate-free
  deterministic session call streams, and policy definition v2
  binding the exact UTF-8 SHA-256 query digest, so the 7876-byte
  procedure source (403 blocks, 81 chunks, 1,305 session calls) and
  the 9269-byte table source (243 blocks, 25 chunks, 1,657 session
  calls) complete at the current caps; the same combined journey
  composes actual structured text records through
  bundle_source_records.validate and bundle_native_records.validate
  into the opaque immutable derived_store container, published
  idempotently and revalidated from a FRESH store in a NEW owned
  process against the actual OriginalStore, both validators, Registry
  chunk/neighbor re-binding, scope, full coverage union, tail, roles
  and deterministic IDs, with corrupted-member and altered-original
  refusals asserted. This is bounded software with honest
  degradation, not a capacity proof: the retained contrary scale
  timings (157,312-byte author run 10.79 s, independent peer 13.81 s,
  root run 15.17 s refused at the 15,000 ms deadline) keep target
  host/model performance 019 OPEN and carry no extra quota authority.
  Observed local tokenization of locally generated fixtures remains
  not inference preprocessing parity, deployed-model equivalence,
  serving or quality evidence; representative corpus counts on real
  assets and human gold questions are still absent; U06 stays OPEN
  for 006 continuation/009 work.
- Component storage composition is not a trusted complete native
  ingestion bundle: the opaque derived store and the two validators
  compose and survive fresh-process revalidation, but the full typed
  ingestion bundle loader, PDF semantic value composition and the
  private installed chunk CLI remain required following 006 work and
  are not claimed by this slice.
- U07 unchanged: the required native development backend remains a
  DEV-only engine-only capsule (pinned hash-verified
  tokenizers==0.21.4 with --no-deps in a new private 0700 target):
  it adds no project dependency, lock, allowlist entry, license
  exception or application graph change and is not upstream
  complete-app dependency or license clearance; the open MIT-0 and
  transitive/native/platform/model license questions stay release
  and redistribution gates. Processing approval and operator grants
  remain metadata, never authentication or clearance. Real
  tokenization on deployed assets, model, GPU, license and corpus
  qualification all remain NOT RUN.

### 2026-11-11, order 006-d (final native operator)

- U06 narrowed further in software only: the corrected concurrent
  derived-store member read now discards a changed attempt and
  re-admits the file at most four fresh times within the existing
  deadline, with only stable bytes reaching the size/hash checks; the
  original root race witness passes unchanged and the closed-FD,
  deadline and corruption witnesses pass, but finite retries are not a
  universal convergence guarantee and a successful read does not attest
  to changes outside its observation interval. The complete typed
  text/PDF semantic bundle (ingestion_bundle.validate) with its durable
  publisher and verified fresh loader (ingestion_store.publish/load),
  the operator profile and the installed private `raggedized chunk` /
  `chunk inspect` routes are implemented and tested with the owned
  actual CPU tokenizer backend and the isolated PDF worker (25
  CLI/service tests; the six combined extraction/count composition
  suites, 49 cases, re-run after integration with no skip or fallback).
  The root reproduced on the merged source a reduced-policy PDF table
  header-relationship loss: a 23-all-text PDF table under a VALID
  reduced policy (target 12 / soft 20 / representation 80 / pair 100 /
  reserve 8) yields eight chunks in which only the first retains the
  actual column header while every source code point, anchor and the
  tail are preserved. This is a header-relationship loss, not dropped
  text; no default-512 failure or procedure-proof claim follows from
  this experiment. The bounded D0 causal repair (architecture 9.2/9.3)
  is isolated in PAR-006-PDF-STRUCTURE-A with no app patch in this
  round, so whole-006 native coverage stays PARTIAL until that reviewed
  fix integrates in a later 006 continuation. The retained contrary
  scale timings (157,312-byte author run 10.79 s, independent peer
  13.81 s, root run 15.17 s refused at the 15,000 ms deadline) keep
  target host/model performance 019 OPEN. Observed local tokenization
  of locally generated fixtures remains not inference preprocessing
  parity, deployed-model equivalence, serving or quality evidence;
  representative corpus counts on real assets and human gold questions
  are still absent; U06 stays OPEN for 006 continuation/009 work.
- The complete semantic bundle is distinct from the opaque store:
  ingestion_store.load alone does not establish native ingestion trust;
  the trusted complete unit is the semantic validator plus durable
  publisher plus verified fresh loader. Source admission approval and
  source validation remain metadata, never current serving
  authentication or rights clearance.
- U07 unchanged: the required native development backend remains a
  DEV-only engine-only capsule (pinned hash-verified
  tokenizers==0.21.4 with --no-deps in a new private 0700 target): it
  adds no project dependency, lock, allowlist entry, license exception
  or application graph change and is not upstream complete-app
  dependency or license clearance; the open MIT-0 and
  transitive/native/platform/model license questions stay release and
  redistribution gates. Real tokenization on deployed assets, model,
  GPU, license and corpus qualification all remain NOT RUN.

### 2026-11-11, order 006-e (bounded native PDF structural correction)

- U06 narrowed further in software only: the integrated conservative
  literal line classifier (pdf-literal-structure-v3) under PDF policy
  definition v4 and the shared kind-bound block fingerprint v2 repairs
  the three root-reproduced structural failures — the default 303-block
  table losing the second header relationship, the fitting-warning body
  (14 observed tokens, soft maximum 20, target 12) separated from its
  procedure, and the closing rule/blank losing the last row's header —
  on the actual post-merge owned fixtures: every row chunk of the
  reduced-policy small/closing tables and of the default-policy 300-row
  table retains the original header fragments with complete
  interval-union coverage, tail, units and anchors preserved, and the
  warning stays with its procedure while the unrelated prefix stays
  separate. The unchanged Root terminator and admission witnesses and
  the independent peer boundary witness pass against the merged source.
  The grammar is a bounded literal heuristic, not a PDF layout or
  fidelity solver: a one-character header offset requires two consistent
  rows, a compatible but incomplete next-table prefix is retained in the
  current table run, and other ambiguous or unsupported material stays
  text; no all-PDF, visual or fidelity claim follows. Records under
  classifier v2 or policy v3 are immutable and incompatible and require
  explicit re-extraction, never a silent upgrade. Whole-006 native
  coverage is software-complete on this branch subject to the
  independent Root review after the 006-e report (code queue and green
  CI alone are not acceptance); representative corpus counts on real
  assets and human gold questions are still absent; U06 stays OPEN for
  006 continuation/009 work.
- U07 unchanged: the classifier adds no dependency, asset, runtime or
  license surface (pure bounded Python over already-extracted lines);
  the required native and PDF development backends remain DEV-only
  pinned hash-verified environments as in 006-d. Real tokenization on
  deployed assets, model, GPU, license and corpus qualification all
  remain NOT RUN.

### 2026-11-11, order 007-a (first 007 slice: vector codec + NumPy pin)

- 007 is PARTIAL after this slice: the exact reviewed normalized FP32 NPY
  subset codec is integrated on the 007 branch (PR not merged), with the
  first exact runtime dependency pin (NumPy 2.5.4 in uv.lock; observed
  dist metadata Requires-Python >=3.12, License-Expression
  "BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0"). No encoder,
  CPU query path, resumable owned GPU batches, snapshot binding or
  qualification contract exists yet; U04 (CPU query latency, CPU/GPU
  embedding parity) and U07 (license/distribution clearance) remain OPEN
  for the following 007 continuations and 018. The codec proves no
  embedding space, row mapping, parity, performance or hardware claim;
  store facts recorded in docs/embedding.md (128-row 524,416-byte member
  roundtrip, 20,000-row 81,920,128-byte frame refused at the 64 MiB
  member cap, 128 job refs 24,492 bytes / 129th refused) are measured
  bounded-software facts from the reviewed batch-capacity interop
  observation, not qualification. The full 018 transitive
  license/SBOM/notice audit remains OPEN; no allowlist exception.
  Real qualification NOT RUN.

### 2026-11-11, order 007-b (source-bound representation batch + published checkpoint space)

- 007 is PARTIAL after this slice: the reviewed source-bound raw retrieval
  representation/batch (one bundle validation, one native session, exact
  receipt admission, 128-item / 1,000,000-codepoint / 4,000,000-byte batch
  preflight) and the published BGE-M3 checkpoint inventory/encoder-space
  software (schema 1/2 byte-verified local admission, fixed
  safetensors/pytorch-state-dict weight names, v1 CLS/1024/normalize/
  identity space binding) are integrated on the 007 branch (PR not
  merged). No deserializer, model execution, CPU query path, resumable
  owned GPU batches, snapshot binding or qualification contract exists;
  U04 and U07 remain OPEN. Pinned layout evidence
  (oap/reviews/007-public-checkpoint-layout.json: upstream revision
  5617a9f6, pytorch_model.bin 2,271,145,830 bytes, LFS SHA b5e0ce34) is
  metadata only: no weight download, no license clearance, no freshness
  claim. Raw .bin byte hashing proves no deserializer safety; a future
  CPU worker requires PyTorch >= 2.10.0 per the current weights-only
  advisory. Schema 1 legacy IDs remain equal; schema 2 differs by
  format+schema. Real qualification NOT RUN.

### 2026-11-11, order 007-c (composed CPU-session software integration)

- 007 is PARTIAL after this slice: the reviewed composed CPU-session
  software is integrated on the 007 branch (PR not merged): owned
  private staging with double admission and pinned-parent cleanup,
  exact native token IDs obtained before any framework construction,
  bounded 1-128 text and native receipt preflight before ONE ordered
  CPU CLS forward, fixed binary32 L2 normalization
  (cls-l2-f64-fp32le-d1024-eps1e-12-tol1e-4-v1) with provenance
  identities kept separate from the encoder/space fingerprint, and a
  fixed CPU CLS backend contract whose runtime checks declare the
  isolated worker pins (CPython 3.12, torch 2.10.0+cpu,
  transformers 4.51.3, tokenizers 0.21.4, safetensors 0.5.3,
  huggingface-hub 0.30.2, numpy 2.2.6) — a declared fixed direct-pin
  list, not a resolved transitive hash lock. The neural framework ran
  only as trusted fakes in tests; no actual model, weight download or
  execution, GPU, network, private corpus or new package installation
  occurred. U04 (CPU query latency, CPU/GPU embedding parity) and U07
  (license/distribution clearance) remain OPEN; a resident real
  encoder, CPU FP32 query path, isolated neural worker process
  bridge, typed durable producer/controller, exclusive GPU/resume and
  hardware qualification all remain NOT RUN.

### 2026-11-12, order 007-d (durable source plans and typed batch journal)

- 007 is PARTIAL after this slice: the reviewed durable source-plan
  substrate is integrated on the 007 branch (PR not merged): a fresh
  original-backed source bundle through ONE native count session into a
  deterministic intended CPU/FP32 embedding batch plan (exact
  dependency/row fingerprints, `embedding-source-scope-v1` scope
  binding), the typed validated embedding batch store (canonical 128-row
  declaration plus NPY, fresh read-back publication, forged non-Store
  refusal), per-job ownership leases (exclusive flock, fork/interrupt
  descriptor cleanup) and the owned atomic job journal (fresh-read
  compare-and-set, 64 events / 16 unique attempts, COMPLETE only on a
  freshly validated full-plan typed output; old/new state honesty after
  replace failure). CPU/FP32 in the plan is intended, not observed; no
  encoder producer/controller/retry, CPU query, GPU or actual model
  execution. A historical verified label is not fresh availability and
  unsigned private history is not rollback-proof. U04 (CPU query
  latency, CPU/GPU embedding parity) and U07 (license/distribution
  clearance) remain OPEN; real qualification NOT RUN.

### 2026-11-12, order 007-e (CPU reference integration)

- 007 is PARTIAL after this slice: the reviewed CPU reference path is
  integrated on the 007 branch (PR not merged): the pre-model schema-2
  `isolated-cpu-embedding-execution-v2` execution contract predicted
  before any model starts (the actual handshake derives the same
  canonical bytes; execution fingerprints change from v1 while legacy
  space/definition/intended-CPU-FP32 identities stay distinct), the
  journal job claim before model startup, observed-record/fingerprint
  comparison before any source text is forwarded, the one-batch producer
  (explicit trusted current-authorization provider with no default
  permissive provider — an extension point, not an implemented
  principal/policy store or rights attestation — one attempt, fresh
  epoch rechecks at the named boundaries, COMPLETE only after actual
  typed publication plus fresh load, verified zero-model-start reuse,
  non-PENDING/non-COMPLETE refusal, no retry/steal/repair/exactly-once),
  the resident CPU worker under the actual bounded OS isolation
  protocol with finite shutdown and retained child ownership, the
  corrected native lifecycle (pre-owned native startup,
  interrupt/close-ownership fixes) and the portable synthetic
  six-real/22-metadata CPU test fixture provisioned in the product CI
  job (synthetic fixture, not an installed real ML runtime; helper
  output never sourced). The actual BGE model has NOT been run: all
  neural behavior in the suites is trusted fakes, and the separately
  scoped old-SHA random one-layer toy evidence is a bounded toy
  observation, not a benchmark or a new neural permit. The legacy
  optional CPU profile (Torch 2.10.0+cpu / Transformers 4.51.3) is NOT
  security qualified: oap/reviews/007-legacy-cpu-profile-security-
  observation.json records current high/medium advisory findings;
  advisory triage, current route reachability and a patched CPU/Volta
  profile refresh are separate pending work — no silent pin change, no
  vulnerability-absence claim, no PoC, no legal/security exception.
  Publication failure can leave an immutable orphan; an ambiguous
  journal COMPLETE may already be committed and is never overwritten
  with a failure. U04 (CPU query latency, CPU/GPU embedding parity)
  and U07 (license/distribution clearance) remain OPEN; the required
  exclusive GPU FP16 corpus encoding path is still unimplemented; real
  qualification NOT RUN.

### 2026-11-12, order 007-f (cleanup/ownership composition and cooperative device lease)

- 007 is PARTIAL after this slice: the two exact root-reviewed
  cleanup/ownership composition candidates and the cooperative
  per-device kernel lease are integrated on the 007 branch (PR not
  merged): finite owned-descriptor close attempts across failures with
  original non-Exception interruptions preserved (a new cleanup interrupt
  outranks an ordinary error), no blind re-close of a reused descriptor
  number (including a same-inode open description), sticky UNKNOWN
  cleanup recorded as a retained `cleanup_owner` that reaches the
  sanitized journal and the producer error even before the claim returns
  (no automatic reclaim, no false clean idempotence), the producer's
  actual pending native/model resource and journal lease held until
  drain, the isolated context-exit under the same interrupt priority,
  and the `gpu-device-lease-v1` key binding ONLY the versioned host +
  physical UUID under the actual trusted common local root (different
  jobs contend on the same key; forked children cannot use the parent's
  lease; pending uncertainty refuses same-key reacquisition in this
  process). The cooperative key does NOT prove physical exclusivity,
  does not grant runtime authority and does not exclude noncooperating
  GPU users; these finite fixes do not guarantee kernel reaping, restart
  recovery or full ICA; a caller must independently verify the real
  assigned device, occupancy and current rights and drain future workers
  before release. The original peerB CHANGES_REQUIRED finding
  (oap/reviews/007-f-peer-producer-b-report.json) with the Root local
  remediation records is immutable provenance, not a completed new ICA
  or human adjudication. The imported seventeen source/test/API files are
  the immutable reviewed bytes (oap/reviews/007-f-components.json): the
  selected source hashes and complete execution fingerprints changed
  naturally, while the predicted/observed handshake, source-job
  matching, semantic, native 0.21.4 and legacy CPU intent identities
  are preserved with no hardcoded old value. The legacy optional CPU
  profile (Torch 2.10.0+cpu / Transformers 4.51.3) remains UNQUALIFIED
  and unchanged: the committed Root observation
  (oap/reviews/007-legacy-fixed-route-static-observation.json) records
  the GitHub TorchScript advisory (GHSA-rrmf-rvhw-rf47) as LOW and the
  Transformers advisory list as four HIGH, six MEDIUM and one LOW — all
  with UNPROVEN transitive reachability and NOT_EXPLICITLY_INVOKED direct
  fixed routes on the installed pins; this finite static observation is
  not package-wide safety and not a clearance; advisory triage and a
  patched profile refresh remain separate pending work — no
  vulnerability-absence or license claim. The actual BGE model has NOT
  been run; all neural behavior in the suites remains trusted fakes.
  U04 (CPU query latency, CPU/GPU embedding parity) and U07
  (license/distribution clearance) remain OPEN; the required exclusive
  GPU FP16 corpus encoding path is still unimplemented; real
  qualification NOT RUN.

### 2026-11-12, order 007-g (profile source integration: CPUv2 selection + corrected GPU raw backend)

- 007 is PARTIAL after this slice: the TWO exact root-reviewed
  candidates are selectively integrated by byte-identical file
  transfer (twenty-five indexed files, oap/reviews/007-g-components.
  json, 278,431 bytes; 23 byte-exact blobs, the two profile READMEs
  preserving the exact candidate prefix plus a precise current-
  selection note; no branch ancestry, no source adaptation). The CPU
  source now selects the cpu-v2 lock (Torch 2.14.0+cpu / Transformers
  5.22.2 / framework tokenizers 0.23.1, safetensors 0.8.0,
  huggingface-hub 1.31.0, NumPy 2.5.4; 38 locked metadata
  distributions) with the BEFORE-content child handshake and
  source-fingerprint semantics preserved and complete source/
  execution/job IDs changed naturally; a legacy pre-cutover COMPLETE
  with the old profile/code/bridge hashes is refused reuse. The legacy
  CPU profile (Torch 2.10.0+cpu / Transformers 4.51.3) remains
  UNQUALIFIED and unchanged, its helper/fixture and the native 0.21.4
  capsule intact. The required CI step provisions the portable
  synthetic CPUv2 fixture (six exact wheels plus 32 explicitly
  DATA-ONLY metadata distributions, no importable fake ML packages)
  after the existing CPU fixture provisioning and before lint on both
  matrix legs, with literal GITHUB_ENV bindings and the legacy fixture
  variables retained. The corrected raw GPU backend source (assigned
  exact synthetic device UUID byte guard before local FP16 loading,
  actual child/process-owned DeviceLease assertion, bounded immutable
  native-ID input, no autocast, finite ordered CPU FP32 raw CLS 1024
  output, sticky close/owner retention, original non-Exception
  identity across hostile backend_owner attachment) is integrated
  finite and inert under trusted in-memory fakes and the cooperative
  kernel lease; before from_pretrained returns there may be no captured
  model owner (documented honest unknown boundary), with no
  parent-owned serialized lease and no caller-lease release. This is
  bounded source integration, not model/runtime qualification: the
  archived prior OWNED random CPU toy execution remains historical toy
  evidence; the actual BGE model, checkpoint and hardware remain
  UNRUN/UNQUALIFIED; the actual full-38 CPUv2 installation remains a
  separate PARTIAL (latest diagnostic: uv allocation abort under the
  fixed 2 GiB address space; no full CLI acceptance or neural import);
  future owned GPU worker/controller and physical drain remain absent.
  The original advisory findings and unproven transitive/security/
  license status are preserved; newer pins alone are no clearance. U04
  (CPU query latency, CPU/GPU embedding parity) and U07 (license/
  distribution clearance) remain OPEN; the required exclusive GPU FP16
  corpus encoding path execution is still unimplemented; real
  qualification NOT RUN.

### 2026-11-12, order 007-h (runtime setup integration: CPUv2 installer tooling + GPU synthetic fixture + current evidence docs)

- 007 is PARTIAL after this slice: the SIX root-reviewed
  setup/test/API files are selectively integrated (no branch
  ancestry, no source adaptation): the original byte-identical
  transfer (70,906 bytes; oap/reviews/007-h-components.json) is
  historical, and per Root CI-portability amendment 007-h-1
  (oap/reviews/007-h-ci-portability-addendum-1.md) ONLY the
  installer unit file now differs from the frozen candidate
  (23,095 → 28,320 bytes; current SHA-256
  6038a3b1766f52911f9d15b800d6fe515630b32f03cec52bca39b30ed56d1482;
  self-contained controlled-fake preflight in its own tmp_path),
  while the other five files, including the production helper
  (SHA-256 226a527650083ec3324fcb783354ca47eb8b30884f0db0d3e4df6c044e6ede0c),
  remain byte-exact (current six-file sum 76,131 bytes;
  oap/reviews/007-h-components-after-portability.json). The fixed
  CPUv2 runtime installer
  (tests/support/prepare_cpu_runtime_v2.py) is developer
  qualification tooling, NOT an implicit deployment/runtime action:
  it enforces the fixed 38-wheel pinned official graph, status/
  origin/length/hash checks with the missing-MIME exception for the
  exact fixed Torch wheel only, offline no-index/no-deps
  hash-required binary-only install, metadata and dependency
  verification without framework import, finite owned cleanup with
  diagnostic interrupt priority, atomic receipts and
  MALLOC_ARENA_MAX=1 (a documented glibc arena limit that does not
  increase any cap). It is never run in CI (CI runs only its
  unit/guard tests); its fixed runtime/binary host qualification
  does not prove generic deployment portability. The required GPU
  fixture CI step (six exact hash-pinned wheels plus 51 explicit
  DATA-ONLY metadata distributions from the fixed GPU lock; no
  importable fake ML packages, real Torch/Transformers/NumPy,
  model, CUDA or neural call) is provisioned after the current
  CPUv2 fixture and before lint on both product legs, with
  set -o pipefail, a new direct /tmp target refusal guard, teed
  setup log and literal GITHUB_ENV bindings (never source/eval);
  expected five jobs, 78 steps, all required current jobs/steps
  must succeed — missing/skipped/pending is not green. Canonical G
  source, profiles, locks, requirements, the old helper, native
  0.21.4 and the existing fixtures remain intact; no candidate
  ancestry or source adaptation.
- Current setup status is corrected against the 007-g-era docs:
  the claim "full 38 still PARTIAL / no framework import" is
  superseded as current status by separately scoped Root actual
  development evidence (oap/reviews/007-h-cpu-runtime-evidence.
  json; public software evidence only, not release qualification):
  a frozen full-CLI acquisition completed in 22.254 s with
  252554535 payload bytes over 38 hash-verified wheels, 38
  metadata and dependency graph, all four commands exit 0, no
  unresolved owned children and sampled disk 2085087847 B under 2
  GiB address space / 120 s CPU / 600 s wall (sampling, not quota);
  a separate actual CPU class import (Torch 2.14.0+cpu plus
  Transformers 5.22.2 XLMRobertaModel) succeeded in 14.73 s with
  352816 KiB RSS inside the standalone CPython 3.12 namespace,
  synthetic /dev, no home, offline, under a separate 4 GiB /
  30 s CPU / 120 s wall allowance. Do NOT read a class import as
  loading BGE weights, constructing a model, running a forward
  pass or measuring query latency, parity, hardware, security or
  licenses. Prior partial receipts/reports are HISTORY, not latest
  current setup status; the original unknown full-CLI failure
  cause is not retroactively invented.
- The broad "no actual model execution" is replaced with precise
  scope: the archived prior OWNED random CPU toy was historically
  run (toy evidence); the ACTUAL BGE checkpoint/model has NOT been
  executed or qualified; the current 38-dependency and class-level
  interoperability differs from real BGE forward, and both differ
  from the controlled neural fakes; child/query parallel prototypes
  are not canonical here. Original advisory findings and unproven
  security/parity/real-hardware/rights/license/visual/held-out/ICA
  gates stay open; newer pins are no clearance.
- The Root 38-wheel license inventory (oap/reviews/007-h-license-
  facts.json) is FACTS ONLY: 38 selected wheels, 141 declared
  license files read and hashed (1,231,200 B), 22 SPDX-expression /
  11 legacy-header / 5 classifier-only declarations; tokenizers
  0.23.1 has a notice gap (classifier only, no declared or
  filename-discovered notice text); ambiguous BSD variants and
  observed out-of-allowlist labels (MPL-2.0/ISC/PSF/CNRI/LLVM
  exception/BSL/0BSD/Zlib/CC0 combinations) plus native/model/
  platform provenance still require proper review. This does not
  widen the MIT/BSD/Apache policy, choose dual licensing, admit a
  license exception or clear U07/distribution (architecture
  SECTION 24 / licensing requirement A04, not requirement A24).
  Missing/unapproved license and notice scope remains blocked for
  distribution; no human adjudication is invented (DHA NONE: no
  provisional exception admitted).
- U04 (CPU query latency, CPU/GPU embedding parity) and U07
  (license/distribution clearance) remain OPEN; the required
  exclusive GPU FP16 corpus encoding path execution is still
  unimplemented; real qualification NOT RUN.
### 2026-11-12, order 007-i (resident query + packaged CPU profile lock assets integration)

- 007 is PARTIAL after this slice: the FIFTEEN root-reviewed
  resident-query/CPU-asset files are selectively integrated by
  byte-exact file copy from the two exact report commits
  (query 1bb40cc6, CPU assets d75baa51;
  oap/reviews/007-i-components.json, 170,026 bytes; no branch
  ancestry, no source adaptation): the private resident CPU
  query encoder (bounded raw Unicode/UTF-8 admission: at most
  8192 characters / 32768 strictly encoded bytes, nonblank,
  with no prefix, title, normalization, truncation or padding;
  independent native 0.21.4 tokenizer IDs enforcing the 1024
  limit; one actually owned CPU worker reused across different
  queries with load-once; immutable normalized FP32 result
  plus observed complete execution provenance; content-free
  QueryRefused before exposure; missing/changed identity and
  invalid input refuse), the shared native/CPU/session
  diagnostic-priority fixes (the selected original non-
  Exception interruption is preserved even when cleanup or
  diagnostic annotation fails; a new cleanup interruption
  outranks an ordinary error; exception notes and owner
  attributes are best effort, never resource ownership; the
  actual session retains its pending handles) and the packaged
  CPU profile lock assets (the actual offline wheel bundles
  byte-identical CPU v2 / legacy CPU / GPU uv.lock files under
  _worker_profiles with RECORD/license/entry/source identity;
  installed-layout selection refuses missing/corrupt/symlinked
  or whole-bundle-missing assets even with a matching ambient
  project/lock under bounded dist-info downgrade guards; a
  src-named wheel prefix is detected before admitting the
  fixed source-checkout layout; source-checkout support
  retained; pyproject adds only the three reviewed force-
  include mappings, dependencies and all CPU/GPU/native locks
  unchanged).
- Mock/real distinction: the composed query/isolated/CPU-
  worker tests substitute a trusted in-memory fake framework
  over actual staged artifacts, actual native tokenizer 0.21.4
  and the actual CPU isolation protocol; the wheel test builds
  and installs the actual wheel offline in a private bounded
  prefix. This is finite model-free software progress: the
  actual BGE execution, latency, parity, model memory and
  hardware remain UNRUN/UNQUALIFIED; GPU child/plan/parent
  resources remain parallel and unintegrated; the corrected GPU
  backend source is preserved unchanged; no security/license/
  current-rights/real-CPU-neural/V100/controller/parity/
  visual/held-out/ICA/full-MVP claim is made.
- The H actual 38 setup/class-import facts and the archived
  random CPU toy distinction are preserved (H history); the
  current host full-unit failure cause remains UNRESOLVED as
  observed H history: no causality is invented and no failure
  is hidden; this round's local full unit sweep passed at the
  current head (1466 collected, exit 0) without retroactively
  clearing the unresolved H-era observation.
- U04 (CPU query latency, CPU/GPU embedding parity) and U07
  (license/distribution clearance) remain OPEN; the required
  exclusive GPU FP16 corpus encoding path execution is still
  unimplemented; real qualification NOT RUN. Whole 007
  remains PARTIAL; no main merge or 008.
### 2026-11-12, order 007-j (GPU child/protocol + prepared launch + packaged GPU resource assets integration)

- 007 is PARTIAL after this slice: the FOURTEEN root-reviewed
  GPU child/protocol, prepared-launch and packaged-resource
  files are selectively integrated by byte-exact file copy
  from the single exact source commit 5445c03bcc85a5cea6ad24f26f137e55f5a806cf
  (oap/reviews/007-j-components.json, 136,921 bytes; no branch
  ancestry, no source adaptation; the old nineteen-file J
  draft is inert and was never used): the GPU worker protocol
  (child-owned device lease acquired before backend load,
  fixed closed bounded wire/version/config/startup
  vocabulary, exact token-ID requests and raw FP32 rows,
  content-free refusals, immutable ready bindings, no fake
  serialized PID-bound lease), the worker main entry
  (original non-Exception interruption priority retained
  under foreign/fork/error/interrupt ownership semantics),
  the corrected raw GPU backend (finite and inert under
  trusted fakes), the prepared launch (actual pinned
  Python/package/config/device inputs with retained FDs,
  exact closed copied capsule, fixed argv/clearenv/private
  namespaces, trusted fixed entry, fork-creating-PID check
  before any close/cleanup, bounded startup checked against
  the fixed 2 MiB request/total input; no parent/module code
  execution, no generic process callback) and the packaged
  GPU profile lock assets (bundled unchanged GPU lock first;
  fail-closed missing/corrupt/symlinked/whole-bundle-missing
  refusal under actual installed normal/src-named prefixes
  even with a matching ambient project/lock; bounded
  dist-info guards; the exact private /app/src/pkg layout is
  a data mapping, not authorization; the real offline wheel
  carries the three exact locks plus RECORD/license/entry/
  source identity).
- Mock/real distinction: the 103 focused GPU
  backend/protocol/launch/assets units and the SEPARATE
  installed-resource integration (8), project launch
  namespace (1, real bwrap/unshare child) and offline
  CPU-wheel (1) invocations use fake/null namespaces,
  synthetic /dev bindings and the actual offline wheel — no
  real GPU, driver, Tensor, model or framework import was
  executed, and a prepared capsule is not a running parent or
  GPU exclusivity proof. The actual BGE execution, latency,
  parity, model memory and hardware remain
  UNRUN/UNQUALIFIED; the actual owned GPU parent, the new
  lock and the worker-identity resources remain parallel and
  unintegrated pending their affected reviews; no complete
  native/normalized/durable GPU execution, controller or
  snapshot activation exists; no security/license/
  current-rights/real-GPU-neural/V100/ICA/full-MVP claim is
  made.
- The H actual 38 setup/class-import/license-fact and the
  archived random CPU toy distinction are preserved (H
  history); the H-era host full-unit failure cause remains
  UNRESOLVED as observed history: no causality is invented
  and no failure is hidden.
- U04 (CPU query latency, CPU/GPU embedding parity) and U07
  (license/distribution clearance) remain OPEN; the required
  exclusive GPU FP16 corpus encoding path execution is still
  unimplemented; real qualification NOT RUN. Whole 007
  remains PARTIAL; no main merge or 008.
