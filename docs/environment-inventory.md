# Environment and contract inventory

Observation date: 2026-11-10 (UTC), order 001-a, architecture revision 2.0 at main
976381e. Scope: read-only, non-secret local discovery on the development host plus a
read-only, bounded review of the reference gateway checkout (reference only: never
fetched, checked out, mutated or touched for its FIFOs). No SSH/network/port scan, no
inference, no model download, no service change.

## 1. Observed local facts (development host)

| Fact | Observed value | Read-only source |
|---|---|---|
| OS | Ubuntu 26.04.1 LTS (Resolute Raccoon) | `/etc/os-release` |
| Kernel / arch | Linux 7.0.0-38-generic, x86_64 | `uname` |
| Virtualization | `none` (bare metal, per detector) | `systemd-detect-virt` |
| CPU | 2x Intel Xeon E5-2680 v2 @ 2.80 GHz; 10 cores/socket, 2 threads/core, 40 logical CPUs | `lscpu` |
| Memory | 121 GiB RAM, 165 GiB swap | `free` |
| Python | 3.14.4 (system interpreter) | `python3 --version` |
| uv | 0.12.5 | `uv --version` |
| git | 2.53.0 | `git --version` |
| tmux | 3.6 | `tmux -V` |
| gh | 2.46.0 | `gh --version` |
| NVIDIA tool | absent (`nvidia-smi` not found) | `command -v` |
| NVIDIA device | absent (no `/dev/nvidia*`) | `ls /dev/nvidia*` |
| CUDA install | absent (no `/usr/local/cuda*`) | `ls` |
| Model caches | none: no Hugging Face, torch or llama.cpp cache directories; no model directories; only tool package caches (e.g. uv/pip) exist | directory names only |
| Local model processes | none observed | `ps` process names |

Consequence: this host is a CPU-only development host. It can host CPU work
(A01/A13: API/retrieval, CPU BGE-M3 query encoding, CPU search). It cannot host the
private GPU reranker (A20), exclusive offline embedding (A16), any long-context Qwen
serving profile, or the preserved V100/3090 offline long-context profiles (A01). No GPU
memory result, allocation or process state was observed or inferred here.

## 2. Gateway repository contract (reference checkout)

- Repository: `ulfe-lmi/slaif-api-gateway`, remote `https://github.com/ulfe-lmi/slaif-api-gateway.git`;
  packaged version `0.1.0rc2` (`VERSION` file).
- Pinned contract revision: commit `f2df0e82df8766740d9ac169ea56ffd7a3cb1f1e`
  (2026-11-02, "Merge pull request #371 from ulfe-lmi/oap/215-gui-email-parity").
- Checkout state at observation: branch `oap/216-gui-accounting-operations` tracking
  `origin/main`, dirty (modified tracked files and untracked 216-series work). The dirty
  working tree is **not** part of the contract; only the pinned commit is.
- Identity (README): self-hosted, OpenAI-compatible organizational AI access control
  plane; gateway-issued keys with per-key policy, hard quota/accounting; provider
  credentials stay server-side; one organization per deployment; Python 3.12+; Apache-2.0.
- Bounded endpoint families (README + compatibility matrix at pinned commit):
  `GET /v1/models`; `POST /v1/chat/completions` (bounded text and explicitly
  route-enabled multimodal/local-tool subsets; non-streaming and SSE);
  `POST /v1/responses` (bounded text/local-tool/stored-reference subsets,
  Conversations, input-token count, compact, one separately fenced `web_search` path);
  `POST /v1/audio/*`; `POST /v1/embeddings`; `POST /v1/realtime/client_secrets`.
  This is an explicit bounded subset, not full OpenAI parity.
- `POST /v1/responses` contract (docs/responses-compatibility.md at pinned commit):
  implemented routes include create, `/input_tokens`, `/compact`, response item
  lifecycle and the `/v1/conversations` family. Implemented request fields are bounded
  (`model`, text or bounded item-array `input`, `instructions`, `max_output_tokens`,
  `temperature`, `top_p`, bounded `metadata`, `stream` only when the resolved route
  advertises Responses streaming, `store` only when the route advertises stored
  Responses, bounded `previous_response_id`/`conversation` references, `text.format`
  including JSON-object/JSON-schema structured output, local function/custom `tools`,
  `tool_choice`, `service_tier` omitted or `auto`). RC2 explicitly rejects
  `background=true`, streaming `previous_response_id`, MCP/connectors, response
  cancellation, response listing, image generation, computer use and hosted
  shell/patch tools. Per-field normative detail lives in that document and
  docs/openai-compatibility.md; it is not reproduced here.
- Vision/multimodal: supported only as explicitly route-enabled, capability-gated
  subsets of the bounded families above. No complete Responses or vision support is
  claimed by the repository.
