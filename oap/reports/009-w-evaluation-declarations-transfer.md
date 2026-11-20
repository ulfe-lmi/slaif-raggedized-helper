# OAP Coding Report — 009-w

Identifier: 009-w
Result: COMPLETE
Repository: ulfe-lmi/slaif-raggedized-helper
PR number: 11
Branch: oap/009-evaluation-baseline
Base branch: main
Implementation head SHA: fceb577e80b2e836a1a5d0d884fa6ba244e965f4
Report publication commit: SELF

## Work and scope

Order `oap/orders/009-w-evaluation-declarations-transfer.md`
(Status: FINAL, PR mode AMEND_EXISTING_PR, Decision: NONE) at round
base `0f24c91c1c04931ffbc3a82d896ce08afc816d05` (the verified 009-v
report-only head). Objective: transfer the exact accepted private
declaration-side binder, source cohort and grade preflight changes,
keeping the existing query-dependent admission and grade behaviors,
order, metering and report identity; the query-independent pieces
support later bounded orchestration before actual encoding.

History pushed in this round (no force push, no merge, one PR):

1. `f68234d21108bfaa08f741ce0eddb934a9a56277` (parent: round base)
   — exact Root transcript: `oap/active` (`009-w` + LF),
   `oap/orders/009-w-evaluation-declarations-transfer.md`,
   `oap/reviews/009-w-declaration-transfer-index.json` (SHA-256
   `34c34d715a24e8eef47a03d6d220aa718bb6c38157ca82d7185046db7103a5f2`),
   `oap/reviews/009-w-prior-resolution.json` (SHA-256
   `6c8cced1117f498ca3c9deb177c44758518f03870d79192631b1ae03d6ba4bb0`).
2. `fceb577e80b2e836a1a5d0d884fa6ba244e965f4` (parent: 1) —
   implementation: the three changed product preimages, the three
   new unit suites, the three original lane orders, the three
   original SELF archival reports in `oap/provenance/009-w/` and
   `STATUS.md` / `docs/evaluation.md` (14 paths total).
3. SELF — this report only; first parent is the implementation head.

## Acceptance evidence

1. Round-base and GitHub reconciliation. Local branch head and
   remote `oap/009-evaluation-baseline` were exactly
   `0f24c91c1c04931ffbc3a82d896ce08afc816d05`; live `main` was
   exactly `5a7b41cc512cf883b5b2cb92d87554b4d24e685b`. GitHub
   shows exactly one open non-draft PR: #11 on
   `oap/009-evaluation-baseline` → `main`, head
   `0f24c91c1c04931ffbc3a82d896ce08afc816d05`, state OPEN,
   MERGEABLE. The working tree before this round contained only the
   Root activation changes (`oap/active` modified to exactly
   `009-w` + LF, 6 bytes; the new order file untracked, byte-identical
   to the strategic workorder copy). The prior 009-v report bytes at
   the round base (`oap/reports/009-v-private-policy-capture-transfer.md`)
   match the prior resolution `report_sha256`
   (`fef468962f5b90b45004cf9351459d3d5acf389f5f538a4b6ff98b53eb6e6814`);
   the consumed 009-v regular response receipt
   (`.oap-state/response-consumed-009-v.json`) matches
   `559bebaae27f2f9ec710d7078f6e9b472a5f90b8da13c920bb74161584168582`;
   the adopted hosted terminal review
   (`audit/009-v-check/Root-terminal-review.json`) matches
   `fd1c6a5cd0492b052d1492973479523c0b0efdb1d9133f7054d1e336062eb905`;
   both strategic source hashes match the order
   (ARCHITECTURE.md `4b41905396a3838269fd6cf372614cd23cb2c3b6a37be09f29ed752803c0983a`,
   oap/governance/MANIFEST.json
   `24cec23235e3defc5f55bab4690298191d5a233d35dd9bf20b0afb4b3925f922`).
   All three existing source preimages were present at the round
   base with their ordered SHA-256:
   `source_bound_stage_loss.py` (`168fca4b151c01c89a66ac1fe50d907758fe8402ea24c0c30303a9aea92773b8`),
   `source_cohort_runner.py` (`d9f1b0e8f748be9c5b32b6e6d45e8228ace43b397517a41e6187638d4c296faf`,
   byte-identical at the cohort lane base cacc5b36) and
   `evaluation_program.py` (`84aceffc09ec7e53fcf96913ad0cb409616b31223d71915e60fbd750300b9b90`);
   all six additive payload paths and the three archive
   destinations (plus `oap/provenance/009-w/` itself) were absent at
   the round base.
