# Supplied-policy primitives — API and evidence (PAR-009-SUPPLIED-POLICY-A)

Local candidate only; Root checkpoint review pending. This component is not
current application authority, not integration, and not release evidence.
DHA NONE. Contract: `docs/parallel/supplied-policy-primitives-v1.md`
(exact Root bytes, SHA256
`9bcfe68dd5a80c2d07f19e9a0a2f97a73da4521de5c9bd9fc71d87c4ed247af7`).
Supersedes the 1593aa6 checkpoint bytes, which remain preserved by the lane
helper ref `refs/oap/implementation-checkpoints/supplied-policy/1593aa6...`.

## 1. Public API (`src/slaif_raggedized_helper/supplied_policy.py`)

* `PrincipalSpec(principal_id, verifier, operations, grants)` — frozen,
  slotted, exact-nominal declaration DTO. `principal_id` exact str matching
  `[A-Za-z0-9][A-Za-z0-9._:-]{0,127}`; `verifier` exact bytes length 32;
  `operations` exact nonempty tuple (<=3) strictly increasing from
  `answer`/`search`/`sources:read` (answer implies `sources:read`);
  `grants` exact existing `provenance_records.Grants`. Nonrevealing repr.
  Declaration DTO only, not admitted authority.
* `DocumentRule(document_id, admitted)` — frozen, slotted, exact-nominal DTO.
  `document_id` exact str, 1..256 codepoints, UTF8-encodable without
  surrogates; `admitted` exact tuple 0..64 pairs, each an exact 2-tuple
  `(revision_id, source_scope_sha256)` with `sha256:[0-9a-f]{64}` and
  `[0-9a-f]{64}`, strictly lexicographically increasing. Empty `admitted`
  means withdrawn; absent document means denied.
* `admit_policy(principals, documents) -> SuppliedPolicy` — closed exact
  admission. Inputs exact tuples; 0..256 principals strictly increasing by
  principal_id (duplicate id or duplicate verifier bytes refuse the whole
  view); 0..20000 documents strictly increasing; total admitted pairs
  <=65536. Closed local checks apply cheap O(1) codepoint pre-bounds before
  order/encoding and check the per-string 1MiB UTF8 cap and the global
  material M <= 67108864 while accumulating each contribution (no whole
  principal deferred to the end). Every string's UTF8 length is measured in
  <=1024-codepoint chunks (each encoded chunk <=4096 bytes). Actual
  `C = M + H <= 67108864` (H = 42 + 4S + 24P + 4D; S = P+O+T+D+2G) is
  enforced; the sufficient-but-not-necessary 66021078 material threshold is
  NOT imposed. Every Grants is re-admitted through public
  `provenance_records.admit_record("Grants", controlled_mapping)` (exactly
  schema_version/corpora/versions/labels) after the local checks. Identity is
  the streamed, domain-separated, length-framed SHA256 per contract section 3:
  each text value is framed as U32(bounded UTF8 length) followed by genuine
  bounded encoded chunks (<=1024 codepoints / <=4096 bytes); no whole-value
  encoding and no complete canonical payload in product code.
* `match_supplied(policy, credential, required_operations) -> SuppliedMatch`
  — requires the exact admitted nominal `SuppliedPolicy` plus internal
  admission marker. Credential exact bytes 43..256 over the 66-symbol
  RFC3986-unreserved ASCII alphabet; `SHA256(credential)` computed once;
  genuine `hmac.compare_digest` of the digest against EVERY principal
  verifier with no early success; after the full scan exactly one match AND
  `required_operations` (exact sorted unique nonempty tuple, <=3, same
  vocabulary) must be a subset of the principal's allowed operations.
  The matched real Grants is re-admitted through the same public
  controlled-mapping admission before the result is built.
