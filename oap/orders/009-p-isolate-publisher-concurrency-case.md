# OAP Work Order — 009-p

Status: FINAL
Identifier: 009-p
PR mode: AMEND_EXISTING_PR
Branch: oap/009-evaluation-baseline
Base commit: e9f24bae9ce47c1ceb3f51e9eff10e91574c7242
PR number: 11
Expected active: 009-o
Provenance: H activated MVP development; A ARCH23/A24 private publication and honest proof; E CI44662270802 repeats thread-start failure; I Root exact-head review and isolated genuine fixture proof
Architecture SHA256: 4b41905396a3838269fd6cf372614cd23cb2c3b6a37be09f29ed752803c0983a
Governance SHA256: 24cec23235e3defc5f55bab4690298191d5a233d35dd9bf20b0afb4b3925f922

## Objective

Isolate the existing 16-slot test in one fresh bounded process while
preserving its default collection, all real concurrency, the existing
seventeenth-publication refusal before open and verified cleanup.
Restore the pre-experiment workflow bytes.

## Dependencies and current state

Only objective PR 11 is open, against main 5a7b41cc512cf883b5b2cb92d87554b4d24e685b.
e9f24bae is the report-only child of 1f8d84a4; its original response has
been consumed once. The two hosted Product legs in run 44662270802
received OPENBLAS_NUM_THREADS=1 and both again collected 2731, passed
2730, and failed the same test with RuntimeError in Thread.start().
The cleanup regression and 96-descriptor bound passed. Three OAP jobs
succeeded. Required downstream Product steps were skipped. The exact
hosted OS cause is unproven.

Read `audit/009-o-ci-terminal/Root-terminal-review.json` SHA256
9003c156bb4f2a66c123ea41ed0634e52c981b652829e4b9d7478b5d5ec94b91 and
`workorders/009-p-prior-resolution.json` SHA256
e0438d4305eaf1340afd34038503a8df0fbb967c7fed9858bdad2b3d762c6ade.
Root's corrected separate local probe executed the existing fixture
with 16 distinct genuine reservations, real refusal/no-open assertions,
one active thread before and after, and all 16 empty cells restored.
With 5 CPU seconds and 512 MiB address-space caps it returned zero in
0.28 elapsed seconds. The initial probe stopped before the fixture on
an incorrect expectation that the fixed-size slot list was false. Both
attempts are preserved. The successful exact probe source and log are
in that same directory (`isolated-harness-probe-v2.*`). This evidence
supports the focused isolation, with actual hosted success still open.

## Allowed paths and scope

CODING pane %30, canonical checkout. First commit exact Root order
`oap/orders/009-p-isolate-publisher-concurrency-case.md`, `oap/active`
(009-p plus LF), and Root bytes `oap/reviews/009-p-prior-resolution.json`.
Transcript sole parent e9f24bae. Implementation only these four paths:

- `tests/unit/test_private_report_publication.py` preimage SHA256
  ce179d9230cb278fb3de364b5e6449604bb6469b82dd4f7e729d8a9d0d50845a.
- `.github/workflows/oap.yml` preimage b919535561a88706d815f79d481aa3480837eb1de75d36b0c89ab7b0d99a6118.
  Remove the exact two 009-o env lines so bytes equal 21341795
  SHA256 29a44dd6f5d36d6035478c469d8b3c666fed8c25fe6c2b36ae2ac4e57c887bc4.
- `STATUS.md` and `docs/evaluation.md` current factual notes only.

## Non-goals

No production or other test-source edits, retries, skip/xfail, weaker
assertions, supervisor, dependency, deadline or CI job changes. No
native model or real publisher storage work, unrelated branch or next
objective. The unchanged partial-startup regression stays in pytest.

## Acceptance criteria

1. Verify the clean exact base apart from activation files, unique
   remote PR/state, transcript bytes, prior resolution and bound source.
2. Keep the default-collected test and original `_sixteen_slot_fixture`
   implementation and partial-startup regression byte-identical.
   Make the one 16-slot testcase launch a fresh `sys.executable -c`
   process with one fixed inline child program and the exact resolved
   physical test path as the argument. Use the existing
   `_child_environment` thread settings, explicitly setting child
   PYTHONPATH to the src corresponding to that exact test path and cwd
   to that checkout. Do not launch pytest recursively or use preexec_fn.
   Set existing child CPU 5s, AS 512 MiB, CORE 0 and FSIZE 16 MiB caps in
   the child before test or product import. Parent bounds subprocess
   to 20 seconds. The child loads the exact given test via runpy, checks
   existing origin assertions, uses a real pytest.MonkeyPatch context
   and calls the same fixture with an observer of genuine reservations.
   Require 16 distinct real reservations and restoration of the
   baseline registry, alongside all unchanged fixture assertions
   including refused 17th call before open and real worker termination.
   Parent requires zero exit and one fixed success marker emitted only
   after those assertions. Timeout/nonzero/missing marker fails the test.
3. Verify removal of the experiment restores the entire workflow bytes,
   including original suite selection and downstream steps. Focused
   Ruff, git diff --check and one scoped publisher-module run under
   existing venv: CPU 60s, AS 2 GiB, TERM 120s then KILL 5s, fresh private
   direct-`/tmp` basetemp and canonical src. Use explicit synthetic
   child/setup paths, preserve output and actual exit; expect 89 passes.
   A test failure remains evidence and requires review. Keep any setup,
   cap or resource failure distinct from a test assertion failure.
4. Verify the three distinct commit layers. Commit one immutable
   report-only sole child of the implementation after passing local
   verification. Reconcile remote base, then one standard non-force
   push to the existing branch. Verify exact report publication before
   responding once via canonical helper. Root independently checks
   full fresh CI before disposition. DEFAULT collection expectation
   remains 2731 and is an expectation before actual CI.

## Verification and negative evidence

Keep exact file hashes and full bounded local outputs in
`audit/009-p-check/` under strategic home. Tests exercise the same
production fixture and its negative boundary in an owned process.
Successful isolation in the local environment is proven only for the
named command. The hosted limiting resource and hosted benefit are
unproven until actual evidence. The full suite remains required.

## Documentation

Update current STATUS marker to 009-p. Add brief 009-p notes to STATUS
and evaluation docs near 009-o. Record both hosted counts, the actual
OpenBLAS step result and restored workflow, test isolation with genuine
unchanged obligations, local actual results and fresh CI pending.
Keep original immutable reports and historical evidence. Baseline
NOT_RUN; 009 remains PARTIAL and MVP gates OPEN.

## Runtime and protected resources

Existing CODING client/profile/auth, exact OAP helpers, existing venv,
private synthetic Linux tests. No environment install, service, GPU,
credentials, corpus, rights, hardware, deploy or release actions.

## Deferred human adjudication

- Decision: NONE

## Publication and report

`oap/reports/009-p-isolate-publisher-concurrency-case.md`, same PR 11,
PARTIAL whole 009, literal SELF and exact order/transcript/implementation
hashes, bounded results, and actual pending checks. No merge. Preserve
other lanes, existing FIFO ownership and prior receipts.
