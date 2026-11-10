# Foundation — installable package, strict config, contracts, doctor (OAP 002-a)

Scope: the minimal application foundation for the raggedized helper — an
installable `src` package, strict configuration, typed generator/embedding/
reranker contracts, model lock/qualification schemas, and an offline
`raggedized doctor` command. Explicitly **not** in this slice: real model or
GPU work, gateway adapters, snapshot/agent framework, API server, web UI,
databases, orchestrators, production/release behavior.

## Installation and layout

- Layout: `src/slaif_raggedized_helper` (hatchling wheel); console entry
  `raggedized`; Python `>=3.12` (CI proves 3.12 and 3.14).
- Environment is locked reproducibly in `uv.lock` (exact artifacts + hashes):

  ```sh
  uv sync --locked          # runtime + dev (pytest, ruff) lightweight groups
  uv sync --locked --no-dev # runtime only
  ```

- The committed `.python-version` (3.14) is the development interpreter default;
  CI overwrites it with the matrix version.
- Importing the package performs no network I/O, loads no models, allocates no
  CUDA and imports no heavy ML stack. Torch/Transformers/SentenceTransformers
  are **not** dependencies of this slice; they belong to later explicit
  optional groups (asserted by `tests/unit/test_import_hygiene.py`).
- Runtime dependency is `pydantic` (v2) only; dev tools are `pytest` and
  `ruff`. See `THIRD_PARTY_NOTICES`.

## Commands

```sh
raggedized --version
raggedized --help
raggedized doctor --config PATH
```

`doctor` validates the local configuration, inspects referenced model
lock/manifest files, and prints one machine-readable JSON document to stdout.
It performs **zero inference, downloads or network** by default (URLs are
checked syntactically only; the shipped example route uses the
RFC 6762-reserved `gateway.invalid` host, which can never resolve).

Exit codes: `0` ok; `1` validation/prerequisite issues; `2` usage error.

Doctor report fields: `status` (`ok`/`issues`), `config`
(`valid`/`invalid`/`missing`), `readiness` (`ready`/`not_ready`/absent when the
config is not valid), `issues` (list of `{code, message}`), `models`,
`route`, `secrets`, `version`. Configuration validity is deliberately
distinguished from qualification/readiness: a syntactically valid config with
missing manifests or absent credential references is `config: valid` but
`readiness: not_ready` with actionable issues — never success by omission.

Issue codes: `CONFIG_MISSING`, `CONFIG_INVALID`, `CONFIG_UNEXPECTED`,
`ROUTE_MISSING`, `SECRETS_MISSING`, `SECRET_ABSENT`, `PROFILES_MISSING`,
`MODEL_COVERAGE_MISSING`, `MODEL_LOCK_MISSING`, `MODEL_LOCK_INVALID`,
`MODEL_ROLE_MISMATCH`, `MODEL_UNQUALIFIED`.

Secret handling: secret values are never revealed. References report `kind`
and `present` only (env name membership / file existence), even when the
secret is provided via an environment variable (canary-tested). Rejected
configurations and manifests never echo input values in error output.

## Configuration reference

JSON only (standard-library parsing), loaded via
`slaif_raggedized_helper.config.load_config`. Unknown fields are rejected at
every level. Examples: `config/examples/example-config.json`; JSON Schemas:
`config/schema/app-config.schema.json`, `config/schema/model-manifest.schema.json`
(generated from the Pydantic models; regenerate with
`uv run python -c "from slaif_raggedized_helper.config import RaggedizedConfig; ..."`
or the CI-verified test suite).

Top level (`RaggedizedConfig`):

| Field | Meaning / constraint |
|---|---|
| `schema_version` | must be `1` |
| `generator` | `GeneratorConfig` (below) |
| `profiles` | list of `ProfileConfig`; names unique |
| `embedding` | `EmbeddingPolicy` (below) |
| `direct_generation` | must keep `enabled: false` (refused otherwise) |
| `secrets` | map name → `SecretRef` (`kind: env\|file`, `name`); never values |
| `model_locks` | list of `{role: generator\|embedding\|reranker, path}` |

`GeneratorConfig`:

| Field | Meaning / constraint |
|---|---|
| `route` | `RouteConfig` or null (missing route = honest doctor issue) |
| `context_expected_tokens` | positive int (generator context expectation) |
| `output_reserve_tokens` | positive int, strictly `< context_expected_tokens` |
| `deadline_seconds` | finite, `> 0` |
| `max_inflight` | positive int (initial parallel 1) |
| `degradation` | `{enabled, allow: [{name}]}`; enabled requires named steps |
| `fallback` | only if degradation enabled and step is in `allow` (else implicit-degradation error) |

