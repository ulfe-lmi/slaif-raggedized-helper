# OAP Coding Report — 009-ak

Identifier: 009-ak
Result: COMPLETE
Repository: ulfe-lmi/slaif-raggedized-helper
PR number: 11
Branch: oap/009-evaluation-baseline
Base branch: main
Implementation head SHA: ab90c05d8b24e87cdd77bd139d81e740aaeec1d0
Report publication commit: SELF

## Work and scope

Exact Root FINAL order 009-ak (AMEND_EXISTING_PR on PR 11, round
base 57f916bdc8d61390ddcea4d975d7f5f22dea24da, main
5a7b41cc512cf883b5b2cb92d87554b4d24e685b). Commits pushed before
this report:

1. Transcript commit 2a79ea1a8785ccb470c58f15f678ce5af6ab4695,
   sole parent 57f916bdc8d61390ddcea4d975d7f5f22dea24da, exactly
   four transcript objects committed byte-exact before any
   implementation change:
   oap/orders/009-ak-current-stage-catalog-transfer.md
   (7,198 B, SHA-256
   ed638f0edd9621eb97ac5dc4c6484dbfb35e0a563e95853aa092db0a955f87ba),
   oap/active (exactly 7 B `009-ak` + LF, SHA-256
   529f8535049a0f5481dfc906175dbcd7f997d085f6971d7391730c88fb26dfe4),
   oap/reviews/009-ak-current-stage-catalog-transfer-index.json
   (12,822 B, SHA-256
   0c73bac614ca8b5992520f7ac3a103678178a62fafaf45ba11bcd1860691e337)
   and oap/reviews/009-ak-prior-resolution.json (781 B, SHA-256
   2e489265c7fcd66b0b848b57d7586f273ccddc81f6b86aadc036fc5316a5cba3).
2. Implementation commit ab90c05d8b24e87cdd77bd139d81e740aaeec1d0,
   sole parent 2a79ea1a, exactly four files: the two reviewed
   candidate blobs transferred byte-for-byte by blob identity
   without importing the candidate history, order or report,
   src/slaif_raggedized_helper/source_bound_stage_loss.py
   (102,411 B, git blob fa59ed8948dc59e1a490ad99fb4d126be723f2bb,
   SHA-256
   a4c707d1ba634e13f140b4ae21929d0182904152837fba7bf99bfbf4d7ba4ba2)
   and
   tests/integration/test_current_stage_catalog_composition.py
   (27,182 B, git blob 5197ba9939b85386769cb1c1b6fa350432d2f5f7,
   SHA-256
   fd27031cc4f51f29bea8104089473fc5183a8c34d2b9d794d8d8babef73a0e8f),
   plus STATUS.md and docs/evaluation.md for concise scope and
   evidence.

