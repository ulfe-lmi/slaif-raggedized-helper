# Runtime and protected resources

Repository ulfe-lmi/slaif-raggedized-helper; coding root
`/home/janezp/codex-work/slaif-raggedized-helper`; strategic root
`/home/janezp/codex-supervision/slaif-raggedized-helper`. They are distinct, non-nested roots.
Current tmux bindings live privately in strategic runtime.json; validate before use.
Agent runtime/model configuration is separate from Qwen/BGE models used inside the product.
Preserve already-selected coding client/provider/model/effort. No auth/history copying.

Known only from supplied requirements: working long-context Qwen vision ~190k V100/~100k RTX.
Unknown until A0: actual hosts, GPUs/UUIDs, serving paths/ports, model hashes, llama build,
gateway deployed commit/route/capabilities, keys, CPU/thread capacity and corpus rights.
Unknown until A1: peak co-resident VRAM, latency, FP16 parity, prefix reuse and fallback choice.
Record unknowns in docs/UNCERTAINTIES.md, not CRITICAL unless the admission threshold is met.

Read-only local contract inspection is allowed. Existing gateway checkout is reference only;
never reset/edit its active work or touch its FIFOs/panes. No GPU probe that allocates models,
inference, large downloads, service stops, SSH to unapproved hosts, corpus ingestion, network
exposure or production mutation during bootstrap. Future live orders name authorization,
host/device/profile, call/data/time limits, owner/drain rules and recovery plan. Never kill
unknown GPU owners. Safe local synthetic setup is autonomous within development authority.
