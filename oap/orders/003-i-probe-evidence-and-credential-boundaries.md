# OAP Work Order — 003-i

Status: FINAL
Identifier: 003-i
PR mode: AMEND_EXISTING_PR
Branch: oap/003-generator-adapters-and-cache-probes
Base commit: 93b43177f4dcd0b28ef2c5ed33a049f83217f152
PR number: 5
Expected active: 003-h
Provenance: E independent owned-HTTP/API/CLI/credential observations; A13 A15 A22 A34 A36; existing003-h criteria1–7
Architecture SHA256: 4b41905396a3838269fd6cf372614cd23cb2c3b6a37be09f29ed752803c0983a
Governance SHA256: f34be4e33937d1eb504bfe40238da4bf92f2b3760868fad6b0a69a816221c2d8

## Objective

Close demonstrated probe evidence/credential boundaries while preserving bounded real adapter
composition. Actual003-h report/head/source and all5finalCI have been independently reviewed.
The confirmed gaps below remain at the exact implementation; no need to reimplement the
working adapter/budget/CLI paths. Same objective003/PR5; all original software scope remains.

## Dependencies and current state

Verified2026-11-10: uniquePR5OPEN, originalbranch, base/main93b43177f4dcd0b28ef2c5ed33a049f83217f152.
CurrentreportSELF24d27a0a404ebc2a9ae4a98935984ef6c4bfbb64, soleimplementationparent
e91e737592deccbbb4dfdcd6ab411a21aae0a776, report-onlydiff and reportSHA256
3573b798eb8410723ee3aa3c61c3e6bdce208f65157e3c4ac037d403a3a32936 verified.
ImplementationCI42795740359/finalCI42798362156 all5SUCCESS(last10:23:23Z). Exactresponse
consumed2026-11-10T10:21:34.118005+00:00; never reread. Worktree clean before new strategic
Hreview; priornativegoalcleared/quiescent, selectedprofile unchanged. Independent exact-code
proof/source and oracle hashes: strategic audit/003-h-exact-head-e91-review.json; finalreview
audit/003-h-review.json and criterionmatrix audit/003-original-software-scope-review.md.
ReportCOMPLETE/allcriteria-met claims are not acceptance: confirmed negative observations
persist, despite working gateway/nativeCLI, shared deadlines/attempt budgets and419green tests.

Independent owned-only scripts remain separate from product code:
/tmp/raggedized003-gateway-capability-review.py,
/tmp/raggedized003-probe-review.py,
/tmp/raggedized003-probe-credential-review.py,
/tmp/raggedized003-probe-cli-review.py,
/tmp/raggedized003-probe-deadline-review.py.
Do not alter these oracles to make a candidate pass. Update project regressions meaningfully.

## Allowed paths and scope

Focused probes.py/cli.py and directly affected credential/config boundary if necessary;
focused model_clients/gateway.py usage-counter validation if needed for the demonstrated
invalid-counter case, with no unrelated SSE/wire/parser redesign;
corresponding actualHTTP/API/CLI and credential-file tests; exact probe evidence/usage docs,
current status/uncertainties and affected governance hashes/readset. Unchanged strategic
activation/priorreview/report. No newdependency, transport rewrite, gateway protocol expansion,
retrieval/model feature or architecture/source rewrite.

## Non-goals

No live target/model/GPU/corpus operation, cache reset, endpoint discovery or qualification
claim; no new PR/number, merge, release/tag/deploy, model/profile/provider change, or independent
agent. Do not replace missing facts with invented performance, runtime identity or permission.

## Acceptance criteria

1. Credential resolution is bounded and safe before any HTTP. Retain configured env/file
   references without exporting their value or private file path. Refuse special files such
   as FIFOs without a blocking open, bound actual bytes read, validate the supported single-line
   encoding/shape, and return a fixed typed configuration outcome for missing/invalid input.
   An ownedFIFO currently blocks before the experiment timer (0.1s budget, no result beyond
   0.395s, zeroHTTP; only the owned test child was killed). InvalidUTF8 currently raises raw
   UnicodeDecodeError. A valid owned credential path containing PRIVATE_SECRET_REF_CANARY
   appears in evidence through ref.name. Address the actual file/read boundary, not a catch
   that cannot unblock an open. Distinguish credential/preflight setup from measured model
   experiment time honestly; no unbounded input read or raw exception/secret echo.
2. Exact output checks are interpretable without raw output. Current text fingerprints include
   the phase label, so identical A/B text produces different fingerprints and no pair-comparison
   field exists. Record available same/different output evidence independently of labels and
   semantic correctness; unavailable/nonterminal text stays unknown. Keep phase identities
   separate, preserve per-phase expected-output checks with a documented digest format and
   installedCLI positive/mismatch tests. Equal outputs never establish truth; do not require
   equal answers for deliberately different child inputs or invent semantic-quality proof.
   Document how an operator actually computes the accepted expected digest; current flags
   use a namespaced structured fingerprint, not an unexplained plain-text sha256sum.
3. Distinguish literal reported counters from validated cache/evaluated-work evidence. Missing
   evaluated-prefill metrics remain unavailable; a positive reported cache counter alone is
   not a complete work-reduction qualification. Impossible cached999/input5 currently yields
   cache_hit_reported without an invalid/unqualified flag. Validate the supported accounting
   relations before any qualification conclusion, or explicitly mark invalid/unavailable
   measurements unqualified while preserving raw facts only as such. Do not substitute submitted
   tokens/wall time for work. Preserve knownzero, honest first-/second-call ordering and unknown
   cold state; no cache reset/isolation inference from a client key.
   Gateway cached tokens and unavailable evaluated-prefill are distinct: the pinned gateway
   f2df0e82 source responses_gateway.py lines710–729 supports input_tokens_details.cached_tokens
   and validates cached+cache_write <= input. Correct H's new claim that the gateway never
   reports prefill/cache metrics. Do not erase a legitimately reported cache counter or invent
   evaluated-prefill from it; prove valid-present, absent and contradictory cases separately.
