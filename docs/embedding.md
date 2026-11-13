# Embedding pipeline — objective 007 (current: 007-a codec + 007-b source space + 007-c composed CPU session + 007-d durable source plans + 007-e CPU reference integration + 007-f cleanup/lease composition + 007-g profile source integration + 007-h runtime setup integration + 007-i resident query assets integration + 007-j GPU child/launch/assets integration + 007-k snapshot declarations integration + 007-l parent/native identity integration + 007-m bridge/plan integration + 007-n corpus pipeline integration)

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
query path, no resumable owned GPU batches and no qualification contract. 007-g
selectively integrates the reviewed CPUv2 profile/portable-fixture and corrected
GPU raw-backend candidates (CPUv2 lock selection, required v2 CI fixture, inert
raw GPU backend source). 007-i
selectively integrates the reviewed resident CPU query encoder,
the shared diagnostic-priority fixes and the packaged CPU
profile lock assets (finite model-free software; the actual
BGE remains UNRUN/UNQUALIFIED). 007-j selectively integrates
the reviewed GPU child/protocol, prepared-launch and packaged-
resource assets (finite model-free software; the actual owned
GPU parent, the new lock and the worker-identity resources
remain parallel/unintegrated). 007-k selectively integrates the
reviewed raw snapshot core/row-map declaration codecs (pure
declared-format software; they establish no actual payload,
source, vector, term, rights, normalization, publication,
retention or activation). 007-l selectively integrates the
reviewed owned GPU parent/identity and native runtime-
identity software (finite model-free software under fake/
null-namespace fixtures and the actual native 0.21.4
tokenizer worker on synthetic strings; no real GPU, driver,
Tensor, model, parity, rights or Ready). 007-m selectively
integrates the reviewed isolated GPU text bridge and
source-bound GPU plan software (finite model-free software
under synthetic fixtures and the approved copied GPU
fake/null fixture; the actual native 0.21.4 tokenizer
worker runs on synthetic strings only; no real GPU, driver,
Tensor, model, parity, rights or Ready, and no GPU
producer/controller/durable execution). Objective
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

## 007-e slice: CPU reference integration (integrated)

Merged into the 007 branch as ONE root-reviewed local candidate, `--no-ff`:
composite tip `bb6a9335` (implementation `e55bc384`, immutable SELF report
SHA-256 `60574ab8a013e6012a6ee86fc54d2711d89534900db100e8fe88695d5088c40d`).
All thirty-three indexed final files hold the exact component-index Git
blobs/SHA-256 (oap/reviews/007-e-components.json), plus the nineteen
immutable parallel history additions; the candidate histories contain 007
parallel lanes only; the Root transcript (order, active and fourteen
records) was committed first and is byte-identical after the merge.

- `cpu_execution_contract.prepare` (blob `5a365347`): shared factory that
  predicts the complete execution contract BEFORE model startup — scalar
  admission, actual model-space file verification, pinned CPU profile
  metadata plus selected code — returning a frozen `PlannedContract` with
  the canonical ASCII schema-2 record (exactly `schema`, `contract`,
  `space`, `definition`, `worker`, `normalization`, `native`, `bridge`,
  `hardware_qualification`; worker = space/definition/profile/code/policy;
  native = artifact SHA/backend/role/revision/preprocessing/policy/
  worker SHA with the fixed ID-session limits; bridge = SHA-256 of the four
  code files; hardware `unknown`), bounded to 16,384 bytes, hashed under
  the `isolated-cpu-embedding-execution-v2` domain. The actual worker
  handshake derives the same canonical bytes. Schema 2 deliberately CHANGES
  the execution identity from v1: no hardcoded old value, no silent v1/v2
  mix, while legacy space, definition and intended-CPU-FP32 fingerprints
  stay distinct and unchanged.
- `cpu_embedding_plan.build` (blob `d2f64fee`): the source-derived plan is
  unchanged except that its execution dependency now binds the COMPLETE
  predicted contract, so the journal job identity can be claimed BEFORE
  model startup; `predicted_record` and `execution_fingerprint` are
  returned next to the legacy `intended_execution_fingerprint`. A
  predicted record is not an observed handshake, authorization,
  package-file attestation, ABI or hardware qualification.
- `cpu_embedding_producer.produce` (blob `80b16513`): requires an EXPLICIT
  trusted current-authorization provider — `provider(canonical_plan_bytes,
  boundary)` freshly checks current permission for every row and purpose at
  `before_model`, `before_encode`, `before_publish`, `before_complete` and,
  on reuse, `before_reuse`, returning a stable 64-hex policy epoch or
  refusing; there is NO default permissive provider and no caller-supplied
  epoch. This is an extension point, not an implemented principal/
  current-policy store or rights attestation. The producer rebuilds the
  complete plan and predicted contract before owning the job, admits a
  fresh PENDING job to EXACTLY ONE attempt (CLAIMED then RUNNING with the
  actual owner before model acquisition), compares the observed execution
  record and fingerprint to the prediction BEFORE any source text is
  encoded, rechecks fresh source rows/texts/dependencies before dispatch,
  publication and completion, publishes and freshly loads the typed output,
  and records COMPLETE only after that real publish+load. Valid COMPLETE
  reuse revalidates the current plan/metadata/store and journal again with
  ZERO model starts. Non-PENDING and non-COMPLETE jobs are refused; no
  retry, steal, repair or exactly-once claim. A publication failure can
  leave an immutable orphan; an ambiguous journal COMPLETE may already be
  committed and is never overwritten with a failure (the journal is
  reread). While session cleanup is pending, the content-free exception
  retains an owner whose `close()` must be retried and the lease is held
  until the child and resources are drained; interrupts propagate with a
  cleanup owner; the native constructor is pre-owned, not lost on startup
  failure.
- `CPUEmbeddingWorker` (blob `b7bef979`, child `cpu_embedding_worker_main`,
  blob `96ed127c`): one resident CPU model worker under the ACTUAL bounded
  OS protocol — the parent verifies the 28 locked distribution metadata
  versions, lock hash, closed staging tree and configuration vocabulary
  before starting the child; the child repeats admission before `ready`,
  which binds space, definition, profile, policy and code fingerprints;
  every call carries a random nonce and SHA-256 of the canonical ID batch
  and the reply must bind both values plus space/profile with exact
  finite binary32 CLS rows before anything is returned; defaults/hard
  ceilings 8/128 rows, 2/2 MiB requests, 8/8 MiB responses, 120/120 s
  startup, 30/120 s forward, 3600 s lifetime, 600 s CPU, 16 GiB address
  space, 1024 calls, 32 MiB input / 256 MiB output; nonblocking deadline-
  bounded I/O; an independent owned `timeout` watchdog enforces lifetime;
  the child runs in the bubblewrap/prlimit envelope with a cleared
  environment, no network and synthetic device nodes, with finite
  shutdown and retained child ownership (no unsandboxed fallback).
  Metadata and lock SELECT a profile; they do not attest installed files
  or clear licenses.
- `IsolatedCPUEmbeddingSession` (blob `82f709d0`): enters the verified
  artifact stage, native token-ID session and fixed resident CPU worker in
  that order; all token receipts are checked before ONE CPU forward with no
  partial batch and no retry; `execution_record`/`execution_fingerprint`
  (schema 2) are separate from `intended_execution_fingerprint` and must be
  explicitly bound and compared by a consumer; native startup is owned
  before construction and a pending native cleanup retains the exact
  tokenizer and its stage; CPU startup is not attempted after native
  startup fails; the creator-PID refusal keeps the known multithreaded-fork
  warning honest — no general fork-safety claim.
- `embedding_tokenizer` (blob `933be076`) carries the native-lifecycle
  correction (pre-owned native startup, interrupt-priority and close-
  ownership fixes) reproduced and corrected in the root-accepted candidate.
