# Supplied-policy wire — API and evidence (PAR-009-SUPPLIED-POLICY-WIRE-A)

Local candidate only; implementation checkpoint requested, strategic review
pending. This component is not current application authority, not
integration, and not release evidence. DHA NONE. Contract:
`docs/parallel/supplied-policy-wire-v1.md` (exact strategic bytes, SHA256
`b737e5e33ff2ce753ea8a9c3e68eba2a250b8f56d2004e57c1b52c5478aa3158`).
Typed base: `supplied_policy.py` at
`7e59a94b98ee9b58af53bd4f350b992dbb0b91c547fd428b31b43b7009927195`
(implementation 191139254f327dd9d987f60db4102f2916e55611) and
`provenance_records.py` at
`88d3edfcfbfd7cb44a7d2a3fbd84d6fd01525a11e5c07a4416a6a316a57178a9`.

## 1. Public API (`src/slaif_raggedized_helper/supplied_policy_wire.py`)

* `admit_policy_bytes(data: bytes) -> SuppliedPolicy` — closed pure
  admission of the exact framed payload of the typed component. Accepts
  only exact `bytes` (bytearray/memoryview/str refused) of length
  42..67108864 inclusive; type and length precede field work. The closed
  wire is the typed component's exact framed payload: 30-byte literal
  prefix, U32(1) top-level schema, U32 principal count, per principal
  S(principal_id), U32(32)+32 verifier bytes, U32 operation count (1..3) +
  S(each operation), U32(1) Grants schema, then for corpora/versions/labels
  in that order U32 count + S(each value); U32 document count, per document
  S(document_id), U32 pair count + S(revision_id), S(scope digest).
  Monotone offset, bounds-first: every length frame is checked against the
  per-string 1048576 UTF-8 bound AND the safe field-specific byte maximum
  (principal ID 128, operation 12, document ID 1024, revision 71, scope
  digest 64) AND the remaining data before any slice or decode; strict
  UTF-8; verifier length frame exactly 32 before its body; counts
  (principals <=256, documents <=20000, operations 1..3, Grants vectors
  <=128, pairs <=64 per document, cumulative <=65536) checked before their
  traversals; admitted empty shapes; exact EOF required.
* Actual M accounting: every verifier and every string occurrence is
  charged to M (<=67108864, checked per contribution before
  construction). Actual canonical C = M + H (H = 42 + 4S + 24P + 4D,
  S = P+O+T+D+2G) is checked <=67108864 after exact EOF for this exact
  grammar; the sufficient-but-not-necessary 66021078 material threshold is
  NOT imposed and no byte estimate replaces the actual limits.
* Reconstructs real `PrincipalSpec` and `DocumentRule` records without
  sorting, normalizing, coercing or treating malformed values as
  admitted. Each Grants record is reconstructed through the real public
  controlled-mapping admission `provenance_records.admit_record("Grants",
  {schema_version, corpora, versions, labels})` with exactly four keys
  (conservative second public Grants admission; intentional and finite).
  The real typed `admit_policy` then performs all domain checks, its
  authoritative Grants snapshots and the framed identity hash; the
  returned immutable admitted object is the decoder's result. The decoder
  never replaces the typed API; no second hash of the original input is
  required or computed.
* `PolicyWireError(ValueError)` — all ordinary public failures raise this
  one type with one fixed input-free message `invalid supplied policy
  wire`. The sanitized error is raised AFTER the caught handlers, so the
  public error's `__cause__` AND `__context__` are both None (verified for
  a structural refusal, a strict-UTF-8 `UnicodeError` refusal and a real
  typed-factory refusal). Non-Exception BaseException identity propagates
  unchanged at the Grants-admission and typed-factory seams (sentinel
  tests). No logs, no partial outputs, no I/O, no currentness checks, no
  real credential provisioning.

## 2. Finite work, costs and joint bounds

Units as in the typed component: P principals, D documents, G total pairs,
O operation strings, T Grants strings, S = P+O+T+D+2G string frames,
M = summed per-occurrence UTF-8 bytes plus 32P verifier bytes, H =
42+4S+24P+4D, C = M+H.

* Structural scan: one O(N) pass over the admitted wire bytes (N = 42..
  67108864) with O(1) bounds-first reads; declared lengths are checked
  before any slice/decode, so no unbounded allocation. Per-string UTF-8
  work is one bounded decode plus one bounded encode for the M charge.
