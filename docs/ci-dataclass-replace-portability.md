# CI correction 009-b: portable `dataclasses.replace` rejection expectation

## Observed failure (009-a report head)

CI run 43395492425 on PR 11 head `21a3cbd` (009-a): the Product
tests (Python 3.12) job failed in
`tests/unit/test_text_evaluation_dataset.py::test_oracle_and_frozen_private_records`.
On CPython 3.12.16 the call

    dataclasses.replace(result, qualification="QUALIFIED")

raises `ValueError` because `qualification` is an `init=False` field,
while the test expected only `TypeError`. The production guard worked
as designed on both versions — the replacement is refused; only the
test's exception-class expectation was not portable. The same job's
later required steps were SKIPPED. The three OAP jobs and the Product
3.14 unit step SUCCEEDED (on 3.14 the same call raises `TypeError`);
no leg of that run is accepted green. Full reconciliation:
`oap/reviews/009-b-prior-ci-failure.json` (recorded at root; no old-run
retry).

## Mechanism

CPython's `dataclasses.replace` validates `init=False` field changes
before calling `__init__`; the stdlib rejection class for that
validation differs across supported versions (ValueError on 3.12.16,
TypeError on 3.14.4). Both are ordinary exception types raised by the
same single rejected call; accepting exactly that two-type tuple admits
only this stdlib variation, not a blanket exception.

## Fix (unit-test expectation only)

The one `pytest.raises(TypeError)` clause immediately around that call
now reads `pytest.raises((TypeError, ValueError))` (line 46). Every
other byte, test case, fixture, assertion, import and production blob
is unchanged: the file's only differing line is 46, and normalizing the
new tuple back to `TypeError` makes the module AST exactly equal to the
base (`21a3cbd`) AST. The call must still refuse the replacement, and
all frozen-record, metadata and oracle assertions are retained. No
product, dependency, workflow, config, law, profile, cap, skip or
xfail change; no test deleted.

## Local evidence (Python 3.14.4 only)

- ONE focused pytest process ran the ENTIRE
  `tests/unit/test_text_evaluation_dataset.py` module after the fix:
  19 passed in 0.44 s, exit 0; builtin cache provider enabled with a
  fresh private cache dir (nodeids 1,614 B) and declared absent private
  basetemp (not created; no tmp_path use); closed benign env (PATH/
  HOME/LANG/PYTHONPATH repo src+tests-unit, private TMPDIR, five
  OMP/OPENBLAS/MKL/RAYON/NUMEXPR thread vars = 1, bytecode and
  third-party plugin autoload disabled); default assertion rewriting
  was used (no `--assert=plain`; project addopts is only `-q`);
  inherited child rlimits CPU 10 s / AS 1 GiB / FSIZE 16 MiB and CPU 0
  affinity; the 60 s wall figure was a launcher-level SIGALRM backstop
  only, not a descendant wall-cap proof — the observed 0.773 s wall /
  exit 0 is a valid measured sample; max RSS 62,724 KiB; GNU time
  0.70 s user / 0.06 s system / 0.77 s wall.
- ONE focused Ruff 0.17.4 check on the changed unit file only: All
  checks passed (same closed env; inherited rlimits CPU 5 s / AS 512
  MiB / FSIZE 16 MiB, CPU 0 affinity; launcher wall backstop 30 s,
  same non-descendant limit).
- Pinned interpreter `/tmp/slaif-pinned-query-setup-20261113/venv/bin/
  python` resolves to `/usr/bin/python3.14` (SHA-256
  52e0a13e60a981d8c4b6478be2ba5176f69da07948a056bf49cf6f077e30cb41);
  the venv's editable app origin belongs to another worktree and was
  not used (explicit canonical `src` via PYTHONPATH).
- Old test file SHA-256
  901707fffd38b0953e43ad054bb78fccca7736e273264d365879499599e89822;
  fixed file SHA-256
  b00aa74f4097002b03cd441a97fd920ed706c7cbaf16ecba80640d9fb93026ac.
- Procedure deviations preserved, not backfilled: the pytest
  preflight JSON's `at` field (09:00Z) is not the actual creation
  time (file mtime 09:08:05; run 09:08:28); no standalone Ruff
  preflight file exists — the shared launcher records the Ruff argv
  and caps before both invocations, and the closed env, source and
  tool hashes are identified in the postflight record.
- Root pre-SELF precision review (audit/
  009-b-local-harness-precision-review.txt, SHA-256
  9dc54831f65c278654095f96f4664ef79f25ae9af4aee56a00f48c0c3a7a00e4):
  the successful synthetic focused unit + Ruff results are accepted as
  LIMITED evidence with the procedural deviations above, not full
  planned-guard compliance; no extra runtime or retry; any new
  actual-source proof needs a separate proper child-lifetime guard.

This is a local 3.14 regression only: no local Python 3.12 run was
performed or claimed. The new full remote 3.12/3.14 matrix at the
report head is the cross-version proof and is PENDING until Root
reviews it; it is not certified by this note.
