# Raw snapshot lexical partition API

`parse(bytes)` returns a frozen `LexicalPartition` containing canonical bytes, their SHA-256, headers and ordered frozen rows and terms. Parsing validates syntax only. `build_partition(originals, derived, row_map_bytes, partition_id)` reloads each actual source group and analyzes its exact rendered text with the current default technical analyzer. `validate_partition` parses and compares with a fresh build. All ordinary refusals raise content-free `LexicalError`; stores are borrowed.

The payload preserves row order, duplicates, spans and derivations. It binds the partition subset of the row map and current analyzer fingerprint. It does not establish current rights, neural origin, search readiness or authorization. The design records the exact schema and resource limits.
