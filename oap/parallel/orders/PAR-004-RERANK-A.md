# Parallel OAP candidate order — PAR-004-RERANK-A

Status: FINAL
Lane: rerank
Worktree: /home/janezp/codex-work/slaif-raggedized-helper-parallel-rerank
Branch: oap/parallel-004-rerank
Base: 57426f5ce76a27601c20512532723e5187895456
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

Implement bounded reranker CPU-reference versus candidate score/rank agreement analysis
for architecture14/23.2 RERANK-01. Reuse actual schema.RerankPair/RerankRequest/RerankResult
and bind_rerank_scores semantics while rejecting raw bool/string/nonfinite score coercion
before those existing models normalize values. Do not alter shared schema.py.

Bind both score sets to the EXACT submitted unique pair IDs and query/passage input digests,
model/checkpoint/tokenizer/pair-budget definitions and declared execution conditions.
Reference/candidate ordering may differ; align by stable pair ID. Missing/extra/duplicate
pair or query/candidate identities are typed errors, not sorted-score magnitude comparisons.
Different declared model/input/pair budget cannot silently pass as precision agreement.
Unknown source/model/artifact facts stay unverified, never inferred from equal scores.

Finite NEGATIVE relevance scores are valid relative scores, not truth/confidence/probability.
Compute signed/absolute paired deltas, stable deterministic descending ranks with a declared
ID tie rule, rank/top-k agreement per query and actual sample counts. Explicit finite
comparison tolerances are declared criteria, not measured GPU speed, VRAM or domain quality.
CPU-reference top-k overlap must not be labeled gold recall. Missing/no-gold is unavailable.
No sampling/model/provider/worker-lifecycle implementation; all values supplied-unverified.

Tests: hand-computed negative/zero/tied scores, permuted pair order, score inversion with
unchanged score magnitudes, different queries, duplicate/missing/extra IDs, model/input/
pair-budget identity conflicts, bool/string/nonfinite scores, finite work/result bounds,
and refusal of supplied-to-live provenance promotion. Include an actual public-API
composition witness. Module is qualification/rerank_parity.py. Final fourteen-gate CLI
composition remains canonical integration work; do not invent worker/hardware evidence.

## Exact activation commands

Read this order, then consume YOUR lane control through this one external helper:
`python3 /home/janezp/codex-supervision/slaif-raggedized-helper/parallel/lane_signal.py wait-control rerank`
Do not read it again. The strategic coordinator already owns the matching control writer
and response reader; do not create any other waiter. Execute only after exact OK is consumed.
Your own active selector is /home/janezp/codex-supervision/slaif-raggedized-helper/parallel/rerank/active; canonical main active004-e is not your task.

Report path: oap/parallel/reports/PAR-004-RERANK-A.json
Exact copied order path: oap/parallel/orders/PAR-004-RERANK-A.md
Allowed implementation paths (and ONLY these): src/slaif_raggedized_helper/qualification/rerank_parity.py, tests/unit/test_rerank_parity.py, tests/integration/test_rerank_parity_composition.py, oap/parallel/orders/PAR-004-RERANK-A.md

After the two local commits and successful checks:
`python3 /home/janezp/codex-supervision/slaif-raggedized-helper/parallel/lane_signal.py respond rerank`

