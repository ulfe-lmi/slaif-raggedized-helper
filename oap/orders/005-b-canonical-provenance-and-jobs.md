# OAP Work Order — 005-b

Status: FINAL
Identifier: 005-b
PR mode: AMEND_EXISTING_PR
Branch: oap/005-artifact-schema-and-source-scopes
Base commit: bd8e454b23b09bb25967b2c496ace9c0719a96a0
PR number: 7
Expected active: 005-a
Provenance: H activated architecture MVP and parallel coding; A architecture §§7.1–7.4,8.2–8.4,13.1–13.2,22.1–22.2; I independently accepted source005-a and local provenance-B/job-B components
Architecture SHA256: 4b41905396a3838269fd6cf372614cd23cb2c3b6a37be09f29ed752803c0983a
Governance SHA256: ee63020db4713561a44cb5eef8a7e679589b3856ce8837038817ce9a86051aa7

## Objective

Complete original005 SOFTWARE scope on existing PR7: integrate the independently reviewed
source block/span/chunk/derived-scope and job/attempt record components, prove one actual
store-to-record end-to-end journey, reconcile docs and combined checks. This is record
validation and pure scope/transition behavior, not extraction/model/worker execution. No
whole005 acceptance is delegated to coding; strategy reviews before a protected merge.

## Dependencies and current state

Current canonical report head bb7fd82a811fd63c63c4dd40e66ff45a706c1a16, sole implementation parent 08b65b9ffc4dc7ebde9651ea258a9cbe4eb37a79, clean005branch;
report SHA d4e427e9a6e87f8a6429d6761d268b138767cb48d830750df2c5639d0f93b241.
Source005-a accepted in exact oap/reviews/005-a-review.json SHA2dd04434984cc3a92e31144a10a3d04c177b25b6894b2b362ba65341ede62c5e:
implementation CI43036091799 and report CI43037886906 all5SUCCESS, lastreportjob14:26:27Z.
Unique OPEN PR7, mainbd8e454 unchanged, noauto-merge/unresolvedthreads. Prior003/004terminal
resolutions already committed. Baseline912product=562unit+350integration, separate41OAP.

Root005-a review is the only intended new untracked round-start file before this order and
active update. Commit it, the order and active bytes unchanged. Do not reset/clean/stash/
switch coding worktree or recreatePR7. No005-a control/response FIFO reread or replay.

Exact accepted LOCAL candidates:
- Provenance-B tip3f2ec5768cc07c86c2f0ab663a4e4af23ecac406, implementation
  4c0b3519ebf242edac9462bf24ee5fccd87ce7b5, reportSHA
  b84b4a6959a066561c012f5b5467255414775cf5dc0869a3607f1aaa3b965bcf.
  Root regular parallel/provenance-b/review.json and opposite peer audit-provenance-b/report.json
  in strategic home accepted scope. Actual provenance_records.py APIs: admit_record, catalog,
  Registry.bind_chunk/bind_derived/bind_neighbors, reader_allows; immutable source-scoped DTOs.
- Jobs-B tip798d92524dfcf4b24bc312712d21453f159b204a, implementation
  7b6959ab65e517dd88edb4ce4569c14a813ba451, reportSHA
  a13c1e275bf0fc566aa9f631c1991c40b1369aedda6f065159305784701abde7.
  Root regular parallel/job-records-b/review.json and opposite peer audit-job-records-b/report.json
  accepted scope. Actual job_records.py APIs: admit/serialize/transition, JobSpec/Configuration/
  InputRef/JobState/Attempt/OutputRef. DTO assertions are not cache or execution proof.

Read compact coding set, this FINAL order and affected actual candidate APIs/tests/docs;
consult cited bounded full-architecture sections only if needed. Do not reload generator,
OAP helper histories, full source books, unrelated future orders or wildcard lane directories.

## Allowed paths and scope

