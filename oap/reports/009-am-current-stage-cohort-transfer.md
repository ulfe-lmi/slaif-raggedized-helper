# OAP Coding Report — 009-am

Identifier: 009-am
Result: COMPLETE
Repository: ulfe-lmi/slaif-raggedized-helper
PR number: 11
Branch: oap/009-evaluation-baseline
Base branch: main
Implementation head SHA: 0d007e3ec374afd310fa1dc30318f6161e698bb8
Report publication commit: SELF

## Work and scope

Exact Root FINAL order 009-am (AMEND_EXISTING_PR on PR 11, round
base 256d1b9b91160a5846563370ec6c2cd333d280c3, main
5a7b41cc512cf883b5b2cb92d87554b4d24e685b). Commits pushed before
this report:

1. Transcript commit 52c7c056a9b4ce3203f4a029d3d2cab61f8a7304,
   sole parent 256d1b9b91160a5846563370ec6c2cd333d280c3, exactly
   four transcript objects committed byte-exact before any
   implementation change:
   oap/orders/009-am-current-stage-cohort-transfer.md
   (9,321 B, SHA-256
   d6f51cdccdfa9515e8f72f2cbdb8b7f2922a2ef1dddc43087f6ca3652bab2df5),
   oap/active (exactly 7 B `009-am` + LF, SHA-256
   7c86b1da05b4895f7ace9a9ae61875e61f74c0ead59715ba1d9cd9dbb62c6e6e),
   oap/reviews/009-am-current-stage-cohort-transfer-index.json
   (22,044 B, SHA-256
   2cd5ec6e7fa6847cc2e4a596e38c15a03a22a3b671429a30726df92cc7aa7196)
   and oap/reviews/009-am-prior-resolution.json (784 B, SHA-256
   3ab5e240ea75065e79fb8934fa43cd449d7427942f710d8d360628feb55cd68e).
2. Implementation commit 0d007e3ec374afd310fa1dc30318f6161e698bb8,
   sole parent 52c7c056a9b4ce3203f4a029d3d2cab61f8a7304, exactly
   six files: the four reviewed candidate blobs transferred
   byte-for-byte by blob identity without importing the candidate
   histories, orders or reports,
   src/slaif_raggedized_helper/source_bound_stage_loss.py
   (113,596 B, git blob d77e60298ac61f2ae54351b68b6e85393b29c39d,
   SHA-256
   807acca02c4fc99e69fcb98a520b1005b049d24d3967b29b18933da7c10051be),
   src/slaif_raggedized_helper/source_cohort_runner.py
   (63,299 B, git blob af41fc246d576177547206538362d1e4a75b6205,
   SHA-256
   bd97dbd4f152cac6e3ab10129e98f1ebd1c32948eb1a6b054e6f5a2c75c4965e),
   tests/integration/test_current_stage_owned_dispatch_
   composition.py (28,499 B, git blob
   3433f0be4d76ce6102d886e97ceb4c24c0f31fd6, SHA-256
   ffa81a00eb33fff845e82538cfe109cfe23653d07aa3097f4198015c5174c41e)
   and
   tests/integration/test_current_cohort_initial_pin_
   composition.py (25,347 B, git blob
   8aa212b255db3c31005d9a775ebe392af70cdf76, SHA-256
   b944b289162cd0bbb33c731352f49b72c57be74fc4d4592ca86598c88b599862),
   plus STATUS.md and docs/evaluation.md for concise scope and
   evidence.

