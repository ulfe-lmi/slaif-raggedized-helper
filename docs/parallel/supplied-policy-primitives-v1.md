# Supplied policy primitives v1 — FINAL private component contract

Root authorship; ordinary D0 choices. Provenance H: activated full-MVP development;
A: ARCHITECTURE 13.1–13.4/A24; E: genuine protected current-principal/current-policy
provider remains absent at the reviewed boundary; I: independent design review
AUDIT-009-POLICY-PRIMITIVES-A, final report SHA256
507b5a6b9dbe781b9038282c3c37aa6ecee8c84522f8b735fadadb7ceba3483f.
This FINAL contract supersedes the inert candidate and Root design choices v1/v2
for this component only. An activated order separately grants implementation and
finite pure-unit execution. Neither this contract nor a supplied match grants
current application authorization, credential provisioning, deployment or release.
DHA NONE. Preserve existing provenance APIs and identities unchanged.

## 1. API, nominal records and trust boundary

New module `slaif_raggedized_helper.supplied_policy`. Public declarations:

* `PrincipalSpec(principal_id, verifier, operations, grants)`
* `DocumentRule(document_id, admitted)`
* `admit_policy(principals, documents) -> SuppliedPolicy`
* `match_supplied(policy, credential, required_operations) -> SuppliedMatch`
* `PolicyError(ValueError)`

All new records are exact nominal, frozen, slotted types with nonrevealing repr;
no subclass/coercion admission. PrincipalSpec and DocumentRule are declaration
DTOs, not admitted authority. SuppliedPolicy is factory-only admitted state, with
immutable `principals`, `documents`, `policy_id`; ordinary public construction or
an uninitialized object must not bypass admission. Match requires this exact
admitted nominal type and internal admission marker. No promise against arbitrary
trusted Python introspection, object.__setattr__, module monkeypatching or memory
inspection. An admission seal is ordinary API discipline, not authenticated
provenance or an OS security boundary.

