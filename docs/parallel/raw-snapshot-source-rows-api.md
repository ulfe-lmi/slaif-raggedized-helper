# Fresh source and stored row group

`load_group(originals, derived, row_map_bytes, bundle_container_id, batch_container_id)`
loads one selected group through the existing private stores. It revalidates source and
bundle, reconstructs default raw representations, checks declared batch rows and returns
frozen data with detached FP32 little-endian vector bytes in map order. The stores are
borrowed. Ordinary refusal raises a content-free `SourceRowsError`.

The result supports fresh original-source and stored normalized-row correspondence. It
does not prove native token counts or execution, current ACL or rights, whole snapshot
readiness, actual model or neural origin, hardware qualification, or independent
acceptance (ICA). Rendered indexing text is not original answer evidence. Only selected
rows are resolved. Time checks are cooperative; the 30-second limit is not preemption.
