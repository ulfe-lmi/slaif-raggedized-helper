# Selected-program row coverage

`raw_snapshot_program_coverage.build(originals, derived, program_bytes, declaration_bytes, completion_bytes, *, deadline_ms=30000)` returns a frozen `CoveredRowMap`. The stores are borrowed `OriginalStore` and `derived_store.Store` instances; the function does not close them or publish anything. Ordinary refusals raise content-free `CoverageError`; non-`Exception` interruptions propagate.

The completion is canonical ASCII JSON with exactly `schema: 1`, `kind: "slaif-raw-program-output-selection-v1"`, `source_program_id`, and `outputs`. Each output has exactly `batch_index`, `container_id`, and `metadata_sha256`. Entries must cover the program batches in index order, with distinct containers. The source program is freshly validated, bounded to 4096 rows, 128 batches and 128 sources, and must use the default representation and batch policies. Smaller valid program-policy limits are supported.

Each supplied batch and source bundle is loaded and checked against the actual program slice. The row constructor then performs its own fresh validation. The resulting map is checked by chunk identity, including the original batch row index, and the program is validated again before returning. The deadline is cooperative; it cannot preempt an underlying operation. Revalidation detects persistent changes, not an intervening change restored before observation.

`coverage` is `COMPLETE_SELECTED_PROGRAM`, `execution_origin` is `SUPPLIED_UNVERIFIED`, and `qualification` is `NOT_QUALIFIED`. These describe the selected data cut only. They do not prove encoder execution, journal completion, current rights, a complete corpus, model or hardware qualification, or readiness. The caller must separately establish publication and authorization requirements.