TWO authorized LOCAL --no-ff merges of ONLY the exact accepted tips above into the existing
005 PR branch, provenance first then jobs. Preserve all original candidate report/order/
implementation identities; no cherry-picking away graph. Forecast each against actual current
parent using git merge-tree; inspect resulting parents/tree. Both independently merged clean
with preliminary005source head24d273a, but that is not permission to invent a later clean tree.
Stop and reconcile any conflict or unexpected shared-code change. This local integration is
explicitly REQUIRED under the human parallel mandate; GitHub PR/default-main merge is forbidden.
No006/PDF/tokenizer/chunk-algorithm/008 candidate branch belongs in005.

Candidate merges add provenance_records.py/job_records.py and their original tests/docs/orders/
reports. New edits limited to a meaningful combined source/provenance/job integration test,
concrete necessary record/scope bug fixes if demonstrated, docs/data-model.md or focused record
protocol, README/STATUS/UNCERTAINTIES/TESTING summaries and affected manifest/context measurements.
Use current canonical source_admission/source_cli interfaces unchanged unless a concrete scoped
integration defect requires correction. Preserve all accepted004/005-a code/tests and the thin
installed source/parity routes. No new dependency or source/role/helper/prompt/architecture rewrite.

## Non-goals

No actual native/PDF/vision extraction, chunk algorithm/tokenizer/model/GPU work, contextual
annotation generation, worker claims/retry/ownership/output publication, index/snapshot/query/API
or source-serving implementation. Those remain006/007/008/010/012/014/015/016/017 as planned.
No real corpus, credentials/services/host scan, source-owner/referral behavior, model/profile/auth
change, legal exception, release/tag/deploy, GitHub/default-main merge or next work selection.

## Acceptance criteria

1. Strict versioned bounded source-block, original-span, chunk and dependency records roundtrip
   through safe JSON/JSONL. Bind exact logical document/source revision, extraction fingerprint,
   stable block identity/reading order/kind/anchor, actual original extracted text and explicit
   origin. Source revision, extraction dependency and chunk policy are distinct traceable
   identities; do not invent an extractor execution before one occurs. Chunk records preserve
   heading/neighbors, source scope and tokenizer-count availability/provenance without claiming
   that a fixture count came from a qualified tokenizer. Reject conflicting IDs/bindings.
2. Reconstruction uses start-inclusive/end-exclusive Unicode CODE-POINT offsets into exact
   unmodified extracted block text. Ordered typed source fragments and explicit separator
   fragments reconstruct the exact claimed chunk text; repeated original table headers keep
   their original references. Test astral characters, combining marks, nonASCII and newlines
   without normalizing away source evidence. Reject unknown block/revision, invalid/boolean/
   out-of-range offsets, conflicting copied text and incorrect dependency/checksum. Define
   empty-fragment handling explicitly; never reinterpret byte/token offsets as code points.
3. Native text, literal visual transcription and interpretation remain distinct origins.
   Vision-derived records retain original page/crop references and uncertainty as applicable;
   actual geometry is optional and cannot be manufactured from model description. Original
   source blocks are immutable and separate from context/interpretation artifacts. This slice
   validates supplied synthetic extraction records; it does not perform real extraction.
4. Required access labels are explicit, canonical sorted sets with all-label semantics;
   missing labels invalid, empty explicitly public classification. Blocks/chunks inherit the
   whole approved source revision classification. Derived representation labels contain the
   target/support union, while v1 support admission STILL rejects crossing the approved
   document/source-access boundary. Unioning labels is not permission to construct a mixed
   public/private parent. Shared bytes or text never merge source/document/rights identities
   or replace restrictions with the most permissive label set. Preserve processing versus
   redistribution rights. Pure effective-scope helpers only intersect corpus/version/caller
   restrictions with explicit operator grants; absent grants never widen access. Authentication,
   policy epochs/revocation and actual retrieval admission remain later implementation.
5. Deterministic job identities bind complete declared inputs/policies, while immutable attempt
   records have their own identities, safe status/request correlation and output-reference/
   failure/unknown-completion evidence. Serialize bounded typed statuses consistent with§8.4.
   Mutable job state is distinct from immutable attempts/artifacts; COMPLETE in a DTO is not
   proof an output exists. Actual claim ownership, output-first publication/reconciliation and
   bounded retry execution remain010. No exactly-once inference from a schema or successfulHTTP.
