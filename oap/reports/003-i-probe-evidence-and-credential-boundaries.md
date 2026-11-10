# OAP Coding Report — 003-i

Identifier: 003-i
Result: COMPLETE
Repository: ulfe-lmi/slaif-raggedized-helper
PR number: 5
Branch: oap/003-generator-adapters-and-cache-probes
Base branch: main
Implementation head SHA: 0a49ab978bcedf65ab9e44c2741a9038a20c7d9f
Report publication commit: SELF

## Work and scope

Executed oap/orders/003-i-probe-evidence-and-credential-boundaries.md
(Status FINAL, Decision: NONE, live authorization: NONE, active 003-i,
PR mode AMEND_EXISTING_PR) on the existing unique 003 objective PR #5,
branch oap/003-generator-adapters-and-cache-probes from verified base
main 93b43177f4dcd0b28ef2c5ed33a049f83217f152. At round start the remote
head 24d27a0a404ebc2a9ae4a98935984ef6c4bfbb64 was the published 003-h
report SELF (sole implementation parent
e91e737592deccbbb4dfdcd6ab411a21aae0a776; PR #5 the sole OPEN
MERGEABLE PR), and the worktree carried exactly the strategic
round-start bytes: modified oap/active (003-h -> 003-i), new
oap/orders/003-i-probe-evidence-and-credential-boundaries.md and new
oap/reviews/003-h-review.json. Two commits were pushed before this
report:

- 2258464ef54e0ee31935f98889e968204f458403 (implementation, 14 files,
  +1647/-124): the corrected probe evidence/credential boundaries in
  src/slaif_raggedized_helper/probes.py and cli.py, the unit and
  installed-CLI regressions, the docs/README/TESTING/STATUS/
  UNCERTAINTIES updates and the refreshed governance measurements, plus
  the exact strategic 003-i activation bytes and the unchanged
  pre-published 003-h review (oap/reviews/003-h-review.json committed
  byte-for-byte as found in the worktree).
- 0a49ab978bcedf65ab9e44c2741a9038a20c7d9f (implementation head,
  CI repair, 1 file, +26/-17): the pre-dispatch `--output`
  destination probe in cli.py is now fully exception-safe. The 3.12 CI
  leg of 2258464 failed because Python 3.12 `Path.exists()` RAISES
  PermissionError for a target inside an unsearchable (mode 000)
  parent, while newer interpreters return False; both are now handled
  identically (unprovable destination = knowably invalid = exit 2,
  zero HTTP). No behavior other than that exception path changed.

Changed behavior, by 003-i criterion (all in probes.py unless noted):

1. Credential resolution is bounded, safe and typed BEFORE any HTTP:
   `resolve_secret_value` was replaced by
   `resolve_secret_reference` -> `SecretResolution` (status
   resolved/missing/invalid + fixed reason code; repr never echoes the
   value). File references are opened non-blocking (`O_RDONLY|
   O_NONBLOCK`) and the opened descriptor is `fstat`-checked
   (S_ISREG): FIFOs, sockets, devices and directories are refused
   (`file_not_regular`) without a blocking open and without killing
   any child. At most 8192 bytes are actually read
   (`file_too_long` beyond), content must be valid UTF-8
   (`file_not_utf8`) and a single line (one optional trailing
   newline, no CR/other line breaks; `file_not_single_line`);
   missing/empty map to `file_absent_or_unreadable`/`file_empty`/
   `env_absent_or_empty`. Because the value is used verbatim as the
   Bearer credential of the Authorization header, it must be
   header-usable: non-Latin-1 code points are refused
   (`value_not_latin1`) and control characters including NUL
   (`value_contains_control_character`) — a non-ASCII value previously
   leaked a raw UnicodeEncodeError mid-dispatch and a NUL value
   consumed the dispatch budget as ambiguous work; both are now fixed
   typed pre-dispatch refusals. The probe returns
   CREDENTIAL_ABSENT / CREDENTIAL_INVALID with the reason at exit 2
   and zero HTTP; no raw exception escapes and no secret or private
   path is echoed. File references appear in evidence only as an
   opaque digest (`fingerprint({"kind":
   "probe-credential-file-ref", "name": path})`); env references keep
   the plain name. Credential/preflight setup is excluded from the
   measured experiment time (`budgets.elapsed_seconds_scope`).
