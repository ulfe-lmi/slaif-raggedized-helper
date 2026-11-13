# Text evaluation dataset admission

`admit(dataset_bytes, *, deadline_ms=5000)` accepts canonical ASCII JSON bytes under the exact schema and limits in the accompanying design. It returns frozen records and tuples containing private declared data, canonical bytes, counts, and distinct dataset and split identities. Invalid input or an expired cooperative deadline raises `DatasetError("text evaluation dataset refused")`; non-Exception interruptions propagate. The decoder is bounded by the input limit, not preempted during decoding.

All outputs remain `NOT_QUALIFIED`, with `DECLARED_UNVERIFIED` authorship and rights and a `STRUCTURAL_ONLY` split. Origin and opaque references are declarations, not attestations. Empty scope lists are unspecified test metadata, not authorization. Null product or version means unknown. Unknown answerability is not a successful abstention.

Gold atoms use original Unicode codepoint offsets and declared substring hashes. Atoms within an alternative are conjunctive, alternatives are disjunctive, and requirements are conjunctive. Admission cannot establish actual source, block, substring, rights, semantic leakage, or human origin. Synthetic held-out cases do not pass human evaluation. A later run must bind both identities and independently verify sources and rights.

The accompanying oracle is a synthetic wrapper; encode its `dataset_ascii` field as ASCII to admit it. It is not a dataset itself or a human-held-out baseline. No metrics, model execution, or evaluation pipeline are supplied here.
