# OAP Work Order — 007-r

Status: FINAL
Identifier: 007-r
PR mode: AMEND_EXISTING_PR
Branch: oap/007-embedding-pipeline
Base commit: 81159dd0d7278edbd07de904cf94a251a964a5aa
PR number: 9
Expected active: 007-q
Provenance: H active full-MVP development; A ARCH9/13 A20/A24/A34/A36; I merged-generator ICA003F1 and original Role-A oppositeF2, exact Role-B oppositea37d; E invalid assistant message roles accepted and latched role failure salvaged by later timeout text
Architecture SHA256: 4b41905396a3838269fd6cf372614cd23cb2c3b6a37be09f29ed752803c0983a
Governance SHA256: 24cec23235e3defc5f55bab4690298191d5a233d35dd9bf20b0afb4b3925f922

## Objective

Integrate the reviewed assistant-role admission and latched stream-error precedence repair. Normal provider assistant output, reasoning/refusal, cleanup/drain, finite retry and honest UNKNOWN_COMPLETION behavior stay intact. D0 known-bug remediation, DHA NONE. No protected gateway service or reference repository changes.

## Dependencies and current state

Q report 81159dd0d7278edbd07de904cf94a251a964a5aa, implementation a518cd3efb40d19bff5d5da2548b130ba7238ef2 and transcript5615057413a4a98ea40e5ea5141939677467623c independently reconciled; immutable8179B report SHA04b1594c2f2bf990b767c6c4a58f10ec84c38bdfe0b4bff4cc94257ffd8af964. Currentreport CI43303810176 all5jobs/78actualstepsSUCCESS, both product24/24 and all OAP10/10. Normalresponse21:04:54 verified and Rootaudit/007-q-review.json + timingledger recorded beforeR. Q accepts only portability; whole007/MVP stillPARTIAL. UniqueOPENnonDraftPR9/head811/main11badc7782bed326995d400f5532b63399b91fbd, auto-mergeOFF and no unresolvedreview/change requests reconciled; publication additionally rechecks exact remote/clean/quiet/runtime/sources.

## Allowed paths and scope

FIRST commit exact order oap/orders/007-r-gateway-role-remediation.md, active007-r+LF, all14 frozen Rootrecords from audit/007-r-root-records.json (39773B source bytes), and exact index SHAc2e05921b4c6ae1f52dbb00b4bfbf8843ca4a2c7b049557a8283612980e024a9 to oap/reviews/007-r-root-records.json. Verify eachsource/target/size/SHA byteexact; no Root-record edits. Soleparent roundbase811.

Then ONE implementation selectively copies EXACT8 files82739B indexed audit/007-r-gateway-role-components.json from immutable local candidate SELF77b4e8c911d558329bfbd2796bb9cc990d5f36e9 (implementation786bc25e8aca53c1f754ae64efb35813920d35b3). No wholesale merge/cherrypick or parallelorder/report copies. Existing replacement is ONLY src/slaif_raggedized_helper/model_clients/gateway.py. Seven new paths are tests/unit/test_gateway_message_role.py; tests/integration/test_gateway_message_role.py; tests/integration/test_gateway_role_error_precedence.py; docs/parallel/gateway-message-role-api.md; docs/parallel/gateway-message-role-design.md; docs/parallel/gateway-role-error-precedence-api.md; docs/parallel/gateway-role-error-precedence-design.md. Preserve exact authored source/test/design bytes; required format adaptation requires Root review BEFORE commit, never silently change the immutable candidate.

Additionally ONLY concise STATUS.md and TESTING.md edits (T16) document currentR integration and actualnewtest results, retaining all prior qualification/history distinctions. Totalimplementation10paths. Do not rewrite oldreports/Rootrecords, law/architecture/CRITICAL/README/deps/CI/othercode. STATUS currently names h in its top-line and carries laterhistory; update current slice toR and add a brief honest paragraph, no invented comprehensive coverage/accounting reset. T16 may append gateway role/precedence proof and priorQportability/currentallCI; preserve Hactual38+toy and BGEUNRUN/UNQUALIFIED distinctions. No copy of speculative downstream drafts.

## Non-goals

No runtime qualification, gateway deployment, source/heldout/visual evaluation, downstreamcapture/recovery integration, dependency/CI/law changes, or mainmerge/release. Keep all prior code and immutable reports outside exactscope unchanged.

## Acceptance criteria

