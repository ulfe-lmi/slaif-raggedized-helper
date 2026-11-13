# Fresh raw snapshot source membership — strategic D0 contract

Status: FINAL DESIGN, INERT until a finalized work order and live dependency reconciliation.
Provenance: H activated full-MVP and parallel mandate; A7/8/11.5/12.1/13.2/21.2 original
evidence, source revision membership and withdrawal; I core b7a2, row map09fe, SourceRows981896,
lexicalb2c619/dense57fe and finite combined peer6aad; E the core requires a membership file,
but existing row-map binding cannot account for an active source with no selected rows.
DHA NONE. This does not activate canonical008 or resolve whole007.

The component establishes correspondence to a caller-selected inventory of actual stored
ingestion bundles, including sources with zero SELECTED rows. Existing ingestion bundles
themselves require chunks; this contract does not claim to support a chunkless ingestion
format. A source need not contribute any of its chunks to this snapshot. Membership is
immutable historical data, never a current access grant or proof that the caller selected
every source in an external corpus. Withdrawn IDs are explicit historical declarations;
this API cannot discover revocations or certify completeness of an external deletion list.

## API and dependency boundaries

Add only new raw_snapshot_membership.py, unit/actual composition tests and API/design/order.
Do not modify the frozen core, row map, SourceRows, stores, source schemas or payload codecs.
Use the existing actual ingestion_store.load(originals, derived, bundle_id), which revalidates
the complete immutable bundle against the original. No caller-provided source provider,
Validated/BoundGroup DTO, registry replacement or model result substitutes for fresh loading.

Public operations:

- parse(membership_bytes) returns frozen Membership with immutable original bytes, their bare
  SHA256, row-map SHA256, row count, detached frozen entries and withdrawn revision tuple.
  It performs DATA validation only, with no store/filesystem/process/model work.
- build(originals, derived, row_map_bytes, bundle_ids, withdrawn_revisions) freshly parses the
  map and loads each selected actual ingestion bundle once. Returns freshly constructed
  immutable Membership; stores are borrowed and remain usable after success or refusal.
- bind(core_bytes, row_map_bytes, membership_bytes) freshly parses all three declared formats
  and checks exact relationships below. It is DATA correspondence only, with no store IO.
- validate(originals, derived, core_bytes, row_map_bytes, membership_bytes) performs bind,
  then rebuilds with the declared exact bundle IDs and withdrawn list, requires exact byte
  equality, and returns the fresh rebuilt Membership. No parsed object is an authority token.

Ordinary errors become content-free MembershipError. Original non-Exception interruptions
propagate unchanged. No API publishes, closes stores, changes source state, reads current
policy, starts a tokenizer/model/process, accesses network or accepts arbitrary paths.

## Canonical closed format

Exact bytes, nonempty and <=8MiB. Canonical ASCII JSON, sort_keys=True, ensure_ascii=True,
separators comma/colon, allow_nan=False, no trailing LF. Reject duplicate/unknown/missing
keys, floats/constants/nonfinite values, bool-as-int, coercion, invalid Unicode, unsupported
nesting and excessive lists. All 64-hex values below are lowercase; prefixed IDs require
exact sha256: plus64hex. No selfhash, snapshot ID, core hash, timestamp, current generation,
policy epoch, permissions, readiness state or operational receipt is stored here.

Top-level exactly schema, kind, row_map_sha256, row_count, entries, withdrawn_revisions.
schema is exact int1; kind is slaif-raw-source-membership-v1; row_map_sha256 is the bare
SHA256 of the ENTIRE exact row-map bytes; row_count exact int0..4096. Entries is a list0..128
sorted strictly by revision_id. Withdrawn IDs are sorted unique prefixed IDs, at most1024,
disjoint from entry revisions. These are supported component bounds; the core's larger
possible source list does not promise that every format maximum is buildable by this leaf.

Each entry has exactly revision_id, extraction_id, bundle_container_id,
bundle_metadata_sha256, chunk_policy_fingerprint, source_scope_sha256, partition_id, scope,
ordinals. Revision/extraction/partition IDs are prefixed; bundle/container metadata and
chunk-policy/source-scope hashes are bare64hex. Distinct entries have distinct revision IDs
and distinct bundle IDs. V1 selects exactly ONE bundle/extraction per active revision;
multiple extractions for the same revision refuse rather than silently selecting one.

scope is the complete exact JSON-shaped provenance_records.Scope model_dump(mode='json')
from the freshly validated bundle: schema_version, document_id, revision_id, corpus, version,
labels, processing_approved, redistribution_rights. Validate exact fields/types/limits against
that existing schema, sorted unique labels, strict valid Unicode, processing_approved true,
scope.revision_id equal entry revision. No normalization silently changes admitted bytes.
For strict Pydantic tuple fields, explicit list-to-tuple conversion is permitted only after
exact list/scalar admission; serialize back to JSON lists and require exact equality.
The static fields are historic admission/classification, not live approval or license proof.

source_scope_sha256 is existing schema.fingerprint({kind:'embedding-source-scope-v1',
scope:scope}) with exact sha256: prefix checked and stripped. partition_id is the existing
schema.fingerprint({schema:1,corpus:scope.corpus,version:scope.version,labels:scope.labels}).
Use the existing canonical fingerprint implementation, not a different JSON spacing policy.
Parsing verifies these declared relationships, not that supplied scope is the actual source.

