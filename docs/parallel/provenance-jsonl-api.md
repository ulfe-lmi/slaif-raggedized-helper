# Provenance JSONL byte codec

`provenance_jsonl.encode(kind, records)` takes a tuple of raw JSON byte records;
`decode(kind, data, expected_sha256, expected_count)` takes immutable bytes, an
exact 64-character lowercase SHA-256 hex digest of the entire stream, and an integer
count. Both return only after complete validation and raise input-free `JsonlError`
on refusal. The fixed case-sensitive kinds are Scope, Dependency, Block,
SourceFragment, Separator, TokenCount, Chunk, Neighbors, Derived, Grants and
Restrictions. Each record passes `provenance_records.admit_record` for its kind.
DTOs and mappings are not encoder inputs.

The encoder emits UTF-8 JSON with sorted keys, compact separators, unescaped Unicode,
finite numbers and one ASCII LF after each record. The hash is SHA-256 over those exact
bytes, including final LFs; the zero-record stream is empty bytes, with SHA-256
`e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.
No BOM, physical CR, blank lines or missing final LF are permitted. Escaped CRLF in
values and literal U+2028/U+2029 are data; framing scans ASCII LF, not Unicode lines.
The encoder preserves JSON values, including omitted fields; this container encoding
is distinct from the versioned `schema.fingerprint` identity format.

Both directions cap streams at 4096 records and 16 MiB, each record at the existing
1 MiB admission limit, and use a five-second cooperative elapsed ceiling checked
between bounded operations. The ceiling is not preemptive: an individual JSON parser,
hash or allocation cannot be interrupted. Input sizes are checked before parsing;
decode verifies the complete checksum and scans bounded frame lengths and counts before
admission. The existing admission boundary enforces strict UTF-8, unique keys, finite
numbers, field schemas, tree depth and Unicode validity. Noncanonical valid JSON lines
may be decoded; re-encoding canonicalizes their container representation.

Record `schema_version` remains the existing version 1 contract. A future incompatible
framing or canonicalization change requires an explicit versioned format; callers must
fix the kind and agree on this codec rather than infer types from untrusted input. A
checksum proves exact bytes against a supplied expectation, not authenticity. Decoded
DTOs alone do not bind records to each other or to original sources: reconstruct and
validate the Registry and chunk/neighbor bindings and verify source revisions separately.
This in-memory codec does not provide safe filesystem paths, atomic bundle publication,
loading, receipts, snapshots, current authorization or hardware/model qualification.
It does not implement the chunk CLI or complete objective 006.
