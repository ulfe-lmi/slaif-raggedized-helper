# OAP Coding Report — 009-t

Identifier: 009-t
Result: COMPLETE
Repository: ulfe-lmi/slaif-raggedized-helper
PR number: 11
Branch: oap/009-evaluation-baseline
Base branch: main
Implementation head SHA: e420d7c16ac14ea96dc46ba3e9e10cc7a1c93240
Report publication commit: SELF

## Work and scope

Order `oap/orders/009-t-pure-policy-component-transfer.md` (Status: FINAL,
PR mode AMEND_EXISTING_PR, Decision: NONE) at round base
`d731dea7f5aad7f55b96386c869795ddba913fe9` (the verified 009-s
report-only head). Objective: transfer the exact accepted typed
supplied-policy declaration, canonical wire reader, selected-view
record and pinned-membership eligibility components, retaining their
reviewed unit contracts and immutable provenance on PR 11.

History pushed in this round (no force push, no merge, one PR):

1. `3cbb4e05568e9fb2bc5e2b3d2017857bcf1e5736` (parent: round base)
   — exact Root transcript: `oap/active` (`009-t` + LF),
   `oap/orders/009-t-pure-policy-component-transfer.md`,
   `oap/reviews/009-t-transfer-index.json` (SHA-256
   `9f8a3e9a3245d213a158004bb9aa64f1dd2fc3d546d9d31438a69dc14ea52460`),
   `oap/reviews/009-t-prior-resolution.json` (SHA-256
   `43c7a09aecaf56054c93fc1988d893b9f15819783ba06914f78a8b3dffb57689`).
2. `e420d7c16ac14ea96dc46ba3e9e10cc7a1c93240` (parent: 1) —
   implementation: the 16 indexed payload paths, the four indexed
   archival report destinations, `STATUS.md` and `docs/evaluation.md`
   (22 paths total).
3. SELF — this report only; first parent is the implementation head.

## Acceptance evidence

1. Round-base and GitHub reconciliation. Local branch head and remote
   `oap/009-evaluation-baseline` were exactly `d731dea7`; live `main`
   was exactly `5a7b41cc512cf883b5b2cb92d87554b4d24e685b`. GitHub
   shows exactly one open non-draft PR: #11 on
   `oap/009-evaluation-baseline` → `main`. The working tree before
   this round contained only the Root activation changes (`oap/active`
   modified, the new order file untracked); no extra changes, unknown
   targets or missing source objects were found. `oap/active` bytes
   are exactly `009-t` + LF; the order file is byte-identical to the
   strategic workorder copy; both strategic files match their ordered
   SHA-256. The prior resolution's 009-s report bytes at the round
   base match its `report_sha256` (`f8a74acc…`) and its receipt
   matches `response_consumed_sha256`; the terminal review
   `audit/009-s-check/Root-terminal-review.json` matches
   `d8a362ce58f53bc2febbcfff6c636e712295599db73b1bd2da8fcf7703d1af9f`.
   009-s integrated CI evidence (unchanged, from the prior resolution
   and order): run 44711903559 attempt 1 passed all five jobs and all
   steps; both Product legs passed the ordered 2,731 units (1,421 in
   A, 1,310 in B) plus the independent full integration; the earlier
   SIGKILL cause remains unproven.
2. Indexed object verification. Every one of the 16 payload paths and
   4 archival report blobs was verified from its exact indexed commit
   (mode, size, SHA-256, Git blob OID); all four lane receipts match
   their ordered SHA-256; each lane's implementation commit has its
   lane base as sole parent and each original report-only SELF commit
   has its implementation as sole parent and touches exactly its one
   report path. All three inherited dependency blobs
   (`provenance_records`, `raw_snapshot_membership`,
   `qualification/parity_io`) are byte-identical at the round base.
   All 16 new source paths and 4 archive destinations were absent at
   the round base. The 20 objects were copied byte-exact (historical
   SELF markers in the archival reports preserved) and mode (0644),
   size, SHA-256 and blob OID were verified at the receiving paths
   before commit and again at the actual implementation head
   `e420d7c1` (20/20 match; inherited blobs and the 009-s report blob
   unchanged at the implementation head).
