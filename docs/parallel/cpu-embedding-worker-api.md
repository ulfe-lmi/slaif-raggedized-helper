# CPU embedding worker

`CPUEmbeddingWorker(manifest_bytes, private_artifact_root, definition, tokenizer_definition,
expected_inventory_id, runtime, policy=None)` owns one subprocess. `runtime` is a
`native_tokenizers.Runtime` specifying a protected CPython 3.12 root, its trusted private
site-packages directory, and `python3.12`. The caller keeps the protected, closed staging tree
alive and unchanged until `close()` finishes; the worker never deletes it. Use the worker as a
context manager or close it explicitly. `space`, `vocab_size`, `profile`, `policy_fingerprint`,
and `code_fingerprint` describe the admitted space and execution provenance. The latter three
are not space identities.

The parent verifies the inventory, space, closed tree, configuration vocabulary, fixed lock hash,
and exactly the 38 locked distribution metadata versions before starting the child; unknown or
duplicate distributions are refused, with bounded metadata and directory enumeration. The child repeats
profile and artifact admission through the existing backend before sending ready. The selected
runtime and packages are trusted and protected: metadata and lock select a profile, they do not
cryptographically attest installed files or clear their licenses. The backend alone loads the fixed
model with its CPU FP32 and offline options. Neither a model, script, factory, device, nor arbitrary
model arguments are selectable through this interface.

`forward_cls(sequences)` accepts 1 through `max_rows` sequences of 2 through 1024 strict integer
IDs in the admitted vocabulary. It validates the complete batch before sending it, refuses rather
than truncates, and returns ordered immutable raw CLS float rows of 1024 values. It does not
normalize, store, authorize documents, or establish CPU/GPU parity. Errors are sanitized; a failed
operation closes the process with no retry or fallback. Concurrent forwards are refused without
interrupting the active call. Cleanup preserves an exception raised inside the context.

The private newline-delimited UTF-8 JSON protocol uses exact keys, unique object keys, and finite
numbers. Startup carries the bounded manifest, definitions, expected identities, and policy. A ready
frame binds space, definition fingerprint, profile, policy and code fingerprints, observed vocabulary,
and CPU FP32 CLS contract. The child checks these identities and independently admits the claimed
space before constructing the backend. Code identity hashes a canonical filename-to-hash map with
versioned schema and API markers.
Each call includes a random nonce and SHA-256 of the canonical JSON ID batch. A complete reply must
bind both values and the space and profile, and contain the exact number of finite, exactly
binary32-representable float rows. All replies are checked before returning any rows. Child stderr is
discarded. No caller text, path, or arbitrary code is part of normal protocol errors.

Defaults and hard ceilings are respectively: rows 8/128; request 2 MiB/2 MiB; response 8 MiB/8 MiB;
startup 120/120 seconds; forward 30/120 seconds; lifetime 3600/3600 seconds; cumulative CPU
600/600 seconds; address space 16/16 GiB; calls 1024/1024; cumulative input 32/32 MiB and output
256/256 MiB. `Policy` accepts positive integers only and can lower each ceiling. These are software
limits, not a claim that real weights fit or hardware is qualified. Parent I/O is nonblocking and
deadline bounded; timeout, malformed frames, EOF, death, or cap violation terminate and reap the
owned child. An independent owned `timeout` watchdog enforces the lifetime even if the parent is
paused; the child also accounts for cumulative input and output. The child runs in the accepted bubblewrap/prlimit envelope with read-only artifacts,
profile, source and runtime; a cleared environment; private temporary home; no network namespace
connectivity to the host; and synthetic device nodes. There is no unsandboxed fallback.

Tests use a test-only fake neural provider and synthetic artifact bytes. They do not establish real
model readiness, hardware capacity, license clearance, or a complete neural security qualification.

The standalone integration tests require `SLAIF_CPU_V2_TEST_ROOT` and
`SLAIF_CPU_V2_TEST_PACKAGES` to name an existing approved CPython 3.12 runtime and its
locked profile. Missing prerequisites fail loudly. The tests acquire no dependencies and perform
no real model loading or inference. A portable CI fixture is a separate setup task.

The parent and pre-model prediction select `worker_profiles/cpu-v2/uv.lock`. The
38 declared metadata versions select the profile and do not attest actual package
code. The independent native tokenizer engine, definition, policy and receipts stay
at 0.21.4; framework tokenizers 0.23.1 is a separate dependency. Semantic space,
definition and intended CPU FP32 identity remain unchanged; complete execution,
profile and code fingerprints and dependent job IDs change. Trusted fake protocol
tests exercise prediction and the staged parent/native/child handshake, not real
neural behavior. Canonical integration and CI must provision both legacy and v2
fixtures. Actual class loading, a newly owned toy model, BGE, ABI, security, license,
numerical parity and independent coverage audit remain future gates.
