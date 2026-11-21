# OAP Coding Report — 009-aq

Identifier: 009-aq
Result: COMPLETE
Repository: ulfe-lmi/slaif-raggedized-helper
PR number: 11
Branch: oap/009-evaluation-baseline
Base branch: main
Implementation head SHA: 474798a3abf5bdfc18cc1be8722c14affa512d8b
Report publication commit: SELF

## Work and scope

Exact Root FINAL order 009-aq (AMEND_EXISTING_PR on PR 11,
round base 8d0729ff4f5c147713f9f35513ef36f2299ea392,
the accepted 009-ap report-only head whose exact
required hosted run 44884293154 attempt 1 passed
all five jobs and every step with ordered 1,440 +
1,998 units and 997 integrations in each Product,
main 5a7b41cc512cf883b5b2cb92d87554b4d24e685b).
Commits pushed before this report:

1. Transcript commit
   0f30a1c98a4f9258ec2ddc0f89ed31f2ea3130b0,
   sole parent
   8d0729ff4f5c147713f9f35513ef36f2299ea392,
   exactly four transcript objects committed
   byte-exact before any implementation change:
   oap/orders/009-aq-current-cohort-stage-
   loop-transfer.md (6,683 B, SHA-256
   475ec70f4e7da2d17c282a93383562042b11ef8757bb36bbccf534a17ce437ab),
   oap/active (exactly 7 B `009-aq` + LF,
   SHA-256
   b613239826a41bc7441a78ce3c7f7a8d8391738c8566d70e85a0e9fa332046f3),
   oap/reviews/009-aq-current-cohort-stage-
   loop-transfer-index.json (22,593 B,
   SHA-256
   c56b682a03f67f91b1c89c155487978c8d31b685def4ccfa8af1442777c06722)
   and oap/reviews/009-aq-prior-resolution.json
   (791 B, SHA-256
   1ce65246daf793d9f3b90dfdee01372e6536bb1355745f9d8988b0c4e6d0df20).
   Both control JSONs are byte-for-byte copies
   of the strategic workorders originals by
   basename.
2. Implementation commit
   474798a3abf5bdfc18cc1be8722c14affa512d8b,
   sole parent 0f30a1c98a4f9258ec2ddc0f89ed31f2ea3130b0,
   exactly four paths: the two reviewed
   transfer blobs by identity (donor
   implementation
   e8501c84745016caae5437d76318cd43fd9ae106,
   donor base
   9e6997ba89de34dba67fd780ad3847540ebdc78c,
   donor report-only child
   9ba75077b6bd1c6f8801d6a9b6995a1a15b32638;
   candidate history, order and report not
   copied) plus the two ordered concise
   documentation entries.

The two transferred objects:
- src/slaif_raggedized_helper/source_
  cohort_runner.py: 112,505 B, git blob
  f8cb34ed60d6c5bfb8fedb1898edc80c657ed4b9,
  SHA-256 9692af53906773ccf15ca907fe488d27cbd7d822223b26bf681c158504819a8c
- tests/integration/test_current_cohort_
  stage_loop_composition.py (NEW): 34,548 B,
  git blob
  3c9d28d4d521de9e38ee2bd22cd129f6719e4079,
  SHA-256 2d6449c20b0346624b818696cfc01804b35b9c8b9e9342902f8ca7a3d520d09b

Documentation: one nested Current line
(009-aq) plus one Slice 009-aq paragraph
(160 words total) in STATUS.md and one
concise section in docs/evaluation.md
(160 words).

Changed behavior: this round receives the
reviewed private guarded current source
cohort stage loop.  One fixed private shared
production iteration and one shared source
result path are now actually reached by both
the supplied run_cohort entry and the
genuine guarded current entry, the mode
difference only in the fixed case dispatch
and the optionally existing supplied grade
step.  Current alone reserves, before any
semantic work, the extra actual
owned-producer full-directory envelope per
selected case over the legacy envelope
(budget overflow refuses the new cases at
admission with zero new physical work; no
legacy cap is raised), then completes the
shared genuine query-free full-cohort check
and one actual guarded initial pin with
every declared runtime/core identity
checked against the held core before the
first protected encoder exposure.  Each
ordered case performs the actual CASE_PIN
revalidation over the exact case and
retained original value, the factored real
encode and same-payload pinned hybrid
(genuine T1/T2, real O1-O5) exactly once,
and the actual stage-owned dispatch over
the same case with its actual same-payload
query and HybridResult; vectors are not
retained and the actual Query is consumed
one at a time.  The shared result checks,
binder accounting, source aggregate and
serialization run once, the actual current
facts recorded in the result ledger with
the bounded final cut work debited before
the counters freeze, and the legacy
serialization bytes stay exact without the
current facts.  No workflow, dependency,
runtime, CLI, provider/API, policy or
service change.

