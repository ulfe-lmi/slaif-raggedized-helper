# OAP Coding Report — 009-aj

Identifier: 009-aj
Result: COMPLETE
Repository: ulfe-lmi/slaif-raggedized-helper
PR number: 11
Branch: oap/009-evaluation-baseline
Base branch: main
Implementation head SHA: 5d7baa39efae53ea5c17f2b269802147877460c1
Report publication commit: SELF

## Work and scope

Exact Root FINAL order 009-aj (AMEND_EXISTING_PR on PR 11, round
base 0ea63e91cf563ca1751bb373010d56ea8d884745, main
5a7b41cc512cf883b5b2cb92d87554b4d24e685b). Commits pushed before
this report:

1. Transcript commit a8795b65578acf539318723833b19fca7d038fd2,
   sole parent 0ea63e9, exactly four transcript objects
   committed byte-exact before any implementation change:
   oap/orders/009-aj-current-pin-revalidation-transfer.md
   (6,574 B, SHA-256
   562235da97b30cc79526dd1129fbb42d16ad7ab25da1758b9ac6223cdc937b14),
   oap/active (exactly 7 B `009-aj` + LF, SHA-256
   9297be69392f2f490153d22aaf12936d4be3d9406b6cf14e021e90324f621893),
   oap/reviews/009-aj-current-pin-revalidation-transfer-index.json
   (10,438 B, SHA-256
   1ea03961188029203505a8af89d692118123a4aa70bc0b8560a75ca562532456)
   and oap/reviews/009-aj-prior-resolution.json (786 B, SHA-256
   13cdfe383200b6e8ce60d681dd8fad0c0fd72d4172bc8376352b9d311f955397).
2. Implementation commit 5d7baa39efae53ea5c17f2b269802147877460c1,
   sole parent a8795b65, exactly five files: the three reviewed
   candidate blobs transferred byte-for-byte by blob identity
   without importing the candidate history, order or report,
   src/slaif_raggedized_helper/raw_snapshot_pin.py (10,382 B,
   git blob 25c9a745bc63a4e13747c9302b449aa5cb56e014, SHA-256
   aa3b312b6d7e18e84e8c478071e7c2199df7a0eac5bf47f3d62d632310113545),
   src/slaif_raggedized_helper/private_policy_pin_eligibility.py
   (29,913 B, git blob 3d8a54efb77de34baf143d6cccdcdc4c9f14cd96,
   SHA-256
   4dfca12dcf067aebbe8d30422f2752afc4ff5873ba1f1e2aca0bfca380fc9827)
   and
   tests/integration/test_current_pin_revalidation_composition.py
   (17,712 B, git blob dc255bcaf99da7b9a332a46593cfebf6dc247b9c,
   SHA-256
   e2a49b82991a4e53d92dbc40f17cd18261271f91bc33b6981b02b2f238f4502f),
   plus STATUS.md and docs/evaluation.md for concise scope and
   evidence.

Changed behavior: one new fixed private entry
`revalidate_current_pin_case(admission, owner, dataset_bytes,
case_id, *, deadline_ms)` in the existing
private_policy_pin_eligibility module (the pinned public `__all__`
surface unchanged) revalidates the borrowed active pin for one
exact canonical case: it accepts only the exact admitted
request, the exact borrowed active PinOwner, the bounded
canonical dataset bytes (1..16,777,216), one exact case ID
(1..128) and one cooperative 1..30,000 ms deadline, with no
caller authority, path/stores, snapshot, clock, generic hook or
provider; the bounded canonical bytes are admitted through the
genuine canonical case declaration, the verified immutable full
grants copy is bound to the selected policy's admitted principal
anchor and refused unless equal to that anchor, and the case
intersection runs through the existing bounded authority
admission with no added restriction and never a second
unverified read of the exposed nominal DTO; the genuine held
capture and the pure complete membership and scope validation
complete before any directory or source load, so an unavailable
effective scope or an unadmitted case refuses with zero new
directory or source work; only then does the guarded variant
run the extracted fixed non-reacquiring held validation body
(`PinOwner._held_revalidation`, shared byte-exact with the
legacy `PinOwner.check`, whose signature, exception behavior,
independent full reload and exact association/equality semantics
are preserved) under one borrowed owner guard and the actual
clipped cooperative end, saving and restoring the actual prior
`op.end` on all exits: the existing metadata association, the
genuine live selected-policy recheck immediately before the
real full directory reload, the original post-load association
and exact held equality, the genuine final selection
observation, the pure detached full-grants comparison and the
final exact deadline cutoff before yielding the same validated
held PinData; a non-Exception interruption propagates by
identity with prior owner custody preserved, every ordinary
failure is the fixed content-free refusal, and the trusted full
directory validation can read pinned sources outside the
effective case scope. Non-goals preserved: no stage and grade
caller wiring, no stage direct catalog, no cohort/program
authority, no report provenance, no actual publication or
delivery; legacy callers, workflow and existing suites
unchanged.

