# OAP Coding Report — 009-av

Identifier: 009-av
Result: COMPLETE
Repository: ulfe-lmi/slaif-raggedized-helper
PR number: 11
Branch: oap/009-evaluation-baseline
Base branch: main
Implementation head SHA: ea0de9eca0d9e17f03cdbc82f5b16ccfb9ae76b1
Report publication commit: SELF

## Work and scope

Exact Root FINAL order 009-av
(AMEND_EXISTING_PR on PR 11, round
base b0bed822c6f1724b702b962b3961a5f809baadf2,
the exact 009-au report head whose
prior resolution
ACCEPT_EXACT_SCOPE_CONTINUATION_ONLY
and terminal review
audit/009-au-check/Root-terminal-
review.json (SHA-256
5d41c23bcd8c593e6f873c8cbdc8f353f9e4485abf4038043be39c1edeb8422f)
established all five jobs and required
steps green with 1,440 + 1,998 units
and 1,003 integrations per Product on
run 44913264880 attempt 1; remote main
5a7b41cc512cf883b5b2cb92d87554b4d24e685b).
The bound transfer index
0f81e2a80a185a0c68a32db4c9fd7639ad2dd3cce8ed26b57182c5556151b03d
and prior resolution
e0b5b23dcfa51f7659bc36c57d01b4f1a801be9e07cf971408dbcc8decb003de
were copied byte-exact from the
strategic workorders.  Donor lane
reconciliation: donor implementation
caccb02dfc3be5e9e6663cb580227f1718924934
(sole parent 915c516c3ad83ab8657b1cc67a98f8ca94d32dc5)
with report-only child
cc7f2710cebe3fd8c1fd3eba72d2e925b4cbb785
(report SHA-256
c7b54f645ad5bacdf626dd142bb95ae34ce5fa9614ebee7d64f6705da87d18d9);
the original coordinator failure and
its regular receipts are preserved
unchanged, and the Root independent
reconciliation
parallel/guarded-graded-
report-publication/Root-response-
reconciliation.json (SHA-256
a3482e537356d0c96e7b3298a6f7440e26efda4d5059b30a4ec8ef49efb27bc8)
is retained.  GitHub reconciliation:
PR 11 is the unique open non-draft PR
with head branch
oap/009-evaluation-baseline at exactly
the round base (refs/pull/11/head and
refs/heads/oap/009-evaluation-baseline
both
b0bed822c6f1724b702b962b3961a5f809baadf2,
gh pr view OPEN / MERGEABLE /
auto-merge null over main
5a7b41cc512cf883b5b2cb92d87554b4d24e685b),
local HEAD equaled the base and the
working tree carried only the strategy
activation (oap/active exactly 7 B
009-av + LF and the new untracked
order file, byte-identical to the
strategic workorders copy, SHA-256
d3fed5c5c63badfbfb4e04f976fae11b97db496e343911f90379a5c88b5c452f).
All 38 receiving preimages were
verified byte-exact at base before
committing.  Commits pushed with this
report:

1. Transcript commit
   20ef3fb62c3c6e3f385e73052e011b4b040fd476,
   sole parent
   b0bed822c6f1724b702b962b3961a5f809baadf2,
   exactly four transcript objects
   committed byte-exact before any
   implementation change:
   oap/orders/009-av-guarded-graded-
   report-publication.md (8,253 B,
   SHA-256 d3fed5c5c63badfbfb4e04f976fae11b97db496e343911f90379a5c88b5c452f),
   oap/active (exactly 7 B 009-av +
   LF, SHA-256
   8ecfc33da6707f0ad0fc3d2f5dd7abb86d6fa7747e23689c0a6cb075845a30b4),
   oap/reviews/009-av-guarded-graded-
   report-publication-index.json
   (17,720 B, byte-exact copy of the
   strategic workorders record, SHA-256
   0f81e2a80a185a0c68a32db4c9fd7639ad2dd3cce8ed26b57182c5556151b03d)
   and
   oap/reviews/009-av-prior-resolution.
   json (1,581 B, byte-exact, SHA-256
   e0b5b23dcfa51f7659bc36c57d01b4f1a801be9e07cf971408dbcc8decb003de).
