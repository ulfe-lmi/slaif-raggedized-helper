# OAP Work Order — 008-g

Status: FINAL
Identifier: 008-g
PR mode: AMEND_EXISTING_PR
Branch: oap/008-raw-hybrid-snapshots
Base commit: 5509c6baa963f06750bc09b425ebdd1f2d577db1
PR number: 10
Expected active: 008-f
Provenance: H full-MVP continuation mandate; E actual CI43383127224 both Product jobs fail pytest cache/nodeids write Errno27 after unit progress100%; A full unchanged CI/no skipped acceptance and bounded diagnostics; I Root source inspection of oversized locator parameter without explicit IDs
Architecture SHA256: 4b41905396a3838269fd6cf372614cd23cb2c3b6a37be09f29ed752803c0983a
Governance SHA256: 24cec23235e3defc5f55bab4690298191d5a233d35dd9bf20b0afb4b3925f922

## Objective

Bound the diagnostic IDs of completion-locator invalid-program tests without reducing their payloads or coverage. Preserve the failed008f report/run. Both Product jobs passed lint/syntax, then failed in pytest_sessionfinish/cacheprovider while writing cache/nodeids (OSError errno27). Unit progress reached100%, but no successful pytest terminal summary or integration result exists; later Product steps were SKIPPED. Three OAP jobs succeeded. Root review audit/008-f-failed-ci-reconciliation.json records this as failure, not acceptance.

## Dependencies and current state

Exact current5509 report-only head/0e866 implementation/c52d transcript, original normal receipt, source review and failure/timing are independently reconciled. The new test_bad_program_refused parameter list includes b"x"*16777217 without explicit pytest IDs. Default byte IDs can serialize the whole oversized payload into cache diagnostics. Existing helper-unit setup calls can leave an inherited RLIMIT_FSIZE, but its exact CI value/cause has NOT been measured; the interaction is an inference to verify, not an invented measurement. No product or CI cap may be raised to hide this failure.

## Allowed paths and scope

FIRST one transcript commit sole parent5509: exact order, active008-g+LF, THREE unchanged Root records from /home/janezp/codex-supervision/slaif-raggedized-helper/audit/008-g-root-records-FINAL.json plus that exact index at oap/reviews/008-g-root-records.json. Index1100B SHA256a2eb15960fb505bd862c87efe0c96ba1f2e0643e22d853b9c2049414d5d72cfd; three records3722B. Six transcript paths.

THEN one implementation with ONLY tests/unit/test_raw_snapshot_completion_locator.py, docs/ci-parameter-ids.md (new), docs/retrieval.md and STATUS.md =four paths. In the unit module change ONLY pytest.mark.parametrize for test_bad_program_refused to add six stable unique short IDs, e.g. empty, malformed-json, trailing-newline, mutable-bytes, bytes-subclass, oversized-program. Preserve all six actual argument expressions byte-for-byte, including b"x"*16777217, and every function body/assertion/other decorator/import/constant/test. No product code, helper limits, dependency/workflow/config/law/profile/old report or other test changes. Then one report-only sole-parent SELF. No branch merge/cherry-pick/reset/clean/stash/switch/rebase/force push.

## Non-goals

No cache-plugin disabling, cache clearing/retry workaround, skip/deselection/xfail, payload shrink, test removal, timeout or file-size cap increase, new model/native/store/scorer invocation, real data, protected service/GPU/credential/release/deployment action, merge by coding or new numeric scope. Do not repair unrelated inherited helper behavior without a concrete finding and Root replan.

## Acceptance criteria

1. Exact uniquePR10/base/main/order/active and three Root records/index. Only six new explicit parameter IDs alter test metadata; after removing that one ids keyword, AST must equal base exactly and original payload expressions/case cardinality remain identical. No suppressed error or changed product semantics.
2. Inspect the exact old parameter node-ID behavior in ONE bounded old-source collect-only process before editing. Preserve actual collected count, maximum/total node-ID lengths and cache-file/error outcome without printing giant IDs or payloads. Do not claim the exact original CI RLIMIT value was measured. Old collection under a deliberately small child file-size limit may fail at cache write; label expected diagnostic reproduction, not a pass.
3. After adding short IDs, ONE focused pytest process runs the ENTIRE unchanged completion-locator unit module with cache provider ENABLED under the same small child file-size limit. The real oversized negative argument must still be exercised; collected test count unchanged. All tests, pytest sessionfinish and cache write succeed, with bounded actual node IDs/cache bytes. This is a local diagnostic regression proof, not full CI acceptance or model evidence.
4. New short CI note describes actual failure, mechanism vs inference, exact local commands/caps/source identities/counts/cache bytes, old/new outcomes and preservation of test data. Update current STATUS/retrieval to record failed008f/laterSKIPPED and pending new-head CI, not overwrite immutable reports or old8d UNPROVEN evidence. Original008 four criteria/public014 gate separation and all real qualification/rights/quality/scale gates stay intact.
5. One final report-head push triggers the complete UNCHANGED five-job CI/allsteps/full unit+integration3.12+3.14. Missing/pending/skipped/cancelled/failed is not green. Root independently reviews exact head and all required jobs/steps before acceptance/merge. No old-run retry.

