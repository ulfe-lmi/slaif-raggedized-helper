# OAP Coding Report — 009-ar

Identifier: 009-ar
Result: COMPLETE
Repository: ulfe-lmi/slaif-raggedized-helper
PR number: 11
Branch: oap/009-evaluation-baseline
Base branch: main
Implementation head SHA: 1a22705471754590f4d0e1a13f5ff526291d7da6
Report publication commit: SELF

## Work and scope

Exact Root FINAL order 009-ar (AMEND_EXISTING_PR
on PR 11, round base
43946c4c2df83d91370e4024d7186b65cc64a986,
the exact failed 009-aq report head whose
exact required hosted run 44893468946
attempt 1 concluded failure: three OAP
success, both Products (Python 3.12 and
3.14) fully ran 3,438 unit tests (ordered
1,440 + 1,998) and 1,000 integration
nodes with the same two failures, main
5a7b41cc512cf883b5b2cb92d87554b4d24e685b).
Commits pushed before this report:

1. Transcript commit
   26628c0eaa1d6af7fd86bd64fed9885c8c281c71,
   sole parent
   43946c4c2df83d91370e4024d7186b65cc64a986,
   exactly two transcript objects committed
   byte-exact before any implementation
   change: oap/orders/009-ar-stage-loop-
   gold-fixture-repair.md (5,927 B,
   SHA-256
   9f59473d9637a86a01bd0de201a8803d194a43e55fa9a96777072dbc12dfa0c4)
   and oap/active (exactly 7 B `009-ar`
   + LF, SHA-256
   8f2c8f967563b3e648bc177af759c5d380599403eec80e772d2a6e2d077a4375).
2. Implementation commit
   1a22705471754590f4d0e1a13f5ff526291d7da6,
   sole parent
   26628c0eaa1d6af7fd86bd64fed9885c8c281c71,
   exactly one path:
   tests/integration/test_current_cohort_
   stage_loop_composition.py (34,548 B
   git blob
   3c9d28d4d521de9e38ee2bd22cd129f6719e4079,
   SHA-256
   2d6449c20b0346624b818696cfc01804b35b9c8b9e9342902f8ca7a3d520d09b,
   -> 40,211 B git blob
   25ae39f3b7919128614a27d2b239f5e7b76d90fa,
   SHA-256
   42f03df1d533d616c50cc379923d49824e75092392782419e4aa926860d9c090).

## Changed behavior

The existing whole-declared-Gold-batch gate
(`text_evaluation_gold_binding._gate`,
251-353) authenticates the whole held
membership by the genuine unavailable
partitions but refuses the declared batch
before any Gold bundle opens whenever a
declared entry's partition is unavailable
under the effective case scope or the
whole-dataset atoms are not covered by
the declared entries.  With the complete
native three-bundle declaration the
genuinely withheld corpus-two member b is
declared and refused while the same
actual raw original pin still holds it,
so both exact 009-aq native suites
refused the first current Gold case:

- FAILED
  tests/integration/test_current_cohort_
  stage_loop_composition.py::test_stage_
  loop_positive_two_cases_match_legacy_
  dispatch -
  slaif_raggedized_helper.source_cohort_
  runner.CohortRunnerError: cohort runner
  refused
- FAILED
  tests/integration/test_current_cohort_
  stage_loop_composition.py::test_stage_
  loop_generation_change_after_first_case
  - assert False is True

(the mutation witness's same-wire change
was never published because the loop was
refused before the second CASE_PIN).  The
native h1/h2 preflight denial passed in
the same run.

