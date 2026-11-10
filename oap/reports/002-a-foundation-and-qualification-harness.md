# OAP Coding Report — 002-a

Identifier: 002-a
Result: COMPLETE
Repository: ulfe-lmi/slaif-raggedized-helper
PR number: 4
Branch: oap/002-foundation-and-qualification-harness
Base branch: main
Implementation head SHA: 6878f83417c31d9fde9349830556388c82efc9b8
Report publication commit: SELF

## Work and scope

Executed oap/orders/002-a-foundation-and-qualification-harness.md (Status FINAL,
active 002-a) on a fresh branch oap/002-foundation-and-qualification-harness from
verified origin/main 3178650b241c249b80b8e1e2a9427356996ecacc (order Base commit).
One objective PR (#4), created via gh. Single implementation commit
6878f83417c31d9fde9349830556388c82efc9b8 (34 files, +3910/-26) changed:

- pyproject.toml, uv.lock, .python-version: installable src-layout package
  `slaif-raggedized-helper` 0.1.0 (hatchling, console entry `raggedized`,
  requires-python >=3.12); locked lightweight environment — runtime: pydantic
  2.14.3 (+pydantic-core 2.50.4, annotated-types 0.8.0, typing-extensions
  4.16.0, typing-inspection 0.4.5); dev: pytest 8.4.2, ruff 0.17.4 (+pluggy,
  iniconfig, packaging, colorama, Pygments). No Torch/Transformers/
  SentenceTransformers anywhere in the lock.
- src/slaif_raggedized_helper/: __init__.py, _constraints.py, config.py
  (strict RaggedizedConfig/GeneratorConfig/RouteConfig/ProfileConfig/
  EmbeddingPolicy/DegradationPolicy/DirectGenerationConfig/SecretRef +
  redacted error rendering), schema.py (GeneratorRequest/Result, Usage/Timing
  Metrics, EmbeddingDefinition/Execution with canonical versioned
  fingerprints, RerankRequest/Result + bind_rerank_scores, ModelLock,
  QualificationRecord, ModelManifest.evaluate promotion), model_clients/base.py
  (small structural Protocols only), cli.py (`raggedized --version/--help`,
  `raggedized doctor --config PATH`; exit 0 ok / 1 issues / 2 usage; offline;
  machine-readable JSON; readiness vs config validity; issue codes
  CONFIG_*/ROUTE_MISSING/SECRETS_MISSING/SECRET_ABSENT/PROFILES_MISSING/
  MODEL_COVERAGE_MISSING/MODEL_LOCK_*/MODEL_ROLE_MISMATCH/MODEL_UNQUALIFIED).
- config/: examples/example-config.json (route on RFC 6762-reserved
  gateway.invalid placeholder), examples/model-locks/*.json (three explicitly
  unqualified placeholder manifests), schema/app-config.schema.json and
  schema/model-manifest.schema.json (generated from the Pydantic models).
- tests/unit/: five focused suites (80 tests): config refusal boundaries,
  contract invariants (outcomes, null-not-zero metrics, space fingerprint
  distinctions, pair binding), lock/qualification promotion, doctor CLI
  semantics (exit codes, safe JSON, offline/no-network, secret canaries,
  URL-secret redaction, role coverage/mismatch, no-success-by-omission),
  import hygiene (no heavy modules/distributions).
- tests/oap/test_harness.py: ordered fixture fix — copy_owned_source now omits
  ignored/private/heavy directories AND private files (.env/.env.*, runtime.json,
  eval/private) via a path-aware ignore function; new boundary test plants
  runtime-assembled canary content (never literal in source) in owned fixture
  temp locations and proves it is not copied and not in the committed tree;
  owned source preservation asserted. No real private data written or deleted.
- .github/workflows/oap.yml: added one separate `product-tests` job (Python
  3.12/3.14: matrix .python-version pin, pinned uv 0.12.5, uv sync --locked,
  ruff product lint, compileall, pytest tests/unit, existing OAP suite +
  check_state, raggedized --help, doctor example asserting exit 1 +
  MODEL_UNQUALIFIED + readiness not_ready). The three governance jobs are
  byte-unchanged.
- docs/foundation.md (new), README.md, TESTING.md, STATUS.md, docs/CI.md
  (updated), THIRD_PARTY_NOTICES (new; exact locked versions + licenses from
  official PyPI metadata 2026-11-10; hatchling noted as build-system range
  `>=1.25,<2`, not locked, MIT; model/license clearance explicitly unresolved).
- oap/active (002-a), oap/orders/002-a-*.md: activated strategic bytes committed
  unchanged. oap/reviews/001-resolution.json: pre-published strategic resolution
  committed unchanged.
- oap/governance/MANIFEST.json + CONTEXT-BUDGET.md: hash/byte refresh for the
  changed governed files only (TESTING.md, tests/oap/test_harness.py,
  CONTEXT-BUDGET.md); declared context total 34378 -> 34594 bytes (ceiling
  50000). check_state reports activation_matches_current_governance=false for
  this authorized candidate governance change, per the protocol source note.

Strategic prepublication review findings (same order, in-round) were fixed and
regression-tested before publication: ModelIdentity.declared_capabilities
added; negative usage counts rejected; output_reserve < context_expected
enforced; FP32 storage required (qualified GPU FP32 offline-embed corpus mode
kept allowed); URL query/fragment refused; env SecretRef name grammar;
required-role coverage + role match + SECRETS_MISSING/SECRET_ABSENT +
config/readiness distinction in doctor; malformed config/manifest errors never
echo input values (URL credential redaction canary-tested).

## Acceptance evidence

1. Installable src layout, `raggedized` entry, Python >=3.12, uv lock; no heavy
   ML import: clean-checkout `uv sync --locked` + console entry verified;
   `tests/unit/test_import_hygiene.py` asserts no torch/transformers/
   sentence_transformers/cuda modules loaded after import+doctor and no heavy
   distributions installed; lock contains only the 12 lightweight artifacts
   above.
2. Strict config: tests/unit/test_config.py — unknown fields refused at every
   level; inf/nan/nonpositive budgets refused; purpose/device/dtype matrix
   (CPU FP32 online query default, GPU FP16 reranker, exclusive-GPU offline
   embedding with FP32 store, qualified GPU FP32 corpus mode allowed);
   direct-generation enabled refused; implicit degradation refused;
   userinfo/query/fragment URL credentials refused; env-name grammar;
   rejected-config error never echoes an embedded URL secret; missing route is
   a valid config + honest doctor issue.
3. Typed contracts: tests/unit/test_contracts.py — terminal/refusal/failed/
   incomplete/unknown_completion outcomes with consistency rules; missing
   usage counts serialize as null (not zero) and negatives rejected; visual
   purpose requires authorized images; required capabilities must be declared;
   bounded trusted input; embedding space fingerprint differs for
   dimension/pooling/normalize/query-policy/checkpoint changes while execution
   fingerprint separates device/precision from the space; rerank pair-ID
   uniqueness, finite scores, exact one-score-per-pair binding.
4. Model lock/qualification: tests/unit/test_model_lock.py — example
   unqualified manifests evaluate unqualified with explicit NOT RUN/unknown
   license/missing artifact issues and a "not proof" note; promotion requires
   approved license + pinned artifact + live pass record with matching
   model_scope; mock/fail/blocked/mismatched evidence fails promotion; GGUF
   generator-only; 64-hex hashes; explicit-UTC timestamps; finite-or-null
   metrics.
5. `raggedized doctor --config PATH`: tests/unit/test_cli_doctor.py — exit 0
   only with full role coverage + qualified manifests + present secrets
   (readiness ready); exit 1 with machine-readable issues otherwise (valid
   config without manifests/secrets is config valid / readiness not_ready,
   never success by omission); role mismatch, missing lock, invalid manifest
   (redacted) codes; --help/--version offline; socket-blocked doctor runs
   (zero network); env/file secret canary value never appears in any output.
   Live run on the shipped example: exit 1, status issues, config valid,
   readiness not_ready, codes MODEL_UNQUALIFIED x3 + SECRET_ABSENT.
6. Focused meaningful tests + CI: 80 product tests (cross-field/behavior, not
   type mirrors); CI `product-tests` installs the locked environment from a
   clean checkout, runs pytest (exit 5 on empty discovery), the existing OAP
   suite + check_state, lint and the doctor example assertion.

## Verification

Exact commands and results (local + clean checkout of implementation head
6878f83417c31d9fde9349830556388c82efc9b8):

- `git fetch origin && git rev-parse origin/main` -> 3178650b241c249b80b8e1e2a9427356996ecacc
  (matches order Base commit); `gh pr list --state all` -> PRs #1/#2/#3 MERGED,
  no open PR before this round; main CI 42728594431 success on that commit.
- `uv lock` -> 13 packages resolved (12 artifacts + project); `uv sync --locked`
  on CPython 3.14.4.
- `python3 -m unittest discover -s tests/oap -v` -> Ran 41 tests, OK (40 prior
  scaffold tests + 1 new source-copy boundary test).
- `uv run pytest tests/unit -q` -> 80 passed.
- `uv run ruff check src tests/unit` -> All checks passed (product scope; OAP
  scaffold is governance-owned compact style, out of product lint scope).
- `python3 oap/bin/check_state.py --repo-root .` -> state ACTIVE, active 002-a,
  order validated, governance verified (manifest refreshed for changed governed
  files; activation_matches_current_governance=false per authorized candidate
  governance change), exit 0.
- Clean checkout (`git clone` of the implementation commit to a temp dir, then
  `uv sync --locked`, full sweep): OAP 41 OK, pytest 80 passed, ruff clean,
  check_state OK, `raggedized --help` OK, doctor example exit 1 — all green.
- Pushed branch; `gh pr create` -> PR #4 (base main).
- Implementation-head CI run 42734169022 on 6878f83417c31d9fde9349830556388c82efc9b8:
  OAP tests (Python 3.12) pass, (3.13) pass, (3.14) pass; Product tests
  (Python 3.12) pass, (3.14) pass; run conclusion success. No in-scope repair
  needed.

Mock/live distinction: all executed tests are synthetic/mock (no keys, network,
GPU, models or downloads; canaries are fixture-owned synthetic values). Live
evidence is limited to read-only GitHub/CI observations and official PyPI
metadata queries for package licenses. No live gateway/model/GPU call,
inference, download, service change or protected-resource access occurred.
This report cannot certify its own future push/CI; the post-publication receipt
and strategic review record those facts separately.

## Documentation impact

- New docs/foundation.md: commands, full config reference (fields, matrix,
  invariants), contract semantics, model lock/qualification and promotion
  rules, doctor report/issue-code reference, test instructions, reproducible
  environment, and honest unresolved-artifact state (no deployed route, no
  downloaded/pinned/approved models, no live trials; no invented hostnames or
  legal clearance).
- README.md: product section (install/doctor/test commands) added; scaffold
  section preserved.
- TESTING.md (governed; manifest hash refreshed): product test commands and CI
  product job documented; T01-T04 preserved.
- docs/CI.md: product job definition/steps documented; scaffold description
  preserved.
- STATUS.md: 002-a state recorded without claiming MVP done; live PR/merge
  state deliberately left to GitHub.
- THIRD_PARTY_NOTICES: exact locked versions + official metadata licenses;
  hatchling stated as unlocked build-system range; model/runtime licenses
  explicitly unresolved.
- Governance manifest/context refreshed for changed governed files only.

## DHA and boundaries

Order DHA declaration: Decision: NONE. No critical append ordered or performed;
CRITICAL.md untouched. Preserved: unrelated branches/worktrees (000/001,
docs/architecture-blueprint-v2, local main), the gateway checkout and its FIFOs
(untouched this round), private configs (never read or published by this agent),
historical orders/reports/receipts, strategic home. No merge performed; no
auto-merge, tag, release or deployment. No model/provider/profile change. No
nested or second consumer started; the sole external wrapper consumed the
control notification before this round.

## Limitations and remaining work

- Foundation code and mocked contract composition only: product runtime
  qualification remains NOT RUN/UNKNOWN; no real model, GPU, tokenizer or
  artifact was downloaded, loaded or executed.
- Deployed gateway route (base URL/commit/capabilities) and secure key
  provisioning remain unknown (docs/environment-inventory.md section 4); the
  example route uses a non-resolving .invalid placeholder.
- Model licenses/status are explicit unknowns; THIRD_PARTY_NOTICES covers the
  locked lightweight packages only — transitive model/runtime license audit is
  later work.
- Report-head CI and strategic review of the exact reviewed head/checks are
  future facts for the separate receipt; not certified here.
