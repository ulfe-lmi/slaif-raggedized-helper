# Literal PDF structure classifier

`pdf-literal-structure-v1` classifies an immutable tuple of `Line` values without I/O. It returns one kind per input and preserves original text. It accepts at most 4096 lines, 500000 total characters and 200000 characters per line, pages 1–32 and finite ordered bounding boxes. Invalid input or a cooperative two-second budget exhaustion raises an input-free `StructureError`.

Only single logical lines are considered. Lists require a literal bullet or numbered marker. Tables require a literal multi-column header, a following hyphen rule, and at least two same-page rows with matching column starts (or matching pipe column count). The rule is retained as a table row. Incomplete, multiline and unsupported material remains text. These limited literal heuristics cannot solve arbitrary PDF layout; this helper does not establish PDF integration, visual fidelity, or MVP acceptance.