- Portable synthetic CI fixture: `tests/support/
  prepare_cpu_worker_test_backend.py` (blob `3a6d093c`) acquires ONLY six
  exact hash-pinned wheels (pinned Pydantic graph plus the native
  `tokenizers` engine) and writes 22 explicitly DATA-ONLY metadata records
  under the trusted standalone CPython 3.12 runtime, then validates the
  profile inventory; there are no importable fake ML modules, no Torch/
  Transformers/NumPy model packages, no weights and no real neural calls.
  The product CI job provisions it per run on disposable GitHub-hosted
  runners with literal `SLAIF_CPU_WORKER_TEST_ROOT` /
  `SLAIF_CPU_WORKER_TEST_PACKAGES` GITHUB_ENV bindings (helper output never
  sourced); missing prerequisites fail the job — never skip/fallback/
  continue-on-error. It is a synthetic fixture, not an installed real ML
  runtime.

Real vs fake vs separately scoped evidence: worker process protocol, store
publication/load, lease/journal mechanics, native count sessions and the
CPU worker test fixture are REAL local/CI execution; the neural framework
runs only as trusted fakes in the imported suites; the separately scoped
single owned RANDOM one-layer CPU toy (old-SHA `88e788e...` evidence,
oap/reviews/007-owned-cpu-toy-evidence.json: 4 native calls/4 forwards, max
raw error 4.76837158203125e-07, equal normalized payload, ~39 s wall,
RSS/worker inter-op UNKNOWN) is old-SHA-scoped toy evidence only — not a
benchmark for BGE/quality/parity/hardware and not permission for any new
neural call; current source corrections require fresh qualification where
relevant. The actual BGE model has NOT been run. No model weights, permits
or credentials enter Git.

Focused suites: seven unit files (worker, backend setup, toy probe, plan,
producer, native tokenizer, isolated session) and the four standalone
integrations (worker, isolated, plan, producer) plus the existing native
composition, each standalone in its own `env -u PYTHONPATH` process under
the approved 3.12 fixtures (`SLAIF_NATIVE_TEST_*`, `SLAIF_CPU_WORKER_TEST_*`,
`PDF_TEST_RUNTIME`). The three unchanged Root witnesses
(`/tmp/raggedized-root-native-close-ownership.py`,
`/tmp/raggedized-root-native-interrupt-priority.py`,
`/tmp/raggedized-root-producer-lease-interrupt.py`) were re-run at the
current canonical, all exit 0 with the indexed sources byte-unchanged
(fault-injected runs included). API contracts:
docs/parallel/cpu-embedding-plan-api.md, cpu-embedding-producer-api.md,
cpu-embedding-worker-api.md, isolated-cpu-embedding-api.md,
cpu-worker-test-setup.md and docs/benchmarks/real-cpu-toy.md (immutable
reviewed bytes).

## 007-f slice: cleanup/ownership composition and cooperative device lease (integrated)

Merged into the 007 branch as TWO exact root-reviewed local candidates,
`--no-ff`, in the ordered sequence: cleanup-composition tip `985806af`
(implementation `4a929261`, whose ancestry already contains the GPU
device-lease report `692fa53b` / implementation `6c29b935`) and then
isolated-exit tip `52252484` (implementation `48aafeef`). All seventeen
indexed source/test/API files hold the exact component-index Git
blobs/SHA-256 (oap/reviews/007-f-components.json, 195,649 bytes), the Root
transcript (order, active, fourteen records plus index) was committed first
and is byte-identical after the merges, and the imported bytes are
immutable: no source adaptation, conflict resolution, cherry-pick or
history rewrite.

- `embedding_job_ownership` (blob `57cac3d7`): cleanup is finite — every
  acquired descriptor receives one close attempt even after an earlier
  attempt fails or is interrupted. An error with `cleanup_owner` retains
  the attempt history and marks the descriptor numbers as not blindly
  retriable because they may already be reused, including a same-inode
  open description; a failed unlock/close does not prove continued
  ownership, and a subsequent close on an uncertain lease refuses rather
  than claiming success. The original non-Exception interruption is
  preserved; otherwise a new cleanup interrupt outranks an ordinary
  error. Retention is not guaranteed kernel reaping.
- `embedding_job_journal` (blob `1a2f384b`): entry and cleanup make one
  finite close attempt per acquired descriptor, including temporaries,
  even after another cleanup failure; a failed close is recorded
  UNKNOWN and its descriptor number is never retried; the retained
  `cleanup_owner` records attempted resource history and any nested
  ownership cleanup owner without proving a lock is held; sticky
  uncertainty refuses subsequent close; a pre-return acquisition failure
  exposes the retained cleanup owner and propagates it to the producer's
  error even before the claim returns; ordinary public errors are
  content-free and preserve any cleanup owner; no automatic reclaim or
  retry.
- `cpu_embedding_producer` (blob `770d6c27`): the producer retains its
  actual pending native/model resource and the journal lease until the
  child and associated resources are drained; an original interruption
  is preserved, otherwise a new interruption during reconciliation or
  cleanup outranks an ordinary refusal; a pre-return low-level descriptor
  UNKNOWN is sticky (closing that owner continues to refuse and never
  retries the unknown descriptor); independent safe cleanup is still
  attempted. The existing current-provider callback, plan, receipt,
  output-before-COMPLETE, fresh reuse and ambiguous-COMPLETE semantics
  are preserved; the provider remains a trusted extension point, not an
  actual current-rights store.
- `isolated_cpu_embedding` (blob `bf968bd8`): context exit follows the
  same interrupt priority — the original body interrupt stays primary, a
  new cleanup interrupt outranks an ordinary body exception, ordinary
  cleanup errors preserve the body exception, and a failing cleanup
  escapes with a fixed note plus retained `cleanup_owner`. An
  uninterruptible kernel task cannot be guaranteed reaped.
- `gpu_device_lease` (blob `0a5ce44e`, new): a COOPERATIVE per-device
  kernel lease. The key is `schema.fingerprint` of the structured
  `gpu-device-lease-v1` object carrying ONLY the versioned host +
  physical UUID, under the actual trusted common local root; different
  jobs contend on the same key while owner incarnation identity and
  kernel exclusion come from the existing ownership module. Forked
  children cannot use the parent's lease. A close failure is sticky and
  ownership becomes unknown — descriptors are not blindly closed again,
  the same key is refused for further acquisition in this process while
  the pending uncertainty is retained, and there is no automatic
  reclaim. Cleanly closed wrappers are not strongly retained by the
  registry. This module does not manage GPU or model lifetime, grant
  inference/maintenance/service-stop permission, or exclude
  noncooperating users: a cooperative key does not prove physical
  exclusivity and does not grant runtime authority. A caller must
  independently verify the real assigned device, occupancy and current
  rights, and future workers must be drained before release; different
  roots, noncooperators and restarts are not coordinated.

Original finding and remediation: the independent producer peer review
(oap/reviews/007-f-peer-producer-b-report.json and
oap/reviews/007-f-peer-producer-b-review.json) is the original
CHANGES_REQUIRED evidence for the journal/producer cleanup composition;
the Root local remediation records (oap/reviews/007-journal-producer-
cleanup-findings.json, oap/reviews/007-f-cleanup-composition-review.json,
oap/reviews/007-f-isolated-exit-review.json,
oap/reviews/007-f-gpu-device-lease-review.json and
oap/reviews/007-f-composed-review-tree.json) are immutable provenance —
they are not a completed new ICA and not human adjudication.

Identities: the selected source hashes and complete execution
fingerprints changed naturally with the corrected cleanup/lease sources;
the predicted/observed handshake and source-job matching still work, with
no hardcoded old value; the semantic, native 0.21.4 and legacy CPU
intent identities are preserved. The legacy optional CPU profile
(Torch 2.10.0+cpu / Transformers 4.51.3) remains UNQUALIFIED and
unchanged; no new CPU/GPU profile cutover or neural permit.

Focused verification at the current canonical: six focused unit files
(105 cases: ownership 12, lease 19, journal 27, producer 11, isolated
34, plan 2) and six standalone integrations (39 cases: ownership 1,
lease 2, journal 2, isolated 3 with the retained multithreaded-fork
warning, producer 30, plan 1), each standalone in its own
`env -u PYTHONPATH` process under the approved 3.12 fixtures (producer
and plan under the lane-accepted `tests/unit:tests/integration`
PYTHONPATH). The TEN original Root witnesses
(`/tmp/raggedized-root-isolated-exit-priority.py`,
`producer-secondary-interrupt.py`, `journal-cleanup-boundaries.py`,
`producer-lease-interrupt.py`, `native-close-ownership.py`,
`native-interrupt-priority.py`, `gpu-lease-registry.py`,
`job-ownership-boundaries.py`, `job-enter-failure.py`,
`job-interrupted-close.py`) all exit 0 at the current canonical with the
seventeen indexed sources byte-unchanged before and after.