2. Implementation commit
   ea0de9eca0d9e17f03cdbc82f5b16ccfb9ae76b1,
   sole parent
   20ef3fb62c3c6e3f385e73052e011b4b040fd476,
   exactly five paths: the three exact
   indexed blobs copied from donor
   caccb02d without donor history
   (private_report_publication.py
   29,405 B -> 39,464 B, git blob
   935f0537d2d6d75e043e918276f144922c01c5d2,
   SHA-256
   7a70eaa65d99b2b43c018e6d0d4381299ca1da2bd1cc21ce702e302450170df4;
   the new
   tests/integration/test_current_
   graded_report_publication_
   composition.py 43,724 B, git blob
   164f215113a36044f8e418d656fe38fa5b9c105c,
   SHA-256
   688da09889b8edd76939a3107d2e4dc6c711710a82dcde592a7ad00093e842da;
   tests/unit/test_private_policy_
   selection.py 74,745 B, git blob
   6a115fdf6fe61b87587a06951b7ceb2cc1784e48,
   SHA-256
   c88323b595e785816f534110c04c99ceddded78b1b074ce60ff0017baacf1592,
   whose single changed line is the one
   authorized _FROZEN_OBJECTS publisher
   digest literal now tracking
   7a70eaa65d99b2b43c018e6d0d4381299ca1da2bd1cc21ce702e302450170df4
   as precisely one line) plus one
   scoped pure-addition paragraph each
   in STATUS.md (+92 lines, 0
   deletions: the current-slice header
   line and the 009-av slice paragraph
   after the complete 009-as
   paragraph) and docs/evaluation.md
   (+71 lines, 0 deletions: the new
   009-av section after the complete
   009-as section).  Every other
   product, test, workflow and doc byte
   is preserved verbatim; no grade or
   stage fixture reversion, no further
   publisher edit and no workflow
   change.

## Changed behavior

One new private product entry,
private_report_publication._publish_
current, with no public alias, reuses
the complete shared admitted-content
report transaction exactly once in its
fixed private current-report mode: the
exact _OwningGradeReport or None is
carried as the private _current_report
keyword through the single shared
_transact/_store/_stage, and the
production storage core itself invokes
the concrete current custody cut at the
two actual storage points - the
genuine pre-write cut after the real
unnamed staging fd is owned and the
genuine initial staging checks
succeeded, strictly before the first
actual report payload write, and the
genuine post-prelink cut after the
genuine prelink metadata verification,
strictly before any state transition or
the first possible link.  No generic
callable guard hook, numeric switch
value or second transaction route
exists (one def _transact, one def
_store, one os.link; publish still
calls _transact once).  The duplicated
bounded directory/digest content
handling is factored into the one
shared fixed body _bounded_parts and
_digest_identity with the legacy
admission byte-for-byte preserved.
_admit_current verifies only the
authentic immutable owner-bound grade
result minted by the successful
genuine grade final cut (the ordinary
legacy Report is refused at this entry
before any separate storage behavior);
it verifies the exact admitted bytes
and digest, the retained plan, the
original active operation, stores and
capture, the copied grants and the
original end.  _current_cut re-
verifies the retained exact live
custody under its own short
nonblocking owner borrow, keeps the
real live same-owner association and a
genuine same-admission selected reread
under the original end with no new
full raw pin, saves and restores the
checked original operation's exact old
end in finally, releases the owner
guard independently on every exit, and
checks the original absolute cutoff
before the protected effect, the safe
release and the receipt.  The separate
short release cut runs only after the
genuine storage transaction's owned
cleanup finishes for both PUBLISHED
and EXISTING; only the actual
successful release cut releases the
narrow content-free receipt.  An
ordinary denial after actual
durability preserves DURABLE/CLEAN and
suppresses the receipt, is normalized
outside the caught exception handler
so the PublicationError carries no
data-bearing __context__ from the
underlying namespace/authority error,
and retains the fixed text, the
observed storage and cleanup truth and
the original non-Exception interruption
identity.  Errors expose the fixed
vocabulary with no payload, path,
identity or underlying namespace
exception context.  The public legacy
publisher and the shared policy payload
and selection writers retain their
separate admission and behavior.  The
new three-node hosted witness drives
the actual product entry over the real
successful h1/h4 grade producer with b
still physically in the same raw pin
and genuinely withheld on the same
live capture; report I/O is attributed
by the captured staging-inode
liveness and the report destination so
a reused fd number never counts and
nested genuine selected-policy writer
I/O cannot count as report work.  No
public API, grade product, budget,
workflow, runtime or CLI change.

