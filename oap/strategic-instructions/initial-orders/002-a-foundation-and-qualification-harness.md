# OAP Work Order — 002-a

Status: DRAFT UNTIL STRATEGIC RECONCILIATION
Identifier: 002-a
PR mode: CREATE_NEW_PR
Branch: oap/002-foundation-and-qualification-harness
Base commit: UNRESOLVED_AT_ACTIVATION
PR number: NEW
Expected active: UNRESOLVED_AT_ACTIVATION
Provenance: A03 A04 A08 A13 A35 A36 A37
Architecture SHA256: UNRESOLVED_AT_ACTIVATION
Governance SHA256: UNRESOLVED_AT_ACTIVATION

## Objective
Create the minimal Python src package, configuration schemas, generator/embedding/reranker interfaces, model/license lock schema and reusable benchmark result format. Tests run entirely with synthetic clients.

## Dependencies and current state
001 resolved; unknown live fields explicitly retained. Strategy must inspect current GitHub/main/PRs/checks, preceding terminal resolution,
source/projection identities, runtime/authorization gates and dirty state. This draft has no
execution authority. Verify/split/revise it before final publication; never fabricate live fields.

## Allowed paths and scope
pyproject.toml, chosen lockfile, src/slaif_raggedized_helper/{config,schema,model_clients,evaluation,cli}.py or focused package equivalents; config/, tests/, docs/.
The activated order/active and this round's report are additional governed transcript paths.

## Non-goals
No unrelated features/refactors, edits to other projects, model/provider replacement, production
service actions, public exposure, real secret/corpus publication, release/tag/deploy or automated
merge by coding. Live hardware/model access is NOT authorized by a draft or by installed keys.

## Acceptance criteria
1. Configuration rejects unknown or inconsistent device/precision/route/timeout fields and requires explicit secret references.
2. Model manifests distinguish checkpoint/tokenizer/pooling/GGUF/projector/runtime identities and unknown licenses.
3. Result records distinguish NOT RUN/BLOCKED/mock/live and missing prefill/usage metrics; no invented zero values.
4. Package imports and minimal doctor command work without model downloads, credentials, GPU or product service starts.

## Verification and negative evidence
Schema/CLI tests cover invalid config, unsafe direct-online fallback, incompatible space identity and secret redaction. Lock dependencies and inspect direct licenses; incomplete transitive audit remains visible.
Use focused local checks; record exact command/result and mock/live distinction. No skipped,
missing, pending or blocked check is a pass. Failures/limits must appear in the immutable report.

## Documentation
Document only implemented commands, profile schema and manifest/benchmark evidence format.

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
