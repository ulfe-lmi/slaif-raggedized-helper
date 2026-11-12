# One-batch durable GPU producer — strategic D0 contract

Status: FINAL DESIGN. Frozen prerequisite GPUplan fb97/reportd100689ef5582a79a29d78e51a4c5ce860d1552c
and fresh affected peerdeeb independently reconciled; activation only by finalized work order. Provenance H active MVP; A8.4/11.2/19; I existing CPU
reference producer/journal/typed batch store, owned GPU parent, bridge4554 and source-plan
contract; E the required GPU path still has no source-bound durable completion/reuse wrapper.
DHA expected NONE; admit any actual future dilemma separately rather than inventing CRITICAL.

One bounded batch, no corpus scheduler/retry/controller/service transition. Candidate module
gpu_embedding_producer.py and new tests/API/design/order only. All predecessors remain exact.
API produce(original_store, bundle_metadata_bytes, bundle_members, chunk_ids, manifest_bytes,
artifact_root, embedding_definition, tokenizer_definition, expected_inventory_id, runtime,
prepared_launch, store, journal_root, authorization_provider, *, purpose="prepare",
representation_policy=None, batch_policy=None) follows actual gpu_embedding_plan.build inputs.
Require exact derived Store, bounded journal root and REQUIRED trusted internal provider. Borrow actual PreparedLaunch, its mode
operation reservation and stores. Own the newly constructed actual GPU parent, bridge/native
session and per-job journal lease. Caller retains preparation/reservation throughout own drain.
Do not accept a supplied worker/session/whole execution provider/Result as proof of execution.

Current authorization provider semantics follow the CPU reference: provider(actual canonical
plan bytes, boundary) must freshly verify permission for every source row/purpose and return
bare64hex epoch or refuse. There is no permissive default or caller-supplied epoch/receipt.
before_model, before_encode, before_publish, before_complete and before_reuse boundaries
must use one unchanged epoch per call. Provider is trusted application wiring, never a reader
request/model-provided callback. These finite fake-provider tests do NOT implement/qualify
the future principal/current policy store, processing rights, licensing or revocation.
Caller must establish permission before invoking operator planning/native source counting.

## Source plan and job transaction

1. Strict bounded inputs first; fresh actual GPU source-plan build, canonical plan/spec and
   full predicted GPU execution plus detached native record. No GPU parent/model starts.
   Obtain current authorization before any possible GPU model construction. Own actual
   journal.Journal(root).own(plan_bytes), preserving pending claim/cleanup uncertainty.
2. Read current durable state. Only fresh PENDING or verified COMPLETE is eligible. Refuse
   CLAIMED/RUNNING/UNKNOWN_COMPLETION/FAILED/CANCELLED; no owner stealing, stale timeout
   interpretation, automatic repair/retry or exactly-once inference promise.
3. COMPLETE reuse: rebuild fresh source/contract, exact equality, integrity-load actual stored
   batch metadata and compare every plan field/dependency/row/codec identity. Actual journal
   verified_output and typed batch load must both succeed. Recheck before_reuse rights/epoch.
   Start no GPU parent/model/bridge. Return fresh immutable verified data and reused=True.
4. PENDING: new actual attempt, monotonic-valid timestamps, CLAIMED then RUNNING with actual
   lease owner through existing journal API. No invented lease/owner/event object. Retain the
   actual GPUEmbeddingWorker allocated by class.__new__ BEFORE fallible class.__init__(prepared).
   Parent already owns fixed namespace/wire/device-lease/confirmed-drain machinery; do not
   reimplement it, start arbitrary commands or infer GPU vacancy from exit/EOF/returncode.
5. Retain actual bridge GPUTextEmbeddingSession before fallible initialization. It borrows
   producer-owned parent and owns independent native tokenizer. Independently compare actual
   observed parent and actual session contract to prediction BEFORE text dispatch. The bridge
   currently exposes its actual admitted _plan via a retained owner record, not public session
   execution properties: inspect finalized exact API. If private coupling is used, use known
   actual class _acquire/_check on the actual registered instance, snapshot the retained plan
   while holding its retained nonblocking lock, and release that SAME captured lock. Never
   substitute a caller DTO/property/callback or claim such private coupling is a public API.
   If a public observation seam is necessary, split it into a separately reviewed prerequisite.
