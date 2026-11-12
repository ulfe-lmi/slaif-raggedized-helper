# OAP Coding Report — 007-e

Identifier: 007-e
Result: PARTIAL
Repository: ulfe-lmi/slaif-raggedized-helper
PR number: 9
Branch: oap/007-embedding-pipeline
Base branch: main
Round base commit: abb269c4b7304e8f3be4c63705c01941dbbb8625
PR main base: 11badc7782bed326995d400f5532b63399b91fbd (verified origin/main)
Implementation head SHA: 2bf4d3916c07bfd8e2ae99612885e364788c9e3f
Report publication commit: SELF

## Work and scope

Order 007-e (FINAL, DHA NONE, AMEND_EXISTING_PR) executed after the sole
consumed control; no resignal, no added readers, no FIFO reread. The exact
order/active (SHA-256 027002df, activation-record match) and fourteen Root
records plus the root-records index were committed byte-identical from the
strategic workspace (bae4529); 8c4456a is the ONE --no-ff merge of exact
composite tip bb6a9335 (implementation e55bc384, immutable SELF report
SHA-256 60574ab8); 2bf4d39 is the ONE new CI step plus docs/governance.
Pushed delta: thirty-three indexed product files (all additions or the
three indexed modifications), nineteen immutable parallel history additions,
no rebase/cherry-pick/force/reset/clean/stash, no product source adaptation.

## Acceptance evidence

1. Merge identity: parents bae4529+bb6a9335 verified; all thirty-three
   indexed files match Git blob and SHA-256 (oap/reviews/007-e-components.
   json) at the implementation head, byte-exact also after all local runs;
   merge tree equals the transcript tree plus exactly the 33+19 candidate
   entries and the tree diff against forecast 75130a36 is exactly the
   seventeen transcript entries; Root order/active/records byte-identical
   after the merge; same PR 9/branch; imported files untouched afterward.
2. Schema-2 `isolated-cpu-embedding-execution-v2`: shared factory predicts
   space/definition/worker profile+code+policy/native identity+policy/
   worker SHA/normalization/four-file bridge/hardware=unknown BEFORE model
   startup; the actual handshake derives the same canonical bytes and the
   suites compare predicted vs observed record+fingerprint before any text
   is forwarded; legacy space/definition/intended-CPU-FP32 identities are
   unchanged and complete execution fingerprints changed with the corrected
   native/isolated source (no hardcoded old value, no silent v1/v2 mix).
   Producer requires the explicit trusted authorization provider (no
   default), fresh epoch at the named boundaries, one attempt, COMPLETE
   only after actual typed publication plus fresh load, verified
   zero-model-start reuse, non-PENDING/non-COMPLETE refusal, ambiguous
   COMPLETE never overwritten, retained cleanup owner and lease drain.
3. Focused at the current canonical: seven unit files 147 passed (12.46 s);
   standalone integrations each in its own env -u PYTHONPATH process:
   worker 4, isolated 2 (existing multithreaded-fork warning retained),
   plan 1 and producer 21 (the latter two under the exact lane-accepted
   PYTHONPATH=tests/unit:tests/integration), plus the existing native
   chunking composition 14. Three unchanged Root witnesses (native close
   ownership, native interrupt priority, producer lease interrupt) all
   exit 0 with indexed sources byte-unchanged after fault injection.
   Full: tests/unit 1303 passed (65.95 s); tests/integration 619 passed
   (606 in one run plus the 13 installed-CLI suites re-passed in 52.59 s
   after fixing MY local invocation PATH only — .venv/bin was not on PATH
   for the direct interpreter call; no product change, CI uses uv run);
   ruff/compileall/diff-check clean; OAP scaffold 41 OK; check_state
   exit 0 (ACTIVE 007-e; routine 49936/50000; MANIFEST re-hashed
   TESTING.md and CONTEXT-BUDGET.md only); console --help 0; doctor
   example exit 1 with honest MODEL_UNQUALIFIED/SECRET_ABSENT.
   One transient local failure (test_timeout_kills_owned_descendant,
   descendant-reap timing under host load) passed 3/3 isolated and in the
   clean focused rerun; reported, not hidden.
4. The actual BGE model has NOT been run: all neural behavior is trusted
   fakes; the old-SHA random one-layer toy evidence is separately scoped
   and grants no new neural call; no weights, permits or credentials in
   Git. Legacy CPU pins (Torch 2.10.0+cpu / Transformers 4.51.3) are NOT
   security qualified (recorded advisory observation committed as ordered);
   the required exclusive GPU FP16 corpus encoding remains unimplemented.
5. CI run 43143641055 at exact 2bf4d39: ALL FIVE required jobs SUCCESS,
   every step success (74/74; Product 3.12/3.14 jobs 130936280870/
   130936280334, OAP 3.12/3.13/3.14 jobs 130936280678/130936280684/
   130936280623). The new portable synthetic six-real/22-metadata CPU
   fixture step (helper output never sourced) succeeded on both product
   legs; no claim about this report's future push/CI.

## Verification

Commands: per-file pytest for the seven unit files and the standalone
integrations (separate env -u PYTHONPATH processes, approved
SLAIF_NATIVE_TEST_*/SLAIF_CPU_WORKER_TEST_*/PDF_TEST_* 3.12 fixtures,
OPENBLAS/OMP threads 1); the three /tmp/raggedized-root-* witnesses via
the venv interpreter from the repo root; full tests/unit and
tests/integration; uv run ruff check; compileall; git diff --check;
unittest discover -s tests/oap (41); oap/bin/check_state.py --repo-root .;
console help/doctor; gh run/job/step inspection for run 43143641055.
Mock/live: synthetic owned fixtures; store/lease/journal/native-count and
the worker process protocol are real local DEV execution on toy artifacts;
the CI capsule is a synthetic fixture, not a real ML runtime; live
model/GPU/corpus authorization NONE.

## Documentation impact

README (007-e paragraph, PARTIAL line), STATUS (current slice 007-e),
TESTING (T16 consolidated within its previous 229 bytes; routine
49936/50000), docs/UNCERTAINTIES (007-e observation incl. legacy-security
advisory state), docs/embedding.md (integrated APIs with exact blobs,
predicted/observed identities, rights-provider trust, one-attempt/reuse/
refusal and cleanup/uncertain-output semantics, real vs fake vs old-toy,
required GPU path, remaining gates); MANIFEST re-hashes TESTING.md and
CONTEXT-BUDGET.md only. Historical orders, reports and Root reviews
unchanged.

## DHA and boundaries

DHA NONE; CRITICAL.md untouched. Strategic bytes committed byte-identical;
candidate immutable histories/SELF identity preserved through the
authorized merge. No merge: PR 9 OPEN on main 11badc7, no auto-merge, no
tag/release/deploy; no model/profile/weight/service/credential/corpus
change; no app pyproject/uv.lock change (worker_profiles/cpu is a
separate isolated profile); FIFOs untouched after the consumed control;
first 007-e response, sent once after remote report verification.

## Limitations and remaining work

- 007 PARTIAL: actual BGE model execution under the fixed CPU worker,
  CPU FP32 query and dot-product search, resumable owned GPU batches and
  the required exclusive GPU FP16 corpus encoding, snapshot/manifest
  binding, all precision/hardware qualification.
- The authorization provider is a trusted extension point, not an
  implemented principal/current-policy store or rights attestation;
  legacy CPU profile advisory triage and a patched profile refresh are
  separate pending work; no vulnerability-absence or license claim.
- Candidate/Root records are immutable provenance, not current CI or
  acceptance; ICA/MVP/rights gates remain open.
