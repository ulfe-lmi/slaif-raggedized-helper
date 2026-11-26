# OAP Coding Report — 009-an

Identifier: 009-an
Result: COMPLETE
Repository: ulfe-lmi/slaif-raggedized-helper
PR number: 11
Branch: oap/009-evaluation-baseline
Base branch: main
Implementation head SHA: 9dababa45f0a9d0716b0ab5da925fb2f62fce529
Report publication commit: SELF

## Work and scope

Exact Root FINAL order 009-an (AMEND_EXISTING_PR
on PR 11, round base 0ea0344de0dbd6c18b20073e795e53830923aeff,
main 5a7b41cc512cf883b5b2cb92d87554b4d24e685b).
Commits pushed before this report:

1. Transcript commit
   cfee2b1a3bd9edfd1d7d5a3cb7c9c7ae02aee7ff,
   sole parent 0ea0344de0dbd6c18b20073e795e53830923aeff,
   exactly four transcript objects committed
   byte-exact before any implementation
   change:
   oap/orders/009-an-current-grade-judgment-
   transfer.md (7,622 B, SHA-256
   4689f82fdfd4faf3098e888cc6616252155a4f4fcab37c3aa865f64cbb5bdf27),
   oap/active (exactly 7 B `009-an` + LF,
   SHA-256
   6d45940350e98e5d2fc8b63a6ac34213d23b1134cf2ed7816677706787e4d6da),
   oap/reviews/009-an-current-grade-judgment-
   transfer-index.json (16,629 B, SHA-256
   c8405f1a770a901c18cdce1525c952ab8f1e9a034be2b36e3e7d74070087c660)
   and oap/reviews/009-an-prior-resolution.json
   (784 B, SHA-256
   9d3c0462e56820cf38724e2749ef2b77e0a946dd9b20a25f2b25c64b9f8863ff).
2. Implementation commit
   9dababa45f0a9d0716b0ab5da925fb2f62fce529,
   sole parent cfee2b1a3bd9edfd1d7d5a3cb7c9c7ae02aee7ff,
   exactly four files: the two reviewed
   candidate blobs transferred byte-for-byte
   by blob identity without importing the
   candidate histories, orders or reports,
   src/slaif_raggedized_helper/evaluation_
   program.py (67,029 B, git blob
   58d4a98a0227ebef280a319c4aaea5425a763b64,
   SHA-256
   cbbad5e07e3ef58123b119efdb7ac74fe5da6839f6aba2e7bf12c85be621adf7)
   and
   tests/integration/test_current_grade_
   judgment_dispatch_composition.py
   (39,127 B, git blob
   0b9a069e077982b1f40de89434bcc0996f4dba03,
   SHA-256
   507c539701bf1dffc08fe428c1f0ee0c2d33d494a23e745f791a1febb72e8bc3),
   plus STATUS.md and docs/evaluation.md for
   concise scope and evidence (insertion-
   only changes).

