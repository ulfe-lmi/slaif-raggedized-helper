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
Objective 006 merged to main as PR #8 (merge commit 11badc7); objective
007 remains PARTIAL — no encoder execution, CPU query, resumable GPU batches
or qualification yet
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
