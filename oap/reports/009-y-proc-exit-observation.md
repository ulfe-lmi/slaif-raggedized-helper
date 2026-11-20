# OAP Coding Report — 009-y

Identifier: 009-y
Result: COMPLETE
Repository: ulfe-lmi/slaif-raggedized-helper
PR number: 11
Branch: oap/009-evaluation-baseline
Base branch: main
Implementation head SHA: 1f07615984e60a45284cb367672d44eff150389d
Report publication commit: SELF

## Work and scope

Order `oap/orders/009-y-proc-exit-observation.md` (FINAL; AMEND existing
PR 11; Decision: NONE) at round base
`53937d7eac0805905a0b6c5ca6e973ea989f8032` (the verified 009-x
report-only head). Objective: correct the Linux procfs exit
observation in the existing owned-descendant timeout test so it
recognizes a task disappearing after a successful stat-file open,
preserving the tested timeout and process custody behavior.

History published in this round (one regular push to the same PR
branch, no force push, no merge, one PR):

1. `97ba0278b0632e9faa73d6cc964f92d93adef0ed` (parent: round base
   `53937d7e`) — exact Root transcript: `oap/active` (`009-y` + LF,
   6 bytes), `oap/orders/009-y-proc-exit-observation.md` (byte-
   identical to the strategic final workorder, SHA-256
   `b2f04e929faf2b9669a7f5e416a15c04236b0d7d7d4fa2bb424b5c0f8d0ca354`),
   `oap/reviews/009-y-prior-resolution.json` (SHA-256
   `61fc5048a5e2df6f26b8c775e9bd999985a3d97034e6229001aee6744256d15c`).
2. `1f07615984e60a45284cb367672d44eff150389d` (parent: 1) —
   implementation: `tests/unit/test_real_cpu_toy_probe.py`
   (changed, 23,282 B; only `test_timeout_kills_owned_descendant`
   touched), `STATUS.md`, `docs/evaluation.md` (3 paths total).
3. SELF — this report only; first parent is the implementation head.

The prior resolution `workorders/009-y-prior-resolution.json`
SHA-256 verified exact at
`/home/janezp/codex-supervision/slaif-raggedized-helper/workorders/`,
and every indexed input verified byte-exact before implementation:
consumed receipt `.oap-state/response-consumed-009-x.json`
(346 B, `b7b0868fe8a5fb5c1bb59f427eeac8d7ce056c9b1a35a1ca5babc47b75ce965e`),
Root terminal review `audit/009-x-check/Root-terminal-review.json`
(4,840 B, `5130c9ad75bbbf90e182393020600680faaf59847092386021cf1b5ddb8bd2b6`),
witness `audit/009-x-check/proc-exit-race-witness.py` (2,431 B,
`8373d6d414bdd22e94d18c5207ed4caa9fe5dd6094683a5488c90eecf14bb8b3`),
legacy witness stdout
`audit/009-x-check/Root-proc-exit-legacy-witness/stdout` (353 B,
`8e7451e15ee3ab85afa955c3b792adc22fc2bb721c1a9b25cb450b8654a4f61d`),
and the five canonical inputs at base (`test_real_cpu_toy_probe.py`
23,122 B `fb8c9d26...`, `.github/workflows/oap.yml` 14,235 B
`54e66869...`, `STATUS.md` 148,964 B `74e95b90...`,
`docs/evaluation.md` 136,700 B `3c1f527e...`,
`oap/reports/009-x-protected-policy-payload-install.md` 13,245 B
`53170b77...`). The accepted isolated candidates remain outside this
continuation, per the prior resolution.

## Acceptance evidence

