# OAP Work Order — 006-a

Status: DRAFT UNTIL STRATEGIC RECONCILIATION
Identifier: 006-a
PR mode: CREATE_NEW_PR
Branch: oap/006-native-extraction-and-chunking
Base commit: UNRESOLVED_AT_ACTIVATION
PR number: NEW
Expected active: UNRESOLVED_AT_ACTIVATION
Provenance: A06 A07 A08 A09 A25
Architecture SHA256: UNRESOLVED_AT_ACTIVATION
Governance SHA256: UNRESOLVED_AT_ACTIVATION

## Objective
Implement text/Markdown and native PDF extraction plus tokenizer-bounded structural chunks, preserving original evidence and exact anchors.

## Dependencies and current state
005 accepted. Strategy must inspect current GitHub/main/PRs/checks, preceding terminal resolution,
source/projection identities, runtime/authorization gates and dirty state. This draft has no
execution authority. Verify/split/revise it before final publication; never fabricate live fields.

## Allowed paths and scope
source_adapters/, extraction/, chunking.py, tokenizer utilities, tests/fixtures/ synthetic licensed text/PDF, tests/{unit,integration}/, docs/ingestion.md.
The activated order/active and this round's report are additional governed transcript paths.

## Non-goals
No unrelated features/refactors, edits to other projects, model/provider replacement, production
service actions, public exposure, real secret/corpus publication, release/tag/deploy or automated
merge by coding. Live hardware/model access is NOT authorized by a draft or by installed keys.

## Acceptance criteria
1. Headings/lists/code/tables/units/warnings/read-order and source spans survive extraction and chunk mapping.
2. Independent tokenizer budgets enforce 512/768/1024 starting values and complete reranker pair checks without silently trimming tails.
3. Oversized procedures/tables split at traceable structural boundaries with repeated original headers and appropriate neighbors.
4. Malformed/resource-heavy documents fail within configured limits; no vision/rasterizer is loaded by this objective.

## Verification and negative evidence
Golden synthetic command/version/negation/table fixtures, multilingual technical identifiers, oversized inputs and extraction resource failures; assert exact span reconstruction.
Use focused local checks; record exact command/result and mock/live distinction. No skipped,
missing, pending or blocked check is a pass. Failures/limits must appear in the immutable report.

## Documentation
Document supported native formats, token policies, refusal and uncertainty behavior.

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