1. Exact8component bytes/hash/blob and narrowexistinggateway diff: Rootaudit/007-r-gateway-current-Q-diff.patch proves28added/0removed lines versusQ. Helper _valid_message_role, collector, stream item-added/done boundaries enforce exact assistant role; malformed/missing/hostile role yields fixed invalid message role/no output text without echoing privatevalue. Reasoning entries, valid assistant refusal/multipleitems and literal untrusted outgoing usercontent unaffected.
2. All FIVE existing stream exception exits preserve already-latched structural state.error through existing _finish_stream before retry/timeout/refused/protocol/generic handling. No early break, cancellation/drain/cleanup/accounting/provider change. FAILED describes client semantic/protocol failure; NEVER imply upstream did not run, was cancelled/unbilled, or GPUvacancy. No-error predeliveryretry and ambiguous post-send partialtext/UNKNOWN_COMPLETION semantics stay intact.
3. Run newrole15units in own src-only process, then19newactualownedloopback cases from BOTH newintegration modules in separateprocess (unitandintegrationduplicatebasename mustnot be combined). Fullintegrationcollectionwithunique-k selection is allowed for established barehelpers. Explicit15role+4precedence cases, originalsamecap/source unchanged. Timeout guard causal control originalFAIL/noText -> guardwithdrawnUNKNOWNtext -> restoredFAIL/noText with healthyUNKNOWNtext; synthetic generic-after-realframes and controlledlateclose faults labelled controlled. Each positive/negative/control oneattempt/call assertions intact; no fabricated actualTCPreset/cancellation/hardware proof.
4. One separate process runs three existing regressions: tests/integration/test_gateway_generator.py::test_full_generator_stream_post_send_close_unknown_no_retry; ::test_pre_connect_retry_policy_is_finite; tests/integration/test_generator_transport.py::test_stream_close_after_send_is_safe_non_retryable. Use existing ordinary owned HTTP/SSEfixtures. These address healthy ambiguity/retry/drain; privacy regressions remain required in normal fullCI. No broad predecessor replay/count-only repeats. Caps CPU30/AS1073741824/wall120 EACH process, five threadvars1/no bytecode/private0700directtmp. Preserve unexpectedfailures and stop furtheractualattempts until Root concrete revisedplan; no blindretry/capraise/skips/fallback.
5. Focused Ruff on changed product/test Python and AST/diff, exactcandidate hashes and10paths. Retain actualcommands/counts/selection/stdout/exit/resources and measuredsource/readset full/ranges. Distinguish copied localpeer/Root proof from newcanonical actualruns. Unit15/newintegration19/regression3 are forecasts to verify, not counts to invent. Concisedocs reflect actualresult; no globalTESTINGbytebudget increase.
6. Immutablebare40SELF report<=8192B, soleparentimplementation, report-onlydiff, strictremoteverification on existingPR9. CURRENT REPORT all5requiredjobs and EVERYactualstepSUCCESS required. No intermediateheadCIwait, skip, capincrease, auto-merge or bypass. Terminalred: preserve exacthead/run/jobs/failedsteps/logs/postpublicreceipt, notifyRoot and ONE original report-readyresponse explicitlynotacceptance; no unrelatedpatch. Waits<=60seconds. Rootindependentlyreviews/resolves/timesbeforeS. AfterONEresponse finishboundedgoal andidle IMMEDIATELY; no redundantpostresponseaudits.

## Verification and negative evidence

Merged003ICA45fc identified roleuser acceptedTERMINAL; Role-A alone failedtimeoutcontrol, repaired inB. Root fullBdelta/source29finitechecks, author immutable7986Breport75f23fa55215c4ede63d4ff7311a07b11ed13a58207c368271fa41eb0c7839ff, oppositea37d and RootownrealwireUTF8onepredicate/restoration3.67s plushealthyretry reviewed. Localadmission is not canonicalacceptance. CurrentQsourcefit EXACT28additions and7newpathsabsence verified. Fresh actualcanonicaltests/currentCI required despite previousgreenQ. Strongestcounterargument: finitecontrolledfaults cannot prove all transport/race/cleanup paths or deployedgateway billing/vacancy; keep currentqualification/fullICA/livegates open.

## Documentation

Only the two named concise STATUS.md/TESTING.md updates described above, plus exact copied API/design files. Preserve NOTRUN/PARTIAL distinctions and original H evidence; report exact current results without inventing aggregate qualification.

## Runtime and protected resources

Preserve humanQwen3.8-27b/A100Q8/xhigh/profile/auth and originalsolecontrol/responsehelpers; no otherpanes/nestedagents. Cached .venv/bin/python3.14 app only, no downloads/installs/newnetwork/model/GPU/service/credential/realdata. Owned127.0.0.1HTTP/SSE withsynthetickeycanaries only. PYTHONPATH=src forunits; normalintegrationimportlayout (unsetPYTHONPATH/fullcollection-k asneeded), preserve allnative/CPUv2testenv when defaultcollectionrequiresfixtures. OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 RAYON_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1. Exactliveprotectedresource qualification remainsNOTRUN. No reset/stash/clean/switch/rebase/cherrypick, mutationofotherworktrees/referencegateway, modelsettings/goalauthoritychange or FIFO reread/replay. One007PR9, not newPR/numericjump.

CurrentsoftwarecaptureS/explicitrepairT remaininert. Original007actualBGE/precision/hardware/drain/currentrights/licenses/fullsourcecoverage and ICA gates stayopen. No sourceRecall/quality/baseline/Ready/MVP/pilot/mainmerge/tag/deploy/release authority from thisorder. Existingarchitecture governs; no newproducthumanowner/referral/contact behavior.

## Deferred human adjudication

- Decision: NONE

## Publication and report

Transcriptfirst, exact8components+2concisedocs implementation, report-onlySELF/push/strictverify, currentallCI/ONEoriginalresponse. Root alone owns developmentacceptance/latermerge andmustrecordreview/timingbeforecontinuation. Ordinarywithinmandate continuation requires no newhumanpermission; no protectedruntime actions authorized.
