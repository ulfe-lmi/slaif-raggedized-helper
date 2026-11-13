# OAP Coding Report — 009-a

Identifier: 009-a
Result: PARTIAL
Repository: ulfe-lmi/slaif-raggedized-helper
PR number: 11
Branch: oap/009-evaluation-baseline
Base branch: main
Round base commit: 5a7b41cc512cf883b5b2cb92d87554b4d24e685b
PR main base: 5a7b41cc512cf883b5b2cb92d87554b4d24e685b
Transcript commit: 3c6a67a3314ddbe41359b7c47895ddbcc229cf3e
Implementation head SHA: aa4cbfa34ae4c4eba417975635c36180e64e3b63
Report publication commit: SELF

## Work and scope

Order 009-a (FINAL, CREATE_NEW_PR) on base 5a7b41cc: first canonical 009
software wave — byte-exact STATIC transfer of the reviewed structural
text-evaluation contracts, supplied graded-rank metrics and
original-source/span support primitives, plus honest baseline
methodology docs. Transcript 3c6a67a (sole parent 5a7b41cc): 11 paths —
unchanged Root FINAL order (9,509 B), active 009-a+LF (6 B), eight exact
Root records (26,410 B; includes unchanged
oap/reviews/008-resolution.json 1,050 B 340d67dc…) and the exact index
(2,628 B 8391fb06…) at oap/reviews/009-a-root-records.json.
Implementation aa4cbfa (sole parent transcript): 35 paths — 32 NEW blobs
(322,735 B) plus docs/evaluation.md (new), docs/benchmarks/raw-baseline.md
(new) and STATUS.md. This report commit changes only this report. No
merge/cherry-pick/reset/clean/stash/rebase/force push; no product-code
edit, dependency/lock/workflow/config/law/profile change, no source
fixup/format.

## Acceptance evidence

1. Reconciled at start: no existing 009 PR or branch (PRs 1–10 all
   MERGED; no remote oap/009-* branch), so NEW PR 11 is the unique
   objective PR; origin/main 5a7b41cc equals the ordered base and local
   object (parents 1a8fddf8 + 29447168, merge tree equal to 2944 — 008
   merged via PR #10 with CI run 43388401267, five jobs / 78 steps
   SUCCESS per oap/reviews/008-resolution.json). All 11 transcript paths
   byte-verified (size + SHA-256) against oap/reviews/009-a-root-records.
   json (2628 B 8391fb06…) before the transcript commit; record sources
   verified at the supervision audit paths; 008-resolution bytes carried
   unchanged, included once.
2. All 32 donor blobs verified before copy: exact Git-object identity,
   size and SHA-256 at donor SELF 8c351a95 against
   oap/reviews/009-a-components.json (13,971 B f3f65b1b…; 322,735 B
   total); all 32 paths confirmed NEW (absent) at base 5a7b41cc; copied
   by git cat-file and re-verified from disk after copy. After copy:
   12 Python files (6 production + 6 unit) parse (ast) and the 7 JSON
   contracts parse. 27 shared lower 008 paths remain byte-identical
   (Root-verified in the retained records); no API adaptation.
3. Local evidence is STATIC ONLY: git hash/size/JSON/AST/metadata
   checks. No local product, unit, integration, collection, import,
   setup, download, model, store, scorer or runtime probe; no app
   import; live authorization NONE. Root preliminary doc-precision
   review (audit/009-a-pending-doc-precision-review.txt, SHA-256
   d6781e02…a19b) applied before this SELF: six-API pure/
   source-resource distinction, raw_lexical_search/raw_dense_search
   versus stored raw_snapshot_lexical/raw_snapshot_dense naming,
   qualified NOT RUN wording, and later separately-ordered ablations —
   in the two new docs and the matching STATUS bullet; the
   implementation commit was amended (same message/paths) before any
   report existed, preserving the one-implementation topology.
4. Docs: docs/evaluation.md documents the actual six APIs, input
   contracts and bounds, split discipline, privacy, the
   metadata/source/geometry distinction, and known-rank unit oracles
   versus real held-out/actual queries;
   docs/benchmarks/raw-baseline.md records the raw BM25/dense/hybrid
   variants, 20/60 source-evidence cutoffs, explicit graded MRR/nDCG
   where applicable, stage-set loss as future work and the current
   NOT_RUN baseline with no invented samples/latencies/model IDs;
   STATUS.md marks 008 software MERGED verified main and the 009 first
   wave PARTIAL, preserving historical at-time entries and report
   limits.

## Mock/live distinction

The copied unit suites use synthetic fixtures/oracles
(docs/parallel/*-oracle.json) proving mathematics and negative
boundaries only; they were NOT executed locally in this static wave.
The full unchanged five-job CI at the new report head (all steps, unit
+ integration on 3.12/3.14, plus OAP) is the behavior evidence boundary
and remains pending — not certified by this report. No live route, real
model, GPU or corpus access occurred.

## Limitations and open gates

Whole 009 PARTIAL: no actual evaluation harness or real baseline (NOT
RUN), no human held-out data, corpus rights, current
principal/policy authorization or qualified real encoder; no
source-bound stage-set loss or metric-meaningfulness review; no 010
activation from this slice. Root audit/009-a-first-wave-replan.json
governs the named remaining gates; the same 009 prefix continues until
Root resolves.

## Preserved resources; no merge

Qwen3.8-27b/A100 Q8/xhigh profile and auth preserved; unrelated
panes/worktrees/source originals untouched; no merge, auto-merge,
tag, release or deploy; DHA Decision NONE (no CRITICAL append).
