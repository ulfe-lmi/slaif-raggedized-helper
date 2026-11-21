# OAP Coding Report — 009-ai

Identifier: 009-ai
Result: COMPLETE
Repository: ulfe-lmi/slaif-raggedized-helper
PR number: 11
Branch: oap/009-evaluation-baseline
Base branch: main
Implementation head SHA: e36638cf239822d97ec95b13331eaa2884fbfe20
Report publication commit: SELF

## Work and scope

Order `oap/orders/009-ai-current-ranking-dispatch-transfer.md`
(FINAL; AMEND_EXISTING_PR 11; Decision: NONE; order file 6,951 B,
SHA-256 `d03c7f36718545eeb56814ce40e9d8c26a9be30deba70c26247dce3702c1b7af`,
byte-identical to the strategic workorders copy) at round base
`78ffe7473c8ab517c339c96c038c3f0e9c041d8c` (the accepted 009-ah
report-only head). At round start the unique open non-draft PR 11
targets main `5a7b41cc512cf883b5b2cb92d87554b4d24e685b` (exact
against the remote) with head ref
`oap/009-evaluation-baseline` at exactly `78ffe747...` and no auto
merge; the exact required hosted run 44840111535 attempt 1 at that
head passed all five jobs and every step, with ordered 1,440 + 1,998
units and 970 integrations in each Product.

Objective: receive the exact reviewed private case-bound ranking
dispatch and its five hosted controlled-source witnesses, guarding
both actual catalog starts and each directly selected load across
the two ranking passes, preserving legacy interfaces and results,
one held owner and one clipped absolute request end. Byte-exact
transfer of the two indexed candidate objects only; the candidate
commit history, its order and its report are not copied into the
receiving branch. Bounded synthetic software evidence; whole 009
remains PARTIAL. Baseline NOT_RUN.

History published in this round (one normal push to the same PR
branch, no force push, no merge, one PR):

1. `b09a816fe6bfe15793dcb9fbfc6fbed40cf6aeb3` (parent: round base
   `78ffe747`; tree `ca81ac898df75bdb56d7d254deb1f0c9c62fa1ff`) —
   exact Root transcript, four paths: `oap/active` (`009-ai` + LF,
   7 B, SHA-256
   `871a29435059cc7a61a4f01e56a8cc8af2e30fdbdc130b1fc4f75958dd433d3a`),
   `oap/orders/009-ai-current-ranking-dispatch-transfer.md` (6,951 B,
   SHA-256
   `d03c7f36718545eeb56814ce40e9d8c26a9be30deba70c26247dce3702c1b7af`)
   and the two indexed JSON control files copied byte-exact by
   basename: `oap/reviews/009-ai-current-ranking-dispatch-transfer-index.json`
   (14,769 B, SHA-256
   `9677c4fd57ccaaaa1d87095fde474505d9db31cb9a84bdbf7e23a4a88df33980`)
   and `oap/reviews/009-ai-prior-resolution.json` (814 B, SHA-256
   `dd6dbe3248e70742c50da274023af350ac4880976ed5564d9bbe7b471d294d50`),
   each re-verified at its ordered SHA-256 after copy.
2. `e36638cf239822d97ec95b13331eaa2884fbfe20` (parent: 1; tree
   `cd2f021dddc5da2bcff86dd7155b1bf2db1dbdcf`) — implementation,
   exactly the four ordered paths:
   `src/slaif_raggedized_helper/source_bound_ranking.py` (30,098 B,
   SHA-256
   `74c9bc48016ade6aa1527f5f1b10cff58f67c65fa33cb4e58d22478f71a99d41`,
   blob `6a51a14939ec84dd93ca26feb4aae9e57c65530e`, replacing the
   receiving preimage blob `7e3205b0`) and
   `tests/integration/test_current_ranking_dispatch_composition.py`
   (33,958 B, SHA-256
   `8764690ca30fde5cee48fe0155f99292e7ebb1831a252ddf829df9dd227ef059`,
   blob `ac11300bde8f3a5c06f58bf8499f9740a7ab7460`, new path),
   transferred byte-exact from candidate `0f7826e8` by blob
   identity, plus `STATUS.md` (blob `b9dd72cf`) and
   `docs/evaluation.md` (blob `e1cc8154`) with the concise scope
   and evidence notes. Everything else — the remaining product
   source, all other test code and IDs, the workflow, dependencies,
   runtime setup, the immutable reports, branches and policy — stays
   byte-exact.

## Implementation

