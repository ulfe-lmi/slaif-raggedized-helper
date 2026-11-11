# Structured text source records

`bundle_source_records.validate(store, revision_id, header_bytes, blocks_jsonl_bytes,
coverage_bytes, expected_blocks)` accepts an exact `OriginalStore`, a sha256 revision ID,
immutable bytes and a strict count from 1 to 4096. It returns frozen typed revision, derived
scope, dependency, blocks and coverage alongside canonical UTF-8 header, Block JSONL and
coverage bytes. Failures raise `BundleSourceError` with an input-free message; no partial
result or publication occurs. A caller can construct a provenance Registry from these values.

The header has exactly dependency, adapter, status, coverage_kind and uncertainty. Coverage
has exactly schema_version, kind and ordered spans (block_id, start, end), using Unicode
codepoint offsets. The exact installed structured-text policy definition and fingerprint are
required. Header, blocks and coverage are capped at 65536 bytes, 16 MiB and 2 MiB;
JSONL retains the existing 1 MiB per record and 4096 record caps. JSON structure, Unicode,
unique keys, counts and a cooperative 30-second deadline are bounded. The source extractor
also enforces its 2 MB, one million codepoint, 100000 line, 4096 block, 200000 character
per block and five-second limits, including any narrower selected policy. Deadlines cannot
interrupt a blocked filesystem operation.

Validation re-reads the verified original and repeats deterministic structured-text extraction;
its cost therefore includes a source read and parse on every validation. All blocks and spans,
policy dependency and uncertainty must match that actual result. This verifies source binding
and mechanical consistency, not producer execution attestation, serving authorization or
retrieval quality. Unknown source versions remain data; scope comes from the verified revision.
PDF, chunks, neighbors, full bundle storage and CLI are outside this boundary.
