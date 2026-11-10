# OAP Work Order — 003-e

Status: FINAL
Identifier: 003-e
PR mode: AMEND_EXISTING_PR
Branch: oap/003-generator-adapters-and-cache-probes
Base commit: 93b43177f4dcd0b28ef2c5ed33a049f83217f152
PR number: 5
Expected active: 003-d
Provenance: H current MVP execution; A13 A15 A22 A36; E003-a absent/incorrect native implementation; E003-d JSONdecoderValueError; DIRECT-01
Architecture SHA256: 4b41905396a3838269fd6cf372614cd23cb2c3b6a37be09f29ed752803c0983a
Governance SHA256: d0fcb42531e4450fc95eb6da56eb84eb1d85e4191817526864aabfe3a326f9bb

## Objective

Implement the real private offline native generator on the already-proved003-b transport,
with documented llama.cpp envelopes, actual template handling, truthful terminal/metric
mapping and controlled HTTP tests. Same003 branch/PR. Whole003 probe/CLI/documentation closure
can follow in003-f; do not expand this context into the entire RAG pipeline or benchmark suite.

## Dependencies and current state

Verified2026-11-10: uniquePR5OPEN/currentremote003-dreportSELF
 af87bcc16dfb252d71f8f909c0a770c5058de853, soleparentimplementation
8e96b0cd50d186ef11e159906d376117488a90ac, onlyreportdiff; reportSHA256
02f8bb5a9d06ee9eb18595019da20be0f27c8d870389fb83070274397feedf1a.
Base/main93b43177f4dcd0b28ef2c5ed33a049f83217f152. ImplCI42764635506 and reportCI42765057169
all5SUCCESS. Exact003-dresponse consumed and remoteverified; never reread it. Strategy proves
the structural slice (13originalcases correct; unhashableaddedtypes now safe; deliberate
parentitemdone closure documented) and continues full003 for native/probes and one separate
olderdecoderValueError gap below. Worktree trackedcleanatSELF, only strategic003-dreview
untracked for unchanged commit. Prior bounded goal completed/cleared; fresh context perhandoff.
Reuse actual003-b/003-d transport/API rather than duplicating timeouts/exception layers.
Read compact coding law, this order and relevant source. Known native reference: official
ggml-org/llama.cpp tools/server/README at commit3b4d6ab3f79651935fba1dd93732f29022a7f5f5,
local read-only copy /tmp/raggedized-llama-server-reference.md. It is a dialect reference,
not the unknown deployed build. Pin current implementation semantics without live claims.
Strategy also retrieved exact pinned tools/server/server-task.cpp, server-context.cpp and
server-common.cpp into /tmp/raggedized-llama-server-{task,context,common}-reference.cpp.
Native final serialization is server-task.cpp to_json_non_oaicompat (line332+); its source
assignments are server-context.cpp line2425+; stats mapping is server-common.cpp line143+.
These small relevant excerpts resolve README ambiguity without reading the whole server.

## Allowed paths and scope

Required prerequisite before native work: the 003-d added-type guard is already fixed;
do not reopen that repair or the SSE design. A separate expected JSON error remains:
current nonstream completed JSON with usage.input_tokens encoded as5000digits throws plain
ValueError under the observed interpreter digit limit4300. _parse_non_stream catches only
JSONDecodeError/RecursionError; JSONDecodeError is only one ValueError subtype. Narrowly map
expected decoder ValueError at that parse call to a safe typed failure and add actualHTTP
regression(s) in tests/integration/test_gateway_generator.py. The read-only
/tmp/raggedized003-json-number-review.py reproduces it and records the actual limit; do not
assume every interpreter has the same enabled limit. Use a controlled supported digit limit
in an isolated test subprocess where necessary; do not change production/global interpreter
limits to force the test. Preserve all existing positive/error outcomes; no whole-generation
catch-all that hides programming errors. Native parsing must handle the same expected decoder
ValueError/RecursionError safely. This narrow gateway parse call/tests are explicitly in
scope; no other gateway refactor. Preserve both structural oracles unchanged.

