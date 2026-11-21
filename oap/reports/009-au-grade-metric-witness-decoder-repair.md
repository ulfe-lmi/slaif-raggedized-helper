# OAP Coding Report — 009-au

Identifier: 009-au
Result: COMPLETE
Repository: ulfe-lmi/slaif-raggedized-helper
PR number: 11
Branch: oap/009-evaluation-baseline
Base branch: main
Implementation head SHA: 0115d9bc471efae17cbddef9c23b41f3773bf7d1
Report publication commit: SELF

## Work and scope

Exact Root FINAL order 009-au
(AMEND_EXISTING_PR on PR 11, round base
a6daecf947447eb393722f2a8e818a1b172824e1,
the exact 009-at report head whose
preserved report SHA-256 is
b94b4bec822be067ef3f815cc2bb92660a3f9f4888810a838b189a6b7bb8f0c1;
remote main
5a7b41cc512cf883b5b2cb92d87554b4d24e685b).
At that exact failed report, run
44909856462 attempt 1 had three green
OAP jobs and both Product ordered unit
steps (1,440 + 1,998) green; each
Product ran 1,003 integrations with
1,002 passing and the same sole stable
metric fixture failure on witness line
766, while the early denial and final
generation mutation witnesses passed
on both (Python 3.12 job
136863152290, Python 3.14 job
136863152411), reviewed by the Root
terminal review
(audit/009-at-check/Root-terminal-
review.json, SHA-256
63aa21cd999ef3069b563c0ca841d79c22971530d13cfa4d13d7a298c9dec00a,
decision REJECT_EXACT_HOSTED_GATE_
STABLE_METRIC_FIXTURE) and retained
here unchanged.  Reconciliation: PR 11
is the unique open non-draft PR with
head branch oap/009-evaluation-
baseline at exactly the round base
(refs/pull/11/head and refs/heads/oap/
009-evaluation-baseline both
a6daecf947447eb393722f2a8e818a1b172824e1,
gh pr view OPEN / MERGEABLE /
auto-merge null over main
5a7b41cc512cf883b5b2cb92d87554b4d24e685b),
local HEAD equaled the base and the
working tree was clean except the
strategy activation (oap/active exactly
7 B `009-au` + LF and the new untracked
order file).  Commits pushed with this
report:

1. Transcript commit
   5b9b1f85ef110992278491fefe3c96a541f00cdc,
   sole parent
   a6daecf947447eb393722f2a8e818a1b172824e1,
   exactly three transcript objects
   committed byte-exact before any
   implementation change:
   oap/orders/009-au-grade-metric-
   witness-decoder-repair.md (5,531 B,
   SHA-256
   ffc16ff50ef28862e065e2b2e20591471a11a00f1712f4fd52987a896437fd24),
   oap/active (exactly 7 B `009-au` +
   LF, SHA-256
   97b904b9eca67d1ec9674de1297adf926590760bb8800809022aea0a4dcdace2)
   and
   oap/reviews/009-au-prior-resolution.
   json (596 B, byte-exact copy of the
   strategic workorders record, SHA-256
   fe4cd8a2fd2e2c43bde8a7d506fc68d902280042d1b427a551d44de2051a2545).
2. Implementation commit
   0115d9bc471efae17cbddef9c23b41f3773bf7d1,
   sole parent
   5b9b1f85ef110992278491fefe3c96a541f00cdc,
   exactly one path:
   tests/integration/
   test_current_graded_cohort_
   composition.py (56,570 B -> 56,818 B,
   git blob
   483be1d127c56410dd40e5e9fc5d102c4ba62728,
   SHA-256
   0778c43f2b80a76d54257185abb775601cb37e5725537b7f24bfa1db05f0656d),
   from the ordered witness source
   preimage SHA-256
   9cfa43d9b039e144706370099e3b5991df3308f145c91aae516d67942f0c7b0e.
   Changes are limited to the existing
   stable metric assertion block of
   test_graded_cohort_positive_two_
   cases_match_legacy_dispatch: the
   block comment, the variant read and
   the h1 cutoff assertions.  The
   other two test functions, all three
   native node names and their order,
   the canonical stage fixture and
   every other source/test/doc byte
   are preserved verbatim; no shared
   tooling edit.

## The exact fixture fault and the
new pure proof

