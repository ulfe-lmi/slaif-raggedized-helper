# OAP Work Order — 003-c

Status: FINAL
Identifier: 003-c
PR mode: AMEND_EXISTING_PR
Branch: oap/003-generator-adapters-and-cache-probes
Base commit: 93b43177f4dcd0b28ef2c5ed33a049f83217f152
PR number: 5
Expected active: 003-b
Provenance: E independent actualHTTP protocol reproduction; A13 A14 A22 A37; original003-b criterion6
Architecture SHA256: 4b41905396a3838269fd6cf372614cd23cb2c3b6a37be09f29ed752803c0983a
Governance SHA256: ab279c09e5ad1bdb3ab680a6b7e924ed2e4497ab4a239fedf4c0f352a776b452

## Objective

Repair the remaining structural gateway validation gaps without rejecting valid supported
Responses streams. Same003 branch/PR; numeric003 native adapter/probes remain required and
will follow in separately finalized continuations. The 003-b report is published and
independently reviewed; the remaining defects below are
reproduced at its exact implementation and report-equivalent source tree. Whole003 stays open.

## Dependencies and current state

Verified2026-11-10: PR5OPEN on the existing branch, main/base93b43177f4dcd0b28ef2c5ed33a049f83217f152.
003-b implementation51dc499a5b08f67901cdfb87436f9026a96c5c48; current remote/reportSELF
e20ad7d855d847aba34c1a1ae960fa5e86f1cc74, sole parent implementation, report-only diff,
reportSHA256d87fef52f8ee7caa180f612f21dd02aee45df3834fe713bb7c61d80011632bcf.
ReportedResultCOMPLETE describes its bounded execution claim; strategic review is CONTINUE,
NOT_ACCEPTED: actual malformed wire successes/raw exception and valid multipart rejection
contradict criterion6. Both implementationCI42754483667 and finalreportCI42755267413 passed
all5checks. Exact003-b response consumed and remote publication independently verified;
never read it again. Coding goal cleared and post-report old turn stopped; prior tracked
worktree clean, only exact strategic003-b review is now untracked for unchanged commit.
The scoped application corrections below are authorized. Do not change architecture/role law,
model/provider/profile or live runtime service settings, or select a new numeric objective.
Use the working003-b transport; no transport redesign, native implementation or new framework.

## Allowed paths and scope

src/slaif_raggedized_helper/model_clients/gateway.py's bounded accumulator/final parsing,
tests/integration/test_gateway_generator.py and necessary shared synthetic fixtures.
Read the affected _collect_output, _GatewayAccumulator and _finish_stream functions first,
then relevant test helpers/cases; avoid loading unrelated whole source books.
Concise actual contract/test docs, current
CI collection only if needed, exact strategic review/order/active/report. No broad schema/
config/source/architecture changes or additional runtime dependencies. Read current affected
functions/tests, this order and the small reproduction first. Do not reread the entire sibling
gateway/Codex tool implementation or historical OAP helper library. Pinned source reference
remains f2df0e82df8766740d9ac169ea56ffd7a3cb1f1e; inspect only specific disputed fields as needed.

## Non-goals

No native/probe implementation in this round, broad transport/framework rewrite, live model
call, source ingestion or retrieval/API work. No model/provider/profile change, architecture/
role-law redesign, new PR/numeric objective, protected service change, merge, tag or release.
Original003 native/probe requirements remain pending for later same-PR continuations.

## Acceptance criteria

The executable independent review probe is /tmp/raggedized003-protocol-review.py. It sends
seven real loopback POSTs through GatewayGenerator. At the observed candidate the baseline
succeeds, four malformed streams wrongly succeed, a malformed status leaks TypeError, and
a valid two-content-part stream wrongly fails. See the final strategic review for fresh
results; historical observations are not claims about a later candidate. Treat the strategic
reproduction as read-only evidence; add proper project tests without weakening its oracle.

1. Malformed JSON structures/types produce safe typed failure, never raw TypeError or a
   salvaged successful answer. In particular message.status={} and[] must be guarded before
   set membership. Handle invalid JSON/UTF8 and excessive nesting within existing bounded
   parsing contracts. Error reasons are fixed/safe; provider canaries never enter public
   exceptions/logs. Preserve genuine refusal/incomplete/unknown-completion distinctions.
2. A completed event requires a valid nonempty response ID consistent with observed events;
   a missing/malformed ID cannot be ignored. Validate actual item identity and all supplied
   item/part coordinates at their correct event-envelope boundary. Wrong delta.output_index
   cannot be ignored even when item_id names a known item. Required coordinates follow the
   actual pinned supported shape; do not invent output_index inside final output-array items.