* `PolicyError(ValueError)` — all ordinary public failures raise this one
  type with one fixed input-free message `invalid supplied policy`. The
  sanitized error is raised AFTER the caught handlers, so the public error's
  `__cause__` AND `__context__` are both None (verified by regression for a
  controlled ordinary failure and a real surrogate `UnicodeEncodeError` at
  the admission boundary, and a controlled failure at the match boundary).
  No supplied identifiers/credential/verifier/grants in the message or repr.
  This is not a zeroization, traceback-locals or caught-payload-object claim:
  the caught object can still exist in caller-owned frames/tracebacks.
  Non-Exception BaseException identity propagates unchanged at
  digest/comparison/admission boundaries.
* `SuppliedPolicy` — factory-only FROZEN record (frozen slotted dataclass
  without a public init): immutable `principals` (admitted principal
  records), `documents` (admitted document records), `policy_id`
  (`sha256:` + 64 lowercase hex) and an internal admission marker. Public
  construction raises `PolicyError`; ordinary assignment or deletion of any
  field (including the marker) raises `FrozenInstanceError`; an
  uninitialized instance is refused by matching. Internal construction uses
  private object assignment only.
* `SuppliedMatch` — factory-only FROZEN record; exposes exactly
  `principal_id`, `grants` (fresh re-admitted real Grants snapshot),
  `operations` (the principal's FULL allowed tuple), `policy_id`, and
  `authorization_status = "SUPPLIED_POLICY_MATCH_ONLY"`. No verifier,
  credential, or document rules. Assignment/deletion refused as above; its
  constructor cannot confer authority.

## 2. Finite work, costs and joint bounds

Units: P = principals (0..256), D = documents (0..20000), G = total pairs
(0..65536), O = operation strings (0..768), T = Grants strings (0..98304),
S = P+O+T+D+2G string frames, M = summed per-occurrence UTF8 bytes of every
input string plus 32*P verifier bytes, H = 42+4S+24P+4D, C = M+H.

* Local closed checks: one O(P+D+G+T) traversal; O(1) codepoint pre-bound
  before encoding; verifier duplicate set O(P); per-string UTF8 chunk
  accounting with early cap inside the chunk loop. For each Grants value,
  in traversal order, its genuine UTF8 count is charged to M and the
  67108864 aggregate is checked BEFORE the adjacent (not sorting) order
  comparison for that value: no value after an aggregate refusal is counted
  or compared and there is no separate uncharged order pre-traversal; other
  vectors keep adjacent comparisons bounded by their per-string pre-bound.
* Public Grants re-admission per principal: `admit_record` mapping walk
  O(chars/nodes), then one `ensure_ascii=False` JSON encode. The encoded
  JSON can transiently reach up to 6*admitted character count + bounded
  punctuation before its separate 1MiB serialized refusal (ASCII controls
  are escaped even with `ensure_ascii=False`). This is encoded-size
  accounting, not a Python heap/RSS/latency theorem.
* Count + stream passes are bounded and separate: the length count pass and
  the stream pass each encode <=1024-codepoint chunks (<=4096 bytes); the
  framed identity streams chunk by chunk. Hashing never re-charges material
  to M; the stream refuses if cumulative framed bytes exceed 67108864.
  Matching: one SHA256(credential) plus P `compare_digest` calls (full scan)
  plus one public Grants re-admission.
* Retained state after success: O(P+D+G+T) record/reference cells; no
  zero-copy or physical RSS promise; no retained plaintext credential.

## 3. Verification evidence (this lane, finite pure-unit only)

Environment: existing canonical venv only (`/home/janezp/codex-work/
slaif-raggedized-helper/.venv`), Python 3.14.4, ruff 0.17.4; `PYTHONPATH`
pointed at THIS worktree `src`; test-startup asserts both module origins are
inside THIS worktree. No installation, download, venv creation, network,
credentials, model or GPU.

Round 1 (implementation 1593aa6, now superseded but preserved by the lane
checkpoint ref): 118 pure-unit cases, 3 pytest attempts under
`timeout --kill-after=5s 180s` + `prlimit --cpu=120 --as=1073741824`
(`/usr/bin/time -v`): attempts 1 and 2 failed on test-fixture bugs (20k
witness doc-ID width; sentinel patch ordering; 129-item Grants through the
public constructor; one hardcoded verifier), attempt 3 exit 0 (118 passed,
user CPU 3.50s, wall 3.69s, max RSS 195520 kB). DISCLOSURE: those three
attempts left no raw log files in the lane; their proof is the CLI transcript
only, not reconstructed logs.

Root FIX review of 1593aa6 (findings F1-F4) and round-2 fixes:
* F1: `SuppliedPolicy`/`SuppliedMatch` are now frozen slotted records
  (assignment AND deletion refused on all exposed fields and marker);
  regression added.
* F2: sanitized `PolicyError` raised after the caught handlers; public
  error `__context__ is None` (not merely suppressed) — regressions for
  controlled ordinary failure, real surrogate `UnicodeEncodeError`
  (admission) and controlled match-boundary failure.
* F3: framed identity streams genuine bounded encoded chunks (<=1024
  codepoints / <=4096 bytes) with the length frame from a bounded count;
  regression records actual hasher update lengths while delegating a real
  SHA256 over multi-chunk Unicode Grants, checks every update <=4096,
  an exact-4096 update, independent golden identity and total == canonical C.
* F4: O(1) codepoint pre-bound before order/encoding, early cap inside the
  UTF8 chunk loop, global M checked per contribution; regressions:
  over-cap string refused before any public Grants admission or identity
  hashing (guarded call recording), 900000-astral byte-cap refusal, and
  68 full-size grant strings refused during accumulation (per-string caps
  hold; M crosses the cap before the principal completes).

Round-2 pytest (own test file, same bounds; FULL logs retained in lane):
* fix attempt 1: `pytest-fix-1.log` — exit 1, 122 passed / 1 failed
  (hygiene `__context__` still linked to the internal marker because the
  raise happened inside the helper call from the handler; real cause found).
* fix attempt 2 (final bytes): `pytest-fix-2.log` — exit 0, 123 passed,
  0 failed/skipped; user CPU 4.20s, wall 4.42s, max RSS 195528 kB
  (observed, not a theorem). Case count 123 (static expansion of the final
  test bytes; 118 round-1 cases + 5 new F1-F4 regressions). No retry of
  unchanged failed bytes; each attempt changed source/test first.
* `ruff format` + `ruff check` on the two NEW Python files: exit 0
  (3 format cycles total across rounds; no other files touched).
* Static syntax (`py_compile`) on both new files: exit 0.

Root FIX review of 3889d730 (findings F5, F4-followup, F6) and round-3
fixes, plus the pre-checkpoint test-instrumentation clarification:
* F5: the module-origin assertion now derives its source directory from
  this test file's resolved physical location (parents[2] / src); the
  hard-coded machine/worktree path is gone; import-time fail-closed
  behavior kept.
* F4-followup: each Grants value, in traversal order, checks exact type and
  the O(1) codepoint pre-bound, charges its genuine bounded UTF8 count to M,
  checks the 67108864 aggregate, and only then performs the adjacent order
  comparison for that value; the separate uncharged string-order traversal
  is removed. A regression witnesses, with a TEST-LOCAL recorder that
  monkeypatches `_utf8_byte_length` to delegate to the real routine and
  filters its record to the genuine test Grants strings by object identity,
  that after the aggregate refusal no later value is ever counted: 65
  earlier principals spend M exactly to the cap, the 66th principal's base
  lands on it, its first 2000-byte value overflows the zero remaining
  allowance, and the record holds exactly the 65 filler lengths plus 2000
  (the 127 later values are never counted). No test hook remains in
  production.
* F6: the full-grant required-subset test now covers all six valid
  subsets, adding answer+search and search+sources:read; the explicit
  answer-only case is preserved.

Round-3 pytest (own test file, same bounds; FULL logs retained in lane):
* pre-correction run (seam version, its exact tested bytes):
  `pytest-fix-3.log` — exit 0, 124 passed; user CPU 4.42s, wall 4.63s,
  max RSS 227356 kB.
* final-bytes run: `pytest-fix-4.log` — exit 0, 124 passed, 0
  failed/skipped; user CPU 4.47s, wall 4.66s, max RSS 227400 kB (observed,
  not a theorem). Case count 124 (123 round-2 cases + 1 new F4-followup
  witness). One process after the actual byte change; no retry needed.
* One focused Ruff check (`format --check` + `check`) on the two lane
  Python files after the clarification byte change: exit 0.

Source identities at base `494a1908b3f0719c0eb78becdcbcb6c5c3ac0d74`:
contract/root review/ARCH13/provenance_records/pyproject/TESTING hashes per
`source-inputs.json` (verified equal before implementation). Final
round-2 implementation file hashes (preserved): `supplied_policy.py`
`fe08c7c17beecd2f52bbe5bf4e12b8e8a65499558a8d1bb574df85445622d27c`,
`test_supplied_policy.py`
`ecc4369dc1eb25325194440f1be2badf097eeb4f5a64e881129635ec6167a7ce`.
Round-3 implementation file hashes: `supplied_policy.py`
`7e59a94b98ee9b58af53bd4f350b992dbb0b91c547fd428b31b43b7009927195`,
`test_supplied_policy.py`
`fcda195ab96170524d5e7472055e994a3b23c3c7128d125dd4f456de69630f01`.

Witnesses included in the suite (real typed objects, no private counters):
20000-declaration admission (M/H/C = 2840039/320074/3160113) and
zero-principal variant (2840000/320042/3160042) with independent test-side
golden framing; above-sufficient material admitted (M 66487296 > 66021078,
C 66611242 <= cap); canonical-cap crossing (C 67103018 admitted vs
C 67131946 refused while M 67008000 <= cap); fullscan first/middle/last/
unknown with recorded real-comparator call count; BaseException identity at
digest/comparison/admission boundaries; public 1MiB Grants JSON refusal
beyond local M/C; real `reader_allows` empty-deny/all-label/corpus/version/
missing-version/Restrictions intersections; frozen-record refusals; the
test-local Grants byte-count recorder's no-later-work oracle (record holds
exactly the 66 charged values at the aggregate refusal).

