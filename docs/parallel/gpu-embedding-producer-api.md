# One-batch GPU embedding producer

The root preparation amendment in `gpu-embedding-producer-design.md` replaces
the original borrowed-preparation contract. The intended internal interface is:

```python
produce(original_store, bundle_metadata_bytes, bundle_members, chunk_ids,
        manifest_bytes, artifact_root, embedding_definition, tokenizer_definition,
        expected_inventory_id, runtime, launch_inputs, reservation, store,
        journal_root, authorization_provider, *, purpose="prepare",
        representation_policy=None, batch_policy=None)
```

`LaunchInputs` contains the five absolute roots, exact device plan, driver tuple,
resource policy and wire policy for the fixed GPU launch. It is trusted operator
configuration, not request data or authorization. Native `runtime` is an
independent tokenizer runtime. The caller retains the actual mode-operation
reservation and both stores throughout the operation; neither is transferred to
the producer.

The producer preallocates and retains an actual `PreparationOwner` before each
fallible preparation. It owns each preparation, capture, journal lease, and any
GPU parent and native session it starts. A failed capture identifies its own
cleanup; a successful handoff exposes the same actual `PreparedLaunch` even if
return is interrupted. The capture cannot itself drain a live handoff. The
parent consumes preparation A. After confirmed
native and parent drain, preparation B rechecks the same source and execution
contract without starting another GPU parent, and closes before `COMPLETE`.
`COMPLETE` reuse creates and closes a fresh preparation without starting a GPU
parent. A pending owned resource must drain before its associated job lease can
be released. Cleanup uncertainty is not proof that a lock remains held or a
physical device is vacant.

The authorization provider is required trusted application wiring. For canonical
plan bytes and each named boundary, it must freshly check the current rights for
every source row and purpose and return a bare 64-hex epoch. The epoch must remain
unchanged across the call. The boundaries are `before_model`, `before_encode`,
`before_publish`, `before_complete`, and, for completed work, `before_reuse`.
The caller must establish permission before invoking planning or native source
counting. The synthetic tests' provider is not a current policy service.

Only a fresh `PENDING` job may start an attempt. Other unfinished or terminal
states are refused; the producer does not steal owners, retry, repair stale jobs,
or promise exactly-once execution. Attempted dispatch followed by failure may
be `UNKNOWN_COMPLETION`. A published but uncommitted batch may remain an
immutable orphan. An error around a journal commit is reconciled by rereading;
committed `COMPLETE` is never downgraded.

The result contains the job ID, output reference, canonical metadata, validated
batch, complete execution record, detached native record, execution fingerprint,
and a reuse flag. The closed typed-batch format stores the execution fingerprint,
not those full records. A stored batch or hash is not permission, neural-origin
proof, or readiness. Ordinary refusals are content-free; a pending cleanup owner
must be retained and only its supported creator-owned cleanup retried. For an
interruption that cannot carry attributes, `pending_cleanup(error)` retrieves the
unique associated pending owner by exception object identity; it returns `None`
if the same exception object is associated with more than one pending operation.
The association keeps that exception and its traceback in process memory until
the owner drains; it is not a durable record or a source of authorization.

Synthetic GPU worker tests do not qualify a model, FP16 behavior, hardware,
device vacancy, restore, throughput, security, licensing, or evaluation. Bulk
scheduling, retry, current-principal policy, controller and real hardware
qualification remain separate work. The preparation-owner prerequisite is
integrated through the ordered local preparation merge. A synthetic full fresh
production and separate fresh-process reuse passed under the amended outer test
budgets; the full positive preceded a later exception-association-only change,
so it is not an exact-current-source run. Historical 30-second outer-driver
failures remain failures. These tests are not development acceptance.
