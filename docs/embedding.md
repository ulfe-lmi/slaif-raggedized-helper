# Embedding pipeline — objective 007 (current: 007-a codec + 007-b source space + 007-c composed CPU session + 007-d durable source plans)

Objective 007 (embedding pipeline) is **PARTIAL** after the 007-a,
007-b, 007-c and 007-d slices. 007-a integrates the exact reviewed bounded vector codec and the
reproducible NumPy 2.5.4 runtime dependency; 007-b integrates the reviewed
source-bound raw retrieval representation/batch software and the published BGE-M3
checkpoint inventory/encoder-space software; 007-c integrates the reviewed composed
CPU-session software (owned staging, exact native token IDs, bounded preflight before
one ordered CPU CLS forward, fixed binary32 L2 normalization) with the neural
framework exercised only through trusted fakes; 007-d integrates the reviewed durable
source-plan substrate (fresh source-bound intended CPU/FP32 plans, typed validated
batch store, per-job ownership leases and the owned atomic job journal with
output-before-COMPLETE). Together they establish no real encoder execution, no CPU
query path, no resumable owned GPU batches and no qualification contract. Objective
007 remains PARTIAL until those are implemented and reviewed. No self-advance to 008
or main merge.

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

## 007-c slice: composed CPU embedding session (integrated)

Merged into the 007 branch as ONE root-reviewed local candidate, `--no-ff`: CPU-session
tip `a7fb1bf0` (implementation `cb439c15`, immutable SELF report SHA-256
`a895b1328e7e780a81b66d3de949b311cc56d4fba5940776a4cdbac638176b94`). All twenty-one
indexed final files hold the exact forecast Git blobs/SHA-256
(oap/reviews/007-c-components.json, oap/reviews/007-c-integration-forecast.json);
the candidate histories contain 007 parallel lanes only, no 008 ancestry; the
Root transcript (order, active and records) was committed first and is
byte-identical after the merge.

- `embedding_staging.stage` (blob `958aece8` / `fc321415`): a context manager that
  performs actual source admission, copies each manifest-declared file into an owned
  0700 private directory (files 0600 during copy, 0500/0400 during use) and performs
  a SECOND actual admission of the staged copy with the tokenizer rebound to the
  staged `tokenizer.json`; both admissions must produce the same space. Pinned-parent
  no-follow checks, 120 s shared deadline (two 30 s admissions plus copy), and
  inode-identity-verified cleanup; `StagingRefused("staging refused")` is input-free.
  No weight deserialization anywhere in staging.
- `embedding_tokenizer.TokenIDSession` (`8aea18f3` / `0da386d2`) plus the data-only
  worker `embedding_tokenizer_worker.py` (`d7b716c4` / `ce0c2fc1`): one isolated
  CPython 3.12 child (1 GiB address space / 30 CPU seconds / 2 s per request / 5 s
  startup / 300 s lifetime / 1,024 calls / 32 MB input / 16 MB output) loads the
  staged tokenizer once (tokenizers 0.21.4, special tokens, no padding/truncation)
  and returns exact token IDs with a frozen receipt binding IDs and count to the
  artifact SHA-256, backend, role `bge_representation`, model revision,
  preprocessing `identity`, nonce and the SHA-256 of compact ASCII-escaped JSON
  `[text,null]`. Receipts are tokenizer-operation evidence, not authorization,
  provenance, parity or license clearance.
- `embedding_vectors.normalize_rows` (`00b1cfec` / `c69906f3`): 1-128 rows of 1,024
  exact finite binary32 floats; float64 stable accumulation; norm > 1e-12; binary32
  little-endian payload with `sha256` and policy
  `cls-l2-f64-fp32le-d1024-eps1e-12-tol1e-4-v1`. Producer provenance only: it does
  not change the encoder definition/space fingerprint and does not repair or
  validate stored vectors on read.
