# OAP Coding Report — 007-r

Identifier: 007-r
Result: PARTIAL
Repository: ulfe-lmi/slaif-raggedized-helper
PR number: 9
Branch: oap/007-embedding-pipeline
Base branch: main
Round base commit: 81159dd0d7278edbd07de904cf94a251a964a5aa
PR main base: 11badc7782bed326995d400f5532b63399b91fbd
Transcript commit: 52e5517de2c60a3b229cb710c6ad8dde5c9dd4fe (order/active/14 records/index, sole parent round base)
Strategic continuation: ad835959f17c0972b5d5c5278651b1afeb4395b1 (Root addendum 1, sole parent transcript)
Implementation head SHA: 270d4156c4bf813a12e58c32cdd638ddb1ca35d0 (sole parent ad835959)
Report publication commit: SELF

## Work and scope

Order 007-r (FINAL, DHA NONE, AMEND_EXISTING_PR) ran transcript-first. Transcript
52e5517d: exact final order (10,006 B, SHA-256
31abbbb2de8090bc9f89706fdcbabc33c00013c58b29f154c05ab8e4c1e2ee0d),
active `007-r`+LF, fourteen exact Root records (39,773 B total) plus the
exact index oap/reviews/007-r-root-records.json (3,487 B, SHA-256
c2e05921b4c6ae1f52dbb00b4bfbf8843ca4a2c7b049557a8283612980e024a9); every
source/target size and hash byte-verified pre-commit; no Root bytes edited.
Before implementation, Root issued scope addendum 1 (2,632 B, SHA-256
66f123c73df3e1b225a24e8cd7abc1c2d572f3475923f96e755c27a1b2a19d4b)
committed byte-exact at oap/reviews/007-r-documentation-scope-addendum-1.md
in the separate strategic-only continuation ad835959: it overrides the
T16/TESTING.md edit, preserves TESTING.md exactly at round-base bytes
(17,448 B, SHA-256 b84fd5c63384bd3a3778599d19f87cf916f567a82e3a64865b4279f6ae6eea8f),
keeps governance/manifest/context-budget (49,999/50,000 B) unchanged, and
narrows the implementation to exactly NINE paths. Implementation 270d4156
changed exactly those nine paths: the EIGHT immutable gateway-role-B files
(82,739 B, byte-exact from candidate SELF 77b4e8c911d558329bfbd2796bb9cc990d5f36e9,
implementation 786bc25e, per oap/reviews/007-r-component-index.json) — ONE
existing production replacement src/.../model_clients/gateway.py (59,033 B;
blob ee970180.. -> 4df60e9a..; diff byte-identical to Root's frozen patch,
SHA-256 d8abd945b1f66f475f3a00fe342884ea1ad648b595d7907b524c3abf45faf6a1,
+28/-0 lines versus Q) plus seven new paths (unit/integration role tests,
integration precedence test, four docs/parallel API/design files) absent at
base — plus ONLY the concise STATUS.md current-slice update. Behavior:
_valid_message_role helper; exact assistant-role admission at the collector
and the stream item-added/done boundaries with the fixed input-free error
"invalid message role" (hostile role value never echoed); latched
structural state.error precedence across ALL FIVE stream exception exits
through existing _finish_stream (no early break, no cancellation/drain/
cleanup/accounting/provider change). Reasoning entries, valid assistant
refusal/multiple items, literal untrusted outgoing user content, no-error
pre-dispatch retry and ambiguous post-send UNKNOWN_COMPLETION semantics
unchanged. No merge/reset/stash/clean/switch/rebase/cherry-pick; no nested
agents.

## Acceptance evidence

