# CI — OAP scaffold only

Objective 000-a. This workflow exercises the OAP scaffold (governance identity, protocol
harness, helper CLI) only. It is not product, hardware or model verification; those evidence
gates remain absent until their ordered implementation (see TESTING.md T03/T04).

## Definition

- File: `.github/workflows/oap.yml`; workflow name: `CI`.
- Runner: `ubuntu-latest` (GitHub-hosted only; no self-hosted runners, no secrets).
- Permissions: `contents: read` only; checkout runs with `persist-credentials: false`.
- Actions pinned by immutable commit SHA (tags verified by strategy with gh):
  - actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 (v7.0.1)
  - actions/setup-python@6d4fd22b20465ccc0f7354476588e8df7c9ca0e0 (v7.1.0)
- Triggers: pull_request targeting main, push to main, workflow_dispatch. No path filters.
- Concurrency group `ci-<workflow>-<ref>` with cancel-in-progress for obsolete runs.
- Job `OAP tests (Python <version>)` per Python 3.12, 3.13, 3.14 (fail-fast false),
  10-minute per-job timeout.

## Steps per job

1. Check required local tools with `command -v` (git, ssh-keygen) so the DHA signature
   tests cannot silently skip; ssh-keygen behavior itself is exercised by the suite.
2. Python syntax check: `python -m compileall -q oap tests`.
3. OAP test suite: `python -m unittest discover -s tests/oap -v`.
4. Governance check: `python oap/bin/check_state.py --repo-root "$GITHUB_WORKSPACE"`.

No product requirements are installed; tests use synthetic fixtures only (no keys, network
services, GPU, tmux or model downloads). The fixture transcript is seeded deterministically,
so the suite passes from an active checkout as well as a clean clone.

## Local parity

The same commands reproduce CI from any checkout (active or inactive):

```sh
python3 -m unittest discover -s tests/oap -v
python3 oap/bin/check_state.py --repo-root .
```

## Results and gates

Runs appear in the repository Actions tab (`gh run list`, `gh pr checks`). A green
implementation-head run is recorded in the round report; strategy separately observes the
final report-head run, so the report never certifies its own future checks. Zero passing
checks never means product verification has passed.
