# OAP Coding Report — 009-as

Identifier: 009-as
Result: COMPLETE
Repository: ulfe-lmi/slaif-raggedized-helper
PR number: 11
Branch: oap/009-evaluation-baseline
Base branch: main
Implementation head SHA: b4eb35ee214b729b5dff20f36deb256bb72535f2
Report publication commit: SELF

## Work and scope

Exact Root FINAL order 009-as
(AMEND_EXISTING_PR on PR 11, round base
895e8467c48838a62c04d22c131ae86e5bb6c705,
the exact accepted 009-ar report-only head
whose required hosted run 44896836955
attempt 2 concluded all five required jobs
and every required step SUCCESS with both
Products (Python 3.12 and 3.14) at ordered
1,440 + 1,998 units and exactly 1,000
integrations each; remote main
5a7b41cc512cf883b5b2cb92d87554b4d24e685b).
Reconciliation: PR 11 is the unique open
non-draft PR with head branch
oap/009-evaluation-baseline at exactly the
round base (refs/pull/11/head and
refs/heads/oap/009-evaluation-baseline both
895e8467c48838a62c04d22c131ae86e5bb6c705),
state OPEN, mergeable, no auto-merge;
local HEAD equaled the base and the
working tree was clean except the strategy
activation (oap/active exactly `009-as` +
LF and the new untracked order file).
Commits pushed with this report:

1. Transcript commit
   8d961f760de305c19a58e92307ffc7b038012beb,
   sole parent
   895e8467c48838a62c04d22c131ae86e5bb6c705,
   exactly four transcript objects
   committed byte-exact before any
   implementation change:
   oap/orders/009-as-current-graded-cohort-
   transfer.md (6,656 B, SHA-256
   4cfc6e4a5943a90daf0e83954d049cfd78ab027449f357c38bb2cf9f75dcb87b),
   oap/active (exactly 7 B `009-as` + LF,
   SHA-256
   478cbce3f50f2ed0b4c5dc335332058f92284b4de5c25c139368837a4bd4c963),
   oap/reviews/009-as-current-graded-cohort-
   transfer-index.json (22,481 B,
   byte-exact copy of the strategic
   workorders record, SHA-256
   f58cab24c3fef26c384a810bf47aa3e71648cd2da21b09c39abf8b2403eef5fe)
   and
   oap/reviews/009-as-prior-resolution.json
   (991 B, byte-exact copy, SHA-256
   e709ae5eec6821ca27288342a0d3426c1f13ae73f3298411ab58f33556546338).
2. Implementation commit
   b4eb35ee214b729b5dff20f36deb256bb72535f2,
   sole parent
   8d961f760de305c19a58e92307ffc7b038012beb,
   exactly six paths:
   src/slaif_raggedized_helper/
   source_cohort_runner.py (112,505 B ->
   142,473 B, git blob
   a617440f0234191476b304f2fd46c355a158f78b,
   SHA-256
   fbcad24cb5b1a8d74840fecdfe7fcc0ee95707ebd9c719c20c667403170b5d4d),
   src/slaif_raggedized_helper/
   evaluation_program.py (69,093 B ->
   86,244 B, git blob
   7d32243178406c6c5ce6b7cf427d2a31e77bbd21,
   SHA-256
   21262edb969f99f368684170779f95853fba97958e312082db1c052d768ffb83),
   src/slaif_raggedized_helper/
   private_evaluation_preflight.py
   (8,131 B -> 9,827 B, git blob
   2a5cff301f7ae181070f7675de01de4fdd967f87,
   SHA-256
   94bae285b472e7362e5aeb724e8c43fd75c39c429650bdbbc432456fff72cac5),
   tests/integration/
   test_current_graded_cohort_composition.py
   (new, 53,355 B, git blob
   90b70b09af70199ee803b6ef1cdb72a4ab3a00e7,
   SHA-256
   6f77e679e1c5d71496c255fa0f7e3fbcc44328bba62a56f8c0aa308c54583758)
   and one scoped paragraph in each of
   STATUS.md and docs/evaluation.md.  The
   four product/test objects are
   byte-exact copies of the reviewed donor
   implementation
   da3cf165c5b92ba404ee8a312132092f140d0cf9
   (donor base 8d0729ff4f5c147713f9f35513ef36f2299ea392,
   donor report-only child
   24333fe9f8a8371b364f5cbfc85150b4c796bd02,
   report SHA-256
   b248fbca56f268fdffd0415af5362caaf24e49cad108ab2bb3e7b411b279818f);
   no donor history, order or report is
   copied.

## Changed behavior

The reviewed current full graded cohort is
now the receiving canonical state:

