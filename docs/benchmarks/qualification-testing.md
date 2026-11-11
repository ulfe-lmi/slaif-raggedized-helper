# Qualification verification notes (objectives 004-a through 004-f)

Detailed non-routine verification notes moved out of TESTING.md T08/T09/T10 so the
routine coding context stays within its measured byte ceiling. All coverage,
limitations and distinctions below are preserved verbatim from the accepted 004
rounds; TESTING.md keeps concise summaries and pointers to this document.
Real target/model/hardware/quality/vision/license qualification remains NOT RUN
in every section (live authorization: NONE for each 004 round).

T08. Finite qualification trial composition (objective 004-a, evidence-contract corrections 004-b/004-c): `uv run
pytest tests/integration/test_qualification_composition.py -q` runs
the INSTALLED `raggedized qualification` CLI in subprocesses with the
real gateway/native adapters against owned 127.0.0.1 loopback servers
(synthetic canaries only): exact total calls across warmups/repetitions
for both dialects (native template work consumes the shared allowance:
the budget-3/budget-4 native boundaries), multiple repetitions under
ONE shared dispatch allowance (never reset per sample), retry
consumption of the allowance via failed connects at the real transport
boundary, global deadline exhaustion mid-trial (in-flight closure, no
replay, honest elapsed bound), accepted-then-closed unknown outcome
without replay, identity/settings preflight with ZERO dispatch
(model mismatch, workload-fingerprint mismatch, missing route,
unmaterialized direct, invalid spec, invalid `--output` destination),
the honest post-work export-stage failure after actual dispatches
(exit 3, full safe evidence on stdout with the spent-attempt ledger),
outcome/metric ambiguity (contradictory reported cache/input counters
stay raw facts only and cannot become positive evidence; missing usage
stays null), and the deterministic explicit synthetic route
(`--synthetic`: owned fixture, evidence labeled MOCK /
synthetic-owned-fixture, timing-stripped evidence identical across
runs, configured secrets never read, a configured loopback URL never
classified synthetic by a boolean), the bounded spec file input typed
refusals (absent spec, owned TEMP FIFO/special file refused WITHOUT
blocking, file past the 65536-byte bound, invalid UTF-8, JSON integer
beyond the fixed decoder bound and deep nesting — all pre-dispatch
with zero HTTP, fixed safe errors and no input or private-path echo),
the decoded workload Unicode admission (unpaired-surrogate parent /
lone-low-surrogate first suffix refused at spec admission with the
fixed safe reason — zero HTTP, no traceback, no input echo, matched
fingerprints proving the refusal is the Unicode admission; valid
escaped-astral and Slovenian Unicode admitted unchanged), and the
available-stage timing summaries (gateway prefill/TTFT stay
n=0 all-null unavailable; direct per-stage quartiles hand-computed
from the sample observations with known-zero/missing/invalid
bookkeeping). Unit contracts
(`tests/unit/test_qualification.py`) cover the strict spec refusals
(unknown settings, named-prerequisite refusals for unimplemented
context/pair/batch/precision/seed controls, bool-as-number,
nonfinite/negative/out-of-bounds values), the bounded spec file reader
(descriptor/type of the actually opened fd, byte/UTF-8/JSON typed
failures, fixed safe messages, no path echo, no process-global
decoder-limit change), the strict sample/result evidence contracts
(frozen extra=forbid fields, strict int/float/bool without coercion,
envelope relations: requests are the exact leading prefix of the
declared workload, remaining+attempted ==
budgets.max_dispatches, status/stop_reason consistency, not_run
implies zero dispatches, and the analysis section must equal the pure
recomputation from the recorded samples driven by the ACTUAL
transport-boundary ledger — an analysis call count that conflicts
with the ledger is refused), the 004-c cross-field bindings (envelope
backend vs declared backend; known per-sample backend fingerprint vs
the observed per-trial binding, an absent binding stays null and is
allowed; evidence class vs target type provenance pair; output
reservation total/per-sample vs the declared budget with the floor
even share over the DECLARED scheduled sample count; cache/input
consistency claims vs the pure derivation from the actually recorded
raw usage — every single-field contradiction refused, the unaltered
envelope admitted), the quartile completeness contract (n=0 iff
all-null quartiles; n>0 every quartile present, finite, non-negative
and ordered; partial quartile sets refused), the serialization-
boundary post-work refusal (fixed safe error with the actual valid
spent-attempt ledger on stdout, ledger availability marked honestly
when the ledger itself cannot validate — never assumed zero, no
crash, the invalid record never exported), the stage metric summaries
(known-zero counts, missing and invalid-observation exclusions,
per-stage provenance), preflight consistency, the nearest-rank
quantile convention and zero-sample nulls, the pure deterministic
analysis and the complete section 23.2 gate projection (all 14 IDs,
real trials NOT_RUN, committed
docs/benchmarks/qualification-gates.json bound to the canonical
rendering). Plan/gates/help are proven zero model/HTTP/telemetry I/O
on a closed port. All synthetic and offline: no external network,
product services, real keys, GPU or model downloads. Real
target/hardware/model qualification remains NOT RUN (order 004-a live
authorization: NONE; 004-b/004-c corrections, live authorization also
NONE).

