# OAP Coding Report — 007-g

Identifier: 007-g
Result: PARTIAL
Repository: ulfe-lmi/slaif-raggedized-helper
PR number: 9
Branch: oap/007-embedding-pipeline
Base branch: main
Round base commit: 8efacce5a0d300833f021b1e442908fdf7318e9f
PR main base: 11badc7782bed326995d400f5532b63399b91fbd (verified origin/main)
Implementation head SHA: 5d1acfe06aa76521046d600971b01500ae41d4d6
Report publication commit: SELF

## Work and scope

Order 007-g (FINAL, DHA NONE, AMEND_EXISTING_PR) executed after the
sole consumed control; no FIFO reread, no second waiter, no
model/profile change. Exact selective integration only: commit
fe00edb committed the exact Root order (SHA-256 10d38716, workorder
match), active (007-g), the fourteen immutable Root records and the
root-records index (0b26b0cf), plus the components index (658f77e0),
all byte-identical from the strategic workspace; commit 5d1acfe then
transferred the TWENTY-FIVE indexed files by byte-identical file copy
from the two reviewed candidates (adfc96e7 CPUv2 alignment/portable-
fixture, d7b9bdc6 corrected GPU raw backend): no branch merge/
cherry-pick/rebase, no candidate ancestry, no source adaptation, no
test weakening. Added the ONE required CPUv2 CI fixture step and the
current docs.

## Acceptance evidence

1. Selection identity: 23 of 25 files byte-exact at the implementation
   head (blob+SHA-256+bytes per oap/reviews/007-g-components.json,
   278,431 B); the two worker_profiles/*/README.md hold the exact
   candidate prefix plus only a precise current-selection note. Order/
   active/14 records + index byte-identical after every run. All other
   changes restricted to the ordered workflow/docs/governance paths;
   the old CPU profile/helper/fixture, the native 0.21.4 inputs and
   the F cleanup/isolated/journal/device-lease behavior remain intact
   (no broad candidate ancestry import).
2. CPUv2 selection: cpu_embedding_backend/worker/execution_contract
   now select worker_profiles/cpu-v2/uv.lock (Torch 2.14.0+cpu /
   Transformers 5.22.2 / framework tokenizers 0.23.1, safetensors
   0.8.0, huggingface-hub 1.31.0, NumPy 2.5.4; 38 locked metadata
   distributions); the BEFORE-content child handshake and source
   fingerprint semantics are preserved, complete source/execution/job
   IDs changed naturally, and a legacy pre-cutover COMPLETE (old
   profile/code/bridge hashes) is refused reuse. The legacy helper
   regression is kept and the /proc descendant-disappearance race is
   narrowed.
3. Focused local at the implementation head (Python 3.14.4 venv,
   NumPy 2.5.4 parent, OPENBLAS/OMP/MKL/RAYON threads 1, no bytecode,
   prlimit 1 GiB AS / 30 s CPU, 120 s wall): v2-fixture unit set 269
   passed (backend/worker/contract/session/plan/producer, batch
   plan/store, journal/ownership, isolated, GPU lease, GPU backend);
   legacy-fixture setup 11 passed; native prereq 20 passed; five
   standalone integrations in separate env -u PYTHONPATH processes:
   worker 4, plan 1, isolated 3 (retained multithreaded-fork
   warning), producer 30, GPU raw 1; /tmp/raggedized-root-gpu-
   interrupt-remediation.py six corrected interrupt cases PASS with
   the script and both GPU sources SHA-unchanged before/after. ruff
   clean; compileall exit 0; OAP scaffold 41 OK; check_state exit 0
   (ACTIVE 007-g; routine 50000/50000; MANIFEST re-hashed TESTING.md
   17,449 B and CONTEXT-BUDGET.md); console help 0; doctor example
   exit 1 with honest issues (MODEL_UNQUALIFIED x3, SECRET_ABSENT).
   Candidate-side counts (CPU 177 unit + 40 standalone + 5 witnesses,
   portable 18 unit + 4 worker + 1 premodel, GPU 84 unit + 1
   standalone + 6 interrupt cases) are candidate evidence, not
   current canonical CI.
4. CI run 43160235569 at exact implementation head 5d1acfe: ALL FIVE
   jobs SUCCESS, 76/76 steps success (Product 3.12 job 130989379595 /
   3.14 job 130989379300, 23 steps each including the new "Provision
   portable synthetic CPU-v2 test fixture" after the legacy CPU
   fixture and before lint; OAP 3.12/3.13/3.14 jobs 130989379548 /
   130989379600 / 130989379642, 10 steps each); no skipped/missing
   steps. No claim about this report's future CI.
5. GPU raw backend finite and inert: corrected candidate exact
   (assigned synthetic device UUID byte guard before local FP16 load,
   child/process-owned DeviceLease assertion, bounded immutable
   native-ID input, no autocast, ordered finite CPU FP32 raw CLS 1024
   output, sticky close/owner retention, original non-Exception
   identity under hostile backend_owner attachment; before
   from_pretrained returns there may be no captured model owner —
   documented honest unknown boundary; no parent-owned serialized
   lease, no caller-lease release). Controlled fakes only.
6. No actual model, weights, GPU, corpus, credential or service
   operation; no Torch/Transformers/NumPy model execution; the
   synthetic CPUv2 fixture is six real wheels plus 32 DATA-ONLY
   metadata distributions, not an installed ML runtime. The actual
   BGE model, checkpoint and hardware remain UNRUN/UNQUALIFIED; the
   actual full-38 CPUv2 installation remains a separate PARTIAL
   (latest diagnostic: uv allocation abort under the fixed 2 GiB
   address space, no full CLI acceptance or neural import); future
   owned GPU worker/controller and physical drain remain absent.
   Newer pins alone are no clearance; advisory findings preserved.

## Verification

Commands: per-file pytest (v2-fixture unit set, legacy-fixture setup,
native prereq units); the five standalone integrations each in its own
env -u PYTHONPATH process (producer/plan under
tests/unit:tests/integration:src PYTHONPATH; approved
SLAIF_CPU_V2_TEST_*/SLAIF_CPU_WORKER_TEST_*/SLAIF_NATIVE_TEST_*/
PDF_TEST_* 3.12 fixtures); the interrupt-remediation script via the
venv interpreter with SHA checks; ruff check src tests/unit
tests/integration; compileall oap tests; git diff --check; unittest
discover -s tests/oap (41); check_state.py --repo-root .; console
help/doctor; gh run/job/step inspection of run 43160235569.
Mock/live: synthetic owned fixtures and trusted in-memory fakes; the
worker protocol and isolated child processes are real local DEV
execution on toy artifacts; live model/GPU/corpus authorization NONE.

## Documentation impact

README (007-g paragraph, PARTIAL line), STATUS (current slice 007-g),
TESTING (T16 compressed: 17,449 B, routine 50000/50000),
docs/UNCERTAINTIES (new 007-g entry), docs/embedding.md (007-g slice
section, remaining-work and evidence-status updates); CONTEXT-BUDGET/
MANIFEST measured updates only. Historical orders, reports and Root
reviews unchanged; the two profile READMEs preserve their historical
preparation evidence.

## DHA and boundaries

DHA NONE; CRITICAL.md untouched. No merge: PR 9 OPEN on main 11badc7,
no auto-merge, no tag/release/deploy; no model/profile/weight/
service/credential/corpus change; no app pyproject/uv.lock change;
FIFOs untouched after the consumed control; one send-response.sh
--identifier 007-g sent after remote report verification.
