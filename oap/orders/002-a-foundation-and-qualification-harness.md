# OAP Work Order — 002-a

Status: FINAL
Identifier: 002-a
PR mode: CREATE_NEW_PR
Branch: oap/002-foundation-and-qualification-harness
Base commit: 3178650b241c249b80b8e1e2a9427356996ecacc
PR number: NEW
Expected active: 001-a
Provenance: H current MVP execution mandate; A03 A04 A08 A13 A35 A36 A37
Architecture SHA256: 4b41905396a3838269fd6cf372614cd23cb2c3b6a37be09f29ed752803c0983a
Governance SHA256: 686ee95fe6c36d6b5647824c8d5fbe5894daaf60600ba0f043a3cc3979e3afce

## Objective

Create an installable minimal application foundation with strict configuration, reusable
generator/embedding/reranker contracts, honest qualification results and a useful offline
doctor command. Do not build speculative application layers or a new governance platform.
This slice must leave subsequent adapters and artifact services with one coherent contract.

## Dependencies and current state

Verified 2026-11-10: PR3/001 merged 2026-11-10T00:28:38Z, main 3178650b241c249b80b8e1e2a9427356996ecacc; final PR CI 42728526859 and main CI 42728594431 passed all 3 jobs; merge tree equals reviewed SELF. No open PR. Existing local branch 001 has clean tracked files and only strategic resolution001 untracked. Reconcile/preserve, then create new branch from origin/main. Read docs/environment-inventory.md and current main/PR/CI/OAP. Unknown live values
remain unknown. All safe schema/client-contract and packaging work can proceed without GPUs.
Source architecture §§2.1,6,8.2,17.1,20.1 and23 are the relevant full excerpts; routine compact
law remains required. Full input source plans need not be reloaded every ordinary turn.

## Allowed paths and scope

