# OAP Work Order — 001-a

Status: DRAFT UNTIL STRATEGIC RECONCILIATION
Identifier: 001-a
PR mode: CREATE_NEW_PR
Branch: oap/001-environment-inventory
Base commit: UNRESOLVED_AT_ACTIVATION
PR number: NEW
Expected active: UNRESOLVED_AT_ACTIVATION
Provenance: A02 A04 A14 A15 A29 A36 A40; UPDATE A0
Architecture SHA256: UNRESOLVED_AT_ACTIVATION
Governance SHA256: UNRESOLVED_AT_ACTIVATION

## Objective
Create a sanitized inventory of relevant installed capabilities and exact missing permissions. Pin the reference gateway contracts and identify which target services/hosts need a later live authorization.

## Dependencies and current state
000 accepted. Strategy must inspect current GitHub/main/PRs/checks, preceding terminal resolution,
source/projection identities, runtime/authorization gates and dirty state. This draft has no
execution authority. Verify/split/revise it before final publication; never fabricate live fields.

## Allowed paths and scope
docs/environment-inventory.md, docs/UNCERTAINTIES.md, config/ discovery schema if needed, focused read-only inventory helper and its synthetic tests.
The activated order/active and this round's report are additional governed transcript paths.

## Non-goals
No unrelated features/refactors, edits to other projects, model/provider replacement, production
service actions, public exposure, real secret/corpus publication, release/tag/deploy or automated
merge by coding. Live hardware/model access is NOT authorized by a draft or by installed keys.

## Acceptance criteria
1. Record deployed vs repository gateway identity separately; identify bounded Responses/vision/streaming contracts and unavailable route facts.
2. Record authorized observable GGUF/projector/runtime/KV/MTP/profile/GPU/CPU facts; preserve human-reported long-context capability without claiming new measurements.
3. List each unknown host/route/hash/access boundary and a safe bounded experiment needed to resolve it.
4. No model allocation, service stop, secret readout, unapproved remote login or inferred credentials occurs.

## Verification and negative evidence
Test inventory serialization with missing fields and redaction canaries; compare recorded commit/contracts to actual read-only sources. Any privileged discovery remains BLOCKED, not inferred.
Use focused local checks; record exact command/result and mock/live distinction. No skipped,
missing, pending or blocked check is a pass. Failures/limits must appear in the immutable report.

## Documentation
Inventory records timestamps, provenance, protected resources and prerequisites for live trials.

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