1. Exact nine-path diff: git status at commit = two modified (gateway.py,
STATUS.md) + seven new; gateway diff byte-equal to Root patch (+28/-0).
AST vs base: 38->39 top-level statements, sole new node FunctionDef
_valid_message_role; sole changed methods _collect_output,
_GatewayAccumulator._handle_item_added, ._handle_item_done,
GatewayGenerator._run_stream; guard counts: collector return 1,
state.fail 2, latched `if acc.state.error is not None:` 5.
2. Actual runs, each once, own process, prlimit --as=1073741824 --cpu=30
timeout 120, cached .venv/bin/python3.14 (3.14.4), PYTHONDONTWRITEBYTECODE=1,
five thread caps 1, private 0700 basetemp: (a) tests/unit/
test_gateway_message_role.py with PYTHONPATH=src: 15 passed (0.54 s), exit
0; (b) tests/integration/test_gateway_message_role.py, separate process,
PYTHONPATH unset: 15 passed (8.53 s), exit 0; (c) tests/integration/
test_gateway_role_error_precedence.py, separate process: 4 passed (3.83 s),
exit 0 (19 new actual owned-loopback cases total; duplicate unit/
integration basenames never combined); (d) three named regressions in one
separate process (test_gateway_generator.py::
test_full_generator_stream_post_send_close_unknown_no_retry, ::
test_pre_connect_retry_policy_is_finite, test_generator_transport.py::
test_stream_close_after_send_is_safe_non_retryable): 3 passed (1.66 s),
exit 0.
3. Timeout-guard causal control ran inside (c): original source FAIL/no
text, guard-withdrawn control (source sha256 printed) UNKNOWN text,
restored FAIL/no text, healthy timeout UNKNOWN text; synthetic
generic-after-real-frames and controlled late-close faults labelled
controlled; one attempt/call asserted per case. No fabricated actual TCP
reset/cancellation/hardware proof.
4. ruff 0.17.4 on the four changed Python files: All checks passed. Exact
candidate hashes verified for all eight files at extraction and at commit.
5. Intermediate CI DISTINCTION: implementation head 270d4156 (an
intermediate head; the order forbids intermediate-head CI waits and no
wait was treated as a gate) run 43311410951 observed terminal failure:
Product tests (Python 3.12) step 17 "Integration test suite (owned
loopback HTTP/SSE)" FAILED at the pre-existing node tests/integration/
test_cpu_embedding_worker_composition.py::
test_watchdog_expires_while_owned_parent_paused (ProcessLookupError on
/proc/<pid>/stat; same step SUCCESS on the 3.14 leg; outside the nine
changed paths); OAP 3.12/3.13/3.14 10/10 and Product 3.14 24/24 success.
No product patch is made in this round; the gate is preserved for Root
(snapshot audit/007-r-coding-intermediate-43311410951-observation.json +
failed-step log in the strategic home). CURRENT REPORT CI (report head) is
PENDING/UNOBSERVED at publication: all 5 required jobs and every actual
step must be SUCCESS there; observed post-push in a separate receipt, not
certified by this report.
6. SELF report: this file, bare 40 SHAs, <=8192 B, sole parent
implementation, report-only diff, strict remote verification on PR 9 per
protocol.

## Documentation impact

ONLY STATUS.md (concise current-slice update to 007-r per addendum 1);
TESTING.md, oap/governance/, MANIFEST and the 49,999/50,000 B routine
readset preserved byte-exact (no T16 accounting added to always-loaded
law). The four copied docs/parallel API/design files and this report carry
the actual scoped test/qualification distinctions.

## DHA and boundaries

Order Decision: NONE; addendum DHA: NONE; no CRIT append, no candidate.
Preserved: human Qwen3.8/A100 profile/auth, sole control/response helpers,
all prior immutable orders/reports/Root records, P/O/Q and other slices'
bytes, pyproject, dependencies, law, CRITICAL, inert drafts. No merge
performed; PR 9 OPEN, auto-merge off; no 008/tag/deploy/release/nested
agents/other consumer; no intermediate-head CI wait honored as a gate.

## Limitations and remaining work

PARTIAL: (1) CURRENT REPORT CI PENDING/UNOBSERVED at publication; (2)
intermediate-head red gate (3.12 watchdog node) recorded, unrepaired this
round — correction needs the next strategically activated suffix; (3)
whole 007 and full MVP remain PARTIAL: actual BGE UNRUN/UNQUALIFIED,
inert synthetic software, live gateway qualification/full ICA open;
controlled faults do not prove all transport/race/cleanup paths or
deployed billing/vacancy.
