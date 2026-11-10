# OAP Coding Report — 003-d

Identifier: 003-d
Result: COMPLETE
Repository: ulfe-lmi/slaif-raggedized-helper
PR number: 5
Branch: oap/003-generator-adapters-and-cache-probes
Base branch: main
Implementation head SHA: 8e96b0cd50d186ef11e159906d376117488a90ac
Report publication commit: SELF

## Work and scope

Executed oap/orders/003-d-structural-validation-closure.md (Status FINAL,
active 003-d, PR mode AMEND_EXISTING_PR) on the existing unique 003
objective PR #5, branch oap/003-generator-adapters-and-cache-probes from
verified base main 93b43177f4dcd0b28ef2c5ed33a049f83217f152 (PR 5 OPEN,
remote head at round start ae05438c037da94bb344046ed8610c5d65514930, the
published 003-c report). Two implementation commits were pushed before
this report:

- d26eee66d7959a833e57769f3466f6a61bd8fc1f: the structural-validation
  closure (criteria 1-4) plus the ordered docs refresh and the exact
  003-d order/active bytes and the pre-published 003-c strategic review
  (oap/reviews/003-c-review.json) committed unchanged.
- 8e96b0cd50d186ef11e159906d376117488a90ac (implementation head): the
  in-scope repair of the strategic incremental-review observation on
  d26eee6 (a raw TypeError for an added item.type of {} or [] at the
  new supported-type membership check), its actual-HTTP regression and
  the documented explicit-part lifecycle contract (see below).

Changed files: src/slaif_raggedized_helper/model_clients/gateway.py,
tests/integration/test_gateway_generator.py, docs/generator-contract.md,
STATUS.md, oap/active (exact 003-d bytes), oap/orders/
003-d-structural-validation-closure.md (new, exact bytes),
oap/reviews/003-c-review.json (new, unchanged pre-published review).
No other files touched; no transport/config/architecture/source-plan
change, no dependency addition, no native/probe work, no helper change,
no model/provider/profile change, no role-law change.

Behavior changes (gateway.py only):

- One shared envelope-coordinate decoder across all recognized events
  where key absence and present-null are distinct: an absent optional
  coordinate keeps the supported implicit forms (the item's observed
  position / content part 0); a present null or any non-integer
  output_index/content_index is malformed and fails before state access
  ("malformed event index" / "malformed content part index");
  content_index is malformed whenever present at the output_item.done
  boundary; a supplied null final output_index in the non-stream path
  is "malformed output item index" (distinct from absence).
