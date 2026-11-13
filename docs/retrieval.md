# Raw retrieval snapshot foundation and source construction (objectives 008-a, 008-b)

This document is the nonroutine retrieval reference for the bounded 008
foundation and source-construction slices. The routine coding context
remains unchanged; exact per-component contracts live in the byte-exact
transferred documents under [docs/parallel/](parallel/)
(`technical-analyzer-api.md`,
`raw-snapshot-membership-api.md`/`-design.md`,
`raw-snapshot-source-rows-api.md`/`-design.md`,
`raw-snapshot-dense-api.md`/`-design.md`,
`raw-snapshot-lexical-api.md`/`-design.md`,
`raw-snapshot-payload-format-map.md`,
`raw-snapshot-row-builder-api.md`/`-design.md`,
`raw-snapshot-files-api.md`/`-design.md`,
`raw-snapshot-program-coverage-api.md`/`-design.md`,
`raw-snapshot-directory-api.md`/`-design.md`).

## Provenance of the 008-a slice

Twenty-five files (142,322 bytes: five production modules, ten test files
— five unit and five integration suites — and ten docs/parallel contract
documents) were transferred byte-exact by Git-object read from the reviewed
local assembly commit SELF `96822ff4` (implementation `3eac764`) of the
parallel raw-foundation worktree, per the Root-owned index
`oap/reviews/008-a-foundation-components.json` (identical to
`audit/008-a-foundation-components-FINAL.json`, SHA-256
`e11bfb74…0633`). The immutable 008-a report carries a documented count
wording ("twenty test files"); per the Root reconciliation
(`oap/reviews/008-a-scoped-prefix-resolution.json`) the report is retained
unchanged and this current wording is corrected to the actual 25 = 5
production + 5 unit + 5 integration + 10 docs. No branch switch, cherry-pick
or ancestry merge of the candidate occurred; no other path was modified. The
candidate carries local Root review
(`oap/reviews/008-a-foundation-Root-review.json`), local admission
(`oap/reviews/008-a-foundation-local-admission.json`), an opposite peer
composition report (`oap/reviews/008-a-foundation-peer.json`, SHA-256
`e206819d…922f`) and its Root review, plus the approved normal-layout test
addendum. Those are provenance records, not canonical acceptance: whole-008
acceptance still requires current canonical CI, same-PR continuations and
Root review.

## Provenance of the 008-b slice

Twenty-one files (145,034 bytes: four production modules, four unit and
five integration suites, eight docs/parallel contract documents) were
transferred byte-exact by Git-object read from the reviewed local assembly
commit SELF `2da3d0df` (implementation `009044a`) of the parallel
program-directory-assembly worktree, per the Root-owned index
`oap/reviews/008-b-construction-components.json` (identical to
`audit/008-b-construction-components-FINAL.json`, SHA-256
`bb292ea9521afa66ee172ffbd89a81eeaa02fcb2e917711d6cfd53bdc1b1ddf9`). All
21 paths were absent at the 008 round base `0ef37069`; no branch switch,
cherry-pick or ancestry merge of the candidate occurred, and no other path
was modified. The candidate carries the Root review
(`oap/reviews/008-b-program-directory-source-review.json`), an opposite peer
review (`oap/reviews/008-b-program-directory-peer-review.json`), the
raw-correspondence source review
(`oap/reviews/008-b-correspondence-source-review.json`) and the bounded
source-composition gate resolution
(`oap/reviews/008-b-correspondence-journey-gate.json`), all per
`oap/reviews/008-b-root-records.json`. Two integration modules contain the
Root-approved existing-provider-import-only initialization; the copied final
prepared bytes are authoritative, not older leaf blobs. Those are provenance
records, not canonical acceptance: whole-008 acceptance still requires
current canonical CI, same-PR continuations and Root review.

## Actual callable foundation (008-a, unchanged)

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

## Actual callable construction layer (008-b, what exists now)

All four modules are importable package members; none is wired into the
CLI, a store lifecycle, a snapshot publisher or any caller in this slice.
None publishes, selects, serves, scores or answers; stores are borrowed and
deadlines are cooperative.

- `raw_snapshot_row_builder`: `build(originals, derived, declaration_bytes,
  groups, *, deadline_ms=30000)` constructs canonical v1 row-map DATA for
  explicitly selected whole batches. The declaration is canonical ASCII JSON
  (schema 1, kind `slaif-raw-row-map-build-declaration-v1`); groups are a
  sorted tuple of unique `(bundle_id, batch_id)` pairs without repeated batch
  IDs. Every batch is freshly validated and every row bound to its actual
  bundle and stored batch position, with a second fresh source-row
  validation per complete group; duplicates and inconsistent inputs refuse
  rather than select a winner. The result carries map bytes and hash, row
  and group counts, `SUPPLIED_UNVERIFIED` execution origin and
  `NOT_QUALIFIED` qualification; empty groups produce empty DATA without
  reading stores. Limits: 128 groups and partitions, 4,096 rows, 16 MiB map
  bytes, subject to inherited source and batch limits; the deadline is
  cooperative and includes final result construction.
