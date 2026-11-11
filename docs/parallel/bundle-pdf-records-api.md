# PDF source record validation

`bundle_pdf_records.validate(store, revision_id, header_bytes, blocks_jsonl_bytes,
coverage_bytes, expected_blocks)` accepts a trusted `OriginalStore`, a selected revision ID,
and immutable untrusted bytes. It returns frozen records and canonical UTF-8 bytes, or raises
`PdfRecordsError` with an input-free message. The header has exactly `dependency`, `adapter`,
`status`, `coverage_kind`, and `uncertainty`. Coverage has exactly `schema_version`, `kind`,
and sequential page/status `pages`. Blocks use the complete provenance Block JSONL schema.

The validator bounds header to 65536 bytes, coverage to 2 MiB, JSONL to 16 MiB and each
record to 1 MiB, with at most 4096 blocks, 32 pages, the policy's 500000-character maximum,
and a 30-second cooperative deadline. The verified original read uses the policy's at most
2,000,000-byte bound; a blocked filesystem read cannot be cancelled by that deadline, and
no fixed RSS guarantee is made. It does not import or run a PDF parser, tokenizer, model,
or subprocess on load. All-visual PDFs may have zero blocks only as partial visual evidence;
the later native bundle still requires nonempty source blocks and chunks.

Original integrity and consistent page, block and ID records do not establish fresh extraction,
complete pages or visual fidelity, equality to original PDF text bytes, or an uncompromised
producer. This boundary relies on the fixed approved producer and pinned bundle identity and
storage, not an execution attestation. Metadata approval is not current serving authorization
or license clearance. Later composition must bind chunks, intervals, neighbors and receipts;
visual extraction, current authorization, licensing, independent audit and MVP gates remain open.

The validator requires PDF policy v4 including classifier version, rederives the complete kind sequence from admitted page, text and geometry, and checks the shared v2 block fingerprint including kind. It rejects older v3 records; re-extract explicitly under the new policy. Load never runs the parser or tokenizer. This is a trusted-producer consistency check, not a fresh fidelity or authorization attestation. Objective 019, visual, license and independent audit gates remain open.

Records bound to classifier `pdf-literal-structure-v2`, including policy v4 records, are incompatible with classifier v3 and require explicit re-extraction.
