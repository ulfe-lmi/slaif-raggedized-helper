# OAP Coding Report — 003-g

Identifier: 003-g
Result: COMPLETE
Repository: ulfe-lmi/slaif-raggedized-helper
PR number: 5
Branch: oap/003-generator-adapters-and-cache-probes
Base branch: main
Implementation head SHA: 29fb8b9686fc0be9f920e7c05fbe72dd86e5f2d3
Report publication commit: SELF

## Work and scope

Executed oap/orders/003-g-native-boundary-closure.md (Status FINAL, active
003-g, PR mode AMEND_EXISTING_PR) on the existing unique 003 objective
PR #5, branch oap/003-generator-adapters-and-cache-probes from verified
base main 93b43177f4dcd0b28ef2c5ed33a049f83217f152. At round start the
remote head 5960ea188b3493ff4964ba584ca13ee3a1f49142 was the published
003-f report SELF (sole parent implementation
db7443fd64b3207a208348ea178c1600e6ff90f4; PR #5 OPEN/MERGEABLE), and the
worktree carried exactly the strategic round-start bytes: modified
oap/active (003-f -> 003-g), new oap/orders/003-g-native-boundary-
closure.md and new oap/reviews/003-f-review.json. Exactly one
implementation commit was pushed before this report:

- 29fb8b9686fc0be9f920e7c05fbe72dd86e5f2d3 (implementation head): the
  two demonstrated native boundary corrections, their mapping and
  actual-HTTP regressions plus the qualified/ordinary positive
  controls, the focused generator docs and the refreshed governance
  measurements, plus the exact strategic 003-g activation bytes and the
  unchanged pre-published 003-f review (oap/reviews/003-f-review.json
  committed byte-for-byte as found in the worktree).

Safe finite phase-total arithmetic (criterion 1), in
src/slaif_raggedized_helper/model_clients/direct.py (_parse_native_
timings and module doc): the derived model-work total is now computed
IN SECONDS from the two individually validated phase conversions
(prompt_ms/1000 + predicted_ms/1000) with a finiteness check, instead
of summing raw milliseconds before division. Safe arithmetic follows
safe input conversion: each phase is first validated finite nonnegative
milliseconds, then summed in seconds. Both reported phases of 1e308 ms
(individually finite, each converting to 1e305 s) now yield the finite
derived total 2e305 s with the individually valid phase values
retained; a derived total that were unrepresentable would be explicitly
withheld (null) rather than reported. No OverflowError/ValidationError
or nonfinite total escapes generate(); there is no arbitrary
physical-time cutoff and no whole-function exception blanket.
ttft_seconds stays never-set, the reported-0ms known-zero semantics,
missing/invalid-value behavior and the narrow input-conversion
boundary are unchanged.

Explicit required-capability admission (criterion 2), in the same file
(DirectNativeGenerator._preflight and module doc): the default-deny
JSON/schema admission now honors BOTH the actual input shape
(response_format json_object/json_schema) AND the explicit minimum
requirement (Capability.JSON_MODE in required_capabilities)
independently. A constructor-validated request may require JSON_MODE
while sending no format field at all; that unqualified requirement is
refused locally BEFORE /apply-template or /completion (zero dispatch)
with the same fixed safe reason, because a model capability declaration
alone cannot prove serving-build support. A qualified JSON_MODE
requirement alone does not invent an output format: with no format
selected the pinned minimal envelope is sent unchanged. The ordinary
TEXT/no-format path, and the existing vision/stream/cache/slot/purpose/
operator-budget gates, are unchanged.

## Acceptance evidence

1. Safe finite phase total: unit test_finite_phase_sum_overflow_is_a_
   safe_finite_total (mapping level and through the full response
   parse: prompt_ms=predicted_ms=1e308 -> prefill_seconds 1e305,
   decode_seconds 1e305, total_seconds 2e305 finite, ttft_seconds
   None, TERMINAL outcome, no exception) and the actual-HTTP twin
   test_finite_phase_sum_overflow_is_safe_over_http (owned loopback,
   same finite values, usage intact, TTFT unavailable). No raw
   OverflowError/ValidationError or nonfinite result escapes
   generate(); no physical cutoff or whole-function blanket was
   introduced. Preserved behaviors re-proven by the still-green
   regressions: reported 0ms known zero (test_reported_zero_
   millisecond_prefill_is_a_known_zero), 10**400 unrepresentable phase
   stays unavailable (test_overflow_reported_time_is_safe_over_http),
   missing fields stay null, bool/NaN/Inf/negative rejected, both-
   phases-zero positive control (test_reported_zero_millisecond_
   values_are_known_zeros; independent vector known_zero_both_model_
   phases -> 0.0/0.0/0.0).
2. Explicit required JSON_MODE honored: test_unsupported_controls_
   refused_before_any_dispatch gained the json-capability-untested
   case (constructor-validated required-capability-only request,
   untested build: FAILED, fixed safe reason "native JSON control
   refused: json_schema grammar support is not tested on this build
   (default deny)", zero recorded requests); test_required_json_mode_
   capability_refused_before_any_dispatch asserts the same over the
   loopback fixture with exactly zero dispatch and response_format
   None/json_schema None on a valid request; unit
   test_required_json_mode_capability_is_default_deny_in_preflight
   pins the local refusal and test_required_json_mode_capability_
   qualified_passes_preflight_without_format pins the qualified pass.
   Qualified positive control (actual HTTP):
   test_required_json_mode_capability_qualified_without_invented_
   format dispatches exactly once per path on the tested build and
   sends the pinned minimal envelope (no json_schema key invented).
   Ordinary TEXT/no-format positive control:
   test_ordinary_text_without_format_preserved_on_untested_build
   (and the pre-existing envelope/terminal regressions) stays
   TERMINAL on an untested build. All prior gates intact (33
   transport, 125 gateway and all 003-e/f native regressions green).
3. Regressions and preserved vectors: the five original native
   vectors (baseline 100/10/90/12 with 30/60ms; zero prefill 0/60ms;
   10**400 unrepresentable time; unqualified json_object zero-
   dispatch; contradictory 90+90 withholding) and the both-phases-
   zero positive control are all retained and green; the new mapping
   and actual-HTTP regressions above assert typed safe outcomes,
   available finite measurements and exact zero refused dispatch.
4. Full local suites and CI: 241 integration (125 gateway + 33
   transport + 83 native) + 135 unit (48 config + 44 native mapping +
   15 cli-doctor + 14 contracts + 11 model-lock + 3 import-hygiene) =
   376 product tests, all passed; separate 41-test OAP unittest suite
   OK; ruff clean; check_state ACTIVE with all manifest hashes
   verifying (see Verification). Implementation-head CI run
   42785261938: all 5 jobs SUCCESS (Product tests Python 3.12 and
   3.14; OAP tests Python 3.12, 3.13, 3.14). No weaker oracle and no
   historical report was mutated.

## Verification

Exact commands at the implementation head (all local, synthetic,
offline; no live model, download, credentials, GPU or corpus):

- uv sync --locked — clean locked environment, exit 0.
- uv run pytest tests/unit — 135 passed, exit 0.
- uv run pytest tests/integration — 241 passed, exit 0 (125 gateway +
  33 transport + 83 native).
- python3 -m unittest discover -s tests/oap — Ran 41 tests, OK.
- python3 oap/bin/check_state.py --repo-root . — state ACTIVE, active
  003-g, exit 0; activation_matches_current_governance=false is the
  expected post-refresh state for the in-scope manifest pin update
  (the immutable order bytes were not rewritten).
- uv run ruff check src tests/unit tests/integration — All checks
  passed.
- Independent eight-vector owned-HTTP observation
  (/tmp/raggedized003-native-boundaries-review.py, original cases
  preserved, run against the final implementation): 8 cases, 12
  actual owned-loopback POSTs (the two unqualified JSON cases —
  unqualified json_object and required-capability-only — dispatch
  exactly zero). Conforming observations: baseline 100/10/90/12 with
  0.03/0.06/0.09 s and the literal prompt preserved byte-for-byte;
  zero reported prefill kept 0.0 with decode 0.06 and total 0.06;
  10**400 prompt_ms unavailable with decode 0.06 preserved;
  contradictory 90+90 breakdown withheld with the task total kept;
  finite_phase_sum_overflow now TERMINAL with prefill 1e305 / decode
  1e305 / total 2e305 s (finite, TTFT null) instead of the previous
  raw ValidationError; both-phases-zero kept 0.0/0.0/0.0; required
  JSON capability without format refused with zero dispatch instead of
  the previous incorrect 2-POST terminal.

CI (GitHub Actions, .github/workflows/oap.yml, clean locked checkout):
- Implementation head 29fb8b9686fc0be9f920e7c05fbe72dd86e5f2d3: run
  42785261938, all 5 jobs SUCCESS (Product tests Python 3.12 and 3.14;
  OAP tests Python 3.12, 3.13, 3.14), conclusion success, observed
  2026-11-10.
- Round-start head remains green in history:
  5960ea188b3493ff4964ba584ca13ee3a1f49142 run 42782276864, all 5
  SUCCESS (the 003-f report head).

Test-count record per the order: the baseline before G is 368 product
tests (236 integration: 125 gateway + 33 transport + 78 native; 132
unit) plus the separate 41 OAP. Actual collection at the
implementation head: 241 integration (125 gateway + 33 transport + 83
native) + 135 unit (48 config + 44 native mapping + 15 cli-doctor +
14 contracts + 11 model-lock + 3 import-hygiene) = 376 product tests,
plus the separate 41 OAP unittest suite (8 new tests: 4 new
integration tests + 1 new parameterized case + 3 new unit tests).

Mock/live distinction: every network fact above is owned 127.0.0.1
loopback fixtures with synthetic qualifications and canaries, plus
pinned-dialect fixtures and GitHub CI from a clean checkout. No live
model/route request, no real upstream key, no gateway access, no GPU
or service control was performed (order live authorization: NONE).

This report cannot certify its own future push or checks on the
report-publication head; the CI facts recorded above are for the
implementation head only, and the post-publication state is recorded
by the separate receipt/strategic review.

## Documentation impact

docs/generator-contract.md: the native admission sections now state
that the default-deny JSON/schema gate honors BOTH the actual input
shape and the explicit minimum requirement (JSON_MODE in
required_capabilities, which a valid request may carry with no format
field), that a model declaration alone cannot prove serving-build
support, and that a qualified requirement alone does not invent an
output format; the metric-mapping section now states the safe
arithmetic order (individually validated finite milliseconds, derived
total summed in seconds with a finite check, 1e308 ms phases -> finite
1e305 s phases and 2e305 s total, unrepresentable derived total
withheld, no physical cutoff) and a new "Proven for the 003-g native
boundary closure" paragraph records the eight-vector evidence.
TESTING.md T06 lists the 003-g native semantics. Governance:
oap/governance/CONTEXT-BUDGET.md table refreshed to the actual final
bytes (TESTING.md 3626; declared routine read set 36177 UTF-8 bytes,
ceiling 50000) and oap/governance/MANIFEST.json pins for TESTING.md
and CONTEXT-BUDGET.md updated together (all other pins unchanged;
check_state verifies every manifest hash). No dependency, schema,
command, performance, license clearance or readiness is claimed beyond
what was executed; config/schema/app-config.schema.json is unchanged
(no contract field changed).

## DHA and boundaries

The order declares Decision: NONE; no critical append was performed or
needed; CRITICAL.md untouched. Preserved: all prior gateway/transport/
native behavior and their regressions (125 + 33 + the 78 pre-G native
tests), the accepted 003-f metric meanings and oracles, the five
original native vectors and the both-phases-zero positive control, all
prior immutable reports/orders/reviews, the exact strategic 003-g
order/active bytes (committed unchanged), the unchanged pre-published
003-f review, model/provider/profile, private state, deadline/
cancellation behavior and original sources. No merge, auto-merge, tag,
release or deploy; PR #5 remains the single 003 objective PR
(amended); no next work selected; no numeric advance; no competing
control reader started (the sole external wrapper consumed the signal
before this round); exactly one response OK is signaled after this
report's verified publication.

## Limitations and remaining work

- The live native target is NOT RUN: no live model/route/service
  authorization exists (order: NONE); all native evidence is synthetic
  owned-loopback HTTP plus pinned-dialect fixtures. The pinned
  reference (ggml-org/llama.cpp tools/server, commit
  3b4d6ab3f79651935fba1dd93732f29022a7f5f5) is a dialect reference, not
  the unknown deployed build; json_grammar_tested remains default deny
  until an actually tested serving build qualifies it.
- Full 003 scope (bounded qualification probes, probe runner, CLI,
  documentation closure) remains required in later finalized suffixes;
  no probe, benchmark or live claim is made here.
- The existing certifi (MPL-2.0) license-policy gate remains explicit
  and unresolved; no distribution audit is claimed from code tests.
- Strategic acceptance of the closed boundary defects is separate:
  this COMPLETE describes execution, not acceptance or release
  readiness.
