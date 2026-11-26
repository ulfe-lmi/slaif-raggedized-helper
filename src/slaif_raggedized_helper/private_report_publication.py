"""Private immutable report publication; storage is not execution attestation.

Protocol (Root amendment unnamed-v2): stage the exact admitted bytes in an UNNAMED
O_TMPFILE inode held by an owned descriptor, then publish with exactly one
no-replace hardlink of that inode via the owned procfs magic-link source.  The
module performs no destructive namespace operation (unlink/remove/rename/replace/
rmtree or equivalent) in any publication, cleanup, cancellation, fault or retry
branch: cleanup closes only definitely-owned descriptors.  No named staging
entry, random temp name, or named fallback ever exists.  O_TMPFILE/procfs runtime
feasibility is environment-specific and remains unproven until separately
authorized evidence (contract gates U1-U5) is accepted; unsupported environments
refuse.
Publication certainty (Root publication amendment): a state describes this
call's effect and verified durability, not a namespace lease.  Once a link is
attempted, every unresolved outcome retains POSSIBLY_PUBLISHED; DURABLE is
latched only after the complete applicable verification, flush and namespace
sequence.  EXISTING means a matching complete artifact was verified through
the full held-fd path, including its file fsync; it is not historical proof
that this call never created a visible entry.
"""

from dataclasses import dataclass
from enum import Enum
import errno
import fcntl
import hashlib
import os
import re
import stat
import sys
import threading
import time
import unicodedata

from .evaluation_program import _OwningGradeReport, Report
from .raw_snapshot_pin import PinData, PinOwner
from .raw_snapshot_selection import _Operation
from .source_cohort_runner import CohortReport


class Publication(Enum):
    NOT_PUBLISHED = "NOT_PUBLISHED"
    CONFLICT = "CONFLICT"
    POSSIBLY_PUBLISHED = "POSSIBLY_PUBLISHED"
    DURABLE = "DURABLE"


class Cleanup(Enum):
    CLEAN = "CLEAN"
    PENDING = "PENDING"


class Outcome(Enum):
    PUBLISHED = "PUBLISHED"
    EXISTING = "EXISTING"


@dataclass(frozen=True, repr=False, slots=True)
class Receipt:
    outcome: Outcome
    durability: Publication
    cleanup: Cleanup


@dataclass(frozen=True, repr=False, slots=True)
class CleanupReceipt:
    attempted: int
    remaining: int
    status: Cleanup


class PublicationError(Exception):
    __slots__ = ("_publication", "_cleanup")

    def __init__(self, publication, cleanup):
        super().__init__("private report publication refused")
        self._publication = publication
        self._cleanup = cleanup

    @property
    def publication(self):
        return self._publication

    @property
    def cleanup(self):
        return self._cleanup


_HASH = re.compile(r"sha256:[0-9a-f]{64}\Z", re.ASCII)
_SOURCE_FIELDS = frozenset(("identity_payload", "identity", "final_work", "final_payload"))
_GRADED_FIELDS = _SOURCE_FIELDS | {"plan_identity"}
_CHUNK = 65536


def _refuse():
    raise PublicationError(Publication.NOT_PUBLISHED, Cleanup.CLEAN) from None


def _deadline(deadline_ms):
    started = time.monotonic()
    if type(deadline_ms) is not int or not 1 <= deadline_ms <= 30000:
        _refuse()
    return started + deadline_ms / 1000


def _check_deadline(end):
    if time.monotonic() >= end:
        _refuse()


def _bounded_parts(directory):
    # The existing bounded directory admission shared by the two
    # entries: the exact legacy path ownership bounds - absolute,
    # bounded UTF-8, one to sixty-four parts, no empty, dot or
    # dot-dot parts, per-part byte bound and no control characters.
    if (
        type(directory) is not str
        or len(directory) > 4096
        or not directory.startswith("/")
        or directory == "/"
    ):
        _refuse()
    invalid_encoding = False
    try:
        parts = directory[1:].split("/")
        encoded = directory.encode("utf-8")
        if (
            len(encoded) > 4096
            or not 1 <= len(parts) <= 64
            or any(
                not part
                or part in (".", "..")
                or len(part.encode("utf-8")) > 255
                or any(unicodedata.category(c) == "Cc" for c in part)
                for part in parts
            )
        ):
            _refuse()
    except UnicodeError:
        invalid_encoding = True
    if invalid_encoding:
        _refuse()
    return parts


