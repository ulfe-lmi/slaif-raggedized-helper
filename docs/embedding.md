# Embedding pipeline — objective 007 (current: 007-a codec + 007-b source space)

Objective 007 (embedding pipeline) is **PARTIAL** after the 007-a and 007-b slices.
007-a integrates the exact reviewed bounded vector codec and the reproducible NumPy 2.5.4
runtime dependency; 007-b integrates the reviewed source-bound raw retrieval
representation/batch software and the published BGE-M3 checkpoint inventory/encoder-space
software. Together they establish no encoder execution, no CPU query path, no resumable
owned GPU batches and no qualification contract. Objective 007 remains PARTIAL until
those are implemented and reviewed. No self-advance to 008 or main merge.

## 007-a slice: bounded normalized FP32 codec (integrated)

- Source: `src/slaif_raggedized_helper/vector_codec.py`, byte-identical (exact Git blob
  `00a83165`, SHA-256 `13a92389`) to the reviewed local candidate implementation
  `01a362b1` (candidate report commit `31bbb862`, report SHA-256
  `8a119b2c5f7f1912aefdb9c8db308df40fc3007858f7ba2ff2079b118dd258d3`), transferred by
  Git object reads only. The candidate descends from future 008 ancestry; only the four
  indexed codec blobs (plus unit/composition tests and the API doc) were transferred.
  No 008 source, history, orders or reports entered this repository or branch.
- API: `encode(matrix, policy=Policy())` / `decode(data, expected_sha256, policy=Policy())`
  over a strict NPY 1.0 subset: little-endian FP32, C-order, shape `(rows, 1024)`, finite
  rows with L2 norm within the fingerprinted tolerance (max 0.0001; no normalize-on-read),
  bounded UTF-8 header dictionary validated by constrained AST (never evaluated), no
  `np.load`/`np.frombuffer`/`np.dtype`/pickle before full header admission, exact payload
  length, no trailing bytes, input-free `CodecError('vector codec refused')`.
  No file or network I/O; the returned matrix is a read-only view over immutable bytes.
- Policy ceilings (software bounds, not measured capacity): 20,000 rows, 82,000,000
  container bytes, 512 header bytes, 20,480,000 elements/work units, 5,000 ms cooperative
  deadline. The fingerprint is SHA-256 over sorted compact JSON of all fields.
- API contract doc: `docs/parallel/vector-codec-api.md` (immutable reviewed bytes).
- Tests: `tests/unit/test_vector_codec.py` (20 cases) and
  `tests/integration/test_vector_codec_composition.py` (1 case), unchanged reviewed
  bytes; synthetic owned fixtures only, no network/keys/GPU/model download.

## NumPy runtime dependency (bounded, first app dependency pin)

- `pyproject.toml` adds the exact runtime pin `numpy==2.5.4`; `uv.lock` carries the
  resolved 2.5.4 sdist/wheel set with SHA-256 hashes. No other locked package version
  changed.
- Observed artifact metadata (installed dist, not assumption): `Requires-Python: >=3.12`,
  `License-Expression: BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0`. The full
  transitive license/SBOM/notice audit (objective 018) remains OPEN; this is not a
  license clearance and no allowlist exception was created.
- Installs from the locked environment on Python 3.12 and 3.14 (product CI legs) without
  any developer `PYTHONPATH` shim; the installed app imports the codec normally.

## Space vs execution, typed storage

- The codec binds neither encoder, row map, embedding space, snapshot, filesystem
  publication nor execution parity: container/payload hashes identify bytes only. The
  shared embedding space (BGE-M3 1024-dim, CLS pooling, L2 normalization, pinned
  model/tokenizer/precision per A13/A18) and the CPU-query/GPU-encode execution split
  remain execution scope: the 007-b `admit` software now provides the v1 space
binding, but no execution is implemented.
- Storage is typed: normalized FP32 vectors; the reviewed store contract admits a 128-row
  (128×1024) member of 524,416 bytes in a durable roundtrip and refuses the 20,000-row
  81,920,128-byte frame against the 64 MiB member cap; 128 job refs are 24,492 bytes and
  the 129th is refused. Full corpus support is expected through future multiple bounded
  batches; the store cap is not raised and no scope was silently reduced. These are
  measured facts from the reviewed batch-capacity interop observation
  (`oap/reviews/007-batch-capacity-review.json`), not qualification.

## 007-b slice: raw retrieval representation and published checkpoint space (integrated)

Merged into the 007 branch as two root-reviewed local candidates, `--no-ff`, in order:
representation batch tip `05257d03` (implementation `4914fe54`, report SHA-256
`8a5e1065`), then published checkpoint format tip `d3836042` (implementation
`2900feaf`, report SHA-256 `fb74619d`). All twelve indexed files hold the exact
forecast Git blobs/SHA-256 (oap/reviews/007-b-components.json,
oap/reviews/007-b-integration-forecast.json); no 008 ancestry entered.

- Source-bound raw retrieval representation
  (`src/slaif_raggedized_helper/retrieval_representation.py`, blob `21f82c1a` /
  SHA-256 `681bf514`): `build`/`build_many` revalidate the whole ingestion bundle
  against the trusted original store (one validation per batch), select 1..128
  unique chunk IDs, join source title, nonempty heading path and original text
  with the fixed `\n\n` separator, and count each final text through ONE native
  tokenizer session (role `bge_representation`, backend 0.21.4) with full receipt
  admission (artifact SHA, backend, revision, preprocessing, input digest,
  mode/serialization). Preflight bounds: 100,000 codepoints / 200,000 request
  bytes per text; batch policy 128 items / 1,000,000 codepoints / 4,000,000
  escaped request bytes; any failure refuses the entire batch with input-free
  `RepresentationError`. Scope records provenance only; token counting is not
  encoder execution.
