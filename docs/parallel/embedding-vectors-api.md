# Raw CLS normalization

`normalize_rows(rows)` accepts a list or tuple of 1–128 list or tuple rows, each exactly 1024 finite, exactly binary32-representable floats. It returns a frozen result with tuple rows, row-major little-endian binary32 `payload`, its `sha256`, and `policy_id`. Invalid input raises sanitized `VectorRefused`. The input is not mutated.

Policy `cls-l2-f64-fp32le-d1024-eps1e-12-tol1e-4-v1` uses stable float64 accumulation, requires norm greater than 1e-12, rounds to binary32 little-endian, and checks output norm within 1e-4. This is producer execution provenance and does not change the legacy encoder definition fingerprint. Payload is raw numeric bytes, not an NPY frame, row map, durable embedding, or qualification. Persisted vectors require separate validation; this function does not repair them on read or reuse.

Worker and native input integration, real-model CPU/GPU mathematical parity measurement, and license audit remain gates. No bitwise reference parity or hardware qualification is claimed.
