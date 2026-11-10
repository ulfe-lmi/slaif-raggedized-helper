# OAP Coding Report — 003-c

Identifier: 003-c
Result: COMPLETE
Repository: ulfe-lmi/slaif-raggedized-helper
PR number: 5
Branch: oap/003-generator-adapters-and-cache-probes
Base branch: main
Implementation head SHA: 5bfca450ffd7a3a7e0a512b2ef66cb40ff5b715a
Report publication commit: SELF

## Work and scope

Executed oap/orders/003-c-gateway-protocol-validation.md (Status FINAL,
active 003-c, PR mode AMEND_EXISTING_PR) on the existing unique 003
objective PR #5, branch oap/003-generator-adapters-and-cache-probes from
verified base main 93b43177f4dcd0b28ef2c5ed33a049f83217f152. Two
implementation commits were pushed before this report:

- 1f2c11114315afbc0e5321f2108ef00bd7498bca: the protocol-validation
  repair plus the ordered docs/governance refresh and the exact 003-c
  order/active bytes and the pre-published 003-b strategic review
  (oap/reviews/003-b-review.json) committed unchanged.
- 5bfca450ffd7a3a7e0a512b2ef66cb40ff5b715a (implementation head): a
  safe in-scope CI failure repair — the two excessive-nesting
  regressions now probe the running interpreter for the depth that
  actually raises RecursionError instead of hardcoding one (see
  Verification).

Changed files: src/slaif_raggedized_helper/model_clients/gateway.py,
tests/integration/test_gateway_generator.py, docs/generator-contract.md,
STATUS.md, oap/governance/CONTEXT-BUDGET.md, oap/governance/
DISTILLATION-MAP.md, oap/governance/MANIFEST.json, oap/active (exact
003-c bytes), oap/orders/003-c-gateway-protocol-validation.md (new,
exact bytes), oap/reviews/003-b-review.json (new, unchanged pre-
published review). No other files touched; no transport redesign, no
native/probe implementation, no model/provider/profile change, no
architecture/role-law change.

Behavior changes (gateway.py only, plus the deterministic test hook):

- Final output parsing: `message.status` and `reasoning.status` are
  type-guarded (must be a string) before set membership, so a hostile
  `status` of `{}` or `[]` is a structural error, never a raw TypeError
  and never a salvaged success (stream and non-stream paths).
- SSE event JSON: `handle()` catches `ValueError` (JSONDecodeError) and
  `RecursionError` (excessive nesting beyond the interpreter's C
  scanner capacity inside the transport byte bounds) as a latched
  "malformed event payload"; `_parse_non_stream` likewise catches
  `RecursionError` as "provider response is not valid JSON".
- Terminal events (completed/failed/incomplete) must carry a valid
  nonempty response ID, consistent with the observed events (a missing,
  malformed or conflicting ID fails closed; conflict uses the existing
  "conflicting response IDs" latch).
- Envelope coordinates: a supplied `output_index` on
  `output_text.delta`/`output_text.done`/`content_part.*` events must
  equal the item's observed position (wrong index refused even when
  `item_id` names a known item); a supplied `content_index` must be a
  bounded non-negative integer and must name a part already added.
- Delta/done types and lifecycle: a non-string `delta` (array, number,
  bool, null, object) is a latched "malformed delta type" and is never
  silently dropped, so a later authoritative terminal text cannot be
  salvaged into a success; a non-string cumulative `text` is
  "malformed output_text.done"; a duplicate `output_text.done` or a
  delta after the part's text/part done is refused; the existing
  error latch (fail() is sticky; `_finish_stream` checks it first)
  prevents a later valid final payload from erasing an observed
  protocol error.
- Item done boundary: a `message` `output_item.done` must carry a
  terminal status (`completed` or `refusal`); a nonterminal or untyped
  status followed by a completed final message is "nonterminal item
  done status", never success.
