# OAP Coding Report — 009-at

Identifier: 009-at
Result: COMPLETE
Repository: ulfe-lmi/slaif-raggedized-helper
PR number: 11
Branch: oap/009-evaluation-baseline
Base branch: main
Implementation head SHA: 4570f29f15ffa68bca73b1e2555cd3c58a8f45e1
Report publication commit: SELF

## Work and scope

Exact Root FINAL order 009-at
(AMEND_EXISTING_PR on PR 11, round base
915c516c3ad83ab8657b1cc67a98f8ca94d32dc5,
the exact sole prior 009-as report head
whose preserved report SHA-256 is
ce83fc56a78e36c435b7280fda68b16e76914e84e08bd754e19a36c796dbfeb8;
remote main
5a7b41cc512cf883b5b2cb92d87554b4d24e685b).
At that exact prior report, run
44905965875 attempt 1 had three green
OAP jobs and both Product jobs passed
ordered 1,440 + 1,998 units; each
integration step ran an observed 1,003
tests with 1,001 passes and two
failures, and that exact failed prior
result is retained here unchanged:
test_graded_cohort_positive_two_cases_
match_legacy_dispatch and
test_graded_cohort_unavailable_
declaration_refuses_without_work on
both Products (Python 3.12 job
136851485613 and Python 3.14 job
136851485420), reviewed by the Root
terminal review
(audit/009-as-check/Root-terminal-
review.json, SHA-256
cbc767fb51f4589f778b4044936a9be02b6f1274575f387baa0a4e73a4ef2b49,
decision REJECT_EXACT_HOSTED_GATE_
TEST_REPAIR).  Reconciliation: PR 11 is
the unique open non-draft PR with head
branch oap/009-evaluation-baseline at
exactly the round base (refs/pull/11/
head, refs/heads/oap/009-evaluation-
baseline and gh pr view all
915c516c3ad83ab8657b1cc67a98f8ca94d32dc5
over main
5a7b41cc512cf883b5b2cb92d87554b4d24e685b),
state OPEN, mergeable, no auto-merge;
local HEAD equaled the base and the
working tree was clean except the
strategy activation (oap/active exactly
7 B `009-at` + LF and the new untracked
order file).  Commits pushed with this
report:

1. Transcript commit
   3adaeb268d649d71c37c4adc2198e23746ff4e98,
   sole parent
   915c516c3ad83ab8657b1cc67a98f8ca94d32dc5,
   exactly three transcript objects
   committed byte-exact before any
   implementation change:
   oap/orders/009-at-graded-cohort-
   witness-repair.md (5,756 B, SHA-256
   02e41255c7bd230871efb52dbf4917a2bc0d7c0cbce811e6480279392f24d73a),
   oap/active (exactly 7 B `009-at` +
   LF, SHA-256
   f037069775f79ef0ea447ac51e8cab42b9e32529d3c0b8d340af67c43276542d)
   and
   oap/reviews/009-at-prior-resolution.
   json (586 B, byte-exact copy of the
   strategic workorders record, SHA-256
   87b440421e762219715060323635b2d514287999a8575ffcbf99e4d87a1c01ae).
2. Implementation commit
   4570f29f15ffa68bca73b1e2555cd3c58a8f45e1,
   sole parent
   3adaeb268d649d71c37c4adc2198e23746ff4e98,
   exactly one path:
   tests/integration/
   test_current_graded_cohort_
   composition.py (53,355 B -> 56,570
   B, git blob
   9d1ea218d550e772378dcaab5dc3e43a65627d13,
   SHA-256
   9cfa43d9b039e144706370099e3b5991df3308f145c91aae516d67942f0c7b0e),
   from the original witness SHA-256
   6f77e679e1c5d71496c255fa0f7e3fbcc44328bba62a56f8c0aa308c54583758.
   Changes are limited to the necessary
   imports (asdict; the existing
   supplied_rank_metrics module) and
   the two existing stable and
   unavailable-declaration tests; the
   final-generation test is preserved
   verbatim, all three native test
   names and their order, the prior
   stage fixture and every product and
   other file are untouched.

