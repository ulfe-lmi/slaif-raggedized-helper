# OAP Work Order — 006-c

Status: FINAL
Identifier: 006-c
PR mode: AMEND_EXISTING_PR
Branch: oap/006-native-extraction-and-chunking
Base commit: 435e4c13c5dee83d4578e8ba1cd68eb1d781ac25
PR number: 8
Expected active: 006-b
Provenance: H activated fullarchitectureMVP/parallel mandate; A architecture8.1/8.2/9.3/9.4/20.2; E baseline1025callrefusal andmissingdurable/sourcebindings; I independentlyreviewedacceptedexactlocalcomponents
Architecture SHA256: 4b41905396a3838269fd6cf372614cd23cb2c3b6a37be09f29ed752803c0983a
Governance SHA256: fadab8544f077f94552affb43b3e5ec0698f066a7f915ecf394708e713f7d2b4

## Objective

Integrate exactly THREE reviewed local component histories, repair the current canonical capacity
expectations, and prove actual native records survive private durable storage and fresh revalidation.
Continue PR8. This foundation slice does NOT implement/claim the full typed ingestionbundle loader,
PDFsemanticvaluecomposition or installedprivatechunkCLI; those remain requiredfollowing006work.
No numeric007 or whole006merge from thisslice.

## Dependencies and current state

006b FINAL Root acceptance /home/janezp/codex-supervision/slaif-raggedized-helper/audit/006-b-review.json SHA71d2083b6f87d316cc3e40ebea4955d21d74f2eacf7ab96a860ab2f9ee44292e.
Exactreport435e4c13c5dee83d4578e8ba1cd68eb1d781ac25, soleimplc2d589c23dab73b6f34bb75ee588db179b1efbb7,
reportSHAd4ae5072526898fc4f8304e894ef98040a145b07de05418a97a606cbb6c28ea4. Implementation43065337340
andreport43068421430 ALL5jobs/stepsSUCCESS, remote/main4977186d3ddbd2259f78590b29c0364fe26eb1fb,
uniqueOPENPR8/base main/noautomerge/zeroreviewthreads; cleanreporthead. Root fullreport/diff/
408testlines read,48actualbaseline+4combinedtests PASS, remote report bytes independently fetched.
Baselineusabilitylimit retained; no whole006acceptance. Prior006bboundedgoal actuallyachieved/
quiet afterresponse; no needclear/replay. No codingpostresponseconsumers.

Root component index /home/janezp/codex-supervision/slaif-raggedized-helper/audit/006-c-components.json SHA9238de5cd3b06b841a19f469e4e6686c6e13c29d2fd5cc30d8279dc364fc3e17 is exact ordered integration authority and expectedsourceblobs.
Read thisindex plus actual API contracts, not whole priorbooks/reports/sourcehistory. Root already
reviewed candidate implementation source; no repeat audit of all inheritedhistory is needed.
Ordered LOCAL --no-ff merges (preserve full histories):
1. nativequeryA 0761f6de94cc388ccfd71042986f13d0fa90db4f (includes accepted efficiencyA/scaleC andquerydelta;
   reportSHA9b35d40efc1a0aa9b611a32f46475b79b9ce0d88d598ce0215a5f9f30d083efc).
2. sourceTextA 1b05f3647ac3ca83593bc1f1ca2e869ebad4826f (includes acceptedJSONLA/receiptC;
   reportSHA7dcef7bf6b83e866f99a6cc28bb01b887b93aaf74c1b43dfe4091cc4c93837f9).
3. derivedStoreC f2a2cedc80286cb114ee87db83e674d901fccd74 (opaquecontainer, sourceidenticalpeer-reviewedB;
   reportSHA056e42ad9b28c02e62791c40524b8c5f17d9280e26336ef55aa000e3245ce7c0).
All accepted source modules must match index blobs after integration. CorrectedPDFparser/worker
must match index unchanged. Firstpreliminary reporthead+nativequeryforecast34fe24aad490c86e3c93054dbea0b1d12362ec07
was clean beforecurrentreport; recompute EVERYactualparent afterroundstart and EACHmerge.

## Allowed paths and scope

Commit exact active/order plus copy Rootreview to oap/reviews/006-b-review.json and componentindex
unchanged to oap/reviews/006-c-components.json as roundstart. Thenthreeexactlocalmerges in order,
verify actualparentpairs/merge-tree equality. No reset/clean/stash/switch/provenance-erasingpick.
Unexpectedconflict/sourceblobchange requires contained evidence, no arbitraryacceptedsourcepatch.
Only new edits: existing tests/integration/test_native_extraction_counts.py; docs/ingestion.md;
README.md/STATUS.md/TESTING.md/docs/UNCERTAINTIES.md; optional detailed
 docs/benchmarks/ingestion-count-storage.md; oap/governance/CONTEXT-BUDGET.md and MANIFEST.json
for affectedmeasurements. Existing detailedqualification-testing.md remainsbyte-identical. No app
source edits expected/authorized, no newworkflow/dependency/lock/law/helper/client/model changes.
No unreviewedPDFsource/fullbundle candidates inthisslice.

## Non-goals

No full typedbundle/PDFsemanticcomposition/installedprivatechunkCLI inthisslice; no embeddings/
snapshots/retrieval/authAPI/vision/model inference/hardware qualification, numeric007, whole006
merge, licenseexception/deployment/release or unrelatedrefactor. Fullscope remainsrequired.