4. Evidence binds the declared actual adapter/config identity and measurement boundaries.
   Export GeneratorResult.fingerprint or prove a fully equivalent stable backend binding;
   endpoint hash alone does not bind all backend controls. Runtime/artifact identity stays
   unverified until actually established. The runner currently hardcodes live=False for any
   configured destination, although it cannot know that it is a fixture: remove or qualify
   that unsupported classification. Explicit synthetic test provenance is valid for owned
   fixtures; a localhost address or work-order live allowance cannot establish target type.
   Do not introduce target discovery or a live request just to test this metadata boundary.
5. InstalledCLI positive commands actually run the bounded experiment; help/import/doctor and
   invalid budgets/configurations stay zero-dispatch. H's transient import-scope mistake was
   corrected: independent installed gateway/native and expected-output-positive commands now
   work. Preserve that repair rather than reimplementing it. Preserve deliberate opt-in,
   actual mode gates and all prior request/template/retry/output/deadline accounting.
6. Distinguish pre-dispatch configuration failures from evidence-export failures after work.
   Independent installedCLI proves --output failure after both requests returns usage2,
   while its docs promise usage2 always means zeroHTTP. Exercise an owned invalid output
   directory produced two actualPOSTs. Reject a knowable invalid destination before costly
   calls; if a later write fails after work, return an honest stage/outcome retaining safe
   spent-attempt evidence.
   Do not imply no dispatch or invite blind replay. A late I/O failure cannot always be
   prevented; no new generic filesystem transaction framework is required here.
7. Actual API/installedCLI and ownedHTTP/file tests prove corrected cases plus positive
   gateway/native paths, valid env/file credentials, no raw response/secret/path leaks,
   same/different/expected output checks, missing/contradictory metrics, partial budgets and
   unknown-completion no-replay. Preserve the independently proved H call-budget positives
   and gateway minimum-admission repair, all earlier native/gateway/transport/unit/OAP/lint/
   governance/schema regressions and exact current-head CI. Complete original003 composition
   evidence before whole-objective acceptance; no narrowed COMPLETE waiver.

## Verification and negative evidence

Re-run all applicable named independent vectors against the actual final source. The credential
FIFO test owns its temporary directory/pipe/child and never touches OAP FIFOs; only that test
child may be terminated. No real credential, source, model or protected resource is needed.
Retain precise distinction between proved behavior and a source-level concern. CLI output-write
behavior is now demonstrated after two actualPOSTs. MalformedUTF8credential returns raw
UnicodeDecodeError/exit1 with no structuredJSON/zeroPOST at exactimplementatione91.
Proved Hpositivecontrols stay intact: .2sglobaldeadline observed .202/.203, nativebudget3
stopsBafter2calls, accepted-closeA not replayed, realfailedTCPconnects consumeallowance.
Missing checks stay visible, and old reports stay immutable.

## Documentation

Document actual credential bounds, evidence/privacy/identity and output-comparison definitions,
reported-vs-qualified metrics, CLI exit stages and safe examples. Preserve NOT RUN realtarget/
hardware/quality/cache gates and the unresolved certifi policy gate. Update affected context
measurements/hash metadata together only when underlying documents change.
Preserve the original003 boundary: its runtime explicitly authorizes software/tooling and
syntheticHTTP acceptance without live inference. Correct new status text that makes live-target
evidence a prerequisite for closing this software objective. Real qualification remains open
for004/019 and MVP readiness; this neither narrows fullMVP nor adds an unauthorized003live trial.

## Runtime and protected resources

Live authorization: NONE. Pending approvedtarget/corpus/GPUownership andcertifi-only
licenseexception questions have no reply; no authority or exception is inferred.
Owned disposable fixtures/subprocesses and ordinary lightweight tooling/GitHubCI are allowed.
Preserve original sources, agent settings/homes/FIFOs, unrelated services/GPUs and secrets.
No endpoint/model downloads, network source fetch, protected operation or license exception.

## Deferred human adjudication

- Decision: NONE

## Publication and report

Amend PR5, commit exact strategic activation/priorreview unchanged, and publish a concise
immutable report-onlySELF with literal implementation parent. Verify remote publication,
respond exactly once through the existing wrapper and end the bounded nativegoal. No consumed
FIFO reread, competing reader, merge or nextwork selection. Strategy decides whole003 acceptance
or another focused continuation. Baseline419product=159unit+260integration(129gateway+
83native+33transport+15probe), separate41OAP. Commit pre-published
oap/reviews/003-h-review.json unchanged. Keep the report concise: literal identities,
actual changed behavior/commands/counts/CI and remaining limits; reference prior evidence
without reprinting the transcript. Existing interfaces:

```sh
python3 oap/bin/verify_report.py --repo-root /home/janezp/codex-work/slaif-raggedized-helper --runtime /home/janezp/codex-supervision/slaif-raggedized-helper/runtime.json --identifier 003-i
bash /home/janezp/codex-supervision/slaif-raggedized-helper/send-response.sh --identifier 003-i
```

The sole externalcontrolwrapper consumes notification before freshstartup. Preserve selected
model/provider/profile. End this bounded nativegoal after truthful report/response; strategy
alone accepts, selects continuation or merges. PARTIAL/BLOCKED/FAILED is valid evidence,
never a scope waiver or reason to choose nextwork.
