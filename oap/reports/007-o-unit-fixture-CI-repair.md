# OAP Coding Report — 007-o

Identifier: 007-o
Result: PARTIAL
Repository: ulfe-lmi/slaif-raggedized-helper
PR number: 9
Branch: oap/007-embedding-pipeline
Base branch: main
Round base commit: 915dbc53bad866be70f730416806e500cdaa4dad
PR main base: 11badc7782bed326995d400f5532b63399b91fbd
Transcript commit: 9c3fe0fc8c9702f28c7d4707698fbb45b6f5424b
Implementation head SHA: d043956033d016e442e9a2fc4b86e65cf3b54d91
Report publication commit: SELF

## Work and scope

Order 007-o (FINAL, DHA NONE, AMEND_EXISTING_PR) ran
transcript-first from the round base: (1) transcript
9c3fe0fc (sole parent = round base): exact final order,
active `007-o` + LF, five exact Root CI-repair records and
the exact index (oap/reviews/007-o-root-records.json SHA-256
38f2855ed939c7f7143ce9998a285e41726761fb0a12465ba28494a1e0a8f30b);
every record verified SHA-256- and byte-exact before commit;
the ordered .log record was force-added because the
protected `*.log` .gitignore would otherwise exclude it (no
law change). (2) Implementation d0439560 (sole parent =
transcript): exactly ONE unit file changed, tests/unit/
test_gpu_embedding_producer.py — the post-COMPLETE journal
interruption test no longer imports the integration-only
test_embedding_job_journal_composition; it reuses the
unit-scoped typed batch fixture from test_embedding_batch_
store with count1 and derives the embedding-job plan from
that same metadata/dependencies/rows/codec policy. Actual
Journal/typed store, publish, commit-then-interrupt
injection, exception identity, COMPLETE reconciliation,
verified output/ref/metadata and all
PENDING/CLAIMED/RUNNING/COMPLETE assertions are unchanged;
no mock replacement, no skip/xfail, no swallowed interrupt.
No merge/cherry-pick/rebase/reset/stash/clean/switch; no
workflow/CI/helper/lock/dependency/law change; no nested
agents or other consumer.

## Acceptance evidence

1. No cross-suite import: the unit test imports only
tests/unit modules; its typed one-row fixture and derived
plan share metadata/dependencies/rows/codec policy by
construction; publish/journal-interrupt/reconcile
semantics and every substantive assertion preserved; no
whole journal/store/validator monkeypatch (only the
ordered single handle._commit interrupt injection), no
skip/xfail, no swallowed interrupt.
2. Clean unit-only proof (PYTHONPATH unset, installed app
interpreter .venv/bin/python 3.14.4, ordinary pytest unit
layout, no integration path added): the formerly failing
node passes (1 passed, exit 0); then its full unit module
under the same conditions: 23 passed, exit 0 (expected 23,
actual 23). One run each, distinct isolation/regression
purposes; no count-only rerun, no old 51/13 replay.
3. Each process separately capped: CPU30/AS1GiB/wall120
(prlimit + timeout), OMP/OPENBLAS/MKL/RAYON/NUMEXPR
threads 1, PYTHONDONTWRITEBYTECODE=1, private 0700
basetemp; existing app NumPy 2.5.4 and synthetic typed
data only; no model/native-worker/GPU/driver/service/
network/install/credential activity.
4. Original failure and masking explained with byte-exact
committed evidence: Root clean repro
(oap/reviews/007-o-unit-isolation-repro.log) shows
ModuleNotFoundError at the former line 198 under clean
unit-only pytest — the unit test imported an
integration-directory module that is not on the unit-only
CI sys.path (the CI product step runs
`uv run pytest tests/unit -q`); the remote record
(oap/reviews/007-o-prior-CI-failure.json, run
43278270704) shows 3/5 jobs, both product jobs failed at
the "Product test suite" step, 64/78 steps successful, 2
failed, 12 skipped, integration and later steps not run.
Broader local PYTHONPATH=src:tests/unit:tests/integration
put tests/integration on sys.path, so the import resolved
and masked the failure locally.
5. CI: no CI run exists for the report commit at
publication; required checks at the CURRENT REPORT head
PENDING/UNOBSERVED; development acceptance REQUIRES every
one of all 5 jobs and every actual required step
(currently 78) SUCCESS; missing/skipped/pending/
cancelled/failed is not green; no bypass; post-push
observation recorded separately.

## Verification

prlimit --as=1073741824 --cpu=30 timeout 120 env -u
PYTHONPATH PYTHONDONTWRITEBYTECODE=1 OMP/OPENBLAS/MKL/
RAYON/NUMEXPR_NUM_THREADS=1 .venv/bin/python -m pytest
"tests/unit/test_gpu_embedding_producer.py::test_actual_
journal_committed_complete_survives_interruption"
--basetemp=<private 0700> -q: 1 passed, exit 0. Then same
capped clean unit-only layout, full module: 23 passed,
exit 0. ruff check on the changed unit file: All checks
passed; AST parse OK; compileall -q exit 0. Unchanged
production/law/CI/governance verified byte-identical to
the round base (clean working tree; per-commit
diff-tree names = exactly the three ordered path sets).
Mock/live: fully synthetic typed fixture exercising the
actual product Journal/derived-store code paths in a
private 0700 tmp tree; no real GPU/model/parity/rights/
Ready touched. No claim about this report's future
push/CI.

## Documentation impact

No README/STATUS/docs/TESTING/T16/manifest change: this
is the order's explicit canonical test-only setup
correction; behavior, governance accounting and product
contracts unchanged. The one unit-file deviation from
frozen N21 is recorded here and retained in future
selective integrations. Report within 8,192 UTF-8 bytes.

## DHA and boundaries

Order Decision: NONE; no consequential candidate; no
CRIT append. No source/vector/rights/Ready/model/GPU
grant; no snapshot/parity/CLI integration; no main merge,
no 008, no tag/deploy/release, no nested agents, no other
consumer, no FIFO reread/replay, no model/profile/client
change. Preserved: human Qwen/A100 profile/auth, all prior
immutable orders/reports/Root records, M10/K, both L
test-only exceptions, all other N21 bytes, pyproject,
dependencies, law, CRITICAL, inert gateway/capture drafts.

## Limitations and remaining work

PARTIAL: whole 007 remains PARTIAL; actual BGE
UNRUN/UNQUALIFIED; the integrated corpus pipeline is
inert synthetic software — no real BGE execution, no FP16
qualification, no physical drain, no snapshot publication.
Report-head CI PENDING/UNOBSERVED at publication; this
report does not certify its future push/CI. PR 9 remains
OPEN, auto-merge off; Root alone reviews, accepts and
advances.
