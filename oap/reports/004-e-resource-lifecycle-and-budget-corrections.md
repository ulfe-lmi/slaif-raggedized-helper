# OAP Coding Report — 004-e

Identifier: 004-e
Result: COMPLETE
Repository: ulfe-lmi/slaif-raggedized-helper
PR number: 6
Branch: oap/004-qualification-harness
Base branch: main
Implementation head SHA: 651635c22e76fef11adbe3f440cf4c5593dfefb0
Report publication commit: SELF

## Work and scope

Executed oap/orders/004-e-resource-lifecycle-and-budget-corrections.md
(Status FINAL, DHA Decision: NONE, live target authorization: NONE, PR
mode AMEND_EXISTING_PR, base commit 2bc320ff9e66c874f07da061218f2ff52e3420a9)
on the existing PR 6, correcting the five independently reproduced 004-d
resource lifecycle, deadline, aggregate accounting, late-export and
resource contract failures recorded in oap/reviews/004-d-review.json
(SHA-256 5a8d4dff6a259dc689cf056071091960501ba1ae321a0b3285b611230bf19e10,
committed byte-unchanged) on the verified 004-d report head
57426f5ce76a27601c20512532723e5187895456 (sole implementation parent
a4f15333de8dfbde0508357d113e123a7f6775f5). Round start reconciled against
GitHub: unique PR 6 OPEN, head oap/004-qualification-harness at 57426f5,
base main 2bc320ff9e66c874f07da061218f2ff52e3420a9, local == remote, no
auto-merge. The sole control OK was consumed by the sole external wrapper
and was never reread or replayed.

Commits pushed on the branch before this report, in order:

1. 8e417696faf2d6152aed1a08a4370fdc7938e85f (parent 57426f5) — F01-F05
implementation plus tests and documentation: F01 shared absolute deadline
admission (single startup nvidia-smi metadata query clipped to the
remaining trial AND observer duration; standalone diagnostic keeps its own
documented D0 bound; already-passed deadline queries nothing, samples
nothing, starts no sampler; admission rechecked after the startup query
and before every sample/query); F02 honest aggregate and pipe-boundary
accounting (pipe reads request at most the remaining declared allowance
plus an explicit bounded one-byte lookahead at the cap; bytes_read is the
sum of ACTUAL observed bytes; aggregate collection calls/bytes/time
enforced before work across the whole observer lifetime; new stop reason
resource_exhausted with a valid honest partial record; startup t=0 and the
final observation count in the documented collection-call allowance); F03
run_trial stops and finitely joins the owned observer on every execution
exit path; F04 late --output failures use the canonical inner trial ledger
(actual known call count plus replay warning; explicit unknown, never
assumed zero; only genuine pre-dispatch refusal documents keep the true
zero-dispatch claim); F05 strict integer-1 mode="before" version
validators and CollectorAccounting binding of collector_id,
collector_source, code_version (actual executing package version) and
source_revision explicitly 'unavailable', disclosed in provenance/notes.

2. df4a42323989e263270df5693f5856ddb97f0463 (parent 8e41769) — in-round
CI repair after run 42892290416 failed Product tests (Python 3.12) in
exactly two new unit tests: the tests replaced os.read globally, so the
spy also intercepted CPython subprocess internals (Popen._execute_child
errpipe reads requesting 50000 bytes), tripping the requested <= 128
assertion while the actual totals (129/128) were still correct. The fix
added the narrow owned collector seam _collector_read in resources.py
(the read loop reads the owned child stdout/stderr through it) and
scoped the two test spies to that seam via monkeypatch; no behavior,
bound or assertion was relaxed.

