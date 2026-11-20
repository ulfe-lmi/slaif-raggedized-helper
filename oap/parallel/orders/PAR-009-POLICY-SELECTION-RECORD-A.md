# Parallel OAP work order — private policy selection record

Status: FINAL for the isolated lane after verified activation.
Provenance H full MVP, ARCH 13.3–13.4/A23/A24, E no policy selection
grammar, I exact read-boundary review 7b6a49611aca8c9923417a0beccc36f8f3b355f970c71f130fe3c692e03cbbd0.
Architecture SHA256: 4b41905396a3838269fd6cf372614cd23cb2c3b6a37be09f29ed752803c0983a
Governance SHA256: 24cec23235e3defc5f55bab4690298191d5a233d35dd9bf20b0afb4b3925f922
DHA: NONE.

## Goal and scope

Implement a small pure private parser for the exact selected-publication
record a later protected reader must observe. It will bind the immutable
view's expected wire length and SHA-256. The reader must later verify
the real bytes and stable namespace. This candidate has no I/O, epoch
enforcement, principal authentication, policy authority or writer.

Use CODING pane %33 and only the separately activated worktree/branch in
the manifest, sole base e9f24bae9ce47c1ceb3f51e9eff10e91574c7242.
This base supplies the read-only precedent and has no required CI
dependency for this pure candidate. Main is 5a7b41cc512cf883b5b2cb92d87554b4d24e685b.
PR #11 remains canonical and active. No remote push, new PR, release,
or canonical change. The wire decoder is a separate isolated lane.

## Exact v1 grammar

One versioned canonical ASCII JSON object, 1–512 bytes inclusive,
no padding, BOM or trailing LF, with exact keys and exact JSON value types.

- `generation` is an integer 1 through 2^63−1, excluding bool.
- `kind` is the exact string `slaif-current-policy-selection-v1`.
- `schema` is integer 1, excluding bool.
- `wire_bytes` is an integer 42 through 67108864 inclusive, excluding bool.
- `wire_sha256` is a string of exactly 64 lowercase ASCII hex digits.

Require exact byte equality with `json.dumps` using sorted keys,
separators comma and colon, and ensure_ascii=True, then ASCII encoding.
Validate type/size before decoding and verify exact field constraints
before round-trip emission. Duplicate keys, alternate spellings,
noncanonical whitespace, and other malformed input fail closed.
A generation number is part of publication identity under the future
trusted writer protocol; it supplies no anti-rollback certificate.

In `src/slaif_raggedized_helper/policy_selection.py`, implement
`parse_policy_selection(data: bytes) -> PolicySelection`, returning
a frozen slotted nominal record exposing `selection_bytes`,
`generation`, `wire_bytes`, and `wire_sha256`. Keep the report's
selected-publication identity distinct from wire and semantic IDs.
Use one fixed input-free ordinary `PolicySelectionError(ValueError)`
without retaining own caught error cause/context. Preserve non-Exception
interruption identity. Exact bytes only, with no optional keys, encoder,
semantic policy admission, alternative public API or file helpers.

## Acceptance and verification

1. Read the exact order, source index and narrow data pointer precedent.
   Confirm lane/control receipt and exact base. Use no prior/canonical FIFO.
2. Implement the grammar with existing conventions. Keep adversarial
   parsing fully bounded by the 512-byte cap. Use genuine parsing,
   a real canonical round trip and direct refusal checks.
3. Add `tests/unit/test_policy_selection.py`, default collected. Cover a
   literal independent canonical example, both wire length and generation
   limits, the 512-byte outer cap, exact bytes, frozen record, type/bool/schema/kind,
   hash case/length/alphabet, non-ASCII, duplicate/extra/missing keys,
   and alternate encoding/whitespace/trailing data. Include an ordinary
   error hygiene proof and portable exact module origin derived from the
   resolved test path. Short bounded pytest case IDs.
4. Existing canonical venv, explicit candidate src origin, one focused
   Ruff check and one normal selected pytest module invocation. Bounds
   CPU 30s, AS 1 GiB, wall 60s with 5s kill and fresh private basetemp.
   Retain full stdout/stderr and actual exits in the lane directory.
   A changed-byte retry for a concrete failed assertion is allowed once
   within those bounds. Preserve outcomes and stop on environment failure.
5. Commit the two new Python files and exact original order at
   `oap/parallel/orders/PAR-009-POLICY-SELECTION-RECORD-A.md`.
   Use one implementation checkpoint with the existing helper and stop
   for FIX or REPORT. No product docs beyond the preserved exact order.
   After REPORT, one local report-only SELF commit, exact topology and
   one original helper response. No branch manipulation after checkpoint.

## Protected resources

Existing client/profile/auth. Synthetic bytes only. No service, real
policy, model, corpus, credentials, policy-root inspection, installation
or hardware execution. No new agents. Keep scope compact. Evidence is a
candidate grammar check and does not qualify the protected reader,
current authorization, production or MVP.
