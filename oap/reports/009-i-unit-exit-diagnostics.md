# OAP Coding Report — 009-i

Identifier: 009-i
Result: PARTIAL
Repository: ulfe-lmi/slaif-raggedized-helper
PR number: 11
Branch: oap/009-evaluation-baseline
Base branch: main
Round base commit: 71172016968615365a59cf0341c699e105d38012
PR main base: 5a7b41cc512cf883b5b2cb92d87554b4d24e685b
Transcript commit: 0cdd00e39a355d2e96d07a309722c54e265842b7
Order SHA256: 545be27632c24c30e0cb985f35c2ccab0d0d176f6533afe8cd9d3b152d1fc163
Root index SHA256: 9e5c58e43a210f022f350cf4986fbb91deddd6aca8fc0f8c05b1990a035036b1
Workflow postimage SHA256: 556fa14da027d7bb489679c4e4774a5ae3079a539fafc30f80ca30d596946951
Implementation head SHA: 200fe4ca2bbc7754a0b21ff9c2cf93be15a1b8b9
Report publication commit: SELF

## Work and scope

009-i (FINAL, AMEND PR 11) at round base 7117201, the 009-h report head whose hosted CI run 43949914814 is terminal FAILURE: product 3.12 unit step exit 137 after 90% progress plus 52 dots, no failed-node traceback or completed summary. Diagnostic-only: evidence for the unexplained unit-process exit, not a product repair. Transcript 0cdd00e (sole parent 7117201): exactly 4 paths — unchanged FINAL order (9,144 B 545be276…), active 009-i+LF, exact prior Root resolution (3,286 B 81afc95b…) and exact Root index (447 B 9e5c58e4…), byte-verified. Implementation 200fe4c (sole parent 0cdd00e): exactly 3 paths — .github/workflows/oap.yml (14,095 B a26bda03… to 14,169 B 556fa14d…, single ordered run-block hunk), docs/evaluation.md (74,853 B a677f0a5…), STATUS.md (105,095 B a7a7f090…). One report-head push; no reset/clean/stash/force-push, no intermediate push, no merge.

## The diagnostic change

Only the Product test suite step changed: `uv run pytest tests/unit -q` became `test -x /usr/bin/time` plus `/usr/bin/time -v uv run pytest tests/unit -o addopts= -vv` (absent /usr/bin/time fails loudly; no install/pipeline/background/status-masking wrapper). pyproject addopts is `-q` alone, so `-o addopts=` and `-vv` change reporting only: verbose per-node results plus GNU time command resources/termination from one external parent. Full suite, node set/order, both 3.12/3.14 matrix legs, the 20-minute job limit and all downstream gates unchanged; every other workflow byte exact. GNU time output is an observation boundary — not process ancestry, measured allocation, additive/delta high-water, live-tree/cgroup accounting or OOM proof; a last printed node is localization, not proof of the kill cause.

## Evidence and boundaries

Previous failed CI (immutable): four jobs SUCCESS (three OAP legs plus product 3.14 job 133589341005, full unit/integration at 100%; retained DeprecationWarning not a failed gate), one FAILURE (product 3.12 job 133589340533); 78 required steps 71/1/6. Exit-137 cause UNPROVEN: no OOM, sender, culprit-node or constructor-recurrence claim. Root's 009-h 104/104 focused units are attributed in the committed 009-h report — prior bounded evidence, not a full-suite replacement or localization. New-head full CI PENDING at publication; no current or future green certificate.

## Acceptance evidence

1. PR 11 unique open/non-draft/unmerged (head = round base 7117201; main 5a7b41cc; no auto-merge); check_state ACTIVE, governance 24cec232… matching the order; tree held only authorized dirties.
2. Transcript: exactly 4 paths, sole parent exact base, byte-verified.
3. Implementation: exactly 3 paths, sole parent transcript; all three postimages equal the Root-approved hashes after both Root doc errata; no unrelated dirty adoption.
4. Gate satisfied: exact three-path diff (7,268 B 49d40713…) + review-request.json in strategic audit/009-i-check/ preceded the implementation commit; Root-review-decision.json (21:34:12Z) approved the exact postimages and completion.
5. Docs distinguish previous failed CI, Root 104-unit evidence and future new-head diagnostics; no green certificate, cause claim, baseline or whole-MVP acceptance.

## Verification (coding side)

Static Git/read/hash/text identity checks only (git fetch/rev-parse/diff/show, sha256sum, wc, gh, check_state); no local product/test/import/collect/lint/format/setup/native/model invocation, no old-CI retry, no new environment/download/credential/service/corpus access. Read ledger (256 KiB allowance): author estimate 227,000 B (~222 KiB) incl. pre-clarification strategic-tree reads retained per gate format; model-token overhead UNMEASURED; unknowns: whole-handoff read, chunk bounds, client overhead; not Root-certified.

## Documentation impact

docs/evaluation.md: new 009-i section; STATUS.md: slice 009-h to 009-i plus 009-i entry (Historical-007 indentation restored per Root erratum). Only the two docs and the ordered workflow run block changed; no report rewrite.

## DHA and boundaries

Decision: NONE (register untouched). Preserved: immutable prior reports/reviews/checkpoints, retained failure evidence, Root private lanes, PAR-009-* parallel worktrees/panes, gateway/services, human Qwen3.8-27B/A100 Q8/xhigh profile/auth, other panes/worktrees. No merge/auto-merge/tag/release/deploy; PR 11 open; no nested agents; no gate FIFO read/replay; no second consumer; no model/profile change.

## Limitations and remaining work

PARTIAL whole 009: no new evidence exists yet — it arrives only at new-head CI, which Root independently reviews (every required job/step, diagnostic output, review threads) before any remediation or acceptance; missing/skipped/pending/cancelled/failed is not green. Real baseline NOT RUN; operator/current-policy/qualified-encoder/data/rights/CLI/plan/publisher/native-OS/20k/hardware/visual/security/license/merged-ICA/MVP/release gates remain open; no 010 activation or merge. This report cannot certify its own push or future checks.