Changed behavior, stage: the single shared stage algorithm is
kept.  The new fixed private case-bound entry
`bind_stage_owned_dispatch` accepts only the exact admitted
current selected-policy request (PolicyRequestAdmission), the
exact live operator-owned pin owner, the bounded canonical
dataset bytes (1..16,777,216), the one exact case ID (1..128),
the existing typed supplied hybrid result, the query payload
with its exact four declared identity fields and the bounded
declared Gold bundle ID tuple; the owner alone chooses its
stores, root, capture and snapshot, and the genuine current
admitted principal and the exact case derive the
original/effective scope through the same
`_admit_authority` case-scope intersection with no restriction
and no caller grants, never a second unverified read of the
exposed nominal DTO.  The entry captures the exact start and
checks the actual admitted end before and after that bounded
pure admission work, then passes the same start to the shared
stage algorithm, which constructs the one exact real stage
clock from the accepted 30,000 ms maximum clipped to the
actual original admitted request end before any semantic work
and never reset or extended.  The fixed private current-mode
switch routes the single existing `_bind_stages` algorithm to
the fixed protected current dispatches only: the five actual
pin checks are the reviewed `revalidate_current_pin_case`
sharing the stage nominal, identity and metering checks with
the legacy pin helper; the direct catalog is the exact
reviewed `bind_stage_catalog` once; the complete declared atom
batch dispatches the genuine
`text_evaluation_gold_binding.bind_pinned` under the effective
case, keeping the complete Gold scope; and the exact eligible
chunk tuple and catalog identity dispatch
`source_bound_ranking.bind_pinned`, with the independent full
grant anchor retained.  Every other declaration, trace,
bounds, geometry, metering, identity and output check, order
and reservation is preserved from the existing stage
algorithm; there is no generic hook, provider or second
algorithm, and each delegate owns its one nonreentrant borrow,
starting after admission and clipping its 30,000 ms operation
allowance to the same recorded admission end, so one exact
common operation end spans every full directory and the exact
prior owner end is preserved on every exit of each actual
borrowed span.  The exact live PinData identity is anchored
from the first guarded reload through all phases, and the
actual final stage result cutoff assembles the actual
_Diagnosis first, then one genuine selected observation under
a suitable short exclusive acquisition of the same owner
immediately before the usable return: it captures and
validates the exact same active operation and PinData across
the association and the genuine selected observation, rechecks
the detached full principal anchor and the deadline at the
cutoff, restores the exact prior operation end and releases
the guard from an unconditional inner finally even if the
restore fails.  It returns only the private stage diagnosis
with the supplied HybridResult's existing qualification and
origin; every ordinary failure is one fixed content-free
StageBindingError, and a non-Exception interruption
propagates by identity with custody preserved.

Changed behavior, cohort: one actual initial full directory
reload and the shared legacy post-reload
pointer/core/row-map/identity work are preserved: the bounded
identity checks are extracted byte-order-exact into
`_pin_capture_identity`, runnable by both the legacy
`_pin_observation` and the new entry with the retained
pre-dispatch value passed as prior, and the legacy entry's
signature, meter order and output are unchanged.  The new
fixed private `_current_cohort_initial_pin` entry accepts only
the genuine current PolicyRequestAdmission, the exact live
PinOwner which alone selects the origin stores, root and
capture, bounded canonical dataset bytes, the exact closed
Cohort (case_ids validated as an exact tuple within the
envelope 1..256 bounds before the identifier length
comparison), the declared encoder identifier tuples, the
declared Gold ID tuple, the exact Config, the bounded source
Budget and one 1..30,000 ms deadline, with no caller grants,
restrictions, path or stores, snapshot, Plan, query payload,
provider, callback or clock.  The exact owner-selected
operation, root and stores are retained before the admission
and passed to the genuine source `_declaration_admission` over
the canonical dataset and exact selected cohort with the
verified full principal anchor and no added restriction,
under one actual source `_Deadline` started once and clipped
to the admission original end before any semantic work; the
clipped deadline is checked immediately before the authority
snapshot work and its bounded completion is validated.  Under
one genuine nonblocking borrowed owner guard, the active
owner is tied to the exact retained operation, root and
stores before any protected work and the pre-dispatch PinData
is retained; the actual canonical row binding from the
retained value and one unavailable table with the real reader
checks complete the pure query-free per-case
readable-availability admission for every ordered effective
case before any new physical work, each retained scope
admitted once as its typed canonical record and reused by the
per-case scan.  The same held value and operation are
required at the pre-load association, then the actual
metadata association and one genuine same-admission selected
reread immediately before the real fixed
`PinOwner._held_revalidation` body (one borrow and one
physical reload, no second full pin and no nested custody);
the shared identity checks with the retained value as prior
complete before the final genuine selected observation, and
the remaining pure accounting (the detached full-grants
verification against the immutable anchor) and the trailing
meter charge complete before it, after which only the exact
cutoff and the required restoration/release intervene on all
exits: the saved operation's actual prior end is restored and
the guard is released unconditionally on refusal or
interruption.  The original PREFLIGHT progress, the saved end
and the guard restoration are retained, a non-Exception
interruption propagates by identity, and an admitted initial
refusal preserves the intended count under the fixed
content-free CohortRunnerError; no required grade catalog or
case dispatch occurs in that operation, and the trusted
nested broader full-directory rebuild may still reach
retained sources outside the effective case scope while the
early pure-admission and final-cutoff boundaries stay
distinct.

