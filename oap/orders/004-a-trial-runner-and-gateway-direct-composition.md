# OAP Work Order — 004-a

Status: FINAL
Identifier: 004-a
PR mode: CREATE_NEW_PR
Branch: oap/004-qualification-harness
Base commit: 2bc320ff9e66c874f07da061218f2ff52e3420a9
PR number: NEW
Expected active: 003-j
Provenance: H activated architecture-MVP program; A architecture §§5,19,23 / UPDATE A1; E inventory CPU-only and missing authorized targets; E actual003 probe interfaces and bounded-goal operational recovery
Architecture SHA256: 4b41905396a3838269fd6cf372614cd23cb2c3b6a37be09f29ed752803c0983a
Governance SHA256: 8d495656ed65746b15bfe33b6c7d703a254737a200e9d3629de8b45c05ecc85f

## Objective

Implement one finite qualification trial runner, strict sample/specification contracts and
actual gateway/direct repeated-parent composition. Deliver executable software, not a JSON
approval wrapper. This is the first proof-sized slice of objective004, one PR. A subsequent
strategically activated004-b adds resource telemetry, parity analysis and full gate composition;
no whole004 acceptance/merge or005 selection is delegated to coding here.

Explicit D0 replan: authorized real gateway/GPU/model/corpus inputs remain absent. Objective004
will establish usable instrumentation and exact prerequisites; actual A1/hardware/quality
feasibility remains UNPROVEN, mandatory at019/ICA/MVP. After the whole replanned004 software
scope is accepted/merged, independent005+ software may proceed. Do not alter human hardware,
quality, source, licensing or full text+visual requirements to fit this host.

## Dependencies and current state

PR5 MERGED2026-11-10T12:43:00Z, main2bc320ff9e66c874f07da061218f2ff52e3420a9. Accepted
003-j report headb2ca2e873354e7526019db471ee41928ca7ae9a4 has sole implementation parent
16fcbcb34fb2075747df7007f3648eac4846916d. Accepted/main tree matches
b5c67871c64601385fcb7bc4d175deacafd7a316. ReportCI42815749057 and mainCI42818124023
all5SUCCESS. Baseline442product=171unit+271integration, separate41OAP.

Coding worktree remains003 branch atb2ca (same accepted tree); strategy did not switch/reset.
Preserve strategic untracked003 reviews below and004 activation. Coding owns safe new branch
creation from verified main and commits these files unchanged; no reset/clean/stash/forcepush.
No other OAP objective PR is open. Prior response consumed; never reread003 responseFIFO.

Bounded read set: normal compact governance; this order; current probes.py, CLI/model-client
composition and their focused tests; config/schema/qualification contracts as used. Consult
ARCHITECTURE.md §§23.1–23.3 for experiment definitions, §§5.2–5.4/19 only if needed for
profile/resource semantics. No routine full source books, future orders or helper internals.
Measure actual task-specific governance/read bytes without inventing token counts.

Existing public API: probes.run_repeated_parent_probe(config, mode, ProbeBudgets(...)) returns
(exit_code,evidence); budget fields deadline_seconds, max_dispatches, max_output_tokens_total.
inner_transport is a test seam, not a production endpoint override. Reuse real configured
credential/endpoint/purpose/capability gates; narrowly extend a trusted shared-budget seam if
needed rather than duplicating HTTP clients. Fixed parent/suffixA/B are synthetic workloads.
Complete/exit0 is execution status and may contain failed/unknown phases, never qualification.

## Allowed paths and scope

Focused src/slaif_raggedized_helper/qualification/ (or evaluation/) contracts/runner/analysis;
CLI explicit qualification subcommands; minimal probes/model_clients/schema/config changes
needed for shared budget composition; tests/unit and tests/integration; small synthetic
non-deployable examples; docs/benchmarks/qualification-protocol.md and current machine-readable
gate evidence; STATUS, README, TESTING, UNCERTAINTIES and focused qualification docs. No new
runtime dependency is expected; explain any unavoidable dependency before changing its lock.

