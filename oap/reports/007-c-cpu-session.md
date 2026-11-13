# OAP Coding Report — 007-c

Identifier: 007-c
Result: PARTIAL
Repository: ulfe-lmi/slaif-raggedized-helper
PR number: 9
Branch: oap/007-embedding-pipeline
Base branch: main
Base commit: 11badc7782bed326995d400f5532b63399b91fbd (verified origin/main)
Implementation head SHA: cef832317989ef2ba933692e27eb38d994c820f2
Report publication commit: SELF

## Work and scope

Order 007-c (FINAL, DHA NONE, AMEND_EXISTING_PR) executed after the single
control consumption: no resignal, no added readers, no FIFO reread.
Topology from round base cdf3125: cc43381 committed the exact strategic
bytes unchanged (active 007-c, order 18ff5e55, eight Root records
d45b211e/c775ec3f/9a789623/f2134ebc/e7d50f1f/bf92cf36/1d649e58/9a1797e4,
byte-identical from the strategic workspace); 26490ac is the ONE --no-ff
merge of exact candidate a7fb1bf (implementation cb439c15, immutable SELF
report SHA-256 a895b132), parents cc43381+a7fb1bf, tree 3785400e equal to
the merge-tree of its actual parents; cef8323 is docs/governance only.
Pushed delta: 21 indexed files exact (oap/reviews/007-c-components.json)
plus 14 lane orders/reports, all additions, no 008 ancestry (common base
d383604; all ten 008 branch tips verified non-ancestors); existing
source/tests/deps and all Root records unchanged. No cherry-pick/rebase/
force/reset/clean/stash.

## Acceptance evidence

1. Exact candidate second parent, expected first parent and actual
   merge-tree match; all 21 indexed blobs exact (blob + SHA-256);
   existing representation/artifact/space/codec/deps unchanged; Root
   order/active/records byte-identical after the merge; only authorized
   007 history; no source/test patches beyond the exact merge.
2. Integrated session composes staging (double admission, pinned parent,
   inode-verified cleanup), actual native token IDs before framework
   construction, ALL 1..128 text/native receipt validation before ONE
   ordered CPU CLS forward, fixed FP32 normalization
   (cls-l2-f64-fp32le-d1024-eps1e-12-tol1e-4-v1) and provenance separate
   from encoder identity (EncodedBatch). Trusted framework fakes only;
   actual owned native fixture. Oversized-selection refusal stays bounded
   (peak 1245 bytes, no unbounded tuple copy), invalid runtime yields
   zero framework events, renewal/reverse-cleanup/guard semantics
   unchanged; not authorization/model/parity proof.
3. Focused at current canonical: five unit files 24/21/26/41/4 = 116
   (tokenizer under the approved 3.12 native fixture env); each of the
   five standalone integrations (1 each) in its own env -u PYTHONPATH
   process under SLAIF_NATIVE_TEST_ROOT/
   /home/janezp/.local/share/uv/python/cpython-3.12.15-linux-x86_64-gnu,
   SLAIF_NATIVE_TEST_PACKAGES=/tmp/raggedized-root-native-setup-b-6cd8bebe0a/
   packages, SLAIF_NATIVE_TEST_PYTHON=python3.12. The two unchanged Root
   witnesses (SHA-256 8d6cbe2c, b32c48d9) re-run on 3.12 exit 0: bounded
   peak, empty framework events, sole-cause-suppression AST mutation
   caught, source unchanged. 007-a/b regression green: 95 unit + 3/1/5
   integrations + codec 20 unit/1 integration. No genuine neural call.
4. Full local at exact cef8323: tests/unit 1123 passed (57.09s; 1007
   baseline + 116 new), tests/integration 569 passed (326.95s; 564 + 5),
   DEV backends, OPENBLAS/OMP threads 1; ruff check, compileall and
   git diff --check clean; OAP scaffold 41 OK; check_state exit 0
   (ACTIVE 007-c, 49936/50000); console --help 0, doctor example 1 with
   honest MODEL_UNQUALIFIED. CI run 43127183557 at exact cef8323:
   ALL FIVE required jobs SUCCESS, every step success (72/72; OAP
   3.12/3.13/3.14 jobs 130882126630/130882126347/130882126698, Product
   3.12/3.14 jobs 130882126895/130882126739). No deselection/cancel-as-
   pass; no claim about this report's future CI.
5. Docs make explicit the Python 3.12 worker-profile vs 3.12/3.14 app
   boundary (separate neural-worker process bridge pending), real
   native/source/math vs trusted neural fakes vs unqualified
   inference/hardware, immutable identity vs current rights/license,
   the declared worker direct pins (not a resolved transitive lock) with
   the optional lock/process bridge pending, unchanged store/native caps.
   Whole-007 PARTIAL; no new objective/PR; no merge.

## Verification

Commands: per-file pytest for the five unit files and five standalone
integrations (separate processes); both witnesses via uv run --isolated
--locked --offline --python 3.12 python with the approved runtime;
007-a/b focused suites; full tests/unit and tests/integration; uv run
ruff check src tests/unit tests/integration; compileall; git diff
--check; unittest discover -s tests/oap (41); oap.py check_state;
console help/doctor; gh run/job/step inspection for run 43127183557.
Mock/live: synthetic owned fixtures; staging/native token IDs/math are
real local DEV execution on toy artifacts; the neural framework is a
trusted fake in every test; live model/GPU/corpus authorization NONE.

## Documentation impact

README (007-c paragraph), STATUS (current slice 007-c), TESTING (T16
consolidated within its previous 230 bytes; routine preload stays
49936/50000, CONTEXT-BUDGET unchanged), docs/UNCERTAINTIES (007-c
observation), docs/embedding.md (integrated APIs, exact identities,
process boundary, real/fake/unqualified distinction, remaining scope),
MANIFEST re-hashes TESTING.md only. Historical orders/reports/reviews
unchanged.

## DHA and boundaries

DHA NONE; CRITICAL.md untouched. Strategic bytes committed
byte-identical; the candidate's immutable histories/SELF identity
preserved through the authorized merge. No merge: PR 9 OPEN on main, no
auto-merge, zero unresolved threads at head; no tag/release/deploy; no
model/profile/weight/service/credential/corpus change; no new package
installed (pyproject/uv.lock unchanged); FIFOs untouched after the
consumed control; this is the first 007-c response, sent once after
remote report verification.

## Limitations and remaining work

- 007 PARTIAL: resident real encoder (actual Torch/model execution,
  weights-only loading policy, execution precision fingerprints), CPU
  FP32 query path and dot-product search, isolated neural-worker process
  bridge and optional transitive lock, typed normalized durable batches
  wired to the store, resumable owned GPU batches, snapshot/manifest
  binding and all precision/hardware qualification.
- Byte/hash admission proves no deserializer safety, current rights,
  publisher provenance or license clearance; the declared worker pins
  (torch 2.10.0+cpu et al.) are a runtime-checked contract, not a
  resolved lock.
- Candidate/Root records are immutable provenance, not current CI or
  Root acceptance; ICA/MVP/019/domain/rights gates remain open.