Changed behavior: the existing direct stage catalog dispatch is
extracted into the single shared private body
`_stage_catalog_dispatch` (reserve/check, one real
`raw_snapshot_catalog.load_catalog` with the bounded remaining
time into the existing loader, check), used by the legacy
`_bind_stages` (call arguments, reservations, effective deadline,
later validation order, observable identities, output and
exception behavior preserved) and by the new private trusted
stage-input seam `bind_stage_catalog`, which accepts only the
genuine `PolicyRequestAdmission`, the exact active operator-owned
`PinOwner`, the canonical dataset bytes (1..16,777,216), one
exact case ID (1..128) and one cooperative 1..30,000 ms deadline,
with no caller authority, path/stores, snapshot, clock, generic
hook or provider; one actual monotonic end is captured before
any semantic work and clipped to the admission lifetime as the
same absolute end across all work, never reset or extended; the
one canonical dataset/case/selected-atom admission
(`_admit_stage_dataset`, the same exact legacy meter call order)
and the same exact stage case declaration are shared with the
supplied stage path, and the effective scope derives only from
the verified immutable full principal anchor (isolated
selected-policy snapshot, admitted principal grants, bound
grants, final detached full-anchor comparison) through the same
`_admit_authority` intersection with no added restriction; under
one real nonreentrant borrowed owner guard with the exact prior
owner end saved and restored on every exit: the real
held-capture verification and the bounded row-map bytes are
retained before any dispatch, the pure effective-scope
membership availability (an unadmitted case, no readable usable
effective scope and an unavailable effective partition) refuses
before any directory/catalog/source read, the real metadata
association runs, and one genuine live same-admission selection
observation is the last eligibility step immediately before the
actual direct catalog call; the returned object is gated to the
exact nominal catalog type and field shapes before any field is
read or sized, the real post-load metadata association and the
exact pre-dispatch held-value identity are checked, the catalog
snapshot/core/row-map ties to the same pre-dispatch held pin,
the exact nominal catalog identity holds, one more genuine
current selection observation precedes the detached full
principal anchor check and the exact cutoff, and only the
trusted intermediate catalog is returned; ordinary failures are
one fixed input-free `StageBindingError` and a non-Exception
interruption propagates by identity with custody restored. The
nested trusted catalog work keeps its own bounded validation and
may still reach pinned sources outside the effective case scope.
Non-goals preserved: no whole stage orchestration, no alternate
caller authority, no operator surfaces, no publication or
delivery; legacy stage semantics, meter order and output,
workflow and existing suites unchanged.

## Acceptance evidence

1. Exact open PR/head, clean activation delta, candidate and
   report topology, all source preimages including the two
   reconciled pin dependencies, absent isolated artifacts and
   new destinations verified; the four exact transcript bytes
   committed first. PR 11 was OPEN, head
   oap/009-evaluation-baseline =
   57f916bdc8d61390ddcea4d975d7f5f22dea24da, base main =
   5a7b41cc512cf883b5b2cb92d87554b4d24e685b, MERGEABLE/CLEAN, no
   auto-merge request, uniquely targeting that main (live
   gh and git ls-remote at round start); the exact receiving
   report head passed run 44852105955 attempt 1 on all five
   jobs and required steps with ordered A 1,440 and B 1,998
   units and 979 integrations in each Product. At round start
   the only working-tree changes were the transcript objects
   (clean activation delta): the order bytes equal the
   strategy copy, active is exactly `009-ak` + LF, and the two
   review JSONs equal the ordered digests. All four required
   exact inputs under the strategy root matched their ordered
   SHA-256s (0c73bac614…, 2e489265c7…, ac1d722dbb…,
   b39d92eaf0…); the architecture digest 4b41905396… matches
   ARCHITECTURE.md and the governance digest 24cec23235…
   matches oap/governance/MANIFEST.json. Candidate topology:
   implementation 8327eec04753100109793856a660e88994ec526f is
   the child of base 0ea63e91cf563ca1751bb373010d56ea8d884745
   and report-only SELF 49cc2d5bd7d16e33c2e0879ddeb2fbf3cc2ee549
   is its sole child, whose report blob 02f5fae602a44fbd64278f7cc6d18a9287f243ce
   (27,428 B) has SHA-256
   2afcac1f6ab29f15f46020844cea3a12ee9b851eb9c19d2085be8f72155995db
   as indexed; the candidate implementation diff is exactly the
   candidate order md plus the two transferred blobs, and the
   report commit changes only the report JSON. All 30 indexed
   preimages rechecked at the receiving head: 28 equal between
   candidate base and receiving (git blob ID, size and SHA-256
   per file), and the two changed preimages (the accepted 009-aj
   raw pin and private pin eligibility blobs) match their
   indexed candidate_base (eb4a51d9/20,581 B/7dc89e52… and
   fd9425ed/9,471 B/3b167782…) at the candidate base and their
   indexed receiving blobs (3d8a54ef/29,913 B/4dfca12d… and
   25c9a745/10,382 B/aa3b312b…) at the receiving head. The
   used guard/authority symbols were compared against the
   receiving dependency versions: all ten
   private_policy_pin_eligibility private symbols used by the
   transferred module exist with identical argument lists in
   the receiving module, PolicyRequestAdmission exposes
   principal_id and _end, PinOwner (through _Capture) exposes
   _association, op, value, derived, originals, guard, state
   and check, and raw_snapshot_catalog exposes Catalog with
   snapshot_id/core_bytes/row_map_bytes and load_catalog; the
   candidate frozen index, import preview and preimage preview
   matched their ordered digests. The owned destinations
   tests/integration/test_current_stage_catalog_composition.py
   and both oap/parallel candidate transcript paths were
   absent at the receiving head (no isolated artifacts).
   Transcript commit 2a79ea1a (sole parent 57f916b) carries
   exactly the four transcript files.
