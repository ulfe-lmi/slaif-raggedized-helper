# Verification contract

T01. Default product tests use synthetic owned fixtures and fake generator/embedding/reranker
interfaces; no key, network, GPU or model download. OAP tests use isolated temp repositories,
FIFOs and fake remote/tmux interfaces. Never exercise live project pipes during fixture tests.
T02. Run focused behavior/negative-path tests for the changed boundary. Add integration proof
for actual composition, filesystem crash/atomicity/concurrency, ACL, cancellations and retries.
Do not accept keyword/assertion-only checks as product behavior proof. Broad suites belong at
phase/release gates or when reproducing their failures, not repeated without a reason.
T03. Real route/model/GPU tests are opt-in and require exact authorized host/device/data/call
budgets, known profiles, fingerprints and safe rollback. Mock success is not real qualification.
Report PASSED/FAILED/SKIPPED/NOT RUN/BLOCKED/PENDING/MISSING exactly. No fake timing/usage/results.
T04. Keep final held-out evaluation separate from tuning and retain safe raw measurements.
Verify negative authorization, contradictory/insufficient evidence, source support, tokenizer
limits, FP16/FP32 parity, no direct fallback, corrupt snapshots, restart and mode contention.
T05. OAP scaffold check: `python3 -m unittest discover -s tests/oap -v`;
`python3 oap/bin/check_state.py --repo-root .` checks installed governance and orchestration.
Product foundation tests (objective 002-a): `uv sync --locked` then `uv run pytest tests/unit`
(synthetic fixtures only; no keys, network, GPU or model downloads; pytest exits 5 on empty
discovery, so the suite can never be falsely green by missing tests). The GitHub Actions
workflow `CI` (.github/workflows/oap.yml, see docs/CI.md) runs the OAP-scaffold checks
(Python 3.12-3.14) plus a product job: locked lightweight environment, real product tests,
OAP checks and lint from a clean checkout (Python 3.12/3.14). Required final-head checks are
read from live policy; zero checks never means product verification has passed.

T06. Real controlled HTTP/SSE behavior tests (objective 003): `uv run pytest
tests/integration -q` runs the transport, gateway and native direct suites against
owned 127.0.0.1 loopback servers that record exact path/headers/body; unique
synthetic API-key canaries only. Still synthetic and offline: no external network,
product services, real keys, GPU or model downloads. They prove wire-path
resolution, total-deadline/retry/UNKNOWN_COMPLETION semantics, literal SSE byte
parsing, bounded queue backpressure, cancellation, the pinned Responses dialect
(003-b/c/d) and the pinned native `/apply-template` + `/completion` dialect
(003-e: exact envelopes, server-rendered template contract including literal
untrusted content forwarded unchanged, tested-only cache/slot controls, the
stop-terminal matrix, distinct-facts metric mapping and refusal zero-dispatch;
003-f: correct metric quantities with a reported 0ms kept as a known zero,
TTFT unavailable, safe overflow/numeric handling, default-deny unqualified
JSON/schema admission with qualified positive controls, and contradictory
evaluated/cache counter withholding; 003-g: safe finite native phase-total
arithmetic (both 1e308 ms phases kept finite with the derived total
computed in seconds, no overflow out of generate()) and explicit required
JSON_MODE capability admission (zero dispatch while untested, qualified
positive control without invented format, ordinary TEXT/no-format
preserved); see docs/generator-contract.md). The
product CI job runs them alongside
tests/unit and product lint from a clean locked install.