pyproject.toml, uv.lock, .python-version if useful; src/slaif_raggedized_helper/ __init__,
config.py, contracts/ or schema.py, model_clients/base.py and evaluation result contracts,
cli.py; focused config/*.json examples/schemas (TOML/JSON safe standard-library parsing is
adequate; YAML optional only if needed); tests/unit/ and existing tests/oap fixture compatibility
only if a concrete packaging issue appears. docs/foundation.md, README, TESTING, STATUS,
THIRD_PARTY_NOTICES seed and model/license manifests with unresolved artifacts clearly marked.
.github/workflows/oap.yml may add a minimal separate product test/install job that runs actual
new tests. Preserve existing three governance jobs. Lock the environment reproducibly.
Only authorized changed governed files get manifest/context refresh. Immutable order/active
and final report follow standard protocol. No unrelated roadmap/source-law rewrite.
Commit the pre-published strategic oap/reviews/001-resolution.json unchanged with this work;
it is authoritative recorded resolution of the previous objective, not unrelated local trash.

Known existing fixture concern: tests/oap/Harness currently copies SOURCE recursively except
__pycache__/.git/.oap-state. A new .venv and later corpora/model caches must not be copied into
every fixture or accidentally committed in temporary test repos. Narrowly fix its source-copy
exclusions to keep owned source/code/governance only and omit ignored/private/heavy directories;
add a meaningful boundary test with canary ignored content in an owned source fixture. Do not
delete real .venv/caches/corpus or change immutable transcripts to make a test pass.

## Non-goals

No real model/GPU download or inference, tokenizer fetching, web API server, source ingestion,
snapshot or agent framework, database, orchestrator platform, broad abstract base-class tree,
authentication implementation, legacy/gateway project edits or post-MVP concept behavior.
No human-owner/referral feature, process/model/profile switch, production/tag/release/deploy.
Bootstrap mechanics already ran successfully: do not repeatedly read the whole helper library,
historic reports, inert proposals or diff a finalized order against its intentionally inert
draft. Read compact governance and selected source excerpts once, run check_state, reconcile
GitHub, then implement. An exact implementation failure justifies a focused helper read.

## Acceptance criteria

1. Package installs from source with src layout, named raggedized console entry and Python
   >=3.12 support. Use uv lock; do not load Torch/Transformers/SentenceTransformers on import.
   Heavy model dependencies belong to later explicit optional groups. This slice needs only
   actually used lightweight validated-contract/runtime/test dependencies (e.g. Pydantic v2,
   HTTPX for next adapter if genuinely used, pytest/Ruff as dev tools). Pin exact artifacts.
2. Configuration rejects unknown fields, invalid/non-finite/nonpositive budgets, mismatched
   profile purpose/device/dtype, enabled direct online generation and implicit degradation.
   Explicit online CPU FP32 query defaults, GPU FP16 reranker, exclusive offline embedding
   policy, generator context expectation/output reserve/finite deadlines. Keep secret *names*
   or secret-file references; never store raw secret literals or serialize env secret values.
   Network destination/userinfo validation prevents embedding credentials in URL. Missing
   deployment route/artifacts is an honest doctor issue, not guessed config or import failure.
3. Typed semantic generator request/result contracts include purpose, bounded trusted input,
   optional authorized images, model/adapter identity, output/time budget, supported-capability
   declarations, explicit terminal/refusal/failed/incomplete/unknown-completion outcomes, and
   available usage/prefill/timing. Missing counts are null/unavailable, not invented zero.
   Embedding definition separates checkpoint/tokenizer/pooling/L2/query policy/dimension from
   execution device/precision. Rerank contract binds pair IDs and finite results without truth
   confidence claims. Keep protocols small and adapter-injectable; no abstract framework.
4. Model lock schema records exact immutable revision/artifact hashes and license status,
   including explicit unknowns, tokenizer/pooling and Qwen GGUF/projector/runtime metadata.
   Example unqualified manifest cannot be mistaken for downloaded/pinned/approved model proof.
   Qualification record identifies named test, timestamp, code/model/runtime scope, mock/live,
   status and optional measured metrics; incompatible/missing evidence fails promotion.
5. `raggedized doctor --config PATH` (or equivalent documented command) validates local config,
   inspects manifest qualification and returns safe machine-readable status with actionable
   missing prerequisites. It performs zero inference/download/network by default and reveals
   no secret values even if provided via a canary env variable. `--help` works offline.
6. Focused meaningful tests prove config refusal, no-network/no-CUDA import/doctor, unknown
   metric preservation, unsupported-direct-online refusal, space fingerprint distinctions and
   CLI exit/result semantics. CI installs locked lightweight groups and runs the real product
   tests plus existing OAP checks from a clean checkout; no falsely green empty discovery.

## Verification and negative evidence

Run lock validation/install, focused product tests, existing governance suite and check_state,
lint if configured, console help and doctor examples from a clean env/checkout. Negative tests
patch HTTP/model import boundaries and use secret canaries; verify no value appears in repr,
JSON/logs/errors. Invalid examples cannot accidentally contact a route. Use normal official
package metadata/docs to establish current versions/licenses; no speculative compatibility.
Do not write dozens of tests that only mirror Pydantic types; test cross-field invariants and
external CLI behavior. No complete future product/hardware suite or real benchmark claimed.

## Documentation

Document implemented commands/config/contracts, lock/install/test instructions and development
dependency notices. Describe unresolved model artifacts/live trials without inventing exact
hostnames or legal clearance. Retain doc/source/architecture digests; status differentiates
foundation code, mocked composition and actual model readiness.

## Runtime and protected resources

Current human MVP activation authorizes ordinary local package/development tooling installation
and GitHub PR/CI. Packages from standard registries and lightweight dev dependencies are allowed.
Live product inference/GPU allocation/protected service modification: NONE in this objective.
Use synthetic fixtures and owned temp directories. Coding owns Git execution and never merges.

## Deferred human adjudication
- Decision: NONE

## Publication and report

One new objective branch/PR, unchanged strategic order/active. Implement/test/document, push,
inspect/repair safe in-scope CI before immutable report-only SELF commit. Report literal full
implementation parent and exact evidence with mock/live distinction. Verify remote report and
send exact response OK, then one idle waiter. Standing MVP delegation covers the next strategic
order, but coding never chooses that number or merges. Strategy independently reviews gates.