## Acceptance evidence

1. Exact open PR/head, clean activation delta, indexed
   preimages, exact candidate/report and absent destination
   verified; the four exact transcript bytes committed first.
   PR 11 is OPEN, head oap/009-evaluation-baseline =
   0ea63e91cf563ca1751bb373010d56ea8d884745, base main =
   5a7b41cc512cf883b5b2cb92d87554b4d24e685b, MERGEABLE/CLEAN,
   uniquely targeting that main; the exact receiving report
   head passed run 44847591776 attempt 1 (all five jobs, all
   required steps). At round start the only working-tree
   changes were the four transcript objects (clean activation
   delta); the order bytes equal the strategy copy, active is
   exactly `009-aj` + LF, and the two review JSONs equal the
   ordered digests. All four required exact inputs under the
   strategy root matched their ordered SHA-256s
   (1ea0396118…, 13cdfe3832…, c657e8dbec…, d6032e96b1…); the
   architecture digest 4b41905396… matches ARCHITECTURE.md and
   the governance digest 24cec23235… matches
   oap/governance/MANIFEST.json. The candidate frozen index
   (parallel/current-pin-revalidation/source-inputs.json, 15,525
   B, SHA-256
   1bcf00167e1efd843bc6c3ddf3efa41375f541824f90c73765bbbd7acd81247a)
   pins 25 source preimages, all 25 equal at the receiving head
   (git cat-file size and SHA-256 comparison, ALL_EQUAL); the
   candidate chain 63936e7c2b9e3098bf039d57b3a8359ad326c746 is
   the sole child of 78ffe7473c8ab517c339c96c038c3f0e9c041d8c
   with report-only SELF cb1373b50a097c7915f6438008f4e42d4cb55e43
   whose report blob SHA-256 is
   06ef5866da8cf1bdd098c7fc39cd001c7a82b8340f3b482d69c0e057f1c50716;
   all three candidate blobs matched their indexed git blob IDs,
   sizes and SHA-256s against both the candidate worktree
   filesystem and the candidate git objects. The owned
   destination tests/integration/
   test_current_pin_revalidation_composition.py was absent at
   the receiving head. Transcript commit a8795b65 (sole parent
   0ea63e9) carries exactly the four transcript files.
2. Real `PinOwner.check` behavior preserved; guarded revalidation
   added. The diff of raw_snapshot_pin.py extracts the fixed
   non-reacquiring held validation body `PinOwner.
   _held_revalidation` (the real `_load` full directory reload,
   post-load association and exact held equality) and the
   legacy `check` now delegates to it, keeping its signature,
   exception behavior, independent full reload and exact
   association/equality semantics; the guarded entry reuses that
   shared body, derives the selected authority from the genuine
   immutable full principal grant and that exact dataset case,
   completes the pure complete membership and scope validation
   before any directory or source load (the h2 unavailable node
   refuses at zero new work), runs under one borrowed real
   owner guard and one clipped end, checks the actual
   association, observes the genuine live selected policy
   before the real full directory reload and again after
   validated association and equality, compares the final
   detached authority and the actual deadline, preserves
   truthful interruption/cleanup and restores the prior owner
   end; the trusted full validation can read pinned sources
   outside the effective case scope.
