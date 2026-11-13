# OAP Coding Report — 007-m

Identifier: 007-m
Result: PARTIAL
Repository: ulfe-lmi/slaif-raggedized-helper
PR number: 9
Branch: oap/007-embedding-pipeline
Base branch: main
Round base commit: 63958c436428aebfc5f58247f4eb9119740e35c6
PR main base: 11badc7782bed326995d400f5532b63399b91fbd
Transcript commit: 3cd39ce6f77540f06ec660703b0d62f31c2ea329
Implementation head SHA: c74407f10ebaf429b233a6d9f6da67a0f367e5e4
Report publication commit: SELF

## Work and scope

Order 007-m (FINAL, DHA NONE, AMEND_EXISTING_PR; order
SHA-256 ba2f3d66c43d357ddeb76cc4e53a686b6daf092e8ebdf97b51def9d9abf1143e)
ran transcript-first from the round base: (1) transcript
3cd39ce (sole parent = round base): the exact final order,
active `007-m` + LF, the SEVENTEEN sanitized Root records
and both exact indices (oap/reviews/007-m-root-records.json
SHA-256 8877b1ec398668d4f09bd07f3c2953088682f254f0753e7dc3d844e3d654e34f;
oap/reviews/007-m-bridge-plan-components.json SHA-256
c4d7540e51107e9dacd25bdccb78229ed79eac4947a6b9bba6eb6e8f5adb1eb5),
every record verified SHA-256- and byte-exact before commit;
(2) implementation c74407f (sole parent = transcript): the
TEN byte-exact frozen GPU text-bridge and source-bound GPU
plan files (95,773 B from exact source commits
a9a5ef0bcc331cffd0857257f7d6568fce63bac0 and
d100689ef5582a79a29d78e51a4c5ce860d1552c; zero adaptation)
plus named current docs (README/STATUS/UNCERTAINTIES/
docs/embedding; TESTING.md T16 only; MANIFEST.json measured
TESTING.md hash update).

The bridge (isolated_gpu_embedding.py) borrows the actual
owned GPU worker parent/PreparedLaunch/reservation and owns
only its own native TokenIDSession: native IDs never
supplied, bounded preflight before native text exposure,
full receipt validation, forward/encode to captured actual
class implementations, creator/closed/busy/fork rules,
pre-return ownership retention, cleanup priority, raw CLS
then normalized FP32. The plan (gpu_embedding_plan.py)
freshly derives complete selected rows, source scope,
independent counts and canonical identities before job
creation, predicts the selected GPU batch execution before
execution, replaces only the legacy CPU intended execution
dependency with the predicted GPU execution;
forged/detached/stale records and source changes refuse; no
truncation, replaced source proof or callback grant.

No merge/cherry-pick/rebase/reset/stash/clean; no
workflow/CI/step/helper/lock/requirements/pyproject/law/
architecture change; no cap raise; no other consumer.

## Acceptance evidence

1. Topology/invariance: two sole-parent commits after the
   round base touching exactly 21+16=37 paths (diffstat: 37
   files, +3471/−15); every path is a transcript path or one
   of the ten indexed files, the five named docs or MANIFEST;
   all preexisting product/test/API/design code outside
   those paths is byte-identical to the round base,
   including BOTH L exceptions (c2b483b7/15,779 B and
   275e10d3/5,179 B: 0-line diff); TESTING T1–T15
   byte-exact (only the T16 line changed); the ten indexed
   blobs re-verified blob+SHA-256+bytes at the
   implementation head.
2. Bridge/plan behavior: per Root clarification after the
   combined module run, EACH of the 9 bridge and 8 plan
   actual composition cases ran in a SEPARATE
   CPU30/AS1GiB/wall120 process with the five thread caps,
   unique private basetemp, archived stdout+exit: 17/17
   exit 0 (bridge walls 5.1–29.9 s; plan walls 4.9–18.6 s).
   Local-setup history, preserved and archived with exact
   exits (not product failures, no source patch, no cap
   raise): the initial whole-9-case module run was killed at
   the 30 s CPU cap (exit 137; first case passed before the
   kill); attempt-1 per-case runs failed only at the
   trusted-path setup guard (group-writable 0775 basetemp
   parent; 17 logs, each exit 1 in 0.68 s before any child);
   attempt 2 under a private 0700 parent passed 17/17.
