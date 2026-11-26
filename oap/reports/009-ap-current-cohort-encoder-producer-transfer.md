# OAP Coding Report — 009-ap

Identifier: 009-ap
Result: COMPLETE
Repository: ulfe-lmi/slaif-raggedized-helper
PR number: 11
Branch: oap/009-evaluation-baseline
Base branch: main
Implementation head SHA: 17e37e2d89711beeceb83cfdbc87adcebb0cfac0
Report publication commit: SELF

## Work and scope

Exact Root FINAL order 009-ap (AMEND_EXISTING_PR on PR 11,
round base 9e6997ba89de34dba67fd780ad3847540ebdc78c,
the accepted 009-ao report-only head whose exact
required hosted run 44880799693 attempt 1 passed
all five jobs and every required step with
ordered 1,440 + 1,998 units and 994 integrations
in each Product, main
5a7b41cc512cf883b5b2cb92d87554b4d24e685b).
Commits pushed before this report:

1. Transcript commit
   d820d51afc4505e66d50875fa2f7b3cc00464e37,
   sole parent
   9e6997ba89de34dba67fd780ad3847540ebdc78c,
   exactly four transcript objects committed
   byte-exact before any implementation change:
   oap/orders/009-ap-current-cohort-
   encoder-producer-transfer.md (7,902 B,
   SHA-256
   467a9fda7a1ab1e95db8b77572028c18f549d8ccde472b4b68b33337d12126f0),
   oap/active (exactly 7 B `009-ap` + LF,
   SHA-256
   5cad6bb309eca7e7ba47c70fa87ab30acb9b7d6a4e7f0cb0ebc8cfab5891cf44),
   oap/reviews/009-ap-current-cohort-encoder-
   producer-transfer-index.json (18,908 B,
   SHA-256
   3882901b03b5f0df34fd4dda50e000c8a034fae756f77427fa6203df89981bc2)
   and oap/reviews/009-ap-prior-resolution.json
   (1,033 B, SHA-256
   3c2cd44e9ac83c98a87a140acecf422b8ffc6d4a312f8703f0f33e32718f2d5b).
   Both control JSONs are byte-for-byte copies
   of the strategic workorders originals by
   basename.
2. Implementation commit
   17e37e2d89711beeceb83cfdbc87adcebb0cfac0,
   sole parent d820d51afc4505e66d50875fa2f7b3cc00464e37,
   exactly eight paths: the six reviewed
   transfer blobs by identity (encoder donor
   f41e8c36baf656caf468a7bef3e1c72e6a2f6262
   implementation; grade identity donor
   8d4538e6e0b76df2cf84f4c67e0a7ea2b2b774f2,
   donor base
   56b34d46fedcfb87ccb6e0c036c500ee69370f7f)
   plus the two ordered concise documentation
   entries.

The six transferred objects (candidate history,
order and report not copied):
- src/slaif_raggedized_helper/query_
  embedding.py: 15,959 B, git blob
  c1319189f1443129b62cbcaeb39060bbf2d3ec2f,
  SHA-256 513fb18be97d3644c25d8c4a6de158a7a804f1f45e2884cbd6047d01e899a51b
- src/slaif_raggedized_helper/source_
  cohort_runner.py: 86,922 B, git blob
  6fbd009387aeeaa8983c4fe9e46a10945ea0cceb,
  SHA-256 c595d501036d1d6211aa0972e3825330045d3838aa9facb0ec23989cd9fd0e94
- src/slaif_raggedized_helper/evaluation_
  program.py: 69,093 B, git blob
  87da9b4a5af7973b071c3bf31bcfaf51b8a9b620,
  SHA-256 7b6fda252ec93475eff5171c137d70a736a634b006ef8908ee3da165aff330f1
  (the unmodified grade donor base
  evaluation_program.py was byte-exact in the
  receiving head, verified by the checker)
- tests/integration/test_current_cohort_
  encoder_producer_composition.py (NEW):
  42,652 B, git blob
  e3cd465d4d8b2934a5f4f3c68864fd35488b8c0b,
  SHA-256 a23af373c8cc2e378098f67ddeefa75facf1ccc79ef975d26493b7086c2643cf
- tests/integration/test_raw_hybrid_search_
  composition.py: 21,337 B, git blob
  23421c862e91e4142df27f37dfe1066d5c3dc64b,
  SHA-256 9f8027fbd018174d645249a11d63610e5054036f822b358d88bca4a0a66da7f3