- `raw_snapshot_files`: `validate_files(originals, derived, core_bytes,
  files)` accepts a sorted tuple of exact `(path, bytes)` pairs and returns
  frozen `BoundSnapshotData` only after complete descriptor checks, fresh row
  and membership binding and fresh source-backed dense and lexical
  validation. It establishes file-set correspondence to declared historical
  source and stored normalized vectors and current terms; ordinary failures
  are content-free `SnapshotFilesError`; core query and qualification fields
  remain declarations; the operation has cooperative bounds, not hard RAM or
  IO preemption.
- `raw_snapshot_program_coverage`: `build(originals, derived, program_bytes,
  declaration_bytes, completion_bytes, *, deadline_ms=30000)` returns a
  frozen `CoveredRowMap`. The completion is canonical ASCII JSON (schema 1,
  kind `slaif-raw-program-output-selection-v1`) whose outputs cover the
  program batches in index order with distinct containers. The source program
  is freshly validated (bounded 4,096 rows, 128 batches, 128 sources;
  default representation and batch policies; smaller valid limits
  supported), each supplied batch and bundle is checked against the actual
  program slice, the map is checked by chunk identity including the original
  batch row index, and the program is validated again before returning.
  `coverage` is `COMPLETE_SELECTED_PROGRAM`, execution origin
  `SUPPLIED_UNVERIFIED`, qualification `NOT_QUALIFIED`; revalidation detects
  persistent changes, not an intervening change restored before
  observation; the caller must separately establish publication and
  authorization.
- `raw_snapshot_directory`: `load_directory(originals, derived, store_root,
  snapshot_id)` reads the fixed private `snapshots/<digest>/.core.json`
  layout and returns detached `BoundSnapshotData` after fresh complete source
  validation, enforcing the private directory bounds (owner, mode, ancestor
  and linked-entry checks, bounded walk). Inputs are internal operator
  configuration; ordinary refusals are content-free `DirectoryError`;
  borrowed stores are neither closed nor written. Pathnames, IDs and inode
  identities establish software directory DATA correspondence only, not
  permission or filesystem immutability; cooperative bounds do not preempt
  blocked operating-system calls.

## Absent as of 008-b (not implemented, not implied)

No snapshot writer/publisher, no FileBuilder (it travels in a later wave
with publication/selection), no snapshot reader/loader beyond the directory
DATA reader, no query path, no principal/current-policy interface, no
selection/catalog/pinning, no operator or CLI, no scoring, RRF or hybrid
fusion, no BM25 index, no quality or readiness interface, no ACL recheck
endpoint, no public route. The 008-b construction modules are DATA
producers and validators for selected cuts; they do not publish or select a
snapshot. The existing canonical manifest, row-map, corpus-program and
representation modules are unchanged and not replaced. Nothing here serves,
scores or answers.

## Evidence: current versus historical

- This round (008-b) ran NO local product, unit, integration, native,
  store, model or diagnostic process: static Git/hash/AST/JSON/metadata and
  governance checks only, plus the unchanged normal hosted CI triggered by
  the report-head push (full unit and integration suites on Python 3.12 and
  3.14 plus the three OAP jobs).
- The prior local proof is historical evidence for the exact source bytes:
  for 008-a, one corrected normal-layout 49-unit process and one source-row
  synthetic native journey passed on the assembly; the original
  48-pass/1-fixture-import failure and its explicit test-only correction are
  preserved in the Root records. For 008-b, one specifically approved
  program-directory synthetic journey (7 rows / 1 batch / 1 partition /
  1 group; 2 native processes, 0 generators, 29 bundle loads, 4.90 s wall)
  passed on the assembly and satisfies only the bounded named
  source-composition gate — not all batch shapes, physical atomicity,
  current-policy behavior or neural quality. The historical first
  correspondence unit receipt omitted a thread field; the separately
  Root-authorized corrected 20-unit process passed. The earlier leaf
  row-builder peer pre-run provenance remains UNPROVEN and is never
  backfilled. The inherited test-only exception is the explicit `importlib`
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
principal/scope machinery that does not exist yet in the 008 slices.
The 008-b construction results are selected-cut DATA with `SUPPLIED_UNVERIFIED`
execution origin and `NOT_QUALIFIED` qualification; `COMPLETE_SELECTED_PROGRAM`
describes the selected data cut only. Neither the data cut nor the private
directory layout establishes rights, precision, permission, filesystem
immutability or readiness. Rendered indexing text is not original answer
evidence. The explicit 4,096 snapshot-row and 128-group limits are preserved
unchanged; the illustrative 20k capacity remains NOTQUALIFIED with no
truncation or cap raise. No human-owner referral behavior is introduced.

## Remaining 008 scope (later same-PR waves, strategy-activated)

FileBuilder and immutable
publication/catalog/selection/pinning (FileBuilder tests need
publication/selection and travel in that later wave); actual
dense/BM25/RRF/hybrid dependencies; usable scoped query, operator and
current-policy integration; scoring; final whole-008 criteria review. The
transferred construction modules do not close those interfaces.
Model/tokenizer/runtime pinning and the independent-tokenizer obligation
remain architecture invariants; objective 014's authenticated principal
boundary cannot waive these pre-scoring scope checks. New direct or
transitive dependencies: NONE (stdlib plus the already locked NumPy).