Changed behavior: the exact guarded grade
judgment source span and its three
synthetic hosted tests, one private grade
judgment binding with current checks around
its physical source work.  The single
shared grading-owned GRADE_PIN -> GRADE_BIND
-> GRADE_PIN source block is kept as the
fixed private _grade_judgment_dispatch:
the legacy grade route preserves its two
actual full pins
(source_cohort_runner._pin_observation
against the exact prior capture) and its
actual ranking body (source_bound_ranking.
bind under the case's effective grants and
restrictions) exactly, and the one fixed
private current route replaces each of the
two actual full pins with the existing
private_policy_pin_eligibility.
revalidate_current_pin_case and the actual
ranking body with the existing
source_bound_ranking.bind_pinned, passing
the full fixed 30,000 ms operation
allowance to every genuine guarded
delegate, which starts later and clips it
to the exact original admission end.  The
exact capture, the binder output gate, the
empty-judgment behavior and the remaining
grade-case metric sequence are preserved;
no alternate binder, callback or stage
algorithm is introduced, and the shared
gate verifies the delegated result's exact
snapshot, catalog, authority, rows,
fragment count and fixed status
categories.  The fixed current route
passes the already verified pre-dispatch
retained PinData as the shared captured
argument and requires both genuine guarded
revalidations to yield exactly that
retained value, verified by identity, the
first check before the actual grade
ranking dispatch.  The new fixed private
_commence_grade_judgment_dispatch entry
accepts only the genuine current
selected-policy request
(PolicyRequestAdmission), the exact live
operator-owned pin (PinOwner), the
canonical plan wire and dataset bytes
(1..16,777,216), the exact ordered cohort
and declaration identifiers, the declared
Gold IDs, the config and the bounded
source and grade budgets and one exact
selected case ID (1..128), with no grants
or restrictions, pre-admitted Plan or
declaration, path or store, catalog,
callback, clock, deadline, provider or raw
credential.  The fixed private 30,000 ms
operation allowance is selected before any
semantic work, and the one exact
monotonic end it establishes clipped once
to the original current request lifetime
is the shared absolute extent for the
genuine ordered joint declaration
preparation, the pure case authority, the
checks and meter and the delegated pin
revalidations and rank binding.  Under one
genuine borrowed nonreentrant guard the
exact held capture is verified before any
use, the verified pre-dispatch pin data
and bounded row-map bytes are retained,
the genuine metadata association and the
joint preparation complete, the same pure
case authority verifies every ordered
admitted case's full readable held
membership and every ordered judgment
before any new protected read, and the
plan snapshot/generation concordance and
the expected effective-scope authority
through the stage _canonical_hash complete
before the span's exact prior operation
end is restored and the guard is released
unconditionally; the delegated shared
dispatch then runs under the one clipped
end, and the final short guard re-
verifies the same active operation and the
same retained PinData, the genuine held
capture and metadata association and the
detached full anchor, with the same
actual operation and PinData confirmed
again after the genuine association,
before the final same-admission
reread/cutoff, the exact prior end
restored on the retained operation under
the guard and the guard released
unconditionally, with the final deadline
check after custody restores.  The return
is at most the internal bounded verified
judgment binding with its existing source,
authorization and qualification
categories: never a grade Report or a
delivery result.  An admitted pure refusal
preserves the intended count under the
actual PREFLIGHT phase; delegated
failures preserve GRADE_PIN or GRADE_BIND;
an ordinary error uses the fixed content-
free EvaluationError; a non-Exception
interruption propagates by identity with
prior custody preserved.

## Acceptance evidence

