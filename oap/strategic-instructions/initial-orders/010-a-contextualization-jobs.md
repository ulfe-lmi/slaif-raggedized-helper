# OAP Work Order — 010-a

Status: DRAFT UNTIL STRATEGIC RECONCILIATION
Identifier: 010-a
PR mode: CREATE_NEW_PR
Branch: oap/010-contextualization-jobs
Base commit: UNRESOLVED_AT_ACTIVATION
PR number: NEW
Expected active: UNRESOLVED_AT_ACTIVATION
Provenance: A10 A11 A12 A13 A15
Architecture SHA256: UNRESOLVED_AT_ACTIVATION
Governance SHA256: UNRESOLVED_AT_ACTIVATION

## Objective
Implement stable-parent contextualization, long-document fallback, bounded validation/retries and artifact reuse while retaining raw-only retrieval on rejected context.

## Dependencies and current state
009 accepted; adapters and preserved-profile prerequisites. Strategy must inspect current GitHub/main/PRs/checks, preceding terminal resolution,
source/projection identities, runtime/authorization gates and dirty state. This draft has no
execution authority. Verify/split/revise it before final publication; never fabricate live fields.

## Allowed paths and scope
context_generation.py, context_validation.py, jobs.py, prompts/, tests/{unit,integration,security}/, docs/contextualization.md.
The activated order/active and this round's report are additional governed transcript paths.

## Non-goals
No unrelated features/refactors, edits to other projects, model/provider replacement, production
service actions, public exposure, real secret/corpus publication, release/tag/deploy or automated
merge by coding. Live hardware/model access is NOT authorized by a draft or by installed keys.

## Acceptance criteria
1. Stable prefix/tokenized template and varying chunk suffix preserve target IDs; no previous annotations fed forward.
2. Whole-parent vs section-plus-references mode and token/image/template/output reserves are explicit.
3. JSON/support/ACL/version/numeric/identifier/negation checks reject malformed or unsupported annotations; rejected jobs remain raw-only.
4. Parent change invalidation and interruption resume preserve exact completed artifacts and adapter/model/prompt provenance.

## Verification and negative evidence
Fake model adversarial outputs, private supporting blocks, contradictory/review-required context, oversized parents and crash/retry tests; authorized sample audit separately.
Use focused local checks; record exact command/result and mock/live distinction. No skipped,
missing, pending or blocked check is a pass. Failures/limits must appear in the immutable report.

## Documentation
Document limitations of validation vs entailment, original supports and measured cache status.

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