The exact fault: the shared grade
serializer inserts each variant's
encoded JSON object as a value of the
report variants object, so parsing the
report already sets each
grade_doc["variants"][name] to a dict;
the stable block nevertheless called
json.loads on that already decoded
dict (hosted line 766), raising
TypeError in both Products before the
metric assertions could run.  The
actual serializer assembly reproducing
the erroneous second decode is
preserved at audit/009-at-check/
Root-pure-variant-shape.log (SHA-256
9dbf631099a5aaeeb50d24d9884488d6620d5f2d837d1342da80f0332f8b42d6).
Correction: each report variant is
read directly from the already decoded
grade_doc["variants"][name] dict.  The
exact query ID matching, the score
recomputation from the genuine legacy
dense, lexical and fusion rankings
(metrics.score_query with the same
(20, 60) cutoffs and 5,000 ms bound)
and the full equality of the parsed
metric rows are preserved.  The h1
retrieved status is no longer the
assumed modality outcome (name !=
"lexical"); at every cutoff it is
derived from membership of the
declared grade-3 chunk chunks["a"] in
the actual ranking prefix
(ranking[:value["k"]]), with the
single positive's ideal gain
(idcg) checked at 7.0 and the
expected relevant count and recall
(1 / 1.0 when retrieved, 0 / 0.0
otherwise).  The h4 undefined
empty-gold checks (relevant_returned 0
with recall, reciprocal rank and nDCG
null and UNDEFINED_EMPTY_POSITIVE_
GOLD at every cutoff) are retained
verbatim.  The new pure proof, the
bounded verifier
audit/009-au-check/check-pure-
metric.py (SHA-256
a7a439f28f4cf2ee712dc73a6b8da8c0a093beeb3f59af1b27e2e3e5a3b945e9),
extracts the published stable
`for name, ranking in rankings.items()`
loop unchanged from the witness,
assembles the report variants with the
actual serializer statement of
evaluation_program._finish_payload and
actual supplied metrics, decodes them,
and exercises the exact published loop
against h1 (lexical retrieves at rank
1, dense misses, fusion hits at rank
2, all against the rank-2
membership-derived expectation) and
h4 empty gold; it passed with the
assigned physical source root as its
argument and that root's src on
PYTHONPATH (see Verification, RUN6).

## Changed behavior

No product behavior changed.  Only
the faulty owned synthetic witness
block in the one hosted test file was
corrected to read the actual decoded
report variant and to derive the h1
retrieved status from the actual
observed rankings instead of an
assumed modality outcome.  No product,
budget, workflow, runtime, grade or
delegated I/O count change, no native
local run, no new pytest node, no
publisher or CLI transfer, no baseline
run, no merge, no deployment and no
release.

## Acceptance evidence

1. AC1 (decoded variant, membership-
   derived retrieval, ideal gain 7):
   the stable block now reads each
   variant directly from the already
   decoded grade_doc["variants"][name]
   dict, keeps the exact query ID
   matching and the full parsed-row
   equality against the recomputed
   score from the genuine legacy
   dense/lexical/fusion rankings,
   derives the h1 retrieved status at
   each cutoff from membership of the
   declared grade-3 chunk in the
   actual ranking prefix, checks the
   single positive's ideal gain 7 and
   the expected relevant count and
   recall, encodes no assumed modality
   outcome, and retains the h4
   undefined empty-gold checks.  The
   bounded pure check passes the exact
   published loop against actual-
   serializer decoded variants in both
   gold shapes (RUN6 below); the
   genuine end-to-end assertions
   remain to be proven by the fresh
   exact report-head hosted CI.
2. AC2 (bounded pure check):
   audit/009-au-check/check-pure-
   metric.py (ordered SHA-256 verified)
   was run with the assigned physical
   source root as its argument and
   that root's src on PYTHONPATH under
   the proof envelope; it extracted
   the unchanged stable loop shape
   (target `(name, ranking)`, iter
   `rankings.items()`) and exited 0
   with both ordered success lines
   (raw pure-metric.log, 136 B, SHA-
   256 66a063af6107508aeaad7e70403419eeee76b610321889ea6b04c3f041e15d1f).
   The loop shape was preserved so the
   check exercises the source being
   published.
3. AC3 (scope and local/hosted gate):
   transcript three objects byte-
   exact, single test-only
   implementation (git diff --name-
   only round base..implementation is
   exactly the three transcript paths
   plus the one witness path), report-
   only child, unchanged product and
   other witnesses, and the exact
   three node names in order (RUN2
   collect-only below).  Local proof:
   361/361 focused units, exact three
   integration nodes collected only,
   scoped one-core Ruff, two fresh
   physical import orders, all exit 0
   (Verification).  The exact remote
   report gate - all five jobs and
   every step green, ordered 1,440 +
   1,998 units and 1,003 integrations
   in each Product - is required at
   the exact report head and is
   PENDING at publication.

## Verification