Advisory severity correction: the earlier high/medium wording on both
pins is corrected against the committed Root observation
(oap/reviews/007-legacy-fixed-route-static-observation.json): the GitHub
TorchScript advisory (GHSA-rrmf-rvhw-rf47) is rated LOW, and the
Transformers advisory list comprises four HIGH, six MEDIUM and one LOW
entries — all with UNPROVEN transitive reachability and NOT_EXPLICITLY_
INVOKED direct fixed routes on the installed pins. This finite static
observation is not package-wide safety and not a clearance.

Limitations: the finite selected fault coverage is not universal
cleanup, power-loss or hardware proof; these fixes do not guarantee
kernel reaping, restart recovery or full ICA; the existing
multithreaded-fork warning remains without any generic fork-safety
proof.

## 007-g slice: profile source integration (integrated)

Selective byte-exact integration of the two reviewed immutable
candidates — the CPUv2 alignment/portable-fixture candidate `adfc96e7`
and the corrected GPU raw-backend candidate `d7b9bdc6` — transferring
TWENTY-FIVE indexed files (oap/reviews/007-g-components.json,
278,431 bytes) by file copy, NOT branch merge: no candidate ancestry
entered, no broad history import, no source adaptation. Twenty-three
files are byte-identical to the indexed blobs at this head; the two
`worker_profiles/*/README.md` files preserve the exact candidate
prefix with only a precise current-selection note appended.

The CPU source now selects the cpu-v2 lock (`worker_profiles/cpu-v2/
uv.lock`, 38 registry distributions: Torch 2.14.0+cpu, Transformers
5.22.2, framework tokenizers 0.23.1, safetensors 0.8.0,
huggingface-hub 1.31.0, NumPy 2.5.4): the backend/worker/execution-
contract gates verify the full 38-name metadata inventory, and the
standalone integrations require the v2 fixture variables
(SLAIF_CPU_V2_TEST_ROOT/PACKAGES). The execution contract and
BEFORE-content child handshake preserve the reviewed alignment and
source-fingerprint semantics; complete source/execution/job IDs
change naturally, and a legacy (pre-cutover) COMPLETE with the old
profile/code/bridge hashes is refused reuse rather than accepted as
current identity. The legacy CPU profile, its helper, fixture and the
native 0.21.4 capsule remain intact; `test_cpu_worker_backend_setup`
keeps the legacy helper regression plus the narrowed /proc
descendant-disappearance race boundary. The required CI step
provisions the portable synthetic CPUv2 fixture (six exact wheels plus
32 explicitly DATA-ONLY metadata distributions, no importable fake ML
packages) after the existing CPU fixture provisioning, before lint,
with literal GITHUB_ENV bindings and the legacy fixture variables
retained.

The GPU raw backend (`gpu_embedding_backend`, new) admits the existing
BGE-M3 space over a local closed artifact tree under a caller-supplied
live DeviceLease and canonical physical UUID: assigned exact synthetic
device UUID byte guard before any local FP16 load, actual child/
process-owned DeviceLease assertion, bounded immutable native-ID
input, no autocast, ordered finite CPU FP32 raw CLS rows of 1024,
sticky close/owner retention and original non-Exception identity
across hostile backend_owner attachment. Before `from_pretrained`
returns there may be no captured model owner: that honest unknown
boundary is documented, with no parent-owned serialized lease and no
caller-lease release. All behavior is proven with in-memory trusted
fakes and the cooperative kernel lease only — no CUDA, driver, device
or model operation.

This order is bounded source integration, not model/runtime
qualification. The archived prior OWNED random CPU toy execution
remains historical toy evidence; the actual BGE model, checkpoint and
hardware are still UNRUN/UNQUALIFIED; the actual full-38 CPUv2
installation remains a separate PARTIAL (latest diagnostic: uv
allocation abort under the fixed 2 GiB address space, no full CLI
acceptance or neural import); the GPU profile/raw source remains
finite and inert with future owned worker/controller/physical drain
absent. The original advisory findings and unproven transitive/
security/license status are preserved; newer pins alone are no
clearance. Whole 007 remains PARTIAL; no main merge or 008.

## 007-h slice: runtime setup integration (integrated)

Selective integration of the SIX root-reviewed setup/test/API files
by file copy from the two exact candidates (3de83d4a CPU installer
arena correction, c6533838 synthetic GPU test fixture): no branch
ancestry, no source adaptation, no test weakening. The original
byte-identical transfer (oap/reviews/007-h-components.json, 70,906
bytes; all six files blob + SHA-256 + size exact at eb4739d) is
historical; per the Root CI-portability amendment 007-h-1
(oap/reviews/007-h-ci-portability-addendum-1.md), ONLY
tests/unit/test_cpu_runtime_setup_v2.py differs from that frozen
candidate (23,095 → 28,320 bytes; current SHA-256
6038a3b1766f52911f9d15b800d6fe515630b32f03cec52bca39b30ed56d1482;
current blob eabb9b419b0b6f933674580538ef5ef2c282e3a5), and the
other five files — including the production helper
tests/support/prepare_cpu_runtime_v2.py (SHA-256
226a527650083ec3324fcb783354ca47eb8b30884f0db0d3e4df6c044e6ede0c)
— remain byte-exact at this head (current six-file sum 76,131
bytes; oap/reviews/007-h-components-after-portability.json).

`tests/support/prepare_cpu_runtime_v2.py` is the fixed CPUv2
runtime installer, developer qualification tooling ONLY: the
38-wheel pinned official graph from the cpu-v2 lock (Torch
2.14.0+cpu from the exact official PyTorch CPU URL; the remaining
37 from PyPI), status/origin/length/hash and the missing-MIME
exception for the exact fixed Torch wheel only, offline
no-index/no-deps hash-required binary-only install into a new
private venv, metadata and dependency verification without any
framework import, finite owned cleanup with diagnostic interrupt
priority, atomic receipts, and `MALLOC_ARENA_MAX=1` in the
sanitized child environment (a documented glibc arena limit; it
does not increase any cap). Per-process limits are 2 GiB address
space, 120 s CPU, 600 s wall, 600 MiB payload and a 3 GiB disk
ceiling with 2.5 GiB sampled abort — sampling, not an atomic
quota. It is never run in CI (CI runs only its unit/guard tests),
it is not an implicit deployment or runtime action, and its fixed
runtime/binary host qualification does not prove generic
deployment portability. Its controlled-fake unit testing does not
authorize or constitute acquisition or installation.

`tests/support/prepare_gpu_worker_test_backend.py` provisions the
portable synthetic GPU worker fixture over a trusted standalone
CPython 3.12 runtime: six exact hash-pinned wheels (the pinned
Pydantic graph plus tokenizers 0.23.1) installed binary-only,
no-dependency, hash-required, plus 51 explicitly DATA-ONLY
metadata distributions matching the fixed GPU lock — no
importable fake ML packages, no real Torch/Transformers/NumPy,
model, CUDA or neural call. The required CI step provisions it
AFTER the current CPUv2 fixture and BEFORE lint on both product
legs (expected five jobs, 78 steps), with `set -o pipefail`, a
new direct `/tmp` target, `test ! -e` refusal, teed setup log and
literal GITHUB_ENV bindings (SLAIF_GPU_TEST_ROOT /
SLAIF_GPU_TEST_PACKAGES); helper output is never sourced or
evaluated, and no skip, fallback or continue-on-error exists. All
existing native/PDF/CPU-legacy/CPUv2 steps, variables, pins,
permissions, matrices and guard behavior are preserved.

