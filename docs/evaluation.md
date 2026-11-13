# Canonical text evaluation foundations (objective 009, slice 009-a)

This document is the nonroutine evaluation reference for the first 009
software wave: the byte-exact transfer of the reviewed structural
text-evaluation dataset contract, the supplied graded-rank metrics and the
original-source/span support primitives. The routine coding context remains
unchanged; the exact per-component contracts live in the byte-exact
transferred documents under [docs/parallel/](parallel/)
(`text-evaluation-dataset-api.md`/`-design.md`/`-oracle.json`,
`supplied-rank-metrics-api.md`/`-design.md`/`-oracle.json`,
`text-evaluation-gold-binding-api.md`/`-design.md`/`-oracle.json`/
`-coverage-followup.md`, `declared-span-support-api.md`/`-design.md`/
`-oracle.json`, `source-bound-ranking-api.md`/`-design.md`/`-oracle.json`,
`source-bound-text-support-api.md`/`-design.md`/`-input-pins.json`/
`-oracle.json`).

## Provenance of the 009-a slice

Thirty-two files (322,735 bytes: six production modules, six unit suites and
twenty docs/parallel contract documents) were transferred byte-exact by
Git-object read from the reviewed local assembly commit SELF `8c351a95`
(implementations `c91a5c2b` and `70d3b61f`) of the parallel 009
source-support and evaluation-foundations preparation worktrees, per the
Root-owned index `oap/reviews/009-a-components.json` (identical to
`audit/009-a-components-FINAL.json`, SHA-256 `f3f65b1b…a80f`), retained with
the other seven exact Root records in the 009-a transcript. All 21 current
008 production blobs plus the six source/derived/ingestion/provenance/
structured lower modules are byte-identical between actual merged main
`5a7b41cc` and the donor, so no lower API adaptation, cherry-pick or branch
ancestry transfer was needed; no other path was modified. The candidate
carries the local Root reviews
(`oap/reviews/009-a-foundations-source-review.json`,
`oap/reviews/009-a-source-support-source-review.json`) and the first-wave
replan (`oap/reviews/009-a-first-wave-replan.json`).

## The six private evaluation APIs

Three of these are pure (no I/O, no store access): dataset admission,
supplied rank metrics and declared span geometry. Three are
source-resource APIs: they borrow the original/derived stores (and, for
the last, the snapshot catalog) and revalidate observed content at call
time — gold binding, source-bound ranking and source-bound text support.

### `text_evaluation_dataset.admit(dataset_bytes, *, deadline_ms=5000)`

Admits canonical ASCII JSON bytes as *declarations* under schema
`slaif-text-evaluation-dataset-v1` (exact key sets, sorted compact
serialization, int64 integers only; floats, constants, duplicate keys,
oversize or non-canonical bytes are refused). Bounds: input ≤ 16,777,216 B,
≤ 200,000 JSON nodes, depth ≤ 16, ≤ 4,000,000 text characters; cases 1–512;
per case `split ∈ {tuning, held_out}`, `origin ∈ {synthetic,
human_declared}`, opaque `authorship_ref`/`rights_ref`/`split_review_ref`
(≤ 512 chars each), question ≤ 8,192 chars / 32,768 B, language grammar,
nullable product/version, `scope` corpora/versions/labels sorted-unique
(≤ 128/128/64), `acceptable_facts`/`disallowed_claims` ≤ 64 each, disjoint
and total ≤ 8,192, `answerability ∈ {answerable, unanswerable, unknown}`,
modality exactly `text`; requirements ≤ 16 with grade 1–3, alternatives ≤ 8
holding 1–8 gold spans each; a gold span is
(`revision_id`, `extraction_id` — both `sha256:` + 64 hex, `block_id`,
`0 ≤ start < end ≤ 200,000` code-point offsets, declared substring
`text_sha256`); total gold atoms ≤ 4,096. Each `family_id` and each exact
question maps to exactly one split (cross-split family or question is
refused). Returns frozen records plus canonical identities: `dataset_id`
(sha256 over the canonical bytes) and `split_id` (sha256 over namespace,
split-policy reference and per-case assignments including question sha256).

The result stays `NOT_QUALIFIED` with `DECLARED_UNVERIFIED` authorship and
rights and a `STRUCTURAL_ONLY` split: admission verifies structure and
internal consistency only, never actual source, block, substring, rights,
semantic leakage, human origin or split review. Unknown answerability is
not a successful abstention; synthetic held-out cases do not pass human
evaluation.

### `supplied_rank_metrics` — `score_query` / `aggregate` / `compare_stage`

