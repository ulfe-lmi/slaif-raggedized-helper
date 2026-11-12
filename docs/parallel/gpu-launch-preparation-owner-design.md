# Caller-retained GPU preparation cleanup owner

Status: FINAL DESIGN; exact order/live reconciliation required for activation.
H full-MVP/parallel; A8.4/19 ownership and safe independent cleanup; E actual
PAR-007-GPU-PRODUCER-A PREPARATION_PRERETURN_OWNER_ATTRIBUTION blocker and Root
actual counterexample at d100. DHA NONE: known software defect, no policy exception.
This is a separately scoped prerequisite, not producer acceptance or canonical next number.

## Problem and chosen boundary

Actual gpu_worker_launch.prepare constructs _Owner, acquires pins/capsule, and on failure
calls owner.cleanup then _failure. _pending retains the actual object, but the raised fresh
LaunchRefused carries no operation association. Under concurrent preparations the caller
cannot safely infer its owner by diffing a global registry. A producer must retain its own
journal lease until actual resources drain; global scanning, guessed ownership and attempted
cleanup are not proof. Exception attribute injection alone cannot guarantee association for
an arbitrary non-Exception whose attribute mutation fails. Preserve original exception identity.

Add a SMALL preallocated caller-owned PreparationOwner to the SAME launch module and an
OPTIONAL keyword preparation_owner=None to existing prepare. Existing default API/callers,
PreparedLaunch/parent consuming ownership, source/pin/namespace/resource/driver/manifest/
reservation/launch invariants and stable fingerprint derivation remain unchanged. No process
or model starts in preparation. No exception-class/DTO authorization or new dependency.

Caller constructs PreparationOwner BEFORE fallible prepare entry and retains it. Passing
that exact actual owner to prepare associates the operation with its actual internal _Owner
before resource acquisition. The caller therefore has a handle even if preparation/cleanup
raises. Never require a returned object, attached exception attribute, global registry diff,
last-owner heuristic or fabricated cleanup record. The caller cannot supply raw _Owner,
foreign/fake/uninitialized/subclass/mutated owner or arbitrary cleanup callback as authority.
Use a proportionate identity/creator/one-use binding to the actual internal object; do not
copy the entire parent supervision system. A small actual registry may hold the binding
rather than trusting caller-rebindable attributes. Ordinary Python allocation/interruption
limits must be documented honestly; no claim of atomicity across every kernel interruption.

## Ownership and public API

PreparationOwner() establishes actual creator PID and one unused operation slot with its
actual internal cleanup owner. `pending` observes that actual owner's remaining/unknown
resources, not a cached Boolean supplied by the caller. `close()` is the supported creator-
only safe cleanup entry for UNUSED or FAILED preparation. It attempts safe independent
cleanup, preserves selected non-Exception identity/priority, raises content-free LaunchRefused
on ordinary failure/remaining uncertainty and never retries an uncertain numeric FD.
The object stays reachable whenever actual pending or unknown state remains. Once drained,
close is idempotent; prepare cannot reuse a closed or previously claimed slot.

One actual slot is usable for one invocation only. Reserve/claim it before resource effects;
reject duplicate/concurrent/reentrant use and forked borrowers without touching its resources.
Cleanup cannot race an in-flight preparation: refuse busy safely, retain the real owner and
let the actual operation unwind. A small nonblocking guard is acceptable; no unbounded wait.
Reject altered coupling/forged initialization before acquisition/close, without closing another
operation's owner. Do not turn class-instance attributes into arbitrary callback dispatch.

On successful prepare the SAME actual _Owner transfers to the returned actual PreparedLaunch,
whose existing close/parent-consumption semantics remain authoritative. The preallocated
PreparationOwner remains an observation/association record; its close MUST refuse to drain
resources handed off to a live successful PreparedLaunch. The caller closes/drains through
actual parent/PreparedLaunch after the appropriate child boundary. It is never a second
independent right to close model mount pins while the parent runs. After confirmed existing
PreparedLaunch close, the capture can observe drained state; no reservation/store is owned.

On failure before a PreparedLaunch is returned, automatic existing cleanup still runs. The
preallocated record remains associated with exactly its own actual owner; close can retry
only safe known directory cleanup and known not-yet-attempted handles. Existing sticky
unknown-FD semantics remain: attempted close recorded BEFORE it can raise, no retry of an
uncertain number, no reused foreign FD close, no unknown-lock or vacancy assertion. Preserve
original non-Exception even when later ordinary cleanup fails; cleanup non-Exception outranks
ordinary error. All safe independent cleanup is attempted. Existing no-owner call remains
supported and strongly retains _pending on failure, but provides no new association guarantee.
Do not patch unrelated lifetime or parent reinitialization behavior.

## Finite proof

Use actual existing `_prepared_fixture` private synthetic setup/current fake GPU package and
null driver fixtures; no framework/model/GPU/service/install. Actual prepare starts no process.
1. Optional-owner success returns actual PreparedLaunch, source/pins/revalidation behave as
   before; capture reports actual pending, capture.close refuses handoff before returned
   preparation closes, then actual close drains; borrowed reservation remains usable.
2. Fault actual PreparedLaunch.revalidate AFTER successful actual admission, and actual
   shutil.rmtree refusal, creating the original concrete pre-return boundary. Capture is
   retained BEFORE call, reports its exact real pending capsule/owner, supports safe retry
   once the controlled cleanup fault is removed. No pending-list diff in production.
