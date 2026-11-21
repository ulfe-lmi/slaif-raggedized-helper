# OAP Coding Report — 009-h

Identifier: 009-h
Result: PARTIAL
Repository: ulfe-lmi/slaif-raggedized-helper
PR number: 11
Branch: oap/009-evaluation-baseline
Base branch: main
Round base commit: 857355abbcfc4f5e322377f2bbee1388bafafc56
PR main base: 5a7b41cc512cf883b5b2cb92d87554b4d24e685b
Transcript commit: b1aafae98c615d679966c56638d43a988162e4c2
Order SHA256: 8d6850f69dad892297dc02935f4af2364133556406fb029b014bf3a3c2084255
Root index SHA256: 6981d295c0a26c390f107aac2ccd9571b188d55133fe87ad27848e8bfebff40c
Program SHA256 (unchanged): 84aceffc09ec7e53fcf96913ad0cb409616b31223d71915e60fbd750300b9b90
Runner SHA256 (unchanged): d9f1b0e8f748be9c5b32b6e6d45e8228ace43b397517a41e6187638d4c296faf
Implementation checkpoint (pre-amend, preserved, unpublished): d78aad9535b077299e45eea52facadb098c60b91, ref checkpoint/009-h-implementation-d78aad9
Implementation head SHA: d8a43fb69466f6bbee1f1737c0dc08505eca1b96
Report publication commit: SELF

## Work and scope

Order 009-h (FINAL, AMEND_EXISTING_PR) on PR 11 at round base 857355ab, the 009-g report head whose hosted CI FAILED (run 43931502904): the confirmed one-character constructor correction in the 009-g broad-session origin-metadata regression plus two current docs; same 009 continuation; PARTIAL whole 009. Transcript b1aafae (sole parent 857355ab): exactly 5 paths — unchanged FINAL order, active 009-h+LF, TWO exact Root records (3,143 B) plus exact 749 B index, all byte-verified. Implementation d8a43fb (sole parent b1aafae): exactly 3 paths — tests/unit/test_evaluation_program.py (085f0cea…/24,446 B to 59f093b4…/24,445 B), docs/evaluation.md, STATUS.md. Program/runner byte-exact; 009-g report aefda76c…/8,180 B unchanged. Coding performed NO local test/lint/format/import/collect/setup/native/model execution and made no duplicate check; Root independently froze, decided, ran and reviewed the ordered 104-unit check (below). Root's full three-path diff review of pre-amend d78aad9 fit source/test/104PASS/gates with two tiny doc-precision findings; docs-only amend d8a43fb, no retest. One report-head push follows; no reset/clean/stash/force-push, no cherry-pick/merge.

## The correction

Root CI resolution (oap/reviews/009-h-prior-resolution.json): product 3.12 job 133524822329 FAILED in the regression's test-local fake_stat (line 96) — os.stat_result(*values) expands ten fields into ten positional arguments (TypeError); pytest error rendering re-entered the same scoped Path.stat monkeypatch (INTERNALERROR); no complete pass/fail summary. Product 3.14 job 133524822987: one F then exit 137 before any complete traceback/summary; cause UNPROVEN, not equated with the 3.12 defect, no OOM claim. Three OAP jobs SUCCESS; 78 required steps 64/2/12; integration SKIPPED, not green. Correction: the single unique byte substitution os.stat_result(values) — postimage 24,445 B 59f093b4… exact; all 50 default nodes (44+6) and every other byte unchanged; no added tests, skip/xfail/filter, sys.path/sys.modules patching or fake packages. Root stdlib value witness (oap/reviews/009-h-stat-result-witness.json): expanded ten fields TYPE_ERROR, single-sequence st_size 3,145,728; not product test or CI acceptance.

## NEW bounded verification (Root-owned, attributed)

