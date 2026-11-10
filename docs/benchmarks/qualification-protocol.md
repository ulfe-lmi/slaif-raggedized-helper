# Qualification trial protocol — finite repeated-parent trials (OAP 004-a)

This document describes the EXECUTED software of objective 004 (the
004-a finite qualification trial runner and the 004-b/004-c evidence
contract corrections): one finite qualification trial runner, strict
bounded trial-spec/sample/result contracts, bounded safe spec file
input, available-stage latency summaries and actual
gateway/direct repeated-parent composition. It records the exact 004
software replan (the D0 replan in order 004-a): authorized real
gateway/GPU/model/corpus inputs remain absent, so this software
establishes usable instrumentation and exact prerequisites; actual
A1/hardware/quality feasibility remains UNPROVEN and is mandatory at
019/ICA/MVP. The 004-b correction completed the evidence contracts
and input boundaries of the verified 004-a head, and the 004-c
correction (this slice) closes the cross-field evidence-consistency,
metric-completeness, decoded-Unicode and serializer/spent-ledger gaps
on the verified 004-b head; resource telemetry, vector/rank parity and
full named gate composition remain required in later proof-sized 004
continuations (strategic activation required). Whole-004
acceptance/merge and 005 selection are not delegated here.

## Explicit supported CLI commands

All commands run offline by default; execution is an explicit opt-in.

```sh
# Machine-readable prerequisite projection (architecture section 23.2;
# offline; zero model/HTTP/telemetry I/O; real trials NOT_RUN).
uv run raggedized qualification gates

# Offline plan for one strict trial spec: validates spec vs configured
# identities, prints deterministic plan (fingerprints, sequence shape,
# budgets, declared identities, gate projection) with execution NOT_RUN.
# Exit 0 = clean plan; exit 2 = rejected plan with exact safe reasons
# (always zero dispatch). Zero model/HTTP/telemetry I/O.
uv run raggedized qualification plan --config CONFIG.json --spec SPEC.json

# EXPLICIT opt-in execution of one finite repeated-parent trial against
# the configured gateway route or materialized offline-diagnostic direct
# destination through the real adapters and real transport.
uv run raggedized qualification run --config CONFIG.json --spec SPEC.json

# Deterministic explicit synthetic route: an owned 127.0.0.1 loopback
# fixture is started by the process, the real adapters speak to it, and
# the evidence is labeled MOCK / synthetic-owned-fixture. Configured
# secret references are NEVER read in synthetic mode.
uv run raggedized qualification run --config CONFIG.json --spec SPEC.json --synthetic
```

`run` exit codes (same honest semantics as `probe`): `0` complete
(execution status — every declared sample resolved; may contain
failed/unknown samples; never qualification), `1` not-run/incomplete
(finite budget or adapter preflight stop), `2` pre-dispatch refusal
(invalid spec, inconsistent fingerprints/settings, missing
target/adapter prerequisites, absent or invalid credential reference,
knowably invalid `--output` destination) — always with zero dispatches,
`3` post-work evidence export failure after the trial returned (the
full safe evidence document, including the transport-boundary
spent-attempt ledger, is written to stdout; blind replay is not
invited). `--output PATH` writes the evidence file; a knowably invalid
destination is refused before dispatch (exit 2, zero HTTP) and a
failure that occurs only after the trial returned is the honest exit-3
export-stage error.

Import, `--help`, `doctor`, `qualification gates` and `qualification
plan` perform zero model/HTTP/telemetry I/O. Only `qualification run`
dispatches, and only on explicit opt-in.

## Trial spec (strict, bounded, frozen)

`raggedized qualification run/plan` take a strict JSON spec validated by
`slaif_raggedized_helper.qualification.spec.TrialSpec`
(`extra="forbid"`, frozen). Fields:

| Field | Constraint | Semantics |
|---|---|---|
| `spec_version` | `1` | contract version |
| `trial_id` | plain token, 1..100 | trial identity (part of request IDs) |
| `workload` | `"repeated-parent"` | the ONLY supported workload |
| `purpose` | `"annotation"` | the ONLY supported purpose (visual: 016; answer: 014) |
| `parent` | 1..4096 chars | constant bounded synthetic parent |
| `suffixes` | 1..8 entries, 1..256 chars each | deterministic child suffixes; sequence = ordinal mod len |
| `seed` | int 0..2^32-1 | bound identity only; no seed-driven variation is implemented (prerequisite 004-b) |
| `warmups` | int 0..16 | warmup samples (kept separate from measured samples) |
| `repetitions` | int 1..64 | measured samples |
| `concurrency` | `1` only | concurrency above 1 is unimplemented (prerequisite 004-b / ONLINE-02) |
| `code_version` | plain token | must equal the executing package version |
| `backend` | `"gateway" \| "direct"` | the actually configured application path |
| `declared_model` | 1..256 chars | must equal the configured route/native model |
| `profile` | plain token or null | when present, must be a configured profile name |
| `template_build_id` | plain token or null | direct trials only; must match the configured template qualification build_id when both present |
| `budgets.deadline_seconds` | finite positive, <= 86400 | ONE absolute trial deadline |
| `budgets.max_dispatches` | int 1..4096 | ONE shared call/attempt admission allowance |
| `budgets.max_output_tokens_total` | int 1..1000000, >= sample count | total output-token allowance |
| `workload_fingerprint` | `sha256:<64hex>` | declared digest of the exact workload; recomputed and refused on mismatch |

Refusals are fixed, safe and pre-dispatch (zero HTTP): unknown settings
(`extra="forbid"`), the unimplemented workload controls
(`context`/`pair`/`batch`/`precision`/`seed_variation`/
`concurrency_policy` each refuse with their NAMED prerequisite, never a
silent claim), bool-as-number, nonfinite/negative/out-of-bounds values,
`workload`/`purpose`/`concurrency` outside the supported values,
inconsistent `workload_fingerprint`, and every declared-identity
mismatch against the executing package and the configured backend.
Arbitrary supplied JSON can select a workload and budgets; it can never
carry or prove execution evidence.

## Bounded spec file input (004-b)

The spec file is operator-supplied untrusted input. The CLI reader
(`slaif_raggedized_helper.qualification.specio`) enforces, in order,
BEFORE any fingerprinting or dispatch:

- descriptor/type: the file is opened NON-BLOCKING and the ACTUAL
  OPENED descriptor is `fstat`-checked — directories, FIFOs, sockets
  and character/block devices (including a path that resolves through
  a symlink to a special file) are refused without ever blocking on a
  writer-less open;
- bytes: a finite documented read bound of 65536 bytes (the bound
  bounds admission; the loop may read one 4096-byte chunk past the
  bound to detect the overflow);
- encoding: STRICT UTF-8 — invalid Unicode is refused before
  fingerprinting/dispatch, never replaced or truncated into a new
  workload;
- decoded Unicode: after decoding and JSON parsing, the strict
  `TrialSpec` field validators refuse a workload string that decodes
  to INVALID Unicode — an unpaired surrogate code point
  (U+D800..U+DFFF, e.g. from a JSON `\uD800` escape) — with a fixed
  safe reason BEFORE fingerprinting or request construction (004-c).
  Valid Unicode — including escaped astral surrogate pairs and
  non-Latin text — is admitted unchanged; the refusal performs no
  replacement, no truncation, no global encoding change and no
  fingerprint-version change;