The transferred `source_bound_ranking.py` adds one fixed private
entry `bind_pinned(admission, owner, dataset_bytes, case_id,
expected_catalog_id, chunk_ids, *, deadline_ms=30000)` over the
single inherited ranking body. It accepts only the exact
`PolicyRequestAdmission` and the exact active `PinOwner`, bounded
canonical dataset bytes, the exact case ID, the bounded expected
catalog ID, the ordered unique requested chunk IDs and one
cooperative 1..30,000 ms deadline; the caller supplies no scope
token, grants, path, snapshot, supplied Catalog, provider, callback
or clock. Stores and snapshot are derived from the actual owner
only, and the effective case scope is derived from the exact
admitted principal intersected with the genuine case declaration,
while the full principal anchor is carried separately for the final
pure detached-grants comparison. One real nonreentrant owner guard
is held across the pure pre-dispatch gate, the shared body and the
pin tie; one end is clipped to the request lifetime and the owner
operation's exact prior end is restored on every exit. Before any
new catalog or bundle load, the complete ordered selected batch is
bound through the actual pure row and membership binds against the
exact held core, row map and membership sealed to their real
manifests, verifying the selected ordinal, scope, exact revision,
extraction, bundle and metadata linkage; unknown, malformed,
unreadable or unavailable selected entries refuse the full batch at
zero new source I/O, while an unselected unavailable bundle never
refuses by itself. One genuine selected observation precedes each
retained actual catalog dispatch and each actual selected bundle
load in both observation passes under the one clipped absolute end,
with the remaining time checked after every genuine reread and
after the nested dispatches, so all protected starts stop upon
denial; the observed bundle revision, extraction, metadata and
admitted scope are compared to the exact held pin in both passes.
The legacy `bind` signature and result, the public interface,
legacy identities and the exact first non-Exception interruption
identity are preserved; every ordinary failure is one fixed
content-free `SourceBindingError`. The nested catalog integrity
still reaches unrequested pinned sources; this cut is no per-original
current-policy authorization or delivery attestation.

The five new default hosted nodes
(`tests/integration/test_current_ranking_dispatch_composition.py`):
`test_pinned_positive_h2_matches_legacy` (stable h2 legacy equality),
`test_unavailable_b_retained_and_ac_dispatch` (retained unavailable
unrequested b with selected a/c),
`test_precheck_refusals_zero_source_io` (zero new source I/O for bad
selected cases),
`test_change_after_last_pass_one_load_denies_catalog_two` (real
change after the last pass-one direct load denying catalog two) and
`test_change_after_first_catalog_and_observational_bounds` (real
change after catalog one denying its first direct load with the
bounded subcases). They run over genuine
`make_owned_support` + `dataset_and_bundles`, the actual raw
selected snapshot, real `PinOwner.acquire_selected_data`, genuine
policy wire and the attributed test-local atomic selector fixture,
attributing true physical original reads per catalog at
`2*M+B+2*G+4*P` ingestion loads using the actual fixture, with each
directory including membership and both dense/lexical group trees.
No inflated proof of per-original current policy is made.

## Acceptance evidence

1. Reconciled before implementation: exact current PR head
   `78ffe7473c8ab517c339c96c038c3f0e9c041d8c` against the remote
   (`git ls-remote`) and the live PR (open, non-draft, base `main`
   `5a7b41cc...`, head ref exact, auto-merge null, PR 11 the unique
   open PR for the objective); worktree clean except the ordered
   transcript state (the `oap/active` swap and the new order file);
   all four required strategic inputs at their ordered SHA-256s
   (`9677c4fd...`, `dd6dbe32...`, `a72bef58...`, `554e7dda...`);
   all 51 indexed receiver objects verified byte-exact at the round
   base by blob OID, mode, bytes and SHA-256 against the index
   (subsuming the 44 indexed candidate receiving preimages,
   `indexed_candidate_preimages_equal: 44`); candidate topology
   verified in the local object store — `0f7826e8`'s sole parent is
   `36f61c21` and the report-only `b69da8f8`'s sole parent is
   `0f7826e8`, with the candidate report bytes at SHA-256
   `fb238a67e15c12c0e1c440fe371d1430441da7b301c7bbc00731ea23b3c5426b`
   (blob `d1cb76e2`, 21,494 B); the other children of `36f61c21` in
   the local store (the prior 009-ag receiving transcript
   `22132988`, an ancestor of the round base, and the superseded PAR
   lane fix-round checkpoints `19526c86`/`adff0625`) were inspected
   and are not part of this transfer; the new integration
   destination was absent at the base; `oap/active` exactly
   `009-ai` + LF and the order file byte-identical to the strategic
   workorders copy. The four exact transcript bytes were committed
   first (commit 1) before any implementation.
