# OAP Coding Report — 009-c

Identifier: 009-c
Result: PARTIAL
Repository: ulfe-lmi/slaif-raggedized-helper
PR number: 11
Branch: oap/009-evaluation-baseline
Base branch: main
Round base commit: aba42a524bbd6a8f1958b4e6a20430aca7d31ccb
PR main base: 5a7b41cc512cf883b5b2cb92d87554b4d24e685b
Transcript commit: ac408fe094cb9c68cc77ab64c7b2429ece60ca43
Source SELF: e6b229b1eaea9cfb2be76a84a0d621b983644127
Component index SHA256: 6fbeb96c235695c32033a1a4ea031ae63d06495486fbdb5d512e40c5c633af91
Root index SHA256: 659d38568455be3ba5fa9729e8e5cfa677ec099c2b3b3e9acddb6c3e01a8f4f5
Implementation head SHA: 4727a202cad8a66264a594bd0600822915148800
Report publication commit: SELF

## Work and scope

Order 009-c (FINAL, AMEND_EXISTING_PR) on PR 11 at round base aba42a52
(009-b report head; CI 43405683635 five jobs / 78 steps SUCCESS):
selective byte-exact transfer of the reviewed source-backed stage
components into the existing 009 PR plus three current docs.
Transcript ac408fe0 (sole parent aba42a52): 14 paths — unchanged FINAL
order, active 009-c+LF (6 B), eleven exact Root records (52,832 B,
including the source component index) and the exact 3,512 B index.
Implementation 4727a202 (sole parent ac408fe0): exactly 25 paths — the
22 indexed blobs (395,115 B: three production 127,064 B, three unit
110,520 B, five integration 78,437 B, eleven docs 79,094 B) copied by
immutable Git object from source SELF e6b229b1 (implementation
748d08b4) per oap/reviews/009-c-components.json (21 NEW, one exact
existing raw-hybrid fixture MODIFY), plus only docs/evaluation.md,
docs/benchmarks/raw-baseline.md and STATUS.md. No cherry-pick/merge/ancestry; no
product/dep/workflow/config/law/profile change.
Before SELF, the trusted strategic pre-SELF doc-precision review (e890ae47…;
counts/bounds/RRF/CI wording only) applied to the three
permitted docs via ONE unpublished implementation amend (old object
d39c0f55 preserved; no product/test/source change). This report commit changes only this report; no
reset/clean/stash/rebase/force-push; one final report-head push
follows.

## Acceptance evidence

1. Reconciled: unique open non-draft PR 11 (head
   aba42a52, branch oap/009-evaluation-baseline, base main 5a7b41cc, no
   auto-merge, CLEAN); local branch at exact base with only the two
   published activation paths dirty; source worktree clean at e6b229b1;
   both frozen indexes hash-verified.
2. All 11 Root records verified by size + SHA-256; 12 NEW review
   targets absent at base. All 22 indexed blobs verified against
   immutable Git objects of e6b229b1 by blob ID + size + SHA-256 before
   and after copy; 21 NEW absent at base; MODIFY preimage verified at
   SHA-256 d4cdcb97… before overwrite; all 22 re-verified in
   implementation HEAD. Changed Python (11 files) parses; structured
   copied inputs (2 JSON) parse. Canonical portable dataset unit
   SHA-256 b00aa74f… and every other production/dep/workflow/law byte
   untouched; diff = exactly 14 + 25 scoped paths (39 excluding
   this report).
3. Docs distinguish the nine private module API families (six 009-a
   foundations + three 009-c stage components) and the actual per-case
   source-backed composition from the ABSENT callable cohort pipeline
   (frozen split selection, per-case producer traces/source binding,
   source Recall@20/60/full multi-source and stage-loss aggregation,
   total/defined/undefined/refused denominators, private report
   provenance) confirmed by independent coverage 2624 (Root adjudicated;
   oap/reviews/009-c-software-coverage-adjudication.json): no CLI
   invented; an operator loop is not harness software. Full eligible/
   matching source validation, captured old generation, declared source
   Recall@20/60 (undefined for no-Gold/OR alternatives), EXACTLY ten
   named stages (returned-index sets 3/7/9 each ≤ 60 rows) and pre-
   prefix 20/60 cap loss described; source binder independently
   recomputes RRF dedup/ranks/scores/tie order (no encoder/BM25/dense
   search forward); chunk MRR/nDCG remain UNAVAILABLE without explicit
   relevance mapping; foundation contracts and unqualified markers
   preserved.