src/slaif_raggedized_helper/model_clients/direct.py, focused shared base/config/schema
extensions, exports and actual native integration/unit tests. Shared transport changes are
limited to the directly necessary fixed native `/apply-template`/`/completion` endpoint
resolution or a demonstrated regression; preserve003-b URL, deadline, privacy, retry and
cleanup behavior and prove existing regressions remain green. Do not make an arbitrary-
destination/path proxy or redo the transport design unnecessarily.
Regenerate affected JSON schemas. docs/generator-contract.md native sections and focused
README/TESTING/STATUS updates; actual dependency/notice/CI wiring only if directly needed.
Exact prior-round strategic review plus order/active/report and affected manifest refresh.
No broad architecture, source-plan or roadmap rewrite, new PR or merge.

## Non-goals

No live model/route request, large downloads, GPU/service/process control, slots management
endpoint exposure, general-purpose proxy, direct online answer fallback, invented templates
or raw model tools. No full probe runner or new retrieval/answer API. Unknown vision/native
features remain explicit refusal until016; no silent ignored image/schema controls. Preserve
human-selected model/provider/profile and unrelated worktrees/private state.

## Acceptance criteria

1. Direct client is materialized only under explicit private trusted offline/diagnostic
   policy and configured private/loopback destination. Reject answer purpose and disabled/
   public/untrusted destination before network work, including after gateway failure.
   Direct network destinations and secret refs are operator-controlled; callers cannot
   supply arbitrary URL/file, model or process endpoint. No ambient proxy or redirect.
2. Use actual server chat-template rendering through the documented `/apply-template`
   semantic contract (messages -> prompt, no inference), or an exact explicitly qualified
   local-template mode with immutable template/build provenance. Unknown template refuses.
   Prefer server rendering to hand-invented model token strings. Native message closing
   markers must never be `</tool_call>`. A template name alone is not qualification.
   Correct the existing config's falsely pinned five-name built-in registry. The exact
   reference README236/243 says Jinja is enabled and the default template comes from model
   metadata; its real built-ins differ (e.g. mistral-v1/v3/v7 and phi3/phi4, not bare mistral/
   phi-2/llava). A qualified server-model/Jinja template identity must work through
   `/apply-template` without guessing special tokens or passing an arbitrary local-name
   allowlist. Separate declared template identity/build evidence from any actually supported
   local rendering mode, and refuse unimplemented local modes. See the concise strategic
   audit/003-native-template-config-review.md. This order now authorizes the native/config changes.
   Preserve trusted instruction/reference separation and stable-prefix identity.
3. `/completion` sends bounded formatted prompt, explicit n_predict and supported sampling
   options. Tested cache control is `cache_prompt`; tested slot selection is singular
   `id_slot`, not invented slot_ids. Each optional control requires the proper declared
   capability and documented native dialect; unsupported requested JSON/schema/cache/vision
   behavior refuses locally rather than being ignored. Until a qualified actual native
   image serializer exists, refuse every visual/image request before dispatch.
4. One caller/config total deadline and finite retry/output budget covers formatting,
   generation, reads and retries. Never reset deadline per attempt. Respect the smaller
   of caller/config output allowance and refuse incompatible requests before inference;
   explicitly choose clamp-vs-refusal semantics and document/test without hidden expansion.
   Materialized offline mode requires explicit finite operator max_output_tokens and
   deadline_seconds; the existing optional None fields are not permission to use an
   uncapped caller allowance. Missing operator limits refuse before template/generation
   dispatch. Test this zero-network boundary and expiry after template work before inference.
   Each actual network/model attempt is countable; unknown completion is non-retryable,
   only positive pre-connect failures may use finite retry. Cancel/close all owned I/O.
5. Native stop=true means stopped, not successful. `stop_type=limit`, `truncated=true`,
   missing/invalid terminal reason and still-generating state cannot become TERMINAL.
   Only supported EOS/qualified stop-word completion plus usable bounded content succeeds.
   Invalid encoding/JSON/fields or explicit failure produces safe typed failure; no raw
   provider body/credential/exception leaks. Model/adapter declared identity is stable and
   distinct from response text/ID; missing deployed runtime/artifact fields stay unknown.
