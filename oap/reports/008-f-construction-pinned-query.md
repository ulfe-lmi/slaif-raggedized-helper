# OAP Coding Report — 008-f

Identifier: 008-f
Result: PARTIAL
Repository: ulfe-lmi/slaif-raggedized-helper
PR number: 10
Branch: oap/008-raw-hybrid-snapshots
Base branch: main
Implementation head SHA: 0e86613a33231537c591b869f1e18144cdbe63a0
Report publication commit: SELF

## Work and scope

Order 008-f (FINAL, AMEND_EXISTING_PR) on base 50a85ac8: repaired the
008-e comment-only E501 lint failure and transferred the reviewed
private completion-locator, construction/publication/selection and
pinned-query joins by byte-exact Git-object copy from prepared SELF
1224dae8 (implementation 78d2598b); no new implementation or source
adaptation. Transcript c52d4fe2 (sole parent 50a85ac8): 14 paths —
unchanged FINAL order (6849d668…b14735), active 008-f+LF, eleven exact
Root records (38,427 B), exact index (3,632 B e54fc23c…59e16c).
Implementation 0e86613a (sole parent transcript): 21 paths — 19 exact
indexed component blobs (129,802 B; 18 NEW plus the existing trace
file changed only in its one overlong docstring line) plus only
docs/retrieval.md and STATUS.md. This report commit changes only this
report. No donor-branch merge/cherry-pick/reset/clean/stash/switch/
rebase/force-push; no 009 extras, private Toy driver, dependency,
workflow, config, law, profile or old-report change; the donor's
unrelated 009 code and obsolete fixture were not copied.

## Acceptance evidence

1. Reconciled at start: unique open PR 10, head branch at 50a85ac8,
   base main 1a8fddf8, mergeable, no auto-merge or reviews. All 19
   blobs byte-verified (SHA-256+size, 129,802 B) against the donor
   SELF and the Root index; 18 NEW absent at base; trace change = the
   single docstring line (E501 101→81 chars); all 14 transcript paths
   hash/size-verified before commit. No mismatch; no Root blocker
   written.
2. Construction join preserves exact bounded DATA serialization, fresh
   source/program coverage, fail-closed ConstructionError (stage/
   attempt flags), one cooperative outer deadline and no automatic
   cleanup or rollback of a published candidate — byte-exact reviewed
   source plus contract docs.
3. Pinned query preserves the borrowed active same-store PinOwner and
   entered ResidentQueryEncoder; provider checked before encode/
   retrieval/return; an affected readable unavailable partition
   refuses BEFORE encode; no current-pointer reacquire, unauthorized
   exposure, owner close or model restart; supplied markers stay
   unverified — all retained byte-exact.
4. Original 008 four criteria remain governing and unchanged by this
   copy (normalization/negation; 60+60/RRF60 deterministic
   identity/cap traces; fail-closed source/vector/ACL/deletion/
   policy/model binding; locked atomic activation with coherent
   retained readers). Existing lower tests plus the two new normal
   integration cases run in the full unchanged CI.
5. docs/retrieval.md and STATUS.md updated: private construction/
   pinned-query joins now described as existing (the private pinned
   query is an actual usable private join; public entrypoint absent);
   stale active-007/current-main-006/client assertions corrected to
   008-f and merged 007 main 1a8fddf8; 007 entries labeled
   historical; 008-e lint failure/later SKIPPED, fixed docstring and
   pending new-head CI recorded; public serving/current principal/
   current policy/evidence-delivery gates and real qualification stay
   open. No invented endpoint, benchmark, model ID or license.
6. One report-head push triggers the complete unchanged five-job
   matrix (all required steps, unit + integration 3.12/3.14); no
   skip, deselection, fallback, continue-on-error, cap, workflow,
   dependency change or old-run retry. Coding publishes and idles;
   Root observes head, all checks and cumulative reviews before any
   protected expected-head development merge.

## Verification

Local static Git/hash/AST/metadata checks only — NO local app import,
test, collection, interpreter/package probe, setup, model, native,
store or scorer process:
- 19/19 indexed blobs byte-exact at donor SELF 1224dae and in the
  committed worktree (129,802 B).
- 11/11 transcript records byte-exact (38,427 B); index 3,632 B
  e54fc23c…; order 6849d668…; active 008-f+LF (6 B).
- Nine Python ASTs identical except docstrings per Root review (78d2);
  first failed lint (two E501) and final pass preserved; trace diff
  vs base = the one docstring line only.
- No dependency/workflow/config change; new modules import only
  existing package layers.

Remote verification (post-push, oap/bin/verify_report.py + gh): remote
branch/PR 10 head = this report commit; first-parent chain
report→0e86613a→c52d4fe2→50a85ac8; report-only diff; transcript and
all 19 blobs byte-verified on remote objects. This report cannot
certify its own future push/CI; a separate receipt and strategic
review record those facts.

## Documentation impact

docs/retrieval.md: 008-f provenance plus actual callable join-layer
section (supplied/controlled distinctions, limits, evidence);
"still absent"/"remaining 008 scope" wording corrected (private joins
no longer claimed absent; public functionality assigned to later
014/operations gates); Evidence records the 008-e failed CI (run
43377547440: both Product jobs lint E501 at the trace fixture
docstring line, later product steps SKIPPED, three OAP jobs success)
and the limited historical V2/V6 component proofs. STATUS.md:
current-state corrections (active 008-f, main 1a8fddf8, client on
008/PR 10), 007 entries historical, 008-f entry added, 008-e entry
superseded in part. ci-proc-observation document and the historical
008-d one-shot UNPROVEN limits preserved; that old harness is never
reused.

## DHA and boundaries

Decision: NONE. Preserved: unrelated files, private config, worktrees,
Qwen3.8/A100Q8/xhigh services and profiles, other panes, the failed
008-e report/run/raw log and all prior immutable reports. No merge,
no auto-merge, no tag/release/deploy, no credential/corpus/network
action, no nested agents, no FIFO reread or duplicate reader.

## Limitations and remaining work

- No local runtime execution; actual combined new-head behavior is
  pending the full unchanged hosted matrix at this report head. The
  008-e head's failed lint/SKIPPED record is preserved, not accepted
  or retried.
- Supplied/controlled encoders and synthetic fixtures only: no real
  BGE, rights, quality, 20k scale, hardware, ICA or full-MVP closure
  claimed. Whole 008 remains PARTIAL; the development merge and next
  scope remain strategy gates.
