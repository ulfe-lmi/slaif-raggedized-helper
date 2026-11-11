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

Default and maximum policy limits are 32,000,000 bytes artifact, 200 KB request, 100,000
characters, 200,000 count, 4096 output bytes, and 5 seconds wall time. Each call
starts one worker. Limits may be lowered but not increased; integer and finite types
are strict. Linux x86-64, bubblewrap user/PID/network namespaces, prlimit, and an
explicit trusted Python runtime and package directory are prerequisites. The fixed
worker sees read-only runtime, package directory, input files and selected system
libraries, an empty tmpfs and isolated /proc and /dev; environment and inherited file
descriptors are cleared. CPU is limited to 3 seconds, address space to 512 MiB,
open descriptors to 32, and file size to 4096 bytes. Output is read with a byte cap;
timeout, errors and cancellation terminate and reap the owned process. Child output must be strict UTF-8 JSON with unique keys; the nonce matches request and response but is not an authentication mechanism. Operators must
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


The 32,000,000-byte default and hard maximum admit the approximately 17.1 MB
class observed in mutable public metadata, while bounding descriptor reads and
memory. Metadata is not a pinned artifact or qualification. Smaller policy values
are supported. Large-file tests pad an owned tiny valid JSON with whitespace; they
do not measure full vocabulary performance or establish real-model parity.

For required native development tests on Linux x86-64, use a trusted standalone
CPython 3.12 base runtime and a new, nonexistent private target directory:

```sh
python3 tests/support/prepare_native_test_backend.py \
  --runtime-dir /path/to/cpython-3.12-base --target /path/to/new-private-capsule
```

The helper checks the actual base prefix, CPython version, installed inventory and
engine API, and emits shell-quoted `SLAIF_NATIVE_TEST_ROOT`,
`SLAIF_NATIVE_TEST_PYTHON=python3.12` and `SLAIF_NATIVE_TEST_PACKAGES` exports.
Run those exports in the test shell. It requires `uv` on PATH, uses the explicit
PyPI registry, a clean child environment, binary-only installation and the pinned
SHA-256 in `tests/support/native-test-requirements.txt`. It refuses existing
targets. On a failed install, inspect and remove only the newly created target you
own before retrying. The target is mode 0700. The worker also requires Linux
bubblewrap with working user, PID and network namespaces, `/usr/bin/prlimit`,
`/usr/bin/timeout` and compatible system libraries; availability of binaries alone
is not namespace qualification.

This is an intentionally engine-only `--no-deps` development capsule for the fixed
`Tokenizer.from_file` and owned fixture API. The upstream wheel declares
`huggingface-hub`; hub functionality is not provided or tested. This is not a
complete application dependency installation, release graph, license clearance,
or model acquisition. Native, vendored, transitive, model and platform audits
remain 018/release gates. No model files or weights are downloaded.

Tests generate their own artifacts and fail explicitly if configuration or the
backend is missing. Run the native and session unit and composition suites with
project test dependencies installed. Each fixture worker uses a 2-second wall
allowance with up to 1 second cleanup; this is distinct from the library's 5-second
production ceiling and 3-second CPU limit. The parent interpreter and explicitly
configured worker interpreter may differ and must be reported separately. Host
isolation tests are host-specific; this helper alone does not qualify CI, inference,
serving, hardware, quality or MVP readiness.
