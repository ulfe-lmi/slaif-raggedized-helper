# OAP Coding Report — 007-h

Identifier: 007-h
Result: COMPLETE for active 007-h (order + Root amendments
H1/doc-review-2); whole objective 007 remains PARTIAL
Repository: ulfe-lmi/slaif-raggedized-helper
PR number: 9
Branch: oap/007-embedding-pipeline
Base branch: main
Round base commit: 999357fe55060212bb081df1bce13b9cfecab921
PR main base: 11badc7782bed326995d400f5532b63399b91fbd (verified origin/main)
Implementation head SHA: 8080fec24dc4cbd0c107ece33d379a1b96d7decd
Report publication commit: SELF

## Work and scope

Order 007-h (FINAL, DHA NONE, AMEND_EXISTING_PR) executed exactly:
commit 5395df2 committed the exact Root order (SHA-256
fd1e5bbddc2c85bda9fc617a8e0b046c5ad973276e1a5b49f36141a8c2c3d49b;
active 007-h), fifteen immutable Root records, the components index and their index;
commit eb4739d transferred the SIX indexed files byte-identical
(70,906 B, oap/reviews/007-h-components.json) from the two exact
candidates, added the ONE required GPU-fixture CI step and corrected
current docs. Root then issued amendment H1 (CI 43169522375 at
eb4739d: OAP 3 SUCCESS, BOTH product legs FAILED at "Product test
suite" with the same five host-dependent installer unit cases —
FileNotFoundError /home/janezp on clean runners; 5 jobs/78 steps;
new GPU fixture step succeeded both legs): commit 5ba8aab committed
the exact amendment (SHA-256
661ea1c366b7991c4ef6d84062ae71fca1c5944611556246acba0646784020e0) and
CI record (SHA-256
cb7a412b946fa32b248ee3bda8165f72e6d02b935797f90ad0f3f39e51c1c4e8);
commit c030ded applied the ONE authorized source change. A second
trusted Root review (doc accuracy, reviewed at c030ded) was then
committed unchanged with the corrected docs as commit 8080fec.

## Acceptance evidence

1. Selection identity: at eb4739d all six files were byte-exact
   (70,906 B); per amendment H1 ONLY
   tests/unit/test_cpu_runtime_setup_v2.py now differs from the
   frozen candidate (23,095 → 28,320 B; SHA-256
   1ac8bce0bd13a6381287c866201b5313af74a9a67815c02b09c411fffa41f733 →
   6038a3b1766f52911f9d15b800d6fe515630b32f03cec52bca39b30ed56d1482,
   blob eabb9b419b0b6f933674580538ef5ef2c282e3a5); the other FIVE
   remain byte-exact (helper
   226a527650083ec3324fcb783354ca47eb8b30884f0db0d3e4df6c044e6ede0c
   et al.), current six-file sum 76,131 B (oap/reviews/007-h-
   components-after-portability.json, SHA-256
   2784d8f31030177456e8c2f3c7300f5fd7df7734304060e6eecba94d3faaee36);
   original index retained as history. The authorized change:
   self-contained controlled-fake preflight in OWN tmp_path (scoped
   m.RUNTIME/m.UV to owned dummy files; narrow test-only identity
   boundary mapping ONLY designated dummy bytes to the production
   digests, all other hashing real; no stub executed); one new
   identity/ambient negative-control case → 18 tests; cleanup-refusal
   cases keep primary failures. Test-only fake identity is NOT
   binary qualification.
2. Focused local at c030ded (Python 3.14.4 venv): installer unit 18
   passed, GPU fixture setup 4 passed, legacy 11, CPUv2 fixture 7,
   native 15+5 (38 total) passed; five Root priority/churn witnesses
   PASS (exit 0) against the canonical unchanged helper; ruff clean;
   compileall 0; OAP 41 OK; check_state ACTIVE 007-h (context
   49,998/50,000); help 0; doctor example exit 1 honest
   (MODEL_UNQUALIFIED x3, SECRET_ABSENT); git diff --check clean.
   The bounded subprocess case uses sys.executable (current test
   interpreter), not a standalone 3.12 test. The full local
   tests/unit sweep fails on this host (one test_derived_store.py
   failure then segfault in
   test_embedding_artifacts.py::test_unicode_admission_and_privacy),
   reproduced at BOTH base 999357f and current in a throwaway
   worktree: observed base/head comparison, cause UNRESOLVED — no
   integration-causality or platform-safety claim; GitHub CI is the
   mandatory gate.
3. CI: run 43172563733 at test-fix head c030ded: ALL FIVE jobs
   SUCCESS, 78/78 steps; final run 43174637884 at exact head 8080fec:
   ALL FIVE jobs SUCCESS, 78/78 steps (Product 3.12 job 131035802078 /
   3.14 job 131035802595, 24 steps each including the new GPU fixture
   step after the CPUv2 fixture and before lint; OAP 3.12/3.13/3.14
   jobs 131035802731/131035802586/131035802659, 10 steps each); no
   skipped/missing steps. GPU fixture on both legs: six hash-pinned
   wheels + 51 DATA-ONLY records, SLAIF_GPU_TEST_ROOT=
   /home/runner/.local/share/uv/python/cpython-3.12.14-linux-
   x86_64-gnu, /tmp/slaif-gpu-test-<run>-<attempt>-<leg>/packages.
   PR 9 OPEN, head 8080fec, base main.
4. Docs corrected per Root doc-accuracy review 2 (SHA-256
   b76a1f30a4f1041e5070c748920e27febaf52f5d5af30925a83701a46406d54d):
   README/STATUS/embedding/UNCERTAINTIES/CPUv2-selection now state
   five-exact + one-amended unit (76,131 B, count 18), bounded
   subprocess = sys.executable, synthetic /dev, segfault cause
   UNRESOLVED, precise toy/BGE execution scope; TESTING T1..T16 and
   context budget unchanged (49,998 B); MANIFEST re-validation via
   check_state.

## Mock/live and boundaries

Controlled fakes for mocked installer flows; real hashing, fixtures
and bounded sys.executable subprocess otherwise; live
model/GPU/corpus authorization NONE. DHA NONE; CRITICAL.md
untouched. No merge (PR 9 OPEN on main 11badc7, no auto-merge/tag/
deploy); no model/profile/weight/service/credential change; no
skips/xfail/deselect, no Root paths on CI, no heavy installs;
FIFOs untouched after the consumed control. No whole-007/MVP/
security/license/hardware/BGE/parity qualification is claimed;
whole 007 remains PARTIAL. One send-response.sh --identifier 007-h
sent after remote report verification.