Commit exact strategic files oap/reviews/003-j-review.json (SHA256
6fb27044b3f6476bae8fd080544f0afc50ca4df2a7d1241fcc82f63451ed1c3f) and
003-resolution.json (SHA25600548c41f27923bbf5981f8e6903eba3309df3277f98dc8defe63ddf2673fe88),
plus unchanged004 order/active. Existing orders/reports/source originals/architecture immutable.

One narrowly authorized operational correction: replace oap/prompts/coding-startup.txt with
exact bytes from /home/janezp/codex-supervision/slaif-raggedized-helper/drafts/coding-startup-bounded-goal.txt.
Update docs/AGENT-ROLE-SETUP.md, docs/OAP-RUNBOOK.md and affected manifest/hash measurements for
this change. No helper/global client/model/profile/auth changes. New /goal-first startup is
NOT operationally validated merely by a file hash: strategy plans to qualify it during the
same-objective004-b fresh control handoff, before final004 acceptance. Do not self-trigger it.

## Non-goals

No encoder/reranker implementation (007/012), full onlineAPI (014), GPUcontroller (015), model
loading/download, arbitrary plugin/shell execution from trial JSON or external target discovery.
No live requests, credentials discovery, service/process/GPU changes, actual sensitive corpus,
release/tag/deploy/merge. No claim of physical cold cache, speedup, quality, VRAM safety or license
clearance from fixtures. No source-law rewrite, reduced fullMVP or human-owner/referral behavior.

## Acceptance criteria

1. Strict finite trial spec/sample/result models bind declared code/backend/model/profile and
   available tokenizer/runtime identities, purpose, exact workload/seed fingerprints, warmup/
   repetition/concurrency and total time/call/output allowances. Distinguish declared identity
   from execution-observed evidence and unavailable physical identities. Missing required
   execution inputs or inconsistent fingerprints/settings refuse before dispatch. Bound counts,
   strings and collections; reject bool-as-number, nonfinite/negative-invalid values and unknown
   settings. Actual supported workload is repeated-parent: unimplemented context/pair/batch/
   precision/seed controls must refuse or name a prerequisite, not silently claim application.
2. Runner actually invokes current gateway/direct application code against the configured
   target through its real transport. One absolute trial deadline and one shared admission
   allowance span ALL warmups, repetitions, retries, template and model calls and any workers;
   never reset full allowances per probe. Enforce at actual transport dispatch including failed
   connects, not only adapter cycles or a remaining-time calculation at each outer invocation.
   Output reservation/observed accounting preserves003 behavior and never fabricates unknown
   usage. Deadline/cancellation stops new work/retries and closes/joins owned work within a
   finite bound; document cooperative in-flight limits, never kill upstream model processes.
3. Capture safe raw per-trial/per-phase observations, actual attempted calls, known usage and
   outcome/error classes. Keep warmups separate from measurement samples and first/repeated
   order separate from cold/warm physical state (unknown absent evidence). Native template
   time is not TTFT. Reported cached tokens are not evaluated-prefill work; missing prefill
   stays null and contradictory cache/input accounting cannot become positive evidence.
   Bind model/backend fingerprints consistently. No raw prompts/output/credential/privateURL
   leakage into exported evidence; arbitrary supplied JSON never proves local execution.
4. Reproducible latency analysis reports sample counts/p50/p95/max with a documented quantile
   convention and finite safe results, separately for measured repetitions/warmups/stages as
   available. Failed, incomplete, unknown and zero-sample sets cannot produce a qualifying
   pass. Do not treat probe complete/exit0 alone as success: inspect actual phase outcomes,
   accounting validity, metric availability and target provenance. Synthetic/unverified target
   evidence cannot be promoted to hardware/model feasibility by configuration or labels.
