# Raw retrieval snapshot foundation, source construction, publication reader and raw scoring (objectives 008-a, 008-b, 008-c, 008-e)

This document is the nonroutine retrieval reference for the bounded 008
foundation, source-construction and publication-reader slices. The routine
coding context remains unchanged; exact per-component contracts live in the
byte-exact transferred documents under [docs/parallel/](parallel/)
(`technical-analyzer-api.md`,
`raw-snapshot-membership-api.md`/`-design.md`,
`raw-snapshot-source-rows-api.md`/`-design.md`,
`raw-snapshot-dense-api.md`/`-design.md`,
`raw-snapshot-lexical-api.md`/`-design.md`,
`raw-snapshot-payload-format-map.md`,
`raw-snapshot-row-builder-api.md`/`-design.md`,
`raw-snapshot-files-api.md`/`-design.md`,
`raw-snapshot-program-coverage-api.md`/`-design.md`,
`raw-snapshot-directory-api.md`/`-design.md`,
`raw-snapshot-publication-api.md`/`-design.md`,
`raw-snapshot-selection-api.md`/`-design.md`,
`raw-snapshot-catalog-api.md`/`-design.md`,
`raw-snapshot-pin-api.md`/`-design.md`,
`raw-snapshot-file-builder-api.md`/`-design.md`).

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
prepared bytes are authoritative, not older leaf blobs. The immutable 008-b
report records an AST count of 11 new Python files; the slice transferred
13 (4 production + 4 unit + 5 integration). Per the Root clarification
(`oap/reviews/008-b-scoped-prefix-resolution.json`) the report is retained
unchanged, all 13 files were Root-verified to parse, and this current
wording records the count limitation. Those are provenance records, not
canonical acceptance: whole-008 acceptance still requires current canonical
CI, same-PR continuations and Root review.

## Provenance of the 008-c slice

Twenty-five files (200,027 bytes: five production modules, ten test files
— five unit and five integration suites — and ten docs/parallel contract
documents) were transferred byte-exact by Git-object read from the reviewed
local assembly commit SELF `4e428b17` of the parallel file-builder-assembly
worktree, per the Root-owned index
`oap/reviews/008-c-publication-reader-components.json` (identical to
`audit/008-c-publication-reader-components-FINAL.json`, SHA-256
`441c130f90cf5a4bc80e5815b12987be90e7a46564661b82d4086a5b7fc91355`). All
25 paths were absent at the 008-c round base `d9ef6b4c`; no branch switch,
cherry-pick or ancestry merge of the candidate occurred, and no other path
was modified. The candidate carries the three source reviews
(`oap/reviews/008-c-publication-selection-source-review.json`,
`oap/reviews/008-c-catalog-pin-source-review.json`,
`oap/reviews/008-c-file-builder-source-review.json`) and the historical
peer Root reviews
(`oap/reviews/008-c-file-builder-historical-peer-root-review.json`,
`oap/reviews/008-c-pin-historical-peer-root-review.json`),
together with the terminal 008-b CI, scoped-prefix resolution and timing
records, all per `oap/reviews/008-c-root-records.json` (index 3,040 B; nine
records, 37,297 B). The FileBuilder historical peer pre-run provenance
remains UNPROVEN and is never backfilled; the pin peer proof's old-author
RAYON-missing/reconstructed-stdout limits are retained separate from the
Root fully bounded FD-reuse proof. Those are provenance records, not
canonical acceptance: whole-008 acceptance still requires current canonical
CI, same-PR continuations and Root review.

## Actual callable foundation (008-a, unchanged)

All five modules are importable package members; none has a CLI or
application entrypoint (the later 008-c file-builder and catalog modules
call the 008-a membership, source-rows, dense, lexical, rows and
technical-analyzer modules as libraries).

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

## Actual callable construction layer (008-b, unchanged)

All four modules are importable package members; none has a CLI or
application entrypoint (008-c's publication, selection, pin and file-builder
modules call the directory and files modules as libraries). None publishes,
selects, serves, scores or answers; stores are borrowed and deadlines are
cooperative.

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

