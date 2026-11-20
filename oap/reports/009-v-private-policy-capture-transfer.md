# OAP Coding Report — 009-v

Identifier: 009-v
Result: COMPLETE
Repository: ulfe-lmi/slaif-raggedized-helper
PR number: 11
Branch: oap/009-evaluation-baseline
Base branch: main
Implementation head SHA: c4f2450f8ac5b42b9b4a6c3a615fabbc25fb7ee1
Report publication commit: SELF

## Work and scope

Order `oap/orders/009-v-private-policy-capture-transfer.md`
(Status: FINAL, PR mode AMEND_EXISTING_PR, Decision: NONE) at round
base `851a1e29870771a0bc68a276a8cd5329d207b305` (the verified 009-u
report-only head). Objective: transfer the exact reviewed private
policy selection reread and selected wire-byte capture
implementation, preserving its existing descriptor ownership,
namespace, deadline and refusal proofs and its original archive.

History pushed in this round (no force push, no merge, one PR):

1. `279de6e786dbe80f8d9430fda0d99f91543e0f97` (parent: round base)
   — exact Root transcript: `oap/active` (`009-v` + LF),
   `oap/orders/009-v-private-policy-capture-transfer.md`,
   `oap/reviews/009-v-capture-transfer-index.json` (SHA-256
   `de87eba313553561b2709f2c6fb051663fda2475a7d9fbca832ee7c91eda7ab2`),
   `oap/reviews/009-v-prior-resolution.json` (SHA-256
   `25e4d59bbc73d8f017df15429e632bdf27879230df4901819ffb4dac91cb24c6`).
2. `c4f2450f8ac5b42b9b4a6c3a615fabbc25fb7ee1` (parent: 1) —
   implementation: the four indexed payload destinations and
   `STATUS.md` / `docs/evaluation.md` (6 paths total).
3. SELF — this report only; first parent is the implementation head.

## Acceptance evidence

1. Round-base and GitHub reconciliation. Local branch head and
   remote `oap/009-evaluation-baseline` were exactly
   `851a1e29870771a0bc68a276a8cd5329d207b305`; live `main` was
   exactly `5a7b41cc512cf883b5b2cb92d87554b4d24e685b`. GitHub
   shows exactly one open non-draft PR: #11 on
   `oap/009-evaluation-baseline` → `main`, head
   `851a1e29870771a0bc68a276a8cd5329d207b305`, state OPEN,
   MERGEABLE. The working tree before this round contained only the
   Root activation changes (`oap/active` modified, the new order
   file untracked). `oap/active` bytes are exactly `009-v` + LF
   (6 bytes); the order file is byte-identical to the strategic
   workorder copy (SHA-256
   `70d8e0676c85207747e85ed5289b8509fa52380f73224159c65b51e21ff9c3c4`);
   both strategic files match their ordered SHA-256. The prior
   009-u report bytes at the round base
   (`oap/reports/009-u-product-ci-job-limit.md`) match the prior
   resolution `report_sha256`
   (`a3d43e72239a5426442504162e40af5d05e523c81fe55526ffe88111d846c12e`);
   the consumed 009-u response receipt
   (`.oap-state/response-consumed-009-u.json`) matches
   `afaaa6d72a4e038643a37320b2764daf46c3006560b8798d8d2076b6e2b741cf`;
   the adopted hosted terminal review
   (`audit/009-u-check/Root-terminal-review.json`) matches
   `d9884ce372967de653db718c59866583554429f96862146f44bc6d1c68d84d24`;
   the consumed lane receipt
   (`parallel/private-policy-capture/response-consumed.json`)
   matches `c0926e750b270bec983ccd71c2b9254569047645651eb61b626c6828fc5c11ae`;
   the draft source index matches
   `87de47e9f8a594d0ca6f234b6a68ea6dce9333d9325079edf511dd6efed1849b`;
   the lane local resolution matches
   `0b34f4e60f556fb09a0c189baad3867f0e7a4e496bf389cf884bc915f9e1a9c4`.
   The two inherited dependency blobs at the round base are
   byte-identical: `policy_selection.py` (2,526 B,
   `eda878a12af9f141b6f9cd48ccec5601932201f9b36baa31fa17fe28659bde87`)
   and `private_report_publication.py` (28,170 B,
   `43207d97f4c195966049cf53bf45c1b47543277dbf95b0bb7068a8a734378e34`);
   all four indexed destination paths were absent at the round
   base.
2. Indexed object verification. The original exact capture
   implementation commit `6e8922c6a35de57ed19a70ed3a5aca59e4b7a68a`
   has `b0bd2821872e2ee82c98a85d9df509e616c8c642` as its sole base;
   the original report-only commit
   `ff876ee785051872df1552b4d9f8f0d68f9c4d99` has the
   implementation as sole parent and touches exactly its one report
   path. All four source blobs were verified at their exact commits
   (mode 100644, size, SHA-256, Git blob OID):
   `private_policy_capture.py` (14,974 B,
   `4d0c3b8002c6c4fabe3c3be3a08d851375249ad2fb807260f56e5fa9e3e7f0fc`,
   blob `68941f04`), `test_private_policy_capture.py` (37,256 B,
   `bb1fccfeddf28c8ecba464fa4f392e6b830f2fc07291a44a65978b19b670f7b9`,
   blob `3c7e2b5b`), the original lane order (5,807 B,
   `f53de63dce3a4dfbd1e0dc0b8962c832fc9cd46502c38016edadf58c7be0b720`,
   blob `6810043f`) and the original lane report-only SELF archival
   report (10,890 B,
   `02cfe227eba7c7ea705a7c7545ebf66c117c74fb7c8d3387f6545b4164321689`,
   blob `4150d6e9`). The original SELF report is preserved verbatim
   at `oap/provenance/009-v/PAR-009-PRIVATE-POLICY-CAPTURE-A.json`
   with its historical SELF identity intact (`result: COMPLETE`,
   `implementation_head: 6e8922c6…`, `report_publication_commit:
   SELF`, review decision REPORT). Each blob was verified at the
   receiving working-tree paths before commit and again at the
   implementation head `c4f2450f…` (4/4 mode/size/SHA-256/blob OID
   match; the two inherited blobs byte-unchanged at the head; the
   diff from the round base to the implementation head touches
   exactly the ten transcript-plus-implementation paths).
