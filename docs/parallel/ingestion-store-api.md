# Native ingestion store adapter

`ingestion_store.publish(originals, derived, metadata_bytes, members)` verifies the complete
bundle against the original and publishes canonical bytes, returning a raw lowercase SHA-256 ID.
`load(originals, derived, id)` verifies storage integrity and revalidates the complete bundle
against the current original, returning an immutable `ingestion_bundle.Validated`. Both refuse
with input-free `IngestionStoreError`. Callers own and close both exact trusted store objects.
Inputs and component limits are those of the bundle validator and derived store. The additional
60-second deadline is cooperative, checked between phases and at return; it cannot interrupt
blocked filesystem operations or guarantee memory use. Failure after publication may leave a
complete visible container; unchanged canonical retries converge if the original remains valid.
No deletion or rollback is attempted. Store cleanup and concurrency semantics remain unchanged.

This private operator API assumes a trusted producer, private stores and a pinned container ID;
mechanical validation does not prove producer authenticity or serving authorization. Loading parses the JSON manifest and reparses pure structured text for verification. It performs
no PDF parsing, inference, tokenization, subprocess or network operations. The installed chunk and
inspect operator journey, PDF integration, current CI, 019, model and domain qualification,
license audit, independent audit and full visual MVP remain open. No deployment is implied.
