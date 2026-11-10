# OAP Work Order — 003-h

Status: FINAL
Identifier: 003-h
PR mode: AMEND_EXISTING_PR
Branch: oap/003-generator-adapters-and-cache-probes
Base commit: 93b43177f4dcd0b28ef2c5ed33a049f83217f152
PR number: 5
Expected active: 003-g
Provenance: H activated MVP; A13 A14 A15 A22 A36; remaining original003-a criteria1/5 and independent gateway minimum-admission evidence
Architecture SHA256: 4b41905396a3838269fd6cf372614cd23cb2c3b6a37be09f29ed752803c0983a
Governance SHA256: 870a62a16bcf90a8152f57fe054c8104008a999145989c94af0367bbc87e264a

## Objective

Finish bounded explicit generator qualification probes, CLI, user documentation and whole003
composition evidence. This is the existing objective003, not another PR. 003-g report/head/CI independently reviewed; its native boundary scope is verified.
Record any unresolved original criteria explicitly; do not bury adapter defects under probe tooling. Earlier continuations
and this inert draft never waive original003 requirements or authorize live inference.

## Dependencies and current state

Verified2026-11-10: uniquePR5OPEN/currentreportSELF883f1cb0587d242a9c675f94e7a5891833342f79,
soleimplementationparent29fb8b9686fc0be9f920e7c05fbe72dd86e5f2d3, report-onlydiff and
reportSHA256f4b88214556e714a802e9a747592c444a996f3f25f13e07489268489b9147cba.
Main/base93b43177f4dcd0b28ef2c5ed33a049f83217f152, sameoriginalbranch/onePR.
ImplementationCI42785261938/finalCI42785852083 all5SUCCESS(last08:53:14Z). Exactresponse
consumed2026-11-10T08:51:17.886551+00:00, no reread. Worktree clean before newstrategicreview;
boundednativegoalcleared/quiescent, selectedprofile unchanged. Independent8HTTPvectors/12POST
and83nativeHTTP+44mappingtests prove bothnativeboundaryfixes; no need to reimplement them.
Full003 remainsOPEN: probe/CLI scope absent and gatewayminimumadmissionrepair required. Read original003-a criteria1–6,
actual final generator/config/transport interfaces and bounded relevant architecture excerpts.
Preserve earlier structural semantics; do not import a stricter Codex profile.
Additional independently demonstrated gateway admission prerequisite: see strategic
audit/003-gateway-capability-admission-review.md and
/tmp/raggedized003-gateway-capability-review.py. This is existing003-a criterion1, not a
new feature or active003-g expansion. At883f1cb the gateway source is unchanged and those observations remain current.

## Allowed paths and scope

Focused model_clients/probes module or scripts/qualification, existing CLI wiring, directly
required contracts/config, real controlled HTTP and CLI tests, generated schemas and concise
generator/probe documentation, README/TESTING/STATUS/UNCERTAINTIES and notices. Adapter changes
only for demonstrated probe composition defects and with retained b/c regression proof,
including the explicitly documented gateway minimum-capability admission repair below.
Exact strategic activation/review files and affected governance hashes. No new model stack,
ingestion/retrieval framework, service/GPU control or OAP helper redesign.

## Non-goals

No live qualification/model/GPU/corpus work, cache-reset/service-control operation, model
download or target discovery; no extraction/retrieval/API/product-agent feature, newdependency,
newPR/numericadvance, merge, tag, release or deploy. This proves executable bounded tooling
and synthetic HTTP composition; realruntime/cache/quality qualification stays NOT RUN.

## Acceptance criteria

1. Public command requires explicit probe opt-in and actual configured gateway/direct mode;
   import, help, doctor, ordinary readiness and default tests never dispatch a probe. Private
   direct mode remains offline-only and subject to the native round's trusted/template gates. Neither mode
   falls back to the other after denial. Credentials resolve only through deliberate safe
   operator reference; no real key on command line, report, error or log.
   Honor explicit gateway requiredJSON_MODE/PROMPT_CACHING minimums independently of actual
   format/cachekey fields. At current883f1cb, validconstructor requiredJSON-only/noformat and
   requiredCACHE-only/nokey both dispatch despite defaultfalse routecapabilities. Refuse
   those unqualified minimums at zeroHTTP, preserve actualformat/cachekey gates, and retain
   qualifiedminimum-only/ordinaryTEXT positives. Requirement alone need not invent a format
   or key. Add actualHTTP regressions; no broader gateway wire/parser redesign.
2. Before dispatch validate finite positive overall wall-time, output-token and request/call
   budgets. One deadline spans the complete experiment, both paired requests, template work
   and retries; a per-call allowance never resets it. Count actual model dispatch attempts
   and separately record non-inference template/network work. A finite budget cannot be
   bypassed by retries or template requests. Insufficient budget yields explicit incomplete/
   not-run evidence with no extra generation. Use small safe synthetic text fixtures only.
   Reserve a call/attempt allowance BEFORE every transport invocation, including template
   work and failed connects; conservatively count ambiguous dispatched work as spent, never
   replay it. Bound total output allowance across the pair, not only each request separately.
   Record attempted calls separately from known/unknown dispatch state. The current native
   GeneratorResult.attempts counts template/generation cycles: it is NOT an authoritative
   count of model dispatches or all network work. Exercise the actual transport boundary;
   do not estimate dispatch counts from a result or reset budgets in each adapter.
