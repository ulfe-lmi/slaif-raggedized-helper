# Supplied parity and qualification gates

Run `python -m slaif_raggedized_helper.qualification.parity_cli embedding --input INPUT --output OUTPUT --allow-supplied-input` or replace `embedding` with `rerank`. Both are operator-local, explicit opt-in, pure supplied-value analyses. Input is the mapping accepted by `embedding_parity.analyze` or `rerank_parity.analyze_rerank_parity` respectively; unknown fields and promotion to executed evidence are refused. Output contains the analyzer's normalized input fingerprint/binding and SHA-256 and byte count of the exact input file. The digest binds bytes, not authenticity or execution. Output is unverified and real qualification remains NOT_RUN even when supplied criteria match.

Exit 0 indicates export succeeded, 2 a safe pre-analysis refusal, 3 an export or serialization failure after analysis. On exit 3 stdout contains computed evidence when bounded serialization permits; otherwise it explicitly marks evidence unavailable. Input and output each default to 16 MiB, with depth 64, two million nodes, 1 MiB strings and 128-character number tokens; analyzer-specific work limits also apply. Output paths are operator arguments, never selected by JSON. The I/O layer trusts operator-chosen parents and hard links; destination preflight is advisory and export is neither atomic nor durable. No source text, exception or path is echoed in errors. Help and import do not run models, telemetry or network operations.

The generated `docs/benchmarks/qualification-gates.json` gives the exact current runner or missing prerequisites for each of the fourteen architecture gates. All real statuses are NOT_RUN and target authorization is NONE:

- GATEWAY-01 and GATEWAY-03: `raggedized qualification run` is a bounded text trial; authorization and real route evidence remain necessary. Gateway sends no slot/cache-key control.
- GATEWAY-02: 016 audited vision path, qualified gateway vision and authorization.
- DIRECT-01: the same trial command supports an authorized materialized offline direct destination; cold/warm physical state needs isolation evidence.
- V100-MEM-01 and V100-MEM-02: 015 ownership and authorized GPU/model experiments; local `raggedized resource diagnose` is only partial own-process/devhost instrumentation. The first also needs 012 worker.
- RERANK-01: 012 worker, pair/batch controls and real measurements; the rerank command analyzes supplied scores only.
- EMBED-01: 007 pipeline and real serving CPU measurements. EMBED-02: 007 and authorized CPU/GPU experiments; the embedding command analyzes supplied vectors only.
- ONLINE-01: 014 authenticated answer API and 019 held-out evaluation. ONLINE-02: 014 and concurrency implementation.
- OPS-01: 007/010 jobs and 017 recovery. OPS-02: 015 mode operations and ownership journal.
- LICENSE-01: 018 exact license audit; no certifi exception has been granted.

Generator trial admission, transport and shared deadline behavior remain those of the existing qualification runner; these parity commands execute no worker, model, resource or quality experiment. Real model, GPU, corpus, vision, license, 019, ICA and MVP qualification remain open.
