# OAP Coding Report — 008-g

Identifier: 008-g
Result: PARTIAL
Repository: ulfe-lmi/slaif-raggedized-helper
PR number: 10
Branch: oap/008-raw-hybrid-snapshots
Base branch: main
Implementation head SHA: b7e9c5fe323396755a91fd1d0c153d17b0d4739f
Report publication commit: SELF

## Work and scope

Order 008-g (FINAL, AMEND_EXISTING_PR) on base 5509c6ba: bound the
diagnostic parameter IDs of the completion-locator invalid-program tests
without reducing payloads or coverage; record the failed 008-f
report-head CI. Transcript 7632109f (sole parent 5509c6ba): 6 paths —
unchanged FINAL order (9,647 B d3f220b3…), active 008-g+LF (6 B), three
exact Root records (3,722 B), exact index (1,100 B a2eb1596…).
Implementation b7e9c5fe (sole parent transcript): 4 paths — the test
file (ONLY test_bad_program_refused parametrize gained six explicit
short IDs: empty, malformed-json, trailing-newline, mutable-bytes,
bytes-subclass, oversized-program; all six payload expressions
byte-identical including b"x" * 16777217; cardinality 6),
docs/ci-parameter-ids.md (new), docs/retrieval.md, STATUS.md. This
report commit changes only this report. No merge/cherry-pick/reset/
clean/stash/switch/rebase/force push; no product code, helper limit,
dependency, workflow, config, law, profile, old-report or other-test
change.

## Acceptance evidence

1. Reconciled at start: unique open PR 10 (head 5509c6ba, base main
   1a8fddf8, mergeable, no auto-merge); 008-f head CI run 43383127224
   terminal-failed exactly as ordered (both Product jobs; three OAP
   jobs success). Order/active bytes, three Root records and index
   byte-verified (SHA-256+size) before the transcript commit. Only the
   six new explicit IDs alter test metadata: after removing the one ids
   keyword the module AST equals base exactly; payload line and all
   six case expressions byte-identical (cardinality 6); no suppressed
   error, no product semantics change.
2. Old diagnostic (bounded, pre-edit source): ONE collect-only child
   (CPU 10 s/AS 1 GiB/wall 60 s/affinity 0/FSIZE 1 MiB/five thread
   vars=1/closed env/bytecode + third-party plugin autoload disabled,
   built-in cache provider enabled/fresh 0700 scratch/private TMPDIR),
   `-p no:terminal` + `-o addopts=` (terminal-owned -q not inherited,
   per Root clarification) + bounded summary hook printing only
   count/max/total. Result: exit 0, 51 collected, max node-ID
   16,777,295 chars (serialized oversized payload), total 16,785,861;
   under --collect-only pytest 8.4.2 skips the cache/nodeids write
   (documented early return), so no cache file, no error — expected
   diagnostic reproduction of the metadata, not a pass. The original CI
   file-size limit was NOT measured and is not claimed.
3. Final focused run (bounded, post-edit source, D0-permitted): the
   ENTIRE unchanged locator unit module, cache provider ENABLED, normal
   config/cache semantics, unchanged caps, fresh absent scratch.
   Result: 51 passed in 0.42 s, exit 0; sessionfinish and cache write
   succeeded under the 1 MiB child limit; cache/v/cache/nodeids 4,601 B
   (51 entries, max node-ID 95, total 4,293 chars); the real oversized
   argument remains exercised. Local diagnostic regression proof, not
   full CI acceptance or model evidence.
4. docs/ci-parameter-ids.md records the actual failure, mechanism vs
   inference, exact local commands/caps/source identities/counts/cache
   bytes, old/new outcomes and the full four-attempt history;
   docs/retrieval.md and STATUS.md record the failed 008-f head CI
   (run 43383127224: both Product jobs passed lint/syntax, then failed
   in pytest sessionfinish writing cache/nodeids, OSError errno 27,
   after unit progress 100%; no failed assertion in the logs; later
   product steps SKIPPED; OAP jobs success) and pending new-head CI;
   immutable reports and the old 8d UNPROVEN evidence untouched.