6. Fresh source-plan rebuild and current authorization before_encode; require exact predicted
   bytes/native bytes/space/definition/intended GPU identity and canonical source plan unchanged.
   Dispatch through actual guarded GPUTextEmbeddingSession.encode on retained actual session,
   rather than instance-supplied method callback (the b457 concrete faults govern this boundary).
   Mark dispatch attempted BEFORE the actual call; failure thereafter may be UNKNOWN_COMPLETION.
7. Validate exact EncodedBatch type and all full execution/native/intended/space/definition
   fields; independently validate full detached records and exact predicted equality. Match
   ordered receipts to plan rows, input digests/token counts, native artifact/backend/revision/
   role/preprocessing, distinct actual nonces/IDs and actual receipt guard. Validate normalized
   FP32 immutable payload/cardinality/hash/policy and actual row bytes. Encode typed NPY using
   existing batch-store fixed codec without changing values. No supplied Result/receipt data
   alone proves that actual method ran; actual-owner dispatch and checks remain necessary.
8. Drain own bridge/native and actual GPU parent BEFORE publishing/completing output. Both
   must be confirmed drained by their actual owned cleanup paths; retain resources/journal if
   either remains pending. PreparedLaunch/reservation/stores are borrowed and never closed by
   this producer. Physical device vacancy, online restoration and live resource qualification
   remain caller/controller gates, not consequences of fake namespace or parent close.
9. Rebuild source/contract and authorize before_publish; use existing actual batch metadata
   plan fields/rows/codec/encoded container hashes. Publish typed batch, freshly load it and
   validate all metadata/vector bindings. Rebuild and authorize before_complete; append actual
   COMPLETE with real output ref and metadata digest, then fresh journal and typed-store
   verification before return. Never record COMPLETE first, or delete published orphan output
   to conceal failure. Output ref is prefixed; complete GPU dependency remains bare64hex.

Result is frozen job_id/output_ref/metadata/fresh validated batch/full execution/native bytes/
execution fingerprint/reused flag. No DTO is authority or full neural/rights/Ready proof.
Full execution record and native declarations in result must not be confused with stored batch
metadata, which currently stores their fingerprint: do not claim it persists fields absent from
that actual closed format. A separately designed archival artifact may be needed later.

## Failure and resource ownership

Catch only for finite owned reconciliation/cleanup, preserving original non-Exception object;
new cleanup/reconciliation interruption outranks an ordinary error. Ordinary refusal is
content-free and retains a reachable cleanup owner when needed. Parent and session allocations
must survive pre-return constructor failures through actual local retention/strong registries,
not a factory DTO or garbage collection. Original child/helper pre-return fixes remain exact.

An exception around journal atomic update does not prove it failed: reread durable state and
never replace committed COMPLETE with failure. CLAIMED before dispatch may become CANCELLED;
RUNNING before dispatch may become FAILED; attempted encode uncertain outcome becomes
UNKNOWN_COMPLETION. Preserve reconciliation uncertainty rather than falsely declaring a known
terminal outcome. Lease/descriptor acquisition failure may occur before a handle returns;
retain actual sticky uncertainty and never retry an uncertain raw descriptor number.

Attempt safe independent cleanup of own native and own GPU parent even if the other fails;
do not strand GPU work merely because native cleanup raised. Journal lease remains retained
until all drainable own neural/native resources are actually drained; recorded descriptor
uncertainty is not evidence that a lock remains held. Retry only the retained actual owner's
supported close, never numeric PID/FD guessing. Closed/forked borrowers cannot initialize,
revive, reap, signal or release creator resources. No unknown owner/process signal, borrowed
reservation release, global process scan/kill or hidden controller/profile operation.

## Finite acceptance to expand against actual prerequisite

Use real private original/derived/journal stores, actual mode-operation reservation and pinned
PreparedLaunch, actual parent/bridge/native workers with existing private copied GPU fake entry
and null device pins. Neural fake input/output is explicitly synthetic; no Torch/Tensor/model/
driver/physical GPU. One actual successful batch, source/receipt/normalized-vector equality,
output-before-COMPLETE, exact durable trace/spec and COMPLETE reuse without GPU parent startup.
Actual claim collision/refused unfinished states, missing/tampered output or metadata/source,
changed contract/current authorization epoch at named boundaries and after publication,
wrong receipt/result binding, interruption before/after dispatch/commit and actual pre-return
acquisition failures. Pending own resources/lease remain reachable; confirmed drain restores
borrowed preparation/reservation usability. Original causal control must target one actual
plan-to-output/journal binding with other actual stores/owner checks intact, not whole proof
provider replacement. Resource faults and ordinary-vs-interruption priority deserve distinct
bounded cases; no huge aggregate invokes a known30CPU failure or relaxed caps.

