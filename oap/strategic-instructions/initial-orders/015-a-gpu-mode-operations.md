# OAP Work Order — 015-a

Status: DRAFT UNTIL STRATEGIC RECONCILIATION
Identifier: 015-a
PR mode: CREATE_NEW_PR
Branch: oap/015-gpu-mode-operations
Base commit: UNRESOLVED_AT_ACTIVATION
PR number: NEW
Expected active: UNRESOLVED_AT_ACTIVATION
Provenance: A02 A12 A27 A28 A35; OPS-01/02
Architecture SHA256: UNRESOLVED_AT_ACTIVATION
Governance SHA256: UNRESOLVED_AT_ACTIVATION

## Objective
Build idempotent profile transition state machine and adapters for explicitly owned services; preserve existing online/long-context profiles and durable jobs.

## Dependencies and current state
014 accepted; live mutation requires scoped service ownership. Strategy must inspect current GitHub/main/PRs/checks, preceding terminal resolution,
source/projection identities, runtime/authorization gates and dirty state. This draft has no
execution authority. Verify/split/revise it before final publication; never fabricate live fields.

## Allowed paths and scope
runtime/ or focused lifecycle module, cli.py, config/profiles/, scripts/operations/, tests/integration/, docs/operations.md.
The activated order/active and this round's report are additional governed transcript paths.

## Non-goals
No unrelated features/refactors, edits to other projects, model/provider replacement, production
service actions, public exposure, real secret/corpus publication, release/tag/deploy or automated
merge by coding. Live hardware/model access is NOT authorized by a draft or by installed keys.

## Acceptance criteria
1. Physical host/GPU identity and owner incarnation prevent conflicting heavy jobs, including different ports/processes.
2. Drain handles new/in-flight work with bounded timeout and refuses unknown processes instead of killing them.
3. Transition journal/checkpoints survive interruption; failed restore stays visible/not-ready and never starts incompatible profile.
4. Successful restore verifies Qwen allocation/projector, private reranker margin, encoder/snapshot/ACL/gateway readiness before admitting traffic.

## Verification and negative evidence
Fake supervisors with crash at every transition, stale/unknown locks, cancellation and repeated calls; authorized OPS-01/02 proves real restore without lost published index.
Use focused local checks; record exact command/result and mock/live distinction. No skipped,
missing, pending or blocked check is a pass. Failures/limits must appear in the immutable report.

## Documentation
Runbooks name supported supervisors, owned-service boundary, maintenance authorization and recovery actions.

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
