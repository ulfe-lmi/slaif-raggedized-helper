# OAP Work Order — 007-a

Status: DRAFT UNTIL STRATEGIC RECONCILIATION
Identifier: 007-a
PR mode: CREATE_NEW_PR
Branch: oap/007-embedding-pipeline
Base commit: UNRESOLVED_AT_ACTIVATION
PR number: NEW
Expected active: UNRESOLVED_AT_ACTIVATION
Provenance: A08 A12 A16 A27
Architecture SHA256: UNRESOLVED_AT_ACTIVATION
Governance SHA256: UNRESOLVED_AT_ACTIVATION

## Objective
Build the shared BGE space definition, CPU FP32 query interface and checkpointed GPU bulk embedding with FP32 storage; parity remains an explicit promotion gate.

## Dependencies and current state
006 accepted; live model claims depend on 004. Strategy must inspect current GitHub/main/PRs/checks, preceding terminal resolution,
source/projection identities, runtime/authorization gates and dirty state. This draft has no
execution authority. Verify/split/revise it before final publication; never fabricate live fields.

## Allowed paths and scope
embedding.py, model manifest/config integration, jobs.py, tests/{unit,integration}/, scripts/qualification/embedding*, docs/embedding.md.
The activated order/active and this round's report are additional governed transcript paths.

## Non-goals
No unrelated features/refactors, edits to other projects, model/provider replacement, production
service actions, public exposure, real secret/corpus publication, release/tag/deploy or automated
merge by coding. Live hardware/model access is NOT authorized by a draft or by installed keys.

## Acceptance criteria
1. Pinned checkpoint/tokenizer/official CLS pooling/L2/text template define one embedding space; mismatches refuse.
2. Online queries request CPU FP32; corpus defaults to exclusive GPU FP16 with FP32 normalized stored vectors.
3. Interrupted batches resume completed unchanged chunk IDs/checksums without duplication; parent/policy changes invalidate work.
4. Precision parity compares cosine/rank/Recall@k and cannot be waived by equal vector dimensions or fake-model tests.

## Verification and negative evidence
Fake encoders prove device contracts/resume/invalidation/corrupt vector handling; run authorized real EMBED-01/02 or retain NOT RUN gate.
Use focused local checks; record exact command/result and mock/live distinction. No skipped,
missing, pending or blocked check is a pass. Failures/limits must appear in the immutable report.

## Documentation
Document model acquisition authority, space fingerprint, parity report and fallback behavior.

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
