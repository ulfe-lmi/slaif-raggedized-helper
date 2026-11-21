# OAP Coding Report — 009-ax

Identifier: 009-ax
Result: COMPLETE
Repository: ulfe-lmi/slaif-raggedized-helper
PR number: 11
Branch: oap/009-evaluation-baseline
Base branch: main
Implementation head SHA: 0e4b0c6d42b2d0ab05cfe2fa5024924c8a4ad3a2
Report publication commit: SELF

## Work and scope

Exact Root FINAL order 009-ax
(AMEND_EXISTING_PR on PR 11, round
base 4e7236116492812ee3cd3b19fd4acf8730e0a9a6,
the exact 009-aw report head whose
prior resolution
ACCEPT_EXACT_SCOPE_CONTINUATION_ONLY
(run 44929451957 attempt 1: all five
required jobs and every required step
SUCCESS at both Products, ordered
1,440 + 1,998 units each, exactly
1,006 integrations each, including
all three guarded publication nodes)
and terminal review
audit/009-aw-check/Root-terminal-
review.json (SHA-256
b93c939071c2ba9460bef64f410d1df7f0cd75427edbe0f6ba2c34bad26c00f2)
established the qualified receiving
state; remote main
5a7b41cc512cf883b5b2cb92d87554b4d24e685b).
The prior resolution was copied
byte-exact from the strategic
workorders to oap/reviews/009-ax-
prior-resolution.json (1,417 B,
SHA-256
009fdfe79fbb0ae60fb382444b2685636b4807ac60dfe6f7b6b4659f7c9177a1)
and the bound transfer index to
oap/reviews/009-ax-evaluate-expected-
pin-index.json (11,232 B, SHA-256
09f00024ed08c58487f0740fc022fcc538a7855d9f1e900e45e2ec2390cbe99d).
GitHub reconciliation: PR 11 is the
unique open non-draft PR with head
branch oap/009-evaluation-baseline at
exactly the round base (headRefOid
4e7236116492812ee3cd3b19fd4acf8730e0a9a6,
base main
5a7b41cc512cf883b5b2cb92d87554b4d24e685b,
autoMergeRequest null), local HEAD
equaled the base, and the working
tree carried only the strategy
activation (oap/active exactly 7 B
009-ax + LF and the new untracked
order file, byte-identical to the
strategic workorders copy, SHA-256
7960f92fd09486fbcfb5e740a3cac02b8c99112675e27b5b4e8eff1f5bf19da0).
The local expected-pin donor was
verified before transfer: donor
implementation 77b0a94ad2e0b87f490058ceb0db20185f6f2adc with sole
parent b0bed822c6f1724b702b962b3961a5f809baadf2, report-only child
50a66a7594a3e99898b1cbbc310f9dc4f5bfb0f6 diffing exactly
oap/parallel/reports/PAR-009-
EVALUATE-EXPECTED-PIN-A.json (SHA-256
368a9f7d97f75f9da10ce21926b2464ab1b70d4226de6e30acba8fd8eed71e21),
root independent evidence
audit/009-evaluate-expected-pin-local-
resolution.json (SHA-256
f6265a2520949fbf5e7af54b9464060ad6d8258857bf10b9d91684b3261b02c7)
and the exact receiving preview
audit/009-expected-pin-receiving/
Root-inertreceiving-preview-
4e723611.json (SHA-256
55786035a95f8f869d6c2fff67f1c2512a27951b4281ae5f4edabb1c7d78dc22).
The transcript-first four-path commit
688e0f0ed507100974b9dd501a5a932e69e12b3e
records the exact order, oap/active
(009-aw to 009-ax, 7 B + LF) and both
byte-exact review copies over the
exact base; the implementation commit
0e4b0c6d42b2d0ab05cfe2fa5024924c8a4ad3a2
copies the two exact reviewed donor
blobs only, with no donor history, no
source merge and no fixture reversion.

## Implementation