The separate Root actual development evidence (summarized in
oap/reviews/007-h-cpu-runtime-evidence.json; public software
evidence only) supersedes the 007-g-era full-38 PARTIAL claim as
current status: a frozen full-CLI acquisition completed in
22.254 s with 252554535 payload bytes over 38 hash-verified
wheels, 38 metadata and dependency graph, all four commands exit
0, no unresolved owned children and sampled disk 2085087847 B
under 2 GiB address space / 120 s CPU / 600 s wall (sampling, not
quota); a separate actual CPU class import (Torch 2.14.0+cpu plus
Transformers 5.22.2 XLMRobertaModel) succeeded in 14.73 s with
352816 KiB RSS inside the standalone CPython 3.12 namespace,
synthetic /dev, no home, offline, under a separate 4 GiB /
30 s CPU / 120 s wall allowance. A class import is not loading
BGE weights, constructing a model, running a forward pass or
measuring query latency, parity, hardware, security or licenses.
The historical 007-g-era partial receipts remain HISTORY; the
original unknown full-CLI failure cause is not retroactively
invented. The actual BGE checkpoint/model remains UNRUN/
UNQUALIFIED; dependency/class interoperability differs from real
BGE forward, and both differ from the controlled neural fakes;
child/query parallel prototypes are not canonical here. The
legacy CPU profile/helper/fixture, the CPUv2 fixture, the native
0.21.4 capsule and the app dependencies are preserved intact.

## 007-i slice: resident query assets integration (integrated)

Selective integration of the FIFTEEN root-reviewed
query/CPU-asset files by file copy from the two exact report
commits (query 1bb40cc63bf4791631337d102ca508ef17c7bf27, CPU
assets d75baa515e1ff2ed3368442b71db2ac8ac29af50;
oap/reviews/007-i-components.json, 170,026 bytes; all fifteen
blob + SHA-256 + size exact at this head): no branch ancestry,
no cherry-pick/rebase/reset/stash/clean, no source adaptation,
no test weakening. The CPU worker file comes from d75 (query
fixes plus packaging), not the older query worker; the
corrected GPU backend, the H installer/fixture helpers, the
existing fixtures, CI, locks, requirements, worker-profile
READMEs and law are unchanged.

`src/slaif_raggedized_helper/query_embedding.py` (new) is the
private resident CPU query encoder: `ResidentQueryEncoder` owns
one `IsolatedCPUEmbeddingSession`; enter it once and call
`encode_query(text)` for each query. Query policy v1 (the
SHA-256 of the canonical ASCII JSON record in `_POLICY`)
accepts exactly a built-in nonblank Unicode string of at most
8192 characters and 32768 strictly encoded UTF-8 bytes and
passes the original string unchanged: no prefix, title,
normalization, truncation or padding. The admitted definition
must have `query_prefix=None`, CLS pooling, L2 normalization
and 1024 dimensions; the independent native 0.21.4 tokenizer
enforces the 1024 ID limit including special tokens before the
CPU forward. One actually owned CPU worker is reused across
different queries (load-once; its finite lifetime and call
limits still apply); an actual session error refuses the
instance while a malformed raw input does not consume it;
concurrent use, reuse after fork and missing/changed identity
refuse before exposure. The frozen `QueryEmbedding` carries the
immutable 4096-byte little-endian FP32 normalized payload, its
SHA-256, the admitted space and definition identities, the
intended CPU FP32 fingerprint, the actual observed execution
record and fingerprint, and the query policy ID (no query text
or token IDs); the encoder validates row/payload/digest/norm/
identity/receipt/observed-record consistency and does not
renormalize. `QueryRefused` is content-free; the inherited
session retains actual handles even on refusal and close may be
retried for pending cleanup.

The shared cleanup/diagnostic priority fixes (
`isolated_cpu_embedding.py`, `embedding_tokenizer.py`,
`cpu_embedding_worker.py`): the selected original non-
Exception interruption is preserved before any diagnostic
attachment: `add_note` and owner-attribute failures can never
replace the chosen exception (best-effort `_annotate_pending` /
`_diagnose` / `_note_cleanup`), a new cleanup interruption
outranks an ordinary operation or context-body error, and the
actual session retains its pending tokenizer/worker/staging
handles independently of any exception notes or attributes.
The historical F1/F2 failure witnesses asserting a bad
secondary are regression inputs, not passing proof; the
corrected copies are verified by the committed hostile-
diagnostic regressions and the original guard-causality
evidence.

`pyproject.toml` adds only the three reviewed force-include
lock-asset wheel mappings
(`worker_profiles/{cpu-v2,cpu,gpu}/uv.lock` ->
`slaif_raggedized_helper/_worker_profiles/...`); dependencies
and metadata are unchanged and the CPU/GPU/native locks remain
exact. The CPU worker and CPU execution contract now select the
bundled CPU v2 lock in an installed layout and refuse missing,
corrupt, symlinked or whole-bundle-missing assets even with a
matching ambient project/lock; a bounded dist-info scan (first
4096 entries) detects this package's installed distribution in
a src-named wheel prefix before admitting the fixed source-
checkout layout, which additionally requires the exact project
name and no installed metadata; no external installation-
relative lock is searched and source-checkout support is
retained. `tests/integration/test_cpu_profile_assets.py`
builds and exercises the ACTUAL wheel in an isolated private
prefix (offline, no-index, bounded 1 GiB address space / 30 s
CPU / 120 s wall), verifying RECORD/license/entry/source
identity and the installed-layout downgrade refusals.

Behavior is proven with the composed fake-framework suites
(trusted in-memory framework over actual staged artifacts,
actual native tokenizer 0.21.4 and the actual CPU isolation
protocol) and the actual offline wheel: finite model-free
software. The actual BGE model, checkpoint and hardware remain
UNRUN/UNQUALIFIED; no BGE execution, latency, parity, model
memory or hardware claim; GPU child/plan/parent resources
remain parallel and unintegrated. The H actual 38 setup/
class-import facts and the archived random CPU toy distinction
are preserved; the current host full-unit failure cause
remains UNRESOLVED as observed H history: no causality is
invented and no failure is hidden. Whole 007 remains PARTIAL;
no main merge, 008, release or tag.

## 007-j slice: GPU child/launch/assets integration (integrated)

Selective integration of the FOURTEEN root-reviewed GPU
child/protocol, prepared-launch and packaged-resource files by
byte-exact file copy from the single exact source commit
5445c03bcc85a5cea6ad24f26f137e55f5a806cf (oap/reviews/
007-j-components.json, 136,921 bytes; every path verified at
this head for blob + SHA-256 + size): no branch ancestry, no
cherry-pick/rebase/reset/stash/clean, no source adaptation, no
test weakening. The current I fifteen files, the H
installer/fixture helpers, the existing fixtures, CI, locks,
requirements, worker-profile READMEs and law are unchanged;
the actual owned GPU parent, the new lock and the worker-
identity resources remain parallel and unintegrated (pending
their affected reviews); the old nineteen-file J draft is
inert and was never used.

`src/slaif_raggedized_helper/gpu_worker_protocol.py` (new) is
the closed child/parent wire: a fixed bounded vocabulary for
version, config, startup, token-ID row requests and raw FP32
row replies; `encode`/`parse` over bounded frames with exact
length/version checks; `identity`/`policy_id`/`code_id`
fingerprint the admitted space/definition/tokenizer and the
copied worker source; `profile` selects the bundled unchanged
GPU lock before any backend import; `rows_ok`/`output_ok`
enforce the vocab/1024/raw-FP32 bounds; refusals are
content-free. No fake serialized PID-bound lease exists: the
child acquires its actually owned device lease before loading
the backend, and the parent lease root is a real owned
directory with real open FDs.

`src/slaif_raggedized_helper/gpu_embedding_worker_main.py`
(new) is the trusted fixed worker entry: it revalidates the
copied capsule and runtime, owns the pipe, admits the immutable
ready binding, serves exact token-ID requests as raw FP32
rows, preserves the original non-Exception interruption
priority under foreign/fork/error/interrupt ownership semantics
and releases actually owned resources honestly on every exit
path.

`src/slaif_raggedized_helper/gpu_embedding_backend.py`
(replacement of the 007-g inert copy) keeps the corrected raw
GPU backend finite and inert under trusted fakes: device UUID
byte guard, process-owned DeviceLease assertion, no autocast,
ordered finite CPU FP32 raw CLS output, sticky close and
original non-Exception identity.

