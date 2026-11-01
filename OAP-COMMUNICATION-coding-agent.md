# Coding handoff protocol — concentrated OAP profile 1.0

Repository: ulfe-lmi/slaif-raggedized-helper. Root: /home/janezp/codex-work/slaif-raggedized-helper.
Strategy: /home/janezp/codex-supervision/slaif-raggedized-helper.
This protocol applies only to CODING and does not activate anything by its presence.

## Selection and publication

`oap/active` is absent when inactive; empty/malformed is an error. Active bytes are exactly
`NNN-suffix\n`, suffix a..z, aa..zz. Only strategy changes it and immutable `oap/orders/`.
Exactly one matching order; never select by mtime, sort or biggest number. Initial -a creates
one objective PR; resumed -a reuses an existing PR. Corrections use next suffix, same PR.
Process/context/model replacement does not create a suffix. After zz change protocol explicitly.

The strategic publisher validates provenance, final status, source identities, allowed
transition and DHA. Under a lock it writes the complete immutable order, then atomically
replaces active. These are two recoverable writes, not one filesystem transaction. A partial
identical unresolved publication may be completed; a historical completed order is not replayed.
Coding commits the authorized order/active bytes unchanged with ordinary implementation.

## FIFOs and fresh turns

`STRATEGIC_HOME/control.fifo`: strategy writes, coding wrapper reads.
`STRATEGIC_HOME/response.fifo`: coding writes, strategic wrapper reads.
Every payload is exactly ASCII `OK`, no LF, ID or status. Close sender after both bytes.
The active pointer's LF is intentional and differs from the wire payload. FIFO is a wakeup,
not authenticated authority or durable completion. Exactly one reader per direction; external
blocking wait consumes no model inference. Helpers reject invalid framing/types and use locks.

At operational startup use the one control waiter; after its consumed notification execute
the selected order without reading again. Tmux wake text says the signal was already consumed.
Normal new rounds use a fresh coding conversation in the existing approved client. Recovery
resumes unfinished work under its original ID/PR. No automated provider/model substitution.
Never start a second waiter, assume a background process automatically wakes the model, or
transmit instructions as FIFO payloads. `message.txt` remains objective-neutral startup law.

## One execution round

1. Reconcile root/role, compact governance, active order, source hashes, GitHub/main/PR and
   dirty state. Preserve unrelated work. Resolve exact PR mode and objective identity.
2. Implement scoped behavior, tests and docs; append exact strategic DHA payload if ordered.
   Safe in-scope setup/failure repair belongs to coding. Report conflicts without scope expansion.
3. Commit/push implementation plus unchanged order/active. Create or reuse exactly one PR.
4. Inspect CI, repair within scope before final report. Record literal full implementation SHA.
5. Atomically create one immutable `oap/reports/NNN-suffix-slug.md` using report template.
   Include `Implementation head SHA: <full ID>` and `Report publication commit: SELF`.
6. Commit ONLY that report, with implementation as first parent; push. Verify remote PR/head,
   exact report bytes, report-only diff and first-parent identity with the report verifier.
7. Publish a separate local execution receipt of post-push checks; send exact response OK using
   the helper only after remote verification. Then stop mutations and return to one idle waiter.

SELF means the report-containing commit; a report cannot contain its future hash. It can state
checks already observed at implementation head, not future report-head success. Strategy waits
for required checks on the exact current reviewed head. A later continuation preserves older
report commits reachable in PR history. No report amendment/rewrite; add evidence in later rounds.
PARTIAL/BLOCKED/FAILED reports may signal if properly published; OK never means accepted/merged.

## Report minimum

Identifier/order, result, canonical repo/PR/base/head, implementation ID and SELF, precise
changes/paths, numbered acceptance evidence, exact commands/results, mock/live distinction,
docs impact, D1 candidate/ordered append, limitations/deviations, preserved resources and
no-merge confirmation. No secrets/private data. Include environment blockers truthfully.

## Recovery

No active → inactive. Consumed signal/no report → reconcile same round/PR and resume explicitly.
Report local only → finish publication, not rewritten claims. Report pushed/lost signal →
strategy verifies and reviews; do not reimplement. Pending CI → wait, no new objective.
Conflicting/multiple orders/PRs, stale governance or invalid bytes → preserve state, report error.
Human quit → stop owned activity, no resurrection. Full decision table: `oap/RECOVERY.md` only
when recovery is needed. Strategy independently accepts, corrects, abandons or escalates D2.
