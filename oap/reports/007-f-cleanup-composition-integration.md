# OAP Coding Report — 007-f

Identifier: 007-f
Result: PARTIAL
Repository: ulfe-lmi/slaif-raggedized-helper
PR number: 9
Branch: oap/007-embedding-pipeline
Base branch: main
Round base commit: 52ae2918c09ea939ba7c8694cd6e65e735c1d918
PR main base: 11badc7782bed326995d400f5532b63399b91fbd (verified origin/main)
Implementation head SHA: 0495713119005c911fe3ea659fcbddd783bfc39a
Report publication commit: SELF

## Work and scope

Order 007-f (FINAL, DHA NONE, AMEND_EXISTING_PR) executed after the sole
consumed control; no FIFO reread, no second waiter, no model/profile
change. Exact integration only: the order (SHA-256 a71a329a,
activation-record match), active, fourteen immutable Root records and
the root-records index (febead50) plus components index (199fd1a2) were
committed byte-identical from the strategic workspace (b6b5ea5), then the TWO authorized local
--no-ff merges in the ordered sequence: cleanup-composition tip 985806af
(implementation 4a929261, ancestry already containing the GPU
device-lease report 692fa53b/implementation 6c29b935) and isolated-exit
tip 52252484 (implementation 48aafeef). Pushed delta: the
activation transcript (order/active/14 records + index), the two
--no-ff merge commits carrying the seven immutable parallel lane
history additions, and the small current docs/governance commit; no
source adaptation, no conflict resolution, no
rebase/cherry-pick/force/reset/clean/stash.

## Acceptance evidence

1. Merge identity: first merge 70e2fa4 parents b6b5ea5+985806af, second
   merge 8825049 parents 70e2fa4+5225248; both trees equal their exact
   git merge-tree forecasts (29496ae7 = base forecast 38d49bf9 + the
   seventeen transcript entries; bd4f3ddc for the second), clean, no
   conflicts. All seventeen indexed source/test/API blobs (blob+SHA-256+bytes per
   oap/reviews/007-f-components.json) exact at the implementation head and byte-unchanged after every local run;
   original order/active/14 records + index byte-identical after the
   merges; all other code/deps/history untouched except the prescribed
   transcript and docs.
2. Focused at the current canonical: six unit files 105 passed (12/19/
   27/11/34/2 = Root 105 at the composed tree); six standalone
   integrations 39 passed (ownership 1, lease 2, journal 2, isolated 3
   with the retained multithreaded-fork warning, producer 30, plan 1),
   each in its own env -u PYTHONPATH process (producer/plan under the
   lane-accepted tests/unit:tests/integration PYTHONPATH; approved
   SLAIF_NATIVE_TEST_*/SLAIF_CPU_WORKER_TEST_*/PDF_TEST_* 3.12 fixtures;
   OPENBLAS/OMP threads 1). The TEN original /tmp/raggedized-root-*
   witnesses (isolated-exit-priority, producer-secondary-interrupt,
   journal-cleanup-boundaries, producer-lease-interrupt,
   native-close-ownership, native-interrupt-priority,
   gpu-lease-registry, job-ownership-boundaries, job-enter-failure,
   job-interrupted-close) all exit 0 with the 17 indexed sources
   byte-unchanged before/after. Full: tests/unit 1341 passed (65.44 s);
   tests/integration 618 passed plus the 13 installed-CLI tests
   (10+3) re-passed in 55.44 s after fixing my local invocation PATH
   only (.venv/bin not on PATH for the direct interpreter call; no
   product change; CI uses uv run). ruff/compileall/diff-check clean;
   OAP scaffold 41 OK; check_state exit 0 (ACTIVE 007-f; routine
   49936/50000; MANIFEST re-hashed TESTING.md only, 17,385 B, 229-B
   T16); console --help 0; doctor example exit 1 with honest issues.
