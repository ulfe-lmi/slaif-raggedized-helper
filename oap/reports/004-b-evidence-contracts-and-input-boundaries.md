# OAP Coding Report — 004-b

Identifier: 004-b
Result: COMPLETE
Repository: ulfe-lmi/slaif-raggedized-helper
PR number: 6
Branch: oap/004-qualification-harness
Base branch: main
Implementation head SHA: a769265cb888271a9daf67dbe333025b4e423a6d
Report publication commit: SELF

## Work and scope

Executed oap/orders/004-b-evidence-contracts-and-input-boundaries.md
(Status FINAL, Decision: NONE, live target authorization: NONE, PR mode
AMEND_EXISTING_PR, base commit 2bc320ff9e66c874f07da061218f2ff52e3420a9)
as the bounded correction on the existing numeric 004/PR 6, completing
the missing 004-a evidence contracts and correcting the independently
reproduced input failures on the verified 004-a head
17085c03f2ebabc5744fe1a19358e71ff4a6aedd (whose immutable COMPLETE
report-only SELF 056ca40f15e172e02dd084ecf4dca92eea594c0a is preserved,
not strategic acceptance). Round start reconciled against GitHub:
unique PR 6 OPEN, original branch, main base
2bc320ff9e66c874f07da061218f2ff52e3420a9, remote head 056ca40. The
worktree carried exactly the strategic round-start bytes: oap/active
004-a -> 004-b (exactly `004-b\n`), the new
oap/orders/004-b-evidence-contracts-and-input-boundaries.md, and the
final 004-a review oap/reviews/004-a-review.json (SHA-256
02ab0d2288191469c5c480b11777d71b509b3963b8110e0f9afeb5f7a6db0611). The
sole control OK (consumed 2026-11-10T14:11:37Z) was never reread or
replayed and no waiter was created. All strategic files were committed
byte-for-byte unchanged inside the single implementation commit
a769265cb888271a9daf67dbe333025b4e423a6d (18 files, +2543/-104) on
branch oap/004-qualification-harness from verified remote head 056ca40.
No reset/clean/stash/force-push was used.

The four ordered corrections from oap/reviews/004-a-review.json:

- F01 NEW `src/slaif_raggedized_helper/qualification/specio.py` —
  bounded safe trial-spec file input: non-blocking
  `O_RDONLY|O_NONBLOCK` open with `fstat` of the ACTUALLY OPENED
  descriptor (directories, FIFOs, sockets and character/block devices,
  including a path that resolves through a symlink to a special file,
  are refused without ever blocking on a writer-less open), a finite
  documented 65536-byte read bound (the loop may read one 4096-byte
  chunk past the bound to detect the overflow), STRICT UTF-8 handled
  before fingerprinting/dispatch (invalid Unicode is never replaced or
  truncated into a new workload), and the expected JSON
  decoder/integer/depth failures normalized to fixed typed refusals
  (`not_json` with the decoder line, `integer_too_large`, `too_deep`)
  with fixed safe messages — no raw traceback, no input or private-
  path echo, no process-global decoder-limit change (the
  interpreter's integer-digit and recursion limits are left untouched;
  the failures they raise are caught and converted). `cli.py` loads the
  spec through `load_trial_spec_json` and maps the refusal to the
  pre-dispatch `SPEC_MISSING`/`SPEC_INVALID` distinction (exit 2,
  always zero HTTP), preserving the ordinary valid regular-file and
  malformed-JSON positives, config/secret privacy and the exit-code
  distinctions.
- F02 NEW `src/slaif_raggedized_helper/qualification/contracts.py` —
  explicit strict bounded sample/result evidence contracts: frozen
  `extra="forbid"` DTOs with strict int/float/bool (no coercion)
  (`UsageFacts`, `TimingsFacts` with finite/nonnegative validators,
  `TrialSample`, `StageMetric`/`StageMetrics`/`GroupStats`/
  `AnalysisSection`, the envelope sections and `TrialEvidence`),
  binding schema/version, sample ordinal/phase, the fixed outcome
  vocabulary, `unknown` physical state, bounded input fingerprint,
  fixed safe error class, declared/observed identities, workload/
  backend fingerprints, known-or-null reported counters/timings (a
  reported known 0 is preserved, unknown stays null, never
  fabricated), actual call accounting and finite field limits.
  Envelope invariants: recorded requests are the EXACT LEADING PREFIX
  of the declared workload (an incomplete tail must be unrecorded),
  `remaining + attempted == budgets.max_dispatches`, status/stop-
  reason consistency, `not_run` implies zero dispatches (it may carry
  zero-dispatch refusal samples), and `validate_trial_evidence`
  additionally requires the analysis section to EQUAL the pure
  recomputation from the recorded samples (lazy import of
  `analyze_trial`). The contracts are used at the ACTUAL boundaries:
  `runner.py` validates every sample at CONSTRUCTION (the runner stores
  the DTO projection; `STOP_EVIDENCE_CONTRACT_VIOLATION` is the
  internal construction-boundary stop), `analysis.py` validates every
  sample at the ANALYSIS boundary, and `cli.py` validates the full
  envelope at SERIALIZATION — a violating executed document is an
  honest post-work exit-3 `EVIDENCE_CONTRACT_VIOLATION` with the
  transport-boundary spent-attempt ledger preserved, never a silent
  export. Malformed identity/outcome/numeric shapes and bool-as-number
  are refused; contradictory reported cache/input facts remain valid
  raw facts (their invalidity label lives in the accounting section).
  The public dict JSON compatibility is preserved through validated
  DTO serialization.