- Explicit content-part coordinates are bounded and sequential
  (0,1,2,... in content_part.added order; a gap, rename or out-of-order
  coordinate is refused as "out-of-order content part") and bound to
  their actual ordered final part positions at the item done boundary
  (part count and per-part text; "content part coordinate missing from
  final content" / "content part text mismatch").
- Item type/identity is frozen from output_item.added through
  output_item.done and the final output array: only message/reasoning
  items enter the lifecycle (added function_call or other/missing type
  is refused, guarded before set membership so an unhashable type is a
  structural error, never a raw exception); a reasoning item cannot
  become a message with the same ID at the done ("item type changed at
  done") or final ("item type changed in final output") boundary; text
  events belong to supported message parts only ("text event for
  non-message item"); no internal reasoning becomes answer text.
- Item completion is latched: duplicate output_item.done ("duplicate
  output_item.done") and delta/text-done/content-part events after the
  done ("text event after item done" / "content part event after item
  done") are refused.
- Terminal done status is validated for every supported type: message
  completed/refusal (existing), reasoning completed ("contradictory
  terminal reasoning item status" for a nonterminal reasoning done,
  even when the final output later shows it completed).
- The message-content part rules are one shared strict validator used by
  both the final output array and the item done boundary (the done
  boundary is no longer lenient about malformed part shapes).

## Acceptance evidence

1. Field absence vs present null in the shared coordinate decoder:
   the rewritten _coordinates() (single shared path for delta,
   output_text.done, content_part.added/done and output_item.done)
   checks "key in payload" before value validation, before any state
   read/mutation. Actual-HTTP regressions: null output_index/content_
   index on delta and text.done, null content_index on content_part.
   added, null output_index on output_item.done, and a present
   content_index on output_item.done all fail safe with the exact fixed
   errors; the positive boundary test (both coordinates absent from
   delta/text.done) retains the implicit forms and succeeds with exact
   text; the non-stream null final output_index regression fails with
   "malformed output item index" while absence stays the pinned form.
   Existing wrong/negative/bool/string/foreign-coordinate refusals are
   unchanged and still pass (full suite green).
2. Part coordinates bound to final positions: sequential bounded
   numbering at content_part.added plus part-to-final-position binding
   at item done. Actual-HTTP regressions: the strategic gap variant
   (second part renamed 1 to 7 throughout, only two final parts) fails
   "out-of-order content part" with no salvaged text; an out-of-order
   part-1-before-part-0 addition fails the same way; a disappeared
   observed part (full lifecycle observed, final content carries one
   concatenated part whose joined text matches the stream) fails
   "content part coordinate missing from final content" — the
   concatenated match no longer suffices. The valid multipart stream
   still succeeds with exact "firstsecond".
3. Type/identity freeze and done latch: added type validated against
   the supported set (message/reasoning; function_call refused as an
   unsupported action at the stream boundary; non-string/unhashable
   types guarded before set membership); done type must equal the
   observed type; the final array must carry the same type for every
   observed ID; text events on non-message items refused; duplicate
   item.done and post-done events refused; per-type terminal done
   status (reasoning done in_progress refused even with a completed
   reasoning in the final output). Actual-HTTP regressions cover every
   one, including the parameterized added-type regression over {},
   [], 7, True, None and the final-only type-change variant (stream
   reasoning, final message with the same ID salvaging text that never
   streamed) which fails "item type changed in final output" with no
   answer text. Existing function_call non-stream refusals unchanged.
4. Preserved positives and oracles: the full pre-existing suite passed
   unmodified — 99 gateway cases of the 003-c era, 33 transport
   cases, 80 unit (132 integration + 80 unit at the pre-round head) —
   and the original read-only seven-case oracle
   /tmp/raggedized003-protocol-review.py (7 owned-loopback POSTs)
   still passes exactly: five malformed variants FAILED with their
   original fixed errors, valid single/multipart TERMINAL with exact
   answer/firstsecond text. Deadlines/privacy/finite no-replay
   behavior: transport.py untouched; all deadline/retry/canary tests
   green.
5. New actual-HTTP project regressions: 24 new cases in
   tests/integration/test_gateway_generator.py (19 structural + 5
   parameterized added-type) against owned 127.0.0.1 loopback with
   synthetic canaries only, asserting exact outcomes, exact fixed
   error vocabulary, result.text is None (no salvaged answer) for
   every malformed variant, attempts == 1, exact path
   /v1/responses and one recorded request, and complete positive text
   for the valid counterexamples (implicit coordinates; completed
   reasoning + message stream with message text only). Gateway suite
   is now 123 cases; product collection is 156 integration (123
   gateway + 33 transport) + 80 unit = 236, plus the separate 41-case
   OAP unittest suite. All product/transport/OAP/lint/governance
   checks and all five CI jobs preserved (see Verification).

Strategic reproductions (read-only, unmodified):
- /tmp/raggedized003-protocol-review.py: 7 actual owned-loopback POSTs
  — all original cases correct (see criterion 4).
- /tmp/raggedized003-structural-variants-review.py: 13 actual
  owned-loopback POSTs exercising all six mutations; every malformed
  variant now yields safe FAILED with a fixed error and no raw
  exception or salvaged answer; both valid cases TERMINAL with exact
  text.
- /tmp/raggedized003-item-lifecycle-review.py (incremental review, 16
  POSTs): the two unhashable added-type cases now fail safe
  ("unsupported output item type", no raw TypeError); the
  unfinished-explicit-part observation returns TERMINAL with exact
  "firstsecond", which the incremental review directed be treated as
  the declared contract rather than an invented defect — the
  generator contract now documents it: each part's own events are
  validated when present, and the output_item.done boundary closes the
  item, so an explicitly declared part without its own
  text.done/part.done before the parent done remains valid when the
  part-to-final-position binding holds at the item boundary.

## Verification

Exact commands at the implementation head (all local, synthetic,
offline; no live model, download, credentials or corpus):

- uv sync --locked — clean locked environment.
- uv run python /tmp/raggedized003-protocol-review.py — 7 POSTs, all
  original cases correct (5 FAILED with original fixed errors; 2
  TERMINAL with exact text).
- uv run python /tmp/raggedized003-structural-variants-review.py — 13
  POSTs, six malformed variants safe FAILED (malformed event index /
  malformed content part index / out-of-order content part / text
  event for non-message item / duplicate output_item.done /
  contradictory terminal reasoning item status), 7 original cases
  correct.
- uv run python /tmp/raggedized003-item-lifecycle-review.py — 16
  POSTs as documented under criterion 3.
- uv run pytest tests/integration -q — 156 passed, exit 0 (123
  gateway + 33 transport).
- uv run pytest tests/unit -q — 80 passed, exit 0.
- python3 -m unittest discover -s tests/oap -v — Ran 41 tests, OK.
- python3 oap/bin/check_state.py --repo-root . — All checks passed
  (governance hashes unchanged: no governance file was modified).
- uv run ruff check src tests/unit tests/integration — clean.

CI (GitHub Actions, .github/workflows/oap.yml, clean locked checkout):
- Implementation head 8e96b0cd50d186ef11e159906d376117488a90ac: run
  42764635506, all 5 jobs SUCCESS (Product tests Python 3.12 and
  3.14; OAP tests Python 3.12, 3.13, 3.14), completed
  2026-11-10T05:52:10Z.
- Prior implementation commit d26eee66d7959a833e57769f3466f6a61bd8fc1f:
  run 42763756609, all 5 jobs SUCCESS (superseded by the fix commit,
  retained in branch history).

Test-count correction per the 003-c strategic review: the 003-c
report's 136/95/41 figures are not authoritative. Actual collection at
the implementation head: 156 integration (123 gateway + 33 transport)
plus 80 unit = 236 product tests; the OAP 41 is a separate unittest
suite. The immutable 003-c report was not edited.

This report cannot certify its own future push or checks on the
report-publication head; CI facts recorded above are for the
implementation head only, and the post-publication state is recorded
by the separate receipt/strategic review.

## Documentation impact

docs/generator-contract.md: documents the presence-vs-null coordinate
semantics, bounded sequential content-part numbering and
part-to-final-position binding, the item-done-closes-open-parts part
lifecycle contract, the added-type guard, the item type/identity
freeze, the done latch, the per-type terminal done status and the
003-d coverage in the proven list; removes the surviving
contradictory "2 MiB default" claim — response 2,000,000 and stream
16,000,000 bytes are decimal (DEFAULT_MAX_RESPONSE_BYTES /
DEFAULT_MAX_STREAM_BYTES), the SSE event bound is exactly 262,144
bytes (256 KiB). STATUS.md: 003-d recorded as the current round,
003-c entry corrected with its strategic outcome, whole-003 native /
probe / live qualification explicitly still pending. The explicit
certifi license gate and the actual context table/distillation map /
manifest synchronization are preserved; no governance file changed, so
all recorded hashes remain accurate. No command, performance, license
clearance or readiness is claimed beyond what was executed.

## DHA and boundaries

The order declares Decision: NONE; no critical append was performed or
needed; CRITICAL.md untouched. No consequential-candidate evidence
arose beyond what the order and the incremental review adjudicate (the
unfinished-explicit-part semantics were resolved by documenting the
declared contract as the incremental review directed). Preserved: the
working 003-b transport (untouched), all prior immutable reports, the
pre-published 003-c strategic review (committed unchanged), exact
strategic 003-d order/active bytes (committed unchanged),
model/provider/profile, private state, deadline/cancellation behavior,
original sources, and both strategic oracles (unmodified). No merge,
auto-merge, tag, release or deploy; PR #5 remains the single 003
objective PR (amended); no next work selected; no numeric advance.

## Limitations and remaining work

- The native direct /completion adapter and qualification probes of
  objective 003 remain pending (separately finalized continuations of
  PR #5); whole 003 stays open and this round is not acceptance or
  readiness for objective 003.
- No live model/service/GPU traffic was performed (order live
  authorization: NONE); all evidence is synthetic owned-loopback HTTP
  plus pinned-dialect fixtures and GitHub CI from a clean checkout.
- The existing certifi (MPL-2.0) license-policy gate remains explicit
  and unresolved; no license evidence was produced.
- The unfinished-explicit-part stream is TERMINAL by the documented
  declared contract (item done closes open parts; binding holds at the
  item boundary). If strategy later decides the stricter full
  per-part lifecycle is required, that is a future-suffix correction,
  not an unmet 003-d invariant.
- Strategic review of this round's candidate is separate; a reported
  COMPLETE describes execution, not acceptance.