2. Output checks are interpretable without raw output: each phase now
   carries BOTH the label-qualified phase-identity
   `text_fingerprint` (kind `probe-response-text`, label part of the
   payload — documented digest an operator computes with the
   installed package's `fingerprint` helper, not a plain-text
   sha256sum) and a label-independent `content_fingerprint` (kind
   `probe-response-content`), plus top-level
   `pair_comparison.same_output` (true/false/null — null while either
   phase is missing or non-terminal; equal outputs never establish
   truth, caching or quality). Per-phase expected-output checks are
   unchanged digest equality (documented namespaced format).
3. Reported counters are distinguished from validated conclusions:
   per-phase `accounting_validity` (not_run / unreported /
   uncheckable:input_tokens_missing / invalid:cache_hit_exceeds_input /
   valid) is computed against the supported relation
   (`cache_hit_tokens <= input_tokens` when both are reported; the
   pinned gateway f2df0e82 validates `cached + cache_write <=
   input_tokens` on its own reported usage). New conclusions:
   `metrics_invalid` (contradictory counters — the demonstrated
   cached-999/input-5 case — preserved as raw facts only, unqualified)
   and `metrics_unvalidated` (relation uncheckable); the documented
   `accounting_relation` string accompanies the evidence.
   CORRECTION of the 003-h claim: the pinned gateway dialect DOES
   report `usage.input_tokens_details.cached_tokens` (mapped to
   `cache_hit_tokens`); what it does NOT report are evaluated-prefill
   metrics, which stay null/unavailable. No submitted-token or
   wall-time substitution; known-zero, first-/second-call ordering and
   unknown cold state preserved.
4. Evidence binds the declared backend identity: each request exports
   the `GeneratorResult.fingerprint` as `backend_fingerprint`, and
   `identities.backend_fingerprint` is
   `gateway_backend_fingerprint(route)` / `direct_backend_fingerprint
   (direct)` (dialect, pinned contract, declared model,
   credential-free endpoint, timeout, capability and, for direct,
   template/limit/slot snapshots) — an endpoint hash alone no longer
   stands in for the full binding. The hard-coded `"live": False` is
   replaced by `"target_type": "unverified"` with a note: the runner
   cannot classify an owned fixture vs a live target, and a localhost
   address or an order live allowance does not establish target type;
   `runtime_identity` stays unverified.
5. Installed-CLI positives preserved: the 003-h import-scope repair is
   retained; independent installed gateway/native commands and the
   expected-output-positive commands run the bounded experiment
   (oracle: match/match), while help/import/doctor and invalid
   budgets/configs stay zero-dispatch.
