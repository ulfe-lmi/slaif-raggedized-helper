# OAP Coding Report — 009-e

Identifier: 009-e
Result: PARTIAL
Repository: ulfe-lmi/slaif-raggedized-helper
PR number: 11
Branch: oap/009-evaluation-baseline
Base branch: main
Round base commit: 598d6dc6d8dd97f711859c1277a08e8bfb606956
PR main base: 5a7b41cc512cf883b5b2cb92d87554b4d24e685b
Transcript commit: f9b76d313828a6f2d98490f8f39022eb45f350ff
Source SELF (runner): 91f31182dae31a01d0f0dbf35b272c18ed08a2c8
Source implementation (runner): 3c92a59d9240826522a7152fc96d4973ec8b94c7
Source SELF (proof): 5ffef4c1f42fc8c01591218bfcbe115318094918
Source implementation (proof): 60b171379a826d97920378a59109d31869970387
Component index SHA256: b73448cfc0156d5846324ce5443352e7a413c75385d9fee170ca68626c55c8e6
Root index SHA256: 709edd08336790262c6615532a0e20aafdd4281943b071e92c18ecfde1030092
Implementation head SHA: 87f7daa15d24f157c0f774a944be7fb098ec4e31
Report publication commit: SELF

## Work and scope

Order 009-e (FINAL, AMEND_EXISTING_PR) on PR 11 at round base 598d6dc6 (009-d report head; CI 43429772054 all five jobs / all 78 steps SUCCESS): static byte-exact transfer of the reviewed source cohort runner plus three current docs; PARTIAL whole 009. Transcript f9b76d31 (sole parent 598d6dc6): 13 paths — unchanged FINAL order, active 009-e+LF (6 B), ten exact Root records (37,449 B, including the components index) and the exact 3,194 B Root index. Implementation 87f7daa1 (sole parent f9b76d31): exactly 12 paths — the nine indexed NEW blobs (167,455 B: runner SELF five, proof SELF four) copied by immutable source Git object per oap/reviews/009-e-components.json, plus only docs/evaluation.md, docs/benchmarks/raw-baseline.md and STATUS.md. No cherry-pick/merge/ancestry; no config/dependency/workflow/law/profile change; no local runtime. This report commit changes only this report; one final report-head push follows; no reset/clean/stash/rebase/force-push.

## Acceptance evidence