`src/slaif_raggedized_helper/gpu_worker_launch.py` (new) is
the prepared launch: `prepare` requires actual pinned
Python/package/config/device inputs with retained FDs, copies
the exact closed capsule (code, lock, profile) with byte-
identity revalidation, and builds the fixed argv (prlimit
AS/CPU bounds, unshare net/pid/ipc/uts, clearenv, private
mounts, trusted fixed entry `python3.12 -I -S /worker.py`).
The fork-creating-PID check precedes any close/cleanup;
bounded startup is checked against the fixed 2 MiB request/
total input; a tiny admitted cap cannot carry its own
startup; mutation or revalidation failure refuses the launch.
No parent or module code execution and no generic process
callback are added.

`tests/unit/test_gpu_profile_assets.py` and
`tests/integration/test_gpu_profile_assets.py` (new) prove the
packaged GPU profile assets: the actual offline wheel bundles
the unchanged GPU lock (alongside the CPU v2 and legacy CPU
locks packaged by 007-i) under `_worker_profiles` with
RECORD/license/entry/source identity; installed-layout
selection uses the bundled GPU lock first and refuses missing,
corrupt, symlinked or whole-bundle-missing assets even with a
matching ambient project/lock under bounded dist-info
downgrade guards, in both the normal and the src-named
installed prefix; the exact private /app/src/pkg layout case is
a data mapping, not authorization; source-checkout support is
retained.

The five `docs/parallel/*.md` GPU API/design docs are the
immutable reviewed bytes of this slice
(`gpu-child-protocol-api.md`, `gpu-worker-launch-api.md`,
`owned-gpu-parent-design.md`, `gpu-profile-assets-api.md`,
`gpu-profile-assets-design.md`).

Behavior is proven by the focused model-free suites at this
head: 103 GPU backend/protocol/launch/assets unit cases,
SEPARATE invocations of the installed-resource integration
(8), the project launch namespace witness (1: a real
bwrap/unshare child under fake/null namespaces with synthetic
/dev bindings and a fake injected backend) and the current
offline CPU-wheel integration (1), plus the query (3) and CPU-
worker (4) affected compatibility invocations; each bounded 1
GiB AS / 30 s CPU / 120 s wall, threads 1, no bytecode. This
is finite model-free software: no real GPU, driver, Tensor,
model or framework import was executed; a prepared capsule is
not a running parent or GPU exclusivity proof. The actual BGE
execution, latency, parity, model memory and hardware remain
UNRUN/UNQUALIFIED; the actual owned GPU parent, the new lock
and the worker-identity resources remain parallel and
unintegrated; no complete native/normalized/durable GPU
execution, controller or snapshot activation exists. The H
actual 38 setup/class-import/license-fact and the archived
random CPU toy distinctions are preserved; the H-era host
full-unit failure cause remains UNRESOLVED (no causality
invented, no failure hidden). Whole 007 remains PARTIAL; no
main merge, 008, release or tag.

## 007-k slice: raw snapshot declaration codecs (integrated)

Selective integration of the EIGHT root-reviewed immutable raw
snapshot core/row-map declaration codec, test, API and design
files by byte-exact file copy from the two exact source commits
b7a2b520ac543d3e78080aa163047b112e0b579f and
09fe0d5e02e01b514378facadb7d50cca12ef471 (oap/reviews/
007-k8-snapshot-components.json, 47,707 bytes; every path
verified at this head for blob + SHA-256 + size): no branch
ancestry, no cherry-pick/rebase/reset/stash/clean, no source
adaptation, no test weakening. The current I fifteen files, the
J child/launch/assets files, the H installer/fixture helpers,
CI, locks, requirements, worker-profile READMEs and law are
unchanged; the held parent K13 plan (oap/reviews/
007-k-activation-hold-reinit.json) and the parallel native work
are not integrated.

`src/slaif_raggedized_helper/raw_snapshot_manifest.py` (new) is
the closed bounded canonical ASCII schema-1 core codec: strict
types, duplicate keys, paths, fields, counts, size and
cross-reference checks, fixed analyzer/normalization
vocabulary, ordered unique lists, 4,096-row / 128-partition /
258-file / 96 MiB declared-total format bounds, and a derived
noncircular SHA-256 snapshot ID over the frozen core bytes.

`src/slaif_raggedized_helper/raw_snapshot_rows.py` (new) is the
8-header/17-row row-map codec: canonical data, bare canonical
representation IDs, immutable outputs, global/partition
ordinals, sort and uniqueness, shared batch/bundle
consistency, nonreused batch rows, canonical complete partition
subsets (header/global ordinal/source/batch refs, no snapshot
ID) and a `bind` that freshly parses both byte inputs and
checks exact descriptor size/hash/header/count/partition/
subset/active-not-withdrawn/corpus-execution-set
correspondence.

The four `docs/parallel/*.md` files are the immutable reviewed
bytes of this slice (`raw-snapshot-manifest-api.md`,
`raw-snapshot-core-design.md`, `raw-snapshot-row-map-api.md`,
`raw-snapshot-row-map-design.md`).

These are pure declared-format codecs only: they validate
declarations, never actual payloads, stored bytes, sources,
vectors, terms, rights, normalization, publication, retention
or readiness, and they load nothing, publish nothing and mint
no authority. A declaration hash, a `bind` pass or a
validation-passed declaration is not source, vector, rights,
hardware or Ready proof. The legacy dense_index.DenseIndex
cannot consume this codec without a new source-verified
adapter; prefix conversion does not fix the different identity
semantics.

Behavior is proven by the focused model-free suites at this
head: 50 core+row-map unit cases (9 manifest + 41 row-map) run
in one process, bounded 1 GiB AS / 30 s CPU / 120 s wall,
threads 1, no bytecode, exit 0. The Root composed review tree
(oap/reviews/007-k8-composed-review-tree.json) is forecast
evidence, not canonical CI/ICA.

## 007-l slice: owned GPU parent/identity + native runtime identity (integrated)

Selective integration of the TWENTY-THREE root-reviewed
immutable owned-GPU parent/identity and native runtime-
identity files by byte-exact file copy from the two exact
source commits 9ac0eabd77bff77101debe9812887993e86a6803 and
d7701a5329d825eefa2d5f7a2a58b74bc0788b10 (oap/reviews/
007-l-parent-native-components.json, 250,571 bytes; every
path verified at this head for blob + SHA-256 + size): no
branch ancestry, no cherry-pick/rebase/reset/stash/clean,
no source adaptation, no test weakening. The current I
fifteen files, the J child/launch/assets files, the K
declaration codecs, the H installer/fixture helpers, CI,
locks, requirements, worker-profile READMEs and law are
unchanged; the parallel GPU text bridge, producer and
controller work is not integrated.

`src/slaif_raggedized_helper/gpu_embedding_worker.py`
(parent, 9ac0eabd) retains the actual creating-process
lock in the strong owner registry before fallible process
acquisition, binds the parent attribute by object
identity, releases only the same captured local lock in
every branch (lock-close race), refuses repeated
initialization BEFORE any owner/process/FD/lock/registry
mutation or prepared-input consumption, and keeps the
original actual Popen pre-return capture, immutable ready
snapshot indices 9/10, source/dependency/FD/namespace
guards and exception priority.

`src/slaif_raggedized_helper/gpu_worker_identity.py`
(9ac0eabd) predicts immutable canonical raw
worker-identity record bytes with a domain-separated
fingerprint over selected file bytes, policy, device
configuration, explicit driver bytes, pinned Python and
profile metadata (instance values excluded);
`validate_record` checks the persisted canonical structure
only; `observe(worker)` validates the actual registered
live owner. A record is data, never authority, ownership
or complete GPU execution.

`src/slaif_raggedized_helper/embedding_native_identity.py`
(d7701a53) is the native runtime-identity leaf: bounded
scans of the selected executable, complete closed
tokenizers and distribution trees, fixed embedding policy
and four application source files, frozen detached
canonical bytes plus domain-separated SHA-256; descriptor
cleanup failures stay in private process-local uncertainty
and an attempted close is never retried.