- The one private current graded
  execution entry over the shared genuine
  source cohort and stage loop makes one
  query-free joint declaration and one
  guarded initial source pin, then runs
  the genuine guarded direct grade
  catalog (shared guarded core with the
  narrow current catalog entry; custody in
  guard compares the retained original raw
  object and live captured object,
  original operation, active owner, stores
  and root before the clipped end is
  attached, with the prepared-pin
  captured value required to be the exact
  raw held value saved at the outer
  entry) and the distinct guarded
  grade-owned physical post-catalog full
  pin.  All share the exact original
  current admission, operation, raw
  capture, stores, root, grant, anchor and
  clipped monotonic end; the current and
  legacy work limits retain their existing
  bounds.
- The one shared production iteration runs
  the real current CASE_PIN revalidation,
  guarded T1/T2, same-payload hybrid and
  source-stage binding, then the shared
  grade case body with its fixed dispatch
  choice and the grading-owned GRADE_PIN /
  GRADE_BIND / GRADE_PIN of the exact
  declared ranking and pin per case; the
  per-case actual query identity, bounded
  ordered metadata, case recording, grade
  aggregation and canonical plan identity
  are shared with the existing
  mathematics and report bytes where
  applicable, while the logical budgets
  and delegated physical observations
  stay distinct.
- The genuine guarded FINAL_PIN
  revalidates the original capture and
  performs a genuine selected reread after
  the actual full load, restoring the
  saved deadline and releasing the guard
  on every exit.  Only success mints the
  private immutable owner-bound exact
  report and corresponding plan identity
  under the original deadline; a denial
  yields a content-free truthful terminal
  prefix.  Interruption identity is
  preserved and the public legacy report/
  storage ABI is unchanged.

No public API change beyond the one new
private entry, the shared grade case
body, the guarded direct catalog core,
the paired declaration core, the factored
remaining-envelope check and the private
frozen slotted owning result; the legacy
behavior stays byte-exact.

## Acceptance evidence

1. AC1 (private entry, shared custody):
   the exact private entry makes one
   query-free joint declaration and one
   guarded initial source pin, then runs
   the genuine guarded direct grade
   catalog and the distinct grade-owned
   post-catalog full pin, all over the
   exact original current admission,
   operation, raw capture, stores, root,
   grant, anchor and clipped monotonic
   end, with the current and legacy work
   limits retaining their existing
   bounds.  The transferred bytes are the
   reviewed donor objects verified
   byte-exact against the transfer index
   (blobs/digests listed above) and the
   ordered checker's donor-scope check:
   donor implementation diffing exactly
   the four transferred paths plus the
   historical stage preload and the
   donor order file over donor base
   8d0729ff.
2. AC2 (shared iteration, distinct
   budgets): the one shared production
   iteration actually reached by both
   entries runs the real current
   CASE_PIN, guarded T1/T2, same-payload
   hybrid and source-stage binding, then
   the grading-owned pin, exact declared
   ranking and pin for each case, with
   per-case actual query identity,
   bounded ordered metadata, case
   recording, grade aggregation and
   canonical plan identity shared where
   applicable and the logical budgets
   distinct from the delegated physical
   observations.  The 361 focused local
   units pass over the unchanged shared
   mathematics (see Verification),
   establishing no hosted outcome.
3. AC3 (FINAL_PIN, minting, denial):
   the genuine guarded FINAL_PIN
   revalidates the original capture and
   performs a genuine selected reread
   after the actual full load with the
   saved deadline restored and the guard
   released on every exit; only success
   yields the private immutable owner-
   bound exact report and corresponding
   plan identity under the original
   deadline, a denial yields a content-
   free truthful terminal prefix, and the
   public legacy report/storage ABI is
   preserved.  These are the reviewed
   donor semantics transferred byte-
   exact; their native execution remains
   hosted-pending.
4. AC4 (three new synthetic witnesses):
   the new hosted file defines exactly
   the three ordered node names
   (test_graded_cohort_positive_two_cases_
   match_legacy_dispatch,
   test_graded_cohort_unavailable_
   declaration_refuses_without_work,
   test_graded_cohort_generation_change_
   after_final_pin) in that order,
   verified by the ordered checker's AST
   node check and collected locally.
   The stable h1/h4 witness uses the
   actual two-bundle a/c projection with
   b still physically in the same raw pin
   and genuinely withheld; the original
   h1/h2 case denies before physical
   work; the real same-wire selected
   generation is published after the
   actual final full pin and before its
   genuine selected reread, yielding
   FINAL_PIN / 2 / 2 / 2 / 0 / 0 and zero
   usable minted result; the independently
   traced 75 directory starts and 21
   actual full pins are the expected
   hosted counts to be checked against
   hosted evidence.  All of this is
   synthetic fixture design; no local
   native run occurred.