## Acceptance evidence

1. AC1 (authentic owner-bound
   admission, one shared transaction,
   separate legacy/policy admission):
   the transferred publisher carries
   the one fixed private entry with
   _admit_current verifying the exact
   admitted bytes and digest, retained
   plan, original active operation/
   stores/capture, copied grants and
   original end; _bounded_parts and
   _digest_identity are the single
   shared fixed body with legacy
   admission preserved byte-for-byte;
   the legacy/public and policy
   payload/selection paths are
   unchanged on their ordinary route
   (one def _transact, one def _store,
   one os.link).  Behavior at runtime
   is proven by the hosted witnesses
   below (PENDING) and by the 388
   focused units at the transferred
   bytes (RUN1).
2. AC2 (real unnamed staging boundary
   cuts, no new full raw pin, saved-
   end restore, independent guard
   release): the two custody cuts are
   invoked by the production storage
   core at the genuine pre-write and
   post-prelink points; _current_cut
   keeps the short live association
   and genuine same-admission selected
   reread under the original end,
   restores the exact saved end in
   finally, releases the guard
   independently on every exit and
   checks the original absolute
   cutoff before the protected effect,
   the safe release and the receipt.
   The pure fixture-teardown proof
   (RUN6) verifies the exact teardown
   and both pre-handoff closure paths
   with synthetic owners, separate
   from test collection; the genuine
   staging-boundary behavior is
   exercised by the three hosted nodes
   (PENDING).
3. AC3 (post-cleanup release cut,
   truthful denial, fixed error
   vocabulary): the release cut runs
   only after the actual successful
   transaction cleanup for PUBLISHED
   and EXISTING; the ordinary
   after-cleanup denial is normalized
   outside the caught handler with no
   data-bearing __context__ and
   preserves DURABLE/CLEAN and
   suppresses the receipt; errors
   expose only the fixed vocabulary.
   Asserted by the stable hosted node
   and the P1/P2 denial witnesses
   (PENDING); the 388 focused units
   keep the fixed-vocabulary and
   context-free paths green at these
   bytes (RUN1).
4. AC4 (three hosted nodes over real
   h1/h4 production with b withheld):
   the exact three node names are
   collected (RUN2): test_current_
   graded_report_publication_stable_
   published_and_existing,
   test_current_graded_report_
   publication_change_before_first_
   write and test_current_graded_
   report_publication_change_before_
   post_prelink.  They verify exact
   bytes on PUBLISHED and EXISTING,
   genuine selected generation
   replacement between successful
   cleanup and release, real selected
   generation changes at P1 and P2,
   zero attempted report writes and
   links at P1, completed staging but
   zero links at P2, real report-slot
   cleanup and retirement at both,
   NOT_PUBLISHED/CLEAN retained, and
   fd/inode/destination attribution so
   nested policy writer I/O cannot
   count as report work.  Native
   outcomes remain PENDING the hosted
   observations.
