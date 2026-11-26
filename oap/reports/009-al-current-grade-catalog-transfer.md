# OAP Coding Report — 009-al

Identifier: 009-al
Result: COMPLETE
Repository: ulfe-lmi/slaif-raggedized-helper
PR number: 11
Branch: oap/009-evaluation-baseline
Base branch: main
Implementation head SHA: cede7ed4c3004f3bbd4aad8a970e10800510787f
Report publication commit: SELF

## Work and scope

Exact Root FINAL order 009-al (AMEND_EXISTING_PR on PR 11, round
base 390ed945376b4d65a0fc8309a9e043c228f6aad2, main
5a7b41cc512cf883b5b2cb92d87554b4d24e685b). Commits pushed before
this report:

1. Transcript commit 6c55d4c0ac16635f71a75f5d4f1540f4021c2442,
   sole parent 390ed945376b4d65a0fc8309a9e043c228f6aad2, exactly
   four transcript objects committed byte-exact before any
   implementation change:
   oap/orders/009-al-current-grade-catalog-transfer.md
   (7,186 B, SHA-256
   5f66d585a3da7986d245d3d3d843202c741ea2b647b9c8d60069491c86cec0db),
   oap/active (exactly 7 B `009-al` + LF, SHA-256
   8ea5a1118807f5b58dadd542a65f31c10e3004eaba8068f73d59dad7dbba6b0c),
   oap/reviews/009-al-current-grade-catalog-transfer-index.json
   (17,259 B, SHA-256
   e301492c8bd3b597e52ff5aa5cb3ade6d8519bf361b4d3aa74c19237e4a1d1b7)
   and oap/reviews/009-al-prior-resolution.json (784 B, SHA-256
   6d421d20c35dafbfb9d7a775cffcb7c8e8970c8a34faf4421c2eeec9e10f5fe1).
2. Implementation commit cede7ed4c3004f3bbd4aad8a970e10800510787f,
   sole parent 6c55d4c0ac16635f71a75f5d4f1540f4021c2442, exactly
   six files: the four reviewed candidate blobs transferred
   byte-for-byte by blob identity without importing the candidate
   history, order or report,
   src/slaif_raggedized_helper/evaluation_program.py
   (48,022 B, git blob f217811b1f07644aac6977f48c4a0d78a2bad0bb,
   SHA-256
   831e755394975c454607253556d89cc8e37ebae35c0b948234a44a2aa408b8e4),
   src/slaif_raggedized_helper/private_evaluation_preflight.py
   (8,131 B, git blob c95fe980eb67a85a4e0b256af16768775e1ba88d,
   SHA-256
   86c173cc7ab7253161c91d44034ecc94430bef9324aa6b0a790bd58bf079754c),
   src/slaif_raggedized_helper/source_bound_ranking.py
   (30,964 B, git blob 1ee0183f06f20746695e67ab69709068f1d3c787,
   SHA-256
   b0eeaa261705e98252912e7ddd9fceef3d0ae4b4e6577494a1d89660d0967e9e)
   and
   tests/integration/test_current_grade_catalog_composition.py
   (36,997 B, git blob 779a31cb1880a172270899b8cea292e900d89674,
   SHA-256
   5854682ae755547a6548c4cc5a0e4ea46a64f57eefbeee56cfe8b8154fa05cd1),
   plus STATUS.md and docs/evaluation.md for concise scope and
   evidence.

