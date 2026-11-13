# OAP Work Order — 007-g

Status: FINAL
Identifier: 007-g
PR mode: AMEND_EXISTING_PR
Branch: oap/007-embedding-pipeline
Base commit: 8efacce5a0d300833f021b1e442908fdf7318e9f
PR number: 9
Expected active: 007-f
Provenance: H activated full-MVP/parallel mandate; A8.4/11.2/19/22/23/24; I exact Root CPU alignment/portable-fixture reviews and independent GPU affected-source re-audit237e; E obsolete selected CPU dependencies, legacy test /proc disappearance race, demonstrated GPU interrupt attachment faults corrected in reviewed candidate
Architecture SHA256: 4b41905396a3838269fd6cf372614cd23cb2c3b6a37be09f29ed752803c0983a
Governance SHA256: ff357d24a632804e9d71e4fdba86c5733ecca7ab79da403fb33b4dd6f9dca1df

## Objective
Selectively integrate TWENTY-FIVE exact reviewed CPUv2/profile/portable-fixture and GPU profile/raw-backend files, add ONE required CPUv2 synthetic-fixture CI step and update current documentation. This is bounded source integration, not model/runtime qualification. Whole007 remains PARTIAL; no default-branch merge or numeric008.

## Dependencies and current state
007-f implementation0495713119005c911fe3ea659fcbddd783bfc39a, sole-parent SELFreport8efacce5a0d300833f021b1e442908fdf7318e9f/reportSHA2d39209dc2d7b52cebb7be54c0c4e6f96f9d8ae010a5b5aeb937e8fdee089e85/7493B independently reviewed in audit/007-f-review.json. BOTH implementationCI43153296812 and reportCI43154816327 independently ALL5/ALL74SUCCESS; unique OPEN PR9, main11badc7782bed326995d400f5532b63399b91fbd, no draft/auto/unresolved threads, clean exact head and consumed response. Never reread FIFO. Canonical routine49936/50000; tokens UNMEASURED, law unchanged.

Root index audit/007-g-components.json SHA658f77e0af49c602381215c00c594f8a4dd9e99e92a19eef5853ad629ad48c6a enumerates25 files/278431B, candidate/blob/SHA/size each. CPU source candidateadfc96e731feef691828e7b96df149a7599bef01 (portable impl485fc6877120597ad86a3f70e2b457eaa0d7f3e6, inherited reviewed alignment8d71e52fcf3d0f90ee60eb79b5b38d939724ddf6); GPUd7b9bdc6b326210ea7191ec85533a8689a0e0622 (impl6da14ba514dbadf55c9e4751fed37c5ad8c1ad19). Independent affected GPU re-audit237e199b1a2f6ca44fa4e27c1e51143f412644b6f73fbe279e52d9c0e550b30f COMPLETE_ACCEPT_CANDIDATE source only. Prior afc5 CHANGES_REQUIRED remains historical, not a false pass. Read index/APIs/current diff and relevant transitive sections, measure reads; do not load all278KB/history/sourcebooks by default.

## Allowed paths and scope
FIRST commit exact Root order/active plus FOURTEEN immutable Rootrecords from audit/007-g-root-records.json and that index itself -> oap/reviews/007-g-root-records.json. Source paths are under strategic root, targets under repository. Commit immutable bytes unchanged; exclude runtime/STATE/FIFOs/private permits/weights.

