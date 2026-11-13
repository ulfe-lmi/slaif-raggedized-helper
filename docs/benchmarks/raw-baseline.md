# Raw baseline methodology and current NOT RUN state (objective 009)

This document records the declared methodology of the raw retrieval
baseline that will be measured once the missing gates are available. As
of slices 009-a, 009-c, 009-d and 009-e it contains NO real baseline
results: no quality, latency or sample measurements, no model IDs and no
quality claims. Every baseline number below is a declared bound, formula
or variant definition; the attributed software test counts cited in the
evaluation docs (51/45/54 unit cases, eight-attempt composition proofs
and one synthetic cohort composition proof) are distinct software
evidence, not held-out samples. The current baseline state is **NOT
RUN**.

## Pipeline variants

The raw baseline ablates the independent retrieval variants of the 008 raw
snapshot stack (see [../retrieval.md](../retrieval.md)):

1. Raw BM25 (lexical) — `raw_lexical_search` search over the stored
   `raw_snapshot_lexical` payload (pinned Lucene BM25 technical
   analyzer): independent of the dense encoder, preserving identifiers,
   components, flags, paths, versions and negation, with no
   indiscriminate English stemming on Slovenian.
2. Raw dense — `raw_dense_search` search over the stored
   `raw_snapshot_dense` payload (pinned normalized FP32 1024-D CPU
   vectors; BGE-M3 CLS pooling / L2 as defined by the encoder contract;
   the real encoder is UNRUN/UNQUALIFIED).
3. Raw hybrid — `raw_rank_fusion` / `raw_hybrid_search`: dedup plus
   reciprocal-rank fusion `Σ 1/(60 + rank)` over the two raw candidate
   lists; raw scores are never added.

The full planned ablations (contextualized hybrid, reranker, Q4/Q6,
alternate embedder, vision per A32) are later, separately ordered scope
— they are not part of this 009 wave and are not asserted as such. The
online A19 serving pipeline (60 + 60 → dedup/RRF → 40 reranked → about
6–10 evidence chunks) is downstream of the raw baseline and is not
measured here.

## Source-evidence size

Baseline scoring is declared at per-query source-evidence cutoffs **20
and 60**, matching the `supplied_rank_metrics` default cutoffs
`(20, 60)` and the 20–60 source-evidence discipline. Cutoffs are
strictly increasing values up to 4,096 (up to 16 per call); the raw
variants return source-bound candidate identities, and the scored units
remain `SUPPLIED_UNIT_ID` until a real adapter binds them to originals.

## Metrics

- Explicit graded MRR / nDCG where applicable — formula version
  `supplied-rank-metrics-v1`: graded gain `2**grade − 1`, `log2` rank
  discount, ideal DCG drawn from all positive gold up to the cutoff;
  recall is positive hits over all positive gold; MRR/recall/nDCG are
  macro-averaged over defined queries only, with every query and count
  retained. Empty positive gold is `UNDEFINED_EMPTY_POSITIVE_GOLD`
  (`None` fields with an explicit reason), never a silent zero.
- Recall@k and candidate loss at the declared cutoffs.
- Stage-set loss (future work) — `compare_stage` over supplied removal
  identities with the `after ⊆ before` invariant; binding it to ACTUAL
  pipeline stage traces (dedup, fusion, rerank) is required subsequent
  009 work. No loss is inferred when stage identities are unavailable.
- Metric meaningfulness gate — conventional chunk MRR/nDCG cannot simply
  follow requirement grades: the grades are declared and
  `DECLARED_UNVERIFIED`. Before any metric is treated as meaningful, the
  original 009 criterion 3 requirements still apply: reviewed typed
  meaningfulness and mapping, independent oracles (source recall and
  source-bound trace/stage loss), and source-bound evidence. A synthetic
  oracle pass is not a real baseline.

## Current state: NOT RUN

009-a, 009-c, 009-d and 009-e are static byte-exact transfers plus
documentation in the canonical lane: no real approved evaluation dataset
and no baseline were measured; the coding local work was static (no
local or CI baseline run occurred and no encoder was executed). Slice
009-c additionally integrates the reviewed source-backed stage
components and their synthetic actual-source composition proofs, slice
009-d the reviewed pure declared-cohort aggregation (exact rationals;
six prefix summaries and seven transition summaries over 1–256 supplied
cases) — supplied-geometry math, not a source run — and slice 009-e the
reviewed source cohort runner: the source-running cohort pipeline
(`source_cohort_runner.run_cohort`) that joins full-dataset admission,
declared split/subset selection, per-case traced producer and
source-bound stage binding and one pure aggregation only after complete
success into the joined private split report, plus its one bounded
synthetic composition proof (four outer attempts, seven producer / six
binder / one aggregate direct calls, no surviving subset). The runner's
1–256-case and 512-Gold admission values are software bounds, not
physical permission or an invented pilot reduction; the bounded 512-row
catalog diagnostic (the joined geometry/source-binder components admit
≤ 512 rows, 256 cases and 512 global Gold occurrences over 1 MiB; the
standalone dataset foundation separately permits 512 cases over 16 MiB)
and the synthetic three-revision fixtures are not 20k-scale
qualification, and the 51/45/54 controlled unit case counts, the
eight-attempt composition proofs and the one synthetic cohort
composition proof are software evidence, not retrieval measurements or
held-out samples.
Future ordinary CI runs of the copied synthetic
unit fixtures are distinct from, and do not constitute, a real
baseline. Missing gates that block the real baseline (each is a gate, not
a synthetic pass):

- Human-approved representative held-out questions (held-out untouched;
  synthetic supplemental only).
- Corpus rights for the evaluation corpus.
- Current principal/policy authorization for the evaluation data.
- A qualified real encoder (BGE weights UNRUN/UNQUALIFIED; no model,
  hardware or hardware-parity claim).

Thresholds must be declared before selection (A32): the proposed targets
(e.g. ≥ 95% held-out single-source Recall@20, zero observed leaks or
invalid citations) are proposals recorded here as policy, not measured
results, and humans must inspect the errors and sampled contexts.

## Provenance

The metrics formulas and bounds are the byte-exact transferred contracts
of the 009-a slice (donor SELF `8c351a95`, per
`oap/reviews/009-a-components.json`, SHA-256 `f3f65b1b…a80f`); see
[../evaluation.md](../evaluation.md) for the API reference and
[../parallel/supplied-rank-metrics-design.md](../parallel/supplied-rank-metrics-design.md)
for the frozen contract. The 009-c source-backed stage slice (source
SELF `e6b229b1`, per `oap/reviews/009-c-components.json`, SHA-256
`6fbeb96c23…c5c633af91`) adds the stage-loss and geometry contracts under
[../parallel/](../parallel/); the 009-d declared-cohort-metrics slice
(source SELF `b33da381`, implementation `b15adaf`, per
`oap/reviews/009-d-components.json`, SHA-256 `665c7118…d656`) adds the
pure cohort-aggregation contract, oracle and API under the same
directory; the 009-e source-cohort-runner slice (source SELFs `91f31182`
runner and `5ffef4c1` proof, per
`oap/reviews/009-e-components.json`, SHA-256 `b73448cf…c55c8e6`) adds
the runner contract, binding, API, composition and proof documents under
the same directory. None of these changes the declared methodology or
any measured result; the real baseline state is unchanged: NOT RUN.
