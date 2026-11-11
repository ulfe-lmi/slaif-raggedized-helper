# Bounded native tokenizer session

`Session(definitions, runtime)` starts one isolated fixed worker. Use it as a context
manager, then call `session.count(role, text, pair=None)` for the same `Count`
identity semantics as `native_tokenizers.count`. Definitions are explicit and
hash verified; up to two distinct artifacts and three distinct roles are accepted.
The pair role requires an explicit second string, including an empty one. Native
parsing occurs in the worker, with special tokens enabled and truncation and padding
disabled. There is no automatic retry or replay after refusal.

The worker is bounded by a 20-second lifetime, 10 CPU seconds and 1 GiB address
space; startup is limited to five seconds, requests to two seconds, and cleanup to
one second. At most 1024 requests, 16 MB request bytes and 4 MB response bytes are
accepted. Requests are capped at 200000 bytes and 100000 characters; responses at
4096 bytes and 200000 tokens. Each response is tied to a nonce, role, artifact and
input digest. No input or native exception is placed in errors. Callers own sessions
and must close them; a failure closes the session. There is no shared cache.

Linux bubblewrap, prlimit, timeout and a trusted local runtime and package directory
are required. Runtime, packages and system libraries are read-only mounts but remain
trusted local filesystem inputs, not immutable supply-chain attestations. The parent
reads bounded raw artifact bytes and mounts copies. The caller must limit concurrency.
Counts and timings are software evidence only; preprocessing/inference parity,
licenses, rights, hardware and production qualification remain open.
