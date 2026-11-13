# OAP Work Order — 007-p

Status: FINAL
Identifier: 007-p
PR mode: AMEND_EXISTING_PR
Branch: oap/007-embedding-pipeline
Base commit: c50213fbbd246adb8d6f89cac601239491974deb
PR number: 9
Expected active: 007-o
Provenance: H full-MVP development mandate; A A24/A40 original007 synthetic proof and normalCI; E O current report run43283406324 both product jobs fail integration collection; I Root exact source/cause review and normal integration collection reproduction
Architecture SHA256: 4b41905396a3838269fd6cf372614cd23cb2c3b6a37be09f29ed752803c0983a
Governance SHA256: 24cec23235e3defc5f55bab4690298191d5a233d35dd9bf20b0afb4b3925f922

## Objective

Correct ONLY fixture import order in the two new N integration modules so complete normal integration collection binds test_gpu_worker_launch to its INTEGRATION module before journey imports insert tests/unit in sys.path. Move `from test_gpu_worker_launch import _prepared_fixture` before `from test_embedding_batch_plan_composition import journey` in both modules. Preserve all tests/functions/fixtures/assertions and actual product behavior. This is an ordinary reversible test-setup repair, not a product/CI policy change.

## Dependencies and current state

O exact implementationd043956033d016e442e9a2fc4b86e65cf3b54d91/SELFc50213fbbd246adb8d6f89cac601239491974deb/report6304B SHAf6b4c208df817ad8b4387676be60036763422f18e0722012cb4ad3db25b4ea53, strict remote verified. Root clean unit node passes; author's full unit module23passes. Currentreport CI43283406324 completed:3OAPjobsSUCCESS, both product jobsFAIL at Integration test suite collection,66/78actualstepsSUCCESS,2failed,10skipped. Product unit suite nowSUCCESS both interpreters. New corpus executor imports journey, whose existing fixture module inserts unit directory into sys.path, then immediate generic test_gpu_worker_launch import chooses unit module; later integration collection rejects duplicate module name. Producer module has same new import order. Root complete integration collect-only with required CPUfixtureenv reproduces only this collision. Root earlier collect-only omitted CPUfixtureenv and had4extraKeyErrors; preserved, not isolated proof.

O normal receipt verified19:09:06 at exactc502 and failed-CI postpublication receipt independently reconciled. Root audit/007-o-review.json and audit/007-o-resolution-timing-event.json plus timing ledger recorded BEFORE this final order. UniquePR9 OPEN/non-draft/currentc502/main11badc/noauto-merge/no unresolved review or change-request gates, clean coding tree and sourcefit verified. Activation additionally requires actual prior goal finished/quiet and live original-helper preflight; publication precedes one signal. Whole007/fullMVP unresolved. Gateway prospectiveQ and capture prospectiveR remain inert until their own gates.

## Allowed paths and scope

FIRST exact FINAL order to oap/orders/007-p-integration-fixture-collection.md, active007-p+LF, indexed exact Root records from audit/007-p-root-records.json plus exact index to oap/reviews/007-p-root-records.json, transcript soleparentc502. THEN ONE implementation soleparenttranscript changing ONLY tests/integration/test_corpus_embedding_executor_composition.py and tests/integration/test_gpu_embedding_producer_composition.py. Both edits import-order only as specified. Exact final forecast audit/007-p-two-import-source-forecast.json: corpus file38234B expectedSHA06eec3c9143aded63deff7b9fc0f64f6c4b08bb85acddac1691f7d1d45060185; producer file70160B expectedSHAb491dc396870dbfa3774cff98f3e1c75c15395267a34af8234f60a0827ea6eaa. FIRST transcript includes all7 exact Root source/target/bytes/hash records in audit/007-p-root-records.json (22204B source records) and index SHA290792a8f465b50e87ccc6d638c26438b98ba283b51ad6d706719a6310a7964b. Do not edit these Root bytes. THEN immutable soleparent report-only oap/reports/007-p-integration-fixture-collection.md. No other tests/fixturehelper/CI/dependency/law/docs/production/source originals changes, no global path configuration, importlib/sys.modules workaround or default collection mode change. Existing journey's global path behavior stays unchanged; no broader helper extraction. Preserve O one-unit correction, both L exceptions, M/K, all other N21 bytes and prior immutable records.

## Non-goals

No rename/package/testloader/import-mode/pytest/CI/pin change; no production patch, gateway/capture/snapshot/recovery integration, broad replay of old suites locally, model/GPU/currentrights/Ready/hardware/release/mainmerge authority. No reset/stash/clean/switch/rebase/cherry-pick or unrelated amendment.

## Acceptance criteria

