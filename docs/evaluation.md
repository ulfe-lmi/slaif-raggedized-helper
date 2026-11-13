# Canonical text evaluation foundations (objective 009, slices 009-a and 009-c)

This document is the nonroutine evaluation reference for the 009
software waves: the byte-exact transfer of the reviewed structural
text-evaluation dataset contract, the supplied graded-rank metrics and the
original-source/span support primitives (slice 009-a), plus the three
source-backed stage components — raw text stage support, declared stage
geometry and source-bound stage loss — with their actual synthetic
source-backed composition proofs (slice 009-c). Together they are the
nine private module API families — the nine callable private evaluation
primitives. The routine coding context
remains unchanged; the exact per-component contracts live in the byte-exact
transferred documents under [docs/parallel/](parallel/)
(`text-evaluation-dataset-api.md`/`-design.md`/`-oracle.json`,
`supplied-rank-metrics-api.md`/`-design.md`/`-oracle.json`,
`text-evaluation-gold-binding-api.md`/`-design.md`/`-oracle.json`/
`-coverage-followup.md`, `declared-span-support-api.md`/`-design.md`/
`-oracle.json`, `source-bound-ranking-api.md`/`-design.md`/`-oracle.json`,
`source-bound-text-support-api.md`/`-design.md`/`-input-pins.json`/
`-oracle.json`, and the 009-c `raw-text-stage-support-api.md`/
`-contract.md`/`-composition.md`, `declared-stage-geometry-api.md`/
`-contract.md`, `source-bound-raw-stage-loss-api.md`/`-contract.md`,
`source-bound-stage-proof-composition.md`/`-inputs.json`,
`raw-text-stage-composition-inputs.json` and
`source-bound-support-ci-preparation.md`).

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

## Provenance of the 009-c slice

Twenty-two files (395,115 bytes: three production modules — 127,064 B —
three unit suites — 110,520 B — five integration suites — 78,437 B, one
of them the exact existing raw-hybrid fixture modification — and eleven
docs/parallel contract and proof documents — 79,094 B) were transferred byte-exact by Git-object read from the
reviewed source SELF `e6b229b1` (implementation `748d08b4`) of the
parallel 009 source-stage-proof worktree, per the Root-owned index
`oap/reviews/009-c-components.json` (identical to
`audit/009-c-components-FINAL.json`, SHA-256
`6fbeb96c23…c5c633af91`). All 21 NEW targets were verified absent at the
round base `aba42a52` and the one MODIFY target verified against its exact
preimage SHA-256 before copy; every blob was verified by size and SHA-256
against immutable Git objects before and after copy. No cherry-pick,
merge or branch-ancestry transfer; no lower adaptation. The candidate
carries the local Root records retained in the 009-c transcript
(`oap/reviews/009-c-source-binder-review.json`,
`oap/reviews/009-c-stage-proof-review.json`,
`oap/reviews/009-c-stage-proof-actual-review.json`,
`oap/reviews/009-c-local-admissions.json`,
`oap/reviews/009-c-source-base-compatibility.json`,
`oap/reviews/009-c-peer-driver.json`) and the Root replan
(`oap/reviews/009-c-replan.json`).

## The six private evaluation APIs (slice 009-a)

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

## The three source-backed stage APIs (slice 009-c)

These three complete the nine callable private evaluation primitives. Two
borrow the original/derived stores plus an active same-root snapshot pin;
one is pure geometry over supplied rows and stage relations.

### `raw_text_stage_support.evaluate_case(originals, derived, store_root, pin_owner, dataset_bytes, case_id, gold_bundle_ids, query_payload, *, query_space_id, query_definition_fingerprint, query_policy_id, query_execution_fingerprint, grants, restrictions=None, deadline_ms=120000)`

Private sequential diagnostic over the ACTUAL raw retrieval stack. It
admits the complete canonical dataset (≤ 16 MiB), the chosen case (ID ≤
128 chars), up to 128 sorted unique bundle hashes, one 4,096-byte
normalized little-endian float32 query vector and four declared query
identifiers; the strict integer deadline is 1–120,000 ms, one cooperative
clock covering admission, every lower call and final construction
(admission ≤ 5,000 ms, each support call ≤ 30,000 ms). The case scope is
the allowlist intersection of the supplied grants with the dataset scope,
retaining restrictions unchanged; an empty corpus or version
intersection denies all, and empty labels allow only unlabeled sources —
supplied declarations, not current rights or Gold eligibility. Per full attempt, under
the held old pin, it performs one owned hybrid call and three sequential
owned source-support calls over the actual dense/lexical/fusion results
(the V3 proof's totals of six each of hybrid/dense/lexical/fusion and 13
support calls are the per-attempt aggregate across its eight attempts,
as recorded in the aggregate counter paragraph below). The
frozen `StageSupport` result carries linkable IDs, counts, cap markers and
the per-cutoff source-support coverage records; it omits question text,
the vector, source content, paths, hits, traces and exceptions. Errors
are content-free `StageSupportError`; coverage is declared original-span
geometry, not factual support, and MRR/nDCG/Gold candidate-loss are
unavailable under `UNSPECIFIED_RELEVANCE_UNIT_MAPPING`. Markers: execution
NOT_ATTESTED, results NOT_QUALIFIED, source binding limited to the owned
binding calls.