5. Installed CLI help/import/default qualification planning performs zero model/HTTP/telemetry
   I/O; execution requires explicit opt-in. Provide a deterministic explicit synthetic route
   invoking actual adapters and owned HTTP fixtures, clearly MOCK/unqualified. An arbitrary
   configured URL cannot become an owned/verified synthetic endpoint by setting a boolean.
   Preserve existing CLI behavior, pre-work output admission and honest post-work export-error
   status with safe stdout evidence and spent ledger. Missing target/adapter prerequisites
   give exact NOT_RUN/BLOCKED evidence, never fake runnable successes.
6. Publish a machine-readable prerequisite projection covering all architecture§23.2 IDs:
   GATEWAY-01/02/03, DIRECT-01, V100-MEM-01/02, RERANK-01, EMBED-01/02, ONLINE-01/02,
   OPS-01/02, LICENSE-01. Only text/repeated-parent runner entrypoints available in this slice
   are executable. Other implementations/telemetry/parity are explicitly pending004-b or
   007/012/014/015/016/018 and actual target authorization. Persist actual real trials NOT_RUN;
   no positive topology/license/readiness claim. Full named composition follows004-b.
7. Meaningful owned-HTTP gateway and direct integration plus installedCLI tests observe real
   total calls across warmups/repetitions, including native templates and bounded retries;
   global deadline/allowance exhaustion and cancellation, identity/settings preflight with
   zero dispatch, outcome/metric ambiguity, deterministic summaries, synthetic promotion refusal
   and missing prerequisites. Preserve003 positive/negative regressions and existing OAP/lint/
   governance behavior. Exact bounded-goal prompt and docs/manifest measurements are updated;
   operational startup qualification remains explicitly pending strategy's004-b handoff.

## Verification and negative evidence

Owned loopback synthetic servers/processes only. Exercise both successful composition and
budget3 native boundary (template calls count), multiple repetitions with one shared allowance,
late body/deadline, accepted-then-closed unknown outcome without replay, and no-call invalid
identity/settings/output cases. Check real production transport composition, not only injected
result dictionaries. Safe cancellation should not leave an owned worker doing new dispatches.
Run focused tests during implementation; once composed run appropriate product/OAP/lint/
governance/CLI checks and inspect all actual final-head CI jobs. No repeated broad runs solely
to count tests. Missing/skipped/pending CI is not success.

## Documentation

Give exact supported CLI commands, spec/sample fields, budget admission/accounting semantics,
quantile definition and distinctions between declared/observed/supplied-unverified/MOCK evidence.
Document finite runner behavior and unsupported workload settings, unknown physical cache state
and unavailable gateway prefill/nativeTTFT. Record explicit004 software replan and remaining
004-b/019/ICA/model/GPU/corpus prerequisites. All real qualification gates and LICENSE-01 remain
open; certifiMPL exception has not been granted. Do not edit immutable earlier claims.

## Runtime and protected resources

Live target authorization: NONE. No approved actual URL/model/secretref/GPU ownership/corpus
reply has arrived. Permission is limited to ordinary reversible development, owned disposable
loopback/subprocess fixtures, lightweight tooling and GitHubCI/publication. No telemetry or
GPU probing in this slice. Preserve Qwen3.8-27B/A100Q8/xhigh/CLI0.164.0 settings, existing services,
agent homes, real credentials and FIFOs. Actual external model/hardware trials remain unrun.

## Deferred human adjudication

- Decision: NONE

## Publication and report

Create/reuse unique oap/004-qualification-harness PR against main; never merge. Commit exact
strategic files above. Implement/test/document/push, inspect and repair safe in-scope CI failures.
Publish one immutable report-only SELF commit with literal implementation parent, verify remote
PR/report/topology, then send exactly one response via qualified wrapper and finish bounded
coding goal. COMPLETE means this004-a slice executed, not whole004 accepted/merged, actual
feasibility passed or authority to choose004-b. Truthful PARTIAL/BLOCKED/FAILED is valid execution
reporting. Strategy alone reviews and activates the continuation. Use existing verify_report.py
and send-response.sh interfaces with identifier004-a; do not re-read consumed control/response
FIFO, add readers, resignal, run future orders or change model/profile.