2. The two transferred objects are byte-exact at their indexed blob
   OIDs, byte counts and SHA-256s (see Work and scope), with exactly
   the two allowed document changes (`STATUS.md`,
   `docs/evaluation.md`); the implementation commit changes exactly
   the four ordered paths and no candidate order, report, branch or
   commit was copied into the receiving branch.
3. Behavior per the ordered acceptance: the one fixed private
   `bind_pinned` case entry under a real admitted request and actual
   live owner; pure exact row/membership validation gating the
   complete selected list before any new source I/O with refusal of
   unreadable/unavailable/unknown selected IDs; full principal
   anchor separated from effective case grants; one true clipped end
   through inputs, both catalog/load passes and the final check,
   with the owner end restored; the exact post-load nominal Scope
   tie, revision/extraction/metadata comparison, the final pure
   detached-grants comparison, legacy identities and interruption
   custody preserved; nested catalog integrity still reaches
   unrequested pinned sources. This is no per-original
   authorization or delivery attestation.
4. The five exact hosted nodes are preserved: collect-only lists
   exactly the five ordered node names (RUN2 below); their behavior
   witnesses (stable h2 legacy equality, retained unavailable
   unrequested b with selected a/c, zero new source I/O for bad
   selected cases, real change after the last pass-one direct load
   denying catalog two, real change after catalog one denying its
   first direct load with the bounded subcases) and the
   `2*M+B+2*G+4*P` per-catalog ingestion-load attribution over the
   actual fixture execute only in hosted CI (hosted-only native
   fixtures; no local native execution was performed or possible).
5. Fresh exact report-head hosted proof is required and PENDING at
   authoring: all five jobs and all required steps, each Product at
   ordered 1,440 + 1,998 unit passes and exactly 975 separate
   integration passes (970 + five), no missing, skipped or
   unchanged re-run evidence counted as success.

## Verification

Environment: pre-existing canonical physical venv (Python 3.14.4,
pytest 8.4.2, ruff 0.17.4) and physical canonical `src` under the
existing repository checkout. The local host `/tmp` (tmpfs) had
exhausted its inode limit at round start (`df -i /tmp`: 1,048,576 /
1,048,576 used, 0 free), so, as ordered, one fresh mode-0700 scratch
`/dev/shm/oap-009ai-proof.qR7FNE` was created directly in sticky
`/dev/shm`; `TMPDIR` was set to it, with the separate private pytest
basetemp child and the raw logs and commands outside the basetemp,
all preserved. `-o addopts= -p no:cacheprovider`,
`OPENBLAS_NUM_THREADS=1`, `PYTHONDONTWRITEBYTECODE=1`,
`PYTHONPATH=src`, and `timeout -k 5 120 prlimit --cpu=60
--as=1073741824` for every proof process. No setup, install, native
local execution or unchanged repeat under the same environment.

Exact commands (as recorded in
`/dev/shm/oap-009ai-proof.qR7FNE/commands.txt`, 1,374 B, SHA-256
`ba85e2d3e7124625ece6f36339e49f55b1bdd351ccec4cebe61b8586b8d4732b`;
probe `origins-probe.py` 1,991 B, SHA-256
`5e6b4bde8b373f83a738e362b90184e25d606fb9bf34ea8a5663581a0cd36a05`):

1. RUN1 one bounded inherited 121-node focus
   (`test_source_bound_ranking.py` 15,
   `test_private_policy_pin_eligibility.py` 53,
   `test_private_policy_request.py` 45, `test_raw_snapshot_pin.py`
   8): `env OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
   PYTHONPATH=src TMPDIR=$SCRATCH timeout -k 5 120 prlimit --cpu=60
   --as=1073741824 .venv/bin/python -m pytest
   tests/unit/test_source_bound_ranking.py
   tests/unit/test_private_policy_pin_eligibility.py
   tests/unit/test_private_policy_request.py
   tests/unit/test_raw_snapshot_pin.py -q -o addopts= -p
   no:cacheprovider --basetemp=$SCRATCH/basetemp` — real exit 0; raw
   output `run1.log` 180 B, SHA-256
   `6135aad815f5dcb45dcc8b125b4ff44b9e975071eca291d5b440254c76ac83c2`:
   `121 passed in 1.77s`.
