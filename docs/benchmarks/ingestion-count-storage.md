# Ingestion count and storage verification notes (objective 006, slices a-c)

Detailed non-routine verification notes moved out of TESTING.md T13/T14 so the
routine coding context stays within its measured byte ceiling. All coverage,
limitations and distinctions below are preserved from the accepted 006-a/006-b/
006-c rounds; TESTING.md keeps concise summaries and pointers to this document.
Real target/model/hardware/quality/vision/license qualification remains NOT RUN
in every section (live authorization: NONE for each 006 round).

T13. Combined canonical 006 first-slice extraction (objective 006-a): `uv run
pytest tests/unit/test_text_extraction.py tests/unit/test_structured_text.py
tests/unit/test_pdf_extraction.py tests/integration/test_text_extraction_composition.py
tests/integration/test_structured_text_composition.py
tests/integration/test_pdf_extraction_composition.py
tests/integration/test_extraction_combined.py -q` runs the merged native
extraction adapters on owned synthetic originals: literal line and bounded
structural Markdown subset adapters with exact Unicode code-point coverage
(contiguous half-open ranges tiling the decoded original) and the fixed
trusted isolated PDF worker (pdfminer.six 20260107 in a private pinned
hash-verified environment under `/usr/bin/prlimit` + `/usr/bin/bwrap` with
user/PID/net/IPC/UTS namespaces) proving native text, nested-form
deduplication, mixed raster/vector visual-needed pages and count/geometry/
object accounting. `test_extraction_combined.py` composes manifest ->
`OriginalStore` -> all three adapters -> `provenance.Registry` in one journey:
shared bytes with distinct corpus/labels/rights/version, a metadata revision
reusing one verified blob, native literal and structural coverage, source
immutability, and malformed/oversized/wrong-hash/unsupported-media refusal;
the source byte-integrity pass, parse limits and cooperative parent/worker
deadlines are separate mechanisms, none a hard filesystem-interrupt guarantee.
Order 006-e adds the conservative literal structure classifier to this adapter: `tests/unit/test_pdf_structure.py` and
`tests/integration/test_native_pdf_structure.py` run under the same backend (006-e notes below).
The required PDF tests fail explicitly (instead of skipping) when
`PDF_TEST_RUNTIME`/`PDF_TEST_PACKAGES` are absent or the backend or isolation
is unavailable. Local setup: `uv python install 3.12` plus `python3
tests/support/prepare_pdf_test_backend.py --runtime-dir <standalone 3.12 root>
--target <new private dir>` (prints exact `PDF_TEST_RUNTIME`/
`PDF_TEST_PACKAGES` exports); product CI provisions the equivalent per run on
disposable GitHub-hosted runners and verifies bwrap/prlimit and an
unprivileged namespace smoke. The development pins (pdfminer.six 20260107,
charset-normalizer 3.5.2, cryptography 50.0.2, cffi 2.0.0, pycparser 3.12,
SHA-256 verified) are DEV-only and add no project dependency, lock,
allowlist, license exception or application graph change. All synthetic and
offline; no real corpus, network, GPU, model or quality work.