1. Two disappearance observations at the owned stat poll. The
   inherited test observed exit only via a missing path
   (`FileNotFoundError` at open) or a zombie. The exact 009-x hosted
   failure (run 44760385202 attempt 1, Product 3.14 job
   136371029375, node
   `tests/unit/test_real_cpu_toy_probe.py::test_timeout_kills_owned_descendant`)
   was the second real form: ESRCH while reading an already-opened
   stat record after the task disappeared, after the actual expected
   parent timeout (legacy witness: ProcessLookupError/3 on the held
   record read, FileNotFoundError/2 on the absent record open;
   controlled ENOENT already passed the base test while controlled
   ESRCH and EACCES escaped). The changed test now accepts
   `FileNotFoundError` at open and `ProcessLookupError` at read at
   the stat poll (`except (FileNotFoundError, ProcessLookupError):
   break`). In the existing pidfd-bound cleanup, a missing stat
   record after successful pidfd acquisition is accepted, with the
   new `except FileNotFoundError: pass` surrounding only the procfs
   stat read; the PID/start-time comparison and the existing
   `pidfd_send_signal` stay outside that handler, inside the
   existing fd-close span, and the original outer
   `except ProcessLookupError: pass` is byte-exact. Other I/O and
   malformed evidence retain their failure behavior: the controlled
   EACCES injection still escapes as PermissionError/13 (acceptance
   item 3 witness), and a malformed record still raises (e.g.
   `IndexError` on `stat[19]`) because the new handler matches only
   `FileNotFoundError`.
2. Preserved behavior, verified byte-level in the diff: actual
   parent timeout (`pytest.raises(TimeoutError)` around
   `probe.run_bounded`), the 2-second observation deadline, the
   zombie check (`state == 'Z'`), the `assert not probe.UNREAPED`
   assertion, the same-handle `signal.pidfd_send_signal(fd,
   signal.SIGKILL)` path, the exact PID/start-time check
   (`stat[19] == start and stat[0] != 'Z'`) before any conditional
   cleanup signal, the still-live failure path
   (`pytest.fail('owned descendant remains live')`), the descriptor
   close (`finally: os.close(fd)`) and all 28 module test nodes.
   No product source, workflow, test inventory, resource or timeout
   budget, test runner, process-signal or PID/start-time binding
   outside the two cuts changed (`.github/workflows/oap.yml` at its
   prior-resolution hash `54e66869...` at the implementation head).
3. Bounded local proof at the implementation bytes (all under
   `timeout -k 5 120 prlimit --cpu=60 --as=1073741824` with
   `OPENBLAS_NUM_THREADS=1`, `PYTHONDONTWRITEBYTECODE=1`, fresh
   private 0700 scratch `/tmp/oap-009-y-proof.XrUXZt` under sticky
   `/tmp`, private basetemp, `-o addopts= -p no:cacheprovider`,
   locked .venv Python 3.14.4 / pytest 8.4.2 / ruff 0.17.4):
   (a) the entire inherited test module once —
   `python -m pytest tests/unit/test_real_cpu_toy_probe.py -v -o
   addopts= -p no:cacheprovider --basetemp <scratch>/pytest-module`
   — `28 passed in 1.93s`, exit 0, expected 28 cases met;
   (b) the existing strategic diagnostic
   `audit/009-x-check/proc-exit-race-witness.py` (byte-exact,
   unmodified) once through the canonical Python from the canonical
   repository with its own private scratch path — exit 0, output:
   `actual_linux.held_record_read` ProcessLookupError/errno 3 and
   `actual_linux.absent_record_open` FileNotFoundError/errno 2 (the
   two actual Linux read forms, real kernel evidence on owned
   synthetic children), then the synthetic injected observations at
   the owned stat poll: ENOENT `PASS`, ESRCH `PASS` (the changed
   test accepts both), EACCES PermissionError/errno 13 (still
   escaping). The synthetic injected observations are presented
   distinctly from the actual timeout and kernel evidence in that
   output; (c) one targeted ruff check on the changed test module
   pinned to one process-local core (`taskset -c 0 ruff check
   tests/unit/test_real_cpu_toy_probe.py`) — `All checks passed!`,
   exit 0. Physical test origin
   `/home/janezp/codex-work/slaif-raggedized-helper/tests/unit/test_real_cpu_toy_probe.py`
   (implementation bytes SHA-256
   `4408a5585918e58b343b49a302ff3906c3ce7a6e34dd8667622ee931f0388de5`);
   product import origin
   `/home/janezp/codex-work/slaif-raggedized-helper/tests/support/real_cpu_toy_probe.py`
   (unchanged, SHA-256
   `be17aab302777d7bdbc39b40a7eae6f0f0f78b9b2aefb46d847a630070dece76`).
   Actual first fault preserved: the first witness invocation
   aborted at setup (`FileNotFoundError` creating
   `<scratch>/witness/ENOENT` because the diagnostic expects the
   supplied scratch directory to already exist) before any
   observation; the raw traceback is preserved and the single
   changed-input diagnostic run above is the authorized observation.