1. Both changed module ASTs are equivalent to their base except ordering of the same two import statements. Every test/fixture function/decorator/assertion/body and all product sources unchanged. Actual fixture still comes from normal integration module with its established uniquely named unit-helper loader; no fake success.
2. Run complete tests/integration --collect-only once with PYTHONPATH UNSET and required existing CPUv2 fixture env; ordinary pytest integration directory. Exit0, all modules collected, no import-file mismatch or missing setup. A small owned pytest observation plugin may record actual `sys.modules['test_gpu_worker_launch'].__file__` at collection finish and assert it resolves exactly tests/integration/test_gpu_worker_launch.py; plugin does not modify sys.path/import/collection. Record all actual counts; no count-only rerun or journey execution during collect-only proof.
3. Two focused actual checks, each own capped process under same default integration import layout and existing synthetic setup: test_gpu_launch_preparation_owner_composition.py::test_owner_handoff_preserves_existing_arguments; test_corpus_embedding_executor_composition.py::test_actual_whole_program_rowfit_refuses_before_dispatch. These verify real fixture/owner/boundary behavior after changed ordering. Do not replay old51/13/full integration journeys locally or historical heavy driver. Failure/extra actual cost requires Root plan; preserve stdout/commands/exit and failed attempts.
4. CPU30/AS1073741824/wall120 each, five OMP/OPENBLAS/MKL/RAYON/NUMEXPR threads1/no bytecode/private0700 direct/tmp basetemp. Existing native/tokenizer synthetic packages only where the two named cases require them; no installation/network/model/GPU/service/credential/privatecorpus. Ruff TWO changed files; AST/body-equivalence and scoped diff/source hashes. Report exact existing required setup paths/env, not fabricated model/qualification.
5. Truthful bare40 immutableSELF report<=8192B; strictremoteverify. Observe CURRENT REPORT fullCI ALL5jobs/EVERYactualstep (currently78). Every required stepSUCCESS mandatory for development acceptance; missing/skipped/pending/cancelled/failed notgreen. Normal full integration CI must actually execute original heavy drivers unchanged; historicalpassesnotreplacement. Individual waits<=60sec, no longbatchobserver/stdin-heredoc JSON misuse. On CIred preserve exacthead/run/jobs/failedstep/log+regularfailed-gate receipt and notifyRoot; no out-of-scope patch. Then ONE normal report-ready response permitted, explicitly failed gates/notacceptance. No intermediateheadCIwait.

## Verification and negative evidence

Root audit/007-o-current-report-CI-failed.log and audit/007-o-root-integration-collection-c502-with-fixtures.log preserve original collision. Passing complete collection with the ordinary path and explicit actual loaded-file observation is the repaired causal boundary. AST equivalence proves scope, not runtime success. The two named actual cases cover fixture/owner/rowfit behavior; currentfullCI remains controlling. Original first Root missing-env collect failure retained honestly, no repeated success counts.

## Documentation

Test-setup only, no README/STATUS/TESTING/governance accounting change. Report explains normal collection collision, why local explicit PYTHONPATH previously masked module identity, exact two import reorders and fixed current setup; no futurepush/CIclaim. Exact source/transitive readset scopes/hash/bytes, preserve all raw logs and attempts. Keep source originals and CRITICAL unchanged.

## Runtime and protected resources

Human Qwen3.8/A100Q8/xhigh/profile/auth preserved. Exact cached synthetic setup: SLAIF_NATIVE_TEST_ROOT=/home/janezp/.local/share/uv/python/cpython-3.12.15-linux-x86_64-gnu; SLAIF_NATIVE_TEST_PYTHON=python3.12; SLAIF_NATIVE_TEST_PACKAGES=/tmp/raggedized-root-native-setup-b-6cd8bebe0a/packages; SLAIF_GPU_TEST_ROOT=/tmp/raggedized-root-cpython312-portability; SLAIF_GPU_TEST_PACKAGES=/tmp/raggedized-root-gpu-fixture-c0e14e2c/packages; SLAIF_CPU_V2_TEST_ROOT=/tmp/raggedized-root-cpython312-portability; SLAIF_CPU_V2_TEST_PACKAGES=/tmp/raggedized-root-cpu-v2-portable-485fc687/packages. Collect-only needs CPU env for import; named actual owner/rowfit cases use GPU/native synthetic setup. Cached app .venv/bin/python3.14, PYTHONPATH UNSET in all named commands, all five thread variables1/no bytecode. Do not confuse runtime-root paths with permission for live GPU. One new context, original singlecontrol/response reader and original publication helpers; no oldFIFO read/replay/newconsumer/nestedagent/rawshellterminal. Shared finalorder precedes activation. Root owns exactsource/report/CI/reviews/acceptance and nextsuffix. CurrentfailedCI nevergrants merge/deploy/release.

## Deferred human adjudication

- Decision: NONE

## Publication and report

Oneexisting007PR9. TranscriptFIRST exactorder/active/indexedRootrecords+index; ONE two-import-order implementation; immutable soleparentSELF report-only. Push existingbranch, verify exactremote/head and reportancestry/bytes. CurrentCI handling percriterion5; ONE normalresponse means reportready, notacceptance. Finishboundedgoal andidle. No nextobjective/mainmerge/auto-merge/tag/deploy/release.
