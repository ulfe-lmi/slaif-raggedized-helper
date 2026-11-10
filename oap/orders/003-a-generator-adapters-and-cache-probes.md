# OAP Work Order — 003-a

Status: FINAL
Identifier: 003-a
PR mode: CREATE_NEW_PR
Branch: oap/003-generator-adapters-and-cache-probes
Base commit: 93b43177f4dcd0b28ef2c5ed33a049f83217f152
PR number: NEW
Expected active: 002-a
Provenance: H current MVP execution mandate; A13 A14 A15 A22 A36; GATEWAY-01/02/03 DIRECT-01
Architecture SHA256: 4b41905396a3838269fd6cf372614cd23cb2c3b6a37be09f29ed752803c0983a
Governance SHA256: cf3afb7eeb64402e9e718a19cd3e98e7a6b97ace2f89892ecd10b0c855c3613e

## Objective

Implement real callable gateway Responses and private offline llama adapters behind the
semantic contracts from 002, with bounded transport, careful terminal parsing and useful
explicit qualification probes. Prove actual HTTP behavior with controlled local fake servers,
not tests that merely assert a mock method was called. Do not invoke a deployed model without
the exact final live allowance in Runtime below.

## Dependencies and current state

Verified 2026-11-10: objective002/PR4 merged 2026-11-10T01:16:51Z; main 93b43177f4dcd0b28ef2c5ed33a049f83217f152; final PR CI42734541790 and main CI42734653881 passed all5 jobs, accepted tree preserved. No open PR. Local tracked source clean on002 branch, .venv ignored, only strategic002 resolution is added for unchanged commit in this round. Reconcile current main/CI, 002 resolution, actual foundation APIs,
active/dirty state and approved target inputs. Use foundation contracts; do not invent parallel
config/result models or silently alter previous public commands. Architecture §§6.3,10.4,15.3,
16.4/16.5,17.1–17.4 and23.2 are relevant full excerpts. Gateway contract inventory pins f2df0e82;
inspect its exact relevant field/event contract at that commit only as needed.
The actual foundation purposes are annotation/visual/answer and outcomes terminal/refusal/
failed/incomplete/unknown_completion. ModelIdentity carries declared_capabilities; request.items
are bounded text and images are authorized ImageRef IDs/revisions. Add directly needed trusted
instructions/sampling/format/cache fields compatibly to these same models, with independent
transport capability checks. Resolve image IDs through an explicitly trusted bounded resolver
interface; no arbitrary caller URL/file load. If vision transport is not yet materialized,
refuse it explicitly rather than pretending an ID was sent as image evidence; 016 qualifies it.
The existing DirectGenerationConfig is disabled-only because it was a foundation scope guard;
extend it narrowly for explicit offline mode while retaining unconditional direct-online refusal.

## Allowed paths and scope

src/slaif_raggedized_helper/model_clients/ gateway/direct/transport/probe code; directly required
config/contracts/CLI additions compatible with 002; scripts/qualification/ or equivalent small
callable probe module; tests/unit/ and tests/integration/ synthetic transport tests;
docs/generator-contract.md and safe qualification examples, README/TESTING/STATUS/UNCERTAINTIES.
pyproject/uv.lock only used dependencies/marker changes (HTTPX); focused product CI test wiring
if needed. Prior strategic resolution002 committed unchanged; transcript order/active/report.
Governed doc/source hashes only when actually changed. No architecture/source-plan rewrite.
Regenerate affected config/schema JSON exports when their model definitions change. Keep
lightweight default import and doctor behavior. Do not re-read the OAP helper library, old
report history or inert draft queue absent a concrete failing orchestration boundary.

## Non-goals

No model downloads, source ingestion or full retrieval service, generic OpenAI proxy, gateway
feature additions, native tool execution, public direct generator, autonomous agent loop,
unsolicited query rewriting, arbitrary recursive response parsing or raw model-output logs.
No helper agents/model switch, production services, deploy/tag/release or coding merge.

## Acceptance criteria

1. Gateway adapter uses configured `/v1/responses` route/model and secret reference. It
   serializes bounded trusted instructions/reference input, explicit max output and store=false
   when qualified. Optional schema/vision/stream/caching fields require explicit capabilities;
   unsupported controls refuse locally before dispatch. Native cache_prompt/id_slot never leak
   to gateway wire. Validate base URL/no embedded userinfo/query credentials, no redirects or
   implicit destination switches; safe status/error handling does not echo response bodies.