4. Attributed to exact sources: 51 controlled source-binder
   unit cases; 45 geometry unit cases; raw bridge V3 eight-attempt pass
   (six each of hybrid/dense/lexical/fusion and 13 support calls across
   attempts; one generator, six Session init/close, 546 counts, 73
   catalog / 2,568 bundle loads); stage-loss v2 eight ordered cases
   (two positive / six expected refusals; six native session wrappers
   reaped, no close overages); v1 ancestor-preflight failure and Root
   attribution retained with the separately approved v2; executed test
   6fee2aa7…a38 and final 02c19ff5…c6 differ only by the reviewed
   header/comment change, no rerun; GNU values are waited-process
   observations, not aggregate tree bounds or encoder performance. No
   source plaintext, vectors, credentials or private corpus in published
   docs.
5. Real raw baseline stays NOT RUN: missing approved human held-out
   data, corpus rights/current principal-policy authority and a
   qualified encoder named as separate gates; the 512-row catalog
   diagnostic bound (joined components ≤ 512 rows / 256 cases / 512 Gold
   occurrences over 1 MiB; standalone admission 512 cases / 16 MiB) and
   the synthetic three-revision fixtures are not 20k qualification;
   hardware/visual/license/ICA/full-MVP gates retained; historical
   009-a/b at-time evidence and the 008 accepted state preserved.
6. The single report-head push triggers the full unchanged five-job CI
   (all required steps, product unit+integration 3.12/3.14, three OAP
   jobs). At publication that new run is PENDING — no result certified;
   missing/skipped/pending/cancelled/failed is not green; no old-run
   retry, no test deletion/skip/xfail, no workflow/dependency change.
   Root independently reviews the exact current source/report/head/
   threads/checks before development acceptance.

## Verification

Static Git/read/hash/AST/JSON identity verification only (git objects/diff, size + SHA-256, ast.parse,
json.load, gh pr view); results as above. No local lint/collect/product/unit/
integration/native/model/scorer/store run, no setup/download, no
runtime probe, GPU, credentials, service or private-corpus access. Transferred test evidence is synthetic/owned; live authorization
NONE; real qualification NOT RUN.

## Documentation impact

docs/evaluation.md: 009-a+009-c intro (nine module API families),
009-c provenance (corrected breakdown), three stage API references
(corrected stage bounds, RRF recomputation), actual seam section
(collection wording, per-attempt counts, full test SHAs), absent-
cohort-harness section (coverage 2624). docs/benchmarks/raw-baseline.md:
no-real-results intro, 009-c current-state/provenance with the 512-row
bound; methodology and NOT RUN state unchanged. STATUS.md: current slice 009-c + round record;
009-a/b records preserved. No other docs.

## DHA and boundaries

Decision: NONE (no CRITICAL append; register untouched, zero entries).
Preserved: all immutable prior reports/reviews, failed 009-a CI run and
at-time evidence, v1 stage-proof failure history, source originals/
worktrees, gateway/services, human Qwen3.8-27b/A100 Q8/xhigh
model/profile/auth, other panes. No merge/auto-merge/tag/release/deploy;
PR 11 remains open; no nested agents; no FIFO reread/replay; no
model/profile change; no second consumer.

## Limitations and remaining work

PARTIAL whole 009: the ABSENT callable cohort pipeline, source metric
aggregation, complete denominators and private split/report integration
require another bounded same-009 continuation (separately ordered
read-only cohort design at immutable e6b229; implementation only after
a new explicit Root FINAL order). Real baseline NOT RUN; synthetic proof
is not qualification (20k scale, visual, hardware, license, current
rights, human held-out, ICA, full MVP all open). Report-head CI PENDING
at publication; this report cannot certify its future push/checks — the
separate post-push receipt records observed facts. No next numeric
objective; no merge performed.