Ordered bounded pure proof and
ordered local proof in a fresh mode-
0700 /dev/shm scratch
/dev/shm/009au-coding over a pristine
tree (git archive of implementation
0115d9bc471efae17cbddef9c23b41f3773bf7d1,
physically re-verified by SHA-256;
physical-inputs.txt 262 B, SHA-256
7ce85454e11bbbeef7b38f5ad452d2818fd5e91749f3fa531ce105ea5a8772fe,
recording the tree witness at SHA-256
0778c43f2b80a76d54257185abb775601cb37e5725537b7f24bfa1db05f0656d
and the ordered pure check at SHA-256
a7a439f28f4cf2ee712dc73a6b8da8c0a093beeb3f59af1b27e2e3e5a3b945e9),
pre-existing checked venv (Python
3.14.4, pytest 8.4.2, ruff 0.17.4), no
dependencies installed,
-o addopts= -p no:cacheprovider,
OPENBLAS_NUM_THREADS=1,
PYTHONDONTWRITEBYTECODE=1, PYTHONPATH=
the proof tree src, separate private
0700 basetemps, and
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
   6a574b278deeaa5e91927e711ae6ac279354735fc08458edaa18ce4068e306e0):
   361 passed in 11.15s.
2. RUN2 the exact repaired hosted
   collect-only (test_current_graded_
   cohort_composition.py) - real exit
   0; raw collect-grade.log (388 B,
   SHA-256
   80a8dc906750201e88ca5c78b378687ac8992716d37a31268d248ff2d87f6d71):
   3 tests collected, the exact three
   ordered native node names
   (test_graded_cohort_positive_two_
   cases_match_legacy_dispatch,
   test_graded_cohort_unavailable_
   declaration_refuses_without_work,
   test_graded_cohort_generation_
   change_after_final_pin).
3. RUN3 the scoped one-file one-core
   Ruff (taskset to the first core of
   the proof shell, RAYON_NUM_THREADS=
   1) over the repaired witness - real
   exit 0; raw lint.log (19 B, SHA-256
   82b3e6a6c090a57601d22943bd23fca9218d1031dbe5a7b754092f9a156b4f18):
   All checks passed!.
4. RUN4/RUN5 two fresh physical import-
   order probes, one process per order
   (runner-first and program-first):
   the production dependencies resolve
   physically to the canonical proof
   tree src in both orders; both real
   exit 0 with ORIGINS_OK; raw streams
   source_cohort_runner-origin.log
   (1,097 B, SHA-256
   ca40d482aa8610b4e9795e43dbdc388b86e56e48e00ea29f92aca6f0ab7dfd48)
   and evaluation_program-origin.log
   (1,095 B, SHA-256
   ff63dd05a2e43dca99066c5344f6657286194aec1a3642559a429228e0ccf4f6).
5. RUN6 the ordered bounded pure check
   (check-pure-metric.py with the
   proof tree as the assigned physical
   source root argument and that tree's
   src on PYTHONPATH) - real exit 0;
   raw pure-metric.log (136 B, SHA-256
   66a063af6107508aeaad7e70403419eeee76b610321889ea6b04c3f041e15d1f):
   "Exact metric loop passed actual
   decoded variants and both gold
   shapes." and "Pure check used
   lexical hit, dense miss and rank-
   two fusion hit."  The pure check is
   a pure check: no native fixture
   work, no network, no model.

The lint and both origin logs are
byte-identical to the 009-at proof
logs of the same names (identical
SHA-256 values), as expected because
the product tree is unchanged at base.
Local proof remains units, collection,
lint, origins and the bounded pure
check; native execution is pending the
exact hosted CI.

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
collect-only, lint, origin proofs and
the pure check establish no hosted
outcome, no baseline, no native or
real-model result; no live model,
credential, data, network, GPU or
hardware was touched.  No claim is
made about this report's future push/
CI; the separate post-publication
receipt records the remote facts
observed after push, and the
strategic review records the hosted
outcomes at the exact report head.

## Documentation impact

This report records the exact fixture
fault (json.loads on the already
decoded serializer variant dict,
hosted line 766) and the new bounded
pure proof (ordered verifier identity
and exact run).  No product
documentation changed: the order
retains the original report and the
existing product documentation without
edits, and no documented command,
measured performance, license
clearance or readiness claim was
added.

## DHA and boundaries

Order Decision: NONE; no critical
register entry appended or read.  No
consequential candidate is reported:
the fault is the exact reviewed
hosted-gate test repair the order
declares, with the corrected
assertions bound to the actual decoded
serializer variant and the actual
observed rankings.  Preserved: the
existing venv and physical canonical
source, every product and fixture byte
outside the one witness path, the
failed 009-at report head and its run
evidence (retained unchanged above),
the prior reports, the protected
automation, the unrelated parallel
work, and all unrelated repository
state; scratch artifacts preserved in
the fresh 0700 /dev/shm scratch
/dev/shm/009au-coding.  No new
dependencies, live model, corpus,
credentials, service, hardware,
deploy or release activity.  No merge
performed; PR 11 remains OPEN with
auto-merge off; no 010 and no next
work chosen.

## Limitations and remaining work

Hosted proof is PENDING: the fresh
exact report-head gate (all five jobs
and every required step, both
Products at ordered 1,440 + 1,998
units and exactly 1,003 integrations
per Product) has not run at
publication, and the native execution
of the repaired stable witness -
including the reported-metric parity
assertions after the first failing
bound - is pending until that hosted
proof.  Representative baseline
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
