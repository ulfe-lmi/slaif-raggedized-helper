# OAP Work Order — 000-a

Status: FINAL
Identifier: 000-a
PR mode: CREATE_NEW_PR
Branch: oap/000-bootstrap-governance-ci
Base commit: 64b2e18d9d58b3073127043937a466d9ed8f266a
PR number: NEW
Expected active: NONE
Provenance: H current user requests enable CI testing for the repo and use gh; A37 A38 A40; initial objective 000 bootstrap/CI proposal
Architecture SHA256: 48809e248ef226607a2bec27de99b995abe15cc2094dd37b819c0d2c065748fc
Governance SHA256: bbf017ad59d91ba6e180345220ae579af9f1d9b7fc87c0ef968900ba9ef1736d

## Objective

Enable useful GitHub Actions CI for this repository using gh for GitHub operations. Publish
the existing reviewed scaffold because its tests/governance are the CI subject and currently
exist only locally. Add a bounded workflow that runs the OAP test suite and governance checks
on pull requests, pushes to main, and manual workflow_dispatch. This authorization is scoped
to objective 000 and corrections. Do not begin objective 001 or RAG product implementation.

## Dependencies and current state

Strategic read-only preflight on 2026-11-01: canonical ulfe-lmi/slaif-raggedized-helper, main at
the literal base above; no PRs, workflows or preceding active objective. Actions already enabled
with allowed_actions=all. Existing main ruleset 26322045 (main protection) is active and denies
deletion/non-fast-forward; no required check or review rule was returned. Preserve these rules.
All merge methods are enabled. There is no existing merge-triggered deployment workflow.

Shared worktree on main has the authorized scaffold: modified README.md/.gitignore and new
governance/docs/oap/tests from bootstrap. These files are intended publication scope, not trash
to reset/stash. LICENSE is unchanged. Bootstrap receipt is historical and must not be rewritten
to claim it originally activated/published anything. Strategic sources and private runtime live
outside Git. Coding pane %30/current root and selected model remain unchanged. Exact existing
source bytes and governance manifest passed bootstrap verification; local host Python is 3.14.4.

Use gh to fetch/reconcile authoritative repository/PR/actions state. Create the branch from
verified base while preserving all intended scaffold bytes. Do not force/reset/clean/stash.

## Allowed paths and scope

Commit the existing scaffold within .gitignore, README.md, AGENTS.md, PLAN.md, ARCHITECTURE.md,
ARCHITECTURE-for-agents.md, CRITICAL.md, SOURCE-MAP.md, SECURITY.md, TESTING.md, STATUS.md,
OAP-COMMUNICATION-coding-agent.md, docs/, oap/ and tests/oap/. Preserve immutable user source
copies and full architecture. New .github/workflows/oap.yml is the workflow. No real credentials,
private runtime, .codex, .oap-state, corpora, models, archives or private logs belong in Git.

Changes beyond already prepared scaffold are limited to the new CI workflow, genuinely needed
test fixture isolation/portability fixes, README/TESTING/STATUS and a concise docs/CI.md, and
coherent governance context measurements/manifest hashes for authorized changed sources.
Fix a concrete helper CI issue only if necessary and tightly scoped; report it and its evidence.
No invented workflow-regex test that merely repeats the YAML; verify actual GitHub execution.

Workflow contract:
- Name: CI; Ubuntu GitHub-hosted runner; Python matrix 3.12, 3.13, 3.14.
- Stable job names OAP tests (Python VERSION); per-job timeout 10 minutes; fail-fast false.
- Triggers pull_request targeting main, push main, workflow_dispatch; no path filter that skips
  required checks. Use concurrency to cancel obsolete runs on the same PR/ref.
- Least privilege contents: read, no secrets, deployment/release, pull_request_target, self-hosted
  runners, model/network inference or dependency downloading beyond official action/tool setup.
- Full immutable action SHA pins verified with gh by strategy:
  actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 (v7.0.1)
  actions/setup-python@6d4fd22b20465ccc0f7354476588e8df7c9ca0e0 (v7.1.0).
  Disable persisted checkout credentials. Verify exact pinned action requirements if necessary.
