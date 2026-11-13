# OAP Coding Report — 007-p

Identifier: 007-p
Result: PARTIAL
Repository: ulfe-lmi/slaif-raggedized-helper
PR number: 9
Branch: oap/007-embedding-pipeline
Base branch: main
Round base commit: c50213fbbd246adb8d6f89cac601239491974deb
PR main base: 11badc7782bed326995d400f5532b63399b91fbd
Transcript commit: 63a9014567b40fe5139abfa802ee06203952a334
Implementation head SHA: cd6d22bd640b23298cdedc8970bed495aa982263
Report publication commit: SELF

## Work and scope

Order 007-p (FINAL, DHA NONE, AMEND_EXISTING_PR) ran transcript-first from the round base: (1) transcript 63a90145 (sole parent = round base): exact final order (SHA-256 a281c27e490d70dca40730c4a8ca65d864969d0cbae4a1a1e8f95ccc3c258306), active `007-p`+LF, seven exact Root integration-fixture-collection records (22,204 B total) and the exact index (oap/reviews/007-p-root-records.json, 1,777 B, SHA-256 290792a8f465b50e87ccc6d638c26438b98ba283b51ad6d706719a6310a7964b); every record verified byte- and hash-exact before commit; no Root bytes edited. (2) Implementation cd6d22bd (sole parent = transcript): exactly TWO files changed, import-order only — in tests/integration/test_corpus_embedding_executor_composition.py and tests/integration/test_gpu_embedding_producer_composition.py the line `from test_gpu_worker_launch import _prepared_fixture` moved before `from test_embedding_batch_plan_composition import journey  # noqa: F401`. Final bytes byte-exact to the ordered forecast: corpus 38,234 B SHA-256 06eec3c9143aded63deff7b9fc0f64f6c4b08bb85acddac1691f7d1d45060185; producer 70,160 B SHA-256 b491dc396870dbfa3774cff98f3e1c75c15395267a34af8234f60a0827ea6eaa. No rename/package/loader/pytest/CI/dependency/law/docs change; no sys.path/importlib/sys.modules workaround or collection-mode change; no merge/cherry-pick/rebase/reset/stash/clean/switch; no nested agents or other consumer.

## Acceptance evidence

