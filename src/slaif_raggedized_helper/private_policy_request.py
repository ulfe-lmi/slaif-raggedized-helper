"""Private current-view request admission and freshness (objective 009, PAR-009).

Composes the accepted private components under one trusted operator-owned
reader (ARCH 13.3-13.4/A23/A24 boundary, provenance E/I): the exact admitted
``PolicyCaptureReader`` observation (``capture``), the pure supplied-policy
wire decoder (``admit_policy_bytes``) and the genuine fullscan supplied-
credential matcher (``match_supplied``) with the exact required operations
``("search", "sources:read")``.

One absolute creator-process request deadline is established on entry from
the bounded monotonic argument and is carried through every later recheck;
a per-check argument can only tighten the original remaining budget and can
never reset it.  Every reader call is capped by the current remaining
request time and the accepted reader cap (1..30000 ms), and the entry
checks the remaining budget after capture, decode, match and the final
reread, refusing a late usable success, and again after constructing the
admission.  Decode and match are pure, so the entry budget is the only
bound that covers them; the final post-reread check is a defensive backstop
because the reader's own clean-expiry checkpoint already refuses a result
crossing its call deadline.  A fresh actual ``read_selection()`` after
decode and match must return exact bytes equal to the captured selected
publication before any private admission is yielded.  A changed generation,
changed bytes, malformed or absent selection, or an expired operation
refuses the whole request.

A recheck serializes the latch check, the budget check, the bounded read,
the exact comparison, the post-comparison cutoff, the latch and the
success decision in one request ownership span acquired nonblocking.
A contended span refuses with zero observations and does not latch:
contention is distinguished from an entered observation, and a foreign
creator PID and an exhausted original deadline refuse before the read,
without latching and without any reader call even under a fresh-looking
per-check timeout.  Once the real read has been entered, an ordinary
observation failure (the admitted reader's one content-free error for
missing, malformed, latched-owner or expired conditions) conservatively
latches the admission invalid permanently; no filesystem or lock cause is
inferred from the error and no extra read is made.  An observed changed
selection, and a late completion against the fixed local observation end
(the monotonic time before the real call plus the capped call duration,
clipped to the fixed original request end) checked after the observation
and the comparison, latch the same way.  A latched admission remains
invalid under concurrent use, even if the record is restored.
A separate request captures and admits fresh bytes; a retained match is
evidence from the earlier verified immutable selected identity.  This
scope measures observations: preventing an undetected selection reversal
between reads still requires the trusted monotonic-generation writer
protocol and an explicit operator recovery protocol.

Boundaries: no public callable or constructor attaches an arbitrary
supplied view to this path.  The entry accepts only an exactly admitted
``PolicyCaptureReader``, exact credential bytes and one bounded deadline;
no root path, arbitrary selector, caller callback, view bytes or match DTO
is accepted.  The raw credential is used only for the bounded initial match
and is cleared from this entry's own retained frame on success and failure;
it is not retained in the admission record, errors or diagnostics (not a
zeroization claim).  Every externally visible ordinary failure is one fixed
input-free ``PolicyRequestError`` with no own caught payload as cause or
context; a non-Exception BaseException propagates by identity, preserving
the owned reader's system interruption and cleanup semantics.  Synthetic
tests only: no write, no credential provisioning, no current authority
invocation, no dispatch.
"""

from __future__ import annotations

from dataclasses import dataclass
import os
import threading
import time

from .policy_selection import PolicySelection
from .private_policy_capture import PolicyCaptureReader
from .provenance_records import Grants
from .supplied_policy import SuppliedPolicy, match_supplied
from .supplied_policy_wire import admit_policy_bytes

__all__ = ["PolicyRequestAdmission", "PolicyRequestError", "request_current_view"]

_REQUEST_ERROR_MESSAGE = "private policy request refused"
_REQUIRED_OPERATIONS = ("search", "sources:read")
_MIN_DEADLINE_MS = 1
_MAX_DEADLINE_MS = 30000  # the accepted reader cap


class PolicyRequestError(ValueError):
    """Fixed, input-free private current-view request refusal."""

    def __init__(self):
        super().__init__(_REQUEST_ERROR_MESSAGE)