1. Exact clean canonical state and
   PR/head/main, donor preimages and exact
   reconciled dependencies, local report-
   only parent and approved scope.  PR 11
   was OPEN, not a draft, head
   oap/009-evaluation-baseline =
   0ea0344de0dbd6c18b20073e795e53830923aeff
   (= the round base and the accepted
   009-am report-only head), base main =
   5a7b41cc512cf883b5b2cb92d87554b4d24e685b,
   MERGEABLE, no auto-merge request (live
   gh at round start).  Its exact required
   hosted run 44870819167 attempt 1 passed
   all five required jobs and steps with
   both Products at ordered 1,440 + 1,998
   units and exactly 991 integration
   passes each (log-verified: unit
   summaries 1440 passed and 1998 passed
   per Product, integration progress at
   100% totaling 991).  At round start the
   only working-tree changes were the
   activation objects (clean activation
   delta): the order bytes equal the
   strategy workorders copy (4689f82f...),
   active is exactly `009-an` + LF
   (6d459403...), and the two review JSONs
   equal the ordered digests (c8405f1a...,
   9d3c0462...).  All five exact inputs
   under the strategy root matched their
   ordered SHA-256s (c8405f1a...,
   9d3c0462..., b9ea064498dc280bfdde14434ce3c60616da0b0257e4c7fd86087ecda4a84add
   for audit/009-am-check/Root-terminal-
   review.json, 05404e2cf2d1209823f2868573b78db7789d253ecbf6b7a871bbe7b85495f4ad
   for audit/009-current-grade-judgment-
   dispatch-local-resolution.json, plus the
   order and both control JSONs above);
   the architecture digest 4b419053...
   matches ARCHITECTURE.md and the
   manifest's architecture_sha256, and the
   governance digest 24cec232... matches
   oap/governance/MANIFEST.json (the
   manifest avoids a circular hash).
   Donor topology: the implementation
   56b34d46fedcfb87ccb6e0c036c500ee69370f7f
   is the sole child of base 256d1b9b91160a5846563370ec6c2cd333d280c3,
   and the isolated report-only SELF
   8aebbb259e8b016f6057396bf033ee6ac1c2670a
   is the implementation's sole child,
   changing exactly one path,
   oap/parallel/reports/PAR-009-CURRENT-
   GRADE-JUDGMENT-DISPATCH-A.json, whose
   blob 3d65a0bb9cb496d2a10361c33f28510f6c66d083
   (7,933 B) has SHA-256
   61bfb8d62b804069af3d26c7f739323ba9f06274a3d2ec4b9a90542fedea274a
   as indexed; the donor order blob
   361f9e118617e8eb61e87dd1d02e51333c9b6fe9
   (6,086 B, 1eef8cb0...) verified in the
   donor implementation tree.  The two
   transferred objects match the index at
   blob ID, size and SHA-256 (58d4a98a/
   67,029 B/cbbad5e0... and 0b9a069e/
   39,127 B/507c5397...).  All 42 indexed
   receiving objects (blob ID, size,
   SHA-256) match the receiving head, and
   all three absent owned destinations
   (the new test file and both
   oap/parallel candidate order and report
   paths) were absent at the receiving
   head.  Frozen dependencies: 33 of the
   35 frozen donor dependencies (base
   blobs) match the current canonical
   head, and the two authorized
   reconciled changes keep the receiver
   versions: source_bound_stage_loss.py
   donor base fa59ed8948dc59e1a490ad99fb4d126be723f2bb
   (102,411 B, a4c707d1...) versus
   receiving d77e60298ac61f2ae54351b68b6e85393b29c39d
   (113,596 B, 807acca0...) and
   source_cohort_runner.py donor base
   1664f813c5af7a5fa6c3ac2020db401723a62bac
   (49,662 B, 040f6813...) versus
   receiving af41fc246d576177547206538362d1e4a75b6205
   (63,299 B, bd97dbd4...).  The used
   stage _canonical_hash, _Meter,
   _admit_authority and _preflight_
   declaration and the cohort _Meter,
   _Deadline, _declaration_admission,
   _case_checks and _run_cohort are
   byte-exact by top-level definition
   digest (AST source segment SHA-256)
   across the donor base and the receiver
   (48792d14..., 339a395b..., bbc9cae5...,
   43a4688a...; 344e6cea..., af6f59fd...,
   42b0e811..., 3f496f43..., 5d040cdd...),
   matching the digest-verified INERT
   preimage preview (618386b1...) exactly;
   the donor's remaining references into
   the reconciled modules (Budget
   a34417f8..., CohortReport 57855bbf...)
   are identical across versions, and the
   legacy _pin_observation changed only by
   the 009-am refactor (65e7185d... to
   0b0014c0...), still performing the same
   actual legacy pin and delegating its
   unchanged pointer/core/row-map
   validation tail (receiving _pin_
   capture_identity 75c496c1...).  The
   lane receipt (1c43e9f0...) and source
   index (90583927...) match their ordered
   digests.  The first transcript contains
   exactly the four exact objects; the
   implementation contains the two byte-
   exact donor blobs and both documents.
2. One shared grade-owned PIN/BIND/PIN
   source block and binder verification
   under the genuine prior bounded joint
   declaration.  The evaluation_program.py
   diff moves no legacy behavior: the
   exact declared judgment IDs and order,
   the grade meter, the phase transitions,
   the binder output gate (now parameter-
   ized on the expected effective-scope
   authority, with the legacy caller
   passing the same state.expected[4]
   value), the empty-judgment behavior and
   the remaining grade-case metric
   sequence are preserved in the fixed
   private _grade_judgment_dispatch, and
   the legacy _case entry delegates to it
   unchanged.  The current route performs
   the genuine prior bounded joint
   declaration preparation (preflight.
   _prepare_declaration_body under one
   source _Deadline clipped to the
   admission original end) before the
   dispatch, verifies the exact ordered
   selected judgment, the same
   snapshot/generation concordance, the
   readable scope and selection
   eligibility through the same pure case
   authority, and the old grade checks
   through the shared gate; the
   independently captured original PinData
   is retained through both actual
   revalidations (each verified by
   identity against the retained value,
   the first check before the genuine rank
   dispatch) and before the final
   association, and every delegate uses
   the exact original request end through
   the one clipped allowance; each owned
   guard restores its own saved op and
   unlocks unconditionally.