## Acceptance evidence

1. Exact current PR, branch, main, preceding report and
   locally clean activation delta, both candidate topology
   chains and report bytes, all indexed receiver preimages and
   absent destinations verified; the exact transcript
   committed first, four exact objects.  PR 11 was OPEN, not
   a draft, head oap/009-evaluation-baseline =
   256d1b9b91160a5846563370ec6c2cd333d280c3, base main =
   5a7b41cc512cf883b5b2cb92d87554b4d24e685b, MERGEABLE/CLEAN,
   no auto-merge request (live gh at round start).  The
   preceding accepted 009-al report head is exactly this
   round base: the prior resolution records decision
   ACCEPT_EXACT_SCOPE_CONTINUATION_ONLY with
   accepted_report_head 256d1b9b…, implementation
   cede7ed4c3004f3bbd4aad8a970e10800510787f, and its exact
   required hosted run 44867051253 attempt 1 passed all five
   required jobs and steps with A 1,440, B 1,998 and
   integration 985 in each Product (prior resolution
   3ab5e240… and Root terminal review 48d8dda4…, both
   digest-verified at the strategy root).  At round start the
   only working-tree changes were the activation objects
   (clean activation delta): the order bytes equal the
   strategy workorders copy (d6f51cdc…), active is exactly
   `009-am` + LF (7c86b1da…), and the two review JSONs equal
   the ordered digests.  All five exact inputs under the
   strategy root matched their ordered SHA-256s (2cd5ec6e…,
   3ab5e240…, 48d8dda4…, d5ab4cfd…, 189be09b…); the
   architecture digest 4b419053… matches ARCHITECTURE.md and
   the manifest's architecture_sha256, and the governance
   digest 24cec232… matches oap/governance/MANIFEST.json
   (the manifest avoids a circular hash).  Stage topology:
   clean local preparation
   a362d1030452d6efb39493f8ca696b4d0b363bfe carries the exact
   ordered parents 57f916bdc8d61390ddcea4d975d7f5f22dea24da +
   8327eec04753100109793856a660e88994ec526f and exact tree
   a176eeebb5c51c556ddd8cf87051bf3f2b171846; the
   implementation 59d4fbdf8381d35b15c84282e365d1a8d25bd9f1 is
   its child and the report-only SELF
   cca80aacc292ab11a723dcec5ce5a0a372c7770f is the
   implementation's sole child, whose report blob
   a18e989e7e16770f6ab48aeee431012796d69b6d (30,938 B) has
   SHA-256
   805b6f499861f75d9795e45a741dd6f9b3360d269c1ab9d1cb0e32157a19aa8a
   as indexed.  Cohort topology: the implementation
   dc901ec0d6a2e5aa8bcf338e030d063fe6fe9bea is the child of
   base 57f916bdc8d61390ddcea4d975d7f5f22dea24da and the
   report-only SELF
   a463029aed1ea40bc20eb2429bafb8d09d650ccb is its sole
   child, whose report blob
   9d05d9f16aee812a0e5fdd1336eb83e4c23183a1 (12,315 B) has
   SHA-256
   8c6dcfc7565287ad28dcfdede69c3b96e788c61caa04f43698d6b80deec0bfee
   as indexed.  All 46 indexed receiving objects (blob ID,
   size, SHA-256) match the receiving head, and all six
   absent owned destinations (both oap/parallel candidate
   order and report paths and both new test files) were
   absent at the receiving head.  The two digest-verified
   local resolutions record the 33/34 prepared-object and
   27/28 frozen-object equalities, and the one authorized
   reconciled change per lane was rechecked directly: the
   stage lane's source_bound_ranking.py donor
   6a51a149/30,098 B/74c9bc48… versus receiving
   1ee0183f/30,964 B/b0eeaa26… factors the same ordered
   membership/chunk loops with the four used pinned entry,
   guard and physical body symbols (bind_pinned, _bind_pinned,
   _body, _finalize) byte-exact by top-level definition
   digest (b658db86…, 4a7bc5a3…, fb894050…, b9906a39…), and
   the cohort lane's source_bound_stage_loss.py donor
   85c7ce3c/91,797 B/caf22819… versus receiving
   fa59ed89/102,411 B/a4c707d1… receives the exact stage
   donor change with combined receiver d77e6029 (the stage
   transfer blob), the used _preflight_declaration,
   _admit_authority and _Meter byte-exact across all three
   versions (43a4688a…, bbc9cae5…, 339a395b…) and the
   legacy _run_cohort, _declaration_admission and
   _case_checks byte-exact before and after transfer.
   Transcript commit 52c7c056 (sole parent 256d1b9b) carries
   exactly the four transcript files (738 insertions, one
   deletion for the active pointer line).
