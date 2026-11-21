# OAP Work Order — 009-l

Status: FINAL
Identifier: 009-l
PR mode: AMEND_EXISTING_PR
Branch: oap/009-evaluation-baseline
Base commit: 3f8b4eb08c4213b2ea11561e722263c40fa75c1e
PR number: 11
Expected active: 009-k
Provenance: H standing full-MVP development; E exact current-head run44017736685 product jobs OVERSIZE128 from unbounded pytest parameter IDs; I Root full product logs/source/closed-AST findings review; A honest complete bounded verification, no weakening inputs or resource limits
Architecture SHA256: 4b41905396a3838269fd6cf372614cd23cb2c3b6a37be09f29ed752803c0983a
Governance SHA256: 24cec23235e3defc5f55bab4690298191d5a233d35dd9bf20b0afb4b3925f922

FINAL after Root current-head reconciliation 2026-11-17T04:43:34.277201+00:00: original009k normal04:40:35/report5891Bad156b09 verified; wrapper4085012 exited; actualpane30 completed and quiescent04:42; remote uniquePR11OPEN/head3f8b/main5a7, reviews0/threads0/noautomerge, clean canonicalbranch/active009k/source governance identities verified. Root audit/009-k-resolution.json records CONTINUE_NOT_ACCEPTED; no merge/release. This source is activated only by original atomic publish+one control.

## Objective

Give fifteen exact parametrized tests explicit short case IDs so verbose diagnostics do not serialize large synthetic payloads into node names. Preserve every fixture value/expression, test body, function name, argument name, parameter count and order. Same numeric009/PR11. No supervisor/output-limit increase or suite narrowing. No product behavior fix or completion claim.

## Dependencies and current state

009k local report3f8b4eb0 soleparent implementation21c3fa66 soleparent transcriptabd577f9, exact five approved blobs and report5891B SHA256 ad156b09a430d312cafccd69961445e450dbc0951c013788319d8da812e4d9ec independently verified clean. Report snapshot freshCI pending is immutable; Root separate terminal review supersedes that timing statement. Current run44017736685/run134/attempt1: all3 OAP jobs SUCCESS; product3.12 job133819608038 and3.14 job133819608377 FAILURE, 78steps64success/2failure/12skipped. Logs are now usable; both2455collected, first native-record refusal passes; next verbose IDs serialize65537B header then huge chunks/receipts; supervisor raw16843391B exceeds16MiB after5.62/5.97s, OVERSIZE128. Observed current failure is not proof of earlier20minute cancellations/137 cause. No automatic retry. Root evidence audit/009-k-ci-terminal/Root-terminal-review.json with complete decoded logs and exact transport-LF precision.

Read only this full order, /home/janezp/codex-supervision/slaif-raggedized-helper/workorders/009-l-root-records.json SHA256 1a00815865cfb946bfae1a65330a7b9032137a37ddc929109f67feb0ab0fb67c + /home/janezp/codex-supervision/slaif-raggedized-helper/workorders/009-l-decorators.txt (15-call line-exact projection), Root terminal review and relevant final docs paragraphs. Full source file identities in index, semantic body reads not needed for keyword-only edit. Source AST scan read116 test modules without executing/importing; it is incomplete for dynamic ID creation. Root excluded nested lambda/dict/DTO literals because pytest does not directly render those as huge scalar IDs. Do not expand scope from residual scan or broad searches. Parser implementation peer and merged008 query ICA are separate, not integration authority.

## Allowed paths and scope

Existing test files below: ONLY add ids= keyword to the named existing pytest.mark.parametrize call, with literal ordered tuple/list of human-readable ASCII case names length1..48 matching case count and unique within call. Labels must be descriptive/content-free, lowercase letters/digits/hyphens, not payload/credential content. No callback/hash/repr/helper/hook or dynamic ID logic. All other AST must remain identical after removing exactly those new ids keywords. Preserve file formatting except locally needed keyword lines. No imports/new tests/refactors/pytest configuration or selection changes.