def _digest_identity(domain, data, identity, end):
    # The existing bounded chunked payload digest shared by the two
    # entries: the domain-prefixed SHA-256 of the exact payload bytes
    # verified against the report identity under the original absolute
    # deadline, one chunk at a time.
    digest = hashlib.sha256()
    digest.update(domain)
    view = memoryview(data)
    for offset in range(0, len(data), _CHUNK):
        _check_deadline(end)
        digest.update(view[offset : offset + _CHUNK])
    _check_deadline(end)
    if "sha256:" + digest.hexdigest() != identity:
        _refuse()
    return view


def _admit(report, directory, end):
    if type(report) is CohortReport:
        expected, cap = _SOURCE_FIELDS, 1642496
        domain, prefix = b"slaif-source-cohort-runner-v1\n", "source-"
    elif type(report) is Report:
        expected, cap = _GRADED_FIELDS, 12582912
        domain, prefix = b"slaif-graded-evaluation-program-v1\n", "graded-"
    else:
        _refuse()
    if len(vars(report)) != len(expected) or frozenset(vars(report)) != expected:
        _refuse()
    data = report.identity_payload
    if type(data) is not bytes or not 1 <= len(data) <= cap:
        _refuse()
    if type(report.identity) is not str or _HASH.fullmatch(report.identity) is None:
        _refuse()
    if type(report) is Report and (
        type(report.plan_identity) is not str or _HASH.fullmatch(report.plan_identity) is None
    ):
        _refuse()
    if (
        type(report.final_work) is not int
        or not 0 <= report.final_work <= 134217728
        or type(report.final_payload) is not int
        or not 0 <= report.final_payload <= 268435456
    ):
        _refuse()
    parts = _bounded_parts(directory)
    view = _digest_identity(domain, data, report.identity, end)
    return parts, prefix + report.identity[7:] + ".json", view


def _admit_current(report, directory, end):
    # The fixed private current admission: only the immutable
    # owner-bound owning result minted by the successful genuine grade
    # final cut, verified against its retained live custody, its exact
    # bound fields, the exact captured raw snapshot and generation,
    # the same order-owned admission with its captured selected
    # publication bytes and admitted operations, and the existing path
    # and directory ownership bounds.  The ordinary legacy Report is
    # refused at this entry, keeping its separate storage behavior,
    # type checks and bytes intact; no caller scope, clock, alternate
    # report, callback or provider is accepted.
    if type(report) is not _OwningGradeReport:
        _refuse()
    from . import private_policy_request as request

    data = report.identity_payload
    if type(data) is not bytes or not 1 <= len(data) <= 12582912:
        _refuse()
    if (
        type(report.identity) is not str
        or _HASH.fullmatch(report.identity) is None
    ):
        _refuse()
    if (
        type(report.plan_identity) is not str
        or _HASH.fullmatch(report.plan_identity) is None
    ):
        _refuse()
    if (
        type(report.final_work) is not int
        or not 0 <= report.final_work <= 134217728
        or type(report.final_payload) is not int
        or not 0 <= report.final_payload <= 268435456
    ):
        _refuse()
    owner = report.owner
    if type(owner) is not PinOwner or owner.state != "ACTIVE":
        _refuse()
    admission = report.admission
    if type(admission) is not request.PolicyRequestAdmission or admission._invalid:
        _refuse()
    if type(report.original_op) is not _Operation:
        _refuse()
    if owner.op is not report.original_op:
        _refuse()
    if owner.originals is not report.originals:
        _refuse()
    if owner.derived is not report.derived:
        _refuse()
    if owner.op.path != report.root:
        _refuse()
    if owner.value is not report.capture:
        _refuse()
    if type(report.capture) is not PinData:
        _refuse()
    if type(report.snapshot_id) is not str or type(report.generation) is not int:
        _refuse()
    if report.snapshot_id != report.capture.pointer.snapshot_id:
        _refuse()
    if report.generation != report.capture.pointer.generation:
        _refuse()
    if type(report.root) is not str:
        _refuse()
    if type(report.end) is not float or not report.end > 0:
        _refuse()
    if admission._expected_selection_bytes is not report.selected_bytes:
        _refuse()
    if admission.operations is not report.operations:
        _refuse()
    parts = _bounded_parts(directory)
    view = _digest_identity(
        b"slaif-graded-evaluation-program-v1\n", data, report.identity, end)
    return parts, "graded-" + report.identity[7:] + ".json", view


