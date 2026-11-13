# OAP Coding Report — 007-u

Identifier: 007-u
Result: PARTIAL
Repository: ulfe-lmi/slaif-raggedized-helper
PR number: 9
Branch: oap/007-embedding-pipeline
Base branch: main
Round base commit: 491c570f7a4c3c4a8117e90504d60a688c61515f
PR main base: 11badc7782bed326995d400f5532b63399b91fbd
Transcript commit: 12afc0a1e5bfa67a74efc490d94b72fc97b67b48
Implementation head SHA: e92ec948e8eaac1413fc3473a3f6065905ad701f
Report publication commit: SELF

## Work and scope

Order 007-u (FINAL, DHA NONE) ran transcript-first. Transcript (sole parent = round base): exact final order (12,698 B a9aafea6...), active 007-u+LF, SIXTEEN frozen Root inputs (57,100 B) plus index (4,267 B e8f4d384...) per oap/reviews/007-u-root-records.json, all byte-exact verified; no Root bytes edited. Implementation (sole parent = transcript): exactly SIX paths — five byte-exact files from immutable source SELF 3fd1d9e per oap/reviews/007-u-components.json (5b014e9f..., 65,717 B; per-file sizes/SHAs in that index): ONE existing journal replacement (25,497 B 2dfd72c8..., all existing journal definitions preserved) + four NEW paths (unit/integration tests, API/design docs); plus ONLY the concise STATUS.md current-U paragraph. Added behavior: explicit locator-only repair of stale RUNNING materialization (contracts: copied API/design docs). Bounded software continuation: no production policy/gateway/CI/dependency change, no merge, no 008.

## Acceptance evidence

1. Five copied files byte-exact (re-verified after copy; blobs equal the indexed git blob IDs at 3fd1d9e); exactly six implementation paths; 19 transcript paths byte-verified pre-commit. Preservation: base-vs-tree diff = only the 25 ordered paths (19 transcript + 5 implementation + STATUS.md). The new locator enforces the exact canonical old RUNNING state/revision, distinct old owner, new live exclusive lease, full frozen plan/output validation, equal fresh provider epochs at both named stages and revision CAS; retains attempt/history/original start, refuses wall-clock rollback, rereads verified output post-commit, cooperative deadline never preempts nested operations.
2. Both processes: cached .venv/bin/python3.14 3.14.4 (binary SHA 52e0a13e...), pytest 8.4.2, argv `-m pytest -v <target> --basetemp=<fresh 0700> -p no:cacheprovider`, timeout 120 + prlimit --as=1073741824 --cpu=30, PYTHONPATH unset, no bytecode, five thread caps 1. P1 (ONE source-only process, target tests/unit/test_embedding_output_repair.py): 11 collected (forecast 11), 11 passed in 0.31 s, exit 0 (wall 0.76 s, max RSS 66,440 kB). P2 (ONE separate cached synthetic process, target ONLY ::test_positive + ::test_postcommit_deadline_preserves_complete): 3 collected (forecast 3), 3 passed in 0.62 s, exit 0 (wall 1.09 s, max RSS 67,764 kB). Raw stdout/stderr/resource/exit + identity/argv/env/caps at /tmp/raggedized-u-007/{p1-unit,p2-integration}/. Import closure reads no environment, so the order's seven SLAIF_* vars were unused. One earlier unit instantiation omitted the ordered thread caps (local runner defect) and exited 1 silently under the ordered 1 GiB AS cap on this 40-CPU host (uncapped math-thread-pool VA > cap — environment misconfiguration, not a test result; all ordered-environment processes passed.
3. ruff (full CI product scope): All checks passed; compileall (oap tests src) clean; AST diff vs base journal: no existing function changed/removed, exactly the three ordered additions. CI-style default collection (two separate collect-only processes, order's exact seven SLAIF_* vars, same caps): tests/unit 1,756/81 files, tests/integration 789/74 files, both exit 0, new modules recognized (11+13). check_state ACTIVE 007-u exit 0 (manifest 24cec232...); OAP scaffold 41 tests OK; raggedized --help exit 0.
4. This report validated pre-commit on actual bytes via oaplib.metadata and oaplib.commit_id: bare 40-hex implementation ID with no commentary, bare header IDs except SELF, no duplicate fields, below 8,192 B, identity/branch/PR/result correct, sole-parent report-only plan.
5. CURRENT sources at publication: header commit chain (implementation ← transcript ← round base); PR 9 OPEN/non-draft, MERGEABLE, auto-merge OFF, reviewDecision empty, remote main 11badc7782.... One push of this final report head; original strict verify-report, CURRENT all-check report-head CI and ONE normal response go to the separate post-publication receipt, not certified here.

## Verification

Mock/live: all local evidence synthetic/offline (synthetic fixed-epoch provider; owned temp journals/stores; sandboxed processes); no real model/GPU/device calls, installs, downloads or network. Counterargument: local nodes are synthetic paths only; the ENTIRE unchanged repair and T capture/reuse drivers (process lease, causal plan binding, six negatives, both postcommit phases) run only in current report CI (both Product jobs); historical proofs (3bea/cf0e/source fit) support selection, not U execution; synthetic success is not neural FP16/hardware/current-rights qualification. Current CI: PENDING/UNOBSERVED at publication.

## Documentation impact

ONLY the concise STATUS.md current-U paragraph plus the five exact copied component files (incl. API/design). No TESTING/law/governance/README edit; repair NOT_QUALIFIED and whole-007/BGE UNRUN/UNQUALIFIED gates preserved; T BLOCKED-epoch and S scoped-acceptance distinctions preserved.

## DHA and boundaries

Order Decision: NONE; no CRIT append; no candidate. Preserved: human Qwen3.8-27b/A100Q8 profile/auth, runtime/helper bytes, prior immutable orders/reports/Root records, borrowed fixture roots. No merge/reset/stash/clean/switch/rebase/cherry-pick/force-push; no nested agents, installs, downloads, credentials, SSH, gateway/model/GPU/service change, network exposure, 008 advance, tag, deploy or release.

## Limitations and remaining work

PARTIAL whole 007: scoped U integration executed (local 11/11 + 3/3), but the mandatory CURRENT report-head CI (all required jobs/actual steps; both drivers on both Product legs) is PENDING/UNOBSERVED at publication; terminal state recorded post-publication; terminal red retains exact head/run/job/step/logs + Root notification + one original report-ready response, no out-of-scope patch or false acceptance. Per source audit 8cd9, F3 remains the real open software gap; U is not yet evidence it is closed. Actual BGE/FP16/current-rights qualification, controller/drain, licenses, held-out quality, visual, 20k capacity, merged ICA, MVP gates open; no 008 advance, no merge.