## The two fixture faults and exact
corrections

1. Stable local work check (hosted
   witness line 372): the assertion
   compared the observed 660,304 local
   source work against
   runner._MAX_BUDGET[10], which is
   the source Budget geometry_calls
   limit (ordinal 10, 256); the source
   work fields local_work and
   local_payload are ordinals 12 and
   13 of the real source Budget.
   Correction: the source final work
   and payload assertions now use the
   named
   runner.Budget(*runner._MAX_BUDGET).
   local_work and .local_payload
   fields, and the grade final work
   and payload assertions use the
   named program.GradeBudget fields,
   with all existing stable assertions
   preserved and reconciled against
   the exact real source definitions
   (ordinals 10 and 11 remain the
   geometry and aggregate call limits
   and are no longer used as work
   bounds in this file).  In the
   existing legacy parity phase the
   actual dense/lexical/fusion rankings
   of the same legacy search now
   verify the reported metric query
   result for each exact query ID
   through the product's own serializer
   round trip (json of asdict of the
   pure bounded supplied_rank_metrics
   score_query), asserting the h1
   grade-3 declared gold retrieval with
   the dense and fusion improvement
   (relevant_returned 1 and recall
   1.0 at every cutoff) and the
   lexical zero, and the h4 empty-gold
   cutoff rows undefined (relevant_
   returned 0 with recall, reciprocal
   rank and nDCG null and
   UNDEFINED_EMPTY_POSITIVE_GOLD at
   every cutoff).
2. Unavailable-declaration wire
   fixture (hosted witness line 778):
   the gold tuple was nested one level
   too deeply - (("h1", (((_c, 3),),)),
   ("h2", ())) - so the accepted
   plan-wire helper raised an unpack
   error before the intended zero-work
   refusal could run.  Correction: the
   intended singleton h1 judgment is
   passed as
   (("h1", ((_c, 3),)), ("h2", ())) to
   the existing plan-wire helper, and a
   bounded pure check in the same test
   proves the real helper encodes
   exactly that pair structure
   ([{"case_id":"h1","gold":[[_c,3]]},
   {"case_id":"h2","gold":[]}]); the
   genuine product now reaches the
   complete all-case admission and
   refuses with PREFLIGHT / 2 / 0 / 0
   / 0 / 2 and zero new protected work
   on the retained exact original
   dataset and three Gold IDs,
   selected authority, live owner and
   all zero-work counters.

## Changed behavior

No product behavior changed.  Only the
two faulty owned synthetic witnesses in
the one repaired hosted test file were
corrected to the exact ordered
fixtures, and the stable legacy parity
phase gained the ordered ranking-
verified reported-metric assertions
within the same stable node.  No stage,
grade or publication product change, no
workflow change, no widened scope, no
synthetic fixture relaxation, no new
hosted node, no native local run, no
writer/CLI, no qualified encoder, no
representative baseline, no merge and
no release.

## Acceptance evidence

1. AC1 (stable witness, named budgets,
   ranking-verified metrics): the
   stable h1/h4 a/c replacement
   declaration is kept with the actual
   same raw pin and withheld b; the
   source final work/payload assertions
   now bound to the named
   runner.Budget(*runner._MAX_BUDGET).
   local_work/.local_payload fields
   and the grade final work/payload to
   the named grade budget fields; the
   legacy parity phase uses the actual
   dense/lexical/fusion rankings to
   verify the reported grade-3 h1
   improvement and the undefined h4
   empty-gold cutoff results, matched
   by exact query ID within the same
   stable node; all pre-existing stable
   assertions are preserved verbatim.
   Local proof of the unchanged shared
   machinery (361 focused units,
   collect-only, lint, origins, see
   Verification) establishes no hosted
   outcome; the stable assertions after
   the first failing bound remain to be
   proven by the fresh exact report-
   head CI.