2. Both stages' shared canonical dataset/case/atom admission and
   actual direct catalog call preserved, legacy meter order and
   output unchanged. The diff of source_bound_stage_loss.py
   moves the existing dispatch (reserve, check, one real
   load_catalog with the same bounded remaining time, check)
   into `_stage_catalog_dispatch` and the legacy `_bind_stages`
   now calls it with identical arguments and keeps its
   reservations, effective deadline, later validation order and
   observable identities; the shared `_admit_stage_dataset`
   body is byte-identical to the inline legacy admission with
   the same meter call order, so the supplied path's measured
   work is unchanged. The guarded path anchors the verified
   complete principal grants and the exact effective case,
   does the pure membership availability before any real
   source work, observes the genuine selected policy after live
   association and immediately before the real catalog, uses
   one actual borrowed owner and the clipped end, checks the
   real nominal catalog and its snapshot/core/map against the
   exact pre-dispatch held pin, final selected and detached
   grants and the exact cutoff, restores the saved owner end
   and custody on all exits, and can only result in a trusted
   internal catalog; the actual nested trusted integrity can
   reach pinned sources outside the effective case scope.
3. The three hosted nodes and exact witnesses preserved.
   Collect-only lists exactly the three ordered nodes:
   test_stage_catalog_h2_identity_and_restricted_h1,
   test_stage_catalog_change_after_association_denies_before_catalog,
   test_stage_catalog_change_after_catalog_and_interruption.
   They reuse the actual 009-ai ranking-dispatch scenario
   fixture (whose Gold fixture 009-af transferred) with the
   exact measured shapes (M + 2P per full directory,
   2*M+B+2*G+4*P per complete catalog, one verified original per
   real structured-text ingestion): the stable h2 equals the
   separate real legacy catalog with one guarded catalog, two
   genuine selected observations and exact pin/custody
   retained; the pure unknown-case and unavailable h2 refusals
   start zero real catalog/directory/source work while the
   distinct narrower h1 genuinely reads the retained withheld b
   by original revision during the trusted catalog validation
   with the request selection scope kept separate; a real
   completed prior PinOwner.check in its own measured phase
   (one directory load, M+2P bundle/original ingests, M+6P
   derived loads, zero catalog work) followed by a fresh
   request establishment proves the real selected generation
   denial/latch at the actual next stage catalog start with
   zero new catalog, directory, bundle or store work and
   exactly one actual selected reread; a real full catalog
   completion followed by the genuine mismatch denies a usable
   catalog output after one genuine complete catalog and two
   live observations with association and prior custody
   preserved, and the bounded interruption subcase on the same
   node asserts the exact non-Exception marker object by
   identity through the cleanup with custody restored and no
   admission latch. Real catalog/directory starts and
   completions, delegated source reads, the exact same held raw
   pin and exact interruption/custody identity are counted and
   asserted per node.
4. Fresh exact report-head CI: PENDING at authoring. Expected
   all five jobs and every required step, each Product passing
   the ordered 1,440 + 1,998 units and exactly 982 integrations
   (979 prior + 3 new), no missing or skipped evidence. This
   report cannot certify its future push or checks.

## Verification