- Content parts: `response.content_part.added`/`done` are validated
  (message items only, explicit bounded `content_index`, matching
  `output_index`, `output_text` part with string text; added parts
  carry no text; done parts require the part's text done and exact
  cumulative text; duplicate/unknown/foreign part coordinates fail
  closed). Text is buffered per item AND per content part (part 0
  implicit when `content_index` is absent), so multiple bounded
  `output_text` parts reconcile independently and the final array part
  order is preserved; unknown or contradictory part coordinates are
  never silently merged.
- Deterministic deadline boundary: `GatewayGenerator` accepts an
  optional generator-local monotonic `clock` (default remains the real
  `time.monotonic`); the zero-dispatch test injects a stepping clock so
  the loop-top guard is exact without measuring machine overhead or
  patching the global time module.

## Acceptance evidence

Criterion 1 (safe typed failures for malformed JSON structures/types):
the read-only strategic reproduction
(/tmp/raggedized003-protocol-review.py, 7 real loopback POSTs through
GatewayGenerator) at the implementation head now yields:
valid_pinned_stream terminal "answer" (baseline preserved);
malformed_delta FAILED "malformed delta type" text=null (previously a
salvaged TERMINAL "answer"); missing_terminal_response_id FAILED
"malformed terminal response ID"; wrong_delta_output_index FAILED
"output_index mismatch"; contradictory_item_done_status FAILED
"nonterminal item done status"; malformed_status_object FAILED
"contradictory terminal message item status" (previously a raw
TypeError leaked); valid_multiple_content_parts TERMINAL "firstsecond"
(previously FAILED "delta/cumulative text mismatch"); 7 local POSTs,
paths {/v1/responses}. Project tests:
test_stream_array_delta_refused_not_salvaged,
test_stream_non_string_delta_refused (delta in [[], 7, True, None, {}]),
test_stream_non_string_done_text_refused,
test_stream_malformed_final_status_object_refused (status in [{} , []]),
test_non_stream_malformed_final_status_refused,
test_non_stream_excessive_json_nesting_refused,
test_stream_excessive_json_nesting_refused. Error reasons are fixed
strings; canary tests (test_stream_nonterminal_item_done_status_canary_
not_leaked, test_stream_refusal_canary_reason_is_fixed,
test_stream_failed_terminal_canary_not_leaked) assert provider canaries
never enter results. Refusal/incomplete/unknown-completion
distinctions preserved: test_stream_valid_refusal_terminal (REFUSAL
"refusal: content_filter"), test_stream_incomplete_terminal_preserved
(INCOMPLETE "incomplete: max_output_tokens" with partial text),
test_stream_failed_terminal_canary_not_leaked (FAILED "provider
failure"), plus the pre-existing UNKNOWN_COMPLETION tests.

Criterion 2 (terminal response ID + event-envelope coordinates):
_handle_terminal rejects missing/malformed IDs (tests:
test_stream_missing_terminal_response_id_refused,
test_stream_malformed_terminal_response_id_refused for id in [{} , [],
7]) and conflicting IDs (test_stream_conflicting_terminal_response_id_
refused). Item/part coordinates at the correct boundary:
test_stream_wrong_delta_output_index_refused (index 9 on a known item),
test_stream_delta_other_item_output_index_refused (two-item stream,
index 1 claimed by item 0), test_stream_part_event_wrong_output_index_
refused, test_stream_part_event_unknown_item_refused,
test_stream_unknown_content_part_refused (explicit content_index 5
never added). Final output-array items are still validated WITHOUT
output_index (pre-existing test_final_item_without_output_index_
accepted and test_out_of_order_output_index_refused unchanged and
green).

Criterion 3 (delta/text/done types and lifecycle/status transitions):
array delta + empty done/item data + authoritative terminal text is a
malformed stream, not success (criterion-1 tests; the reproduction
case). Nonterminal item.done status followed by a completed final
message is contradictory (test_stream_nonterminal_item_done_status_
refused for status in [in_progress, incomplete, failed, {}, [], None]).
Duplicate/foreign/terminal/order checks retained: pre-existing
duplicate-ID, out-of-order, duplicate-terminal, foreign-item and
completed-output-mismatch tests all still pass; the sticky error latch
plus _finish_stream's error-first ordering prevents a later valid
final payload from erasing an observed protocol error (demonstrated by
the reproduction cases, where the completed event still carries the
full "answer" text and the outcome is FAILED with text=null).

Criterion 4 (text by item AND content-part identity, final array
order): valid two-part stream with complete
part-added/delta/text-done/part-done events and consistent item/final
data succeeds with exact fixture text "firstsecond"
(test_stream_valid_multiple_content_parts_succeeds; reproduction
valid_multiple_content_parts). One buffer per part, not per item:
per-part cumulative reconciliation is exercised by
test_stream_delta_after_text_done_refused,
test_stream_duplicate_text_done_refused,
test_stream_part_done_before_text_done_refused,
test_stream_part_added_with_text_refused,
test_stream_part_done_text_mismatch_refused,
test_stream_part_event_non_message_item_refused — all fail closed, no
silent merge, no blanket multipart refusal. Multiple-message ordering
retained (test_stream_multiple_messages_in_order_succeeds, exact text
"alpha\nbeta"; pre-existing non-stream multi-message test unchanged).
No arbitrary recursive text extraction was added; text extraction
remains the bounded output_text-part path.

Criterion 5 (deterministic zero-dispatch test + controlled HTTP
regressions): test_already_expired_deadline_refused_before_any_dispatch
now uses a generator-local stepping clock (deadline = 0.0 + 1.0 = 1.0,
loop-top guard observes 1.0 >= 1.0) — zero attempts, zero transport
calls, zero server requests, both stream and non-stream; the measured-
overhead 1µs premise and _DeadlineProbeTransport are removed; the
global time module is never patched. Real HTTP deadline/finite-retry
coverage preserved and green: test_pre_connect_retry_policy_is_finite,
test_budget_exhausted_retry_refused_before_dispatch,
test_full_generator_post_send_close_unknown_no_retry (stream and
normal), test_full_generator_stream_post_send_close_unknown_no_retry,
test_full_generator_header_delay_unknown_no_retry,
test_stream_total_deadline_mid_body_unknown_with_partial_text,
test_stream_valid_slow_inside_budget_succeeds. Controlled loopback HTTP
regressions cover every failing reproduction plus the malformed
type/ID/coordinate/status variants listed above, and the positive
single/multiple part/message streams, valid refusal and incomplete/
failed terminals; they assert actual request paths/counts
(/v1/responses exactly once), outcomes, safe canaries and supported
text exactly.

Documentation (the demonstrated 003-b omissions):
docs/generator-contract.md now states the actual multipart/type
validation behavior, the terminal-ID/coordinate rules, part lifecycle
refusals, and the byte defaults as the decimal literals 2,000,000 /
16,000,000 (DEFAULT_MAX_RESPONSE_BYTES / DEFAULT_MAX_STREAM_BYTES),
not 2/16 MiB (SSE event bound exactly 262,144 bytes); the
native/probe scope is stated as pending for separately finalized
continuations. STATUS.md now separates historical events (bootstrap
2026-11-01 with product implementation absent at that time; 000-a
merged PR #1 08b21db; architecture v2 merged PR #2 976381e; 001-a
merged PR #3 3178650; 002-a merged PR #4 93b4317, the current main)
from the current state (003-c active on PR #5, product implementation
in progress, coding client active rather than idle). Measured
governance refreshed together: CONTEXT-BUDGET.md TESTING.md 2043→2718
bytes, aggregate 34594→35269 (recomputed actual bytes); DISTILLATION-
MAP.md operational row TESTING T01–T05→T01–T06; MANIFEST.json hashes
for the two changed governance files recomputed — check_state.py
verifies the manifest and reports 35269 declared context bytes. Prior
orders and all other manifest entries are byte-identical.

## Verification

All checks below were run locally at the implementation head
5bfca450ffd7a3a7e0a512b2ef66cb40ff5b715a (uv-locked environment,
Python 3.14.4; CI additionally covers 3.12/3.13/3.14):

- uv run pytest tests/integration tests/unit -q → 136 passed (95
  integration loopback, 41 unit), 0 failed.
- uv run ruff check src tests/unit tests/integration → All checks
  passed.
- python3 -m compileall -q oap tests → OK.
- python3 -m unittest discover -s tests/oap → Ran 41 tests, OK.
- python3 oap/bin/check_state.py --repo-root . → state ACTIVE, active
  003-c, order located, manifest hashes verified, declared context
  35269 bytes; activation_matches_current_governance=false is the
  expected authorized-candidate state (this order explicitly authorizes
  the governance refresh; the order's pinned hash is the pre-003-c
  manifest, per check_state's own "candidate governance change may
  differ from activation" note).
- Read-only strategic reproduction
  (uv run python /tmp/raggedized003-protocol-review.py) at the
  implementation head: the 7-case table in Acceptance evidence; no
  case raised a raw exception.
- GitHub CI on PR #5 at the implementation head, run 42760298472:
  OAP tests Python 3.12/3.13/3.14 and Product tests Python 3.12/3.14
  → all 5 checks pass (lint, unit + integration suites, OAP tests,
  governance check, console/doctor offline steps).

Mock/live distinction: every test is synthetic — owned 127.0.0.1
loopback servers with unique synthetic API-key canaries, no external
network, no live services/models/GPU, no model downloads; the
reproduction probe is owned-localhost and read-only. No live route,
route/model/provider/profile change was made or needed.

CI failure found and repaired in-scope: at the first implementation
commit (1f2c11114315afbc0e5321f2108ef00bd7498bca) the Product tests
(Python 3.14) job failed the two fixed-depth (100_000) nesting tests:
the C JSON scanner's nesting capacity depends on the interpreter build
and C stack size (fixed at interpreter startup; not the Python
recursion limit — locally a 100_000-level payload raises
RecursionError on 3.14.4 and 3.12.15, while GitHub's 3.14 build
parses it cleanly). The fix (5bfca45) probes the running interpreter
for the smallest depth that raises RecursionError and sends exactly
that payload over the wire (asserting the safe typed refusal); when
the capacity exceeds the transport byte bound it sends the deepest
proven-parseable nesting and asserts the safe typed result instead
(FAILED "unexpected provider terminal status" non-stream; INCOMPLETE
with safe error stream). Verified locally under default, 4MB
(ulimit -s 4096) and unlimited C-stack configurations (trigger branch
and parse branch both exercised).

This report cannot certify its own future push or checks on the
report-publication head; CI facts recorded above are for the
implementation head only, and the post-publication state is recorded
by the separate receipt/strategic review.

## Documentation impact

docs/generator-contract.md (behavior + byte defaults as above),
STATUS.md (historical/current separation; merge facts), oap/
governance/CONTEXT-BUDGET.md + DISTILLATION-MAP.md + MANIFEST.json
(measured refresh, changed together). No behavioral documentation was
added that the code/tests do not prove; no commands, performance,
license clearance or readiness is claimed beyond what was executed.

## DHA and boundaries

The order declares Decision: NONE; no critical append was performed or
needed; CRITICAL.md untouched. No consequential-candidate evidence
arose beyond what the order itself adjudicates. Preserved: the
working 003-b transport (no redesign), all prior immutable reports,
the pre-published 003-b strategic review (committed unchanged), exact
strategic 003-c order/active bytes (committed unchanged),
model/provider/profile, private state, deadline/cancellation
behavior, original sources. No merge, auto-merge, tag, release or
deploy; PR #5 remains the single 003 objective PR (amended); no next
work selected.

## Limitations and remaining work

- The native direct /completion adapter and qualification probes of
  objective 003 remain pending (separately finalized continuations of
  PR #5); whole 003 stays open and this slice is not acceptance or
  readiness for objective 003.
- Existing missing live-qualification and certifi/license-policy gates
  remain explicit; no live evidence was produced.
- The excessive-nesting refusals are proven at the interpreter
  capacities available locally and in CI (trigger branch on builds
  whose C capacity is within the byte bound, safe-parse branch on
  builds whose capacity exceeds it); the adapter's RecursionError
  guard is active on all of them.
- Strategic review of the 003-b report remains NOT_ACCEPTED/CONTINUE at
  the 003-b candidate; this round's publication is for strategic
  re-review, not acceptance.