3. Behavior per the imported immutable APIs: finite owned-descriptor
   close attempts with original non-Exception interruptions preserved,
   new cleanup interrupt outranking ordinary errors; no blind re-close
   of a reused number (same-inode included); sticky UNKNOWN/cleanup
   owner reaching sanitized journal and producer errors even before the
   claim returns, no auto-reclaim/false idempotence; producer pending
   native/model resource and journal lease held until drain; isolated
   context-exit same interrupt priority; cooperative gpu-device-lease-
   v1 key binding ONLY versioned host+physical UUID under the trusted
   common local root (cooperation, not physical exclusivity or runtime
   authority). Identities: predicted/observed handshake and source-job
   matching work, no hardcoded old value; semantic/native 0.21.4/legacy
   CPU intent identities preserved; legacy CPU profile UNQUALIFIED and
   unchanged. Advisory severity corrected: GitHub TorchScript advisory
   GHSA-rrmf-rvhw-rf47 LOW; Transformers list four HIGH/six MEDIUM/one
   LOW, all UNPROVEN transitive reachability, NOT_EXPLICITLY_INVOKED
   direct fixed routes (committed Root observation; severities
   re-verified on GitHub 2026-11-12).
4. The actual BGE model has NOT been run: all neural behavior is trusted
   fakes; no weights, permits or credentials in Git; no actual GPU
   lifecycle, retry/reclaim/mode controller, current-policy store or
   service/credential operation.
5. CI run 43153296812 at exact 0495713: ALL FIVE required jobs SUCCESS, every step success (74/74; Product jobs 130967316151/130967316361, OAP jobs 130967316270/130967316525/130967316343); no claim about this report's future CI.

## Verification

Commands: per-file pytest for the six unit files and the standalone
integrations (separate env -u PYTHONPATH processes, approved 3.12
fixtures, threads 1); the ten /tmp/raggedized-root-* witnesses via the
venv interpreter from the repo root; full tests/unit and
tests/integration; ruff check; compileall; git diff --check; unittest
discover -s tests/oap (41); oap/bin/check_state.py --repo-root .;
console help/doctor; gh run/job/step inspection for run 43153296812.
Mock/live: synthetic owned fixtures; store/lease/journal/native-count
and the worker process protocol are real local DEV execution on toy
artifacts; the CI capsule is a synthetic fixture, not a real ML
runtime; live model/GPU/corpus authorization NONE.

## Documentation impact

README (007-f paragraph, PARTIAL line), STATUS (current slice 007-f),
TESTING (T16 compressed within its 229-B footprint; TESTING.md still
17,385 B, routine 49936/50000), docs/UNCERTAINTIES (new 007-f entry
with exact peer finding/remediation and corrected advisory severities),
docs/embedding.md (007-f section with 17-identity proof, cooperative
vs physical ownership, unknown cleanup/refusal/finite-process limits,
advisory severity correction, evidence status); MANIFEST re-hash of
TESTING.md only. Historical orders, reports and Root reviews unchanged.

## DHA and boundaries

DHA NONE; CRITICAL.md untouched. No merge: PR 9 OPEN on main 11badc7,
no auto-merge, no tag/release/deploy; no model/profile/weight/service/
credential/corpus change; no pyproject/uv.lock change; FIFOs untouched
after the consumed control; one send-response.sh --identifier 007-f
sent after remote report verification.

## Limitations and remaining work

- 007 PARTIAL: actual BGE model execution under the fixed CPU worker,
  CPU FP32 query and dot-product search, resumable owned GPU batches
  and the required exclusive GPU FP16 corpus encoding,
  snapshot/manifest binding, precision/hardware qualification.
- Finite fault coverage is not universal cleanup, power-loss,
  kernel-reaping, restart-recovery or hardware proof; the cooperative
  device key is not physical exclusivity; the provider is not an
  implemented current-policy/rights store; peer records are provenance,
  not a new ICA or human adjudication; ICA/MVP gates remain open.