`RouteConfig`: `base_url` (http/https, hostname required, **no userinfo, no
query/fragment** — credentials cannot live in the URL), `model`,
`api` (`v1-responses`), `timeout_seconds` (finite, `> 0`).

`ProfileConfig` purpose/device/dtype matrix (anything else is an error):

| purpose | device | dtype |
|---|---|---|
| `online_query_embedding` | cpu | fp32 |
| `online_rerank` | gpu | fp16 |
| `offline_embed` | gpu | fp16 **or** fp32 (qualified GPU FP32 corpus mode) |
| `offline_context` | gpu | fp16 |

`EmbeddingPolicy`: `exclusive_offline_gpu` must be `true` (shared offline
embedding refused); `store_dtype` must be `fp32` (stored vectors are
normalized FP32).

`SecretRef`: `kind: env` requires a valid environment-variable name
(`[A-Za-z_][A-Za-z0-9_]*`); `kind: file` is a path reference.

Defaults preserved per architecture: online query embedding CPU FP32, GPU FP16
reranker, exclusive-GPU offline embedding, generator context expectation /
output reserve / finite deadlines.

## Contracts (`slaif_raggedized_helper.schema`)

- `GeneratorRequest`: purpose (`annotation|visual|answer`), bounded trusted
  text items (≤64 items, ≤200 000 chars each), optional authorized images
  (`image_id` + `source_revision`, ≤16), `ModelIdentity` (name/adapter/
  revision/`declared_capabilities`), `required_capabilities` (must be a subset
  of declared), `max_output_tokens`, `deadline_seconds`.
- `GeneratorResult`: explicit outcome (`terminal|refusal|failed|incomplete|
  unknown_completion`); terminal requires text; failed/unknown_completion
  require a safe reason (no provider raw body); `UsageMetrics`/`TimingMetrics`
  keep missing counts `null`/unavailable — never invented zero, negative
  counts rejected; optional result fingerprint.
- `EmbeddingDefinition`: checkpoint/tokenizer/pooling/L2/query policy/
  dimension (the *space*), fingerprinted canonically (`slaif-fingerprint-v1`
  digest over sorted JSON — not Python `hash()`). `EmbeddingExecution` binds
  one definition to a device/precision with its own fingerprint; equal
  dimensions alone never imply the same space.
- `RerankRequest`/`RerankResult`: unique pair IDs; exactly one finite score
  per submitted pair ID (`bind_rerank_scores`); scores are relevance
  estimates, not truth/confidence claims.
- Client protocols (`slaif_raggedized_helper.model_clients`): small structural
  `Protocol`s (generator/embedding/reranker) for adapter injection — no
  abstract framework.

## Model locks and qualification

`ModelLock` records the exact immutable revision, artifact hash (explicit
null = unknown), license name/status (`approved`/`unknown`), tokenizer
revision, pooling, Qwen GGUF quantization, projector and runtime metadata.
`QualificationRecord` records named test, explicit-UTC timestamp,
code/model/runtime scope, `mock|live` mode, `pass|fail|not_run|blocked`
status and optional finite metrics (null = unavailable).

Promotion (`ModelManifest.evaluate`): a manifest is `qualified` only with
approved license + pinned artifact hash + a `pass` record whose `model_scope`
matches the lock revision, and the record must be live-mode. Incompatible or
missing evidence fails promotion. **Unqualified example manifests are never
proof of a downloaded, pinned or license-approved model** (shipped examples
are placeholder, explicitly unresolved). Mock evidence is recorded honestly
and never promotes live readiness.

## Tests

```sh
uv run pytest tests/unit -q   # product foundation tests (synthetic fixtures)
python3 -m unittest discover -s tests/oap -v   # OAP scaffold suite
python3 oap/bin/check_state.py --repo-root .   # governance identity
uv run ruff check src tests/unit               # product lint
```

Product tests exercise config refusal boundaries (unknown fields,
non-finite/nonpositive budgets, profile shape, direct-online refusal, implicit
degradation, URL credentials, env-name grammar), contract invariants (outcomes,
null metrics, space fingerprint distinctions, pair binding), lock/qualification
promotion, and doctor CLI semantics (exit codes, machine-readable output,
offline/no-network runs, secret canaries). Mock/live distinction: all tests
are mock/synthetic; no keys, network, GPU, models or downloads are used.

## Unresolved artifacts (honest state)

- No deployed gateway route is known: the example uses a non-resolving
  `.invalid` placeholder host; real base URL/commit/capabilities remain
  unknown (docs/environment-inventory.md section 4).
- No model/tokenizer/artifact has been downloaded or pinned: example locks
  carry explicit unknowns; license status is `unknown` (no legal clearance
  claimed).
- No live trial has been run: qualification records are absent; hardware and
  live gateway evidence remain NOT RUN.
