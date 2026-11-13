# OAP Work Order — 007-o

Status: FINAL
Identifier: 007-o
PR mode: AMEND_EXISTING_PR
Branch: oap/007-embedding-pipeline
Base commit: 915dbc53bad866be70f730416806e500cdaa4dad
PR number: 9
Expected active: 007-n
Provenance: H activated full-MVP/development mandate; A original007 synthetic-proof/CI obligations A24/A40; E currentN reportCI43278270704 fails both productunitjobs at tests/unit/test_gpu_embedding_producer.py:198; I Root clean-environment actual reproduction and independent current-source review
Architecture SHA256: 4b41905396a3838269fd6cf372614cd23cb2c3b6a37be09f29ed752803c0983a
Governance SHA256: 24cec23235e3defc5f55bab4690298191d5a233d35dd9bf20b0afb4b3925f922

## Objective

Repair ONLY the unit fixture's cross-suite import so the actual post-COMPLETE journal interruption test runs with normal unit-suite isolation. Reuse the existing unit-scoped typed batch fixture from test_embedding_batch_store with count1, and derive the embedding-job seed from that SAME metadata/dependencies/rows/codec policy. This is an ordinary reversible test-setup choice. Keep the actual Journal/typed store, publish/commit-then-interrupt injection, original exception identity, COMPLETE reconciliation, verified output/ref/metadata and exact PENDING/CLAIMED/RUNNING/COMPLETE assertions. Do not replace this with a mock or weaken/skip it.

## Dependencies and current state

N exact implementation99249e7acf45309a641d481f4585227c22ed7775/transcript96e06a07d96f15cdad21885dc0e390fe69951535/immutableSELF915dbc53bad866be70f730416806e500cdaa4dad/report7176B SHA7a4a023e5b9c75d60ddbc1d62852133a6d634ca36f41bbfd5e945d20c0a65c23 and normalresponse18:20:31 are independently reconciled. Rootreview audit/007-n-review.json is NOT ACCEPTED: currentCI43278270704 has3/5jobs successful,2productjobs failed,64/78actualsteps successful,2failed,12skipped. Integration and later product checks were not run. Both failures are ModuleNotFoundError for integration-only test_embedding_job_journal_composition imported by a UNIT test. Root reproduction with PYTHONPATH unset fails identically, while broader local src:unit:integration setup masked it. No pipeline production bug demonstrated by this failure, no green CI or acceptance implied.

PR9 uniqueOPEN/non-draft/auto-mergeOFF, head915d/main11badc7782bed326995d400f5532b63399b91fbd unchanged, no unresolvedreviewthreads/change requests; coding tree clean. N source21/335687B,29Rootrecords,BOTH L exceptions/M10/K andgovernance aggregate49999 verified. Root51unit+2actualchecks passed only in their declared broader local setup; currentCI failure controls acceptance. Timing/review recorded before this corrective continuation. Existing gateway repair draft formerlyO and capture draft formerlyP remain INERT, resequenced later; do not integrate them now.

## Allowed paths and scope

FIRST transcript sole-parent base915d: copy this exact order to oap/orders/007-o-unit-fixture-CI-repair.md, active007-o+LF, all5 exact source/target/bytes/hash records from audit/007-o-root-records.json, plus that exact index to oap/reviews/007-o-root-records.json. Shared actual bytes available; copy unchanged, verify before commit. THEN ONE implementation sole-parent transcript changing ONLY tests/unit/test_gpu_embedding_producer.py. THEN immutable sole-parent report-only oap/reports/007-o-unit-fixture-CI-repair.md. No other product/test/helper/fixture/docs/CI/pins/dependency/law/source-original/ARCH/CRITICAL changes. Existing UNIT helper may be imported/read but stays unchanged. No global sys.path/PYTHONPATH change or integration fixture import by spec/path to hide the problem. No canonical production patch.

This one unit-file deviation from frozenN21 is an explicit canonical test-only correction; retain it in future selective integrations. Preserve all other N21 bytes, M10/K, BOTH L test-only exceptions and all previous immutable orders/reports/Rootrecords. No reset/clean/stash/switch/merge/cherry-pick/rebase or unrelated scope.

## Non-goals