## Acceptance criteria

1. Threeexactmerges/indexblobs/provenance and unchangedcorrectedPDF verified. Currentnative:
   native default15s/legacyexplicitdefault5s/max15s,16384calls/32MBinput/4MBoutput; allotherhard
   worker/policy/callback caps retained. Native perbuild reuse/source/cuts/counts unaffected.
   Legacy/interim policyv2 exactUTF8querydigest removesrawquery4096limit; finalnativev1 identity
   andreceiptfingerprints unchanged. Inheritedtests includeactual10kASCII/Unicodequery successes,
   changed samecountqueryID, overlength/overreserve refusal. No universalcapacity/throughputclaim.
2. Update existing combinedtest: replace staleattempt1025negative with actual7876Bprocedure and
   9269Btable positive journeys atcurrentcaps; currenthardquota negative standaloneSession can
   seedcalls16384andassertnextcount refuses/ownedchildcleanup, rather than tokenizehugefixture.
   Tighten existing assert_exact_block_coverage helper to fullintervalunion/no gap, notonlymaxend.
   Retain literal/structure/realPDF/native3roles/independentrecounts/identity/budgets/overlap/tail/
   cross-source/rights/version/partialvisual cases. No testweakened to accommodatea failure.
3. Extend SAMEcombinedtest with actual structuredtextrecords -> sourcevalidator+receiptvalidator
   -> derivedStore.publish opaquecontainer -> close -> FRESHStore/newprocess load -> reverified
   actualOriginalStore/sourcevalidator+receiptvalidator/Registry/neighbors. Check immutablebytes,
   fullsourceunion/tail/roles/IDs/scopes, unchangedoriginal/retryidempotency and corruptmember or
   alteredoriginal refusal. Fixedowned subprocess fixture permitted, no source-definedexecutable.
   Label this componentstorage composition; successful opaqueStore.load is NOTtrustedcomplete
   native ingestionbundle. Do not invent missingfullvalue/loader/privateCLI productAPI.
4. Run local focused existingcombined and affected source/receipt/store/native tests afterlastedit,
   pluslint/diff/governance/console. Fullunits/integration/OAP/console/doctor on BOTHproduct CI
   remainmandatory: actualexactimplementation-headALL5SUCCESS beforeimmutableSELFreport.
   Do NOT duplicate wholelocal suites alreadyexecutedbycurrentCI withoutnewfailure/concern;
   collectioncounts maybe reportedascollection, neverunexecutedtestsasPASS. BackendabsenceFAILS,
   no skip/fallback; requirednative/PDF pinnedsetup/read-onlyrunner/actionpinsunchanged.
5. Docs currentboundaries/defaults/queryidentity/nativeobservedvsprovided/sourcevsopaquecontainer,
   private sourceverification/currentservingauth distinction, contraryscale timings and remaining
   fullbundle/PDF/loader/privateCLI. Keep routine<=50000UTF8bytes: consolidate TESTINGsummary
   with details innewingestion-count-storage.md ifneeded; update context+manifest together,
   exactmodeltokensUNMEASURED. No futureproof/model/license/ICA/MVP claims.

## Verification and negative evidence

Actual ownedUnicode/technical/source fixtures with real approved private isolatednative/PDF
backends, fullspanunion/tail/sourceintegrity/privatefreshstore/revision-rights binding. Retain
existingsource/hash/identity/count/deadline/cleanup/corruption and sourcegrant denial regressions.
Cmanualauthor10.79s/peer13.81s complete andRoot15.17s deadline refusal ALLretained; this isbounded
softwarewithhonestdegradation, targethost/model performance019OPEN, notextraquota authority.
No syntheticendpoint/model/VRAM/license or unauthorizedpassages invented.

## Documentation

Succinctcurrentprotocol/uncertainty/remainingwork only; current docs supersede baseline1024call
limit while preservinghistoricalobservations. No repeatedwholehistory. Detailedoriginalsource/
architecture/qualification docs remain unchanged. Copy Root bytesunchanged andnevereditreports.

## Runtime and protected resources

No target/GPU/service/credentials/privatecorpus/legalexception/release/deployauthority. Existing
ordinaryCPU/DEV/ownedfixtures and approvedprivatebackends only. Native env andPDFenv from006b
remainvalid. No newdownloadrequiredexcept alreadyrevieweddisposableCIprovisioning. Preserve
humanQwen3.8-27B/A100Q8/xhigh andallclientsettings. No nestedagents or selfassignednextobjective.

## Deferred human adjudication

- Decision: NONE

## Publication and report

AmendPR8only. Freshordinaryorder/source/index tools and roundstart first; strategy may send ONE
boundedoperationalgoal afteractualtools, never selfreplay. Finish finite scope andallrequiredCI,
shortGit subjects<=72chars. Report-only SELF soleparentimplementation, concise<=6000UTF8bytes:
requiredidentityfields,actualmergeheads/trees,testcommands/exits/counts,implementationCIrun+5job
results,docs/remainingboundaries/DHA NONE. Do notrepeat fullhistory/long commitmessage/prooftext.
Verifyremotehead/reportbytes/topology, respondONCE, markboundedgoalcompleteandidle. No postresponse
polls/readers/audits/nextwork; Rootownscontinuation/devmerge. No mainmerge/tag/release/deploy.
