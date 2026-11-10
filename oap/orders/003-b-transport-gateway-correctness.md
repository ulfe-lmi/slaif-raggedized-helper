# OAP Work Order — 003-b

Status: FINAL
Identifier: 003-b
PR mode: AMEND_EXISTING_PR
Branch: oap/003-generator-adapters-and-cache-probes
Base commit: 93b43177f4dcd0b28ef2c5ed33a049f83217f152
PR number: 5
Expected active: 003-a
Provenance: H current MVP execution; E003 partial checkpoint and independently reproduced HTTP/SSE failures; A13 A14 A22 A36 A37
Architecture SHA256: 4b41905396a3838269fd6cf372614cd23cb2c3b6a37be09f29ed752803c0983a
Governance SHA256: cf3afb7eeb64402e9e718a19cd3e98e7a6b97ace2f89892ecd10b0c855c3613e

## Objective

Repair and prove the transport/gateway slice of the SAME003 objective PR. Focus on executable
positive/negative HTTP and SSE behavior, finite budgets and safe outcomes. The original003
native direct adapter/probe deliverables remain pending for later same-PR continuation; this
round does not waive them, satisfy003 as a whole or permit merge of a partial objective.

## Dependencies and current state

Verified 2026-11-10: unique open PR5, branch oap/003-generator-adapters-and-cache-probes, base main at93b43177f4dcd0b28ef2c5ed33a049f83217f152. Current remote head/report SELF52d99fceda755aee5cd3f3ab01f4bcdc6af3e998, sole implementation parentf34b9906c7757913104a4ccc9899ee59879d00d4; reportSHA256f5ce1b5b1e1601b41a0e4f88b0eb3b0715b0cfec74adf2076dc1d7c83780d162; ResultPARTIAL. All5currentCI succeeded but none earns newadapterHTTP/SSE tests. Exact003-a response consumed and remote report verified before this continuation. Tracked worktree clean atSELF, only strategic003-a review JSON untracked. See that review for every failed/unrun check; objective003 remains unresolved, never merged. Reconcile same unfinished objective; never create another003 PR. The prior
control is consumed and prior report immutable. Current final order003-b is the sole selector
after its new exact notification. Read compact law, exact order and actual current files below.
Do not reload all historical plans/reports/helper source, scan runtime/processes or redesign
the whole native/probe feature. The report helper interface already works.

## Allowed paths and scope

src/slaif_raggedized_helper/model_clients/transport.py and gateway.py; directly necessary
schema.py/config.py/base protocol correction only to support these same contracts. Focused
tests/integration/test_generator_transport.py, test_gateway_generator.py or equivalent small
test modules; tests/unit only affected config/provenance regressions. pyproject.toml/uv.lock
only actually needed lightweight constraints; no new model stack. CI/TESTING/docsCI wiring must
run new integration tests, not only prior tests/unit. Regenerate affected JSON schema exports,
docs/generator-contract.md transport/gateway sections only, README/STATUS actual behavior links.
Affected governance hashes/context measurement only for genuinely changed covered files.
Previous strategic003-a review notes if pre-published; unchanged order/active/final report.

Record the known HTTPX->certifi2026.10.23 MPL-2.0 dependency gate in a concise dependency
notice/gate document or THIRD_PARTY_NOTICES update, using actual installed/locked metadata.
This is unapproved under current whitelist unless a later explicit human exception is supplied;
policy question is pending. Do not call it a Python/NVIDIA platform waiver or license-audit pass.
Do not redesign the transport dependency during this focused defect repair merely to evade
the question; final003/license gates must resolve actual policy before distribution. No legal
interpretation or automatic allowlist expansion. Include the pre-published strategic
oap/reviews/003-a-review.json unchanged as the round review/evidence record.

Do not implement/rewrite the native direct adapter or qualification probe here. Preserve any
partial owned files and accurately list their state for003-c. Do not delete them casually.

## Non-goals

No direct model/template/slot implementation, GPU/model download/inference, live gateway
request, source ingestion, retrieval pipeline, new framework or broad public API refactor.
No OAP helper rewrite, new PR, next objective, merge, tag, deploy or release. Existing model/
provider/profile is preserved. Passing this bounded slice is not hardware/model qualification.

## Acceptance criteria

1. One total absolute deadline spans dispatch/connect/write/headers/body/retry; both normal
   and streaming calls refuse before dispatch if already expired. A body that drips bytes
   or stalls late in the budget cannot overrun it through per-read timeout resetting. The
   known `/tmp/raggedized003-deadline-repro.py` regression passed under the first async rewrite;
   preserve that result and test valid slow calls inside budget. No premature blanket refusal
   or socket-timeout trick that breaks normal generation. Own/cancel/close all I/O on timeout
   or consumer cancellation; no unbounded worker or queue. Existing sync public entrypoints
   can be wrappers over async I/O; actual API usage/limitations must be documented clearly.
