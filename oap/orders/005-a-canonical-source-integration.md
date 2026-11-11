# OAP Work Order — 005-a

Status: FINAL
Identifier: 005-a
PR mode: CREATE_NEW_PR
Branch: oap/005-artifact-schema-and-source-scopes
Base commit: bd8e454b23b09bb25967b2c496ace9c0719a96a0
PR number: NEW
Expected active: 004-f
Provenance: H activated full MVP and parallel coding; A05 A07 A24 A25 A34 / architecture §§7.1,8.1–8.3,9.1,13.2,22.1–22.2; I accepted local source-admission-b and source-cli reviews; E verified004 software replan and protected development merge
Architecture SHA256: 4b41905396a3838269fd6cf372614cd23cb2c3b6a37be09f29ed752803c0983a
Governance SHA256: b41a0685ee4ad16633757aa52df51257b0c10de66bb58444dadad670f5ff83d1

## Objective

Integrate the independently reviewed local source admission/store and operator CLI candidate,
provide a thin installed `raggedized source` route, and prove actual import/inspect behavior
on the canonical combined branch. This is the first005 slice on one PR. Block/span/chunk,
derived-scope and job/attempt contracts remain REQUIRED in same-PR continuations before
whole005 acceptance. No006 canonical activation or partial005 merge.

## Dependencies and current state

004 replanned software accepted and PR6 merged to main bd8e454b23b09bb25967b2c496ace9c0719a96a0,
accepted tree d563611cb32ff5cb966d52c2aa8b50b50f8da9a3. The exact prior resolution
is oap/reviews/004-resolution.json; it must record all5 mainCI SUCCESS before this order
is published. Final004 report ca6efbfe1867a81c027a1c249c48f07f10528522, sole implementation
parent d34e31b334848501c2ef0e60c165edae3d3c7fa6; report SHA3795727fca00f3b328254a2aba7b7d95a70502c74a72a027f7fe21944f7e8bbd.
Root final review audit/004-f-review.json SHA5c5c431e5f6ace85472c123c0afb69d5c7dfcae76bf7e94f3909ac0aec0b7225
accepts software ONLY. All real014/015/016/018/019/model/hardware/quality/license/ICA/MVP
gates remain open; actual qualification not replaced by development merge.

Coding worktree remains004 branch at ca6efbf, clean apart from authorized Root005 activation
and prior review/resolution. Coding owns safe creation of NEW005 branch from verified main,
preserving these bytes. Strategy has not switched/reset/stashed/cleaned coding state.
No other objective PR is open. No004 response/control FIFO may be read or replayed.

Read normal compact coding set, this exact order, actual affected source/CLI/tests, and cited
architecture sections as needed. Do not reload generator histories, helper internals or future
orders. Candidate is exact branch oap/parallel-005-source-cli at
32a2b84d099f2641123d2569b01afe533064ac61; it includes source-admission-b tip
0837191198b2b1712445d5ba6ca268d358637866 with boundary corrections. Actual APIs:
source_admission.parse_manifest, OriginalStore.admit/inspect/read_original and source_cli.main.
Root accepted reviews are exact regular strategic parallel/source-admission-b/review.json
and parallel/source-cli/review.json; opposite-author audit-source-b and audit-source-cli
report.json corroborate. Recheck their exact receipt/report identities before integration.

## Allowed paths and scope

ONE authorized LOCAL --no-ff merge of exactly32a2b84d099f2641123d2569b01afe533064ac61 into
new005 branch, preserving candidate order/report/implementation histories. Do not cherry-pick
away report identities. Forecast from main+tip is clean automatic tree
8332b7bf6d967685d991ffdb7782ad639d6dbf88, plus strategic round-start files. Any source
conflict requires stop/reconcile; no unreviewed source rewrites to force a merge.
This LOCAL integration is required under explicit human parallel mandate; GitHubPR/default-main
merge stays forbidden to coding. No provenance/jobs/text/PDF/006 branches in this slice.

Source candidate brings source_admission.py, source_cli.py, their source/CLI tests, component
docs and original005 local candidate histories. New edits limited to thin cli.py source-prefix
delegation to existing source_cli.main (reuse argparse/logic; follow accepted parity pattern),
focused installed source CLI tests, necessary source bug fixes if actually demonstrated,
docs/data-model.md or focused source protocol, README/STATUS/UNCERTAINTIES/TESTING and affected
governance measurements. No unrelated qualification/resource/model-client changes. Preserve all
accepted004 source/tests and architecture/source-original/role/helper/prompt bytes.

Commit exact Root oap/reviews/004-f-review.json and004-resolution.json plus this order/active
unchanged. All application work remains coding's; strategy provides reviews/orders only.

## Non-goals

No extraction/chunking/parser algorithm, PDF/backend/dependency changes, tokenizers/models,
context jobs, retrieval/API/source-serving endpoint or network source fetch. No claim of
principal authentication, policy revocation, snapshots or workers from admission records.
No real corpus, protected service/GPU operation, human-owner/referral behavior, model/profile/
auth changes, PR/default-main merge, next-objective selection, release/tag/deploy or license
exception. Real trials stay NOT_RUN and source processing approval never means redistribution.

## Acceptance criteria

1. Strict versioned source manifest, original artifact and admitted document-revision records
   round-trip through bounded safe JSON. Preserve logical document identity, approved source
   location, inert canonical display URI, corpus, explicit required access labels, processing
   and redistribution rights, declared product/version and original SHA256/media type/size/
   controlled immutable storage reference. Relevant revision metadata includes title/language/
   product/version/effective-date/declared authority and its revision identity; unknown facts
   stay unknown. Do not fabricate an extraction/model fingerprint before extraction occurs:
   source revision and later extraction dependency remain distinct and traceable. Do not
   invent new jurisdiction/authority-resolution behavior from the post-MVP concept document.