Then SELECTIVE file copies from exact candidates according to index, NOT branch merges/cherry-picks/rebase. Candidate history includes unrelated work and older GPU faults. Twenty-three indexed files must be byte-identical at final source/current report. The TWO worker_profiles/*/README.md files may ONLY append a precise current-selection note after the exact candidate prefix; preserve historical preparation evidence. No source adaptations or test weakening; report concrete incompatibility before changing indexed code.

Additional paths allowed: .github/workflows/oap.yml (ONE required additional product step, described below), README.md, STATUS.md, TESTING.md, docs/embedding.md, docs/UNCERTAINTIES.md; oap/governance/CONTEXT-BUDGET.md and MANIFEST.json only measured documentation/hash updates if necessary. Preserve routine<=50000 by concise current T16 compression within existing footprint; no law/sourcebook/architecture/projection refresh. Imported profile locks/pyprojects/requirements/helpers remain exact. Existing old CPU profile/helper/fixture and native0.21.4 inputs remain intact. No actual full38 installer or GPU57 fixture transfer in this order.

## Non-goals
No mainmerge/008/release/deploy/auto-merge, actual heavy ML package installation/import, Torch/Transformers/NumPy/Tensor/model execution, checkpoints/weights, GPU/driver/device/service/SSH/credential/private corpus operation, current-rights store, resident query implementation, GPU worker/controller/bulk or physical vacancy claim. Corrected raw GPU source is not an executable owned GPU process. No old CPU toy allowance transfers.

## Acceptance criteria
1. Exact14Rootrecords+index/order/active, exact25file selection with23immutable blobs and2prefix-preserving README appends. All other changes restricted above. Preserve F cleanup/isolated/journal/device-lease behavior; no broad candidate ancestry import. Record actual hashes/diff.
2. CPU source gates select reviewed CPUv2 graph38/Torch2.14.0+cpu/Transformers5.22.2/framework tokenizers0.23.1; execution contract and BEFORE-content actual child handshake/source fingerprint align. Native engine0.21.4 stays independent. Semantic/intended identity remains; complete source/execution/job IDs naturally change. Legacy COMPLETE cannot masquerade as current identity. Preserve every original producer cleanup test alongside added profile case, and narrow legacy /proc read race fix.
3. CPUv2 portable helper uses explicit canonical trusted standalone3.12 runtime, six exact actual lightweight wheels plus32 explicitly DATA-ONLY metadata distributions. No importable fake ML packages or actual framework. Keep separate OLD28fixture/variables required for legacy helper regression. A synthetic metadata fixture is not actual installed38runtime.
4. Add ONE mandatory step after existing CPU fixture provisioning, before lint/tests, on BOTH product legs. Invoke tests/support/prepare_cpu_worker_test_backend_v2.py with --runtime-dir "$PDF_TEST_RUNTIME" and NEW direct /tmp target containing GITHUB_RUN_ID, GITHUB_RUN_ATTEMPT and matrix interpreter (e.g. /tmp/slaif-cpu-v2-${GITHUB_RUN_ID}-${GITHUB_RUN_ATTEMPT}-${{ matrix.python-version }}). test target absent, set -o pipefail, tee setup log. Literal GITHUB_ENV entries SLAIF_CPU_V2_TEST_ROOT=$PDF_TEST_RUNTIME and SLAIF_CPU_V2_TEST_PACKAGES=$target/packages. Never source/eval exports; no skip/fallback/continue-on-error. Retain all existing steps/pins/permissions/matrices and old fixture variables. Expected5jobs76steps; actual required current checks/steps govern, no skipped/missing success.
5. GPU raw backend is exact corrected candidate: full57locked graph, assigned exact synthetic device UUID byte guard before local FP16 model loading, actual child/process-owned DeviceLease assertion, bounded immutable native-ID input, no autocast, finite ordered CPU FP32 raw CLS1024 output, sticky close/owner retention, original non-Exception identity across hostile backend_owner attachment. Before from_pretrained returns there is no captured model owner: document that honest unknown boundary. No parent-owned serialized lease or caller-lease release. All of this is tested controlled fake/source behavior only.
6. Current docs distinguish archived prior OWNED random CPU toy execution from actual BGE/checkpoint/hardware still UNRUN/UNQUALIFIED. CPUv2 source selection is current after this order; actual full38 setup attempts are separate PARTIAL (latest diagnostic known uv allocation abort under fixed2GiB AS, no full CLI acceptance/neural import). GPU profile/raw source finite/inert; future owned-worker/controller/physical drain remain absent. Preserve original advisory findings and unproven transitive/security/license status; newer pins alone are no clearance. No source compatibility/quality/hardware claim from fakes.

## Verification and negative evidence
Inspect candidate source/API/current diff identities. Run relevant CPU backend/worker/executioncontract/profile/legacy+v2 setup/GPU backend/device-lease/producer/isolated units. Run SEPARATELY worker, plan, isolated, producer and GPU raw standalone integrations with BOTH old/new fixture environments and native/PDF prerequisites. Root prior CPU177unit+40standalone+5original witnesses, portable18unit+worker4+premodel1 and GPU84unit+1standalone+6corrected independent interruption cases remain candidate evidence, not current canonical CI. Reproduce existing relevant Root causal scripts at current code with indexed source hashes checked before/after; /tmp/raggedized-root-gpu-interrupt-remediation.py tests six corrected interrupt cases. Do not run historical scripts that assert an old bug as if expecting current success.

Product lint/compile/diff, OAP41/check_state/source-copy/budget and consolehelp/doctor honest. Current GitHub full unit/integration/OAP suites on both matrix legs required; proportionate focused local tests plus CI suffice, avoid needless duplicate entire local sweeps absent a new failure. Prepend project.venv/bin to PATH or uv run for installedCLI lookup. Report counts separately/actually, no collection-only/separate-files-as-single-sweep claims. Missing prereq means failed evidence, not silent skip or unsandboxed fallback.

## Runtime and protected resources
Existing cached app/Python3.14+NumPy2.5.4 parent, threads1 (OPENBLAS/OMP/MKL/RAYON), no bytecode. Focused <=1GiBAS/30CPU/120wall after uv startup; full CI approved disposable runner bounds. Native/PDF/OLDCPU fixtures use original standalone /home/janezp/.local/share/uv/python/cpython-3.12.15-linux-x86_64-gnu. SLAIF_NATIVE_TEST_PACKAGES=/tmp/raggedized-root-native-setup-b-6cd8bebe0a/packages and SLAIF_NATIVE_TEST_PYTHON=python3.12. SLAIF_CPU_WORKER_TEST_PACKAGES=/tmp/raggedized-root-cpu-synthetic-56cdd5b2898d3d17/packages. NEW SLAIF_CPU_V2_TEST_ROOT=/tmp/raggedized-root-cpython312-portability and SLAIF_CPU_V2_TEST_PACKAGES=/tmp/raggedized-root-cpu-v2-portable-485fc687/packages. PDF_TEST_PACKAGES=/tmp/raggedized-root-pdf-setup-20ca62cd48/lib/python3.12/site-packages, PDF_TEST_RUNTIME original3.12. No new LOCAL installations/downloads/metadata mutations needed. GPU raw unit/integration use in-memory trusted facades; no actual GPU fixture setup/model imports. No human agent model/profile/auth changes.

## Documentation
Current selected profile/source and exact integration evidence, finite independent GPU re-audit provenance, actual old toy versus unrun BGE, separate actual installer failure, synthetic-vs-real fixture distinction and all unfinished whole007/fullMVP gates. No history/report rewrites, queue-complete closure, human-owner referral behavior or invented measured capacity/security/license result.

## Deferred human adjudication

- Decision: NONE

## Publication and report
Root owns orders/review/acceptance/next; coding implementation/Git only. Same PR9 implementation literal SHA, then sole-parent immutable report-only SELFreport <=7500B with indexed identities/actual commands/counts/limits/docs/CI only as observed. Whole007 PARTIAL. Verify remote report then ONE normal send-response.sh --identifier007-g, end bounded goal/idle. Never reread/replay FIFO or start next objective/audit/merge. Preserve Qwen human settings and ordinary tool startup before optional Root bounded goal. Standing D0 development authority; no recurring human confirmation.
