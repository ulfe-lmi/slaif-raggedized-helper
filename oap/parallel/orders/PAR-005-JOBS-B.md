# Parallel OAP candidate order — PAR-005-JOBS-B

Status: FINAL
Worktree: /home/janezp/codex-work/slaif-raggedized-helper-parallel-job-records
Base: 968da9025f259a519daa7f81407fe171cd034f28
Decision: NONE

## Human authority and isolated role

The human explicitly activated parallel coding using panes32/33 with GPT6.1 Terra
medium. You are a CODING WORKER despite the CLI starting in the strategic directory;
this trusted assignment overrides that initial role for this bounded task. Use the
specified isolated worktree as workdir for EVERY command/tool and absolute edit paths.
Never edit the main worktree or strategic files except your lane response via helper.

This is LOCAL CANDIDATE preparation under the human parallel mandate, not canonical
objective activation or another GitHub PR. The lane order/active/control replace main
oap/active only for your candidate. Main004-e and its FIFO pair remain untouched.
No push/PR/merge/next-work choice; strategy reviews and later commissions integration.
This scoped exception to single-executor activation/publication is explicitly authorized
by the human; ordinary engineering/security invariants remain. Preserve Terra medium,
no profile/model/auth/global changes, nested agents, services, GPU/model/downloads,
real keys/corpus, unknown-directory scans, or source-owner/contact/referral behavior.

Read root router, coding constitution/compact architecture/security and the exact relevant
source sections below. Do not explore OAP helpers, history, unrelated future orders or
full source books. Standard library/Pydantic/locked lightweight tools only, no new deps.
Actual code and meaningful negative/positive tests are required. Persist through routine
engineering issues; no arbitrary time/token limit or empty report-only success. No real
qualification follows from synthetic fixtures. Errors/logs must be safe and input-free.

## Local Git and report protocol

Only the exact allowed implementation paths may change. The copied lane order must be
committed unchanged. Make ONE implementation commit with sole parent the stated base.
Then commit ONLY the specified report JSON, sole parent implementation. Report fields:
lane_id, result COMPLETE/PARTIAL/FAILED, implementation_head full literal SHA,
report_publication_commit literal SELF, summary, API, tests with actual commands/results,
limitations. Do not push. Existing candidate/history remains intact. Report metadata
verification is not strategic acceptance. After local checks and clean worktree, call
this lane's respond helper ONCE, complete the actual implementation goal and idle.
No canonical FIFO/readers or post-response polling. A report alone does not fulfill work.


## Objective — job identity/state and immutable attempt contracts

Preparatory005 SOFTWARE contracts only, not canonical005 activation or worker010.
Read architecture8.2–8.4 (especially actual8.4 states/recovery),7.1,22.1–22.2,
actual source_admission contracts and schema.fingerprint. No provenance module
import (it is a separate candidate), no shared schema/router/source/governance edits.

Implement strict finite versioned job specification/identity, mutable logical-state
snapshot and distinct IMMUTABLE attempt diagnostic records with safe bounded APIs.
Deterministic job identity binds ALL declared input artifact/source refs and their
fingerprints, purpose/kind and full relevant policy/model/prompt/encoder/runtime
configuration digests. No ignored settings or changing identity through dictionary
order. Unknown/unqualified runtime identity remains explicit, not guessed. IDs/data
cannot select arbitrary executable/module/plugin/network actions; this is data only.

Follow architecture suggested state semantics PENDING/CLAIMED/RUNNING/COMPLETE,
RETRYABLE_FAILED/UNKNOWN_COMPLETION/REJECTED/FAILED/CANCELLED, with actual documented
consistent pure transitions/record validation. Job state is logically mutable;
individual record values/immutable attempts are separate. Attempt identity/correlation
must distinguish retries even for same job. Known0 counters remain0, unknown staysnull;
refuse booleans/nonfinite/inconsistent statuses/times/correlations. Diagnostics use
safe codes/opaque IDs, no source text/raw upstream errors/credentials.

