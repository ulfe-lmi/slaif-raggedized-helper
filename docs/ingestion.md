# Ingestion — native extraction and observed-count chunking (canonical 006)

This document describes the integrated extraction behavior of order
006-a, the observed native count/chunk integration of order 006-b, the
006-c durable component record integration, the 006-d final native
operator (corrected concurrent derived-store reads, the complete typed
text/PDF semantic bundle with its durable publisher and verified fresh
loader, the operator profile and the installed private chunk/inspect
route), and the 006-e bounded native PDF structural correction
(conservative literal line classifier, PDF policy definition v4 and the
shared kind-bound block fingerprint v2) on the accepted 005 record/store
foundation. It is the routine projection of the detailed per-adapter
contracts in `docs/parallel/text-extraction-api.md`,
`docs/parallel/structured-text-api.md`,
`docs/parallel/pdf-extraction-api.md`,
`docs/parallel/pdf-structure-api.md` and of the native count/chunk
contracts in `docs/parallel/native-tokenizers-api.md`,
`docs/parallel/tokenizer-session-api.md`,
`docs/parallel/native-chunking-api.md`,
`docs/parallel/bundle-source-records-api.md`,
`docs/parallel/bundle-native-records-api.md` and
`docs/parallel/derived-store-api.md`; those files remain the detailed
contracts. Nothing here is CommonMark parsing, OCR, rasterization,
semantic reconstruction or a model claim; the counts below are observed
local tokenization of explicit declared inputs, not inference
preprocessing.

## Supported formats and bounded subset

Admitted source media types: `text/plain`, `text/markdown`, `application/pdf`
(strict UTF-8 for text; bounded verified PDF otherwise).

- Literal line adapter (`text_extraction.extract`): one block per
  `str.splitlines(keepends=True)` line, exact decoded text and original line
  endings. For `text/markdown` only, ATX headings (up to three leading
  spaces), bullet/numbered procedure items and backtick/tilde fenced code are
  classified `heading`/`list`/`code`; every other line, including tables,
  links, HTML and indentation, stays literal `text`.
- Structural adapter (`structured_text.extract`): ordered units — headings,
  paragraphs, fenced code (closing fence requires sufficient matching
  markers), individual list items with indented continuations, and pipe
  table headers (header + literal separator line together) followed by
  subsequent pipe rows. Consecutive blank lines are literal text units.
  `text/plain` never claims Markdown structure. Unclosed fences retain the
  remainder as literal code with an explicit uncertainty note. This is a
  deliberately limited classifier; unrecognized syntax remains literal and
  unclassified.
- Native PDF adapter (`pdf_extraction.extract`): a fixed trusted isolated
  worker (pdfminer.six exactly 20260107 in a private, pinned,
  hash-verified development environment). Each page is `native_text` or
  `visual_needed`; any raster image, vector primitive or unsupported text
  leaf — including inside nested Form XObjects and mixed pages — marks the
  page `visual_needed` and the result `partial_visual_needed`, even when
  other native blocks are present. Nested forms retain their native text
  with actual character boxes without duplication. Images and vector
  content are never decoded or rendered here. The extracted lines are
  then classified by the conservative literal structure classifier
  (`pdf_structure.classify`, version `pdf-literal-structure-v3`): every
  block kind is `text`, `list` (literal bullet or numbered marker),
  `table_header` or `table_row` (literal multi-column header, following
  hyphen rule and at least two same-page rows with matching column
  starts; the rule line itself is retained as a table row). A following
  table starts only when its header, rule and two consistent rows form a
  complete same-page candidate; closing rules, blanks and EOF preserve
  the preceding last row. The grammar is bounded (at most 4,096 lines,
  500,000 total characters, 200,000 characters per line, pages 1–32,
  finite ordered bounding boxes, cooperative two-second budget) and
  cannot infer arbitrary PDF layout or fidelity: incomplete, multiline
  or unsupported material stays `text`, and a compatible but incomplete
  next-table prefix (a header and rule without two consistent same-page
  rows) is retained in the current table run rather than starting a new
  table.

## Source-to-block coverage and anchors

