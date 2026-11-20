# OAP Coding Report — 009-q

Identifier: 009-q
Result: PARTIAL
Repository: ulfe-lmi/slaif-raggedized-helper
PR number: 11
Branch: oap/009-evaluation-baseline
Base branch: main
Round base commit: 3522d263991e35b25b65f2621a289a05ad4231be
Transcript commit: 8ae8846c31be75d0e2772dcd16f0dae8803e75e8
Implementation head SHA: dc91afbf0681e2a45410f294859f034609bb7cad
Report publication commit: SELF
Order SHA256: d83c79613a1855213f70165e3d366e21e0af9fa02f86085b7f8d2126f267d4cd
Active bytes: 009-q + LF (SHA256 19d1b738929ee1624da6aef019d97e4d155bccf565d479c68e55ed18bdcaea53)
Prior resolution SHA256: abeaa64b4dea622bcc9a2c7d7562b3747a43f0bb088fd8ac5c429e90a3f15151
Publication authorization: FINAL order 009-q-combine-ci-process-resource-controls.md (d83c7961…) at round base 3522d263; Root prior resolution decision ACCEPT_ISOLATED_PUBLISHER_CASE_EVIDENCE_REQUIRED_3_14_CI_RED_CONTINUE_SAME009; standard non-force push to the existing branch subject to its named checks

## Scope

009-q (FINAL) at round base 3522d263 (the 009-p report head): run a
fresh full hosted comparison that combines the now-passing isolated
publisher case with the previously exercised OpenBLAS control on the
Product unit step, retaining every test and required check. The only
functional change is the exact two-line 009-o env stanza restored
under the unique Product test suite step of
`.github/workflows/oap.yml`, plus current docs. No test/product or
supervisor change, no workflow change outside that unit step, no
coverage alteration, no resource limit increase, unchanged retry, no
other PR, no merge, no real service/data/model/hardware operation.

## Change

Transcript 8ae8846 (sole parent 3522d263): the exact three-path Root
transcript (order d83c7961…, active 009-q+LF, prior resolution
abeaa64b…), byte-verified against the strategic home.
Implementation dc91afb (sole parent 8ae8846): exactly 3 paths.
- .github/workflows/oap.yml: preimage SHA256 29a44dd6… (14,186 B,
  byte-equal to the 21341795 preimage); the exact two-line 009-o
  environment stanza restored after the unique Product test suite
  name (both Python matrix legs), LF/indentation and all other bytes
  preserved:

        - name: Product test suite
          env:
            OPENBLAS_NUM_THREADS: '1'
          run: |

  postimage SHA256 b9195355… (14,235 B) equals the whole workflow
  from e9f24bae byte-for-byte; suite selection, commands, matrices,
  resource controls, selection and all downstream steps unchanged.
- STATUS.md: preimage SHA256 c29ea629…; current-state lead advanced
  009-p -> 009-q plus one short factual 009-q continuation paragraph.
- docs/evaluation.md: preimage SHA256 f612268b…; new 009-q section
  near the preserved 009-p section, plus the ordered 009-p
  clarification (the 520260 KiB observation and first 73748 KiB
  increments belong to the separate instrumented baseline trials; the
  first publisher-module failure itself established the traceback and
  88/89); no other 009-o/009-p report or section rewritten.
Publisher test tests/unit/test_private_report_publication.py
byte-verified unchanged at 1b8cb255… and supervisor
oap/bin/ci_unit_diagnostics.py byte-verified unchanged at 3e15bf1c…;
the successful 009-p isolated-child allocator setting is retained.

## Verification (static Git/hash/diff only; exact command results and
hashes private in the strategic audit/009-q-check directory, never in Git)

- Preflight: local HEAD/branch = origin/oap/009-evaluation-baseline =
  3522d263 (= order base); origin/main 5a7b41cc; local tracked base
  clean except the exact activation bytes (order d83c7961…, active
  009-q+LF); PR 11 unique OPEN, head 3522d263, base main, not draft,
  no auto-merge, MERGEABLE; prior resolution abeaa64b… and Root
  audit/009-p-ci-terminal/Root-terminal-review.json 35c86e47… match
  the order; workflow preimage 29a44dd6… and e9f24bae postimage
  b9195355… match; publisher test 1b8cb255… and supervisor 3e15bf1c…
  match.
- Actual 009-p terminal outcome (run 44667676605 at 3522d263):
  Python 3.12 Product job 136060860677 all 24 steps succeeded with
  2731 collected and 2731 unit passes including integration; Python
  3.14 job 136060860643 collected 2731 and emitted 2532 pass marks
  before child exit 137 after 63.57 s without a final unit summary,
  last unfinished forwarded node
  tests/unit/test_source_bound_stage_loss.py::test_controlled_two_partition_full_stages_exceed_return_cap
  with its six subsequent steps skipped; both versions passed the
  corrected 16-slot publisher case; the three OAP jobs succeeded
  (10 steps each); neither the exit status nor that last forwarded
  node establishes the cause.
- Limited reason for the combined comparison: the 009-o
  Product-step OPENBLAS_NUM_THREADS=1 trial alone left the publisher
  thread-start failure on both versions while each job completed the
  other 2730 cases, including that 3.14 last forwarded node, and a
  separate local controlled probe reduced collection from 40 native
  OS threads to one; keeping the verified 009-p isolated-child
  allocator setting and adding the earlier exact Product-step control
  justifies this bounded resource control without attributing the
  hosted exit to OpenBLAS. Both full hosted Product matrices are
  required again.
