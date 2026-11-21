# OAP Coding Report — 009-k

Identifier: 009-k
Result: PARTIAL
Repository: ulfe-lmi/slaif-raggedized-helper
PR number: 11
Branch: oap/009-evaluation-baseline
Round base commit: cc51b9a9a3eb478b3812bb3295459172bc5882b7
Transcript commit: abd577f9ea7b24ef6eeddde48e0699baab7245a5
Order SHA256: 3165d88d78665aa08a770f022e49d8d334d6e3eb57d942f0f61e766e49fd72e9
Workflow postimage SHA256: 29a44dd6f5d36d6035478c469d8b3c666fed8c25fe6c2b36ae2ac4e57c887bc4
Source SHA256: 3e15bf1c2e3707de12365ffb6ec73fd24b180c9e7ea023b0817d853c04ab3681
Test SHA256: e4f348a12defe4b4996ef553c33c544c297acf17b4f1a0c7cca5363804c6ab65
Docs SHA256: 03c1a9cc62ef9a2172830324735b35012347746bdf60ec92dd87c264592aa7c5 (docs/evaluation.md); b2022ba3fa9654cd8ca824c848cb17e54d1106b12f17ed1d8749ab83b3f7f534 (STATUS.md)
Implementation head SHA: 21c3fa6644b0243c076bc062756c2cc2c7e625bf
Report publication commit: SELF

## Scope

009-k (FINAL) at base cc51b9a (009-j report head = remote PR head). Owned unit-diagnostics supervisor: a bounded stdlib-only helper plus default-discovered unittest run by the Product step under /usr/bin/time -v; diagnostic-only, no acceptance. Transcript abd577f (sole parent cc51b9a): exact order/active/resolution/index, byte-verified. Implementation 21c3fa6 (sole parent abd577f): exactly the five approved postimages (helper 48,746 B 3e15bf1c…; test 38,303 B e4f348a1…; docs 84,221 B 03c1a9cc…; STATUS 112,910 B b2022ba3…; workflow 14,186 B 29a44dd6… byte-identical v1 postimage; 180 s/10 s child bounds, both matrix legs, 20-minute job limit, downstream gates unchanged). One report-head push; no reset/stash/force, no intermediate push, no merge.

## Diagnostic change

Product step command only: `test -x /usr/bin/time` + `PYTHONUNBUFFERED=1 /usr/bin/time -v python3 oap/bin/ci_unit_diagnostics.py` (fixed, no arguments). One short stdlib child owned under bounded supervision: 180 s deadline; TERM then KILL after 10 s on the identity-verified owned group; bounded 5 s post-kill/post-drain windows; 4 MiB labeled display cap (4096-char segments); honest nonzero 124-132; exact child exit/signal preservation (no 128 addition); bounded exclusive 0600 status/summary records, run record never overwritten; raw 16 MiB log always preserved. On refusal forwarded_bytes = queued/attempted display bytes, not guaranteed channel-delivered; raw log stays distinct from the bounded display and summary-phase record. No selector/skip; no production rlimit added; no resource-limit increase.

## Evidence

Root-owned actual check (not a coding-owned run): Root's stdlib-only check parent ran the complete 19 default-discovered methods in the owning process: 19/19 PASS; actual 14 constructor attempts = 13 returned/owned children + 1 failed Popen constructor/exec attempt; 0 grandchildren; max 1 concurrent; all reaped in supervised teardown; no Root rescue; 20/20 post/current hashes matched. Local Python 3.14.4 stdlib only; full log 2,948 B sha256 1ca4be4ec4e367a67a633120ed6f7d17e958a3ddf4e7efa2c9673f2ca87c7279 (preserved). Amended per-process limits only (CPU 20 / AS 512 MiB / FSIZE 32 MiB / NOFILE 256 / CORE 0 / affinity 0 / alarm 90; rescue limit 5 s unused): not an aggregate-CPU/RAM, OS-blocking, external-SIGKILL, adoption or escaped-descendant theorem. Retained prior failure (immutable): V3 17-case attempt 16 PASS / 1 FAIL (t11; log b60807561943df885b95d60bc46659886a0032cec9e923156080207502cfc8cd); per-case values unobserved, old cause NOT proven - the new deterministic near-cap oracle + honest-bounded real-child contract is what passes (no invented old result). Frozen-V2 peer K20-K22 findings differentially resolved by Root current-byte review + actual V5 regressions; peer did not review V5; not a merged ICA. CI: cc51b9a CI 43978029330 CANCELLED (20 m 0 s, cause UNPROVEN, output-ownership hypothesis only); fresh head CI PENDING/NOT_YET_RUN - first actual 009-k command invocation; no green/cause/baseline/whole-MVP certificate follows.

## Acceptance evidence

1. PR 11 unique open/non-draft/unmerged (head = remote head = cc51b9a; main 5a7b41cc…; no auto-merge); only authorized dirties.
2. Implementation: exactly five approved postimages, sole parent transcript; hashes equal the Root-approved precommit postimages.
3. precommit-review-request.json (3,772 B 9f289042…) + docs-only diff preceded the commit; Root-precommit-publication-decision.json (04:24:41Z) approved the exact five postimages and one-push/original-respond.
4. Current 009-k docs/STATUS sections carry finite true evidence (all 8 precision items); census 19 methods / 14 attempts stays true.

## Verification

Static Git/read/hash/text identity only (git, sha256sum, wc, gh, diff); the one actual check ran under Root's parent, not coding. No local product/test/import/collect/lint/format/setup invocation; no old-CI retry; no new environment/download/credential access. 24 KiB publication ledger: author estimate under 15,000 B; model-token overhead UNMEASURED; not Root-certified.

## DHA

Decision: NONE (register untouched). Preserved: immutable prior reports/reviews and failure evidence (V3 16/1 b6080756…; V5 19/19 1ca4be4e…), Root private lanes, human Qwen3.8-27B/A100 Q8/xhigh profile/auth. No merge/auto-merge/tag/release/deploy; PR 11 open; no gate FIFO read/replay; no second consumer; no model/profile change.

## Limitations

PARTIAL whole 009: fresh head CI is next and Root independently reviews every required job/step, output and review/thread; missing/skipped/pending/cancelled/blocked/failed is not green; no old-run retry. Real baseline NOT RUN; operator/current-policy/qualified-encoder/data/rights/CLI/plan/publisher/native-OS/20k/hardware/visual/security/license/merged-ICA/MVP/release gates remain open; no 010 activation or merge. No source-program/parser/publisher real-data qualification claimed; this report cannot certify its own push or future checks.