- Every block is a `provenance_records.Block` bound to its exact
  revision/extraction identity, with `origin="native"` and deterministic
  input-fingerprint `block_id`s. PDF block IDs use the shared kind-bound
  fingerprint (version 2) over revision, extraction, order, page, text
  SHA-256, geometry and classified kind; producer and stored validators
  share that one recipe.
- Text adapters: literal blocks anchor `line:N`; structural blocks anchor
  `section:N/line:M` (section = most recent heading). Structural coverage
  is a contiguous tuple of half-open Unicode code-point ranges that tile
  the decoded original exactly; block texts concatenate to all original
  characters (CRLF, blank lines, astral and combining code points, final
  incomplete lines). Offsets are code points, never bytes, PDF coordinates
  or tokenizer positions.
- PDF blocks anchor `page:N` with actual pdfminer layout bounding boxes in
  PDF points (bottom-left convention) and explicit heuristic
  reading-order uncertainty. No original byte equivalence, OCR or layout
  ordering guarantee is made.
- Identical bytes with different rights/ACL/version metadata produce
  distinct revisions, scopes and block identities over one verified shared
  blob; a metadata correction publishes a new revision and reuses the blob.

## Parser resource and trusted-runtime limits

- Text adapters: 2,000,000 original bytes, 1,000,000 decoded code points,
  4,096 blocks (line) / 100,000 lines, 4,096 blocks and 200,000 code points
  per block (structural). A five-second cooperative monotonic deadline is
  checked between units; it cannot interrupt a blocked filesystem call.
- PDF policy: 2,000,000 input bytes (checked before any blob read), 32
  pages, 20,000 layout objects, 500,000 text code points, 2,000,000 output
  bytes and a 2-second cooperative parent wall deadline. The parent reads
  the pipe only up to the output cap plus one byte and terminates/kills and
  reaps only its exact child on failure (bounded cleanup). Worker OS
  limits: 256 MiB address space, 1 CPU second, 32 descriptors, 2 MiB file
  size via `prlimit`. The byte-integrity pass (store hash/size
  verification), the parser limits and the cooperative deadlines are
  separate mechanisms; none is a hard filesystem-interrupt guarantee.
  The policy definition (version 4) binds the adapter, classifier
  version, explicit policy fields, geometry and isolation identities;
  records under policy v3 or classifier v2 remain immutable and
  incompatible and require explicit re-extraction, never a silent
  upgrade.
- Isolation: the launcher requires Linux `/usr/bin/prlimit` and
  `/usr/bin/bwrap`, working user/PID/network/IPC/UTS namespaces, the
  explicitly configured trusted CPython 3.12 runtime and package graph and
  the system library mounts. The worker sees only those read-only mounts,
  the fixed worker, the input, minimal proc/dev and a fresh tmpfs; the
  environment is cleared and inherited descriptors closed. Namespace
  support alone is not a hardened sandbox or hostile-PDF security proof.

## Required development test setup (DEV only)

The required PDF development tests fail — they do not skip — when
`PDF_TEST_RUNTIME`/`PDF_TEST_PACKAGES` are absent or invalid or when the
actual backend or isolation is unavailable.

Local (Linux x86-64, `uv`): install a standalone CPython 3.12 base runtime,
then run the reviewed helper on a NEW private target:

```sh
uv python install 3.12
python3 tests/support/prepare_pdf_test_backend.py \
  --runtime-dir "$(uv python dir)/cpython-3.12.X-linux-x86_64-gnu" \
  --target /absolute/path/new-private-pdf-test-env
# copy the printed export lines into the shell
uv run --isolated --locked --offline --python 3.12 pytest -p no:cacheprovider -o addopts='' -q \
  tests/unit/test_pdf_extraction.py tests/integration/test_pdf_extraction_composition.py
```

