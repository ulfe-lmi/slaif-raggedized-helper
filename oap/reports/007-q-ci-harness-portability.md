# OAP Coding Report — 007-q

Identifier: 007-q
Result: PARTIAL
Repository: ulfe-lmi/slaif-raggedized-helper
PR number: 9
Branch: oap/007-embedding-pipeline
Base branch: main
Round base commit: 986ab7ef0fa44eced4027fd3aebe9a7bb14e3812
PR main base: 11badc7782bed326995d400f5532b63399b91fbd
Transcript commit: 5615057413a4a98ea40e5ea5141939677467623c
Implementation head SHA: a518cd3efb40d19bff5d5da2548b130ba7238ef2
Report publication commit: SELF

## Work and scope

Order 007-q (FINAL, DHA NONE, AMEND_EXISTING_PR) ran transcript-first: transcript 56150574 (sole parent = round base): exact final order (10,290 B, SHA-256 22d70d888513cfdf98ec5b1691fc569ec086b1e2bf049145fea5b7c1302378dc), active `007-q`+LF, eleven exact Root portability records (32,262 B total) plus the exact index oap/reviews/007-q-root-records.json (2,795 B, SHA-256 ae15e7be2b12d56307e5026f6cc270c9f23cb761708e0b8a17c3a6d29d616493); all byte- and hash-verified pre-commit; no Root bytes edited. Implementation a518cd3e (sole parent = transcript): exactly THREE files: (1) tests/integration/test_corpus_embedding_executor_composition.py — the creator cap line now wraps its min arguments in one tuple so min always receives a nonempty iterable (original CPU120/AS1073741824 ceilings, actual setrlimit, aggregate 120-CPU accounting and the stop/resume journey unchanged); (2) tests/integration/test_corpus_embedding_program_composition.py — unused `subprocess` import replaced by `hashlib`; added the tiny tests-relative `_base_representation_bytes()` loader with mandatory size 7049 and SHA 681bf5145e980f77f67903c2fb5fd153f4694cf33344e208cd6181a5e65947a3 admission; replaced ONLY the two historical `subprocess.check_output(["git","show",...])` calls (second keeps `.decode()`); all historical-versus-current semantic/preflight/causal comparisons preserved; (3) new tests/fixtures/retrieval_representation_b0ca5a68.py.txt — exact 7049 B historical bytes of b0ca5a68f8e55667ada5dd7523903b5585cbe0af:src/slaif_raggedized_helper/retrieval_representation.py, byte-verified against the full local clone, not reformatted. Final bytes byte-exact to the ordered forecast: executor 38,236 B SHA-256 790e4e05063fb433d4d989a288a4c511db17a083166229c9eac0742955fac6b2; program 16,528 B SHA-256 d8e5700cbb3ac800446d2fc2d79535a1676952ee032c3a21f83a7056792530bc; fixture 7049 B SHA-256 681bf5145e980f77f67903c2fb5fd153f4694cf33344e208cd6181a5e65947a3. No product/CI/dependency/policy/law/docs/collection-layout change; no merge/reset/stash/clean/switch/rebase/cherry-pick; no nested agents.

## Acceptance evidence

