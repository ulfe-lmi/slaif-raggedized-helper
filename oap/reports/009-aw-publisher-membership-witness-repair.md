# OAP Coding Report — 009-aw

Identifier: 009-aw
Result: COMPLETE
Repository: ulfe-lmi/slaif-raggedized-helper
PR number: 11
Branch: oap/009-evaluation-baseline
Base branch: main
Implementation head SHA: fc4c95a4979401a226d24094a60492a00afd7761
Report publication commit: SELF

## Work and scope

Exact Root FINAL order 009-aw
(AMEND_EXISTING_PR on PR 11, round
base 13563000b2e44f01f455ca880744017c0e6433da,
the exact 009-av report head whose
prior resolution
REJECT_EXACT_HOSTED_GATE_MEMBERSHIP_
FIXTURE (head run 44923276160 attempt
1 passed all three OAP jobs and both
ordered Product unit sets, 1,440 +
1,998, each Product completing 1,006
integration nodes with 1,003 passes
and the same three failed publisher
nodes) and terminal review
audit/009-av-check/Root-terminal-
review.json (SHA-256
1a8f5ab40c5ee9263c245f394fb07bda2d217651ce0dd15dcff9e74feb4137c9)
established the exact shared-fixture
line-253 fault; remote main
5a7b41cc512cf883b5b2cb92d87554b4d24e685b).
The prior resolution was copied
byte-exact from the strategic
workorders to oap/reviews/009-aw-
prior-resolution.json (593 B,
SHA-256
3fb75d31bd261426e039c6aedd550a62120725ba0fbf67b921f0e1004f88b24f).
GitHub reconciliation: PR 11 is the
unique open non-draft PR with head
branch oap/009-evaluation-baseline at
exactly the round base (refs/
pull/11/head and refs/heads/
oap/009-evaluation-baseline both
13563000b2e44f01f455ca880744017c0e6433da,
base main
5a7b41cc512cf883b5b2cb92d87554b4d24e685b,
auto-merge null), local HEAD equaled
the base and the working tree carried
only the strategy activation (oap/
active exactly 7 B 009-aw + LF and
the new untracked order file,
byte-identical to the strategic
workorders copy, SHA-256
f64dec360c8b8b39e1115acbc835a02e693b877e35ccfd1eb5f6b84a02d8e3a7).
The witness preimage was verified at
base (git blob
164f215113a36044f8e418d656fe38fa5b9c105c,
43,724 B, SHA-256
688da09889b8edd76939a3107d2e4dc6c711710a82dcde592a7ad00093e842da),
and the ordered pure checker
reproduced the exact prior fault on
the genuine membership Entry type at
that base before any edit
(--expect-old-fault, output
byte-identical to the strategic log
audit/009-aw-check/Root-exact-prior-
negative.log, SHA-256
07ffd619c00d8d45daf7f4a9fb557b11fe2b86ebafac34363b165fc8fc71eb78).
Commits pushed with this report:

1. Transcript commit
   0ba4007af69fd9a1f0a0f992d8422f4482707be9,
   sole parent
   13563000b2e44f01f455ca880744017c0e6433da,
   exactly three transcript objects
   committed byte-exact before any
   implementation change:
   oap/orders/009-aw-publisher-
   membership-witness-repair.md
   (6,293 B, SHA-256
   f64dec360c8b8b39e1115acbc835a02e693b877e35ccfd1eb5f6b84a02d8e3a7),
   oap/active (exactly 7 B 009-aw +
   LF, SHA-256
   3982c8b2944410e3af3889e4aa5e7c00f8688a23399df974cedbac2bd2e66690)
   and oap/reviews/009-aw-prior-
   resolution.json (593 B, byte-exact,
   SHA-256
   3fb75d31bd261426e039c6aedd550a62120725ba0fbf67b921f0e1004f88b24f).
