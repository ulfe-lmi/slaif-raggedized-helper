# OAP Work Order — 011-a

Status: DRAFT UNTIL STRATEGIC RECONCILIATION
Identifier: 011-a
PR mode: CREATE_NEW_PR
Branch: oap/011-contextual-index-evaluation
Base commit: UNRESOLVED_AT_ACTIVATION
PR number: NEW
Expected active: UNRESOLVED_AT_ACTIVATION
Provenance: A11 A16 A17 A18 A33
Architecture SHA256: UNRESOLVED_AT_ACTIVATION
Governance SHA256: UNRESOLVED_AT_ACTIVATION

## Objective
Connect accepted contexts to embedding/BM25 text construction and controlled raw-vs-contextual evaluation without changing authoritative source evidence.

## Dependencies and current state
010 accepted. Strategy must inspect current GitHub/main/PRs/checks, preceding terminal resolution,
source/projection identities, runtime/authorization gates and dirty state. This draft has no
execution authority. Verify/split/revise it before final publication; never fabricate live fields.

## Allowed paths and scope
embedding.py, lexical.py, snapshots.py, evaluation/, tests/, docs/benchmarks/contextual-retrieval.md.
The activated order/active and this round's report are additional governed transcript paths.

## Non-goals
No unrelated features/refactors, edits to other projects, model/provider replacement, production
service actions, public exposure, real secret/corpus publication, release/tag/deploy or automated
merge by coding. Live hardware/model access is NOT authorized by a draft or by installed keys.

## Acceptance criteria
1. Only accepted contexts enter enriched indexes and retain most restrictive supporting ACL.
2. Enrichment overflow shortens valid annotation or rechunks/regenerates; original text is never truncated.
3. Raw and contextual variants share extraction/chunking/evaluation splits so gains are attributable.
4. A measured benefit or honest inconclusive/negative result is reported; no automatic accuracy claim.

## Verification and negative evidence
Rejected-context exclusion, ACL inheritance, fingerprint invalidation, overflow/regeneration and fixed-split ablation tests; actual model quality only from qualified runs.
Use focused local checks; record exact command/result and mock/live distinction. No skipped,
missing, pending or blocked check is a pass. Failures/limits must appear in the immutable report.

## Documentation
Report enrichment failure categories, source support review and promotion/rollback decision.

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