- tests/integration/test_source_bound_
  support_ci_composition.py: 10,706 B, git
  blob dfb62d33c971bd4daca26a9074503ff500666734,
  SHA-256 28b7da848b0173ada52c4932a8628b70336de5b1e6aac6e2a26feca3343c6dc8

Documentation: one concise entry in STATUS.md
(nested Current line plus Slice 009-ap
paragraph, 160 words) and one concise section
in docs/evaluation.md (160 words).

Changed behavior: this round receives the
reviewed single-case guarded encoder-to-
producer composition and the separately
reviewed pure grade identity assembly.  The
encoder route now shares actual query-free
all-case admission and one actual initial
physical pin, resolves the exact nominated
case before the reload, verifies the
retained live core and all four identity
fields against the genuine resident before
T1, and uses the genuine real T1/T2 with
exact actual text and normalized payload
once; the one actual same-payload guarded
retrieval performs O1-O5 with result
identity and custody verified, no generic
callback/clock/provider or extra physical
pin; both short borrows restore the same
retained operation's prior end and
independently release before the cutoff; the
internal result preserves legacy origin and
qualification, and ordinary refusal and
interruption identity remain bounded.  The
grade assembly preserves the legacy clock
and reserve/meter ordering with one actual
per-query expected identity, ten bounded
metadata fields without retaining payload,
one reservation called in its original pre-
allocation position, and one final canonical
plan hash; legacy digests, algebra, shape,
uniqueness/refusal and bounds are unchanged,
with no new entry point or new unit nodes.
No workflow, dependency, runtime, CLI,
provider/API, policy or service change.

## Acceptance evidence

1. Reconciliation verified: PR 11 is the
   exact unique open non-draft PR (state
   OPEN, autoMergeRequest null, mergeable)
   with head branch oap/009-evaluation-
   baseline at
   9e6997ba89de34dba67fd780ad3847540ebdc78c
   and base main; remote main is
   5a7b41cc512cf883b5b2cb92d87554b4d24e685b,
   matching the index; local HEAD equaled
   the exact base and the working tree was
   clean except the strategy activation
   (oap/active exactly `009-ap` + LF and the
   new untracked order file).  All five
   ordered supervised inputs verified at
   their order-declared SHA-256: transfer
   index 3882901b..., prior resolution
   3c2cd44e..., 009-ao terminal review
   f53168a7..., encoder local resolution
   71b3a097..., grade identity local
   resolution b21e5c4e....  The exact
   checker audit/009-ap-check/check-exact-
   transfer.py at the base verified the
   complete 52 locked receiver preimages,
   both donor topologies (encoder candidate
   f41e8c36 under prepared 332cc42a with
   ordered parents 256d1b9b + dc901ec0 and
   prepared tree ad3d6b3f, report child
   5fb031c5 scoped to the one report path;
   grade identity 8d4538e6 over base
   56b34d46 scoped to the one source and
   order path, report child 61d9c7a6 scoped
   to the one report path), both consumed
   receipts with result COMPLETE, the grade
   donor base byte-equal to the receiving
   head preimage, the exact three witnessed
   node names in the reviewed test, and the
   absent owned destinations.  The exact
   four transcript paths were committed
   first, byte-verified.
2. Exactly six blobs implemented and both
   concise docs; the 009-ao grade test and
   all closed receiver bytes remain exact:
   the checker re-verified all 52 frozen
   objects at the base and every unchanged
   frozen object at the implementation
   head, and the 92 grade/preflight focused
   units (50 evaluation program + 42 joint
   preflight) pass unmodified on the
   transferred tree (part of RUN1 310/310).
3. Encoder route (as reviewed and donated,
   witnessed hosted): shares actual
   query-free all-case admission and one
   actual initial physical pin, resolves
   the exact nominated case before the
   reload, verifies the retained live core
   and all four identity fields against the
   genuine resident before T1, uses the
   genuine real T1/T2 with exact actual text
   and normalized payload once; the one
   actual same-payload guarded retrieval
   O1-O5, result identity and custody
   verified, no generic callback/clock/
   provider or extra physical pin; both
   short borrows restore the same retained
   operation's prior end and independently
   release before the cutoff; internal
   result preserves legacy origin and
   qualification; ordinary refusal and
   interruption identity remain bounded.
   Local proof is collection-only of the
   three witnessed nodes (RUN2); native
   execution is treated as pending until
   hosted, and no local hosted-witness
   execution is claimed.
