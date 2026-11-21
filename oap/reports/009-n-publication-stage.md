# OAP Coding Report — 009-n

Identifier: 009-n
Result: PARTIAL
Repository: ulfe-lmi/slaif-raggedized-helper
PR number: 11
Branch: oap/009-evaluation-baseline
Round base commit: 0b1311576eb5f66025ab422f74d7b07d1629784c
Transcript commit: ffb2ea2636ab187e9302c8a0faf7ebdd6e4081bc
Implementation head SHA: 09f1633b36b05fec7bea2cb24e33a60fdaef4434
Report publication commit: SELF
Order SHA256: 05f1f6297e6846992c4e73360f26c2648c1aa759e085cb77217df670a14afb43
Order chain SHA256 (this round, in sequence): 084a748a0909e9f96ca0c358bd655adbcd908173022da9bb841104af8f2e20e4 (diagnostic-1), dd248d0bb42389fdecf22eb0e3e26971932d1d033dc1141d78d4344a263bc8d9 (diagnostic-2), d642027cd32c3a10253f822e194d8a955084149f5de39ed59f8354e94e0dff70 (fixture-correction), ffaaee8f7ff28ac89fff8b94339a934c334e72edce22564ae4750266719f0fe2 (fixture-proof-amendment), 8fce66bafd0f930709c60b616c1aaa2eb1c319a60cbcec421ebcb0d4aff98f58 (reader-admission), ad72b9e24e57d8fcb317a21c4ac1912e8b812b57da75e406e575af97ff35dbf8 (publication-doc-precision)
Publication authorization: FINAL order 009-n-publication-stage.md (05f1f629…): standard non-force push to the existing branch authorized subject to its named checks; original live response coordinator PID 75786/start 350969001 (control receipt retained in private audit)

## Scope

009-n (FINAL) at base 0b131157 (the 009-m report head): bounded
diagnostic-to-publication continuation of the same objective and PR.
Changed semantics only: the spec reader depth guard, the bounded
manifest read loop with its corrected comment and fully exercised
fixture, and the publisher unit fixture ownership of partially-started
threads; plus current docs. No CI, manifest capacity, product
infrastructure, requirement, dependency/environment, credential,
model, hardware or protected-service change; no merge.

## Change

Transcript ffb2ea26 (sole parent 0b131157): the exact four-path Root
transcript (order/active/resolution/index), byte-verified.
Implementation 09f1633b (sole parent ffb2ea26): exactly 7 paths = 5
source/test + 2 docs.
- qualification/specio.py: parse_spec_json runs the package-internal
  quote-aware parity_io._depth_check (existing 64-container envelope)
  BEFORE json.loads; only its refusal translates to the fixed
  SPEC_INVALID/too_deep result; native RecursionError fallback,
  not_json line path, integer limit path and all reader/decoder
  behavior otherwise unchanged.
- test_qualification.py: test_deep_nesting_is_typed rewritten in place
  (same name, default-collected; bounded 65-container case immediately
  above the limit with typed refusal and an independent json.loads
  sentinel) + NEW positive test_depth_at_limit_parses_escaped_content
  (real parsing at the 64-container limit with escaped content).
- source_cli.py: _manifest_bytes read loop bounded to the captured
  initial regular size plus one; the first unexpected extra byte or
  early EOF ends the read and the excess is refused immediately; work
  is O(captured size), reaching the existing global limit only when
  the captured size is that large; the earlier wrong "never
  O(MAX_MANIFEST)" comment corrected; all other admission logic
  unchanged.
- test_source_cli.py: exact MAX_MANIFEST (256000) input admitted in
  full bytes (256001 still refused); test_manifest_growth_refused
  keeps its real read of a growing short file and now asserts the
  fully exercised fixture - exactly one read of the captured two bytes
  plus one actually observed extra byte (calls==1,
  requested==captured+1, returned==captured+1) - with the typed
  refusal retained; the only-upper-bound asserts that could pass
  without any read are dropped.
- test_private_report_publication.py: the publisher unit fixture owns
  partially-started threads on cleanup failure (abort barrier/signal,
  bounded joins, re-raise of the exact original exception) - one new
  default case (publisher partial-start cleanup); the exact
  postimage ce179d92 keeps its already accepted 89-case evidence.
- docs/evaluation.md + STATUS.md: current 009-n stage sections,
  combined delta 4492 B (<= 6000 B discipline); header/current-slice
  lead updated to 009-n (2026-11-20); 009-l report head 494a1908
  run 44022614755 SUCCESS preserved distinctly from the 009-m report
  head 0b131157 run 44028728886 FAILURE; local comparison and
  selected tests distinguished from actual CI; no unrelated docs
  change.

## Verification (bounded; all private logs/hashes in the audit dir, never in Git)