# Each slot preallocates six closed builtin state/number cells before any
# acquisition.  CLOSING/UNKNOWN cells are counted, never retried and occupy
# the slot until process restart; FREE always implies a cleared number.
_FREE = 0
_PRE = 1
_OWNED = 2
_CLOSING = 3
_UNKNOWN = 4
_CREATOR = os.getpid()
_REGISTRY_LOCK = threading.Lock()
_SLOTS = [None] * 16
_DIR_FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
_READ_FLAGS = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC


class _Failure(Exception):
    pass


class _Conflict(_Failure):
    pass


class _Slot:
    def __init__(self):
        self.guard = threading.Lock()
        # Preallocated closed builtin storage, allocated before any
        # acquisition: int state cells and numeric cells.  FREE always has a
        # cleared number; PRE/-1 is reserved-unresolved, PRE/fd and OWNED/fd
        # are definitely stored and closeable; CLOSING/UNKNOWN are counted
        # and never retried.
        self.st = [0] * 6
        self.fdn = [-1] * 6
        self.root = None
        self.stage = None
        self.stage_identity = None
        self.state = Publication.NOT_PUBLISHED
        self.pending = False

    def _occupied(self):
        return sum(1 for state in self.st if state != _FREE)

    def _all_free(self):
        return all(state == _FREE for state in self.st)

    def _free_cell(self):
        for k, state in enumerate(self.st):
            if state == _FREE:
                return k
        raise _Failure()

    def _find(self, fd):
        for k, state in enumerate(self.st):
            if state in (_PRE, _OWNED) and self.fdn[k] == fd:
                return k
        return -1

    def _close_cell(self, k):
        # One conservative close protocol: mark CLOSING before the first
        # close; after a known success clear the numeric cell BEFORE FREE; an
        # interrupted pre-call/return/bookkeeping outcome stays counted.
        # CLOSING/UNKNOWN are never retried and never closed again; a fresh
        # genuine open may reuse the same integer as a NEW cell.
        self.st[k] = _CLOSING
        try:
            os.close(self.fdn[k])
            self.fdn[k] = -1
            self.st[k] = _FREE
        except BaseException:
            self.st[k] = _UNKNOWN
            raise

    def opened(self, name, flags, mode=0o777, *, parent=None):
        if self._occupied() >= 6:
            raise _Failure()
        k = self._free_cell()
        self.st[k] = _PRE
        self.fdn[k] = -1
        try:
            self.fdn[k] = os.open(name, flags, mode, dir_fd=parent)
            self.st[k] = _OWNED
            return self.fdn[k]
        except BaseException as primary:
            cleanup_error = None
            if self.st[k] in (_PRE, _OWNED) and self.fdn[k] >= 0:
                # A definitely stored returned descriptor stays closeable
                # until it enters the close protocol.
                try:
                    self._close_cell(k)
                except BaseException as close_error:
                    # The handler target is cleared on leaving the suite;
                    # retain the cleanup exception under this outer name
                    # so the priority checks below see the real object.
                    cleanup_error = close_error
            else:
                # Unresolved acquisition: a raising open or interrupted
                # handler does not prove the kernel acquired no fd; the
                # reservation remains counted, with no number to close.
                self.st[k] = _UNKNOWN
                self.fdn[k] = -1
            if (
                isinstance(primary, Exception)
                and isinstance(cleanup_error, BaseException)
                and not isinstance(cleanup_error, Exception)
            ):
                # A genuine cleanup cancellation after an ordinary failure
                # keeps the existing cancellation priority.
                raise cleanup_error
            if cleanup_error is not None:
                # A latched primary is never replaced by a cleanup error.
                raise primary from cleanup_error
            raise

    def close(self, fd):
        k = self._find(fd)
        if k < 0:
            raise _Failure()
        self._close_cell(k)


def _creator():
    if os.getpid() != _CREATOR:
        raise PublicationError(Publication.NOT_PUBLISHED, Cleanup.PENDING) from None


def _reserve():
    _creator()
    with _REGISTRY_LOCK:
        for i, slot in enumerate(_SLOTS):
            if slot is None:
                slot = _Slot()
                # Recovery-visible pending before the slot is handed out: a
                # returned-but-unbound slot must not disappear from accounting.
                slot.pending = True
                slot.guard.acquire()
                _SLOTS[i] = slot
                return slot
    raise PublicationError(Publication.NOT_PUBLISHED, Cleanup.PENDING) from None