3. Four exact hosted fixtures preserved. Collect-only lists
   exactly the four ordered nodes:
   test_case_bound_h2_matches_legacy_check, test_case_bound_
   gate_denies_unavailable_scope_before_protected_work,
   test_case_bound_first_selection_denial_before_full_directory,
   test_case_bound_final_observation_denial_after_full_reload.
   They reuse the actual 009-ai gold-dispatch fixture: the
   stable h2 matches legacy semantics with one real full
   directory and two selected observations; the unavailable
   selected h2 refuses before I/O while the narrower h1 retains
   b and the trusted integrity genuinely verifies it (the
   withheld b revision asserted among the actually verified
   original reads); a real selected-generation denial after the
   initial association prevents all new directory and source
   reads; a real selected denial after one complete reload
   returns no usable guarded pin; exact physical/revision and
   interruption identities are preserved (one exact marker
   instance asserted by identity across the closed/busy-owner,
   exhausted-deadline and non-Exception interruption subcases).
4. Fresh exact report-head CI: PENDING at authoring. Expected
   all five jobs and every required step, each Product passing
   the ordered 1,440 + 1,998 units and exactly 979 integrations
   (975 prior + 4 new), no missing or skipped evidence. This
   report cannot certify its future push or checks.

## Verification

Environment: pre-existing canonical physical venv (Python
3.14.4, pytest 8.4.2, ruff 0.17.4) and physical canonical `src`
under the existing repository checkout. The local host /tmp
remains exhausted, so, as ordered, one fresh mode-0700 scratch
`/dev/shm/oap-009aj-proof.wmgm7C` was created directly in
sticky /dev/shm (mode 700); `TMPDIR` was set to it, with the
separate private pytest basetemp child (mode 700) and the raw
logs and commands outside the basetemp, all preserved. `-o
addopts= -p no:cacheprovider`, `OPENBLAS_NUM_THREADS=1`,
`PYTHONDONTWRITEBYTECODE=1`, `PYTHONPATH=src` and
`timeout -k 5 120 prlimit --cpu=60 --as=1073741824` for every
proof process. No setup, install, native local execution or
unchanged repeat under the same environment.

Exact commands (as recorded in
`/dev/shm/oap-009aj-proof.wmgm7C/commands.txt`, 1,347 B,
SHA-256
fc84ac52b649c289e857aac02cba97e6f054e7b32d86aa944f603400464af560;
probe `origins-probe.py` 2,784 B, SHA-256
b20a7024c562ce5044b8e8bf58dc657fa004e9087a53b34e43de825d8cbdea45).
The RUN1 record preserves one inert `PYTHONDONTWRITECODE=1`
variable alongside the applied `PYTHONDONTWRITEBYTECODE=1`.

1. RUN1 one bounded inherited 106-node focus
   (`test_raw_snapshot_pin.py` 8,
   `test_private_policy_pin_eligibility.py` 53,
   `test_private_policy_request.py` 45): `env
   OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITECODE=1
   PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src
   TMPDIR=/dev/shm/oap-009aj-proof.wmgm7C timeout -k 5 120
   prlimit --cpu=60 --as=1073741824 .venv/bin/python -m pytest
   tests/unit/test_raw_snapshot_pin.py
   tests/unit/test_private_policy_pin_eligibility.py
   tests/unit/test_private_policy_request.py -q -o addopts= -p
   no:cacheprovider --basetemp=/dev/shm/oap-009aj-proof.wmgm7C/
   basetemp` — real exit 0; raw output `run1.log` 180 B,
   SHA-256
   49b43852066fbcb66d300f8e944b0b6ce867eab34e8d22efc2c7815f37e300ae:
   `106 passed in 1.69s`.
2. RUN2 one bounded collect-only of the four new hosted nodes:
   `env OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
   PYTHONPATH=src TMPDIR=/dev/shm/oap-009aj-proof.wmgm7C
   timeout -k 5 120 prlimit --cpu=60 --as=1073741824
   .venv/bin/python -m pytest
   tests/integration/test_current_pin_revalidation_composition.
   py --collect-only -q -o addopts= -p no:cacheprovider
   --basetemp=/dev/shm/oap-009aj-proof.wmgm7C/basetemp` — real
   exit 0; raw output `run2.log` 512 B, SHA-256
   16985861253f9a56800d72241e5c103ad0d674f4d9fc61359bc3383c4ff42b22:
   the four ordered node names listed, then `4 tests collected
   in 0.84s`.