src/slaif_raggedized_helper/
raw_snapshot_pin.py (15,648 B, git
blob ec922fee1e404ec4e776eda94e65399b85b54f73,
SHA-256
4ed3ce40d95b3bd08def08fd8b4ab6a66604ba8f87de3c2fec32a3bb6c99f736)
gains the one fixed private guarded
expected-ID-and-generation
acquisition entry
PinOwner._acquire_expected_selected_
data for the named evaluation over
already opened, approved stores. It
takes the current exact store types
and root plus one already established
absolute monotonic end bounded by the
existing 120-second acquisition
ceiling, and admits the mandatory
exact canonical snapshot ID (the
optional legacy None sentinel is
refused before any namespace resource
is created or opened) and the non-
bool integer generation within the
existing canonical pointer grammar
and _MAX_GENERATION bound; an already
elapsed end is refused before any
namespace resource. The working
operation is fixed to that original
finite nominal end before any
namespace work (no re-derived
relative clock), and one original
timeout is preserved at each actual
protected start and check. The
legacy relative route and the new
expected route share the one actual
selected acquisition body
_selected_acquisition: after the
original guard and creator/type checks
already run in the start, it takes
the real shared snapshots-parent
selection lock, admits the pointer,
and - in the expected route - compares
the requested ID and generation
immediately after the actual pointer
read under that same selection lock
and before any protected data load or
target open, so an absent or changed
selection is refused there with the
exact fixed content-free PinError and
a previously read pointer or a
caller-facing post-load comparison
cannot serve as the guard. The shared
body then performs the real initial
full load, the exact target lock, the
association, the second full equality,
the final repeated pointer equality
and the existing lock handoff; on
success the exact owned PinData and
operation are retained with the
unchanged original absolute end. The
nested directory loaders keep their
existing independent cooperative
bound, and a late actual nested load
result is unusable at the original
end by the deadline checks around
each protected step (documented,
without claiming an in-flight
OS/native call is interrupted). The
real shared legacy and expected
acquisition, original full validation,
actual target lock, final repeated
pointer equality, unchanged relative
legacy/retirement behavior and precise
owned cleanup (independent finite
cleanup, truthful pending ownership,
non-Exception interruption
propagation) are preserved; no
authorization, alternate loader,
callback, provider/clock change or
new public API is added.

tests/integration/test_evaluate_
expected_raw_pin_composition.py (10,
655 B, git blob
9b38ccf1e7e467c1b2f67c84a4d5c23aaf65851b,
SHA-256
9c62bf21dfbd1237a2efc0211faeec6977ed55dcc3e8fec13b6d63d73e673d95)
is the new owned module holding the
two exact additive hosted synthetic
witness nodes over the existing real
two-snapshot fixture (the reviewed
pin-composition fixture imported as
helpers: setup_pair,
restore_owned_directories, actual):
test_expected_acquisition_accepts_
exact_selected_id_and_generation
holds the real fixture pair, acquires
under the mandatory exact selected
ID/generation with end = now+60 in a
guarded finally that closes the owner
even when an assertion fails, verifies
the returned PinData holds the exact
current pointer, both real loads
observe the same op.end == end and
the owner operation keeps the original
absolute end, proves the separate-fd
exclusive flock released the real
held target, and in its one closely
bounded subcase advances only the
selection module's observed clock at
the exact real load-return boundary
through a local test-only clock proxy
(real monotonic preserved before the
boundary, past the fixed end reported
afterwards, patch restored, no product
clock change, no wall-clock wait),
showing the actual late load ran once
and no PinData becomes usable; and
test_expected_acquisition_refuses_
malformed_stale_and_changed proves the
missing (None) ID, bool generation,
zero, _MAX_GENERATION+1, 63-hex ID,
None store and expired end perform
zero namespace work with the full
open, pointer and owner-open logs
asserted empty, the separate wrong-
ID and stale same-ID-generation cases
(the latter after a real same-ID
reselect) and the real intervening
change to the other snapshot perform
zero actual data loads and zero target
opens, counting the actual selection-
lock open, pointer, directory-load and
target-open events on the same
acquisition operation, with the exact
fixed content-free PinError message,
truthful fd cleanup, CLOSED owner
state and released guard.

## Acceptance evidence

1. One exact private expected-ID and
   generation route exists
   (_acquire_expected_selected_data);
   it refuses malformed, expired or
   mismatched values at the
   appropriate pre-effect boundary
   (mandatory canonical ID and
   bounded generation admitted and the
   elapsed end refused before any
   namespace resource; the same-lock
   mismatch refused content-free
   immediately after the real pointer
   read). No generic provider/clock or
   public interface change: the only
   new surface is the one private
   entry, and the working operation is
   fixed to the original finite
   nominal end before namespace work.
2. The real shared legacy and expected
   acquisition, original full
   validation, actual target lock,
   final repeated pointer equality,
   unchanged relative legacy/retirement
   behavior and precise owned cleanup
   are preserved by both routes
   reusing _selected_acquisition; a
   late actual nested load result is
   unusable at the original end (the
   deterministic late-load subcase),
   and the nested real loader stays
   cooperatively bounded per its
   existing behavior.
