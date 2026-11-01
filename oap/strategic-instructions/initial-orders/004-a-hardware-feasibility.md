# OAP Work Order — 004-a

Status: DRAFT UNTIL STRATEGIC RECONCILIATION
Identifier: 004-a
PR mode: CREATE_NEW_PR
Branch: oap/004-hardware-feasibility
Base commit: UNRESOLVED_AT_ACTIVATION
PR number: NEW
Expected active: UNRESOLVED_AT_ACTIVATION
Provenance: A02 A15 A16 A20 A27 A29 A36; UPDATE A1
Architecture SHA256: UNRESOLVED_AT_ACTIVATION
Governance SHA256: UNRESOLVED_AT_ACTIVATION

## Objective
Run the early feasibility matrix with the real preserved Qwen profile and model artifacts, then record measured safe defaults and fallbacks. If access is missing, publish an honest blocker; strategy must replan rather than pretend the gate passed.

## Dependencies and current state
003 accepted; authorized dedicated test hardware/profile ownership. Strategy must inspect current GitHub/main/PRs/checks, preceding terminal resolution,
source/projection identities, runtime/authorization gates and dirty state. This draft has no
execution authority. Verify/split/revise it before final publication; never fabricate live fields.

## Allowed paths and scope
scripts/qualification/, config/profiles/ measured candidates, docs/benchmarks/, docs/UNCERTAINTIES.md; no changes to unrelated serving repos.
The activated order/active and this round's report are additional governed transcript paths.

## Non-goals
No unrelated features/refactors, edits to other projects, model/provider replacement, production
service actions, public exposure, real secret/corpus publication, release/tag/deploy or automated
merge by coding. Live hardware/model access is NOT authorized by a draft or by installed keys.

## Acceptance criteria
1. Fingerprint known-working long-context profiles before any separately authorized transition and restore them after the test.
2. Measure Q6 vision 32k plus FP16 reranker batch 1/2/4/8 at worst permitted length/concurrency, cold/warm/peak allocation and restart.
3. Measure CPU query embeddings, CPU/GPU BGE parity, reranker CPU reference and gateway/direct true prefill behavior.
4. Select provisional online context/batch/fallback only from evidence; do not claim co-resident safety or quality if any mandatory measurement is absent.

## Verification and negative evidence
GATEWAY/DIRECT, V100-MEM-01/02, RERANK-01, EMBED-01/02; capture raw safe metrics and no OOM/lockup/regression with peak margin. Test harness failure paths in synthetic fixtures before live use.
Use focused local checks; record exact command/result and mock/live distinction. No skipped,
missing, pending or blocked check is a pass. Failures/limits must appear in the immutable report.

## Documentation
Benchmark report declares host/device/model/runtime, authorization, raw data, limitations, restore result and topology decision.

## Runtime and protected resources
Routine disposable synthetic setup is permitted after activation. Preserve source originals,
human client settings, unrelated worktrees and existing Qwen/gateway services. Final order must
name any live authorization, host/GPU/profile, call/data/time limits and rollback, or say NONE.

## Deferred human adjudication
- Decision: NONE

## Publication and report
Follow compact coding protocol. One numeric objective/PR; reuse it on interrupted -a. Commit
strategic order/active unchanged, implement/test/document, push and create/amend PR. Final report
records literal implementation SHA and SELF; its commit changes only the report, parent equals
implementation. Verify remote publication before response OK. Coding never merges. Strategy
independently reviews exact head, required checks and gates before development acceptance.