2. Implementation commit
   fc4c95a4979401a226d24094a60492a00afd7761,
   sole parent
   0ba4007af69fd9a1f0a0f992d8422f4482707be9,
   exactly one path:
   tests/integration/test_current_
   graded_report_publication_
   composition.py (43,724 B ->
   44,378 B, git blob
   164f215113a36044f8e418d656fe38fa5b9c105c
   -> eb5a97a86e6d9acecc893f475f9ed5868c1312cc,
   SHA-256
   688da09889b8edd76939a3107d2e4dc6c711710a82dcde592a7ad00093e842da
   -> 7238a4e7dac9db505542338133accadf0b48debe89ea9b772afdfed5d1ecd2b2).
   All three test bodies, all other
   fixture bytes, docs, product,
   workflow, other tests and
   dependencies stay exact; no
   production edit, no test addition
   or removal, no CLI, no dependency
   change.

## Changed behavior

Test-only repair of the shared
guarded publisher witness fixture
(_fixture in
test_current_graded_report_
publication_composition.py).  The
held_rows block now reads the actual
owner.value.data.row_map.rows as the
common test-local assignment at the
start of the comparison, proves
member_b.ordinals nonempty, and for
each declared ordinal proves the
exact ordinal, bundle ID (the b ID
extracted from the actual bundle IDs
and omitted by the actual projected
declaration), revision ID,
extraction ID and partition ID
against the actual held row, with
exactly one matching row required
per ordinal and no unused or
invented Entry field (the faulting
Entry.batch_container_id reference is
gone; the genuine membership-to-row
association is via Entry.ordinals).
After the real current admission and
captured policy snapshot, the
existing
supplied_policy_eligibility.
unavailable_partitions is called on
the actual policy_snapshot and
held.data.membership, and the actual
b partition is asserted unavailable,
with the single import line from the
canonical grade witness (including
its noqa) as the only new import.
The real b pin, projected a/c h1/h4
grade, native producer/publisher
calls, all teardown and actual I/O
assertions are preserved verbatim.
No product, CLI, workflow, doc,
runtime or dependency behavior
changed.

## Acceptance evidence

1. AC1 (actual held row membership
   proof): the repaired block keeps
   the b ID extracted from the actual
   bundle IDs and omitted by the
   actual projected declaration,
   keeps held_rows as the common
   test-local assignment at the start
   of the comparison, reads the
   actual owner.value.data.row_map.
   rows, proves member_b.ordinals
   nonempty and proves the exact
   ordinal, bundle ID, revision ID,
   extraction ID and partition ID
   against the actual held row for
   each declared ordinal (exactly one
   matching row each), using only
   genuine Entry fields.  Behavior is
   proven by the ordered pure checker
   on the actual Entry/Row types
   (RUN6) and by the three hosted
   nodes over the real pin (PENDING).
2. AC2 (actual selected-policy
   withholding): after the real
   current admission and captured
   policy snapshot the existing
   supplied_policy_eligibility.
   unavailable_partitions is called
   on the actual policy_snapshot and
   held.data.membership and the
   actual b partition is asserted
   unavailable; the real b pin,
   projected a/c h1/h4 grade, native
   producer/publisher calls, all
   teardown and actual I/O
   assertions are preserved, and the
   single import line from the
   canonical grade witness (with its
   noqa) is the only new import
   (exactly one occurrence verified
   by the ordered topology checker).
3. AC3 (exact patched row-proof
   block, positive and five
   negative bindings): the ordered
   pure checker
   audit/009-aw-check/check-pure-
   membership.py (SHA-256
   c5b5434c4c9f54e9ef131fe2e7d8ed4caebea3f196ca76a86c224375fffaef3a,
   verified before use) extracted the
   exact comparison between
   held_rows and the assignment to
   ctx.pointer_generation, executed
   it with the real
   raw_snapshot_membership.Entry and
   raw_snapshot_rows.Row over the
   physical source, passed the one
   positive binding and rejected all
   five wrong bindings (RUN6); the
   exact prior fault was reproduced
   at the failed base before the
   edit (--expect-old-fault output
   byte-identical to the strategic
   log).