2. Only positively pre-dispatch connect failure can retry automatically. A server that has
   accepted/read a POST but delayed its headers has UNKNOWN_COMPLETION/non-retryable outcome,
   for BOTH HTTPX read timeout and total-deadline cancellation, in BOTH normal and streaming
   paths. No raw HTTPX/network exception or body escapes. Tests must record that the local
   server accepted the request and assert no duplicate attempt; also prove known pre-connect
   failure follows the finite allowed retry policy. Retries share the original total budget.
3. SSE parser produces exact event/data from actual LF and CRLF bytes, split multibyte UTF8,
   coalesced frames, multiline data/comments and partial trailing frames. Use LF/CR constants
   or correctly escaped source; prior nested patch escapes produced empty-string delimiters
   and dropped/mangled frames. Test literal real wire bytes independently of serializer code.
   Bound unfinished line, full event metadata/data and aggregate bytes; refuse malformed UTF8.
4. Stream worker backpressure is finite and cancellation-aware. Terminal/error/EOF signals
   cannot be silently dropped when a data queue fills; slow consumers eventually observe the
   real result or explicit failure. Closing a consumer cancels only owned request and stops
   its worker/async client; no orphaned threads/readers. Test queue saturation, early close,
   failed startup/header read, body failure, split/large frames and realistic valid stream.
5. Gateway serializes only pinned bounded Responses fields; native cache/slot/process fields
   never appear. Actual images require declared model/route capability and trusted bounded
   resolver even when required_capabilities omits VISION. Unsupported JSON/schema/stream/cache
   controls refuse before dispatch. No redirects, proxy-env destination switches, response-body
   errors or raw secret values. Declared route/model/config identity is stable and separate
   from response ID/content hash; unavailable deployed build fields remain unknown.
6. Parse valid multiple message/output-text items in order; refuse duplicate/foreign/malformed
   IDs, contradictory terminal/item states, invalid encoding and unexpected/unsupported output.
   Refusal/failed/incomplete or missing terminal EOF never becomes terminal success. Completed
   response with no usable text is not a successful answer. Delta/cumulative/done/final shapes
   reconcile per exact supported dialect; request-ID/answer changes do not change backend
   identity. Known safe error codes use an allowlist/fixed reasons; canaries in provider code,
   message/refusal fields and auth exceptions never appear in public errors or logs.
7. Real controlled HTTP positive/negative tests run from clean locked install in product CI,
   alongside all existing foundation/OAP regressions and product lint. Do not claim compliance
   from keyword tests or mocked method calls. Document precisely what is supported/proven and
   what remains NOT RUN or pending in003-c before whole-objective acceptance.

## Verification and negative evidence

Use existing audit/003-transport-review-findings.md and audit/003-async-timeout-classification.md
in the strategic home as evidence leads; revalidate current code rather than copy stale bugs.
Implement focused regression tests with an owned local HTTP server and unique synthetic keys;
no real product services or corpora. Tests verify exact backend calls/counts, wall deadlines
with sensible scheduling tolerance, safe malformed output and resource cleanup. Run affected
new tests first, then existing product/OAP/lock/lint/governance checks and actual CI. All unrun/
failed/skipped/pending evidence stays visible. No extra broad matrices without a failure reason.

## Documentation

Provide concise actual gateway/transport contract and cancellation/deadline/outcome semantics,
safe configuration/secret/proxy behavior and exact test commands. Do not rewrite full architecture
or invent deployed route support. Keep remaining native/probe003 work explicitly pending.

## Runtime and protected resources

Current MVP mandate permits lightweight packages, owned localhost HTTP fixtures, GitHub/CI and
safe local tests. Live inference, GPU work, unapproved SSH, credentials from other agents and
protected service changes: NONE. Preserve other projects/panes/FIFOs and private state.

## Deferred human adjudication
- Decision: NONE

## Publication and report

Amend the existing unique003 PR/branch. Commit exact strategic order/active unchanged with
changes. Inspect/repair in-scope CI, then publish immutable003-b report-only SELF commit with
literal implementation parent; verify remote state and respond exactly once. Result states
whether this bounded slice is complete; whole003 remains unresolved until later native/probe
scope is proved. Do not merge or self-select another round. Native coding goal should end at
this report/response boundary, with truthful partial/failed/blocker reports permitted.
