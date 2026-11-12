# Source embedding program API

`build(originals, derived, bundle_ids, *, policy=None, batch_policy=None, program_policy=None)`
loads and revalidates every selected ingestion container. IDs must be a sorted, unique tuple of
bare container hashes. The result is immutable source data, with ordered batches that do not cross
bundle boundaries. Stores are borrowed. `parse(program_bytes)` checks canonical structure and
returns data without accessing stores. `validate(originals, derived, program_bytes)` freshly
rebuilds the selected sources and requires identical bytes.

`ProgramPolicy` sets bounded counts, serialized bytes and a cooperative deadline; defaults and
maximums are 128 bundles, 65,536 rows, 65,536 batches, 16 MiB and 120 seconds. Policies can lower
these limits. `ProgramError` contains no source content. Temporary encoding includes each record
for incremental byte accounting, including the pending batch, and a final whole manifest; it is not a hard memory or I/O bound.

The program contains hashes and size facts, not source text. Its ID identifies source data only.
Native token counts, current rights, execution compatibility and completion are not established.
An executor must freshly validate and independently enforce the relevant producer, job and policy
checks. No model or worker is started by these APIs.
