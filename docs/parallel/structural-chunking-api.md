# Preparatory structural chunking API

`chunking.build(registry, blocks, counters, query, policy=None)` returns immutable chunks
and reciprocal neighbors or a fixed input-free `ChunkingError` with no partial result.
Supply every ordered block of one registered revision and extraction. Registry snapshots
bind source fragments; the caller must use the same immutable registry and authorized scope.
This function does not perform authorization. Every source offset is covered; table headers
and paragraph overlap deliberately repeat original offsets. Heading path is literal context in
representation and the IDs bind policy, identities, query, source and fragments.

Defaults are body target 512, soft maximum 768, representation maximum 1024 and pair
maximum 512 with query reserve 64; all counts include whatever specials the supplied
counter adds. Policy limits narrow these bounds and also cap blocks, characters, chunks,
callback calls and total callback input characters; each chunk has at most 256 fragments.
The strict integer `deadline_ms` defaults to 5000 and ranges from 1 to 15000.
The deadline is cooperative: a blocking trusted callback cannot be interrupted.
The complete body, heading plus body, and query plus heading plus body are measured separately.
The pair counter also measures empty-query and empty-passage cases, and the latter must fit
the query reserve. Contradictory repeat measurements and invalid results are refused. The effective deadline is
part of the policy fingerprint, so changing it changes policy and chunk IDs.

An immediately adjacent warning or prerequisite and numbered procedure, optionally separated
by one blank block, are grouped ahead of target when their combined budgets fit. Other content
is not bridged. Code blocks remain whole or are refused. Tables repeat the original header and
separator with continuation rows. Oversized prose is split at sentence boundaries; where a
paragraph crosses a chunk boundary, the longest fitting word-boundary suffix of its preceding
sentence is repeated, measured by the body counter and capped at 64 supplied tokens. No
sentence or tail is silently truncated. Indivisible overlength units are refused.

Counters are trusted operator-supplied callbacks, never selected by document text. Body and
representation are explicit modes and may share the same actual BGE artifact identity; the
reranker identity must be independent. Counts are `SUPPLIED_UNVERIFIED`, not evidence of a
qualified tokenizer. A production qualified-artifact adapter, full 006, independent audit and
MVP gates remain outstanding. No model, hardware or real-corpus qualification is implied.

A maximal adjacent chain of recognized warnings, prerequisites and numbered procedure
items (with at most one literal blank block between units) is kept together when all
budgets fit, even above the target. If the chain cannot fit, eligible adjacent pairs
are considered independently; unrelated text is never crossed. Empty originals have
no blocks and are refused by this builder. Zero-length blocks contribute no fragments;
a revision containing only zero-length blocks is refused. Indivisible over-budget
units are refused. Registry validation happens at construction and its in-memory
snapshot is used for binding; this is neither persistent storage nor authorization.

Structural policy definitions use version 2, binding `query_sha256` to the exact UTF-8
query bytes instead of embedding the raw query as in version 1. This changes legacy
policy and chunk IDs, including for unchanged inputs; queries are neither normalized nor
truncated. Native final policy definitions retain their separate version 1 format.