6. Metrics map only from the pinned dialect's actual reported fields. Document native
   timings.prompt_n/cache_n/prompt_ms/predicted_n/predicted_ms semantics and units where
   supported; do not substitute total/submitted tokens for newly evaluated work. Unknown
   old-build fields stay null. Undocumented prompt_eval_count/eval_count fields cannot be
   asserted to be the native metric contract without actual source/version proof. Keep
   caller wall time separate from model timings and cold/warm cache correctness unqualified.
   Exact pinned source: tokens_evaluated comes from task.n_tokens(), whereas timings.prompt_n
   comes from n_prompt_processed and timings.cache_n from n_prompt_cached. The top-level
   tokens_cached is the slot's resulting prompt.n_tokens(), NOT necessarily cache hits for
   this request; never substitute it for timings.cache_n. A synthetic100-token submitted
   prompt with10new/90cached and12generated must preserve those distinct facts even if
   tokens_cached reports112. Validate finite nonnegative numeric types without accepting
   bool, NaN or infinity; malformed/contradictory counters cannot prove evaluated work.
7. Real controlled HTTP tests prove exact apply-template/completion payloads, supported
   multi-request deadline/call budgets, id_slot/caching gates, unsupported-purpose/image/
   schema refusal with zero inference dispatch, stopped-limit/context-truncation outcomes,
   malformed/canary/error refusal and actual native metrics. Prove complete positive calls
   with the documented dialect as well as failures; fake acceptance of invented fields
   is not compatibility. All003-b/003-c/003-d/foundation/OAP/lint/governance/CI remain green.

## Verification and negative evidence

Use owned local HTTP server fixtures and explicit synthetic qualification records. No model
downloads, real upstream keys or gateway access needed. Reference audit/003-direct-contract-
review-findings.md in strategic home for original defects, but inspect actual current source.
Test deadline across template+generation and retries, exact code/content/config fingerprints,
unit conversion and missing metrics, and response cancellation cleanup. CI must run new native
integration tests rather than skip them via a unit-only test path. Report actual test scope;
direct caching effectiveness and live deployment remain NOT RUN without actual target input.

## Documentation

Supported exact wire dialect, safe config/templates/capabilities, explicit offline-only
boundary, stable declared-vs-verified identity and actual metrics. Native qualification is
still open. Preserve the known certifi/license-policy gate unless explicit human action
supersedes it; do not declare a distribution audit passed from code tests.

## Runtime and protected resources

Live target/service/model/GPU/corpus authorization: NONE. Ordinary development and controlled
localhost fixtures are authorized. Other projects/services/GPUs/secrets remain protected;
no reads of agent credentials, unapproved SSH or live inference. Coding never merges.

## Deferred human adjudication

- Decision: NONE

## Publication and report

Amend the same003 PR and preserve all prior reports/orders. Commit unchanged strategic
activation with work, inspect/repair focused CI, publish immutable003-e report-only SELF
commit with actual implementation parent, remotely verify and send response once. Bounded
execution goal ends at truthful report/response; full003 remains open for explicit remaining
probe/closure scope. Strategy alone reviews and chooses continuation/acceptance/merge.

Commit oap/reviews/003-d-review.json unchanged with the exact strategic003-e order/active.
Use actual collection/run results in the report: baseline before003-e is236product tests
(156integration:123gateway+33transport;80unit), plus separate41OAP. Record new actual counts,
never copy the old erroneous003-c136/95/41 figures. No next-round selection or merge.

Existing operational interfaces (no helper-internal scan needed):

```sh
python3 oap/bin/verify_report.py --repo-root /home/janezp/codex-work/slaif-raggedized-helper --runtime /home/janezp/codex-supervision/slaif-raggedized-helper/runtime.json --identifier 003-e
bash /home/janezp/codex-supervision/slaif-raggedized-helper/send-response.sh --identifier 003-e
```

The sole external control wrapper consumes the signal before fresh-context startup; do not
reread it or start a competing reader. End the native bounded coding goal at truthful published
report/response; strategic acceptance and full003 closure remain separate. Preserve selected
model/provider/profile. PARTIAL/BLOCKED/FAILED reports are valid when actual limits remain;
never replace a missing contract with passing invented-field fixtures.