2. One shared stage algorithm, actual five full protected pin
   revalidations, guarded direct stage catalog and genuine
   protected Gold and ranking under exact same private case
   and one original admission end.  The source_bound_stage_
   loss.py diff moves no legacy behavior: the fixed private
   _CurrentStageMode and bind_stage_owned_dispatch are added
   and the current-mode switch inside _bind_stages routes
   only the five pin checks to the reviewed
   revalidate_current_pin_case (sharing the legacy stage
   nominal, identity and metering checks), the one direct
   catalog to the exact reviewed bind_stage_catalog, the
   complete declared atom batch to the genuine
   text_evaluation_gold_binding.bind_pinned under the
   effective case (complete Gold scope) and the exact
   eligible chunk tuple and catalog identity to
   source_bound_ranking.bind_pinned, with the independent
   full grant anchor detached and preserved separately and
   every other declaration, trace, bounds, geometry,
   metering, identity and output check, order and
   reservation preserved.  One exact common operation end
   spans all full directories: the h2 witness observes all
   eleven full directories started under the same recorded
   admission end, each delegate borrowing once after
   admission with its 30,000 ms allowance clipped to the same
   recorded end and the exact prior owner end preserved on
   every exit of each of the eight actual borrowed spans.
   The exact live PinData identity is anchored from the
   first guarded reload through all phases, and the short
   final guard ties the exact same active operation and
   PinData across the association and the genuine selected
   observation with the cutoff, the prior-end restoration and
   the unconditional release (restored from the inner finally
   even if the restore fails); the entry returns only the
   private stage diagnosis carrying the supplied
   HybridResult's existing qualification and origin.
3. One actual cohort initial full directory reload and the
   shared legacy post-reload pointer/core/row-map/identity
   work.  The source_cohort_runner.py diff keeps the legacy
   _run_cohort, _declaration_admission and _case_checks
   byte-exact and extracts the bounded
   pointer/core/row-map identity checks byte-order-exact
   into _pin_capture_identity, runnable by both the legacy
   _pin_observation and the new entry with the retained
   pre-dispatch value passed as prior, so the legacy meter
   order and output are unchanged.  The pure genuine
   query-free declaration admission and readable-
   availability admission for every ordered effective case
   complete before any new physical work (the actual
   canonical row binding from the retained value and one
   unavailable table with the real reader checks, each
   retained scope admitted once as its typed canonical
   record and reused), and the exact stores, saved
   operation, root and retained PinData are tied with one
   genuine nonblocking borrowed owner guard before protected
   work.  The genuine selected reads occur before the real
   reload (the pre-load recheck) and as the final cut after
   the full identity and grant checks under one exact
   deadline (the one source _Deadline clipped to the
   admission original end, checked immediately before the
   authority snapshot work).  The original PREFLIGHT
   progress with the intended count under the fixed
   content-free CohortRunnerError, the saved end and the
   guard restoration, and the non-Exception identity are
   retained; one borrow and one physical reload occur with
   no second full pin and no nested custody, and no
   required grade catalog or case dispatch occurs in that
   operation.
