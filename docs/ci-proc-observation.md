# CI process observation — 008-d

This note records one narrowly observed CI failure and the test-only
observer repair made in objective 008, slice 008-d. It changes no
product behavior and grants no broader process-cleanup authority.

## Observed failure (preserved, immutable)

At the 008-c report head 322c7fe0, the unchanged normal hosted matrix
ran the actual Python 3.14 Product job (run 43368073059, job
131697112168). The node ID
`tests/unit/test_cpu_worker_backend_setup.py::test_timeout_kills_owned_descendant`
failed in its post-kill observation loop: `_descendant_gone` reads
`/proc/PID/stat` and caught only `FileNotFoundError`, while the runner
raised `ProcessLookupError` with errno ESRCH (3). The real descendant
timeout assertion itself had passed (TimeoutError raised, kill
dispatched); the observer misread an absence signal as an unexpected
error. The failed 3.14 run and its artifacts are preserved unchanged;
this does not mark 008-c retrospectively green. At the recorded
observation the Product 3.12 job was still running and three OAP jobs
had succeeded; that timing is continuation routing only, not
acceptance.

## Observer-only fix

In `tests/unit/test_cpu_worker_backend_setup.py`, `_descendant_gone`
now accepts exactly the two absence classes, `FileNotFoundError`
(ENOENT) and `ProcessLookupError` (ESRCH). Everything else is
preserved: the direct `/proc/PID/stat` read (no existence precheck),
zombie `Z` still reads as gone, live states still refuse, and no
broad `OSError`/`Exception` catch, retry, sleep increase, deadline
change, skip, or fixture rewrite was added. ESRCH is an absence
observation here; it is not authority to suppress arbitrary OS
errors — `PermissionError`/EPERM and `OSError`/EIO still propagate.

## Local evidence (single bounded process)

One `pytest` process, four node IDs, five cases (two parameterized
absence cases), all passed, exit 0, under CPU 10 s / AS 1 GiB / wall
30 s SIGKILL / CPU affinity 0 / five thread vars = 1 / closed benign
environment (`env -i`; no PYTHONPATH/VIRTUAL_ENV; bytecode disabled),
fresh owned 0700 TMPDIR, pinned interpreter
/tmp/slaif-scoring-test-assembly-setup-v2-20261113/venv/bin/python
(Python 3.14.4, pytest 8.4.2). GNU time: user 0.45 s, system
0.05 s, elapsed 1.18 s, max RSS 44,716 KiB. The venv's editable
application origin belongs to another isolated worktree and was not
used: the selected tests import only stdlib, pytest, and the
canonical-checkout `tests/support/prepare_cpu_worker_test_backend.py`
(tracked; byte identity retained in the private preflight record).
Read-only post-run observation: the owned descendant PID was absent.
Private records (preflight/argv/env/caps guard, split stdout/stderr,
GNU time, exit; fsync'd 0700 directory) are retained on the
development host only; identities are recorded in the 008-d report.

## Current CI status

The 008-d report-head push triggers the unchanged normal matrix (full
unit + integration on Python 3.12 and 3.14 plus the three OAP jobs).
Pending/skipped/cancelled is not green; Root observes post-response.