Use existing per-invocation1GiBAS/30CPU/120wall/five threads1/no bytecode/native0.21/GPUfake
setup. Fresh finite peer before canonical integration; current canonical source/docs/CI/report
gates mandatory. Current policy implementation, bulk resume/scheduling/controller/vacancy/
restore, real hardware/model/FP16 parity/performance/memory/security/license/heldout/visual/
ICA/MVP/release/deployment remain open. Do not jump canonical objectives or infer live runtime permission from product code.

Final prerequisite/source reconciliation: GPUplan d100/implementationfb97 and bridge a9a5/4554
are frozen clean exact reports, Root source/report reviews and peerdeeb/170d verified. Current
canonical007-l unit fixture repair is independent; all production native/parent bytes stay exact.
No preparation merge needed for this leaf; base is exact d100 report.

If actual success plus COMPLETE reuse would exceed one30CPU test invocation, split into two
explicitly owned bounded subprocesses with fresh creator-owned stores/reservation/preparation
in each and the same owned temporary durable files. Each child has the same caps; parent only
waits/reaps its own children. This also proves stable job identity across new startup nonce/PID/
plan_id. Never pass inherited creator-owned objects as authority, relax caps, fake successful
model execution or claim manually seeded typed output demonstrates neural origin. Other reuse
corruption negatives may use real typed/journal fixtures and must disclose their provenance.

## Root amendment 1 — producer owns preparation; existing parent consumes it

Status: FINAL, SAME PAR-007-GPU-PRODUCER-A, branch/base/context. DHA NONE.
Original order and contract925ed9 remain immutable history. This Root amendment overrides
ALL references in that contract to a borrowed caller-supplied PreparedLaunch remaining usable
after parent drain. Actual documented GPUEmbeddingWorker CONSUMES PreparedLaunch and its
successful _close_owned closes it. Parent, launch, GPU plan and bridge remain byte-identical.
No guard bypass, private drain-without-close, predecessor patch or fabricated fresh prediction.

Root reviewed blocker.json and actual parent line685/PreparedLaunch.close/revalidate/GPUplan.
The conflict was Root's composition assumption, not an existing parent bug. Resolve it by
owning preparation and honestly rebuilding a fresh actual one after drain, not by weakening
fresh validation or retaining a closed object as live authority. Preserve all preliminary
uncommitted producer helpers/tests; adapt same unfinished order. No reset/new control/suffix.

### Revised exact input and ownership contract

Provide a frozen LaunchInputs DATA class in the NEW producer module with exactly source_root,
staging_root, runtime_root, packages_root, lease_root, device, drivers, resource, wire_policy.
Five roots are canonical absolute strings within existing path bounds; device is exact existing
DevicePlan, drivers exact tuple of existing DriverFile, resource exact ResourcePolicy and
wire_policy exact wire.Policy. The configuration is trusted INTERNAL operator input, not HTTP
request commands or a permission DTO. Snapshot/revalidate its scalar/dataclass values on each
use; frozen-object mutation cannot silently change a running call. Reject unknown/invalid
types/fields/bounds before filesystem work. Use actual prepare to validate all operational
inputs, current reservation and pinned files; no factory/callback substitutes for preparation.

produce(original_store,bundle_metadata_bytes,bundle_members,chunk_ids,manifest_bytes,
artifact_root,embedding_definition,tokenizer_definition,expected_inventory_id,runtime,
launch_inputs,reservation,store,journal_root,authorization_provider,*,purpose='prepare',
representation_policy=None,batch_policy=None) replaces the old prepared_launch argument
with launch_inputs and reservation. Native runtime remains independent from GPU runtime_root.
The source manifest/definition/tokenizer/inventory/artifact_root come ONLY from source arguments
and are passed consistently to actual gpu_worker_launch.prepare, not duplicated config fields.

