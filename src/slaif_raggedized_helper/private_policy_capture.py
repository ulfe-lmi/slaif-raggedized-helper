"""Private offline policy wire capture from one explicit trusted root.

One private offline evaluation invocation owner (ARCH 13.3-13.4/A23/A24
boundary, provenance E): observe the current selection and capture the
opaque policy wire bytes from a single explicit trusted operator-owned
root, under synthetic tests only.  The trust model is a configured root
and a trusted immutable writer; no hostile same-UID, special-device race
or guaranteed kernel I/O timeout claim is made.

Boundaries: no write, delete, link, rename, fsync, lock file, file
creation in product source, separate broker mutation, or change to the
existing shared primitives; no actual current auth invocation.  The
reader makes only boundary observations and records no rollback or
durability guarantee.  Descriptor custody is independent from the
publisher: each operation uses a reader-owned slot with the publisher's
exact fixed six-cell protocol, never its publication pool, and the
module makes no program-wide descriptor or service/parallel ownership
claim.  An uncertain open/close or a failed cleanup latches the owner
closed and retains its counted slot; it never acquires more, never
retries numeric closes and never evicts an unresolved slot.

Operation discipline: the creator PID is checked before lock entrance,
the latched-closed state is checked under the acquired guard before any
slot or open, and the closed latch plus any retained unresolved slot are
published while still under the guard.  The finite six-cell teardown
traverses without a time cut-off, closing all definitely owned cells
even if the observation deadline has expired; no successful result is
delivered after a cooperative expiry, which is verified as the final
checkpoint before returning success without latching a clean owner.
"""

from dataclasses import dataclass
import hashlib
import os
import stat
import sys
import threading
import time
import unicodedata

from .policy_selection import PolicySelection, parse_policy_selection
from .private_report_publication import (
    _CHUNK,
    _Failure,
    _READ_FLAGS,
    _Slot,
    _cleanup,
    _file_ok,
    _file_signature,
    _namespace,
    _tick,
    _walk,
)

__all__ = ["CapturedPolicyBytes", "PolicyCaptureError", "PolicyCaptureReader"]

_SELECTION_NAME = "current-policy.json"
_MAX_RECORD_BYTES = 512


class PolicyCaptureError(ValueError):
    """Fixed, input-free private policy capture refusal."""

    def __init__(self):
        super().__init__("private policy capture refused")


@dataclass(frozen=True, repr=False, slots=True)
class CapturedPolicyBytes:
    """Immutable stable capture; no dev/inode or other descriptor state."""

    selection: PolicySelection
    wire_bytes: bytes


def _root_path_ok(root):
    # Existing absolute path checks for the trusted private root,
    # mirroring publisher root admission: <=4096 total UTF-8 bytes,
    # <=64 components, <=255 UTF-8 bytes per component, path charset
    # and grammar.  The character count is rejected before any
    # encoding, and a malformed UTF-8 root (for example a lone
    # surrogate) is refused without leaking an encoding context.
    if type(root) is not str or len(root) > 4096:
        return False
    if not root.startswith("/") or root == "/":
        return False
    parts = root[1:].split("/")
    try:
        encoded = root.encode("utf-8")
    except UnicodeError:
        return False
    if len(encoded) > 4096 or not 1 <= len(parts) <= 64:
        return False
    for part in parts:
        if (
            not part
            or part in (".", "..")
            or len(part.encode("utf-8")) > 255
            or any(unicodedata.category(c) == "Cc" for c in part)
        ):
            return False
    return True


def _deadline_end(deadline_ms):
    # Deadline integer 1..30000 ms; monotone cooperative checkpoints, not
    # a guaranteed kernel I/O timeout claim.
    if (
        type(deadline_ms) is not int
        or isinstance(deadline_ms, bool)
        or not 1 <= deadline_ms <= 30000
    ):
        raise PolicyCaptureError() from None
    return time.monotonic() + deadline_ms / 1000


def _probe_entry(root_fd, name, end):
    # Pre-probe the linked entry and refuse special files before any open
    # attempt; the later fd recheck revalidates type and identity.
    _tick(end)
    try:
        st = os.lstat(name, dir_fd=root_fd)
    except OSError:
        raise _Failure() from None
    if not stat.S_ISREG(st.st_mode):
        raise _Failure()
    return st


