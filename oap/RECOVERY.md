# Recovery without replay

Run check_state, inspect GitHub and exact active order/report before any restart. Receipts assist
diagnosis; cannot override remote truth. Role/client replacement does not renumber work.

| Observed durable state | Required action |
|---|---|
| No active | Remain inactive; drafts are not tasks |
| Empty/invalid active or multiple matching orders | Preserve conflict and repair by strategy; do not guess |
| Order written, active replace interrupted | Publish identical unresolved transition under same expected predecessor; never reactivate completed history |
| Control consumed, no report, worker gone | Verify no competing worker; explicitly resume same order/branch/PR without consuming another signal |
| Initial -a already has PR | Reuse unique verified PR; no duplicate creation |
| Report exists only locally | Verify immutable contents/parent; complete remote publication; no claims of success early |
| Report remotely published, response lost | Strategic verify/report review; no coding replay or mandatory new signal |
| Duplicate notification | Verify durable state, reject duplicate execution/notification; diagnose stale consumer |
| CI pending | Wait/recheck exact head; no new suffix merely for waiting |
| Remote head changed since review | Re-review changed code/report/checks before merge |
| Conflicting PRs or unknown uncommitted work | Preserve; investigate ownership; no reset/clean/stash |
| Human quit | Stop owned waiter/client; no automatic resurrection |

Sparse tmux intervention: verify designated pane/cwd, capture only needed tail, identify failing
boundary and smallest diagnostic, record action in strategic logs. Never copy secrets, change
model/profile or run shell in a live agent prompt. A recovery prompt names the same objective
and already-consumed notification. Starting a second response/control reader is forbidden.