Caller owns actual mode-operation reservation and original/derived stores. Producer owns ALL
actual PreparedLaunch objects it creates plus its actual parent/bridge/native/journal lease.
It NEVER closes/releases the caller's reservation or stores. Parent normally consumes/closes
the first owned preparation; producer must reconcile actual pending state if parent close fails.
No caller-supplied worker/session/prepared/prediction/authorization epoch becomes proof.

### Concrete preparation phases and freshness

1. Existing strict source scalar preflight plus launch-input/reservation admission first.
   Actual prepare uses exact source_root/staging_root/runtime_root/packages_root/lease_root,
   source artifact_root/manifest/definition/tokenizer/inventory and config device/drivers/
   resource/wire_policy/reservation. It starts no GPU parent/model. Retain actual returned
   preparation and any real pending/unknown helper cleanup owner on failure; no discarded
   pre-return resource or unsupported numeric descriptor retry.
2. Build actual gpu_embedding_plan against initial owned preparation A, authorize, own job
   journal, handle PENDING/COMPLETE exactly as original design. On PENDING construct actual
   parent from A; the parent now owns A's active lifetime. Capture/observe actual bridge and
   compare full prediction before source dispatch; all existing guards/authorization/receipts/
   FP32/output/journal invariants stay exact. No real framework/GPU in this leaf's tests.
3. After encoded result, drain actual own native session and actual parent. Parent success
   closes A as designed. Treat A as consumed, not reusable. A pending parent/preparation is
   not a drain proof; retain actual owner and do not publish/complete yet. Attempt safe
   independent own cleanup even if the other resource fails, preserving error priority.
4. Create a SECOND fresh actual preparation B using the SAME admitted source/config values
   and SAME caller-held actual reservation. No GPU parent/model starts for B. This creates
   fresh pins/capsule and validates current artifacts/code/runtime/device inputs after drain.
   Rebuild GPUplan with B before_publish and before_complete, requiring EXACT same canonical
   plan/spec/texts/full execution/native records and identities as initial A. Startup nonce,
   PID/FD/capsule path/plan_id naturally differ and must not contaminate stable identities;
   never ignore a real stable fingerprint difference to manufacture equality.
5. Publish/load actual typed batch after before_publish/current rights; rebuild/re-authorize
   before_complete with B. Close/drain B's owned pins/capsule BEFORE appending COMPLETE;
   no need for a GPU model or live parent just to validate B. Then append/verify COMPLETE
   and release job lease with original uncertainty semantics. Failure during B close leaves
   explicit failure/unknown and retained actual cleanup owner, possibly an immutable orphan;
   do not claim COMPLETE or closed resources from attempted close alone.
6. COMPLETE reuse needs only initial owned preparation A for fresh prediction/source checks;
   create NO GPU parent/bridge/model. Verify actual journal/output/current epoch, then close
   owned A before successful return. Existing COMPLETE never downgraded on later cleanup/
   reconciliation failure. Borrowed reservation/stores remain usable; no borrowed preparation
   usability assertion remains because there is no borrowed preparation input anymore.

Returned full record fields remain data distinct from actually stored closed batch metadata,
which only persists the execution fingerprint. All current-policy-provider/rights/typed-store/
unknown-completion/no-stale-steal/no-auto-retry/non-Exception/sticky-FD rules remain. If any
actual helper drops an owned cleanup handle and prevents the required safe composition,
report the precise concrete counterexample; do not fake proof or patch immutable prerequisites.

### Meaningful bounded proof and reporting

Demonstrate actual parent consumption of A, fresh actual B with different ephemeral startup
but identical stable prediction/job plan, real fresh rechecks after drain, no second GPU parent
startup for validation, successful typed publication-before-COMPLETE and COMPLETE reuse without
GPU model. Actual reservation and stores still usable. All named failure/current-epoch/output/
source/constructor/pending-cleanup cases remain; preparation acquisition/close faults retain
real owner/uncertainty. Two bounded subprocesses may prove success then fresh-process reuse
when combined compute would exceed one30CPU invocation; fresh objects per creator, same own
durable files, same per-child caps, no inherited-owner authority or cap waiver.

This one-batch reference may recreate preparation/capsule/model between distinct jobs; it is
not a qualified efficient resident multi-batch scheduler/controller. Measure/qualify or evolve
that later; no invented throughput, physical vacancy, rights/license, FP16 quality or MVP claim.

