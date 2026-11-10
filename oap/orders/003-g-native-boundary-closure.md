# OAP Work Order — 003-g

Status: FINAL
Identifier: 003-g
PR mode: AMEND_EXISTING_PR
Branch: oap/003-generator-adapters-and-cache-probes
Base commit: 93b43177f4dcd0b28ef2c5ed33a049f83217f152
PR number: 5
Expected active: 003-f
Provenance: E independent native HTTP boundary experiments; A13 A15 A22; unmet003-f criteria2/3
Architecture SHA256: 4b41905396a3838269fd6cf372614cd23cb2c3b6a37be09f29ed752803c0983a
Governance SHA256: 2dce38b0e965843263d8d2c7bb69acb2d3737224d30b6d212eed9177bd390b5a

## Objective

Close two demonstrated native boundary defects before qualification-probe composition.
This is a focused correction within objective003/PR5; preserve the accepted metric meanings,
all prior gateway/transport/native behavior and the full original003 scope. No merge here.

## Dependencies and current state

Verified2026-11-10: final003-f reportSELF5960ea188b3493ff4964ba584ca13ee3a1f49142,
soleimplementationparentdb7443fd64b3207a208348ea178c1600e6ff90f4; report-onlydiff,
reportSHA25653076b74b2b9f744e4415d4eef53fd4c746ceee013a1580dbda10dc39f226f7d.
UniquePR5OPEN/originalbranch/base/main93b43177f4dcd0b28ef2c5ed33a049f83217f152.
ImplementationCI42781488186/finalCI42782276864 all5SUCCESS. Exactresponse consumed
at2026-11-10T08:24:18.414082+00:00; no reread. Worktree clean before newstrategicreview.
Priorboundedcodinggoalcleared/panequiescent; selectedprofile unchanged. ReportCOMPLETE
isnotstrategicacceptance: final003-f reviewCONTINUE, twoexistingcontractdefects remain.
At implementationdb7443fd64b3207a208348ea178c1600e6ff90f4 all5CI passed, and the
independent eight-vector owned-HTTP experiment still demonstrates the two failures below.
The report-only publication preserves that exact implementation source; both failures are current.
Reference: /tmp/raggedized003-native-boundaries-review.py and
audit/003-f-incremental-review.md in the strategic home. Existing earlier oracles remain unchanged.

## Allowed paths and scope

Focused model_clients/direct.py timing arithmetic and native required-capability admission;
native mapping/unit and actualHTTP regression tests; directly affected generator docs and
governance measurements only if changed. Unchanged strategic activation/priorreview/report.
No dependencies, broad transport rewrite, new capability, architecture/source change or
qualification-probe runner in this correction.

## Non-goals

No live model/service/GPU/corpus work; no model/profile/provider replacement; no numeric
advance, separate PR, merge, release, tag or deploy. Full003 probe/CLI scope remains required.

## Acceptance criteria

1. Safe arithmetic follows safe input conversion. Both reported phase times1e308ms are
   individually finite; each converts to1e305seconds, but their millisecond sum overflows
   before division in current code. No ValidationError/OverflowError or invalid nonfinite
   result may escape generate(). Compute a finite derived total safely, or explicitly
   withhold an unrepresentable derived measure; retain individually valid phase values.
   Keep TTFT unavailable, known zeros, missing-value behavior and narrow boundary handling.
   Do not impose an arbitrary physical-time cutoff or whole-function exception blanket.
2. Honor explicit minimum native capabilities as well as actual input shape. A valid
   GeneratorRequest with model declaringTEXT/JSON_MODE, required_capabilities={JSON_MODE},
   response_format=None and json_grammar_tested=False currently makes both HTTP calls.
   Refuse that unqualified requirement before template/completion dispatch. Model declaration
   alone cannot prove serving-build support. Preserve ordinaryTEXT/noformat success and
   qualified positive controls; requiring a capability alone need not invent an output format.
   Keep existing vision/stream/cache/slot/purpose and operator-budget gates intact.
3. Add meaningful mapping and realHTTP regressions for finite phase-sum overflow and
   constructor-validated requiredJSON-only input. Assert typed safe outcome/available finite
   measurements and exact zero refused dispatch, plus qualified and ordinaryTEXT positive
   controls. Retain all five original native vectors and bothphasezero positive control.
4. All affected unit/integration, complete product/OAP suites, lint, schemas/governance and
   every current-head CI job pass. No weaker oracle or historical report mutation.

## Verification and negative evidence

Use only owned loopback HTTP fixtures. Run the independent eight-vector script against the
final implementation, inspect outcomes/counts/metric meanings, and preserve its original
cases. A green self-consistent fixture suite is insufficient if either actual observation
still fails. Report exact current test counts and command outcomes, never future CI claims.

## Documentation

Update focused metric-boundary/admission text if needed. Preserve unavailable live runtime,
real cache/quality/qualification and distribution/license gates; no model-performance claims.
Refresh affected measured read set and hashes together only when underlying files change.

## Runtime and protected resources

Live authorization: NONE. Ordinary lightweight development, ownedHTTP fixtures and GitHub CI
are allowed. Preserve source originals, other services/GPUs/secrets and selected agent
settings. No downloads, protected operations or new license exception.

## Deferred human adjudication

- Decision: NONE

## Publication and report

Amend uniquePR5. Commit unchanged strategic activation and003-f review. Publish immutable
report-onlySELF with literal implementation parent, verify remote publication and signal
exactly once using the existing wrappers. End bounded coding goal at truthful report/response;
strategy alone accepts/selects continuation. No competing reader or replay of consumedFIFO.
Baseline368product=236integration(125gateway+33transport+78native)+132unit, separate41OAP.
Commit exactprepublished oap/reviews/003-f-review.json unchanged. Interfaces:

```sh
python3 oap/bin/verify_report.py --repo-root /home/janezp/codex-work/slaif-raggedized-helper --runtime /home/janezp/codex-supervision/slaif-raggedized-helper/runtime.json --identifier 003-g
bash /home/janezp/codex-supervision/slaif-raggedized-helper/send-response.sh --identifier 003-g
```

The sole externalcontrolwrapper consumes notification before freshstartup. Do not reread
control, create anotherreader or selectnextwork. Preserve selectedmodel/provider/profile.