3. Both exact additive native
   witnesses are present and verified
   collect-only locally: the positive
   node (true selected stable PinData
   under the exact end, actual
   retained lock close, deterministic
   observed expiry after the real
   nested loader) and the negative
   node (actual matching and
   wrong/stale/changed pointer
   observations, zero protected data
   load/target start on mismatch).
   Their hosted execution is PENDING
   the fresh exact report-head CI.
   The exact protected publisher
   (private_report_publication.py at
   blob 935f0537, SHA-256
   7a70eaa65d99b2b43c018e6d0d4381299ca1da2bd1cc21ce702e302450170df4)
   and all existing grade/stage
   witnesses are preserved byte-exact
   as receiving preimages.
4. Local gate: all 153 focused
   existing units pass (8 pin, 5
   selection, 53 eligibility, 45
   request, 42 evaluation preflight);
   the exact two native nodes are
   collected only; scoped two-file
   one-core Ruff is clean; both fresh
   physical import orders (pin-first
   and eligibility-first over all
   twelve modules) resolve to the
   proof tree; and the ordered
   transcript/transfer checker passes
   in implementation mode. The fresh
   report-head gate requires all five
   jobs and every step green, ordered
   1,440 + 1,998 units and exactly
   1,008 integrations in each
   Product; native pass claims require
   actual hosted evidence and remain
   PENDING.

## Verification

Ordered local proof in a fresh mode-
0700 /dev/shm scratch /dev/shm/
009ax-coding over a pristine tree
(git archive of implementation
0e4b0c6d42b2d0ab05cfe2fa5024924c8a4ad3a2,
physically re-verified: the pin
transfer at SHA-256
4ed3ce40d95b3bd08def08fd8b4ab6a66604ba8f87de3c2fec32a3bb6c99f736
and the witness at SHA-256
9c62bf21dfbd1237a2efc0211faeec6977ed55dcc3e8fec13b6d63d73e673d95
equal the committed donor blobs),
pre-existing checked venv (Python
3.14.4, pytest 8.4.2, ruff 0.17.4),
no dependencies installed, -o
addopts= -p no:cacheprovider,
separate private 0700 basetemps,
OPENBLAS_NUM_THREADS=1,
PYTHONDONTWRITEBYTECODE=1,
RAYON_NUM_THREADS=1, PYTHONPATH the
proof tree src, and taskset to one
core with timeout -k 5 120 prlimit
--cpu=60 --as=1073741824 for every
proof process:

1. RUN1 the 153 focused existing
   units in the two inventory runs -
   real exit 0 both; raw focus1a.log
   (99 B, SHA-256
   ed2d0e837c3cd8a0463ff6ba04b4723be88ec1a09ad0048a61fcef5843d2aa3d):
   66 passed in 1.63s (test_raw_
   snapshot_pin.py 8, test_raw_
   snapshot_selection.py 5, test_
   private_policy_pin_eligibility.py
   53) and focus1b.log (179 B,
   SHA-256
   d29b0669d8ff5c5afcc84bd232a7d82b647aed9077045b25356a3447a6eec3e8):
   87 passed in 1.73s (test_private_
   policy_request.py 45, test_private_
   evaluation_preflight.py 42).
2. RUN2 the exact hosted collect-only
   (test_evaluate_expected_raw_pin_
   composition.py) - real exit 0; raw
   collect.log (287 B, SHA-256
   7b4917d0906d8b87b4b3ec785ae6cee966274dfb36c5511006f29fa2fd27fb36):
   exactly the two additive hosted
   nodes collected without executing
   fixture assertions.
3. RUN3 the scoped two-file one-core
   Ruff over the transferred pin and
   witness - real exit 0; raw lint.log
   (19 B, SHA-256
   82b3e6a6c090a57601d22943bd23fca9218d1031dbe5a7b754092f9a156b4f18):
   All checks passed!
4. RUN4/RUN5 two fresh physical
   import-order probes, one process
   per order (pin-first
   raw_snapshot_pin then all twelve
   modules; eligibility-first
   private_policy_pin_eligibility
   then all twelve: raw_snapshot_pin,
   raw_snapshot_selection,
   raw_snapshot_directory,
   raw_snapshot_publication,
   raw_snapshot_membership,
   private_policy_pin_eligibility,
   private_policy_request,
   private_evaluation_preflight,
   source_admission, derived_store,
   evaluation_program,
   source_cohort_runner): every
   production module resolves
   physically to the canonical proof
   tree src in both orders; both real
   exit 0; raw origins logs (28 B,
   SHA-256
   03b355cd58becc5fecc597310c383c7931fd2ce50102d678ab7ae66d859c4c2d;
   42 B, SHA-256
   b452e7bd17d435d4ee2ae7905a19325a3c99f5cb47dae7f5829dcdb6963667ef):
   ORIGINS_OK raw_snapshot_pin and
   ORIGINS_OK private_policy_pin_
   eligibility.
