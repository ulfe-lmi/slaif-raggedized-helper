# Private dense trace

`search(..., trace=True)` opts into private, ephemeral authorized dense stage identities. The default is `False`, returning `DenseResult.trace = None`; an empty captured trace is distinct. This adds a field to the public dataclass and its `asdict` shape, while preserving its twelve positional arguments. Trace records hide their contents in default repr, but explicit access, equality, hashing, serialization and export remain caller controlled. They are linkable data, not anonymized or an access grant. No implicit logging or persistence is performed.

The rows and stages describe supplied-scope checks and observed dense selection only. Frozen records and fingerprints do not attest execution or current rights. Later lexical, fusion and hybrid capture and original-source coverage require separate designs. This does not establish source gold, held-out quality, model execution, current authorization or MVP qualification.
