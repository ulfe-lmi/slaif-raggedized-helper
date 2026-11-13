# Private snapshot DATA publication

`publish_directory(originals, derived, store_root, core_bytes, files)` validates the
actual original and derived stores and the exact sorted file tuple, then returns frozen
`Publication(snapshot_id, created, data)` after a fresh directory read. Stores are
borrowed. The caller must establish processing permission before calling; this API
provides no rights, Ready state, current pointer, deployment, or model qualification.

The configured root must already be an absolute canonical private 0700 directory
under trusted ancestors. The publisher may create its `snapshots` container. It stages
a private tree and uses Linux `renameat2(RENAME_NOREPLACE)`, never overwrites a target,
and validates an existing target before reuse. Cooperating publishers use a bounded
advisory lock on the pinned namespace so staging does not invalidate the reader's
stability check. Other writers are not trusted and can cause refusal. File and directory
fsync calls establish the documented local sequence, not universal power-loss proof.

`PublicationError` contains a candidate ID when computable and
`publication_may_exist` after a rename attempt; neither proves publication. A caller
may use the actual directory reader to investigate. Non-Exception interruptions are
preserved. Creator-owned cleanup failures retain the operation for a creator-process
`retry_cleanup()` through the module's pending owners; concurrent or nested retry
is refused before resource access. A still-unknown descriptor close returns a
`CleanupPendingError` result and the numeric descriptor is never retried. An interrupted rename may leave an unreferenced final tree. Never remove it
as recovery. The actual reader and original sources are revalidated before success.

The inherited 4096 row limit remains; this is not efficient-scale qualification.
Rights, query integration, retention, current selection, real models, hardware, licenses,
held-out evaluation, canonical integration, ICA and deployment remain separate gates.