Product CI (GitHub-hosted, both Python 3.12/3.14 legs) performs the
equivalent steps per run: installs and verifies `bubblewrap`/`prlimit`,
runs an unprivileged namespace smoke mirroring the worker unshare set,
stubs `/usr/lib64` when the merged-usr host lacks that fixed bind source,
provisions the standalone 3.12 runtime and a new private
hash-verified backend via the same helper, and exports
`PDF_TEST_RUNTIME`/`PDF_TEST_PACKAGES`. The exact development pins
(SHA-256 verified): pdfminer.six 20260107, charset-normalizer 3.5.2,
cryptography 50.0.2, cffi 2.0.0, pycparser 3.12. These are development test
dependencies only: they add no project dependency, lock, allowlist entry,
license exception or application graph change; cffi MIT-0 and the other
transitive/native/platform/model license questions remain release and
redistribution gates (see `docs/UNCERTAINTIES.md` U07).

## Observed native counts and chunks (006-b/006-c)

`native_chunking.build(registry, blocks, body, representation, pair, runtime,
query, policy=None)` takes a validated provenance Registry and the complete
ordered block tuple of ONE extraction. The three explicit
`native_tokenizers.Definition` values must carry the roles `bge_body`,
`bge_representation` and `reranker_pair`. A fixed owned
`tokenizer_session.Session` verifies the actual artifact bytes (SHA-256,
exactly tokenizers 0.21.4 backend) and counts the exact
already-preprocessed strings in the isolated worker; at most two distinct
artifacts are permitted and the same file may serve both BGE roles.

- Body input is the chunk text; representation input is the concatenated
  heading path followed by the chunk text; pair input is the query followed
  by the complete representation. The worker uses special tokens, no
  truncation and no padding; the input digest is SHA-256 of the exact
  `[text, pair]` UTF-8 JSON serialization.
- Each returned chunk carries three frozen `TokenCount` records with
  `OBSERVED_LOCAL_NATIVE_TOKENIZATION` provenance and three matching frozen
  receipts (one per role) binding the exact count, input digest, observed
  artifact SHA, backend version, declared revision/preprocessing, role,
  mode and serialization. `receipts_json()` is bounded versioned JSON with
  digests and declarations but never source or query text.
- Chunks keep exact original spans/separators, heading paths, warnings with
  their procedures, repeated original table headers, conditional
  word-boundary overlap (observed body count at most 64 tokens) and no
  silently discarded tail; neighbor links are reciprocal and re-bound
  through the Registry. Rebuilding with the same inputs is deterministic;
  changed definitions, query, policy or revision change the chunk IDs.
- Defaults: 512 BGE body target, 768 soft maximum, 1024 representation
  maximum, full independent pair maximum 1280 with explicit 64 query
  reserve (the architecture example; the caller-supplied smaller values
  remain strict). The legacy `chunking.build` callback fixture keeps its
  supplied pair 512 default and `SUPPLIED_UNVERIFIED` provenance; supplied
  counts are assertions, never observed measurements.
- Budgets: builder deadline of 15,000 ms for the native default policy and
  5,000 ms for the legacy explicit default (hard maximum 15,000 ms), 4096
  blocks/chunks, one million source characters, 20,000 calls, 20 million
  work characters; Session startup five seconds, request two seconds,
  lifetime 20 seconds, 16,384 calls, 32 MB input, 4 MB output, 200,000
  bytes/100,000 characters per request, 4,096-byte responses, 200,000 tokens
  per count. Exceeding any limit refuses the whole build without partial
  output; errors contain no source text. Filesystem reads and the trusted
  local runtime/packages are trusted local inputs, not attestations.
- Per-build reuse (006-c): identical role/text/pair requests are counted
  once per build, so a deterministic build issues no duplicate session
  calls. The native v1 definition identity, receipt fingerprints and
  serialization are unchanged.
- Query identity (006-c): the policy definition (version 2) binds the exact
  UTF-8 SHA-256 digest of the query instead of the raw query text, so the
  4,096-byte policy-definition ceiling no longer bounds query length; the
  10,000-character query bound remains. Two queries with equal observed
  counts still produce different policy IDs.

### Representative-scale behavior (observed 2026-11-11; 006-c correction)