T07. Bounded probe composition (objectives 003-h/003-i/003-j): `uv run
pytest tests/integration/test_probe_composition.py -q` runs the
INSTALLED `raggedized` CLI in subprocesses with the real
gateway/native adapters against owned 127.0.0.1 loopback servers
(synthetic canaries only): exact request count/order/control payloads,
finite aggregate budgets across the pair and retries (single
experiment deadline; call allowance reserved before every transport
invocation; ambiguous work spent, never replayed; no bypass by
retries/template work), no implicit dispatch on
import/help/doctor/missing opt-in, invalid config and absent or
invalid credentials (owned FIFO, directory, invalid UTF-8,
control-character and non-ASCII values — including the 0x80-0xFF
Latin-1 range that the locked HTTPX 0.28.1 ASCII string-header
serializer cannot encode, file and env references alike — refused
without a blocking open, no child process killed, and no raw
UnicodeEncodeError, at zero HTTP with the fixed typed
`value_not_ascii` reason; a knowably invalid `--output` destination
refused before dispatch (exit 2) and a post-work evidence write
failure after actual dispatches returning the honest exit-3
export-stage error with the full spent-attempt evidence on stdout,
missing-metric nulls, label-independent same/different output
evidence with the installed-CLI expected-output positive and mismatch
(documented namespaced fingerprint digests, not plain-text
sha256sums), reported-vs-validated cache counters (valid present
qualifies; contradictory cached/input is `metrics_invalid` with raw
facts preserved; uncheckable is `metrics_unvalidated`; absent stays
`metrics_unavailable`), the exported declared backend fingerprint with
`target_type: unverified`, no private credential file path or value in
evidence, and no endpoint URL, credential, raw prompt/response text or
provider error. The probe budget/boundary/credential unit regressions
live in tests/unit/test_probes.py; the gateway explicit-minimum
capability admission regressions (zero-HTTP refusal of required
JSON_MODE/PROMPT_CACHING on an unqualified route plus qualified
minimum-only positive controls) extend the gateway loopback suite.
All synthetic and offline: no external network, product services,
real keys, GPU or model downloads. Real runtime/cache/quality
qualification remains NOT RUN.

T08. Finite qualification trial composition (objective 004-a, evidence-contract corrections
004-b/004-c): `uv run pytest tests/integration/test_qualification_composition.py -q` runs the
INSTALLED `raggedized qualification` CLI in subprocesses against owned 127.0.0.1 loopback
servers (synthetic canaries only): shared dispatch allowance across warmups/repetitions/retries
for both dialects, bounded spec file input refusals, strict evidence contracts with the analysis
pure-recomputation driven by the actual transport ledger, honest post-work export-stage failures
and zero-dispatch plan/gates/help. Unit contracts live in tests/unit/test_qualification.py.
Full command coverage, stage-metric and NOT-RUN distinctions: docs/benchmarks/
qualification-testing.md (T08). All synthetic and offline; real qualification NOT RUN.

T09. Bounded local resource telemetry (objectives 004-d, 004-e corrections): `uv run pytest
tests/unit/test_qualification_resources.py -q` and `uv run pytest
tests/integration/test_qualification_resources.py -q` cover the strict versioned observation
DTOs, own-process probes, the bounded fixed-argv nvidia-smi query against owned deterministic
collector executables, the narrow trusted observer and the zero-telemetry import/help negative,
plus the installed `raggedized resource diagnose` and `qualification run --resources`
composition (plain v1 trial byte-intact inside the explicit versioned wrapper, every-exit-path
observer stop, late-export spent accounting). Full command coverage and NOT-RUN distinctions:
docs/benchmarks/qualification-testing.md (T09). All synthetic and owned; real GPU/model
qualification NOT RUN (D0 local observational allowance only).

T10. Supplied-value parity and gate projection (objective 004-f): four parity unit suites
(embedding, rerank, shared safe file I/O, CLI/gates) cover the pure supplied-value analyzers,
the shared bounded safe I/O layer and the canonical fourteen-gate projection bound to the
committed docs/benchmarks/qualification-gates.json; integration suites run the INSTALLED
`raggedized parity embedding|rerank --input FILE --output FILE` on owned disposable files with
the exit 0/2/3 matrix. Full command coverage and NOT-RUN distinctions: docs/benchmarks/
qualification-testing.md (T10). All synthetic and offline; real qualification NOT RUN.

T11. Bounded local source admission and installed source CLI (objective 005-a): `uv run
pytest tests/unit/test_source_admission.py tests/unit/test_source_cli.py
tests/integration/test_source_admission_composition.py
tests/integration/test_source_module_cli.py tests/integration/test_source_installed_cli.py -q`
runs the strict versioned manifest/store contracts and the INSTALLED `raggedized source
import|inspect` route (thin delegation to the module entrypoint) in subprocesses on owned
disposable roots/stores: two synthetic logical documents sharing bytes with distinct
rights/ACL/corpus produce separate immutable revisions over one verified shared blob, a
metadata correction publishes a new revision while the unchanged document and blob are reused,
inspect verifies record/blob binding and read_original returns exact bytes; negatives exercise
actual descriptors for traversal/symlink/intermediate replacement/special files, oversized and
growing streams, corrupt stored artifacts, conflicting immutable objects, interrupted
publication with safe retry, unchecked-copy escape and atime-only changes, all with fixed
safe input-free errors that never echo source passages or private paths, and guarded
help/import at zero network/model work. All synthetic and offline: no extraction, parsing,
network fetch, models, GPU or real corpus; operator approval is metadata, not authentication.
Source serving, provenance/job records and 006 extraction remain later ordered scope; real
qualification NOT RUN.

T12. Combined canonical 005 record journey (objective 005-b): `uv run pytest
tests/integration/test_canonical_records_journey.py -q` composes the actual
005-a `OriginalStore` with the merged provenance and job record modules in ONE
owned journey: two synthetic logical documents sharing bytes with distinct
corpus/labels/rights and a metadata-corrected revision over one verified blob;
exact byte load via `read_original`; synthetic native Block/Dependency records
with astral/combining/CRLF content; start-inclusive/end-exclusive code-point
multi-span chunks with explicit separators and a repeated original table-header
reference; Registry chunk/neighbor binding with reciprocal links; same-source
derived support (label union, cross-boundary and cross-revision rejection);
pure reader grant/restriction intersection with unknown-version fail-closed;
and `JobSpec`/`JobState`/`Attempt` admission, serialization roundtrip and
bounded transitions (COMPLETE with an asserted-only verified output reference,
UNKNOWN_COMPLETION without automatic retry, RETRYABLE_FAILED retry with a fresh
attempt ID). Forged spans, conflicting copied text, boolean/out-of-range
offsets, wrong revision/dependency/hash and missing labels are refused with
input-free errors. The candidate unit suites (`test_provenance_records.py`,
`test_job_records.py`) and component composition suites cover the remaining
per-record negative boundaries. All synthetic and offline: no extraction,
parsing, network, models, GPU or real corpus; supplied text/counts are
assertions, not executed parsers or qualified tokenizer measurements; DTO
COMPLETE is not artifact or cache proof. Real qualification NOT RUN.

T13. Combined canonical 006 first-slice extraction (objective 006-a):
`uv run pytest tests/unit/test_text_extraction.py tests/unit/test_structured_text.py
tests/unit/test_pdf_extraction.py tests/integration/test_text_extraction_composition.py
tests/integration/test_structured_text_composition.py
tests/integration/test_pdf_extraction_composition.py
tests/integration/test_extraction_combined.py -q` runs the merged native
extraction adapters on owned synthetic originals: literal line and bounded
structural adapters with exact Unicode code-point coverage (half-open ranges
tiling the decoded original) and the fixed trusted isolated PDF worker
(pdfminer.six 20260107 in a private pinned hash-verified environment under
`/usr/bin/prlimit` + `/usr/bin/bwrap`), composing manifest ->
`OriginalStore` -> all three adapters -> `provenance.Registry` in ONE journey
with shared-byte distinct scopes, a metadata revision over one verified
blob, source immutability and safe refusals. The required PDF tests fail
explicitly (never skip) when `PDF_TEST_RUNTIME`/`PDF_TEST_PACKAGES`, the
backend or the isolation is absent or invalid; product CI provisions the
DEV-only pinned backend per run. Full command coverage, isolation and
NOT-RUN distinctions: docs/benchmarks/ingestion-count-storage.md (T13). Order 006-e integrates the conservative literal structure classifier into the PDF adapter (pdf-literal-structure-v3, policy definition v4, shared kind-bound block fingerprint v2; classifier v2 / policy v3 records are immutable and require explicit re-extraction): `tests/unit/test_pdf_structure.py` (grammar, admission bounds, two-second deadline, terminator and incomplete-prefix limits) and `tests/integration/test_native_pdf_structure.py` (owned reduced-policy small and closing, default-policy and fitting-warning PDFs through extraction and native chunking; every row chunk retains the original header; full coverage and tail preserved) join the T13 command under the same backends. All synthetic and offline; real qualification NOT RUN.

T14. Combined canonical 006 observed-count journey (objectives
006-b/006-c): `uv run pytest tests/unit/test_native_tokenizers.py
tests/unit/test_native_chunking.py
tests/integration/test_native_chunking_composition.py
tests/integration/test_native_extraction_counts.py -q` runs the merged
native count/chunk stack on owned synthetic originals: manifest ->
OriginalStore -> line/structure/PDF extraction -> Registry ->
native_chunking.build with three OBSERVED local token counts and receipts
per chunk (exact role inputs, artifact SHA, backend,
revision/preprocessing, input digests), 512/768/1024 budgets, up-to-64-token
word-boundary overlap, no discarded tail, reciprocal neighbors,
deterministic rebuild, same-byte distinct IDs and cross-source denial,
native pair 1280/reserve 64 with strict smaller-policy refusal, legacy
callback pair 512 kept SUPPLIED_UNVERIFIED, and independent session
re-counts. Current 006-c bounds: Session hard caps 16,384 calls / 32 MB
input / 4 MB output; builder deadline 15,000 ms native default / 5,000 ms
legacy explicit default (max 15,000 ms); per-build reuse removes duplicate
identical count requests; policy definition v2 binds the exact UTF-8 SHA-256
query digest (10,000-character query bound kept; native v1 identity and
receipt fingerprints unchanged). Representative-scale 7876-byte procedure
and 9269-byte table sources complete under the current caps (exact observed
session call counts 1,305 and 1,657), and the hard-quota negative is a
standalone Session seeded at 16,384 calls whose next count refuses with
owned-child cleanup. The required native tests fail explicitly (never skip)
when SLAIF_NATIVE_TEST_ROOT/PACKAGES/PYTHON, the backend or the isolation is
absent or invalid; product CI provisions the NEW private pinned
hash-verified engine-only tokenizers 0.21.4 capsule per run on both Python
3.12/3.14 legs with literal GITHUB_ENV bindings (helper output never
sourced). Full command coverage, observed results, component storage
composition (T14a) and NOT-RUN distinctions:
docs/benchmarks/ingestion-count-storage.md. The capsule is DEV-only
(engine-only --no-deps; no dependency/lock/allowlist/license change); toy
artifacts only — no deployed-model equivalence, serving, hardware, license
or quality claim. Real qualification NOT RUN.

T15. Installed private chunk/inspect operator and complete semantic
bundle (objective 006-d): `uv run pytest tests/unit/test_chunk_cli.py
tests/unit/test_ingestion_prepare.py
tests/integration/test_chunk_cli_composition.py -q` with the T13/T14
dev backends runs the INSTALLED `raggedized chunk` and
`raggedized chunk inspect` routes in subprocesses on owned private
stores: prepare + durable publication under an explicit operator
profile (actual private CPU tokenizer session and isolated PDF
worker), the bounded JSON overview, exit 0/1/2 semantics,
`no_native_chunks` with `source_status` partial visual truth, the
known `published_bundle_id` retained on later failure, idempotent
canonical retries, coherent cross-revision semantic refusal,
corruption/profile/hash/backend/policy/query refusals and the
cooperative 180-second budget. The six combined extraction/count
integration composition suites (T13/T14: text/structured/PDF
extraction composition, extraction combined, native chunking
composition and native extraction counts; 49 cases) re-run unchanged
after integration with no skip or fallback. Full command coverage,
backend setup, the four-fresh-read derived-store semantics and NOT-RUN
distinctions: docs/benchmarks/ingestion-count-storage.md (T15). All
synthetic and offline; real qualification NOT RUN.

T16. 007-a..j: 007-a..h per H docs; 007-i resident query + profile locks; 007-j GPU child/launch/assets (fake/null ns, no real GPU/model; 8/1/1). BGE UNRUN/UNQUALIFIED; GPU parent/lock/identity unintegrated; H actual-38 + toy kept; host full-unit fault UNRESOLVED. Real qualification NOT RUN.
