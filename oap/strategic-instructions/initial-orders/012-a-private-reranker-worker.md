# OAP Work Order — 012-a

Status: DRAFT UNTIL STRATEGIC RECONCILIATION
Identifier: 012-a
PR mode: CREATE_NEW_PR
Branch: oap/012-private-reranker-worker
Base commit: UNRESOLVED_AT_ACTIVATION
PR number: NEW
Expected active: UNRESOLVED_AT_ACTIVATION
Provenance: A20 A28 A29; RERANK-01
Architecture SHA256: UNRESOLVED_AT_ACTIVATION
Governance SHA256: UNRESOLVED_AT_ACTIVATION

## Objective
Implement a private resident reranker worker with bounded pairs/batches/queues, cancellation, health and tested CPU reference behavior.

## Dependencies and current state
011 accepted; 004 profile evidence required for GPU readiness. Strategy must inspect current GitHub/main/PRs/checks, preceding terminal resolution,
source/projection identities, runtime/authorization gates and dirty state. This draft has no
execution authority. Verify/split/revise it before final publication; never fabricate live fields.

## Allowed paths and scope
reranking.py or reranking/, private worker/supervisor interface, config/profiles/, tests/, docs/reranker.md.
The activated order/active and this round's report are additional governed transcript paths.

## Non-goals
No unrelated features/refactors, edits to other projects, model/provider replacement, production
service actions, public exposure, real secret/corpus publication, release/tag/deploy or automated
merge by coding. Live hardware/model access is NOT authorized by a draft or by installed keys.

## Acceptance criteria
1. Online default selects pinned V100 FP16 cross-encoder, keeps BGE query encoder on CPU, and rejects unvalidated pair truncation.
2. Private IPC, bounded queue/in-flight/batch timeout and cancellation release ownership correctly.
3. Worker death/OOM/unready state produces truthful failure or explicitly configured labeled RRF-only mode.
4. Real ranking/reference/latency/peak evidence is linked; mock worker tests do not prove GPU performance.

## Verification and negative evidence
Queue saturation/cancel/restart/malformed-score fixtures, private-interface access rejection, CPU reference subset and authorized co-residency smoke.
Use focused local checks; record exact command/result and mock/live distinction. No skipped,
missing, pending or blocked check is a pass. Failures/limits must appear in the immutable report.

## Documentation
Document ready vs configured, evaluated batches, degradation and worker recovery.

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