3. The genuine final short association is
   preserved on the same op and capture:
   the final short guard re-verifies the
   same active operation and retained
   PinData, the genuine held capture and
   metadata association and the detached
   full anchor, confirms the same actual
   operation and PinData again after the
   genuine association, performs the
   final same-admission reread/cutoff
   under the guard, restores the exact
   prior end on the retained operation and
   releases unconditionally, with the
   final deadline check after custody
   restores.  The return is only the
   internal bounded judgment binding with
   its truthful existing provenance and
   qualification categories, never a
   grade Report or delivery result; the
   PREFLIGHT progress for an admitted pure
   refusal stays distinct from the actual
   delegated GRADE_PIN/GRADE_BIND
   progress, and the fixed content-free
   EvaluationError carries no caught
   context while a non-Exception
   interruption propagates by identity
   with custody preserved.
4. Exactly three hosted nodes preserved.
   test_judgment_dispatch_stable_nonempty_
   and_empty_judgments completes the
   stable nonempty and the unaffected
   empty spans at one catalog identity
   each across two catalog loads with six
   actual directory validations (two
   independently guarded pins plus four
   actual directories in two catalogs),
   the recorded metering, the exact
   original operation end and the true
   selection counts.  test_judgment_
   dispatch_pure_refusals_zero_new_reads
   proves the pure unreadable/
   unavailable/unknown judgments refuse
   before any new full read.  test_
   judgment_dispatch_same_pin_generation_
   changes witnesses the advances of the
   genuine selection after a completed
   actual first grade pin or actual rank
   binding denying later starts while
   preserving the same raw pin and fixed
   custody.  All three are built on the
   009-al grade catalog support over the
   underlying genuine 009-ai ranking
   scenario and the inherited support and
   source cohort fixtures.
5. Fresh exact report-head CI: PENDING at
   publication.  The exact report head is
   published once to the existing PR and
   the fresh CI gate runs on it, with no
   intermediate implementation-only push
   or CI wait as ordered.  Expected at the
   report head: all five required jobs
   and every required step, both Products
   passing the ordered 1,440 + 1,998
   units and exactly 994 integrations
   (991 prior + 3 new), no missing or
   skipped evidence, with Root
   independently reviewing the exact
   report-head logs and receiving scope.
   This report cannot certify its future
   push or checks.

## Verification

Environment: pre-existing canonical
physical venv (Python 3.14.4, pytest
8.4.2, ruff 0.17.4) and physical
canonical `src` under the existing
repository checkout.  One fresh mode-0700
scratch `/dev/shm/oap-009an-proof.f5bc80`
was created directly in sticky /dev/shm
(mode 700); `TMPDIR` was set to it, with
the separate private pytest basetemp
child (mode 700) and the raw logs and
commands outside the basetemp, all
preserved.  `-o addopts= -p
no:cacheprovider`,
`OPENBLAS_NUM_THREADS=1`,
`PYTHONDONTWRITEBYTECODE=1`,
`PYTHONPATH=src` and `timeout -k 5 120
prlimit --cpu=60 --as=1073741824` for
every proof process.  No setup, install,
native local execution or unchanged
repeat under the same environment.

Exact commands (as recorded in
`/dev/shm/oap-009an-proof.f5bc80/
commands.txt`, 1,658 B, SHA-256
80cddcd55ee71eda7fd0a5bccf7c824fc729eef6e2996910a11ce0447e0d6b74;
probe `origins-probe.py` 2,904 B, SHA-256
e200df5e4282deccb0c732ca2e822df49f203138978666ce623685e3ee73adc2).