3. Validate delta/text/done field types and supported lifecycle/status transitions. An array
   delta followed by empty done/item data and an authoritative terminal text is a malformed
   stream, not success. A nonterminal item.done status followed by a completed final message
   is contradictory, not success. Retain duplicate/foreign/terminal/order checks and prevent
   a later valid final payload from erasing an observed protocol error.
4. Accumulate and reconcile text by item AND content-part identity, preserving final array
   order. A valid message with two output_text parts, complete part-added/delta/text-done/
   part-done events and consistent item/final data must succeed (fixture text firstsecond).
   The pinned source accepts multiple bounded content parts; one buffer per item confuses
   the second part's cumulative text with concatenated prior parts. Keep multiple-message
   ordering, content bounds, delta/done/final comparison and safe refusal semantics. Unknown
   or contradictory part coordinates cannot be silently merged or accepted. No arbitrary
   recursive text extraction or blanket refusal of all multipart streams.
5. Replace the measured-overhead/1microsecond relative-deadline premise in the gateway
   zero-dispatch test with a deterministic generator-local clock/boundary setup. Do not patch
   the global stdlib time module or weaken real HTTP deadline/finite-retry coverage. Then add
   controlled HTTP regressions for every failing reproduction plus malformed type/ID/
   coordinate/status variants, and positive single/multiple parts/messages, valid refusal
   and incomplete terminals. Assert actual request paths/counts/outcomes, safe canaries and
   supported text exactly. Preserve all003-b transport/gateway/foundation/OAP tests and lint,
   schema/governance and actual current-head CI. Mock invocation or a parser-only selection
   cannot substitute for wire-to-result evidence. Report any remaining failure truthfully.

## Verification and negative evidence

Run the read-only owned-localhost reproduction, add the corresponding real HTTP project
regressions, then run affected gateway/transport tests, existing unit/OAP/lint/governance
checks and actual CI. Preserve the positive single/multiple part/item cases and every safe
failure boundary; do not label a merely nonterminal refusal as successful text. Missing,
failed, skipped, pending or unrun evidence stays explicit. No live services/models are needed.

## Documentation

The final 003-b candidate still has the following directly affected controlled documentation
omissions; finish their refresh: TESTING now2718bytes/routine context35269 (recalculate actual final
bytes), but CONTEXT-BUDGET still2043/34594 and DISTILLATION-MAP onlyT01–T05. Update measured
oap/governance/CONTEXT-BUDGET.md, DISTILLATION-MAP.md and MANIFEST.json together without
changing immutable prior orders. Correct STATUS.md's stale
current product-absent/idle/bootstrap-main claims by clearly separating historical events.
Keep generator-contract claims aligned with actual multipart/type validation and native/probe
pending scope; byte defaults are decimal2,000,000/16,000,000, not2/16MiB. These few documentation
paths are expressly in scope for those demonstrated003-b omissions, not a governance redesign.

## Runtime and protected resources

Live service/model/GPU/corpus authorization: NONE. Owned loopback fixtures, ordinary local
tooling and GitHub CI are authorized. Preserve existing model/provider/profile, private state,
transport deadline/cancellation behavior, original sources and all prior immutable reports.
No native/probe scope expansion, helper redesign, new PR, merge, tag, deploy or release.
Existing missing live-qualification and certifi/license-policy gates remain explicit.

## Deferred human adjudication

- Decision: NONE

## Publication and report

Commit pre-published oap/reviews/003-b-review.json unchanged, along with exact strategic
003-c order/active bytes. Do not edit any prior coding report. Amend the same unique003 PR,
publish an immutable report-only SELF with literal implementation parent, verify remote publication and
respond exactly once. End the coding goal at report/response. Strategy alone reviews and
decides next continuation; passing this slice does not satisfy full003 without native/probes.

Use the existing verifier/response interfaces and exact runtime path:

```sh
python3 oap/bin/verify_report.py --repo-root /home/janezp/codex-work/slaif-raggedized-helper --runtime /home/janezp/codex-supervision/slaif-raggedized-helper/runtime.json --identifier 003-c
bash /home/janezp/codex-supervision/slaif-raggedized-helper/send-response.sh --identifier 003-c
```

After response, return to the existing sole external control waiter; start one only if none
exists. Never read either FIFO manually or create a competing reader. Do not scan helper
internals merely to rediscover these working interfaces. Preserve the actual selected client
model/provider/profile. Native per-round goal ends with truthful publication/response, and
strategic acceptance remains independent.
