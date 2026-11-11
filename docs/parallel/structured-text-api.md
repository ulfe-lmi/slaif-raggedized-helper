# Native structured text candidate

`structured_text.extract(store, revision_id, policy=None)` uses the public
bounded `OriginalStore.read_verified` operation to inspect the immutable
revision and read actual verified original bytes. The byte cap is checked
before blob reading and enforced on its descriptor. The small revision record
is separately read under the store's metadata bound. Only approved
`text/plain` and `text/markdown` sources and strict UTF-8 are admitted; PDF is
not handled. The caller owns and closes the store. Processing approval, ACL,
corpus and rights remain metadata, not authentication or serving authority.

`StructureResult` contains the revision, its provenance scope and dependency,
ordered native `Block`s and a parallel immutable `coverage` tuple. Each
coverage range is half-open Unicode code-point offsets in the decoded original;
its block ID and substring correspond exactly to that block. Ranges are
contiguous in order and concatenated block text reconstructs all original
characters, including CRLF, indentation, blank lines and final incomplete
lines. An empty original yields an explicit zero-block result. Geometry is
unavailable. Anchors identify the most recent recognized heading's line and
the unit's first line, using section 0 before any heading. IDs bind revision,
policy, order, anchor, kind and actual UTF-8 text hash.

The bounded subset recognizes Markdown ATX headings, individual bullet or
numbered procedure items with indented continuation lines, fenced backtick or
tilde code through the matching closing fence, and pipe table headers followed
by matching delimiter cells and their subsequent pipe rows. A header block
includes its literal separator line. Repeated headers and warnings are never
removed. Unclosed fences retain the remaining literal text as code and carry
an uncertainty note. Consecutive nonblank unrecognized lines form text
paragraphs; consecutive blank lines form literal text blocks. Plain text
recognizes numbered/bullet procedure items but leaves Markdown syntax literal.
This is a deliberately limited classifier, not CommonMark parsing or semantic
structure validation. Result-level uncertainty explicitly states that other
syntax is literal and not fully classified. Links, HTML, instructions and
commands are never fetched, rendered or executed.

Default and maximum limits are 2,000,000 input bytes, 1,000,000 decoded code
points, 100,000 lines, 4,096 blocks and 200,000 code points per block. The
frozen policy can narrow these values; booleans, nonintegers, zero and values
above the caps are refused. Policy definition and every limit are bound to
the extraction fingerprint. A five-second monotonic deadline is cooperative:
it is checked after storage/decoding, between units and before returning; it
cannot interrupt blocked filesystem calls. Failures return a fixed input-free
`StructureError`, never a truncated or partial success. These character and
line limits are not tokenizer counts. Token-aware chunking, PDF, vision,
real corpus quality evaluation, ICA and full 006 qualification remain open.
