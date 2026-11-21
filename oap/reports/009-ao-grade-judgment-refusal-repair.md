# OAP Coding Report — 009-ao

Identifier: 009-ao
Result: COMPLETE
Repository: ulfe-lmi/slaif-raggedized-helper
PR number: 11
Branch: oap/009-evaluation-baseline
Base branch: main
Implementation head SHA: baea33361fe21fcd0e719abb9d62a0f01fff23ff
Report publication commit: SELF

## Work and scope

Exact Root FINAL order 009-ao (AMEND_EXISTING_PR on
PR 11, round base dc09ae4f90ffab086aadf24ca39de9b9f2b29384,
which is the failed 009-an report head, main
5a7b41cc512cf883b5b2cb92d87554b4d24e685b).  Commits
pushed before this report:

1. Transcript commit
   d6131ce2857323207ea590f18295855daf9cbbb3,
   sole parent
   dc09ae4f90ffab086aadf24ca39de9b9f2b29384,
   exactly four transcript objects committed
   byte-exact before any implementation
   change:
   oap/orders/009-ao-grade-judgment-refusal-
   repair.md (6,112 B, SHA-256
   d7b47b2e66916772cce7c9e2be2ffd01f604723435aefa250571f9d58a5a36c3),
   oap/active (exactly 7 B `009-ao` + LF,
   SHA-256
   9c765bc62a9bac69136e027161bf942121d0f92af49ed730af1946b707e67f7d),
   oap/reviews/009-ao-grade-judgment-refusal-
   repair-index.json (4,004 B, SHA-256
   149d921ef154b3d5a990b2cc8470fb43f7d2eb7b0c11f581c6264bc5072ea507)
   and oap/reviews/009-ao-prior-resolution.json
   (796 B, SHA-256
   852a91f22bbb1872c4713dd9bfd59f72e99efc0575ab9e824207c889e1ed60f0).
   Both control JSONs are byte-for-byte copies
   of the strategic workorders originals by
   basename.
2. Implementation commit
   baea33361fe21fcd0e719abb9d62a0f01fff23ff,
   sole parent d6131ce2857323207ea590f18295855daf9cbbb3,
   exactly one file:
   tests/integration/test_current_grade_
   judgment_dispatch_composition.py, from the
   locked preimage git blob
   0b9a069e077982b1f40de89434bcc0996f4dba03
   (39,127 B, SHA-256
   507c539701bf1dffc08fe428c1f0ee0c2d33d494a23e745f791a1febb72e8bc3)
   to the exact postimage git blob
   8b3b51668987dc99327e473c5b6157224c938e9e
   (39,076 B, SHA-256
   8aca72099afff0e7c4712e9a9d4d88d9098b6c90a924c43c83439079352c7bf1),
   3 insertions and 4 deletions inside
   test_judgment_dispatch_pure_refusals_zero_new_reads
   subcase (g) only: the expected progress
   value changed from plan_level to None and
   the immediately preceding comment now says
   the extra judgment fails joint preparation
   before admission with no progress prefix
   and no new reads.

Changed behavior: none in product code.  The
order's single erroneous hosted witness
expectation was corrected to match the
actual, already-accepted product behavior:
in subcase (g) one selected case carries two
plan judgments, which is a malformed plan for
the operation.  The paired admission calls
prepare then admit, and the order/length gate
raises before admitted=True, so the fixed
content-free EvaluationError correctly has
progress=None; the witness incorrectly
expected an admitted PREFLIGHT progress
prefix.  The genuine malformed-plan inputs,
no-reads counters, exact status/message,
caught-context check, admission latch and
custody checks are unchanged, as are
subcases (a)-(f), the other two hosted nodes
and their two product source modules,
workflow, dependencies and product docs.

