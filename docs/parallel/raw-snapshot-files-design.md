# Fresh raw snapshot file-set correspondence — strategic D0 contract

Status: FINAL DESIGN, activation requires its finalized order and live reconciliation.
H full-MVP/parallel; A11.5/12.1/12.2; I core/row codecs, actual SourceRows981896,
lexicalb2c619/dense57fe/peer6aad, membership892ef2/605a/peer0d82 and payload format map;
E there is no single consumer checking the complete actual file set against the same core
and fresh original-backed sources. DHA NONE. Independent local future008 work under the
existing replan; canonical007 and actual qualification gates remain unresolved.

This is a bounded consumer of EXACT FILE BYTES, not a filesystem reader, publisher, current
pointer, retained reader, search engine or Ready authority. Later directory IO must supply
verified bytes under its own path/descriptor/stability protocol. The filesystem inventory
e03a establishes source/local syscall facts only; no deployment filesystem is qualified.

Add only new raw_snapshot_files.py, unit/actual tests/API/exact design/order. Predecessor
code, schemas, payload formats, policies, stores, original inputs, dependencies and CI remain
unchanged. Base/prerequisite topology is finalized in the work order; no hidden adaptation.

## API, input and immutable data

validate_files(originals, derived, core_bytes, files) returns frozen BoundSnapshotData with
snapshot_id, exact core_bytes, freshly bound RawRowMap, fresh Membership, and an immutable
tuple of BoundPartition in core partition order. Each partition holds its ID, subset-map
hash, fresh immutable DensePartition and LexicalPartition. No store/FD/worker/permission
handle or mutable matrix/dict/list alias. Dataclasses are forgeable DATA, not capabilities.
Ordinary errors are content-free SnapshotFilesError; original non-Exception propagates.

Require exact OriginalStore and derived_store.Store and exact nonempty core bytes within
the actual core codec's262144 ceiling. files is an exact tuple of2..258 exact (path, bytes)
tuples, ordered lexicographically by unique exact path. No dict/mapping callback, generator,
path object, open file, ndarray, parsed DTO or caller source provider. The paths are only
the core's closed syntactically admitted relative names; do not resolve/read them here.

Freshly parse the core. Before ANY store access require the actual supplied file set equals
its file descriptors EXACTLY, with no extra/missing/shared alias; each actual byte size and
SHA256 equals its descriptor. Apply the core's per-role/total96MiB file-byte limits and
the actual payload codec limits as well. Core bytes are additional, not part of its own
descriptor sum. Check known counts/sizes before hashing/retaining another item; input exact
bytes are immutable. Build only an internal bounded lookup from admitted tuples.

Reject core.validation.state failed. An unproven or passed string is not a successful fresh
validation or permission; passed is NEVER used to skip checks. This operation does not write
or change that declaration or core hash. New immutable snapshot ID is the actual core codec's
SHA256(core_bytes) identity; payloads never gain a circular assigned snapshot self-hash.

Global bounds: core<=256KiB, actual files<=258/96MiB, rows<=4096, partitions<=128,
membership active bundles<=128 and distinct (bundle_container_id,batch_container_id) groups
across all rows<=128. These are conservative supported-component bounds, not promises every
core-format maximum builds within a test budget. Existing per-payload term/text/NPY/native
limits remain exact. Total operation cooperative60s, checked before/after each helper and
partition; no hard IO preemption or raised lower helper deadline/memory limit. Tests retain
outer120wall/30CPU/1GiB. Lower helpers may transiently load their existing96MiB envelopes;
do not claim the96MiB descriptor sum is total process RAM.

## One core, one exact mapping, fresh original correspondence

1. Select the one row-map and one membership byte string by the actual core's declared
   paths/roles. Call actual raw_snapshot_rows.bind(core_bytes,map_bytes), not a forged parsed
   mapping. It verifies core/map sizes/hash/headers/partitions/subsets/row counts, active vs
   withdrawn and exact declared corpus execution set. The core query execution/policy fields
   remain independent DECLARATIONS; no loaded query encoder is observed by this API.
2. Call actual raw_snapshot_membership.validate(originals,derived,core_bytes,map_bytes,
   membership_bytes). This covers every declared active source INCLUDING zero selected rows,
   exact historical withdrawals, and actual original-backed bundle/source/policy/scope/entry
   correspondence. Input active inventory is caller-selected, not proof of external inventory
   completeness or current withdrawal authority. Do not replace this with parse/bind alone.
3. Require core.analyzer.fingerprint equals the actual current default
   technical_analyzer.analyzer_id(Policy()) with exact sha256: prefix verified/stripped.
   Check even for zero partitions. Core backend/version strings already have closed codec
   values; matching them is not installed bm25s/SciPy runtime or BM25 scoring qualification.
