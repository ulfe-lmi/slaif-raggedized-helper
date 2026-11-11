# Native ingestion bundle publication and load contract v1

Status: FINAL DEVELOPMENT CONTRACT
Authority: Root strategic D0, architecture8.1–8.3/9.3/20.2/25.2 and full native-bundle-v1.md.
This contract does not activate coding, accept a candidate, authorize target resources or close006.

The storage adapter composes the accepted derived Store and complete semantic bundle validator.
Use bytes-first publish(originals: OriginalStore, derived: derived_store.Store, metadata: bytes,
members: immutable tuple[(name,bytes),...])->raw64hex container ID. Validate/canonicalize every
semantic member against the actual verified original BEFORE Store.publish. Build fixed Member
values from canonical bytes, preserving exact five-member order. Do not accept an unchecked
Validated DTO, arbitrary Snapshot or cached Registry as evidence. No producer/model/parser/runtime
path selection is added by this adapter. Callers own and close both trusted store objects.

Load(originals, derived, container_id)->immutable ingestion_bundle.Validated first uses bounded
Store.load for manifest/member integrity and descriptor safety, then always reconstructs the
canonical metadata bytes and calls the complete semantic validator against the current verified
original. Store.load alone does not establish native ingestion trust. Store metadata is a frozen
opaque value; use its bounded verified manifest to recover the metadata object and canonicalize
it without an unsafe generic DTO/model_copy traversal. Preserve Store's independent admission
limits; fixed full-bundle schemas and tighter limits remain enforced by semantic validation.

Both operations admit exact trusted store types and bounded immutable inputs/container ID before
work. Container IDs are raw64lowercasehex, never paths or source-provided filenames. Type/kind,
member count/order/names, corruption, wrong ID and incompatible policy/schema refuse with one
input-free adapter error. No tokenizer/PDF/model/subprocess/network action on load or publication.
Actual producers are used only by owned tests or later explicit trusted operator preparation.

The semantic validator and Store each retain their 30-second cooperative budgets. The adapter
checks a finite60-second monotonic overall budget between phases and before returning; this is
a ceiling on cooperating work, not an interrupt of blocked filesystem operations or a hard RSS
claim. A publication deadline/failure AFTER the manifest link may leave a complete committed
container. Never promise rollback, delete published content or relabel this as partial success.
The call returns no successful ID on failure; retry with unchanged canonical bytes converges to
the same ID if original verification still passes. Preserve owned-stage cleanup semantics and
leave orphan collection/retention to later separately authorized lifecycle work.

Positive proof: owned OriginalStore -> actual text/PDF extraction -> actual native counts/chunks
-> complete semantic validation -> content publication -> close -> fresh store objects AND a fresh
process load -> full source/span/coverage/heading/neighbor/receipt validation and same immutable
canonical result. Distinct revisions sharing bytes retain distinct rights/version/labels and
identities. Original bytes remain unchanged. Repeat publication is deterministic and concurrent
publication uses existing Store convergence semantics; this adapter must not invent another lock.

Negative proof: opaque container with wrong native kind/schema/members, corrupt manifest/member,
wrong ID/root, altered verified original, cross-source/revision, invalid policy/receipt/coverage/
neighbor, expired overall deadline including the final return, and closed-store refusal without
cross-store FD reuse. Integrity refusal precedes semantic admission of corrupt bytes. All
required backend tests fail explicitly if missing; no skipped proof. Component fault matrices
already cover Store crash/fsync behavior; repeat only causal adapter failure boundaries.

Verified original and mechanically consistent native receipts do not prove producer authenticity,
fresh extraction, query-only reserve counts, PDF completeness/visual fidelity, actual inference
preprocessing or current serving authorization. Trusted producer and pinned bundle ID/private
storage remain assumptions. No source Scope is accepted as reader authorization. Full model,
hardware/domain/held-out/license/ICA/full visual MVP and deployment gates remain open.

This module exposes a library adapter. A separate thin installed operator chunk/inspect route
must still invoke the actual fixed producer, this adapter and a fresh semantic load, report safe
IDs/counts/status rather than source/query text, preserve honest visual-needed/no-native-chunks
outcomes and return nonzero typed errors. No implicit downloads/inference/network/GPU, document
executable selection or product human-owner referral is introduced. Whole006 requires that usable
durable operator journey, relevant source coverage and exact-head CI before its PR can merge.
