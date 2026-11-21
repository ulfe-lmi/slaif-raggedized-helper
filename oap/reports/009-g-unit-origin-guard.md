# OAP Coding Report — 009-g

Identifier: 009-g
Result: PARTIAL
Repository: ulfe-lmi/slaif-raggedized-helper
PR number: 11
Branch: oap/009-evaluation-baseline
Base branch: main
Round base commit: 4e2d073ac297933501abea6d61bc3fa5437e8397
PR main base: 5a7b41cc512cf883b5b2cb92d87554b4d24e685b
Transcript commit: a60a04d7e3ca1f9075f2d4a6966467845adae0b5
Order SHA256: 476ca35c59d8e52d45cbb192426c5acfee6b50f106f9151fd42fd46ccabe062b
Root index SHA256: 7ab107cdd033cbb8857cff536ea86814a29dc9609eac2a4dbaf9623961ff9870
Program SHA256 (unchanged): 84aceffc09ec7e53fcf96913ad0cb409616b31223d71915e60fbd750300b9b90
Runner SHA256 (unchanged): d9f1b0e8f748be9c5b32b6e6d45e8228ace43b397517a41e6187638d4c296faf
Implementation checkpoint (Root-reviewed, preserved, unpublished): aecf3ac216967846fcb703710317ff1b3174ba92, ref checkpoint/009-g-implementation-aecf3ac
Implementation head SHA: 9b3622ce6ae7dc278292da2fc88a396e95a14e43
Report publication commit: SELF

## Work and scope

Order 009-g (FINAL, AMEND_EXISTING_PR) on PR 11 at round base 4e2d073a — the 009-f report head whose hosted CI FAILED (run 43921457809): bounded test-origin context repair, same 009 continuation; PARTIAL whole 009. Transcript a60a04d7 (sole parent 4e2d073a): 6 paths — unchanged FINAL order, active 009-g+LF (6 B), three exact Root records (4,558 B) + exact 1,069 B Root index, all byte-verified. Implementation 9b3622ce (sole parent a60a04d7): exactly 3 paths — tests/unit/test_evaluation_program.py (preimage 593a3be6…/20,405 B), docs/evaluation.md, STATUS.md. No product helper/API/module; program 84aceffc… and runner d9f1b0e8… verified byte-exact; 009-f report 96fcfaf3…/7,943 B unchanged. Root's exact-diff review of checkpoint aecf3ac (private record; FIX_WITHIN_CURRENT_SCOPE) required a corrected broad-session regression before report publication; the checkpoint is preserved at the ref above and the fix amended the unpublished implementation within the original three-path scope. One report-head push follows; no reset/clean/stash/force-push, no cherry-pick/merge.

## The repair

The failed run's four unit failures were exactly the four origin entry points (test_local_program_origins and its z/zz/zzz wrappers); every per-module local origin predicate passed, and the failure was the helper's misplaced final global assertion summing session-loaded product/test source-file extents (2,923,383 B) against the focused 2 MiB readset ceiling (2,445 PASS/4 FAIL per product leg; OAP jobs SUCCESS; integration SKIPPED, not green). That ceiling is the dynamic limit of the separately frozen focused check (parallel/evaluation-core proposal; 98 focused units passed on these same bytes) measuring that focused readset's extents — not actual bytes read, RSS, or the full default session. Per the Root D0 scope decision only the misplaced global sum was removed from the broad default suite; the strict provenance checks remain global and unchanged in meaning (real local __file__ resolving under assigned root/src for every loaded slaif_raggedized_helper package/module and root/tests/unit for every loaded test_ module; foreign, missing, non-file or resolved-escaping origins still fail; session start/end checks at all four entry points preserved). No cap raise, no skip/xfail/filter, no collection change, no sys.path/sys.modules manipulation, no fake package modules.

New regression intent (test-local verifier over bounded synthetic (name, __file__) metadata): focused legitimate local origins pass; the broader case is a distinct-file witness — two different real local unit files given bounded synthetic st_size metadata (3 MiB each via test-scoped Path.stat substitution, fixture-restored) so the deduplicated old-style sum over their unique source extents (6 MiB) exceeds the old 2 MiB sum while the revised check passes; foreign package origin, foreign test origin, missing __file__/non-file origin and resolved path escape fail with unswallowed negative sentinels. All 44 old nodes preserved; 6 added (AST census 50).