- JSON: the expected decoder failures are FIXED typed refusals —
  `not_json` (with the decoder line number), `integer_too_large`
  (a JSON integer beyond the interpreter's fixed digit bound) and
  `too_deep` (nesting beyond the interpreter's recursion bound). The
  process-global decoder limits are deliberately NOT changed to work
  around the failures; a syntactically valid but wrong-type document
  is refused by the strict `TrialSpec` validation instead.

All refusals are pre-dispatch (exit 2, always zero HTTP) with fixed
safe JSON evidence: `SPEC_MISSING` (absent/unreadable) or
`SPEC_INVALID` with the fixed `reason` code and a fixed message that
never echoes the input value or a private path; no raw traceback.
Ordinary valid regular-file specs and the existing typed malformed-
JSON refusal (`SPEC_INVALID`, exit 2) are preserved, as are the
config/secret privacy rules and the exit-code distinctions.

## Budget admission and accounting semantics

- ONE absolute trial deadline spans ALL warmups, repetitions, adapter
  retries, template and model calls. It is never reset per sample.
- ONE shared dispatch admission allowance is reserved BEFORE every real
  transport invocation — model dispatches, native template work and
  failed connects all consume it. It is never reset per sample.
- Both are enforced at the ACTUAL transport dispatch boundary (the
  trusted shared-budget seam from objective 003, reused, not
  duplicated): the deadline is rechecked and the allowance reserved
  before each `post_json`; per-call allowances can only tighten the
  absolute deadline, never extend it.
- A native sample minimum of 2 calls (template + completion) and a
  gateway minimum of 1 call guard sample START ADMISSION: a sample is
  never started unless its minimum fits the remaining shared
  allowance, so the admission boundary is exact. This is an
  ADMISSION GUARD ONLY — it does not guarantee a complete sample:
  the absolute deadline can expire while a sample is in flight,
  template work can fail or be refused, retries can consume the
  allowance, and operator cancellation can close in-flight work. In
  each case the work already dispatched is preserved in the
  transport-boundary spent-attempt ledger, the recorded sample (if
  any) keeps its honest outcome (terminal / failed /
  unknown_completion) and the trial reports `incomplete` /
  `not_run` with the exact `stop_reason`. Retries inside a sample
  still consume the shared allowance at the transport boundary.
- Output reservation: each sample reserves its deterministic even share
  (`max_output_tokens_total // sample_count`) as the request's
  `max_output_tokens` before dispatch; the summed per-sample
  reservation never exceeds the total. Observed usage is recorded
  exactly as reported by the backend; unknown usage stays null and is
  never fabricated (preserving the 003 usage behavior).
- Deadline/cancellation: expiry stops NEW work and retries before
  dispatch; the owned in-flight exchange is closed and joined by the
  transport's bounded cancellation scope (finite join bound;
  cooperative in-flight limit). The upstream model process is never
  killed.
- Ambiguity: a post-dispatch failure (accepted-then-closed) leaves
  completion UNKNOWN, is conservatively counted as spent and is never
  replayed; only positively pre-dispatch failures are retryable under
  the adapter's finite configured retry policy (which itself consumes
  the shared allowance).

## Strict sample/result evidence contracts (004-b/004-c)

The per-sample records and the trial result envelope are EXACT,
BOUNDED, FROZEN DTOs
(`slaif_raggedized_helper.qualification.contracts`), not loose dicts:

- `TrialSample` binds the sample ordinal/phase, the fixed outcome
  vocabulary (terminal/refusal/failed/incomplete/unknown_completion),
  the `unknown` physical state, suffix index, bounded input
  fingerprint, fixed safe error class (no provider raw body),
  adapter-reported cycles (not the authoritative dispatch count),
  label-qualified and label-independent text/content fingerprints,
  the per-request declared backend binding (absent stays null),
  `UsageFacts` (known-or-null reported counters — a reported known 0
  is preserved, unknown stays null, never fabricated), `TimingsFacts`
  (known-or-null reported model-phase timings) and the caller
  wall-seconds observation;
- the `TrialEvidence` envelope binds the schema/version, backend,
  status/stop-reason, evidence/target class, the declared workload
  section (digests, positional suffix evidence, sequence shape), the
  budget section (including measured elapsed), the declared/observed
  identity sections (unavailable physical identities stay the fixed
  `unverified`/`unavailable` literals, never guessed), the credential
  reference section (opaque env name / file digest / synthetic
  canary), the recorded requests, the transport-boundary call
  accounting (never dropped after work), the accounting section and
  the analysis section;
- malformed identity/outcome/numeric shapes and bool-as-number are
  REFUSED; contradictory reported cache/input facts remain valid raw
  facts (their invalidity label lives in the accounting section,
  never in a mutation of the raw value);
- the contracts are used at the ACTUAL boundaries: sample records are
  validated at CONSTRUCTION (the runner stores the DTO projection),
  the analysis boundary validates every sample before computing, and
  the full envelope is validated at SERIALIZATION (the CLI refuses to
  render/export a document that violates the contract — an honest
  post-work exit-3, never a silent export);
- `validate_trial_evidence` additionally requires the analysis
  section to EQUAL the pure recomputation from the recorded samples,
  driven by the ACTUAL transport-boundary call ledger
  (`transport_boundary.calls_by_kind`), never the analysis's own copy
  of the call counts (the analysis is a pure function of its
  observations; a forged or drifted analysis — including a call count
  that conflicts with the ledger — is a contract violation; adapter
  cycles can differ legitimately and never replace actual transport
  attempts);
