# OAP Coding Report — 007-l

Identifier: 007-l
Result: PARTIAL
Repository: ulfe-lmi/slaif-raggedized-helper
PR number: 9
Branch: oap/007-embedding-pipeline
Base branch: main
Round base commit: 3b41a6b39d18a4805ecad253b38ffb2fc5ef130f
PR main base: 11badc7782bed326995d400f5532b63399b91fbd
Transcript commit: 8ce0f5a82fecbceb3de81336e6d050508eb591b1
Implementation head SHA: d1d3f0b032946b7babb7cc7ea53b72c1121c98a7
Report publication commit: SELF

## Work and scope

Order 007-l (FINAL, DHA NONE, AMEND_EXISTING_PR; SHA-256
faf3662ab7ca461d3b4df37b560025033229a4c48bb38d798b4d3a2707bf101e)
ran transcript-first from round base 3b41a6b: (1) transcript
8ce0f5a (sole parent = round base): the exact order, active
`007-l\n` LF, the EIGHTEEN sanitized Root records
(oap/reviews/007-l-root-records.json) and the exact components
index (oap/reviews/007-l-parent-native-components.json,
SHA-256 010d2b52080fb814dc507a8f1d9a5052a235b661360985f1808833181dfc3fa5),
SHA-256-verified before commit; (2) implementation c82e608
(sole parent 8ce0f5a): the TWENTY-THREE byte-exact frozen
owned-GPU parent/identity and native runtime-identity files
(250,571 B from exact source commits
9ac0eabd77bff77101debe9812887993e86a6803 parent 14 and
d7701a5329d825eefa2d5f7a2a58b74bc0788b10 native 9) plus scoped
current docs (README/STATUS/UNCERTAINTIES/docs/embedding;
TESTING.md T16 only, 49,999/50,000 B; MANIFEST.json measured-
hash update).

Two Root-authorized test-only exceptions, each committed
AFTER its exact Root record(s); the other 22 indexed files and
all production byte-exact at d1d3f0b (re-verified vs the
components index):
- Exception 1 (6de7bea, after addenda 1/2 records 86dafd9/
  f7a7615): native FILE unit tests/unit/
  test_embedding_native_identity.py (current 15,779 B, SHA-256
  c2b483b77c84f304ead4a6ae5c2ef27e5194c1df6ccd6adbb62992a7904a8df6;
  original 13,668 B) — an fstat device/inode size-boundary seam
  replaces the 32 MiB+1 fixture-file creation; pre-read refusal
  evidence plus one-guard-omission read-then-consistency-
  refusal control; production guards unchanged.
- Exception 2 (eb757a3, after addendum-3 records ce6db9e;
  sequencing corrected at d1d3f0b): tests/integration/
  test_cpu_embedding_session_composition.py (current 5,179 B,
  SHA-256 275e10d333555f6e02f3261449e6f9becf99e659a352ee9d4464e4837a843fd0;
  original 4,855 B /
  a45301b444da6fc6c64bd018d0d133fb97da5d992711415c16b7b40e6f635ad0)
  — observes the actual preallocated native child at the real
  subprocess.Popen.__init__ boundary (child appended BEFORE the
  fallible initializer delegation so the observation survives
  initializer failure), delegating to the captured actual
  initializer; public Popen class identity exact; production
  exact-class guard unchanged.

No merge/cherry-pick/rebase/reset/stash/clean; no
workflow/CI/step/helper/lock/requirements/pyproject/law/
architecture change; no limit raised or reset.

## Acceptance evidence

1. Topology/invariance: eight sole-parent commits after the
   round base (8ce0f5a, c82e608, 86dafd9, f7a7615, 6de7bea,
   ce6db9e, eb757a3, d1d3f0b) touching exactly 21+29+2+2+5+3+5+3
   paths; c82e608 is the initial 23-file source transfer with
   its scoped docs; every path in the six later correction
   commits is one of the two named test files, the four narrow
   docs or an exact Root record; all preexisting paths outside
   the 23 indexed transfer paths and those correction paths
   (I/J files, all locks, pyproject, H helpers/fixtures/CI,
   law) are byte-identical to the round base.
2. Both failed CIs, Root-caused and repaired test-only: run
   43209043099 (c82e608) failed ONLY the FILE unit (OSError 27
   — 32 MiB RLIMIT_FSIZE inherited from an earlier CPUv2 setup
   test in the same CI process; Root sequence proof: three
   CPUv2 setup cases pass, then the old fixture fails exact
   OSError 27); run 43217061569 (6de7bea) failed both Product
   integration steps ONLY at test_real_composition (children
   observed 0 expected 1 — the old public-class Popen
   replacement spy is refused by the integrated exact-class
   guard before any child). Root addenda 1/2/3,
   failure/sequence/causal records and the path erratum
   clarification (oap/reviews/, byte-verified) precede each
   repair.
