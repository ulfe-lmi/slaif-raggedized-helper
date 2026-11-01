# OAP Work Order — 000-a

Status: DRAFT UNTIL STRATEGIC RECONCILIATION
Identifier: 000-a
PR mode: CREATE_NEW_PR
Branch: oap/000-bootstrap-governance
Base commit: UNRESOLVED_AT_ACTIVATION
PR number: NEW
Expected active: UNRESOLVED_AT_ACTIVATION
Provenance: H scaffold request; A38 A39 A40
Architecture SHA256: UNRESOLVED_AT_ACTIVATION
Governance SHA256: UNRESOLVED_AT_ACTIVATION

## Objective
Publish the reviewed architecture, source inputs, compact instructions, helper tests and audit/roadmap materials as the first development PR after activation. Establish narrowly scoped governance CI with no deployment side effects.

## Dependencies and current state
none. Strategy must inspect current GitHub/main/PRs/checks, preceding terminal resolution,
source/projection identities, runtime/authorization gates and dirty state. This draft has no
execution authority. Verify/split/revise it before final publication; never fabricate live fields.

## Allowed paths and scope
Root governance files, docs/, oap/, tests/oap/, .gitignore and a focused .github/workflows/oap.yml; preserve LICENSE and user setup.
The activated order/active and this round's report are additional governed transcript paths.

## Non-goals
No unrelated features/refactors, edits to other projects, model/provider replacement, production
service actions, public exposure, real secret/corpus publication, release/tag/deploy or automated
merge by coding. Live hardware/model access is NOT authorized by a draft or by installed keys.

## Acceptance criteria
1. Source originals match supplied SHA-256 and newer update precedence survives the projections.
2. Helper suite and state/context checks pass from clean clone without model/credential access.
3. Governance-only CI runs at the final report head; merge/push automation has no deployment or exposure action.
4. No RAG implementation, fabricated audit, live inference, credential/config change or readiness claim is included.

## Verification and negative evidence
Run stdlib OAP tests, negative protocol fixtures, context/source manifest check and clean-clone check. Inspect workflow diff for publish/deploy/secrets or privilege expansion.
Use focused local checks; record exact command/result and mock/live distinction. No skipped,
missing, pending or blocked check is a pass. Failures/limits must appear in the immutable report.

## Documentation
README, STATUS and bootstrap receipt distinguish local setup, remote publication and unrun client/product gates.

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