- tests/unit/test_bundle_native_records.py :: test_refusal :: SHA256 9265f4033caca5159b527afdd76fb6ff1fe31a343030213066f38ea7be21e7ac :: decorator lines [5, 17]
- tests/unit/test_bundle_pdf_records.py :: test_bad_json_tree :: SHA256 84a2fe319b2a1b674f8ae3b66496468bbb0e16db0870ae30ec8c06c090f4bbca :: decorator lines [32, 43]
- tests/unit/test_cpu_embedding_session.py :: test_late_invalid_preflight_no_worker_or_forward :: SHA256 bad8d8d5a22afb13849a91b65cd51a8c335f5d00145fde00debbcf015b2ca549 :: decorator lines [62, 63]
- tests/unit/test_derived_store.py :: test_json_complexity_and_unicode_limits :: SHA256 209dc75c7ea18c12bc36c297b72e2c76826de55ab7fee778a6df9a166309d0be :: decorator lines [339, 348]
- tests/unit/test_embedding_batch_store.py :: test_bad_syntax_before_io :: SHA256 8efee30c265604db3bf8b62f1262a512db28b5992cc5541050aa647c19c75cc9 :: decorator lines [72, 74]
- tests/unit/test_embedding_space.py :: test_definition_refused :: SHA256 4910c5b8b50491a1750d3d9fddb1bfcfe14e45c2ac009535348ed41e11c8165d :: decorator lines [62, 75]
- tests/unit/test_embedding_tokenizer.py :: test_malformed_response :: SHA256 ca6dadb7a7bf5c83edac7dc4cb04754bcb6e411915f5fdd20e6537679647b517 :: decorator lines [92, 94]
- tests/unit/test_gpu_device_lease.py :: test_preflight_without_io :: SHA256 1e29e3b54392dd038cecce705f0d6d359e83e2b63816eb25b0a0411222a52b99 :: decorator lines [29, 34]
- tests/unit/test_ingestion_profile.py :: test_invalid_raw :: SHA256 d14cd674fd7f19da4f7027a2746821f99d57c44ef6a75aa0512a6db807b932aa :: decorator lines [73, 76]
- tests/unit/test_owned_gpu_worker.py :: test_control_rejects_missing_duplicate_and_oversize :: SHA256 d96fac12b41960e91935443ffa203dc4696384af0127bf87e7c893b8f528297b :: decorator lines [98, 101]
- tests/unit/test_query_embedding.py :: test_raw_refusal_before_dispatch :: SHA256 c9805376ac4573655cb88f37efe64ef6df81e9b0e079e26e70140da1dc2eb77a :: decorator lines [29, 30]
- tests/unit/test_raw_hybrid_search.py :: test_invalid_before_source_or_engines :: SHA256 48010b7445c130c2e10361f229aff3ff5fc4f528999e3edb1a48ec9f10a78cd9 :: decorator lines [19, 25]
- tests/unit/test_raw_snapshot_query.py :: test_bad_question_before_policy :: SHA256 cd7c959d7b067756dce7c8a04b09f8111e261d32821d65509e65936c045f3e08 :: decorator lines [351, 352]
- tests/unit/test_source_bound_stage_loss.py :: test_payload_preflight_refuses_before_source :: SHA256 b6b10890ef8697e47d5b493a5fecbf914144f5124dcc0945f0c43f26e7d0e41a :: decorator lines [1584, 1585]
- tests/unit/test_tokenizer_session.py :: test_malformed_response_closes_worker :: SHA256 92120f50b5c7ee0449c09cdaa21e8a7b08637d91565dbc39db553022846f07be :: decorator lines [44, 50]

Additionally current009l-only factual sections in docs/evaluation.md and STATUS.md (combined delta <=6000B), exact Root order copied unchanged to oap/orders/009-l-bounded-pytest-ids.md, active009l, exact Root-authored /home/janezp/codex-supervision/slaif-raggedized-helper/workorders/009-l-root-records.json copied unchanged to oap/reviews/009-l-root-records.json and /home/janezp/codex-supervision/slaif-raggedized-helper/workorders/009-l-prior-resolution.json copied unchanged to oap/reviews/009-l-prior-resolution.json, and one canonical report oap/reports/009-l-bounded-pytest-ids.md. Do not author Root acceptance/resolution/CRIT entries or modify old reports/orders. No other tracked paths.

## Non-goals

No src/, supervisor/test_ci_unit_diagnostics.py/workflow/dependency/setup/native fixture changes. Do not raise4MiB/16MiB/180s/20minute limits, hide failures, filter tests, use -q/-k, skip/xfail, change assertions/inputs, reduce parameter counts, change numeric objective or integrate parser/publisher. No new checkout/codex-work sibling, new PR, release/deploy or credentials/services. Existing live hardware/auth/data/license/MVP gates remain open.

## Acceptance criteria