## Verification and negative evidence

Only two focused pytest processes authorized locally: ONE old collect-only and ONE final full locator-unit run, each CPU10s/AS1GiB/wall60/CPU0/file-size1MiB per disposable child, five thread vars OMP/OPENBLAS/MKL/RAYON/NUMEXPR=1, bytecode/plugin-autoload disabled except the normal built-in CACHE provider remains enabled. Use existing /tmp/slaif-pinned-query-setup-20261113/venv/bin/python, verifying executable/package metadata first; no setup/download/version probe or broad suite. Closed benign env PATH/HOME/LANG, exact repo src/tests-unit PYTHONPATH and private TMPDIR; retain literal argv/cwd/env/source/tool hashes/caps BEFORE each process, split stdout/stderr/GNUtime/exit AFTER. Each attempt uses a NEW owned0700 scratch, absent basetemp/cache child; never reuse/recreate/clean prior targets. Source hashes are checked immediately before invocation.

Suppress only giant terminal listing for the OLD collect using pytest's no:terminal reporter plus a tiny private in-memory plugin that prints ONLY count/max-ID-length/total-ID-length (no IDs/content). CACHE stays enabled, and no case is deselected. Explicitly place cache_dir under that process's new scratch so no prior cache can contaminate measurements; this changes storage location, not cache behavior. The same optional summary hook can report final new IDs. A small private launcher/probe may live under its fresh owned scratch or strategic lane evidence, not product code; save its exact bytes/hash and review its bounded behavior before invoking. No shell reset/cleanup, hidden filesystem operations, parent-limit mutation or extra subprocess. Local file-size limit is deliberately LOWERED in the child, never raised; hard limit applies to each file, not aggregate disk.

One final Ruff check on the changed unit file only, CPU5/AS512MiB/wall30/CPU0/five1 using existing0.17.4 binary SHA4ef33997b4bb7c5f141527e90b2da0abe918108362ca1b9825c4d13adce0e347. Static Git/hash/AST/scripts CPU5/AS256MiB/wall30. No extra formatter or semantic changes. Unexpected failure/timeout/missing tool/identity or cardinality mismatch -> preserve and regular Root blocker before retry/capraise/adaptation. No environment dumps or actual worker/framework/source/scorer activity.

## Documentation

Only the three allowed docs. Distinguish actual pytest failure from assertion failures (the logs do not show failed assertions) and incomplete/full CI. Local cache proof is synthetic owned test infrastructure, not original CI cap measurement. Keep concise current outcome and remaining gates; no invented benchmark, endpoint, license or readiness claim.

## Runtime and protected resources

Live authorization NONE. The explicitly bounded pure locator diagnostic is the only local runtime permission; no native/model/store/scorer/PDF/CPU-worker/framework fixtures, broad product suite, setup or service. Preserve Qwen/A100Q8/xhigh/profile/auth, all other panes/worktrees/source originals. No nested agents, FIFO reread/replay/duplicate reader, release/tag/deploy or merge. Root's coding activation remains standing delegated development, no new human permission needed for this reversible test-metadata repair.

## Deferred human adjudication

- Decision: NONE

## Publication and report

Six transcript +four implementation +one ownreport =eleven unique round paths including report/ten excluding. Target report<=6000B/hard8192, literal implementationSHA/SELF, Result PARTIAL whole008 until current CI/Root gate. Preserve old report/run/raw log, report both bounded old diagnostic and new full focused outcomes honestly, no future CI claim. Strict remote verification then ONE original normalresponse and finish goal idle. Root observes allchecks, resolves/times the round and chooses same008 continuation or guarded development merge; coding does not choose next scope.

Strongest counterargument: short IDs may not explain the original active file-size ceiling. Bound ID/cache measurements and real cache-enabled focused execution isolate the new metadata risk without waiving any resource or test. The full unchanged new-head CI must still establish the complete behavior; a further failure remains a real same-objective finding.