4. AC4 (exact topology and local
   proof): the ordered topology
   checker audit/009-aw-check/
   check-exact-repair.py (SHA-256
   80c156e62f1fa0a75b817024db4d80fb68b86f9b2ab3fcd1ee2c5eb26e94158a,
   verified before use) exited 0 in
   implementation mode on
   fc4c95a4979401a226d24094a60492a00afd7761,
   proving the exact transcript,
   the test-only implementation
   scope and the byte-exact controls,
   and will be rerun with --report
   after the report-only commit and
   before push.  Locally: 388/388
   focused existing units (89
   publisher, 62 policy payload, 68
   selection, 71 capture, 45 request,
   53 pin eligibility), the exact
   three hosted nodes collected only,
   scoped one-file one-core Ruff, two
   fresh physical import orders and
   the pure membership checker, all
   exit 0 (RUN1-RUN6).  The exact
   remote report gate - all five
   jobs and every required step, both
   Products at ordered 1,440 + 1,998
   units in their existing order and
   exactly 1,006 integrations in each
   Product - is required at the new
   exact report head and is PENDING
   at publication.

## Verification

Ordered local proof in a fresh mode-
0700 /dev/shm scratch
/dev/shm/009aw-coding over a
pristine tree (git archive of
implementation
fc4c95a4979401a226d24094a60492a00afd7761,
physically re-verified: the repaired
witness at SHA-256
7238a4e7dac9db505542338133accadf0b48debe89ea9b772afdfed5d1ecd2b2
equals the committed blob
eb5a97a86e6d9acecc893f475f9ed5868c1312cc),
pre-existing checked venv (Python
3.14.4, pytest 8.4.2, ruff 0.17.4),
no dependencies installed, -o
addopts= -p no:cacheprovider,
separate private 0700 basetemps,
OPENBLAS_NUM_THREADS=1,
PYTHONDONTWRITEBYTECODE=1,
RAYON_NUM_THREADS=1, PYTHONPATH the
proof tree src, and timeout -k 5 120
prlimit --cpu=60 --as=1073741824 for
every proof process:

1. RUN1 the 388 focused existing
   units (test_private_report_
   publication.py 89, test_private_
   policy_payload.py 62, test_
   private_policy_selection.py 68,
   test_private_policy_capture.py 71,
   test_private_policy_request.py 45,
   test_private_policy_pin_
   eligibility.py 53) - real exit 0;
   raw focus.log (501 B, SHA-256
   7923473ca93d57c9cb453daf3b5aa7d7e5185023b4c9cc8dcb723c9ab79b646a):
   388 passed in 16.09s.
2. RUN2 the exact hosted collect-only
   (test_current_graded_report_
   publication_composition.py) -
   real exit 0; raw collect.log
   (447 B, SHA-256
   55e82a77939517a76a2ce811f0f56a45dbee815e6cafc8a6036da936f8e9fb69):
   3 tests collected -
   test_current_graded_report_
   publication_stable_published_and_
   existing, test_current_graded_
   report_publication_change_before_
   first_write and test_current_
   graded_report_publication_change_
   before_post_prelink - without
   executing fixture assertions.
3. RUN3 the scoped one-file one-core
   Ruff (taskset to one core,
   RAYON_NUM_THREADS=1) over the
   repaired witness - real exit 0;
   raw lint.log (19 B, SHA-256
   82b3e6a6c090a57601d22943bd23fca9218d1031dbe5a7b754092f9a156b4f18):
   All checks passed!
4. RUN4/RUN5 two fresh physical
   import-order probes, one process
   per order (policy-eligibility-
   first supplied_policy_
   eligibility, private_policy_pin_
   eligibility, private_report_
   publication, private_policy_
   selection, evaluation_program,
   private_policy_payload and
   publisher-first private_report_
   publication, supplied_policy_
   eligibility, private_policy_pin_
   eligibility, private_policy_
   selection, evaluation_program,
   private_policy_payload): every
   production module resolves
   physically to the canonical proof
   tree src in both orders; both
   real exit 0; raw origins1.log
   (768 B, SHA-256
   8627a039fe6ba473604388163081fc78142aac931fb9098e98246b2c924d4252)
   and origins2.log (768 B, SHA-256
   e7f0dba59b7ae067fbc75c17106b59a11088e45a85ab71e74799d5edc076f68a).