The 006-b 1024-call session limit is superseded: with the raised session
caps (16,384 calls / 32 MB input / 4 MB output), the 15,000 ms native
default builder deadline and per-build reuse, the independently measured
7876-byte procedure source (403 blocks, 81 chunks, 1,305 session calls) and
the 9269-byte table source (243 blocks, 25 chunks, 1,657 session calls) both
complete under the current caps with total, duplicate-free session call
streams, exact observed counts and full code-point coverage. These are
precise observed results on bounded software with honest degradation, not a
universal capacity or throughput claim. Contrary scale timings from the
accepted parallel evidence are retained: a 157,312-byte author run completed
in 10.79 s, an independent peer run in 13.81 s, and a root run at 15.17 s
was refused at the 15,000 ms deadline — bounded evidence of honest
degradation, with target host/model performance still open (objective 019)
and no extra quota or packing authority. The smaller 938-byte Unicode
(765 calls) and 148-byte manual (150 calls) sources likewise complete.
Representative-scale behavior and the hard-quota negative (standalone
Session seeded at 16,384 calls refuses the next count and reaps its owned
child) are asserted in the combined journey; details in
`docs/benchmarks/ingestion-count-storage.md`.

### Component storage composition (006-c)

`bundle_source_records.validate` re-derives the bounded source from the
`OriginalStore` and binds the supplied structured-text header, block JSONL
and coverage bytes to that result, returning canonical bytes; it is private
source verification, not current serving authentication. The PDF
counterpart (`bundle_pdf_records.validate`) verifies the original
hash/catalog plus producer-record consistency — including the shared
classifier re-run over stored block text and the kind-bound block IDs —
WITHOUT executing a fresh PDF parse or any fidelity attestation.
`bundle_native_records.validate` checks the policy identity, chunks and
three receipts per chunk from immutable bytes alone, with no source access
and no tokenizer execution. The combined journey publishes those canonical
bytes as ONE opaque immutable `derived_store` container
(`slaif-derived-container-v1`) with minimal metadata, closes the stores,
and revalidates from a FRESH store in a NEW process: source validation
against the actual original, receipt validation, Registry chunk binding,
reciprocal neighbor re-binding, source scope, full coverage union over the
decoded original, tail, role order and deterministic chunk IDs. Identical
republication is idempotent (same container ID); a corrupted container
member or altered stored original bytes are refused. This is component
storage composition: a successful opaque store load is NOT a trusted
complete native ingestion bundle; the 006-d round then adds that complete
semantic bundle, its durable publisher/verified fresh loader and the
installed private operator below.

### Complete semantic bundle, durable publisher and installed operator (006-d)

`ingestion_bundle.validate` is the complete semantic fresh validator: it
accepts an actual trusted `OriginalStore`, immutable metadata bytes and the
five ordered members (`blocks`, `coverage`, `chunks`, `neighbors`,
`receipts`), re-derives the verified source (structured text) or
revalidates the stored PDF producer records against the verified original
without a PDF parse (see above), binds each chunk to its exact
source fragments in contiguous first-exposure original order, checks the
complete neighbor chain and native receipt consistency, and returns one
frozen `Validated` value; structured text and PDF source records are
supported. It refuses the whole input with input-free errors; it does not
publish, invoke tokenizers or execute a document-supplied path.
`ingestion_store.publish` verifies the complete bundle against the original
and publishes the canonical bytes as ONE opaque immutable derived container,
returning its raw SHA-256 ID; `ingestion_store.load` first checks storage
integrity and then always revalidates the complete bundle against the
current verified original, returning the immutable `Validated` value. A
successful store load alone does not establish native ingestion trust: the
complete semantic bundle (validator + publisher + fresh loader) is the
trusted complete unit, while the opaque derived store remains the lower
component container of the 006-c composition. Both operations are bounded
by cooperative deadlines and clean up owned resources on every exit path.
`ingestion_profile.parse_profile`/`load_profile` admit ONE operator-selected
exact JSON profile (native runtime, BGE and reranker tokenizer records,
optional PDF runtime, and the complete explicit chunk policy; no defaults
are inserted) under a cooperative five-second deadline. The installed
private `raggedized chunk` (prepare + durable publication) and
`raggedized chunk inspect` (verified fresh load against the retained
original, no profile load, tokenizer or PDF parsing) routes use that
profile; usage, the bounded JSON overview (revision/bundle IDs, adapter,
status, coverage kind and blocks/chunks/neighbors/receipts counts), exit
0/1/2 semantics, the `no_native_chunks` + `source_status` partial visual
truth, the known `published_bundle_id` retained on a later failure,
idempotent canonical retries that can converge to the same ID, and the
cooperative 180-second overall budget are documented in
`docs/ingestion-operator.md`. Source admission approval remains metadata,
never current serving authentication or rights clearance.

