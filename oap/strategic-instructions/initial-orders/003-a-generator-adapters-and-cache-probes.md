# OAP Work Order — 003-a

Status: DRAFT UNTIL STRATEGIC RECONCILIATION
Identifier: 003-a
PR mode: CREATE_NEW_PR
Branch: oap/003-generator-adapters-and-cache-probes
Base commit: UNRESOLVED_AT_ACTIVATION
PR number: NEW
Expected active: UNRESOLVED_AT_ACTIVATION
Provenance: A13 A14 A15 A22 A36; GATEWAY-01/02/03 DIRECT-01
Architecture SHA256: UNRESOLVED_AT_ACTIVATION
Governance SHA256: UNRESOLVED_AT_ACTIVATION

## Objective
Implement the semantic generator interface using bounded SLAIF Responses online and explicit private llama offline adapters. Add cache/capability probes without changing either backend.

## Dependencies and current state
002 accepted; live probes require named route authority. Strategy must inspect current GitHub/main/PRs/checks, preceding terminal resolution,
source/projection identities, runtime/authorization gates and dirty state. This draft has no
execution authority. Verify/split/revise it before final publication; never fabricate live fields.

## Allowed paths and scope
src/slaif_raggedized_helper/model_clients/, focused config/schemas, scripts/qualification/, tests/{unit,integration}/, docs/generator-contract.md.
The activated order/active and this round's report are additional governed transcript paths.

## Non-goals
No unrelated features/refactors, edits to other projects, model/provider replacement, production
service actions, public exposure, real secret/corpus publication, release/tag/deploy or automated
merge by coding. Live hardware/model access is NOT authorized by a draft or by installed keys.

## Acceptance criteria
1. Gateway fixture tests parse multiple output items, refusal/error/cancel and supported streaming without assuming complete Responses parity.
2. Direct native cache/slot controls are capability-gated and never forwarded as undocumented gateway fields.
3. Gateway denial/failure never invokes a direct online backend; secrets cannot enter URLs/logs/prompts.
4. Probes record cold/warm actual evaluated prompt tokens, template identity and unavailable metrics distinctly; real tests run only with scoped authorization.

## Verification and negative evidence
Use fake HTTP servers for errors/timeouts/malformed streams/retry ambiguity and scope refusal. When authorized execute small GATEWAY-01/02 and cache probes with exact call budget; otherwise report live gates NOT RUN.
Use focused local checks; record exact command/result and mock/live distinction. No skipped,
missing, pending or blocked check is a pass. Failures/limits must appear in the immutable report.

## Documentation
Document actual accepted contract, route/version qualification and remaining live prerequisites.

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
