# Native bundle records boundary

`validate(header_bytes, chunks_jsonl_bytes, receipts_json_bytes, expected_chunks)` returns
immutable validated policy and chunks with canonical bytes, or an input-free refusal. Inputs
are bounded before parsing. The cooperative deadline is 30 seconds; it is not a hard CPU or
memory guarantee. Aggregate native input characters are limited to 20 million and each input
and serialization to Session limits. No tokenizer is invoked.

This checks mechanical consistency of the producer's policy, chunks and three exported count
receipts. Those receipts omit query-only and empty-passage reserve observations, so reserve
admission remains a trusted producer invariant. This does not attest execution, authenticate
source, qualify deployed inference, or establish current serving authorization. A later source
bundle layer must verify Registry, revision, original spans, coverage and neighbors, and current
serving authorization separately. Full ingestion, PDF semantics and CLI remain future work.

Container output uses compact sorted UTF-8 JSON and is subject to the same 65,536-byte
header, 8,000,000-byte receipt and 16 MiB JSONL caps as input; native definition and input
fingerprints retain their original ASCII serialization. A final deadline check applies before
return. Parsing permits depth 16 and counts every value and dictionary key, including pending
work, before expanding a container. The header budget is 10,000 nodes and receipt budget is
500,000. A maximum receipt document has 12,288 receipts, each with at most 27 key/value nodes plus
the root's five nodes: 331,781, below the receipt budget. These limits bound traversal after
JSON decoding; the raw byte limits independently bound the decoder input.