## Acceptance evidence

1. Reconciliation verified: PR 11 is the
   exact unique open non-draft PR (state
   OPEN, autoMergeRequest null, mergeable)
   with head branch oap/009-evaluation-
   baseline at
   8d0729ff4f5c147713f9f35513ef36f2299ea392
   and base main; remote main is
   5a7b41cc512cf883b5b2cb92d87554b4d24e685b,
   matching the index; local HEAD equaled
   the exact base and the working tree was
   clean except the strategy activation
   (oap/active exactly `009-aq` + LF and the
   new untracked order file).  All ordered
   supervised inputs verified at their
   order-declared SHA-256: transfer index
   c56b682a..., prior resolution 1ce65246..,
   donor local resolution a86ebe9e...,
   009-ap terminal review b690641b...; the
   order's Architecture SHA256 equals the
   received ARCHITECTURE.md and its
   Governance SHA256 equals the received
   oap/governance/MANIFEST.json.  The exact
   checker audit/009-aq-check/check-exact-
   transfer.py at the base verified the
   complete 64 locked receiver preimages,
   the donor topology (implementation
   e8501c84 under base 9e6997ba, report
   child 9ba75077 scoped to the one report
   path whose bytes digest 44ce5830...
   equals the consumed
   audit/009-aq-check/Root-donor-report.json),
   the consumed receipt, verdict and
   verdict_consumed bytes, the four
   unmodified encoder donor preloads
   byte-exact between the donor candidate
   and the receiving base, the exact three
   witnessed node names in the reviewed
   test, and the absent owned
   destinations.  The exact four transcript
   paths were committed first, byte-
   verified.
2. Exactly two blobs implemented and both
   concise docs; the grade code and its
   009-ao test-only repair remain frozen:
   the checker re-verified all 64 frozen
   objects at the base and every unchanged
   frozen object at the implementation
   head (evaluation_program.py,
   test_current_grade_judgment_dispatch_
   composition.py and all closed receiver
   bytes among them), and the 50 legacy
   grade units (test_evaluation_program.py)
   pass unmodified on the transferred tree
   (part of RUN1 319/319).
3. Stage loop (as reviewed and donated,
   witnessed hosted): one shared production
   iteration and result/ledger/aggregation
   path for supplied and guarded current
   modes; legacy admission, phase
   ordering, meters, schema, goldens and
   grade optional dispatch preserved.
   Current uses one shared query-free
   full-cohort check and one actual initial
   pin, the exact original deadline,
   original grants and captured PinData;
   each ordered case uses actual CASE_PIN
   and fixed repeated encode/same-query
   hybrid and stage delegates.  True
   observed I/O starts are separated from
   conservative admission reservations,
   including the extra current producer
   directory and all associated bounds
   without changing historical budgets or
   legacy report bytes; the final current
   selected observation preserves original
   authority and exact custody/time without
   an additional full source-only reload;
   no ordinary partial result and exact
   interruption identity.  Local proof is
   collection-only of the three witnessed
   nodes (RUN2); native execution is
   treated as pending until hosted, and no
   local hosted-witness execution is
   claimed.
4. Stable behavior (as reviewed and
   donated): all exact witnessed stable two
   cases (h1/h4), the whole pure
   unreadable-declaration refusal, and the
   real same-wire generation change between
   the completed first case and before the
   second protected case; actual token ID
   receipts, source/Gold/ranking delegates,
   unchanged raw pointer and expected
   refusal prefix.  The prior forecast 59
   source directories is an expected
   number until the hosted traces pass;
   per the donor resolution the local
   scenario counters are source forecasts
   until native execution, and none is
   claimed here.