6. Pre-dispatch vs post-work output stages (cli.py): a knowably
   invalid `--output` destination (missing/non-directory/
   non-searchable/non-writable parent, non-regular-file target, or a
   pre-existing non-writable target file) is refused BEFORE dispatch
   with exit 2 `OUTPUT_DESTINATION_INVALID` and zero HTTP; a write
   failure after the probe returned returns exit 3
   `EVIDENCE_EXPORT_FAILED` with `stage: post_work_evidence_export`,
   the FULL safe evidence document on stdout and the error JSON on
   stderr stating honestly whether transport calls were attempted
   (">0 calls: do not replay blindly" vs "no transport call was
   attempted").

## Acceptance evidence

1. tests/unit/test_probes.py: test_resolve_secret_reference_env,
   _file_positive, _file_missing_and_empty,
   test_resolve_secret_reference_fifo_refused_without_blocking (owned
   FIFO, non-blocking open + fstat, < 1.0 s, no child killed),
   test_resolve_secret_reference_special_files_and_shapes (directory,
   invalid UTF-8, multi-line, CR, over-8192-byte),
   test_resolve_secret_reference_header_unusable_values (NUL/DEL/
   non-Latin-1 file AND env refusals with boundary positives: Latin-1
   0x80-0xFF and space remain usable),
   test_gateway_credential_reference_absent_refuses_before_dispatch,
   test_gateway_credential_invalid_file_refuses_before_dispatch
   (FIFO, invalid UTF-8, NUL, non-Latin-1 -> exit 2 CREDENTIAL_
   INVALID with the exact reason, zero transport calls, no private
   path in the document). Installed-CLI:
   integration/test_probe_composition.py invalid-config/credential
   cases (owned FIFO, directory, invalid UTF-8) refused pre-dispatch
   at zero HTTP.
2. tests/unit/test_probes.py label-qualified vs label-independent
   fingerprints (identical A/B text -> same content fingerprint,
   different phase-identity fingerprints),
   test_expected_output_check_match_mismatch_not_provided;
   integration test_gateway_probe_expected_output_positive (installed
   CLI: a/b "match") and the mismatch case; oracle
   probe-evidence-review: identical outputs -> same_output true,
   different -> false, non-terminal -> null; probe-export-review
   expected_digest_positive -> match/match at exit 0.
3. tests/unit/test_probes.py cache-counter cases: valid present ->
   `cache_hit_reported` with validity `valid`; contradictory
   cached-999/input-5 -> `metrics_invalid` with raw facts preserved;
   uncheckable (input missing) -> `metrics_unvalidated`; absent ->
   `metrics_unavailable`; gateway-dialect missing prefill stays null.
   Oracle probe-evidence-review gateway_contradictory_cache_counts:
   accounting_validity a/b `invalid:cache_hit_exceeds_input`,
   conclusion `metrics_invalid`.
4. tests/unit/test_probes.py identity binding (per-request
   backend_fingerprint equals the declared gateway/direct fingerprint
   and identities.backend_fingerprint; `target_type: unverified`
   present, no `live` field); oracle probe-evidence-review:
   backend_binding_present true, phase_bindings_match true,
   target_type unverified on every terminal case;
   private_secret_reference_export: canary path absent from the
   evidence (private_secret_reference_leaked false) while the
   credential still reaches only the Authorization header.
5. tests/integration/test_probe_composition.py:
   test_doctor_help_and_missing_optin_never_dispatch (zero requests on
   import/help/doctor), gateway/native happy paths, the retained 003-h
   budget positives (dispatch allowance, shared deadline,
   unknown-completion no-replay, ambiguous work spent); oracle
   probe-cli-review/probe-export-review: help 0 paths, gateway_cli 2
   POSTs, native_cli 4 POSTs, invalid_budget 2 paths 0.
6. tests/unit/test_probes.py test_cli_probe_invalid_output_
   destination_refuses_before_dispatch (missing parent, directory
   target, non-writable parent, pre-existing mode-0400 file — all
   exit 2 OUTPUT_DESTINATION_INVALID, zero dispatch) and
   test_cli_probe_late_write_failure_returns_export_stage (exit 3,
   stage post_work_evidence_export, full evidence on stdout, honest
   dispatch note); oracle probe-export-review: invalid_output_
   directory 2/0 paths, knowably_readonly_output 2/0 paths,
   late_export_failure_after_work 3 with 2 spent POSTs and
   export_stage post_work_evidence_export.
7. Full regressions retained and green at the implementation head:
   440 product = 171 unit + 269 integration (129 gateway + 83 native
   + 33 transport + 24 probe composition), separate 41 OAP, ruff
   clean, check_state ACTIVE (see Verification). The five 003-h
   named oracles plus the two 10:56 strategic oracles were re-run
   against the source: gateway minimum-admission refusal/positives,
   shared .2 s deadline (.203 observed both modes), budget-3 native
   stop, accepted-close no-replay, failed-connects spend allowance,
   FIFO credential (0.037 s < 0.1 s deadline, 0 POSTs, no killed
   child) — all as observed above; no oracle was altered.

## Verification

Exact commands at the implementation head
0a49ab978bcedf65ab9e44c2741a9038a20c7d9f (all local, synthetic,
offline; no live model, download, credentials, GPU or corpus):

- uv run --locked pytest tests/unit -q — 171 passed, exit 0, on BOTH
  Python 3.12.15 and Python 3.14.4 (15 cli-doctor + 48 config + 14
  contracts + 3 import-hygiene + 11 model-lock + 44 native-mapping +
  36 probes, one of them parameterized).
- uv run --locked pytest tests/integration -q — 269 passed, exit 0
  (129 gateway + 83 native + 33 transport + 24 probe composition), at
  the 2258464 source; after the 0a49ab9 repair the CLI surface was
  re-verified on 3.12 (full unit suite + all 24 probe-composition
  tests) and on 3.14 (full unit suite); the clean-checkout CI matrix
  below re-runs the whole suite at the final head.
- python3 -m unittest discover -s tests/oap — Ran 41 tests, OK.
- uv run ruff check src tests/unit tests/integration — All checks
  passed.
- python3 oap/bin/check_state.py --repo-root . — state ACTIVE, active
  003-i, exit 0; activation_matches_current_governance=false is
  expected (the immutable order's Governance SHA256 predates the
  in-scope TESTING.md/CONTEXT-BUDGET/MANIFEST refresh, same state as
  003-h).

Baseline 419 product = 159 unit + 260 integration (129 + 83 + 33 + 15
probe) + separate 41 OAP. Actual at the implementation head: 440
product = 171 unit + 269 integration (129 + 83 + 33 + 24 probe) = +21
unit / +9 probe-composition, plus the separate 41-test OAP suite
unchanged.

Independent oracles (owned 127.0.0.1 loopback, synthetic canaries,
read-only, unmodified): all seven ran clean —
/tmp/raggedized003-gateway-capability-review.py (7/7), -probe-review.
py (7/7), -probe-credential-review.py (1/1), -probe-cli-review.py
(7/7), -probe-deadline-review.py (4/4), -probe-evidence-review.py
(9/9), -probe-export-review.py (9/9). The evidence/export oracles
were additionally re-run at the final head 0a49ab9 after the CI
repair with identical outcomes (knowably_readonly_output exit 2 zero
HTTP; late export exit 3 post-work stage; credential NUL/non-Latin-1
pre-dispatch typed refusals).

CI (GitHub Actions, clean locked checkout):
- Implementation head 0a49ab978bcedf65ab9e44c2741a9038a20c7d9f: run
  42809853110 (created 2026-11-10T11:44:00Z), all 5 jobs SUCCESS —
  Product tests Python 3.12 and 3.14; OAP tests Python 3.12, 3.13,
  3.14.
- Repaired within scope: run 42809336766 at 2258464
  (Product tests Python 3.12 FAILED: interpreter-dependent
  Path.exists() PermissionError on an unsearchable parent in the new
  pre-dispatch destination probe; OAP legs SUCCESS) — fixed by the
  exception-safe rewrite in 0a49ab9 and re-verified on 3.12 locally
  before push.

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

- docs/generator-contract.md: the probe section is now "003-h,
  boundaries corrected in 003-i"; documents the bounded credential
  resolution (non-blocking regular-file read, 8192-byte bound,
  single-line UTF-8 shape, header-usability rule with the fixed
  reason codes), the documented expected-digest computation
  (namespaced structured fingerprint, not plain-text sha256sum), the
  label-qualified vs label-independent fingerprints and
  pair_comparison semantics, the accounting-relation validation with
  the new metrics_invalid/metrics_unvalidated conclusions, the
  corrected gateway claim (cached_tokens IS reportable by the pinned
  dialect; evaluated-prefill is NOT), the exported backend
  fingerprint binding with target_type: unverified, the CLI exit-3
  post-work export stage and the pre-dispatch destination refusal
  (including a pre-existing non-writable target file).
- README.md: probe CLI overview updated (exit codes 0/1/2/3,
  bounded credential references).
- TESTING.md T07: extended with the 003-i corrected cases
  (control-character/non-Latin-1 credential values, knowably
  invalid --output incl. non-writable target, exit-3 export stage,
  label-independent comparison, validated cache counters, backend
  fingerprint + target_type).
- STATUS.md: active objective 003-i plus the round entry.
- docs/UNCERTAINTIES.md: 003-i observation appended (003-h entry
  preserved): U05 CORRECTION of the superseded gateway claim
  (cached_tokens reportable; prefill not), the tooling narrowing
  (validated counters, backend binding, unverified target type).
- Governance, updated together with the doc change:
  oap/governance/CONTEXT-BUDGET.md (TESTING.md 5780; declared
  routine project governance 38331 UTF-8 bytes, ceiling 50000) and
  oap/governance/MANIFEST.json pins for TESTING.md
  (1b0e75cc0fcb4e1c3fb9d5987b8087007992110b37801baa3e50bee9d1689f5b)
  and oap/governance/CONTEXT-BUDGET.md
  (c254cca1cc7e5308487878a5ab2d775cf961341107f6351e58ad633cc32b7816);
  check_state verifies every manifest hash.
- src/slaif_raggedized_helper/model_clients/gateway.py is unchanged:
  the order allowed usage-counter validation there "if needed for the
  demonstrated invalid-counter case"; it was not needed — the pinned
  gateway already validates cached + cache_write <= input server-side
  at the pinned commit, and the demonstrated contradictory-counter
  case is closed by the probe-level relation check (criterion 3
  "validate the supported accounting relations, or explicitly mark
  invalid/unavailable measurements unqualified"), with no SSE/wire/
  parser redesign.

## DHA and boundaries

The order declares Decision: NONE; no critical append was performed or
needed; CRITICAL.md untouched. Preserved: all prior gateway/
transport/native behavior and regressions (129 + 33 + 83), the
accepted 003-e/f/g metric meanings and oracles, the 003-h import-
scope repair and budget positives, the /tmp/raggedized003-* oracle
scripts (read-only, unmodified), the OAP FIFOs (untouched), all prior
immutable reports/orders/reviews, the exact strategic 003-i order/
active bytes (committed unchanged) and the unchanged pre-published
003-h review (byte-for-byte), model/provider/profile, private state
and original sources. No merge, auto-merge, tag, release or deploy;
PR #5 remains the single 003 objective PR (amended); no next work
selected; no numeric advance; no competing control reader started
(the sole external wrapper consumed the notification before fresh
startup); exactly one response OK is signaled after this report's
verified publication.

## Limitations and remaining work

- Live qualification is NOT RUN: no live model/route/service
  authorization exists (order: NONE); all probe evidence is synthetic
  owned-loopback HTTP plus pinned-dialect fixtures. No cache-hit,
  speedup or prefix-reuse observation exists (U05 OPEN); a reported
  cached counter alone never qualifies work reduction, and evaluated-
  prefill metrics remain unavailable in the pinned dialect.
- The 3.12 CI failure at 2258464 was repaired within scope (0a49ab9);
  the repair is exception-handling only in the pre-dispatch
  destination probe, re-verified on both matrix interpreters.
- Whole-003 acceptance (including live-target evidence and the
  protected expected-head development merge) is a separate strategic
  decision: this COMPLETE describes execution of the ordered 003-i
  scope, not acceptance or release readiness.
- The existing certifi (MPL-2.0) license-policy gate remains explicit
  and unresolved; no distribution audit is claimed from code tests.