## Acceptance evidence

1. Reconciled: unique open non-draft PR 11 (head 4e2d073a = round base, base main 5a7b41cc); local at exact base with only the two published activation paths dirty; order 476ca35c…/12,078 B and index 7ab107cd…/1,069 B verified; three Root records size+SHA-256 verified, JSON-parsed; ancestry transcript→4e2d073a, implementation→a60a04d7, report→9b3622ce verified at commit time.
2. Only the three allowed paths changed vs transcript; program/runner/009-f report byte-exact at implementation head; prior report/review bytes unchanged.
3. Test-file static checks: AST parse OK; all lines ≤100 chars, no trailing whitespace (ruff E/F/W surface); census 34 functions / 50 nodes (44 preserved + 6 new); no skip/xfail/filter marks; verifier names defined; stat substitution fixture-scoped.
4. Docs state the exact 009-f CI failure (run 43921457809, jobs 133489544939/133489545017, 2,445/4 per leg, 2,923,383 B extents) and causal distinction (extent stat ≠ bytes read/RSS; frozen focused readset vs full default session); source implementation unchanged and source proof tied to its old exact bytes (98-unit focused check post-check hashes = 593a3be6…/84aceffc…/d9f1b0e8…); new regressions and new-head CI stated as NEW evidence; real baseline NOT RUN, all gates preserved; orphan bwrap on both failed legs before integration UNPROVEN, no worker fix; 009-f count clarification restated (17 = 16 NEW + one MODIFY; actual NEW groups 5+6+5, total groups 5+7+5); the two misspelled node IDs corrected.

## Verification

Static Git/read/hash/AST/JSON identity checks only (git fetch/ls-remote/rev-parse/cat-file/branch/diff/show, sha256sum, wc, ast.parse, json.load, gh). No local format/lint/test/collect/import/setup/native/model execution, no new environment/download, no runtime/GPU/credential/service/corpus access. Semantic read ledger (256 KiB allowance; repeated/own verification reads; author-reported conservative bound, no material unknowns): compact read set (router/constitution/architecture-for-agents/OAP-communication/security/testing) 50,000 B; order 12,078; root records 4,558 + index 1,069 + activation 855; focused check proposal 17,127 + decision 1,915 + result 874 + unit-log tail ≤2,000; 009-f report 7,943; test file all versions 20,405+23,846+24,446 (own output); docs/evaluation.md + STATUS.md read portions ≤39,000; workflow ≤1,500; pyproject 2,025; report template 569; 009-f components index 7,355; 009-f/009-e order headers ≤4,200; git show/log/diff ≤5,000; gh ≤2,000; Root implementation review ≤2,100; other shell ≤4,000. Total ≤234,865 B ≈ 229 KiB, within the allowance.

## Documentation impact

docs/evaluation.md: new "009-g unit origin-guard repair" section (exact failed run, causal distinction, preserved invariant, distinct-file broad-session regression with the synthetic stat seam, unchanged source bytes, new-vs-source evidence, gates, orphan, count clarification) + the two node-name corrections. STATUS.md: current slice 009-g + round record. No other docs; no report rewrite.

## DHA and boundaries

Decision: NONE (no CRITICAL append; register untouched). Preserved: immutable prior reports/reviews, retained failure evidence, checkpoint ref aecf3ac2…, source worktrees, gateway/services, human Qwen3.8-27B/A100 Q8/xhigh model/profile/auth, other panes/worktrees. No merge/auto-merge/tag/release/deploy; PR 11 remains open; no nested agents; no FIFO reread/replay; no second consumer; no model/profile change.

## Limitations and remaining work

PARTIAL whole 009: the old failed run (43921457809 on 4e2d073a) is preserved, distinct from the new current CI, PENDING at publication on the report head — no result certified, no old-run reuse, no future CI certificate; missing/skipped/pending/cancelled/failed is not green; Root independently reviews exact new source/report/CI/threads before acceptance. Real baseline NOT RUN; private publisher, named plan/evaluate CLI and current-policy verification remain separate required work; no 009 closure or next numeric objective from this repair. This report cannot certify its own push or future checks.