This round corrects only the owned
stage-loop native synthetic fixture: the
stable h1/h4 and mutation witnesses now
form one test-local projection to the
genuinely admissible synthetic Gold batch
(`_admissible_gold_batch`), following the
already proven Gold witness
(`test_current_gold_dispatch_composition.
py` 317-416, case (c)): b is resolved
from the actually retained membership and
its corpus scope, its bundle ID is
excluded from the declared Gold, and
every one of its revision/extraction
spans is projected out of the entire
declared five-case dataset, pruning only
the resulting emptied alternatives and
requirements, reassembled with the exact
existing canonical JSON assembly and
source fixture.  The h1/h4 case scopes
and questions, the five dataset cases,
the six projected Gold atom occurrences
and a/c as the two declared Gold bundles
are preserved (asserted by the helper
against the admitted projection); the
same actual raw original pin keeps b
present and genuinely unavailable under
the selected policy (asserted against the
genuine unavailable partitions); the
separate h1/h2 denial keeps the exact
original full declaration and its
refusal.  Gold selected-read and
source-bundle counts are recomputed from
the actual declared two IDs in both
stable cases and the mutation (case
reads and bundle work take two declared
bundles; dataset_gold_occurrences 7 ->
6); the legacy stage compares against the
same projected dataset and Gold IDs.  The
true final stage and outer selected
reads, the 59 stable and 30 mutation raw
directory forecasts, the actual
processor and receipt assertions and the
precise original raw pointer/custody are
preserved unchanged.  A bounded test-
local diagnostic for an unexpected
refusal shows only the existing content-
free progress and fixture aggregate
counts.  The exact three native nodes
and the actual same-wire generation
publication at the real second CASE_PIN
after first-case completion are
preserved.  No production byte changed.

## Acceptance evidence

1. Reconciliation verified: PR 11 is the
   exact unique open non-draft PR (state
   OPEN, mergeable) with head branch
   oap/009-evaluation-baseline at the
   exact failed report head
   43946c4c2df83d91370e4024d7186b65cc64a986
   and base main (remote refs/pull/11/
   head and refs/heads/oap/009-
   evaluation-baseline both
   43946c4c...); remote main is
   5a7b41cc512cf883b5b2cb92d87554b4d24e685b,
   matching the order; local HEAD equaled
   the exact base and the working tree
   was clean except the strategy
   activation (oap/active exactly
   `009-ar` + LF and the new untracked
   order file).  Protected automation is
   unchanged: no .github, config,
   worker_profiles, oap/bin,
   oap/governance, oap/templates,
   oap/prompts, pyproject.toml or
   uv.lock byte differs in the working
   tree, and no such path is in any
   round commit.  The exact original
   witness file from the receiving index
   was byte-exact at the base (blob
   3c9d28d4..., digest
   2d6449c2... equal to the 009-aq
   record).  The order's Architecture
   SHA256 equals the received
   ARCHITECTURE.md and its Governance
   SHA256 equals the received
   oap/governance/MANIFEST.json.  The
   exact two transcript paths were
   committed first, byte-verified; only
   the named witness file followed.
2. Exactly one test-only path; all 131
   production files under src/ are byte-
   identical to the base (git diff of
   src/ against
   43946c4c2df83d91370e4024d7186b65cc64a986
   empty; RUN4).  No production edit,
   current scope or ACL relaxation,
   partition/reader bypass, manifest,
   workflow, documentation, dependency/
   lock, fixture source module or test
   inventory change: the three added
   imports reference only existing
   modules and fixtures (
   provenance_records,
   supplied_policy_eligibility,
   test_source_cohort_runner_composition
   canonical assembly), and the three
   witnessed node names are unchanged.
3. Local proofs all exit 0 (exact
   commands and raw streams below):
   319 exact focused existing units
   (269 stage focus + 50 legacy grade),
   the ordered three hosted collect-only
   nodes collected (the four-file
   collect lists 17 tests: the three
   exact new nodes plus the inherited
   encoder-producer, raw-hybrid and
   source-bound support CI witnesses),
   scoped one-file one-core Ruff, exact
   full production file preimages byte-
   identical, and two fresh physical
   runner-first and encoder-first import-
   origin probes (ORIGINS_OK).  No local
   native execution; the three hosted
   nodes were only collected locally.
4. Expected at the exact report head:
   all five jobs and every required step
   pass, both Products ordered 1,440 +
   1,998 units and exactly 1,000
   integrations (997 prior + three new),
   no skipped/failed evidence; that gate
   is PENDING at publication, and native
   evidence is PENDING before
   publication as the order declares.

## Verification

