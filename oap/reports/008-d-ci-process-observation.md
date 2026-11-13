# OAP Coding Report — 008-d

Identifier: 008-d
Result: PARTIAL
Repository: ulfe-lmi/slaif-raggedized-helper
PR number: 10
Branch: oap/008-raw-hybrid-snapshots
Base branch: main
Round base commit: 322c7fe0f54e3ce53fa4550c914cd73f51525126
Transcript commit: ba9970373e1ee1dcfdc0d350ffb76a633a564a5d
Implementation head SHA: 2ca3cec3d5bcaee0ad550607950499159f7d4003
Report publication commit: SELF

## Work and scope

Order 008-d (FINAL, DHA NONE, AMEND_EXISTING_PR) amended PR 10 on exact
branch/base 322c7fe0. Transcript ba997037 (sole parent 322c7fe0):
unchanged FINAL order, active 008-d+LF, THREE exact Root records
(5,272 B) + exact index (1,178 B 24ba99d3…d341f) per
oap/reviews/008-d-root-records.json — 6 paths, all bytes verified
before commit, no Root bytes edited. Implementation 2ca3cec3 (sole
parent transcript): ONLY the test-only observer repair in
tests/unit/test_cpu_worker_backend_setup.py — _descendant_gone now
accepts exactly FileNotFoundError(ENOENT)+ProcessLookupError(ESRCH);
direct /proc/PID/stat read, zombie Z observation and live-state
refusal preserved; no broad except, existence precheck, retry, sleep
increase, deadline/cap change, skip or fixture rewrite — plus two new
deterministic regressions (parameterized errno-bearing ENOENT/ESRCH,
one read each; live S false, zombie Z true, PermissionError/EPERM and
OSError/EIO propagate, one read each); the existing boundary and real
timeout tests byte-unchanged — plus new docs/ci-proc-observation.md
and the current STATUS 008-d entry. 3 paths; 9 round paths total; no
product module, setup.run/cleanup, other test, CI, dependency,
profile, law, prior report or source-book change; no merge.

## Acceptance evidence

1. Same PR 10/branch/322c7fe0 base: report ← 2ca3cec3 ← ba997037 ←
322c7fe0; round diff vs base = 9 paths (6 transcript + 3
implementation), none unexpected; order/active bytes unchanged in
both commits and byte-identical to worktree; no reset/stash/clean/
rebase/force-push/report amendment; main and other branches
preserved.
2. Exactly the narrow observer fix plus the deterministic
errno/read-count/live/zombie/unexpected-error regressions; the
preserved test_timeout_kills_owned_descendant (literal stdlib
parent+child sleep code, timeout 0.7, observation budget 2) remains
intact and its real descendant-disappearance assertion is the live
check; product setup.run and cleanup implementations unchanged; a
still-running process still fails (live S → false; EPERM/EIO
propagate; no existence precheck).
3. ONE focused local pytest process, four node IDs, expected five
cases — five passed, exit 0 — pinned
/tmp/slaif-scoring-test-assembly-setup-v2-20261113/venv/bin/python
(Python 3.14.4, pytest 8.4.2), -q -p no:cacheprovider, caps CPU 10 s
/ AS 1 GiB / wall 30 s SIGKILL / affinity 0 / five thread vars 1,
env -i closed benign env (no PYTHONPATH/VIRTUAL_ENV;
PYTHONDONTWRITEBYTECODE=1, -B), fresh owned 0700 TMPDIR
/tmp/slaif-008d-proc-observer-proof-20261113; GNU time user 0.45 s /
system 0.05 s / elapsed 1.18 s / max RSS 44,716 KiB; only the two
owned Python children ran; read-only post-run observation: owned
descendant PID 165119 absent. No full unit module or unrelated
tests: the other module tests require explicit capsule fixtures and
are covered by unchanged hosted CI.
4. docs/ci-proc-observation.md and STATUS.md describe the actual
old-3.14 failure, observer-only fix, exact local evidence and
current final-head CI status; the old failed 3.14 artifacts are
preserved unchanged; 008-c is not marked retrospectively green; no
whole-008/MVP/model/scale/rights/license or closed-ICA claim.
5. One final report-head push triggers the unchanged normal matrix
(full unit+integration on BOTH Python 3.12/3.14 plus three OAP
jobs); pending/skipped/cancelled/failed are not green; Root observes
after the one normal response; no future-CI claim, no
self-acceptance/merge.

## Verification

Private fsync'd 0700 records (guard/raw stdout/stderr/GNU time/exit)
retained on the development host only; witness identities: driver
db633fad…b97f8; test 0fb11320…13674; support 4b782177…dfb8 (tracked
in this canonical checkout); config lock e0a2b1be…41299 (matches the
support LOCK_HASH) + requirements d20b4d12…5ce63; tools prlimit
cb28811c…57bc4 / timeout f84e76ea…8e02 / taskset 42acb8e2…2d57 /
time 34ba90f8…7bf1e; interpreter /usr/bin/python3.14 52e0a13e…0cb41;
pytest module 66993a5e…dcdc6. Exact argv/env/caps were recorded in
the durable attempt-guard BEFORE the single exclusive attempt. The
venv's editable application origin (another isolated worktree) was
NOT used or represented: selected tests import only stdlib, pytest
and the canonical-checkout support script. Optional static checks
(CPU 5 s / AS 256 MiB / wall 30 s, five vars 1, no bytecode): AST
parse + py_compile OK, 9,985 B, exit 0. This report cannot certify
its own future push or CI: at publication the 008-d report-head CI
is PENDING; the 322c7fe0 3.14 failure (run 43368073059, job
131697112168) is preserved, not hidden or rerun.

## Documentation impact

New narrow docs/ci-proc-observation.md: observed failure,
observer-only fix, ESRCH-as-absence-not-suppression, single-process
local evidence and current CI status. STATUS.md current 008-d
entry. Source/data snapshots, retrieval docs, README, TESTING, CI,
pyproject, uv.lock, law and all prior reports byte-unchanged.

## DHA and boundaries

Decision: NONE; no CRITICAL entry. Preserved: unrelated files and
worktrees, human Qwen3.8-27B/A100Q8 profile/auth, other panes and
branches, prior immutable orders/reports/records; no service/GPU/
credential/corpus/model action, no public exposure. No merge
performed; PR 10 remains open for Root observation; no tag/deploy/
release; no FIFO read/replay, no duplicate readers, no nested
agents, no next-suffix work.

## Limitations and remaining work

Test-only evidence-observation repair: no claim of universal
arbitrary-descendant cleanup or kernel behavior; the preserved real
timeout test and the full current CI are the mandatory live checks.
No local full-module or integration run this round. Not qualified:
whole 008, the deferred scoring transfer (later suffix), dense/
BM25/RRF/hybrid waves, corpus, neural/FP16 quality, capacity,
rights/license clearance, ICA, held-out quality. Report-head CI
pending at publication; Root independently reviews the final head
and all required jobs/steps before any further development gate.
