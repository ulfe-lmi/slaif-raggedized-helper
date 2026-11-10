# Concentrated OAP operation

The setup is installed inactive. This runbook documents real scaffold helpers, not implemented
RAG commands. Default role is BOOTSTRAP; mutation commands require explicit assigned role.
Flags/role markers are procedural guards, not authenticated human authority or an OS sandbox.

## Installed layout

Repository root holds canonical PLAN, UPDATE, ARCHITECTURE, projection and CRITICAL. Root AGENTS
routes to dense coding law or preserves the existing strategic role. Versioned full strategic
law, init, protocol and roadmap are under oap/strategic-instructions; controlled identical copies
are installed in strategic home. Strategic ARCHITECTURE/PLAN/CRITICAL and initial-orders links
point to canonical repository files. Original user specifications remain untouched in strategy.
Private runtime.json, logs, receipts, locks, drafts, homes and FIFOs are outside Git.

## Scaffold verification and setup

```sh
python3 -m unittest discover -s tests/oap -v
python3 oap/bin/check_state.py --repo-root .
python3 oap/bin/setup.py --repo-root /home/janezp/codex-work/slaif-raggedized-helper --runtime /home/janezp/codex-supervision/slaif-raggedized-helper/runtime.json --dry-run
```

Setup does not need credentials or model configuration. Existing human-configured tmux clients
remain untouched. `setup.py --new-session NAME` explicitly opens two setup shells in the correct
roots; it does not start clients or activate anything. Separate empty role-home directories are
available for an explicitly configured replacement; no credentials/config/history are copied.
The current in-place clients retain their selected settings. This is an explicit adaptation
of the reference profile's isolated client-home launch to the user's already-running panes.

`materialize.py` installs a reviewed staging package, default no-write dry run; `--apply` writes.
It refuses conflicts, preserves live CRITICAL/private runtime/timing, supports identical no-op
rerun and explicitly scoped `--refresh repo/PATH` with prior-byte checks and backups. Never use
it to reset an active project. Public governance refresh updates manifest/projections/map/bytes,
then refreshes installed strategic copies at a quiescent checkpoint; it is not a seed restore.

## Activation preflight — later, under human authority

1. Record the actual human mandate; enable runtime activation only within it. A local true flag
   alone is insufficient. Respect human_stopped and do not restart a deliberately quit agent.
2. Reconcile remote/main/open PRs/checks/rules and merge-triggered actions. Development merge
   delegation cannot authorize deployment side effects. Bootstrap initially has no CI/rules;
   000 establishes narrow governance CI, not a fiction that zero required checks prove quality.
3. Verify source/projection identities, current clients/roots/panes, no competing consumers,
   actual fresh-context behavior and selected model/profile. Record qualification honestly.
4. Finalize one draft: Status FINAL; actual full base object ID, expected prior active or NONE,
   exact source/manifest SHA256, PR mode/number, concrete provenance/acceptance/paths, runtime
   permission or NONE, and complete DHA declaration. Draft placeholders may not execute.
5. Run publish_order dry-run, then real publication as STRATEGIC. It validates current remote
   and transitions, writes immutable order then active LF under lock. It sends no signal.
6. Start the sole control waiter in the coding role, then sole strategic signal/response waiter.
   These block outside inference. No extra reader or manual FIFO echo.

Example operational commands, only after that preflight:

```sh
python3 oap/bin/publish_order.py --repo-root /home/janezp/codex-work/slaif-raggedized-helper --runtime /home/janezp/codex-supervision/slaif-raggedized-helper/runtime.json --role STRATEGIC --source /absolute/path/to/final-order.md --dry-run
# Repeat without --dry-run only after satisfying actual activation authority.
python3 oap/bin/start_waiter.py control --repo-root /home/janezp/codex-work/slaif-raggedized-helper --runtime /home/janezp/codex-supervision/slaif-raggedized-helper/runtime.json
python3 oap/bin/start_waiter.py response --repo-root /home/janezp/codex-work/slaif-raggedized-helper --runtime /home/janezp/codex-supervision/slaif-raggedized-helper/runtime.json --identifier 000-a
```

