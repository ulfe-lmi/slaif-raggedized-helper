# OAP Work Order — 009-v

Status: FINAL
Identifier: 009-v
PR mode: AMEND_EXISTING_PR
Branch: oap/009-evaluation-baseline
Base commit: 851a1e29870771a0bc68a276a8cd5329d207b305
PR number: 11
Expected active: 009-u
Provenance: H activated MVP, A ARCH13.3–13.4/A23/A24, E bounded filesystem selection and wire-byte capture absent from canonical PR, I exact capture lane and final hosted 009-u review
Architecture SHA256: 4b41905396a3838269fd6cf372614cd23cb2c3b6a37be09f29ed752803c0983a
Governance SHA256: 24cec23235e3defc5f55bab4690298191d5a233d35dd9bf20b0afb4b3925f922

## Objective

Transfer the exact reviewed private policy selection reread and selected
wire-byte capture implementation. Preserve its existing descriptor
ownership, namespace, deadline and refusal proofs and original archive.

## Dependencies and current state

PR 11 open and non-draft with base main
`5a7b41cc512cf883b5b2cb92d87554b4d24e685b`. The exact 009-u report-only
head is the base above. Run 44724323631 attempt 1 passed all five jobs
and all steps. Each Product leg passed 3,015 units (A 1,421, B 1,594)
and a separate 951-case integration run. Both finished within the former
20-minute limit. The 30-minute finite bound remains the current setting.
Prior wall-time variance remains unproven. Root terminal review SHA256
`d9884ce372967de653db718c59866583554429f96862146f44bc6d1c68d84d24`.

Use the exact shared strategic files below.

- `workorders/009-v-capture-transfer-index.json` SHA256
  `de87eba313553561b2709f2c6fb051663fda2475a7d9fbca832ee7c91eda7ab2`.
  It freezes capture implementation, original report and receipt,
  indexed mode/path/blob/bytes, destination and inherited selection
  and publisher preimages.
- `workorders/009-v-prior-resolution.json` SHA256
  `25e4d59bbc73d8f017df15429e632bdf27879230df4901819ffb4dac91cb24c6`.
  Use the already consumed regular 009-u response and recorded hosted
  terminal review for provenance.

## Allowed paths and scope

Canonical CODING pane %30. The transcript contains four exact Root
paths, `oap/active` with `009-v` + LF, the unchanged order under
`oap/orders/`, and the two files above copied exactly under `oap/reviews/`
by basename. The implementation may add only the indexed source module,
new focus suite, original lane order, and original SELF report at
`oap/provenance/009-v/PAR-009-PRIVATE-POLICY-CAPTURE-A.json`.
Add cumulative notes only to `STATUS.md` and `docs/evaluation.md`.
The report is the sole addition in its own SELF child.

## Non-goals

Preserve prior product paths, selection and publisher code, current CI
settings and scopes, package lock, reports and governance. Keep actual
wire decoding/matching through a protected request, writer/generation
policy, current principal, credentials, actual pin/catalog, data rights,
model, engine, publisher dispatch and delivery outside this transfer.
Use temporary synthetic private roots only. No lane history import,
cherry-pick, force push, merge, new PR or release.

## Acceptance criteria

1. Verify canonical branch/base, unique PR/main, the exact prior report
   and adopted hosted review, receipt, and pre-authorized transcript
   bytes. Admission requires two exact inherited dependency blobs and
   all four indexed destination paths absent at the round base.
2. Inspect the original exact capture implementation and report-only
   parent, consumed local receipt and Root resolution. Copy the three
   payload blobs and original archived report verbatim, with the indexed
   mode, length, SHA256 and Git blob OID. Preserve historical SELF as
   the original report identity. Verify actual receiving blob bytes and
   allowed path scope before and at the new immutable implementation.
3. Use one targeted Ruff check on the new two Python files and one
   selected pytest invocation of `tests/unit/test_private_policy_capture.py`
   and `tests/unit/test_policy_selection.py`. Verify candidate imports
   originate in the canonical checkout. Expect 71 new tests and 47
   inherited selection tests, total 118. Keep actual bounded fixture,
   raw outputs, exit and any setup/verification failure. No repacking
   or editing accepted bytes in response to a local failure.
4. Publish the exact transcript, its sole implementation child and one
   report-only immutable child. For both Product legs Root requires
   expected A 1,421, B 1,665, total 3,086 units, separate full
   integration and every subsequent and OAP check. Counts are
   projections until measured. No full transfer or qualification
   acceptance flows from publication alone.

## Verification and negative evidence

Use canonical installed locked `.venv` and a fresh private 0700
directory under `/tmp` with admissible ancestry. Use scoped
`OPENBLAS_NUM_THREADS=1`, `PYTHONDONTWRITEBYTECODE=1`, private pytest
basetemp and disabled cacheprovider. Bound each proof invocation by
`timeout -k 5 120 prlimit --cpu=60 --as=1073741824`. For Ruff, the prior
verified one-core process-local affinity is permitted under the same
ceiling. Origin check may use the existing interpreter under those same
limits. No full local unit or integration suite, package installation,
unchanged retry, broader resource scope, or cap raise. Preserve failures.

## Documentation

Add brief cumulative STATUS and evaluation observations covering the
selected identity and opaque wire bytes, bounded owner, exact archival
provenance, actual local proof and pending fresh CI. Preserve the
representative baseline NOT_RUN and 009 PARTIAL. Real protected runtime
and operator current-authorization qualification remain open.

## Runtime and protected resources

Synthetic ephemeral filesystem only. No real service, workspace data
other than exact source/receipts, protected roots, credentials, models,
corpora, GPU or deployment. No new reader, direct FIFO access, prior
signal replay, or remote writes outside the one existing branch push.

## Deferred human adjudication

- Decision: NONE

## Publication and report

Same PR 11 and one ordinary push. Publish the exact report at
`oap/reports/009-v-private-policy-capture-transfer.md`. Include actual
commands, original local report/receipt identities, bytes and bounds,
failure history and current exact hosted CI pending. Once the remote
report is verified, use only the existing owned strategic helper
`send-response.sh --identifier 009-v --timeout 10`, then quiesce.
