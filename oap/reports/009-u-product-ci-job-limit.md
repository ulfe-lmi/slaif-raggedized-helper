# OAP Coding Report — 009-u

Identifier: 009-u
Result: COMPLETE
Repository: ulfe-lmi/slaif-raggedized-helper
PR number: 11
Branch: oap/009-evaluation-baseline
Base branch: main
Implementation head SHA: 84a0b62fc3fe9fd6be95a24eeb15d15dacf5ec44
Report publication commit: SELF

## Work and scope

Order `oap/orders/009-u-product-ci-job-limit.md` (Status: FINAL, PR mode
AMEND_EXISTING_PR, Decision: NONE) at round base
`e97d29fb63a9dbc07dacc36f0feb13008251c92b` (the verified 009-t
report-only head). Objective: one changed CI job-limit comparison on
the same private PR — change the finite Product job-level
`timeout-minutes` from 20 to 30, keep every existing integration and
unit test execution and downstream check required, and let the effect
on this run be observed before the policy capture transfer can
advance.

History pushed in this round (no force push, no merge, one PR 11):

1. `d505f6d599a2c7d935a639cd707f89283bb3e9da` (parent: round base
   `e97d29fb63a9dbc07dacc36f0feb13008251c92b`) — exact Root
   transcript, committed unchanged: `oap/active` (bytes exactly
   `009-u` + LF, was `009-t` + LF),
   `oap/orders/009-u-product-ci-job-limit.md` (SHA-256
   `5b9a7818e7c80a7ea5a7c1e51c838b02d4f1809ada7a11ae1b58d36b92e13fdc`),
   `oap/reviews/009-u-ci-job-limit-prior-resolution.json` (SHA-256
   `1443a9c4b7ce676a03a1bcd39a106f1addeb31ae9c42bffe01ae53e0acb07f1c`,
   copied unchanged from the strategy workorders).
2. `84a0b62fc3fe9fd6be95a24eeb15d15dacf5ec44` (parent: 1, sole parent)
   — implementation: `.github/workflows/oap.yml` (the single
   line-70 integer change in product-tests `timeout-minutes`, 20 to
   30), `STATUS.md` (current-slice lead 009-t to 009-u plus the 009-u
   entry), `docs/CI.md` (Product job-limit line to 30 minutes),
   `docs/evaluation.md` (cumulative 009-u section). Four paths total.
3. SELF — this report only; first parent is the implementation head.

## Acceptance evidence

1. Reconciliation (round base, GitHub, order bytes, prior evidence).
   - Local branch head and remote
     `refs/heads/oap/009-evaluation-baseline` were exactly
     `e97d29fb63a9dbc07dacc36f0feb13008251c92b` (ordered base, the
     009-t report-only head); working tree clean except the pending
     ordered transcript bytes (`oap/active` modified `009-t` to
     `009-u`, order file untracked) — no unexpected working changes.
   - Live `refs/heads/main` was exactly
     `5a7b41cc512cf883b5b2cb92d87554b4d24e685b` (ordered value).
   - `gh pr view 11` (2026-11-20, ~10:45 UTC): state OPEN, isDraft
     false, headRefName `oap/009-evaluation-baseline`, headRefOid
     `e97d29fb63a9dbc07dacc36f0feb13008251c92b`, baseRefName `main`,
     mergeable MERGEABLE. `gh pr list --state open` shows PR 11 is
     the unique open non-draft PR.
   - Workflow preimage at the round base: 14,235 bytes, SHA-256
     `b919535561a88706d815f79d481aa3480837eb1de75d36b0c89ab7b0d99a6118`
     — exact ordered preimage; no drift.
   - Prior resolution source
     (strategy `workorders/009-u-ci-job-limit-prior-resolution.json`):
     SHA-256 `1443a9c4b7ce676a03a1bcd39a106f1addeb31ae9c42bffe01ae53e0acb07f1c`
     — exact ordered hash.
   - Adopted terminal evidence
     `audit/009-t-check/Root-terminal-review.json` (strategy home):
     SHA-256 `1b5fafccf0f70a649a7373c6df589a0f67366132271d4a85c14683e77e8fe131`
     — exact ordered hash.