T14. Combined canonical 006 observed-count journey (objectives 006-b/006-c):
`uv run pytest tests/unit/test_native_tokenizers.py
tests/unit/test_native_chunking.py tests/integration/test_native_chunking_composition.py
tests/integration/test_native_extraction_counts.py -q` runs the merged native
count/chunk stack on owned synthetic originals: manifest -> OriginalStore ->
line/structure/PDF extraction -> Registry -> native_chunking.build with three
OBSERVED local token counts and receipts per chunk (exact role inputs,
artifact SHA, backend, revision/preprocessing, input digests), 512/768/1024
budgets, up-to-64-token word-boundary overlap, no discarded tail, reciprocal
neighbors, deterministic rebuild, same-byte distinct IDs and cross-source
denial, native pair 1280/reserve 64 with strict smaller-policy refusal,
legacy callback pair 512 kept SUPPLIED_UNVERIFIED, and independent session
re-counts instead of hand-derived word counts. Current 006-c bounds: the
owned Session hard caps are 16,384 calls, 32 MB input and 4 MB output; the
builder deadline is 15,000 ms for the native default policy and 5,000 ms for
the legacy explicit default (maximum 15,000 ms); per-build reuse removes
duplicate identical count requests within one build (deterministic,
duplicate-free session call streams); the policy definition (version 2)
binds the exact UTF-8 SHA-256 digest of the query instead of the raw query
text (the 4,096-byte policy-definition ceiling no longer bounds query length;
the 10,000-character query bound remains; equal-count distinct queries keep
distinct policy IDs); the native v1 definition identity, receipt fingerprints
and serialization are unchanged. Representative-scale behavior (observed
2026-11-11, reproducible): the 7876-byte procedure source (403 blocks, 81
chunks, exactly 1,305 session calls) and the 9269-byte table source (243
blocks, 25 chunks, exactly 1,657 session calls) both complete under the
current caps with full code-point coverage (the tightened combined helper now
asserts the full interval union per block: exact copied text, no gap, full
original end), while the 938-byte Unicode (765 calls) and 148-byte manual
(150 calls) sources complete as well. These are precise observed results on
bounded software with honest degradation, not a universal capacity or
throughput claim; contrary accepted parallel scale timings are retained
(157,312-byte author run 10.79 s, independent peer 13.81 s, root run 15.17 s
refused at the 15,000 ms deadline) and target host/model performance remains
open (objective 019) with no extra quota authority. The hard-quota negative
is a standalone owned Session seeded at exactly 16,384 calls: the next count
is refused before any worker request with `tokenizer session refused`, the
session closes itself, and the owned child process is terminated and reaped
(no huge fixture tokenized). The required native tests fail explicitly
(never skip) when SLAIF_NATIVE_TEST_ROOT/PACKAGES/PYTHON, the backend or the
isolation is absent or invalid. Local setup: `python3
tests/support/prepare_native_test_backend.py --runtime-dir <standalone 3.12
root> --target <new private dir>`; product CI provisions the NEW private
pinned hash-verified engine-only tokenizers 0.21.4 capsule per run on both
Python 3.12/3.14 legs with literal GITHUB_ENV bindings (helper output never
sourced). The capsule is DEV-only (engine-only --no-deps; no dependency,
lock, allowlist or license change); toy artifacts only — no deployed-model
equivalence, serving, hardware, license or quality claim. Real qualification
NOT RUN.

T14a. Durable component record storage composition (objective 006-c): the SAME
combined journey (tests/integration/test_native_extraction_counts.py,
test_durable_component_storage_composition) extends the native counts path
with the accepted component validators and opaque store: actual structured
text records are bound by `bundle_source_records.validate` (re-derivation of the
bounded source against the `OriginalStore`; canonical header/blocks/coverage bytes); the PDF counterpart
(`bundle_pdf_records.validate`) verifies the original hash/catalog plus producer-record consistency, including the shared
classifier re-run over stored block text and the kind-bound block IDs, WITHOUT executing a fresh PDF parse or any fidelity attestation; the
observed-count chunks and receipts are bound by
`bundle_native_records.validate` (policy identity, chunk text/fragment
reconstruction, three receipts per chunk, pure bytes, no source access and no
tokenizer), and the six canonical member bytes plus minimal metadata are
published as ONE opaque immutable `derived_store` container
(`slaif-derived-container-v1`; content-addressed members, manifest hash as
container ID, 0600/0700 owned-private layout, fsync, 30 s bounded
operations). After close, a FRESH derived store in a NEW owned subprocess
(re-fixed `sys.executable -c` snippet; no source-defined executable) reloads
the container and revalidates: source validation against the actual
original, receipt validation from immutable bytes, Registry chunk binding,
reciprocal neighbor re-binding, source scope (corpus/labels/rights/version),
full coverage union over the decoded original, tail, role order and
deterministic chunk IDs; identical republication returns the same container
ID (retry idempotency), a corrupted container member object refuses load
with `invalid container`, and altered stored original bytes refuse source
validation with `source bundle records refused`. Source metadata approval and
source validation remain distinct from current serving authentication and
rights clearance. This is component storage composition only: a successful
opaque store load is NOT a trusted complete native ingestion bundle, and no
full typed bundle loader, PDF semantic value composition or private installed
chunk CLI product API is invented or claimed. All synthetic and offline; real
qualification NOT RUN.