## 4. Limits, counterargument and later mandatory composition

* Strongest counterargument: pure typed matching risks substituting supplied
  declarations for protected current authority. This component ends strictly
  at `SUPPLIED_POLICY_MATCH_ONLY`; it grants nothing about currentness.
* No I/O, env, clock, network, config, parser, cache, current-pointer, pin,
  model, database or caller-callback behavior; no credential generation or
  acquisition; synthetic fixed byte fixtures only (alphabet capacity is not
  an entropy claim).
* The per-string 1MiB UTF8 bound is enforced (O(1) pre-bound plus early
  chunk-cap), but for Grants values it is subsumed in practice by the public
  1MiB serialized-JSON refusal; the suite documents the subsumption rather
  than claiming a separately observable crossing for that one input class.
* Frozen-record immutability is API discipline against ordinary
  attribute/delattr access; the contract's explicit exclusions (arbitrary
  trusted introspection, `object.__setattr__` used by untrusted code,
  monkeypatching, memory inspection) remain out of scope.
* Later MANDATORY composition (not implemented here): protected current
  selection/epoch/owner/mode/raw-byte loader; real application principal
  verification; eligibility of captured membership; first admitting real
  `Scope` from captured `Entry.scope_bytes`, then joining on
  `Scope.document_id` and exact `(Entry.revision_id,
  Entry.source_scope_sha256)` (Entry has NO document_id); checks at
  encode/scoring/source/grade/dispatch/delivery; revocation-safe cache keys;
  real `Restrictions` intersection at actual readers; fixed real CPU encoder
  path; private operator composition; approved data/rights and representative
  held-out baseline.
* Real baseline remains NOT_RUN; hardware/rights/license/security/visual/
  ICA/full-MVP gates remain OPEN. 20000 declarations here is finite pure-unit
  evidence, never 20k source qualification. Current raw membership caps
  (128 entries / 4096 rows / 8MiB) are unchanged.
