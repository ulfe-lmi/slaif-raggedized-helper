# OAP Coding Report — 000-a

Identifier: 000-a
Result: COMPLETE
Repository: ulfe-lmi/slaif-raggedized-helper
PR number: 1
Branch: oap/000-bootstrap-governance-ci
Base branch: main
Implementation head SHA: 5afd2a239b50c07f5359e749bfcc6e8681c20b9a
Report publication commit: SELF

## Work and scope

Executed the FINAL active order 000-a (oap/orders/000-a-bootstrap-governance-ci.md,
PR mode CREATE_NEW_PR, expected active NONE, base 64b2e18d9d58b3073127043937a466d9ed8f266a).
One implementation commit 5afd2a239b50c07f5359e749bfcc6e8681c20b9a on branch
oap/000-bootstrap-governance-ci, created from verified remote main 64b2e18; PR #1 is the
single objective PR. The commit publishes the reviewed bootstrap scaffold (90 files)
together with the activated order and oap/active bytes unchanged, adds the OAP scaffold CI
workflow, and applies the authorized test/docs/governance updates:

- .github/workflows/oap.yml (new): workflow CI, ubuntu-latest, Python 3.12/3.13/3.14 matrix
  (fail-fast false, 10-minute job timeout), triggers pull_request to main, push to main and
  workflow_dispatch, concurrency ci-<workflow>-<ref> with cancel-in-progress, top-level
  permissions contents: read, no secrets, actions pinned to immutable commit SHAs
  (actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 v7.0.1,
  actions/setup-python@6d4fd22b20465ccc0f7354476588e8df7c9ca0e0 v7.1.0) with
  persist-credentials: false; steps: git/ssh-keygen availability precheck,
  python -m compileall -q oap tests, python -m unittest discover -s tests/oap -v,
  python oap/bin/check_state.py --repo-root "$GITHUB_WORKSPACE".
