# OAP Work Order — 003-j

Status: FINAL
Identifier: 003-j
PR mode: AMEND_EXISTING_PR
Branch: oap/003-generator-adapters-and-cache-probes
Base commit: 93b43177f4dcd0b28ef2c5ed33a049f83217f152
PR number: 5
Expected active: 003-i
Provenance: E exact-candidate credential-encoding observations; existing003-i criterion1 and remaining original003 documentation scope
Architecture SHA256: 4b41905396a3838269fd6cf372614cd23cb2c3b6a37be09f29ed752803c0983a
Governance SHA256: 48d621ab2070f2f745c918a48f4b106ddd0c965c8f6fd46f2bc3c9eb31456550

## Objective

Align credential-value admission with the actual locked HTTPX string-header serializer and
finish accurate003 software-scope documentation. FinalI source/report/head/all5CI have been
independently reconciled; the failure below remains and verifiedI improvements are preserved.
Same003PR5, no new objective or merge authority.

## Dependencies and current state

Verified2026-11-10: uniquePR5OPEN/originalbranch, base/main93b43177f4dcd0b28ef2c5ed33a049f83217f152.
CurrentIreportSELF693bec103b2a45472ac9477a94817d58928ddb85, soleimplementationparent
0a49ab978bcedf65ab9e44c2741a9038a20c7d9f, report-onlydiff and reportSHA256
110cc592df602494e61627799d083f8fb08d0bf8aebeb0ebee27bc14f2751881 verified.
ImplementationCI42809853110/finalCI42811174828 all5SUCCESS(last11:56:22Z). Exactresponse
consumed2026-11-10T11:54:25.058878+00:00; neverreread. Worktree clean before strategicIreview.
Priorboundedgoalcleared; quietpromptverified before freshstartup, model/profile unchanged.
Finalreview strategic audit/003-i-review.json records independent evidence andremaininggap.
ObservedI commits2258464ef54e0ee31935f98889e968204f458403 andCIrepair0a49ab978bcedf65ab9e44c2741a9038a20c7d9f
already fix originalFIFO/UTF8/path/counter/comparison/identity/export failures plus NUL and
non-Latin1 credential values and preexistingunwritable output targets. Do not reimplement them.
CI42809336766 failed Python3.12 on Path.exists PermissionError; repairCI42809853110 all5SUCCESS.
FinalIreportedCOMPLETE is notstrategicacceptance: actualfile/env U+00E9 failure persists;
allotherlistedIpositives are substantiated and not work to repeat.

Exactremainingcaseat0a49: /tmp/raggedized003-credential-latin1-review.py uses ownedHTTP,
syntheticcredentials andconfiguredfile/env references. ASCIIfilepositive makes2POST/complete0;
UTF8file orenv value containingU+00E9 both raise rawUnicodeEncodeError/zeroHTTP. Current
_header_value_unsafe_reason admits codepoints<=0xFF, but the real transport passes Pythonstr
headers and lockedHTTPX0.28.1 _models.py::_normalize_header_value encodes strings as ASCII
unless an encoding is supplied. The transport supplies none. This is the same required
header-usability boundary, not another Unicode feature or a new network capability.

Use a boundedreadset: current credential-value guard/caller, transportheader construction,
lockedHTTPX helper excerpt above, correspondingtests, compactgovernance and finalIreview.
Supplied verifier/response CLI interfaces suffice; do not reread helper internals or prior
source books absent a concrete orchestration failure.

## Allowed paths and scope

Focused probes.py value-admission guard and directly required caller/reason projection;
correspondingunit/API/realHTTP/installedCLI tests; currentcredential/header/output docs,
STATUS/README/TESTING/UNCERTAINTIES and affected governance measurements/hashes. Unchanged
strategicactivation/priorreview/report. No dependency or transport/parser rewrite, broader
credentialencoding support, architecture/source-original change or new service/model stack.

## Non-goals

No live model/target/GPU/corpus work, credential discovery, newPR/number, merge, tag/release/
deploy, helper rewrite or model/provider/profile change. Do not introduce rawbinary/Unicode
header support or silently re-encode/transliterate a key as a workaround.

## Acceptance criteria

1. Before any transport invocation, admit only credential strings representable by the current
   HTTPX header path. Correct the Latin1-vs-ASCII mismatch: validUTF8 file bytes are not proof
   that their decoded value is usable as a Pythonstr HTTPX header. Apply the same supported
   value check to env and file references. All unsupported nonASCII values, including the
   currently missed0x80–0xFF range, get a fixed typed CREDENTIAL_INVALID/exit2/zeroHTTP result;
   no rawUnicodeEncodeError, key/path echo or ambiguous transport attempt. Preserve ASCII
   positives, supportedfileending, C0/DEL-control refusal, boundedregular-file/FIFO/UTF8/size
   handling and privatepathdigest. Do not patch one character alone; align the entire admitted
   value domain with the actual serializer. ExistingreferencePATH NUL admission is already
   correct and is separate from credentialVALUE shape.