## Actual callable publication layer (008-c, what exists now)

All five modules are importable package members with explicit interlibrary
callers within this slice (file-builder → rows/membership/dense/lexical/
manifest; publication → files/manifest/directory; selection →
directory/publication; catalog → directory/source-rows/dense; pin →
directory/publication/selection). None has a CLI or application entrypoint,
and none serves, scores or answers a query; stores are borrowed and
deadlines are cooperative.

- `raw_snapshot_file_builder`: `build(originals, derived, row_map_bytes,
  active_bundle_ids, withdrawn_revisions, query_context_bytes,
  *, deadline_ms=30000)` constructs the unqualified raw snapshot DATA file
  set (row map, fresh whole-batch membership, per-partition dense and
  lexical payloads) from the borrowed source stores, preserving fresh
  membership/payload/manifest/file binding and the declared
  `slaif-raw-snapshot-query-context-v1` (space and definition fingerprints
  must match the row map), and independently revalidates the complete file
  set through `raw_snapshot_files.validate_files` before returning a frozen
  `BuiltSnapshotFiles` (`SUPPLIED_UNVERIFIED` execution origin,
  `NOT_QUALIFIED` qualification). It never publishes or qualifies. Limits:
  128 active bundles, 1,024 withdrawn revisions, 128 groups, 258 files,
  96 MiB total payload, 256 KiB core; the deadline is cooperative and
  includes final construction; ordinary failures are content-free
  `SnapshotBuildError`.
- `raw_snapshot_publication`: `publish_directory(originals, derived,
  store_root, core_bytes, files)` validates the complete source-backed file
  set before any filesystem mutation, stages a private candidate, fsyncs,
  and renames once without replace (`created=True` exactly once;
  `created=False` when the snapshot ID already exists — no replacement),
  then freshly reads the detached DATA back through the directory reader.
  Cooperating writers serialize on the namespace lock under a 30 s
  cooperative deadline; failures are content-free `PublicationError` with
  the explicit `publication_may_exist` uncertainty after an attempted
  rename, and unknown descriptor-close outcomes surface as non-retryable
  `CleanupPendingError`. Publishing grants no authority.
- `raw_snapshot_selection`: `parse_pointer` (canonical
  `raw-snapshot-selection-data-v1` bytes: schema 1, generation
  1..2^63-1, `sha256:<hex64>` snapshot ID), `read_selected_data` and
  `compare_and_select_data` (exact expected-pointer compare-and-select with
  generation increment, atomic `current.json` replace, fresh source-
  validated candidate load under the namespace lock, 1..120,000 ms
  cooperative deadline). `SelectionError.selection_may_have_changed` flags
  post-replace uncertainty; selection has no serving or retention authority.
- `raw_snapshot_catalog`: `load_catalog(originals, derived, store_root,
  snapshot_id, *, deadline_ms=120000)` freshly converts one named snapshot
  into row/declaration/chunk/source/scope/rendered/vector/term
  correspondence over the borrowed stores (32 MiB non-vector retention
  budget, 120 s cooperative deadline), ends with a fresh directory re-read
  equality check and a `catalog_id` identity digest, and establishes no
  query authority. Ordinary refusals are content-free `CatalogError`.
- `raw_snapshot_pin`: `PinOwner.acquire_selected_data` /
  `RetirementOwner.acquire_unselected_data` (plus `check`, `close` and the
  context manager) hold a source-validated DATA identity under a shared or
  exclusive target lock with creator-only cleanup and numeric descriptor
  no-retry. They perform no removal, no authorization, no retention or
  unlink decision; the owners are final (not subclassable); ordinary
  refusals are content-free `PinError`.

## Actual callable scoring layer (008-e, what exists now)

Four private DATA scoring modules import over the 008-c catalog and row
layers. The lexical and hybrid paths require the exact pinned backends
(NumPy 2.5.4, bm25s 0.2.14, SciPy 1.18.1) and refuse on absence or
mismatch. None has a CLI, application or serving entrypoint; all score
unqualified snapshot DATA and grant no authorization.