- Qwen/llama.cpp mechanism (docs/upstream-llm-adapter.md at pinned commit): operator-
  selected upstream LLM profiles `responses-passthrough-v1`, `llama-cpp-qwen-v1`
  (leading system/developer block for prefix-only llama.cpp Qwen templates) and
  `native-vllm-v1`, applied after gateway validation/admission; Responses create and
  streaming only. Evidence at the pinned commit is synthetic and mocked transport
  verification; no live provider qualification is implied.
- Qwen3.8-27B in the repository (docs/configuration.md at pinned commit): a "Qwen3.8-
  27B text / Codex 0.148 candidate" is described as `mocked-conformant, unregistered,
  live target absent` (candidate metadata: Responses text only, 150,000-token context
  window, client-local compaction at 125,000, 8,192/24,576 default/max output). This is
  a Codex client-protocol qualification candidate, not a deployed route and not the
  MVP online default route.
- Deployment model (README/INSTALL.md/docs/deployment*.md at pinned commit): Docker
  Compose self-hosting; per-deployment keys/routes/pricing in PostgreSQL; a documented
  public CLI example uses base URL `https://api.ulfe.slaif.si/v1`. That is an explicit
  public documentation clue only: unverified, and no live route, endpoint or capability
  is claimed from it.
- Boundary: repository model/route support is not a discovered deployed route. Per-route
  and per-key capabilities (context window, vision, streaming, tools, model identity)
  are deployment configuration, not repository facts.

## 3. Architecture inputs: reported existing capability vs unmeasured targets

Architecture revision 2.0 at base 976381e (A01) is the MVP contract. Its inputs split
into two classes:

- Reported existing capability (human-reported, preserved, not re-measured here): the
  preserved long-context Qwen V100/3090 vision setup, about 190k tokens on V100 and
  about 100k tokens on 3090, used for offline context work.
- Unmeasured target configurations (design targets in the architecture, not
  already-working deployments): the online Qwen3.8-27B Q6 vision allocation with actual
  server 32768 context on the gateway `/v1/responses` path (parallel 1 initially);
  bge-reranker-v2-m3 FP16 co-resident on a V100 32 GB GPU with that online profile;
  and the mixed-precision embedding plan (CPU FP32 BGE-M3 query encoding and CPU search
  paired with GPU FP16 corpus compute, FP32 stored vectors).

This round observed none of these hosts, routes or endpoints. No new measurement or
proof of any of them is performed or claimed (A29 qualification remains future work);
only the long-context vision setup is carried as reported existing capability, and the
rest remain target configurations to be established.

## 4. Unknown deployed facts and exact required inputs

| # | Unknown | Exact input needed to resolve it |
|---|---|---|
| 1 | Online generator route | Exact deployed gateway base URL and gateway commit; exact route/model identity; enabled capabilities (text, vision, streaming, structured output); actual context window |
| 2 | Gateway key provisioning | Secure out-of-band provisioning of a gateway-issued key with `/v1/responses` endpoint policy for MVP scope (no secret in Git, reports or logs) |
| 3 | Reranker host/GPU | Approved host and GPU (model/VRAM; expected V100 32 GB per A01), named ownership, residency of the FP16 bge-reranker-v2-m3 worker |
| 4 | Offline embedding host/GPU | Approved exclusive host/GPU for BGE-M3 FP16 compute, named ownership, artifact provenance |
| 5 | Long-context hosts | Hosts/ownership for the reported ~190k V100 / ~100k 3090 profiles; GGUF/projector/KV/MTP/runtime artifact metadata and provenance for the generator hosts |
| 6 | Permitted test-call scope | Explicit authorization for bounded live qualification calls: model/endpoint, count, token and time budgets, allowed routes (needed by 003/004) |
| 7 | Corpus/evaluation rights | Approved documentation corpus (roots/domains, ACL, versions, EN/SL) and rights for human-authored evaluation questions (needed by 005/009) |

Until inputs 1-2 exist, the online generator path stays NOT RUN/UNKNOWN; until 3-6 exist,
GPU qualification stays NOT RUN/UNKNOWN. No placeholder secrets or invented endpoints are
recorded.

## 5. Scope, uncertainty and prerequisites

- Uncertainty IDs are tracked in [UNCERTAINTIES.md](UNCERTAINTIES.md); this round narrows
  U01 (gateway repository contract pinned to f2df0e82; deployed gateway commit, local-Qwen
  route and accepted payload remain unknown) and U02 (development host has no NVIDIA
  device/tool; target GPU hosts remain unknown).
- Prerequisites before live qualification: items 1-6 above; corpus/evaluation rights
  (item 7) gate quality claims, not software work.
- The current human target and post-MVP exclusions are persisted unchanged in
  [MVP-EXECUTION-PLAN.md](MVP-EXECUTION-PLAN.md); development state is in
  [../STATUS.md](../STATUS.md).
