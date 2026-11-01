# OAP Work Order — 005-a

Status: DRAFT UNTIL STRATEGIC RECONCILIATION
Identifier: 005-a
PR mode: CREATE_NEW_PR
Branch: oap/005-artifact-schema-and-source-scopes
Base commit: UNRESOLVED_AT_ACTIVATION
PR number: NEW
Expected active: UNRESOLVED_AT_ACTIVATION
Provenance: A05 A07 A12 A24 A25 A34
Architecture SHA256: UNRESOLVED_AT_ACTIVATION
Governance SHA256: UNRESOLVED_AT_ACTIVATION

## Objective
Implement immutable source/block/chunk/job schemas and allowed manifest ingestion with independent rights and ACL provenance. Establish access partitions before retrieval models see data.

## Dependencies and current state
002 accepted; 004 resolved or explicit independent-work replan preserving live gates. Strategy must inspect current GitHub/main/PRs/checks, preceding terminal resolution,
source/projection identities, runtime/authorization gates and dirty state. This draft has no
execution authority. Verify/split/revise it before final publication; never fabricate live fields.

## Allowed paths and scope
src/slaif_raggedized_helper/{schema,artifacts,jobs,authorization}.py, source_adapters/, tests/{unit,security}/, docs/data-model.md.
The activated order/active and this round's report are additional governed transcript paths.

## Non-goals
No unrelated features/refactors, edits to other projects, model/provider replacement, production
service actions, public exposure, real secret/corpus publication, release/tag/deploy or automated
merge by coding. Live hardware/model access is NOT authorized by a draft or by installed keys.

## Acceptance criteria
1. Logical document identity, revision, authority/version/language/rights/ACL and source spans round-trip without losing original text.
2. Byte dedup retains distinct rights/provenance and deterministic IDs; annotations remain separate.
3. Traversal, symlink escape, arbitrary URL fetch, missing scope and invalid rights/ACL metadata refuse safely.
4. Atomic artifact writes and interrupted retry preserve prior complete data; no untrusted pickle path exists.

## Verification and negative evidence
Synthetic manifests with shared bytes/different ACL, corrupt hashes, duplicate IDs, invalid path and interrupted writes; assert no unauthorized content/secret leaks.
Use focused local checks; record exact command/result and mock/live distinction. No skipped,
missing, pending or blocked check is a pass. Failures/limits must appear in the immutable report.

## Documentation
Define schema versions, fingerprints, safe storage layout, source rights and identity policy.

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