- F03 MODIFIED `qualification/analysis.py` — reproducible available-
  stage summaries: each warmup/measured group carries `stage_metrics`
  of n/min/p50/p95/max per stage metric
  (`caller_wall_seconds`, `prefill_seconds`, `decode_seconds`,
  `model_total_seconds`, `ttft_seconds`) retaining the documented
  nearest-rank convention, with known-zero counts, missing (null)
  absence, nonfinite/negative invalid-observation exclusion and
  per-stage provenance. Native reported prefill/decode/model-total
  stay distinct from caller wall/template work; the gateway dialect
  prefill and native TTFT stay `n=0` all-null (unavailable, not 0).
  Invalid/empty/incomplete/synthetic/unverified evidence sets cannot
  qualify; physical cold/warm state and evaluated-prefill work are
  never inferred from cached/submitted token counters.
- F04 MODIFIED docs to the actual implementation: TESTING.md T08
  (14 section 23.2 IDs, not 15, plus the new contract/input-reader/
  stage-summary coverage), docs/benchmarks/qualification-protocol.md
  (new "Bounded spec file input (004-b)" and "Strict sample/result
  evidence contracts (004-b)" sections, available-stage summaries in
  the quantile section, the sample-start minimums documented as an
  ADMISSION GUARD ONLY — it does not guarantee a complete sample after
  deadline/cancellation/template-failure/retries — the
  `evidence_contract_violation` construction-boundary stop, the
  updated 004-b replan, and the startup paragraph recording that the
  004-b fresh-handoff /goal-first startup qualification is RECORDED
  FAILED by strategy with the restored ordinary startup), README.md
  (the 004 bullet now matches the executed software), STATUS.md
  (current state + the full 004-b history entry), docs/
  UNCERTAINTIES.md (dated 004-b observation), and the context
  measurements refreshed from the final actual files with the
  manifest: routine governance 42158 UTF-8 bytes (ceiling 50000),
  TESTING.md 9607, MANIFEST.json hashes updated for TESTING.md and
  oap/governance/CONTEXT-BUDGET.md (the only manifest-tracked files
  changed this round); exact model tokens and client injection remain
  UNMEASURED.

No dependency, serving-stack, encoder/reranker, architecture or
protected source-original change; no helper/global client/model/
profile/auth/runtime-policy change; no prompt-source edit (oap/
prompts/coding-startup.txt untouched — the ordinary startup
restoration and bounded native goal are strategy's, set AFTER this
ordinary startup). No merge, no next-objective work; resource
telemetry, vector/rank parity and full named gate composition remain
required in later proof-sized 004 continuations.

## Acceptance evidence