5. AC5 (exact topology, local proof,
   hosted gate): the ordered checker
   audit/009-av-check/check-exact-
   receiving.py (SHA-256
   f891c3cc675ae9118291dd8f9cd69508fa8c2c0ce59276f12b52574f804ae7ac,
   verified before use) exited 0 in
   implementation mode on
   ea0de9eca0d9e17f03cdbc82f5b16ccfb9ae76b1,
   verifying the base -> transcript ->
   implementation topology, the four
   transcript objects byte-exact, the
   three transfers byte-equal to donor
   caccb02d, all 38 receiving
   preimages at base and preserved at
   the implementation, and the
   add-only documentation diffs; it
   will be rerun with --report before
   push.  Locally: 388/388 focused
   existing units (89 publisher, 62
   policy payload, 68 selection, 71
   capture, 45 request, 53 pin-
   eligibility), the exact three
   hosted nodes collected only, scoped
   two-file one-core Ruff, two fresh
   physical import orders and the pure
   fixture-teardown proof, all exit 0
   (RUN1-RUN6).  The exact remote
   report gate - all five jobs and
   required steps, the unchanged
   ordered 1,440 + 1,998 units and
   exactly 1,006 integrations in each
   Product including all three new
   witnesses - is required at the
   exact report head and is PENDING at
   publication.

## Verification

Ordered local proof in a fresh mode-
0700 /dev/shm scratch
/dev/shm/009av-coding over a pristine
tree (git archive of implementation
ea0de9eca0d9e17f03cdbc82f5b16ccfb9ae76b1,
physically re-verified: the three
transfers at the exact SHA-256 values
above; physical-inputs.txt 1,121 B,
SHA-256
4bc3fd580c5524773bc14371f12e86497c6c961c9919cdcc5bf03e5eb33fe2cb),
pre-existing checked venv (Python
3.14.4, pytest 8.4.2, ruff 0.17.4), no
dependencies installed, -o addopts= -p
no:cacheprovider, separate private 0700
basetemps, OPENBLAS_NUM_THREADS=1,
PYTHONDONTWRITEBYTECODE=1,
RAYON_NUM_THREADS=1, PYTHONPATH the
proof tree src, and
timeout -k 5 120 prlimit --cpu=60
--as=1073741824 for every proof
process:

1. RUN1 the 388 focused existing units
   (test_private_report_publication.py
   89, test_private_policy_payload.py
   62, test_private_policy_selection.
   py 68, test_private_policy_capture.
   py 71, test_private_policy_request.
   py 45, test_private_policy_pin_
   eligibility.py 53) - real exit 0;
   raw focus.log (501 B, SHA-256
   ffc642376c897a872a512aba6c1fb1187f60a65b1dfa2fda9daa792f06f51b77):
   388 passed in 16.05s.
2. RUN2 the exact hosted collect-only
   (test_current_graded_report_
   publication_composition.py) - real
   exit 0; raw collect.log (447 B,
   SHA-256
   2e2d303cc8274232fcc1c093f3eb909f5a8412e0cbe6bd67fc743bb6b8244e96):
   3 tests collected, the exact three
   ordered node names above, without
   executing fixture assertions at
   import.
3. RUN3 the scoped two-file one-core
   Ruff (taskset to one core,
   RAYON_NUM_THREADS=1) over
   private_report_publication.py and
   the new witness - real exit 0; raw
   lint.log (19 B, SHA-256
   82b3e6a6c090a57601d22943bd23fca9218d1031dbe5a7b754092f9a156b4f18):
   All checks passed!
4. RUN4/RUN5 two fresh physical import
   -order probes, one process per
   order (publisher-first
   private_report_publication,
   private_policy_selection,
   evaluation_program,
   private_policy_payload and policy-
   selection-first
   private_policy_selection,
   private_report_publication,
   private_policy_payload,
   evaluation_program): every
   production module resolves
   physically to the canonical proof
   tree src in both orders; both real
   exit 0; raw origins.log (840 B,
   SHA-256
   f2cd771d76f330ebd926977464b9fab0114ef4c4e9e1f467cb9ae17bde51d447).
5. RUN6 the pure fixture-teardown
   proof, run from the strategic home
   as python3 -B audit/009-av-check/
   check-fixture-teardown.py over the
   physical committed witness file,
   separate from test collection -
   real exit 0; raw pure.log (169 B,
   SHA-256
   88afffa9796ca7b40fed79ae4aa2d8ee4190504f8bfee7bc8a83c2e0a8226a1d):
   "Exact teardown preserved failure
   identity and attempted all four
   owners in six cases." and "Exact
   pre-handoff failures closed the
   entered encoder once and preserved
   priority."