2. Admit only operator-approved local regular files beneath explicit approved roots. Bound
   manifest bytes/entries and actual streamed file reads, not just a priorstat. Require
   processing approval and explicit rights/ACL/corpus fields; absent access labels are invalid,
   an explicitly empty set denotes public classification. A processing grant never implies
   redistribution permission. Source bytes/display metadata cannot choose an output path,
   add a source location, invoke tools or cause a fetch. Support the initial architecture's
   localtext/Markdown/nativePDF originals as bytes; parsing those formats remains006/016.
3. Prevent traversal, escaped/absolute relative paths, symlink and special-file access at the
   actual open/read boundary, including intermediate-directory replacement races. Approval
   must still bind the descriptor actually read; string normalization followed by unchecked
   open is insufficient. Reject oversize/growing streams within finite memory/time limits.
   Document source-change handling and the qualified local filesystem assumptions honestly.
   Do not solve untrusted input by following a symlink and declaring its final target approved.
4. Hash and store the exact admitted bytes in the architecture's controlled original layout.
   Two logical documents with identical bytes may reuse one verified original blob while
   retaining separate source/document identities, corpus, rights and ACL metadata. A metadata
   correction affecting identity must produce the appropriate new immutable revision even
   if bytes are unchanged; identical retries reuse verified matching complete artifacts.
   Canonical identities are independent of incidental JSON key order and use schema versions.
   Refuse corrupt existing bytes, conflicting immutable IDs, wrongschema/hash/size or unsafe
   stored references; never overwrite an existing immutable artifact to make reuse appear valid.
5. Publish owned same-filesystem temporary data only after complete validation and flush,
   using atomic publication/directory durability suitable for the documented localPOSIX scope.
   A final metadata reference never points to partial/unverified bytes. Interrupted operations
   leave prior complete artifacts readable and allow an idempotent retry; an orphan complete
   original is not a completed document import. Inspect/load only controlled bounded schema/
   checksum-verified artifacts. No pickle/object execution, arbitrary loader or source-chosen
   executable path. Keep private locks/staging operational state distinct from source records.
6. Exercise installedCLI/application import-store-inspect behavior with two owned synthetic
   logical documents sharing bytes and differing rights/ACL, then a relevant metadata revision.
   Assert one shared verified blob, separate correct document revisions/classifications, safe
   reuse and verified loading. Negative tests exercise actual descriptors/reads for traversal,
   symlink/intermediate replacement, special files, oversized/growing input, corrupt stored
   artifacts, conflicting IDs/schema, interrupted publication and retry. Use deterministic
   owned fixtures, not timing luck or mock-only method assertions. Routine errors/logs exclude
   source passages, private paths/URLs, raw exception messages and credentials; source content
   belongs only in its deliberately authorized corpus artifacts. Existing suites/CI stay green.

## Verification and negative evidence

Recheck candidate exact local report-only SELF ancestry/order bytes/clean branch and accepted
Root reviews. Preserve actual corrected source boundary behavior (unchecked model_copy cannot
escape root; labels immutable; stat identity excludes atime). Run real INSTALLED source import/
inspect on disposable two-document shared-byte distinct rights/ACL roots/store; metadata update,
verified reuse and bounded refusal, actual corruption/path/race/interrupted-publication negatives.
Default help/import performs zero source reads/network/model work. Fixed errors do not echo
source passages/private paths. Reconcile late partial import honestly, no fictitious batch
transaction. Actual tests and required implementation-head CI must pass; skipped/missing/pending
is not green. Run focused checks then appropriate combined product/OAP/lint/governance once.

## Documentation

Document schemas/source-vs-extraction identity, actual installed/module commands/exitcodes,
verified byte dedup and independent rights/ACL, atomic same-filesystem POSIX assumptions,
private operator store trust, bounded descriptor reads, partial import results and remaining
005 records/006 extraction/010 execution/014 auth/017 revocation gates.
Routine governance currently49996/50000 bytes. Before adding new TESTING detail, move detailed
historical T08/T09/T10 qualification verification notes into a focused non-routine document
(e.g. docs/benchmarks/qualification-testing.md), preserving ALL current coverage/limitations
there, and leave concise sufficient summaries/pointers in TESTING.md. Retain required checks
and actual commands; do not weaken a law/check or merely raise/remove the50000 ceiling.
Update context measurement and affected manifest/distillation references together; exact model
tokens remain UNMEASURED. No strategic/coding constitution or helper/prompt rewrite.

## Runtime and protected resources

Live authorization: NONE. No new attributable target/corpus/license answer. Owned disposable
files/CPU/loopback fixtures, normal lightweight tooling, Git/GitHub publication and CI only.
No extra real NVIDIA query, model/GPU/credential/host scans, protected services, real corpus,
agent homes as data, network source fetch, unknown PID control, legal exception or deployment.
Preserve human-selected Qwen3.8-27B/A100Q8/xhigh/CLI0.164.0 settings. Pending license questions
remain open; no MIT-0/certifi/native-component clearance.

## Deferred human adjudication

- Decision: NONE

## Publication and report

Create unique005 PR via gh from exact main; no current objective PR reuse. Ordered LOCAL merge
is explicitly allowed; GitHub PR/default-main merge is NOT. Commit exact strategic activation/
prior review/resolution unchanged. Inspect all actual implementation-head CI before immutable
report-only SELF with literal sole implementation parent; verify remote exact report/head/
ancestry then send ONE response with qualified wrapper identifier005-a. End bounded coding
goal and idle; no post-response polls/readers or next-work choice. Strategy owns report-head
CI/review/005-b activation/whole005 merge. All real qualification and fullMVP remain unproven.
