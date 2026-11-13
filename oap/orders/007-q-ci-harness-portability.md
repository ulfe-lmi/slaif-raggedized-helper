# OAP Work Order — 007-q

Status: FINAL
Identifier: 007-q
PR mode: AMEND_EXISTING_PR
Branch: oap/007-embedding-pipeline
Base commit: 986ab7ef0fa44eced4027fd3aebe9a7bb14e3812
PR number: 9
Expected active: 007-p
Provenance: H activated full-MVP development; E current P report CI43293767218 failures; A original007 acceptance and required CI/resource contracts; I Root and opposite-agent exact forecast review
Architecture SHA256: 4b41905396a3838269fd6cf372614cd23cb2c3b6a37be09f29ed752803c0983a
Governance SHA256: 24cec23235e3defc5f55bab4690298191d5a233d35dd9bf20b0afb4b3925f922

## Objective

Repair two test-harness portability defects: the creator's min() fails when both inherited resource limits are unlimited; two corpus-program tests require a historical Git object missing from a shallow checkout. Preserve product behavior, historical comparison assertions, resource ceilings and CI policy. D0; DHA NONE.

## Dependencies and current state

P implementation cd6d22bd640b23298cdedc8970bed495aa982263, report SELF986ab7ef0fa44eced4027fd3aebe9a7bb14e3812, report SHA812963d01f718c68da4c00c6555074524f08e8b3319704ea631c6f8fbcd6c0b0. P's exact two import reorders repaired collection. CI43293767218 reached actual integration execution on both product legs: creator unlimited-limit TypeError and two historical Git-show failures. All five jobs/78 steps inspected: three OAP jobs succeeded; both product jobs failed; 66 successful, two failed, ten skipped steps. Red CI is not acceptance.

Normal response consumed20:10:32; strict remote verification20:11:06. Root audit/007-p-review.json rejects acceptance and requires this continuation; audit/007-p-resolution-timing-event.json and timing ledger precede this final order. Unique open non-draft PR9, branch/base/head/main11badc7782bed326995d400f5532b63399b91fbd, clean tree, auto-merge off and no unresolved review/change-request gates reconciled. Publication additionally requires actual prior goal finished/quiet and current helper/runtime/source checks. Whole007 and MVP remain PARTIAL.

## Allowed paths and scope

First commit the exact order to oap/orders/007-q-ci-harness-portability.md, active007-q+LF, all11 frozen Root records from audit/007-q-root-records.json (32262 source bytes), and the exact index to oap/reviews/007-q-root-records.json. Index SHAae15e7be2b12d56307e5026f6cc270c9f23cb761708e0b8a17c3a6d29d616493. Verify every source/target/size/SHA; never edit Root records. Transcript's sole parent is the round base.

Then ONE implementation changes exactly three files:

1. tests/integration/test_corpus_embedding_executor_composition.py: wrap the existing min arguments in one tuple, so min always receives a nonempty iterable containing the original ceiling and all finite inherited limits. Keep actual setrlimit, original CPU120/AS1073741824 creator ceilings, aggregate120-CPU accounting, all fixtures/assertions/import order and actual stop/resume journey unchanged.
2. tests/integration/test_corpus_embedding_program_composition.py: replace the unused subprocess import with hashlib; add the tiny tests-relative _base_representation_bytes() loader with mandatory size7049 and SHA681bf5145e980f77f67903c2fb5fd153f4694cf33344e208cd6181a5e65947a3 checks. Replace ONLY the two historical subprocess.check_output calls with this loader (retain the second decode). Preserve all historical-versus-current semantic/preflight/causal comparisons.
3. tests/fixtures/retrieval_representation_b0ca5a68.py.txt: exact7049 historical source bytes from b0ca5a68f8e55667ada5dd7523903b5585cbe0af:src/slaif_raggedized_helper/retrieval_representation.py, SHA681bf514 above. This inert fixture must not be reformatted.

Exact private forecasts are indexed in audit/007-q-ci-harness-portability-forecast.json: executor38236B SHA790e4e05063fb433d4d989a288a4c511db17a083166229c9eac0742955fac6b2; program16528B SHAd8e5700cbb3ac800446d2fc2d79535a1676952ee032c3a21f83a7056792530bc; fixture7049B SHA681bf514. Coding implements and independently validates the scope. Required formatting that changes these bytes needs Root reconciliation before commit. Root does not patch coding files.

## Non-goals

No product, CI, dependency, policy, law, CRITICAL, documentation/accounting or collection-layout change. No fetch/full-history workaround, skip, weaker assertion, alternate/current oracle, higher cap, new native profile, snapshot/gateway/capture/recovery integration or broad predecessor replay. Preserve P/O and all other N/M/K/L bytes and immutable reports. No reset/stash/clean/switch/rebase/cherry-pick or unrelated amendment. No model/GPU/service/private-corpus/credential/Ready/merge/release authority.

## Acceptance criteria