6. Ordered checker (implementation
   mode, post-commit) - real exit 0,
   JSON output recording base
   b0bed822, transcript 20ef3fb6,
   implementation ea0de9ec, donor
   caccb02d, transfer index SHA-256
   0f81e2a8, 38 receiving preimages
   and the three exact transfer
   objects; the --report mode runs
   after the report-only commit and
   before push.

The lint, pure and exit logs are
byte-identical to the independent
strategic receiving preview logs of
the same names recorded in the bound
transfer index (SHA-256
82b3e6a6c090a57601d22943bd23fca9218d1031dbe5a7b754092f9a156b4f18,
88afffa9796ca7b40fed79ae4aa2d8ee4190504f8bfee7bc8a83c2e0a8226a1d
and
c811c3034af1b6e838ebc8646eb9725f8ec4fad1636c336b17029c125e7fd6e7
respectively); the focus and collect
logs differ from the preview only in
the trailing wall-clock field, and the
origin log differs only in the scratch
path prefix, with the same eight
module-to-canonical-src lines in the
same order.  Raw exit inventory
exit.log (238 B, SHA-256
c811c3034af1b6e838ebc8646eb9725f8ec4fad1636c336b17029c125e7fd6e7):
both import orders, focus, collect,
lint and pure all 0.

Mock/live distinction: all fixtures,
roots and policy material are
synthetic and operator-owned.  The
three hosted nodes are hosted-only
synthetic compositions over the real
admission/cut/pin/grade machinery
with the trusted synthetic delegates,
and were only collected, never
executed, locally.  The 388 focused
units, collect-only, lint, origin
proofs and the pure teardown establish
no hosted outcome, no baseline, no
native or real-model result; no live
model, credential, data, network, GPU
or hardware was touched.  No claim is
made about this report's future push/
CI; the separate post-publication
receipt records the remote facts
observed after push, and the strategic
review records the hosted outcomes at
the exact report head.

## Documentation impact

One scoped pure-addition paragraph in
STATUS.md (current-slice header line
plus the 009-av slice paragraph after
the complete 009-as paragraph) and one
new section in docs/evaluation.md
(after the complete 009-as section)
record the current guarded stored/
report-release paths, the synthetic
witness scope, the local proof, the
expected hosted results presented as
pending, and the retained baseline
NOT_RUN and the true scope of the
existing grade evidence.  No existing
documentation line was modified, and
no documented command, measured
performance, license clearance or
readiness claim was added.

## DHA and boundaries

Order Decision: NONE; no critical
register entry appended or read.  No
consequential candidate is reported:
the transfer is the exact reviewed
guarded publication the order bounds,
with the sole fixture literal update
authorized by the recorded scope
supplement.  Preserved: the existing
venv and physical canonical source,
every product, test and fixture byte
outside the five implementation paths
(including the repaired canonical
grade witness and stage fixture), the
009-au report head and its run
evidence, the donor lane receipts
including the original coordinator
failure and the Root reconciliation,
the protected automation, the
unrelated parallel work, and all
unrelated repository state; scratch
artifacts preserved in the fresh 0700
/dev/shm scratch /dev/shm/009av-coding.
No new dependencies, live model,
corpus, credentials, service,
hardware, deploy or release activity.
No merge performed; PR 11 remains
OPEN with auto-merge off; no 010 and
no next work chosen.

## Limitations and remaining work

Hosted proof is PENDING: the fresh
exact report-head gate (all five jobs
and every required step, both
Products at ordered 1,440 + 1,998
units and exactly 1,006 integrations
per Product including the three new
witnesses) has not run at publication,
and the native execution of the three
hosted witnesses remains pending until
that hosted proof.  Representative
baseline NOT_RUN; whole 009 PARTIAL;
no production or deployed activity.
The named operator command,
representative baseline, live
hardware qualification, workflow
change, merge, deployment and release
remain outside this order's scope.
Nothing in this report certifies this
report's own future push or checks;
the separate post-publication receipt
and the strategic review record those
facts.
