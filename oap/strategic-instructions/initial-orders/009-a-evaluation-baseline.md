# OAP Work Order — 009-a

Status: DRAFT UNTIL STRATEGIC RECONCILIATION
Identifier: 009-a
PR mode: CREATE_NEW_PR
Branch: oap/009-evaluation-baseline
Base commit: UNRESOLVED_AT_ACTIVATION
PR number: NEW
Expected active: UNRESOLVED_AT_ACTIVATION
Provenance: A32 A33 A37
Architecture SHA256: UNRESOLVED_AT_ACTIVATION
Governance SHA256: UNRESOLVED_AT_ACTIVATION

## Objective
Implement evaluation harness and dataset split discipline, then evaluate raw lexical/dense/hybrid retrieval on available authorized representative data.

## Dependencies and current state
008 accepted; human pilot data/rights scope supplied for real baseline. Strategy must inspect current GitHub/main/PRs/checks, preceding terminal resolution,
source/projection identities, runtime/authorization gates and dirty state. This draft has no
execution authority. Verify/split/revise it before final publication; never fabricate live fields.

## Allowed paths and scope
evaluation/, eval/ synthetic example schemas only, tests/, docs/evaluation.md, docs/benchmarks/raw-baseline.md.
The activated order/active and this round's report are additional governed transcript paths.

## Non-goals
No unrelated features/refactors, edits to other projects, model/provider replacement, production
service actions, public exposure, real secret/corpus publication, release/tag/deploy or automated
merge by coding. Live hardware/model access is NOT authorized by a draft or by installed keys.

## Acceptance criteria
1. Gold original spans, acceptable/disallowed claims, ACL/version/language/answerability and split provenance are required.
2. Synthetic examples are labeled and cannot count as the required human-held-out set.
3. Recall@20/60, multi-source coverage, MRR/nDCG and candidate loss have tested independent oracles.
4. Published results include sample sizes/splits/scope and missing human data as a blocker, with no held-out tuning leakage.

## Verification and negative evidence
Known-rank metric fixtures, duplicate/split leakage detection, multilingual/version/ACL/unanswerable cases; real evaluation only under corpus rights authorization.
Use focused local checks; record exact command/result and mock/live distinction. No skipped,
missing, pending or blocked check is a pass. Failures/limits must appear in the immutable report.

## Documentation
Publish baseline methodology, data provenance, privacy handling and remaining quality gates.

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