- Published BGE-M3 checkpoint inventory and encoder space
  (`embedding_artifacts.py` blob `3d07335b` / `f9f52ece`; `embedding_space.py`
  blob `93bc9dcf` / `2cf63b8d`): `verify_artifacts` admits a caller-selected
  manifest (schema 1 legacy safetensors set; schema 2 adds exactly
  `checkpoint_format` with fixed names `model.safetensors` /
  `pytorch_model.bin`) plus the protected local tree: strict UTF-8 JSON,
  duplicate-key/`auto_map`/nonfinite refusals, symlink-free component opens,
  streaming 64 KiB hashing of sizes/digests, pre/post-read signature recheck,
  XLM-RoBERTa/1024 CLS/8192/normalize module semantics, 30 s cooperative
  deadline, input-free `ArtifactRefused`. Weights are hashed bytes only: no
  deserializer, no torch import, no model load. `admit` binds the verified
  inventory, checkpoint weight digest and tokenizer to the v1 identity policy
  (BAAI/bge-m3, CLS, normalize, 1024 dimensions, identity preprocessing,
  backend 0.21.4) and derives a path-free `space_id`; expected IDs are
  configuration, not approval, license or provenance.
- Legacy and format compatibility: schema 1 inventory IDs remain equal to the
  pre-007-b verifier (witness compares the old source at commit `b83c1ba7` with
  the current module; ID `c46798c1...`); schema 2 IDs differ by format+schema.
  The pinned public layout evidence
  (oap/reviews/007-public-checkpoint-layout.json) records upstream BGE-M3
  revision `5617a9f6` publishing `pytorch_model.bin` (2,271,145,830 bytes, LFS
  SHA `b5e0ce34...`), not safetensors: metadata-only evidence, no weight
  download, no license clearance, no freshness or authorization claim.
- Documented doc delta (the only indexed-byte exception for 007-b):
  docs/parallel/embedding-artifacts-api.md now cites the versioned
  `oap/reviews/007-public-checkpoint-layout.json` instead of the private
  strategic audit path (+6 bytes); all other merged API doc bytes are
  unchanged.
- Focused tests (no developer `PYTHONPATH`; approved native fixture runtime
  `SLAIF_NATIVE_TEST_ROOT=/home/janezp/.local/share/uv/python/cpython-3.12.15-linux-x86_64-gnu`,
  `SLAIF_NATIVE_TEST_PACKAGES=/tmp/raggedized-root-native-setup-b-6cd8bebe0a/packages`,
  `SLAIF_NATIVE_TEST_PYTHON=python3.12`; PDF routes
  `PDF_TEST_RUNTIME` same 3.12 root /
  `PDF_TEST_PACKAGES=/tmp/raggedized-root-pdf-setup-20ca62cd48/lib/python3.12/site-packages`):
  `uv run --isolated --locked --offline --python 3.14 pytest
  tests/unit/test_retrieval_representation.py
  tests/unit/test_embedding_artifacts.py tests/unit/test_embedding_space.py -q`
  plus each standalone integration file
  `tests/integration/test_retrieval_representation_composition.py`,
  `test_embedding_artifacts_composition.py`, `test_embedding_space_composition.py`.
  Root witnesses re-run unchanged: `/tmp/raggedized-root-batch-boundaries.py`
  (SHA-256 `004064b0`), `/tmp/raggedized-root-artifact-json-boundary.py`
  (`f94d4d4f`), `/tmp/raggedized-root-artifact-trace-privacy.py` (`dfa36035`),
  `/tmp/raggedized-root-schema1-compatibility.py` (`a576e7db`). Store caps
  (64 MiB member / 96 MiB aggregate / 16 members) and native session 20 s /
  2 s request caps unchanged; a 20k corpus uses future multiple bounded
  batches.

## Remaining 007 work (not implemented this round)

CPU FP32 query path and CPU exact dot-product search against admitted spaces;
the resident actual encoder (model execution, a reviewed locked weights-only
loading policy, execution precision fingerprints); resumable owned GPU encode
batches with bounded resource telemetry; snapshot/manifest binding of vectors,
row maps, ACL and space fingerprints; query/GPU precision qualification (FP16
vs FP32 cosine/ranking/Recall@k); typed normalized durable batches wired to
the store; and all artifact/encoder/execution/auth gates. A future CPU worker
requires PyTorch >= 2.10.0 per the current weights-only advisory; no unsafe
fallback. Live authorization remains NONE; no model weights, inference, GPU,
services, credentials, private corpus, release or deploy in this slice.

## Evidence status

007-a codec behavior is proven by the owned synthetic suite and the unchanged
root witness (`/tmp/audit_007_vector_witness.py`): writer interop, immutability,
12 malformed frames refused before materialization, Latin-1 comment refused
where NumPy accepts it, zero forbidden-call intercepts. 007-b behavior is
proven by the merged reviewed suites (representation, artifact and space
unit/composition) and the four unchanged root witnesses (batch boundary
preflight refusals, positive receipt regression with AST guard-removal catch,
UTF-16/surrogate JSON boundary refusals, dynamic path trace privacy,
old-reader schema 1 equality). The root-accepted local candidate reviews
(oap/reviews/007-representation-batch-review.json,
oap/reviews/007-published-format-review.json) are immutable provenance, not
current CI or Root approval of this integration. Real qualification remains
NOT RUN (U04/U07 relevant).