- `cpu_embedding_backend.CPUEmbeddingBackend` (`a2706ad7` / `cd0f4a3b`): after
  admission and closed-tree verification it loads ONE fixed XLMRobertaModel;
  `forward_cls` accepts 1-128 ordered sequences of 2-1,024 IDs and returns
  immutable raw (not normalized) FP32 CLS rows; `close()` is idempotent and a
  failed forward closes the instance. `_framework()` requires CPython 3.12 with the
  exact worker pins (torch 2.10.0+cpu, transformers 4.51.3, tokenizers 0.21.4,
  safetensors 0.5.3, huggingface-hub 0.30.2, numpy 2.2.6) checked at runtime: that
  list is a declared fixed direct-pin contract for the isolated worker profile, not
  a resolved transitive hash lock, and it is separate from the application
  dependencies (no pyproject/lock change in this slice; no new package installed).
- `cpu_embedding_session.CPUEmbeddingSession` (`589560a3` / `375472b7`): the owned
  composition. `embed`/`encode` over 1-128 exact strings (100,000 chars / 200,000
  wire bytes per text; 1,000,000 / 4,000,000 per batch) run ALL text and native
  receipt validation before ONE ordered backend forward; a nonblocking guard
  rejects concurrent/reentrant use; failures close owned resources; the native
  worker is renewed (never model-reloaded) when its budgets cannot fit the batch
  with the 2 s/row and 5 s startup margin, and a failed forward is never retried.
  `encode` returns the frozen `EncodedBatch` (normalized payload, receipts,
  `space_id`, definition fingerprint, execution fingerprint, policy ID): execution
  and policy identities are provenance separate from the embedding-space
  fingerprint.

Python version/process boundary: the canonical app runs on Python 3.12/3.14, while
the fixed CPU backend runtime check targets the isolated CPython 3.12 worker
profile. The in-process backend cannot make that 3.12 profile executable inside a
Python 3.14 application by declaration; the separate neural-worker process bridge
remains explicitly pending (future work), as do the optional transitive lock for
the worker profile and real package/model startup. The native tokenizer child is
already a separate 3.12 process under the existing isolation profile.

Real vs fake vs unqualified: staging, admissions, native token IDs, receipts and
normalization math are REAL local execution on the approved 3.12 native fixture;
the neural framework (Torch/model/forward) is a TRUSTED FAKE in every test; no
actual model, weight, GPU, network or inference evidence exists in this slice.
Admitted identities (inventory/space IDs, fingerprints, policy IDs) are immutable
byte identities: they establish neither current rights, publisher provenance,
license clearance nor deserializer safety. Ownership/trust assumptions: the caller
establishes rights and current ACL before invoking the API and must trust the
protected artifact parent ancestry and filesystem; runtime and installed
tokenizer packages remain trusted. Store caps (64 MiB member / 96 MiB aggregate /
16 members) and native session 20 s / 2 s request caps are unchanged.

Focused suites: five new unit files (21 session cases plus the backend/staging/
tokenizer/vectors suites) and five standalone integrations, each run in its own
`env -u PYTHONPATH` process under the approved
`SLAIF_NATIVE_TEST_ROOT=/home/janezp/.local/share/uv/python/cpython-3.12.15-linux-x86_64-gnu`,
`SLAIF_NATIVE_TEST_PACKAGES=/tmp/raggedized-root-native-setup-b-6cd8bebe0a/packages`,
`SLAIF_NATIVE_TEST_PYTHON=python3.12` fixture. The two unchanged Root witnesses
(`/tmp/raggedized-root-cpu-session-boundaries.py`, SHA-256 `8d6cbe2c`;
`/tmp/raggedized-root-cpu-trace-causality.py`, SHA-256 `b32c48d9`) were re-run at
the current canonical: the oversized-selection refusal peak stays bounded (no
unbounded tuple copy before the 128-row admission) and an invalid native runtime
produces zero framework-load events; the sole-cause-suppression AST mutation is
caught with the source files unchanged. API contracts:
docs/parallel/cpu-embedding-backend-api.md, cpu-embedding-session-api.md,
embedding-staging-api.md, embedding-tokenizer-api.md, embedding-vectors-api.md
(immutable reviewed bytes).