1. AST equivalence: both changed module ASTs equal to their c502 base except the ordering of the same two ImportFrom statements (verified node-by-node; the other 18 and 51 top-level statements identical in order/content); every test/fixture/function/decorator/assertion and all product sources unchanged. The fixture is still loaded from the normal integration module test_gpu_worker_launch.py via its established uniquely named unit-helper loader (importlib file spec `gpu_launch_unit_fixture`); no fake success.
2. Complete tests/integration --collect-only, ONE run, exit 0: 752 items collected, all modules, no import-file mismatch, no missing setup. PYTHONPATH unset; required existing CPUv2 fixture env (SLAIF_CPU_V2_TEST_ROOT, SLAIF_CPU_V2_TEST_PACKAGES, exact cached paths). A small owned pytest plugin recorded the ACTUAL sys.modules['test_gpu_worker_launch'].__file__ at collection finish and asserted it equals tests/integration/test_gpu_worker_launch.py (recorded OK); the plugin only read sys.modules, no sys.path/import/collection change. Per-module counts match Root's archived reproduction (corpus 11, journey 6, producer 35, worker-launch 1). No count-only rerun; no journey execution during collect-only.
3. Two focused actual checks, each ONE own capped process under the same default integration import layout (ordinary full tests/integration collection with -k selection: 1 selected / 751 deselected; full collection is also what makes the fixture's bare unit-helper import resolve, as in CI) and the exact cached synthetic setup: test_gpu_launch_preparation_owner_composition.py::test_owner_handoff_preserves_existing_arguments: 1 passed, exit 0; test_corpus_embedding_executor_composition.py::test_actual_whole_program_rowfit_refuses_before_dispatch: 1 passed, exit 0. Real fixture/owner/rowfit behavior after the reorder; no old 51/13/full integration replay, no historical heavy driver. First full-layout attempt without the CPUv2 pair reproduced Root's four KeyErrors (preserved); the pair was then included as required.
4. Each process capped CPU30/AS1073741824/wall120 (prlimit+timeout), five OMP/OPENBLAS/MKL/RAYON/NUMEXPR threads 1, PYTHONDONTWRITEBYTECODE=1, private 0700 basetemp. ruff check on the two changed files: All checks passed. AST/body-equivalence and scoped diff/source hashes per evidence 1-2. No installation/network/model/GPU/service/credential/private corpus; existing synthetic cached packages only where the named cases require them.
5. CI: no CI run exists for the report commit at publication; required checks at the CURRENT REPORT head PENDING/UNOBSERVED; development acceptance REQUIRES every one of all 5 jobs and every actual required step (currently 78) SUCCESS; missing/skipped/pending/cancelled/failed is not green; no bypass; post-push observation recorded separately.

## Verification

prlimit --as=1073741824 --cpu=30 timeout 120 env -u PYTHONPATH PYTHONDONTWRITEBYTECODE=1 OMP/OPENBLAS/MKL/RAYON/NUMEXPR_NUM_THREADS=1 SLAIF_CPU_V2_TEST_ROOT=/tmp/raggedized-root-cpython312-portability SLAIF_CPU_V2_TEST_PACKAGES=/tmp/raggedized-root-cpu-v2-portable-485fc687/packages <owned driver: pytest.main(['tests/integration','--collect-only']) + read-only observation plugin> --basetemp=<private 0700>: exit 0, 752 collected in 1.23 s, loaded-file assertion INTEGRATION. Same caps and unset PYTHONPATH, plus SLAIF_GPU_TEST_ROOT=/tmp/raggedized-root-cpython312-portability, SLAIF_GPU_TEST_PACKAGES=/tmp/raggedized-root-gpu-fixture-c0e14e2c/packages, the CPUv2 pair (full-collection import), and for the rowfit case only SLAIF_NATIVE_TEST_ROOT=/home/janezp/.local/share/uv/python/cpython-3.12.15-linux-x86_64-gnu, SLAIF_NATIVE_TEST_PYTHON=python3.12, SLAIF_NATIVE_TEST_PACKAGES=/tmp/raggedized-root-native-setup-b-6cd8bebe0a/packages: .venv/bin/python3.14 -m pytest tests/integration -k <named node> --basetemp=<private 0700> -q: 1 passed, exit 0, each case once. Cached app interpreter .venv/bin/python 3.14.4. Mock/live: fully synthetic — the owner case exercises the real fixture/PreparationOwner/launch-argument path with /dev/null device pins and asserts refusal on close before handoff completes; the rowfit case runs the real journey (cached synthetic tokenizers generated by the trusted python3.12 backend), real ingestion/publish/build and the real producer rowfit refusal before dispatch. No real GPU/model/rights/Ready touched. No claim about this report's future push/CI.

## Documentation impact

No README/STATUS/TESTING/governance accounting change: test-setup repair only. The collision: both N modules imported the journey module first, whose module-level sys.path.insert(0, tests/unit) made the immediately following bare `from test_gpu_worker_launch import _prepared_fixture` bind the UNIT copy; later collection of tests/integration/test_gpu_worker_launch.py then failed the import-file mismatch (Root archived log; remote run 43283406324, both product jobs). A broader explicit local PYTHONPATH previously masked module identity by putting both test directories on sys.path before collection; the ordinary pytest prepend layout used here does not. The two import reorders bind the integration module before any journey side effect; the journey's global path behavior and all other bytes stay unchanged. Report within 8,192 UTF-8 bytes.

## DHA and boundaries

Order Decision: NONE; no consequential candidate; no CRIT append. No source/vector/rights/Ready/model/GPU grant; no snapshot/parity/CLI integration; no main merge, no 008, no tag/deploy/release, no nested agents, no other consumer, no FIFO reread/replay, no model/profile/client change. Preserved: human Qwen/A100 profile/auth, all prior immutable orders/reports/Root records, the O one-unit correction, both L exceptions, M/K, all other N21 bytes, pyproject, dependencies, law, CRITICAL, inert gateway/capture drafts.

## Limitations and remaining work

PARTIAL: whole 007 remains PARTIAL; actual BGE UNRUN/UNQUALIFIED; the integrated corpus pipeline is inert synthetic software — no real BGE execution, no FP16 qualification, no physical drain, no snapshot publication. Report-head CI PENDING/UNOBSERVED at publication; this report does not certify its future push/CI. PR 9 remains OPEN, auto-merge off; Root alone reviews, accepts and advances.