- the envelope binds every duplicated fact to its authoritative
  section (004-c): the envelope backend equals the declared backend;
  every KNOWN per-sample backend fingerprint equals the observed
  per-trial backend binding (an absent binding stays null, never
  guessed); the target type is consistent with the evidence class
  (MOCK iff synthetic-owned-fixture, CONFIGURED_UNVERIFIED iff
  unverified); the output-reservation total/per-sample equal the same
  declared `max_output_tokens_total` / per-sample budget, with the
  per-sample share the floor even share over the DECLARED scheduled
  sample count (never the shorter recorded prefix after an early
  stop); and the cache/input consistency counts equal the shared pure
  derivation from the actually recorded raw usage (an unreported
  cache counter is uncounted, a known cache with unknown input is
  uncheckable, cache > input is contradictory — raw contradictory
  counters stay valid sample facts, the label lives in the accounting
  section);
- the stage metric summaries are complete or null (004-c): `n=0`
  requires ALL-NULL quartiles and `n>0` requires EVERY quartile
  present, finite, non-negative and ordered `min <= p50 <= p95 <=
  max`; a partial quartile set with a positive count is refused;
- the CLI serialization boundary uses the canonical FULL strict
  result contract (`validate_trial_evidence` — strict shape plus the
  analysis pure-recomputation), not a basic shape check (004-c): a
  post-work rejection is an honest exit 3 — a fixed safe structured
  error carrying the ACTUAL valid spent-attempt ledger is written to
  stdout (and stderr) and the invalid record is never exported as a
  valid result; when the ledger itself cannot be validated its
  availability is marked honestly (never assumed zero, never a crash
  while formatting);
- these checks prove INTERNAL consistency only — never that the
  declared metadata is true, that a fingerprint proves deployed
  hardware/model identity, or that the imported JSON was executed
  here;
- the public dict JSON compatibility is preserved through validated
  DTO serialization (the rendered document is the DTO projection of
  the same values).

## Quantile definition (latency analysis)

`slaif_raggedized_helper.qualification.analysis` computes
min/p50/p95/max with the NEAREST-RANK convention: sort the finite
non-negative sample values ascending; quantile p takes rank
`ceil(p/100 * n)`, 1-based, clamped to 1..n. Statistics are over
terminal-outcome samples ONLY (per phase group: warmups and measured,
separately); failed, unknown-completion, refusal, incomplete and
invalid observations are counted separately and never averaged into
model latency. Zero-sample sets produce `n=0` and all-null metrics.
The analysis is a pure function of the recorded observations: the same
observations always produce the same summary (deterministic summaries).

In addition to the caller-wall `latency_seconds` summary, each phase
group carries reproducible AVAILABLE-STAGE summaries
(`stage_metrics`) of n/min/p50/p95/max per metric, separately for
warmups and measured samples:

- `caller_wall_seconds` — caller wall time (includes adapter cycles
  and template work; not model work);
- `prefill_seconds` / `decode_seconds` / `model_total_seconds` — the
  native-reported model-phase metrics (reported `prompt_ms/1000`,
  `predicted_ms/1000` and their reported model-total), distinct from
  caller wall time and template work;
- `ttft_seconds` — first-token latency, never reported by the pinned
  dialects.

A reported KNOWN ZERO counts as a measurement; a MISSING (null)
reported value is ABSENT (counted in `missing`), never a zero; a
non-finite or negative reported value is counted invalid and excluded.
The gateway dialect reports no prefill, so its `prefill_seconds`
stage stays `n=0` / all-null (unavailable, not 0); native
`ttft_seconds` likewise stays unavailable. Metric provenance is
carried per stage (`source`); failure/unknown counts, known zeros,
missingness and the nearest-rank convention are all explicit. An
invalid/empty/incomplete/synthetic/unverified evidence set cannot
qualify, and physical cold/warm cache state or evaluated-prefill work
is never inferred from cached/submitted token counters.

Wall-time boundary: per-sample `wall_seconds` is CALLER wall time
around one `generate()` call — it includes adapter cycles, template
work and transport time. It is NOT model work time. Native template
time is NOT TTFT (the native dialect reports no first-token
measurement, so `ttft_seconds` stays null). The pinned gateway dialect
reports no evaluated-prefill metrics, so `prefill_seconds` stays
null/unavailable and missing prefill is never a zero.