def _release(slot):
    with _REGISTRY_LOCK:
        for i, current in enumerate(_SLOTS):
            if current is slot:
                # Unregister only when every token is definitely FREE; a slot
                # that still owns or counts descriptors stays visible.
                if not slot._all_free():
                    raise _Failure()
                slot.pending = False
                _SLOTS[i] = None
                return
    raise _Failure()


def _tick(end):
    if time.monotonic() >= end:
        raise _Failure()


def _identity(st):
    return st.st_dev, st.st_ino, st.st_uid, stat.S_IMODE(st.st_mode)


def _ancestor(st):
    if not stat.S_ISDIR(st.st_mode) or st.st_uid not in (0, os.geteuid()):
        raise _Failure()
    if st.st_mode & 0o022 and not (st.st_uid == 0 and st.st_mode & stat.S_ISVTX):
        raise _Failure()


def _walk(slot, parts, end):
    _tick(end)
    fd = slot.opened("/", _DIR_FLAGS)
    _tick(end)
    _ancestor(os.fstat(fd))
    _tick(end)
    for part in parts:
        _tick(end)
        child = slot.opened(part, _DIR_FLAGS, parent=fd)
        _tick(end)
        st = os.fstat(child)
        _tick(end)
        linked = os.stat(part, dir_fd=fd, follow_symlinks=False)
        _tick(end)
        if _identity(st) != _identity(linked):
            raise _Failure()
        _ancestor(st)
        slot.close(fd)
        _tick(end)
        fd = child
    st = os.fstat(fd)
    _tick(end)
    if st.st_uid != os.geteuid() or stat.S_IMODE(st.st_mode) != 0o700:
        raise _Failure()
    return fd


def _namespace(slot, parts, end):
    fd = _walk(slot, parts, end)
    try:
        if _identity(os.fstat(fd)) != _identity(os.fstat(slot.root)):
            raise _Failure()
    finally:
        active = sys.exc_info()[1]
        try:
            slot.close(fd)
        except BaseException as close_error:
            if active is None or (
                isinstance(active, Exception) and not isinstance(close_error, Exception)
            ):
                raise
    _tick(end)