Changed behavior: the existing grade catalog cut is extracted
into the shared private `_direct_catalog` (the held pointer bound
to the exact declared snapshot and generation, one actual direct
`raw_snapshot_catalog.load_catalog` under the remaining loader
bound, the exact nominal catalog bound to the declared snapshot
and catalog identities, returning the internal verified catalog
identity only, never rows or a report), used by the legacy
`_catalog` with its phase, source pin observation, remaining
grade-owned reservations, producer work and output preserved, and
by the new fixed private current commencement
`_commence_grade_catalog`, which accepts only the genuine current
selected-policy request (PolicyRequestAdmission), the exact live
operator-owned PinOwner, the canonical plan wire and dataset bytes
(1..16,777,216), the exact ordered cohort and declaration
identifiers, the declared Gold IDs, the config and the bounded
source and grade budgets, and one cooperative 1..30,000 ms
deadline, with no grants or restrictions, pre-admitted Plan or
declaration, path or stores, catalog, callback, clock, provider
or raw credential. The preflight body is extracted into
`_prepare_declaration_body` under one already-owned caller clock
(the legacy entry constructs its own fixed clock, delegates, and
keeps its after-assembly clock check and fixed PreparationError
semantics); the rank gate is factored into `_bound_indexes` and
`_admit_selected_chunks` with the legacy `_gate` output and meter
order preserved. Under the one genuine borrowed nonreentrant
guard, with the exact saved owner operation's prior end restored
on every exit and the guard release unconditional: the held
capture against the real manifest and immutable pin, the verified
pre-dispatch pin data and bounded row-map bytes, and the real
metadata association are verified; the shared genuine joint
declaration preparation runs; the new pure case authority then
verifies every ordered admitted case's full readable held
membership and every ordered selected judgment through the rank
gate's exact scope and linkage indexes before any catalog,
directory or bundle read (an unavailable partition inside a
readable case scope, no readable membership at all, or an
unknown, unreadable or unavailable selected entry anywhere
refuses the whole plan with zero new reads, while an empty
judgment over a fully available readable case scope authorizes
zero selected judgment reads and retains the broad trusted
catalog operation); the plan snapshot/generation concordance
holds; the genuine same-admission selected policy is the last
gate before the one actual direct owned catalog; and after it
the exact same pre-dispatch pin data and associated operation,
the same held owner and metadata association, the exact nominal
catalog and the genuine final same-admission observation are
re-verified, the detached full grant and time are rechecked, and
at most the internal verified catalog identity is returned. One
actual monotonic end is captured before any semantic work and
clipped to the original current request lifetime; it is the same
absolute end across the joint preparation, the checks and
meter, the real borrowed owner end, the genuine selected
observations and the catalog, never reset, resampled or
extended. An admitted refusal preserves the intended count
(attempted=0, completed=0, refused=0, pending=intended) under the
fixed content-free EvaluationError whose caught handler has left
before the raise; a non-Exception interruption propagates by
identity with prior custody preserved. The three new default
hosted nodes reuse the actual 009-ai ranking-dispatch scenario
fixture - the slice's immediate fixture, built on the inherited
support and source cohort fixtures - with the attributed
synthetic selected policy and fresh admissions after the
expensive setup: the stable ordered multi-case plan including
the empty judgment completing at one genuine catalog, the pure
early refusals at zero new reads including the mixed
readable-but-withheld case and the unaffected narrower empty
judgment, and the real selected generation denial on the same
raw pin both pre-catalog (exactly one actual selected reread,
latched admission) and post-catalog after one genuine complete
catalog. Non-goals preserved: whole source cohort, full grade
and stage composition, report provenance/publication, current
delivery, legacy public entry semantics, existing suites,
dependencies and CI unchanged otherwise.

## Acceptance evidence

