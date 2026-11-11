# Bounded vector codec

`encode(matrix, policy=Policy())` and `decode(data, expected_sha256, policy=Policy())`
return a frozen `Result`: immutable container bytes, lowercase hex SHA-256 of the entire
container and of the raw payload, `(rows, 1024)`, policy fingerprint, and a read-only
NumPy matrix backed by immutable bytes. Decode requires immutable `bytes` and a lowercase
64-character expected container digest. Errors are input-free `CodecError` and return no
partial result. Encoding snapshots caller values; subsequent caller mutation cannot change
the result. Concurrent mutation during the initial snapshot is outside the trusted-memory
contract. NumPy and CPU execution are trusted; the cooperative deadline is checked between
bounded operations and cannot preempt a NumPy operation.

The only frame is NPY 1.0: magic and version, little-endian unsigned 16-bit header length,
a bounded UTF-8 Python-literal dictionary with exactly `descr: '<f4'`,
`fortran_order: False`, and `shape: (N, 1024)`, followed by exactly N×1024×4 bytes.
Header AST syntax is constrained and never evaluated; no NumPy deserializer or pickle is
used. The writer uses NumPy's v1 numeric writer with pickle disabled and revalidates its
actual output. Each row must be finite and have L2 norm within the explicitly fingerprinted
policy tolerance, at most 0.0001; no normalization occurs. Norm accumulation uses bounded
128-row FP64 batches. No file or network I/O is performed.

Policy ceilings are 20,000 nonempty rows, 82,000,000 container bytes, 512 header bytes,
20,480,000 elements and element-work units, and 5,000 ms cooperative deadline; callers
may reduce each. The policy fingerprint is SHA-256 over sorted compact JSON of all fields.
These limits are illustrative software bounds, not measured capacity. Container and payload
hashes do not identify encoder, row map, shared embedding space, execution parity, or
qualification. Callers must establish those and bind rows and hashes in a trusted manifest.
Filesystem publication, snapshots, and manifest validation are outside this codec. Objectives
007/008/019, license qualification, independent audit and MVP gates remain open; no model,
quality, latency, or hardware qualification follows from this implementation.