def _lock(slot, end):
    for _ in range(4096):
        _tick(end)
        try:
            fcntl.flock(slot.root, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            remaining = end - time.monotonic()
            if remaining <= 0:
                raise _Failure()
            time.sleep(min(0.01, remaining))
        else:
            _tick(end)
            return
    raise _Failure()


def _file_signature(st):
    return (
        st.st_dev,
        st.st_ino,
        st.st_uid,
        st.st_mode,
        st.st_nlink,
        st.st_size,
        st.st_mtime_ns,
        st.st_ctime_ns,
    )


def _file_ok(st, size, links):
    return (
        stat.S_ISREG(st.st_mode)
        and st.st_uid == os.geteuid()
        and stat.S_IMODE(st.st_mode) == 0o400
        and st.st_nlink == links
        and st.st_size == size
    )


def _verify(slot, name, data, end, *, expected_identity=None):
    _tick(end)
    try:
        os.stat(name, dir_fd=slot.root, follow_symlinks=False)
    except FileNotFoundError:
        # Absent at the bounded no-acquisition observation: take the
        # normal staging/link path without a final open on the common
        # fresh path.
        return False
    except OSError:
        # A probe error is not a decision: the real open below, with
        # all original validation, decides.
        pass
    _tick(end)
    try:
        fd = slot.opened(name, _READ_FLAGS, parent=slot.root)
    except FileNotFoundError:
        return False
    except OSError as exc:
        if exc.errno in (errno.ELOOP, errno.ENXIO, errno.EACCES, errno.EPERM):
            raise _Conflict() from None
        raise
    try:
        _tick(end)
        before = os.fstat(fd)
        _tick(end)
        if (
            expected_identity is not None
            and (
                before.st_dev,
                before.st_ino,
            )
            != expected_identity
        ):
            # Clean own publication: the held final descriptor must be
            # exactly the retained fsynced staging inode.  The generic
            # existing/recovery verification deliberately accepts a
            # different inode holding exactly the admitted bytes.
            raise _Failure()
        if not _file_ok(before, len(data), 1):
            raise _Conflict()
        offset = 0
        while offset < len(data):
            _tick(end)
            chunk = os.read(fd, min(_CHUNK, len(data) - offset))
            _tick(end)
            if not chunk or chunk != data[offset : offset + len(chunk)]:
                raise _Conflict()
            offset += len(chunk)
        if os.read(fd, 1):
            raise _Conflict()
        _tick(end)
        if expected_identity is None:
            # Generic existing/recovery final: flush the verified file
            # data while the descriptor is held, before the post-fstat
            # and linked-entry stability observations and before DURABLE.
            # A clean own publication reuses the stage's already-
            # successful file fsync through the identity binding above.
            os.fsync(fd)
            _tick(end)
        after = os.fstat(fd)
        _tick(end)
        entry = os.stat(name, dir_fd=slot.root, follow_symlinks=False)
        _tick(end)
        if _file_signature(before) != _file_signature(after) or _file_signature(
            after
        ) != _file_signature(entry):
            raise _Conflict()
        return True
    finally:
        active = sys.exc_info()[1]
        try:
            slot.close(fd)
        except BaseException as close_error:
            if active is None or (
                isinstance(active, Exception) and not isinstance(close_error, Exception)
            ):
                raise


def _cleanup(slot, end):
    # No destructive namespace operation exists in this protocol: cleanup
    # closes only definitely-owned descriptors.  An unnamed staging inode is
    # reclaimed by the kernel at its last close; closing a cell never changes
    # a link count.  CLOSING/UNKNOWN cells are counted and never retried.
    interrupt = None
    try:
        for k in range(6):
            if time.monotonic() >= end:
                break
            if slot.st[k] in (_PRE, _OWNED) and slot.fdn[k] >= 0:
                try:
                    slot._close_cell(k)
                except BaseException as exc:
                    if not isinstance(exc, Exception) and interrupt is None:
                        interrupt = exc
        slot.stage = None
        slot.stage_identity = None
        free = slot._all_free()
    except BaseException as helper_fault:
        # A first caught per-close cancellation is never lost to a
        # later loop, clock or bookkeeping fault, ordinary or
        # non-Exception; no exception objects are stored in retained
        # slot state and the finite six-cell protocol is unchanged.
        if interrupt is not None:
            raise interrupt from helper_fault
        raise
    return free, interrupt


def retry_cleanup(*, deadline_ms=30000):
    end = _deadline(deadline_ms)
    _creator()
    attempted = 0
    retirement_uncertain = False
    for i in range(len(_SLOTS)):
        with _REGISTRY_LOCK:
            slot = _SLOTS[i]
            if slot is None or not slot.pending:
                continue
        if time.monotonic() >= end:
            break
        if not slot.guard.acquire(blocking=False):
            continue
        body_error = None
        guard_error = None
        interrupt = None
        released_known = False
        retirement_fault = False
        try:
            with _REGISTRY_LOCK:
                registered = slot.pending and any(current is slot for current in _SLOTS)
            if not registered:
                continue
            attempted += 1
            try:
                clean, interrupt = _cleanup(slot, end)
            except BaseException as exc:
                body_error = exc
            else:
                if clean:
                    try:
                        _release(slot)
                    except BaseException as exc:
                        body_error = exc
                        # A release fault cannot be assumed to have had
                        # no effect: the slot may already be unregistered
                        # (after-effect) or still pending (before-effect).
                        retirement_fault = True
                    else:
                        released_known = True
        finally:
            try:
                slot.guard.release()
            except BaseException as exc:
                guard_error = exc
        # Same coherent priority policy as publish: the first caught
        # per-close interruption keeps its object; ordinary local
        # recovery faults never escape raw; a completed release is
        # never reinserted and no count is fabricated.
        first_fault = body_error if body_error is not None else guard_error
        if interrupt is not None and not isinstance(interrupt, Exception):
            if first_fault is not None:
                interrupt.__context__ = first_fault
            raise interrupt
        if body_error is not None and not isinstance(body_error, Exception):
            raise body_error
        if guard_error is not None and not isinstance(guard_error, Exception) and interrupt is None:
            raise guard_error
        if retirement_fault or (released_known and first_fault is not None):
            # A retirement or finalization fault, before or after its
            # effect, is not a proven clean retirement: the observed
            # count stays real and the status conservative.
            retirement_uncertain = True
    try:
        with _REGISTRY_LOCK:
            remaining = sum(slot is not None and slot.pending for slot in _SLOTS)
    except Exception:
        # Reliable counting failed: no fabricated count and no raw
        # ordinary fault; report the constant content-free refusal.
        raise PublicationError(Publication.NOT_PUBLISHED, Cleanup.PENDING) from None
    # Any retirement or finalization fault, before or after its
    # effect, is not a proven clean retirement: the observed status
    # stays conservative; the remaining count is always the real registry.
    if remaining == 0 and not retirement_uncertain:
        status = Cleanup.CLEAN
    else:
        status = Cleanup.PENDING
    return CleanupReceipt(attempted, remaining, status)


def _stage(slot, data, end, *, _current_report=None):
    # Unnamed staging: no directory entry, no random name, no fallback path.
    _tick(end)
    if getattr(os, "O_TMPFILE", None) is None:
        raise _Failure()
    try:
        fd = slot.opened(".", os.O_TMPFILE | os.O_RDWR | os.O_CLOEXEC, 0o600, parent=slot.root)
    except OSError:
        # Unsupported kernel/filesystem/procfs environment: fail closed.
        raise _Failure() from None
    _tick(end)
    st = os.fstat(fd)
    _tick(end)
    # Requested 0600 is umask-masked: the observed mode must be exactly 0600.
    # The same-root-device observation is made before the first write.
    if (
        not stat.S_ISREG(st.st_mode)
        or st.st_uid != os.geteuid()
        or stat.S_IMODE(st.st_mode) != 0o600
        or st.st_nlink != 0
        or st.st_dev != os.fstat(slot.root).st_dev
    ):
        raise _Failure()
    slot.stage = fd
    slot.stage_identity = (st.st_dev, st.st_ino)
    if _current_report is not None:
        # The genuine pre-write current-report cut: the actual unnamed
        # staging fd now exists and the genuine initial staging
        # fd/type/mode/link/device checks succeeded, strictly before
        # the first actual report payload write.  The fixed private
        # mode carries only the exact owning result - no callable hook.
        if type(_current_report) is not _OwningGradeReport:
            raise _Failure()
        _current_cut(_current_report, end)
    offset = 0
    while offset < len(data):
        _tick(end)
        count = os.write(fd, data[offset : min(offset + _CHUNK, len(data))])
        _tick(end)
        if count <= 0:
            raise _Failure()
        offset += count
    os.fchmod(fd, 0o400)
    _tick(end)
    os.fsync(fd)
    _tick(end)
    st = os.fstat(fd)
    _tick(end)
    if not _file_ok(st, len(data), 0) or (st.st_dev, st.st_ino) != slot.stage_identity:
        raise _Failure()
    # The descriptor stays open through publication and verification.
    return fd


def _stage_ok(slot, size):
    # Normative prelink recheck: the owned stage fd/inode must still be the
    # retained, unlinked, exact-mode staging inode on the root's device; the
    # deadline is rechecked again after this metadata observation,
    # immediately before POSSIBLY_PUBLISHED is marked and the link attempted.
    st = os.fstat(slot.stage)
    return (
        stat.S_ISREG(st.st_mode)
        and st.st_uid == os.geteuid()
        and stat.S_IMODE(st.st_mode) == 0o400
        and st.st_nlink == 0
        and st.st_size == size
        and (st.st_dev, st.st_ino) == slot.stage_identity
        and st.st_dev == os.fstat(slot.root).st_dev
    )


def _store(slot, name, data, parts, end, *, _current_report=None):
    # Generic admitted-content storage shared by the trusted entries:
    # the unnamed stage, the normative prelink recheck, the single
    # no-replace link, the full held-fd verification and both fsync
    # boundaries.  No destructive namespace operation exists here or in
    # any caller: a collision and every unresolved post-attempt state
    # are handled by the caller's conservative state and verification
    # rules, never by rollback.
    _stage(slot, data, end, _current_report=_current_report)
    _namespace(slot, parts, end)
    _tick(end)
    if not _stage_ok(slot, len(data)):
        raise _Failure()
    if _current_report is not None:
        # The genuine post-prelink current-report cut: after the genuine
        # prelink metadata verification, strictly before the state
        # transition and the first possible link.
        if type(_current_report) is not _OwningGradeReport:
            raise _Failure()
        _current_cut(_current_report, end)
    _tick(end)
    slot.state = Publication.POSSIBLY_PUBLISHED
    try:
        os.link(
            "/proc/self/fd/%d" % slot.stage,
            name,
            dst_dir_fd=slot.root,
            follow_symlinks=True,
        )
    except FileExistsError:
        # One bounded recovery-verification branch: the collision
        # itself cannot publish this staged inode, and the observed
        # exception alone does not prove that the link had no
        # effect, so POSSIBLY_PUBLISHED is retained until the full
        # generic held-fd verification (including its file flush)
        # proves an identical final.
        if not _verify(slot, name, data, end):
            raise _Failure()
        _tick(end)
        os.fsync(slot.root)
        _tick(end)
        _namespace(slot, parts, end)
        slot.state = Publication.DURABLE
        return Outcome.EXISTING
    _tick(end)
    st = os.fstat(slot.stage)
    _tick(end)
    if (
        (st.st_dev, st.st_ino) != slot.stage_identity
        or not stat.S_ISREG(st.st_mode)
        or st.st_nlink != 1
    ):
        raise _Failure()
    if not _verify(slot, name, data, end, expected_identity=slot.stage_identity):
        raise _Failure()
    _tick(end)
    os.fsync(slot.root)
    _tick(end)
    _namespace(slot, parts, end)
    slot.state = Publication.DURABLE
    return Outcome.PUBLISHED


def _transact(parts, name, data, end, *, error, note, _current_report=None):
    # The complete shared admitted-content transaction, performed once
    # for every trusted entry after its own admission: pool
    # reservation, no-follow namespace walk, directory-inode writer
    # lock, namespace stability, the exact-existing final
    # verification or the generic storage core, the conservative
    # state, the cleanup/retirement and guard policy and the
    # ordinary-failure normalization.  ``error`` maps the truthful
    # (publication, cleanup) state to the calling entry's fixed
    # content-free refusal; ``note`` is the cleanup-pending note
    # attached to a non-Exception primary that still owns
    # descriptors.  Non-Exception interruptions preserve identity and
    # never enter the fixed refusal.  Returns the shared ``Outcome``
    # only after the complete storage and verification sequence.
    # ``_current_report`` is the fixed private current-report mode:
    # the exact owning result or None - when set, the shared storage
    # core performs the concrete current custody cuts at the two
    # actual storage points; no callable hook is accepted.
    slot = _reserve()
    outcome = None
    failure = None
    try:
        slot.root = _walk(slot, parts, end)
        _lock(slot, end)
        _namespace(slot, parts, end)
        if _verify(slot, name, data, end):
            _tick(end)
            os.fsync(slot.root)
            _tick(end)
            _namespace(slot, parts, end)
            slot.state = Publication.DURABLE
            outcome = Outcome.EXISTING
        else:
            outcome = _store(
                slot, name, data, parts, end, _current_report=_current_report)
        _tick(end)
    except BaseException as exc:
        failure = exc
        # CONFLICT is assigned only to pre-attempt namespace conflicts: an
        # unresolved post-attempt state keeps POSSIBLY_PUBLISHED and is
        # never downgraded to NOT_PUBLISHED or CONFLICT.
        if isinstance(exc, _Conflict) and slot.state is not Publication.POSSIBLY_PUBLISHED:
            slot.state = Publication.CONFLICT
    # Recovery-visible pending before risky cleanup work: an
    # interruption outside the per-fd close try must never leave a
    # non-clean slot invisible to retry_cleanup.
    slot.pending = True
    state = slot.state
    clean = False
    cleanup_interrupt = None
    boundary_error = None
    guard_error = None
    try:
        clean, cleanup_interrupt = _cleanup(slot, end)
        if clean:
            _release(slot)
    except BaseException as exc:
        boundary_error = exc
    try:
        slot.guard.release()
    except BaseException as exc:
        guard_error = exc
    # One coherent cleanup/retirement/guard policy: the latched
    # primary and the first caught non-Exception interruption outrank
    # later ordinary faults; ordinary faults never escape raw but
    # degrade the conservative count; an ambiguous guard release is
    # never retried blindly and no descriptor work follows the
    # ownership transfer.
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
    if first_fault is not None:
        clean = False
    if cleanup_interrupt is not None and (failure is None or isinstance(failure, Exception)):
        failure = cleanup_interrupt
    if failure is not None and not isinstance(failure, Exception):
        if not clean:
            try:
                failure.add_note(note)
            except BaseException:
                pass
        raise failure
    if failure is not None or not clean:
        raise error(state, Cleanup.CLEAN if clean else Cleanup.PENDING) from None
    return outcome


def _publication_error(installation, cleanup):
    return PublicationError(installation, cleanup)


def publish(report, *, directory, deadline_ms=30000):
    end = _deadline(deadline_ms)
    _creator()
    parts, final, data = _admit(report, directory, end)
    outcome = _transact(
        parts,
        final,
        data,
        end,
        error=_publication_error,
        note="private report publication cleanup pending",
    )
    return Receipt(outcome, Publication.DURABLE, Cleanup.CLEAN)


def _current_cut(report, end):
    # One short live guarded cut under its own nonblocking owner
    # borrow: the retained exact live custody re-verified under the
    # borrow - the live original operation object, the original owner
    # and its stores/root, the exact retained capture plus its
    # snapshot and generation, the exact admission selected bytes and
    # admitted operations, and the bounded detached grants against the
    # original anchor - the short live same-owner association
    # (metadata observations only - no full raw load for this
    # continuous captured owner, and no reusable generic hook) with
    # the original clipped absolute end attached only on the checked
    # original operation for the duration of the association and the
    # genuine same-admission selected reread under the original end,
    # the exact saved end of the checked original operation restored
    # on that same object, the guard released independently and the
    # original absolute cutoff checked before the protected effect or
    # the safe release.  No extra full pin and no relative deadline
    # reset.
    from . import private_policy_pin_eligibility as pin_eligibility

    owner = report.owner
    admission = report.admission
    original_op = report.original_op
    pin_eligibility._borrowed_owner(owner)
    try:
        if (
            type(original_op) is not _Operation
            or owner.state != "ACTIVE"
            or owner.op is not original_op
            or owner.originals is not report.originals
            or owner.derived is not report.derived
            or owner.op.path != report.root
            or owner.value is not report.capture
            or type(report.capture) is not PinData
            or type(report.snapshot_id) is not str
            or type(report.generation) is not int
            or report.snapshot_id != report.capture.pointer.snapshot_id
            or report.generation != report.capture.pointer.generation
            or admission._expected_selection_bytes is not report.selected_bytes
            or admission.operations is not report.operations
        ):
            raise _Failure()
        if pin_eligibility._bound_grants(admission, report.anchor) != report.grants:
            raise _Failure()
        prior_end = original_op.end
        original_op.end = end
        try:
            owner._association()
            pin_eligibility._genuine_recheck(admission, end)
        finally:
            original_op.end = prior_end
    finally:
        owner.guard.release()
    _tick(end)


def _publish_current(report, *, directory):
    # The fixed private current entry: the exact owning result with its
    # original clipped absolute end as the deadline, the complete
    # shared admitted-content transaction in its fixed private
    # current-report mode with its two genuine short live guarded cuts
    # - one before the first actual report payload write and one after
    # the genuine prelink metadata verification, preceding the state
    # transition and the first possible link - and the separate short
    # release cut only after the genuine storage transaction's owned
    # cleanup finishes, performed for both PUBLISHED and EXISTING.
    # Only the actual successful release cut and the original absolute
    # cutoff checked before it release the narrow content-free
    # receipt; an ordinary refusal after durability is normalized
    # outside the caught handler, retains the observed DURABLE/CLEAN
    # storage and cleanup truth, and suppresses both the result and the
    # safe receipt with one fixed content-free error, no data-bearing
    # context, no raw identity, path, authority or report content,
    # while a non-Exception interruption keeps its original identity.
    # The exact saved end is restored on the checked original operation
    # and every cut releases the owner guard independently on every
    # exit.
    if type(report) is not _OwningGradeReport:
        _refuse()
    end = report.end
    parts, final, data = _admit_current(report, directory, end)
    outcome = _transact(
        parts,
        final,
        data,
        end,
        error=_publication_error,
        note="private current report publication cleanup pending",
        _current_report=report,
    )
    denied = False
    interrupt = None
    try:
        _current_cut(report, end)
        # The original absolute cutoff is checked again before the safe
        # receipt is released.
        _tick(end)
    except BaseException as exc:
        # The ordinary after-cleanup denial is normalized outside the
        # caught handler, so the fixed refusal carries no data-bearing
        # context from the underlying namespace/authority error.
        if isinstance(exc, Exception):
            denied = True
        else:
            interrupt = exc
    if interrupt is not None:
        raise interrupt
    if denied:
        raise _publication_error(Publication.DURABLE, Cleanup.CLEAN)
    return Receipt(outcome, Publication.DURABLE, Cleanup.CLEAN)