No gateway/parity/snapshot integration, newnumericobjective, model/GPU/rights/currentpolicy/Ready/qualification, CI/workflow change, default test discovery/path broadening, additional helper extraction or release/mainmerge. Do not investigate unrelated old host full-unit failure by rerunning broad local suites.

## Acceptance criteria

1. Existing unit test no longer imports the integration directory. Its real typed one-row fixture and derived plan match each other; preserve actual publish/journal interruption/reconcile semantics and all substantive assertions. No monkeypatched whole journal/store/validator, skip/xfail or swallowed interrupt.
2. Run the formerly failing node with PYTHONPATH UNSET, current installed app interpreter, pytest ordinary unit-only layout. Assert actual pass, original post-commit KeyboardInterrupt identity, verified COMPLETE output and transition history. Then run ONLY its full unit module (expected23cases; report actual count) under same clean unit-layout conditions. No added integration path, no count-only rerun or old51/13 replay.
3. Each process separately CPU30/AS1GiB/wall120/five OMP/OPENBLAS/MKL/RAYON/NUMEXPR threads1/no bytecode/private0700basetemp; existing appNumPy and synthetic typed data only. No model/native-worker/GPU/driver/service/network/install/privatecorpus/credential activity. Ruff changed unit file, syntax AST/diff; unchanged production/law/CI/governance verified rather than unnecessary full local sweeps.
4. Exact current implementation/source/readset hashes/bytes and actual semantic scopes, raw commands/env/stdout/exit and every failed attempt preserved. Explain original failure and why broad local PYTHONPATH masked it. Test-only fix needs no product documentation or governance-accounting change; order/report describe it. Both local commands actually run once for distinct isolation/regression purposes; no passing counts-only retries.
5. After truthful bare40 SELF report publication and strict verify-report, inspect CURRENT REPORT CI ALL5jobs/EVERYactualstep (currently78). Development acceptance REQUIRES every one SUCCESS; missing/skipped/pending/cancelled/failed is not green. Do not wait on intermediateimplementationhead, batchlongpolls or use stdin/heredoc JSONpipes. Wait intervals<=60s, keep doing actual evidence review. If current CI fails, preserve exact run/head/job/step/log and notifyRoot promptly in regular failure record; do not patch outside scope or invent success. A normal report-ready response may then be sent with explicit FAILED-CI gate receipt so Root can issue the next bounded correction; it is NOT acceptance. On success record actual all-job/step proof before normal response. This response handling changes notification timing only, never the green development gate.

## Verification and negative evidence

Original failing Root witness audit/007-n-root-CI-unit-isolation-repro-915d.log and actual remote log audit/007-n-current-report-CI-failed.log are supplied evidence; do not rerun old failure merely to recount it. New setup must genuinely reach actual commit/interruption assertions under clean unit-only pytest. Full current GitHub CI must execute all normal tests without skips/changedworkflow, including the N freshproducer and complete-resume drivers under their original child limits. If further currentCI failures emerge, return concrete exact evidence forRoot continuation; no waiver/capraise or ad-hoc unrelated fix.

## Documentation

Immutable report<=8192UTF8bytes, concise: exact correction, current-head actual checks, preserved failure/setup evidence, test-only exception and incomplete qualification. No README/history append or TESTING/T16/manifest edit for this setup-only change. No future push/CI claims in immutable report; post-publication observation receipt records actual state separately.

## Runtime and protected resources

Human Qwen3.8/A100Q8/xhigh/profile/auth preserved. Native runtime configuration is not product permission. All code/test execution local synthetic app data; no real model/GPU/service/credential/corpus/network/install/otherpanes/nestedagents. One new round context and ONE control/response via original helpers. No oldFIFO read/replay/duplicateconsumer or terminal shell injection. Safe routine continuation inside fullMVPmandate, no new human permission needed.

## Deferred human adjudication

- Decision: NONE

## Publication and report

One existing007PR9. FIRST exact transcript/active/5Rootrecords+index; ONE single-unit-file implementation; bare40 SELF report-only. Push existingbranch, verify exact remote/head/SELF/source/transcript. Current fullCI as above; original ONE response signifies report ready, explicitly failed gates if any, never merge permission. Finish this bounded goal and idle; Root owns independent current-head review, acceptance and next work. No merge/auto-merge/tag/deploy/release/008 or old reported-round amendment.
