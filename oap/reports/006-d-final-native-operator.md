# OAP Coding Report — 006-d

Identifier: 006-d
Result: PARTIAL
Repository: ulfe-lmi/slaif-raggedized-helper
PR number: 8
Branch: oap/006-native-extraction-and-chunking
Base branch: main
Base commit: 4977186d3ddbd2259f78590b29c0364fe26eb1fb
Implementation head SHA: 62fc63ca4d99b38d30e531e1fd5421c1de53b508
Report publication commit: SELF

## Work and scope

Order 006-d (FINAL, DHA NONE) on PR 8 (main 4977186). Round start
334ef7d committed the strategic bytes unchanged (order e0d3eb3f,
active 006-d, 006-c root review e4f98f1f, component index 871656cd;
root re-verified). Two ordered local --no-ff merges, each forecast
clean with git merge-tree against the actual parents, merged trees
equal to the recomputed forecasts: 18d1d6c (334ef7d+b2d274c, tree
bec0606a) and 065f25a (18d1d6c+b3ac81b, tree c12577b5). All sixteen
accepted source blobs plus the unchanged corrected PDF parser/worker
match the root component index. Implementation commit 62fc63c: docs
and governance only (docs/ingestion.md, README, STATUS, TESTING T15,
UNCERTAINTIES, benchmarks/ingestion-count-storage.md T15,
CONTEXT-BUDGET 49017/50000, MANIFEST re-hashes). No src/, .github/,
dependency or model/profile change; NO app patch for the reproduced
PDF gap (isolated PAR-006-PDF-STRUCTURE-A owns it).

## Acceptance evidence

1. Two exact merges/index source blobs/unchanged corrected PDF
   parser+worker verified (independently root-verified). Store D
   bounded read
   retry: changed attempt discarded, at most four fresh re-admissions
   under the existing deadline, only stable bytes hash-checked;
   security/stat/hash/FD/fsync/member-first/post-commit semantics
   preserved; explicitly NOT universal convergence.
2. Full typed text/PDF bundle, publisher, semantic fresh loader,
   profile and installed chunk+inspect present. Focused actual runs
   (owned private CPU tokenizer backend, isolated PDF worker): 25
   CLI/service tests PASSED 37.68s (tests/unit/test_chunk_cli.py,
   test_ingestion_prepare.py, tests/integration/
   test_chunk_cli_composition.py); 84 Store tests PASSED 0.64s; the
   six combined extraction/count integration suites (49 cases) PASSED
   28.53s, no skip/fallback; exit 0/1/2, no_native_chunks +
   source_status partial truth, known published ID on later failure,
   idempotent retries and the cooperative 180s budget asserted.
3. Focused local checks + ruff/compileall/diff/governance/console all
   exit 0 (41 OAP scaffold OK; check_state ACTIVE 006-d 49017/50000;
   raggedized --help exit 0; doctor example exit 1 with
   MODEL_UNQUALIFIED x3 + SECRET_ABSENT). Required CI run 43082584764
   at EXACT implementation 62fc63c: ALL FIVE jobs SUCCESS (OAP
   3.12/3.13/3.14 check IDs 130738668656/130738669017/130738669123;
   Product 3.12/3.14 130738669136/130738669198). Current report-head
   0b6e51b CI 43079404016: 5/5 SUCCESS. Known 006-c race CI
   43076681862 superseded by the Store D fix (all four witnesses
   pass).
4. Docs: installed usage/profile/backend references, safe overview,
   statuses/counts/exits, no-native visual truth, known published ID,
   retries, 180s cooperative budget, component budgets, full semantic
   bundle vs opaque store, source approval vs auth; explicit
   four-read-attempts-not-universal-convergence; contrary 157,312-byte
   timings/refusal and 019 OPEN preserved; routine 49017/50000 UTF-8;
   exact model tokens UNMEASURED.
5. PARTIAL: whole-006 native coverage cannot pass until the bounded
   D0 causal repair (architecture 9.2/9.3) of the root-reproduced
   reduced-policy PDF table header-relationship loss integrates in a
   later 006 continuation: a 23-all-text PDF table under a VALID
   reduced policy (target 12 / soft 20 / representation 80 / pair 100
   / reserve 8) yields eight chunks in which only the first retains
   the actual column header while every source code point, anchor and
   tail are preserved (header-relationship loss, not dropped text; no
   default-512 failure claim; PAR-006-PDF-STRUCTURE-A, coordination
   006-d-pdf-coverage-coordination.json sha256 9717eb1b). All
   remaining non-006/model/domain/hardware/license/auth/visual/ICA
   gates are honest.

## Verification

At 62fc63c (devhost, DEV backends): the evidence 2 pytest commands
(84/25/49 passed as recorded); uv run ruff check src tests,
python3 -m compileall -q src tests, python3 -m unittest discover -s
tests/oap, python oap/bin/check_state.py --repo-root . and git diff
--check all exit 0. The four independent /tmp root witnesses
(link-race, closed-FD, deadline, corruption) all exit 0 unchanged
against the merged module. All inputs synthetic owned fixtures;
native route is REAL local tokenization of toy artifacts (no
deployed-model or inference-parity claim); PDF route is the real
006-a worker parse; live/model/GPU/corpus authorization NONE. No
claim about this report's own future push or CI.

## Documentation impact

docs/ingestion.md 006-d section (semantic bundle/publisher/fresh
loader/profile/operator, four-read semantics, residual gap); README/
STATUS 006-d entries; TESTING T15 + benchmarks T15; UNCERTAINTIES
006-d block (U06 narrowed software-only, 019 OPEN, U07 unchanged,
real qualification NOT RUN); CONTEXT-BUDGET 49017/50000 + MANIFEST
re-hashes. Historical reports untouched.

## DHA and boundaries

DHA NONE; CRITICAL.md untouched. Preserved resources: strategic
round-start bytes unchanged; candidate histories intact (no
reset/clean/stash/pick); all other MANIFEST-listed files
byte-identical. No merge performed: PR 8 OPEN, base main, no
auto-merge, no tag/release/deploy.

## Limitations and remaining work

- Criterion 5 PARTIAL as above: reduced-policy PDF table
  header-relationship loss; isolated causal repair pending review and
  integration in a later 006 continuation.
- Whole-006 acceptance, 019 and all real qualification NOT RUN; no
  numeric 007, no self-assigned next work.
