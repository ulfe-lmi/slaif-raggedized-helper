# OAP Coding Report — 009-j

Identifier: 009-j
Result: PARTIAL
Repository: ulfe-lmi/slaif-raggedized-helper
PR number: 11
Branch: oap/009-evaluation-baseline
Round base commit: a7ad70b5e96995122afeae937ce8dd49d569131b
Transcript commit: 10a2e037fcb733646ad1c334343ceb1412e85ebc
Order SHA256: f4e28a800b544d50076221e8b2b4fabc3ee8636516f30e0010c505894017f0b6
Root index SHA256: 749c6d45a758e38fd04e3fff98cc9491d61c87b2353fa169144fab64e43cf53d
Workflow postimage SHA256: fc1ba2cd062ae5d314dc480bb2f2270834a7c22b9a2937fa9afc4b430101655d
Implementation head SHA: a0575b260b7055f7ea61460b3f4a2e78ce38b894
Report publication commit: SELF

## Scope

009-j (FINAL, AMEND PR 11) at round base a7ad70b, the 009-i report head (cancelled CI: below). Diagnostic-only: the unit step terminates and prints stack/status evidence before the enclosing job limit; no speculative repair or acceptance. Transcript 10a2e03 (sole parent a7ad70b): exactly 4 paths — unchanged FINAL order, active 009-j+LF, exact prior Root resolution 3,293 B f79d684f…, exact Root index 447 B, byte-verified. Implementation a0575b2 (sole parent 10a2e03): exactly 3 paths — workflow 556fa14d…→fc1ba2cd… (single ordered run-block substitution), docs/evaluation.md a677f0a5…→3c7a9e89…, STATUS.md a7a7f090…→bfcc10f8…. One report-head push; no reset/clean/stash/force-push, no intermediate push, no merge.

## Diagnostic change

The Product test suite step alone changed: the 009-i line became `test -x /usr/bin/timeout` plus `PYTHONUNBUFFERED=1 /usr/bin/time -v /usr/bin/timeout --signal=TERM --kill-after=10s 180s uv run pytest tests/unit -o addopts= -vv -o faulthandler_timeout=60`. Missing tools fail loudly; no install/pipeline/background/masking/continue-on-error/retry. A LOWERED 180-second unit-command deadline — no resource-limit increase: TERM on expiry (KILL after 10 s if necessary); any timeout/nonzero exit fails the step, never succeeds. Builtin `faulthandler_timeout=60` only requests a stack dump in a long test — not cancellation, cause proof or OS containment; `PYTHONUNBUFFERED=1` reduces lost progress. External time/timeout change ancestry/observation boundaries only (no live-tree accounting, descendant reap, escaped-child containment, exact allocation or OOM cause); a printed last node is localization only. No selector/filter/skip/xfail/split; full default node set/order, both matrix legs, 20-minute job limit and every downstream gate unchanged; all other workflow bytes exact. A >180 s command MAY be a legitimate slow case: preserve and replan from evidence — never cap-raise or suite-filter. Program 84aceffc…/runner d9f1…/unit 59f093b4… unchanged.

## Evidence

Prior CANCELLED CI (immutable): run 43962945486 terminal — three OAP jobs SUCCESS; product 3.12 (133634863960) and 3.14 (133634863970) CANCELLED by the unchanged 20-minute job limit; both check-runs annotated "exceeded the maximum execution time of 20m0s". Raw terminal API: 76 steps (60 SUCCESS, 2 unit steps in_progress, 14 pending), the two Complete job steps absent; inconsistency preserved, never promoted. Blocked node/cause UNPROVEN: connector logs 404 BlobNotFound; `gh --log` 0 bytes (not execution/success evidence); earlier 009-h exit-137 also UNPROVEN. Root's 009-h 104/104 focused units (committed 009-h report) remain prior bounded evidence, not full-CI substitution. New-head full CI PENDING at publication — first actual invocation of the revised command; no green/cause/baseline/whole-MVP certificate follows.

## Acceptance evidence

1. PR 11 unique open/non-draft/unmerged (head = round base = remote head a7ad70b; main 5a7b41cc512cf883b5b2cb92d87554b4d24e685b; no auto-merge); only authorized dirties.
2. Transcript: exactly 4 paths, sole parent exact base, byte-verified.
3. Implementation: exactly 3 paths, sole parent transcript; all three postimages equal the Root-approved hashes after the two exact doc precision substitutions; no unrelated dirty adoption.
4. Gate: exact three-path diff (8,905 B 5f8622e7…) + review-request.json in strategic audit/009-j-check/ preceded the implementation commit; Root-review-decision.json (22:55:08Z) approved exact postimages and completion; no second pre-commit gate.
5. Docs: new 009-j section (docs/evaluation.md) and STATUS entry (Root precision: no resource-limit increase; slow case MAY be legitimate); distinguish observed 20m0s cancellation, unknown node/cause, prior Root 104 evidence, future new-head CI; no green/baseline/whole-MVP certificate.

## Verification

Static Git/read/hash/text identity checks only (git, sha256sum, wc, gh, diff rc=0 vs reference); no local product/test/import/collect/lint/format/setup/native/model invocation, no old-CI retry, no new environment/download/credential/service/corpus access. Read ledger (192 KiB): author estimate ~85,000 B (~83 KiB) = ~76,000 B at gate submission plus ~9,000 B follow-up (Root decision, 009-i report ranges, verification outputs); model-token overhead UNMEASURED; unknowns: list sizes, output truncation, client overhead; not Root-certified.

## DHA

Decision: NONE (register untouched). Preserved: immutable prior reports/reviews/checkpoints and cancellation evidence, Root private lanes, PAR-* worktrees, gateway/services, human Qwen3.8-27B/A100 Q8/xhigh profile/auth, other panes. No merge/auto-merge/tag/release/deploy; PR 11 open; no nested agents; no gate FIFO read/replay; no second consumer; no model/profile change.

## Limitations

PARTIAL whole 009: no new evidence yet — new-head CI is the next, which Root independently reviews (every required job/step, diagnostic output, reviews/threads); missing/skipped/pending/cancelled/blocked/failed is not green; no old-run retry. Real baseline NOT RUN; operator/current-policy/qualified-encoder/data/rights/CLI/plan/publisher/native-OS/20k/hardware/visual/security/license/merged-ICA/MVP/release gates remain open; no 010 activation or merge. This report cannot certify its own push or future checks.