2. Indexed object verification. Each original candidate was
   verified: the binder implementation
   `cacc5b362574638e09862a0d82e14e53bd1abef1` has
   `416009c94a6759c9a42e9c19dab688c0f54d9650` as its sole base;
   the cohort implementation
   `ab832488600088b6717d4a4d59758495e91a7dc9` has the exact
   accepted binder implementation cacc5b36 as its sole parent
   (the ordered dependency, with report_self 63e36735 and the
   binder resolution
   `77d25a57fc3403bc34f7b5267ea3c3d562aec65ec8f978ca58a14c69a630937f`);
   the grade implementation
   `d052c3c978a7b97b18eb5580a6ffe04692bdde4f` has
   `dfe301c7c5796dc6de2bf8309f885dfc3b1cd2af` as its sole base.
   Each original report-only child has the implementation as sole
   parent and touches exactly its one report path:
   `63e36735376e72e64abf239ba4d77d518c72731f` →
   `oap/parallel/reports/PAR-009-ENCODER-DECLARATION-PREFLIGHT-A.json`,
   `00940a6def4bf03c779fae8c4a0949402960f4bf` →
   `oap/parallel/reports/PAR-009-COHORT-DECLARATION-PREFLIGHT-A.json`,
   `66f0c98a3fa561f406cdf2d993ba094cda3468ad` →
   `oap/parallel/reports/PAR-009-GRADE-DECLARATION-PREFLIGHT-A.json`.
   The three Root resolutions match their ordered SHA-256 (binder
   `77d25a57…`, cohort `c29a937c1e6fbef48a12698cb935d380465d120ea02a64b4220831b796dd1c9c`,
   grade `e51177e12a2b6d57ddea3402ac3d717ce71eea4250d6e4e98a7f199398eef817`)
   and the three consumed lane receipts match (encoder
   `65f494c8886ecb1f96b8a97d1d08e4d30796ed1c53d37467392c341fd6de1d89`,
   cohort `55649af55e789c6053bd68b1f72f4fe57b3bf3df5b8fb57542d4906666843749`,
   grade `bc972b7c0c1843fb03cf9d7691008d556e5c80d27686b2bc39456372b3109ff1`).
   All twelve indexed paths were verified at their exact source
   commits (mode 100644, full size, SHA-256, Git blob OID):
   `source_bound_stage_loss.py` (91,797 B,
   `caf22819c1148dd3dcadf368904fdd4f98475451ff2f0c50fc7e51caa37fe546`,
   blob `85c7ce3c`), `test_source_bound_stage_loss_preflight.py`
   (9,051 B, `cc8a9c00c2466d60809f5630e533e549392b84f910e6961d81347149c923e6f5`,
   blob `9e33fadd`), encoder lane order (5,013 B,
   `dc98acb1dadc9d2c3990d5c9190d201bf8accb0e784f6b3a194894baf77c9042`,
   blob `988c5862`), encoder archival report (7,267 B,
   `d1a3a6647b1aae4dc1951a6902c9a954c37c8526c45d7e38e621f6aa81f86bda`,
   blob `dae9d2a6`), `source_cohort_runner.py` (49,662 B,
   `040f6813d6f2d5772392dca49daf57e6ba2b6b5a94fe3dd6bd5e7fd324b7580f`,
   blob `1664f813`), `test_source_cohort_declaration_preflight.py`
   (30,088 B, `126cac8862946742b1429367308daeb443643df49dece85a5838af3058fed21e`,
   blob `8c7b2fac`), cohort lane order (5,144 B,
   `ac4684085b0e700303d89957351c04598b2031e8a94063cdb310f332024ffcfd`,
   blob `ee18b6c3`), cohort archival report (12,019 B,
   `cbaeabf00af20ed75c95322108fb97d6b6da033c28f3dab3bf993cafcd176cd4`,
   blob `dc24247c`), `evaluation_program.py` (34,416 B,
   `fc00a26059e73f9c5d1f35354b7d22b57bb76a73697b0e2ee5c6f92728d2474d`,
   blob `63581446`), `test_evaluation_grade_preflight.py` (23,010 B,
   `524325d12033581bcda67a7f1f9c7457df17fbd2ec922454148f2662c9ebdc12`,
   blob `476e50cc`), grade lane order (4,586 B,
   `95cdc21579cc2b51e794afc7b783a91796ef0b87a7fcfc30d4ec44582d8a52c4`,
   blob `2a25ee73`) and grade archival report (8,207 B,
   `ed6bd81db938537c264a7377baa3f2fecf2a89cc11d5fde6b588676d873d8eeb`,
   blob `770f59de`). All twelve were re-verified mode/size/SHA-256/
   blob OID at the receiving working-tree paths before commit and
   again at the implementation head (12/12 match); the historical
   original SELF markers are preserved unchanged (each archival
   report keeps its own lane `result: COMPLETE`,
   `implementation_head` and `report_publication_commit: SELF`).
   The committed diff scope from the round base to the
   implementation head is exactly the four transcript paths plus
   the fourteen implementation paths; the original old-path
   behavior witnesses are the ten inherited parameterized nodes
   executed in item 3 (legacy binder payload gate, legacy cohort
   query flow and legacy grade budget/refusal behavior). No drift
   was found, so the stop-on-drift condition never triggered.
