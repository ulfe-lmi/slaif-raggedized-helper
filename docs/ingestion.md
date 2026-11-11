# Ingestion — native extraction and observed-count chunking (canonical 006)

This document describes the integrated extraction behavior of order 006-a and
the observed native count/chunk integration of order 006-b on the accepted
005 record/store foundation. It is the routine projection of the detailed
per-adapter contracts in `docs/parallel/text-extraction-api.md`,
`docs/parallel/structured-text-api.md` and
`docs/parallel/pdf-extraction-api.md` and of the native count/chunk contracts
in `docs/parallel/native-tokenizers-api.md`,
`docs/parallel/tokenizer-session-api.md` and
`docs/parallel/native-chunking-api.md`; those files remain the detailed
contracts. Nothing here is CommonMark parsing, OCR, rasterization, semantic
reconstruction or a model claim; the counts below are observed local
tokenization of explicit declared inputs, not inference preprocessing.

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
  content are never decoded or rendered here.

## Source-to-block coverage and anchors

- Every block is a `provenance_records.Block` bound to its exact
  revision/extraction identity, with `origin="native"` and deterministic
  input-fingerprint `block_id`s.
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

## Observed native counts and chunks (006-b)

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
- Budgets: builder five-second budget, 4096 blocks/chunks, one million
  source characters, 20,000 calls, 20 million work characters; Session
  startup five seconds, request two seconds, lifetime 20 seconds, 1024
  calls, 16 MB input, 4 MB output, 200,000 bytes/100,000 characters per
  request, 4,096-byte responses, 200,000 tokens per count. Exceeding any
  limit refuses the whole build without partial output; errors contain no
  source text. Filesystem reads and the trusted local runtime/packages are
  trusted local inputs, not attestations.

### Actual usability limit (observed 2026-11-11)

The Session call budget makes representative-scale documents unusable with
the current accepted bridge: the independently measured 7876-byte procedure
source (403 blocks) and 9269-byte table source (243 blocks) are refused at
attempted session call 1025 before any chunk/neighbor/receipt output (the
765-call 938-byte Unicode source and 150-call 148-byte manual complete).
The refusal is honest and total — no partial result — but it is a precise
observed limit, not a capacity proof, and no representative large-document
PASS is claimed from the bounded test fixtures. An isolated
PAR-006-NATIVE-EFFICIENCY-A correction is commissioned as required same-PR
006 work before whole-006 acceptance; durable derived bundles/loaders and
the private installed chunk command remain separate required same-PR work
as well.

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

Durable derived bundle/loaders, the private installed chunk command,
contextualization, embeddings, snapshots, retrieval, the answer API,
GPU/vision work, real corpus access, legal exception handling and all
physical/model/domain/license/ICA qualification remain separate open
scope. The representative-scale session call budget limit above is closed
by the commissioned same-PR efficiency correction, not by this slice.
Source metadata approval remains distinct from authentication and rights
clearance.