Pure mathematics over caller-supplied, unverified opaque relevance units.
`score_query(query_id, gold, ranking, *, cutoffs=(20, 60), deadline_ms=5000)`:
gold is a sorted-unique tuple of `(ident, grade 0–3)` pairs, ranking a
tuple of unique IDs, cutoffs 1–16 strictly increasing values ≤ 4,096. Per
cutoff k it reports `returned_at_k`, `relevant_returned`, graded DCG
`Σ (2**grade − 1)/log2(rank + 1)` against the ideal arrangement of all
positive gold up to k, recall (positive hits over all positive gold),
reciprocal rank and nDCG clamped to [0, 1]. Empty positive gold yields
`None` fields with the explicit reason `UNDEFINED_EMPTY_POSITIVE_GOLD`; a
positive-gold query with no hits scores zero. `aggregate(cases, …)` keeps
every query and count and averages MRR/recall/nDCG over the defined
queries only. `compare_stage(gold, before, after, …)` describes supplied
removal identities: it requires `after ⊆ before` (a stage removes, never
adds), reports removed/gold-removed IDs, recall before/after/loss and the
retained fraction; a `None` stage is `UNAVAILABLE` with
`MISSING_STAGE_IDENTITIES` and no loss is inferred.

All results carry `SUPPLIED_UNVERIFIED` origin, `NOT_QUALIFIED`
qualification, `SUPPLIED_UNIT_ID` relevance unit and formula version
`supplied-rank-metrics-v1`. Bounds: 16 MiB of UTF-8 ID occurrences,
65,536 aggregate entries, 2,097,152 work units, 64 MiB serialized
fingerprint bytes, cooperative deadline 1–30,000 ms; ordinary errors raise
the content-free `MetricsError`. No I/O occurs. These units do not resolve
original Unicode-span AND/OR alternatives, duplicate credit, source
coverage or actual stage traces, and they are not a held-out evaluation.

### `text_evaluation_gold_binding.bind(originals, derived, dataset_bytes, bundle_ids, *, deadline_ms=30000)`

Revalidates the declared gold spans against selected controlled-store
bundles: the adapter must be `structured_text`, every matching block
`native` and non-visual, the span within the block text, and the exact
substring sha256 equal to the declaration. Every gold atom must occur in at
least one selected bundle and every selected bundle must match at least one
atom; the whole store is observed twice and the two observations must be
identical. Positive binding reports `ORIGINALS_REVALIDATED_AT_BIND_TIME`
and retains every matching bundle ID per atom; empty gold requires no
bundles and reports `NO_GOLD_SOURCE_VALIDATED` (the stores are not
validated). All PDF and visual source bindings are refused; the stores are
borrowed and remain open. Bounds: bundles ≤ 128 sorted hex-64 IDs, atoms ≤
4,096, span length ≤ 4,194,304 code points, blocks ≤ 4,096, bytes ≤
100,663,296, matched bytes ≤ 16,777,216, deadline 1–120,000 ms. Markers
stay `NOT_QUALIFIED` / `DECLARED_UNVERIFIED` / `STRUCTURAL_ONLY`: the record
is an observation at bind time, not an atomic snapshot and not current
authorization, withdrawal, rights, source quality or human held-out
provenance. It consumes no rankings and calculates no metrics.

### `declared_span_support.score_case(dataset_bytes, case_id, ranking, *, cutoffs=(20, 60), deadline_ms=5000)`

Geometry only. It re-admits the canonical dataset and takes a supplied
ranking of rows `(chunk_id, revision_id, extraction_id, fragments)` where
the first three are `sha256:` + 64 hex and each fragment is a
`(block_id, lo, hi)` half-open code-point interval with
`0 ≤ lo < hi ≤ 200,000` (≤ 256 fragments per chunk, ≤ 65,536 total). At
each cutoff the returned fragments are merged per
`(revision, extraction, block)`; a declared gold atom is covered when its
`[start, end)` is fully contained in a merged interval; atoms within an
alternative are conjunctive, alternatives disjunctive, and a requirement is
covered when any alternative is covered. Coverage fractions count ALL
declared requirements of the case in the denominator; an empty ranking is
an observed empty input (`None` is refused) and a case without
requirements reports the `NO_GOLD_REQUIREMENTS` reason.

Outputs stay `SUPPLIED_UNVERIFIED` with `source_binding: UNVERIFIED` and
`NOT_QUALIFIED` (formula `declared-span-support-v1`). The fingerprint binds
the supplied ordering and the admitted dataset (including grades), not
source truth, query, snapshot or authorization; a full-block claim can
score without being true.

### `source_bound_ranking.bind(originals, derived, store_root, snapshot_id, expected_catalog_id, chunk_ids, *, grants, restrictions=None, deadline_ms=30000)`

Binds an exact ordered tuple of up to 4,096 distinct supplied chunk IDs to
revalidated originals through the 008 raw-snapshot catalog and row map.
`store_root` is a canonical absolute snapshot directory; both the snapshot
ID and the expected catalog ID are required; grants (mandatory) and
restrictions (optional) are copied before source validation, and any
selected row denied by those supplied grants refuses the whole call with
the content-free `SourceBindingError`. Each pass revalidates the selected
bundles from the borrowed stores (per-pass cumulative limits: 128 bundles,
4,096 block occurrences, 100,663,296 metadata/member bytes, 65,536 source
fragments, 16,777,216 copied UTF-8 bytes, 2,097,152 block-ID bytes),
requires `structured_text`/`complete_text`/`unicode_codepoints` with text
media type and native non-visual blocks, rechecks every row declaration
against the catalog rows and recorded chunk/revision/dependency bytes,
rebinds each chunk scope through the provenance registry (equal to the
recorded row scope) and applies `reader_allows(scope, grants,
restrictions)`; each fragment's copied text must equal the block substring
with the exact digest. The catalog is loaded twice and both passes must be
identical (determinism; this is not an atomic lease, ABA proof or hard
deadline).