3. RUN3 one scoped three-file one-core Ruff with one Rayon
   thread: `env OPENBLAS_NUM_THREADS=1
   PYTHONDONTWRITEBYTECODE=1 TMPDIR=/dev/shm/oap-009aj-proof.
   wmgm7C RAYON_NUM_THREADS=1 timeout -k 5 120 prlimit
   --cpu=60 --as=1073741824 taskset -c 0 .venv/bin/ruff check
   src/slaif_raggedized_helper/raw_snapshot_pin.py
   src/slaif_raggedized_helper/private_policy_pin_eligibility.py
   tests/integration/test_current_pin_revalidation_composition.
   py` — real exit 0; raw output `run3.log` 19 B, SHA-256
   82b3e6a6c090a57601d22943bd23fca9218d1031dbe5a7b754092f9a156b4f18
   (byte-identical to the prior rounds' Ruff digest): `All
   checks passed!`.
4. RUN4 one bounded physical product import-origin probe:
   `slaif_raggedized_helper` and the modules touched by the
   transfer (`raw_snapshot_pin`, `private_policy_pin_
   eligibility`, and the two modules the changed module newly
   uses, `source_bound_stage_loss` and `text_evaluation_
   dataset`) all resolve physically to the canonical repository
   `src`; the two changed files' working-tree SHA-256s are the
   exact indexed transfer digests (aa3b312b…, 4dfca12d…) and
   the two newly used modules match their receiving preimage
   digests (caf22819…, 923d34d2…); ORIGINS_OK, exit 0; raw
   stream `run4.log` 1,349 B, SHA-256
   710c47b0d935d7e068111f3490c02b0f26fe8b923ba4a6954a007b0d08632139.

Mock/live distinction: all fixtures, roots and policy material
are synthetic and operator-owned; the four hosted nodes are
hosted-only compositions over real fixtures and the real
admission/selection machinery with the trusted synthetic
delegates. Collect-only, lint and the origin probe prove
structure and provenance only, not hosted behavior; the 106-
node focus exercises the inherited unit behavior of the
unchanged preimage suites against the transferred modules. The
local proof establishes no hosted outcome; no live model,
credential, data, network, GPU or hardware was touched.

No claim is made about this report's future push/CI; the
separate post-publication receipt records the remote facts
observed after push, and strategic review records the hosted
outcomes.

## Documentation impact

`STATUS.md`: one new nested current-state line
(`current slice 009-aj`) and one new slice paragraph recording
the exact-blob transfer with sizes and SHA-256s, the entry and
guard semantics, the four hosted nodes and witnesses, the
receiving local proof environment, the expected hosted gate at
exactly 979 integrations, and the open gates. `docs/
evaluation.md`: one new section "The 009-aj current pin
revalidation transfer (same 009 continuation)" before the
preserved input-contracts section, recording the blob-identity
transfer, the entry and guarded held-body semantics, the actual
current selected checks versus the trusted full-directory
integrity, the four witnesses, the local proof and limits, and
the pending hosted gate. No other documentation changed; no
implemented commands, measured performance, license clearance,
readiness or baseline measurement is claimed.

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

The fresh exact report-head hosted CI is PENDING at authoring;
this report cannot certify its future push or checks. Until it
is measured, the four hosted outcomes and the 979-passing
integration expectation (975 prior + 4 new, both Products at
ordered 1,440 + 1,998 units) are not hosted-proven. The
candidate lane's prior bounded local checks (106/106 focus,
four-node collect-only, three-file scoped Ruff, ORIGIN_OK at
the exact candidate bytes) and the Root terminal review of the
accepted 009-ai head are prior evidence, not receiving proof.
No scope deviation. The remaining stage, cohort, grade,
publication, delivery, source rights and baseline
qualification gates stay open without exclusivity or release
claims; baseline NOT_RUN; whole 009 PARTIAL; no merge.
