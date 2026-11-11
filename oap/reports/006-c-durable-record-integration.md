# OAP Coding Report — 006-c

Identifier: 006-c
Result: PARTIAL
Repository: ulfe-lmi/slaif-raggedized-helper
PR number: 8
Branch: oap/006-native-extraction-and-chunking
Base branch: main
Base commit: 435e4c13c5dee83d4578e8ba1cd68eb1d781ac25
Implementation head SHA: 55dd89ee68390adf0a0a3e8441c43e322005bac4
Report publication commit: SELF

## Work and scope

Order 006-c (FINAL, DHA NONE) on PR 8 (main 4977186). Round start 668e92d
committed the strategic bytes unchanged (active, order, 006-b review,
component index 9238de5c...). Three ordered local --no-ff merges, each
merge-tree forecast clean vs the actual parent; merged trees equal the
recomputed forecasts: 8411b2f (668e92d+0761f6d, tree c324ad72), e4c10e7
(8411b2f+1b05f36, tree e397079f), eb4c3b8 (e4c10e7+f2a2ced, tree
699121b1); after the merges all nine accepted source blobs and the
corrected PDF parser/worker matched the root component index.
Implementation commit 55dd89e: the ONE combined journey test plus
docs/ingestion.md, README, STATUS, TESTING (T13/T14 condensed into NEW
docs/benchmarks/ingestion-count-storage.md), docs/UNCERTAINTIES.md,
governance (47696/50000; MANIFEST re-hashes TESTING.md,
CONTEXT-BUDGET.md). No src/, .github/, dependency or model/profile
change.

## Acceptance evidence

1. Merges/blobs/provenance as above; caps enforced: session 16,384 calls
   / 32 MB input / 4 MB output, deadline 15,000 ms native default /
   5,000 ms legacy explicit (max 15,000 ms), per-build reuse, policy v2
   exact UTF-8 SHA-256 query digest; native v1 identity and receipt
   fingerprints unchanged.
2. Stale 1025-attempt negative replaced by current-cap positives:
   7876-byte procedure (403 blocks, 81 chunks, 1,305 session calls) and
   9269-byte table (243 blocks, 25 chunks, 1,657 calls) complete with
   duplicate-free deterministic call streams; standalone Session seeded
   at 16,384 refuses the next count and reaps its owned child;
   assert_exact_block_coverage tightened to full interval union/no gap.
3. Same test gains component storage composition: records -> both
   validators -> ONE opaque derived_store container (idempotent
   publication) -> FRESH store in a NEW owned subprocess revalidating
   source against the actual OriginalStore, receipts, Registry
   chunk/neighbor re-binding, scope, coverage union, tail, roles, IDs;
   corrupted-member and altered-original refusals. An opaque load is
   NOT a trusted complete native ingestion bundle.
4. Local checks green (Verification); the ALL-five-CI-success criterion
   is NOT met: see CI below.
5. Docs and governance as in scope;
   docs/benchmarks/qualification-testing.md byte-identical.

## CI (honest)

Run 43076681862 at head 55dd89e (2026-11-11 18:19:33-18:24:06Z): OAP
3.12/3.13/3.14 SUCCESS (130718212894/130718212985/130718212790); BOTH
Product legs FAILED: 3.12 (130718214025) unit test_derived_store.py::
test_concurrent_publication; 3.14 (130718212384) integration
test_derived_store_composition.py::test_independent_processes_converge;
both StoreError "publication failed". Reproduced locally (2/120 four-way
concurrent publishes); a /tmp diagnostic copy shows: in derived_store
_put the winner's os.unlink of its stage hard link updates the shared
inode ctime, so the loser's FileExistsError fallback read sees _changed
and raises a spurious ValueError. Pre-existing race in the accepted
derived_store.py (byte-identical to C tip f2a2ced). Trusted strategic
coordination (006-c-ci-failure-coordination.json) assigns the isolated
repair PAR-006-MEMBER-STORE-D; per its scope no canonical store patch
and no rerun-only acceptance here. PARTIAL: implementation executed as
ordered; all-green CI unmet; reviewed repair integrates in the next
continuation.

## Verification

At 55dd89e (devhost, provisioned dev backends): uv run ruff check src
tests/unit tests/integration exit 0; python3 -m compileall -q src tests
exit 0; focused 16-file set 274 passed, exit 0; python3 -m unittest
discover -s tests/oap: 41 OK; python oap/bin/check_state.py --repo-root
. exit 0 (ACTIVE 006-c, 47696/50000); uv run raggedized --help exit 0;
doctor example exit 1 status issues (MODEL_UNQUALIFIED, SECRET_ABSENT).
All inputs are synthetic owned fixtures; the native route is REAL local
tokenization (bwrap/prlimit-isolated tokenizers 0.21.4 worker, toy
artifacts - no deployed-model or inference-parity claim); the PDF route
is the real 006-a worker parse; live/model/GPU/corpus authorization
NONE. No claim about this report's own future push or CI.

## Documentation impact

docs/ingestion.md current caps, representative-scale behavior and
component storage composition; NEW docs/benchmarks/
ingestion-count-storage.md (T13/T14/T14a); TESTING.md T13/T14 condensed
with pointers; README/STATUS moved to 006-c with historical entries;
UNCERTAINTIES 006-c block (U06 narrowed in software only, 019 OPEN,
U07 unchanged, real qualification NOT RUN); CONTEXT-BUDGET 47696/50000
and MANIFEST re-hashes. The observed CI race is recorded in this report
only (report commit's sole parent is the implementation head).

## DHA and boundaries

DHA NONE; CRITICAL.md untouched (critical {}). Preserved resources:
strategic round-start bytes unchanged; candidate histories intact (no
reset/clean/stash/pick); all other MANIFEST-listed files byte-identical.
No merge performed: PR 8 OPEN, base main, no auto-merge, no
tag/release/deploy.

## Limitations and remaining work

- CI 43076681862: 3/5 jobs SUCCESS; both Product legs failed on the
  pre-existing derived_store concurrent-publication race documented
  above. Isolated repair PAR-006-MEMBER-STORE-D is assigned and
  integrates in the next continuation before any all-green claim.
- Full typed ingestion bundle loader, PDF semantic value composition
  and the private installed chunk CLI remain required following 006
  work; 019 (target host/model performance) OPEN; whole-006 acceptance
  and all real qualification NOT RUN.
