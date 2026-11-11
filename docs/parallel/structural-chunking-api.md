# Preparatory structural chunking API

`chunking.build(registry, blocks, counters, query, policy=None)` returns immutable chunks
and reciprocal neighbor records or raises the fixed `ChunkingError` without a partial result.
Supply all ordered blocks for one registry revision and extraction. Registry binding is checked;
source fragments retain exact Unicode offsets. Headings are included as literal context in the
representation counted by the operator callbacks. Table continuation repeats the original header.
Prose splits only at sentence boundaries; indivisible overlength units are refused. Actual pair
counts use the complete query and representation. Counters must be trusted cooperative operator
callbacks, including special tokens, with three distinct identities. The work deadline cannot
interrupt a blocking callback. Counts are marked SUPPLIED_UNVERIFIED; a production qualified
artifact adapter and independent model tokenizer qualification remain required. No model or
hardware measurement is implied. This preparatory implementation does not implement conditional
paragraph overlap or full procedure-warning grouping and is not full 006 acceptance.
