"""Private current-policy partition eligibility over a borrowed pin capture.

Composes the exact admitted current selected-policy request
(``private_policy_request.PolicyRequestAdmission``) with the already
admitted in-memory capture of one exact borrowed operator-owned active
``raw_snapshot_pin.PinOwner`` (objective 009, PAR-009): one absolute
cooperative deadline bound to this operation, honoring the shorter
remaining current request lifetime, the genuine ``recheck`` before using
pin data and again after scope computation, and the real
``supplied_policy_eligibility.unavailable_partitions`` over the exact
retained current policy and captured membership with the real narrowed
scope rules (``provenance_records.reader_allows`` and canonical effective
access) deciding one fixed, content-free eligible or unavailable outcome.

Boundaries: the caller supplies no policy bytes/DTO, stored root,
``PinData``, provider, raw credential, arbitrary grants or clock.  The
entry only borrows the already created ``PinData`` and keeps the owner's
existing nonblocking creator/operation guard across the in-memory
capture, the scope computation, the final current check and the result
assembly, releasing it on every exit; it verifies the active in-memory
capture and binds the exact snapshot identity (including the parsed
manifest's own snapshot ID), core digest and captured membership bytes
to the admitted manifest's membership descriptor.  ``PinOwner.check``
(a full snapshot reload validating source, dense and lexical backing)
is outside this operation, as are namespace revalidation,
snapshot/source file opens, catalog, pin acquisition, encoding, scoring
and publication.  Owner lifetime and cleanup are preserved.  A currently
unavailable partition intersecting the requested readable scope refuses
the whole scope; a scope narrowed to zero readable membership entries
has no usable scope and refuses the same fixed way; a withdrawn
partition outside that scope does not block an unaffected scope.
Grants come only from the admitted principal: the retained selected
policy is re-admitted in memory as one bounded coherent isolated
snapshot through the genuine closed supplied-policy admission and
verified against the exact semantic identity bound by the original
admission before any of its principal or document rules are used, so no
exposed mutable nominal DTO - detached or nested - can anchor
authority; the admission's detached nominal authority value is then
bound to that verified snapshot's exact admitted principal grant
through the existing bounded DTO admission, one coherent isolated
grants snapshot serving both scope evaluation and the opaque binding,
and a changed or invalid detached authority is refused at the initial
and final observation cuts.  Optional nominal source restrictions only
narrow.  Any
disallowed partition identity and all source text stay out of outward
results and errors.  Every ordinary failure is one fixed input-free
``PolicyPinEligibilityError`` carrying no caught cause or context; a
non-Exception BaseException propagates by identity, preserving
interruption and cleanup semantics.  This is an observation of in-memory
membership under genuine selected policy, compatible with a separately
authorized pinned data history; durable writer, actual pin/file
freshness, scoring/encoding/source transfer, publication and final
delivery remain distinct gates.  Synthetic tests only: no write, no
credential provisioning, no current authority invocation, no dispatch.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
import time

from . import (
    provenance_records,
    raw_lexical_search,
    raw_snapshot_manifest,
    supplied_policy,
    supplied_policy_eligibility,
)
from .private_policy_request import PolicyRequestAdmission
from .raw_snapshot_files import BoundSnapshotData
from .raw_snapshot_membership import Membership
from .raw_snapshot_pin import PinData, PinOwner
from .raw_snapshot_selection import Pointer

__all__ = [
    "PinEligibilityObservation",
    "PolicyPinEligibilityError",
    "prepare_current_pin_eligibility",
]

_ERROR_MESSAGE = "private pin eligibility refused"
_MIN_DEADLINE_MS = 1
_MAX_DEADLINE_MS = 30000  # the accepted reader cap


class PolicyPinEligibilityError(ValueError):
    """Fixed, input-free private pin-eligibility refusal."""

    def __init__(self):
        super().__init__(_ERROR_MESSAGE)


class _Refused(Exception):
    """Internal refusal marker; never escapes a public boundary."""

    def __init__(self) -> None:
        super().__init__()


@dataclass(frozen=True, repr=False, slots=True, init=False)
class PinEligibilityObservation:
    """Factory-only private observation; see :func:`prepare_current_pin_eligibility`.

    Binds the eligible or unavailable outcome to the specific borrowed
    owner, the current admission, the exact snapshot identity and the
    selected policy identity, and retains the exact captured core and
    membership bytes plus the normalized narrowed-authority identity
    only as opaque private bindings.  Frozen record; its constructor
    cannot confer authority.  No partition identity and no source text
    appear in any exposed attribute.
    """

    eligible: bool
    snapshot_id: str
    policy_id: str
    principal_id: str
    selection_generation: int
    _owner: object
    _admission: object
    _core: bytes
    _membership: bytes
    _grants: object
    _restrictions: object

    def __init__(self, *_args, **_kwargs):
        raise PolicyPinEligibilityError()

    def __repr__(self) -> str:
        return "PinEligibilityObservation(<redacted>)"


def _deadline_accepted(deadline_ms) -> bool:
    # One bounded monotonic operation deadline in the accepted reader range.
    return (
        type(deadline_ms) is int
        and not isinstance(deadline_ms, bool)
        and _MIN_DEADLINE_MS <= deadline_ms <= _MAX_DEADLINE_MS
    )


def _remaining_ms(end) -> float:
    return (end - time.monotonic()) * 1000.0


def _still_within(end) -> None:
    # Refuse a late usable success after every phase.
    if time.monotonic() >= end:
        raise _Refused()


def _validated_restrictions(restrictions):
    # The existing authority bounder: an exact Restrictions DTO or None,
    # nothing wider; a ValueError refuses before any observation.  The
    # returned snapshot is the normalized narrowed-authority identity.
    if restrictions is None:
        return None
    try:
        _grants, snapshot = raw_lexical_search._authority(None, restrictions)
    except Exception:
        raise _Refused() from None
    return snapshot


def _bounded_admission(value):
    # The existing bounded DTO admission for one authority value.
    try:
        snapshot, _ = raw_lexical_search._authority(value, None)
    except Exception:
        raise _Refused() from None
    return snapshot


def _admitted_principal_grants(policy, principal_id):
    # The exact admitted principal grant of the verified isolated policy
    # snapshot for the admitted principal ID: the anchor for the
    # admission's detached nominal authority value.
    if type(policy) is not supplied_policy.SuppliedPolicy:
        raise _Refused()
    for admitted in policy.principals:
        if admitted.principal_id == principal_id:
            return admitted.grants
    raise _Refused()


def _isolated_policy_snapshot(admission):
    # One bounded coherent in-memory isolated snapshot of the retained
    # selected policy: the genuine closed supplied-policy admission over
    # its principal and document rules, with the existing bounds and
    # canonical hash, verified against the exact semantic identity bound
    # by the original admission.  Its fresh re-admission of every
    # exposed nominal DTO is the only policy object this observation
    # uses, so agreement between two mutable copies cannot anchor
    # authority.  No stored policy bytes are re-opened.
    try:
        principals = tuple(
            supplied_policy.PrincipalSpec(
                admitted.principal_id, admitted.verifier, admitted.operations, admitted.grants
            )
            for admitted in admission.policy.principals
        )
        documents = tuple(
            supplied_policy.DocumentRule(admitted.document_id, admitted.admitted)
            for admitted in admission.policy.documents
        )
        snapshot = supplied_policy.admit_policy(principals, documents)
    except Exception:
        raise _Refused() from None
    if snapshot.policy_id != admission.policy_id:
        raise _Refused()
    return snapshot


def _bound_grants(admission, anchor_snapshot):
    # Bind the detached nominal authority value to the selected policy's
    # admitted principal through the existing bounded DTO admission; a
    # changed or invalid detached value refuses with the fixed error.
    candidate = _bounded_admission(admission.grants)
    if candidate is None or candidate != anchor_snapshot:
        raise _Refused()
    return candidate


def _genuine_recheck(admission, end) -> None:
    # The genuine recheck under the remaining budget of the one absolute
    # deadline; the request end is never reset or extended by it.
    remaining_ms = _remaining_ms(end)
    if remaining_ms < _MIN_DEADLINE_MS:
        # The absolute request budget cannot cover the reader's 1 ms
        # minimum; refuse before the call.
        raise _Refused()
    if not admission.recheck(deadline_ms=min(int(remaining_ms), _MAX_DEADLINE_MS)):
        raise _Refused()


def _scope_refused(policy_snapshot, membership, grants, restrictions) -> bool:
    # Real unavailable-partition derivation over the verified isolated
    # selected-policy snapshot and captured membership, then the real
    # narrowed
    # scope rules: an unavailable partition inside the requested readable
    # scope refuses the whole scope; a scope with no readable membership
    # entry at all has no usable scope and refuses the same fixed way; a
    # withdrawal outside the readable scope does not block an unaffected
    # scope.
    unavailable = set(
        supplied_policy_eligibility.unavailable_partitions(policy_snapshot, membership)
    )
    usable = False
    for entry in membership.entries:
        scope = provenance_records.admit_record("Scope", entry.scope_bytes)
        if not provenance_records.reader_allows(scope, grants, restrictions):
            continue
        usable = True
        if entry.partition_id in unavailable:
            return True
    return not usable


def _observed(admission, owner, end, policy_snapshot, grants, restrictions):
    # Read-only borrow that keeps the owner's own nonblocking
    # creator/operation guard across the in-memory capture, the scope
    # computation, the final current check and the result assembly,
    # releasing it on every exit: a concurrently closed owner can never
    # receive a returned preparation, and a busy owner is refused
    # nonblocking.  The active in-memory capture is verified, never
    # reloaded.
    if owner.pid != os.getpid():
        raise _Refused()
    if not owner.guard.acquire(blocking=False):
        raise _Refused()
    try:
        if owner.state != "ACTIVE" or owner.value is None:
            raise _Refused()
        value = owner.value
        if type(value) is not PinData:
            raise _Refused()
        pointer, data = value.pointer, value.data
        if type(pointer) is not Pointer or type(data) is not BoundSnapshotData:
            raise _Refused()
        if pointer.snapshot_id != data.snapshot_id:
            raise _Refused()
        core = data.core_bytes
        if type(core) is not bytes:
            raise _Refused()
        # Exact snapshot identity and core digest binding.
        if hashlib.sha256(core).hexdigest() != pointer.core_sha256:
            raise _Refused()
        # Pure in-memory manifest re-admission of the captured core; the
        # parsed manifest's own snapshot ID must bind to the capture.
        manifest = raw_snapshot_manifest.parse(core)
        if manifest.snapshot_id != data.snapshot_id:
            raise _Refused()
        membership = data.membership
        if type(membership) is not Membership:
            raise _Refused()
        membership_bytes = membership.membership_bytes
        if type(membership_bytes) is not bytes:
            raise _Refused()
        path = json.loads(core.decode("ascii"))["membership_path"]
        descriptor = next((f for f in manifest.files if f.path == path), None)
        if (
            descriptor is None
            or descriptor.role != "source_membership"
            or descriptor.schema != "slaif-raw-source-membership-v1"
            or descriptor.bytes != len(membership_bytes)
            or descriptor.sha256 != hashlib.sha256(membership_bytes).hexdigest()
        ):
            raise _Refused()
        _still_within(end)
        refused = _scope_refused(policy_snapshot, membership, grants, restrictions)
        _still_within(end)
        # Genuine current freshness again, under the same held guard,
        # before exposing either a usable preparation or a scope
        # diagnostic.
        _genuine_recheck(admission, end)
        _still_within(end)
        # Final observation cut: the detached authority value must still
        # agree with the selected policy's admitted principal, so a
        # changed authority can never bind under the same selected
        # identity.
        if _bound_grants(admission, grants) != grants:
            raise _Refused()
        _still_within(end)
        return _build_observation(
            admission, owner, pointer, core, membership_bytes,
            grants, restrictions, not refused,
        )
    finally:
        owner.guard.release()


def _build_observation(
    admission, owner, pointer, core, membership_bytes, grants, restrictions, eligible
):
    observation = object.__new__(PinEligibilityObservation)
    object.__setattr__(observation, "eligible", eligible)
    object.__setattr__(observation, "snapshot_id", pointer.snapshot_id)
    object.__setattr__(observation, "policy_id", admission.policy_id)
    object.__setattr__(observation, "principal_id", admission.principal_id)
    object.__setattr__(observation, "selection_generation", admission.selection.generation)
    object.__setattr__(observation, "_owner", owner)
    object.__setattr__(observation, "_admission", admission)
    # Exact capture and normalized narrowed-authority identity, retained
    # opaquely: no partition identity and no source text are exposed.
    object.__setattr__(observation, "_core", core)
    object.__setattr__(observation, "_membership", membership_bytes)
    object.__setattr__(observation, "_grants", grants)
    object.__setattr__(observation, "_restrictions", restrictions)
    return observation


def prepare_current_pin_eligibility(admission, owner, *, deadline_ms, restrictions=None):
    """Observe current partition eligibility under one borrowed active pin.

    The exact admitted ``admission`` carries the retained current policy,
    the admitted principal grants and the one absolute creator-process
    request deadline; the exact borrowed ``owner`` carries the already
    created in-memory pin capture.  One absolute cooperative deadline
    bound to this operation starts before any restriction work and
    honors the shorter remaining current request lifetime.  Current
    freshness is checked through the genuine ``recheck`` before using
    pin data and again after scope computation, with the owner's
    existing nonblocking guard held across the in-memory capture, the
    scope computation, the final current check and the result assembly;
    a current or timed refusal prevents any usable output.  The outcome
    is the real unavailable-partition derivation over the exact retained
    current policy and captured membership intersected with the real
    narrowed scope rules; an unavailable partition inside the requested
    readable scope refuses the whole scope, a scope narrowed to zero
    readable membership entries has no usable scope and refuses the same
    fixed way, and one outside it does not block an unaffected scope.
    The retained selected policy is re-admitted in memory as one
    bounded coherent isolated snapshot through the genuine closed
    supplied-policy admission and verified against the exact semantic
    identity bound by the original admission before any of its
    principal or document rules are used; the admission's detached
    nominal authority value is then bound to that verified snapshot's
    exact admitted principal grant through the existing bounded DTO
    admission, and the same agreement is re-verified at the final
    observation cut, so one coherent isolated grants snapshot serves
    scope evaluation and the opaque binding and a changed or invalid
    detached authority refuses with the fixed error.  No disallowed
    partition identity or source text appears in the result or in any
    ordinary error; a non-Exception BaseException propagates by
    identity.
    """
    error = None
    result = None
    try:
        try:
            if not _deadline_accepted(deadline_ms):
                raise _Refused()
            if type(admission) is not PolicyRequestAdmission or type(owner) is not PinOwner:
                raise _Refused()
            # The single absolute cooperative deadline bound to this
            # operation starts before any restriction work, honoring the
            # shorter remaining current request lifetime; the request
            # end is never reset or extended.
            end = min(time.monotonic() + deadline_ms / 1000.0, admission._end)
            _still_within(end)
            restrictions = _validated_restrictions(restrictions)
            _still_within(end)
            # One bounded coherent in-memory isolated snapshot of the
            # retained selected policy, verified against the exact
            # semantic identity bound by the original admission; it is
            # the only policy object used for principal or document
            # rules in this observation.
            policy_snapshot = _isolated_policy_snapshot(admission)
            _still_within(end)
            # Bind the detached nominal authority value to the verified
            # snapshot's exact admitted principal grant; one coherent
            # isolated snapshot serves scope evaluation and the opaque
            # binding, and is re-verified at the final observation cut.
            anchor_snapshot = _bounded_admission(
                _admitted_principal_grants(policy_snapshot, admission.principal_id)
            )
            grants = _bound_grants(admission, anchor_snapshot)
            _still_within(end)
            # Genuine current freshness before using any pin data.
            _genuine_recheck(admission, end)
            _still_within(end)
            result = _observed(admission, owner, end, policy_snapshot, grants, restrictions)
            _still_within(end)
        except Exception:
            error = PolicyPinEligibilityError()
        # Raised after the handler exits: no caught cause or context is
        # retained; a non-Exception BaseException already propagated by
        # identity through the outer span.
        if error is not None:
            raise error
        return result
    finally:
        # The entry retains no caller-owned nominal authority beyond the
        # bound observation locals; clear them from this retained frame.
        error = None
        result = None
