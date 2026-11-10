# OAP Work Order — 003-d

Status: FINAL
Identifier: 003-d
PR mode: AMEND_EXISTING_PR
Branch: oap/003-generator-adapters-and-cache-probes
Base commit: 93b43177f4dcd0b28ef2c5ed33a049f83217f152
PR number: 5
Expected active: 003-c
Provenance: E actualHTTP structural variants; A13 A14 A22 A37; unfulfilled003-c criteria2–4
Architecture SHA256: 4b41905396a3838269fd6cf372614cd23cb2c3b6a37be09f29ed752803c0983a
Governance SHA256: d0fcb42531e4450fc95eb6da56eb84eb1d85e4191817526864aabfe3a326f9bb

## Objective

Finish shared coordinate and item-lifecycle validation while preserving valid supported
streams. This remains original objective003 on the same PR. The published003-c candidate still fails the actual structural variants, independently
reproduced at the current head and documented by the final strategic review. Native generation
and probes remain required in later separately finalized suffixes; no numeric advance/merge.

## Dependencies and current state

Verified2026-11-10: uniquePR5OPEN on the existing003 branch, base/main
93b43177f4dcd0b28ef2c5ed33a049f83217f152. Currentremote003-c reportSELF
 ae05438c037da94bb344046ed8610c5d65514930, soleparentimplementation
5bfca450ffd7a3a7e0a512b2ef66cb40ff5b715a; onlyreportdiff; reportSHA256
 d7791f5c820b70697ac6fa5bb0a911fc5b09b15a2d526710ca4b8c08259e0566.
FinalheadCI42760691508 and repairedimplCI42760298472 all5SUCCESS. Firstimpl1f2c111
had a real3.14 nesting-fixture failure, fixed in5bfca45 by capacity-aware tests. All original
7HTTPcases now correct, but6additional malformed structural variants still produce
TERMINAL. Strategy's exact oap/reviews/003-c-review.json therefore CONTINUE/NOT_ACCEPTED;
reportedCOMPLETE is not acceptance. Exact003-cresponse consumed and remote report verified;
never reread it. Old boundedcodinggoal cleared/postreportturn stopped. Before publication,
tracked worktree clean atSELF, only strategic003-creview is untracked for unchanged commit.
Preserve all existing fixes.

## Allowed paths and scope

src/slaif_raggedized_helper/model_clients/gateway.py's shared coordinate/state validation,
focused actualHTTP gateway tests and necessary synthetic fixture helpers; accurate generator
contract/status/test docs and directly affected governance measurements/hashes only. Exact
strategic review/order/active/report bytes. No transport/config/architecture/source-plan
redesign, dependency addition, native/probe work or helper changes. Existing Pydantic is
available if useful; one consistent private validation path or equivalent explicit guards
must enforce the supported invariants, rather than special-casing individual test strings.
Read affected coordinate/item/part methods and the concise reproduction first; do not reload
the full sibling gateway/Codex/history books. No broad public protocol expansion is requested.

## Non-goals

No new wire family/tool execution, full OpenAI parity, model/profile/provider replacement,
real service/model/GPU work, source ingestion, new PR/objective, merge, tag or release.

## Acceptance criteria

1. Distinguish field absence from present null in the shared coordinate decoder. A missing
   optional content coordinate can retain the supported implicit-part0 semantics; a supplied
   null output_index/content_index is malformed, not absence. Validate all supplied critical
   coordinates/types before state access and consistently across recognized event boundaries.
   Existing wrong/negative/bool/string/object/foreign-coordinate refusals remain safe.
2. Bind explicit content-part coordinates to their actual ordered final part positions. A
   stream that renames the second part1 to7 throughout events but has only2final parts must
   fail, not be sorted into apparent valid text. Enforce known bounded part membership/order
   and reconcile observed lifecycle/completion with final content. Unknown/unfinished parts
   cannot disappear solely because final concatenated text happens to match.
3. Freeze output-item type/identity from added through done and final. A reasoning item
   cannot become a message with the same ID to salvage output_text. Text events belong to
   supported message parts. Latch item completion: duplicate item.done or later contradictory
   state is refused. Validate terminal done status for each supported type, including a
   reasoning done in_progress followed by completed reasoning in the final output. Existing
   unsupported function actions remain refused and no internal reasoning becomes answer text.
4. Preserve all original positive single-part/multipart/multiple-message and valid refusal/
   incomplete/error cases, exact text/order, deadlines/privacy and finite no-replay behavior.
   The original read-only seven-case oracle must still pass. The separate read-only
   /tmp/raggedized003-structural-variants-review.py sends thirteen real loopback POSTs and
   exercises all six mutations; every malformed variant yields safe FAILED and no successful
   salvaged answer or raw exception. Do not weaken/modify a strategic oracle to make it pass.
5. Add actualHTTP project regressions for the six cases and boundary/type/lifecycle variants
   that test the invariants above, not only helper calls. Assert paths/counts, exact outcomes,
   safe error/canary behavior and complete positive text. Preserve existing product/transport/
   OAP/lint/governance/schema checks and all current-head CI jobs. Update claims to exactly
   supported/proven behavior. If any criterion remains unmet, report it truthfully; green
   fixture counts are not a substitute for the independent structural evidence.

## Verification and negative evidence

Run both read-only owned-localhost reproductions, focused actualHTTP project regressions,
then affected gateway/transport/unit/OAP/lint/governance checks and actual CI. No live model,
download, credentials or corpus required. Reproduce supplied nulls, part coordinate gap,
type-changing completion, duplicate completion and contradictory reasoning status, plus valid
counterexamples. Report code/fixture/version limits and every failed/unrun/skipped check.

## Documentation

Keep the generator contract accurate for supplied coordinates, explicit/implicit parts,
supported item lifecycle and safe outcomes. Remove any surviving contradictory2MiB default
claim: response2,000,000 and stream16,000,000 bytes are decimal; event262,144bytes is256KiB.
Current status must preserve whole003 native/probe/live qualification as pending. Preserve
the explicit certifi license gate and actual context table/map/manifest synchronization.

## Runtime and protected resources

Live authorization: NONE. Owned disposable loopback fixtures, ordinary lightweight local
tooling and GitHub CI are permitted. Preserve model/provider/profile, other projects/services,
private state, source originals, transport behavior and all prior immutable orders/reports.

## Deferred human adjudication

- Decision: NONE

## Publication and report

Commit exact strategic activation/prior review unchanged, amend the existing unique003 PR,
publish immutable report-only SELF with literal implementation parent, verify remote report
identity/bytes and send one response using the existing wrapper. Stop mutations and end the
coding goal at that boundary; strategy independently accepts or orders continuation.
Commit pre-published oap/reviews/003-c-review.json unchanged with the exact strategic
003-d order/active. Previous reports remain immutable. Correct the prior report's test-count
claim in later evidence: actual current collection212product=132integration(99gateway+33transport)
plus80unit; separate OAP41. The003-c report's136/95/41 figures are not authoritative.

Use the working interfaces, not helper-internal scans:

```sh
python3 oap/bin/verify_report.py --repo-root /home/janezp/codex-work/slaif-raggedized-helper --runtime /home/janezp/codex-supervision/slaif-raggedized-helper/runtime.json --identifier 003-d
bash /home/janezp/codex-supervision/slaif-raggedized-helper/send-response.sh --identifier 003-d
```

The sole control wrapper already consumed this round's signal before waking the fresh coding
context. Do not reread either FIFO or create competing readers. Preserve selected client
model/provider/profile and end the bounded native goal at truthful report/response; strategic
acceptance remains separate. No old report reimplementation or next-work selection.