1. Exact three-file diff/fixture identity. AST comparison shows executor only tuple wrapping; program only the import/helper/two load-call substitutions. Every remaining test/fixture/assertion is preserved. No runtime Git/history/network dependency remains in those two controls.
2. Source-derived cheap admission matrix verifies both-unlimited, one/both finite and values below/above the existing ceiling; actual proposed setrlimit arguments never raise inherited finite caps. Mocks may replace resource get/set and stop at creator phase entry. Label this harness logic only. Root audit/007-q-root-cap-admission-proof.json already records ten original/fixed source cases; inspect proportionately, no repeat just for counts.
3. Exact historical fixture loads; missing/corrupt bytes refuse before compilation. No current module substituted as the old oracle. Root/peer static identity and AST proof are inputs, not actual journey proof.
4. Run complete tests/integration collect-only once with PYTHONPATH UNSET and required CPUv2 import environment. Then run each formerly failing program node ONCE in its own CPU30/AS1073741824/wall120 process: test_corpus_embedding_program_composition.py::test_actual_selected_sources and ::test_actual_remaining_char_preflight_matches_base. Use the same normal integration import layout; full tests/integration collection with unique -k selection is allowed for established bare helpers. No global path workaround. Capture exact command, selection, stdout, exit and resources; all five thread caps1, no bytecode and private0700 direct/tmp basetemp. Preserve failures and stop extra actual attempts pending Root's revised plan.
5. Ruff the two changed Python files; AST/scoped diff and exact fixture SHA. No local whole-suite/over128-chunk or heavy driver replay. A separate local heavy invocation requires an exact source/driver/budget decision; do not request it merely to count passes. Normal CURRENT REPORT CI must execute the entire unchanged creator stop/resume/reuse driver and all other collected tests under existing caps. Historical proof or mocked admission cannot replace that gate.
6. Immutable bare40 SELF report <=8192B, sole parent implementation, report-only diff; strict remote verification. Observe all five required jobs and every actual step (currently78) at CURRENT REPORT. Every required step must succeed; missing/skipped/pending/cancelled/failed is not green. On terminal red preserve exact head/run/jobs/failed steps/logs and a separate postpublication receipt, notify Root, make no unrelated patch, then send ONE original report-ready response explicitly recording failed gates/not acceptance. Each wait <=60 seconds; no intermediate-head CI wait or long observer batch.

## Verification and negative evidence

Root archived audit/007-p-current-report-CI-full.json and ...CI-failed.log contain the original actual failures. Source-derived matrix reproduces the original unlimited TypeError and verifies unchanged finite ceilings after the tuple correction; it changes no real OS limits or workers. Historical fixture byte equality, corrupt-fixture refusal and preservation of both live semantic comparisons address shallow-checkout portability. Root Ruff of the forecasts and opposite static review6d91 passed. Actual changed source and current complete CI still need independent review.

## Documentation

Test-harness repair only: no README/STATUS/TESTING/law accounting edits. Report why finite outer local caps/full Git history masked both failures; distinguish original failures, private forecast/static/mocked proof, current actual cases and current CI. Give measured source/readset paths/bytes/SHA and full or precise semantic ranges. No future-push/CI claims before observation. Whole007 actual BGE/precision/hardware/drain/license/full-MVP gates remain open.

## Runtime and protected resources

Preserve human Qwen3.8/A100Q8/xhigh/profile/auth and original single control/response helpers. App /home/janezp/codex-work/slaif-raggedized-helper/.venv/bin/python3.14; PYTHONPATH UNSET for default commands. Native fixture environment: SLAIF_NATIVE_TEST_ROOT=/home/janezp/.local/share/uv/python/cpython-3.12.15-linux-x86_64-gnu; SLAIF_NATIVE_TEST_PYTHON=python3.12; SLAIF_NATIVE_TEST_PACKAGES=/tmp/raggedized-root-native-setup-b-6cd8bebe0a/packages. CPU import pair: SLAIF_CPU_V2_TEST_ROOT=/tmp/raggedized-root-cpython312-portability; SLAIF_CPU_V2_TEST_PACKAGES=/tmp/raggedized-root-cpu-v2-portable-485fc687/packages. No GPU worker setup is needed for the two program cases.

Explicit OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 RAYON_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1; PYTHONDONTWRITEBYTECODE=1. Cached owned synthetic setup only; no installs/downloads/network/model/service/credential/private-corpus use. Native test execution is not actual model qualification. No other panes/nested agents/settings/goal reset or FIFO reread/replay.

## Deferred human adjudication

- Decision: NONE

## Publication and report

Transcript first, one three-file implementation, immutable sole-parent report-only SELF. Push existing branch, verify exact remote report/head. Follow criterion6 for current CI and the ONE original response. Finish the bounded goal and idle immediately after responding; Root's independent reconciliation covers closure, so no redundant postresponse audit loop. Root reviews/resolves/times before any continuation. GatewayR, captureS and explicit repairT remain inert; old Q/R/S draft names are historical aliases. No numeric jump/main merge/auto-merge/tag/deploy/release. Full-MVP mandate remains active.