5. RUN6 the local I/O-free
   None-sentinel probe:
   owner._acquire_expected_selected_
   data(None, None, '/tmp', None, 1,
   end=now+60) - real exit 0, raw
   none.log (36 B, SHA-256
   5540430ffb8247f778bda2f09264027417f6123f5e8ec513228b2c8989253abc):
   NONE_SENTINEL_REFUSED_PRE_
   NAMESPACE (the exact fixed content-
   free PinError, zero opens, no
   operation created, CLOSED state,
   guard released).
6. Ordered topology checker
   audit/009-ax-check/check-exact-
   transfer.py (strategic home, SHA-
   256
   ecb9b8ee34783abf49240e74c4abec30b13c283f6589b83c4d14725d00ad148d)
   in implementation mode over
   REPOSITORY STRATEGIC_HOME
   0e4b0c6d42b2d0ab05cfe2fa5024924c8a4ad3a2
   - real exit 0; raw checker-impl.log
   (890 B, SHA-256
   d5ad21a455fb3a92a360a33d89d15a9ddc13aeea8a69a272f0e7b8bb0f6381dd):
   topology base 4e7236116492812ee3cd3b19fd4acf8730e0a9a6 ->
   transcript 688e0f0ed507100974b9dd501a5a932e69e12b3e ->
   implementation 0e4b0c6d42b2d0ab05cfe2fa5024924c8a4ad3a2,
   donor 77b0a94ad2e0b87f490058ceb0db20185f6f2adc verified at its
   exact sole-parent topology and
   report scope, 35 receiving
   preimages preserved, transcript
   scope exactly oap/active (7 B
   009-ax + LF) + the order + the two
   review copies all byte-exact, and
   the transfer scope exactly the two
   donor blobs. The --report rerun
   passes after the report-only
   commit and before push.

Mock/live distinction: all fixtures,
stores, datasets and policy material
are synthetic and operator-owned.
The two hosted nodes are hosted-only
synthetic compositions over the real
selection/lock/pin/flock machinery
with the trusted synthetic loaders,
and were only collected, never
executed, locally. The 153 focused
units, collect-only, lint, origin
probes and the I/O-free probe
establish no hosted outcome, no
baseline, no native or real-model
result; no live model, credential,
data, network, GPU or hardware was
touched. No claim is made about this
report's future push/CI; the separate
post-publication receipt records the
remote facts observed after push, and
the strategic review records the
hosted outcomes at the exact report
head.

## Documentation impact

None: existing documentation and all
previous reports are preserved
byte-exact. The exact transfer, real
custody shapes, prior qualified
publisher and pending pin native
proof are recorded in this immutable
report only. All new native
publication outcomes are treated as
pending hosted proof. No documented
command, measured performance,
license clearance or readiness claim
was added.

## DHA and boundaries

Order Decision: NONE; no critical
register entry appended or read.
Preserved: the existing venv and
physical canonical source, every
product, test, fixture, doc, workflow
and order byte outside the two
transfer paths and the transcript
paths (all 35 receiving preimages
verified byte-exact at base and
implementation, including the
protected publisher
test_current_graded_report_
publication_composition.py and the
grade/stage witnesses), the prior
qualified publisher witness and its
run 44929451957 evidence, the 009-aw
report head and all prior reports,
the protected automation, the
unrelated parallel work and all
unrelated repository state; scratch
artifacts preserved in /dev/shm/
009ax-coding. No dependency setup,
credential, live data, model,
service or hardware action. No merge
performed; PR 11 remains OPEN with
auto-merge off; no 010 and no next
work chosen.

## Limitations and remaining work

Hosted proof is PENDING: the fresh
exact report-head gate (all five
jobs and every required step, both
Products at ordered 1,440 + 1,998
units in their existing order and
exactly 1,008 integrations in each
Product, the two new expected-pin
witness nodes plus the three
guarded publication nodes) has not
run at publication, and the hosted
execution of the two additive native
witnesses - including the two actual
concurrent-selection refusal proofs
and the deterministic observed expiry
after the real nested loader -
remains pending until that hosted
proof. Representative baseline
NOT_RUN; whole 009 PARTIAL; no
production or deployed activity.
Store/credential adapters, actual
named CLI, representative
data/quality baseline, runtime or
workflow edits, merge, deployment and
release remain outside this order's
scope. Nothing in this report
certifies this report's own future
push or checks; the separate post-
publication receipt and the
strategic review record those facts.
