# OAP Coding Report — 009-aa

Identifier: 009-aa
Result: COMPLETE
Repository: ulfe-lmi/slaif-raggedized-helper
PR number: 11
Branch: oap/009-evaluation-baseline
Base branch: main
Implementation head SHA: 8113a998f1c15c48168c740cc5173a5959a0a2ad
Report publication commit: SELF

## Work and scope

Order `oap/orders/009-aa-joint-and-current-pin-transfer.md` (FINAL;
AMEND existing PR 11; Decision: NONE; order file SHA-256
`0542fca1d9734bd73cda49a5a95bdb7436f1f8e14468c056c2eaa40bd030d60f`)
at round base `ca8e9c8a98281ba8e426788459ff40a694bae020` (the
accepted 009-z report-only head). Objective: transfer the two exact
independently reviewed private prerequisites — the joint evaluation
declaration preparation and the current-policy borrowed-pin
eligibility observation — verbatim into the canonical PR, preserving
the existing public entry points; the accepted artifacts do not
connect evaluation execution to either entry.

History published in this round (one regular push to the same PR
branch, no force push, no merge, one PR):

1. `f7e6350a62ffea9df10be4069a797dbe06344a5b` (parent: round base
   `ca8e9c8a`) — exact Root transcript, four paths: `oap/active`
   (`009-aa` + LF, 7 bytes),
   `oap/orders/009-aa-joint-and-current-pin-transfer.md` (the FINAL
   order above), `oap/reviews/009-aa-joint-and-current-pin-transfer-index.json`
   (byte-exact copy, SHA-256
   `9bd1da70a5cf37a91b90d6c11f4f16dc8c791eb91ab46736c686b2a58ddd35e4`,
   16,828 B) and `oap/reviews/009-aa-prior-resolution.json`
   (byte-exact copy, SHA-256
   `dbc5d5006a6073aa0473218ccdcf56f33a4a2def442b4e5ffbed20fa1d8c3d8b`,
   1,724 B).
2. `8113a998f1c15c48168c740cc5173a5959a0a2ad` (parent: 1) —
   implementation: the eight transferred objects plus cumulative
   `STATUS.md` and `docs/evaluation.md` notes (10 paths total).
3. SELF — this report only; first parent is the implementation head.

## Reconciliation at activation

- GitHub: main exactly `5a7b41cc512cf883b5b2cb92d87554b4d24e685b`;
  unique open non-draft PR 11, OPEN/MERGEABLE, head
  `oap/009-evaluation-baseline` at `ca8e9c8a` on base main; local
  HEAD and round base equal. Required run 44775148168 attempt 1 at
  the round base: passed all five jobs and every step, both Products
  at 3,275 ordered units (1,440 A plus 1,835 B) and 951 integration
  cases each, per the bound prior resolution.
- The two control files were read at their exact strategic paths
  under `/home/janezp/codex-supervision/slaif-raggedized-helper` and
  matched the order's pinned SHA-256s. The terminal gate
  `audit/009-z-check/Root-terminal-review.json` (SHA-256
  `b170214e8e30313f054381e5317be1ffdd4e6892b1b6fd23b6731c7d7f15a331`,
  11,346 B) and the prospective ordered inventory
  `audit/009-aa-preview-inventory/Root-projection.json` (SHA-256
  `5dbce70c1ca6adbdd8e2ad6349bc1bc7d54369cfe9ccc8c625332d7da898630d`,
  1,189 B: focus 208, A 1,440, B 1,930, units 3,370, new 95,
  separate integration 951) were verified at their pinned hashes.
  The exact accepted predecessor 009-z report (commit `ca8e9c8a`,
  `oap/reports/009-z-current-view-and-encoder-transfer.md`, blob
  `2be2494f`, 10,870 B, SHA-256
  `1e85eecdc8a8c0c18daa02f5d96422f452ad992301c9b6ba6a2e7d080930b7d8`)
  and the consumed regular receipt
  `.oap-state/response-consumed-009-z.json` (346 B, SHA-256
  `48102fc5450b9a7b8fea61758fce880ae47c90e3849bbb7aede133464f424fe8`)
  were verified. The two consumed lane receipts
  (`parallel/joint-evaluation-declaration/response-consumed.json`
  713 B, SHA-256 `88b478485039ab967556b91e14889353720863d7b0176c3ebde1ab544e4ee59a`;
  `parallel/current-policy-pin-eligibility/response-consumed.json`
  723 B, SHA-256 `cbfaf227b443f3eedf0074c09dbac96ce4e9edbe81f61acf3bed7f9371c1dfbb`)
  and the two local Root resolutions
  (`audit/009-joint-evaluation-declaration-local-resolution.json`
  14,277 B, SHA-256 `9b88ff058d7765a72600d6e12e9a7d99355703e439bef795ec7595929b8fac4f`;
  `audit/009-current-policy-pin-eligibility-local-resolution.json`
  15,937 B, SHA-256 `aa3e48af3ad9fdb2b11114bbf14d19d0117ff0b5c7471e87d757e51fe204a713`)
  were verified at their indexed hashes. The configured workflow
  `.github/workflows/oap.yml` (14,235 B, SHA-256
  `54e66869d9a2a02e95202ed3eaecba199a2494ca6f6c5742554e722cf14367c6`)
  was verified at its bound hash.
