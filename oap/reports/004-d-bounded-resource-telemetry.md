# OAP Coding Report — 004-d

Identifier: 004-d
Result: COMPLETE
Repository: ulfe-lmi/slaif-raggedized-helper
PR number: 6
Branch: oap/004-qualification-harness
Base branch: main
Implementation head SHA: a4f15333de8dfbde0508357d113e123a7f6775f5
Report publication commit: SELF

## Work and scope

Executed oap/orders/004-d-bounded-resource-telemetry.md (Status FINAL,
DHA Decision: NONE, live target authorization: NONE, PR mode
AMEND_EXISTING_PR, base commit 2bc320ff9e66c874f07da061218f2ff52e3420a9)
as the bounded resource-telemetry slice on the existing numeric
004/PR 6, building bounded read-only own-process local resource
telemetry (CPU/RSS plus at most one bounded local nvidia-smi metadata
query) and composing it with the actual finite repeated-parent trials,
preserving the accepted 004-c validation/deadline/accounting. Round
start reconciled against GitHub: unique PR 6 OPEN, original branch,
main base 2bc320ff9e66c874f07da061218f2ff52e3420a9, remote head
305d12056db6e388cddf2277c97efad55b031992 (the verified 004-c
report-only SELF with sole implementation parent
b35e82026343725d441708d57a9d5863373d8508 and exact remote
bytes/topology), local == remote, no auto-merge. The sole control OK
was consumed by the sole external wrapper and was never reread or
replayed; no waiter was created. All strategic round-start bytes were
committed byte-for-byte unchanged in the single implementation commit
a4f15333de8dfbde0508357d113e123a7f6775f5 (18 files, +3712/−28) on
branch oap/004-qualification-harness: oap/orders/004-d-bounded-
resource-telemetry.md, oap/reviews/004-c-review.json (SHA-256
a183aa6b9f8909f65e1169034c068d3d7db8b224ca180491119459664861fed6,
re-verified byte-identical before commit) and oap/active (exactly
`004-d\n`, 004-c -> 004-d). The previously qualified 582-byte ordinary
startup and the root-authored role/runbook docs are untouched. No
reset/clean/stash/force-push was used. Pushed 305d120..a4f1533.

The slice, as implemented:

- qualification/resources.py (new, pure stdlib, no new dependency):
  strict frozen extra=forbid pydantic DTOs with StrictInt/StrictFloat
  and no coercion — SampleObservation, CpuFacts, RssFacts, GpuDevice,
  GpuObservation, CollectorAccounting, PhaseEvent, ResourceSection
  (kind resource-telemetry, version 1) and ResourceDiagnostic (kind
  resource-diagnostic, version 1) — binding code/collector provenance,
  the actual own-process identity (ProcessScope: scope own-process +
  the actual caller pid), monotonic sample cadence within the finite
  duration, units and per-value availability; aggregate finite bounds
  (observation duration <= 86400 s matching TrialBudgets, 10000
  samples, 1000000 collection calls, 8 MiB collector bytes, 16 device
  queries, 8 devices, 128-char device name, 1024-char note, 8
  provenance entries, phase events <= warmups+repetitions); boolean-
  as-number, nonfinite, negative, extra-field and contradictory
  values are refused; absent stays null/unavailable, known 0 stays 0.
  Own-process probes: getrusage(RUSAGE_SELF) cumulative user/system
  captured at series start with disclosed per-interval deltas;
  /proc/self/status VmRSS (kB -> bytes, bounded 8 KiB read) as
  CURRENT sampled RSS; ru_maxrss as the process-lifetime high-water
  mark (documented Linux KIBOBYTES -> bytes; unavailable, not zero,
  where the platform unit is not the documented Linux one); the
  observed interval sample peak is distinct from both.
  run_gpu_metadata_query: the ONLY device query shape is the fixed
  whitelisted argv (nvidia-smi --query-gpu=index,name,memory.
  total,memory.used,memory.free --format=csv,noheader,nounits),
  shell=False, with the finite timeout AND the stdout/stderr byte
  bounds enforced AT THE PIPE BOUNDARY while the child produces data
  (cap+1 byte recorded, raw bytes never kept), and on timeout/oversize
  only the exact owned collector child is terminated/killed. Exact
  reason vocabulary: unavailable tool_absent/no_devices/
  query_budget_exhausted; error spawn_failed/timeout/
  stdout_oversize/stderr_oversize/query_failed/malformed_output/
  contradictory_values. TrialResourceObserver: construction starts NO
  work; start(deadline) binds the single actual trial deadline with a
  t=0 sample (an already-passed deadline yields zero samples, reason
  deadline_reached); at most ONE bounded metadata query at start when
  opted in; record_phase accepts facts only (phase/ordinal/
  attempted_calls/elapsed_seconds — never raw prompts/outputs/
  credentials, never arbitrary callbacks); stop() is idempotent with
  an explicit finite cleanup join (default 1 s, max 5 s); aggregate
  caps span every sample/query and are never reset per invocation.
  wrap_trial_with_resources/validate_resource_wrapper keep the plain
  v1 trial evidence BYTE-INTACT inside the explicit versioned wrapper
  {resource_wrapper: 1, trial, resources}, re-validating the inner
  trial with validate_trial_evidence and refusing version/key/
  tampering drift. run_resource_diagnostic enforces the D0 local
  observational allowance (up to 5 s / 64 samples per diagnosis; at
  most ONE optional real local nvidia-smi metadata query with
  timeout <= 1 s, stdout <= 16 KiB, stderr <= 4 KiB), refusing
  allowance violations pre-work with a typed USAGE_INVALID that names
  that no telemetry ran.