5. One final report-head push triggers the complete unchanged five-job
   CI (all steps, unit + integration 3.12/3.14 plus three OAP jobs).
   Missing/pending/skipped/cancelled/failed is not green; Root
   independently reviews the exact head and all required jobs before
   acceptance/merge. No old-run retry.

## Verification

Local bounded evidence only, no broad suite.
- Static (children CPU 5 s/AS 256 MiB/wall 30 s/affinity 0): AST
  equality after ids removal; payload line byte-identical; exactly the
  six ordered expected unique IDs; no line over the 100-char lint
  limit. Two earlier private verifier runs failed from wrapper/script
  bugs (recorded, preserved, superseded by the corrected direct
  invocation).
- Ruff 0.17.4 (SHA-256 4ef33997…; CPU 5 s/AS 512 MiB/wall 30 s/
  affinity 0) on the changed unit file only: All checks passed.
- Honest attempt history (all logs preserved; no replay, no removal):
  FOUR attempted pytest processes — A (usage-fail exit 4 before
  collection: --cache-dir is not a pytest 8.4.2 CLI flag), A2 (old
  collect success; preceded its Root permission; no retroactive
  approval), B (pre-correction full run, 51 passed, cache 4,601 B), F
  (D0-permitted final run, 51 passed, cache 4,601 B). The original
  two-total allowance was exceeded before the Root corrections; no
  further runtime is authorized or performed.
- Pinned /tmp/slaif-pinned-query-setup-20261113/venv/bin/python
  (Python 3.14.4, pytest 8.4.2; its editable app origin belongs to
  another worktree and was not used — canonical src won via explicit
  PYTHONPATH; module files recorded in postflight). Literal argv/cwd/
  env, source and tool hashes, caps, split stdout/stderr, GNU time and
  exit recorded per attempt on the development host only.

Remote verification (post-push, oap/bin/verify_report.py + gh): remote
branch/PR 10 head = this report commit; first-parent chain
report→b7e9c5fe→7632109f→5509c6ba; report-only diff; transcript bytes
re-verified on the remote object. This report cannot certify its own
future push/CI; a separate receipt and strategic review record those
facts.

## Documentation impact

docs/ci-parameter-ids.md (new): observed 008-f CI failure, mechanism
(actual) vs inference (unmeasured CI cap), the IDs-only repair, bounded
local evidence with full procedural history, and limits.
docs/retrieval.md: title + Evidence current bullet (008-g round; 008-f
head CI terminal-failed and preserved; pending new-head CI). STATUS.md:
current-state slice 008-g and a 008-g round entry. No invented
benchmark, endpoint, license or readiness claim; mock/synthetic and
real-route distinctions preserved.

## DHA and boundaries

Decision: NONE. Preserved: unrelated files, private config, worktrees,
the failed 008-f report/run/raw log, all prior immutable reports, the
old 8d UNPROVEN evidence, and all attempt logs (A/A2/B/F, D verifier
failures, C ruff). No merge, no auto-merge, no tag/release/deploy, no
credential/corpus/network action, no nested agents, no FIFO reread or
duplicate reader, no model/profile change.

## Limitations and remaining work

- The exact original CI file-size limit value is unknown (inherited
  RLIMIT_FSIZE remains an unverified inference); the local 1 MiB bound
  is an owned diagnostic limit, not a CI-ceiling measurement.
- Local proof is synthetic owned-test-infrastructure (four disclosed
  attempts); whole 008 remains PARTIAL until the unchanged hosted
  matrix at this report head passes and Root independently reviews the
  exact head. Real qualification (BGE/rights/quality/scale/hardware)
  remains NOT RUN; the 008 four criteria and public 014 gate separation
  stay intact.