3. Local proofs (all synthetic, offline, locked .venv Python
   3.14.4 / pytest 8.4.2 / ruff 0.17.4, fresh private 0700 scratch
   under /tmp, `OPENBLAS_NUM_THREADS=1`,
   `PYTHONDONTWRITEBYTECODE=1`, private `--basetemp`,
   cacheprovider disabled; each invocation bounded by
   `timeout -k 5 120 prlimit --cpu=60 --as=1073741824`):
   - One targeted ruff check on the two new Python files
     (`taskset -c 0` one-core affinity with `RAYON_NUM_THREADS=1`
     under the same cap): exit 0, "All checks passed!".
   - One selected pytest invocation of
     `tests/unit/test_private_policy_capture.py` and
     `tests/unit/test_policy_selection.py` (`-q --tb=long`):
     exit 0, exactly 118 progress dots (72 + 46) and no failure or
     error markers — the expected 118 = 71 new + 47 inherited.
     Note: the repository `addopts = -q` plus the invocation `-q`
     suppress the final summary line in pytest 8.4.2 (confirmed
     with a throwaway single-test harness under identical bounds);
     the preserved raw output is therefore exactly 160 bytes of
     progress dots. This is a harness output observation, not a
     product failure; no product byte was touched by it.
   - One bounded origin check (existing interpreter, same bounds):
     exit 0 — all three product modules imported by the candidate
     (`private_policy_capture`, `policy_selection`,
     `private_report_publication`) resolve to the canonical
     repository `src/` with the exact indexed SHA-256/size.
   No setup or verification failure occurred; no repacking, edits
   or retries were needed.
4. Git scope. Exactly four Root transcript paths, the
   implementation-only six-path scope above, then this one
   report-only commit naming the implementation as its sole first
   parent. Prior report bytes, the ordered unit process shape and
   all earlier tests are unchanged (verified at the implementation
   head). Expected counts at the new report head (expected until
   measured): group A 1,421, group B 1,665, total 3,086 units,
   plus the separate full integration and every subsequent and OAP
   check; 009 stays PARTIAL with baseline NOT_RUN. No full
   transfer or qualification acceptance flows from publication
   alone.

## Verification

Commands and outcomes are the exact bounded invocations listed in
acceptance item 3 (raw streams preserved in the private 0700
scratch). All product test evidence is synthetic/offline: the
capture suite exercises owned temporary roots, generated bytes and
fault-injected descriptor witnesses only; no network, keys, GPU,
model download or live route, and no actual current-auth
invocation, protected policy service, real credential or
protected-runtime use. The fresh full hosted comparison (both
Product legs plus all OAP jobs) at this exact report head is
PENDING at report authoring; the adopted prior hosted evidence is
run 44724323631 attempt 1 (all five jobs and all steps passed; both
Product legs 3,015 units — 1,421 and 1,594 — plus the separate
951-case integration run, both within the former 20-minute limit),
and prior wall-time variance remains unproven. This report does not
certify its own push or that CI, and Root owns the fresh CI and
terminal review.

## Documentation impact

`STATUS.md`: current slice advanced 009-u → 009-v and one
cumulative 009-v entry added (four-payload scope, adopted 009-u
hosted evidence, preserved original SELF provenance, selected
identity and opaque wire bytes, bounded owner, actual local proof,
pending exact-head CI, expected counts). `docs/evaluation.md`:
new 009-v section before the preserved input-contracts section
with the same content. Both preserve the representative baseline
NOT_RUN and whole 009 PARTIAL, and state that the real protected
runtime and operator current-authorization qualification remain
open. All historical sections preserved.

## DHA and boundaries

Decision: NONE. No critical entry appended or modified. Preserved:
the canonical locked .venv (no installation or upgrade), all prior
reports/reviews/orders bytes, the lane worktree history, unrelated
branches and worktrees. No merge, no new PR, no force push, no
tag/release/deploy, no model/provider/profile change.

## Limitations and deviations

The ordered unit counts (A 1,421, B 1,665, total 3,086) are
projections until the fresh hosted run measures them; the prior
wall-time variance and the 30-minute bound's effect remain
unproven until observed. The double-quiet pytest summary
suppression is disclosed above; the 118-test expectation is
verified by the exact dot count and by the byte-identical source
files' preserved lane provenance (71 + 47). No local full unit or
integration suite was run, per the order.

## No merge

No merge performed or requested; PR 11 remains open and
non-draft. Baseline NOT_RUN; whole 009 PARTIAL; DHA NONE.