1. Exact open PR/head, clean activation delta, candidate and
   report topology, frozen preimages, exact reconciled changes,
   absent isolated artifacts and new destinations verified; the
   four exact transcript bytes committed first. PR 11 was OPEN,
   not a draft, head oap/009-evaluation-baseline =
   390ed945376b4d65a0fc8309a9e043c228f6aad2, base main =
   5a7b41cc512cf883b5b2cb92d87554b4d24e685b, MERGEABLE/CLEAN, no
   auto-merge request, and the only open PR in the repository
   (live gh and git ls-remote at round start). The exact
   receiving report head passed run 44860721647 attempt 1 on all
   five jobs and required steps with ordered A 1,440 and B 1,998
   units and 982 integrations in each Product (ordered prior
   resolution and Root terminal review, both digest-verified). At
   round start the only working-tree changes were the transcript
   objects (clean activation delta): the order bytes equal the
   strategy copy, active is exactly `009-al` + LF, and the two
   review JSONs equal the ordered digests. All four required
   exact inputs under the strategy root matched their ordered
   SHA-256s (e301492c…, 6d421d20…, 9aac94e4…, 2f464930…); the
   architecture digest 4b41905396… matches ARCHITECTURE.md and
   the governance digest 24cec23235… matches the oap/governance/
   MANIFEST.json self-digest (the manifest avoids a circular
   hash). Candidate topology: implementation
   bf4f289733cbbd6ef3fada8de128165d4da3d94f is the child of base
   0ea63e91cf563ca1751bb373010d56ea8d884745 and report-only SELF
   4db0b7528c4b48d8b78e9cbd2a09a2c5a8b758e9 is its sole child,
   whose report blob 9680478eb1a7bff521271600bcfa3f466187ae93
   (2,472 B) has SHA-256
   0fc1c059aabedb8b31d24d8fcb0e62b58bf68dc46da9f04743a84c56a1f68850
   as indexed; the candidate implementation diff is exactly the
   candidate order md plus the four transferred blobs, and the
   report commit changes only the report JSON. All 37 frozen
   source preimages rechecked at the receiving head: 34 equal
   between candidate base and receiving (git blob ID, size and
   SHA-256 per file), and the three authorized differences (the
   two accepted 009-aj pin objects raw_snapshot_pin.py and
   private_policy_pin_eligibility.py and the accepted 009-ak
   stage module source_bound_stage_loss.py) match their indexed
   candidate-base values at the candidate base (fd9425ed/9,471
   B/3b167782…, eb4a51d9/20,581 B/7dc89e52…, 85c7ce3c/91,797
   B/caf22819…) and their indexed receiving values at the
   receiving head (25c9a745/10,382 B/aa3b312b…, 3d8a54ef/29,913
   B/4dfca12d…, fa59ed89/102,411 B/a4c707d1…); all 16 used
   guard/authority symbols in those three receiving modules
   verify by top-level definition digest (SHA-256 over the
   stripped top-level definition source) against the indexed
   unchanged_relevant_symbols values. All 44 indexed receiving
   objects (blob ID, size, SHA-256) match the receiving head. The
   candidate frozen index (26,405 B, 523936b8…; its 27 frozen
   excerpts byte-exact against the candidate base line ranges),
   the preimage preview (3,903 B, 31ac5d15…) and the import
   preview (1,143 B, b64d95e9…) match their ordered digests. The
   owned destinations
   tests/integration/test_current_grade_catalog_composition.py
   and both oap/parallel candidate transcript paths were absent
   at the receiving head (no isolated artifacts). Transcript
   commit 6c55d4c0 (sole parent 390ed945) carries exactly the
   four transcript files.
2. Grade direct catalog, legacy plan/snapshot/generation and
   catalog ID checks, real post-catalog pin and remaining
   budget floor, established dispositions and progress
   preserved. The evaluation_program.py diff moves the existing
   snapshot/generation/catalog-identity condition set and the
   one real `load_catalog` under the same bounded remaining
   time into `_direct_catalog`; the legacy `_catalog` keeps its
   CATALOG phase, the `source._pin_observation` call, the
   remaining grade-owned observation reservations and all later
   producer work, so the supplied path's measured work is
   unchanged. The preflight legacy entry keeps the fixed clock
   construction, the exact nominal config/budget snapshotting,
   the genuine wire admission, the genuine declaration
   admission, the `PreparedDeclaration` field set, the
   after-assembly clock check and the fixed
   `PreparationError` semantics; only the body moved under the
   caller-owned clock. The ranking `_gate` delegates to the
   extracted `_bound_indexes` and `_admit_selected_chunks` with
   the same meter call order and returns the same
   (effective, pinned) output, so the legacy rank's distinct
   selected set behavior (unknown, malformed, unreadable or
   unavailable selected entries refuse the whole batch while an
   unselected unavailable bundle never refuses by itself) stays
   intact and is now shared with the private guarded route. The
   private guarded route uses the shared genuine joint
   declaration preparation and the shared rank kernel; the new
   pure case authority verifies, under exact admitted principal
   scope, every selected case's full readable held membership
   and every ordered judgment before any new protected work:
   the real mixed unavailable case (readable member with a
   genuinely withheld partition) refuses, the narrow empty
   unavailable case (no usable membership) refuses, and the
   narrower usable empty judgment retains the actual trusted
   catalog. The real post-catalog pin re-verification (same
   held value, same associated operation, held capture,
   association, exact nominal catalog, genuine final
   observation, detached full-grant recheck, exact
   `_still_within(end)` cutoff) is the remaining budget floor,
   and admitted progress is the established
   `FailurePrefix("CATALOG", intended, 0, 0, 0, intended)`
   under the fixed content-free EvaluationError with
   non-Exception interruption by identity and unconditional
   guard release.