3. Local proofs (all synthetic, offline, locked .venv Python
   3.14.4 / pytest 8.4.2 / ruff 0.17.4, fresh private 0700 scratch
   under /tmp, `OPENBLAS_NUM_THREADS=1`,
   `PYTHONDONTWRITEBYTECODE=1`, private `--basetemp`,
   cacheprovider disabled; each invocation bounded by
   `timeout -k 5 120 prlimit --cpu=60 --as=1073741824`):
   - One targeted ruff check on the six changed Python files
     (`taskset -c 0` one-core affinity with `RAYON_NUM_THREADS=1`
     under the same cap): exit 0, "All checks passed!".
   - One combined focused pytest invocation of the three indexed
     new unit files plus the eight exact inherited selectors
     (addopts reset to preserve the summary, `--tb=long`):
     exit 0, `collected 58 items`, `58 passed in 0.99s` — exactly
     58 = 48 new (8 + 21 + 19) + 10 inherited parameterized nodes
     (1 binder, 4 cohort, 3 evaluation program).
   - One bounded origin check (same bounds): exit 0 — all three
     imported product modules (`source_bound_stage_loss`,
     `source_cohort_runner`, `evaluation_program`) resolve to the
     canonical repository `src/` with the exact indexed
     SHA-256/size.
   No setup or verification failure occurred; no concrete failure
   is retained for Root, no accepted transfer byte was changed, and
   no repacking, edits or retries were needed.
4. Git scope. Exactly four Root transcript paths, the
   implementation-only fourteen-path scope above, then this one
   report-only commit naming the implementation as its sole first
   parent. Prior report bytes, the ordered unit process shape and
   all earlier tests are unchanged (verified at the implementation
   head). Expected counts at the new report head (expected until
   measured): group A 1,440, group B 1,694, total 3,134 units,
   plus the unchanged complete integration (951 cases) and every
   downstream step, with all OAP jobs; 009 stays PARTIAL with
   baseline NOT_RUN. No full transfer or qualification acceptance
   flows from publication alone.

## Verification

Commands and outcomes are the exact bounded invocations listed in
acceptance item 3 (raw streams preserved in the private 0700
scratch `/tmp/oap-009-w-proof.Oz4rAn`). All product test evidence
is synthetic/offline: the three declaration suites exercise owned
temporary roots, generated bytes, meter/clock witnesses and
fault-injected refusals only; no network, keys, GPU, model
download or live route, no actual encoder, pin/catalog, publisher,
delivery, current-policy authentication or protected-runtime use.
The fresh full hosted comparison (both Product legs plus all OAP
jobs) at this exact report head is PENDING at report authoring; the
adopted prior hosted evidence is run 44731327493 attempt 1 (all
five jobs and all steps passed; both Product legs 3,086 units —
1,421 and 1,665 — plus the separate 951-case integration run). This
report does not certify its own push or that CI, and Root owns the
fresh CI and terminal review.

## Documentation impact

`STATUS.md`: current slice advanced 009-v → 009-w and one
cumulative 009-w entry added (three-component scope, adopted
009-v hosted evidence, preserved original SELF provenance, old and
new synthetic behavior, actual local proof, pending exact-head CI,
expected counts, open gates). `docs/evaluation.md`: new 009-w
section before the preserved input-contracts section with the same
content. Both preserve the representative baseline NOT_RUN and
whole 009 PARTIAL, and state that the open governed operator, the
real representative baseline, source rights and model gates remain
open. All historical sections preserved.

## DHA and boundaries

Decision: NONE. No critical entry appended or modified. Preserved:
the canonical locked .venv (no installation or upgrade), all prior
reports/reviews/orders bytes, the lane worktree history, unrelated
branches and worktrees. No merge, no new PR, no force push, no
tag/release/deploy, no model/provider/profile change.

## Limitations and deviations

The ordered unit counts (A 1,440, B 1,694, total 3,134) are
projections until the fresh hosted run measures them; the prior
wall-time variance remains unproven until observed. No local full
unit or integration suite was run, per the order. No deviations
from the ordered scope occurred.

## No merge

No merge performed or requested; PR 11 remains open and
non-draft. Baseline NOT_RUN; whole 009 PARTIAL; DHA NONE.
