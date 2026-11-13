# CI parameter-ID bounds — 008-g

This note records the observed 008-f report-head CI failure, the
test-metadata repair made in objective 008, slice 008-g, and the bounded
local evidence with its full procedural history. It changes no product
behavior, no CI cap and grants no broader test authority.

## Observed failure (preserved, immutable)

At the 008-f report head 5509c6ba, the unchanged normal hosted matrix
ran (run 43383127224). Both Product jobs passed lint/syntax and then
failed in the pytest session finish (cache provider) while writing
`cache/nodeids` with `OSError` errno 27 (file too large):

- Product 3.12 job 131745302976 — FAILED
- Product 3.14 job 131745303383 — FAILED

Unit progress reached 100% before the session-finish failure; no pytest
terminal summary and no integration result exist for the failed runs, and
every later Product step was SKIPPED, not pass. The three OAP jobs
(3.12/3.13/3.14) succeeded. The logs show no failed test assertion: this
is a diagnostic/cache write failure, not a product assertion failure, and
incomplete CI is not full CI. The failure and its raw logs are preserved
unchanged (`oap/reviews/008-g-prior-ci-failure.json`); 008-f is not
marked green retrospectively, and the failed run is not accepted or
retried.

## Mechanism (actual) and inference (unmeasured)

Actual: `test_bad_program_refused` in
`tests/unit/test_raw_snapshot_completion_locator.py` was parametrized
over six byte payloads without explicit pytest IDs. Pytest derives
default IDs from the argument values; for the oversized argument
`b"x" * 16777217` the derived ID serializes the full 16,777,217-character
payload into the node ID (measured locally: max node-ID length
16,777,295 characters). The cache provider writes every collected node ID
to `cache/nodeids` at session finish; the untruncated write of such a
value under a per-file size limit raises errno 27 during
`pytest_sessionfinish` (pytest 8.4.2 `Cache.set` writes without
truncating).

Inference, NOT measured: the CI runner's exact file-size limit value and
whether it was inherited from helper unit setup (e.g. an inherited
RLIMIT_FSIZE) have NOT been measured; no original CI cap value is claimed
or inferred from ID length alone. No CI or product cap was raised or
changed.

## Test-metadata repair (008-g)

Only the `pytest.mark.parametrize` of `test_bad_program_refused` gained
six stable unique short IDs: `empty`, `malformed-json`,
`trailing-newline`, `mutable-bytes`, `bytes-subclass`,
`oversized-program`. All six actual argument expressions are preserved
byte-for-byte (including `b"x" * 16777217`); case cardinality is
unchanged (6); the module AST equals the base after removing the one
`ids` keyword. No payload shrink, skip, deselection, xfail, cache-plugin
disabling, cache clear/retry workaround, timeout or file-size cap
change, and no other test, product, workflow, dependency or law change.

## Local bounded evidence (synthetic, owned infrastructure)

Pinned interpreter
`/tmp/slaif-pinned-query-setup-20261113/venv/bin/python` (Python 3.14.4,
pytest 8.4.2; its editable app origin belongs to another worktree and was
not used — the canonical `src` won via explicit PYTHONPATH, module files
recorded in postflight), repo `.venv` ruff 0.17.4 (SHA-256
`4ef33997b4bb7c5f141527e90b2da0abe918108362ca1b9825c4d13adce0e347`),
GNU time. Each focused child: CPU 10 s / address space 1 GiB / wall 60 s
SIGKILL (5 s grace) / CPU affinity 0 / file-size limit deliberately
lowered to 1 MiB in the child / five thread vars = 1 / closed benign
environment (PATH, HOME, LANG) / bytecode disabled / third-party plugin
autoload disabled (`PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`; the only venv
pytest11 entrypoint is anyio) with the built-in cache provider enabled /
fresh owned 0700 scratch with private TMPDIR and no pre-existing
basetemp/cache children. One bounded launcher/probe (bytes + SHA-256
recorded per attempt) printed only count/max/total node-ID lengths, never
IDs or payloads.

Honest attempt history (all logs preserved; two pre-correction
over-allowance attempts disclosed, none replayed or removed):

1. `A` (07:27, old collect-only): aborted at pytest argument parsing,
   exit 4, before any collection — `--cache-dir` is not a pytest 8.4.2
   CLI flag (`cache_dir` is an INI option); the postflight still recorded
   module provenance. Preserved, not replayed.
2. `A2` (07:30, old collect-only): the one successful old diagnostic.
   argv: `[file, --collect-only, -o addopts=, -o cache_dir=<scratch>/cache,
   -p no:terminal]` — `-o addopts=` for this diagnostic only, so the
   terminal-owned `-q` is not rejected under `no:terminal` (Root
   clarification record), plus the bounded summary hook. Result: exit 0,
   51 collected, max node-ID length 16,777,295, total 16,785,861
   characters. Under `--collect-only` the pytest 8.4.2 cache provider
   skips the `cache/nodeids` write (documented early return), so no cache
   file was created and no errno-27 write was attempted in this mode.
   This measured the actual giant old node ID; it is NOT a measurement of
   the original CI file-size limit and NOT an old cache failure (the
   cache was empty during collect). Expected diagnostic reproduction of
   the metadata, not a pass claim. A2 preceded its Root permission; there
   is no retroactive approval.
3. `B` (07:32, full module, cache enabled): 51 passed in 0.42 s, exit 0;
   session finish and cache write succeeded under the 1 MiB child limit;
   `v/cache/nodeids` 4,601 bytes (51 entries, max node-ID 95 chars).
   Executed before the Root D0 reconciliation record; preserved, not
   replayed.
4. `F` (07:39, full module, cache enabled): the final focused run under
   the Root D0 future permission, unchanged caps and a fresh absent
   scratch. Result: 51 passed in 0.42 s, exit 0; `v/cache/nodeids`
   4,601 bytes (51 entries, max node-ID 95, total 4,293 chars); the real
   oversized argument remains exercised.

Static checks (disposable children, CPU 5 s / AS 256 MiB / wall 30 s /
affinity 0): AST equality after removing the one `ids` keyword; payload
line byte-identical; exactly the six ordered expected unique IDs; no line
over the 100-char lint limit. Two earlier verifier runs failed from
private wrapper/script bugs (recorded and preserved) and are superseded
by the corrected direct-invocation run. One ruff 0.17.4 check (CPU 5 s /
AS 512 MiB / wall 30 s / affinity 0) on the changed unit file only: All
checks passed.

The total is FOUR attempted pytest processes (A usage-fail, A2, B, F),
not two or three; the original two-total allowance was exceeded before
the Root corrections. No further test, collection, lint, setup or probe
is authorized or performed. Private preflight/postflight records (literal
argv/cwd/env, source and tool hashes, caps, split stdout/stderr, GNU
time, exit) are retained on the development host only.

## Limits

All local evidence is synthetic owned-test-infrastructure proof: no keys,
network, GPU, model, store or scorer activity. The 1 MiB file-size limit
is an owned diagnostic bound deliberately lowered in the child, not a
measurement of the original CI ceiling. The unchanged hosted matrix at
the new report head (five jobs, all steps, unit + integration on
3.12/3.14) is the evidence boundary and remains pending; the failed
008-f CI is not accepted. Real qualification remains NOT RUN.