* Grants seam: <=256 real public `admit_record` calls (mapping walk,
  character sum, one `ensure_ascii=False` JSON encode with the separate
  1MiB serialized refusal) — separate bounded work, encoded-size
  accounting, not a heap/RSS/latency theorem.
* Typed factory: rechecks every local/global count, the per-string and
  actual M/C limits, duplicate principal/verifier sets, order
  comparisons, re-snapshots <=256 Grants, and streams the framed identity
  (chunked <=4096-byte updates) with the cumulative 67108864 refusal.
* Retained state after success is the factory's own admitted object
  (O(P+D+G+T) cells); the decoder retains no partial view on failure.
* A hash is content identity; alone it authenticates no policy.

## 3. Verification evidence (this lane, finite pure-unit only)

Environment: existing canonical venv only
(`/home/janezp/codex-work/slaif-raggedized-helper/.venv`), Python 3.14.4,
ruff 0.17.4, pytest 8.4.2; `PYTHONPATH` pointed at THIS worktree `src`;
test-startup (import-time, fail-closed) asserts `supplied_policy_wire`,
`supplied_policy` and `provenance_records` module origins are inside this
worktree `src` derived from the resolved physical test-file location. No
installation, download, venv creation, network, credentials, model or GPU.
Bounds: `timeout --kill-after=5s 180s /usr/bin/time -v prlimit
--cpu=120 --as=1073741824`, full logs retained in the lane.

* One focused Ruff cycle on the two new Python files: `ruff format`
  (2 files reformatted) + `ruff check` (exit 0); focused `format --check`
  + `check` on the corrected test file exit 0 in both FIX rounds.
* Bounded pure-unit executions (normal default entries for the two
  supplied-policy test modules, inherited typed + new wire); every attempt
  is an actual changed-byte process, no retry of unchanged failed bytes:
  * run 1: `pytest-run-1.log` — exit 1, 217 passed / 1 failed
    (test-fixture bug: raw pair builder concatenated str to bytes);
    user CPU 8.05s, wall 8.76s, max RSS 403292 kB.
  * run 2 (checkpoint f5fcf7a bytes): `pytest-run-2.log` — exit 0, 218
    passed (124 inherited typed + 94 wire), 0 failed/skipped; user CPU
    8.19s, wall 8.87s, max RSS 419516 kB.
  * Root FIX at f5fcf7a (narrow test-boundary findings; product decoder
    bytes preserved exact at
    `d18a93996baa36ea88b538f439994e9d658eb1fe4de32fb6daac15068ec4805a`):
    (1) the principal-count-cap witness needed a >=42-byte input proving
    refusal before the first framed text traversal; (2) the cumulative
    pair boundary needed fixed-width sorted document IDs, a genuine
    admitted 65536-pair boundary and refusal of the 65537th pair proven
    by a test-local observer delegating to the genuine framed read.
  * run 3 (first correction bytes): `pytest-run-3.log` — exit 1, 218
    passed / 1 failed (oracle omitted the two real principal reads: the
    128-cap principal ID frame and the 12-cap operation frame; observed
    132099); user CPU 9.03s, wall 9.88s, max RSS 450316 kB. Failure
    preserved; run 3 process was an actual changed-byte correction.
  * run 4 (final bytes): `pytest-run-4.log` — exit 0, 219 passed
    (124 inherited typed + 95 wire), 0 failed/skipped; user CPU 8.92s,
    wall 9.73s, max RSS 450248 kB (observed, not a theorem).
* Source identities at base `191139254f327dd9d987f60db4102f2916e55611`:
  contract `b737e5e3...`, typed module
  `7e59a94b98ee9b58af53bd4f350b992dbb0b91c547fd428b31b43b7009927195`,
  provenance `88d3edfcfbfd7cb44a7d2a3fbd84d6fd01525a11e5c07a4416a6a316a57178a9`
  (all verified equal to the lane index before implementation). Final
  implementation file hashes: `supplied_policy_wire.py`
  `d18a93996baa36ea88b538f439994e9d658eb1fe4de32fb6daac15068ec4805a`
  (preserved exact through both FIX rounds),
  `test_supplied_policy_wire.py`
  `00ce55eabe893386ad48449231964d7ea12cb34fb22336705c859c5952c3eb59`.

Witnesses in the wire suite (real typed objects, independent test-side
golden framings, no private counters):
* exact 42-byte empty policy literal; direct field equality; independent
  golden identity plus one-byte value-change witness; two independent
  test-side framings agree; Unicode/control/empty shapes (Unicode doc ID
  and Grants values, empty Grants string, ASCII-control Grants value,
  withdrawn document, zero documents).
