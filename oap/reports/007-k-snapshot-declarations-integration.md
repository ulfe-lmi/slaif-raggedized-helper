# OAP Coding Report — 007-k

Identifier: 007-k
Result: PARTIAL
Repository: ulfe-lmi/slaif-raggedized-helper
PR number: 9
Branch: oap/007-embedding-pipeline
Base branch: main
Round base commit: 41b093f5a3961048e9637b85869f8b5cd8567e9b
PR main base: 11badc7782bed326995d400f5532b63399b91fbd
Transcript commit: 206334927ec80203001146571486f9e7332c08b5
Implementation head SHA: 16559d585f425202acd4f60d55c701ad2812f8a9
Report publication commit: SELF

## Work and scope

Order 007-k (FINAL, DHA NONE, AMEND_EXISTING_PR) executed in the
ordered THREE-commit topology: (1) transcript-only 2063349
(sole parent = round base 41b093f): the exact Root FINAL order
(SHA-256 1755eb69a63dbea62c1617bdfeba934d7a7e48482be0fdeb007e1a1378d60a5d),
active `007-k\n` LF, the FOURTEEN sanitized Root records and the
exact index (oap/reviews/007-k8-root-records.json), all
SHA-256-verified against the strategic audit index before commit;
(2) implementation 16559d5 (sole parent 2063349): the EIGHT
frozen snapshot declaration codec/test/API/design files
byte-exact from the two exact source commits
b7a2b520ac543d3e78080aa163047b112e0b579f and
09fe0d5e02e01b514378facadb7d50cca12ef471 (oap/reviews/
007-k8-snapshot-components.json, 47,707 B; every path
re-verified at HEAD for blob + SHA-256 + size) plus the scoped
current docs (README.md, STATUS.md, docs/embedding.md,
docs/UNCERTAINTIES.md; TESTING.md with ONLY T16 updated,
T1..T15 byte-unchanged; oap/governance/MANIFEST.json measured
hash update only, routine 49,999/50,000 B). No
merge/cherry-pick/rebase/reset/stash/clean; the held parent K13
index (audit/007-k-components.json) was never used; no
workflow/CI-step/helper/lock/requirements/pyproject/law/
architecture/CRITICAL change.

## Acceptance evidence

1. Exact topology and invariance: 17 paths (1 M active, 1 A
   order, 15 A records/index) in 2063349; 14 paths (6 M docs,
   8 A) in 16559d5; the base-to-head diff is exactly these 31
   paths; the I fifteen files, J fourteen files, all three
   locks, pyproject/dependencies/locks, H helpers/fixtures/CI,
   source books/ARCH/law/CRITICAL are byte-unchanged.
2. Core codec: closed bounded canonical ASCII schema 1 with
   strict types, duplicate keys, paths, fields, counts, size and
   cross-reference checks, fixed analyzer/normalization
   vocabulary, ordered unique lists, 4,096-row / 128-partition /
   258-file / 96 MiB format bounds (bounds, not measured
   throughput) and a derived noncircular snapshot ID over the
   frozen core bytes.
3. Row-map codec: exact 8-header/17-row schema, canonical data,
   bare canonical representation IDs, immutable outputs,
   global/partition ordinals, sort and uniqueness, shared
   batch/bundle consistency, nonreused batch rows; canonical
   complete partition subsets (header/global ordinal/source/
   batch refs, no snapshot ID); bind freshly parses both byte
   inputs and checks exact descriptor size/hash/header/count/
   partition/subset/active-not-withdrawn/corpus-execution set.
4. Focused local checks at the implementation head (observed;
   each 1 GiB AS / 30 s CPU / 120 s wall, threads 1, no
   bytecode): 50 core+row-map units (9 manifest + 41 row-map,
   ONE process, distinct basenames, explicit PYTHONPATH)
   0.48 s exit 0; ruff "All checks passed!" (host ruff panics
   under RLIMIT_AS; ran wall-bounded uncapped; canonical CI
   lint is the uncapped gate); compileall exit 0; OAP scaffold
   41 tests OK; check_state ACTIVE 007-k exit 0; --help exit 0;
   doctor example exit 1 with honest SECRET_ABSENT + 3x
   MODEL_UNQUALIFIED.
5. GitHub CI at implementation head 16559d5: run 43200113662:
   ALL 5 jobs / 78 steps SUCCESS (observed 2026-11-12 ~10:32
   UTC; OAP 3.12/3.13/3.14 10 steps each, Product 3.12/3.14 24
   steps each; none missing/skipped/pending/cancelled).

## Verification

Exact commands: prlimit --as=1073741824 --cpu=30 timeout 120
env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src
OMP/OPENBLAS/MKL/RAYON/NUMEXPR_NUM_THREADS=1 .venv/bin/python
-m pytest tests/unit/test_raw_snapshot_manifest.py
tests/unit/test_raw_snapshot_rows.py (50 passed);
.venv/bin/ruff check src tests (all checks passed);
compileall -q src exit 0; python -m unittest discover -s
tests/oap (41 OK); oap/bin/check_state.py --repo-root .
(ACTIVE 007-k exit 0); raggedized --help (0) and doctor --config
config/examples/example-config.json (1). CI: gh run view
43200113662 --json jobs (5 jobs / 78 steps SUCCESS at 16559d5).
Machine header IDs were prepublication-validated with
oaplib.metadata + oaplib.commit_id (bare full 40-hex literals
matching actual Git facts); parent facts are stated in this
body prose only. Mock/live: synthetic declared bytes only; no
real source, payload, vector, term, rights, model or GPU was
touched. No claim about this report's future push/CI; a
separate post-publication receipt records those observed
facts.

## Documentation impact

README.md, STATUS.md, docs/embedding.md, docs/UNCERTAINTIES.md
add concise current-state entries linking the exact API/review
records; TESTING.md T16 only (T1..T15 byte-unchanged);
oap/governance/MANIFEST.json carries the measured TESTING.md
hash update (the order-pinned Governance SHA256 predates this
authorized measured update); CONTEXT-BUDGET.md unchanged
(TESTING.md still 17,448 B; routine 49,999/50,000).

## DHA and boundaries

Order Decision: NONE. No consequential candidate reported; no
CRIT append. No source/vector/rights/Ready/model/GPU grant; no
snapshot directory, loader, publication, retention or
atomic-CAS work. No main merge, no 008, no tag/deploy/release,
no nested agents, no other consumer started, no FIFO bytes
reread. Preserved: human Qwen/A100 profile/auth, I/J files, H
helpers/fixtures/CI, all locks, pyproject, law, source books,
CRITICAL.

## Limitations and remaining work

PARTIAL: pure declared-format codecs only; a declaration hash,
a bind pass or a validation-passed declaration is not
source/vector/rights/normalization/publication/retention or
Ready proof. The legacy dense_index.DenseIndex needs a new
source-verified adapter (prefix conversion insufficient). The
held parent K13 plan and the parallel parent-single-init /
native-token-acquisition work remain unintegrated; the parent
reinit defect is under separate repair. No
security/license/parity/hardware/heldout/visual/ICA/full-MVP
closure. PR 9 remains OPEN, auto-merge off; Root alone
reviews/accepts/activates next.