5. AC5 (local proof and hosted gate):
   361 focused existing units, exact new
   hosted collect-only, scoped five-file
   one-core Ruff and two fresh physical
   import orders all ran locally with the
   exact ordered environment and all exit
   0 (raw streams and digests under
   Verification); the exact remote
   report-head gate (all five green jobs
   and every required step, both Products
   ordered 1,440 + 1,998 units and
   exactly 1,003 integrations per
   Product, 1,000 prior + three new,
   including the prior stage nodes and
   the three new grade nodes) is PENDING
   at publication as the order declares.

## Verification

Ordered checker
(audit/009-as-check/check-exact-transfer.py
under the strategic home) in preimages-
only mode and again in implementation
mode on
b4eb35ee214b729b5dff20f36deb256bb72535f2:
72 protected base preimages verified
byte-exact at the base and preserved at
the implementation, the receiving stage
witness byte-exact (blob
25ae39f3b7919128614a27d2b239f5e7b76d90fa,
SHA-256
42f03df1d533d616c50cc379923d49824e75092392782419e4aa926860d9c090),
the prior terminal
(audit/009-ar-check/Root-terminal-review.
json, SHA-256
785e160d70bbdd281344f8a75b7419dd5339246c9aa55aaf2fd870853160f8e)
and lane inputs
(parallel/current-graded-cohort/source-
inputs.json) re-verified, the donor
topology exact (donor base == lane base
== parent of candidate, report parent ==
candidate, report path/scope/bytes
exact, receipt/verdict/verdict-consumed
ownership fields exact, donor order
byte-exact), the grade witness absent at
the base, the transcript scope and bytes
exact (four paths), and the
implementation scope exact (six paths)
with all four transfers byte-equal to
the donor.  Exit 0 in both modes.

Ordered local proof
(audit/009-as-check/run-root-proof.sh) in
a fresh mode-0700 /dev/shm scratch
/dev/shm/009as-coding over a pristine
tree (git archive of the base plus the
donor transfers, physically re-verified
by SHA-256, physical-inputs.txt 751 B,
SHA-256
cc64c138277b0e31627e424e7c44f7a926056ee578ec53ee4b2a632e878c9113),
pre-existing checked venv (Python 3.14.4,
pytest 8.4.2, ruff 0.17.4), no
dependencies installed,
-o addopts= -p no:cacheprovider,
OPENBLAS_NUM_THREADS=1,
PYTHONDONTWRITEBYTECODE=1, PYTHONPATH=
src, RAYON_NUM_THREADS=1, separate
private basetemps and
timeout -k 5 120 prlimit --cpu=60
--as=1073741824 for every proof process:

1. RUN1 the 361 focused existing units
   (test_query_embedding.py 51,
   test_source_cohort_runner.py 54,
   test_raw_hybrid_search.py 15,
   test_private_policy_request.py 45,
   test_private_policy_pin_eligibility.
   py 53, test_source_bound_stage_loss.
   py 51, test_evaluation_program.py
   50, test_private_evaluation_
   preflight.py 42) - real exit 0; raw
   focus.log (501 B, SHA-256
   6a574b278deeaa5e91927e711ae6ac279354735fc08458edaa18ce4068e306e0):
   361 passed in 11.15s.
2. RUN2 the exact new hosted collect-
   only (test_current_graded_cohort_
   composition.py) - real exit 0; raw
   collect-grade.log (388 B, SHA-256
   b2d1770893bf2b20c1365ebd81408dc2f295cd539f3c3483e8437112293e863b):
   3 tests collected, the three exact
   ordered node names above.
3. RUN3 the preserved stage collect-
   only (test_current_cohort_stage_loop_
   composition.py) - real exit 0; raw
   collect-stage.log (392 B, SHA-256
   317e3458d25fcd355621ad2b4e1e8cde22dc9d6e4491c7d595115d615323eecb):
   3 tests collected.
4. RUN4 the scoped five-file one-core
   Ruff (taskset to the first core of the
   proof shell, RAYON_NUM_THREADS=1)
   over the four transferred files plus
   the preserved stage witness - real
   exit 0; raw lint.log (19 B, SHA-256
   82b3e6a6c090a57601d22943bd23fca9218d1031dbe5a7b754092f9a156b4f18):
   All checks passed!
5. RUN5/RUN6 two fresh physical import-
   order probes, one process per order
   (runner-first and program-first): the
   transferred production dependencies
   resolve physically to the canonical
   tree src in both orders; both real
   exit 0 with ORIGINS_OK; raw streams
   source_cohort_runner-origin.log (1,097
   B, SHA-256
   ca40d482aa8610b4e9795e43dbdc388b86e56e48e00ea29f92aca6f0ab7dfd48)
   and evaluation_program-origin.log
   (1,095 B, SHA-256
   ff63dd05a2e43dca99066c5344f6657286194aec1a3642559a429228e0ccf4f6).