3. One actual monotonic clock, exact witnesses and separated
   counts. `started = time.monotonic()`;
   `end = min(started + deadline_ms/1000, admission._end)`; the
   one real `source._Deadline(started, deadline_ms)` is clipped
   in place to that end and is the same absolute end across the
   joint preparation (passed as the caller clock), the checks
   and meter, the real borrowed owner end (the saved prior end
   restored on every exit), the genuine selected observations
   (the pre-catalog last gate and the post-catalog final
   observation) and the direct catalog as the overall cutoff,
   never reset, resampled or extended. The three exact hosted
   witnesses: (a) stable ordered cases including empty - the
   multi-case plan with the empty judgment completes at one
   genuine catalog (two real directory validations, two genuine
   selected observations, zero new pin reload, no producer,
   scoring or report work) with the shared exact clock observed
   across preparation, dispatch and both metadata associations
   (all equal to the fresh admission's end, and the actual
   saved owner operation end under the guard equal to it), the
   empty judgment authorizing zero selected judgment reads
   while the broad trusted catalog reaches every retained
   bundle; (b) genuine available/unavailable membership and
   selected refusals - the unknown well-formed chunk, the real
   unreadable selected scope, the genuinely unavailable
   selected partition, the mixed readable-but-withheld case
   (empty judgment, another readable membership remaining), and
   the no-usable-membership scope each refuse with zero new
   catalog/directory/bundle reads, while the unaffected
   narrower empty judgment completes the catalog; (c) genuine
   pre/post-catalog generation denial on the same raw pin -
   after a real completed prior PinOwner.check measured in its
   own phase, the selected generation is advanced on the same
   raw pin and pointer with the identical wire payload: the
   pre-catalog denial at the last gate (zero new catalog
   starts, exactly one actual selected reread, latched
   admission whose recheck refuses further reads) and the
   post-catalog denial after one genuine complete catalog with
   two real directory validations, the raw pin bytes retained
   identically across both mutations. Actual started/completed
   catalog/directory and delegated read counts are asserted
   separately from the earlier source pin (measured in its own
   phase, then zeroed) and from the claimed per-case progress
   (the FailurePrefix fields).
4. Fresh exact report-head CI: PENDING at publication. At the
   exact implementation head, run 44864462735 (cede7ed4)
   completed with all five jobs and every required step
   success (two Products at 24 steps, three OAP jobs at 10
   steps each), with the ordered unit tallies A 1,440 and
   B 1,998 passed in each Product's unit phases and the
   integration suite reaching 100% with no failed or skipped
   evidence (job success). Expected at the report head: all
   five jobs and every required step, each Product passing the
   ordered 1,440 + 1,998 units and exactly 985 integrations
   (982 prior + 3 new), no missing or skipped evidence, with
   Root independently reviewing the exact report-head logs and
   receiving scope. This report cannot certify its future push
   or checks.

## Verification

Environment: pre-existing canonical physical venv (Python
3.14.4, pytest 8.4.2, ruff 0.17.4) and physical canonical `src`
under the existing repository checkout. One fresh mode-0700
scratch `/dev/shm/oap-009al-proof.sqqIcj` was created directly
in sticky /dev/shm (mode 700); `TMPDIR` was set to it, with the
separate private pytest basetemp child (mode 700) and the raw
logs and commands outside the basetemp, all preserved. `-o
addopts= -p no:cacheprovider`, `OPENBLAS_NUM_THREADS=1`,
`PYTHONDONTWRITEBYTECODE=1`, `PYTHONPATH=src` and
`timeout -k 5 120 prlimit --cpu=60 --as=1073741824` for every
proof process. No setup, install, native local execution or
unchanged repeat under the same environment.