### `declared_stage_geometry.diagnose(dataset_bytes, case_id, rows, stages, *, deadline_ms=10000)`

Pure supplied-stage geometry diagnostic (no store, model or runtime
access). It re-admits the canonical dataset (≤ 1 MiB here) and takes
supplied row geometry (≤ 512 rows, ≤ 8,192 fragments, ≤ 65,536 block-ID
characters, ≤ 512 global Gold occurrences, ≤ 256 cases), EXACTLY ten
named stage relations (each ≤ 512 indices; the returned-index sets of
stage positions 3, 7 and 9 are each ≤ 60 rows; ≤ 5,120 stage indices
total) and a strict
1–10,000 ms deadline covering admission and all thirteen lower calls
under one bounded work/serialization ledger (W ≤ 67,108,864 work units,
B ≤ 134,217,728 bytes of declared logical allowances — not CPU, memory or
I/O limits). It reports per-stage and ordered @20/@60 completion,
full-stage requirement/alternative coverage, removal transitions with
lost alternatives and requirements, and declared required source recall:
the denominator is ALL mandatory chosen Gold revisions, every atom of a
revision must be covered, independently of requirement coverage; the
measure is undefined for no-Gold cases and OR alternatives. Chunk MRR and
nDCG are UNAVAILABLE because no explicit chunk relevance mapping exists;
alternative requirement grades cannot supply one, and a separate explicit
graded-item rank library exists but is not called here. Inputs are caller
declarations: source binding UNVERIFIED, eligibility NOT_CHECKED,
execution NOT_ATTESTED, qualification NOT_QUALIFIED; stage relations
alone do not establish a complete eligible universe, score ordering or
rights.

### `source_bound_stage_loss.bind_stages(originals, derived, root, pin_owner, dataset_bytes, case_id, gold_bundle_ids, hybrid_result, query_payload, *, query_space_id, query_definition_fingerprint, query_policy_id, query_execution_fingerprint, grants, restrictions=None, deadline_ms=120000)`

Source-bound stage diagnostic. It takes the supplied hybrid result
(HybridResult) traces, validates the complete eligible and matching
universes from source through sequentially observed source bindings
under one 1–120,000 ms cooperative deadline, constructs the ten stage
relations and independently recomputes the RRF dedup, ranks, scores and
tie order (pure arithmetic over the supplied modality order — no
actual encoder, BM25 or dense scoring/search forward is executed; dense
and lexical score order remains `SUPPLIED_SCORE_ORDER_NOT_REEXECUTED`),
then passes the geometry to the pure component. The fixed source
envelope comprises five direct pin checks, one direct catalog load and
two catalog loads inside ranking (three catalog loads total), one Gold
binding and one ranking binding — at most 12,288 derived loads and
4,986,555,627,809 logical read-payload bytes — with owned logical
work/payload limits 134,217,728 / 268,435,456 (not CPU, memory or
physical I/O limits). The pure component retains `UNVERIFIED` source
binding; the observations establish neither current rights nor
atomicity. Pre-prefix cap loss is reported at the 20/60
cutoffs from the observed stage rows. A successful binding still proves
only sequential consistency of the supplied trace with observed source
metadata — not that the declared model/scorer produced the ranking, that
policy remains current after the last observation, or any user quality.

## Input contracts and bounds

Every deadline is cooperative (checked between steps; it cannot preempt a
running operation) and is an int in 1–30,000 ms except gold binding
(1–120,000 ms) and the three 009-c stage APIs (raw text stage support and
source-bound stage loss 1–120,000 ms; declared stage geometry
1–10,000 ms). All refusals are content-free; `BaseException`
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

## The actual source-backed stage seam (slice 009-c)

The integration suites — collected by the unchanged ordinary CI's
explicit `tests/integration` command; the global pytest default
`testpaths` remains `tests/unit` — compose the actual synthetic raw
retrieval with the new components on owned three-revision fixtures (no
model forward, no encoder; supplied synthetic queries and normalized
vectors only):

- `test_raw_text_stage_support_composition.py` — the Root-approved V3
  actual proof joined one actual hybrid retrieval to three actual
  source-bound support calls under one retained selection pin across
  eight ordered attempts (positive; empty intersection; chosen no-Gold
  case with unrelated Gold retained; corrupt unrelated Gold; temporarily
  withdrawn original; restored positive; expiry after the actual hybrid
  returned; closed-pin refusal). It passed all eight attempts on the
  executed bytes; recorded counters were one generator, six Session
  initializations and closes, 546 Session counts, 73 catalog loads,
  2,568 bundle loads, six each of hybrid/dense/lexical/fusion and 13
  support calls, final pin state CLOSED. GNU time for its waited process:
  64.31 s wall / 62.36 s user / 0.50 s system, 92,240 KiB max RSS —
  waited-process observations, not aggregate tree bounds or encoder
  performance.