Criterion 1 (bounded spec input, unsupported file types refused
without blocking, before inference): `specio.load_trial_spec_json`
opens non-blocking and fstats the opened descriptor, enforces the
65536-byte bound, strict UTF-8, and fixed typed JSON failures with no
process-global decoder-limit change. Proof:
tests/unit/test_qualification.py::TestSpecInputReader (valid regular-
file roundtrip; absent -> typed `SPEC_MISSING`; owned FIFO refused
WITHOUT blocking; symlink-to-FIFO refused on the opened descriptor
while symlink-to-regular is admitted; directory refused; file past the
bound refused at the bound while the file AT the exact bound is
admitted; invalid UTF-8 refused before fingerprinting; malformed JSON
typed with the decoder line; oversize integer typed with the global
limit verified untouched; deep nesting typed; refusal messages never
echo the path) and installed-CLI zero-HTTP proofs:
tests/integration/test_qualification_composition.py::
test_spec_invalid_utf8_refused_typed_zero_http,
::test_spec_oversize_integer_refused_typed_zero_http,
::test_spec_fifo_refused_without_blocking,
::test_spec_deep_nesting_and_malformed_json_typed,
::test_spec_absent_file_stays_typed_missing, while the 004-a
::test_trial_invalid_spec_refused_zero_dispatch (typed malformed-JSON
positive) and the ordinary valid regular-file admission stay green.
The retained /tmp/raggedized004-cli-spec-input-review.py witness (an
owned disposable input fixture, never an OAP FIFO) was re-run at this
head: the three 004-a reproductions (invalid UTF-8 raw
UnicodeDecodeError/exit 1; 5000-digit integer raw ValueError/exit 1;
owned TEMP FIFO blocking `Path.read_text`) are now fixed — typed
`SPEC_INVALID` exit 2 at zero HTTP with no traceback and a bounded
FIFO refusal — while the malformed-JSON typed positive and all 004-a
witnesses (budget-admission, runner-http, connect-retry, sigint-
cancellation) preserve their positives unchanged.

Criterion 2 (explicit strict bounded sample/result contracts used at
actual construction/serialization/analysis boundaries):
`contracts.py` provides the frozen extra=forbid DTOs with strict
int/float/bool; `runner._sample_record` validates via
`TrialSample.model_validate` at construction; `analyze_trial`
validates every sample at the analysis boundary; the CLI validates the
full envelope at serialization (an executed `complete`/`incomplete`/
`not_run` document that violates the contract is exit 3
`EVIDENCE_CONTRACT_VIOLATION` with the spent ledger on stdout). Proof:
tests/unit/test_qualification.py::TestSampleContracts (full roundtrip;
bool-as-number refused at every numeric field; extra/missing fields
refused; malformed outcome/fingerprints refused; malformed numeric
shapes refused; known-zero and all-null preserved; contradictory
cache facts stay valid raw facts) and ::TestEvidenceEnvelope (valid
envelope passes; FORGED analysis refused; drifted group count refused;
tampered identity refused; ordinal/phase mismatch refused; status/
accounting relations enforced including
remaining+attempted == budgets.max_dispatches; not_run envelope with
zero dispatch valid, including zero-dispatch refusal samples;
incomplete prefix envelope valid; incomplete requires the exact
stop_reason and the unrecorded tail). The public dict JSON
compatibility is preserved: the installed-CLI composition suite (which
asserts on the rendered JSON) is unchanged and green.

Criterion 3 (reproducible available-stage n/p50/p95/max summaries,
nearest-rank retained, missing gateway prefill/native TTFT
unavailable not zero): `analysis.py` emits `stage_metrics` per
warmup/measured group. Proof: tests/unit/test_qualification.py::
TestStageSummaries (hand-computed stage quantiles; gateway prefill
stays unavailable-not-zero; a known zero counts while missing is
absent; failed/unknown outcomes excluded from stages; warmup and
measured stages separate; deterministic) and
::TestAnalysisBoundary (malformed samples refused at the analysis
boundary); installed-CLI proofs:
test_gateway_evidence_stage_metrics_available (gateway caller-wall
summary present with prefill/TTFT n=0 all-null) and
test_direct_evidence_stage_metrics_hand_computed (direct per-stage
quartiles hand-computed from the sample observations).

Criterion 4 (meaningful tests: actual CLI regular-file admission,
invalid UTF-8, decoder integer/malformed/deep JSON, owned special-
file/FIFO refusal within finite child bounds, zero HTTP and safe
fixed errors; validated roundtrips and invalid fields/identity/
missingness/accounting; hand-computed stage quantiles and outcome
exclusion; ALL 004-a transport/global-budget/retry/native-template/
UNKNOWN/credential/export positives preserved): the 576-test product
suite (275 unit + 301 integration) is green at the implementation
head, including every test named under criteria 1-3 and the unchanged
004-a composition suite (shared allowance across warmups/repetitions,
retry consumption at the real transport boundary, deadline
exhaustion without replay, accepted-then-closed unknown without
replay, budget-3/budget-4 native boundaries, preflight zero-dispatch,
post-work export stage, metric ambiguity, deterministic synthetic
route, closed-port zero-I/O plan/gates). No assertion was weakened:
the diff only ADDS coverage and tightens the tested contracts; the
root independent oracles remain unchanged.