1. Exact original009k response normal/remote report/unique PR11/current main5a7/reviews+threads/CI and clean3f8b reviewed by Root before activation; old wrapper absent, original receipts preserved, no FIFO replay.
2. Exactly fifteen intended parametrize calls gain explicit unique bounded ASCII literal IDs. Same case vectors, bodies, imports, names, decorators other than ids, assertions/count/order. A static AST differential stripping only these new ids yields exact preimage AST for every file; 15calls/15files, total case count unchanged. Labels fit all criteria. No fake execution evidence.
3. All supervisor/workflow/core bytes unchanged; current full-unit test invocation/order/matrices/downstream required checks unchanged. New labels alter verbose names only; documented compatibility impact is display-node-ID change, not test-set change. CI should still collect2455 current-unit cases; any mismatch STOP, not an adjusted expected number.
4. Root independently reviews exact patch/15 AST identities/label vectors/docs/topology before implementation/report/push; no local product/native collection/testing/setup by implication. A later exact verification decision is required for any actual process outside ordinary Git/hash/text/AST inspection. Fresh report-head full CI is the actual whole-unit run. No failed-CI retry or repetition hidden.
5. Honest new report and docs retain old current failure, earlier unproven causes, Root19 local synthetic pass scope and all open gates. Missing/skipped/failed current jobs remain not green. DHA NONE. No development merge before every current required job/step succeeds and Root independent full acceptance.

## Verification and negative evidence

Static initially: read-only hash/Git/diff/text/AST-shape checks only; never eval/import test code, execute collection, fixture/native/model/GPU or install env. Verify labels do not contain payload and each literal tuple count matches exact literal case list; verify unknown/dynamic fixture expressions remain byte-identical. No new implementation-mirroring test. Root independent AST equivalence is meaningful invariant for this metadata-only fix; actual whole product suite remains hosted CI. If missing context/dependency/tool/mismatch/helper refusal, preserve precise regular blocker and await Root replan; no silent retry or scan expansion. After static patch write <=6000B precommit-review-request.json under audit/009-l-check with exact file hashes/diff path/label census/read ledger; STOP for Root review.

## Documentation

Append concise current009l evidence, expected display-only behavior, real currentCI failure and next-run pending. Never rewrite history or claim original timeout cause solved. Keep whole009 PARTIAL, real representative baseline NOT_RUN; current-principal/policy/encoder/data+rights/operator/CLI/parser/publisher/raw4096-row ceiling/hardware/visual/security/license/mergedICA/MVP/release gates remain open. Human illustration20kCHUNKS not20kdocuments. No measured physical/aggregate resource qualification from synthetic tests.

## Runtime and protected resources

Prospective96KiB semantic allowance INCLUDING own/repeats/helper/listing/output; use compact15decorator projection (~8KiB), full source identities/hash I/O separate. Read only relevant last current docs ranges, not whole large books/docs/history/worktrees. No tokens-to-bytes certificate or budget reset/refund; preserve prior uncertainty/overruns. Preserve current canonical branch/context unless Root actual fresh startup, human Qwen/profile/auth and all other panes. No nested agents. Helpers own sole FIFO readers; read regular receipts only. Root original009l control once after FINAL+active atomic publication. Separate helper owns sole control reader and fresh CODING wake; no coder FIFO read. Native bounded goal follows verified initial read.

## Deferred human adjudication

- Decision: NONE

## Publication and report

Root precommit gate mandatory. Once separately authorized, CODING owns Git: transcript exact ordered Root bytes then exact implementation, one report-only SELF commit and one normal fast-forward report-head push to existing PR11/branch; no intermediate push/force/automerge/tag/deploy. Report target3000-4500B soft6000/hard8192, original log hashes/current implementation/SELF/PR/order/15test identity index/negative evidence, static-vs-actual check distinction, freshCI pending, DHA NONE/all open gates. Original respond009l once under sole wrapper only after actual remote verification, then quiesce. Never read FIFO, replay original009k or invent report publication/cause claims.

Strongest counterargument: changing fifteen tests to repair diagnostic output is wider than one observed failure. Root selected only fifteen direct scalar literal parameter declarations whose static size can produce large verbose IDs, excluding three nested container/callback false positives; metadata-only AST equivalence preserves inputs/assertions and avoids predictable next oversized names without increasing limits or masking failures. Dynamic ID completeness remains unproven; fresh full CI still required. This is D0 routine reversible test-display metadata, not D1 or human gate acceptance.

Startup discipline: read exact current active/order/full compact index/projection once. Do not run find/recursive ls, inspect helper implementations, huge logs or past transcripts. Root supplied exact protocol commands and prior resolution. Hash-only whole-file I/O is distinct from shown semantic text. Account for own outputs, save early notes and hard-stop before allowance exhaustion; prior overruns do not justify another. After static patch + concise precommit request, stop for Root, not speculative next work.