Keep EXACT same six allowed implementation paths and original order bytes; no helper manifest/
coordinator/scope refresh or extra implementation file. Copy design as EXACT concatenation of
original contracts/gpu-embedding-producer-v1.md bytes THEN this entire Root amendment bytes
into existing docs/parallel/gpu-embedding-producer-design.md. Root will verify prefix/addendum
hashes. API docs/report explicitly cite this amendment and real consumed-owned preparation
semantics. No report/response before ordinary implementation checkpoint and Root REPORT.

## Root amendment 2 — measured outer synthetic test-driver CPU budget

Status: FINAL, SAME PAR-007-GPU-PRODUCER-A/context/base/partial six files. DHA NONE.
This changes only the OUTER TEST DRIVER budget for the exact full-fresh synthetic positive
case, not any product/native/GPU worker policy, public API, source check or protected runtime.
Original30CPU failed attempts remain failures. Do not claim they passed after this amendment.

Evidence: actual fixture generation moved to a separate capped process (1.63user+0.15system),
then a fresh creator-owned produce invocation still reached before_encode and exited137 at
28.26user+1.80system/30.80wall/~79MiB peak RSS, before publication. A separately controlled
before_encode denial measured parent process_time15.744s since immediately before produce,
with actual source/parent/native guards and confirmed cleanup. Source review shows mandatory
fresh preparation/plan/bridge observations and before_publish/before_complete rebuilds remain.
Splitting fixture work did not fix the outer cap; splitting midway through the actual call
would abandon creator ownership and would not prove this composition. No repeated killed
aggregate, fake producer, skipped validation, worker-cap increase or cached authority is allowed.

Root ordinary D0 choice under human autonomous disposable-test authority: permit ONE exact
full-fresh actual synthetic producer positive invocation with outer prlimit CPU60 instead of30.
Keep outerAS1073741824, timeout120wall, five threads1, no bytecode/privatebasetemp and current
owned fake GPU/null/syntheticnative fixtures. All ACTUAL product worker/native subprocess
CPU30/lifetime/memory/thread/device/namespace/source/policy guards remain unchanged. The outer
pytest driver's prior30 was a work-order testing budget, not a human/product invariant.
Reuse and previously bounded early-fault proofs remain CPU30. No new install/model/framework/
Tensor/GPU/driver/service/unknown process/network/data authority. Root will review any further
late-fault budget need separately; this is not blanket permission to increase budgets.

Measure actual process_time immediately around the complete produce call, outer user/system/
wall/peakRSS and phase timings. Record synthetic inputs/rowcount/source/full records/output/
COMPLETE, actual owned cleanup, borrowed reservation/store usability and fresh separate-process
COMPLETE reuse. If60 still fails, preserve exact evidence and return actual measured boundary;
do not silently increase again. This is a bounded correctness proof, not an efficiency fix or
latency/throughput/realGPU qualification. The expensive fake-software validation path remains
an explicit performance observation for later measured qualification/optimization.

Producer pre-return cleanup association is STILL a named dependency until the independently
reviewed launch-owner prerequisite is explicitly admitted and the same producer is adapted
under a subsequent exact addendum. A positive normal path on the old helper does not resolve
that failure gate or permit report. Preserve original20units/negative histories and real pending
association blocker. No product/predecessor edits to bypass it.

Keep original six paths/order. Existing design path becomes EXACT concatenation ORIGINAL
contracts/gpu-embedding-producer-v1.md THEN parent-preparation-addendum-1.md THEN this entire
Root amendment. Docs/report state changed OUTER test-only budget and all old failures. No new
control/FIFO/goal/model reset or premature report. Fresh affected peer/current canonical CI
remain mandatory before integration. Strongest counterargument: larger driver budget can hide
expensive checking; mitigation is retained exact measurements, bounded60/120 and unchanged
worker/source safety, with no performance or readiness claim. This is ordinary reversible D0,
not human adjudication debt or a waiver of any source/authorization/ownership invariant.

## Root amendment 3 — consume the independently reviewed preparation-owner prerequisite

