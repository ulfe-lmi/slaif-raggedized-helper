# OAP Work Order — 017-a

Status: DRAFT UNTIL STRATEGIC RECONCILIATION
Identifier: 017-a
PR mode: CREATE_NEW_PR
Branch: oap/017-updates-recovery-security
Base commit: UNRESOLVED_AT_ACTIVATION
PR number: NEW
Expected active: UNRESOLVED_AT_ACTIVATION
Provenance: A18 A24 A25 A26 A34 A37
Architecture SHA256: UNRESOLVED_AT_ACTIVATION
Governance SHA256: UNRESOLVED_AT_ACTIVATION

## Objective
Qualify source revision/deletion/revocation propagation, backup/restore and concurrent snapshot readers; fix demonstrated security/privacy gaps.

## Dependencies and current state
016 resolved with visual scope honestly classified. Strategy must inspect current GitHub/main/PRs/checks, preceding terminal resolution,
source/projection identities, runtime/authorization gates and dirty state. This draft has no
execution authority. Verify/split/revise it before final publication; never fabricate live fields.

## Allowed paths and scope
artifacts/jobs/snapshots/authorization/caches, focused source/CLI integration, tests/{integration,security}/, docs/data-lifecycle.md.
The activated order/active and this round's report are additional governed transcript paths.

## Non-goals
No unrelated features/refactors, edits to other projects, model/provider replacement, production
service actions, public exposure, real secret/corpus publication, release/tag/deploy or automated
merge by coding. Live hardware/model access is NOT authorized by a draft or by installed keys.

## Acceptance criteria
1. Changed/deleted sources invalidate dependent contexts/vectors and disappear from activated results/source access.
2. Snapshot rollback/backup restore cannot revive revoked ACL or cross incompatible model/policy spaces.
3. Crash at publication boundaries preserves last complete state and predictable resumable jobs.
4. Prompt injection, traversal/SSRF, private-cache leakage and logging canaries are denied/redacted without weakening legitimate scope.

## Verification and negative evidence
Disposable filesystem fault injection, concurrent readers/writers, rights/revocation policy changes, backup restore and adversarial request/extraction tests.
Use focused local checks; record exact command/result and mock/live distinction. No skipped,
missing, pending or blocked check is a pass. Failures/limits must appear in the immutable report.

## Documentation
Document retention/tombstone/purge boundaries, backup integrity and operator recovery limitations.

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
