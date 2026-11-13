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
timeout assertion itself had passed (TimeoutError
raised); the "kill dispatched" wording in that old trace is inference
from the timeout path, not a separately measured observation. The
observer misread an absence signal as an unexpected error. The failed
3.14 run and its artifacts are preserved unchanged;
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

## Harness limits and attestation status (Root replan, 008-e)

The focused five-case success under the inner caps is positive behavior
evidence only. The private harness directory reset, check-cat guard and
uncapped metadata, fsync and pytest-version probes do not establish
one-shot provenance, and there is no evidence that actual prior
directory data was deleted; no such absence claim is made. The
historical LOCAL-008D-ONE-SHOT-ATTESTATION remains UNPROVEN permanently
and is not repaired by 008-e; the unsafe private harness is never
rerun or reused. That round moved 9 paths excluding its own report and
10 including it; the immutable 008-d report keeps its own wording.
The old failed 3.14 CI (run 43368073059) is preserved and is not marked
green retrospectively.

## 008-e trace fixture portability

The incoming trace integration fixture had pointed at a strategic
private historical witness cache, which is not clean-runner portable.
Per the exact Root D0 addendum, `trace_owned` now calls the inherited
`test_native_tokenizers.make_native(tmp_path)` exactly once before
installing its subprocess guard, verifies the two pinned artifact
hashes, and keeps monkeypatching that helper to the same owned
paths/runtime/definition so the inherited source builder regenerates
nothing; the hard-coded private cache, manual paths and redundant
runtime/definition recreation are removed. The private witness remains
historical evidence of its exact run only. No local generator, test,
collection, import or setup ran in 008-e; the full unchanged hosted CI
alone executes the corrected fixture.

## Current CI status

At the exact c3e3 report head the unchanged normal matrix is terminal:
run 43370945412, all five jobs / all 78 required steps SUCCESS with
1,864 unit + 894 integration on both Product 3.12 and 3.14 legs (per
oap/reviews/008-d-ci-terminal-summary.json). The 008-e report-head push
triggers a fresh unchanged normal matrix (full unit + integration on
Python 3.12 and 3.14 plus the three OAP jobs).
Pending/skipped/cancelled is not green; Root observes post-response.
