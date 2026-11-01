# OAP Work Order — 014-a

Status: DRAFT UNTIL STRATEGIC RECONCILIATION
Identifier: 014-a
PR mode: CREATE_NEW_PR
Branch: oap/014-authenticated-answer-api
Base commit: UNRESOLVED_AT_ACTIVATION
PR number: NEW
Expected active: UNRESOLVED_AT_ACTIVATION
Provenance: A14 A22 A23 A24 A25 A26 A28; ONLINE-01
Architecture SHA256: UNRESOLVED_AT_ACTIVATION
Governance SHA256: UNRESOLVED_AT_ACTIVATION

## Objective
Wire the complete API path from principal scope to hybrid search/rerank/evidence/gateway answer and authorized citations, including bounded conversation/error behavior.

## Dependencies and current state
013 accepted. Strategy must inspect current GitHub/main/PRs/checks, preceding terminal resolution,
source/projection identities, runtime/authorization gates and dirty state. This draft has no
execution authority. Verify/split/revise it before final publication; never fabricate live fields.

## Allowed paths and scope
api.py, answering.py, authorization.py, cli.py, config/, tests/{unit,integration,security}/, docs/api.md.
The activated order/active and this round's report are additional governed transcript paths.

## Non-goals
No unrelated features/refactors, edits to other projects, model/provider replacement, production
service actions, public exposure, real secret/corpus publication, release/tag/deploy or automated
merge by coding. Live hardware/model access is NOT authorized by a draft or by installed keys.

## Acceptance criteria
1. Search/answer/source/image routes require valid server-owned scope; caller filters cannot widen it and private data never crosses downstream boundaries.
2. Normal answer uses one gateway call; bounded follow-up rewrite/extra retrieval limits preserve identifiers and budget.
3. Gateway multiple items/stream/cancel/timeout errors are safe; no direct fallback on denial/failure; source-only outcome is explicitly different.
4. Citations, versions, insufficiency and degradation metadata remain truthful; logs/redaction and cache isolation hold under concurrency.

## Verification and negative evidence
Synthetic full-path HTTP tests with downstream spies proving no unauthorized exposure; auth revocation, cache scope, malicious sources, streaming cancellation and bounded retries. Authorized live ONLINE-01 separately.
Use focused local checks; record exact command/result and mock/live distinction. No skipped,
missing, pending or blocked check is a pass. Failures/limits must appear in the immutable report.

## Documentation
OpenAPI/route contract, operator auth setup, privacy defaults and supported response/stream limits.

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