- Unique lane report topologies verified: joint publication
  `cfb7ef41a14851530f4eefc173335aaebd5ec0e0` is a report-only
  single-parent commit over implementation `0a816ab06500c8b7090e3afbdae76e86ae788afa`;
  pin publication `dc28c0d242d899c4b03579019ad7e87357a84704` is a
  report-only single-parent commit over implementation
  `57d463a5d19b22059d9f0eaf4361ffe03ec91ab5`, whose ordered
  preparation head `9e6283fe554ebae8c93ea133765119622dca3a77` has
  tree `0279879f4a3aa87e6c448cad43261ffdb7bf19af` and exact merge
  parents `4b798897dcc3b6194eeda960046d0bf040747dfe` +
  `7f6190adf3d8092f2381505b45185db78db901d0`, as indexed. Both local
  lane worktrees (`slaif-raggedized-helper-parallel-joint-evaluation-declaration`
  at `cfb7ef41`, `slaif-raggedized-helper-parallel-current-policy-pin-eligibility`
  at `dc28c0d2`) are clean at those report heads.
- At the round base the report path and all eight destinations were
  absent in the tree and on disk.

## Transfer (eight objects, all mode 100644)

Lane 1, joint-evaluation-declaration — implementation
`0a816ab06500c8b7090e3afbdae76e86ae788afa` on effective base
`ed48ca58934b21003ba57d057be1a9921d666e1c`:

| destination | bytes | blob | SHA-256 |
|---|---|---|---|
| `src/slaif_raggedized_helper/private_evaluation_preflight.py` (new) | 7,140 | `20a41167` | `5ef16bec3a48fc497a147a5ddded156fa2a55ad6551fdc7fde82b3ce6aea60a6` |
| `tests/unit/test_private_evaluation_preflight.py` (new) | 37,427 | `f2899fd5` | `ae90709f1813ac4bdfb0e79152fe0fd3544eee1468c93acdd38c3ce7905bedb8` |
| `oap/parallel/orders/PAR-009-JOINT-EVALUATION-DECLARATION-A.md` (verbatim) | 5,825 | `224ab7a7` | `65ade514c1f961d198fa8ac917fb46558cc123422a74d8646b2323a2ed92e2ae` |
| `oap/provenance/009-aa/PAR-009-JOINT-EVALUATION-DECLARATION-A.json` (immutable lane SELF report, publication `cfb7ef41`) | 18,640 | `b974ed9d` | `e899bae105966be38a769afb2b3f14784493e040bbca7f7d472de06a316121dd` |

Lane 2, current-policy-pin-eligibility — implementation
`57d463a5d19b22059d9f0eaf4361ffe03ec91ab5` on the ordered
preparation head `9e6283fe554ebae8c93ea133765119622dca3a77`:

| destination | bytes | blob | SHA-256 |
|---|---|---|---|
| `src/slaif_raggedized_helper/private_policy_pin_eligibility.py` (new) | 19,591 | `05305412` | `a09c501656a6b39973bc5d4cae9a8e8e089ee1c39f95359f06c586a5be55dfb3` |
| `tests/unit/test_private_policy_pin_eligibility.py` (new) | 70,832 | `4ea14deb` | `afae35e211143d66bd647a8afb211555909c4590257d6a7a1898b9d3a6d75970` |
| `oap/parallel/orders/PAR-009-CURRENT-POLICY-PIN-ELIGIBILITY-A.md` (verbatim) | 6,376 | `f56d25d7` | `7523127383be53549d9f328c88a1abe58a14d92d67355e854ca4f9dbac11626c` |
| `oap/provenance/009-aa/PAR-009-CURRENT-POLICY-PIN-ELIGIBILITY-A.json` (immutable lane SELF report, publication `dc28c0d2`) | 35,496 | `f8bef0df` | `ea78972b03d5b8ae5b2fa59bdde8b848ff83e4d8dc1e6cc19a81cfde0cb5788e` |

Every row was verified at the exact source commits and at the
receiving working tree (and staged index) for Git mode, byte count,
SHA-256 and blob OID; the original immutable report `SELF` bytes are
preserved unchanged. No product code or test outside the indexed
copies changed.

## Preimage verification at the round base

All 27 indexed receiving preimages verified byte-exact (mode, blob,
size, SHA-256) at `ca8e9c8a`: lane 1 the
`source_cohort_runner.py`, `evaluation_program.py`,
`source_bound_stage_loss.py`, `evaluation_plan_wire.py` sources and
the `test_source_cohort_declaration_preflight.py`,
`test_evaluation_grade_preflight.py`, `test_source_cohort_runner.py`,
`test_evaluation_program.py`, `test_evaluation_plan_wire.py` suites;
lane 2 the actually inherited current-view files
`private_policy_request.py` (14,885 B) and
`test_private_policy_request.py` (42,773 B), the pin ownership
sources (`raw_snapshot_pin.py`, `raw_snapshot_directory.py`,
`raw_snapshot_files.py`, `raw_snapshot_manifest.py`,
`raw_snapshot_membership.py`, `raw_snapshot_query.py`,
`raw_snapshot_selection.py`), `provenance_records.py`,
`raw_lexical_search.py`, `supplied_policy_eligibility.py`,
`test_raw_snapshot_pin.py`, `test_supplied_policy_eligibility.py`
and the genuine policy admission code (`supplied_policy.py`,
`policy_selection.py`, `private_policy_capture.py`,
`supplied_policy_wire.py`).

## Acceptance evidence

1. Exact local/remote identity, consumed prior regular response and
   required terminal gate: all verified as listed under
   "Reconciliation at activation"; every indexed original byte,
   source and test preimage, lane report topology and lane worktree
   state verified.
2. All eight destinations absent before copying; every new path and
   archive destination checked; source/test dependency identities
   (including the inherited current-view files, pin ownership and the
   genuine policy admission code) and the pin candidate's native
   preparation merge parents and tree verified; all eight objects
   copied byte-exact and verified for mode, byte count, SHA-256 and
   Git blob identity at the receiving tree; original immutable
   report `SELF` bytes preserved.
3. One bounded focus (208 expected — see Verification) and one
   targeted Ruff on the four new Python paths completed with actual
   exits recorded; import origins confirmed under the same limits.
   The old positive/refusal paths (inherited 113 focused cases,
   including the full `test_private_policy_request.py` 45-case
   current-view suite and `test_raw_snapshot_pin.py`) preserved and
   passing.
4. Fresh exact-report-head CI is PENDING at report authoring with
   the ordered expectations (A 1,440, B 1,930, 3,370 ordered units
   each Product, all 95 new cases in B, separate 951 integration
   each, all five required jobs and all existing steps); Root
   independently owns the fresh CI, transfer acceptance and the
   subsequent mandate work. Whole 009 PARTIAL; representative
   baseline NOT_RUN.

## Verification

Environment: existing canonical locked `.venv` (Python 3.14.4),
physical canonical `src`, fresh mode-0700 scratch directly under
sticky `/tmp` as the private `--basetemp`, `-o addopts=
-p no:cacheprovider`, `OPENBLAS_NUM_THREADS=1`,
`PYTHONDONTWRITEBYTECODE=1`, and
`timeout -k 5 120 prlimit --cpu=60 --as=1073741824` on every local
execution, including Ruff and the import-origin check.