4. Grade assembly (as reviewed and
   donated): legacy clock and reserve/meter
   ordering preserved; one actual per-query
   expected identity and ten bounded
   metadata fields without retaining
   payload; one reservation called in its
   original pre-allocation position; one
   final canonical plan hash; legacy
   digests, algebra, shape,
   uniqueness/refusal and bounds unchanged;
   no new entry point or new unit nodes.
   The two donors are disjoint (verified:
   the grade path is not in the encoder
   transfer set) and fit one receiving
   proof; future guarded composition
   remains separate.  The 50 grade units
   pass unmodified in RUN1.
5. Local proofs all exit 0: 310 exact
   focused existing units (218
   encoder/cohort/request/eligibility + 92
   grade/preflight), three exact hosted
   collect-only (the ordered three nodes),
   scoped six-file one-core Ruff with one
   Rayon thread, fresh physical encoder-
   first, cohort-first and grade-first
   import-origin probes (ORIGINS_OK), and
   exact working-tree hashes (58 objects).
   Expected at the exact report head: all
   exact required hosted jobs and steps,
   both Products ordered 1,440 + 1,998
   units and exactly 997 integrations (994
   prior + three), no skipped/failed
   evidence; that gate is PENDING at
   publication.

## Verification

Environment and exact commands as recorded
in the fresh mode-0700 scratch /dev/shm/
oap-009ap-proof.3EhsWA (commands.txt,
1,802 B, SHA-256
73f18135d9f4aebf23fbf07d9c94145f8880ca8a86b92a1fc411c5a2a6366f2d):
pre-existing canonical physical venv
(Python 3.14.4, pytest 8.4.2, ruff 0.17.4)
and physical canonical src; -o addopts= -p
no:cacheprovider with the exact indexed
files, OPENBLAS_NUM_THREADS=1,
PYTHONDONTWRITEBYTECODE=1, PYTHONPATH=src,
separate TMPDIR/basetemp (separate private
0700 basetemp child), and timeout -k 5 120
prlimit --cpu=60 --as=1073741824 for every
proof process.  No dependencies installed,
no local native execution, no unchanged
retry.

1. RUN1 the 310 focused existing units
   (test_query_embedding.py 51,
   test_source_cohort_runner.py 54,
   test_raw_hybrid_search.py 15,
   test_private_policy_request.py 45,
   test_private_policy_pin_eligibility.py
   53, test_evaluation_program.py 50,
   test_private_evaluation_preflight.py 42)
   - real exit 0; raw output run1.log
   (420 B, SHA-256
   713c4d1f6929577e8af53cfa996dadd6be5515638ad5b9bb3416b652a01ef651):
   310 passed in 9.41s.
2. RUN2 one bounded collect-only of the
   three new hosted nodes in
   test_current_cohort_encoder_producer_
   composition.py - real exit 0; raw
   output run2.log (425 B, SHA-256
   037aac5f20e12b7618a56f962b2cfdf8e13cd5a44bd3612990297d5b576e59d6):
   the three ordered node names
   (test_encoder_producer_positive_binds_
   resident_and_matches_unguarded,
   test_encoder_producer_all_case_and_
   incompatible_declaration_denials,
   test_encoder_producer_generation_change_
   denials) listed, then 3 tests collected
   in 1.04s.  Collection proves the
   transferred file is import- and
   collection-clean; it does not execute
   the hosted witnesses.
3. RUN3 one scoped six-file one-core Ruff
   on the six transferred files, taskset -c
   0 with RAYON_NUM_THREADS=1 - real exit
   0; raw output run3.log (19 B, SHA-256
   82b3e6a6c090a57601d22943bd23fca9218d1031dbe5a7b754092f9a156b4f18,
   byte-identical to the prior rounds' Ruff
   digest): All checks passed!
4. RUN4 three fresh physical import-origin
   probes, one process per order (encoder-
   first, cohort-first, grade-first): the
   three transferred src modules plus the
   five receiving dependencies
   (private_policy_pin_eligibility,
   source_bound_ranking,
   private_evaluation_preflight,
   source_bound_stage_loss,
   raw_hybrid_search) all resolve
   physically to the canonical repository
   src in every import order, and the six
   transferred working-tree SHA-256s equal
   the exact indexed digests; all real exit
   0 with ORIGINS_OK; raw streams
   run4-encoder-first.log (667 B, SHA-256
   d3653a3d89bde26dbf4b3fb7bd43c101391af4ae03226ac057da208889cf967c),
   run4-cohort-first.log (671 B, SHA-256
   a11cde085e79729ffdd97d607abf0b5c542e68d008af2a5941f9a994820738aa)
   and run4-grade-first.log (668 B, SHA-256
   0a4999e4a355a3c5d4ddbdd2d64da36d5be4effe4d0cc7d42b2f2b7fe4dc9b52).