Environment: pre-existing canonical physical venv (Python
3.14.4, pytest 8.4.2, ruff 0.17.4) and physical canonical `src`
under the existing repository checkout. One fresh mode-0700
scratch `/dev/shm/oap-009ak-proof.SBOW8z` was created directly
in sticky /dev/shm (mode 700); `TMPDIR` was set to it, with the
separate private pytest basetemp child (mode 700) and the raw
logs and commands outside the basetemp, all preserved. `-o
addopts= -p no:cacheprovider`, `OPENBLAS_NUM_THREADS=1`,
`PYTHONDONTWRITEBYTECODE=1`, `PYTHONPATH=src` and
`timeout -k 5 120 prlimit --cpu=60 --as=1073741824` for every
proof process. No setup, install, native local execution or
unchanged repeat under the same environment.

Exact commands (as recorded in
`/dev/shm/oap-009ak-proof.SBOW8z/commands.txt`, 1,555 B,
SHA-256
8434d39e92b78581d5b83d20b2b4928aa19246b7951ab794ed5f122c0d149f45;
probe `origins-probe.py` 2,234 B, SHA-256
3aa0d76e5ddf0b3b3458e448c2b17b5fb9ec40973f84d4162c0a1ee442db3426).

1. RUN1 one bounded inherited 62-node focus
   (`test_source_bound_stage_loss.py` 51,
   `test_raw_snapshot_catalog.py` 3,
   `test_raw_snapshot_pin.py` 8): `env
   OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
   PYTHONPATH=src TMPDIR=/dev/shm/oap-009ak-proof.SBOW8z
   timeout -k 5 120 prlimit --cpu=60 --as=1073741824
   .venv/bin/python -m pytest
   tests/unit/test_source_bound_stage_loss.py
   tests/unit/test_raw_snapshot_catalog.py
   tests/unit/test_raw_snapshot_pin.py -q -o addopts= -p
   no:cacheprovider --basetemp=/dev/shm/oap-009ak-proof.SBOW8z/
   basetemp` — real exit 0; raw output `run1.log` 99 B,
   SHA-256
   f4e2061912a3660f5237717575a2cffc64086e11e0eb5bb3662b6df4d34e0d3d:
   `62 passed in 1.81s`.
2. RUN2 one bounded collect-only of the three new hosted
   nodes: `env OPENBLAS_NUM_THREADS=1
   PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src
   TMPDIR=/dev/shm/oap-009ak-proof.SBOW8z timeout -k 5 120
   prlimit --cpu=60 --as=1073741824 .venv/bin/python -m pytest
   tests/integration/test_current_stage_catalog_composition.py
   --collect-only -q -o addopts= -p no:cacheprovider
   --basetemp=/dev/shm/oap-009ak-proof.SBOW8z/basetemp` — real
   exit 0; raw output `run2.log` 383 B, SHA-256
   a021c0c9c660aa92e4ee00eb9cdc9e7f820d670e9d5f175ca1c8d60b2e0da2c2:
   the three ordered node names listed, then `3 tests collected
   in 0.89s`.