4. For every declared partition in canonical core order, select its actual dense and lexical
   bytes via exact closed roles/schemas. Use actual raw_snapshot_dense.validate_partition
   with actual descriptor SHA and actual raw_snapshot_lexical.validate_partition(originals,
   derived,map_bytes,partition_id,payload_bytes), which
   independently rebuild from original-backed stored groups/current rendered source/default
   analyzer and compare actual bytes. No caller matrix, supplied whole validator or cached
   BoundGroup substitutes for these calls. Do not catch refusal and fall back to parse.
5. Independently cross-check returned partition ID, subset-map SHA, space, definition and
   normalization against the SAME core/map/partition. Dense row_count and exact container
   bytes/hash match descriptor; codec policy equals actual dense.POLICY.fingerprint().
   Lexical bytes/hash match descriptor, row count matches partition, representation/chunk
   policy and current analyzer match core/map. Its rows' ordinal/partition_row/chunk/
   representation/rendered IDs equal the corresponding actual map rows in order. Dense
   build already selects actual normalized stored vectors into that order; lexical rebuild
   analyzes the SAME raw title/headings/body representation. No reordering one side alone.
6. Return fresh immutable results only after every file/partition/source check and deadline.
   No partition omission, partial result or validation of only a caller-authorized subset
   is part of this whole-data operation. Empty row map/zero partitions still requires BOTH
   row-map and membership files; active zero-selected-row membership sources still load.
   A withdrawn-only/entirely empty selection is permitted with correctly declared empty data.

Use the exact frozen format map: source_membership schema/kind slaif-raw-source-membership-v1;
row_map schema/kind slaif-raw-row-map-v1; lexical_terms descriptor schema
slaif-raw-lexical-terms-v1 maps intentionally to internal JSON kind slaif-raw-lexical-v1;
dense schema slaif-normalized-fp32le-d1024-npy-v1 is actual non-pickle NPYv1 C-order<f4/1024.
Do not rename formats or accept executable/backend-native serializers to hide differences.

SourceRows/typed batch checks prove stored normalized-vector/declared-source correspondence,
not authentic neural execution, historic token execution or FP16 quality. A qualification ref
in the core is only a reference. Query policy/execution compatibility with actual resident
CPU query service, measured CPU/GPU parity, current principal/source authorization and
restrictions, retrieval smoke/indexes, filesystem integrity at consumption, publication/CAS,
retention and target readiness remain explicit future gates. This DATA result is not an
authorization token or Ready proof and cannot silently waive those gates.

## Required finite evidence

Actual small positive uses original/derived stores and existing SourceRows fixture with
permuted batch order, actual current lexical build, actual dense build, actual membership,
and a constructed core whose every descriptor size/hash/subset/header matches those actual
bytes. Full validate result preserves exact raw normalized vector bytes and term/row order;
ID equals core hash, stores remain usable, nested outputs detached/frozen. Forbid Popen,
publication and writes during validate_files; synthetic native fixture construction may
occur beforehand. One existing source with zero selected rows and empty/tombstone-only
snapshot exercise complete inventory beyond row presence.

Negatives: missing/extra/duplicate/unsorted/name/type/oversized files or wrong hash/size
BEFORE store access; correct-byte-hash but wrong normalized dense row order; correct-byte-
hash but altered canonical terms; membership/core inventory mismatch; changed original or
actual stored vector; mixed space/definition/map subset/analyzer/policy/corpus execution.
Update descriptor/core hashes in semantic-corruption cases so they reach the intended fresh
semantic comparison rather than failing only the outer digest. Current core validation
passed with well-shaped declarations cannot make corrupted actual payload pass. Refuse
invalid store types; a closed store must refuse when actual source/store loading is needed.
An entirely empty inventory needs no store IO: type admission alone there is not a claim of
live store ownership or lifecycle qualification. Do not invent a new global store registry,
change OriginalStore.close or add filesystem probes solely for that empty-data case. Never
close borrowed stores or return partial accepted partitions on failure.

One ORIGINAL narrow cross-file/compatibility guard control with actual stored fixtures and
only ONE relevant comparison removed in an owned temporary in-memory source. For example,
otherwise valid file set with core analyzer fingerprint changed and core hash recomputed:
original refuses; omitting only core-to-current-analyzer equality admits mismatched declared
core while actual source/dense/lexical rebuilds still run. Restore/original again refuses.
Proves selected DATA consistency only, not rights or secure loader authority. No fake whole
source/validator/registry, product disk patch or shared fixture modification.

Run focused new units/actual cases plus relevant core/row/membership/lexical/dense parser
units; existing unchanged predecessor actual checks may reuse verified evidence where new
whole composition already exercises them. Separate duplicate test basenames/worktrees and
known costly cases, no gratuitous full suite or cap relaxation/skip/aggregate retry. Exact
source/order/design/clean scope, hashes, retained logs, measured read set, setup failures and
strongest counterargument. Fresh affected peer and later exact current canonical integration/
required CI remain mandatory. No models/framework/Tensor/GPU/driver/install/download/network/
service/credential/real corpus/CI/law/ARCH mutation, mainmerge/release/deploy or FIFO replay.