Exact commands (as recorded in
`/dev/shm/oap-009al-proof.sqqIcj/commands.txt`, 237 B,
SHA-256
f9d3796db5db9c827e8a95fc642f86c4ebc96936638d814a7c6b3a56465ed5c1;
probe `origins-probe.py` 2,791 B, SHA-256
f14d8eb04db7d529c78159b74cb2fe439daf183bb487bec66c266d0e851f69ff).

1. RUN1 one bounded inherited 107-node focus
   (`test_evaluation_program.py` 50,
   `test_source_bound_ranking.py` 15,
   `test_private_evaluation_preflight.py` 42): `env
   OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
   PYTHONPATH=src TMPDIR=/dev/shm/oap-009al-proof.sqqIcj
   timeout -k 5 120 prlimit --cpu=60 --as=1073741824
   .venv/bin/python -m pytest
   tests/unit/test_evaluation_program.py
   tests/unit/test_source_bound_ranking.py
   tests/unit/test_private_evaluation_preflight.py -q -o
   addopts= -p no:cacheprovider
   --basetemp=/dev/shm/oap-009al-proof.sqqIcj/basetemp` — real
   exit 0; raw output `run1.log` 180 B, SHA-256
   0f7839782413198e5ae6f1cf9df9abe816754c05f0da316141b75e9f223eea81:
   `107 passed in 5.53s`.
2. RUN2 one bounded collect-only of the three new hosted
   nodes: `env OPENBLAS_NUM_THREADS=1
   PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src
   TMPDIR=/dev/shm/oap-009al-proof.sqqIcj timeout -k 5 120
   prlimit --cpu=60 --as=1073741824 .venv/bin/python -m pytest
   tests/integration/test_current_grade_catalog_composition.py
   --collect-only -q -o addopts= -p no:cacheprovider
   --basetemp=/dev/shm/oap-009al-proof.sqqIcj/basetemp` — real
   exit 0; raw output `run2.log` 373 B, SHA-256
   c2707a4382cc4dd164d29434d9973622f85dd3f8fd38fee1815f61e590676d04:
   the three ordered node names
   (test_grade_catalog_stable_plan_empty_judgment_completes,
   test_early_pure_refusals_zero_new_reads,
   test_selection_change_denies_catalog_and_post_catalog_
   observation) listed, then `3 tests collected in 0.91s`.