- Static checks: git diff --check exit 0 on the transcript and
  implementation ranges; implementation diff exactly the three scoped
  paths with the transcript as sole parent; workflow diff versus base
  exactly the two ordered lines; postimage diff against the e9f24bae
  blob empty (byte-equal); no product, test, fixture, job, deadline,
  limit, retry, selection, supervisor or downstream-step bytes
  changed in the commit.
- Local product run: not needed for this exact static byte
  replacement and not run.
- Mock/live distinction: no local product execution, no keys, no
  network, no GPU, no model download or live inference; the fresh
  hosted run at the new head is the actual CI evidence and is PENDING
  at report authoring - pending is pending, and no green/cause/
  baseline claim follows from this report.

## Acceptance evidence

1. Exact local and remote identity verified (local HEAD = branch =
   origin/oap/009-evaluation-baseline = 3522d263; origin/main
   5a7b41cc) and the base clean apart from the activation files
   (order d83c7961…, active 009-q+LF, prior resolution abeaa64b…);
   unique remote PR 11 (OPEN, head 3522d263, base main, not draft, no
   auto-merge); transcript committed with exactly its three paths as
   the sole child of 3522d263.
2. The two workflow lines and the exact historical postimage
   verified: the whole workflow equals the e9f24bae postimage
   byte-for-byte (SHA256 b9195355, diff against that blob empty) and
   differs from the round base by exactly the two ordered lines under
   the unique Product test suite name; publisher test 1b8cb255…,
   supervisor 3e15bf1c…, resource controls, commands, matrices,
   selection and downstream steps all unchanged; git diff --check
   exit 0 on both scoped commit ranges; static Git/hash/diff checks
   suffice for this env-only comparison.
3. Actual 009-p outcomes and the limited reason for the combined
   comparison documented in STATUS.md and docs/evaluation.md (44667676605:
   3.12 all 24 steps succeeded with 2731 unit passes including
   integration vs 3.14 exit 137 after 2532 pass marks, last
   forwarded node and six skipped steps, OAP jobs green, both
   versions passing the corrected 16-slot publisher case, cause
   unproven; 009-o step-env trial and 40-to-1 local probe rationale;
   both full hosted matrices required again); committed exactly the
   three scoped implementation paths as the transcript's sole child;
   active exact authorized bytes (009-q+LF) reported and the actual
   fresh CI pending at report authoring.
4. One immutable report-only SELF commit (this file) as the
   implementation's sole child, through one ordinary non-force push
   to the existing branch after current remote reconcilation; remote
   report bytes and topology (remote PR head = this commit,
   report-only diff, first-parent chain 3522d263 -> 8ae8846 ->
   dc91afb -> SELF) verified before the one canonical response.
   Scope: whole 009 PARTIAL; fresh CI ownership stays with Root and
   every gate is protected.
5. Acceptance after publication requires both complete Product
   matrices and all three required OAP jobs to succeed at the exact
   report head; a new red result requires cause evidence and bounded
   hosted diagnostics, independent of the exact last forwarded node;
   no automatic retry.

## Documentation impact

STATUS.md: current-state lead advanced to 009-q with one short
current continuation note (run 44667676605 exact per-version
outcomes, the restored two-line env stanza making the workflow
byte-equal to the e9f24bae postimage, the retained 009-p isolated
allocator setting, the limited combined-comparison reason, both full
hosted matrices required again, fresh CI pending). docs/evaluation.md:
new 009-q section near the preserved 009-p section recording the same
exact facts, plus the ordered 009-p section clarification (the 520260
KiB observation and first 73748 KiB increments belong to the separate
instrumented baseline trials; the first publisher-module failure
itself established the traceback and 88/89). Numeric evidence,
historical immutable reports and all other material preserved; no
unrelated docs change.

## DHA and boundaries

DHA NONE; no CRITICAL change. Preserved: Qwen profile/auth,
credentials, models, services and hardware untouched; no
dependency/environment installation; no test/product or supervisor
edit; no candidate-branch or worktree action (no merge/cherry-pick/
reset/force/tag/deploy/duplicate PR); no new FIFO reader or replay
(the sole external wrapper ownership and prior receipts are
preserved); all private command results and hashes retained in the
strategic audit/009-q-check directory, away from Git. No merge; PR 11
remains open and unmerged.

## Limitations and remaining work

Whole 009 PARTIAL; no deployment readiness implied. The fresh
report-head CI is PENDING at report authoring (no green/cause/
baseline/whole-MVP certificate follows; this report cannot certify
its future push or checks). The hosted limiting resource of the 3.14
exit 137 remains unproven and a new red result stays possible - any
failure goes to Root for cause evidence and bounded hosted
diagnostics, never auto-retry. Baseline NOT_RUN; the full default
count stays 2731 as an expectation until observed; no narrower CI
selection; no-auth/no-current-policy/no-real-producer/no-model-
qualification labels hold; protected authority/hardware/right/
license/MVP and release gates remain OPEN. Strategy owns the fresh
full check/acceptance review. No 010, no merge; DHA NONE.