- tests/oap/test_harness.py: setUp now isolates the fixture's mutable OAP
  transcript/register/state (oap/active, oap/orders/*.md, oap/reports/*.md,
  oap/adjudications, CRITICAL.md) with a deterministic synthetic empty seed, so the suite
  passes from an active checkout; new test
  test_fixture_transcript_isolated_and_live_preserved asserts the seeded boundary and that
  fixture mutations (activate, critical append, report write) leave the live transcript
  byte-for-byte unchanged.
- oap/governance/MANIFEST.json: hashes refreshed for the three authorized changed sources
  (TESTING.md, oap/governance/CONTEXT-BUDGET.md, tests/oap/test_harness.py); all 65 other
  manifest entries verified byte-identical before commit. oap/governance/CONTEXT-BUDGET.md:
  measured rows and declared total regenerated (27131 bytes, ceiling 50000).
- README.md, TESTING.md, STATUS.md updated; docs/CI.md added.
- .gitignore: OAP/private runtime and corpus artifact patterns (unchanged from scaffold).

## Acceptance evidence

1. Workflow valid and three Python jobs on the objective PR: remote run 41339670392 at
   implementation head 5afd2a2 — jobs OAP tests (Python 3.12/3.13/3.14) all success; every
   step (checkout, setup, tool check, syntax, suite, governance) concluded success;
   "Ran 40 tests ... OK" in each job; check_state passed on the CI checkout. The final
   report-head run is triggered by this report commit and is pending at report time;
   strategy observes it. The report does not certify that future run.
2. Scaffold and exact order/active published in one unique PR: PR #1 is the only 000 PR
   (gh pr list); oap/orders/000-a-bootstrap-governance-ci.md and oap/active committed
   byte-identical to the strategic publication (pre-push sha256 0d71ecbc... and
   a0c3e485... respectively, unchanged by this work); all 90 staged files match the
   allowed paths; .oap-state/, __pycache__/, .codex/, runtime.json are gitignored and
   absent from the commit (git check-ignore verified); governance manifest validates every
   covered source byte-for-byte at the implementation head.
3. Active checkout and clean clone: 40/40 tests OK locally in the active worktree (Python
   3.14.4) and in a clean clone of the published 5afd2a2 without credentials, services,
   GPUs or downloads; 40/40 on all three remote matrix versions; fixture containment is
   asserted by the new test (live transcript snapshot equal before/after fixture mutation);
   live oap/active, CRITICAL.md and order hashes verified unchanged after the suite runs.
4. Docs and governance: docs/CI.md, README, TESTING and STATUS state CI covers the OAP
   scaffold only and that product/hardware evidence is absent; manifest/context totals
   (27131 <= 50000) regenerated from actual files; exact model token counts remain
   UNMEASURED; the order's recorded Architecture/Governance SHAs are immutable history
   (activation_matches_current_governance is therefore false by design, an informational
   field that check_state does not fail on).
5. Read-only CI and intact rules: workflow uses contents: read only, no secrets, no
   deployment, no pull_request_target, GitHub-hosted runners only; runner log confirms
   "Contents: read / Metadata: read"; the DHA signature test ran and passed on the runner
   (test_human_signature_and_latest_disposition_gates ... ok, not skipped); git/ssh-keygen
   availability is checked explicitly in every job; ruleset 26322045 "main protection"
   (deletion, non_fast_forward) re-verified after PR creation; Actions enabled with
   allowed_actions=all and no required checks or review rules, all preserved.

## Verification

Local, implementation head, active worktree (Python 3.14.4, no network beyond gh):
- python3 -m unittest discover -s tests/oap -v -> Ran 40 tests, OK (pre-fix baseline on
  this active worktree: 39 tests, 2 failures + 5 errors, all from live-transcript
  contamination of fixtures, exactly the order's pre-activation concern).
- python3 oap/bin/check_state.py --repo-root . -> state ACTIVE, active 000-a, order
  validated, manifest 89fbff0742ff0ffcc26f81d9391a8a09ef349714cde74d012b6e7fafb4732bcd,
  declared_context_bytes 27131, exact_model_tokens UNMEASURED, critical {}.
- git diff --check -> clean; staged file list inspected (90 files, no private artifacts).
Remote (live GitHub, authorized gh use):
- gh pr view 1 -> OPEN, MERGEABLE, head 5afd2a239b50c07f5359e749bfcc6e8681c20b9a,
  base main, branch oap/000-bootstrap-governance-ci.
- gh run list/view 41339670392 (pull_request) -> success; per-job step conclusions all
  success; tool check executed ssh-keygen availability only (availability gate
  command -v; no ssh-keygen --help, which exits 1 on OpenSSH and would fail every job —
  corrected before publication per strategic in-scope review observation).
- Clean clone of 5afd2a2 (temporary, removed after use): 40/40 OK and check_state ACTIVE
  with the same manifest identity.
Mock/live distinction: all suite tests use synthetic fixtures (fake gh/tmux/FIFO/Git
repositories); live operations were limited to authorized gh reads, the branch push, PR
creation and the resulting GitHub Actions execution. No model, GPU, gateway, corpus or
product network activity.

## Documentation impact

README.md (CI scope pointer), TESTING.md T05 (CI exists; OAP-scaffold scope only; product
CI still absent), STATUS.md (000-a implemented on open PR; not merged/deployed; live state
queried on GitHub), docs/CI.md (triggers, matrix, pins, steps, local parity, results and
gate boundaries), oap/governance/CONTEXT-BUDGET.md (measured totals). Bootstrap receipts
left historical; no historical statement refreshed.

## DHA and boundaries

Order DHA: Decision NONE; no critical append performed or candidate reported. The
strategic in-scope observation about ssh-keygen --help was handled as a correction under
existing acceptance criterion 5 and is recorded here as evidence. Preserved: gateway/Qwen
projects, panes, FIFOs and services, strategic sources, private runtime, .oap-state,
credentials, tmux client/model settings, bootstrap receipts, and the activated order/
active bytes. No merge, no auto-merge, no tag/release/deploy, no next objective, no
agent/model/profile change, no nested agents.

## Limitations and remaining work

- The CI run at this report head is pending at report time; strategy observes the exact
  final-head run separately (per protocol, this report certifies only checks already
  observed at the implementation head).
- Local verification used Python 3.14.4; the remote matrix covers 3.12/3.13/3.14.
- CI exercises the OAP scaffold only; product, hardware and model evidence remain absent
  until their ordered objectives.
- activation_matches_current_governance is false by design (order's immutable governance
  SHA vs updated manifest); review against the accepted base, no rewrite of the order.
- No product requirements are installed in CI; the Python syntax check covers oap/ and
  tests/ only.