T15. Installed private chunk/inspect operator and complete semantic
bundle (objective 006-d): `uv run pytest -o addopts='' -q
tests/unit/test_chunk_cli.py tests/unit/test_ingestion_prepare.py
tests/integration/test_chunk_cli_composition.py` under the T14 native
and T13 PDF dev backends (25 tests; observed 37.68 s on the 006-d
devhost) runs the INSTALLED `raggedized chunk` and
`raggedized chunk inspect` routes in subprocesses on owned private
original/derived stores. `chunk` takes `--original-store`,
`--derived-store`, `--revision sha256:<64hex>`, `--adapter
structured_text|pdf_extraction`, `--profile` (the complete explicit
operator profile: native runtime, BGE and reranker tokenizer records,
optional PDF runtime, full chunk policy, no defaults) and optional
`--query` (at most 10,000 valid Unicode characters); it re-extracts,
builds the observed-count chunks with the profile's three actual CPU
tokenizer definitions, durably publishes the complete typed bundle as
ONE opaque derived container, and finally inspect-verifies the
published ID before returning the bounded JSON overview (revision and
bundle IDs, adapter, status, coverage kind and blocks/chunks/neighbors/
receipts counts). `chunk inspect --bundle <id>` verifies a published
bundle against the retained original without loading a profile or
running tokenizers or PDF parsing. Exit semantics: 0 on successful
preparation/inspection; 1 on an empty native result (status
`no_native_chunks`, a `source_status` of `complete_text` or the PDF
`partial_visual_needed` partial visual truth, no bundle ID) or a typed
ingestion failure (`{"error": "ingestion_failed"}`, carrying
`published_bundle_id` when publication completed before a later
verification, deadline or cleanup failure; if no ID is known the commit
state is unknown; no rollback is implied); 2 on invalid input
(`{"error": "invalid_input"}`). The overview is bounded JSON with no
source text or query; output over 65,536 bytes or a deadline expiry
refuses. The overall 180-second budget is cooperative and cannot
interrupt a blocked filesystem or stdout operation; interruptions
propagate and owned stores are closed on every exit path. Canonical
retries with unchanged verified inputs converge to the same container
ID; a coherently re-published container bound to another revision is
refused by semantic validation (more than a changed manifest hash);
corrupted members, altered stored originals, invalid profiles/hashes/
backends/policies and oversized queries are refused input-free.
The corrected derived-store member read (006-d) discards a changed
attempt and re-admits the file at most four fresh times within the
existing deadline; only stable bytes reach the size/hash checks. Finite
retries are not a universal convergence guarantee under persistent
churn, and a successful read does not attest to changes outside its
observation interval. The independent root witnesses (link-race,
closed-FD, deadline, corruption) run unchanged against the merged
module and all pass (the link-race witness failed before the fix).
After the 006-d integration the six combined extraction/count
integration composition suites of T13/T14
(test_text_extraction_composition.py,
test_structured_text_composition.py,
test_pdf_extraction_composition.py, test_extraction_combined.py,
test_native_chunking_composition.py,
test_native_extraction_counts.py; 49 cases; observed 28.53 s) re-run
unchanged with no skip or fallback, and the 84 derived-store unit and
composition tests (observed 0.64 s) pass unchanged.
006-e structural correction: the root-reproduced failures (default
303-block table losing the second header relationship, fitting warning
body 14 <= soft 20 > target 12 separated from its procedure, closing
rule/blank losing the last row) are repaired by the integrated literal
classifier pdf-literal-structure-v3 under PDF policy definition v4 and
the shared kind-bound block fingerprint v2. On the actual post-merge
owned fixtures — reduced-policy small (20 rows) and closing (same
table plus a closing hyphen rule), default-policy 300-row table (all
two-column), and the fitting-warning procedure source — every row
chunk carries the original header fragments with complete interval-union
coverage, tail, units and anchors preserved; the warning and its
procedure stay in one chunk while the unrelated prefix stays separate;
closing rules and trailing blanks preserve the last row's header. The
grammar remains a bounded literal heuristic: a one-character header
offset requires two consistent rows, a compatible but incomplete
next-table prefix is retained in the current table run rather than
starting a new table, and other ambiguous or unsupported material stays
text; it cannot infer arbitrary PDF layout or fidelity. Records under
classifier v2 or policy v3 are immutable and incompatible: explicit
re-extraction, never a silent upgrade. The unchanged Root terminator and
admission witnesses and the independent peer boundary witness pass
against the merged source. All synthetic and offline; real
qualification NOT RUN.