Environment and exact commands as
recorded in the fresh mode-0700 scratch
/dev/shm/oap-009ar-proof.Kef88y
(commands.txt, 2,351 B, SHA-256
89f44b5a77708c72797a88cafb647c94dc509da5dadd92be791594e4c5d44c47):
pre-existing canonical physical venv
(Python 3.14.4, pytest 8.4.2, ruff
0.17.4) and physical canonical src; -o
addopts= -p no:cacheprovider with the
exact indexed files,
OPENBLAS_NUM_THREADS=1,
PYTHONDONTWRITEBYTECODE=1,
PYTHONPATH=src, separate TMPDIR/basetemp
(separate private 0700 basetemp
children), taskset -c 0 with
RAYON_NUM_THREADS=1 for Ruff, and
timeout -k 5 120 prlimit --cpu=60
--as=1073741824 for every proof
process.  No dependencies installed, no
local native execution, no unchanged
retry.

1. RUN1 the 319 focused existing units
   (test_query_embedding.py 51,
   test_source_cohort_runner.py 54,
   test_raw_hybrid_search.py 15,
   test_private_policy_request.py 45,
   test_private_policy_pin_eligibility.
   py 53, test_source_bound_stage_loss.
   py 51, test_evaluation_program.py
   50) - real exit 0; raw output
   run1.log (421 B, SHA-256
   0103da37bf33f000fc89c8f9569a7f404dbcf1e6ec7975312fc62f189b471f51):
   319 passed in 10.21s.
2. RUN2 one bounded four-file collect-
   only (test_current_cohort_stage_loop_
   composition.py, test_current_cohort_
   encoder_producer_composition.py,
   test_raw_hybrid_search_composition.
   py, test_source_bound_support_ci_
   composition.py) - real exit 0; raw
   output run2.log (1,884 B, SHA-256
   8483b37d02b9c694800c8502239aa5c6aef3a6ea2e31c432d712831e748e32b8):
   17 tests collected in 1.21s,
   including the three exact ordered
   node names (test_stage_loop_positive_
   two_cases_match_legacy_dispatch,
   test_stage_loop_unavailable_
   declaration_refuses_without_work,
   test_stage_loop_generation_change_
   after_first_case).  Collection proves
   the corrected file is import- and
   collection-clean; it does not
   execute the hosted witnesses.
3. RUN3 one scoped one-file one-core
   Ruff on the corrected witness file,
   taskset -c 0 with RAYON_NUM_THREADS=1
   - real exit 0; raw output run3.log
   (19 B, SHA-256
   82b3e6a6c090a57601d22943bd23fca9218d1031dbe5a7b754092f9a156b4f18):
   All checks passed!
4. RUN4 the exact full production file
   preimages: git diff of the complete
   src/ tree (131 files) against base
   43946c4c2df83d91370e4024d7186b65cc64a986
   empty, and the full working-tree
   status showing only the three ordered
   round paths - real exit 0; raw
   output run4.log (546 B, SHA-256
   6e69eeb62456d855285089846a923b53ab06cfd2f6533ff40647b44298df4ebe).
5. RUN5/RUN6 two fresh physical import-
   origin probes, one process per order
   (runner-first and encoder-first,
   origin_probe.py 1,876 B, SHA-256
   49d41e0e99435b96a23fe246ad99b9664e4ec17c460c0f050a65a0e5260ba52c):
   the corrected witness's production
   dependencies (source_cohort_runner,
   query_embedding,
   cpu_embedding_worker,
   embedding_tokenizer,
   private_policy_capture,
   private_policy_payload,
   private_policy_pin_eligibility,
   private_policy_request,
   provenance_records, raw_hybrid_search,
   raw_snapshot_catalog,
   source_bound_ranking,
   source_bound_stage_loss,
   supplied_policy_eligibility,
   text_evaluation_dataset,
   text_evaluation_gold_binding,
   evaluation_program) all resolve
   physically to the canonical repository
   src in both import orders, and the
   corrected working-tree SHA-256 equals
   the exact post-state digest
   42f03df1...; both real exit 0 with
   ORIGINS_OK; raw streams
   run5-runner-first.log (104 B,
   SHA-256
   d3dc9defdcc2e02a315e770f44e47950fb589b434ef9d16ceb828ec1df3440f2)
   and run5-encoder-first.log (105 B,
   SHA-256
   a70ebbda70a378774a7d67a112865b9116db7941e250f37ee2495d379caa8f88).

