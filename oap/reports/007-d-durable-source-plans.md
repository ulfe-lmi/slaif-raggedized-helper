# OAP Coding Report — 007-d

Identifier: 007-d
Result: PARTIAL
Repository: ulfe-lmi/slaif-raggedized-helper
PR number: 9
Branch: oap/007-embedding-pipeline
Base branch: main
Round base commit: 65f1ab5b2668b418a4a10ee6d83af84322196d12
PR main base: 11badc7782bed326995d400f5532b63399b91fbd (verified origin/main)
Implementation head SHA: 244b96e86b741b71319beacf4022d6d6d7f1dff6
Report publication commit: SELF

## Work and scope

Order 007-d (FINAL, DHA NONE, AMEND_EXISTING_PR) executed after the sole
consumed control; no resignal, no added readers, no FIFO reread. The exact
order/active (SHA-256 638aac11, activation-record match) and twelve Root
records were committed byte-identical from the strategic workspace
(3ab35a6); d10dab3 is the ONE --no-ff merge of exact candidate tip 2b50e658
(implementation 55ea655c, immutable SELF report SHA-256 cdcf15f3), parents
3ab35a6+2b50e658; 244b96e is docs/governance only. The 007-c CI erratum
(oap/reviews/007-c-CI-supplement.json) is committed as ordered and preserved
with the immutable order text. Pushed delta: the sixteen indexed files
(oap/reviews/007-d-components.json) plus eight lane orders/reports, all
additions; no rebase/cherry-pick/force/reset/clean/stash.

## Acceptance evidence

1. Actual merge parents verified (3ab35a6 transcript, 2b50e658 exact tip);
   merge tree equals the transcript tree plus exactly the 24 forecast
   additions (oap/reviews/007-d-integration-forecast.json); all sixteen
   indexed files match Git blob and SHA-256 at the implementation head;
   Root order/active/records byte-identical after the merge; existing
   codec/representation/artifact/space/CPU-session/source/deps unchanged;
   artifact doc reference fix preserved; 007-only candidate histories, no
   optional CPU profile or 008 transfer; same PR 9/branch.
2. Typed actual-Store publication and fresh load: canonical bounded
   metadata (seven root/seven dependency/eight row fields, 1-128 ordered
   rows), NPY container plus payload hash, shape, finite FP32 norm, fixed
   codec policy; no normalize-on-read; forged non-Store refused by the
   single typed guard (witness). Nonblocking per-job flock with PID+FD
   rooted ownership; failed-enter leaves no registry leak; fork and
   interrupt descriptor cleanup (witnesses). Actual-lease journal: bounded
   524,288-byte/depth-32/20,000-node/64-event/16-attempt envelopes, fresh
   SHA CAS, stage fsync, atomic replace, parent dirsync, fresh read; old
   state before and new state after post-replace failure; COMPLETE/reuse
   only a fresh real typed output matching the FULL plan; no automatic
   recovery/retry or pid steal; the 17th claim is honestly unreachable
   under the 64-event cap (no manufactured guard coverage).
3. Fresh source plan: actual OriginalStore plus source bundle plus native
   count batch plus local space admission; one source validation, one
   native count session (real 3.12 fixture); raw trusted title/headings/
   original text; ordered 1-128 unique chunks; exact seven dependencies /
   eight row fields / canonical UTF-8 / prefix mapping; positive revision,
   title, scope, count and policy order-change proofs in the suites;
   intended CPU FP32 execution declared as intent, not observed profile.
4. At the current canonical: four unit files 43 passed (0.99 s, Python
   3.14); each of the four standalone integrations (13/1/2/6) passed in
   its own env -u PYTHONPATH process under the approved 3.12 native
   fixture. All eight unchanged Root witnesses re-run exit 0 with indexed
   sources byte-unchanged (guard-removal and event-cap mutations caught;
   preflight peaks 2,208/2,248 bytes on 1,000,000-char inputs). Full
   regression green: tests/unit 1166 passed (57.84 s),
   tests/integration 591 passed (346.61 s). No skip/deselection/fake pass;
   no genuine neural call.
5. Full checks at exact 244b96e: ruff clean, compileall clean, git diff
   --check clean, OAP scaffold 41 OK, check_state exit 0 (ACTIVE 007-d;
   routine 49935/50000; MANIFEST re-hashed TESTING.md and CONTEXT-BUDGET.md
   only), console --help 0, doctor example 1 with honest CONFIG_MISSING.
   CI run 43133432374 at exact 244b96e: ALL FIVE required jobs SUCCESS,
   every step success (72/72; Product 3.12/3.14 jobs 130902875188/
   130902875492, OAP 3.12/3.13/3.14 jobs 130902875544/130902875569/
   130902875773). No claim about this report's future push/CI.

## Verification

Commands: per-file pytest for the four unit files and the four standalone
integrations (separate env -u PYTHONPATH processes, approved
SLAIF_NATIVE_TEST_ROOT/PACKAGES/PYTHON fixture, OPENBLAS/OMP threads 1);
the eight /tmp/raggedized-root-* witnesses via the venv interpreter from
the repo root; full tests/unit and tests/integration; uv run ruff check;
compileall; git diff --check; unittest discover -s tests/oap (41);
oap/bin/check_state.py --repo-root .; console help/doctor; gh
run/job/step inspection for run 43133432374. Mock/live: synthetic owned
fixtures; store/ownership/journal/native-count are real local DEV
execution on toy artifacts; no neural framework in this scope; live
model/GPU/corpus authorization NONE.

## Documentation impact

README (007-d paragraph), STATUS (current slice 007-d), TESTING (T16
consolidated within its previous 230 bytes; routine 49935/50000),
docs/UNCERTAINTIES (007-d observation), docs/embedding.md (integrated
APIs, exact hashes, ownership/failure semantics, intended vs observed,
real fixture vs actual model/auth/license distinction, 64-event/16-attempt
honesty, remaining gates); MANIFEST re-hashes TESTING.md and
CONTEXT-BUDGET.md only. Historical orders, reports and Root reviews
unchanged.

## DHA and boundaries

DHA NONE; CRITICAL.md untouched. Strategic bytes committed
byte-identical; candidate immutable histories/SELF identity preserved
through the authorized merge. No merge: PR 9 OPEN on main 11badc7, no
auto-merge, no tag/release/deploy; no model/profile/weight/service/
credential/corpus change; no new package (pyproject/uv.lock unchanged);
FIFOs untouched after the consumed control; first 007-d response, sent
once after remote report verification.

## Limitations and remaining work

- 007 PARTIAL: encoder producer/controller/retry wiring the plans, store
  and journal to real execution, actual Torch/model execution, CPU FP32
  query and dot-product search, resumable owned GPU batches,
  snapshot/manifest binding and all precision/hardware qualification.
- Prepared values are forgeable; byte/hash admission proves no
  deserializer safety, current rights, publisher provenance or license
  clearance; a historical verified label is not fresh availability and
  unsigned private history is not rollback-proof.
- Candidate/Root records and the 007-c erratum are immutable provenance,
  not current CI or acceptance; ICA/MVP/rights gates remain open.