The four non-timed proof logs
(receiving-preimages.json,
collect-stage.log, lint.log and both
origin logs) are byte-identical to the
independent strategic receiving preview
recorded in
audit/009-current-graded-cohort-local-
resolution.json (SHA-256
f9ef731f2c7f968178867ced4037301b4462ca25ecee2e40d90b72d408fabe83).

Pre-publication correction (procedural,
preserved): the first implementation
attempt a1502e329da79548f48282c580991ac00dafe83b
wedged the new docs/evaluation.md
section between "(997 + 3" and
"new). Baseline ..." inside the existing
009-aq paragraph and described the
scoped Ruff as one-file.  Before any
push and with no immutable report
commit, the implementation commit was
amended once to
b4eb35ee214b729b5dff20f36deb256bb72535f2
changing only the two documentation
paths: the new section now follows the
full existing 009-aq paragraph with a
blank line, the 75 directory starts and
21 full pins are called expected hosted
counts, and the Ruff scope is described
as the five-file one-core set actually
run (re-verified clean).  The four
product/test blobs, the transcript, the
order and the index are byte-unchanged,
and the ordered checker re-verified the
amended commit in implementation mode.
No replay of the round.

First-attempt record (environmental,
preserved): the host /tmp tmpfs was
inode-exhausted (100% inodes, ENOSPC) by
unrelated work before any proof ran, so
all scratch material went to the ordered
fresh 0700 /dev/shm scratch from the
first command; no product byte was
changed for any correction.

Mock/live distinction: all fixtures,
roots and policy material are synthetic
and operator-owned.  The three new
hosted nodes are hosted-only synthetic
compositions over the real
admission/selection/pin/catalog/
encoder/grade machinery with the trusted
synthetic delegates, and were only
collected, never executed, locally.  The
361 focused units, collect-only, lint,
preimage and origin proofs establish no
hosted outcome, no baseline, no native
or real-model result; no live model,
credential, data, network, GPU or
hardware was touched.  The 75 directory
starts and 21 full pins are expected
hosted counts, not local observations.
No claim is made about this report's
future push/CI; the separate post-
publication receipt records the remote
facts observed after push, and the
strategic review records the hosted
outcomes at the exact report head.

## Documentation impact

One scoped paragraph (plus the nested
current-slice bullet) added to STATUS.md
and one scoped section added to
docs/evaluation.md, after the existing
009-aq record.  They state the actual
synthetic observations, the configured
resource bounds (CPU60s/AS1GiB/wall120s/
KILL5, collect-only) and the expected
hosted counts (1,003 integrations, 75
directory starts, 21 full pins), and
distinguish held-out quality and encoder
qualification, which remain NOT RUN.
The representative baseline is retained
NOT_RUN; no command, performance,
license or readiness claim was added.

## DHA and boundaries

Order Decision: NONE; no critical
register entry appended or read.  No
consequential candidate is reported:
the transfer is an exact byte copy of
the reviewed donor with the canonical
repaired stage fixture and all other
receiving preimages preserved, and the
hosted proof is the designated pending
gate.  Preserved: the existing venv and
physical canonical source, all 72
locked base preimages byte-exact, the
repaired canonical stage fixture, the
prior 009-ap/009-ar reports and their
hosted history, the protected
automation, the unrelated parallel
work, and all unrelated repository
state; scratch artifacts preserved in
the fresh 0700 /dev/shm scratch.  No new
dependencies, live model, corpus,
credentials, service, hardware, deploy
or release activity.

## Limitations and remaining work

Hosted proof is PENDING: the fresh exact
report-head gate (all five jobs and
every required step, both Products at
ordered 1,440 + 1,998 units and exactly
1,003 integrations per Product, 1,000
prior + three new, including the prior
stage nodes and the three new grade
nodes) has not run at publication, and
the native execution of the three graded
witnesses - including the traced 75
directory starts and 21 actual full
pins against hosted evidence - is
pending until that hosted proof.
Representative baseline NOT_RUN; whole
009 PARTIAL; no production or deployed
activity.  Publisher, delivery, named
operator command, model qualification,
representative evaluation, workflow
change, merge, deployment and release
remain outside this order's scope.
Nothing in this report certifies this
report's own future push or checks; the
separate post-publication receipt and
the strategic review record those facts.

No merge performed, no auto-merge
enabled, no PR recreated; PR 11 remains
open and non-draft with the transcript
commit, the implementation commit and
this report-only child as its head
sequence.
