# slaif-raggedized-helper

A local documentation assistant using contextual retrieval, authorized source evidence,
and Qwen through SLAIF API Gateway (English/Slovenian). This checkout contains the
architecture, a tested concentrated OAP scaffold, the foundation package
(objective 002-a): strict configuration, typed generator/embedding/reranker
contracts, model lock/qualification schemas and an offline `raggedized doctor`
command; the complete objective 003 slice (merged as PR #5): the gateway
`POST /v1/responses` generator adapter with bounded HTTP/SSE transport, the
private offline native llama.cpp `/completion` adapter (explicit
offline-diagnostic policy, server-rendered templates via `/apply-template`,
truthful native stop/metric mapping), the bounded explicit
`raggedized probe` qualification probe and real loopback integration tests
([docs/generator-contract.md](docs/generator-contract.md)); and — merged as
PR #6 — the objective 004 finite qualification trial runner (004-a) plus the
004-b/004-c evidence-contract corrections: strict bounded trial
spec/sample/result contracts with cross-field consistency bindings
(actual-ledger-driven analysis recomputation, backend/fingerprint
bindings, provenance pairs, declared-budget reservation, pure
cache/input consistency derivation) and quartile-complete stage
metrics enforced at the construction/serialization/analysis
boundaries, bounded safe spec file input with decoded-Unicode
admission (special-file/FIFO, byte, UTF-8, JSON-decoder and unpaired-
surrogate typed refusals at zero dispatch), the canonical full strict
result contract at CLI serialization with the actual spent-attempt
ledger preserved on post-work rejection, actual
gateway/direct repeated-parent composition under one absolute trial
deadline and one shared dispatch allowance at the real transport
boundary, reproducible nearest-rank caller-wall latency analysis with
available-stage timing summaries, the deterministic explicit synthetic
route and the machine-readable section 23.2 prerequisite projection
([docs/benchmarks/qualification-protocol.md](docs/benchmarks/qualification-protocol.md)).
Real target/hardware/model qualification remains NOT RUN; snapshot/agent
layers are not implemented yet. The 004-d slice adds bounded read-only
local resource telemetry (explicit opt-in only): the
`raggedized resource diagnose` own-process CPU/RSS diagnostic on this
devhost (D0 bounded allowance: 5 s / 64 samples, at most ONE bounded
nvidia-smi fixed-argv metadata query with `--gpu`) and
`raggedized qualification run --resources[ --resource-gpu]`, which
returns the plain v1 trial evidence INTACT inside an explicit
versioned wrapper carrying the strict versioned own-process
observation (peaks are observed sample peaks; phase events are
declarations; GPU absence is an exact unavailable, never a zero; the
004-e correction enforces the shared-deadline startup admission,
honest observed-byte aggregate accounting, every-exit-path owned
observer stop and canonical inner-trial-ledger late-export
accounting that the telemetry semantics require). The first 005
slice (open on the 005 PR, branch
`oap/005-artifact-schema-and-source-scopes`, not merged) adds the
independently reviewed local original admission/store and a thin
installed `raggedized source import|inspect` route: a strict
versioned manifest admits operator-approved local regular files
beneath an explicit approved root into a private operator store
with bounded descriptor-verified reads, digest-named immutable
blobs, metadata-sensitive immutable revisions, byte deduplication
with distinct rights/ACL/corpus metadata, atomic same-filesystem
publication and safe input-free failures. The 005-b continuation
merges the independently reviewed provenance and job record modules:
versioned block/span/chunk/derived-scope records reconstruct exact
original text from code-point spans with explicit separators,
all-label source scopes keep distinct rights and reject
cross-boundary support, and bounded job/attempt DTOs carry safe
status transitions without claiming execution, caching or output
existence; parsing/extraction remain 006 scope and operator
approval is metadata, not authentication
([docs/parallel/source-admission-api.md](docs/parallel/source-admission-api.md),
[docs/parallel/source-cli-api.md](docs/parallel/source-cli-api.md),
[docs/parallel/provenance-records-api.md](docs/parallel/provenance-records-api.md),
[docs/parallel/job-records-api.md](docs/parallel/job-records-api.md),
[docs/data-model.md](docs/data-model.md)).
The 006 slices (merged to main as PR #8, branch
`oap/006-native-extraction-and-chunking`) add native
extraction on that foundation: the exact literal line and bounded
structural Markdown subset adapters with full Unicode code-point
coverage, and the fixed trusted isolated PDF worker (bounded verified
read, private pinned hash-verified development backend, required
reproducible PDF development tests on product CI). The 006-b/006-c
continuation integrates the reviewed fixed native tokenizer session and
structural chunk adapter with canonical extraction: chunks with exact
original spans/separators, conditional word-boundary overlap and no
discarded tail, each carrying three observed local token counts and
receipts binding exact role inputs, artifact SHA, backend, declared
revision/preprocessing and input digests (512/768/1024 budgets, up to
64-token overlap, native pair 1280 with 64 reserved; the legacy
callback fixture keeps supplied pair 512 unverified); the 006-c
correction raises the session caps to 16,384 calls / 32 MB input /
4 MB output, adds the 15,000 ms native default builder deadline (legacy
explicit default 5,000 ms) and per-build reuse, so the representative-
scale 7876-byte procedure and 9269-byte table sources now complete
under the current caps; the required native tests are mandatory on
both product CI legs under a NEW private pinned hash-verified
engine-only tokenizers 0.21.4 capsule (DEV only; no dependency, lock,
allowlist or license change). The 006-c slice composes the reviewed source/receipt
record validators and the opaque immutable derived container store in the
same combined journey (validated records survive publication and
fresh-process revalidation). The 006-d continuation corrects concurrent
derived-store reads (a changed read attempt is discarded and the file is
re-admitted at most four fresh times within the existing deadline; not a
universal convergence guarantee), adds the complete typed text/PDF
semantic bundle with its durable publisher and verified fresh loader, the
operator profile, and the installed private `raggedized chunk` /
`chunk inspect` route (bounded JSON overview, exit 0/1/2,
`no_native_chunks` with partial visual truth, the known published ID
retained on later failure, idempotent canonical retries, cooperative
180-second budget); the root-reproduced reduced-policy PDF table
header-relationship loss (all source code points, anchors and tail
preserved) is repaired by the 006-e bounded native PDF structural
correction: the conservative literal line classifier
(`pdf-literal-structure-v3`) under PDF policy definition v4 and the
shared kind-bound block fingerprint v2 restores the original header
relationship, the closing-rule last row and the warning/procedure
grouping on the actual owned PDF fixtures (reduced-policy small and
closing tables, default-policy 300-row table, fitting warning) with full
source coverage, tail, units and anchors preserved; classifier v2 /
policy v3 records remain immutable and require explicit re-extraction,
and the literal grammar cannot infer arbitrary PDF layout. Whole-006
acceptance and all real qualification remain open.
The first 007 slice (open on the 007 PR, branch
`oap/007-embedding-pipeline`, not merged) integrates the exact reviewed
bounded normalized FP32 NPY subset codec (`vector_codec`: strict header
admission before materialization, writer interop, immutable read-only
views, input-free refusals) and the first exact runtime dependency pin
(NumPy 2.5.4 in the lock; the full 018 license/SBOM audit remains OPEN).
The 007-b continuation integrates the reviewed source-bound raw retrieval
representation/batch (one bundle validation, one native token-counting
session, exact receipt admission, bounded batch preflight) and the published
BGE-M3 checkpoint inventory/encoder-space software (schema 1/2 byte-verified
local artifact admission with fixed safetensors/pytorch-state-dict weight
names; v1 CLS/1024/normalize/identity space binding; pinned layout evidence
metadata-only, no deserialization or model execution).
The 007-c continuation integrates the reviewed composed CPU-session
software: owned staging with double admission, exact native token IDs
obtained before any framework construction, bounded 1-128 text and
native receipt preflight before one ordered CPU CLS forward, and fixed
binary32 L2 normalization with provenance kept separate from encoder
identity. The neural framework runs only as trusted fakes; no actual
model, weights, GPU or network were used.
The 007-d continuation integrates the reviewed durable source-plan
substrate: a fresh original-backed source bundle through ONE native count
session into a deterministic intended CPU/FP32 embedding batch plan with
exact dependency and row fingerprints, the typed validated embedding
batch store with fresh read-back publication, per-job ownership leases
and the owned atomic job journal whose COMPLETE only accepts a freshly
validated full-plan typed output. Plan, store, lease and journal are
software contracts; no encoder producer, controller, retry, CPU query,
GPU or actual model execution exists yet.
The 007-e continuation integrates the reviewed CPU reference path: a
pre-model schema-2 execution contract predicted before any model starts,
job claim before model startup, observed-execution comparison before any
source text is forwarded, the one-batch CPU producer (explicit trusted
authorization provider, one attempt, COMPLETE only after actual typed
publication plus fresh load, verified reuse with zero model starts), the
resident CPU worker under the actual bounded OS isolation protocol and the
portable synthetic six-real/22-metadata CPU test fixture provisioned in CI.
The actual BGE model has never been run and the legacy optional CPU pins
(Torch 2.10.0+cpu / Transformers 4.51.3) are NOT security qualified; the
required exclusive GPU FP16 corpus encoding remains unimplemented.
The 007-f continuation integrates the two exact root-reviewed
cleanup/ownership composition candidates and the cooperative
per-device kernel lease: finite owned-descriptor close attempts across
failures with original non-Exception interruptions preserved (a new
cleanup interrupt outranks ordinary errors), no blind re-close of a
reused descriptor number (same-inode included), sticky UNKNOWN cleanup
retained as a cleanup owner reaching the sanitized journal and producer
errors even before the claim returns, the producer's pending native/model
resource and journal lease held until drain, the isolated context-exit
under the same interrupt priority, and the GPU device lease key binding
only the versioned host + physical UUID under the trusted common local
root (cooperative: no physical exclusivity, no granted runtime
authority, no GPU lifecycle managed). The imported seventeen
source/test/API files are the immutable reviewed bytes; no actual model,
GPU operation, profile cutover or runtime change.
The 007-g continuation selectively integrates the TWO exact
root-reviewed candidates by byte-identical file transfer (twenty-five
indexed files, no branch ancestry, no source adaptation): the CPU source
now selects the cpu-v2 lock (Torch 2.14.0+cpu / Transformers 5.22.2 /
framework tokenizers 0.23.1; 38 locked metadata distributions) with the
legacy profile/helper/fixture and the native 0.21.4 capsule intact, the
required portable synthetic CPUv2 CI fixture (six exact wheels plus 32
DATA-ONLY metadata distributions, no importable fake ML packages) is
provisioned before lint on both matrix legs with the legacy fixture
variables retained, and the corrected raw GPU backend source is
integrated finite and inert (assigned device UUID byte guard, process-
owned DeviceLease assertion, bounded native-ID input, no autocast,
ordered finite CPU FP32 raw CLS output, sticky close and original
non-Exception identity under hostile attachment). This is bounded
source integration, not model/runtime qualification: the actual BGE
model, checkpoint and hardware remain UNRUN/UNQUALIFIED, the actual
full-38 CPUv2 installation remains a separate PARTIAL (uv allocation
abort under the fixed 2 GiB address space; no full CLI acceptance or
neural import), and no owned GPU process/controller or physical drain
exists.
The 007-h continuation selectively integrates the SIX root-reviewed
setup/test/API files (no branch ancestry, no source adaptation): the
original byte-identical transfer (70,906 bytes;
oap/reviews/007-h-components.json) is historical, and per the Root
CI-portability amendment 007-h-1
(oap/reviews/007-h-ci-portability-addendum-1.md) ONLY the installer
unit file differs from that frozen candidate (23,095 → 28,320 bytes;
current SHA-256
6038a3b1766f52911f9d15b800d6fe515630b32f03cec52bca39b30ed56d1482;
self-contained controlled-fake preflight in its own tmp_path), while
the other five files, including the production helper (SHA-256
226a527650083ec3324fcb783354ca47eb8b30884f0db0d3e4df6c044e6ede0c),
remain byte-exact at this head (current six-file sum 76,131 bytes;
oap/reviews/007-h-components-after-portability.json): the fixed CPUv2
runtime
installer source — developer qualification tooling with the 38-wheel
pinned official graph, offline no-index/no-deps hash-required
install, MALLOC_ARENA_MAX=1 and atomic receipts, never run in CI and
not an implicit deployment or runtime grant — the portable synthetic
GPU worker fixture helper (six exact wheels plus 51 DATA-ONLY
metadata distributions from the fixed GPU lock, no importable fake ML
packages) and their unit suites and API docs. The ONE required GPU
fixture CI step is provisioned after the CPUv2 fixture and before
lint on both matrix legs with literal GITHUB_ENV bindings. The
007-g-era full-38 PARTIAL claim is superseded as current status by
separately scoped Root actual development evidence (not release
qualification): a frozen full-CLI acquisition of all 38 wheels
completed in 22.254 s (252554535 payload bytes, 38 hash-verified
wheels, 38 metadata and dependency graph, all four commands exit 0,
no unresolved owned children, sampled disk 2085087847 B under 2 GiB
address space / 120 s CPU / 600 s wall, sampling not quota), and a
separate actual CPU class import (Torch 2.14.0+cpu plus
Transformers 5.22.2 XLMRobertaModel) succeeded in 14.73 s with
352816 KiB RSS inside the standalone CPython 3.12 namespace,
synthetic /dev, no home, offline, under a separate 4 GiB /
30 s CPU / 120 s wall allowance. A class import is not loading BGE
weights, constructing a model, running a forward pass or measuring
query latency, parity, hardware, security or licenses.
The 007-i continuation selectively integrates the FIFTEEN
root-reviewed resident-query/CPU-asset files (no branch ancestry,
no source adaptation; oap/reviews/007-i-components.json,
170,026 bytes): the private resident CPU query encoder
(ResidentQueryEncoder over one owned isolated CPU session:
bounded raw Unicode/UTF-8 query admission of at most 8192
characters / 32768 strictly encoded bytes with no prefix,
title, normalization, truncation or padding; independent native
0.21.4 tokenizer IDs enforcing the 1024 limit; one actually
owned CPU worker reused across different queries with
load-once; immutable normalized FP32 result with observed
complete execution provenance; content-free refusal before
exposure on invalid input or missing/changed identity), the
shared native/CPU/session diagnostic-priority fixes (the
selected original non-Exception interruption is preserved even
when cleanup or diagnostic annotation fails; a new cleanup
interruption outranks an ordinary error; exception notes and
owner attributes are best effort, never resource ownership) and
the packaged CPU profile lock assets (the actual offline wheel
bundles byte-identical CPU v2 / legacy CPU / GPU locks under
_worker_profiles with RECORD/license/entry/source identity
checks; installed-layout selection refuses missing, corrupt,
symlinked or whole-bundle-missing assets even with a matching
ambient project/lock under bounded dist-info downgrade guards;
source-checkout support retained; pyproject adds only the three
reviewed force-include lock mappings, with dependencies and all
CPU/GPU/native locks unchanged). This is finite model-free
software: the composed tests substitute a trusted in-memory fake
framework over actual staged artifacts, actual native tokenizer
0.21.4 and the actual CPU isolation protocol, and the wheel test
builds and exercises the actual wheel offline in a private
bounded prefix. The actual BGE execution, latency, parity, model
memory and hardware remain UNRUN/UNQUALIFIED; the corrected GPU
backend and the H helpers/fixtures/CI/locks are preserved
unchanged; GPU child/plan/parent resources remain parallel and
unintegrated; whole 007 remains PARTIAL
([docs/parallel/query-embedding-api.md](docs/parallel/query-embedding-api.md),
[docs/parallel/cpu-profile-assets-api.md](docs/parallel/cpu-profile-assets-api.md)).
The 007-j continuation selectively integrates the FOURTEEN
root-reviewed GPU child/protocol, prepared-launch and packaged-
resource files (no branch ancestry, no source adaptation;
oap/reviews/007-j-components.json, 136,921 bytes, single exact
source commit 5445c03): the GPU worker protocol (child-owned
GPU device lease acquired before any backend load, fixed
closed bounded wire/version/config/startup vocabulary, exact
token-ID requests and raw FP32 rows, content-free refusals,
immutable ready bindings and no fake serialized PID-bound
lease), the worker main entry (the original non-Exception
interruption priority is retained; foreign/fork/error/
interrupt ownership semantics keep actually owned resources
honest), the corrected raw GPU backend (finite and inert under
trusted fakes: device UUID byte guard, process-owned
DeviceLease assertion, ordered finite CPU FP32 raw CLS
output), the prepared launch (actual pinned Python/package/
config/device inputs with retained FDs, exact closed copied
capsule, fixed argv/clearenv/private namespaces and trusted
fixed entry; the fork-creating-PID check precedes any
close/cleanup and bounded startup is checked against the
fixed 2 MiB request/total input; no parent or module code
execution and no generic process callback) and the packaged
GPU profile assets (bundled unchanged GPU lock first;
fail-closed for missing, corrupt, symlinked or whole-bundle-
missing assets under the actual installed normal and src-
named prefixes even with a matching ambient project/lock;
bounded dist-info recognition; the exact private /app/src/pkg
layout case is a data mapping, not authorization; the real
offline wheel carries the three exact locks plus
RECORD/license/entry/source identity). This is finite
model-free software: the focused units and the separate
installed/launch/wheel invocations use fake/null namespaces,
synthetic /dev bindings and the actual offline wheel, never a
real GPU, driver, Tensor, model or framework import. The
actual BGE execution, latency, parity, model memory and
hardware remain UNRUN/UNQUALIFIED; the actual owned GPU
parent, the new lock and the worker-identity resources remain
parallel and unintegrated (pending their affected reviews);
the current I fifteen files, the H helpers/fixtures/CI/locks
and the CPU paths are preserved unchanged; whole 007 remains
PARTIAL
([docs/parallel/gpu-child-protocol-api.md](docs/parallel/gpu-child-protocol-api.md),
[docs/parallel/gpu-worker-launch-api.md](docs/parallel/gpu-worker-launch-api.md),
[docs/parallel/gpu-profile-assets-api.md](docs/parallel/gpu-profile-assets-api.md)).
The 007-k continuation selectively integrates the EIGHT
root-reviewed immutable raw snapshot core/row-map declaration
codec, test, API and design files (oap/reviews/007-k8-snapshot-
components.json, 47,707 bytes, byte-exact from the two exact
source commits b7a2b52 and 09fe0d5): a closed bounded canonical
ASCII schema-1 core codec with strict types, duplicate-key and
cross-reference checks and a derived noncircular snapshot ID,
and an 8-header/17-row row-map codec with canonical partition
subsets and a fresh-bytes bind checking exact declared
correspondence. They are pure declared-format data only: they
validate declarations, never actual payloads, sources,
vectors, terms, rights, normalization, publication or
retention, and no snapshot is activated or loaded. The held
parent K13 plan and the parallel native work are not
integrated; whole 007 remains PARTIAL
([docs/parallel/raw-snapshot-manifest-api.md](docs/parallel/raw-snapshot-manifest-api.md),
[docs/parallel/raw-snapshot-row-map-api.md](docs/parallel/raw-snapshot-row-map-api.md)).
The 007-l continuation selectively integrates the TWENTY-THREE
root-reviewed immutable owned-GPU parent/identity and native
runtime-identity files (oap/reviews/007-l-parent-native-
components.json, 250,571 bytes, byte-exact from the two exact
source commits 9ac0eabd and d7701a53): the owned GPU embedding
worker parent (creating-process retained lock in the strong
owner registry, lock-close race, raw worker identity, single
initialization refused before any owner/process/FD/lock/
registry mutation, original Popen pre-return capture), the raw
GPU worker-identity predictor/validator (canonical selected-
file bytes with domain-separated fingerprint; a record is
data, never authorization) and the native runtime-identity
leaf plus the TokenIDSession acquisition corrections (owned
Popen retained before fallible initialization, independent
strong pending owner, fork refusal, creator/once/closed/
context/error precedence, bounded no-follow artifact
identity). They are finite model-free software: parent and
identity proofs run against the actual offline fixture with
fake/null namespaces and synthetic copied entries, and the
token work uses the actual native 0.21.4 tokenizer worker on
synthetic strings — no real GPU, driver, Tensor, model,
parity, rights or Ready is established; the GPU text bridge,
producer, controller and durable GPU execution remain
unimplemented; two authorized test-only
portability exceptions (Root addenda 1/2/3) replace the
frozen FILE unit's 32 MiB+1 fixture-file creation with an
exact device/inode fstat size boundary under the
inherited CI FSIZE cap, and the CPU-session composition's
public-class Popen replacement spy with a real
Popen.__init__ spy (the integrated exact-class guard
refuses a replaced public class) while all other 22 files
and all production guards/limits stay byte-exact; whole
007 remains PARTIAL
([docs/parallel/owned-gpu-worker-api.md](docs/parallel/owned-gpu-worker-api.md),
[docs/parallel/gpu-worker-identity-api.md](docs/parallel/gpu-worker-identity-api.md),
[docs/parallel/embedding-native-runtime-identity-api.md](docs/parallel/embedding-native-runtime-identity-api.md),
[docs/parallel/embedding-tokenizer-api.md](docs/parallel/embedding-tokenizer-api.md)).
Objective 006 merged to main as PR #8 (merge commit 11badc7); objective
007 remains PARTIAL — the CPU reference path (now selecting the CPUv2
lock) plus the cleanup/lease/isolated-exit composition, the 007-j GPU
child/protocol/launch/assets software, the 007-k pure snapshot
declaration codecs, the 007-l owned GPU parent/identity and
native runtime-identity software and the inert raw GPU backend
source are software under trusted neural fakes only (no real
GPU, driver, Tensor or model was run).
Execution scope is precise: the archived prior OWNED random CPU toy
was historically executed (toy evidence only); the ACTUAL BGE
checkpoint/model has NOT been executed or qualified, and a class
import is not model construction or a forward pass; the current
38-dependency and class-level interoperability differs from real BGE
forward and both differ from the controlled neural fakes; the
resident CPU query encoder and the packaged CPU profile lock
assets are finite model-free software, but there is still no
actual-model CPU query execution, resumable GPU batches or
qualification yet
([docs/embedding.md](docs/embedding.md),
[docs/parallel/vector-codec-api.md](docs/parallel/vector-codec-api.md)).
Source-to-block anchors, native versus visual-needed page semantics,
refusal behavior, budgets and observed-count provenance are documented
in
[docs/ingestion.md](docs/ingestion.md) with the detailed per-adapter
contracts under [docs/parallel/](docs/parallel/). Contextualization,
embeddings, snapshot/retrieval, GPU/vision and all
model/license/ICA qualification remain open.

The target uses CPU query embedding/search and measured co-resident V100 Qwen Q6 + FP16
reranking, with separate long-context preprocessing and exclusive GPU bulk embedding modes.
Original documents remain the authority for citations. Generated context improves indexing.

- [Architecture](ARCHITECTURE.md) and [source precedence](SOURCE-MAP.md).
- [Original plan](PLAN.md) and [binding update](docs/sources/IMPLEMENTATION-UPDATE-2026-11-01.md).
- [Work program](oap/strategic-instructions/INITIAL-ROADMAP.md) and [requirement coverage](oap/COMPLETENESS.md).
- [OAP runbook](docs/OAP-RUNBOOK.md), [agent setup](docs/AGENT-ROLE-SETUP.md), [recovery](oap/RECOVERY.md).
- [Readiness](docs/READINESS.md), [security](SECURITY.md), [testing](TESTING.md), [DHA](CRITICAL.md).

Scaffold checks require Python 3 and standard POSIX tooling:

```sh
python3 -m unittest discover -s tests/oap -v
python3 oap/bin/check_state.py --repo-root .
```

These commands do not start agents, model services, product jobs or an OAP objective.

Product foundation (objective 002-a; `uv` required for the locked environment):

```sh
uv sync --locked
uv run raggedized --help
uv run raggedized doctor --config config/examples/example-config.json
uv run raggedized qualification gates   # offline section 23.2 prerequisite projection
uv run raggedized qualification plan --config CONFIG.json --spec SPEC.json   # offline, zero I/O
uv run raggedized resource diagnose --duration-seconds 1 --samples 4   # explicit opt-in, own-process only
uv run raggedized source import --root ROOT --store STORE --manifest MANIFEST.json   # local operator tool
uv run raggedized source inspect --store STORE --revision sha256:...   # verified revision read
uv run pytest tests/unit -q
uv run pytest tests/integration -q   # 003-b/i/j + 004-a: owned loopback HTTP/SSE, probe and trial composition, synthetic keys
```

`doctor` validates configuration and inspects model manifests offline (zero
inference/download/network; machine-readable JSON; exit 0 ok / 1 issues /
2 usage error). `probe` is the explicit opt-in bounded repeated-parent
qualification probe against the configured gateway route or
offline-diagnostic direct destination (explicit finite
deadline/dispatch/output-token budgets, bounded safe credential
resolution, safe structured evidence; exit 0 complete / 1
not-run-incomplete / 2 usage-config error with zero dispatches / 3
post-work evidence export failure — after the probe returned, whether
or not any dispatch occurred, as its spent-attempt ledger states —
with the full evidence on stdout; import, help and doctor never
dispatch a probe). `qualification` is the objective 004-a finite trial
runner: `gates` prints the machine-readable section 23.2 prerequisite
projection and `plan` validates one strict trial spec offline (both
zero model/HTTP/telemetry I/O; execution NOT_RUN); `run` is the explicit
opt-in execution of one repeated-parent trial against the configured
gateway route or offline-diagnostic direct destination through the real
adapters/transport (`--synthetic` for the deterministic owned MOCK
fixture; exit 0 complete execution status / 1 not-run-incomplete /
2 pre-dispatch refusal with zero dispatches / 3 post-work evidence
export failure). Full reference, spec fields, budget admission/
accounting semantics, quantile definition and evidence classes:
`source` is the objective 005-a local operator route: `import`
admits a bounded manifest (version 1, at most 128 approved sources
with explicit labels, processing approval and independent
redistribution rights) from an explicit approved root into a
private store, and `inspect` verifies and prints a stored
revision (exit 0 complete / 1 typed safe failure; help and import
perform zero network/model work; original bytes are never
printed).
[docs/benchmarks/qualification-protocol.md](docs/benchmarks/qualification-protocol.md),
[docs/foundation.md](docs/foundation.md) and
[docs/generator-contract.md](docs/generator-contract.md).

The `CI` GitHub Actions workflow runs the OAP scaffold checks (Python 3.12-3.14)
plus a separate product job (locked lightweight environment, real product
tests, owned-loopback integration tests, OAP checks, lint; Python 3.12/3.14;
triggers, permissions and results
in [docs/CI.md](docs/CI.md)). CI produces no hardware evidence; live model and
gateway qualification remains NOT RUN. The public product CLI currently
provides `raggedized doctor`, `probe` (explicit opt-in qualification
probe), `qualification gates|plan|run` (finite qualification trials,
explicit opt-in execution), `resource diagnose` (bounded local
telemetry diagnostic), `parity embedding|rerank` (supplied-value
analysis) and `source import|inspect` (local original admission/store
operator tool), plus `--help`/`--version`; further API commands remain
proposed, not available.
Apache-2.0; retain LICENSE and [THIRD_PARTY_NOTICES](THIRD_PARTY_NOTICES).