4. All six exact hosted nodes preserved with completed
   versus attempted physical work, logical meters and
   fixture/baseline scopes distinct.  Stage (the 009-ai
   ranking fixture over the inherited support and source
   cohort fixtures): test_owned_h2_matches_legacy_stage
   reproduces the legacy diagnosis with eleven actual full
   directories (five independent pin revalidations, the one
   direct stage catalog's two load_directory trees and the
   two retained ranking catalogs' two trees each, in exact
   order), three completed catalogs, the per-phase M+2*P
   pin and 2*M+B+2*G+4*P catalog shapes, the measured
   selected reads (two per revalidation, two for the direct
   catalog, one before each Gold bundle load in both passes,
   one before each ranking catalog dispatch and selected
   bundle load in both passes, and one at the actual final
   stage result cutoff) and the exact common deadline and
   custody, with the diagnosis equal to the separately
   measured legacy bind_stages output under its own
   counters.  Its actual generation change after the
   completed catalog (test_owned_change_after_catalog_
   denies_next_pin) denies the next physical pin start
   before any directory or source load with positive prior
   physical work (one completed revalidation and one
   complete catalog), the latched admission, zero later
   guarded stages, no diagnosis, the same held pin and the
   restored guard/end.  Its actual final-cutoff change
   (test_owned_final_cutoff_denies_assembled_result) is
   armed immediately before the real read at the exact
   one-based final reader index, proves the assembled
   diagnosis refused with that same pin, exact owner end and
   guard restore, no extra full source load, and includes
   the bounded interruption subcase asserting the exact
   marker object by identity at the route's fifteenth and
   final association with the real owner custody preserved
   and no usable diagnosis.  Cohort (the 009-af Gold
   dispatch fixture, used directly):
   test_initial_cohort_h1_h4_matches_legacy_observation
   succeeds under the actual withheld b outside the h1/h4
   scopes with one full directory (delegated raw directory
   start/completion 1/1) and two genuine selected
   observations, the actual installed withdrawal for b
   (the installed selected policy retains b's document but
   withdraws b's exact revision pair, so b's partition is
   genuinely unavailable under the retained membership),
   both exact narrowed case scopes excluding b, the exact
   retained raw value, the one clipped cooperative end
   observed at the actual association and loader and equal
   to the fresh admission's end, and the trusted rebuild
   reaching the retained b revision while the separately
   measured legacy _pin_observation matches.
   test_initial_cohort_h2_denies_unavailable_scope_
   before_protected_work refuses the later broad h2 with
   readable unavailable b before any new pin, directory,
   ingestion, original or selected check with the exact
   PREFLIGHT progress (PREFLIGHT, 2, 0, 0, 0, 2), zero
   directory starts/completions, incomplete attempts zero,
   the admission not latched and the guard and prior end
   retained.  test_initial_cohort_generation_change_refuses_
   without_usable_pin witnesses the same-pin generation
   change under the same raw pointer and owner denied
   before the reload with one genuine selected denial and
   zero new directory or source reads, and after one
   completed physical reload (a separate fresh admission
   whose own initial selected read is excluded from the
   counted span) producing no usable pin, with the exact
   same pre-dispatch held value and raw pointer asserted
   across both genuine mutations, each subcase resetting
   monkeypatch before its next fresh admission and fresh
   witness, plus the bounded exact interruption witness
   with zero directory starts/completions.
5. Fresh exact report-head CI: PENDING at publication.  The
   exact report head is published once to the existing PR
   and the fresh CI gate runs on it, with no intermediate
   implementation-only push or CI wait as ordered.
   Expected at the report head: all five required jobs and
   every required step, both Products passing the ordered
   1,440 + 1,998 units and exactly 991 integrations
   (985 prior + 6 new), no missing or skipped evidence,
   with Root independently reviewing the exact report-head
   logs and receiving scope.  This report cannot certify its
   future push or checks.

## Verification

Environment: pre-existing canonical physical venv (Python
3.14.4, pytest 8.4.2, ruff 0.17.4) and physical canonical
`src` under the existing repository checkout.  One fresh
mode-0700 scratch `/dev/shm/oap-009am-proof.vcT4fN` was
created directly in sticky /dev/shm (mode 700); `TMPDIR` was
set to it, with the separate private pytest basetemp child
(mode 700) and the raw logs and commands outside the
basetemp, all preserved.  `-o addopts= -p no:cacheprovider`,
`OPENBLAS_NUM_THREADS=1`, `PYTHONDONTWRITEBYTECODE=1`,
`PYTHONPATH=src` and `timeout -k 5 120 prlimit --cpu=60
--as=1073741824` for every proof process.  No setup,
install, native local execution or unchanged repeat under
the same environment.