2. Exact preimage/target bytes and single-integer scope.
   - Pre-change full file: 14,235 B, SHA-256 `b9195355…a6118`
     (ordered preimage).
   - One bounded edit (line 70 only): product-tests
     `timeout-minutes: 20` to `timeout-minutes: 30`.
   - Post-change full file: 14,235 B, SHA-256
     `54e66869d9a2a02e95202ed3eaecba199a2494ca6f6c5742554e722cf14367c6`
     — exact ordered target.
   - `git diff` of the workflow shows exactly that one line changed;
     the oap-tests job (three matrix legs: Python 3.12/3.13/3.14)
     keeps `timeout-minutes: 10` (line 27 untouched), and every
     action pin, permissions block, setup and step byte is exact by
     the full-file target hash.
   - Path scope checked before commit and at the candidate
     implementation head `84a0b62…` (`git diff e97d29f… 84a0b62…
     --name-status`): exactly the ordered seven paths —
     `.github/workflows/oap.yml`, `STATUS.md`, `docs/CI.md`,
     `docs/evaluation.md`, `oap/active`,
     `oap/orders/009-u-product-ci-job-limit.md`,
     `oap/reviews/009-u-ci-job-limit-prior-resolution.json`.
   - Blob verification at the candidate implementation head
     (`git show HEAD:<path> | sha256sum`): workflow 14,235 B /
     `54e66869…f6c6`; `oap/active` exactly `009-u` + LF (0x3030392d75
     0x0a); prior resolution `1443a9c4…f1c`; order file
     `5b9a7818…fdc`.
3. Requirements preserved; pending status before remote CI.
   - Both Product legs (Python 3.12/3.14) keep the unchanged unit
     commands requiring 3,015 actual units (1,421 group A and 1,594
     group B) and the same independent integration command, plus the
     complete unchanged later steps (lint, compileall, OAP suite,
     governance check, CLI checks); all matrices, permissions, pins,
     setup, fixtures, outputs and the 180 s unit-process budget are
     byte-exact.
   - The three OAP checks (oap-tests 3.12/3.13/3.14) are unchanged.
   - Pending status before remote CI: at report authoring NO run had
     yet started at the new report head; the push publishes the
     branch and the fresh hosted run is PENDING. Root assesses the
     new exact report-head terminal run and the remaining
     uncertainty; this report certifies no future check outcome.
4. Commit shape.
   - Ordered transcript committed unchanged (commit 1, byte-verified
     as above); implementation on its sole parent (commit 2); one
     immutable report-only SELF child (commit 3, this report). No
     advance to another objective, no merge, no release, no
     qualification on local proof.

## Verification

Exact commands and results (canonical checkout, 2026-11-20 UTC):

- `wc -c .github/workflows/oap.yml; sha256sum
  .github/workflows/oap.yml` (pre-change): `14235`,
  `b919535561a88706d815f79d481aa3480837eb1de75d36b0c89ab7b0d99a6118`.
- Bounded single-line edit at line 70
  (`sed -i '70s/timeout-minutes: 20/timeout-minutes: 30/'`), then the
  same size/hash command (post-change): `14235`,
  `54e66869d9a2a02e95202ed3eaecba199a2494ca6f6c5742554e722cf14367c6`
  (exact ordered target).
- `diff` old vs new workflow: exactly one differing line (70c70:
  `timeout-minutes: 20` to `timeout-minutes: 30`).
- `git status --porcelain=v1` at round start: only
  ` M oap/active`, `?? oap/orders/009-u-product-ci-job-limit.md` —
  the pending ordered transcript; nothing else dirty.
- `git diff oap/active`: `-009-t` / `+009-u` only.
- `xxd oap/active`: `3030 392d 750a` (`009-u` + LF, 6 bytes).
- `sha256sum` of the strategy prior-resolution source:
  `1443a9c4b7ce676a03a1bcd39a106f1addeb31ae9c42bffe01ae53e0acb07f1c`;
  identical after copy to `oap/reviews/` and at the implementation
  head.
- `sha256sum` of `audit/009-t-check/Root-terminal-review.json`
  (strategy home): `1b5fafccf0f70a649a7373c6df589a0f67366132271d4a85c14683e77e8fe131`.
- `git ls-remote origin refs/heads/main
  refs/heads/oap/009-evaluation-baseline`: `5a7b41cc512cf883b5b2cb92d87554b4d24e685b`
  and `e97d29fb63a9dbc07dacc36f0feb13008251c92b`.