5. Local proofs all exit 0: 319 exact
   focused existing units (269 stage focus
   + 50 legacy grade), the ordered three
   hosted collect-only nodes collected
   (RUN2's four-file collect lists 17
   tests: the three exact new nodes plus
   the inherited encoder-producer,
   raw-hybrid and source-bound support CI
   witnesses), scoped two-file one-core
   Ruff with one Rayon thread, two fresh
   physical runner-first and encoder-first
   import-origin probes (ORIGINS_OK), and
   exact working-tree hashes (61 frozen
   base preimages plus the active
   post-state, the two transferred
   postimages and the absent owned report
   destination).  The full checker with
   the implementation argument re-verified
   64 preimages at the base, the donor
   topology and receipts, the transcript
   four objects byte-exact, and the
   implementation exactly the four ordered
   paths.  Expected at the exact report
   head: all exact required hosted jobs
   and steps, both Products ordered 1,440 +
   1,998 units and exactly 1,000
   integrations (997 prior + three new),
   no skipped/failed evidence; that gate
   is PENDING at publication.

## Verification

Environment and exact commands as recorded
in the fresh mode-0700 scratch
/dev/shm/oap-009aq-proof.drivw4
(commands.txt, 1,727 B, SHA-256
088df489ba8b6fb9d4bf222bfe6b8520530f6cb2f78f91e2121c7d34a805922e):
pre-existing canonical physical venv
(Python 3.14.4, pytest 8.4.2, ruff 0.17.4)
and physical canonical src; -o addopts= -p
no:cacheprovider with the exact indexed
files, OPENBLAS_NUM_THREADS=1,
PYTHONDONTWRITEBYTECODE=1, PYTHONPATH=src,
separate TMPDIR/basetemp (separate private
0700 basetemp children), taskset -c 0 with
RAYON_NUM_THREADS=1, and timeout -k 5 120
prlimit --cpu=60 --as=1073741824 for every
proof process.  No dependencies installed,
no local native execution, no unchanged
retry.

1. RUN1 the 319 focused existing units
   (test_query_embedding.py 51,
   test_source_cohort_runner.py 54,
   test_raw_hybrid_search.py 15,
   test_private_policy_request.py 45,
   test_private_policy_pin_eligibility.py
   53, test_source_bound_stage_loss.py 51,
   test_evaluation_program.py 50) - real
   exit 0; raw output run1.log (428 B,
   SHA-256
   d4c8cd90541616fbabe7caaced59ec0d5f7950d71cf070a8a5192a822bdd7655):
   319 passed in 10.24s.
2. RUN2 one bounded four-file collect-only
   (test_current_cohort_stage_loop_
   composition.py, test_current_cohort_
   encoder_producer_composition.py,
   test_raw_hybrid_search_composition.py,
   test_source_bound_support_ci_
   composition.py) - real exit 0; raw
   output run2.log (1,891 B, SHA-256
   b1f675256f0b043224b43bde49a58701b87f44dc59f3f5efd753929fcc8c5b29):
   17 tests collected in 1.21s, including
   the three ordered node names
   (test_stage_loop_positive_two_cases_
   match_legacy_dispatch,
   test_stage_loop_unavailable_
   declaration_refuses_without_work,
   test_stage_loop_generation_change_
   after_first_case).  Collection proves
   the transferred file is import- and
   collection-clean; it does not execute
   the hosted witnesses.
3. RUN3 one scoped two-file one-core Ruff
   on the two transferred files, taskset
   -c 0 with RAYON_NUM_THREADS=1 - real
   exit 0; raw output run3.log (26 B,
   SHA-256
   7e8e995beb6b942867c80817910cf3a80d4b9cb10974bc60ce55e6e21f00e688):
   All checks passed!
4. RUN4 two fresh physical import-origin
   probes, one process per order (runner-
   first and encoder-first): the
   transferred source_cohort_runner module
   plus the receiving dependencies
   (query_embedding,
   private_policy_pin_eligibility,
   source_bound_ranking, raw_hybrid_search,
   evaluation_program) all resolve
   physically to the canonical repository
   src in both import orders, and the two
   transferred working-tree SHA-256s equal
   the exact indexed digests; both real
   exit 0 with ORIGINS_OK; raw streams
   run4-runner-first.log (1,081 B,
   SHA-256
   0ec7bc9a44c67112148b0a2c6a4b2fd1d3031a48cc455bf749b99a55022ef0a2)
   and run4-encoder-first.log (1,082 B,
   SHA-256
   0899314958abf821f57b0dd49d477141970f45210f7d2c4fbae960d59ff7c87d).