class _Refused(Exception):
    """Internal refusal marker; never escapes a public boundary."""

    def __init__(self) -> None:
        super().__init__()


@dataclass(frozen=True, repr=False, slots=True, init=False)
class PolicyRequestAdmission:
    """Factory-only private request admission; see :func:`request_current_view`.

    Binds the admitted principal match, the exact captured selected
    publication, the independent semantic policy identity and the admitted
    immutable policy to the trusted reader that produced them, under one
    absolute creator-process deadline established on entry.  Frozen record;
    its constructor cannot confer authority.  Carries no raw credential.
    """

    principal_id: str
    grants: Grants
    operations: tuple[str, ...]
    policy_id: str
    authorization_status: str
    selection: PolicySelection
    policy: SuppliedPolicy
    _reader: PolicyCaptureReader
    _expected_selection_bytes: bytes
    _end: float
    _owner_pid: int
    _latch_guard: threading.Lock
    _invalid: bool

    def __init__(self, *_args, **_kwargs):
        raise PolicyRequestError()

    def __repr__(self) -> str:
        return "PolicyRequestAdmission(<redacted>)"

    def recheck(self, *, deadline_ms: int) -> bool:
        """Reread the same trusted selector under the original request budget.

        The per-check deadline only tightens the remaining time of the one
        absolute deadline established on entry; it can never reset it.
        Returns True only while the exact selected publication bytes still
        match the captured record and the operation completes by its fixed
        local observation end (the monotonic time before the real call
        plus the capped call duration, clipped to the fixed original
        request end, which is never reset).  An observed changed
        selection, an ordinary observation failure after entering the
        real read (the admitted reader's one content-free error for
        missing, malformed, latched-owner or expired conditions; no cause
        is inferred and no extra read is made), or a late completion at
        the post-comparison operation cutoff latches this admission
        invalid permanently, while the original request end is preserved
        for any subsequent check; later rechecks refuse without a further
        reader call, even if the record is restored.  A contended span, a
        foreign creator PID or an exhausted original deadline refuses
        before the read, without latching and without any reader call.
        A new request captures and admits a fresh view instead; the
        shared reader itself is never latched by this admission.
        """
        if not _deadline_accepted(deadline_ms):
            raise PolicyRequestError() from None
        # Refuse a foreign creator PID before attempting the lock.
        if os.getpid() != self._owner_pid:
            return False
        # One request ownership span: latch check, budget check, bounded
        # read, exact comparison, latch and success decision are
        # serialized.  A concurrent span is refused nonblocking with zero
        # observations (contention, not an observed mismatch).
        if not self._latch_guard.acquire(blocking=False):
            return False
        try:
            if self._invalid:
                return False
            remaining_ms = (self._end - time.monotonic()) * 1000.0
            if remaining_ms < 1:
                # The absolute request deadline established on entry is
                # exhausted; no per-check argument can reset it.  Refuse
                # without a reader call.
                return False
            call_ms = min(int(remaining_ms), deadline_ms, _MAX_DEADLINE_MS)
            # The fixed local observation end for this recheck: the
            # monotonic time before the real call plus the capped call
            # duration, clipped to the fixed original request end.  The
            # integer reader limit and the 1 ms lower floor are kept, and
            # the original end is never reset or extended.
            observation_end = min(time.monotonic() + call_ms / 1000.0, self._end)
            try:
                fresh = self._reader.read_selection(deadline_ms=call_ms)
            except Exception:
                # An ordinary observation failure after entering the real
                # read: the admitted reader reports one content-free
                # ordinary error for different unavailable conditions, so
                # no filesystem or lock cause is inferred from it and no
                # extra read is made.  The admission is conservatively
                # latched invalid permanently under the held span.
                object.__setattr__(self, "_invalid", True)
                return False
            if fresh.selection_bytes != self._expected_selection_bytes:
                # An observed mismatch is permanent.
                object.__setattr__(self, "_invalid", True)
                return False
            if time.monotonic() >= observation_end:
                # The tightened operation cutoff at the caller, after the
                # observation and the exact comparison: the operation
                # completed late against its fixed local observation end
                # (itself clipped to the fixed original request end), so
                # a late usable success never qualifies.  The late
                # completion latches this admission permanently, while
                # the original request end is preserved for any
                # subsequent check.
                object.__setattr__(self, "_invalid", True)
                return False
            return True
        finally:
            self._latch_guard.release()