- `raw_dense_search.search(originals, derived, store_root, snapshot_id,
  query_payload, *, query_space_id, query_definition_fingerprint,
  query_policy_id, query_execution_fingerprint, grants,
  restrictions=None, k=60, partition_cap=60, deadline_ms=120000)`: the
  query is exactly 4,096 bytes of finite normalized 1024-D
  little-endian float32 (norm tolerance 1e-4) and the four declared
  encoder IDs must equal the snapshot core embedding fields including
  the exact query execution domain. Authorized partitions select rows
  before any dot-product scoring; ranking is descending float32 score
  then chunk/revision/representation ID with per-partition then global
  caps (exact integers 1-60). Frozen `DenseResult` carries
  eligible/selected/returned, both cap flags, `SUPPLIED_UNVERIFIED`
  origin and `NOT_QUALIFIED` qualification; failures are content-free
  `DenseSearchError` under a cooperative deadline.
- `raw_lexical_search.search(originals, derived, store_root, snapshot_id,
  text, *, grants, restrictions=None, k=60, partition_cap=60,
  deadline_ms=120000)`: one ephemeral Lucene BM25 scorer
  (method/idf_method=lucene, k1=1.5, b=0.75, delta=0.5, float32/int32,
  numpy backend) over the stored rendered terms of the authorized union,
  using the existing default technical analyzer (prefixed ID compared to
  the core fingerprint); no scorer is retained. Finite limits: 8,192
  query codepoints, 2,048 query terms, 200,000 stored allowed terms,
  100,000 vocabulary terms, 200,000 postings, 4,000,000 query-document
  work units; content-free `LexicalSearchError`.
- `raw_rank_fusion.fuse(originals, derived, store_root, snapshot_id,
  query_id, *, dense, lexical, grants, restrictions=None, k=60,
  deadline_ms=120000)`: independently captured supplied
  `Ranking`/`Entry` lists (at most 60 contiguous entries per modality,
  no duplicate row or representation); every candidate must match the
  actual catalog and pass `reader_allows` before any contribution.
  Equal-weight RRF sums `1/(60+rank)` per supplied modality; raw scores
  are never added. Both-unavailable refuses, one-unavailable marks
  `degraded`; frozen `FusionResult` carries candidate/overlap/returned
  counts, `ranking_origin` `SUPPLIED_UNVERIFIED`, `NOT_QUALIFIED` and
  `global_cap_applied`.
- `raw_hybrid_search.search(originals, derived, store_root, snapshot_id,
  text, query_payload, *, the four declared encoder IDs, grants,
  restrictions=None, dense_k=60, lexical_k=60, partition_cap=60, k=60,
  deadline_ms=120000)`: runs the actual dense, lexical and fusion stages
  in sequence on one named snapshot under one cooperative deadline,
  loading the complete catalog before the engines and again after
  fusion (eight catalog loads per successful journey); any stage failure
  refuses the whole request with content-free `HybridSearchError`.
  Frozen `HybridResult` binds kind `raw-hybrid-query/v1`,
  snapshot/catalog IDs, both query hashes, all four declared encoder
  IDs, authority SHA-256 over canonical JSON `[grants, restrictions]`
  and the four cap values.

The keyword-only `trace` parameter (default `False`, exact boolean)
forwards to the one dense and one lexical search used by fusion; when
false the nested trace values stay `None`, when true the private lower
traces are admitted, checked against the actual results, request,
counts and returned identities and linked before fusion, with no new
top-level field and unchanged `query_id` preimage. Trace records carry
fixed defaults `input_origin` `SUPPLIED_UNVERIFIED`, `qualification`
`NOT_QUALIFIED`, dense `authorization_status`
`SUPPLIED_SCOPE_CHECKS_ONLY` and `execution_status` `NOT_ATTESTED`:
supplied origins and unattested execution are not actual
authentication, neural provenance or current rights.

Query-execution binding is declared data, not observed execution: the
payload and the four encoder IDs must equal the snapshot core's
declared embedding fields exactly, and mismatch, source/catalog
change, invalid or oversize input, deadline overrun or backend mismatch
refuse the whole request fail-closed. Grants/restrictions are static
trusted-caller data; None grants or unknown source version deny.

