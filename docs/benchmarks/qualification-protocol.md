# Qualification trial protocol — finite repeated-parent trials (OAP 004-a)

This document describes the EXECUTED software of objective 004-a: one
finite qualification trial runner, strict sample/specification
contracts and actual gateway/direct repeated-parent composition. It
records the exact 004 software replan (the D0 replan in order 004-a):
authorized real gateway/GPU/model/corpus inputs remain absent, so this
slice establishes usable instrumentation and exact prerequisites;
actual A1/hardware/quality feasibility remains UNPROVEN and is
mandatory at 019/ICA/MVP. A subsequent strategically activated 004-b
adds resource telemetry, parity analysis and full gate composition;
whole-004 acceptance/merge and 005 selection are not delegated here.

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
  gateway minimum of 1 call guard sample START: a sample is never
  started unless its minimum fits the remaining shared allowance, so
  the boundary is exact and no sample is half-dispatched. Retries
  inside a sample still consume the shared allowance at the transport
  boundary.
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
  failed/unknown samples), `incomplete` (budget stop mid-sequence with
  the exact `stop_reason`: `budget_exhausted_deadline` /
  `budget_exhausted_dispatches`) or `not_run` (zero dispatches, e.g.
  deterministic adapter preflight refusal).
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

- The 004 D0 replan is explicit: this slice (004-a) delivers the
  runner, strict contracts, composition and the machine-readable
  prerequisite projection only. 004-b (strategic activation required)
  adds resource telemetry, parity analysis and full named gate
  composition; 019/ICA/MVP gates actual feasibility.
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
- The new bounded-goal `/goal`-first coding startup prompt
  (`oap/prompts/coding-startup.txt`, order 004-a operational
  correction) is NOT operationally validated by file hash alone;
  strategy qualifies it during the same-objective 004-b fresh control
  handoff, before final 004 acceptance. Do not self-trigger it.

## Tests

See TESTING.md T08 (unit contracts in `tests/unit/test_qualification.py`;
installed-CLI owned-loopback composition in
`tests/integration/test_qualification_composition.py`). Synthetic and
offline only: no external network, product services, real keys, GPU or
model downloads.
