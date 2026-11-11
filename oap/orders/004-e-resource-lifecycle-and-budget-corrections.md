# OAP Work Order — 004-e

Status: FINAL
Identifier: 004-e
PR mode: AMEND_EXISTING_PR
Branch: oap/004-qualification-harness
Base commit: 2bc320ff9e66c874f07da061218f2ff52e3420a9
PR number: 6
Expected active: 004-d
Provenance: H activated full MVP; A resource/qualification contracts; E independent 004-d implementation review
Architecture SHA256: 4b41905396a3838269fd6cf372614cd23cb2c3b6a37be09f29ed752803c0983a
Governance SHA256: dd7f3a7bd62888edef5a5cb1678a80d26b1a7af28bd85659ce5da2634755c8f4

## Objective

Correct the independently reproduced resource lifecycle, deadline, aggregate
accounting, late-export and resource contract failures in 004-d. Preserve the useful local telemetry
and the plain trial v1 contract. Same objective 004 and PR6; this is not whole-004
acceptance, parity completion, real qualification, or merge authority.

## Dependencies and current state

Verified immutable report-only SELF57426f5ce76a27601c20512532723e5187895456 has
sole implementation parent a4f15333de8dfbde0508357d113e123a7f6775f5; report SHA256
d5de17d065dec659b63d9f6e6395552cc1db1178ce02b4d19b3ead4872bbf28f. Exact remote
bytes/head/topology verified. Unique OPEN PR6/original branch/base-main
2bc320ff9e66c874f07da061218f2ff52e3420a9, no auto-merge. Implementation
CI42878145680 and report CI42879646566 ALL5SUCCESS (last18:47:12Z and18:57:38Z).
Reuse completed runs; do not dispatch duplicates. Sole D response consumed
2026-11-10T18:53:50.426508+00:00; do not reread FIFO/replay. Actual coding native
goal achieved and quiet/no pending tool observed before one goal clear; footer
cleared. No post-response CI poll. Worktree clean before strategic review addition.
Independent collection452unit+316integration=768product,41OAP; governance check0,
manifestdd7f3a7bd62888edef5a5cb1678a80d26b1a7af28bd85659ce5da2634755c8f4,
routine46759/50000bytes. No actual target/corpus/license-exception input received.

FINAL strategic review oap/reviews/004-d-review.json SHA256
5a8d4dff6a259dc689cf056071091960501ba1ae321a0b3285b611230bf19e10 records
CHANGES_REQUIRED_CONTINUE_SAME_PR_004_e. Actual committed resource/runner/CLI
bytes equal the independently reviewed source; report-only publication changes no
product code. Read this review and the actual affected code/tests plus ordinary
compact governance, not whole original books/helper internals/future orders.

F01: initial owned GPU query takes ~0.276s under a bound0.08s deadline, admits a
late first sample and claims finished. F02: synthetic1100 samples charge9011200
bytes beyond8388608 cap and yield an invalid final section; read caps are called
actual bytes_read. An actual pipe-read observer also proves cap128 reads4096 but
reports129: enforce remaining read allowance and report actual observed bytes. F03: in-process KeyboardInterrupt after one actual owned HTTP
reply leaves observer running and samples grow2->6 while caller survives.
F04: a genuine late file-export failure after two actual HTTP calls preserves the
wrapper on stdout but falsely reports zero calls/pre-dispatch refusal on stderr.
F05: both resource schemas admit boolean version=True, and omit collector/code
source identity despite the immutable D report claiming code_version + collector provenance.

## Allowed paths and scope

Focused fixes in qualification/resources.py, qualification/runner.py and cli.py;
necessary strict resource contracts, meaningful owned fixtures/tests and concise
resource protocol/README/STATUS/TESTING/UNCERTAINTIES/context/manifest updates.
Commit exact published order/active and oap/reviews/004-d-review.json unchanged
(SHA2565a8d4dff6a259dc689cf056071091960501ba1ae321a0b3285b611230bf19e10).
No new dependency expected. Preserve startup/role/runbook sources unchanged.

## Non-goals

No architecture, transport/provider stack, helper, client/profile/model/auth/global
configuration changes. No heavyweight model installation, real target/GPU/model
allocation, unknown PID/service control, host discovery, sensitive data or license
exception. No parity scope substitution, next objective, merge/tag/release/deploy.

## Acceptance criteria

1. Reuse one absolute work deadline. Clip initial metadata-query allowance to the
   remaining trial AND observer duration; check admission again after any startup
   query and before every sample/query. No new sampling or query work after expiry,
   no sample labelled t=0 when actually admitted late. Explicit bounded cleanup
   may follow expiry; it never authorizes further collection/model dispatch.