## 007-d slice: durable source plans and typed batch journal (integrated)

Merged into the 007 branch as ONE root-reviewed local candidate, `--no-ff`: source-plan
tip `2b50e658` (implementation `55ea655c`, immutable SELF report SHA-256
`cdcf15f35fc41376344d5e5a29f523cc77ccc7d19df678b6b257c6b94bb70dee`). All sixteen indexed
final files hold the exact component-index Git blobs/SHA-256
(oap/reviews/007-d-components.json, oap/reviews/007-d-integration-forecast.json); the
candidate histories contain 007 parallel lanes only, no 008 ancestry; the Root
transcript (order, active and twelve records) was committed first and is byte-identical
after the merge.

- `embedding_batch_store.publish/load` (blob `af130ee6` / `8e53be2d`): admits a bounded
  canonical UTF-8 JSON declaration (schema 1 `embedding-batch-v1`; exact root,
  seven dependency and eight row fields; 1–128 ordered rows; no floats or duplicate
  keys) plus normalized NPY vectors under the fixed 128-row codec policy, publishes
  one `vectors` member and validates a fresh read before returning the content ID.
  `load` revalidates the complete expected declaration before I/O, rereads through the
  actual `derived_store.Store` (a forged non-Store is refused by the single typed
  guard) and revalidates vectors: no normalize-on-read and no forged-snapshot
  availability. A failed publication may leave immutable orphan objects; the same
  content retries idempotently.
- `embedding_job_ownership.claim` (`bfc33a98` / `4eae9bd6`): per-job exclusive
  nonblocking POSIX flock over an euid-owned 0700 root with `sha256:` + 64 lowercase
  hex job IDs; each lease owns its file and directory descriptors, `assert_owned` at
  boundaries, idempotent sanitized close; a forked child cannot assert ownership and
  closing its inherited lease does not unlock the parent. Internal per-job concurrency
  only: no GPU ownership, ACL enforcement, durable state, retry policy or
  claim-steal semantics.
- `embedding_job_journal` (`7c5df637` / `6b3b1640`): `make_spec` revalidates a bounded
  `embedding-job-plan-v1` declaration into the existing `job_records.JobSpec` (kind
  `embedding`, no-generator-prompt policy); `Journal(root).own(plan)` takes the actual
  ownership lease over pinned 0700/0600 digest-named files, records initial PENDING
  and bounds envelopes at 524,288 bytes / depth 32 / 20,000 nodes / 64 events / 16
  unique claimed attempts. `append` is a fresh-read compare-and-set whose new envelope
  is staged exclusively, fsynced, rechecked, atomically replaced, directory-fsynced
  and freshly read: failures before replacement leave the old envelope; failures after
  can leave the new one. COMPLETE additionally requires the actual store and
  full expected plan-equal batch metadata whose container `load` freshly validates,
  binding the output refs to the loaded container/metadata digests with availability
  `verified`; `verified_output` reloads on every use. No automatic recovery, retry or
  pid-based steal; a historical verified label is not fresh proof and unsigned
  private history is not rollback-proof. A valid 64-event history can hold 16 distinct
  claims (15 complete retryable-failure cycles plus claim/running/failure), so the
  17th claim is unreachable under the 64-event cap.