Root independently froze/decided/ran one direct pytest child over the two full unit files under the specified caps (CPU 20 s / AS 1 GiB / wall 120 s / core 0 / file 16 MiB / affinity 0 / five thread variables 1; private fresh 0700 /tmp): 104/104 PASSED (54 runner + 50 program, including all six new provenance regressions and four actual origin entry points), no skip/xfail/xpass; all 79 frozen input identities rechecked unchanged post-run; waited-children CPU 7.725588 s user / 0.094994 s system, parent-observed wall 7.952863 s, waited-children high-water 87,292 KiB (absolute Linux high-water, not a delta). Attribution: Root proposal 52f4fe9c…, decision 19:29:13.683334Z, result 0fb613bb…, log beb63602…/11,326 B, result review 19:30:24.722453Z. The coder's product-check launcher was NOT RUN (preserved unexecuted, v1/v2 plus Root-archived preimages); the static AST inventory was generated without product imports (56 files / 731,417 B lower bound, corrected per Root review) and supplied the Root check input set; Root owned the actual 104-unit process. Development-unit evidence only — not full-suite, CI, source-proof, runtime or baseline qualification.

## Acceptance evidence

1. Reconciled: unique open non-draft PR 11 (head 857355ab = round base; base main 5a7b41cc); remote active 009-g = expected; local at exact base, only authorized activation dirties; order byte-identical to strategic workorder; index/records verified; failed run 43931502904 at head; 009-g report immutable.
2. Transcript b1aafae: exactly 5 paths, sole parent exact base. Implementation d8a43fb: exactly 3 paths, sole parent transcript; report first parent d8a43fb; no unrelated dirty adoption.
3. Static checks (coding side): pre/post test hashes exact per order; git diff exactly one line / one character; AST parse OK; 50-node census unchanged; program/runner/009-g report byte-exact at implementation head; the post-review amend changed only the two docs (test blob re-verified 59f093b4…).
4. Root gate sequence satisfied: unit process only under Root's exact decision; Root result review preceded implementation commit and report; full log independently read by Root; zero coding-side invocations, no duplicate check, no old-run retry.
5. Docs state the exact 009-g failure, confirmed 3.12 defect, UNPROVEN 3.14 cause, the NEW Root-attributed bounded result with the NOT_RUN-launcher distinction, old 98 focused units tied to old test bytes 593a3be6… (program/runner the same exact bytes across 009-f/g/h), regression intent not a pass, full new-head CI PENDING, real baseline NOT RUN, all gates open.

## Verification (coding side)

Static Git/read/hash/AST/JSON identity checks only (git fetch/ls-remote/rev-parse/diff/show, sha256sum, wc, ast.parse, json.load, gh); no local product execution; no new environment/download/credential/service/corpus access. Semantic read ledger (256 KiB allowance, repeated/own-verification reads, author-reported conservative bound, no material unknowns): compact read set ~36,100; order+activation+goal 14,034; manifest 8,683; records+index 3,892; five strategic reviews 10,570; Root decision+result 2,679; reference frozen lane ~31,200; 009-g report 8,180; test partials+own outputs ~12,000; docs ~10,500; venv ~4,500; pyproject 2,025; git/gh/sha ~15,000; other ~3,000 (all B). Total ~162,300 B ≈ 158 KiB, within the allowance.

## Documentation impact

docs/evaluation.md: new "009-h stat-fixture constructor correction" section. STATUS.md: current slice 009-h + round record. Only the two docs plus the ordered test file changed; no report rewrite.

## DHA and boundaries

Decision: NONE (no CRITICAL append; register untouched). Preserved: immutable prior reports/reviews/checkpoints, retained failure evidence, Root private scratch (RETAINED_NO_DESTRUCTIVE_CLEANUP), source worktrees, gateway/services, human Qwen3.8-27B/A100 Q8/xhigh model/profile/auth, other panes/worktrees. No merge/auto-merge/tag/release/deploy; PR 11 remains open; no nested agents; no FIFO read/replay; no second consumer; no model/profile change.

## Limitations and remaining work

PARTIAL whole 009: focused 104 units do not cover the whole default product/integration 3.12/3.14 suite; the new-head full complete hosted CI is PENDING at publication — no result certified, no old-run reuse, no future CI certificate; missing/skipped/pending/cancelled/failed is not green; Root independently reviews exact new source/report/CI/threads before acceptance. Real baseline NOT RUN; operator/current-policy/qualified-encoder/data/rights/CLI/plan/publisher/native-OS/20k/hardware/visual/security/license/merged-ICA/MVP/release gates remain open; no 010 activation or merge from this correction. This report cannot certify its own push or future checks.