2. RUN2 one bounded collect-only of the five new hosted nodes:
   `env ... .venv/bin/python -m pytest
   tests/integration/test_current_ranking_dispatch_composition.py
   --collect-only -q -o addopts= -p no:cacheprovider
   --basetemp=$SCRATCH/basetemp` — real exit 0; raw output
   `run2.log` 582 B, SHA-256
   `4ac81c7c6af821e2437796e42a1c88720bf82558d03c839620a169e2b392bdeb`:
   the five ordered node names listed, then `5 tests collected in
   0.81s`.
3. RUN3 one scoped two-file one-core Ruff: `env ... timeout -k 5 120
   prlimit --cpu=60 --as=1073741824 taskset -c 0 .venv/bin/ruff
   check src/slaif_raggedized_helper/source_bound_ranking.py
   tests/integration/test_current_ranking_dispatch_composition.py`
   — real exit 0; raw output `run3.log` 19 B, SHA-256
   `82b3e6a6c090a57601d22943bd23fca9218d1031dbe5a7b754092f9a156b4f18`
   (byte-identical to the prior rounds' Ruff digest): `All checks
   passed!`.
4. RUN4 one bounded physical product import-origin probe: the
   changed module `slaif_raggedized_helper.source_bound_ranking` and
   the seven modules it newly uses (`private_policy_pin_eligibility`,
   `raw_snapshot_membership`, `source_bound_stage_loss`,
   `supplied_policy_eligibility`, `text_evaluation_dataset`,
   `private_policy_request`, `raw_snapshot_pin`) all resolve to the
   canonical repository physical `src`; the changed file's
   working-tree SHA-256 is the exact indexed transfer digest
   `74c9bc48...` and the seven newly used modules match their
   receiving preimage digests (the six indexed ones at their indexed
   SHA-256s); ORIGINS_OK, exit 0; raw stream `run4.log` 1,503 B,
   SHA-256
   `8b4b1f3ca65e75fd8a8b98c0fc232a1baa2c61b4a41fd23a0e33ce948a046170`.

Mock/live distinction: all fixtures, roots and policy material are
synthetic and operator-owned; the five hosted nodes are hosted-only
compositions over real child processes, real pipes and real
fixtures with the trusted synthetic delegates. Collect-only, lint
and the origin probe prove structure and provenance only, not
hosted behavior; the 121-node focus exercises the inherited unit
behavior of the unchanged preimage suites against the transferred
module. The local proof establishes no hosted outcome.

No claim is made about this report's future push/CI; the separate
post-publication receipt records the remote facts observed after
push, and Root independently assesses the hosted results.

## Documentation impact

`STATUS.md`: current-slice line for 009-ai plus the concise 009-ai
slice note (round base, exact prior run 44840111535 attempt 1,
transcript byte identities, the two exact transferred blobs with
their SHAs, the bind_pinned guard/gate/clipped-end/post-load-tie
behavior, the five new hosted nodes and `2*M+B+2*G+4*P`
attribution, the receiving local proof under the `/dev/shm`
recovered scratch, the expected hosted gate at exactly 975
integrations, and the open gates). `docs/evaluation.md`: new
section "The 009-ai current ranking dispatch transfer (same 009
continuation)" before the preserved input-contracts section,
recording the blob-identity transfer, the entry and guard
semantics, the five witnesses, the per-catalog count formula, the
local proof environment recovery and limits, and the pending hosted
gate. No other documentation changed; no implemented commands,
measured performance, license clearance, readiness or baseline
measurement is claimed.

## DHA and boundaries

Decision: NONE (no D1 candidate reported; no ordered append; the
CRITICAL register was not loaded). Preserved: all remaining product
source, other test code and IDs, workflow, dependencies, runtime
setup, immutable prior reports and reviews, branches, policy,
unrelated worktrees, the parallel lane state and the strategy-side
state. No live model, data, credentials, protected runtime,
hardware, license decision, public interface, release, deployment
or merge performed or requested.

## Limitations and remaining work

The fresh exact report-head hosted CI is PENDING at authoring; this
report cannot certify its future push or checks. Until it is
measured, the five new hosted outcomes and the 975-passing
integration expectation are not hosted-proven. The candidate lane's
prior bounded local checks (121/121 focus, 5-node collect-only,
two-file one-core Ruff, ORIGINS_OK, plus the Root independent
`/dev/shm` source proof at the exact candidate bytes) and the Root
terminal review of the accepted 009-ah head are prior evidence, not
receiving proof. No scope deviation. Real source rights,
subsequent ranking, grading, cohort, stage, publisher,
authenticated delivery, governed full evaluation and the
representative baseline remain open; baseline NOT_RUN; whole 009
PARTIAL; no merge.