Criterion 5 (docs corrected to actual implementation; fourteen
section 23.2 IDs; admission guard does not guarantee a complete
sample; accurate source/prompt hashes and measured transitive
governance bytes): TESTING.md T08 now says "all 14 IDs" (the
committed docs/benchmarks/qualification-gates.json contains exactly
the 14 IDs: DIRECT-01, EMBED-01/02, GATEWAY-01/02/03, LICENSE-01,
ONLINE-01/02, OPS-01/02, RERANK-01, V100-MEM-01/02) and names the new
contract/input-reader/stage-summary coverage; the protocol documents
the bounded spec input, the strict contracts, the stage summaries and
the admission-guard-only semantics; oap/governance/CONTEXT-BUDGET.md
was refreshed from the final actual files (42158 bytes, ceiling
50000; TESTING.md 9607) with the MANIFEST.json hashes updated in the
same commit for the two manifest-tracked files changed this round;
the `oap/prompts/coding-startup.txt` manifest hash is untouched
(strategy owns the startup restoration); exact model tokens and
client injection remain UNMEASURED. No retrospective report edits and
no positive physical-feasibility/license claim; real qualification
remains NOT RUN.

Criterion 6 (relevant checks and CI pass; startup qualification
owned by strategy): ruff clean, 576 product tests, 41 OAP scaffold
tests, check_state exit 0 (below), and CI at the implementation head
green (below). The fresh-handoff /goal-first startup qualification is
separately owned by strategy and is RECORDED FAILED (upstream payload
refusal before any implementation; the stalled goal was cleared); it
is NOT claimed passed, no operational validation is claimed from file
hash, no reader was added, and the consumed control signal was never
replayed.

## Verification

Local commands at the implementation worktree (before commit), all
run from /home/janezp/codex-work/slaif-raggedized-helper:

- `uv run ruff check src tests/unit tests/integration` -> All checks
  passed! (exit 0)
- `uv run pytest tests/unit tests/integration` -> 576 passed (275
  unit = 171 baseline + 104 qualification, of which 37 are new 004-b
  tests, zero 004-a tests removed; 301 integration = 271 baseline +
  30 qualification, of which 7 are new 004-b tests, zero removed)