3. Local proofs (all synthetic, offline, locked .venv, fresh private
   0700 scratch, `PYTHONDONTWRITEBYTECODE=1`,
   `OPENBLAS_NUM_THREADS=1`, each invocation bounded by
   `timeout -k 5 120 prlimit --cpu=60 --as=1073741824`, private
   `--basetemp`, cacheprovider disabled; one-thread CPU affinity was
   added so the ruff worker pool fits the ordered AS cap — a setup
   accommodation, not a limit increase):
   - One targeted ruff check on the eight copied Python files
     (`supplied_policy.py`, `supplied_policy_wire.py`,
     `policy_selection.py`, `supplied_policy_eligibility.py`,
     `test_supplied_policy.py`, `test_supplied_policy_wire.py`,
     `test_policy_selection.py`, `test_supplied_policy_eligibility.py`):
     exit 0, "All checks passed!" (the first default-parallel attempt
     crashed before checking files in ruff's own rayon pool setup —
     `ThreadPoolBuildError WouldBlock` under the 1 GiB AS cap — and
     was re-run under the identical cap with the affinity
     accommodation; no file was modified).
   - One selected pytest invocation of all four new default unit
     modules: exit 0, "collected 284 items … 284 passed in 9.49 s",
     exactly the expected 284 (124 typed, 95 wire, 47 selection, 18
     eligibility).
   - One bounded local origin check: every imported product module
     (the four new plus the three inherited dependencies) resolves to
     the canonical repository `src/` path with the exact indexed
     blob SHA-256/size.
   The indexed artifact bytes are immutable for this transfer; no
   failure required a fix, so no further tests or pushes were needed
   locally.
4. Git scope. Exactly four Root transcript paths, the
   implementation-only 22-path scope above, then this one report-only
   commit naming the implementation as its sole first parent. Prior
   report bytes, the ordered unit process shape and all earlier tests
   are unchanged (verified at the implementation head). No old test
   changes. Expected counts at the new report head (expected until
   measured): Group A 1,421, Group B 1,594, total 3,015, plus the
   separate integration and all unchanged required jobs/steps; 009
   stays PARTIAL with baseline NOT_RUN.

## Verification

Commands and outcomes are the exact bounded invocations listed in
acceptance item 3 (raw streams preserved in the private 0700 scratch).
All product test evidence is synthetic/offline: the four unit suites
exercise owned fixtures and supplied bytes only; no network, keys,
GPU, model download or live route. The transferred primitives hash
only explicitly supplied bytes and perform no I/O, configuration,
model/provider work or credential acquisition. The fresh full hosted
comparison (both Product legs plus all OAP jobs) at this exact report
head is PENDING at report authoring; this report does not certify its
own push or that CI, and Root owns the fresh CI and terminal review.

## Documentation impact

`STATUS.md`: current slice advanced 009-s → 009-t and one cumulative
009-t entry added (four component scopes, 009-s exact integrated CI
evidence, preserved original SELF provenance, actual local 009-t
proof, pending exact-head CI, supplied-policy limit); all historical
sections preserved. `docs/evaluation.md`: new 009-t section near the
preserved 009-s section with the same content. The supplied-policy
limit is stated without implying that a protected policy service,
live credentials, model dispatch or real representative held-out
qualification exists.

## DHA and boundaries

Decision: NONE. No critical entry appended or modified. Preserved:
all product source/tests/workflow outside the 22-path scope, the
009-s CI supervisor, lock/environment, package metadata, earlier
reports, governance, the critical register, unrelated worktrees and
state. No policy capture, authenticated operator policy, actual
pin/catalog, model-access or source-rights decisions, retrieval,
dispatch, delivery or release work. No branch history import,
cherry-pick, new PR, force push or merge; PR 11 only. No package
installation; no product service, real user/corpus data, protected
policy, credentials, models or GPU operations; no external write
beyond the one ordinary push to the existing branch.

## Limitations and remaining work

- The expected 3,015-unit counts (1,421 + 1,594) are expectations,
  not measurements; the fresh full CI at this report head is pending.
- Local proof covered the ordered targeted ruff check, the one
  bounded pytest invocation and the bounded origin check only; the
  local full suite was not run (not ordered).
- The transferred components are supplied-data primitives: no
  protected policy service, current-policy verification, live
  credentials, model dispatch or representative held-out
  qualification exists. Baseline NOT_RUN; whole 009 PARTIAL.