* Actual 20000-declaration admission: M/H/C = 2840039/320074/3160113 and
  zero-principal variant 2840000/320042/3160042, transport wire length ==
  canonical C, golden identity.
* Actual M/C boundary: above-sufficient material admitted
  (M 66492352 > 66021078, C 66936298 <= 67108864) vs canonical-cap
  crossing refused (C 67341290 > 67108864 while M 66897344 <= cap).
* Size/count/remaining/EOF: type gate (str/bytearray/memoryview), 41B and
  64MiB/64MiB+1 length boundaries, 18 truncation cuts, trailing 1/4/17
  bytes, principal 257 at 43 bytes refused before the first framed text
  (sentinel witness) / document 20001 / operation 0+4 / Grants vector
  129 / pair 65 count refusals; cumulative pair boundary: genuine
  admitted 1024-doc x 64-pair view (65536 pairs, delivered rules/counts
  and golden identity) then the 65537th pair refused with the observer
  recording exactly 2 principal frames (128-cap ID, 12-cap operation) +
  1025 document IDs (1024-cap) + 2 x 65536 pair strings (71/64-cap) and
  no traversal of the 65537th pair (132099 total); field byte caps
  (principal 129, operation 13, document 1025, revision 72, digest 65,
  Grants value 1MiB+1) with the 128B principal ID and 1024B document ID
  boundaries admitted, verifier frames 31/33/32-truncated, six strict
  invalid-UTF-8 sequences, both schema locations (top-level and encoded
  Grants, zero and two), three prefix mutations.
* Structurally valid but typed-refused: charset, leading punctuation,
  duplicate/unsorted principal IDs, duplicate verifiers, unsorted/vocabulary
  operations, answer closure, unsorted Grants that the REAL public
  `admit_record` admits (drives both the typed refusal and the wire
  refusal), revision/digest shape, duplicate/unsorted documents,
  unsorted/duplicate pairs.
* Real outputs: genuine returned `SuppliedPolicy` type and identity parity
  with a direct `admit_policy` call; genuine fullscan
  `match_supplied` outcomes (first/middle principals, unknown credential,
  insufficient operations) with `SUPPLIED_POLICY_MATCH_ONLY`; real
  `reader_allows` / `Restrictions` intersections on the returned real
  Grants (corpus/version/label matches and denials, None grants, None
  version, narrowing restrictions).
* Error ABI: fixed input-free message, no marker leakage in
  str/repr/args, `__cause__`/`__context__` None for structural, caught
  `UnicodeError` and caught typed-factory failures; BaseException sentinel
  identity at the Grants-admission and typed-factory seams.
* Transport size vs canonical semantics: for this exact grammar the wire
  bytes ARE the canonical payload (len(wire) == C asserted), documented as
  distinct from any heap/RSS/latency claim.

## 4. Limits, counterargument and later mandatory composition

* Strongest counterargument: the wire binds an input format to the
  identity grammar and a pure decoder could substitute supplied
  declarations for protected current authority. This component ends
  strictly at the real typed admitted object; `SUPPLIED_POLICY_MATCH_ONLY`
  grants nothing about currentness, and trust in any later loader rests on
  content-vs-trusted-selection verification, never on the hash alone.
* No I/O, env, clock, network, config, parser, cache, current-pointer, pin,
  model, database or caller-callback behavior; no credential generation or
  acquisition; synthetic fixed byte fixtures only.
* The 20000-declaration and 67MB witnesses are finite pure-unit evidence,
  never source/snapshot capacity, throughput or latency evidence; observed
  CPU/RSS values are measurements, not theorems.
* Later MANDATORY composition (not implemented here): protected current
  selection/epoch/owner/mode/raw-byte loader; real application principal
  verification; eligibility of captured membership; first admitting real
  `Scope` from captured `Entry.scope_bytes`, then joining on
  `Scope.document_id` and exact `(Entry.revision_id,
  Entry.source_scope_sha256)` (Entry has NO document_id); checks at
  encode/scoring/source/grade/dispatch/delivery; revocation-safe cache
  keys; real `Restrictions` intersection at actual readers; fixed real CPU
  encoder path; private operator composition; approved data/rights and
  representative held-out baseline.
* Real baseline remains NOT_RUN; hardware/rights/license/security/visual/
  ICA/full-MVP gates remain OPEN. Canonical objective 009 and PR #11
  remain owned by the original coding/control path; this lane publishes no
  remote branch, PR or canonical change.

DHA NONE.