- `embedding_batch_plan.build` (`b14d85d0` / `e7080dad`): from a fresh original-backed
  source bundle (one source validation) and ONE native token-counting session it
  derives the deterministic intended CPU/FP32 plan: admitted space/inventory IDs,
  definition and intended-execution fingerprints, normalized representation/batch
  policy fingerprints, and 1–128 ordered rows binding chunk/revision/extraction/
  representation IDs, rendered and input SHA-256, the observed count and the
  `embedding-source-scope-v1` scope fingerprint. CPU/FP32 is an INTENDED execution
  identity, not an observed worker profile or model runtime; a future producer must
  explicitly bind the complete planned/observed contract. `Prepared` is forgeable: no
  fresh authorization, current ACL or source proof for a later consumer; revalidate at
  the relevant boundary.

Real vs fake vs unqualified: store publication/load, flock ownership and descriptor
cleanup, journal fsync/replace/read mechanics and the native count session are REAL
local execution on the approved 3.12 native fixture; the plan declares intended (not
observed) CPU execution; no actual encoder, model, weights, GPU, network,
producer/controller or retry exists in this slice. Fault injection is software
semantics, not power-loss qualification. Store caps (64 MiB member / 96 MiB aggregate
/ 16 members), native session caps and the optional CPU profile are unchanged.

Focused suites: four new unit files (43 cases) and the four standalone integrations
(13 + 1 + 2 + 6 cases), each run in its own `env -u PYTHONPATH` process under the
approved `SLAIF_NATIVE_TEST_ROOT=/home/janezp/.local/share/uv/python/cpython-3.12.15-linux-x86_64-gnu`,
`SLAIF_NATIVE_TEST_PACKAGES=/tmp/raggedized-root-native-setup-b-6cd8bebe0a/packages`,
`SLAIF_NATIVE_TEST_PYTHON=python3.12` fixture. The eight unchanged Root witnesses
(batch-store forged-refusal and guard-causality; job-ownership boundaries,
enter-failure and interrupted-close; journal boundaries and event-bound causality;
source-plan preflight memory with bounded 2,208/2,248-byte peaks on 1,000,000-
character inputs) were re-run at the current canonical, all exit 0 with the indexed
sources byte-unchanged. API contracts:
docs/parallel/embedding-batch-store-api.md, embedding-job-ownership-api.md,
embedding-job-journal-api.md, embedding-batch-plan-api.md (immutable reviewed bytes).

## Remaining 007 work (not implemented this round)

The composed CPU-session software now exists (software contract only, trusted
neural fakes); still open: the CPU FP32 query path and CPU exact dot-product
search against admitted spaces;
the resident actual encoder (model execution, a reviewed locked weights-only
loading policy, execution precision fingerprints); resumable owned GPU encode
batches with bounded resource telemetry; snapshot/manifest binding of vectors,
row maps, ACL and space fingerprints; query/GPU precision qualification (FP16
vs FP32 cosine/ranking/Recall@k); the encoder producer/controller wiring that
drives the plans, store and journal to real execution; and all
artifact/encoder/execution/auth gates. A future CPU worker
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
current CI or Root approval of this integration. 007-c behavior is proven by the merged reviewed suites (five new unit files,
five standalone integrations in separate processes) and the two unchanged root
witnesses (oversized-selection bounded peak, invalid-runtime zero framework
events, sole-cause-suppression AST mutation caught with source unchanged).
The root-accepted local component reviews (oap/reviews/007-cpu-backend-review.json,
oap/reviews/007-artifact-staging-review.json, oap/reviews/007-normalization-review.json,
oap/reviews/007-token-ids-review.json, oap/reviews/007-cpu-session-review.json)
are immutable provenance, not current CI or Root approval of this integration.
007-d behavior is proven by the merged reviewed suites (four new unit files,
four standalone integrations in separate processes) and the eight unchanged
root witnesses (forged non-Store refusal and guard-causality, ownership
boundaries and descriptor cleanup, journal CAS/fsync/interruption boundaries
and event-bound causality, bounded preflight memory); the candidate/Root
records are immutable provenance, not current CI or Root acceptance of this
integration. Real qualification remains NOT RUN (U04/U07 relevant).