Still absent after 008-e: the completion-locator/construction wrapper
join, any usable pinned-query or scoped query entrypoint, the
application/serving constructor and current-service integration,
principal/current-policy enforcement and every qualification gate.
The private directory, selected-data, catalog and pin readers remain
the only readers; nothing here serves, scores an answer or authorizes
access, and no blanket no-reader claim is made for the private layers.

## Absent as of 008-c (not implemented, not implied)

No completion-locator or construction wrapper yet, no snapshot
reader/loader beyond the directory DATA reader, no query path, no
principal/current-policy interface, no operator or CLI, no scoring, RRF or
hybrid fusion, no BM25 serving index, no quality or readiness interface, no
ACL recheck endpoint, no public route. The 008-c layer is private DATA
publication, expected-pointer selection, source-backed cataloging, lifetime
pinning and unqualified DATA construction: it does not serve, score or
answer, and it grants no authorization, retention, unlink or deletion. The
existing canonical manifest, row-map, corpus-program and representation
modules are unchanged and not replaced. Nothing here serves, scores or
answers.

## Evidence: current versus historical

- This round (008-c) ran NO local product, unit, integration, native,
  store, model or diagnostic process: static Git/hash/AST/JSON/metadata and
  governance checks only, plus the unchanged normal hosted CI triggered by
  the final-head push (full unit and integration suites on Python 3.12 and
  3.14 plus the three OAP jobs).
- The 008-b report-head CI is recorded terminal at `d9ef6b4c` per
  `oap/reviews/008-b-ci-terminal.json`: run 43362986520, all five jobs / all
  78 steps SUCCESS with the full normal suites on both Product 3.12/3.14
  legs (1,836 unit + 838 integration per leg); it is canonical for the
  008-b head only, not for this 008-c head.
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
  Root-authorized corrected 20-unit process passed. For 008-c, the Root
  separate bounded fault proofs support component admission; the FileBuilder
  historical peer pre-run provenance remains UNPROVEN and is never
  backfilled; the pin peer proof's old-author RAYON-missing /
  reconstructed-stdout limits are retained separate from the Root fully
  bounded FD-reuse proof. The earlier leaf row-builder peer pre-run provenance remains
  UNPROVEN and is never backfilled. Historical primitive proof scopes and
  path metrics are not rerun and are not reinterpreted as hardware
  qualification. The inherited test-only exception is the explicit
  `importlib` load of the real existing structured-text fixture inside
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
evidence. The 008-c publication, selection, catalog and pin results are
private DATA and lifetime coordination, not authorization, retention,
unlink, ABA, power-loss, hard-preemption or model-readiness proof:
publication renames once without replace and reports
`publication_may_exist` uncertainty after an attempted rename; selection
replaces `current.json` only against the exact expected pointer and reports
`selection_may_have_changed` uncertainty after an attempted replace; pin
performs no removal; unknown descriptor-close outcomes surface as
non-retryable `CleanupPendingError`. The explicit 4,096 snapshot-row,
128-group and 96 MiB build-payload (catalog 32 MiB non-vector) limits are
preserved unchanged; the illustrative 20k capacity remains NOTQUALIFIED
with no cap raise or silent truncation. No human-owner referral behavior
is introduced.

## Remaining 008 scope (later same-PR waves, strategy-activated)

Completion-locator/construction wrapper join over the 008-c
publication-reader layer and the 008-e scoring modules; usable scoped
query, operator and current-policy integration; the application/serving
constructor and pinned-query entrypoint; final whole-008 criteria
review. The transferred scoring modules do not close those interfaces:
no construction/query join, no current-service path and no current
principal or policy enforcement exist yet. Model/tokenizer/runtime
pinning and the independent-tokenizer obligation remain architecture
invariants; objective 014's authenticated principal boundary cannot
waive these pre-scoring scope checks. Direct dependencies after 008-e:
the already locked set plus exactly the two pinned additions bm25s
0.2.14 and SciPy 1.18.1 (no old package version removed or changed, no
lock regeneration); otherwise stdlib plus the already locked NumPy.