2. Parse every supported output text item in order. Refusal, incomplete/failed responses,
   duplicate/malformed event/order/terminal IDs or EOF without terminal success never appear
   COMPLETE. Qualified SSE parser handles split/coalesced frames, UTF-8, bounds, terminal
   failure, timeout and cancellation with response/connection cleanup. Never infer full
   Responses/vision compatibility from fixture success. Do not recursively accept text from
   arbitrary untrusted fields or strip reported failure to salvage an apparent answer.
3. Direct adapter is explicit context_annotation/visual-extraction offline/diagnostic policy,
   private trusted destination only, never answer fallback. Native /completion request uses
   qualified formatted prompt/chat template and tested cache/slot capabilities. Private IP
   alone is not access-control proof; its enablement requires declared trusted/private policy.
   No public caller chooses model/slot process endpoints. Reject direct online purpose before
   network work, including on gateway auth/quota/timeout failures.
4. End-to-end finite deadlines and bounded output/event sizes apply. No retries for auth/schema/
   permission refusals. Distinguish pre-dispatch retryable failures from ambiguous completion
   after dispatch; at most configured retries and explicit attempt evidence. Default avoids
   automatic replay of costly unknown-completion generations. Cancellation closes owned HTTP
   work, does not launch orphan retries, and cannot cancel another request. Usage/prefill
   fields are present only if actually reported/validated, otherwise null/unavailable.
5. Qualification command explicitly opts into probes, accepts a finite request/time/token
   budget and model/runtime identity, and emits safe structured GATEWAY/DIRECT evidence.
   Repeated-parent probe compares cold A/warm B and records actual evaluated prefill tokens,
   cache/slot template identity and output correctness limitations. Missing metric cannot
   be replaced by submitted token count or wall-time proof of caching. No probe occurs on
   import, normal doctor/help, readiness polling or tests by default.
6. Controlled local HTTP integration tests prove exact outgoing envelopes, multiple output
   items, malformed/partial/refused/error/SSE terminal handling, secret canary non-disclosure,
   unsupported direct purpose/capability refusal, no redirects, bounded retries and cleanup.
   Existing public config/contracts remain compatible or deliberate changes are documented
   and all affected tests/consumers updated. Product/OAP CI passes; real model trials remain
   unrun when target configuration is absent.

## Verification and negative evidence

Run focused HTTP integration/unit tests and actual CLI probe against a synthetic owned loopback
server; distinguish it from the real gateway. Test split SSE frames, oversized responses, failed
terminal events, ambiguous disconnect, redirect destinations, malformed usage and canary errors.
Run existing product regressions, OAP tests and governance check as needed for actual touched
boundaries; rely on CI matrix. Include exact relevant gateway contract commit/events as evidence.
Do not add blanket broad suites or claim model quality/caching from a stub returning fixed text.

## Documentation

Document exact supported Responses/native fields/events, safe configuration and explicit
capability setup; bounded examples, missing live prerequisites and probe output semantics.
Never publish real keys/private URLs or unqualified speed/vision/structured-output claims.

## Runtime and protected resources

Live deployed gateway/model/GPU authorization for this objective: NONE. No target inputs have been supplied; all real trials remain NOT RUN. Accept callable adapters/probe tooling and synthetic HTTP evidence only; this is not hardware or model qualification. Ordinary lightweight
dependency setup, synthetic localhost test servers and GitHub publication are authorized under
MVP mandate. No scans/unapproved SSH or protected gateway/Qwen changes. No inference simply
because a key is present. Preserve original source and human client model/profile/settings.

## Deferred human adjudication
- Decision: NONE

## Publication and report

Create one new objective PR via gh from verified base. Commit unchanged strategic order/active
and previous resolution, implement/test/document, inspect/repair safe in-scope CI. Final report
states full literal implementation SHA and SELF, commit changes only report with that parent.
Verify remote publication, send exact response OK once, then one external idle waiter. Coding
never merges or chooses the next objective. Strategy independently reviews scope/security/
contract/current-head CI and either merges or orders same-PR correction.
