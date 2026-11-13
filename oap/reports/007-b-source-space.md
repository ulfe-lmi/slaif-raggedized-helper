# OAP Coding Report — 007-b

Identifier: 007-b
Result: PARTIAL
Repository: ulfe-lmi/slaif-raggedized-helper
PR number: 9
Branch: oap/007-embedding-pipeline
Base branch: main
Base commit: 11badc7782bed326995d400f5532b63399b91fbd (verified origin/main; 006 merge PR #8)
Implementation head SHA: d0601a74486d7c23021773a686cd4ea931b23c0d
Report publication commit: SELF

## Work and scope

Order 007-b (FINAL, DHA NONE, AMEND_EXISTING_PR) executed as the explicit
same-order recovery after the single control consumption (receipt
control-consumed-007-b; no resignal, no report replay, no added readers).
Commit c4e1963 committed the exact strategic bytes unchanged: active 007-b,
order (4ec2ecfb) and six Root records (efcc2464, c6f29053, 6e6f3c8c,
68a7ef3a, a3e61e16, 19036fb6) copied byte-identical from the strategic
workspace. Then two clean --no-ff merges in order: candidate 1 tip 05257d03
(implementation 4914fe54, report SHA-256 8a5e1065) and candidate 2 tip
d3836042 (implementation 2900feaf, report SHA-256 fb74619d). At the merges, all twelve indexed files held the exact
forecast Git blob/SHA-256 (the only later change to an indexed file is
the documented +6-byte reference correction); merge trees agree with the
forecast plus only the committed Root-record files. The pushed
delta is exactly 61 files; no 008 code or history transferred. d0601a7 is
docs/governance: the single permitted indexed-byte exception
(embedding-artifacts-api.md: private audit/ path to versioned
oap/reviews/007-public-checkpoint-layout.json, +6 bytes, documented),
stale whole-006-open README sentence reconciled to the merged fact, T16+T17
consolidated (236 to 230 bytes) with detail in docs/embedding.md,
CONTEXT-BUDGET 49936/50000, MANIFEST re-hashes TESTING.md and
CONTEXT-BUDGET.md only.

## Acceptance evidence

1. Exact ordered merges/parents as instructed; existing codec/deps
   unchanged; no separate PR or duplicate implementation. The 61-file
   delta equals forecast deltas plus Root records plus allowed docs.
2. Focused suites (no developer PYTHONPATH; uv run --isolated --locked
   --offline --python 3.14; approved SLAIF_NATIVE_TEST_*/PDF_TEST_* 3.12
   fixtures): unit 95 (representation 25, artifacts 48, space 22) plus
   standalone integrations 9 in separate processes (3/1/5). The four
   unchanged Root witnesses exit 0 on 3.12 against current canonical
   (hashes 004064b0, f94d4d4f, dfa36035, a576e7db): 21
   selection/policy refusals before the validator, faithful positive
   receipt regression and AST guard-removal CAUGHT_DID_NOT_RAISE with
   source unchanged (sha256 681bf514); 3/3 UTF-16/surrogate JSON
   refusals; no canary path in formatted traces; old-reader schema 1 ID
   c46798c1 equals current, schema 2 ID ffe98f95 differs by
   format+schema. Existing codec focused regression 21 green.
3. Full local at exact head: tests/unit 1007 passed (48.92s),
   tests/integration 564 passed (326.42s) under DEV backends with
   OPENBLAS/OMP threads 1; ruff, compileall, diff --check clean; OAP
   scaffold 41 OK; check_state exit 0 (ACTIVE 007-b, manifest
   consistent, 49936/50000); console --help 0, doctor example 1
   (honest issues).
4. CI run 43120729838 at exact d0601a7: ALL FIVE required jobs SUCCESS,
   every step success (OAP 3.12/3.13/3.14 jobs 130860208917/
   130860208907/130860208816; Product 3.12/3.14 jobs 130860208791/
   130860208429). No deselection/fake/cancel-as-pass. 007-a report CI
   43114524779 (b15e56e) terminal success recorded before this push.
   This report's future CI not asserted.
5. Docs distinguish original source/scope from rights, expected
   inventory/config from provenance/license/physical runtime, and
   representation IDs from encoder/execution IDs. Pinned layout evidence
   (oap/reviews/007-public-checkpoint-layout.json): upstream BGE-M3
   revision 5617a9f6 publishes pytorch_model.bin 2,271,145,830 bytes /
   LFS b5e0ce34, not safetensors — metadata only; no weight download or
   license clearance. Store 64MiB/96MiB/16 caps and native 20s/2s caps
   unchanged; a 20k corpus uses future multiple bounded batches. No 128
   throughput, new model/query/hardware or ICA claim. Exact model tokens
   UNMEASURED.

## Verification

Commands: focused pytest per file (95/9), each standalone integration in
its own process (3/1/5); the four witnesses via uv run --isolated
--locked --offline --python 3.12 python under the approved runtime;
isolated 3.14 codec regression (21); full tests/unit (1007) and
tests/integration (564) with -u PYTHONPATH and DEV env; uv run ruff
check src tests/unit tests/integration; compileall; git diff --check;
unittest discover -s tests/oap (41); oap.py check (exit 0); console
help/doctor. Mock/live: synthetic owned fixtures; native routes are real
local DEV execution on toy artifacts; live model/GPU/corpus
authorization NONE. No claim about this report's future push/CI; the
separate post-publication receipt verifies remote facts.

## Documentation impact

README (006 merged fact plus 007-b paragraph), STATUS (current slice
007-b), TESTING (consolidated T16 within prior bytes),
docs/UNCERTAINTIES (007-b observation), docs/embedding.md (actual
integrated APIs, source hashes, schema 1/2 compatibility, pinned layout,
remaining scope), docs/parallel/embedding-artifacts-api.md (single
reference correction, +6 bytes), CONTEXT-BUDGET 49936/50000, MANIFEST
re-hashes. Historical reports/orders unchanged.

## DHA and boundaries

DHA NONE; CRITICAL.md untouched. Strategic bytes committed
byte-identical; candidates preserved as separate histories through the
authorized merges (no reset/clean/stash/force). No merge: PR 9 OPEN on
main, no auto-merge, zero unresolved threads at head; no tag/release/
deploy; no model/profile/weight/service/credential/corpus change. FIFOs
untouched in this recovery; this is the first 007-b response, sent once
after remote report verification.

## Limitations and remaining work

- 007 PARTIAL: resident actual encoder (model execution, reviewed locked
  weights-only loading policy, execution precision fingerprints), CPU
  FP32 query path, resumable owned GPU batches, typed normalized durable
  batches wired to the store, snapshot/manifest binding, query/GPU
  precision qualification.
- Raw .bin byte hashing proves no deserializer safety; a future CPU
  worker requires PyTorch >= 2.10.0 per the current advisory, no unsafe
  fallback.
- Candidate reviews/records are immutable provenance, not current CI or
  Root approval; full ICA/MVP/019/domain/rights gates remain open.