2. Meaningful unit and actualAPI/installedCLI/ownedHTTP tests cover file andenv U+00E9 plus
   an outside-Latin1 value and validASCII positives; unsupported inputs refuse before any
   HTTP/transport attempt. Retain original probes/comparison/backend/target/counter tests,
   shareddeadline/retry/attempt/output budgets, unknown-completion no-replay, expected-output
   checks and prioradapter regressions. Do not weaken the oracles to make the candidate pass.
3. Preserve the now-proved output fixes: existingowned0400target andinvaliddirectory refuse
   beforeHTTP, and a genuinelylate output failure after work yields exit3/fullsafeJSONstdout/
   exactspentaccounting and a safe post-work stderr stage. Preserve exception-safe filesystem
   probes on supportedPython3.12/3.14; no reintroduction of the0a49 CI failure.
4. Finish accurate current documentation. At observed0a49, STATUS and generator-contract's
   final paragraph still imply that live trials must be completed in003/samePR. Original003-a
   Runtime explicitly accepts software/tooling+syntheticHTTP withliveNONE: correct current
   projections without removing actual004/019/fullMVP qualification gates. Clarify8192 as the
   acceptedcredential-file size cap rather than an exact actual-read claim (boundedlookahead
   reads more); correct model_clients/probes.py to actualpackageprobes.py; distinguish post-
   work export from necessarily-post-dispatch, since its ledger states whether work occurred.
   Explain supportedheader values using actualHTTPX string encoding, not an abstract HTTP
   field-character allowance. Keep previous immutable reports/orders unchanged.
5. Reconcile full original003-a criteria1–6 andallrequiredsuffixcontracts with actualcurrent
   evidence. Complete product/OAP/lint/schema/governance and every expectedcurrent-headCI job
   must pass. One corrected guard alone is not whole003 acceptance; anyotherunmetI/original
   requirement remains visible. Strategy alone chooses protected development merge or another
   continuation. No live/runtime/cachequality/license/distribution claim is created here.

## Verification and negative evidence

Re-run /tmp/raggedized003-credential-latin1-review.py against finalsource, plus the applicable
original andsupplementaryAPI/CLI/deadline/FIFO/exportoracles referenced in finalIreview.
Original files remain unchanged; inspectactualfieldsemantics rather than obsolete projection
names (phaseidentity digests differ legitimately while contentcomparison is label-independent).
Ownedfixtures only. If coder is switching the sharedvenv for matrix reproduction, strategy
uses an isolatedreviewenvironment rather than mutating that venv concurrently.

## Documentation

Document the actualsupportedheader representation, fixedtypedreasons and meaningfulpositive/
negativeproof. Preserve allI improvements, explicitrealqualificationNOTRUN and the unresolved
license/distribution gate. Update affectedcontextmeasurements/hashes together. No new auditpass
or exception is inferred from directcomponent licenses, greenCI or elapsedtime.

## Runtime and protected resources

Live authorization: NONE. Pendingreal-target/credential/corpus/GPUownership andlicense
questions have no attributable reply; no permission or exception is inferred.
Owneddisposablefixtures/subprocesses and ordinarylightweighttooling/GitHubCI only. Preserve
source originals, agenthomes/settings/FIFOs, unrelatedservices/GPUs andrealcredentials. No
networksourcefetch, licenseexception, release or deployment authority.

## Deferred human adjudication

- Decision: NONE

## Publication and report

Amend uniquePR5. Commit exactstrategicactivation/priorreview unchanged, publish a concise
truthful immutable report-onlySELF withliteralimplementationparent, verifyremotepublication,
respond exactlyonce through existingwrapper and end boundednativegoal. No consumedFIFO
reread, competingreader, merge or nextworkselection. Baseline440product=171unit+
269integration(129gateway+83native+33transport+24probe), separate41OAP. Commit exact
pre-published oap/reviews/003-i-review.json unchanged. Correct priorreport increment facts
without editing it: Iadded+21total =+12unit +9integration, not+21unit/+9integration.
Use concise evidence and literal identities, not a repeated transcript. Existing interfaces:

```sh
python3 oap/bin/verify_report.py --repo-root /home/janezp/codex-work/slaif-raggedized-helper --runtime /home/janezp/codex-supervision/slaif-raggedized-helper/runtime.json --identifier 003-j
bash /home/janezp/codex-supervision/slaif-raggedized-helper/send-response.sh --identifier 003-j
```

For collection counts, projectpytest configalreadyaddsquietmode: use
uv run --locked pytest tests/unit tests/integration --collect-only -q -o addopts=''
instead of --co -q | tail -1 (which canhide the summary). Collection is not passingproof;
do not rerun passedHTTPsuites solely to count them. Newchanges/failures still need relevant
verification and finalheadCI. End boundednativegoal aftertruthful report/response; strategy
aloneaccepts/selectscontinuation/merges. No model/provider/profile change.