class PolicyCaptureReader:
    """One explicit trusted operator-owned root for private capture.

    The root is admitted by this private constructor only; it is never
    taken from a query, a caller-supplied selection, or a data snapshot.
    The reader retains the validated absolute path, the creator PID and
    one operation lock.  Each operation checks the creator PID before
    entering the lock and serializes one active operation per owner
    through nonblocking lock entrance.
    """

    def __init__(self, root: str):
        if not _root_path_ok(root):
            raise PolicyCaptureError() from None
        self._root = root
        self._parts = root[1:].split("/")
        self._creator = os.getpid()
        self._guard = threading.Lock()
        self._latched = False
        self._retained_slot = None

    def read_selection(self, *, deadline_ms: int = 30000) -> PolicySelection:
        """Return the decoded PolicySelection at its successful observation."""
        return self._operation(deadline_ms, self._read_selection)

    def capture(self, *, deadline_ms: int = 30000) -> CapturedPolicyBytes:
        """Return immutable captured bytes only after stable capture and cleanup."""
        return self._operation(deadline_ms, self._capture)

    def _operation(self, deadline_ms, body):
        end = _deadline_end(deadline_ms)
        if os.getpid() != self._creator:
            raise PolicyCaptureError() from None
        if not self._guard.acquire(blocking=False):
            raise PolicyCaptureError() from None
        result = None
        failure = None
        slot = None
        clean = False
        cleanup_interrupt = None
        boundary_error = None
        guard_error = None
        try:
            try:
                if self._latched:
                    raise PolicyCaptureError() from None
                slot = _Slot()
                result = body(slot, end)
            except BaseException as exc:
                failure = exc
            if slot is not None:
                # The finite six-cell teardown (at most six cleanup
                # closes, no retries of unknown numeric closes, first
                # interruption identity preserved) traverses without a
                # time cut-off: every definitely owned cell is closed
                # even if the observation deadline has expired.
                try:
                    clean, cleanup_interrupt = _cleanup(slot, float("inf"))
                except BaseException as exc:
                    boundary_error = exc
        finally:
            if slot is not None and (not clean or boundary_error is not None):
                # Publish the closed latch and retain the unresolved
                # counted slot while still under the guard, before the
                # release is attempted.
                self._latched = True
                self._retained_slot = slot
            try:
                self._guard.release()
            except BaseException as exc:
                guard_error = exc
                # A guard release fault is never retried; the owner's
                # lock state is uncertain, so the owner latches closed.
                self._latched = True
                if slot is not None:
                    self._retained_slot = slot
        first_fault = boundary_error if boundary_error is not None else guard_error
        if failure is not None and not isinstance(failure, Exception) and first_fault is not None:
            raise failure from first_fault
        if (
            boundary_error is not None
            and not isinstance(boundary_error, Exception)
            and cleanup_interrupt is None
        ):
            if failure is None:
                raise boundary_error
            raise boundary_error from failure
        if (
            guard_error is not None
            and not isinstance(guard_error, Exception)
            and cleanup_interrupt is None
        ):
            raise guard_error
        if cleanup_interrupt is not None and (failure is None or isinstance(failure, Exception)):
            failure = cleanup_interrupt
        if failure is not None and not isinstance(failure, Exception):
            raise failure
        if failure is not None or guard_error is not None or (
            slot is not None and not clean
        ):
            raise PolicyCaptureError() from None
        # Final checkpoint before returning success: no successful
        # result after a cooperative expiry; a clean owner is not
        # latched.
        if time.monotonic() >= end:
            raise PolicyCaptureError() from None
        return result

    def _close_quietly(self, slot, fd):
        # Same close protocol priority as the publisher: a latched
        # ordinary primary is never replaced by a cleanup error.
        active = sys.exc_info()[1]
        try:
            slot.close(fd)
        except BaseException as close_error:
            if active is None or (
                isinstance(active, Exception) and not isinstance(close_error, Exception)
            ):
                raise

    def _observe_selection(self, slot, root_fd, end):
        probe = _probe_entry(root_fd, _SELECTION_NAME, end)
        _tick(end)
        try:
            fd = slot.opened(_SELECTION_NAME, _READ_FLAGS, parent=root_fd)
        except OSError:
            raise _Failure() from None
        try:
            _tick(end)
            st = os.fstat(fd)
            _tick(end)
            if (
                (st.st_dev, st.st_ino) != (probe.st_dev, probe.st_ino)
                or not _file_ok(st, st.st_size, 1)
                or not 1 <= st.st_size <= _MAX_RECORD_BYTES
            ):
                raise _Failure()
            data = bytearray()
            while len(data) < st.st_size:
                _tick(end)
                # Bounded by the captured size, plus the one-byte EOF probe.
                chunk = os.read(fd, st.st_size - len(data))
                _tick(end)
                if not chunk:
                    raise _Failure()
                data.extend(chunk)
            _tick(end)
            if os.read(fd, 1):
                raise _Failure()
            _tick(end)
            after = os.fstat(fd)
            _tick(end)
            entry = _probe_entry(root_fd, _SELECTION_NAME, end)
            _tick(end)
            if (
                _file_signature(st) != _file_signature(after)
                or _file_signature(after) != _file_signature(entry)
            ):
                raise _Failure()
            selection = parse_policy_selection(bytes(data))
            return selection, _file_signature(st)
        finally:
            self._close_quietly(slot, fd)

    def _read_payload(self, slot, root_fd, end, name, selection):
        probe = _probe_entry(root_fd, name, end)
        _tick(end)
        try:
            fd = slot.opened(name, _READ_FLAGS, parent=root_fd)
        except OSError:
            raise _Failure() from None
        try:
            _tick(end)
            st = os.fstat(fd)
            _tick(end)
            if (st.st_dev, st.st_ino) != (probe.st_dev, probe.st_ino) or not _file_ok(
                st, selection.wire_bytes, 1
            ):
                raise _Failure()
            expected = selection.wire_bytes
            data = bytearray()
            while len(data) < expected:
                _tick(end)
                chunk = os.read(fd, min(_CHUNK, expected - len(data)))
                _tick(end)
                if not chunk:
                    raise _Failure()
                data.extend(chunk)
            _tick(end)
            if os.read(fd, 1):
                raise _Failure()
            _tick(end)
            after = os.fstat(fd)
            _tick(end)
            entry = _probe_entry(root_fd, name, end)
            _tick(end)
            if (
                _file_signature(st) != _file_signature(after)
                or _file_signature(after) != _file_signature(entry)
            ):
                raise _Failure()
            digest = hashlib.sha256()
            view = memoryview(data)
            for offset in range(0, len(view), _CHUNK):
                _tick(end)
                digest.update(view[offset : offset + _CHUNK])
            _tick(end)
            if digest.hexdigest() != selection.wire_sha256:
                raise _Failure()
            return bytes(data), _file_signature(st)
        finally:
            self._close_quietly(slot, fd)

    def _read_selection(self, slot, end):
        root_fd = _walk(slot, self._parts, end)
        slot.root = root_fd
        try:
            selection, selection_signature = self._observe_selection(slot, root_fd, end)
            _namespace(slot, self._parts, end)
            _tick(end)
            selection_entry = _probe_entry(root_fd, _SELECTION_NAME, end)
            _tick(end)
            if _file_signature(selection_entry) != selection_signature:
                raise _Failure()
            return selection
        finally:
            self._close_quietly(slot, root_fd)

    def _capture(self, slot, end):
        root_fd = _walk(slot, self._parts, end)
        slot.root = root_fd
        try:
            _tick(end)
            selection, selection_signature = self._observe_selection(slot, root_fd, end)
            _tick(end)
            # Payload filename derived from the admitted digest only.
            name = selection.wire_sha256 + ".bin"
            wire_bytes, payload_signature = self._read_payload(
                slot, root_fd, end, name, selection
            )
            _tick(end)
            second, second_signature = self._observe_selection(slot, root_fd, end)
            _tick(end)
            if (
                second.selection_bytes != selection.selection_bytes
                or second_signature != selection_signature
            ):
                raise _Failure()
            _namespace(slot, self._parts, end)
            _tick(end)
            selection_entry = _probe_entry(root_fd, _SELECTION_NAME, end)
            _tick(end)
            payload_entry = _probe_entry(root_fd, name, end)
            _tick(end)
            if (
                _file_signature(selection_entry) != second_signature
                or _file_signature(payload_entry) != payload_signature
            ):
                raise _Failure()
            return CapturedPolicyBytes(selection, wire_bytes)
        finally:
            self._close_quietly(slot, root_fd)