ordinals is sorted unique exact ints0..4095, at most4096, and may be empty. Across all entries
ordinals are disjoint and their union is exactly range(row_count), with no omitted or extra
global row. Each canonical encoded entry <=131072 bytes. Total encoded output <=8MiB;
reject before retaining a further entry/loading a subsequent bundle if budget is exhausted.
Return no mutable nested dictionary/list alias: detached scope_bytes and ordinal tuples are
acceptable; frozen descriptors must not wrap caller mutable structures.

## Fresh build and map correspondence

Require exact OriginalStore and derived_store.Store, bounded exact map bytes, bundle_ids
an exact tuple of0..128 unique bare64hex IDs sorted lexicographically, withdrawn_revisions
an exact tuple of0..1024 sorted unique prefixed IDs. Complete scalar/map admission precedes
store access. Empty selection requires an empty map. Nonempty map groups require all their
referenced bundles in selection; additional selected bundles may contribute zero rows.
Do not require every selected source to contribute a row, or every bundle chunk to be selected.

For each selected ID call actual ingestion_store.load. Derive revision/extraction/scope and
metadata SHA from its freshly validated result; use its actual chunk policy and exact existing
policy fingerprint. Check it equals row-map chunk_policy_fingerprint even for a selected
zero-row source. Existing bundle validation establishes original bytes/fragments/heading/
policy/receipts structurally; it does not rerun tokenization or certify historical neural work.

All map rows for this revision must reference THIS bundle ID and exact metadata SHA, actual
extraction, chunk policy, scope hash and static partition. Confirm every selected chunk ID is
in the actual bundle, with matching revision/extraction and policy. Construct ordinals from
those exact matching map rows, sorted numerically. A row referencing a different bundle for
the same revision refuses. A map row cannot escape this check by belonging to another entry.
Active entry revisions are disjoint from withdrawn declarations, and every map row is covered
exactly once. No batch/vector/lexical loading or token count/rendered ID recomputation is added
here: SourceRows and payload validators independently own those checks in a future full loader.

Do not retain full loaded bundles across iterations. Extract bounded scalar/scope/ordinal data,
check entry and aggregate budgets immediately, and release chunks/blocks/members before the
next load. One existing ingestion call can still consume its existing <=96MiB bundle envelope;
this outer API does not lower the helper's bound or promise hard memory/preemption limits.
Use cooperative30s checks before/after each load/entry and before return; blocked IO and lower
helper work are not hard-preempted. No retry, persistent cache or fallback to stale records.

## Declared core binding and fresh validation

bind first uses actual raw_snapshot_rows.bind(core_bytes,row_map_bytes). Require the core's
membership_path descriptor is exactly role/schema source_membership/slaif-raw-source-membership-v1,
with byte size and SHA matching the actual membership bytes. Membership map hash/count must
match actual map. Sorted entry revision IDs equal core.active_revisions INCLUDING zero-row
entries; withdrawn IDs exactly equal core.withdrawn_revisions. No active/withdrawn overlap.

For every entry require map chunk-policy equality. Its ordinals exactly equal all map rows
for that revision; each such row matches entry bundle ID/metadata/extraction/scope/partition.
No unknown revision or additional uncovered row. Empty membership plus empty map is allowed,
including a nonempty withdrawn list; active zero-row entries are also allowed. Their partitions
need not have dense/lexical descriptors because core partitions describe nonempty row sets.

validate performs the above then actual fresh build with the same ordered bundle selection
and declared withdrawals; exact bytes must match. A structurally valid forged scope or bundle
hash may parse/bind if all declarations agree, but fresh validation must refuse when actual
original-backed bundle differs. Output is fresh source-membership correspondence only.

## Required finite evidence and open gates

Meaningful pure tests cover closed/canonical/type/hash/order/ordinal/uniqueness/resource limits,
scope-to-partition/hash consistency, immutable results, zero rows/zero selected sources and
zero-selected-row active sources. bind tests use real core/map codecs and exact descriptor
bytes/hash, including source-withdrawal/active-list mismatch, unknown rows, wrong extraction/
bundle/scope/partition and row count/map digest. Passed declarations remain DATA only.

Actual tests use existing private actual originals/derived/bundle fixtures; select a proper
subset of a bundle's chunks and then zero of its chunks, demonstrating source membership is
not inferred only from row presence. Test fresh original corruption, wrong existing bundle,
different scope/metadata and omitted required bundle; restore only own fixture bytes. Borrowed
stores remain usable. Forbid Popen/publish during component calls; synthetic native fixture
construction before those calls remains allowed under the existing setup.

One original narrow declared-to-fresh correspondence control in owned temporary in-memory
source, with actual stores and only ONE relevant comparison omitted, must demonstrate the
precise guard; no whole proof callback, fake registry, shared fixture mutation or product patch.
Record exact source/control hashes, commands/results and strongest counterargument. Focused
new units/actual tests plus unchanged core/row50 and relevant ingestion/source checks; avoid
gratuitous full-suite or overlapping-count inflation. Fresh peer and current canonical
integration/CI remain required before stronger acceptance.

Each model-free test invocation: timeout120, AS1GiB, CPU30, five thread budgets1, no bytecode,
existing app Python and existing synthetic native0.21 fixture only. No dependency/install/
network/framework/Tensor/model/GPU/driver/service/credential/real-corpus action. Actual file
binder/full loader, current policy/ACL/withdrawal authority, directory publication/current-CAS,
reader retention/deletion, search/BM25/fusion, precision/neural/hardware/license/held-out/visual/
ICA/fullMVP gates remain open. No legal exception, release or deployment authority is created.