Status: FINAL, SAME PAR-007-GPU-PRODUCER-A/base/context/partial six paths. DHA NONE.
H full-MVP/parallel; E original pre-return owner-association blocker and actual6f92 return
interruption; I exact5a1b source/SELFb0ca plus opposite-agent finalcba97e61 and Root source/
return/actualparent/handoff controls. Full normal peer response independently reconciled.
This is local prerequisite admission only, not canonical CI/whole007/MVP acceptance.

Mandatory ONE clean --no-ff preparation merge from original d100689ef5582a79a29d78e51a4c5ce860d1552c
with exact frozen b0ca5a68f8e55667ada5dd7523903b5585cbe0af. Root has refreshed private lane scope
and sole unconsumed response reader BEFORE signaling this amendment; original control/order
bytes remain untouched. Preserve all partial/untracked producer files; no reset/clean/stash/
switch/cherry-pick/history rewrite. If any tracked/untracked merge collision exists STOP that
merge boundary and report facts, never overwrite partial work. Expected merge parents exactly
[d100,b0ca], tree equals actual git merge-tree --write-tree. No edits/resolution to prerequisite.
The implementation's sole parent becomes this exact preparation merge. Immutable SELF report
MUST include preparation_head as literal full40hex. Original base stays d100. No newcontrol.

Frozen source gpu_worker_launch.py SHA256
89230e00f2e4fca3271c4e60f55a487a186d932fdce142ee9525852c9a49d3b3.
All other prerequisites/shared production retain exact d100 bytes. New helper owns actual
preallocated PreparationOwner, optional prepare(preparation_owner=...), readonly prepared,
creator/one-use/actualrecord/busy/fork guards and successful PreparedLaunch handoff. It retains
actual prepared BEFORE handoff and preserves failed capture association without relying on
exception attributes. Default no-capture prepare still has its documented old limitation;
old counterexample is truthful history and is not magically a default-API fix.

### Actual producer adaptation

1. Retain a NEW exact PreparationOwner in produce's operation state BEFORE each fallible
   prepare entry, including A, post-drain B and COMPLETE reuse. Pass that actual object into
   actual prepare; do not create it only inside an unobservable helper and later infer it
   from an exception or global registry. Actual same capture must remain accessible in
   outer operation state on every exception, including hostile non-Exception annotation
   refusal and interruption before a helper/prepare return is assigned.
2. On failed/unassigned return, inspect the actual capture through known class/creator rules.
   If prepared is None use only the actual failed/unused capture's supported close. If its
   prepared property exposes the successfully admitted actual PreparedLaunch, recover that
   SAME object and use existing actual PreparedLaunch.close only when no child was started
   or its actual parent drain is confirmed. Capture.close never independently drains a
   pending handoff. Do not guess by pending-list difference, borrowed object identity,
   arbitrary callback, stale id(error) mapping or fabricated owner/cleanup record.
3. If a real parent remains live/pending, retain it plus A/capture and actual journal lease;
   drain via supported actual parent first. Keep native independent safe cleanup attempts.
   B has no GPU parent by design; capture/prepared failure still retains its exact actual
   resources. Keep journal lease until all KNOWN actual owned native/parent/preparation/
   capture resources are confirmed drained. Merely putting one in an uncertainty list must
   not release a still-live known journal lease. An attempted/uncertain journal close itself
   cannot prove it still holds a lock; never retry an unknown numeric FD or claim vacancy.
4. Preserve original non-Exception priority and strong actual pending cleanup reachability.
   Exception annotations are best effort, not the only association. For a preparation helper
   error, outer operation already has the actual capture; do not use exception-ID side maps
   to identify it. Remove obsolete map code if no longer needed within the NEW module only;
   no predecessor patch. Safe independent cleanup remains attempted even if another fails.
5. A consumed by successfully drained parent remains consumed; B freshly prepares exact same
   current source/config/reservation and must produce same stable actual plan/full records.
   New launch source hash changes expected execution identity versus old d100; recompute all
   actual predictions/jobs. Algorithm preservation is not equality of old fingerprints.
   Do not reuse old failed30/synthetic COMPLETE journal as if source stayed unchanged. Use
   fresh own journal/fixtures for new success, preserve all previous evidence.

### Required affected proof