- `test_source_bound_stage_loss_composition.py` — one actual hybrid
  producer plus source-bound stage diagnosis; the selected case requires
  source spans from `a` and `c`, an unrelated case retains a `c` beta
  atom, and the reciprocal-rank-fusion oracle expects `2/61` and `1/62`.
  The separately approved v2 actual attempt completed all eight ordered
  cases — two positive bindings and six expected refusals (coherent
  eligible and lexical omissions, a fused-score alteration, owned-blob
  withdrawal after Gold returned, controlled expiration after Rank
  returned, closed pin) — asserting the intended pre-Gold/pre-Rank/
  pre-pure boundaries and restoring the blob in `finally`. Observed: one
  producer, two successful and six refused binder calls, two pure
  diagnoses, 26 lower scoring calls; six captured native session wrappers
  reaped, six session closes, both store closes and the pin close
  complete, no close overages. GNU time for its waited process: 24.18 s
  elapsed / 23.20 s user / 0.25 s system, 92,832 KiB max RSS. The earlier
  v1 attempt failed before selection when the existing directory guard
  rejected writable ancestors of the proposed scratch path; Root
  attributed the path-preflight omission to its approval and separately
  authorized v2 with a fresh private scratch path under a permitted
  sticky ancestor — both the failure and the pass are preserved
  privately; no shared permissions or product guards changed. The
  executed test (SHA-256
  `6fee2aa7767c4449b01f2fb0d9ac4a988cff1dd3e8bfd44b832bac3915859a38`)
  and the final bytes (SHA-256
  `02c19ff566a426ea5e513d022d52f47f63040b0d0d958cdc9a9c2879f1b760c6`)
  differ only in a reviewed module docstring and the removal of a stale
  comment (header/comment-only change); no rerun is invented.
- `test_source_bound_support_ci_composition.py` /
  `test_source_bound_support_ci_cleanup.py` — the portable
  source-bound support fixture journey (support 1/2 at both cutoffs for
  one row, 2/2 for both; whole-dataset three occurrences / three distinct
  atoms; empty ranking zero support with a nonzero denominator; denied
  source, absent case, absent Gold bundle and wrong unrelated Gold hash
  refusals) and its controlled failure/cleanup negatives.

The stage-loss proof checks ten full stages (`dense.eligible/ranked/
selected/returned`, `lexical.eligible/ranked/selected/returned`,
`fusion.input`, `fusion.returned`), seven supplied transitions and the
20/60 prefixes without inventing chunk relevance grades. The caller
retains a real pin across a pointer-generation advance of the same
snapshot (captured old generation and pointer SHA-256 asserted), so the
proof covers the captured old generation only: it does not prove a
distinct snapshot transition, ABA prevention or current policy. Full
eligible/matching source validation is revalidated at call time on every
pass (Gold bundles and selected ranking rows against the borrowed stores;
sequential, not atomic). Controlled unit runs attributed to their exact
sources: 51 controlled source-binder unit cases (source-bound stage
loss; Ruff7 passed on the same Python bytes) and 45 geometry unit cases
(declared stage geometry; final Ruff passed); earlier partial runs and
their corrections are preserved in the transcript records.

## Absent cohort harness (independent coverage 2624)

The nine callable private per-case primitives and the actual per-case
source-backed seam above are components, not a harness. The independent
COMPLETE software-coverage audit (SHA-256 `262440e2…54f139`, Root
adjudicated and retained as
`oap/reviews/009-c-software-coverage-adjudication.json`) confirms what
remains ABSENT from production: a callable cohort pipeline joining
frozen split selection, per-case producer traces/source binding,
original source Recall@20/60/full multi-source and stage-loss
aggregation, and total/defined/undefined/refused denominators with
private report provenance. Source-linked chunk grades are absent: the
existing generic MRR/nDCG oracle is valid over supplied units and is not
grounds to infer requirement-to-chunk grades. No CLI is invented as a
requirement, but an operator still writing a loop around the generic
aggregate is not implemented harness software. This is an ordinary
missing implementation — not D1 and not an external human blocker — and
requires another bounded same-009 continuation (a separately ordered
read-only cohort contract/oracle design may proceed at the immutable
source; bounded implementation only after a new explicit Root FINAL
order).

## Unit oracles versus real held-out and actual queries

The nine unit suites (six 009-a plus the three 009-c slices) exercise the
copied synthetic fixtures and the `docs/parallel/*-oracle.json` vectors:
they prove the mathematics, the admission boundaries and the negative
paths, not retrieval quality; the 009-c integration suites are the
synthetic source-backed composition proofs described above and are
likewise not a baseline. The
real raw baseline additionally requires human-approved representative
held-out questions, corpus rights, current principal/policy authorization
and a qualified real encoder; those gates are missing, so the baseline is
NOT RUN — see [docs/benchmarks/raw-baseline.md](benchmarks/raw-baseline.md)
for the declared methodology.
