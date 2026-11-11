# Isolated native tokenizer counting candidate

`native_tokenizers.count(Definition, Runtime, text, pair=None, policy=None)` returns a
`Count` or raises an input-free `TokenizerError`. A count of zero is a valid result;
a failure has no count. The operator declares the SHA-256 of the local JSON, the
backend version (`0.21.4` only), role (`bge_body`, `bge_representation`, or
`reranker_pair`), model revision and preprocessing definition. The strings passed
are already transformed according to that definition. The pair role requires both
query and passage; the other roles require one string. Same artifact may serve both
BGE roles; use the separately declared reranker artifact for its role. The result
binds actual file hash, declared revision and preprocessing, role, mode, backend,
serialization policy, and SHA-256 of the exact compact ASCII-escaped JSON array
`[text,pair]` (UTF-8, no spaces). Revision and preprocessing are declarations, not
verification of inference equivalence. No raw text, tokens, paths or native errors
are returned. The digest can be sensitive to dictionary attacks and is not an
anonymization mechanism.

The parent reads a no-follow regular file through a bounded descriptor, checks size
and metadata before and after reading, verifies its hash, and mounts an owned copy.
The fixed worker loads `Tokenizer.from_file`, calls `no_truncation()` and
`no_padding()`, verifies both properties are `None`, and uses `encode` with
`add_special_tokens=True`. Pair templates and specials come from the artifact, not
sums or assumed overhead. Native imports occur only in the worker; no AutoTokenizer,
remote-code loader or fetch is used. Use callbacks extracting `.count` with
`chunking.Counters`; its provenance remains `SUPPLIED_UNVERIFIED`.

Default and maximum policy limits are 4 MB artifact, 200 KB request, 100,000
characters, 200,000 count, 4096 output bytes, and 5 seconds wall time. Each call
starts one worker. Limits may be lowered but not increased; integer and finite types
are strict. Linux x86-64, bubblewrap user/PID/network namespaces, prlimit, and an
explicit trusted Python runtime and package directory are prerequisites. The fixed
worker sees read-only runtime, package directory, input files and selected system
libraries, an empty tmpfs and isolated /proc and /dev; environment and inherited file
descriptors are cleared. CPU is limited to 3 seconds, address space to 512 MiB,
open descriptors to 32, and file size to 4096 bytes. Output is read with a byte cap;
timeout, errors and cancellation terminate and reap the owned process. Operators must
bound concurrent calls externally. Runtime, packages, native code and system
libraries are trusted operator inputs; neither the artifact nor a request selects
code or an executable. Unsupported hosts must refuse; there is no unsandboxed fallback.

The 0.21.4 wheel used in development is not a project dependency or license
clearance. Source Apache terms, native/transitive components and notices still need
review. The two owned synthetic JSON fixtures establish only the tested API behavior,
not arbitrary hostile-file or supply-chain security. Actual pinned BGE and reranker
artifacts, preprocessing and inference-tokenizer parity remain unqualified; they
require the applicable 006/007/012/019 work and independent audit. No actual model
identity, rights, GPU or MVP qualification is implied.
