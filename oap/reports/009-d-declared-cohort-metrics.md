# OAP Coding Report — 009-d

Identifier: 009-d
Result: PARTIAL
Repository: ulfe-lmi/slaif-raggedized-helper
PR number: 11
Branch: oap/009-evaluation-baseline
Base branch: main
Round base commit: b87e264d5b138a7be5e89c3e8820a21697cc0aab
PR main base: 5a7b41cc512cf883b5b2cb92d87554b4d24e685b
Transcript commit: a7ee2b26708d96029c5fd541df9b214efd8e8338
Source SELF: b33da3811d82d651ad711bf5878f4f7159b5fcad
Source implementation: b15adafe0a99e557644d1b8fdb06f5089d72a359
Component index SHA256: 665c71182af5aa3008edf3c54df8619c9ad127fa763a0dc08fed38936891d656
Root index SHA256: a1d85c6a7d9a3ded4565e0a0de73fee3f9e48d6f213c66f5eebbb2dee07da0a4
Implementation head SHA: 157fb909e54cff43e2f8e2c60d55065470ed436d
Report publication commit: SELF

## Work and scope

Order 009-d (FINAL, AMEND_EXISTING_PR) on PR 11 at round base b87e264d
(009-c report head; CI 43420512522 all five jobs / all 78 steps
SUCCESS): static byte-exact transfer of the five reviewed pure
declared-cohort-metrics blobs plus three current docs; PARTIAL whole
009. Transcript a7ee2b26 (sole parent b87e264d): 13 paths — unchanged
FINAL order, active 009-d+LF (6 B), ten exact Root records (24,830 B,
including the component index) and the exact 3,221 B Root index.
Implementation 157fb909 (sole parent a7ee2b26): exactly 8 paths — the
five indexed NEW blobs (89,811 B: one production 32,800 B, one unit
22,772 B, three docs 34,239 B) copied by immutable source Git object
per oap/reviews/009-d-components.json, plus only docs/evaluation.md,
docs/benchmarks/raw-baseline.md and STATUS.md. No cherry-pick/merge/
ancestry; no product config/dependency/workflow/law/profile change; no
local runtime. This report commit changes only this report; one final
report-head push follows; no reset/clean/stash/rebase/force-push.

## Acceptance evidence

1. Reconciled: unique open non-draft PR 11 (head b87e264d, branch
   oap/009-evaluation-baseline, base main 5a7b41cc, zero review
   threads/reviews); local branch at exact base with only the two
   published activation paths dirty; both frozen indexes hash-verified
   (component 665c7118…d656, Root a1d85c6a…a4).
2. Exactly 22 round paths (21 excluding this report): 13 transcript +
   8 implementation. All ten Root records verified by size + SHA-256
   before/after copy and parse as JSON; all five NEW blobs verified
   against immutable source Git objects (blob ID + size + SHA-256)
   before/after copy and at implementation head; all five absent at
   base. Changed Python (2 files) parses via AST without import; copied
   oracle JSON parses. Canonical dataset unit SHA-256 b00aa74f…26ac and
   every other production/test/config/dependency/workflow/law byte
   untouched (diff = exactly the 21 paths).
3. Docs describe the TEN callable private module families and the pure
   supplied-geometry cohort aggregation as implemented (exact rationals,
   six prefix summaries, seven transition summaries over 1–256 cases,
   source-macro vs pooled denominators, complete-evidence coverage,
   OR/no-Gold undefined reasons, cap-loss partitions, chunk MRR/nDCG
   meaningfulness gate, supplied/unverified markers), distinguished from
   the still-ABSENT source-running orchestration, joined private split
   report and actual cohort composition proof; original full-256 scope
   preserved; no invented pilot.
4. Local proof attributed, not rerun: ONE approved current Ruff
   format/check and 33 complete unit tests PASS under Python 3.14
   (CPU 15 s/AS 1 GiB/wall 90 s/FSIZE 32 MiB/CPU 0, plain assertions,
   cache enabled) at source 743a8949…529e4 / unit 5a60130f…e78aa8; GNU
   1.81 s wall waited-process observation only; earlier 19/22 passes
   predate corrected semantics/metering; final API-only amendment did
   not rerun tests (source/test identical); other-author review is not
   whole-project ICA or an independent rerun.
5. Real raw baseline stays NOT RUN: missing approved human held-out
   data, corpus rights/current principal-policy authority and a
   qualified encoder named as gates; the 512-row diagnostic and 256-case
   admission are not 20k throughput or hardware qualification;
   hardware/visual/license/ICA/full-MVP gates retained; historical
   009-a/b/c and 008 evidence preserved; no 010 activation.
6. The single report-head push triggers the full unchanged five-job CI
   (all required steps; product unit/integration 3.12/3.14; three OAP
   jobs). At publication that new run is PENDING — no result certified;
   missing/skipped/pending/cancelled/failed is not green; no old-run
   reuse, no test deletion/skip/xfail, no workflow/dependency change.
   Root independently reviews the exact current source/report/head/
   threads/checks before development acceptance.

## Verification

Static Git/read/hash/AST/JSON identity verification only (git
cat-file/rev-parse/diff, sha256sum, ast.parse without import, json.load,
gh pr view/api). No local lint/collect/product/unit/integration/native/
model/scorer/store run, no setup/download, no runtime probe, GPU,
credentials, service or private-corpus access. Readset: root router,
coding constitution, ARCHITECTURE-for-agents.md, OAP-COMMUNICATION,
SECURITY.md, TESTING.md, the exact order, both frozen indexes, the ten
record sources, the five transferred files and the three docs. No
secrets or private data in this report.

## Documentation impact

docs/evaluation.md: title/intro (ten families), 009-d provenance,
cohort API reference, deadline bounds, absent-harness status (pure
implemented / source orchestration absent), unit-suite count.
docs/benchmarks/raw-baseline.md: current-state and provenance with the
009-d slice; methodology and NOT RUN unchanged. STATUS.md: current slice
009-d + round record; 009-a/b/c records preserved. No other docs.

## DHA and boundaries

Decision: NONE (no CRITICAL append; register untouched, zero entries).
Preserved: all immutable prior reports/reviews, failed 009-a CI
evidence, v1 stage-proof failure history, source originals/worktrees,
gateway/services, human Qwen3.8-27b/A100 Q8/xhigh model/profile/auth,
other panes/worktrees. No merge/auto-merge/tag/release/deploy; PR 11
remains open; no nested agents; no FIFO reread/replay; no second
consumer; no model/profile change.

## Limitations and remaining work

PARTIAL whole 009: the ABSENT source-running cohort pipeline, joined
private split report and actual cohort composition proof require
another bounded same-009 continuation (Root replan scopes a separate
source-runner lane at immutable b33da381 after normal quiet). Real
baseline NOT RUN; synthetic/supplied-geometry proof is not source or
qualification evidence. New-head CI pending; this report cannot certify
its own push or future checks.