3. RUN3 one scoped two-file one-core Ruff with one Rayon
   thread: `env OPENBLAS_NUM_THREADS=1
   PYTHONDONTWRITEBYTECODE=1 TMPDIR=/dev/shm/oap-009ak-proof.
   SBOW8z RAYON_NUM_THREADS=1 timeout -k 5 120 prlimit
   --cpu=60 --as=1073741824 taskset -c 0 .venv/bin/ruff check
   src/slaif_raggedized_helper/source_bound_stage_loss.py
   tests/integration/test_current_stage_catalog_composition.py`
   — real exit 0; raw output `run3.log` 19 B, SHA-256
   82b3e6a6c090a57601d22943bd23fca9218d1031dbe5a7b754092f9a156b4f18
   (byte-identical to the prior rounds' Ruff digest): `All
   checks passed!`.
4. RUN4 one bounded physical canonical import-origin probe in
   two fresh processes, stage-first (RUN4a) and
   eligibility-first (RUN4b):
   `env OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
   PYTHONPATH=src TMPDIR=/dev/shm/oap-009ak-proof.SBOW8z
   timeout -k 5 120 prlimit --cpu=60 --as=1073741824
   .venv/bin/python /dev/shm/oap-009ak-proof.SBOW8z/
   origins-probe.py stage-first` (and `eligibility-first`) —
   both real exit 0: `slaif_raggedized_helper` and the modules
   touched by the transfer (`source_bound_stage_loss`,
   `private_policy_pin_eligibility`, `raw_snapshot_pin`,
   `raw_snapshot_catalog`, `private_policy_request`) all
   resolve physically to the canonical repository `src` in
   both import orders; the two transferred files' working-tree
   SHA-256s are the exact indexed transfer digests (a4c707d1…,
   fd27031c… checked against the two 009-aj receiving
   dependencies 4dfca12d… and aa3b312b…); ORIGINS_OK; raw
   streams `run4a.log` 1,109 B, SHA-256
   20282cb731c89cdd1828ba162713dd649565439c5c8565fb549eb357430eb9c5,
   and `run4b.log` 1,122 B, SHA-256
   3731dc5b3ea01ca267e298d598bf0747ce511f4c191ed01a8edf7dd73517f7e4.

Mock/live distinction: all fixtures, roots and policy material
are synthetic and operator-owned; the three hosted nodes are
hosted-only compositions over real fixtures and the real
admission/selection/pin machinery with the trusted synthetic
delegates. Collect-only, lint and the origin probe prove
structure and provenance only, not hosted behavior; the 62-node
focus exercises the inherited unit behavior of the unchanged
preimage suites against the transferred modules. The local
proof establishes no hosted outcome; no live model,
credential, data, network, GPU or hardware was touched.

No claim is made about this report's future push/CI; the
separate post-publication receipt records the remote facts
observed after push, and strategic review records the hosted
outcomes.

## Documentation impact

`STATUS.md`: one new nested current-state line
(`current slice 009-ak`) and one new slice paragraph recording
the exact-blob transfer with sizes and SHA-256s, the shared
dispatch body and guarded entry semantics, the trusted nested
catalog boundary, the three hosted nodes and witnesses, the
receiving local proof environment, the expected hosted gate at
exactly 982 integrations, and the open gates. The existing
009-aj prose is corrected as ordered: the reused Gold fixture
is attributed to 009-af (009-ai transferred the ranking
dispatch), and the closed, busy-owner and exhausted-deadline
subcases are described as each deliberately asserting the
ordinary content-free PolicyPinEligibilityError refusal,
separately from the single non-Exception interruption subcase
that alone asserts the exact marker instance by object
identity. `docs/evaluation.md`: the same two 009-aj prose
corrections, plus one new section "The 009-ak current stage
catalog transfer (same 009 continuation)" before the
input-contracts section, recording the blob-identity transfer,
the shared dispatch and guarded entry semantics, the bounded
private direct catalog and commencement-only scope, the
trusted integrity boundary, the actual selected observation
cuts, the three witnesses, the local proof and limits, and the
pending hosted gate. No other documentation changed; the exact
historical orders, evidence and immutable reports are
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

The fresh exact report-head hosted CI is PENDING at authoring;
this report cannot certify its future push or checks. Until it
is measured, the three hosted outcomes and the 982-passing
integration expectation (979 prior + 3 new, both Products at
ordered 1,440 + 1,998 units) are not hosted-proven. The
candidate lane's prior bounded local checks (62/62 focus,
three-node collect-only, two-file scoped Ruff, ORIGINS_OK at
the exact candidate bytes) and the Root terminal review of the
accepted 009-aj head are prior evidence, not receiving proof.
No scope deviation. The remaining whole stage orchestration,
alternate caller authority, operator surfaces, cohort, grade,
publication, delivery, source rights and baseline
qualification gates stay open without exclusivity or release
claims; baseline NOT_RUN; whole 009 PARTIAL; no merge.