Prior-hosted-failure rationale (recorded per
the order's Documentation section): hosted CI
run 44877969312 attempt 1 at exact 009-an
report head dc09ae4f90ffab086aadf24ca39de9b9f2b29384
failed exactly this assertion in both
required Product jobs — Python 3.12 job
136766782796 and Python 3.14 job
136766782678 — each after passing the
ordered 1,440 + 1,998 unit tests; the three
standalone OAP jobs passed and skipped
Product steps are unqualified.  The terminal
review (SHA-256
75a25a1c29f873f9590456532316bf0d0fd24921b5d15b1bb4c8042b5ec21aa8)
and the hosted refusal-failure review (SHA-256
7a0bd26ab01947e626437f29645ead127a25fb0f46a5ca7a4b4e84b3dd78bc64)
identify the exact source facts:
evaluation_program.py line 152
(_plan_admission compares the length of the
ordered judgments against the selection and
refuses the mismatch before constructing the
PreparedDeclaration),
private_evaluation_preflight.py lines
215-218 (preparing the complete paired
declaration calls program._prepare_plan
before returning) and
evaluation_program.py lines 1588-1605
(admitted=True occurs only after genuine
preparing has returned, so a failure at this
predicate retains progress=None).  The prior
resolution is REMEDIATION_REQUIRED_NO_
ACCEPTANCE with the decision to continue the
same numeric objective as 009-ao; this
suffix is that continuation on the same PR.

## Acceptance evidence

1. Reconciliation verified: PR 11 is the
   exact open non-draft PR (state OPEN,
   isDraft false, mergedAt null,
   autoMergeRequest null) with head branch
   oap/009-evaluation-baseline at head
   dc09ae4f90ffab086aadf24ca39de9b9f2b29384
   and base main; remote main is
   5a7b41cc512cf883b5b2cb92d87554b4d24e685b,
   matching the index; the local branch
   HEAD equaled the exact 009-an failed
   report head and the working tree was
   clean except the strategy activation
   (oap/active replaced by exactly
   `009-ao` + LF and the new untracked
   order file).  All four final order inputs
   verified at their order-declared SHA-256:
   workorders index 149d921e..., workorders
   prior resolution 852a91f2..., terminal
   review 75a25a1c..., hosted refusal
   failure review 7a0bd26a....  All 13
   receiver objects verified byte-exact at
   the base by the regular check script
   (preimages_verified: 13); the only
   receiver divergence pre-implementation
   was oap/active, the activation itself.
   Transcript committed first: the four
   transcript objects only, byte-verified.
2. Exactly one implementation file changed:
   the exact subcase (g) expectation and its
   immediately preceding comment, from the
   locked preimage to the exact indexed
   postimage (39,076 B, SHA-256
   8aca72099afff0e7c4712e9a9d4d88d9098b6c90a924c43c83439079352c7bf1),
   asserted exactly once in the preimage.
   The old accepted product behavior and
   actual enforcement remain intact: the
   92 focused existing units covering the
   evaluation program (50) and the joint
   preflight (42) pass unmodified on the
   repaired tree, the three hosted files
   collect byte-cleanly, and the regular
   check script re-derives the corrected
   file from the base preimage and verifies
   the expected digest, the transcript
   topology (four exact objects) and the
   implementation topology (exactly the one
   test path, byte-exact corrected content).
   The repaired witness itself keeps the
   genuine malformed-plan inputs, the
   no-reads counters, the exact
   content-free status/message, the
   caught-context check, the admission
   latch and the custody checks, so the
   admitted progress path (subcases
   a-f, other nodes) stays distinct from
   the pre-admission refusal.
3. Local environment and commands:
   pre-existing canonical physical venv
   (Python 3.14.4, pytest 8.4.2, ruff
   0.17.4) and physical canonical src under
   the existing checkout; one fresh mode-0700
   scratch /dev/shm/oap-009ao-proof.CG4YRn
   with the separate private mode-0700
   pytest basetemp child and all raw logs
   and commands preserved outside the
   basetemp; -o addopts= -p
   no:cacheprovider, OPENBLAS_NUM_THREADS=1,
   PYTHONDONTWRITEBYTECODE=1,
   PYTHONPATH=src, separate TMPDIR, and
   timeout -k 5 120 prlimit --cpu=60
   --as=1073741824 for every proof process;
   no dependencies installed and no local
   native test execution.  Results:
   (a) 92 focused existing units (50 + 42)
   all passed, real exit 0; (b) three exact
   hosted collect-only runs (grade judgment
   3 tests, grade catalog 3 tests, ranking
   dispatch 5 tests) all real exit 0;
   (c) one-file scoped Ruff on one allowed
   CPU (taskset -c 0) with one Rayon thread
   (RAYON_NUM_THREADS=1), real exit 0,
   output byte-identical to the prior
   rounds' Ruff digest
   (82b3e6a6c090a57601d22943bd23fca9218d1031dbe5a7b754092f9a156b4f18);
   (d) exact source and test hashes re-
   verified on the repaired tree: the
   repaired test file at the exact indexed
   postimage and all 12 other receiver
   objects byte-exact.
4. One immutable report-only SELF child:
   this report is the sole change over the
   implementation head; transcript,
   implementation and report are pushed
   together to the existing PR 11 in one
   push with no separate implementation-
   only push and no unchanged rerun; remote
   publication of the report head, report
   bytes, parent and diff paths is verified
   by the separate post-push receipt, not
   claimed here.  No waiting for CI before
   publication; hosted proof remains
   PENDING in this report.
5. The fresh exact report-head gate is
   PENDING at publication: it must pass all
   five required jobs and every required
   step, both Products at ordered 1,440 +
   1,998 units and exactly 994 passing
   integrations per Product.  The prior
   failure (run 44877969312 attempt 1 at
   dc09ae4f) remains recorded in the
   terminal and refusal-failure reviews
   cited above; this report does not
   supersede it.

## Verification

Environment and exact commands as recorded
in /dev/shm/oap-009ao-proof.CG4YRn/
commands.txt (2,218 B, SHA-256
ae643ab28ae2ff27be37c56e4b31dd823aae4f6d185b9ecf9bcac215bd3c76e4):

1. RUN1 the 92 focused existing units
   (test_evaluation_program.py 50,
   test_private_evaluation_preflight.py 42)
   -q -o addopts= -p no:cacheprovider with
   the scratch basetemp - real exit 0; raw
   output run1.log (179 B, SHA-256
   e0b62b6da353dcd4ad57fa800d9e21141495fab6917250a351d579e662eb3d4b):
   92 passed in 5.50s.
2. RUN2/RUN3/RUN4 the three exact hosted
   collect-only runs of
   test_current_grade_judgment_dispatch_
   composition.py (3 tests:
   test_judgment_dispatch_stable_nonempty_
   and_empty_judgments,
   test_judgment_dispatch_pure_refusals_
   zero_new_reads,
   test_judgment_dispatch_same_pin_
   generation_changes),
   test_current_grade_catalog_composition.py
   (3 tests) and
   test_current_ranking_dispatch_composition.py
   (5 tests) - all real exit 0; raw outputs
   run2.log (403 B, SHA-256
   20f42598d6f195f186124a1465b5010a17a589c4bb6024682a25428019c52161),
   run3.log (373 B, SHA-256
   0246faa11a4608159420918f173da7ab86372af92abb7496d7d866c5934ece79)
   and run4.log (582 B, SHA-256
   87560c11d05d0c1e89c9a55d3350338b1870e06b1a5a2b16752cc13f759acfb6).
   Collection proves the repaired file is
   import- and collection-clean; it does
   not execute the hosted witnesses.
3. RUN5 the one-file scoped Ruff on the
   repaired test file, taskset -c 0 with
   RAYON_NUM_THREADS=1 - real exit 0; raw
   output run5.log (19 B, SHA-256
   82b3e6a6c090a57601d22943bd23fca9218d1031dbe5a7b754092f9a156b4f18):
   All checks passed!
4. RUN6 the exact source and test hashes on
   the repaired tree - real exit 0; raw
   output run6.log (1,396 B, SHA-256
   3c9f459dcdb1b25f9bfe96aa4529c376448fa990131718710604225fbc2c419c):
   the repaired test file at the exact
   indexed postimage (8aca7209..., 39,076 B)
   and all other receiver objects byte-exact
   against the index, including the two
   product modules and the two other hosted
   integration files.
5. RUN7 the regular check script
   audit/009-ao-check/check-refusal-repair.py
   with the implementation argument - real
   exit 0; raw output run7-check-impl.log
   (1,088 B, SHA-256
   c087173b99b78a87ff1dbd58055d60758fba5e17676dd449a23dd95f266fbf27):
   13 preimages verified at the base,
   expected test digest equal to the
   postimage, transcript and implementation
   topology exact (four transcript objects
   byte-exact, exactly the one test path
   changed to the byte-exact corrected
   content).

Mock/live distinction: all fixtures, roots
and policy material are synthetic and
operator-owned; the three hosted files are
hosted-only compositions over real fixtures
and the real admission/selection/pin
machinery with the trusted synthetic
delegates, and were only collected, never
executed, locally.  No local hosted-witness
execution is claimed.  The unit focus,
collect-only and lint results are local
mock/synthetic evidence only; the hosted
gate at the fresh exact report head remains
PENDING and is the required independent
proof of the repaired witness.

## Documentation impact

No product documentation changed: the
repair corrects a test expectation to the
already-accepted product behavior, so no
behavioral documentation change is
required by the order.  This report records
the test expectation correction and the
prior-hosted-failure rationale.  The
product documentation has no new behavior
to describe.

## DHA and boundaries

Order Decision: NONE; no critical register
entry appended or read.  No consequential
candidate is reported: the single assertion
mismatch is exactly the ordered repair and
the product refusal behavior was
independently reconfirmed by the strategy
reviews.  Preserved: the existing venv and
physical canonical source, all 12
unchanged receiver objects byte-exact,
STATUS.md, docs, workflow, dependencies,
the unrelated encoder candidate awaiting
its own later receiving scope, and all
unrelated repository state; scratch
artifacts preserved in the fresh 0700
/dev/shm scratch.  No new dependencies,
live model, corpus, credentials, service,
hardware, deploy or release activity.
No merge performed, no auto-merge
enabled, no PR recreated; PR 11 remains
open and non-draft with the three new
commits as its head sequence.

## Limitations and remaining work

Hosted proof is PENDING: the fresh exact
report-head gate (all five required jobs
and steps, both Products at ordered 1,440 +
1,998 units and exactly 994 passing
integrations per Product) has not run at
publication.  The prior failure at
dc09ae4f (run 44877969312 attempt 1)
remains recorded and un-superseded.
Representative baseline NOT_RUN; whole 009
PARTIAL; no production or deployed
activity.  The remaining encoder work and
the full grade transfer continue after the
exact repair gate, under their own later
ordered scopes.  Nothing in this report
certifies this report's own future push or
checks; the separate post-publication
receipt and the strategic review record
those facts.