6. Compose actual005-a admission/store/load with two synthetic logical documents sharing bytes
   and differing ACL/rights, relevant metadata revision, synthetic ordered blocks and exact
   multispan chunks, pure reader-scope decisions and job/attempt roundtrip. Assert one verified
   blob with distinct revisions/scopes, no cross-boundary support/dedup broadening, exact
   reconstruction and immutable-dependency validation. Preserve descriptor/pathrace/readbounds,
   safe atomic publication/retry and corruption-refusal regressions; do not substitute record
   constructors for the previously required real filesystem journey. Check ALL original005
   criteria before recommending whole-objective acceptance. Current-head CI and actual product/
   OAP/lint/governance checks must pass; missing/skipped/pending is not success.

## Verification and negative evidence

Add one actual unified journey beyond separate component constructors: owned two-document
shared-byte roots/store with different rights/labels/corpus and declared versions, immutable
metadata revision, verified stored byte load, synthetic original Block/Dependency records,
Unicode/CRLF multi-span plus explicit separators, Registry reconstruction/neighbor binding,
same-source derived support scope, reader grant/restriction intersection, and job/attempt
roundtrip/transition with real revision fingerprints. Unknown version remains fail-closed by
existing reader policy; do not widen access to make fixtures pass. Supplied extraction/counts
and job output availability are assertions, not executed parsers/tokenizers/cache validation.
Configuration hashes may describe explicitly not-applicable fixture settings; never fabricate
an observed model/encoder identity or real extraction to fill a record.

Preserve actual path/descriptor/byte/hash/race/atomic-publication/corruption source regressions.
Test copied/forged records, wrong revision/dependency/text/hash/offset and scope unions, missing
labels/grants, known0 versus null, unknown completion/no automatic retry, safe UTF8/privacy
admission and neighbor reciprocity. Actual worker locks, artifact reuse verification and full
history/request correlation remain010; document the boundary without pretending it is done.

Run meaningful focused new/affected checks, then appropriate product/OAP/lint/governance on
combined source once. CI runs tests/unit and tests/integration SEPARATELY; same-basename
collection collision is known, do not rename/remove tests or repeatedly run combined discovery.
Use -o addopts= with -q if a summary is needed; capture actual subprocess exit status. For counts
use collect-only, not repeated full suites/grep pipelines. Every required actual implementation-
head CI check must succeed; skipped/missing/pending/cancelled is not green.

## Documentation

Document exact source/extraction/chunk/config identities, Unicode codepoint and separator
reconstruction, native/transcription/interpretation provenance, complete-label scope/rights and
same-source support, unknown-version behavior, reciprocal neighbors and actual job/attempt DTO
versus execution/cache claims. Reconcile every original005criterion before recommending closure.
Keep the routine <=50000byte ceiling; current42370 permits concise T12 notes, put detailed
contracts outside routine. Update measured context/manifest entries together; model tokens stay
UNMEASURED. Existing qualification-testing detail stays verbatim and linked; no weakening checks.

## Runtime and protected resources

Live target/model/GPU/corpus authorization: NONE. Ordinary reversible local development, owned
synthetic files/CPU/loopback fixtures and GitHub publication/CI only. No actual NVIDIA probe,
model/tokenizer/artifact downloads, unknown PID/service/host/credential action, real data,
source fetch, legal exception or deployment. Preserve human-selected coding Qwen3.8-27B/A100
Q8/xhigh/CLI0.164.0. Real qualification/license/ICA/full text+visual MVP remains open.

## Deferred human adjudication

- Decision: NONE

## Publication and report

Amend existing PR7, commit exact Root review/order/active unchanged. Only the TWO ordered
local candidate integrations are authorized; no GitHub PR/default-main merge. Inspect actual
implementation-head CI before immutable report-only SELF with literal sole implementation
parent; verify exact remote report bytes/head/ancestry then send ONE response005-b using the
qualified wrapper. Complete bounded coding goal and idle. No post-response CI polls/readers,
next work or canonical006 activation. Strategy owns report-head CI, independent whole005
review, protected qualifying merge/mainCI/resolution and any continuation.
