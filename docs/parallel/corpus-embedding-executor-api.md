# Selected-source corpus executor

`run(originals, derived, program_bytes, manifest_bytes, artifact_root, embedding_definition,
tokenizer_definition, expected_inventory_id, runtime, launch_inputs, reservation, journal_root,
authorization_provider, *, deadline_ms, purpose="prepare")` borrows both stores and the actual
reservation. The caller must establish permission before invoking it. The required trusted
provider is called with each actual per-batch plan and producer boundary; one epoch must hold for
the operation. No result or stored data conveys current authorization.

A successful frozen `CorpusResult` includes the source-program ID, total row count, lightweight
batch completions, and one common full execution/native record pair and execution fingerprint.
Each completion contains its batch index, job ID, output reference, metadata hash and reuse flag.
The complete source selection is freshly validated before and after execution. A refusal can leave
already completed batch journals and outputs intact; the producer's exceptions and pending cleanup
remain accessible to the caller. Only the existing journal decides whether a batch can be reused
or started. The explicit deadline is cooperative, at most 24 hours, and does not preempt I/O or
workers. There is no throughput or hardware qualification claim.