4. Fresh hosted gate. The fresh full hosted CI at the exact report
   head — both Product legs (Python 3.12 and 3.14), each with
   unchanged ordered A 1,440 and B 1,756 unit cases, the separate
   951-case integration and the same three OAP jobs, every existing
   step succeeding — is PENDING at report authoring and is a
   distinct gate from the local proof above; Root owns this
   terminal review. The prior failure is attributed to the exact
   009-x run 44760385202 attempt 1 only; its passing 3.12 full leg
   (3,196 ordered units), 62 new payload cases on both Products and
   three OAP jobs are preserved as prior results.

## Verification

Exact commands and raw results as listed in acceptance item 3, with
raw streams preserved in the private 0700 scratch
`/tmp/oap-009-y-proof.XrUXZt` (`module-run.txt`, `ruff-run.txt`,
`witness-run.txt`, `witness-setup-fault-1.txt`, `origins.txt`).
All local evidence is synthetic/owned: owned temporary processes and
procfs records only; no network, keys, GPU, model download, live
route, real corpus or protected-runtime use. The witness
`actual_linux` section is real Linux kernel evidence on owned
synthetic children (the same sequence Root reproduced in the legacy
witness); the ENOENT/ESRCH/EACCES sections are synthetic injected
observations at the owned stat poll. The fresh full hosted
comparison at this exact report head is PENDING at report authoring;
the adopted prior hosted evidence is run 44760385202 attempt 1 as
attributed in acceptance item 4. This report does not certify its
own push or that CI, and Root owns the fresh CI and terminal review.

## Documentation impact

`STATUS.md`: current slice advanced 009-x → 009-y and one
cumulative 009-y entry added (observed inherited procfs exit race,
exact 009-x run attribution, the two bounded observation cuts and
their scoping, preserved behavior, actual local proof, pending
exact-head hosted gate distinguished from local proof, expected
counts, open gates). `docs/evaluation.md`: new 009-y section before
the preserved input-contracts section with the same content. Both
preserve the representative baseline NOT_RUN and whole 009 PARTIAL,
and state that the open governed operator, the real representative
baseline, source rights and model gates remain open. All historical
sections preserved.

## DHA and boundaries

Decision: NONE. No critical entry appended or modified. Preserved:
the canonical locked .venv (no installation or upgrade), all prior
reports/reviews/orders bytes, the strategic draft
`009-y-proc-exit-observation-DRAFT.md` (untouched; only the final
workorder bytes were committed), unrelated branches and worktrees.
No merge, no new PR, no force push, no tag/release/deploy, no
model/provider/profile change, no next-work selection, no other
consumer started.

## Limitations and deviations

No local full unit or integration suite was run, per the order; the
expected hosted counts (A 1,440, B 1,756 per Product, 3,196 units,
951 integration) are projections until the fresh hosted run measures
them. The actual first fault (witness scratch-directory setup, raw
traceback preserved) occurred before any observation and is not a
test or product fault. The order's `Expected active: 009-x` field is
the activation-time compare-and-set state; at execution `oap/active`
is exactly `009-y\n` with exactly one matching order in
`oap/orders/`, so no conflict exists. The round used the canonical
`.venv` Python 3.14.4 for all local proofs; the hosted 3.12/3.14
legs remain the pending gate.

## No merge

No merge performed or requested; PR 11 remains open and non-draft.
Baseline NOT_RUN; whole 009 PARTIAL; DHA NONE.