3. 651635c22e76fef11adbe3f440cf4c5593dfefb0 — the authorized local
integration merge (--no-ff) of the root-approved parallel candidate tip
59c184d05d40b67cd5b10d2d94977e44e11e6c90, per integration-approved.json
decision ACCEPT_LOCAL_CANDIDATE_FOR_CANONICAL_INTEGRATION recorded
2026-11-10T21:28:50.432508+00:00 under the explicit human parallel
mandate; strategic review
/home/janezp/codex-supervision/slaif-raggedized-helper/parallel/
resource-fix-e-b/review.json SHA-256
0c168790e9111fb69f11cd33f2e0016e1579f6b4b48a5741a9720eee2cfe4ea5
(re-verified byte-identical before the merge); expected canonical head
df4a42323989e263270df5693f5856ddb97f0463 re-verified (clean worktree,
exact branch/head); candidate branch oap/parallel-004-resource-fix-e
forked exactly at df4a42323989e263270df5693f5856ddb97f0463. The merged
history preserves candidate provenance (oap/parallel orders and reports
for both lanes, docs/parallel/resource-e-corrections.md):
   - f506095ed5eb05a3f641b699c20b50bfbe371f19 +
     a481ac47b2f4e748c7e6ca7316555f8d03b96c00 (lane resource-fix-e-a,
     PAR-004-RESOURCE-E-A): closes the independently audited 004E-A01
     standalone-diagnostic interruption (owned observer stopped and
     finitely joined on normal, error and interruption exits), 004E-A02
     startup device query clipping to the observer duration as well as
     the trial deadline with no late sample, and 004E-A03 no post-expiry
     collection, a single lifetime collection-call allowance covering
     baseline CPU, device query, samples and the final observation, and
     the combined self+device aggregate byte pool with conservative
     reservations (a sample reserves the full status-read cap; a device
     query reserves both pipe caps plus one lookahead byte per pipe);
     a refused final observation leaves CPU delta and lifetime RSS
     unavailable rather than inventing zero; device cleanup waits at
     most 0.5 s each for terminate and kill.
   - 20c00cc3547e42b97b68651c72c9106e6a02b75f +
     59c184d05d40b67cd5b10d2d94977e44e11e6c90 (lane resource-fix-e-b,
     PAR-004-RESOURCE-E-B): separates the bounded observation window
     (ResourceSeries.duration_seconds: start to admitted CPU endpoint or
     report assembly, intersected with the observer-duration and
     optional trial-deadline work window) from actual collector
     completion elapsed (CollectorAccounting.wall_seconds, which may
     exceed the work window); a final CPU probe crossing expiry keeps
     its measured endpoint and the subsequent lifetime-RSS probe is not
     started after cutoff; the supported-max fake-clock finalize at
     86400.1 under MAX 86400 now yields a valid resource section.
This local integration merge is authorized by the human parallel request;
it is NOT a GitHub PR/default-main merge. No reset/clean/stash/force-push
was used. Pushed 57426f5..8e41769..df4a423..651635c. The strategic
round-start bytes are committed byte-for-byte unchanged (the order, the
review at the SHA-256 above, oap/active exactly `004-e\n` from 004-d) and
the root-authored startup/role/runbook sources are untouched.

## Acceptance evidence

Numbered against the 004-d review criterion status (1-8), with the F01-F05
corrections and the audited A01/A02/A03 plus lane-B window corrections.

1. Strict finite versioned observations, source binding and aggregate
caps (F05, F02; review criterion 1): ResourceSection and ResourceDiagnostic
versions are exact integer 1 via before-validators — booleans, floats and
strings refused on both schemas; CollectorAccounting binds
collector_id (fixed safe token), collector_source (the code module),
code_version (actual executing package version 0.1.0) and
source_revision explicitly 'unavailable' (no attestation/signing system,
no Git subprocess on import or default commands), disclosed in
provenance/notes; aggregate collection call and byte budgets are enforced
BEFORE work across the whole observer lifetime, now including baseline
CPU, the device query and the final observation in a single lifetime call
allowance, with stop reason resource_exhausted and a valid honest partial
record. Proof: new unit negatives; source-binding witness (both schemas
refuse boolean versions; collector source fields present; notes mention
code_version); audit witness call_exhaustion (limit 1: reported 1 call,
resource_exhausted, section valid); process witness (synthetic 1100-sample
section valid, actual 0 bytes).

2. Own-process interval, RSS and availability facts (review criterion 2):
actual own CPU interval deltas from a disclosed baseline, current RSS from
/proc/self/status, Linux ru_maxrss lifetime high-water, exact units,
unavailable (never zero) where missing; a final observation refused by
time or budget leaves CPU delta and lifetime RSS unavailable rather than
inventing zero (lane A). Proof: unit positives preserved; audit witness
expired_before_start (zero collector probes, 0 collection calls,
deadline_reached).