- Preflight exact: HEAD ffb2ea26 (sole parent 0b131157), branch
  oap/009-evaluation-baseline, exactly the five frozen uncommitted
  files at their order-table SHA256 (specio ee19a99d, source_cli
  afb7ea82, test_qualification f65b5800, test_source_cli 3cf4e91c,
  test_private_report_publication ce179d92 preserved byte-for-byte);
  main 5a7b41cc; PR 11 unique OPEN at head 0b131157, no
  auto-merge; coordinator 75786/start 350969001 alive; control
  receipt present; retained checkpoint evidence verified
  (fixture-correction 89/89 v1 81197ca3 / v2 ce179d92, both exit 0;
  reader-correction 19 passed exit 0; observer 7431d05c
  byte-identical).
- CI run 44028728886 at 0b131157 (the round base): completed FAILURE;
  only the two Product unit steps (3.14 and 3.12) failed, all three
  OAP jobs succeeded. The earlier five unit failures are UNTRACED and
  the native exit causes (139 on 3.14, 137 on 3.12) are UNPROVEN; no
  native pool owner or CI cause is claimed.
- Bounded local diagnostics (private audit only, scoped comparison,
  not actual CI): with the original configuration the comparison
  observed 40 OS threads and nearly exhausted virtual address space,
  with RuntimeError (can't start new thread) at the 8th
  partially-started publisher thread (p2); only setting
  OPENBLAS_NUM_THREADS=1 in the test subprocess changed collection to
  one OS thread and made the same case pass (p3); the publisher
  module passed 88/88 (p4); after the fixture correction 89/89 (v1,
  then strengthened v2 with real reservations before failure and
  exact release afterwards).
- One Ruff check (existing venv, repo config) of the two refined
  files: exit 0, "All checks passed!".
- ONE fresh bounded pytest invocation, identical envelope to the
  reader-correction step (CPU 60s / AS 2 GiB / wall 120s + kill 5s,
  prlimit, OPENBLAS_NUM_THREADS=1 subprocess-only, observer
  byte-identical, OBS_MATCH empty, OBS_CANON canonical, new 0700
  private basetemp): targets TestSpecInputReader + test_source_cli.py
  = 19 passed, no skips, true exit 0; observer n=19 sel=0,
  session_finish exit=0.
- The exact publisher test bytes were NOT re-run: their accepted
  89-case evidence is retained. No full local run, no historic
  fatal-case reproduction, no unchanged retry.
- Fresh report-head full CI: PENDING after the single push (observed
  state; pending is pending). Expected full default count 2731 =
  2729 + 2 (publisher partial-start cleanup; at-limit spec parsing)
  - an expectation only, awaiting actual CI evidence; a mismatch is a
  stop, not a silent adjustment; no narrower CI selection.

## Acceptance evidence

1. GitHub reconciled at round start and re-verified before push: PR 11
   unique OPEN, head = round base 0b131157, base main 5a7b41cc, branch
   graph ffb2ea26 (transcript) -> 09f1633b (implementation) -> report
   head; original coordinator alive; no competing response.
2. Implementation commit: sole parent ffb2ea26, exact 7-path set,
   clean index and worktree, machine-verified before push.
3. Report: one report-only diff, sole parent the implementation
   commit; exact bytes verified.
4. ONE standard non-force push to the existing branch; if the remote
   head had changed the push would have stopped. After remote
   verification of the report SHA and branch/PR identities, the
   original 009-n response completes once through the canonical
   CODING response helper (coordinator 75786 the only reader; never
   replayed; reconcile actual remote publication on notification
   failure, never resend).

## Documentation impact

New 009-n stage section in docs/evaluation.md and the STATUS.md
current-state update: CI attribution (009-l SUCCESS vs 009-m
FAILURE), untraced/unproven failures, local comparison vs actual CI,
changed semantics, two new default cases and the 2731 expectation,
baseline NOT_RUN, protected authority/hardware/right/license/MVP and
release gates open. Historical 009-m report/CI evidence preserved.
No history rewrite.

## DHA and boundaries

DHA NONE; no CRITICAL change. Preserved: Qwen profile/auth,
credentials, models, services and hardware untouched; no
dependency/environment installation; candidate branches/worktrees
untouched (no merge/cherry-pick/reset/force/tag/deploy/duplicate PR);
original FIFO readers untouched (no replay, no new reader); all final
local logs and hashes retained in the private audit directory, away
from Git. No merge; PR 11 remains open and unmerged.

## Limitations and remaining work

Whole 009 PARTIAL; no deployment readiness implied. Fresh report-head
CI pending (no green/cause/baseline/whole-MVP certificate follows).
The earlier five CI failures remain UNTRACED; the native exit causes
(139/137) remain UNPROVEN; local comparison and selected tests are
not actual CI. Real representative baseline NOT_RUN; no narrower CI
selection. no-auth/no-current-policy/no-real-producer/no-model-
qualification labels hold; protected authority/hardware/right/
license/MVP and release gates remain OPEN. Strategy owns the fresh
full check/acceptance review. No 010, no merge; DHA NONE.