1. Reconciled: unique open non-draft PR 11 (head 598d6dc6, base main 5a7b41cc); local at exact base with only the two published activation paths dirty; both frozen indexes hash-verified (b73448cf…c55c8e6, 709edd08…1030092).
2. Exactly 26 round paths (25 excluding this report): 13 transcript + 12 implementation. All ten Root records verified by size + SHA-256 before/after copy and parse as JSON; all nine NEW blobs verified against immutable source Git objects (blob ID + size + SHA-256) before/after copy and at implementation head, all nine absent at base; copied Python (2) parses via AST without import; copied JSON (4) parses. Canonical dataset unit SHA-256 b00aa74f…3026ac and every other production/test/config/dependency/workflow/law byte untouched (diff = exactly the 26 paths).
3. Docs describe the ELEVEN private module families including source_cohort_runner.run_cohort (all-case admission, full dataset/all Gold bundles, per-case effective-authority intersection before producer, original authority at binder, borrowed old-generation pin, one aggregate only after complete success, joined private split report, linkable identities, intended/attempted/completed/refused/pending prefixes, no surviving-subset refusal, 1–256-case/512-Gold software bounds, FULL_ADMITTED_SPLIT versus DECLARED_SUBSET) and correct the three 009-d findings: lexical 4→5→6→7 edges; OR AMBIGUOUS_ALTERNATIVE_SOURCE_UNIVERSE versus the no-Gold NO_GOLD_REQUIREMENTS/NO_GOLD_SOURCES; pure 13-tuple/declared-field-insertion-order identity versus sorted-key JSON, distinct from the runner wrapper encoding; macro versus pooled denominators, complete-evidence coverage, undefined partitions, seven loss transitions and the MRR/nDCG relevance-mapping gate preserved.
4. Attributed, not rerun: corrected runner 96e69714…/unit 4d01ca5c… passed 54 controlled units plus focused Ruff in their source lane; ONE actual synthetic composition proof against exact driver 065b2cb4…/source/oracle e291137d…: 5 cases/4 selected, 6 selected/7 full Gold occurrences, three bundles per binder, four outer attempts, 7 producer/6 binder/1 aggregate, no surviving subset (success 5 pin/4/4/1; missing query zero delegates; changed space 4/3/2/0 + PRODUCER 4/3/2/1/1; closed pin zero delegates + PREFLIGHT 4/0/0/0/4); one generator exit 0, six captured wrappers deliberately closed/reaped 143 — not six zero exits nor whole-tree containment; observed pytest 59.29 s / launcher 62.39849 s / SELF 2.707422 + waited CHILDREN 58.910207 CPU s; sampled scratch 286,066 B/74 entries; first inventory and collection-guard failures retained, corrected checks passed; Root ten-case cleanup witness PASS once (coding author did not rerun).
5. Real raw baseline stays NOT RUN: missing approved human held-out data, corpus rights/current principal-policy authority, qualified encoder; synthetic declared held_out is not human held-out discipline or rights attestation; no domain quality, gateway/V100 co-residency, 20k, visual, license, merged ICA, full-MVP or human release gate closed; no 010 activation; 009-a/b/c/d and 008 evidence preserved.
6. The single report-head push triggers the full unchanged five-job CI (product unit/integration 3.12/3.14; three OAP jobs); at publication the new run is PENDING — no result certified; missing/skipped/pending/cancelled/failed is not green; no 598d reuse, no old-run retry, no test deletion/skip/xfail, no workflow/dependency edit; Root independently reviews exact current source/report/head/threads/checks before development acceptance.

## Verification

Static Git/read/hash/AST/JSON identity checks only (git cat-file/rev-parse/hash-object/diff/log, sha256sum, ast.parse without import, json.load, gh pr view/run list). No local format/lint/test/collect/setup/native/store/scorer/model execution, no new environments/downloads, no runtime probe, GPU, credentials, service or private-corpus access. Readset: root router, coding constitution, ARCHITECTURE-for-agents, OAP-COMMUNICATION, SECURITY, TESTING, the exact order, both frozen indexes, ten record sources, the nine transferred files with their contract/API/composition/proof docs, the three current docs, 009-d report. No secrets or private data.

## Documentation impact

docs/evaluation.md: eleven families, 009-e provenance, runner API reference, the three 009-d precision corrections, harness section now implemented software plus synthetic-proof status, unit count, deadline bounds. docs/benchmarks/raw-baseline.md: current state/provenance with 009-e; methodology and NOT RUN unchanged. STATUS.md: current slice 009-e plus round record; 009-a/b/c/d preserved. No other docs.

## DHA and boundaries

Decision: NONE (no CRITICAL append; register untouched). Preserved: all immutable prior reports/reviews, retained failure evidence, source originals/worktrees (source topology evidence only, not merged history), gateway/services, human Qwen3.8-27b/A100 Q8/xhigh model/profile/auth, other panes/worktrees. No merge/auto-merge/tag/release/deploy; PR 11 remains open; no nested agents; no FIFO reread/replay; no second consumer; no model/profile change.

## Limitations and remaining work

PARTIAL whole 009: the tiny synthetic source proof is weaker than the required representative real baseline and does not establish complete runtime/hardware/application qualification; full canonical CI predates these additions. A qualified real baseline (approved data/rights/current principal-policy authority/qualified encoder) remains separate required work; no original 009 closure or next numeric objective from this transfer. New-head CI pending; this report cannot certify its own push or future checks.
