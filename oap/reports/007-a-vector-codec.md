# OAP Coding Report — 007-a

Identifier: 007-a
Result: PARTIAL
Repository: ulfe-lmi/slaif-raggedized-helper
PR number: 9
Branch: oap/007-embedding-pipeline
Base branch: main
Base commit: 11badc7782bed326995d400f5532b63399b91fbd (verified origin/main; 006 merge PR #8)
Implementation head SHA: 1f637ce3da442af2300808ca75f30866f0d1156c
Report publication commit: SELF

## Work and scope

Order 007-a (FINAL, DHA NONE, CREATE_NEW_PR): first bounded 007 slice; whole
007 stays PARTIAL. New single branch from actual main 11badc7. Commit
5251ce5 committed the exact strategic bytes unchanged (active 007-a, order
02536d2d, 006-resolution e3787d36, 006-e-review e6565d0e,
007-vector-codec-source-index e6222f03, 007-vector-codec-component-review
9b13124c, 007-batch-capacity-review edb61147; read from the strategic
workspace, none authored). Implementation 1f637ce: four codec files as
exact indexed Git blobs via Git object reads from reviewed candidate
31bbb862 (implementation 01a362b1; report SHA-256 8a119b2c provenance
only): vector_codec.py 00a83165/13a92389, test_vector_codec.py
6a930a6d/d4311ed5, test_vector_codec_composition.py 866d330a/a38bb02c,
vector-codec-api.md 600f4f9c/eb1c191a (blob/sha256). No 008 ancestry,
source, orders or reports transferred; candidate histories not merged,
reset, cleaned or stashed. pyproject.toml adds numpy==2.5.4; uv.lock
gains only NumPy sdist/wheel entries (75 lines; all other locked versions
unchanged). Docs: new docs/embedding.md; README/STATUS/TESTING(T16)/
UNCERTAINTIES updates; CONTEXT-BUDGET 49942/50000 plus MANIFEST re-hashes
(TESTING.md, CONTEXT-BUDGET.md only). Nothing else changed.

## Acceptance evidence

1. Single 007 branch/PR from actual accepted main; Root record commit,
   implementation, then this SELF report. All four codec paths hold the
   indexed blobs+SHA256 (git rev-parse/cat-file verified). Reviewed
   behavior: strict bounded numeric NPY subset, read-only copied bytes,
   shape/dtype/finite/norm/input-hash admission, error privacy, no
   normalize-on-read, no unvalidated deserialization, no
   file/network/model side effect (20 unit + 1 composition cases).
2. NumPy 2.5.4 installs from the updated lock on required Python 3.12 and
   3.14 without developer PYTHONPATH: local uv sync --locked (3.14.4) and
   uv run --isolated --locked --offline --python 3.12 (wheel fetched once
   under the order's express PyPI allowance, then offline); CI clean legs
   pass. Observed dist metadata: Requires-Python >=3.12,
   License-Expression BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0.
   018 license/SBOM audit OPEN; no allowlist exception, no unreviewed
   upgrade, no heavy backend.
3. Actual codec tests and the UNCHANGED witness
   /tmp/audit_007_vector_witness.py (SHA-256
   d9efd9c02b7250c6d2575d0ab87101a07d843141a1673a4c7f9aa5f37952e675;
   inspected first: owned 2x1024 fixtures, 12 malformed frames, NumPy
   writer interop) exit 0 on both Pythons against CURRENT canonical
   source: container 694fdbf4f3665888855d2540d7b3ded3f1a099bf0e6689af4cf66d8ea04a1ca5,
   payload de8161462d57804a7765091178fc11add449cbceacc44ed3d88d01fcca1c91a8,
   length 8320, writer_equals_codec True, malformed_cases 12,
   intercept_counts all zero, huge_frame
   4b53d3edab0e12bf52f4ad8b67030b077a98fdb41cb4cb24642477aad1529fa7,
   canary_frame
   c88b410601439dc25d774159444f9ec6d1a84a8793572664a8b64264f8c360d1,
   latin1 NumPy-accepts/codec-refuses
   f389dd4bf500c242be6679c41fd9ccca57327aee4edc325d47906822a22f163c.
   Count is the exact codec selection: 21 cases (not the old 29, which
   included 008 dense tests; none imported).
4. Full current suites/gates at exact implementation: local tests/unit
   912 passed (48.69s), tests/integration 555 passed (327.70s) under
   approved SLAIF_NATIVE_TEST_*/PDF_TEST_* DEV backends (OPENBLAS/OMP
   threads 1); ruff, compileall, diff --check exit 0; OAP scaffold 41
   tests OK; check_state exit 0 (ACTIVE 007-a, manifest consistent,
   49942/50000); console --help 0, doctor example 1 (honest issues). CI
   run 43112136624 at exact head 1f637ce: ALL FIVE required jobs SUCCESS,
   every step success (OAP 3.12/3.13/3.14 jobs 130830672350/130830672313/
   130830672270; Product 3.12/3.14 jobs 130830672226/130830672080). No
   deselection/skip/fake/cancel. This report's future CI not asserted.
5. Docs describe PARTIAL 007 codec software only: no CPU-resident
   encoder, resumable GPU batch, model or parity claim. Measured store
   facts kept separate from typed row mapping/model proof (128 raw rows
   524,416-byte roundtrip; 20k frame 81,920,128 bytes refused at 64 MiB
   member cap; 128 job refs 24,492 bytes / 129 refused). Query/GPU
   precision qualification and artifact/encoder/execution/auth gates OPEN.
6. Exact Root bytes, source books, law, architecture unchanged; routine
   UTF-8 context 49942/50000, MANIFEST consistent; exact model tokens
   UNMEASURED. Result PARTIAL for whole 007; no next objective, no
   self-merge, no real runtime claim.

## Verification

Commands: uv sync --locked; pytest codec unit (20 passed)/composition
(1 passed); uv run --isolated --locked --offline --python 3.12 pytest
(21 passed) and witness (exit 0); witness on 3.14 (exit 0); full
tests/unit (912) and tests/integration (555) with approved DEV backends;
uv run ruff check src tests/unit tests/integration; compileall;
unittest discover -s tests/oap (41); check_state; console help/doctor.
Mock/live: synthetic owned fixtures; native/PDF routes are real local DEV
execution on toy artifacts; live model/GPU/corpus authorization NONE.
No claim about this report's future push/CI; the separate
post-publication receipt verifies remote facts.

## Documentation impact

New docs/embedding.md (canonical 007 slice, dependency + observed license
expression, space-vs-execution, typed storage, remaining work); README
007-a paragraph + 006 merged fact; STATUS current state to 007-a / main
11badc7; TESTING T16 (budget-bound); UNCERTAINTIES 007-a observation;
CONTEXT-BUDGET 49942/50000; MANIFEST re-hashes. Historical 006 reports
untouched.

## DHA and boundaries

DHA NONE; CRITICAL.md untouched. Strategic round bytes byte-identical and
committed unchanged; candidate 31bbb86/01a362b and report retained as
separate provenance only; all other MANIFEST-listed files unchanged. No
merge: PR 9 OPEN on main, no auto-merge, no tag/release/deploy, no
model/profile/weight/service/credential/corpus change.

## Limitations and remaining work

- 007 PARTIAL: shared encoder definition, CPU FP32 query path, resumable
  owned GPU batches, snapshot/manifest binding, query/GPU precision
  qualification not implemented; Root dispatches same-PR continuations.
- Codec bounds are software limits, not capacity/quality proof; store
  facts are measured bounded facts, not qualification.
- NumPy 018 full transitive license/SBOM/notice audit OPEN; allowlist
  unchanged.