1. RUN1 one bounded inherited 168-node
   focus (`test_evaluation_program.py`
   50, `test_source_bound_ranking.py` 15,
   `test_private_policy_pin_
   eligibility.py` 53,
   `test_raw_snapshot_pin.py` 8,
   `test_private_evaluation_preflight.py`
   42): `env OPENBLAS_NUM_THREADS=1
   PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src
   TMPDIR=/dev/shm/oap-009an-proof.f5bc80
   timeout -k 5 120 prlimit --cpu=60
   --as=1073741824 .venv/bin/python -m
   pytest tests/unit/test_evaluation_
   program.py tests/unit/test_source_
   bound_ranking.py tests/unit/test_
   private_policy_pin_eligibility.py
   tests/unit/test_raw_snapshot_pin.py
   tests/unit/test_private_evaluation_
   preflight.py -q -o addopts= -p
   no:cacheprovider
   --basetemp=/dev/shm/oap-009an-proof.f5bc80/
   basetemp` — real exit 0; raw output
   `run1.log` 260 B, SHA-256
   cc7a58aed395a00b6560e41862e50f118272e2359497e24f4a856f350ff4ce18:
   `168 passed in 6.38s`.
2. RUN2 one bounded collect-only of the
   three new hosted nodes: `env
   OPENBLAS_NUM_THREADS=1
   PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src
   TMPDIR=/dev/shm/oap-009an-proof.f5bc80
   timeout -k 5 120 prlimit --cpu=60
   --as=1073741824 .venv/bin/python -m
   pytest tests/integration/test_current_
   grade_judgment_dispatch_composition.py
   --collect-only -q -o addopts= -p
   no:cacheprovider
   --basetemp=/dev/shm/oap-009an-proof.f5bc80/
   basetemp` — real exit 0; raw output
   `run2.log` 403 B, SHA-256
   72d5f7474dc8f146cffdab93544162014fad14b95c4ff2e4911e480ce55d0660:
   the three ordered node names (test_
   judgment_dispatch_stable_nonempty_and_
   empty_judgments, test_judgment_
   dispatch_pure_refusals_zero_new_reads,
   test_judgment_dispatch_same_pin_
   generation_changes) listed, then `3
   tests collected in 0.99s`.
3. RUN3 one scoped two-file one-core Ruff
   with one Rayon thread: `env
   OPENBLAS_NUM_THREADS=1
   PYTHONDONTWRITEBYTECODE=1 TMPDIR=/dev/
   shm/oap-009an-proof.f5bc80
   RAYON_NUM_THREADS=1 timeout -k 5 120
   prlimit --cpu=60 --as=1073741824
   taskset -c 0 .venv/bin/ruff check
   src/slaif_raggedized_helper/
   evaluation_program.py tests/integration/
   test_current_grade_judgment_dispatch_
   composition.py` — real exit 0; raw
   output `run3.log` 19 B, SHA-256
   82b3e6a6c090a57601d22943bd23fca9218d1031dbe5a7b754092f9a156b4f18
   (byte-identical to the prior rounds'
   Ruff digest): `All checks passed!`.
4. RUN4 one bounded physical canonical
   import-origin probe in two fresh
   processes, grade-first (RUN4a) and
   eligibility-first (RUN4b): `env
   OPENBLAS_NUM_THREADS=1
   PYTHONDONTWRITEBYTECODE=1
   PYTHONPATH=src TMPDIR=/dev/shm/oap-
   009an-proof.f5bc80 timeout -k 5 120
   prlimit --cpu=60 --as=1073741824
   .venv/bin/python /dev/shm/oap-009an-
   proof.f5bc80/origins-probe.py
   grade-first` (and `eligibility-first`)
   — both real exit 0: the two
   transferred modules and the four
   touched receiving dependencies
   (private_policy_pin_eligibility,
   source_bound_stage_loss,
   source_cohort_runner,
   source_bound_ranking,
   private_evaluation_preflight) all
   resolve physically to the canonical
   repository `src` in both import orders
   matching the strategy INERT preview
   structure; the two transferred files'
   working-tree SHA-256s are the exact
   indexed transfer digests (cbbad5e0...,
   507c5397...) checked against the
   receiving dependencies 807acca0...,
   bd97dbd4..., b0eeaa26... and 86c173cc...;
   ORIGINS_OK; raw streams `run4a.log`
   1,270 B, SHA-256
   54a6b2d0526b102482b7d604696d6aea821a0ddcefee5b99b11766d301b51bfe,
   and `run4b.log` 1,276 B, SHA-256
   2b566e4a25ee1fb9f83eb81098432d66efe1f27ecee919fa54830dacfcc1cc4e.