- `gh pr view 11 --json state,isDraft,number,headRefName,headRefOid,
  baseRefName,mergeable`: OPEN / false / 11 /
  oap/009-evaluation-baseline / e97d29f…c92b / main / MERGEABLE.
- `gh pr list --state open`: PR 11 only.
- `git diff e97d29f… 84a0b62… --stat`:
  `.github/workflows/oap.yml | 2 +-`, `STATUS.md | 30 +…-`,
  `docs/CI.md | 2 +-`, `docs/evaluation.md | 46 +…` plus the
  transcript files in commit 1 — no other paths.
- `git show 84a0b62…:.github/workflows/oap.yml | sha256sum` /
  `wc -c`: `54e66869…f6c6` / `14235`.

Implementation-head CI already observed: none at the implementation
head (no run existed before this report); the only CI observation in
this round is the prior round's run 44717676140 attempt 1
(CANCELLED) as recorded in the order and the adopted Root terminal
review. No claim is made about this report's future push or checks;
the fresh hosted run at the exact report head is PENDING and a
separate post-publication receipt records the observed publication
facts.

Mock/live distinction: this round changed CI metadata only. No
product code, tests, fixtures, model data, corpora, GPU,
credentials, services or deployment were touched; no local suite,
setup installation or runtime observation was run (the order
requires none for this exact workflow change). All evidence above is
static byte/hash/repo-state verification on the canonical checkout;
the hosted run result remains unmeasured until Root's terminal
review.

## Documentation impact

- `docs/CI.md`: the existing Product job-limit line updated from
  20-minute to 30-minute per-job timeout (the bound now matches the
  workflow bytes; historical 20-minute facts retained in STATUS and
  docs/evaluation.md earlier sections).
- `STATUS.md`: current-slice lead moved 009-t to 009-u; new 009-u
  entry identifying the prior run 44717676140, the verified 20m0s
  timeout, the actual counts (3,015 units: 1,421 A / 1,594 B; the
  four policy modules at the expected 47/124/18/95 file counts; 3.14
  full 24 steps; three OAP jobs passed; 3.12 unit step
  10:15:30-10:17:35 UTC, integration 90% at 10:32:54, cancellation
  10:35:42, check-run 136225094911 explicit 20m0s, five later steps
  skipped), the reason for the bounded comparison (headroom against
  the proven platform cancellation after successful units; effect
  must be observed before the policy capture transfer can advance),
  the exact pending status and the NOT_RUN baseline / PARTIAL 009
  state.
- `docs/evaluation.md`: cumulative 009-u section with the same
  prior-run evidence, the single verified byte change with
  preimage/target hashes, the bounded headroom reason, the pending
  exact-report-head CI state, the gate rule (a second timeout or
  partial run cannot close it) and the historical 20-minute bound
  retained as a historical fact.
- No other behavioral documentation changed; no implemented
  commands, measured performance, license clearance or readiness
  claimed.

## DHA and boundaries

- Decision: NONE (as declared in the order); no critical-register
  append, no D1 candidate reported.
- Preserved: both matrices, permissions, action pins, setup, runner
  isolation, all unit/integration commands and fixtures, outputs and
  the 180 s unit-process budget, local runtime, prior reports, the
  previous cancellation annotation and progress evidence, all
  historical 20-minute job-limit records, unrelated branches,
  worktrees and private configuration.
- No merge performed; PR 11 remains OPEN and non-draft; no
  auto-merge, release, tag or deployment; the capture transfer and
  any product modification remain for a later exact order.
- No direct FIFO read/write by this round except the single owned
  `send-response.sh --identifier 009-u --timeout 10` after remote
  verification; no extra reader, activation replay or unchanged CI
  rerun; no nested/helper agents or model/profile changes.

## Limitations and remaining work

- The new 30-minute bound has not yet been observed: the fresh full
  hosted CI at the exact report head is PENDING at report
  authoring; Root owns the fresh CI terminal review of the new exact
  report-head run and the remaining uncertainty.
- The exact integration wall-time variance and the active test at
  cancellation in the prior run remain unproven (retained from the
  order; unchanged by this round).
- If the new hosted job ends early or fails, actual output is
  retained and the round stops for review; a second timeout or
  partial run cannot close the gate.
- Representative baseline NOT_RUN; protected
  authority/hardware/right/license/MVP and release gates open; whole
  009 PARTIAL.
