# Supplied policy wire v1 — FINAL private component contract

Strategic authorship. Provenance H full MVP, ARCH §13.1–13.4/A23/A24,
E operator-byte admission remains absent, and the scoped design audit
c9499b77b67aaab5067e8b9041798071beb48b07b6eedb4277adf8b8bcc03977.
This adopts the reviewed grammar for an isolated pure decoder against
the typed implementation 191139254f327dd9d987f60db4102f2916e55611,
independent implementation review 912237c17f901bbaa21c0e56da9f354abdc2196e6a80436c848083e7ed069da9.
A separate finalized order grants execution. The decoder is only a
private supplied-policy prerequisite. Protected selection, issuance,
delivery and application policy remain separate obligations. DHA NONE.

## Boundary

`admit_policy_bytes(data: bytes) -> SuppliedPolicy` accepts exact bytes with
length 42 through 67108864 inclusive. Type and length precede field work.
The closed wire is expressly the exact framed payload in §3 of the typed
component contract, with the same versioned prefix, U32 framing, canonical
field order and strict UTF-8. The typed contract on its own establishes
identity only. This draft defines the new optional private input surface.
No envelope, checksum, second spelling, normalization or optional fields.

Use a monotone offset and fail before any length-based slice or decode that
would exceed remaining data. Consume the full prefix, top-level U32 schema
and each encoded Grants U32 schema, with each schema value exactly 1.
Check principal, document, operation, Grants vector, local pair and
cumulative pair counts before their traversals. Permit admitted empty
shapes. Require the verifier length frame exactly 32 before reading its
body. Before UTF-8 decode check both the 1048576 per-string bound and the
safe field-specific byte maximum (principal ID 128, operation 12, document
ID 1024, revision 71, source scope digest 64). Grants string values use the
per-string and aggregate/public admission limits without narrower ASCII limits.
Count each verifier and string occurrence against actual M before
construction. Require exact EOF. The raw bound checks actual C for this
exact grammar. Neither a smaller sufficient M cap nor byte estimates
replace the actual limits.

Reconstruct real PrincipalSpec and DocumentRule records without sorting,
normalizing, coercing or treating malformed values as admitted. For each
Grants record use the controlled public admit_record mapping with exactly
four keys. Invoke actual typed admit_policy for all domain checks and the
returned immutable admitted object. The factory's own Grants snapshots,
strict local checks and framed hash remain authoritative. The conservative
second public Grants admission is intentional and finite. This contract
does not require a second hash of the original input. Verification
establishes identity parity by independent encoding and real outcomes.

Reject malformed input with one fixed input-free PolicyWireError, a
ValueError subclass. Raised ordinary failures carry no own caught payload
as a cause or context. Controlled non-Exception BaseException propagates
by identity. No logs, partial outputs, IO, currentness checks or real
credential provisioning. The decoder never replaces the typed API.

## Evidence and limits

Test exact canonical/golden identity and snapshots, empty/Unicode/controls
and 20000 declarations, strict nominal input and EOF, wrong or truncated
frames and both schema refusals, actual count/remaining/M/C boundaries,
and real typed rejection for structurally sound but semantically invalid
values. Validate meaningful real Grants and supplied-only match outcomes
through the genuine functions. Test fixed error hygiene and sentinel
behavior. No private counter as sole oracle and no lowered production cap.

Frame-scan work is bounded by admitted bytes plus bounded slot counts.
The public Grants mapping/JSON admission and the typed factory's bounded
accounting, comparison and streaming add separate work. Aggregate declared
UTF-8 material is neither Unicode allocation size nor a universal heap,
RSS, throughput or latency measurement. A hash is content identity and
alone authenticates no policy. A later operator path must own a trusted
selection and prove protected file/epoch, current identity, eligibility,
dispatch/delivery checks and safe rollback. Full MVP and its qualification
gates remain open. DHA NONE.