- `python3 -m unittest discover -s tests/oap` -> Ran 41 tests, OK
- `python3 oap/bin/check_state.py --repo-root .` -> exit 0, state
  ACTIVE, active 004-b, order path present, no report yet,
  declared_context_bytes 42158 (activation_matches_current_governance
  is informationally False because the ordered manifest measurement
  change legitimately postdates the activation, exactly as in 004-a,
  per check_state's own source_note)
- Retained /tmp witnesses re-run at this head (owned disposable
  fixtures; see criterion 1): cli-spec-input now shows the typed
  SPEC_INVALID exit-2 refusals and bounded FIFO behavior; budget-
  admission, runner-http, connect-retry and sigint-cancellation
  preserve their 004-a positives.
- CLI smoke: `uv run raggedized --help` exit 0; `qualification
  gates` renders the 14-ID projection with real_trials NOT_RUN;
  `plan`/`run` exercised through the installed-CLI integration suite
  above.

CI observed at the implementation head (run 42840299833, headSha
a769265cb888271a9daf67dbe333025b4e423a6d, workflow CI): OAP tests
(Python 3.12) pass, OAP tests (Python 3.13) pass, OAP tests (Python
3.14) pass, Product tests (Python 3.12) pass, Product tests (Python
3.14) pass — all five jobs SUCCESS. PR #6 head a769265, base main,
open; no auto-merge configured. This report does NOT claim anything
about the future push/CI of the report commit itself; the separate
post-publication verification records those facts.

Mock/live distinction: everything above is synthetic/offline — owned
127.0.0.1 loopback servers, unique synthetic canary keys, owned
disposable /tmp input fixtures, no external network, no product
services, no real keys, no GPU, no model downloads. Live target
authorization: NONE; no live model/hardware trial was executed and
none could be (no approved URL/model/secretref/GPU/corpus). Mock
success is not real qualification; all real qualification gates and
LICENSE-01 remain open and NOT RUN.

## Documentation impact

- docs/benchmarks/qualification-protocol.md: new "Bounded spec file
  input (004-b)" and "Strict sample/result evidence contracts (004-b)"
  sections; available-stage summaries added to the quantile section
  (known-zero/missing/invalid semantics, gateway prefill/TTFT
  unavailable-not-zero, per-stage provenance); the sample-start
  minimums documented as an ADMISSION GUARD ONLY (deadline expiry,
  template failure/refusal, retries and operator cancellation can
  still leave a sample incomplete, with the spent ledger and honest
  stop_reason preserved); `evidence_contract_violation` added as the
  internal construction-boundary stop; the 004 software replan
  updated for 004-b (this correction does not substitute a smaller
  objective for the later telemetry/parity/full-gate continuations);
  the startup paragraph records the RECORDED-FAILED goal-first
  fresh-handoff qualification, the restored ordinary startup and the
  strategy-set bounded native goal AFTER this ordinary startup.
- TESTING.md: T08 updated (14 IDs; contract, input-reader and stage-
  summary coverage; 004-b live authorization NONE).
- README.md: the 004 bullet now matches the executed software
  (bounded contracts at the actual boundaries, bounded safe spec file
  input, available-stage timing summaries).
- STATUS.md: current state moved to the 004-b correction of the 004-a
  slice; full 004-b history entry.
- docs/UNCERTAINTIES.md: dated 004-b observation (U01/U02 stay open;
  U03/U04/U05/U08 unchanged; the stage summaries are instrumentation
  only; U10 stays OPEN with the goal-first qualification RECORDED
  FAILED; live authorization NONE; LICENSE-01 open).
- oap/governance/CONTEXT-BUDGET.md + oap/governance/MANIFEST.json:
  measurements refreshed from the final actual files (42158/50000;
  manifest hashes for TESTING.md and CONTEXT-BUDGET.md; all other
  manifest entries untouched); exact model tokens/client injection
  UNMEASURED.
- No earlier report/order/review bytes were edited; the 004-a report,
  both orders' other bytes and the strategic review remain immutable.

## DHA and boundaries

Decision: NONE (as ordered); no APPEND CRIT-* was ordered and no
candidate critical entry was appended. No D1/D2 action taken.
Preserved resources: Qwen3.8-27B/A100 Q8/xhigh model/profile
settings, existing services, agent homes, real credentials and OAP
FIFOs untouched; `oap/prompts/coding-startup.txt` untouched (strategy
restores the previously qualified ordinary startup and sets the
bounded native goal after this ordinary startup; the goal-first
fresh-handoff qualification is RECORDED FAILED and is not claimed
passed); no live model requests, downloads, service/process/GPU
changes, GPU/telemetry probing or network exposure beyond owned
loopback and GitHub CI/publication; the consumed control/response
signal was never read or replayed; no second waiter started. No merge
performed and no auto-merge requested; the strategic 004-b order,
oap/active (exactly `004-b\n`) and oap/reviews/004-a-review.json
(SHA-256 02ab0d2288191469c5c480b11777d71b509b3963b8110e0f9afeb5f7a6db0611,
re-verified byte-identical in the worktree and in the commit) are
committed byte-for-byte as found. Whole-004 acceptance, further 004
continuations and 005 selection remain strategy alone. Unrelated
worktree state preserved.

## Limitations and remaining work

- The 004-b slice is a bounded correction on the verified 004-a head:
  resource telemetry, vector/rank parity and full named gate
  composition remain required in LATER proof-sized 004 continuations
  (strategic activation required); 019/ICA/MVP gate actual
  A1/hardware/quality feasibility. COMPLETE here is slice execution,
  not whole-004 acceptance, merge or actual feasibility.
- Live target authorization: NONE — no approved actual URL/model/
  secretref/GPU ownership/corpus reply has arrived; ALL real trials
  persist NOT_RUN, and no positive topology, cache, speedup, quality,
  VRAM, license or readiness claim follows from this software or from
  any synthetic/configured-unverified evidence.
- LICENSE-01 remains open: the certifi (MPL-2.0) policy exception has
  not been granted (018 owns the full dependency/model/renderer
  inventory).
- The 004-b fresh-handoff /goal-first startup qualification is
  RECORDED FAILED by strategy (upstream payload refusal before any
  implementation; stalled goal cleared; sole control OK consumed,
  never replayed). The previously qualified ordinary startup is
  restored and the bounded native goal sequence is set by strategy
  AFTER this ordinary startup. U10 stays OPEN; no operational
  validation is claimed from file hash alone; no self-triggering was
  performed.
- Unavailable physical identities (deployed runtime/GGUF, tokenizer,
  GPU state) remain unverified/unavailable on this host by design;
  physical cold/warm cache state stays unknown without cache
  reset/isolation evidence; the trial sends no cache-key/slot control
  (no assumed slot reuse); the sample-start minimums are an admission
  guard only, not a guarantee of a complete sample after deadline/
  cancellation/template failure/retries.
- No failures, skips or blocked tests at the implementation head; no
  scope deviations — the implementation stayed within the ordered
  allowed paths with no new runtime dependency.