The implementation head was amended once
before any push, solely for the ordered
one-line documentation fact correction in
the docs/evaluation.md stable-witness
paragraph ("one catalog identity each
across two catalog loads"); the product
and test bytes are byte-identical before
and after (blob 58d4a98a/0b9a069e, SHA-
256 cbbad5e0.../507c5397...), the
transcript parent is preserved, no other
path changed, and every raw log above was
produced on exactly these product/test
bytes and remains preserved unchanged.

Mock/live distinction: all fixtures,
roots and policy material are synthetic
and operator-owned; the three hosted
nodes are hosted-only compositions over
real fixtures and the real
admission/selection/pin machinery with
the trusted synthetic delegates.
Collect-only, lint and the origin probe
prove structure and provenance only, not
hosted behavior; the 168-node focus
exercises the inherited unit behavior of
the preimage suites against the
transferred modules.  The local proof
establishes no hosted outcome; no live
model, credential, data, network, GPU or
hardware was touched.

No claim is made about this report's
future push/CI; the separate
post-publication receipt records the
remote facts observed after push, and
strategic review records the hosted
outcomes at the exact report head.

## Documentation impact

`STATUS.md`: one new nested current-state
line (`current slice 009-an`) and one new
slice paragraph recording the exact-blob
transfer with sizes and SHA-256s, the
single shared grading-owned
PIN/BIND/PIN dispatch with the legacy
route preserved and the fixed current
route's two guarded revalidations and
pinned rank binding, the fixed private
entry contract, the final short
association and cutoff semantics, the
three hosted witnesses with their
009-al/009-ai attribution, the reconciled
dependency exactness, the receiving local
proof environment, the expected hosted
gate at exactly 994 integrations, and
the open gates.  `docs/evaluation.md`:
one new section "The 009-an current grade
judgment transfer (same 009
continuation)" before the input-
contracts section, recording the blob-
identity transfer, the shared dispatch
semantics, the entry contract and guard
lifecycle, the three witnesses with
their early/final boundaries, the
legacy preservation, the local proof and
limits, and the PENDING hosted gate with
the baseline NOT_RUN truth.  No other
documentation changed; the exact
historical orders, evidence and
immutable reports are preserved; no
implemented commands, measured
performance, license clearance,
readiness or baseline measurement is
claimed.

## DHA and boundaries

Decision: NONE (no D1 candidate
reported; no ordered append; the
CRITICAL register was not loaded).
Preserved: all remaining product source,
other test code and IDs, workflow,
dependencies, runtime setup, immutable
prior reports and reviews, branches,
policy, unrelated worktrees (including
the candidate worktree, whose history,
order and report were not copied), the
strategy-side state, and the local
/dev/shm proof scratch with its raw
logs.  No live model, data, credentials,
protected runtime, hardware, license
decision, public interface, release,
deployment or merge performed or
requested; no model/profile change; no
second consumer started; no new
activation.

## Limitations and remaining work

The fresh exact report-head hosted CI is
PENDING at publication; this report
cannot certify its future push or
checks.  Until it is measured, the three
hosted outcomes and the 994-passing
integration expectation (991 prior + 3
new, both Products at ordered 1,440 +
1,998 units) are not hosted-proven at
the report head.  The candidate lane's
prior bounded local checks (168-node
inherited unit focus, three hosted
collect-only, scoped two-file one-core
Ruff and ORIGINS_OK over the frozen
prepared objects at the exact candidate
bytes) and the Root terminal review of
the accepted 009-am head are prior
evidence, not receiving proof.  No scope
deviation.  The remaining full cohort
and grade execution, final grade pin,
encoder/producer and stage wiring,
report provenance/publication, delivery,
live-data maintenance and held-out or
hardware qualification gates stay open
without exclusivity or release claims;
baseline NOT_RUN; whole 009 PARTIAL; no
merge.