3. Local focused checks at the implementation head (each 1 GiB
   AS / bounded CPU / wall clock, threads 1, no bytecode,
   fixture env): 112 units (23 owned-worker + 7
   worker-identity + 58 TokenID + 24 FILE) exit 0;
   compositions: parent 29 (OS-disjoint 28 as 11/7/5/5, plus 1
   new), identity OS 1, acquisition 8, query 3, isolated CPU 3,
   CPU-session 1 — all pass; FSIZE-32 MiB isolated FILE child
   24/24; CPUv2 setup (3 cases) + FILE (24) ordering proof 27
   passed; replaced-public-class Popen refusal re-proven (no
   factory call before any child); ruff "All checks passed!";
   compileall exit 0; OAP scaffold 41 tests OK; check_state
   ACTIVE 007-l exit 0.
4. GitHub CI at implementation head d1d3f0b: run 43226491920
   ALL 5 jobs / 78 steps SUCCESS (completed 2026-11-12T13:27:33Z;
   OAP 3.12/3.13/3.14 10 steps each, Product 3.12/3.14 24 steps
   each; none missing/skipped/pending/cancelled; re-observed
   via gh; frozen at audit/007-l-implementation-CI-final.json).

## Verification

Exact commands: prlimit --as=1073741824 --cpu=30 timeout 120
env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:tests/unit
OMP/OPENBLAS/MKL/RAYON/NUMEXPR_NUM_THREADS=1
SLAIF_NATIVE/GPU/CPU_V2_TEST_* fixtures .venv/bin/python -m
pytest <suite> (each exit 0); .venv/bin/ruff check src tests
(all checks passed); compileall -q src tests oap (exit 0);
python3 -m unittest discover -s tests/oap (41 OK);
oap/bin/check_state.py --repo-root . (ACTIVE 007-l exit 0).
CI: gh run view 43226491920 --json jobs (5/78 SUCCESS at
d1d3f0b). Machine header IDs are bare 40-hex literals matching
observed Git facts; parent facts are prose only. Mock/live:
synthetic fixtures only (native 0.21.4 worker on synthetic
data under hash-verified backends); no real
GPU/Tensor/model/source/vector/rights touched. No claim about
this report's future push/CI; a separate post-publication
receipt records those facts.

## Documentation impact

README.md, STATUS.md, docs/embedding.md,
docs/UNCERTAINTIES.md carry current state: the two
Root-authorized test-only exceptions with exact current
hash/size (FILE c2b483b7/15,779 B; CPU 275e10d3/5,179 B), the
two failed CIs and Root addenda 1/2/3 records; TESTING.md T16
only (routine 49,999/50,000 B); oap/governance/MANIFEST.json
carries the measured TESTING.md hash update.
Report size: Root D0 reporting amendment (audit/
007-l-report-size-D0.json, SHA-256
8ba8ab3dd0b1bf29f675b85601ddaf9db9958fe6f1f62d861ede512c9b6f514a):
"Root D0 reporting amendment: this 007-l report may use at most
8,192 UTF-8 bytes. All other order requirements apply."

## DHA and boundaries

Order Decision: NONE. No consequential candidate reported; no
CRIT append. No source/vector/rights/Ready/model/GPU grant; no
snapshot/publication/retention work. No main merge, no 008, no
tag/deploy/release, no nested agents, no other consumer
started, no FIFO bytes reread/replayed, no model/profile/
client change, no CI/limit change. Preserved: human
Qwen/A100 profile/auth, all locks, pyproject, dependencies,
law, source books, CRITICAL.

## Limitations and remaining work

PARTIAL: BGE qualification UNRUN/UNQUALIFIED; the exclusive
GPU FP16 corpus encoding path is still unimplemented; the
owned-GPU bridge/producer/controller are not part of this
frozen slice's runtime surface; the held parent K13 plan is
remediated at frozen software + fresh peer per the 007-k
records, with no human DHA waiver; H actual-38/toy/
UNRESOLVED are preserved as-is. The two test-only exceptions
remain confined to the exact Root-named files; production
guards (exact-class Popen guard, fstat size-consistency
guard) are unchanged. PR 9 remains OPEN, auto-merge off; Root
alone reviews/accepts/activates next.
