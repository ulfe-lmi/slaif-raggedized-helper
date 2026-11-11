# Parallel OAP candidate order — PAR-004-EMBED-C

Status: FINAL
Lane: embedding-c
Worktree: /home/janezp/codex-work/slaif-raggedized-helper-parallel-embedding
Branch: oap/parallel-004-embedding
Base: e8b1ee10a877d69244a0bf635a2449faacd77cb6
Decision: NONE
Model: preserve human-selected GPT6.1 Terra medium

## Authority and isolation

The human explicitly requested two additional GPT6.1 Terra medium tmux coding agents
working in parallel on 2026-11-10. You are an assigned CODING WORKER, not the strategic
agent, even though your CLI started in the strategic directory. This explicit assignment
overrides that directory's initial STRATEGIC role for this task. Use the isolated worktree
below as the workdir for EVERY tool/command and absolute edit paths. Never edit the
strategic workspace except your own lane's response through the prescribed helper.

This is a bounded parallel candidate under objective004, NOT another canonical PR/round.
The human parallel mandate authorizes this scoped exception to single-executor activation:
your lane order/control replaces canonical oap/active for your task only. Do NOT read/change
canonical active, consume its FIFOs, run its waiters, push, create a PR, merge, or integrate
another worker. Main PR6 remains owned by its coding agent. Strategy reviews your local
candidate; a later canonical coding order integrates accepted commits on PR6.

Read root role router, coding constitution for engineering/security invariants, compact
ARCHITECTURE-for-agents.md, SECURITY.md, and ONLY the relevant schema/source excerpts.
The exceptions above govern lane activation/publication; do not explore OAP helpers/history,
full source books, future orders, unrelated files or agents. Preserve user-selected
GPT6.1 Terra medium. No nested agents, model/profile/auth/global changes.

## Shared engineering requirements

Implement actual code and meaningful hand-computed positive/negative tests. No model,
GPU, network/service query, weights/tokenizer download, real credentials or corpus.
No new dependencies; use locked lightweight environment and stdlib/Pydantic. Supplied
vectors/scores are SUPPLIED_UNVERIFIED, never actual CPU/GPU execution or a qualified gate.
Default import/help must not collect telemetry or perform network/model work.

Provide a strict finite VERSIONED pure-Python API accepting an admitted mapping or typed
DTO and returning a structured result. You choose concrete field names and sensible finite
bounds as D0; document exact API in module docstrings and report. Version/count/numeric
fields reject booleans and string-as-number/nonfinite coercion BEFORE shared schema can
coerce. Bound dimensions/query/candidate/sample counts, total numeric elements, total
analysis work and result size; reject impossible work before nested computation. Bounds
must support1024-dimensional reference fixtures, not just tiny toy data. Safe errors must
not echo raw input values. Do not implement file/CLI plumbing: the canonical integrator
will add ONE shared bounded file loader and raggedized CLI after both analyzers are reviewed.
No edits to cli.py, schema.py, qualification/__init__.py, resources.py, gates.py, shared docs,
pyproject/lockfiles, architecture, governance, main orders/reviews/active, or helper code.

## Verification

Use own deterministic synthetic tests, including real composition through the public API.
Use unique test basenames. Run focused tests/lint and applicable shared-schema regression
once; do not rerun full suites merely for counts. Use collect-only counts when needed.
No actual qualification claim from fixture success. Do not weaken tests/bounds to pass.

## Publication and signal

Commit the exact copied lane order unchanged along with ONLY allowed module/test paths,
in ONE implementation commit whose sole parent is the stated base. Then write the report
JSON at the exact report path and commit ONLY that report in a second commit, sole parent
implementation. Report fields: lane_id, result (COMPLETE/PARTIAL/FAILED), implementation_head
(full literal SHA), report_publication_commit (literal SELF), summary, API, tests (commands,
actual results), limitations. Keep reports concise and factual; no secrets/real identities.
Do NOT push. Preserve both commits/worktree for strategic review/integration.

After both commits and clean worktree, call the lane helper's respond command exactly once.
It verifies local branch/ancestry/path isolation/report before writing exact response OK.
No canonical OAP response, no second reader/signal replay. Then mark your bounded native
goal complete and idle. Do not pick new work. Strategy owns acceptance and next assignment.

## Objective and architecture