3. Bounded owned device query with actual pipe accounting and combined
byte admission (F01/F02, A02/A03; review criterion 3): fixed whitelisted
argv, shell=False, owned child, finite timeout; the startup device query
is clipped to the EARLIER of the remaining trial deadline and observer
duration (trials) or the observer duration (standalone diagnostics), with
post-query expiry checks no longer conditional on a non-None trial
deadline; pipe reads request at most the remaining allowance plus the
bounded one-byte lookahead at the cap and report the ACTUAL observed
bytes; bytes_read (own-process) and device_query_bytes_read (device pipe)
are non-overlapping actual counts whose sum is admitted against
MAX_COLLECTOR_BYTES, with conservative reservations (full status-read cap
per sample; both pipe caps plus one lookahead byte per pipe per device
query) — reservations are never reported as actual reads. Proof: unit pipe
tests (cap 128 flood: stdout_oversize, reported 129, sum(actual)==129,
every request <= 128, last request == 1; exact-128 stream: malformed,
reported 128, (1,0) EOF lookahead); read-accounting witness (128+1 = 129
reported); audit witness standalone_startup_duration (0.05 s duration,
0.6 s timeout, slow child: elapsed 0.0519 s, no sample, duration_reached,
gpu error) and device_aggregate_bytes (32-byte cap, 16-byte sample
reservation, 31-byte device output: refused, 0 actual bytes);
combined-byte-corrected witness (32-byte cap: conservative full-pipe
reservation refuses both device query and sample, 0 actual bytes).

4. Bounded device-wide metadata, units and ranges (review criterion 4):
exact MiB total/used/free, device identity, range checks, exact reason
vocabulary (tool_absent/no_gpus/permission_denied/malformed_output/
timeout/stdout_oversize/stderr_oversize/nonzero_exit), raw output never
kept; device-wide memory stays distinct from per-process/CUDA
allocated/reserved/worker peaks which remain unavailable; cleanup bounded
(0.5 s max per terminate and kill, lane A). Proof: process witness (exact
MiB 100/25/75 via owned fake nvidia-smi; devhost GPU absence an honest
tool_absent; silent-child timeout ~0.08 s; no further queries after
oversize); coding witness W2 (actual child timeout bounded, query clipped
to the remaining window, no device data).

5. Phase declaration, observed peak, lifecycle and observation-window
semantics (F02, lane B; review criterion 5): one phase event per sample
with facts only; startup t=0 and the single final observation count in
the documented collection-call allowance; ResourceSeries.duration_seconds
is the observation window (start to admitted CPU endpoint, otherwise
report assembly, intersected with the work window) and does NOT
represent cleanup elapsed; CollectorAccounting.wall_seconds is actual
elapsed through report assembly and may exceed the work window; CPU
wall_seconds is the actual CPU endpoint elapsed when observed (possibly
beyond the window) with the subsequent lifetime-RSS probe omitted after
cutoff; sample offsets preserved; the supported-max fake-clock finalize
(86400.1 vs MAX 86400) no longer emits invalid resource JSON. Proof: unit
regressions (fake-clock max window 86400.0 with deadline_reached and a
valid section; late report assembly; post-CPU-cutoff check; sample
offsets preserved); max-duration witness (86400.0 window, deadline_
reached, resource_section_valid true); coding witness W3/W5 series.

6. Shared deadline, every-exit-path cleanup and honest late export
(F01/F03/F04, A01; review criterion 6, previously FAIL): the 0.08 s
shared-deadline case stops at ~0.081 s with zero samples and the exact
deadline_reached reason (no late first sample, no t=0 mislabel);
run_trial finally stops and finitely joins the owned observer on every
execution exit path (normal return, pre-dispatch refusal, post-work
contract failure, in-process KeyboardInterrupt/any BaseException with a
surviving caller), preserving the original exception and the trial's
deadline/call/output semantics; standalone diagnostics stop and join the
owned observer in a finally on normal, error and interruption exits
(A01); late --output failures read the canonical inner trial ledger:
actual known call count with the replay warning, explicit unknown for a
missing/invalid ledger, and only genuine pre-dispatch refusal documents
keep the true zero-dispatch claim. Proof: unit regressions (owned-loopback
slow-HTTP stop, budget_exhausted_deadline, attempted_calls intact, no
replay; in-process KeyboardInterrupt regression); integration witness
(two actual owned-loopback POSTs, exit 3, full wrapper on stdout, inner
ledger attempted_calls 2, replay warning, false_zero_call_claim false;
cancellation after owned reply: exception propagated, sampler stopped,
thread dead, samples stable 2->2); audit witness diagnostic_interrupt
(state stopped, thread dead, samples stable 3->3).

7. Explicit opt-in, default no-telemetry (review criterion 7): import/
help/plan/gates/doctor perform zero telemetry/model/network work;
--resource-gpu alone refused pre-dispatch with typed exit 2 and zero
HTTP; the plain trial v1 document stays byte-intact inside the explicit
versioned wrapper. Proof: preserved 004-d/004-e unit and integration
positives; coding witness W1/W7 zero-telemetry and wrapper-shape checks.