Actual prepare failure with real retained capsule and cleanup fault now associates exactly
with its preallocated producer capture; safe retry drains it and retains any existing journal
lease until then. Actual return interruption after handoff recovers SAME prepared and cleans
at a no-child boundary; hostile annotation failure still retains actual operation association.
Exercise A and B boundaries meaningfully, actual parent consumption, original interruption,
known pending resource/journal retention and unchanged borrowed reservation/store usability.
One full actual fresh synthetic produce may use OUTER CPU60 per amendment2, all worker30/
AS1GiB/120wall/five threads1/source/rights guards unchanged. Fresh-process COMPLETE reuse30.
Actual source/native/fullrecord/FP32/output-before-COMPLETE/currentepoch/no-stale-steal checks
remain. Record all real commands/phases/CPU/wall/RSS/failures/source hashes; no performance,
realmodel/GPU/license/Ready/ICA/MVP claim. Additional cap increase requires new evidence/Root
choice, not automatic retry. Existing passing unchanged tests need no gratuitous full repeat.

Keep SAME six allowed implementation paths, original order unchanged. Existing design is
EXACT concatenation ORIGINAL gpu-embedding-producer-v1.md THEN parent-preparation-addendum-1.md
THEN test-driver-addendum-2.md THEN this entire amendment3. No new design path. Normal source
checkpoint required at NEW unpublished implementation with sole preparation parent; Root
FIX/REPORT before immutable SELFreport/ONEresponse. Prerequisite source/tests/reports immutable;
never patch them to force producer proof. No new goal/context/model/profile/auth/FIFO control
or replay. Whole canonical007-l remains active; no numeric jump/mainmerge/release authority.

## Root amendment 4 — three exact late-boundary synthetic test drivers

Status: FINAL, SAME PAR-007-GPU-PRODUCER-A/context/preparation/six paths. DHA NONE.
Root read late-boundary-budget-request.json, verified source/test hashes, all three selectors
and full actual _one_batch_scenario fixture/body/faults/assertions. Reported positive reached
before_publish at30.290 processCPU, before_complete34.048 and finished34.064. These phase
measurements explain why the old outer30 cannot exercise the late paths; old failures stay.
Root still independently reviews complete producer/source/positive logs at checkpoint.

Authorize ONLY these THREE additional separate synthetic outer driver invocations CPU60:
 tests/integration/test_gpu_embedding_producer_composition.py::test_epoch_change_before_publish_after_dispatch
 tests/integration/test_gpu_embedding_producer_composition.py::test_epoch_change_before_complete_leaves_orphan
 tests/integration/test_gpu_embedding_producer_composition.py::test_b_close_failure_retains_journal_and_orphan
Each retains AS1073741824, timeout120wall/five threads1/no bytecode/private fresh basetemp;
all actual product/native/GPU workerCPU30/other limits unchanged. Sequential heavy tests,
existing approved native/fake GPU/null fixtures, no real framework/model/GPU/driver. Record
exact commands/phase/process/outer timing/RSS/failures, no throughput qualification. No blanket
budget increase for other tests or subsequent >60 retries. A real failure is evidence, never
skip/xfail/policy bypass. No need repeat unchanged passing predecessor suites.

Expected actual evidence: before_publish changed epoch refuses without output; before_complete
changed epoch retains typed immutable orphan; B close fault before cleanup retains exact real
preparation capture and known journal lease until supported retry after fault removed. Actual
parent/native/source forward and all fresh checks execute; UNKNOWN_COMPLETION stays honest,
no committed COMPLETE overwrite. Returned lease or attempted cleanup alone is not vacancy.
No product control-flow change solely to reduce test work or manufacture passed assertions.

Same six allowed paths/original order and exact38ac45b preparation. Design existing path is
EXACT concatenation ORIGINAL gpu-embedding-producer-v1.md THEN parent-preparation-addendum-1.md,
test-driver-addendum-2.md, capture-prerequisite-addendum-3.md, then this whole amendment4.
Report all budgets/source hashes/failures and fixed scope; normal implementation checkpoint/
RootFIXorREPORT before immutableSELF/ONEresponse. No newgoal/context/model/auth/FIFO replay.
Root D0 rationale: measured actual late paths exceed an arbitrary outer test budget while
worker/source/rights safety stays exact; correctness proof needs those paths. Strongest
counterargument is hidden expensive validation; retain exact measurements and later actual
performance gate. No runtime/product invariant, authority or qualification is waived.