SuppliedMatch exposes exactly principal_id, grants (a newly re-admitted exact real
provenance Grants snapshot), operations (the principal's FULL allowed tuple),
policy_id, authorization_status=`SUPPLIED_POLICY_MATCH_ONLY`. No verifier,
credential or document rules in the match result or its repr. Its constructor
must not confer stronger authority. SuppliedPolicy declarations may be inspected
by later trusted provider code; they are not secrets or proof of currentness.
The exact real Grants record is from provenance_records, not a local replacement.

This component performs no filesystem/env/clock/network/HTTP/config/parser/cache/
current-pointer/pin/model/database/caller-callback operation. Hashing an explicitly
supplied credential is allowed. No generation or acquisition of actual credentials.
No edits to existing readers, source capacity, restrictions or Plan/report identity.

## 2. Closed declaration admission

Outer inputs exact tuples. Principals 0..256, strictly increasing by principal_id.
Each item exact PrincipalSpec, exactly these field domains:

* principal_id exact str matching ASCII `[A-Za-z0-9][A-Za-z0-9._:-]{0,127}`.
* verifier exact bytes length 32, representing SHA256 of an exact credential.
* operations exact nonempty tuple, at most 3 exact strings, strictly increasing
  in Python codepoint order from `answer`, `search`, `sources:read`.
  A principal allowing answer MUST also allow sources:read.
* grants exact existing Grants; schema_version exact int 1 (bool refused).
  corpora/versions/labels exact tuples, each 0..128 exact strings, each strictly
  increasing by Python Unicode codepoint lexicographic order. Empty strings and
  empty tuples remain admissible when genuine public Grants admission permits.

Duplicate principal IDs or exact verifier bytes refuse the WHOLE view. No sorting,
normalization, case folding, coercion or partial admission. Sorted unique Grants
is an intentional NEW filter; existing Grants can be valid without that ordering.
Show a genuine existing API-valid unsorted Grants refused here without changing
provenance admission or reader_allows. Do not impose ASCII128/256 on Grants values.

Documents exact tuple 0..20000; items exact DocumentRule, strictly increasing by
exact document_id. document_id exact Unicode str, 1..256 codepoints, UTF8 encodable
without surrogates, no normalization. admitted exact tuple 0..64 pairs per document,
total pairs <=65536. Each pair exact 2-tuple of exact strings: revision_id matches
`sha256:[0-9a-f]{64}` (71 characters); source_scope_sha256 matches `[0-9a-f]{64}`.
Pairs strictly lexicographically increasing by the two strings. Empty admitted
means withdrawn; absent document means denied. Multiple history pairs may be
explicitly admitted. No approval/rights/currentness inferred from declarations.

Exact outer/local record, tuple/scalar types and local counts must be checked
before deeper traversal. Reject bypassed malformed Grants fields, subclasses,
bools, missing data, invalid Unicode and all order/duplicate violations generically.
Check UTF8 lengths with chunks <=1024 codepoints, each encoded chunk <=4096 bytes;
no full-string UTF8 allocation solely to discover length. Per input string UTF8
bytes <=1048576, plus any smaller field-specific bound. Global material M <=67108864,
counting EACH occurrence of every input string UTF8 bytes and every verifier byte:
principal IDs, operations, all Grants strings, document IDs and both pair strings.
Repeated identical strings count repeatedly. Exclude schema constants, integer
framing and field names from M. Track total pair count during traversal.

After exact local checking and counters, snapshot every Grants through public
`provenance_records.admit_record("Grants", controlled_mapping)` with exactly four
keys schema_version/corpora/versions/labels. Do not recursively model_dump arbitrary
unchecked records and do not use private _snapshot as a substitute for the public
bounded admission. Existing public per-record limits apply in addition to new M/C
limits, including 1MiB serialized JSON and existing node/depth/character limits.
Preserve accepted field values. Whole success returns only newly owned immutable
declaration tuples/records and real Grants snapshots; failure returns no view.
Borrowed immutable strings may be shared; no zero-copy or physical RSS promise.

## 3. Exact semantic identity, streamed and length-framed

policy_id is `sha256:` plus lowercase hex SHA256 of this EXACT grammar. This new
identity changes no existing identity and is not an input wire format or JSON.
U32 = unsigned 4-byte big-endian; all lengths/counts fit. S(text) = U32(exact UTF8
byte length), then exact UTF8 bytes; B(verifier) = U32(32), then exact 32 bytes.

Sequence:

1. Literal bytes `b"slaif-supplied-policy-view-v1\n"` (30 bytes), U32(1 schema),
   U32(principal count).
2. For each principal in admitted order: S(principal_id), B(verifier),
   U32(operation count), S(each operation), U32(Grants.schema_version=1);
   then for corpora, versions, labels IN THAT ORDER: U32(tuple count), S(each value).
3. U32(document count); for each document in admitted order: S(document_id),
   U32(admitted pair count), and S(revision_id), S(scope digest) for each pair.

No sorting, omitted empties, field-name strings, normalization or JSON escaping.
Never materialize a complete canonical payload in product code. Count canonical
bytes C BEFORE each hash update; refuse before exceeding 67108864. Only finish
digest/return after whole admission succeeds. A partial digest is not a result.
Bounded UTF8 count pass followed by bounded streaming pass is allowed; account for
both passes separately from existing Grants serialization and comparison work.
Hashing must not charge the same material twice to M. No retained plaintext secret.

Let P=principals, D=documents, G=total pairs, O=all operation strings, T=all Grants
strings across all three tuples/all principals. S=P+O+T+D+2G counts string frames.
Exact framing overhead H=42+4S+24P+4D=42+28P+4O+4T+8D+8G; C=M+H.
42 is prefix+schema+principalcount+documentcount. 24P consists of B-frame,
operation-count, Grants schema and three Grants tuple counts; S(id) is ALREADY
in 4S, not in 24P. 4D is each document's pair count. At independent count caps
P256,D20000,G65536,O768,T98304, H<=1087786.

M<=66021078 is SUFFICIENT for C<=67108864 at every allowed shape, NOT necessary.
DO NOT impose that smaller blanket material cap. Enforce ACTUAL M<=67108864 AND
ACTUAL C<=67108864. Values above the sufficient threshold can fit smaller framing;
other material-admissible shapes intentionally fail canonical capacity. Test both
semantics through actual typed inputs at meaningful boundary values.

Static witness: principal_id="p", verifier32B, operations=("search",), Grants
tuples empty; 20000 ordered seven-ASCII-character document IDs and one 71+64-byte
pair each. P1,D20000,G20000,O1,T0 => M2840039,S60002,H320074,C3160113.
Zero-principal variant M2840000,H320042,C3160042. Execute a genuine 20000-declaration
admission in the bounded pure-unit suite; never call it source/snapshot capacity.
Current raw membership remains128 entries/4096 rows/8MiB; do not raise caps.

## 4. Supplied credential matching

credential exact bytes length43..256, only ASCII RFC3986-unreserved alphabet:
letters, digits, `.`, `_`, `~`, `-` (66 symbols). No decoding/transformation.
43*log2(66)>=256 shows possible alphabet capacity, NOT actual entropy. Repeated
bytes are not entropy proof. Generation/provisioning >=256-bit randomness is a
later operator/human trust action; do not generate or configure real credentials.
Tests may use explicitly synthetic fixed byte fixtures hashed by genuine SHA256.

required_operations exact sorted unique nonempty tuple of at most3 exact strings
from the same vocabulary. Requested ("answer",) is a valid subset request: answer
closure is enforced on PRINCIPAL declarations, not by adding requested operations.
Compute SHA256 on the exact admitted credential ONCE. Call actual
`hmac.compare_digest` on digest bytes versus EVERY principal verifier, no early
success. After full scan require exactly one match AND required ops subset;
otherwise one generic refusal. Empty policy refuses. No prefix/substring match,
gateway-token substitution or claimed whole-Python constant-time theorem.
Snapshot the matched real Grants through the same public controlled-mapping
admission before returning a SuppliedMatch with the FULL allowed ops tuple.

Tests must use genuine comparison outcomes (a wrapper recording calls may invoke
the real comparator, but no constant-success fake). Exercise first/middle/last/
unknown matches, all required subsets, malformed inputs and exactly-one behavior.
Admission already rejects duplicate verifiers. Controlled BaseException sentinels
at real digest/comparison/admission boundaries propagate by identity, not swallowed.

## 5. Failure, finite work and integration limits

All ordinary failures at public calls return no partial result and raise exact
PolicyError with one fixed input-free message, e.g. `invalid supplied policy`.
No caught payload exception retained as visible cause/context: raise the sanitized
error after leaving handlers as needed; from None alone is not a context-erasure
claim. Exception repr/args must not leak supplied identifiers, credential, verifier
or grants. Non-Exception BaseException identity propagates unchanged. No stdout/log
payload disclosure. Repr/error hygiene does not promise zeroization or eliminate
caller-owned data/traceback locals or arbitrary trusted caller logging.

Count bounds are finite: new records/reference cells O(P+D+G+T); T<=98304. Adjacent
order checking, not sorting, bounds comparisons in terms of admitted characters/
bytes/pairs. State traversal, count+stream hashing, duplicate verifier set and real
Grants re-admission costs honestly, including refusals. Public admit_record's
controlled mapping checks character sum before JSON, but ensure_ascii=False STILL
escapes ASCII controls: encoded JSON can transiently reach up to6*admitted character
count+bounded punctuation before its separate1MiB serialized refusal. UTF8 checks,
JSON Unicode string/encoding, mappings/models/snapshots add work/copies. This is
encoded-size accounting, not a Python heap/RSS/latency bound. Positive Grants
remain subject to genuine public admission. No zero-allocation/16MiB universal
heap/3M-node/80M-sort claims. The framed POLICY identity itself has no JSON escaping.

Use genuine reader_allows in tests for empty-deny, all-label, corpus/version and
Restrictions intersections, including missing Scope.version. Matching does not
take Restrictions or perform scope authorization. Later provider MUST intersect
them at actual readers. Future membership join first admits real Scope from
captured Entry.scope_bytes, then uses Scope.document_id and exact
(Entry.revision_id,Entry.source_scope_sha256) in the current rule. Entry has NO
document_id. Do not implement that provider or a replacement membership mock here.

Later mandatory work: protected current selection/epoch/owner/mode/raw-byte loader,
actual application principal verification, eligibility of captured membership,
checks at encode/scoring/source/grade/dispatch/delivery and revocation-safe cache
keys; fixed real CPU encoder path; private operator composition; approved data/
rights and representative held-out baseline. Real baseline remains NOT_RUN.
Policy presence/match is never CURRENT_POLICY_VERIFIED, actual token authority,
operator completeness, 20k source qualification or full-MVP acceptance. Remaining
hardware/visual/security/license/merged-ICA/human/release gates stay open.

Required default-collected pure unit coverage includes: exact closed types and
constructed-unadmitted objects; nominal/bypassed Grants; all local/global counts
and actual M/C limits; ordering/duplicates; UTF8 controls/surrogates/chunk boundary
and no normalization; multiple history pairs, withdrawn/absent declarations;
independently encoded identity golden/ambiguity and value-change witnesses;
genuine matching/all-comparison/operation/result semantics; real scope restrictions;
generic failure cause/context hygiene and sentinel identity; exact capacity witness.
Tests must not mirror implementation by using its private counters as the oracle.