2. AC2 (unavailable-declaration
   witness): the intended singleton h1
   judgment is passed as
   (("h1", ((_c, 3),)), ("h2", ())) to
   the existing plan-wire helper with
   the bounded pure encoding check;
   the genuine product reaches the
   complete all-case admission and
   refuses with PREFLIGHT / 2 / 0 / 0
   / 0 / 2 and zero new protected work;
   the exact original dataset, three
   Gold IDs, selected authority, live
   owner and all zero-work counters are
   retained.
3. AC3 (final-generation witness
   preserved): the actual final-
   generation witness is preserved
   verbatim (the ordered checker
   verifies byte-identical source
   segment at base and implementation);
   both failed runs already passed it,
   with actual 75 directories and 21
   full pins, the fresh genuine same-
   wire mutation after the final full
   pin, exact FINAL_PIN / 2 / 2 / 2 /
   0 / 0 and no usable mint.
4. AC4 (scope and local/hosted gate):
   the sole-parent transcript, test-
   only implementation, report-only
   child, preserved exact product and
   fixture bytes (implementation scope
   exactly the one witness path) and
   all three native node names are
   verified by the ordered checker (see
   Verification); the established 361
   focused units, collect-only exact
   three native nodes, scoped one-core
   Ruff and two fresh physical imports
   all exit 0 locally (see
   Verification).  The exact remote
   report gate - all five green jobs
   and every step, ordered 1,440 +
   1,998 units and 1,003 integrations
   in each Product job (1,000 prior +
   three new, including the prior stage
   nodes and the three grade nodes) -
   is required at the exact report head
   and is PENDING at publication; no
   unchanged rerun of the failing head
   occurred or is requested.

## Verification

Ordered checker
(audit/009-at-check/check-exact-
repair.py under the strategic home) on
implementation
4570f29f15ffa68bca73b1e2555cd3c58a8f45e1:
sole parent of the implementation is
the transcript, sole parent of the
transcript is exactly the failed report
base, the transcript scope and bytes
are exact (the three controls above,
byte-verified against the strategic
workorders records), the
implementation scope is exactly the
one witness path, the original witness
SHA-256 is the ordered preimage, the
exact hosted node inventory is
unchanged (the three names in order),
the already passing exact final
mutation test is byte-identical, and
both repaired tests differ from base.
Exit 0.  The same checker runs again
with --report on this report commit
before push and reports the
report-only scope
oap/reports/009-at-graded-cohort-
witness-repair.md over the
implementation head.

Ordered local proof in a fresh mode-
0700 /dev/shm scratch
/dev/shm/009at-coding over a pristine
tree (git archive of the base plus the
repaired witness, physically re-
verified by SHA-256; physical-inputs.
txt 153 B, SHA-256
d3a6cbd32e41232914530c27e44743c2b981ad69422b6bef7514b0236a7d6921,
recording the tree witness copy at
SHA-256
9cfa43d9b039e144706370099e3b5991df3308f145c91aae516d67942f0c7b0e),
pre-existing checked venv (Python
3.14.4, pytest 8.4.2, ruff 0.17.4), no
dependencies installed,
-o addopts= -p no:cacheprovider,
OPENBLAS_NUM_THREADS=1,
PYTHONDONTWRITEBYTECODE=1, PYTHONPATH=
src, RAYON_NUM_THREADS=1, separate
private basetemps and
timeout -k 5 120 prlimit --cpu=60
--as=1073741824 for every proof
process:

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
   fffee05d36b12f6ca998d29be11386dc6cd3aa2d602fee803fec2a454ab741ff): 361 passed in 10.52s.
2. RUN2 the exact repaired hosted
   collect-only (test_current_graded_
   cohort_composition.py) - real exit
   0; raw collect-grade.log (388 B,
   SHA-256
   6efd73c7dbd5f98cfe4c8197441d164aa4553fc870525067ab22aefe02bcfbc4):
   3 tests collected, the three exact
   ordered native node names.
