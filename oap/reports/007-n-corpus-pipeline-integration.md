# OAP Coding Report — 007-n

Identifier: 007-n
Result: PARTIAL
Repository: ulfe-lmi/slaif-raggedized-helper
PR number: 9
Branch: oap/007-embedding-pipeline
Base branch: main
Round base commit: e9ee12568fdfbfd9f122ceb3ed0d15690b4dbbfa
PR main base: 11badc7782bed326995d400f5532b63399b91fbd
Transcript commit: 96e06a07d96f15cdad21885dc0e390fe69951535
Implementation head SHA: 99249e7acf45309a641d481f4585227c22ed7775
Report publication commit: SELF

## Work and scope

Order 007-n (FINAL, DHA NONE, AMEND_EXISTING_PR) ran
transcript-first from the round base: (1) transcript
96e06a0 (sole parent = round base): exact final order,
active `007-n` + LF, 29 sanitized Root records and
both exact indices (oap/reviews/007-n-root-records.json
SHA-256 64e22fd4c5b655e4bcc45cafd690e08d2ecb14758be99b1efd5474718cf11ebb, oap/reviews/
007-n-corpus-pipeline-components.json SHA-256
7d28fbb58e4cfaf888ddc0cb60f066297f76c66e31766f040c39f1823e78d752), every record verified SHA-256- and
byte-exact before commit; (2) implementation 99249e7
(sole parent = transcript): the TWENTY-ONE byte-exact
frozen corpus-pipeline files (335,687 B from exact
source commits b0ca5a68/880dedf3/6f5b3112/bac11bee;
two deliberate production replacements, nineteen new;
zero adaptation) plus the named current docs and
measured accounting. Per the Root interim review
clarification the new 007-n summaries were condensed
to behavior/evidence/remaining gates + exact API
links; archival history, T1-T15, the 21 source files
and the 29 records are untouched. No
merge/cherry-pick/rebase/reset/stash/clean/switch, no
workflow/CI/helper/lock/dependencies/law change, no
cap raise, no nested agents or other consumer.

## Acceptance evidence

1. Topology/invariance: three sole-parent commits
after the round base; transcript touches exactly the
33 transcript paths, implementation exactly the 21
indexed paths + 6 named docs/accounting; every
preexisting product/test/API/design path outside them
byte-identical to the round base, including BOTH L
exceptions (c2b483b7/15,779 B; 275e10d3/5,179 B) and
all M10; TESTING T1-T15 byte-exact (T16 only; 17,448
B); the 21 blobs re-verified blob+SHA-256+bytes at
the implementation head.
2. Behavior at this head: four new unit modules in
one capped invocation — static parametrization
predicts 51, actual collection 51 (10+23+3+15), 51
passed, exit 0; the 13 ordered actual composition
cases each in its OWN capped process (CPU30/AS1GiB/
wall120, five threads 1, unique private 0700
basetemp): 13/13 exit 0, per-case walls 1.8-19.3 s
(handoff; selected sources; >128 chunks; remaining-
char preflight parity; byte-budget refusal before
next source load; before-model refusal pre-journal;
rowfit refusal before dispatch; changed-source
refusal; changed-launch refusal after validation;
provider refusal stops before later batch; terminal
journal stops corpus [FAILED, UNKNOWN_COMPLETION];
hostile interrupt retains producer cleanup).
3. Historical Root-observed heavy proof (5 rows/2
batches, stop, fresh-creator resume, all-COMPLETE
reuse; SELF+CHILD CPU 102.715/104.983 s wall) is
transcript record oap/reviews/
007-n-executor-heavy-proof-observed.json; NOT rerun
(no new local heavy run authorized).
4. Local gates at the implementation head: ruff
(src tests/unit tests/integration) All checks passed;
compileall -q src tests oap exit 0; OAP scaffold 41
tests OK; check_state ACTIVE 007-n exit 0;
raggedized --help exit 0; doctor on the shipped
example exit 1 (config valid / MODEL_UNQUALIFIED);
governance measured 49,999/50,000 B, manifest hashes
exact.
5. CI: no CI run exists for the report commit at
publication; required checks at the CURRENT REPORT
head PENDING/UNOBSERVED; all 5 jobs and every actual
required step (currently 78) are observed after push;
missing/skipped/pending/cancelled/failed is not
green; no bypass.