5. RUN6 the ordered pure membership
   checker, run from the strategic
   home as python3 -B audit/009-aw-
   check/check-pure-membership.py
   over the physical committed
   witness file in the pristine
   proof tree - real exit 0; raw
   pure.log (87 B, SHA-256
   eed19a8da732df729bdfe05cba3d7a04e30621f1188ccde3bf2bf17b993bb67f):
   "Exact fixture block passed with
   real Entry/Row types and rejected
   five wrong bindings."  The same
   checker in --expect-old-fault
   mode over the exact base witness
   reproduced the precise prior
   AttributeError before the edit.
6. Ordered topology checker
   (implementation mode, post-
   commit) - real exit 0, JSON
   output recording base
   13563000b2e44f01f455ca880744017c0e6433da,
   transcript
   0ba4007af69fd9a1f0a0f992d8422f4482707be9,
   implementation
   fc4c95a4979401a226d24094a60492a00afd7761,
   changed witness blob
   eb5a97a86e6d9acecc893f475f9ed5868c1312cc
   (44,378 B, SHA-256
   7238a4e7dac9db505542338133accadf0b48debe89ea9b772afdfed5d1ecd2b2)
   and the scope statement; the
   --report mode runs after the
   report-only commit and before
   push.

Raw exit inventory exit.log (54 B,
SHA-256
c3f9d77d13b3b809a234b9e5d165cdf17a6c2239e9fad9ddee4f7e21e12b2ae2):
both import orders, focus, collect,
lint and pure all 0.

Mock/live distinction: all fixtures,
roots and policy material are
synthetic and operator-owned.  The
three hosted nodes are hosted-only
synthetic compositions over the real
admission/cut/pin/grade machinery
with the trusted synthetic
delegates, and were only collected,
never executed, locally.  The 388
focused units, collect-only, lint,
origin proofs and the pure checker
establish no hosted outcome, no
baseline, no native or real-model
result; no live model, credential,
data, network, GPU or hardware was
touched.  No claim is made about
this report's future push/CI; the
separate post-publication receipt
records the remote facts observed
after push, and the strategic review
records the hosted outcomes at the
exact report head.

## Documentation impact

None: existing documentation and all
previous reports are preserved
byte-exact.  The native fixture
failure (exact line-253
AttributeError on the genuine
membership Entry at the failed base)
and the exact proof (pure checker
positive and five negative bindings,
fault reproduction, topology
verification) are recorded in this
immutable report only.  All new
native publication outcomes are
treated as pending hosted proof.  No
documented command, measured
performance, license clearance or
readiness claim was added.

## DHA and boundaries

Order Decision: NONE; no critical
register entry appended or read.  No
consequential candidate is reported:
the repair is the exact shared
fixture witness correction the order
bounds.  Preserved: the existing
venv and physical canonical source,
every product, test, fixture, doc
and workflow byte outside the one
implementation path (including the
canonical grade witness
test_current_graded_cohort_
composition.py and all stage
fixtures), the 009-av report head
13563000b2e44f01f455ca880744017c0e6433da
and its run 44923276160 evidence,
the rejected report and all exact
logs, the protected automation, the
unrelated parallel work and all
unrelated repository state; scratch
artifacts preserved in the fresh 0700
/dev/shm scratch /dev/shm/
009aw-coding.  No dependency setup,
credential, live data, model,
service or hardware action.  No
merge performed; PR 11 remains OPEN
with auto-merge off; no 010 and no
next work chosen.

## Limitations and remaining work

Hosted proof is PENDING: the fresh
exact report-head gate (all five
jobs and every required step, both
Products at ordered 1,440 + 1,998
units in their existing order and
exactly 1,006 integrations in each
Product, the three publisher nodes
now past the repaired fixture to real
grade and publication) has not run
at publication, and the native
execution of the three hosted
witnesses remains pending until that
hosted proof.  Representative
baseline NOT_RUN; whole 009 PARTIAL;
no production or deployed activity.
Production edits, test additions or
removals, CLI, local native
execution, live data, hardware
qualification, merge, deployment and
release remain outside this order's
scope.  Nothing in this report
certifies this report's own future
push or checks; the separate post-
publication receipt and the
strategic review record those facts.