Original failure evidence (hosted,
exact failed report head
43946c4c2df83d91370e4024d7186b65cc64a986,
CI run 44893468946 attempt 1, job logs
fetched through the GitHub API):
conclusion failure; OAP tests (Python
3.12/3.13/3.14) all success; Product
tests (Python 3.12, job 136814051908)
and Product tests (Python 3.14, job
136814052005) failed at the "Integration
test suite (owned loopback HTTP/SSE)"
step with the same two FAILED lines
quoted under Changed behavior; unit
steps in the 3.12 Product log recorded
1440 passed and 1998 passed.  New exact
node names: the three node names are
unchanged (identical to the 009-aq
record); the only behavioral deltas are
the projected declaration (two declared
Gold bundles, six Gold atom
occurrences, recomputed Gold selected-
read and source-bundle counts) and the
bounded unexpected-refusal diagnostic.

First-attempt record (procedural
deviations, preserved): the host /tmp
tmpfs was inode-exhausted (100% inodes,
ENOSPC on any write) by an unrelated
parallel lane before any proof ran, so
all scratch material went to the ordered
fresh 0700 /dev/shm scratch from the
first command; the CI log fetch first
failed only for the same /tmp cache
reason and was repeated against the
/dev/shm scratch.  Each deviation is
environmental, was corrected before the
final clean runs, and no product byte
was changed for any correction.  The
recorded raw logs are the final clean
runs.

Mock/live distinction: all fixtures,
roots and policy material are synthetic
and operator-owned; the three hosted
nodes are hosted-only compositions over
real fixtures and the real
admission/selection/pin/encoder/stage
machinery with the trusted synthetic
delegates, and were only collected,
never executed, locally.  The unit
focus, collect-only, lint, preimage and
origin proofs establish no hosted
outcome, no baseline, no native or
real-model result; no live model,
credential, data, network, GPU or
hardware was touched.  No claim is made
about this report's future push/CI; the
separate post-publication receipt
records the remote facts observed after
push, and the strategic review records
the hosted outcomes at the exact report
head.

## Documentation impact

No documentation change, as ordered.
The actual whole-declared-Gold-batch
contract and the synthetic projection
are explained in the scoped test helper
(`_admissible_gold_batch` docstring and
witness comments) and in this report.
No product documentation, STATUS.md or
docs/ path changed.

## DHA and boundaries

Order Decision: NONE; no critical
register entry appended or read.  No
consequential candidate is reported:
the hosted refusal is a fixture-versus-
gate interaction exactly diagnosed by
the order and repaired within the
ordered test-only scope, with the
h1/h2 negative witness and all
production behavior preserved.
Preserved: the existing venv and
physical canonical source, all 131
unchanged receiver objects byte-exact,
the prior 009-aq report and its recorded
hosted history byte-exact, the
protected automation, the unrelated
parallel work, and all unrelated
repository state; scratch artifacts
preserved in the fresh 0700 /dev/shm
scratches.  No new dependencies, live
model, corpus, credentials, service,
hardware, deploy or release activity.

## Limitations and remaining work

Hosted proof is PENDING: the fresh exact
report-head gate (all five jobs and
every required step, both Products at
ordered 1,440 + 1,998 units and exactly
1,000 integrations per Product: 997
prior + three new) has not run at
publication; native execution of the
three stage-loop witnesses is treated as
pending until that hosted proof.
Representative baseline NOT_RUN; whole
009 PARTIAL; no production or deployed
activity.  Grade program execution,
named CLI, publication or safe
delivery, baseline claims, release and
further guarded composition remain
separate later ordered scopes.  Nothing
in this report certifies this report's
own future push or checks; the separate
post-publication receipt and the
strategic review record those facts.

No merge performed, no auto-merge
enabled, no PR recreated; PR 11 remains
open and non-draft with the two new
commits and this report-only child as
its head sequence.