8. Automated suites and independent negatives (review criterion 8):
802 product tests (484 unit = 452 baseline + 21 new 004-e + 11 parallel
candidate; 318 integration = 316 baseline + 2 new 004-e; zero tests
removed) plus 41 OAP scaffold tests all pass locally and on
implementation-head CI; the four retained independent strategic witnesses
(byte-identical to the review oracles) rerun unchanged demonstrate the
corrected behaviors; the three audit witnesses
(/tmp/raggedized-audit004e-extra.py,
/tmp/raggedized-004e-combined-byte-corrected-review.py,
/tmp/raggedized-004e-max-duration-review.py) pass on the integrated head;
the coding-authored retained witness passes 23/23 after one stale
elapsed floor was updated to the corrected clipping contract (documented
in the witness; see Limitations).

## Verification

Local evidence on Python 3.14 (uv run --isolated --locked --python 3.14),
on implementation head 651635c22e76fef11adbe3f440cf4c5593dfefb0:

- ruff check src tests/unit tests/integration: all checks passed.
- python -m compileall -q src tests/unit tests/integration: clean.
- pytest tests/unit -q: 484 passed (452 baseline + 21 new 004-e + 11
  parallel candidate; zero removed).
- pytest tests/integration -q: 318 passed (316 baseline + 2 new 004-e).
- Product total: 802.
- python3 -m unittest discover -s tests/oap: OK (41 scaffold tests).
- oap.py check (check_state): exit 0, active 004-e, declared context
  budget 48206/50000 bytes unchanged.
- Witnesses, on the integrated head: process (exact MiB 100/25/75, 129
  actual cap+lookahead bytes, ~0.081 s shared-deadline stop with zero
  samples, synthetic 1100-sample valid section), integration (two owned
  loopback POSTs, correct wrapped ledger, late-export replay warning,
  surviving caller with stopped sampler), read-accounting (128+1 = 129
  reported), source-binding (boolean versions refused, collector source
  fields present), audit-extra (interrupt stopped 3->3; expired start
  zero probes; 0.05 s standalone slow query ~0.052 s with no sample;
  call limit 1 reported 1; 32-byte device aggregate refused with 0
  actual bytes), combined-byte-corrected (conservative reservation
  refuses both, 0 actual bytes), max-duration (86400.0 window,
  deadline_reached, valid section). The coding-authored retained
  /tmp/raggedized004-resource-telemetry-review.py: 23/23.
- Implementation-head CI: run 42909169894 on
  651635c22e76fef11adbe3f440cf4c5593dfefb0 — all five jobs SUCCESS
  (OAP tests 3.12/3.13/3.14; Product tests 3.12/3.14), observed before
  this report. Superseded runs: 42892290416 on 8e41769 failed Product
  tests (Python 3.12) in exactly two new unit tests (global os.read spy
  intercepted CPython subprocess internals); repaired in df4a423 by
  scoping the spies to the owned collector seam with no bound relaxed.
- Parallel-lane provenance: candidate worktree
  /home/janezp/codex-work/slaif-raggedized-helper-parallel-resource-fix-e,
  branch oap/parallel-004-resource-fix-e, lane reports
  oap/parallel/reports/PAR-004-RESOURCE-E-A.json and
  PAR-004-RESOURCE-E-B.json and docs/parallel/resource-e-corrections.md
  committed with the integration.
- Mock/live distinction: synthetic/offline only — owned disposable
  fixtures (owned fake nvidia-smi executables, owned loopback HTTP
  servers), fake clocks in the max-duration case; devhost is
  nvidia-smi-less so GPU absence is an honest tool_absent diagnosis,
  never a V100 feasibility pass; live target authorization NONE; all
  real trials NOT_RUN; no real unique host/device metadata or secrets in
  any committed file.
- No claim about this report's future push/CI; a separate post-publication
  receipt verifies it.

## Documentation impact

- 8e41769: docs/benchmarks/qualification-protocol.md new 004-e correction
  section (exact deadline/cleanup and aggregate accounting semantics,
  truthful partial availability and byte units, actual-caller versus
  remote-model scope, valid inner-ledger handling); TESTING.md T09;
  STATUS.md (prior failure and correction recorded); README.md;
  docs/UNCERTAINTIES.md (004-e observations supersede the 004-d
  over-claims without rewriting the immutable 004-d report);
  oap/governance/CONTEXT-BUDGET.md routine 48206/50000 bytes;
  oap/governance/MANIFEST.json hashes updated for TESTING.md and
  CONTEXT-BUDGET.md with every manifest entry re-verified against disk.