- runner.py: run_trial(config, spec, ..., resources_observer=None) —
  the optional observer is started only AFTER the BudgetedTransport is
  constructed (the one shared absolute trial deadline, already
  spanning all warmups/repetitions/retries/templates/model calls, is
  what it binds; no extension/reset), records one phase event per
  sample, is stopped after the loop, and the document is wrapped only
  AFTER validate_trial_evidence — so valid trial evidence and the
  spent-attempt ledger are preserved even when telemetry or export is
  unavailable.
- cli.py: new `raggedized resource diagnose [--duration-seconds]
  [--samples] [--gpu] [--output]` (bounded flags; real own-process
  measurement of THIS caller process on THIS devhost; GPU absence is
  an honest unavailable, never a zero; no config/credentials/
  network/model work) and `qualification run --resources
  [--resource-gpu]` (explicit opt-in only; --resource-gpu without
  --resources is refused pre-dispatch with typed exit 2 and zero HTTP;
  the wrapper is validated at the serialization boundary with the
  same honest exit-3 path, and the post-work contract error reads the
  spent ledger from the wrapper's trial member). import/help/plan/
  gates/doctor perform zero telemetry/model/network work.
- gates.py + docs/benchmarks/qualification-gates.json: V100-MEM-01/
  V100-MEM-02/RERANK-01 pending text now cites the 004-d bounded
  local resource telemetry (own-process/devhost scope only) alongside
  015/012 and authorized real GPU; all statuses remain NOT_RUN;
  projection regenerated from the code (bytes bound by a unit test).
- Tests: 138 new unit tests (tests/unit/test_qualification_resources.
  py) and 15 new integration tests (tests/integration/test_qualific-
  ation_resources.py: installed-CLI subprocesses, owned deterministic
  fake nvidia-smi executables, owned slow loopback HTTP server,
  synthetic route); every 004-a/004-b/004-c positive is preserved and
  zero tests were removed.
- Documentation: qualification-protocol.md new 004-d section,
  TESTING.md T09, STATUS.md, README.md, docs/UNCERTAINTIES.md,
  CONTEXT-BUDGET.md and MANIFEST.json (see Documentation impact).

## Acceptance evidence

Criterion 1 (strict finite versioned observations/series): the DTOs
are frozen, extra=forbid, strict-typed without coercion, and bind
collector/code source (code_version + collector provenance), the
actual available local identity (ProcessScope own-process + actual
pid), monotonic interval/cadence (elapsed ordering, sample-within-
duration, wall == duration, interval bound), units and per-value
availability. Sample/device/string/output and total collection
calls/time/bytes are bounded (10000 samples, 1000000 calls, 8 MiB
bytes, 16 queries, 8 devices, 128/1024-char notes/names, 8
provenance entries, phase events <= warmups+repetitions, 86400 s).
Boolean-as-number, nonfinite, negative and contradictory values are
refused (TestSampleObservationStrict, TestCpuFactsStrict including
total/utilization mismatch and one-side-unknown, TestRssFactsStrict,
TestGpuDeviceStrict including used>total/free>total/zero-total,
TestGpuObservationStrict status/reason bindings,
TestCollectorAndPhaseStrict samples<=calls + stop vocabulary,
TestSeriesSectionStrict non-monotonic/beyond-duration/peak-binding/
wall-duration/interval/scope/section bindings,
TestWrapperContract wrong-version/extra-missing/tampered-trial).
Absent stays unavailable/null while known 0 remains 0
(test_absent_stays_null_and_known_zero_kept, test_known_zero_kept,
TestRssFactsStrict). Local devhost measurements never establish the
remote inference host or an assigned production device/process/model:
ProcessScope is own-process with a fixed scope note, and the
coding-authored witness case W1-own-process-scope verifies the
diagnostic records a real caller pid (a child of the witness, != the
witness pid) on this devhost only.

Criterion 2 (actual own-process CPU/RSS, RSS kinds distinct):
user/system CPU time is measured from getrusage(RUSAGE_SELF) —
cumulative values captured at series start with per-interval deltas
(TestObserverLifecycle.test_cpu_interval_deltas_from_baseline); the
CPU/wall ratio is disclosed as a normalization note that may exceed
1.0 on multi-core and is null (unavailable), never fabricated, when
the interval wall time is missing or zero
(TestCpuFactsStrict.test_zero_wall_utilization_unavailable_not_
fabricated, test_utilization_may_exceed_one_and_is_disclosed).
Current sampled RSS comes from /proc/self/status VmRSS (kB -> bytes,
line format with/without unit covered); the process-lifetime high-
water mark is ru_maxrss with the documented Linux KIBOBYTES -> bytes
conversion and honest unavailable elsewhere (never zero)
(TestOwnProcessProbes.test_rss_from_status_bytes, test_rss_line_
without_unit, test_rss_unavailable_never_zero, test_lifetime_max_
linux_kibibytes, test_lifetime_max_negative_unavailable); the
observed interval sample peak is a distinct, bound field
(TestSeriesSectionStrict.test_sample_peak_binding_mismatch_refused,
test_sample_peak_without_known_values_refused). No unknown PID/
process inspection and no allocator attribution exist in the module
(probes touch only own-process interfaces). Real measurements were
taken on this devhost (witness W1-real-rss-measured: non-null
current and lifetime max; W1-cpu-interval-finite) and are labeled in
the diagnostic as measurements of this caller process on this
devhost, never embedding/reranker resource evidence; a standalone
trial client is not the remote model process (fixed scope note).

Criterion 3 (bounded nvidia-smi collection): the fixed whitelisted
argv is the only query shape — no argument, command or executable
path is selectable by config, spec JSON or caller strings
(TestGpuMetadataQuery.test_fixed_argv_never_selectable; the CLI
exposes no path/argv flags; tests inject only the owned trusted
seams gpu_executable/gpu_env and owned PATH fixtures). The query runs
with shell=False and enforces the finite timeout AND the actual
stdout/stderr byte bounds AT THE PIPE BOUNDARY while the child
produces data (cap+1 recorded, raw output never kept) — never after
unbounded capture (TestGpuMetadataQuery.test_stdout_oversize_kills_
owned_child, test_stderr_oversize, test_timeout_kills_owned_child;
installed-CLI TestFixedArgvGpuQueryViaCli.test_stdout_byte_
exhaustion_at_pipe_boundary asserts exactly 16*1024+1 bytes and that
the raw payload is absent from the evidence, and test_actual_child_
timeout asserts a bounded real child timeout with the child stopped).
On timeout/oversize only the exact owned collector child is
terminated/killed, never upstream models/services/drivers. Aggregate
caps span every warmup/repetition/phase/query and never reset per
invocation (CollectorAccounting.device_queries; the trial observer
runs at most ONE query per observer — TestObserverGpuQuery.
test_at_most_one_bounded_query; section-level 16-query bound).
Missing tool / no GPU / permission / malformed / timeout / oversize
produce exact unavailable/error evidence with devices == [] and a
fixed safe reason — never 0 used/full/free (witness
W1-gpu-absent-honest-unavailable: status unavailable, reason
tool_absent on this nvidia-smi-less devhost; W2-stdout-oversize:
error reason stdout_oversize, devices []). Raw stderr/command output
and private host metadata are never dumped (only byte counts and the
safe reason; TestGpuMetadataQuery.test_nonzero_exit_is_query_failed_
without_raw_stderr, test_malformed_output, test_contradictory_values).

Criterion 4 (device identity and memory, units, distinctions):
GpuDevice records the queried actual device_index (<= 255), an
opaque bounded device_name (<= 128 chars) and total/used/free memory
with the exact unit "mib" (nvidia-smi --format=csv,noheader,nounits
memory.* are MiB) plus range checks (total > 0, used <= total,
free <= total; TestGpuDeviceStrict, witness W2-available-exact-
mib-units with the owned fake returning exact 81920/1024/80000 MiB
values). Device-wide memory is distinct from per-process/CUDA
allocated/reserved and worker peaks: those remain unavailable until
actually instrumented by an owned worker, supplied worker
measurements are supplied-unverified, sampling does not prove
ownership/exclusivity, real model load, absence of contention/OOM or
a true worst-case peak, and no allocator zero is invented — all
recorded verbatim in the fixed GPU_NOTE attached to every
GpuObservation. No Torch import: the module is pure stdlib and the
qualification package imports no model/allocator stack.

Criterion 5 (phase order vs lifecycle, observed vs true peak):
PhaseEvent carries exactly {phase (warmup|measured), ordinal,
attempted_calls, elapsed_seconds} — caller stage declarations plus
the ledger fact, with non-ledger fields refused (TestCollectorAnd-
PhaseStrict.test_phase_event_rejects_non_ledger_fields,
TestObserverLifecycle.test_phase_events_recorded_then_dropped_after_
stop). The documentation and fixed provenance notes state that the
trial_start/warmup/measured observation order is distinct from actual
model service startup, physical cold/warm state and worker-lifecycle
events; beginning a trial against an already running service is not
cold model startup; stage tags are declarations until tied to owned
lifecycle evidence (015). The section reports the finite sampled
interval/counts/missing periods and the OBSERVED sample peak, with a
fixed note that peaks are observed sample peaks, never true
worst-case peaks. The ~2GiB architecture margin stays a declared
criterion: V100-MEM-01/02 and RERANK-01 remain NOT_RUN pending 015/
012 + this 004-d telemetry + authorized real GPU (gate projection
regenerated, bytes bound by a unit test).

Criterion 6 (composition with real trials, one deadline, separation):
the actual finite repeated-parent trials (synthetic owned fixture and
owned loopback HTTP) compose with the explicit optional bounded
observer: run_trial starts the observer only after the
BudgetedTransport — the ONE shared absolute trial deadline spanning
all warmups/repetitions/retries/templates/model calls is the same
object the observer binds, with no extension or reset. Constructing
an observer starts no work before binding the actual single trial
deadline (TestObserverLifecycle.test_construction_starts_no_work:
the monkeypatched probe is uncalled and no new thread exists after
construction); an already-passed deadline binds zero samples with
reason deadline_reached (test_deadline_already_passed_samples_
nothing). Collector activity accounting (samples/calls/bytes/
device_queries) is separate from actual model/template dispatches
(witness W3-collector-separate-from-dispatches: collector samples
>= 1 while transport attempted_calls == 3; TestCollectorAndPhase-
Strict). On finish/failure/cancellation new samples stop and the
owned collection closes/joins within the explicit finite cleanup
bound, never leaving a detached sampler (test_stop_idempotent,
test_trial_deadline_stops_sampling; the slow-HTTP witness case
W4-shared-deadline-stops-trial-and-sampling shows the trial
incomplete/budget_exhausted_deadline with attempted_calls == 1 and
NO replay, sampling stopped at the deadline, finite cleanup, and the
witness elapsed time bounded). Stop/kill applies only to the exact
owned collector child. The plain v1 trial evidence stays byte-intact
inside the explicit versioned wrapper (TestWrapperContract.
test_trial_member_is_byte_identical_v1_document,
test_tampered_inner_trial_refused; witness W3-plain-v1-intact-
inside-wrapper: the inner trial validates with
validate_trial_evidence and carries no resources/wrapper keys); the
document is wrapped only after validate_trial_evidence so a valid
trial and its spent ledger survive telemetry/export unavailability
(the wrapper is re-validated at the CLI serialization boundary with
the same honest exit-3 path; _post_work_contract_error reads the
ledger from the wrapper trial member). The narrow trusted loop
observer receives only phase/ordinal/deadline/ledger facts — never
raw prompts/outputs/credentials or JSON-selected callbacks.

Criterion 7 (zero-telemetry paths, opt-in, honest GPU absence):
import creates no sampler thread and plan/gates never touch the
telemetry seams (TestZeroTelemetryOnNonOptInPaths); installed-CLI
help/gates/plan/doctor perform zero telemetry/model/network work
(TestZeroTelemetryOnNonOptInCommands.test_help_gates_plan_doctor_
zero_telemetry; witness zero-telemetry-help/gates/plan assert the
telemetry kinds are absent from their output). Standalone sampling
and trial-with-resources require explicit opt-in through the
installed CLI and actual functions (resource diagnose;
qualification run --resources). Ordinary tests need no external
services, real keys, physical GPU or model downloads — they use
owned disposable CPU/loopback/fake-nvidia-smi fixtures only. Real
local CPU observations are labeled as measurements of this caller
process on this devhost (fixed scope note + CLI docstring +
witness). GPU absence on this nvidia-smi-less devhost is an honest
tool_absent diagnosis, never a V100 feasibility pass (witness
W1-gpu-absent-honest-unavailable; V100 gates NOT_RUN). Missing
model/worker/lifecycle paths retain the exact 007/012/015/019
prerequisites and all real gate statuses stay NOT_RUN (gates
projection + UNCERTAINTIES).

Criterion 8 (meaningful tests, preserved positives, CI/lint/
governance): 138 new unit + 15 new integration tests cover exact
units (mib exact values), absent/malformed/contradictory/nonfinite
telemetry, known-0-vs-unknown, actual child timeout/byte exhaustion/
no further queries (at-most-one per observer; D0 pre-work refusals),
finite cleanup/cancellation, phase/peak provenance, and sampling
under a shared short deadline during slow owned HTTP
(budget_exhausted_deadline, attempted_calls == 1, no replay). ALL
current input/DTO/stage/transport/retry/UNKNOWN/Unicode/ledger/
export positives and meaningful negatives are preserved: 452 unit
(314 baseline + 138 new) and 316 integration (301 baseline + 15 new)
= 768 product tests, all pass, zero tests removed (see
Verification). Product/OAP/lint/governance and implementation-head
CI pass with no skipped/missing green (Verification).

## Verification

Local, on the implementation commit (Python 3.14.4 venv, editable
CLI; synthetic and offline only, owned disposable 127.0.0.1 loopback
fixtures and owned deterministic fake nvidia-smi executables, zero
network/keys/GPU/model access):

- `ruff check src tests` — clean.
- `pytest tests/unit` — 452 passed (314 at 004-c + 138 new 004-d unit
  tests; zero removed); `pytest tests/integration` — 316 passed (the
  unchanged 301 004-a/b/c positives + 15 new 004-d installed-CLI
  tests, including the owned-loopback slow-HTTP shared-deadline case
  and the owned fake nvidia-smi pipe-boundary/timeout cases).
  Standard invocations are the per-directory ones used by CI; the
  two new files share a basename across the two directories (no
  __init__.py), which the per-directory convention avoids.
- `python3 -m unittest discover -s tests/oap` — 41 passed
  (governance scaffold, including verify_governance over the
  refreshed manifest).
- Coding-authored retained root witness
  /tmp/raggedized004-resource-telemetry-review.py (SHA-256
  c4b8875dd90c8182a92288c7f21fe63a785680360cf687933ae9e2c1b990e959,
  runs the INSTALLED raggedized CLI; this is coding-authored
  verification, not an independent strategic/root witness): 23/23
  checks PASS from actual output — real own-process measurement,
  D0 duration/sample caps refused pre-work ("no telemetry ran"),
  GPU absence honest tool_absent, exact MiB units/values via the
  owned fake smi, 16KiB+1 stdout byte exhaustion at the pipe
  boundary with the raw payload absent, bounded actual child
  timeout (~1.6 s against a 1 s budget, child stopped), wrapper with
  plain v1 intact and exact phase/ordinal/ledger facts (no text),
  collector accounting separate from transport dispatches, shared-
  deadline slow-HTTP stop (incomplete/budget_exhausted_deadline,
  attempted_calls == 1, no replay, finite cleanup), plain run
  without opt-in staying plain v1, --resource-gpu-alone and
  preflight refusals pre-dispatch with no telemetry, and zero
  telemetry on help/gates/plan.
- `python3 oap/bin/check_state.py --repo-root .` — exit 0: state
  ACTIVE, active 004-d, order resolved, report absent pre-
  publication, governance verified (all manifest file hashes
  re-verified against disk after the authorized refresh;
  activation-vs-current-governance reported informational only —
  an authorized candidate governance change may differ from
  activation, as in 004-c).
- Implementation-head CI: push a4f15333de8dfbde0508357d113e123a7f6775f5
  to origin/oap/004-qualification-harness (305d120..a4f1533) — CI
  run 42878145680 (pull_request) all five jobs SUCCESS (OAP tests
  3.12/3.13/3.14; Product tests 3.12/3.14), observed after push and
  before this report was written.
- Mock/live distinction: every executed path above is synthetic/
  offline or owned disposable loopback/fake-GPU fixtures. The devhost
  has no nvidia-smi, so the real GPU path was exercised only through
  the owned deterministic fake executables and the honest
  tool_absent diagnosis; no physical GPU, model download, real key,
  live target or corpus was touched. Live target authorization is
  NONE; ALL real qualification trials remain NOT_RUN.
- No claim is made about this report's future push/CI; a separate
  post-publication receipt verifies it.

## Documentation impact

- docs/benchmarks/qualification-protocol.md: new 004-d section with
  the exact opt-in commands (resource diagnose; qualification run
  --resources/--resource-gpu), the versioned wrapper contract and
  plain-v1-intact rule, the finite budgets/units/availability
  semantics (own-process CPU/RSS kinds, ru_maxrss Linux KiB note,
  disclosed utilization normalization, MiB device units, exact
  unavailable/error vocabulary), the sampler scope (own-process,
  trusted loop observer, facts only, finite cleanup bound), the
  observed-peak-versus-true-peak limitation, the phase/lifecycle
  provenance boundary (declarations, not owned lifecycle evidence;
  015), the D0 local observational allowance and its library-max
  distinction, and the real-local-CPU-vs-MOCK/GPU-absent/supplied-
  unverified distinctions.
- TESTING.md T09 (14208 UTF-8 bytes): the 004-d coverage (DTO
  strictness, own-process probes, bounded fixed-argv GPU query,
  observer lifecycle, diagnostic D0 bounds, wrapper contract,
  installed-CLI composition, zero-telemetry paths) and the
  live-authorization NONE statement.
- STATUS.md: current-state line and the 004-d history block with the
  telemetry slice, the preserved positives and the NOT_RUN real-gate
  status.
- docs/UNCERTAINTIES.md: new 004-d observation updating U03/U04/U08
  to the actual bounded telemetry (own-process/devhost scope only,
  honest GPU absence) and recording the narrow U10 startup-scope
  evidence from the final 004-c review while preserving the failed
  goal-first history as RECORDED FAILED (never relabeled passed).
- README.md: PR #6 summary now names the 004-d bounded resource
  telemetry composition.
- oap/governance/CONTEXT-BUDGET.md + oap/governance/MANIFEST.json:
  routine governance refreshed from the final actual files (routine
  total 43569 -> 46759 UTF-8 bytes, ceiling 50000; TESTING.md
  11018 -> 14208; manifest file hashes updated for TESTING.md
  (8ca482c2c32adaf9365308f7d6154b2849080ae6b7523c79958f532f12a92960)
  and CONTEXT-BUDGET.md
  (042a427cef006a9dc692201a00759ba1600ef8d78e58bce177eaca3e132b162b);
  every manifest hash re-verified against disk). Exact model tokens
  and client injection remain UNMEASURED.
- docs/benchmarks/qualification-gates.json: regenerated from the
  code with the 004-d telemetry cited in the V100-MEM-01/V100-MEM-
  02/RERANK-01 pending text (all NOT_RUN); bytes bound by a unit
  test.
- The root-authored startup docs and prompt are committed
  byte-unchanged as ordered.

## DHA and boundaries

Decision: NONE — no CRITICAL append was ordered or made; the register
is unchanged (critical state empty per check_state). No merge was
performed, no auto-merge enabled, no release/tag/deploy, no next-
work selection, no model/provider/profile change, no nested/helper
agents, no new consumer or waiter; the control FIFO was never reread.
Preserved: the immutable 004-a/004-b/004-c reports, orders and the
final 004-c review (byte-unchanged, SHA-256 verified before commit),
the strategic round-start activation/order/active bytes, the three
root-authored startup-governance bytes, agent homes, private FIFOs,
source originals and unrelated worktrees. No live target/model/GPU/
corpus work (live authorization NONE); no secrets, real corpus/
prompts, private URLs, credentials or real unique host/device
metadata in any commit or this report (GPU identity examples are
synthetic fixture values only).

## Limitations and remaining work

- This telemetry proves bounded, honest OWN-PROCESS measurement on
  this devhost and correct composition with the finite trials; it
  does not establish the remote inference host, an assigned
  production device/process/model, ownership/exclusivity, real model
  load, absence of contention/OOM or any true worst-case peak, and a
  local resource observation is not actual target/model
  qualification.
- This devhost has no nvidia-smi: the real GPU path is exercised
  only through owned deterministic fakes plus the honest
  tool_absent diagnosis; per-process/CUDA allocated/reserved and
  worker peaks remain unavailable until an owned worker instruments
  them.
- No live qualification: real gateway/GPU/model/corpus inputs remain
  absent (authorization NONE); ALL real trials remain NOT_RUN;
  019/ICA/MVP gate actual A1/hardware/quality feasibility.
- Vector/rank parity and full named gate composition remain required
  in later proof-sized 004 continuations (strategic activation
  required) before any whole-004 acceptance; this slice alone is not
  whole-004 acceptance, and no merge/005 authority is claimed.
  LICENSE-01 (certifi MPL-2.0 exception) remains open.
- U10 stays OPEN with the failed goal-first history preserved; exact
  model token counts and client injection overhead remain
  UNMEASURED.
