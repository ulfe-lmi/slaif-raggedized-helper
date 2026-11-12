# Isolated CPU embedding session

`IsolatedCPUEmbeddingSession(manifest_bytes, artifact_root, definition, tokenizer_definition,
expected_inventory_id, tokenizer_runtime, cpu_runtime, *, worker_policy=None, parent=None)`
performs scalar preflight at construction. Entering the context owns a verified private artifact
stage, a native token ID session, and a fixed resident CPU worker in that order. Both runtimes
must explicitly select CPython 3.12 and their protected packages; their roots and ancestry must be
trusted. Callers must establish current rights before exposing content. Neither inventory nor a
source plan proves authorization.

`encode(texts)` accepts a bounded list or tuple of strings and returns frozen normalized vectors,
ordered native receipts, space and definition IDs, and execution provenance. `embed(texts)` returns
fresh mutable lists. All token receipts are checked before one CPU forward; failures return no
partial batch and do not retry neural inference. A native worker may be renewed before its budget
is exhausted; the resident CPU worker is not reloaded. Sessions reject concurrent, reentrant,
forked and closed use. The creator-PID refusal does not make forking a multithreaded
application safe. Limits are software bounds, not a throughput qualification.

`intended_execution_fingerprint` identifies the legacy CPU FP32 execution intent. The separate
canonical schema-2 `execution_record` and `execution_fingerprint` bind the successful worker handshake,
profile, policies, native identity, normalization and selected code hashes. A future producer must
explicitly bind and compare both identities. The profile hash selects declared pinned package
metadata; it does not attest package files, license terms, or distinguish fake from neural execution.
No hardware qualification is inferred.

Close is finite and idempotent after successful release. A `SessionRefused` with `pending` true
retains its cleanup owner in `owner`; retain it and retry `owner.close()`. A CPU child that has not
been confirmed released keeps the stage alive. Cleanup refusal after the staging context has
exhausted remains pending and is not retried as if it succeeded. A body exception or interrupt is
preserved with a fixed cleanup note and `cleanup_owner` when needed. An uninterruptible kernel task
cannot be guaranteed reaped. The stage never purges foreign replacements.

The synthetic tests use a trusted fake framework in the real process protocol; they do not load a
real model or establish security, license clearance, model parity, performance, or hardware
readiness. The runtime, packages, protected artifact ancestry and caller remain trust boundaries.

The schema-2 execution hash uses `isolated-cpu-embedding-execution-v2`, deliberately changing
the v1 execution identity while preserving the legacy space and intended CPU FP32 identities.
See [the pre-model contract and plan API](cpu-embedding-plan-api.md) for prediction and the
consumer comparison required before content forwarding and output completion.

Native startup is owned before construction begins. If native cleanup remains pending, the
session retains both that exact tokenizer and its stage; `SessionRefused.owner` or an
interrupt's `cleanup_owner` provides the owner for a bounded later `close()` retry. CPU startup
is not attempted after native startup fails. A child that cannot be reaped keeps its borrowed
artifacts and stage pending.