- df4a423: no documentation change (the seam is a module-private
  internal; all documented behavior and guarantees unchanged).
- 651635c: candidate-provenance documentation added —
  docs/parallel/resource-e-corrections.md (observer correction semantics
  including the observation-window versus completion-elapsed split) and
  oap/parallel lane orders/reports; canonical product docs otherwise
  unchanged; CONTEXT-BUDGET.md and MANIFEST.json unchanged (declared
  48206/50000 bytes, re-verified by check_state exit 0).

## DHA and boundaries

- DHA Decision: NONE (per the order). No CRITICAL append; the critical
  table is empty (check_state critical {} on the integrated head).
- Strategic round-start bytes preserved byte-for-byte: the order,
  oap/reviews/004-d-review.json (SHA-256
  5a8d4dff6a259dc689cf056071091960501ba1ae321a0b3285b611230bf19e10,
  re-verified) and oap/active exactly `004-e\n`; the immutable 004-d
  report commit 57426f5ce76a27601c20512532723e5187895456 is unchanged.
- Parallel mandate: the human-authorized, Root-reviewed LOCAL candidate
  integration only — integration-approved.json
  ACCEPT_LOCAL_CANDIDATE_FOR_CANONICAL_INTEGRATION (recorded
  2026-11-10T21:28:50.432508+00:00), strategic review SHA-256
  0c168790e9111fb69f11cd33f2e0016e1579f6b4b48a5741a9720eee2cfe4ea5
  verified byte-identical, expected canonical head re-verified, and ONLY
  the reviewed local tip 59c184d05d40b67cd5b10d2d94977e44e11e6c90 merged
  with --no-ff inside the existing PR branch, preserving candidate
  implementation/report provenance. It is NOT a GitHub PR/default-main
  merge; no release or deployment.
- No merge of PR 6 to main performed (PR 6 remains OPEN, no auto-merge);
  no next work chosen; no live target/model/GPU/corpus work (live
  authorization NONE, all real trials NOT_RUN, LICENSE-01 open); no
  model/profile/auth/runtime-policy change; no secrets in Git.

## Limitations and remaining work

- In-round CI failure, honestly recorded: the first implementation head
  8e41769 failed CI run 42892290416 in Product tests (Python 3.12) only —
  two new unit tests replaced os.read globally so the spy intercepted
  CPython subprocess internals (Popen._execute_child errpipe reads of
  50000 bytes). Repaired in-round in df4a423 by scoping the spies to the
  owned collector read seam; no bound was relaxed; the repaired head's
  CI was all five SUCCESS.
- Independent audit (lane AUDIT-004E-IMPL-A, CHANGES_REQUIRED on the
  frozen 8e41769 head) reproduced three unresolved E-criteria gaps —
  004E-A01 (standalone diagnostic interruption left the owned sampler
  running), 004E-A02 (start(None) startup query not clipped to the
  observer duration, admitting a late sample) and 004E-A03 (post-expiry
  final probes still charged; baseline/device-query calls bypassed the
  call allowance; device bytes outside the aggregate byte pool). All
  three were closed by the root-approved parallel lane A integrated in
  651635c, and lane B additionally closed the supported-max fake-clock
  case where finalize at 86400.1 under MAX 86400 previously produced
  invalid resource JSON; the audited witnesses now demonstrate the
  corrected behaviors on the integrated head.
- The coding-authored retained witness W2-actual-child-timeout-bounded
  carried a 0.9 s elapsed floor that encoded the pre-A02 unclipped 1 s
  startup query. After integration it was updated (with an explanatory
  comment in the witness) to assert the corrected clipping contract:
  device_query_wall_seconds < 0.5 for the 0.2 s duration case with the
  bounded-above guarantee retained; the witness passes 23/23. The four
  strategic witnesses remain byte-identical to the review oracles and
  were rerun unchanged.
- One local integration run early in the round observed 3 transient
  environment-dependent skips that did not recur (318/318 on rerun; both
  CI Product jobs fully green on the integrated head).
- This round is a correction slice, not whole-004 acceptance: no
  vector/rank parity, no full named gate composition (all 14 gates), no
  real gate pass; 019/ICA/MVP and LICENSE-01 remain open; 004
  continuations/005 selection, report-head CI/acceptance and any
  qualifying protected PR merge remain strategy alone. No merge
  performed.
