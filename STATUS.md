# Project status

## Current state (2026-11-11)

- Active objective: 005, current slice 005-b (canonical provenance
  and job records on the 005 source foundation), open on the 005 PR,
  branch oap/005-artifact-schema-and-source-scopes from main bd8e454;
  first slice 005-a (canonical source integration of the
  independently reviewed local original admission/store plus a thin
  installed `raggedized source import|inspect` route) remains in the
  branch;
  live PR/CI/merge state is queried on GitHub, not asserted
  here. Objective 004 is complete: the explicitly replanned 004
  software scope was root-reviewed and merged to main as PR #6
  (merge commit bd8e454; final review
  oap/reviews/004-f-review.json, terminal resolution
  oap/reviews/004-resolution.json). All fourteen real
  qualification trials remain NOT_RUN; the development merge is
  not qualification.
- Product implementation: IN PROGRESS — foundation (objective 002-a,
  merged), the complete 003 gateway/transport/native/probe slice
  (merged as PR #5) plus the 004-a finite qualification trial runner
  with the 004-b strict bounded trial spec/sample/result evidence
  contracts with the 004-c cross-field consistency bindings and
  quartile-complete stage summaries, bounded safe spec file input with
  decoded-Unicode admission and available-stage summaries, actual
  gateway/direct repeated-parent composition and the machine-readable
  section 23.2 gate projection, plus the 004-d bounded read-only local
  resource telemetry (explicit opt-in `resource diagnose` own-process
  CPU/RSS diagnostic and `qualification run --resources` wrapper with
  the plain v1 trial evidence intact; at most one bounded nvidia-smi
  metadata query; no remote/worker/model-process measurement), open on
  PR #6, see history, with the 004-e corrections of its resource
  lifecycle (shared-deadline startup admission, every-exit-path
  observer stop), honest aggregate byte accounting at the pipe and
  sample boundaries, late-export spent-ledger handling and strict
  versioned collector/code-source binding. Hardware/model
  qualification: NOT RUN. ICA:
  NOT RUN.
- The coding client is active on objective 005 (new 005 PR), not idle.
- Current main is the 004 merge commit bd8e454 (PR #6); the 005
  branch builds from it.
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
  isolated subprocess), regenerated JSON schema and scoped docs. The 003
  probe tooling then remained pending (delivered in 003-h); live
  qualification is out of 003 software scope (003-a Runtime: live
  authorization NONE) and stays with the 004/019/full-MVP gates.
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
- 003-j (current round): credential-value admission aligned to the
  ACTUAL locked HTTPX 0.28.1 string-header serializer: the transport
  passes the `Authorization` header as a Python str whose serializer
  encodes as ASCII with no encoding override, so the admitted domain
  is exactly 0x20-0x7E. The previously missed 0x80-0xFF Latin-1 range
  (e.g. U+00E9, valid UTF-8 file/env bytes decoding to an
  unserializable str) is now refused pre-dispatch for env AND file
  references with the fixed typed `CREDENTIAL_INVALID` /
  `value_not_ascii` outcome (exit 2, zero HTTP, no raw
  `UnicodeEncodeError`, no key or path echo), replacing the 003-i
  `value_not_latin1` reason; ASCII positives, C0/DEL control refusal,
  bounded regular-file/FIFO/UTF-8/size handling and the opaque
  credential-path digest are retained. Unit and installed-CLI
  owned-loopback regressions cover file and env U+00E9 plus an
  outside-Latin-1 value and ASCII positives; the proved 003-i
  output-stage fixes (owned-0400 / invalid-directory pre-dispatch
  refusal; genuinely late post-work export failure with exit 3, full
  safe JSON on stdout, exact spent-attempt accounting and a safe
  post-work stderr stage) and the exception-safe Python 3.12/3.14
  destination probes are preserved. Documentation corrected to the
  actual scope: 003 software acceptance is adapters/probe tooling +
  synthetic HTTP (003-a Runtime: live authorization NONE), with
  live-target evidence a separate 004/019/full-MVP gate; the 8192
  credential-file size cap (bounded lookahead, not an exact read
  claim), the real probe module path and the post-work export stage
  described accurately. Live qualification, caching-effectiveness and
  hardware evidence remain NOT RUN.
- Objective 003 scope fidelity (order 003-a Runtime: live
  authorization NONE — "accept callable adapters/probe tooling and
  synthetic HTTP evidence only"): the 003 software acceptance is the
  adapters and bounded probe tooling qualified by synthetic
  owned-loopback HTTP; live-target evidence is NOT a 003 closure
  prerequisite — it belongs to the separate 004/019/full-MVP
  qualification gates, which remain OPEN and NOT RUN. Objective 003
  was accepted and merged as PR #5 (merge commit 2bc320f,
  2026-11-10); the strategic 003-j review and resolution records were
  committed unchanged with 004-a.
- 004-a (trial runner and gateway/direct composition; open on PR #6,
  branch oap/004-qualification-harness from main 2bc320f): the first
  proof-sized slice of objective 004 under the explicit D0 replan
  (authorized real gateway/GPU/model/corpus inputs remain absent;
  004 establishes usable instrumentation and exact prerequisites;
  actual A1/hardware/quality feasibility remains UNPROVEN, mandatory
  at 019/ICA/MVP). Delivered executable software, not a JSON approval
  wrapper: strict finite trial spec/sample/result contracts
  (slaif_raggedized_helper/qualification/spec.py: bounded, frozen,
  extra-forbid; declared workload/seed fingerprints verified
  pre-dispatch; unimplemented context/pair/batch/precision/seed
  controls refuse with named prerequisites); a finite trial runner
  (qualification/runner.py) that actually invokes the current
  gateway/direct application adapters through the REAL transport with
  ONE absolute trial deadline and ONE shared dispatch admission
  allowance spanning all warmups, repetitions, retries, template and
  model calls (enforced at the real transport dispatch boundary, the
  reused 003 shared-budget seam; native template work consumes the
  allowance; exact sample-start minimums), safe per-trial/per-phase
  observations (fingerprints only, declared-vs-observed identities
  with unavailable physical identities explicit, physical cold/warm
  state unknown, reported-only usage, contradictory cache/input
  accounting as raw facts only); reproducible nearest-rank latency
  analysis (qualification/analysis.py: deterministic pure function,
  terminal samples only, zero-sample nulls, no qualifying pass from
  synthetic/configured-unverified evidence); the deterministic
  explicit synthetic route (--synthetic: owned loopback fixture,
  real adapters, evidence labeled MOCK / synthetic-owned-fixture,
  configured secrets never read; a configured URL is never
  classified synthetic by a boolean); CLI `raggedized
  qualification gates|plan|run` (help/import/plan/gates zero
  model/HTTP/telemetry I/O; run is explicit opt-in; exit codes 0/1/2/3
  with the honest post-work export stage); the machine-readable
  prerequisite projection of every architecture section 23.2 ID
  (qualification/gates.py + docs/benchmarks/qualification-gates.json:
  all real trials NOT_RUN, live target authorization NONE, only text
  repeated-parent runner entrypoints executable in this slice);
  installed-CLI owned-loopback composition tests (gateway + direct,
  budget boundaries, deadline/cancellation, unknown-no-replay,
  preflight zero-dispatch, metric ambiguity, deterministic synthetic
  route, zero-I/O plan/gates) and unit contracts; docs/benchmarks/
  qualification-protocol.md plus README/TESTING (T08)/STATUS/CI/
  UNCERTAINTIES updates. The one ordered operational correction:
  oap/prompts/coding-startup.txt replaced with the exact
  /goal-first bounded-goal bytes (SHA-256
  6d2323bb832e5f78e4cd86d6951c04c0b3975dc80730c473fc7834820965a98e)
  with docs/AGENT-ROLE-SETUP.md, docs/OAP-RUNBOOK.md and the
  governance manifest measurement updated; the new startup is NOT
  operationally validated by file hash alone (strategy qualifies it
  during the same-objective 004-b fresh control handoff). The
  strategic 003-j review/resolution files and the unchanged 004
  order/active are committed with this round. Live target/model/GPU/
  corpus work: NONE; all real qualification gates and LICENSE-01
  remain open (certifi MPL-2.0 exception not granted); 004-b/005+
  selection remains strategy alone.
- 004-b (evidence-contract correction of the verified 004-a head;
  amends the same open PR #6, branch oap/004-qualification-harness):
  the four ordered corrections from the final 004-a review
  (oap/reviews/004-a-review.json committed byte-unchanged, SHA-256
  02ab0d2288191469c5c480b11777d71b509b3963b8110e0f9afeb5f7a6db0611):
  (F01) bounded safe trial-spec file input (qualification/specio.py:
  non-blocking open with fstat of the actually opened descriptor —
  directories/FIFOs/sockets/devices, including a path resolving
  through a symlink to a special file — refused without blocking;
  65536-byte bound; strict UTF-8; typed JSON decoder/integer/depth
  refusals; fixed safe messages with no input or private-path echo;
  no process-global decoder-limit change); (F02) explicit strict
  bounded sample/result evidence contracts (qualification/contracts.
  py: frozen extra=forbid DTOs with strict int/float/bool; envelope
  invariants — requests are the exact leading prefix of the declared
  workload, remaining+attempted == budgets.max_dispatches,
  status/stop_reason consistency, not_run implies zero dispatches —
  and the analysis section must equal the pure recomputation from the
  recorded samples; used at the construction, analysis and
  serialization boundaries, a violating executed document is an
  honest post-work exit-3 evidence_contract_violation, and the spent
  ledger is preserved); (F03) reproducible available-stage
  n/min/p50/p95/max summaries per warmup/measured group
  (caller_wall/prefill/decode/model_total/ttft with known-zero,
  missing and invalid-observation bookkeeping and per-stage
  provenance; gateway prefill/TTFT stay n=0 all-null, unavailable not
  zero); (F04) documentation corrections to the actual implementation
  (14 section 23.2 IDs, sample-start minimums are an admission guard
  only, context measurements refreshed from the final actual files:
  routine governance 42158 bytes, ceiling 50000; exact model tokens
  and client injection remain UNMEASURED). The 004-b fresh-handoff
  /goal-first startup qualification is RECORDED FAILED by strategy
  (upstream payload refusal before any implementation; the stalled
  goal was cleared and the sole control OK was consumed, never
  replayed); the previously qualified ordinary startup is restored
  and the bounded native goal sequence is set by strategy after this
  ordinary startup — it is NOT claimed passed, and U10 stays OPEN.
  All 004-a transport/budget/retry/native-template/UNKNOWN/
  credential/export positives preserved. No live target/model/GPU/
  corpus work (live authorization NONE); all real qualification
  gates and LICENSE-01 remain open; resource telemetry, vector/rank
  parity and full named gate composition remain required in later
  proof-sized 004 continuations; no merge; 004 continuations and 005
  selection remain strategy alone.

- 004-c (evidence-consistency and metric-completeness correction of
  the verified 004-b head; amends the same open PR #6, branch
  oap/004-qualification-harness): the four ordered corrections from
  the final 004-b review (oap/reviews/004-b-review.json committed
  byte-unchanged, SHA-256
  81f1fa1b4e8566bb5b7ab6a18ea0bef66f81f576dbaaa86516e6984b8c2f5fc4):
  (F01) cross-field evidence bindings (qualification/contracts.py:
  the analysis pure-recomputation is driven by the ACTUAL
  transport-boundary call ledger — an analysis call count that
  conflicts with the ledger is refused; the envelope backend equals
  the declared backend; every KNOWN per-sample backend fingerprint
  equals the observed per-trial backend binding, an absent binding
  stays null; the evidence class and target type form the consistent
  provenance pair; the output reservation total/per-sample equal the
  declared budget with the per-sample share the floor even share over
  the DECLARED scheduled sample count; the cache/input consistency
  counts equal the shared pure derivation from the actually recorded
  raw usage — every single-field contradiction refused, the unaltered
  actual owned-HTTP result admitted); (F02) metric completeness
  (n=0 iff all-null quartiles; n>0 requires EVERY quartile present,
  finite, non-negative and ordered min <= p50 <= p95 <= max; partial
  quartile sets refused; the full result validation still
  recomputes the deterministic summaries); (F03) decoded-Unicode
  admission (qualification/spec.py: a workload string that decodes to
  an unpaired surrogate code point is refused at spec admission with
  a fixed safe reason BEFORE fingerprinting or request construction —
  typed exit 2, zero HTTP, no input echo; valid Unicode including
  escaped astral pairs and Slovenian text admitted unchanged; no
  replacement/truncation/global-encoding/fingerprint-version
  change); (F04) serializer/spent-ledger boundary (cli.py: the
  canonical FULL strict result contract — strict shape plus the
  analysis pure-recomputation — is enforced at serialization; a
  post-work rejection is an honest exit 3 with the fixed safe
  structured error carrying the ACTUAL valid spent-attempt ledger on
  stdout, honest ledger availability when the ledger itself cannot
  validate — never assumed zero, never a crash — and the invalid
  record is never exported as a valid result). These checks prove
  INTERNAL consistency only — never that declared metadata is true,
  that a fingerprint proves deployed identity, or that imported JSON
  was executed here. The root-authored startup-governance restoration
  (oap/prompts/coding-startup.txt the exact previously qualified
  582-byte ordinary prompt, docs/AGENT-ROLE-SETUP.md and
  docs/OAP-RUNBOOK.md) is committed byte-unchanged; the 004-a
  /goal-first qualification remains RECORDED FAILED history, never
  relabeled passed; U10 stays OPEN and real restored
  wrapper/role/order/post-start-goal qualification is strategy's,
  performed on this actual handoff, never inferred from hash.
  Documentation (protocol/TESTING/STATUS/UNCERTAINTIES/README) and
  context measurements refreshed to the actual implementation. All
  004-a/004-b transport/budget/retry/native-template/UNKNOWN/
  credential/export/file-input/Unicode/ledger positives preserved.
  No live target/model/GPU/corpus work (live authorization NONE);
  all real qualification gates and LICENSE-01 remain open; resource
  telemetry, vector/rank parity and full named gate composition
  remain required in later proof-sized 004 continuations; no merge;
  004 continuations and 005 selection remain strategy alone.
- 004-e (resource lifecycle and budget correction of the verified
  004-d head; amends the same open PR #6, branch
  oap/004-qualification-harness): the five ordered corrections from
  the final 004-d review (oap/reviews/004-d-review.json committed
  byte-unchanged, SHA-256
  5a8d4dff6a259dc689cf056071091960501ba1ae321a0b3285b611230bf19e10):
  (F01) the startup nvidia-smi metadata query is clipped to the
  remaining trial AND observer duration and admission is rechecked
  after the query and before every sample — an already-passed
  deadline queries nothing and samples nothing, and no late first
  sample is admitted past expiry (the 0.08 s deadline case that
  previously admitted a ~0.276 s late query/sample); (F02) pipe
  reads enforce the remaining declared allowance plus a bounded
  one-byte lookahead and report the ACTUAL observed bytes (a cap-128
  overflow reports the observed 129 instead of requesting 4096 and
  claiming cap+1), and aggregate collection calls/bytes/time are
  enforced before work across the whole observer lifetime —
  bytes_read is actual observed bytes (never the read cap) with the
  cap reserved per admitted sample, so a finite workload terminates
  with a valid honest partial record at resource_exhausted instead
  of an over-limit invalid document; (F03) the runner stops and
  finitely joins the owned observer on EVERY execution exit path,
  including in-process KeyboardInterrupt with a surviving caller
  (no detached sampler, no continued samples, original exception
  preserved); (F04) late --output failures use the canonical inner
  trial ledger (wrapper-aware): after real work the error reports
  the actual known call count with a replay warning, a
  missing/invalid ledger stays an explicit unknown, and only genuine
  pre-dispatch refusals keep the true zero-dispatch claim; (F05)
  resource schema versions refuse booleans and wrong numeric types,
  and the collector record binds the bounded collector identity,
  code source and actual executing package version with the Git
  source revision explicitly unavailable (no attestation/signing, no
  Git subprocess on import or default commands). The published
  004-d report is immutable; its over-claimed pipe bound, aggregate
  admission, cancellation and collector/code metadata statements are
  superseded by this correction. The retained independent 004-d
  witnesses now demonstrate the corrected behaviors; the plain trial
  v1 contract, the 004-a/b/c positives and the D0 bounded allowance
  are preserved. No live target/model/GPU/corpus work (live
  authorization NONE); all real qualification gates, vector/rank
  parity and the full named gate composition, 019/ICA/MVP and
  LICENSE-01 remain open; no merge; 004 continuations and 005
  selection remain strategy alone.
- 005-a (canonical source integration, first 005 slice; new 005 PR,
  branch oap/005-artifact-schema-and-source-scopes from main bd8e454,
  the PR #6 merge): ONE authorized local --no-ff merge of the
  root-reviewed local candidate branch oap/parallel-005-source-cli tip
  32a2b84d099f2641123d2569b01afe533064ac61 (including the
  source-admission-b tip
  0837191198b2b1712445d5ba6ca268d358637866) preserving candidate
  order/report/implementation histories, plus the thin installed
  `raggedized source` prefix delegation to the existing source_cli.main,
  focused installed-CLI source tests and documentation/governance
  reconciliation. Adds source_admission.py (strict versioned manifest,
  descriptor-bounded approved-root reads, digest-named immutable blobs,
  metadata-sensitive immutable revisions, atomic same-filesystem
  publication) and source_cli.py (bounded import/inspect operator tool);
  the installed route proves shared-byte blob dedup with distinct
  rights/ACL/corpus metadata, metadata-revision immutability, verified
  reuse and safe input-free failures on owned disposable fixtures.
  Strategic 005-a round-start bytes committed byte-for-byte unchanged.
  Block/span/chunk, derived-scope and job/attempt records remain REQUIRED
  same-PR continuations before whole-005 acceptance; no 006 activation or
  partial 005 merge; all real qualification, provenance, license and MVP
  gates remain open (NOT RUN).
- 005-b (canonical provenance and job records; same PR 7 branch):
  TWO authorized local --no-ff merges of the root-reviewed candidate
  tips, provenance first (oap/parallel-005-provenance tip
  3f2ec5768cc07c86c2f0ab663a4e4af23ecac406) then jobs
  (oap/parallel-005-job-records tip
  798d92524dfcf4b24bc312712d21453f159b204a), each forecast clean with
  git merge-tree against the actual parent (purely additive trees, no
  shared-code change), preserving candidate order/report/implementation
  histories. Adds provenance_records.py (admit_record/catalog/Registry
  bind_chunk/bind_neighbors/bind_derived/reader_allows over strict
  versioned Scope/Dependency/Block/SourceFragment/Separator/Chunk/
  Neighbors/Derived/Grants/Restrictions DTOs) and job_records.py
  (admit/serialize/transition over JobSpec/Configuration/InputRef/
  JobState/Attempt/OutputRef), the ONE combined
  tests/integration/test_canonical_records_journey.py store-to-record
  journey (shared-byte two-document store with distinct
  rights/labels/corpus, metadata revision, code-point multi-span
  chunks with explicit separators and repeated table-header
  references, reciprocal neighbors, same-source derived support with
  label union and cross-boundary rejection, unknown-version
  fail-closed reader intersection, job/attempt roundtrip and bounded
  transitions) and docs/data-model.md record protocol. NOT a GitHub
  PR/default-main merge. Extraction, contextualization, embedding,
  snapshots, serving/auth and worker execution remain later ordered
  scope (006/010/007/008/014/017); DTO COMPLETE is not artifact, cache
  or execution proof; all real qualification remains NOT RUN.