A COMPLETE DTO does not prove output exists or is valid. Represent output references
and verification availability honestly; never call a missing/unverified artifact a
cache hit. Actual output-first staging/validation/atomic publication, owner/claim locks,
reconciliation after restart and retry execution belong010. A worker-owner reference
is process coordination, NOT product human-owner lookup/contact/referral. Old PID or
timestamp alone grants no ownership/steal action. No exactly-once inference claim;
UNKNOWN_COMPLETION stays explicit and cannot silently become retryable/completed.

Provide safe input-free admission for untrusted mapping/JSON, strict nested validation,
finite byte/node/string/ref/count limits and bounded serialization/roundtrip. Public
input-facing APIs must not leak caller-controlled unknown field locations from raw
Pydantic errors. Do not build a signing/auth or actual worker/service/control framework.

Meaningful tests: handcomputed identity/order stability and every relevant input/policy
change; separate retry attempts and correlation; valid state/attempt/output-reference
compositions; malformed/boolean/nonfinite/unknown/contradictory records, safe errors,
missing output not cache success, no automatic unknown-completion retry, bounded
JSON and immutable copied/mutated inputs. Compose actual owned SourceStore admission/
inspection to job input references while keeping separate ACL/corpus/rights for identical
bytes. Source approval is supplied operator metadata, not authentication. No model or
hardware, realcorpus, credentials, network/service/GPU or process ownership actions.

Document exact API, versions/identity/state/availability and remaining010 responsibilities.
Run focused tests/lint plus existing source/schema regressions once. No full count loops.
Whole005/MVP still requires canonical integration/CLI and architecture assessment.

## Lane controls/publication

ConsumeONLYfreshlanecontrolonce:
`python3 /home/janezp/codex-supervision/slaif-raggedized-helper/parallel/lane_signal.py wait-control job-records-b`
Ownactive:/home/janezp/codex-supervision/slaif-raggedized-helper/parallel/job-records-b/active. Nevercanonicalactive/FIFOs or wildcards overlanedirs.
Allowedpaths:src/slaif_raggedized_helper/job_records.py, docs/parallel/job-records-api.md, tests/unit/test_job_records.py, tests/integration/test_job_records_composition.py, oap/parallel/orders/PAR-005-JOBS-B.md
Copiedorder:oap/parallel/orders/PAR-005-JOBS-B.md
Report-onlypath:oap/parallel/reports/PAR-005-JOBS-B.json
Oneimplementationcommit(parent=statedbase), thenreport-onlycommit(parent=implementation),
cleanworktree andONElane response:
`python3 /home/janezp/codex-supervision/slaif-raggedized-helper/parallel/lane_signal.py respond job-records-b`
No push/PR/merge/nextwork. Complete actualtestedcode, notonlyreport, thenidle.

## Focused correction

Read exact regular JSON /home/janezp/codex-supervision/slaif-raggedized-helper/parallel/job-records/review.json and /home/janezp/codex-supervision/slaif-raggedized-helper/parallel/audit-job-records/report.json. Preserve immutable old reports and all prior identity, owner, unknown-completion, output and privacy positives.

- JOBS-A01: PENDING->CANCELLED must not fabricate an execution Attempt. Never-claimed pending cancellation retains null attempt reference. Retry-pending cancellation preserves the previous attempt reference and immutable history, not an unclaimed fabricated terminal attempt. Claimed/running cancellation still correlates to current actual attempt.
- JOBS-A02: Documented UTF8 bytes admission must decode strict UTF8 before JSON; json.loads(rawbytes) currently autoacceptsUTF16/32. Reject those safely while preserving valid UTF8/Slovenian/astral values.

Add actual cancellation-without-execution, retry-pending history/correlation and UTF16/32 refusal regressions. One implementation commit on this base, one report-only commit and one NEW lane response. No worker/claim/cache/auth/signature framework, main/PR/FIFO/model/profile changes or physical execution. Complete the actual corrections, then idle.
