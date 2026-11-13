# Raw retrieval snapshot foundation (objective 008-a)

This document is the nonroutine retrieval reference for the first bounded 008
slice. The routine coding context remains unchanged; exact per-component
contracts live in the byte-exact transferred documents under
[docs/parallel/](parallel/) (`technical-analyzer-api.md`,
`raw-snapshot-membership-api.md`/`-design.md`,
`raw-snapshot-source-rows-api.md`/`-design.md`,
`raw-snapshot-dense-api.md`/`-design.md`,
`raw-snapshot-lexical-api.md`/`-design.md`,
`raw-snapshot-payload-format-map.md`).

## Provenance of this slice

Twenty-five files (142,322 bytes: five production modules, twenty test
files, ten docs/parallel contract documents; five unit and five integration
suites) were transferred byte-exact by Git-object read from the reviewed local
assembly commit SELF `96822ff4` (implementation `3eac764`) of the parallel
raw-foundation worktree, per the Root-owned index
`oap/reviews/008-a-foundation-components.json` (identical to
`audit/008-a-foundation-components-FINAL.json`, SHA-256
`e11bfb74…0633`). No branch switch, cherry-pick or ancestry merge of the
candidate occurred; no other path was modified. The candidate carries local
Root review (`oap/reviews/008-a-foundation-Root-review.json`), local admission
(`oap/reviews/008-a-foundation-local-admission.json`), an opposite peer
composition report (`oap/reviews/008-a-foundation-peer.json`, SHA-256
`e206819d…922f`) and its Root review, plus the approved normal-layout test
addendum. Those are provenance records, not canonical acceptance: whole-008
acceptance still requires current canonical CI, same-PR continuations and
Root review.

## Actual callable foundation (what exists now)

All five modules are importable package members; none is wired into the CLI,
a store lifecycle, a snapshot publisher or any caller in this slice.

- `technical_analyzer`: `analyze(text, policy)` returns ordered
  `Term(text, start, end, derivation)` tuples with half-open codepoint spans;
  `analyzer_id(policy)` is the canonical version-1 fingerprint over limits,
  NFKC/casefold policy and the Unicode database version. Bounded by
  `Policy` defaults (1,000,000 B / 250,000 chars / 4,096 token chars /
  100,000 terms / 128 components per run / 2,000,000 work units / 5,000 ms)
  under hard ceilings; every failure is a content-free `AnalyzerError`.
  Identifiers, connectors, flags, paths, versions and negation-bearing
  literals are preserved; no stemming, no stopword removal, no language,
  path or URL parsing, no fetch, no execution.
- `raw_snapshot_membership`: `parse` (canonical `slaif-raw-source-membership-v1`
  bytes only), `build` (fresh reload of caller-selected actual ingestion
  bundles against their originals, including selected sources with zero
  rows), `bind` (declared core + row-map correspondence) and `validate`
  (bind + exact-byte fresh rebuild). Whole-batch membership: entry ordinals
  must cover `0..row_count-1` exactly once; bounded to 4,096 rows, 128
  entries, 1,024 withdrawn revisions, 8 MiB payload. Stores are borrowed;
  errors carry no source content.
- `raw_snapshot_source_rows`: `load_group(originals, derived, row_map_bytes,
  bundle_container_id, batch_container_id)` freshly binds one declared group
  (1..128 rows) through the existing private stores, reconstructs default raw
  representations, checks declared batch rows, and returns frozen rows with
  detached little-endian FP32 vector bytes in map order. Cooperative 30 s
  checks; per-group output bounded to 16 MiB.
- `raw_snapshot_dense`: `parse` (bounded normalized NPY validation under the
  fixed codec policy: 4,096 rows, (rows, 1024) `<f4`, finite normalized
  read-only storage), `build_partition` and `validate_partition` (byte
  equality with a fresh source-rebuilt payload). A partition is at most
  4,096 rows over at most 128 groups.
- `raw_snapshot_lexical`: `parse` (canonical `slaif-raw-lexical-v1` payload:
  4,096 rows, `partition_row` strictly sequential, strictly increasing
  ordinals, 100,000 terms/row and 250,000 total terms, 4,096-char/16,384-B
  terms, fixed derivations, 16 MiB payload), `build_partition` (fresh source
  groups analyzed with the current default technical analyzer) and
  `validate_partition`. `normalization_policy_id` must equal the canonical
  `embedding_vectors.POLICY_ID`.

## Absent in this slice (not implemented, not implied)

No snapshot writer/publisher, no snapshot reader/loader, no query path, no
principal/current-policy interface, no selection/directory/catalog/pinning,
no scoring, RRF or hybrid fusion, no BM25 index, no quality or readiness
interface, no ACL recheck endpoint, no public route. The existing canonical
manifest, row-map, corpus-program and representation modules are unchanged
and not replaced. Nothing here serves, scores or answers.

## Evidence: current versus historical

- This round ran NO local product, unit, integration, native, store, model or
  diagnostic process: static byte/hash/JSON/AST/diff and governance checks
  only, plus the unchanged normal hosted CI triggered by the report-head
  push (full unit and integration suites on Python 3.12 and 3.14 plus the
  three OAP jobs).
- The prior local proof is historical evidence for the exact source bytes:
  one corrected normal-layout 49-unit process and one source-row synthetic
  native journey passed on the assembly; the original 48-pass/1-fixture-import
  failure and its explicit test-only correction are preserved in the Root
  records. The inherited test-only exception is the explicit `importlib`
  load of the real existing structured-text fixture inside
  `tests/unit/test_raw_snapshot_membership.py` (no `sys.path`/`sys.modules`
  override); no further adaptation is authorized.
- Mock/synthetic store fixtures are not real routes, real models or hardware.
  Supplied DTOs, hashes, fingerprints and this byte transfer are not neural
  origin, current principal, rights, current-ACL or readiness proof.

## Trust and data boundaries

Source, query and snapshot payload content is untrusted data (S01–S05):
bounded parsers, ASCII/canonical JSON admission, no pickle, no traversal,
content-free errors, borrowed read-only stores. Membership and row
correspondence declarations are data, never authorization grants; ACL,
rights, withdrawal authority and current access remain owned by the
principal/scope machinery that does not exist yet in this slice. Rendered
indexing text is not original answer evidence. The explicit 4,096
snapshot-row and 128-group limits are preserved unchanged; the illustrative
20k capacity remains NOTQUALIFIED with no truncation or cap raise. No
human-owner referral behavior is introduced.

## Remaining 008 scope (later same-PR waves, strategy-activated)

Correspondence/program coverage and directory; immutable
publication/catalog/selection/pinning; actual dense/BM25/RRF/hybrid
dependencies; usable scoped query and current-policy integration; final
whole-008 criteria review. Model/tokenizer/runtime pinning and the
independent-tokenizer obligation remain architecture invariants; objective
014's authenticated principal boundary cannot waive these pre-scoring scope
checks. New direct or transitive dependencies: NONE (stdlib plus the already
locked NumPy).