The control wrapper validates exact OK, records consumption before wake, starts /new in the
designated idle coding client and sends the small coding prompt. It never changes model/profile.
Fresh-context behavior must first be qualified for this installed client; a checkout chooser or
busy prompt requires manual reconciliation, not blind command injection. Tmux input is trusted
startup/recovery only; durable order remains authority. Both sender and receiver use lock files;
duplicates refuse. Notifications contain exactly OK without LF, IDs or JSON. Active ends LF.

Since the 004-a operational correction, the coding startup prompt is the `/goal`-first
bounded-goal prompt at `oap/prompts/coding-startup.txt` (SHA-256
6d2323bb832e5f78e4cd86d6951c04c0b3975dc80730c473fc7834820965a98e; the
governance manifest measurement was updated in the same round). It
declares one bounded coding goal per order — execute only the exact
FINAL order selected by `oap/active`, continue implementation/tests/
docs/unique PR/CI through the immutable report-only SELF commit and
remote verification, send exactly one response OK, then mark the goal
complete and remain idle. A truthful COMPLETE/PARTIAL/BLOCKED/FAILED
execution report ends the bounded goal; strategic acceptance, merge and
next-order selection stay separate. The new `/goal`-first startup is
NOT operationally validated by file hash alone: strategy qualifies it
during the same-objective 004-b fresh control handoff, before final 004
acceptance. Do not self-trigger it.

## Completion, review and development merge

Coding commits unchanged strategic activation with implementation and creates/reuses one PR.
After local/implementation-head checks it writes immutable report with literal implementation
SHA and SELF, commits only report and pushes. Verify using verify_report.py; then
`oap.py respond --role CODING --identifier ID` with root/runtime sends exact OK after independent
remote publication checks. Report cannot attest its future push or CI. A post-push receipt does.
Then coding starts one control waiter for the next round; current model stops mutations.

Strategy validates report topology/identity and current-head code/tests/docs/review/security/
license/DHA. Required checks all successful; absent/skipped/pending is not a pass. Current-head
change invalidates review. Merge only under delegated development authority, expected-head
guard and permitted merge mode; no admin bypass/auto-merge. Verify actual remote merge commit
and main. Save `oap/reviews/NNN-resolution.json` with decision MERGED, pr, accepted_head,
merge_commit and evidence/timestamps; for ABANDONED include dependency_reassessment and actual
closed unmerged PR. Keep original report PR identities if squash/rebase rewrites main graph.
Record timings. Only then next numeric objective. Same objective corrections use next suffix.
Helpers never themselves merge or create releases.

## Critical judgments and human records

Every order has NONE or APPEND CRIT-NNNN. For APPEND use exact unfenced payload markers from
template, actual existing PR, prior-register and payload SHA256. append_critical.py takes only
the active order/ID, verifies bytes and preserves history. Identical completed append is no-op.
Its parser validates structure, not the five conditions' substantive truth. Strategy owns that.

For externally signed human dispositions, the human configures a trusted signer/public identity
outside the repository. The human signs exact JSON with namespace slaif-oap-dha, without placing
the private key here. verify_human_disposition.py verifies and imports statement/signature;
check_state.py with --runtime verifies all records and reports latest authenticated decision.
Invalid/unconfigured/ambiguous records remain blocking. Only ACCEPTED clears that exact gate;
later DEFERRED/REJECTED/CHANGE REQUIRED blocks again. No automatic deployment authority follows.

## Recovery and stopping

See oap/RECOVERY.md. Sent/consumed receipts are private diagnostic history, not project truth.
An attempted send followed by crash is deliberately not retried automatically; inspect durable
order/report/remote state. Published report + lost response resumes review without code replay.
No report + consumed control resumes same order explicitly after proving old worker stopped.
Terminate only recorded owned waiter PID after checking identity, or deliberately stop its
owned process. No daemon/cron/restart policy is installed. Human quit is respected.