1. One bounded focus of the nine ordered entries under
   `tests/unit/` (`test_private_evaluation_preflight.py` 42,
   `test_source_cohort_declaration_preflight.py` 21,
   `test_evaluation_grade_preflight.py` 19,
   `test_source_cohort_runner.py::test_success_and_private_report`
   1, `test_evaluation_program.py::test_two_cases_empty_and_unretrieved_positive`
   1, `test_private_policy_pin_eligibility.py` 53,
   `test_supplied_policy_eligibility.py` 18,
   `test_private_policy_request.py` 45, `test_raw_snapshot_pin.py`
   8): **208 passed in 2.65 s, exit 0** — the expected 208, with
   all 95 new cases in the two transferred suites. Setup note,
   recorded as an actual deviation in evidence capture only: the
   first focus execution also exited 0, but its raw output file had
   been written inside the pytest basetemp, which pytest cleaned;
   the identical ordered focus was re-executed to capture the raw
   artifact (result above, identical entry list, no drift).
2. One four-file Ruff check on
   `private_evaluation_preflight.py`,
   `private_policy_pin_eligibility.py`,
   `test_private_evaluation_preflight.py`,
   `test_private_policy_pin_eligibility.py` on one process-local
   core (`taskset -c 0`): "All checks passed!", exit 0.
3. One bounded import-origin check: both transferred product
   modules resolve to the canonical repository `src` with the exact
   indexed SHA-256s — PASS, exit 0.

Genuine checks versus controlled lower synthetic fixture
delegation: the 42 joint witnesses exercise the genuine evaluation
plan wire admission, the genuine source cohort declaration
admission, the actual grade declaration preparation and the real
bounded deadline machinery, with the declared datasets, envelopes
and budgets as controlled synthetic fixture inputs. The 53 pin
witnesses exercise the real `PolicyRequestAdmission` recheck
before and after scope computation, the genuine closed
`supplied_policy.admit_policy` re-admission of the retained
selected policy and the real `unavailable_partitions` /
`reader_allows` narrowed-scope rules, with the borrowed
in-memory capture, policy bytes, grants and clocks as controlled
synthetic fixture inputs. Both suites therefore prove the genuine
declaration/capture admission and refusal boundaries; they do not
exercise real evaluation execution, real pin or file freshness,
durable writer, current authority invocation, scoring, model
dispatch or publication — all remain with their dedicated owners.

## Fresh hosted gate (pending)

At the report head the ordered inventories are expected: group A
1,440 unchanged, group B 1,930 (all 95 new default nodes in B),
3,370 total units each Product, the separate complete 951-case
integration, all five required jobs (the two Product legs on Python
3.12/3.14 and the three OAP legs on Python 3.12/3.13/3.14) and
every existing step. The fresh full hosted CI at the exact report
head is PENDING at report authoring; Root owns the independent exact
fresh CI and terminal review. The report cannot certify its future
push or checks. The representative baseline stays NOT_RUN; whole
009 PARTIAL.

## Documentation impact

`STATUS.md`: new current-slice 009-aa lead line and cumulative
009-aa entry (exact artifact identities, scoped local evidence,
hosted status at report authoring, remaining real operator,
current writer, request execution, rights, baseline and hardware
gates); prior notes preserved. `docs/evaluation.md`: new "The
009-aa joint declaration and current pin transfer" section with
the same distinctions; no other doc changed.

## DHA and boundaries

Decision: NONE. No D1 candidate reported. No register load beyond
the ordered scope, no D2 action. Preserved resources: unrelated
files, private config, all other worktrees and lane states
untouched; the consumed wrappers, receipts and resolutions are
untouched strategic state. No merge performed; no branch-history
merge, cherry-pick, force push, new PR, release, tag or deploy.

## Limitations and remaining work

No evaluation execution is connected to either transferred entry;
no joint-declaration or pin-eligibility wiring into a runner, no
durable policy selector, no source-authorization composition, no
callback authority, no protected model dispatch, no representative
evaluation, no product fixes beyond the indexed transfer, no
fixture/environment setup changes, no full local suite, no CI
changes, no dependency installs, no new PR, no merge. The open
governed operator, current durable writer, request execution,
source rights, model and hardware gates remain open. DHA: NONE.
