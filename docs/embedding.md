# Embedding pipeline — objective 007 (current: first 007-a slice)

Objective 007 (embedding pipeline) is **PARTIAL** after the 007-a slice. This slice
integrates the exact reviewed bounded vector codec and the reproducible lightweight NumPy
runtime dependency only. It establishes no encoder, no CPU query path, no resumable owned
GPU batches and no qualification contract. Numeric 007 remains PARTIAL until those are
implemented and reviewed. No self-advance to 008 or main merge.

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
  are future 007 scope and remain unimplemented here.
- Storage is typed: normalized FP32 vectors; the reviewed store contract admits a 128-row
  (128×1024) member of 524,416 bytes in a durable roundtrip and refuses the 20,000-row
  81,920,128-byte frame against the 64 MiB member cap; 128 job refs are 24,492 bytes and
  the 129th is refused. Full corpus support is expected through future multiple bounded
  batches; the store cap is not raised and no scope was silently reduced. These are
  measured facts from the reviewed batch-capacity interop observation
  (`oap/reviews/007-batch-capacity-review.json`), not qualification.

## Remaining 007 work (not implemented this round)

Shared encoder definition binding model/tokenizer/pooling/normalization and execution
precision fingerprints; CPU FP32 query path and CPU exact dot-product search; resumable
owned GPU encode batches with bounded resource telemetry; snapshot/manifest binding of
vectors, row maps, ACL and space fingerprints; query/GPU precision qualification (FP16
vs FP32 cosine/ranking/Recall@k); and all artifact/encoder/execution/auth gates.
Live authorization remains NONE; no model weights, inference, GPU, services,
credentials, private corpus, release or deploy in this slice.

## Evidence status

Codec behavior is proven by the owned synthetic suite and the unchanged root witness
(`/tmp/audit_007_vector_witness.py`): writer interop, immutability, 12 malformed frames
refused before materialization, Latin-1 comment refused where NumPy accepts it, zero
forbidden-call intercepts. Real qualification remains NOT RUN (U04/U07 relevant).
