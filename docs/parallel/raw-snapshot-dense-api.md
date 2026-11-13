# Dense partition API

`parse(bytes, sha256, rows)` validates bounded normalized NPY data under the fixed policy and returns the codec's read-only result. This is data validation only.

`build_partition(originals, derived, row_map_bytes, partition_id)` freshly loads each selected group from borrowed stores and returns an immutable `DensePartition`. Its payload preserves the stored FP32 bytes in selected row-map order. `validate_partition` accepts the same arguments plus container bytes and their SHA-256, parses the candidate and requires byte equality with a fresh rebuild. Ordinary failures raise content-free `DenseError`.

This establishes correspondence to stored source rows and vectors, not neural provenance, current rights, or readiness. The operation has cooperative 30-second checks and fixed group, row and codec limits; it does not preempt a running helper.