3. RUN3 the preserved stage collect-
   only (test_current_cohort_stage_
   loop_composition.py) - real exit 0;
   raw collect-stage.log (392 B,
   SHA-256
   3f8431e8fe095272cc9a974e5d947eeda823787c18478f74997486e8be107f1e):
   3 tests collected.
4. RUN4 the scoped one-file one-core
   Ruff (taskset to the first core of
   the proof shell, RAYON_NUM_THREADS=
   1) over the repaired witness - real
   exit 0; raw lint.log (19 B, SHA-256
   82b3e6a6c090a57601d22943bd23fca9218d1031dbe5a7b754092f9a156b4f18):
   All checks passed!.
5. RUN5/RUN6 two fresh physical import-
   order probes, one process per order
   (runner-first and program-first):
   the production dependencies resolve
   physically to the canonical tree
   src in both orders; both real exit
   0 with ORIGINS_OK; raw streams
   source_cohort_runner-origin.log
   (1,097 B, SHA-256
   ca40d482aa8610b4e9795e43dbdc388b86e56e48e00ea29f92aca6f0ab7dfd48)
   and evaluation_program-origin.log
   (1,095 B, SHA-256
   ff63dd05a2e43dca99066c5344f6657286194aec1a3642559a429228e0ccf4f6).

The lint and both origin logs are byte-
identical to the 009-as proof logs of
the same names (identical SHA-256
values), as expected because the
product tree is unchanged at base.
Local proof remains units, collection
and lint; native execution is pending
the exact hosted CI.

Mock/live distinction: all fixtures,
roots and policy material are
synthetic and operator-owned.  The
three hosted nodes are hosted-only
synthetic compositions over the real
admission/selection/pin/catalog/
encoder/grade machinery with the
trusted synthetic delegates, and were
only collected, never executed,
locally.  The 361 focused units,
collect-only, lint and origin proofs
establish no hosted outcome, no
baseline, no native or real-model
result; no live model, credential,
data, network, GPU or hardware was
touched.  No claim is made about this
report's future push/CI; the separate
post-publication receipt records the
remote facts observed after push, and
the strategic review records the
hosted outcomes at the exact report
head.

## Documentation impact

None: the order retains the original
report and the existing product
documentation without edits, and no
documented command, measured
performance, license clearance or
readiness claim was added.

## DHA and boundaries

Order Decision: NONE; no critical
register entry appended or read.  No
consequential candidate is reported:
the two faults are the exact reviewed
hosted-gate test repairs the order
declares, with the corrected
assertions bound to the exact real
source definitions.  Preserved: the
existing venv and physical canonical
source, every product and fixture byte
outside the one witness path, the
preserved 009-as report and its hosted
history (the exact failed prior result
retained above), the prior reports,
the protected automation, the
unrelated parallel work, and all
unrelated repository state; scratch
artifacts preserved in the fresh 0700
/dev/shm scratch /dev/shm/009at-coding.
No new dependencies, live model,
corpus, credentials, service,
hardware, deploy or release activity.

## Limitations and remaining work

Hosted proof is PENDING: the fresh
exact report-head gate (all five jobs
and every required step, both
Products at ordered 1,440 + 1,998
units and exactly 1,003 integrations
per Product, 1,000 prior + three new,
including the prior stage nodes and
the three grade nodes, with the
expected 75 directory starts and 21
full pins checked against hosted
evidence) has not run at publication,
and the native execution of the two
repaired witnesses - including the
stable assertions after the first
failing bound that remain unproven
end to end - is pending until that
hosted proof.  Representative baseline
NOT_RUN; whole 009 PARTIAL; no
production or deployed activity.
Publisher, delivery, named operator
command, model qualification,
representative evaluation, workflow
change, merge, deployment and release
remain outside this order's scope.
Nothing in this report certifies this
report's own future push or checks;
the separate post-publication receipt
and the strategic review record those
facts.

No merge performed, no auto-merge
enabled, no PR recreated; PR 11
remains open and non-draft with the
transcript commit, the implementation
commit and this report-only child as
its head sequence.