## Evidence classes: declared / observed / supplied-unverified / MOCK

- DECLARED identity: what the spec/config say (code version, backend,
  model, profile, purpose, template build, workload/seed fingerprints).
  Verified pre-dispatch; a mismatch refuses.
- OBSERVED evidence: what the executed adapters/transport reported per
  sample (outcome, error class, known usage, reported timings,
  backend fingerprint). Missing measurements stay null.
- UNAVAILABLE physical identity: runtime/GGUF/tokenizer hardware facts
  the runner cannot measure on this host. Recorded as
  `runtime_identity: unverified`, `model_runtime_identity: unverified`,
  `tokenizer_identity: unavailable` — never guessed.
- TARGET PROVENANCE: a configured destination is
  `target_type: unverified` (`evidence_class:
  CONFIGURED_UNVERIFIED`) — the runner cannot classify an arbitrary
  configured URL (loopback or not) as owned or live, and no boolean
  makes it so. Only the explicit `--synthetic` route, which actually
  starts the owned deterministic fixture, is
  `target_type: synthetic-owned-fixture` / `evidence_class: MOCK`
  (configured secrets never read; a fixed synthetic canary is used for
  the fixture Authorization header).
- First/repeated ORDER is the sample ordinal; physical COLD/WARM state
  is UNKNOWN without cache reset/isolation evidence and is never
  inferred from position (`physical_state: unknown` per sample).
- Reported cache counters are distinct reported facts, not
  evaluated-prefill work; the supported relation
  (`cache_hit_tokens <= input_tokens` when both reported) is checked
  per sample, contradictory counters are preserved as RAW FACTS only
  and can never become positive evidence; the pinned gateway dialect's
  reported `cached_tokens` maps to `cache_hit_tokens` while
  evaluated-prefill metrics stay null.
- No raw prompt/output text, endpoint URL, credential, private path or
  provider error body in evidence: inputs/outputs are fingerprints
  only, the endpoint is an opaque digest (a constant fixture identity
  in synthetic mode), file credential references are opaque digests.

## Finite runner behavior and unsupported workload settings

- The trial executes exactly the declared sequence (warmups then
  measured, ordinal mod len(suffixes)); status is `complete` (every
  sample resolved — an execution status that may contain
  failed/unknown samples), `incomplete` (budget stop mid-sequence
  with the exact `stop_reason`: `budget_exhausted_deadline` /
  `budget_exhausted_dispatches`; `evidence_contract_violation` is the
  internal construction-boundary stop) or `not_run` (zero dispatches,
  e.g. deterministic adapter preflight refusal).
- Unsupported workload settings (context/pair/batch/precision/
  seed-variation, concurrency above 1, visual/answer purposes) are
  refused at spec validation with their named prerequisites — they are
  never silently applied or claimed.
- The trial sends NO cache-key/slot control: no assumed slot reuse
  (GATEWAY-03), no cache-affinity claim.

## Deterministic explicit synthetic route

`--synthetic` starts an owned disposable 127.0.0.1 loopback server
(deterministic pinned-dialect responses, deterministic usage and
native timings), points the real adapters/transport at it and shuts it
down when the trial returns. For identical inputs the evidence is
identical apart from per-run wall-clock measurements (per-sample
`wall_seconds`, `elapsed_seconds` and the latency min/p50/p95/max
derived from them); all identity, accounting, outcome, metric,
convention and gate fields are deterministic. The route is MOCK and
unqualified: it proves executable bounded composition, wire behavior
and accounting, never real target, hardware, model, cache or quality
feasibility.

## 004 software replan and remaining prerequisites