The result marks `SUPPLIED_RANKING_UNVERIFIED` origin,
`SUPPLIED_SCOPE_CHECKS_ONLY` authorization, `NOT_ATTESTED` execution and
`NOT_QUALIFIED` qualification; status is
`ORIGINALS_REVALIDATED_AT_BIND_TIME`, or `NO_SELECTED_SOURCE_VALIDATED` for
an empty tuple (which still triggers two complete catalog validations and
proves no retrieval was empty). Rows carry no source plaintext, rendered
text, scores or tokens; the result is private linkable data.

### `source_bound_text_support.score_case(originals, derived, store_root, snapshot_id, expected_catalog_id, dataset_bytes, case_id, gold_bundle_ids, chunk_ids, *, grants, restrictions=None, cutoffs=(20, 60), deadline_ms=30000)`

Private operator-only diagnostic that composes the three prerequisites:
admit the complete dataset, bind gold across the complete dataset (which
can refuse because of an unrelated case), bind the supplied ranking to its
source, then apply the declared span geometry, cross-checking identities
and counts between the stages. The calls share one cooperative deadline
with nested sub-deadlines; sources are observed sequentially, not under an
atomic lease. The frozen `TextSupport` result contains the per-cutoff
coverage over all declared case requirements, case and global gold-atom
counts, the three stage statuses (case gold
`ORIGINAL_GOLD_SPANS_REVALIDATED_AT_CALL_TIME` or
`NO_CASE_GOLD_REQUIREMENTS`, plus the gold and ranking source statuses),
and the geometry fingerprint. It retains no plaintext, question text, path
or source fragment.

Markers: `SUPPLIED_RANKING_UNVERIFIED` origin,
`OWNED_TEXT_BINDING_CALLS_ONLY` source binding, `NOT_CHECKED` gold
eligibility, `SUPPLIED_RANK_SCOPE_ONLY_GOLD_RIGHTS_UNVERIFIED`
authorization, `NOT_ATTESTED` execution,
`SEQUENTIAL_OBSERVATIONS_NOT_ATOMIC` temporal consistency, `NOT_QUALIFIED`
(formula `source-bound-text-support-v1`). Gold eligibility and current gold
rights are not checked; supplied ranking, query execution, human quality,
held-out status and model/hardware qualification are not attested. Do not
publish result data or use it as a serving route.

## Input contracts and bounds

Every deadline is cooperative (checked between steps; it cannot preempt a
running operation) and is an int in 1–30,000 ms except gold binding
(1–120,000 ms). All refusals are content-free; `BaseException`
subclasses propagate. Fingerprints are domain-separated sha256 over
canonical sorted ASCII JSON of the exact supplied inputs. Ordinary
dataclass constructors are not admission APIs and results are forgeable
DTOs, not later admission credentials.

## Split discipline

The declared split is `{tuning, held_out}`; `family_id` and exact question
text each map to exactly one split at admission. The dataset exposes
`tuning_count`, `held_out_count`, `synthetic_count`,
`human_declared_count` and `held_out_human_declared_count`; split review is
an opaque reference (`STRUCTURAL_ONLY`), so admission never reviews the
split. Held-out cases must stay untouched by tuning; synthetic cases may
supplement but a synthetic held-out split is not a human held-out. Dataset
bytes, questions and gold are private operator data and stay out of Git
(A32).

## Privacy

Results are private, linkable and not anonymized: fingerprints are
linkable and dictionary-attackable, `asdict`/equality/hashing can expose
data, and `repr` hides record values. No result contains source plaintext
or paths; errors never echo input content. Callers must protect the data
and never publish it.

## Metadata versus source versus geometry

Three distinct layers, each with its own status fields:

- Declared metadata — authorship/rights/split references, origin, scope:
  `DECLARED_UNVERIFIED`; admission cannot verify them.
- Revalidated source — gold spans rechecked against the stores at bind
  time: `ORIGINALS_REVALIDATED_AT_BIND_TIME` (or
  `NO_GOLD_SOURCE_VALIDATED`); an observation, not atomic, not current.
- Geometry — declared span containment and supplied stage-set loss:
  `SUPPLIED_UNVERIFIED` / `UNVERIFIED`; no source truth.

Conflating the layers is a category error; missing or unrelated
gold/source failure is a refusal, never an empty or qualified success, and
no private operator here is an authenticated or current-policy claim.

## Unit oracles versus real held-out and actual queries

The six unit suites exercise the copied synthetic fixtures and the
`docs/parallel/*-oracle.json` vectors: they prove the mathematics, the
admission boundaries and the negative paths, not retrieval quality. The
real raw baseline additionally requires human-approved representative
held-out questions, corpus rights, current principal/policy authorization
and a qualified real encoder; those gates are missing, so the baseline is
NOT RUN — see [docs/benchmarks/raw-baseline.md](benchmarks/raw-baseline.md)
for the declared methodology.