Exact commands (as recorded in
`/dev/shm/oap-009am-proof.vcT4fN/commands.txt`, 1,884 B,
SHA-256
2c2b1d51a8be9e5c36449a67d02b857809ad96bc6087a6523647f835d22ce3c4;
probe `origins-probe.py` 3,234 B, SHA-256
142f56cf8bbaa0002a0c52f37a0f9f9c13d3bffbf3f220c889748b586ac6af29).

1. RUN1 one bounded inherited 202-node focus
   (`test_source_bound_stage_loss.py` 51,
   `test_raw_snapshot_pin.py` 8,
   `test_source_bound_ranking.py` 15,
   `test_text_evaluation_gold_binding.py` 21,
   `test_source_cohort_runner.py` 54,
   `test_private_policy_pin_eligibility.py` 53): `env
   OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
   PYTHONPATH=src TMPDIR=/dev/shm/oap-009am-proof.vcT4fN
   timeout -k 5 120 prlimit --cpu=60 --as=1073741824
   .venv/bin/python -m pytest
   tests/unit/test_source_bound_stage_loss.py
   tests/unit/test_raw_snapshot_pin.py
   tests/unit/test_source_bound_ranking.py
   tests/unit/test_text_evaluation_gold_binding.py
   tests/unit/test_source_cohort_runner.py
   tests/unit/test_private_policy_pin_eligibility.py -q -o
   addopts= -p no:cacheprovider
   --basetemp=/dev/shm/oap-009am-proof.vcT4fN/basetemp` —
   real exit 0; raw output `run1.log` 260 B, SHA-256
   d3341a24b49eb2351caa58551f31b3860216a091b4770fe27173510c4657ce03:
   `202 passed in 4.89s`.
2. RUN2 one bounded collect-only of the six new hosted
   nodes: `env OPENBLAS_NUM_THREADS=1
   PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src
   TMPDIR=/dev/shm/oap-009am-proof.vcT4fN timeout -k 5 120
   prlimit --cpu=60 --as=1073741824 .venv/bin/python -m
   pytest
   tests/integration/test_current_stage_owned_dispatch_
   composition.py
   tests/integration/test_current_cohort_initial_pin_
   composition.py --collect-only -q -o addopts= -p
   no:cacheprovider
   --basetemp=/dev/shm/oap-009am-proof.vcT4fN/basetemp` —
   real exit 0; raw output `run2.log` 749 B, SHA-256
   0813f7f540b15b7cbb2ef6fcd70c60f48d7bd0f8011d460008cd882387ae6567:
   the six ordered node names (test_owned_h2_matches_
   legacy_stage, test_owned_change_after_catalog_denies_
   next_pin, test_owned_final_cutoff_denies_assembled_
   result, test_initial_cohort_h1_h4_matches_legacy_
   observation, test_initial_cohort_h2_denies_unavailable_
   scope_before_protected_work,
   test_initial_cohort_generation_change_refuses_without_
   usable_pin) listed, then `6 tests collected in 1.03s`.
