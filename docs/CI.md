# CI — OAP scaffold plus product foundation job

Objective 000-a established the OAP scaffold coverage; objective 002-a adds a minimal
separate product job. The product job is not hardware or model verification: it runs the
locked lightweight environment, the real product tests (synthetic fixtures only) and the
OAP scaffold checks from a clean checkout. Hardware/model evidence gates remain absent
until their ordered implementation (see TESTING.md T03/T04).

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
- Job `Product tests (Python <version>)` per Python 3.12, 3.14 (fail-fast false),
  20-minute per-job timeout (objective 002-a).

## Steps per job

1. Check required local tools with `command -v` (git, ssh-keygen) so the DHA signature
   tests cannot silently skip; ssh-keygen behavior itself is exercised by the suite.
2. Python syntax check: `python -m compileall -q oap tests`.
3. OAP test suite: `python -m unittest discover -s tests/oap -v`.
4. Governance check: `python oap/bin/check_state.py --repo-root "$GITHUB_WORKSPACE"`.

No product requirements are installed; tests use synthetic fixtures only (no keys, network
services, GPU, tmux or model downloads). The fixture transcript is seeded deterministically,
so the suite passes from an active checkout as well as a clean clone.

## Product job steps (002-a)

1. Check out with `persist-credentials: false`; set up the matrix Python.
2. Overwrite `.python-version` with the matrix version (the committed file is the
   development default) and install `uv==0.12.5` from the standard registry.
3. `uv sync --locked` installs the locked lightweight environment (no heavy ML stack).
4. `uv run ruff check src tests/unit tests/integration` lints the product scope (the
   OAP scaffold is governance-owned compact style, out of product lint scope).
5. `python -m compileall -q oap tests` syntax check.
6. `uv run pytest tests/unit -q` runs the real product tests; pytest exits 5 on empty
   discovery, so the suite cannot be falsely green.
7. `uv run pytest tests/integration -q` runs the real controlled HTTP/SSE behavior
   tests (objective 003: 003-b transport/gateway, 003-c/d protocol validation,
   003-e native direct adapter) against owned loopback fixtures with synthetic
   keys (see TESTING.md T06 and docs/generator-contract.md); same clean locked
   install.
8. The existing OAP test suite and governance check run on the same clean checkout.
9. `uv run raggedized --help` (offline) and `raggedized doctor` on the shipped example:
   the step asserts exit code 1, `config: valid`, `readiness: not_ready` and the
   `MODEL_UNQUALIFIED` code in the machine-readable output (honest unqualified examples).

## Local parity

The same commands reproduce CI from any checkout (active or inactive):

```sh
python3 -m unittest discover -s tests/oap -v
python3 oap/bin/check_state.py --repo-root .

# product foundation (002-a)
uv sync --locked
uv run ruff check src tests/unit tests/integration
uv run pytest tests/unit -q
uv run pytest tests/integration -q
uv run raggedized doctor --config config/examples/example-config.json
```

## Results and gates

Runs appear in the repository Actions tab (`gh run list`, `gh pr checks`). A green
implementation-head run is recorded in the round report; strategy separately observes the
final report-head run, so the report never certifies its own future checks. Zero passing
checks never means product verification has passed. The product job proves the foundation
package, its tests and the OAP checks install and run from a locked clean checkout; it does
not prove live model, hardware or gateway readiness. The integration suite proves the
bounded transport/gateway HTTP and SSE behavior described in
docs/generator-contract.md; native direct-adapter and qualification-probe evidence
(the remainder of objective 003) stays NOT RUN / pending.