T09. Bounded local resource telemetry (objective 004-d): `uv run
pytest tests/unit/test_qualification_resources.py -q` covers the strict
versioned observation DTOs (boolean-as-number, nonfinite, negative,
out-of-range and contradictory values refused; unknown fields
forbidden; absent stays null, known 0 kept; CPU interval deltas from
the baseline with disclosed utilization normalization, unavailable not
fabricated when the wall interval is missing/zero; RSS current vs
ru_maxrss lifetime high-water mark (Linux KiB unit documented) vs
observed interval sample peak; device-wide memory range checks; exact
unavailable/error reason vocabulary; phase events structurally
text-free; the series monotonic/peak/duration bindings; the wrapper
contract with the INTACT plain v1 trial inside), the own-process
probes through owned seams (getrusage//proc/self/status failures stay
unavailable, never zero; own PID scope), the bounded fixed-argv
nvidia-smi query against owned deterministic collector executables
(fixed argv, shell=False, exact MiB units, tool_absent vs
spawn_failed, no_devices, malformed, contradictory, nonzero-exit
query_failed with raw stderr canaries never kept, timeout with owned
child stopped, stdout/stderr byte exhaustion at the pipe boundary with
the byte cap + 1 recorded, invalid budget refusals) and the narrow
trusted observer (no work before the deadline bind, double-start
refusal, already-passed deadline samples nothing, phase facts
recorded then dropped after stop, CPU interval deltas, unavailable
probes stay null, sample cap and trial-deadline stop reasons, finite
idempotent cleanup, at most one bounded gpu query, construction-bound
refusals) plus the zero-telemetry negative (plan/gates/import never
touch the telemetry seams and create no sampler thread). `uv run
pytest tests/integration/test_qualification_resources.py -q` runs the
INSTALLED `raggedized` CLI in subprocesses: `resource diagnose`
(real own-process measurement on this Linux devhost, D0 bounded
allowance enforced before work, GPU absence as an exact honest
unavailable, output destination handling) and the owned deterministic
`nvidia-smi` executables on PATH (available exact units/values,
stdout byte exhaustion, actual child timeout without hang, raw output
never in the evidence), the `qualification run --resources`
composition over the real gateway/direct application code (plain v1
trial evidence byte-intact inside the explicit versioned wrapper;
phase/ordinal/ledger facts exactly with no text; collector accounting
separate from transport-boundary dispatches; --resource-gpu alone
refused pre-dispatch; preflight refusal binds no telemetry; slow
loopback HTTP under ONE shared short deadline with sampling stopped at
the deadline, finite cleanup and no replay; gpu observation composed
into the wrapper once, unavailable stays valid) and the
zero-telemetry import/help/gates/plan/doctor negative. All synthetic
and owned: no external network, product services, real keys, physical
GPU requirement, model downloads or sensitive corpus (order 004-d live
authorization: NONE; the D0 local observational allowance applies).

The 004-e correction regressions extend T09: unit — strict version
binding on both schemas (boolean, float, string and non-1 versions
refused) with the collector identity/code-source/package-version
bound and the explicitly unavailable Git revision; startup deadline
admission (an already-passed deadline queries nothing and samples
nothing; a slow owned startup fixture under a 0.08 s shared deadline
is clipped to the remaining allowance, records the exact
deadline-reached stop with zero samples and a valid section, and a
fast startup within the deadline admits samples); aggregate
admission and honest byte accounting (actual observed read bytes
charged, never the read cap; the reserved cap yields a valid honest
partial record at resource_exhausted; probes without real reads
charge zero bytes; pipe reads honor the remaining allowance with
the bounded one-byte EOF lookahead, including exact fit at the cap);
integration — the every-exit-path observer stop (in-process
KeyboardInterrupt after one real owned POST: the original exception
propagates, the caller survives, the owned sampler is stopped and
finitely joined with no continued samples) and the late-export
spent accounting over the canonical inner trial ledger (the wrapper
case reports the actual call count with the replay warning, the
genuine pre-dispatch refusal keeps its true zero claim, and a
missing/invalid ledger stays an explicit unknown, never an assumed
zero). Real target/model/GPU qualification remains NOT RUN.

T10. Supplied-value parity and gate projection (objective 004-f): the
four parity unit suites (embedding, rerank, shared safe file I/O,
CLI/gates) cover the pure supplied-value analyzers (digest/identity
binding; declared CPU-FP32 vs GPU-FP16 execution with identical
definition fingerprints; paired cosine/L2 deviation versus raw dot
ranking with deterministic ties; requested/effective k, gold
denominators, unavailable nulls; signed relative deltas; work limits;
input-free refusals), the shared bounded safe I/O layer (exact-byte
SHA-256/size; bounded UTF-8 JSON; underflow refusal keeping
representable subnormals/signed zero; NUL/symlink/non-regular and
changed-during-read refusals; advisory preflight; post-work ExportError
retaining evidence) and the canonical fourteen-gate projection
(committed docs/benchmarks/qualification-gates.json byte-equal to the
exact rendering; available analysis and partial instrumentation
distinct from full experiments; every real status NOT_RUN).
Integration suites run the INSTALLED `raggedized parity
embedding|rerank --input FILE --output FILE` (delegating to `python
-m slaif_raggedized_helper.qualification.parity_cli`) in subprocesses
on owned disposable files: exit 0 with input provenance plus
SUPPLIED_UNVERIFIED/NOT_RUN evidence, exit 2 pre-work refusals
(absent/invalid/oversize input, bad arguments, bad output
destination), exit 3 post-analysis export failure with bounded
computed evidence on stdout, help/import at zero work, zero
model/network/telemetry I/O, no redundant approval flag. All synthetic
and offline: no external network, product services, real keys, GPU or
model downloads. Supplied-value analysis is not execution; real
model/hardware/quality/vision/license qualification remains NOT RUN
(live authorization: NONE).
