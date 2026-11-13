# Raw snapshot core API

`parse(core_bytes)` accepts canonical bounded JSON bytes and returns an immutable core descriptor with a noncircular SHA-256 ID. `ManifestError` carries no input content. The format records declarations, including validation state, and does not establish readiness, authorization, source truth, or file integrity.

The two frozen source inventory targets are separate, not an integrated runtime. Payload codecs and fresh loading, current-pointer publication and retention, rights and deletion checks, parity and model qualification, security, license review and independent acceptance remain future gates.