def _deadline_accepted(deadline_ms) -> bool:
    # One bounded monotonic request deadline in the accepted reader range.
    return (
        type(deadline_ms) is int
        and not isinstance(deadline_ms, bool)
        and _MIN_DEADLINE_MS <= deadline_ms <= _MAX_DEADLINE_MS
    )


def _call_deadline_ms(end) -> int:
    # Cap each reader call by the current remaining request time and the
    # accepted reader cap; refuse before the call when the remaining budget
    # cannot cover the reader's 1 ms minimum.
    remaining_ms = (end - time.monotonic()) * 1000.0
    if remaining_ms < 1:
        raise _Refused()
    return min(int(remaining_ms), _MAX_DEADLINE_MS)


def _still_within(end) -> None:
    # Refuse a late usable success after every phase.
    if time.monotonic() >= end:
        raise _Refused()


def _build_admission(reader, captured, policy, match, end):
    # The raw credential is a local of request_current_view only; it is not
    # retained here or in any error.
    admission = object.__new__(PolicyRequestAdmission)
    object.__setattr__(admission, "principal_id", match.principal_id)
    object.__setattr__(admission, "grants", match.grants)
    object.__setattr__(admission, "operations", match.operations)
    object.__setattr__(admission, "policy_id", match.policy_id)
    object.__setattr__(admission, "authorization_status", match.authorization_status)
    object.__setattr__(admission, "selection", captured.selection)
    object.__setattr__(admission, "policy", policy)
    object.__setattr__(admission, "_reader", reader)
    object.__setattr__(admission, "_expected_selection_bytes", captured.selection.selection_bytes)
    object.__setattr__(admission, "_end", end)
    object.__setattr__(admission, "_owner_pid", os.getpid())
    object.__setattr__(admission, "_latch_guard", threading.Lock())
    object.__setattr__(admission, "_invalid", False)
    return admission


def request_current_view(reader, credential, *, deadline_ms):
    """Admit one private current-view request under one bounded deadline.

    The trusted operator-owned ``reader`` is admitted by this private entry
    only: exact ``PolicyCaptureReader`` type, nothing else.  One absolute
    creator-process deadline established on entry spans capture, pure
    decode, match and the final fresh reread, and is carried through every
    later recheck of the yielded admission; the exact selected publication
    must still match before any admission is yielded.  The raw credential
    is used only for the bounded initial match and is cleared from this
    entry's own retained frame on success and failure; it is not retained
    in the admission record, errors or diagnostics (not a zeroization
    claim).
    """
    try:
        if type(reader) is not PolicyCaptureReader:
            raise PolicyRequestError() from None
        if not _deadline_accepted(deadline_ms):
            raise PolicyRequestError() from None
        end = time.monotonic() + deadline_ms / 1000
        error = None
        result = None
        try:
            captured = reader.capture(deadline_ms=_call_deadline_ms(end))
            _still_within(end)
            policy = admit_policy_bytes(captured.wire_bytes)
            _still_within(end)
            match = match_supplied(policy, credential, _REQUIRED_OPERATIONS)
            _still_within(end)
            fresh = reader.read_selection(deadline_ms=_call_deadline_ms(end))
            _still_within(end)
            if fresh.selection_bytes != captured.selection.selection_bytes:
                raise _Refused()
            result = _build_admission(reader, captured, policy, match, end)
            _still_within(end)
        except Exception:
            error = PolicyRequestError()
        # Raised after the handler exits: no caught cause or context is
        # retained; a non-Exception BaseException already propagated by
        # identity through the outer span.
        if error is not None:
            raise error
        return result
    finally:
        # The raw credential is cleared from this entry's own retained
        # frame on success and on every failure, without changing the
        # fixed content-free error, the shared matcher or the identity
        # propagation of a non-Exception BaseException.
        credential = None