- The 004 D0 replan is explicit: 004-a delivered the runner, strict
  spec contracts, composition and the machine-readable prerequisite
  projection. The 004-b correction completed the missing evidence
  contracts (strict bounded sample/result DTOs used at the
  construction/serialization/analysis boundaries, the analysis
  recomputation invariant), the bounded safe spec file input
  (descriptor/type/byte/UTF-8/JSON-decoder typed refusals at zero
  HTTP) and the available-stage summaries. The 004-c correction (this
  slice) closes the independently reproduced cross-field evidence
  consistency bindings (analysis recomputation driven by the actual
  transport-boundary ledger; envelope/declared backend and per-sample
  backend-fingerprint bindings; evidence-class/target-type provenance
  pairs; output reservation bound to the declared budget with the
  floor even share over the DECLARED scheduled sample count; cache/
  input consistency counts equal to the pure derivation from the
  actually recorded raw usage), the metric-completeness contract
  (n=0 iff all-null quartiles; n>0 every quartile present, finite,
  non-negative and ordered), the decoded-Unicode admission refusal
  (unpaired surrogate code points refused at spec admission with the
  fixed safe reason, zero HTTP, no input echo) and the
  serializer/spent-ledger boundary (the canonical FULL strict result
  contract at CLI serialization; a post-work rejection emits the
  fixed safe error with the actual valid spent ledger and honest
  ledger availability, never an assumed zero, and the invalid record
  is never exported), and corrects the documentation and context
  measurements to the actual implementation. Resource telemetry,
  vector/rank parity and full named gate composition remain required
  in LATER proof-sized 004 continuations (strategic activation
  required); 019/ICA/MVP gate actual feasibility. These corrections
  do not substitute a smaller objective for that scope.
- Live target authorization: NONE. No approved actual URL/model/
  secretref/GPU ownership/corpus reply has arrived. ALL real trials
  persist NOT_RUN; no positive topology, cache, speedup, quality,
  VRAM, license or readiness claim follows from this software or from
  any synthetic/configured-unverified evidence.
- Gate projection: `docs/benchmarks/qualification-gates.json` covers
  every architecture section 23.2 ID (GATEWAY-01/02/03, DIRECT-01,
  V100-MEM-01/02, RERANK-01, EMBED-01/02, ONLINE-01/02, OPS-01/02,
  LICENSE-01) with status NOT_RUN and named pending prerequisites
  (004-b, 007, 012, 014, 015, 016, 017, 018). Only the text
  repeated-parent runner entrypoints (GATEWAY-01, GATEWAY-03,
  DIRECT-01) are executable in this slice; LICENSE-01 remains open and
  the certifi (MPL-2.0) exception has not been granted.
- Startup prompt: the `/goal`-first bounded-goal prompt introduced by
  the 004-a operational correction is NOT operationally validated by
  file hash alone. The 004-b fresh-handoff goal-first startup
  qualification attempt is RECORDED FAILED by strategy (upstream
  payload refusal before any implementation; the stalled goal was
  cleared). The previously qualified ORDINARY startup is restored,
  and the bounded native goal sequence is set by strategy AFTER this
  ordinary startup. U10 stays OPEN; do not self-trigger it, do not
  claim the goal-first qualification passed, and do not add readers
  or replay the consumed control signal.

## Tests

See TESTING.md T08 (unit contracts in `tests/unit/test_qualification.py`;
installed-CLI owned-loopback composition in
`tests/integration/test_qualification_composition.py`). Covers the
strict spec refusals, the bounded spec file input refusals (special
file/FIFO without blocking, byte bound, strict UTF-8, typed JSON
decoder/integer/depth refusals, zero HTTP, no path echo), the decoded
workload Unicode admission (unpaired-surrogate parent / lone-low-
surrogate first suffix refused at spec admission with the fixed safe
reason — zero HTTP, no traceback, no input echo; valid escaped-astral
and non-Latin Unicode admitted unchanged), the strict sample/result
contract roundtrips and invalid shapes, the envelope relations (prefix
recording, status/stop-reason/allowance invariants, the analysis
recomputation driven by the actual transport-boundary ledger) and the
004-c cross-field bindings (every single-field contradiction refused:
envelope backend vs declared backend, known per-sample backend
fingerprint vs the observed per-trial binding (null stays allowed),
evidence class vs target type, output reservation vs the declared
budget and the floor even share over the declared sample count,
cache/input consistency claims vs the pure derivation from the
actually recorded raw usage; the unaltered envelope stays the
positive), the quartile completeness contract (n=0 iff all-null
quartiles; n>0 every quartile present, finite, non-negative and
ordered), the hand-computed stage quantiles with known-zero/missing/
exclusion semantics, the serialization-boundary post-work refusal
(fixed safe error with the actual valid spent-attempt ledger on
stdout, honest ledger availability, the invalid record never
exported), and all 004-a transport, global-budget, retry, native-
template, UNKNOWN-outcome, credential and export positives. Synthetic
and offline only: no external network, product services, real keys,
GPU or model downloads.