3. RUN3 one scoped four-file one-core Ruff with one Rayon
   thread: `env OPENBLAS_NUM_THREADS=1
   PYTHONDONTWRITEBYTECODE=1 TMPDIR=/dev/shm/oap-009al-proof.
   sqqIcj RAYON_NUM_THREADS=1 timeout -k 5 120 prlimit
   --cpu=60 --as=1073741824 taskset -c 0 .venv/bin/ruff check
   src/slaif_raggedized_helper/evaluation_program.py
   src/slaif_raggedized_helper/private_evaluation_preflight.py
   src/slaif_raggedized_helper/source_bound_ranking.py
   tests/integration/test_current_grade_catalog_composition.py`
   — real exit 0; raw output `run3.log` 19 B, SHA-256
   82b3e6a6c090a57601d22943bd23fca9218d1031dbe5a7b754092f9a156b4f18
   (byte-identical to the prior rounds' Ruff digest): `All
   checks passed!`.
4. RUN4 one bounded physical canonical import-origin probe in
   two fresh processes, grade-first (RUN4a) and
   eligibility-first (RUN4b): `env OPENBLAS_NUM_THREADS=1
   PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src
   TMPDIR=/dev/shm/oap-009al-proof.sqqIcj timeout -k 5 120
   prlimit --cpu=60 --as=1073741824 .venv/bin/python
   /dev/shm/oap-009al-proof.sqqIcj/origins-probe.py grade-first`
   (and `eligibility-first`) — both real exit 0: the
   transferred modules (`evaluation_program`,
   `private_evaluation_preflight`, `source_bound_ranking`) and
   the touched receiving dependencies (`source_bound_stage_
   loss`, `private_policy_pin_eligibility`) all resolve
   physically to the canonical repository `src` in both import
   orders; the four transferred files' working-tree SHA-256s
   are the exact indexed transfer digests (831e7553…,
   86c173cc…, b0eeaa26…, 5854682a…) checked against the three
   receiving dependencies a4c707d1…, 4dfca12d… and aa3b312b…;
   ORIGINS_OK; raw streams `run4a.log` 1,552 B, SHA-256
   b323901638fbdaed576fbc8ea5458d980e3435ca65b548a09e127bf5fdd134aa,
   and `run4b.log` 1,570 B, SHA-256
   6b58862c1df8d0a9647009d22d858acd1f6c98a34cc8e052d44896c66ac64366.

Mock/live distinction: all fixtures, roots and policy material
are synthetic and operator-owned; the three hosted nodes are
hosted-only compositions over real fixtures and the real
admission/selection/pin machinery with the trusted synthetic
delegates. Collect-only, lint and the origin probe prove
structure and provenance only, not hosted behavior; the
107-node focus exercises the inherited unit behavior of the
preimage suites against the transferred modules. The local
proof establishes no hosted outcome; no live model,
credential, data, network, GPU or hardware was touched. The
observed implementation-head CI facts are hosted runner
evidence for that head only.

No claim is made about this report's future push/CI; the
separate post-publication receipt records the remote facts
observed after push, and strategic review records the hosted
outcomes at the exact report head.

## Documentation impact

`STATUS.md`: one new nested current-state line
(`current slice 009-al`) and one new slice paragraph recording
the exact-blob transfer with sizes and SHA-256s, the shared
direct cut and guarded commencement semantics, the pure case
authority with its refusal/retention distinctions, the one
clipped exact clock, the three hosted nodes and witnesses, the
receiving local proof environment, the expected hosted gate at
exactly 985 integrations, and the open gates. The existing
009-ak prose is corrected as ordered: its hosted nodes'
immediate fixture is the 009-ai ranking scenario built on the
inherited support and source cohort fixtures, and that
scenario's Gold fixture is the 009-af transfer (the 009-af Gold
attribution in the 009-ai/009-aj prose and all immutable
historical evidence remain untouched). `docs/evaluation.md`:
the same 009-ak prose correction, plus one new section "The
009-al current grade catalog transfer (same 009 continuation)"
before the input-contracts section, recording the blob-identity
transfer, the shared direct cut, the preflight/rank factoring,
the fixed private commencement contract, the pure case
authority, the one clipped clock, the three witnesses, the
local proof and limits, and the PENDING hosted gate with the
baseline NOT_RUN truth. No other documentation changed; the
exact historical orders, evidence and immutable reports are
preserved; no implemented commands, measured performance,
license clearance, readiness or baseline measurement is
claimed.

## DHA and boundaries

Decision: NONE (no D1 candidate reported; no ordered append;
the CRITICAL register was not loaded). Preserved: all
remaining product source, other test code and IDs, workflow,
dependencies, runtime setup, immutable prior reports and
reviews, branches, policy, unrelated worktrees (including the
candidate worktree, whose history, order and report were not
copied), and the strategy-side state. No live model, data,
credentials, protected runtime, hardware, license decision,
public interface, release, deployment or merge performed or
requested; no model/profile change; no second consumer
started.

## Limitations and remaining work

The fresh exact report-head hosted CI is PENDING at
publication; this report cannot certify its future push or
checks. Until it is measured, the three hosted outcomes and
the 985-passing integration expectation (982 prior + 3 new,
both Products at ordered 1,440 + 1,998 units) are not
hosted-proven at the report head. The candidate lane's prior
bounded local checks (107/107 focus, three-node collect-only,
four-file scoped Ruff, ORIGINS_OK at the exact candidate
bytes) and the Root terminal review of the accepted 009-ak
head are prior evidence, not receiving proof. No scope
deviation. The remaining whole source cohort, full grade and
stage composition, report provenance/publication, current
delivery, source rights and baseline qualification gates stay
open without exclusivity or release claims; baseline
NOT_RUN; whole 009 PARTIAL; no merge.
