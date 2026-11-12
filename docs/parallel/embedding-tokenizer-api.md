# Isolated embedding token IDs

`TokenIDSession(definition, runtime, policy=None)` owns one worker and copied tokenizer
artifact. Use it as a context manager and call `encode(text)` for each already-preprocessed
single string. `close()` is idempotent. Any refusal closes the session and raises the
input-free `native_tokenizers.TokenizerError`; a closed session cannot be reused.

The exact `native_tokenizers.Definition` must name backend 0.21.4, role
`bge_representation`, a 40-character lowercase hexadecimal model revision, preprocessing
`identity`, and an artifact whose SHA-256 matches its securely read bytes. The exact
`native_tokenizers.Runtime` selects the approved runtime and packages. The fixed worker loads
that copied artifact once, disables saved padding and truncation, and uses special tokens.
It returns the original input's IDs in order. The frozen receipt binds the tuple and count to
the artifact hash, backend, role, revision, preprocessing, nonce and SHA-256 of compact
ASCII-escaped JSON `[text,null]`; its serialization label records the encoding contract.

`Policy` permits only downward adjustments to these ceilings: artifact 32,000,000 bytes;
100,000 code points and 200,000 wire bytes per request; 16,384 bytes per response; 1,024
IDs per response and calls per session; 32,000,000 total input bytes and 16,000,000 total
output bytes; 300 seconds lifetime, 5 seconds startup and 2 seconds per request. The child
is limited to 1 GiB address space and 30 CPU seconds. A hard timeout also ends an idle child.
Limits are refusals, never truncation. No throughput or latency qualification is implied.

The existing native isolation profile supplies namespaces, no network, cleared environment,
private home and read-only runtime, packages and artifact mounts. This relies on the host
providing trustworthy runtime/packages and working OS sandbox tools. A receipt is evidence of
this tokenizer operation, not authorization to expose content, model provenance, model/tokenizer
parity, license clearance or hardware qualification. The actual model and parity gates remain
open; this fixture proof does not load neural weights.

Cleanup retains the exact child and private artifact whenever drain or descriptor cleanup is
interrupted or cannot be confirmed. `close()` makes bounded termination and reap attempts;
retry it on the retained owner after resolving the failure. Constructor or request refusal
exposes a pending owner as `owner`, and an interrupt exposes it as `cleanup_owner`. A kernel
that cannot reap the child leaves cleanup pending; no successful drain is assumed.