The corrected derived-store read (006-d): if descriptor metadata changes
during a member read, that attempt is discarded and the file is reopened
and rechecked, at most four fresh attempts within the existing deadline;
only bytes from a stable, secure attempt reach the normal size and hash
checks. Persistent churn can still cause failure, and a successful read
does not attest to changes outside its observation interval; this is not a
universal convergence guarantee.

### Native PDF structural correction (006-e)

The root-reproduced structural failures are repaired by the integrated
bounded literal classifier (`pdf-literal-structure-v3`) under PDF policy
definition v4 and the shared kind-bound block fingerprint v2. On the
actual post-merge owned fixtures, every row chunk of the small (20-row)
and closing reduced-policy tables and of the default-policy 300-row
table now carries the original header fragment with complete
interval-union coverage, tail, units and anchors preserved; the
fitting-warning case (body 14 observed tokens, soft maximum 20, target
12) keeps the warning and its procedure in one chunk while the
unrelated prefix stays separate; and the closing-rule and
trailing-blank cases preserve the last row's header instead of
dropping it to unclassified text. The unchanged Root terminator and admission
witnesses and the independent peer boundary witness pass against the
merged source (recorded in the 006-e report). The grammar's limits stay
honest and documented: it is a bounded literal grammar, not a PDF layout
or fidelity solver; a one-character header offset requires two consistent
rows, and an incomplete or ambiguous next-table prefix keeps the material
in the preceding run or as `text` rather than guessing. Records produced
under classifier v2 or policy v3 are immutable and incompatible: they
require explicit re-extraction, never a silent upgrade. The broader
PAR-006-PDF-STRUCTURE-A experiment is superseded as the current repair by
this reviewed correction.

### Required development test setup (native, DEV only)

The required native development tests fail — they do not skip — when
`SLAIF_NATIVE_TEST_ROOT`/`SLAIF_NATIVE_TEST_PACKAGES`/
`SLAIF_NATIVE_TEST_PYTHON` are absent or invalid or when the actual
backend or isolation is unavailable. Local (Linux x86-64, `uv`) after the
PDF backend runtime exists:

```sh
python3 tests/support/prepare_native_test_backend.py \
  --runtime-dir "$(uv python dir)/cpython-3.12.X-linux-x86_64-gnu" \
  --target /absolute/path/new-private-native-test-env
# copy the printed export lines into the shell
uv run --isolated --locked --offline --python 3.12 pytest -p no:cacheprovider -o addopts='' -q \
  tests/unit/test_native_tokenizers.py tests/unit/test_native_chunking.py \
  tests/integration/test_native_chunking_composition.py \
  tests/integration/test_native_extraction_counts.py
```

The capsule is engine-only: the pinned hash-verified `tokenizers==0.21.4`
wheel with `--no-deps` in a new private 0700 target. It is not an upstream
complete application dependency, a lock/allowlist entry, a license
clearance or a model/tokenizer equivalence claim; tests use locally
generated toy tokenizer artifacts (see
`tests/unit/test_native_tokenizers.py`), never deployed model assets.
Product CI (both Python 3.12/3.14 legs) provisions the same capsule per run
on disposable runners with the same verified bwrap/prlimit/timeout
isolation and binds the literal `SLAIF_NATIVE_TEST_*` values in GITHUB_ENV
(never sourcing helper output).

## Explicitly not in this slice

The bounded literal classifier is the last 006 native-structure repair
integrated on this branch; whole-006 native coverage is software-complete
here subject to the independent Root review after the 006-e report — the
code queue and green CI alone are not acceptance, and no all-PDF, visual,
model, license, ICA or MVP claim is made. Contextualization, embeddings,
snapshots, retrieval, the answer API, GPU/vision work, real corpus access,
legal exception handling and all physical/model/domain/license/ICA
qualification remain separate open scope. Source metadata approval remains
distinct from authentication and rights clearance.