5. RUN5 the exact working-tree hashes: all
   61 frozen base preimages (the 64
   indexed receiver objects minus the two
   ordered doc edits and the transferred
   runner; the new witness test is absent
   from the base preimages), oap/active at
   the exact transcript post-state
   `009-aq` + LF, the two transferred
   objects at their indexed postimages,
   and the absent owned report destination
   clean - real exit 0; raw output
   run5.log (606 B, SHA-256
   2213a696849f7cb027c563285f080f1758fd0075ffccc1ca80b61806a3807bc5).
6. RUN6 the exact checker with the
   implementation argument (audit/009-aq-
   check/check-exact-transfer.py) - real
   exit 0; raw output run6-check-impl.log
   (2,023 B, SHA-256
   d889c65dc19c971f23051d1a452ebd9da0d765415b60f313993fdf9d980be5f8):
   64 preimages verified at the base, the
   donor topology and receipts exact,
   transcript four objects byte-exact,
   implementation exactly the four ordered
   paths with both blobs at their donor
   identities.

First-attempt record (procedural
deviations, preserved): the initial
scratch-pointer write to /tmp failed on a
transient No-space-left caused by a
parallel lane (the scratch root itself was
created 0700 and verified); the RUN5
verification script needed three logic
iterations (ordered doc edits and the
transferred runner were initially
misclassified as frozen preimages, and the
active post-state was initially compared
against its old base digest) and RUN6
needed one argument-expansion retry; each
failure was in this round's local proof
harness only, was corrected before the
final clean runs, and no product byte was
changed for any correction.  The recorded
raw logs are the final clean runs.

Mock/live distinction: all fixtures,
roots and policy material are synthetic
and operator-owned; the three hosted nodes
are hosted-only compositions over real
fixtures and the real
admission/selection/pin/encoder/stage
machinery with the trusted synthetic
delegates, and were only collected, never
executed, locally.  The unit focus,
collect-only, lint and origin proves
establish no hosted outcome, no baseline,
no native or real-model result; no live
model, credential, data, network, GPU or
hardware was touched.  No claim is made
about this report's future push/CI; the
separate post-publication receipt records
the remote facts observed after push, and
the strategic review records the hosted
outcomes at the exact report head.

## Documentation impact

STATUS.md: one new nested Current line
(009-aq) and one concise Slice 009-aq
paragraph (160 words total), recording the
two-object transfer, the shared
iteration/result-path scope with the
current-only reservation and per-case
delegates, the conservative budget and
exact synthetic source reads, the legacy
controls, the local proof, the expected
hosted proof and baseline NOT_RUN.
docs/evaluation.md: one new concise
section (160 words) with the same scoped
facts, separate from the hosted status and
representative baseline.  No other
product documentation changed; no grade
or release capability is described.

## DHA and boundaries

Order Decision: NONE; no critical register
entry appended or read.  No consequential
candidate is reported: the recorded
deviations are local proof-harness
iterations corrected before any
publication, fully recorded above, with no
product or strategic effect.  Preserved:
the existing venv and physical canonical
source, all unchanged receiver objects
byte-exact, the prior 009-ap report and
its recorded hosted history, the
candidate_blocked object
401ffaf503021ac3ea6259122095076fec196177,
the unrelated parallel work, and all
unrelated repository state; scratch
artifacts preserved in the fresh 0700
/dev/shm scratch.  No new dependencies,
live model, corpus, credentials, service,
hardware, deploy or release activity.  No
merge performed, no auto-merge enabled, no
PR recreated; PR 11 remains open and
non-draft with the three new commits as
its head sequence.

## Limitations and remaining work

Hosted proof is PENDING: the fresh exact
report-head gate (all exact required jobs
and steps, both Products at ordered 1,440 +
1,998 units and exactly 1,000 integrations
per Product: 997 prior + three new) has
not run at publication; native execution
of the three stage-loop witnesses is
treated as pending until that hosted
proof.  Representative baseline NOT_RUN;
whole 009 PARTIAL; no production or
deployed activity.  Grade program
execution, named CLI, publication or safe
delivery, baseline claims, release and
further guarded composition remain
separate later ordered scopes.  Nothing
in this report certifies this report's
own future push or checks; the separate
post-publication receipt and the
strategic review record those facts.
