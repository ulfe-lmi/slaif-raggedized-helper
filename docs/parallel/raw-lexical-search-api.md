# Source-backed raw lexical DATA search

`raw_lexical_search.search(originals, derived, store_root, snapshot_id, text, *, grants,
restrictions=None, k=60, partition_cap=60, deadline_ms=120000)` borrows the actual original and
derived stores and loads the explicitly named snapshot twice. It returns frozen `LexicalResult`,
`Hit`, and `PartitionCount` records, or raises content-free `LexicalSearchError`. Non-Exception
interruptions propagate. `grants` and `restrictions` are static trusted-caller data, not a claim
about current principal policy. A missing grant or source version denies access.

Hits carry the original source ordinal, partition, chunk, revision, bare representation ID,
canonical scope and chunk bytes, score and global rank. Counts describe eligible, matching,
partition-selected and globally returned authorized rows; cap flags report discarded matches.
The corpus comprises stored rendered terms of the authorized union, with a single ephemeral Lucene
BM25 scorer. Sorting is descending score followed by chunk, revision and representation IDs.

Successful calls require the exact declared and installed bm25s 0.2.14, NumPy 2.5.4 and SciPy
1.18.1 backend; absence or mismatch refuses rather than falling back. The analyzer is the actual
default technical analyzer, with its prefixed ID compared to the core's bare fingerprint. No
scorer is retained. Empty or out-of-vocabulary queries and empty authorized corpora return empty
hits only after source, authority and backend validation.

Inputs and scorer work have finite limits: 8,192 query codepoints, 2,048 query terms, 200,000
stored allowed terms, 100,000 vocabulary terms, 200,000 postings and 4,000,000 query-document work
units. The single deadline is cooperative; it does not promise hard latency or peak memory bounds.
This DATA search does not establish readiness, current rights, model origin, license compliance,
evaluation quality, security qualification, or 20k-scale performance.

The backend parameters are `method=lucene`, `idf_method=lucene`, `k1=1.5`, `b=0.75`,
`delta=0.5`, `dtype=float32`, `int_dtype=int32` and `backend=numpy`. The full score vector is
validated for shape, dtype, and finiteness before selection. Partition caps apply after ranking
within each authorized partition; global ranks are assigned after merging partition selections.
Query text is limited to 32,768 UTF-8 bytes. Caller authority is bounded before recursive copying:
at most 128 items per tuple, 65,536 combined string codepoints and 262,144 bytes of combined
canonical JSON. Input caps must be exact integers in 1–60, and the deadline is 1–120,000 ms.