3. Focused units: 13 (7 bridge + 2 plan + 4 normalizer) in
   one capped invocation: 13 passed in 3.06 s, exit 0.
4. Local gates at the implementation head: ruff (src
   tests/unit tests/integration) All checks passed;
   compileall -q src tests oap exit 0; OAP scaffold 41
   tests OK; check_state ACTIVE 007-m exit 0; raggedized
   --help exit 0; doctor on the shipped example exit 1 with
   config valid / readiness not_ready / MODEL_UNQUALIFIED;
   governance measured 49,999/50,000 B, manifest hashes
   exact.
5. CI: no CI run exists for these commits at publication
   (this suffix's ordering: local checks precede
   publication; no intermediate implementation CI awaited).
   Current truth at publication: PR 9 OPEN, non-draft,
   auto-merge off, base main
   11badc7782bed326995d400f5532b63399b91fbd; required checks
   at the CURRENT REPORT head PENDING/UNOBSERVED. All 5
   jobs and every actual required step (currently 78) at
   that head are observed after push; missing, skipped,
   pending, cancelled or failed is not green.

## Verification

Exact commands: prlimit --as=1073741824 --cpu=30 timeout
120 env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:tests/unit:
tests/integration OMP/OPENBLAS/MKL/RAYON/NUMEXPR_NUM_
THREADS=1 SLAIF_NATIVE/GPU/CPU_V2_TEST_* fixtures
.venv/bin/python -m pytest <node> --basetemp=<private 0700>
(17 per-case invocations, 17/17 exit 0); same env for the 13
units (13 passed); .venv/bin/ruff check src tests/unit
tests/integration (passed); .venv/bin/python -m compileall
-q src tests oap (exit 0); python3 -m unittest discover -s
tests/oap (41 OK); python3 oap/bin/check_state.py --repo-
root . (ACTIVE 007-m, exit 0); .venv/bin/raggedized --help
(exit 0) / doctor --config config/examples/example-config.json
(exit 1 as asserted). Machine header IDs are bare 40-hex
literals matching actual Git facts; parent facts are prose
only. Mock/live: synthetic fixtures only — the actual
native 0.21.4 tokenizer worker on synthetic strings and the
approved copied GPU fake/null fixture; no real GPU, driver,
Tensor, model, parity, rights or Ready touched. No claim
about this report's future push/CI; a separate
post-publication receipt records those facts.

## Documentation impact

README.md, STATUS.md, docs/embedding.md and
docs/UNCERTAINTIES.md carry the exact integrated
components, the two preserved L exceptions with exact
hash/size, whole-007/MVP PARTIAL, actual BGE
UNRUN/UNQUALIFIED, and the frozen synthetic fake CPU/GPU vs
real native tokenization distinction; TESTING.md T16 only
(49,999/50,000 B); oap/governance/MANIFEST.json carries the
measured TESTING.md hash. Report within 8,192 UTF-8 bytes.

## DHA and boundaries

Order Decision: NONE. No consequential candidate; no CRIT
append. No source/vector/rights/Ready/model/GPU grant; no
producer/corpus executor/controller; no snapshot
payload/publisher/selection/retention/Ready; no runtime
promotion or current rights. No main merge, no 008, no
tag/deploy/release, no nested agents, no other consumer, no
FIFO reread/replay, no model/profile/client change.
Preserved: human Qwen/A100 profile/auth, all locks,
pyproject, dependencies, law, source books, CRITICAL, both
L exceptions.

## Limitations and remaining work

PARTIAL: whole 007 remains PARTIAL; actual BGE
UNRUN/UNQUALIFIED; the GPU producer, corpus controller,
durable GPU execution and snapshot publication remain
separate local candidates, not this runtime surface;
records/fingerprints/normalized vectors are data, never
qualification. Strongest reason against merge: the
required exclusive GPU FP16 corpus-encoding path exists
only as predicted/planned software under trusted fakes — no
real BGE execution, no FP16/FP32 parity, no hardware or
model qualification, no snapshot publication; whole-007
acceptance, ICA and Root review/timing ledger remain open.
The two local setup facts (CPU-cap kill of the combined
run; 0775-parent trusted-path guard) are preserved with
exact exits under /tmp/007m-checks-attempt1-0775-parent and
/tmp/007m-checks2. H actual-38/toy/UNRESOLVED history
preserved as-is. PR 9 remains OPEN, auto-merge off; Root
alone reviews, accepts and advances.