- Check required local tools (git and ssh-keygen) so signature tests cannot silently skip;
  run python -m unittest discover -s tests/oap -v and python oap/bin/check_state.py --repo-root
  "$GITHUB_WORKSPACE". Python syntax checks may be included; no product requirements are installed.

Known pre-activation test concern: Harness.setUp copies the source tree wholesale and currently
assumes its copy is inactive with an empty CRITICAL register. The real source now contains an
active order, and future reports/adjudications would also contaminate fixtures. Isolate ONLY
the temporary fixture's mutable OAP transcript/register/state, using a deterministic synthetic
empty seed. Preserve the real worktree/order/active/register. Cover the meaningful isolation
boundary and verify the suite in this actual active worktree, not an artificially inactive
live checkout. Never delete actual activation to make CI pass.

## Non-goals

No product code, GPU/model download/inference, service change, gate relaxation, branch-rule
change, agents/model/profile switch, external deployment, release/tag, auto-merge or coding
merge. No next numeric objective. Do not edit original source files or the activated order.
Do not refresh historical receipts/source snapshots to make old statements appear current.

## Acceptance criteria

1. Official pinned workflow is valid and runs three Python jobs on the objective PR; tests and
   governance check pass on the actual final report head. Strategy observes the final-head run.
2. Existing scaffold and exact order/active are published in one unique objective PR. Source
   copies/full architecture remain byte-identical; no private/unintended artifacts are committed.
3. Tests pass from an active checkout and a clean clone without product credentials, services,
   GPUs or downloads. Fixture mutation never touches live transcript/CRITICAL or another project.
4. README/TESTING/STATUS/CI docs distinguish current CI from future product/hardware evidence.
   Updated governance manifest/context byte totals match all authorized modified sources; exact
   model token counts remain UNMEASURED. The old order source hash remains immutable history.
5. CI has read-only permissions, no deployment side effects and no silent skipped signature
   tests. Required runner tools are checked explicitly. Existing protection rules remain intact.

## Verification and negative evidence

Run the focused OAP suite locally, check_state using the real repo root and active order, and
git diff --check including intended new files. Exercise fixture isolation against active order,
report/register content in owned temporary fixtures, preserving real state byte-for-byte.
After pushing, use gh pr checks/run list/run view to inspect remote jobs; repair concrete in-scope
failures before final report. Report local Python vs remote matrix accurately. Pending final
report-head checks cannot be reported as passed before they run; strategy verifies those later.
No full product or hardware suite exists yet. Verify a clean clone/temporary checkout of the
published implementation with the same test/check commands. Do not enter real project FIFOs
except the protocol's one response and later idle control waiter.

## Documentation

Document triggers, Python matrix, exact local commands, read-only/no-secret behavior, where to
find Actions results, and that CI currently covers OAP scaffolding only. Mark the initial
scaffold publication/CI work in STATUS without claiming merged/deployed prematurely. Keep
bootstrap receipts historical. Regenerate affected manifest hashes and context byte totals
from actual files; do not weaken identity checks to obtain green CI.

## Runtime and protected resources

Explicit authority: the user's current request enables CI testing using gh. It authorizes this
bounded GitHub publication and ordinary development PR workflow; strategy owns reviewed merge.
Live product runtime authority: NONE. Preserve gateway/Qwen projects/panes/FIFOs/services, all
human client settings, credentials and ignored state. All ordinary tests use disposable fixtures.
Both source and staged baseline hashes are available from source lock/manifest for review.

## Deferred human adjudication
- Decision: NONE

## Publication and report

Commit/push intended scaffold, CI and test/docs corrections with unchanged strategic order and
oap/active. Create exactly one PR via gh with title "Enable OAP scaffold CI" and a body describing
the actual scope and verification. Preserve one objective/PR on interruption or correction.
After implementation checks and safe repairs, publish one immutable report with full literal
implementation SHA and Report publication commit: SELF. Final commit changes ONLY the report,
first parent is implementation. Push, verify using verify_report.py, then send response OK using
send-response.sh --identifier 000-a. Coding never merges. Return to one external control waiter;
do not self-assign more work. Strategy reviews and merges only after exact final-head gates.
