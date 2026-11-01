# OAP Work Order — 008-a

Status: DRAFT UNTIL STRATEGIC RECONCILIATION
Identifier: 008-a
PR mode: CREATE_NEW_PR
Branch: oap/008-raw-hybrid-snapshots
Base commit: UNRESOLVED_AT_ACTIVATION
PR number: NEW
Expected active: UNRESOLVED_AT_ACTIVATION
Provenance: A17 A18 A19 A24
Architecture SHA256: UNRESOLVED_AT_ACTIVATION
Governance SHA256: UNRESOLVED_AT_ACTIVATION

## Objective
Implement exact CPU dense and technical-token BM25 indexes with authorized retrieval, fusion and atomic snapshot publication.

## Dependencies and current state
007 accepted. Strategy must inspect current GitHub/main/PRs/checks, preceding terminal resolution,
source/projection identities, runtime/authorization gates and dirty state. This draft has no
execution authority. Verify/split/revise it before final publication; never fabricate live fields.

## Allowed paths and scope
lexical.py, snapshots.py, retrieval.py, authorization.py, tests/{unit,integration,security}/, docs/retrieval.md.
The activated order/active and this round's report are additional governed transcript paths.

## Non-goals
No unrelated features/refactors, edits to other projects, model/provider replacement, production
service actions, public exposure, real secret/corpus publication, release/tag/deploy or automated
merge by coding. Live hardware/model access is NOT authorized by a draft or by installed keys.

## Acceptance criteria
1. Technical identifiers/flags/versions/negation and Slovenian handling survive lexical normalization; no raw-score addition.
2. 60+60 initial candidate retrieval and RRF k=60 expose stage/cap loss with deterministic dedup/version identity.
3. Snapshot validation binds all row IDs/vectors/ACL/deletion/policy/model hashes; corrupt/missing/mismatched snapshots fail closed.
4. Readers pin a coherent snapshot while a locked writer atomically activates another; unauthorized rows never reach candidates.

## Verification and negative evidence
Rank fixtures, raw baseline retrieval, cross-ACL poison passages, checksum/count/NaN mismatches and concurrent activation/reader tests.
Use focused local checks; record exact command/result and mock/live distinction. No skipped,
missing, pending or blocked check is a pass. Failures/limits must appear in the immutable report.

## Documentation
Explain raw baseline, snapshot manifest/versioning, atomicity and exact-search limits.

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