3. Two actual owned pending failures interleaved demonstrate cleanup association: closing A
   cannot delete/close B, both eventually clean with supported own handles. Global registry
   references are retention only, not operation identification.
4. Actual interruption identity plus ordinary/non-Exception cleanup priority; creator/fork
   borrower refusal and parent owner still usable; duplicate/busy/forged/mutated use refused
   before acquisition. Tests may inspect actual private state as evidence, not inject a fake
   complete owner/authority. A deliberately hostile exception rejects attribute assignment:
   actual preallocated capture still retains its association while that same exception escapes.
5. Controlled close of one actual own FD closes then raises, optionally allocate a fresh own
   FD reusing its number, supported retry never closes that reused number; unknown remains
   explicit. No global FD scan or unrelated process/signal.
6. One original narrow association guard control using two actual captures can omit only
   the concrete coupling/one-use check in an isolated module/function. State the exact
   finite effect; do not require one removed early guard to defeat all independent guards.
   Baseline refusal and actual full call/source checks remain; no fake whole prepare.
7. Relevant unchanged launch pure tests and selected actual launch/parent composition only
   where the new delta can affect them. Split actual cases into bounded invocations; no
   repeated whole suites absent a new concern. Keep exact source/command/log/hash/failure
   history and count overlaps honestly. Fresh affected independent review before producer
   preparation merge/integration; current canonical CI remains a separate required gate.

Only SIX allowed paths: existing src/slaif_raggedized_helper/gpu_worker_launch.py;
NEW tests/unit/test_gpu_launch_preparation_owner.py;
NEW tests/integration/test_gpu_launch_preparation_owner_composition.py;
NEW docs/parallel/gpu-launch-preparation-owner-api.md;
NEW docs/parallel/gpu-launch-preparation-owner-design.md (EXACT this Root contract);
NEW order path supplied by finalized order. Existing tests/API/other source/dependencies/
source books/law/ARCH/critical/CI/helpers/locks/profiles are immutable. Actual design conflict
returns a precise regular blocker while independent finite work continues, never hidden scope.

Per invocation120wall/30CPU/1GiB/five threads1/no bytecode/cached application and actual
existing synthetic fixtures only; private newly allocated --basetemp, no shared retention
cleanup. No install/network/framework/Tensor/model/GPU/driver/service/credential/real corpus,
unknown-owner actions, canonical FIFO read/replay, push/merge/release/deploy. Ruff wall-only
allocator exception disclosed. No claimed neural provenance, GPU vacancy, deployment safety,
current authorization/rights, efficient bulk/controller, security/license/ICA/MVP qualification.

## Root amendment 1 — retain the actual successful handoff across return interruption

Status: FINAL, SAME PAR-007-LAUNCH-OWNER-A/branch/base/context. DHA NONE.
Original contract/order remain immutable. Root independently reviewed6f925c92, ran36 relevant
unit cases/one actual parent-binding case, then reproduced a real pre-return interruption:
actual _prepare_impl succeeds, record becomes handoff, Python interruption occurs at actual
prepare's `return result` line; caller receives no PreparedLaunch and capture.close refuses
as transferred. Actual pins/capsule remain pending. Root used actual own no-process owner
cleanup only after recording failure, so no fixture/process leak remains. This is a concrete
finite return-path gap in the required caller-retained association, not permission to remove
handoff protection or to claim atomic Python return.

Extend the small public capture with read-only `prepared` property, returning the SAME actual
PreparedLaunch once a successful handoff has been recorded, or None before a successful
handoff. Creator/exact-record and nonblocking busy checks apply. The record must strongly
retain the actual returned object BEFORE switching to handoff. If return itself is interrupted,
the caller can recover that actual object from its already retained capture and use the
EXISTING PreparedLaunch.close after confirming the same normal no-child/drained boundary.
This is access to the original owned object, not a new independent cleanup right. Capture.close
continues to refuse a pending successful handoff; it cannot close a live parent's resources.

Use actual record binding and known class dispatch; no caller-supplied result/DTO/callback or
lookup by pending-list diff. On failed preparation no successful object is exposed. Store the
actual object before handoff state under the existing operation guard; a failure before that
transition remains safely cleanup-able through the failed capture. State that microscopic
allocation/lock-release/kernel interruption windows are finite limitations, not solved by
Python-level claims. No new broad lock/parent redesign or predecessor mutation.

Meaningful regression: construct actual private preparation with capture, inject original
non-Exception at actual `return result` AFTER successful handoff, confirm same interruption,
no returned variable, capture.prepared is actual successfully admitted PreparedLaunch with
same actual _Owner. Capture.close still refuses. Capture.prepared.close (no model child ever
started) drains and borrowed reservation remains usable. Normal success capture.prepared is
exact returnedobject, failure propertyNone, foreign/fork/busy property refuses. Preserve the
original counterexample/Root logs and add only affected tests/docs. The complete case must use
actual prepare/pins/capsule/source checks, not fake prepare success. Existing36+1 proof remains
finite historical; rerun affected new/source checks proportionately, not gratuitous full suites.

Keep exact same SIX allowed paths/original order. Existing design path becomes EXACT byte
concatenation of original contracts/gpu-launch-preparation-owner-v1.md THEN this entire Root
amendment. API/report explain recovery and success transfer limits. Request checkpoint at NEW
unpublished SHA; previous6f92 retained. No report/response until Root REPORT; fresh affected
independent peer/current canonical CI remain required before integration. No newcontrol/goal/
FIFOread/replay/model/profile/auth/reset or actual GPU/framework operation.