5. RUN5 the exact working-tree hashes: all
   52 frozen receiver objects (oap/active
   at the exact transcript post-state
   `009-ap` + LF), all six transferred
   objects at their indexed postimages, and
   the absent owned destinations clean -
   real exit 0; raw output run5.log (5,362
   B, SHA-256
   9ae63885fa6d440df61293f7d73290d3ae8bdbdbbbb6a2a251e1e3d081e94ec6).
6. RUN6 the exact checker with the
   implementation argument (audit/009-ap-
   check/check-exact-transfer.py) - real
   exit 0; raw output run6-check-impl.log
   (4,092 B, SHA-256
   0495132fcfffbcab2171a1365b21a04c525ef9d87de06f347b0134b8be7ef3c2):
   52 preimages verified at the base, both
   donor topologies and receipts exact,
   transcript four objects byte-exact,
   implementation exactly the eight
   ordered paths with all six blobs at
   their donor identities.

First-attempt record (procedural
deviation, preserved): the first bounded
focus run was launched in a scratch root
created via mkdir -p whose intermediate
directory retained the default group-
writable mode 0775 (only the basetemp
child received 0700).  That run (raw
stream preserved at /dev/shm/oap-009ap-
proof.60150dee.first-attempt-0775-root/
run1.log, 220,514 B, SHA-256
eaabf98a8b3af5add5b51229999e2e8be16d0630bdaab91ad4ceb1f50833b2d9)
showed 94 failed / 216 passed, cross-suite
content-free refusals traceable to
raw_snapshot_directory._ancestor refusing
the group-writable non-root ancestor.  No
product byte was changed for the
correction; the corrected bounded run used
a fresh mktemp -d root directly under
/dev/shm verified 0700 with a separate
0700 basetemp (RUN1, 310 passed).  The
evidence is the root mode correction, not
an unchanged retry.

Mock/live distinction: all fixtures, roots
and policy material are synthetic and
operator-owned; the three hosted nodes are
hosted-only compositions over real fixtures
and the real admission/selection/pin/
encoder machinery with the trusted
synthetic delegates, and were only
collected, never executed, locally.  The
unit focus, collect-only, lint and origin
proves establish no hosted outcome, no
baseline, no native or real-model result;
no live model, credential, data, network,
GPU or hardware was touched.  No claim is
made about this report's future push/CI;
the separate post-publication receipt
records the remote facts observed after
push, and the strategic review records the
hosted outcomes at the exact report head.

## Documentation impact

STATUS.md: one new nested Current line
(009-ap) and one concise Slice 009-ap
paragraph (160 words total), recording the
six-object transfer, the private encoded
case handoff plus shared legacy grade
bookkeeping scope, the fixture facts
(encoder fixture is the existing guarded
transport synthetic case; the direct Gold
selector fixture was received in 009-af;
the encoder donor's historic 009-am gate
is not this round's evidence), the local
proof, the expected hosted proof and
baseline NOT_RUN.  docs/evaluation.md: one
new concise section (160 words) with the
same scope facts.  No other product
documentation changed.

## DHA and boundaries

Order Decision: NONE; no critical register
entry appended or read.  No consequential
candidate is reported: the scratch-root
mode slip is a local procedural deviation
corrected before any publication, fully
recorded above, with no product or
strategic effect.  Preserved: the existing
venv and physical canonical source, all
unchanged receiver objects byte-exact, the
prior 009-ao report and its recorded hosted
failure history, the unrelated parallel
work, the first-attempt raw logs, and all
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
1,998 units and exactly 997 integrations
per Product: 994 prior + three new) has
not run at publication; native execution
of the encoder witnesses is treated as
pending until that hosted proof.
Representative baseline NOT_RUN; whole 009
PARTIAL; no production or deployed
activity.  The whole cohort/grade
execution, published report content and
delivery, and further guarded composition
remain separate later ordered scopes.
Nothing in this report certifies this
report's own future push or checks; the
separate post-publication receipt and the
strategic review record those facts.
