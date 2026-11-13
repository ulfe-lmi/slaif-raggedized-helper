# Raw snapshot core manifest — Root D0 contract

Status: FINAL bounded format leaf. Elaborates architecture11.5/12 without changing it. This implements a pure codec for declared manifest data. It does NOT validate actual files, source truth, authorization, index correspondence, retrieval smoke, qualification, publication, pointers or reader retention. Those later gates must not be inferred from a valid record or its hash. Source inventoryf73c separates old retrieval330e and later store/codec b982; no integration is implied.

Provide new raw_snapshot_manifest.py with parse(core_bytes) returning a frozen RawSnapshotManifest. Public state consists of canonical immutable core_bytes, snapshot_id, frozen file/partition descriptors and immutable source revision tuples. No caller-owned mutable dictionary/list alias, arbitrary deserializer, filesystem, network, process or framework operation. Input is exact bytes, nonempty and at most262144 bytes. Canonical ASCII JSON is sort_keys=True, ensure_ascii=True, separators=(comma,colon), allow_nan=False, no trailing LF. Reject duplicate keys, floats/nonfinite numbers, coercion, unknown/missing keys, invalid Unicode, excessive structure and bool-as-int. Ordinary errors are content-free ManifestError; original non-Exception propagates unchanged. Validation is bounded by input and finite field/list limits.

## Exact schema1 core

Exactly these top-level keys:
- schema: exact integer1.
- kind: slaif-raw-snapshot-core-v1.
- representation: raw.
- embedding: exact keys space_id, definition_fingerprint, query_policy_fingerprint, query_execution_fingerprint, corpus_execution_fingerprints, normalization_policy_id, precision_qualification_ref. space/query-policy/query-execution and corpus-execution values are bare lowercase64hex; definition is sha256: plus64hex. Corpus execution list is sorted unique, at most128, nonempty for a nonempty snapshot. normalization_policy_id equals the existing embedding_vectors.POLICY_ID. precision_qualification_ref is null or a prefixed sha256 ID; a reference is a declaration, not proof of parity.
- analyzer: exact keys fingerprint, backend, bm25s_version, numpy_version, scipy_version. fingerprint is bare64hex; fixed values bm25s-lucene,0.2.14,2.5.4,1.18.1 respectively. This version records the selected authorized-union reference, never qualifies backend-native persistence or actual installed packages.
- chunk_policy_fingerprint and representation_policy_fingerprint: each bare64hex.
- sources: exact keys active_revisions and withdrawn_revisions, each sorted unique list of prefixed sha256 IDs, at most1024 each, disjoint. Actual source objects, membership and deletion coverage still require independent fresh validation.
- row_count: exact integer0..4096. The bound matches existing dense/global lexical reference limits; architecture's20k example is not a current throughput/capacity claim.
- row_map_path and membership_path: canonical relative paths naming the single row_map and source_membership files below.
- files: sorted by path, unique paths, at most258 descriptors. Each has exactly path,role,schema,bytes,sha256. bytes is exact nonnegative integer; sha256 bare64hex. Roles and declared schema strings are closed below; no executable/pickle/backend-native file role.
- partitions: sorted unique by partition_id, at most128. Each has exactly partition_id,row_count,row_map_sha256,dense_path,lexical_path. partition_id is prefixed sha256 ID, row_count exact integer1..4096, row_map_sha256 bare64hex; paths refer to exact declared dense and lexical_terms files. Sum of partition row counts equals total row_count. Zero rows implies zero partitions; nonzero rows implies at least one partition. These are declared counts/subset-map hashes, not verified row correspondence.
- validation: exact keys state and validator_fingerprint. state unproven with null fingerprint, or passed/failed with bare64hex validator fingerprint. These are recorded declarations. A passed string or fingerprint is never a readiness/capability/authorization result; later fresh validators must establish actual truth before publication.

There is NO snapshot_id, timestamp, generation, current pointer, credentials, live grants or arbitrary extension field inside the core. snapshot_id is exactly sha256: plus SHA256(core_bytes); fixed kind/schema provides the format domain. This is the canonical core manifest required by architecture12, without a circular self-hash. Operational timestamps, generation, publication/validation receipts and selected-state reconciliation belong outside this immutable core. Do not hash a core containing its own ID or substitute an ephemeral index/launch/PID identity.

## File and cross-reference rules

Path is exact ASCII string, length1..240, at most4 nonempty slash-separated components. Each component starts with lowercase ASCII letter or digit, then at most79 lowercase letters/digits/underscore/dot/hyphen. Reject dot/dotdot, leading dot, absolute paths, backslash, repeated/trailing slash, controls/NUL and normalization aliases. This is lexical validation only; it does not establish containment or no-symlink behavior of actual filesystem paths.

Closed role/schema pairs:
- row_map / slaif-raw-row-map-v1.
- source_membership / slaif-raw-source-membership-v1.
- dense / slaif-normalized-fp32le-d1024-npy-v1.
- lexical_terms / slaif-raw-lexical-terms-v1.

Exactly one row_map and one source_membership file; their paths match the corresponding core fields and differ. Every partition references one distinct dense and one distinct lexical_terms file; no sharing across partitions, missing/unreferenced files, role mismatch or extra file allowed. Thus file count is2+2*partition_count, including the empty snapshot's two common files. Every declared file size <=64MiB; nondense files additionally <=16MiB; total declared bytes <=96MiB. These caps are conservative compatibility with existing private stores/codecs, not actual IO or durability proof. Dense schema name declares the existing bounded normalized FP32 NPY format; JSONL schema names declare future raw row/membership/term payload contracts. This codec does not implement or qualify those payloads. No backend-native BM25 binary format is admitted.

Per-partition row-map hash must eventually derive from canonical original/representation row correspondence excluding assigned snapshot ID, so assigning the resulting snapshot ID to runtime rows does not create a content cycle. This leaf only validates its hash shape; later loader/builder must define and verify the actual subset bytes, source scopes and global row correspondence. Do not invent source/ACL validation here or persist live grants. Authorized-union lexical statistics are rebuilt from permitted rows; per-partition terms do not authorize local BM25 scores to become global ranks.

## Proof and remaining work

Tests exercise canonical nonempty and empty records, deterministic derived ID and content changes, immutable results, closed nesting/duplicate keys, strict scalar/list/path/resource bounds, active-withdrawn disjointness, partition total and exact file membership/reference relationships. Include malformed/trailing/unknown/self-ID/timestamp/generation, unsafe paths, oversized bytes/counts and mismatched roles/maps. Verify no explicit filesystem/network/process/model work and no readiness method or permission minted from passed declarations. Tests are meaningful format/cross-reference cases, not assertions mirroring every code line.

Use cached app Python, threads1/no bytecode, each fake/format invocation <=1GiBAS30CPU120wall. No install/network/model/framework/Tensor/GPU/driver/service/corpus/credential action or mutation of existing product sources. Source/law/architecture/locks/CI unchanged. Raw row/membership/term payload codec, actual source/deletion/ACL/row checks, fresh loader and retrieval smoke, staged directory publication/current-generation CAS, pinned request handles/retention, current policy, real model/precision/security/license/visual/held-out/fullICA remain open. A valid declared core and a content hash establish none of those.