## Verification

prlimit --as=1073741824 --cpu=30 timeout 120 env
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:tests/unit:
tests/integration OMP/OPENBLAS/MKL/RAYON/NUMEXPR_NUM_
THREADS=1 SLAIF_NATIVE/GPU/CPU_V2_TEST_* fixtures
.venv/bin/python -m pytest <node> --basetemp=<private
0700>: one 4-module invocation (51 passed, exit 0)
and 13 separate per-case invocations (13/13 exit 0);
ruff; compileall; python3 -m unittest discover -s
tests/oap (41 OK); python3 oap/bin/check_state.py
--repo-root . (ACTIVE 007-n, exit 0); raggedized
--help/doctor (0/1 as asserted). Current evidence
archived by Root at audit/
007-n-author-current-evidence-observed. Harness
history, disclosed truthfully: the FIRST per-case
driver (nohup background from the coding session)
completed case 1's pytest (progress line recorded;
final summary suppressed by doubled -q; no exit
recorded) and was then killed by the session
process-group termination before writing any summary
or starting case 2; I then DELETED the whole
/tmp/007n-percase directory, so the attempt-1 case-1
log no longer remains locally and no attempt-1 exit
is recorded; a one-off FOREGROUND diagnostic run of
case 1 (validating the fixed harness; stdout kept in
the session, not file-archived) preceded a fully
detached setsid relaunch whose complete 13/13
exit-0 logs/summary ARE the current proof above. No
passing-case reruns were done for counts. Mock/live:
synthetic fixtures only — actual native 0.21.4
tokenizer worker on synthetic strings, approved
copied GPU fake/null fixture, DATA-only fake CPUv2
distributions; no real GPU, driver, Tensor, model,
parity, rights or Ready touched. No claim about this
report's future push/CI.

## Documentation impact

README.md, STATUS.md, docs/embedding.md,
docs/UNCERTAINTIES.md carry the condensed current
007-n summary (behavior/evidence/remaining gates +
exact API/design links); TESTING.md T16 only (17,448
B; T1-T15 byte-exact); oap/governance/MANIFEST.json
carries the measured TESTING.md hash; CONTEXT-
BUDGET.md unchanged (aggregate still 49,999/50,000
B). Report within 8,192 UTF-8 bytes.

## DHA and boundaries

Order Decision: NONE; no consequential candidate; no
CRIT append. No source/vector/rights/Ready/model/GPU
grant; no operational mode controller, current-
principal policy, inference CLI, snapshot/parity
integration or physical qualification supplied; no
main merge, no 008, no tag/deploy/release, no nested
agents, no other consumer, no FIFO reread/replay, no
model/profile/client change. Preserved: human Qwen/
A100 profile/auth, all locks, pyproject,
dependencies, law, source books, CRITICAL, both L
exceptions, archived H actual-38/toy/UNRESOLVED
history.

## Limitations and remaining work

PARTIAL: whole 007 remains PARTIAL; actual BGE
UNRUN/UNQUALIFIED; the integrated corpus pipeline is
inert synthetic software — no real BGE execution, no
FP16 qualification, no physical drain, no snapshot
publication. Strongest reason against merge: 21
files 335,687 B of inert software, two existing
production extensions and the new required CI cases
add review/dependency/runtime cost without
qualification. Attempt-1 per-case evidence is missing
locally as disclosed; current proof stands on the
archived second-attempt source/commands/exits. PR 9
remains OPEN, auto-merge off; Root alone reviews,
accepts and advances.