2. Enforce aggregate collection calls/bytes/time before work, across the whole
   observer lifetime. Choose and document honest units and accounting semantics:
   actual observed bytes and reserved/read-cap allowances are distinct. Include
   startup/final observations and device work in their documented applicable
   allowances; never reset limits per phase. A permitted finite workload must
   terminate with a valid honest partial resource record at resource exhaustion,
   rather than generating an over-limit invalid document. Known0 stays0;
   unavailable stays null; collector work never consumes/invents model attempts.
3. Stop and finitely join owned observer work on EVERY execution exit, including
   in-process KeyboardInterrupt/BaseException with a surviving caller, startup
   failure, ordinary failure, and standalone diagnostic interruption. No continued
   samples or queries after cancellation; no daemon/process-exit masking of a leak.
   Stop only exact owned collector children. Preserve the original exception and
   original trial model/template deadline/call/output semantics.
4. Late output failures use the canonical valid inner trial ledger for resource
   wrappers. After real work retain full safe evidence on stdout, exit3, report
   actual known calls with a replay warning, never falsely label zero/pre-dispatch.
   Missing/invalid ledger availability remains explicit unknown. Preserve genuine
   pre-dispatch refusal, plain-v1 export and post-work invalid-resource positives.
5. Bind bounded collector identity and actual package/code-source metadata into
   resource records, including standalone diagnostics, with unavailable revision
   explicit rather than invented. Do not add an attestation/signing system or Git
   subprocess on import/default commands. Resource schema versions refuse booleans
   and wrong numeric types; retain finite known-zero/unavailable semantics. Update
   claims to the actual represented binding.
6. Applicable unchanged independent process/HTTP witnesses now demonstrate the
   corrected behaviors, alongside fixed CSV units, pipe-boundary cap/timeout,
   plain wrapper/ledger and invalid-resource safe-exit positives. Do not weaken or
   overwrite strategic witnesses, relabel mock as measured hardware, or claim
   coding-authored fixtures are independent strategic evidence.
7. Add focused regression evidence for admission, cancellation with surviving
   caller, aggregate exhaustion and late-export spent accounting. Preserve current
   product/OAP contracts and existing relevant negatives. Complete relevant checks,
   lint/governance and actual current-head CI; missing/skipped checks are not green.
8. Correct documentation to actual guarantees and tests. Record prior failure and
   correction without rewriting immutable reports or erasing failed startup history.
   Keep encoder/rank parity, all14 gate composition, actual019/ICA/MVP/license gates
   explicitly outstanding. Keep documentation concise within the current byte ceiling;
   update measured context/manifest, never weaken ceilings or immutable sources.

## Verification and negative evidence

Retained independent witnesses:
/tmp/raggedized004-resource-process-review.py
/tmp/raggedized004-resource-integration-review.py
/tmp/raggedized004-resource-read-accounting-review.py
/tmp/raggedized004-resource-source-binding-review.py
Use actual committed APIs and inspect outputs, not exit0 alone: these observational
scripts intentionally print failing facts without necessarily exiting nonzero.
Run meaningful focused regressions then required full checks once at final state;
obtain counts by collection only, separately per directory as project CI does.
No repeated successful full suites solely to recover suppressed summary output.

## Documentation

Give exact deadline/cleanup and aggregate accounting semantics; truthful partial
availability and byte units; actual caller versus remote model scope; valid inner
ledger handling. Coding-authored /tmp/raggedized004-resource-telemetry-review.py
is useful coding evidence only, never an independent strategic/root witness.

## Runtime and protected resources

Live model/target/GPU/corpus authorization: NONE. Same bounded owned fixtures asD:
own-process CPU/RSS diagnoses <=5s/64samples per diagnosis; synthetic probes may
exercise higher library limits. Owned fake collector children <=2s timeout plus
<=1s cleanup and explicit output caps. No actual NVIDIA query is authorized or needed
for these corrections: use owned fixed-argv fake collector fixtures. Existing regression fixture budgets unchanged. Ordinary
lightweight dev tooling/GitHub CI/publication allowed. No actual host/device private
identity in Git, secret scan, service/driver/model changes, or upstream process kill.

## Deferred human adjudication

- Decision: NONE

## Publication and report

Amend existing PR6. Commit exact strategic artifacts unchanged. Inspect exact
implementation-head CI before immutable report-only SELF with literal sole parent;
verify remote bytes/head/topology, send one responseOK, mark bounded coding goal
complete and idle. Strategy owns report-head CI/review/next selection. No post-response
poll loop, competing reader, signal replay, or whole-objective acceptance claim.