`src/slaif_raggedized_helper/embedding_tokenizer.py`
(replaced, d7701a53) corrects TokenIDSession acquisition:
the actual owned Popen object is captured and retained
BEFORE fallible initialization can create a process, an
independent strong same-process pending owner survives
constructor failure, the creating PID is checked before
every encode/close/context branch (a forked borrower
refuses before touching the creator's resources), and
creator/once/closed/context/error precedence plus bounded
no-follow artifact identity are preserved. The positive
FILE test now uses the existing required
SLAIF_NATIVE_TEST_* CI fixture variables (no hardcoded
workstation paths).

These are finite model-free software: the parent/identity
proofs use the actual offline fixture with fake/null
namespaces and synthetic copied entries, and the token
work uses the actual native 0.21.4 tokenizer worker on
synthetic strings. No real GPU, driver, Tensor, model,
parity, rights, security, license or Ready is established;
source and package hashes do not establish ABI, publisher
or semantic identity. Behavior is proven by the focused
model-free suites at this head: 112 composed units (23
parent + 7 identity + 58 TokenID + 24 FILE) plus the
composition/acquisition suites (29 parent OS-disjoint
11/7/5/5 + 1 new, 1 identity OS, 8 native actual
acquisition, 3 query, 3 isolated CPU), each 1 GiB AS /
30 s CPU / 120 s wall, threads 1, no bytecode, exit 0. The
Root composed review tree (oap/reviews/
007-l-parent-native-composed-review-tree.json) is forecast
evidence, not canonical CI/ICA.

Root addenda 1/2 (oap/reviews/
007-l-ci-size-fixture-addendum-1.md,
007-l-ci-size-fixture-addendum-2.md,
007-l-CI-size-fixture-failure.json,
007-l-root-original-sequence-FSIZE-c82e.json) record ONE
authorized unit-only portability exception:
`tests/unit/test_embedding_native_identity.py` (current
15,779 B, SHA-256
c2b483b77c84f304ead4a6ae5c2ef27e5194c1df6ccd6adbb62992a7904a8df6;
frozen d770 original 13,668 B) no longer creates an actual
32 MiB+1 fixture file, because the earlier CPUv2 setup
unit in the same CI test process leaves a 32 MiB hard
RLIMIT_FSIZE inherited by later units (CI run
43209043099, OSError 27). It now keeps one owned real
small regular file and reports st_size as MAX_FILE+1 only
at the exact device/inode fstat boundary (every other
descriptor delegates to the original fstat), proves the
production size guard refuses BEFORE any read of that
file (zero reads observed), and that an owned in-memory
one-guard-omission source copy reads the actual file (7
bytes + 0-byte EOF) before the intact consistency guard
still refuses. The other 22 indexed files and all
production code/limits remain byte-exact; no
CI/workflow/helper/pin change, no skip/xfail, no cap
raised or reset.

Root addendum 3 (oap/reviews/
007-l-ci-native-spy-addendum-3.md,
007-l-root-native-spy-causal-record.json,
007-l-native-spy-path-clarification.json) records a
second authorized test-only exception after CI run
43217061569 at 6de7bea failed both Product integration
steps only at this test (children observed 0 expected 1;
skipped required follow-ups are NOT green):
`tests/integration/test_cpu_embedding_session_composition.py`
(current 5,179 B, SHA-256
275e10d333555f6e02f3261449e6f9becf99e659a352ee9d4464e4837a843fd0;
original 4,855 B /
a45301b444da6fc6c64bd018d0d133fb97da5d992711415c16b7b40e6f635ad0)
replaces its public-class Popen replacement spy with a
narrow spy on the actual `subprocess.Popen.__init__`
(delegating to the captured actual initializer on the
actual preallocated child), because the integrated
exact-class guard refuses a replaced public
`subprocess.Popen` class before any child. Public class
identity stays exact; the production guard is unchanged
and the replaced-class refusal negative was re-proven
locally; all original test behavior (encoding, renewal,
distinct vectors, worker reaping, staging cleanup) is
preserved.

## 007-m slice: GPU text bridge + source-bound plan (integrated)

Selective integration of the TEN root-reviewed immutable
GPU text-bridge and source-bound GPU plan files by
byte-exact file copy from the two exact source commits
a9a5ef0bcc331cffd0857257f7d6568fce63bac0 (bridge) and
d100689ef5582a79a29d78e51a4c5ce860d1552c (plan)
(oap/reviews/007-m-bridge-plan-components.json, 95,773
bytes; every path verified at this head for blob + SHA-256
+ size): no branch ancestry, no cherry-pick/rebase/reset/
stash/clean, no source adaptation, no test weakening. All
preexisting product/test/API/design paths are preserved,
including BOTH 007-l test-only exceptions (tests/unit/
test_embedding_native_identity.py, SHA-256
c2b483b77c84f304ead4a6ae5c2ef27e5194c1df6ccd6adbb62992a7904a8df6,
15,779 B; tests/integration/
test_cpu_embedding_session_composition.py, SHA-256
275e10d333555f6e02f3261449e6f9becf99e659a352ee9d4464e4837a843fd0,
5,179 B); no old parallel predecessor overwrites them.

`src/slaif_raggedized_helper/isolated_gpu_embedding.py`
(a9a5ef0) is the isolated GPU embedding bridge: it BORROWS
an actual current-process GPUEmbeddingWorker, its
PreparedLaunch and the caller operation reservation,
owning only its own independent native TokenIDSession and
private tokenizer copy; it never closes, replaces, reaps,
signals or releases the caller's parent/launch/reservation
in any branch. predict() takes the actual PreparedLaunch
and validates worker identity plus native
runtime/artifact/source inputs without launching any
process or importing a framework, emitting the frozen
isolated-gpu-fp16-cls-v1 execution record (closed
canonical ASCII JSON, prefixed domain-separated execution
fingerprint, detached native runtime record, bare
space/definition/intended-execution identities,
hardware_qualification unknown). Session admission
requires the actual registered live parent via
gpu_worker_identity.observe and exact source guards and
native runtime checks BEFORE starting or exposing text to
its own native worker; native IDs come only from the
actual owned native 0.21.4 TokenIDSession (never supplied
receipts/IDs/callback, GPU tokenizer or re-tokenization);
strict bounded UTF-8 preflight precedes any native text
exposure; every receipt field is validated; the bridge
renews only its own native session under unchanged
contract before budget exhaustion and never restarts the
borrowed GPU parent; forward and encode dispatch reach
the captured actual class implementations, not selected
instance shadows; creator/once/closed/busy/fork rules,
pre-return ownership retention and cleanup priority are
preserved; returned raw CLS rows are checked for binding/
cardinality/finite FP32 and normalized with the existing
embedding_vectors normalizer; a frozen EncodedBatch
(normalized FP32 vectors, immutable receipts,
space/definition/intended-execution/execution identities,
execution record + fingerprint, detached native record) is
returned only after post-forward re-observation proves the
parent/identity/native/source state unchanged. A record is
data: never authority, liveness, readiness or
qualification.

`src/slaif_raggedized_helper/gpu_embedding_plan.py`
(d100689) is the source-bound pre-model GPU batch plan:
build() freshly derives the complete selected rows, source
scope, independent native token counts and canonical
order/hash/space/definition/inventory/policy through the
actual source-plan stack BEFORE any job creation; it calls
the actual bridge predict and strictly compares every
predicted field/fingerprint to the bytes, revalidates the
actual PreparedLaunch startup (manifest/definition/
inventory/space/tokenizer identity), performs the complete
source plan, then REPLACES ONLY the legacy CPU intended
execution dependency with the complete predicted GPU
execution (bare 64-hex SHA-256 of the execution record,
distinct from the CPU reference contract's prefixed
identity), rechecks prediction/prepared identity after
counting (changed selected runtime/source/artifact/
preparation refuses), emits the existing
embedding-job-plan-v1 canonical bytes and freshly calls
the actual journal make_spec so the job ID derives from
the actual specification. Forged, detached or stale
records and any source change refuse; no truncation,
replaced source proof, callback grant or inference is
created; the legacy CPU intended identity stays distinct
from the full GPU execution.

These are finite model-free software: behavior is proven
by the focused suites at this head — 13 focused units (7
bridge + 2 plan + 4 normalizer in the existing
tests/unit/test_embedding_vectors.py) plus all 9 bridge
actual composition cases and all 8 GPU plan actual
composition cases in separate capped invocations (1 GiB
AS / 30 s CPU / 120 s wall, threads 1, no bytecode, exit
0), the actual native 0.21.4 tokenizer worker on
synthetic strings and the approved copied GPU fake/null
fixture only. No real GPU, driver, Tensor, model, parity,
rights, security, license or Ready is established; no GPU
producer, corpus controller, runtime promotion, current
rights or physical qualification is integrated by this
slice. Whole 007 remains PARTIAL; the Root records
(oap/reviews/007-m-root-records.json) and the component
index are immutable provenance, not current CI or Root
acceptance.

## 007-n slice: corpus pipeline integration (integrated)

Selective integration of the TWENTY-ONE root-reviewed
immutable corpus-pipeline files by byte-exact file copy
from the four exact source commits
b0ca5a68f8e55667ada5dd7523903b5585cbe0af (launch
owner), 880dedf33e7b9eb1da497bf88acb6bb626a7fce3 (GPU
producer), 6f5b31123d080376b6b0c09a803bd67033694484
(source program) and
bac11bee72fa809157b77e21be8bcf8ef17529a9 (executor)
(oap/reviews/007-n-corpus-pipeline-components.json,
335,687 bytes; every path verified at this head for
blob + SHA-256 + size): no branch ancestry, no
cherry-pick/rebase/reset/stash/clean, no source
adaptation, no test weakening. TWO deliberate existing
production replacements (gpu_worker_launch.py,
retrieval_representation.py); nineteen new paths. All
preexisting product/test/API/design paths are
preserved, including BOTH 007-l test-only exceptions
(tests/unit/test_embedding_native_identity.py,
SHA-256 c2b483b77c84f304ead4a6ae5c2ef27e5194c1df6ccd6adbb62992a7904a8df6,
15,779 B; tests/integration/
test_cpu_embedding_session_composition.py, SHA-256
275e10d333555f6e02f3261449e6f9becf99e659a352ee9d4464e4837a843fd0,
5,179 B); no old parallel predecessor overwrites them.

Behavior, concisely (exact contracts in the linked
API/design docs): the owned launch
preparation/handoff associates a failed preparation
with its actual cleanup owner and hands the same
actual PreparedLaunch to the existing parent on
success, reservation borrowed; the one-batch GPU
embedding producer owns each captured preparation,
journal lease, parent and native session, checks fresh
current rights at every producer boundary under one
unmoved epoch, starts attempts only from fresh PENDING
jobs, and never promises exactly-once; the source
embedding program freshly revalidates every selected
original-backed container into stable ordered
source-local batches with no silent >128-row
truncation and no whole-corpus row ceiling; the
corpus executor runs the selected program under one
operation-wide epoch, stops on failure before
uncertain later work, keeps lightweight batch
completions plus one common full execution/native
record pair, and reuses or resumes only where the
existing journal decides (fresh-creator resume after
a clean between-batch stop; unknown/failed/claimed/
running attempts never retryable by decree).

[docs/parallel/gpu-launch-preparation-owner-api.md](docs/parallel/gpu-launch-preparation-owner-api.md),
[docs/parallel/gpu-launch-preparation-owner-design.md](docs/parallel/gpu-launch-preparation-owner-design.md),
[docs/parallel/gpu-embedding-producer-api.md](docs/parallel/gpu-embedding-producer-api.md),
[docs/parallel/gpu-embedding-producer-design.md](docs/parallel/gpu-embedding-producer-design.md),
[docs/parallel/corpus-embedding-program-api.md](docs/parallel/corpus-embedding-program-api.md),
[docs/parallel/corpus-embedding-program-design.md](docs/parallel/corpus-embedding-program-design.md),
[docs/parallel/corpus-embedding-executor-api.md](docs/parallel/corpus-embedding-executor-api.md),
[docs/parallel/corpus-embedding-executor-design.md](docs/parallel/corpus-embedding-executor-design.md).

These are finite model-free software: behavior is
proven by the focused suites at this head — the four
new unit modules (static parametrization predicts 51
cases) in one capped invocation plus the 13 actual
composition cases, each in its OWN capped process (1
GiB AS / 30 s CPU / 120 s wall, threads 1, no
bytecode, exit 0), the actual native 0.21.4 tokenizer
worker on synthetic strings and the approved copied
GPU fake/null fixture only. No real GPU, driver,
Tensor, model, parity, rights, security, license or
Ready is established; no operational mode controller,
current-principal policy, inference CLI, snapshot/
parity integration or physical qualification is
integrated by this slice. Whole 007 remains PARTIAL;
the Root records (oap/reviews/007-n-root-records.json)
and the component index are immutable provenance, not
current CI or Root acceptance.

## Remaining 007 work (not implemented this round)
The CPU reference software path now selects the CPUv2 lock (trusted
neural fakes only); still open: running the ACTUAL BGE-M3 model under
the fixed weights-only CPU worker (the real model has never been run
here; the full-38 CPUv2 acquisition has a separately scoped Root
actual frozen full-CLI completion as developer qualification
evidence, not a deployment or runtime grant), running the resident CPU query path against the ACTUAL model
(the query encoder is integrated model-free; the real model has
never been run) and CPU exact dot-product search against admitted
spaces, resumable
owned GPU encode batches with bounded resource telemetry (the REQUIRED
exclusive GPU FP16 corpus encoding per the architecture; the corrected
raw GPU backend source, the GPU child/protocol wire, the worker entry,
the prepared launch, the owned GPU parent/lock/identity software
(007-l), the isolated GPU text bridge + source-bound GPU plan
software (007-m) and the 007-n owned launch preparation, one-batch
GPU producer, source program and corpus executor are integrated
and inert under trusted fakes — no operational mode controller,
current-principal policy, inference CLI, snapshot/parity
integration or physical drain exists), snapshot/manifest
binding of vectors, row maps, ACL and space fingerprints (the pure
declared core/row-map codecs are integrated; actual payload loaders,
stored-byte validation, atomic publication, current-generation CAS,
retention and deletion remain unimplemented), query/GPU
precision qualification (FP16 vs FP32 cosine/ranking/Recall@k), and all
artifact/encoder/execution/auth gates. The legacy optional CPU profile
(Torch 2.10.0+cpu / Transformers 4.51.3) is NOT security qualified: the
committed Root observations (oap/reviews/007-legacy-cpu-profile-
security-observation.json, oap/reviews/007-legacy-fixed-route-static-
observation.json) record the GitHub TorchScript advisory as LOW and the
Transformers advisory list as four HIGH, six MEDIUM and one LOW — all
with UNPROVEN transitive reachability and NOT_EXPLICITLY_INVOKED direct
fixed routes on the installed pins; advisory triage, current route
reachability and a patched CPU/Volta profile refresh are separate
pending work — no silent upgrade, no vulnerability-absence claim, no
legal/security exception. Live
authorization remains NONE; no model weights, inference, GPU, services,
credentials, private corpus, release or deploy in this slice.

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
007-e behavior is proven by the merged reviewed suites (seven focused unit
files; four standalone integrations plus the existing native composition in
separate processes) and the three unchanged root witnesses (native close
ownership, native interrupt priority, producer lease interrupt), all exit 0
with indexed sources byte-unchanged after the private fault injections; the
portable synthetic CI fixture is verified by the product CI job itself.
The root-accepted local component records (oap/reviews/007-e-cpu-profile-
review.json, 007-e-cpu-worker-review.json, 007-e-cpu-test-setup-review.json,
007-e-isolated-cpu-session-review.json, 007-e-execution-plan-review.json,
007-e-cpu-toy-probe-review.json, 007-e-native-lifecycle-review.json,
007-e-cpu-producer-review.json, plus oap/reviews/007-e-components.json and
oap/reviews/007-e-root-records.json) are immutable provenance, not current
CI or Root acceptance of this integration; the legacy CPU profile advisory
observation (oap/reviews/007-legacy-cpu-profile-security-observation.json)
is a recorded finding set, not a clearance; the old-SHA random toy evidence
(oap/reviews/007-owned-cpu-toy-evidence.json) is scoped toy evidence, not a
new neural permit. Real qualification remains NOT RUN (U04/U07 relevant).
007-f behavior is proven at the current canonical by the six focused unit
files (105 cases) and the six standalone integrations (39 cases, each in
its own process) plus the TEN original Root witnesses, all exit 0 with
the seventeen indexed sources byte-unchanged before and after; the
twelve root-accepted component/peer/remediation records (oap/reviews/
007-f-peer-producer-b-report.json, 007-f-peer-producer-b-review.json,
007-journal-producer-cleanup-findings.json, 007-f-cleanup-composition-
review.json, 007-f-isolated-exit-review.json, 007-f-gpu-device-lease-
review.json, 007-f-composed-review-tree.json, 007-f-components.json,
007-f-root-records.json and the 007-e final review/CI/GitHub records)
are immutable provenance, not current CI or Root acceptance of this
integration. The finite fault coverage is not kernel-reaping, restart-
recovery, power-loss, hardware or ICA proof, and the cooperative device
key is not physical exclusivity or runtime authority. Real qualification
remains NOT RUN (U04/U07 relevant).

007-g behavior is proven at the current canonical by the focused unit
set (269 cases: CPU backend/worker/contract/session/plan/producer,
batch plan/store, job journal/ownership, isolated CPU, GPU device
lease and GPU backend under the v2 fixture; plus 11 legacy-fixture
setup cases and 20 native prerequisite cases) and the five standalone
integrations (worker 4, plan 1, isolated 3 with the retained
multithreaded-fork warning, producer 30, GPU raw 1), each in its own
process, plus the six corrected independent interrupt cases
(`/tmp/raggedized-root-gpu-interrupt-remediation.py`), all exit 0 with
the twenty-five indexed sources byte-unchanged before and after (23
byte-exact blobs; the two profile READMEs byte-exact candidate prefix
plus appended selection note). The candidate-side evidence (Root CPU
177 unit + 40 standalone + 5 original witnesses, portable 18 unit + 4
worker + 1 premodel, GPU 84 unit + 1 standalone + 6 corrected interrupt
cases) remains candidate evidence, not current canonical CI. The
root-accepted records (oap/reviews/007-g-cpu-v2-alignment-b-review.json,
007-g-cpu-v2-fixture-portable-c-review.json,
007-cpu-v2-portable-source-review-485f.json,
007-cpu-v2-portable-root-setup-result.json, 007-g-gpu-backend-b-
review.json, 007-g-audit-gpu-backend-b-report.json,
007-g-audit-gpu-backend-b-review.json,
007-gpu-backend-b-source-review-6da1.json,
007-gpu-peer-b-causal-root-reproduction.json, 007-g-components.json
and 007-g-root-records.json) are immutable provenance, not current CI
or Root acceptance of this integration; the independent affected GPU
re-audit (237e) is COMPLETE_ACCEPT_CANDIDATE for source only, and the
prior afc5 CHANGES_REQUIRED remains historical, not a false pass.
Real qualification remains NOT RUN (U04/U07 relevant).

007-h behavior is proven at the current canonical by the focused
local suites: CPUv2 runtime installer 18 passed (the 17 original
controlled-fake cases plus one added identity/ambient negative-
control case; the controlled-fake binary preflight maps ONLY the
designated dummy bytes to the production identity digests with all
other hashing real and no stub binary executed — test-only fake
identity, not actual binary qualification; the bounded subprocess
case uses sys.executable, the current test interpreter, and is not
a real standalone 3.12 test; no actual heavy install, download or
network operation), GPU fixture setup 4
passed (gate-only in-memory trusted framework facades over the
Root-copied real standalone 3.12 fixture — six actual
distributions plus 51 DATA-ONLY records — with no model
constructor, Tensor or CUDA), legacy helper regression 11 passed,
CPUv2 fixture setup 7 passed and native controls 20 passed
(15 tokenizer + 5 bounded-capture); the five Root installer
priority/churn witnesses (receipt, cleanup, note, file churn,
directory churn) PASS against the canonical unchanged helper, and
the diagnostic atomic-receipt priority causal bypass is inspected.
The full local tests/unit sweep fails on this host (one failure in
test_derived_store.py then a segmentation fault in
test_embedding_artifacts.py::test_unicode_admission_and_privacy),
reproduced at BOTH the round base 999357f and the current head in
a throwaway worktree — an observed base/head comparison, not
proven environmental causality: the cause is UNRESOLVED, and no
claim is made that this integration does not cause it or that the
host platform is globally safe; the current full GitHub
unit/integration/OAP jobs on both matrix legs are the
mandatory gate (expected five jobs, 78 steps) and are reported as
observed, with no duplicate local sweep absent failure. The
fifteen root-accepted records (oap/reviews/007-g-review.json,
007-g-implementation-CI-final.json, 007-g-report-CI-final.json,
007-g-GitHub-current-final.json, 007-h-components.json,
007-h-cpu-install-arena-d-review.json, 007-installer-D-source-
review-ec9b.json, 007-installer-D-root-tests-ec9b.json,
007-h-cpu-runtime-evidence.json, 007-h-gpu-test-fixture-review.
json, 007-gpu-fixture-source-review-c0e1.json,
007-h-gpu-fixture-evidence.json, 007-h-cpu38-license-inventory-
report.json, 007-h-cpu38-license-inventory-review.json and
007-h-license-facts.json, indexed by 007-h-root-records.json) are
immutable provenance, not current CI or Root acceptance of this
integration. The Root actual frozen full-CLI completion and the
separate class import are development qualification evidence for
the fixed runtime/binary host only; they do not qualify models,
hardware, security, licenses, parity or deployment, and a test
fixture or historical Root allowance is not a new runtime grant.
Real qualification remains NOT RUN (U04/U07 relevant).
007-i behavior is proven at the current canonical by the full
local unit sweep (1466 collected, all passed, exit 0), the four
separate integration invocations, each in its own process (query
composition 3, isolated composition 3 with the retained
multithreaded-fork deprecation warning, CPU worker composition
4 under the CPUv2 fixture variables, actual offline wheel 1; all
exit 0), the full integration sweep (637 cases, exit 0) and
ruff/compileall/OAP-scaffold/check_state/help/doctor, with the
fifteen indexed sources byte-unchanged before and after. The
disposable Root 15-file composed review tree
(oap/reviews/007-i15-composed-review-tree.json: 246 focused
unit + separate query 3 / isolated 3 / CPU worker 4 / wheel 1
PASS; the initial Root invocation errors - nonexistent test
names and missing CPUv2 env - are retained and corrected in that
record, not product failures) is forecast evidence, not
canonical CI or ICA. The root-accepted records
(oap/reviews/007-h-review.json, 007-h-root-source-final.json,
007-h-implementation-CI-final.json, 007-h-report-CI-final.json,
007-h-response-format-reconciliation.json,
007-i-query-boundary-b-review.json,
007-i-audit-query-boundary-c-review.json,
007-query-C-peer-root-review-758f.json,
007-i-cpu-profile-assets-review.json,
007-i-audit-cpu-profile-assets-review.json,
007-cpu-assets-source-review-c5e9.json,
007-cpu-assets-peer-root-review-b65e.json), the components index
(oap/reviews/007-i-components.json) and its record index
(oap/reviews/007-i-root-records.json) are immutable provenance,
not current CI or Root acceptance of this integration. The
required exact-head GitHub five jobs / all 78 steps at
implementation and report head are the mandatory gate and are
reported as observed. The composed proof substitutes a trusted
in-memory fake framework over actual staged artifacts, actual
native tokenizer 0.21.4 and the actual CPU isolation protocol;
the wheel test exercises the actual offline wheel in a private
bounded prefix. This is finite model-free software: no BGE
execution, latency, parity, model memory or hardware claim; GPU
child/plan/parent resources remain parallel and unintegrated.
The H actual 38 setup/class-import facts and the archived random
CPU toy distinction are preserved; the H-era host full-unit
failure (derived-store failure then embedding-artifacts
segmentation fault at the H base/head) remains an UNRESOLVED
observed historical observation: no causality is invented, no
failure is hidden, and this round's passing local full unit
sweep does not retroactively clear it. Real qualification
remains NOT RUN (U04/U07 relevant).