1. Exact three-file diff: git status = two modified + one new fixture only. AST vs round base: executor — the sole differing top-level statement (test_actual_complete_resume_driver) holds the sole delta, the min Call args [Name ceiling, Starred(gen)] -> [Tuple(Name ceiling, Starred(same gen))]; program — sole deltas are the import swap (subprocess->hashlib), the added helper FunctionDef and exactly the two `base = ...` load-call substitutions (second retains the .decode() chain over the new call); every other statement AST-identical. No runtime Git/history/network dependency remains in the program module (no subprocess at all); the executor's remaining subprocess uses are the ordered creator journey only.
2. Cap admission (harness logic only, mocked, no OS limits changed, stop at creator phase entry): source-derived — the actual `if phase:` branch bytes were extracted from the base and fixed files and exec'd with mocked resource.get/setrlimit plus a sentinel phase: base both-unlimited reproduces the original `TypeError: 'int' object is not iterable` with zero setrlimit calls; fixed source admits all five inheritance patterns with exact proposed pairs — both unlimited (120,-1)/(1073741824,-1); soft-only (30,-1)/(700000000,-1); hard-only (90,90)/(900000000,900000000); finite below ceiling (30,60)/(700000000,900000000); above ceiling (200,300)->(120,300)/(1073741824,2000000000) — matching Root's archived ten-case proof values; the proposed pair never raises an inherited finite cap (hard unchanged, soft<=hard).
3. Fixture: the loader returns exactly the 7049 B historical bytes (byte-compared with the full-clone git object) which compile; a one-flipped-byte fixture is refused by the loader (AssertionError) before any compilation; a missing fixture is refused (FileNotFoundError) before compilation; the loaded old module differs from the current module (no substitution as the old oracle).
4. Actual runs, each once: (a) complete tests/integration --collect-only, exit 0: 752 items / 69 modules; (b) ::test_actual_selected_sources: 1 passed, exit 0, wall 7.56 s, max RSS 195,924 kB; (c) ::test_actual_remaining_char_preflight_matches_base: 1 passed, exit 0, wall 4.66 s, max RSS 195,468 kB. All under prlimit --as=1073741824 --cpu=30 timeout 120, env -u PYTHONPATH, PYTHONDONTWRITEBYTECODE=1, five thread caps 1, private 0700 direct/tmp basetemp, ordinary full-collection -k selection. No failures, so no extra actual attempts.
5. ruff 0.17.4 on the two changed Python files: All checks passed. AST/scoped diff and exact fixture SHA per criteria 1-3. No local whole-suite/over-128-chunk/heavy driver replay.
6. SELF report: this file; strict remote verification and CURRENT REPORT CI (all 5 required jobs, every actual step, currently 78) are observed post-push and recorded in a separate receipt; not certified here.

## Verification

Exact command (repo root, .venv/bin/python3.14 = 3.14.4, cached): `prlimit --as=1073741824 --cpu=30 timeout 120 env -u PYTHONPATH PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 RAYON_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 SLAIF_CPU_V2_TEST_ROOT=/tmp/raggedized-root-cpython312-portability SLAIF_CPU_V2_TEST_PACKAGES=/tmp/raggedized-root-cpu-v2-portable-485fc687/packages .venv/bin/python3.14 -m pytest tests/integration --collect-only -q --basetemp=<private 0700>` (collect-only) and the same plus SLAIF_NATIVE_TEST_ROOT=/home/janezp/.local/share/uv/python/cpython-3.12.15-linux-x86_64-gnu SLAIF_NATIVE_TEST_PYTHON=python3.12 SLAIF_NATIVE_TEST_PACKAGES=/tmp/raggedized-root-native-setup-b-6cd8bebe0a/packages and `-k` the unique node name -> criterion 4 results. Mock/live: criterion 2's matrix and the corrupt/missing fixture checks are mocked harness logic (no OS limits, no workers, sentinel stop); collect-only and the two nodes are actual synthetic executions (cached tokenizers; no real GPU/model/keys/network). Why masked: local/dev focused runs always spawn creator children under explicit finite prlimit caps, so the inherited (soft,hard) held a finite value and min() never received an empty iterable; the full local clone (379 commits) contains b0ca5a68 so `git show` worked locally — CI's shallow checkout lacks the object and its product-job children ran without an outer cap, surfacing both defects only in CI43293767218 (two product jobs failed; 66/2/10 passed/failed/skipped steps; logs frozen at oap/reviews/007-q-prior-CI-failure.json). Distinction: original = that CI; forecast/static/mocked = forecast bytes (Root Ruff, opposite static review 6d91), Root ten-case proof, mocked matrix; current actual = criteria 3-4; current CI = PENDING/UNOBSERVED at publication.

## Documentation impact

None — test-harness repair only, per the order (no README/STATUS/TESTING/law accounting edit).

## DHA and boundaries

Order Decision: NONE; no CRIT append; no candidate. Preserved: human Qwen3.8/A100 profile/auth, single control/response helpers, all prior immutable orders/reports/Root records, P/O and other N/M/K/L bytes, pyproject, dependencies, law, CRITICAL, inert gateway/capture/repair drafts. No merge performed; PR 9 OPEN, auto-merge off; no 008/tag/deploy/release/nested agents/other consumer.

## Limitations and remaining work

PARTIAL: report-head CI PENDING/UNOBSERVED at publication; no future push/CI claim (criterion 6 observed separately post-push). Whole 007 and full MVP remain PARTIAL: actual BGE UNRUN/UNQUALIFIED; the pipeline is inert synthetic software — no real BGE execution, FP16 qualification, drain, snapshot publication or license clearance.
