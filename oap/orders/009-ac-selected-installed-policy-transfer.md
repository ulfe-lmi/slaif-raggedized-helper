# OAP Work Order — 009-ac

Status: FINAL
Identifier: 009-ac
PR mode: AMEND_EXISTING_PR
Branch: oap/009-evaluation-baseline
Base commit: 8f1ba9aa38f38cffc3d8a9adc66ea1a7bbfa1459
PR number: 11
Expected active: 009-ab
Provenance: H activated MVP, A ARCH 13.3–13.4, E immutable payload installer leaves the current selector untouched, I reviewed selected-writer seam and exact owned candidate
Architecture SHA256: 4b41905396a3838269fd6cf372614cd23cb2c3b6a37be09f29ed752803c0983a
Governance SHA256: 24cec23235e3defc5f55bab4690298191d5a233d35dd9bf20b0afb4b3925f922

## Objective

Transfer the independently reviewed private installed-policy selector
and its synthetic regression suite byte-exact. It updates an existing
selector using already installed admissible bytes under the one shared
root writer lock. This transfer establishes the bounded synthetic
selection component and preserves the separate immutable payload installer.

## Dependencies and current state

Unique open non-draft PR 11 on main
`5a7b41cc512cf883b5b2cb92d87554b4d24e685b`. The accepted 009-ab
report at the exact base above passed run 44796492067 attempt 1 with
all five jobs and every required step, each Product at 3,370 ordered
units and 957 separate integration cases.

Resolve the following files under
`/home/janezp/codex-supervision/slaif-raggedized-helper`.

- `workorders/009-ac-selected-installed-policy-transfer-index.json` SHA-256
  `711bf2b8851b81e889e3837c0941c0e06e8479a2e0800c4468f3e8781257e2dc`.
- `workorders/009-ac-prior-resolution.json` SHA-256
  `d6448b4fa86a6e1355fbffc20281752c41277895f67b2812f72a0cd1ebb426ba`.
- `audit/009-select-installed-policy-local-resolution.json` SHA-256
  `8822091c998b5d96b329ddf64d146483b40bda89cf90eac247f692d614ce9c11`.
- `audit/009-ab-check/Root-terminal-review.json` SHA-256
  `7b69c35334dae037691b1b119212cf660813ac715af8e204d983dafbd2a8aed5`.

## Allowed paths and scope

Canonical CODING pane %30. The first transcript commit contains
`oap/active` with `009-ac` plus LF, this exact order under
`oap/orders/`, and the exact two indexed strategic control JSON
files by basename under `oap/reviews/`.

A separate implementation commit adds only the exact new
`src/slaif_raggedized_helper/private_policy_selection.py`,
`tests/unit/test_private_policy_selection.py`, its original
`oap/parallel/orders/PAR-009-SELECT-INSTALLED-POLICY-A.md`, and
`oap/provenance/009-ac/PAR-009-SELECT-INSTALLED-POLICY-A.original.json`
with the exact original SELF report. Also update `STATUS.md` and
`docs/evaluation.md` with concise cumulative notes.

## Non-goals

Keep caller-facing policy admission, payload installation, private
retrieval, evaluation and publication behavior outside this transfer.
Real root initialization, protected recovery, source rights and baseline
qualification remain separate gates.

## Acceptance criteria

1. Reconcile the terminal prior report and regular receipt, exact
   remote head and main, unique PR, clean source lane, one
   implementation parent and sole report-only SELF child. Check
   indexed object modes, Git object IDs, byte counts and SHA-256.
   Confirm the four destinations absent and every indexed receiver
   preimage exact. Stop on a concrete mismatch.
2. Copy the four exact blobs. Preserve existing dependencies, the
   publisher and payload installer, prior hybrid code/tests and the
   workflow and CI partition. Do not regenerate or edit the source
   report. Cite Root's raw reconciliation for the omitted Ruff line
   and inaccurate repeated origins line. Preserve the historical
   bounded and excluded failure evidence.
3. Run the single scoped canonical local proof below. Record real
   exits, exact inputs, synthetic witness boundaries, commands and
   raw proof locators. Preserve actual first failure, if any. Preserve
   separate stage, descriptor and observed publication states under
   ambiguity and root association loss.
4. Exact report-head hosted gate requires A 1,440 and B 1,998,
   totaling 3,438 ordered units per Product (68 new B cases), plus
   957 separate integrations each. The other three OAP jobs, both
   Products and every previous required step must pass. Root owns
   that fresh review. Pending jobs are pending at report authoring.

## Verification and negative evidence

One bounded focus with these exact paths under `tests/unit/`.

- `test_private_policy_selection.py` (68)
- `test_private_policy_payload.py` (62)
- `test_private_policy_capture.py` (71)
- `test_private_report_publication.py` (89)

Expect 290 total. Run one targeted Ruff on the two copied Python
files on one allowed local core and one bounded physical import-origin
probe for `private_policy_selection`, `private_policy_payload`,
`private_policy_capture`, `private_report_publication`,
`policy_selection` and `supplied_policy_wire`. Use the existing
canonical `.venv`, physical canonical `src`, fresh 0700 scratch
directly under sticky `/tmp`, private pytest basetemp, raw logs outside
basetemp, `-o addopts= -p no:cacheprovider`, and
`OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1`. Use
`timeout -k 5 120 prlimit --cpu=60 --as=1073741824` on all
process proofs including Ruff and origins. Capture actual status
without pipeline masking. No full local suite or repeated unchanged
proofs, native setup, or live baseline.

## Documentation

Record the isolated artifact identities, operating cuts, no automatic
rollback, and reserved-stage availability limitation across restart.
Keep runtime/model, rights, real operator initialization and recovery,
guarded encoding and protected delivery, and representative evaluation
gates open. Whole 009 PARTIAL and baseline NOT_RUN.

## Runtime and protected resources

Use existing canonical and read-only candidate checkouts, isolated
owned synthetic fixtures, configured CI, and the same private PR.
No real policy roots, credentials, hardware, outside installs,
environment changes, branch merge/cherry-pick, new PR, release, deploy
or direct FIFO access.

## Deferred human adjudication

- Decision: NONE

## Publication and report

One normal push to the same PR of the exact transcript, implementation
and the sole-parent report-only SELF child
`oap/reports/009-ac-selected-installed-policy-transfer.md`. Record
exact active, order, dependencies, archived provenance, actual local
proof and pending hosted check. Verify actual publication through
the existing helper. Call `send-response.sh --identifier 009-ac --timeout 10`
once, then quiesce for the Root review.
