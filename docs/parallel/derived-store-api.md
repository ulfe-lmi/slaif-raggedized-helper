# Private derived container store

`Store(root)` opens an existing private operator-owned 0700 OriginalStore root and creates
`derived/v1/{objects,manifests}`. Use it as a context manager or call `close()`.
`publish(metadata_json_bytes, tuple_of_Member)` returns a lowercase SHA-256 container ID.
`load(id)` returns a frozen snapshot: canonical manifest bytes, recursively immutable metadata,
and an ordered tuple of frozen `Member(name, data)` values. Failures raise input-free `StoreError`.

The canonical UTF-8 sorted-key compact JSON manifest has exactly `format` (the string
`slaif-derived-container-v1`), `metadata` (an opaque JSON object), and `members` (an ordered
array of exact `{name,sha256,bytes}` objects). The ID hashes those exact manifest bytes.
Names match `[a-z][a-z0-9_]{0,31}` and are unique; content hashes are lowercase SHA-256.
Metadata input and canonical form are limited to 262144 bytes; manifests to 524288 bytes;
there are at most 16 members, each at most 64 MiB, with at most 96 MiB total. JSON has at
most 20000 nodes, depth 32 and 430-bit integers. A 30-second cooperative monotonic deadline
cannot interrupt a blocked syscall and does not establish a hard RSS bound.

Only the operator supplies the root; its ancestors must be protected from untrusted mutation.
The store checks owner, modes, file type, content and descriptor changes, and uses fixed digest
paths. It publishes durable members before the manifest, without overwrite. An error after
manifest linking may already have committed; retry the same publication or look up its ID.
Orphan objects and stages after a crash are not garbage-collected. Storage integrity does not
validate typed ingestion bundles, rights, current serving authorization or deployment readiness.
A future typed bundle loader must validate those semantics; any future CLI needs its own gate.