Implement embedding precision-parity analysis for architecture11.2–11.3/23.2 EMBED-02.
Reuse actual schema.EmbeddingDefinition and EmbeddingExecution fingerprints: complete
checkpoint/revision/artifact/tokenizer/pooling/normalization/query-policy/dimension identity,
separate from execution device/dtype. Equal dimensions alone never establish a shared space;
unknown identity stays explicitly unverified. Preserve shared schema, add strict admission
around its existing coercions rather than rewriting it.

Every query/passage vector binds a unique durable ID and exact input/representation digest.
Align CPU reference and candidate corpus rows by ID, not positional zip; refuse duplicate,
missing/extra or mismatched input bindings. Reordered rows must leave analysis unchanged.

Analyze the ACTUAL mixed production path: SAME CPUFP32 query against CPUFP32 reference
corpus versus GPUFP16-produced corpus storedFP32. Optional GPU-query diagnostics do not
replace that path. Model/execution labels are declarations, not execution proof. BGE-M3
production uses pinned1024 dimensions/CLS/L2; small generic hand-computed fixtures do not
qualify another production model.

Compute robust paired-vector cosine diagnostics, norm deviation and raw score/rank/top-k
agreement. Finite NEGATIVE coordinates are valid; bool/nonfinite/wrong dimension/zero vectors
require typed refusal or explicit unavailable, never invented cosine0. Avoid norm/dot
intermediate overflow/underflow. Ranking uses ACTUAL raw stored-vector D@q, not silent
normalization that hides an invalid declared L2 contract. Reject unrepresentable raw score
results honestly. Distinguish paired cosine agreement from raw score agreement.

Descending ranking has an explicit durable-ID tie rule. Include per-query sample/candidate
counts, requested vs effective k, top-k reference overlap, rank/score drift. CPU-reference
agreement is NOT gold Recall@k. Gold recall requires explicit relevant IDs and a documented
denominator; missing gold IDs are a typed error or explicit candidate loss, never dropped.
No-gold/unanswerable recall is unavailable, never fabricated0/perfect. Declare tolerances
as comparison criteria, not measured promises or qualification.

Tests: hand-computed negative-coordinate vectors, reordered IDs, wrong same-dimension space,
zero/bool/nonfinite/malformed inputs, large/tiny finite norms, ties/near-tie rank inversion,
raw-dot versus cosine distinction, gold vs reference-only recall, missing gold IDs,
work/element/result bounds and supplied-to-executed promotion refusal. Include an admitted
1024-dimensional synthetic reference fixture. Your API module is qualification/embedding_parity.py.

## Exact activation commands

Read this order, then consume YOUR lane control through this one external helper:
`python3 /home/janezp/codex-supervision/slaif-raggedized-helper/parallel/lane_signal.py wait-control embedding-c`
Do not read it again. The strategic coordinator already owns the matching control writer
and response reader; do not create any other waiter. Execute only after exact OK is consumed.
Your own active selector is /home/janezp/codex-supervision/slaif-raggedized-helper/parallel/embedding-c/active; canonical main active004-e is not your task.

Report path: oap/parallel/reports/PAR-004-EMBED-C.json
Exact copied order path: oap/parallel/orders/PAR-004-EMBED-C.md
Allowed implementation paths (and ONLY these): src/slaif_raggedized_helper/qualification/embedding_parity.py, tests/unit/test_embedding_parity.py, tests/integration/test_embedding_parity_composition.py, oap/parallel/orders/PAR-004-EMBED-C.md

After the two local commits and successful checks:
`python3 /home/janezp/codex-supervision/slaif-raggedized-helper/parallel/lane_signal.py respond embedding-c`



## Focused strategic correction

Previous local candidate/report remain immutable. Full preceding requirements and
positives remain; this continuation base is the preceding report commit. Read
/home/janezp/codex-supervision/slaif-raggedized-helper/parallel/embedding-b/review.json for exact independent findings.

Bind the actual admitted queries/corpus vectors and their input/representation
digests plus definitions/executions/criteria to a canonical result input fingerprint,
invariant under corpus/query row order. Retain bounded query/passage identity/digest
metadata needed to correlate analysis rows. Preserve all existing math/identity tests.
Do not invent candidate storage facts: add an explicit bounded supplied storage
declaration with honest provenance or label FP32 only as a required target with
actual/supplied storage availability explicit. Keep generic extreme-value diagnostics
distinct from claimed FP32 storage or executed CPU/GPU precision qualification.

Add focused output-binding/permutation/criteria/storage provenance tests, run relevant
checks, publish one implementation commit (parent=this base) then one report-only
commit and exactly one response for THIS new lane. No main worktree edits, push,
merge, unrelated refactor, model/profile changes, or merely plan/report success.