3. Repeated-parent experiment deliberately constructs stable parent A and child suffixes,
   records cold A/warm B ordering, exact prefix/config/template/backend identities, native
   cache/slot controls only where qualified, and actual safe response outcomes. Do not call
   a first application request physically cold unless cache reset/isolation was authorized
   and verified. Without such control label it first-call/second-call, cold state unknown.
   Preserve purpose separation and never publish arbitrary parent/model output as evidence.
   Use one constant bounded synthetic parent and explicit deterministic child suffixes; record
   fingerprints/lengths rather than raw material. Stable reuse does not authorize a reset or
   prove a serving cache exists. Do not assert cache isolation from a client key alone.
4. Safe structured evidence records declared model/runtime identity, exact dialect, budgets,
   attempts/outcomes and elapsed timings with their measurement boundaries. Absent deployed
   runtime/artifact identity stays unknown. Record actually reported evaluated prefill/cache
   metrics and denominators; submitted/input tokens or faster wall time cannot substitute
   for evaluated work or prove cache hits. Gateway missing prefill remains unavailable.
   Missing/invalid measurements must produce an unqualified conclusion, never a synthetic
   zero or claimed cache success. Fixed synthetic fixture metrics are test data only.
5. Output correctness is explicitly limited: record terminal validity, available exact
   expected-output checks and disagreement, separately from semantic model quality. Equal
   answers do not establish truth, speed does not establish caching, and a mock does not
   qualify actual model/template/context-window behavior. Preserve NOT RUN for all real trials
   absent approved targets. Evidence export is bounded and excludes raw secret/prompt/image/
   provider-error content and private endpoint credentials.
   Declared identities are bounded safe operator metadata, not independently verified model
   artifacts. Arbitrary response text must not enter evidence: use a digest/equality result
   when needed. Never include an endpoint URL, authorization header, secret reference value,
   configured instruction, rendered prompt, source item, image material or provider error.
6. Exercise the installed CLI and both real adapter paths against owned local HTTP servers.
   Assert exact request count/order/control payloads, budget exhaustion across the pair and
   retries, no implicit dispatch, missing metrics, mismatched outputs, unknown-completion
   no-replay, safe canaries and invalid config before dispatch. Test actual composition,
   not only mock invocation. All existing transport/gateway/native/foundation/OAP regressions,
   product lint, generated schemas/governance and the current CI matrix must pass.
7. Review original003-a criteria1–6 and final b/c/d/e/f/g contracts in a concise evidence table,
   including actual test/command references and any limits. Complete docs cover exact public
   CLI/config contract and safe examples. Whole003 acceptance needs full software scope;
   any absent requirement yields truthful continuation, not a narrowed COMPLETE claim.

## Verification and negative evidence

Prove composition with the installed raggedized CLI in subprocesses and actual gateway/native
adapters against owned loopback servers, observing paths/order, finite generation controls
and complete aggregate budgets. Include missing explicitoptin/invalid budget at zero dispatch,
too-small remaining call/output allowance, deadline exhausted during firstcall or template
stage, pre-dispatch retry consumption, unknowncompletion/no replay, missing/invalid metric
evidence, differing terminal outputs and secret/provider canaries in exported JSON.
Run applicable fullproduct/OAP/lint/governance and currentheadCI. Fixture timing/counters are
testdata; preserve earlier gateway/native negative oracles and positive controls.

## Documentation

Document exact public CLI arguments/exitcodes/config/credentials and safe synthetic examples.
Add original003-a criteria1–6 plus suffixcontract evidence table with specific current
test/command references, not counts alone. Whole003 software acceptance needs adapter/probe/
CLI/docs composition. Update STATUS/UNCERTAINTIES and measured governance readset/hashes
together when changed. Explicitly retain realtarget/hardware/license gates.

## Runtime and protected resources

Live authorization: NONE. No reply to the pending approvedtarget/corpus/GPUownership or
certifi-onlylicenseexception questions. Their absence does not create authority or a waiver.
Without a supplied explicit live allowance: no deployed gateway/model requests, SSH, downloads,
GPU/process changes or real corpora. Owned loopback fixtures and ordinary GitHub CI remain
authorized. Preserve the known HTTPX/certifi MPL policy gate unless attributable human
instruction resolves it; code acceptance never implies permission to distribute or release.
No tag/deploy/release or coding merge.

## Deferred human adjudication

- Decision: NONE

## Publication and report

Amend the existing unique003 PR, publish unchanged activation bytes and an immutable report-only
SELF commit with literal implementation parent, verify remote publication and signal once.
End the coding goal at the report/response boundary. Strategy independently decides full003
acceptance, same-objective continuation or protected expected-head development merge.
Commit strategic003-g review and exactactivation unchanged; report actual newcounts and exact
implementationCI. No futureCI/reportpublishclaim in an immutable report. Existing wrappers
and report-verifier interfaces remain unchanged; do not scan/rewrite orchestration internals.
Baseline376product=241integration(125gateway+33transport+83native)+135unit; separate41OAP.
Commit pre-published oap/reviews/003-g-review.json unchanged. Keep the report concise: exact
identities, changed behavior, actual commands/counts/CI and remaining limits; reference prior
immutable evidence without reprinting the full transcript. Interfaces:

```sh
python3 oap/bin/verify_report.py --repo-root /home/janezp/codex-work/slaif-raggedized-helper --runtime /home/janezp/codex-supervision/slaif-raggedized-helper/runtime.json --identifier 003-h
bash /home/janezp/codex-supervision/slaif-raggedized-helper/send-response.sh --identifier 003-h
```

The sole external wrapper consumes notification before freshstartup. No reread/competingreader,
no nextwork selection or merge. End the bounded nativegoal at truthful report/response; a
PARTIAL/BLOCKED/FAILED report is valid evidence, never a whole003 scope waiver.