3. RUN3 one scoped four-file one-core Ruff with one Rayon
   thread: `env OPENBLAS_NUM_THREADS=1
   PYTHONDONTWRITEBYTECODE=1 TMPDIR=/dev/shm/oap-009am-
   proof.vcT4fN RAYON_NUM_THREADS=1 timeout -k 5 120
   prlimit --cpu=60 --as=1073741824 taskset -c 0
   .venv/bin/ruff check
   src/slaif_raggedized_helper/source_bound_stage_loss.py
   src/slaif_raggedized_helper/source_cohort_runner.py
   tests/integration/test_current_stage_owned_dispatch_
   composition.py
   tests/integration/test_current_cohort_initial_pin_
   composition.py` — real exit 0; raw output `run3.log`
   19 B, SHA-256
   82b3e6a6c090a57601d22943bd23fca9218d1031dbe5a7b754092f9a156b4f18
   (byte-identical to the prior rounds' Ruff digest): `All
   checks passed!`.
4. RUN4 one bounded physical canonical import-origin probe
   in two fresh processes, stage-first (RUN4a) and cohort-
   first (RUN4b): `env OPENBLAS_NUM_THREADS=1
   PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src
   TMPDIR=/dev/shm/oap-009am-proof.vcT4fN timeout -k 5 120
   prlimit --cpu=60 --as=1073741824 .venv/bin/python
   /dev/shm/oap-009am-proof.vcT4fN/origins-probe.py
   stage-first` (and `cohort-first`) — both real exit 0:
   the two transferred modules and the four touched
   receiving dependencies (private_policy_pin_eligibility,
   raw_snapshot_pin, source_bound_ranking,
   text_evaluation_gold_binding) all resolve physically to
   the canonical repository `src` in both import orders;
   the four transferred files' working-tree SHA-256s are
   the exact indexed transfer digests (807acca0…,
   bd97dbd4…, ffa81a00…, b944b289…) checked against the
   four receiving dependencies 4dfca12d…, aa3b312b…,
   b0eeaa26… and e712c9d5…; ORIGINS_OK; raw streams
   `run4a.log` 1,834 B, SHA-256
   d9f4d2a94811e649d3f86fb3ec6364e3ecb991adb86ccb6c5e3eae984d59ecf1,
   and `run4b.log` 1,835 B, SHA-256
   f569a9e2a221557f20c3417ed116cab6152e989ac9d043876a272027990c4b9f.

Mock/live distinction: all fixtures, roots and policy
material are synthetic and operator-owned; the six hosted
nodes are hosted-only compositions over real fixtures and
the real admission/selection/pin machinery with the trusted
synthetic delegates.  Collect-only, lint and the origin
probe prove structure and provenance only, not hosted
behavior; the 202-node focus exercises the inherited unit
behavior of the preimage suites against the transferred
modules.  The local proof establishes no hosted outcome; no
live model, credential, data, network, GPU or hardware was
touched.

No claim is made about this report's future push/CI; the
separate post-publication receipt records the remote facts
observed after push, and strategic review records the
hosted outcomes at the exact report head.

## Documentation impact

`STATUS.md`: one new nested current-state line
(`current slice 009-am`) and one new slice paragraph
recording the exact-blob transfer with sizes and SHA-256s,
the single shared stage algorithm with its fixed private
current-mode switch and final guarded cutoff, the fixed
private cohort initial-pin contract with its pure pre-
work admission and one borrow/one reload, the six hosted
nodes and their witness sources, the reconciled dependency
exactness, the receiving local proof environment, the
expected hosted gate at exactly 991 integrations, and the
open gates.  `docs/evaluation.md`: one new section "The
009-am current stage cohort transfer (same 009
continuation)" before the input-contracts section,
recording the blob-identity transfer, the stage entry and
cutoff semantics, the cohort entry semantics, the six
witnesses with their early/final boundaries and trusted
nested broader I/O kept distinct, the legacy preservation,
the local proof and limits, and the PENDING hosted gate
with the baseline NOT_RUN truth.  No other documentation
changed; the exact historical orders, evidence and
immutable reports are preserved; no implemented commands,
measured performance, license clearance, readiness or
baseline measurement is claimed.

## DHA and boundaries

Decision: NONE (no D1 candidate reported; no ordered
append; the CRITICAL register was not loaded).  Preserved:
all remaining product source, other test code and IDs,
workflow, dependencies, runtime setup, immutable prior
reports and reviews, branches, policy, unrelated worktrees
(including both candidate worktrees, whose histories,
orders and reports were not copied), and the strategy-side
state.  No live model, data, credentials, protected
runtime, hardware, license decision, public interface,
release, deployment or merge performed or requested; no
model/profile change; no second consumer started.

## Limitations and remaining work

The fresh exact report-head hosted CI is PENDING at
publication; this report cannot certify its future push or
checks.  Until it is measured, the six hosted outcomes and
the 991-passing integration expectation (985 prior + 6 new,
both Products at ordered 1,440 + 1,998 units) are not
hosted-proven at the report head.  The candidate lanes'
prior bounded local checks (stage: 95/95 inherited unit
focus (stage 51, raw pin 8, ranking 15, Gold 21), three
hosted collect-only, scoped two-file one-core Ruff and
ORIGINS_OK over the 34 frozen prepared objects; cohort:
115/115 inherited unit focus (source cohort 54, raw pin 8,
current eligibility 53), three hosted collect-only, scoped
two-file one-core Ruff and bounded physical import origins,
all at the exact candidate bytes) and the Root terminal
review of the accepted 009-al head are prior evidence, not
receiving proof.  No scope deviation.  The remaining full
cohort execution, encoder/producer and grading wiring,
report provenance/publication, current delivery, source
rights and baseline qualification gates stay open without
exclusivity or release claims; baseline NOT_RUN; whole 009
PARTIAL; no merge.
