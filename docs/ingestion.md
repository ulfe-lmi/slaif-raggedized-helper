# Ingestion — native extraction protocol (canonical 006 first slice)

This document describes the integrated extraction behavior of order 006-a on
the accepted 005 record/store foundation. It is the routine projection of the
detailed per-adapter contracts in `docs/parallel/text-extraction-api.md`,
`docs/parallel/structured-text-api.md` and
`docs/parallel/pdf-extraction-api.md`; those files remain the detailed
contracts. Nothing here is CommonMark parsing, OCR, rasterization, semantic
reconstruction, tokenization, chunking or a model claim.

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

## Explicitly not in this slice

Structural chunking, native tokenizer sessions and exact 512/768/1024
body/representation budgets with 64-overlap remain the ordered same-PR 006
continuation. Contextualization, embeddings, snapshots, retrieval, the
answer API, GPU/vision work, real corpus access, legal exception handling
and all physical/model/domain/license/ICA qualification remain separate
open scope. Source metadata approval remains distinct from
authentication and rights clearance.
